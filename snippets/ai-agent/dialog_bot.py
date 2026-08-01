from openai import OpenAI, AssistantEventHandler
import os, json
from typing_extensions import override
import json
import logging

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
        name=f"AI助手小瓜",
        instructions=f"你是AI助手小瓜，是一位精通 政治学、文学、哲学、社会学、数学、计算机原理、C++、Python、AI、TensorFlow、Pytorch、推荐系统和算法 等领域的专家",
        model="gpt-4o",
    )
    existing_assistants[color] = assistant
    return assistant
  
FILENAME = '/Users/bytedance/variables.json'

thread_id = None
assistant_id = None
  
if not os.path.exists(FILENAME):
  thread = client.beta.threads.create()
  assistant = create_assistant('black')
  thread_id = thread.id
  assistant_id = assistant.id
  data = {
        'thread_id': thread_id,
        'assistant_id': assistant_id
  }
  with open(FILENAME, 'w') as file:
    json.dump(data, file)
    print(f"{FILENAME} file created and variables stored.")
    
else:
  with open(FILENAME, 'r') as file:
    data = json.load(file)
    thread_id = data['thread_id']
    assistant_id = data['assistant_id']
  print(f"Variables loaded from {FILENAME}.")

print(f"thread_id: {thread_id}, assistant_id: {assistant_id}")

topic = """
# 需求

详细解释一下top-k Hit Ratio (HR@k), top-k Normalized Discounted Cumulative Gain (NDCG@k)

# Output Format

* 最好给出关键示例
* 侧重讲解核心原理
* 以自然且类似人类的方式回答问题5.确保你的回答无偏见，不依赖于刻板印象
"""



# 添加 user message
message = client.beta.threads.messages.create(
    thread_id=thread_id,
    role="user",
    content=f"{topic}",
)

with client.beta.threads.runs.stream(
    thread_id=thread_id,
    assistant_id=assistant_id,
    event_handler=EventHandler(),
) as stream:
    stream.until_done()
print()
    
# 清理实验环境
# for _, assistant in existing_assistants.items():
#     client.beta.assistants.delete(assistant.id)