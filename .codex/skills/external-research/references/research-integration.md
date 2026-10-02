# Integration with research workflows

This skill owns retrieval and interpretation technique. A research orchestrator
owns the question decomposition, evidence state, budgets and completion rules.
Do not create a parallel ledger or silently replace an active research question.

## LoopX deep research

When the user invokes `loopx-deepresearch`, or this skill is used for an expedition
inside an existing LoopX research run, read the available `loopx-deepresearch`
skill and follow its current CLI packet. Do not start a LoopX run merely because
the user asks for ordinary web research or asks to create this skill.

- Read status before selecting the expedition. Respect `research_contract`,
  `next_expedition`, `stop_conditions` and the packet's `evidence_commands`.
- Use external-research to formulate queries, inspect originals, distinguish
  claims from observations and decide whether another source removes a real gap.
- Record durable sources/findings through the current typed evidence commands.
  Map observation strength, source-family dependence and uncertainty into the
  supported fields; do not invent CLI flags or a second persisted schema. Use
  help or the packet for exact syntax. Do not write canonical state files directly.
- Resolve subquestions only under the research owner's evidence rules. Re-read
  status after the expedition; stop/report when its contract says to do so.
- If the user changes scope, reconcile it through that owner's supported flow;
  do not quietly close another active run or keep searching the superseded target.

The installed LoopX command skill may be generated. Do not patch a managed copy
as the integration mechanism: use this companion skill during retrieval. Changes
to the generated entrypoint belong in its canonical owner and normal repository
workflow, only when such a change is part of the task.

## Other research tasks

Reuse the task's existing outline, source table, RFC or report. Keep one compact
claim-to-source map where it helps auditing; do not require a database, new goal,
subagents or a published artifact for a short comparison. If the orchestrator is
unavailable, external retrieval can still be useful, but do not claim that its
state, report or qualification was updated.
