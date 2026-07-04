*** intro

import torch
from torchvision import transforms
from torch.utils.data import Dataset

torch.utils.data.Dataset需要覆写下面两个方法

class MyDataset(Dataset):
    def __init__(self, root_dir, transform=None):
        self.root_dir = root_dir
        self.transform = transform
        self.data = [...] # 根据需求加载数据集

    def __len__(self):
        return len(self.data)

    def __getitem__(self, index):
        # 加载数据
        img_path = self.data[index]["image_path"]
        label_path = self.data[index]["label_path"]
        img = self.load_image(img_path)
        label = self.load_label(label_path)

        # 数据预处理
        if self.transform:
            img = self.transform(img)

        return img, label

transform = transforms.Compose([
    transforms.Resize((256, 256)),
    transforms.ToTensor(),
    transforms.Normalize((0.5,), (0.5,))
])

dataloader = DataLoader(dataset, batch_size=32, shuffle=True)

for images, labels in dataloader:
    ...


X = torch.randn(100, 3)
Y = torch.randn(100, 1)

dataset = TensorDataset(X, Y)


*** parquet dataset

class CriteoParquetDataset(Dataset):
    def __init__(self, file_name: str):
        df = pd.read_parquet(file_name)
        self.total_rows = len(df)
        self.label_tensor = torch.from_numpy(df["labels"].values).to(torch.float32)
        dense_columns = [f for f in df.columns if f.startswith("DENSE")]
        sparse_columns = [f for f in df.columns if f.startswith("SPARSE")]
        self.dense_tensor = torch.from_numpy(df[dense_columns].values)
        self.sparse_tensor = torch.from_numpy(df[sparse_columns].values)

    def __len__(self):
        return self.total_rows

    def __getitem__(self, idx):
        return self.label_tensor[idx], self.dense_tensor[idx], \
        self.sparse_tensor[idx]


*** 内存问题 -- 读多个文件的实现

* 读数据
  * https://zhuanlan.zhihu.com/p/376974245
  * Dataset 每次获取一个Part的Dataframe，外部再进行batch_size的划分，这样在整个迭代期间，最多只会有num_worker个Dataset被实例化，事实上也确实不再有内存溢出的问题

