import imp
import os
from IPython.core.debugger import set_trace
import matplotlib.pyplot as plt
from torch.utils.cpp_extension import load_inline

# os.environ['TRITON_INTERPRET'] = '1' # needs to be set *before* triton is imported

import torch
import triton
import triton.language as tl

tl_print = print if os.environ.get("TRITON_INTERPRET", 0) else tl.device_print

def set_pretty_tensor_print():
  def custom_repr(self):
    return f'{{Tensor{tuple(self.shape)}(dtype={self.dtype}): {original_repr(self)}}}'
  original_repr = torch.Tensor.__repr__
  torch.Tensor.__repr__ = custom_repr

def is_cuda():
  return triton.runtime.driver.active.get_current_target().backend == "cuda"


def is_hip_cdna2():
  target = triton.runtime.driver.active.get_current_target()
  return target.backend == 'hip' and target.arch == 'gfx90a'


# Bigger tolerance for AMD CDNA2 devices.
# CDNA2 devices use reduced precision fp16 and bf16 and flush input and output denormal values to zero.
# Detailed info is at: https://pytorch.org/docs/stable/notes/numerical_accuracy.html#reduced-precision-fp16-and-bf16-gemms-and-convolutions-on-amd-instinct-mi200-devices
RTOL = 1e-2 if is_hip_cdna2() else 0
properties = triton.runtime.driver.active.utils.get_device_properties(torch.device('cuda:0').index)
NUM_SM = properties["multiprocessor_count"]


def show_img(x, figsize=(4, 3), **kwargs):
  "Display HW or CHW format image `x`"
  plt.figure(figsize=figsize)
  plt.axis('off')
  if len(x.shape) == 3:
    x = x.permute(1, 2, 0)  # CHW -> HWC
  plt.imshow(x.cpu(), **kwargs)


cuda_begin = r'''
#include <torch/extension.h>
#include <stdio.h>
#include <c10/cuda/CUDAException.h>

// #include "nccl.h"

#define CHECK_CUDA(x) TORCH_CHECK(x.device().is_cuda(), #x " must be a CUDA tensor")
#define CHECK_CONTIGUOUS(x) TORCH_CHECK(x.is_contiguous(), #x " must be contiguous")
#define CHECK_INPUT(x) CHECK_CUDA(x); CHECK_CONTIGUOUS(x)
#define CUDA_ERR(ans) { gpuAssert((ans), __FILE__, __LINE__); }
inline void gpuAssert(cudaError_t code, const char *file, int line, bool abort=true)
{
   if (code != cudaSuccess) 
   {
      fprintf(stderr,"GPUassert: %s %s %d\n", cudaGetErrorString(code), file, line);
      if (abort) exit(code);
   }
}

#define NCCLCHECK(cmd) do {                         \
  ncclResult_t res = cmd;                           \
  if (res != ncclSuccess) {                         \
    printf("Failed, NCCL error %s:%d '%s'\n",       \
        __FILE__,__LINE__,ncclGetErrorString(res)); \
    exit(EXIT_FAILURE);                             \
  }                                                 \
} while(0)

__host__ __device__ inline unsigned int cdiv(unsigned int a, unsigned int b) { return (a + b - 1) / b;}
'''


def load_cuda(cuda_source,
              cpp_source,
              funcs,
              opt=False,
              verbose=False,
              name=None):
  if name is None:
    name = funcs[0]
  opt_flags = "-O3 -Xptxas -O3 -Xcompiler -O3" if opt else "-O0 -Xptxas -O0 -Xcompiler -O0"
  return load_inline(
      name=name,
      cuda_sources=[cuda_source],
      cpp_sources=[cpp_source],
      functions=funcs,
      extra_cuda_cflags=[opt_flags] +
      ['--ptxas-options=-v'],  # '--expt-relaxed-constexpr'
      verbose=verbose,
      # extra_cuda_cflags=['--expt-relaxed-constexpr']
      build_directory='./load_inline_cuda')


def check_tensors_gpu_ready(*tensors):
  for t in tensors:
    assert t.is_contiguous, "A tensor is not contiguous"
    if not os.environ.get('TRITON_INTERPRET') == '1':
      assert t.is_cuda, "A tensor is not on cuda"


def test_pid_conds(conds, pid_0=[0], pid_1=[0], pid_2=[0]):
  '''Test if condition on pids are fulfilled
    E.g.:
        '=0'  checks that pid_0 == 0
        ',>1' checks that pid_1 > 1
        '>1,=0' checks that pid_0 > 1 and pid_1 == 0
    '''
  pids = pid_0[0], pid_1[0], pid_2[0]
  conds = conds.replace(' ', '').split(',')
  for i, (cond, pid) in enumerate(zip(conds, pids)):
    if cond == '':
      continue
    op, threshold = cond[0], int(cond[1:])
    if op not in ['<', '>', '>=', '<=', '=', '!=']:
      raise ValueError(
          f"Rules may only use these ops: '<','>','>=','<=','=', '!='. Invalid rule: '{condition}'."
      )
    op = '==' if op == '=' else op
    if not eval(f'{pid} {op} {threshold}'):
      return False
  return True


assert test_pid_conds('')
assert test_pid_conds('>0', [1], [1])
assert not test_pid_conds('>0', [0], [1])
assert test_pid_conds('=0,=1', [0], [1], [0])


