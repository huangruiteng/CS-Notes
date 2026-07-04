
https://github.com/pytorch/pytorch/blob/main/c10/macros/Macros.h

C10_LAUNCH_BOUNDS_0
CUDA_MAX_THREADS_PER_SM




常量内存：

__constant__ float constData[10];

__global__ void kernel() {
    int idx = threadIdx.x;
    // 访问常量内存
    float value = constData[idx];
    // 可以在这里进行具体的计算
    std::cout << "Thread " << idx << " read value: " << value << std::endl;
}

int main() {
    float hostData[10] = {1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0};
    // 将数据从主机内存复制到常量内存
    cudaMemcpyToSymbol(constData, hostData, sizeof(hostData));