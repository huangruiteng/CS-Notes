# DeepSeek Harness plugin scaling - 小红书发布稿

## 当前状态

- 正文已重写，LoopX 不再是中段类比或结尾 CTA，而是由 LoopX 的产品判断自然接管收尾，不写生硬的 creator 自我介绍。
- 7 页紧凑版图片已生成：`DeepSeekHarness-plugin-scaling-紧凑排版/`。
- LoopX `content-ops layout-check` 已通过；7 页有效内容密度为 `0.821–0.906`，其中封面为 `0.906`、正文页（第 2–6 页）为 `0.821–0.899`，无溢出、碰撞或孤字行。正文页均包含主判断、机制或对比，以及含义或证据边界；最后一页保持原版。
- 当前仍是本地 `draft`，`autopublish_allowed=false`。

## 排版决策

使用 `light-serif-longform` 的浅色衬线长文模板，统一为 1440 × 1920：

1. 封面：DeepSeek Harness 在赌什么；答案是 Plugin Scaling 与长期吸收
2. 机制：Everything is a Plugin，连 agent loop 也能换
3. 对比：kernel 串行吸收，plugin 并行试验
4. 证据：三层吸收飞轮，以及数据回流边界
5. 边界：数据、分层、治理、激励四个瓶颈
6. 指标：不看 plugin 数，看 absorption cycle
7. 收尾：LoopX 对「吸收」的产品判断

第 7 页由 LoopX 观点成为主角，但不写产品 CTA：DSH 的启发被落到 LoopX 要解决的长程实践吸收问题。

## 标题

推荐：

**DeepSeek Harness 在赌什么？Plugin Scaling**

备选：

- DeepSeek Harness 真正想 scale 的，是吸收速度
- DSH 把 agent loop 做成 plugin，到底在赌什么
- plugin 比 kernel 更能 scale，但代价呢

## 正文

DeepSeek Harness 最值得看的，不是论文里的范畴论，也不是仓库里塞了多少插件。

我先说判断：它对大多数日常 coding 场景仍然太重，但这个「重」背后是一张很清楚的明牌——不急着和 Claude Code、Codex 拼当前版本的绝对完备，而是把 harness 拆成可替换、可组合的 plugin，赌生态扩展性与长期吸收速度。

### 1. Everything is a Plugin，连 agent loop 也能换

在 DSH 里，模型适配器、工具注册表、会话日志，连 agent loop 本身都由 plugin 提供；Web GUI 也沿着同一套机制装配。

这不是常见的「给产品留几个扩展点」。连控制流都能被卸载、替换，说明 DSH 想把 harness 做成实验底座：开发者不用等官方改 kernel，就能换掉模型接入、工具链、会话机制乃至整个 agent loop。

代价同样直接。可替换面越大，理解、配置、兼容、权限与运行时治理的成本越高。DSH 当前更像一套可研究、可改造的 agent substrate，还不是一个人人开箱即用的 coding agent。

### 2. plugin 比 kernel 更能 scale，scale 的是并行试验

kernel 每吸收一项能力，都要一起处理兼容、迁移、回滚和发布节奏。所有创新排队进同一个内核，组织本身就会变成串行瓶颈。

plugin 把创新变成并行增量：不同作者可以独立试验，失败的能力可以单独卸载，有价值的能力再进入官方预置或 kernel。

所以 plugin scaling 扩大的不是简单度，而是试验与迭代的并行度。复杂度没有消失，只是被搬到了边界：版本兼容、权限、安全、隔离、可观测性和运维，最后都要有人负责。plugin 越多，治理越重要。

### 3. 真正的飞轮，不是插件数量

我理解的完整飞轮有三层：

- 外部实践先被写成 plugin；
- 高频、稳定的能力被吸收成官方 plugin，甚至进入 kernel；
- 如果使用数据能在清晰授权下进入训练或评测，模型再吸收这些工具交互经验。

公开架构明确支持「外部能力可插拔」这一步，但不等于后两层已经跑通。尤其是第三层，我没有看到足够公开证据证明 plugin 数据已经回流模型训练。

没有数据回流，DSH 仍然可以是一个很强的插件系统；只有回流、蒸馏和反哺真的闭环，它才可能成为模型能力的外部研发系统。这是它最有想象力、也最需要证据的一步。

