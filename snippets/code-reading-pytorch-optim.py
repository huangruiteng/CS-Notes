https://zhuanlan.zhihu.com/p/346205754

GPU-Mode Lecture 6 Optimizing Optimizers

### Note
只有parameter才会被自动优化，tensor(...,require_grad=True)只会计算梯度，不会自动更新

### usage

import torch
import numpy as np
import warnings
warnings.filterwarnings('ignore') #ignore warnings

x = torch.linspace(-np.pi, np.pi, 2000)
y = torch.sin(x)

p = torch.tensor([1, 2, 3])
xx = x.unsqueeze(-1).pow(p)

model = torch.nn.Sequential(
    torch.nn.Linear(3, 1),
    torch.nn.Flatten(0, 1)
)
loss_fn = torch.nn.MSELoss(reduction='sum')

learning_rate = 1e-3
optimizer = torch.optim.RMSprop(model.parameters(), lr=learning_rate)
for t in range(1, 1001):
    y_pred = model(xx)
    loss = loss_fn(y_pred, y)
    if t % 100 == 0:
        print('No.{: 5d}, loss: {:.6f}'.format(t, loss.item()))
    optimizer.zero_grad() # 梯度清零
    loss.backward() # 反向传播计算梯度
    optimizer.step() # 梯度下降法更新参数

# param_groups

optimizer = SGD([
                {'params': model.base.parameters()}, 
                {'params': model.fc.parameters(), 'lr': 1e-3} # 对 fc的参数设置不同的学习率
            ], lr=1e-2, momentum=0.9)

### Optimizer
torch.optim.optimizer
Optimizer._optimizer_step_post_hooks

self.state: DefaultDict[torch.Tensor, Any] = defaultdict(dict)
self.param_groups: List[Dict[str, Any]] = []

def __getstate__(self) -> Dict[str, Any]:  # noqa: D105
        return {
            "defaults": self.defaults,
            "state": self.state,
            "param_groups": self.param_groups,
        }

def add_param_group
 # This can be useful when fine tuning a pre-trained network as frozen layers can be made
   #      trainable and added to the :class:`Optimizer` as training progresses.
   # 检查 group之间的param_group["params"] 不冲突

# 注册hook
所有注册：register_optimizer_step_post_hook
单个注册：register_step_pre_hook

register_state_dict_post_hook
register_load_state_dict_post_hook

参数prepend

# 状态

state_dict()

``state`` is a Dictionary mapping parameter ids
            to a Dict with state corresponding to each parameter.

{
    'state': {
        0: {'momentum_buffer': tensor(...), ...},
        1: {'momentum_buffer': tensor(...), ...},
        2: {'momentum_buffer': tensor(...), ...},
        3: {'momentum_buffer': tensor(...), ...}
    },
    'param_groups': [
        {
            'lr': 0.01,
            'weight_decay': 0,
            ...
            'params': [0]
        },
        {
            'lr': 0.001,
            'weight_decay': 0.5,
            ...
            'params': [1, 2, 3]
        }
    ]
}

# zero_grad
set_to_none

梯度设置为 None 和 0 在 PyTorch 中处理逻辑会不一样

set_to_none (bool): instead of setting to zero, set the grads to None.
                This will in general have lower memory footprint, and can modestly improve performance.
                However, it changes certain behaviors. For example:
                1. When the user tries to access a gradient and perform manual ops on it,
                a None attribute or a Tensor full of 0s will behave differently.
                2. If the user requests ``zero_grad(set_to_none=True)`` followed by a backward pass, ``.grad``\ s
                are guaranteed to be None for params that did not receive a gradient.
                3. ``torch.optim`` optimizers have a different behavior if the gradient is 0 or None
                (in one case it does the step with a gradient of 0 and in the other it skips
                the step altogether).

for_each优化
torch._foreach_zero_(grads)

### 优化器有哪些

adagrad.py  adamax.py  asgd.py   rmsprop.py  sgd.py
adadelta.py    adam.py     adamw.py   lbfgs.py  nadam.py         radam.py      rprop.py    sparse_adam.py


### SGD

@_use_grad_for_differentiable
def step(self, closure=None):

