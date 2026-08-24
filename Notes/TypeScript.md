# TypeScript

> 相关：[Rust.md](./Rust.md)、[AI-Agent-Engineering.md - LoopX 长程 agent 的本地控制面](./AI-Agent-Engineering.md)、[Software-Engineering.md - Strangler Fig](./Software-Engineering.md)。

## 阅读地图

1. “TypeScript 心智模型”先建立 TS / JS / Node 的分工，理解“类型只存在于编译期”。
2. “类型基础”把 interface、readonly、泛型、`as const`、判别联合、`unknown`、Promise 看作同一种动作：把协议或状态写进类型。
3. “状态机建模”讲核心设计原则：让非法状态无法构造，而不是靠运行时 `if` 拦截。
4. “Effect Program 与语义内核”以 LoopX PR-1 为例，讲纵向迁移如何把 settlement / journal 语义收口到 TS。
5. “Runtime 工程模式”沉淀幂等重试、fail closed、常驻 runtime 生命周期与性能基线。
6. “迁移策略与验证”解释为什么纵向切片优于“先迁测试”，以及六层验证金字塔。
7. “学习路径”和“源码阅读检查表”给动手顺序和读代码时的检查问题。

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

### readonly：表达不可在原地修改

```ts
export interface EffectProgram {
  steps: readonly EffectStep[];
  execution_mode: string | null;
}
```

`readonly EffectStep[]` 让 `program.steps.push(newStep)` 直接成为类型错误。这对状态机很重要：receipt、计划、phase prefix 应更接近不可变值，而不是任何函数都能原地修改的共享 list。

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

后者合法，但会把数组收窄声明成 `readonly SettlementStepKind[]`，丢失精确 tuple 信息。区别在于：类型注解是「要求值符合声明类型」，`satisfies` 是「只校验、不改变推断」。

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

### requireExactFields：把 JSON 当版本化协议

TS 的结构类型默认容忍“多余字段”（fresh object literal 除外），但控制面协议往往要求相反：未知字段意味着协议漂移，必须拒绝。

```ts
requireExactFields(
  receipt,
  EFFECT_RECEIPT_FIELDS,
  "external capability effect_receipt",
);
```

`requireExactFields` 检查对象是否存在未知字段或缺少字段。对跨语言、跨 provider 的协议很重要：外部系统多返回一个看似无害的字段，可能慢慢形成未定义协议。原则是：

> 把 JSON 当作版本化协议，而不是随意的字典；未知字段在边界处拒绝，而不是悄悄透传。

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

### 索引访问类型：直接引用权威字段

不想手写第二份类型时，可以直接“按字段取类型”：

```ts
receipts: SettlementResult<unknown>["receipts"]
```

它不是重新声明 `receipts: readonly SettlementReceipt[]`，而是引用 `SettlementResult` 里 `receipts` 字段的权威类型。收益：以后 `SettlementResult.receipts` 的只读性或结构变化，这里自动同步，不会形成第二份类型知识。与数组上的 `[number]`（取元素类型）是同一套 indexed access 机制，只是把下标换成字段名。

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

但“状态与字段的语义约束”类型系统表达不了：

- `running` 不能有 receipt；
- `running` 不能带 mutation；
- `succeeded` 必须对应 committed receipt；
- `no_change` 必须对应 no_change receipt，且不能带 mutation。

这类交叉约束需要在边界校验函数里显式 enforce。设计目标是“非法状态难以表达”，两层叠加才完整：类型层限定形态，边界层限定组合。

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

## TS 不会自动解决什么

1. **类型在运行时不存在**：外部 JSON 仍可能传 `{"step_kind": 12345}`，RPC、文件、插件输入必须有 runtime decoder。
2. **`as` 可以绕过类型系统**：`as unknown as SettlementIdentityInput` 是受控但真实的逃生通道，应逐步收紧，而不是大量复制。
3. **类型不证明业务正确**：effect 顺序写错、receipt 判定错误、idempotency key 设计错误、crash window 没覆盖、replan 语义不合理，类型全通过也可能发生。
4. **字符串分类债务**：部分失败类型仍根据 reason 是否包含 `"budget"` 分类；长期应让 callback 返回 typed error kind，而不是从错误文案反推语义。
5. **Node 引入运行成本**：安装要求、冷启动、常驻 RSS、socket / framing、进程恢复、包升级一致性。TS 应优先迁移“值得成为语义内核”的部分，而不是机械迁移所有 Python 文件。

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

## 类型关系速查

```text
interface  → 对象合同（结构类型，不用声明 class）
readonly   → 不可在原地修改
泛型 <T>   → 同一结构承载不同 value
as const   → 从数组得到字面量联合
联合类型   → 封闭的形态集合
判别联合   → 按判别字段自动收窄
never      → 穷尽检查（新增状态漏处理会编译失败）
unknown    → 使用前必须证明它是什么
any        → 放弃检查
Promise<T> → 未来成功的值；失败走异常
```

一句话：TS 对 LoopX 的核心价值，是把“状态集合明确、分支可穷尽、字段不漂移、改协议时所有消费者一起报错、副作用与纯决策分离、replay 与 idempotency 成为一等类型和测试合同”变成可编译检查的约束。

补充：`===` 是默认相等运算符（值 + 类型都相同，且是类型收窄触发器）；`==` 会隐式转换，只保留 `== null` 惯用法。
