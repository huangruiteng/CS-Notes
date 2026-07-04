"""
Fused Softmax
=============

In this tutorial, you will write a fused softmax operation that is significantly faster
than PyTorch's native op for a particular class of matrices: those whose rows can fit in
the GPU's SRAM.

In doing so, you will learn about:

* The benefits of kernel fusion for bandwidth-bound operations.

* Reduction operators in Triton.

"""

# %%
# Motivations
# -----------
#
# Custom GPU kernels for elementwise additions are educationally valuable but won't get you very far in practice.
# Let us consider instead the case of a simple (numerically stabilized) softmax operation:

import torch

import triton
import triton.language as tl
from triton.runtime import driver

DEVICE = torch.cuda.current_device()


def is_hip():
  return triton.runtime.driver.active.get_current_target().backend == "hip"


def is_cdna():
  return is_hip() and triton.runtime.driver.active.get_current_target().arch in ('gfx940', 'gfx941', 'gfx942',
                                                                                 'gfx90a', 'gfx908')


def naive_softmax(x):
  """Compute row-wise softmax of X using native pytorch

  We subtract the maximum element in order to avoid overflows. Softmax is invariant to
  this shift.
  """
  # read  MN elements ; write M  elements
  x_max = x.max(dim=1)[0]
  # read MN + M elements ; write MN elements
  z = x - x_max[:, None]
  # read  MN elements ; write MN elements
  numerator = torch.exp(z)
  # read  MN elements ; write M  elements
  denominator = numerator.sum(dim=1)
  # read MN + M elements ; write MN elements
  ret = numerator / denominator[:, None]
  # in total: read 5MN + 2M elements ; wrote 3MN + 2M elements
  return ret

compiled_naive_softmax = torch.compile(naive_softmax)

# %%
# When implemented naively in PyTorch, computing :code:`y = naive_softmax(x)` for :math:`x \in R^{M \times N}`
# requires reading :math:`5MN + 2M` elements from DRAM and writing back :math:`3MN + 2M` elements.
# This is obviously wasteful; we'd prefer to have a custom "fused" kernel that only reads
# X once and does all the necessary computations on-chip.
# Doing so would require reading and writing back only :math:`MN` bytes, so we could
# expect a theoretical speed-up of ~4x (i.e., :math:`(8MN + 4M) / 2MN`).
# The `torch.jit.script` flags aims to perform this kind of "kernel fusion" automatically
# but, as we will see later, it is still far from ideal.

# %%
# Compute Kernel
# --------------
#
# Our softmax kernel works as follows: each program loads a set of rows of the input matrix X strided by number of programs,
# normalizes it and writes back the result to the output Y.
#
# Note that one important limitation of Triton is that each block must have a
# power-of-two number of elements, so we need to internally "pad" each row and guard the
# memory operations properly if we want to handle any possible input shapes:


@triton.jit
def softmax_kernel(output_ptr, input_ptr, input_row_stride, output_row_stride, n_rows, n_cols, BLOCK_SIZE: tl.constexpr,
                   num_stages: tl.constexpr,
                   num_warps: tl.constexpr):
  # starting row of the program
  row_start = tl.program_id(0)
  row_step = tl.num_programs(0)
  for row_idx in tl.range(row_start, n_rows, row_step, num_stages=num_stages): # num_stages不一定有收益，需要autotune
    # The stride represents how much we need to increase the pointer to advance 1 row
    row_start_ptr = input_ptr + row_idx * input_row_stride
    # The block size is the next power of two greater than n_cols, so we can fit each
    # row in a single block
    col_offsets = tl.arange(0, BLOCK_SIZE)
    input_ptrs = row_start_ptr + col_offsets
    # Load the row into SRAM, using a mask since BLOCK_SIZE may be > than n_cols
    mask = col_offsets < n_cols
    row = tl.load(input_ptrs, mask=mask, other=-float('inf'))
    # Subtract maximum for numerical stability
    row_minus_max = row - tl.max(row, axis=0)
    # Note that exponentiation in Triton is fast but approximate (i.e., think __expf in CUDA)
    numerator = tl.exp(row_minus_max)
    denominator = tl.sum(numerator, axis=0)
    softmax_output = numerator / denominator
    # Write back output to DRAM
    output_row_start_ptr = output_ptr + row_idx * output_row_stride
    output_ptrs = output_row_start_ptr + col_offsets
    tl.store(output_ptrs, softmax_output, mask=mask)


# %%
# We can create a helper function that enqueues the kernel and its (meta-)arguments for any given input tensor.

