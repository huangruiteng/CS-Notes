### find_unused_parameters = True

import os   
import torch   
import torch.distributed as dist   
import torch.multiprocessing as mp   
import torch.nn as nn   
import torch.optim as optim   

from torch.nn.parallel import DistributedDataParallel as DDP
from timeit import default_timer as timer

os.environ['MASTER_ADDR'] = 'localhost'   
os.environ['MASTER_PORT'] = '12138'   
 

def example(rank, world_size):       
    # create default process group       
    dist.init_process_group("gloo",rank=rank, 
world_size=world_size,init_method='env://')       
    # create local model
    model = nn.Linear(10, 10).to(rank)
    # construct DDP model
    ddp_model = DDP(model, device_ids=[rank], find_unused_parameters = False)
    # define loss function and optimizer
    loss_fn = nn.MSELoss()
    optimizer = optim.SGD(ddp_model.parameters(), lr=0.001)

    buf = 0
    tmp = 0
    for i in range(10000):
        start = timer()
        # forward pass
        outputs = ddp_model(torch.randn(20, 10).to(rank))
        end = timer()

        tmp = end-start
        buf+=tmp
        labels = torch.randn(20, 10).to(rank)
        # backward pass
        loss_fn(outputs, labels).backward()
        # update parameters
        optimizer.step()
    print(tmp)
    print(buf)
    print(buf/10000)

def main():
    world_size = 1
    mp.spawn(example,
        args=(world_size,),
        nprocs=world_size,
        join=True)

if __name__=="__main__":
   for i in range(10):
     main()



### distributed example


"""run.py:"""
#!/usr/bin/env python
import os
import sys
import torch
import torch.distributed as dist
import torch.multiprocessing as mp

#!/usr/bin/env python
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim

from math import ceil
from random import Random
from torch.multiprocessing import Process
from torch.autograd import Variable
from torchvision import datasets, transforms


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

### 手写DDP

""" Dataset partitioning helper """
class Partition(object):

  def __init__(self, data, index):
    self.data = data
    self.index = index

  def __len__(self):
    return len(self.index)

  def __getitem__(self, index):
    data_idx = self.index[index]
    return self.data[data_idx]


class DataPartitioner(object):

  def __init__(self, data, sizes=[0.7, 0.2, 0.1], seed=1234):
    self.data = data
    self.partitions = []
    rng = Random()  # from random import Random
    rng.seed(seed)
    data_len = len(data)
    indexes = [x for x in range(0, data_len)]
    rng.shuffle(indexes)

    for frac in sizes:
      part_len = int(frac * data_len)
      self.partitions.append(indexes[0:part_len])
      indexes = indexes[part_len:]

  def use(self, partition):
    return Partition(self.data, self.partitions[partition])


""" Partitioning MNIST """
def partition_dataset():
  dataset = datasets.MNIST('./data', train=True, download=True,
                           transform=transforms.Compose([
                             transforms.ToTensor(),
                             transforms.Normalize((0.1307,), (0.3081,))
                           ]))
  size = dist.get_world_size()
  bsz = 128 // size
  partition_sizes = [1.0 / size for _ in range(size)]
  partition = DataPartitioner(dataset, partition_sizes)
  partition = partition.use(dist.get_rank())
  train_set = torch.utils.data.DataLoader(partition,
                                          batch_size=bsz,
                                          shuffle=True)
  return train_set, bsz


""" Distributed Synchronous SGD Example """

class Net(nn.Module):
  """ Network architecture. """

  def __init__(self):
    super(Net, self).__init__()
    self.conv1 = nn.Conv2d(1, 10, kernel_size=5)
    self.conv2 = nn.Conv2d(10, 20, kernel_size=5)
    self.conv2_drop = nn.Dropout2d()
    self.fc1 = nn.Linear(320, 50)
    self.fc2 = nn.Linear(50, 10)

  def forward(self, x):
    x = F.relu(F.max_pool2d(self.conv1(x), 2))
    x = F.relu(F.max_pool2d(self.conv2_drop(self.conv2(x)), 2))
    x = x.view(-1, 320)
    x = F.relu(self.fc1(x))
    x = F.dropout(x, training=self.training)
    x = self.fc2(x)
    return F.log_softmax(x)

def run_4(rank, size):
  torch.manual_seed(1234)
  train_set, bsz = partition_dataset()
  model = Net().to(rank)
  optimizer = optim.SGD(model.parameters(),
                        lr=0.01, momentum=0.5)

  num_batches = ceil(len(train_set.dataset) / float(bsz))
  for epoch in range(10):
    epoch_loss = 0.0
    for data, target in train_set:
      optimizer.zero_grad()
      output = model(data.to(rank))
      loss = F.nll_loss(output, target.to(rank))
      epoch_loss += loss.item()
      loss.backward()
      average_gradients(model)
      optimizer.step()
    print('Rank ', dist.get_rank(), ', epoch ',
          epoch, ': ', epoch_loss / num_batches)


""" Gradient averaging. """
def average_gradients(model):
  size = float(dist.get_world_size())
  for param in model.parameters():
    dist.all_reduce(param.grad.data, op=dist.ReduceOp.SUM)
    param.grad.data /= size


if __name__ == "__main__":
  world_size = 2
  processes = []
  if "google.colab" in sys.modules:
    print("Running in Google Colab")
    mp.get_context("spawn")
  else:
    mp.set_start_method("spawn")
  for rank in range(world_size):
    p = mp.Process(target=init_process, args=(rank, world_size, run_4, 'nccl'))
    p.start()
    processes.append(p)

  for p in processes:
    p.join()
