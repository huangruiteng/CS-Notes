# 加载环境变量
from dotenv import load_dotenv, find_dotenv
_ = load_dotenv(find_dotenv())

from Agent.AutoGPT import AutoGPT
from langchain_openai import ChatOpenAI
from Tools import *
from Tools.PythonTool import ExcelAnalyser
from langchain_community.chat_message_histories.in_memory import ChatMessageHistory


def launch_agent(agent: AutoGPT):
    human_icon = "\U0001F468"
    ai_icon = "\U0001F916"
    chat_history = ChatMessageHistory()

    while True:
        task = input(f"{ai_icon}：有什么可以帮您？\n{human_icon}：")
        if task.strip().lower() == "quit":
            break
        reply = agent.run(task, chat_history, verbose=True)
        print(f"{ai_icon}：{reply}\n")


def main():

    # 语言模型
    llm = ChatOpenAI(
        model="gpt-4-turbo",
        temperature=0,
        model_kwargs={
            "seed": 42
        },
    )

    # 自定义工具集
    tools = [
        document_qa_tool,
        document_generation_tool,
        email_tool,
        excel_inspection_tool,
        directory_inspection_tool,
        finish_placeholder,
        ExcelAnalyser(
            prompt_file="./prompts/tools/excel_analyser.txt",
            verbose=True
        ).as_tool()
    ]

    # 定义智能体
    agent = AutoGPT(
        llm=llm,
        tools=tools,
        work_dir="./data",
        main_prompt_file="./prompts/main/main.txt",
        max_thought_steps=20,
    )

    # 运行智能体
    launch_agent(agent)


if __name__ == "__main__":
    main()
