### Intro
https://github.com/triton-lang/triton

https://triton-lang.org/main/getting-started/tutorials/02-fused-softmax.html

https://www.youtube.com/watch?v=DdTsX6DQk24

支持AMD

### tutorials


The official documentation: https://triton-lang.org/
The LightLLM repo has a ton of real-world triton kernels: https://github.com/ModelTC/lightllm/tree/main/lightllm/common/basemodel/triton_kernel
So does the Unsloth repo: https://github.com/unslothai/unsloth/tree/main/unsloth/kernels


### tl.program_id

2d用1d

pid = tl.program_id(axis=0)
grid_n = tl.cdiv(N, BLOCK_SIZE_N)
pid_m = pid // grid_n
pid_n = pid % grid_n


pid_m = tl.program_id(axis=0).to(tl.int64)
- int32的范围是 -2,147,483,648 到 +2,147,483,647
- 当元素数量较多，可能达到 20亿以上 float 时，pid_m = tl.program_id(axis=0).to(tl.int64) 是 Triton Kernel 的最佳实践
  - 20亿 float，当 emb_dim =4096、batch size = 1024时，每个 instance 有 5000 个 emb，在现实场景中可能达到
  - https://github.com/triton-lang/triton/issues/1058



### swizzle

- 手工

# Program ID
pid = tl.program_id(axis=0)
# Number of program ids along the M axis
num_pid_m = tl.cdiv(M, BLOCK_SIZE_M)
# Number of programs ids along the N axis
num_pid_n = tl.cdiv(N, BLOCK_SIZE_N)
# Number of programs in group
num_pid_in_group = GROUP_SIZE_M * num_pid_n
# Id of the group this program is in
group_id = pid // num_pid_in_group
# Row-id of the first program in the group
first_pid_m = group_id * GROUP_SIZE_M
# If `num_pid_m` isn't divisible by `GROUP_SIZE_M`, the last group is smaller
group_size_m = min(num_pid_m - first_pid_m, GROUP_SIZE_M)
# *Within groups*, programs are ordered in a column-major order
# Row-id of the program in the *launch grid*
pid_m = first_pid_m + ((pid % num_pid_in_group) % group_size_m)
# Col-id of the program in the *launch grid*
pid_n = (pid % num_pid_in_group) // group_size_m

- API
pid_m, pid_n = tl.swizzle2d(
      pid_m, pid_n, num_pid_m, num_pid_n,
      group_sz)

*** tl.dot

input_precision (string. Available options for nvidia: "tf32", "tf32x3", "ieee")


*** benchmark
- grad_to_none=[x]，避免累加开销

if mode == 'forward':
        gbps = lambda ms: 2 * x.numel() * x.element_size() * 1e-9 / (ms * 1e-3)
        ms, min_ms, max_ms = triton.testing.do_bench(y_fwd, quantiles=quantiles, rep=500)
    # backward pass
    if mode == 'backward':
        y = y_fwd()
        gbps = lambda ms: 3 * x.numel() * x.element_size() * 1e-9 / (ms * 1e-3)  # noqa: F811, E704
        ms, min_ms, max_ms = triton.testing.do_bench(lambda: y.backward(dy, retain_graph=True), quantiles=quantiles,
                                                     grad_to_none=[x], rep=500)

### Autotune

tricks&configs可参考 https://www.youtube.com/watch?v=SGhfUhlowB4
