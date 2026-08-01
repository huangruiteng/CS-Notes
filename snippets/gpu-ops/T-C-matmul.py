# TODO(huangruiteng):
# 1. integrate cuda-sgemm.cu
# 2. integrate cutlass/python/README.md
# 3. cutlass https://pytorch.org/blog/cutlass-ping-pong-gemm-kernel/


# matmul-performance-matrix-size(gbps):
#    square_matrix_size      Naive    Grouped  Grouped & Auto-Tuned  Grouped & Auto-Tuned (Leaky ReLU)       Torch  Torch-Compiled (dynamic=None)  Torch-Compiled (dynamic=True)  Torch-Compiled (dynamic=False)  Numpy-Broadcast  Cuda-Naive  Cuda-Shared     Numba  Grouped & Auto-Tuned & FP16  Torch-FP16  Torch-FP32-Cast16  Torch-FP16-Cast16-Compiled (dynamic=False)  Grouped-FP8
# 0                32.0   2.086956   2.098361              1.949239                           1.949239    1.699115                       0.440873                       0.399584                        1.714286         0.013409    1.376344     1.560976  0.089993                     2.042553    1.989637           1.072626                                    0.590769     2.206897
# 1                64.0   7.492683   7.211267              7.314286                           7.349282    5.862596                       1.837321                       1.613445                        5.885057         0.026114    4.208219     5.260274  0.373450                     7.603961    7.796954           4.585075                                    2.549378     7.718593
# 2               128.0  14.663485  23.722008             25.924051                          26.033898   18.070588                       6.973893                       6.218624                       18.070588         0.051775   12.023484    16.471850  1.465649                    28.444444   28.576745          17.405099                                   10.538593    26.829695
# 3               256.0  62.060608  62.217720             69.423731                          70.620689   64.335079                      32.041720                      27.382729                       64.167101         0.102760   30.378245    43.497346  5.390656                   101.135802  103.696202          63.503875                                   30.044010    79.022505
# 4               512.0  59.904935  59.506053            137.873770                         137.296093  128.166881                      98.599797                      88.086022                      128.334202         0.197396   32.954745    44.421146  8.838698                   333.233892  252.061538         176.172043                                  162.485948   118.868197
# 5              1024.0  35.504830  35.479201            109.135721                         103.260507  130.333447                     129.688653                     130.290261                      130.290261         0.369252   20.625020    27.445802  4.921721                   497.112498  447.344710         332.670041                                  338.979315    82.125311
# 6              2048.0  18.231243  18.247952             64.663049                          62.269450   71.708942                      71.692602                      71.725297                       71.722025         0.746988   10.966609    14.289022  2.505494                   369.650761  316.854145         279.421577                                  281.320696    43.466094
 
# * Block-level matrix multiplications.

# * Multi-dimensional pointer arithmetic.

# * Program re-ordering for improved L2 cache hit rate.

# * Automatic performance tuning.

# Analysis:
# - shared memory: 128k/2k -> 64
# - threads: 1536/256 -> 6

# SGEMM walkthrough: https://github.com/NervanaSystems/maxas/wiki/SGEMM

import os
import numpy as np

# os.environ['TRITON_INTERPRET'] = '1' # make sure set it before import triton
# os.environ['NUMBA_ENABLE_CUDASIM'] = '1' # 目前无法开启，有报错

import triton
import triton.language as tl
import torch

np.set_printoptions(precision=2, linewidth=140)
torch.set_printoptions(precision=2, linewidth=140, sci_mode=False)
np.seterr(all="warn")

from gpu_kernel_utils import (cdiv, breakpoint_if, print_if,
                              check_tensors_gpu_ready, get_1d_offset,
                              get_2d_offset, get_1d_mask, get_2d_mask,
                              load_cuda, cuda_begin, is_cuda, is_hip_cdna2,
                              RTOL, check_implementation)
from functools import partial


def matmul(a, b, matmul_k_fn, bs=16, GROUP_SZ=None, activation=''):
  assert a.shape[1] == b.shape[0], "matrix dims not compatible for matmul"
  check_tensors_gpu_ready(a, b)
  (M, K), (_, N) = a.shape, b.shape
  c = torch.empty((M, N), device=a.device, dtype=a.dtype)
  grid = lambda meta: (triton.cdiv(M, meta["BM"]), triton.cdiv(N, meta["BN"]))
  GROUP_SZ = ({} if GROUP_SZ is None else {
    "GROUP_SZ": GROUP_SZ
  })  # not used in naive_matmul, but will be in grouped_matmul further below
  matmul_k_fn[grid](a,
                    b,
                    c,
                    M,
                    N,
                    K,
                    a.stride(0),
                    a.stride(1),
                    b.stride(0),
                    b.stride(1),
                    c.stride(0),
                    c.stride(1),
                    BM=bs,
                    BN=bs,
                    BK=bs,
                    **GROUP_SZ,
                    ACTIVATION=activation)
  return c


