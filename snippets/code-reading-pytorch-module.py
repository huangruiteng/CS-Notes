### Intro

nn.module 源码解读 https://zhuanlan.zhihu.com/p/340453841

一般有一个基类来定义接口，通过继承来处理不同维度的 input，如：
- Conv1d，Conv2d，Conv3d，ConvTransposeNd 继承自 _ConvNd
- MaxPool1d，MaxPool2d，MaxPool3d 继承自 _MaxPoolNd 等

每一个类都有一个对应的 nn.functional 函数，类定义了所需要的 arguments 和模块的 parameters，
在 forward 函数中将 arguments 和 parameters 传给 nn.functional 的对应函数来实现 forward 功能。比如：
- 所有的非线性激活函数，都是在 forward 中直接调用对应的 nn.functional 函数
- Normalization 层都是调用的如 F.layer_norm， F.group_norm 等函数




### 关于写一个新类继承module

继承 nn.Module 的模块主要重载 init、 forward、 和 extra_repr 函数，含有 parameters 的模块还会实现 reset_parameters 函数来初始化参数
继承 nn.Module 的神经网络模块在实现自己的 __init__ 函数时，一定要先调用 super().__init__()

MMCV 例子：https://github.com/open-mmlab/mmcv/blob/master/mmcv/ops/deform_conv.py#L299


### nn.Module Intro


class Module

  def load_state_dict:

  	 ...
     def load(module, local_state_dict, prefix=""):
        local_metadata = {} if metadata is None else metadata.get(prefix[:-1], {})
        if assign:
            local_metadata["assign_to_params_buffers"] = assign
        module._load_from_state_dict(
            local_state_dict,
            prefix,
            local_metadata,
            True,
            missing_keys,
            unexpected_keys,
            error_msgs,
        )
        for name, child in module._modules.items():
            if child is not None:
                child_prefix = prefix + name + "."
                child_state_dict = {
                    k: v
                    for k, v in local_state_dict.items()
                    if k.startswith(child_prefix)
                }
                load(child, child_state_dict, child_prefix)  # noqa: F821

  def __setattr__(self, name: str, value: Union[Tensor, "Module"]) -> None:
    ...
    modules = self.__dict__.get("_modules")
    modules[name] = value
    ...
    register_buffer(...)


细节：
    1.register_buffer：增加不通过 BP 更新的 buffer（如 BN 中的 running_mean 和 running_var），更新 self._buffers，
    如果 buffer 不是 persistant 的，还会同时更新到 self._non_persistent_buffers_set 中。
    buffer 是否 persistant 的区别在于这个 buffer 是否会能被放入 self.state_dict 中被保存下来。
     这 3 个函数都会先检查 self.__dict__ 中是否包含对应的属性字典以确保 nn.Module 被正确初始化，
     然后检查属性的 name 是否合法，如不为空 string 且不包含“.”，同时还会检查他们是否已经存在于要修改的属性字典中。

2. 增加 self._parameters，self._modules 的时候，会预先调用 remove_from 函数 （15 和 29 行）从其余私有属性中删除对应的 name，
这说明 self.dict，self._buffers，self._parameters，self._modules 中的属性应该是互斥的

3.self.xxxx = torch.Tensor() 是一种不被推荐的行为,在将模块进行状态转换的时候，self.xxxx 会被遗漏进而导致 device 或者 type 不一样的 bug

  def to(self, *args, **kwargs):
    ...


    

    通过 self.children() 进行递归的调用
    对 self._parameters 中的参数及其 gradient 通过 function 进行处理
    对 self._buffers 中的 buffer 逐个通过 function 来进行处理

  def _apply(self, fn, recurse=True):
        if recurse:
            for module in self.children():
                module._apply(fn)
        ...
        for key, param in self._parameters.items():
            if param is None:
                continue
            with torch.no_grad():
                param_applied = fn(param)
            param_grad = param.grad
            if param_grad is None:
                continue
            with torch.no_grad():
                grad_applied = fn(param_grad)
        for key, buf in self._buffers.items():
            if buf is not None:
                self._buffers[key] = fn(buf)
        return self

        只处理自己
    def apply(self: T, fn: Callable[['Module'], None]) -> T:
        for module in self.children():
            module.apply(fn)
        fn(self)
        return self

