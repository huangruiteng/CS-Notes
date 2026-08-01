*** examples/cute/tutorial/sgemm_2.cu



*** examples/cute/tutorial/hopper/wgmma_tma_sm90.cu

Reading material :
• https://github.com/NVIDIA/cutlass/blob/main/media/docs/cute/
• https://www.nvidia.com/en-us/on-demand/session/gtcspring23-s51413/
• https://www.nvidia.com/en-us/on-demand/session/gtc24-s61198/
• https://github.com/NVIDIA/cutlass/pull/1578

void gemm_tn() {
  ...
  // Define TN strides (mixed)
  auto dA = make_stride(ldA, Int<1>{});                      // (dM, dK)
  auto dB = make_stride(ldB, Int<1>{});                      // (dN, dK)
  auto dC = make_stride(Int<1>{}, ldC);                      // (dM, dN)

  // Define CTA tile sizes (static)
  auto bM = Int<128>{};
  auto bN = Int<128>{};
  auto bK = Int< 64>{};
  auto cta_tiler = make_shape(bM, bN, bK);                   // (BLK_M, BLK_N, BLK_K)
  auto bP = Int<3>{};  // Pipeline

  // Define the smem layouts (static)
  // GMMA::Layout_K_SW128_Atom: swizzling
  // Layout_K_SW128_Atom 是一种针对K维度（即 A^T 的行维度）优化的布局。
  // 它确保了在共享内存中， A^T 的行是 物理上连续或以最优方式交错 存储的，以避免共享内存bank conflict，从而实现高效的访问。
  auto sA = tile_to_shape(GMMA::Layout_K_SW128_Atom<TA>{}, make_shape(bM,bK,bP));
  auto sB = tile_to_shape(GMMA::Layout_K_SW128_Atom<TB>{}, make_shape(bN,bK,bP));

  // Define the thread layouts (static)
  TiledCopy copyA = make_tiled_copy(Copy_Atom<SM80_CP_ASYNC_CACHEALWAYS<uint128_t>, TA>{},
                                    Layout<Shape<_16,_8>,Stride<_8,_1>>{}, // Thr layout 16x8 k-major
                                    Layout<Shape< _1,_8>>{});              // Val layout  1x8
  TiledCopy copyB = make_tiled_copy(Copy_Atom<SM80_CP_ASYNC_CACHEALWAYS<uint128_t>, TB>{},
                                    Layout<Shape<_16,_8>,Stride<_8,_1>>{}, // Thr layout 16x8 k-major
                                    Layout<Shape< _1,_8>>{});              // Val layout  1x8

  TiledMMA tiled_mma = make_tiled_mma(SM90_64x64x16_F16F16F16_SS<GMMA::Major::K,GMMA::Major::K>{});

  // Define the TMAs
  // Create Global memory tensors for TMA inspection
  Tensor mA = make_tensor(A, make_shape(M,K), dA);
  Tensor mB = make_tensor(B, make_shape(N,K), dB);

  // Create TMA Atoms with the desired copy operation on the source and destination
  Copy_Atom tmaA = make_tma_atom(SM90_TMA_LOAD{}, mA, sA(_,_,0), make_shape(bM,bK));
  Copy_Atom tmaB = make_tma_atom(SM90_TMA_LOAD{}, mB, sB(_,_,0), make_shape(bN,bK));

  //
  // Setup and Launch
  //

  // Launch parameter setup
  int smem_size = int(sizeof(SharedStorage<TA, TB, decltype(sA), decltype(sB)>));
  dim3 dimBlock(size(tiled_mma));
  dim3 dimCluster(2, 1, 1);
  dim3 dimGrid(round_up(size(ceil_div(m, bM)), dimCluster.x),
               round_up(size(ceil_div(n, bN)), dimCluster.y));
  cutlass::ClusterLaunchParams params = {dimGrid, dimBlock, dimCluster, smem_size};

  void const* kernel_ptr = reinterpret_cast<void const*>(
                              &gemm_device<decltype(prob_shape), decltype(cta_tiler),
                                           TA, decltype(sA), decltype(tmaA),
                                           TB, decltype(sB), decltype(tmaB),
                                           TC, decltype(dC), decltype(tiled_mma),
                                           decltype(alpha), decltype(beta)>);

  CUTE_CHECK_ERROR(cudaFuncSetAttribute(
    kernel_ptr,
    cudaFuncAttributeMaxDynamicSharedMemorySize,
    smem_size));

  // Kernel Launch
  cutlass::Status status = cutlass::launch_kernel_on_cluster(params, kernel_ptr,
                                                             prob_shape, cta_tiler,
                                                             A, tmaA,
                                                             B, tmaB,
                                                             C, dC, tiled_mma,
                                                             alpha, beta);
  CUTE_CHECK_LAST();

  if (status != cutlass::Status::kSuccess) {
    std::cerr << "Error: Failed at kernel Launch" << std::endl;
  }

}

