https://nvidia.github.io/cccl/cpp.html

https://discord.com/invite/nvidiadeveloper
#cuda

*** thrust

e.g. scatter+tuple+load_cs

auto map = thrust::make_transform_iterator(
  thrust::make_counting_iterator(0), [=] __host__ __device__(int idx) {
		auto [b, n, nh_, d_] = i2n(idx, NH, T, HS);
		return (b * NH * T * HS) + (n * NH * HS) + (nh_ * HS) + d_;
	});
cub::CacheModifiedInputIterator<cub::LOAD_CS, float> vaccumcs(vaccum);
thrust::scatter(thrust::device, vaccumcs, vaccumcs + B * T * C, map, out);



** 类似C++ container

* Detects the issue at compile time
thrust::device_vector<cuda::std::complex<float>> complex_vec(10);
thrust::device_vector<int> int_vec = complex_vec;

// Compiles successfully (but shouldn't)
cuda::std::complex<float>* d_complex{};
int* d_int{};
cudaMemcpy(d_int, d_complex, sizeof(cuda::std::complex<float>), cudaMemcpyDeviceToDevice);


* type conversion

// type punning
float *d_float{};
cudaMalloc(&d_float, sizeof(float));

int val = 42;
cudaMemcpy(d_float, &val, sizeof(float), cudaMemcpyHostToDevice); // d_float[0] = 5.88545e-44

// vs conversion
thrust::device_vector<float> d_vec(1, 42); 
// d_vec[0]  = 42.0f

* customizable

template <class T>
using pinned_vector = thrust::host_vector<
    T, thrust::mr::stateless_resource_allocator<
           T, thrust::system::cuda::universal_host_pinned_memory_resource>>;


* 异步、同步、stream

传入 thrust::cuda::par_nosync、thrust::cuda::device、thrust::cuda::par.on(stream)

* atomic
增加thread_scope的参数
- https://nvidia.github.io/cccl/libcudacxx/extended_api/synchronization_primitives/atomic_ref.html

cuda::atomic_ref<float, cuda::thread_scope_device> dwte_ix_ref(*dwte_ix);
cuda::atomic_ref<float, cuda::thread_scope_device> dwte_tc_ref(*dwpe_tc);
dwte_ix_ref.fetch_add(*dout_btc, cuda::memory_order_relaxed);
dwte_tc_ref.fetch_add(*dout_btc, cuda::memory_order_relaxed);



** algorithm

* memcpy

float dloss_mean = 1.0f / (B*T);
thrust::fill_n(thrust::device, grad_acts.losses, B*T, dloss_mean)

如果用cudaMemset，很坑，会对每个byte赋值，因此赋成了0

* transform

并且支持
#define THRUST_DEVICE_SYSTEM THRUST_DEVICE_SYSTEM_OMP，切换transform内部实现

void gelu_forward(float* out, const float* inp, int N) {
    thrust::transform(thrust::cuda::par_nosync, inp, inp + N, out, [] __device__(float xi) {
        float cube = 0.044715f * xi * xi * xi;
        return 0.5f * xi * (1.0f + tanhf(GELU_SCALING_FACTOR * (xi + cube)));
    });
}


** iterator

	auto c = thrust::make_counting_iterator(10);
	std::cout << c[0]   << std::endl; // 10
	std::cout << c[1]   << std::endl; // 11
	std::cout << c[100] << std::endl; // 110
	auto c3 = c + 3;
	std::cout << c3[0] << std::endl; // 13

	auto t = thrust::make_transform_iterator(
					c, [] __host__ __device__(int i) { 
                  return i * 2; 
                });

	std::cout << t[0] << std::endl;   // 20
	std::cout << t[1] << std::endl;   // 22
	std::cout << t[100] << std::endl; // 220
	auto t3 = t + 3;
	std::cout << t3[0] << std::endl;  // 26

* 关于lambda function：不能直接传入定义好的function，原因是地址在CPU上，但可以定义struct，overload struct的call operator

struct AddConstantFunctor {
    int constant_to_add;

    __host__ __device__
    AddConstantFunctor(int c) : constant_to_add(c) {}

    __host__ __device__
    int operator()(int x) const {
        return x + constant_to_add;
    }
};


*** libcu++

cuda::std::variant
cuda::std::tuple
cuda::std::pair

__device__ cuda::std::pair<int, int> i2n(int idx, int E1) {
    return {idx / E1, idx % E1};
}

__device__ cuda::std::tuple<int, int, int> i2n(int idx, int E1, int E2) {
    int bt = idx / E1;
    int b = bt / E2;
    int t = bt % E2;
    int c = idx % E1;
    return {b, t, c};
}

__host__ __device__ cuda::std::tuple<int, int, int, int> i2n(int idx, int E1, int E2, int E3) {
    int b = idx / (E1 * E2 * E3);
    int rest = idx % (E1 * E2 * E3);
    int nh_ = rest / (E2 * E3);
    rest = rest % (E2 * E3);
    int t = rest / E3;
    int hs = rest % E3;
    return {b, t, nh_, hs};
}

auto [b, n, nh_, d_] = i2n(idx, NH, T, HS);


*** cub

* scope

Scope is a set of threads that may interact directly with given operation and establish relations described in the memory consistency model
cuda::thread_scope_block is a set of threads of a given thread block
cuda::thread_scope_device is a set of threads of a given device
cuda::thread_scope_system is a set of threads of a given system


* cub::CacheModifiedInputIterator<cub::LOAD_CS, float>
- 不止对builtin type能用

__global__ void residual_forward_kernel(float* out,
                                        const float* inp1, const float* inp2, int N) {
    int idx = blockIdx.x * blockDim.x + threadIdx.x;
    if (idx < N) {
        out[idx] = __ldcs(&inp1[idx]) + __ldcs(&inp2[idx]);
    }
}

-->

void residual_forward_alternative(float* out, const float* inp1, const float* inp2, int N) {
    cub::CacheModifiedInputIterator<cub::LOAD_CS, float> inp1cs(inp1);
    cub::CacheModifiedInputIterator<cub::LOAD_CS, float> inp2cs(inp2);
    thrust::transform(thrust::device,
                      inp1cs, inp1cs + N, inp2cs, out, thrust::plus<float>());
}

* Block load/scan

constexpr int threads = 512;
constexpr int items = 1;
constexpr int tile_size = threads * items;

using load_t = cub::BlockLoad<std::uint32_t, threads, items>;
using store_t = cub::BlockStore<std::uint32_t, threads, items>;
using scan_t = cub::BlockScan<std::uint32_t, threads>;

std::uint32_t thread_data[items];
load_t{storage_load}.Load(X + bid * tile_size, thread_data);
scan_t{storage_scan}.InclusiveSum(thread_data, thread_data);

SingleWordStream(previous_sum, thread_data);
for (int i = 0; i < items; i++) {
    thread_data[i] += previous_sum;
}
store_t{storage_store}.Store(Y + bid * tile_size, thread_data);


*** nvbench

NVBENCH_BENCH(kernel2).add_int64_axis("block_size", {32, 64, 128, 256, 512, 1024});