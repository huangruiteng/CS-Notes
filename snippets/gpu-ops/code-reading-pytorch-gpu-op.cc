### Aten

*** native_functions.yaml

构造函数的多种构建方式

- func: sparse_coo_tensor.size(int[] size, *, ScalarType? dtype=None, Layout? layout=None, Device? device=None, bool? pin_memory=False) -> Tensor
  dispatch:
    CompositeExplicitAutograd: sparse_coo_tensor
  autogen: sparse_coo_tensor.size_out
- func: sparse_coo_tensor.indices(Tensor indices, Tensor values, *, ScalarType? dtype=None, Layout? layout=None, Device? device=None, bool? pin_memory=None, bool? is_coalesced=None) -> Tensor
- func: sparse_coo_tensor.indices_size(Tensor indices, Tensor values, int[] size, *, ScalarType? dtype=None, Layout? layout=None, Device? device=None, bool? pin_memory=None, bool? is_coalesced=None) -> Tensor


*** reduce_ops

- Implementation is accumulator and reduction op agnostic
- TensorIterator to iterate over tensor elements
- ReduceConfig: Has kernel launch parameters like block size and number of threads, grid etc.. and its set in setReduceConfig
- Reduce_kernel is where it gets launched
- Reduction strategies: thread level, block level x,y, or global reduce
- Vectorization: Over input and/or output


* min的实现：
aten/src/ATen/native/cuda/ReduceOps.cpp
->
aten/src/ATen/native/cuda/ReduceMinValuesKernel.cu
->
aten/src/ATen/native/cuda/Reduce.cuh: 

struct ReduceOp

auto config = ReduceConfig(sizeof(arg_t), num_outputs, inputs_per_output);

template<int max_threads, typename R>
static void launch_reduce_kernel(const ReduceConfig& config, const R& reduction) {
  dim3 block = config.block();
  dim3 grid = config.grid();

  auto stream = at::cuda::getCurrentCUDAStream();
  int shared_memory = config.shared_memory_size();

  switch(config.output_vec_size) {
  case 4:
    reduce_kernel<max_threads / 4, 4, R><<<grid, block, shared_memory, stream>>>(reduction);
    C10_CUDA_KERNEL_LAUNCH_CHECK();
    break;
  case 2:
    reduce_kernel<max_threads / 2, 2, R><<<grid, block, shared_memory, stream>>>(reduction);
    C10_CUDA_KERNEL_LAUNCH_CHECK();
    break;
  default:
    reduce_kernel<max_threads / 1, 1, R><<<grid, block, shared_memory, stream>>>(reduction);
    C10_CUDA_KERNEL_LAUNCH_CHECK();
  }
}

gpu_reduce_kernel
  - can_accumulate_in_output
  // at::Half/at::ComplexHalf overflows easily as it's range is very small.
  // So when scalar_t and out_scalar_t are at::Half/at::ComplexHalf, we
  // set can_accumulate_in_output to False.
  static constexpr bool is_inp_out_type_half_or_chalf =
      (std::is_same_v<at::Half, scalar_t> &&
       std::is_same_v<at::Half, out_scalar_t>) ||
      (std::is_same_v<c10::complex<Half>, scalar_t> &&
       std::is_same_v<c10::complex<Half>, out_scalar_t>);
  // at::BFloat16 has lower precision and can lead to rounding errors.
  // So when scalar_t and out_scalar_t are at::BFloat16, we
  // set can_accumulate_in_output to False.
  static constexpr bool is_inp_out_type_bfloat16 =
      (std::is_same_v<at::BFloat16, scalar_t> &&
       std::is_same_v<at::BFloat16, out_scalar_t>);
  static constexpr bool can_accumulate_in_output =
      std::is_convertible_v<arg_t, out_scalar_t> &&
      !(is_inp_out_type_half_or_chalf || is_inp_out_type_bfloat16);



*** _foreach_add_

* aten/src/ATen/native/native_functions.yaml

- func: _foreach_add.Scalar(Tensor[] self, Scalar scalar) -> Tensor[]
  device_check: NoCheck   # foreach kernels fall back to slow path when tensor are on different devices
  variants: function
  dispatch:
    CompositeExplicitAutograd: foreach_tensor_add_scalar_kernel_slow
    CUDA: foreach_tensor_add_scalar_kernel_cuda

