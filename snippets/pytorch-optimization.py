*** Intro

Pytorch的框架开销：As long as you have Tensors with a few 100s of elements, “Python is slow” and data administrative
overhead (allocate tensor structure) is single digit percentages

*** dataset

num_workers、prefetch_factor

优化数据预处理：pillow-simd

减少不必要的CPU线程：numpy偷偷创建cpu核数的线程

*** cuda

https://docs.pytorch.org/docs/stable/notes/cuda.html#tensorfloat-32-tf32-on-ampere-and-later-devices
https://github.com/Lightning-AI/pytorch-lightning/issues/18665

# The flag below controls whether to allow TF32 on matmul. This flag defaults to False
# in PyTorch 1.12 and later.
torch.backends.cuda.matmul.allow_tf32 = True
torch.backends.cudnn.allow_tf32 = True # The flag below controls whether to allow TF32 on cuDNN. This flag defaults to True.


*** nvfuser

https://pytorch.org/blog/introducing-nvfuser-a-deep-learning-compiler-for-pytorch/

*** Thunder

https://lightning.ai/docs/thunder/latest/
https://github.com/Lightning-AI/lightning-thunder
https://www.nvidia.com/en-us/on-demand/session/gtc24-s62544/


*** tunable op

https://docs.pytorch.org/docs/stable/cuda.tunable.html


*** activation ckpt

import torch
import torch.nn as nn
from torch.utils.checkpoint import checkpoint_sequential

model = nn.Sequential(
    nn.Linear(10, 20),
    nn.ReLU(),
    nn.Linear(20, 30),
    nn.ReLU(),
    nn.Linear(30, 40)
)

x = torch.randn(16, 10)
output = checkpoint_sequential(model, segments=2, input=x)

print("Output shape:", output.shape)


*** ZERO

https://pytorch.org/tutorials/recipes/zero_redundancy_optimizer.html


from torch.distributed.optim import ZeroRedundancyOptimizer

def print_peak_memory(prefix, device):
    if device == 0:
        print(f"{prefix}: {torch.cuda.max_memory_allocated(device) // 1e6}MB ")

def example(rank, world_size, use_zero):
    ...
    # construct DDP model
    ddp_model = DDP(model, device_ids=[rank])
    if use_zero:
        optimizer = ZeroRedundancyOptimizer(
            ddp_model.parameters(),
            optimizer_class=torch.optim.Adam,
            lr=0.01
        )
    ...
    print(f"params sum is: {sum(model.parameters()).sum()}")


*** 坑
* 尽量减少张量搬运
* 使用inplace操作

*** 显存memory优化

torch.cuda.empty_cache()

export PYTORCH_CUDA_ALLOC_CONF=max_split_size_mb:128 # 128-500

export PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True 
适用于动态shape场景
https://docs.pytorch.org/docs/stable/notes/cuda.html#optimizing-memory-usage-with-pytorch-cuda-alloc-conf

** 细节
- 原位操作，但多次使用原位操作可能导致backward错误，比如连续两次sigmoid_
- del logits再loss.backward()


# grad acc
牺牲训练速度，保batch size+显存
- 显存方面，激活值降低，梯度增加，复杂模型可能会降低

is_sync_step = (step + 1) % int(args.grad_accum_step) == 0 if int(args.grad_accum_step) > 0 else True
sync_context = contextlib.nullcontext() if is_sync_step else model.no_sync()

# act recomputation


def checkpoint_wrapper(fn):
    def inner(*args):
        return torch.utils.checkpoint.checkpoint(fn, *args, use_reentrant=True)

    return inner


import torch
import torch.nn as nn
from torch.utils.checkpoint import checkpoint_sequential

model = nn.Sequential(
    nn.Linear(1000, 40000),
    nn.ReLU(),
    nn.Linear(40000, 1000),
    nn.ReLU(),
    nn.Linear(1000, 5),
    nn.ReLU(),
).to("cuda")
input_var = torch.randn(10, 1000, device="cuda", requires_grad=True)
segments = 2
modules = [module for k, module in model._modules.items()]

# (1). 使用checkpoint技术
out = checkpoint_sequential(modules, segments, input_var)
model.zero_grad()
out.sum().backward()
print(f"使用checkpoint技术显存分配峰值: {torch.cuda.max_memory_allocated()/1024/1024}MB") # 628.63671875MB
out_checkpointed = out.data.clone()
grad_checkpointed = {}
for name, param in model.named_parameters():
    grad_checkpointed[name] = param.grad.data.clone()

# (2). 不使用checkpoint技术
original = model
x = input_var.clone().detach_()
out = original(x)
out_not_checkpointed = out.data.clone()
original.zero_grad()
out.sum().backward()
print(f"不使用checkpoint技术显存分配峰值: {torch.cuda.max_memory_allocated()/1024/1024}MB") # 936.17431640625MB

