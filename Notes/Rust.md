# Rust

## 基础语法：结构体与反序列化

来源：脱敏整理自一次 Rust 配置结构体阅读。原始业务字段不作为笔记主题保留，这里只沉淀通用语法。

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
