# index_select-fwd_bwd-performance (D=1024):
# num_indices  Triton Bwd  PyTorch Bwd  PyTorch Bwd (scatter_add)  Compiled PyTorch Bwd (scatter_add)
# 0          16.0    0.216608     0.031328                   0.243776                            0.314304
# 1          32.0    0.303616     0.058064                   0.301088                            0.368288
# 2          64.0    0.280704     0.056832                   0.292032                            0.327360
# 3         128.0    0.204640     0.038544                   0.317024                            0.372480
# 4         256.0    0.195120     0.033568                   0.315360                            0.356160
# 5         512.0    0.197712     0.035552                   0.322208                            0.364160
# 6        1024.0    0.198928     0.039104                   0.324800                            0.366816
# 7        2048.0    0.199712     0.060640                   0.332240                            0.372064
# 8        4096.0    0.204192     0.103392                   0.334528                            0.376864
# 9        8192.0    0.210080     0.192000                   0.385280                            0.399648
# 10      16384.0    0.414304     0.366912                   0.677856                            0.676480
# 11      32768.0    0.863440     0.704448                   1.295616                            1.288128
# 12      65536.0    1.793984     1.374560                   2.553872                            2.525248
# 13     131072.0    3.975488     2.724704                   5.430160                            5.405392
# 14     262144.0    6.903984     5.541632                   9.906432                            9.868544
# 15     524288.0   13.891072    11.231120                  20.021584                           19.919823
# 16    1048576.0   27.119425    22.745104                  39.652206                           39.512432

from functools import partial
import torch
import math
import unittest
from monotorch.layers.triton_ops.index_select_op import index_select, index_select_native_scatter_add
import triton
import triton.testing

def custom_repr(self):
  return f'{{Tensor{tuple(self.shape)}: {original_repr(self)}}}'

original_repr = torch.Tensor.__repr__
torch.Tensor.__repr__ = custom_repr


class TestIndexSelect(unittest.TestCase):
    def test_index_select(self):
      device = torch.device("cuda:0")
      unique_values = torch.tensor([[1, 2, 3], [4, 5, 6], [7, 8, 9]],
                                   dtype=torch.float32, device=device, requires_grad=True)
      indices = torch.tensor([0, 1, 0, 2], device=device)
      output = index_select(unique_values, indices)
      expected_output = torch.tensor([[1, 2, 3], [4, 5, 6], [1, 2, 3], [7, 8, 9]], dtype=torch.float32, device=device)
      grad_output = torch.randn_like(output)
      output.backward(gradient=grad_output)
      self.assertTrue(torch.allclose(output, expected_output))

    def _run_and_check_grad(self, func, unique_values_ref, indices_ref, torch_out_ref, torch_grad_ref, device, N, D, num_indices, label):
        """Helper method to run forward/backward and check gradients."""
        unique_values_ref.grad.zero_()
        indices = indices_ref.clone()

        output = func(unique_values_ref, indices)
        torch.manual_seed(42)
        grad_output = torch.randn_like(output)
        output.backward(gradient=grad_output)
        grad = unique_values_ref.grad

        self.assertTrue(torch.allclose(torch_out_ref, output), f"{label} forward mismatch, torch_grad_ref: {torch_grad_ref}, grad: {grad}")
        self.assertTrue(torch.allclose(torch_grad_ref, grad, rtol=1e-3, atol=1e-3), f"{label} backward mismatch, torch_grad_ref: {torch_grad_ref}, grad: {grad}")

    def test_index_select_grad(self):
      device = torch.device("cuda:0")
      N, D, num_indices = 55, 68, 111
      torch.manual_seed(42)
      unique_values_ref = torch.randn(N, D, dtype=torch.float32, device=device, requires_grad=True)
      indices_ref = torch.randint(low=0, high=N, size=(num_indices,), device=device)
      torch_out_ref = torch.index_select(unique_values_ref, 0, indices_ref)

      torch.manual_seed(42)
      grad_output = torch.randn_like(torch_out_ref)
      torch_out_ref.backward(gradient=grad_output)
      torch_grad_ref = unique_values_ref.grad.clone()
      self._run_and_check_grad(index_select, unique_values_ref, indices_ref, torch_out_ref, torch_grad_ref, device, N, D, num_indices, "Triton")
      self._run_and_check_grad(index_select_native_scatter_add, unique_values_ref, indices_ref, torch_out_ref, torch_grad_ref, device, N, D, num_indices, "PyTorch Bwd (scatter_add)")


    def test_batch_index_select_grad(self):
      device = torch.device("cuda:0")
      B, N, D, num_indices = 1025, 96, 1290, 2058
      # B, N, D, num_indices = 4, 55, 68, 4096

      torch.manual_seed(42)
      unique_values_ref = torch.randn(N, D, dtype=torch.float32, device=device, requires_grad=True)
      indices_ref = torch.randint(low=0, high=N, size=(B, num_indices), device=device)

      expanded_values = unique_values_ref.unsqueeze(0).expand(B, -1, -1)
      expanded_indices = indices_ref.unsqueeze(-1).expand(-1, -1, D)
      torch_out_ref = torch.gather(expanded_values, 1, expanded_indices)
      torch.manual_seed(42)
      grad_output = torch.randn_like(torch_out_ref)
      torch_out_ref.backward(gradient=grad_output)
      torch_grad_ref = unique_values_ref.grad.clone()
      self._run_and_check_grad(index_select, unique_values_ref, indices_ref, torch_out_ref, torch_grad_ref, device, N, D, num_indices, "Triton")
      self._run_and_check_grad(index_select_native_scatter_add, unique_values_ref, indices_ref, torch_out_ref, torch_grad_ref, device, N, D, num_indices, "Triton")


