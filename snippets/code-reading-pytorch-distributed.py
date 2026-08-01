Q: DDP中buffer是如何sync的?
Q: 混合精度训练 + DDP是如何work的？
_module_wait_for_copy_hook
_fire_reducer_autograd_hook


DP&DDP源码解析 https://zhuanlan.zhihu.com/p/343951042


原理也参考「MLSys.md - 并行训练」


### DP

DP原理解析 https://zhuanlan.zhihu.com/p/675217571

只有前向传播在K卡之间并行，损失函数计算（loss_f）以及反向传播的启动(.backward())、优化器更新都只进行了一次，都不需要更改。

def simulate_dp(model, x, K, cpu=False):
    """
    model: nn.Module to use
    x: input tensor
    K: number of devices
    cpu: whether to use cpu devices
    """
    if cpu:
        devices = [torch.device("cpu") for i in range(K)] # simulate data parallel in cpu
    else:
        devices = [torch.device(f"cuda:{i}") for i in range(K)]

    # split the input and scatter to devices
    xs = torch.chunk(x, K)
    xs = [t.to(d) for t, d in zip(xs, devices)]
    
    # replicate module's state to devices
    state_dict = model.state_dict(keep_vars=True)
    state_dicts = [state_dict]
    for device in devices[1:]:
        new_state_dict = torch.utils._pytree.tree_map(lambda x: x.clone().to(device), state_dict)
        state_dicts.append(new_state_dict)
    
    # call forward in devices separately
    ys = []
    for t, state_dict in zip(xs, state_dicts):
        output = torch.func.functional_call(model, state_dict, t)
        ys.append(output)
    
    # gather outputs to one device and concat
    y = torch.cat([each.to(devices[0]) for each in ys])
    return y

nn/parallel/data_parallel.py

class DataParallel(Module):

    def __init__(self, module, device_ids=None, output_device=None, dim=0):
        super(DataParallel, self).__init__()

        # 检查是否有可用的 GPU
        device_type = _get_available_device_type()
        if device_type is None:
            self.module = module
            self.device_ids = []
            return
        
        # 默认使用所有可见的 GPU
        if device_ids is None:
            device_ids = _get_all_device_indices()

        # 默认 server 是 device_ids 列表上第一个
        if output_device is None:
            output_device = device_ids[0]

        self.dim = dim
        self.module = module
        self.device_ids = list(map(lambda x: _get_device_index(x, True), device_ids))
        self.output_device = _get_device_index(output_device, True)
        self.src_device_obj = torch.device(device_type, self.device_ids[0])

        # 检查负载是否平衡， 不平衡（指内存或者处理器 max/min > 0.75 会有警告）
        if device_type == "cuda":
            _check_balance(self.device_ids)

        # 单卡
        if len(self.device_ids) == 1:
            self.module.to(self.src_device_obj)

    def forward(self, *inputs, **kwargs):

        # 没 GPU 可用
        if not self.device_ids:
            return self.module(*inputs, **kwargs)

        # 运行前 GPU device_ids[0] （即我们的 server ）上必须有 parallelized module 的parameters 和 buffers
        # 因为 DP 保证 GPU device_ids[0] 和 base parallelized module 共享存储
        # 所以在device[0] 上的 in-place 更新也会被保留下来，其他的则不会

        for t in chain(self.module.parameters(), self.module.buffers()):
            if t.device != self.src_device_obj:
                raise RuntimeError("module must have its parameters and buffers "
                                   "on device {} (device_ids[0]) but found one of "
                                   "them on device: {}".format(self.src_device_obj, t.device))

        # nice 现在 device[0] 上已经有了 module 和 input， 接下来我们就要开始 PS 算法了
        # 可以开始看正文了

        inputs, kwargs = self.scatter(inputs, kwargs, self.device_ids)

        # 如果仅有单卡可用，直接单卡计算，不用并行
        if len(self.device_ids) == 1:
            return self.module(*inputs[0], **kwargs[0])

        replicas = self.replicate(self.module, self.device_ids[:len(inputs)])
        outputs = self.parallel_apply(replicas, inputs, kwargs)
        return self.gather(outputs, self.output_device)

    def replicate(self, module, device_ids):
        return replicate(module, device_ids, not torch.is_grad_enabled())

    def scatter(self, inputs, kwargs, device_ids):
        return scatter_kwargs(inputs, kwargs, device_ids, dim=self.dim)

    def parallel_apply(self, replicas, inputs, kwargs):
        return parallel_apply(replicas, inputs, kwargs, self.device_ids[:len(replicas)])

    def gather(self, outputs, output_device):
        return gather(outputs, output_device, dim=self.dim)

def scatter_kwargs(inputs, kwargs, target_gpus, dim=0):
    r"""Scatter with support for kwargs dictionary"""

    # 主要函数
    inputs = scatter(inputs, target_gpus, dim) if inputs else []
    kwargs = scatter(kwargs, target_gpus, dim) if kwargs else []

    # 用空项补全使 inputs 和 kwargs 长度相当
    if len(inputs) < len(kwargs):
        inputs.extend([() for _ in range(len(kwargs) - len(inputs))])
    elif len(kwargs) < len(inputs):
        kwargs.extend([{} for _ in range(len(inputs) - len(kwargs))])
    # 返回 tuple
    inputs = tuple(inputs)
    kwargs = tuple(kwargs)
    return inputs, kwargs

# scatter_gather.py

scatter 函数，负责将 tensor 分成大概相等的块并将他们分给不同的 GPU。对其他的数据类型，则是复制分散给不同的 GPU 。


