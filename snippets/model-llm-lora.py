
- https://lightning.ai/lightning-ai/studios/code-lora-from-scratch?view=public&section=featured

class LoRALayer(torch.nn.Module):
    def __init__(self, in_dim: int, out_dim: int, rank: int, alpha: float, device: str):
        super().__init__()
        std_dev = 1 / torch.sqrt(torch.tensor(rank).float())
        self.A = torch.nn.Parameter(torch.randn(in_dim, rank) * std_dev).to(device)
        self.B = torch.nn.Parameter(torch.zeros(rank, out_dim)).to(device)
        self.alpha = alpha

    def forward(self, x):
        return self.alpha * (x @ self.A @ self.B)