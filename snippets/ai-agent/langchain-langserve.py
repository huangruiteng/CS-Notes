### LangServe

# 安装 LangServe
# !pip install --upgrade "langserve[all]"

# 也可以只安装一端
# !pip install "langserve[client]"
# !pip install "langserve[server]"


### Server

#!/usr/bin/env python
from fastapi import FastAPI
from langchain.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langserve import add_routes
import uvicorn

app = FastAPI(
  title="LangChain Server",
  version="1.0",
  description="A simple api server using Langchain's Runnable interfaces",
)

model = ChatOpenAI()
prompt = ChatPromptTemplate.from_template("讲一个关于{topic}的笑话")
add_routes(
    app,
    prompt | model,
    path="/joke",
)

if __name__ == "__main__":
    uvicorn.run(app, host="localhost", port=9999)


### Client

import requests

response = requests.post(
    "http://localhost:9999/joke/invoke",
    json={'input': {'topic': '小明'}}
)
print(response.json())

