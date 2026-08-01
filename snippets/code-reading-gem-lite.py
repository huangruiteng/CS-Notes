也参考 GPU.md —— GemLite

### intro

allow for weight only quantization at 4 and 8 bits,
under asymmetric and symmetric quantization schemes,
32 and 8 bit packing sizes,
as well as grouped and ungrouped quantization


### batch size = 1, a GEMV kernel performs best,

* for packed data, our experiments indicate that **loading scales and zero points only once per two consecutive blocks minimizes redundant operations**. Since these blocks share the same metadata, this approach results in:
  - 5–8% end-to-end inference speedup compared to the default GEMV kernel
  - 30–40% improvement over the traditional Split-K method
  - https://github.com/mobiusml/gemlite/blob/master/gemlite/triton_kernels/gemv_revsplitK_A16fWnO16f_int32packing.py


* For non-packed data, the GEMV_SPLITK algorithm is employed.
 	- This algorithm iterates over the k-dimension to compute the dot product without relying on Triton’s tl.dot.
	- https://github.com/mobiusml/gemlite/blob/master/gemlite/triton_kernels/gemv_splitK_A16fWnO16f_int32packing.py


### batch size 2-64
* GEMV_SPLITK 

during Split-K tuning, configurations are selected only if K is divisible by BLOCK_SIZE_K × SPLIT_K,,
and BLOCKS_SIZE_K is further pruned based on the group-size value. This approach ensures both efficiency and correctness in kernel operation.

### batch_size > 64
* GEMM ( depending on the matrix shape and the device.)


### 基于torch custom op，和torch.compile更紧密
https://pytorch.org/tutorials/advanced/python_custom_ops.html

This integration allows advanced features such as pre-hooks and early configuration pruning to function correctly,、

相关issue：https://github.com/pytorch/pytorch/issues/139059