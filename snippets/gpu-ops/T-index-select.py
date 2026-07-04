import torch
import triton
import triton.language as tl
from triton.runtime import driver
from torch.amp import custom_fwd, custom_bwd
from absl import logging
import os

__all__ = ["index_select"]

tl_print = print if os.environ.get("TRITON_INTERPRET", 0) else tl.device_print
DEVICE = torch.device('cuda:0')
properties = driver.active.utils.get_device_properties(DEVICE.index)
NUM_SM = properties["multiprocessor_count"]


@triton.jit
def index_select_fwd(unique_values, indices, output, num_rows: int,
                     num_cols: int, num_indices: int,
                     BLOCK_M_SIZE: tl.constexpr, BLOCK_N_SIZE: tl.constexpr):
  # unique_values: shape (num_rows, num_cols)
  pid_m = tl.program_id(axis=0).to(tl.int64)
  pid_n = tl.program_id(axis=1).to(tl.int64)
  off_m = pid_m * BLOCK_M_SIZE + tl.arange(0, BLOCK_M_SIZE)
  off_n = pid_n * BLOCK_N_SIZE + tl.arange(0, BLOCK_N_SIZE)
  index_data = tl.load(indices + off_m, mask=off_m < num_indices, other=-1)
  row_mask = (index_data >= 0) & (index_data < num_rows)
  col_mask = (off_n < num_cols)
  mask = row_mask[:, None] & col_mask[None, :]
  block_unique_values = tl.load(unique_values + index_data[:, None] * num_cols +
                                off_n[None, :],
                                mask=mask)
  tl.store(output + off_m[:, None] * num_cols + off_n[None, :],
           value=block_unique_values,
           mask=mask)


