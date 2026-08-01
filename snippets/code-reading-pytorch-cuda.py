*** cuda device management

由于cuda runtime API都不带device参数，所以具体使用的device都得依靠current device。在cuda runtime API中，通过cudaSetDevice可以设置当前使用的device。

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

** 
