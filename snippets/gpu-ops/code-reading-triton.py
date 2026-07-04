

*** usage

* atomic_cas，支持block处理

https://github.com/triton-lang/triton/pull/2514

- test_core中的用法测试



* reduce op

lib/Conversion/TritonGPUToLLVM/ReduceOpToLLVM.cpp


struct ReduceOpConversion
    : public ConvertTritonGPUReduceScanToLLVMPattern<triton::ReduceOp>
   	LogicalResult
  matchAndRewrite(triton::ReduceOp op, OpAdaptor adaptor,
                  ConversionPatternRewriter &rewriter) const override {

  	// First reduce all the values along axis within each thread.
    reduceWithinThreads(helper, srcValues, accs, indices, rewriter);

    // Then reduce across threads within a warp.
    reduceWithinWarps(helper, accs, rewriter);

    storeWarpReduceToSharedMemory(helper, accs, indices, smemBases, rewriter);


    accumulatePartialReductions(helper, smemBases, rewriter);

    loadReductionAndPackResult(helper, smemShape, smemBases, rewriter);




*** AOT compile and link

compiler = os.path.join(triton.tools.__path__[0], "compile.py")


python/triton/tools/link.py

linker = os.path.join(triton.tools.__path__[0], "link.py")


*** cubin

直接通过`libcuda.so`调用驱动，直接把Python代码翻译成驱动可执行的cubin程序

* https://github.com/triton-lang/triton/blob/main/third_party/nvidia/backend/driver.py