def scatter(inputs, target_gpus, dim=0):
    r"""Slice tensors into approximately equal chunks and distributes them across given GPUs.

    Duplicates references to objects that are not tensors.
    """

    def scatter_map(obj):
        if isinstance(obj, torch.Tensor):
            return Scatter.apply(target_gpus, None, dim, obj)
        if _is_namedtuple(obj):
            return [type(obj)(*args) for args in zip(*map(scatter_map, obj))]
        if isinstance(obj, tuple) and len(obj) > 0:
            return list(zip(*map(scatter_map, obj)))
        if isinstance(obj, list) and len(obj) > 0:
            return [list(i) for i in zip(*map(scatter_map, obj))]
        if isinstance(obj, dict) and len(obj) > 0:
            return [type(obj)(i) for i in zip(*map(scatter_map, obj.items()))]
        return [obj for _ in target_gpus]

    # After scatter_map is called, a scatter_map cell will exist. This cell
    # has a reference to the actual function scatter_map, which has references
    # to a closure that has a reference to the scatter_map cell (because the
    # fn is recursive). To avoid this reference cycle, we set the function to
    # None, clearing the cell
    try:
        res = scatter_map(inputs)
    finally:
        scatter_map = None  # type: ignore[assignment]
    return res

class Scatter(Function):
    @staticmethod
    def forward(ctx, target_gpus, chunk_sizes, dim, input):
        target_gpus = [_get_device_index(x, True) for x in target_gpus]
        ctx.dim = dim
        ctx.input_device = input.get_device() if input.device.type != "cpu" else -1
        streams = None
        if torch.cuda.is_available() and ctx.input_device == -1:
            # Perform CPU to GPU copies in a background stream
            streams = [
                _get_stream(torch.device("cuda", device)) for device in target_gpus
            ]
        outputs = comm.scatter(input, target_gpus, chunk_sizes, ctx.dim, streams)
        # Synchronize with the copy stream
        if streams is not None:
            for i, output in enumerate(outputs):
                with torch.cuda.device(target_gpus[i]):
                    main_stream = torch.cuda.current_stream()
                    main_stream.wait_stream(streams[i])
                    output.record_stream(main_stream)
        return outputs

    @staticmethod
    def backward(ctx, *grad_output):
        return None, None, None, Gather.apply(ctx.input_device, ctx.dim, *grad_output)

class BroadCast
    @staticmethod
    def backward(ctx, *grad_outputs):
        return (None,) + ReduceAddCoalesced.apply(ctx.input_device, ctx.num_inputs, *grad_outputs)

def replicate(network, devices, detach=False):
    # 需要复制到哪些 GPU， 复制多少份
    devices = [_get_device_index(x, True) for x in devices]
    num_replicas = len(devices)

    # 复制 parameters
    params = list(network.parameters())
    param_indices = {param: idx for idx, param in enumerate(params)}

    param_copies = _broadcast_coalesced_reshape(params, devices, detach)
    ...

    modules = list(network.modules())
    module_copies: List[List[Module]] = [[] for _ in devices]
    module_indices: Dict[Module, int] = {}

    for i, module in enumerate(modules):
            module_indices[module] = i
            for j in range(num_replicas):
                replica = module._replicate_for_data_parallel()
                # This is a temporary fix for DDP. DDP needs to access the
                # replicated model parameters. It used to do so through
                # `mode.parameters()`. The fix added in #33907 for DP stops the
                # `parameters()` API from exposing the replicated parameters.
                # Hence, we add a `_former_parameters` dict here to support DDP.
                replica._former_parameters = OrderedDict()

                module_copies[j].append(replica)

    # 接下来分别复制 module，param，buffer

    for i, module in enumerate(modules):
        for key, child in module._modules.items():
            if child is None:
                for j in range(num_replicas):
                    replica = module_copies[j][i]
                    replica._modules[key] = None
            else:
                module_idx = module_indices[child]
                for j in range(num_replicas):
                    replica = module_copies[j][i]
                    setattr(replica, key, module_copies[j][module_idx])
        for key, param in module._parameters.items():
            if param is None:
                for j in range(num_replicas):
                    replica = module_copies[j][i]
                    replica._parameters[key] = None
            else:
                param_idx = param_indices[param]
                for j in range(num_replicas):
                    replica = module_copies[j][i]
                    param_copy = param_copies[j][param_idx]
                    # parameters in replicas are no longer leaves,
                    # so setattr them as non-parameter attributes
                    setattr(replica, key, param_copy)
                    # expose the parameter for DDP
                    replica._former_parameters[key] = param_copy
        for key, buf in module._buffers.items():  # type: ignore[assignment]
            if buf is None:
                for j in range(num_replicas):
                    replica = module_copies[j][i]
                    replica._buffers[key] = None
            else:
                if buf.requires_grad and not detach:
                    buffer_copies = buffer_copies_rg
                    buffer_idx = buffer_indices_rg[buf]
                else:
                    buffer_copies = buffer_copies_not_rg
                    buffer_idx = buffer_indices_not_rg[buf]
                for j in range(num_replicas):
                    replica = module_copies[j][i]
                    setattr(replica, key, buffer_copies[j][buffer_idx])

    return [cast(T, module_copies[j][0]) for j in range(num_replicas)]


返回的object：
module.py

def _replicate_for_data_parallel(self):
        replica = self.__new__(type(self))
        replica.__dict__ = self.__dict__.copy()

        # replicas do not have parameters themselves, the replicas reference the original
        # module.
        replica._parameters = {}
        replica._buffers = replica._buffers.copy()
        replica._modules = replica._modules.copy()
        replica._is_replica = True  # type: ignore[assignment]

        return replica

# parallel_forward.py

# DP 代码
outputs = self.parallel_apply(replicas, inputs, kwargs)

# threading 实现，用前面准备好的 replica 和输入数据，然后
# for 循环启动多线程

