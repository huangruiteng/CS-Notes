# vector-add-performance:
# size       Triton         CUDA  CUDA Coarsened  CUDA Privatized
# 0        4096.0     9.088757     8.629213        8.677966         8.581006
# 1        8192.0    17.964912    17.258427       16.786886        17.355933
# 2       16384.0    34.516854    33.391304       33.032257        33.391304
# 3       32768.0    67.516482    66.782607       65.015874        67.147542
# 4       65536.0   132.129029   127.999995      129.347364       130.723400
# 5      131072.0   260.063494   246.994973      248.242431       239.765849
# 6      262144.0   463.698115   431.157886      440.825121       429.275114
# 7      524288.0   792.774204   714.938186      744.727267       712.347810
# 8     1048576.0  1285.019601  1077.304067     1180.828816      1086.232069
# 9     2097152.0  1850.428211  1459.057591     1648.704423      1472.719124
# 10    4194304.0  2390.370804  1726.524679     2058.722522      1726.524679
# 11    8388608.0  2864.961804  1966.080050     2448.037343      1974.719369
# 12   16777216.0  3235.513464  2121.907594     2760.621457      2135.592610
# 13   33554432.0  3461.598926  2221.559392     2957.901411      2236.962044
# 14   67108864.0  3606.969284  2279.203436     3072.750022      2297.409519
# 15  134217728.0  3670.092554  2292.595792     3104.400700      2306.939119

# TODO:
# if provider == 'torch':
    # ms, min_ms, max_ms = triton.testing.do_bench(lambda: x + y,
    #                                              quantiles=quantiles)


import torch
import triton
import triton.language as tl
import triton.testing

from gpu_kernel_utils import load_cuda, cuda_begin

@triton.jit
def add_kernel(
    x_ptr,
    y_ptr,
    output_ptr,
    n_elements,
    BLOCK_SIZE: tl.constexpr,
):
    pid = tl.program_id(axis=0)
    block_start = pid * BLOCK_SIZE
    offsets = block_start + tl.arange(0, BLOCK_SIZE)
    mask = offsets < n_elements
    x = tl.load(x_ptr + offsets, mask=mask)
    y = tl.load(y_ptr + offsets, mask=mask)
    output = x + y
    tl.store(output_ptr + offsets, output, mask=mask)

def triton_add(x: torch.Tensor, y: torch.Tensor):
    output = torch.empty_like(x)
    assert x.is_cuda and y.is_cuda and output.is_cuda
    n_elements = output.numel()
    # The SPMD launch grid denotes the number of kernel instances that run in parallel.
    # It is analogous to CUDA launch grids. It can be either Tuple[int], or Callable(metaparameters) -> Tuple[int].
    # In this case, we use a 1D grid where the size is the number of blocks:
    grid = lambda meta: (triton.cdiv(n_elements, meta['BLOCK_SIZE']),)
    add_kernel[grid](x, y, output, n_elements, BLOCK_SIZE=1024)
    return output

    
cuda_src = cuda_begin + r'''
__global__ void VecAdd(float* A, float* B, float* C, int N)
{
    int i = blockIdx.x * blockDim.x + threadIdx.x;
    if (i < N)
        C[i] = A[i] + B[i];
}

__global__ void VecAddCoarsened(float* A, float* B, float* C, int N)
{
    int i = (blockIdx.x * blockDim.x + threadIdx.x) * 2;
    if (i < N)
        C[i] = A[i] + B[i];
    if (i + 1 < N)
        C[i + 1] = A[i + 1] + B[i + 1];
}

__global__ void VecAddPrivatized(float* A, float* B, float* C, int N) {
    int i = threadIdx.x + blockIdx.x * blockDim.x;
    if (i < N) {
        float A_private = A[i]; // Load into private memory
        float B_private = B[i]; // Load into private memory
        C[i] = A_private + B_private;
    }
}

void VecAdd(torch::Tensor A, torch::Tensor B, torch::Tensor C) {
    int n_elements = A.numel();
    if (n_elements == 0) return;

    const int threads_per_block = 128;
    const int blocks = cdiv(n_elements, threads_per_block);

    VecAdd<<<blocks, threads_per_block>>>(
        A.data_ptr<float>(),
        B.data_ptr<float>(),
        C.data_ptr<float>(),
        n_elements
    );
    C10_CUDA_KERNEL_LAUNCH_CHECK();
}

void VecAddCoarsened(torch::Tensor A, torch::Tensor B, torch::Tensor C) {
    int n_elements = A.numel();
    if (n_elements == 0) return;

    const int threads_per_block = 128;
    const int blocks = cdiv(n_elements, threads_per_block * 2);

    VecAddCoarsened<<<blocks, threads_per_block>>>(
        A.data_ptr<float>(),
        B.data_ptr<float>(),
        C.data_ptr<float>(),
        n_elements
    );
    C10_CUDA_KERNEL_LAUNCH_CHECK();
}

void VecAddPrivatized(torch::Tensor A, torch::Tensor B, torch::Tensor C) {
    int n_elements = A.numel();
    if (n_elements == 0) return;

    const int threads_per_block = 128;
    const int blocks = cdiv(n_elements, threads_per_block);

    VecAddPrivatized<<<blocks, threads_per_block>>>(
        A.data_ptr<float>(),
        B.data_ptr<float>(),
        C.data_ptr<float>(),
        n_elements
    );
    C10_CUDA_KERNEL_LAUNCH_CHECK();
}
'''

