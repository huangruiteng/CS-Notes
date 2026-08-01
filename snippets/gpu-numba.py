pip3 install numba-cuda

https://numba.readthedocs.io/en/stable/cuda/simulator.html
NUMBA_ENABLE_CUDASIM=1

原理：通过 tensor.__cuda_array_interface__

import math
from numba import cuda
from numba.cuda import as_cuda_array as ca
@cuda.jit
def matmul_k_numba(m, n, out, tw):
    cbi,cbd,tid = cuda.blockIdx,cuda.blockDim,cuda.threadIdx
    tc,tr = tid.x,tid.y
    r,c = cbi.y * cbd.y + tr, cbi.x * cbd.x + tc
    h,k  = m.shape
    k2,w = n.shape

    shar = cuda.shared.array(0, dtype=np.float32)
    ms,ns = shar[:tw*tw],shar[tw*tw:2*tw*tw]

    p = np.float32(0.0)
    for ph in range(math.ceil(k/tw)):
        idx = ph*tw
        ms[tr*tw+tc] = m[r, tc+idx] if r<h and idx+tc<k else 0.
        ns[tr*tw+tc] = n[tr+idx, c] if c<w and idx+tr<k else 0.
        cuda.syncthreads()
        for i in range(tw): p += ms[tr*tw+i] * ns[i*tw+tc]
        cuda.syncthreads()
    if r < h and c < w: out[r, c] = p

def matmul_2d_numba(m, n, tw=16):
    h,k  = m.shape
    k2,w = n.shape
    assert k==k2, "Size mismatch!"
    out = torch.zeros(h, w, dtype=m.dtype, device=m.device)
    dyn_shared_mem_size = 2 * tw * tw * 4
    tpb = tw,tw
    blocks = cdiv(w,tpb[0]), cdiv(h,tpb[1])
    matmul_k_numba[blocks, tpb, 0, dyn_shared_mem_size](ca(m), ca(n), ca(out), tw)
    return out