def breakpoint_if(conds, pid_0=[0], pid_1=[0], pid_2=[0]):
  '''Stop kernel, if any condition of pids is fulfilled'''
  if test_pid_conds(conds, pid_0, pid_1, pid_2):
    set_trace()


def print_if(txt, conds, pid_0=[0], pid_1=[0], pid_2=[0]):
  '''Print txt, if any condition of pids is fulfilled'''
  if test_pid_conds(conds, pid_0, pid_1, pid_2):
    print(txt)


def cdiv(a, b):
  return (a + b - 1) // b


assert cdiv(10, 2) == 5
assert cdiv(10, 3) == 4


@triton.jit
def get_1d_offset(size, n_prev_chunks):
  return n_prev_chunks * size + tl.arange(0, size)


@triton.jit
def get_2d_offset(offs_0, offs_1, stride_0, stride_1=1):
  return tl.expand_dims(offs_0, 1) * stride_0 + tl.expand_dims(offs_1,
                                                               0) * stride_1


@triton.jit
def get_1d_mask(offs, max):
  return offs < max


@triton.jit
def get_2d_mask(offs_0, offs_1, max_0, max_1):
  return (tl.expand_dims(offs_0, 1) < max_0) & (tl.expand_dims(offs_1, 0)
                                                < max_1)


def check_implementation(
    impl_func_a,
    impl_func_b,
    name_a,
    name_b,
    common_args,  # 两个函数共用的位置参数 (例如 [a, b])
    kwargs_a=None,
    kwargs_b=None,
    dtypes=[torch.float32,
            torch.float16,
            torch.float8_e5m2],
    comparison_func=torch.allclose,
    **comparison_kwargs  # 传递给比较函数的额外参数 (例如 atol, rtol)
):
  """
  Runs two implementations with given arguments for specified dtypes,
  compares their results, and prints the outcome for each dtype.
  Returns the results (tensor_a, tensor_b) of the first failed comparison,
  or the results of the last comparison if all succeed.
  """
  if kwargs_a is None:
    kwargs_a = {}
  if kwargs_b is None:
    kwargs_b = {}
  if dtypes is None:
    first_tensor_dtype = next(
        (arg.dtype for arg in common_args if isinstance(arg, torch.Tensor)),
        torch.float32)
    dtypes = [first_tensor_dtype]

  last_tensor_a, last_tensor_b = None, None

  for dtype in dtypes:
    print(f"--- Testing with dtype: {dtype} ---")
    casted_common_args_a = []
    casted_common_args_b = []
    for arg in common_args:
      if not isinstance(arg, torch.Tensor):
        casted_common_args_a.append(arg)
        casted_common_args_b.append(arg)
      elif dtype == torch.float8_e5m2:
        if impl_func_a == torch.matmul:
          # "addmm_cuda" not implemented for 'Float8_e5m2'
          casted_common_args_a.append(arg)
        else:
          casted_common_args_a.append(arg.to(device=arg.device, dtype=dtype))
        if impl_func_b == torch.matmul:
          casted_common_args_b.append(arg)
        else:
          casted_common_args_b.append(arg.to(device=arg.device, dtype=dtype))
      else:
        casted_common_args_a.append(arg.to(device=arg.device, dtype=dtype))
        casted_common_args_b.append(arg.to(device=arg.device, dtype=dtype))

    try:
      tensor_a = impl_func_a(*casted_common_args_a, **kwargs_a)
    except Exception as e:
      print(f"⚠️ {name_a} Error during testing with {dtype}: {e}")
      continue
    try:
      tensor_b = impl_func_b(*casted_common_args_b, **kwargs_b)
    except Exception as e:
      print(f"⚠️ {name_b} Error during testing with {dtype}: {e}")
      continue
    compare_dtype = torch.float16 if dtype == torch.float8_e5m2 else dtype
    try:
        tensor_a_comp = tensor_a.to(device=arg.device, dtype=compare_dtype)
        tensor_b_comp = tensor_b.to(device=arg.device, dtype=compare_dtype)
    except Exception as e:
        print(f"⚠️ Error casting results to {compare_dtype} for comparison: {e}")
        continue

    default_comp_kwargs = {'atol': 5e-2, 'rtol': RTOL}
    # 特别处理低精度类型，可能需要更大的容忍度
    if dtype == torch.float16 or dtype == torch.bfloat16:
      default_comp_kwargs['atol'] = 1e-2
    if dtype == torch.float8_e5m2:
      default_comp_kwargs['atol'] = 0.125
      default_comp_kwargs['rtol'] = 0

    kwargs_to_use = {**default_comp_kwargs, **comparison_kwargs}
    match = comparison_func(tensor_a_comp, tensor_b_comp, **kwargs_to_use)
    if match:
      print(f"✅ {name_a} and {name_b} match for {dtype}")
      last_tensor_a, last_tensor_b = tensor_a, tensor_b
    else:
      print(f"❌ {name_a} and {name_b} differ for {dtype}")
      print(f"   Max diff: {torch.max(torch.abs(tensor_a_comp - tensor_b_comp))}, tensor_a: {tensor_a_comp}, tensor_b: {tensor_b_comp}")
  return last_tensor_a, last_tensor_b