cpp_src = r'''
void VecAdd(torch::Tensor A, torch::Tensor B, torch::Tensor C);
void VecAddCoarsened(torch::Tensor A, torch::Tensor B, torch::Tensor C);
void VecAddPrivatized(torch::Tensor A, torch::Tensor B, torch::Tensor C);
'''
    
vec_add_module = load_cuda(
    cuda_src,
    cpp_src, ['VecAdd', 'VecAddCoarsened','VecAddPrivatized'],
    opt=True,
    verbose=True,
    name='vec_add',
)

def cuda_vec_add(A, B):
    C = torch.empty_like(A)
    vec_add_module.VecAdd(A, B, C)
    return C

def cuda_vec_add_coarsened(A, B):
    C = torch.empty_like(A)
    vec_add_module.VecAddCoarsened(A, B, C)
    return C

def cuda_vec_add_privatized(A, B):
    C = torch.empty_like(A)
    vec_add_module.VecAddPrivatized(A, B, C)
    return C

torch.manual_seed(0)
size = 1024
x = torch.rand(size, device='cuda')
y = torch.rand(size, device='cuda')

triton_result = triton_add(x, y)
cuda_result = cuda_vec_add(x, y)
cuda_coarsened_result = cuda_vec_add_coarsened(x, y)
cuda_privatized_result = cuda_vec_add_privatized(x, y)

torch.allclose(triton_result, cuda_result)
torch.allclose(triton_result, cuda_coarsened_result)
torch.allclose(triton_result, cuda_privatized_result)


@triton.testing.perf_report(
    triton.testing.Benchmark(
        x_names=['size'],
        x_vals=[2 ** i for i in range(12, 28, 1)],
        line_arg='provider',
        line_vals=['triton', 'cuda', 'cuda_coarsened', 'cuda_privatized'],
        line_names=['Triton', 'CUDA', 'CUDA Coarsened', 'CUDA Privatized'],
        styles=[('blue', '-'), ('green', '-'), ('red', '-'), ('purple', '-')],
        ylabel='GB/s',
        plot_name='vector-add-performance',
        args={},
    )
)
def benchmark(size, provider):
    x = torch.rand(size, device='cuda', dtype=torch.float32)
    y = torch.rand(size, device='cuda', dtype=torch.float32)
    quantiles = [0.5, 0.2, 0.8]
    if provider == 'triton':
        ms, min_ms, max_ms = triton.testing.do_bench(lambda: triton_add(x, y), quantiles=quantiles)
    elif provider == 'cuda':
        ms, min_ms, max_ms = triton.testing.do_bench(lambda: cuda_vec_add(x, y), quantiles=quantiles)
    elif provider == 'cuda_coarsened':
        ms, min_ms, max_ms = triton.testing.do_bench(lambda: cuda_vec_add_coarsened(x, y), quantiles=quantiles)
    elif provider == 'cuda_privatized':
        ms, min_ms, max_ms = triton.testing.do_bench(lambda: cuda_vec_add_privatized(x, y), quantiles=quantiles)
    gbps = lambda ms: 12 * size / ms * 1e-6
    return gbps(ms), gbps(max_ms), gbps(min_ms)

benchmark.run(print_data=True, save_path='.')