@triton.jit
def naive_matmul_k(a_ptr, b_ptr, c_ptr, M, N, K, stride_am, stride_ak,
                   stride_bk, stride_bn, stride_cm, stride_cn, BM: tl.constexpr,
                   BN: tl.constexpr, BK: tl.constexpr,
                   ACTIVATION: tl.constexpr):
  pid_m, pid_n = tl.program_id(0), tl.program_id(1)
  # chunks along m/n/k dimensions
  rm = get_1d_offset(size=BM, n_prev_chunks=pid_m)
  rn = get_1d_offset(size=BN, n_prev_chunks=pid_n)
  rk = get_1d_offset(size=BK, n_prev_chunks=0)
  # relevant offsets of a, b
  a_ptrs = a_ptr + get_2d_offset(rm, rk, stride_am, stride_ak)
  b_ptrs = b_ptr + get_2d_offset(rk, rn, stride_bk, stride_bn)
  # initialize and iteratively update accumulator
  acc = tl.zeros((BM, BN), dtype=tl.float32)
  for k in range(0, tl.cdiv(K, BK)):
    tmp_rk = get_1d_offset(size=BK, n_prev_chunks=k)
    a = tl.load(a_ptrs, mask=get_2d_mask(rm, tmp_rk, M, K), other=0.0)
    b = tl.load(b_ptrs, mask=get_2d_mask(tmp_rk, rn, K, N), other=0.0)
    acc += tl.dot(
      a, b, allow_tf32=(a.dtype != tl.float32)
    )  # matmul in block ; Weirdness: allow_tf32 must be set to False for older GPUs, otherwise won't compile
    # allow_tf32=False when fp32, True when fp16/fp8
    a_ptrs += BK * stride_ak
    b_ptrs += BK * stride_bk
  c = c_ptr + get_2d_offset(rm, rn, stride_cm, stride_cn)
  mask = get_2d_mask(rm, rn, M, N)
  tl.store(c, acc, mask=mask)


naive_matmul = partial(matmul, matmul_k_fn=naive_matmul_k)

torch.manual_seed(0)
a = torch.randn((511, 513), device="cuda", dtype=torch.float32)
b = torch.randn((513, 1231), device="cuda", dtype=torch.float32)


@triton.jit
def leaky_relu(x):
  return tl.where(x >= 0, x, 0.01 * x)


@triton.jit
def swizzle_k(x_ptr, z_ptr, GROUP_SZ: tl.constexpr):
  pid_m, pid_n = tl.program_id(0), tl.program_id(1)
  num_pid_m, num_pid_n = tl.num_programs(0), tl.num_programs(1)

  pid_m_, pid_n_ = tl.swizzle2d(
    pid_m, pid_n, num_pid_m, num_pid_n,
    GROUP_SZ)  # Weirdness: tl.swizzle2d doesn't work when simulating on CPU

  offs_m = get_1d_offset(1, n_prev_chunks=pid_m)
  offs_n = get_1d_offset(1, n_prev_chunks=pid_n)

  offs = get_2d_offset(offs_m, offs_n, stride_0=num_pid_n)
  mask = get_2d_mask(offs_m, offs_n, max_0=num_pid_m, max_1=num_pid_n)

  offs_sw_m = get_1d_offset(1, n_prev_chunks=pid_m_)
  offs_sw_n = get_1d_offset(1, n_prev_chunks=pid_n_)

  offs_sw = get_2d_offset(offs_sw_m, offs_sw_n, stride_0=num_pid_n)
  mask_sw = get_2d_mask(offs_sw_m, offs_sw_n, max_0=num_pid_m, max_1=num_pid_n)

  x = tl.load(x_ptr + offs, mask=mask)
  tl.store(z_ptr + offs_sw, x, mask=mask_sw)


blocks_m, blocks_n = 5, 4
x = torch.arange(blocks_m * blocks_n, device="cuda").view(blocks_m, blocks_n)
print(x)
z = -torch.ones_like(x)
swizzle_k[(blocks_m, blocks_n)](x, z, GROUP_SZ=3)
print(z)


