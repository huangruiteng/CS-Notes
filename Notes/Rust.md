# Rust

## 基础语法：结构体与反序列化

### `derive` 属性

```rust
use serde::Deserialize;

#[derive(Deserialize)]
struct TaskConfig {
    initial_items: Vec<String>,
    positive_actions: Vec<String>,
    neg_num: usize,
    start_num: usize,
    max_item_num: usize,
    seed: u64,
}
```

`#[derive(Deserialize)]` 是 Rust 的派生宏属性。它让编译器为 `TaskConfig` 自动生成 `Deserialize` trait 的实现，从而可以把 JSON、YAML、TOML 等外部配置反序列化成 Rust 结构体。

这通常需要引入 `serde`：

```rust
use serde::Deserialize;
```

以及在 `Cargo.toml` 中启用 derive：

```toml
[dependencies]
serde = { version = "1", features = ["derive"] }
```

### 名称后的 `!`：调用宏

> 来源：[Rust Book：Macros](https://doc.rust-lang.org/book/ch19-06-macros.html)、[Rust Reference：Macro invocation](https://doc.rust-lang.org/reference/macros.html)。

在名称后出现 `!`，表示调用 **macro（宏）**。宏在编译期接收 Rust token，并展开成新的 Rust 代码。

| 写法 | 含义 |
|---|---|
| `foo()` | 调用函数 |
| `foo!()` / `foo![]` / `foo!{}` | 调用宏 |
| `!condition` | 对值执行逻辑或位取反 |

常见例子：

```rust
println!("id={id}");              // 格式化并打印
let xs = vec![1, 2, 3];           // 生成 Vec 构造代码
let (a, b) = tokio::join!(fa, fb); // 生成并发 poll 多个 Future 的代码
```

函数接收预先定义好的参数类型和数量；宏可以接收可变数量、不同类型甚至更接近语法片段的输入，再生成对应代码。因此 `println!` 能处理不同格式参数，`join!` 能组合数量与类型不同的 Future。

Rust 还有不带调用 `!` 的 derive / attribute 宏：

```rust
#[derive(Deserialize)] // derive macro
#[tokio::main]         // attribute macro
```

一句话：**`!` 出现在名称后表示宏调用；它不表示异步、并发或“强制执行”。**

### `struct` 结构体

`struct` 用来定义一组具名字段：

```rust
struct TaskConfig {
    field_name: FieldType,
}
```

字段写法是：

```rust
字段名: 类型,
```

Rust 里字段末尾通常保留逗号，即使是最后一个字段也可以保留。这样后续新增字段时 diff 更干净。

### 常见字段类型

`Vec<String>` 表示动态数组，元素类型是 `String`：

```rust
initial_items: Vec<String>,
```

可以理解成：

```text
initial_items 是一个字符串列表
```

`usize` 是平台相关的无符号整数，常用于长度、下标、数量：

```rust
neg_num: usize,
start_num: usize,
max_item_num: usize,
```

`u64` 是固定 64 位无符号整数，常用于需要跨平台稳定宽度的数值，例如随机种子、ID、计数器：

```rust
seed: u64,
```

### 从 JSON 反序列化

如果外部配置长这样：

```json
{
  "initial_items": ["a", "b"],
  "positive_actions": ["click"],
  "neg_num": 10,
  "start_num": 0,
  "max_item_num": 100,
  "seed": 42
}
```

可以用 `serde_json` 读成结构体：

```rust
use serde::Deserialize;

#[derive(Deserialize)]
struct TaskConfig {
    initial_items: Vec<String>,
    positive_actions: Vec<String>,
    neg_num: usize,
    start_num: usize,
    max_item_num: usize,
    seed: u64,
}

fn main() -> Result<(), serde_json::Error> {
    let raw = r#"
    {
      "initial_items": ["a", "b"],
      "positive_actions": ["click"],
      "neg_num": 10,
      "start_num": 0,
      "max_item_num": 100,
      "seed": 42
    }
    "#;

    let config: TaskConfig = serde_json::from_str(raw)?;
    println!("{}", config.seed);
    Ok(())
}
```

这里的关键点：

- JSON key 默认要和 Rust 字段名一致。
- JSON array 可以映射到 `Vec<T>`。
- JSON number 可以映射到 `usize`、`u64` 等整数类型，但必须在目标类型范围内。
- `?` 会把错误向上传递，所以 `main` 返回 `Result`。

### 什么时候用 `String` / `&str`

结构体字段里常用 `String`，因为它拥有字符串数据，适合从外部配置中反序列化出来后长期保存：

```rust
name: String
```

`&str` 是字符串切片，通常用于临时借用已有字符串：

```rust
fn print_name(name: &str) {
    println!("{name}");
}
```

配置结构体里直接用 `&str` 会涉及生命周期标注，初学阶段优先用 `String` 更稳。

### 小结

这段结构体体现了几个 Rust 基础点：

- `#[derive(...)]`：自动生成 trait 实现。
- `Deserialize`：把外部数据转成 Rust 类型。
- `struct`：定义具名字段集合。
- `Vec<String>`：字符串列表。
- `usize`：长度、数量、下标类整数。
- `u64`：固定 64 位无符号整数，适合随机种子等需要稳定宽度的值。

## 基础语法：`Result`、`match`、enum 与 `=>`

### `Ok` / `Err`：一次调用的成功或失败

`Result<T, E>` 是 Rust 标准库里的 enum，概念上是：

```rust
enum Result<T, E> {
    Ok(T),
    Err(E),
}
```

- `Ok(value)`：成功，并携带一个 `T` 类型的值；
- `Err(error)`：失败，并携带一个 `E` 类型的错误。

例如：

```rust
fn load_count() -> Result<u32, LoadError> {
    Ok(3)
}
```

这里：

```text
T = u32
E = LoadError
Ok(3) = 成功返回整数 3
```

`Ok` 不是布尔值，也不是普通函数。它是 `Result` 的 enum variant constructor，可以粗略读成 `Result::Ok(value)`。

### `match` 与 `=>`

`match` 根据一个值匹配不同 pattern：

```rust
let label = match count {
    0 => "empty",
    1 => "one",
    _ => "many",
};
```

每一行叫一个 match arm：

```text
pattern => expression,
```

可以朗读为：

```text
如果 count 匹配 0，就得到 "empty"
如果 count 匹配 1，就得到 "one"
其他情况，就得到 "many"
```

`_` 是通配 pattern。`=>` 表示“这个 pattern 对应执行/返回右边的表达式”，不是大于等于。

`match` 本身是 expression，可以产生值；各分支必须返回兼容的类型。上面三个分支都返回 `&str`，因此整个 match 也得到 `&str`。

### enum variant：一个类型的几种形态

```rust
enum DocumentMode {
    Plain,
    Template {
        body: String,
        file_id: String,
    },
    Summary {
        body: String,
    },
}
```

这个 enum 有三种 variant：

| variant | 形态 |
|---|---|
| `DocumentMode::Plain` | unit-like，不携带字段 |
| `DocumentMode::Template { ... }` | struct-like，携带两个具名字段 |
| `DocumentMode::Summary { ... }` | struct-like，携带一个具名字段 |

`::` 表示从类型或 module 中访问关联项：

```rust
DocumentMode::Plain
Result::Ok(value)
```

### `self` 与 `Self`

在 `impl DocumentMode` 中：

- `Self` 是类型名 `DocumentMode` 的简写；
- `self` 是当前这个具体值。

```rust
impl DocumentMode {
    fn consume(self) -> Self {
        self
    }
}
```

参数写成 `self` 表示方法取得当前值的所有权。调用以后，原变量通常不能继续使用。若只想读取而不取得所有权，通常写 `&self`。

### 串起来

下面是一个完整的脱敏例子：

```rust
impl DocumentMode {
    fn render(
        self,
        renderer: &Renderer,
    ) -> Result<Self, RenderError> {
        Ok(match self {
            Self::Plain => Self::Plain,

            Self::Template {
                body,
                file_id,
            } => Self::Template {
                body: renderer.render(body)?,
                file_id,
            },

            Self::Summary {
                body,
            } => Self::Summary {
                body: renderer.render(body)?,
            },
        })
    }
}
```

可以按从外到内的顺序读：

```text
Ok(
  match self {
    pattern => new_value,
    ...
  }
)
```

| 代码 | 读法 |
|---|---|
| `self` | 方法取得当前 `DocumentMode` 的所有权 |
| `renderer: &Renderer` | 只借用 `renderer` |
| `-> Result<Self, RenderError>` | 成功返回新 `DocumentMode`，失败返回错误 |
| `match self` | 根据当前 enum variant 选择分支 |
| `Self::Plain => Self::Plain` | 匹配 `Plain`，并生成一个 `Plain` |
| `Self::Template { body, file_id }` | `=>` 左边是 pattern：拆出两个字段 |
| `Self::Template { body: ..., file_id }` | `=>` 右边是 expression：构造新 variant；`file_id` 是 `file_id: file_id` 的简写 |
| `renderer.render(body)?` | `Ok(text)` 时取出 `text`；`Err(error)` 时从当前函数提前返回 |
| `Ok(match ...)` | `match` 先生成 `Self`，`Ok` 再把它包装成 `Result` |
| 最后的 `Ok(...)` 无分号 | 它就是函数返回值；加分号会丢弃该值，使 block 得到 `()` |

同一种 `{ field }` 写法在 `=>` 两边的角色不同：

```text
pattern { field } => expression { field }
       拆值                  造值
```

整体白话：

> 取得一个 `DocumentMode`，按 variant 拆开；转换需要处理的字段，重建同一种 variant，最后用 `Ok` 表示成功返回。

### 相似符号速查

| 符号 | 含义 | 示例 |
|---|---|---|
| `=` | 绑定或赋值 | `let x = 1` |
| `==` | 判断相等 | `x == 1` |
| `>=` | 大于等于 | `x >= 1` |
| `->` | 函数返回类型 | `fn f() -> u32` |
| `=>` | match pattern 对应的分支 | `Some(x) => x` |
| `::` | 访问类型/module 的关联项 | `Result::Ok` |
| `&` | 借用 | `value: &Value` |
| `?` | 成功取值，失败提前返回 | `load()?` |
| `,` | 分隔参数、字段、match arm | `field,` |
| `;` | 结束 statement，并通常丢弃 expression 值 | `do_work();` |

最后只记住这一句：

> `Ok(match self { pattern => value, ... })`：把当前 enum 拆成不同 variant，每个分支生成一个新值，再把新值作为成功结果返回。

## 异步 Rust 源码阅读：所有权、模式匹配与错误建模

来源：脱敏整理自多段异步 Rust 服务代码，包括冷恢复故障与作业完成处理函数。原项目名、服务名、存储名、会话标识、内部路径、业务类型和接口均已删除或改为通用名称。本节只保留可复用的 Rust 知识。

公开参考：

- [Rust Book：`Result` 与 `?`](https://doc.rust-lang.org/stable/book/ch09-02-recoverable-errors-with-result.html)
- [Rust Book：Enum、`Option` 与模式匹配](https://doc.rust-lang.org/book/ch06-00-enums.html)
- [Rust Book：`if let` 与 `let ... else`](https://doc.rust-lang.org/book/ch06-03-if-let.html)
- [Rust Reference：identifier patterns 与 `@` 绑定](https://doc.rust-lang.org/reference/patterns.html#identifier-patterns)
- [Rust 标准库：`Option`](https://doc.rust-lang.org/std/option/enum.Option.html)
- [Rust Book：所有权](https://doc.rust-lang.org/book/ch04-01-what-is-ownership.html)
- [Rust Book：共享状态并发](https://doc.rust-lang.org/book/ch16-03-shared-state.html)
- [Rust 标准库：`Arc`](https://doc.rust-lang.org/std/sync/struct.Arc.html)
- [Rust Reference：Trait objects](https://doc.rust-lang.org/reference/types/trait-object.html)
- [Rust Reference：`let` statements](https://doc.rust-lang.org/reference/statements.html#let-statements)
- [Tokio：共享状态](https://tokio.rs/tokio/tutorial/shared-state)
- [Tokio：异步运行原理](https://tokio.rs/tokio/tutorial/async)

### 学习路线

1. 先读“问题模型与源码阅读”，建立 `Result` 的技术成功与业务成功边界。
2. 再读“所有权与共享状态”，理解 `&self`、clone、`Arc`、`Mutex`、`Send` 和 `Sync`。
3. 接着读“异步与错误控制流”，掌握 `.await?`、Future 内存布局、`BoxFuture`、fallback 和 fire-and-forget 的准确语义。
4. 然后读“Trait 与业务状态建模”，学习用 enum、newtype 和 trait object 收紧接口。
5. 最后读“Runtime 边界与验证”，把 Rust 类型知识放回 Actor、event replay 和测试。

### 问题模型与源码阅读

#### 技术成功不等于业务成功

先把真实系统脱敏成一个通用调用链：

```text
逻辑会话
-> SessionRegistry
-> RuntimeActor
-> EventStore
-> PrimaryArchive
-> FastCache fallback
-> Vec<Message>
-> ModelProvider
```

冷恢复时，新的 `RuntimeActor` 需要从 `EventStore` 重建消息历史。故障发生在：

```text
PrimaryArchive 返回空列表
-> FastCache 也返回空列表
-> EventStore 返回 Ok(Vec::new())
-> runtime 将空历史标记为恢复成功
-> ModelProvider 在缺失历史的情况下继续执行
```

对全新会话来说，空历史是合法状态；对已经运行过的会话来说，空历史可能表示数据丢失。`Vec::is_empty()` 无法区分这两种业务语义。

这一案例贯穿本节：

> Rust 能保证程序正确处理**已经进入类型系统**的状态，却不会自动知道某个技术成功值在业务上是否异常。

系统设计中的 event、projection 与 replay 见 [Event Sourcing：用事件日志重建系统状态](./Software-Engineering.md#event-sourcing用事件日志重建系统状态)。

#### 阅读 Rust 源码：先看函数签名

初学 Rust 时，很容易逐行陷入语法。更高效的读法是先拆函数签名：

```rust
pub async fn list_messages(
    &self,
) -> Result<Vec<Message>, StoreError>
```

这行已经给出五类信息：

| 语法 | 含义 | 阅读时追问 |
|---|---|---|
| `pub` | 其他模块可以调用 | 这是内部 helper 还是模块契约？ |
| `async fn` | 调用后产生 `Future` | 哪些地方会 `.await`？ |
| `&self` | 借用当前对象 | 函数是否会取得所有权或修改状态？ |
| `Vec<Message>` | 成功值是消息列表 | 空列表是否合法？ |
| `StoreError` | 已建模的失败类型 | 哪些业务失败没有进入这个错误类型？ |

源码阅读顺序可以固定为：

1. 参数由谁拥有：`T`、`&T`、`&mut T` 还是 `Arc<T>`。
2. 返回什么状态：普通值、`Option<T>`、`Result<T, E>` 还是业务 `enum`。
3. 哪些操作会 `.await`。
4. 锁在什么范围内被持有。
5. 哪些值发生了 move、borrow 或 clone。
6. trait 把实现边界隔离在哪里。

#### 综合例题：读懂一段 async Rust 函数

下面的代码脱敏改写自一段异步服务代码。所有业务名称、类型名、字段名和接口名均已替换，只保留通用语法结构：

```rust
pub async fn process_job_completion(
    &self,
    state: &(dyn StateSession + '_),
    history: &(dyn HistoryProvider + '_),
    audit: &(dyn AuditWriter + '_),
    notifier: &(dyn NotificationSink + '_),
    request: JobCompleted,
) -> Result<bool, ProcessError> {
    if !self.feature.is_enabled() {
        return Ok(false);
    }

    let event_id = request.event_id.clone();
    let upper_bound = request.upper_bound;
    let snapshot = state.snapshot();

    let Some(mut started) = state.begin_check(request) else {
        return Ok(false);
    };

    if let Err(error) = audit
        .append(AuditEntry::check_started(
            started.request.job_id.clone(),
            event_id,
            upper_bound,
        ))
        .await
    {
        state.restore(snapshot);
        return Err(error);
    }

    notifier.publish(started.notification.clone()).await?;

    let query = HistoryQuery {
        job_id: started.request.job_id.clone(),
        upper_bound,
    };

    match history.load(query).await {
        Ok(events) => {
            started.request.events = events;
            Ok(true)
        }
        Err(error) => {
            state.restore(snapshot);
            Err(error)
        }
    }
}
```

先把控制流压缩成白话：

```text
公开的异步方法
-> 功能未启用：正常跳过
-> 保存稍后仍要使用的字段与状态快照
-> 无法开始检查：正常跳过
-> 写审计记录失败：恢复快照并返回错误
-> 发布通知失败：由 ? 直接返回错误
-> 加载历史
   -> 成功：更新请求并返回 true
   -> 失败：恢复快照并返回错误
```

**函数签名**

| 语法 | 含义 |
|---|---|
| `pub` | 这个方法对其可见性范围外开放；具体能开放多远还受所在 module 影响 |
| `async fn` | 调用得到 Future；执行者需要 `.await` 或 poll 它 |
| `&self` | 暂时借用当前对象，不取得对象所有权 |
| `request: JobCompleted` | request 按值传入，函数取得它的所有权 |
| `-> Result<bool, ProcessError>` | 成功返回 bool，失败返回已建模错误 |

`Result<bool, E>` 中的两层语义不要混在一起：

- `Ok(true)`：调用成功，并且完成了目标动作；
- `Ok(false)`：调用成功，但功能关闭或当前不需要处理；
- `Err(error)`：调用失败。

语法上没有问题，但当 `true/false` 的含义继续增加时，业务接口更适合改成 `enum ProcessOutcome { Completed, Disabled, Skipped }`。

**`&(dyn Trait + '_)`：借用一个运行时选择的实现**

以这个参数为例：

```rust
history: &(dyn HistoryProvider + '_)
```

可以从里向外读：

1. `HistoryProvider` 是描述行为的 trait；
2. `dyn HistoryProvider` 是 trait object，具体实现到运行时才确定；
3. `&...` 表示这里只借用该实现，不取得所有权；
4. `'_` 让编译器推断 trait object 的 lifetime bound。

trait object 不知道具体类型的编译期大小，因此通常放在 `&dyn Trait`、`Box<dyn Trait>` 或 `Arc<dyn Trait>` 后面。调用时通过 vtable 动态分派。

`&(dyn Trait + '_)` 中的括号主要用于把 `dyn Trait + lifetime` 组合成一个整体；常见代码也会写成更简洁的 `&dyn Trait`，由编译器应用 lifetime elision。

这里传入的是 `&dyn Trait`，并不自动意味着底层状态绝对不可变。若 trait 方法接收 `&self`，实现仍可能通过 `Mutex`、`RwLock` 或原子类型进行 interior mutability；是否允许修改要继续看 trait 方法签名与实现。

**所有权：为什么有的字段 `.clone()`，有的直接赋值**

```rust
let event_id = request.event_id.clone();
let upper_bound = request.upper_bound;
let Some(mut started) = state.begin_check(request) else {
    return Ok(false);
};
```

`begin_check(request)` 按值接收 request，因此 request 在这里被 **move**，后面不能再访问 `request.event_id`。

- `event_id` 可能是 `String` 等非 `Copy` 类型，因此先 `.clone()` 保存一份独立值；
- `upper_bound` 可能是整数等 `Copy` 类型，赋值时自动复制，原值仍可用；
- clone 的成本由具体类型决定：复制 `String` 通常要复制堆数据，复制 `Arc<T>` 通常只增加引用计数。

看到 clone 时，应先问：**后面的哪次 move 迫使这里提前保留数据？**

**`let Some(mut started) = ... else`：匹配成功后继续 happy path**

```rust
let Some(mut started) = state.begin_check(request) else {
    return Ok(false);
};
```

右侧返回 `Option<T>`：

- 是 `Some(value)`：把内部 value 绑定为 `started`；
- 是 `None`：执行 `else` 并提前返回。

`mut started` 表示这个局部变量绑定的值之后可以修改，例如：

```rust
started.request.events = events;
```

`let ... else` 的 `else` 分支必须 **diverge**，即不能回到下一行继续执行。常见写法是 `return`、`break`、`continue` 或 `panic!`。匹配成功后，`started` 在外层作用域继续可用，这正适合保持主流程左对齐。

**`if let Err(error) = ...`：只关心一个 variant**

```rust
if let Err(error) = audit.append(entry).await {
    state.restore(snapshot);
    return Err(error);
}
```

它近似等价于：

```rust
match audit.append(entry).await {
    Ok(_) => {}
    Err(error) => {
        state.restore(snapshot);
        return Err(error);
    }
}
```

`if let` 适合只处理一个 pattern、忽略其余情况；`match` 则默认要求穷举所有分支。这里不能直接写 `.await?`，因为错误返回前还要先执行 `restore`。

示例假设 `append` 的错误类型已经是 `ProcessError`。若它返回其他错误类型，则需要显式转换，例如 `return Err(error.into());`。

**`.await` 与 `.await?`**

```rust
audit.append(entry).await
notifier.publish(notification).await?
```

- `.await`：等待 Future 产出结果；它不是创建线程；
- `.await?`：先 await，再对得到的 `Result` 使用 `?`；
- `?` 遇到 `Ok(value)` 就取出 value，遇到 `Err(error)` 就从当前函数提前返回；
- 若内层错误类型和 `ProcessError` 不同，通常还需要实现相应的 `From` 转换。

需要清理、补偿、记录日志时，不能机械地用 `?`，应像 audit 分支一样显式处理错误。

**`Type::name` 与方法链**

```rust
AuditEntry::check_started(...)
audit.append(...).await
```

- `::` 从类型或 module 路径查找关联项；`check_started` 可能是 associated function，也可能构造某个 enum variant；
- `.` 在一个值上读取字段或调用方法；
- 多行方法链仍是一个表达式，`.await` 作用于 `append(...)` 返回的整个 Future。

**结构体字面量与字段简写**

```rust
let query = HistoryQuery {
    job_id: started.request.job_id.clone(),
    upper_bound,
};
```

`job_id: expression` 是普通字段初始化。`upper_bound,` 是 field init shorthand，等价于：

```rust
upper_bound: upper_bound,
```

字段名与当前变量名相同时可以简写。末尾逗号合法，而且能让增删字段时的 diff 更干净。

**`match`、block 返回值与分号**

```rust
match history.load(query).await {
    Ok(events) => {
        started.request.events = events;
        Ok(true)
    }
    Err(error) => {
        state.restore(snapshot);
        Err(error)
    }
}
```

`match` 是 expression。这里它位于函数末尾，因此整个 match 的值就是函数返回值。

- `Ok(true)`、`Err(error)` 后没有分号：它们是各自 block 的返回值；
- 加上分号会丢弃表达式值，使 block 变成 `()`；
- 两个 match arm 必须得到兼容类型，这里都是 `Result<bool, ProcessError>`；
- `return Err(error);` 则是不等函数走到末尾，立即返回。

**容易混淆的两个 `!`**

```rust
if !enabled { /* ... */ }  // 一元逻辑非：true 变 false
println!("done");          // 名称后的 !：调用宏
```

截图中的 `!self.feature.is_enabled()` 是布尔取反，不是宏。判断方法是：`!` 在表达式前通常表示逻辑非；`name!(...)` 才是宏调用。

读类似函数时，可以按这条顺序：

```text
签名与返回类型
-> 哪些参数是借用，哪个值会被 move
-> Option / Result 的提前退出
-> 每个 await 暂停点
-> clone 的必要性与成本
-> 失败时是否需要 restore / cleanup
-> 最后一个无分号表达式返回什么
```

### 所有权与共享状态

#### `struct`：组合状态，不自动提供业务语义

```rust
use std::sync::Arc;
use tokio::sync::Mutex;

struct SessionRegistry {
    state: Mutex<RegistryState>,
    event_store: Arc<dyn EventStore + Send + Sync>,
}
```

`struct` 是一组具名字段：

- `state` 是进程内 registry 状态；
- `event_store` 是可替换的历史存储实现；
- `Mutex` 负责互斥访问；
- `Arc` 负责共享所有权；
- `dyn EventStore` 负责运行时多态。

这些类型分别解决不同问题。把它们叠在一起，也不意味着系统自动获得持久化、故障恢复或跨服务一致性。

#### 所有权、借用与 clone

**`self`、`&self`、`&mut self`**

| 写法 | 含义 |
|---|---|
| `self` | 取得对象所有权，调用后原变量通常不能再用 |
| `&self` | 只读借用，不取得所有权 |
| `&mut self` | 独占可变借用，借用期间不能再有其他借用 |

例如：

```rust
pub async fn list_messages(&self) -> Result<Vec<Message>, StoreError>
```

`&self` 表示调用者仍然拥有 store；这个方法只是暂时借用它。

**`.clone()` 可能很便宜，也可能很贵**

下面两种 clone 的成本完全不同：

```rust
let shared_store = Arc::clone(&self.event_store);
let messages = state.projection.messages.clone();
```

- `Arc::clone` 只增加引用计数，多个 `Arc` 仍指向同一份底层对象。
- `Vec<Message>::clone` 通常会复制整个列表及其元素，成本与消息数量有关。

看到 `.clone()` 时，不要统一理解成“复制数据”。先看被 clone 的具体类型。

**为什么从锁里 clone 快照**

```rust
pub async fn list_messages(&self) -> Result<Vec<Message>, StoreError> {
    self.ensure_consistent().await?;

    let messages = {
        let state = self.state.lock().await;
        state.projection.messages.clone()
    };

    Ok(messages)
}
```

这个 block 的价值是缩短锁的生命周期：

1. 获取锁；
2. clone 出不可变快照；
3. 离开 block，`MutexGuard` 被 drop，锁自动释放；
4. 后续逻辑使用快照，不再占用共享状态。

不要为了省一次 clone，把锁一直带到模型请求、网络 I/O 或其他 `.await` 之后。那会扩大临界区，降低并发能力，甚至造成死锁。

#### `Arc<T>`：共享所有权，不是共享可变性或持久化

`Arc` 是 Atomically Reference Counted，提供线程安全的引用计数。

```rust
let store_a = Arc::new(store);
let store_b = Arc::clone(&store_a);
```

`store_a` 和 `store_b` 共同拥有同一对象。当最后一个 `Arc` 被 drop，底层对象才被释放。

需要区分三个概念：

| 能力 | `Arc` 是否提供 |
|---|---|
| 多个任务共同拥有对象 | 是 |
| 自动允许修改内部数据 | 否 |
| 进程重启后恢复对象 | 否 |

共享可变状态通常需要 `Arc<Mutex<T>>`、`Arc<RwLock<T>>`，或者把状态交给专门的 Actor，通过 channel 发送命令。

`Arc<T>` 只有在 `T` 满足相应约束时才是 `Send` / `Sync`。它不会把一个本来不支持跨线程使用的类型“包装成线程安全”。

#### `Send` 与 `Sync`

- `Send`：值的所有权可以安全地移动到另一个线程。
- `Sync`：多个线程可以安全地共享 `&T`。

常见 trait object 会写成：

```rust
Arc<dyn EventStore + Send + Sync>
```

意思是：

- `EventStore` 的具体实现运行时才确定；
- 该实现可以跨线程移动；
- 该实现的共享引用可以被多个线程使用。

Tokio 多线程 runtime 中，`tokio::spawn` 的 Future 通常需要 `Send`，因为任务可能在一次 `.await` 之后被调度到另一个 worker thread。

#### `Mutex<T>`：锁保护的是临界区

`Mutex` 提供互斥访问：同一时刻只有一个执行者能拿到内部数据。

```rust
let state = self.state.lock().await;
```

如果这里使用 `tokio::sync::Mutex`，`.lock().await` 会在锁不可用时让当前 task 暂停，把执行权还给 runtime。

但“异步代码”不意味着必须使用异步 Mutex。Tokio 的建议是：

- 临界区很短，且不会跨 `.await`：可以考虑 `std::sync::Mutex`；
- 必须持锁跨异步 I/O：才可能需要 `tokio::sync::Mutex`；
- 对需要异步操作的复杂资源，专用 Actor + channel 往往比大锁更清晰。

核心检查项：

```text
拿锁以后，直到 guard 被 drop 之间，是否出现了 .await？
```

Rust 可以防止很多不安全内存访问，但不能自动消灭锁顺序错误、活锁、饥饿或所有死锁。

#### `Cell<T>`：单任务内部可变性

`Cell<T>` 提供 interior mutability：即使只有共享引用，也可以读取或替换内部值。

```rust
use std::cell::Cell;

struct RequestBudget {
    remaining: Cell<usize>,
}

impl RequestBudget {
    fn consume(&self) -> bool {
        let remaining = self.remaining.get();
        if remaining == 0 {
            return false;
        }
        self.remaining.set(remaining - 1);
        true
    }
}
```

这里 `consume` 只拿到 `&self`，仍能修改计数。`Cell` 适合 `usize`、`bool` 等小型 `Copy` 值，以及能保证状态只由一个线程或一个逻辑 task 独占访问的场景。

它不是轻量版 `Mutex`：`Cell` 不是 `Sync`，不能直接让多个线程并发共享；也不能像普通引用一样借出内部字段。需要跨 task / 线程共享时，通常使用 `Mutex`、原子类型或 Actor。

#### `Box<T>`：缩小大型 enum 的外层尺寸

Rust 的 enum 通常要能在原地容纳最大的 variant，再加上用于区分 variant 的 discriminant：

```rust
struct ActiveRuntime {
    buffers: [u8; 4096],
}

enum RuntimeMode {
    Disabled,
    Active(Box<ActiveRuntime>),
}
```

若直接写成 `Active(ActiveRuntime)`，每个 `RuntimeMode` 都要按大型 variant 预留空间，即使当前值是 `Disabled`。改成 `Box<ActiveRuntime>` 后，`Active` payload 只在 enum 内保存固定大小的 heap pointer，不再内嵌整个大对象；大对象在真正构造 `Active` 时才分配。

这也是 Clippy `large_enum_variant` 常见修法。代价是一次 heap allocation 和一次指针间接访问；适合尺寸差异悬殊、创建频率低或生命周期长的 variant，不要为了“看到大 struct”就在高频路径机械装箱。

### 异步与错误控制流

#### `async` / `.await`：Future、暂停点与执行顺序

`async fn` 调用后返回 Future。Future 需要被 `.await` 或由 executor poll，里面的异步工作才会推进。

```rust
let events = store.load(session_id).await?;
```

`.await?` 解析为 `(store.load(session_id).await)?`，类型变化是：

```text
Future<Output = Result<T, E>>
  -- .await --> Result<T, E>
  -- ? ------> T，或遇到 Err(E) 时从当前函数提前返回
```

可以按顺序读成：

1. 调用 `load`，得到 Future；
2. `.await` 等待 Future 完成，等待期间当前 task 可以让出执行权；
3. 得到 `Result<Vec<Event>, StoreError>`；
4. `?` 在 `Err` 时提前返回，在 `Ok` 时取出列表。

`.await` 不是创建新线程，也不等于自动并行。下面两次调用仍然是串行的：

```rust
let a = load_a().await?;
let b = load_b().await?;
```

如果两者相互独立，才可能用 `tokio::join!` 等方式并发等待；名称后的 `!` 表示它是宏调用。

#### `Box::pin` / `BoxFuture`：给大型 async 状态机建立固定边界

**`async fn` 会编译成具体 Future 状态机**

下面的 dispatcher 看起来只是一个 `match`：

```rust
async fn handle(
    &self,
    command: Command,
) -> Result<EventBatch, DispatchError> {
    match command {
        Command::Create(command) => {
            self.create(*command).await
        }
        Command::Update(command) => {
            self.lookup(&command.id)
                .await?
                .refresh(command)
                .await
        }
        Command::Execute(command) => {
            self.execute(command).await
        }
    }
}
```

编译器会将它转换成一个匿名状态机，概念上近似：

```rust
enum HandleFuture {
    Start,
    Creating(CreateFuture),
    Updating {
        lookup: LookupFuture,
        command: UpdateCommand,
    },
    Refreshing(RefreshFuture),
    Executing(ExecuteFuture),
    Done,
}
```

Future 需要保存：

- 当前执行到哪个 suspension point；
- 跨 `.await` 仍然存活的局部变量；
- 当前正在等待的子 Future；
- `match` 当前进入了哪个分支。

状态机的尺寸通常接近**最大状态/分支的尺寸，加上 discriminant 与 alignment**，不是所有分支简单相加。但只要某个分支包含很大的子 Future、跨 `.await` 的大对象或很深的 async 调用组合，整个 dispatcher Future 都可能变大。

这和递归导致的“调用栈越来越深”不同：

```text
递归栈溢出：
  同一个调用不断增加 stack frame

大型 Future：
  单个编译期状态机本身很大
  + 构造、移动、poll 时仍可能使用线程栈
  + 外层 async 状态机还可能继续内嵌它
```

async 不等于“不使用栈”。Future 最终可能存放在 task allocation 或其他 heap 对象中，但创建它、把它交给 runtime、poll 它以及执行 poll 内部的同步代码仍会使用线程栈。精确 placement 会受编译器优化和 runtime 实现影响，不能只靠源码形状下绝对结论。

**分支级装箱**

可以把异构分支在 dispatcher 边界统一成 `BoxFuture`：

```rust
use futures::future::BoxFuture;

type DispatchFuture<'a> =
    BoxFuture<'a, Result<EventBatch, DispatchError>>;

fn dispatch(
    &self,
    command: Command,
) -> DispatchFuture<'_> {
    match command {
        Command::Create(command) => {
            Box::pin(self.create(*command))
        }
        Command::Update(command) => {
            Box::pin(async move {
                self.lookup(&command.id)
                    .await?
                    .refresh(command)
                    .await
            })
        }
        Command::Execute(command) => {
            Box::pin(self.execute(command))
        }
    }
}

async fn handle(
    &self,
    command: Command,
) -> Result<EventBatch, DispatchError> {
    self.dispatch(command).await
}
```

同步的 `dispatch` 先选择分支，每个分支立即返回同一种固定大小的 boxed handle。外层 `handle` 只需保存一个 `BoxFuture`，不再把所有 command 的具体 Future 状态合进自己的匿名类型。

关键不是“代码里出现了 Box”，而是：

> **type erasure / heap indirection 边界是否早于那个巨型组合状态机。**

如果先构造完整的巨大 dispatcher Future，再在更外层装箱，调用者拿到的确实是固定大小指针，但 dispatcher 自身的具体状态、heap allocation 大小以及构造过程仍然存在。分支级装箱直接阻止多个大型分支继续合并成同一个内联状态机。

**逐层读懂 `BoxFuture`**

`futures::future::BoxFuture<'a, T>` 大致等价于：

```rust
use std::future::Future;
use std::pin::Pin;

type BoxFuture<'a, T> =
    Pin<Box<dyn Future<Output = T> + Send + 'a>>;
```

| 组成 | 解决的问题 |
|---|---|
| `Future<Output = T>` | 描述异步计算完成后产出什么 |
| `dyn Future` | 擦除具体 Future 类型，让不同分支返回同一种接口 |
| `Box<...>` | 把具体状态放到 heap；外层持有固定大小的指针 |
| `Pin<...>` | poll 开始后保持 Future 内部地址稳定 |
| `Send` | 允许 Future 随 task 在线程之间移动 |
| `'a` | Future 可以借用外部对象，但不能活得比这些借用更久 |

`Box` 与 `dyn` 不完全是一回事：

```text
Box<F>
  -> F 放在 heap
  -> F 的具体类型仍然保留

Box<dyn Future<...>>
  -> Future 放在 heap
  -> 具体类型同时被擦除，通过 vtable 动态分发 poll
```

`Box::pin(value)` 可以理解为“在 heap 上放置 value，并得到 `Pin<Box<T>>`”。普通 `Box::new(value)` 只负责 heap allocation，不自动提供 pinned API。

**为什么 Future 需要 `Pin`**

`Future::poll` 的接收者形态是：

```rust
fn poll(
    self: Pin<&mut Self>,
    context: &mut Context<'_>,
) -> Poll<Self::Output>;
```

编译器生成的 async 状态机可能包含跨 `.await` 的内部引用，因此一旦开始 poll，随意移动内部对象可能让引用失效。`Pin` 保证的是 **被 pin 的 Future 本体不再随意换地址**：

- `Pin<Box<F>>` 中的 Box 指针变量仍可以移动；
- heap 上的 `F` 保持稳定地址；
- `Pin` 不表示 Future 不能 drop，也不表示 task 不能取消。

**`Send` 与 `'a`**

```rust
fn dispatch(&self, command: Command) -> BoxFuture<'_, Result<...>>
```

- `'_` 通常由编译器从 `&self` 推断：返回的 Future 借用了当前 dispatcher；
- 调用者不能让这个 Future 活得比 dispatcher 更久；
- `Send` 要求所有跨 `.await` 保留下来的捕获值都满足相应线程安全条件；
- 如果 Future 只能在单线程 executor 上运行，可以使用不要求 `Send` 的 `LocalBoxFuture`。

看到“future cannot be sent between threads safely”时，重点检查跨 `.await` 的 `Rc`、`RefCell`、非 `Send` guard 或 trait object；问题不一定出在 `.await` 本身。

**`async move` 解决捕获值所有权**

```rust
Box::pin(async move {
    self.lookup(&command.id).await?.refresh(command).await
})
```

`move` 会把捕获的 `command` 所有权移入 Future，使它能跨多个 `.await` 保存。若捕获的是 `&self`，被 move 的只是这份引用，Future 的可存活时间仍受 `'a` 限制。

`async move` 不表示创建线程，也不表示自动移到 heap；heap allocation 来自外面的 `Box::pin`。

再看一个 detached task：

```rust
let task = async move {
    context.run(route(stream)).await;
    release(guard).await;
};

tokio::spawn(task);
```

这里发生了三层不同的 move：

```text
构造 async move block
  -> context / stream / guard 从外层局部变量移入 Future

调用 tokio::spawn(task)
  -> Future 自身移入 Tokio scheduler

Future 被 poll
  -> stream 按值传给 route
  -> guard 按值传给 release
```

可以把编译器生成的 Future 粗略想成一个匿名 struct：

```rust
struct SpawnedFuture {
    context: RequestContext,
    stream: EventStream,
    guard: Option<SessionGuard>,
    state: FutureState,
}
```

这不是实际展开代码，但能解释所有权：`async move` 创建 Future 时，非 `Copy` 的 `stream` 和 `guard` 已经成为这个 Future 的字段，因此外层不能再使用它们。

```rust
let task = async move {
    route(stream).await;
    release(guard).await;
};

// use_stream(stream); // 编译错误：stream 已被 move
tokio::spawn(task);
```

之所以常和 `tokio::spawn` 搭配，是因为普通 spawn 的约束近似为：

```rust
fn spawn<F>(future: F) -> JoinHandle<F::Output>
where
    F: Future + Send + 'static,
    F::Output: Send + 'static;
```

spawn 出的 task 可能比当前函数活得更久。若 Future 只借用当前栈上的 `stream` 或 `guard`，当前函数返回后引用就可能悬空；把值的所有权交给 Future 后，Future 活多久，这些值就活多久。

这里的 `'static` 不是“task 永远不释放”，而是 Future 内不能保存会提前失效的非 `'static` 借用。把一个 `&self` move 进去，移动的仍只是一份引用；若 `self` 不是 `'static`，照样可能无法 spawn。常见做法是先 clone 一个 `Arc<Self>`：

```rust
let runtime = Arc::clone(&runtime);
tokio::spawn(async move {
    runtime.run().await;
});
```

`async move` 对不同值的效果也不同：

| 外层值 | 捕获结果 |
|---|---|
| `String`、stream、lock guard | 非 `Copy`，所有权移入 Future |
| `u64`、`bool` 等 `Copy` 类型 | 复制一份值进入 Future |
| `Arc<T>` | Arc handle 被 move；想保留外层 handle，先 `Arc::clone` |
| `&T` | 引用本身被 move，底层 `T` 没有被 move；lifetime 约束仍存在 |

为什么 guard 必须跨第一个 `.await` 保存？因为它在 `route(stream).await` 完成后才会交给 `release`。编译器因此必须把 guard 留在 Future 状态机里跨越这个 suspension point。stream 则在开始执行 `route(stream)` 时进入 route Future；等待 route 完成期间，该子 Future 也由外层状态机保存。

最后还要区分 **move 与 cleanup**：move 只明确“谁拥有 guard”，不保证异步释放一定执行完。task 被 abort 时，Future 及尚未消费的字段会被 drop；但 `Drop` 不能 `.await`。重要锁通常仍需 Drop 兜底、lease timeout、作用域化 task 或显式 cancellation cleanup。

一句话：**`async move` 把任务运行所需的行李装进 Future，`spawn` 再把整件行李交给 runtime；其中非 `Copy` 值的原所有者随之失去使用权。**

**`?` 返回的是哪一层**

`?` 总是从它所在的最近函数、closure 或 async block 提前返回。

```rust
Box::pin(async move {
    let target = self.lookup(&command.id).await?;
    target.refresh(command).await
})
```

这里 `lookup` 失败时：

```text
boxed async block
-> 完成为 Err(error)
-> 外层 await 得到 Err(error)
-> 外层仍有机会记录 status、metrics 或执行统一清理
```

如果同一个 `?` 原本直接位于外层 `async fn`，它可能在外层状态更新前就提前返回。最终 `Result` 可以完全相同，但外围 observability 可能从“提前 drop”变成明确的 `"error"`。

因此机械搬移 `?` 时，除了比较返回值，还要检查：

- metrics / tracing guard；
- cleanup / restore；
- retry / fallback；
- cancellation 与 Drop 行为。

**取消语义**

外层丢弃 `BoxFuture` 时，Box 中的具体 Future 也会被 drop。分支级装箱本身通常不会把任务变成 detached task，也不会改变为 fire-and-forget。

但是“drop 即取消”只保证 Rust 对象被析构，不保证外部副作用回滚。Future 在取消前可能已经写数据库、发请求或投递消息；这些操作仍要靠事务、幂等键、receipt 或补偿机制处理。

**代价与选择**

| 方案 | 优点 | 代价/边界 |
|---|---|---|
| 直接内联 async `match` | 无额外 allocation，便于静态优化 | 分支多且 Future 大时，组合状态机可能膨胀 |
| 分支级 `BoxFuture` | 固定 dispatch 边界，类型统一，减小外层 Future | 每次一次 heap allocation + vtable dispatch |
| 自定义 enum / `Either` | 避免 heap allocation | 分支类型和状态仍显式进入 enum，代码复杂度上升 |
| 拆成多个独立 handler | 缩小每个函数职责与 Future | 仍要在最终 dispatch 边界统一类型 |
| 增大线程栈 | 可做诊断或临时缓解 | 容易掩盖 Future 形状问题，不是稳定修复 |

对于本来就会访问存储、网络、Actor 或工具的 command，一次 allocation 和动态分发通常远小于业务 I/O 成本。高频、低延迟、纯内存热路径则应先测量再决定。

**验证大型 Future 修复**

不要只验证“正常功能还能跑”。更有诊断性的检查是：

1. 在接近生产默认的较小 worker stack 下运行完整路径；
2. 保留 negative control，证明修改前能稳定复现、修改后消失；
3. 使用 `std::mem::size_of_val(&future)` 辅助比较 Future 尺寸，但不要把编译器相关的精确字节数当长期 API；
4. 覆盖每个 dispatch 分支的成功与错误传播；
5. 检查取消、Drop guard 和 metrics label 是否发生变化；
6. 确认问题与输入数据量无关，避免把代码形状问题误判成“大请求”。

一句话：

> `Box::pin` 把 Future 放到稳定的 heap 地址；`dyn Future` 统一异构分支；`BoxFuture` 把两者连同 `Send` 和 lifetime 组合成固定的 async dispatch 边界。

#### Tokio：Rust 异步程序的 runtime

> 来源：[Tokio Tutorial](https://tokio.rs/tokio/tutorial)、[Spawning](https://tokio.rs/tokio/tutorial/spawning)、[`select!`](https://tokio.rs/tokio/tutorial/select)、[`spawn_blocking`](https://docs.rs/tokio/latest/tokio/task/fn.spawn_blocking.html)。

Rust 标准库定义了 `Future` 和 `.await` 的协议，但没有提供完整的异步执行器。**Tokio 是第三方异步 runtime**，主要面向高并发 I/O 程序，负责：

- 调度并反复 poll Future；
- 在 socket、timer 等资源就绪时唤醒 task；
- 提供异步网络、时间、channel、锁和进程 API；
- 管理 task、runtime thread 与 blocking thread pool。

```text
async fn                编译成 Future 状态机
Future                  描述“怎样继续”，自身不会主动运行
Tokio task              被 runtime 调度的 Future
Tokio runtime           executor/scheduler + I/O driver + timer
OS thread               runtime 用来实际执行 task 的线程资源
```

`#[tokio::main]` 可以粗略理解为：创建 Tokio runtime，再用它 `block_on(main())`。它不是 Rust `main` 函数天然支持 `.await`。

| API | 心智模型 | 是否创建独立 task |
|---|---|---|
| `future.await` | 当前 task 等一个 Future；等待时让出执行权 | 否 |
| `tokio::join!(a, b)` | 在当前 task 内交替 poll，等全部完成 | 否 |
| `tokio::select!` | 在当前 task 内等待多个分支，先完成者胜出，其余 Future 通常被丢弃 | 否 |
| `tokio::spawn(future)` | 把 Future 交给 scheduler 独立推进，返回 `JoinHandle` | 是 |
| `tokio::task::spawn_blocking(f)` | 把阻塞函数放进专用 blocking thread pool | 是，但不是普通 async task |

`spawn` 不等于创建 OS 线程。Tokio task 类似轻量级 green thread，可能在同一线程并发运行，也可能被多线程 runtime 移到其他 worker thread。`spawn` 后即使不 `.await JoinHandle`，task 仍会运行；丢弃 handle 只是失去结果、panic 和取消状态的观察入口。

```rust
#[tokio::main]
async fn main() -> anyhow::Result<()> {
    let a = tokio::spawn(load_a());
    let b = load_b().await?;
    let a = a.await??; // 第一层 Result 是 task join，第二层是 load_a
    use_both(a, b);
    Ok(())
}
```

两个常见边界：

- `join!` / `select!` 提供并发，不保证多核并行；分支仍在当前 task 上被轮流 poll。
- async task 中执行阻塞 I/O 或长时间 CPU 计算，会占住 runtime worker，拖慢其他 task。短期阻塞工作用 `spawn_blocking`；大量 CPU 计算通常交给 Rayon 或专用线程池。

一句话：**Rust 提供 Future 语言协议，Tokio 提供让 Future 持续向前运行的执行系统。**

**Task-local：给一次异步调用链附加隐式上下文**

`tokio::task_local!` 类似异步世界的 thread-local，但状态跟随 Tokio task，而不是绑定某条 OS 线程：

```rust
tokio::task_local! {
    static REQUEST_BUDGET: RequestBudget;
}

async fn run_with_budget(limit: usize) {
    let state = RequestBudget {
        remaining: Cell::new(limit),
    };

    REQUEST_BUDGET.scope(state, run_work()).await;
}
```

这里的 `static REQUEST_BUDGET` 定义的是一个全局可见的访问键，不是一份全进程共享的 `RequestBudget`；每次 `.scope(...)` 才为当前 task 安装具体值。

- `.scope(state, future)` 只在该 Future 执行期间安装状态，结束后自动移除；
- 嵌套 scope 会暂时遮蔽外层值，结束后恢复外层状态；
- task-local 不会因为 task 被调度到另一条 worker thread 就失效；
- 新 `tokio::spawn` 出来的独立 task 不会自动继承当前 task-local。

它适合 trace context、deadline、单次请求预算等横切状态，可以避免把参数穿过整条函数链。代价是依赖隐式上下文：若缺少 scope 会影响正确性，应显式报错或提供清楚的默认语义，不能悄悄绕过约束。

**同步 admission，异步 completion**

异步 HTTP 服务不必在“全程同步等待”和“立即 spawn 后返回成功”之间二选一。更实用的边界是：**在请求内同步确认权威状态机是否接纳命令，接纳后的事件流再交给后台 task 推进。**

```rust
async fn dispatch(
    runtime: &Runtime,
    command: Command,
    guard: Option<SessionGuard>,
) -> Result<Accepted, PublicError> {
    let stream = match runtime.admit(command).await {
        Ok(stream) => stream,
        Err(RuntimeError::Rejected(message)) => {
            release(guard).await;
            return Err(PublicError::bad_request(message));
        }
        Err(error) => {
            release(guard).await;
            return Err(PublicError::internal(error.to_string()));
        }
    };

    let context = RequestContext::capture();
    tokio::spawn(async move {
        context.run(route(stream)).await;
        release(guard).await;
    });

    Ok(Accepted)
}
```

这里的 HTTP 成功承诺的是：

```text
命令已经通过 actor / state machine 的同步校验并被接纳
```

它不承诺整个事件流已经消费完，也不承诺所有下游观察者都已处理。这个边界适合“校验与内存状态变更很短，但事件持久化、广播或 SSE 推送可能较长”的命令。

`tokio::spawn` 通常要求被提交的 Future 满足 `Send + 'static`。`async move` 会把 `stream`、`guard` 和 context snapshot 的所有权移入新 task：

- 外层返回后，这些值仍由后台 task 持有；
- `guard` 被 move 后，外层不能再次释放它，所有权系统避免 double release；
- guard 的生命周期被自然延长到事件流处理结束；
- task-local 不会自动跨 `spawn`，需要显式 capture / restore。

设计时仍要问：锁是否真的应覆盖整个后台阶段。若锁只保护 admission，就应尽早释放；若同一 session 的 projection 必须在下一条命令前完成，才应把 guard 一起移入 task，持有到 canonical event 路由结束。错误路径也必须显式释放，不能只写成功路径。

一句话：**同步等待到“可以诚实回复成功”的最小权威边界，再把其余工作异步化。**

#### 没有 `.await`，不自动等于 fire-and-forget

**Fire-and-forget 描述的是结果所有权**：调用方发起工作后，不等待最终完成，也不接收成功、失败或返回值。它不等于“没有 `.await`”，也不等于并发。

| 形态 | 实际语义 |
|---|---|
| 调用 `async fn` 但不 `.await` | Future 被创建后丢弃，函数体通常根本没有执行 |
| 调用同步函数但忽略 `Result` | 工作已经执行，只是失败被忽略 |
| `tokio::spawn(...)` 后丢弃 `JoinHandle` | detached task，最接近 fire-and-forget；结果、panic 和中断通常无人观察 |
| `send(...).await` 后立即返回 | 可能只确认“已入队”，不确认消费者已经处理 |

判断时不要只找 `.await`，而要问：**调用方究竟确认到了哪一层——任务已启动、已入队、已持久化、已送达，还是已处理？**

例如 `append(...).await?; publish(...); Ok(seq)` 至少确认主存储成功；是否确认旁路投递，要看 `publish` 是未被 poll 的 Future、同步发送、内部 spawn，还是会等待远端 ACK。

#### `Result<T, E>`：只传播已经建模的错误

`Result` 是 enum：

```rust
enum Result<T, E> {
    Ok(T),
    Err(E),
}
```

例如：

```rust
Result<Vec<Message>, StoreError>
```

表达的是：

- `Ok(messages)`：成功拿到一个列表；
- `Err(error)`：发生了已建模的存储错误。

但 `Ok(vec![])` 仍属于 `Ok`。Rust 不会自动把空列表解释成异常。

**`?` 的展开**

```rust
let events = archive.fetch(session_id).await?;
```

可以近似理解为：

```rust
let events = match archive.fetch(session_id).await {
    Ok(events) => events,
    Err(error) => return Err(StoreError::from(error)),
};
```

`?` 有两个效果：

1. `Ok(value)`：取出 `value`，继续执行；
2. `Err(error)`：提前返回，并通过 `From` / `Into` 转成当前函数的错误类型。

它不会记录日志、重试或 fallback。是否做这些动作，仍由业务控制流决定。

**空结果 fallback 的真值表**

```rust
let archived = archive.fetch(session_id).await?;

if !archived.is_empty() {
    return Ok(archived);
}

cache.load(session_id).await
```

| Archive 结果 | 行为 |
|---|---|
| `Err(error)` | `?` 立即向上返回，不执行 fallback |
| `Ok(non_empty)` | 直接返回归档结果 |
| `Ok(empty)` | 执行 cache fallback |
| Archive `Ok(empty)` + Cache `Ok(empty)` | 整体返回 `Ok(empty)` |

这说明“请求失败”和“请求成功但没有数据”是两条完全不同的控制流。

**恢复失败时，返回哪一个错误是一项 API 契约**

```rust
match recover().await {
    Ok(value) => Ok(value),
    Err(recovery_error) => {
        tracing::warn!(?recovery_error, "recovery failed");
        Err(original_error)
    }
}
```

这段代码记录了恢复错误，却向调用方返回原始错误。它可能是刻意兼容旧契约，也可能遮蔽了更直接的失败原因。Rust 只保证返回类型正确，不会替系统判断哪个错误更重要。

设计恢复、fallback 或多层错误转换时，要明确：调用方看到哪个 canonical error code，次要原因是否进入 `source` / error chain，日志与对外错误是否保持一致。

**`binding @ pattern`：匹配 variant，同时保留整个值**

```rust
fn to_public_error(error: RuntimeError) -> PublicError {
    match error {
        rejected @ RuntimeError::InvalidRequest { .. } => {
            PublicError::bad_request(rejected.to_string())
        }
        other => PublicError::internal(other.to_string()),
    }
}
```

`rejected @ RuntimeError::InvalidRequest { .. }` 同时做两件事：

1. 确认值属于 `InvalidRequest` variant；
2. 把完整的 `RuntimeError` 值绑定为 `rejected`，右侧仍可调用其方法或整体传走。

若只需要判断而不使用整个值，可以写 `RuntimeError::InvalidRequest { .. }`；若要拆字段，可以写 `error @ RuntimeError::InvalidRequest { code, .. }`。这种写法适合在模块边界做 typed error projection，例如把请求拒绝映射为 4xx，把内部持久化或执行失败映射为 5xx。

#### `Option<T>`：表达缺失，不表达缺失原因

`Option` 也是 enum：

```rust
enum Option<T> {
    Some(T),
    None,
}
```

例如：

```rust
Option<ThreadId>
```

只能表达：

- `Some(thread_id)`：有 thread ID；
- `None`：没有 thread ID。

它不能表达：

- 这是一个尚未分配 thread 的新会话；
- thread 数据丢失；
- thread 正在迁移；
- thread 被主动释放。

当“为什么没有值”会改变业务行为时，应该定义更具体的 enum。

**同时匹配多个 `Option`：把覆盖规则写成真值表**

当两个可选输入共同决定结果时，直接匹配 tuple 往往比连续 `map` / `or_else` 更清楚：

```rust
fn resolve_scope(
    configured: Option<Scope>,
    requested_path: Option<&String>,
) -> Option<Scope> {
    match (configured, requested_path) {
        (Some(mut scope), Some(path)) => {
            scope.current = Some(path.clone());
            Some(scope)
        }
        (Some(scope), None) => Some(scope),
        (None, Some(path)) => Some(Scope::single(path.clone())),
        (None, None) => None,
    }
}
```

四个 match arm 就是一张完整真值表，编译器会检查四种组合是否穷举。这里的所有权细节是：

- `configured` 按值进入 tuple，`Some(mut scope)` 取出并拥有 `scope`，因此可以修改再返回；
- `requested_path: Option<&String>` 只借用请求字段；常见来源是 `request.path.as_ref()`；
- `path.clone()` 把 `&String` 指向的字符串复制成新的 `String`；
- 若用 `request.path.map(...)`，会消费该 `Option<String>`，后面不能再整体借用相应字段。

连续的 `requested.map(...).or_else(|| configured)` 表达的是“请求值优先，配置只兜底”。如果真正语义是“配置定义稳定边界，请求只覆盖其中一个字段”，这种链式写法虽然类型正确，却会把业务合并规则写错。

**`Option::take()`：移出旧值，并在原位留下 `None`**

[`Option::take`](https://doc.rust-lang.org/std/option/enum.Option.html#method.take) 接收 `&mut Option<T>`，返回原来的 `Option<T>`，同时把原位置改成 `None`：

```rust
struct RuntimeState {
    active_job: Option<Job>,
}

fn finish_job(state: &mut RuntimeState) -> Option<Job> {
    state.active_job.take()
}
```

```text
调用前：active_job = Some(job)
返回值：Some(job)
调用后：active_job = None
```

它近似等价于：

```rust
std::mem::replace(&mut state.active_job, None)
```

当只有 `&mut self` 时，不能直接把非 `Copy` 字段移出去，因为那会让被借用的 struct 留下未初始化洞；`take()` 用合法的 `None` 当占位值，因此可以安全转移所有权，也不需要 clone。

常见用途是一次性消费状态：

```rust
if let Some(sender) = self.pending_sender.take() {
    let _ = sender.send(result); // sender 最多被消费一次
}
```

| 写法 | 效果 |
|---|---|
| `option.as_ref()` | 借用内部值，原处不变 |
| `option.clone()` | 复制一份，原处不变，要求 `T: Clone` |
| `option.take()` | 移出内部值，原处变成 `None` |
| `option.replace(new)` | 移出旧值，原处变成 `Some(new)` |

注意：`take()` 后若后续操作失败，原字段也已经是 `None`；需要事务语义时，要么先完成所有可能失败的校验，要么在失败分支把值放回去。它本身也不提供并发原子性；共享状态仍需 Actor 独占、`Mutex` 或其他同步边界。

**`Option<NonZeroUsize>`：让配置中的非法状态无法表达**

```rust
use std::num::NonZeroUsize;

struct RetryPolicy {
    max_attempts: Option<NonZeroUsize>,
}
```

这可以定义成：

- `None`：不设上限；
- `Some(n)`：上限是一个严格大于 0 的整数；
- `0`：不能成为 `NonZeroUsize`。`NonZeroUsize::new(0)` 会返回 `None`，反序列化为该类型时通常直接报配置错误。

相比用裸 `usize` 再约定“0 表示关闭还是无限”，这种组合把歧义移出 runtime。原则是：能用标准类型表达的不变量，不要只写在注释和 `if` 中。

`NonZeroU32`、`NonZeroUsize` 还把 `0` 留作 niche，`Option<NonZeroU32>` 因而不需要额外保存一个 `Some / None` discriminant。这个布局优化是额外收益，首要价值仍是让非法状态无法表达。

`Option<NonZeroUsize>` 也适合表达“尚未进入某类重试 / 已进入第 n 次重试”：

```rust
let mut retry_index: Option<NonZeroUsize> = None;
retry_index = Some(NonZeroUsize::MIN); // 第一次针对性重试，值为 1
```

这里 `None` 与 `Some(1)` 是不同业务状态，没必要再约定 `0` 是特殊哨兵。递增计数时仍应使用 `checked_add` 或 `saturating_add`，明确溢出策略。

**`Option<Result<T, E>>::transpose()`：可选动作也可能失败**

```rust
let rendered: Result<Option<String>, RenderError> = retry_index
    .map(|index| render_retry_guidance(index)) // Option<Result<String, E>>
    .transpose();                              // Result<Option<String>, E>

let rendered = rendered?;
```

[`transpose()`](https://doc.rust-lang.org/std/option/enum.Option.html#method.transpose) 的三种结果是：`None -> Ok(None)`、`Some(Ok(v)) -> Ok(Some(v))`、`Some(Err(e)) -> Err(e)`。它适合“某个分支可以不执行；一旦执行，仍可能失败”的控制流，避免手写嵌套 `match`。

几个经常一起出现的借用技巧：

```rust
if matches!(&error, Error::OutputTruncated { .. }) {
    // 借用 error 做分类；后面仍可记录或返回 error
}

let prompt: &str = rendered.as_deref().unwrap_or(base_prompt);
```

- [`matches!(&value, Pattern)`](https://doc.rust-lang.org/std/macro.matches.html) 用引用做模式判断，不移动非 `Copy` 的错误值。
- [`Option<String>::as_deref()`](https://doc.rust-lang.org/std/option/enum.Option.html#method.as_deref) 把 `Option<String>` 临时借成 `Option<&str>`，可与已有 `&str` 共享同一 fallback 类型，不必 clone。
- [`include_str!`](https://doc.rust-lang.org/std/macro.include_str.html) 可以在编译期把 prompt / schema 模板嵌入二进制：缺文件会编译失败，部署时无需再携带外部模板；代价是模板变更必须重新编译，并应同步推进可观测的 prompt version。

### Trait 与业务状态建模

#### 用 enum 让业务状态显式化

空 `Vec<Event>` 同时表示“新会话”和“恢复失败”，说明返回类型太窄。

可以把结果改成：

```rust
enum RestoreSource {
    PrimaryArchive,
    FastCache,
}

enum HistoryLoadOutcome {
    FreshSession,
    Restored {
        source: RestoreSource,
        events: Vec<StoredEvent>,
    },
    MissingOnResume {
        archive_count: usize,
        cache_count: usize,
    },
}
```

函数签名变成：

```rust
async fn load_history(
    &self,
    intent: SessionIntent,
) -> Result<HistoryLoadOutcome, StoreError>
```

创建与恢复意图也不必用模糊 bool：

```rust
enum SessionIntent {
    Create,
    Resume,
}
```

调用方必须显式处理每种状态：

```rust
match outcome {
    HistoryLoadOutcome::FreshSession => start_fresh(),
    HistoryLoadOutcome::Restored { events, .. } => replay(events)?,
    HistoryLoadOutcome::MissingOnResume { .. } => {
        return Err(ResumeError::HistoryMissing);
    }
}
```

`match` 默认要求穷举所有 variant。以后增加 `PartiallyRestored` 时，遗漏处理的位置会在编译期暴露。若滥用 `_` 通配分支，则会削弱这种保护：

```rust
match error {
    ServiceError::Unavailable => PublicError::unavailable(),
    _ => PublicError::internal(),
}
```

加入新的 `ServiceError::BudgetExhausted` 后，这段代码仍能编译，但新错误会被静默降级成 `internal`。在错误码、状态机和协议转换等边界，优先显式列出 variant；只有“未来任何新值都确实应采用同一语义”时才使用 `_`。

#### newtype：避免混用外观相同的 ID

多个 ID 都可能存成 `String`，但语义不同：

```rust
struct SessionId(String);
struct ThreadId(String);
struct ActorId(String);
```

这叫 newtype pattern。它让下面的误用无法通过类型检查：

```rust
fn load_session(id: &SessionId) { /* ... */ }

let thread_id = ThreadId("thread-1".to_string());
// load_session(&thread_id); // 类型不匹配
```

它特别适合区分：

- 外部逻辑会话；
- 进程内 Actor；
- Actor 内部 thread；
- 存储记录主键。

这些对象看起来都是 ID，却有不同生命周期和连续性语义。

#### trait 与 `dyn Trait`：隔离实现边界

trait 类似接口，描述多个类型共享的行为：

```rust
#[async_trait::async_trait]
trait EventStore: Send + Sync {
    async fn load(
        &self,
        session_id: &SessionId,
    ) -> Result<Vec<StoredEvent>, StoreError>;
}
```

不同实现可以是：

- 内存 store；
- 快速缓存；
- 远端归档；
- 测试 fake。

调用方只依赖：

```rust
Arc<dyn EventStore + Send + Sync>
```

`dyn EventStore` 是 trait object，使用运行时动态分派。它适合在启动配置或依赖注入时选择实现。

**`Box<dyn Trait>`：拥有一个类型擦除后的值**

```rust
trait CodedError {
    fn code(&self) -> &'static str;
}

enum RequestError {
    Fatal(Box<dyn CodedError + Send + Sync>),
}
```

- `dyn CodedError` 擦除具体错误类型，调用方只依赖 trait；
- `Box` 在 heap 上拥有该具体值，因此可以把不同大小的错误放进同一个 enum variant；
- `Send + Sync` 允许它跨线程移动并通过共享引用访问；
- 方法通过 vtable 动态分派。

这种边界常用于底层模块不应依赖所有具体错误类型、但又要保留稳定错误码的场景。上层可以委托内部对象提供 `code()`，再在对外 API 层映射成公开错误类别；Rust 不会自动完成委托或脱敏，这仍需要显式转换。

与泛型的区别：

```rust
struct Runtime<S: EventStore> {
    store: Arc<S>,
}
```

| 方式 | 分派 | 特点 |
|---|---|---|
| `S: EventStore` | 静态分派 | 编译期确定类型，便于内联，但会让类型向上传播 |
| `dyn EventStore` | 动态分派 | 运行时选择实现，边界稳定，但有 vtable 和 dyn compatibility 约束 |

一个进阶细节：原生 `async fn` 可以写在 trait 中，但含原生 async 方法的 trait 目前不能直接作为普通 trait object 使用。需要动态分派时，项目常用 `async-trait`，或显式返回 boxed Future。阅读项目时应先确认它采用哪一种。

### Runtime 边界与验证

#### Actor：把可变状态所有权集中起来

Actor Model 的基本思路是：

```text
一个 Actor 拥有一份可变状态
其他任务通过消息要求 Actor 修改状态
同一 Actor 内的消息按规则串行处理
```

它减少了到处共享 `Arc<Mutex<State>>` 的需要。

在会话 runtime 中，常见职责拆分是：

- `SessionRegistry`：把逻辑 session 路由到 Actor；
- `RuntimeActor`：拥有当前 session 的进程内可变状态；
- `EventStore`：在 Actor 重建时提供持久历史；
- `ModelProvider`：只消费已投影的消息，不负责持久化。

Actor 仍然只是进程内对象：

> Rust 可以保证 Actor 内存状态的所有权边界，但进程重启后的连续性必须由持久化和 replay 保证。

当一个 task 独占 Actor，并从 channel 串行收取事件时，状态方法可以直接使用 `&mut self`：

```rust
async fn handle_event(&mut self, event: RuntimeEvent) -> Result<(), RuntimeError> {
    self.state.apply(event)?;
    Ok(())
}
```

`&mut self` 表示当前调用独占整个对象；再结合“每个 Actor 只有一个事件循环 owner”，通常不需要把内部状态额外包成 `Arc<Mutex<_>>`。这不代表整个服务被串行化：不同 Actor 仍可由不同 task 并发运行。

**先完成旧生命周期，再启动恢复动作**

收到失败事件时，不一定应立即启动下一次执行。常见做法是先记录 pending intent，等待同一 execution ID 的 `Idle / Settled` 事件，再 dispatch 新执行：

```text
RunFailed(id)
-> pending_recovery = id
-> RunIdle(id)
-> dispatch Resume with a new id
```

这样可以保证错误先可见、旧 owner 已释放、新旧执行不重叠。execution ID 是相关性约束，避免另一次运行的 Idle 误触发恢复。若 pending intent 只存在 Actor 内存里，进程重启时会丢失；需要重启级恢复时，应把 intent 或足以重建 intent 的事实写入 durable journal。

#### Event replay：事件、projection 与 hydrate

一个典型恢复过程：

```rust
let loaded = event_store.load(&session_id).await?;
let replayed = EventLog::from_stored(loaded).try_replay()?;

state.projection = replayed.state;
state.hydrated = true;
```

这里有三个概念：

- event：发生过的事实；
- replay：按顺序重新应用 event；
- projection：从 event 推导出的当前状态，例如 `Vec<Message>`。

**修改 source state 后，要同步失效旧的派生状态。** 例如某个 `last_measured_usage` 是基于旧 history 计算的；替换 history 后若继续保留它，下一轮判断会把旧测量误当成新事实，重复触发动作。最简单的修法是写入新 baseline 时同时设为 `None`，再等待基于新 baseline 的 fresh measurement；更复杂的系统可以给 source 和 derived state 绑定 generation/version。

`hydrated: bool` 只能表示“是 / 否”，无法表达恢复来源和异常原因。更清晰的状态可以是：

```rust
enum HydrationState {
    NotStarted,
    Restored {
        source: RestoreSource,
        event_count: usize,
    },
    Fresh,
    MissingOnResume,
}
```

这能避免：

```text
空事件 replay 成功
-> hydrated = true
-> 调用方误以为历史完整
```

**命令是意图，canonical event 才是 projection 的提交点**

在 actor + event stream 系统中，入口层常同时维护一份便于 HTTP / SSE 使用的 projection。不要在收到请求时就抢先修改它：命令之后还可能被 actor 因权限、路径、并发状态或持久化失败而拒绝。

```rust
fn translate(&mut self, event: RuntimeEvent) -> Vec<WireEvent> {
    if let RuntimeEvent::WorkspaceChanged(change) = &event {
        self.workspace = Some(WorkspaceView {
            roots: change.workspace.roots.clone(),
            current: change.workspace.current.clone(),
        });
    }

    self.translator.translate(event)
}
```

这里先用 `&event` 借用匹配，复制 projection 所需字段，再把原始 `event` move 给 translator。若直接写 `if let ... = event`，可能提前消费 event，后面无法继续传递。

正确顺序是：

```text
request -> command intent -> actor validation/mutation
-> canonical event -> persistence/routing -> secondary projection
```

这样命令被拒绝时，actor 与入口 projection 都保持旧状态；成功事件则成为所有投影共同认可的 commit point。

**一个逻辑变更尽量对应一个 aggregate command**

若一个请求同时携带两个相关字段，不要未经设计就拆成两条独立命令：

```text
错误形态：先更新路径成功 -> 再更新策略失败 -> 请求只生效一半
更稳形态：一个 UpdateCommand { path: Some(...), policy: Some(...) }
         -> actor 一次校验整组字段
         -> 全部接受或全部拒绝
```

Rust 的 `Option<T>` 很适合表达 patch 中“这个字段是否出现”，但原子性来自命令边界和 actor 的验证顺序，不是 `Option` 本身。需要跨持久化系统的真正事务时，还要继续使用数据库事务、WAL、幂等键或补偿机制。

**稳定 authority 与可变 cursor 不应混成一个字段**

文件 workspace、租户 scope、数据库 schema 等结构常同时包含两类状态：

```text
authority / roots：允许访问的稳定边界
cursor / cwd：当前选中的位置
```

请求指定新的 cwd，通常只是改变 cursor，不应把 roots 缩成 cwd。否则从一个子目录启动 session 后，之后即使切换到原 authority 内的 sibling 目录，也会被误判越界。

```rust
match (configured_scope, request.cwd.as_ref()) {
    (Some(mut scope), Some(cwd)) => {
        scope.cwd = Some(cwd.clone()); // 保留 roots，只替换 cursor
        Some(scope)
    }
    (None, Some(cwd)) => {
        Some(Scope::single_root(cwd.clone())) // 兼容无配置模式
    }
    // 其余组合省略
}
```

后续 resolver 仍必须 canonicalize 路径，并验证 `cwd` 位于至少一个 root 内。这里的关键不只是路径安全，而是状态建模：**配置提供 capability boundary，请求只能在 boundary 内选择初始位置。**

#### 同步主写 + 异步旁路：`Ok` 到底确认了什么

再看一个常见双写形态：

```rust
let seq = primary.append(session_id, event).await?;
publisher.publish(event);
Ok(seq)
```

从 API 契约看，`Ok(seq)` 至少确认了 `primary.append` 成功；它是否确认 `publish` 成功，取决于 `publish` 是否返回并传播结果。

如果旁路投递对最终持久化很重要，可考虑：

```rust
let seq = primary.append(session_id, event).await?;
let receipt = publisher.publish(event).await?;
Ok(AppendReceipt { seq, receipt })
```

但这会把两个系统耦合到同一请求延迟和可用性。更常见的可靠设计是 transactional outbox：

```text
在同一主事务中写业务事件 + outbox
-> 独立 worker 重试投递 outbox
-> 投递成功后标记完成
```

Rust 能帮助把 receipt、错误和状态写进类型；是否采用同步双写、异步旁路还是 outbox，仍是系统设计决策。

#### 编译器能保证什么，不能保证什么

| Rust 能帮助保证 | Rust 不会自动保证 |
|---|---|
| safe Rust 中的内存安全 | 远端归档一定有数据 |
| borrow 不会悬空 | 两个存储的数据一致 |
| `&mut T` 的独占访问 | TTL 与产品会话周期一致 |
| `match` 处理已定义的 enum variant | 空列表在业务上是否合法 |
| `Send` / `Sync` 线程边界 | 异步旁路一定投递成功 |
| `Result` 显式携带已建模错误 | 所有业务失败都已经被建模 |

一句话：

> Rust 可以让错误状态难以被误用，但前提是先把业务错误设计成类型，而不是继续用空列表、bool 和日志暗示它。

#### 最小失败测试

适合初学者的第一个练习，是为“恢复已存在会话但两个后端都为空”写测试。

```rust
#[tokio::test]
async fn resume_with_empty_backends_fails_closed() {
    let archive = FakeArchive::returns_empty();
    let cache = FakeCache::returns_empty();
    let provider = RecordingProvider::new();

    let runtime = Runtime::new(archive, cache, provider.clone());

    let result = runtime
        .open(SessionIntent::Resume, SessionId::new("example"))
        .await;

    assert!(matches!(
        result,
        Err(ResumeError::HistoryMissing)
    ));
    assert_eq!(provider.call_count(), 0);
}
```

这个测试同时训练：

- `#[tokio::test]`：在 Tokio runtime 中执行 async test；
- fake implementation：用 trait 替换真实存储；
- `matches!`：按 enum variant 断言；
- fail-closed：恢复证据不足时不调用模型或执行后续副作用；
- 行为验收：不仅检查错误，还检查 provider 没被调用。

还应补充三组对照：

```text
Create + 两端为空 -> FreshSession
Resume + Archive 非空 -> Restored(PrimaryArchive)
Resume + Archive 为空 + Cache 非空 -> Restored(FastCache)
```

#### 初学者检查表

读一段异步 Rust 服务代码时，依次回答：

1. 这个函数拿走所有权，还是只借用？
2. `.clone()` 复制的是指针、handle，还是整份数据？
3. 哪些 `.await` 是潜在暂停点？
4. 是否持有 `MutexGuard` 跨越 `.await`？
5. `Result` 的 `Ok` 中是否还包含业务失败状态？
6. `Option::None` 是否混合了多种缺失原因？
7. 是否可以用 enum 取代 bool、空列表或魔法字符串？
8. `dyn Trait` 隔离了哪一层实现？
9. 某个 `Ok(...)` 究竟确认了哪些副作用？
10. 进程内所有权和跨进程持久化是否被混为一谈？

本节最值得记住的类型关系：

```text
Arc       -> 共享所有权
Mutex     -> 互斥访问
async     -> 构造 Future
.await    -> 等待并允许 task 暂停
Result    -> 成功或已建模错误
Option    -> 有值或无值
enum      -> 枚举业务状态
match     -> 穷举处理状态
dyn Trait -> 运行时多态
newtype   -> 隔离外观相同、语义不同的值
```
