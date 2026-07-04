- [RAM](https://github.com/xinyu1205/recognize-anything) (Recognize Anything): 用于给定一张图片，识别出图片中包含的所有物体类别
- [Grounding DINO](https://github.com/IDEA-Research/GroundingDINO): 用于对于给定的物体标签，框出其所在图像中的位置坐标

- RAM： [https://huggingface.co/spaces/xinyu1205/recognize-anything/blob/main/ram_swin_large_14m.pth](https://huggingface.co/spaces/xinyu1205/recognize-anything/blob/main/ram_swin_large_14m.pth)
- RAM++： [https://huggingface.co/xinyu1205/recognize-anything-plus-model/blob/main/ram_plus_swin_large_14m.pth](https://huggingface.co/xinyu1205/recognize-anything-plus-model/blob/main/ram_plus_swin_large_14m.pth)
- GroundingDINO：[https://github.com/IDEA-Research/GroundingDINO/releases/download/v0.1.0-alpha/groundingdino_swint_ogc.pth](https://github.com/IDEA-Research/GroundingDINO/releases/download/v0.1.0-alpha/groundingdino_swint_ogc.pth)

!pip install --user git+https://github.com/xinyu1205/recognize-anything.git
!git clone https://github.com/IDEA-Research/GroundingDINO.git
!pip install -e ./GroundingDINO
!pip uninstall opencv-python-headless -y
!pip install  opencv-python-headless


### 任务一： 抽取出图像中包含的所有物体

使用 RAM 完成上述任务。与 CLIP 不同，RAM 默认提供了可识别的物体类别列表，
详见：[https://github.com/xinyu1205/recognize-anything/blob/main/ram/data/ram_tag_list.txt](https://github.com/xinyu1205/recognize-anything/blob/main/ram/data/ram_tag_list.txt) （共计**4,585**类标签的识别）

import argparse
import numpy as np
import random
import os
import torch

from PIL import Image
from ram.models import ram_plus, ram
from ram import inference_ram as inference
from ram import get_transform

device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
print(device)

image_size = 384  # 一般来说，图像分辨率越大，可识别的图像内容精细程度越高。但是随之可能带来的风险是提升识别错误的概率。
transform = get_transform(image_size=image_size)
# model = ram(pretrained="models/ram_swin_large_14m.pth",
#                             image_size=image_size,
#                             vit='swin_l')
model = ram_plus(pretrained="models/ram_plus_swin_large_14m.pth",
                 image_size=image_size,
                 vit='swin_l')
model.eval()
model = model.to(device)

from IPython.display import display
from PIL import Image
image_path = "data_examples/test.jpg"
image_pil = Image.open(image_path)
image = transform(image_pil).unsqueeze(0).to(device)
recog_res = inference(image, model)


display(image_pil)
print("Image Tags: ", recog_res[0])
print("图像标签: ", recog_res[1])


### 任务二：根据抽取出来的物体列表，获取其在图像中的位置信息


!pip uninstall groundingdino -y
!pip install -e ./GroundingDINO

from groundingdino.util.inference import load_model, load_image, predict, annotate, Model
import cv2

CONFIG_PATH = "GroundingDINO/groundingdino/config/GroundingDINO_SwinT_OGC.py"
CHECKPOINT_PATH = "models/groundingdino_swint_ogc.pth"
model = load_model(CONFIG_PATH, CHECKPOINT_PATH)

image_path = "data_examples/test.jpg"
image_source, image = load_image(image_path)
# "bicycle. man. passenger train. railroad. ride. rural. track. train. train track"
TEXT_PROMPT = recog_res[0].replace(" | ", ". ")
BOX_TRESHOLD = 0.25
TEXT_TRESHOLD = 0.25
boxes, logits, phrases = predict(
    model=model,
    image=image,
    caption=TEXT_PROMPT,
    box_threshold=BOX_TRESHOLD,
    text_threshold=TEXT_TRESHOLD,
    device=device,
)
annotated_frame = annotate(image_source=image_source,
                           boxes=boxes, logits=logits, phrases=phrases)
annotated_frame = cv2.cvtColor(annotated_frame, cv2.COLOR_BGR2RGB)
annotated_frame = Image.fromarray(annotated_frame)
print(TEXT_PROMPT)
print(boxes, logits, phrases)

from PIL import Image
from IPython.display import display

display(annotated_frame)

def convertDINO2GPT(boxes, phrases):
    return ", ".join(f"{phrases[i]}: {boxes[i].numpy()}" for i in range(len(phrases)))


bbox_query = convertDINO2GPT(boxes, phrases)
print(bbox_query)


### 生成llava训练数据

from openai import OpenAI
import io
import base64
import os

# Function to encode the image to base64


def encode_image_to_base64(image):
    buffered = io.BytesIO()
    image.save(buffered, format="JPEG")
    return base64.b64encode(buffered.getvalue()).decode('utf-8')

# Function to query GPT-4 Vision


def query_gpt4_vision(messages, api_key=os.getenv('OPENAI_API_KEY')):
    client = OpenAI(api_key=api_key)

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=messages,
        max_tokens=4096,
    )
    return response.choices[0].message.content

# Function to query GPT-4 Vision


def query_gpt4_text(messages, api_key=os.getenv('OPENAI_API_KEY')):
    client = OpenAI(api_key=api_key)

    response = client.chat.completions.create(
        model="gpt-4",
        messages=messages,
        max_tokens=2048,
    )
    return response.choices[0].message.content

### 数据类型一：图像caption

from IPython.display import display
from PIL import Image
system_message_description = f"""你是一个功能强大的中文图像描述器。请创建详细的描述，阐述给定图片的内容。包括物体的类型和颜色、计算物体的数量、物体的动作、物体的精确位置、图片中的文字、核对物体之间的相对位置等。不要描述虚构的内容，只描述从图片中可以确定的内容。在描述内容时，不要以清单形式逐项列出。尽可能最小化审美描述。"""

image_path = "data_examples/test.jpg"
image = Image.open(image_path)
base64_image = encode_image_to_base64(image)
messages = [{"role": "system", "content": system_message_description}, {"role": "user", "content": [
    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}]}]
gpt4v_description = query_gpt4_vision(messages)

display(image)

print(gpt4v_description)


### 数据类型二：生成**对话类数据**

system_message_conversation = f"""你是一个AI视觉助手，你正在观看一张图片。你看到的可能是描述一副图片的若干句子，它们描述了你正在看的同一张图片。回答所有问题时，你要像正在观看图片一样回答。设计一段你和询问这张照片的人之间的对话。回答应该以视觉AI助手正在观看图片并回答问题的语气来进行。提出各种问题并给出相应的答案。包括询问图片中的视觉内容，包括物体类型、计算物体数量、物体动作、物体位置、物体之间的相对位置等。只包括有明确答案的问题：
(1) 可以在图片中看到问题所询问的内容，并能给出自信地回答；
(2) 可以明确在图像中看不到的内容。不要提出任何无法自信回答的问题。

还要包括与图片内容相关的复杂问题，例如询问图片中物体的背景知识，讨论图片中正在发生的事件等。同样，不要询问不确定的细节。在回答复杂问题时提供详细答案。例如，给出详细的例子或推理步骤，使内容更有说服力和组织性。如果必要，可以包括多个段落。"""

fewshot_samples = [{
    "context": "这是一家电影院，放映时间显示在门上方。一个红色的消防栓深埋在雪中。消防栓位于一条最近刚刚清扫过的人行道旁的雪地里。这个城市经历了一个雪量非常大的严冬。在冬天的雪中有一家狗狗的酒店。",
    "response": f"""问题：
图片中的消防栓是什么颜色？
===
答案：
图片中的消防栓是红色的。
===
问题：
消防栓是否被雪完全覆盖还是部分可见？
===
答案：
消防栓部分可见，其大部分被深雪覆盖。
===
问题：
消防栓附近的人行道状况如何？
===
答案：
消防栓附近的人行道最近刚刚清扫过，与周围地区相比，相对没有那么多雪。
===
问题：
这张图片对这个城市的冬季有何暗示？
===
答案：
这张图片暗示这个城市的冬季非常严酷和具有挑战性。图片中可见的大量积雪表明这个城市经历了大量降雪，这可能会给居民生活带来各种困难和中断。
例如，消防栓被深雪覆盖可能会妨碍紧急情况下的可及性，这就引发了安全问题。最近清扫过的人行道表明城市维护人员一直在积极工作，以保持人行道的清洁和安全，但大量降雪可能使持续的除雪工作变得困难。
此外，这种极端的冬季条件可能影响交通，导致交通问题、公共交通延误以及由于道路湿滑而增加的事故风险。这也可能给商业和学校带来问题，因为人们上班或上课的通勤可能会面临挑战。此外，大量积雪还可能对基础设施造成额外压力，如屋顶和电线，增加了结构损坏或停电的可能性。
总之，深埋在雪中的红色消防栓和最近刚刚清扫过的人行道的图片表明这个城市经历了一个特别严酷的冬季，大量降雪可能已经给居民和基础设施带来了各种挑战和中断。"""
},
    {"context": "一名男子正在开阔的雪地山丘上滑雪。一名滑雪者正滑入雪地。滑雪者位于一座巨大山脉的山麓。一名滑雪者站在小径标志旁边，望着山脉。一名独自滑雪者滑过一片灌木丛生的区域。",
     "response": f"""问题：
这个滑雪者在做什么？
===
答案：
这个滑雪者正在雪覆盖的山丘上滑雪，他穿越雪地，享受着美丽的山景。他们还站在一块指示他们在山上位置的小路标识牌旁边。
===
问题：
图片中有其他人或滑雪者可见吗？
===
答案：
不，图片中只有一个人在滑雪，他们被许多灌木丛所包围。
===
问题：
这个人在做什么类型的滑雪？越野滑雪还是高山滑雪？
===
答案：
根据我在照片中看到的，无法明确确定这个滑雪者是在做越野滑雪还是高山滑雪。但是，考虑到存在小路标识牌，以及他们在山丘上滑雪的事实，更有可能是这个滑雪者在进行越野滑雪。高山滑雪通常发生在更陡峭的斜坡上，并涉及使用滑雪缆车，而越野滑雪通常发生在相对平坦的地形上，并有标记的小路。
===
问题：
你能更详细地解释一下越野滑雪和高山滑雪吗？
===
答案：
越野滑雪和高山滑雪是两种不同类型的滑雪，每种都有自己的技术、装备和地形偏好。
1. 越野滑雪：
也称为北欧滑雪，越野滑雪是利用滑雪板和滑雪杖在相对平坦的地形或缓坡上滑行。它是一项受欢迎的娱乐和竞技运动，注重耐力、平衡和有氧健身。越野滑雪者依靠自身运动在雪覆盖的地形上移动，而不是依靠滑雪缆车或其他辅助方式。
越野滑雪有两种主要技术：
- 古典式：这种技术涉及在平行的轨道上滑行，使用前后滑动的动作，保持滑雪板互相平行。滑雪者使用滑雪杖推动自己向前滑行。
- 滑行式滑雪：这种技术类似于溜冰，滑雪者在一个滑雪板上以角度用力踢出并在另一侧滑行。它需要平滑的小路表面，通常比古典式技术更快。
越野滑雪装备包括轻便滑雪板、靴子、绑脚器和滑雪杖。鞋子比高山滑雪的鞋子更灵活，使踝关节更容易移动和控制。
2. 高山滑雪：
也称为滑降滑雪，高山滑雪是利用滑雪板和滑雪杖以高速下滑斜坡来平衡和控制。这项运动更注重速度、技术和在富有挑战性的地形上滑降，包括陡坡、障碍和甚至跳跃。
高山滑雪可以进一步分为几个项目，例如回转滑雪、大回转、超级大回转、速降滑雪等。每个项目都有一套自己的规则、赛道和滑雪设备。
高山滑雪装备包括比越野滑雪使用的滑雪板、靴子、绑脚器和滑雪杖更重、更硬。鞋子更硬以在高速下降和急转弯时提供更好的支撑和控制。
总的来说，越野滑雪是一项基于耐力的运动，涉及在平坦或缓坡地形上旅行，而高山滑雪则集中在速度和技术上，滑雪者在陡坡和富有挑战性的地形上滑降。两种运动都需要专业的装备和技术，但它们给参与者带来不同的体验和挑战。"""}]

messages = [{"role": "system", "content": system_message_conversation}]
for sample in fewshot_samples:
    messages.append({"role": "user", "content": sample['context']})
    messages.append({"role": "assistant", "content": sample['response']})
messages.append({"role": "user", "content": '\n'.join(gpt4v_description)})

from IPython.display import display
from PIL import Image
gpt4t_conversation = query_gpt4_text(messages)

display(image)

print(gpt4t_conversation)



### 数据类型三：生成**复杂推理类问题**

这里需要结束图像解析过程最终得到的物体在图像上的坐标信息[`bbox_query`]，来辅助构建一些复杂推理类问题。

import json
system_message_reasoning = f"""你是一个可以分析单张图片的AI视觉助手。你收到了若干句子，每个句子都描述了你正在观察的同一幅图片。此外，还给出了图片内特定物体的位置，以及详细的坐标。这些坐标以边界框的形式表示，用四个浮点数（x1, y1, x2, y2）范围从0到1表示。这些值对应于左上角的x、左上角的y、右下角的x和右下角的y。

任务是利用提供的标题和边界框信息，创建一个关于图片的合理问题，并详细提供答案。

创建超出描述场景的复杂问题。要回答这样的问题，首先需要理解视觉内容，然后根据背景知识或推理，解释为什么会发生这种情况，或者针对用户的请求提供指导和帮助。通过在问题中不包含视觉内容细节来使问题具有挑战性，这样用户需要首先对此进行推理。

在描述场景时，不要直接提及边界框坐标，而是利用这些数据用自然语言解释场景。包括物体的数量、物体的位置、物体之间的相对位置等细节。

在使用标题和坐标的信息时，直接解释场景，不要提及信息来源是标题或边界框。始终回答得好像你是直接在看这幅图片。

要求‘问题’和‘答案’交替输出，中间用单独一行‘===’隔开
"""

fewshot_samples = [{
    "context": f"""一个戴着多根领带的男人做鬼脸。
一个穿着白衬衫戴着很多领带的男人。
一个戴着领带的男人摆姿势照相。
一个脖子上戴着多根领带的男人。
一个年轻男子戴着几条领带微笑着。

tie: [0.574, 0.298, 0.752, 0.704]
tie: [0.464, 0.339, 0.639, 0.789]
tie: [0.349, 0.363, 0.563, 0.732]
tie: [0.259, 0.255, 0.668, 0.805]
person: [0.019, 0.065, 0.962, 0.988]
person: [0.0, 0.24, 0.214, 1.0]
tie: [0.316, 0.778, 0.443, 0.867]
tie: [0.386, 0.707, 0.496, 0.801]
tie: [0.251, 0.354, 0.402, 0.747]
tie: [0.44, 0.318, 0.63, 0.397]
tie: [0.566, 0.33, 0.655, 0.543]
tie: [0.25, 0.409, 0.359, 0.556]",""",
    "response": f"""问题:
这张照片有什么不寻常之处？
===
答案：
在照片中，这个男人脖子上戴了多条领带。这被认为是不寻常的，因为通常情况下，一个人只会戴一条领带。这个男人傻笑的表情也增加了这张照片的非同寻常和幽默性质。"""
},
    {
        "context": f"""一群人站在一辆黑色车辆外面，带着各种行李。
行李散落在地下停车场的一辆车周围。
人们试图把所有的行李都塞进一辆SUV中。
这辆运动型多用途车停在公共车库里，正在为一次旅行做准备。
一些人带着行李靠近一辆用于运输的货车。

person: [0.681, 0.242, 0.774, 0.694]
person: [0.63, 0.222, 0.686, 0.516]
person: [0.444, 0.233, 0.487, 0.34]
backpack: [0.384, 0.696, 0.485, 0.914]
backpack: [0.755, 0.413, 0.846, 0.692]
suitcase: [0.758, 0.413, 0.845, 0.69]
suitcase: [0.1, 0.497, 0.173, 0.579]
bicycle: [0.282, 0.363, 0.327, 0.442]
car: [0.786, 0.25, 0.848, 0.322]
car: [0.783, 0.27, 0.827, 0.335]
car: [0.86, 0.254, 0.891, 0.3]
car: [0.261, 0.101, 0.787, 0.626]""",
    "response": f"""问题：
这些人面临着什么挑战？
===
答案：
在这张图片中，一群人站在一个停车区域外面，周围散落着各种行李，包括手提箱和背包。他们面临的挑战是要把所有的行李都塞进这辆黑色SUV中。有多个手提箱和背包需要装载，这表明这个团队有相当多的物品需要安排。他们可能需要制定策略，高效地安排行李，以确保一切都能够正确地放入车内。此外，他们还需要考虑乘客的舒适度和驾驶过程中的可见性，因此行李的放置不能妨碍驾驶员的视线，也不能让乘客在旅途中感到不舒服。"""
}]

messages = [{"role": "system", "content": system_message_reasoning}]
for sample in fewshot_samples:
    messages.append({"role": "user", "content": sample['context']})
    messages.append({"role": "assistant", "content": sample['response']})
messages.append({"role": "user", "content": '\n'.join(
    [gpt4v_description, bbox_query])})

print(json.dumps(messages, indent=2, ensure_ascii=False))


from IPython.display import display
from PIL import Image
gpt4t_reasoning = query_gpt4_text(messages)

display(image)

print(gpt4t_reasoning)

import re
def parser_gpt4_return(input_string, first_block=True):
    # Split the input string into blocks based on the question and answer pattern
    blocks = re.split(r"===\n", input_string.strip())
    
    # Create a list to hold conversation elements
    conversations = []
    
    # Process each block to extract questions and answers
    for block in blocks:
        lines = block.split("\n")
        if lines[-1] == "":
            lines = lines[:-1]
        if lines:
            if lines[0][:3] == "问题：":
                if first_block:
                    conversations.append({"from": "human", "value": "<image>\n" + "\n".join(lines[1:])})
                    first_block = False
                else:
                    conversations.append({"from": "human", "value": "\n".join(lines[1:])})
            elif lines[0][:3] == "答案：":
                conversations.append({"from": "gpt", "value": "\n".join(lines[1:])})
            else:
                raise ValueError(f"lines[0] should be Answer: or Question. Unexpected: -{lines[0]}-")
    
    return conversations

parsed_json = parser_gpt4_return(gpt4t_conversation)
parsed_json += parser_gpt4_return(gpt4t_reasoning, first_block=False)
print(json.dumps(parsed_json, indent=2, ensure_ascii=False))