# 源码
def parallel_apply(modules, inputs, kwargs_tup=None, devices=None):

        # 每个 GPU 都有模型和输入
    assert len(modules) == len(inputs)

    # 确保每个 GPU 都有相应的数据，如没有就空白补全
    if kwargs_tup is not None:
      # 咱们在 scatter 已经补全了
        assert len(modules) == len(kwargs_tup)
    else:
        kwargs_tup = ({},) * len(modules)

    if devices is not None:
        assert len(modules) == len(devices)
    else:
        devices = [None] * len(modules)

    devices = [_get_device_index(x, True) for x in devices]

    # 多线程实现

    lock = threading.Lock()
    results = {}
    grad_enabled, autocast_enabled = torch.is_grad_enabled(), torch.is_autocast_enabled()

    # 定义 worker
    def _worker(i, module, input, kwargs, device=None):
        torch.set_grad_enabled(grad_enabled)
        if device is None:
            device = get_a_var(input).get_device()
        try:
            with torch.cuda.device(device), autocast(enabled=autocast_enabled):
                # this also avoids accidental slicing of `input` if it is a Tensor
                if not isinstance(input, (list, tuple)):
                    input = (input,)
                output = module(*input, **kwargs)
            with lock:
              # 并行计算得到输出
                results[i] = output
        except Exception:
            with lock:
                results[i] = ExceptionWrapper(
                    where="in replica {} on device {}".format(i, device))

    if len(modules) > 1:

      # 如有一个进程控制多个 GPU ，起多个线程
      # 需要强调一下，虽然 DDP 推荐单卡单进程，即每次调用 DDP device_ids 都只输入一张卡的 id（通常是 args.local_rank），但是如果输入多个 device_id，此时 DDP 就是单进程多线程控制多卡，和 DP 一样，关于 DDP 的解读可以看下文

        threads = [threading.Thread(target=_worker,
                                    args=(i, module, input, kwargs, device))
                   for i, (module, input, kwargs, device) in
                   enumerate(zip(modules, inputs, kwargs_tup, devices))]

        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
    else:
      # 一个 GPU 一个进程 （ DDP 推荐操作）
        _worker(0, modules[0], inputs[0], kwargs_tup[0], devices[0])

    outputs = []
    for i in range(len(inputs)):
        output = results[i]

        # error handle
        if isinstance(output, ExceptionWrapper):
            output.reraise()
        outputs.append(output)
    # 输出 n 个计算结果
    return outputs



### DDP

DDP 通过 Reducer 来管理梯度同步。为了提高通讯效率， Reducer 会将梯度归到不同的桶里
（按照模型参数的 reverse order， 因为反向传播需要符合这样的顺序），一次归约一个桶。其中桶的大小为参数 bucket_cap_mb 默认为 25，可根据需要调整。

DDP 通过在构建时注册 autograd hook 进行梯度同步。
反向传播时，当一个梯度计算好后，相应的 hook 会告诉 DDP 可以用来归约。
当一个桶里的梯度都可以了，Reducer 就会启动异步 allreduce 去计算所有进程的平均值。
allreduce 异步启动使得 DDP 可以边计算边通信，提高效率。当所有桶都可以了，Reducer 会等所有 allreduce 完成，然后将得到的梯度写到 param.grad。

Design Note: https://pytorch.org/docs/main/notes/ddp.html


代码架构：
distributed.py
--
reducer.h, comm.h
--
ProcessGroup.hpp (NCCL, GLOO, MPI, RR)


Prerequisite:
DDP relies on c10d ProcessGroup for communications. 
Hence, applications must create ProcessGroup instances before constructing DDP.

Construction:
The DDP constructor takes a reference to the local module, and broadcasts state_dict() from the process with rank 0 to all other processes in the group
to make sure that all model replicas start from the exact same state. 
Then, each DDP process creates a local Reducer, which later will take care of the gradients synchronization during the backward pass. 
To improve communication efficiency, the Reducer organizes parameter gradients into buckets, and reduces one bucket at a time. 
Bucket size can be configured by setting the bucket_cap_mb argument in DDP constructor. 
The mapping from parameter gradients to buckets is determined at the construction time, based on the bucket size limit and parameter sizes.


 Model parameters are allocated into buckets in (roughly) the reverse order of Model.parameters() from the given model. 
 The reason for using the reverse order is
 - because DDP expects gradients to become ready during the backward pass in approximately that order
 - DDP requires Reducer instances on all processes to invoke allreduce in exactly the same order,
   which is done by always running allreduce in the bucket index order instead of actual bucket ready order. Mismatched allreduce order across processes can lead to wrong results or DDP backward hang.

还注册了autograd hooks during construction, one hook per parameter


Forward Pass:

解决执行subgraph部分梯度不存在的问题
proactively marking them ready at the end of the forward pass, 获知梯度存在信息
find_unused_parameters： During the backward pass, the Reducer would only wait for unready parameters, but it would still reduce all buckets.
- when the optimizer uses gradient absence information to skip updating momentum values.
- DDP uses a bitmap to keep track of local parameter participants and launches one additional AllReduce to
collect globally unused parameters.
训练时有可能某次迭代只用到整个模型的一个 subgraph， 并且这个 subgraph 迭代时可能会改变，
就是说某些参数可能会在训练时被跳过。但因为所有parameters 在一开始就被分好桶了，而我们的 hook 又规定了只有整个桶 ready 了（pending==0）才会通信，
如果我们不将 unused parameter 标记为 ready，整个过程会没法进行。



Backward Pass: 
DDP uses autograd hooks registered at construction time to trigger gradients synchronizations
When gradients in one bucket are all ready, the Reducer kicks off an asynchronous allreduce on that bucket to calculate mean of gradients across all processes.
When all buckets are ready, the Reducer will block waiting for all allreduce operations to finish.
When this is done, averaged gradients are written to the param.grad field of all parameters.

Optimizer Step:
From the optimizer’s perspective, it is optimizing a local model.
Model replicas on all DDP processes can keep in sync because they all start from the same state
and they have the same averaged gradients in every iteration.
- optimizer开销大吗？比完整参数传输开销小

# find_unused_parameters小实验

参考「pytorch-distributed-example.py」


