### 基础操作

from threading import Barrier, Thread

Barrier可以传入executor.map的fn中
num = 3
sb = Barrier(num)
with ThreadPoolExecutor(num) as ex: list(ex.map(lambda i: g(i,sb), range(1,num+1)))


### example


import threading
import time

def download_from_hdfs():
    if not hasattr(download_from_hdfs, "counter"):
        download_from_hdfs.counter = 0
    download_from_hdfs.counter += 1
    time.sleep(1)
    counter = download_from_hdfs.counter
    return [f"model_{counter}"], counter

def thread_A(lock):
    global latest_version, models
    while True:
        tmp_models, tmp_latest_version = download_from_hdfs()
        with lock:
            models, latest_version = tmp_models, tmp_latest_version

def thread_B(lock):
    global latest_version, models
    while True:
        with lock:
            # Access the global variables directly
            if models:
                print("Latest model: {}, version: {}".format(models[-1], latest_version))
            else:
                print("No models available.")
        time.sleep(2)

if __name__ == "__main__":
    lock = threading.Lock()

    models = []
    latest_version = 0

    t1 = threading.Thread(target=thread_A, args=(lock,))
    t2 = threading.Thread(target=thread_B, args=(lock,))

    t1.start()
    t2.start()

    t1.join()
    t2.join()