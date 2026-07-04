*** Overview

1.pytorch Profiler

2. Nsight systems
- 非侵入
- OS、CUDA API、通信信息，多GPU性能分析支持更完善

3. Nsight Compute
- 优化GPU算子

自顶向下的分析（不同数值影响profile结果）：https://www.thonking.ai/p/strangely-matrix-multiplications


*** GPU Monitoring

# nvitop

https://github.com/XuehaiPan/nvitop

# nvidia-smi

https://gist.github.com/padeoe/771c4972ae185c9a7d3d497fa4e1ecab

alias nvidia-info='nvidia-smi && (nvidia-smi |tr -s " "|grep -Eo "| [0123456789]+ N/A N/A [0-9]{3,} .*"|awk -F" " '\''{system("s=$(cat /proc/"$4"/cmdline| tr \"\\0\" \" \");u=$(ps -o uname= -p "$4");echo "$1"sep"$4"sep$u sep"$7"sep$s" ) }'\''|sed "s/sep/\t/g")'


# 查询频率
nvidia-smi --query-gpu=pstate,clocks.mem,clocks.sm,clocks.gr --format=csv

# clocks.current.memory [MHz], clocks.current.sm [MHz], clocks.current.graphics [MHz]
# 9751 MHz, 1695 MHz, 1695 MHz

# 查询GPU支持的clock组合
nvidia-smi --query-supported-clocks=gpu_name,mem,gr --format=csv

# 设置persistent mode
sudo nvidia-smi -pm 1

# 固定GPU时钟
nvidia-smi -ac 9751,1530 # <memory, graphics>


*** time - 1
class TimePytorchFunction:

  def __init__(self, func, *args):
    self.start = torch.cuda.Event(enable_timing=True)
    self.end = torch.cuda.Event(enable_timing=True)
    self.result = None
    self.func = func
    self.args = args

  def __enter__(self):
    # 预热
    for _ in range(5):
      self.func(*self.args)
    self.start.record()
    return self

  def __exit__(self, exc_type, exc_val, exc_tb):
    self.end.record()
    torch.cuda.synchronize()
    elapsed_time = self.start.elapsed_time(self.end)
    print(f"{self.func.__name__} elapsed time: {elapsed_time} ms")

  def run(self):
    self.result = self.func(*self.args)
    return self.result

b = torch.randn(10000, 10000).cuda()
with TimePytorchFunction(torch.square, b) as timer:
    result = timer.run()

*** time - 2

# Timing utilities
import gc, time
start_time = None


def start_timer():
  global start_time
  gc.collect()
  torch.cuda.empty_cache()
  torch.cuda.reset_max_memory_allocated()
  torch.cuda.synchronize()
  start_time = time.perf_counter()


def end_timer_and_print(local_msg):
  torch.cuda.synchronize()
  end_time = time.perf_counter()
  print("\n" + local_msg)
  print("Total execution time = {:.3f} sec".format(end_time - start_time))
  print("Max memory used by tensors = {} MB, reserved = {} MB".format(
      torch.cuda.max_memory_allocated() // 1e6, torch.cuda.max_memory_reserved() // 1e6))

*** set seed

def set_seed(seed: int = 37) -> None:
    np.random.seed(seed)
    random.seed(seed)
    torch.manual_seed(seed)  # 适用于所有PyTorch后端，包括CPU和所有CUDA设备
    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = False

    os.environ["PYTHONHASHSEED"] = str(seed)
    print(f"设置随机数种子为{seed}")



*** ncu profiler

# install
https://www.bilibili.com/opus/898996578463776788

wget https://developer.nvidia.com/tools-downloads#?dn=nsight-compute-2025.1.1 
再运行
export PATH=$PATH:/usr/local/NVIDIA-Nsight-Compute-2025.1



# usage

ncu --target-processes all sudo python gpu_op_test.py
ncu --set full -o output $(which python) train.py     # basic模式和full模式

ncu --set full divergence


profiling心得
* active occupancy低，可能是：
1）线程计算任务简单，导致warp的创建和调度开销显著大于计算开销  --> 考虑合并简单线程
2）warp的负载不均衡，不同分支的warp无法同步执行 --> 分析代码