# apply的应用：参数重新初始化

@torch.no_grad()
def init_weights(m):
    print(m)
    if type(m) == nn.Linear:
        m.weight.fill_(1.0)
        print(m.weight)

net = nn.Sequential(nn.Linear(2, 2), nn.Linear(2, 2))
net.apply(init_weights)


CPU：将所有 parameters 和 buffer 转移到 CPU 上
type：将所有 parameters 和 buffer 转变成另一个类型
CUDA：将所有 parameters 和 buffer 转移到 GPU 上
float：将所有浮点类型的 parameters 和 buffer 转变成 float32 类型
double：将所有浮点类型的 parameters 和 buffer 转变成 double 类型
half：将所有浮点类型的 parameters 和 buffer 转变成 float16 类型
bfloat16：将所有浮点类型的 parameters 和 buffer 转变成 bfloat16 类型
to：移动模块或/和改变模块的类型
ipu、xpu、mtia、to_empty

# hooks

_global_buffer_registration_hooks: Dict[int, Callable] = OrderedDict()
_global_module_registration_hooks: Dict[int, Callable] = OrderedDict() # 可以包装一层module
_global_parameter_registration_hooks: Dict[int, Callable] = OrderedDict()

_global_backward_pre_hooks: Dict[int, Callable] = OrderedDict()
_global_backward_hooks: Dict[int, Callable] = OrderedDict()
_global_is_full_backward_hook: Optional[bool] = None
_global_forward_pre_hooks: Dict[int, Callable] = OrderedDict()
_global_forward_hooks: Dict[int, Callable] = OrderedDict()
_global_forward_hooks_always_called: Dict[int, bool] = OrderedDict()
_global_forward_hooks_with_kwargs: Dict[int, bool] = OrderedDict()


多个hooks的result是嵌套关系

_register_state_dict_hook
_register_load_state_dict_pre_hook


# Attributes

    dump_patches: bool = False
    _version: int = 1
    training: bool
    _parameters: Dict[str, Optional[Parameter]]
    _buffers: Dict[str, Optional[Tensor]]
    _non_persistent_buffers_set: Set[str]
    _backward_pre_hooks: Dict[int, Callable]
    _backward_hooks: Dict[int, Callable]
    _is_full_backward_hook: Optional[bool]
    _forward_hooks: Dict[int, Callable]
    _forward_hooks_with_kwargs: Dict[int, bool]
    _forward_hooks_always_called: Dict[int, bool]
    _forward_pre_hooks: Dict[int, Callable]
    _forward_pre_hooks_with_kwargs: Dict[int, bool]
    _state_dict_hooks: Dict[int, Callable]
    _load_state_dict_pre_hooks: Dict[int, Callable]
    _state_dict_pre_hooks: Dict[int, Callable]
    _load_state_dict_post_hooks: Dict[int, Callable]
    _modules: Dict[str, Optional["Module"]]
    call_super_init: bool = False
    _compiled_call_impl: Optional[Callable] = None

def __init__
    torch._C._log_api_usage_once("python.nn_module")
    super().__setattr__(...) # avoid Module.__setattr__ overhead


# 方法

add_module、register_module、get_submodule("net_b.net_c.conv")、set_submodule
还有parameter、buffer、extra_state

named_parameters、named_buffer、named_children

def named_modules(...):
    if memo is None:
        memo = set()
    if self not in memo:
        if remove_duplicate:
            memo.add(self)
        yield prefix, self
        for name, module in self._modules.items():
            if module is None:
                continue
            submodule_prefix = prefix + ("." if prefix else "") + name
            yield from module.named_modules(
                memo, submodule_prefix, remove_duplicate
            )


### 状态转变

# train、eval
self.eval 直接调用了 self.train(False)，而 self.train() 会修改 self.training 并通过 self.children() 来调整所有子模块的状态

def train(self: T, mode: bool = True) -> T:
    self.training = mode
    for module in self.children():
        module.train(mode)
    return self

