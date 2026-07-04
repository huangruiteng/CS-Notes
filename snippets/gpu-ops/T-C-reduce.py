# TODO:
# 1.COARSE_FACTOR templated
# 2.torch.compile的性能和第一次的shape强相关，有坑
# 3.另一种思路，两层kernel，先局部归约，再全局归约
# 4.Kernel Decomposition: Recursive kernel invocation

# reduce-performance(gbps): compile dynamic=None
#         size   torch.sum  torch.compile(sum)  ReduceSum0  ReduceSum1  ReduceSum2  ReduceSum3  ReduceSum4  ReduceSum5  ReduceSum6(BLOCK_SIZE=128,COARSE_FACTOR=8)
# 0  1048576.0  203.527946          426.944612  124.593159  216.647931  219.551087  322.837433  355.208685  362.077356                                  424.181236

# reduce-performance(gbps): compile dynamic=False
#          size   torch.sum  torch.compile(sum)  ReduceSum0  ReduceSum1  ReduceSum2  ReduceSum3  ReduceSum4  ReduceSum5  ReduceSum6(BLOCK_SIZE=128,COARSE_FACTOR=8)
# 0       128.0    0.060150            0.095238    0.066667    0.070175    0.070485    0.071111    0.071749    0.072398                                    0.070485
# 1       256.0    0.113475            0.196319    0.129555    0.138528    0.139130    0.141593    0.144144    0.144796                                    0.140351
# 2       512.0    0.198758            0.383234    0.244275    0.270042    0.272340    0.279476    0.283186    0.285714                                    0.280702
# 3      1024.0    0.389058            0.748538    0.435374    0.509960    0.509960    0.531120    0.544681    0.549356                                    0.524590
# 4      2048.0    0.744186            1.479769    0.859060    1.003922    1.007874    1.040650    1.071130    1.084746                                    1.019920
# 5      4096.0    1.442254            2.860335    1.735593    2.039841    2.039841    2.115703    2.169491    2.188034                                    2.064516
# 6      8192.0    2.760108            5.626374    3.436242    4.015686    4.015686    4.179592    4.284519    4.320675                                    4.063492
# 7     16384.0    5.132832            8.291498    6.849498    8.031373    8.000000    8.325203    8.533334    8.677966                                    8.126984
# 8     32768.0    8.982456            9.002198   13.473685   15.753846   15.693486   16.253968   16.718367   16.855967                                   15.875970
# 9     65536.0   14.422535           14.422535   26.771242   31.148290   31.148290   32.379446   33.300812   33.436734                                   31.629344
# 10   131072.0   32.572565           32.315581   46.545454   58.099292   58.306053   62.534354   64.758892   64.758892                                   61.363297
# 11   262144.0   64.377213           64.377213   69.571124   96.093840   97.234420  118.296023  125.547889  126.517378                                  120.029299
# 12   524288.0  122.956852          123.187975  100.515335  153.121496  154.202351  201.030670  215.578957  217.727580                                  231.575971
# 13  1048576.0  202.584242          202.584242  124.356737  215.934094  219.183942  322.044215  353.293799  361.079891                                  424.181236



import torch
import triton
import triton.language as tl
import triton.testing

from gpu_kernel_utils import load_cuda, cuda_begin, cdiv

REDUCE_SIZE = 1024