- func: _foreach_add_.Scalar(Tensor(a!)[] self, Scalar scalar) -> () # a!表示原地修改
  device_check: NoCheck   # foreach kernels fall back to slow path when tensor are on different devices
  variants: function
  dispatch:
    CompositeExplicitAutograd: foreach_tensor_add_scalar_kernel_slow_
    CUDA: foreach_tensor_add_scalar_kernel_cuda_
  autogen: _foreach_add.Scalar_out

* aten/src/ATen/native/ForeachOpsKernels.cpp

#define FOREACH_BINARY_OP_LIST(FUNCTION, NAME, OP, DIVISION_OP)     \
  void foreach_tensor_##NAME##_list_kernel_cuda_(                   \
      TensorList tensors1, TensorList tensors2) {                   \
    check_foreach_api_restrictions(tensors1, tensors2);             \
    if (!can_use_fast_route(tensors1, tensors2, DIVISION_OP)) {     \
      return at::native::foreach_tensor_##NAME##_list_kernel_slow_( \
          tensors1, tensors2);                                      \
    }                                                               \
                                                                    \
    FUNCTION##_<OP>(tensors1, tensors2);                            \
  }   

FOREACH_BINARY_OP_LIST_ALPHA(
    all_types_complex_bool_half_bfloat16,
    add,
    std::plus,
    false);
在宏展开之后， FUNCTION##_<OP> 会被替换成 all_types_complex_bool_half_bfloat16_<std::plus>


* 判断条件：can_use_fast_route(tensors1, tensors2, DIVISION_OP=false)
--> aten/src/ATen/native/ForeachUtils.h

To go via 'fast' path, several conditions must be satisfied
- All tensors in all lists must have the same dtype.
- All tensors must be on the same device
- All tensors must have strided layout
- All tensors must be non-overlapping and dense
- Resulting tensor must have the same dtype as the input one

* fast版本

先分发
template <template <class> class Op>
void all_types_complex_bool_half_bfloat16_(
    TensorList tensors1,
    TensorList tensors2,
    const Scalar& alpha = 1) {
  AT_DISPATCH_ALL_TYPES_AND_COMPLEX_AND3(
      kBool,
      kBFloat16,
      kHalf,
      tensors1[0].scalar_type(),
      "foreach_binary_op_list_cuda_",
      [&]() {
        foreach_tensor_list_op_<scalar_t, Op>(tensors1, tensors2, alpha);
      });
}

template <typename T, template <class> class Op>
void foreach_tensor_list_op_(
    TensorList tensors1,
    TensorList tensors2,
    const Scalar& alpha = 1) {
  std::vector<std::vector<at::Tensor>> tensor_lists;
  tensor_lists.emplace_back(tensors1.vec());
  tensor_lists.emplace_back(tensors2.vec());

  using opmath_t = at::opmath_type<T>;
  multi_tensor_apply<2>(
      tensor_lists,
      BinaryOpListAlphaFunctor<
          T,
          /* depth */ 2,
          /* r_args_depth */ 2,
          /* res_arg_index */ 0>(),
      Op<opmath_t>(),
      alpha.to<opmath_t>());
  increment_version(tensors1);
}

