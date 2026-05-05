# Agent Harness Post-S15 Steering

> 用途：把 agent-harness 最新 TAU2 memory strategy 进展转成可执行 steering。本文基于本地 agent-harness TODO 与公开/通用技术判断整理，不包含内部文档链接。

## 一句话判断

S15 `S11c + action-family soft rerank` 已经从“下一候选”降级为 negative diagnostic：family rerank 本身没有稳定带来 uplift。下一步不应继续堆更多 family rule，而应把问题拆成三条更本质的线：confirmation / write timing 稳定化、argument grounding、applicability boundary，并把 paired simulator variance 变成默认报告。

## 当前信号怎么读

1. **S11c 有机制信号，但不是 solid uplift**
   - compact agent procedure memory 在部分 retail seed 上能提升，但 multi-seed 后方差很大。
   - 这说明“更窄、更程序化的 memory view”方向值得保留，但不能靠单轮高点讲效果。

2. **S15 证明 action-family rerank 不够**
   - action-family soft rerank 没有保住 S11c 的高点，retail / airline 都偏负。
   - 这不是说明 family signal 没价值，而是说明单独把 family 当排序特征太薄：它解决不了用户确认后提前 STOP、write tool 未执行、参数不 grounded、memory applicability 过宽这些更上游的问题。

3. **真正的 failure mode 更像执行稳定性 + applicability**
   - 有些回退不是 memory 没召回，而是 memory 改变了对话节奏，触发 user simulator 提前停止。
   - 有些回退是 agent 已接近正确行动，但 write arguments / object identity / order state 没对齐。
   - 有些回退来自宽泛 procedure 被提前注入，后续 pre-write checker 没机会补 action-specific memory。

## 建议的下一步实验顺序

### P0. paired simulator variance 默认化

每个 S-triggered / S11c-like 策略都默认生成 paired simulator variance report，而不是只看 reward mean：

```text
same-seed S0 vs treatment:
  reward_delta
  db_match_delta
  write_tool_attempt_delta
  premature_confirm_stop_transition
  agent_no_write_after_confirmation_transition
  selected_memory_key_delta
  prompt_token_delta
```

验收标准：任何策略进入“候选主线”前，至少说明它的收益来自：

- 减少 premature confirm STOP；
- 提高确认后 write tool 执行率；
- 改善 write arguments grounding；
- 或者真实减少 memory-induced regression。

如果说不清，只能标为 diagnostic，不进入主结论。

### P1. confirmation / write timing 稳定化

先把“用户确认后 agent 是否立刻执行 write tool”作为单独稳定化目标。

建议新增一个 treatment，不改变 memory corpus，只在 agent-side policy / prompt 上约束：

```text
after user confirms permission:
  if pending write action is known and all required args are grounded:
    execute write tool before summarizing or asking again
  else:
    ask exactly one missing-argument question
```

这条线要和 official-comparable run 分开标注：如果使用 altered user simulator，只能作为 diagnostic；如果只改 agent-side policy，可以作为 product-like treatment。

验收标准：

- premature confirm STOP 不一定消失，但 agent no-write-after-confirmation 要下降；
- reward / DB 提升必须和 write tool attempt 增加对应；
- 不允许用 hidden expected actions 或 gold DB diff。

### P2. argument grounding checker

把 pre-write checker 从“找同 family procedure”升级为“检查 candidate write arguments 是否被 observed state 支撑”。

最小字段：

```text
candidate_write_tool
candidate_write_args
observed_entity_ids
observed_order_status
observed_item_ids
observed_address/payment/shipping_state
missing_required_args
arg_source_refs
memory_applicability_notes
```

核心判断：

- memory 可以提醒“这种状态下要改地址/退货/换货”，但不能替代当前 task 的 entity grounding。
- 若 memory 和 observed state 冲突，应该降权或只作为 caution，而不是注入成强 procedure。

验收标准：

- write attempted but wrong arguments 的 case 下降；
- matched memory 不再只按 title / URI family 注入，而是需要和当前 observed state 对齐；
- 对 multi-item / multi-order / compound action case 有单独 attribution。

### P3. applicability boundary / negative memory

对每条 procedure memory 增加轻量 applicability boundary：

```text
applies_when
does_not_apply_when
required_observations
required_user_confirmation
known_counterexamples
last_negative_exposure
```

不要一开始做复杂模型；先从 paired replay / regressed cases 生成 `does_not_apply_when` 和 `known_counterexamples`。

验收标准：

- same memory 在 improved case 和 regressed case 上能被解释；
- regressed case 的 memory 后续会被 bury / caution / rewrite，而不是继续同等优先级曝光。

## 给 Agent Harness 主控的转发稿

Steering: S15 `S11c + action-family soft rerank` 已经是 negative diagnostic，不建议继续堆 family rerank 本身。我的判断是，当前主问题已经不是“再多一个 family 特征”，而是三类更上游的可执行问题：确认后的 write timing、write arguments grounding、procedure memory 的 applicability boundary。

建议下一步拆成三个 P0/P1：

1. 把 paired simulator variance report 设为 S-triggered / S11c-like 策略默认产物，至少统计 `premature_confirm_stop_transition`、`agent_no_write_after_confirmation_transition`、`write_tool_attempt_delta`、`selected_memory_key_delta` 和 token delta。没有这个报告的 reward mean 不进入主结论。
2. 做一个 confirmation / write timing treatment：用户确认授权后，如果 pending write action 已知且参数 grounded，agent 先执行 write tool，再总结或继续问；如果缺参数，只问一个缺失参数。若改 user simulator，必须标注 diagnostic-only；若只改 agent-side policy，可作为 product-like treatment。
3. 把 pre-write checker 升级为 argument grounding checker：记录 candidate write tool / args、observed entity/order/item/status、missing args、arg_source_refs、memory applicability notes。memory 只能提示 procedure，不能替代当前 task 的 entity grounding。

验收标准：下一轮不只看 reward uplift，还要证明回退 case 是否来自 STOP timing、no-write、wrong args、off-applicability memory。目标是把 S11c 的机制信号转成更稳的 execution policy + applicability feedback，而不是继续扩大 memory 注入。

## 与用户职业主线的关系

这条线非常适合包装成“Agent memory recommendation / RL-style feedback learning”的工程证据：

- `memory exposure` 不是召回命中，而是会改变 agent 行为的 action prior；
- feedback 不只看最终 reward，还要分解到 write timing、tool correctness、DB diff、argument grounding；
- memory lifecycle 不只是 add / delete，而是 exposure 后的 promote / bury / rewrite / caution；
- 推荐系统经验可以迁移到 post-exposure utility、negative feedback、counterexample-aware rerank 和 delayed outcome。

因此后续材料和项目叙事应避免说成“调 prompt 提升 tau2”，而要说成：构建 agent experience item 的 exposure feedback loop，并用 paired replay / simulator variance / applicability boundary 估计 memory 的真实 utility。
