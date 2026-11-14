# Lean 与形式化证明

## 从函数类型读懂一个证明

Lean 把命题表示为类型。证明 `P → Q` 就是构造一个函数，它接收 `P` 的证明，返回 `Q` 的证明。证明 `∀ n : Nat, P n` 也像写函数，只是返回类型随输入 `n` 变化。

```lean
theorem swapAnd (P Q : Prop) : P ∧ Q → Q ∧ P := by
  intro h
  exact ⟨h.right, h.left⟩
```

`intro h` 后，当前上下文多了 `h : P ∧ Q`，目标变成 `Q ∧ P`。`exact` 给出一个顺序正确的证明对。也可以直接写 `fun h => ⟨h.right, h.left⟩`。tactic 是生成证明项的交互方法，最后由 Lean 内核检查证明项的类型。 [Theorem Proving in Lean 4](https://lean-lang.org/theorem_proving_in_lean4/Propositions-and-Proofs/)

### 三种容易混淆的相等

| 层次 | 一个例子 | 用在什么地方 |
| --- | --- | --- |
| 定义相等（definitional equality） | `(fun x : Nat => x) 3` 规约成 `3` | 类型检查时可以通过计算转换，`rfl` 常用于确认 |
| 命题相等（propositional equality） | 变量 `n` 的 `0 + n = n` | 用定理或假设给出证明，再通过 `rw`、`subst` 或等式消去把证明送到目标类型 |
| 工程接口一致 | 改完后，原声明名、类型及评测追踪的生成声明仍满足原契约 | 下游引用、公开 API 或 benchmark 兼容性，需要按验证器实际口径检查 |

依赖类型里，值变了，类型也可能跟着变。比如 `Fin n` 表示小于 `n` 的自然数。已有 `x : Fin n` 和 `h : n = m` 时，可以用 `h` 把 `x` 运输到 `Fin m`，不必重新构造一个数及其上界证明。

```lean
def transportFin {n m : Nat} (h : n = m) (x : Fin n) : Fin m := by
  subst m
  exact x
```

把这个例子放大到工程里，就是复用调用方已经提供的证明，先把类型对齐，再把它传给需要它的构造器。若只在某个普通定义里做了对照，还要回到原来的实例、隐式参数和类型位置验证，那里生成的辅助声明可能不同。 [Lean：等式与替换](https://lean-lang.org/theorem_proving_in_lean4/Quantifiers-and-Equality/) · [Lean 类型系统](https://lean-lang.org/doc/reference/latest/The-Type-System/)

### 能构建，和证明已经闭合，是两次检查

`sorry` 是允许留空的占位符。含 `sorry` 的声明可能照常构建并产生警告。即便某个定理的源码里搜不到 `sorry`，它仍可能间接引用了有缺口的引理。`#print axioms` 能列出传递依赖的公理。比如以下前者已证明，后者预期有警告，公理列表会包含 `sorryAx`。

```lean
theorem checked : True := True.intro
theorem unfinished : True := by sorry

#print axioms checked
#print axioms unfinished
```

项目可能允许 Lean 的标准公理，并对额外公理设限。评测还可以对比提交前后的声明类型，检查删除、改名和签名变化。因此排查时依次看 **能否构建、目标声明类型是否仍在、依赖的公理是否合规、原来通过的声明有没有掉下去**。只数源文件中少了几个 `sorry`，会漏掉跨文件依赖和生成声明。 [Lean：Axioms](https://lean-lang.org/doc/reference/latest/Axioms/) · [Lean：Validating a Lean Proof](https://lean-lang.org/doc/reference/latest/ValidatingProofs/)

## 集合论背景：New Foundations 和 ConNF

无约束地从任意条件构造集合，会遇到 Russell 悖论。试着构造“由所有不属于自身的集合组成的集合” $R$。问 $R$ 是否属于自身，会得到 $R\in R$ 当且仅当 $R\notin R$。

Quine 的 New Foundations（NF）限制 comprehension（按谓词形成集合）的公式。公式必须 **可分层（stratified）**：能给每个变量赋一个辅助层级，使得相等两边层级相同，成员关系右侧比左侧高一层。例如 $x\in y\land y\in z$ 可以赋层级 0、1、2。$x\notin x$ 要求同一个 $x$ 比自己高一层，无法分层。层级用于检查公式，NF 的对象语言仍是无类型集合论。 [Holmes、Wilshaw：New Foundations is consistent](https://randall-holmes.github.io/Nfproof/maybedetangled2-for-arxiv.pdf)

相容性问题问的是公理能否导出矛盾。一条常见思路是为公理构造模型。ConNF 项目沿 Holmes 的证明，在 Lean 中构造 Tangled Type Theory（TTT）的模型，再利用 TTT 与 NF 相容性的等价关系。上游 ConNF 已完成这项形式化。EdgeBench 基于这一既有工程制造证明缺口，任务是恢复通过评测的声明。 [ConNF 项目与 Blueprint](https://leanprover-community.github.io/con-nf/) · [EdgeBench 题目说明](https://github.com/ByteDance-Seed/EdgeBench/blob/main/edgebench/tasks/new_foundations_consistency/NOTES.md)

### 为什么代码里常出现置换、作用、轨道和商

可以用一个很小的例子理解这些词。把三个标签重新命名叫置换。一个置换作用在集合 `{a,b}` 上，就是逐个把标签换掉。只允许交换 `a`、`b` 时，`{a,b}` 保持不变，`{a}` 可以变成 `{b}`。从一个对象出发经所有允许置换能到达的对象，组成它的**轨道**。如果只关心两个对象是否能在这种重命名下互相转换，可以按轨道分组，得到商。

在 Lean 里，`Quotient` 从带等价关系证明的 `Setoid` 得到商类型，`Quot` 是接受关系的更底层原语。对商定义函数时通常要证明它尊重代表元之间的关系。代码中多一层包装，可能多出一条证明依赖，也可能影响 Lean 自动生成的声明。对于复杂的置换模型，排查一个轨道构造或证明运输时，要同时核对结果、原接口和依赖。 [Lean：Quotients](https://lean-lang.org/doc/reference/latest/The-Type-System/Quotients/) · [ConNF Blueprint](https://leanprover-community.github.io/con-nf/)

## 形式化工程的后程怎么排查

先把目标写到一个最小文件里，固定原声明的名字和类型。用 `#check` 看接口，用 `#print axioms` 看依赖。一次只试一种机制，例如复用已给出的等式证明，或把多余包装改写成已有的商构造。小例子成立后，把改动放回原模块，确认依赖它的声明也通过。最后按题目规定运行 `lake build` 和正式检查，比较修复集、仍失败的声明、类型变动和新增失败。

公开的 Astra max 五臂案例中，Official 达到 2,065/2,246 后，随后 11 次提交都没有再涨。带证据记录与周期复盘的 Explore 臂在后程继续验证未覆盖的声明，最终到 2,074/2,246。工程上的抓手是让下一轮知道具体哪个假设已经失败、哪些类型得守住、哪份候选已经正式通过。该批轨迹展示了后程仍能产出可验证增量。复盘机制的净贡献需要同状态续跑的独立对照。 [LoopX 的五臂轨迹](https://loopx-project.github.io/loopx/blog/edgebench-feedback-and-memory/#astra-late-breakthrough)

最小练习是在有 Lean 4 的环境里运行 `lean Example.lean`。先对照 `checked` 和 `unfinished` 的公理输出，再另写一个引用 `unfinished` 的定理，检查它如何继承 `sorryAx`。进入 ConNF 时，沿项目自己的 `lean-toolchain`、依赖锁定和构建说明运行。通用 Lean 练习用标准环境，题目复现用题包固定的工具链。 [Lean 工具链安装](https://lean-lang.org/install/) · [ConNF 构建说明](https://leanprover-community.github.io/con-nf/)
