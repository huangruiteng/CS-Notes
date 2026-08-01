### 关于驱动

dpkg -l | grep nvidia
cat /proc/driver/nvidia/version

根据nvidia-smi的驱动版本

https://docs.nvidia.com/cuda/cuda-toolkit-release-notes/index.html

* CUDA版本

% nvcc -V

cat /usr/local/cuda/version.txt

# note
nvcc是准确的。  nvidia-smi是最大支持版本
一个CUDA Driver版本可以支持多个CUDA版本

* cuDNN版本

cat /usr/local/cuda/include/cudnn.h | grep CUDNN_MAJOR -A 2

*** 关于容器

https://hub.docker.com/r/nvidia/cuda

training_image="nvcr.nju.edu.cn/nvidia/cuda:12.6.3-cudnn-devel-ubuntu22.04"


### basic

>>> a = torch.cuda.get_device_properties(0)
>>> a.
a.L2_cache_size                    a.max_threads_per_multi_processor  a.total_memory
a.gcnArchName                      a.minor                            a.uuid
a.is_integrated                    a.multi_processor_count            a.warp_size
a.is_multi_gpu_board               a.name
a.major                            a.regs_per_multiprocessor

CUDA_VISIBLE_DEVICES='0,1,2'

import torch

if torch.cuda.is_available():
    device_count = torch.cuda.device_count()
    print("CUDA设备数量:", device_count)

    for i in range(device_count):
        print("CUDA设备{}型号:".format(i), torch.cuda.get_device_name(i))
else:
    print("CUDA不可用")

print(torch.cuda.current_device())

### nvcc

nvcc -o output xx.cu

常见flags:
-O3 -Xptxas -O3 -Xcompiler -O3 -Xptxas -v --ptxas-options=-v
-out


### utils

import GPUtil
GPUtil.showUtilization()


### nvlink

cudaMemcpyPeerAsync
cudaDeviceEnablePeerAccess

NVIDIA的CUDA驱动在检测到NVLink存在时，会自动启用GPU直接内存访问（PeerMemory）和一致性功能。
例如，在CUDA C++中调用。cudaMemcpyPeerAsync 在有NVLink时会利用其高带宽传输数据。在多GPU范畴的高级框架（如NCCL通信库）中，
也会自动根据拓扑使用NVLink路径来实现最佳通信性能 。开发者也可以使用CUDA的cudaDeviceEnablePeerAccess接口手动开启两GPU间直接访问权限，
一旦启用，之后两GPU间的cudaMemcpy就会走NVLink而非绕经主机内存。在MPI等并行库中，NVIDIA提供的GPUDirect RDMA和NCCL等也会结合NVLink/NVSwitch做拓扑优化，
通常开发者不需要特别为NVLink编写代码，只需确保驱动和库版本支持即可。



