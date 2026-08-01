// 整个链条是通过 bid 、 flags 和 scan_value 这三个以 bid 为索引的组件动态构建和同步

__shared__ T XY[stream_block_size];
__shared__ unsigned int sbid;
__shared__ T previous_sum;

if (threadIdx.x == 0)
    sbid = atomicAdd(DCounter, 1);
__syncthreads();

const int bid = sbid;

int i = bid * stream_block_size + threadIdx.x;
if (i < InputSize)
    XY[threadIdx.x] = X[i];

BrentKung(XY);

if (threadIdx.x == 0) {
    cuda::atomic_ref<int, cuda::thread_scope_device> aref(flags[bid]);
    while (aref.load(cuda::memory_order_acquire) == 0) {}
    previous_sum = scan_value[bid];
    scan_value[bid + 1] = previous_sum + XY[block_size - 1];
    __threadfence();
    atomicAdd(&flags[bid + 1], 1);
}
__syncthreads();

if (i < InputSize)
    Y[i] = previous_sum + XY[threadIdx.x];


// 基于tiled state打包的实现，不依赖memory ordering

if (threadIdx.x == 0) {
    unsigned long long int prev_state;
    do {
        prev_state = atomicAdd(&tile_states[bid], 0);
    } while (prev_state == 0);
    previous_sum = prev_state & 0xFFFFFFFF;

    unsigned long long int current_state 
        = (1ull << 32) | (previous_sum + XY[block_size - 1]);
    atomicAdd(&tile_states[bid + 1], current_state);
}
__syncthreads();