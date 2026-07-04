import os
from typing import Callable
import math
import torch
import torch.distributed as dist
from absl import logging

from .utils import (
  get_timeout_from_env,
)
from .utils import Singleton


class DistInfo(metaclass=Singleton):

  def __init__(self) -> None:
    pass

  @property
  def rank(self) -> int:
    return int(os.environ.get("RANK", 0))

  @property
  def local_rank(self) -> int:
    return self.rank % self.local_world_size

  @property
  def world_size(self) -> int:
    return dist.get_world_size()

  @property
  def node_idx(self) -> int:
    return self.rank // self.local_world_size

  @property
  def local_world_size(self) -> int:
    local_worker_count = os.environ.get("LOCAL_WORKER_COUNT", None)
    if local_worker_count is not None:
      return int(local_worker_count)
    return torch.cuda.device_count()

  @property
  def nnodes(self) -> int:
    return int(self.world_size / self.local_world_size)


dist_info: DistInfo = DistInfo.instance()


class Communicator:
  _instance = None

  @staticmethod
  def getInstance(*args, **kwargs):
    if Communicator._instance is None:
      Communicator._instance = Communicator(*args, **kwargs)
    return Communicator._instance

  def __init__(
      self,
      shard_fn: Callable,
      comm_group: dist.ProcessGroup,
      enable_hierarchical_all2all=False
  ):
    self._enable_hierarchical_all2all = enable_hierarchical_all2all
    self._init_comm_group(comm_group)
    self._shard_fn_raw = shard_fn

  def _shard_fn(self, ids, world_size, hierarchical_mode=None):
    if hierarchical_mode is None:
      return self._shard_fn_raw(ids, world_size)
    if hierarchical_mode == "intra":
      return self._shard_fn_raw(ids, self._nproc_per_node)
    elif hierarchical_mode == "inter":
      return self._shard_fn_raw(ids, self._world_size) // self._nproc_per_node
    else:
      logging.warning("hierarchical_mode: %s not supported!", hierarchical_mode)
    return self._shard_fn_raw(ids, world_size)

  def _init_comm_group(self, comm_group: dist.ProcessGroup):
    self._world_size = dist.get_world_size()
    self._local_rank = dist_info.local_rank
    self._nproc_per_node = dist_info.local_world_size
    self._node_idx = dist_info.node_idx
    self._rank = dist_info.rank
    self.emb_comm_group = comm_group
    self._model_parallel_size = len(
      dist.get_process_group_ranks(self.emb_comm_group))
    if not self._enable_hierarchical_all2all:
      return

    timeout = get_timeout_from_env()
    nnodes = dist_info.nnodes
    if self._model_parallel_size != self._world_size:
      logging.warning(
        "set model_parallel_size = world_size to enable hierarchical all2all")
      logging.warning(
        "current model_parallel_size: %s, world_size: %s",
        self._model_parallel_size,
        self._world_size,
      )
      self._enable_hierarchical_all2all = False
      return
    if nnodes <= 1:
      logging.warning(
        "hierarchical all-to-all will be disabled since nnodes <= 1")
      self._enable_hierarchical_all2all = False
      return

    if self._nproc_per_node <= 1:
      logging.warning(
        "hierarchical all-to-all will be disabled since nproc_per_node <= 1")
      self._enable_hierarchical_all2all = False
      return

    all_intra_groups = [
      dist.new_group(
        ranks=list(
          range(
            idx * self._nproc_per_node,
            (idx + 1) * self._nproc_per_node,
          )),
        backend="cuda:nccl",
        timeout=timeout,
      ) for idx in range(nnodes)
    ]

    all_inter_groups = [
      dist.new_group(
        ranks=[
          idx * self._nproc_per_node + rank_id for idx in range(nnodes)
        ],
        backend="cuda:nccl",
        timeout=timeout,
      ) for rank_id in range(self._nproc_per_node)
    ]

    self._intra_group = all_intra_groups[self._node_idx]
    self._inter_group = all_inter_groups[self._local_rank]

  def all_to_all_ckpt(self,
                      rank,
                      fid_embs,
                      valid_fids,
                      device,
                      send_empty=False):
    timeout = get_timeout_from_env()
    world_size = self._model_parallel_size
    if valid_fids is not None:
      assert valid_fids.dtype == torch.int64, valid_fids.dtype
    if fid_embs is not None:
      assert fid_embs.dtype == torch.float32, fid_embs.dtype

    assert send_empty == (fid_embs is None)
    assert send_empty == (valid_fids is None)

    if device.type == "cpu":
      gloo_comm_group = dist.new_group(ranks=list(range(0, world_size)),
                                       backend="cpu:gloo",
                                       timeout=timeout)
      dist.barrier(group=gloo_comm_group)
      group = gloo_comm_group
      dist.barrier(group=group)
    else:
      group = self.emb_comm_group

    recv_shape_tensor = torch.full(
      (int(world_size),),
      -12345,
      dtype=torch.int32,
      device=device,
    )
    send_shape_tensor = torch.zeros((int(world_size)), dtype=torch.int32)
    recv_total_size_tensor = torch.full((int(world_size),), -1, dtype=torch.int32, device=device)
    send_total_size_tensor = torch.zeros((int(world_size),), dtype=torch.int32)

    sort_indices = None
    if not send_empty:
      # place unique op on CPU
      assert fid_embs.dim() == 2
      shard_ids = self._shard_fn(valid_fids.cpu(), world_size)
      sort_indices = torch.argsort(shard_ids, stable=True)
      sort_shard_ids = shard_ids[sort_indices]

      uniq_shard_ids, num_ids_per_shard = torch.unique_consecutive(
        sort_shard_ids, return_counts=True)
      send_shape_tensor[uniq_shard_ids] += num_ids_per_shard

      assert fid_embs.numel() % fid_embs.size(
        0) == 0, f"fid_embs.numel() ({fid_embs.numel()}) 不能被 fid_embs.size(0) ({fid_embs.size(0)}) 整除"
      send_total_size_tensor[uniq_shard_ids] += num_ids_per_shard * (fid_embs.numel() // fid_embs.size(0))
    send_shape_tensor = send_shape_tensor.to(device)
    send_total_size_tensor = send_total_size_tensor.to(device)

    dist.all_to_all_single(recv_shape_tensor, send_shape_tensor, group=group)
    dist.all_to_all_single(recv_total_size_tensor, send_total_size_tensor, group=group)
    recv_emb_size = recv_total_size_tensor.sum() // recv_shape_tensor.sum() if recv_shape_tensor.sum() > 0 else 0
    print(
      f"rank {rank} send_shape_buffer {send_shape_tensor}, recv_shape_buffer {recv_shape_tensor}, recv_total_size_tensor {recv_total_size_tensor}, recv_emb_size {recv_emb_size}",
      flush=True)

    if device.type == "cpu":
      return self._all_to_all_ckpt_cpu(rank, world_size, fid_embs, valid_fids, timeout, send_empty, group,
                                       recv_shape_tensor, send_shape_tensor, recv_emb_size, sort_indices)
    else:
      return self._all_to_all_ckpt_gpu(rank, world_size, fid_embs, valid_fids, device, send_empty, group,
                                       recv_shape_tensor, send_shape_tensor, recv_emb_size, sort_indices)

  def _all_to_all_ckpt_cpu(self, rank, world_size, fid_embs, valid_fids, timeout, send_empty, group, recv_shape_tensor,
                           send_shape_tensor, recv_emb_size, sort_indices):
    fid_dtype = torch.int64
    emb_dtype = torch.float32

    send_shape_buffer = list(torch.split(send_shape_tensor, [1] * world_size))
    recv_shape_buffer = list(torch.split(recv_shape_tensor, [1] * world_size))

    if send_empty:
      send_tensor = torch.empty(
        (0,),
        dtype=emb_dtype,
      )
      send_fids = torch.empty(
        (0,),
        dtype=fid_dtype,
      )
    else:
      unique_id = torch.unique(sort_indices)
      assert (unique_id.size() == sort_indices.size()), "unique fids when all_to_all_ckpt failed"
      send_tensor = fid_embs[sort_indices].cpu()
      send_fids = valid_fids[sort_indices].cpu()
      assert recv_emb_size == math.prod(fid_embs.shape[1:]), "recv_emb_size not match"

    recv_tensor = torch.empty(
      (recv_shape_tensor.sum(), recv_emb_size), dtype=emb_dtype,
    )
    recv_fids = torch.empty(
      (recv_shape_tensor.sum(),), dtype=fid_dtype,
    )

    if os.environ.get("TORCH_DISTRIBUTED_DEBUG") == "DETAIL":
      print(
        f"_all_to_all_ckpt_cpu debug rank {rank} (before all2all), tensor {send_tensor}, send_fids {send_fids} recv_ts {recv_tensor}, recv_shape: {recv_shape_buffer}, send_shape: {send_shape_buffer}",
        flush=True)
    dist.all_to_all_single(
      recv_tensor,
      send_tensor,
      recv_shape_buffer,
      send_shape_buffer,
      group=group,
    )
    dist.all_to_all_single(
      recv_fids,
      send_fids,
      recv_shape_buffer,
      send_shape_buffer,
      group=group,
    )
    sort_indices = torch.argsort(recv_fids, stable=True)
    recv_fids = recv_fids[sort_indices]
    recv_tensor = recv_tensor[sort_indices]
    dist.barrier(group=group)
    print("ckpt alltoall cpu end", flush=True)
    if os.environ.get("TORCH_DISTRIBUTED_DEBUG") == "DETAIL":
      print(
        f"_all_to_all_ckpt_cpu debug rank {rank} (after all2all), send_ts {send_tensor}, send_fids {send_fids}, recv_ts {recv_tensor}, recv_fids: {recv_fids}, recv_shape: {recv_shape_buffer}, send_shape: {send_shape_buffer}",
        flush=True)
    return recv_tensor, recv_fids

  def _all_to_all_ckpt_gpu(self, rank, world_size, fid_embs, valid_fids, device, send_empty, group, recv_shape_tensor,
                           send_shape_tensor, recv_emb_size, sort_indices):
    fid_dtype = torch.int64
    emb_dtype = torch.float32

    if send_empty:
      send_tensor_list = [
        torch.empty(
          (0,),
          dtype=emb_dtype,
          device=device,
        ) for _ in range(world_size)
      ]
      send_fids_list = [
        torch.empty(
          (0,),
          dtype=fid_dtype,
          device=device,
        ) for _ in range(world_size)
      ]
    else:
      unique_id = torch.unique(sort_indices)
      assert (unique_id.size() == sort_indices.size()), "unique fids when all_to_all_ckpt failed"
      send_tensor_list = list(torch.split(fid_embs[sort_indices].to(device), send_shape_tensor.tolist()))
      send_fids_list = list(torch.split(valid_fids[sort_indices].to(device), send_shape_tensor.tolist()))
      assert recv_emb_size == math.prod(fid_embs.shape[1:]), "recv_emb_size not match"

    recv_tensor_list = [
      torch.empty(
        (recv_shape_tensor[i].item(), recv_emb_size),
        dtype=emb_dtype,
        device=device
      ) for i in range(world_size)
    ]
    recv_fids_list = [
      torch.empty(
        (recv_shape_tensor[i].item(),),
        dtype=fid_dtype,
        device=device
      ) for i in range(world_size)
    ]
    dist.all_to_all(
      recv_tensor_list,
      send_tensor_list,
      group=group,
    )
    if os.environ.get("TORCH_DISTRIBUTED_DEBUG") == "DETAIL":
      print(f'_all_to_all_ckpt_gpu debug {rank}', send_fids_list, send_tensor_list, flush=True)
    dist.all_to_all(
      recv_fids_list,
      send_fids_list,
      group=group,
    )
    recv_tensor = torch.concat(recv_tensor_list)
    recv_fids = torch.concat(recv_fids_list)
    dist.barrier(group=group)
    print("ckpt alltoall gpu end", flush=True)
    return recv_tensor, recv_fids


def get_communicator(*args, **kwargs) -> Communicator:
  return Communicator.getInstance(*args, **kwargs)


def all_to_all_ckpt(rank, fid_embs, valid_fids, device, send_empty=False):
  communicator = get_communicator()
  return communicator.all_to_all_ckpt(rank=rank, fid_embs=fid_embs, valid_fids=valid_fids, device=device,
                                      send_empty=send_empty)
