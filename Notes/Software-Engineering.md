# Software Engineering


[toc]

## Intro

> todo 《A Philosophy of Software Design》
>
> todo 《Software Design X-Rays》

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

#### 和锁、Event Sourcing、CRDT 的关系

| 机制 | 核心思路 | 适合场景 |
| --- | --- | --- |
| Pessimistic locking | 先加锁，再读写，提前阻止冲突 | 冲突率高、写入代价大、不能接受重试 |
| OCC | 先并发执行，提交前验证，不通过就 retry | 冲突率低、读多写少、希望减少锁等待 |
| Event Sourcing | 把状态变化记录成事件流，用 replay / projection 重建状态 | 需要审计、回放、历史状态、并行 read model |
| CRDT | 让并发更新天然可合并，减少中心化冲突检测 | 分布式、离线、多副本协作编辑 |

OCC 解决的是 **提交时能不能接受这次写入**；Event Sourcing 解决的是 **状态变化如何被记录、重放和审计**；CRDT 解决的是 **多个副本并发更新如何自动收敛**。它们不是互斥关系：一个系统可以用 OCC 做提交验证，用 event log 记录已通过的提交，再用 projection 服务读路径。

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
  * property-based testing属于单测



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
