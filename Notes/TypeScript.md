# TypeScript

> 相关：[Rust.md](./Rust.md)、[AI-Agent-Engineering.md - LoopX 长程 agent 的本地控制面](./AI-Agent-Engineering.md)、[Software-Engineering.md - Strangler Fig](./Software-Engineering.md)。

## 阅读地图

1. “TypeScript 心智模型”先建立 TS / JS / Node 的分工，理解类型擦除；`erasableSyntaxOnly` 约束源码语法，实际运行兼容性仍需验证。
2. “类型基础”把 interface、readonly、泛型、Generator、`as const`、判别联合、`unknown`、Promise 看作同一种动作：把协议或状态写进类型；Generator 区分产出、结束返回与恢复输入，惰性迭代不等于端到端流式读取；Node 调度、`return await` 与回调时序三节说明类型不表达运行时边界。
3. “状态机建模”讲核心设计原则：让非法状态无法构造，而不是靠运行时 `if` 拦截。
4. “Effect Program 与语义内核”以 LoopX PR-1 为例，讲纵向迁移如何把 settlement / journal 语义收口到 TS。
5. “Runtime 工程模式”沉淀幂等重试、fail closed、常驻 runtime 生命周期、共享解析缓存与性能基线；缓存内容有效性和共享对象的修改隔离需要分别保证。
6. “迁移策略与验证”解释为什么纵向切片优于“先迁测试”、六层验证金字塔，以及并发测试如何控制交错、用 Proxy 做定点故障注入。
7. “学习路径”和“源码阅读检查表”给动手顺序和读代码时的检查问题。

类型工具的组合读法：`Pick` 限制函数依赖，`Partial<Pick<…>>` 限制构造器可调项，`Extract<Awaited<ReturnType<…>>, …>` 从异步接口派生阶段输入；更新协议用判别联合区分 keep / clear / set。内置 `Omit` 不会分配到联合成员上（`keyof` 只留共同键），需要保留分支时改用分配式条件类型。静态类型、运行时校验与业务授权分别承担不同约束。

