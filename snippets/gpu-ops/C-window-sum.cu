#include <cstdio>
#include <cuda_runtime.h>

#define RADIUS                3
#define THREADS_PER_BLOCK     512


__global__ void windowSumNaiveKernel(const float* A, float* B, int n) {
  int out_index = blockDim.x * blockIdx.x + threadIdx.x;
  int in_index = out_index + RADIUS;
  if (out_index < n) {
    float sum = 0.;
// https://stackoverflow.com/questions/22278631/what-does-pragma-unroll-do-exactly-does-it-affect-the-number-of-threads
// 对于 SIZE 固定的循环，cuda用 #pragma unroll 有利于 Instruction-Level Parallelism (ILP)、减少判断
#pragma unroll
    for (int i = -RADIUS; i <= RADIUS; ++i) {
      sum += A[in_index + i];
    }
    B[out_index] = sum;
  }
}

__global__ void windowSumKernel(const float* A, float* B, int n) {
  __shared__ float temp[THREADS_PER_BLOCK + 2 * RADIUS];
  int out_index = blockDim.x * blockIdx.x + threadIdx.x;
  int in_index = out_index + RADIUS;
  int local_index = threadIdx.x + RADIUS;
  if (out_index < n) {
    // compute the number of elements of every blocks
    int num = min(THREADS_PER_BLOCK, n - blockIdx.x * blockDim.x);
    temp[local_index] = A[in_index];
    if (threadIdx.x < RADIUS) {
      temp[local_index - RADIUS] = A[in_index - RADIUS];
      // use correct offset
      temp[local_index + num] = A[in_index +  num];
    }
    __syncthreads();
    float sum = 0.;
#pragma unroll
    for (int i = -RADIUS; i <= RADIUS; ++i) {
      sum += temp[local_index + i];
    }
    B[out_index] = sum;
  }
}

void windowSumNaive(const float* A, float* B, int n) {
	float *d_A, *d_B;
	int size = n * sizeof(float);
	cudaMalloc((void **) &d_A, (n + 2 * RADIUS) * sizeof(float));
	cudaMemset(d_A, 0, (n + 2 * RADIUS) * sizeof(float));
	cudaMemcpy(d_A + RADIUS, A, size, cudaMemcpyHostToDevice);
	cudaMalloc((void **) &d_B, size);
	dim3 threads(THREADS_PER_BLOCK, 1, 1);
	dim3 blocks((n + THREADS_PER_BLOCK - 1) / THREADS_PER_BLOCK, 1, 1);
	windowSumNaiveKernel<<<blocks, threads>>>(d_A, d_B, n);
	cudaMemcpy(B, d_B, size, cudaMemcpyDeviceToHost);
	cudaFree(d_A);
	cudaFree(d_B);
}

void windowSum(const float* A, float* B, int n) {
	float *d_A, *d_B;
	int size = n * sizeof(float);
	cudaMalloc((void **) &d_A, (n + 2 * RADIUS) * sizeof(float));
	cudaMemset(d_A, 0, (n + 2 * RADIUS) * sizeof(float));
	cudaMemcpy(d_A + RADIUS, A, size, cudaMemcpyHostToDevice);
	cudaMalloc((void **) &d_B, size);
	dim3 threads(THREADS_PER_BLOCK, 1, 1);
	dim3 blocks((n + THREADS_PER_BLOCK - 1) / THREADS_PER_BLOCK, 1, 1);
	windowSumKernel<<<blocks, threads>>>(d_A, d_B, n);
	cudaMemcpy(B, d_B, size, cudaMemcpyDeviceToHost);
	cudaFree(d_A);
	cudaFree(d_B);
}

int main() {
  int n = 1024 * 1024;
  float* A = new float[n];
  float* B = new float[n];
  for (int i = 0; i < n; ++i) {
    A[i] = i;
  }
  windowSumNaive(A, B, n);
  windowSum(A, B, n);
  delete [] A;
  delete [] B;
  return 0;
}