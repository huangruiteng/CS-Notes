*** c++

* c10::irange

#include <torch/torch.h>

for (auto i : c10::irange(variable_count)) {
    std::cout << "当前索引: " << i << std::endl;
}

* weak ref

c10/util/intrusive_ptr.h

using weakref_type = c10::weak_intrusive_ptr<TensorImpl, UndefinedTensorImpl>;
get_cached_casts().emplace(arg.unsafeGetTensorImpl(), val_type{weakref_type(arg.getIntrusivePtr()), casted_arg});


* parallel cpu

aten/src/ATen/Parallel-inl.h
aten/src/ATen/Parallel.h
实现在invoke_parallel，native实现用threadpool


*** tensor

# torchao tensor utils

包装tensor，支持dispatch方法

class TorchAOBaseTensor(torch.Tensor):
    """A util tensor subclass that provides commonly used functions
       new tensor subclass can inherit it to get all the utility functions

       class MyTensor(TorchAOBaseTensor):
           pass

    This includes:
       `_get_to_kwargs` that can get the kwargs for `to`
            class MyTensor(TorchAOBaseTensor):
                def to(self, *args, **kwargs):
                    kwargs = _get_to_kwargs(*args, **kwargs)
                    ...
        `implements`:
            implements = MyTensor.implements

            @implements(torch.nn.functional.linear):
            def _(func, types, args, kwargs):
                ...

        `register_layout`:
            register_layout = MyTensor.register_layout

            @register_layout(PlainLayout)
            class PlainAQTTensorImpl(...):
                ...

         `get_tensor_impl_constructor`:
            get_tensor_impl_constructor = MyTensor.get_tensor_impl_constructor
            # in constructor of MyTensor:
            tensor_impl_ctr = get_tensor_impl_constructor(type(_layout))
            tensor_impl = tensor_impl_ctr(data, scale, zero_point, _layout)

    """

    implements = classmethod(_implements)
    __torch_dispatch__ = classmethod(_dispatch__torch_dispatch__)
    __torch_function__ = classmethod(_dispatch__torch_function__)
    register_layout = classmethod(_register_layout)
    get_tensor_impl_constructor = classmethod(_get_tensor_impl_constructor)
    _get_to_kwargs = _get_to_kwargs

    def __tensor_flatten__(self):
        raise NotImplementedError("Subclasses must implement __tensor_flatten__")

    @classmethod
    def __tensor_unflatten__(
        cls, tensor_data_dict, tensor_attributes, outer_size, outer_stride
    ):
        raise NotImplementedError("Subclasses must implement __tensor_unflatten__")

    def __repr__(self):
        raise NotImplementedError("Subclasses must implement __repr__")

    def get_layout(self):
        if not hasattr(self, "_layout"):
            return None
        return self._layout


def _implements(cls, aten_ops_or_torch_fns):
    """Use this decorator to implement a function for an aten ops in __torch_dispatch__
    (if user passed in a list of ops)
    or torch function in __torch_function__ (if user passed in a single object)

    class MyTensor(torch.Tensor):
        ...
        implements = classmethod(_implements)

    implements = MyTensor.implements

    @implements(torch.nn.functional.linear):
    def _(func, types, args, kwargs):
        ...

    """
    if not hasattr(cls, "_ATEN_OP_OR_TORCH_FN_TABLE"):
        cls._ATEN_OP_OR_TORCH_FN_TABLE = {}

    if not isinstance(aten_ops_or_torch_fns, (list, tuple)):
        aten_ops_or_torch_fns = [aten_ops_or_torch_fns]

    def decorator(func):
        for op in aten_ops_or_torch_fns:

            @functools.wraps(op)
            def wrapper(f, types, args, kwargs):
                return func(f, types, args, kwargs)

            cls._ATEN_OP_OR_TORCH_FN_TABLE[op] = wrapper
        return func

    return decorator

# PackedTensor

import torch
from dataclasses import dataclass
from typing import List, Union
from functools import reduce


@dataclass
class TensorMeta:
  shape: torch.Size
  dtype: torch.dtype
  device: Union[str, torch.device]


