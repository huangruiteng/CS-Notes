### sok

# sparse emb
The distributed sparse embedding scatters keys across GPUs by computing gpu_id = key % number_of_gpus

SOK uses collective operation Reduce-Scatter when reduction of embedding vectors intra-slots (feature-fields) happens.
ALL-Gather is used for the accumulation of gradient during backward propagation.

# dense emb
An All2Allcommunication primitive during forward propagation is first used to exchange keys among all GPUs.
Then, another All2All is used to exchange embedding vectors among all GPUs. During backward propagation,
All2All it is used to exchange top gradients among all GPUs.


# snippet


import sparse_operation_kit as sok

emb_layer = sok.distributed_embedding(max_vocabulary_size_per_gpu,
                                      embedding_vec_size,
                                      slot_num, nnz_per_slot)
emb_layer = sok.All2AllDenseEmbedding(max_vocabulary_size_per_gpu,
                                      embedding_vec_size,
                                      slot_num, nnz_per_slot)


@tf.function
def _train_step(inputs, labels):
    emb_vectors = emb_layer(inputs)
    ...

for i, (inputs, labels) in enumerate(dataset):
    _train_step(inputs)