// multi_tensor_apply enables horizontal fusion across lists of tensors.
// For example, whereas you once had a for-loop of a + b = c, where a, b,
// and c are individual tensors in lists as, bs, and cs, you can now with
// fewer kernel launches compute as + bs = cs.
//
// You can also imagine bs to be a scalar list vs a tensor list.
//
// The function below takes in tensor lists, scalars, and a callable and
// chunks up the computation to launch as few kernels as possible by iterating
// through every "chunk" in every tensor (thus the nested for loops). In the
// simplest case, everything gets bundled into just one kernel launch, but
// due to blocksize constraints, we may need to launch multiple kernels.
// Each kernel launch is defined by one tensorListMeta construct, which we
// use to track and reset the necessary metadata for each launch.
template <int depth, typename scalar_T, typename T, typename... ArgTypes>
void multi_tensor_apply(

  static constexpr int64_t kChunkSize = 65536;
static constexpr int64_t kBlockSize = 512;

* slow版本
aten/src/ATen/native/ForeachOpsKernels.cpp： for循环




*** fused实现

aten/src/ATen/native/cuda/fused_adamw_impl.cu

void _fused_adamw_cuda_impl_ ... {
  std::vector<std::vector<at::Tensor>> tensor_lists{
      params.vec(), grads.vec(), exp_avgs.vec(), exp_avg_sqs.vec()};

  const float* grad_scale_ptr =
      grad_scale.has_value() ? grad_scale->data_ptr<float>() : nullptr;
  const float* found_inf_ptr =
      found_inf.has_value() ? found_inf->data_ptr<float>() : nullptr;
  const float* lr_ptr = nullptr;

  AT_DISPATCH_FLOATING_TYPES_AND2(
      kHalf,
      kBFloat16,
      params[0].scalar_type(),
      "fused_adamw_kernel_cuda",
      [&]() {
        multi_tensor_apply_for_fused_optimizer<4>(
            tensor_lists,
            state_steps,
            FusedAdamMathFunctor<scalar_t, 4, ADAM_MODE::ADAMW, false>(),
            lr_ptr, // unused
            lr,
            beta1,
            beta2,
            weight_decay,
            eps,
            maximize,
            grad_scale_ptr,
            found_inf_ptr);
      });
}

* aten/src/ATen/native/cuda/fused_adam_utils.cuh

struct FusedAdamMathFunctor


*** foreach kernel中的内存对齐优化

* aten/src/ATen/native/cuda/MultiTensorApply.cuh

template <typename T>
__device__ __forceinline__ bool is_aligned(T* p) {
  return ((uint64_t)p) % (kILP * sizeof(T)) == 0;
}

template <typename T>
__device__ __forceinline__ void load_store(
    T* dst,
    T* src,
    int64_t dst_offset,
    int64_t src_offset) {
  using LT = at::native::memory::aligned_vector<T, kILP>;
  ((LT*)dst)[dst_offset] = ((LT*)src)[src_offset];
}

如果不对齐，则 load_args

template <int depth, typename T>
__device__ void load_args(
    T r_args[][kILP],
    T** args,
    const int64_t i_start,
    const int64_t chunk_size,
    const int64_t n) {
#pragma unroll
  for (int ii = 0; ii < kILP; ii++) {
    const auto i = i_start + threadIdx.x + ii * blockDim.x;
    for (int r_index = 0; r_index < depth; r_index++) {
      r_args[r_index][ii] = 0;
      if (i < n && i < chunk_size) {
        r_args[r_index][ii] = args[r_index][i];
      }
    }
  }
}


*** vectorized_elementwise_kernel

void at::native::vectorized_elementwise_kernel<4, at::native::(anonymous namespace)::pow_tensor_scalar_kernel_impl<float, float>(at::TensorIteratorBase&, float)::{lambda(float)#1},

-->

template <int vec_size, typename func_t, typename array_t>
C10_LAUNCH_BOUNDS_1(num_threads())
__global__ void vectorized_elementwise_kernel(int N, func_t f, array_t data) {
  using traits = function_traits<func_t>;
  int remaining = N - block_work_size() * blockIdx.x;

  if (remaining < block_work_size()) { // if this block handles the reminder,
                                       // just do a naive unrolled loop
    auto input_calc = TrivialOffsetCalculator<traits::arity>();
    auto output_calc = TrivialOffsetCalculator<1>();
    auto loader = memory::LoadWithoutCast();
    auto storer = memory::StoreWithoutCast();
    auto policy = memory::policies::unroll<
        array_t,
        decltype(input_calc),
        decltype(output_calc),
        memory::LoadWithoutCast,
        memory::StoreWithoutCast>(
        data, remaining, input_calc, output_calc, loader, storer);
    elementwise_kernel_helper(f, policy);
  } else { // if this block has a full `block_work_size` data to handle, use
           // vectorized memory access
    elementwise_kernel_helper(
        f, memory::policies::vectorized<vec_size, array_t>(data));
  }
}


template<typename func_t, typename policy_t>
__device__ inline void elementwise_kernel_helper(func_t f, policy_t policy) {
  using traits = function_traits<func_t>;
  using return_t = typename traits::result_type;
  using args_t = typename traits::ArgsTuple;

  int idx = blockIdx.x;

  return_t results[thread_work_size()];
  args_t args[thread_work_size()];

  // load
  policy.load(args, idx);

  // compute
  #pragma unroll
  for (int i = 0; i < thread_work_size(); i++) {
    if (policy.check_inbounds(i)) {
      results[i] = c10::guts::apply(f, args[i]);
    }
  }

  // store
  policy.store(results, idx);
}