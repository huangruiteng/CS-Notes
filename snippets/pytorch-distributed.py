详细介绍：https://pytorch.org/docs/stable/distributed.html
- 不同backend+CPU/GPU支持通信原语的情况
- Common environment variables

tutorial：https://pytorch.org/tutorials/intermediate/dist_tuto.html
tutorial2: https://pytorch.org/tutorials/intermediate/ddp_tutorial.html

overview: https://pytorch.org/tutorials/beginner/dist_overview.html

Distributed Data-Parallel (DDP)
Fully Sharded Data-Parallel Training (FSDP) when your model cannot fit on one GPU.
- https://pytorch.org/tutorials/intermediate/FSDP_tutorial.html
Tensor Parallel (TP)  if you reach scaling limitations with FSDP.
Pipeline Parallel (PP)

* Sharding primitives
- DTensor and DeviceMesh are primitives used to build parallelism in terms of sharded or replicated tensors on N-dimensional process groups.
- DTensor represents a tensor that is sharded and/or replicated, and communicates automatically to reshard tensors as needed by operations.
- DeviceMesh abstracts the accelerator device communicators into a multi-dimensional array, which manages the underlying ProcessGroup instances for collective communications in multi-dimensional parallelisms. Try out our Device Mesh Recipe to learn more.

torchrun


DDP和DP的区别：
- Each process maintains its own optimizer and performs a complete optimization step with each iteration. While this may appear redundant, since the gradients have already been gathered together and averaged across processes and are thus the same for every process, this means that no parameter broadcast step is needed, reducing time spent transferring tensors between nodes.
- 多进程，Python性能好
- 通信效率: DP 的通信成本随着 GPU 数量线性增长，而 DDP 支持 Ring AllReduce，其通信成本是恒定的，与 GPU 数量无关。
- 同步参数: DP 通过收集梯度到 device[0]，在device[0] 更新参数，然后其他设备复制 device[0] 的参数实现各个模型同步；
  DDP 通过保证初始状态相同并且改变量也相同（指同步梯度） ，保证模型同步。
- DDP支持Model Parallel：
  - DistributedDataParallel works with model parallel, while DataParallel does not at this time.
  - When DDP is combined with model parallel, each DDP process would use model parallel, and all processes collectively would use data parallel.

  Ring AllReduce
  baidu allreduce: https://andrew.gibiansky.com/blog/machine-learning/baidu-allreduce/

### 通信库

Gloo: a collective communications library.
https://github.com/facebookincubator/gloo, 2019.

NVIDIA Collective Communications Library (NCCL).
https://developer.nvidia.com/nccl, 2019.

NVLINK AND NVSWITCH: The Building Blocks of
Advanced Multi-GPU Communication. https:
//www.nvidia.com/en-us/data-center/nvlink/,
2019.

Open MPI: A High Performance Message Passing Library. https://www.open-mpi.org/, 2019


MPI的讨论，若干库和优化，引入pytorch的步骤：https://pytorch.org/tutorials/intermediate/dist_tuto.html#communication-backends


# nccl

use shared file system to init: the file system must support locking through fcntl.

dist.init_process_group(
    init_method='file:///mnt/nfs/sharedfile',
    rank=args.rank,
    world_size=4)

tcp: init_method='tcp://10.1.1.20:23456'


### DP

model = nn.DataParallel(model)


### DDP

细节
- 优化器同一随机种子 For optimizers with intrinsic randomness, diﬀerent processes can initialize their states using the same random seed
- GPU devices cannot be shared across DDP processes (i.e. one GPU for one DDP process).

Currently, find_unused_parameters=True must be passed into torch.nn.parallel.DistributedDataParallel() initialization
if there are parameters that may be unused in the forward pass,

import torch
import torch.distributed as dist
import torch.multiprocessing as mp
import torch.nn as nn
import torch.optim as optim
import os
from torch.nn.parallel import DistributedDataParallel as DDP