# Gradient Accumulation


ddp = DistributedDataParallel(net)
with ddp.no_sync ():
    for inp , exp in zip(inputs , expected_outputs):
        # no synchronization , accumulate grads
        loss_fn(ddp(inp), exp).backward()
# synchronize grads
loss_fn(ddp(another_inp), another_exp).backward()
opt.step()


### distributed.py

# 细节
1.超参
process_group: to specify a process group
instance for DDP to run AllReduce, which helps to avoid
messing up with the default process group

bucket_cap_mb: to control the AllReduce bucket size, where applications
should tune this knob to optimize training speed,

find_unused_parameters: to toggle whether DDP should detect unused parameters by traversing the autograd graph.

gradient_as_bucket_view: 优化显存
delay_all_reduce_named_params
mixed_precision: 似乎是被autocast替代的

2.Model Device Aﬃnity
treats the multi-device model as one entirety

3.Model Buﬀers
are necessary when layers need to keep
track of states like the running variance and the running
mean (e.g., BatchNorm).

DDP supports model buﬀers by letting the process with the rank 0 to take the authority.

If the model contains buﬀers, DDP will broadcast the buﬀer values
from rank 0 process to all other processes before starting
the forward pass on the local model. This behavior is also
compatible with the no sync mode. When no sync mode is
enabled, it sets a ﬂag in the forward pass properly to indi-
cate whether it expects gradient reductions in the immediate
backward pass. If the communication takes place, DDP will
then broadcast buﬀers prior to the subsequent forward pass

# 代码

