https://github.com/harvardnlp/annotated-transformer.git

class MultiHeadedAttention(nn.Module):
    def __init__(self, h, d_model, dropout=0.1):
        "Take in model size and number of heads."
        super(MultiHeadedAttention, self).__init__()
        assert d_model % h == 0
        # We assume d_v always equals d_k
        self.d_k = d_model // h
        self.h = h
        self.linears = clones(nn.Linear(d_model, d_model), 4)
        self.attn = None
        self.dropout = nn.Dropout(p=dropout)

    def forward(self, query, key, value, mask=None):
        "Implements Figure 2"
        if mask is not None:
            # Same mask applied to all h heads.
            mask = mask.unsqueeze(1)
        nbatches = query.size(0)

        # 1) Do all the linear projections in batch from d_model => h x d_k
        query, key, value = [
            lin(x).view(nbatches, -1, self.h, self.d_k).transpose(1, 2)
            for lin, x in zip(self.linears, (query, key, value))
        ]

        # 2) Apply attention on all the projected vectors in batch.
        x, self.attn = attention(
            query, key, value, mask=mask, dropout=self.dropout
        )

        # 3) "Concat" using a view and apply a final linear.
        x = (
            x.transpose(1, 2)
            .contiguous()
            .view(nbatches, -1, self.h * self.d_k)
        )
        del query
        del key
        del value
        return self.linears[-1](x)

# 工程技巧

.transpose(1, 2)：交换第 1 维和第 2 维，将形状变为 (nbatches, h, seq_len, d_k)，这样可以方便后续对每个头进行并行计算。【每个头的数据在内存上放一起】

# Embeddings

class Embeddings(nn.Module):
    def __init__(self, d_model, vocab):
        super(Embeddings, self).__init__()
        self.lut = nn.Embedding(vocab, d_model)
        self.d_model = d_model

    def forward(self, x):
        return self.lut(x) * math.sqrt(self.d_model)

# positional encoding

class PositionalEncoding(nn.Module):
    "Implement the PE function."

    def __init__(self, d_model, dropout, max_len=5000):
        super(PositionalEncoding, self).__init__()
        self.dropout = nn.Dropout(p=dropout)

        # Compute the positional encodings once in log space.
        pe = torch.zeros(max_len, d_model)
        position = torch.arange(0, max_len).unsqueeze(1)
        div_term = torch.exp(
            torch.arange(0, d_model, 2) * -(math.log(10000.0) / d_model)
        )
        pe[:, 0::2] = torch.sin(position * div_term)
        pe[:, 1::2] = torch.cos(position * div_term)
        pe = pe.unsqueeze(0)
        self.register_buffer("pe", pe)       # 不会被视为模型的参数（即不会在反向传播中更新），但会作为模块的一部分保存和加载

    def forward(self, x):
        x = x + self.pe[:, : x.size(1)].requires_grad_(False) #  requires_grad_(False)
        return self.dropout(x)



# Initialize parameters with Glorot / fan_avg.
for p in model.parameters():
    if p.dim() > 1:
        nn.init.xavier_uniform_(p)


# Batch操作，引入填充标记

class Batch:
    """Object for holding a batch of data with mask during training."""

    def __init__(self, src, tgt=None, pad=2):  # 2 = <blank>
        self.src = src
        self.src_mask = (src != pad).unsqueeze(-2)
        if tgt is not None:
            self.tgt = tgt[:, :-1]
            self.tgt_y = tgt[:, 1:]
            self.tgt_mask = self.make_std_mask(self.tgt, pad)
            self.ntokens = (self.tgt_y != pad).data.sum()

    @staticmethod
    def make_std_mask(tgt, pad):
        "Create a mask to hide padding and future words."
        tgt_mask = (tgt != pad).unsqueeze(-2)
        tgt_mask = tgt_mask & subsequent_mask(tgt.size(-1)).type_as(     # tgt_mask 的形状为 (batch_size, seq_len, seq_len)
            tgt_mask.data
        )
        return tgt_mask

# training loop

optimizer.zero_grad(set_to_none=True)

当设置 set_to_none=True 时，optimizer.zero_grad() 会将所有参数的梯度张量设置为 None，而不是填充为零。
这种方式可以节省内存，因为将梯度设置为 None 后，之前存储梯度的内存可以被释放。

Sentence pairs were batched together by approximate sequence length.
Each training batch contained a set of sentence pairs containing approximately 25000 source tokens and 25000 target tokens.

8 NVIDIA P100 GPUs
base model: a total of 100,000 steps or 12 hours
large model: 300,000 steps (3.5 days)

