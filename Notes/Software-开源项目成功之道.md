[toc]

# 开源项目成功之道

> 原书：John Mertic《Open Source Projects - Beyond Code: A Blueprint for Scalable and Sustainable Open Source Projects》（Packt, 2023）；中译《开源项目成功之道》（人民邮电出版社，孙振华、林旅强译，ISBN 978-7-115-65575-2）。
> 已读第 1–10 章。整理时间 2026-08-17；2026-08-21 增补 Kimi K3 License 与「开源上的再次发布」（我的拓展）；2026-08-23 补齐第 5、6、8、9、10 章。部分内容按我的理解补充拓展（Zowe 一致性计划、TiVo 化、Blender 募资等）。
> 相关已有笔记：非技术知识.md「开源」小节（Log4j 维护者、许可证速览）、Software-Engineering.md。

## 1 什么是开源，为什么要开源

### 1.1 开源不是“免费代码”，而是一种生产与协作模式

* 核心判断：开源的实质是“把开发过程开放给用户和协作者”，源码可见只是结果；用户、公司、社区共同决定项目走向。
* 历史时间线：
  * George Baldwin Selden：专利律师，1879 年申请“公路发动机”专利、1895 年获授权，主张覆盖所有汽油车并靠授权费收租；Henry Ford 被诉，1909 年初审败诉、1911 年上诉胜诉——法院把专利解释窄到 Brayton 两冲程发动机，Ford 的 Otto 四冲程不侵权。寓意：专利战能拖延产业，但挡不住技术事实与市场竞争。
  * 1955 SHARE：IBM 701 用户自发组织的用户团体，共享经验与代码，是早期“开放社区”雏形。
  * 1969：美国政府起诉 IBM 垄断；IBM 同年宣布软件与硬件分离计价，催生独立软件产业（1982 年以同意令和解）。
  * 1983：Stallman 启动 GNU 项目，目标是构建自由的 Unix 类操作系统；1985 年成立 FSF，1989 年发布 GPL。
  * 1991：Linus Torvalds 发布 Linux（借鉴 MINIX 的代码、概念和思想，放在 GPL 下）。
  * 1997：Raymond《大教堂与集市》——集中式规划的大教堂 vs 众包演进的集市。
  * 1998：OSI 成立，“Open Source Definition”确立（脱胎于 Debian 自由软件准则）；同年 Netscape 开源 Mozilla。
  * 1999：Apache 软件基金会成立，确立“委员会制 + 精英治理”的托管模式。

### 1.2 UNIX 理念：基础化、模块化

* 小工具只做一件事、通过文本流组合：grep / sed / cat。
* 现代延续：Android（Linux 内核 + 分层开源组件）、Ruby on Rails（gem 生态聚合）、Pandoc（转换器 + filter 组合）、Memcached（只做分布式缓存一件事）。
* 对 LoopX 的判断：带着集市开放姿态的大教堂——有统一架构与方向，同时开放 RFC/贡献流程。

### 1.3 为什么要开源：四个案例

* PHP：Rasmus Lerdorf 1994 年做“Personal Home Page Tools”，后改名 PHP: Hypertext Preprocessor；个人工具开源后成为整个 Web 生态的底座。动机：低门槛动态建站，个人需求变成公共基础设施。
* Blender：NaN 公司破产后，2002 年社区发起“Free Blender”募资，7 周筹到 €100,000，从公司买回版权，由 Blender Foundation 以 GPL 发布；此后靠 Development Fund 等可持续资助养活全职团队。开源把“将死产品”变成公共资产。
* Zowe：大型机（z/OS）与现代应用集成的开源框架，2018 年由 IBM 等发起，托管在 Linux Foundation 旗下的 Open Mainframe Project。动机：大型机现代化必须靠 ISV 生态，闭源集成层只会碎片化；开源降低第三方接入门槛，把竞争对手变成生态伙伴。详见 3.5、4.5 与文末《附：Zowe 案例详解》。
* PiSCSI：让树莓派模拟老式电脑 SCSI 磁盘/光驱的开源项目（RaSCSI 的 fork）。软硬件一体开源：PCB 设计、固件、工具、文档全部公开。说明开源不止代码，还包括硬件、规格与协作流程。

## 2 什么造就好的开源项目

### 2.1 Linux 的三个关键动作

* 站在前人肩膀上：借鉴 MINIX 的代码、概念和思想，而不是闭门造车。
* 第一个版本就是 beta 质量：尽早发布，接受不完美。
* 鼓励他人反馈和参与：把用户变成共同开发者。
* 类比“汽车的开放演进”：用户本身就是开发过程的一部分，项目按真实使用反馈迭代，而不是按假想需求设计。

### 2.2 开源的多种方式（光谱）

* 智能代码转储（smart code dump）：只把代码扔出来，没有社区流程与响应，基本不算“开源项目”。
* 开放核心（open core）：核心开源 + 商业增值部分闭源；需要明确边界，避免社区付出被单方面收割。
* 治理模型：仁慈独裁（BDFL，如早期 Linux / Python）vs 委员会（如 Apache）；后者牺牲决策速度，换稳定性与品牌中立。

### 2.3 fork、upstream 与冲突

