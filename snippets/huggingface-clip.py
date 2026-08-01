
from transformers import CLIPProcessor, CLIPModel

model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32")
processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")

from IPython.display import Image, display
display(Image(filename="data_examples/truck.jpg"))

from PIL import Image
image = Image.open("data_examples/truck.jpg")
cls_list = ["dog", "woman", "man", "car", "truck",
            "a black truck", "bird", "a white truck", "black cat"]
input = processor(text=cls_list, images=image,
                  return_tensors="pt", padding=True)
outputs = model(**input)
print(outputs.keys())



CLIP 模型反馈的结果包含['logits_per_image', 'logits_per_text', 'text_embeds', 'image_embeds', 'text_model_output', 'vision_model_output'] 这六组结果，分别对应：

- `logits_per_image`: 每个图像于 cls_list 中所有文本标签的相似度；[1x9]
- `logits_per_text`: logits_per_image 的矩阵转置 `logits_per_text = logits_per_image.t()`
- `text_embeds`: 每个文本标签对应的特征矩阵
- `image_embeds`: 每个图像对应的特征矩阵
- `text_model_output`: 文本模型（未经过）特征映射的输出
- `vision_model_output`: 图像模型（未经过）特征映射的输出


logits_per_image = outputs.logits_per_image
probs = logits_per_image.softmax(dim=1)

for i in range(len(cls_list)):
    print(f"{cls_list[i]}: {probs[0][i]}")

### CNClip

`B` 代表 Big，`L`代表 Large, `H`代表 Huge;
B L H 后面紧跟的数字代表图像 patch 化时，每个 patch 的分辨率大小，14 代表图像是按照 14x14 的分辨率被划分成相互没有 overlap 的图像块。
-336 表示，输入图像被 resize 到 336x336 分辨率后进行的处理；默认是 224x224 的分辨率。
RN50 表示 ResNet50

%pip install cn_clip

import torch
import cn_clip.clip as clip
from PIL import Image
from cn_clip.clip import load_from_name, available_models
device = "cuda" if torch.cuda.is_available() else "cpu"
print("Available models:", available_models())
# Available models: ['ViT-B-16', 'ViT-L-14', 'ViT-L-14-336', 'ViT-H-14', 'RN50']

model, preprocess = load_from_name(
    "ViT-B-16", device=device, download_root='./')
model.eval()

image = preprocess(Image.open("data_examples/truck.jpg")
                   ).unsqueeze(0).to(device)
cls_list = ["狗", "汽车", "白色皮卡", "火车", "皮卡"]
text = clip.tokenize(cls_list).to(device)

import torch

with torch.no_grad():
    image_features = model.encode_image(image)
    text_features = model.encode_text(text)
    # 对特征进行归一化，请使用归一化后的图文特征用于下游任务
    image_features /= image_features.norm(dim=-1, keepdim=True)
    text_features /= text_features.norm(dim=-1, keepdim=True)

    logits_per_image, logits_per_text = model.get_similarity(image, text)
    probs = logits_per_image.softmax(dim=-1).cpu().numpy()


### SigLip


from IPython.display import Image, display
display(Image(filename="data_examples/truck.jpg"))
for i in range(len(cls_list)):
    print(f"{cls_list[i]}: {probs[0][i]}")
from PIL import Image
import requests
from transformers import AutoProcessor, AutoModel
import torch


image = Image.open("data_examples/truck.jpg")

texts = ["dog", "woman", "man", "car", "truck",
            "a black truck", "a white truck", "cat"]
inputs = processor(text=texts, images=image, padding="max_length", return_tensors="pt")

with torch.no_grad():
    outputs = model(**inputs)

logits_per_image = outputs.logits_per_image
probs = torch.sigmoid(logits_per_image) # these are the probabilities
print(probs)
for i in range(len(texts)):
    print(f"{probs[0][i]:.1%} that image 0 is '{texts[i]}'")

model = AutoModel.from_pretrained("google/siglip-base-patch16-224")
processor = AutoProcessor.from_pretrained("google/siglip-base-patch16-224")
