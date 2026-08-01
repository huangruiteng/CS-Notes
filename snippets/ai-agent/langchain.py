### chat model

from langchain_openai import ChatOpenAI
from langchain_community.chat_models import QianfanChatEndpoint

llm = ChatOpenAI()  # 默认是gpt-3.5-turbo
llm = QianfanChatEndpoint(
    qianfan_ak=os.getenv('ERNIE_CLIENT_ID'),
    qianfan_sk=os.getenv('ERNIE_CLIENT_SECRET')
)
response = llm.invoke("你是谁")
print(response.content)

from langchain.schema import (
    AIMessage,  # 等价于OpenAI接口中的assistant role
    HumanMessage,  # 等价于OpenAI接口中的user role
    SystemMessage  # 等价于OpenAI接口中的system role
)

messages = [
    SystemMessage(content="你是AGIClass的课程助理。"),
    HumanMessage(content="我是学员，我叫王卓然。"),
    AIMessage(content="欢迎！"),
    HumanMessage(content="我是谁")
]

ret = llm.invoke(messages)

print(ret.content)

### Prompt template

from langchain.prompts import PromptTemplate

template = PromptTemplate.from_template("给我讲个关于{subject}的笑话")
print("===Template===")
print(template)
print("===Prompt===")
print(template.format(subject='小明'))

from langchain.prompts import (
    ChatPromptTemplate,
    HumanMessagePromptTemplate,
    SystemMessagePromptTemplate,
)
from langchain_openai import ChatOpenAI

template = ChatPromptTemplate.from_messages(
    [
        SystemMessagePromptTemplate.from_template(
            "你是{product}的客服助手。你的名字叫{name}"),
        HumanMessagePromptTemplate.from_template("{query}"),
    ]
)

llm = ChatOpenAI()
prompt = template.format_messages(
    product="AGI课堂",
    name="瓜瓜",
    query="你是谁"
)

ret = llm.invoke(prompt)

print(ret.content)

from langchain.prompts import (
    ChatPromptTemplate,
    HumanMessagePromptTemplate,
    MessagesPlaceholder,
)

# ChatPromptTemplate 用模板表示的对话上下文
# MessagesPlaceholder 把多轮对话变成模板

template = ChatPromptTemplate.from_messages(
    [
        SystemMessagePromptTemplate.from_template(
            "你是{product}的客服助手。你的名字叫{name}"),
        HumanMessagePromptTemplate.from_template("{query}"),
    ]
)

# 从文件加载
template = PromptTemplate.from_file("example_prompt_template.txt")


### Output Parser

# Pydantic (JSON) Parser

from langchain_core.pydantic_v1 import BaseModel, Field, validator
from typing import List, Dict

# 定义你的输出对象

class Date(BaseModel):
    year: int = Field(description="Year")
    month: int = Field(description="Month")
    day: int = Field(description="Day")
    era: str = Field(description="BC or AD")

    # ----- 可选机制 --------
    # 你可以添加自定义的校验机制
    @validator('month')
    def valid_month(cls, field):
        if field <= 0 or field > 12:
            raise ValueError("月份必须在1-12之间")
        return field

    @validator('day')
    def valid_day(cls, field):
        if field <= 0 or field > 31:
            raise ValueError("日期必须在1-31日之间")
        return field

    @validator('day', pre=True, always=True)
    def valid_date(cls, day, values):
        year = values.get('year')
        month = values.get('month')

        # 确保年份和月份都已经提供
        if year is None or month is None:
            return day  # 无法验证日期，因为没有年份和月份

        # 检查日期是否有效
        if month == 2:
            if cls.is_leap_year(year) and day > 29:
                raise ValueError("闰年2月最多有29天")
            elif not cls.is_leap_year(year) and day > 28:
                raise ValueError("非闰年2月最多有28天")
        elif month in [4, 6, 9, 11] and day > 30:
            raise ValueError(f"{month}月最多有30天")

        return day

    @staticmethod
    def is_leap_year(year):
        if year % 400 == 0 or (year % 4 == 0 and year % 100 != 0):
            return True
        return False

from langchain.prompts import PromptTemplate, ChatPromptTemplate, HumanMessagePromptTemplate
from langchain_openai import ChatOpenAI

from langchain_core.output_parsers import PydanticOutputParser


model_name = 'gpt-3.5-turbo'
temperature = 0
model = ChatOpenAI(model_name=model_name, temperature=temperature)

# 根据Pydantic对象的定义，构造一个OutputParser
parser = PydanticOutputParser(pydantic_object=Date)

template = """提取用户输入中的日期。
{format_instructions}
用户输入:
{query}"""

