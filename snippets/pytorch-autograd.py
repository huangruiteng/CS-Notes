### example
import torch
x = torch.tensor([1.0, 2.0, 3.0], requires_grad=True)

# 前向传播：
# 1. 构建并执行前向图
# 2. 构建反向图
t = x * 10
z = t * t

# t.add_(1)会破坏backward，报错

loss = z.mean()
loss.retain_grad()   # loss grad为1

# retain_graph()

# 反向传播：当场构建，延迟执行
loss.backward()
print(x.grad)

- loss非标量，backward需要知道梯度形状：output.backward(gradient=grad_output)

### 利用Function创建customized backward func

class Exp(torch.autograd.Function):
 @staticmethod
 def forward(ctx, i):
     result = i.exp()
     ctx.save_for_backward(result)
     return result

 @staticmethod
 def backward(ctx, grad_output):
     result, = ctx.saved_tensors
     return grad_output * result

# Use it by calling the apply method:
output = Exp.apply(input)


class MyMul(torch.autograd.Function):
    @staticmethod
    def forward(ctx, input1, input2):
        ctx.save_for_backward(input1, input2)
        return input1 * input1 * input2

    @staticmethod
    def backward(ctx, grad_output):
        input1, input2 = ctx.saved_tensors
        grad_input1 = grad_output * 2 * input1 * input2
        grad_input2 = grad_output * input1 * input1
        return grad_input1, grad_input2


# 使用自定义的乘法操作
x = torch.tensor([2.0, 3.0], requires_grad=True)
y = torch.tensor([3.0, 4.0], requires_grad=True)
z = MyMul.apply(x, y)
z.backward(torch.tensor([1.0, 1.0]))

print(f"x.grad={x.grad}, y.grad={y.grad}")
# x.grad=tensor([12., 24.]), y.grad=tensor([4., 9.])


### Gradient Check

from torch.autograd import gradcheck

# gradcheck takes a tuple of tensors as input, check if your gradient
# evaluated with these tensors are close enough to numerical
# approximations and returns True if they all verify this condition.
# Note: it's recommended to use double precision for gradcheck
input1 = torch.randn(4, 4, dtype=torch.double, requires_grad=True)
input2 = torch.randn(4, 4, dtype=torch.double, requires_grad=True)
test = gradcheck(MyMul.apply, (input1, input2), eps=1e-6, atol=1e-4)
print(f"Gradcheck result: {test}")
