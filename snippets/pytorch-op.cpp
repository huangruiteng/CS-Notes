*** 写kernel

Tensor my_op_out_cpu(Tensor& result, const Tensor& self, const Tensor& other) {
    // 错误检查
    TORCH_CHECK(result.is_cpu() && self.is_cpu() && other.is_cpu());
    TORCH_CHECK(self.dim() == 1);
    TORCH_CHECK(self.sizes() == other.sizes()); 

    // 输出分配
    result.resize_(self.sizes()); 

    // 数据类型调度
    AT_DISPATCH_FORALL_TYPES(
        self.scalar_type(), "my_op_cpu", [&] {
            my_op_cpu_kernel<scalar_t>(result, self, other);
        }
    );
}

template <typename scalar_t>
void my_op_cpu_kernel(Tensor& result, const Tensor& self, const Tensor& other) {
    auto result_accessor = result.accessor<scalar_t, 1>();
    auto self_accessor = self.accessor<scalar_t, 1>();
    auto other_accessor = other.accessor<scalar_t, 1>();

    // 并行化
    parallel_for(0, self.size(0), 0, [&](int64_t start, int64_t end) {
       ... self_accessor[i]...
    });
    // 数据访问（向量化？！）
}

One important thing to be aware about when writing operators in PyTorch, is that you are often signing up to write three operators: 
- abs_out, which operates on a preallocated output (this implements the out= keyword argument),
- abs_, which operates inplace
- abs, which is the plain old functional version of an operator.

Tensor& abs_out(Tensor& result, const Tensor& self) {
    result.resize_(self.sizes());
    //... 实际实现部分...
}

Tensor abs(const Tensor& self) {
    Tensor result = at::empty({0}, self.options());
    abs_out(result, self);
    return result;
}

Tensor& abs_(Tensor& self) {
    return abs_out(self, self);
}

*** dispatch
 - 并非涵盖实际所有类型

AT_DISPATCH_ALL_TYPES(
    self.scalar_type(), "my_op_cpu", [&] {
        my_op_cpu_kernel<scalar_t>(result, self, other);
    }
);
 - 针对每种标量类型特化 lambda 表达式

AT_DISPATCH_ALL_TYPES(TYPE, NAME,...)
AT_DISPATCH_FLOATING_TYPES(TYPE, NAME,...)
AT_DISPATCH_INTEGRAL_TYPES(TYPE, NAME,...)
AT_DISPATCH_ALL_TYPES_AND(SCALARTYPE, TYPE, NAME,...)

### error checking

#include <c10/util/Exception.h>
// 手写错误信息
TORCH_CHECK(self.dim() == 1, "Expected self to be 1-D tensor, but "
                           "was ", self.dim(), "-D tensor"); // 本质上使用 << 实现

#include <ATen/TensorUtils.h>
// 关于每个参数的元数据
TensorArg result_arg{result, "result", 0},
          self_arg{self, "self", 1},
          other_arg{other, "other", 2};
CheckedFrom c = "my_op_cpu";
checkDim(c, self_arg, 1);
checkContiguous(c, result)

### data accessor

#### 逐点访问
```cpp
auto x_accessor = x.accessor<float, 3>();
float val = x_accessor[0][0][0];
```
CUDA：`packed_accessor`（注意：32 位！）

#### 逐元素访问
```cpp
#include <ATen/native/TensorIterator.h>
auto iter = TensorIterator::Builder()
   .add_output(output)
   .add_input(input)
   .build();
binary_kernel(iter, [](float a, float b) {
    return a + b;
});
```
CUDA：`gpu_binary_kernel`

#### 向量化访问
```cpp
#include <ATen/native/cpu/Loops.h>
binary_kernel_vec(iter,
    [](scalar_t a, scalar_t b) -> scalar_t {
        return a + alpha * b; 
    },
    [](Vec256<scalar_t> a, Vec256<scalar_t> b) {
        return vec256::fmadd(b, alpha_vec, a);
    });
``` 