class PackedTensor:

  def __init__(self):
    self._meta = []
    self._offsets = []
    self.data = None

  @classmethod
  def build_from_tensors_with_offset(cls, tensor_list):
    packed_tensor = cls()
    offset = 0
    for i, tensor in enumerate(tensor_list):
      packed_tensor._meta.append((TensorMeta(tensor.shape, tensor.dtype,
                                             tensor.device)))
      element_size = tensor.element_size()
      num_bytes = element_size * tensor.numel()
      packed_tensor._offsets.append(offset)
      offset += num_bytes
    packed_tensor._offsets.append(offset)

    new_tensor_list = []
    new_tensor_offset = []
    for tensor in tensor_list:
      new_tensor = tensor.view(-1).view(torch.uint8)
      new_tensor_offset.append(new_tensor.size(0))
      new_tensor_list.append(new_tensor)

    packed_tensor.data = torch.cat(new_tensor_list)

    return packed_tensor, new_tensor_offset

  @classmethod
  def build_from_meta_with_offset(cls, meta_list: List[TensorMeta]):
    packed_tensor = cls()
    offset = 0
    new_tensor_offset = []
    for i, meta in enumerate(meta_list):
      packed_tensor._meta.append(meta)
      packed_tensor._offsets.append(offset)
      num_elements = torch.prod(torch.tensor(meta.shape)).item()
      element_size = torch.tensor([], dtype=meta.dtype).element_size()
      num_bytes = num_elements * element_size
      new_tensor_offset.append(num_bytes)
      offset += num_bytes
    packed_tensor._offsets.append(offset)

    packed_tensor.data = torch.empty([offset],
                                     dtype=torch.uint8,
                                     device=meta_list[0].device)
    # new_tensor_offset = [
    #     j - i
    #     for i, j in zip(packed_tensor._offsets[:-1], packed_tensor._offsets[1:])
    # ]

    return packed_tensor, new_tensor_offset

  @classmethod
  def build_from_tensors(cls, tensor_list):
    packed_tensor = cls()
    offset = 0
    for i, tensor in enumerate(tensor_list):
      packed_tensor._meta.append((TensorMeta(tensor.shape, tensor.dtype,
                                             tensor.device)))
      element_size = tensor.element_size()
      num_bytes = element_size * tensor.numel()
      packed_tensor._offsets.append(offset)
      offset += num_bytes
    packed_tensor._offsets.append(offset)

    new_tensor_list = []
    for tensor in tensor_list:
      new_tensor = tensor.view(-1).view(torch.uint8)
      new_tensor_list.append(new_tensor)

    packed_tensor.data = torch.cat(new_tensor_list)
    return packed_tensor

  @classmethod
  def build_from_meta(cls, meta_list: List[TensorMeta]):
    packed_tensor = cls()
    offset = 0
    for i, meta in enumerate(meta_list):
      packed_tensor._meta.append(meta)
      num_elements = reduce(lambda a, b: a * b, meta.shape)
      if isinstance(num_elements, torch.Tensor):
        num_elements = num_elements.item()

      element_size = meta.dtype.itemsize
      num_bytes = num_elements * element_size
      packed_tensor._offsets.append(offset)
      if offset % element_size != 0:
        packed_tensor._offsets[i] += element_size - offset % element_size
        offset += element_size - offset % element_size
      offset += num_bytes

    packed_tensor._offsets.append(offset)
    packed_tensor.data = torch.empty([offset],
                                     dtype=torch.uint8,
                                     device=meta_list[0].device)
    return packed_tensor

  def unpack(self):
    ret = []

    for i, meta in enumerate(self._meta):
      num_elements = reduce(lambda a, b: a * b, meta.shape)
      if isinstance(num_elements, torch.Tensor):
        num_elements = num_elements.item()
      element_size = meta.dtype.itemsize
      num_bytes = num_elements * element_size
      st = self._offsets[i]
      try:
        ret.append(self.data[st:st + num_bytes].view(meta.dtype).view(
            meta.shape))
      except Exception:
        ret.append(self.data[st:st + num_bytes].clone().view(meta.dtype).view(
            meta.shape))
    return ret



# find tensor

def _find_tensors(obj):
    r"""Recursively find all tensors contained in the specified object."""
    if RPC_AVAILABLE and isinstance(obj, RRef):
        # If the current node is the owner of the RRef, unwrap it and try to
        # find Tensors.
        # TODO: Expand to remote RRefs.
        if obj.is_owner():
            return _find_tensors(obj.local_value())
    if isinstance(obj, torch.Tensor):
        return [obj]
    if isinstance(obj, (list, tuple)):
        return itertools.chain.from_iterable(map(_find_tensors, obj))
    if isinstance(obj, dict):
        return itertools.chain.from_iterable(map(_find_tensors, obj.values()))
    if is_dataclass(obj):
        return itertools.chain.from_iterable(
            map(_find_tensors, (getattr(obj, f.name) for f in fields(obj)))
        )

    return []

*** model

# replicate module's state to devices
state_dict = model.state_dict(keep_vars=True)
state_dicts = [state_dict]
for device in devices[1:]:
    new_state_dict = torch.utils._pytree.tree_map(lambda x: x.clone().to(device), state_dict)
    state_dicts.append(new_state_dict)

# call forward in devices separately
ys = []
for t, state_dict in zip(xs, state_dicts):
    output = torch.func.functional_call(model, state_dict, t)
    ys.append(output)

