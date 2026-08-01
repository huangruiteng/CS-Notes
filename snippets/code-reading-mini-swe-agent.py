https://github.com/SWE-agent/mini-SWE-agent

SWE-bench/SWE-agent 团队出品, 核心 ~310 行 Python, SWE-bench verified 74%+
设计哲学: 当 LLM 足够强时, agent 框架应做减法而非加法


*** 整体架构: 三层解耦

Model (LLM 接口)  →  Agent (控制流)  →  Environment (执行环境)
     |                    |                    |
  query()              run()/step()         execute()
  format_message()     query()              _check_finished()
  format_observation()  execute_actions()    get_template_vars()

三层通过 Python Protocol (鸭子类型) 解耦, 任何实现了对应方法的对象都可注入


*** 核心循环: DefaultAgent.run() — 整个 agent 就是一个 while True

# src/minisweagent/agents/default.py

class DefaultAgent:
    def run(self, task: str = "", **kwargs) -> dict:
        self.extra_template_vars |= {"task": task, **kwargs}
        self.messages = []
        # 1. 初始化: system prompt + user task → messages
        self.add_messages(
            self.model.format_message(role="system", content=self._render_template(self.config.system_template)),
            self.model.format_message(role="user", content=self._render_template(self.config.instance_template)),
        )
        # 2. 主循环: query → execute → observe → repeat
        while True:
            try:
                self.step()  # = self.execute_actions(self.query())
            except InterruptAgentFlow as e:
                # Submitted / LimitsExceeded / FormatError / UserInterruption
                # 都是 InterruptAgentFlow 的子类, 通过异常控制流跳出正常 step
                self.add_messages(*e.messages)
            except Exception as e:
                self.handle_uncaught_exception(e)
                raise
            finally:
                self.save(self.config.output_path)
            # 3. 退出条件: 最后一条消息 role == "exit"
            if self.messages[-1].get("role") == "exit":
                break
        return self.messages[-1].get("extra", {})

# 关键洞察: 没有状态机、没有规划模块、没有反思循环
# 就是 "问 LLM → 执行命令 → 看结果 → 再问 LLM" 的死循环
# 异常控制流 (InterruptAgentFlow) 是唯一的"跳出"机制


*** step(): 两步走 — query + execute

def step(self) -> list[dict]:
    return self.execute_actions(self.query())

def query(self) -> dict:
    # 1. 检查限制 (step_limit / cost_limit)
    if 0 < self.config.step_limit <= self.n_calls or 0 < self.config.cost_limit <= self.cost:
        raise LimitsExceeded({...})  # 通过异常退出循环
    # 2. 调用 LLM
    self.n_calls += 1
    message = self.model.query(self.messages)  # 核心: 把整个 messages 历史传给 LLM
    self.cost += message.get("extra", {}).get("cost", 0.0)
    self.add_messages(message)
    return message

def execute_actions(self, message: dict) -> list[dict]:
    # 1. 从 LLM 回复中提取 actions
    outputs = [self.env.execute(action) for action in message.get("extra", {}).get("actions", [])]
    # 2. 格式化 observation 并 append 到 messages
    return self.add_messages(*self.model.format_observation_messages(message, outputs, self.get_template_vars()))


*** 异常体系: 用异常控制 Agent 流程

# src/minisweagent/exceptions.py

class InterruptAgentFlow(Exception):
    """所有 agent 流程中断的基类"""
    def __init__(self, *messages: dict):
        self.messages = messages  # 携带要注入 messages 列表的内容

class Submitted(InterruptAgentFlow):
    """任务完成, agent 提交结果"""

class LimitsExceeded(InterruptAgentFlow):
    """超出 step/cost 限制"""

class UserInterruption(InterruptAgentFlow):
    """用户中断"""

class FormatError(InterruptAgentFlow):
    """LLM 输出格式错误"""

# 设计巧妙之处:
# - 所有"非正常 step"都通过异常机制处理, 不污染主循环逻辑
# - 异常携带 messages, 被 run() 的 except 捕获后注入到 messages 列表
# - FormatError 让 LLM 看到格式错误提示, 自动修正 (自修复机制)


*** Environment: 无状态执行 — subprocess.run 替代 shell session

# src/minisweagent/environments/local.py

class LocalEnvironment:
    def execute(self, action: dict, cwd: str = "", *, timeout: int | None = None) -> dict[str, Any]:
        command = action.get("command", "")
        cwd = cwd or self.config.cwd or os.getcwd()
        try:
            # 核心: 每次命令都是独立的子进程, 不维护 shell session
            result = subprocess.run(
                command, shell=True, text=True, cwd=cwd,
                env=os.environ | self.config.env,
                timeout=timeout or self.config.timeout,
                encoding="utf-8", errors="replace",
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            )
            output = {"output": result.stdout, "returncode": result.returncode, "exception_info": ""}
        except Exception as e:
            output = {"output": raw_output, "returncode": -1, "exception_info": f"An error occurred: {e}", ...}
        self._check_finished(output)  # 检查是否提交
        return output

    def _check_finished(self, output: dict):
        # 提交协议: 如果输出第一行是 COMPLETE_TASK_AND_SUBMIT_FINAL_OUTPUT 且 returncode == 0
        # 则 raise Submitted, 通过异常机制退出 agent 循环
        lines = output.get("output", "").lstrip().splitlines(keepends=True)
        if lines and lines[0].strip() == "COMPLETE_TASK_AND_SUBMIT_FINAL_OUTPUT" and output["returncode"] == 0:
            submission = "".join(lines[1:])
            raise Submitted({"role": "exit", "content": submission, "extra": {"exit_status": "Submitted", "submission": submission}})

