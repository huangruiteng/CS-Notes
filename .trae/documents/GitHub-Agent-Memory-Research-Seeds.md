# GitHub Agent Memory Research Seeds

> 目的：验证 `gh` 搜索能力已经可用，并把第一次 GitHub 召回转成后续 Agent memory / memory routing / 开源贡献的线索池。

## 验证结论

已完成：

```bash
Notes/snippets/github-search.sh status
Notes/snippets/github-search.sh repos "agent memory llm" 3
Notes/snippets/github-search.sh repos "llm agent" 3
Notes/snippets/github-search.sh repos "agent memory eval" 10
Notes/snippets/github-search.sh issues "memory" openai/codex 3
Notes/snippets/github-search.sh issues "memory" mem0ai/mem0 5
Notes/snippets/github-search.sh issues "memory" langchain-ai/langgraph 5
```

结论：

- `gh` 已登录并能返回结构化 JSON。
- repo / issue 两类搜索都可用。
- `agent memory eval` 方向的 GitHub 召回质量比泛搜 `agent memory llm` 更高。

## 高价值线索

### 1. verifiedstate/agent-memory-eval

- URL: https://github.com/verifiedstate/agent-memory-eval
- 来源类型：GitHub repo search
- 读取状态：只读 GitHub search metadata，尚未读 README。
- 摘要：描述为 “Open benchmark suite for AI agent memory systems”，覆盖 temporal reasoning、conflict detection、multi-hop retrieval、abstention、provenance。
- 判断：A 档偏高。它不像普通 memory demo，更接近 benchmark/eval，和 Agent Harness 的 memory routing / future-action outcome delta 很贴。
- 下一步：读取 README，判断是否能转成 Agent Harness 的 baseline/metric 对照。

### 2. mem0ai/mem0 issue: Type-Aware Memory Retrieval

- URL: https://github.com/mem0ai/mem0/issues/4926
- 来源类型：GitHub issue search
- 读取状态：只读 issue metadata，尚未读正文。
- 摘要：标题是 `Type-Aware Memory Retrieval with Support for Deterministic (Persistent) Memory`。
- 判断：A 档。它指向 production memory stack 的真实需求：memory 不能只按语义相似度召回，还要有 type-aware、persistent / deterministic memory 的区分。
- 下一步：读 issue 正文，对照 OpenViking 的 `Memory / Resource / Ability` 和 Agent Harness 的 memory item schema。

### 3. langchain-ai/langgraph issue: ClawMem memory/store integration

- URL: https://github.com/langchain-ai/langgraph/issues/7430
- 来源类型：GitHub issue search
- 读取状态：只读 issue metadata，尚未读正文。
- 摘要：标题是 `Proposal: community ClawMem memory/store integration`。
- 判断：B+。它未必直接服务你的 artifact，但说明 LangGraph 社区也在把外部 memory/store 当成核心 integration surface。
- 下一步：只读正文和讨论，不精读；看是否有 memory/store API 的可复用边界。

### 4. openai/codex memory issues

- URLs:
  - https://github.com/openai/codex/issues/19523
  - https://github.com/openai/codex/issues/19195
  - https://github.com/openai/codex/issues/19758
- 来源类型：GitHub issue search
- 读取状态：只读 issue metadata，尚未读正文。
- 摘要：三个 issue 都和 Codex memory UX / writability / topic-based memory 相关。
- 判断：B+。适合作为“真实 coding agent 用户如何抱怨 memory”的 product/infra pain point 观察，不应抢 P0 paper 时间。
- 下一步：等要写 Codex/Agent memory UX 观察时再读。

### 5. agentic-memory-eval / MemEval 系列小仓库

- URLs:
  - https://github.com/jeffhurst/MemEval
  - https://github.com/OliverZhu-2021/agentic-memory-eval
  - https://github.com/konrad-woj/agentic-memory-eval
- 来源类型：GitHub repo search
- 读取状态：只读 metadata。
- 摘要：多为小型 benchmark/eval 复现或课程/个人项目。
- 判断：B。可以作为 negative/landscape 样本，用来快速确认社区 eval 还比较浅；不建议用户亲自读。
- 下一步：Codex 有空扫 README，抽取 metric taxonomy。

## 下一步 TODO 候选

1. `调研：verifiedstate/agent-memory-eval`，读取 README，判断是否能接进 Agent Harness。
2. `调研：mem0 type-aware memory retrieval issue`，提炼 memory type/filter/persistent memory 的生产需求。
3. 建一个每周 GitHub issue radar：关键词 `agent memory eval`、`memory routing`、`type-aware memory`、`episodic memory agent`。

短期最建议推进第 1 个，因为它最接近 `memory_ranking_dataset_v0` 的 benchmark/eval 叙事。
