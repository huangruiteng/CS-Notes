*** Intro

https://docs.nvidia.com/deeplearning/nccl/user-guide/docs/api/colls.html

ncclAllReduce(const void* sendbuff, void* recvbuff, size_t count, ncclDataType_t datatype, ncclRedOp_t op, ncclComm_t comm, cudaStream_t stream)

Reduces data arrays of length count in sendbuff using the op operation and leaves identical copies of the result in each recvbuff.

In-place operation will happen if sendbuff == recvbuff.

* 可以用nccltest做profile

* 概念：communication objects，指代一组GPU



** 两种编程模型

● 1 GPU per CPU process
○ Root process generates uniqueId
○ Broadcast id to all processes (e.g. use MPI)
○ All processes initialize communicator with same id, unique rank
○ Each process then launches AllReduce Kernel

———— 这是pytorch选择的方式

int myRank, nRanks;
MPI_Comm_rank(MPI_COMM_WORLD, &myRank);
MPI_Comm_size(MPI_COMM_WORLD, &nRanks);

ncclUniqueId id;
if (myRank == 0) ncclGetUniqueId(&id);
MPI_Bcast(&id, sizeof(id), MPI_BYTE, 0, MPI_COMM_WORLD);

ncclComm_t comm;
ncclCommInitRank(&comm, nRanks, id, myRank);


● Multiple GPUs on 1 CPU process
○ Generate uniqueId (no need to broadcast)
○ Loop through initializing each rank
○ Wrapper that does both for you (ncclCommInitAll)
○ Process launches all AllReduce Kernels

ncclResult_t ncclCommInitAll(ncclComm_t* comm, int ndev, const int* devlist) {
    ncclUniqueId Id;
    ncclGetUniqueId(&Id);
    ncclGroupStart();
    for (int i = 0; i < ndev; i++) {
        cudaSetDevice(devlist[i]);
        ncclCommInitRank(comm + i, ndev, Id, i);
    }
    ncclGroupEnd();
    return ncclSuccess;
}


*** DDP + nccl

性能调优：
- https://docs.pytorch.org/docs/stable/distributed.html#common-environment-variables
- https://github.com/NVIDIA/nccl/issues/318

NCCL_SOCKET_NTHREADS and NCCL_NSOCKS_PERTHREAD


*** Example

https://docs.nvidia.com/deeplearning/nccl/user-guide/docs/examples.html

#include <stdlib.h>
#include <stdio.h>
#include "cuda_runtime.h"
#include "nccl.h"

#define CUDACHECK(cmd) do {                         \
  cudaError_t err = cmd;                            \
  if (err != cudaSuccess) {                         \
    printf("Failed: Cuda error %s:%d '%s'\n",       \
        __FILE__,__LINE__,cudaGetErrorString(err)); \
    exit(EXIT_FAILURE);                             \
  }                                                 \
} while(0)


#define NCCLCHECK(cmd) do {                         \
  ncclResult_t res = cmd;                           \
  if (res != ncclSuccess) {                         \
    printf("Failed, NCCL error %s:%d '%s'\n",       \
        __FILE__,__LINE__,ncclGetErrorString(res)); \
    exit(EXIT_FAILURE);                             \
  }                                                 \
} while(0)


int main(int argc, char* argv[])
{
  ncclComm_t comms[4];


  //managing 4 devices
  int nDev = 4;
  int size = 32*1024*1024;
  int devs[4] = { 0, 1, 2, 3 };


  //allocating and initializing device buffers
  float** sendbuff = (float**)malloc(nDev * sizeof(float*));
  float** recvbuff = (float**)malloc(nDev * sizeof(float*));
  cudaStream_t* s = (cudaStream_t*)malloc(sizeof(cudaStream_t)*nDev);


  for (int i = 0; i < nDev; ++i) {
    CUDACHECK(cudaSetDevice(i));
    CUDACHECK(cudaMalloc((void**)sendbuff + i, size * sizeof(float)));
    CUDACHECK(cudaMalloc((void**)recvbuff + i, size * sizeof(float)));
    CUDACHECK(cudaMemset(sendbuff[i], 1, size * sizeof(float)));
    CUDACHECK(cudaMemset(recvbuff[i], 0, size * sizeof(float)));
    CUDACHECK(cudaStreamCreate(s+i));
  }


  //initializing NCCL
  NCCLCHECK(ncclCommInitAll(comms, nDev, devs));


   //calling NCCL communication API. Group API is required when using
   //multiple devices per thread
  NCCLCHECK(ncclGroupStart());
  for (int i = 0; i < nDev; ++i)
    NCCLCHECK(ncclAllReduce((const void*)sendbuff[i], (void*)recvbuff[i], size, ncclFloat, ncclSum,
        comms[i], s[i]));
  NCCLCHECK(ncclGroupEnd());


  //synchronizing on CUDA streams to wait for completion of NCCL operation
  for (int i = 0; i < nDev; ++i) {
    CUDACHECK(cudaSetDevice(i));
    CUDACHECK(cudaStreamSynchronize(s[i]));
  }


  //free device buffers
  for (int i = 0; i < nDev; ++i) {
    CUDACHECK(cudaSetDevice(i));
    CUDACHECK(cudaFree(sendbuff[i]));
    CUDACHECK(cudaFree(recvbuff[i]));
  }


  //finalizing NCCL
  for(int i = 0; i < nDev; ++i)
      ncclCommDestroy(comms[i]);


  printf("Success \n");
  return 0;
}