step 方法可传入闭包函数 closure，主要目的是为了实现如Conjugate Gradient和LBFGS等优化算法，这些算法需要对模型进行多次评估
Python 中闭包概念：在一个内部函数中，对外部作用域的变量进行引用(并且一般外部函数的返回值为内部函数)，那么内部函数就被认为是闭包

# 原地更新，破坏梯度传播
buf.mul_(momentum).add_(grad, alpha=1 - dampening)
param.add_(grad, alpha=-lr)

_multi_tensor_sgd
_single_tensor_sgd
* _foreach_add_
_fused_sgd_
* _fused_sgd_

### adamw

def _single_tensor_adam
    for i, param in enumerate(params):
        ...


def _multi_tensor_adam                       ** 默认实现 **
    torch._foreach_add_(device_state_steps, 1)
    # Perform stepweight decay
    if weight_decay != 0:
        torch._foreach_mul_(device_params, 1 - lr * weight_decay)

    # Decay the first and second moment running average coefficient
    torch._foreach_lerp_(device_exp_avgs, device_grads, 1 - beta1)

    torch._foreach_mul_(device_exp_avg_sqs, beta2)
    torch._foreach_addcmul_(device_exp_avg_sqs, device_grads, device_grads, 1 - beta2)

    . . .

    torch._foreach_div_(exp_avg_sq_sqrt, bias_correction2_sqrt)
    torch._foreach_add_(exp_avg_sq_sqrt, eps)
    torch._foreach_addcdiv_(device_params, device_exp_avgs, exp_avg_sq_sqrt, step_size)


def _fused_adam
    func = torch._fused_adam_ if not decoupled_weight_decay else torch._fused_adamw_


### 问题：如何实现_foreach_add_的cuda kernel
* 优化的历程：https://github.com/pytorch/pytorch/commits/main/aten/src/ATen/native/cuda/MultiTensorApply.cuh

- attempt 1: 传入 std::vector<float*> self --> cuda不支持
- attempt 2: 传入 float** self
    Does this work?
    Nope! This will cause an Illegal Memory Access (IMA)
    because the outer pointer * is a CPU address!
- attempt 3: 

struct TensorListMetadata {
  const float* addresses[3][NUM_TENSORS];
};

<add all the addresses into the struct>

__device__ void _foreach_add_kernel(
            TensorListMetadata tlm,
            float alpha=1) {
…
}

- attempt 3 bug: illegal memory access

params = [torch.rand(2, 3, device="cuda") for _ in range(N)]
torch._foreach_norm(params, ord=1)
torch.cuda.synchronize()

Only if NUM_TENSORS < 424, it works
<-- CUDA Kernel argument space has a max limit of 4KB 
--> 当前限制了110个tensor？
--> 拆分结构的code在哪？    参考「code-reading-pytorch-gpu-op」
static constexpr int64_t kChunkSize = 65536;
static constexpr int64_t kBlockSize = 512;

- revisit attempt 2: memcpy float** self 对应的tensor地址到cuda上

- 未来规划：
- 思路1: we will be doing a mix of struct + memcpy
- 思路2: cuda unified memory，避免memcpy
  e.g. bitsandbytes paged optimizer
   https://github.com/bitsandbytes-foundation/bitsandbytes/blob/main/docs/source/explanations/optimizers.mdx
   https://github.com/bitsandbytes-foundation/bitsandbytes/issues/962
  pytorch由于有cuda cache allocator，因此使用unified memory比较麻烦


### torch.compile优化

optimizer = torch.optim.AdamW(params)

@torch.compile(fullgraph=False)
def compiled_step():
    optimizer.step()

All optimizers in pytorch/pytorch with a foreach implementation are now compilable
So everything except L-BFGS（两次backward） and SparseAdam（sparse tensor）
Vertical fusion of any sequence of supported _foreach_* ops should work!



### lr_scheduler

有序调整策略:
StepLR
MultiStepLR
ExponentialLR
CyclicLR
OneCycleLR
CosineAnnealingLR
CosineAnnealingWarmRestarts


自适应调整策略:
ReduceLROnPlateau


自定义调整策略:
LambdaLR
MultiplicativeLR

确保lr_scheduler.step()是在optimizer.step()之后调用的
LRScheduler在初始化时已经调用过一次step()方法。

