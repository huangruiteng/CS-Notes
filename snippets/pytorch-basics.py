dev论坛：https://dev-discuss.pytorch.org/
torchscript：https://pytorch.org/docs/stable/jit.html

### Intro

class LinearLayer(Module):
  def __init__(self, in_sz, out_sz):
    super().__init__()
    t1 = torch.randn(in_sz, out_sz)
    self.w = nn.Parameter(t1)
    t2 = torch.randn(out_sz)
    self.b = nn.Parameter(t2)
  def forward(self, activations):
    t = torch.mm(activations, self.w)
    return t + self.b
  
class FullBasicModel(nn.Module):
  def __init__(self):
    super().__init__()
    self.conv = nn.Conv2d(1, 128, 3)
    self.fc = LinearLayer(128, 10)
  def forward(self, x):
    t1 = self.conv(x)
    t2 = nn.functional.relu(t1)
    t3 = self.fc(t1)
    return nn.functional.softmax(t3)


discriminator = create_discriminator()
generator = create_generator()
optimD = optim.Adam(discriminator.parameters())
optimG = optim.Adam(generator.parameters())
def step(real_sample):
    # (1) Update Discriminator
    errD_real = loss(discriminator(real_sample), real_label)
    errD_real.backward()
    fake = generator(get_noise())
    errD_fake = loss(discriminator(fake.detach(), fake_label)
    errD_fake.backward()
    optimD.step()
    # (2) Update Generator
    errG = loss(discriminator(fake), real_label)
    errG.backward()
    optimG.step()

### tensor

input = torch.ones(3, 5)
print(input)

dim = len(input.shape)
print(dim)

# 创建一个3通道的RGB图像，大小为3x64x64
image = torch.rand(3, 64, 64)

# 输出：torch.Size([3, 64, 64])
print(image.size()) 


empty/zeros/ones/arange/linspace/rand/rand_like/randn

arange和linspace的区别：1)linspace包含尾部节点，arange不包含;2)linspace是生成N个元素
rand 01均匀分布；randn均值0方差1正态分布


result1 = torch.sum(input, dim=0)
print(result1)

result2 = torch.sum(input, dim=1)
print(result2)

# tensor([3., 3., 3., 3., 3.])
# tensor([5., 5., 5.])

import torch.nn.functional as F

data = torch.FloatTensor([[1.0, 2.0, 3.0], [4.0, 6.0, 8.0]])

# 在列上应用Softmax
prob = F.softmax(data, dim=0)

# 输出Softmax后的概率分布
print(prob)

# tensor([[0.0474, 0.0180, 0.0067],
#         [0.9526, 0.9820, 0.9933]])

tensor = torch.zeros(2, 3, 4)

print(tensor.stride())

# (12, 4, 1)

# 修改步长
torch.as_strided(input, size, stride, storage_offset=0)—>Tensor

# stride模拟卷积
image = torch.tensor([[1, 2, 3, 4],
                      [5, 6, 7, 8],
                      [9, 10, 11, 12],
                      [13, 14, 15, 16]])
kernel_weight = torch.tensor([[1, 1, 1],
                               [1, 1, 1],
                               [1, 1, 1]])
stride = 1
output_height = (image.shape[0] - kernel_weight.shape[0]) // stride + 1
output_width = (image.shape[1] - kernel_weight.shape[1]) // stride + 1
output = []
for i in range(output_height):
    row_output = []
    for j in range(output_width):
        image_patch = torch.as_strided(image, size=kernel_weight.shape,
                                       stride=(image.shape[1], 1),
                                       storage_offset=i * image.shape[1] + j)
        conv_result = (image_patch * kernel_weight).sum()
        row_output.append(conv_result)
    output.append(row_output)
output = torch.tensor(output)
print(output)


# long tensor

torch.LongTensor 储存int64


# to numpy/DLPack

零成本开销！

x = np.ones(3)
y = torch.tensor(x)
y = torch.from_numpy(x)

x = torch.ones(3)
y = x.detach().numpy() # gpu->cpu->numpy

y = x.numpy()

* Note
- 不支持负数stride x = np.random.random(size=(4, 4, 2)) y = np.flip(x, axis=0)



### tensor operation

# inplace原地更新: 破坏梯度传播、不分配内存
buf.mul_(momentum).add_(grad, alpha=1 - dampening)
param = param.add_(grad, alpha=-lr)

param += (- lr * grad) # 也会触发原地操作

Note [local_used_map_ -> local_used_map_dev copying]
We do async H2D to avoid the blocking overhead. The async copy and
allreduce respect the current stream, so will be sequenced correctly.

local_used_map_tmp.copy_(local_used_map_);
local_used_map_dev_.copy_(local_used_map_tmp, true);


在旧版本的 PyTorch 中，使用 .data 属性来获取张量中的数据，现在更推荐使用 .item() 方法。

sigmoid_()

exponential_() 生成指数分布随机数


# 视图操作
基础索引
expand（虚拟增加向量维度）
transpose/permute
narrow
squeeze/unsqueeze
chunk/split
as_strided
view
detach