@triton.autotune(
  # Choices of configs to auto-tune over
  configs=[
    triton.Config({
      "BM": 128,
      "BN": 256,
      "BK": 64,
      "GROUP_SZ": 8
    },
      num_stages=3,
      num_warps=8),
    triton.Config({
      "BM": 64,
      "BN": 256,
      "BK": 32,
      "GROUP_SZ": 8
    },
      num_stages=4,
      num_warps=4),
    triton.Config({
      "BM": 128,
      "BN": 128,
      "BK": 32,
      "GROUP_SZ": 8
    },
      num_stages=4,
      num_warps=4),
    triton.Config({
      "BM": 128,
      "BN": 64,
      "BK": 32,
      "GROUP_SZ": 8
    },
      num_stages=4,
      num_warps=4),
    triton.Config({
      "BM": 64,
      "BN": 128,
      "BK": 32,
      "GROUP_SZ": 8
    },
      num_stages=4,
      num_warps=4),
    triton.Config({
      "BM": 128,
      "BN": 32,
      "BK": 32,
      "GROUP_SZ": 8
    },
      num_stages=4,
      num_warps=4),
    triton.Config({
      "BM": 64,
      "BN": 32,
      "BK": 32,
      "GROUP_SZ": 8
    },
      num_stages=5,
      num_warps=2),
    triton.Config({
      "BM": 32,
      "BN": 64,
      "BK": 32,
      "GROUP_SZ": 8
    },
      num_stages=5,
      num_warps=2),
  ],
  # Definition of problem size. If it changes, a new auto-tune is run for the new problem size.
  key=["m", "n", "k"],
)
@triton.jit
def grouped_autotuned_matmul_k(
    a_ptr,
    b_ptr,
    c_ptr,
    M,
    N,
    K,
    stride_am,
    stride_ak,
    stride_bk,
    stride_bn,
    stride_cm,
    stride_cn,
    BM: tl.constexpr,
    BN: tl.constexpr,
    BK: tl.constexpr,
    GROUP_SZ: tl.constexpr,
    ACTIVATION: tl.constexpr,
):
  grouped_matmul_k(a_ptr, b_ptr, c_ptr, M, N, K, stride_am, stride_ak,
                   stride_bk, stride_bn, stride_cm, stride_cn, BM, BN, BK,
                   GROUP_SZ, ACTIVATION)


@triton.jit
def grouped_matmul_k(
    a_ptr,
    b_ptr,
    c_ptr,
    M,
    N,
    K,
    stride_am,
    stride_ak,
    stride_bk,
    stride_bn,
    stride_cm,
    stride_cn,
    BM: tl.constexpr,
    BN: tl.constexpr,
    BK: tl.constexpr,
    GROUP_SZ: tl.constexpr,
    ACTIVATION: tl.constexpr,
):
  pid_m, pid_n = tl.program_id(0), tl.program_id(1)
  num_pid_m, num_pid_n = tl.num_programs(0), tl.num_programs(1)
  # determine location of block in grouped ordering
  pid_m, pid_n = tl.swizzle2d(
    pid_m, pid_n, num_pid_m, num_pid_n,
    GROUP_SZ)  # Weirdness: tl.swizzle2d doesn't work when simulating on CPU
  # chunks along m/n/k dimensions
  rm = get_1d_offset(size=BM, n_prev_chunks=pid_m)
  rn = get_1d_offset(size=BN, n_prev_chunks=pid_n)
  rk = get_1d_offset(size=BK, n_prev_chunks=0)
  # relevant offsets of a, b
  a_ptrs = a_ptr + get_2d_offset(rm, rk, stride_am, stride_ak)
  b_ptrs = b_ptr + get_2d_offset(rk, rn, stride_bk, stride_bn)
  # initialize and iteratively update accumulator
  acc = tl.zeros((BM, BN), dtype=tl.float32)
  for k in range(0, tl.cdiv(K, BK)):
    # todo umer: don't we need mask when loading a & b?
    tmp_rk = get_1d_offset(size=BK, n_prev_chunks=k)
    a = tl.load(a_ptrs, mask=get_2d_mask(rm, tmp_rk, M, K), other=0.0)
    b = tl.load(b_ptrs, mask=get_2d_mask(tmp_rk, rn, K, N), other=0.0)
    acc = tl.dot(
      a, b, acc, allow_tf32=(a.dtype != tl.float32)
    )  # block level matrix multiplication ; Weirdness: allow_tf32 must be set to False for older GPUs, otherwise won't compile
    # increase offets, so next iteration loads next chunks
    a_ptrs += BK * stride_ak
    b_ptrs += BK * stride_bk
  if ACTIVATION == "leaky_relu":
    acc = leaky_relu(acc)
  c = c_ptr + get_2d_offset(rm, rn, stride_cm, stride_cn)
  mask = get_2d_mask(rm, rn, M, N)
  tl.store(c, acc, mask=mask)


grouped_matmul = partial(matmul, matmul_k_fn=grouped_matmul_k)


@triton.testing.perf_report(
  triton.testing.Benchmark(
    x_names=["block_size"],
    x_vals=[2**i for i in range(4, 7, 1)],
    x_log=True,
    # > 7 makes shared memory requirement exceeds limit 232448
    line_arg="provider",
    line_vals=["naive", "grouped", "torch"],
    line_names=["Naive", "Grouped", "Torch"],
    styles=[("blue", "-"), ("green", "-"), ("orange", "-")],
    ylabel="GB/s",
    plot_name="matmul-performance-block-size",
    args={},
  ))
