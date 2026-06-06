# AMA-Bench -> Agent Harness Steering

> 用途：把 AMA-Bench 读后判断转成 agent-harness 可执行 steering。本文只基于公开论文、开源仓库、公开 dataset / leaderboard 和用户读后判断整理，不包含内部链接。

## 结论

AMA-Bench 值得加入 Agent Harness 的 benchmark radar，但定位应是 **long-horizon agent trajectory memory diagnostic**，不是下一阶段唯一主 benchmark。

它最有价值的是 trajectory 数据：真实 agent 轨迹覆盖 web、software、Text2SQL、embodied AI、game、open-world tool QA，且包含工具调用、结构化机器表示、状态转移和稀疏客观证据。这和 Agent Harness / OpenViking 要做的 trace、memory construction、retrieval evidence、paired replay 很接近。

它较弱的是 QA 终点：很多问题仍是 post-hoc trajectory QA，例如询问某个 step 的 action / observation。它能测 memory 是否读懂过去轨迹，但不能直接证明 memory 是否改善未来 action、tool correctness、DB diff 或 task outcome。

## 建议动作

### P0. AMA-Bench Adapter Smoke Test

新增一个小而闭合的 adapter smoke，而不是先复现 AMA-Agent：

1. 读取官方 `dataset/test/open_end_qa_set.jsonl` 的 5-20 条样本。
2. 将 `trajectory` 映射到 Harness trajectory schema：
   - `episode_id`
   - `task`
   - `domain`
   - `task_type`
   - `turn_idx`
   - `action`
   - `observation`
3. 实现最小两阶段接口：
   - `memory_construction(trajectory_text, task) -> memory_object`
   - `memory_retrieve(memory_object, question) -> context_string`
4. 先跑 baseline retrieval：
   - long context
   - BM25 by turn
   - embedding by turn
5. 输出 answer artifact：
   - `episode_id`
   - `question_uuid_list`
   - `answer_list`
   - `retrieved_evidence`
   - `reasoning_trace`
   - `judge_result`

验收标准：

- 能稳定跑通 5-20 条样本。
- 每条答案都能追溯到原始 trajectory turn 和 retrieved evidence。
- 输出里能区分 retrieval failure、answering failure、judge disagreement。
- 形成一页 adapter spec，说明哪些 AMA-Bench 字段自然映射到 Harness，哪些字段只是 benchmark-local。

### P1. 不追 leaderboard，先做 capability diagnostic

AMA-Bench 官方 leaderboard 可以作为外部参照，但短期不要把目标写成 leaderboard score。更有用的是把它拆成 memory capability smoke：

| Capability | Harness 侧检查点 |
| --- | --- |
| Recall | 能否找回 step / temporal / sequential evidence |
| Causal Inference | 能否找出 action precondition 和 state dependency |
| State Updating | 能否跟踪 explicit observation 与 hidden state update |
| State Abstraction | 能否从长轨迹压缩出关键状态，且不丢 objective evidence |

这些检查点应和 tau2 / OV replay 分层：AMA-Bench 测 memory backend / retrieval evidence，tau2 / OV 测 memory injection 是否提升 future outcome。

### P2. 继续找相邻 outcome benchmark

用户当前判断是：AMA-Bench trajectory 数据不错，但 QA 对不一定有实际意义。因此 OV 候选 benchmark 还要继续调研，优先找和 AMA-Bench domain 相邻、但终点更接近 future action / outcome 的 benchmark：

- web：WebArena / browser task replay / state diff
- software：SWE-bench / coding agent trace replay
- Text2SQL：Spider 2.0 / DB execution correctness
- embodied AI：ALFWorld / MiniHack / environment state success
- game / open-world QA：有明确 state transition 和 final reward 的任务

验收标准不是“又列一批 benchmark”，而是给出每个候选是否能支持：

- trajectory extraction
- memory construction from previous episodes
- memory injection during future episode
- paired replay with / without memory
- objective outcome delta

## Agent Harness 主控转发稿

背景：AMA-Bench 值得进 radar，但建议把它定位为 long-horizon agent trajectory memory diagnostic，而不是主 benchmark 终点。它的 trajectory 数据和 two-stage memory interface 很适合 Harness；但 QA 多是 post-hoc trajectory QA，不直接等价于 memory 是否改善 future action / outcome。

建议动作：新增 `AMA-Bench Adapter Smoke Test`。读取 `dataset/test/open_end_qa_set.jsonl` 少量样本，映射 trajectory schema；实现 `memory_construction` / `memory_retrieve` 最小接口；跑 longcontext、BM25、embedding 三个 baseline；保存 answer、retrieved evidence、judge result、trace id。

验收标准：能跑通 5-20 条样本；每条答案可追溯到原始 trajectory turn；能区分 retrieval failure、answering failure、judge disagreement；形成 adapter spec。不要先追 leaderboard 或复现 AMA-Agent。

后续：继续调研 OV 相邻 benchmark，沿 web、software、Text2SQL、embodied AI、game、open-world tool QA 找能评估 future action / outcome delta 的任务。AMA-Bench 负责 memory capability diagnostic，tau2 / OV replay 负责最终 outcome evaluation。

相关链接：

- https://arxiv.org/abs/2602.22769
- https://github.com/AMA-Bench/AMA-Bench
- https://huggingface.co/datasets/AMA-bench/AMA-bench
- https://huggingface.co/spaces/AMA-bench/AMA-bench-Leaderboard