* fork 是开源赋予的自由，但社区分裂对双方都是损失；优先合并回 upstream，除非方向确实不可调和。
* 避免/解决冲突的实操建议：
  * 过度沟通（over-communicate）；
  * 针对已知问题制定规则，不要为假设情况立法；
  * 把一切写下来（决策、流程、FAQ 都要文档化）；
  * 拥抱社群，而不是把贡献者当资源。
  * 警惕 bikeshed：琐碎议题的讨论会不成比例地膨胀（见非技术知识.md「思维模型」）。

## 3 开源许可证和知识产权管理

### 3.1 许可证（License）

* 宽松（permissive）：MIT / BSD / Apache 2.0——允许闭源再分发。
  * MIT：义务最少（保留版权与许可声明），主要作用是“发布软件不给自己添责任”。
  * Apache 2.0：在 MIT 之上显式包含软件专利授权——贡献者把专利许可授予下游用户，防止“先贡献、后用专利钓鱼”。
* copyleft（非宽松）：MPL（文件级）、GPL（作品级）、AGPL（网络使用也触发）。
  * Stallman 的四种自由：①自由使用；②自由研究/修改；③自由发布副本；④自由发布 fork 给所有人。
  * GPL：下游衍生作品必须保持同一许可证（Linux、Blender 等），不能把 GPL 代码改成闭源护城河。

### 3.2 TiVo 化 → GPLv3

* TiVo 化：厂商用了开源代码、也公开源码，但硬件只认自家数字签名，用户拿到源码也刷不进设备——“源码自由，设备锁死”。
* 出处：TiVo 公司的机顶盒内置 Linux（GPLv2），源码按协议公开、法律上挑不出毛病，但固件只认 TiVo 自己的数字签名——用户拿到源码也装不回设备，合规却让自由落空。
* 漏洞在 GPLv2：它要求“给源码”，不要求“改过的代码能在设备上跑”。
* GPLv3 补洞：消费类设备若内置 GPLv3 代码，必须提供 Installation Information（安装信息），让用户能运行修改版；给不出就不得使用 GPLv3 代码。
* 结果：Linux 内核至今留在 GPLv2，Android 手机、路由器、电视这类“开源内核 + 锁死硬件”的产品才能继续合法存在。
* 一句话：TiVo 化 = 用硬件锁抵消开源许可证，让“自由”只停留在纸面上。

### 3.3 copyleft 的价值判断（何时值得选）

* 让下游靠培训/服务赚钱，而不是靠卖副本赚钱。
* 进入竞争激烈、已有商业解决方案的领域时，防止“开源成果变成别人闭源护城河的垫脚石”——这是选择 copyleft 的核心理由。

### 3.4 版权与贡献签署：CLA vs DCO

* CLA（贡献者许可协议）：法律文件，声明贡献者可授权、授权范围明确；分 ICLA（个人）和 CCLA（公司），Apache 基金会等采用。例子：MongoDB 把协议改成 SSPL、Redis 部分模块加 Commons Clause（后转 RSAL/SSPL），本质都是收紧“谁可以用、怎么用”。
* DCO（开发者原创声明）：更轻量，Linux 内核用 Signed-off-by 表示“代码是我写的/我有权贡献”，不用律师介入。
* 品牌：商标由基金会托管，防止项目名被商业公司垄断；配套一致性计划（conformance program）保证品牌含义不变。

### 3.5 品牌一致性机会

