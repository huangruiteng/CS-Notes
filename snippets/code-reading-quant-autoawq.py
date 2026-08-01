
https://github.com/casper-hansen/AutoAWQ

https://medium.com/@crclq2018/awq-how-its-code-works-1ea92fb80bd2


### 支持huggingface model

### filter linear

named_linears = get_named_linears(self.modules[i])

{'attn.c_attn': Linear(in_features=5120, out_features=15360, bias=True),

'attn.c_proj': Linear(in_features=5120, out_features=5120, bias=False),

'mlp.c_proj': Linear(in_features=13696, out_features=5120, bias=False),

'mlp.w1': Linear(in_features=5120, out_features=13696, bias=False),

'mlp.w2': Linear(in_features=5120, out_features=13696, bias=False)}

# Filter out the linear layers we don't want to exclude
named_linears = exclude_layers_to_not_quantize(
    named_linears, self.modules_to_not_convert
)

### feature importance

input_feat = self._get_input_feat(self.modules[i], named_linears)

The rationale behind AWQ is simple. We scale up some important weights so that they can preserve better precision during the quantization. 
To correct for the weight upscaling, the weights of the previous module, such as LayerNorm, are also modified.
-  the scale is solely determined by the input

# first gets the average of the absolute value of a channel over all B*S tokens.

x_mean = inp.abs().view(-1, inp.shape[-1]).mean(0)

# AutoAWQ will try 20 different ratios and decide which one suits best
scales = x_mean.pow(ratio).clamp(min=1e-4).view(-1)

scales = scales / (scales.max() * scales.min()).sqrt()

# Q(W * s)
fc.weight.mul_(scales_view)
fc.weight.data = (
    self.pseudo_quantize_tensor(fc.weight.data)[0] / scales_view
)

It then multiplies the pseudo-quantized weights with the input and compares the output with the original output. 
It calculates the L2 distance between the two to measure how much the quantization has affected the accuracy.

After repeating 20 times it chooses the ratio with the smallest loss.


* Find the best clipping value
- there’s always a tradeoff between the clipping error and the rounding error.
- simply tries 20 different shrinkage value and selects the one yielding the smallest L2 loss.

### kernel

pack 8*int4 into one int32
you have 0x1, 0x2, 0x3, 0x4, 0x5, 0x6, 0x7, 0x8, you can pack them as 0x12345678, or 0x86427531. 
AutoAWQ uses the second pattern, the interleaved one, for better performance in unpacking.

- 实际上GemLite发现pack成int8的性能更好

self.register_buffer(
    "qweight",
    torch.zeros(
        (in_features, out_features // (32 // self.w_bit)),
        dtype=torch.int32,
        device=dev,
    ),
)


### triton算子








