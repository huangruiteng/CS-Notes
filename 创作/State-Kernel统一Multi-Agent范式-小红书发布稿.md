# 长程 Multi-Agent：A2A 与 Dynamic Workflow 的统一状态协议

## 排版选型

这篇采用「小逸技术长文 + 状态卡片」混合版：

- 主体沿用「Handoff 不动点」的浅底、蓝标题、宋体长文，保证连续推导和技术密度。
- 吸收 LoopX 产品卡风格的三个优点：一页只立一个结论；状态、角色和协议用白色卡片；demo 与命令单独成页。
- 不采用黑底白字。长文、英文 schema 和来源信息在浅底上更稳定。
- 不采用整篇产品卡。State Kernel 的论证需要连续正文，全部卡片化会像产品说明书，削弱技术判断。
- 全部图片保持 `1440 x 1800`，采用 4:5 紧凑画布，保留小逸长文排版，同时压缩底部空白。

## 图片顺序

1. `01-cover-and-paradigms.jpg`：从数字员工理解两种长程 Multi-Agent 范式
2. `02-state-kernel.jpg`：State Kernel 的 source state / projection
3. `03-a2a-and-workflow.jpg`：State Kernel 分别承接 A2A 与 Dynamic Workflow
4. `04-papers.jpg`：CooperBench / Shepherd 与精炼解析
5. `05-loopx.jpg`：LoopX 对两种范式的承接与边界
6. `06-auto-research.jpg`：auto-research 角色与状态机
7. `07-knn-demo.jpg`：KNN demo 真实轨迹 + 一键命令 + GitHub

当前已渲染 7 页。第 7 页使用真实 demo 截图，仅做裁切与拼接。

## 小红书标题

推荐：

**长程 Multi-Agent：A2A 与 Dynamic Workflow 的统一状态协议**

备选：

- 长程 Multi-Agent 的控制面：State Kernel
- 长程 Multi-Agent 为什么需要 State Kernel
- Multi-Agent 跑成长程任务后，状态应该放在哪里

## 正文

长程 Multi-Agent 可以从人类 Leader 管理数字员工的视角理解。

第一种管理方式是 `Context, Not Control`：集中维护文档、群聊、项目状态和核心规划，员工基于共享上下文敏捷协作。整体效率更高，但会引入不确定性。

第二种管理方式是 Leader / POC 主导的 SOP or Workflow：根据业务场景，为多个角色定义严格的交互方式和流程。确定性更强，也方便做 domain 优化，但存在单点瓶颈，局势变化后需要重编排。

两种管理方式分别对应去中心化 A2A 与 Dynamic Workflow。

去中心化 A2A 没有中心 leader。agent 基于 state / mailbox / session 观察、认领和推进任务，适合开放探索与高并发协作。

Dynamic Workflow 由 workflow / supervisor 编排 execution graph，定义顺序、并行、分支、循环和状态保存，适合 domain SOP 与可复现流程。

长程任务通常会同时使用两种范式。开放任务由 agent 自主认领，关键链路交给 workflow；二者需要共享目标、边界、gate、quota、evidence 与 handoff。

State Kernel 是两种范式共享的控制面：

- Source state：goal、todo、claim、run history、evidence、operator gate、quota、rollback packet。只能通过受控写路径更新。
- Projection：status、todo index、task graph、review packet、dashboard。可以排序、压缩和展示，但不拥有 truth。

Source state 负责 truth，Projection 负责读取。State Kernel 不接管 executor、workflow runtime 或 mailbox，也不把 dashboard 当成事实源。

State Kernel 支持去中心化 A2A 的方式，是让多个 agent 围绕共享状态协作：

- shared event ledger：共享 source-of-truth event stream，状态不分叉；
- per-agent frontier：每个 agent 根据 scope、claim 和当前状态读取自己的可执行项；
- scoped claim：用 claimed_by、write scope 和 capability boundary 标记 ownership；
- quota guard：决定当前 agent 继续、等待、进入 gate，或先修复控制面；
- evidence graph：记录 artifact、eval、branch、失败尝试和负证据；
- handoff gate：约束 owner route、successor todo 与 no-follow-up。

多个 agent 可以读取不同 frontier，但所有执行结果写回同一份 source state。

State Kernel 支持 Dynamic Workflow 时，职责拆分为：

- workflow script / supervisor：顺序、并行、循环、工具调用和子 agent 调度；
- State Kernel：checkpoint / resume、branch basis、human gate、evidence writeback、quota spend、rollback / compensation 和 handoff。

node 完成后先写 evidence 与 state transition，再决定继续、分支、回滚、等待人类决策或 handoff。workflow 可以重编排，长期状态继续沿用。

CooperBench 从同一 repo 和 base commit 出发，构造两个可独立实现、但可能修改重叠逻辑的 feature。solo 模式由一个 agent 同时完成两项任务；coop 模式由两个 agent 在隔离 workspace 中各做一项任务，只通过自然语言消息协作，最后合并 patch 并运行两组测试。

