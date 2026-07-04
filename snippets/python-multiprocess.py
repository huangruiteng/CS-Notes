### GIL

https://opensource.com/article/17/4/grok-gil

### consumer-producer

- 基础实现：https://stackoverflow.com/questions/67363793/correct-way-to-implement-producer-consumer-pattern-in-python-multiprocessing-pool
  - 解决logging死锁：
    - 工业版 https://blog.csdn.net/weixin_68789096/article/details/135546285
      - python的进程池是基于fork实现的，当我们只使用fork()创建子进程而不是用execve()来替换进程上下文时，需要注意一个问题：fork()出来的子进程会和父进程共享内存空间，除了父进程所拥有的线程。父进程中的子线程并没有被fork到子进程中，而这正是导致死锁的原因:
      - 当父进程中的线程要向队列中写log时，它需要获取锁。如果恰好在获取锁后进行了fork操作，那这个锁也会被带到子进程中，同时这个锁的状态是占用中。这时候子进程要写日志的话，也需要获取锁，但是由于锁是占用状态，导致永远也无法获取，至此，死锁产生。                       
    - 基础版：https://blog.51cto.com/u_16175479/8903194
  - 解决consumer退出：不要用JoinableQueue，用Manager().Queue()
   - https://stackoverflow.com/questions/45866698/multiprocessing-processes-wont-join


import queue
import random
from multiprocessing import Process, set_start_method, Manager # JoinableQueue


def consumer(q: Queue):
    while True:
        try:
            res = q.get(block=False)
            print(f'Consume {res}')
            q.task_done()
        except queue.Empty:
            pass


def producer(q: Queue, food):
    for i in range(2):
        res = f'{food} {i}'
        print(f'Produce {res}')
        q.put(res)
    q.join()


if __name__ == "__main__":
    set_start_method('spawn')
    foods = ['apple', 'banana', 'melon', 'salad']
    jobs = 2
    q = Manager().Queue(maxsize=1024)

    producers = [
        Process(target=producer, args=(q, random.choice(foods)))
        for _ in range(jobs)
    ]

    # daemon=True is important here
    consumers = [
        Process(target=consumer, args=(q, ), daemon=True)
        for _ in range(jobs * 2)
    ]

    # + order here doesn't matter
    for p in consumers + producers:
        p.start()

    for p in producers:
        p.join()