视图操作的细节：
- torch.save会存储storage而不是tensor，因此存储的文件大小可能大于自身的数据量
- reshape和flatten的行为不确定，可能返回view可能返回copy


# 高级索引
x[x < 10]、x[torch.tensor([0,1,2]), torch.tensor([2,3,4])]
高级索引会copy内存

- 高级索引的赋值会影响原向量


a = torch.arange(1, 13).view(4, 3)
a_t = a.t()

print(a.is_contiguous()) ## True

print(a_t.is_contiguous()) ## False
# 对一个 tensor 进行转置操作之后会改变它的 contiguous 特性

# 当对张量进行一些操作（如 transpose()、permute()、split(..., dim=1) 等）后，张量在内存中的存储可能不再连续

# 此时如果直接使用 view() 方法，就会抛出错误

a_t_v = a_t.view(-1) ## 会报错
a_t = a.t().contiguous()
a_t_v = a_t.view(-1)

# stack
torch.stack(inputs,dim=0,out=None)

# concat
torch.cat(tensors, dim=0, out=None)

数据合并：在数据预处理阶段，可能需要将来自不同源的数据集合并在一起。
特征融合：在深度学习模型中，经常需要将来自不同层或不同路径的特征合并起来，以增强模型的表示能力。
批处理操作：在处理批数据时，可以用torch.cat来合并来自不同批次的输出结果。

# 其它

bool tensor的all方法

### tensor index

x[1:9:3]
x[:, None, :]

torch.gather(input, dim, index, *, sparse_grad=False, out=None)

data = torch.arange(1, 10).view(3, 3)

# tensor([[1, 2, 3],
#         [4, 5, 6],
#         [7, 8, 9]])

index = torch.tensor([[2, 1, 0]])
result = data.gather(dim=0, index=index)

# tensor([[7, 5, 3]])

result = data.gather(dim=1, index=index)

# tensor([[3, 2, 1]])

torch.Tensor.scatter_(dim, index, src) 用于将源张量中的值按照指定的索引位置填充到目标张量中

# tensor的bool mask
def get_split_partition_masks(tensor: torch.Tensor, num_partition: int):
  partition_idx = torch.fmod(tensor, num_partition)
  return [partition_idx == i for i in range(num_partition)]


### leaf node

a = torch.tensor([1.0, 1.0], requires_grad=False)
print(a.is_leaf) # T
print(a.requires_grad) # F
b = a + 1
print(b.is_leaf) # T
print(b.requires_grad) # F

b = a + 1 # 非叶子

### detach

- 将张量从当前计算图中分离出来，从而不需要跟踪张量的梯度变化
- 可视化
- 独立tensor


### Global setting

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

data = data.to(device)
model = Model(...).to(device)

torch.set_default_device("cuda")  # current device is 0
torch.set_default_device("cuda:1")

# 提醒：这不会影响创建与输入共享相同内存的张量的函数，如：torch.from_numpy()和torch.from_buffer()

# PyTorch 默认浮点类型是 torch.float32
torch.tensor([1.2, 3]).dtype
# torch.float32
# PyTorch 默认复数的浮点类型是 torch.complex64
torch.tensor([1.2, 3j]).dtype
# torch.complex64

torch.set_default_dtype(torch.float16)


### Debugging

torch.set_printoptions(precision=None, threshold=None, edgeitems=None, linewidth=None, profile=None, sci_mode=None)

precision – Number of digits of precision for floating point output (default = 4).
threshold – Total number of array elements which trigger summarization rather than full repr (default = 1000).
edgeitems – Number of array items in summary at beginning and end of each dimension (default = 3).
linewidth – The number of characters per line for the purpose of inserting line breaks (default = 80). Thresholded matrices will ignore this parameter.
profile – Sane defaults for pretty printing. Can override with any of the above options. (any one of default, short, full)
sci_mode – Enable (True) or disable (False) scientific notation. If None (default) is specified, the value is defined by torch._tensor_str._Formatter. This value is automatically chosen by the framework.


### device

torch.randn((2,3), device=1)
torch.randn((2,3), device="cuda:1")

张量永远不会在设备之间自动移动，需要用户进行显式调用。标量张量（tensor.dim()==0）是此规则的唯一例外，当需要时，它们会自动从CPU转移到GPU，因为此操作可以“自动”完成

.cuda()
.to(device)

# CUDA设备索引与GPU设备索引

# CUDA设备索引
os.environ["CUDA_VISIBLE_DEVICES"] = "0"
print(torch.cuda.get_device_name(0))
print(torch.cuda.get_device_properties(0))

# GPU设备索引
nvidia-smi -L

# nvidia-smi命令中的GPU编号与PyTorch代码中的CUDA编号正好相反
原因：nvidia-smi下的GPU编号默认使用 PCI_BUS_ID，而 PyTorch 代码默认情况下设备排序是 FASTEST_FIRST
解决办法：os.environ["CUDA_DEVICE_ORDER"]="PCI_BUS_ID"


### eval模式
影响Dropout层和BatchNorm层行为

