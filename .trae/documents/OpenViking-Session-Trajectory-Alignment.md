# OpenViking Session / Agent Harness Trajectory Alignment

> 用途：推进 `todo-20260504-012`，给用户和 OpenViking 同学沟通 session 是否适合承载一次 agent task trajectory。本文只基于 OpenViking 公开文档、开源代码观察和 CS-Notes 公开笔记整理，不包含内部文档链接。

## 一句话判断

OpenViking session 适合做一次 agent task run 的 coarse trajectory container：记录 task instruction、observation、assistant response、tool call、context / skill usage，并在 `commit()` 后归档与抽取长期记忆。但它不应替代 Agent Harness 的 step-level trace / replay / eval schema；后者仍要独立保存 memory exposure、DB diff、tool correctness、paired replay branch 和 evaluator delta。

## 建议边界

| 层级 | 推荐 owner | 内容 |
|---|---|---|
| Coarse session archive | OpenViking | task instruction、user / assistant messages、ToolPart、ContextPart、used contexts / skills、commit archive、summary、memory extraction |
| Fine-grained eval trace | Agent Harness | step_id、env_state、tool correctness、DB diff、memory_exposure_id、retrieval_query、query_intent、trigger_state、paired replay branch、reward / evaluator delta、token / latency cost |
| Cross-system join key | Both | `session_id`、`context_uri`、`memory_exposure_id`、`trace_run_id` |

这个边界的好处是：OpenViking 负责上下文数据库和长期记忆生命周期，Agent Harness 负责实验、反事实回放和弱监督标签生成。两边不会互相吞掉对方的核心价值。

## 建议询问 OpenViking 同学的问题

1. 是否推荐把一次 agent task run / episode 映射成一个 OpenViking session？
2. 如果采用这个映射，task instruction / observation / response 写成 messages，tool call 写成 `ToolPart`，memory / resource / skill 注入写成 `ContextPart` 或 `used()`，任务结束后 `commit()`，这个用法是否符合 OpenViking session 的长期设计？
3. 对 replay / eval 必需的细粒度字段，例如 `step_id`、环境状态、tool correctness、DB diff、reward / evaluator delta、memory exposure id、paired replay branch，OpenViking 是否建议原生支持，还是由外部 harness 保存，只用 `session_id` / `context_uri` 对齐？
4. 当前公开实现中，memory / resource / skill 更像统一 context collection + context type / URI routing。这个方向是否是长期设计，还是未来会拆成独立 collection / index？
5. `used(contexts, skill)` 是否适合作为实际 memory / skill exposure 日志？这些 usage 未来是否会进入优先级、生命周期、summary 或 memory extraction？
6. 如果外部系统要读取 session commit 后抽取出的具体 memory content，推荐使用哪组公开 API / CLI？是否有比直接读内部存储更稳定的方式？

## 可直接发给 OV 同学的话

我想确认一下 OpenViking session 能否作为一次 agent task run 的 trajectory 容器：把 task instruction / observation / response 写成 messages，把 tool call 写成 `ToolPart`，把 memory / resource / skill 注入写成 `ContextPart` 或 `used()`，任务结束后 `commit()` 形成 archive / overview / memory extraction。这个用法是否推荐？

如果要支持 replay / eval，`step_id`、env state、tool correctness、DB diff、reward / evaluator delta、memory exposure id、paired replay branch 这些细粒度字段，你们建议扩展进 OpenViking session schema，还是由外部 Agent Harness 保存，只通过 `session_id` / `context_uri` / `memory_exposure_id` 对齐？

另外想确认一下：当前公开实现里 memory / resource / skill 更像统一 context collection + context type / URI routing，这是否是长期方向？`used(contexts, skill)` 是否适合作为真实 exposure / usage 日志，并参与后续 priority / lifecycle / memory extraction？

## 给 Agent Harness 主控的转发稿

Steering: OpenViking session 可以优先当作 coarse task-run archive，而不要把它误当成完整 replay substrate。建议 Agent Harness 继续自己持有 step-level trace / replay / eval schema，只在 OpenViking 侧写入 session archive、context URI、used contexts / skills、commit summary / memory extraction。

建议新增一个最小 integration gate：一条 tau2 run 写入一个 OpenViking session，同时 Agent Harness trace 里写入 `session_id`、`context_uri`、`memory_exposure_id`、`retrieval_query`、`query_intent`、`trigger_state` 和 evaluator delta。验收标准不是大规模效果提升，而是能从同一条 run 同时追溯：

- OpenViking 里归档了哪些 messages / tool parts / context usage；
- Agent Harness 里哪个 step 注入了哪些 memory；
- paired replay / suppressed retrieval branch 如何影响 tool correctness、DB diff、interaction efficiency 和 task outcome。

如果 OV 同学确认 session-as-trajectory 不推荐，则退一步：OpenViking 只做 context database + session summary archive，Agent Harness 完整保留 trajectory，二者通过 context URI 和 memory item id 对齐。

## 后续动作

1. 用户把上面的 OV 同学问题发出，并把回复贴回 Codex。
2. Codex 根据回复更新 `todo-20260504-012`：
   - 若推荐 session-as-trajectory：新增 Agent Harness / OpenViking session bridge adapter TODO。
   - 若不推荐：新增 external-trace + OpenViking-context-uri join TODO。
3. 再决定是否推动 agent-harness 主控实现最小 integration gate。

## 公开参考

- [OpenViking Session 文档](https://github.com/volcengine/OpenViking/blob/main/docs/zh/concepts/08-session.md)
- [OpenViking Storage 文档](https://github.com/volcengine/OpenViking/blob/main/docs/zh/concepts/05-storage.md)
- [OpenViking Retrieval 文档](https://github.com/volcengine/OpenViking/blob/main/docs/zh/concepts/07-retrieval.md)
- [CS-Notes OpenViking 公开笔记](../../Notes/AI-Agent-Product&PE.md)
