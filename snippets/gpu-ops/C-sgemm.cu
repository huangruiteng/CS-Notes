block_dim: <M / b, N / b>
thread_dim: <t, t>
thread function

// Each thread block computes a b x b area
// 双buffer的思路：sA的第一维是2，感觉是利用GPU流水线的能力，提前去fetch下一次循环的数据

__global__ void SGEMM(float *A, float *B, float *C, int b, int s) {
	__shared__ float sA[2][b][s], sB[2][s][b]; // shared by a thread block
	float rC[bt][bt] = {0}; // thread local buffer, in the registers
	Cooperative fetch first strip from A, B to sA[0], sB[0]
	__sync_threads();
	for (k = 0; k < K / s; k += 1) {
		Cooperative fetch next strip from A, B to sA[(k + 1) % 2], sB[(k + 1) % 2] // 和矩阵计算parallelly运行
		__sync_threads();
		for (kk = 0; kk < s; kk += 1) {
			for (j = 0; j < bt; j += 1) { // unroll loop
				for (i = 0; i < bt; i += 1) { // unroll loop
					rC[j][i] += sA[k % 2][threadIdx.x * bt + j][kk] * sB[k % 2][kk][threadIdx.y * bt + i];
				}
			}
		}
	}
	Write rC back to C
}