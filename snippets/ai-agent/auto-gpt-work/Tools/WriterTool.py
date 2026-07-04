from langchain.prompts import ChatPromptTemplate
from langchain.prompts.chat import SystemMessagePromptTemplate, HumanMessagePromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain_openai import ChatOpenAI


def write(query: str, verbose=False):
    """按用户要求撰写文档"""
    template = ChatPromptTemplate.from_messages(
        [
            SystemMessagePromptTemplate.from_template(
                "你是专业的文档写手。你根据客户的要求，写一份文档。输出中文。"),
            HumanMessagePromptTemplate.from_template("{query}"),
        ]
    )

    chain = {"query": RunnablePassthrough()} | template | ChatOpenAI() | StrOutputParser()

    return chain.invoke(query)


if __name__ == "__main__":
    print(write("写一封邮件给张三，内容是：你好，我是李四。"))
