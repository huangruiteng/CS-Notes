# Fine-Mem → Agent Harness / OpenViking 设计准备

> 用途：在用户精读 Fine-Mem 前，先分析如何把 schema 和 attribution 逻辑落到 Agent Harness / OpenViking 设计上，这样当用户精读后，就可以更快地推进。

## 一句话判断

Fine-Mem 最值得读的点不是“又一个 memory 方法”，而是它把 long-horizon agent 的最终成败拆回到细粒度 memory operation：哪次 read/write/update 被证据支持，哪次只是噪声，哪次造成后续 regression。对 Agent Harness 来说，它直接决定 memory_ranking_dataset_v0 不能只存 task-level pass/fail，而要存 step-level evidence、operation type 和 attribution。

## 对 Agent Harness 的直接改造建议（预分析）

### 1. 给 memory_ranking_dataset_v0 增加字段

建议给 memory_ranking_dataset_v0 增加这些字段：

```text
trigger_event_id
phase
memory_operation_type
memory_id
memory_type
retrieval_query
used_as_evidence
evidence_span_ref
tool_call_changed
db_state_changed
final_answer_changed
step_reward
attribution_weight
final_outcome_delta
regression_source
raw_trace_ref
```

### 2. 改变 replay summary 的格式

建议把 replay summary 从“有没有召回 memory”改成：

```text
retrieved -> injected -> cited/followed -> changed_action -> changed_state -> changed_outcome
```

### 3. 先实现 fine_grained_memory_feedback_v0

Agent Harness 的下一步不应是直接训练 RL policy，而是先实现 fine_grained_memory_feedback_v0：

1. 从 tau2 / OpenViking trace 中抽 memory-trigger event。
2. 对每个 event 记录 operation type 和证据锚点。
3. 如果有 paired replay，则计算 with-memory vs suppressed-memory delta。
4. 如果没有 paired replay，则先用 tool correctness、DB diff、final answer evidence 和 regression tag 做弱归因。
5. 输出可用于 ranker / write gate / update gate 的训练行。

## 对 OpenViking 的影响（预分析）

如果 OpenViking session 被用作 coarse trajectory container：

- OpenViking 负责上下文数据库和长期记忆生命周期。
- Agent Harness 负责实验、反事实回放和弱监督标签生成。
- 两边通过 session_id、context_uri、memory_exposure_id 对齐。

如果 OpenViking 不推荐 session-as-trajectory：

- OpenViking 只做 context database + session summary archive。
- Agent Harness 完整保留 trajectory。
- 二者通过 context URI 和 memory item id 对齐。

## 下一步（用户精读后）

1. 执行“读完 Fine-Mem”流程模板。
2. 根据 Fine-Mem 的实际内容，调整上述预分析。
3. 生成给 Agent Harness 主控的 steering 文档。
4. 如果需要，新增 Agent Harness / OpenViking integration TODO。