def example(rank, world_size):
  # create default process group
  dist.init_process_group("gloo", rank=rank, world_size=world_size)
  # create local model
  model = nn.Linear(10, 10).to(rank)
  # construct DDP model
  ddp_model = DDP(model, device_ids=[rank])
  # define loss function and optimizer
  loss_fn = nn.MSELoss()
  optimizer = optim.SGD(ddp_model.parameters(), lr=0.001)

  # forward pass
  outputs = ddp_model(torch.randn(20, 10).to(rank))
  labels = torch.randn(20, 10).to(rank)
  # backward pass
  loss_fn(outputs, labels).backward()
  # update parameters
  optimizer.step()
  dist.barrier()
  print(ddp_model.state_dict(), rank)

def main():
  world_size = 2
  mp.spawn(example,
           args=(world_size,),
           nprocs=world_size,
           join=True)

if __name__=="__main__":
  # Environment variables which need to be
  # set when using c10d's default "env"
  # initialization mode.
  os.environ["MASTER_ADDR"] = "localhost"
  os.environ["MASTER_PORT"] = "29500"
  main()


# 细节：

- DDP仅支持所有worker同一设备类型，不支持部分worker GPU、部分worker CPU

- 是否需要torch.cuda.set_device
https://discuss.pytorch.org/t/does-ddp-with-torchrun-need-torch-cuda-set-device-device/178723


### DDP Example

import os
import sys
import tempfile
import torch
import torch.distributed as dist
import torch.nn as nn
import torch.optim as optim
import torch.multiprocessing as mp

from torch.nn.parallel import DistributedDataParallel as DDP


def setup(rank: int, world_size: int):
  os.environ['MASTER_ADDR'] = 'localhost'
  os.environ['MASTER_PORT'] = '12355'
  if torch.cuda.is_available() and world_size <= torch.cuda.device_count():
    device = torch.device(f"cuda:{rank}")
    device_ids = [rank]
    torch.cuda.set_device(device)
  else:
    print(
        f"invalid cuda device count: {torch.cuda.device_count()}, use cpu instead"
    )
    device = torch.device("cpu")
    device_ids = None
  backend = "nccl" if device.type == "cuda" else "gloo"
  dist.init_process_group(backend, rank=rank, world_size=world_size)
  print(
      f"DDP setup, device: {device}, backend: {backend}, rank: {rank}, world_size: {world_size}"
  )
  return device, device_ids


def cleanup():
  dist.destroy_process_group()


class ToyModel(nn.Module):

  def __init__(self):
    super(ToyModel, self).__init__()
    self.net1 = nn.Linear(10, 10)
    self.relu = nn.ReLU()
    self.net2 = nn.Linear(10, 5)

  def forward(self, x):
    return self.net2(self.relu(self.net1(x)))


def demo_basic(rank, world_size):
  print(f"Running basic DDP example on rank {rank}.")
  setup(rank, world_size)

  # create model and move it to GPU with id rank
  model = ToyModel().to(rank)
  ddp_model = DDP(model, device_ids=[rank])

  loss_fn = nn.MSELoss()
  optimizer = optim.SGD(ddp_model.parameters(), lr=0.001)

  optimizer.zero_grad()
  outputs = ddp_model(torch.randn(20, 10))
  labels = torch.randn(20, 5).to(rank)
  loss_fn(outputs, labels).backward()
  optimizer.step()

  cleanup()
  print(f"Finished running basic DDP example on rank {rank}.")


