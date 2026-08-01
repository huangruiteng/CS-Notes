pytorch quant的计划和分析：
https://dev-discuss.pytorch.org/t/clarification-of-pytorch-quantization-flow-support-in-pytorch-and-torchao/2809/2


### 也参考code-reading-xxx


### AMP

参考 pytorch-amp.py

### quantize optimizers DEMO


import torch
from torch import Tensor

lr = 1e-4
momentum = 0.9


def sgd(p: Tensor, grad: Tensor, momentum_buffer: Tensor, lr: float, momentum: float):
  new_momentum_buffer = momentum_buffer * momentum + grad
  new_p = p - lr * new_momentum_buffer

  momentum_buffer.copy_(new_momentum_buffer)
  p.copy_(new_p)


def sgd_bf16(p: Tensor, grad: Tensor, momentum_buffer: Tensor, lr: float, momentum: float):
  # upcast to FP32 for accurate calculations
  new_momentum_buffer = momentum_buffer.float() * momentum + grad
  new_p = p - lr * new_momentum_buffer

  momentum_buffer.copy_(new_momentum_buffer)  # implicit downcast to BF16
  p.copy_(new_p)


def sgd_fp8(p: Tensor, grad: Tensor, momentum_buffer: Tensor, lr: float, momentum: float):
  # upcast to FP32 for accurate calculations
  new_momentum_buffer = momentum_buffer.float() * momentum + grad
  new_p = p - lr * new_momentum_buffer

  momentum_buffer.copy_(new_momentum_buffer)  # implicit downcast to FP8
  p.copy_(new_p)


torch.manual_seed(2024)
p = torch.randn(4, 4)
momentum_buffer = torch.randn(4, 4)

for _ in range(5):
  grad = torch.randn(4, 4)
  sgd(p, grad, momentum_buffer, lr, momentum)
print(p)

torch.manual_seed(2024)
p = torch.randn(4, 4)
momentum_buffer = torch.randn(4, 4).bfloat16()

for _ in range(5):
  grad = torch.randn(4, 4)
  sgd_bf16(p, grad, momentum_buffer, lr, momentum)
print(p)

torch.manual_seed(2024)
p = torch.randn(4, 4)
momentum_buffer = torch.randn(4, 4).to(torch.float8_e4m3fn)

for _ in range(5):
  grad = torch.randn(4, 4)
  sgd_fp8(p, grad, momentum_buffer, lr, momentum)
print(p)

DTYPE = torch.float8_e4m3fn


def quantize_fp8(x: Tensor):
  scale = x.abs().max() / torch.finfo(DTYPE).max
  quantized_x = (x / scale.clip(1e-12)).to(DTYPE)
  return quantized_x, scale


def sgd_scaled_fp8(
    p: Tensor,
    grad: Tensor,
    momentum_buffer: Tensor,
    momentum_buffer_scale: Tensor,
    lr: float,
    momentum: float,
):
  # upcast to FP32 for accurate calculations
  new_momentum_buffer = momentum_buffer.float() * momentum_buffer_scale * momentum + grad
  new_p = p - lr * new_momentum_buffer

  new_momentum_buffer_quantized, new_momentum_buffer_scale = quantize_fp8(new_momentum_buffer)
  momentum_buffer.copy_(new_momentum_buffer_quantized)
  momentum_buffer_scale.copy_(new_momentum_buffer_scale)
  p.copy_(new_p)


torch.manual_seed(2024)
p = torch.randn(4, 4)
grad = torch.randn(4, 4)
momentum_buffer = torch.randn(4, 4)
momentum_buffer, momentum_buffer_scale = quantize_fp8(momentum_buffer)

for _ in range(5):
  grad = torch.randn(4, 4)
  sgd_scaled_fp8(p, grad, momentum_buffer, momentum_buffer_scale, lr, momentum)
print(p)

# INT8 + small fraction

x = torch.tensor(10, dtype=torch.int8)
N = 100
for _ in range(N):
  x.copy_(x + 0.2)

print(f"Expected output: {10 + 0.2 * N}")
print(f"INT8 No SR output: {x}")


def sr(x: torch.Tensor):
  rand = torch.rand(x.shape, device=x.device)  # get a random number [0,1)
  return torch.where(rand < x - x.floor(), x.floor() + 1, x.floor())


x = torch.tensor(10, dtype=torch.int8)
for _ in range(N):
  x.copy_(sr(x.float() + 0.2))

print(f"INT8 SR Actual output: {x}")

x = torch.tensor(200, dtype=torch.bfloat16)
N = 100
for _ in range(N):
  x.copy_(x + 1)

print(f"BF16 Expected output: {200 + N}")
print(f"BF16 No SR output: {x}")


def bf16_sr(x: torch.Tensor):  # x is FP32
  x_i32 = x.view(torch.int32)  # cast to INT32 to do bit manipulation
  x_floor = x_i32 & 0xFFFF0000  # truncate the least significant 16 bits

  # this will generate 31 random bits. we only need 16
  rand = torch.empty(x.shape, dtype=torch.int32).random_()
  rand = rand & 0xFFFF

  out = torch.where(rand < (x_i32 & 0xFFFF), x_floor + 0x10000, x_floor)
  return out.view(torch.float32).bfloat16()


x = torch.tensor(200, dtype=torch.bfloat16)
N = 100
for _ in range(N):
  x.copy_(bf16_sr(x.float() + 1))

print(f"BF16 SR output: {x}")
