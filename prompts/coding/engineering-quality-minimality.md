# Engineering Quality And Minimality

适用场景：放入项目级 `AGENTS.md`、review checklist、coding agent system/developer prompt，用于约束重构、抽象、smoke、fixture、bounded context 和批量改动。

```text
Treat code volume as a cost, especially during refactors. A good LoopX change
should make the next change easier to localize, test, and revert; it should not
turn a design possibility into unused production structure.

Before adding a new module, builder, protocol field, CLI option, fixture, smoke
section, or abstraction, pass a minimality review:

- Identify the immediate shipped behavior or active call site that needs it.
  If the only consumer is a future runner, a design note, or a hypothetical
  extension, keep the design in docs or todo state until the real call site
  appears.
- Prefer the smallest behavior-preserving seam. For example, let the ledger
  first recognize one compact public-safe row shape before adding a dedicated
  benchmark-specific builder, arm constants, or wide field-level smoke.
- Characterize before moving code. For status, quota, review-packet, scheduler,
  monitor, and handoff behavior, add or extend parity fixtures first, then
  extract the smallest proven rule.
- Reuse existing repository patterns and bounded contexts. Add code where its
  change reason belongs, such as `control_plane/runtime`, `control_plane/quota`,
  or `control_plane/todos`; do not create generic sink directories or helper
  layers just because several files share a similar shape.
- Treat large or hot files as warning signals. When a change would grow an
  already oversized module, first look for a narrow read model, domain helper,
  or bounded-context home with a compatibility wrapper left behind.
- Distinguish duplicate knowledge from duplicate-looking code. Collapse shared
  state rules, protocol semantics, serialization contracts, and lifecycle
  invariants; avoid a parameter-heavy abstraction when two callers merely look
  similar but will evolve for different reasons.
- Keep smokes thin and durable. They should prove shipped behavior, boundary
  enforcement, and regression contracts, not every incidental field produced by
  a temporary builder. Large smokes are a prompt to move reusable logic into
  product modules or to narrow the assertion surface.
- Make illegal states hard to express. For status, quota, scheduler, monitor,
  todo, and handoff flows, prefer explicit enums, schemas, and transition
  helpers over scattered booleans and prose-only assumptions.
- Fail fast with actionable context at input, config, permission, and state
  boundaries, but do not replace clear control flow with broad exception
  plumbing or silent fallback.
- Ship small, reversible batches. Separate characterization/parity fixtures,
  mechanical moves, behavior changes, and cleanup when that makes review and
  rollback clearer. Avoid opportunistic rewrites, unrelated formatting, and
  "while here" cleanup.

Use this checklist to delete or defer code as actively as you add it. A PR that
removes an unused abstraction, narrows a smoke to the real contract, or moves a
rule into the right bounded context is often more valuable than one that adds a
larger framework around the same behavior.
```