def demo_checkpoint(rank, world_size):
  print(f"Running DDP checkpoint example on rank {rank}.")
  setup(rank, world_size)

  model = ToyModel().to(rank)
  ddp_model = DDP(model, device_ids=[rank])

  CHECKPOINT_PATH = tempfile.gettempdir() + "/model.checkpoint"
  if rank == 0:
    # All processes should see same parameters as they all start from same
    # random parameters and gradients are synchronized in backward passes.
    # Therefore, saving it in one process is sufficient.
    torch.save(ddp_model.state_dict(), CHECKPOINT_PATH)

  # Use a barrier() to make sure that process 1 loads the model after process
  # 0 saves it.
  dist.barrier()
  # configure map_location properly
  map_location = {'cuda:%d' % 0: 'cuda:%d' % rank}
  ddp_model.load_state_dict(
      torch.load(CHECKPOINT_PATH, map_location=map_location, weights_only=True))

  loss_fn = nn.MSELoss()
  optimizer = optim.SGD(ddp_model.parameters(), lr=0.001)

  optimizer.zero_grad()
  outputs = ddp_model(torch.randn(20, 10))
  labels = torch.randn(20, 5).to(rank)

  loss_fn(outputs, labels).backward()
  optimizer.step()

  # Not necessary to use a dist.barrier() to guard the file deletion below
  # as the AllReduce ops in the backward pass of DDP already served as
  # a synchronization.

  if rank == 0:
    os.remove(CHECKPOINT_PATH)

  cleanup()
  print(f"Finished running DDP checkpoint example on rank {rank}.")


class ToyMpModel(nn.Module):

  def __init__(self, dev0, dev1):
    super(ToyMpModel, self).__init__()
    self.dev0 = dev0
    self.dev1 = dev1
    self.net1 = torch.nn.Linear(10, 10).to(dev0)
    self.relu = torch.nn.ReLU()
    self.net2 = torch.nn.Linear(10, 5).to(dev1)

  def forward(self, x):
    x = x.to(self.dev0)
    x = self.relu(self.net1(x))
    x = x.to(self.dev1)
    return self.net2(x)


def demo_model_parallel(rank, world_size):
  print(f"Running DDP with model parallel example on rank {rank}.")
  setup(rank, world_size)

  # setup mp_model and devices for this process
  dev0 = rank * 2
  dev1 = rank * 2 + 1
  mp_model = ToyMpModel(dev0, dev1)
  # When passing a multi-GPU model to DDP, device_ids and output_device must NOT be set.
  # Input and output data will be placed in proper devices by either the application or the model forward() method.
  ddp_mp_model = DDP(mp_model)

  loss_fn = nn.MSELoss()
  optimizer = optim.SGD(ddp_mp_model.parameters(), lr=0.001)

  optimizer.zero_grad()
  # outputs will be on dev1
  outputs = ddp_mp_model(torch.randn(20, 10))
  labels = torch.randn(20, 5).to(dev1)
  loss_fn(outputs, labels).backward()
  optimizer.step()

  cleanup()
  print(f"Finished running DDP with model parallel example on rank {rank}.")


def run_demo(demo_fn, world_size):
  mp.spawn(demo_fn, args=(world_size,), nprocs=world_size, join=True)


if __name__ == "__main__":
  n_gpus = torch.cuda.device_count()
  assert n_gpus >= 2, f"Requires at least 2 GPUs to run, but got {n_gpus}"
  world_size = n_gpus
  run_demo(demo_basic, world_size)
  run_demo(demo_checkpoint, world_size)
  world_size = n_gpus // 2
  run_demo(demo_model_parallel, world_size)


### distributed

"""run.py:"""
#!/usr/bin/env python
import os
import sys
import torch
import torch.distributed as dist
import torch.multiprocessing as mp


def init_process(rank, size, fn, backend='gloo'):
  """ Initialize the distributed environment. """
  os.environ['MASTER_ADDR'] = '127.0.0.1'
  os.environ['MASTER_PORT'] = '29500'
  dist.init_process_group(backend, rank=rank, world_size=size)
  fn(rank, size)


"""Blocking point-to-point communication."""


def run_1(rank, size):
  print("Blocking point-to-point communication.")
  tensor = torch.zeros(1).to(rank)
  if rank == 0:
    tensor += 1
    # Send the tensor to process 1
    dist.send(tensor=tensor, dst=1)
  else:
    # Receive tensor from process 0
    dist.recv(tensor=tensor, src=0)
  print('Rank ', rank, ' has data ', tensor[0])

"""Non-blocking point-to-point communication."""

# 用于实现：
# 1. https://github.com/baidu-research/baidu-allreduce
# 2. Accurate, Large Minibatch SGD: Training ImageNet in 1 Hour