def benchmark_block_size(block_size, provider):
  sz = 512
  a = torch.rand((sz, sz), device="cuda", dtype=torch.float32)
  b = torch.rand((sz, sz), device="cuda", dtype=torch.float32)
  quantiles = [0.5, 0.2, 0.8]
  if provider == "naive":
    ms, min_ms, max_ms = triton.testing.do_bench(
      lambda: naive_matmul(a, b, bs=block_size), quantiles=quantiles)
  if provider == "grouped":
    ms, min_ms, max_ms = triton.testing.do_bench(
      lambda: grouped_matmul(a, b, bs=block_size, GROUP_SZ=8),
      quantiles=quantiles)
  if provider == "torch":
    ms, min_ms, max_ms = triton.testing.do_bench(lambda: torch.matmul(a, b),
                                                 quantiles=quantiles)
  gbps = lambda ms: 12 * sz / ms * 1e-6
  return gbps(ms), gbps(max_ms), gbps(min_ms)


benchmark_block_size.run(print_data=True, show_plots=True, save_path=".")


def get_hip_autotune_config():
  return [
    triton.Config(
      {
        'BM': 128,
        'BN': 256,
        'BK': 16,
        'GROUP_SZ': 1,
        'waves_per_eu': 2
      },
      num_warps=4,
      num_stages=2),
    triton.Config(
      {
        'BM': 256,
        'BN': 256,
        'BK': 16,
        'GROUP_SZ': 4,
        'waves_per_eu': 2
      },
      num_warps=8,
      num_stages=2),
    triton.Config(
      {
        'BM': 128,
        'BN': 128,
        'BK': 32,
        'GROUP_SZ': 1,
        'waves_per_eu': 2
      },
      num_warps=8,
      num_stages=2),
    triton.Config(
      {
        'BM': 64,
        'BN': 128,
        'BK': 32,
        'GROUP_SZ': 8,
        'waves_per_eu': 3
      },
      num_warps=4,
      num_stages=2),
    triton.Config(
      {
        'BM': 64,
        'BN': 64,
        'BK': 32,
        'GROUP_SZ': 1,
        'waves_per_eu': 8
      },
      num_warps=4,
      num_stages=2),
  ]


def get_cuda_autotune_config():
  return [
    triton.Config({
      "BM": 128,
      "BN": 256,
      "BK": 64,
      "GROUP_SZ": 8
    },
      num_stages=3,
      num_warps=8),
    triton.Config({
      "BM": 64,
      "BN": 256,
      "BK": 32,
      "GROUP_SZ": 8
    },
      num_stages=4,
      num_warps=4),
    triton.Config({
      "BM": 128,
      "BN": 128,
      "BK": 32,
      "GROUP_SZ": 8
    },
      num_stages=4,
      num_warps=4),
    triton.Config({
      "BM": 128,
      "BN": 64,
      "BK": 32,
      "GROUP_SZ": 8
    },
      num_stages=4,
      num_warps=4),
    triton.Config({
      "BM": 64,
      "BN": 128,
      "BK": 32,
      "GROUP_SZ": 8
    },
      num_stages=4,
      num_warps=4),
    triton.Config({
      "BM": 128,
      "BN": 32,
      "BK": 32,
      "GROUP_SZ": 8
    },
      num_stages=4,
      num_warps=4),
    triton.Config({
      "BM": 64,
      "BN": 32,
      "BK": 32,
      "GROUP_SZ": 8
    },
      num_stages=5,
      num_warps=2),
    triton.Config({
      "BM": 32,
      "BN": 64,
      "BK": 32,
      "GROUP_SZ": 8
    },
      num_stages=5,
      num_warps=2),
    triton.Config({
      "BM": 32,
      "BN": 32,
      "BK": 32,
      "GROUP_SZ": 8
    },
      num_stages=5,
      num_warps=2),
    triton.Config({
      "BM": 32,
      "BN": 32,
      "BK": 16,
      "GROUP_SZ": 8
    },
      num_stages=5,
      num_warps=2),
    triton.Config({
      "BM": 16,
      "BN": 16,
      "BK": 16,
      "GROUP_SZ": 8
    },
      num_stages=5,
      num_warps=2),
    # Good config for fp8 inputs.
    triton.Config({
      'BM': 128,
      'BN': 256,
      'BK': 128,
      'GROUP_SZ': 8
    },
      num_stages=3,
      num_warps=8),
    triton.Config({
      'BM': 256,
      'BN': 128,
      'BK': 128,
      'GROUP_SZ': 8
    },
      num_stages=3,
      num_warps=8),
    triton.Config({
      'BM': 256,
      'BN': 64,
      'BK': 128,
      'GROUP_SZ': 8
    },
      num_stages=4,
      num_warps=4),
    triton.Config({
      'BM': 64,
      'BN': 256,
      'BK': 128,
      'GROUP_SZ': 8
    },
      num_stages=4,
      num_warps=4),
    triton.Config({
      'BM': 128,
      'BN': 128,
      'BK': 128,
      'GROUP_SZ': 8
    },
      num_stages=4,
      num_warps=4),
    triton.Config({
      'BM': 128,
      'BN': 64,
      'BK': 64,
      'GROUP_SZ': 8
    },
      num_stages=4,
      num_warps=4),
    triton.Config({
      'BM': 64,
      'BN': 128,
      'BK': 64,
      'GROUP_SZ': 8
    },
      num_stages=4,
      num_warps=4),
    triton.Config({
      'BM': 128,
      'BN': 32,
      'BK': 64,
      'GROUP_SZ': 8
    },
      num_stages=4,
      num_warps=4)
  ]


