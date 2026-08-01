from openai import OpenAI

from dotenv import load_dotenv, find_dotenv
_ = load_dotenv(find_dotenv())

client = OpenAI()

prompt = "今天我很"  # 改我试试
# prompt = "下班了，今天我很"
# prompt = "放学了，今天我很"
# prompt = "AGI 实现了，今天我很"
response = client.chat.completions.create(
    model="gpt-3.5-turbo-instruct",
    prompt=prompt,
    max_tokens=512,
    stream=True
)

for chunk in response:
    print(chunk.choices[0].text, end='')
