# Code Reading: Polars 行扩展模式

来源：脱敏整理自一次 Polars LazyFrame 代码阅读。业务语义、原函数名、原字段名和实际用途均已替换为通用表达；这里只沉淀读代码时可复用的列式处理模式。

## 每行生成 List 列，再展开成多行

这类代码常见于一种通用转换：

```text
原始表
 -> 每行生成一个 list-valued column
 -> 将 list 展开成多行
 -> 用行号把原始上下文 join 回来
 -> 替换 / 派生部分字段
 -> 得到一张派生表
```

核心不是某个业务函数，而是 Polars 里的几个基础动作：

- `with_row_index`：给原始行显式加行号。
- `with_columns`：新增一个 `List` 类型列。
- `select`：只保留展开所需的窄列，减少中间数据量。
- `explode`：把一行里的 list 展成多行。
- `join`：通过行号把原始上下文补回来。
- `alias` / `pl.lit`：覆盖或新增派生字段。

## 为什么要先加行号

Polars 的表没有稳定的隐式“行身份”。一旦执行 `explode`，一行可能变成多行，原来的行位置就不能再当作可靠身份使用。

因此先做：

```python
indexed_lf = lf.with_row_index("__src_row")
```

`__src_row` 是一个显式来源行号。后续每条展开后的记录都能通过它知道自己来自原表哪一行。

## 每行生成一个 `List` 列

可以先给每行新增一个列表列：

```python
prepared_lf = indexed_lf.with_columns(
    pl.col("source_col")
      .some_expr_or_udf(...)
      .alias("__values")
)
```

这里的 `__values` 是 `List` 列。示意如下：

| `__src_row` | `source_col` | `context_col` | `__values` |
|---:|---|---|---|
| 0 | A | c1 | `[X, Y]` |
| 1 | B | c2 | `[]` |
| 2 | C | c3 | `[Z]` |

这种写法的好处是：先把“一行对应多个派生值”表达成列式 `List`，暂时不复制整行上下文。

## 只展开窄表

展开前先只保留来源行号和列表列：

```python
expanded_values_lf = (
    prepared_lf
    .select(["__src_row", "__values"])
    .explode("__values")
)
```

得到：

| `__src_row` | `__values` |
|---:|---|
| 0 | X |
| 0 | Y |
| 2 | Z |

这样做比直接对整张宽表 `explode` 更稳：中间表更窄，避免在展开阶段重复复制大量上下文字段。

## join 回原始上下文

展开后，再通过 `__src_row` 把原始行的其他字段补回来：

```python
joined_lf = expanded_values_lf.join(
    indexed_lf,
    on="__src_row",
    how="left",
)
```

示意：

| `__src_row` | `__values` | `source_col` | `context_col` |
|---:|---|---|---|
| 0 | X | A | c1 |
| 0 | Y | A | c1 |
| 2 | Z | C | c3 |

语义上，这一步是：每个展开后的值复制一份原始上下文。

## 替换或新增派生字段

最后可以用展开后的值覆盖某个字段，或新增一个标记字段：

```python
result_lf = joined_lf.with_columns([
    pl.col("__values").alias("source_col"),
    pl.lit("derived").alias("label_col"),
])
```

如果临时列不再需要，可以删除：

```python
result_lf = result_lf.drop(["__src_row", "__values"])
```

## 通用代码骨架

```python
import polars as pl

src_row_col = "__src_row"
values_col = "__values"

indexed_lf = lf.with_row_index(src_row_col)

prepared_lf = indexed_lf.with_columns(
    pl.col("source_col")
      .some_expr_or_udf(...)
      .alias(values_col)
)

expanded_values_lf = (
    prepared_lf
    .select([src_row_col, values_col])
    .explode(values_col)
)

result_lf = (
    expanded_values_lf
    .join(indexed_lf, on=src_row_col, how="left")
    .with_columns([
        pl.col(values_col).alias("source_col"),
        pl.lit("derived").alias("label_col"),
    ])
    .drop([src_row_col, values_col])
)
```

## 性能直觉

这个模式比 Python row-wise 循环更 Polars-native：

- 多值结果先放在 `List` 列里，而不是 Python 里一行行构造 `dict`。
- 展开用 `explode`，属于 Polars 的列式操作。
- 原始上下文通过 `join` 回补，避免在生成列表时复制整张宽表。
- 整体可以保留在 `LazyFrame` 计划里，让 Polars 优化执行。

一句话：先用 `List` 列承载“一行多值”，再用 `explode + join` 把它变成“一值一行”，这是 Polars 中处理行扩展类逻辑的常用列式模式。
