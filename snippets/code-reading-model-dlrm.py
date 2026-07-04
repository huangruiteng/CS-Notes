- DLRM Blog Post: https://ai.meta.com/blog/dlrm-an-advanced-open-source-deep-learning-recommendation-model/
- DLRM Paper: https://arxiv.org/pdf/1906.00091
- DLRM github repo: https://github.com/facebookresearch/dlrm
- Criteo Dataset: https://ailab.criteo.com/download-criteo-1tb-click-logs-dataset/
	- https://huggingface.co/datasets/criteo/CriteoClickLogs/tree/main


有torchrec实现


***** torchrec

merged_ids, inverse_idx = torch.unique(ids_tensor, return_inverse=True, return_counts=False)
num_row = merged_ids.size(0)
merged_embedding = torch.ops.segment_ops.collect_sum(emb_tensor, inverse_idx, num_row)

***** simple-DLRM
- gpu-mode:lectures/lecture_018 https://github.com/gpu-mode/lectures.git

*** model.py


class MLP(nn.Module):
    def __init__(self, input_size: int, hidden_sizes: List[int], output_size: int):
        super(MLP, self).__init__()
        fc_layers = []
        for i, hidden_size in enumerate(hidden_sizes):
            if i == 0:
                fc_layers.append(nn.Linear(input_size, hidden_size))
            else:
                fc_layers.append(nn.Linear(hidden_sizes[i - 1], hidden_size))
            fc_layers.append(nn.ReLU())
        fc_layers.append(nn.Linear(hidden_sizes[-1], output_size))
        self.fc_layers = nn.Sequential(*fc_layers)

    def forward(self, x: torch.Tensor):
        return self.fc_layers(x)

class SparseFeatureLayer(nn.Module):
    def __init__(self, cardinality: int, embedding_size: int):
        super(SparseFeatureLayer, self).__init__()
        self.embedding = nn.Embedding(cardinality, embedding_size)

    def forward(self, inputs: torch.Tensor) -> torch.Tensor:
        # Input : B X 1 # Output : B X E
        embeddings = self.embedding(inputs)
        return embeddings


class SparseArch(nn.Module):
	...
	def _forward_index_hash(self, inputs: torch.Tensor) -> List[torch.Tensor]:
        output_values = []
        for i in range(self.num_sparse_features):
            indices = self.index_hash(inputs[:, i], self.mapping[i])
            sparse_out = self.sparse_layers[i](indices)
            output_values.append(sparse_out)
        return output_values

    def _forward_modulus_hash(self, inputs: torch.Tensor) -> List[torch.Tensor]:
        sparse_hashed = self.modulus_hash(inputs, self.cardinality_tensor)
        return [sparse_layer(sparse_hashed[:, i]) for i, sparse_layer in enumerate(self.sparse_layers)]


class DenseSparseInteractionLayer(nn.Module):
    SUPPORTED_INTERACTION_TYPES = ["dot", "cat"]

    def __init__(self, interaction_type: str = "dot"):
        super(DenseSparseInteractionLayer, self).__init__()
        if interaction_type not in self.SUPPORTED_INTERACTION_TYPES:
            raise ValueError(f"Interaction type {interaction_type} not supported. "
                             f"Supported types are {self.SUPPORTED_INTERACTION_TYPES}")
        self.interaction_type = interaction_type

    def forward(self, dense_out: torch.Tensor,
                sparse_out: List[torch.Tensor]) -> Tensor:
        concat = torch.cat([dense_out] + sparse_out, dim=-1).unsqueeze(2)
        if self.interaction_type == "dot":
            out = torch.bmm(concat, torch.transpose(concat, 1, 2))
        else:
            out = concat
        flattened = torch.flatten(out, 1)
        return flattened