__global__ void transposeOptimized(float *input, float *output, int m, int n){ 
	int colID_input = threadIdx.x + blockDim.x*blockIdx.x;
	int rowID_input = threadIdx.y + blockDim.y*blockIdx.y;

	__shared__ float sdata[32][33];
	// bank ~ 一次传32 words，32次访问 ~ 32次unit time，所以希望存在shared memory里的数据尽可能多地分布在不同bank上
	// 希望shared memory中每列数据所在的bank尽可能多
	if (rowID_input < m && colID_input < n) {
		int index_input = colID_input + rowID_input*n; 
		sdata[threadIdx.y][threadIdx.x] = input[index_input];

		__syncthreads();

		int dst_col = threadIdx.x + blockIdx.y * blockDim.y;
		int dst_row = threadIdx.y + blockIdx.x * blockDim.x; 
		output[dst_col + dst_row*m] = sdata[threadIdx.x][threadIdx.y];
	}
}