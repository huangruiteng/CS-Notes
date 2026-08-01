* fourier位置编码

input_dim = (input_axis * ((num_freq_bands * 2) + 1)) + input_channels
- 3(rgb)+26，其中26代表的是2D位置编码，每个轴（height轴和width轴）上分别是13个点

用concat的方式，而不是sum pooling


* latents

self.latents = nn.Parameter(torch.randn(num_latents, latent_dim))

任务导向 ：与无监督的 K-Means 聚类不同，Perceiver 的 latents 的学习过程是 由最终任务的损失函数指导的 。
因此，它们学习到的不是通用的“聚类中心”，而是对完成特定任务（如分类、生成等） 最有用 的信息表示。
它们学习成为能够捕捉输入数据中最关键特征的“专家”或“代表”。

* attention

# context_dim不是None的时候，代表cross-attention
# 为None的时候，代表self-attention。