* Kubernetes：每个自称 Certified Kubernetes 的供应商发行版都必须通过 CNCF 一致性测试，保证支持的 API 语义一致。
* Zowe Conformance Program（拓展）：
  * 由 Open Mainframe Project 管理：厂商按公开评价准则自测，提交结果由 OMP 官方审查，通过后获得 “Zowe Conformant” 徽章。
  * 按核心组件分类：API Mediation Layer / App Framework / CLI / Explorer for VS Code（新增 Explorer for IntelliJ、Client SDK），另有 Support Provider 认证。
  * 与 Zowe 大版本绑定：V1 / V2 / V3，每个大版本需重新认证，避免“名义兼容、实际分叉”。
  * 准则公开在 OMP GitHub（conformance test evaluation guide），任何人都可 PR 修改，形成社区共治的契约。
  * 收益：用户获得“通用功能、互操作性、体验一致”的预期；ISV 获得可信度；项目避免被“蹭名字”的产品稀释品牌。
  * 来源：[Zowe Docs v3.4: Zowe Conformance Program](https://docs.zowe.org/v3.4.x/extend/zowe-conformance-program/)、[zowe/community #2172](https://github.com/zowe/community/issues/2172)。
  * 完整案例（背景、治理、数据）见文末《附：Zowe 案例详解》。
* 参考资料：FOSSMarks、Linux 基金会、Software Freedom Law Center 相关文章。

### 3.6 Kimi K3 License：开放权重的定制商业许可（我的拓展）

* 事实：2026-07-27 月之暗面发布 Kimi K3（2.8T 参数开放权重模型），完整权重放 Hugging Face / ModelScope，代码仓库与权重统一使用自研 [Kimi K3 License](https://raw.githubusercontent.com/moonshotai/kimi-k3/main/LICENSE)（[GitHub 仓库](https://github.com/MoonshotAI/Kimi-K3)）。Hugging Face 把它登记为 `license: other` / `license_name: kimi-k3`（[模型卡](https://huggingface.co/moonshotai/Kimi-K3)），不是 OSI 标准许可证；官方口径说 "open-weight"（开放权重），不说 "open source"。
* 结构 = 宽松授权 + 两道商业触发条款 + 两类豁免：
  * 基础授权与 MIT 类似：免费使用、复制、修改、合并、发布、分发、再许可、出售，可运行、部署、微调、做衍生作品；义务是保留版权与许可声明、遵守适用法律。范围不仅含权重，也含配置、推理/训练代码和文档。
  * 触发 1（MaaS 收入门槛）：若被许可方或其关联方经营 "Model as a Service"（对外提供模型推理或微调，如 API，且第三方能对输入、参数或训练数据施加实质性控制），且集团连续 12 个月合计收入超 2000 万美元，则在商业使用前必须与 Moonshot 另行签署商业协议。MaaS 定义刻意收窄：终端产品内嵌能力、纯转发他人托管模型都不算。
  * 触发 2（品牌展示）：产品/服务月活超 1 亿，或月收入超 2000 万美元，须在界面显著位置展示 "Kimi K3"。
  * 豁免：纯内部使用（不向第三方提供模型、输出或能力）不受触发条款约束；通过 Moonshot 官方产品或认证推理合作伙伴访问也不触发。
* 与 K2 的演进：K2 是 [Modified MIT License](https://raw.githubusercontent.com/MoonshotAI/Kimi-K2/main/LICENSE)——只加了一条 100M MAU / $20M 月收入的品牌展示条款；K3 弃用 "modified MIT" 标签，新增 MaaS 收入分成门槛，把"大玩家要回来谈"从署名升级成合同义务。
* 设计逻辑：免费增值（freemium）式授权——研究、内部使用、中小团队无感；真正被瞄准的是云厂商、模型聚合平台、头部 Agent 公司这类"把开源权重变成规模化收入"的大鱼。关联方合并计算防分拆规避；认证伙伴豁免为生态合作留口子；微调出的衍生模型同样继承原许可约束。
* 行业趋势（2026-08 报道）：[钛媒体](https://www.tmtpost.com/8107377.html)称 Qwen3.8-Max 也改用类似定制 License（MaaS 或 AI Work Assistant 业务、集团连续 12 个月收入超 5000 万美元须另签；同样有品牌展示条款），DigitalOcean 等已与月之暗面签商业协议（分成比例未公开，报道称最高可达 30%，未经证实）；同期 DeepSeek V4、GLM-5.2 仍是标准 MIT。报道称中国大模型授权正从宽松 Apache/MIT 向定制商业许可迁移，变现从第一方 API 直销扩展到与云厂商分成。
* 对选型与实践的判断：
  * 对普通开发者、内部使用和 API 转发，K3 License 实际约束很小；但许可是版本依赖——K2 是 modified MIT、K3 是自定义、别的模型又可能是 MIT/Apache，产品栈应维护"模型许可证清单"。
  * 与标准许可对比：没有 Apache 2.0 式专利授权，也没有 copyleft；它是"宽松 + 商业阈值"的第三类，介于 MIT 与商业授权之间。把 K3 权重微调后对外做规模化 MaaS 会进入谈判区；仅做终端产品嵌入或转发官方/认证伙伴 API 则落在豁免区。
  * 对开源策略的启发：许可证本身也是产品分层工具——"免费 + 阈值"能同时获得生态分发与商业变现，代价是放弃 OSI 开源标签、标准依赖扫描与部分生态信任。
* 来源：[Kimi K3 License 原文](https://raw.githubusercontent.com/moonshotai/kimi-k3/main/LICENSE)、[Kimi K3 GitHub](https://github.com/MoonshotAI/Kimi-K3)、[Hugging Face 模型卡](https://huggingface.co/moonshotai/Kimi-K3)、[Kimi K3 官方技术博客](https://www.kimi.com/blog/kimi-k3)、[Simon Willison 解读](https://simonwillison.net/2026/jul/27/kimi-k3/)、[钛媒体：当开源大模型开始谈分成](https://www.tmtpost.com/8107377.html)。

## 4 向公司展现开源项目的商业价值

### 4.1 开明的自我利益（enlightened self-interest）

* 公司开源不是慈善，而是投资：通过开放非核心层换取生态红利，集中资源投入差异化核心。

### 4.2 公司开源的动机

* 摊薄开发成本；
* 更快支持客户想要的新功能；
* 更快推向市场；
* 公司可以集中投资核心内容。
* 例子：
  * Meta/Facebook：开源 PHP 运行时 HHVM、React、PyTorch 等共性设施，生态共建，自己聚焦产品与差异化。
  * Mac OS X：基于 FreeBSD 与 Mach 构建（抢占式多任务、受保护内存、访问控制、多用户），不必从零造操作系统。
  * Cloud Foundry → Pivotal Software：把 Cloud Foundry 打造成适用于任何云的多云 PaaS 标准，围绕标准建公司。

### 4.3 什么代码值得开源（决策因素）

* 非核心代码：外部参与可能获利；
* 有挑战的问题：希望获得广泛专业知识；
* 与公司正在使用的开源项目相关：可派生/回馈。

### 4.4 推动公司开源的操作路径

* 问题陈述 → 解决方案概述与商业案例 → 法律/工程/市场审查、预算、外部合作伙伴。
* 找盟友：预算盟友、技术盟友、执行主管/OSPO。
* 设预期：法律审查要留足时间；影响力需要长期投入，不是发布会开完就结束。
* 法律审查清单：第三方授权代码；软件专利；对贡献者的要求；公司是否需遵守许可证义务。
* 案例：COBOL 缺人维护 → 开源课程/培训吸引维护者；某公司数据库接口层不满足需求 → 物色现有开源项目贡献，而不是自研。

### 4.5 帮助竞争对手 vs 播种技术抢得先机

* 经典取舍：开源可能让竞争对手更快推出产品；但不开源，整个市场都长不大。
* Zowe 案例：IBM 选择后者——把大型机集成层开源、建立生态和一致性品牌，赌“市场扩大 + 心智领先”比“闭源独占”更值；ISV 成为伙伴而非对抗者。结果：一致性计划 2019 年启动后，截至 2024-10 有 77 个产品获 Zowe Conformant 徽章；Arcati 2024 年鉴显示 85% 的大型机组织已/将在 2024 年内采用 Zowe；Zowe Explorer 下载超 100 万。Broadcom 等原竞争对手反而成为共同贡献者与支持方。

### 4.6 衡量成功

* 用渐进式目标：贡献者数量、GitHub 社区指标、Bitergia、LFX Insights 等；先看趋势，不看单点爆发。

### 4.7 Mozilla × Rust：价值创造 ≠ 价值捕获（我的拓展）

* 时间线：2006 年 Graydon Hoare 在 Mozilla 做 Rust 原型 → 2009 年 Mozilla 正式资助（为 Servo / Firefox 找内存安全系统语言）→ 2015 年 Rust 1.0 → 2017 年 Firefox Quantum 首次大规模用 Rust（Stylo CSS 引擎）→ 2020 年 Mozilla 大裁员、Servo 转 Linux Foundation → 2021 年 Rust 基金会成立（Mozilla / AWS / Google / 华为 / 微软），商标与治理权归社区。
* 正向收益：
  * 技术自用：Firefox 性能与内存安全提升，安全漏洞减少；
  * 品牌 / 人才：系统编程领域的技术声誉和招聘招牌；
  * 使命：符合 Mozilla“健康开放的互联网”叙事。
* 没捕获到的：
  * 直接收入：MIT / Apache 双许可，无授权费，也没有互补商业产品；
  * 生态控制权：Rust 成为基础设施后，话语权归 Rust 基金会和大厂；
  * 经济价值外溢：AWS / 微软 / Cloudflare / Google 用 Rust 降本、卖服务，还接走了 Mozilla 培养的核心团队；
  * Firefox 商业模式未被拯救，公司仍依赖 Google 搜索合作分成。
* 判断：对行业和使命是成功，对公司财务是负 ROI 的公共品投资——典型的“开源价值外溢”案例，与 Zowe 的成功（文末附录）形成对照。
* 可复用结论：开源公司要捕获价值，不能只靠“技术自用 + 品牌”；要么有互补收入（云 / 服务 / 咨询），要么有标准 / 生态话语权，否则价值会被下游基础设施玩家拿走。

## 5 治理和托管模式

* 引言（丘吉尔）：「如果你有 1 万条法规，就会破坏人们对法律的所有尊重」——治理规则宁少勿滥，规则要少而准。

* 治理模式（光谱）：
  * 行动至上模式（action-first）：先做事、后立规，围绕实际动作组织社区，适合早期项目；
  * BDFL（终身仁慈独裁者，Benevolent Dictator for Life）：一个人拥有最终决定权，决策快但依赖个人，Linux 早期是典型；
  * 技术委员会（TSC）：把决策权交给一组人，分散单点依赖；
  * 选举模式：有任期的选举，适合个人与公司利益冲突的场景；Apache Way 的做法是公开讨论 + 共识，投 `-1` 票必须说明理由；
  * 单一供应商模式：一个公司主导，常见于实用型项目、开放核心模式，或「开源换反馈与兴趣」的获客策略；
  * 供应商中立的基金会：把项目托管给中立组织，防止单家公司控制。

* 角色：用户、贡献者、维护者、领导者
  * 维护者：了解代码、帮助完善代码、判断代码、关注可维护性与安全问题；
  * 领导者：确立方向、解决冲突、平衡优先事项、为社群服务——服务型领导者（servant leadership）。

* 治理结构示例：
  * Rust RFC：流程公开、可发现性好，兼顾简单性与灵活性；
  * Zowe：领导者从 PM 转向研发——技术治理更容易获得贡献者信任（详见文末附录）。

* 财务支持：
  * 小费式捐赠；
  * 众筹：Blender 是经典案例——需要合法组织（基金会）接收捐赠；
  * 单一组织资助：e.g. Mozilla 裁撤 Rust 员工——单点资助意味着组织裁员会直接打击项目；
  * 基金会：e.g. Python Software Foundation（管理 PyCon、处理 Python 项目法律事务、为开发提供资助）与 LFE；PSF 是 501(c)(3)、LFE 是 501(c)(6)，对前者捐赠可抵税；配套技术咨询委员会（TAC）。

## 6 让你的项目备受欢迎

* 「欢迎马车」（welcome wagon）：把欢迎新贡献者做成仪式/流程，e.g. Hyper 项目主动引导新人上手。
* 有效支持最终用户：
  * 用 stale issue 这类 GitHub Action 自动标记过期 issue，保持 issue 可追踪；
  * 理解用户需求、积极主动帮忙、融入社区、有同理心；
  * e.g. OpenStack 靠社群与开发者管理胜出，成为市场领导者，压过 Apache CloudStack。
* 商业支持：Red Hat、SUSE 等发行版；Kubernetes 生态的 KCSP（认证服务商）。
* 参与到对话中：主动发现讨论、分享讨论，把社区对话当成产品的耳朵。

## 7 将贡献者发展为维护者

* 导师制：暑期导师项目（Google Summer of Code、Outreachy、Season of Docs 等）是把新人“扶上马”的成熟路径：结构化任务 + 专人辅导 + 社区资源。
* 维护者的能力不只有技术：
  * 技术知识：能评审、能定方向；
  * 公共演讲/布道：能代表项目对外沟通；
  * 社群管理：能处理冲突、授权、带人。
* 成长路径本质：从“做贡献”到“做判断、带人、定规则”；项目要主动把责任和信任移交，而不是等贡献者自己抢。

## 8 处理冲突

* 理解人及其动机——大脑是「情绪系统 + 理性系统」的组合：
  * 边缘系统（limbic system）：冲动、反应和纯粹的情感，先触发；
  * 前额叶（prefrontal cortex）：决策、规划、短期记忆，后参与；
  * 神经多样性：孤独症谱系障碍（ASD）等是神经发育差异，不是缺陷；文化和生活经历塑造每个人的行为。
  * 大脑分区图与生物学背景见 [Anatomy-大脑与神经科学.md](./Anatomy-大脑与神经科学.md)。
* 解法是包容性决策：
  * 开放的沟通和协作；
  * 明确的决策方法论——「牧猫群」（herding cats）要变成有序、包容的过程；
  * 讨论 → 投票 → deadline 的组合；注意决策讨论期间的信噪比。
* 具体策略：
  * 细化问题、持合作态度、分析和解决问题；
  * 关注「有投票权但没参与投票的人」（沉默的多数）；
  * 会纠偏、知道什么时候停；
  * 纠正有害行为：e.g. 安静倾听 10 分钟，先听再回应；
  * 倾听、警惕无意识偏见、有意识地处理有害行为。
* 其它：
  * 冲突也可能激发创新——哪怕是竞争对手供应商之间；
  * Contributor Covenant（贡献者公约）：开源界事实标准的 code of conduct 模板，Coraline Ada Ehmke 2014 年发布，现 v2.1，GitHub 把它作为社区健康默认模板，几百万仓库在用。结构：承诺（Pledge，无骚扰、包容的环境）、标准（Standards，鼓励行为 vs 不可接受行为）、适用范围（Scope，所有社区空间 + 代表项目对外发言）、执行（Enforcement，举报渠道、处理流程、分档后果、举报者隐私）。

## 9 应对增长

* 四个维度：认知度、采用度、贡献多样性、领导力扩展；加上避免倦怠。纠正「stars、PR 数量和真实采用是一回事」的错觉。
* 社群会议的目的：更新发布 / 开发进度 / 特别兴趣小组（SIG）动态；展示相关项目与工作；表扬对社群有显著影响的成员。
* 衡量增长（Peter Drucker：「不能衡量就无法管理」）：
  * 认知度：用 CHAOSS 分析社区健康度；
  * 采用度：商业项目遥测不受欢迎；早期看 issue 与新增贡献者，成熟期看 blog、自媒体、公开项目推荐和组织公开采用声明；
  * 「让某人认同自己是用户并公开倡导别人使用，是很高的门槛」；
  * 多样性：组织、维护者、代表性不足群体的参与。
* 增强和扩展领导力：
  * 从项目通才到项目专家，关注长期机遇；
  * 低成本领导力入口：CLA assistant、写文档、外联资源、做演示文稿；
  * 时间与预期管理：把人力投入进度落后的软件项目只会延迟工期（工作流程不流畅、目标不明确）；想清楚要更多资源还是专门资源；
  * 避免倦怠。

## 10 开源商业化

* 商业化是项目价值的验证：项目持续发展 → 组织投资、内部使用、构建进自己的产品。*Every good work of software starts by scratching a developer's personal itch*（Raymond）。
* FLOSS 与商用的张力：
  * 公司商用开源却不回馈社群 → 「利用和掠夺开源」的敏感问题；
  * 常见化解：1）围绕软件提供服务与支持；2）开放核心模式；3）TiVo 化（负面案例，见 3.2）。
  * 循环：项目 → 产品 → 利润 → 项目；技术 → 产品 → 市场 → 参与者 → 开发者社群 → 技术。
  * 利润价值：1）降低软件开发成本；2）扩展潜在市场；3）加快上市时间。
* 商业化模式：
  * 作为更大商业软件包的依赖项 / 组件（e.g. FOSSology）；
  * 服务和支持；
  * 开放核心。
* 为商用设置项目：
  * 品牌和知识产权管理；
  * 认可与一致性计划：认可供应商；一致性计划能帮项目从市场营销拿预算、募集资金（呼应 3.5 与 Zowe 附录）。

## 11 开源上的“再次发布”（我的拓展）

* 核心观察：开源产品的“发布”不是一次性事件。每当行业出现一个新概念（agent harness、platform、统一模型格式），同一产品都有机会借这个概念窗口再发布一次——重写定位、收口入口、补文档和案例，重新获得一轮新闻 / 搜索 / GitHub Trending 曝光。旧 star 与旧社区是现成流量池，重启叙事的成本远低于开新项目。

### 11.1 OpenAI Codex：从开源 CLI 到 “Codex as a platform”

* 时间线：2025-04-13 创建仓库并开源 Codex CLI（Apache-2.0，[github.com/openai/codex](https://github.com/openai/codex)，2026-08-21 约 109k stars）；2026-08-18/19 官方博客《[Codex as a platform: build on the open agent harness](https://developers.openai.com/blog/codex-as-a-platform)》（Nicolas Bonamy、Derrick Choi）宣布平台化。
* 这次“再次发布”的实质是平台化收口，源码本身此前已逐步开放：
  * 把可复用资产明确为 agent loop / harness：管理对话状态、流式执行、工具调用、sandbox 与 approval 边界、跨 turn 延续；并给出 harness 设计改变结果的证据——ARC-AGI-3 上 retained reasoning + context compaction 把 GPT-5.6 Sol 从 13.3% 提到 38.3%，输出 token 降为 1/6。
  * 收口成三个集成入口：
    * `codex exec`：CI / 脚本 / 一次性后台任务，跑有界 agent workflow、返回结构化输出；
    * Codex SDK（TypeScript / Python）：在应用代码里启动、恢复、流式消费任务；
    * Codex app-server：产品内嵌 agent runtime——本地 Codex 进程 + 持久会话 + 事件流 + 打断 + 暴露工具 + 审批处理（JSON-RPC 客户端协议）。
  * 开源组件清单化（CLI / app-server / SDK + [open-source components guide](https://developers.openai.com/codex/open-source)），并划清边界：开源层是 harness 与集成面，模型访问和托管服务保持独立。
  * 架构叙事 + 示例：应用拥有 UI、业务上下文、MCP 工具和审批，harness 只提供 agent loop 与 sandbox 执行（官方示例 Relay 操作台）。
  * 落地信号：[GitHub / JetBrains 把 Codex 作为 IDE 的 agent provider](https://github.blog/changelog/2026-07-07-codex-as-agent-provider-and-agentic-enhancements-in-jetbrains-ides/)、[Cisco App Builder 使用 Codex SDK](https://blogs.cisco.com/ai/from-an-idea-to-a-live-app-on-cisco-in-minutes)、[Thrive Holdings & Crete 的税务 agent pilot 处理 7000 份报税、时间降约 1/3](https://openai.com/index/building-self-improving-tax-agents-with-codex/)。
* star 表现：2026-04 约 75.6k → 5-10 约 81.9k（[zengineer 周报](https://zengineer.blog/blog/tech/ai-agentic-weekly-github-20260510/)）→ 7-14 约 97.7k（[dev.to](https://dev.to/theagentbeat/the-33000-token-tax-a-30-hour-star-race-and-where-agents-actually-fail-468p)）→ 7-22 约 100.4k（[whatstrending](https://whatstrending.ai/repos/openai/codex)）→ 8-21（平台化发布后数日）约 107.4k（[cnblogs](https://www.cnblogs.com/vibecodinghuanzhe/p/22608989)）→ 8-21 GitHub API 快照 109,384。曲线在发布前就已陡增，这次再发布的增量更多在定位、入口和生态叙事，而非 star 爆发。

### 11.2 DeerFlow 2.0：从 Deep Research 到 Super Agent Harness

* v1（2025-05 发布）：定位 Deep Research 框架，7 天 10k stars，累计约 15.8k 后热度回落。
* 2.0（2026-02-28）：README 明确 “a ground-up rewrite. It shares no code with v1”；叙事是社区把 v1 用成了 harness（数据 pipeline、slide deck、dashboard、内容自动化），所以从 “framework you wire together” 重造为 “super agent harness — batteries included, fully extensible”（基于 LangGraph / LangChain）。
* 这次再次发布的内容：
  * 定位重写：Deep Research → Super Agent Harness；
  * 能力重新打包：skills（Markdown 定义工作流、按需渐进加载）、sub-agents（独立上下文 / 并行 / 结构化回报）、sandbox（Docker 隔离 + 文件系统 + 审计）、context engineering、long-term memory、MCP、IM channels（Telegram / Slack / Feishu）、Gateway 模式、CLI-backed providers（Codex CLI / Claude Code / DeepSeek 等）、InfoQuest 搜索集成；
  * v1 保留在 1.x 分支继续维护，主动管理版本分裂。
* star 表现：发布当日登 [GitHub Trending #1](https://github.com/bytedance/deer-flow)；3-29 48k+（发布一个月内，[网易解读](https://www.163.com/dy/article/KP68FDIR05568W0A.html)）→ 4-03 57.9k+（[h3blog](https://www.h3blog.com/article/758/)）→ 5-27 约 70k（[cnblogs：三个月逼近 7 万](https://www.cnblogs.com/itech/p/20206290)）→ 6-28 73.8k（[腾讯云开发者](https://cloud.tencent.cn/developer/article/2699825)）→ 8-21 GitHub API 快照 80,442。与 v1 平台期形成鲜明对比，是“同一产品第二次陡增”的典型曲线。
* 来源：[DeerFlow README（From Deep Research to Super Agent Harness 一节）](https://github.com/bytedance/deer-flow/blob/main/README.md)、[v1 发布：7 天 10k star 回顾](https://zhuanlan.zhihu.com/p/2021122968340764270)。

### 11.3 更多例子（支持与对照）

* 口径说明：以下 star 数字均为对应日期的第三方报道或 GitHub API 快照（8-21），非精确历史曲线，用于看量级和趋势。
* vLLM V0 → V1（2025-01，随 v0.7.0 发布）：核心引擎 ground-up rewrite，用 “V1 engine” 概念再发布并成为默认引擎（[官方博客](https://vllm.ai/blog/2025-01-27-v1-alpha-release)，吞吐最高提升 1.7x）。star 增长：2024-12 约 31k（[PyTorch 博客](https://pytorch.org/blog/vllm-joins-pytorch/)）→ 2025-09 超 77k（[CSDN 转载报道](https://www.python88.com/topic/187158)）→ 2026-08-21 API 快照 89,596；Linux Foundation 口径下 2025-05 起一年内新增约 53.4k stars（[LFX Insights](https://insights.linuxfoundation.org/project/vllm/popularity?timeRange=past365days&start=2025-05-01&end=2026-05-01&widget=stars)）。V1 没有营销化包装，靠工程口碑和默认引擎切换，增长与推理/agent 需求大盘同步，难以把增量单独归因给某次发布。
* OpenDevin → OpenHands：2024-03 以 Devin 开源替代品启动；2024-09-05 更名 OpenHands 时 30k+（[TechCrunch](https://techcrunch.com/2024/09/05/all-hands-ai-raises-5m-to-build-open-source-agents-for-developers/)）→ 2025-03 一周年 50k+（[One Year of OpenHands](https://www.openhands.dev/blog/one-year-of-openhands-a-journey-of-open-source-ai-development)）→ 2025-12-21 65,846（[wal.sh 2025 Terminal AI Agents 调查](https://www.wal.sh/research/2025-terminal-ai-agents/)）。2025-12-16 v1.0 基于新的 software-agent-sdk 重写，替换原 pub/sub EventStream 架构，重新包装为“cloud coding agents 开放平台”（[1.0.0 release](https://newreleases.io/project/github/OpenHands/OpenHands/release/1.0.0)）；到 2026-08-21 API 快照 84,662，v1.0 前后约 8 个月增约 18.8k，增长叠加 A 轮融资与 SDK 重构叙事，工程里程碑本身不是唯一驱动。
* llama.cpp：GGML → GGMF → GGJT → GGUF 格式迭代（GGUF 于 2023-08-21 合并进主仓，[PR #2398](https://github.com/ggerganov/llama.cpp/pull/2398)），同一引擎随“统一模型格式”概念反复发布，成为本地推理事实标准。star 增长：2023-06 超 30k（[eeworld 报道](https://en.eeworld.com.cn/mp/QbitAI/a217505.jspx)）→ 2024-10 超 65k（[NVIDIA 博客](https://developer.nvidia.cn/blog/accelerating-llms-with-llama-cpp-on-nvidia-rtx-systems/)）→ 2026-08-21 API 快照 124,935。缺 GGUF 前后周级精确快照，单次格式发布难以单独归因；增长更依赖生态地位与本地推理需求。
* 对照 AutoGPT：2023-03 现象级首发；2024-05 约 156k（[OpenUK fireside](https://openuk.uk/thought-leadership/fireside-chat-toran-bruce-richards-2024-phase-one/)）→ 2024-12 约 169k+（[ITU：State of open (UK 2024)](https://aiforgood.itu.int/ai_digital_library/state-of-open-the-uk-in-2024-phase-four-ai-openness-end-of-year-update-2024/)）→ 2026-08-21 API 快照 186,694。2024-09 以 “AutoGPT Platform”（无代码 agent 平台）概念再发布，但发布前 4 个月到 2024 年底仅增约 13k，2024 年底到 2026-08 约 20 个月增约 17.7k，都远慢于首发期——说明再次发布 ≠ 自动获得第二曲线；概念窗口必须有真实交付物支撑。

### 11.4 为什么有效 / 风险

* 新概念 = 新心智入口：每个新词（harness、platform、V2、V1 engine、统一格式）都是一次新的搜索 / 新闻 / Trending 窗口；旧 star 与社区是现成分发基础。
* 再次发布通常做三件事之一：定位/概念重写（DeerFlow）、入口与文档收口（OpenAI Codex）、核心架构换代（vLLM V1、OpenHands 1.0）。
* 风险：概念空心化（有新词没新交付，AutoGPT 式）；社区疲劳；版本/社区分裂（DeerFlow 把 v1 放到 1.x 分支）；“platform”标签通胀。
* 可操作判断：当出现与自身能力匹配的新概念时，优先把已有资产重新收口发布（README、入口、文档、示例、客户案例），而不是开新仓库；验收标准是“新概念有真实交付物 + 明确集成入口 + 已有资产被复用”。
* 衡量口径：star 只是漏斗顶部信号，判断再发布是否有效还要配合下载量、贡献者、厂商/客户采用和生态集成（见 4.6），否则容易把“新闻窗口”误判成“价值窗口”。

## 附：Zowe 案例详解

### 背景与问题

* 大型机（z/OS）承载银行、保险、政府等核心业务，但开发工具和集成方式老旧：API 少、DevOps 工具链不兼容、新一代开发者不愿碰。
* 若 IBM 和各家 ISV 各自做集成层，市场会碎片化：客户被锁定、生态长不大，大型机在“云原生优先”时代被进一步边缘化。

### 为什么开源（决策）

* 2018-08-27，Open Mainframe Project（Linux Foundation 旗下）在 Open Source Summit 发布 Zowe——第一个基于 z/OS 的开源项目；IBM、CA Technologies（现 Broadcom）、Rocket Software 是主要发起贡献者。
* 取舍：开源会让竞争对手更快推出产品，但能统一接口标准、降低第三方接入门槛、把 ISV 从对抗者变成生态伙伴。IBM 赌“市场扩大 + 心智领先”胜过“闭源独占”。

### 产品形态

* Zowe = 面向 z/OS 的现代集成框架，核心组件：
  * API Mediation Layer：统一 REST API 网关/服务目录，让大型机能力像云平台 API 一样被调用；
  * Application Framework（Zowe Desktop）：浏览器里的桌面式管理界面；
  * Zowe CLI：命令行操作 z/OS；
  * Zowe Explorer：VS Code / IntelliJ 插件，让开发者在熟悉的 IDE 里工作；
  * 外加 Java / Kotlin / Node.js Client SDK。
* 治理：贡献者主导（contributor-led）——技术委员会（TSC）管技术，咨询委员会（ZAC）管方向与品牌；社区成员包括 IBM、Broadcom、Rocket Software、Phoenix Software、Vicom Infinity 等。
* 发布：V1 于 2019 年 GA → V2 → V3 LTS（2024-10-03）。V3 把 API Mediation Layer 从 Netflix Zuul 换成 Spring Cloud Gateway、刷新 Desktop 前端、推出安装向导与季度发布节奏，并结束 V1 支持。

### 一致性计划 = 生态契约

* 2019 年启动 Zowe Conformance Program：自测 + OMP 官方审查 + 版本化徽章，按组件分类认证（详见 3.5）。
* 结果：截至 2024-10，77 个产品获得 Zowe Conformant 徽章；另有 Support Provider 认证（Broadcom、IBM、Rocket、IBA Group 等）。Broadcom 甚至向客户免费提供 Zowe 企业级支持——竞争对手变成生态的共同投资者。

### 结果与数据（2024 快照）

* Arcati Mainframe Yearbook 2024：85% 的大型机组织已采用或将在 2024 年底前采用 Zowe。
* Zowe Explorer for VS Code：下载超 100 万、活跃用户 15 万+；Zowe CLI 2024 年下载超 10 万；IntelliJ 插件接近 1 万；Docs 年访客近 5 万。
* 2024 年 330 位独立贡献者（LFX Insights；2020 年为 367），属于成熟期正常收敛。
* 来源：[OMP：Zowe 发布公告](https://openmainframeproject.org/press/open-mainframe-project-announces-the-launch-of-zowe-an-open-source-framework-that-strengthens-integration-with-modern-enterprise-applications/)、[Linux Foundation：Zowe LTS V3 发布](https://www.linuxfoundation.org/press/open-mainframe-project-announces-zowes-lts-v3-release)、[OMP：2024 是 Zowe 生产化采用之年](https://openmainframeproject.org/blog/2024-the-year-of-production-adoption-for-zowe/)、[OMP：Zowe Conformant Support Provider Program](https://openmainframeproject.org/our-projects/zowe-conformant-support-provider-program/)。

### 可复用判断

* 老平台 + 新生态：如果平台市场本身在缩小，独占集成层只会加速边缘化；开放接口 + 一致性品牌能把“存量护城河”换成“增量生态权”。
* 光开源代码不够：品牌、徽章、兼容性测试决定了“Zowe 兼容”是否可信，一致性计划是抗碎片化的关键治理工具。
* 竞争对手可以变成共同投资者：Zowe 的主要贡献者正是原来互相竞争的商业厂商（IBM / Broadcom / Rocket）。

## 对 LoopX / 个人开源实践的借鉴

* 一致性程序 = 公开契约 + 自证 + 官方审查 + 版本化徽章：可迁移到 agent benchmark / harness 生态（LoopX 的 adapter conformance 同思路，见 AI-Agent-Engineering.md）。
* 治理上：统一架构/方向（大教堂）+ 开放 RFC/贡献（集市）可以共存。
* 衡量上：用渐进式社区指标代替“star 数崇拜”；把用户/贡献者当开发过程的一部分。
* 价值捕获：开源创造的价值 ≠ 自己捕获的价值；要设计互补收入或生态话语权，否则价值外溢（Mozilla × Rust 为反面案例）。
* 概念窗口再发布：LoopX 的 harness / benchmark / conformance 能力也应在新概念出现时收口重发（新入口 + 新文档 + 真实案例），而不是只开新仓库；参考第 11 节，避免 AutoGPT 式“只有概念没有交付”。
* 商业化校准（第 10 章）：用「服务支持 / 开放核心 / 生态组件」三个模式对照 LoopX——哪些继续开放（harness 内核、benchmark 口径），哪些适合形成托管控制面、企业治理和连接器；一致性计划既服务生态，也能从市场预算为项目募资（呼应 Zowe 附录）。
* 治理与冲突（第 5、8 章）：早期用行动至上 + 单一权威快速推进，成熟后向技术委员会 / 基金会过渡；冲突处理先让情绪落地（边缘系统），再做包容性决策，注意沉默多数与信噪比。