prompt = PromptTemplate(
    template=template,
    input_variables=["query"],
    # 直接从OutputParser中获取输出描述，并对模板的变量预先赋值
    partial_variables={"format_instructions": parser.get_format_instructions()}
)

print("====Format Instruction=====")
print(parser.get_format_instructions())


query = "2023年四月6日天气晴..."
model_input = prompt.format_prompt(query=query)

print("====Prompt=====")
print(model_input.to_string())

output = model.invoke(model_input.to_messages())
print("====模型原始输出=====")
print(output.content)
print("====Parse后的输出=====")
date = parser.parse(output.content)
print(date.dict())

# As an example, for the schema {"properties": {"foo": {"title": "Foo", "description": "a list of strings", "type": "array", "items": {"type": "string"}}}, "required": ["foo"]}
# the object {"foo": ["bar", "baz"]} is a well-formatted instance of the schema. The object {"properties": {"foo": ["bar", "baz"]}} is not well-formatted.

from langchain.output_parsers import OutputFixingParser

new_parser = OutputFixingParser.from_llm(
    parser=parser, llm=ChatOpenAI(model="gpt-3.5-turbo"))

# 我们把之前output的格式改错
output = output.content.replace("4", "四月")
print("===格式错误的Output===")
print(output)
try:
    date = parser.parse(output)
except Exception as e:
    print("===出现异常===")
    print(e)

# 用OutputFixingParser自动修复并解析
date = new_parser.parse(output)
print("===重新解析结果===")
print(date.json())



### Data connector

# LangChain 的 PDFLoader 和 TextSplitter 实现都比较粗糙，实际生产中不建议使用。

from langchain_community.document_loaders import PyPDFLoader

loader = PyPDFLoader("llama2.pdf")
pages = loader.load_and_split()

print(pages[0].page_content)

from langchain_text_splitters import RecursiveCharacterTextSplitter

text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=200,
    chunk_overlap=100, 
    length_function=len,
    add_start_index=True,
)

paragraphs = text_splitter.create_documents([pages[0].page_content])
for para in paragraphs:
    print(para.page_content)
    print('-------')


from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_openai import ChatOpenAI
from langchain_community.document_loaders import PyPDFLoader

# 加载文档
loader = PyPDFLoader("llama2.pdf")
pages = loader.load_and_split()

# 文档切分
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=200,
    chunk_overlap=100,
    length_function=len,
    add_start_index=True,
)

texts = text_splitter.create_documents(
    [page.page_content for page in pages[:4]]
)

# 灌库
embeddings = OpenAIEmbeddings(model="text-embedding-ada-002")
db = FAISS.from_documents(texts, embeddings)

# 检索 top-5 结果
retriever = db.as_retriever(search_kwargs={"k": 5})

docs = retriever.invoke("llama2有多少参数")

for doc in docs:
    print(doc.page_content)
    print("----")


### Memory
from langchain.memory import ConversationBufferMemory, ConversationBufferWindowMemory

history = ConversationBufferMemory()
history.save_context({"input": "你好啊"}, {"output": "你也好啊"})

print(history.load_memory_variables({}))

history.save_context({"input": "你再好啊"}, {"output": "你又好啊"})

print(history.load_memory_variables({}))


from langchain.memory import ConversationBufferWindowMemory

window = ConversationBufferWindowMemory(k=2) # 一问一答算一轮，保留一轮
window.save_context({"input": "第一轮问"}, {"output": "第一轮答"})
window.save_context({"input": "第二轮问"}, {"output": "第二轮答"})
window.save_context({"input": "第三轮问"}, {"output": "第三轮答"})
print(window.load_memory_variables({}))

from langchain.memory import ConversationTokenBufferMemory
from langchain_openai import ChatOpenAI

memory = ConversationTokenBufferMemory(
    llm=ChatOpenAI(),
    max_token_limit=40
)
memory.save_context(
    {"input": "你好啊"}, {"output": "你好，我是你的AI助手。"})
memory.save_context(
    {"input": "你会干什么"}, {"output": "我什么都会"})

print(memory.load_memory_variables({}))

- ConversationSummaryMemory: 对上下文做摘要
  - https://python.langchain.com/docs/modules/memory/types/summary
- ConversationSummaryBufferMemory: 保存 Token 数限制内的上下文，对更早的做摘要
  - https://python.langchain.com/docs/modules/memory/types/summary_buffer
- VectorStoreRetrieverMemory: 将 Memory 存储在向量数据库中，根据用户输入检索回最相关的部分
  - https://python.langchain.com/docs/modules/memory/types/vectorstore_retriever_memory



