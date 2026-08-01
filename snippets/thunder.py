### register implementation

import thunder

attn_ex = thunder.extend.OperatorExecutor('attn_ex', version=0.01)
thunder.add_default_executor(attn_ex)

def my_attn_checker(query, key, value, attn_mask=None, dropout_p=0.0, is_causal=False, scale=None):
    if attn_mask is not None or dropout_p != 0.0 or is_causal:
        return False
    if len(query.shape) > 2:
        return False
    return (query.device.device_type == torch.device('cuda').type and
            key.device == query.device and
            value.device == query.device)

def my_attn_transform(query, key, value, attn_mask=None, dropout_p=0.0, is_causal=False, scale=None):
    if scale is None:
        scale = d ** (-0.5)
    out = my_attn(query, key, value, scale)
    return out[0]

attn_ex.register_implementation(torch.scaled_dot_product_attention,
                                checker=my_attn_checker,
                                execution_transform=my_attn_transform)


### debug

def test_fn(query, key, value):
    return torch.nn.functional.scaled_dot_product_attention(query, key, value, is_causal=False)

jfn = thunder.jit(test_fn)
print((jfn(Qc, Kc, Vc) - test_fn(Qc, Kc, Vc)).abs().max())
print(thunder.last_traces(jfn)[0])