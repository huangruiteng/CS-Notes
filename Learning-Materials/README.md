# 学习素材

这里保存当前学习队列中的公开材料：论文、代码、官方文档、公开文章，以及可分享的自制讲义。长期知识结论仍归入 [Notes](../Notes/)。

- [学习队列：Top30 与 ranked backlog](./QUEUE.md)：建议阅读顺序，每条是独立学习单元。
- [其余候选](./CANDIDATES.md)：已收录但尚未排名，不把浏览序号当优先级。
- [机器可读目录](./catalog.json)：稳定材料 ID、来源、档位、生命周期、读取范围与队列内排名。
- [数据库与分布式系统补课](./distributed-systems-for-loopx/补课讲义.md)：17 节讲义，配套[练习与四周路线](./distributed-systems-for-loopx/练习与讨论.md)和[可运行实验](./distributed-systems-for-loopx/recovery_lab.py)。
- [跨境数字支付机制导读](./payment-mechanisms/跨境数字支付机制导读.md)：约 2—4 小时，串起授权、请款、清算、3DS、自动续费、退款争议与三种余额，配流程图、余额推演和纸面练习。
- [商业传记与通识书目](./booklists/business-biography-and-general-knowledge.md)：6 本书的书名清单。

S 表示优先亲读，A 表示先读摘要、按需追原文，B 表示背景索引，U 表示未读。这是学习分档，不是事实可信度评级。来源为二手观点或未核实线索时，仍需回到一手材料验证。

公开版只收录经过字段审查的书目、学习提示和公开链接。公司材料、私人批注、原始截图及无法确认公开性的资源留在私有队列；历史归档不在本目录展示。同一材料同时有公开论文和内部讨论时，公开版只引用可核验的公开来源。

“沿用既有阅读记录”表示迁移时保留原有材料入口，不表示本次重新精读了原文，更不表示学习者已掌握。正文未读、只看元信息、公开摘要页核验、全文审查和实验运行是不同状态。链接中的分享与登录参数已去除；旧链接可能失效，迁移不保证所有外链目前可访问。

公开目录是受管 catalog 的审查后投影；私有原文和审计证据不会从这里反向恢复。相同链接可能对应不同历史记录或阅读单元，按稳定 ID 保留，不静默去重。必要时使用经审查的公开 ID，来源 ID 映射保留本地。内外队列分别连续编号，保留各自原有相对顺序。

## 阅读与维护

队列同时考虑近期可验证产物、长期研究价值与基础能力，不只按新鲜度或工程紧急程度排序。Top30 是选读入口，不是三十项并行任务；需要补哪个概念，先用推导、故障反例或小实验检查，再决定阅读深度。