数组与集合操作还要区分值、位置与顺序：[`map` 的 ordinal](#map--filter位置属于来源快照)可以被推断为 `number`，但类型不证明它属于正确的数组快照；[`Map` 的首次插入顺序](#map首次插入顺序与分组)可以决定分组展示顺序，不能随意换成普通对象。

对象操作还要区分“值类型合法”“必填键齐全”与运行时属性语义：[`Record` + `satisfies`](#record--satisfies在动态转换前检查键完整性)先检查领域对象，动态写入还需正确处理 `__proto__` 等键。跨语言排序也要明确比较的是 UTF-16 码元还是 Unicode 码点，不能仅按运算符外观迁移。

## TypeScript 心智模型

### TS / JS / Node 是什么

| 概念 | 作用 |
|---|---|
| JavaScript | 真正运行的语言 |
| TypeScript | 给 JavaScript 增加的静态类型检查层 |
| Node.js | 在服务器 / CLI 环境运行 JavaScript 的 runtime |
| `tsc` | TypeScript 类型检查器 / 编译器 |
| `package.json` | Node 项目的依赖、命令和 runtime 要求 |
| `tsconfig.json` | TypeScript 的类型检查规则 |

```ts
function add(a: number, b: number): number {
  return a + b;
}
```

运行时不存在 `number` 这些类型：`tsc` 先检查，Node 实际执行的是去掉类型后的 JavaScript。因此：

> TypeScript 能检查代码内部的类型关系，但不能自动保证网络、JSON、磁盘文件中的数据符合类型。

这也是 TS runtime 的输入仍需要 `requiredString()`、`asObject()` 等运行时校验的原因。PR-1 使用 Node 22.6+ 的 type stripping 直接执行 `.ts` 文件，不额外生成 `.js` 构建产物。

### `erasableSyntaxOnly`：约束可擦除语法

```json
{ "compilerOptions": { "erasableSyntaxOnly": true } }
```

该选项限制不能仅靠擦除 TS 语法来运行的写法。例如 `constructor(public store: Store) {}` 中的参数属性还隐含创建字段与赋值；`enum` 通常也需要生成运行时代码，因此都会被拒绝。可改用显式字段与赋值、字符串联合等写法。

它把类型擦除的语法边界前移到编译期，但不保证目标 Node 版本能解析、加载并正确执行源码，仍需实际运行验证。参考：[官方配置说明](https://www.typescriptlang.org/tsconfig/#erasableSyntaxOnly)。

### `private constructor`：旧的 TS 语法，新的 runtime 兼容性边界

`private constructor(after: string | null, offset: bigint, limit: number)` 不是 TypeScript 6 的新特性：`private` 是 TypeScript 的构造器访问修饰符，至少从 TypeScript 2.0 就已支持；参数类型注解则会在编译后被擦除。它表达的是：类外不能 `new`，子类也不能继承这个类，实例必须由类内部或静态 factory 创建。

```ts
class AuthorityJournalScan {
  private constructor(after: string | null, offset: bigint, limit: number) {}
}
```

`tsc` 会把它变成 JavaScript 形态：

```js
class AuthorityJournalScan {
  constructor(after, offset, limit) {}
}
```

因此，LoopX 用它把 `prepare()` 设为唯一构造入口：先校验 cursor / limit，再创建 `AuthorityJournalScan`，避免外部直接构造未验证对象。这是 **controlled construction**，不是 runtime 的硬私有；它和 JavaScript 的 `#private` 字段不是一回事。

| 写法 | 约束发生在哪里 | 编译 / 运行时含义 |
|---|---|---|
| `private constructor()` | TypeScript 类型检查 | 编译后只是普通 `constructor()`；直接 `new` 的限制会消失 |
| `#field` | JavaScript runtime | 运行时仍保持私有，但不能写成 `#constructor` |

这也解释了 [PR #4287](https://github.com/huangruiteng/loopx/pull/4287) 的 comment：最低版本 job 使用 Node.js 22.6.0 的内置 `strip-types`，它最初只做轻量的类型擦除，不是完整的 TypeScript 编译器；在 [新扫描器的第 12 行](https://github.com/huangruiteng/loopx/blob/1588949ccc4c7ff5cf96250db9fc25807db91925/loopx/control_plane/coordination/authority_journal_scan.ts#L12) 解析到 `private constructor` 时，Node 不能把这个 TS-only 修饰符转换掉，于是报 `Unexpected identifier 'constructor'`。`tsc` 通过不代表声明的最低 Node runtime 一定能加载源码。

兼容 Node 22.6 的直接修复是去掉 `private`，保留显式字段和赋值；但这会削弱“只能由 `prepare()` 构造”的静态门禁。若该不变量重要，应把校验放进普通构造器，或使用模块私有 token / factory 在运行时继续保护构造入口，并补一个最低版本的直接 import smoke test。Node 官方也明确区分了轻量 type stripping 与完整 TypeScript 支持：[Node.js 22.6.0 release note](https://nodejs.org/en/blog/release/v22.6.0)、[TypeScript runtime 文档](https://nodejs.org/api/typescript.html#type-stripping)。

### 核心结论

> TypeScript 对 LoopX 的主要价值，不是“代码更短”或“运行更快”，而是把状态机、协议、effect 顺序和失败分支变成编译器能够检查的结构。

PR-1 做的不是“把 Python 翻译成 TS”，而是一次纵向迁移：

1. TypeScript 成为 Effect Program 与 settlement 规则的唯一语义所有者；
2. Python 保留兼容入口和仍未迁移的副作用 callback；
3. 引入一个可复用的常驻 TS runtime；
4. Turn journal 的判断和真实原子写入已迁到 TS；
5. 同一个 PR 删除对应 Python 解释器，避免长期维护两套规则。

## 类型基础：把协议写进类型

### interface：对象合同与结构类型

```ts
export interface SettlementIdentityInput {
  goal_id: string;
  agent_id: string;
  todo_id?: string | null;
  turn_instance_id: string;
  replan_obligation_id?: string | null;
}
```

它表示合法输入必须有 `goal_id`、`agent_id`、`turn_instance_id`，而 `todo_id` / `replan_obligation_id` 可缺省或为 `null`。Python 的 dataclass 也能表达，但 TS 的优势是接口直接约束所有调用者、handler、测试和返回值——重命名字段时，`tsc` 会把所有受影响位置找出来。

TypeScript 是结构类型（structural typing）：

```ts
const input = {
  goal_id: "g1",
  agent_id: "a1",
  turn_instance_id: "t1",
};

settlementIdentity(input);
```

只要对象结构满足接口即可，不必显式声明“它是某个类的实例”。

**弱类型检测（weak type detection）不等于额外字段白名单。** 下面的 `Context` 属性全部可选，属于弱类型；将一个有属性、却与它没有任何共同属性的对象赋给它，会触发错误：

```ts
interface Context { work_summary?: string; rationale?: string }

const unrelated = { agent_id: "伪造身份" };
const rejected: Context = unrelated; // 错误：没有共同属性

const raw = { work_summary: "已完成调查", agent_id: "伪造身份" };
const context: Context = raw; // 通过：存在共同属性，且属性类型兼容
Object.keys(context); // ["work_summary", "agent_id"]

const empty: Context = {}; // 通过：所有属性都可省略
```

还要区分多余属性检查（excess property checking）：直接把对象字面量赋给 `Context`，显式写出的未知字段会被检查；经变量传入时，结构类型仍可能容许额外字段。

```ts
const direct: Context = {
  work_summary: "已完成调查",
  agent_id: "伪造身份", // 错误：对象字面量含未知属性
};
```

有共同属性只消除了“完全无交集”的错误，仍须满足属性类型等约束。类型注解既不复制对象，也不删除字段；`context` 仍引用 `raw`，序列化或展开它时，`agent_id` 仍可能被带出。需要严格字段边界时，应使用 [协议解码校验](#requireexactfields把-json-当版本化协议) 拒绝未知字段，或逐字段构造新对象。参考：[TS 2.4 — Weak Type Detection](https://www.typescriptlang.org/docs/handbook/release-notes/typescript-2-4.html#weak-type-detection)、[Excess Property Checks](https://www.typescriptlang.org/docs/handbook/2/objects.html#excess-property-checks)。

### readonly：表达不可在原地修改

```ts
export interface EffectProgram {
  steps: readonly EffectStep[];
  execution_mode: string | null;
}
```

`readonly EffectStep[]` 让 `program.steps.push(newStep)` 直接成为类型错误。这对状态机很重要：receipt、计划、phase prefix 应更接近不可变值，而不是任何函数都能原地修改的共享 list。

注意边界：`readonly` 只阻止 TypeScript 调用者直接修改数组，**不会冻结运行时对象，也不会深度复制内部字段**。如果 Store 把内部 receipt 数组直接返回给外部，调用方仍能通过嵌套对象改坏内部状态。做法是返回前做值隔离：

```ts
structuredClone(transaction.receipts)
```

Conformance 测试会故意修改返回的 projection，再重新读取，验证内部状态没有变化——这是在验证 value isolation，不是普通类型检查。

共享数据可以按使用需求选择复制或冻结：

| 方式 | 运行时效果 | 成本与边界 |
|---|---|---|
| 每次深拷贝 | 调用者修改自己的副本 | 每次都要遍历、分配，增加 GC 压力 |
| 逐层冻结后共享 | 调用者共用不可修改的对象图 | 冻结也有遍历成本，但同一缓存值只需做一次；需要修改的调用者另行复制 |

`Object.freeze()` 只冻结当前这一层，不会沿引用自动递归：

```js
const data = { items: [{ count: 1 }] };
Object.freeze(data);
data.items[0].count = 2; // 仍能修改：items 和内部对象都没有冻结
```

对普通 `JSON.parse()` 产生的对象与数组，需要逐层冻结后再共享；基本类型无需处理。这个结论不能直接推广到任意 JS 对象，例如冻结 `Map` 本身仍不能阻止 `.set()`。参考：[Object.freeze 与 deep freezing](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Object/freeze#deep_freezing)。缓存的磁盘有效性另见[共享解析缓存](#共享解析缓存内容有效性与引用隔离)。

### 泛型：同一结构承载不同 value

```ts
export interface SettlementResult<Value = unknown> {
  value: Value | null;
  receipts: readonly SettlementReceipt[];
  failure: SettlementFailure | null;
}
```

`SettlementResult<string>`、`SettlementResult<SettlementIdentity>`、`SettlementResult<JsonObject>` 共享 receipt / failure 结构，但成功值不同。这比把所有返回值写成 `dict[str, Any]` 更容易理解，也让 IDE 知道 `value` 里究竟是什么。

注意：当前接口理论上允许 `value` 和 `failure` 同时存在。更强的表达见“状态机建模”。

泛型参数只建立“可赋值关系”，不自动建立“值相等关系”。`S` 可以被推断成联合类型，因此两个参数不一致也可能通过检查：

```ts
declare function pair<S extends string>(schema: S, returned: S): S;

const value = pair("create_v0", "archive_v0");
// S 可被推断为 "create_v0" | "archive_v0"
```

如果第一个参数应决定合同，其他位置只能服从，可用 [`NoInfer<S>`](https://www.typescriptlang.org/docs/handbook/release-notes/typescript-5-4.html)：

```ts
declare function pair<S extends string>(
  schema: S,
  returned: NoInfer<S>,
): S;

pair("create_v0", "archive_v0"); // 类型错误
```

`NoInfer<S>` 仍要求参数满足 `S`，但不让该位置参与推断；它收紧的是推断来源，不是运行时校验。

**品牌类型：给字符串附加用途身份。** 普通别名仍都是 `string`，品牌则模拟名义类型，防止把 `ProviderRevision` 接到需要 `OperationId` 的位置：

```ts
type OperationId = string & { readonly __brand: "OperationId" };
type RequestDigest = string & { readonly __brand: "RequestDigest" };
type ProviderRevision = string & { readonly __brand: "ProviderRevision" };

declare const revision: ProviderRevision;
declare function recover(id: OperationId): void;

recover(revision); // 类型错误
```

在 LoopX 中，`OperationId` 用于定位原操作，`RequestDigest` 用于核对请求意图，`ProviderRevision` 用于并发版本比较。品牌只防内部误接线：JSON 字符串仍须在解析边界验证后才能获得对应品牌，也不代表权限、存在性或租约有效。

参考：[TypeScript 名义类型示例](https://www.typescriptlang.org/play/typescript/language-extensions/nominal-typing.ts.html)。

### Generator<Y, R, N>：产出、结束与恢复输入

生成器函数 `function* distinctTurns(...)` 的返回类型 `Generator<Run, void, unknown>` 描述三个通道：

| 参数 | 含义 | 本例 |
|---|---|---|
| `Y` | 每次 `yield` 交给调用方的值 | `Run` |
| `R` | 生成器结束时的返回值 | `void`，不返回有用的终值 |
| `N` | 调用方通过 `.next(value)` 传回、由 `yield` 表达式接收的值 | `unknown`；本例未使用此输入通道，并非禁止传值 |

相较于先构造完整的去重 `Run[]`，生成器让调用方**按需取下一条**：计数达到 2、6 或 20 次阈值即可停止，省去后续遍历与完整结果数组的构造。这里惰性发生在去重迭代层，历史输入的解码仍是有界批量处理，不能据此称整个系统已改成流式读取。

来源：[TypeScript 3.6：Stricter Generators](https://www.typescriptlang.org/docs/handbook/release-notes/typescript-3-6.html#stricter-generators)。

### as const：从数组得到字面量联合

```ts
export const SETTLEMENT_STEP_KINDS = [
  "validation",
  "durable_writeback",
  "quota_spend",
  "terminal_closeout",
] as const;

export type SettlementStepKind =
  (typeof SETTLEMENT_STEP_KINDS)[number];
```

`as const` 后得到的不是普通 `string`，而是四个字面量的联合；`const step: SettlementStepKind = "quota_spned"` 会被编译器拒绝。对 LoopX 特别有价值，因为过去许多控制面 bug 的根源是：字符串拼错、新增状态后漏处理、某个模块使用旧枚举、不同模块对同一状态含义理解不同。

另一处常见写法（把“转换名/状态名”收窄成联合）：

```ts
const TRANSITIONS = [
  "initial",
  "identity_reset",
  "advance_after_interval",
] as const;

type Transition = typeof TRANSITIONS[number];
```

关键读法：`[number]` 是**索引访问类型（indexed access）**，对数组 / 元组类型做 `[number]`，得到“任意下标位置的元素类型”——这里是三个字面量的联合。名字容易误导，它不是“第 number 个元素”，而是“元素们的类型”：

```text
typeof TRANSITIONS        -> readonly ["initial", "identity_reset", "advance_after_interval"]
typeof TRANSITIONS[number] -> "initial" | "identity_reset" | "advance_after_interval"
```

两个等价写法：`(typeof TRANSITIONS)[number]` 与 `typeof TRANSITIONS[number]`，后者读起来像 `typeof (TRANSITIONS[number])`，但意义相同。

最容易踩的坑是**去掉 `as const`**：此时 `typeof TRANSITIONS` 是 `string[]`，`[number]` 只能得到 `string`，字面量联合消失。收窄是 `as const` 做的，`[number]` 只是把它取出来——两者缺一不可。

如果是对象而不是数组，对应写法是 `keyof typeof OBJ` 生成键的联合：数组擅长表达“一组候选值”，对象擅长表达“一组键”，按场景选择。

这类联合类型是状态机 / 协议的基础素材：判别字段的候选值、合法的状态集合、白名单配置都可以从“单一来源数组”派生，新增一项时所有 `switch` / 判别收窄 / 校验点会被编译器推动着一起更新（见“判别联合与 never”）。

**`as const satisfies`：既要精确，又要校验**

如果联合类型已经定义好（比如 `SettlementStepKind`），又想从一个数组推导出精确成员，可以：

```ts
const BASE_SETTLEMENT_STEPS = [
  "validation",
  "durable_writeback",
  "quota_spend",
] as const satisfies readonly SettlementStepKind[];
```

两个关键字分工不同：

- `as const` 保留精确字面量和 tuple 顺序；
- `satisfies` 检查每个成员都符合 `SettlementStepKind`，但不会把精确类型扩宽成普通数组。

误写 `"quota_spned"` 编译器直接报错；同时后续代码仍知道数组里是三个具体 step，而不是“某些字符串”。

对比单纯类型注解：

```ts
const steps: readonly SettlementStepKind[] = [...]
```

后者合法，但会把数组收窄声明成 `readonly SettlementStepKind[]`，丢失精确 tuple 信息。区别在于：类型注解是「要求值符合声明类型」，而 `satisfies` 是「校验表达式是否符合目标类型，同时保留表达式自身的类型」。

不过这句话要说得更精确一点：**`satisfies` 保留表达式自身的类型，但目标类型仍会作为上下文类型参与推断**，于是结果不一定等于「完全没有目标类型时的推断」。两个可验证的后果：

```ts
const a = { allowed: true };
a.allowed = false;  // 可以：a.allowed 推断为 boolean

const b = { allowed: true } satisfies { allowed: boolean };
b.allowed = false;  // 报错：这里保留了字面量类型 true
```

原因是 `boolean` 本身就是 `true | false`，当上下文期望的类型是字面量类型（或字面量类型的联合）时，字面量不会被扩宽——`satisfies` 并不等于「绕开目标类型」。

```ts
interface Observation {
  hash: string;
  proof?: { version: number };
}

const a = { hash: "abc" } satisfies Observation;
a.proof = { version: 3 };  // 报错：a 的类型里没有这个属性

const b: Observation = { hash: "abc" };
b.proof = { version: 3 };  // 可以
```

`satisfies` 只检查、不补全：目标类型里「对象字面量没有写出来的可选属性」不会进入推断结果。后续需要写入这些字段时，就用明确的类型注解，或者在字面量里把字段写出来。

同样地，`satisfies` 是静态检查，**不会在运行时裁掉字段**：

```ts
type Edit = { note?: string };

const source = { note: "reviewed", actor: "B" };
const edit = { ...source } satisfies Edit;

console.log(edit.actor);  // "B"，字段仍然存在
```

对象字面量里**显式写出**的多余属性可能被 excess property check 拦下；而通过展开（`...source`）带进来的属性会原样保留。类型只表达设计意图，运行时白名单得由输入边界自己执行——比如需要「只传指定字段」时，就得显式构造新对象，而不是指望 `satisfies` 或 `Pick` 帮忙裁剪。

### Record + satisfies：在动态转换前检查键完整性

**先区分运行时对象与编译器知道的类型。** `Object.fromEntries` 是 JavaScript 函数，把一组 `[键, 值]` 转成对象；键就是对象的属性名：

```ts
const counts = Object.fromEntries([
  ["open_items", 2],
  ["done_items", 1],
]);
// 实际对象：{ open_items: 2, done_items: 1 }
// 标准库推断的类型：{ [k: string]: number }
```

这里没有把实际对象的键删掉；丢失的是返回类型里“必定包含 open_items、done_items”的保证。标准库通用重载的返回类型为 `{ [k: string]: T }`，`T` 表示值的类型；`[k: string]` 是字符串索引签名，约束字符串键对应的值类型，不列出必须存在的属性。例如空对象 `{}` 也能赋给 `{ [k: string]: number }`，不能据此断言任意键真的存在。开启 `noUncheckedIndexedAccess` 后，经这种索引签名读取的值还会带 `undefined`。

**`Record<键集合, 值类型>` 可以把必填栏目列成类型。** 假设待办摘要必须包含“待办”和“已完成”两个栏目，lane 只是业务里的“分组名称”，不是 TS 关键字：

```ts
type TodoSummaryLane = "open_items" | "done_items";
type Row = { ordinal: number; text: string };

type Selected = Record<TodoSummaryLane, readonly Row[]>;
// 相当于：
type SelectedExpanded = {
  open_items: readonly Row[];
  done_items: readonly Row[];
};
```

`|` 表示“或”，一个 `TodoSummaryLane` 值只能是这两个字符串之一；`Record` 则要求联合中的**每一个键都存在**。`Row` 定义一条记录的形状，`Row[]` 是记录数组，`readonly Row[]` 是只读数组类型；上面的属性没有 `?`，所以不能省略。

对照看，`Record<string, number>` 是没有指定必填键的字典，`Record<TodoSummaryLane, number>` 则必须有这两个键。同样，`TodoSummaryLane[]` 只检查数组中每个名称是否合法，`["open_items"]` 仍合法，不保证覆盖全部栏目。

**`satisfies` 要求编译器在对象构造处对照这份合同。**

```ts
const openRows: readonly Row[] = [{ ordinal: 0, text: "写笔记" }];
const doneRows: readonly Row[] = [{ ordinal: 1, text: "读材料" }];

const selected = {
  open_items: openRows,
  done_items: doneRows,
} satisfies Record<TodoSummaryLane, readonly Row[]>;

const missing = {
  open_items: openRows,
} satisfies Record<TodoSummaryLane, readonly Row[]>;
// 编译错误：缺少必填的 done_items
```

可以把 `satisfies` 读作“请检查左边是否符合右边的类型”。此处能检查漏键、值类型错误，以及直接写出的属性名拼错；它在编译时工作，不会运行一遍检查函数，不会自动补齐字段。它也不是要求精确删除额外字段，展开对象等边界见前面的 `as const satisfies` 小节。

若将 `TodoSummaryLane` 扩展为 `"open_items" | "done_items" | "blocked_items"`，原来的 `selected` 就会因缺少 `blocked_items` 报错，推动摘要构造逻辑一起更新。该联合应来自业务合同；若仅从 `selected` 反推键集合，就无法发现它相对业务要求漏了什么。

这件事也能用普通类型注解完成：`const selected: Selected = { ... }`。`satisfies` 的作用是检查可赋值关系并保留表达式自身的类型信息（目标类型仍会参与上下文推断），不必把它视为唯一正确写法。`as Selected` 则是类型断言，不能用来证明字段真的齐全。

**完整性检查放在动态转换之前，因为这时编译器还看得见具体键。** 例如传输层只需要每个栏目的原始 ordinal：

```ts
const lanes = Object.fromEntries(
  Object.entries(selected).map(([lane, rows]) =>
    [lane, rows.map(row => row.ordinal)] as const,
  ),
);
// 实际对象：{ open_items: [0], done_items: [1] }
// 标准库返回类型：{ [k: string]: number[] }
const json = JSON.stringify({ lanes });
```

`Object.entries` 将对象拆成键值对；`map` 保留栏目名，将记录数组换成 ordinal 数组；`as const` 在这里保留每一对的 tuple 结构；`Object.fromEntries` 再组装对象。真正生成 JSON 文本的是 `JSON.stringify`，`fromEntries` 本身不负责序列化。

如果只在这个宽返回类型后面加 `satisfies Selected`，并不能找回原来的键信息，而且上例的值也已从 `Row[]` 转成 `number[]`。即使检查目标改成 `Record<TodoSummaryLane, number[]>`，该通用返回类型仍未证明必填键存在。原始 `selected` 已经通过检查，也不意味着后续转换可以任意过滤或漏掉栏目；转换过程仍需遵守一一映射的合同。

三层检查各管一件事：**构造时用 `Record` 检查栏目齐全；转换时保持键和值的映射；接收外部 JSON 时做运行时校验。** TS 类型不会随 JSON 传到另一种语言，接收端仍要检查键集合、数组形状，以及 ordinal 是否属于原快照和选中集合，见 [map + filter：位置属于来源快照](#map--filter位置属于来源快照)。

参考：[TypeScript — Record](https://www.typescriptlang.org/docs/handbook/utility-types.html#recordkeys-type)、[TS 4.9 — satisfies](https://www.typescriptlang.org/docs/handbook/release-notes/typescript-4-9.html#the-satisfies-operator)、[TS 5.9.3 标准库 fromEntries 声明](https://github.com/microsoft/TypeScript/blob/v5.9.3/src/lib/es2019.object.d.ts)。此处讨论通用重载；标准库另有返回 `any` 的宽重载，同样不能提供键完整性保证。

**`Record` 不改变动态属性写入的语义。** `Record<string, number>` 只是静态类型，`{}` 仍是普通 JavaScript 对象，不会自动变成“任何键都只作为数据”的字典：

```ts
const sources: Record<string, number> = {};
const key = "__proto__";
const ordinal = 7;

sources[key] = ordinal;
Object.hasOwn(sources, key); // 默认对象原型下为 false：没有创建自身属性

Object.defineProperty(sources, key, {
  value: ordinal,
  enumerable: true,
  writable: true,
  configurable: true,
});
Object.hasOwn(sources, key); // true
JSON.stringify(sources); // '{"__proto__":7}'
```

普通赋值可能调用继承的 `__proto__` setter；此例的数字值会被忽略，而不是保存为自身属性，也不是修改了原型。`Object.defineProperty` 则直接定义自身数据属性，不调用该继承 setter；`enumerable: true` 让键参与枚举和 JSON 序列化，另外两项允许改值与重新配置。创建属性时这三个标志默认都是 `false`，需要按合同显式设置。

因此，类型检查通过不代表动态写入符合协议；对来源表、计数表等开放键集合，须明确采用自身数据属性、无原型对象或 `Map`，并分别检查序列化与消费端的行为。参考：[ECMAScript — Object.defineProperty](https://tc39.es/ecma262/multipage/fundamental-objects.html#sec-object.defineproperty)、[MDN — `__proto__`](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Object/proto)。

### 判别联合与 never：状态机的穷尽检查

**`|`：联合类型（union type）**

`|` 读作「或」。`type X = A | B` 表示 X 可以取 A 或 B 中的一种形态。下面 `SettlementNextAction` 是三个对象形状的联合：一个结算决策要么是 `failed`、要么是 `execute`、要么是 `complete`。

关键点：

- 联合里的每个分支叫一个 member / variant；
- 变量是联合类型时，必须先确定它落在哪个分支（用判别字段判断、`switch`、`typeof` / `in` 收窄），TS 才允许访问该分支独有的字段；
- 没有收窄前，只能访问所有分支共有的字段。

```ts
type Result =
  | { ok: true; value: string }
  | { ok: false; error: string };

function show(r: Result) {
  if (r.ok) {
    r.value; // 已收窄到 { ok: true; ... }
  } else {
    r.error; // 已收窄到 { ok: false; ... }
  }
}
```

**`const` 解构后仍可关联收窄（TS 4.6+）。** 如果类型把 `status` 与 `next_action` 的合法组合写成判别联合，检查解构出的 `status`，也能收窄同时解构出的 `next_action`：

```ts
type ProgressResult =
  | { status: "current" | "delivered"; next_action: "finish" }
  | { status: "waiting"; next_action: "retry" };

function handle(result: ProgressResult) {
  const { status, next_action } = result;
  // 此时 next_action: "finish" | "retry"

  if (status === "current" || status === "delivered") {
    const action: "finish" = next_action; // 已收窄为 "finish"
  }
}
```

`const { ... } = result` 是对象解构；`if` 触发控制流分析；`: "finish"` 是字符串字面量类型注解，要求赋值只能是这个字符串。它不是 `as` 断言，也不会在运行时把值转换成 `"finish"`；纯 JavaScript 没有这段类型注解。

关键是原类型已经表达了字段关联。如果把两个字段各自写成独立的联合（`status: "current" | "delivered" | "waiting"`、`next_action: "finish" | "retry"`），类型就允许任意组合，检查 `status` 不能推出 `next_action`。这里的能力适用于 `const` 解构，也支持函数体内从不重新赋值的解构参数，不能泛化为任意 `let` 解构。参考：[TS 4.6 — Control Flow Analysis for Destructured Discriminated Unions](https://www.typescriptlang.org/docs/handbook/release-notes/typescript-4-6.html#control-flow-analysis-for-destructured-discriminated-unions)。

`|` 也用于字面量联合（`"running" | "succeeded" | "no_change"`），与对象联合是同一机制。

```ts
export type SettlementNextAction =
  | {
      decision: "failed";
      step_kind: null;
      result: SettlementResult<JsonObject>;
    }
  | {
      decision: "execute";
      step_kind: SettlementStepKind;
      result: SettlementResult<JsonObject>;
    }
  | {
      decision: "complete";
      step_kind: null;
      result: SettlementResult<JsonObject>;
    };
```

`decision` 是判别字段。判断 `if (action.decision === "execute")` 后，TS 自动知道 `step_kind` 不可能是 `null`。配合穷尽 `switch`：

```ts
switch (action.decision) {
  case "execute":
    return run(action.step_kind);
  case "complete":
    return finish();
  case "failed":
    return fail(action.result);
  default: {
    const unreachable: never = action;
    return unreachable;
  }
}
```

以后新增 `"paused"` 但忘记更新这个 `switch`，`never` 会让 typecheck 失败。这就是 TS 对状态机真正有价值的地方：

> 新增一种状态时，编译器会指出所有没有同步理解这种状态的消费者。

`|` 的搭档是交叉类型 `&`：同时满足两种结构，适合给现有 payload 增加判别字段而不重复声明所有字段：

```ts
type StoreLoadResult =
  | ({ status: "loaded" } & StoreHead)   // loaded 分支同时拥有 status + head 的全部字段
  | { status: "missing" }
  | StoreReadFailure;
```

注意：互相矛盾的交叉类型会坍缩成 `never`，例如 `{ status: "loaded" } & { status: "missing" }`——类型层面能表达，但永远构造不出值。

### unknown 与 any：外部数据的态度差异

```ts
type JsonObject = Record<string, unknown>;
```

而不是 `Record<string, any>`：

- `any`：编译器放弃检查；
- `unknown`：使用前必须证明它是什么。

```ts
function requiredString(value: unknown, label: string): string {
  if (typeof value !== "string" || !value.trim()) {
    throw new Error(`${label} must be a non-empty string`);
  }
  return value;
}
```

输入是 `unknown`，经过 `typeof value === "string"` 后 TS 才把它收窄为 `string`。但 `params as unknown as TurnJournalInspectionRequest` 这类写法是迁移缝：它告诉编译器“相信我”，并不构成运行时验证，后续应逐步用 typed decoder 或显式 schema parser 替代，不能误以为“用了 TS 就自动安全”。

解码协议中的次数时，应依次检查数值类型、安全整数和业务范围。下面的 `maxCount` 是协议定义的可信上限：

```ts
function decodeCount(value: unknown, maxCount: number): number {
  if (
    typeof value === "number" &&
    Number.isSafeInteger(value) &&
    value >= 0 && value <= maxCount
  ) {
    return value;
  }
  throw new TypeError("invalid count");
}
```

- `typeof` 在运行时排除非数字，同时让编译器把 `unknown` 收窄为 `number`；`&&` 右侧和成功分支都能使用这个结论。
- `Number.isSafeInteger` 排除小数、`NaN`、无穷大和安全整数范围以外的数；它返回普通 `boolean`，不是类型谓词，单独调用不会把 `unknown` 收窄为 `number`。
- 安全整数仍可能是负数或超过协议允许的次数，需要另做范围校验。校验后的静态类型仍是 `number`，不会自动变成“有界整数类型”。

**执行了检查，与类型系统理解了检查结果，是两件事。** 跨语言协议解码既需要真实的运行时验证，也需要编译器能跟踪的类型收窄，不能用 `as number` 替代。参考：[TS 类型收窄](https://www.typescriptlang.org/docs/handbook/2/narrowing.html)、[Number.isSafeInteger](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Number/isSafeInteger)。

### requireExactFields：把 JSON 当版本化协议

TS 的结构类型通常容许变量携带额外字段；对象字面量的多余属性检查和弱类型检测只能拦下一部分情况，不能替代运行时白名单（见 [interface 与结构类型](#interface对象合同与结构类型)）。控制面协议往往要求拒绝未知字段，以发现协议漂移。

```ts
requireExactFields(
  receipt,
  EFFECT_RECEIPT_FIELDS,
  "external capability effect_receipt",
);
```

`requireExactFields` 检查对象是否存在未知字段或缺少字段。对跨语言、跨 provider 的协议很重要：外部系统多返回一个看似无害的字段，可能慢慢形成未定义协议。原则是：

> 把 JSON 当作版本化协议，而不是随意的字典；未知字段在边界处拒绝，而不是悄悄透传。

共享 decoder 时，内部命令全集不应自动成为每个入口的白名单：例如 terminal 入口只接受 `complete / cancel`，mutation 入口只接受 `claim / update`，仍需按入口分别校验。若统一返回宽联合类型，调用方仍看不到 kind 与 command 的对应关系；需要时可用判别联合与重载保留这种关联。命令白名单限定协议范围，具体操作授权仍需独立检查。

### async / Promise：未来才有的值

```ts
export async function commitTurnJournal(
  params: JsonObject,
): Promise<JsonObject> {
  await atomicWriteJson(path, journal);
  return { ok: true, appended: true, effect_id: incomingEffectId };
}
```

`Promise<JsonObject>` 读作：这个函数现在不能立刻给出结果，但未来成功时一定给出一个 `JsonObject`，失败时抛出异常。Node 的网络、文件、进程 API 大量采用异步模型，适合未来的多 Agent control plane；代价是需要避免无界并发和丢失 `await`。

但 `Promise<T>` 只描述 fulfilled 通道的值：它不声明 rejected 通道的异常类型，也不要求调用者必须处理拒绝。`async` 函数甚至可以抛出任意值：

```ts
async function run(): Promise<number> {
  throw "connection lost";
}
```

因此，读异步函数时要同时追踪两条通道：

- 正常兑现：返回值（例如 `AuthorityStoreCommitResult` 中的 `conflict`、`ambiguous`）；
- Promise 拒绝：连接错误、驱动异常、实现缺陷等，标准库的拒绝回调参数也是 `reason: any`。

返回值列全失败状态，不等于异常通道消失。对 `Promise<AuthorityStoreCommitResult>`，LoopX 将 `try/catch` 精确放在可能产生提交副作用的 `store.commitAuthority` 周围：调用已经进入写入边界，异常不能证明“没有写入”，所以恢复成 `status: "ambiguous"`，而不是重试或伪装成明确失败。回执 payload 解码则只把已知的 `AuthorityStoreProtocolError` 转成 typed failure，其他异常继续抛出，避免把程序 bug 包装成存储异常。见 [提交与回执恢复](https://github.com/loopx-project/loopx/blob/709734cd6f8183017b528857bff63b773cdd7ac9/loopx/control_plane/coordination/command_receipt.ts#L59-L89)。

阅读习惯可压缩为一句话：先看返回值和异常分别代表什么，再判断异常发生前是否已经跨过副作用边界。

### Node 调度：async 不等于并行

`async` 让函数返回 Promise，并允许用 `await` 暂停；**不会把其中的同步计算移到后台线程**：

```js
const raw = await readFile(path, "utf8"); // 等待文件期间，可以处理其他工作
const data = JSON.parse(raw);           // 恢复后，在当前 JS 线程同步解析
```

同一事件循环上的 JS 回调需要轮流执行。解析或大循环持续多久，其他请求的 JS 处理就可能被阻塞多久。可在有界的小段工作之间主动让出事件循环：

```ts
import { setImmediate } from "node:timers/promises";

// 每个 Buffer 都是一条完整且大小受限的 JSON 记录。
async function parseRecords(records: readonly Buffer[]): Promise<unknown[]> {
  const values: unknown[] = [];
  let processedBytes = 0;
  for (const record of records) {
    values.push(JSON.parse(record.toString("utf8")));
    processedBytes += record.byteLength;
    if (processedBytes >= 256 * 1024) { // 示例预算，按实际耗时调整
      processedBytes = 0;
      await setImmediate();
    }
  }
  return values;
}
```

这里导入的是 **Promise 版** `setImmediate`：暂停当前函数，等事件循环运行到 check 阶段兑现 Promise 后再续跑。其他就绪的 I/O 回调等因此获得调度机会，但不保证所有请求都先执行。

| 写法 | 暂停后怎样恢复 | 对长循环的作用 |
|---|---|---|
| `await Promise.resolve()` | 后续代码进入微任务队列；事件循环继续处理 I/O 等阶段前，需先清空微任务 | 循环不断追加微任务，仍可能让 I/O 一直等待 |
| `await setImmediate()` | 等待事件循环的 immediate 调度，再恢复后续代码 | 在计算片段之间给事件循环推进的机会 |

这是**协作式让出，提高响应性**，没有减少解析工作量，也没有让计算并行。字节预算只是耗时近似：单条巨大记录、解码或递归冻结仍可能长时间占用线程；单次 `JSON.parse()` 中途无法插入 `await`。也不能随意切开一个 JSON 文档分别解析：需要独立记录或增量解析器；CPU 工作确需并行时再考虑 Worker Threads。

参考：[Node 调度说明](https://nodejs.org/en/learn/asynchronous-work/understanding-setimmediate)、[Promise 版 setImmediate](https://nodejs.org/api/timers.html#timerspromisessetimmediatevalue-options)。

### `return await`：异常处理与 `finally` 的边界

> 参考：[MDN: await](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Operators/await)、[ESLint: no-return-await（v8.46.0 起弃用）](https://eslint.org/docs/latest/rules/no-return-await)。

`return promise` 和 `return await promise` 只差一个 `await`，但改变了**谁来观察这次拒绝**、以及 **`finally` 在什么时刻运行**。

```ts
async function first() {
  try {
    return readProof();        // 返回 Promise 本身
  } catch {
    return { status: "ambiguous" };
  }
}

async function second() {
  try {
    return await readProof();  // 在 try 内等待
  } catch {
    return { status: "ambiguous" };
  }
}
```

- `first`：`catch` 只能捕获调用 `readProof()` 这一刻同步抛出的异常；返回的 Promise 之后发生的拒绝不会进入这个 `catch`，而是直接传播给调用者。
- `second`：在 `try` 内 `await`，异步拒绝也进入本地 `catch`，调用者拿到的是 `{ status: "ambiguous" }`。

涉及资源释放时，差别更直接：

```ts
async function withLock<T>(operation: () => Promise<T>): Promise<T> {
  const lock = await acquireLock();

  try {
    return await operation();  // 不能写成 return operation()
  } finally {
    await releaseLock(lock);
  }
}
```

- `return operation()`：函数立刻把 Promise 交出去，控制流随即进入 `finally` → **锁在操作完成之前就被释放**。
- `return await operation()`：先在锁内等到操作结束（成功或失败），再进入 `finally` 释放锁；顺序是「操作完成 → 释放锁」。

所以 `return await` 的判据不是风格，而是**这次异步结果是否需要被本地的 `try` / `finally` 观察**：

| 位置 | 是否必须 `await` |
|---|---|
| `try { return f() } catch { ... }`，希望异步拒绝被本地转换 | 必须 |
| `try { return f() } finally { ... }`，希望释放发生在其后 | 必须 |
| 单纯透传、外层不关心时序 | 二者等价，可省 |

两个容易过时的印象：

- 「`return await` 会多花一次微任务」是早期引擎的行为；ECMA-262 改过之后不再成立，ESLint 的 `no-return-await` 规则也已在 v8.46.0 弃用（并指出 `return await` 的栈追踪反而更好）。
- 类型系统不会替你补这个 `await`：两种写法都通过 `Promise<T>` 检查，差的是运行时边界。

一句话：`await` 决定异常在哪里被观察、资源在哪里被释放；`return` 只决定值怎么交出去。

### 回调类型不表达时序：`() => void` 也可能是异步的

`() => void` 表达的是**调用方不使用返回值**，不是「这个函数同步执行」；返回其它值的函数本来就可以赋给它（TypeScript 手册写在 [Return Type void](https://www.typescriptlang.org/docs/handbook/2/functions.html#return-type-void) 一节）。

```ts
const hook: () => void = async () => {
  await saveSomething();
};

hook();  // 调用方没有等待，拒绝也没人处理
```

所以把回调标注成 `() => void` 并不能防止异步工作被丢到后台。要建立顺序，必须在**调用点**明确等待：

```ts
type WriteDeps = {
  beforeWrite?: (handle: JsonObject) => void | Promise<void>;
};

await deps.beforeWrite?.(handle);  // 同步返回也能 await
await revalidateAuthority();
await commit();
```

`void | Promise<void>` 是诚实的合同（可以实现成同步，也可以实现成异步），而调用点的 `await` 同时覆盖两种实现；反过来，只把类型写成 `Promise<void>` 却漏掉 `await`，顺序依然没有保证——**合同声明和调用方式要一起成立**。

### 闭包捕获的是对象引用，不是当时的属性值

```ts
const path = source.path;
const digest = source.sha256;

return async () => hash(await readFile(path)) === digest;
```

为什么不直接在回调里读 `source.path`、`source.sha256`？因为闭包持有的是**对象引用**，属性在调用时才被读取：

```ts
const source = { path: "old" };

const readProperty = () => source.path;  // 调用时才读属性
const path = source.path;
const readSnapshot = () => path;         // 捕获的是取出的值

source.path = "new";

readProperty();  // "new"
readSnapshot();  // "old"
```

`const source` 只固定变量绑定，并没有冻结对象。把要用的值提前取出成局部常量，等于给这次判断拍一张快照——即使别处改了请求对象，校验器也不会被悄悄换成「检查另一个文件、另一个摘要」。

类型侧是同一件事的另一面：

```ts
function makeReader(source: { path: unknown }) {
  if (typeof source.path !== "string") throw new Error("invalid");

  return () => source.path.toUpperCase();
  // 报错：回调执行时，这个可变属性未必仍是 string
}
```

收窄只对当前这次读取有效，不会延伸到回调执行的那一刻。提成局部常量可以同时解决两个问题：

```ts
const path = source.path;  // 此处已收窄为 string
return () => path.toUpperCase();
```

- 类型层面：把已经确认的 `string` 交给闭包，而不是让它在未来重新读一个 `unknown` 属性；
- 运行时层面：闭包用的是取出的值，不受之后属性变更影响。

判断规则：闭包要长期持有一个「已校验」的值，就在收窄处取出来（`const local = obj.prop`），不要在闭包里反复写 `obj.prop`。这和 [TS 不会自动解决什么](#ts-不会自动解决什么)里的 TOCTOU 是同一主题——校验的时点和使用的时点之间，状态可能已经变了。

### 索引访问类型：直接引用权威字段

不想手写第二份类型时，可以直接“按字段取类型”：

```ts
receipts: SettlementResult<unknown>["receipts"]
```

它不是重新声明 `receipts: readonly SettlementReceipt[]`，而是引用 `SettlementResult` 里 `receipts` 字段的权威类型。收益：以后 `SettlementResult.receipts` 的只读性或结构变化，这里自动同步，不会形成第二份类型知识。与数组上的 `[number]`（取元素类型）是同一套 indexed access 机制，只是把下标换成字段名。

### Pick 与 Partial：限制依赖和构造自由度

`Pick<T, K>` 从 `T` 中挑出 `K` 指定的键，构造一个新的对象类型；它是**纯编译期**操作——不拷贝、也不删除任何运行时字段。它同时承担两个作用：声明函数依赖哪些事实，以及限制构造器允许设置哪些字段。

```ts
type CheckInput = Pick<Request, "resource" | "actorId" | "expectedVersion">;
type ResultOptions = Partial<Pick<Result, "retryable" | "nextState">>;
```

`Pick<T, K>` 选取字段，也声明函数允许依赖哪些事实：接收 `CheckInput` 的函数不能在正常类型检查下读取完整请求中的其他字段。TS 使用结构类型，已有完整请求对象仍可合法传入；`Pick` 不会删除运行时字段，裁剪或脱敏需要显式构造新对象。

`Partial<Pick<…>>` 先选出可调字段，再将其变为可选，适合构造器的 options：

```ts
function makeResult(
  outcome: Result["outcome"],
  code: string,
  options: ResultOptions = {},
): Result {
  return {
    retryable: false, nextState: null, ...options,
    schemaVersion: 1, outcome, code,
  };
}
```

相较 `Partial<Result>`，调用方不会获得 outcome、code 等字段的第二个设置入口；固定字段放在展开之后，也避免运行时额外同名字段覆盖它们。需要严格白名单时仍应逐字段构造。受限 options 只能减少自由度，不能自动排除“失败结果带成功状态”等组合；可用结果判别联合或专门的成功 / 失败构造器进一步约束。

### 内置 `Omit` 作用在联合类型上会丢分支

`Omit<T, K>` 的定义是 `Pick<T, Exclude<keyof T, K>>`，而 `keyof (A | B)` 只保留**各成员共有的键**。所以直接对联合类型用 `Omit`，会把分支专属字段一起丢掉：

```ts
type Effect =
  | { kind: "validate"; command: string; trace: string }
  | { kind: "commit"; revision: string; trace: string };

type Collapsed = Omit<Effect, "trace">;
// 期望：{ kind: "validate"; command: string } | { kind: "commit"; revision: string }
// 实际：{ kind: "validate" | "commit" }——command / revision 都不见了
```

要让 `Omit` 分别作用于每个分支，用分配式条件类型（裸类型参数放在 `extends` 左边会触发分配律）：

```ts
type DistributiveOmit<T, K extends PropertyKey> =
  T extends unknown ? Omit<T, K> : never;

type Preserved = DistributiveOmit<Effect, "trace">;
// { kind: "validate"; command: string }
// | { kind: "commit"; revision: string }
```

对用判别联合描述 effect / state 的协议，这一点很关键：`kind` 必须和它对应的 payload 一起被收窄，丢字段等于丢掉了「这个分支能做什么」的信息。反过来，从单个 interface 上 `Pick` / `Omit` 字段（如 `Pick<EditInput, "patch" | "clearFields">`）不存在这个问题，不必为此引入新泛型工具。

### 模块边界：只导出稳定协议联合

```ts
type TurnSettlementExecution = ...; // 内部实现
type TurnSettlementOutcome = ...;   // 内部实现

export type TurnSettlementReduction =
  | TurnSettlementExecution
  | TurnSettlementOutcome;
```

外部只依赖导出的协议联合，内部的具体类型不暴露：

- 外部依赖一个稳定的契约，内部可自由重构 helper / 拆分结构；
- 不把每个临时实现类型都变成公共 API——TS 项目很容易因为“导出很方便”把所有内部 DTO 暴露，最后任何重构都变成 breaking change。

判断标准：能成为公共 API 的是“别人要依赖的形状”，内部字段、临时 helper、演进中的结构都留在模块里。

### 错误分层：typed failure 与 invariant violation

可预期的业务失败作为结果返回，理论上不应到达的状态直接抛异常：

```ts
// 业务失败：调用方需要处理，走正常返回
return settlementFailed({ kind: "receipt_missing", ... });

// 不变量违背：实现或协议出现矛盾，不应该伪装成业务失败继续跑
throw new Error(
  `failed_provider_attempt for ${stepKind} unexpectedly committed`,
);
```

两者语义不同：

- typed failure：系统知道这类失败如何进入 receipt、projection 和恢复流程；
- exception：表示状态机或协议本身出了 bug，继续“优雅包装”只会掩盖问题。

控制面代码里把所有异常都转成优雅结果反而危险：它把实现矛盾当成普通业务失败，等 bug 被吞掉后，错误会以更难查的形式冒出来。

异常是否能恢复取决于边界：effect adapter 可以在“副作用可能已发生、响应丢失”的窗口把外部 I/O 异常转成 `ambiguous`；协议解码只转换已知错误；未知异常仍应暴露。

## 类型进阶：谓词、资源边界与序列化安全

### 用户定义类型谓词 + const type parameter：从白名单到精确类型

```ts
function isStringLiteral<const Values extends readonly string[]>(
  value: string,
  allowed: Values,
): value is Values[number]
```

拆解三件事：

- `const Values` 尽量保留调用方数组的字面量 tuple 信息（精确成员集合）；
- `value is Values[number]` 是**用户定义类型谓词（type predicate）**：告诉 TS「这个函数返回 true 时，`value` 就是这个联合」；
- runtime 真的执行 membership check（不是假装通过）。

因此 `requireStringLiteral(value, QUOTA_SPEND_SOURCES, ...)` 同时完成两件事：运行时白名单校验 + 返回精确的 `QuotaSpendSource`，没有任何不受验证的 `as QuotaSpendSource`——类型收窄来自真实的运行时证据。谓词 = 可执行的真值函数 + 类型契约。

**TS 5.5 起可自动推断部分类型谓词**，使 `filter` 的结果随之收窄（开启 `strictNullChecks`）：

```ts
const values: (string | undefined)[] = ["todo_next", undefined];
const ids = values.filter(value => value !== undefined); // string[]
// 回调自动推断为 (value: string | undefined) => value is string
```

推断要求：无显式返回类型、只有一个返回且无隐式返回、不修改参数，返回与参数收窄相关的布尔表达式。给回调标 `: boolean` 会阻止本例的谓词推断；`!!value` 也不能在这里替代 `value !== undefined`，因为它还会排除空字符串，返回 `false` 不代表值一定是 `undefined`。参考：[TS 5.5 — Inferred Type Predicates](https://www.typescriptlang.org/docs/handbook/release-notes/typescript-5-5.html#inferred-type-predicates)。

### `asserts`：把检查结果传给后续代码

断言签名告诉 TS：**函数正常返回，所断言的条件就成立**。例如 `assert.ok` 的简化声明：

```ts
declare function ok(value: unknown): asserts value;
```

在测试辅助函数内：

```ts
const result = await store.loadAuthority();
assert.ok(result.status === "loaded");
return result; // 已收窄到 loaded 分支
```

类型谓词在返回 `true` 的分支收窄；断言函数在正常返回后收窄。普通返回 `void` 的检查函数通常不能向调用者传递这条类型事实。`asserts` 签名本身不生成检查逻辑，自定义实现必须在条件不成立时抛错，不能只靠签名保证正确。参考：[TypeScript Assertion Functions](https://www.typescriptlang.org/docs/handbook/release-notes/typescript-3-7.html#assertion-functions)。

### 泛型高阶函数：对返回值透明的资源边界

```ts
async function withFileMutationLock<T>(
  targetPath: string,
  operation: () => Promise<T>,
): Promise<T>
```

它不关心 `operation` 返回什么，只增加一个控制面性质：该 operation 在锁内串行执行。调用者仍得到原始的精确返回类型：

```ts
return await withFileMutationLock(indexPath, async () => {
  return QuotaSpendCommitResult;
});
```

这是 **resource-scoped combinator**：把 acquire / release / finally 固化在一个边界中，业务函数无法「忘记解锁」，同时 `T` 透传、不污染业务返回类型。

这里的 `return await` 不能省：它决定 `finally` 在操作完成之前还是之后运行，机制见 [`return await`：异常处理与 `finally` 的边界](#return-await异常处理与-finally-的边界)。

### 错误码的运行时收窄：instanceof + in（而不是 as）

```ts
// 脆弱：开发者承诺
(error as NodeJS.ErrnoException).code === "ENOENT"

// 稳健：运行时建立证据
error instanceof Error && "code" in error && error.code === code
```

现代 TS 中 `catch (error)` 应视为 `unknown`：第一种写法是「相信我它有 `.code`」的承诺；第二种逐步建立证据——先确认是 Error，再确认存在 `code` 字段，最后比较值。通用 helper 推荐第二种：它更适合未来把非 Node 异常或测试 double 送进来时 fail closed，而不是因为「某个对象恰好有 `code` 但语义不同」而误判。

### canonical JSON：稳定序列化 ≠ JSON.stringify

```ts
{ a: 1, b: 2 }
{ b: 2, a: 1 }
```

语义相同，但 insertion order 不同可能得到不同字符串——`request_digest` 这类 hash 用途不能直接 hash 普通对象。本 PR 用递归 `stableValue()`：数组保留顺序、对象 key 排序、`Object.fromEntries()` 重建、再 `JSON.stringify()` + SHA-256。

它只是项目内 canonicalization，不是完整标准 Canonical JSON（如 RFC 8785）：

- `undefined` / 函数 / `NaN` / `Infinity` 有特殊序列化行为；
- `BigInt` 会抛错；
- 循环引用无法处理；
- 键排序必须遵守选定协议：`localeCompare` 是地区排序，不能代替明确的码元 / 码点规则；[RFC 8785 §3.2.3](https://www.rfc-editor.org/rfc/rfc8785#section-3.2.3) 指定 UTF-16 码元顺序，并非 Python 字符串的码点顺序。两种次序的差异见 [跨语言排序](#filter--sort先副本再排序)。

当前主要安全来源是请求先经过 JSON RPC；未来 Stage 3 进程内直接调用 TS kernel 后，不能默认「类型是 `JsonObject` 就一定可以稳定 JSON 化」。

### Record<string, unknown> ≠ JSON-safe object

```ts
type JsonObject = Record<string, unknown>; // 只表示：字符串键 → 任意未知值
const commit = { ... } satisfies JsonObject; // 只能证明结构可赋值
```

`Record<string, unknown>` 不保证值可被 JSON 序列化——bigint、function、undefined、class instance、cycle 都可能混进来。`satisfies JsonObject` 只是「宽类型可赋值」检查，很容易制造错误安全感。控制面真正的安全合同来自 runtime decoder、RPC serialization 和 domain invariant，而不是 `JsonObject` 这个名字（呼应「unknown 与 any」「requireExactFields」）。

### `ReturnType<typeof fn>`：从实现派生类型，避免类型知识重复

```ts
let expectedRevision: ReturnType<typeof parseRevision>;
```

不手写 `{ store_identity: string; revision: string } | null` 这种第二份返回类型，而是直接取解析函数的返回类型。以后 parser 返回结构变化，变量类型自动同步。

这是「类型知识单一来源」的延续：parser 已经是权威，就不要再维护第二份返回类型（和「索引访问类型」「用户定义类型谓词」同一思路）。

工具类型可以从内向外组合，直接派生异步接口的成功分支：

```ts
type Loaded = Extract<
  Awaited<ReturnType<Store["load"]>>,
  { status: "loaded" }
>;
```

`Store["load"]` 取方法类型，`ReturnType` 取返回类型，`Awaited` 取 await 后的结果，`Extract` 保留可赋值给 `{ status: "loaded" }` 的联合成员。接收 `Loaded` 的提交函数只接受已加载分支，字段随上游接口演进，无需重复手写。前提是上游返回类型已用字面量 status 区分分支；这不会替代运行时加载检查。

### `import type`：类型导入在运行时被擦除

```ts
import type { Store, StoreCommit } from "./store.ts";
```

`import type` 只供 `tsc` 检查，运行时会被擦除。它避免三件事：

- 只引用 interface，却产生不必要的 runtime import；
- ESM 循环依赖；
- Node 在运行时加载一个本不需要的模块。

配合 type-strip 执行的配置：

```json
{
  "module": "NodeNext",
  "moduleResolution": "NodeNext",
  "allowImportingTsExtensions": true,
  "noEmit": true
}
```

含义：TypeScript 只做检查、不生成 JS，Node 直接 type-strip 执行 `.ts`，所以源码 import 可以显式写 `.ts` 后缀。

### 内部 BigInt、协议边界 string：跨 JSON 的三段转换

数据库 cursor / revision 可能超过 JS 安全整数范围（`Number` 最大安全整数 `2^53 - 1`），所以：

```ts
const parsed = BigInt(cursor);
const next = (parsed + 1n).toString();
```

完整链路：

```text
PostgreSQL bigint
  → SQL ::text
  → TypeScript BigInt 做比较和加法
  → decimal string 进入 JSON / provider token
```

不能直接把 TS `bigint` 塞进 JSON：`JSON.stringify({ cursor: 1n })` 会抛异常。模式是**内部用 BigInt 做数学，协议边界一律 string**（呼应「canonical JSON」里 BigInt 不是 JSON-safe——这里补上完整用法）。

### 非空断言 `!`：承诺不是校验

```ts
const match = PATTERN.exec(value);
if (!match) throw new Error(...);

return {
  store_identity: `postgresql:${match[1]!}`,
  revision: match[2]!,
};
```

`match[1]!` 的意思是「我向编译器保证这里不是 undefined」——它**不生成任何运行时检查**。这里之所以安全，是因为前面已经检查 `match` 非空、且正则拥有固定的两个捕获组。

`!` 应只用在编译器无法追踪、但程序已经有明确运行时证明的地方；滥用它和滥用 `as` 一样，都是在绕过类型系统（见「错误码的运行时收窄」）。

### tsconfig 的 `strict` 不等于「全部严格检查」

> 参考：[tsconfig: noUncheckedIndexedAccess](https://www.typescriptlang.org/tsconfig/#noUncheckedIndexedAccess)、[tsconfig: exactOptionalPropertyTypes](https://www.typescriptlang.org/tsconfig/#exactOptionalPropertyTypes)。

`strict: true` 打开的是一组固定开关，另有若干严格检查必须单独开启。两个常用的：

```jsonc
{
  "compilerOptions": {
    "strict": true,
    "noUncheckedIndexedAccess": true,
    "exactOptionalPropertyTypes": true
  }
}
```

**`noUncheckedIndexedAccess`**：让数组与索引签名的读取体现「可能不存在」。

```ts
const items: Item[] = [];
const first = items[0];
// 关闭时：Item
// 开启时：Item | undefined
```

它对回执数组、按 id 建立的冲突索引这类代码很有价值。但它只说明「这个位置可能没有值」，不证明下标与内容对应正确——业务边界仍然要自己校验。

**`exactOptionalPropertyTypes`**：区分「属性缺席」与「属性存在但值显式是 `undefined`」。

```ts
type Options = { ttl?: number };

const a: Options = {};                  // 合法
const b: Options = { ttl: undefined };  // 开启后不合法
```

这与更新协议直接相关：`"ttl" in options` 能区分这两种对象，而直接读 `options.ttl` 在两种情况下都可能是 `undefined`。如果合同确实允许显式 `undefined`，要写成 `{ ttl?: number | undefined }`。

开启这些开关不是「顺手加一行」：新增的 `undefined` 分支要逐处确认真实语义（是缺失、是显式清空，还是实现 bug），否则只是把问题从运行时挪到一份很长的编译错误清单里。

### 接口方法 vs 函数属性：参数检查不是同一套规则

同一份实现，写成「方法简写」和写成「函数属性」，参数兼容性的检查强度并不一样——这是 `strictFunctionTypes` 留下的一处例外：

```ts
interface MethodHook {
  authenticate(value: unknown): boolean;
}

const hook: MethodHook = {
  authenticate(value: string) {          // 允许
    return value.startsWith("token-");
  },
};

hook.authenticate(42);                   // 编译通过，但运行时会崩
```

接口承诺「任何值都能传」，实现却只处理 `string`，编译器仍然接受——因为**方法语法保留了参数双变（bivariance）检查**：只要两个参数类型互相可赋值其一，就算兼容。

把同一个接口改成函数属性，实现就会被拒绝：

```ts
interface FunctionHook {
  authenticate: (value: unknown) => boolean;
}

const hook: FunctionHook = {
  authenticate: (value: string) => value.startsWith("token-"),
  // 报错：string 处理不了任意 unknown
};
```

直觉：接口说「你可以传任何值」，实现就不能只接受字符串——参数位置要求**逆变**，实现的输入至少要能和目标一样宽。

工程含义：

- **外部会拿任意输入调用你的边界**（回调、认证函数、插件 handler、事件订阅）优先用函数属性语法，让 `strictFunctionTypes` 挡掉参数收窄；
- 方法语法适合「调用方是同一抽象内部的代码、参数由该抽象自己保证」的场景；
- 读到「实现明显只处理一种输入，却依然编译通过」的接口时，先确认它是方法简写还是函数属性——`strictFunctionTypes` 的收紧只作用于函数类型位置，方法被有意排除在外。

> 参考：[TypeScript Handbook: Function Parameter Bivariance](https://www.typescriptlang.org/docs/handbook/type-compatibility.html#function-parameter-bivariance)、[tsconfig: strictFunctionTypes](https://www.typescriptlang.org/tsconfig/#strictFunctionTypes)。

### 静态形状 vs 行为合同：conformance suite 证明语义

```ts
interface Store {
  load(): Promise<...>;
  commit(...): Promise<...>;
  readReceipt(...): Promise<...>;
}
```

File 和 Database 都能 `implements Store`，只说明方法签名一致；编译器无法证明它们都满足：

- CAS 只能一个 writer 成功；
- state / event / receipt 原子提交；
- 历史 receipt 可重放；
- cursor 有序；
- 返回结果不会泄漏内部引用。

做法是用 typed factory 为每个 provider 注册同一套 conformance tests：

```ts
registerStoreConformance("Database provider", async () => ({ store, contender }));
```

核心认识：

> TypeScript interface 是静态形状合同；分布式存储的行为合同必须由共享 conformance suite 和真实 backend 测试证明。

## 表达式、数组方法与箭头函数

### `some` + `includes` + 箭头函数：存在性谓词、取反与短路

真实写法（settle_completion 的 gate 检查）：

```ts
if (
  completed.completion_continuation === "successor" &&
  completed.successor_todo_ids.some(
    (todoId) => !request.materialized_todo_ids.includes(todoId),
  )
) {
  return unchangedResult(
    "settle_completion",
    "awaiting_successor",
    request.lines,
  );
}
```

从里到外拆解：

```text
request.materialized_todo_ids.includes(todoId)
    → 已物化列表里是否包含这个 todoId（返回 boolean）

!request.materialized_todo_ids.includes(todoId)
    → 取反：这个 todoId 尚未被物化

completed.successor_todo_ids.some((todoId) => !...includes(todoId))
    → 对 successor_todo_ids 逐元素调用箭头函数
    → 只要「存在一个」尚未物化的 todoId，整体就是 true
```

整句读法：

> successor_todo_ids 里存在至少一个不在 materialized_todo_ids 中的 id。

`.some()` 是数组的存在性谓词：对每个元素执行传入的函数，任一元素返回 `true` 就立即返回 `true`（短路，不再遍历）；空数组返回 `false`。箭头函数 `(todoId) => ...` 是匿名函数，`todoId` 是当前元素，函数体返回 boolean。

等价 Python 写法：

```python
any(
    todo_id not in request.materialized_todo_ids
    for todo_id in completed.successor_todo_ids
)
```

对照表：

| TS | 含义 | Python 对应 |
|---|---|---|
| `arr.some(fn)` | 存在一个元素满足谓词 | `any(fn(x) for x in arr)` |
| `arr.every(fn)` | 所有元素都满足谓词 | `all(fn(x) for x in arr)` |
| `arr.includes(x)` | 数组是否包含 x | `x in arr` |
| `!arr.includes(x)` | 数组是否不包含 x | `x not in arr` |

常见坑：

- 空数组的语义相反：`some` 返回 `false`，`every` 返回 `true`——写 gate 条件时要先想清楚“空列表应该放行还是停留”；
- `includes` 用 SameValueZero 比较，能正确识别 `NaN`；`indexOf` 用严格相等，`NaN` 永远找不到；
- `some` / `every` 都会短路，谓词里不要写有副作用、且依赖“全部元素都被访问”的代码。

这个片段也是状态机的典型写法：continuation 是 `"successor"` 但还有 successor 未物化时，不推进结算，而是返回 `unchangedResult("awaiting_successor")`——条件不满足就幂等停留，避免提前结算或重复副作用。

### filter + sort：先副本，再排序

选择下一个可执行 Todo 的典型写法：

```ts
const candidates = todos.filter((todo) =>
  todo.status === "open" &&
  !CONTROL_TASK_CLASSES.has(todo.task_class ?? ""),
);

candidates.sort((left, right) => {
  const leftClass = left.task_class === "advancement_task" ? 0 : 1;
  const rightClass = right.task_class === "advancement_task" ? 0 : 1;

  return leftClass - rightClass ||
    priorityRank(left.text) - priorityRank(right.text) ||
    left.index - right.index;
});
```

关键细节：

- `filter` 创建新数组，所以后续 `sort` 修改的是副本，不会污染调用者传进来的 `readonly todos`；如果直接对 `todos.sort(...)`，即使类型写了 `readonly`，实现也会破坏原数组；
- 多条件排序用 `||` 串联比较结果：第一个非零差值决定顺序（first diff wins）；
- `advancement task` 优先于监控、用户 gate、阻塞类控制任务，再按 `[P0]` 到 `[P4]`、最后按原始 index 排序。

**元素可以是 `bigint`，比较器返回值仍应是 `number`。** `Array<T>.sort` 的 TS 比较器合同是 `(a: T, b: T) => number`；排序只需要负数、零、正数表达前后关系，不需要精确差值。

```ts
const instants: bigint[] = [9007199254740993n, 9007199254740992n];

// 错误：a - b 返回 bigint，TS 不接受
instants.sort((a, b) => a - b);

// 正确：精确比较 bigint，返回 number；这里是降序
instants.sort((a, b) => a > b ? -1 : a < b ? 1 : 0);
```

前一种写法在 JS 中也有问题：比较器被调用后，排序算法会对返回值执行 `ToNumber`，而 `bigint` 会触发 `TypeError`。后一种直接比较原始整数，可保留以 `bigint` 存储的微秒时间戳精度；排序结果只需用 `-1 / 0 / 1` 表示。参考：[ECMAScript — CompareArrayElements](https://tc39.es/ecma262/multipage/indexed-collections.html#sec-comparearrayelements)。

**跨语言“字符串排序”未必相同。** JavaScript 字符串的 `<` 按 UTF-16 码元做字典序比较，Python `str` 按 Unicode 码点；ASCII 样本看不出差异，补充平面字符则可能改变顺序：

```js
"\u{10000}" < "\uE000"; // true
// U+10000 在 UTF-16 中是 D800 DC00，首码元 D800 < E000
```

```python
"\U00010000" < "\uE000"  # False：码点 0x10000 > 0xE000
```

迁移事件 / ID 排序时应保留协议规定的顺序：若要兼容 Python，就用统一的码点字典序比较器，逐码点比较，公共前缀相同时较短字符串在前，并用补充平面字符覆盖回归。不能直接复用 JS 的 `<`，也不能任意换成 `localeCompare`：地区排序语义不同，还可能受 locale、选项与实现版本影响。码点顺序也不是所有协议的默认正确答案，须以具体合同为准。

参考：[ECMAScript — IsLessThan](https://tc39.es/ecma262/multipage/abstract-operations.html#sec-islessthan)、[Python — Value comparisons](https://docs.python.org/3/reference/expressions.html#value-comparisons)。

### map + filter：位置属于来源快照

**需要把筛选结果交回原数组处理时，应先保留来源位置，再过滤或排序。** `ordinal` 意为序号，这里特指从 0 开始的原始数组下标，不是筛选结果的新排名，也不是元素的永久 ID。

```ts
const source = ["A", "B", "C"];

const selected = source
  .map((item, ordinal) => ({ item, ordinal }))
  .filter(({ item }) => item === "C");
// [{ item: "C", ordinal: 2 }]

const renumbered = source
  .filter(item => item === "C")
  .map((item, ordinal) => ({ item, ordinal }));
// [{ item: "C", ordinal: 0 }]；这个 0 用于 source[0] 会取到 "A"
```

**`ordinal` 从哪里来，要区分值的传入与类型推断。** JavaScript 的 `map` 调用回调时依次传入当前元素、它在被遍历数组中的下标、该数组；第二个参数可以任意命名为 `index`、`i` 或 `ordinal`，名称不改变行为。上述第一段遍历的是 `source`，因此处理 `"C"` 时收到 `2`；第二段遍历的是过滤后的 `["C"]`，因此收到 `0`。

TypeScript 则根据 `map` 的声明对回调做**上下文类型推断**。简化声明为：

```ts
interface Array<T> {
  map<U>(callback: (value: T, index: number, array: T[]) => U): U[];
}
```

`source` 是 `string[]`，因此 `T = string`，`item` 被推断为 `string`、`ordinal` 为 `number`；`({ item, ordinal })` 是返回对象的箭头函数，属性简写等价于 `{ item: item, ordinal: ordinal }`，进而推断 `U` 为 `{ item: string; ordinal: number }`。TS 没有自动生成名为 `ordinal` 的变量，也没有把它推断为“这个元素在这份快照里的合法位置”。`filter` 只保留符合条件的元素，不会重写对象里已经保存的 `ordinal`。

**类型正确不代表来源正确。** 普通 `number` 不关联具体数组或快照，`noUncheckedIndexedAccess` 也只能提示可能越界，不能识别“合法下标取错元素”。跨语言 / 进程返回这些位置时，应检查它们是合法整数、在来源数组范围内、属于此次选中集合，并按合同检查重复与元素身份对应；来源可能变化时还要绑定并核对 `snapshot_id / revision`。保存 ordinal 不会冻结数组：原数组发生插入、删除或重排后，旧位置可能失效；跨快照追踪元素应使用稳定 ID，位置另行解析。

参考：[MDN — `map` 回调参数](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Array/map#parameters)、[TypeScript — Contextual Typing](https://www.typescriptlang.org/docs/handbook/type-inference.html#contextual-typing)。

### Map：首次插入顺序与分组

`Map` 按键的首次插入顺序遍历；更新已有键不会把它移到末尾，删除后重新插入则算新插入。这个顺序可以成为算法语义：按任务原顺序遍历，首次遇到领取者时建立分组，再按组的插入顺序分配展示位置，最后按事先保存的 `ordinal` 恢复任务原顺序。分组展示顺序与任务来源顺序是两个维度。

```js
const groups = new Map();
groups.set("10", "先加入");
groups.set("2", "后加入");
groups.set("10", "更新已有组");
[...groups.keys()]; // ["10", "2"]

Object.keys({ "10": "先加入", "2": "后加入" });
// ["2", "10"]：普通对象的数组索引式字符串键按数值升序枚举
```

Python 字典保持插入顺序；迁到 TS 时，不能只看两边都像“键值表”，还要检查是否依赖遍历顺序。普通对象也有确定的键枚举规则，但不等同于 `Map` 的插入顺序。参考：[MDN — Map](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Map)、[Python — dict](https://docs.python.org/3/library/stdtypes.html#mapping-types-dict)。

### Set 与 `??`：成员判断与空值回退

```ts
const CONTROL_TASK_CLASSES = new Set([
  "continuous_monitor",
  "user_gate",
  "blocker",
]);

... !CONTROL_TASK_CLASSES.has(todo.task_class ?? "")
```

`Set.has()` 是 O(1) 成员判断，也比 `includes` 更直接地表达“这是语义化黑名单”。`task_class ?? ""` 表示 `null` / `undefined` 时回退到空字符串（`??` 只回退 nullish，不覆盖 `0`、`false` 这类 falsy 值），让 `has("")` 自然返回 false——未分类的 Todo 不会被误判为控制任务。

### `===` 与 `==`：严格相等与类型收窄

```ts
"1" == 1    // true：宽松相等会先做类型转换
"1" === 1   // false：严格相等要求值和类型都相同
```

JavaScript 有两种相等比较：

- `===`（严格相等）：不转换类型，值和类型都相同才返回 `true`；
- `==`（宽松相等）：先做复杂的隐式转换再比较，是经典 bug 来源。

| 表达式 | 结果 | 原因 |
|---|---|---|
| `"1" == 1` | true | 宽松相等把字符串转成数字 |
| `"1" === 1` | false | 类型不同 |
| `0 == ""` | true | 都隐式转成 0 |
| `0 == false` | true | false 转成 0 |
| `"" == false` | true | 都转成 0 |
| `null == undefined` | true | 宽松相等的特殊规则 |
| `null === undefined` | false | 类型不同 |
| `NaN === NaN` | false | NaN 不等于任何值（包括自己） |
| `[] == false` | true | 空数组先转 `""` 再转 0 |
| `[] === []` | false | 对象按引用比较，两个空数组不是同一个引用 |

要点：

- 对象 / 数组按引用比较：`[] === []` 为 false，`const x = []; x === x` 才为 true；
- 判断 NaN 用 `Number.isNaN(value)` 或 `Object.is(value, NaN)`，不要用 `===`；
- `Object.is()` 与 `===` 几乎一致，两个区别：`Object.is(NaN, NaN)` 为 true、`Object.is(+0, -0)` 为 false；
- 唯一值得用的 `==` 惯用法是 `value == null`：同时匹配 `null` 和 `undefined`（`===` 做不到，必须写 `value === null || value === undefined`）。

TypeScript 语境：`===` 是类型收窄的触发器。判别联合里写 `if (action.decision === "execute")` 之后，TS 会把 `action` 自动收窄到该分支（呼应“判别联合与 never”）；`switch` 的 `case` 比较同样是严格相等语义。

速记：

> 写比较默认用 `===`；只有明确想同时匹配 null / undefined 时才用 `== null`。

### 对象展开：覆盖顺序与阶段升级

```ts
return checked.outcome === "apply"
  ? { ...checked, code: "transition", nextStatus: "done" }
  : checked;
```

后写字段覆盖先写字段。外层在检查通过后继承内层证据，并明确增加状态转移；反过来写 `{ nextStatus: "done", ...checked }`，可能被旧值覆盖。展开是浅拷贝，嵌套对象仍共享引用。检查这种代码时，要看继承了什么、覆盖了什么、是否带入不属于当前阶段的字段；展开语法本身不证明业务转换合法。

## 状态机建模：让非法状态无法构造

核心原则：

> 不只给字段标类型，还要让非法状态无法构造。

### 案例：settlement 双重 binding

一个 settlement 只能绑定一个 todo、一个 autonomous replan obligation，或者保持 unbound；不能同时绑定 todo 和 replan。当前代码在运行时拦截：

```ts
if (todoId && replanObligationId) {
  throw new Error(
    "settlement identity cannot bind both todo_id and replan_obligation_id",
  );
}
```

更进一步，可以把输入直接建模为联合类型，让“双重 binding”甚至不能被构造出来：

```ts
type SettlementBinding =
  | { kind: "todo"; todo_id: string }
  | { kind: "autonomous_replan"; obligation_id: string }
  | { kind: "unbound" };
```

### 案例：SettlementResult 的成功 / 失败判别联合

原接口理论上允许 `value` 和 `failure` 同时存在；更强的表达：

```ts
type SettlementResult<T> =
  | {
      ok: true;
      value: T;
      failure: null;
      receipts: readonly SettlementReceipt[];
    }
  | {
      ok: false;
      value: null;
      failure: SettlementFailure;
      receipts: readonly SettlementReceipt[];
    };
```

成功值和失败同时出现，在类型层就无法表达。

### 案例：完成 Todo 的顺序与 successor fence

真实流程（Todo 完成 → Next Action 重投影）必须按固定顺序：

```text
标记旧 Todo 为 done
  → 创建并物化 successor Todo
  → 把 successor ID 写回旧 Todo 的 lineage
  → 重投影 Next Action
  → 统一写回 state 文件
```

顺序很重要：如果先重投影 Next Action、后创建 successor，可能出现“旧 Todo 已完成、新 Todo 还不存在、Next Action 被清空”。因此引入 successor fence——所有声明的 successor 都 materialize 之后，才允许切换 Next Action（对应上一节的 `some` + `includes` 片段）：

```ts
if (
  completed.completion_continuation === "successor" &&
  completed.successor_todo_ids.some(
    (todoId) => !request.materialized_todo_ids.includes(todoId),
  )
) {
  return unchangedResult(
    "settle_completion",
    "awaiting_successor",
    request.lines,
  );
}
```

这是状态机的通用思想：

> 只有满足前置不变量，才允许进入下一状态；条件不满足时返回“未变化”，而不是强行推进。

### 状态与字段的交叉约束：类型表达不了，就放边界校验

字面量联合能限定状态集合：

```ts
type ProviderStatus = "running" | "succeeded" | "no_change";
type SettlementStatus = "running" | "ready_to_settle";
```

比 `status: string` 强：非法状态在边界处就被拒绝。

仅靠两个独立的状态联合，还没有表达状态与字段的关联：

- `running` 不能有 receipt；
- `running` 不能带 mutation；
- `succeeded` 必须对应 committed receipt；
- `no_change` 必须对应 no_change receipt，且不能带 mutation。

这些字段关联可以进一步写成判别联合；外部输入仍需在边界校验，receipt 是否真实提交等事实还需查询权威状态。类型约束对象形态，运行时验证输入与业务事实。

### 更新意图：keep / clear / set

`string | null` 表达数据值，无法单独区分“不修改”和“明确清空”。PATCH API、配置继承、数据库更新可显式建模操作意图：

```ts
type Change<T> =
  | { kind: "keep" }
  | { kind: "clear" }
  | { kind: "set"; value: T };

function applyChange<T>(current: T | null, change: Change<T>): T | null {
  switch (change.kind) {
    case "keep": return current;
    case "clear": return null;
    case "set": return change.value;
  }
}
```

也可约定“字段缺省表示保持、null 表示清空、具体值表示设置”，但 decoder 必须保留缺省与 null 的区别；提前使用 `??` 回退可能吞掉清空意图。判别联合适合替代多组 boolean + nullable 字段，减少互相矛盾的组合。

## Effect Program 与语义内核

### Effect Program 是什么

```text
读取当前状态
    ↓
判断下一项可执行 effect
    ↓
执行 effect
    ↓
获得 typed receipt 或 typed failure
    ↓
reduce 成新状态
    ↓
可重放地判断下一步
```

在 LoopX 里，effect 不是泛指“函数调用”，而是具备业务意义、可观察的动作：validation、durable writeback、quota spend、terminal closeout、Turn journal 原子写入。基础结构是：

```text
输入 Request
  → 解释 Interpretation
  → 得到 Observation/Decision
  → 生成 Next Effect
```

`EffectTurn` 接口由 `request / interpretation / observation / next_effect` 组成。LoopX 本质不是脚本集合，而是长程 Agent 的语义状态机，因此这个抽象很贴合。

### PR-1 是纵向迁移，不是翻译

```text
Python CLI / Control Plane
  → Python transition adapter
  → loopback JSON RPC
  → Managed TS Effect Runtime
  → Typed handler registry
  → effect_program.ts / turn_journal.ts / turn_journal_effects.ts
  → Typed result / receipt / failure
```

关键文件（名称保留，路径脱敏）：

- TS 语义核心：`effect_program.ts`；
- RPC 方法注册：`effect_runtime_handlers.ts`；
- 常驻进程与传输：`effect_runtime_server.ts`；
- Python 迁移桥：`effect_runtime.py`；
- Turn journal 规则：`turn_driver/turn_journal.ts`；
- TS 原生副作用：`turn_driver/turn_journal_effects.ts`。

这里不是“每迁一个模块，就造一个 server”，而是：

> 一个 TS control-plane runtime，内部用一个 typed method registry 承载多个逐步迁入的 bounded context。

以后迁移 todo、quota、replan 等域，继续注册到同一个 runtime，而不是分别启动多个 Node 服务。

### 终局形态

这个 server 是迁移桥，不一定是终局：

- **CLI-only 形态**：LoopX CLI 和 control-plane 主体都迁到 TS 后，同进程直接 import TS kernel，Python→TS RPC bridge 可以删除；
- **App / 多进程共享权威形态**：如果未来需要多 CLI 并发、App 与 CLI 共享状态、多 Agent 跨进程协作、watcher / scheduler 常驻，仍可能保留一个可选的 control-plane daemon。

最终删除的是“因为 Python→TS 迁移而存在的桥”，不一定删除所有长期有价值的共享 runtime。

### 规则所有权 vs 副作用执行位置

迁移中必须区分两个概念：

- 哪一步可执行、receipt 是否齐全、phase 是否合法：TS 拥有；
- 某些遗留 writeback / spend callback：暂时仍由 Python 调用；
- Turn journal 写入：已经完全由 TS 执行。

因此这不是双实现，而是迁移中的端口：`TS owns decision → Python temporarily supplies some effect handlers → TS reduces the result`。

### 单一语义所有者：为什么可维护性真的改善

迁移前可能出现：Python 实现一份 settlement 规则、Python 另一处又解释一份 journal、测试自己再隐含一份 phase 认知。迁移后：

```text
effect_program.ts
    = settlement 语义所有者

turn_journal.ts
    = journal 解释所有者

turn_transaction_contract.json
    = transaction phase 唯一数据源（Python 和 TS 不再各维护一份 phase 列表）
```

Python 只负责兼容和调用，不再保留第二份规则解释器。实际效果：

- `effect_program.py` 减少约 177 行；
- 删除旧约 238 行 Python journal 规则测试；
- 新增 TS 原生测试和 Python→TS 集成测试。

但行数不是价值证明：规则定位更清晰、旧实现被删除、语义能被独立验证，才是价值。

假设新增一个 settlement step（如 `"human_gate"`），类型系统会推动你检查：step union、receipt、failure、next-action、reducer、handler、测试。在 Python 动态字典模式下，很多遗漏只能等运行到罕见分支才暴露。

另一个长期收益是合同共享：LoopX 控制面最终包含 CLI、本地 App、dashboard、scheduler、multi-agent runtime、extension provider，这些表面天然接近 JSON / TypeScript 世界，TS kernel 可以共享 enum、DTO、state transition、projection schema、error contract。更理想的方式不是手工复制接口，而是从同一 schema 生成或导入类型。

## 纯函数式 transition：Todo → Next Action

PR #3414 的核心模块 `next_action.ts` 是一个完整的 TS 语义转换案例：Python 负责文件和集成，TS 负责协议解析、状态转换和纯语义规则。四步走：

### 入口：unknown → runtime validation → typed request

请求来自 Python / JSON，入口类型必须是 `unknown`，不能直接相信它满足某个接口：

```ts
function requiredObject(value: unknown, label: string): JsonObject {
  if (typeof value !== "object" || value === null || Array.isArray(value)) {
    throw new Error(`${label} must be an object`);
  }
  return value as JsonObject;
}
```

分层是：

```text
unknown
  ↓ runtime validation
JsonObject
  ↓ field validation
TodoNextActionRequest
```

TypeScript 类型只在编译期存在；JSON 运行时不会自动遵守接口，所以每个边界都要显式验证。

### 判别联合：operation 区分操作分支

请求不是“一个充满可选字段的大接口”，而是两个明确分支：

```ts
export type TodoNextActionRequest =
  | {
      operation: "bind";
      lines: readonly string[];
      todo_id: string;
    }
  | {
      operation: "settle_completion";
      lines: readonly string[];
      todo_id: string;
      agent_todos: readonly TodoNextActionSnapshot[];
      materialized_todo_ids: readonly string[];
    };
```

`operation` 是判别字段，判断后 TS 自动收窄：

```ts
if (request.operation === "bind") {
  // 这里 request 一定有 todo_id 和 lines
} else {
  // 这里 request 一定有 agent_todos 和 materialized_todo_ids
}
```

对比不安全写法：一个大接口 + 大量可选字段（`operation: string; agent_todos?: Todo[]; ...`），会允许大量非法状态，到处需要 `if (!request.agent_todos)`。

### fail-closed：不确定归属时不改写

匹配旧 Next Action 的优先级：

1. 正确 schema 的 typed binding（Markdown 注释里的 `todo_id` 外键）；
2. 没有任何 binding 时，允许一次 legacy exact-text 迁移（唯一可见条目且文本与完成的 Todo 相同）；
3. 其他情况全部 `route_unmatched`，不修改。

```ts
const boundTodoId =
  matches.length === 1 &&
  matches[0].schema === NEXT_ACTION_BINDING_SCHEMA
    ? matches[0].todoId
    : null;
```

随后：`boundTodoId === completed.todo_id` → `typed_todo_binding`；无 binding 且唯一可见条目文本等于已完成 Todo → `legacy_exact_text`；否则 `routeUnmatched`。即使某个 Agent Todo 完成，也不能推断 Owner 手写的 “发布路线” 属于它。

> 不确定归属时，不自动改写用户状态。

### Python facade / TS semantic transition 边界

```text
Python public API
  ↓
Python snapshot / file integration
  ↓
TypeScript semantic transition
  ↓
typed result
  ↓
Python state writeback
```

Python 只做：文件、CLI、锁、状态写回、兼容入口；TS 只做：协议解析、状态转换、纯语义规则。效果 runtime 的 fingerprint 列表会包含 `todos/next_action.ts`，新源码进 wheel 后不会误连旧 bundle。

### 技巧速查表

| 技巧 | PR 中的用途 |
|---|---|
| `unknown` | 把 JSON / 跨语言输入视为不可信 |
| runtime type guard | 进入核心逻辑前验证字段 |
| discriminated union | 用 `operation` 区分 `bind` / `settle_completion` |
| `typeof CONSTANT` | 让 schema version 成为字面量类型 |
| `readonly` | 表达“函数不应修改输入” |
| copy-on-write | `const updated = [...lines]`，返回新数组，不污染原值 |
| `Set` | O(1) 判断状态和控制任务类别 |
| `Extract<Union, {...}>` | 从 union 中取出指定操作分支 |
| `??` / `?.` | 清楚表达 nullish fallback |
| `Map<string, Handler>` | effect runtime 的 handler 注册表 |
| schema version | Python 与 TS 之间的协议演进边界 |
| 纯函数式 transition | 相同输入得到相同结果，便于测试和推理 |
| `Partial<T>` | 测试 helper 中只覆盖需要变化的字段 |

测试 helper 示例：

```ts
function todo(
  todoId: string,
  overrides: Partial<TodoNextActionSnapshot> = {},
): TodoNextActionSnapshot {
  return {
    todo_id: todoId,
    status: "open",
    task_class: "advancement_task",
    // ...默认值
    ...overrides,
  };
}
```

`Partial<T>` 的意思是：构造测试对象时所有字段都可以暂时省略，最后通过默认值补齐，比每个测试重复写整个 Todo 对象更清晰。

### 设计取舍（长期演进点）

1. Markdown 解析仍是兼容层：只在 `## Next Action` 下存在唯一明确条目时才自动迁移，安全但说明未来应让结构化 Todo 成为主路径；
2. `task_class` 仍是 `string | null`：未来可建模成字面量 union（`"advancement_task" | "continuous_monitor" | ...`），获得编译期约束；
3. 优先级仍从文本 `[P0]`–`[P4]` 解析：兼容现有 Markdown 的实用方案，但业务语义藏在字符串里，长期应来自结构化 metadata；
4. Python / TS 之间仍有两套字段规范化逻辑：当前靠 schema version 和双端验证保持安全，更进一步可抽成 JSON Schema 减少字段规则重复。

## 架构模式：imperative shell + functional core

核心思想：把“会失败的 I/O”和“纯状态规则”分开。

```text
shell（命令式外壳）          core（纯函数核心）
文件锁、网络 I/O、持久化      状态校验、receipt 绑定、
环境变量、进程、平台 API      结算状态、字段语义
```

- shell 拥有副作用和失败；core 是纯函数，相同输入得到相同结果，可以独立单测；
- shell 把 writeback、spend 这类动作作为 callback 传给 core，由 core 决定顺序；
- 收益：外部世界可以失败，但状态规则只集中在一个核心，避免多处在各处维护自己的状态机。

这是 RPC、effect runtime、外部集成里最值得复制的分层：外层随便换，语义核心不漂移。

### Map<string, Handler>：协议注册表

```ts
const handlers = new Map<string, EffectRuntimeHandler>([
  ["capability.validate_result", validateResult],
  ["capability.validate_settlement_callback", validateSettlementCallback],
]);
```

把协议名和实现解耦：

- 新增 handler 不需要改一大串 `if / else`，注册一行即可；
- 调用方只依赖稳定的协议名，不依赖具体实现；
- 所有协议入口统一收口到同一个 runtime / dispatcher，方便统一校验、日志和审计。

### 边界资源保护：数组长度与 payload 上限

外部输入除了类型验证，还要做资源保护：数组长度、字符串大小、payload 字节数都要设上限。否则一个“形状合法”的超大 JSON 也能拖垮运行时（呼应“unknown 不保证数据量”）。

> 边界校验同时回答两个问题：形状对不对、规模是否可接受。

## Runtime 工程模式

### 幂等与崩溃恢复：effect_id 合同

真实场景：TS 已经把 journal 写入磁盘，但还没来得及给 Python 回应，进程崩溃——Python 无法知道写入到底有没有发生，直接重试可能重复产生副作用。

解决办法是为每个 effect 建立稳定 `effect_id`：

```text
goal_id : agent_id : todo/replan binding : turn_instance_id
```

写 journal 前检查已有文件：

- 没有文件：正常写；
- 已有相同 `effect_id`：同一 effect 的安全重放；
- 已有不同 `effect_id`：拒绝覆盖。

合同是：

```text
same effect_id + same typed effect → retry safe
different effect_id               → fail closed
```

Python runtime 复用相同 request identity，并且只对声明为 `retry_safe` 的调用重试。测试覆盖：常驻 runtime 复用、重启后同 effect 可重放、不同 effect 不得覆盖、runtime 意外退出后自动恢复。

这类“副作用发生了，但 ACK 丢了”的问题，是长程 Agent control plane 必须认真处理的，不是普通 CRUD 的边角问题。

完整链路可以再拉长一层：

```text
effect_id → invocation_id → provider idempotency_key → receipt → writeback / spend
```

同一个 effect 只允许对应一次真实调用：进程崩溃后不换 invocation 重发，而是读 journal、用同一个 key reconcile，最终只允许一个 receipt 进入结算。

### fail closed：请求过大直接断连

RPC 请求被限制为 2 MiB。Python 在连接前拒绝超大请求；TS server 也独立限制：

```ts
if (Buffer.byteLength(raw, "utf8") > MAX_REQUEST_BYTES) {
  socket.destroy();
  return;
}
```

`return` 很关键：连接销毁后不能继续 parse 或 dispatch。行为测试证明：oversized request 没有进入 handler、runtime 没有因此重启、后续正常请求继续使用相同 PID。

### 常驻 runtime 生命周期

- **冷启动**：Python 计算源码 fingerprint → 查找 runtime info → 不存在则拿 startup lock → 启动 Node → 注册 typed handlers → 写入 0600 runtime info；
- **热调用**：后续请求直接复用同一个 Node 进程，不需要每次重启；
- **升级**：fingerprint 覆盖所有相关 TS/JSON 源码，升级后的 wheel 拥有不同 fingerprint，不会误连旧 runtime；
- **空闲退出**：默认空闲 5 分钟后关闭并释放内存。

### 共享解析缓存：内容有效性与引用隔离

复用解析结果时，需要分别回答两个问题：

| 问题 | 对应机制 |
|---|---|
| 磁盘内容是否仍与缓存对应？ | 将新读到的字节与缓存对应的字节比较，或按约定比较内容摘要 |
| 调用者能否改坏共享结果？ | 将解析出的普通 JSON 对象与数组逐层冻结后再共享，见 [readonly 与冻结](#readonly表达不可在原地修改) |

只冻结对象，无法发现磁盘变化；只校验字节，也无法防止调用者通过共享引用修改解析结果。**内容匹配后复用已冻结的解析值，可以省去重复解析和逐次深拷贝，但未必省去读盘。**

内容匹配仅说明本次读到的内容与缓存一致，不保证磁盘随后不会再变；需要更强的一致性时，还须定义读取快照或版本语义。冻结与内容校验本身也有成本，应计入整体收益。

### 性能基线

| 场景 | 结果 |
|---|---:|
| Node 冷启动 | 约 163 ms |
| warm ping p50 | 约 0.243 ms |
| warm identity p50 | 约 0.236 ms |
| 两次 RPC 的 bind p50 | 约 0.464 ms |
| crash recovery | 约 137 ms |
| 活跃 runtime RSS | 约 85 MB |
| idle 资源释放 | 默认 5 分钟 |

端到端 deep-doctor 的成对差异：p50 约 `-237 ms`、p95 约 `+169 ms`——波动大于桥本身的亚毫秒 warm RPC 成本，当前没有观察到显著端到端性能回退，也不能据此宣称 TS 让 LoopX 更快。

正确结论：

> PR-1 以可接受的冷启动和内存成本，换来了长期运行中的低延迟 TS 语义内核；主要收益是可维护性和正确性，而非单次命令提速。

后续两个原则：不要把每个微小表达式都拆成一次 RPC；紧密的 Effect Program 步骤应在 TS 一侧批量解释、reduce 或直接执行。等主 CLI 迁入 TS 后，同进程 import 会消除这层 RPC 成本。

## 迁移策略与验证

### 为什么不先迁测试：测试跟随语义所有者

“先把测试全部迁成 TS”看起来风险小，但若生产语义仍归 Python，TS 测试只能隔着接口测 Python 行为，并没有形成新的架构所有权——结果是 Python 实现一套、Python 测试保留、TS 又写一套跨语言测试，仓库更重。

PR-1 采用纵向切片：

```text
先刻画 Python 现状
  → 迁移一个 cohesive semantic owner
  → 切真实生产调用
  → 删除对应 Python 规则
  → TS 原生测试新 owner
  → 跨语言测试只验证边界
```

先用 characterization 锁定行为，再让测试跟随新的语义所有者一起迁移。

### 验证金字塔（六层）

仅有 `tsc` 通过远远不够：

1. **静态类型检查**：`npm run typecheck:control-plane`，`strict: true`；
2. **TS 原生单元测试**：直接测试 Effect Program 与 Turn journal 的语义 owner，当前 13/13 通过；
3. **Python characterization parity**：以迁移前固定基准构造输入，分别跑旧基线和新实现，当前 Turn journal 10/10 精确一致——回答“这次迁移是否偷偷改变了原有语义”，不宣布旧行为永远正确；
4. **Python→TS runtime 集成测试**：覆盖 runtime 复用、restart/replay、cross-effect overwrite、crash recovery、idle shutdown、oversized request，当前 5/5 通过；
5. **wheel/sdist 安装测试**：证明 `.ts` 文件真的进入 wheel / sdist、全新环境能启动 Node runtime、deep doctor 能验证真实语义而非只检查文件存在；
6. **性能与故障测试**：cold start、warm latency、memory、idle exit、crash recovery、端到端 overhead。

### 后续迁移的判断标准

适合优先迁移的模块通常具备：大量 typed state、明确状态转移、非法状态较多、需要 replay / idempotency、会被 CLI / App / dashboard 共同消费、当前规则散布在多个 Python 文件、能形成 cohesive vertical slice。例如 todo completion / continuation 状态机、quota should-run 决策、replan obligation lifecycle、scheduler projection / ack、typed event reduction、goal authority / handoff contract。

不适合为了迁移而迁移的：很薄的 shell / OS glue、稳定且只在 Python 调用的辅助脚本、仍强依赖 Python-only SDK 的 host adapter、没有明确语义所有权的小工具函数。

判断标准不是“这个文件能不能翻译成 TS”，而是：

> 把它迁到 TS 后，能否删除旧规则、收紧状态合同，并让下一次修改更容易定位、验证和回滚？

### assert.throws：测试「必须失败」的路径

```ts
test("runtime input and validation receipts fail closed", () => {
  assert.throws(
    () =>
      reduceTodoCompletionTransaction(
        request({ requested_no_followup: "true" }),
      ),
    /requested_no_followup must be a boolean/,
  );

  assert.throws(
    () =>
      reduceTodoCompletionTransaction(
        request({
          todo: { ...baseTodo, validation_command: "true" },
          validation_receipt: {
            schema_version: "issue_fix_validation_command_v0",
            command_label: "unsafe receipt",
            exit_code: 0,
            passed: true,
            stdout_captured: true,
            stderr_captured: false,
            local_path_captured: false,
          },
        }),
      ),
    /stdout_captured must be false/,
  );

  assert.throws(
    () =>
      reduceTodoCompletionTransaction(
        request({
          requested_no_followup: true,
          requested_has_successor: true,
        }),
      ),
    /cannot record both no_followup and a successor/,
  );
});
```

这段语法有三层，从外到内拆：

1. **`test("名字", () => {...})`**：声明一个测试用例。第一个参数是测试名（失败时会在报告中显示），第二个是执行体——`assert` 抛错时 `test` 会把这个用例标记为失败。
2. **`assert.throws(fn, /正则/)`**：断言「调用 `fn` 必须抛出异常」，并且抛出的错误消息要匹配第二个参数的正则字面量 `/.../`。
3. **`() => reduceTodoCompletionTransaction(request({...}))`**：**延迟执行的关键**。`assert.throws` 接收的是「一个函数」，由它内部去调用并捕获异常。如果不包这层箭头函数、直接写 `reduceTodoCompletionTransaction(request({...}))`，函数会当场执行，异常在 `assert` 之外抛出——测试用例直接崩掉，`assert.throws` 根本没机会断言。

为什么要断言「错误消息」而不只是「会抛」：`/requested_no_followup must be a boolean/` 验证的是「不仅失败，而且以正确的方式失败」——错误消息点出了具体字段和期望类型。如果只写 `assert.throws(fn)`，任何异常都能通过，可能掩盖「字段校验根本没走到、错误从别处冒出来」的假失败。

三段都在测 **fail-closed（防御式拒绝）**，和「边界校验」「让非法状态无法构造」是同一主题的测试形态：

- 第一段：`requested_no_followup` 传了字符串 `"true"` 而不是 boolean → 边界运行时校验拒绝类型错误，而不是悄悄接受（呼应「TS 类型只在编译期存在，外部输入必须 runtime 校验」）；
- 第二段：构造非法 `validation_command`（字符串）配一个可疑的 `validation_receipt`，断言这类「command 与 receipt 字段组合」被拒绝，错误消息指向 `stdout_captured` 字段——测的是 receipt 内部的交叉约束，而不是单个字段；
- 第三段：`no_followup` 和 `successor` 是互斥语义，同时设置必须被拒绝（呼应「判别联合 / 让非法状态无法表达」——类型层面没拦住时，运行时校验兜底）。

其它语法细节：

- 多行函数调用 + 尾逗号：`request({...})` 跨多行、嵌套调用闭括号对齐，都是纯格式，不影响语义；
- `{ ...baseTodo, validation_command: "true" }`：对象展开构造「在基础对象上覆盖单个字段」的变体，是测试里构造合法基线的常用手法（和 `Partial<T>` 测试 helper 是同一思路）。

（`test` / `assert.throws` 来自 Node 内置 `node:test` 或 Vitest / Jest 等测试框架，写法一致。）

### 并发测试：同时启动不等于竞争发生

`Promise.all` 只表达「一起启动、等全部完成」，**不表达「两个操作读到同一个旧版本」**：

```ts
await Promise.all([createA(), createB()]);
```

实际执行顺序可能退化成串行：

```text
A 读取 → A 提交 → B 读取
```

此时 B 看到的是 A 提交后的新状态，可能直接以「已存在」返回，根本没走到预期的 CAS 分支。于是「断言一胜一冲突」的测试在某种交错下失败、在另一种交错下通过——它测到的是调度运气，而不是 CAS 语义。

要真正验证 CAS，必须把交错**做出来**：

```text
A 读取旧版本 ─┐
              ├─ 两者都读完 → 放行提交 → 一胜一冲突
B 读取旧版本 ─┘
```

做法是在两个关键动作之间插入共享屏障（barrier / latch）：两边各自完成读取后停在屏障上，等对方也到达，再一起进入提交。这样「同一版本上的两个写者」就从概率场景变成确定性场景。

可以当检查表用：

- `Promise.all` / `allSettled` 只保证「都在跑、都会等到」，不保证任何读写顺序；
- 用 `setTimeout`、随机延迟「制造并发」得到的是概率覆盖，不是证明；
- 并发测试要控制的是**关键事件的先后关系**（读到旧版本 → 放行 → 提交），而不是「同时开始」。

### `Proxy<T>` 类型上仍是 `T`，行为上不一定

**背景：Proxy 是什么。** `Proxy` 用一组拦截器（trap）包住目标对象：读属性走 `get`、写属性走 `set`、函数调用走 `apply`……没写的 trap 就是默认行为。TypeScript 标准库给它的声明是（`lib.es2015.proxy.d.ts`）：

```ts
new <T extends object>(target: T, handler: ProxyHandler<T>): T;
get?(target: T, p: string | symbol, receiver: any): any;
```

两处值得注意：构造结果类型就是 `T`，和原对象**完全相同**；而 `get` 拦截器的返回值是 `any`。也就是说，`get` 里返回什么都能编译通过，编译器照样认为这个对象是 `T`——「类型检查通过」证明不了转发正确。

**为什么直接转发会出问题：`this` 变了。** Proxy 是与目标**不同身份**的对象，而方法调用时 `this` 是接收者：

```js
const proxy = new Proxy(new Map([["k", 1]]), {});
proxy.get("k");
// TypeError: Method Map.prototype.get called on incompatible receiver #<Map>
```

`Map` 的数据存在目标对象的**内部槽**（`[[MapData]]`）里，proxy 没有这个槽。私有字段同理，MDN 专门记了 [no private field forwarding](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Proxy#no_private_field_forwarding)：

```js
class Secret {
  #secret = "x";
  get secret() { return this.#secret; }
}

const proxy = new Proxy(new Secret(), {});
proxy.secret;
// TypeError: Cannot read private member #secret from an object whose class did not declare it
```

这里炸的是 **getter**——读属性时 `this` 一样是 proxy。

**修法就是这次测试里的写法**：

```js
const value = Reflect.get(target, property);  // 不传 receiver，getter 的 this 仍是 target
return typeof value === "function"
  ? value.bind(target)                        // 方法绑定回真实对象再返回
  : value;
```

- `Reflect.get(target, property)` 不传 `receiver`，getter 内部 `this` 就是 `target`；若写成 `Reflect.get(target, property, receiver)`，或直接 `target[property]` 取到方法后不绑定就调用，`this` 又会变回 proxy；
- `bind(target)` 把方法固定成「以真实对象为 `this` 调用」——上面两个 TypeError 场景都能靠它恢复；
- 代价：每次取到的都是新的绑定函数（`proxy.method !== proxy.method`）。所以它适合**有限代理**，不是通用透明代理；
- 原生对象（Map、Set、Date、DOM 节点等带内部槽的对象）都不能靠「空 handler 的 Proxy」假装透明，这也是 MDN 强调「no-op 转发只对普通对象成立」的原因。

**这种代理在测试里做什么。** 用 Proxy 包住真实 store，只拦截 `commit`，其余调用原样转发——既能在「提交成功、响应丢失」这个精确位置注入故障，又保留真实的数据库提交，验证到的是真正的恢复语义，而不是一个被替换掉的假存储。

**边界**：类型上的 `T` 是标准库给的假设，约束不了 trap 的实现；要行为等价，靠的是针对该接口的契约测试（见「静态形状 vs 行为合同：conformance suite 证明语义」），而不是 Proxy 本身。

## TS 不会自动解决什么

1. **类型在运行时不存在**：外部 JSON 仍可能传 `{"step_kind": 12345}`，RPC、文件、插件输入必须有 runtime decoder。
2. **`as` 可以绕过类型系统**：`as unknown as SettlementIdentityInput` 是受控但真实的逃生通道，应逐步收紧，而不是大量复制。
3. **类型不证明业务正确**：effect 顺序写错、receipt 判定错误、idempotency key 设计错误、crash window 没覆盖、replan 语义不合理，类型全通过也可能发生。
4. **类型不会让「检查过」的事实保鲜**：`ValidatedX` 这类标记只能证明构造时校验通过，不能证明使用时仍然成立（TOCTOU）。中间的 `await`、其它请求、其它进程都可能推进状态，因此授权、锁与 epoch 要在**真正执行副作用的边界**再检查一次，而不是拿到对象时检查一次就一路信任；外部执行器的 fencing 与终态锁是独立职责。
5. **字符串分类债务**：部分失败类型仍根据 reason 是否包含 `"budget"` 分类；长期应让 callback 返回 typed error kind，而不是从错误文案反推语义。
6. **Node 引入运行成本**：安装要求、冷启动、常驻 RSS、socket / framing、进程恢复、包升级一致性。TS 应优先迁移“值得成为语义内核”的部分，而不是机械迁移所有 Python 文件。
7. **标准库的类型是假设，不是行为保证**：`Proxy<T>` 声明为 `T`、`get` 拦截器返回 `any`，代理行为是否真的等价于 `T` 只能由测试证明；同类情况还有「类型通过但转发错误」「并发启动但没发生竞争」。

真正让迁移成立的不是 `.ts` 后缀，而是：

```text
typed model
+ single semantic owner
+ runtime validation
+ explicit effects
+ idempotency
+ characterization parity
+ crash/replay tests
+ artifact validation
+ performance measurement
```

缺少这些，换成 TS 也可能只是一次昂贵的语法翻译。

## 学习路径

**第一阶段：只学类型**。读 Effect request / turn、Settlement enums、Settlement identity / result、NextAction union。练习：给 failure kind 增加一个值看 `tsc` 是否提示遗漏；把 `SettlementResult` 改写为成功 / 失败判别联合；写一个带 `never` 的穷尽 `switch`。

**第二阶段：理解状态机**。读 `settlementIdentity`、`seedCommittedSteps`、`settlementNextAction`、`commitStepPayload`。思考三个问题：当前哪些 receipt 已经存在？下一步 effect 为什么是它？重放时如何避免重复执行？

**第三阶段：理解 runtime**。读 Python request bridge、runtime server、handler registry、native journal effect。

**第四阶段：运行验证**。依次执行 `npm ci`、`npm run typecheck:control-plane`、`npm run test:control-plane`、Python 集成测试、`uv build`、`loopx doctor --deep`。

## 源码阅读检查表

读一段 TS control-plane 代码时，依次回答：

1. 这个值来自外部 JSON 还是内部构造？有没有 runtime decoder？
2. 有没有 `as` / `any` 逃生通道？它是不是迁移缝？
3. 联合类型的判别字段是否穷尽处理？新增 variant 会不会被编译器抓住？
4. 非法状态是否可构造（例如成功值和失败同时存在）？
5. 副作用有没有稳定 identity？重试是否幂等？不同 identity 是否 fail closed？
6. 谁拥有规则语义？Python / TS 是否各有一份？
7. 哪些是纯决策、哪些是副作用？边界在哪一层？
8. `await` 是否丢失？并发是否无界？
9. 错误分类靠类型还是字符串匹配？
10. 这个模块迁到 TS 后能否删除旧规则？
11. 未知字段是否被 exact-field 校验拒绝？还是被悄悄透传？
12. 外部输入的数组长度 / payload 是否有上限？
13. 异步函数有哪些 fulfilled / rejected 通道？异常发生前是否已经跨过副作用边界？哪些异常可恢复，哪些必须继续抛出？

## 类型关系速查

```text
interface  → 对象合同（结构类型，不用声明 class）
readonly   → 不可在原地修改
泛型 <T>   → 同一结构承载不同 value
as const   → 从数组得到字面量联合
Record<K,V> → K 为有限键联合时，要求每个键都有 V 类型的值
satisfies  → 在构造处检查类型合同，不生成运行时校验
联合类型   → 封闭的形态集合
判别联合   → 按判别字段自动收窄；TS 4.6+ 支持 const 解构后关联收窄
类型谓词   → TS 5.5 起部分检查可自动推断，filter 据此收窄元素类型
asserts    → 断言函数正常返回后收窄；实际检查由实现负责
never      → 穷尽检查（新增状态漏处理会编译失败）
unknown    → 使用前必须证明它是什么
any        → 放弃检查
Promise<T> → 只约束未来成功的值；拒绝无异常类型，也无处理义务
NoInfer<S> → 禁止某个参数参与泛型推断，收紧推断来源
品牌类型    → 给 string 附加用途身份，防止 ID / digest / revision 混用
Pick<T,K>  → 选取字段，收窄静态依赖
Partial<T> → 字段可选，常用于受限 options
ReturnType → 从函数派生返回类型
Awaited<T> → 递归解包 await 结果类型
Extract    → 按可赋值条件筛选联合成员
```

一句话：TS 对 LoopX 的核心价值，是把“状态集合明确、分支可穷尽、字段不漂移、改协议时所有消费者一起报错、副作用与纯决策分离、replay 与 idempotency 成为一等类型和测试合同”变成可编译检查的约束。

补充：`===` 是默认相等运算符（值 + 类型都相同，且是类型收窄触发器）；`==` 会隐式转换，只保留 `== null` 惯用法。
