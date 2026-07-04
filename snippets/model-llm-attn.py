### 基本的Attention前向传播实现
def attention_forward(Q, K, V):
    """
    Q: [N x d] 查询矩阵
    K: [N x d] 键矩阵
    V: [N x d] 值矩阵
    """
    # 1. 计算注意力分数
    S = Q @ K.T  # [N x N]
    
    # 2. 计算softmax
    max_scores = torch.max(S, dim=-1, keepdim=True)[0]  # 数值稳定性
    exp_scores = torch.exp(S - max_scores)  # [N x N]
    sum_scores = torch.sum(exp_scores, dim=-1, keepdim=True)  # [N x 1]
    P = exp_scores / sum_scores  # [N x N]
    
    # 3. 计算输出
    O = P @ V  # [N x d]
    
    # 保存中间结果用于反向传播
    cache = (P, Q, K, V)
    return O, cache
    
### 基本的Attention反向传播实现
def attention_backward(dO, cache):
    """
    dO: 输出梯度 [N x d]
    cache: 前向传播缓存的中间结果
    """
    P, Q, K, V = cache
    N, d = Q.shape
    
    # 1. 计算dV
    dV = P.T @ dO  # [N x d]
    
    # 2. 计算dP
    dP = dO @ V.T  # [N x N]
    
    # 3. 计算softmax梯度
    # softmax导数: dS = P * (dP - sum(P * dP))
    sum_dP = torch.sum(P * dP, dim=-1, keepdim=True)  # [N x 1]
    dS = P * (dP - sum_dP)  # [N x N]
    # 4. 计算dQ和dK
    dQ = dS @ K  # [N x d]
    dK = dS.T @ Q  # [N x d]
    return dQ, dK, dV



### Flash-Attn V1

# 外循环：遍历K和V矩阵的块
for j in range(Tc):  # Tc = N/Bc
    # 加载Kj,Vj到片上SRAM
    
    # 内循环：遍历Q矩阵的块
    for i in range(Tr):  # Tr = N/Br
        # 1. 加载Qi到SRAM
        # 2. 计算Si,j = QiKj^T
        # 3. 更新softmax中间结果
        # 4. 计算输出Oi的部分结果
# 关键优化步骤 
# 1. 分块计算避免大矩阵存储
S_ij = Q_i @ K_j.T  # 只在SRAM中计算局部注意力分数

# 2. Softmax的在线计算
m_i = max(m_i, rowmax(S_ij))  # 动态更新最大值
l_i = exp(m_i_old - m_i)*l_i + rowsum(P_ij)  # 累积和

# 3. 输出的递增计算
O_i = diag(l_i_new)^(-1) * (O_i + P_ij @ V_j)


