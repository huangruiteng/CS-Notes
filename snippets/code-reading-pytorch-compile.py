*** intro

tutorial: https://pytorch.org/tutorials/intermediate/torch_compile_tutorial.html
API: https://docs.pytorch.org/docs/stable/generated/torch.compile.html#torch.compile
trouble-shooting: https://docs.pytorch.org/docs/main/torch.compiler_troubleshooting.html

torch.compile = fusion + cudagraph
- max-autotune和reduce-overhead都用了cudagraph
- default没开，因为有slight memory overhead
- cuda-graph的基础假设是static shape，所以dynamic shape需要cache很多graph



*** Debugging

TORCH_COMPILE_DEBUG_DIR=~/torch_compile_logs TORCH_LOGS=recompiles,+dynamo,inductor,guards,graph_breaks,output_code python model.py

TORCH_LOGS=graph_breaks,output_code


*** depyf: Debugging Tool

https://zhuanlan.zhihu.com/p/730714110


*** 性能调优

fullgraph
dynamic=False
mode='max-autotune'


config.coordinate_descent_tuning = True
config.cache_size_limit = 16


*** fusion

**** manual fusion

fused_model = torch.nn.utils.fusion.fuse_linear_bn_eval(model.linear, model.bn)

**** fusion精度问题

fma can cause drastically worse precision in torch.compile/Triton
- https://github.com/pytorch/pytorch/issues/122260

[inductor] Disable fp contraction and add option to use precise division #115435
- https://github.com/pytorch/pytorch/pull/115435


*** mm.py

部分参考 「code-reading-pytorch-quantization.py」



*** TorchDynamo DDPOptimizer

DDP works with TorchDynamo. 
When used with TorchDynamo, apply the DDP model wrapper before compiling the model,
such that torchdynamo can apply DDPOptimizer (graph-break optimizations) based on DDP bucket sizes. 

https://pytorch.org/docs/main/notes/ddp.html#torchdynamo-ddpoptimizer

ddp_model = DDP(model, device_ids=[rank])
ddp_model = torch.compile(ddp_model)

*** optimizer

optimizer = torch.optim.AdamW(params)

@torch.compile(fullgraph=False)
def compiled_step():
    optimizer.step()


DDP’s performance advantage comes from overlapping allreduce collectives with computations during backwards.
AotAutograd prevents this overlap when used with TorchDynamo for compiling a whole forward and whole backward graph,
because allreduce ops are launched by autograd hooks _after_ the whole optimized backwards computation finishes.

TorchDynamo’s DDPOptimizer helps by breaking the forward graph at the logical boundaries of DDP’s allreduce buckets during backwards.
Note: the goal is to break the graph during backwards,
and the simplest implementation is to break the forward graphs and then call AotAutograd and compilation on each section.
This allows DDP’s allreduce hooks to fire in-between sections of backwards, and schedule communications to overlap with compute.

相关资料：
https://dev-discuss.pytorch.org/t/torchdynamo-update-9-making-ddp-work-with-torchdynamo/860
torch/_dynamo/optimizations/distributed.py


Debug DDPOptimizer：
set TORCH_LOGS=’ddp_graphs’ for full graph dumps.
For logs without graphs, add any of ‘dynamo’, ‘distributed’, or ‘dist_ddp’ to TORCH_LOGS (for basic info about bucket boundaries).
To disable DDPOptimizer, set torch._dynamo.config.optimize_ddp=False. DDP and TorchDynamo should still work correctly without DDPOptimizer, but with performance degradation.


*** nested/jagged tensor


*** Examples: torch.compile generate Triton Kernel

* compile_square.py

import torch
compiled_square = torch.compile(torch.square)
x = torch.randn(10, 10).cuda()
result = compiled_square(x)

TORCH_LOGS="output_code" python compile_square.py
TORCH_LOGS="inductor"


@torch.compile
def square_2(a):
  a = torch.square(a)
  a = torch.square(a)
  return a

* fuse matmul + relu

- triton_poi_fused_relu_0
  - fuse ReLU(xW^T + b)，把add和relu fuse起来了
  - reinterpret_tensor: 按新的stride解释

