cutlass = cutlass + cute

nvcc -std=c++17 examples/cute/tutorial/tiled_copy.cu -o examples/cute/tutorial/tiled_copy_app -I include -I tools/util/include

*** tutorials

https://docs.nvidia.com/cutlass/media/docs/cpp/cute/00_quickstart.html

*** setup cutlass gemm

https://github.com/pytorch-labs/applied-ai/blob/main/kernels/cuda/cutlass_gemm/setup.py
https://research.colfax-intl.com/tutorial-python-binding-for-cuda-libraries-in-pytorch/

*** 编程模型

- underscores: some_tensor(2, _, _)
- local_tile
- local_partition
- partition_D
- partition_S
- _3

- [A..B) half-open integers

- CuTe的mode概念

	在CuTe的语境下：

	- Mode 是构成数据布局描述的基本单元。
	- 它存在于一个（可能） 嵌套的元组结构 中。
	- 一个mode可以是一个 标量值 （比如一个整数，代表一个维度的大小或步长），也可以是 另一个元组 （代表更深层次的结构或组合的维度特征）。
	这种设计允许CuTe以一种非常灵活和可组合的方式来描述和操作复杂的多维数据布局，这对于在GPU上高效实现线性代数运算（如GEMM）至关重要。
	例如，一个张量的形状 (M, N, K) 可以被看作是一个包含三个mode（M, N, K）的元组。如果这个张量在内存中是分块存储的，
	那么每个mode（M, N, K）自身可能又被一个更复杂的mode（可能是一个元组）所替代，用以描述其分块细节。

- indexing: dot_product((i,j,k), (1,M,MN))
	- layout: (M,N,K):(1,M,MN)
		- stride: (1,M,MN)
		- shape: (M,N,K)
	- 定义concat layout: (3:1, 2:3) = (3,2):(1,3)
	- nested layout: ((3,4), 2):((1,3), 40)
		- accept coordinates like ((1,2), 1)


e.g.  (3,4):(1,3)    -> column major
	  (3,4):(4,1)   -> row major

(a,b,c,d):LayoutLeft = (a,b,c,d):(1,a,ab,abc) -> Generalized Column Major
(a,b,c,d):LayoutRight = (a,b,c,d):(bcd,cd,d,1) -> Row Major 逐行存储


** tile

- layout：仅改变shape，stride和大tensor一致
- 多个tile之间：layout一致、engine(tensor offset)和shape不一致

e.g (5,6)起点的tile(3,5):(1,M) offset: 5*1+6*M


big tensor: T, tile: t

- with_shape
	function composition: T and layout(t)
	如果静态，可以compile time生成
- local_tile
- local_partition
- compose/composition 

A*B*C、a*b*c

T1 tiled by T2
T1/T2 -> T3

(A,B,C)/(a,b,c) = ((a,b,c), (A/a, B/b, C/c))
				  inner mode    outer mode

(A,B,C)/(a,c) = ((a,c), (A/a,B,C/c))


** layout的tile运算

layout/shape -> layout

(A,B,C):(1,A,AB) / (a,b,c)
->
(a,b,c):(1,M,MN),(A/a,B/b,C/c):(a,bM,cMN)

** nested layout

比如 (thread_idx, value_idx)对应 (threads_per_block, value_num), threads_per_block是一个mode


** 关于check
利用_3等概念，check at compile time

** non contiguous

3:2    ->    i=0,1,2, offset=2*i


*** cute API

Spatial microkernels: cute::Tiled{Mma|Copy}<>
- Robust representation power across a wide range GPU architectures

Temporal Microkernels: collective::Collective{Mma|Conv|Epilogue|Transform}<>
- Dispatched against by policies that also define the set of kernel schedules they can be composed with

Kernel layer: kernel::{Gemm|Conv}Universal<>
- Treats GEMM as a composition of a collective mainloop and a collective epilogue
- Tile Schedulers are a first class at this level – decide which tile coords map to which program ID

Device layer: device::{Gemm|Conv}UniversalAdapter<>
- Just a handle object to the kernel
- cutlass::Pipeline: used for abstracting synchronization across or within the layers

Static asserts everywhere to guard against invalid compositions or incorrect layouts


** collective API

// Dispatch policy examples
// 2 stage pipeline through 1 stage in smem, 1 in rmem, with predicated gmem loads
struct MainloopSm70TwoStage;

// n-buffer in smem (cp.async), pipelined with registers, WITHOUT predicated gmem loads
struct MainloopSm80CpAsyncUnpredicated;

// n-buffer in smem (TMA), pipelined with Hopper GMMA and TMA, Warp specialized dynamic schedule
struct MainloopSm90TmaGmmaWarpSpecialized;

template <
    class DispatchPolicy,
    class TileShape,
    class ElementA,
    class SmemLayoutA,
    class ElementB,
    class SmemLayoutB,
    class ElementC,
    class ArchTag,
    class TiledMma,
    class GmemCopyAtomA,
    class SmemCopyAtomA,
    class GmemCopyAtomB,
    class SmemCopyAtomB
