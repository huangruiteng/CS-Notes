import torch
import gc


class Module1(torch.nn.Module):
    def __init__(self):
        super(Module1, self).__init__()
        self.saved = Module2(self)  # Module1对象保存了对Module2对象的引用
        self.tensor = torch.randn(1024, 1024, device="cuda")


class Module2(torch.nn.Module):
    def __init__(self, module):
        super(Module2, self).__init__()
        self.saved = module  # Module2对象也保存了对Module1对象的饮用
        self.tensor = torch.randn(1024, 1024, device="cuda")


net = Module1()
print("Memory allocated: ", torch.cuda.memory_allocated(0))

del net
print("Memory allocated after delete: ", torch.cuda.memory_allocated(0))

gc.collect()
print("Memory allocated after gc: ", torch.cuda.memory_allocated(0))