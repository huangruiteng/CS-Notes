utils/data

### datasets.py

class IterableDataset(Dataset[T_co]):
    def __iter__(self) -> Iterator[T_co]:
        raise NotImplementedError("Subclasses of IterableDataset should implement __iter__.")

    def __add__(self, other: Dataset[T_co]):
        return ChainDataset([self, other])

torch.utils.data.ConcatDataset: 用于连接多个 ConcatDataset 数据集
 
torch.utils.data.ChainDataset : 用于连接多个 IterableDataset 数据集，在 IterableDataset 的 __add__() 方法中被调用
 
torch.utils.data.Subset: 用于获取指定一个索引序列对应的子数据集


# 支持多个tensor，一次返回所有tensor的第i行
class TensorDataset(Dataset):
    def __init__(self, *tensor):
        assert all(tensors[0].size(0) == tensor.size(0) for tensor in tensors)
        self.tensors = tensors

    def __getitem__(self, index):
        return tuple(tensor[index] for tensor in tensors

    def __len__(self):
        return self.tensors[0].size(0)

### _utils/worker.py


# worker_loop被DataLoader的多进程类使用
# 子进程fetcher封装的业务逻辑：dataset、collate_fn
def _worker_loop(
    dataset_kind,
    dataset,
    index_queue,
    data_queue,
    done_event,
    auto_collation,
    collate_fn,
    drop_last,
    base_seed,
    init_fn,
    worker_id,
    num_workers,
    persistent_workers,
    shared_seed,
):

	if init_fn is not None:  # 调用init_fn
	    init_fn(worker_id)

	# 生成一个fetcher
	fetcher = _DatasetKind.create_fetcher(
	    dataset_kind, dataset, auto_collation, collate_fn, drop_last)     # collate_fn：组batch；  auto_collation：dataset内做batch的时候告诉外层，设为True

	watchdog = ManagerWatchdog()

		class ManagerWatchdog:  # type: ignore[no-redef]
	        def __init__(self) -> None:
	            self.manager_pid = os.getppid()
	            self.manager_dead = False

	        def is_alive(self):
	            if not self.manager_dead:
	                self.manager_dead = os.getppid() != self.manager_pid
	            return not self.manager_dead


	while watchdog.is_alive():
	    try:
	        # 在一般情况下， r的数据类型是: tuple[int, list[Any]]
	        # 其中int是全局batch_index; list[Any]是dataset中样本的index
	        r = index_queue.get(timeout=MP_STATUS_CHECK_INTERVAL)
	    except queue.Empty:
	        continue
	    # 先处理三种特殊情况： 1) 新epoch; 2) 通过r is None主动退出；3）通过done_event延迟退出
	    if isinstance(r, _ResumeIteration):
	        # 用于开启一个新的epoch, 返回None, 并重新构造一个fetcher
	        data_queue.put((r, None))
	        iteration_end = False
	        fetcher = _DatasetKind.create_fetcher(
	            dataset_kind, dataset, auto_collation, collate_fn, drop_last)
	        continue
	    elif r is None:  # None是退出标志，这里会check done_event
	        assert done_event.is_set() or iteration_end
	        break
	    elif done_event.is_set() or iteration_end:
	        continue
	    
	    # 读取数据正常，解出r, 其中index 是一个list, len(index) = batch_size, 对于IteratorDataset
	    # 基值都是None, 对于其它dataset, 这个index可以直接从dataset取值


	    # idx：第几个mini-batch,可能乱序（如果shuffle）
	    # index：mini-batch中包含哪些行
	    idx, index = r  
	    data: Union[_IterableDatasetStopIteration, ExceptionWrapper]
	    if init_exception is not None:
	        data = init_exception
	        init_exception = None
	    else:
	        try:
	            data = fetcher.fetch(index)  # 事实上返回的是一个mini-batch, 不是一行
	        except Exception as e:
	            if isinstance(e, StopIteration) and dataset_kind == _DatasetKind.Iterable:
	                data = _IterableDatasetStopIteration(worker_id)
	                iteration_end = True
	            else:
	                data = ExceptionWrapper(where=f"in DataLoader worker process {worker_id}")
	    data_queue.put((idx, data))


### shutdown逻辑

See NOTE [ Data Loader Multiprocessing Shutdown Logic ]

### _utils/fetch.py

class _IterableDatasetFetcher(_BaseDatasetFetcher):
    def __init__(self, dataset, auto_collation, collate_fn, drop_last):
        super().__init__(dataset, auto_collation, collate_fn, drop_last)
        self.dataset_iter = iter(dataset)
        self.ended = False

    def fetch(self, possibly_batched_index):
        if self.ended:
            raise StopIteration

        if self.auto_collation:
            data = []
            for _ in possibly_batched_index:
                try:
                    data.append(next(self.dataset_iter))
                except StopIteration:
                    self.ended = True
                    break
            if len(data) == 0 or (
                self.drop_last and len(data) < len(possibly_batched_index)
            ):
                raise StopIteration
        else:
            data = next(self.dataset_iter)
        return self.collate_fn(data)


class _MapDatasetFetcher(_BaseDatasetFetcher):
    def fetch(self, possibly_batched_index):
        if self.auto_collation:
            if hasattr(self.dataset, "__getitems__") and self.dataset.__getitems__:
                data = self.dataset.__getitems__(possibly_batched_index)
            else:
                data = [self.dataset[idx] for idx in possibly_batched_index]
        else:
            data = self.dataset[possibly_batched_index]
        return self.collate_fn(data)

当关闭自动批处理 (automatic batching) 时，collate_fn 作用于单个数据样本，只是在 PyTorch 张量中转换 NumPy 数组。
_utils.collate.default_convert
当开启自动批处理 (automatic batching) 时，collate_fn 作用于数据样本列表，将输入样本整理为一个 batch，一般做下面 3 件事情
_utils.collate.default_collate
- 添加新的批次维度（一般是第一维）
- 它会自动将 NumPy 数组和 Python 数值转换为 PyTorch 张量
- 它保留数据结构，例如，如果每个样本都是 dict，则输出具有相同键集但批处理过的张量作为值的字典（或list，当不能转换的时候）。list, tuples, namedtuples 同样适用



### dataloader.py

# dataloader

torch dataloader的问题：
1）全同步训练场景，无法graceful shutdown；
--> 用all reduce时loss*0的方法
2）rank*worker_num，需要文件分发机制



Data loader combines a dataset and a sampler, and provides an iterable over the given dataset.

对于 map-style 数据，主线程会用 Sampler 产生 indice，并将它们送到 worker 里。因此，shuffle是在主线程做的
对于 iterable-style 数据，因为每个 worker 都有相同的 data 复制样本，并在各个进程里进行不同的操作，以防止每个进程输出的数据不是重复的，
所以一般用torch.utils.data.get_worker_info() 来进行辅助处理。

注意，通常不建议在多进程加载中返回CUDA张量，因为在使用CUDA和在多处理中共享CUDA张量时存在许多微妙之处
（文档中提出：只要接收进程保留张量的副本，就需要发送进程来保留原始张量）。
可能和“Another unique feature of this system is that it transparently handles sharing of CUDA tensors, 
making it easy to implement techniques like Hogwild [42].” 有关

建议采用 pin_memory=True ，以将数据快速传输到支持CUDA的GPU。简而言之，不建议在使用多线程的情况下返回CUDA的tensor。

class DataLoader(Generic[T_co]):
    ...
    def __iter__(self) -> '_BaseDataLoaderIter':

        if self.persistent_workers and self.num_workers > 0:
            if self._iterator is None:
                self._iterator = self._get_iterator()
            else:
                self._iterator._reset(self) # reset好像没啥用
            return self._iterator
        else:
            return self._get_iterator()


    def _get_iterator(self) -> '_BaseDataLoaderIter':
        if self.num_workers == 0:
            return _SingleProcessDataLoaderIter(self)
        else:
            self.check_worker_number_rationality()
            return _MultiProcessingDataLoaderIter(self)

    @property
    def _auto_collation(self):
        return self.batch_sampler is not None

    @property
    def _index_sampler(self):
        if self._auto_collation:
            return self.batch_sampler
        else:
            return self.sampler

if sampler is None:  # give default samplers
  if self._dataset_kind == _DatasetKind.Iterable:
      # See NOTE [ Custom Samplers and IterableDataset ]
      # IterableDataset 不支持用户自定义 batch_sampler 或sampler,发送的全是None
      sampler = _InfiniteConstantSampler()
  else:  # map-style
      if shuffle:
          sampler = RandomSampler(dataset, generator=generator)  # type: ignore[arg-type]
      else:
          sampler = SequentialSampler(dataset)  # type: ignore[arg-type]


### Sampler: sampler.py

batch_sampler也是一个迭代器， 它会从sampler中依次取出下标，关组成一个mini-batch, 一次返回一个batch_size长度的下标list
- 当指定了batch_size, 又没有指定batch_sampler时， 系统会给一个默认的batch_sampler

torch.utils.data.SequentialSampler : 顺序采样样本，始终按照同一个顺序
torch.utils.data.RandomSampler: 可指定有无放回地，进行随机采样样本元素
torch.utils.data.SubsetRandomSampler: 无放回地按照给定的索引列表采样样本元素
torch.utils.data.WeightedRandomSampler: 按照给定的概率来采样样本。样本元素来自 [0,…,len(weights)-1] ， 给定概率（权重）
torch.utils.data.BatchSampler: 在一个batch中封装一个其他的采样器, 返回一个 batch 大小的 index 索引
torch.utils.data.DistributedSample: 将数据加载限制为数据集子集的采样器。与 torch.nn.parallel.DistributedDataParallel 结合使用。 在这种情况下，每个进程都可以将 DistributedSampler 实例作为 DataLoader 采样器传递


class RandomSampler
def __iter__:
	if self.replacement:
    for _ in range(self.num_samples // 32):
        yield from torch.randint(
            high=n, size=(32,), dtype=torch.int64, generator=generator
        ).tolist()
    yield from torch.randint(
        high=n,
        size=(self.num_samples % 32,),
        dtype=torch.int64,
        generator=generator,
    ).tolist()
else:
    for _ in range(self.num_samples // n):
        yield from torch.randperm(n, generator=generator).tolist()
    yield from torch.randperm(n, generator=generator).tolist()[
        : self.num_samples % n
    ]


SubsetRandomSampler
WeightedRandomSampler

DistributedSampler

epoch影响随机性

sampler = DistributedSampler(dataset) if is_distributed else None
loader = DataLoader(dataset, shuffle=(sampler is None), sampler=sampler)
for epoch in range(start_epoch, n_epochs):
    if is_distributed:
        sampler.set_epoch(epoch)
    train(loader)


### DataLoaderIter

_SingleProcessDataLoaderIter

class _BaseDataLoaderIter:
  def _next_index(self):
      return next(self._sampler_iter)  # may raise StopIteration

  def _reset(self, loader, first_iter=False):
        self._sampler_iter = iter(self._index_sampler)
        ...

  def _next_data(self):
      raise NotImplementedError


  # 在 _sampler_iter 为 None 的情况下，会调用 _reset 方法来重置迭代器的状态
  def __next__(self) -> Any:
        with torch.autograd.profiler.record_function(self._profile_name):
            if self._sampler_iter is None:
                # TODO(https://github.com/pytorch/pytorch/issues/76750)
                self._reset()  # type: ignore[call-arg]
            data = self._next_data()
            self._num_yielded += 1
            ...
            return data


class _SingleProcessDataLoaderIter(_BaseDataLoaderIter):
    def __init__(self, loader):
        super().__init__(loader)
       	...
        self._dataset_fetcher = _DatasetKind.create_fetcher(
            self._dataset_kind,
            self._dataset,
            self._auto_collation,
            self._collate_fn,
            self._drop_last,
        )

    def _next_data(self):
        index = self._next_index()  # may raise StopIteration
        data = self._dataset_fetcher.fetch(index)  # may raise StopIteration
        if self._pin_memory:
            data = _utils.pin_memory.pin_memory(data, self._pin_memory_device)
        return data


# pin memory

  def pin_memory(data):
    if isinstance(data, torch.Tensor):
        return data.pin_memory()
    elif isinstance(data, string_classes):
        return data
    elif isinstance(data, container_abcs.Mapping):
        return {k: pin_memory(sample) for k, sample in data.items()}
    elif isinstance(data, tuple) and hasattr(data, '_fields'):  # namedtuple
        return type(data)(*(pin_memory(sample) for sample in data))
    elif isinstance(data, container_abcs.Sequence):
        return [pin_memory(sample) for sample in data]
    elif hasattr(data, "pin_memory"):
        return data.pin_memory()
    else:
        return data


[ worker processes ]
  While loader process is alive:
    Get from `index_queue`.
      If get anything else,
         Check `workers_done_event`.
           If set, continue to next iteration
                   i.e., keep getting until see the `None`, then exit.
           Otherwise, process data:
               If is fetching from an `IterableDataset` and the iterator
                   is exhausted, send an `_IterableDatasetStopIteration`
                   object to signal iteration end. The main process, upon
                   receiving such an object, will send `None` to this
                   worker and not use the corresponding `index_queue`
                   anymore.
      If timed out,
         No matter `workers_done_event` is set (still need to see `None`)
         or not, must continue to next iteration.
  (outside loop)
  If `workers_done_event` is set,  (this can be False with `IterableDataset`)
    `data_queue.cancel_join_thread()`.  (Everything is ending here:
                                         main process won't read from it;       '
                                         other workers will also call
                                         `cancel_join_thread`.)

[ pin_memory_thread ]
  # No need to check main thread. If this thread is alive, the main loader
  # thread must be alive, because this thread is set as daemonic.
  While `pin_memory_thread_done_event` is not set:
    Get from `worker_result_queue`.
      If timed out, continue to get in the next iteration.
      Otherwise, process data.
      While `pin_memory_thread_done_event` is not set:
        Put processed data to `data_queue` (a `queue.Queue` with blocking put)
        If timed out, continue to put in the next iteration.
        Otherwise, break, i.e., continuing to the out loop.

  NOTE: we don't check the status of the main thread because      '
          1. if the process is killed by fatal signal, `pin_memory_thread`
             ends.
          2. in other cases, either the cleaning-up in __del__ or the
             automatic exit of daemonic thread will take care of it.
             This won't busy-wait either because `.get(timeout)` does not       '
             busy-wait.

[ main process ]
  In the DataLoader Iter's `__del__`       '
    b. Exit `pin_memory_thread`
         i.   Set `pin_memory_thread_done_event`.
         ii   Put `None` in `worker_result_queue`.
         iii. Join the `pin_memory_thread`.
         iv.  `worker_result_queue.cancel_join_thread()`.

    c. Exit the workers.
         i.   Set `workers_done_event`.
         ii.  Put `None` in each worker's `index_queue`.     '
         iii. Join the workers.
         iv.  Call `.cancel_join_thread()` on each worker's `index_queue`.    '

       NOTE: (c) is better placed after (b) because it may leave corrupted
             data in `worker_result_queue`, which `pin_memory_thread`
             reads from, in which case the `pin_memory_thread` can only
             happen at timing out, which is slow. Nonetheless, same thing
             happens if a worker is killed by signal at unfortunate times,
             but in other cases, we are better off having a non-corrupted
             `worker_result_queue` for `pin_memory_thread`.

  NOTE: If `pin_memory=False`, there is no `pin_memory_thread` and (b)
        can be omitted


class _MultiProcessingDataLoaderIter(_BaseDataLoaderIter):
    

	(_send_idx, index)进入index queue
	(_send_idx, data)进入data queue

    def __init__(self, loader):
        super(_MultiProcessingDataLoaderIter, self).__init__(loader)
        self._rcvd_idx = 0 表示下一个要在 __next__ 方法中返回的任务的索引。它跟踪了主进程期望从工作进程接收的下一个数据批次的顺序。
        self._send_idx = 0 表示下一个要发送给工作进程的任务的索引。它记录了主进程已经发送出去的任务的编号，用于跟踪任务的发送进度。

        # information about data not yet yielded, i.e., tasks w/ indices in range [rcvd_idx, send_idx).
        # map: task idx => - (worker_id,)        if data isn't fetched (outstanding)
        #                  \ (worker_id, data)   if data is already fetched (out-of-order)
        self._task_info = {}

        ...
        self._worker_result_queue = multiprocessing_context.Queue()  # 把该worker取出的数放入该队列，用于进程间通信
        ...
        self._workers_done_event = multiprocessing_context.Event()

        self._index_queues = []
        self._workers = []
        for i in range(self._num_workers):
            index_queue = multiprocessing_context.Queue()  # 索引队列，每个子进程一个队列放要处理的下标
            index_queue.cancel_join_thread() # See sections (2) and (3b) above. -> 确保 3.b b. A process(loader process) won't hang when putting into a queue;

            # _worker_loop 的作用是：从index_queue中取索引，然后通过collate_fn处理数据，
            # 然后再将处理好的 batch 数据放到 data_queue 中。（发送到队列中的idx是self.send_idx）
            w = multiprocessing_context.Process(
                target=_utils.worker._worker_loop,  # 每个worker子进程循环执行的函数，主要将数据以(idx, data)的方式传入_worker_result_queue中
                args=(self._dataset_kind, self._dataset, index_queue, 
                      self._worker_result_queue, self._workers_done_event,
                      self._auto_collation, self._collate_fn, self._drop_last,
                      self._base_seed + i, self._worker_init_fn, i, self._num_workers,
                      self._persistent_workers))
            w.daemon = True
            w.start()
            self._index_queues.append(index_queue)
            self._workers.append(w)

        if self._pin_memory:
            self._pin_memory_thread_done_event = threading.Event()

            self._data_queue = queue.Queue()  # 用于存取出的数据进行 pin_memory 操作后的结果
            pin_memory_thread = threading.Thread(
                target=_utils.pin_memory._pin_memory_loop,
                args=(self._worker_result_queue, self._data_queue,
                      torch.cuda.current_device(),
                      self._pin_memory_thread_done_event))
            pin_memory_thread.daemon = True
            pin_memory_thread.start()
            # Similar to workers (see comment above), we only register
            # pin_memory_thread once it is started.
            self._pin_memory_thread = pin_memory_thread
        else:
            self._data_queue = self._worker_result_queue
        ...
        self._reset(loader, first_iter=True)

	def _next_data(self):
        while True:
            这里可能丢数据？没有提示    

            # If the worker responsible for `self._rcvd_idx` has already ended
            # and was unable to fulfill this task (due to exhausting an `IterableDataset`),
            # we try to advance `self._rcvd_idx` to find the next valid index.
            #
            # This part needs to run in the loop because both the `self._get_data()`
            # call and `_IterableDatasetStopIteration` check below can mark
            # extra worker(s) as dead.
            while self._rcvd_idx < self._send_idx:
                info = self._task_info.get(self._rcvd_idx, None)
                if info:
                    worker_id = info[0]
                    if (
                        len(info) == 2 or self._workers_status[worker_id]
                    ):  # has data or is still active
                        break
                    del self._task_info[self._rcvd_idx]
                self._rcvd_idx += 1
            else:
                # no valid `self._rcvd_idx` is found (i.e., didn't break)
                if not self._persistent_workers:
                    self._shutdown_workers()
                raise StopIteration

            # Now `self._rcvd_idx` is the batch index we want to fetch

            # Check if the next sample has already been generated
            if len(self._task_info[self._rcvd_idx]) == 2:
                data = self._task_info.pop(self._rcvd_idx)[1]
                self._rcvd_idx += 1
                return self._process_data(data)

            assert not self._shutdown and self._tasks_outstanding > 0
            idx, data = self._get_data()
            self._tasks_outstanding -= 1
            if self._dataset_kind == _DatasetKind.Iterable:
                # Check for _IterableDatasetStopIteration
                if isinstance(data, _utils.worker._IterableDatasetStopIteration):
                    if self._persistent_workers:
                        self._workers_status[data.worker_id] = False
                    else:
                        self._mark_worker_as_unavailable(data.worker_id)
                    self._try_put_index()
                    continue

            if idx != self._rcvd_idx:
                if not self._in_order:
                    # don't store it for later, process now
                    del self._task_info[idx]
                    return self._process_data(data)
                # store out-of-order samples
                self._task_info[idx] += (data,)
            else:
                del self._task_info[idx]
                self._rcvd_idx += 1
                return self._process_data(data)

	def _try_put_index(self):
        assert self._tasks_outstanding < self._prefetch_factor * self._num_workers

        try:
            index = self._next_index()
        except StopIteration:
            return
        for _ in range(self._num_workers):  # find the next active worker, if any
            worker_queue_idx = next(self._worker_queue_idx_cycle)
            if self._workers_status[worker_queue_idx]:
                break
        else:
            # not found (i.e., didn't break)
            return

        self._index_queues[worker_queue_idx].put((self._send_idx, index))  # type: ignore[possibly-undefined]
        self._task_info[self._send_idx] = (worker_queue_idx,)
        self._tasks_outstanding += 1
        self._send_idx += 1



    # 当从队列中获取一个批次的数据后，会调用 _process_data 方法，该方法会再次调用 _try_put_index 来保持预取队列的填充状态。
    def _process_data(self, data):
        self._try_put_index()
        if isinstance(data, ExceptionWrapper):
            data.reraise()
        return data


    def _reset(self, loader, first_iter=False):
        super()._reset(loader, first_iter)
        self._send_idx = 0 
        self._rcvd_idx = 0

        self._task_info = {}

        # _tasks_outstanding 指示当前已经准备好的 task/batch 的数量（可能有些正在准备中）
        # 初始值为 0, 在 self._try_put_index() 中 +1,在 self._next_data 中-1
        self._tasks_outstanding = 0

        self._workers_status = [True for i in range(self._num_workers)] 
        # We resume the prefetching in case it was enabled
        if not first_iter:
            for idx in range(self._num_workers):
                self._index_queues[idx].put(_utils.worker._ResumeIteration())
            resume_iteration_cnt = self._num_workers
            while resume_iteration_cnt > 0:
                data = self._get_data()
                if isinstance(data, _utils.worker._ResumeIteration):
                    resume_iteration_cnt -= 1
        ...
        # 初始化的时候，就将 2*num_workers 个 (batch_idx, sampler_indices) 放到 index_queue 中, 作为预取的buffer
        for _ in range(self._prefetch_factor * self._num_workers):
            self._try_put_index() # 进行预取


# NOTE [ Data Loader Multiprocessing Shutdown Logic ]
    #
    # Preliminary:
    #
    # Our data model looks like this (queues are indicated with curly brackets):
    #
    #                main process                              ||
    #                     |                                    ||
    #               {index_queue}                              ||
    #                     |                                    ||
    #              worker processes                            ||     DATA
    #                     |                                    ||
    #            {worker_result_queue}                         ||     FLOW
    #                     |                                    ||
    #      pin_memory_thread of main process                   ||   DIRECTION
    #                     |                                    ||
    #               {data_queue}                               ||
    #                     |                                    ||
    #                data output                               \/
    #
    # P.S. `worker_result_queue` and `pin_memory_thread` part may be omitted if
    #      `pin_memory=False`.

设计目标：
1. The iterator gracefully exits the workers when its last reference is gone or it is depleted.
--> we implement the shutdown logic in `__del__` of DataLoaderIterator.
--> `workers_done_event`

2. The iterator exits the workers when the loader process and/or worker processes exits normally or with error.
--> We set all workers and `pin_memory_thread` to have `daemon=True`.

3. All processes exit if any of them die unexpectedly by fatal signals.
a. A process won't hang when getting from a queue.
b. A process won't hang when putting into a queue;
--> 


# 关于 num_workers的工作原理:

开启num_workers个子进程(worker)。
每个worker通过主进程获得自己需要采集的ids。
ids的顺序由采样器（sampler）或shuffle得到。然后每个worker开始采集一个batch的数据。(因此增大num_workers的数量，内存占用也会增加。因为每个worker都需要缓存一个batch的数据）
在第一个worker数据采集完成后，会卡在这里，等着主进程把该batch取走，然后采集下一个batch。
主进程运算完成，从第二个worker里采集第二个batch，以此类推。
主进程采集完最后一个worker的batch。此时需要回去采集第一个worker产生的第二个batch。如果第一个worker此时没有采集完，主线程会卡在这里等。（这也是为什么在数据加载比较耗时的情况下，每隔num_workers个batch，主进程都会在这里卡一下。）

所以:
如果内存有限，过大的num_workers会很容易导致内存溢出。
可以通过观察是否每隔num_workers个batch后出现长时间等待来判断是否需要继续增大num_workers。如果没有明显延时，说明读取速度已经饱和，不需要继续增大。反之，可以通过增大num_workers来缓解。
如果性能瓶颈是在io上，那么num_workers超过(cpu核数*2)是有加速作用的。但如果性能瓶颈在cpu计算上，继续增大num_workers反而会降低性能。(因为现在cpu大多数是每个核可以硬件级别支持2个线程。超过后，每个进程都是操作系统调度的，所用时间更长）


# 关于缓存2*worker_num batch

所有的 worker 进程最多缓存的 batch 数量就是 2 x self.num_workers 个。
* 在初始化 dataloader 的时候，我们一共放了 2 x self.num_workers 个 batch 的 index 到 index_queue。
* dataloader 只会在每次迭代成功的时候才会放入新的 index 到 index_queue 

参考 _reset函数

————————————————
                        
原文链接：https://blog.csdn.net/ytusdc/article/details/128517308
