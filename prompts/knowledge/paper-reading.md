# Paper Reading Prompt

适用场景：让 agent 先读论文，再输出机制摘要、核心设计和用户最小阅读路径。

```text
请你先阅读这篇论文/研究材料，再给我机制导向的精读摘要。

# 材料

{论文链接或正文}

# 输出要求

1. 一句话判断：这篇材料真正解决什么问题，是否值得我本人亲自读原文。
2. 我实际读了什么：HTML / PDF / repo / code / figures / tables / appendix，以及哪些部分未读。
3. 精要内容：问题设定、系统边界、输入输出、数据构造、训练或评测流程、指标、baseline、主要结论和限制。
4. 核心机制：3-6 个机制抓手，每个都说明作者怎么做、怎么证明、我应该怎么理解。
5. 对我的 artifact 的直接改造：schema、feedback signal、benchmark variant、TODO、steering 或 deep dive 论点。
6. 我本人还需要读什么：必须亲自看 / 有空再看 / 可以跳过，尽量具体到 section、figure、table、code path。
7. 边读边核验的问题：3-6 个尖锐问题，帮助后续读完闭环。
```
