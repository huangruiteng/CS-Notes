### asyncio


# loop_in_executor内部，不能执行async函数

class _AsyncMapDatasetFetcher(_BaseDatasetFetcher):
    def __init__(
        self, dataset: Dataset, auto_collation: bool, collate_fn: Callable, drop_last: bool, num_fetch_workers: int = 1
    ):
        super(_AsyncMapDatasetFetcher, self).__init__(dataset, auto_collation, collate_fn, drop_last)
        # Initialize a thread pool
        self.thread_pool_size = num_fetch_workers
        self._executor = ThreadPoolExecutor(num_fetch_workers)
        # Create a new async event loop
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

    async def worker(self, worker_id: int, task_queue: asyncio.Queue, result_queue: asyncio.Queue) -> None:
        while not task_queue.empty():
            index = await task_queue.get()
            try:
                result = await self.loop.run_in_executor(self._executor, self.dataset.__getitem__, index)
                result_queue.put_nowait((index, result))
            except Exception as e:
                print(f"Exception in fetch worker {worker_id}: {str(e)}")
            finally:
                task_queue.task_done()

    async def initiate_fetch_tasks(self, batch_indices: List[int]) -> List[Tensor]:
        """Creates a list of tasks and initiates their execution using a thread
        pool.

        Arguments:
           batch_indices -- a list of integers which represent the index of an
           item that should be fetched by the dataset
        Returns:
           a list of tensor objects sorted in accordance to the batch_indices order
        """
        # Create input and output queue, task_, result_ to store the tasks and their results (respectively)
        task_queue = asyncio.Queue()
        result_queue = asyncio.Queue()
        # load indexes into a queue
        for index in batch_indices:
            task_queue.put_nowait(index)

        # create tasks and run
        tasks = [asyncio.create_task(self.worker(i, task_queue, result_queue)) for i in range(self.thread_pool_size)]

        # await for results
        await asyncio.gather(*tasks, return_exceptions=True)

        # read the result queue
        result_list = []
        while not result_queue.empty():
            result_list.append(result_queue.get_nowait())

        # sort wrt index
        result_list.sort(key=lambda v: v[0])
        # collate the batch (index 0 are indexes, not necessary after sorting)
        if self.collate_fn is not None:
            return self.collate_fn(result_list)[1]
        return result_list

    @stopwatch(trace_name="(4)-asyncmapdataset-fetcher", trace_level=4)
    def fetch(self, batch_indices: List[int]) -> List[Tensor]:
        """Entrypoint function to async execution. It calls the async function
        initiate_fetch_tasks that uses batch indices to create a list of tasks
        that are performed asynchronously.

        - This fetch function cannot be async itself, otherwise, it would need to be awaited by it's caller.

        Arguments:
           batch_indices -- a list of integers which represent the index of an
           item that should be fetched by the dataset
        Returns:
           a list of tensor objects (fetched items, by the dataset.__getitem__
           and with the predefined transformations applied)
        """
        # create a future that waits for all tasks to complete
        result = self.loop.run_until_complete(self.initiate_fetch_tasks(batch_indices))
        return result


### uvloop

import uvloop
asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())