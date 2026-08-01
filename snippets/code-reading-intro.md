
### MLSys


#### PyTorch 二次开发

- PyTorch
- https://github.com/pytorch/pytorch

- TorchRec
  - https://pytorch.org/torchrec/overview.html

- vLLM
  - https://github.com/vllm-project/vllm.git

- SGLang
  - https://github.com/sgl-project/sglang.git

- Thunder
  - https://github.com/Lightning-AI/lightning-thunder



#### Tf 二次开发

- HugeCTR

#### 训练框架、最佳实践

- llm.cccl
  - https://github.com/gevtushenko/llm.c

- nvidia例子库
  - https://github.com/NVIDIA/DeepLearningExamples/tree/master


#### Data Pipeline

- ConcurrentDataLoader
  - https://github.com/iarai/concurrent-dataloader/tree/master


#### 通信、序列并行

- nccl
  - https://github.com/NVIDIA/nccl
  - nccl-test https://github.com/NVIDIA/nccl-tests
- AllReduce
  - https://github.com/baidu-research/baidu-allreduce
- RingFlashAttention
  - https://github.com/zhuzilin/ring-flash-attention
- RingAttention
  - https://github.com/gpu-mode/ring-attention


#### 推理

- TensorRT
  - https://github.com/NVIDIA/TensorRT
- TensorRT-LLM
  - https://github.com/NVIDIA/TensorRT-LLM
- Nvidia Triton Inference
  - https://github.com/triton-inference-server/server
  - .../core
  - .../backend
  - .../python_backend
  - .../pytorch_backend     for LibTorch
  - PyTriton: https://github.com/triton-inference-server/pytriton
  - Model Analyzer: https://github.com/triton-inference-server/model_analyzer/tree/main/docs

#### 量化

- TorchAO
  - https://github.com/pytorch/ao/tree/main
  - Current best way to access all the pytorch native gpu quantization work, Used by sdxl-fast and segment-anything-fast
- GPT-Fast
  - https://github.com/pytorch-labs/gpt-fast
  - (has GPTQ support for int4)
  - Best for weight only quant
- Segment-Anything-Fast
  - https://github.com/pytorch-labs/segment-anything-fast
  - Best for dynamic quant
- AutoAWQ
  - https://github.com/casper-hansen/AutoAWQ


### Model & Algo

#### LLM

- llama3
  - https://github.com/meta-llama/llama3

- nanoGPT
  - https://github.com/karpathy/nanoGPT

- DeepSeek-V3
  - https://github.com/deepseek-ai/DeepSeek-V3

- transformers
  - https://github.com/huggingface/transformers

#### LM

- the Annotated Transformer
  - https://github.com/harvardnlp/annotated-transformer
- Perceiver
  - https://github.com/lucidrains/perceiver-pytorch
- OpenNMT
  - https://github.com/OpenNMT/OpenNMT-py.git


#### RL

- ZeroSearch
  - https://github.com/Alibaba-nlp/ZeroSearch

#### DLRM

- simple-DLRM
  - gpu-mode:lectures/lecture_018 https://github.com/gpu-mode/lectures.git

- facebook-DLRM
  - https://github.com/facebookresearch/dlrm

#### 生成式推荐

- MIMIGenRec
  - https://github.com/cocoshe/MIMIGenRec
  - 灵活的生成式推荐训练框架，集成 LlamaFactory 和 TRL
- MiniOneRec
  - https://github.com/AkaliKong/MiniOneRec
  - 端到端生成式推荐框架开源复现

#### GR、RQ-VAE

- GRID
  - https://github.com/snap-research/GRID

- rq-vae-quantization
  - https://github.com/kakaobrain/rq-vae-transformer
  - quantizations.py

- TIGER (unofficial)
  - https://github.com/EdoardoBotta/RQ-VAE-Recommender


### Applied Algo

#### Search Engine

