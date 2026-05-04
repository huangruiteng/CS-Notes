# verifiedstate/agent-memory-eval 调研简报

> 来源：https://github.com/verifiedstate/agent-memory-eval  
> 读取状态：已读取 repo metadata、README、package.json、src 目录、adapter interface、runner、temporal/conflict fixture 样例。  
> 结论：不建议直接接入为依赖；建议吸收其 eval taxonomy 和 adapter shape。

## 仓库状态

- GitHub repo: `verifiedstate/agent-memory-eval`
- Description: `Open benchmark suite for AI agent memory systems. Tests temporal reasoning, conflict detection, multi-hop retrieval, abstention, and provenance.`
- Primary language: TypeScript
- License: `package.json` 写 Apache-2.0，但 GitHub metadata 未识别 license。
- Stars: 0
- Repo 状态：archived
- 目录结构很轻：
  - `src/adapter.ts`
  - `src/runner.ts`
  - `src/fixtures/{temporal,conflict,multihop,abstention,provenance}.ts`
  - `src/adapters/verifiedstate.ts`

## 它测什么

README 定义了 5 类 memory eval：

| 维度 | 权重 | 含义 |
| --- | ---: | --- |
| temporal | 25% | 更新后的当前状态、历史时间点查询、过期事实、recency preference |
| conflict | 25% | 矛盾检测、supersession、trust-level resolution、exclusive slot |
| multihop | 20% | 2-hop/3-hop reasoning、reverse lookup、cycle detection |
| abstention | 20% | 未知、撤回、冲突不可解、低置信、未来状态时拒答 |
| provenance | 10% | source attribution、span citation、derived-fact chain、多源 corroboration |

这五类不是 agent memory 的全部，但对生产 memory 系统很像“基础体检项”。尤其是 temporal/conflict/abstention/provenance，比普通向量召回 eval 更贴近 OpenViking / Agent Harness 的风险。

## Adapter Shape

`MemorySystemAdapter` 接口：

```ts
store({ content, timestamp, source?, confidence? }) -> { id }
query({ question, limit? }) -> { answers, abstained, abstention_reason? }
queryAt({ question, timestamp }) -> { answers, abstained }
getConflicts(factId) -> { has_conflict, conflicting_facts? }
reset()
```

它的优点是很清晰：把 memory 系统当成一个可黑盒测试的服务。  
它的缺点也明显：对 Agent Harness 的 `memory routing / injected context / task outcome delta` 来说，它只测 memory store/query 的事实能力，不测“注入后是否改善 agent 行为”。

## Fixture 形态

fixture schema：

```ts
{
  id,
  description,
  category,
  setup: [{ content, timestamp, source?, confidence? }],
  query: { question, type?, factId? },
  expected: { contains?, abstained?, has_conflict?, source_cited? },
  score_dimension
}
```

样例特点：

- temporal fixture 会写入多条同一实体的更新事实，然后问当前状态或历史状态。
- conflict fixture 会写入来自不同 source/confidence 的矛盾事实，要求检测 conflict 或按 supersession / trust 取值。
- scoring 很轻，主要是 `contains`、`abstained`、`has_conflict`、`source_cited`。

## 对 Agent Harness 的价值

### 可吸收

1. **Memory Capability Taxonomy**
   - temporal / conflict / multihop / abstention / provenance 可以作为 `memory_eval_dimensions_v0`。
   - 它能补充 Agent Harness 目前偏 task-outcome 的 eval，把“memory store/query 基础能力”单独分层。

2. **Adapter Pattern**
   - 可以定义一个更适合 OpenViking 的 adapter：
     - `store_fact` / `store_experience`
     - `retrieve`
     - `retrieve_at`
     - `detect_conflict`
     - `reset_namespace`
   - 对应 OpenViking 的 `find/list/cat/commit` 与 memory namespace。

3. **Fixture Schema**
   - 可转成 JSON fixture，作为 `memory_capability_smoke_v0`。
   - 尤其适合跑 OpenViking / local mock / baseline vector store 的横向 smoke test。

### 不应直接照搬

1. **不测 Agent 行为改变**
   - 它问的是 memory query 是否答对，不是 agent 拿到 memory 后任务是否成功。
   - Agent Harness 的核心仍应是 `future-action outcome delta` 和 `regression risk`。

2. **scoring 过轻**
   - `contains` 型打分太脆，无法覆盖 tau2/OpenViking 的 tool action、DB diff、policy compliance。

3. **repo 已 archived**
   - 不适合作为长期依赖，只适合作为 taxonomy / fixture 参考。

## 建议给 Agent Harness 的动作

不要接入这个 npm 包；建议新建一个独立小任务：

- 新增 `memory_capability_smoke_v0`，从五类维度里先取 2-3 类最相关的：
  - temporal current / supersession
  - conflict detection
  - abstention / provenance
- 目标不是替代 tau2 eval，而是作为 OpenViking memory backend 的基础体检。
- 输出和 `memory_ranking_dataset_v0` 分层：
  - capability smoke：memory store/query 是否有基本事实能力。
  - routing/outcome eval：memory 被注入后是否改善 agent 行为。

## Agent Harness 主控转发稿

可以转发给 agent-harness 主控：

```text
我这边用 GitHub 搜索发现并读了一下 verifiedstate/agent-memory-eval：
https://github.com/verifiedstate/agent-memory-eval

结论：不建议直接接入依赖，因为 repo 已 archived，fixture/scoring 比较轻；但它的 memory eval taxonomy 值得吸收。

建议在 agent-harness 里新增一个很小的 `memory_capability_smoke_v0` 设计 TODO，不替代 tau2 outcome eval，只作为 OpenViking/local memory backend 的基础体检。可先覆盖 3 类：
1. temporal / supersession：同一实体状态更新后能否取最新值，或按时间点查询。
2. conflict detection：不同 source/confidence 的矛盾事实能否标出 conflict，而不是静默取一个。
3. abstention / provenance：未知或撤回事实能否拒答；答案能否带 source/provenance。

建议产物：
- 一个 JSON fixture schema：setup facts + query + expected + score_dimension。
- 一个 OpenViking adapter sketch：store/retrieve/retrieve_at/detect_conflict/reset_namespace。
- 文档里明确分层：capability smoke 测 memory backend 基础能力；memory_ranking_dataset_v0 / tau2 replay 测 memory injection 对 agent outcome 的增益。

验收标准：先不跑大规模 eval，只需要 10-15 条 fixture 能在 mock backend/OpenViking backend 上跑通并输出 category scores。
```