# 1 GPU Per CPU process
* 只调用一次原语
* calculating localRank which is used in selecting a GPU

uint64_t hostHashs[nRanks];
char hostname[1024];
getHostName(hostname, 1024);
hostHashs[myRank] = getHostHash(hostname);
MPICHECK(MPI_Allgather(MPI_IN_PLACE, 0, MPI_DATATYPE_NULL, hostHashs, sizeof(uint64_t), MPI_BYTE, MPI_COMM_WORLD));
for (int p=0; p<nRanks; p++) {
 if (p == myRank) break;
 if (hostHashs[p] == hostHashs[myRank]) localRank++;
}



*** all reduce

* 图解参考 Resources/nccl.pdf

src/device/all_reduce.h

  template<typename T, typename RedOp, typename Proto>
  __device__ __forceinline__ void runRing(int tid, int nthreads, struct ncclDevWorkColl* work) {
    ncclRing *ring = &ncclShmem.channel.ring;
    int ringIx = ring->index;
    const int nranks = ncclShmem.comm.nRanks;
    ssize_t gridOffset;
    ssize_t channelCount;
    ssize_t chunkCount;
    ncclCollCbdPart(work, ncclShmem.channelId, Proto::Id, sizeof(T), (ssize_t*)nullptr, &gridOffset, &channelCount, &chunkCount);
    const ssize_t loopCount = nranks * chunkCount;
    ssize_t offset;
    int nelem;
    int chunk;

    // Coverity reports that the callee treats &ring->next as an array.  However, due to the use of
    // FanSymmetric<1>, only the first element is ever accessed, so it's fine.
    // coverity[callee_ptr_arith:FALSE]
    Primitives<T, RedOp, FanSymmetric<1>, 1, Proto, 0> prims
      (tid, nthreads, &ring->prev, &ring->next, work->sendbuff, work->recvbuff, work->redOpArg, 0, 0, 0, work);

    for (ssize_t elemOffset = 0; elemOffset < channelCount; elemOffset += loopCount) {
      ssize_t remCount = channelCount - elemOffset;
      ssize_t chunkOffset;

      if (remCount < loopCount) chunkCount = alignUp(divUp(remCount, nranks), 16/sizeof(T));

      auto modRanks = [&]__device__(int r)->int {
        return r - (r >= nranks ? nranks : 0);
      };

      // step 0: push data to next GPU
      chunk = modRanks(ringIx + nranks - 1);
      chunkOffset = chunk * chunkCount;
      offset = gridOffset + elemOffset + chunkOffset;
      nelem = (int)min(chunkCount, remCount - chunkOffset);
      prims.directSend(offset, offset, nelem);

      // k-2 steps: reduce and copy to next GPU
      for (int j = 2; j < nranks; ++j) {
        chunk = modRanks(ringIx + nranks - j);
        chunkOffset = chunk * chunkCount;
        offset = gridOffset + elemOffset + chunkOffset;
        nelem = (int)min(chunkCount, remCount - chunkOffset);
        prims.directRecvReduceDirectSend(offset, offset, nelem);
      }

      // step k-1: reduce this buffer and data, which will produce the final
      // result that we store in this data and push to the next GPU
      chunk = ringIx + 0;
      chunkOffset = chunk * chunkCount;
      offset = gridOffset + elemOffset + chunkOffset;
      nelem = (int)min(chunkCount, remCount - chunkOffset);
      prims.directRecvReduceCopyDirectSend(offset, offset, nelem, /*postOp=*/true);

      // k-2 steps: copy to next GPU
      for (int j = 1; j < nranks - 1; ++j) {
        chunk = modRanks(ringIx + nranks - j);
        chunkOffset = chunk * chunkCount;
        offset = gridOffset + elemOffset + chunkOffset;
        nelem = (int)min(chunkCount, remCount - chunkOffset);
        prims.directRecvCopyDirectSend(offset, offset, nelem);
      }

      // Make final copy from buffer to dest.
      chunk = modRanks(ringIx + 1);
      chunkOffset = chunk * chunkCount;
      offset = gridOffset + elemOffset + chunkOffset;
      nelem = (int)min(chunkCount, remCount - chunkOffset);

      prims.directRecv(offset, nelem);
    }
  }

*** Collective Operations Prims
● Prims functions like prims.send, prims.recvReduceSend, etc. are how data is
sent between GPUs during collective operations
● Implemented in three different “protocols” with different synchronization
	○ Simple
	○ LL (low latency, 8 byte stores are atomic, 4 bytes of data and 4 bytes of flag)
	○ LL128 (low latency, 128 byte stores are atomic, 120 bytes of data and 8 bytes of flag)
● AllReduce has 3 algorithms and 3 protocols for a total of 9 ways it can run



