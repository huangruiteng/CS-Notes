# 外部材料学习队列

[说明与维护](./README.md) · [其余候选](./CANDIDATES.md)

排名是建议阅读顺序，不代表已读或同时开工承诺。按材料 ID 保留重复来源；当前队列不含历史归档。

## Top 30

| 顺序 | 材料 | 档位 | 读取范围与备注 |
| --- | --- | --- | --- |
| 1 | [FP 入门：Algebraic Data Types——用 product/sum 与基数思维做类型建模，让非法状态不可表示](<https://dev.to/gcanti/functional-design-algebraic-data-types-36kf>) | S | 沿用既有阅读记录；用 product/sum 与基数建模；把一个状态结构改为判别联合，找出原先允许的非法状态。 |
| 2 | [Manus Context Engineering：缓存稳定性、外置记忆、目标复述与失败证据](<https://manus.im/zh-cn/blog/Context-Engineering-for-AI-Agents-Lessons-from-Building-Manus>) | S | 沿用既有阅读记录；比较缓存稳定前缀、文件外置记忆、目标复述与失败证据各自解决什么问题。 |
| 3 | [How we built Grok Bot in a month：产品迭代、onboarding 与持久 Agent](<https://x.com/shao__meng/status/2097578493353803800>) | S | 沿用既有阅读记录；关注原型到上线的产品取舍、手动 onboarding 与功能减法；区分采用证据和发布叙事。 |
| 4 | [Agents Should Be Durable, Not Long-Lived：durable state + leased executor 的 agent 运行时抽象（Ju Lin）](<https://julin.ai/2026/08/26/durable-agents/>) | S | 沿用既有阅读记录；画出 durable state 与 leased executor 的边界，解释 worker 重启和任务恢复的区别。 |
| 5 | [Anthropic Frontier Red Team：多 Agent 行为失败模式与协调机制](<https://www.anthropic.com/research/multiagent-systems>) | S | 沿用既有阅读记录；按共享目标、信息隔离与激励结构归类多 Agent 失败，思考哪些需要协议而非提示词。 |
| 6 | [pstack 作者原文 Pt.1：验证 CLI、Feature Map 与云 Agent](<https://x.com/yibie/status/2099458595150528543>) | S | 沿用既有阅读记录；选一个工程动作设计验证 CLI，列出输入、可观察结果和失败判定。 |
| 7 | [Co-ReAct：把 Rubric 从结果评分器前移为 Step-Level Action Spec](<http://xhslink.com/o/3xwVLFbj0gj>) · [来源 2](<https://arxiv.org/abs/2605.23590>) · [来源 3](<https://arxiv.org/html/2605.23590>) · [来源 4](<https://github.com/ZBWpro/Co-ReAct>) · [来源 5](<https://github.com/ZBWpro/Co-ReAct/blob/ff5540a6ba69090c7b41b81c7fa7f4b5b9627a3a/README.md>) · [来源 6](<https://github.com/ZBWpro/Co-ReAct/blob/ff5540a6ba69090c7b41b81c7fa7f4b5b9627a3a/agent/workflows/co_react_eval.py>) · [来源 7](<https://github.com/ZBWpro/Co-ReAct/blob/ff5540a6ba69090c7b41b81c7fa7f4b5b9627a3a/agent/dr_agent/rubric_generator.py>) · [来源 8](<https://github.com/ZBWpro/Co-ReAct/blob/ff5540a6ba69090c7b41b81c7fa7f4b5b9627a3a/rubric_rl/reward_fn.py>) | S | 沿用既有阅读记录；追踪 rubric 如何进入逐步行动选择，区分训练奖励、推理约束与结果评分。 |
| 8 | [Designing Grok Bot：为 persistent agents 设计五个产品原语（Bot roster/avatar presence/Bot 自有 computer/capability-context 分界/Routine 触发）](<https://x.ai/news/designing-grok-bot>) | S | 沿用既有阅读记录；比较 Bot 身份、存在感、自有计算机、能力与上下文、Routine 触发五个产品原语。 |
| 9 | [Google Antigravity Teamwork：多 agent 研究编排框架，patterns 解耦 + 自适应 agent 数量，Long Proof 竞争式策略搜索解决开放问题](<https://antigravity.google/blog/teamwork-when-ai-becomes-a-research-partner>) | S | 沿用既有阅读记录；读协作 patterns 与动态 Agent 数量；区分竞争式搜索、并行分工和结果集成。 |
| 10 | [Server-side Agent 的 Harness tradeoff（高策）：sandbox 单用户 → 多租户服务端 / sandbox=无状态执行环境 / session 与 context 工程 / eval parity 与轻量 JS runtime 探索](<https://gaocegege.com/Blog/genai/server-side-agent>) | S | 沿用既有阅读记录；比较本地单用户与服务端多租户的 sandbox、session、资源隔离与 eval 约束。 |
| 11 | [异步续延与 Effect 架构的第一性原理：要虚拟化时间/确定性调度/中断就必须持有续延，用户态解释器（Effect）vs 运行时下沉（PocketJS）](<https://x.com/ewind_dev/status/2092955281714209193>) | S | 沿用既有阅读记录；用续延解释中断、虚拟时间与确定性调度；区分用户态解释器和运行时支持。 |
| 12 | [Mastra Observational Memory：Observer/Reflector 后台把原始消息压缩成有界 observation log，prompt-cache 友好并保留 retrieval 还原](<https://mastra.ai/docs/memory/observational-memory>) | S | 沿用既有阅读记录；画出 Observer/Reflector 与检索回查链路，观察压缩对 token 成本和信息保真的影响。 |
| 13 | [Tencent WorkBuddy Bench：真实分布驱动的多域 Agent Benchmark 与 Harness 敏感性](<https://arxiv.org/abs/2607.20911>) · [来源 2](<https://github.com/Tencent/workbuddy-bench>) | S | 沿用既有阅读记录；检查真实任务分布、双 harness 对照、评分边界和预算记录。 |
| 14 | [WorkBuddy：从非目标用户的越界使用发现真实需求，并封装成高价值结果工作流](<https://mp.weixin.qq.com/s/r9RdgVLqsBG56rlsf3A5mA>) | A | 沿用既有阅读记录；关注越界使用怎样暴露需求，以及怎样把通用 Agent 包装为可验收的结果工作流。 |
| 15 | [The AI-native SDLC playbook：6 阶段 + plays + intent.md 产物链，AI 嵌入每个环节但人保留在 gate 之上](<https://claude.com/blog/the-ai-native-sdlc-playbook>) | S | 沿用既有阅读记录；对照六阶段产物链，说明模型自动化、人工 gate 与持续评估分别落在哪里。 |
| 16 | [Knowledge-Centric Self-Improvement：让共享知识而非 Agent 实现成为持续改进对象](<http://xhslink.cn/o/7F0W1DHVBPg>) · [来源 2](<https://arxiv.org/abs/2607.19592>) | S | 沿用既有阅读记录；区分共享知识更新和 Agent 实现更新；追踪知识如何验证、复用及失效。 |
| 17 | [SkillOpt-Lite 与 HarnessOpt：把 rollout 调试、skill 演化和执行框架演化统一成受控闭环](<https://mp.weixin.qq.com/s/GL0GTUp1OoxwU_2EHqLVnA>) · [来源 2](<https://arxiv.org/abs/2607.03451>) · [来源 3](<https://github.com/EvolvingLMMs-Lab/SkillOpt-Lite>) | S | 沿用既有阅读记录；比较 rollout 调试、skill 更新和 harness 修改三个优化对象及其验证边界。 |
| 18 | [DeepSeek-V4.1-Flash：CED、CSA2、FP4 KV cache 与 bounded replay](<https://huggingface.co/deepseek-ai/DeepSeek-V4.1-Flash/resolve/main/DeepSeek_V41_Tech_Report.pdf>) · [来源 2](<https://huggingface.co/deepseek-ai/DeepSeek-V4.1-Flash>) | S | 沿用既有阅读记录；拆解 prefill/decode 计算与 KV 存储账本；核对压缩收益成立的模型和负载条件。 |
| 19 | [火山引擎张鑫：企业 Agent 落地，我们之前忽视了经营问题](<https://mp.weixin.qq.com/s/lqRMub0fU3StGCvONZkvUg>) | A | 沿用既有阅读记录；把企业 Agent 采用拆为业务结果、运营责任、留存与成本，避免只看单次演示。 |
| 20 | [跨太平洋的 AI 棋局：公开译文中的开源商业化与 RSI 观点](<https://x.com/foxshuo/status/2093697436779004196>) | A | 沿用既有阅读记录；公开译文的产业观点；对照开源成本、云厂商价值捕获与 RSI 判断，事实需追一手证据。 |
| 21 | [Pi AgentHarness v3：durable runtime 实现规范（官方 spec）](<https://github.com/earendil-works/pi/blob/main/packages/agent/docs/harness-v3.md>) | S | 沿用既有阅读记录；读 durable runtime 的状态、恢复和接口契约；规范声明需与具体实现区分。 |
| 22 | [DeepSeek Harness（dsh）：一切皆插件的 agent harness 全栈](<https://github.com/deepseek-ai/deepseek-harness>) · [来源 2](<https://github.com/deepseek-ai/deepseek-harness/blob/47f943859bef60e4160492346772ded9b24f765a/docs/architecture.md>) | S | 沿用既有阅读记录；追踪插件、Session Log、权限和工具执行的所有权边界。 |
| 23 | [Cordis：时空可组合性的编程范式（design paper + 框架）](<https://github.com/cordiverse/cordis>) · [来源 2](<https://github.com/cordiverse/paper/blob/948a07b369c62adb3b12e102458be5c18dfb69b9/paper.pdf>) | S | 沿用既有阅读记录；用一个插件加载与卸载例子理解服务注入、资源生命周期和可回收副作用。 |
| 24 | [Pi Coding Agent：minimal core + self-extensible agent harness](<https://pi.dev/>) · [来源 2](<https://github.com/earendil-works/pi>) · [来源 3](<https://github.com/earendil-works/pi/blob/3da591ab74ab9ab407e72ed882600b2c851fae21/packages/agent/src/agent-loop.ts>) · [来源 4](<https://github.com/earendil-works/pi/blob/3da591ab74ab9ab407e72ed882600b2c851fae21/packages/agent/src/harness/session/session.ts>) · [来源 5](<https://github.com/earendil-works/pi/blob/3da591ab74ab9ab407e72ed882600b2c851fae21/packages/coding-agent/docs/session-format.md>) · [来源 6](<https://github.com/earendil-works/pi/blob/3da591ab74ab9ab407e72ed882600b2c851fae21/packages/coding-agent/docs/extensions.md>) · [来源 7](<https://github.com/earendil-works/pi/blob/3da591ab74ab9ab407e72ed882600b2c851fae21/packages/coding-agent/docs/security.md>) | S | 沿用既有阅读记录；从最小 agent loop 追到 session 与扩展点，区分核心责任和可替换策略。 |
| 25 | [AI4AI at Test-Time：strong builder 用 5% validation 迭代构造 harness，把 weak target 精度从 0.49 提到 0.91](<https://arxiv.org/abs/2608.12307>) | S | 沿用既有阅读记录；核对 builder/target 分工、验证集预算与基线；避免把 test-time 搜索收益混为模型增益。 |
| 26 | [Argus：长期研究 Agent 的证据闭环与验证门禁](<https://mp.weixin.qq.com/s/n9nutLHUSHPzCJf-2Pe_bQ>) · [来源 2](<https://github.com/lbx154/Argus>) · [来源 3](<https://arxiv.org/abs/2608.05144>) | S | 沿用既有阅读记录；关注四角色的证据交接、验证门禁与 Core/Vertical 分层，而不只看运行时长。 |
| 27 | [Fast Weight Attention for Continual Learning：把 fast-weight 记忆统一到在线持续学习框架（Falcon-1/2/3 家族）](<https://arxiv.org/abs/2608.27763>) | A | 沿用既有阅读记录；从在线学习看 fast weights，区分参数记忆、上下文记忆和持续学习假设。 |
| 28 | [Dream-RSI：通过已验证发现树回放，优化探索策略](<https://arxiv.org/abs/2609.14858>) · [来源 2](<https://github.com/zhengkid/Dream-RSI>) | S | 沿用既有阅读记录；手算发现树上的一次策略回放，检查候选预算、零执行评估与收益估计的条件。 |
| 29 | [Linear Sync Engine 逆向研究：事务、delta 顺序、离线队列与权限订阅](<https://github.com/wzhudev/reverse-linear-sync-engine>) | S | 沿用既有阅读记录；按本地事务、delta 顺序、离线重试和权限订阅追一条同步路径。 |
| 30 | [Dream-RSI 第三方复现：独立实现、回放契约与证据边界](<https://arxiv.org/abs/2609.14858>) | A | 沿用既有阅读记录；对照论文与第三方实现的回放和预算契约；独立复现不等于作者官方代码。 |

## Ranked backlog

| 顺序 | 材料 | 档位 | 读取范围与备注 |
| --- | --- | --- | --- |
| 31 | [数据库与分布式系统补课讲义：从 FP 与状态机到事务、幂等、fencing 与恢复](<./distributed-systems-for-loopx/补课讲义.md>) | S | 本次全文审查；17 节连接类型、纯决策、提交时验证、并发历史、日志与恢复、共识、存储与排队；用公开 commit 固定的 LoopX 代码作案例。 |
| 32 | [数据库与分布式系统：故障推演、交叉讨论与四周学习路线](<./distributed-systems-for-loopx/练习与讨论.md>) | A | 本次全文审查；8 道故障题、10 组讨论与四周安排；区分会复述、会推演、能实现和能提出反例。 |
| 33 | [Recovery Lab：幂等扣减、旧执行者、乱序投影与 write skew 教学实验](<./distributed-systems-for-loopx/recovery_lab.py>) | A | 本次运行通过；SQLite 演示盲重试余额 80、原子去重余额 90；覆盖参数冲突、提交前回滚、epoch 条件写和 snapshot 版本；write skew 是抽象内存模型。 |
| 34 | [Temporal 架构：History、Matching、内部任务队列、Outbox 与持久化](<https://docs.temporal.io/encyclopedia/architecture/temporal-architecture>) | A | 沿用既有阅读记录 |
| 35 | [TeamAI：通过 Git 分发团队 skills、rules、MCP 与记忆](<https://github.com/Tencent/teamai-cli>) | S | 沿用既有阅读记录 |
| 36 | [Koishi 官方文档：可逆的插件系统（Cordis 的可回收副作用与资源安全）](<https://koishi.chat/zh-CN/cookbook/design/disposable>) | B | 沿用既有阅读记录 |
| 37 | [Apache Maka（Incubating）：Log Is the Runtime——append-only RuntimeEvent Log 作为 agent 状态事实基座，UI/模型上下文/恢复都是投影](<https://github.com/apache/maka/blob/main/docs/blogs/log-is-the-runtime.md>) · [来源 2](<https://github.com/apache/maka>) | S | 沿用既有阅读记录 |
| 38 | [π-agent book：pi-agent-core 源码逐行架构解读（在线连载）](<https://books.antinomie.org/pi/>) · [来源 2](<https://github.com/antinomie-lab/pi-book>) | S | 沿用既有阅读记录 |
| 39 | [SoL-Pi：基于 Pi 的 harness 自动研究与机制筛选](<https://github.com/NVlabs/SoL-Pi>) | S | 沿用既有阅读记录 |
| 40 | [Rust Book Ch.6：Enums 与 Pattern Matching——sum type + match 穷尽检查 + if let 语法糖](<https://doc.rust-lang.org/book/ch06-00-enums.html>) | S | 沿用既有阅读记录 |
| 41 | [引用透明性：表达式替换、纯函数与程序优化的条件](<https://zh.wikipedia.org/wiki/%E5%BC%95%E7%94%A8%E9%80%8F%E6%98%8E%E6%80%A7>) | S | 沿用既有阅读记录 |
| 42 | [Huxley–Gödel Machine：Clade-Metaproductivity、Thompson Sampling 与自修改搜索](<https://www.xiaohongshu.com/discovery/item/6a944e4f000000001803fd8f>) · [来源 2](<https://github.com/metauto-ai/HGM>) | S | 沿用既有阅读记录 |
| 43 | [Grok Bot for Engineering：工程 Agent 的工种、验收与复盘](<https://x.com/ayi_ainotes/status/2094714127801262395>) | S | 沿用既有阅读记录 |
| 44 | [Crouzeix 猜想候选证明仓库：long-horizon 多 Agent 科研编排 prompt + 公开 trace + Lean 公理审计](<https://github.com/jinshanmu/CrouzeixConjecture>) | S | 沿用既有阅读记录 |
| 45 | [Cloudflare：Build your own vulnerability harness](<https://blog.cloudflare.com/build-your-own-vulnerability-harness/>) | A | 沿用既有阅读记录 |
| 46 | [LongHorizonOS：时间片、上下文切换、重启门禁与版本化进展图](<https://github.com/Yang-Jiashu/LongHorizonOS>) | S | 沿用既有阅读记录 |
| 47 | [Omarchy：Agent launcher、崩溃交接与跨 harness skills](<https://omarchy.org/>) · [来源 2](<https://github.com/omacom/omarchy>) | S | 沿用既有阅读记录 |
| 48 | [Scala 与 Algebraic data type：sealed trait + case class + match 穷尽性，TypeScript/Rust 之外的第三种 ADT 实现](<https://blog.cc1234.cc/posts/scala-adt/>) | S | 沿用既有阅读记录 |
| 49 | [Kimi K2.5 / Agent Swarm](<https://arxiv.org/abs/2602.02276>) | A | 沿用既有阅读记录 |
| 50 | [Hermes Mixture-of-Agents：多模型协同与聚合](<https://mp.weixin.qq.com/s/R12IIHds4qEXBgi8dGXT_g>) · [来源 2](<https://arxiv.org/html/2406.04692v1>) · [来源 3](<https://openreview.net/forum?id=h0ZfDIrj7T>) · [来源 4](<https://github.com/togethercomputer/moa>) · [来源 5](<https://github.com/togethercomputer/moa/blob/1b5cab0f0905d9da821e37322ac6df96ba65e1a7/README.md>) | A | 沿用既有阅读记录 |
| 51 | [JIT-Agent：训练模型即时生成受协议约束的 harness](<https://mp.weixin.qq.com/s/7EvVnk3iu68Lf0ABCTW6ig>) · [来源 2](<https://arxiv.org/abs/2608.25593>) · [来源 3](<https://github.com/bingreeky/JIT>) | S | 沿用既有阅读记录 |
| 52 | [Agentic Harness Engineering：把 harness 自迭代从 craft 变成可观测工程系统](<https://arxiv.org/abs/2604.25850>) · [来源 2](<https://github.com/china-qijizhifeng/agentic-harness-engineering>) | A | 沿用既有阅读记录 |
| 53 | [Harness Updating Is Not Harness Benefit: Disentangling Evolution Capabilities in Self-Evolving LLM Agents](<https://arxiv.org/abs/2605.30621>) · [来源 2](<https://github.com/A-EVO-Lab/a-evolve/tree/release/harness-evolution>) | A | 沿用既有阅读记录 |
| 54 | [EvoTrainer: Co-Evolving LLM Policies and Training Harnesses for Autonomous Agentic Reinforcement Learning](<https://arxiv.org/abs/2606.03108>) | A | 沿用既有阅读记录 |
| 55 | [EnvHarness：把 agent harness 思想镜像到环境侧，用 Setup/Rules/Link 插件层重塑冻结环境并保留原 verifier，LLM 设计器 EnvRigger 自动诊断并共进化](<https://arxiv.org/abs/2608.19880>) · [来源 2](<https://github.com/google-research/envharness>) | S | 沿用既有阅读记录 |
| 56 | [EvoMap / Evolver：Gene、Capsule 与进化资产共享协议](<https://github.com/EvoMap/evolver>) · [来源 2](<https://arxiv.org/abs/2604.15097>) | S | 沿用既有阅读记录 |
| 57 | [陈宇森 / MuleRun Agent Builder：runtime + skills + conversational marketplace](<https://mp.weixin.qq.com/s/YOvw2JAECFfrLC_tgYuHiw>) | A | 沿用既有阅读记录 |
| 58 | [Palantir 的“本体论骗局”：企业 AI 平台叙事解构与采购判断框架](<https://mp.weixin.qq.com/s/QRjoBm2zvLzF_tCGFYPnuw>) | A | 沿用既有阅读记录 |
| 59 | [Running a Software Factory Efficiently at Uber Scale：软件工厂成本工程（四层 agent、六项成本方程、模型路由、Code-Mode、context graph、16 类 session 反模式）](<https://x.com/ubereng/status/2093444169037762840>) | S | 沿用既有阅读记录 |
| 60 | [Dan Shipper / After Automation：异步委派 Agent、共享工作界面与必须有人照料的自动化](<https://mp.weixin.qq.com/s/39_b60E2gSPJmlx_UdnwGA>) | A | 沿用既有阅读记录 |
| 61 | [DSH + AWiki：Agent 原生身份与外部消息/邮箱接入的实现样本](<https://mp.weixin.qq.com/s/kyEN4P32IPy6arnxyHmtmQ>) | A | 沿用既有阅读记录 |
| 62 | [Chat 不是终局：长程任务的状态卡片、监督与信任设计](<https://x.com/siyuxu15/status/2096161966175948992>) | S | 沿用既有阅读记录 |
| 63 | [pstack 指南解读：验证基础设施、Agent CLI 与 Feature Map](<https://github.com/cursor/plugins/tree/main/pstack>) · [来源 2](<https://github.com/poteto/verification-skill-example>) | S | 沿用既有阅读记录 |
| 64 | [机器之心：DeepSeek Harness 震撼开源（二手报道 / 产品采用信号）](<https://mp.weixin.qq.com/s/mcVfdDVUVlEYJj61sJWKZA>) | B | 沿用既有阅读记录 |
| 65 | [Cordis 在做什么：从 DeepSeek Harness 看——服务/inject/effect/Loader 的机制级代码映射](<https://blog.antinomie.org/>) | A | 沿用既有阅读记录 |
| 66 | [万字长文：DeepSeek Harness 一文全看懂——Profile/Bundle/Patch、Cordis、Session Log、安全管线、四种模式与动态造工具](<https://x.com/russell3402/status/2092535898034630816>) | A | 沿用既有阅读记录 |
| 67 | [Dive into Claude Code: The Design Space of Today's and Future AI Agent Systems](<https://arxiv.org/pdf/2604.14228>) · [来源 2](<https://arxiv.org/abs/2604.14228>) · [来源 3](<https://arxiv.org/html/2604.14228>) · [来源 4](<https://github.com/VILA-Lab/Dive-into-Claude-Code>) · [来源 5](<https://github.com/VILA-Lab/Dive-into-Claude-Code/blob/ac7307fbd60a6e6598845e401db2c6a17cf7ae95/docs/architecture.md>) · [来源 6](<https://github.com/VILA-Lab/Dive-into-Claude-Code/blob/ac7307fbd60a6e6598845e401db2c6a17cf7ae95/docs/build-your-own-agent.md>) | S | 沿用既有阅读记录 |
| 68 | [OpenAI Codex Persistent mode：reasoning effort 新档让 Codex “继续工作直到被休眠”，并主动创建后续任务（WIRED 一手报道）](<https://www.wired.com/story/openai-is-developing-a-persistent-ai-agent/>) | A | 沿用既有阅读记录 |
| 69 | [Learn Claude Code：从 0 到 1 构建 nano Claude Code 风格 agent harness（20 个渐进 session，102→1708 LOC）](<https://learn.shareai.run/en/>) | S | 沿用既有阅读记录 |
| 70 | [Prime Agent：自我改进的 RLM coding/research harness（持久 IPython + Continual Harness）](<https://www.primeintellect.ai/blog/prime-agent>) · [来源 2](<https://arxiv.org/abs/2605.09998>) · [来源 3](<https://github.com/PrimeIntellect-ai/prime-agent>) | S | 沿用既有阅读记录 |
| 71 | [Multica：human + agent teams 的开源 managed agents platform](<https://github.com/multica-ai/multica>) · [来源 2](<https://github.com/multica-ai/multica/blob/c0c41fa0b4015355c9d6dbd38501b8381a61a29a/README.md>) · [来源 3](<https://github.com/multica-ai/multica/blob/c0c41fa0b4015355c9d6dbd38501b8381a61a29a/CLI_AND_DAEMON.md>) | S | 沿用既有阅读记录 |
| 72 | [FDE Observatory：Claude Managed Agents 深度调研 / Anthropic 的第三条路](<https://feizhuniu-infja.github.io/FDE-observatory/insights/cross/2026-07-03_anthropic-managed-agents.html>) | A | 沿用既有阅读记录 |
| 73 | [Paperclip：AI-agent company control plane](<https://github.com/paperclipai/paperclip>) · [来源 2](<https://github.com/paperclipai/paperclip/blob/b4a7efa8d2c1e2f57c042d50fda0157e025feac6/README.md>) · [来源 3](<https://github.com/paperclipai/paperclip/blob/b4a7efa8d2c1e2f57c042d50fda0157e025feac6/doc/PRODUCT.md>) · [来源 4](<https://github.com/paperclipai/paperclip/blob/b4a7efa8d2c1e2f57c042d50fda0157e025feac6/doc/SPEC-implementation.md>) · [来源 5](<https://github.com/paperclipai/paperclip/releases/tag/v2026.618.0>) | A | 沿用既有阅读记录 |
| 74 | [Agent libOS: A Library-OS-Inspired Runtime for Long-Running, Capability-Controlled LLM Agents](<https://arxiv.org/abs/2606.03895>) | A | 沿用既有阅读记录 |
| 75 | [Harness-1: Reinforcement Learning for Search Agents with State-Externalizing Harnesses](<https://arxiv.org/abs/2606.02373>) · [来源 2](<https://github.com/pat-jj/harness-1>) | A | 沿用既有阅读记录 |
| 76 | [Cloudflare Workflows saga rollbacks：durable step compensation for long-running workflows](<https://blog.cloudflare.com/rollbacks-for-workflows/>) | A | 沿用既有阅读记录 |
| 77 | [repo-harness：把 Claude/Codex 工程会话变成 repo-local 的可恢复工作流](<https://github.com/Ancienttwo/repo-harness>) | A | 沿用既有阅读记录 |
| 78 | [Terminal-Bench：命令行环境中的 hard realistic tasks](<https://arxiv.org/abs/2601.11868>) | A | 沿用既有阅读记录 |
| 79 | [SkillsBench：benchmarking how well agent skills work across diverse tasks](<https://arxiv.org/abs/2602.12670>) · [来源 2](<https://arxiv.org/html/2602.12670v1>) · [来源 3](<https://github.com/benchflow-ai/skillsbench>) | A | 沿用既有阅读记录 |
| 80 | [Agents' Last Exam：economically valuable long-horizon agent benchmark](<http://xhslink.com/o/1tiETi329bL>) · [来源 2](<https://arxiv.org/abs/2606.05405>) · [来源 3](<https://github.com/rdi-berkeley/agents-last-exam>) | A | 沿用既有阅读记录 |
| 81 | [Orca：worktree-native 的多 Agent 开发工作台与早期 orchestration control plane](<https://github.com/stablyai/orca>) | A | 沿用既有阅读记录 |
| 82 | [Measuring AI Agent Autonomy：用 code inspection 评估 autonomy / oversight / observability](<https://openreview.net/forum?id=VulxpvCNoA>) | A | 沿用既有阅读记录 |
| 83 | [Harnessing Embodied Agents：runtime governance 作为独立执行层](<https://arxiv.org/abs/2604.07833>) | A | 沿用既有阅读记录 |
| 84 | [MI9：goal-aware authorization + telemetry + conformance + containment](<https://openreview.net/forum?id=TseVPnC26W>) · [来源 2](<https://arxiv.org/abs/2508.03858>) | A | 沿用既有阅读记录 |
| 85 | [Position: AI Agents Need Authenticated Delegation：agent 委托、scope 与审计链](<https://openreview.net/forum?id=9skHxuHyM4>) · [来源 2](<https://arxiv.org/html/2501.09674v1>) | A | 沿用既有阅读记录 |
| 86 | [Unfireable Safety Kernel：execution-time authorization kernel for escapable AI systems](<https://arxiv.org/abs/2606.26057>) | A | 沿用既有阅读记录 |
| 87 | [OpenRSI / OpenMLE：可执行 AI4AI 元进化全栈（Frontis-MA1）](<https://arxiv.org/abs/2607.28568>) · [来源 2](<https://github.com/FrontisAI/OpenRSI>) | S | 沿用既有阅读记录 |
| 88 | [Evolvent AI：长期 Agent、权限、skills 与 RSI 评测研究目录](<https://x.com/evolvent_ai>) | S | 沿用既有阅读记录 |
| 89 | [MetaRSI-v1 / RSI-Harness：Data、Harness、Model 三类自改进算子](<https://mp.weixin.qq.com/s/HYFx2Vo0n1Uqkpd2eFE2VQ>) · [来源 2](<https://arxiv.org/abs/2609.06396>) | A | 沿用既有阅读记录 |
| 90 | [RSIAgent：curriculum、actor、verifier 与可迁移经验](<https://mp.weixin.qq.com/s/bg0tkvHsKTZ88uBNKUdVTQ>) · [来源 2](<https://arxiv.org/abs/2609.15364>) | A | 沿用既有阅读记录 |
| 91 | [递归自我改进现场观点汇编：验证、学习过程与生态分工](<https://mp.weixin.qq.com/s/VIPVAk0cxj5e9L36uIO-HQ>) | A | 沿用既有阅读记录；公开转载或观点整理；不复制非公开原始录音、转写或内部文档，观点不作为已验证事实。 |
| 92 | [红杉 RSI 讨论的公开图文整理：搜索、验证成本与自改进层级](<https://www.xiaohongshu.com/discovery/item/6aaf91f5000000002700abac>) | A | 沿用既有阅读记录；公开转载或观点整理；不复制非公开原始录音、转写或内部文档，观点不作为已验证事实。 |
| 93 | [Lilian Weng: Harness Engineering for Self-Improvement](<http://xhslink.com/o/30WhTMnQ3R2>) | S | 沿用既有阅读记录 |
| 94 | [Pat Grady 的公开转载观点：计算革命、能力采纳鸿沟与应用组织](<https://x.com/Michaelzsguo/status/2104049393062285740>) | A | 沿用既有阅读记录；公开转载或观点整理；不复制非公开原始录音、转写或内部文档，观点不作为已验证事实。 |
| 95 | [OpenAI Understands Something Important and Rare：客户创造、分发与定价](<https://x.com/davidgeorge83/status/2104576086101426620>) | A | 沿用既有阅读记录 |
| 96 | [五源资本：Loop Engineering——被高估的循环，被低估的拓扑](<https://mp.weixin.qq.com/s/_NXWh9DA3t4XTEH2GnTaDw>) · [来源 2](<https://arxiv.org/abs/2510.06674>) | A | 沿用既有阅读记录 |
| 97 | [Karpathy autoresearch + Loop Engineering：从人工 prompt 到 autonomous experiment loop](<https://mp.weixin.qq.com/s/fhx_Lozs5G-sX11b7wnZgg>) · [来源 2](<https://github.com/karpathy/autoresearch>) · [来源 3](<https://github.com/karpathy/autoresearch/blob/228791fb499afffb54b46200aca536f79142f117/README.md>) · [来源 4](<https://github.com/karpathy/autoresearch/blob/228791fb499afffb54b46200aca536f79142f117/program.md>) · [来源 5](<https://github.com/alchaincyf/loop-engineering-orange-book>) · [来源 6](<https://github.com/alchaincyf/loop-engineering-orange-book/blob/76cabe661699b36d3b0438f3cb97334082c8c49a/README.md>) | A | 沿用既有阅读记录 |
| 98 | [AMIE (Video)：实时 Agent 不能只有一个 Loop——Talker/Planner/Perception 按时间尺度异步编排](<https://arxiv.org/abs/2608.09861>) | S | 沿用既有阅读记录 |
| 99 | [Reef：把推理服务器变成持续自改进 Agent 基础设施（stateful inference + experience stream + model/harness 联合演化）](<https://x.com/ao_qu18465/status/2094867930081337730>) · [来源 2](<https://github.com/Human-Agent-Society/reef>) | S | 沿用既有阅读记录 |
| 100 | [Microsoft ASSERT + Agent Control Specification：spec-driven agent eval / open trust stack](<https://commandline.microsoft.com/assert-written-intent-executable-evals/>) | A | 沿用既有阅读记录 |
| 101 | [TypeSafe System One：类型化决策、概率校准与路由](<https://docs.typesafe.ai/concepts/system-one>) | A | 沿用既有阅读记录 |
| 102 | [Building a Harness with Jev：模型路由与工具执行前的风险门控](<https://x.com/sydneyrunkle/status/2100754364545761643>) | A | 沿用既有阅读记录 |
| 103 | [3SPO：state-score-supervised policy optimization for long-horizon LLM agents](<https://arxiv.org/abs/2606.09961>) · [来源 2](<https://arxiv.org/html/2606.09961v1>) · [来源 3](<https://github.com/genalyu/3SPO>) | A | 沿用既有阅读记录 |
| 104 | [HIPIF / Context-Folding：planning + information folding for long-horizon agent context control](<https://arxiv.org/abs/2606.10507>) · [来源 2](<https://arxiv.org/pdf/2606.10507>) · [来源 3](<https://arxiv.org/abs/2510.11967>) · [来源 4](<https://github.com/sunnweiwei/FoldAgent>) | A | 沿用既有阅读记录 |
| 105 | [DeepSeek V4 × J-Space 能力释放报告：capability-realization loss、思维链二极管与长程状态账本](<https://github.com/Tiger3807861189/DeepSeek-V4-J-Space-Capability-Realization-Report>) | A | 沿用既有阅读记录 |
| 106 | [ktx: open-source executable context layer for data agents](<https://www.kaelio.com/>) · [来源 2](<https://github.com/Kaelio/ktx>) | A | 沿用既有阅读记录 |
| 107 | [Agent Client Protocol / acpx / Paperclip ACP fit：structured session protocol vs control-plane boundary](<https://agentclientprotocol.com/get-started/introduction>) · [来源 2](<https://github.com/openclaw/acpx>) · [来源 3](<https://github.com/paperclipai/paperclip/discussions/787>) | A | 沿用既有阅读记录 |
| 108 | [stdrc：agent becomes the interface over everything](<https://x.com/istdrc/status/2070553645146636714>) | A | 沿用既有阅读记录 |
| 109 | [Raft source-available：release mirror、prompt request 与贡献模式](<https://x.com/istdrc/article/2103168507878011088>) | A | 沿用既有阅读记录 |
| 110 | [阿里技术：重新思考研发基础设施，当 Agent 成为第一公民](<https://mp.weixin.qq.com/s/fOONHtYDAJ39BojQxJ2-qg>) | A | 沿用既有阅读记录 |
| 111 | [平行记陆：AI Infra：跳出数据库，看到更大的 Agent Data Runtime](<https://mp.weixin.qq.com/s/1pA3l4brconluLWcpC0p3A>) | A | 沿用既有阅读记录 |
| 112 | [MemPoison / Hijacking Agent Memory：绕过 selective extraction 的 long-term memory poisoning](<http://xhslink.com/o/1mQp3aTSBjg>) · [来源 2](<https://arxiv.org/abs/2605.29960>) | A | 沿用既有阅读记录 |
| 113 | [Defeating Prompt Injections by Design / CaMeL：capability-based agent security](<https://arxiv.org/abs/2503.18813>) | A | 沿用既有阅读记录 |
| 114 | [Overeager Coding Agents：Benchmarking Horizontal Privilege Escalation in Software Engineering Agents](<https://arxiv.org/abs/2605.18583>) | A | 沿用既有阅读记录 |
| 115 | [Skill-Pro / ProcMEM：从 episodic trace 学 reusable executable procedural memory](<http://xhslink.com/o/1mQp3aTSBjg>) · [来源 2](<https://arxiv.org/abs/2602.01869>) | A | 沿用既有阅读记录 |
| 116 | [SWE-Skills-Bench：skills 是否真的帮助软件工程 agent](<https://arxiv.org/abs/2603.15401>) | A | 沿用既有阅读记录 |
| 117 | [SkillLens / From Raw Experience to Skill Consumption: A Systematic Study of Model-Generated Agent Skills](<https://arxiv.org/abs/2605.23899>) · [来源 2](<https://github.com/microsoft/SkillLens>) | A | 沿用既有阅读记录 |
| 118 | [SkillOpt: Executive Strategy for Self-Evolving Agent Skills](<https://mp.weixin.qq.com/s/pMlyj3a3KOh8L7cIHClRXA>) · [来源 2](<https://arxiv.org/abs/2605.23904>) · [来源 3](<https://github.com/microsoft/SkillOpt>) | A | 沿用既有阅读记录 |
| 119 | [Bayesian-Agent：用 posterior-guided evidence loop 做 skill / SOP 演化](<http://xhslink.com/o/3s6dSDLl3sa>) · [来源 2](<https://arxiv.org/abs/2606.08348>) · [来源 3](<https://github.com/DataArcTech/Bayesian-Agent>) · [来源 4](<https://github.com/DataArcTech/Bayesian-Agent/blob/e3a26a3c516c78c788094a6b1be71127bdeb7064/README.md>) | A | 沿用既有阅读记录 |
| 120 | [SkillAxe + SkillVetBench：agent skill 从 prompt 库升级成可评测、可审计、可上架的对象](<https://arxiv.org/abs/2606.10546>) · [来源 2](<https://arxiv.org/abs/2606.15899>) | A | 沿用既有阅读记录 |
| 121 | [vLLM Hybrid SSM Disaggregated Serving：agentic serving 的 state transfer 复杂度参照](<https://vllm.ai/blog/hybrid-ssm-disagg>) | A | 沿用既有阅读记录 |
| 122 | [SGLang HiCache / PD Disaggregation：hierarchical KV cache and prefill-decode split](<https://docs.sglang.io/docs/advanced_features/hicache_design>) | A | 沿用既有阅读记录 |
| 123 | [LMCache / vLLM APC：prefill once, reuse wherever possible](<https://docs.lmcache.ai/>) | A | 沿用既有阅读记录 |
| 124 | [dots3-note Preview：挑战 IMO 的 LLM 选手（Proof/Verify/Refine harness、TEMPO macro-step RL 与 40-50 小时 agent 负载的 serving/cache 账本）](<https://xhslink.cn/o/7u5qACGvFMa>) | S | 沿用既有阅读记录 |
| 125 | [NVIDIA Dynamo agentic inference：harness -> orchestrator 的 agent hints interface](<https://developer.nvidia.com/blog/full-stack-optimizations-for-agentic-inference-with-nvidia-dynamo/>) | A | 沿用既有阅读记录 |
| 126 | [Sail Research：agent inference throughput / long-running sandbox cost](<https://thenextweb.com/news/sail-research-80m-ai-agent-inference>) | A | 沿用既有阅读记录 |
| 127 | [GRU-Mem / When to Memorize and When to Stop：长上下文 recurrent memory 的 update gate 与 exit gate](<http://xhslink.com/o/5HwWelHrLws>) · [来源 2](<https://arxiv.org/abs/2602.10560>) | A | 沿用既有阅读记录 |
| 128 | [OpenAI Dreaming: Better memory for a more helpful ChatGPT](<https://openai.com/index/chatgpt-memory-dreaming/>) | A | 沿用既有阅读记录 |
| 129 | [TaskMem：把 agent 记什么建模成 task-focused memorization policy](<http://xhslink.com/o/AuvscrrKapl>) · [来源 2](<https://arxiv.org/abs/2605.31075>) · [来源 3](<https://github.com/ByteDance-Seed/TaskMem>) | A | 沿用既有阅读记录 |
| 130 | [TRUSTMEM：trustworthy memory consolidation verifier](<https://arxiv.org/abs/2606.25161>) | A | 沿用既有阅读记录 |
| 131 | [AMA-Bench：real agent trajectories 上的 long-horizon memory eval](<http://xhslink.com/o/1mQp3aTSBjg>) · [来源 2](<https://arxiv.org/abs/2602.22769>) · [来源 3](<https://github.com/AMA-Bench/AMA-Bench>) · [来源 4](<https://huggingface.co/datasets/AMA-bench/AMA-bench>) | A | 沿用既有阅读记录 |
| 132 | [AgentMemoryBench: Benchmarking Continual Agent Memory for Online Learning, Transfer, and Forgetting](<https://openreview.net/forum?id=MSXbrNExax>) · [来源 2](<https://github.com/solomoon313/AgentMemoryBench>) | A | 沿用既有阅读记录 |
| 133 | [MRAgent：Memory is Reconstructed, Not Retrieved](<http://xhslink.com/o/1mQp3aTSBjg>) · [来源 2](<https://arxiv.org/abs/2606.06036>) · [来源 3](<https://openreview.net/forum?id=YPoHy6lgKP>) · [来源 4](<https://github.com/Ji-shuo/MRAgent>) | A | 沿用既有阅读记录 |
| 134 | [STITCH / Grounding Agent Memory in Contextual Intent](<https://arxiv.org/abs/2601.10702>) · [来源 2](<https://openreview.net/forum?id=7FigeE9Zyl>) | A | 沿用既有阅读记录 |
| 135 | [Memoir / OpenViking：versioned and filesystem-like memory substrate](<https://www.memoir-ai.dev/>) · [来源 2](<https://github.com/volcengine/OpenViking>) | B | 沿用既有阅读记录 |
| 136 | [主流 Agent Harness 实现对比：Memory 篇](<https://mp.weixin.qq.com/s/qhwEhvE3IJqwYO088zfoYA>) | A | 沿用既有阅读记录 |
| 137 | [CodeGraph：为 Agent 预计算语义代码图与 surgical context](<https://github.com/colbymchenry/codegraph>) | A | 沿用既有阅读记录 |
| 138 | [Patronus AI digital worlds：agent simulation / stress-test environments](<https://www.patronus.ai/press>) | A | 沿用既有阅读记录 |
| 139 | [Heuresis：quality-diversity search for autonomous AI research agents](<https://arxiv.org/abs/2606.25198>) | A | 沿用既有阅读记录 |
| 140 | [Autodata：agentic data scientist for synthetic training/eval data](<https://arxiv.org/abs/2606.25996>) | A | 沿用既有阅读记录 |
| 141 | [真实工作流与训练数据：数据市场、hillclimbability 与 verifier 约束](<https://mp.weixin.qq.com/s/k7FDEUExvAkLvlXifE3_xw>) | B | 沿用既有阅读记录 |
| 142 | [DeepSWE：long-horizon coding-agent benchmark](<https://deepswe.net/>) · [来源 2](<https://github.com/datacurve-ai/deep-swe>) | A | 沿用既有阅读记录 |
| 143 | [唐杰 / 姚顺宇 long-horizon task 观点 + ProgramBench / RepoZero](<http://xhslink.com/o/1a3QvCWrloB>) · [来源 2](<https://github.com/facebookresearch/ProgramBench>) · [来源 3](<https://arxiv.org/abs/2605.03546>) · [来源 4](<https://arxiv.org/abs/2605.07122>) · [来源 5](<https://github.com/JesseZZZZZ/RepoZero>) | A | 沿用既有阅读记录 |
| 144 | [DeNovoSWE：whole-repository generation as verifiable long-horizon SWE environment](<https://arxiv.org/abs/2606.10728>) · [来源 2](<https://arxiv.org/html/2606.10728v1>) · [来源 3](<https://github.com/AweAI-Team/DeNovoSWE>) · [来源 4](<https://huggingface.co/datasets/AweAI-Team/DeNovoSWE>) | A | 沿用既有阅读记录 |
| 145 | [Tasteful Agent / Taste-Bench：长程轨迹中决策岔口的测量与训练](<https://x.com/shao__meng/article/2103772253691449820>) · [来源 2](<https://arxiv.org/abs/2609.25804>) · [来源 3](<https://github.com/wbopan/tastebench>) | S | 沿用既有阅读记录 |
| 146 | [Fiona Fung / Claude Code-Cowork：What happens after coding is solved?](<https://mp.weixin.qq.com/s/CFpLlR1SS7bn-Te50QF-3g>) | A | 沿用既有阅读记录 |
| 147 | [AEvo 上游谱系精读包：DGM -> GEPA -> ADAS](<https://arxiv.org/abs/2505.22954>) · [来源 2](<https://github.com/jennyzzt/dgm>) · [来源 3](<https://arxiv.org/abs/2507.19457>) · [来源 4](<https://github.com/gepa-ai/gepa>) · [来源 5](<https://arxiv.org/abs/2408.08435>) · [来源 6](<https://github.com/ShengranHu/ADAS>) | A | 沿用既有阅读记录 |
| 148 | [Autogenesis / AGP：自进化 Agent 的协议化资源治理](<https://mp.weixin.qq.com/s/nQXjwCTJIuaQEi6EQpVNIg>) · [来源 2](<https://arxiv.org/abs/2604.15034>) · [来源 3](<https://github.com/DVampire/Autogenesis>) | A | 沿用既有阅读记录 |
| 149 | [CORAL: Towards Autonomous Multi-Agent Evolution for Open-Ended Discovery](<https://mp.weixin.qq.com/s/13qdTAGV3pNot4X9KhCv0A>) · [来源 2](<https://arxiv.org/abs/2604.01658>) · [来源 3](<https://github.com/Human-Agent-Society/CORAL>) | A | 沿用既有阅读记录 |
| 150 | [Uni-Agent：veRL 通用 Agent 构建、运行、训练统一框架](<https://mp.weixin.qq.com/s/T2nQrogVjB82flnHvuFDHg>) · [来源 2](<https://github.com/verl-project/uni-agent>) | A | 沿用既有阅读记录 |
| 151 | [XiaomiMiMo/verl 与 MiMo-V2.6 §7：多 harness rollout、轨迹结构与信用分配](<https://github.com/XiaomiMiMo/verl>) | S | 沿用既有阅读记录 |
| 152 | [SearchAgent-Zero：从零训练多轮 Search Agent 的 verl RL 框架](<http://xhslink.com/o/3hBUiuuOj1j>) · [来源 2](<https://github.com/NLPJCL/SearchAgent-Zero>) · [来源 3](<https://arxiv.org/abs/2503.09516>) | A | 沿用既有阅读记录 |
| 153 | [Agent Lightning：Train ANY AI Agents with Reinforcement Learning](<https://arxiv.org/abs/2508.03680>) · [来源 2](<https://github.com/microsoft/agent-lightning>) | A | 沿用既有阅读记录 |
| 154 | [UnityMAS-O: A General RL Optimization Framework for LLM-Based Multi-Agent Systems](<https://arxiv.org/abs/2605.26646>) · [来源 2](<https://huggingface.co/papers/2605.26646>) | A | 沿用既有阅读记录 |
| 155 | [JitRL / Just-In-Time Reinforcement Learning：用经验记忆做 test-time policy optimization](<http://xhslink.com/o/5HwWelHrLws>) · [来源 2](<https://arxiv.org/abs/2601.18510>) · [来源 3](<https://openreview.net/forum?id=us2YPNouOm>) · [来源 4](<https://github.com/liushiliushi/JitRL>) | A | 沿用既有阅读记录 |
| 156 | [Progress Advantage for LLM Agents：annotation-free step-level scoring from RL post-training](<https://arxiv.org/abs/2606.26080>) | A | 沿用既有阅读记录 |
| 157 | [Agentic Reinforced Policy Optimization / ARPO](<https://arxiv.org/abs/2507.19849>) · [来源 2](<https://github.com/dongguanting/ARPO>) | A | 公开摘要页已核验；本次核验公开论文页面；技术细节沿用既有阅读记录。 |
| 158 | [Agentic Entropy-Balanced Policy Optimization / AEPO](<https://arxiv.org/abs/2510.14545>) · [来源 2](<https://github.com/RUC-NLPIR/ARPO>) | A | 公开摘要页已核验；本次核验公开论文页面；技术细节沿用既有阅读记录。 |
| 159 | [Let It Flow / ROLL / iFlow-ROME：Agentic RL 的三个苦涩教训](<http://xhslink.com/o/4fZpS3IJGrT>) · [来源 2](<https://arxiv.org/abs/2512.24873>) | A | 沿用既有阅读记录 |
| 160 | [EMPO²: Exploratory Memory-Augmented LLM Agent via Hybrid On- and Off-Policy Optimization](<https://openreview.net/forum?id=UOzxviKVFO>) | A | 沿用既有阅读记录 |
| 161 | [Training LLM Agents for Spontaneous, Reward-Free Self-Evolution via World Knowledge Exploration](<http://xhslink.com/o/ANgkXAy3h9b>) · [来源 2](<https://arxiv.org/abs/2604.18131>) · [来源 3](<https://arxiv.org/html/2604.18131v1>) · [来源 4](<https://github.com/Bklight999/world-knowledge>) · [来源 5](<https://github.com/Bklight999/world-knowledge/blob/589b65fa5d12f47db264fdfe521ad4b498271579/README.md>) · [来源 6](<https://huggingface.co/Bklight999/World-Knowledge>) | A | 沿用既有阅读记录 |
| 162 | [POM special issue + OM human-AI interaction：把 Goal Harness catalog 映射到运营管理语言](<https://www.poms.org/sites/default/files/callforpapers/Special%20Issue%20POM-Generative%20AI%20%28GenAI%29%20and%20Agentic%20AI%20at%20the%20Operations%E2%80%93Marketing%20Interface.pdf>) · [来源 2](<https://arxiv.org/abs/2605.14830>) | A | 沿用既有阅读记录 |
| 163 | [Cursor Composer 2.5：targeted RL with textual feedback](<https://cursor.com/blog/composer-2-5/>) | A | 沿用既有阅读记录 |
| 164 | [Codex 正在重塑传统推理框架开发流程：SGLang Diffusion、benchmark/profile、custom op 与 torch.compile graph break](<https://zhuanlan.zhihu.com/p/2017030396777346704>) · [来源 2](<https://github.com/sgl-project/sglang/pull/20699>) | A | 沿用既有阅读记录 |
| 165 | [AI-Infra-Auto-Driven-SKILLS：SGLang/vLLM SOTA Humanize Loop 与推理框架 agent workflow](<https://mp.weixin.qq.com/s/6uzb0OFDCDt4xmRcWaelaw>) · [来源 2](<https://github.com/BBuf/AI-Infra-Auto-Driven-SKILLS>) · [来源 3](<https://github.com/BBuf/AI-Infra-Auto-Driven-SKILLS/releases/tag/v0.1.0>) · [来源 4](<https://github.com/BBuf/AI-Infra-Auto-Driven-SKILLS/tree/main/skills/sglang-sota-humanize-loop>) | A | 沿用既有阅读记录 |
| 166 | [Kernel Design Agents：让 Agent 自己优化 CUDA kernel，并在 MLSys 2026 FlashInfer Full-Agent Track 拿下前三](<https://mp.weixin.qq.com/s/xIOIr4y60dzyeOn_3toipA>) · [来源 2](<https://github.com/mit-han-lab/kernel-design-agents>) · [来源 3](<https://github.com/DongyunZou/HANLab-Kernel-Mafia-MLSys2026-Submissions>) · [来源 4](<https://github.com/flashinfer-ai/flashinfer-bench>) | A | 沿用既有阅读记录 |
| 167 | [AI agents for science & the human-value debate（Zesen Huang @ AstroAI）](<https://x.com/zesenhuang/status/2086941232496824591>) | B | 沿用既有阅读记录 |
| 168 | [The State Monad：纯函数状态转换与 LoopX 状态机重构参考](<https://brandon.si/code/the-state-monad-a-tutorial-for-the-confused/>) | B | 沿用既有阅读记录 |
| 169 | [未核实的交易研究海报：论文核验与 backtest overfitting 方法](<https://x.com/0xkvro/status/2098468226397012054>) | B | 沿用既有阅读记录；来源真实性未确认；保留为核验案例，不作为论文结论。 |
| 170 | [量化交易教程的商业化样本：harness 结构、营销主张与证据边界](<https://x.com/rohonchain/status/2099500150939127945>) | B | 沿用既有阅读记录 |
