### Usage

# Method 1: cloud.langfuse.com

LANGFUSE_SECRET_KEY="sk-lf-..."
LANGFUSE_PUBLIC_KEY="pk-lf-..."


# Method 2: Clone repository
git clone https://github.com/langfuse/langfuse.git
cd langfuse

# Run server and db
docker compose up -d

LANGFUSE_SECRET_KEY="sk-lf-..."
LANGFUSE_PUBLIC_KEY="pk-lf-.."
LANGFUSE_HOST="http://localhost:3000"


### Decorator记录

from langfuse.decorators import observe
from langfuse.openai import openai # OpenAI integration
 
@observe()
def run():
    return openai.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
          {"role": "user", "content": "对我说Hello, World!"}
        ],
    ).choices[0].message.content
 
print(run())


def observe(
	self,
	*,
	name: Optional[str] = None, # Trace 或 Span 的名称，默认为函数名
	as_type: Optional[Literal['generation']] = None, # 将记录定义为 Observation (LLM 调用）
	capture_input: bool = True, # 记录输入
	capture_output: bool = True, # 记录输出
	transform_to_string: Optional[Callable[[Iterable], str]] = None # 将输出转为 string
) -> Callable[[~F], ~F]:


# 通过 `langfuse_context` 记录 User ID、Metadata 等

from langfuse.decorators import observe, langfuse_context
from langfuse.openai import openai # OpenAI integration
 
@observe()
def run():
    langfuse_context.update_current_trace(
        name="HelloWorld",
        user_id="wzr",
        metadata={"test":"test value"}
    )
    return openai.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
          {"role": "user", "content": "对我说Hello, World!"}
        ],
    ).choices[0].message.content
 
print(run())


### 通过 LangChain 的回调集成

import os
os.environ["LANGCHAIN_TRACING_V2"] = ""
os.environ["LANGCHAIN_API_KEY"] = ""

from langchain.prompts import (
    ChatPromptTemplate,
    HumanMessagePromptTemplate,
)
from langchain_core.output_parsers import StrOutputParser
from langchain_openai import ChatOpenAI
from langchain_core.runnables import RunnablePassthrough

model = ChatOpenAI(model="gpt-3.5-turbo")

prompt = ChatPromptTemplate.from_messages([
    HumanMessagePromptTemplate.from_template("Say hello to {input}!")
])


# 定义输出解析器
parser = StrOutputParser()

chain = (
    {"input": RunnablePassthrough()}
    | prompt
    | model
    | parser
)

from langfuse.decorators import langfuse_context, observe

@observe()
def run():
    langfuse_context.update_current_trace(
            name="LangChainDemo",
            user_id="wzr",
        )
    
    # get the langchain handler for the current trace
    langfuse_handler = langfuse_context.get_current_langchain_handler()
    
    return chain.invoke(input="AGIClass", config={"callbacks": [langfuse_handler]})

print(run())



### 原始Demo

# 构建 PromptTemplate
from langchain.prompts import PromptTemplate

need_answer = PromptTemplate.from_template("""
*********
你是AIGC课程的助教，你的工作是从学员的课堂交流中选择出需要老师回答的问题，加以整理以交给老师回答。

你的选择需要遵循以下原则：
1 需要老师回答的问题是指与课程内容或AI/LLM相关的技术问题；
2 评论性的观点、闲聊、表达模糊不清的句子，不需要老师回答；
3 学生输入不构成疑问句的，不需要老师回答；
4 学生问题中如果用“这”、“那”等代词指代，不算表达模糊不清，请根据问题内容判断是否需要老师回答。
 
课程内容:
{outlines}
*********
学员输入:
{user_input}
*********
Analyse the student's input according to the lecture's contents and your criteria.
Output your analysis process step by step.
Finally, output a single letter Y or N in a separate line.
Y means that the input needs to be answered by the teacher.
N means that the input does not needs to be answered by the teacher.""")

check_duplicated = PromptTemplate.from_template("""
*********
已有提问列表:
[
{question_list}
]
*********
新提问:
{user_input}
*********
已有提问列表是否有和新提问类似的问题? 回复Y或N, Y表示有，N表示没有。
只回复Y或N，不要回复其他内容。""")

outlines = """
LangChain
模型 I/O 封装
模型的封装
模型的输入输出
PromptTemplate
OutputParser
数据连接封装
文档加载器：Document Loaders
文档处理器
内置RAG：RetrievalQA
记忆封装：Memory
链架构：Chain/LCEL
大模型时代的软件架构：Agent
ReAct
SelfAskWithSearch
LangServe
LangChain.js
"""

question_list = [
    "LangChain可以商用吗",
    "LangChain开源吗",
]

# 创建 chain
model = ChatOpenAI(temperature=0, model_kwargs={"seed": 42})
parser = StrOutputParser()

need_answer_chain = (
    need_answer
    | model
    | parser
)

is_duplicated_chain = (
    check_duplicated
    | model
    | parser
)

import uuid
from langfuse.decorators import langfuse_context, observe

# 主流程
@observe()
def verify_question(
    question: str,
    outlines: str,
    question_list: list,
    user_id: str,
) -> bool:
    langfuse_context.update_current_trace(
            name="AGIClassAssistant",
            user_id=user_id,
        )
    
    # get the langchain handler for the current trace
    langfuse_handler = langfuse_context.get_current_langchain_handler()
    # 判断是否需要回答
    if need_answer_chain.invoke(
        {"user_input": question, "outlines": outlines},
        config={"callbacks": [langfuse_handler]}
    ) == 'Y':
        # 判断是否为重复问题
        if is_duplicated_chain.invoke(
            {"user_input": question,
                "question_list": "\n".join(question_list)},
            config={"callbacks": [langfuse_handler]}
        ) == 'N':
            question_list.append(question)
            return True
    return False

ret = verify_question(
    # "LangChain支持Java吗",
    "老师好",
    outlines,
    question_list,
    user_id="wzr",
)
print(ret)



### Session

from langchain_openai import ChatOpenAI
from langchain_core.messages import (
    AIMessage,  # 等价于OpenAI接口中的assistant role
    HumanMessage,  # 等价于OpenAI接口中的user role
    SystemMessage  # 等价于OpenAI接口中的system role
)
from datetime import datetime
from langfuse.decorators import langfuse_context, observe

now = datetime.now()

llm = ChatOpenAI()

messages = [
    SystemMessage(content="你是AGIClass的课程助理。"),
]

@observe()
def chat_one_turn(user_input, user_id, turn_id):
    langfuse_context.update_current_trace(
        name=f"ChatTurn{turn_id}",
        user_id=user_id,
        session_id="chat-"+now.strftime("%d/%m/%Y %H:%M:%S")
    )
    langfuse_handler = langfuse_context.get_current_langchain_handler()
    messages.append(HumanMessage(content=user_input))
    response = llm.invoke(messages, config={"callbacks": [langfuse_handler]})
    messages.append(response)
    return response.content    



### Prompt Management

# 按名称加载
prompt = langfuse.get_prompt("need_answer_v1")

# 按名称和版本号加载
prompt = langfuse.get_prompt("need_answer_v1", version=2)

# 对模板中的变量赋值
compiled_prompt = prompt.compile(input="老师好", outlines="test")

print(compiled_prompt)

# 获取 config

prompt = langfuse.get_prompt("need_answer_v1", version=5)

print(prompt.config)