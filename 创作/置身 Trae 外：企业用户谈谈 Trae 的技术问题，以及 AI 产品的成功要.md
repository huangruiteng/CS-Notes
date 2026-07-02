# 置身 Trae 外：企业用户谈谈 Trae 的技术问题，以及 AI 产品的成功要素

*纯人手写 1100 字*

我从 Trae 切换到 Codex 一个月，效率上就有了数倍的提升；同事想搭建一套自动模型优化 Agent，基于 Trae 一周都没搞定，换到 Codex 半天即落地。

Trae v.s. Codex/Claude Code，全是模型能力的差距么？不尽然，也关乎于 Product Interaction 和 Harness，Trae 给大家上了一堂 the bitter lesson 的生动教学课

the bitter lesson 的核心观点是技术和产品发展应遵循 scaling up 的趋势，技术上，面向可 scaling 的通用计算能力和 harness；产品上，追求产品、模型、工具、长程状态的协同演进；不应追求过度手工雕刻的领域技巧。

## 技术决策失误：IDE 不是底座

Trae 的第一个决策失误是，早期没有认知到 Cli/Harness Runtime 是更统一的底层。AI 产品不仅面向人，也面向计算机/Agent，而 Cli 是产品与计算机的最佳交互接口。这本质是 前端思维太重，未意识到伴随模型能力发展，人的注意力是宝贵资源，此时 前端在精不在多，越重越损耗易用性。早期没有将 IDE 背后的 runtime、CLI、任务队列、状态管理、远程执行抽成统一底座，伴随产品迭代，一坨前后端代码不再可能重构成 Cli。纵使 Codex/Claude Code 爆火，Trae 也无法快速在市场上推出 Trae Cli ，迎合新的技术趋势，一步落后步步落后。

## 成本约束下的保守架构：过重的上下文工程省 Token

我用过一阵子 Trae 的外部企业版，能看到 Token 消耗数据，当时高强度工作一天，只消耗大约 几十到 100 万 token，而现今 codex 随便一个 task 就是上百万 token，重度长程使用日均十五亿 token，产出也高了许多。 目前人类 AI 发展趋势是大力出奇迹，堆算力、堆参数、堆 token、堆产品能力，过重的上下文工程制约了 scaling，制约 scaling 即等于制约了产品上限。

## 落后的 IDE 交互范式

清晰的交互范式定义能辅助产品显著强于陈旧的范式，比如 codex 的 queuing/steering/automation/goal，定义了 agent 如何与人进行异步交互。但 trae 至今也不支持这些，仅最近推出的 trae work 支持了 automation。

Coding 产品的发展，应紧密与模型协同，面向 Agent 投入更多 effort、人投入更少的 attention，从而减轻人的负担的同时，具备更长程的任务执行能力。Trae 缺少面向长程任务的统计 agent control plane 设计，上述能力的缺失导致开发者手动 ralph loop 都很困难。 此外还有若干细节，比如当命令执行时间过长之后，会自动把任务切到后台，影响在单次对话内完成 e2e 的 task。

## 尾大不掉：功能跟进的缓慢

且不谈codex的实验能力如 memory、chronicle、computer using 等能力，连自动化、queuing 和 steering 这些基础产品能力都跟进的异常缓慢。如果我是 trae，codex 推出这几个能力的同时，第一时间就会推进把这几个抄了。OpenAI 定义的优雅、general 的用户交互模型，显然比一问一答模式强。

## AI 产品的成功要素

### 面向模型未来能力友好的

模型和产品的高效协同是老生常谈的话题，codex、cc 和 doubao 就做的不错，此处不展开。

### 与用户的交互模型应是精准、优雅的

前面讨论的 goal + task queuing + reward steering + automation，是面向长程 agent 与人协作的一个切口。此外 Codex 在产物审阅上亦有创新，弱化了文件系统可视化，强化了 evidence，比如不同粒度的改动 diff，面向用户 review。

### 能用海量 token 换效果的

至少在短期高烈度的 AI 产品竞争环境下，成功产品一定是能用成本换效果的。比如：

- 豆包的长期免费。
- CodeX 的大量 token 消耗和实惠套餐，套餐折扣程度是 API 的几十分之一。
- 哪怕是曾短期出圈的 OpenClaw，一个成功点也在于它在年初早期，用海量的 token 消耗以及配套的架构设计，让较弱的模型也初步具备自主任务执行的能力。

## 总结

企业用户视角下，AI Coding 产品的胜负已从 IDE 功能转向 agent control plane。获胜的关键点在于，与前沿模型的协同、精准优雅的用户交互范式、token 资源 等。谁掌握了这些，谁才能在 ai tob 市场上占据主动权。
