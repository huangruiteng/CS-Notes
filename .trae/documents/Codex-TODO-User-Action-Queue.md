# Codex TODO User Action Queue

> 更新时间：2026-05-08
> 用途：当 `推进TODO` 发现没有 Codex 可独立推进的 active TODO 时，本文件作为用户动作队列入口。这里不替代 `.trae/todos/todos.json`，只作为 `推进TODO` 的阻塞面板，把用户下一步压缩成可执行、可复制、可回填的动作卡片。

## 当前队列

### 1. OpenViking session / Agent Harness trajectory 边界确认

- TODO：`todo-20260504-012`
- 状态：等待用户向 OpenViking 同学确认。
- 完整沟通包：[OpenViking-Session-Trajectory-Alignment.md](./OpenViking-Session-Trajectory-Alignment.md)
- 公开参考：[OpenViking Session 文档](https://github.com/volcengine/OpenViking/blob/main/docs/zh/concepts/08-session.md)

#### 30 秒可复制版本

```text
我想确认一下 OpenViking session 能否作为一次 agent task run / episode 的 coarse trajectory 容器：把 task instruction / observation / response 写成 messages，把 tool call 写成 ToolPart，把 memory / resource / skill 注入写成 ContextPart 或 used()，任务结束后 commit() 形成 archive / overview / memory extraction。这个用法是否推荐？

如果要支持 replay / eval，step_id、env state、tool correctness、DB diff、reward / evaluator delta、memory exposure id、paired replay branch 这些细粒度字段，你们建议扩展进 OpenViking session schema，还是由外部 Agent Harness 保存，只通过 session_id / context_uri / memory_exposure_id 对齐？

另外想确认：当前公开实现里 memory / resource / skill 更像统一 context collection + context type / URI routing，这是否是长期方向？used(contexts, skill) 是否适合作为真实 exposure / usage 日志，并参与后续 priority / lifecycle / memory extraction？
```

#### 需要带回给 Codex 的回复格式

```text
OV 回复摘要：
1. session-as-trajectory 是否推荐：
2. 细粒度 replay/eval 字段归属：
3. memory/resource/skill 是否长期统一 context collection：
4. used(contexts, skill) 是否可作为 exposure / usage 日志：
5. 他们建议的稳定 API / CLI / schema：
6. 其他注意事项：
```

#### 回复后的 Codex 分支动作

- 如果推荐 session-as-trajectory：新增 `OpenViking session bridge adapter` TODO，验收为一条 run 同时能追溯 OpenViking session archive 与 Agent Harness step-level trace。
- 如果不推荐：新增 `external trace + OpenViking context-uri join` TODO，OpenViking 只负责 context database / session summary archive。
- 如果边界仍不清楚：把问题继续收敛成最小 integration gate，不进入大规模实现。

## 空队列规则

如果只剩本文件里的用户动作，`推进TODO` 不应永久卡住。Codex 可以提醒用户动作，同时继续从流程优化、机制优化、效率优化、素材探索能力、笔记重构、脚本/skill 改进、索引治理或最近 completed TODO 中找一个安全小切口。

如果本文件也没有待用户动作，`推进TODO` 更不应硬编历史任务。按顺序检查：

1. 最近 completed TODO 是否有可沉淀的流程规则或脚本。
2. 素材探索机制本身是否需要优化：trusted sources、读取工具、候选库治理、Unread/fallback 规则；不要默认消费具体材料队列。
3. 是否有新材料、项目状态或用户反馈触发新的 Codex-owned TODO。
4. 没有明确小切口时，直接回复“当前 TODO 队列为空”，不制造伪进展。
