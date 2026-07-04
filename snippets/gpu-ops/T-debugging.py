### debug frontend
https://triton-lang.org/main/programming-guide/chapter-3/debugging.html

static_print and static_assert are intended for compile-time debugging.
device_print and device_assert are used for runtime debugging.


TRITON_DEBUG=1

tl.device_print("all_tasks_done:" ,all_tasks_done) # 第一个是str，后面全是tensor

num_warps=1 也可能帮助



### interpret mode


TRITON_INTERPRET=1 python interpret_triton_square.py

@triton.jit()
def square_kernel(output_ptr, input_ptr, input_row_stride, output_row_stride, n_cols, BLOCK_SIZE: tl.constexpr):
  # The rows of the softmax are independent, so we parallelize across those
  row_idx = tl.program_id(0)
  # The stride represents how much we need to increase the pointer to advance 1 row
  row_start_ptr = input_ptr + row_idx * input_row_stride
  # The block size is the next power of two greater than n_cols, so we can fit each
  # row in a single block
  col_offsets = tl.arange(0, BLOCK_SIZE)
  breakpoint()
  input_ptrs = row_start_ptr + col_offsets
  # Load the row into SRAM, using a mask since BLOCK_SIZE may be > than n_cols
  row = tl.load(input_ptrs, mask=col_offsets < n_cols, other=-float('inf'))

  square_output = row * row
  breakpoint()
  # Write back output to DRAM
  output_row_start_ptr = output_ptr + row_idx * output_row_stride
  output_ptrs = output_row_start_ptr + col_offsets
  tl.store(output_ptrs, square_output, mask=col_offsets < n_cols)


print(tensor.handle.data[idx])

### debug autotune

TRITON_PRINT_AUTOTUNING=1

### profiling

https://developer.nvidia.com/nvidia-development-tools-solutions-err_nvgpuctrperm-permission-issue-performance-counters#AllUsersTag

ncu --target-processes all sudo python triton_test.py

### visualization

https://github.com/Deep-Learning-Profiling-Tools/triton-viz

### debug backend

https://github.com/triton-lang/triton?tab=readme-ov-file#tips-for-hacking


