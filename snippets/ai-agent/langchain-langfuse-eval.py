import json

# 调整数据格式 {"input":{...},"expected_output":"label"}
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


from langfuse import Langfuse
from langfuse.model import CreateDatasetRequest, CreateDatasetItemRequest
from tqdm import tqdm
import langfuse


dataset_name = "my-dataset"

# 初始化客户端
langfuse=Langfuse()

# 创建数据集，如果已存在不会重复创建
try:
    langfuse.create_dataset(
        name=dataset_name,
        # optional description
        description="My first dataset",
        # optional metadata
        metadata={
            "author": "wzr",
            "type": "demo"
        }
    )
except:
    pass

# 考虑演示运行速度，只上传前50条数据
for item in tqdm(data[:50]):
    langfuse.create_dataset_item(
        dataset_name="my-dataset",
        input=item["input"],
        expected_output=item["expected_output"]
    )

def simple_evaluation(output, expected_output):
    return output == expected_output

from langchain.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import StrOutputParser

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
    need_answer
    | model
    | parser
)

from concurrent.futures import ThreadPoolExecutor
from langfuse import Langfuse
from datetime import datetime

langfuse = Langfuse()

def run_evaluation(chain, dataset_name, run_name):
    dataset = langfuse.get_dataset(dataset_name)

    def process_item(item):
        handler = item.get_langchain_handler(run_name=run_name)

        # Assuming chain.invoke is a synchronous function
        output = chain.invoke(item.input, config={"callbacks": [handler]})

        # Assuming handler.root_span.score is a synchronous function
        handler.trace.score(
            name="accuracy",
            value=simple_evaluation(output, item.expected_output)
        )
        print('.', end='', flush=True)

    for item in dataset.items:
        process_item(item)

    # 建议并行处理
    # with ThreadPoolExecutor(max_workers=4) as executor:
    #    executor.map(process_item, dataset.items)


from langchain_core.output_parsers import BaseOutputParser
import re


class MyOutputParser(BaseOutputParser):
    """自定义parser，从思维链中取出最后的Y/N"""

    def parse(self, text: str) -> str:
        matches = re.findall(r'[YN]', text)
        return matches[-1] if matches else 'N'

chain_v2 = (
    need_answer
    | model
    | MyOutputParser()
)

run_evaluation(chain_v2, "my-dataset", "cot-"+datetime.now().strftime("%d/%m/%Y %H:%M:%S"))
langfuse.flush()
