### Intro 

浅谈大模型训练排障平台的建设
https://cloud.tencent.com/developer/article/2359942


TORCH_SHOW_CPP_STACKTRACES=1
TORCH_DISTRIBUTED_DEBUG=DETAIL
TORCH_CPP_LOG_LEVEL=INFO
NCCL_DEBUG=INFO
PYTHONFAULTHANDLER=1
CUDA_LAUNCH_BLOCKING=1

### set seed

def set_seed(seed: int = 37) -> None:
    np.random.seed(seed)
    random.seed(seed)
    torch.manual_seed(seed)  # 适用于所有PyTorch后端，包括CPU和所有CUDA设备
    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = False

    os.environ["PYTHONHASHSEED"] = str(seed)
    print(f"设置随机数种子为{seed}")


### tensor

def set_pretty_tensor_print():
  def custom_repr(self):
    return f'{{Tensor{tuple(self.shape)}(dtype={self.dtype}): {original_repr(self)}}}'
  original_repr = torch.Tensor.__repr__
  torch.Tensor.__repr__ = custom_repr


import numpy as np
np.set_printoptions(precision=2, linewidth=140)
torch.set_printoptions(precision=2, linewidth=140, sci_mode=False)
torch.set_printoptions(profile='full')

### params

print(f"params sum is: {sum(model.parameters()).sum()}")

### grad

retain_grad

from torch.autograd import gradcheck
# gradcheck takes a tuple of tensors as input, check if your gradient
# evaluated with these tensors are close enough to numerical
# approximations and returns True if they all verify this condition.
input = (torch.randn(20,20,dtype=torch.double,requires_grad=True), torch.randn(30,20,dtype=torch.double,requires_grad=True))
test = gradcheck(linear, input, eps=1e-6, atol=1e-4)
print(test)


### op

TORCH_SHOW_CPP_STACKTRACES=1


### DDPModel

* NCCL_DEBUG=INFO
* 断点打在上面会卡住，打到后面

torch.distributed.breakpoint(rank)


* TORCH_DISTRIBUTED_DEBUG = OFF (default), INFO, or DETAIL

非常有用！

For fine-grained control of the debug level during runtime the functions torch.distributed.set_debug_level(),
torch.distributed.set_debug_level_from_env(), and torch.distributed.get_debug_level() can also be used.


# debug速度
https://pytorch.org/docs/stable/ddp_comm_hooks.html

from torch.distributed.algorithms.ddp_comm_hooks.debugging_hooks import noop_hook
model.register_comm_hook(None, noop_hook)


import torch
import torch.distributed as dist
import torch.multiprocessing as mp


def worker(rank):
    dist.init_process_group("nccl", rank=rank, world_size=2)
    torch.cuda.set_device(rank)
    tensor = torch.randn(10 if rank == 0 else 20).cuda()
    dist.all_reduce(tensor)
    torch.cuda.synchronize(device=rank)


if __name__ == "__main__":
    os.environ["MASTER_ADDR"] = "localhost"
    os.environ["MASTER_PORT"] = "29501"
    os.environ["TORCH_CPP_LOG_LEVEL"]="INFO"
    os.environ["TORCH_DISTRIBUTED_DEBUG"] = "DETAIL"
    mp.spawn(worker, nprocs=2, args=())


### debug rank hang: dist.monitored_barrier

import os
from datetime import timedelta

import torch
import torch.distributed as dist
import torch.multiprocessing as mp


def worker(rank):
    dist.init_process_group("nccl", rank=rank, world_size=2)
    # monitored barrier requires gloo process group to perform host-side sync.
    group_gloo = dist.new_group(backend="gloo")
    if rank not in [1]:
        dist.monitored_barrier(group=group_gloo, timeout=timedelta(seconds=2))


if __name__ == "__main__":
    os.environ["MASTER_ADDR"] = "localhost"
    os.environ["MASTER_PORT"] = "29501"
    mp.spawn(worker, nprocs=2, args=())