Example: freeze 部分模型参数
在目标检测等任务中，常见的 training practice 会将 backbone 中的所有 BN 层保留为 eval 状态，
即 freeze BN 层中的 running_mean 和 running_var，并且将浅层的模块 freeze。
此时就需要重载 detector 类的 train 函数，MMDetection 中 ResNet 的 train 函数实现如下：



def train(self, mode=True):
    super(ResNet, self).train(mode)
    self._freeze_stages()
    if mode and self.norm_eval:
        for m in self.modules():
            # trick: eval have effect on BatchNorm only
            if isinstance(m, _BatchNorm):
                m.eval()


### 梯度处理

梯度的处理
对于梯度的处理 nn.Module 有两个相关的函数实现，分别是 requires_grad_ 和 zero_grad 函数，
他们都调用了 self.parameters() 来访问所有的参数，并修改参数的 requires_grad 状态 或者 清理参数的梯度。

深入了解梯度参考 https://pytorch.org/docs/stable/notes/autograd.html#locally-disabling-gradient-computation


def requires_grad_(self: T, requires_grad: bool = True) -> T:
    for p in self.parameters():
        p.requires_grad_(requires_grad)
    return self

def zero_grad(self, set_to_none: bool = False) -> None:
    if getattr(self, '_is_replica', False):
        warnings.warn(
            "Calling .zero_grad() from a module created with nn.DataParallel() has no effect. "
            "The parameters are copied (in a differentiable manner) from the original module. "
            "This means they are not leaf nodes in autograd and so don't accumulate gradients. "
            "If you need gradients in your forward method, consider using autograd.grad instead.")

    for p in self.parameters():
        if p.grad is not None:
            if set_to_none:
                p.grad = None
            else:
                if p.grad.grad_fn is not None:
                    p.grad.detach_()
                else:
                    p.grad.requires_grad_(False)
                p.grad.zero_()

分离梯度张量：
p.grad.grad_fn 表示梯度张量的 grad_fn 属性，它记录了梯度是如何计算出来的。如果 p.grad.grad_fn 不为 None，说明梯度张量仍然连接在计算图中。
此时使用 p.grad.detach_() 方法将梯度张量从计算图中分离出来，这样在后续的计算中就不会再对其进行求导。
如果 p.grad.grad_fn 为 None，说明梯度张量已经与计算图分离，此时使用 p.grad.requires_grad_(False) 方法将其 requires_grad 属性设置为 False，表示不再需要对其进行求导。


### Forward

__call__ -> _call_impl/_compiled_call_impl  -> _global_forward_pre_hooks -> _forward_pre_hooks

-> _slow_forward/forward -> _global_forward_hooks -> self._forward_hooks
-> bw_hook.setup_output_hook(result) -> non_full_backward_hook

# 细节
在 torch._C._get_tracing_state() 为 True 的时候，
nn.Module 会通过 _slow_forward() 来调用 forward 函数而非直接调用 forward 函数，这一功能主要用于 JIT


### state_dict

state_dict()

模块的 _version 信息会首先存入 metadata 中，用于模型的版本管理，
然后会通过 _save_to_state_dict() 将 self._parameters 以及 self._buffers 中的 persistent buffer 进行保存。
 用户可以通过重载 _save_to_state_dict 函数来满足特定的需求。

def load_state_dict():
    for name, param in local_state.items():
        key = prefix + name
        if key in state_dict:
            input_param = state_dict[key]
            with torch.no_grad():
                if use_swap_tensors:
                    new_input_param = param.module_load(
                        input_param, assign=assign_to_params_buffers
                    )
                    if id(new_input_param) == id(input_param) or id(
                        new_input_param
                    ) == id(param):
                        raise RuntimeError(
                            "module_load returned one of self or other, please .detach() "
                            "the result if returning one of the inputs in module_load"
                        )
                    if isinstance(param, torch.nn.Parameter):
                        if not isinstance(new_input_param, torch.nn.Parameter):
                            new_input_param = torch.nn.Parameter(
                                new_input_param,
                                requires_grad=param.requires_grad,
                            )
                        else:
                            new_input_param.requires_grad_(param.requires_grad)
                    torch.utils.swap_tensors(param, new_input_param)
                    del new_input_param
                elif assign_to_params_buffers:
                    # Shape checks are already done above
                    if isinstance(param, torch.nn.Parameter):
                        if not isinstance(input_param, torch.nn.Parameter):
                            input_param = torch.nn.Parameter(
                                input_param, requires_grad=param.requires_grad
                            )
                        else:
                            input_param.requires_grad_(param.requires_grad)
                    setattr(self, name, input_param)
                else:
                    param.copy_(input_param)