### Pipeline 式调用 PromptTemplate, LLM 和 OutputParser
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser, PydanticOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain_core.pydantic_v1 import BaseModel, Field, validator
from typing import List, Dict, Optional
from enum import Enum
import json

# 输出结构
class SortEnum(str, Enum):
    data = 'data'
    price = 'price'


class OrderingEnum(str, Enum):
    ascend = 'ascend'
    descend = 'descend'


class Semantics(BaseModel):
    name: Optional[str] = Field(description="流量包名称", default=None)
    price_lower: Optional[int] = Field(description="价格下限", default=None)
    price_upper: Optional[int] = Field(description="价格上限", default=None)
    data_lower: Optional[int] = Field(description="流量下限", default=None)
    data_upper: Optional[int] = Field(description="流量上限", default=None)
    sort_by: Optional[SortEnum] = Field(description="按价格或流量排序", default=None)
    ordering: Optional[OrderingEnum] = Field(
        description="升序或降序排列", default=None)


# OutputParser
parser = PydanticOutputParser(pydantic_object=Semantics)

# Prompt 模板
prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "将用户的输入解析成JSON表示。输出格式如下：\n{format_instructions}\n不要输出未提及的字段。",
        ),
        ("human", "{text}"),
    ]
).partial(format_instructions=parser.get_format_instructions())

# 模型
model = ChatOpenAI(model="gpt-4-turbo", temperature=0)

### LCEL 表达式
runnable = (
    {"text": RunnablePassthrough()} | prompt | model | StrOutputParser()
)
ret = runnable.invoke("不超过100元的流量大的套餐有哪些")
# for s in runnable.stream("不超过100元的流量大的套餐有哪些"):
#    print(s, end="")
print(json.dumps(ret.dict(),indent=4,ensure_ascii=False))


# Coercion
mapping = {
    "key1": runnable1,
    "key2": runnable2,
}

chain = mapping | runnable3

def some_func(x):
    return x

chain = some_func | runnable1
chain = RunnableSequence([RunnableLambda(some_func), runnable1])

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough


prompt = ChatPromptTemplate.from_template(
    "Tell me a short joke about {topic}"
)
output_parser = StrOutputParser()
model = ChatOpenAI(model="gpt-3.5-turbo")
chain = (
    {"topic": RunnablePassthrough()} 
    | prompt
    | model
    | output_parser
)

chain.invoke("ice cream")

for chunk in chain.stream("ice cream"):
    print(chunk, end="", flush=True)

chain.batch(["ice cream", "spaghetti", "dumplings"])
await chain.ainvoke("ice cream")
await chain.abatch(["ice cream", "spaghetti", "dumplings"])

from langchain_core.runnables import ConfigurableField


configurable_model = model.configurable_alternatives(
    ConfigurableField(id="model"), 
    default_key="chat_openai", 
    openai=llm,
    anthropic=anthropic,
)
configurable_chain = (
    {"topic": RunnablePassthrough()} 
    | prompt 
    | configurable_model 
    | output_parser
)

configurable_chain.invoke(
    "ice cream", 
    config={"model": "openai"}
)
stream = configurable_chain.stream(
    "ice cream", 
    config={"model": "anthropic"}
)
for chunk in stream:
    print(chunk, end="", flush=True)

configurable_chain.batch(["ice cream", "spaghetti", "dumplings"])

# await configurable_chain.ainvoke("ice cream")


fallback_chain = chain.with_fallbacks([anthropic_chain])

fallback_chain.invoke("ice cream")
# await fallback_chain.ainvoke("ice cream")
fallback_chain.batch(["ice cream", "spaghetti", "dumplings"])


# Full Example
import os

from langchain_anthropic import ChatAnthropic
from langchain_openai import ChatOpenAI
from langchain_openai import OpenAI
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough, ConfigurableField

os.environ["LANGCHAIN_API_KEY"] = "..."
os.environ["LANGCHAIN_TRACING_V2"] = "true"

prompt = ChatPromptTemplate.from_template(
    "Tell me a short joke about {topic}"
)
chat_openai = ChatOpenAI(model="gpt-3.5-turbo")
openai = OpenAI(model="gpt-3.5-turbo-instruct")
anthropic = ChatAnthropic(model="claude-2")
model = (
    chat_openai
    .with_fallbacks([anthropic])
    .configurable_alternatives(
        ConfigurableField(id="model"),
        default_key="chat_openai",
        openai=openai,
        anthropic=anthropic,
    )
)

chain = (
    {"topic": RunnablePassthrough()} 
    | prompt 
    | model 
    | StrOutputParser()
)

### LangChain应用

# LangChain RAG