def get_autotune_config():
  if is_cuda():
    return get_cuda_autotune_config()
  else:
    return get_hip_autotune_config()


@triton.autotune(
  # Choices of configs to auto-tune over
  configs=get_cuda_autotune_config(),
  # Definition of problem size. If it changes, a new auto-tune is run for the new problem size.
  key=["m", "n", "k"],
)
@triton.jit
def grouped_autotuned_matmul_k(a_ptr, b_ptr, c_ptr, m, n, k, stride_am,
                               stride_ak, stride_bk, stride_bn, stride_cm,
                               stride_cn, BM: tl.constexpr, BN: tl.constexpr,
                               BK: tl.constexpr, GROUP_SZ: tl.constexpr,
                               ACTIVATION: tl.constexpr):
  grouped_matmul_k(a_ptr, b_ptr, c_ptr, m, n, k, stride_am, stride_ak,
                   stride_bk, stride_bn, stride_cm, stride_cn, BM, BN, BK,
                   GROUP_SZ, ACTIVATION)


def grouped_autotuned_matmul(a, b, activation=""):
  matmul_k_fn = grouped_autotuned_matmul_k

  assert a.shape[1] == b.shape[0], "matrix dims not compatible for matmul"
  check_tensors_gpu_ready(a, b)
  (m, k), (_, n) = a.shape, b.shape
  c = torch.empty((m, n), device=a.device, dtype=a.dtype)
  grid = lambda meta: (triton.cdiv(m, meta["BM"]), triton.cdiv(n, meta["BN"]))
  matmul_k_fn[grid](
    a,
    b,
    c,
    m,
    n,
    k,
    a.stride(0),
    a.stride(1),
    b.stride(0),
    b.stride(1),
    c.stride(0),
    c.stride(1),
    ACTIVATION=activation
    # BM=bs, BN=bs, BK=bs, <- will be autotuned
    # **GROUP_SZ <- will be autotuned
  )
  return c


def numpy_matmul(a, b):
  (ar, ac), (br, bc) = a.shape, b.shape
  c = torch.zeros(ar, bc, device=a.device, dtype=a.dtype)
  for i in range(ar):
    c[i] = (a[i, :, None] * b).sum(dim=0)
  return c


