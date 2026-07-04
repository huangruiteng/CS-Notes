import torch, math

# within one block.
N_inp = 64
N_out = 64
d = 128
Q = torch.randn(N_out, d).cuda()
K = torch.randn(N_inp, d).cuda()
V = torch.randn(N_inp, d).cuda()
O = torch.zeros(N_out, d).cuda()
L = torch.zeros(N_out, 1).cuda()

B_c = 16
B_r = 16
T_c = (N_inp + B_c - 1) // B_c
T_r = (N_out + B_r - 1) // B_r

scale_factor = 1 / math.sqrt(Q.size(-1))

# Q and O L split into T_r; K, V in T_c blocks
for i in range(T_r):
    Q_i = Q[i * B_r: (i + 1) * B_r]
    O_i = torch.zeros(B_r, d)
    l_i = torch.zeros(B_r, 1)
    m_i = torch.full((B_r, 1), -math.inf)
    last_m_i = m_i
    for j in range(T_c):
        K_j = K[j * B_c: (j + 1) * B_c]
        V_j = V[j * B_c: (j + 1) * B_c]
        S_i = scale_factor * (Q_i @ K_j.T)
        m_i = torch.maximum(m_i, S_i.max(dim=-1, keepdim=True).values)
        P_i = torch.exp(S_i - m_i)
        l_i = torch.exp(last_m_i - m_i) * l_i + P_i.sum(dim=-1, keepdim=True)
        O_i = torch.exp(last_m_i - m_i) * O_i + P_i @ V_j
        last_m_i = m_i
    O_i = (1.0 / l_i) * O_i
    L_i = m_i + torch.log(l_i)
    O[i * B_r: (i + 1) * B_r] = O_i
    L[i * B_r: (i + 1) * B_r] = L_i


expected = torch.nn.functional.scaled_dot_product_attention(Q[:, :], K[:, :], V[:, :])
print("abs diff", (O - expected).abs().max())
