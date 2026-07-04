- Intro: https://towardsdatascience.com/the-mystery-behind-the-pytorch-automatic-mixed-precision-library-d9386e4b787e/

- https://pytorch.org/tutorials/recipes/recipes/amp_recipe.html
- https://pytorch.org/docs/stable/notes/amp_examples.html
- https://pytorch.org/docs/stable/amp.html
- https://www.digitalocean.com/community/tutorials/automatic-mixed-precision-using-pytorch
- 源码阅读：https://zhuanlan.zhihu.com/p/348554267
- NVIDIA https://www.cs.toronto.edu/ecosystem/documents/AMP-Tutorial.pdf


- 核心API：torch.autocast and torch.cuda.amp.GradScaler

- 支持的CUDA op：https://pytorch.org/docs/stable/amp.html#autocast-op-reference

 Most matrix multiplication, convolutions, and linear activations are fully covered by the amp.autocast,
 however, for reduction/sum, softmax, and loss calculations, the calculations are still performed in FP32
 as they are more sensitive to data range and precision.

 CUDA Ops that can autocast to float16
__matmul__, addbmm, addmm, addmv, addr, baddbmm, bmm, chain_matmul, multi_dot, conv1d, 
conv2d, conv3d, conv_transpose1d, conv_transpose2d, conv_transpose3d, GRUCell, linear, LSTMCell, matmul, mm, mv, prelu, RNNCell

- loss scaling
 
* 如何选择loss scale
 - Choose a value so that its product with the maximum absolute gradient value is below 65,504 (the maximum value representable in FP16)
 - dynamic: https://docs.nvidia.com/deeplearning/performance/mixed-precision-training/index.html#scalefactor

scaler = torch.cuda.amp.GradScaler()
# start your training code
# ...
with torch.autocast(device_type="cuda"):
  # training code

# wrapping loss and optimizer
scaler.scale(loss).backward()
scaler.step(optimizer)

scaler.update()

mixed precision training doesn’t really resolve the GPU memory issue if the model weight size is much larger than the data batch.
For one thing, only certain layers of the model is casted into FP16 while the rest are still calculated in FP32;
second, weight update need FP32 copies, which still takes much GPU memory;
third, parameters from optimizers like Adam takes much GPU memory during training and the mixed precision training keeps the optimizer parameters unchanged.

* 精度debug
- advanced use cases
- https://pytorch.org/docs/stable/amp.html#prefer-binary-cross-entropy-with-logits-over-binary-cross-entropy
   In autocast-enabled regions, the forward input may be float16, which means the backward gradient must be representable in float16
- Disable autocast or GradScaler individually (by passing enabled=False to their constructor) and see if infs/NaNs persist.
- https://blog.csdn.net/qq_40243750/article/details/128207067


with torch.autocast(device_type="cuda"):
    e_float16 = torch.mm(a_float32, b_float32)
    with torch.autocast(device_type="cuda", enabled=False):
        # Calls e_float16.float() to ensure float32 execution
        # (necessary because e_float16 was created in an autocasted region)
        f_float32 = torch.mm(c_float32, e_float16.float())

    # No manual casts are required when re-entering the autocast-enabled region.
    # torch.mm again runs in float16 and produces float16 output, regardless of input types.
    g_float16 = torch.mm(d_float32, f_float32)



* Advanced use cases
- https://pytorch.org/docs/stable/notes/amp_examples.html
Gradient accumulation

Gradient penalty/double backward

Networks with multiple models, optimizers, or losses

Multiple GPUs (torch.nn.DataParallel or torch.nn.parallel.DistributedDataParallel)
(DP时需要@autocast修饰大的forward函数)

Custom autograd functions (subclasses of torch.autograd.Function)


手写的kernel指定amp类型，用custom_fwd


* 实现AMP Kernel
https://pytorch.org/tutorials/advanced/dispatcher.html#autocast

// Autocast-specific helper functions
#include <ATen/autocast_mode.h>

