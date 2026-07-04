### positional encoding

def positional_encoding(seq_len, d_model):
    # 初始化位置编码矩阵
    pe = torch.zeros(seq_len, d_model)
    position = torch.arange(0, seq_len, dtype=torch.float).unsqueeze(1)
    div_term = torch.exp(torch.arange(0, d_model, 2).float() * (-math.log(10000.0) / d_model))
    # 计算偶数维度的正弦编码
    pe[:, 0::2] = torch.sin(position * div_term)
    # 计算奇数维度的余弦编码
    pe[:, 1::2] = torch.cos(position * div_term)
    return pe

# 示例使用
seq_len = 10
d_model = 512
pe = positional_encoding(seq_len, d_model)
print(pe.shape)  # 输出: torch.Size([10, 512])



### modeling_swinv2.py

# https://huggingface.co/microsoft/swinv2-large-patch4-window12-192-22k

# patch embedding
# 每个patch的特征长度：4*4*3=48
self.projection = nn.Conv2d(num_channels, hidden_size, kernel_size=patch_size, stride=patch_size)
hidden_size=config.embed_dim=192
(batch_size, 192, height // p_h, width // p_w)

# feature num
self.num_features = int(config.embed_dim * 2 ** (self.num_layers - 1))

192*2^3=1536

self.layernorm = nn.LayerNorm(self.num_features, eps=config.layer_norm_eps)

# block

Swin Transformer block consists of a shifted window based MSA
module, followed by a 2-layer MLP with GELU non-linearity in between


# last_hidden_state

sequence_output = encoder_outputs[0]
sequence_output = self.layernorm(sequence_output)

最后一个hidden state
layer_outputs[0] -> Swinv2Stage -> Swinv2Layer -> Swinv2Attention -> Swinv2SelfAttention


# layer之间差异

class Swinv2Encoder
	dpr = [x.item() for x in torch.linspace(0, config.drop_path_rate, sum(config.depths))]
	stage_i = Swinv2Stage(drop_path=dpr[sum(config.depths[:i_layer]) : sum(config.depths[: i_layer + 1])],...)

class Swinv2Stage
	block_i = Swinv2Layer(drop_path_rate=drop_path[i], ...)

	for i, layer_module in enumerate(self.blocks):
        layer_head_mask = head_mask[i] if head_mask is not None else None

        layer_outputs = layer_module(
            hidden_states,
            input_dimensions,
            layer_head_mask,
            output_attentions,
        )

        hidden_states = layer_outputs[0]


# pooled_output

self.pooler = nn.AdaptiveAvgPool1d(1) if add_pooling_layer else None
...
pooled_output = self.pooler(sequence_output.transpose(1, 2))
pooled_output = torch.flatten(pooled_output, 1)

用pooled_output做分类