grad_not_checkpointed = {}
for name, param in model.named_parameters():
    grad_not_checkpointed[name] = param.grad.data.clone()
assert torch.allclose(out_checkpointed, out_not_checkpointed)
for name in grad_checkpointed:
    assert torch.allclose(grad_checkpointed[name], grad_not_checkpointed[name])

# offloading

def forward(self, x):
    self.layer1.to("cuda")
    x = self.layer1(x)
    x = torch.relu(x)
    self.layer1.to("cpu")

    self.layer2.to("cuda")
    x = self.layer2(x)
    x = torch.relu(x)
    self.layer2.to("cpu")
    return x

# 优化器

foreach=False



*** 小心同步

tensor.item()、tensor[0]
tensor.cpu()、numpy()
print(tensor)
torch.num_nonzero()

*** gradient compress reduction
- https://main-horse.github.io/posts/reduction-precision/

m.register_comm_hook(dist.group.WORLD, bf16_compress_hook)
with torch.autocast("cuda", bfloat16):
  m(x).backward() # <-- will sync grads via bf16


# 分析

import torch

def pow2range(start, stop, base=1.0):
    return [base * (2 ** i) for i in range(start, stop + 1)]

BS = 4096
grad_stds = pow2range(-8, -4)  # approx 0.004 ~ 0.0625
world_sizes = [int(R) for R in pow2range(1, 10)]  # 2..=1024

# Simulate reductions
std_of_diff = {std: [] for std in grad_stds}
with torch.device('cuda'):
    for std in grad_stds:
        for R in world_sizes:
            w = torch.normal(0.0, std, (R, BS), dtype=torch.bfloat16)
            o_bf16 = sum(v for v in w/R)
            o_fp32 = (w/R).sum(dim=0)  # equivalent to float().sum().bfloat16()
            diff_std = (o_bf16 - o_fp32).std().item()
            std_of_diff[std].append(diff_std)


*** 异步优化

https://zhuanlan.zhihu.com/p/9616453650

* pinned=True+ non_blocking=True + multiple cuda streams ，传输数据最快
- pinned=True+ non_blocking=True： 
  1）h2d从pageable的15ms到pinned memory的2ms；2）优化 从h2d完成 到 下一个GPU kernel launch期间的CPU耗时
- multiple cuda streams：
    h2d和GPU计算并行，double buffering的思想
    可能增加GPU队列间同步的额外开销



https://pytorch.org/tutorials/intermediate/pinmem_nonblock.html

Generally, asynchronous copies to a device are safe without explicit synchronization
only when the target is a CUDA-enabled device and the original tensor is in pageable memory.

In summary, copying data from CPU to GPU is safe when using non_blocking=True,
but for any other direction, non_blocking=True can still be used but the user must make sure that a device synchronization
is executed before the data is accessed. (torch.cuda.synchronize())


# Example

import time
import torch
from torch import nn
from torch.profiler import profile, ProfilerActivity
import torchvision.transforms as transforms
from torchvision.datasets import CIFAR10
from torch.utils.data import DataLoader


class SimpleNet(nn.Module):
  def __init__(self):
    super(SimpleNet, self).__init__()
    self.fc1 = nn.Linear(512, 10000)
    self.fc2 = nn.Linear(10000, 1000)
    self.fc3 = nn.Linear(1000, 10)

  def forward(self, x):
    out = self.fc1(x)
    out = self.fc2(out)
    out = self.fc3(out)
    return out


assert torch.cuda.is_available()
device = torch.device("cuda")
model = SimpleNet().to(device)
optimizer = torch.optim.SGD(model.parameters(), lr=0.01)


def train_1(model, optimizer, trainloader, num_iters):
  with profile(activities=[ProfilerActivity.CPU, ProfilerActivity.CUDA]) as prof:
    for i, batch in enumerate(trainloader, 0):
      if i >= num_iters:
        break
      data = batch[0].cuda(non_blocking=True)

      optimizer.zero_grad()
      output = model(data)
      loss = output.sum()

      loss.backward()
      optimizer.step()
  prof.export_chrome_trace(f"logs/traces/PROF_non_blocking.json")


def train_2(model, optimizer, trainloader, num_iters):
  # Create two CUDA streams
  stream1 = torch.cuda.Stream()
  stream2 = torch.cuda.Stream()
  submit_stream = stream1
  running_stream = stream2
  with profile(activities=[ProfilerActivity.CPU, ProfilerActivity.CUDA]) as prof:
    for i, batch in enumerate(trainloader, 0):
      if i >= num_iters:
        break

      with torch.cuda.stream(submit_stream):
        data = batch[0].cuda(non_blocking=True)
        submit_stream.wait_stream(running_stream)

        # Forward pass
        optimizer.zero_grad()
        output = model(data)
        loss = output.sum()

        # Backward pass and optimize
        loss.backward()
        optimizer.step()

      # Alternate between the two streams
      submit_stream = stream2 if submit_stream == stream1 else stream1
      running_stream = stream2 if running_stream == stream1 else stream1

  prof.export_chrome_trace(f"logs/traces/PROF_double_buffering_wait_after_data.json")

