### flash attn varlen

# fused-attention-batch4-head32-d64-fwd-causal=True(TFLOPS):
#      N_CTX  Triton [FP16]  Triton [FP8]    Flash-2      Torch
# 0   1024.0     109.401005    177.267951  63.648125  63.416724
# 1   2048.0     126.494226    219.654219  74.116781  73.599677
# 2   4096.0     134.347472    243.889652  79.950963  79.493111
# 3   8192.0     138.274682    257.320406  82.823309  82.781158
# 4  16384.0     140.180181    264.430476  84.144511  84.408326
# fused-attention-batch4-head32-d64-fwd-causal=False(TFLOPS):
#      N_CTX  Triton [FP16]  Triton [FP8]    Flash-2      Torch
# 0   1024.0     125.073254    227.845079  76.990110  78.312257
# 1   2048.0     135.747284    250.757518  81.662243  82.936451
# 2   4096.0     137.831221    262.107051  83.852429  85.281573
# 3   8192.0     140.485131    267.100924  84.256177  85.444708
# 4  16384.0     141.414108    267.942942  84.714427  85.942829
# fused-attention-batch4-head32-d64-bwd-causal=True(TFLOPS):
#      N_CTX  Triton [FP16]  Triton [FP8]    Flash-2      Torch
# 0   1024.0      65.156899     65.120720  58.187804  51.075234
# 1   2048.0      79.650563     79.674509  70.731665  64.588201
# 2   4096.0      88.405380     88.457147  78.682864  73.839141
# 3   8192.0      93.300402     93.360699  83.057697  79.123305
# 4  16384.0      95.250280     95.293259  85.456407  82.148268

# https://github.com/Dao-AILab/flash-attention/blob/main/flash_attn/flash_attn_interface.py#L1375

### 工业版 —— Triton Tutorial

"""
Fused Attention
===============

This is a Triton implementation of the Flash Attention v2 algorithm from Tri Dao (https://tridao.me/publications/flash2/flash2.pdf)

Credits: OpenAI kernel team

Extra Credits:

* Original flash attention paper (https://arxiv.org/abs/2205.14135)
* Rabe and Staats (https://arxiv.org/pdf/2112.05682v2.pdf)

"""

"""
code reading:
- 基础写法：
    - tl.make_block_ptr，order=(1, 0) 表示按行存储，order=(0, 1) 表示按列存储
    - K_block_ptr = tl.advance(K_block_ptr, (0, lo))
    - tl.trans(A)
- forward
    - attn casual mask实现：tril: tri + lower; triu: tri + upper
    - assert HEAD_DIM_K in {16, 32, 64, 128, 256}, 确保放进shared memory
    - qk_scale *= 1.44269504 ： Triton 内核使用了 tl.math.exp2 （以 2 为底的指数）而不是标准的 exp （以 e 为底的指数）来计算 Softmax
    - 先load q: it will stay in SRAM throughout
    - 结构化的分离（由两个 if 实现）“makes it easier for compiler to schedule the two loops independently”
        让编译器更容易独立地调度这两个循环/计算阶段）。编译器可以更清晰地看到数据依赖关系，并分别优化每个阶段的指令执行和内存访问，
        而不需要处理一个混合了两种复杂逻辑（带掩码/不带掩码，处理不同范围的 K/V）的大循环。
- backward
    - BATCH * N_HEAD 作为grid的一维，充分并行
    - mask，dkdv的求解中，要对pT做，是未归一化的概率分布


- _attn_fwd_inner
    - STAGE == 1: 处理当前 Query 块（由 start_m 决定） 之前 的所有 Key/Value 块。
    - STAGE == 2: 处理与当前 Query 块 对齐 的那个 Key/Value 块（即“对角线块”）。
        - mask = offs_m[:, None] >= (start_n + offs_n[None, :])
        - lo = tl.multiple_of(lo, BLOCK_M) : 
    - STAGE == 3: 处理所有的 Key/Value 块，不应用任何因果掩码。
    - 量化：p = p.to(tl.float16) acc = tl.dot(p, v, acc)，对QK做量化
- _attn_bwd_dkdv
    - Load m before computing qk to reduce pipeline stall.
- _attn_bwd_dq
    - dq += tl.dot(ds, tl.trans(kT))

- TMA:
    k = desc_k.load([offsetkv_y, 0]).T
    qk = tl.dot(q, k)

### 参数tune

- tiling i/j 64/128, at least 4 versions

"""
from typing import Optional
import pytest
import torch
from torch.amp import custom_fwd

import triton
import triton.language as tl

try:
  from triton.tools.tensor_descriptor import TensorDescriptor
  HAS_TENSOR_DESC = True
except ModuleNotFoundError:
  HAS_TENSOR_DESC = False

DEVICE = torch.cuda.current_device()


def is_hip():
  return triton.runtime.driver.active.get_current_target().backend == "hip"


def is_cuda():
  return triton.runtime.driver.active.get_current_target().backend == "cuda"


def supports_tma():
  return HAS_TENSOR_DESC and is_cuda() and torch.cuda.get_device_capability()[0] >= 9

print(f"HAS_TENSOR_DESC: {HAS_TENSOR_DESC}, supports_tma: {supports_tma()}")

@triton.jit
def _attn_fwd_inner(acc, l_i, m_i, q,  #
                    K_block_ptr, V_block_ptr,  #
                    start_m, qk_scale,  #
                    BLOCK_M: tl.constexpr, HEAD_DIM: tl.constexpr, BLOCK_N: tl.constexpr,  #
                    STAGE: tl.constexpr, offs_m: tl.constexpr, offs_n: tl.constexpr,  #
                    N_CTX: tl.constexpr, fp8_v: tl.constexpr):
  # range of values handled by this stage
  if STAGE == 1:
    lo, hi = 0, start_m * BLOCK_M
  elif STAGE == 2:
    lo, hi = start_m * BLOCK_M, (start_m + 1) * BLOCK_M
    lo = tl.multiple_of(lo, BLOCK_M)
  # causal = False
  else:
    lo, hi = 0, N_CTX
  K_block_ptr = tl.advance(K_block_ptr, (0, lo))
  V_block_ptr = tl.advance(V_block_ptr, (lo, 0))
  # loop over k, v and update accumulator
  for start_n in range(lo, hi, BLOCK_N):
    start_n = tl.multiple_of(start_n, BLOCK_N)
    # -- compute qk ----
    k = tl.load(K_block_ptr)
    qk = tl.dot(q, k)
    if STAGE == 2:
      mask = offs_m[:, None] >= (start_n + offs_n[None, :])
      qk = qk * qk_scale + tl.where(mask, 0, -1.0e6)
      m_ij = tl.maximum(m_i, tl.max(qk, 1))
      qk -= m_ij[:, None]
    else:
      m_ij = tl.maximum(m_i, tl.max(qk, 1) * qk_scale)
      qk = qk * qk_scale - m_ij[:, None]
    p = tl.math.exp2(qk)
    l_ij = tl.sum(p, 1)
    # -- update m_i and l_i
    alpha = tl.math.exp2(m_i - m_ij)
    l_i = l_i * alpha + l_ij
    # -- update output accumulator --
    acc = acc * alpha[:, None]
    # update acc
    v = tl.load(V_block_ptr)
    if fp8_v:
      p = p.to(tl.float8e5)
    else:
      p = p.to(tl.float16)
    acc = tl.dot(p, v, acc)
    # update m_i and l_i
    m_i = m_ij
    V_block_ptr = tl.advance(V_block_ptr, (BLOCK_N, 0))
    K_block_ptr = tl.advance(K_block_ptr, (0, BLOCK_N))
  return acc, l_i, m_i


