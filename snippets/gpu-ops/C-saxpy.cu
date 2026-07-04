#include <stdio.h>
#include <assert.h>

#define N 2048 * 2048 // Number of elements in each vector

/*
 * Aim to profile `saxpy` (without modifying `N`) running under
 * 20us.
 */

__global__ void saxpy(int * a, int * b, int * c)
{
    int tid = blockIdx.x * blockDim.x + threadIdx.x;
    int stride = blockDim.x * gridDim.x;

    for ( int i = tid; i < N; i += stride ){
        c[i] = 2 * a[i] + b[i];
    }
}

inline cudaError_t checkCuda(cudaError_t result)
{
  if (result != cudaSuccess) {
    fprintf(stderr, "CUDA Runtime Error: %s\n", cudaGetErrorString(result));
    assert(result == cudaSuccess);
  }
  return result;
}

int main()
{
    int deviceId;
    int numberOfSMs;

    cudaGetDevice(&deviceId);
    cudaDeviceGetAttribute(&numberOfSMs, cudaDevAttrMultiProcessorCount, deviceId);
    printf("Device ID: %d\tNumber of SMs: %d\n", deviceId, numberOfSMs);
    
    int *a, *b, *c;

    int size = N * sizeof (int); // The total number of bytes per vector

    cudaMallocManaged(&a, size);
    cudaMallocManaged(&b, size);
    cudaMallocManaged(&c, size);
    
    cudaMemPrefetchAsync(a, size, cudaCpuDeviceId);
    cudaMemPrefetchAsync(b, size, cudaCpuDeviceId);
    cudaMemPrefetchAsync(c, size, cudaCpuDeviceId);

    // Initialize memory
    for( int i = 0; i < N; ++i )
    {
        a[i] = 2;
        b[i] = 1;
        c[i] = 0;
    }
    
    
    int threads_per_block = 256;
    int number_of_blocks = 32 * numberOfSMs;
    
    cudaMemPrefetchAsync(a, size, deviceId);
    cudaMemPrefetchAsync(b, size, deviceId);
    cudaMemPrefetchAsync(c, size, deviceId);

    saxpy <<< number_of_blocks, threads_per_block >>> ( a, b, c );
    cudaDeviceSynchronize();
    
    cudaMemPrefetchAsync(c, size, cudaCpuDeviceId);
    // Print out the first and last 5 values of c for a quality check
    for( int i = 0; i < 5; ++i )
        printf("c[%d] = %d, ", i, c[i]);
    printf ("\n");
    for( int i = N-5; i < N; ++i )
        printf("c[%d] = %d, ", i, c[i]);
    printf ("\n");

    cudaFree( a ); cudaFree( b ); cudaFree( c );
}

