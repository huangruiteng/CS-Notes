#include <math.h>
#include <stdio.h>
#include <stdlib.h>
#include "timer.h"
#include "check.h"
#include <assert.h>

#define SOFTENING 1e-9f

inline cudaError_t checkCuda(cudaError_t result)
{
  if (result != cudaSuccess) {
    fprintf(stderr, "CUDA Runtime Error: %s\n", cudaGetErrorString(result));
    assert(result == cudaSuccess);
  }
  return result;
}

/*
 * Each body contains x, y, and z coordinate positions,
 * as well as velocities in the x, y, and z directions.
 */

typedef struct { float x, y, z, vx, vy, vz; } Body;

void randomizeBodies(float *data, int n) {
  for (int i = 0; i < n; i++) {
    data[i] = 2.0f * (rand() / (float)RAND_MAX) - 1.0f;
  }
}

/*
 * This function calculates the gravitational impact of all bodies in the system
 * on all others, but does not update their positions.
 */

__global__ 
void bodyForce(Body *p, float dt, int n) {
  int index = threadIdx.x + blockIdx.x * blockDim.x;
  int stride = blockDim.x * gridDim.x;
  for (int i = index; i < n; i += stride) {
    float Fx = 0.0f; float Fy = 0.0f; float Fz = 0.0f;

    for (int j = 0; j < n; j++) {
      float dx = p[j].x - p[i].x;
      float dy = p[j].y - p[i].y;
      float dz = p[j].z - p[i].z;
      float distSqr = dx*dx + dy*dy + dz*dz + SOFTENING;
      float invDist = rsqrtf(distSqr);
      float invDist3 = invDist * invDist * invDist;

      Fx += dx * invDist3; Fy += dy * invDist3; Fz += dz * invDist3;
    }

    p[i].vx += dt*Fx; p[i].vy += dt*Fy; p[i].vz += dt*Fz;
  }
}

__global__
void updatePos(Body *p, float dt, int n){
  int index = threadIdx.x + blockIdx.x * blockDim.x;
  int stride = blockDim.x * gridDim.x;
  for (int i = index; i < n; i += stride) { // integrate position
    p[i].x += p[i].vx*dt;
    p[i].y += p[i].vy*dt;
    p[i].z += p[i].vz*dt;
  }
}

int main(const int argc, const char** argv) {

  /*
   * Do not change the value for `nBodies` here. If you would like to modify it,
   * pass values into the command line.
   */

  int nBodies = 2<<11;
  int salt = 0;
  if (argc > 1) nBodies = 2<<atoi(argv[1]);

  /*
   * This salt is for assessment reasons. Tampering with it will result in automatic failure.
   */

  if (argc > 2) salt = atoi(argv[2]);

  const float dt = 0.01f; // time step
  const int nIters = 10;  // simulation iterations

  int deviceId;
  int numberOfSMs;

  cudaGetDevice(&deviceId);
  cudaDeviceGetAttribute(&numberOfSMs, cudaDevAttrMultiProcessorCount, deviceId);
  printf("Device ID: %d\tNumber of SMs: %d\n", deviceId, numberOfSMs);

  int bytes = nBodies * sizeof(Body);
  float *buf;

  cudaMallocManaged(&buf, bytes);

  Body *p = (Body*)buf;

  /*
   * As a constraint of this exercise, `randomizeBodies` must remain a host function.
   */

  cudaMemPrefetchAsync(buf, bytes, cudaCpuDeviceId);

  randomizeBodies(buf, 6 * nBodies); // Init pos / vel data

  double totalTime = 0.0;

  size_t threadsPerBlock;
  size_t numberOfBlocks;

  threadsPerBlock = 256;
  numberOfBlocks = 32 * numberOfSMs;


  /*******************************************************************/
  // Do not modify these 2 lines of code.
  for (int iter = 0; iter < nIters; iter++) {
    StartTimer();
  /*******************************************************************/

    cudaMemPrefetchAsync(buf, bytes, deviceId);

    bodyForce<<<numberOfBlocks, threadsPerBlock>>>(p, dt, nBodies); // compute interbody forces

    checkCuda(cudaGetLastError());

    checkCuda(cudaDeviceSynchronize());

    updatePos<<<numberOfBlocks, threadsPerBlock>>>(p, dt, nBodies);

    checkCuda(cudaGetLastError());

    checkCuda(cudaDeviceSynchronize());

  /*******************************************************************/
  // Do not modify the code in this section.
    const double tElapsed = GetTimer() / 1000.0;
    totalTime += tElapsed;
  }

  double avgTime = totalTime / (double)(nIters);
  float billionsOfOpsPerSecond = 1e-9 * nBodies * nBodies / avgTime;

#ifdef ASSESS
  checkPerformance(buf, billionsOfOpsPerSecond, salt);
#else
  checkAccuracy(buf, nBodies);
  printf("%d Bodies: average %0.3f Billion Interactions / second\n", nBodies, billionsOfOpsPerSecond);
  salt += 1;
#endif
  /*******************************************************************/

  cudaFree(buf);
}