used the Adam optimizer [(cite)](https://arxiv.org/abs/1412.6980)
# with $\beta_1=0.9$, $\beta_2=0.98$ and $\epsilon=10^{-9}$

$$ 学习率先升后降
# lrate = d_{\text{model}}^{-0.5} \cdot
#   \min({step\_num}^{-0.5},
#     {step\_num} \cdot {warmup\_steps}^{-1.5})
$$
warmup_steps=4000

def rate(step, model_size, factor, warmup):
    """
    we have to default the step to 1 for LambdaLR function
    to avoid zero raising to negative power.
    """
    if step == 0:
        step = 1
    return factor * (
        model_size ** (-0.5) * min(step ** (-0.5), step * warmup ** (-1.5))
    )



# label smoothing

class LabelSmoothing(nn.Module):
    "Implement label smoothing."

    def __init__(self, size, padding_idx, smoothing=0.0):
        super(LabelSmoothing, self).__init__()
        self.criterion = nn.KLDivLoss(reduction="sum")
        self.padding_idx = padding_idx
        self.confidence = 1.0 - smoothing
        self.smoothing = smoothing
        self.size = size
        self.true_dist = None

    def forward(self, x, target):
        assert x.size(1) == self.size
        true_dist = x.data.clone()
        true_dist.fill_(self.smoothing / (self.size - 2))     # 初始化真实分布，减去 2 是因为要排除真实标签和填充标记对应的类别。
        true_dist.scatter_(1, target.data.unsqueeze(1), self.confidence)
        true_dist[:, self.padding_idx] = 0
        mask = torch.nonzero(target.data == self.padding_idx)
        if mask.dim() > 0:
            true_dist.index_fill_(0, mask.squeeze(), 0.0)
        self.true_dist = true_dist
        return self.criterion(x, true_dist.clone().detach())


# 简单的copy-task

data_gen 函数用于生成源 - 目标复制任务的数据，即目标序列是源序列的复制。
将起始标记设置为相同的值（这里是 1），可以让模型更容易学习到复制的模式。模型在处理输入序列时，能够通过起始标记快速识别出序列的开始位置，然后专注于复制后续的元素，从而更好地完成复制任务。


# real world example

load the dataset using torchtext and spacy for tokenization.

构建词表：
vocab_src = build_vocab_from_iterator(
        yield_tokens(train + val + test, tokenize_de, index=0),
        min_freq=2,
        specials=["<s>", "</s>", "<blank>", "<unk>"],
    )


def collate_batch(

bs_id = torch.tensor([0], device=device)  # <s> token id
eos_id = torch.tensor([1], device=device)  # </s> token id



# Distributed训练

from torch.utils.data.distributed import DistributedSampler
import torch.distributed as dist
import torch.multiprocessing as mp
from torch.nn.parallel import DistributedDataParallel as DDP


DistributedSampler

if is_distributed:
  dist.init_process_group(
      "nccl", init_method="env://", rank=gpu, world_size=ngpus_per_node
  )
  model = DDP(model, device_ids=[gpu])
  module = model.module
  is_main_process = gpu == 0

for epoch in ...
	train_dataloader.sampler.set_epoch(epoch)
	...
	torch.cuda.empty_cache()


def train_distributed_model(vocab_src, vocab_tgt, spacy_de, spacy_en, config):
    from the_annotated_transformer import train_worker

    ngpus = torch.cuda.device_count()
    os.environ["MASTER_ADDR"] = "localhost"
    os.environ["MASTER_PORT"] = "12356"
    print(f"Number of GPUs detected: {ngpus}")
    print("Spawning training processes ...")
    mp.spawn(
        train_worker,
        nprocs=ngpus,
        args=(ngpus, vocab_src, vocab_tgt, spacy_de, spacy_en, config, True),
    )

def train_model(vocab_src, vocab_tgt, spacy_de, spacy_en, config):
    if config["distributed"]:
        train_distributed_model(
            vocab_src, vocab_tgt, spacy_de, spacy_en, config
        )
    else:
        train_worker(
            0, 1, vocab_src, vocab_tgt, spacy_de, spacy_en, config, False
        )


# Additional Components: 

1.BPE/ Word-piece
https://github.com/rsennrich/subword-nmt
减少未登录词（OOV）的问题

2.Shared Embeddings
https://arxiv.org/abs/1608.05859

3.Beam Search
https://github.com/OpenNMT/OpenNMT-py/

4.Model Averaging
average_models.py








