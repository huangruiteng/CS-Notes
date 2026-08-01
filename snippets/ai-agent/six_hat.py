hats = {
    "蓝色": "思考过程的控制和组织者。你负责会议的组织、思考过程的概览和总结。"
    + "首先，整个讨论从你开场，你只陈述问题不表达观点。最后，再由你对整个讨论做简短的总结并给出最终方案。",
    "白色": "负责提供客观事实和数据。你需要关注可获得的信息、需要的信息以及如何获取那些还未获得的信息。"
    + "思考“我们有哪些数据？我们还需要哪些信息？”等问题，并提供客观答案。",
    "红色": "代表直觉、情感和直觉反应。不需要解释和辩解你的情感或直觉。"
    + "这是表达未经过滤的情绪和感受的时刻。",
    "黑色": "代表谨慎和批判性思维。你需要指出提案的弱点、风险以及为什么某些事情可能无法按计划进行。"
    + "这不是消极思考，而是为了发现潜在的问题。",
    "黄色": "代表乐观和积极性。你需要探讨提案的价值、好处和可行性。这是寻找和讨论提案中正面方面的时候。",
    "绿色": "代表创造性思维和新想法。鼓励发散思维、提出新的观点、解决方案和创意。这是打破常规和探索新可能性的时候。",
}
queue = ["蓝色", "白色", "红色", "黑色", "黄色", "绿色", "蓝色"]

from openai import OpenAI, AssistantEventHandler
import os
from typing_extensions import override
import json

from dotenv import load_dotenv, find_dotenv
_ = load_dotenv(find_dotenv())

# 初始化 OpenAI 服务
client = OpenAI()

available_functions = {}

class EventHandler(AssistantEventHandler):
    @override
    def on_text_created(self, text) -> None:
        """响应回复创建事件"""
        print(f"\nassistant > ", end="", flush=True)

    @override
    def on_text_delta(self, delta, snapshot):
        """响应输出生成的流片段"""
        print(delta.value, end="", flush=True)

    @override
    def on_tool_call_created(self, tool_call):
        """响应工具调用"""
        print(f"\nassistant > {tool_call.type}\n", flush=True)

    @override
    def on_tool_call_delta(self, delta, snapshot):
        """响应工具调用的流片段"""
        if delta.type == 'code_interpreter':
            if delta.code_interpreter.input:
                print(delta.code_interpreter.input, end="", flush=True)
            if delta.code_interpreter.outputs:
                print(f"\n\noutput >", flush=True)
                for output in delta.code_interpreter.outputs:
                    if output.type == "logs":
                        print(f"\n{output.logs}", flush=True)

    @override
    def on_event(self, event):
        """
        响应 'requires_action' 事件
        """
        if event.event == 'thread.run.requires_action':
            run_id = event.data.id  # 获取 run ID
            self.handle_requires_action(event.data, run_id)

    def handle_requires_action(self, data, run_id):
        tool_outputs = []

        for tool in data.required_action.submit_tool_outputs.tool_calls:
            arguments = json.loads(tool.function.arguments)
            print(
                f"{tool.function.name}({arguments})",
                flush=True
            )
            # 运行 function
            tool_outputs.append({
                "tool_call_id": tool.id,
                "output": available_functions[tool.function.name](
                    **arguments
                )}
            )

        # 提交 function 的结果，并继续运行 run
        self.submit_tool_outputs(tool_outputs, run_id)

    def submit_tool_outputs(self, tool_outputs, run_id):
        """提交function结果，并继续流"""
        with client.beta.threads.runs.submit_tool_outputs_stream(
            thread_id=self.current_run.thread_id,
            run_id=self.current_run.id,
            tool_outputs=tool_outputs,
            event_handler=EventHandler(),
        ) as stream:
            stream.until_done()

existing_assistants = {}

def create_assistant(color):
    if color in existing_assistants:
        return existing_assistants[color]
    assistant = client.beta.assistants.create(
        name=f"{color}帽子角色",
        instructions=f"我们在进行一场Six Thinking Hats讨论。按{queue}顺序。你的角色是{color}帽子。",
        model="gpt-4o",
    )
    existing_assistants[color] = assistant
    return assistant
  
# 创建 thread
thread = client.beta.threads.create()

topic = "如果穿越到了中国古代（明朝）成为了乞丐，如何利用现代知识一步步生存下来，并成为时代风云人物"

# 添加 user message
message = client.beta.threads.messages.create(
    thread_id=thread.id,
    role="user",
    content=f"讨论话题：{topic}\n\n[开始]\n",
)

for hat in queue:
    assistant = create_assistant(hat)
    with client.beta.threads.runs.stream(
        thread_id=thread.id,
        assistant_id=assistant.id,
        event_handler=EventHandler(),
    ) as stream:
        stream.until_done()
    print()
    
# 清理实验环境
for _, assistant in existing_assistants.items():
    client.beta.assistants.delete(assistant.id)