TN: transpose A: row major; B: column major


...
void
gemm_device(ProblemShape shape_MNK, CtaTiler cta_tiler,
            TA const* A, CUTLASS_GRID_CONSTANT TmaA const tma_a,
            TB const* B, CUTLASS_GRID_CONSTANT TmaB const tma_b,
            TC      * C, CStride dC, TiledMma mma,
            Alpha alpha, Beta beta)
{
  // Full and Tiled Tensors
  //

  // Represent the full tensors
  auto [M, N, K] = shape_MNK;
  Tensor mA = tma_a.get_tma_tensor(make_shape(M,K));                   // (M,K) TMA Tensor
  Tensor mB = tma_b.get_tma_tensor(make_shape(N,K));                   // (N,K) TMA Tensor
  Tensor mC = make_tensor(make_gmem_ptr(C), make_shape(M,N), dC);      // (M,N)

  // Get the appropriate blocks for this thread block
  auto cta_coord = make_coord(blockIdx.x, blockIdx.y, _);              // (m,n,k)
  Tensor gA = local_tile(mA, cta_tiler, cta_coord, Step<_1, X,_1>{});  // (BLK_M,BLK_K,k)
  Tensor gB = local_tile(mB, cta_tiler, cta_coord, Step< X,_1,_1>{});  // (BLK_N,BLK_K,k)
  Tensor gC = local_tile(mC, cta_tiler, cta_coord, Step<_1,_1, X>{});  // (BLK_M,BLK_N)

  // Shared memory tensors
  extern __shared__ char shared_memory[];
  using SharedStorage = SharedStorage<TA, TB, SmemLayoutA, SmemLayoutB>;
  SharedStorage& smem = *reinterpret_cast<SharedStorage*>(shared_memory);
  Tensor sA = make_tensor(make_smem_ptr(smem.A.begin()), SmemLayoutA{}); // (BLK_M,BLK_K,PIPE)
  Tensor sB = make_tensor(make_smem_ptr(smem.B.begin()), SmemLayoutB{}); // (BLK_N,BLK_K,PIPE)

  //
  // Partition the copying of A and B tiles
  //
  // TUTORIAL:
  //   These are TMA partitionings, which have a dedicated custom partitioner.
  //   The Int<0>, Layout<_1> indicates that the TMAs are not multicasted.
  //     Any multicasting must be in conformance with tma_x constructed with make_tma_atom on host.
  //   The group_modes<0,2> transforms the (X,Y,Z)-shaped tensors into ((X,Y),Z)-shaped tensors
  //     with the understanding that the TMA is responsible for everything in mode-0.
  //   The tma_partition reorders and offsets mode-0 according to the tma_x atom and the multicast info.
  //

  // 同时partition sA和gA，为tma做准备
  auto [tAgA, tAsA] = tma_partition(tma_a, Int<0>{}, Layout<_1>{},
                                    group_modes<0,2>(sA), group_modes<0,2>(gA));  // (TMA,k) and (TMA,PIPE)

  auto [tBgB, tBsB] = tma_partition(tma_b, Int<0>{}, Layout<_1>{},
                                    group_modes<0,2>(sB), group_modes<0,2>(gB));  // (TMA,k) and (TMA,PIPE)

  // The TMA is responsible for copying everything in mode-0 of tAsA and tBsB
  constexpr int tma_transaction_bytes = sizeof(make_tensor_like(tensor<0>(tAsA)))
                                      + sizeof(make_tensor_like(tensor<0>(tBsB)));
  ...

  int warp_idx = cutlass::canonical_warp_idx_sync();
  int lane_predicate = cute::elect_one_sync();
  uint64_t* producer_mbar = smem.tma_barrier;
  uint64_t* consumer_mbar = smem.mma_barrier;

  using ProducerBarType = cutlass::arch::ClusterTransactionBarrier;  // TMA
  using ConsumerBarType = cutlass::arch::ClusterBarrier;             // MMA
  CUTE_UNROLL
  for (int pipe = 0; pipe < K_PIPE_MAX; ++pipe) {
    if ((warp_idx == 0) && lane_predicate) {
      ProducerBarType::init(&producer_mbar[pipe],   1);
      ConsumerBarType::init(&consumer_mbar[pipe], 128);
    }
  }
  // Ensure barrier init is complete on all CTAs
  cluster_sync();

  // Start async loads for all pipes
  CUTE_UNROLL
  for (int pipe = 0; pipe < K_PIPE_MAX; ++pipe)
  {
    if ((warp_idx == 0) && lane_predicate)
    {
      // Set expected Tx Bytes after each reset / init
      ProducerBarType::arrive_and_expect_tx(&producer_mbar[pipe], tma_transaction_bytes);
      copy(tma_a.with(producer_mbar[pipe]), tAgA(_,k_tile), tAsA(_,pipe));
      copy(tma_b.with(producer_mbar[pipe]), tBgB(_,k_tile), tBsB(_,pipe));
    }
    --k_tile_count;
    ++k_tile;
  }
  ...
  //
  // Define A/B partitioning and C accumulators
  //
  // TUTORIAL:
  //   The tCrA and tCrB are actually Tensors of MMA Descriptors constructed as views of SMEM.
  //   The MMA Descriptor generation is automatic via inspection and validation of the SMEM Layouts.
  //   Because the MMA reads directly from SMEM and the fragments are descriptors rather than registers,
  //     there is no need for copy(tCsA, tCrA) in the mainloop.
  //

  ThrMMA thr_mma = mma.get_thread_slice(threadIdx.x);
  Tensor tCsA = thr_mma.partition_A(sA);                               // (MMA,MMA_M,MMA_K,PIPE)
  Tensor tCsB = thr_mma.partition_B(sB);                               // (MMA,MMA_N,MMA_K,PIPE)
  Tensor tCgC = thr_mma.partition_C(gC);                               // (MMA,MMA_M,MMA_N)

  // Allocate accumulators and clear them
  Tensor tCrC = thr_mma.make_fragment_C(tCgC);                         // (MMA,MMA_M,MMA_N)
  clear(tCrC);

  // Allocate "fragments"
  Tensor tCrA = thr_mma.make_fragment_A(tCsA);                         // (MMA,MMA_M,MMA_K,PIPE)
  Tensor tCrB = thr_mma.make_fragment_B(tCsB);                         // (MMA,MMA_N,MMA_K,PIPE)


  //
  // PIPELINED MAIN LOOP
  //
  // TUTORIAL:
  //   Rather than interleaving the stages and instructions like in SM70 and SM80,
  //     the SM90 mainloops rely on explicit producer-consumer synchronization
  //     on the purely async instructions TMA and MMA.
  //   More advanced pipeline and warp-specialization strategies are available in CUTLASS mainloops.
  //

  // A PipelineState is a circular pipe index [.index()] and a pipe phase [.phase()]
  //   that flips each cycle through K_PIPE_MAX.
  auto write_state = cutlass::PipelineState<K_PIPE_MAX>();             // TMA writes
  auto read_state  = cutlass::PipelineState<K_PIPE_MAX>();             // MMA  reads

  CUTE_NO_UNROLL
  while (k_tile_count > -K_PIPE_MAX)
  {
    // Wait for Producer to complete
    int read_pipe = read_state.index();
    ProducerBarType::wait(&producer_mbar[read_pipe], read_state.phase());

    // MMAs to cover 1 K_TILE
    warpgroup_arrive();
    gemm(mma, tCrA(_,_,_,read_pipe), tCrB(_,_,_,read_pipe), tCrC);     // (V,M) x (V,N) => (V,M,N)
    warpgroup_commit_batch();

    // Wait for all MMAs in a K_TILE to complete
    warpgroup_wait<0>();

    // Notify that consumption is done
    ConsumerBarType::arrive(&consumer_mbar[read_pipe]);
    ++read_state;

    if ((warp_idx == 0) && lane_predicate)
    {
      int pipe = write_state.index();
      // Wait for Consumer to complete consumption
      ConsumerBarType::wait(&consumer_mbar[pipe], write_state.phase());
      // Set expected Tx Bytes after each reset / init
      ProducerBarType::arrive_and_expect_tx(&producer_mbar[pipe], tma_transaction_bytes);
      copy(tma_a.with(producer_mbar[pipe]), tAgA(_,k_tile), tAsA(_,pipe));
      copy(tma_b.with(producer_mbar[pipe]), tBgB(_,k_tile), tBsB(_,pipe));
      ++write_state;
    }
    --k_tile_count;
    ++k_tile;
  }

  //
  // Epilogue (unpredicated)
  //

  axpby(alpha, tCrC, beta, tCgC);
}

*** pingpong gemm

https://pytorch.org/blog/cutlass-ping-pong-gemm-kernel/