class ExpDataset2(Dataset):
    def __init__(self, filenames, features_config): 
        self._filenames = filenames
        
    def __getitem__(self, idx):
        path = self._filenames[idx]
        return preprocess(read_csv(path)

def load_data(paths, features_config, num_workers, batch_size):
    dataset = ExpDataset2(paths, features_config)
    data = DataLoader(
        dataset,
        num_workers=num_workers,
        batch_size=1,
        collate_fn=collate_fn2
    )
    for df in data:
        for idx_from in range(0, df.shape[0], batch_size):
            yield examples[idx_from : idx_from + batch_size]


- DistributedSampler 要求输入的数据集是可索引的（map-style dataset）

- to_map_style_dataset 函数的作用是将迭代式数据集转换为可索引的数据集，使得数据集可以被 DistributedSampler 使用。
通过这种转换，我们可以为数据集添加 __getitem__ 和 __len__ 方法，从而满足 DistributedSampler 的要求。


### IterableDataset

def worker_init_fn(worker_id):
...     worker_info = torch.utils.data.get_worker_info()
...     dataset = worker_info.dataset  # the dataset copy in this worker process
...     overall_start = dataset.start
...     overall_end = dataset.end
...     # configure the dataset to only process the split workload
...     per_worker = int(math.ceil((overall_end - overall_start) / float(worker_info.num_workers)))
...     worker_id = worker_info.id
...     dataset.start = overall_start + worker_id * per_worker
...     dataset.end = min(dataset.start + per_worker, overall_end)

print(list(torch.utils.data.DataLoader(ds, num_workers=2, worker_init_fn=worker_init_fn)))

### collate_fn

class SimpleCustomBatch:
    # 自定义一个类，该类不能被PyTorch原生的pin_memory方法所支持

    def __init__(self, data):
        transposed_data = list(zip(*data))
        self.inp = torch.stack(transposed_data[0], 0)
        self.tgt = torch.stack(transposed_data[1], 0)

    # custom memory pinning method on custom type
    def pin_memory(self):
        self.inp = self.inp.pin_memory()
        self.tgt = self.tgt.pin_memory()
        return self

def collate_wrapper(batch):
    return SimpleCustomBatch(batch)

inps = torch.arange(10 * 5, dtype=torch.float32).view(10, 5)
tgts = torch.arange(10 * 5, dtype=torch.float32).view(10, 5)
dataset = TensorDataset(inps, tgts)

loader = DataLoader(dataset, batch_size=2, collate_fn=collate_wrapper,
                    pin_memory=True)

for batch_ndx, sample in enumerate(loader):
    print(sample.inp.is_pinned())  # True
    print(sample.tgt.is_pinned())  # True


### dataset加速 -- prefetcher

最早见于nvidia apex

https://blog.csdn.net/weiman1/article/details/125610786

class data_prefetcher():
    def __init__(self, loader, device):
        self.loader = iter(loader)
        self.stream = torch.cuda.Stream()
        self.device = device
        self.preload()

    def preload(self):
        try:
            self.next_input, self.next_target = next(self.loader)
        except StopIteration:
            self.next_input = None
            self.next_target = None
            return
        with torch.cuda.stream(self.stream):
            self.next_input, self.next_target = ensure_device(self.device, self.next_input, self.next_target, non_blocking=True)

    def next(self):
        torch.cuda.current_stream().wait_stream(self.stream)
        input = self.next_input
        target = self.next_target
        if input is not None:
          if isinstance(input, dict):
            for k, v in input.items():
              if isinstance(v, torch.Tensor):
                v.record_stream(torch.cuda.current_stream())
          else:
            input.record_stream(torch.cuda.current_stream())
        if target is not None:
            target.record_stream(torch.cuda.current_stream())
        self.preload()
        return input, target

### prefetch generator

https://stackoverflow.com/questions/7323664/python-generator-pre-fetch

DDP不work

### DDP + queue

- DDP 和 dataloader中Queue的使用不兼容
  - DDP自己管理了共享内存，有些比较深的hack操作
  - https://discuss.pytorch.org/t/communicating-with-dataloader-workers/11473/9
  - things break predictably when you nest shared memory structures within other nested shared memory structures. The ideal way to have asynchronous communication between PyTorch dataloader workers is to use process Queues, which shuttle active child process state information to the next active worker which then in turn shuttles new information to the next.
  - 需要结合torch.multiprocessing.Manager().RLock()进行实现

### torch.data

https://pytorch.org/data/main/what_is_torchdata_nodes.html
https://github.com/pytorch/data?tab=readme-ov-file#what-is-torchdata
  - 性能上受益于 Python No-GIL的趋势
  - stateful dataset

- torchdata.nodes performs on-par or better with torch.utils.data.DataLoader when using multi-processing (see Migrating to torchdata.nodes from torch.utils.data)
- With GIL python, torchdata.nodes with multi-threading performs better than multi-processing in some scenarios, but makes features like GPU pre-proc easier to perform, which can boost throughput for many use cases.
- With No-GIL / Free-Threaded python (3.13t), we ran a benchmark loading the Imagenet dataset from disk, and manage to saturate main-memory bandwidth at a significantly lower CPU utilization than with multi-process workers (blogpost expected eary 2025). See imagenet_benchmark.py to try on your own hardware.


### concurrent dataloader

- paper：https://arxiv.org/pdf/2211.04908
- 代码：https://github.com/iarai/concurrent-dataloader/blob/master/src/concurrent_dataloader/dataloader_mod/worker.py

### predefined dataset

import torchvision.datasets as datasets
import torchvision.transforms as transforms

transform = transforms.Compose([transforms.ToTensor()])

train_dataset = datasets.CIFAR10(root="./data", train=True, download=True, transform=transform)
test_dataset = datasets.CIFAR10(root="./data", train=False, download=True, transform=transform)
