https://github.com/OpenNMT/OpenNMT-py.git

# Additional Components: 

1.BPE/ Word-piece
https://github.com/rsennrich/subword-nmt
减少未登录词（OOV）的问题

onmt/transforms
- tokenize.py
class BPETransform(TokenizerTransform):
- transform.py
class TransformPipe(Transform):
<-
inference_engine.py:class InferenceEngineCT2(InferenceEngine):self.transform.apply_reverse(tokens)

2.Shared Embeddings
https://arxiv.org/abs/1608.05859

share_embeddings参数
onmt/model_builder.py

3.Beam Search
https://github.com/OpenNMT/OpenNMT-py/

4.Model Averaging