### 4. 这套打法最难的不是写 plugin

真正的瓶颈至少有四个：

- 数据是否回流，授权与遥测边界是否清楚；
- 哪些能力进 kernel，哪些留在官方 plugin，哪些交给第三方；
- 兼容、安全、隔离与可观测性由谁兜底；
- 好 plugin 被官方吸收后，原作者为什么还愿意持续贡献。

最后一条尤其容易被忽略。如果优秀 plugin 的终点都是「被内置并替代」，生态作者就需要新的收益、声誉或治理权，否则飞轮会先在供给侧停下来。

所以我不会急着把 plugin scaling 叫作 DeepSeek 的护城河。它是一张明牌，也是一场尚未完成验证的赌局。

闭环成立，外部生态会不断变成官方能力，甚至反过来改进模型；闭环不成立，Everything is a Plugin 仍然是漂亮的架构，但再多 plugin 也只是目录。

真正值得长期跟踪的指标，不是 plugin 数量，而是一个外部 plugin 从出现，到进入官方能力、评测甚至模型，究竟需要多久。

吸收周期，才是这套架构的核心指标。

### 5. LoopX 也有共性

LoopX 也有共性。作为长程 Harness 当前最具竞争力的中间层，它希望持续吸收长程任务和数字员工领域的最佳实践与能力，也已经有了初步的函数式编程抽象，去承载这些实践。

长程 Agent 每天都会产生新的做法：一次更稳的 handoff、一条避免失控的 gate、一个能恢复任务的状态转换、一套社区验证过的工作流。它们如果只留在某次 session、日志或个人 prompt 里，就没有形成系统能力。

LoopX 要吸收的不是模型训练数据，而是长程运行中的公开实践与工程规则：把偶然奏效的做法，沉淀成可审计的协议、状态机、effect program 和控制面能力，让后续 Agent 可以直接继承。

DeepSeek 把 plugin scaling 押在「生态实践 → 官方能力 → 模型」；LoopX 押在「长程运行 → 可复核规则 → 控制面」。

没有 DeepSeek 的资源，道阻且长；所幸社区开发者们已经做出了许多贡献。两条路的共同点，是把「吸收」做成 Harness 的一等能力。

## 技术来源

- DeepSeek Harness（Everything is a Plugin）：<https://github.com/deepseek-ai/deepseek-harness>
- DeepSeek Harness 架构文档：<https://github.com/deepseek-ai/deepseek-harness/blob/master/docs/architecture.zh.md>
- Web Cordis 示例：<https://github.com/deepseek-ai/deepseek-harness/blob/master/examples/web-cordis/README.zh.md>
- X 原文（plugin scaling 明牌）：<https://x.com/huangruiteng/status/2088306107332833559>
- X 原文补充（数据回流与作者激励尚未验证）：<https://x.com/huangruiteng/status/2088307842315128869>
- LoopX：<https://github.com/huangruiteng/loopx>
- LoopX Effect Interpreter RFC：<https://github.com/huangruiteng/loopx/blob/main/docs/architecture/rfcs/agent-loop-effect-interpreter-v0.zh-CN.md>

## 图片文件

- `DeepSeekHarness-plugin-scaling-紧凑排版/01-cover.jpg`
- `DeepSeekHarness-plugin-scaling-紧凑排版/02-everything-plugin.jpg`
- `DeepSeekHarness-plugin-scaling-紧凑排版/03-plugin-vs-kernel.jpg`
- `DeepSeekHarness-plugin-scaling-紧凑排版/04-absorption-flywheel.jpg`
- `DeepSeekHarness-plugin-scaling-紧凑排版/05-four-bottlenecks.jpg`
- `DeepSeekHarness-plugin-scaling-紧凑排版/06-absorption-cycle.jpg`
- `DeepSeekHarness-plugin-scaling-紧凑排版/07-loopx-creator-thesis.jpg`

## 发布备注

- 旧 `小逸排版/` 目录仅保留历史版本，不再用于发布。
- 「plugin 数据回流模型训练」仍是未验证判断，不写成已发生事实。
- LoopX 只在最后一节接管论点，不加 GitHub 搜索、安装或关注 CTA。
- 发布前仍需用户确认正文与图片；布局通过不等于发布授权。
