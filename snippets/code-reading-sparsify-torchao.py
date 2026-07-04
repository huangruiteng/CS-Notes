https://github.com/pytorch/ao/blob/main/torchao/prototype/sparsity/superblock/README.md

import torch
from torch.sparse import to_sparse_semi_structured, SparseSemiStructuredTensor

# Sparsity helper functions
def apply_fake_sparsity(model):
    """
    This function simulates 2:4 sparsity on all linear layers in a model.
    It uses the torch.ao.pruning flow.
    """
    # torch.ao.pruning flow
    from torch.ao.pruning import WeightNormSparsifier
    sparse_config = []
    for name, mod in model.named_modules():
        if isinstance(mod, torch.nn.Linear):
            sparse_config.append({"tensor_fqn": f"{name}.weight"})

    sparsifier = WeightNormSparsifier(sparsity_level=1.0,
                                      sparse_block_shape=(1,4),
                                      zeros_per_block=2)
    sparsifier.prepare(model, sparse_config)
    sparsifier.step()

    sparsifier.step()
    sparsifier.squash_mask()


def apply_sparse(model):
    apply_fake_sparsity(model)
    for name, mod in model.named_modules():
        if isinstance(mod, torch.nn.Linear):
            mod.weight = torch.nn.Parameter(to_sparse_semi_structured(mod.weight))


- Get zeros into the right spots, then call to_sparse_semi_structured
- Works with torch.compile!
-- Only first matrix sparse
-- xW’ = (xW’)’’ = (Wx’)’ 这样可以对第一个矩阵W进行稀疏化，但Needed to fuse transpositions


### sparsity training

torchao/sparsity/training/autograd.py

### sparse&quant fusion

[sparse][quant] Add support for vector alpha in cusparselt mm
- https://github.com/pytorch/pytorch/pull/112056

问题：缺少 fused dequant + cusparse + bf16


### sparsity + triton

[DRAFT][AMD][Backend] Enable 2:4 Structured Sparsity for Triton-AMD #6714
https://github.com/triton-lang/triton/pull/6714