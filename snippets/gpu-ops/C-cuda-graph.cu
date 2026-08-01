
*** record

cudaGraph_t graph;
cudaStreamBeginCapture(stream);
... CUDA calls on stream
cudaStreamEndCapture(stream, &graph);

*** make CPU code async

cudaGraph_t graph;
cudaStreamBeginCapture(a);
kernel1<<<,,,a>>>();
cudaEventRecord(e1, a);
kernel2<<<,,,b>>>();
cudaStreamWaitEvent(b, e1);
cudaMemcpyAsync(,,,,b);
kernel3<<<,,,a>>>();
cudaEventRecord(e3, a);

cudaLaunchHostFunc(b, cpucode, params);

cudaStreamWaitEvent(b, e3);
kernel4<<<,,,b>>>();
cudaStreamEndCapture(a, &graph);



*** explicit

cudaGraph_t graph;
cudaGraphCreate(&graph, 0);
cudaGraphNode_t k1,k2,k3,k4,mc,cpu;


cudaGraphAddKernelNode(&k1, graph,
0, 0, // no dependency yet
paramsK1, 0);
...
cudaGraphAddKernelNode(&k4, graph,
0, 0, paramsK4, 0);
cudaGraphAddMemcpyNode(&mc, graph,
0, 0, paramsMC);
cudaGraphAddHostNode(&cpu, graph,
0, 0, paramsCPU);


__host__ cudaError_t
cudaGraphAddKernelNode(cudaGraphNode_t* pGraphNode,
	cudaGraph_t graph, const cudaGraphNode_t* pDependencies,
	size_t numDependencies, const cudaKernelNodeParams* pNodeParams);


struct cudaKernelNodeParams
{
	void* func; // Kernel function
	dim3 gridDim;
	dim3 blockDim;
	unsigned int sharedMemBytes;
	void **kernelParams; // Array of pointers to arguments
	void **extra; // (low-level alternative to kernelParams)
};

cudaGraphAddDependencies(graph,
	&k1, &k3, 1); // kernel1 -> kernel3
cudaGraphAddDependencies(graph,
	&k1, &mc, 1); // kernel1 -> memcpy
cudaGraphAddDependencies(graph,
	&k2, &mc, 1); // kernel2 -> memcpy
cudaGraphAddDependencies(graph,
	&mc, &cpu, 1); // memcpy -> cpu
cudaGraphAddDependencies(graph,
	&k3, &k4, 1); // kernel3 -> kernel4
cudaGraphAddDependencies(graph,
	&cpu, &k4, 1); // cpu -> kernel4

// Instantiating and running the graph
cudaGraphExec_t exec;
cudaGraphInstantiate(&exec, graph, 0, 0, 0);
cudaGraphLaunch(exec, stream);
cudaStreamSynchronize(stream);
	
- Once a graph is instantiated, its topology cannot be changed
- Kernel/memcpy/call… parameters can still be changed using cudaGraphExecUpdate
	or cudaGraphExec{Kernel,Host,Memcpy,Memset}NodeSetParams