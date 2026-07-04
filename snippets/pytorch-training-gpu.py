### Basic

import torch
import torch.nn as nn
from torch.utils.data import DataLoader
from torch.nn import DataParallel

x = torch.randn(5, 3)

if torch.cuda.is_available():
    x = x.to("cuda:0")
    print("Tensor moved to GPU")
else:
    print("GPU is not available, using CPU instead")

class SimpleModel(nn.Module):
    def __init__(self):
        super(SimpleModel, self).__init__()
        self.fc = nn.Linear(10, 1)

    def forward(self, x):
        return self.fc(x)

model = SimpleModel().to("cuda")


### Data Parallel

torch.nn.DataParallel(module, device_ids=None, output_device=None, dim=0)

# output_device默认为None，梯度回传到第一张卡做optimize
# 数据分割->模型副本->合并结果
# 只需要将输入数据通过 .to(torch.device("cuda:0")) 移动到主GPU（即 DataParallel 中的第一个GPU），模型和损失函数会自动处理分布式计算。


model = nn.Linear(10, 10)
data_loader = DataLoader(torch.randn(100, 10), batch_size=10)

# 在GPU(s)上创建模型的实例
device_ids = [0, 1]
model = DataParallel(model, device_ids=device_ids)

# 将模型和数据加载器移动到GPU
model.to(torch.device("cuda:0"))

# 训练循环
for data in data_loader:
    input = data.to(torch.device("cuda:0"))  # 将输入移动到主GPU
    output = model(input)
    loss = loss_function(output, target)
    loss.backward()
    optimizer.step()


### fp16

import autocast
from torch.cuda.amp import autocast

@autocast()
def forward(self, x):
    ...
    return x


 for x in train_loader:
    x = x.cuda()
    with autocast():
        output = model(x)
        ...