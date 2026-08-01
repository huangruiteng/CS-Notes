import torch
import triton
import triton.language as tl

# performance:
#    batch_size  weight_size       triton       torch  torch_scripted  Torch Compile  Torch Compile (Max-Autotuned)
# 0         4.0          4.0     0.035503    0.014851        0.034884       0.036364                       0.007952
# 1        16.0          8.0     0.292683    0.119107        0.276657       0.289157                       0.067797
# 2        64.0         16.0     2.145251    0.894063        2.232558       2.181818                       0.558952
# 3       256.0         32.0    14.912622    6.872483       16.879121      16.879121                       4.348195
# 4      1024.0         64.0   121.064037   51.848101      130.723400     132.129029                      28.313365
# 5      4096.0        128.0   759.104267  312.572329      675.628857     780.190482                     111.172175
# 6     16384.0        256.0  2340.571447  878.204347     1482.435374    2358.116889                    1014.423703
# 7     65536.0        512.0  3461.598926  921.858824     1861.377574    3458.744370                    1191.620141


from torch._inductor import config
config.cache_size_limit = 16

@triton.jit
def fused_add_mul_activation_kernel(x_ptr, bias_ptr, in_ptr,
                                    num_weights: tl.constexpr,
                                    xnumel: tl.constexpr,
                                    multiplier: tl.constexpr,
                                    activation: tl.constexpr,
                                    BLOCK_SIZE: tl.constexpr):
    xoffset = tl.program_id(0) * BLOCK_SIZE
    index = xoffset + tl.arange(0, BLOCK_SIZE)[:]
    mask = index < xnumel
    bias_index = index % num_weights
    tmp0 = tl.load(x_ptr + index, mask)
    tmp1 = tl.load(bias_ptr + bias_index, mask, eviction_policy='evict_last')
    tmp3 = tl.load(in_ptr + index, mask)
    activ_input = multiplier * tmp3 + tmp0 + tmp1
    if activation == "sigmoid":
        ma_result = tl.sigmoid(activ_input)
        # option 2 - calculate sigmoid using exp
        # ma_result = 1.0 / (1.0 + tl.exp(-sigmoid_input))
        # option 3: fast sigmoid - inaccurate but faster
        # ma_result = 1.0 / (1.0 + tl.abs(sigmoid_input))
    elif activation == "relu":
        ma_result = tl.maximum(0, activ_input)

    tl.store(x_ptr + index, ma_result, mask)


def fused_add_mul_activation_torch(in_out_tensor: torch.Tensor, bias: torch.Tensor,
                                   in_tensor: torch.Tensor) -> torch.Tensor:
    # print("calling fused_add_mul_relu_torch")
    grid = lambda meta: (triton.cdiv(in_out_tensor.numel(), meta['BLOCK_SIZE']),)
    BLOCK_SIZE = min(2048, in_out_tensor.numel())
    fused_add_mul_activation_kernel[grid](in_out_tensor, bias, in_tensor,
                                          bias.numel(),
                                          in_out_tensor.numel(),
                                          multiplier=0.5,
                                          activation="sigmoid",
                                          BLOCK_SIZE=BLOCK_SIZE)
    return in_out_tensor


def add_mul_activation_torch(in_out_tensor: torch.Tensor, bias: torch.Tensor, in_tensor: torch.Tensor) -> torch.Tensor:
    return torch.sigmoid(in_out_tensor + 0.5 * in_tensor + bias)


def get_inputs(batch_size: int = 8, weight_size: int = 8, add_manual_seed: bool = False):
    if add_manual_seed:
        torch.manual_seed(0)
    dense_size = (batch_size, weight_size)
    in_out_tensor = torch.randn(dense_size, device='cuda', dtype=torch.float32)
    in_tensor = torch.randn(dense_size, device='cuda', dtype=torch.float32)
    bias = torch.randn((1, weight_size), device='cuda', dtype=torch.float32)
    return in_out_tensor, in_tensor, bias


add_mul_activation_torch_scripted = torch.jit.script(add_mul_activation_torch, example_inputs=[get_inputs()])


@triton.testing.perf_report(
    triton.testing.Benchmark(
        x_names=['batch_size', 'weight_size'],  # Argument names to use as an x-axis for the plot.
        x_vals=[(2 ** i, 2 ** j) for i, j in zip(range(2, 18, 2), range(2, 10, 1))],
        # Different possible values for `x_name`.
        x_log=True,  # x axis is logarithmic.
        line_arg='provider',  # Argument name whose value corresponds to a different line in the plot.
        line_vals=['triton', 'torch', 'torch_scripted', 'torch_compile', 'torch_compile_max_autotune'],
        line_names=['triton', 'torch', 'torch_scripted', 'Torch Compile', 'Torch Compile (Max-Autotuned)'],
        styles=[('blue', '-'), ('green', ':'), ("red", '-.'), ('purple', '--'), ('orange', '-')],
        ylabel='GB/s',  # Label name for the y-axis.
        plot_name='performance',  # Name for the plot. Used also as a file name for saving the plot.
        args={},  # Values for function arguments not in `x_names` and `y_name`.
    ))
def benchmark(batch_size, weight_size, provider):
    in_out_tensor, in_tensor, bias = get_inputs(batch_size=batch_size, weight_size=weight_size, add_manual_seed=True)
    quantiles = [0.5, 0.2, 0.8]
    if provider == "triton":
        ms, min_ms, max_ms = triton.testing.do_bench(
            lambda: fused_add_mul_activation_torch(in_out_tensor, bias, in_tensor),
            quantiles=quantiles)
    if provider == "torch":
        ms, min_ms, max_ms = triton.testing.do_bench(lambda: add_mul_activation_torch(in_out_tensor, bias, in_tensor),
                                                     quantiles=quantiles)

    if provider == "torch_scripted":
        ms, min_ms, max_ms = triton.testing.do_bench(
            lambda: add_mul_activation_torch_scripted(in_out_tensor, bias, in_tensor),
            quantiles=quantiles)

    if provider == "torch_compile":
        compiled_fn = torch.compile(add_mul_activation_torch, fullgraph=True, dynamic=False)
        ms, min_ms, max_ms = triton.testing.do_bench(
            lambda: compiled_fn(in_out_tensor, bias, in_tensor),
            quantiles=quantiles)
    if provider == "torch_compile_max_autotune":
        compiled_fn = torch.compile(add_mul_activation_torch, fullgraph=True, dynamic=False, mode='max-autotune')
        ms, min_ms, max_ms = triton.testing.do_bench(
            lambda: compiled_fn(in_out_tensor, bias, in_tensor),
            quantiles=quantiles)
    gbps = lambda ms: 12 * (batch_size * weight_size) / ms * 1e-6
    return gbps(ms), gbps(max_ms), gbps(min_ms)


if __name__ == "__main__":
    # # The flag below controls whether to allow TF32 on matmul. This flag defaults to False
    # # in PyTorch 1.12 and later.
    torch.backends.cuda.matmul.allow_tf32 = True
    #
    # # The flag below controls whether to allow TF32 on cuDNN. This flag defaults to True.
    torch.backends.cudnn.allow_tf32 = True
    benchmark.run(print_data=True, show_plots=True)