@triton.jit
def _attn_fwd_inner_tma(acc, l_i, m_i, q,  #
                        desc_k, desc_v,  #
                        offset_y, dtype: tl.constexpr, start_m, qk_scale,  #
                        BLOCK_M: tl.constexpr, HEAD_DIM: tl.constexpr, BLOCK_N: tl.constexpr,  #
                        STAGE: tl.constexpr, offs_m: tl.constexpr, offs_n: tl.constexpr,  #
                        N_CTX: tl.constexpr):
  # range of values handled by this stage
  if STAGE == 1:
    lo, hi = 0, start_m * BLOCK_M
  elif STAGE == 2:
    lo, hi = start_m * BLOCK_M, (start_m + 1) * BLOCK_M
    lo = tl.multiple_of(lo, BLOCK_M)
  # causal = False
  else:
    lo, hi = 0, N_CTX
  offsetkv_y = offset_y + lo
  # loop over k, v and update accumulator
  for start_n in range(lo, hi, BLOCK_N):
    start_n = tl.multiple_of(start_n, BLOCK_N)
    # -- compute qk ----
    k = desc_k.load([offsetkv_y, 0]).T
    qk = tl.dot(q, k)
    if STAGE == 2:
      mask = offs_m[:, None] >= (start_n + offs_n[None, :])
      qk = qk * qk_scale + tl.where(mask, 0, -1.0e6)
      m_ij = tl.maximum(m_i, tl.max(qk, 1))
      qk -= m_ij[:, None]
    else:
      m_ij = tl.maximum(m_i, tl.max(qk, 1) * qk_scale)
      qk = qk * qk_scale - m_ij[:, None]
    p = tl.math.exp2(qk)
    l_ij = tl.sum(p, 1)
    # -- update m_i and l_i
    alpha = tl.math.exp2(m_i - m_ij)
    l_i = l_i * alpha + l_ij
    # -- update output accumulator --
    acc = acc * alpha[:, None]
    # update acc
    v = desc_v.load([offsetkv_y, 0])
    p = p.to(dtype)
    # note that this non transposed v for FP8 is only supported on Blackwell
    acc = tl.dot(p, v, acc)
    # update m_i and l_i
    m_i = m_ij
    offsetkv_y += BLOCK_N
  return acc, l_i, m_i


# We don't run auto-tuning every time to keep the tutorial fast. Keeping
# the code below and commenting out the equivalent parameters is convenient for
# re-tuning.
configs = [
  triton.Config({'BLOCK_M': BM, 'BLOCK_N': BN}, num_stages=s, num_warps=w) \
  for BM in [64, 128] \
  for BN in [32, 64] \
  for s in ([1] if is_hip() else [3, 4, 7]) \
  for w in [4, 8] \
  ]


def keep(conf):
  BLOCK_M = conf.kwargs["BLOCK_M"]
  BLOCK_N = conf.kwargs["BLOCK_N"]
  if BLOCK_M * BLOCK_N < 128 * 128 and conf.num_warps == 8:
    return False
  return True


@triton.autotune(list(filter(keep, configs)), key=["N_CTX", "HEAD_DIM"])
@triton.jit
def _attn_fwd(Q, K, V, sm_scale, M, Out,  #
              stride_qz, stride_qh, stride_qm, stride_qk,  #
              stride_kz, stride_kh, stride_kn, stride_kk,  #
              stride_vz, stride_vh, stride_vk, stride_vn,  #
              stride_oz, stride_oh, stride_om, stride_on,  #
              Z, H, N_CTX,  #
              HEAD_DIM: tl.constexpr,  #
              BLOCK_M: tl.constexpr,  #
              BLOCK_N: tl.constexpr,  #
              STAGE: tl.constexpr  #
              ):
  tl.static_assert(BLOCK_N <= HEAD_DIM)
  start_m = tl.program_id(0)
  off_hz = tl.program_id(1)
  off_z = off_hz // H
  off_h = off_hz % H
  qvk_offset = off_z.to(tl.int64) * stride_qz + off_h.to(tl.int64) * stride_qh

  # block pointers
  Q_block_ptr = tl.make_block_ptr(
    base=Q + qvk_offset,
    shape=(N_CTX, HEAD_DIM),
    strides=(stride_qm, stride_qk),
    offsets=(start_m * BLOCK_M, 0),
    block_shape=(BLOCK_M, HEAD_DIM),
    order=(1, 0),
  )
  v_order: tl.constexpr = (0, 1) if V.dtype.element_ty == tl.float8e5 else (1, 0)
  V_block_ptr = tl.make_block_ptr(
    base=V + qvk_offset,
    shape=(N_CTX, HEAD_DIM),
    strides=(stride_vk, stride_vn),
    offsets=(0, 0),
    block_shape=(BLOCK_N, HEAD_DIM),
    order=v_order,
  )
  K_block_ptr = tl.make_block_ptr(
    base=K + qvk_offset,
    shape=(HEAD_DIM, N_CTX),
    strides=(stride_kk, stride_kn),
    offsets=(0, 0),
    block_shape=(HEAD_DIM, BLOCK_N),
    order=(0, 1),
  )
  O_block_ptr = tl.make_block_ptr(
    base=Out + qvk_offset,
    shape=(N_CTX, HEAD_DIM),
    strides=(stride_om, stride_on),
    offsets=(start_m * BLOCK_M, 0),
    block_shape=(BLOCK_M, HEAD_DIM),
    order=(1, 0),
  )
  # initialize offsets
  offs_m = start_m * BLOCK_M + tl.arange(0, BLOCK_M)
  offs_n = tl.arange(0, BLOCK_N)
  # initialize pointer to m and l
  m_i = tl.zeros([BLOCK_M], dtype=tl.float32) - float("inf") # Running Maximum
  l_i = tl.zeros([BLOCK_M], dtype=tl.float32) + 1.0 # Running Normalizer Sum
  acc = tl.zeros([BLOCK_M, HEAD_DIM], dtype=tl.float32)
  # load scales
  qk_scale = sm_scale
  qk_scale *= 1.44269504  # 1/log(2)
  # load q: it will stay in SRAM throughout
  q = tl.load(Q_block_ptr)
  # stage 1: off-band
  # For causal = True, STAGE = 3 and _attn_fwd_inner gets 1 as its STAGE
  # For causal = False, STAGE = 1, and _attn_fwd_inner gets 3 as its STAGE
  if STAGE & 1:
    acc, l_i, m_i = _attn_fwd_inner(acc, l_i, m_i, q, K_block_ptr, V_block_ptr,  #
                                    start_m, qk_scale,  #
                                    BLOCK_M, HEAD_DIM, BLOCK_N,  #
                                    4 - STAGE, offs_m, offs_n, N_CTX, V.dtype.element_ty == tl.float8e5  #
                                    )
  # stage 2: on-band
  if STAGE & 2:
    # barrier makes it easier for compiler to schedule the
    # two loops independently
    acc, l_i, m_i = _attn_fwd_inner(acc, l_i, m_i, q, K_block_ptr, V_block_ptr,  #
                                    start_m, qk_scale,  #
                                    BLOCK_M, HEAD_DIM, BLOCK_N,  #
                                    2, offs_m, offs_n, N_CTX, V.dtype.element_ty == tl.float8e5  #
                                    )
  # epilogue
  m_i += tl.math.log2(l_i)
  acc = acc / l_i[:, None]
  m_ptrs = M + off_hz * N_CTX + offs_m
  tl.store(m_ptrs, m_i)
  tl.store(O_block_ptr, acc.to(Out.type.element_ty))