cuda_src = cuda_begin + r'''

// k对应的维度做tiling（phases）

// Analysis:
// 1. TILE_WIDTH设为32会导致性能严重劣化, 1536
// 2. 采用 sharedMatMult<<<blocks, tpb, 2 * TILE_WIDTH * TILE_WIDTH>>>, dynamic shared mem，性能劣化的一种原因是kernel内部编译时不知道TILE_WIDTH大小，无法最优化
// 3. 改写用模版传入TILE_WIDTH，性能相比static有微小提升
// 4. 对于NaiveMatmul, 当square_matrix_size >= 1024时，block=(32,32)相比(16,16)有提升

template<int TILE_WIDTH>
__global__ void sharedMatMult( float *a, float *b, float *c, int M, int K, int N){
    C10_LAUNCH_BOUNDS_0;
    extern __shared__ float aTile[];
    float *bTile = &aTile[TILE_WIDTH*TILE_WIDTH];
    // __shared__ float aTile[TILE_WIDTH][TILE_WIDTH];  
    // __shared__ float bTile[TILE_WIDTH][TILE_WIDTH];
  
    // note how threadIdx.x is the fastest moving bit --> coalesced memory access, improve 7x at most
    int ir = threadIdx.y;
    int ic = threadIdx.x; 

    int row = blockIdx.y * blockDim.y + ir;
    int col = blockIdx.x * blockDim.x + ic;
    float sum = 0.0f;

    for(int phase = 0; phase < cdiv(K, TILE_WIDTH); phase++){
        int a_col = ic + phase * TILE_WIDTH;
        int b_row = ir + phase * TILE_WIDTH;
        aTile[ir*TILE_WIDTH + ic] = ((a_col < K && row < M) ? a[row * K + a_col] : 0.0f);
        bTile[ir*TILE_WIDTH + ic] = ((b_row < K && col < N) ? b[b_row * N + col] : 0.0f);
        __syncthreads();
        for(int i = 0; i < TILE_WIDTH; i++){
          sum += aTile[ir*TILE_WIDTH + i] * bTile[i*TILE_WIDTH + ic];
        }
        __syncthreads();
    }
    if (row < M && col < N) {
      c[row * N + col] = sum;
    }
}


__global__ void matrixMulGPU( float * a, float * b, float * c, int M, int K, int N)
{
  float val = 0;

  int row = blockIdx.y * blockDim.y + threadIdx.y;
  int col = blockIdx.x * blockDim.x + threadIdx.x;

  if (row < M && col < N)
  {
    for ( int k = 0; k < K; ++k )
      val += a[row * K + k] * b[k * N + col];
    c[row * N + col] = val;
  }
}


void matrixMulCPU( float * a, float * b, float * c, int M, int K, int N)
{
  for( int row = 0; row < M; ++row )
    for( int col = 0; col < N; ++col )
    {
      float val = 0;
      for ( int k = 0; k < K; ++k )
        val += a[row * K + k] * b[k * N + col];
      c[row * N + col] = val;
    }
}


torch::Tensor naive_matmul(torch::Tensor m, torch::Tensor n) {
    CHECK_INPUT(m); CHECK_INPUT(n);
    int h = m.size(0);
    int w = n.size(1);
    int k = m.size(1);
    TORCH_CHECK(k==n.size(0), "Size mismatch!");
    auto output = torch::zeros({h, w}, m.options());

    // int minGridSize, optimalBlockSize;
    // cudaError_t occupancy_status = cudaOccupancyMaxPotentialBlockSize(
       // &minGridSize,
       // &optimalBlockSize,
       // (void*)matrixMulGPU, // Pointer to the kernel function
       // 0,                   // Dynamic shared memory per block (assuming 0 for matrixMulGPU)
       // 0                    // block size limit (0 means no limit beyond hardware)
    // );
    // C10_CUDA_CHECK(occupancy_status);

    dim3 tpb;
    tpb.x = 32;
    tpb.y = 32;
    // tpb.y = std::max(1, optimalBlockSize / (int)tpb.x); // Ensure at least 1 thread in y-dim
    // if (tpb.x * tpb.y > optimalBlockSize) {
    //     tpb.y = optimalBlockSize / (int)tpb.x;
    //     tpb.y = std::max(1, (int)tpb.y);
    // }
    dim3 blocks(cdiv(w, tpb.x), cdiv(h, tpb.y)); 
    matrixMulGPU<<<blocks, tpb>>>(
        m.data_ptr<float>(), n.data_ptr<float>(), output.data_ptr<float>(), h, k, w);
    C10_CUDA_KERNEL_LAUNCH_CHECK();
    return output;
}

torch::Tensor shared_matmul(torch::Tensor m, torch::Tensor n) {
    CHECK_INPUT(m); CHECK_INPUT(n);
    int h = m.size(0);
    int w = n.size(1);
    int k = m.size(1);
    TORCH_CHECK(k==n.size(0), "Size mismatch!");
    auto output = torch::zeros({h, w}, m.options());
    
    // dynamic tile width
    // cudaDeviceProp devProp;
    // CUDA_ERR(cudaGetDeviceProperties(&devProp, 0));
    // int maxThreads = devProp.maxThreadsPerBlock;
    // int TILE_WIDTH = std::sqrt(maxThreads);

    int TILE_WIDTH = 16;
    dim3 tpb(TILE_WIDTH, TILE_WIDTH);
    dim3 blocks(cdiv(w, tpb.x), cdiv(h, tpb.y));
    size_t size = TILE_WIDTH*TILE_WIDTH*2 * sizeof(float);
    
    auto f = [&](auto kf) { kf<<<blocks, tpb, size>>>(
        m.data_ptr<float>(), n.data_ptr<float>(), output.data_ptr<float>(), h, k, w);
    };
    switch(TILE_WIDTH) {
        case 8: f(sharedMatMult<8>); break;
        case 16: f(sharedMatMult<16>); break;
        case 32: f(sharedMatMult<32>); break;
        default: break;
    }
        
        
    C10_CUDA_KERNEL_LAUNCH_CHECK();
    return output;
}
'''

cpp_src = '''
torch::Tensor naive_matmul(torch::Tensor m, torch::Tensor n);
torch::Tensor shared_matmul(torch::Tensor m, torch::Tensor n);
'''

mm_module = load_cuda(cuda_src,
                      cpp_src, ['naive_matmul', 'shared_matmul'],
                      opt=True,
                      verbose=True,
                      name="mm_load_inline")

import math
from numba import cuda

is_cuda_sim = os.environ.get('NUMBA_ENABLE_CUDASIM') == '1'
if not is_cuda_sim:
  from numba.cuda import as_cuda_array as ca
else:

  def ca(x):
    return x


@cuda.jit
def matmul_k_numba(m, n, out, tw):
  cbi, cbd, tid = cuda.blockIdx, cuda.blockDim, cuda.threadIdx
  tc, tr = tid.x, tid.y
  r, c = cbi.y * cbd.y + tr, cbi.x * cbd.x + tc
  h, k = m.shape
  k2, w = n.shape

  shar = cuda.shared.array(0, dtype=np.float32)
  ms, ns = shar[:tw * tw], shar[tw * tw:2 * tw * tw]

  p = np.float32(0.0)
  for ph in range(math.ceil(k / tw)):
    idx = ph * tw
    ms[tr * tw + tc] = m[r, tc + idx] if r < h and idx + tc < k else 0.
    ns[tr * tw + tc] = n[tr + idx, c] if c < w and idx + tr < k else 0.
    cuda.syncthreads()
    for i in range(tw):
      p += ms[tr * tw + i] * ns[i * tw + tc]
    cuda.syncthreads()
  if r < h and c < w:
    out[r, c] = p


