import torch
from torch import nn
from torch.profiler import profile, ProfilerActivity
import torchvision.transforms as transforms
from torchvision.datasets import CIFAR10
from torch.utils.data import DataLoader


class SimpleNet(nn.Module):
    def __init__(self):
        super(SimpleNet, self).__init__()
        self.fc1 = nn.Linear(512, 10000)
        self.fc2 = nn.Linear(10000, 1000)
        self.fc3 = nn.Linear(1000, 10)

    def forward(self, x):
        out = self.fc1(x)
        out = self.fc2(out)
        out = self.fc3(out)
        return out


assert torch.cuda.is_available()
device = torch.device("cuda")
model = SimpleNet().to(device)
optimizer = torch.optim.SGD(model.parameters(), lr=0.01)


def train(model, optimizer, trainloader, num_iters):
    with profile(activities=[ProfilerActivity.CPU, ProfilerActivity.CUDA]) as prof:
        for i, batch in enumerate(trainloader, 0):
            if i >= num_iters:
                break
            data = batch[0].cuda()

            # 前向
            optimizer.zero_grad()
            output = model(data)
            loss = output.sum()

            # 反向
            loss.backward()
            optimizer.step()
    prof.export_chrome_trace(f"traces/PROF_workers_{trainloader.num_workers}.json")


num_workers = 0
transform = transforms.Compose(
    [transforms.ToTensor(), transforms.Resize([512, 512])]
)
trainset = CIFAR10(root="./data", train=True, download=True, transform=transform)
trainloader = DataLoader(trainset, batch_size=32, num_workers=num_workers)

train(model, optimizer, trainloader, num_iters=20)