def _tma_pre_hook(nargs):
  BLOCK_M = nargs["BLOCK_M"]
  BLOCK_N = nargs["BLOCK_N"]
  HEAD_DIM = nargs["HEAD_DIM"]
  nargs["desc_q"].block_shape = [BLOCK_M, HEAD_DIM]
  nargs["desc_v"].block_shape = [BLOCK_N, HEAD_DIM]
  nargs["desc_k"].block_shape = [BLOCK_N, HEAD_DIM]
  nargs["desc_o"].block_shape = [BLOCK_M, HEAD_DIM]


# We don't run auto-tuning every time to keep the tutorial fast. Keeping
# the code below and commenting out the equivalent parameters is convenient for
# re-tuning.
configs_tma = [
  triton.Config({'BLOCK_M': BM, 'BLOCK_N': BN}, num_stages=s, num_warps=w, pre_hook=_tma_pre_hook) \
  for BM in [64, 128] \
  for BN in [32, 64, 128] \
  for s in [2, 3, 4, 6] \
  for w in [4, 8] \
  ]


def keep_tma(conf):
  BLOCK_M = conf.kwargs["BLOCK_M"]
  BLOCK_N = conf.kwargs["BLOCK_N"]
  if (torch.cuda.get_device_capability()[0] == 9 and BLOCK_M * BLOCK_N < 128 * 128 and conf.num_warps == 8):
    return False
  return True


@triton.autotune(configs=list(filter(keep_tma, configs_tma)), key=["N_CTX", "HEAD_DIM", "FP8_OUTPUT"])
@triton.jit
def _attn_fwd_tma(sm_scale, M,  #
                  Z, H, desc_q, desc_k, desc_v, desc_o, N_CTX,  #
                  HEAD_DIM: tl.constexpr,  #
                  BLOCK_M: tl.constexpr,  #
                  BLOCK_N: tl.constexpr,  #
                  FP8_OUTPUT: tl.constexpr,  #
                  STAGE: tl.constexpr  #
                  ):
  dtype = tl.float8e5 if FP8_OUTPUT else tl.float16
  tl.static_assert(BLOCK_N <= HEAD_DIM)
  start_m = tl.program_id(0)
  off_hz = tl.program_id(1)
  off_z = off_hz // H
  off_h = off_hz % H

  offset_y = off_z + off_h * N_CTX
  qo_offset_y = offset_y + start_m * BLOCK_M
  # initialize offsets
  offs_m = start_m * BLOCK_M + tl.arange(0, BLOCK_M)
  offs_n = tl.arange(0, BLOCK_N)
  # initialize pointer to m and l
  m_i = tl.zeros([BLOCK_M], dtype=tl.float32) - float("inf")
  l_i = tl.zeros([BLOCK_M], dtype=tl.float32) + 1.0
  acc = tl.zeros([BLOCK_M, HEAD_DIM], dtype=tl.float32)
  # load scales
  qk_scale = sm_scale
  qk_scale *= 1.44269504  # 1/log(2)
  # load q: it will stay in SRAM throughout
  q = desc_q.load([qo_offset_y, 0])
  # stage 1: off-band
  # For causal = True, STAGE = 3 and _attn_fwd_inner gets 1 as its STAGE
  # For causal = False, STAGE = 1, and _attn_fwd_inner gets 3 as its STAGE
  if STAGE & 1:
    acc, l_i, m_i = _attn_fwd_inner_tma(acc, l_i, m_i, q,  #
                                        desc_k, desc_v,  #
                                        offset_y, dtype, start_m, qk_scale,  #
                                        BLOCK_M, HEAD_DIM, BLOCK_N,  #
                                        4 - STAGE, offs_m, offs_n, N_CTX,  #
                                        )
  # stage 2: on-band
  if STAGE & 2:
    # barrier makes it easier for compielr to schedule the
    # two loops independently
    acc, l_i, m_i = _attn_fwd_inner_tma(acc, l_i, m_i, q,  #
                                        desc_k, desc_v,  #
                                        offset_y, dtype, start_m, qk_scale,  #
                                        BLOCK_M, HEAD_DIM, BLOCK_N,  #
                                        2, offs_m, offs_n, N_CTX,  #
                                        )
  # epilogue
  m_i += tl.math.log2(l_i)
  acc = acc / l_i[:, None]
  m_ptrs = M + off_hz * N_CTX + offs_m
  tl.store(m_ptrs, m_i)
  desc_o.store([qo_offset_y, 0], acc.to(dtype))


@triton.jit
def _attn_bwd_preprocess(O, DO,  #
                         Delta,  #
                         Z, H, N_CTX,  #
                         BLOCK_M: tl.constexpr, HEAD_DIM: tl.constexpr  #
                         ):
  off_m = tl.program_id(0) * BLOCK_M + tl.arange(0, BLOCK_M)
  off_hz = tl.program_id(1)
  off_n = tl.arange(0, HEAD_DIM)
  # load
  o = tl.load(O + off_hz * HEAD_DIM * N_CTX + off_m[:, None] * HEAD_DIM + off_n[None, :])
  do = tl.load(DO + off_hz * HEAD_DIM * N_CTX + off_m[:, None] * HEAD_DIM + off_n[None, :]).to(tl.float32)
  delta = tl.sum(o * do, axis=1)
  # write-back
  tl.store(Delta + off_hz * N_CTX + off_m, delta)