cuda_src = cuda_begin + r'''
// reduce0: Interleaved Addressing
// Problem: highly divergent warps are very inefficient, and % operator is very slow

__global__ void reduce0(int *g_idata, int *g_odata) {
	extern __shared__ int sdata[];
	// each thread loads one element from global to shared mem
	unsigned int tid = threadIdx.x;
	unsigned int i = blockIdx.x*blockDim.x + threadIdx.x;
	sdata[tid] = g_idata[i];
	__syncthreads();
	// do reduction in shared mem
	for(unsigned int s=1; s < blockDim.x; s *= 2) {
		if (tid % (2*s) == 0) {
			sdata[tid] += sdata[tid + s];
		}
		__syncthreads();
	}
	// write result for this block to global mem
	if (tid == 0) atomicAdd(g_odata, sdata[0]);
}

// reduce1: 优化 % operator
// Problem: Shared Memory Bank Conflicts

__global__ void reduce1(int *g_idata, int *g_odata) {
    extern __shared__ int sdata[];
    unsigned int tid = threadIdx.x;
    unsigned int i = blockIdx.x*blockDim.x + threadIdx.x;
    sdata[tid] = g_idata[i];
    __syncthreads();

    for(unsigned int s=1; s < blockDim.x; s *= 2) {
        if ((tid & (2*s - 1)) == 0) {
            sdata[tid] += sdata[tid + s];
        }
        __syncthreads();
    }
    if (tid == 0) {
        atomicAdd(g_odata, sdata[0]);
    }
}

// reduce2: sequential addressing
// Problem: idle threads

__global__ void reduce2(int *g_idata, int *g_odata) {
	extern __shared__ int sdata[];
	// each thread loads one element from global to shared mem
	unsigned int tid = threadIdx.x;
	unsigned int i = blockIdx.x*blockDim.x + threadIdx.x;
	sdata[tid] = g_idata[i];
	__syncthreads();
	// do reduction in shared mem
	for(unsigned int s=blockDim.x/2; s > 0; s >>= 1) {
		if (tid < s) {
			sdata[tid] += sdata[tid + s];
		}
		__syncthreads();
	}
	// write result for this block to global mem
	if (tid == 0) atomicAdd(g_odata, sdata[0]);
}

// reduce3: first add during global load
// blockDim.x减半

__global__ void reduce3(int *g_idata, int *g_odata) {
	extern __shared__ int sdata[];
	// perform first level of reduction,
	// reading from global memory, writing to shared memory
	unsigned int tid = threadIdx.x;
	unsigned int i = blockIdx.x*(blockDim.x*2) + threadIdx.x;
	sdata[tid] = g_idata[i] + g_idata[i+blockDim.x];
	__syncthreads();
	// do reduction in shared mem
	for(unsigned int s=blockDim.x/2; s > 0; s >>= 1) {
		if (tid < s) {
			sdata[tid] += sdata[tid + s];
		}
		__syncthreads();
	}
	// write result for this block to global mem
	if (tid == 0) atomicAdd(g_odata, sdata[0]);
}

// Instruction Bottleneck
// At 17 GB/s, we’re far from bandwidth bound
// And we know reduction has low arithmetic intensity

// Therefore a likely bottleneck is instruction overhead
// Ancillary instructions that are not loads, stores, or
// arithmetic for the core computation
// In other words: address arithmetic and loop overhead

// Strategy: unroll loops

// reduce4: unroll last warp

__device__ void warpReduce(volatile int* sdata, int tid) {
	sdata[tid] += sdata[tid + 32];
	sdata[tid] += sdata[tid + 16];
	sdata[tid] += sdata[tid + 8];
	sdata[tid] += sdata[tid + 4];
	sdata[tid] += sdata[tid + 2];
	sdata[tid] += sdata[tid + 1];
}

__global__ void reduce4(int *g_idata, int *g_odata) {
	extern __shared__ int sdata[];
	// perform first level of reduction,
	// reading from global memory, writing to shared memory
	unsigned int tid = threadIdx.x;
	unsigned int i = blockIdx.x*(blockDim.x*2) + threadIdx.x;
	sdata[tid] = g_idata[i] + g_idata[i+blockDim.x];
	__syncthreads();
	// do reduction in shared mem
	for(unsigned int s=blockDim.x/2; s > 32; s >>= 1) {
		if (tid < s) {
			sdata[tid] += sdata[tid + s];
		}
		__syncthreads();
	}
	if (tid < 32) warpReduce(sdata, tid);
	// write result for this block to global mem
	if (tid == 0) atomicAdd(g_odata, sdata[0]);
}

// reduce5: Completely unrolled with Templates
// 编译器确定if/else

template <unsigned int blockSize>
__device__ void warpReduce(volatile int* sdata, unsigned int tid) {
	if (blockSize >= 64) sdata[tid] += sdata[tid + 32];
	if (blockSize >= 32) sdata[tid] += sdata[tid + 16];
	if (blockSize >= 16) sdata[tid] += sdata[tid + 8];
	if (blockSize >= 8) sdata[tid] += sdata[tid + 4];
	if (blockSize >= 4) sdata[tid] += sdata[tid + 2];
	if (blockSize >= 2) sdata[tid] += sdata[tid + 1];
}

template <unsigned int blockSize>
__global__ void reduce5(int *g_idata, int *g_odata) {
	extern __shared__ int sdata[];
	// perform first level of reduction,
	// reading from global memory, writing to shared memory
	unsigned int tid = threadIdx.x;
	unsigned int i = blockIdx.x*(blockDim.x*2) + threadIdx.x;
	sdata[tid] = g_idata[i] + g_idata[i+blockDim.x];
	__syncthreads();
	if (blockSize >= 512) {
		if (tid < 256) {
			sdata[tid] += sdata[tid + 256];
		}
		__syncthreads();
	}
	if (blockSize >= 256) {
		if (tid < 128) {
			sdata[tid] += sdata[tid + 128];
		}
		__syncthreads();
	}
	if (blockSize >= 128) {
		if (tid < 64) {
			sdata[tid] += sdata[tid + 64];
		}
		__syncthreads();
	}
	if (tid < 32) warpReduce<blockSize>(sdata, tid);
	// write result for this block to global mem
	if (tid == 0) atomicAdd(g_odata, sdata[0]);
}


// O(N)
// O(N/P + log N)

// Cost of a parallel algorithm is processors × time complexity
// Allocate threads instead of processors: O(N) threads
// Time complexity is O(log N), so cost is O(N log N) : not cost efficient!

// Brent’s theorem suggests O(N/log N) threads
// Cost = O((N/log N) * log N) = O(N) : cost efficient!

// Sometimes called algorithm cascading
// Can lead to significant speedups in practice
// each thread should sum O(log n) elements

// In my experience, beneficial to push it even further
// Possibly better latency hiding with more work per thread
// More threads per block reduces levels in tree of recursive kernel invocations
// High kernel launch overhead in last levels with few blocks

// On G80, best perf with 64-256 blocks of 128 threads
// 1024-4096 elements per thread

// reduce 6: Multiple Adds Per Thread

template <unsigned int blockSize>
__global__ void reduce6(int *g_idata, int *g_odata, unsigned int n, unsigned int COARSE_FACTOR) {
	extern __shared__ int sdata[];
	unsigned int tid = threadIdx.x;
    sdata[tid] = 0;
    unsigned int i = blockIdx.x * blockSize * COARSE_FACTOR + tid;
    for (unsigned int tile = 0; tile < COARSE_FACTOR; ++tile) {
        unsigned int index = i + tile * blockDim.x;
        if (index < n) {
            sdata[tid] += g_idata[index];
        }
    }

	__syncthreads();
	if (blockSize >= 1024) { if (tid < 512) { sdata[tid] += sdata[tid + 512]; } __syncthreads(); }
	if (blockSize >= 512) { if (tid < 256) { sdata[tid] += sdata[tid + 256]; } __syncthreads(); }
	if (blockSize >= 256) { if (tid < 128) { sdata[tid] += sdata[tid + 128]; } __syncthreads(); }
	if (blockSize >= 128) { if (tid < 64) { sdata[tid] += sdata[tid + 64]; } __syncthreads(); }
	if (tid < 32) warpReduce(sdata, tid);
	if (tid == 0) atomicAdd(g_odata, sdata[0]);
}


void ReduceSum(torch::Tensor input, torch::Tensor output, int version, unsigned int BLOCK_SIZE, unsigned int COARSE_FACTOR) {
    CHECK_INPUT(input);
    CHECK_INPUT(output);

    const auto size = input.numel();
    int threads_per_block = (size >= BLOCK_SIZE) ? BLOCK_SIZE : size;
    int blocks = cdiv(size, threads_per_block);
    int smem_size = threads_per_block * sizeof(int);
    if (version == 0) {
        reduce0<<<blocks, threads_per_block, smem_size>>>(
            input.data_ptr<int>(),
            output.data_ptr<int>()
        );
    } else if (version == 1) {
        reduce1<<<blocks, threads_per_block, smem_size>>>(
            input.data_ptr<int>(),
            output.data_ptr<int>()
        );
    } else if (version == 2) {
        reduce2<<<blocks, threads_per_block, smem_size>>>(
            input.data_ptr<int>(),
            output.data_ptr<int>()
        );
    } else if (version == 3) {
        threads_per_block /= 2;
        reduce3<<<blocks, threads_per_block, smem_size>>>(
            input.data_ptr<int>(),
            output.data_ptr<int>()
        );
    } else if (version == 4) {
        threads_per_block /= 2;
        reduce4<<<blocks, threads_per_block, smem_size>>>(
            input.data_ptr<int>(),
            output.data_ptr<int>()
        );
    } else if (version == 5) {
        threads_per_block /= 2;
        auto d_idata = input.data_ptr<int>();
        auto d_odata = output.data_ptr<int>();
        switch (threads_per_block) {
            case 512:
                reduce5<512><<< blocks, threads_per_block, smem_size >>>(d_idata, d_odata); break;
            case 256:
                reduce5<256><<< blocks, threads_per_block, smem_size >>>(d_idata, d_odata); break;
            case 128:
                reduce5<128><<< blocks, threads_per_block, smem_size >>>(d_idata, d_odata); break;
            case 64:
                reduce5< 64><<< blocks, threads_per_block, smem_size >>>(d_idata, d_odata); break;
            case 32:
                reduce5< 32><<< blocks, threads_per_block, smem_size >>>(d_idata, d_odata); break;
            case 16:
                reduce5< 16><<< blocks, threads_per_block, smem_size >>>(d_idata, d_odata); break;
            case 8:
                reduce5< 8><<< blocks, threads_per_block, smem_size >>>(d_idata, d_odata); break;
            case 4:
                reduce5< 4><<< blocks, threads_per_block, smem_size >>>(d_idata, d_odata); break;
            case 2:
                reduce5< 2><<< blocks, threads_per_block, smem_size >>>(d_idata, d_odata); break;
            case 1:
                reduce5< 1><<< blocks, threads_per_block, smem_size >>>(d_idata, d_odata); break;
        }
    }
    else if (version == 6) {
        blocks = (size + threads_per_block * COARSE_FACTOR - 1) / (threads_per_block * COARSE_FACTOR);
        auto d_idata = input.data_ptr<int>();
        auto d_odata = output.data_ptr<int>();
        switch (threads_per_block) {
            case 1024:
                reduce6<1024><<< blocks, threads_per_block, smem_size >>>(d_idata, d_odata, size, COARSE_FACTOR); break;
            case 512:
                reduce6<512><<< blocks, threads_per_block, smem_size >>>(d_idata, d_odata, size, COARSE_FACTOR); break;
            case 256:
                reduce6<256><<< blocks, threads_per_block, smem_size >>>(d_idata, d_odata, size, COARSE_FACTOR); break;
            case 128:
                reduce6<128><<< blocks, threads_per_block, smem_size >>>(d_idata, d_odata, size, COARSE_FACTOR); break;
            case 64:
                reduce6< 64><<< blocks, threads_per_block, smem_size >>>(d_idata, d_odata, size, COARSE_FACTOR); break;
            case 32:
                reduce6< 32><<< blocks, threads_per_block, smem_size >>>(d_idata, d_odata, size, COARSE_FACTOR); break;
            case 16:
                reduce6< 16><<< blocks, threads_per_block, smem_size >>>(d_idata, d_odata, size, COARSE_FACTOR); break;
            case 8:
                reduce6< 8><<< blocks, threads_per_block, smem_size >>>(d_idata, d_odata, size, COARSE_FACTOR); break;
            case 4:
                reduce6< 4><<< blocks, threads_per_block, smem_size >>>(d_idata, d_odata, size, COARSE_FACTOR); break;
            case 2:
                reduce6< 2><<< blocks, threads_per_block, smem_size >>>(d_idata, d_odata, size, COARSE_FACTOR); break;
            case 1:
                reduce6< 1><<< blocks, threads_per_block, smem_size >>>(d_idata, d_odata, size, COARSE_FACTOR); break;
        }
    }
    C10_CUDA_KERNEL_LAUNCH_CHECK();
}


'''