transform = transforms.Compose(
  [transforms.ToTensor(), transforms.Resize([512, 512])]
)
trainset = CIFAR10(root="../data", train=True, download=True, transform=transform)
trainloader = DataLoader(trainset, batch_size=32, pin_memory=True, num_workers=4)

start = time.perf_counter()
train_1(model, optimizer, trainloader, num_iters=60) # non_blocking: 9.32s, pin_memory=False: 9.96s, non_blocking=False: 10.38s
# train_2(model, optimizer, trainloader, num_iters=60) # 9.23s
print(time.perf_counter() - start)


*** backward异步

https://docs.pytorch.org/docs/stable/notes/cuda.html#stream-semantics-of-backward-passes


*** distributed ckpt

https://github.com/pytorch/tutorials/blob/main/recipes_source/distributed_checkpoint_recipe.rst

*** async distributed ckpt

https://pytorch.org/tutorials/recipes/distributed_async_checkpoint_recipe.html

https://github.com/pytorch/pytorch/blob/main/torch/distributed/checkpoint/state_dict_saver.py

import os

import torch
import torch.distributed as dist
import torch.distributed.checkpoint as dcp
import torch.multiprocessing as mp
import torch.nn as nn

from torch.distributed.fsdp import FullyShardedDataParallel as FSDP
from torch.distributed.checkpoint.state_dict import get_state_dict, set_state_dict
from torch.distributed.checkpoint.stateful import Stateful
from torch.distributed.fsdp.fully_sharded_data_parallel import StateDictType

CHECKPOINT_DIR = "checkpoint"


class AppState(Stateful):
    """This is a useful wrapper for checkpointing the Application State. Since this object is compliant
    with the Stateful protocol, DCP will automatically call state_dict/load_stat_dict as needed in the
    dcp.save/load APIs.

    Note: We take advantage of this wrapper to hande calling distributed state dict methods on the model
    and optimizer.
    """

    def __init__(self, model, optimizer=None):
        self.model = model
        self.optimizer = optimizer

    def state_dict(self):
        # this line automatically manages FSDP FQN's, as well as sets the default state dict type to FSDP.SHARDED_STATE_DICT
        model_state_dict, optimizer_state_dict = get_state_dict(model, optimizer)
        return {
            "model": model_state_dict,
            "optim": optimizer_state_dict
        }

    def load_state_dict(self, state_dict):
        # sets our state dicts on the model and optimizer, now that we've loaded
        set_state_dict(
            self.model,
            self.optimizer,
            model_state_dict=state_dict["model"],
            optim_state_dict=state_dict["optim"]
        )

class ToyModel(nn.Module):
    def __init__(self):
        super(ToyModel, self).__init__()
        self.net1 = nn.Linear(16, 16)
        self.relu = nn.ReLU()
        self.net2 = nn.Linear(16, 8)

    def forward(self, x):
        return self.net2(self.relu(self.net1(x)))


def setup(rank, world_size):
    os.environ["MASTER_ADDR"] = "localhost"
    os.environ["MASTER_PORT"] = "12355 "

    # initialize the process group
    dist.init_process_group("nccl", rank=rank, world_size=world_size)
    torch.cuda.set_device(rank)


def cleanup():
    dist.destroy_process_group()


def run_fsdp_checkpoint_save_example(rank, world_size):
    print(f"Running basic FSDP checkpoint saving example on rank {rank}.")
    setup(rank, world_size)

    # create a model and move it to GPU with id rank
    model = ToyModel().to(rank)
    model = FSDP(model)

    loss_fn = nn.MSELoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=0.1)

    checkpoint_future = None
    for step in range(10):
        optimizer.zero_grad()
        model(torch.rand(8, 16, device="cuda")).sum().backward()
        optimizer.step()

        # waits for checkpointing to finish if one exists, avoiding queuing more then one checkpoint request at a time
        if checkpoint_future is not None:
            checkpoint_future.result()

        state_dict = { "app": AppState(model, optimizer) }
        checkpoint_future = dcp.async_save(state_dict, checkpoint_id=f"{CHECKPOINT_DIR}_step{step}")

    cleanup()


if __name__ == "__main__":
    world_size = torch.cuda.device_count()
    print(f"Running async checkpoint example on {world_size} devices.")
    mp.spawn(
        run_fsdp_checkpoint_save_example,
        args=(world_size,),
        nprocs=world_size,
        join=True,
    )