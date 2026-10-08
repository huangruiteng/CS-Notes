# Decision-driven discovery and benchmark reading

## Discover evidence that can change a decision

Start with one to three unresolved questions and the artifact each answer changes. Check current notes and canonical material IDs before searching. Separate `already_read`, `gap_read`, `first_read`, and `assistant_digest` in the reading recommendation without inventing lifecycle fields.

For X, use complementary query families: the exact benchmark/mechanism; its strongest competing explanation; and author/project updates. Compare Top and Latest when useful. Ambiguous common names need a paper ID, author, or distinctive technical phrase. A noisy query is a reason to refine or stop, not to ingest its unrelated results.

For each useful lead, retain post URL/author/date and follow its original paper/repository. Check whether the latest paper changes an older blog's conclusion. Keep positive and negative findings with their task/model/budget boundaries. Deduplicate by canonical paper ID, repository, and existing note coverage; do not create another record for a new tweet about the same material.

Stop when the key evidence gaps have adequate coverage or further results repeat existing sources. Report novel verified candidates, revised existing materials, useful duplicates, and rejected/unread leads with reasons. No candidate-count quota. High-value candidates still require the managed workflow's ranking settlement and readback.

Do not put private employment disputes, offer terms, internal names or private message excerpts into search queries. Reading authorization is not authorization to post, message, follow, bookmark, join a group, or change accounts.

## Read benchmarks as measurement contracts

A user operating or making claims from a benchmark should personally inspect:

- **Construct:** what capability is tested; one long task versus learning across tasks or changing environments.
- **Feedback:** agent-visible feedback versus evaluator-only measurements; hidden tests, cooldowns, oracle access and contamination.
- **Budget/comparator:** model and harness versions; wall time, inference/learning cost, restart and sequential-refinement baselines; held-out task separation.
- **Metric:** best-so-far versus the delivered final artifact; pass@k versus pass@1; valid-run exclusions, repeated seeds, uncertainty, grader calibration.
- **Attribution:** state preservation versus useful experience; generating a memory/update versus using it; selection effects and task-specific adaptation versus transfer.
- **Limits:** failures, missing runs, protocol drift and which claims the evidence cannot establish.

Give a reader map with actual section/figure/table identifiers and an output (for example, a one-page evaluation contract). Long derivations, every task appendix and infrastructure code can remain assistant-led unless they affect the user's claim. Do not demand complete-paper reading for every benchmark. Check existing notes before proposing additions; if they already cover the mechanism and limitations, move to an experiment or decision instead of repeating the explanation.