properties = driver.active.utils.get_device_properties(DEVICE)
NUM_SM = properties["multiprocessor_count"]
NUM_REGS = properties["max_num_regs"]
SIZE_SMEM = properties["max_shared_mem"]
WARP_SIZE = properties["warpSize"]
target = triton.runtime.driver.active.get_current_target()


def softmax(x):
  n_rows, n_cols = x.shape

  # The block size of each loop iteration is the smallest power of two greater than the number of columns in `x`
  BLOCK_SIZE = triton.next_power_of_2(n_cols)

  # Another trick we can use is to ask the compiler to use more threads per row by
  # increasing the number of warps (`num_warps`) over which each row is distributed.
  # You will see in the next tutorial how to auto-tune this value in a more natural
  # way so you don't have to come up with manual heuristics yourself.
  num_warps = 8

  # Number of software pipelining stages.
  num_stages = 4 if SIZE_SMEM > 200000 else 2

  # Allocate output
  y = torch.empty_like(x)

  # pre-compile kernel to get register usage and compute thread occupancy.
  kernel = softmax_kernel.warmup(y, x, x.stride(0), y.stride(0), n_rows, n_cols, BLOCK_SIZE=BLOCK_SIZE,
                                 num_stages=num_stages, num_warps=num_warps, grid=(1, ))
  kernel._init_handles()
  n_regs = kernel.n_regs
  size_smem = kernel.metadata.shared
  if is_hip():
    # NUM_REGS represents the number of regular purpose registers. On CDNA architectures this is half of all registers available.
    # However, this is not always the case. In most cases all registers can be used as regular purpose registers.
    # ISA SECTION (3.6.4 for CDNA3)
    # VGPRs are allocated out of two pools: regular VGPRs and accumulation VGPRs. Accumulation VGPRs are used
    # with matrix VALU instructions, and can also be loaded directly from memory. A wave may have up to 512 total
    # VGPRs, 256 of each type. When a wave has fewer than 512 total VGPRs, the number of each type is flexible - it is
    # not required to be equal numbers of both types.
    if is_cdna():
      NUM_GPRS = NUM_REGS * 2

    # MAX_NUM_THREADS represents maximum number of resident threads per multi-processor.
    # When we divide this number with WARP_SIZE we get maximum number of waves that can
    # execute on a CU (multi-processor)  in parallel.
    MAX_NUM_THREADS = properties["max_threads_per_sm"]
    max_num_waves = MAX_NUM_THREADS // WARP_SIZE
    occupancy = min(NUM_GPRS // WARP_SIZE // n_regs, max_num_waves) // num_warps
  else:
    occupancy = NUM_REGS // (n_regs * WARP_SIZE * num_warps)
  occupancy = min(occupancy, SIZE_SMEM // size_smem)
  num_programs = NUM_SM * occupancy

  num_programs = min(num_programs, n_rows)

  # Create a number of persistent programs.
  # he values for BLOCK_SIZE , num_stages , and num_warps were already baked into the kernel object during the warmup phase.
  kernel[(num_programs, 1, 1)](y, x, x.stride(0), y.stride(0), n_rows, n_cols)
  return y


# %%
# Unit Test
# ---------

# %%
# We make sure that we test our kernel on a matrix with an irregular number of rows and columns.
# This will allow us to verify that our padding mechanism works.

torch.manual_seed(0)
x = torch.randn(1823, 781, device=DEVICE)
y_triton = softmax(x)
y_torch = torch.softmax(x, axis=1)
assert torch.allclose(y_triton, y_torch), (y_triton, y_torch)


@triton.testing.perf_report(
  triton.testing.Benchmark(
    x_names=['N'],  # argument names to use as an x-axis for the plot
    x_vals=[128 * i for i in range(2, 100)],  # different possible values for `x_name`
    line_arg='provider',  # argument name whose value corresponds to a different line in the plot
    line_vals=['triton', 'torch', 'naive', 'torch_compile'],  # possible values for `line_arg``
    line_names=[
      "Triton",
      "Torch",
      "Naive",
      "Torch Compile",
    ],  # label name for the lines
    styles=[('blue', '-'), ('green', '-'), ('red', '--'), ('magenta', ':')],  # line styles
    ylabel="GB/s",  # label name for the y-axis
    plot_name="softmax-performance",  # name for the plot. Used also as a file name for saving the plot.
    args={'M': 4096},  # values for function arguments not in `x_names` and `y_name`
  ))
def benchmark(M, N, provider):
  x = torch.randn(M, N, device=DEVICE, dtype=torch.float32)
  stream = torch.cuda.Stream()
  torch.cuda.set_stream(stream)
  if provider == 'torch':
    ms = triton.testing.do_bench(lambda: torch.softmax(x, axis=-1))
  if provider == 'triton':
    ms = triton.testing.do_bench(lambda: softmax(x))
  # Calculate GB/s. Note: naive_softmax reads/writes more data,
  # but for fair comparison with fused kernels, we often use the minimal theoretical I/O (2*M*N)
  if provider == 'naive':
    ms = triton.testing.do_bench(lambda: naive_softmax(x))
  if provider == 'torch_compile':
    ms = triton.testing.do_bench(lambda: compiled_naive_softmax(x))
  # Calculate GB/s.
  gbps = lambda ms: 2 * x.numel() * x.element_size() * 1e-9 / (ms * 1e-3)
  return gbps(ms)


benchmark.run(show_plots=True, print_data=True, save_path='.')

# %%
# In the above plot, we can see that:
#  - Triton is noticeably faster than :code:`torch.softmax` -- in addition to being **easier to read, understand and maintain**.
#    Note however that the PyTorch `softmax` operation is more general and will work on tensors of any shape.


# softmax-performance:
# N       Triton        Torch       Naive  Torch Compile
# 0     256.0   517.827501   900.092921  229.534363     901.881639
# 1     384.0   793.354332  1077.564322  303.081560     765.490341
# 2     512.0  1028.380394  1272.203464  348.274317    1004.857868
# 3     640.0  1196.569289  1309.992345  391.156678     886.821517
# 4     768.0  1428.508325  1497.599978  423.023030    1052.987376
# 5     896.0  1619.062540  1596.098415  445.889904    1220.842188
# 6    1024.0  1793.886334  1720.608749  464.112402    1373.879173
# 7    1152.0  1687.211016   625.491994  482.712744    1224.339378
# 8    1280.0  1844.467440   683.845411  482.866207    1342.632074
# 9    1408.0  1987.978926   744.926756  489.885569    1460.072036
# 10   1536.0  2058.919231   796.125208  484.092808    1559.942816
# 11   1664.0  2121.913874   833.069931  479.314983    1417.579960
# 12   1792.0  2187.988990   885.001788  477.348887    1503.766447
# 13   1920.0  2252.681814   937.369420  474.095271    1585.483324
# 14   2048.0  2291.907624   986.255066  475.731032    1679.253504
# 15   2176.0  2093.652909  1012.475279  479.066435    1551.256678
# 16   2304.0  2201.668315  1064.468037  476.530062    1617.560337
# 17   2432.0  2308.765068  1114.194647  479.759246    1703.541652
# 18   2560.0  2396.996435  1153.521557  480.439430    1773.657283
# 19   2688.0  2458.257379  1178.605224  483.999217    1642.543737
# 20   2816.0  2460.641627  1224.124914  485.257227    1710.221370
# 21   2944.0  2488.145510  1265.112563  484.634422    1771.241508
# 22   3072.0  2487.159969  1298.747507  486.067974    1830.593889
# 23   3200.0  2479.295834  1321.887122  486.417190    1707.898289
# 24   3328.0  2492.238525  1362.902713  484.770719    1768.415641
# 25   3456.0  2493.729028  1403.058271  487.410716    1821.145236
# 26   3584.0  2533.720160  1431.556168  486.532966    1883.128794
# 27   3712.0  2537.715464  1451.974793  488.576336    1772.048195
# 28   3840.0  2540.323489  1486.604459  489.105293    1816.772051
# 29   3968.0  2581.843727  1517.984937  488.503419    1853.414471
# 30   4096.0  2577.099884  1538.094665  489.324480    1900.058993
# 31   4224.0  2183.898312  1377.184291  489.537488    1801.282124
# 32   4352.0  2229.731245  1393.613260  489.655646    1847.757970
# 33   4480.0  2282.757131  1408.965102  491.420229    1875.052840
# 34   4608.0  2336.805798  1421.321103  490.590807    1912.617140
# 35   4736.0  2375.245833  1444.266024  492.529520    1819.039024
# 36   4864.0  2434.347427  1471.466747  493.541453    1839.655261
# 37   4992.0  2476.745457  1490.632641  493.798867    1863.147447
# 38   5120.0  2518.189232  1514.660869  494.258327    1895.992225
# 39   5248.0  2567.634087  1535.533200  495.875425    1808.827349
# 40   5376.0  2615.642397  1568.465121  495.443718    1832.672642
# 41   5504.0  2656.117183  1588.312070  497.167481    1861.953370
# 42   5632.0  2708.872560  1611.762170  496.751096    1875.918452
# 43   5760.0  2731.921548  1627.636931  497.982023    1806.339350
# 44   5888.0  2777.482890  1653.450245  498.666161    1821.965128
# 45   6016.0  2814.002260  1667.078384  498.310738    1824.405436
# 46   6144.0  2852.386110  1690.942613  499.153406    1846.370792
# 47   6272.0  2890.538507  1714.140961  499.926088    1769.373431
# 48   6400.0  2921.292822  1737.242380  500.000882    1785.417146
# 49   6528.0  2986.144197  1759.108229  501.882645    1792.682897
# 50   6656.0  3011.199558  1778.478004  501.048461    1816.700245
# 51   6784.0  3038.972312  1790.017459  502.471396    1737.975340
# 52   6912.0  3068.100743  1808.572970  503.301527    1747.906775
# 53   7040.0  3074.661833  1830.693021  502.506629    1759.638718
# 54   7168.0  3094.787105  1844.512485  502.945694    1775.582100
# 55   7296.0  3090.080255  1863.275384  504.598025    1699.080651
# 56   7424.0  2999.415781  1876.388340  504.801113    1708.902118
# 57   7552.0  2938.079124  1896.834771  505.394959    1701.616541
# 58   7680.0  2901.593742  1916.026405  505.017087    1706.251924
# 59   7808.0  2944.104803  1928.299014  505.897220    1650.474171
# 60   7936.0  2921.363515  1944.025248  506.602017    1642.741756
# 61   8064.0  2865.326648  1944.216813  507.109908    1653.893791
# 62   8192.0  2853.217605  1958.393539  472.469207    1656.466713
# 63   8320.0  1721.062160  1884.017558  470.639939    1595.463179
# 64   8448.0  1744.410443  1866.131318  470.526703    1598.465913
# 65   8576.0  1768.569586  1869.915509  472.319155    1596.432524
# 66   8704.0  1784.002133  1869.695071  473.300539    1598.723114
# 67   8832.0  1805.408442  1873.493928  474.630584    1553.205332
# 68   8960.0  1817.919551  1866.232367  475.644278    1547.308125
# 69   9088.0  1848.500529  1886.542450  476.691237    1542.680334
# 70   9216.0  1867.751504  1897.767315  478.488132    1558.327229
# 71   9344.0  1888.822210  1908.966040  479.504191    1511.286714
# 72   9472.0  1910.178179  1914.283138  479.920934    1506.897850
# 73   9600.0  1937.901878  1927.473729  481.880620    1506.630710
# 74   9728.0  1948.550934  1919.804057  482.437746    1525.239796
# 75   9856.0  1966.416495  1941.862952  483.966344    1477.812615
# 76   9984.0  1989.700721  1966.758952  485.265986    1481.632000
# 77  10112.0  2009.835013  1966.703489  485.706319    1476.606416
# 78  10240.0  2020.859796  1980.401093  487.392007    1479.793188
# 79  10368.0  2045.068165  1994.828124  486.191773    1450.082591
# 80  10496.0  2079.544358  1997.938960  486.176311    1453.601814
# 81  10624.0  2100.706097  2019.173859  487.071532    1446.759960
# 82  10752.0  2116.814580  2037.448580  488.100367    1464.593137
# 83  10880.0  2122.871296  2039.206100  488.577472    1423.447786
# 84  11008.0  2163.743698  2046.561662  489.742038    1424.893619
# 85  11136.0  2173.474971  2066.965575  490.198383    1422.701467
# 86  11264.0  2190.109990  2074.734954  491.420251    1445.703101
# 87  11392.0  2194.175153  2088.884649  492.065110    1416.387725
# 88  11520.0  2235.774182  2089.577119  491.994964    1418.264317
# 89  11648.0  2252.905173  2096.708798  494.017927    1416.862099
# 90  11776.0  2270.833546  2114.072408  494.140464    1425.627565
# 91  11904.0  2265.595880  2118.824742  496.223156    1405.544049
# 92  12032.0  2311.228077  2134.006126  496.459903    1409.518702
# 93  12160.0  2317.522006  2139.404423  496.676163    1403.957945
# 94  12288.0  2339.770303  1262.128245  497.994865    1424.816418
# 95  12416.0  2352.785642  1218.213569  497.532784    1393.222614
# 96  12544.0  2375.355736  1209.083998  497.898804    1404.065587
# 97  12672.0  2397.072891  1215.697461  498.060463    1405.200655