def run_2(rank, size):
  print("Non-blocking point-to-point communication.")
  tensor = torch.zeros(1).to(rank)
  req = None
  if rank == 0:
    tensor += 1
    # Send the tensor to process 1
    req = dist.isend(tensor=tensor, dst=1)
    print('Rank 0 started sending')
  else:
    # Receive tensor from process 0
    req = dist.irecv(tensor=tensor, src=0)
    print('Rank 1 started receiving')
  req.wait()
  print('Rank ', rank, ' has data ', tensor[0])

""" All-Reduce example."""
def run_3(rank, size):
  """ Simple collective communication. """
  print("All-Reduce example.")
  group = dist.new_group([0, 1])
  tensor = torch.ones(1).to(rank)
  dist.all_reduce(tensor, op=dist.ReduceOp.SUM, group=group)
  print('Rank ', rank, ' has data ', tensor[0])

if __name__ == "__main__":
  world_size = 2
  processes = []
  if "google.colab" in sys.modules:
    print("Running in Google Colab")
    mp.get_context("spawn")
  else:
    mp.set_start_method("spawn")
  for rank in range(world_size):
    p = mp.Process(target=init_process, args=(rank, world_size, run_3, 'nccl'))
    p.start()
    processes.append(p)

  for p in processes:
    p.join()



### 通信原语、Group 的运用

dist.ReduceOp.SUM,
dist.ReduceOp.PRODUCT,
dist.ReduceOp.MAX,
dist.ReduceOp.MIN,
dist.ReduceOp.BAND,
dist.ReduceOp.BOR,
dist.ReduceOp.BXOR,
dist.ReduceOp.PREMUL_SUM.

支持情况：https://pytorch.org/docs/stable/distributed.html

dist.broadcast(tensor, src, group): Copies tensor from src to all other processes.
dist.reduce(tensor, dst, op, group): Applies op to every tensor and stores the result in dst.
dist.all_reduce(tensor, op, group): Same as reduce, but the result is stored in all processes.
dist.scatter(tensor, scatter_list, src, group): Copies the ith tensor scatter_list[i] to the ith process.
dist.gather(tensor, gather_list, dst, group): Copies tensor from all processes in dst.
dist.all_gather(tensor_list, tensor, group): Copies tensor from all processes to tensor_list, on all processes.
dist.barrier(group): Blocks all processes in group until each one has entered this function.
dist.all_to_all(output_tensor_list, input_tensor_list, group): Scatters list of input tensors to all processes in a group and return gathered list of tensors in output list.

# Group

As opposed to point-to-point communcation, collectives allow for communication patterns across all processes in a group.
A group is a subset of all our processes. To create a group, we can pass a list of ranks to dist.new_group(group).
By default, collectives are executed on all processes, also known as the world.
For example, in order to obtain the sum of all tensors on all processes, we can use the dist.all_reduce(tensor, op, group) collective.

""" All-Reduce example."""
def run(rank, size):
    """ Simple collective communication. """
    group = dist.new_group([0, 1])
    tensor = torch.ones(1)
    dist.all_reduce(tensor, op=dist.ReduceOp.SUM, group=group)
    print('Rank ', rank, ' has data ', tensor[0])


### Other usage

def _distributed_task(rank, world_size, ckpt_dir, task_name, result_dir):
  setup(rank, world_size)
  ...
  device = None
  device_ids = None
  if torch.cuda.is_available() and world_size <= torch.cuda.device_count():
    device = torch.device(f"cuda:{rank}")
    device_ids = [rank]
  else:
    print(f"invalid cuda device count: {torch.cuda.device_count()}, use cpu instead")
    device = torch.device("cpu")

  model = model.to(device)
  ddp_model = DDPModel(model, device_ids=device_ids)
  ...
  dist.barrier()
  all_loaders = [None] * world_size
  dist.all_gather_object(all_loaders, loader.state_dict())
  dist.barrier()
  if rank == 0:
    ...
  dist.destroy_process_group()


### all_reduce

