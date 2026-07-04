*** intro

- speed-first
- 依赖torch.compile做算子优化
- With Tensor Subclass, we extend PyTorch native Tensor abstractions and model quantization as dtype conversion, 
    while different packing formats for custom kernels are handled through layouts.
- with tinygemm or GemLite kernel implementations
- compatibility with tensor parallel, torch.compile, and other PyTorch features.

tutorial: https://pytorch.org/ao/stable/quick_start.html
README: https://github.com/pytorch/ao/blob/main/torchao/quantization/README.md
CONTRIBUTOR：https://pytorch.org/ao/stable/contributor_guide.html

* https://github.com/pytorch-labs/ao
- Current best way to access all the pytorch native gpu quantization work,
- Used by sdxl-fast and segment-anything-fast

* https://github.com/pytorch-labs/gpt-fast
- (has GPTQ support for int4)
- Best for weight only quant

* https://github.com/pytorch-labs/segment-anything-fast
- Best for dynamic quant

* https://gist.github.com/HDCharles/287ac5e997c7a8cf031004aad0e3a941 ■ triton microbenchmarks

TorchAOBaseTensor参考code-reading-pytorch-utils.py

e.g. int4 quantized tensor
- dtype: int4 AffineQuantizedTensor
- layout: TensorCoreTiledLayout/GemlitePackedLayout

