# Functional Programming

[toc]

入门顺序：纯函数 → [代数数据类型](#代数数据类型积和与合法状态) → [Monoid 与组合器](#monoid-与组合器从合并值到组合动作) → effect 的描述与执行 → [Tagless Final 的效果抽象](#组合式设计组合器数据与效果抽象)；TypeScript 语法例子通过下文链接展开。

## 组合式设计：组合器、数据与效果抽象

gcanti 的 Functional Design 前三篇是一条递进路线：先让能力可以组合，再让调用方决定如何使用结果，最后让调用方选择效果实现；第 4–6 篇接着讨论合法值的构造、按类型拆解实现，以及合法状态的建模。

| 篇目 / 来源 | 设计变化 | 关键例子与笔记 |
|---|---|---|
| ① [Combinators](https://dev.to/gcanti/functional-design-combinators-14pn) | 少量 primitives + 可反复组合的 combinators，生成复杂能力 | `Eq<A> → Eq<ReadonlyArray<A>>`；`Monoid<A> → Monoid<IO<A>>`；[time](./TypeScript.md#io-的-time用-chain-串联动作用-map-保留结果) 为动作加计时 |
| ② [让 time 更通用](https://dev.to/gcanti/functional-design-how-to-make-the-time-combinator-more-general-3fge) | 把固定的“打印耗时”改为返回 `[结果, 耗时]`，测量与消费策略分开 | `IO<A> → IO<[A, number]>`；调用方可打印、忽略耗时，或用 [fastest](./TypeScript.md#fastest用-ord-与-semigroup-选择耗时最短的结果) 选择结果 |
| ③ [Tagless Final](https://dev.to/gcanti/functional-design-tagless-final-332k) | 把写死的 IO 操作改为 `MonadIO<F>` 参数，同一流程支持不同效果 | `F<A> → F<[A, number]>`；传 IO 实现得到同步计时，传 Task 实现得到异步计时；[代码读法](./TypeScript.md#tagless-final-与-monadio把效果实现作为参数) |
| ④ [Smart constructors](https://dev.to/gcanti/functional-design-smart-constructors-14nb) | 运行时检查约束，再把合法性保留在类型里 | `make: T → Option<R>`；[品牌、谓词与受检构造入口](./TypeScript.md#smart-constructor校验品牌与构造边界) |
| ⑤ [类型驱动开发](https://dev.to/gcanti/functional-design-tdd-in-typescript-aka-abusing-declare-59il) | 先写目标和辅助函数的类型，再逐步填实现 | [sequence → reduce → liftA2](./TypeScript.md#类型驱动开发用-declare-拆解实现)；编译器约束组合方式，运行语义仍需验证 |
| ⑥ [Algebraic Data Types](https://dev.to/gcanti/functional-design-algebraic-data-types-36kf) | 独立字段用积类型，互斥场景用和类型 | [积、和与合法状态](#代数数据类型积和与合法状态)；Option / Either 显式表达缺失与失败 |

组合器的重点是输出能继续参与组合，不要求具体类型完全不变：`getEq(getEq(numberEq))` 可以从数字比较逐层得到二维数组比较；`time(replicateIO(3, time(action)))` 可以同时测每次和整体耗时。这里的 combinator 指库设计模式，不是组合逻辑中“无自由变量”的严格定义。

Tagless Final 的动机是复用程序结构：`开始计时 → 执行动作 → 结束计时 → 返回二元组` 不应因 IO / Task 不同而复制。程序依赖类型化的能力接口，实现负责解释这些操作；本文采用 Tagless Final / MTL 风格，接口是 `MonadIO`，instance 是普通操作字典。`tagless` 指不依靠逐个语法节点的运行时标签组织程序，`final` 指以操作及其解释来表示程序，不要求先构造 AST 再遍历解释，也不是 `finally` 或“最后执行”。

基础关系：`map` 转换动作的结果；`chain` 根据前一步结果串联下一动作；`of` 把纯值放入效果；`fromIO` 把已有同步动作提升到目标效果。IO 的 `fromIO` 原样保留函数，Task 的 `fromIO` 包装成惰性的 Promise 动作。选择实现、构造动作、执行动作是三个阶段。

[`liftA2`](./TypeScript.md#lifta2把二元函数提升到-promise) 展示另一种提升：将普通二元函数 `(A, B) => C` 变成 `(Promise<A>, Promise<B>) => Promise<C>`，保留 f 的计算逻辑，由组合器负责取得两个输入值。名字中的 A 指 Applicative，2 指二元；两个输入没有数据依赖，具体的等待、并发与失败传播方式由实现决定。

边界：`fastest` 顺序执行全部候选再选结果，落败者的副作用也发生；Tagless Final 只复用流程结构，并不保证不同实现有相同的执行语义。本文示例只编码一元类型构造器，扩到 `TaskEither` / `ReaderTaskEither` 还需处理错误、环境等类型参数。

## 代数数据类型：积、和与合法状态

来源：[Functional design: Algebraic Data Types](https://dev.to/gcanti/functional-design-algebraic-data-types-36kf)。ADT 用已有类型组合领域模型；关键是模型允许的状态，是否正好对应业务允许的状态。

| 形式 | 含义与适用场景 | 例子 |
|---|---|---|
| 积类型（product） | 同时包含各部分；字段可自由组合时适用 | tuple `[Hour, Period]`、结构体 `{ name, age }` |
| 和类型（sum） | 互斥分支中选一个；分支内部仍可包含多个字段 | 带 tag 的 READONLY / EDITABLE、None / Some、Left / Right |

对有限状态集合，积的状态数相乘；带标签保证分支不相交时，和的状态数相加：

$$
|A \times B| = |A| \cdot |B|, \qquad |A + B| = |A| + |B|
$$

例如 `[Hour, Period]` 有 12 × 2 = 24 种状态，`Option<boolean>` 有 None、Some(false)、Some(true) 共 3 种。普通 TypeScript 联合若有重叠，不能直接相加计数；这里的和指互不重叠的分支。

字段存在依赖时，独立排列会多出非法状态：`editable: boolean` 与可选 `onChange` 允许“可编辑却没有回调”；改成 READONLY / EDITABLE 两个分支，只在后者要求 onChange。类似地，错误优先回调的 err / data 按有无可组合成 4 种状态，但约定只允许“有错误”或“有数据”两种，可改为 `Either<Error, string>`。具体写法见 [判别联合](./TypeScript.md#判别联合与-never状态机的穷尽检查)。

| 常见和类型 | 建模目的 |
|---|---|
| `Option<A>`：None / Some(A) | 表示值可能不存在；如空数组取首项返回 None，失败不再隐藏在返回 A 的签名外 |
| `Either<E, A>`：Left(E) / Right(A) | 保留失败原因；按约定 Left 失败、Right 成功，对应 io-ts 的解码结果 |
| `List<A>`：Nil / Cons(A, List<A>) | 泛型与递归可组合：空链表，或一个元素加剩余链表 |

构造器（如 none / some）创建分支；`fold` 接收每个分支的处理函数，把整个和类型消解为共同结果 R。原文的 List.fold 只分派当前节点，链表长度通过 Cons 分支里的 `1 + length(tail)` 显式递归；fold 并不自动遍历整张结构。TypeScript 也可用 switch 收窄，并通过 never 检查是否漏分支。

## 纯函数、Functional Effect 与 ZIO

来源：Scalac，[Introduction to Programming with ZIO Functional Effects](https://scalac.io/blog/introduction-to-programming-with-zio-functional-effects/)（2021-02 首发，已随 ZIO 2.0 更新）。

![Scalac ZIO 文章封面](./Functional-Programming/zio-cover.jpg)

整体：程序是纯函数的组合；但真实应用必须读写控制台、调 API、查数据库。文章用 Hangman 演示矛盾怎么解：领域模型全部写成纯函数，交互写成 functional effect（对外部世界的“描述”），最后在 `run` 这个“世界尽头”由 ZIO Runtime 真正执行。

### 纯函数三性质

- **Total（全函数）**：每个输入都有定义好的输出。`def divide(a: Int, b: Int): Int` 在 `b = 0` 时抛异常，签名等于撒谎；改成 `Option[Int]` 后失败显式化，编译器强制调用方处理 `None`。
- **Deterministic（确定性）**：同一输入必然同一输出。`generateRandomInt(): Int` 隐藏了对 `scala.util.Random` 的依赖，两次调用结果不同；改成 `RNG(seed) => (Int, RNG)` 后随机状态显式传入并返回新状态，同一 seed 永远得到同一结果。
- **无副作用**：不改内存、不打控制台、不调 API / DB；只能基于不可变值、只返回输出。

收益：局部推理（local reasoning）、更少 bug、易测试、行为可预测、并发安全（没有共享可变状态就没有 race condition）。

一个 TypeScript 入门例子是 [`fp-ts getEq`](./TypeScript.md#fp-ts-eq从元素比较规则生成数组比较规则)：把元素比较规则 `Eq<A>` 作为参数，构造数组比较规则 `Eq<ReadonlyArray<A>>`。它展示如何用普通对象和函数组合规则；链接中保留 import、泛型、箭头函数与 `every` 的逐项语法解释。

接着看 [`contramap`、柯里化与部分应用](./TypeScript.md#contramap连续箭头函数柯里化与闭包)：`f => E => ...` 是函数返回函数，按 `contramap(f)(E)` 分两次传参；闭包保留先传入的规则，让“按 id 提取再比较”成为可复用的对象比较器。

![FP vs OOP 对比图](./Functional-Programming/fp-vs-oop.png)

### Monoid 与组合器：从合并值到组合动作

> 来源：gcanti，[Functional design: combinators](https://dev.to/gcanti/functional-design-combinators-14pn)，Example 2–3。

**Monoid（幺半群）= 一种值类型 + 合并操作 concat + 单位元 empty**。合并两个值仍得到同类型的值；满足结合律，empty 放在左右都不改变结果。不要求交换律，所以动作顺序不能随意互换。

**Semigroup（半群）**只要求满足结合律的 concat，不要求 empty。非空输入可直接用首项作为归约初值：例如 [`fastest(head, tail)`](./TypeScript.md#fastest用-ord-与-semigroup-选择耗时最短的结果) 先将每次执行变成 `[结果, 耗时]`，用 Ord 定义按耗时排序，再用 Semigroup 保留较小者。head 保证至少一个候选；返回耗时数据使日志、选择等策略可以由调用者组合。

| 值 | concat | empty |
|---|---|---|
| 整数 | 相加 | 0 |
| 字符串 | 按顺序拼接 | 空字符串 |
| 无有用返回值的动作 `IO<void>` | 先执行左动作，再执行右动作 | 不做事的动作 |

`IO<A>` 在这个例子里就是 `() => A`：调用后执行并返回 A 的同步函数。`getMonoid(M)` 将“合并两个 A 的规则”提升为“组合两个 IO<A> 的规则”：先执行两个动作，再用 M 合并结果；组合过程本身只创建新函数。`Monoid<void>` 忽略返回值，但不会取消动作的执行。代码见 [TypeScript：IO 与 Monoid](./TypeScript.md#io-与-monoid把多个动作组合成一个动作)。

`replicateIO(3, action)` 将三个动作合成一个 `IO<void>`，末尾再加 `()` 才执行；[`time(action)`](./TypeScript.md#io-的-time用-chain-串联动作用-map-保留结果) 用 chain 串起取时间、执行与日志，再用 map 保留原结果 A。组合后仍保留相同接口，因而能继续组合。与前面的 Eq 例子贯通：`getEq` 扩展比较规则，`contramap` 预处理比较输入，`getMonoid` 组合动作；库用少量基本值和组合器构造更复杂的能力。

单位元也解释了空集合归约为什么有默认结果：见 [空集的极值与单位元](./mathematics.md#空集的极值与单位元)。

### 描述世界交互，而非直接执行

> instead of writing functions that interact with the outside world, we write **functions that describe interactions with the outside world**, which are executed only at a specific point in our application, (usually called the **end of the world**) for example the main function.

副作用描述本身是不可变值，可以像普通数据一样做纯函数的输入输出，因此不违反“无副作用”原则。“end of the world”就是程序边界（`main` / `ZIOAppDefault.run`）：功能世界在这里结束，描述被真正执行，越晚越好。这些描述就是 **functional effect**。

### ZIO：`R => Either[E, A]`

`ZIO[-R, +E, +A]` 是不可变的 functional effect，心智模型：

```text
R => Either[E, A]
```

- `R`：运行所需 context（DB 连接、REST client、config），逆变；
- `E`：可能失败的错误类型，协变；
- `A`：成功时返回的值，协变。

只看签名就能知道：依赖什么环境、会不会失败、失败类型是什么、成功返回什么。常用别名：

| Alias | 展开 | 含义 |
|---|---|---|
| `Task[A]` | `ZIO[Any, Throwable, A]` | 无需环境，可失败 |
| `UIO[A]` | `ZIO[Any, Nothing, A]` | 无需环境，不可失败 |
| `RIO[R, A]` | `ZIO[R, Throwable, A]` | 需要环境，可失败 |
| `IO[E, A]` | `ZIO[Any, E, A]` | 无需环境，可失败 |
| `URIO[R, A]` | `ZIO[R, Nothing, A]` | 需要环境，不可失败 |

Hangman 里用到的组合方式：

- `flatMap` / for-comprehension：顺序组合，后一步依赖前一步结果，前一步失败则短路；
- `<*>`（zip）/ `*>`（zipRight）：组合两个 effect，ZIO 2 的 Compositional Zips 会自动丢弃 `Unit`，所以 `Console.printLine(msg) <*> Console.readLine` 直接得到 `String`；
- `<>`（orElse）：第一个 effect 失败时才执行第二个（输入校验失败后重试）；
- `ZIO.succeed / ZIO.from / ZIO.attempt`：把纯值、`Option`、可能抛异常的表达式提升为 effect；
- `orDie / orDieWith`：把“逻辑上不可能失败”的失败视为 defect，直接崩溃，不进入业务错误路径。

`ZIOAppDefault.run` 只返回一个 effect；ZIO Runtime 负责把它真正翻译成副作用。失败则记日志并返回非零退出码，这就是应用的 end of the world：

```scala
val run: IO[IOException, Unit] =
  for {
    name <- Console.printLine("Welcome to ZIO Hangman!") <*> getName
    word <- chooseWord
    _    <- gameLoop(State.initial(name, word))
  } yield ()
```

### Smart constructor：让非法状态不可构造

来源补充：gcanti，[Functional design: smart constructors](https://dev.to/gcanti/functional-design-smart-constructors-14nb)。通用模式是 `make: T → Option<R>`：在系统边界检查原始值，失败返回 None，成功才给出满足领域约束的 R；业务 API 只接收 R，并收紧未经检查的构造入口。

TypeScript 中，运行时条件（如 `s.length > 0`）真正验证值；类型谓词 `s is NonEmptyString` 让编译器将通过检查的值视为品牌类型。品牌将“已校验”这一信息带到后续调用，但谓词实现仍须正确，类型断言 / any 可绕过它；“非法状态不可构造”成立于受控构造与类型检查的边界内。详见 [校验、品牌与构造边界](./TypeScript.md#smart-constructor校验品牌与构造边界)。

[io-ts](https://github.com/gcanti/io-ts/blob/864a3a2f03c5d7b974afeb1da0faf46c21758779/index.md#the-idea) 将这条路线接回组合器：用基础 codec 构造对象、数组、联合与品牌校验，`decode` 返回 `Either<Errors, A>` 保留失败原因，`TypeOf` 从同一份定义提取业务类型。系统边界完成解码，内部传递成功值；代码与 decode / is / encode 的区别见 [TypeScript：io-ts](./TypeScript.md#io-ts由运行时-codec-推导静态类型)。

领域对象想保证不变量（Name 非空、Guess 恰好一个字母），但 case class 自动生成的 `apply` / `copy` 会绕过校验，递进方案：

1. `final case class Name(name: String)` + companion 的 `make` 做校验 → `apply` / `copy` 仍可造出非法值；
2. `final case class private Name(...)` → 原生构造器私有，但 `apply` / `copy` 还在；
3. `sealed abstract case class Name private (...)` → 不生成 `apply` / `copy`，唯一构造入口是 `make`。

```scala
sealed abstract case class Guess private (char: Char)
object Guess {
  def make(str: String): Option[Guess] =
    Some(str.toList).collect {
      case c :: Nil if c.isLetter => new Guess(c.toLower) {}
    }
}
```

`make` 本身是纯函数：total（用 `Option` 表达失败）、deterministic（只依赖 `str`）、无副作用。`c :: Nil` 要求恰好一个字符，`isLetter` 排除数字和符号，`toLower` 统一小写——业务代码拿到 `Guess` 后无需再校验。`Word.make`、`State.addGuess` 同理；`GuessResult` 用 sealed trait 表达枚举，pattern match 漏分支时编译器会警告。

与 [Algebraic Effects 与 Effect Handlers](#algebraic-effects-与-effect-handlers分离做什么和如何执行) 对照：ZIO 是 functional effect 的工程化实现，把“描述 effect”与“执行 effect”分离成类型和 Runtime；同一套思想在 Agent runtime 里对应 intent 与 handler。

## Algebraic Effects 与 Effect Handlers：分离“做什么”和“如何执行”

函数式编程并不等于“完全没有副作用”。更实用的目标是把纯计算与外部作用分开描述：程序声明自己需要读取文件、发送消息或查询状态，但不在业务逻辑里固定这些操作如何到达真实世界。`algebraic effects` 用抽象 operation 表达“做什么”，`effect handler` 决定“如何解释”。

### Effect 不是普通日志事件

一个 algebraic effect 首先是一组带类型的抽象操作，例如：

```text
ReadFile   : Path -> String
SendMessage: Message -> Unit
GetState   : Unit -> State
PutState   : State -> Unit
```

程序通过 `perform` 发出操作，而不是直接调用固定实现：

```text
program():
  text = perform ReadFile("report.md")
  perform SendMessage(summarize(text))
```

运行到 `perform ReadFile(...)` 时，当前计算在该点暂停；最近的 handler 获得 operation、参数，以及“拿到结果后如何继续”的 continuation。Handler 可以返回真实结果并恢复 continuation，也可以拒绝、改写、重试，甚至让 continuation 执行多次。因此，把 effect 说成“reified typed event”适合作为工程直觉，但严格来说它不仅是被记录的数据，还包含一次可被 handler 解释的控制转移。

### 同一程序可以更换解释器

程序源码只依赖 effect interface，不依赖具体 handler：

| Handler | `ReadFile` 的解释 | `SendMessage` 的解释 |
|---|---|---|
| Production | 读取真实文件 | 调用真实消息 API |
| Audit | 读取后追加 typed record | 记录发送意图并继续 |
| Dry-run | 返回 fixture / snapshot | 只产生 preview，不外发 |
| Permission | 检查 capability 后执行 | 未授权时拒绝 |
| Replay | 返回历史记录中的 outcome | 压制不可重复的外部副作用 |
| Test | 返回 mock value | 收集断言对象 |

核心价值是：

> 业务程序描述 effect；运行环境提供 effect 的语义。替换执行、审计、测试或权限策略时，不必改写业务程序本身。

### Handler 与 continuation

Handler 的能力来自它同时拿到 effect 和 continuation `k`：

```text
handle ReadFile(path, k):
  value = filesystem.read(path)
  audit.append({operation: "ReadFile", path, value_hash: hash(value)})
  return k(value)
```

它可以采用不同控制策略：

- `k(value)`：正常恢复一次；
- 不调用 `k`：中止、拒绝或短路；
- 修改 `value` 后恢复：mock、fallback、fault injection；
- 多次调用 `k`：从同一中间点探索多个 continuation；
- 保存 `k` 稍后恢复：暂停、审批、resume。

这使异常、状态、异步、回溯搜索、权限 gate 等机制可以在同一抽象下讨论。工程实现不一定真的把语言 continuation 暴露出来，也可以用状态机、生成器、协程或持久 execution trace 模拟相同结构。

### 和 callback、middleware、Monad 的区别

| 机制 | 谁控制“如何执行” | 主要特点 |
|---|---|---|
| Callback | 业务代码显式接收并调用 callback | 简单直接，但 callback 会渗入函数签名和控制流 |
| Middleware | 预先固定的一条调用管线 | 适合请求级横切逻辑，通常围绕既定入口工作 |
| Monad | 用类型与组合操作显式编码 effectful computation | 强调顺序组合；具体 effect 集合和解释方式往往绑定得更紧 |
| Algebraic effect + handler | 程序 perform operation，局部 handler 解释 | operation 与 interpretation 分离，handler 可嵌套、替换并控制 continuation |

不能简单说 algebraic effects “优于” Monad；两者都在管理 effect，只是模块化边界不同。Algebraic effects 更适合表达“同一操作需要多种局部解释”，例如 production、sandbox、audit、replay 和 deny。

### Non-perturbing observation 的条件

只读 observer handler 可以把 effect 追加到不可变 stream，再以相同返回值和相同恢复顺序继续执行。这样，是否安装 observer 不需要改变业务程序的输入、输出或 source code，这是“观察而不干扰”的理论基础。

但 non-perturbing 不是自动获得的现实保证：记录仍可能增加延迟、改变并发时序、触发 backpressure，handler 也可能错误修改返回值或恢复次数。严谨的 runtime 还需要不可变记录、只读订阅接口、顺序和 identity 约束，以及对 timing-sensitive behavior 的单独验证。

### 映射到 Agent Runtime

[Shepherd §3.2](https://arxiv.org/html/2605.10913v3#S3.SS2) 把这套语言设计迁移到 Agent execution：

| Functional Programming | Agent Runtime |
|---|---|
| Typed function | task / agent definition |
| Algebraic effect | model call、tool call、file operation、message intent |
| Effect handler | provider、sandbox、permission gate、recorder、simulator |
| Region-scoped handler | Agent scope / isolated execution region |
| Continuation | pause、resume、fork 后的后续执行 |
| Persistent effect record | execution trace / effect stream |

Worker 只表达 `ToolCall`、`FileWrite`、`SendMessage` 等 intent；runtime handler 决定真实执行、记录、拒绝或模拟。Supervisor 从外部读取 immutable effect stream，便不必要求 worker 把每一步塞回自身 context；换一个 handler，还可以对同一段执行做 dry-run、审计或 counterfactual replay。

更偏工程化的入门路径，从朴素 `while true` agent loop 一步步推到 `A => F[B]` 和 middleware 判断尺，见 [AI-Applied-Algorithms：Agent Loop 是 effectful program](./AI-Applied-Algorithms.md)。

这个映射解释了 Shepherd 为什么强调“Agent execution 是 first-class object”：只有 model call、tool call、环境变化和 continuation 都能被 runtime 持有，meta-agent 才能观察、拦截、暂停、分叉或恢复另一个 Agent。

但 algebraic effects 只给出 operation / handler / continuation 的语言结构，不自动产生“Agent execution 的版本控制”。Shepherd 还需要把 Agent continuation 与环境 snapshot 耦合进 content-addressed trace，并实现 scope fork、merge、discard、checkpoint、restore 和 materialization。完整 runtime、CRO 与 Tree-RL 分析见 [AI-Applied-Algorithms：Shepherd](./AI-Applied-Algorithms.md#shepherdagent-execution-的版本控制与事务层)。

### 工程边界

Algebraic effects 只提供 effect 与 interpretation 分离的程序结构，并不自动解决真实世界状态：

- 文件系统能否回滚，还需要 snapshot / copy-on-write substrate；
- 外部消息、支付和邮件已经发出后不可逆，只能在 materialization 前 gate 或事后补偿；
- replay 需要记录 outcome、顺序、identity 和环境版本，不能只重放 operation 名称；
- 跨 session resume 还需要 durable continuation 或显式状态机；
- handler 的权限必须由 sandbox / OS 强制，不能只依赖类型和 prompt。

因此，Agent runtime 中完整的可逆执行通常是：

```text
algebraic effect interface
  + scoped handler
  + persistent trace
  + environment snapshot / COW
  + materialization and compensation boundary
```

参考：Plotkin & Power, [Algebraic Operations and Generic Effects](https://doi.org/10.1023/A:1023064908962)；Plotkin & Pretnar, [Handlers of Algebraic Effects](https://doi.org/10.1007/978-3-642-00590-9_7)。