# The main inner-loop logic for computing dK and dV.
@triton.jit
def _attn_bwd_dkdv(dk, dv,  #
                   Q, k, v, sm_scale,  #
                   DO,  #
                   M, D,  #
                   # shared by Q/K/V/DO.
                   stride_tok, stride_d,  #
                   H, N_CTX, BLOCK_M1: tl.constexpr,  #
                   BLOCK_N1: tl.constexpr,  #
                   HEAD_DIM: tl.constexpr,  #
                   # Filled in by the wrapper.
                   start_n, start_m, num_steps,  #
                   MASK: tl.constexpr):
  offs_m = start_m + tl.arange(0, BLOCK_M1)
  offs_n = start_n + tl.arange(0, BLOCK_N1)
  offs_k = tl.arange(0, HEAD_DIM)
  qT_ptrs = Q + offs_m[None, :] * stride_tok + offs_k[:, None] * stride_d
  do_ptrs = DO + offs_m[:, None] * stride_tok + offs_k[None, :] * stride_d
  # BLOCK_N1 must be a multiple of BLOCK_M1, otherwise the code wouldn't work.
  tl.static_assert(BLOCK_N1 % BLOCK_M1 == 0)
  curr_m = start_m
  step_m = BLOCK_M1
  for blk_idx in range(num_steps):
    qT = tl.load(qT_ptrs)
    # Load m before computing qk to reduce pipeline stall.
    offs_m = curr_m + tl.arange(0, BLOCK_M1)
    m = tl.load(M + offs_m)
    qkT = tl.dot(k, qT)
    pT = tl.math.exp2(qkT - m[None, :])
    # Autoregressive masking.
    if MASK:
      mask = (offs_m[None, :] >= offs_n[:, None])
      pT = tl.where(mask, pT, 0.0)
    do = tl.load(do_ptrs)
    # Compute dV.
    ppT = pT
    ppT = ppT.to(tl.float16)
    dv += tl.dot(ppT, do)
    # D (= delta) is pre-divided by ds_scale.
    Di = tl.load(D + offs_m)
    # Compute dP and dS.
    dpT = tl.dot(v, tl.trans(do)).to(tl.float32)
    dsT = pT * (dpT - Di[None, :])
    dsT = dsT.to(tl.float16)
    dk += tl.dot(dsT, tl.trans(qT))
    # Increment pointers.
    curr_m += step_m
    qT_ptrs += step_m * stride_tok
    do_ptrs += step_m * stride_tok
  return dk, dv


# the main inner-loop logic for computing dQ
@triton.jit
def _attn_bwd_dq(dq, q, K, V,  #
                 do, m, D,
                 # shared by Q/K/V/DO.
                 stride_tok, stride_d,  #
                 H, N_CTX,  #
                 BLOCK_M2: tl.constexpr,  #
                 BLOCK_N2: tl.constexpr,  #
                 HEAD_DIM: tl.constexpr,
                 # Filled in by the wrapper.
                 start_m, start_n, num_steps,  #
                 MASK: tl.constexpr):
  offs_m = start_m + tl.arange(0, BLOCK_M2)
  offs_n = start_n + tl.arange(0, BLOCK_N2)
  offs_k = tl.arange(0, HEAD_DIM)
  kT_ptrs = K + offs_n[None, :] * stride_tok + offs_k[:, None] * stride_d
  vT_ptrs = V + offs_n[None, :] * stride_tok + offs_k[:, None] * stride_d
  # D (= delta) is pre-divided by ds_scale.
  Di = tl.load(D + offs_m)
  # BLOCK_M2 must be a multiple of BLOCK_N2, otherwise the code wouldn't work.
  tl.static_assert(BLOCK_M2 % BLOCK_N2 == 0)
  curr_n = start_n
  step_n = BLOCK_N2
  for blk_idx in range(num_steps):
    kT = tl.load(kT_ptrs)
    vT = tl.load(vT_ptrs)
    qk = tl.dot(q, kT)
    p = tl.math.exp2(qk - m)
    # Autoregressive masking.
    if MASK:
      offs_n = curr_n + tl.arange(0, BLOCK_N2)
      mask = (offs_m[:, None] >= offs_n[None, :])
      p = tl.where(mask, p, 0.0)
    # Compute dP and dS.
    dp = tl.dot(do, vT).to(tl.float32)
    ds = p * (dp - Di[:, None])
    ds = ds.to(tl.float16)
    # Compute dQ.
    # NOTE: We need to de-scale dq in the end, because kT was pre-scaled.
    dq += tl.dot(ds, tl.trans(kT))
    # Increment pointers.
    curr_n += step_n
    kT_ptrs += step_n * stride_tok
    vT_ptrs += step_n * stride_tok
  return dq


