Great at composing “simple” operations together
○ Fused_int_mm_mul
○ SAM flash attention
■ https://github.com/facebookresearch/segment-anything/blob/main/segmen
t_anything/modeling/image_encoder.py#L358
■ https://github.com/pytorch-labs/segment-anything-fast/blob/main/segment
_anything_fast/flash_4.py#L13

import numpy as np
import triton
import triton.language as tl
import torch

np.set_printoptions(precision=2, linewidth=140)
torch.set_printoptions(precision=2, linewidth=140, sci_mode=False)
np.seterr(all='warn')


from gpu_kernel_utils import cdiv, breakpoint_if, print_if, check_tensors_gpu_ready, get_1d_offset, get_2d_offset, \
  get_1d_mask, get_2d_mask

### backward用atomic_add，因为可能多个thread可能更新同一行
- atomic_add不支持bf16: https://github.com/pytorch/pytorch/issues/97016

@triton.jit
def index_select_bwd(grad_outputs, indices, grad_unique_values, num_rows: int,
                     num_cols: int, num_indices: int, BLOCK_SIZE: tl.constexpr):
  pid = tl.program_id(axis=0)
  off_m = get_1d_offset(BLOCK_SIZE, pid)
  indices = tl.load(indices + off_m, mask=off_m < num_indices, other=-1)
  row_mask = (indices >= 0) & (indices < num_rows) & (off_m < num_indices)

  for i in range(num_cols):
    block_grad_unique_values = tl.load(grad_outputs +
                                       off_m[:, None] * num_cols + i,
                                       mask=row_mask[:, None])
    tl.atomic_add(grad_unique_values + indices[:, None] * num_cols + i,
                  val=block_grad_unique_values,
                  mask=row_mask[:, None])

### 最简单的copy kernel、rgb2gray kernel

# # This is a normal python function, which launches the triton kernels
def copy(x, bs, kernel_fn):
  z = torch.zeros_like(x).cuda()
  check_tensors_gpu_ready(x, z)
  n = x.numel()
  n_blocks = cdiv(n, bs)
  grid = (n_blocks,)  # how many blocks do we have? can be 1d/2d/3d-tuple or function returning 1d/2d/3d-tuple

  # launch grid!
  # - kernel_fn is the triton kernel, which we write below
  # - grid is the grid we constructed above
  # - x,z,n,bs are paramters that are passed into each kernel function
  kernel_fn[grid](x, z, n, bs)

  return z


# # This is the triton kernel:

# The triton.jit decorator takes a python function and turns it into a triton kernel, which is run on the GPU.
# Inside this function only a subset of all python ops are allowed.
# E.g., when NOT simulating, we can't print or use breakpoints, as these don't exist on the GPU.
@triton.jit
# When we pass torch tensors, they are automatically converted into a pointer to their first value
# E.g., above we passed x, but here we receive x_ptr
def _copy(x_ptr, z_ptr, n, bs: tl.constexpr):
  pid = tl.program_id(0)
  offs = pid * bs + tl.arange(0, bs)
  mask = offs < n
  x = tl.load(x_ptr + offs, mask)
  tl.store(z_ptr + offs, x, mask)
  # print_if(f'pid = {pid} | offs = {offs}, mask = {mask}, x = {x}', '')


x = torch.tensor([1, 2, 3, 4, 5, 6]).cuda()
y = torch.tensor([0, 1, 0, 1, 0, 1]).cuda()
z = copy(x, bs=2, kernel_fn=_copy)

import matplotlib.pyplot as plt
from urllib.request import urlretrieve
from pathlib import Path
import torchvision as tv
import torchvision.transforms.functional as tvf
from torchvision import io


def show_img(x, figsize=(4, 3), **kwargs):
  plt.figure(figsize=figsize)
  plt.axis('off')
  if len(x.shape) == 3: x = x.permute(1, 2, 0)  # CHW -> HWC
  plt.imshow(x.cpu(), **kwargs)


@triton.jit
def rgb2grey_k(x_ptr, out_ptr, h, w, bs0: tl.constexpr, bs1: tl.constexpr):
  pid_0 = tl.program_id(0)
  pid_1 = tl.program_id(1)

  offs_0 = pid_0 * bs0 + tl.arange(0, bs0)  # 1d vector
  offs_1 = pid_1 * bs1 + tl.arange(0, bs1)  # 1d vector

  # Weirdness: None-slicing currently doesn't work when simulating on cpu. Use tl.expand_dim instead.
  # offs = w * tl.expand_dims(offs_0, 1) + tl.expand_dims(offs_1, 0)
  offs = w * offs_0[:, None] + offs_1[None, :]  # 2d matrix! - we multiply first offset by width, see image above

  mask_0 = offs_0 < h  # 1d vector
  mask_1 = offs_1 < w  # 1d vector

  # mask = tl.expand_dims(mask_0, 1) & tl.expand_dims(mask_1, 0)
  mask = mask_0[:, None] & mask_1[None,
                           :]  # 2d matrix! - data musn't go out of bounds along either axis, therefore `logical and` of the individual masks

  r = tl.load(x_ptr + 0 * h * w + offs, mask=mask)
  g = tl.load(x_ptr + 1 * h * w + offs, mask=mask)
  b = tl.load(x_ptr + 2 * h * w + offs, mask=mask)

  # Weirdness: multiplying float with uint vectors fails when simulating on cpu
  out = 0.2989 * r + 0.5870 * g + 0.1140 * b  # don't worry why it's these 3 numbers we're multiplying with

  tl.store(out_ptr + offs, out, mask=mask)


def rgb2grey(x, bs):
  c, h, w = x.shape
  out = torch.empty((h, w), dtype=x.dtype, device=x.device)

  # grid can be a function returning a 1d/2d/3d-tuple
  # (having a grid function is not more useful than a grid tuple in this case, but will be below when benchmarking & auto-tuning)
  grid = lambda meta: (cdiv(h, meta['bs0']), cdiv(w, meta['bs1']))

  rgb2grey_k[grid](x, out, h, w, bs0=bs[0], bs1=bs[1])  # all kwargs are passed into grid function
  return out.view(h, w)


url = 'https://upload.wikimedia.org/wikipedia/commons/thumb/4/43/Cute_dog.jpg/1600px-Cute_dog.jpg?20140729055059'
path_img = Path('puppy.jpg')
if not path_img.exists(): urlretrieve(url, path_img)
img = io.read_image('puppy.jpg')
print(img.shape)
img[:2, :3, :4]

img = tvf.resize(img, 150, antialias=True)
ch, h, w = img.shape
ch, h, w, h * w

show_img(img)
grey_img = rgb2grey(img.to('cuda'), bs=(32, 32)).to('cpu')
show_img(grey_img, cmap='gray')

import os

# os.environ["TRITON_INTERPRET"] = "1"