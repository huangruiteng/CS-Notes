*** 细节优化算子

torch._foreach_zero_

*** unique

** cpu unique

- aten/src/ATen/native/Unique.cpp
    - sort实现

https://zhuanlan.zhihu.com/p/652659936

** GPU unique

radixsort + scatter