cpp_src = r'''
void ReduceSum(torch::Tensor input, torch::Tensor output, int version, unsigned int BLOCK_SIZE = 1024, unsigned int COARSE_FACTOR = 1);
'''

reduce_module = load_cuda(
  cuda_src,
  cpp_src,
  ['ReduceSum'],
  opt=True,
  verbose=True,
  name='reduce',
)


def cuda_reduce_sum(A, version, BLOCK_SIZE=1024, COARSE_FACTOR=1):
  output = torch.zeros(1,
                       dtype=A.dtype,
                       device='cuda')
  assert A.numel() % 2 == 0, A.numel()
  if version == 4:
    assert A.numel() >= 128, A.numel()
  assert isinstance(COARSE_FACTOR, int), type(COARSE_FACTOR)
  reduce_module.ReduceSum(A, output, version, BLOCK_SIZE, COARSE_FACTOR)
  return output


def test_reduce():
  torch.manual_seed(0)
  test_sizes = [2**i for i in range(7, 18, 1)]
  for total_size in test_sizes:
    x = torch.randint(0, 100, (total_size,), dtype=torch.int32, device='cuda')

    expected_output = x.sum().unsqueeze(0)
    assert expected_output.dtype == torch.int64, expected_output.dtype  # sum of ints is int

    output0 = cuda_reduce_sum(x, 0)
    assert output0.dtype == torch.int32, f"ReduceSum0 output dtype mismatch: expected torch.int32, got {output0.dtype}"
    assert output0.shape == expected_output.shape, f"ReduceSum0 output shape mismatch: expected {expected_output.shape}, got {output0.shape}"
    assert torch.equal(
      output0.long(), expected_output
    ), f"ReduceSum0 failed.\nOutput:\n{output0}\nExpected:\n{expected_output}"
    print("ReduceSum0 test passed.")

    output1 = cuda_reduce_sum(x, 1)
    assert output1.dtype == torch.int32, f"ReduceSum1 output dtype mismatch: expected torch.int32, got {output1.dtype}"
    assert output1.shape == expected_output.shape, f"ReduceSum1 output shape mismatch: expected {expected_output.shape}, got {output1.shape}"
    assert torch.equal(
      output1.long(), expected_output
    ), f"ReduceSum1 failed.\nOutput:\n{output1}\nExpected:\n{expected_output}"
    print("ReduceSum1 test passed.")

    output2 = cuda_reduce_sum(x, 2)
    assert output2.dtype == torch.int32, f"ReduceSum2 output dtype mismatch: expected torch.int32, got {output2.dtype}"
    assert output2.shape == expected_output.shape, f"ReduceSum2 output shape mismatch: expected {expected_output.shape}, got {output2.shape}"
    assert torch.equal(
      output2.long(), expected_output
    ), f"ReduceSum2 failed.\nOutput:\n{output2}\nExpected:\n{expected_output}"
    print("ReduceSum2 test passed.")

    output3 = cuda_reduce_sum(x, 3)
    assert output3.dtype == torch.int32, f"ReduceSum3 output dtype mismatch: expected torch.int32, got {output3.dtype}"
    assert output3.shape == expected_output.shape, f"ReduceSum3 output shape mismatch: expected {expected_output.shape}, got {output3.shape}"
    assert torch.equal(
      output3.long(), expected_output
    ), f"ReduceSum3 failed.\nOutput:\n{output3}\nExpected:\n{expected_output}"
    print("ReduceSum3 test passed.")

    output4 = cuda_reduce_sum(x, 4)
    assert output4.dtype == torch.int32, f"ReduceSum4 output dtype mismatch: expected torch.int32, got {output4.dtype}"
    assert output4.shape == expected_output.shape, f"ReduceSum4 output shape mismatch: expected {expected_output.shape}, got {output4.shape}"
    assert torch.equal(
      output4.long(), expected_output
    ), f"ReduceSum4 failed.\nOutput:\n{output4}\nExpected:\n{expected_output}"
    print("ReduceSum4 test passed.")

    output5 = cuda_reduce_sum(x, 5)
    assert output5.dtype == torch.int32, f"ReduceSum5 output dtype mismatch: expected torch.int32, got {output5.dtype}"
    assert output5.shape == expected_output.shape, f"ReduceSum5 output shape mismatch: expected {expected_output.shape}, got {output5.shape}"
    assert torch.equal(
      output5.long(), expected_output
    ), f"ReduceSum5 failed.\nOutput:\n{output5}\nExpected:\n{expected_output}"
    print("ReduceSum5 test passed.")

    output6 = cuda_reduce_sum(x, 6, BLOCK_SIZE=128, COARSE_FACTOR=8)
    assert output6.dtype == torch.int32, f"ReduceSum6 output dtype mismatch: expected torch.int32, got {output6.dtype}"
    assert output6.shape == expected_output.shape, f"ReduceSum6 output shape mismatch: expected {expected_output.shape}, got {output6.shape}"
    assert torch.equal(
        output6.long(), expected_output
    ), f"ReduceSum6 failed.\nOutput:\n{output6}\nExpected:\n{expected_output}"
    print("ReduceSum6 test passed.")

    print(f"All reduce tests passed successfully! total_size: {total_size}")