def compute_block_sizes(M, d, N):
    """
    计算最优分块大小
    M: SRAM大小
    d: head维度
    N: 序列长度
    """
    def get_block_sizes():
        # Bc: key/value的块大小
        # Br: query的块大小
        
        # 1. 基本约束
            # 1. Q块(Br × d) - 用于计算当前query行的注意力分数
            # 2. K块(Bc × d) - 用于与Q块计算注意力分数
            # 3. V块(Bc × d) - 用于与注意力分数相乘得到输出
            # 4. O块(Br × d) - 存储中间输出结果
            # 总内存需求 = Q块 + K块 + V块 + O块
            #           = (Br * d) + (Bc * d) + (Bc * d) + (Br * d)
            #           = d * (2Br + 2Bc)
            #           = 2d * (Br + Bc)
            # Br、Bc <= M/(4d)
        # 2. 计算Bc (key block size)
        Bc = min(M // (4 * d), N)  # 不超过序列长度
        
        # 3. 计算Br (query block size)
        Br = min(M // (4 * d), N)  # 不超过序列长度
        
        return Br, Bc

    # 计算块数
    def compute_num_blocks(Br, Bc):
        Tr = (N + Br - 1) // Br  # 向上取整
        Tc = (N + Bc - 1) // Bc  # 向上取整
        return Tr, Tc


def tiled_forward(self, q, k, v, Bc, Br):
    N, d = q.shape
    Tc = (N + Bc - 1) // Bc  # 列块数
    Tr = (N + Br - 1) // Br  # 行块数
    
    O = torch.zeros_like(q)
    l = torch.zeros(N)
    m = torch.full((N,), float('-inf'))

    # 外循环：遍历K,V的块
    for j in range(Tc):
        # 加载K,V块到SRAM
        k_block = k[j*Bc:min((j+1)*Bc, N)]
        v_block = v[j*Bc:min((j+1)*Bc, N)]
        
        # 内循环：遍历Q的块
        for i in range(Tr):
            # 加载Q块到SRAM
            start_idx = i * Br
            end_idx = min((i+1)*Br, N)
            q_block = q[start_idx:end_idx]
            
            # 计算局部注意力分数
            S_ij = self.sm_scale * (q_block @ k_block.T)  # [Br x Bc]
            
            # 更新最大值
            m_block = m[start_idx:end_idx]
            m_new = torch.max(torch.max(S_ij, dim=-1)[0], m_block)
            
            # 计算局部softmax
            P_ij = torch.exp(S_ij - m_new.unsqueeze(1))
            l_block = l[start_idx:end_idx]
            l_new = torch.exp(m_block - m_new) * l_block + torch.sum(P_ij, dim=-1)
            
            # 更新输出
            O_block = O[start_idx:end_idx]
            O[start_idx:end_idx] = (
                torch.exp(m_block - m_new).unsqueeze(1) * O_block +
                P_ij @ v_block
            ) / l_new.unsqueeze(1)
            # 更新中间变量
            m[start_idx:end_idx] = m_new
            l[start_idx:end_idx] = l_new

    return O


def backward(self, dO, q, k, v, O, L, Bc, Br):
    N, d = q.shape
    Tc = (N + Bc - 1) // Bc
    Tr = (N + Br - 1) // Br
    
    dq = torch.zeros_like(q)
    dk = torch.zeros_like(k)
    dv = torch.zeros_like(v)
    
    for j in range(Tc):
        k_block = k[j*Bc:min((j+1)*Bc, N)]
        v_block = v[j*Bc:min((j+1)*Bc, N)]
        
        for i in range(Tr):
            start_idx = i * Br
            end_idx = min((i+1)*Br, N)
            
            q_block = q[start_idx:end_idx]
            O_block = O[start_idx:end_idx]
            L_block = L[start_idx:end_idx]
            dO_block = dO[start_idx:end_idx]
            
            # 计算局部梯度
            S_ij = self.sm_scale * (q_block @ k_block.T)
            P_ij = torch.exp(S_ij - L_block.unsqueeze(1))
            
            # 计算dv
            dv_block = P_ij.T @ dO_block
            dv[j*Bc:min((j+1)*Bc, N)] += dv_block
            
            # 计算dp和ds
            dP_ij = dO_block @ v_block.T
            dS_ij = P_ij * (dP_ij - (torch.sum(P_ij * dP_ij, dim=-1, keepdim=True)))
            
            # 计算dq和dk
            dq_block = self.sm_scale * (dS_ij @ k_block)
            dk_block = self.sm_scale * (dS_ij.T @ q_block)
            
            dq[start_idx:end_idx] += dq_block
            dk[j*Bc:min((j+1)*Bc, N)] += dk_block

    return dq, dk, dv


### Flash-Attn V2

def forward(self, q, k, v, key_padding_mask=None):
    """
    Flash Attention V2前向传播
    
    Args:
        q: 查询矩阵 [batch_size, seq_len_q, num_heads, head_dim]
        k: 键矩阵 [batch_size, seq_len_k, num_heads, head_dim]
        v: 值矩阵 [batch_size, seq_len_k, num_heads, head_dim]
        key_padding_mask: 键的填充掩码
    """
    batch_size, seq_len_q, num_heads, head_dim = q.shape
    seq_len_k = k.shape[1]
    
    # 初始化输出和中间结果
    output = torch.zeros_like(q)
    L = torch.zeros(batch_size, num_heads, seq_len_q, 
                   device=q.device, dtype=q.dtype)
    
    # 计算分块数量
    num_block_q = (seq_len_q + self.block_size_r - 1) // self.block_size_r
    num_block_k = (seq_len_k + self.block_size_c - 1) // self.block_size_c
    
    # 主要计算循环
    for i in range(num_block_q):
        # Q的当前块范围
        q_start = i * self.block_size_r
        q_end = min(q_start + self.block_size_r, seq_len_q)
        
        # 初始化当前Q块的状态
        q_block = q[:, q_start:q_end]
        m_i = torch.full((batch_size, num_heads, q_end-q_start), 
                        float('-inf'), device=q.device)
        l_i = torch.zeros((batch_size, num_heads, q_end-q_start), 
                         device=q.device)
        
        # 遍历K,V块
        for j in range(num_block_k):
            k_start = j * self.block_size_c
            k_end = min(k_start + self.block_size_c, seq_len_k)
            
            # 加载当前K,V块
            k_block = k[:, k_start:k_end]
            v_block = v[:, k_start:k_end]
            
            # 计算注意力分数
            S_ij = torch.matmul(q_block, k_block.transpose(-2, -1))
            if self.softmax_scale is not None:
                S_ij = S_ij * self.softmax_scale
                
            # 应用掩码（如果有）
            if key_padding_mask is not None:
                mask_block = key_padding_mask[:, k_start:k_end]
                S_ij = S_ij.masked_fill(~mask_block.unsqueeze(1).unsqueeze(2), 
                                      float('-inf'))
            
            # 更新最大值和累积和
            M_ij = torch.max(S_ij, dim=-1)[0]
            m_new = torch.max(m_i, M_ij)
            
            # 计算局部softmax
            exp_ij = torch.exp(S_ij - m_new.unsqueeze(-1))
            l_new = torch.exp(m_i - m_new) * l_i + torch.sum(exp_ij, dim=-1)
            
            # 更新输出
            output_block = output[:, q_start:q_end]
            output_block = torch.exp(m_i.unsqueeze(-1) - m_new.unsqueeze(-1)) * output_block
            output_block = output_block + torch.matmul(exp_ij, v_block)
            
            # 更新状态
            m_i = m_new
            l_i = l_new
            output[:, q_start:q_end] = output_block
            
        # 保存最终的logsumexp值
        L[:, :, q_start:q_end] = m_i + torch.log(l_i)
    
    # 最终归一化
    output = output / torch.exp(L).unsqueeze(-1)
    return output


### Flash Attention V3

import torch
import torch.cuda as cuda
from dataclasses import dataclass
from typing import Optional, Tuple
import math

@dataclass
class FlashAttentionV3Config:
    """FA3配置"""
    M: int           # SRAM大小
    d: int           # head维度
    s: int           # 环形缓冲区阶段数
    dtype: torch.dtype = torch.float16
    
class CircularBuffer:
    """环形缓冲区"""
    def __init__(self, stages: int, size: int, dtype=torch.float16):
        self.buffer = torch.empty(
            (stages, size), 
            dtype=dtype, 
            device='cuda'
        )
        self.stages = stages
        self.head = 0
        self.tail = 0
        self.full = False
        
    def put(self, data: torch.Tensor, stage: int):
        """放入数据"""
        self.buffer[stage % self.stages] = data
        
    def get(self, stage: int) -> torch.Tensor:
        """获取数据"""
        return self.buffer[stage % self.stages]
        
 class Producer:
    def __init__(self, config: FlashAttentionV3Config):
        self.config = config
        self.Bc = config.M // (4 * config.d)
        self.Br = config.M // (4 * config.d)
        
        # 初始化环形缓冲区
        self.q_buffer = CircularBuffer(config.s, self.Br * config.d)
        self.k_buffer = CircularBuffer(config.s, self.Bc * config.d)
        self.v_buffer = CircularBuffer(config.s, self.Bc * config.d)
        
    @torch.cuda.amp.autocast()
    def produce(self, q: torch.Tensor, k: torch.Tensor, v: torch.Tensor,
                l: torch.Tensor, m: torch.Tensor):
        """生产者主循环"""
        batch_size, num_heads, seq_len, head_dim = q.shape
        
        for i in range(0, seq_len, self.Br):
            # 计算当前块的范围
            i_end = min(i + self.Br, seq_len)
            stage = i // self.Br
            
            # 1. 加载Q块到片上内存
            q_block = q[:, :, i:i_end].contiguous()
            self.q_buffer.put(q_block, stage)
            
            # 2. 通知消费者（这里用event模拟）
            cuda.Event(enable_timing=False).record()
            
            # 3. 等待消费完成
            cuda.Event(enable_timing=False).wait()
            
            # 4. 加载K,V块
            for j in range(0, seq_len, self.Bc):
                j_end = min(j + self.Bc, seq_len)
                
                k_block = k[:, :, j:j_end].contiguous()
                v_block = v[:, :, j:j_end].contiguous()
                
                self.k_buffer.put(k_block, stage)
                self.v_buffer.put(v_block, stage)
                
                # 加载l和m向量
                l_block = l[:, :, i:i_end].contiguous()
                m_block = m[:, :, i:i_end].contiguous()

class Consumer:
    def __init__(self, config: FlashAttentionV3Config):
        self.config = config
        self.Bc = config.M // (4 * config.d)
        self.Br = config.M // (4 * config.d)
    
    @torch.cuda.amp.autocast()
    def consume(self, producer: Producer) -> Tuple[torch.Tensor, torch.Tensor]:
        """消费者主循环"""
        
        for i in range(0, seq_len, self.Br):
            stage = i // self.Br
            
            # 1. 等待生产者数据就绪
            cuda.Event(enable_timing=False).wait()
            
            # 2. 从缓冲区加载数据
            q = producer.q_buffer.get(stage)
            
            for j in range(0, seq_len, self.Bc):
                k = producer.k_buffer.get(stage)
                v = producer.v_buffer.get(stage)
                
                # 3. 计算attention scores (SS-GEMM)
                S = torch.matmul(q, k.transpose(-2, -1))
                
                # 4. 更新m和l
                m0 = m.clone()
                m = torch.maximum(m0, torch.max(S, dim=-1)[0])
                
                # 5. 计算softmax
                p = torch.exp(S - m.unsqueeze(-1))
                l = torch.exp(m0 - m) * l + torch.sum(p, dim=-1)
                
                # 6. 计算输出 (RS-GEMM)
                o = torch.diag_embed(torch.exp(m0 - m).reciprocal()) @ o + p @ v
                
            # 7. 释放缓冲区
            cuda.Event(enable_timing=False).record()
            
        # 8. 最终归一化
        O = torch.diag_embed(torch.exp(m0 - m).reciprocal()) @ o
        L = m + torch.log(l)
        
        return O, L
class FlashAttentionV3:
    def __init__(self, config: FlashAttentionV3Config):
        self.config = config
        self.producer = Producer(config)
        self.consumer = Consumer(config)
        
    @torch.cuda.amp.autocast()
    def forward(self, q: torch.Tensor, k: torch.Tensor, v: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
        """前向传播"""
        batch_size, num_heads, seq_len, head_dim = q.shape
        
        # 初始化
        l = torch.zeros((batch_size, num_heads, seq_len), device='cuda')
        m = torch.full((batch_size, num_heads, seq_len), float('-inf'), device='cuda')
        
        # 启动生产者-消费者
        self.producer.produce(q, k, v, l, m)
        O, L = self.consumer.consume(self.producer)
        
        return O, L

    @staticmethod
    def setup_memory_layout():
        """设置内存布局优化"""
        # 设置最大寄存器数
        torch.cuda.set_max_memory_allocated()
        
        # 启用TMA
        torch.cuda.set_device_properties(
            torch.cuda.current_device(),
            {'async_engine_count': 2}
        )

class OptimizationUtils:
    @staticmethod
    def transpose_with_registers(matrix: torch.Tensor) -> torch.Tensor:
        """使用寄存器进行矩阵转置"""
        return matrix.transpose(-2, -1).contiguous()
    
    @staticmethod
    def quantize_block(tensor: torch.Tensor, dtype=torch.float8):
        """块级量化"""
        scale = tensor.abs().max()
        return (tensor / scale).to(dtype), scale
    
    @staticmethod
    def generate_random_orthogonal(size: int) -> torch.Tensor:
        """生成随机正交矩阵用于量化误差平滑"""
        M = torch.randn(size, size, device='cuda')
        U, _, V = torch.linalg.svd(M)
        return U @ V

def example_usage():
    # 配置
    config = FlashAttentionV3Config(
        M=49152,  # 48KB
        d=64,     # head维度
        s=64      # 环形缓冲区阶段数
    )
    
    # 创建模型
    fa3 = FlashAttentionV3(config)
    
    # 准备输入
    batch_size, num_heads = 32, 8
    seq_len, head_dim = 1024, 64
    
    q = torch.randn(batch_size, num_heads, seq_len, head_dim, device='cuda')
    k = torch.randn(batch_size, num_heads, seq_len, head_dim, device='cuda')
    v = torch.randn(batch_size, num_heads, seq_len, head_dim, device='cuda')
    
    # 前向传播
    O, L = fa3.forward(q, k, v)



### 为什么Q和K/V的seq len可能不相等

m_size 和 n_size 分别代表了Query矩阵（Q）和Key/Value矩阵（K、V）在序列维度上的长度

通常情况下二者的关系：在多数常规的自注意力计算场景中，m_size 和 n_size 是相等的。这是因为自注意力机制往往是针对同一输入序列，Q、K、V 均基于该序列生成，所以它们在序列维度上的长度一致。例如在Transformer的编码器部分，对输入的句子进行编码时，Q 会去查询同一个句子里其他位置的信息，此时 m_size = n_size。

在某些特定场景下，m_size 和 n_size 可能不相等，下面列举两个典型场景：
- 解码器的自注意力：在Transformer的解码器中，进行自注意力计算时要考虑因果关系，也就是当前时刻只能关注到之前时刻的信息。在推理阶段（decode阶段），解码器通常是逐个生成输出，每次生成一个新的词。此时 Q 矩阵仅包含当前要生成词的信息，所以 m_size = 1，而 K 和 V 矩阵则包含了之前已经生成的所有词的信息，n_size 等于之前生成词的数量，一般会大于1。
- 交叉注意力：在一些模型结构中会使用交叉注意力机制，比如Transformer的解码器在处理编码器输出时。此时 Q 来自解码器的输入序列，K 和 V 来自编码器的输出序列，两个序列的长度可能不同，从而导致 m_size 和 n_size 不相等。