# --- Performance Benchmark ---
@triton.testing.perf_report(
    triton.testing.Benchmark(
        x_names=['num_indices'],
        # x_vals=[64, 128, 256, 512, 1024, 2048, 4096],
        # x_vals=[8192, 2*8192, 4*8192, 8*8192, 16*8192, 32*8192, 64*8192, 128*8192],
        x_vals=[64, 128, 256, 512, 1024, 2048, 4096, 8192, 2*8192,4*8192, 8*8192, 16*8192, 32*8192, 400000, 64*8192, 128*8192],
        line_arg='provider',
        line_vals=['triton','torch-index_select'], #'torch-scatter_add', 'torch-compiled_scatter_add'],
        line_names=[
            'Triton Bwd',
            'PyTorch Bwd',
            # 'PyTorch Bwd (scatter_add)',
            # 'Compiled PyTorch Bwd (scatter_add)',
        ],
        ylabel='ms',
        # plot_name='index_select-fwd_bwd-performance (D=1024, num_indices <= 4096)',
        # plot_name='index_select-fwd_bwd-performance (D=1024, num_indices > 4096)',
        plot_name='index_select-fwd_bwd-performance (unique_ratio=0.02,D=512)',
        args={
            'D': 512,
            'unique_ratio': 0.02,
            'dtype': torch.float32,
            'device': 'cuda'
        }
    )
)
def benchmark(D, num_indices, provider, unique_ratio, dtype, device):
    """
    Benchmark function for index_select forward + backward pass.
    """
    num_unique_value = int(num_indices * unique_ratio) or 1
    unique_values = torch.randn(num_unique_value, D, dtype=dtype, device=device, requires_grad=True)
    indices = torch.randint(low=0, high=num_unique_value, size=(num_indices,), device=device)
    output_shape = (num_indices, D)
    grad_output = torch.randn(output_shape, dtype=dtype, device=device) # 预先创建梯度, 原因是对于非标量的backward需要知道梯度形状

    if provider == 'triton':
        func = index_select
    elif provider == 'torch-index_select':
        func = lambda input_tensor, index_tensor: torch.index_select(input_tensor, 0, index_tensor)
    elif provider == 'torch-scatter_add':
        func = index_select_native_scatter_add
    elif provider == 'torch-compiled_scatter_add':
        func = torch.compile(index_select_native_scatter_add)
    else:
        raise ValueError(f"Unknown provider: {provider}")

    output = func(unique_values, indices)
    def run_op():
      output.backward(gradient=grad_output, retain_graph=True)

    ms, min_ms, max_ms = triton.testing.do_bench(run_op, warmup=25, rep=100, grad_to_none=[unique_values], quantiles=[0.5, 0.2, 0.8])
    return ms, min_ms, max_ms

if __name__ == '__main__':
    unittest.main(argv=['first-arg-is-ignored'], exit=False)
    benchmark.run(print_data=True, show_plots=True, save_path=".")