*** hooks

class RemovableHandle:
    r"""
    A handle which provides the capability to remove a hook.

    Args:
        hooks_dict (dict): A dictionary of hooks, indexed by hook ``id``.
        extra_dict (Union[dict, List[dict]]): An additional dictionary or list of
            dictionaries whose keys will be deleted when the same keys are
            removed from ``hooks_dict``.
    """

    id: int
    next_id: int = 0

    def __init__(self, hooks_dict: Any, *, extra_dict: Any = None) -> None:
        self.hooks_dict_ref = weakref.ref(hooks_dict)
        self.id = RemovableHandle.next_id
        RemovableHandle.next_id += 1

        self.extra_dict_ref: Tuple = ()
        if isinstance(extra_dict, dict):
            self.extra_dict_ref = (weakref.ref(extra_dict),)
        elif isinstance(extra_dict, list):
            self.extra_dict_ref = tuple(weakref.ref(d) for d in extra_dict)

    def remove(self) -> None:
        hooks_dict = self.hooks_dict_ref()
        if hooks_dict is not None and self.id in hooks_dict:
            del hooks_dict[self.id]

        for ref in self.extra_dict_ref:
            extra_dict = ref()
            if extra_dict is not None and self.id in extra_dict:
                del extra_dict[self.id]

    def __getstate__(self):
        if self.extra_dict_ref is None:
            return (self.hooks_dict_ref(), self.id)
        else:
            return (self.hooks_dict_ref(), self.id, tuple(ref() for ref in self.extra_dict_ref))

    def __setstate__(self, state) -> None:
        if state[0] is None:
            # create a dead reference
            self.hooks_dict_ref = weakref.ref(OrderedDict())
        else:
            self.hooks_dict_ref = weakref.ref(state[0])
        self.id = state[1]
        RemovableHandle.next_id = max(RemovableHandle.next_id, self.id + 1)

        if len(state) < 3 or state[2] is None:
            self.extra_dict_ref = ()
        else:
            self.extra_dict_ref = tuple(weakref.ref(d) for d in state[2])

    def __enter__(self) -> "RemovableHandle":
        return self

    def __exit__(self, type: Any, value: Any, tb: Any) -> None:
        self.remove()


*** futures

* 在comm_hook上的运用

from typing import Any, Callable, cast

import torch
import torch.distributed as dist


__all__ = [
    "allreduce_hook",
    "fp16_compress_hook",
    "bf16_compress_hook",
    "fp16_compress_wrapper",
    "bf16_compress_wrapper",
]


def _allreduce_fut(
    process_group: dist.ProcessGroup, tensor: torch.Tensor
) -> torch.futures.Future[torch.Tensor]:
    """Average the input gradient tensor by allreduce and returns a future."""
    group_to_use = process_group if process_group is not None else dist.group.WORLD

    # Apply the division first to avoid overflow, especially for FP16.
    tensor.div_(group_to_use.size())

    return (
        dist.all_reduce(tensor, group=group_to_use, async_op=True)
        .get_future()
        .then(lambda fut: fut.value()[0])
    )


def allreduce_hook(
    process_group: dist.ProcessGroup, bucket: dist.GradBucket
) -> torch.futures.Future[torch.Tensor]:
    return _allreduce_fut(process_group, bucket.buffer())


def _compress_hook(
    dtype: torch.dtype,
    process_group: dist.ProcessGroup,
    bucket: dist.GradBucket,
) -> torch.futures.Future[torch.Tensor]:
    group_to_use = process_group if process_group is not None else dist.group.WORLD
    world_size = group_to_use.size()

    buffer = (
        cast(tuple[torch.Tensor, ...], bucket)[0]
        if isinstance(bucket, tuple)
        else bucket.buffer()
    )
    compressed_tensor = buffer.to(dtype).div_(world_size)

    def decompress(fut):
        decompressed_tensor = buffer
        # Decompress in place to reduce the peak memory.
        # See: https://github.com/pytorch/pytorch/issues/45968
        value = fut if isinstance(fut, torch.Tensor) else fut.value()[0]
        decompressed_tensor.copy_(value)
        return decompressed_tensor

    if torch.compiler.is_compiling():
        grad = dist._functional_collectives.all_reduce(
            compressed_tensor, "sum", group_to_use
        )
        return decompress(grad)
    else:
        fut = dist.all_reduce(
            compressed_tensor, group=group_to_use, async_op=True
        ).get_future()
        return fut.then(decompress)


def bf16_compress_hook(
    process_group: dist.ProcessGroup,
    bucket: dist.GradBucket,
) -> torch.futures.Future[torch.Tensor]:
    return _compress_hook(torch.bfloat16, process_group, bucket)