class DistributedDataParallel(Module):       
    def __init__(self, module, device_ids=None,
                 output_device=None, dim=0, broadcast_buffers=True,
                 process_group=None,  
                 bucket_cap_mb=25,       
                 find_unused_parameters=False,       
                 check_reduction=False,      
                 gradient_as_bucket_view=False):

        super(DistributedDataParallel, self).__init__()

        assert any((p.requires_grad for p in module.parameters())), (
            "DistributedDataParallel is not needed when a module "
            "doesn't have any parameter that requires a gradient."
        )

        self.is_multi_device_module = len({p.device for p in module.parameters()}) > 1
        distinct_device_types = {p.device.type for p in module.parameters()}
        assert len(distinct_device_types) == 1, (
            "DistributedDataParallel's input module must be on "
            "the same type of devices, but input module parameters locate in {}."
        ).format(distinct_device_types)
        self.device_type = list(distinct_device_types)[0]

        if self.device_type == "cpu" or self.is_multi_device_module:
            assert not device_ids and not output_device, (
                "DistributedDataParallel device_ids and output_device arguments "
                "only work with single-device GPU modules, but got "
                "device_ids {}, output_device {}, and module parameters {}."
            ).format(device_ids, output_device, {p.device for p in module.parameters()})

            self.device_ids = None
            self.output_device = None
        else:
            # Use all devices by default for single-device GPU modules
            if device_ids is None:
                device_ids = _get_all_device_indices()

            self.device_ids = list(map(lambda x: _get_device_index(x, True), device_ids))

            if output_device is None:
                output_device = device_ids[0]

            self.output_device = _get_device_index(output_device, True)

        if process_group is None:
            self.process_group = _get_default_group()
        else:
            self.process_group = process_group

        self.dim = dim
        self.module = module
        self.device = list(self.module.parameters())[0].device
        self.broadcast_buffers = broadcast_buffers
        self.find_unused_parameters = find_unused_parameters
        self.require_backward_grad_sync = True
        self.require_forward_param_sync = True
        self.ddp_join_enabled = False
        self.gradient_as_bucket_view = gradient_as_bucket_view

        if check_reduction:
            # This argument is no longer used since the reducer
            # will ensure reduction completes even if some parameters
            # do not receive gradients.
            warnings.warn(
                "The `check_reduction` argument in `DistributedDataParallel` "
                "module is deprecated. Please avoid using it."
            )
            pass

        # used for intra-node param sync and inter-node sync as well
        self.broadcast_bucket_size = int(250 * 1024 * 1024)

        #
        # reduction bucket size
        self.bucket_bytes_cap = int(bucket_cap_mb * 1024 * 1024)

        # 保证初始状态一样
        # All collectives during initialization are gated by this flag.
        if init_sync:
            # Verify model equivalence.
            _verify_param_shape_across_processes(self.process_group, parameters)
            # Sync params and buffers. Ensures all DDP models start off at the same value.
            _sync_module_states(
                module=self.module,
                process_group=self.process_group,
                broadcast_bucket_size=self.broadcast_bucket_size,
                src=0,
                params_and_buffers_to_ignore=self.parameters_to_ignore,
                broadcast_buffers=self.broadcast_buffers,
            )

        # 下拉看源码
        self._ddp_init_helper()


    def _ddp_init_helper(self):
        """
        Initialization helper function that does the following:

        (1) replicating the module from device[0] to the other devices （前文提到 DDP 也支持一个进程多线程利用多卡，类似 DP ，这时候就会用到第一步）
        (2) bucketing the parameters for reductions （把 parameter 分组，梯度通讯时，先得到梯度的会通讯）
        (3) resetting the bucketing states
        (4) registering the grad hooks （创建管理器）
        (5) passing a handle of DDP to SyncBatchNorm Layer （为 SyncBN 准备）
        """

        def parameters(m, recurse=True):
            def model_parameters(m):
                ps = m._former_parameters.values() \
                    if hasattr(m, "_former_parameters") \
                    else m.parameters(recurse=False)
                for p in ps:
                    yield p

            for m in m.modules() if recurse else [m]:
                for p in model_parameters(m):
                    yield p

        if self.device_ids and len(self.device_ids) > 1:

            warnings.warn(
                "Single-Process Multi-GPU is not the recommended mode for "
                "DDP. In this mode, each DDP instance operates on multiple "
                "devices and creates multiple module replicas within one "
                "process. The overhead of scatter/gather and GIL contention "
                "in every forward pass can slow down training. "
                "Please consider using one DDP instance per device or per "
                "module replica by explicitly setting device_ids or "
                "CUDA_VISIBLE_DEVICES. "
            )

            # only create replicas for single-device CUDA modules
            #
            # TODO: we don't need to replicate params in here. they're always going to
            # be broadcasted using larger blocks in broadcast_coalesced, so it might be
            # better to not pollute the caches with these small blocks
            self._module_copies = replicate(self.module, self.device_ids, detach=True)
            self._module_copies[0] = self.module

            for module_copy in self._module_copies[1:]:
                for param, copy_param in zip(self.module.parameters(), parameters(module_copy)):
                    # Reducer requires param copies have the same strides across replicas.
                    # Fixes up copy_param strides in case replicate didn't match param strides.
                    if param.layout is torch.strided and param.stride() != copy_param.stride():
                        with torch.no_grad():
                            copy_param.set_(copy_param.clone()
                                                      .as_strided(param.size(), param.stride())
                                                      .copy_(copy_param))
                    copy_param.requires_grad = param.requires_grad

        else:
            self._module_copies = [self.module]

        self.modules_params = [list(parameters(m)) for m in self._module_copies]
        self.modules_buffers = [list(m.buffers()) for m in self._module_copies]

        # Build tuple of (module, parameter) for all parameters that require grads.
        modules_and_parameters = [
            [
                (module, parameter)
                for module in replica.modules()
                for parameter in filter(
                    lambda parameter: parameter.requires_grad,
                    parameters(module, recurse=False))
            ] for replica in self._module_copies]

        # Build list of parameters.
        parameters = [
            list(parameter for _, parameter in replica)
            for replica in modules_and_parameters]

        # Checks if a module will produce a sparse gradient.
        def produces_sparse_gradient(module):
            if isinstance(module, torch.nn.Embedding):
                return module.sparse
            if isinstance(module, torch.nn.EmbeddingBag):
                return module.sparse
            return False

        # Build list of booleans indicating whether or not to expect sparse
        # gradients for the corresponding parameters.
        expect_sparse_gradient = [
            list(produces_sparse_gradient(module) for module, _ in replica)
            for replica in modules_and_parameters]

        # The bucket size limit is specified in the constructor.
        # Additionally, we allow for a single small bucket for parameters
        # that are defined first, such that their gradients don't spill into
        # a much larger bucket, adding unnecessary latency after gradient
        # computation finishes. Experiments showed 1MB is a reasonable value.
        bucket_indices = dist._compute_bucket_assignment_by_size(
            parameters[0],
            [dist._DEFAULT_FIRST_BUCKET_BYTES, self.bucket_bytes_cap],
            expect_sparse_gradient[0])

        # Note: reverse list of buckets because we want to approximate the
        # order in which their gradients are produced, and assume they
        # are used in the forward pass in the order they are defined.
        # 管理器
        self.reducer = dist.Reducer(
            parameters,
            list(reversed(bucket_indices)),
            self.process_group,
            expect_sparse_gradient,
            self.bucket_bytes_cap,
            self.find_unused_parameters,
            self.gradient_as_bucket_view)

        # passing a handle to torch.nn.SyncBatchNorm layer
        self._passing_sync_batchnorm_handle(self._module_copies)

        if self.mixed_precision is not None:
            ...

    def _pre_forward
        # Calling _rebuild_buckets before forward computation,
        # It may allocate new buckets before deallocating old buckets
        # inside _rebuild_buckets. To save peak memory usage,
        # call _rebuild_buckets before the peak memory usage increases
        # during forward computation.
        # This should be called only once during whole training period.
        if torch.is_grad_enabled() and self.reducer._rebuild_buckets():
            logger.info("Reducer buckets have been rebuilt in this iteration.")
            self._has_rebuilt_buckets = True

        # sync params according to location (before/after forward) user
        # specified as part of hook, if hook was specified.
        if self._check_sync_bufs_pre_fwd():
            self._sync_buffers()


    def forward(self, *inputs, **kwargs):
        with torch.autograd.profiler.record_function("DistributedDataParallel.forward"):
            inputs, kwargs = self._pre_forward(*inputs, **kwargs)
            output = (
                self.module.forward(*inputs, **kwargs)
                if self._delay_all_reduce_all_params
                else self._run_ddp_forward(*inputs, **kwargs)
            )
            return self._post_forward(output)

        intra-process parameter synchronization when one DDP process works on multiple devices,
        and it also broadcasts model buffers from the process with rank 0 to all other processes

    def _post_forward(self, output):
        ...
        if self._delay_all_reduce_all_params:
            self._clear_grad_buffer()
            return output

        # sync params according to location (before/after forward) user
        # specified as part of hook, if hook was specified.
        if self._check_sync_bufs_post_fwd():
            self._sync_buffers()

        if torch.is_grad_enabled() and self.require_backward_grad_sync:
            self.require_forward_param_sync = True
            # We'll return the output object verbatim since it is a freeform
            # object. We need to find any tensors in this object, though,
            # because we need to figure out which parameters were used during
            # this forward pass, to ensure we short circuit reduction for any
            # unused parameters. Only if `find_unused_parameters` is set.
            # 当DDP参数 find_unused_parameter 为 true 时，其会在 forward 结束时，启动一个回溯，
            # 标记出所有没被用到的 parameter，提前把这些设定为 ready，这样 backward 就可以在一个 subgraph 进行，但这样会牺牲一部分时间。
            if self.find_unused_parameters and not self.static_graph:
                # Do not need to populate this for static graph.
                self.reducer.prepare_for_backward(list(_find_tensors(output)))
            else:
                self.reducer.prepare_for_backward([])
        else:
            self.require_forward_param_sync = False

        # TODO: DDPSink is currently enabled for unused parameter detection and
        # static graph training for first iteration.
        if (self.find_unused_parameters and not self.static_graph) or (
            self.static_graph and not self._static_graph_delay_allreduce_enqueued
        ):
            (
                output_tensor_list,
                treespec,
                output_is_rref,
            ) = _tree_flatten_with_rref(output)
            output_placeholders: list[Optional[torch.Tensor]] = [
                None for _ in range(len(output_tensor_list))
            ]
            # Do not touch tensors that have no grad_fn, which can cause issues
            # such as https://github.com/pytorch/pytorch/issues/60733
            for i, output in enumerate(output_tensor_list):
                if torch.is_tensor(output) and output.grad_fn is None:
                    output_placeholders[i] = output

            # When find_unused_parameters=True, makes tensors which require grad
            # run through the DDPSink backward pass. When not all outputs are
            # used in loss, this makes those corresponding tensors receive
            # undefined gradient which the reducer then handles to ensure
            # param.grad field is not touched and we don't error out.
            passthrough_tensor_list = _DDPSink.apply(
                weakref.ref(self),
                *output_tensor_list,
            )
            for i in range(len(output_placeholders)):
                if output_placeholders[i] is None:
                    output_placeholders[i] = passthrough_tensor_list[i]

            # Reconstruct output data structure.
            output = _tree_unflatten_with_rref(
                output_placeholders, treespec, output_is_rref
            )

        # At the end of the forward pass, reset the grad buffer and grad views
        self._clear_grad_buffer()
        return output

    def _sync_module_states
        the inter-process parameter synchronization happens in Reducer.cpp.