Tensor mymatmul_autocast(const Tensor& self, const Tensor& other) {
  c10::impl::ExcludeDispatchKeyGuard no_autocast(c10::DispatchKey::Autocast);
  return mymatmul(at::autocast::cached_cast(at::kHalf, self),
                  at::autocast::cached_cast(at::kHalf, other));
}

TORCH_LIBRARY_IMPL(myops, Autocast, m) {
  m.impl("mymatmul", mymatmul_autocast);
}



*** amp ctx


import torch
from contextlib import nullcontext

# todo(huangruiteng):
# 支持scalar状态的load&save


def nan_hook(self, inp, out):
  """
    Check for NaN inputs or outputs at each layer in the model
    Usage:
        # forward hook
        for submodule in model.modules():
            submodule.register_forward_hook(nan_hook)
    """

  def _check_nan(x):
    if isinstance(x, torch.Tensor):
      return torch.isnan(x).any()
    elif isinstance(x, (list, tuple)):
      return any(_check_nan(item) for item in x)
    return False

  outputs = isinstance(out, tuple) and out or [out]
  inputs = isinstance(inp, tuple) and inp or [inp]
  layer = self.__class__.__name__

  for i, inp in enumerate(inputs):
    if inp is not None and _check_nan(inp):
      assert False, f'Found NaN input at index: {i} in layer: {layer}, inputs {inputs}'

  for i, out in enumerate(outputs):
    if out is not None and _check_nan(out):
      assert False, f'Found NaN output at index: {i} in layer: {layer}, inputs {inputs}'


class bcolors:
  HEADER = '\033[95m'
  OKBLUE = '\033[94m'
  OKGREEN = '\033[92m'  # 绿色
  WARNING = '\033[93m'
  FAIL = '\033[91m'  # 红色
  ENDC = '\033[0m'
  BOLD = '\033[1m'
  UNDERLINE = '\033[4m'


