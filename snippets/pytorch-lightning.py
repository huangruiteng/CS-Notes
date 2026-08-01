### Intro

减少样板代码

### pytorch

epochs = 5

for i in range(epochs):
    train_loss = 0.0
    for data,label in trainloader:
        if is_gpu:
            data, label = data.cuda(), label.cuda()
        output = model(data)
        optimizer.zero_grad()
        loss = criterion(output,label)
        loss.backward()
        optimizer.step()
        train_loss += loss.item() * data.size(0)

### lightning

def training_step(self, train_batch, batch_idx):
    x, y = train_batch
    logits = self.forward(x)
    loss = self.loss(logits,y)
    return loss


### pytorch

import torch
import torch.nn as nn
import torch.optim as optim
from torchvision import datasets, transforms

# Define the model
class NeuralNetwork(nn.Module):
    def __init__(self):
        super(NeuralNetwork, self).__init__()
        self.fc1 = nn.Linear(784, 256)
        self.fc2 = nn.Linear(256, 128)
        self.fc3 = nn.Linear(128, 10)

    def forward(self, x):
        x = torch.flatten(x, 1)
        x = torch.relu(self.fc1(x))
        x = torch.relu(self.fc2(x))
        x = self.fc3(x)
        return x

# Load the dataset
transform = transforms.Compose([
    transforms.ToTensor(),
    transforms.Normalize((0.1307,), (0.3081,))
])
train_dataset = datasets.MNIST("data", train=True, download=True, transform=transform)
test_dataset = datasets.MNIST("data", train=False, download=True, transform=transform)
train_loader = torch.utils.data.DataLoader(train_dataset, batch_size=64, shuffle=True)
test_loader = torch.utils.data.DataLoader(test_dataset, batch_size=64, shuffle=False)

# Initialize the model
model = NeuralNetwork()

# Define the optimizer and loss function
optimizer = optim.SGD(model.parameters(), lr=0.01)
criterion = nn.CrossEntropyLoss()

# Training loop
def train(model, train_loader, optimizer, criterion):
    model.train()
    for batch_idx, (data, target) in enumerate(train_loader):
        optimizer.zero_grad()
        output = model(data)
        loss = criterion(output, target)
        loss.backward()
        optimizer.step()

# Validation loop
def validate(model, test_loader, criterion):
    model.eval()
    test_loss = 0
    correct = 0
    with torch.no_grad():
        for data, target in test_loader:
            output = model(data)
            test_loss += criterion(output, target).item()
            pred = output.argmax(dim=1, keepdim=True)
            correct += pred.eq(target.view_as(pred)).sum().item()
    test_loss /= len(test_loader.dataset)
    accuracy = 100. * correct / len(test_loader.dataset)
    print("Validation set: Average loss: {:.4f}, Accuracy: {}/{} ({:.2f}%)".format(
        test_loss, correct, len(test_loader.dataset), accuracy))

# Train and validate the model
for epoch in range(10):
    train(model, train_loader, optimizer, criterion)
    validate(model, test_loader, criterion)


### Lightning

import torch
from torch import nn
from torch.utils.data import DataLoader
from torchvision.datasets import MNIST
from torchvision.transforms import ToTensor
from torch.optim import Adam
import pytorch_lightning as pl

class MyModel(pl.LightningModule):
    def __init__(self):
        super().__init__()
        self.model = nn.Sequential(
            nn.Linear(784, 256),
            nn.ReLU(),
            nn.Linear(256, 128),
            nn.ReLU(),
            nn.Linear(128, 10),
            nn.Softmax(dim=1)
        )

    def forward(self, x):
        x = x.view(x.size(0), -1)  # Reshape the input
        return self.model(x)

    def training_step(self, batch, batch_idx):
        x, y = batch
        y_hat = self(x)
        loss = nn.CrossEntropyLoss()(y_hat, y)
        self.log("train_loss", loss)
        return loss

    def validation_step(self, batch, batch_idx):
        x, y = batch
        y_hat = self(x)
        loss = nn.CrossEntropyLoss()(y_hat, y)
        self.log("val_loss", loss)
        # Calculate accuracy
        correct = (y_hat.argmax(1) == y).sum().item()
        total = y.size(0)
        self.log("accuracy", correct / total, on_step=False, on_epoch=True, prog_bar=True)

    def configure_optimizers(self):
        return Adam(self.parameters(), lr=0.001)

# Load the MNIST dataset
train_dataset = MNIST(root=".", train=True, transform=ToTensor(), download=True)
val_dataset = MNIST(root=".", train=False, transform=ToTensor())

# Create data loaders
train_loader = DataLoader(train_dataset, batch_size=64, shuffle=True)
val_loader = DataLoader(val_dataset, batch_size=64)

# Initialize the model
model = MyModel()

# Initialize the trainer
trainer = pl.Trainer(max_epochs=10, accelerator = "cpu" if torch.cuda.is_available() else "cpu")

# Train the model
trainer.fit(model, train_loader, val_loader)

trainer.validate(model, val_loader)