# mixed_precision

https://github.com/pytorch/pytorch/pull/92882

forward_pre_hook: hook1 fwd之前cast to low, hook2 等待copy






### reducer.h, comm.h

调用  torch.distributed.init_process_group
--> 生成c10d ProcessGroup实例

# comm.h

implements the coalesced broadcast helper function which is invoked to broadcast model states during initialization
and synchronize model buffers before the forward pass.


# reducer.h

Reducer: The constructor is called in distributed.py which registers Reducer::autograd_hook() to gradient accumulators.

- Parameter-to-Bucket Mapping:
-- make sure that all parameters in the same bucket are on the same device
-- launches AllReduce in the reverse order of model.parameters()


- autograd_hook()
-- function will be invoked by the autograd engine when a gradient becomes ready.
-- each bucket keeps a count of pending gradients. Each post-hook function decrements the count, and
DDP marks a bucket as ready when that count reaches zero.
-- In the next forward pass, DDP replenishes the pending gradient count for every bucket.

- Bucket AllReduce
-- By default, each bucket is 25MB in size.

- Globally Unused Parameters
-- prepare_for_backward() is called at the end of DDP forward pass in distributed.py.
   It traverses the autograd graph to find unused parameters when find_unused_parameters is set to True in DDP constructor.
-- DDP maintains local unused parameter information in a bitmap, and launches an additional AllReduce to gather a global bitmap.
-- all parameters in the model share the same bitmap，没有per-bucket的设计
-- 存在CPU上
-- DDP maintains another bitmap on the same device as the ﬁrst model parameter,
  and invokes a non-blocking copy to move the CPU bitmap to the device bitmap for collective communications.


注册autograd hook