@triton.jit
def _attn_bwd(Q, K, V, sm_scale,  #
              DO,  #
              DQ, DK, DV,  #
              M, D,
              # shared by Q/K/V/DO.
              stride_z, stride_h, stride_tok, stride_d,  #
              H, N_CTX,  #
              BLOCK_M1: tl.constexpr,  #
              BLOCK_N1: tl.constexpr,  #
              BLOCK_M2: tl.constexpr,  #
              BLOCK_N2: tl.constexpr,  #
              BLK_SLICE_FACTOR: tl.constexpr,  #
              HEAD_DIM: tl.constexpr):
  LN2: tl.constexpr = 0.6931471824645996  # = ln(2)

  bhid = tl.program_id(2)
  off_chz = (bhid * N_CTX).to(tl.int64)
  adj = (stride_h * (bhid % H) + stride_z * (bhid // H)).to(tl.int64)
  pid = tl.program_id(0)

  # offset pointers for batch/head
  Q += adj
  K += adj
  V += adj
  DO += adj
  DQ += adj
  DK += adj
  DV += adj
  M += off_chz
  D += off_chz

  # load scales
  offs_k = tl.arange(0, HEAD_DIM)

  start_n = pid * BLOCK_N1
  start_m = start_n

  MASK_BLOCK_M1: tl.constexpr = BLOCK_M1 // BLK_SLICE_FACTOR
  offs_n = start_n + tl.arange(0, BLOCK_N1)

  dv = tl.zeros([BLOCK_N1, HEAD_DIM], dtype=tl.float32)
  dk = tl.zeros([BLOCK_N1, HEAD_DIM], dtype=tl.float32)

  # load K and V: they stay in SRAM throughout the inner loop.
  k = tl.load(K + offs_n[:, None] * stride_tok + offs_k[None, :] * stride_d)
  v = tl.load(V + offs_n[:, None] * stride_tok + offs_k[None, :] * stride_d)

  num_steps = BLOCK_N1 // MASK_BLOCK_M1

  dk, dv = _attn_bwd_dkdv(dk, dv,  #
                          Q, k, v, sm_scale,  #
                          DO,  #
                          M, D,  #
                          stride_tok, stride_d,  #
                          H, N_CTX,  #
                          MASK_BLOCK_M1, BLOCK_N1, HEAD_DIM,  #
                          start_n, start_m, num_steps,  #
                          MASK=True  #
                          )

  start_m += num_steps * MASK_BLOCK_M1
  num_steps = (N_CTX - start_m) // BLOCK_M1

  # Compute dK and dV for non-masked blocks.
  dk, dv = _attn_bwd_dkdv(  #
    dk, dv,  #
    Q, k, v, sm_scale,  #
    DO,  #
    M, D,  #
    stride_tok, stride_d,  #
    H, N_CTX,  #
    BLOCK_M1, BLOCK_N1, HEAD_DIM,  #
    start_n, start_m, num_steps,  #
    MASK=False  #
  )

  dv_ptrs = DV + offs_n[:, None] * stride_tok + offs_k[None, :] * stride_d
  tl.store(dv_ptrs, dv)

  # Write back dK.
  dk *= sm_scale
  dk_ptrs = DK + offs_n[:, None] * stride_tok + offs_k[None, :] * stride_d
  tl.store(dk_ptrs, dk)

  # THIS BLOCK DOES DQ:
  start_m = pid * BLOCK_M2
  end_n = start_m + BLOCK_M2

  MASK_BLOCK_N2: tl.constexpr = BLOCK_N2 // BLK_SLICE_FACTOR
  offs_m = start_m + tl.arange(0, BLOCK_M2)

  q = tl.load(Q + offs_m[:, None] * stride_tok + offs_k[None, :] * stride_d)
  dq = tl.zeros([BLOCK_M2, HEAD_DIM], dtype=tl.float32)
  do = tl.load(DO + offs_m[:, None] * stride_tok + offs_k[None, :] * stride_d)

  m = tl.load(M + offs_m)
  m = m[:, None]

  # Compute dQ for masked (diagonal) blocks.
  # NOTE: This code scans each row of QK^T backward (from right to left,
  # but inside each call to _attn_bwd_dq, from left to right), but that's
  # not due to anything important.  I just wanted to reuse the loop
  # structure for dK & dV above as much as possible.
  num_steps = BLOCK_M2 // MASK_BLOCK_N2
  dq = _attn_bwd_dq(dq, q, K, V,  #
                    do, m, D,  #
                    stride_tok, stride_d,  #
                    H, N_CTX,  #
                    BLOCK_M2, MASK_BLOCK_N2, HEAD_DIM,  #
                    start_m, end_n - num_steps * MASK_BLOCK_N2, num_steps,  #
                    MASK=True  #
                    )
  end_n -= num_steps * MASK_BLOCK_N2
  # stage 2
  num_steps = end_n // BLOCK_N2
  dq = _attn_bwd_dq(dq, q, K, V,  #
                    do, m, D,  #
                    stride_tok, stride_d,  #
                    H, N_CTX,  #
                    BLOCK_M2, BLOCK_N2, HEAD_DIM,  #
                    start_m, end_n - num_steps * BLOCK_N2, num_steps,  #
                    MASK=False  #
                    )
  # Write back dQ.
  dq_ptrs = DQ + offs_m[:, None] * stride_tok + offs_k[None, :] * stride_d
  dq *= LN2
  tl.store(dq_ptrs, dq)


class _attention(torch.autograd.Function):

  @staticmethod
  def forward(ctx, q, k, v, causal, sm_scale, USE_TMA=True):
    # shape constraints
    HEAD_DIM_Q, HEAD_DIM_K = q.shape[-1], k.shape[-1]
    # when v is in float8_e5m2 it is transposed.
    HEAD_DIM_V = v.shape[-1]
    assert HEAD_DIM_Q == HEAD_DIM_K and HEAD_DIM_K == HEAD_DIM_V
    assert HEAD_DIM_K in {16, 32, 64, 128, 256}
    o = torch.empty_like(q)
    stage = 3 if causal else 1
    extra_kern_args = {}
    # Tuning for AMD target
    if is_hip():
      waves_per_eu = 3 if HEAD_DIM_K <= 64 else 2
      extra_kern_args = {"waves_per_eu": waves_per_eu, "allow_flush_denorm": True}

    M = torch.empty((q.shape[0], q.shape[1], q.shape[2]), device=q.device, dtype=torch.float32)
    if USE_TMA and supports_tma() and not (torch.cuda.get_device_capability()[0] == 9
                                           and q.dtype == torch.float8_e5m2):
      # Note that on Hopper we cannot perform a FP8 dot with a non-transposed second tensor
      y_dim = q.shape[0] * q.shape[1] * q.shape[2]

      dummy_block = [1, 1]
      # dummy_block 只是初始值，实际的 block_shape 会在 autotune 的 pre_hook ( _tma_pre_hook ) 中根据调优参数设置。
      desc_q = TensorDescriptor(q, shape=[y_dim, HEAD_DIM_K], strides=[HEAD_DIM_K, 1], block_shape=dummy_block)
      desc_v = TensorDescriptor(v, shape=[y_dim, HEAD_DIM_K], strides=[HEAD_DIM_K, 1], block_shape=dummy_block)
      desc_k = TensorDescriptor(k, shape=[y_dim, HEAD_DIM_K], strides=[HEAD_DIM_K, 1], block_shape=dummy_block)
      desc_o = TensorDescriptor(o, shape=[y_dim, HEAD_DIM_K], strides=[HEAD_DIM_K, 1], block_shape=dummy_block)

      def grid(META):
        return (triton.cdiv(q.shape[2], META["BLOCK_M"]), q.shape[0] * q.shape[1], 1)

      ctx.grid = grid
      _attn_fwd_tma[grid](
        sm_scale, M,  #
        q.shape[0], q.shape[1],  #
        desc_q, desc_k, desc_v, desc_o,  #
        N_CTX=q.shape[2],  #
        HEAD_DIM=HEAD_DIM_K,  #
        FP8_OUTPUT=q.dtype == torch.float8_e5m2,  #
        STAGE=stage,  #
        **extra_kern_args)
    else:
      grid = lambda args: (triton.cdiv(q.shape[2], args["BLOCK_M"]), q.shape[0] * q.shape[1], 1) # BLOCK_M ~ seq_len, batch*head, 1
      ctx.grid = grid
      _attn_fwd[grid](
        q, k, v, sm_scale, M, o,  #
        q.stride(0), q.stride(1), q.stride(2), q.stride(3),  #
        k.stride(0), k.stride(1), k.stride(2), k.stride(3),  #
        v.stride(0), v.stride(1), v.stride(2), v.stride(3),  #
        o.stride(0), o.stride(1), o.stride(2), o.stride(3),  #
        q.shape[0], q.shape[1],  #
        N_CTX=q.shape[2],  #
        HEAD_DIM=HEAD_DIM_K,  #
        STAGE=stage,  #
        **extra_kern_args)

    ctx.save_for_backward(q, k, v, o, M)
    ctx.sm_scale = sm_scale
    ctx.HEAD_DIM = HEAD_DIM_K
    ctx.causal = causal
    return o

  @staticmethod
  def backward(ctx, do):
    q, k, v, o, M = ctx.saved_tensors
    assert do.is_contiguous()
    assert q.stride() == k.stride() == v.stride() == o.stride() == do.stride()
    dq = torch.empty_like(q)
    dk = torch.empty_like(k)
    dv = torch.empty_like(v)
    BATCH, N_HEAD, N_CTX = q.shape[:3]

    PRE_BLOCK = 128
    assert N_CTX % PRE_BLOCK == 0
    pre_grid = (N_CTX // PRE_BLOCK, BATCH * N_HEAD)
    delta = torch.empty_like(M)
    _attn_bwd_preprocess[pre_grid](
      o, do,  #
      delta,  #
      BATCH, N_HEAD, N_CTX,  #
      BLOCK_M=PRE_BLOCK, HEAD_DIM=ctx.HEAD_DIM  #
    )

    NUM_WARPS, NUM_STAGES = 4, 5
    BLOCK_M1, BLOCK_N1, BLOCK_M2, BLOCK_N2 = 32, 128, 128, 32
    BLK_SLICE_FACTOR = 2
    RCP_LN2 = 1.4426950408889634  # = 1.0 / ln(2)
    arg_k = k
    arg_k = arg_k * (ctx.sm_scale * RCP_LN2)
    grid = (N_CTX // BLOCK_N1, 1, BATCH * N_HEAD)
    _attn_bwd[grid](
      q, arg_k, v, ctx.sm_scale, do, dq, dk, dv,  #
      M, delta,  #
      q.stride(0), q.stride(1), q.stride(2), q.stride(3),  #
      N_HEAD, N_CTX,  #
      BLOCK_M1=BLOCK_M1, BLOCK_N1=BLOCK_N1,  #
      BLOCK_M2=BLOCK_M2, BLOCK_N2=BLOCK_N2,  #
      BLK_SLICE_FACTOR=BLK_SLICE_FACTOR,  #
      HEAD_DIM=ctx.HEAD_DIM,  #
      num_warps=NUM_WARPS,  #
      num_stages=NUM_STAGES  #
    )

    return dq, dk, dv, None, None


attention = _attention.apply


@pytest.mark.parametrize("Z, H, N_CTX, HEAD_DIM", [(1, 2, 1024, 64)])
@pytest.mark.parametrize("causal", [True])
def test_op(Z, H, N_CTX, HEAD_DIM, causal, dtype=torch.float16):
  torch.manual_seed(20)
  q = (torch.empty((Z, H, N_CTX, HEAD_DIM), dtype=dtype, device=DEVICE).normal_(mean=0.0, std=0.5).requires_grad_())
  k = (torch.empty((Z, H, N_CTX, HEAD_DIM), dtype=dtype, device=DEVICE).normal_(mean=0.0, std=0.5).requires_grad_())
  v = (torch.empty((Z, H, N_CTX, HEAD_DIM), dtype=dtype, device=DEVICE).normal_(mean=0.0, std=0.5).requires_grad_())
  sm_scale = HEAD_DIM ** -0.5
  dout = torch.randn_like(q)
  # reference implementation
  M = torch.tril(torch.ones((N_CTX, N_CTX), device=DEVICE))
  p = torch.matmul(q, k.transpose(2, 3)) * sm_scale
  if causal:
    p[:, :, M == 0] = float("-inf")
  p = torch.softmax(p.float(), dim=-1).half()
  # p = torch.exp(p)
  ref_out = torch.matmul(p, v)
  ref_out.backward(dout)
  ref_dv, v.grad = v.grad.clone(), None
  ref_dk, k.grad = k.grad.clone(), None
  ref_dq, q.grad = q.grad.clone(), None

  # triton implementation
  tri_out = attention(q, k, v, causal, sm_scale).half()
  tri_out.backward(dout)
  tri_dv, v.grad = v.grad.clone(), None
  tri_dk, k.grad = k.grad.clone(), None
  tri_dq, q.grad = q.grad.clone(), None

  # triton implementation
  torch_out = torch.nn.functional.scaled_dot_product_attention(q, k, v, attn_mask=None, is_causal=causal).half()
  torch_out.backward(dout)
  torch_dv, v.grad = v.grad.clone(), None
  torch_dk, k.grad = k.grad.clone(), None
  torch_dq, q.grad = q.grad.clone(), None


  # compare
  assert torch.allclose(ref_out, tri_out, atol=1e-2, rtol=0)
  rtol = 0.0
  # Relative tolerance workaround for known hardware limitation of CDNA2 GPU.
  # For details see https://pytorch.org/docs/stable/notes/numerical_accuracy.html#reduced-precision-fp16-and-bf16-gemms-and-convolutions-on-amd-instinct-mi200-devices
  if torch.version.hip is not None and triton.runtime.driver.active.get_current_target().arch == "gfx90a":
    rtol = 1e-2
  assert torch.allclose(ref_dv, tri_dv, atol=1e-2, rtol=rtol)
  assert torch.allclose(ref_dk, tri_dk, atol=1e-2, rtol=rtol)
  assert torch.allclose(ref_dq, tri_dq, atol=1e-2, rtol=rtol)

  # compare
  assert torch.allclose(ref_out, torch_out, atol=1e-2, rtol=0)
  rtol = 0.0
  if torch.version.hip is not None and triton.runtime.driver.active.get_current_target().arch == "gfx90a":
    rtol = 1e-2
  assert torch.allclose(ref_dv, torch_dv, atol=1e-2, rtol=rtol)
  assert torch.allclose(ref_dk, torch_dk, atol=1e-2, rtol=rtol)
  assert torch.allclose(ref_dq, torch_dq, atol=1e-2, rtol=rtol)


try:
  from flash_attn.flash_attn_interface import \
    flash_attn_qkvpacked_func as flash_attn_func
  HAS_FLASH = True
except BaseException:
  HAS_FLASH = False

TORCH_HAS_FP8 = hasattr(torch, 'float8_e5m2')
BATCH, N_HEADS, HEAD_DIM = 4, 32, 64
# vary seq length for fixed head and batch=4
configs = []
for mode in ["fwd", "bwd"]:
  for causal in [True, False]:
    if mode == "bwd" and not causal:
      continue
    configs.append(
      triton.testing.Benchmark(
        x_names=["N_CTX"],
        x_vals=[2**i for i in range(10, 15)],
        line_arg="provider",
        line_vals=["triton-fp16"] + (["triton-fp8"] if TORCH_HAS_FP8 else []) +
                  (["flash"] if HAS_FLASH else []) + ["torch"],
        line_names=["Triton [FP16]"] + (["Triton [FP8]"] if TORCH_HAS_FP8 else []) +
                   (["Flash-2"] if HAS_FLASH else []) + ["Torch"],
        styles=[("red", "-"), ("blue", "-"), ("green", "-"), ("orange", "-")],
        ylabel="TFLOPS",
        plot_name=f"fused-attention-batch{BATCH}-head{N_HEADS}-d{HEAD_DIM}-{mode}-causal={causal}(TFLOPS)",
        args={
          "H": N_HEADS,
          "BATCH": BATCH,
          "HEAD_DIM": HEAD_DIM,
          "mode": mode,
          "causal": causal,
        },
      ))


@triton.testing.perf_report(configs)
def bench_flash_attention(BATCH, H, N_CTX, HEAD_DIM, causal, mode, provider, device=DEVICE):
  assert mode in ["fwd", "bwd"]
  dtype = torch.float16
  if "triton" in provider:
    q = torch.randn((BATCH, H, N_CTX, HEAD_DIM), dtype=dtype, device=device, requires_grad=True)
    k = torch.randn((BATCH, H, N_CTX, HEAD_DIM), dtype=dtype, device=device, requires_grad=True)
    v = torch.randn((BATCH, H, N_CTX, HEAD_DIM), dtype=dtype, device=device, requires_grad=True)
    if mode == "fwd" and "fp8" in provider:
      q = q.to(torch.float8_e5m2)
      k = k.to(torch.float8_e5m2)
      v = v.permute(0, 1, 3, 2).contiguous()
      v = v.permute(0, 1, 3, 2)
      v = v.to(torch.float8_e5m2)
    sm_scale = 1.3
    fn = lambda: attention(q, k, v, causal, sm_scale)
    if mode == "bwd":
      o = fn()
      do = torch.randn_like(o)
      fn = lambda: o.backward(do, retain_graph=True)
    ms = triton.testing.do_bench(fn)
  elif provider == "flash":
    qkv = torch.randn((BATCH, N_CTX, 3, H, HEAD_DIM), dtype=dtype, device=device, requires_grad=True)
    fn = lambda: flash_attn_func(qkv, causal=causal)
    if mode == "bwd":
      o = fn()
      do = torch.randn_like(o)
      fn = lambda: o.backward(do, retain_graph=True)
    ms = triton.testing.do_bench(fn)
  elif provider == "torch":
    q = torch.randn((BATCH, H, N_CTX, HEAD_DIM), dtype=dtype, device=device, requires_grad=True)
    k = torch.randn((BATCH, H, N_CTX, HEAD_DIM), dtype=dtype, device=device, requires_grad=True)
    v = torch.randn((BATCH, H, N_CTX, HEAD_DIM), dtype=dtype, device=device, requires_grad=True)
    fn = lambda: torch.nn.functional.scaled_dot_product_attention(q, k, v, attn_mask=None, is_causal=causal)
    if mode == "bwd":
      o = fn()
      do = torch.randn_like(o)
      fn = lambda: o.backward(do, retain_graph=True)
    ms = triton.testing.do_bench(fn)
  else:
    raise ValueError(f"Unknown provider {provider}")
  flops_per_matmul = 2.0 * BATCH * H * N_CTX * N_CTX * HEAD_DIM
  total_flops = 2 * flops_per_matmul
  if causal:
    total_flops *= 0.5
  if mode == "bwd":
    total_flops *= 2.5  # 2.0(bwd) + 0.5(recompute)
  return total_flops * 1e-12 / (ms * 1e-3)


### 简化版 —— flash attn v1/v2

@triton.jit
def flash_attention_v2_kernel(
    # 输入指针
    q_ptr,      # Query 矩阵指针
    k_ptr,      # Key 矩阵指针
    v_ptr,      # Value 矩阵指针
    o_ptr,      # 输出矩阵指针

    # Q 矩阵的步长
    q_batch_stride,    # batch 维度的步长
    q_heads_stride,    # heads 维度的步长
    q_seq_stride,      # 序列维度的步长
    q_dim_stride,      # head_dim 维度的步长

    # K 矩阵的步长
    k_batch_stride,
    k_heads_stride,
    k_seq_stride,
    k_dim_stride,      # matrix K stride for columns, [seq_len, head_dim]

    # V 矩阵的步长
    v_batch_stride,
    v_heads_stride,
    v_seq_stride,
    v_dim_stride,

    # 输出矩阵的步长
    out_batch_stride,
    out_heads_stride,
    out_seq_stride,
    out_dim_stride,

    # 其他参数
    n_heads,           # 注意力头数量
    m_size,           # Q 矩阵的序列长度
    n_size,           # K/V 矩阵的序列长度
    BLOCK_DHEAD_SIZE: tl.constexpr,  # head_dim 维度的块大小
    BLOCK_M_SIZE: tl.constexpr,      # Q 序列维度的块大小
    BLOCK_N_SIZE: tl.constexpr,      # K/V 序列维度的块大小
    sm_scale,         # 注意力分数的缩放因子 1/sqrt(head_dim)
):
  """Flash Attention V1 的 CUDA kernel 实现

  参数:
      q_ptr, k_ptr, v_ptr: 输入矩阵的指针
      o_ptr: 输出矩阵的指针
      *_stride: 各个维度的步长
      n_heads: 注意力头数量
      m_size: Q 矩阵的序列长度
      n_size: K/V 矩阵的序列长度
      BLOCK_*_SIZE: 各个维度的块大小
      sm_scale: 注意力分数的缩放因子
  """

  # 获取当前程序块的索引
  block_m_idx = tl.program_id(0)  # 序列维度的块索引
  head_idx = tl.program_id(1)     # batch * heads 维度的索引

  # 计算当前处理的 batch 和 head 索引
  cur_batch_idx = head_idx // n_heads
  cur_head_idx = head_idx % n_heads

  # 生成各个维度的偏移量
  m_range_offs = tl.arange(0, BLOCK_M_SIZE)      # Q 矩阵行偏移
  n_range_offs = tl.arange(0, BLOCK_N_SIZE)      # K 矩阵行偏移
  dhead_range_offs = tl.arange(0, BLOCK_DHEAD_SIZE)  # head_dim 维度偏移

  # 计算 Q 矩阵当前块的实际行索引
  m_offs = block_m_idx * BLOCK_M_SIZE + m_range_offs

  # 计算各个矩阵在内存中的偏移地址
  ## m_offs[:, None] 这一操作利用了索引技巧来增加 m_offs 张量的维度。
  q_offs = (
      cur_batch_idx * q_batch_stride +
      cur_head_idx * q_heads_stride +
      (m_offs[:, None] * q_seq_stride + dhead_range_offs[None, :] * q_dim_stride)
  )

  k_offs = (
      cur_batch_idx * k_batch_stride +
      cur_head_idx * k_heads_stride +
      (n_range_offs[:, None] * k_seq_stride + dhead_range_offs[None, :] * k_dim_stride)
  )

  v_offs = (
      cur_batch_idx * v_batch_stride +
      cur_head_idx * v_heads_stride +
      (n_range_offs[:, None] * v_seq_stride + dhead_range_offs[None, :] * v_dim_stride)
  )

  o_offs = (
      cur_batch_idx * out_batch_stride +
      cur_head_idx * out_heads_stride +
      (m_offs[:, None] * out_seq_stride + dhead_range_offs[None, :] * out_dim_stride)
  )

  # 计算实际的内存地址
  q_ptrs = q_ptr + q_offs
  k_ptrs = k_ptr + k_offs
  v_ptrs = v_ptr + v_offs
  out_ptrs = o_ptr + o_offs

  # 初始化 online softmax 所需的变量，确保存入register中
  m_i = tl.zeros((BLOCK_M_SIZE,), dtype=tl.float32) - float("inf")  # 最大值
  d_i = tl.zeros((BLOCK_M_SIZE,), dtype=tl.float32)                 # 分母
  o_i = tl.zeros((BLOCK_M_SIZE, BLOCK_DHEAD_SIZE), dtype=tl.float32)  # 累积输出

  # 加载 Q 矩阵数据
  ## 实际的序列长度 m_size 可能不是 BLOCK_M_SIZE 的整数倍
  q_mask = m_offs[:, None] < m_size
  q = tl.load(q_ptrs, mask=q_mask, other=0.0)

  # 分块处理 K、V 矩阵
  for block_n_start_idx in range(0, n_size, BLOCK_N_SIZE):
    block_n_offs = block_n_start_idx + n_range_offs
    k_mask = block_n_offs[:, None] < n_size
    k = tl.load(k_ptrs + block_n_start_idx * k_seq_stride, mask=k_mask, other=0.0)

    # 计算注意力分数 QK^T
    qk = tl.zeros((BLOCK_M_SIZE, BLOCK_N_SIZE), dtype=tl.float32)
    qk = tl.dot(q, tl.trans(k))
    qk *= sm_scale  # 缩放注意力分数

    # 计算当前块的 softmax 统计量
    m_j = tl.max(qk, 1)                        # 当前块的最大值
    n_j = tl.exp(qk - m_j[:, None])           # 计算 exp(qk - max)
    d_j = tl.sum(n_j, 1)                      # 当前块的 softmax 分母

    # 更新 softmax 统计量
    m_new = tl.maximum(m_j, m_i)              # 更新全局最大值
    alpha = tl.exp(m_i - m_new)               # 旧数据的缩放因子
    beta = tl.exp(m_j - m_new)                # 新数据的缩放因子
    d_new = alpha * d_i + beta * d_j          # 更新分母

    # 重新缩放累积的输出
    scale1 = d_i / d_new * alpha
    o_i = o_i * scale1[:, None]

    # 计算当前块的输出贡献
    p_scale = beta / d_new
    qk_softmax = n_j * p_scale[:, None]
    v_ptr_mask = block_n_offs[:, None] < n_size
    V = tl.load(v_ptrs + block_n_start_idx * v_seq_stride, mask=v_ptr_mask, other=0.0)
    o_i += tl.dot(qk_softmax, V)

    # 更新统计量
    m_i = m_new
    d_i = d_new

  # 存储最终结果
  out_mask = m_offs[:, None] < m_size
  tl.store(out_ptrs, o_i, mask=out_mask)


@torch.no_grad()
@custom_fwd(cast_inputs=torch.float16, device_type='cuda')
def flash_attention_v2(
    q: torch.Tensor,
    k: torch.Tensor,
    v: torch.Tensor,
    sm_scale,
    attention_mask: Optional[torch.Tensor] = None,
):
  """Compute Flash-attention, can't support fp32 input

  参数:
      q: Query tensor, shape: [bs, n_heads, m_size, head_dim]
         在 decode 阶段, q 的 seq_len 和 k/v 不一致, 其值为 1
      k: Key tensor, shape: [bs, n_heads, n_size, head_dim]
      v: Value tensor, shape 与 k 相同
      sm_scale: 注意力分数的缩放因子
      attention_mask: 注意力掩码矩阵，可广播至 (batch, head_size, m_size, n_size)

  返回:
      output: 注意力输出张量，shape 与 q 相同
  """
  # 创建输出张量
  output = torch.empty_like(q)

  # 检查输入维度和类型
  assert q.shape[-1] == k.shape[-1] == v.shape[-1]
  assert (
      q.dtype == k.dtype == v.dtype == output.dtype
  ), f"All tensors must have the same dtype: {q.dtype}, {k.dtype}, {v.dtype}, {output.dtype}"

  # 获取输入张量的维度
  bs, n_heads, m_size, head_dim = q.size()
  n_size = k.shape[2]

  # 定义计算网格
  ## grid的0维 和 block_m_idx = tl.program_id(0) 对应
  grid = lambda meta: (
    triton.cdiv(m_size, meta["BLOCK_M_SIZE"]),  # 序列维度的块数
    bs * n_heads,                                # batch 和 head 维度的总数
    1
  )

  # 启动 kernel 计算
  flash_attention_v2_kernel[grid](
    q, k, v, output,
    *q.stride(),      # (batch, heads, m_size, head_dim)
    *k.stride(),      # (batch, heads, n_size, head_dim)
    *v.stride(),      # (batch, heads, n_size, head_dim)
    *output.stride(), # (batch, heads, m_size, n_size)
    n_heads,
    m_size,
    n_size,
    head_dim,
    64,              # BLOCK_M_SIZE
    64,              # BLOCK_N_SIZE
    sm_scale
  )
  return output


if __name__ == "__main__":
  pytest.main(["-x", __file__])
  # only works on post-Ampere GPUs right now
  bench_flash_attention.run(save_path=".", print_data=True)