def _index_select_forward_common(unique_values: torch.Tensor,
                                 indices: torch.Tensor):
  """Helper function containing common forward logic."""
  assert unique_values.is_contiguous()
  assert indices.is_contiguous()
  assert indices.device == unique_values.device
  assert indices.dtype in (torch.int32, torch.int64)

  if unique_values.ndim == 2:
    out_shape = [*indices.shape, unique_values.shape[1]]
    num_rows, num_cols = unique_values.shape
  else:
    assert unique_values.ndim == 1
    num_rows, num_cols = unique_values.shape[0], 1
    out_shape = [*indices.shape]

  output = torch.zeros(*out_shape,
                       dtype=unique_values.dtype,
                       device=unique_values.device)
  num_indices = indices.numel()
  if num_indices > 0 and num_rows > 0 and num_cols > 0:
    BLOCK_M_SIZE, BLOCK_N_SIZE = 128, min(128,
                                          triton.next_power_of_2(num_cols))
    grid = ((num_indices + BLOCK_M_SIZE - 1) // BLOCK_M_SIZE,
            (num_cols + BLOCK_N_SIZE - 1) // BLOCK_N_SIZE)
    index_select_fwd[grid](unique_values,
                           indices,
                           output,
                           num_rows,
                           num_cols,
                           num_indices,
                           BLOCK_M_SIZE=BLOCK_M_SIZE,
                           BLOCK_N_SIZE=BLOCK_N_SIZE,
                           num_warps=4)
  else:
    logging.info(
        f"IndexSelect fwd skipped: num_indices={num_indices}, num_rows={num_rows}, num_cols={num_cols}"
    )

  return output, num_rows, num_cols, num_indices


@triton.jit
def index_select_bwd_atomic_add(grad_outputs, indices, grad_unique_values,
                                num_rows: int, num_cols: int, num_indices: int,
                                BLOCK_M_SIZE: tl.constexpr,
                                BLOCK_N_SIZE: tl.constexpr,
                                sem: tl.constexpr = None):
  # grad_unique_values: shape (num_rows, num_cols)
  # grad_outputs: shape (num_indices, num_cols)
  pid_m = tl.program_id(axis=0).to(tl.int64)
  pid_n = tl.program_id(axis=1).to(tl.int64)
  off_cols = pid_n * BLOCK_N_SIZE + tl.arange(0, BLOCK_N_SIZE)
  mask = off_cols < num_cols

  start = pid_m * BLOCK_M_SIZE
  end = (pid_m + 1) * BLOCK_M_SIZE
  if start >= num_indices:
    return
  if end > num_indices:
    end = num_indices.to(tl.int64)
  for index_row_id in range(start, end):
    unique_row_id = tl.load(indices + index_row_id)
    if unique_row_id >= 0 and unique_row_id < num_rows:
      grads = tl.load(grad_outputs + index_row_id * num_cols + off_cols,
                      mask=mask,
                      other=0.0)
      tl.atomic_add(grad_unique_values + unique_row_id * num_cols + off_cols,
                    grads.to(grad_unique_values.dtype.element_ty),
                    mask=mask, sem=sem)


class IndexSelect_TritonAtomicAdd(torch.autograd.Function):

  @staticmethod
  @custom_fwd(device_type="cuda", cast_inputs=torch.float32)
  def forward(ctx, unique_values: torch.Tensor, indices: torch.Tensor):
    output, num_rows, num_cols, num_indices = _index_select_forward_common(
        unique_values, indices)
    ctx.save_for_backward(indices)
    ctx.input_shape = unique_values.shape
    ctx.input_dtype = unique_values.dtype
    ctx.input_device = unique_values.device
    ctx.num_rows = num_rows
    ctx.num_cols = num_cols
    ctx.num_indices = num_indices
    return output

  @staticmethod
  @custom_bwd(device_type="cuda")
  def backward(ctx, *grad_outputs: list[torch.Tensor]):
    (indices,) = ctx.saved_tensors
    input_shape = ctx.input_shape
    input_dtype = ctx.input_dtype
    input_device = ctx.input_device
    num_rows = ctx.num_rows
    num_cols = ctx.num_cols
    num_indices = ctx.num_indices

    grad_output = grad_outputs[0].contiguous()
    grad_unique_values = torch.zeros(input_shape,
                                     dtype=input_dtype,
                                     device=input_device)

    if num_indices > 0 and num_rows > 0 and num_cols > 0:
      # BLOCK_M_SIZE, BLOCK_N_SIZE = 8, 128
      # grid = ((indices.numel() + BLOCK_M_SIZE - 1) // BLOCK_M_SIZE,
      #         (num_cols + BLOCK_N_SIZE - 1) // BLOCK_N_SIZE)

      BLOCK_M_SIZE, BLOCK_N_SIZE = 8, triton.next_power_of_2(num_cols)
      grid = ((indices.numel() + BLOCK_M_SIZE - 1) // BLOCK_M_SIZE, 1)

      index_select_bwd_atomic_add[grid](grad_output,
                                        indices,
                                        grad_unique_values,
                                        num_rows,
                                        num_cols,
                                        num_indices,
                                        BLOCK_M_SIZE=BLOCK_M_SIZE,
                                        BLOCK_N_SIZE=BLOCK_N_SIZE)
    return grad_unique_values, None


class IndexSelect_TritonAtomicAddRelaxed(torch.autograd.Function):

  @staticmethod
  @custom_fwd(device_type="cuda", cast_inputs=torch.float32)
  def forward(ctx, unique_values: torch.Tensor, indices: torch.Tensor):
    output, num_rows, num_cols, num_indices = _index_select_forward_common(
        unique_values, indices)
    ctx.save_for_backward(indices)
    ctx.input_shape = unique_values.shape
    ctx.input_dtype = unique_values.dtype
    ctx.input_device = unique_values.device
    ctx.num_rows = num_rows
    ctx.num_cols = num_cols
    ctx.num_indices = num_indices
    return output

  @staticmethod
  @custom_bwd(device_type="cuda")
  def backward(ctx, *grad_outputs: list[torch.Tensor]):
    (indices,) = ctx.saved_tensors
    input_shape = ctx.input_shape
    input_dtype = ctx.input_dtype
    input_device = ctx.input_device
    num_rows = ctx.num_rows
    num_cols = ctx.num_cols
    num_indices = ctx.num_indices

    grad_output = grad_outputs[0].contiguous()
    grad_unique_values = torch.zeros(input_shape,
                                     dtype=input_dtype,
                                     device=input_device)

    if num_indices > 0 and num_rows > 0 and num_cols > 0:
      # BLOCK_M_SIZE, BLOCK_N_SIZE = 8, 128
      # grid = ((indices.numel() + BLOCK_M_SIZE - 1) // BLOCK_M_SIZE,
      #         (num_cols + BLOCK_N_SIZE - 1) // BLOCK_N_SIZE)
      if num_indices * num_cols > 3000000 * 64:
        BLOCK_M_SIZE = 32
      else:
        BLOCK_M_SIZE = 8
      BLOCK_N_SIZE = triton.next_power_of_2(num_cols)
      grid = ((indices.numel() + BLOCK_M_SIZE - 1) // BLOCK_M_SIZE, 1)

      index_select_bwd_atomic_add[grid](grad_output,
                                        indices,
                                        grad_unique_values,
                                        num_rows,
                                        num_cols,
                                        num_indices,
                                        BLOCK_M_SIZE=BLOCK_M_SIZE,
                                        BLOCK_N_SIZE=BLOCK_N_SIZE,
                                        sem='relaxed')
    return grad_unique_values, None


class IndexSelect(torch.autograd.Function):

  @staticmethod
  @custom_fwd(device_type="cuda", cast_inputs=torch.float32)
  def forward(ctx, unique_values: torch.Tensor, indices: torch.Tensor):
    output, num_rows, num_cols, num_indices = _index_select_forward_common(
        unique_values, indices)
    ctx.save_for_backward(indices)
    ctx.input_shape = unique_values.shape
    ctx.input_dtype = unique_values.dtype
    ctx.input_device = unique_values.device
    ctx.num_rows = num_rows
    ctx.num_cols = num_cols
    ctx.num_indices = num_indices
    return output

  @staticmethod
  @custom_bwd(device_type="cuda")
  def backward(ctx, *grad_outputs: list[torch.Tensor]):
    (indices,) = ctx.saved_tensors
    input_shape = ctx.input_shape
    input_dtype = ctx.input_dtype
    input_device = ctx.input_device
    num_rows = ctx.num_rows
    num_cols = ctx.num_cols
    num_indices = ctx.num_indices

    grad_output = grad_outputs[0].contiguous()
    grad_unique_values = torch.zeros(input_shape,
                                     dtype=input_dtype,
                                     device=input_device)
    if num_indices <= 0 or num_rows <= 0 or num_cols <= 0:
      return grad_unique_values, None
    unique_ratio = num_indices / num_rows
    # heuristic for choosing the backward implementation
    # Ref: internal benchmark note; private document URL removed.
    threshold = None
    if unique_ratio <= 0.02:
      threshold = 400000
    elif unique_ratio <= 0.03:
      threshold = 350000
    elif unique_ratio <= 0.05:
      threshold = 300000
    elif unique_ratio <= 0.2:
      threshold = 200000
    elif unique_ratio <= 0.5:
      threshold = 300000
    else:
      threshold = 400000
    if num_indices <= threshold:
      # BLOCK_M_SIZE, BLOCK_N_SIZE = 8, 128
      # grid = ((indices.numel() + BLOCK_M_SIZE - 1) // BLOCK_M_SIZE,
      #         (num_cols + BLOCK_N_SIZE - 1) // BLOCK_N_SIZE)

      BLOCK_M_SIZE, BLOCK_N_SIZE = 8, triton.next_power_of_2(num_cols)
      grid = ((indices.numel() + BLOCK_M_SIZE - 1) // BLOCK_M_SIZE, 1)

      index_select_bwd_atomic_add[grid](grad_output,
                                        indices,
                                        grad_unique_values,
                                        num_rows,
                                        num_cols,
                                        num_indices,
                                        BLOCK_M_SIZE=BLOCK_M_SIZE,
                                        BLOCK_N_SIZE=BLOCK_N_SIZE)
    else:
      indices = indices.flatten()
      # unique_indices, counts = torch.unique(
      #     indices, sorted=True, return_inverse=False, return_counts=True)
      # inverse_indices = torch.argsort(indices)
      sorted_values, inverse_indices = torch.sort(indices)
      unique_indices, counts = torch.unique_consecutive(sorted_values, return_counts=True)
      offsets = torch.zeros(counts.size(0) + 1,
                            dtype=counts.dtype,
                            device=counts.device)
      offsets[1:] = torch.cumsum(counts, dim=0)
      if num_indices < 250000:
        BLOCK_SIZE = 128
      else:
        BLOCK_SIZE = 1024
      grid = (counts.size(0), (num_cols + BLOCK_SIZE - 1) // BLOCK_SIZE)
      index_select_bwd_reorder[grid](
          grad_output,
          grad_unique_values,
          unique_indices,
          inverse_indices,
          offsets,
          num_rows=num_rows,
          num_cols=num_cols,
          BLOCK_SIZE=BLOCK_SIZE,
      )
    return grad_unique_values, None

@triton.jit
def index_select_bwd_reorder(
    grad_outputs,
    grad_unique_values,
    unique_indices,
    inverse_indices,
    offsets,
    num_rows: int,
    num_cols: int,
    BLOCK_SIZE: tl.constexpr,
):
  # grad_unique_values: shape (num_rows, num_cols)
  # grad_outputs: shape (num_indices, num_cols)
  pid = tl.program_id(axis=0).to(tl.int64)
  pid_col = tl.program_id(axis=1).to(tl.int64)
  off_cols = pid_col * BLOCK_SIZE + tl.arange(0, BLOCK_SIZE)
  mask = off_cols < num_cols
  acc = tl.zeros((BLOCK_SIZE,), dtype=tl.float32)

  start = tl.load(offsets + pid)
  end = tl.load(offsets + pid + 1)
  unique_index = tl.load(unique_indices + pid)
  if unique_index < 0 or unique_index >= num_rows:
    return
  for i in range(start, end):
    row_id = tl.load(inverse_indices + i)
    acc += tl.load(grad_outputs + row_id * num_cols + off_cols,
                   mask=mask,
                   other=0.0)
  tl.store(
      grad_unique_values + unique_index * num_cols + off_cols,
      acc.to(grad_outputs.dtype.element_ty),
      mask=mask,
  )


class IndexSelect_TritonReorder(torch.autograd.Function):

  @staticmethod
  @custom_fwd(device_type="cuda", cast_inputs=torch.float32)
  def forward(ctx, unique_values: torch.Tensor, indices: torch.Tensor):
    output, num_rows, num_cols, num_indices = _index_select_forward_common(
        unique_values, indices)
    ctx.save_for_backward(indices)
    ctx.input_shape = unique_values.shape
    ctx.input_dtype = unique_values.dtype
    ctx.input_device = unique_values.device
    ctx.num_rows = num_rows
    ctx.num_cols = num_cols
    ctx.num_indices = num_indices
    return output

  @staticmethod
  def backward(ctx, *grad_outputs: list[torch.Tensor]):
    (indices,) = ctx.saved_tensors
    input_shape = ctx.input_shape
    input_dtype = ctx.input_dtype
    input_device = ctx.input_device
    num_rows = ctx.num_rows
    num_cols = ctx.num_cols
    num_indices = ctx.num_indices

    grad_output = grad_outputs[0].contiguous()
    grad_unique_values = torch.zeros(input_shape,
                                     dtype=input_dtype,
                                     device=input_device)

    indices = indices.flatten()
    # unique_indices, counts = torch.unique(
    #     indices, sorted=True, return_inverse=False, return_counts=True)
    # inverse_indices = torch.argsort(indices)
    sorted_values, inverse_indices = torch.sort(indices)
    unique_indices, counts = torch.unique_consecutive(sorted_values, return_counts=True)
    offsets = torch.zeros(counts.size(0) + 1,
                          dtype=counts.dtype,
                          device=counts.device)
    offsets[1:] = torch.cumsum(counts, dim=0)
    if num_indices < 250000:
      BLOCK_SIZE = 128
    else:
      BLOCK_SIZE = 1024
    grid = (counts.size(0), (num_cols + BLOCK_SIZE - 1) // BLOCK_SIZE)
    index_select_bwd_reorder[grid](
        grad_output,
        grad_unique_values,
        unique_indices,
        inverse_indices,
        offsets,
        num_rows=num_rows,
        num_cols=num_cols,
        BLOCK_SIZE=BLOCK_SIZE,
    )
    return grad_unique_values, None
    


@triton.jit
def index_select_bwd_reorder_2d(grad_outputs, grad_unique_values,
                                unique_indices, inverse_indices, offsets,
                                num_rows: int, num_cols: int,
                                BLOCK_M_SIZE: tl.constexpr,
                                BLOCK_N_SIZE: tl.constexpr):
  # grad_unique_values: shape (num_rows, num_cols)
  # grad_outputs: shape (num_indices, num_cols)
  pid = tl.program_id(axis=0).to(tl.int64)
  pid_n = tl.program_id(axis=1).to(tl.int64)
  off_cols = pid_n * BLOCK_N_SIZE + tl.arange(0, BLOCK_N_SIZE)
  mask = off_cols < num_cols

  start = pid * BLOCK_M_SIZE
  end = (pid + 1) * BLOCK_M_SIZE
  if start >= num_rows:
    return
  if end > num_rows:
    end = num_rows.to(tl.int64)
  for unique_row_id in range(start, end):
    unique_start = tl.load(offsets + unique_row_id)
    unique_end = tl.load(offsets + unique_row_id + 1)
    unique_index = tl.load(unique_indices + unique_row_id)
    if unique_index >= 0 and unique_index < num_rows:
      acc = tl.zeros((BLOCK_N_SIZE,), dtype=tl.float32)
      for i in range(unique_start, unique_end):
        row_id = tl.load(inverse_indices + i)
        acc += tl.load(grad_outputs + row_id * num_cols + off_cols,
                       mask=mask,
                       other=0.0)
      tl.store(grad_unique_values + unique_index * num_cols + off_cols,
               acc.to(grad_unique_values.dtype.element_ty),
               mask=mask)


class IndexSelect_TritonReorder2D(torch.autograd.Function):

  @staticmethod
  @custom_fwd(device_type="cuda", cast_inputs=torch.float32)
  def forward(ctx, unique_values: torch.Tensor, indices: torch.Tensor):
    output, num_rows, num_cols, num_indices = _index_select_forward_common(
        unique_values, indices)
    ctx.save_for_backward(indices)
    ctx.input_shape = unique_values.shape
    ctx.input_dtype = unique_values.dtype
    ctx.input_device = unique_values.device
    ctx.num_rows = num_rows
    ctx.num_cols = num_cols
    return output

  @staticmethod
  def backward(ctx, *grad_outputs: list[torch.Tensor]):
    (indices,) = ctx.saved_tensors
    input_shape = ctx.input_shape
    input_dtype = ctx.input_dtype
    input_device = ctx.input_device
    num_rows = ctx.num_rows
    num_cols = ctx.num_cols

    grad_output = grad_outputs[0].contiguous()
    grad_unique_values = torch.zeros(input_shape,
                                     dtype=input_dtype,
                                     device=input_device)
    unique_indices, inverse_indices, counts = torch.unique(indices,
                                                           sorted=True,
                                                           return_inverse=True,
                                                           return_counts=True)
    offsets = torch.zeros(counts.size(0) + 1,
                          dtype=counts.dtype,
                          device=counts.device)
    offsets[1:] = torch.cumsum(counts, dim=0)

    BLOCK_M_SIZE, BLOCK_N_SIZE = 2, 128
    grid = ((counts.numel() + BLOCK_M_SIZE - 1) // BLOCK_M_SIZE,
            (num_cols + BLOCK_N_SIZE - 1) // BLOCK_N_SIZE)
    index_select_bwd_reorder_2d[grid](grad_output,
                                      grad_unique_values,
                                      unique_indices,
                                      inverse_indices,
                                      offsets,
                                      num_rows=num_rows,
                                      num_cols=num_cols,
                                      BLOCK_M_SIZE=BLOCK_M_SIZE,
                                      BLOCK_N_SIZE=BLOCK_N_SIZE)
    return grad_unique_values, None


@triton.jit
def index_select_bwd_row_lock(grad_outputs, grad_unique_values, locks, indices,
                              num_rows: int, num_cols: int, num_indices: int,
                              BLOCK_M_SIZE: tl.constexpr,
                              BLOCK_N_SIZE: tl.constexpr):
  # grad_unique_values: shape (num_rows, num_cols)
  # grad_outputs: shape (num_indices, num_cols)
  pid_m = tl.program_id(axis=0).to(tl.int64)
  pid_n = tl.program_id(axis=1).to(tl.int64)
  off_cols = pid_n * BLOCK_N_SIZE + tl.arange(0, BLOCK_N_SIZE)
  mask = off_cols < num_cols

  start = pid_m * BLOCK_M_SIZE
  end = (pid_m + 1) * BLOCK_M_SIZE
  if start >= num_indices:
    return
  if end > num_indices:
    end = num_indices.to(tl.int64)
  for index_row_id in range(start, end):
    unique_row_id = tl.load(indices + index_row_id)
    if unique_row_id >= 0 and unique_row_id < num_rows:
      while tl.atomic_cas(locks + unique_row_id, 0, 1) == 1:
        pass
      grads = tl.load(grad_outputs + index_row_id * num_cols + off_cols,
                      mask=mask,
                      other=0.0)
      prev_grads = tl.load(grad_unique_values + unique_row_id * num_cols +
                           off_cols,
                           mask=mask,
                           other=0.0)
      tl.store(grad_unique_values + unique_row_id * num_cols + off_cols,
               (prev_grads + grads).to(grad_unique_values.dtype.element_ty),
               mask=mask)
      tl.atomic_xchg(locks + unique_row_id, 0)


class IndexSelect_TritonRowLock(torch.autograd.Function):

  @staticmethod
  @custom_fwd(device_type="cuda", cast_inputs=torch.float32)
  def forward(ctx, unique_values: torch.Tensor, indices: torch.Tensor):
    output, num_rows, num_cols, num_indices = _index_select_forward_common(
        unique_values, indices)
    ctx.save_for_backward(indices)
    ctx.input_shape = unique_values.shape
    ctx.input_dtype = unique_values.dtype
    ctx.input_device = unique_values.device
    ctx.num_rows = num_rows
    ctx.num_cols = num_cols
    ctx.num_indices = num_indices
    return output

  @staticmethod
  def backward(ctx, *grad_outputs: list[torch.Tensor]):
    (indices,) = ctx.saved_tensors
    input_shape = ctx.input_shape
    input_dtype = ctx.input_dtype
    input_device = ctx.input_device
    grad_output = grad_outputs[0].contiguous()
    grad_unique_values = torch.zeros(input_shape,
                                     dtype=input_dtype,
                                     device=input_device)
    num_rows, num_cols, num_indices = ctx.num_rows, ctx.num_cols, ctx.num_indices
    locks = torch.zeros(num_rows, dtype=torch.int32, device=indices.device)
    # BLOCK_M_SIZE, BLOCK_N_SIZE = 8, 128
    # grid = ((indices.numel() + BLOCK_M_SIZE - 1) // BLOCK_M_SIZE,
    #         (num_cols + BLOCK_N_SIZE - 1) // BLOCK_N_SIZE)
    BLOCK_M_SIZE, BLOCK_N_SIZE = 8, triton.next_power_of_2(num_cols)
    grid = ((indices.numel() + BLOCK_M_SIZE - 1) // BLOCK_M_SIZE, 1)
    index_select_bwd_row_lock[grid](grad_output,
                                    grad_unique_values,
                                    locks,
                                    indices,
                                    num_rows=num_rows,
                                    num_cols=num_cols,
                                    num_indices=num_indices,
                                    BLOCK_M_SIZE=BLOCK_M_SIZE,
                                    BLOCK_N_SIZE=BLOCK_N_SIZE,
                                    num_warps=4)
    return grad_unique_values, None


@triton.jit
def index_select_bwd_batch_lock(
    grad_outputs,
    indices,
    grad_unique_values,
    Lock,
    num_rows: int,
    num_cols: int,
    num_indices: int,
    BLOCK_SIZE: tl.constexpr,
    BLOCK_SIZE_COLS: tl.constexpr,
):
  pid = tl.program_id(axis=0).to(tl.int64)
  off_m = pid * BLOCK_SIZE + tl.arange(0, BLOCK_SIZE)
  source_mask = off_m < num_indices
  indices = tl.load(indices + off_m, mask=source_mask, other=-1)
  dest_mask = (indices >= 0) & (indices < num_rows) & source_mask

  tl_print("[INIT] [PID] [off_m], [indices], [dest_mask]", pid, off_m, indices,
           dest_mask)

  zeros = tl.full((BLOCK_SIZE,), 0, dtype=indices.dtype)
  ones = tl.full((BLOCK_SIZE,), 1, dtype=indices.dtype)

  # Note: 将无效索引映射到同一个虚拟锁位置 -- 第num_rows个元素
  safe_indices = tl.where(dest_mask, indices, num_rows)
  lock_ptrs = Lock + safe_indices
  # Note: "'InterpreterBuilder' object has no attribute 'get_int1_ty'")
  task_done = tl.zeros((BLOCK_SIZE,), dtype=tl.int32)
  keep_looping = True  # Note: unsupported AST node type: Break

  while keep_looping:
    old_locks = tl.atomic_cas(lock_ptrs, zeros, ones)
    new_locks = tl.load(lock_ptrs)
    tl_print("debug ruiteng", old_locks, new_locks, safe_indices)
    acquired_mask = old_locks == 0
    cur_dest_mask = acquired_mask & dest_mask & (task_done == 0)

    tl_print(
        "[LOCK] [pid] [old_locks], [acquired_mask], [cur_dest_mask]",
        pid,
        old_locks,
        acquired_mask,
        cur_dest_mask,
    )

    if tl.sum(cur_dest_mask.to(tl.int32), axis=0) > 0:
      for col_block_start in range(0, num_cols, BLOCK_SIZE_COLS):
        off_cols = col_block_start + tl.arange(0, BLOCK_SIZE_COLS)
        col_mask = off_cols < num_cols
        load_store_dest_mask = col_mask[None, :] & cur_dest_mask[:, None]

        grad_ptrs = grad_outputs + off_m[:, None] * num_cols + off_cols[None, :]
        grad_vals = tl.load(grad_ptrs, mask=load_store_dest_mask, other=0.0)
        tl_print(
            "[LOAD_VAL] [pid] [col_block] [grad_vals]",
            pid,
            col_block_start,
            grad_vals,
        )

        dest_ptrs = (grad_unique_values + indices[:, None] * num_cols +
                     off_cols[None, :])

        old_values = tl.load(dest_ptrs, mask=load_store_dest_mask, other=0.0)
        tl_print("[BEFORE ADD] [pid] [old_values]", pid, old_values)
        new_values = old_values + grad_vals
        tl.store(dest_ptrs, new_values, mask=load_store_dest_mask)
        tl_print("[AFTER ADD] [pid] [delta] [new_val]", pid, grad_vals,
                 new_values)
    tl.debug_barrier()
    tl.atomic_xchg(lock_ptrs, 0, mask=acquired_mask)
    task_done = ((task_done > 0) | cur_dest_mask | (dest_mask == 0)).to(
        tl.int32)
    lock_ptrs = Lock + tl.where(task_done == 0, indices,
                                num_rows)  # tl.atomic_cas doesn't support mask
    all_tasks_done = (tl.sum((dest_mask & (task_done == 0)).to(tl.int32),
                             axis=0) == 0)
    tl_print(
        "[UNLOCK] [acquired_mask], [cur_dest_mask], [task_done], [all_tasks_done]",
        acquired_mask,
        cur_dest_mask,
        task_done,
        all_tasks_done,
    )
    if all_tasks_done:
      keep_looping = False
      tl_print("[EXIT]: All tasks done.", pid)


class IndexSelect_TritonBatchLock(torch.autograd.Function):

  @staticmethod
  @custom_fwd(device_type="cuda", cast_inputs=torch.float32)
  def forward(ctx, unique_values: torch.Tensor, indices: torch.Tensor):
    output, num_rows, num_cols, num_indices = _index_select_forward_common(
        unique_values, indices)
    ctx.save_for_backward(indices)
    ctx.input_shape = unique_values.shape
    ctx.input_dtype = unique_values.dtype
    ctx.input_device = unique_values.device
    ctx.num_rows = num_rows
    ctx.num_cols = num_cols
    ctx.num_indices = num_indices
    return output

  @staticmethod
  @custom_bwd(device_type="cuda")
  def backward(ctx, *grad_outputs: list[torch.Tensor]):
    (indices,) = ctx.saved_tensors
    input_shape = ctx.input_shape
    input_dtype = ctx.input_dtype
    input_device = ctx.input_device
    num_rows = ctx.num_rows
    num_cols = ctx.num_cols
    num_indices = ctx.num_indices

    grad_output = grad_outputs[0].contiguous()
    grad_unique_values = torch.zeros(input_shape,
                                     dtype=input_dtype,
                                     device=input_device)

    if num_indices > 0 and num_rows > 0 and num_cols > 0:
      Lock = torch.zeros(num_rows + 1, dtype=indices.dtype, device=input_device)
      Lock[num_rows] = 1

      BLOCK_SIZE = min(32, triton.next_power_of_2(num_indices))
      BLOCK_SIZE_COLS = triton.next_power_of_2(num_cols)
      grid = ((num_indices + BLOCK_SIZE - 1) // BLOCK_SIZE, 1)
      index_select_bwd_batch_lock[grid](
          grad_output,
          indices,
          grad_unique_values,
          Lock,
          num_rows,
          num_cols,
          num_indices,
          BLOCK_SIZE=BLOCK_SIZE,
          BLOCK_SIZE_COLS=BLOCK_SIZE_COLS,
      )
    return grad_unique_values, None


class IndexSelect_NativeScatterAdd(torch.autograd.Function):

  @staticmethod
  @custom_fwd(device_type="cuda", cast_inputs=torch.float32)
  def forward(ctx, unique_values: torch.Tensor, indices: torch.Tensor):
    output, num_rows, num_cols, num_indices = _index_select_forward_common(
        unique_values, indices)
    ctx.save_for_backward(indices)
    ctx.input_shape = unique_values.shape
    ctx.input_dtype = unique_values.dtype
    ctx.input_device = unique_values.device
    return output

  @staticmethod
  @custom_bwd(device_type="cuda")
  def backward(ctx, *grad_outputs: list[torch.Tensor]):
    (indices,) = ctx.saved_tensors
    grad_output = grad_outputs[0].contiguous()
    grad_unique_values = torch.zeros(ctx.input_shape,
                                     dtype=ctx.input_dtype,
                                     device=ctx.input_device)

    # Flatten indices and grad_output if they are batched
    if indices.dim() > 1:
      indices_flat = indices.flatten()
      # Reshape grad_output to (B * num_indices, D)
      grad_output_flat = grad_output.reshape(-1, grad_output.shape[-1])
    else:
      indices_flat = indices
      grad_output_flat = grad_output

    # Create a mask to filter out indices with value -1
    valid_mask = indices_flat != -1
    valid_indices = indices_flat[valid_mask].to(torch.int64)
    valid_grad_output = grad_output_flat[valid_mask]

    if valid_indices.numel() > 0:
      # scatter_add_ 需要 index 的形状能广播到 src 的形状
      # index: [M_valid], src: [M_valid, D]
      # 我们将 valid_indices 扩展为 [M_valid, 1]，scatter_add_ 会自动处理广播
      expanded_valid_indices = valid_indices.unsqueeze(1)  # Shape: [M_valid, 1]

      # dim=0 表示沿着 grad_unique_values 的第0维 (N维) 进行累加
      # expanded_valid_indices ([M_valid, 1]) 会被广播以匹配 valid_grad_output ([M_valid, D])
      grad_unique_values.scatter_add_(
          0,
          expanded_valid_indices.expand_as(valid_grad_output),
          valid_grad_output,
      )

    return grad_unique_values, None


# @triton.autotune(configs=[
#     triton.Config({
#         'BLOCK_SIZE_UNIQUE': 1,
#         'BLOCK_SIZE_COLS': 128,
#     },
#                   num_warps=4),
#     triton.Config({
#         'BLOCK_SIZE_UNIQUE': 1,
#         'BLOCK_SIZE_COLS': 256,
#     },
#                   num_warps=8),
#     triton.Config({
#         'BLOCK_SIZE_UNIQUE': 2,
#         'BLOCK_SIZE_COLS': 64,
#     }, num_warps=4),
#     triton.Config({
#         'BLOCK_SIZE_UNIQUE': 2,
#         'BLOCK_SIZE_COLS': 64,
#     }, num_warps=8),
#     triton.Config({
#         'BLOCK_SIZE_UNIQUE': 2,
#         'BLOCK_SIZE_COLS': 64,
#     },
#                   num_warps=16),
#     triton.Config({
#         'BLOCK_SIZE_UNIQUE': 2,
#         'BLOCK_SIZE_COLS': 128,
#     },
#                   num_warps=4),
#     triton.Config({
#         'BLOCK_SIZE_UNIQUE': 4,
#         'BLOCK_SIZE_COLS': 64,
#     }, num_warps=4),
#     triton.Config({
#         'BLOCK_SIZE_UNIQUE': 4,
#         'BLOCK_SIZE_COLS': 64,
#     }, num_warps=4),
#     triton.Config({
#         'BLOCK_SIZE_UNIQUE': 4,
#         'BLOCK_SIZE_COLS': 128,
#     },
#                   num_warps=4),
#     triton.Config({
#         'BLOCK_SIZE_UNIQUE': 4,
#         'BLOCK_SIZE_COLS': 64,
#     }, num_warps=4),
#     triton.Config({
#         'BLOCK_SIZE_UNIQUE': 8,
#         'BLOCK_SIZE_COLS': 64,
#     }, num_warps=4),
# ],
#                  key=['num_unique_indices', 'num_cols', 'max_segment_length'])
@triton.jit
def index_select_bwd_segmented(
    sorted_grad_output_ptr,
    unique_indices_ptr,
    segment_start_offsets_ptr,
    segment_end_offsets_ptr,
    grad_unique_values_ptr,
    num_unique_indices: int,
    num_cols: int,
    max_segment_length: int,
    BLOCK_SIZE_UNIQUE: tl.constexpr,
    BLOCK_SIZE_COLS: tl.constexpr,
    BLOCK_SIZE_SEGMENT: tl.constexpr,
):
  pid_unique = tl.program_id(axis=0).to(tl.int64)
  off_unique_idx = pid_unique * BLOCK_SIZE_UNIQUE + tl.arange(
      0, BLOCK_SIZE_UNIQUE)
  unique_mask = off_unique_idx < num_unique_indices

  unique_indices = tl.load(unique_indices_ptr + off_unique_idx,
                           mask=unique_mask,
                           other=0)
  segment_start_offsets = tl.load(segment_start_offsets_ptr + off_unique_idx,
                                  mask=unique_mask,
                                  other=0)
  segment_end_offsets = tl.load(segment_end_offsets_ptr + off_unique_idx,
                                mask=unique_mask,
                                other=0)

  segment_lengths = segment_end_offsets - segment_start_offsets
  segment_lengths = tl.where(unique_mask, segment_lengths, 0)

  for col_block_start in range(0, num_cols, BLOCK_SIZE_COLS):
    off_cols = col_block_start + tl.arange(0, BLOCK_SIZE_COLS)
    col_mask = off_cols < num_cols
    acc = tl.zeros((BLOCK_SIZE_UNIQUE, BLOCK_SIZE_COLS), dtype=tl.float32)
    for segment_block_start in range(0, max_segment_length, BLOCK_SIZE_SEGMENT):
      # Shape: [BLOCK_SIZE_SEGMENT]
      off_segment_relative = segment_block_start + tl.arange(
          0, BLOCK_SIZE_SEGMENT)
      # Shape: [BLOCK_SIZE_UNIQUE, BLOCK_SIZE_SEGMENT]
      elem_idx = segment_start_offsets[:, None] + off_segment_relative[None, :]
      # Shape: [BLOCK_SIZE_UNIQUE, BLOCK_SIZE_SEGMENT]
      segment_mask = off_segment_relative[None, :] < segment_lengths[:, None]

      # Shape: [BLOCK_SIZE_UNIQUE, BLOCK_SIZE_SEGMENT, BLOCK_SIZE_COLS]
      grad_ptrs = (sorted_grad_output_ptr + elem_idx[:, :, None] * num_cols +
                   off_cols[None, None, :])
      # Shape: [BLOCK_SIZE_UNIQUE, BLOCK_SIZE_SEGMENT, BLOCK_SIZE_COLS]
      load_mask = segment_mask[:, :, None] & col_mask[None, None, :]
      # Shape: [BLOCK_SIZE_UNIQUE, BLOCK_SIZE_SEGMENT, BLOCK_SIZE_COLS]
      grad_vals = tl.load(grad_ptrs, mask=load_mask, other=0.0)
      # Shape of tl.sum result: [BLOCK_SIZE_UNIQUE, BLOCK_SIZE_COLS]
      acc += tl.sum(grad_vals, axis=1)

    grad_unique_values_ptrs = (grad_unique_values_ptr +
                               unique_indices[:, None] * num_cols +
                               off_cols[None, :])
    write_mask = unique_mask[:, None] & col_mask[None, :]
    tl.store(grad_unique_values_ptrs, acc, mask=write_mask)


class IndexSelect_TritonSorted(torch.autograd.Function):

  @staticmethod
  @custom_fwd(device_type="cuda", cast_inputs=torch.float32)
  def forward(ctx, unique_values: torch.Tensor, indices: torch.Tensor):
    # Forward pass is the same, use the common helper
    output, num_rows, num_cols, num_indices = _index_select_forward_common(
        unique_values, indices)

    # Save necessary tensors and shapes for backward
    # Note: We don't strictly need to save unique_values itself if we only need its shape/dtype
    ctx.save_for_backward(indices)
    ctx.input_shape = unique_values.shape
    ctx.input_dtype = unique_values.dtype
    ctx.input_device = unique_values.device
    return output

  @staticmethod
  @custom_bwd(device_type="cuda")
  def backward(ctx, *grad_outputs: list[torch.Tensor]):
    (indices,) = ctx.saved_tensors
    # Handle potential 1D input for unique_values
    if len(ctx.input_shape) == 1:
      num_rows = ctx.input_shape[0]
      num_cols = 1
    else:
      num_rows, num_cols = ctx.input_shape

    grad_output = grad_outputs[0].contiguous()
    grad_unique_values = torch.zeros(ctx.input_shape,
                                     dtype=ctx.input_dtype,
                                     device=ctx.input_device)
    if indices.dim() > 1:
      indices_flat = indices.flatten()
      grad_output_flat = grad_output.reshape(-1, num_cols)
    else:
      indices_flat = indices
      grad_output_flat = grad_output.reshape(-1, num_cols)

    num_indices_total = indices_flat.numel()

    if num_indices_total == 0 or num_rows == 0 or num_cols == 0:
      return grad_unique_values, None

    sorted_indices, perm = torch.sort(indices_flat)
    sorted_grad_output = grad_output_flat[perm]
    unique_indices, segment_counts = torch.unique_consecutive(
        sorted_indices, return_counts=True)
    num_unique_indices = unique_indices.numel()
    segment_start_offsets = torch.cat((
        torch.tensor([0], device=ctx.input_device, dtype=torch.long),
        torch.cumsum(segment_counts[:-1], dim=0),
    ))

    max_segment_length = 0
    if num_unique_indices > 0:
      segment_end_offsets = segment_start_offsets + segment_counts
      max_segment_length = torch.max(segment_counts).item()
    else:
      segment_end_offsets = torch.empty_like(segment_start_offsets)

    if num_unique_indices > 0 and max_segment_length > 0:
      sorted_grad_output = sorted_grad_output.contiguous()
      unique_indices = unique_indices.contiguous()
      segment_start_offsets = segment_start_offsets.contiguous()
      segment_end_offsets = segment_end_offsets.contiguous()
      grid_unique = lambda meta: (triton.cdiv(num_unique_indices, meta[
          "BLOCK_SIZE_UNIQUE"]),)
      index_select_bwd_segmented[grid_unique](
          sorted_grad_output,
          unique_indices,
          segment_start_offsets,
          segment_end_offsets,
          grad_unique_values,
          num_unique_indices,
          num_cols,
          max_segment_length,
          BLOCK_SIZE_UNIQUE=1,
          BLOCK_SIZE_COLS=triton.next_power_of_2(num_cols),
          BLOCK_SIZE_SEGMENT=128,
      )  # triton.next_power_of_2(max_segment_length)
    if grad_unique_values.shape != ctx.input_shape:
      grad_unique_values = grad_unique_values.reshape(ctx.input_shape)

    return grad_unique_values, None


index_select_torch = lambda unique_values, indices: torch.index_select(
    unique_values, 0, indices)
index_select_torch_native_scatter_add = IndexSelect_NativeScatterAdd.apply
index_select_torch_compiled = torch.compile(
    index_select_torch_native_scatter_add)
index_select_triton_atomic_add = IndexSelect_TritonAtomicAdd.apply
index_select_triton_atomic_add_relaxed = IndexSelect_TritonAtomicAddRelaxed.apply
index_select_triton_reorder = IndexSelect_TritonReorder.apply
index_select_triton_reorder_2d = IndexSelect_TritonReorder2D.apply
index_select_triton_row_lock = IndexSelect_TritonRowLock.apply
index_select_triton_batch_lock = IndexSelect_TritonBatchLock.apply
index_select_triton_sorted = IndexSelect_TritonSorted.apply
index_select_triton_sorted_compiled = torch.compile(index_select_triton_sorted)
index_select = IndexSelect.apply
