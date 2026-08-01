*** PyTorch的initCUDAStreamsOnce函数

调用到了cuda runtime API的cudaDeviceGetStreamPriorityRange函数

此时cuda primary context还没被创建，于是cuDevicePrimaryCtxRetain函数就被调用了

由于cuda runtime API都不带device参数，所以具体使用的device都得依靠current device。在cuda runtime API中，通过cudaSetDevice可以设置当前使用的device。

*** PyTorch cuda device management

在PyTorch中，当我们使用torch.ones(5).cuda()时，实际上它包括两步：

tmp = torch.ones(5)创建一个tensor。创建tensor的函数叫做factory function。创建出来的tensor放在哪里，有一个default device的概念（默认是CPU）。
tmp.cuda()移动一个tensor，由于没有指定具体的cuda设备号，它将使用cuda current device（默认是cuda 0）
当我们通过torch.ones(5, device="cuda:1")创建tensor时，PyTorch知道我们要把数据放在1号GPU上，这要分为三步：

* 首先通过cudaGetDevice获取当前的current device，保存这一信息
* 切换到device 1，创建cuda tensor
* 切换回之前的current device

从PyTorch用户的角度来看，我们似乎可以直接指定数据存储在哪个GPU上，这是因为PyTorch为用户做了current device的管理。

因此，PyTorch的device management可以总结为下面三类：

* with target_device的用法，影响tensor factory function（没有指定在CPU还是在GPU的情况）
* .cuda()或者.to()的用法，影响tensor movement，使用cuda runtime里的current device（指定在GPU，但是没有指定具体设备的情况）
* .cuda(i)或者.to(f"cuda:{i}")的用法，影响tensor movement，临时切换cuda runtime里的current device，并在最后还原之前的current device（指定在具体某个GPU的情况）


import torch

# by default, factory functions place tensors in cpu
data = torch.ones(5)
assert data.device == torch.device("cpu")

with torch.device("cuda:1"):
    # inside `with torch.device` , factory functions place tensors in that device
    data = torch.ones(5)
    assert data.device == torch.device("cuda:1")

# when device is explicitly specified, pytorch temporarily switch the current device, launch the operation to create tensor, and then switch it back
assert torch.cuda.current_device() == 0
data = torch.ones(5, device="cuda:1")
assert data.device == torch.device("cuda:1")
assert torch.cuda.current_device() == 0

--> 为什么不建议在一个进程里使用多个GPU：这将会带来频繁的cuda context切换，由此可能产生性能上的损失。



** nccl也强依赖current device

import torch
import torch.distributed as dist
dist.init_process_group(backend='nccl')

rank = dist.get_rank()
data = torch.ones((1024, 1024, 1024), device=f"cuda:{rank}")
dist.all_reduce(data)

# shift the process-device mapping
rank = (dist.get_rank() + 3) % dist.get_world_size()
data = torch.ones((1024, 1024, 1024), device=f"cuda:{rank}")
dist.all_reduce(data)

打开环境变量export NCCL_DEBUG=TRACE，会发现其实这两次allreduce，用的是不一样的NCCL

PyTorch会记录进程与GPU的对应关系，每当我们进行allreduce的时候，它会检查当前的进程与GPU的对应关系是否发生了改变，如果发生了改变，则需要重新初始化NCCL。


** Cannot re-initialize CUDA in forked subprocess.

https://zhuanlan.zhihu.com/p/1916193728541982811

一个进程初始化了cuda driver（也就是调用了cuInit(0)之后），就不能再进行fork了，或者说fork的进程里面就不能再使用cuda相关的API了。

PyTorch通过pthread_atfork系统调用，注册了一个回调函数，让子进程知道父进程是否初始化了cuda driver，从而抛出对应的异常。


*** 如何确保每个进程占用一个GPU？

GPU编程的常见情况，就是一个进程占用一个GPU。那么，如何占住GPU呢？初始化了对应GPU上面的cuda context，就算是占住了这块GPU了。

这里要介绍的一个坑点，就在于torch.cuda.set_device()函数，torch.cuda.set_device(0)占不住GPU，而torch.cuda.set_device(1)可以：
- https://github.com/pytorch/pytorch/issues/155668


import torch
import ctypes
import argparse

# Set up argument parser
parser = argparse.ArgumentParser(description='Set CUDA device and check context')
parser.add_argument('device', type=int, help='CUDA device number to use')
args = parser.parse_args()

# Set the device based on command line argument
torch.cuda.set_device(args.device)

# Load the CUDA driver library
cuda = ctypes.CDLL("libcuda.so")  # Linux
# cuda = ctypes.CDLL("nvcuda.dll")  # Windows

# Define CUcontext as a pointer type
CUcontext = ctypes.c_void_p

# Define return and argument types for cuCtxGetCurrent
cuda.cuCtxGetCurrent.restype = ctypes.c_int  # CUresult
cuda.cuCtxGetCurrent.argtypes = [ctypes.POINTER(CUcontext)]

# Create a CUcontext variable
ctx = CUcontext()

# Call cuCtxGetCurrent
result = cuda.cuCtxGetCurrent(ctypes.byref(ctx))

# Check the result
if result != 0:
    print(f"cuCtxGetCurrent failed with error code {result}")
elif not ctx:
    print(f"No active CUDA context. res: {ctx}")
else:
    print("Active CUDA context detected.")


其根本原因，在于PyTorch的torch.cuda.set_device并不直接对应cuda runtime的cudaSetDevice函数，
而是首先调用cudaGetDevice函数做判断，而这个函数在cuda context没有初始化的时候也会返回0，从而导致torch.cuda.set_device(0)并没有发挥作用。

保险起见的做法，是用data = torch.zeros(1, device=f"cuda:{args.device}")代替torch.cuda.set_device。


*** example

import ctypes
import pynvml

from contextlib import contextmanager
import pynvml

@contextmanager
def _nvml():
    try:
        pynvml.nvmlInit()
        yield
    finally:
        pynvml.nvmlShutdown()

@_nvml()
def report_used_memory(index=0, msg=""):
    # Get the handle for the same device using NVML
    handle = pynvml.nvmlDeviceGetHandleByIndex(index)
    # Get memory information
    info = pynvml.nvmlDeviceGetMemoryInfo(handle)
    print(f"{msg}: Used memory: {info.used / 1024 ** 2} MB")

# Load the CUDA driver library
cuda = ctypes.CDLL('libcuda.so')

report_used_memory(msg="before cuinit")

# Initialize the CUDA Driver API
result = cuda.cuInit(0)
if result != 0:
    raise Exception("Failed to initialize the CUDA driver API")

report_used_memory(msg="after cuinit")

device = 0
# Create contexts on device 0
contexts = []
for i in range(3):
    context = ctypes.c_void_p()
    result = cuda.cuCtxCreate(ctypes.byref(context), 0, device)
    if result != 0:
        raise Exception("Failed to create one or both CUDA contexts")
    report_used_memory(msg=f"after creating {i + 1} cuda context")
    contexts.append(context)