>
struct CollectiveMma;


* 49_hopper_gemm_schedules_with_collective_builder

- “I want a Hopper collective but composed with persistent kernel and 5 stages”

using CollectiveOp = typename collective::CollectiveBuilder<
	arch::Sm90, arch::OpClassTensorOp,
	half_t, LayoutA, 8,
	half_t, LayoutB, 8,
	float,
	Shape<_128,_128,_64>, Shape<_1,_2,_1>,
	gemm::collective::StageCount<5>,
	gemm::KernelTmaWarpSpecializedPersistent
	>::CollectiveOp;



*** profiler

https://docs.nvidia.com/cutlass/media/docs/cpp/profiler.html

* CUTLASS has a python based kernel emitter and a manifest to hold a bunch of kernels
* Autotuning strategy is to stamp out a set of candidates kernels and then …
* Use the CUTLASS profiler to pick the best kernel for your problems of interest
* It is also possible to dump ptx of the best performing kernel with `cuobjdump` or –DCUTLASS_NVCC_KEEP

*** write custom kernels

template<
    int Stages_,
    class ClusterShape_ = Shape<-1,-1,-1>,
    class KernelSchedule = KernelTmaWarpSpecialized // or KernelTmaWarpSpecializedPersistent
>
struct MyCustomHopperMainloopWoot {
    constexpr static int Stages = Stages_;
    using ClusterShape = ClusterShape_;
    using ArchTag = arch::Sm90;
    using Schedule = KernelSchedule;
};

** epilogue fusion

有python interface，参考gpu-cutlass.py

using EVTOutput = Sm90LinCombPerRowBiasEltAct<
TileShape, ReLu, ElementOutput, ElementCompute>;

<->

using Alpha = Sm90ScalarBroadcast<ElementScalar>;
using Accum = Sm90AccFetch;
using Bias = Sm90ColBroadcast<
    0, TileShape, ElementBias, Stride<-1,0,int>, AlignmentBias>;
using MultiplyAdd = Sm90Compute<
    multiply_add, ElementCompute, ElementCompute, RoundStyle>;
using EVTCompute0 = Sm90EVT<MultiplyAdd, Alpha, Accum, Bias>;

using Beta = Sm90ScalarBroadcast<ElementScalar>;
using C = Sm90SrcFetch<ElementSource>;
using EVTCompute1 = Sm90EVT<MultiplyAdd, Beta, C, EVTCompute0>;

using ReLUAct = Sm90Compute<
    ReLu, ElementOutput, ElementCompute, RoundStyle>;
using EVTOutput = Sm90EVT<ReLUAct, EVTCompute1>;

using CollectiveEpilogue = typename
cutlass::epilogue::collective::CollectiveBuilder<
    cutlass::arch::Sm90, cutlass::arch::OpClassTensorOp,
    TileShape, ClusterShape,
    cutlass::epilogue::collective::EpilogueTileAuto,
    ElementAccumulator, ElementCompute,
    ElementC, LayoutC, AlignmentC,
    ElementD, LayoutD, AlignmentD,
    EpilogueScheduleType,
    EVTOutput
>::CollectiveOp;


*** examples

** GETT

examples/51_hopper_gett/gett_kernel.cuh

// Build the mainloop type
using CollectiveMainloop = typename cutlass::gemm::collective::CollectiveBuilder<
    arch::Sm90, arch::OpClassTensorOp,
    ElementA, StrideA, AlignmentA,
    ElementB, StrideB, AlignmentB,
    ElementAccumulator,
    TilesShape, ClusterShape,
    cutlass::gemm::collective::StageCountAuto,
    cutlass::gemm::collective::KernelScheduleAuto
>::CollectiveOp;

// Build the epilogue type
using CollectiveEpilogue = typename cutlass::epilogue::collective::CollectiveBuilder<
    arch::Sm90, arch::OpClassTensorOp,
    TileShape, ClusterShape,
    cutlass::epilogue::collective::EpilogueTileAuto,
    ElementAccumulator, ElementCompute,
    ElementC, StrideC, AlignmentC,
    ElementD, StrideD, AlignmentD,
    cutlass::epilogue::collective::EpilogueScheduleAuto
>::CollectiveOp;

// Compose both at the kernel layer, and define the type of our problem shape tuple
using GettKernel = cutlass::gemm::kernel::GemmUniversal<
    ProblemShape_MNKL, // still a rank-4 tuple, but now is hierarchical
    CollectiveMainloop,
    CollectiveEpilogue>;

// Device layer handle to the kernel
using Gett = cutlass::gemm::device::GemmUniversalAdapter<GettKernel>;


*** cute/tutorials

** tiled_copy.cu

nvcc -std=c++17 examples/cute/tutorial/tiled_copy.cu -o examples/cute/tutorial/tiled_copy_app -I include -I tools/util/include
