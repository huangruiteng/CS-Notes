
*** epilogue fusion

import cutlass
import torch

# 1. Declare a basic GEMM
plan = cutlass.op.Gemm(
    element=torch.float32,
    layout=cutlass.LayoutType.RowMajor
)

# 2. Define an epilogue as a Python function
def my_epilogue(accum, alpha, C, beta, bias):
    D = torch.relu(alpha * accum + beta * C + bias)
    return D

# 3. Define types and shapes of each EVT operand/output
empty_mn = torch.empty(size=(m, n), dtype=torch.float32)
empty_bias = torch.empty(size=(m, 1), dtype=torch.float32)
examples_inputs = {
    "accum": empty_mn, "C": empty_mn, "D": empty_mn,
    "alpha": 1.0, "beta": 1.0, "bias": empty_bias
}

# 4. Construct the EVT and assign it to the GEMM
plan.epilogue_visitor = cutlass.epilogue.trace(
    my_epilogue, examples_inputs
)

# 5. Compile and run the kernel
# 这里假设A、B、C、D、bias已经正确定义并初始化
A, B, C, D, bias =...
visitor_args = {
    "alpha": 2.0, "beta": 0.0,
    "C": C, "D": D, "bias": bias
}
plan.run(A, B, C, D, visitor_args=visitor_args)