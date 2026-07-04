*** 控制NumPy底层库创建的线程数量

from os import environ

N_THREADS = "4"
environ["OMP_NUM_THREADS"] = N_THREADS
environ["OPENBLAS_NUM_THREADS"] = N_THREADS
environ["MKL_NUM_THREADS"] = N_THREADS
environ["VECLIB_MAXIMUM_THREADS"] = N_THREADS
environ["NUMEXPR_NUM_THREADS"] = N_THREADS

import numpy as np

import pdb

pdb.set_trace()
x = np.zeros((1024, 1024))


*** print



*** 存储

npy格式存tensor

简单方式也可 file.write(tensor.detach().numpy().astype("float32").tobytes())