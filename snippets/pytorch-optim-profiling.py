# For-loop
# Total execution time = 0.404 sec
# Max memory used by tensors = 80436224 bytes
#
# For-each
# Total execution time = 0.115 sec
# Max memory used by tensors = 96242688 bytes
#
# Fused
# Total execution time = 0.064 sec
# Max memory used by tensors = 105991680 bytes


import torch
from torch.profiler import profile, ProfilerActivity
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
  print("Max memory used by tensors = {} bytes".format(
      torch.cuda.max_memory_allocated()))


class SimpleNet(torch.nn.Module):
    def __init__(self):
        super(SimpleNet, self).__init__()
        self.fcs = torch.nn.ModuleList(torch.nn.Linear(200, 200) for i in range(20))

    def forward(self, x):
        for i in range(len(self.fcs)):
            x = torch.relu(self.fcs[i](x))
        return x


def train(net, optimizer, opt_name=""):
    data = torch.randn(64, 200, device="cuda:0")
    target = torch.randint(0, 1, (64,), device="cuda:0")
    criterion = torch.nn.CrossEntropyLoss()
    with profile(activities=[ProfilerActivity.CPU, ProfilerActivity.CUDA]) as prof:
        for _ in range(5):
            optimizer.zero_grad()
            output = net(data)
            loss = criterion(output, target)
            loss.backward()
            optimizer.step()
    prof.export_chrome_trace(f"logs/traces/PROF_perf_{opt_name}.json")


# For-loop
net = SimpleNet().to(torch.device("cuda:0"))
adam_for_loop = torch.optim.Adam(
    net.parameters(), lr=0.01, foreach=False, fused=False
)
start_timer()
train(net, adam_for_loop, opt_name="for_loop")
end_timer_and_print("For-loop")


# For-each
net = SimpleNet().to(torch.device("cuda:0"))
adam_for_each = torch.optim.Adam(
    net.parameters(), lr=0.01, foreach=True, fused=False
)
start_timer()
train(net, adam_for_each, opt_name="for_each")
end_timer_and_print("For-each")


# Fused
net = SimpleNet().to(torch.device("cuda:0"))
adam_fused = torch.optim.Adam(net.parameters(), lr=0.01, foreach=False, fused=True)
start_timer()
train(net, adam_fused, opt_name="fused")
end_timer_and_print("Fused")