600+ 个协作编码任务中，coop 的平均成功率比 solo 低约 30%。论文暴露了三类 coordination failure：消息含糊、时机不对或不准确；agent 偏离已经达成的承诺；agent 对同伴计划和通信形成错误预期。

这个 benchmark 的关键不只是「agent 不会聊天」。两个 agent 分别持有局部任务与局部 workspace，natural-language message 无法自动形成共享 checkpoint、ownership 与可验证 evidence。rebase / checkpoint 的价值，可理解为把隐式协作重新变成共享状态。

Shepherd 把 agent execution 变成可观察、可 fork、可 revert、可 replay 的一等对象。每个 model action、tool call 与 environment change 都进入 Git-like reversible trace；agent 与 environment 可以原子 fork，任意历史状态可以恢复和重放。

基于这个 substrate，supervisor meta-agent 在冲突发生前观察与介入，把 CooperBench pair-coding pass rate 从 28.8% 提升到 54.7%。CRO 则从行为发生变化的位置 fork 并 replay，避免每次从头重跑完整 trajectory。

CooperBench 说明 communication-only A2A 的上限；Shepherd 说明可操作的 execution state 可以直接改善协调。Shepherd 解决 execution trace 的 observe / fork / revert / replay，State Kernel 解决 goal / ownership / evidence / gate / quota / handoff 的长期事实源。两者处于不同层次，可以组合。

LoopX 在 executor 外实现 State Kernel，分别承接两种长程 Multi-Agent 范式：

- 对去中心化 A2A，提供 per-agent frontier、todo claim、evidence graph 与 handoff gate；
- 对 Dynamic Workflow，提供 checkpoint / resume、branch、human gate、rollback 与 quota spend。

Codex、Claude Code 与 workflow runtime 继续执行 bounded loop。LoopX 维护 goal / todo / evidence / gate / quota / handoff，不限定 agent 必须采用哪一种协作范式。

同一套状态合约可服务 A2A 与 Dynamic Workflow，两种范式也可以在同一个长程目标中切换。

Auto-research 是这套 State Kernel 上的一个 A2A demo。Research curator、Hypothesis proposer、Research executor、Evaluator / promoter 四个角色，分别负责 contract、hypothesis、dev / holdout experiment 与 promotion gate。

本次 KNN demo 中，Research executor 将 dev speedup 从 0.962107 提升到 1.130833，held-out test 为 1.139315；Evaluator / promoter 将其标记为受支持的晋级候选，Hypothesis proposer 继续产生 successor hypothesis。

GitHub：<https://github.com/huangruiteng/loopx>

#LoopEngineering #MultiAgent #AIAgent #AgentInfra #StateKernel #Codex #ClaudeCode #LoopX #开源项目

## 第 7 页实拍内容

标题：

**Auto-research：四个角色共享 State Kernel**

图：

- 原始 tmux 截图完整归档；发布页从原图裁出四段真实轨迹，避免横屏终端缩小后无法阅读。
- 四段证据分别对应 contract、successor hypothesis、dev / held-out evidence 与 promotion candidate。
- 截图仅裁切与拼接，不使用模型生成 UI。

命令：

```bash
loopx --format json auto-research start \
  "如何在保持精确近邻结果的前提下提升 KNN 查询速度？" \
  --preset knn-demo \
  --language zh \
  --session-name loopx-knn-demo \
  --workspace "$HOME/loopx-auto-research/knn-demo/visible-workspace" \
  --create-workspace \
  --execute \
  --no-attach
```

页尾：

`GitHub：github.com/huangruiteng/loopx`

## 技术来源

- CooperBench：<https://arxiv.org/abs/2601.13295>
- Shepherd：<https://arxiv.org/html/2605.10913v3>
- LoopX：<https://github.com/huangruiteng/loopx>
- Long-horizon state protocol：<https://github.com/huangruiteng/loopx/blob/eab76cd89a3e7a1dd81b9d4ced2ca601b0a1a05d/docs/reference/protocols/long-horizon-agent-state-protocol-v0.md>
- Auto-research role state machine：<https://github.com/huangruiteng/loopx/blob/eab76cd89a3e7a1dd81b9d4ced2ca601b0a1a05d/docs/reference/protocols/auto-research-role-state-machine-v0.md>
- Goal / vision / replan contract：<https://github.com/huangruiteng/loopx/blob/eab76cd89a3e7a1dd81b9d4ced2ca601b0a1a05d/docs/reference/protocols/goal-vision-replan-contract-v0.md>
- Auto-research command path：<https://github.com/huangruiteng/loopx/blob/eab76cd89a3e7a1dd81b9d4ced2ca601b0a1a05d/docs/guides/auto-research-command-path.md>

## 公开边界

- 正文与图片不放内部飞书链接、内部人员、内部案例或临时媒体 URL。
- CooperBench 的数据使用论文原始表述；「通信不等于共享状态」标明为工程推论。
- Shepherd 的效果数字使用论文公开结果，不扩写成 LoopX 的 benchmark 收益。
- 第 7 页只使用公开安全的真实 demo 截图。