- Typesense
  - https://github.com/typesense/typesense
  - Open Source alternative to Algolia and an Easier-to-Use alternative to ElasticSearch
  - Written in C++

#### Deep Research

- https://github.com/bytedance/deer-flow
- https://github.com/langchain-ai/open_deep_research
- https://github.com/nickscamara/open-deep-research
- https://github.com/LearningCircuit/local-deep-research

#### Context Engineering

- MineContext

#### Agent / RAG

- Qwen Agent
  - https://github.com/QwenLM/Qwen-Agent

- UltraRAG
  - https://github.com/OpenBMB/UltraRAG
  - DeepResearch、Search-o1的开源实现，yaml形式支持多种agent pipeline

- LightRAG

- XAgent
  - https://github.com/OpenBMB/XAgent
  - 自主智能体框架
  - ToolServer：工具执行环境
  - Planning、Execution 双循环的设计
  - 统一基于function calling的实现

- MLE-bench
  - https://github.com/openai/mle-bench
  - OpenAI 基于 75 个 Kaggle 竞赛构建的 ML Agent 评测 benchmark


### GPU

#### environment

- nvidia-container-toolkit
  - https://github.com/NVIDIA/nvidia-container-toolkit

#### 基础库

- cccl
  - https://github.com/NVIDIA/cccl
- cuCollections
  - 比如各类set、map等
  - https://github.com/NVIDIA/cuCollections



### GPU Op

#### Intro

- GPU-Mode
  - https://github.com/gpu-mode/lectures.git


#### Triton

- GemLite
  - https://github.com/mobiusml/gemlite

- MicroBenchmark
  - https://gist.github.com/HDCharles/287ac5e997c7a8cf031004aad0e3a941

- TritonIndex
  - https://github.com/gpu-mode/triton-index

- FlagGems
  - https://github.com/FlagOpen/FlagGems

- FlagAttention
 - https://github.com/FlagOpen/FlagAttention

- SparseAttention
 - https://github.com/epfml/dynamic-sparse-flash-attention 

- SAM flash attention
 - https://github.com/facebookresearch/segment-anything/blob/main/segment_anything/modeling/image_encoder.py#L358
 - https://github.com/pytorch-labs/segment-anything-fast/blob/main/segment_anything_fast/flash_4.py#L13


#### CUTLASS

- CUTLASS
  - https://github.com/NVIDIA/cutlass


#### Attention Kernel

- Pod-Attention
  - https://github.com/microsoft/vattention/blob/main/pod_attn/tests/fabench.py

#### kernel fusion

- cv fusion
  - https://github.com/morousg/cvGPUSpeedup
  - https://github.com/morousg/FusedKernelLibrary


#### Assembler

- Assembler for NVIDIA Maxwell architecture
  - https://github.com/NervanaSystems/maxas.git
  - SGEMM Impl


### C++

#### basic

- Mandelbrot Set
  - https://github.com/sol-prog/Mandelbrot_Set

#### 通信相关

- Protobuf
  - https://github.com/protocolbuffers/protobuf

#### 并行编程

- DPDK QSBR Cuckoo Hash Table
  - https://github.com/DPDK/dpdk/blob/main/lib/hash/rte_cuckoo_hash.c
  - 基于 RCU 的布谷鸟哈希表，代码结构清晰易懂，非常适合并发编程进阶

- Maple Tree
  - https://github.com/torvalds/linux/blob/master/lib/maple_tree.c
  - Linux Kernel MM 新秀，接过了 rbtree 的接力棒，tree node 更加地 cache efficient，采用 RCU 保证 reader lockless，writer lock 是 tree level coarse-grained 而不是 node level fine-grained。与普通 BTree 不同的是支持非重叠区间的增删改查（non-overlapping interval index），最神秘的地方是区间的覆盖写（overwrite multiple entries），此过程中删除多个 leaf nodes 和 internal nodes 同时维持 Btree invariant，核心函数是 mas_spanning_rebalance。阅读过程中可以结合 mailing list。
