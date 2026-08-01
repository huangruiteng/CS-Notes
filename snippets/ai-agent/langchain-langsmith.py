import os
from datetime import datetime
os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGCHAIN_API_KEY"] = os.getenv("LANGCHAIN_API_KEY", "YOUR_LANGSMITH_API_KEY")
# 可选
os.environ["LANGCHAIN_PROJECT"] = "hello-world-"+datetime.now().strftime("%d/%m/%Y %H:%M:%S")

from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough

# 定义语言模型
llm = ChatOpenAI()

# 定义Prompt模板
prompt = PromptTemplate.from_template("Say hello to {input}!")

# 定义输出解析器
parser = StrOutputParser()

chain = (
    {"input": RunnablePassthrough()}
    | prompt
    | llm
    | parser
)

chain.invoke("AGIClass")

import json

data = []
with open('my_annotations.jsonl', 'r', encoding='utf-8') as fp:
    for line in fp:
        example = json.loads(line.strip())
        item = {
            "input": {
                "outlines": example["outlines"],
                "user_input": example["user_input"]
            },
            "expected_output": example["label"]
        }
        data.append(item)

from langsmith import Client

client = Client()

dataset_name = "assistant-"+datetime.now().strftime("%d/%m/%Y %H:%M:%S")

dataset = client.create_dataset(
    dataset_name,  # 数据集名称
    description="AGIClass线上跟课助手的标注数据",  # 数据集描述
)


client.create_examples(
    inputs=[{"input": item["input"]} for item in data[:50]],
    outputs=[{"output": item["expected_output"]} for item in data[:50]],
    dataset_id=dataset.id
)

from langchain.evaluation import StringEvaluator
from nltk.translate.bleu_score import sentence_bleu, SmoothingFunction
import re
from typing import Optional, Any


class AccuracyEvaluator(StringEvaluator):

    def __init__(self):
        pass

    @property
    def requires_input(self) -> bool:
        return False

    @property
    def requires_reference(self) -> bool:
        return True

    @property
    def evaluation_name(self) -> str:
        return "accuracy"

    def _evaluate_strings(
        self,
        prediction: str,
        input: Optional[str] = None,
        reference: Optional[str] = None,
        **kwargs: Any
    ) -> dict:
        return {"score": int(prediction == reference)}

from langchain.evaluation import EvaluatorType
from langchain.smith import RunEvalConfig

evaluation_config = RunEvalConfig(
    # 自定义评估标准
    custom_evaluators=[AccuracyEvaluator()],
)

from langchain.prompts import PromptTemplate

need_answer = PromptTemplate.from_template("""
*********
你是AIGC课程的助教，你的工作是从学员的课堂交流中选择出需要老师回答的问题，加以整理以交给老师回答。
 
课程内容:
{outlines}
*********
学员输入:
{user_input}
*********
如果这是一个需要老师答疑的问题，回复Y，否则回复N。
只回复Y或N，不要回复其他内容。""")

model = ChatOpenAI(temperature=0, model_kwargs={"seed": 42})
parser = StrOutputParser()

chain_v1 = (
    {
        "outlines": lambda x: x["input"]["outlines"],
        "user_input": lambda x: x["input"]["user_input"],
    }
    | need_answer
    | model
    | parser
)

from langchain.smith import (
    arun_on_dataset,
    run_on_dataset,
)

results = await arun_on_dataset(
    dataset_name=dataset_name,
    llm_or_chain_factory=chain_v1,
    evaluation=evaluation_config,
    verbose=True,
    client=client,
    project_metadata={
        "version": "prompt_v1",
    },  # 可选，自定义的标识
)
