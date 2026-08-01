*** FFN实现: SwiGLU

def forward(self, x):
    return self.w2(F.silu(self.w1(x)) * self.w3(x))


*** kv cache实现

输入x，batch size先是seq_len，再是1

self.cache_k = torch.zeros(
    (
        args.max_batch_size,
        args.max_seq_len,
        self.n_local_kv_heads,
        self.head_dim,
    )
).cuda()
self.cache_v = torch.zeros(
    (
        args.max_batch_size,
        args.max_seq_len,
        self.n_local_kv_heads,
        self.head_dim,
    )
).cuda()


def forward(...):
	self.cache_k[:bsz, start_pos : start_pos + seqlen] = xk
    self.cache_v[:bsz, start_pos : start_pos + seqlen] = xv

    keys = self.cache_k[:bsz, : start_pos + seqlen]
    values = self.cache_v[:bsz, : start_pos + seqlen]



*** GQA实现

    # repeat k/v heads if n_kv_heads < n_heads
    keys = repeat_kv(
        keys, self.n_rep
    )  # (bs, cache_len + seqlen, n_local_heads, head_dim)
    values = repeat_kv(
        values, self.n_rep
    )  # (bs, cache_len + seqlen, n_local_heads, head_dim)