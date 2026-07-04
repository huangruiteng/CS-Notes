*** dev

install: https://docs.sglang.ai/start/install.html

source $HOME/anaconda3/bin/activate 
# conda create -n sglang
conda activate sglang
conda install pip

*** pip

# Use the last release branch
git clone -b v0.4.5 https://github.com/sgl-project/sglang.git
cd sglang

pip install --upgrade pip
pip install -e "python[all]" --find-links https://flashinfer.ai/whl/cu124/torch2.5/flashinfer-python

*** docker

docker pull lmsysorg/sglang:latest

docker run -itd --gpus all \
  --userns=host \
  --mount type=bind,source=$(pwd),target=$(pwd) \
  --mount type=bind,source=$HOME/.ssh,target=$HOME/.ssh \
  --mount type=bind,source=/tmp,target=/tmp \
  --shm-size 32g \
  -p 30000:30000 \
  -v ~/.cache/huggingface:/root/.cache/huggingface \
  --env "HF_TOKEN=<your_hf_token>" \
  --name sglang_container \
  -d ml-platform-hub-cn-beijing.cr.volces.com/lmsysorg/sglang:latest \
  /bin/bash
# python3 -m sglang.launch_server --model-path meta-llama/llama-3.1-8b-instruct --host 0.0.0.0 --port 30000

*** torchao集成

--torchao-config
--tp-size

BATCH_SIZE=16
# Note: gemlite is only compatible with float16
# while int4wo-64 (tinygemm-4-64 as shown in the graph) and fp8dq-per_row should use bfloat16
DTYPE=float16
# int4wo-64, fp8dq-per_tensor
TORCHAO_CONFIG=gemlite-4-64
TP_SIZE=2
# Decode performance
python3 -m sglang.bench_offline_throughput --model-path meta-llama/Llama-3.1-8B-Instruct --json-model-override-args '{"architectures": ["TorchNativeLlamaForCausalLM"]}' --dataset-name random --random-input 1024 --random-output 512 --random-range 1 --num-prompts $BATCH_SIZE --enable-torch-compile --dtype $DTYPE --torchao-config $TORCHAO_CONFIG --tp-size $TP_SIZE




*** Torch Native Tensor Parallel Support in SGLang

https://github.com/sgl-project/sglang/blob/main/python/sglang/srt/models/torch_native_llama.py

Existing model definitions in SGLang use special linear modules that are coupled with tensor parallelism style, 
for example: MergedColumnParallelLinear, QKVParallelLinear and RowParallelLinear. 
To decouple the model definition and tensor parallelization style, we defined a pytorch native model that 
uses plain nn.Linear module from PyTorch and rely on PyTorch tensor parallelism APIs for parallelization 
and torch.compile for speedup. At related module hierarchies, we add a dictionary describing how a submodule should be parallelized. 
For example, in class LlamaAttention, we define:

_tp_plan = {
    "qkv_proj": "Colwise_Sharded",
    "o_proj": "Rowwise",
}

where "qkv_proj" and "o_proj" are the FQNs of the wqkv and wo projections, and the values are their TP styles.

We then define a TP engine in model_parallel.py. 
It searches for _tp_plan recursively within the model, and applies the indicated TP styles to the submodules 
using PyTorch’s parallelize_module API.
- https://pytorch.org/docs/stable/distributed.tensor.parallel.html#torch.distributed.tensor.parallel.parallelize_module


*** 性能优化

** SGLANG_ENABLE_LOGITS_PROCESSOR_CHUNK

优化logits计算的显存消耗；  配合deterministic推理做测试

https://www.xiaohongshu.com/explore/690af6dc0000000005002cb1?app_platform=ios&app_version=8.86&share_from_user_hidden=true&xsec_source=app_share&type=normal&xsec_token=CBCcIgqWM7cWaaFvFdGrZ5JiCFVrFWVQD0FZi2fxxuskk=&author_share=1&xhsshare=CopyLink&shareRedId=N0lEN0Y6Rk82NzUyOTgwNjc5OTg2NUpP&apptime=1762336862&share_id=293a2f99a3c944da9090dbb4f2ef52df












