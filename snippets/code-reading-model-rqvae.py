
*** GRID

* 子序列增强

collate_with_sid_causal_duplicate


*** RQ-VAE demo

import torch
import torch.nn as nn
import torch.nn.functional as F


class VectorQuantizer(nn.Module):

  def __init__(self, num_embeddings, embedding_dim):
    super().__init__()
    self.embedding_dim = embedding_dim
    self.num_embeddings = num_embeddings
    self.embedding = nn.Embedding(num_embeddings, embedding_dim)
    self.embedding.weight.data.uniform_(-1 / self.num_embeddings,
                                        1 / self.num_embeddings)

  def forward(self, z):
    # Flatten input
    flat_z = z.view(-1, self.embedding_dim)  # [B*H*W, D]
    distances = (flat_z**2).sum(
        1, keepdim=True) - 2 * flat_z @ self.embedding.weight.t() + (
            self.embedding.weight**2).sum(1)
    encoding_indices = distances.argmin(1)
    quantized = self.embedding(encoding_indices).view(z.shape)
    return quantized, encoding_indices


class Encoder(nn.Module):

  def __init__(self, in_dim, hidden_dim, z_dim):
    super().__init__()
    self.net = nn.Sequential(
        nn.Conv2d(in_dim, hidden_dim, 4, 2, 1),
        nn.ReLU(),
        nn.Conv2d(hidden_dim, z_dim, 3, 1, 1),
        nn.ReLU(),
    )

  def forward(self, x):
    return self.net(x)


class Decoder(nn.Module):

  def __init__(self, z_dim, hidden_dim, out_dim):
    super().__init__()
    self.net = nn.Sequential(nn.ConvTranspose2d(z_dim, hidden_dim, 4, 2, 1),
                             nn.ReLU(), nn.Conv2d(hidden_dim, out_dim, 3, 1, 1))

  def forward(self, z):
    return self.net(z)


class RQVAE(nn.Module):

  def __init__(self,
               img_channels=1,
               hid=32,
               z_dim=16,
               num_embeds=64,
               n_levels=2):
    super().__init__()
    self.encoder = Encoder(img_channels, hid, z_dim)
    self.decoder = Decoder(z_dim, hid, img_channels)
    self.vq_layers = nn.ModuleList(
        [VectorQuantizer(num_embeds, z_dim) for _ in range(n_levels)])
    self.n_levels = n_levels

  def forward(self, x):
    z = self.encoder(x)
    residual = z
    quantizeds = []
    for vq in self.vq_layers:
      q, _ = vq(residual)
      quantizeds.append(q)
      residual = residual - q
    quantized_sum = sum(quantizeds)
    x_recon = self.decoder(quantized_sum)
    return x_recon, quantizeds


# 用法示例
if __name__ == '__main__':
  model = RQVAE()
  x = torch.randn(2, 1, 28, 28)  # batch=2, MNIST
  x_recon, quantizeds = model(x)
  print("Reconstructed shape:", x_recon.shape)    # torch.Size([2, 1, 28, 28])
  print("Quantized levels:", [q.shape for q in quantizeds])   # [torch.Size([2, 16, 14, 14]), torch.Size([2, 16, 14, 14])]