# 无状态执行的代价与收益:
# - 代价: 环境变量不持久, cd 不持久 (但 prompt 里告诉 LLM 用 VAR=val cd /path && command)
# - 收益: 代码极简, 天然支持沙箱化, 无僵尸进程/状态污染
# - 沙箱化只需换一个 execute() 实现: subprocess.run → docker exec


*** Docker 环境: 与 Local 共享接口, 只换 execute()

# src/minisweagent/environments/docker.py

class DockerEnvironment:
    def execute(self, action: dict, cwd: str = "", *, timeout: int | None = None) -> dict[str, Any]:
        command = action.get("command", "")
        cwd = cwd or self.config.cwd
        # 与 LocalEnvironment 唯一区别: 用 docker exec 替代 subprocess.run
        cmd = [self.config.executable, "exec", "-w", cwd]
        # ... 环境变量转发 ...
        cmd.extend([self.container_id, *self.config.interpreter, command])
        result = subprocess.run(cmd, text=True, timeout=timeout or self.config.timeout, ...)
        # 后续 _check_finished 逻辑完全一致

# Protocol 的威力: Agent 不知道也不关心 Environment 是 local 还是 docker
# 只要实现了 execute() + get_template_vars() + serialize() 就行


*** Model: LitellmModel — 通过 litellm 统一所有 LLM API

# src/minisweagent/models/litellm_model.py

class LitellmModel:
    def query(self, messages: list[dict[str, str]], **kwargs) -> dict:
        # 1. 重试机制 (tenacity)
        for attempt in retry(logger=logger, abort_exceptions=self.abort_exceptions):
            with attempt:
                response = self._query(self._prepare_messages_for_api(messages), **kwargs)
        # 2. 计算成本
        cost_output = self._calculate_cost(response)
        # 3. 解析 actions (tool calls)
        message = response.choices[0].message.model_dump()
        message["extra"] = {
            "actions": self._parse_actions(response),  # 从 tool calls 提取 bash 命令
            "response": response.model_dump(),
            **cost_output,
            "timestamp": time.time(),
        }
        return message

    def _query(self, messages, **kwargs):
        return litellm.completion(
            model=self.config.model_name,
            messages=messages,
            tools=[BASH_TOOL],  # 唯一工具: bash
            **(self.config.model_kwargs | kwargs),
        )


*** Tool 定义: 只有 bash 一个工具

# src/minisweagent/models/utils/actions_toolcall.py

BASH_TOOL = {
    "type": "function",
    "function": {
        "name": "bash",
        "description": "Execute a bash command",
        "parameters": {
            "type": "object",
            "properties": {
                "command": {
                    "type": "string",
                    "description": "The bash command to execute",
                }
            },
            "required": ["command"],
        },
    },
}

# 极简工具设计的核心洞察:
# - bash 是最通用的工具接口, LLM 已经知道如何用 bash 做任何事
# - 不需要 file_editor (用 sed/cat), 不需要 search_tool (用 grep/find)
# - 避免了 agent 框架替 LLM 做工具选择的决策
# - 任何模型都能用, 不需要支持 function calling (还有 text-based 模式)


*** Tool Call 解析: 从 LLM 回复中提取 bash 命令

def parse_toolcall_actions(tool_calls: list, *, format_error_template: str) -> list[dict]:
    if not tool_calls:
        # LLM 没有调用任何工具 → FormatError
        # FormatError 是 InterruptAgentFlow 子类, 会被 run() 捕获
        # 携带的 message 会告诉 LLM "你必须调用 bash tool"
        raise FormatError({...})
    actions = []
    for tool_call in tool_calls:
        args = json.loads(tool_call.function.arguments)
        if tool_call.function.name != "bash":
            raise FormatError({...})  # 未知工具 → FormatError
        if "command" not in args:
            raise FormatError({...})  # 缺少 command 参数 → FormatError
        actions.append({"command": args["command"], "tool_call_id": tool_call.id})
    return actions

# 自修复机制: FormatError → 注入错误提示到 messages → LLM 下次自动修正格式


*** Observation 格式化: 把执行结果渲染回 LLM

