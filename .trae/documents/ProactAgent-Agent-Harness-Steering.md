# ProactAgent -> Agent Harness Steering

> 来源：[Ask Only When Needed / ProactAgent](https://arxiv.org/abs/2604.20572)。用途：给 agent-harness 主控的技术 steering，可直接转发；不包含私人职业叙事。

## 一句话判断

ProactAgent 把 memory / skill retrieval 从 passive RAG 改写成 policy action：agent 可以在执行中选择环境动作，也可以选择 `RETRIEVE(q)`。这直接影响 Agent Harness 的 memory feedback 设计：日志不能只保存注入了哪些 memory，还要保存 retrieval decision 的触发状态、query 和 intent，否则后续只能训练 memory ranker，训练不了 retrieval policy。

## 建议给 Agent Harness 的增量目标

### P0. 补齐 memory-trigger event 日志字段

对每次 memory 注入 / retrieval 触发，至少记录：

```text
run_id
task_id
domain
step_id
prefix_trace_ref
trigger_state
phase
retrieval_action_taken
retrieval_query
query_intent
candidate_memory_ids
selected_memory_ids
selected_memory_types
retrieval_scores
injected_context_tokens
tool_action_after_injection
```

如果只存 `retrieved_memory_ids`，后续最多能做 rerank；补上这些字段后，才能评估：

- 当前 step 是否应该 recall memory；
- query 是否生成正确；
- 哪类 memory 应该被注入；
- memory 注入后是否改变了工具调用、DB 状态或交互效率。

### P1. 实现 paired replay evaluator v0

对 memory-trigger event 做最小 paired replay：

```text
for a step where memory is injected:
  replay from the same prefix with current retrieval suppressed
  compare with original retrieval branch
  compute deltas:
    task_success_delta
    tool_correctness_delta
    db_state_delta
    interaction_efficiency_delta
    token_cost_delta
```

V0 不需要每个 step 都 replay，也不需要做复杂 step-level policy。先聚焦“发生了 memory injection 的 step”，得到 suppressed-retrieval baseline，即可把现有 tau2 策略优化 eval 先搞稳定。

这一步先服务三个后续弱监督目标：

- `should_retrieve`：当前 step 是否应该 recall memory。
- `retrieval_query_generator`：如果需要 recall，当下 query 应该怎么生成。
- `memory_selector / reranker`：召回后哪些 memory type / item 应该注入。

任务阶段差异不要拆成多套策略。建议把阶段作为事件字段，例如 `planning`、`before_tool_call`、`after_tool_error`、`recovery`、`final_check`。

### P2. 把 ProactAgent 五类 experience schema 映射到 Agent Harness

可先不一次性做满，但 schema 方向应明确：

| ProactAgent entry | Agent Harness 映射 |
|---|---|
| Factual memory | 环境事实、DB/tool 输出、持久状态快照 |
| Episodic memory | 单次任务的局部计划、约束、交互模式 |
| Success skill | 成功轨迹抽象出的 procedure / strategy |
| Failure skill | 失败轨迹抽象出的 anti-pattern / corrective rule |
| Comparative skill | paired replay branch 产生的“为什么 A continuation 优于 B” |

先做 factual / episodic / success / failure；comparative skill 等 paired replay evaluator 稳定后再生成。

## Claim Boundary

- 不建议现在就引入 GRPO 训练；当前优先做 evaluator、日志 schema 和 paired replay 数据。
- ProactAgent 的 priority update 很轻量：被 retrieve 且轨迹成功则 priority +1。Agent Harness 可以先复用这个思想，但最终应升级为 post-exposure utility，而不是单纯 success count。
- Step-level replay 的目的不是把任务所有阶段都复杂化，而是先提供 retrieval event 的 counterfactual label：`should_retrieve`、`query_generator`、`memory_reranker` 三类后续模型都依赖这个 label。
- `phase` 只是 context feature，不是多套策略；V0 先做 evaluator 和日志字段，V1 才考虑 weak label，V2 再考虑 contextual bandit / retrieval policy。

## 可直接转发给主控的话

Steering: ProactAgent / Ask Only When Needed 对 Agent Harness 的直接启发是，memory retrieval 应被视为 policy action，而不是 passive RAG。请在 tau2 / memory feedback 日志里补齐 `retrieval_query`、`query_intent`、`trigger_state`、`phase`、`retrieval_action_taken` 和 `prefix_trace_ref`，否则我们后续只能训练 memory ranker，无法训练 should-retrieve / query-generator / retrieval-policy。

建议先实现一个 `paired_replay_evaluator_v0`：只对发生 memory injection 的 step，从同一 prefix replay 一个 suppress current retrieval 的分支，比较 task success、tool correctness、DB state、interaction efficiency、token cost 的 delta。V0 不需要 replay 每个 step，也不需要马上做 GRPO 或复杂阶段策略；`phase` 只作为 context feature。先把 tau2 的 paired replay eval 做稳定，并把 delta 写回 `memory_feedback_event_v0`。这些 delta 后续服务三个子模块：`should_retrieve`、`retrieval_query_generator`、`memory_reranker`，以及 memory priority / promote / bury 的设计。
