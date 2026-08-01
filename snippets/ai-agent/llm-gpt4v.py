pip  install gradio openai google-generativeai


import gradio as gr
from openai import OpenAI
import base64
from PIL import Image
import io
import os
import google.generativeai as genai
import anthropic, openai

# Function to encode the image to base64


def encode_image_to_base64(image):
    buffered = io.BytesIO()
    image.save(buffered, format="JPEG")
    return base64.b64encode(buffered.getvalue()).decode('utf-8')

# Function to query GPT-4 Vision


def query_gpt4_vision(text, image1, image2, image3):
    client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
    messages = [{"role": "user", "content": [{"type": "text", "text": text}]}]

    images = [image1, image2, image3]
    for image in images:
        if image is not None:
            base64_image = encode_image_to_base64(image)
            image_message = {
                "type": "image_url",
                "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}
            }
            messages[0]["content"].append(image_message)

    response = client.chat.completions.create(
        #model="gpt-4-vision-preview",
        model="gpt-4-turbo",
        messages=messages,
        max_tokens=1024,
    )
    return response.choices[0].message.content

def query_gpt4o_vision(text, image1, image2, image3):
    client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
    messages = [{"role": "user", "content": [{"type": "text", "text": text}]}]

    images = [image1, image2, image3]
    for image in images:
        if image is not None:
            base64_image = encode_image_to_base64(image)
            image_message = {
                "type": "image_url",
                "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}
            }
            messages[0]["content"].append(image_message)

    response = client.chat.completions.create(
        model="gpt-4o",
        #model=model_type,
        messages=messages,
        max_tokens=1024,
    )
    return response.choices[0].message.content

def query_gpt4o_mini_vision(text, image1, image2, image3):
    client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
    messages = [{"role": "user", "content": [{"type": "text", "text": text}]}]

    images = [image1, image2, image3]
    for image in images:
        if image is not None:
            base64_image = encode_image_to_base64(image)
            image_message = {
                "type": "image_url",
                "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}
            }
            messages[0]["content"].append(image_message)

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        #model=model_type,
        messages=messages,
        max_tokens=1024,
    )
    return response.choices[0].message.content
# Function to query Gemini-Pro

def query_claude_vision(text, image1, image2, image3):
    claude_key = ""
    modelConfig ={
        "claude_S": "claude-3-haiku-20240307",
        "claude_M": "claude-3-sonnet-20240229",
        "claude_B": "claude-3-opus-20240229",
    }
    client = anthropic.Anthropic(api_key=claude_key)
    messages = [{"role": "user", "content": [{"type": "text", "text": text}]}]

    images = [image1, image2, image3]
    for image in images:
        if image is not None:
            base64_image = encode_image_to_base64(image)
            image_message = {
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": "image/jpeg",
                    "data": base64_image,
                }
            }
            messages[0]["content"].append(image_message)
    #print(messages)
    response = client.messages.create(
        #model="gpt-4-vision-preview",
        model=modelConfig["claude_M"],
        messages=messages,
        max_tokens=1024,
    )
    return response.content[0].text

def query_gemini_vision(text, image1, image2, image3):
    # Or use `os.getenv('GOOGLE_API_KEY')` to fetch an environment variable.
    # GOOGLE_API_KEY=userdata.get('GOOGLE_API_KEY')
    GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
    genai.configure(api_key=GOOGLE_API_KEY)
    model = genai.GenerativeModel('gemini-1.5-flash')

    images = [image1, image2, image3]
    query = [text]
    for image in images:
        if image is not None:
            query.append(image)
    response = model.generate_content(query, stream=False)
    response.resolve()

    return response.text

# 由于Gradio 2.0及以上版本的界面构建方式有所不同，这里使用blocks API来创建更复杂的UI


