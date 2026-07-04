import torch
import torch.nn as nn
import numpy as np
from sklearn.cluster import KMeans

def kmeans_cluster(
    samples: torch.Tensor,
    num_clusters: int,
    num_iters: int = 10,
) -> torch.Tensor:
    """
    使用 scikit-learn 的 KMeans 对 PyTorch 张量进行聚类。
    """
    B, dim, dtype, device = samples.shape[0], samples.shape[-1], samples.dtype, samples.device
    x_cpu = samples.cpu().detach().numpy()
    cluster_algo = KMeans(n_clusters=num_clusters, max_iter=num_iters, n_init='auto').fit(x_cpu)     # init 的 默认值是 'k-means++'
    centers = cluster_algo.cluster_centers_
    tensor_centers = torch.from_numpy(centers).to(device)
    return tensor_centers

class VectorQuantizerWithKMeansInit(nn.Module):
    """
    一个使用KMeans初始化码本的向量量化器示例。
    """
    def __init__(self, num_embeddings: int, embedding_dim: int, kmeans_iters: int = 10):
        super().__init__()
        self.n_e = num_embeddings
        self.e_dim = embedding_dim
        self.kmeans_iters = kmeans_iters
        self.embedding = nn.Embedding(self.n_e, self.e_dim)
        self.initted = False
        self.embedding.weight.data.zero_()

    def _init_codebook(self, data: torch.Tensor):
        if self.initted or not self.training:
            return
        print("Initializing codebook with K-Means...")
        centers = kmeans_cluster(data, self.n_e, self.kmeans_iters)
        self.embedding.weight.data.copy_(centers)
        self.initted = True
        print("Codebook initialized.")

    def forward(self, x: torch.Tensor):
        latent = x.view(-1, self.e_dim)
        self._init_codebook(latent)
        d = torch.sum(latent**2, dim=1, keepdim=True) + \
            torch.sum(self.embedding.weight**2, dim=1, keepdim=True).t() - \
            2 * torch.matmul(latent, self.embedding.weight.t())
        indices = torch.argmin(d, dim=-1)
        x_q = self.embedding(indices).view(x.shape)
        return x_q, indices

if __name__ == '__main__':
    embedding_dim = 64
    num_embeddings = 512
    batch_size = 128
    input_data = torch.randn(batch_size, embedding_dim)
    vq = VectorQuantizerWithKMeansInit(num_embeddings, embedding_dim)
    vq.train()
    quantized_output, _ = vq(input_data)
    print(f"Input shape: {input_data.shape}")
    print(f"Quantized output shape: {quantized_output.shape}")
    assert vq.initted
    assert not torch.all(vq.embedding.weight.data == 0)
        print("\nSuccessfully initialized codebook with K-Means and performed quantization.")