from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_openai import ChatOpenAI
from langchain.chains import RetrievalQA
from langchain_community.document_loaders import PyPDFLoader

loader = PyPDFLoader("llama2.pdf")
pages = loader.load_and_split()

text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=200,
    chunk_overlap=100,
    length_function=len,
    add_start_index=True,
)

texts = text_splitter.create_documents(
    [page.page_content for page in pages[:4]]
)

db = FAISS.from_documents(texts, OpenAIEmbeddings(model="text-embedding-ada-002"))
retriever = db.as_retriever(search_kwargs={"k": 5})


from langchain.schema.output_parser import StrOutputParser
from langchain.schema.runnable import RunnablePassthrough

template = """Answer the question based only on the following context:
{context}

Question: {question}
"""
prompt = ChatPromptTemplate.from_template(template)

rag_chain = (
    {"question": RunnablePassthrough(), "context": retriever}
    | prompt
    | model
    | StrOutputParser()
)

rag_chain.invoke("Llama 2有多少参数")

# LangChain Function Calling
from langchain_core.tools import tool


@tool
def multiply(first_int: int, second_int: int) -> int:
    """两个整数相乘"""
    return first_int * second_int


@tool
def add(first_int: int, second_int: int) -> int:
    """Add two integers."""
    return first_int + second_int


@tool
def exponentiate(base: int, exponent: int) -> int:
    """Exponentiate the base to the exponent power."""
    return base**exponent

from langchain_core.output_parsers import StrOutputParser
from langchain.output_parsers import JsonOutputToolsParser

tools = [multiply, add, exponentiate]
# 带有分支的 LCEL
llm_with_tools = model.bind_tools(tools) | {
    "functions": JsonOutputToolsParser(),
    "text": StrOutputParser()
}




# LangChain直接选择工具并运行
from typing import Union
from operator import itemgetter
from langchain_core.runnables import (
    Runnable,
    RunnableLambda,
    RunnableMap,
    RunnablePassthrough,
)

tool_map = {tool.name: tool for tool in tools}


def call_tool(tool_invocation: dict) -> Union[str, Runnable]:
    """根据模型选择的 tool 动态创建 LCEL"""
    tool = tool_map[tool_invocation["type"]]
    return RunnablePassthrough.assign(
        output=itemgetter("args") | tool
    )


call_tool_list = RunnableLambda(call_tool).map() # .map() 使 function 逐一作用于一组输入

import json


def route(response):
    if len(response["functions"]) > 0:
        return response["functions"]
    else:
        return response["text"]


llm_with_tools = model.bind_tools(tools) | {
    "functions": JsonOutputToolsParser() | call_tool_list,
    "text": StrOutputParser()
} | RunnableLambda(route)

result = llm_with_tools.invoke("1024的平方是多少")
print(result)

result = llm_with_tools.invoke("你好")
print(result)


### Langchain工厂模式

from langchain_core.runnables.utils import ConfigurableField
from langchain_openai import ChatOpenAI
from langchain_community.chat_models import QianfanChatEndpoint
from langchain.prompts import (
    ChatPromptTemplate,
    HumanMessagePromptTemplate,
)
from langchain.schema import HumanMessage
import os

# 模型1
ernie_model = QianfanChatEndpoint(
    qianfan_ak=os.getenv('ERNIE_CLIENT_ID'),
    qianfan_sk=os.getenv('ERNIE_CLIENT_SECRET')
)

# 模型2
gpt_model = ChatOpenAI()


# 通过 configurable_alternatives 按指定字段选择模型
model = gpt_model.configurable_alternatives(
    ConfigurableField(id="llm"), 
    default_key="gpt", 
    ernie=ernie_model,
    # claude=claude_model,
)

# Prompt 模板
prompt = ChatPromptTemplate.from_messages(
    [
        HumanMessagePromptTemplate.from_template("{query}"),
    ]
)

# LCEL
chain = (
    {"query": RunnablePassthrough()} 
    | prompt
    | model 
    | StrOutputParser()
)

# 运行时指定模型 "gpt" or "ernie"
ret = chain.with_config(configurable={"llm": "ernie"}).invoke("介绍你自己，包括你的生产商")

print(ret)


### LangGraph
from langchain_core.messages import HumanMessage
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import START, MessagesState, StateGraph

# Define a new graph
workflow = StateGraph(state_schema=MessagesState)


# Define the function that calls the model
def call_model(state: MessagesState):
    response = llm.invoke(state["messages"])
    # Update message history with response:
    return {"messages": response}


# Define the (single) node in the graph
workflow.add_edge(START, "model")
workflow.add_node("model", call_model)

# Add memory
memory = MemorySaver()
app = workflow.compile(checkpointer=memory)