* [Keynote talk at GPU MODE IRL](https://youtu.be/FH5wiwOyPX4?si=VZK22hHz25GRzBG1&t=1009)
* [Low precision dtypes at PyTorch conference](https://youtu.be/xcKwEZ77Cps?si=7BS6cXMGgYtFlnrA)
* [Slaying OOMs at the Mastering LLM's' course](https://www.youtube.com/watch?v=UvRl4ansfCg)
* [Advanced Quantization at CUDA MODE](https://youtu.be/1u9xUK3G4VM?si=4JcPlw2w8chPXW8J)
* [Chip Huyen's' GPU Optimization Workshop](https://www.youtube.com/live/v_q2JTIqE20?si=mf7HeZ63rS-uYpS6)
* [Cohere for AI community talk](https://www.youtube.com/watch?v=lVgrE36ZUw0)




*** 支持哪些量化？

- int4_weight_only quantization：it’s a 4 bit groupwise quantization with group size of 64, using tinygemm kernel
- gemlite_uintx_weight_only：4 means 4 bit, and 64 is also the group size, using GemLite kernel
- float8_dynamic_activation_float8_weight： quantization in TorchAO, both activation and weights are quantized with per row scales

- fp6 weight only(fp16/bf16 model): Torchao/dtypes/floatx



### serialization
Save and load quantized weights into a state_dict just like a floating point model, 
eliminating the need to transform floating point model to quantized model before the quantized weights are loaded. 
This reduces friction of distributing and deploying quantized models.


### Tensor Parallel Support
quantize the model first then distribute the Tensor
QuantizedTensor should support the operators called when constructing a DTensor, including slice and view ops
pack and slice operation should commute, otherwise the packing format is not compatible with tensor parallelism.

### GemLite

quantize_(model, gemlite_uintx_weight_only(group_size, bit_width, packing_bitwidth))


### float 8 (fp8)
https://github.com/pytorch-labs/float8_experimental

FBGEMM-fp8-rowwise: https://github.com/pytorch/FBGEMM/commit/1b5a7018a935f6ffbe29898e3413b36df5843521



### dynamic quantization

from torchao.quantization import apply_dynamic_quant
import copy
model2 = copy.deepcopy(model)
apply_dynamic_quant(model2)
torch.__inductor.config.force_fuse_int_mm_with_mul = True
model_c = torch.compile(model2, mode='max-autotune')
model_c(image)


config.force_fuse_int_mm_with_mul -> 对int8 matmul和pointwise scale操作进行fusion

def tuned_fused_int_mm_mul(mat1, mat2, mat3, out_dtype, *, layout=None):
    out_dtype = (
        torch.promote_types(mat3.get_dtype(), torch.int32)
        if out_dtype is None
        else out_dtype
    )
    m, n, k, layout, mat1, mat2, mat3 = mm_args(
        mat1, mat2, mat3, layout=layout, out_dtype=out_dtype
    )

    def mul_epilogue(v1, v2):
        return V.ops.mul(v1, v2)

    choices: List[Dict[Any, Any]] = []
    for config in int8_mm_configs(
        m, n, k, **mm_config_kwargs(ir.get_device_type(mat1))
    ):
        mm_template.maybe_append_choice(
            choices,
            input_nodes=(mat1, mat2, mat3),
            layout=layout,
            **dict(mm_options(config, m, n, k, layout), ACC_TYPE="tl.int32"),
            suffix_args=1,
            epilogue_fn=mul_epilogue,
        )
    return autotune_select_algorithm("int_mm", choices, [mat1, mat2, mat3], layout)


# 8da4w quantization
mixed 4-bit/8-bit GEMM is added in cutlass.
https://github.com/NVIDIA/cutlass/pull/1413


### weight-only quantization

from torchao.quantization import apply_weight_only_int8_quant
import copy
model2 = copy.deepcopy(model)
apply_weight_only_int8_quant(model2)
torch.__inductor.config.use_mixed_mm = True
model_c = torch.compile(model2, mode='max-autotune')
model_c(image)


torch/_inductor/kernel/mm.py

mm_template

TritonTemplate(...)
	if B_PROLOGUE_CAST_TYPE is not None:
     b = b.to(B_PROLOGUE_CAST_TYPE)

### int4

_inductor/kernel/unpack_mixed_mm.py
性能差

--> _convert_weight_to_int4pack

triton缺点：
L2 cache optimization, quantization时不好弄;
config heuristic

# int4 weight mm kernel with bitpacking
https://github.com/pytorch/pytorch/blob/v2.3.1/aten/src/ATen/native/cuda/int4mm.cu#L865

integrated in torchao https://github.com/pytorch/ao/pull/383



# int4 CPULayout
https://github.com/pytorch/ao/pull/1278/files
https://github.com/pytorch/ao/issues/1117#issuecomment-2451252756.


# decompostion.py

基于 量化+triton，优化weighted sumpooling。 这样写之后，triton op会每列一个线程，速度快

config.coordinate_descent_tuning
if guard_size_oblivious(self.shape[0] == 1) or guard_size_oblivious(
            input2.shape[1] == 1
        ):
   return (self.unsqueeze(2) * input2.unsqueeze(0)).sum(dim=1)



### QAT

api: https://github.com/pytorch/ao/tree/main/torchao/quantization/qat
distributed training: https://pytorch.org/blog/quantization-aware-training/#fine-tuning-with-torchtune
- tune run --nproc_per_node 8 qat_distributed --config llama3/8B_qat_full


# Theory

# PTQ: x_q is quantized and cast to int8
# scale and zero point (zp) refer to parameters used to quantize x_float
# qmin and qmax refer to the range of quantized values
x_q = (x_float / scale + zp).round().clamp(qmin, qmax).cast(int8)

# QAT: x_fq is still in float
# Fake quantize simulates the numerics of quantize + dequantize
x_fq = (x_float / scale + zp).round().clamp(qmin, qmax)
x_fq = (x_fq - zp) * scale

# Usage

import torch
from torchtune.models.llama3 import llama3
from torchao.quantization.prototype.qat import Int8DynActInt4WeightQATQuantizer

# Smaller version of llama3 to fit in a single GPU
model = llama3(
    vocab_size=4096,
    num_layers=16,
    num_heads=16,
    num_kv_heads=4,
    embed_dim=2048,
    max_seq_len=2048,
).cuda()

# Quantizer for int8 dynamic per token activations +
# int4 grouped per channel weights, only for linear layers
qat_quantizer = Int8DynActInt4WeightQATQuantizer()

# Insert "fake quantize" operations into linear layers.
# These operations simulate quantization numerics during
# training without performing any dtype casting
model = qat_quantizer.prepare(model)

# Standard training loop
optimizer = torch.optim.SGD(model.parameters(), lr=0.001, momentum=0.9, weight_decay=1e-5)
loss_fn = torch.nn.CrossEntropyLoss()
for i in range(10):
    example = torch.randint(0, 4096, (2, 16)).cuda()
    target = torch.randn((2, 16, 4096)).cuda()
    output = model(example)
    loss = loss_fn(output, target)
    loss.backward()
    optimizer.step()
    optimizer.zero_grad()

# Convert fake quantize to actual quantize operations
# The quantized model has the exact same structure as the
# quantized model produced in the corresponding PTQ flow
# through `Int8DynActInt4WeightQuantizer`
model = qat_quantizer.convert(model)

### GPTQ

https://github.com/pytorch/ao/blob/main/torchao/quantization/GPTQ.py#L968

Int8DynActInt4WeightGPTQQuantizer::quantize -> _convert_for_runtime -> _replace_linear_8da4w(linear_class=Int8DynActInt4WeightLinear)

from torchao.quantization.quant_api import _replace_with_custom_fn_if_matches_filter 替换linear层


### quantized training

- 当前是dequant的实现，没有用int8 matmul
- Still not very attractive: memory reduction is not yet ideal (might be due to row-wise
scaling) + slower training due to quantization overhead + accuracy is slightly lower
- For fine-tuning, QLoRA is simpler

# int8 with SR

tensor-wise scale

int8.py
https://github.com/pytorch/ao/pull/644

class _Int8WeightOnlyLinear(torch.autograd.Function):
    @staticmethod
    def forward(
        ctx,
        input: Tensor,
        weight: Int8QuantizedTrainingLinearWeight,
        bias: Optional[Tensor] = None,
    ):
        ctx.save_for_backward(input, weight)
        ctx.bias = bias is not None 

        # NOTE: we have to .T before .to(input.dtype) for torch.compile() mixed matmul to work
        out = (input @ weight.int_data.T.to(input.dtype)) * weight.scale
        out = out + bias if bias is not None else out
        return out

    @staticmethod
    def backward(ctx, grad_output):
        input, weight = ctx.saved_tensors

        grad_input = (grad_output * weight.scale) @ weight.int_data.to(
            grad_output.dtype
        )
        grad_weight = grad_output.view(-1, weight.shape[0]).T @ input.view(
            -1, weight.shape[1]
        )
        grad_bias = grad_output.view(-1, weight.shape[0]).sum(0) if ctx.bias else None
        return grad_input, grad_weight, grad_bias


@implements(aten.copy_.default)
def _(func, types, args, kwargs):
    if isinstance(args[0], Int8QuantizedTrainingLinearWeight) and isinstance(
        args[1], Int8QuantizedTrainingLinearWeight
    ):
        args[0].int_data.copy_(args[1].int_data, **kwargs)
        args[0].scale.copy_(args[1].scale, **kwargs)

    elif isinstance(args[0], Int8QuantizedTrainingLinearWeight):
        int_data, scale = quantize_int8_rowwise(args[1], stochastic_rounding=True)
        args[0].int_data.copy_(int_data, **kwargs)
        args[0].scale.copy_(scale, **kwargs)

    else:
        args[0].copy_(args[1].dequantize(), **kwargs)

    return args[0]

# bf16 w/ SR

https://github.com/karpathy/llm.c/blob/7ecd8906afe6ed7a2b2cdb731c042f26d525b820/llmc/adamw.cuh#L19-L46
https://github.com/gau-nernst/quantized-training/blob/c42a7842ff6a9fe97bea54d00489e597600ae683/other_optim/bf16_sr.py#L108-L122

- Note on optimizer
existing PyTorch optimizers may modify the param in-place multiple times. e.g. AdamW
https://github.com/pytorch/pytorch/blob/32be3e942c3251dc50892334c6614a89327c122c/torch/optim/adamw.py#L384
 Therefore, this PR also adds an alternative implementation of AdamW in torchao.prototype.low_bit_optim.AdamW, which only applies in-place update of param in the final step.


# int8 mixed precision 优化compute

https://github.com/pytorch/ao/pull/748

 Many of optimization of FP8 training can be applied here too. Namely, delayed scaling (my current INT8 mixed-precision here is basically dynamic scaling), 
 quantize before FSDP all-gather to reduce communication bandwidth. I leave this for future PRs.

@torch.compiler.allow_in_graph  # this is required for module-swap, but not for tensor subclass
class _Int8MixedPrecisionTrainingLinearFunction(torch.autograd.Function):
    @staticmethod
    def forward(...
        if config.output:
            out = _dynamic_int8_mm(input, weight.T)

def scaled_int8_mm(
    A: Tensor, B: Tensor, row_scale: Tensor, col_scale: Tensor
) -> Tensor:
    """Compute `(A @ B) * row_scale * col_scale`, where `A` and `B` are INT8 to utilize
    INT8 tensor cores. `col_scale` can be a scalar.
    """
    assert A.dtype is torch.int8 and B.dtype is torch.int8
    assert row_scale.dtype is col_scale.dtype
    assert A.shape[1] == B.shape[0]
    assert row_scale.squeeze().shape == (A.shape[0],)
    assert col_scale.squeeze().shape in ((B.shape[1],), ())
    assert row_scale.is_contiguous()
    assert col_scale.is_contiguous()
    return torch.ops.torchao.scaled_int8_mm(A, B, row_scale, col_scale)


# BitNet b1.58 Training
https://github.com/pytorch/ao/pull/930
- 暂未对backward做量化

class _BitNetTrainingLinear(torch.autograd.Function):
    @staticmethod
    def forward(
        ctx,
        input: Tensor,
        weight: BitNetTrainingLinearWeight,
        bias: Optional[Tensor] = None,
    ):
        batch_dims = input.shape[:-1]
        input = input.view(-1, weight.shape[1])

        # https://github.com/microsoft/unilm/blob/master/bitnet/The-Era-of-1-bit-LLMs__Training_Tips_Code_FAQ.pdf
        # Figure 3
        input_i8, row_scale = quantize_int8_rowwise(input, eps=1e-5)

        # NOTE: use FP32 scale for weight quantization, but cast scale to possibly lower precision
        # for matmul and backward
        tensor_scale = get_bitnet_scale(weight._data)
        weight_i8 = quantize_bitnet_weight(weight._data, tensor_scale)
        tensor_scale = tensor_scale.to(weight.dtype)

        ctx.save_for_backward(input_i8, row_scale, weight_i8, tensor_scale)

        # use int8 tensor cores
        out = scaled_int8_mm(
            input_i8.contiguous(), weight_i8.contiguous().T, row_scale, tensor_scale
        )
        out = out.view(*batch_dims, weight.shape[0])

        out = out + bias if bias is not None else out
        return out


class BitNetTrainingLinearWeight(TorchAOBaseTensor):
    ...
    # FSDP all-gather extension v1
    def fsdp_pre_all_gather(self, mesh):
        # quantize and pack into 2-bit to save comm bandwidth
        if self._precomputed_scale is not None:
            scale = self._precomputed_scale

        else:
            scale = get_bitnet_scale(self._data)
            dist.all_reduce(scale, op=dist.ReduceOp.AVG)

        # NOTE: scale is in FP32
        data_i8 = quantize_bitnet_weight(self._data, scale)
        data_i2 = _pack_i2_in_i8(data_i8)
        return (data_i2,), (scale,)

    def fsdp_post_all_gather(
        self,
        all_gather_outputs: Tuple[Tensor, ...],
        metadata: Any,
        param_dtype: torch.dtype,
        *,
        out: Optional[Tensor] = None,
    ):
        (data_i2,) = all_gather_outputs
        (scale,) = metadata
        scale = scale.to(param_dtype)
        if out is not None:
            assert isinstance(out, BitNetPacked2bitLinearWeight)
            out.scale = scale
            return
        return BitNetPacked2bitLinearWeight(data_i2, scale), all_gather_outputs

### low bit optimizer

背景：
pytorch optimizer不支持fp32 param + bf16 optimizer

特性：
- Stochastic rounding for BF16 weight： bf16_stochastic_round=True


torchao/prototype/low_bit_optim/adam.py

def single_param_adam():
    # compute in FP32 for accurate calculations
    p_f32 = p.float()
    grad_f32 = grad.float()

    ...
    # keep high precision copy for param update
    exp_avg_f32 = exp_avg.float().lerp(grad_f32, 1 - beta1)
    exp_avg_sq_f32 = exp_avg_sq.float().lerp(grad_f32.square(), 1 - beta2)

    exp_avg.copy_(exp_avg_f32)
    exp_avg_sq.copy_(exp_avg_sq_f32)
    ...

torchao/prototype/low_bit_optim/subclass_8bit.py
- aten.lerp.Scalar
- aten.copy_.default

@OptimState8bit.implements(aten.lerp.Scalar)
def _(func, types, args, kwargs):
    # 进行dequant
    args = [x.dequantize() if isinstance(x, OptimState8bit) else x for x in args]
    return func(*args, **kwargs)


@OptimState8bit.implements(aten.copy_.default)
def _(func, types, args, kwargs):
    dst = args[0]
    src = args[1]

    if isinstance(dst, OptimState8bit) and isinstance(src, OptimState8bit):
        assert dst.signed == src.signed and dst.block_size == src.block_size
        dst.codes.copy_(src.codes)
        dst.scale.copy_(src.scale)
        # qmap should be the same, don't need to copy

    # 进行量化
    elif isinstance(dst, OptimState8bit):
        scaled_src, scale = scale_tensor(src, dst.block_size)
        codes = quantize_8bit_with_qmap(scaled_src, dst.qmap)
        dst.codes.copy_(codes)
        dst.scale.copy_(scale)

    else:
        dst.copy_(src.dequantize())

    return dst


### utils

utils.py

包装tensor，支持dispatch方法


### bitsandbytes
accuracy-first

https://huggingface.co/docs/bitsandbytes/main/en/index

* 8-bit optimizers uses block-wise quantization to maintain 32-bit performance at a small fraction of the memory cost.
* LLM.int8() or 8-bit quantization enables large language model inference with only half the required memory
 and without any performance degradation. This method is based on vector-wise quantization to quantize most features to 8-bits and separately treating outliers with 16-bit matrix multiplication.
* QLoRA or 4-bit quantization enables large language model training with several 
memory-saving techniques that don’t compromise performance. This method quantizes a model to 4-bits and inserts a small set of trainable low-rank adaptation (LoRA) weights to allow training.