class AmpContext(object):

  def __init__(self,
               model: torch.nn.Module,
               optimizer: torch.optim.Optimizer,
               dtype: torch.dtype = torch.bfloat16,
               grad_clip: float = 1000.0,
               enabled: bool = True,
               debug_fwd: bool = False,
               debug_bwd: bool = False):
    self._model = model
    self._optim = optimizer
    self._dtype = dtype
    self._grad_clip = grad_clip
    self._device = str(model.device).split(':')[0]
    self._ctx = None
    self._scaler = None
    self._enabled = enabled
    self._debug_fwd = debug_fwd
    self._debug = self._debug_fwd or debug_bwd
    if debug_bwd:
      torch.autograd.set_detect_anomaly(True)

    self._entered = False
    self._nan_found = False

    if self._enabled and self._device != "cpu":
      for name, module in self._model.named_modules():
        if isinstance(module, torch.nn.Linear):
          if module.in_features % 8 != 0 or module.out_features % 8 != 0:
            print(
                f"{bcolors.FAIL}Warning: Linear layer '{name}' has dimensions ({module.in_features}, {module.out_features}) "
                f"not divisible by 8, TensorCore may not work efficiently{bcolors.ENDC}"
            )

  def get(self):
    return self

  def __enter__(self):
    # autocast上下文只能包含网络的前向过程(包括loss的计算), 不能包含反向传播, BP的op会自动使用和前向op相同的类型。
    if self._ctx is None:
      if self._device == "cpu":
        self._ctx = nullcontext()
      else:
        torch.cuda.synchronize()
        if not self._model.training:
          self._ctx = nullcontext()
          for p in self._model.parameters():
            p.data = p.data.float()
            if p.grad:
              p.grad.data = p.grad.data.float()
        else:
          self._ctx = torch.autocast(device_type=self._device,
                                     dtype=self._dtype,
                                     enabled=self._enabled)
          self._scaler = torch.amp.GradScaler('cuda', enabled=self._enabled)
    self._ctx.__enter__()
    self._entered = True
    return self

  def __exit__(self, exc_type, exc_val, exc_tb):
    if self._ctx is not None and self._entered:
      self._ctx.__exit__(exc_type, exc_val, exc_tb)
      self._entered = False

  def zero_grad(self):
    self._optim.zero_grad(set_to_none=True)

  def backward(self, losses: list[torch.Tensor] | torch.Tensor, step: int):
    self.__exit__(None, None, None)

    if isinstance(losses, (list | tuple)):
      losses = sum(losses)
    assert isinstance(losses, torch.Tensor)
    if torch.isnan(losses):
      if not self._nan_found:
        print(f"{bcolors.FAIL}LOSS NAN FOUND{bcolors.ENDC}, step: {step}")
        self._nan_found = True
        for submodule in self._model.modules():
          submodule.register_forward_hook(nan_hook)
      if not self._debug_fwd:
        raise RuntimeError("LOSS NAN FOUND")

    if self._scaler is not None:
      self._scaler.scale(losses).backward()
    else:
      losses.backward()
    if torch.cuda.is_available():
      torch.cuda.empty_cache()

    # debug model parameters
    if self._debug:
      for name, param in self._model.named_parameters():
        if param is not None and not param.is_sparse:
          has_nan = torch.isnan(param).any()
          if has_nan:
            color = bcolors.FAIL
          else:
            color = bcolors.OKGREEN
          if has_nan or self._debug:
            print(
                f'{color}value {name}: {param.min().item():.3e} ~ {param.max().item():.3e}\033[0m'
            )
        if param.grad is not None and not param.grad.is_sparse:  # emb SparseTensor不支持max和min方法
          has_nan = torch.isnan(param.grad).any()
          if has_nan:
            color = bcolors.FAIL
          else:
            color = bcolors.OKGREEN
          if has_nan or self._debug:
            print(
                f'{color}grad {name}: {param.grad.min().item():.3e} ~ {param.grad.max().item():.3e}\033[0m'
            )

  def step(self):
    self.__exit__(None, None, None)
    if self._scaler is not None:  # unscale before grad clip
      self._scaler.unscale_(self._optim)
    if self._grad_clip != 0.0:
      dense_params = (p for n, p in self._model.named_parameters()
                      if p.grad is not None and not p.grad.is_sparse)
      dense_params_iter = list(dense_params) if any(
          1 for _ in dense_params) else []
      torch.nn.utils.clip_grad_norm_(dense_params_iter, max_norm=self._grad_clip, norm_type=2)
    if self._scaler is not None:
      self._scaler.step(self._optim)
      self._scaler.update()
    else:
      self._optim.step()
    if self._debug:
      print(f"AMP Debug Scaler State: {self._scaler.state_dict()}")



### example

import torch, time, gc
import numpy as np
import random, os

# Timing utilities
start_time = None


def start_timer():
  global start_time
  gc.collect()
  torch.cuda.empty_cache()
  torch.cuda.reset_max_memory_allocated()
  torch.cuda.synchronize()
  start_time = time.time()


def end_timer_and_print(local_msg):
  torch.cuda.synchronize()
  end_time = time.time()
  print("\n" + local_msg)
  print("Total execution time = {:.3f} sec".format(end_time - start_time))
  print("Max memory used by tensors = {} bytes".format(
      torch.cuda.max_memory_allocated()))

def set_seed(seed: int = 37) -> None:
  np.random.seed(seed)
  random.seed(seed)
  torch.manual_seed(seed)  # 适用于所有PyTorch后端，包括CPU和所有CUDA设备

  os.environ["PYTHONHASHSEED"] = str(seed)
  print(f"设置随机数种子为{seed}")

def make_model(in_size, out_size, num_layers):
  layers = []
  for _ in range(num_layers - 1):
    layers.append(torch.nn.Linear(in_size, in_size))
    layers.append(torch.nn.ReLU())
  layers.append(torch.nn.Linear(in_size, out_size))
  return torch.nn.Sequential(*tuple(layers)).cuda()