def format_toolcall_observation_messages(*, actions, outputs, observation_template, ...) -> list[dict]:
    not_executed = {"output": "", "returncode": -1, "exception_info": "action was not executed"}
    padded_outputs = outputs + [not_executed] * (len(actions) - len(outputs))
    results = []
    for action, output in zip(actions, padded_outputs):
        # observation_template 是 Jinja2 模板, 在 YAML 配置中定义
        content = Template(observation_template, undefined=StrictUndefined).render(output=output, ...)
        msg = {"content": content, "extra": {...}}
        if "tool_call_id" in action:
            msg["tool_call_id"] = action["tool_call_id"]
            msg["role"] = "tool"  # OpenAI tool call 格式
        else:
            msg["role"] = "user"  # 人工输入的命令
        results.append(msg)
    return results


*** Prompt 模板: 策略编码在 prompt 而非代码

# src/minisweagent/config/mini.yaml — 核心配置

agent:
  system_template: |
    You are a helpful assistant that can interact with a computer.
  instance_template: |
    Please solve this issue: {{task}}
    # ... 推荐工作流 (6步) ...
    # ... 命令执行规则 ...
    # ... 提交协议: echo COMPLETE_TASK_AND_SUBMIT_FINAL_OUTPUT ...
    # ... 环境适配: macOS 用 sed -i '' ...
    <system_information>
    {{system}} {{release}} {{version}} {{machine}}  # Jinja2 变量, 从 env.get_template_vars() 注入
    </system_information>

model:
  observation_template: |
    # 输出截断逻辑: <10000 字符完整显示, 否则 head/tail 各 5000
    {%- if output.output | length < 10000 -%}
    {"returncode": {{ output.returncode }}, "output": {{ output.output | tojson }}}
    {%- else -%}
    {"returncode": {{ output.returncode }},
     "output_head": {{ output.output[:5000] | tojson }},
     "output_tail": {{ output.output[-5000:] | tojson }},
     "elided_chars": {{ output.output | length - 10000 }},
     "warning": "Output too long."}
    {%- endif -%}
  format_error_template: |
    # 格式错误时注入的提示, 引导 LLM 修正
    Tool call error: <error>{{error}}</error>
    Every response needs to use the 'bash' tool at least once.

# 策略编码在 prompt 的好处:
# - 修改策略不需要改代码, 只改 YAML
# - LLM 直接理解自然语言指令, 不需要代码解析
# - 输出截断用 Jinja2 模板实现, 不需要专门的 token 管理代码


*** Protocol: 鸭子类型接口定义

# src/minisweagent/__init__.py

class Model(Protocol):
    config: Any
    def query(self, messages: list[dict[str, str]], **kwargs) -> dict: ...
    def format_message(self, **kwargs) -> dict: ...
    def format_observation_messages(self, message, outputs, template_vars=None) -> list[dict]: ...
    def get_template_vars(self, **kwargs) -> dict[str, Any]: ...
    def serialize(self) -> dict: ...

class Environment(Protocol):
    config: Any
    def execute(self, action: dict, cwd: str = "") -> dict[str, Any]: ...
    def get_template_vars(self, **kwargs) -> dict[str, Any]: ...
    def serialize(self) -> dict: ...

class Agent(Protocol):
    config: Any
    def run(self, task: str, **kwargs) -> dict: ...
    def save(self, path: Path | None, *extra_dicts) -> dict: ...

# Protocol = 结构化子类型, 只要实现了这些方法就是合法的 Model/Environment/Agent
# 不需要继承任何基类, 零耦合, 扩展只需写新类


*** 最简使用: hello_world.py — 5 行核心代码

# src/minisweagent/run/hello_world.py

agent = DefaultAgent(
    LitellmModel(model_name=model_name),
    LocalEnvironment(),
    **yaml.safe_load(Path(package_dir / "config" / "default.yaml").read_text())["agent"],
)
agent.run(task)

# 这就是 mini-SWE-agent 的全部: Model + Environment + Config → Agent → run


*** 数据流总结

1. 用户输入 task
2. Agent.run() 渲染 system_template + instance_template → 初始 messages
3. while True:
   a. Agent.query() → Model.query(messages) → LLM API → response
   b. Model 解析 response → 提取 tool calls (bash commands) → message["extra"]["actions"]
   c. Agent.execute_actions() → Environment.execute(action) → output
   d. 如果 output 包含 COMPLETE_TASK_AND_SUBMIT_FINAL_OUTPUT → raise Submitted → 退出
   e. Model.format_observation_messages() → 渲染 observation → append 到 messages
   f. 回到 a
4. 返回 messages[-1]["extra"] (包含 exit_status + submission)


*** 与 SWE-agent v1 的对比

| 维度           | SWE-agent v1          | mini-SWE-agent        |
|---------------|----------------------|-----------------------|
| 代码量         | 数千行               | ~310 行               |
| 工具           | 多种 (file_edit 等)   | 仅 bash               |
| Shell          | 有状态 session       | 无状态 subprocess.run |
| 消息历史       | 有 history processor | 线性 append           |
| 扩展方式       | 继承基类             | Protocol 鸭子类型     |
| 策略编码       | 代码 + prompt        | 纯 prompt (YAML)      |
| SWE-bench      | ~相似                | 74%+ verified         |

核心差异: v1 在 agent 框架层面做更多决策, mini 把决策权交给 LLM
当 LLM 足够强时, 框架越简单, LLM 自由度越高, 性能反而更好
