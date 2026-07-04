https://docs.pytorch.org/docs/stable/sparse.html

* attribute

Currently, one can acquire the COO format data only when the tensor instance is coalesced:
s.indices()

For acquiring the COO format data of an uncoalesced tensor, use torch.Tensor._values() and torch.Tensor._indices():


* Uncoalesced sparse COO tensors


>>> i = [[1, 1]]
>>> v =  [3, 4]
>>> s=torch.sparse_coo_tensor(i, v, (3,))
>>> s
tensor(indices=tensor([[1, 1]]),
       values=tensor(  [3, 4]),
       size=(3,), nnz=2, layout=torch.sparse_coo)

coalesce会生成7