if __name__ == "__main__":
  set_seed()
  batch_size = 512  # Try, for example, 128, 256, 513.
  in_size = 4096
  out_size = 4096
  num_layers = 3
  num_batches = 50
  epochs = 3

  device = 'cuda' if torch.cuda.is_available() else 'cpu'
  torch.set_default_device(device)

  # Creates data in default precision.
  # The same data is used for both default and mixed precision trials below.
  # You don't need to manually change inputs' ``dtype`` when enabling mixed precision.
  data = [torch.randn(batch_size, in_size) for _ in range(num_batches)]
  targets = [torch.randn(batch_size, out_size) for _ in range(num_batches)]

  loss_fn = torch.nn.MSELoss().cuda()

  set_seed() # 必须在这里，原因是前面调用了randn
  # warm up
  net = make_model(in_size, out_size, num_layers)
  opt = torch.optim.SGD(net.parameters(), lr=0.001)
  for epoch in range(epochs):
    for input, target in zip(data, targets):
      output = net(input)
      loss = loss_fn(output, target)
      loss.backward()
      opt.step()
      opt.zero_grad(set_to_none=True)
  fp32_result_1 = net(data[0])

  set_seed()
  net = make_model(in_size, out_size, num_layers)
  opt = torch.optim.SGD(net.parameters(), lr=0.001)
  start_timer()
  for epoch in range(epochs):
    for input, target in zip(data, targets):
      output = net(input)
      loss = loss_fn(output, target)
      loss.backward()
      opt.step()
      opt.zero_grad(set_to_none=True)
  end_timer_and_print("Default precision:")
  fp32_result = net(data[0])

  if torch.allclose(fp32_result, fp32_result_1, atol=5e-2, rtol=0):
    print("✅ Default precision match")
  else:
    print("❌ Default precision differ")
    print(fp32_result, fp32_result_1)

  set_seed()
  net = make_model(in_size, out_size, num_layers)
  opt = torch.optim.SGD(net.parameters(), lr=0.001)

  # Constructs a ``scaler`` once, at the beginning of the convergence run, using default arguments.
  # If your network fails to converge with default ``GradScaler`` arguments, please file an issue.
  # The same ``GradScaler`` instance should be used for the entire convergence run.
  # If you perform multiple convergence runs in the same script, each run should use
  # a dedicated fresh ``GradScaler`` instance. ``GradScaler`` instances are lightweight.
  scaler = torch.amp.GradScaler("cuda")

  start_timer()
  for epoch in range(epochs):
    for input, target in zip(data, targets):
      with torch.autocast(device_type=device, dtype=torch.float16):
        output = net(input)
        # output is float16 because linear layers ``autocast`` to float16.
        assert output.dtype is torch.float16
        loss = loss_fn(output, target)
        # loss is float32 because ``mse_loss`` layers ``autocast`` to float32.
        assert loss.dtype is torch.float32
      # Exits ``autocast`` before backward().
      # Backward passes under ``autocast`` are not recommended.
      # Backward ops run in the same ``dtype`` ``autocast`` chose for corresponding forward ops.
      # Scales loss. Calls ``backward()`` on scaled loss to create scaled gradients.
      scaler.scale(loss).backward()
      scaler.unscale_(opt)
      # torch.nn.utils.clip_grad_norm_(net.parameters(), max_norm=0.1)
      # otherwise, optimizer.step() is skipped.
      scaler.step(opt)
      # Updates the scale for next iteration.
      scaler.update()
      # checkpoint = {"model": net.state_dict(),
      #               "optimizer": opt.state_dict(),
      #               "scaler": scaler.state_dict()}
      opt.zero_grad(set_to_none=True)
  end_timer_and_print("Mixed precision:")
  fp16_result = net(data[0]).to(torch.float32)

  if torch.allclose(fp32_result, fp16_result, atol=5e-2, rtol=0):
    print("✅ Default and Mixed precision match")
  else:
    print("❌ Default and Mixed precision differ")
    print(fp32_result, fp16_result)


### amp examples

https://pytorch.org/docs/stable/notes/amp_examples.html

### grad acc

scaler = GradScaler()