_load_from_state_dict 妙用

Example: 避免 BC-breaking
在模型迭代的过程中，module 很容易出现 BC-breaking ，PyTorch 通过 _version 和 _load_from_state_dict 来处理的这类问题（这也是 PyTorch 推荐的方式）。
 下面的代码是 _NormBase 类避免 BC-breaking 的方式。在 PyTorch 的开发过程中，
 Normalization layers 在某个新版本中 引入了 num_batches_tracked 这个 key，给 BN 记录训练过程中经历的 batch 数，
 为了兼容旧版本训练的模型，PyTorch 修改了 _version，并修改了 _load_from_state_dict

def _load_from_state_dict(self, state_dict, prefix, local_metadata, strict,
                          missing_keys, unexpected_keys, error_msgs):
    version = local_metadata.get('version', None)
    if (version is None or version < 2) and self.track_running_stats:
        # at version 2: added num_batches_tracked buffer
        #               this should have a default value of 0
        num_batches_tracked_key = prefix + 'num_batches_tracked'
        if num_batches_tracked_key not in state_dict:
            state_dict[num_batches_tracked_key] = torch.tensor(0, dtype=torch.long)
    super(_NormBase, self)._load_from_state_dict(
        state_dict, prefix, local_metadata, strict,
        missing_keys, unexpected_keys, error_msgs)

再举一个 MMCV 中的例子，DCN 经历了一次重构，属性的名字经过了重命名

Example: 模型无痛迁移

如果在 MMDetection 中训练了一个 detector，MMDetection3D 中的多模态检测器想要加载这个预训练的检测器，很多权重名字对不上，又不想写一个脚本手动来转，
可以使用 _load_from_state_dict 来进行。通过这种方式，MMDetection3D 可以加载并使用 MMDetection 训练的任意一个检测器。

def _load_from_state_dict(self, state_dict, prefix, local_metadata, strict,
                          missing_keys, unexpected_keys, error_msgs):
    # override the _load_from_state_dict function
    # convert the backbone weights pre-trained in Mask R-CNN
    # use list(state_dict.keys()) to avoid
    # RuntimeError: OrderedDict mutated during iteration
    for key_name in list(state_dict.keys()):
        key_changed = True
        if key_name.startswith('backbone.'):
            new_key_name = f'img_backbone{key_name[8:]}'
        elif key_name.startswith('neck.'):
            new_key_name = f'img_neck{key_name[4:]}'
        elif key_name.startswith('rpn_head.'):
            new_key_name = f'img_rpn_head{key_name[8:]}'
        elif key_name.startswith('roi_head.'):
            new_key_name = f'img_roi_head{key_name[8:]}'
        else:
            key_changed = False
        if key_changed:
            logger = get_root_logger()
            print_log(
                f'{key_name} renamed to be {new_key_name}', logger=logger)
            state_dict[new_key_name] = state_dict.pop(key_name)
    super()._load_from_state_dict(state_dict, prefix, local_metadata,
                                  strict, missing_keys, unexpected_keys,
                                  error_msgs)

### 其它

def __dir__(self):
    module_attrs = dir(self.__class__)
    attrs = list(self.__dict__.keys())
    parameters = list(self._parameters.keys())
    modules = list(self._modules.keys())
    buffers = list(self._buffers.keys())
    keys = module_attrs + attrs + parameters + modules + buffers
    # Eliminate attrs that are not legal Python variable names
    keys = [key for key in keys if not key[0].isdigit()]
    return sorted(keys)

