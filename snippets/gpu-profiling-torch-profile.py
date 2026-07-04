*** 打开文件
https://ui.perfetto.dev/
chrome://tracing
https://pytorch.org/memory_viz

*** example

model = torchvision.models.resnet18().cuda()
inputs = torch.randn(5, 3, 224, 224, device="cuda")

for _ in range(5):
  model(inputs)

from torch.profiler import profile, record_function, ProfilerActivity
with profile(activities=[ProfilerActivity.CPU, ProfilerActivity.CUDA], profile_memory=True) as prof:
  with record_function("model_inference"):
    model(inputs)


*** torch.profile

self.profiler_schedule = torch.profiler.schedule(wait=3,
                                                   warmup=3,
                                                   active=5,
                                                   repeat=1)
self.trace_profiler = torch.profiler.profile(
          activities=[
              torch.profiler.ProfilerActivity.CPU,
              torch.profiler.ProfilerActivity.CUDA
          ],
          schedule=self.profiler_schedule,
          on_trace_ready=torch.profiler.tensorboard_trace_handler(
              dir_name=self.trace_log_dir,
              worker_name=f"trace_{self.rank}_{self.task_id}",
              use_gzip=True),
          record_shapes=True,
          profile_memory=True,
          with_stack=True,
          with_flops=True,
          with_modules=True)

# TODO: on_trace_ready=trace_handler

def trace_handler(prof):
    print(prof.key_averages().table(
        sort_by="self_cuda_time_total", row_limit=-1))
    print(prof.key_averages().table(sort_by="self_cuda_memory_usage", row_limit=15))
    prof.export_chrome_trace("~/profiling_results/test_trace_" + str(prof.step_num) + ".json")
    prof.export_memory_timeline("~/profiling_results/memory_" + str(prof.step_num) + ".html")


*** 显存profile

https://docs.pytorch.org/memory_viz

https://pytorch.org/blog/understanding-gpu-memory-1/
https://pytorch.org/blog/understanding-gpu-memory-2/

memory snapshot可以日常开启
pytorch memory profiler: 只能跟踪categorized memory曲线

import torch

torch.cuda.memory._record_memory_history()
torch.cuda.reset_max_memory_allocated() # 可传入device

with torch.inference_mode():
    shape = [256, 1024, 1024, 1]
    x1 = torch.randn(shape, device="cuda:0")
    x2 = torch.randn(shape, device="cuda:0")

    # Multiplication
    y = x1 * x2

torch.cuda.memory._dump_snapshot("logs/traces/vram_profile_example.pickle")
print("Max memory used by tensors = {} MB, reserved = {} MB".format(
      torch.cuda.max_memory_allocated() // 1e6, torch.cuda.max_memory_reserved() // 1e6))

- 无法profile第三方库比如nccl的显存占用

- 检测tensor cycles

from torch.utils.viz._cycles import warn_tensor_cycles
warn_tensor_cycles()


*** tensorboard展示

https://docs.pytorch.org/tutorials/intermediate/tensorboard_profiler_tutorial.html