| 学习线 | 入口与读法 | 最小产物 |
| --- | --- | --- |
| 因果与贡献识别 | [What If](https://miguelhernan.org/whatifbook) 选读 §1.1–1.2、§2.1、§3.1–3.3、§3.6，按需追 §2.4 | 写一页实验协议：比较单位、干预、分配、结果窗口和识别假设；区分相关与贡献 |
| 记忆与上下文诊断 | [PAIR](https://arxiv.org/html/2609.36526v1) 的成对延续；[CMP v3](https://arxiv.org/html/2610.02070v3) §2–3 与附录 I/J 的暴露干预和限制 | 明确可恢复状态、上下文预算和旁路信息；区分未召回、被使用与条件收益 |
| 延迟信用分配 | [RUDDER](https://arxiv.org/html/1806.07857v3) §2–3 与限制，按问题触发阅读 | 在同一短轨迹上分开标注终局结果、预测贡献与可干预动作，不将预测分解当因果证明 |
| 系统基本功 | [分布式系统 × LoopX 讲义](./distributed-systems-for-loopx/补课讲义.md) → [练习](./distributed-systems-for-loopx/练习与讨论.md) → [Recovery Lab](./distributed-systems-for-loopx/recovery_lab.py)；先状态机、事务、幂等与 fencing，再日志、共识和恢复 | 预测故障结果，解释修复所依赖的条件 |
| 个人支付基本功 | [跨境数字支付机制导读](./payment-mechanisms/跨境数字支付机制导读.md)；先交易生命周期，再认证/续费与资金边界，按已有知识跳读 | 解释占用与扣款、首付与续费、卡余额取回与法币退出的区别，完成纸面案例 |
| 概率与序贯决策 | [Bandit Algorithms](https://tor-lattimore.com/downloads/book/book.pdf) 选读 §5.3、§7.1、§33.1–33.2，按需补 §3.3；能完成推导则跳读 | 写清目标、观察、预算、停止与最终选择；辨认独立、平稳等假设 |
| 矩阵与表示 | [Mathematics for Machine Learning](https://mml-book.github.io/book/mml-book.pdf) §2.6、§4.5–4.6，按需补 §3.8；已有 SVD 笔记可先诊断跳读 | 手算低秩截断误差，解释矩阵近似目标与下游损失的关系 |
| 优化原理 | [Boyd & Vandenberghe](https://web.stanford.edu/~boyd/cvxbook/bv_cvxbook.pdf) §3.1 → §4.2 → §9.3，按需补强凸和线搜索前提 | 用二维二次目标检查条件数、步长、驻点与收敛结论；列出前提 |
| 信息与压缩 | [Stanford EE376A](https://web.stanford.edu/class/ee376a/files/lecture_notes.pdf) §2.3 → [MIT 6.441 Chapter 23](https://ocw.mit.edu/courses/6-441-information-theory-spring-2016/resources/mit6_441s16_chapter_23/) §23.2；已知熵/KL可跳过基础定义 | 明确源、编码、任务变量和失真，区分平均损失与关键事件的尾部风险 |
| 持续学习与联合演化 | 按队列选读 Dream-RSI、SkillOpt-Lite / HarnessOpt、HGM、Fast Weight Attention、EvoTrainer；先机制、假设、关键对照，再源码 | 画出更新对象、反馈与采用路径，提出一个可推翻假设的对照 |

已有 [RL 笔记](../Notes/Reinforcement-Learning.md)可用于定位 MDP/POMDP、信用分配与离策略评估概念。实现目录和重复综述可以由助手先整理；亲读重点放在决定问题如何定义、证据如何成立的部分。已读材料继续作为参考时标明回看目的，不重新列为首读任务。

[数学笔记](../Notes/mathematics.md)已有 SVD、熵与 KL 的复习入口；新增材料各对应独立的章节选读单元，按诊断结果选择深度。上述教材与课程不要求整本或整门并行阅读，理论保证须与实际模型、搜索和压缩任务的假设分别核对。

从仓库根目录运行实验：

```bash
python3 Learning-Materials/distributed-systems-for-loopx/recovery_lab.py
```

从公开目录重建或检查 Markdown，不需要 LoopX 及维护者私有状态：

```bash
python3 note-system/materials/material_queue.py
python3 -s note-system/materials/material_queue.py --check
python3 -m unittest discover -s note-system/materials/tests -p 'test_material_queue*.py'
```

`catalog.json` 是公开副本的渲染输入，`QUEUE.md` 和 `CANDIDATES.md` 是生成文件。维护者新增、归档或调序时，先更新受管 catalog，再审查公开字段并刷新投影；不能只手改生成表格。未经审查的新记录、正文版本变化或材料重新激活，默认保留在私有侧，不能继承旧版本的公开许可。

经核验的公开素材默认在当次工作流完成字段审查并进入公开队列。用户已读材料经受管流程归档后移出当前排名；明确保留的已读参考注明复习用途并放入 backlog。助手的读取范围不代表用户已经读完。

归档须有对应材料的用户完成声明或能追溯到该声明的远端记录。远端队列缺少条目、PR 的批次摘要或已有笔记不能代替完成证据；同步时先区分本地新增与远端删除，保留尚未提交的素材。

分区、预览、版本检查、恢复与测试的通用代码也在仓库中，见[素材体系维护](../note-system/materials/README.md)；真实来源绑定与逐条审查记录留在本地。

目前两个队列共用材料生命周期与全局阅读顺序，再按公开范围筛选。它们不是独立的多租户权限系统，也没有第二套归档 authority。未来若需要不同 owner、独立排序政策或不同存储 provider，应再扩展 LoopX 的 queue identity 与授权契约；当前无需为展示分区重写核心 capability。