""" Implementation of a ring-reduce with addition. """
def allreduce(send, recv):
  rank = dist.get_rank()
  size = dist.get_world_size()
  send_buff = send.clone()
  recv_buff = send.clone()
  accum = send.clone()

  left = ((rank - 1) + size) % size
  right = (rank + 1) % size

  for i in range(size - 1):
    if i % 2 == 0:
      # Send send_buff
      send_req = dist.isend(send_buff, right)
      dist.recv(recv_buff, left)
      accum[:] += recv_buff[:]
    else:
      # Send recv_buff
      send_req = dist.isend(recv_buff, right)
      dist.recv(send_buff, left)
      accum[:] += send_buff[:]
    send_req.wait()
  recv[:] = accum[:]


### TP

dtensor = _shard_tensor(mA, device_mesh, (Shard(0),))

### TorchRun

https://pytorch.org/docs/stable/distributed.elastic.html

https://pytorch.org/docs/stable/elastic/run.html

torchrun provides a superset of the functionality as torch.distributed.launch with the following additional functionalities:

- Worker failures are handled gracefully by restarting all workers.

- Worker RANK and WORLD_SIZE are assigned automatically.

- Number of nodes is allowed to change between minimum and maximum sizes (elasticity).

# single node multi worker

torchrun
    --standalone
    --nnodes=1
    --nproc-per-node=$NUM_TRAINERS
    YOUR_TRAINING_SCRIPT.py (--arg1 ... train script args...)

# Stacked single-node multi-worker

torchrun
    --rdzv-backend=c10d
    --rdzv-endpoint=localhost:0
    --nnodes=1
    --nproc-per-node=$NUM_TRAINERS
    YOUR_TRAINING_SCRIPT.py (--arg1 ... train script args...)

torchrun
    --nnodes=$NUM_NODES
    --nproc-per-node=$NUM_TRAINERS
    --max-restarts=3
    --rdzv-id=$JOB_ID
    --rdzv-backend=c10d
    --rdzv-endpoint=$HOST_NODE_ADDR
    YOUR_TRAINING_SCRIPT.py (--arg1 ... train script args...)



torchrun --nnodes=2 --nproc_per_node=8 --rdzv_id=100 --rdzv_backend=c10d --rdzv_endpoint=localhost:29400 elastic_ddp.py

### pdsh, clustershell, or slurm

# slurm

user also needs to apply cluster management tools like slurm to actually run this command on 2 nodes.

export MASTER_ADDR=$(scontrol show hostname ${SLURM_NODELIST} | head -n 1)

srun --nodes=2 ./torchrun_script.sh.


### elastic_ddp.py

import torch
import torch.distributed as dist
import torch.nn as nn
import torch.optim as optim

from torch.nn.parallel import DistributedDataParallel as DDP

class ToyModel(nn.Module):
    def __init__(self):
        super(ToyModel, self).__init__()
        self.net1 = nn.Linear(10, 10)
        self.relu = nn.ReLU()
        self.net2 = nn.Linear(10, 5)

    def forward(self, x):
        return self.net2(self.relu(self.net1(x)))


def demo_basic():
    torch.cuda.set_device(int(os.environ["LOCAL_RANK"]))
    dist.init_process_group("nccl")
    rank = dist.get_rank()
    print(f"Start running basic DDP example on rank {rank}.")
    # create model and move it to GPU with id rank
    device_id = rank % torch.cuda.device_count()
    model = ToyModel().to(device_id)
    ddp_model = DDP(model, device_ids=[device_id])
    loss_fn = nn.MSELoss()
    optimizer = optim.SGD(ddp_model.parameters(), lr=0.001)

    optimizer.zero_grad()
    outputs = ddp_model(torch.randn(20, 10))
    labels = torch.randn(20, 5).to(device_id)
    loss_fn(outputs, labels).backward()
    optimizer.step()
    dist.destroy_process_group()
    print(f"Finished running basic DDP example on rank {rank}.")

if __name__ == "__main__":
    demo_basic()


### GPU相关

torch.distributed.barrier()
torch.cuda.synchronize()