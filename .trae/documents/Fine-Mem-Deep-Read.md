# Fine-Mem Deep Read

> 来源：[Fine-Mem: Fine-Grained Feedback Alignment for Long-Horizon Memory Management](https://arxiv.org/abs/2601.08435)。提交时间：2026-01-13。读取路径：已读取 arXiv abstract、PDF 正文与 TeX source；HTML experimental 链接存在，但本次浏览器打开不稳定，因此以 PDF / TeX source 为主。PDF 与 TeX source 缓存在 `.local/paper-cache/`。

## 一句话判断

Fine-Mem 真正解决的是 memory manager 的 credit assignment：长程任务最后答对/答错，不足以告诉系统哪一步 INSERT / UPDATE / DELETE / SKIP 有价值。它的可迁移价值不是“照着训 GRPO”，而是把 Agent Harness 的 `memory_feedback_event_v0` 从 outcome log 推成 step-level evidence attribution log。

对当前 Agent Harness，最重要的结论是：

```text
不要把一次 memory 命中直接记为 useful。
要记录：它来自哪个 source step、是否被下游 query 检索、是否支撑正确回答、是否改善 paired replay outcome、是否带来 token / regression 成本。
```

## 用户读后判断

用户 2026-05-07 读完后的核心判断是：Fine-Mem 更侧重 **memory 如何更新**，把输入与生成端到端一次搞定；Agent Harness 更关注专用模型 / 规则如何判断哪些 experience 应该进入 memory，并把 source-to-corpus lifecycle 与 corpus-to-context exposure funnel 拆得更细。

这意味着 Fine-Mem 对 Agent Harness 的价值主要是 schema / attribution 方法线索，而不是 procedure-memory benchmark 背书。Memalpha 和 MemoryAgentBench 更偏 user / conversation memory、conversation chunks、QA / 分类 / 摘要包装任务；它们能说明 memory update training 有价值，但不能直接说明 procedure memory 会改善工具调用、DB/action outcome 或 OpenViking worker 行为。

后续状态：本材料已归档到 `.local/LEARNING_MATERIAL_ARCHIVE.md`，公开长期笔记落在 `Notes/AI-Applied-Algorithms.md` 的 `Fine-Mem：memory update 的 step-level credit assignment`。候选库中不再保留 S18 待读条目。

## 核心机制

### 1. Memory management 被建成流式顺序决策

作者把输入表示成 chunk stream：

```text
C = {c1, c2, ..., cT}
```

Memory Manager 在每个 step 看到当前 chunk 和旧 memory state，输出一组 memory operations：

```text
Pt ~ pi_theta(. | ct, M_{t-1})
Mt = T(M_{t-1}, Pt)
```

最终 Reasoning Agent 面对 query 时，从最终 memory state `MT` 里检索 memory item，再生成答案。

你应该这样理解：Fine-Mem 不是研究“RAG 检索器怎么更强”，而是研究“历史信息进入 durable memory 的生命周期动作怎么训练”。这和 Agent Harness 当前的 S17/S19 很贴：我们的问题已经不是有无 memory backend，而是每次 exposure / write / category / rerank / lifecycle action 如何归因。

### 2. 操作空间很窄，但足够暴露 lifecycle 问题

论文只用单层 memory architecture，每个 memory item 是：

```text
{id, content, step}
```

Memory Manager 的 action space 是：

```text
INSERT
UPDATE
DELETE
SKIP
```

这很朴素，但恰好对 Agent Harness 有启发：V0 不应先追复杂 memory graph / multi-layer hierarchy。先保证每条 memory 有稳定 `source_step_id` / `experience_key`，并能追踪它后来是否被 retrieve / inject / follow / cause delta。

迁移到我们的 schema 时，不应该把所有细分动作都变成 V0 action space。更合理的做法是把它们分成两层：

```text
V0 决策动作：
  upsert / skip / retire

V0 观测事件：
  retrieved / filtered_or_deduped / injected / followed_or_cited / outcome_delta
```

也就是说，`admit / rewrite` 可以先合并成 `upsert`，通过 `memory_version` 和 `source_step_id` 区分新增还是改写；`bury / delete` 可以先合并成 `retire`，通过 `retire_reason` 和 `retire_mode = soft | hard` 区分降权、隐藏还是硬删除；`keep` 对应 `skip` 或无状态变更。

`retrieve / filter / dedupe / inject / cite_or_follow` 不必作为初版 policy action。它们更适合做 exposure funnel 的日志字段：系统有没有召回、为什么没注入、是否去重、是否真的进入 context、后续 action 是否跟随它。Fine-Mem 的论文动作主要在 source-to-corpus lifecycle；Agent Harness 必须补 corpus-to-context exposure，但可以先用日志和离线归因实现，不必一开始训练一个复杂多动作策略。

### 3. Chunk-level Step Reward 是局部保真度，不是最终价值

CSR 的做法：

1. 对每个 chunk 用 GPT-4o-mini 生成 factoid QA。
2. 用 Qwen3-32B verifier 只看该 chunk 回答。
3. 不能由 chunk 支撑的 QA 丢弃。
4. 去重后每个 chunk 保留 5 个 QA。
5. 训练时用 `Mt` 回答当前 chunk QA，得到 step-level reward。

这解决的是 reward sparsity：如果某一步把 chunk 中关键事实丢了，不必等最终任务失败才知道。

但它也有边界：CSR 容易奖励“保留更多局部事实”。论文 ablation 也显示，只加 CSR 会提高性能但 memory length 变长。对 Agent Harness 来说，CSR 不能直接等价为“多写 memory 就好”；它更像 `source_quality_gate` 的弱监督：

```text
当前 chunk / trace 里哪些事实值得进入 candidate memory？
这条 memory 是否保留了可验证事实？
```

### 4. EARA 的关键是 memory item -> source step 的反向映射

EARA 的核心变量：

```text
sj: 第 j 个 global QA 的得分
Mj: 回答第 j 个 global QA 时检索到的 memory item 集合
phi(m): memory item m 来自哪个 update step
```

它先计算某个 step 的 Normalized Evidence Contribution：

```text
Nt = sum_j sum_{m in Mj and phi(m)=t} sj / (|Mj| * n)
```

再把全局 reward 重新分配到每个 step：

```text
r_EARA(t) = (1 - beta) * r_global / T + beta * Nt
```

这里最有用的不是公式本身，而是三个设计约束：

- 必须能从 memory item 追到 source step。
- 下游 query 的 reward 只分给被检索为 evidence 的 memory item。
- 不能让 evidence attribution 过强，仍保留 uniform participation credit。

论文里 `beta = 0.5` 最好；过高会让 reward 集中到少数 step，OOD 泛化变差。迁移到 Agent Harness，就是不要把一两次正向 replay delta 直接升成 durable lifecycle 决策；要保留不确定性、聚合证据和最低样本数。

### 5. CSR 和 EARA 是互补，不是替代

论文的 ablation 很清楚：

```text
OR-only: avg perf 0.627, avg len 92.4K
w/ CSR: avg perf 0.639, avg len 86.2K
w/ EARA: avg perf 0.622, avg len 60.7K
Fine-Mem: avg perf 0.663, avg len 79.1K
```

解释：

- CSR 让系统更愿意保留局部信息，提升信息保真，但可能过度记忆。
- EARA 让系统更关注对下游任务有 evidence contribution 的 memory，压缩更强，但单独使用会太稀疏。
- 合起来才是“保留局部可验证事实 + 对下游有用的事实更高权重”。

对 Agent Harness 的迁移是双通道 reward：

```text
source_quality_reward:
  这条 memory 是否忠实保留了 source trace / chunk 的关键事实？

post_exposure_utility_reward:
  它被检索/注入后，是否改善目标任务 outcome / DB / action / grounding？
```

只做前者会变成知识库堆料；只做后者会稀疏且容易误归因。

### 6. 论文的实验强点和可疑点都要记住

强点：

- 在 Memalpha 和 MemoryAgentBench 都超过七个 baseline。
- MemoryAgentBench 是 OOD，更长上下文、更复杂。
- 覆盖 Accurate Retrieval、Test-Time Learning、Long-Range Understanding。
- 对 Qwen3-4B、Qwen3-1.7B、Llama3.2-3B 都有增益。

可疑点 / 边界：

- 检索使用 BM25，Reasoning Agent 固定为 Qwen3-32B / GPT-4o-mini 等强模型，系统收益不一定来自 manager policy 本身。
- CSR 依赖 LLM 生成与 verifier，存在 teacher / verifier bias。
- EARA 把 query score 均分给 retrieved memory item，不能识别“被检索但没真正用上”的 item。
- `phi(m)=step` 对 INSERT 很自然，但对 UPDATE / DELETE 的归因会更复杂；更新后的 memory 是归因给原始 step、update step，还是两者共享，论文处理得比较粗。
- 它没有解决 retrieval policy 的 should-retrieve 问题；这要和 ProactAgent 的 paired branch 思路合并。

## 对 Agent Harness 的直接改造

### 1. `memory_feedback_event_v0` 增加 Fine-Mem 字段组

建议新增或检查这些字段：

```text
source_step_id
source_chunk_ref
source_trace_ref
memory_operation_type
operation_set_id
operation_valid
memory_state_before_ref
memory_state_after_ref

local_fact_qa_count
local_fact_qa_pass_count
source_quality_reward
source_quality_boundary

global_query_id
retrieved_for_global_query
retrieved_memory_set_size
reasoning_answer_score
normalized_evidence_contribution

uniform_participation_credit
evidence_credit
attribution_weight
step_reward

paired_baseline_run_id
post_exposure_reward_delta
db_state_delta
tool_action_delta
argument_grounding_delta
regression_source
```

其中 `local_fact_qa_*` 不一定要真的生成 QA，可以先用更工程化的替代：

```text
source_quality_reward =
  official source task reward
  + DB/action diagnostic
  + stop reason
  + trace consistency
  + memory rewrite quality judge
```

### 2. 把 event 拆成两层，避免混淆

Fine-Mem 论文里 memory operation 和 downstream retrieval 比较紧耦合。Agent Harness 最好拆开，但拆开不等于把每个环节都升成 action：

```text
memory_source_event_v0:
  trace/chunk -> candidate memory -> upsert/skip/retire

memory_exposure_event_v0:
  query/trigger -> retrieved -> injected/not_injected(reason) -> followed_or_cited -> outcome delta
```

初版最小闭环可以只有：

```text
source_step_id
experience_key
memory_id
memory_version
lifecycle_action = upsert | skip | retire
retrieved = true | false
injected = true | false
followed_or_cited = true | false
outcome_delta
```

`filter`、`dedupe`、`bury`、`delete`、`cite_or_follow` 这些名字仍然有用，但先作为 reason / mode / derived label，而不是顶层 action。否则 V0 的样本、标注、报表都会被动作枚举拖复杂。

如果暂时只保留一个 `memory_feedback_event_v0`，也要在字段里显式区分 `event_phase`：

```text
source_construction
retrieval_matching
context_injection
post_exposure_outcome
lifecycle_aggregation
```

### 3. `memory_ranking_dataset_v0` 不只做 ranker，要能训练四个模块

Fine-Mem 读完后，`memory_ranking_dataset_v0` 的目标应扩展成：

```text
should_admit_memory:
  source_quality_reward, local_fact_support, rewrite_needed

should_retrieve:
  trigger_state, query_intent, phase, previous_failure_signal

should_inject / rerank:
  normalized_evidence_contribution, category match, precondition match, token cost

should_promote_or_bury:
  post_exposure_reward_delta, regression_count, repeated exposure utility
```

这比“候选 memory 排序”更接近完整 memory lifecycle。

### 4. 不要现在训 GRPO，先做 offline attribution

Fine-Mem 用 GRPO 是论文训练方案，但 Agent Harness 当前最需要的是数据和 evaluator：

```text
V0:
  same-prefix paired replay
  suppressed retrieval branch
  event-level outcome delta
  attribution fields

V1:
  rule / logistic / GBDT ranker
  source_quality + exposure_utility feature ablation

V2:
  contextual bandit / OPE
  retrieval action and lifecycle action

V3:
  RL runner bridge / GRPO-style training
```

## Benchmark 边界：Memalpha / MemoryAgentBench 偏什么 memory

结论：这两个 benchmark 都不等价于 Agent Harness 当前最关心的 procedure / tool-use / DB-state memory。它们更像“用户对话式长期信息记忆 + 长上下文信息管理”的 benchmark。

### MemoryAgentBench：明显偏 user / conversation memory

MemoryAgentBench 的论文和数据卡都说，它把 long-context 数据改造成 incremental multi-turn interaction，模拟信息逐渐进入 agent memory 的过程。官方定义的四类能力是：

```text
Accurate Retrieval
Test-Time Learning
Long-Range Understanding
Selective Forgetting / Conflict Resolution
```

它的数据形态有很强的用户对话感：

- 输入被包装成 User / Assistant dialogue。
- prompt 会显式要求 agent 记住用户给出的内容。
- Accurate Retrieval 包括 RULER / LongMemEval 等长对话或长文 QA。
- TTL 包括分类规则学习和 movie recommendation，对话中给 examples，再问后续问题。
- LRU 包括小说/长文本的全局理解。
- SF / CR 关注事实变化、用户状态变化、冲突信息覆盖。

所以它不是单纯 user profile benchmark，但确实更靠近“用户持续聊天、偏好/事实/故事/规则逐步进入记忆”的场景。它缺的是 agent 执行轨迹里的 tool correctness、DB state、procedure precondition、action outcome attribution。

### Memalpha：训练框架偏 memory construction，但数据仍偏信息保留

Memalpha 不是 benchmark 名字那么单一，它是一个 RL memory construction framework，并自建训练/验证数据。它的 memory architecture 明确有：

```text
core memory
episodic memory
semantic memory
```

其中 core memory 被定义为用户基本事实、偏好、角色、目标；episodic memory 记录带时间戳的用户/助手动作；semantic memory 记录更一般的知识。这个设计非常像 agent/user memory system。

但 Memalpha 的训练/验证数据来源是混合的：

```text
AR: SQuAD, HotpotQA, PerLTQA, LME-Train
TTL: PubMed-RCT, NLU, TREC-Coarse
LRU: BookSum
```

也就是说，它把 QA、分类、书籍摘要等任务改造成“conversation chunks”，让 memory manager 学会在流式输入中构建 memory。它更像“信息流 -> memory construction -> answer/eval”的训练环境，不是专门测 agent 在环境里执行 tool/procedure 的 memory。

### 对 Fine-Mem 结论的影响

Fine-Mem 在 Memalpha / MemoryAgentBench 上提升，能支持这些 claim：

```text
fine-grained reward helps memory construction
source step attribution helps long-horizon information retention
CSR + EARA can improve AR / TTL / LRU-style memory tasks
```

但不能直接支持这些更强 claim：

```text
它已经证明 procedure memory 能改善 tool-use agent outcome
它已经解决 DB/action/state 的 causal attribution
它能直接迁移到 tau2 / OpenViking 的 same-prefix paired replay
它能判断 memory 是否改变了 planner action 或 write tool behavior
```

因此 Agent Harness 应把它当成 schema / attribution 方法线索，而不是 benchmark 充分背书。真正要证明 procedure memory，仍需要自己的 evaluation：

```text
same-prefix paired replay
DB/action/tool correctness delta
procedure precondition match
memory exposure -> action change -> state change -> outcome change
```

## 读原文时要特别核验的点

1. CSR 生成的 chunk QA 是否和目标任务同分布？如果 chunk QA 只测 factoid retention，迁移到 tau2 procedure memory 时要补 action / DB / precondition QA。
2. EARA 是否只看 retrieved memory item，而不看 final answer 中是否真的引用或遵循它？如果是，Agent Harness 要补 `used_or_cited / changed_action / changed_state`。
3. UPDATE / DELETE 的 source attribution 是否可靠？如果不可靠，Agent Harness 要记录 `memory_state_before_ref` 和 `memory_state_after_ref`。
4. Compression reward 是否会惩罚必要长 memory？迁移时不能只用 token length，要用 `token_cost - utility_delta`。
5. OOD 提升主要来自 AR 还是 TTL？论文结果显示 MemoryAgentBench 上 AR / TTL 都有提升，但 LRU 仍弱；不要把它包装成解决所有 long-context memory。

## 阅读路径

这篇不用再从头泛读。后续只回查这些位置：

1. Abstract / Introduction：只抓任务定义和 final reward 为什么不够。
2. Method：重点看 CSR 如何构造 chunk QA，以及 EARA 如何把 global QA reward 分配回 source step。
3. Ablation：重点看 CSR / EARA 单独使用时的性能和 memory length trade-off。
4. Appendix：只查 reward construction、operation schema、chunk QA prompt、GRPO detail。

边读边问四个问题：

1. step reward 来自可观测 evidence，还是来自 LLM judge 弱监督？
2. memory 被检索后，论文是否真的证明它被使用，而不只是出现在 context？
3. read / write / update / delete 是否被同一个 reward 粗暴混在一起？
4. 迁移到 tau2 / OpenViking 时，哪些信号能用 DB diff、tool correctness、paired replay delta 替代 chunk QA？

## Agent Harness 主控转发稿

```text
背景：我精读了 Fine-Mem（arXiv:2601.08435）。它的核心不是又一个 memory benchmark，而是把最终 QA reward 通过 source step 和 retrieved memory item 做 fine-grained attribution。对 Agent Harness，最有价值的是把 memory_feedback_event_v0 从 outcome log 升级成 source-quality + exposure-utility 的 feedback event。

建议动作：
1. 检查 memory item 是否有稳定 source_step_id / source_trace_ref / memory_state_before_after_ref，能从 injected memory 反查到产生或更新它的 step。
2. 把 memory_feedback_event_v0 至少拆出两类字段：source_quality_reward（源轨迹/局部事实/DB-action diagnostic）和 post_exposure_utility_reward（same-prefix paired replay delta）。
3. 初版 action space 先收敛到 `upsert / skip / retire`；`add/rewrite`、`soft bury/hard delete` 用 mode/reason 字段区分，不直接扩成一堆顶层动作。
4. 对每次 retrieval 记录 retrieved / injected / followed_or_cited / changed_action / changed_state；filter、dedupe、not_injected_reason 先作为 exposure funnel 日志。不要把 retrieved 当成 useful。
5. lifecycle 决策不要用单次正负样本直接 promote/delete；至少聚合 normalized_evidence_contribution、reward_delta、regression_count、token_cost。

验收标准：
- 一个 memory item 能完整追踪：source trace -> upsert/skip/retire -> retrieval/injection -> paired outcome delta -> lifecycle hint。
- strict dashboard 只展示 same-seed / same-corpus / same-backend paired replay 的 delta；LLM judge / chunk QA 只作为 weak label 或 diagnostic。
- V0 先产出 dataset / evaluator，不直接上 GRPO。
```

## 精读后结论

S18 已读完归档。它不是最强质量背书的公开论文，而是一个很适合改 schema 的机制论文。后续只在实现 `memory_feedback_event_v0`、`memory_ranking_dataset_v0` 或 Agent Harness steering 时回查四个字段族：

```text
source_step_id / memory_operation_type
source_quality_reward / local_fact_support
normalized_evidence_contribution / attribution_weight
post_exposure_reward_delta / regression_source
```

读完它之后，下一步不是继续堆 memory paper，而是回到 Agent Harness，把 `memory_feedback_event_v0` 和 `memory_ranking_dataset_v0` 的字段草案对齐到 source-quality + exposure-utility 双通道。