// All variables are expected to have their `grad_fn` set to the gradient
  // accumulation function (since they are leafs in the autograd graph).
  // We store pointers to these functions such that we can check if they are
  // used in an autograd pass. If they are not, we know their grad tensors
  // can be marked as ready for reduction.
  {
    const auto variable_count = params_.size();
    grad_accumulators_.resize(variable_count);
    for (const auto variable_index : c10::irange(variable_count)) {
      auto& variable = params_[variable_index];

      // The gradient accumulator function is lazily initialized once.
      // Therefore we can use its presence in the autograd graph as
      // evidence that the parameter has participated in an iteration.
      auto grad_accumulator = torch::autograd::impl::grad_accumulator(variable);

      using torch::distributed::autograd::ThreadLocalDistAutogradContext;
      // Hook to execute after the gradient accumulator has executed.

     // grad_accumulator 执行完后，autograd_hook 就会运行
      hooks_.emplace_back(
          grad_accumulator->add_post_hook(std::make_unique<
                                          torch::autograd::utils::
                                              LambdaPostHook>(
              [this, variable_index](
                  const torch::autograd::variable_list& outputs,
                  const torch::autograd::variable_list& /* unused */) {
                this->rpc_context_.set(
                    ThreadLocalDistAutogradContext::getContextPtr());
                this->autograd_hook(variable_index);
                return outputs;
              },
              [=](torch::autograd::CompiledNodeArgs& args) {
                TORCH_INTERNAL_ASSERT(
                    "Compiled autograd is not compatible with C++ DDP Reducer, please use torch._dynamo.config.optimize_ddp=\"python_reducer\".");
              })),
          grad_accumulator);

      // Map raw function pointer to parameter index.
      // This is used later on when the autograd graph is traversed
      // to check for parameters for which no gradient is computed, if
      // find_unused_parameters=True.
      // Note that the mapping of gradient accumulator to variable should be
      // one to one as we deduplicate shared parameters before constructing
      // Reducer.
      if (find_unused_parameters_) {
        gradAccToVariableMap_[grad_accumulator.get()] = variable_index;
      }

      numGradHooksTriggeredMap_[variable_index] = 0;

      // The gradient accumulator is stored as weak_ptr in the autograd
      // metadata of the variable, so we have to keep it alive here for
      // the raw pointer to be valid.
      REDUCER_CHECK(
          grad_accumulators_[variable_index] == nullptr,
          logger_,
          c10::str(
              "Reducer tried to register duplicate grad accumulator for variable ",
              variable_index));

      grad_accumulators_[variable_index] = std::move(grad_accumulator);
    }

    std::unordered_map<torch::autograd::Node*, VariableIndex> func_;
    // func_ 存了grad_accumulator & index 的对应，方便我们之后在 autograd graph 寻找 unused parameters

    std::vector<std::vector<std::shared_ptr<torch::autograd::Node>>> grad_accumulators_;
    //  grad_accumulators_ 对应的 index 存了相应的 grad_accumulator

    std::vector<std::pair<uintptr_t, std::shared_ptr<torch::autograd::Node>>> hooks_;


void Reducer::autograd_hook(VariableIndex index) {
     std::lock_guard lock(this->mutex_);
     if (find_unused_parameters_) {
       // 在 no_sync 时，只要参数被用过一次，就会被标记为用过
       // Since it gets here, this param has been used for this iteration. We want
       // to mark it in local_used_maps_. During no_sync session, the same var can
       // be set multiple times, which is OK as does not affect correctness. As
       // long as it is used once during no_sync session, it is marked as used.
       local_used_maps_[index.replica_index][index.variable_index] = 1;
     }

    // Ignore if we don't expect to be called.
    // This may be the case if the user wants to accumulate gradients
    // for number of iterations before reducing them.
    if (!expect_autograd_hooks_) {
      return;
    }

    // Rebuild bucket only if 1) it is the first time to rebuild bucket 2)
    // find_unused_parameters_ is false, currently it does not support when there
    // are unused parameters 3) this backward pass needs to run allreduce. Here,
    // we just dump tensors and their parameter indices into rebuilt_params_ and
    // rebuilt_param_indices_ based on gradient arriving order, and then at the
    // end of finalize_backward(), buckets will be rebuilt based on
    // rebuilt_params_ and rebuilt_param_indices_, and then will be broadcasted
    // and initialized. Also we only need to dump tensors and parameter indices of
    // one replica.
    push_rebuilt_params(index);

    // If `find_unused_parameters_` is true there may be model parameters that
    // went unused when computing the model output, they won't be part of the
    // autograd graph, and won't receive gradients. These parameters are
    // discovered in the `prepare_for_backward` function and their indexes stored
    // in the `unused_parameters_` vector.
    if (!has_marked_unused_parameters_ && find_unused_parameters_) {
      has_marked_unused_parameters_ = true;
      for (const auto& unused_index : unused_parameters_) {
        mark_variable_ready(unused_index);
      }
    }

    // Finally mark variable for which this function was originally called.
    mark_variable_ready(index);
}

- 核心逻辑：如何启动all reduce

struct Bucket {
  std::vector replicas;
    
  // Global indices of participating variables in the bucket
  std::vector<size_t> variable_indices;

  // Number of replicas to be marked done before this bucket is ready.
  // 计数
  size_t pending;

  // Keep work handle around when this set of buckets is being reduced.
  std::shared_ptr<c10d::ProcessGroup::Work> work;

  // Keep future work handle around if DDP comm hook is registered.
  c10::intrusive_ptr<torch::jit::Future> future_work;

  // If this bucket should expect a single sparse gradient.
  // Implies: replicas[i].variables.size() == 1.
  bool expect_sparse_gradient = false;
};

void Reducer::mark_variable_ready(VariableIndex index) {
    const auto replica_index = index.replica_index;
    const auto variable_index = index.variable_index;
    TORCH_CHECK(replica_index < replicas_.size(), "Out of range replica index.");
    TORCH_CHECK(variable_index < variable_locators_.size(), "Out of range variable index.");
    backward_stats_[replica_index][variable_index] = current_time_in_nanos() - backward_stats_base_;
    // 每当变量被标记成 ready 了，都要调用一下 finalize
    require_finalize_ = true;

    const auto& bucket_index = variable_locators_[variable_index];
    auto& bucket = buckets_[bucket_index.bucket_index];
    auto& replica = bucket.replicas[replica_index];


    // If it was scheduled, wait on allreduce in forward pass that tells us
    // division factor based on no. of currently participating processes.
    if (divFactor_ == kUnsetDivFactor) {
      divFactor_ = process_group_->getSize();
      auto& workHandle = forwardPassWorkHandle_.workHandle;
      if (workHandle && !forwardPassWorkHandle_.useStaticWorldSize) {
        workHandle->wait();
        auto results = workHandle->result();
        // Guard against the results being empty
        TORCH_INTERNAL_ASSERT(results.size() > 0);
        at::Tensor& res = results.front();
        divFactor_ = res.item().to<int>();
      }
    }

    if (bucket.expect_sparse_gradient) {
      mark_variable_ready_sparse(index);
    } else {
      mark_variable_ready_dense(index);
    }

    // 检查桶里的变量是不是都ready了，如果没有东西 pending，那就是都 ready了
    if (--replica.pending == 0) {
      if (--bucket.pending == 0) {
        mark_bucket_ready(bucket_index.bucket_index);
      }
    }

    // Run finalizer function and kick off reduction for local_used_maps once the
    // final bucket was marked ready.
    if (next_bucket_ == buckets_.size()) {
      if (find_unused_parameters_) {
        // H2D from local_used_maps_ to local_used_maps_dev_
        for (size_t i = 0; i < local_used_maps_.size(); i++) {
          // We do async H2D to avoid the blocking overhead. The async copy and
          // allreduce respect the current stream, so will be sequenced correctly.
          local_used_maps_dev_[i].copy_(local_used_maps_[i], true);
        }
        local_used_work_ = process_group_->allreduce(local_used_maps_dev_);
      }

      // The autograd engine uses the default stream when running callbacks, so we
      // pass in the current CUDA stream in case it is not the default.
      c10::DeviceType deviceType = replica.contents.device().type();
      const c10::impl::VirtualGuardImpl guard =
          c10::impl::VirtualGuardImpl{deviceType};
      const c10::Stream currentStream =
          guard.getStream(replica.contents.device());
      torch::autograd::Engine::get_default_engine().queue_callback([=] {
        std::lock_guard<std::mutex> lock(this->mutex_);
        // Run callback with the current stream
        c10::OptionalStreamGuard currentStreamGuard{currentStream};
        this->finalize_backward();
      });
    }
}

// Called when the bucket at the specified index is ready to be reduced.
void Reducer::mark_bucket_ready(size_t bucket_index) {
  TORCH_INTERNAL_ASSERT(bucket_index >= next_bucket_);

  // Buckets are reduced in sequence. Ignore this bucket if
  // it's not its turn to be reduced.
  if (bucket_index > next_bucket_) {
    return;
  }

  // Keep going, until we either:
  // - have kicked off reduction for all buckets, or
  // - found a bucket that's not yet ready for reduction.
  for (; next_bucket_ < buckets_.size() && buckets_[next_bucket_].pending == 0;
       next_bucket_++) {
    num_buckets_ready_++;
    if (num_buckets_ready_ == 1 && should_collect_runtime_stats()) {
      record_backward_comm_start_time();
    }
    auto& bucket = buckets_[next_bucket_];
    all_reduce_bucket(bucket);
  }
}



all_reduce_bucket() {
    
}



*** 深入分析DDP和autocast的交互

https://discuss.pytorch.org/t/does-nccl-allreduce-use-fp16/141461/6

- DDP：注册hooks
    - 支持注册python hook
    - 支持注册C++ hook
        - 仅支持 ddp._register_builtin_comm_hook(dist.BuiltinCommHookType.FP16_COMPRESS)
        - AllReduceCommHook、FP16CompressCommHook、_AllReduceBySumCommHook

c10::intrusive_ptr<c10::ivalue::Future> FP16CompressCommHook::runHook(
    GradBucket& bucket) {
  auto compressed_tensor = bucket.getBufferRef().to(torch::kFloat16);
  // Apply the division first to avoid overflow.
  compressed_tensor /= state_->getSize();
  std::vector<at::Tensor> tensors = {compressed_tensor};

  auto allreduce_fut = state_->allreduce(tensors)->getFuture();
  auto decompressed_tensor = bucket.getBufferRef();
  auto decompress = [decompressed_tensor](c10::ivalue::Future& allreduce_fut) {
    auto result = allreduce_fut.value();
    TORCH_INTERNAL_ASSERT(
        result.isTensorList(),
        "ProcessGroup::allreduce should return TensorList");

    auto reduce_tensor = result.toTensorVector()[0];
    TORCH_INTERNAL_ASSERT_DEBUG_ONLY(
        reduce_tensor.scalar_type() == at::ScalarType::Half,
        "Expected reduced tensor to be fp16 in FP16CompressHook, but got type ",
        reduce_tensor.scalar_type());
    decompressed_tensor.copy_(reduce_tensor);
    return c10::IValue(decompressed_tensor);
  };

  return allreduce_fut->then(decompress, allreduce_fut->elementType());
}

- DDP：reduce的dtype取决于bucket.gradients的dtype
    - torch/csrc/distributed/c10d/default_comm_hooks.hpp
    - all_reduce_bucket

- bucket.gradients的dtype取决于bucket的dtype

void Reducer::initialize_buckets(
    std::vector<std::vector<size_t>> bucket_indices) {
    ...
    for (const auto variable_index : bucket_indices[bucket_index]) {
        options = options.dtype(variable.dtype());
        ...
        bucket.gradients = backend->allocateTensor(bucketSize, options);
    }
    ...
}

- bucket的dtype取决于params的dtype
    - Reducer的初始化
    - self.reducer = ...

- backward过程中，从params.grad到bucket.gradients的复制
    - mark_variable_ready_dense -> runGradCallbackForVariable

void Reducer::runGradCallbackForVariable(
    at::Tensor& variable,
    const GradCallback& cb) {
  auto context_ptr = rpc_context_.context_ptr.load();
  if (context_ptr == nullptr) {
    cb(variable.mutable_grad());
  } else {
    // Under distributed autograd
    context_ptr->runGradCallbackForVariable(variable, cb);
  }
}



** 其它


void Reducer::set_mixed_precision_param_dtype(c10::ScalarType dtype) {
  mixed_precision_param_dtype_ = dtype;
  for (auto& bucket : buckets_) {
    bucket.gradients = bucket.gradients.to(dtype);
  }
}




### ProcessGroup.hpp (NCCL, GLOO, MPI, RR)

All ProcessGroup instances construct at the same time by
using a rendezvous service, where the ﬁrst arrival will block
waiting until the last instance joins

For NCCL backend, the ProcessGroup maintains a dedicated set of CUDA streams
for communication, so that communications will not block the computation in the default stream

DistributedDataParallel uses ProcessGroup::broadcast()
to send model states from the process with rank 0 to others during initialization and ProcessGroup::allreduce() to sum gradients.

### torch/csrc/distributed/c10d/ProcessGroupNCCL.cpp

用heartbeat的方式做容错和优雅退出

# round-robin ProcessGroups

PyTorch v1.5 provides a composite round-
robin ProcessGroup implementation, which takes a list of
ProcessGroup instances and dispatches collective communi-
cations to those ProcessGroup instances in a round-robin
manner. By using round-robin ProcessGroups, DDP can at-
tain higher bandwidth utilization if a single NCCL, Gloo, or
MPI ProcessGroup is unable to saturate the link capacity.


# Store.hpp
assists the rendezvous service for process group instances to find each other.

### run.py

逻辑：elastic_launch

命令行启动：利用python的console script

entry_points = {
    "console_scripts": [
        "torchrun = torch.distributed.run:main",
    ],
    "torchrun.logs_specs": [
        "default = torch.distributed.elastic.multiprocessing:DefaultLogsSpecs",
    ],
}

### multiprocessing

pytorch 在 multiprocessing 又加了一个 wrapper 以实现shared memory