for epoch in epochs:
    for i, (input, target) in enumerate(data):
        with autocast(device_type='cuda', dtype=torch.float16):
            output = model(input)
            loss = loss_fn(output, target)
            loss = loss / iters_to_accumulate

        # Accumulates scaled gradients.
        scaler.scale(loss).backward()

        if (i + 1) % iters_to_accumulate == 0:
            # may unscale_ here if desired (e.g., to allow clipping unscaled gradients)

            scaler.step(optimizer)
            scaler.update()
            optimizer.zero_grad()

### grad penalty

scaler = GradScaler()

for epoch in epochs:
    for input, target in data:
        optimizer.zero_grad()
        with autocast(device_type='cuda', dtype=torch.float16):
            output = model(input)
            loss = loss_fn(output, target)

        # Scales the loss for autograd.grad's backward pass, producing scaled_grad_params
        scaled_grad_params = torch.autograd.grad(outputs=scaler.scale(loss),
                                                 inputs=model.parameters(),
                                                 create_graph=True)

        # Creates unscaled grad_params before computing the penalty. scaled_grad_params are
        # not owned by any optimizer, so ordinary division is used instead of scaler.unscale_:
        inv_scale = 1./scaler.get_scale()
        grad_params = [p * inv_scale for p in scaled_grad_params]

        # Computes the penalty term and adds it to the loss
        with autocast(device_type='cuda', dtype=torch.float16):
            grad_norm = 0
            for grad in grad_params:
                grad_norm += grad.pow(2).sum()
            grad_norm = grad_norm.sqrt()
            loss = loss + grad_norm

        # Applies scaling to the backward call as usual.
        # Accumulates leaf gradients that are correctly scaled.
        scaler.scale(loss).backward()

        # may unscale_ here if desired (e.g., to allow clipping unscaled gradients)

        # step() and update() proceed as usual.
        scaler.step(optimizer)
        scaler.update()

### multi model

Each optimizer checks its gradients for infs/NaNs and makes an independent decision whether or not to skip the step. 
This may result in one optimizer skipping the step while the other one does not.
 Since step skipping occurs rarely (every several hundred iterations) this should not impede convergence. 


scaler = torch.amp.GradScaler()

for epoch in epochs:
    for input, target in data:
        optimizer0.zero_grad()
        optimizer1.zero_grad()
        with autocast(device_type='cuda', dtype=torch.float16):
            output0 = model0(input)
            output1 = model1(input)
            loss0 = loss_fn(2 * output0 + 3 * output1, target)
            loss1 = loss_fn(3 * output0 - 5 * output1, target)

        # (retain_graph here is unrelated to amp, it's present because in this
        # example, both backward() calls share some sections of graph.)
        scaler.scale(loss0).backward(retain_graph=True)
        scaler.scale(loss1).backward()

        # You can choose which optimizers receive explicit unscaling, if you
        # want to inspect or modify the gradients of the params they own.
        scaler.unscale_(optimizer0)

        scaler.step(optimizer0)
        scaler.step(optimizer1)

        scaler.update()

# DDP

autocase在forward方法内即可

model = MyModel()
dp_model = nn.DataParallel(model)

# Sets autocast in the main thread
with autocast(device_type='cuda', dtype=torch.float16):
    # dp_model's internal threads will autocast.
    output = dp_model(input)
    # loss_fn also autocast
    loss = loss_fn(output)


### Autocast and Custom Autograd Functions

If your network uses custom autograd functions (subclasses of torch.autograd.Function), changes are required for autocast compatibility if any function

takes multiple floating-point Tensor inputs,

wraps any autocastable op (see the Autocast Op Reference), or

requires a particular dtype (for example, if it wraps CUDA extensions that were only compiled for dtype).

with autocast(device_type='cuda', dtype=torch.float16):
    ...
    with autocast(device_type='cuda', dtype=torch.float16, enabled=False):
        output = imported_function(input1.float(), input2.float())

class MyMM(torch.autograd.Function):
    @staticmethod
    @custom_fwd
    def forward(ctx, a, b):
        ctx.save_for_backward(a, b)
        return a.mm(b)
    @staticmethod
    @custom_bwd
    def backward(ctx, grad):
        a, b = ctx.saved_tensors
        return grad.mm(b.t()), a.t().mm(grad)