@triton.testing.perf_report(
  triton.testing.Benchmark(
    x_names=['size'],
    x_vals=[2**i for i in range(7, 21, 1)],
    line_arg='operation',
    line_vals=[
      'torch', 'torch_compile', 'cuda0', 'cuda1', 'cuda2', 'cuda3', 'cuda4', 'cuda5', 'cuda6'
    ],
    line_names=[
      'torch.sum', 'torch.compile(sum)', 'ReduceSum0', 'ReduceSum1', 'ReduceSum2',
      'ReduceSum3', 'ReduceSum4', 'ReduceSum5', 'ReduceSum6(BLOCK_SIZE=128,COARSE_FACTOR=8)'
    ],
    styles=[('blue', '-'), ('blue', '--'), ('green', '-'), ('red', '-'), ('purple', '-'),
            ('orange', '-'), ('cyan', '-'), ('magenta', '-'), ('yellow', '-')],
    ylabel='us',
    plot_name='reduce-performance(gbps)',
    args={},
  ))
def benchmark(size, operation):
  x = torch.randint(0, 100, (size,), device='cuda', dtype=torch.int32)
  if operation == 'torch':
    fn = lambda: torch.sum(x)
  elif operation == 'torch_compile':
    compiled_sum = torch.compile(torch.sum, dynamic=False)
    fn = lambda: compiled_sum(x)
  elif operation == 'cuda0':
    fn = lambda: cuda_reduce_sum(x, 0)
  elif operation == 'cuda1':
    fn = lambda: cuda_reduce_sum(x, 1)
  elif operation == 'cuda2':
    fn = lambda: cuda_reduce_sum(x, 2)
  elif operation == 'cuda3':
    fn = lambda: cuda_reduce_sum(x, 3)
  elif operation == 'cuda4':
    fn = lambda: cuda_reduce_sum(x, 4)
  elif operation == 'cuda5':
    fn = lambda: cuda_reduce_sum(x, 5)
  elif operation == 'cuda6':
    fn = lambda: cuda_reduce_sum(x, 6, BLOCK_SIZE=128, COARSE_FACTOR=8)
  else:
    raise ValueError(f"Invalid operation: {operation}")
  ms, min_ms, max_ms = triton.testing.do_bench(fn, quantiles=[0.5, 0.2, 0.8])
  gbps = lambda ms: (x.numel() * x.element_size()) / ms * 1e-6
  return gbps(ms), gbps(max_ms), gbps(min_ms)
  # return ms * 1e3, max_ms * 1e3, min_ms * 1e3


# TORCH_LOGS="output_code"
@torch.compile
def f(a):
  c = torch.sum(a)
  return c

if __name__ == '__main__':
  f(torch.randn(100000).cuda())
  test_reduce()
  benchmark.run(print_data=True, save_path='.')