def main():
    with gr.Blocks() as demo:
        gr.Markdown("### 输入文本")
        input_text = gr.Textbox(lines=2, label="输入文本")
        input_images = [
            gr.Image(type="pil", label="Upload Image", tool="editor") for i in range(3)]
        output_gpt4 = gr.Textbox(label="GPT-4v-Turbo 输出")
        output_gemini = gr.Textbox(label="Gemini-Pro 输出")
        output_claude3 = gr.Textbox(label="Claude3 sonnet 输出")
        output_gpt4o = gr.Textbox(label="GPT-4o 输出")
        output_gpt4o_mini = gr.Textbox(label="GPT-4o-mini 输出")


        btn_gpt4 = gr.Button("调用GPT-4")
        btn_gemini = gr.Button("调用Gemini-Pro")
        btn_claude = gr.Button("调用Claude-3-sonnet")
        btn_gpt4o = gr.Button("调用GPT-4o")
        btn_gpt4o_mini = gr.Button("调用GPT-4o-mini")

        btn_gpt4.click(fn=query_gpt4_vision, inputs=[
                       input_text] + input_images, outputs=output_gpt4)
        btn_gemini.click(fn=query_gemini_vision, inputs=[
                            input_text] + input_images, outputs=output_gemini)
        btn_claude.click(fn=query_claude_vision, inputs=[
                       input_text] + input_images, outputs=output_claude3)
        btn_gpt4o.click(fn=query_gpt4o_vision, inputs=[
                       input_text] + input_images, outputs=output_gpt4o)
        btn_gpt4o_mini.click(fn=query_gpt4o_mini_vision, inputs=[
                       input_text] + input_images, outputs=output_gpt4o_mini)

    demo.launch(share=True)


if __name__ == "__main__":
    main()

import gradio as gr
from openai import OpenAI
import base64
from PIL import Image
import io
import os

# Function to encode the image to base64


def encode_image_to_base64(image):
    buffered = io.BytesIO()
    image.save(buffered, format="JPEG")
    return base64.b64encode(buffered.getvalue()).decode('utf-8')

# Function to query GPT-4 Vision


def query_gpt4_vision(*inputs):
    client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
    messages = [{"role": "user", "content": []}]

    for input_item in inputs:
        if isinstance(input_item, str):  # Text input
            messages[0]["content"].append({"type": "text", "text": input_item})
        elif isinstance(input_item, Image.Image):  # Image input
            base64_image = encode_image_to_base64(input_item)
            messages[0]["content"].append({
                "type": "image_url",
                "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}
            })

    response = client.chat.completions.create(
        model="gpt-4-turbo",
        messages=messages,
        max_tokens=1024,
    )
    return response.choices[0].message.content

# Function to query Gemini-Pro


def query_gemini_vision(*inputs):
    # Or use `os.getenv('GOOGLE_API_KEY')` to fetch an environment variable.
    # GOOGLE_API_KEY=userdata.get('GOOGLE_API_KEY')
    GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
    # print(GOOGLE_API_KEY)
    genai.configure(api_key=GOOGLE_API_KEY)
    model = genai.GenerativeModel('gemini-1.5-flash')

    query = []
    for item in inputs:
        if item is not None:
            query.append(item)
    response = model.generate_content(query, stream=False)
    response.resolve()

    return response.text


'''
    
# Dynamically generate input components
input_components = []
for i in range(2):  # Change this number to add more inputs
    input_components.append(gr.components.Textbox(lines=2, placeholder=f"Enter your text input {i+1}..."))
    input_components.append(gr.components.Image(type="pil", label=f"Upload Image {i+1}", tool="editor"))

iface = gr.Interface(
    fn=query_gpt4_vision,
    inputs=input_components,
    outputs=gr.components.Text(update=True), 
)

iface.launch(share=True)

'''

# 由于Gradio 2.0及以上版本的界面构建方式有所不同，这里使用blocks API来创建更复杂的UI


def main():
    with gr.Blocks() as demo:
        gr.Markdown("### 输入文本")
        # input_text = gr.Textbox(lines=2, label="输入文本")
        input_components = []
        for i in range(2):  # Change this number to add more inputs
            input_components.append(gr.Textbox(
                lines=2, placeholder=f"Enter your text input {i+1}..."))
            input_components.append(
                gr.Image(type="pil", label=f"Upload Image {i+1}", tool="editor"))

        # input_images = [gr.Image(type="pil", label="Upload Image", tool="editor") for i in range(3)]
        output_gpt4 = gr.Textbox(label="GPT-4 输出")
        output_other_api = gr.Textbox(label="Gemini-Pro 输出")
        btn_gpt4 = gr.Button("调用GPT-4")
        btn_other_api = gr.Button("调用Gemini-Pro")

        btn_gpt4.click(fn=query_gpt4_vision,
                       inputs=input_components, outputs=output_gpt4)
        btn_other_api.click(fn=query_gemini_vision,
                            inputs=input_components, outputs=output_other_api)

    demo.launch(share=True)


if __name__ == "__main__":
    main()