### 写GPU Op

#include <torch/extension.h>
#include <stdio.h>
#include <c10/cuda/CUDAException.h>

#define CHECK_CUDA(x) TORCH_CHECK(x.device().is_cuda(), #x " must be a CUDA tensor")
#define CHECK_CONTIGUOUS(x) TORCH_CHECK(x.is_contiguous(), #x " must be contiguous")
#define CHECK_INPUT(x) CHECK_CUDA(x); CHECK_CONTIGUOUS(x)

inline unsigned int cdiv(unsigned int a, unsigned int b) { return (a + b - 1) / b;}

__global__ void rgb_to_grayscale_kernel(unsigned char* x, unsigned char* out, int n) {
    int i = blockIdx.x*blockDim.x + threadIdx.x;
    if (i<n) out[i] = 0.2989*x[i] + 0.5870*x[i+n] + 0.1140*x[i+2*n];
}

torch::Tensor rgb_to_grayscale(torch::Tensor input) {
    CHECK_INPUT(input);
    int h = input.size(1);
    int w = input.size(2);
    printf("h*w: %d*%d\n", h, w);
    auto output = torch::empty({h,w}, input.options());
    int threads = 256;
    rgb_to_grayscale_kernel<<<cdiv(w*h,threads), threads>>>(
        input.data_ptr<unsigned char>(), output.data_ptr<unsigned char>(), w*h);      // 类型转换
    C10_CUDA_KERNEL_LAUNCH_CHECK(); // 检查kernel错误
    return output;
}



TORCH_LIBRARY(my_op_cpu, m) {
  m.class_<monotorch::FeatureMapCPU>("MyOpCPU")
    .def(torch::init<int64_t, double_t, int64_t, int64_t>())
    .def("reinit", &MyWorkspace::MyOpCPU::reinit)
}

### packed accessor

#include <ATen/ATen.h>
#include <ATen/cuda/CUDAContext.h>
#include <ATen/cuda/detail/TensorInfo.cuh>

template <typename scalar_t>
__global__ void my_add_kernel(
    PackedTensorAccessor64<scalar_t, 2> input1,
    PackedTensorAccessor64<scalar_t, 2> input2,
    PackedTensorAccessor64<scalar_t, 2> output) {
  
  // 获取当前线程处理的元素位置
  const int x = blockIdx.x * blockDim.x + threadIdx.x;
  const int y = blockIdx.y * blockDim.y + threadIdx.y;

  // 检查边界
  if (x < input1.size(0) && y < input1.size(1)) {
    // 执行逐元素加法
    output[x][y] = input1[x][y] + input2[x][y];
  }
}

Tensor my_add_cuda(const Tensor& input1, const Tensor& input2) {
  // 检查输入合法性
  TORCH_CHECK(input1.sizes() == input2.sizes(), "Input sizes must match");
  
  // 准备输出张量
  auto output = at::empty_like(input1);
  
  // 获取CUDA网格和块大小
  const dim3 blocks(32, 32);
  const dim3 grids(
    (input1.size(0) + blocks.x - 1) / blocks.x,
    (input1.size(1) + blocks.y - 1) / blocks.y
  );

  // 启动核函数
  AT_DISPATCH_FLOATING_TYPES(input1.scalar_type(), "my_add_cuda", [&] {
    my_add_kernel<scalar_t><<<grids, blocks, 0, at::cuda::getCurrentCUDAStream()>>>(
      input1.packed_accessor64<scalar_t, 2>(),
      input2.packed_accessor64<scalar_t, 2>(),
      output.packed_accessor64<scalar_t, 2>()
    );
  });
  
  return output;
}

### cpu op

at::parallel_for(0, input_size, grain_size, [&](int64_t begin, int64_t end) {
    for (auto i = begin; i < end; i++) {
        //...
    }
});