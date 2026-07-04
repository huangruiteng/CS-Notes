@triton.autotune(
  configs=[
    triton.Config(kwargs={'BLOCK_SIZE': 128}, num_warps=2),
    triton.Config(kwargs={'BLOCK_SIZE': 256}, num_warps=4),
    triton.Config(kwargs={'BLOCK_SIZE': 512}, num_warps=4),
    triton.Config(kwargs={'BLOCK_SIZE': 1024}, num_warps=8),
    triton.Config(kwargs={'BLOCK_SIZE': 2048}, num_warps=8),
    triton.Config(kwargs={'BLOCK_SIZE': 4096}, num_warps=16),
  ],
  key=('n_cols',)
)
@triton.jit
def square_kernel_autotune(output_ptr, input_ptr, input_row_stride, output_row_stride, n_cols,
                           BLOCK_SIZE: tl.constexpr):
  return _square_kernel(output_ptr, input_ptr, input_row_stride, output_row_stride, n_cols, BLOCK_SIZE)


@triton.jit
def square_kernel_no_autotune(output_ptr, input_ptr, input_row_stride, output_row_stride, n_cols,
                              BLOCK_SIZE: tl.constexpr):
  return _square_kernel(output_ptr, input_ptr, input_row_stride, output_row_stride, n_cols, BLOCK_SIZE)


@triton.jit
def _square_kernel(output_ptr, input_ptr, input_row_stride, output_row_stride, n_cols, BLOCK_SIZE: tl.constexpr):
    row_idx = tl.program_id(0)
    input_row_start = input_ptr + row_idx * input_row_stride
    output_row_start = output_ptr + row_idx * output_row_stride

    num_blocks = (n_cols + BLOCK_SIZE - 1) // BLOCK_SIZE

    for block_idx in range(num_blocks):
        block_start_col = block_idx * BLOCK_SIZE
        col_offsets = tl.arange(0, BLOCK_SIZE) + block_start_col
        input_block_ptrs = input_row_start + col_offsets
        output_block_ptrs = output_row_start + col_offsets

        input_block = tl.load(input_block_ptrs, mask=col_offsets < n_cols, other=-float('inf'))
        square_output = input_block * input_block

        tl.store(output_block_ptrs, square_output, mask=col_offsets < n_cols)

def _calculate_block_size_and_warps(n_cols):
  BLOCK_SIZE = triton.next_power_of_2(n_cols)
  # BLOCK_SIZE = 1024
  num_warps = 4
  if BLOCK_SIZE >= 2048:
    num_warps = 8
  if BLOCK_SIZE >= 4096:
    num_warps = 16
  return BLOCK_SIZE, num_warps


def square_autotune(x):
  n_rows, n_cols = x.shape
  # Allocate output
  y = torch.empty_like(x)
  # Enqueue kernel. The 1D launch grid is simple: we have one kernel instance per row of the input matrix
  square_kernel_autotune[(n_rows,)](
    y,
    x,
    x.stride(0),
    y.stride(0),
    n_cols,
  )
  return y


def square_no_autotune_large_block(x):
  n_rows, n_cols = x.shape
  BLOCK_SIZE, num_warps = _calculate_block_size_and_warps(n_cols)
  # Allocate output
  y = torch.empty_like(x)
  # Enqueue kernel. The 1D launch grid is simple: we have one kernel instance per row of the input matrix
  square_kernel_no_autotune[(n_rows,)](
    y,
    x,
    x.stride(0),
    y.stride(0),
    n_cols,
    num_warps=num_warps,
    BLOCK_SIZE=BLOCK_SIZE,
  )
  return y


def square_no_autotune_fixed_block(x):
  n_rows, n_cols = x.shape
  BLOCK_SIZE, num_warps = 1024, 4
  # Allocate output
  y = torch.empty_like(x)
  # Enqueue kernel. The 1D launch grid is simple: we have one kernel instance per row of the input matrix
  square_kernel_no_autotune[(n_rows,)](
    y,
    x,
    x.stride(0),
    y.stride(0),
    n_cols,
    num_warps=num_warps,
    BLOCK_SIZE=BLOCK_SIZE,
  )
  return y


torch.manual_seed(0)
x = torch.randn(1823, 781, device='cuda')
y_triton_autotune = square_autotune(x)
y_triton_no_autotune_large_block = square_no_autotune_large_block(x)
y_triton_no_autotune_fixed_block = square_no_autotune_fixed_block(x)
y_torch_compile = torch.compile(torch.square)(x)

y_torch = torch.square(x)

assert torch.allclose(y_triton_autotune, y_torch), (y_triton_autotune, y_torch)
assert torch.allclose(y_triton_no_autotune_large_block, y_torch), (y_triton_no_autotune_large_block, y_torch)
assert torch.allclose(y_triton_no_autotune_fixed_block, y_torch), (y_triton_no_autotune_fixed_block, y_torch)
assert torch.allclose(y_torch_compile, y_torch), (y_torch_compile, y_torch)


@triton.testing.perf_report(
  triton.testing.Benchmark(
    x_names=['N'],  # argument names to use as an x-axis for the plot
    x_vals=[128 * i for i in range(2, 100)],  # different possible values for `x_name`
    line_arg='provider',  # argument name whose value corresponds to a different line in the plot
    line_vals=[
      'triton-autotune',
      'triton-no-autotune-large-block',
      'triton-no-autotune-fixed-block',
      'torch-native',
      'torch-compile'
    ],  # possible values for `line_arg``
    line_names=[
      "Triton (Autotune)",
      "Triton (No Autotune Large Block)",
      "Triton (No Autotune Fixed Block)",
      "Torch (native)",
      "Torch (compiled)"
    ],  # label name for the lines
    styles=[('blue', '-'), ('red', '-'), ('red', '--'), ('green', '-'), ('green', '--')],  # line styles
    ylabel="GB/s",  # label name for the y-axis
    plot_name="square() performance",  # name for the plot. Used also as a file name for saving the plot.
    args={'M': 4096},  # values for function arguments not in `x_names` and `y_name`
  ))
def benchmark(M, N, provider):
  x = torch.randn(M, N, device='cuda', dtype=torch.float32)
  quantiles = [0.5, 0.2, 0.8]
  if provider == 'torch-native':
    ms, min_ms, max_ms = triton.testing.do_bench(lambda: torch.square(x), quantiles=quantiles)
  elif provider == 'triton-autotune':
    ms, min_ms, max_ms = triton.testing.do_bench(lambda: square_autotune(x), quantiles=quantiles)
  elif provider == 'triton-no-autotune-large-block':
    ms, min_ms, max_ms = triton.testing.do_bench(lambda: square_no_autotune_large_block(x), quantiles=quantiles)
  elif provider == 'triton-no-autotune-fixed-block':
    ms, min_ms, max_ms = triton.testing.do_bench(lambda: square_no_autotune_fixed_block(x), quantiles=quantiles)
  elif provider == 'torch-compile':
    ms, min_ms, max_ms = triton.testing.do_bench(lambda: torch.compile(torch.square)(x), quantiles=quantiles)
  gbps = lambda ms: 2 * x.nelement() * x.element_size() * 1e-9 / (ms * 1e-3)
  return gbps(ms), gbps(max_ms), gbps(min_ms)


benchmark.run(show_plots=True, print_data=True, save_path='.')