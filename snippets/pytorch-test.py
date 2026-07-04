

torch.isclose(x, y, equal_nan=True)

torch.allclose(a, b)     / numpy.allclose

* 标准：absolute(a - b) <= atol + rtol * absolute(b)
* 该标准具备不对称性，a为待测值，b为expected值

