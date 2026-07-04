
### 阶段一：图文特征对齐预训练

基本数据格式：

```JSON
{
    "id": "任意一个非重复id，例如 0888888",
    "image": ",
    "conversations": [
      {
        "from": "human",
        "value": "请简要描述这幅图像.\n<image>"
      },
      {
        "from": "gpt",
        "value": "这张图片中显示了一名男子骑自行车和一列正在行驶的火车。前台的男子穿着深色上衣和裤子，看起来有亚洲面孔，他正骑着一辆深色自行车，从左向右穿过画面，并且与镜头形成了接近正面的视角。他的表情专注，似乎正在前往某个目的地。

在他的后方，可以看到一列红色和白色相间的高速火车，火车车身上有几个窗户，火车上方有电网。火车左边的树木使得场景给人一种自然的氛围。在图片的左上角部分，还有一个路牌，上面有日文和英文的混合文本，但具体内容不清晰。整个场景是在室外拍摄的，光线来自自然光，可能是在傍晚或清晨，因为阳光有点斜射到场景中。

整体上，这张照片创造了一种行驶中的火车与骑自行车的人共同构成的动态场面，可能在日本的城市郊外或者乡村地区拍摄。。"
      }
    ]
},
```

下载[LLaVA 预训练数据集](https://huggingface.co/datasets/liuhaotian/LLaVA-Pretrain)

### 开始训练

- 8x A100 (80GB) 耗时 5.5h
- 基于 DeepSpeed ZeRO2
- 输入图像分辨率 336 px
- 训练参数：特征映射层结构（2 层全连接层)

训练脚本 [`pretrain.sh`](https://github.com/haotian-liu/LLaVA/blob/main/scripts/v1_5/pretrain.h)


#!/bin/bash

deepspeed llava/train/train_mem.py \
    --deepspeed ./scripts/zero2.json \
    --model_name_or_path lmsys/vicuna-13b-v1.5 \
    --version plain \   #一阶段
    --data_path ./playground/data/LLaVA-Pretrain/blip_laion_cc_sbu_558k.json \
    --image_folder ./playground/data/LLaVA-Pretrain/images \
    --vision_tower openai/clip-vit-large-patch14-336 \
    --mm_projector_type mlp2x_gelu \
    --tune_mm_mlp_adapter True \
    --mm_vision_select_layer -2 \  #倒数第二层
    --mm_use_im_start_end False \
    --mm_use_im_patch_token False \
    --bf16 True \
    --output_dir ./checkpoints/llava-v1.5-13b-pretrain \
    --num_train_epochs 1 \
    --per_device_train_batch_size 32 \
    --per_device_eval_batch_size 4 \
    --gradient_accumulation_steps 1 \    # 单卡训练，改成8
    --evaluation_strategy "no" \
    --save_strategy "steps" \
    --save_steps 24000 \
    --save_total_limit 1 \
    --learning_rate 1e-3 \
    --weight_decay 0. \
    --warmup_ratio 0.03 \
    --lr_scheduler_type "cosine" \
    --logging_steps 1 \
    --tf32 True \
    --model_max_length 2048 \
    --gradient_checkpointing True \
    --dataloader_num_workers 4 \
    --lazy_preprocess True \
    --report_to wandb



### 阶段二：图-文指令微调训练

基本数据格式：

```JSON
  {
    "id": "任意一个非重复id，例如 0999999",
    "image": "图像文件路径，例如：my_data/hongyadong.jpg ",
    "conversations": [
      {
        "from": "human",
        "value": "<im图中的男子正在做什么？拍摄于哪里?"
      },
      {
        "from": "gpt",
        "value": "图中的男子正在骑自行车，他的视线专注，看起来他正在前往某个目的地。市洪崖洞景区的照片."
      },
      {
        "from": "human",
        "value": "图中有什么可以识别的文字内容?"
      },
      {
        "from": "gpt",
        "value”: “图片右下角墙体上写着\”洪崖洞\“三个字."
      }]
  },

```

下载 LLaVA 训练所需文本数据集: [llava_v1_5_mix665k.json](https://huggingface.co/datasets/liuhaotian/LLaVA-Instruct-150K/blob/main/llava_v1_5_mix665k.json)

下载 LLaVA 训练所需图像数据集:

- COCO: [train2017](http://images.cocodataset.org/zips/train2017.zip)
- GQA: [images](https://downloads.cs.stanford.edu/nlp/data/gqa/images.zip)
- OCR-VQA: [download script](https://drive.google.com/drive/folders/1_GYPY5UkUy7HIcR0zq3ZCFgeZN7BAfm_?usp=sharing), **we save all files as `.jpg`**
- TextVQA: [train_val_images](https://dl.fbaipublicfiles.com/textvqa/images/train_val_images.zip)
- VisualGenome: [part1](https://cs.stanford.edu/people/rak248/VG_100K_2/images.zip), [part2](https://cs.stanford.edu/people/rak248/VG_100K_2/images2.zip)

### 开始训.练

- 8x A100 (80GB) 耗 20h
- 基于 DeepSpeed ZeR3
- 输入图像分辨率 336 px
- 训练参数：特征映射层结构（2 层全连接层以及 LLM

训练脚本: [`finetune.sh`](https://github.com/haotian-liu/LLaVA/blob/main/scripts/v1_5/finetune.sh)
LoRA 训练脚本: [`finetune_lora.sh`](https://github.com/haotian-liu/LLaVA/blob/main/scripts/v1_5/finetune_lora.sh)

#!/bin/bash

deepspeed llava/train/train_mem.py \
    --deepspeed ./scripts/zero3.json \
    --model_name_or_path lmsys/vicuna-13b-v1.5 \
    --version v1 \
    --data_path ./playground/data/llava_v1_5_mix665k.json \
    --image_folder ./playground/data \
    --vision_tower openai/clip-vit-large-patch14-336 \
    --pretrain_mm_mlp_adapter ./checkpoints/llava-v1.5-13b-pretrain/mm_projector.bin \
    --mm_projector_type mlp2x_gelu \
    --mm_vision_select_layer -2 \
    --mm_use_im_start_end False \
    --mm_use_im_patch_token False \
    --image_aspect_ratio pad \
    --group_by_modality_length True \
    --bf16 True \
    --output_dir ./checkpoints/llava-v1.5-13b \
    --num_train_epochs 1 \
    --per_device_train_batch_size 16 \
    --per_device_eval_batch_size 4 \
    --gradient_accumulation_steps 1 \
    --evaluation_strategy "no" \
    --save_strategy "steps" \
    --save_steps 50000 \
    --save_total_limit 1 \
    --learning_rate 2e-5 \
    --weight_decay 0. \
    --warmup_ratio 0.03 \
    --lr_scheduler_type "cosine" \
    --logging_steps 1 \
    --tf32 True \
    --model_max_length 2048 \
    --gradient_checkpointing True \
    --dataloader_num_workers 4 \
    --lazy_preprocess True \
    --report_to wandb
