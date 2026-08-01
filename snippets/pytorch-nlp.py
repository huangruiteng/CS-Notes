
### torch.nn.Embedding

torch.nn.Embedding(num_embeddings, embedding_dim, padding_idx=None, max_norm=None, norm_type=2.0, scale_grad_by_freq=False, sparse=False, _weight=None, device=None, dtype=None)

num_embeddings: 构建语料库字典的大小
embedding_dim: 每个词向要编码成向量的长度
padding_idx: 输出遇到此下标时用0填充(非必要参数)
max_norm：对词嵌入进行归一化，使他们的范数小于max_norm(非必要参数)
norm_type: max_norm在计算范数时的范数类型，如：可以选择1范数，2范数
scale_grad_by_freq：将通过小批量中单词频率的倒数来缩放梯度。这里的词频是指输入的句子。
sparse：如果为True，则与权重矩阵相关的梯度转变为稀疏张量。这里的稀疏张量是指方向传播的时候只更新当前使用此的权重矩阵，加快更新速度。这里和word2vec的负采样有相似之处

import torch
import torch.nn as nn

torch.manual_seed(1)

word_to_ix = {"hello": 0, "world": 1}
embeds = nn.Embedding(2, 5)  # 2 words in vocab, 5 dimensional embeddings
lookup_tensor = torch.tensor([word_to_ix["hello"]], dtype=torch.long)
hello_embed = embeds(lookup_tensor)

print(embeds.weight)
print(hello_embed)

# tensor([[ 0.6614,  0.2669,  0.0617,  0.6213, -0.4519]],
#        grad_fn=<EmbeddingBackward0>)

input = torch.LongTensor([1, 2])

result = embeds(input)

embeds = nn.Embedding(5, 3, padding_idx=0)

# 应用：情感分类任务