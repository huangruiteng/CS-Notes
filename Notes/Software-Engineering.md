# Software Engineering


[toc]

## Intro

> todo 《A Philosophy of Software Design》
>
> todo 《Software Design X-Rays》
>
> 开源项目运营、许可与商业价值 → [Software-开源项目成功之道.md](Software-开源项目成功之道.md)

### Intro

*  the three most impactful points are interfaces, stateful systems, and data models.

### Interfaces

* *Interfaces* are contracts between systems. Effective interfaces decouple clients from the encapsulated implementation. Durable interfaces **expose all the underlying essential complexity and none of the underlying accidental complexity**.
* Delightful interfaces are [Eagerly discerning, discerningly eager](https://increment.com/apis/api-design-for-eager-discering-developers/).

### State

* *State* is the hardest part of any system to change, and that resistance to change makes *stateful systems* another critical leverage point. State gets complex faster than other systems and has an inertia that makes it relatively expensive to improve later.
* 安全隐私合规：As you incorporate business obligations around security, privacy, and compliance, changing your stateful systems becomes even more challenging.

### Data models

* *Data models* are the intersection of the interfaces and state, constraining your stateful system’s capabilities down to what your application considers legal.
* A good data model is rigid: it only exposes what it genuinely supports and prevents invalid states’ expression.
* 兼容性：A good data model is tolerant of evolution over time.
* Effective data models are not even slightly clever.

* Domain state 与 projection metadata 按语义归属分层，不能只按“是否出现在 UI”分类。任务的 `archive_state` 若决定是否进入活跃工作集，就属于持久化业务状态；`source_section`、文档内 `index` 属于展示位置。若排序本身表达业务优先级，则应另建 domain 字段。移除 renderer 后仍需保留、参与决策或审计的字段，不应要求 adapter 临时伪造。可参考 [Todo domain / projection contract](https://github.com/huangruiteng/loopx/blob/e3f9b5366015f6ad7ae306f8b01fc6e2b3e3806b/loopx/control_plane/coordination/coordination_state_contract.ts)；投影同步边界见下文 Outbox。



### A/B Testing

#### 实验设计

* **核心原则**：确保实验组 (Experiment) 和对照组 (Control) 在统计学上的同质性 (Homogeneity)，唯一变量是实验策略。
* **流量分配**：通常基于 Hash(User_ID) % 1000 进行分桶。
* **分流模型**：
  * **正交分层**：不同层级的实验（如 UI 层 vs 算法层）相互正交，流量复用。
  * **互斥实验**：同一层级的不同策略实验，流量互斥。

#### 常见陷阱

##### 1. 辛普森悖论 (Simpson's Paradox)
* **现象**：在分组比较中占优势的一方，在总评中反而处于劣势。

##### 3. 幸存者偏差 (Survivorship Bias)
* **现象**：只统计了留存下来的用户，忽略了流失用户。
* **场景**：长周期实验中，实验组策略导致低活跃用户流失，剩下的高活跃用户拉高了平均指标，看似实验效果正向，实则总量下降。

#### 指标统计 SQL 模板

* [Snippet: 通用 A/B 实验指标统计 SQL](snippets/sql-abtest-metrics.sql)

## 研发效率和质量

### Intro

* If you have a development velocity problem, it might be optimizing test runtimes, moving your Docker compile step onto a RAM disk, or using the techniques described in Software Design X-Rays to find the specific files to improve.

### 代码质量 code quality

### 核心工程实践：从原则到 agent prompt

这些原则不是口号，而是降低复杂度、缩小变更半径、提升可验证性的工程约束。对人类工程师如此，对 coding agent 更如此：agent 最容易犯的错不是“不会写代码”，而是过度改动、隐式假设、跳过验证、为了显得聪明而制造不必要结构。

#### Fail-fast：尽早暴露错误

Fail-fast 的核心是：错误一旦出现，应尽早、明确、带上下文地失败，而不是在远处以模糊副作用的形式爆炸。

- **适用场景**：参数校验、配置加载、依赖不可用、状态不一致、数据格式不合法、权限或资源缺失。
- **工程价值**：缩短 debug 路径，让调用方知道“哪里坏了、为什么坏、需要谁处理”。
- **常见误用**：把 fail-fast 理解成“到处抛异常”。真正好的 fail-fast 需要错误信息可行动，并区分用户错误、系统错误、可重试错误和不可恢复错误。
- **agent 要求**：修改代码前先识别输入边界和失败模式；新增逻辑时优先补清晰校验和可诊断错误；不要吞异常、不要只打印日志后继续运行。

#### KISS：保持简单

KISS（Keep It Simple, Stupid）的意思不是写“简陋代码”，而是让实现只承载当前问题的必要复杂度。

- **适用场景**：新功能、bug fix、临时实验、代码重构、agent 自动生成代码。
- **工程价值**：降低理解成本、测试成本和回滚成本。
- **常见误用**：为了“简单”牺牲正确性，或者把必要的抽象全部摊平成重复逻辑。
- **agent 要求**：优先复用现有模式；先做最小正确实现；只有当重复或复杂度真实出现时再抽象；不要新增框架、全局状态、复杂配置或宽泛 helper 来解决局部问题。

#### DRY：不要重复知识

DRY（Don’t Repeat Yourself）真正反对的是“同一份知识散落多处”，而不是机械地消灭所有长得像的代码。

- **适用场景**：业务规则、字段含义、权限判断、序列化协议、状态流转、公共算法。
- **工程价值**：同一规则只需改一处，避免行为漂移。
- **常见误用**：过早抽象，把只是表面相似、变化原因不同的逻辑强行合并，最后得到一个参数爆炸的“万能函数”。
- **agent 要求**：先判断重复的是“知识”还是“形状”。如果只是两段代码长得像，但业务语义和演化方向不同，可以暂不合并；如果重复的是协议、规则或状态机，必须收敛到单一来源。

#### YAGNI：不要提前实现未来

YAGNI（You Aren’t Gonna Need It）的核心是拒绝为想象中的未来需求付当下复杂度成本。

- **适用场景**：扩展点、配置项、策略接口、抽象层、缓存、异步化、多租户、多后端。
- **工程价值**：避免系统在真实需求到来前就被“可能有用”的结构绑架。
- **常见误用**：用 YAGNI 拒绝必要的边界设计。不会立刻实现未来功能，不等于可以忽略兼容性、数据模型演进和错误边界。
- **agent 要求**：不要因为“以后可能需要”新增未被当前任务使用的代码、参数、文件、测试或文档；如果确实留下扩展点，要写明当前调用方和立即收益。

#### SRP / Separation of Concerns：职责单一，关注点分离

单一职责原则强调一个模块应该只有一个主要变化原因。关注点分离强调不同层次的问题不要混在一起。

- **适用场景**：业务逻辑与 IO、策略与执行、解析与校验、状态更新与展示、数据访问与领域规则。
- **工程价值**：让修改能被局部理解、局部测试、局部回滚。
- **常见误用**：把职责单一变成“每三行代码一个函数”，导致调用链碎片化。
- **agent 要求**：新增代码前先找现有边界；不要把 unrelated concerns 塞进已有函数；拆分时以“变化原因”和“测试边界”为准，而不是按行数机械拆分。

#### Least Surprise：最小惊讶原则

代码行为应符合调用方和维护者的合理预期。命名、默认值、错误处理、返回值语义都应减少意外。

- **适用场景**：API 设计、配置默认值、CLI 参数、函数命名、状态迁移、feature flag。
- **工程价值**：降低误用概率，减少隐形线上事故。
- **常见误用**：过度追求“显得高级”的命名或控制流，让简单行为变得难猜。
- **agent 要求**：遵循仓库既有命名、目录、错误处理和测试风格；不要引入和周围代码不一致的默认行为；如果必须改变语义，要同步文档和测试。

#### Small, Reversible Changes：小步、可回滚

高质量改动通常有清晰边界、较小 diff、可单独验证，失败时能快速回滚。

- **适用场景**：线上系统、基础设施、共享库、数据迁移、agent 长程任务。
- **工程价值**：降低 review 难度和事故半径。
- **常见误用**：把一个原子变更拆得过碎，导致中间状态不可运行。
- **agent 要求**：一次只解决一个明确问题；避免顺手重构；如果必须大改，先拆出机械改动、行为改动、验证改动；每一步都能解释“为什么现在必须改”。

#### Make Invalid States Unrepresentable：让非法状态不可表达

好的模型不只是处理错误状态，而是尽量不允许错误状态被构造出来。

- **适用场景**：类型设计、枚举、状态机、配置 schema、数据库约束、任务生命周期。
- **工程价值**：把运行时错误前移到编译期、构造期或校验期。
- **常见误用**：为了追求类型完美而引入过重模型，使简单业务难以演进。
- **agent 要求**：涉及状态流转时，先列合法状态和转移；优先用 enum / dataclass / schema / invariant 表达约束，而不是靠散落的 if 判断兜底。
- Rust 配置解析示例：enum 按 variant 分流、类型保证校验完成（见 [Rust.md](Rust.md#配置解析先按-variant-分流再施加对应不变量)）。

#### Tests, Observability, Documentation：验证闭环

工程质量不是“代码看起来对”，而是能被测试、日志、指标和文档持续证明。

- **测试**：覆盖核心行为、边界条件、回归 case；不要为了覆盖率给无分支 glue code 写脆弱测试。
- **可观测性**：关键路径要能回答发生了什么、耗时多少、失败原因是什么、影响范围多大。
- **文档**：记录非显然决策、接口契约、迁移步骤和运维假设；不要解释每一行显而易见的代码。
- **agent 要求**：改代码后必须尽力运行最相关验证；跑不了要说明原因和替代检查；新增复杂逻辑时同步测试或最小可复现验证。

#### Agent 工程质量 Prompt

可以把下面这段作为 coding agent 的任务前置 prompt 或 code review checklist；独立 snippet 见 [agent-engineering-quality-prompt.md](snippets/agent-engineering-quality-prompt.md)。

```text
在本次工程任务中，请优先遵守以下软件工程原则：

1. 先理解目标和现有边界，再修改代码。优先复用仓库已有模式、工具函数、测试风格和错误处理方式。
2. Fail-fast：对非法输入、缺失配置、状态不一致和不可恢复错误，尽早给出清晰、可行动的失败信息；不要吞异常或静默降级。
3. KISS：做最小正确改动。不要为了局部任务新增框架、复杂抽象、全局状态或未被使用的扩展点。
4. DRY：消除重复的业务规则、协议和状态知识；但不要把只是表面相似、变化原因不同的代码强行抽象到一起。
5. YAGNI：不要实现当前任务没有用到的未来功能、参数、配置或测试。保留扩展点时必须说明立即收益。
6. SRP / 关注点分离：业务逻辑、IO、解析、校验、状态更新和展示尽量保持边界清晰；拆分以变化原因和可测试性为准。
7. 最小惊讶：命名、默认值、返回值、错误语义和目录位置要符合现有代码习惯。改变行为时同步测试和文档。
8. 小步可回滚：避免顺手重构和无关格式化。若任务较大，拆成机械改动、行为改动和验证改动。
9. 让非法状态不可表达：涉及生命周期、状态机、schema 或配置时，显式列出合法状态和转移，优先用类型或 schema 固化约束。
10. 验证闭环：改完后运行最相关测试、lint、类型检查或最小复现；无法运行时说明原因、风险和替代验证。

输出时请说明：改了什么、为什么这样改、遵守了哪些原则、如何验证、剩余风险是什么。
```

### 软件测试与质量保障：从规格到生产

测试提供的是**针对已表达条件的反例搜索与回归证据**，不能证明软件没有 Bug。QA（Quality Assurance）比测试更宽：它还包括规格评审、流程设计、质量门禁、风险管理、发布验证、生产监控和复盘。对 [refactor 任务](#refactor-eval真实负载写流量回放与-no-op)，还要分别证明行为保持、重构目标完成和新实现确实被执行。

#### 测试组合：不同层次回答不同问题

| 层次 | 主要回答 | 特点与边界 |
|---|---|---|
| 静态检查 | 代码是否违反类型、语法、风格、安全或架构规则 | 不运行程序；反馈快，但不能证明运行时行为 |
| 单元测试 | 一个函数、类或小组件的局部行为是否正确 | 数量多、速度快、失败易定位；通常隔离数据库、网络等外部依赖 |
| 集成测试 | 组件与数据库、文件、队列、外部 API 能否正确协作 | 能发现序列化、事务、配置和协议错误；比单测慢且更依赖环境 |
| Contract test | 服务消费者与提供者是否仍满足约定的请求 / 响应契约 | 比全链路测试轻；不证明完整业务流程正确 |
| 验收测试 | 系统是否满足用户可见的业务规格 | 从外部行为出发，可作为交付 gate；质量取决于规格是否完整 |
| End-to-End | 部署后的完整系统能否走通关键用户旅程 | 置信度高，但慢、贵、易 flaky，只保留少量关键路径 |
| 探索性 / 人工测试 | 是否存在规格没有提前想到的问题 | 擅长发现 usability、异常组合和 unknown unknowns；难以稳定回归 |

测试金字塔是一条反馈成本原则：保留大量小而快的测试、适量边界测试、少量全链路测试。具体形状取决于系统，不能把“单测数量最多”机械化成目标。[Practical Test Pyramid](https://martinfowler.com/articles/practical-test-pyramid.html)

#### Gherkin / BDD：把业务行为写成可执行规格

[Gherkin](https://cucumber.io/docs/gherkin/reference/) 是 Cucumber 使用的结构化自然语言 DSL，不是测试执行引擎。它用 `Given / When / Then` 描述初始状态、行为和可观察结果，再由 step definition 映射到测试代码：

```gherkin
Feature: 支付幂等

  Scenario: 相同幂等键重复提交
    Given 订单尚未支付
    When 客户端使用相同幂等键提交两次支付
    Then 只产生一笔扣款
    And 两次请求返回同一个支付结果
```

好的 Gherkin 面向领域行为，不写 CSS selector、内部函数或数据库实现；`Then` 检查用户或外部系统能观察到的结果。它的价值是让产品、QA 和工程师共同审查“系统应该做什么”，并留下机器可执行的 acceptance criteria。Gherkin 文件能运行，不代表规格完整；遗漏的场景依然不会被测试发现。

#### Coverage：测到不等于测对

- **Line / statement coverage**：测试执行过哪些语句。
- **Branch coverage**：条件的不同分支是否都被走过。
- **Condition coverage**：复合条件中的各个布尔项是否取过不同结果。

Coverage 只证明代码被执行过，不证明断言能识别错误。一个没有有效 assertion 的测试也可以得到很高覆盖率。因此：

- 低覆盖率是强烈的风险信号，说明存在自动化测试从未触达的区域。
- 高覆盖率只是弱正向信号，不能替代测试设计、边界 case 和业务验收。
- 不存在适用于所有项目的统一目标值；应按业务风险、复杂度、变更频率和寿命制定门槛。
- Coverage 更适合用来寻找测试空白，而不是作为让团队刷到某个百分比的 KPI。[Google Code Coverage Best Practices](https://testing.googleblog.com/2020/08/code-coverage-best-practices.html)

#### Mutation testing：测试“测试能否发现错误”

变异测试会自动对生产代码注入小错误，例如把 `>` 改成 `>=`、删除一次调用、替换返回值，然后重新运行测试：

```text
baseline tests pass
-> generate mutant
-> run relevant tests
-> test fails: mutant killed
-> test passes: mutant survived
```

Coverage 问“测试是否执行过这段代码”；mutation testing 问“这段代码被改错后，测试是否会察觉”。常用指标是 `mutation score = killed mutants / valid mutants`。survived mutant 通常表示断言或 case 太弱，但也可能是行为等价、无业务影响的 equivalent mutant，需要人工判读。[PIT 基础概念](https://pitest.org/quickstart/basic_concepts/)

Mutation testing 的成本较高，因为每个 mutant 都可能触发一次测试。生产实践通常只变异本次改动、按历史有效性筛选 operator，并只运行相关测试；Google 的增量方案也是把它放进 code review，而不是每次扫描整个仓库。[Practical Mutation Testing at Scale](https://arxiv.org/abs/2102.11378)

#### 相邻方法

- **Property-based testing**：给出 invariant，由框架生成大量输入并缩减失败样例。例如对任意列表，`sort(sort(xs)) == sort(xs)`。它扩大输入空间，但仍依赖人先写对 property。
- **Fuzzing**：持续生成畸形、随机或 coverage-guided 输入，主要寻找 crash、越界、hang 和安全缺陷。[OSS-Fuzz](https://google.github.io/oss-fuzz/)
- **Regression testing**：把曾经出现的 Bug 固化为测试，防止相同行为再次出现。
- **Performance / load / soak testing**：分别检查延迟与吞吐、并发负载、长时间运行下的泄漏和退化。
- **Security testing**：结合 SAST、依赖扫描、DAST、fuzzing、权限与威胁模型；普通功能测试无法覆盖其全部风险。

#### Refactor eval：真实负载、写流量回放与 no-op

[Refactoring](https://refactoring.com/) 的目标是在保持可观察行为的前提下改变内部结构。因此，refactor eval 需要同时检查**行为保持、任务目标完成、验证路径有效**；仅比较输出或统计测试通过率，会把“原样交回”也评成成功。下面是通用工程框架，不是某个 benchmark 已实现的评分规则。

**真实 workload：录制请求，也要保留执行条件。** 少量手写 happy path 无法代表真实负载；录制流量可提供请求分布、调用链、历史错误和长尾输入，但录到了多少请求不等于覆盖了多少语义。

| 需要覆盖 | 评测关注点 |
| --- | --- |
| 输入与状态 | 请求种类、参数关联、数据规模与倾斜、空值、边界值、schema / 配置版本、初始状态 |
| 时间与依赖 | 会话内顺序、读写依赖、并发冲突、重试、超时、部分失败、时钟与随机数 |
| 运行条件 | 冷 / 热缓存、连接池、外部依赖响应、后台任务及资源限制 |
| 结果 | 响应与错误语义、最终状态、外部副作用、必要的事件顺序，以及延迟和资源开销 |

按业务风险分层抽样，单独报告关键写路径与罕见失败，不让大量简单读请求淹没它们。录制数据脱敏时保留关联、分布与因果关系；保留未参与开发的流量集，并用人工构造或故障注入补充录制期没出现的情况。真实性、覆盖率与可复现性需要分别记录。

新旧实现应从相同版本的初始状态分别运行同一工作负载，并固定或记录相关依赖。比较可以容许已声明的非确定性差异，但不能笼统忽略时间戳、ID、顺序等字段：生成 ID 可以映射后比较，引用关系仍须一致。旧实现是兼容性参照，不是绝对正确的规格；若同时修 Bug，应把预期行为变化单列。

**写流量：复制请求不等于可以安全、有效地重放。** 创建订单、扣库存、发消息等操作依赖先前状态；重复发送可能再次产生副作用，也可能因“已创建 / 已扣减”走到另一分支。沿用已消费的幂等键还可能只返回缓存结果，完全没执行待验证逻辑。例如 [Stripe 幂等请求](https://docs.stripe.com/api/idempotent_requests) 会保存同键首次执行的状态码和响应，后续返回同一结果；这是接口特定的重试保证，不是通用 replay 环境。

| 验证方式 | 能得到的证据与边界 |
| --- | --- |
| 隔离状态回放 | 给新旧实现各一份相同的数据库 / 缓存快照或 fixture，重建请求依赖，分别执行后比较响应、状态与副作用；仍需补并发交错与故障场景 |
| 捕获副作用意图 | 核心逻辑真实运行，在邮件、支付、消息等出口记录 payload、目标、次数与顺序；证明“打算做什么”，不能证明外部投递或事务正确 |
| 受控集成环境 | 对关键路径使用独立数据库、队列、测试账户等验证实际提交与可观察结果；覆盖依赖服务真实语义 |
| 只读 shadow / 流量镜像 | 可观察候选处理真实请求的情况；必须核对实际副作用和共享资源影响，不能只凭 HTTP 方法判定只读 |

流量镜像也不自带差分判定：[Istio mirroring](https://istio.io/latest/docs/tasks/traffic-management/mirroring/) 的镜像响应会被丢弃，要额外采集才能比较；“不把候选响应返回给用户”不意味着候选不会写库或发消息。事务回滚也只能撤销事务覆盖的变更，不能自动收回已发邮件、外部扣款等动作。

例如回放“库存为 2 时下单 1 件”，新旧实现应各从库存为 2 的独立状态开始，分别得到库存 1、一笔订单和预期事件；不能让旧实现先改同一数据库，再让新实现处理一次。首次创建与相同幂等键重试应作为不同 case：后者不新增订单可能正是正确行为。

**No-op 检测：行为没变是要求，没有完成重构才是失败。** 至少区分三层：

| 层次 | 容易出现的假成功 | 有效检查 |
| --- | --- | --- |
| 提交 no-op | 空补丁、只改注释 / 格式、增加无人调用的新模块 | 验证任务声明的结构目标；例如调用者确实迁移、旧依赖退出构建 / 发布闭包、重复实现被消除。非空 diff 或行数变化不构成完成证据 |
| 执行 no-op | 加载旧构建、flag 未切换、全部 fallback、请求只命中幂等缓存 | 记录构建 revision、路由选择、候选调用与 fallback；确认目标路径承担了预期工作，而不只是进入过函数 |
| 验证 no-op | Mock 永远成功、所有写操作被吞掉、只检查 HTTP 200、差分规则忽略关键变化 | 对应有变化的 case 检查状态增量与副作用；给候选注入“跳过写入 / 改错结果”等已知缺陷，确认评测会失败 |

增加两个对照：**原样提交应通过行为保持测试，但不能通过重构完成门槛；已知错误变体应被相关断言发现。** 后者可复用 [mutation testing](#mutation-testing测试测试能否发现错误)，但变异必须在该 case 中确实改变要求的行为。合法的幂等重试、未命中更新或拒绝冲突可能本来就不写，不能要求每条请求都有状态变化。

验收先声明结构目标和允许变化，再固定新旧 revision、状态与 workload，按副作用选择回放方式，最后报告行为差异、目标完成度、候选实际执行与资源回归。性能优化任务还需相同质量与负载下的重复测量；普通重构不必更快，但应满足既有性能预算。无法隔离的写路径应列为未验证或另走受控集成，不能算进“全量回放通过”。

#### QA 流程与质量指标

一条可执行的质量链路通常是：

```text
规格与风险评审
-> static checks + unit tests
-> integration / contract tests
-> acceptance / critical E2E
-> security / performance gates
-> risk-based review
-> canary / feature flag
-> production metrics + rollback
```

质量指标也应覆盖多个维度：

| 维度 | 可用信号 |
|---|---|
| 测试有效性 | coverage gap、mutation score、flaky rate、测试耗时 |
| 功能质量 | escaped defects、回归缺陷、验收通过率 |
| 可维护性 | 复杂度、重复、依赖环、hotspot、变更耦合 |
| 可靠性与性能 | error rate、p95 / p99 latency、资源水位、SLO |
| 交付风险 | change failure rate、rollback rate、MTTR |
| 安全 | 高危依赖、静态 / 动态扫描结果、权限越界与漏洞修复时长 |

指标是 proxy，不是目标本身。Coverage 可以靠无效测试刷高，复杂度可以靠机械拆函数降低，测试通过率也会因跳过 flaky case 变好。质量 gate 必须和真实风险、生产反馈及人工判断交叉验证。

#### 测试设计的最低要求

- Bug 修复的回归测试应先在旧实现上失败，再在修复后通过；纯重构的行为测试则应新旧都通过，另行验证结构目标，不能把两种验收混为一谈。
- expected result 应来自规格或独立 oracle，不能照抄被测实现的输出。
- 除 happy path 外，覆盖边界值、非法输入、部分失败、重试、幂等、并发与状态恢复。
- Mock 外部边界，不要把核心业务逻辑全部 mock 掉；关键集成仍需面对真实或高保真依赖。
- 优先审查 assertion 和测试意图，而不是只看测试数量与 coverage 增量。



### 衡量 Measure technical quality

> [Building Evolutionary Architectures](https://www.amazon.com/Building-Evolutionary-Architectures-Support-Constant/dp/1491986360/) and [Reclaim unreasonable software](https://lethain.com/reclaim-unreasonable-software/).

* What percentage of the code is statically typed?
* How many files have associated tests?
* What is test coverage within your codebase?
* How narrow are the public interfaces across modules?
* What percentage of files use the preferred HTTP library?
* Do endpoints respond to requests within 500ms after a cold start?
* How many functions have dangerous read-after-write behavior? Or perform unnecessary reads against the primary database instance?
* How many endpoints perform all state mutation within a single transaction?
* How many functions acquire low-granularity locks?
* How many hot files exist which are changed in more than half of pull requests?

#### proxy measurement

* the number of files changed in each pull request on the understanding
  * smaller pull requests are generally higher quality.
* measure a codebase’s lines of code per file
  * on the assumption that very large files are generally hard to extend.

#### 埋点 instrumentation

* instrumentation is a requirement for useful metrics. Instrumentation complexity is the biggest friction point for adopting these techniques in practice, but if you can push through, you unlock something pretty phenomenal: a real, dynamic quality score that you can track over time and use to create a clarity of alignment in your approach that conceptual alignment cannot.

### 研发效率团队 Technical quality team

> https://staffeng.com/guides/manage-technical-quality/

* Intro	
  * maybe one engineer working on developer tooling for every fifteen product engineers, in addition to your infrastructure engineering investment.
* 人员配置：
  * Technical Program Manager, but typically that is after they cross into operating a Quality program
  * 1-N个P9兼管
* 要点：
  * **Trust metrics over intuition.** 
  * **Keep your intuition fresh**
    * team embedding、team rotation、1:1 discussion
  * **Listen to and learn from your users.**
  * **Do fewer things, but do them better**
  * **Don’t hoard impact.**

* 衡量产出：
  * discounted developer productivity (in the spirit of [discounted cash flow](https://en.wikipedia.org/wiki/Discounted_cash_flow))

### 开发流程：瀑布式开发

> 参考：W. W. Royce, [Managing the Development of Large Software Systems](https://www.praxisframework.org/files/royce1970.pdf), 1970；[Agile Manifesto](https://agilemanifesto.org/)、[Agile Principles](https://agilemanifesto.org/principles.html)。

瀑布式开发把软件项目拆成线性阶段：需求、规格、设计、实现、集成、测试、交付 / 运维。每一阶段有明确产物和 sign-off，下游依赖上游完成，像水从上游流到下游。

它的设计动机不是“慢”，而是**用阶段门管理承诺**：先把需求、预算、责任、文档、验收口径和合同边界固定下来，再进入实现。它适合需求稳定、变更成本高、合规文档重、硬件 / 外包 / 多团队依赖强的项目。

核心问题在于，软件开发往往不是制造业复制，而是知识发现。瀑布隐含三个强假设：

- 需求能在早期说清。
- 设计能在实现前接近正确。
- 集成和测试可以后置。

一旦这些假设不成立，错误会沿阶段向下游滚动：需求误解到测试阶段才暴露，设计缺陷到集成阶段才发现，返工成本就会非常高。瀑布最危险的地方不是文档多，而是**反馈太晚**。

更好的理解：

- 瀑布适合管理外部承诺：合同、审计、里程碑、供应商、合规验收。
- 敏捷 / 迭代适合管理不确定性：用户需求、产品体验、技术方案、模型行为、真实数据反馈。
- 真实组织里通常是混合形态：外层有阶段门，内层用短迭代交付可运行软件。

一句话：瀑布式开发的本质是用计划和阶段门降低管理不确定性；敏捷的本质是用更早、更频繁的工作软件和用户反馈降低产品 / 技术不确定性。关键不在流程标签，而在反馈是否早于不可逆承诺。

### 前后端协作与接口联调

前后端联调指前端页面与后端服务在开发阶段进行接口数据对接、调试与验证的过程。核心是“契约先行”：先约定 URL、方法、参数、返回结构，再并行开发，联调阶段验证一致性。

* 接口契约（API contract）
  * 先定义再开发：用 Swagger / OpenAPI、YApi、Apifox 等工具沉淀文档；前端可先用 Mock 数据开发，后端完成后切真实接口
  * 变更管理：字段变更尽量收敛到适配层，不直接散落到业务组件；联调期用 Network 面板 / Postman / 抓包工具核对请求与响应
* 常见联调问题：参数名/类型不一致、返回结构漂移、跨域（CORS）、鉴权/token、空值语义、重复请求、环境根地址配置
* TOP 接口 / top 接口
  * 大写 TOP：Taobao Open Platform（淘宝开放平台）的缩写，指淘宝/阿里系对外开放数据和能力的 HTTP API；外部服务、小程序、千牛插件都会调用
  * 调用特点：REST 风格，大部分接口支持 GET/POST，写操作只支持 POST；用 app key + 签名请求 TOP 服务器，返回业务数据
  * 前端调用常见入口：千牛插件用 `QN.top.invoke()` / `QN.top.batch()`，小程序用 `cloud.topApi.invoke()`；涉及权限/敏感数据的接口一般要在服务端转发
  * 联调语境里若看到小写 `top`，多半不是淘宝 TOP：可能是 `window.top`（iframe 嵌套时返回最顶层窗口，常配合 postMessage 做跨层通信），也可能是团队内部对“顶层聚合接口/BFF 入口”的简称；先看上下文再判断。BFF 的职责边界与适用场景见 [Web-基础：BFF](./Web-基础.md#bffbackend-for-frontend)

### 开发协作工具链：GitHub / GitLab / Gitea / SonarCloud / 1Password / Confluence / JIRA / Netlify

一套典型 SaaS 研发链路的串联视角：代码托管（GitHub / GitLab / Gitea）→ 质量门禁（SonarCloud）→ 凭据管理（1Password）→ 团队文档（Confluence）→ 任务跟踪（JIRA）→ 前端部署（Netlify）。

**GitHub**
* 定位：全球最大代码托管与协作平台（git 仓库 + PR / issue + 社交化开源）。
* 核心：PR review 流程、GitHub Actions（CI/CD）、Codespaces、Packages、Copilot / AI 助手、开源生态（stars / forks / discussion）。
* 适合：开源项目与默认云端托管；生态最全但平台有绑定。

**GitLab**
* 定位：DevOps 一体化平台，一个应用内包含 repo + CI/CD + 安全扫描 + 容器 / 部署 + wiki。
* 核心：Single Application 理念；支持自托管（CE / EE），数据不出内网；内置 CI/CD（`.gitlab-ci.yml`）、代码质量、SAST / 依赖扫描。
* 对比 GitHub：GitHub 偏「生态 + 协作」，GitLab 偏「一体化 + 可自托管」，适合数据合规 / 私有化要求高的团队。

**Gitea**
* 定位：Go 写的轻量自建 Git 服务，官方口径是「painless、self-hosted、all-in-one」：Git 托管 + PR / code review + issue / 看板 + package registry + CI/CD 收在一个二进制里，面向个人、小团队和内网私有化部署。
* 核心：单二进制 + SQLite / MySQL / PostgreSQL / MSSQL 任选；`gitea` CLI 负责运维（含 `dump` 备份）；资源门槛低（官方口径 Raspberry Pi 3 可跑小负载，2 核 1GB 够小团队）；Gitea Actions 语法兼容 GitHub Actions，但要单独部署 Gitea Runner；内置 packages registry、LFS、webhook、OAuth2 / LDAP、仓库迁移导入，code review 支持 PR 与 AGit 两种流程；官方还配 Tea CLI 与 VS Code 扩展。
* 对比 GitLab：GitLab 是一体化全家桶（安全扫描、更完整的权限与流水线）；Gitea 砍掉这部分能力，换「一个二进制 + 一个数据库」的部署与运维成本。私有化 / 合规两者都能做，选型看功能覆盖面与运维投入。
* 谱系与治理（选型前值得知道）：2016 年从 Gogs 分叉（几乎全部重写，也不从上游同步代码，从 Gogs 过来要迁移仓库而不是原位升级）；2022-10 创建者成立 Gitea Ltd. 并转移域名与商标，社区事先未参与决策、引发争议，随后出现分叉 Forgejo——域名由柏林非营利组织 Codeberg e.V. 托管，Codeberg 自身就跑在 Forgejo 上，Forgejo 自 v9 起改为 GPLv3+、2024 年初起与 Gitea 成为 hard fork。Gitea 侧现在每年由 maintainer 投票选举 TOC，商业支持与 Gitea Cloud / Enterprise 来自创始团队的公司 CommitGo。
* 适合：内网 / 隔离环境自建代码托管；资源有限的小团队；想要 GitHub 式体验但代码必须留在自己机器上的场景。

**SonarCloud**
* 定位：代码质量与安全静态分析云服务（SonarQube 的 SaaS 版）。
* 核心：扫描 Bug、漏洞、坏味道、重复代码、测试覆盖；质量门禁（Quality Gate）决定能否合入；支持主流语言并与 GitHub / GitLab CI 集成。
* 对比：GitHub 自带 CodeQL / secret scanning 偏安全；Sonar 偏「可维护性 + 质量门禁」；本地 lint 只管语法风格，Sonar 管跨文件与历史趋势。

**1Password**
* 定位：团队密码与密钥管理（password manager）。
* 核心：密码 / 密钥 / SSH key 集中存储，按团队保险库（Vault）共享，浏览器 + CLI 集成，2FA，开发者工具（`op` CLI、CI secret 注入）。
* 边界：只管理「凭据」，不替代 `.env` 或云 Secret Manager——本地开发用 `.env`（不入库），生产 / CI 用平台 Secret Manager（Vault / AWS Secrets Manager），1Password 偏「人与开发者的凭据」。已有提及见 [Security-Privacy-Cryptography.md](./Security-Privacy-Cryptography.md)「密码管理器」。

**Confluence**
* 定位：团队知识库 / 协作文档（Atlassian）。
* 核心：空间（Space）+ 页面层级 + 权限 + 模板（技术方案、周报、API 文档）+ 与 JIRA 双向引用。
* 对比：Notion 更灵活 / 个人向；Confluence 适合按团队空间做权限与审计。文档原则：可检索、有 owner、定期清理。

**JIRA**
* 定位：项目与问题跟踪（Atlassian），敏捷开发事实标准之一。
* 核心：issue / 史诗 / 故事 / 任务 + 看板 / 冲刺 + 自定义工作流 + 与 Git 集成（提交 → issue 关联 → PR 自动关闭）。
* 对比：GitHub Issues 轻量够用（开源 / 小团队）；JIRA 强在规模化流程与报表；Linear 体验更现代但生态浅。

**Netlify**
* 定位：前端 / 静态站点托管与部署平台（Jamstack 代表）。
* 核心：Git 推送即部署、PR 预览部署（Preview Deployments）、CDN + 边缘、Serverless Functions、表单 / 身份、回滚。
* 对比：Vercel 同为前端部署平台（更偏 Next.js 生态）；Netlify 偏静态站 / 内容站点；个人轻量站也可用 GitHub Pages。已提及见 [Web-基础.md](./Web-基础.md)「部署到 Vercel、Netlify、Cloudflare 这类平台」。

选型一句话：开源 / 云原生协作选 GitHub；私有化 / 合规一体化选 GitLab；自建轻量 / 内网部署选 Gitea（更看重社区治理可换 Forgejo）；质量门禁接 SonarCloud；人与开发者凭据用 1Password；规模化文档与任务用 Confluence + JIRA；前端发布用 Netlify / Vercel。

来源：各官方站点 [GitHub](https://github.com)、[GitLab](https://about.gitlab.com/)、[Gitea](https://about.gitea.com/)（对比与部署细节见 [Gitea Docs](https://docs.gitea.com/)、[Forgejo](https://forgejo.org/)）、[SonarCloud](https://www.sonarsource.com/products/sonarcloud/)、[1Password](https://1password.com/)、[Confluence](https://www.atlassian.com/software/confluence)、[JIRA](https://www.atlassian.com/software/jira)、[Netlify](https://www.netlify.com/)。



### Linear：给特定人做工具的公司样本（小团队、质量、agent 转向）

> Linear 是一家产品开发 / issue tracking / roadmap SaaS，2019 年成立，总部旧金山、全员远程。它是 JIRA 之外最有代表性的现代工程协作工具样本：先靠 opinionated 的体验赢得 PMF，再在 2026 年主动宣布 issue tracking 已死、转向 context + agents。

**创始与 PMF（First Round Review 口径）**
* 三人均被 JIRA 折磨过：Karri Saarinen（CEO，Airbnb principal designer / Coinbase 创始设计师）、Jori Lallo（CPO，前 Coinbase）、Tuomas Artman（CTO，前 Uber / Groupon 工程）；动机是「给自己和同类 IC 造工具」。
* 节奏：正式创业前一年每周三在酒吧讨论验证需求 → 2019-03 全职、一个月做出可用原型 → 2019-04 邀请制 beta（每周只放约 10 人）→ 约一年 waitlist、约 1000 DAU 后才公开 → 2021 年盈利。
* 产品哲学：设计给特定的人，强默认、opinionated，不追求无限可配置；早期功能刻意分 Enabler（让现有用户更开心）和 Blocker（扫清 ICP 加入障碍）两类。
* Linear Method 11 条把「小团队、质量、原则而非手册」写成制度：Ship early & smaller、Build with users、Know what good looks like、Think in principles not playbooks、Build things that last、Avoid side quests、Say it as it is、Keep the team small / do more with less、Hire the best people、Create fans、Fully remote；质量是 competitive advantage 和公司 gravity，明确反 hustle / 996 文化。

**规模与资本（截至 2026-08）**
* 融资：2019 seed $4.2M → 2021 Series B（Accel 领投，$400M 估值）→ 2025 Series C（$1.25B）→ 2026-08 员工流动性轮 $2.5B 估值（Accel 领投、$99M，新增 Salesforce Ventures / S32）。
* 业务：ARR $100M+、40,000+ 付费组织、net revenue retention 177%；客户含 OpenAI、Coinbase、Ramp、Vercel、Stripe、Figma，AI 原生客户含 Cursor、Cognition、Harvey、Physical Intelligence、Legora、Baseten；Ramp / Coinbase 已自建集成 Linear 的 custom coding agent。
* 组织与财务纪律：全员远程下团队从约 120 人只扩到 2026 年的 203 人，工程约 25 人量级；2026-08 口径现金流转正、账面现金超过历史 primary 融资总额，因此拒绝稀释性融资。
* 定价：免费版限 250 active issues；付费档约 $8–14/user/mo（Standard→Plus），Enterprise 按需——显著高于老牌 issue tracker，靠价值而非低价取胜。

**产品演进与 2026 agent 转向**
* 产品从 Issue 起步长成 shared product system：Issue / Cycles / Projects / Roadmaps / Inbox / Analytics / Project Docs；产品速度 sub-100ms、键盘优先。
* 2026 年明确范式判断：issue tracking 是围绕 handoff（人传人交接）设计的，agent 时代应围绕 context（agents 可共享、消费、执行的产品上下文）设计；推出 Linear Agent + Skills / Automations + Code Intelligence，外部接 Claude Code / Codex，2026-06 起 Coding Sessions 可在 Linear 内完成 triage → plan → review → ship。
* 官方效果口径（日期不同不可混用）：2026-03 称 75%+ enterprise workspaces 装了 coding agent、agent 活动量 3 个月 5x、agent 撰写约 25% 新 issue；2026-08 传播口径为 95% paid workspaces 使用 coding agent、agent 产出的工作占比一年内从 3% 到 50%；2026-06 changelog 称约 30% incoming bug reports 由 Linear Agent 一轮解决。

**对研发协作与 agent infra 的启发**
* Linear 是把「质量先行 + 小团队 + opinionated 工具」同时落到产品形态和管理制度的可研究样本；其克制（功能分层、拒绝无限配置）正是很多 agent 产品缺的部分。
* 对 coding agent 的量化：bug 自动一轮解决率 30%、agent 撰写 issue 占比等是生产环境的 real signal，接近 harness 里 triage → reproduce → fix → verify 闭环的成功率口径，值得做成可对照的 eval。
* 其 agent 指标随时间明显漂移（安装率 75%+ vs 95%、占比 25% vs 50%），引用必须带日期和定义（installed vs active、new issues authored vs work share）——这本身就是 agent 产品数据报告的典型案例。
* 若 issue 的主要消费者从人变成 agent，tracker 的价值就从「人的状态看板 / 交接系统」转向「context store + 可执行工作单元」，状态机、owner、handoff 语义都会重构。

来源：[Linear About](https://linear.app/about)、[Linear Method](https://linear.app/method)、[Careers](https://linear.app/careers)、[Linear Next：Issue tracking is dead](https://linear.app/next)、[Coding Sessions changelog](https://linear.app/changelog/2026-06-11-coding-sessions)、[First Round Review：PMF 之路](https://review.firstround.com/linears-path-to-product-market-fit/)、[First Round Review podcast：Inside Linear](https://review.firstround.com/podcast/inside-linear-why-craft-and-focus-still-win-in-product-building/)、[Contrary Research 报告](https://research.contrary.com/company/linear)、[Pulse2：$2.5B tender / ARR $100M](https://pulse2.com/linear-completes-99-million-tender-at-2-5-billion-valuation-as-arr-tops-100-million-and-net-retention-hits-177/)、[ValueAddVC：商业模式拆解](https://valueaddvc.com/blog/how-does-linear-make-money-per-seat-pricing-product-led-growth-and-the-2b-valuation-breakdown)。



## DevOps --> 「云原生-ToB.md」

> todo 《Accelerate: The Science of Lean Software and DevOps: Building and Scaling High Performing Technology Organizations》

### Intro

* DevOps的重点：
  * version control
  * trunk-based development
  * CI/CD
  * production observability (including developers on-call for the systems they write)
  * working in small, atomic changes.

### Monitoring 可观测性服务 —— 运维监控

> 经验中，云原生系统的可观测性开销，往往占到云开销的 15%-25%。
>
> 这么高吗？

#### Intro

* 阿里云有非常丰富的可观测性服务，包括日志服务 SLS，云监控 CloudMonitor， 应用实时监控服务 ARMS

#### 网络

* PingMesh https://cloud.tencent.com/developer/article/1780947

#### 通用

* [Grafana：SpaceX 的数据监测利器，云原生领域的 Tableau](https://mp.weixin.qq.com/s/zgd8KjpGoqwPGC6b1I9owg)
  * 本质是提升数据可观测性（Data Observability），打破数据边界，提供一个“统一的视窗”，实现对数据的全览和实时监控
  * 也有观点认为，可视化的重要性远大于指标、日志和链路追踪
  * 推动“数据民主化”

### Logging



### Tracing

### Alert



### CI/CD平台 DevOps

* 阿里云云效
  * https://www.aliyun.com/product/yunxiao
* [vivo自建](https://mp.weixin.qq.com/s?__biz=MzI4NjY4MTU5Nw==&mid=2247498843&idx=1&sn=314aff57db845b164d2e70d0d58ad12a&scene=21)

#### Jenkins clusters



## 系统架构

### 系统迁移 (Migrations)

> 参考: [Migrations: the sole scalable fix to tech debt.](https://lethain.com/migrations/)

系统迁移是在公司和代码库增长过程中，唯一能够规模化解决技术债的有效机制。当公司快速发展时，任何工具或流程都将达到其规模上限，迁移因此成为必然。有效的迁移能力是维持组织高效迭代的关键，否则最终将陷入技术债的泥潭或被迫进行更具破坏性的完全重写。

#### 迁移执行三阶段

有状态系统还要明确 source of truth 的切换：shadow 阶段由旧系统写入、候选系统跟随；promotion 后由新系统写入、旧格式降为兼容视图。两端长期各自接受业务写入，会把迁移变成双 authority。事务捕获、追平水位、旧 writer fencing 和回退条件见 [Outbox：把业务提交与异步投递绑定](#outbox把业务提交与异步投递绑定)。

一次成功的迁移可以遵循一个标准化的三阶段手册：

1.  **去风险 (Derisk)**
    *   **目标**: 尽快、低成本地验证方案并建立信任。
    *   **执行**: 
        *   与最困难、最边缘的团队深入沟通，迭代设计文档。
        *   **不要从最简单的案例开始**。选择并嵌入1-2个最复杂的团队，与他们共同构建并完成迁移，这能真正暴露方案的弱点。
        *   成功完成早期迁移是为后续大规模推广建立信誉的关键。
2.  **赋能 (Enable)**
    *   **目标**: 规模化推广，降低整个组织的迁移成本。
    *   **执行**: 
        *   **构建自动化工具**: 投入时间开发能自动化处理90%简单场景的迁移工具，而不是急于分发任务。
        *   为剩下10%的复杂场景提供清晰的文档和支持。
3.  **完成 (Finish)**
    *   **目标**: 彻底终结项目，不留尾巴。
    *   **执行**: 
        *   **设定明确的截止日期**: 这是确保项目完成的最有效手段。
        *   **停止支持旧系统**: 在截止日期后，正式停止对旧系统的维护，推动剩余部分完成迁移。
        *   **清理旧代码**: 迁移完成后，务必将旧代码和基础设施彻底移除。

#### Strangler Fig：绞杀式逐步替换

> 来源：[Martin Fowler - Strangler Fig Application](https://martinfowler.com/bliki/StranglerFigApplication.html)、[TypeScript Project References](https://www.typescriptlang.org/docs/handbook/project-references.html)。

**模式**：Strangler Fig（绞杀榕）是 Martin Fowler 提出的应用现代化模式。名字来自绞杀榕：种子落在宿主树冠上，根系沿树干向下包裹，最终宿主枯死、榕树独存。对应到软件：**不一次性重写旧系统，而是用新系统在旧系统旁边/前面逐步绞杀它**，直到旧系统不再被调用后拆除。它专门反对 Big Bang rewrite——重写周期长、期间零交付、需求漂移后回不来。

**“逐步替换”怎么执行**：

1. 旧系统继续运行，入口加一层 facade / router 拦截流量；
2. 按模块或功能切片，把一部分请求路由到新实现，新老并行；
3. 验证一块、替换一块，通过 feature flag / 比例放量逐步扩大新系统接管范围；
4. 旧系统只剩“还在被调用”的最后几块时集中替换；
5. 确认零调用后彻底拆除旧系统（对应迁移三阶段的 Finish）。

**为什么有效**：每步都有交付、可回滚、风险局部化；替换顺序按边界清晰度而非架构美观排序；旧系统里稳定的部分可以留到最后甚至保留。

**关键条件与坑**：

- 接口兼容与数据一致性：新老实现共享同一份数据或做好迁移同步，否则分流后行为分裂；
- 从 bounded context 边界清晰处开切：边界糊的地方先划边界，再谈替换；
- 可观测性必须能回答“旧系统是否还在被调用”，否则不知道何时收尾；
- 收尾必须拆旧代码，否则变成“新系统 + 僵尸旧系统”双倍维护。

**工程约束变体（LoopX / TypeScript）**：Strangler Fig 只规定替换顺序，不规定“谁在改”。LoopX 在此基础上加硬约束：**每个 revision、每个语义块只有一个 owner**——同一语义块同时只允许一个 agent / 进程拥有写入权，从控制面杜绝并发改写同一块导致状态漂移。TypeScript 的 [project references](https://www.typescriptlang.org/docs/handbook/project-references.html) 则把 bounded context 变成编译期边界：composite project + 显式 references + 构建顺序，让“哪块依赖哪块、谁可以引用谁”由类型系统把关，逐块替换在编译层面可控。机制详见 [AI-Agent-Engineering.md - LoopX](./AI-Agent-Engineering.md#loopx长程-agent-的本地控制面)。




### Optimistic Concurrency Control：提交前验证的并发控制

> 来源：H. T. Kung and John T. Robinson, [On Optimistic Methods for Concurrency Control](https://doi.org/10.1145/319566.319567), ACM TODS 1981。

OCC 的核心不是“不处理冲突”，而是 **先不加锁地并发做，提交前做 validation**：验证通过才把本地修改原子写回全局状态；验证失败就 abort / retry。

```text
read phase:
  读全局状态；写操作只写本地 copy

validation phase:
  检查这次 transaction 是否可串行化

write phase:
  validation 通过后，把本地 copy 原子写回全局
```

它适合冲突概率不高、读多写少、希望避免长时间持锁的系统。代价是：冲突会在提交前才暴露，失败事务需要重试；如果冲突率高，OCC 会把成本从“等待锁”转成“反复 abort / retry”。

#### 正确性目标：serial equivalence

并发事务的最终结果，必须等价于某个串行执行顺序。形式上，如果初始数据库状态为 `d_initial`，事务集合为 `T_1 ... T_n`，那么并发执行后的结果应等价于某个排列 `π` 的串行组合：

$$
d_{\text{final}}
=
T_{\pi(n)} \circ \cdots \circ T_{\pi(1)}(d_{\text{initial}})
$$

这个目标比“每个事务自己看起来没错”更强。并发系统真正要保证的是：虽然实际执行交错发生，但外部观察到的状态变化像是事务按某个顺序一个个完成。

#### Validation 的直觉：read set / write set 不冲突

对一个准备提交的新事务 `T_j`，validation 要检查所有在串行顺序上更早的事务 `T_i`。直觉是：更早事务的写入，不能破坏 `T_j` 已经读到的东西，也不能和 `T_j` 即将写入的东西产生不可串行化冲突。

记：

```text
R(T) = transaction T 的 read set
W(T) = transaction T 的 write set
```

典型安全条件可以这样理解：

1. `T_i` 完全早于 `T_j`：`T_i` 写完后，`T_j` 才开始读。这等价于普通串行顺序，安全。
2. `T_i` 与 `T_j` 读阶段重叠，但 `T_i` 写入的内容没有被 `T_j` 读过：

$$
W(T_i) \cap R(T_j) = \varnothing
$$

这表示 `T_j` 没有基于被 `T_i` 改写过的旧值做决策，因此可以把 `T_i` 排在 `T_j` 前面。

3. 更强的安全条件是：`T_i` 写入的内容既不影响 `T_j` 读到的东西，也不和 `T_j` 即将写的东西相交：

$$
W(T_i) \cap \bigl(R(T_j) \cup W(T_j)\bigr) = \varnothing
$$

这说明两者虽然时间上重叠，但在数据依赖上互不干扰，可以安全并发。

#### 和锁、WAL、Event Sourcing、CRDT 的关系

| 机制 | 核心思路 | 适合场景 |
| --- | --- | --- |
| Pessimistic locking | 先加锁，再读写，提前阻止冲突 | 冲突率高、写入代价大、不能接受重试 |
| OCC | 先并发执行，提交前验证，不通过就 retry | 冲突率低、读多写少、希望减少锁等待 |
| WAL | 正式数据持久化前，先持久化足以恢复的记录 | 崩溃恢复、事务 durability、延迟刷写数据页 |
| Event Sourcing | 把状态变化记录成事件流，用 replay / projection 重建状态 | 需要审计、回放、历史状态、并行 read model |
| CRDT | 让并发更新天然可合并，减少中心化冲突检测 | 分布式、离线、多副本协作编辑 |

OCC 解决的是 **提交时能不能接受这次写入**；WAL 解决的是 **已接受的写入如何经受进程或机器崩溃**；Event Sourcing 解决的是 **业务状态变化如何被记录、重放和审计**；CRDT 解决的是 **多个副本并发更新如何自动收敛**。它们不是互斥关系：数据库可以用 OCC 做提交验证，用 WAL 保证持久化；应用再用 domain event / event log 记录已提交的业务事实，并用 projection 服务读路径。

**应用场景：versioned agent memory 提交协议。**

Agent memory / experience 系统里也有类似事务问题：多个 session、heartbeat、goal tick 或 meta-agent 可能同时读旧 memory，然后生成 patch。不能因为大家都“想改进 memory”，就直接 append / overwrite。

可以把一次 memory update 看成事务：

```text
read set:
  当前任务读过的 memory ids / data_version / policy view

local write:
  生成的 memory patch、merge proposal、delete / bury decision

validation:
  检查 read set 是否仍是当前版本；检查 write set 是否和已提交 patch 冲突

write:
  apply patch，生成新的 data_version，并写入 event log
```

最小字段可以这样补到 versioned memory / eval 系统里：

```text
memory_patch_txn:
  txn_id
  source_run_id
  read_data_version
  read_set
  write_set
  generated_patch
  validation_status: accepted | aborted | retry_required | manual_merge_required
  committed_data_version
```

这能避免两类常见问题：

- **lost update**：两个 agent 基于同一个旧版本生成 patch，后提交的覆盖先提交的。
- **future leakage**：eval 时把某个 run 当时不可见的后续 memory patch 也算进 policy view。

因此 OCC 和 Event Sourcing 是互补的：OCC 让 memory patch 在提交前验证依赖是否仍成立；Event Sourcing / versioning 让提交后的状态变化可追踪、可回放、可按 `data_version` 解释历史行为。



### WAL（Write-Ahead Log）：先持久化恢复记录，再持久化正式状态

> 来源：[ARIES](https://research.ibm.com/publications/aries-a-transaction-recovery-method-supporting-fine-granularity-locking-and-partial-rollbacks-using-write-ahead-logging)、[PostgreSQL WAL](https://www.postgresql.org/docs/current/wal-intro.html)、[SQLite WAL](https://sqlite.org/wal.html)、[RocksDB WAL format](https://github.com/facebook/rocksdb/wiki/Write-Ahead-Log-File-Format)、[Linux ext4 journal](https://docs.kernel.org/filesystems/ext4/journal.html)、[Raft paper](https://raft.github.io/raft.pdf)。

WAL 的核心是一条**持久化顺序约束**：

> 在正式数据页、索引、内存表对应的持久化状态落盘前，先把足以恢复该修改的日志记录刷到稳定存储。

数据库可以先修改内存中的 buffer page；真正不能发生的是：脏数据页已经持久化，而描述这次修改的 WAL 还没有持久化。

```text
修改路径：
  修改内存中的 buffer page
  -> append WAL record

data page 写回门槛：
  flush WAL through page LSN
  -> 才允许对应 dirty page 写回正式数据文件

transaction 提交门槛：
  append commit record
  -> flush WAL through commit LSN
  -> 才向调用方确认 committed
```

两个关键不变量：

```text
写回 data page 前：
  durable_wal_lsn >= page_lsn

确认 transaction committed 前：
  durable_wal_lsn >= commit_lsn
```

其中 LSN（Log Sequence Number）是日志记录的单调位置。它让系统知道数据页已经包含到哪条日志、恢复应从哪里继续。

#### 为什么 WAL 能兼顾 durability 与性能

如果每次事务提交都随机写回所有数据页，I/O 成本很高。WAL 把同步路径收敛成顺序追加：

```text
commit path:
  sequential append + fsync(WAL)

background path:
  batch flush dirty pages
  checkpoint
  recycle old WAL
```

顺序写通常比散落的数据页随机写便宜；多个并发事务还可以通过 **group commit** 共用一次 WAL flush。PostgreSQL 因此不要求每次提交都同步刷完所有被修改的数据页。

但 `write()` / append 返回成功不等于已经耐久。数据可能仍在操作系统 page cache、磁盘控制器缓存或设备易失缓存中。真正的 durability 取决于：

- `fsync` / `fdatasync` 或等价持久化屏障；
- WAL 与数据文件之间的 flush ordering；
- commit record 何时被认为稳定；
- checksum、record length 等 torn-write / partial-record 检测；
- 存储设备是否诚实实现 flush。

#### WAL record、checkpoint 与恢复

一条通用 WAL record 常包含：

```text
lsn
transaction_id
record_type
target_page / key
redo information
optional undo information
previous_lsn
length + checksum
```

崩溃后，系统从 checkpoint 附近扫描 WAL：

```text
读取 checkpoint
-> 丢弃尾部不完整或 checksum 错误的 record
-> REDO：重做已持久化日志、但尚未进入正式数据页的修改
-> 可选 UNDO：撤销崩溃时未提交事务已经写出的修改
-> 重新建立一致状态
```

并非所有 WAL 都同时支持 REDO 和 UNDO：

- PostgreSQL、RocksDB 等常见路径主要依赖 redo；
- ARIES 这类 undo/redo recovery 会分析事务、重复历史，再撤销 loser transactions；
- 日志只保存 after-image、before-image、physical page delta 还是 logical operation，决定了能执行哪种恢复。

checkpoint 不是“日志已经没用”。它只建立一个更近的恢复起点。只有当相关状态已安全进入正式存储、没有 reader / replica / backup 再依赖旧日志时，旧 WAL 才能回收。

#### 编程中的经典应用

| 场景 | WAL 记录什么 | 恢复方式与边界 |
|---|---|---|
| 关系数据库 | page change、transaction 与 commit record | 从 checkpoint redo；具体系统可能还需要 undo / MVCC cleanup |
| SQLite | 修改先追加到 `-wal` 文件，主数据库保持旧版本 | reader 固定自己的 end mark；checkpoint 把 WAL page 合并回主文件；仍只有一个 writer |
| RocksDB / LSM KV | `WriteBatch` 先进入 WAL，再更新 MemTable | crash 后 replay WAL 重建尚未 flush 成 SSTable 的 MemTable |
| ext4 / journaling filesystem | metadata 或 data block transaction + commit block | 没有合法 commit/checksum 的事务在 replay 时丢弃；完成事务再写回 home location |
| 2PC participant / coordinator | prepare state、commit / abort decision | 节点重启后恢复 in-doubt transaction；WAL 不会消除等待 coordinator 的阻塞问题 |
| Raft replicated state machine | term、vote 与 command log 持久化，并复制到 quorum | committed entry 才 apply 到 state machine；这是“本地 WAL + 分布式共识”，不能只靠 append 本地文件替代 |
| durable job / workflow | task transition、input、attempt、result intent | 启动时 replay 到状态机；外部副作用还要靠 idempotency key、receipt 或补偿协议 |

最后两类需要注意：

- Raft log 不只是 WAL。WAL 解决单节点崩溃恢复；Raft 还要建立跨副本的一致顺序和 commit quorum。
- 应用状态机可以使用 WAL 思路，但不宜轻易手写存储引擎。多数业务先使用数据库事务、SQLite 或成熟 KV，再把业务状态机建在其上。

#### WAL、Event Sourcing、Outbox 与普通日志

| 概念 | 核心目的 | 是否通常是业务 source of truth |
|---|---|---|
| WAL | 存储层 crash recovery 与 durability | 否；可 checkpoint、归档或回收 |
| Event Sourcing | 用 domain event 定义和重建业务状态 | 是 |
| Transactional Outbox | 将“业务提交”和“待发送消息”放进同一数据库事务 | Outbox row 是可靠投递意图，不是底层 WAL |
| Consensus log | 在多个副本间建立一致的 command 顺序 | 是 replicated state machine 的提交依据 |
| Observability log | 调试、搜索、监控 | 通常不是 correctness 依赖 |

一个订单系统可能同时拥有：

```text
PostgreSQL WAL
  保证订单表和 outbox 表的事务持久化

Outbox
  保证 OrderPaid 消息最终交给 broker

Domain event
  表达“订单已支付”这个业务事实

Application log
  记录 handler 延迟和错误，供排障
```

四者都可能是 append-only，却承担不同正确性责任。

#### 常见误解与工程边界

- **WAL 不是备份。** 磁盘损坏、误删除或错误操作可能同时影响数据与日志；备份需要独立副本和恢复演练。
- **WAL 不是自动幂等。** recovery 可能重复执行 record，必须用 page LSN、transaction state、sequence 或幂等操作避免二次生效。
- **WAL 不能安全重放任意外部副作用。** 发邮件、扣款、调用外部 API 需要 intent/outcome、idempotency key、receipt 或补偿；不能把日志 replay 直接等同于再次执行。
- **checkpoint 太少会让日志膨胀、恢复变慢；太频繁会增加写放大与延迟。**
- **关闭同步刷盘是在改变 durability contract。** 吞吐提升来自允许掉电后丢失最近提交，不能仍对外宣称严格 durable。

一句话：

> WAL 是“先留下足以恢复的证据，再允许正式状态落盘”的存储协议；Event Sourcing 是业务状态模型，Outbox 是跨系统投递协议，Raft 是复制与共识协议。

### Outbox：把业务提交与异步投递绑定

> 来源：[Transactional Outbox](https://microservices.io/patterns/data/transactional-outbox.html)；文件系统变体参考 [transaction-bound capture](https://github.com/huangruiteng/loopx/blob/e3f9b5366015f6ad7ae306f8b01fc6e2b3e3806b/loopx/control_plane/coordination/local_authority_shadow_outbox.py)、[drain / receipt / cursor](https://github.com/huangruiteng/loopx/blob/e3f9b5366015f6ad7ae306f8b01fc6e2b3e3806b/loopx/control_plane/coordination/local_authority_shadow_adapter.py)。通用机制与该实现的阶段性保证分开理解。

业务状态提交成功之后，消息、搜索索引、shadow store 和 Markdown 视图可能尚未更新。可靠同步需要持久化“这次提交还欠哪些投递”，并在重启后继续完成。

#### Snapshot 的版本归因与 Outbox 的提交边界

事后快照有两个独立问题：采样内容可能属于后续事务；主写入与回调之间存在丢失窗口。

```text
A：提交 Todo「已认领」，revision = 10
B：提交 Todo「已完成」，revision = 11
A：shadow 回调开始采样 → 读到 revision 11
```

revision 11 可以是一份完全一致的快照，却无法代表 A 的提交结果。如果把它绑定到 A 的 operation，就把“此刻看到什么”误当成“那次事务写了什么”。跨文件采样还可能混合不同时间点。MVCC snapshot 能解决一致读，但只有显式绑定目标 revision，才能进一步解决事务归因。

如果 A 在主提交成功后、调用 shadow 前崩溃，内存中的回调还会直接丢失。提高轮询频率只能缩短平均延迟，不能消除这两个正确性窗口。

经典 Transactional Outbox 把业务数据和待投递消息放进同一个数据库事务：

```text
BEGIN
  修改业务状态
  插入 outbox(event_id, aggregate_id, version, payload)
COMMIT

relay：读取已提交 outbox → 投递 → 确认进度 → 按策略回收
```

事务回滚时，两者一起回滚；事务提交时，待投递意图已经持久化。发送可以发生在锁外，由独立进程重试。最终送达仍依赖存储可靠、relay 持续运行、下游恢复可用以及足够的保留期。

文件系统迁移可以采用较弱的 transaction-bound capture：持有主 writer 的同一把锁，先 durable 写 `prepared`（绑定即将写入的内容、摘要和序号），再执行主写入，成功后写 `committed`；释放锁后 drain。锁保证配合该协议的 writer 不交错，但多个文件的写入并未因此成为一个原子事务，仍需要逐个分析 crash window，也不能把它等同于分布式 2PC。

上述参考实现让 shadow 捕获失败不影响主业务提交，并用 typed evidence 报告缺口。这适合默认关闭的迁移观测路径；若对外承诺每个已提交业务效果都有可靠投递，则必须使用同事务 outbox，或提供覆盖全部缺口、经过验证的恢复协议。

Outbox 的 payload 可以是 domain event、delta，也可以是绑定 revision 的完整分区快照。选择快照可简化应用端，但会增加写放大；选择 delta 需要严格定义缺失字段、显式删除、顺序和 schema 演进。Outbox 并不要求系统采用 Event Sourcing，也不自动替代持久化业务主记录。

#### 重试、顺序与投影：保证到哪里

**投递通常是 at-least-once。** 下游已提交、relay 尚未记录 ACK 时崩溃，恢复后会重发。消费端需要把去重 receipt 和业务效果放在同一原子提交边界内：同一 `event_id`、同一 payload digest 返回原结果；同 ID 不同内容应拒绝。幂等保证只覆盖这个边界及其 receipt 保留期，不能自动扩展到邮件、扣款等外部副作用。

**幂等和顺序是两个问题。** revision 11 先渲染完成，迟到的 revision 10 仍可能把文件覆盖回旧版本，即使两次都只执行了一遍。可对同一 aggregate / partition 串行 drain，或在发布阶段用锁、CAS、fencing token 检查单调水位；仅在渲染开始前比较版本不够。独立分区序号不提供跨分区总序或全局一致快照。

恢复时至少检查以下窗口：

| 中断位置 | 恢复要求 |
| --- | --- |
| prepared 已落盘，主写入是否完成不明 | 用可靠提交证据或受锁保护的 readback 判定；无法证明就保留 `unproved`，不能猜成成功。当前值相同也未必能排除 A→B→A 历史 |
| 下游已提交，drain cursor 未前移 | 用原 entry ID 重试，从 receipt 恢复原结果，不能重复业务效果 |
| cursor 已持久化，entry 文件尚未清理 | 当作已消费残留回收，不再分配同一序号或重复应用 |
| cursor 损坏、序列缺口或 schema 不支持 | 停止并报告；按受控协议核对 receipt / reseed。新快照能恢复当前状态，不等于补齐丢失的事务历史 |

迁移过程中，Outbox 的同步方向会随 authority 切换：

```text
切换前：旧主存储 → capture outbox → shadow candidate → 对齐版本后比较
切换后：新 provider → projection outbox → Markdown / 索引 / 旧格式视图
```

Shadow receipt 只证明候选端接收了某条记录。要声称 parity，还需在同一 source revision / 分区水位、同一 schema 与规范化规则下，比较完整业务字段。积压导致候选落后时，应区分“尚未追平”和“相同版本结果不一致”；采样几次一致也不能代替混合 writer 和崩溃恢复验证。

Promotion 需要在受控边界内追平、验证并 fence 旧 writer；之后业务决策只读新 authority。兼容视图可以短暂落后，用 `projection_revision` 暴露新鲜度；需要 read-your-writes 时，可等待投影追到本次写入 receipt 的 revision，或直接读取 authority。渲染器不能因为主存储不可用，就反向把过期视图当成真相。

Domain / projection 分层让 renderer 可以替换；transaction-bound outbox 让提交后的同步可以恢复。二者分别解决数据归属和效果交付，只有组合起来，才能安全地把旧存储降为兼容视图。

### Event Sourcing：用事件日志重建系统状态

> 来源：[Martin Fowler: Event Sourcing](https://martinfowler.com/eaaDev/EventSourcing.html)、[OpenViking discussion #2277: Memory Data Versioning](https://github.com/volcengine/OpenViking/discussions/2277)。

Event Sourcing 的核心是：系统状态不是直接被覆盖保存，而是由一串事件推导出来。

```text
event log
-> replay / projection
-> current state
```

也就是说，系统不只保存“订单现在是什么状态”，而是记录：

```text
OrderSubmitted
PriceChanged
PaymentCaptured
OrderShipped
```

再由 handler / projector 把事件流投影成当前状态。latest state 可以存成 cache / snapshot，但它不是唯一真相；真正可重建、可审计、可回放的是 event log。

#### Event Sourcing 解决什么

| 能力 | 含义 |
| --- | --- |
| Complete rebuild | 从 event log 重新构建当前状态，修复 projection bug 或迁移新模型 |
| Temporal query | 查询某个历史时刻的状态，而不是只看 latest |
| Event replay | 用旧事件流驱动新 handler / projection，验证新逻辑 |
| Parallel model | 同一事件流可以投影出多个 read model / index / report |
| Audit / debugging | 状态如何一步步变成现在这样，有可追踪依据 |

这和普通“记录日志”不一样：日志经常只是观测副产物；Event Sourcing 里的 event 是系统状态变化的源事实。状态表、索引、报表、缓存只是 projection。

#### 版本化 memory：latest projection + reverse diff history

OpenViking 的 memory versioning 设计可以看作 Event Sourcing 的一个工程化变体：memory 文件正文保存最新版本，历史状态通过文件内 `VERSION_HISTORY` 的 reverse diff 链回退得到。

```text
latest memory file
+ VERSION_HISTORY(reverse diffs)
-> materialize_memory_at_version(data_version)
-> historical memory state
```

核心动机不是“想看历史”这么简单，而是让 memory / experience 系统具备按时间回到当时可见状态的能力：

```text
Task A consumes policy view(v1)
Task A finishes -> MemoryPatchApplied(E1) -> data_version=v2
Task B consumes policy view(v2)
```

如果事后只看 latest memory(v2)，就会把 Task A 解释成“明明知道 E1 还做错了”。但 Task A 当时的 policy view 其实是 v1，E1 尚未存在或尚未更新。版本化 memory 的价值，是让分析时能明确区分：

```text
generated_at_version
applied_at_version
consumed_at_version
evaluated_at_version
```

这类字段能避免未来知识污染历史归因。

#### search(data_version) 的近似语义

OpenViking discussion #2277 采用一个低成本一期方案：

```text
search(query, data_version=X)
-> 用最新向量索引召回候选文件
-> 对每个候选文件 materialize 到 <= X 的最近版本
-> 过滤当时不存在或当时已删除的文件
-> 返回目标版本视角下的内容
```

这个设计的优点是不用为每个历史版本维护独立 embedding，存储和索引成本低；缺点也很明确：历史检索不是严格的 historical semantic retrieval，而是“latest recall + historical materialization”的近似。也就是说，它适合做可用的 time-travel read/search，但如果要严格复现过去某次检索结果，还需要记录当时的候选集、ranking score、query、index version 和注入结果。

#### 事件日志、diff history 与 replay 的边界

这组三者要分清：

| 概念 | 关注点 | 在 memory 系统里的映射 |
| --- | --- | --- |
| Event log | 发生了什么状态变化 | `MemoryPatchGenerated`、`MemoryPatchApplied`、`MemoryDeleted`、`MemoryCompacted` |
| Diff history | 如何从一个版本还原到另一个版本 | `VERSION_HISTORY.reverse_diff` |
| Projection | 给读路径用的当前视图 | latest memory file、vector index、overview、summary |
| Replay | 用历史事件或版本重建某个状态 | `materialize_memory_at_version`、rebuild index、offline eval |

Event Sourcing 的长期价值，是让状态变化可以被重放；OpenViking 的版本化方案优先解决的是“按版本读取/检索 memory 文件”。如果未来要支持更强的 replay / eval，还需要把 memory patch 的来源、生成策略、apply 策略、merge 决策和消费证据也记录成事件。

#### 对 memory event log / eval replay 的启发

一个最小 schema 可以这样设计：

```text
memory_event_log_v0:
  event_id
  event_type: source_session_committed | patch_generated | patch_applied | merge_required | conflict_retry | memory_deleted | compacted
  source_session_id
  memory_uri
  src_data_version
  head_data_version
  applied_data_version
  patch_id
  read_set
  write_set
  merge_path
  evaluator_delta
  consumed_by_run_id
```

这里的关键不是把所有东西都做复杂，而是把 latest memory 从“唯一事实”降级为一个 projection。真正用于归因的是：

```text
source trajectory
-> memory event
-> versioned policy view
-> exposure / consumption
-> outcome delta
```

这样才能回答几个重要问题：

- 某次任务执行时，agent 实际可见的是哪个 memory state？
- 一条经验是何时生成、何时 apply、何时第一次被消费的？
- 任务变好是因为 memory update，还是因为随机性 / 环境变化 / evaluator 漂移？
- 如果 memory 后来被改写，历史失败是否仍应按旧版本解释？

#### 实用边界

- Event Sourcing 不是说每次读取都必须从头 replay。生产系统通常会保存 latest projection / snapshot，只在审计、回放、迁移、debug 时回放事件。
- `search(data_version)` 如果只用最新向量召回，就不是严格的历史检索，只是低成本近似。严格历史检索要额外保存 index version 或 retrieval trace。
- diff history 只说明文本如何还原，不说明语义上为什么改。要做 memory learning，还需要记录 patch reason、source trace、evaluator signal 和消费证据。
- 事件 replay 要压制外部副作用：重放时不能重新发消息、下单、调用外部写接口；只能重建状态或在 sandbox 中验证。


### CRDT：让多副本并发更新最终收敛的数据类型

> 来源：[Shapiro et al.: A comprehensive study of Convergent and Commutative Replicated Data Types](https://inria.hal.science/inria-00555588)。

CRDT（Conflict-free Replicated Data Type）的核心是：把数据类型设计成多副本异步更新后，即使没有前台同步协调，也能最终收敛到同一个状态。

它适合解决的是：对天然可交换、可合并的数据结构放宽同步要求，让副本先本地写入，再通过异步传播合并状态。代价是：并不是所有业务约束都能靠 CRDT 自动保证。

#### State-based CRDT / CvRDT

State-based CRDT 传播的是状态本身。状态集合需要构成 join-semilattice：

$$
(S, \le)
$$

merge 操作是 least upper bound：

$$
\operatorname{merge}(x, y) = x \sqcup y
$$

直觉上，`x \sqcup y` 是“刚好包含两个副本全部信息、且不多引入额外信息”的最小共同上界。只要每次本地 update 都让状态单调向上，并且 merge 满足下面三条性质，副本最终就会收敛：

$$
x \sqcup y = y \sqcup x
$$

$$
(x \sqcup y) \sqcup z = x \sqcup (y \sqcup z)
$$

$$
x \sqcup x = x
$$

典型例子：

- **G-Set**：只增集合，`merge = union`。
- **G-Counter**：每个 replica 一个 counter slot，`merge = component-wise max`，读值时求和。

#### Operation-based CRDT / CmRDT

Operation-based CRDT 传播的不是整个 state，而是 operation。只要所有副本最终收到操作，并且并发操作可以 commute，就能收敛。

它通常还需要 causal delivery：如果一个操作依赖另一个操作，那么依赖项必须先送达。否则副本可能先看到后续操作，却缺少解释它的因果前提。

#### 最重要的边界：CRDT 不自动保证全局 invariant

CRDT 不是“无锁万能药”。它保证的是合并收敛，不等于保证所有业务约束都成立。

典型问题是 non-negative counter：两个副本本地都看到余额为 `1`，同时执行 `decrement`，各自本地都合法；异步合并后，全局结果可能变成 `-1`。这类“不小于 0”“库存不能超卖”“权限不能被并发绕过”的全局 invariant，通常仍需要同步、escrow / reservation、中心化 validation，或把约束重新设计成可组合的局部配额。

**应用场景。** 在 agent memory / eval 系统里，CRDT 更适合处理“天然可合并”的辅助状态，例如去重集合、计数器、tag 追加、观测事件集合；不适合直接处理需要全局排序、互斥决策、不可重复消费或严格版本边界的 memory patch 提交。后者更接近 OCC / Event Sourcing / versioned policy view 的问题。


## 代码质量

### 《The Art of Readable Code》 by Dustin Boswell and Trevor Foucher. Copyright 2012 Dustin Boswell and Trevor Foucher, 978-0-596-80229-5

#### chpt 1 Code Should Be Easy to Understand

* Code should be written to minimize the time it would take for someone else to understand it.

#### Part I: Surface Level Improvements

#### chpt 2 Packing Information into Names

* Word Alternatives
  * send: deliver, dispatch, announce, distribute, route
  * find: search, extract, locate, recover
  * start: launch, create, begin, open
  * make: create, set up, build, generate, compose, add, new
* Avoid Generic Names Like tmp and retval
  * `sum_squares += v[i] * v[i];`
  * The name tmp should be used only in cases when being short-lived and temporary is the most important fact about that variable
    * `tmp_file`
  * loop iterators: ci, mi, ui
* Prefer Concrete Names over Abstract Names
  * ServerCanStart() -> CanListenOnPort()
  * `#define DISALLOW_COPY_AND_ASSIGN(ClassName) ...`
* Attaching Extra Information to a Name
  * delay_secs, size_mb, max_kbps, degrees_cw (cw means clockwise)
  * untrustedUrl, **plaintext_**password, **unescaped_**comment, html**_utf8**, data**_urlenc**
  * 拓展：Hungarian notation
    * pszbuffer, z(zero-terminated)
* How Long Should a Name Be?
  * Shorter Names Are Okay for Shorter Scope
  * `ConvertToString()->ToString()`

* Use Name Formatting to Convey Meaning
  * kMaxOpenFile 方便和宏区分
  * 私有成员加下划线后缀

```c++
static const int kMaxOpenFiles = 100;
class LogReader {
  public:
		void OpenFile(string local_file);
	private:
		int offset_;
  	DISALLOW_COPY_AND_ASSIGN(LogReader);
};
```

* about HTML/CSS
  * use underscores to separate words in IDs and dashes to separate words in classes
  * `<div id="middle_column" class="main-content">`

#### chpt 3 Names That Can’t Be Misconstrued

* `filter()` -> `select()` or `exclude()`
* `Clip(text, length)`  -> `truncate(text, max_chars)`
* The clearest way to name a limit is to put `max_` or `min_` in front of the thing being limited.
* when considering ranges
  * Prefer first and last for Inclusive Ranges
  * Prefer begin and end for Inclusive/Exclusive Ranges
* when using bool
  * `read_password` -> `need_password` or `user_is_authenticated`
  * avoid *negated* terms
  * `HasSpaceLeft()` , use `is` or `has`
* Matching Expectations of Users, users may expect `get()` or `size()` to be lightweight methods.
  * `get_mean` -> `compute_mean()`
  * `list::size()`不一定是O(1)
* Example: Evaluating Multiple Name Candidates
  * `inherit_from_experiment_id:` or `copy_experiment:`

#### chpt 4 Aesthetics

* principles
  * Use consistent layout, with patterns the reader can get used to.
  * Make similar code look similar.
  * Group related lines of code into blocks.

* Rearrange Line Breaks to Be Consistent and Compact

```java
public class PerformanceTester {
        // TcpConnectionSimulator(throughput, latency, jitter, packet_loss)
        //                            [Kbps]   [ms]    [ms]    [percent]
        public static final TcpConnectionSimulator wifi =
        		new TcpConnectionSimulator(500, 	80, 		200, 			1);
        public static final TcpConnectionSimulator t3_fiber =
        		new TcpConnectionSimulator(45000, 10, 			0, 			0);
        public static final TcpConnectionSimulator cell =
        		new TcpConnectionSimulator(100,  400, 		250, 			5);
}
```

* Use Methods to Clean Up Irregularity
  * If multiple blocks of code are doing similar things, try to give them the same silhouette.

```c++
void CheckFullName(string partial_name,
                   string expected_full_name,
									 string expected_error) {
  // database_connection is now a class member
  string error;
  string full_name = ExpandFullName(database_connection, partial_name, &error); 			assert(error == expected_error);
  assert(full_name == expected_full_name);
}
```

* Use Column Alignment When Helpful
* Pick a Meaningful Order, and Use It Consistently
  * Match the order of the variables to the order of the `input` fields on the corresponding HTML form.
  * Order them from “most important” to “least important.”
  * Order them alphabetically.
* Organize Declarations into Blocks
* Break Code into “Paragraphs”

```python
def suggest_new_friends(user, email_password):
  # Get the user's friends' email addresses.
  friends = user.friends()
  friend_emails = set(f.email for f in friends)

  # Import all email addresses from this user's email account.
  contacts = import_contacts(user.email, email_password)
  contact_emails = set(c.email for c in contacts)

  # Find matching users that they aren't already friends with.
  non_friend_emails = contact_emails - friend_emails
  suggested_friends = User.objects.select(email__in=non_friend_emails)
  
	# Display these lists on the page.
  display['user'] = user
	display['friends'] = friends
  display['suggested_friends'] = suggested_friends

	return render("suggested_friends.html", display)
```

* Personal Style versus Consistency
  * Consistent style is more important than the “right” style.

#### chpt 5 Knowing What to Comment

The purpose of commenting is to help the reader know as much as the writer did.

* What NOT to Comment
  * Don’t comment on facts that can be derived quickly from the code itself.
  * Don’t Comment Just for the Sake of Commenting
  * Don’t Comment Bad Names—Fix the Names Instead

```python
# remove everything after the second '*'
name = '*'.join(line.split('*')[:2])
```

```c++
// Find a Node with the given 'name' or return NULL.
// If depth <= 0, only 'subtree' is inspected.
// If depth == N, only 'subtree' and N levels below are inspected.
Node* FindNodeInSubtree(Node* subtree, string name, int depth);
```

```c++
// Make sure 'reply' meets the count/byte/etc. limits from the 'request'
void EnforceLimitsFromRequest(Request request, Reply reply);

void ReleaseRegistryHandle(RegistryKey* key);
```

* Recording Your Thoughts
  * Include “Director Commentary”
  * Comment the Flaws in Your Code
  * Comment on Your Constants

```c++
// Surprisingly, a binary tree was 40% faster than a hash table for this data.
// The cost of computing a hash was more than the left/right comparisons.

// This heuristic might miss a few words. That's OK; solving this 100% is hard.

// This class is getting messy. Maybe we should create a 'ResourceNode' subclass to
// help organize things.
```

```c++
// TODO: use a faster algorithm
// TODO(dustin): handle other image formats besides JPEG

// FIXME
// HACK
// XXX: Danger! Major problem here!

// todo: (lower case) or maybe-later:
```

```c++
NUM_THREADS = 8; // as long as it's >= 2 * num_processors, that's good enough.

// Impose a reasonable limit - no human can read that much anyway.
const int MAX_RSS_SUBSCRIPTIONS = 1000;

image_quality = 0.72; // users thought 0.72 gave the best size/quality tradeoff
```

* Put Yourself in the Reader’s Shoes
  * Anticipating Likely Questions
  * Advertising Likely Pitfalls
  * “Big Picture” Comments
  * Summary Comments

```c++
// Force vector to relinquish its memory (look up "STL swap trick")
vector<float>().swap(data);
```

```c++
// Calls an external service to deliver email.  (Times out after 1 minute.)
void SendEmail(string to, string subject, string body);

// Runtime is O(number_tags * average_tag_depth), so watch out for badly nested inputs.
def FixBrokenHtml(html): ...
```

```c++
// This file contains helper functions that provide a more convenient interface to
// our file system. It handles file permissions and other nitty-gritty details.
```

```python
def GenerateUserReport():
  # Acquire a lock for this user
  ...
  # Read user's info from the database
  ...
  # Write info to a file
  ...
  # Release the lock for this user
```

* Final Thoughts—Getting Over Writer’s Block

```c++
// Oh crap, this stuff will get tricky if there are ever duplicates in this list.
--->
// Careful: this code doesn't handle duplicates in the list (because that's hard to do)
```

#### chpt 6 Making Comments Precise and Compact

**Comments should have a high information-to-space ratio.**

* Keep Comments Compact

```c++
// CategoryType -> (score, weight)
typedef hash_map<int, pair<float, float> > ScoreMap;
```

* Avoid Ambiguous Pronouns

```c++
// Insert the data into the cache, but check if it's too big first.
--->
// Insert the data into the cache, but check if the data is too big first.
--->
// If the data is small enough, insert it into the cache.
```

* Polish Sloppy Sentences
  * e.g.  Give higher priority to URLs we've never crawled before.

* Describe Function Behavior Precisely
  * e.g. Count how many newline bytes ('\n') are in the file.
* Use Input/Output Examples That Illustrate Corner Cases

```c++
// ...
// Example: Strip("abba/a/ba", "ab") returns "/a/"
String Strip(String src, String chars) { ... }

// Rearrange 'v' so that elements < pivot come before those >= pivot;
// Then return the largest 'i' for which v[i] < pivot (or -1 if none are < pivot)
// Example: Partition([8 5 9 8 2], 8) might result in [5 2 | 8 9 8] and return 1
int Partition(vector<int>* v, int pivot);
```

* State the Intent of Your Code

```c++
void DisplayProducts(list<Product> products) {
  products.sort(CompareProductByPrice);
  // Display each price, from highest to lowest
  for (list<Product>::reverse_iterator it = products.rbegin(); it != products.rend(); ++it)
    DisplayPrice(it->price);
		... 
	}
```

* “Named Function Parameter” Comments

```c++
void Connect(int timeout, bool use_encryption) { ... }

// Call the function with commented parameters
Connect(/* timeout_ms = */ 10, /* use_encryption = */ false);
```

* Use Information-Dense Words
  * // This class acts as a **caching layer** to the database.
  * // **Canonicalize** the street address (remove extra spaces, "Avenue" -> "Ave.", etc.)

#### Part II: Simplifying Loops and Logic

#### chpt 7 Making Control Flow Easy to Read

* The Order of Arguments in Conditionals
  * `while (bytes_received < bytes_expected)`
* The Order of if/else Blocks
  * Prefer dealing with the *positive* case first instead of the negative—e.g., if (debug) instead of if (!debug).
  * Prefer dealing with the *simpler* case first to get it out of the way. This approach might also allow both the if and the else to be visible on the screen at the same time, which is nice.
  * Prefer dealing with the more *interesting* or conspicuous case first.
* The ?: Conditional Expression (a.k.a. “Ternary Operator”)
  * By default, use an if/else. The ternary ?: should be used only for the simplest cases.
* Avoid do/while Loops

```java
public boolean ListHasNode(Node node, String name, int max_length) {
  while (node != null && max_length-- > 0) {
    if (node.name().equals(name)) return true;
    node = node.next();
  }
  return false;
}
```

```c++
do {
  continue;
} while (false);
// loop just once
```

* Returning Early from a Function
  * cleanup code
    * C++: destructor
    * Java, Python: try finally
      * [Do it with a Python decorator](https://stackoverflow.com/questions/63954327/python-is-there-a-way-to-make-a-function-clean-up-gracefully-if-the-user-tries/63954413#63954413)
    * Python: with
    * C#: using

```c++
struct StateFreeHelper {
  state* a;
  StateFreeHelper(state* a) : a(a) {}
  ~StateFreeHelper() { free(a); }
};

void func(state* a) {
  StateFreeHelper(a);
  if (...) {
    return;
  } else {
    ...
  }
}
```

```python
def do_stuff(self):
  self.some_state = True
  try:
    # do stuff which may take some time - and user may quit here
  finally:
    self.some_state = False
```

* The Infamous goto
  * 问题在于滥用，比如多种goto混合、goto到前面的代码
* Minimize Nesting
  * Removing Nesting by Returning Early
  * Removing Nesting Inside Loops: use continue for independent iterations

* Can You Follow the Flow of Execution?

![flow](./Software-Engineering/flow_of_execution.png)

#### chpt 8 Breaking Down Giant Expressions

* Explaining Variables

```python
username = line.split(':')[0].strip()
if username == "root":
	...
```

* Summary Variables

```java
final boolean user_owns_document = (request.user.id == document.owner_id);
if (user_owns_document) {
}
...
if (!user_owns_document) {
  // document is read-only...
}
```

* Using De Morgan’s Laws
* Abusing Short-Circuit Logic
  * There is also a newer idiom worth mentioning: in languages like Python, JavaScript, and Ruby, the “or” operator returns one of its arguments (it doesn’t convert to a boolean), so code like: x = a || b || c, can be used to pick out **the first “truthy” value** from a, b, or c.

```c++
assert((!(bucket = FindBucket(key))) || !bucket->IsOccupied());
--->
bucket = FindBucket(key);
if (bucket != NULL) assert(!bucket->IsOccupied());
```

* Example: Wrestling with Complicated Logic

```c++
struct Range {
	int begin;
	int end;
  // For example, [0,5) overlaps with [3,8)
  bool OverlapsWith(Range other);
};

bool Range::OverlapsWith(Range other) {
  return (begin >= other.begin && begin < other.end) ||
         (end > other.begin && end <= other.end) ||
         (begin <= other.begin && end >= other.end);
}

bool Range::OverlapsWith(Range other) {
  if (other.end <= begin) return false;  // They end before we begin
  if (other.begin >= end) return false;  // They begin after we end
  return true;  // Only possibility left: they overlap
}
```

* Breaking Down Giant Statements

* Another Creative Way to Simplify Expressions

```c++
 void AddStats(const Stats& add_from, Stats* add_to) {
   #define ADD_FIELD(field) add_to->set_##field(add_from.field() + add_to->field())
   ADD_FIELD(total_memory);
   ADD_FIELD(free_memory);
   ADD_FIELD(swap_memory);
   ADD_FIELD(status_string);
   ADD_FIELD(num_processes);
   ...
   #undef ADD_FIELD
 }
```

#### chpt 9 Variables and Readability

* Eliminating Variables
  * Useless Temporary Variables
  * Eliminating Intermediate Results
  * Eliminating Control Flow Variables
* Shrink the Scope of Your Variables
  * Another way to restrict access to class members is to **make as many methods static as possible**. Static methods are a great way to let the reader know “these lines of code are isolated from those variables.”
  * break the large class into smaller classes
  * if Statement Scope in C++
  * Creating “Private” Variables in JavaScript
  * JavaScript Global Scope
    * always define variables using the var keyword (e.g., var x = 1)
  * No Nested Scope in Python and JavaScript
    * 在最近祖先手动定义 xxx = None
  * Moving Definitions Down

```c++
if (PaymentInfo* info = database.ReadPaymentInfo()) {
  cout << "User paid: " << info->amount() << endl;
}
```

```javascript
var submit_form = (function () {
	var submitted = false; // Note: can only be accessed by the function below
	return function (form_name) {
    if (submitted) {
      return;  // don't double-submit the form
    }
		...
		submitted = true;
  };
}());
```

* Prefer Write-Once Variables
  * The more places a variable is manipulated, the harder it is to reason about its current value.
* A Final Example

```javascript
var setFirstEmptyInput = function (new_value) {
  for (var i = 1; true; i++) {
    var elem = document.getElementById('input' + i);
    if (elem === null)
      return null;  // Search Failed. No empty input found.
    if (elem.value === '') {
      elem.value = new_value;
      return elem;
    }
  }
};
```

#### Part III: Reorganizing Your Code

#### chpt 10 Extracting Unrelated Subproblems

* Introductory Example: findClosestLocation()
* Pure Utility Code
  * read file to string
* Other General-Purpose Code

```javascript
var format_pretty = function (obj, indent) {
  // Handle null, undefined, strings, and non-objects.
  if (obj === null) return "null";
  if (obj === undefined) return "undefined";
  if (typeof obj === "string") return '"' + obj + '"';
  if (typeof obj !== "object") return String(obj);
  if (indent === undefined) indent = "";
  // Handle (non-null) objects.
  var str = "{\n";
  for (var key in obj) {
    str += indent + "  " + key + " = ";
    str += format_pretty(obj[key], indent + " ") + "\n";
  }
  return str + indent + "}";
};
```

* Create a Lot of General-Purpose Code

* Project-Specific Functionality

```python
CHARS_TO_REMOVE = re.compile(r"['\.]+")
CHARS_TO_DASH = re.compile(r"[^a-z0-9]+")

def make_url_friendly(text):
  text = text.lower()
  text = CHARS_TO_REMOVE.sub('', text)
  text = CHARS_TO_DASH.sub('-', text)
  return text.strip("-")

business = Business()
business.name = request.POST["name"]
business.url = "/biz/" + make_url_friendly(business.name)
business.date_created = datetime.datetime.utcnow()
business.save_to_database()
```

* Simplifying an Existing Interface
* Reshaping an Interface to Your Needs

```python
def url_safe_encrypt(obj):
  obj_str = json.dumps(obj)
  cipher = Cipher("aes_128_cbc", key=PRIVATE_KEY, init_vector=INIT_VECTOR, op=ENCODE)
  encrypted_bytes = cipher.update(obj_str)
  encrypted_bytes += cipher.final() # flush out the current 128 bit block
  return base64.urlsafe_b64encode(encrypted_bytes)
```

* Taking Things Too Far

#### chpt 11 One Task at a Time

* Tasks Can Be Small
  * e.g. 分解 old vote 和 new vote
* Extracting Values from an Object

```javascript
var first_half, second_half;

if (country === "USA") {
  first_half = town || city || "Middle-of-Nowhere";
  second_half = state || "USA";
} else {
  first_half = town || city || state || "Middle-of-Nowhere";
  second_half = country || "Planet Earth";
}

return first_half + ", " + second_half;
```

* A Larger Example

#### chpt 12 Turning Thoughts into Code

* Describing Logic Clearly
  *  “rubber ducking”
  *  You do not really understand something unless you can explain it to your grandmother. —Albert Einstein

```php
if (is_admin_request()) {
  // authorized
} elseif ($document && ($document['username'] == $_SESSION['username'])) {
  // authorized
} else {
  return not_authorized();
}
// continue rendering the page ...
```

* Knowing Your Libraries Helps
* Applying This Method to Larger Problems

```python
def PrintStockTransactions():
  stock_iter = ...
	price_iter = ...
  num_shares_iter = ...

  while True:
    time = AdvanceToMatchingTime(stock_iter, price_iter, num_shares_iter)
    if time is None:
      return

    # Print the aligned rows.
    print "@", time,
    print stock_iter.ticker_symbol,
    print price_iter.price,
    print num_shares_iter.number_of_shares

    stock_iter.NextRow()
    price_iter.NextRow()
    num_shares_iter.NextRow()
    
def AdvanceToMatchingTime(row_iter1, row_iter2, row_iter3):
  while row_iter1 and row_iter2 and row_iter3:
    t1 = row_iter1.time
    t2 = row_iter2.time
    t3 = row_iter3.time

    if t1 == t2 == t3:
      return t1

    tmax = max(t1, t2, t3)

    # If any row is "behind," advance it.
    # Eventually, this while loop will align them all.
    if t1 < tmax: row_iter1.NextRow()
    if t2 < tmax: row_iter2.NextRow()
    if t3 < tmax: row_iter3.NextRow()

  return None  # no alignment could be found
```

#### chpt 13 Writing Less Code

* Don’t Bother Implementing That Feature—You Won’t Need It
* Question and Break Down Your Requirements
  * Example: A Store Locator ---- For any given user’s latitude/longitude, find the store with the closest latitude/longitude.
    * When the locations are on either side of the International Date Line
    * When the locations are near the North or South Pole
    * Adjusting for the curvature of the Earth, as “longitudinal degrees per mile” changes
  * Example: Adding a Cache
* Keeping Your Codebase Small

* Be Familiar with the Libraries Around You
  * Example: Lists and Sets in Python
* Example: Using Unix Tools Instead of Coding
  * When a web server frequently returns 4xx or 5xx HTTP response codes, it’s a sign of a potential problem (4xx being a client error; 5xx being a server error). 

#### PART IV Selected Topics

#### chpt 14 Testing and Readability

* testing中的一些概念：
  * 单测：单元性和隔离性
  * property-based testing 常用于单测，也可以作用于组件、状态机或 API；它是一种输入生成与 invariant 验证方法，不是固定的测试层级
  * 完整的测试层次、Gherkin、coverage 与 mutation testing 见[软件测试与质量保障](#软件测试与质量保障从规格到生产)



* Make Tests Easy to Read and Maintain
* What’s Wrong with This Test?

```c++
void CheckScoresBeforeAfter(string input, string expected_output) {
  vector<ScoredDocument> docs = ScoredDocsFromString(input);
  SortAndFilterDocs(&docs);
  string output = ScoredDocsToString(docs);
  assert(output == expected_output);
}

vector<ScoredDocument> ScoredDocsFromString(string scores) {
  vector<ScoredDocument> docs;
  replace(scores.begin(), scores.end(), ',', ' ');
  // Populate 'docs' from a string of space-separated scores.
  istringstream stream(scores);
  double score;
  while (stream >> score) {
    AddScoredDoc(docs, score);
  }
  return docs;
}
string ScoredDocsToString(vector<ScoredDocument> docs) {
  ostringstream stream;
  for (int i = 0; i < docs.size(); i++) {
    if (i > 0) stream << ", ";
    stream << docs[i].score;
  }
  return stream.str();
}
```

* Making Error Messages Readable
  * Python `import unittest`

```c++
BOOST_REQUIRE_EQUAL(output, expected_output)
```

* Choosing Good Test Inputs
  * In general, you should pick the simplest set of inputs that completely exercise the code.
  * Simplifying the Input Values
    * -1e100、-1
    * it’s more effective to construct large inputs programmatically, constructing a large input of (say) 100,000 values
* Naming Test Functions
* What Was Wrong with That Test?

* Test-Friendly Development
  * Test-driven development (TDD)
  * Table 14.1: Characteristics of less testable code
    * Use of global variables ---> gtest set_up()
    * Code depends on a lot of external components
    * Code has nondeterministic behavior

* Going Too Far
  * Sacrificing the readability of your real code, for the sake of enabling tests.
  * Being obsessive about 100% test coverage.
  * Letting testing get in the way of product development.

#### chpt 15 Designing and Implementing a “Minute/Hour Counter”

* Defining the Class Interface

```c++
// Track the cumulative counts over the past minute and over the past hour.
// Useful, for example, to track recent bandwidth usage.
class MinuteHourCounter {
  // Add a new data point (count >= 0).
  // For the next minute, MinuteCount() will be larger by +count. 
  // For the next hour, HourCount() will be larger by +count.
  void Add(int count);

  // Return the accumulated count over the past 60 seconds.
  int MinuteCount();
  
  // Return the accumulated count over the past 3600 seconds.
  int HourCount();
};
```

* Attempt 1: A Naive Solution
  * list, reverse_iterator，效率低
* Attempt 2: Conveyor Belt Design
  * 两个传送带，内存消耗大，拓展成本高
* Attempt 3: A Time-Bucketed Design
  * 本质利用了统计精度可牺牲的特点，离散化实现

```c++
// A class that keeps counts for the past N buckets of time.
class TrailingBucketCounter {
  public:
    // Example: TrailingBucketCounter(30, 60) tracks the last 30 minute-buckets of time.
    TrailingBucketCounter(int num_buckets, int secs_per_bucket);
    void Add(int count, time_t now);
    // Return the total count over the last num_buckets worth of time
    int TrailingCount(time_t now);
};
class ConveyorQueue;
```
