# 长程任务的 insight

## 小红书正文

最近准备 Goal Harness 分享稿时，我重新理解了一次“长程任务”。

它不是让 agent 多跑几轮。

也不是把上下文窗口拉得更长。

我的判断是：长程任务的核心，是给 agent work 补一层控制面。

### 1. 长程任务不是聊天变长，而是状态变复杂

短任务里，agent 的上下文基本就是任务现场。

长任务里，现场会散到聊天、文档、代码、实验、用户反馈和权限边界里。

如果这些状态没有被外置，agent 仍然能继续做事，但人会重新变成调度器。

### 2. Agent 是 worker，state 才是共同事实面

Codex thread、Claude Code session、CLI runner，本质上都是 worker。

worker 可以中断、替换、旁路推进。

长期任务不能把真相放在某个 worker 的记忆里。

它需要 goal state、run history、evidence state、gate state、quota state 和 reward state。

### 3. Run history 不该是总结，而该是事件账本

“我做了什么”不够。

长程任务需要知道：产物在哪里，验证结果是什么，消耗了什么资源，还缺什么证据，下一步是否仍然合法。

`artifact / validation / gate / evidence / spend` 这些事实应该写成 event。

否则下一轮 agent 只能从自然语言里猜。

### 4. Human gate 不是一句确认，而是一个可继承的决策

人在聊天里说“继续”“先等”“不允许写”，agent 当下能理解。

但长期协作里，这些判断必须绑定到 run、gate 和 evidence。

一次 approval 需要知道它基于什么状态产生，当前状态是否仍然满足前置条件。

人的反馈不是聊天消息，是控制面信号。

### 5. Quota 不是省钱，而是防止自动化反噬人

长程 agent 消耗的不只有 token。

还有实验位、CI slot、上下文窗口、用户 review 面。

没有 quota，自动化会持续制造 diff、候选方案和 review packet。

表面上 agent 很勤奋，实际把人拖回审阅循环。

### 6. Incremental progress 不是越小越好

小步可以降低风险。

但连续小步也可能变成 surface-only patch。

看起来每轮都 clean，primary outcome 却没动。

真正有价值的 incremental progress，应该有 artifact、validation、checkpoint、replayable record 和 state writeback。

### 7. 产品上，长程 agent 需要 operator view

用户不应该每隔几分钟说一次“继续”。

用户应该第一眼看到：哪个项目需要判断，哪个项目在等证据，哪个项目可以继续，哪个项目不能越界。

这不是把所有日志展示出来。

而是把“谁欠什么、谁能继续、谁不能动”压成一张控制面。

### 8. Goal Harness 的位置

Goal Harness 不是新的 agent framework。

它更像 long-horizon agent engineering 的控制面原型。

向下连接 repo、docs、experiments、runtime。

向上连接 operator、gate、reward、priority。

中间沉淀 goal state、run history、evidence、quota 和 delivery contract。

如果说模型能力决定单步上限，那么控制面决定长期协作下限。

这也是我现在对长程任务最大的 insight：

技术问题走到最后，会变成产品问题。

产品问题再往下挖，会逼出新的工程抽象。

GitHub 搜：`huangruiteng goal-harness`

## 标签

`#AIAgent` `#AI编程` `#Codex` `#ClaudeCode` `#Cursor` `#AgentInfra` `#开源项目` `#程序员` `#AI工作流` `#效率工具`