def matmul_2d_numba(m, n, tw=16):
  h, k = m.shape
  k2, w = n.shape
  assert k == k2, "Size mismatch!"
  out = torch.zeros(h, w, dtype=m.dtype, device=m.device)
  dyn_shared_mem_size = 2 * tw * tw * 4
  tpb = tw, tw
  blocks = cdiv(w, tpb[0]), cdiv(h, tpb[1])
  matmul_k_numba[blocks, tpb, 0, dyn_shared_mem_size](ca(m), ca(n), ca(out), tw)
  return out


check_implementation(
  naive_matmul,
  torch.matmul,
  "Triton-Naive",
  "Torch",
  common_args=(a, b),
)
check_implementation(
  grouped_matmul,
  torch.matmul,
  "Triton-Grouped",
  "Torch",
  common_args=(a, b),
  kwargs_a={
    'GROUP_SZ': 32,
    'activation': ''
  },
)
# check_implementation(
#     grouped_autotuned_matmul, torch.matmul,
#     "Triton-Grouped-Autotuned", "Torch",
#     common_args=(a, b)
# )
check_implementation(torch.compile(torch.matmul),
                     torch.matmul,
                     "Torch-Compiled",
                     "Torch",
                     common_args=(a, b))
check_implementation(
  mm_module.naive_matmul,
  torch.matmul,
  "Cuda-Naived",
  "Torch",
  common_args=(a, b),
  dtypes=[torch.float32],
)
check_implementation(
  mm_module.shared_matmul,
  torch.matmul,
  "Cuda-Shared",
  "Torch",
  common_args=(a, b),
  dtypes=[torch.float32],
)
check_implementation(matmul_2d_numba,
                     torch.matmul,
                     "Numba",
                     "Torch",
                     common_args=(a, b),
                     atol=6e-2)


@triton.testing.perf_report(
  triton.testing.Benchmark(
    x_names=["square_matrix_size"],
    x_vals=[2**i for i in range(5, 12, 1)],
    x_log=True,  # x axis is logarithmic.
    line_arg="provider",
    line_vals=[
      "naive",
      "grouped",
      "grouped-autotuned",
      "grouped-autotuned-leaky-relu",
      "torch",
      "torch-compiled-dynamic-none",
      "torch-compiled-dynamic-true",
      "torch-compiled-dynamic-false",
      "numpy-broadcast",
      "cuda-naive",
      "cuda-shared",
      "numba",
      "grouped-autotuned-fp16",
      "torch-fp16",
      "torch-fp32-cast16",
      "torch-fp32-cast16-compiled-dynamic-false",
      "grouped-fp8",  # "grouped-autotuned-fp8"
    ],
    line_names=[
      "Naive",
      "Grouped",
      "Grouped & Auto-Tuned",
      "Grouped & Auto-Tuned (Leaky ReLU)",
      "Torch",
      "Torch-Compiled (dynamic=None)",
      "Torch-Compiled (dynamic=True)",
      "Torch-Compiled (dynamic=False)",
      "Numpy-Broadcast",
      "Cuda-Naive",
      "Cuda-Shared",
      "Numba",
      "Grouped & Auto-Tuned & FP16",
      "Torch-FP16",
      "Torch-FP32-Cast16",
      "Torch-FP16-Cast16-Compiled (dynamic=False)",
      "Grouped-FP8",  # "Grouped & Auto-Tuned (FP8)"
    ],  # Label name for the lines.
    styles=[
      ("blue", "-"),
      ("green", "-"),
      ("green", "--"),
      ("green", ":"),
      ("orange", "-"),
      ("orange", "--"),
      ("red", "-"),
      ("purple", "-"),
      ("purple", "--"),
      ("brown", "-"),
      ("cyan", "--"),
      ("magenta", "-"),
      ("cyan", ":"),
      ("teal", "-"),
      ("olive", "-"),
      ("navy", "-"),
      ("olive", "--"),
    ],  # Line styles.
    ylabel="GB/s",  # Label name for the y-axis.
    plot_name=
    "matmul-performance-matrix-size(gbps)",  # Name for the plot. Used also as a file name for saving the plot.
    args={},  # Values for function arguments not in `x_names` and `y_name`.
  ))
