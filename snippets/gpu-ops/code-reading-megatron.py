
连续进行两个互相垂直的切分, ColumnParallelLinear 和 RowParallelLinear, 相邻的 Column+Row 可以消去中间的 allgather.
https://github.com/NVIDIA/Megatron-LM/blob/main/megatron/core/tensor_parallel/layers.py