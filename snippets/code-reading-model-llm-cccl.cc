python train_gpt2.py --tensorcores=1 --num_iterations=100 --sequence_length=1024 // 107ms
./train_gpt2cu // 82ms


pip install -r requirements.txt
python prepro_tinyshakespeare.py
python train_gpt2.py
make train_gpt2cu
./train_gpt2cu

*** cmake构建

*** train_gpt2.py

- 模型结构见「code-reading-model-nanogpt.py」

# init the tokenizer
enc = tiktoken.get_encoding("gpt2")
encode = lambda s: enc.encode(s, allowed_special={"<|endoftext|>"})
decode = lambda l: enc.decode(l)

write_tokenizer(enc, "gpt2_tokenizer.bin")
 -> b = enc.decode_bytes([i])



*** thrust运用

- 15 kernels变成3个，大部分可以用algorithm实现
- algorithm有tune的能力，会调优block size，但仅对generic algorithm有效，比如transform、scatter、reduction、scan、sorting
- 有支持用户传入block size的计划

template <class T>
using pinned_vector = thrust::host_vector<
    T, thrust::mr::stateless_resource_allocator<
           T, thrust::system::cuda::universal_host_pinned_memory_resource>>;

void kernel2(nvbench::state &state)
{
  int B = 8;
  int T = 1024;
  int C = 768;

  thrust::host_vector<float> h_inp(B * T * C);
  thrust::host_vector<float> h_weight(C);
  thrust::host_vector<float> h_bias(C);

  thrust::default_random_engine gen(42);
  thrust::uniform_real_distribution<float> dis(-1.0f, 1.0f);
  thrust::generate(h_inp.begin(), h_inp.end(), [&] { return dis(gen); });
  thrust::generate(h_weight.begin(), h_weight.end(), [&] { return dis(gen); });
  thrust::generate(h_bias.begin(), h_bias.end(), [&] { return dis(gen); });

  thrust::device_vector<float> d_out(B * T * C);
  thrust::device_vector<float> d_mean(B * T);
  thrust::device_vector<float> d_rstd(B * T);
  thrust::device_vector<float> d_inp(h_inp);
  thrust::device_vector<float> d_weight(h_weight);
  thrust::device_vector<float> d_bias(h_bias);

  const int N = B * T;
  const int block_size = state.get_int64("block_size");

  state.add_global_memory_reads<float>(d_inp.size() + d_weight.size() + d_bias.size());
  state.add_global_memory_writes<float>(d_out.size() + d_mean.size() + d_rstd.size());

  const int normalization_block_size = 256;
  const int normalization_grid_size =
      (B * T * C + normalization_block_size - 1) / normalization_block_size;

  state.exec([&](nvbench::launch &launch) {
    cudaStream_t stream = launch.get_stream();
    mean_kernel<<<B * T, block_size, block_size * sizeof(float)>>>(
      thrust::raw_pointer_cast(d_mean.data()), 
      thrust::raw_pointer_cast(d_inp.data()), 
      N, C, block_size);
    rstd_kernel<<<B * T, block_size, block_size * sizeof(float)>>>(
      thrust::raw_pointer_cast(d_rstd.data()), 
      thrust::raw_pointer_cast(d_inp.data()), 
      thrust::raw_pointer_cast(d_mean.data()), 
      N, C, block_size);
    normalization_kernel<<<normalization_grid_size, normalization_block_size>>>(
      thrust::raw_pointer_cast(d_out.data()), 
      thrust::raw_pointer_cast(d_inp.data()), 
      thrust::raw_pointer_cast(d_mean.data()), 
      thrust::raw_pointer_cast(d_rstd.data()), 
      thrust::raw_pointer_cast(d_weight.data()), 
      thrust::raw_pointer_cast(d_bias.data()), 
      B, T, C);
  });
}


void gelu_forward(float* out, const float* inp, int N) {
    thrust::transform(thrust::cuda::par_nosync, inp, inp + N, out, [] __device__(float xi) {
        float cube = 0.044715f * xi * xi * xi;
        return 0.5f * xi * (1.0f + tanhf(GELU_SCALING_FACTOR * (xi + cube)));
    });
}