def benchmark_matrix_size(square_matrix_size, provider):
  sz = square_matrix_size
  dtype = torch.float32
  if "fp16" in provider:
    dtype = torch.float16
  elif 'fp8' in provider:
    TORCH_HAS_FP8 = hasattr(torch, "float8_e5m2")
    if not TORCH_HAS_FP8:
      print(f"Skipping {provider} benchmark: float8_e5m2 not supported.")
      return 0, 0, 0
    dtype = torch.float8_e5m2
  a = torch.rand((sz, sz), device="cuda").to(dtype)
  b_fp32 = torch.rand((sz, sz), device="cuda")
  # Note: pre-transpose b for efficiency.
  b = b_fp32.T.to(dtype) if ('fp16' in provider or
                             'fp8' in provider) else b_fp32
  quantiles = [0.5, 0.2, 0.8]
  if provider == "naive":
    ms, min_ms, max_ms = triton.testing.do_bench(lambda: naive_matmul(a, b),
                                                 quantiles=quantiles)
  elif provider == "grouped":
    ms, min_ms, max_ms = triton.testing.do_bench(
      lambda: grouped_matmul(a, b, GROUP_SZ=8), quantiles=quantiles)
  elif provider == "grouped-autotuned":
    ms, min_ms, max_ms = triton.testing.do_bench(
      lambda: grouped_autotuned_matmul(a, b), quantiles=quantiles)
  elif provider == "grouped-autotuned-leaky-relu":
    ms, min_ms, max_ms = triton.testing.do_bench(
      lambda: grouped_autotuned_matmul(a, b, activation="leaky_relu"),
      quantiles=quantiles)
  elif provider == "torch":
    ms, min_ms, max_ms = triton.testing.do_bench(lambda: torch.matmul(a, b),
                                                 quantiles=quantiles)
  elif provider == "torch-compiled-dynamic-none":
    compiled_matmul_dynamic_none = torch.compile(torch.matmul, dynamic=None)
    ms, min_ms, max_ms = triton.testing.do_bench(lambda: compiled_matmul_dynamic_none(a, b),
                                                 quantiles=quantiles)
  elif provider == "torch-compiled-dynamic-true":
    compiled_matmul_dynamic_true = torch.compile(torch.matmul, dynamic=True)
    ms, min_ms, max_ms = triton.testing.do_bench(lambda: compiled_matmul_dynamic_true(a, b),
                                                 quantiles=quantiles)
  elif provider == "torch-compiled-dynamic-false":
    compiled_matmul_dynamic_false = torch.compile(torch.matmul, dynamic=False)
    ms, min_ms, max_ms = triton.testing.do_bench(lambda: compiled_matmul_dynamic_false(a, b),
                                                 quantiles=quantiles)
  elif provider == "numpy-broadcast":
    ms, min_ms, max_ms = triton.testing.do_bench(lambda: numpy_matmul(a, b),
                                                 quantiles=quantiles)
  elif provider == "cuda-naive":
    ms, min_ms, max_ms = triton.testing.do_bench(
      lambda: mm_module.naive_matmul(a, b), quantiles=quantiles)
  elif provider == "cuda-shared":
    ms, min_ms, max_ms = triton.testing.do_bench(
      lambda: mm_module.shared_matmul(a, b), quantiles=quantiles)
  elif provider == "numba":
    ms, min_ms, max_ms = triton.testing.do_bench(lambda: matmul_2d_numba(a, b),
                                                 quantiles=quantiles)
  elif provider == "grouped-autotuned-fp16":
    ms, min_ms, max_ms = triton.testing.do_bench(
      lambda: grouped_autotuned_matmul(a, b), quantiles=quantiles)
  elif provider == "torch-fp16":
    ms, min_ms, max_ms = triton.testing.do_bench(lambda: torch.matmul(a, b),
                                                 quantiles=quantiles)
  elif provider == "torch-fp32-cast16":
    ms, min_ms, max_ms = triton.testing.do_bench(
      lambda: torch.matmul(a.to(torch.float16), b.to(torch.float16)),
      quantiles=quantiles)
  elif provider == "torch-fp32-cast16-compiled-dynamic-false":
    compiled_matmul_dynamic_false_fp16 = torch.compile(
      lambda x, y: torch.matmul(x.to(torch.float16),
                                y.to(torch.float16)),
      dynamic=False)
    ms, min_ms, max_ms = triton.testing.do_bench(
      lambda: compiled_matmul_dynamic_false_fp16(a, b), quantiles=quantiles)
  elif provider == "grouped-fp8":
    ms, min_ms, max_ms = triton.testing.do_bench(
      lambda: grouped_matmul(a, b, GROUP_SZ=8), quantiles=quantiles)
  # TRITON LLVM Error: size mismatch when packing elements for LLVM struct expected 4 but got 8
  # elif provider == "grouped-autotuned-fp8":
  #   ms, min_ms, max_ms = triton.testing.do_bench(
  #       lambda: grouped_autotuned_matmul(a, b),
  #       quantiles=quantiles)

  # RuntimeError: "addmm_cuda" not implemented for 'Float8_e5m2'
  # elif provider == "torch-fp8":
  #   ms, min_ms, max_ms = triton.testing.do_bench(lambda: torch.matmul(a, b),
  #                                                quantiles=quantiles)

  else:
    raise ValueError("Unknown provider")

  def gbps(ms):
    return 12 * sz * sz / ms * 1e-6

  return gbps(ms), gbps(max_ms), gbps(min_ms)


benchmark_matrix_size.run(print_data=True, show_plots=True, save_path=".")