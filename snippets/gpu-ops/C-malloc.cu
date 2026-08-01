*** stream

#include <stdio.h>

__global__
void initWith(float num, float *a, int N)
{

  int index = threadIdx.x + blockIdx.x * blockDim.x;
  int stride = blockDim.x * gridDim.x;

  for(int i = index; i < N; i += stride)
  {
    a[i] = num;
  }
}

__global__
void addVectorsInto(float *result, float *a, float *b, int N)
{
  int index = threadIdx.x + blockIdx.x * blockDim.x;
  int stride = blockDim.x * gridDim.x;

  for(int i = index; i < N; i += stride)
  {
    result[i] = a[i] + b[i];
  }
}

void checkElementsAre(float target, float *vector, int N)
{
  for(int i = 0; i < N; i++)
  {
    if(vector[i] != target)
    {
      printf("FAIL: vector[%d] - %0.0f does not equal %0.0f\n", i, vector[i], target);
      exit(1);
    }
  }
  printf("Success! All values calculated correctly.\n");
}

int main()
{
  int deviceId;
  int numberOfSMs;

  cudaGetDevice(&deviceId);
  cudaDeviceGetAttribute(&numberOfSMs, cudaDevAttrMultiProcessorCount, deviceId);

  const int N = 2<<24;
  size_t size = N * sizeof(float);

  float *a;
  float *b;
  float *c;
  float *h_c;

  cudaMalloc(&a, size);
  cudaMalloc(&b, size);
  cudaMalloc(&c, size);
  cudaMallocHost(&h_c, size);

  size_t threadsPerBlock;
  size_t numberOfBlocks;

  threadsPerBlock = 256;
  numberOfBlocks = 32 * numberOfSMs;

  cudaError_t addVectorsErr;
  cudaError_t asyncErr;

  /*
   * Create 3 streams to run initialize the 3 data vectors in parallel.
   */

  cudaStream_t stream1, stream2, stream3;
  cudaStreamCreate(&stream1);
  cudaStreamCreate(&stream2);
  cudaStreamCreate(&stream3);

  /*
   * Give each `initWith` launch its own non-standard stream.
   */

  initWith<<<numberOfBlocks, threadsPerBlock, 0, stream1>>>(3, a, N);
  initWith<<<numberOfBlocks, threadsPerBlock, 0, stream2>>>(4, b, N);
  initWith<<<numberOfBlocks, threadsPerBlock, 0, stream3>>>(0, c, N);

  const int numberOfSegments = 4;
  int segmentN = N / numberOfSegments;             
  size_t segmentSize = size / numberOfSegments;

  for(int i = 0; i < numberOfSegments; i++){
    int segmentOffset = i * segmentN;
    cudaStream_t stream;
    cudaStreamCreate(&stream);
    addVectorsInto<<<numberOfBlocks, threadsPerBlock, 0, stream>>>(c[segmentOffset], a[segmentOffset], b[segmentOffset], segmentSize);
    cudaMemcpyAsync(&h_c[segmentOffset], &c[segmentOffset], segmentSize, cudaMemcpyDeviceToHost, stream);
    cudaStreamDestroy(stream);
  }

  asyncErr = cudaDeviceSynchronize();
  if(asyncErr != cudaSuccess) printf("Error: %s\n", cudaGetErrorString(asyncErr));

  checkElementsAre(7, h_c, N);

  /*
   * Destroy streams when they are no longer needed.
   */

  cudaStreamDestroy(stream1);
  cudaStreamDestroy(stream2);
  cudaStreamDestroy(stream3);

  cudaFree(a);
  cudaFree(b);
  cudaFree(c);
  cudaFreeHost(h_c);
}

*** cudaHostAlloc
pinned memory

*** cudaMemAdvise
有效地指导数据在不同处理器之间的迁移，从而最小化因数据不在本地而导致的缺页中断，提升应用程序性能。

#define GPU_DEVICE 0
{
  char * array = nullptr;       
  cudaMallocManaged(&array, N)  //分配内存
  fill_data(array);
  cudaMemAdvise(array, N, cudaMemAdviseSetReadMostly, GPU_DEVICE); //提示GPU端几乎仅用于读取这片数据
  cudaMemPrefetchAsync(array, N, GPU_DEVICE, NULL); // GPU prefetch
  qsort<<<...>>>(array);        //GPU 无缺页中断，产生read-only副本
  //cudaDeviceSynchronize();  
  use_data(array);              //CPU process 没有page-fault.
  cudaFree(array);
}