def state_dict(self):
    """Return the state of the scheduler as a :class:`dict`.

    It contains an entry for every variable in self.__dict__ which
    is not the optimizer.
    """
    return {
        key: value for key, value in self.__dict__.items() if key != "optimizer"
    }

def load_state_dict(self, state_dict: Dict[str, Any]):
    """Load the scheduler's state.

    Args:
        state_dict (dict): scheduler state. Should be an object returned
            from a call to :meth:`state_dict`.
    """
    self.__dict__.update(state_dict)


def step
该方法里对last_epoch自增之后，在内部上下文管理器类里调用子类实现的get_lr()方法获得各参数组在此次 epoch 时的学习率，
并更新到 optimizer的param_groups属性之中，最后记录下最后一次调整的学习率到self._last_lr，此属性将在get_last_lr()方法中返回


### 可视化学习率

## 可视化学习率
from torch.optim import lr_scheduler
from matplotlib import pyplot as plt
%matplotlib inline

def create_optimizer():
    return SGD(model.parameters(), lr=0.1, momentum=0.9, weight_decay=1e-4)

def plot_lr(scheduler, title='', labels=['base'], nrof_epoch=100):
    lr_li = [[] for _ in range(len(labels))]
    epoch_li = list(range(nrof_epoch))
    for epoch in epoch_li:
        scheduler.step()  # 调用step()方法,计算和更新optimizer管理的参数基于当前epoch的学习率
        lr = scheduler.get_last_lr()  # 获取当前epoch的学习率
        for i in range(len(labels)):
            lr_li[i].append(lr[i])
    for lr, label in zip(lr_li, labels):
        plt.plot(epoch_li, lr, label=label)
    plt.grid()
    plt.xlabel('epoch')
    plt.ylabel('lr')
    plt.title(title)
    plt.legend()
    plt.show()
## StepLR 可视化学习率
optimizer = create_optimizer()
scheduler = lr_scheduler.StepLR(optimizer, step_size=30, gamma=0.1)
plot_lr(scheduler, title='StepLR')


### 随机参数平均 swa_utils

AveragedModel: 实现 SWA 算法的权重平均模型
SWALR: 与AverageModel配合使用的学习率调整策略
update_bn: 更新模型中的 bn

随机权重平均(SWA)是一种优化算法，在SWA 论文的结果证明，取 SGD 轨迹的多点简单平均值，以一个周期或者不变的学习率，会比传统训练有更好的泛化效果。
论文的结果同样了证明了，随机权重平均 (SWA) 可以找到更广的最优值域。

def get_ema_avg_fn(decay=0.999):
    """Get the function applying exponential moving average (EMA) across a single param."""

    @torch.no_grad()
    def ema_update(ema_param: Tensor, current_param: Tensor, num_averaged):
        return decay * ema_param + (1 - decay) * current_param

    return ema_update


def get_swa_avg_fn():
    """Get the function applying stochastic weight average (SWA) across a single param."""

    @torch.no_grad()
    def swa_update(
        averaged_param: Tensor, current_param: Tensor, num_averaged: Union[Tensor, int]
    ):
        return averaged_param + (current_param - averaged_param) / (num_averaged + 1)

    return swa_update

 Stochastic Weight Averaging was proposed in `Averaging Weights Leads to
    Wider Optima and Better Generalization`_ by Pavel Izmailov, Dmitrii
    Podoprikhin, Timur Garipov, Dmitry Vetrov and Andrew Gordon Wilson
    (UAI 2018).

    Exponential Moving Average is a variation of `Polyak averaging`_,
    but using exponential weights instead of equal weights across iterations.


### 技巧
from typing_extensions import ParamSpec, Self, TypeAlias

ParamsT: TypeAlias = Union[Iterable[torch.Tensor], Iterable[Dict[str, Any]]]
_P = ParamSpec("_P")
R = TypeVar("R")
T = TypeVar("T")

Args: TypeAlias = Tuple[Any,...]
Kwargs: TypeAlias = Dict[str, Any]
StateDict: TypeAlias = Dict[str, Any]

OrderedDict()

GlobalOptimizerPreHook: TypeAlias = Callable[
    ["Optimizer", Args, Kwargs], Optional[Tuple[Args, Kwargs]]
]


self.register_buffer(
    "n_averaged", torch.tensor(0, dtype=torch.long, device=device)
)

itertools.chain