** 利用MDSpan做多维permute
MDSpan: light-weight、non-owning

void attention_forward() {
	...
	float *q, *k, *v;
    q = qkvr + 0 * B * T * C;
    k = qkvr + 1 * B * T * C;
    v = qkvr + 2 * B * T * C;

    constexpr auto dyn = cuda::std::dynamic_extent;
    using ext_t = cuda::std::extents<int, dyn, dyn, 3, dyn, dyn>;
    using mds_t = cuda::std::mdspan<const float, ext_t, cuda::std::layout_right, streaming_accessor<const float>>;

    ext_t extents{B, T, NH, HS};
    mds_t inp_md{inp, extents};

    // Q[b][nh_][n][d_] = inp[b][n][0][nh_][d_]
    thrust::for_each(thrust::cuda::par_nosync, thrust::make_counting_iterator(0),
                     thrust::make_counting_iterator(B * NH * T * HS),
                     [=] __device__(int idx) {
                        auto [b, t, nh_, hs] = i2n(idx, NH, T, HS);
                        q[idx] = inp_md(b, t, 0, nh_, hs);
                        k[idx] = inp_md(b, t, 1, nh_, hs);
                        v[idx] = inp_md(b, t, 2, nh_, hs);
                     });
    ...
}


template <class T> struct streaming_accessor {
    using offset_policy = streaming_accessor;
    using element_type = T;
    using data_handle_type = const T *;
    using reference = const T;

    inline __host__ __device__ 
    reference access(data_handle_type p, size_t i) const {
        NV_IF_TARGET(NV_IS_DEVICE, (return __ldcs(p + i);), (return p[i];));
    }

    inline __host__ __device__ 
    data_handle_type offset(data_handle_type p, size_t i) const {
        return p + i;
    }
};


void encoder_forward(float* out,
                     const thrust::device_vector<int>& inpv, float* wte, float* wpe,
                     int B, int T, int C, int V) {
    cuda::std::mdspan<float, cuda::std::dextents<int, 3>> out_md(out, B, T, C);
    cuda::std::mdspan<float, cuda::std::dextents<int, 2>> wte_md(wte, V, C);
    cuda::std::mdspan<float, cuda::std::dextents<int, 2>> wpe_md(wpe, T, C);
    cuda::std::mdspan<const int, cuda::std::dextents<int, 2>> inp_md(thrust::raw_pointer_cast(inpv.data()), B, T);

    cudaCheck(cub::DeviceFor::Bulk(B * T * C, [=] __device__(int idx) {
      auto [b, t, c] = i2n(idx, C, T);
      out_md(b, t, c) = wte_md(inp_md(b, t), c) + wpe_md(t, c);
    }));
}

** kernel fusion

fused_classifier_kernel3
- 用cooperative_groups实现
- 将loss reduce和前面操作fuse起来


target_matrix targets_md(thrust::raw_pointer_cast(model.targets.data()), B, T);

auto map = thrust::make_transform_iterator(
    thrust::make_counting_iterator(0),
    [=] __device__(int i) -> int {
        int b = i / T;
        int t = i % T;
        return targets_md(b, t) + b * T * V + t * V;
    });

auto permutation = thrust::make_permutation_iterator(acts.probs, map);
auto losses = thrust::make_transform_iterator(
    permutation, [ ] __device__(float prob) -> float { return -logf(prob); });

model.mean_loss = thrust::reduce(thrust::device, losses, losses + B * T, 0.0) / (B * T);


*** layer_norm

layernorm_forward_kernel3
- 用cooperative_groups实现

-->

绕开cg,block_size不再受限于warp.size()

sum = cub::BlockReduce<float, block_size>().Sum(sum);
__shared__ float shared_mean;
if(tid == 0 && mean != nullptr) {
	float m = sum / C;
	shared_mean = m;
	__stcs(mean + idx, m);
}
__syncthreads();
const float m = shared_mean;


*** nvbench

NVBENCH_BENCH(kernel2).add_int64_axis("block_size", {32, 64, 128, 256, 512, 1024});