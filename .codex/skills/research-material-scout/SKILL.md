---
name: research-material-scout
description: Research and triage learning materials; read and explain sources for "请你读" / "精读"; process "素材：" intakes and "读完" closure. Explicit reading follows the source's argument, not career or project ranking.
---

# Research Material Scout

## Choose the mode first

- `请你读 / 精读 / 帮我读一下`: read [the reading protocol](references/paper-reading-protocol.md) before source work. It owns source coverage, explanation, figures and delivery checks for articles, papers, chapters, repos and bundles. Use the source routes below as needed; skip discovery ranking and intake workflows. Explain the author's argument before project applications. Do not edit notes, indexes or lifecycle/ranking; cache only reading artifacts.
- `素材 / 调研 / 继续调研`: follow discovery, source verification and managed intake below. Decision Context guides what to select, not what an explicitly requested reading may omit.
- `整理笔记 / 读完`: follow repository note-integration rules and detail preservation below; only user-backed completion authorizes archiving.

## Discovery Mission

Build a high-signal learning and career material pipeline for the user.

Use the user's current, explicitly confirmed Decision Context to select the next learning action. Read its current version and distinguish user facts, source evidence, and assistant proposals. Career themes are defaults, not permanent weights: new responsibilities, a decision deadline, or a completed reading can change the order. Keep private context out of public queries and skill text.

Before recommending a first read, check existing Notes, managed material records, and the user's latest read-completion statements. Material importance and remaining reading effort are separate: a central paper already understood may need only one missing experiment, a design delta, or a later revisit. Do not invent a completed/archive transition; use the active lifecycle contract and an explicit disposition.

For user-directed note integration, the named target and source's primary domain take precedence over career mapping. Common discovery lanes include agent runtime/evaluation/memory, model learning, serving and RL systems, product workflows, and career signals; select among them from the current task rather than a fixed percentage split.

For decision-driven X discovery or benchmark reading recommendations, read [the focused scout protocol](references/decision-driven-scouting.md).

## Boundary With LoopX Material

This skill is the CS-Notes source-discovery and exact-reading adapter. It owns
source recall, primary-source verification, reader maps, domain scoring, and
the CS-Notes public/private landing decision.

When the connected project or goal explicitly activates Material Lifecycle, use the
project-local managed `loopx-material` skill for generic store inventory, candidate/archive
transitions, lossless migration, ranked-entry rebuild, bounded rerank,
owner-gated apply, rollback, and audit. Pass exact-read evidence and the
project-specific score into that workflow; do not duplicate or weaken its
authority and losslessness gates here.

For CS-Notes, a managed authority pointer under
`.local/material-lifecycle/authority/current.json` means the old candidate and
archive Markdown files are immutable legacy content backing. Never append a
candidate, archive an item, or edit the old Top30 in those files. Use the
project-local `loopx-material` workflow and the private managed intake adapter.
An explicit `素材：` request authorizes candidate intake, a ranking
settlement, and reviewed public-field export for verified public sources
in the same user workflow. Keep intake and ranking as separate
receipts and, when ranking changes, separate authority revisions so CAS,
preview, rollback, and audit remain independent.

For verified public sources, finish version-bound field review and public queue
prepare/apply/check in that workflow; do not wait for another request to publish
the local queue. Keep original content, private annotations and audit evidence
local. Internal or uncertain sources remain private. A public-looking domain
alone is insufficient evidence, and public export never bypasses digest or
owner-gate checks.

Before recommending a first read or refreshing after Git pull, reconcile explicit
owner read-completion evidence and verified remotely merged completion records
with the managed authority. Archive completed material through the source owner;
retain original sources/backing. If retained as a read reference, label the revisit
purpose and keep it in backlog. Assistant `read_scope` is not owner completion.

Every intake must end with one explicit disposition: `top_window`,
`ranked_backlog`, or `no_change`. Determine high value from exact-read evidence,
S/A/B tier, current Decision Context, overlap, and artifact convertibility rather
than tier alone. A high-value material must gain verified ranked membership in
the Top30 or ranked backlog; it may not remain only an unranked candidate.
`no_change` requires a reason and is reserved for lower-value or substantially
duplicative material. If the Top30 is full, move displaced entries into the
ranked backlog without loss. Do not move protected anchors without a changed
Decision Context or explicit owner instruction.

The installed project skill does not itself activate Material Lifecycle.
Without an active project- or goal-scoped profile, declared source authority, and current native owner authorization, this skill may research or read material but must not rewrite the managed store. An already authorized ordinary project source does not require a new Goal or a borrowed agent identity.

## Source Strategy

Prefer primary sources for technical conclusions:

- Papers: arXiv, conference pages, official PDFs.
- Code: GitHub repositories, README, issues, releases.
- Products: official docs, release notes, engineering blogs.
- Internal/user links: Lark/ByteTech only when accessible through user-provided context or approved local tools.

Use social media, 微信公众号, 小红书, X/Twitter, 微博, and aggregators as discovery signals, not final truth.

When extracting mechanisms from a repo, quickstart, prompt, or code file, include file-level links in the user-facing answer and persisted notes/archive. For GitHub sources, prefer commit-pinned permalinks and record the commit read; avoid writing only a repo name or bare filename when a concrete source file drove the claim.

Choose currently callable tools by the question and source type:

- Use web search for broad recall, alternate terminology, and recent developments.
- Use platform search or authenticated source readers for social opinions and author posts; inspect the original posts and links.
- Use paper lanes, GitHub, official docs, release notes, and engineering blogs for technical evidence.
- Use existing local readers for specific URLs, RSS, or transcripts when they add coverage.

Codex remains responsible for verification, ranking, summarization, and local persistence. No specific aggregator is a prerequisite. A publicly listed skill or downloadable client does not establish that its backend is publicly usable; verify service access and dependencies before adopting one. Continue through available sources when an optional tool is absent, and report only coverage gaps that affect the answer.

### Implementation-First Catalogs

For Agent Harness / agent infra exploration, use implementation-first catalogs as a source-discovery layer before broad web search when available.

Current primary catalog:

- `Agent Harness Engineering implementation-first catalog`: `https://github.com/Picrew/awesome-agent-harness`

Use it as an index, not as evidence by itself:

1. Pick the relevant ETCLOVG layer first: execution, tooling, context, lifecycle, observability, verification, or governance.
2. Inspect the candidate repo's README, docs, releases, issues, or paper before ranking it.
3. Prefer implementation entries that can change the user's artifacts: sandbox boundary, tool registry/schema, state/context contract, handoff/workflow loop, trace/eval schema, policy/audit layer.
4. Do not dump many frameworks into Top30. Promote only high-signal projects through the current managed candidate authority, with read status and concrete artifact deltas.
5. Treat stars and catalog summaries as recall/ranking hints, not truth.

### arXiv / Paper Reading Route

For arXiv papers, do not jump straight to PDF extraction unless HTML is unavailable.

Resolution order:

1. Normalize the paper id and version from any of these forms:
   - `https://arxiv.org/abs/<id>`
   - `https://arxiv.org/pdf/<id>`
   - `https://arxiv.org/html/<id>vN`
   - bare title + discovered arXiv id.
2. Try arXiv HTML first:
   - if a version is known, open `https://arxiv.org/html/<id>vN`;
   - if only bare id is known, inspect the abs page for the current version, then try `https://arxiv.org/html/<id>v<version>`;
   - also try `https://arxiv.org/html/<id>` if versioned HTML is not obvious.
3. Use the abs page for metadata, title, authors, abstract, version history, and links.
4. For `精读`, method-heavy papers, or cases where HTML lacks needed appendix, math, algorithm, prompt, or caption detail, try the arXiv TeX source before PDF fallback:
   - download `https://arxiv.org/src/<id>` into `.local/paper-cache/<id>-src.tar.gz`;
   - unpack into `.local/paper-cache/<id>-src/`;
   - locate the entry `.tex` file, usually `main.tex` or the file containing `\documentclass`;
   - recursively inspect included `.tex`, `.bib`, figure captions, tables, algorithm blocks, appendices, and prompt/templates.
5. Fall back to PDF only when HTML/source is missing, blocked, malformed, or lacks the needed figures/tables.
6. If using PDF fallback, extract text into `.local/paper-cache/` and explicitly say that the read path was PDF fallback.

Why this matters:

- arXiv HTML preserves section anchors, table/figure order, equation context, and is easier for user-side parallel reading.
- arXiv TeX source often preserves appendices, captions, algorithms, prompts, and bibliography context better than PDF text extraction.
- PDF extraction can lose figures, captions, math, and table structure; it is acceptable for quick scanning but weaker for `请你读` / `精读`.
- For `请你读` / `精读`, always provide the user-facing HTML link when it exists, even if Codex also used the PDF for extraction.

### Paper Radar Pattern

For recurring or paper-heavy exploration, use `daily-paper-reader` as a design reference, not as a dependency to install. Its useful increment is the pipeline shape: intent profiles -> multi-lane recall -> fusion/rerank -> evidence scoring -> deep/quick/carryover selection.

Adopt these patterns:

1. Convert the user's current goal into 1-3 intent profiles. Each profile should have:
   - a short tag,
   - 3-6 atomic English keywords for exact/BM25-style recall,
   - 1-4 semantic intent queries for embedding/web search,
   - an explicit source lane such as arXiv, OpenReview, conference proceedings, domain preprint servers, GitHub, official docs, social, or implementation catalog.
2. Run more than one lane when possible. Combine exact keywords, semantic queries, and source-specific searches instead of relying on one giant query.
   - For AI / agent infra paper search, treat `arXiv`, `OpenReview`, and major venue lanes (`NeurIPS`, `ICLR`, `ICML`, `ACL`, `EMNLP`, `AAAI`) as high-value paper sources.
   - For cross-domain or bio/chem/medical-adjacent topics, optionally add `bioRxiv`, `medRxiv`, and `ChemRxiv` as separate lanes.
   - Do not sweep every source by default. Pick lanes that match the topic, then record which lane found each candidate.
3. Fuse and rank qualitatively:
   - keep at least one strong result from each active lane before global ranking,
   - prefer candidates hit by multiple lanes,
   - require an evidence sentence for every S/A candidate.
4. Split results into `deep`, `quick`, `background`, and `carryover`:
   - `deep`: user should personally read or Codex should deep-read next;
   - `quick`: Codex summary is enough now;
   - `background`: useful but not active;
   - `carryover`: high-signal but not yet processed, keep it visible for the next exploration pass instead of letting daily freshness bury it.
5. For papers where figures/tables are central, inspect HTML, TeX, PDF figures, tables, or repo assets before ranking when feasible.

Do not copy these parts by default: GitHub Actions / Pages deployment, Supabase schema, remote public embedding/rerank services, front-end panels, API keys, or the exact prompt text. Keep the local skill lightweight and source-agnostic.

### Multi-Source Paper Exploration Mesh

For paper-heavy exploration, absorb `daily-paper-reader`'s paper data-source coverage rather than its hosted search/deployment stack. The key improvement is to search several paper-source lanes in parallel and then merge them with Codex's existing source stack.

Default paper lanes:

- `arXiv`: fast preprint and recent-paper recall.
- `OpenReview`: ICLR / NeurIPS / ICML / AAAI submissions, public reviews, decisions, and withdrawn-public papers when visible.
- Venue lanes: `NeurIPS`, `ICLR`, `ICML`, `ACL`, `EMNLP`, `AAAI`; use official venue pages, OpenReview, ACL Anthology, AAAI/OJS, proceedings pages, or targeted web search as appropriate.
- Domain preprint lanes: `bioRxiv`, `medRxiv`, `ChemRxiv`; use only when the topic is bio / medical / chemistry / scientific-agent adjacent.

Combine these with non-paper lanes:

- GitHub repos, release notes, project pages, Papers with Code-style project pages when available;
- official product or framework docs;
- implementation-first catalogs for agent infra;
- Social platforms and aggregators as broad recall, never as final fact sources.

Operational rule:

1. For a focused paper search, choose at least 2 relevant paper lanes plus 1 implementation or docs lane when possible.
2. For a broader paper radar, choose 3-6 lanes and keep per-lane coverage visible.
3. Do not wait for a local database or hosted search service to exist. Use official source pages, platform APIs, source-specific search, ordinary web search, and available local readers in parallel.
4. Rank by cross-lane agreement, primary-source quality, code/data availability, and direct artifact impact.
5. Record which lane found each S/A candidate and which high-value lane was checked but produced no useful hit.

If this skill has `scripts/multi_source_paper_explore.py`, use it as the first-pass paper-source recall helper for paper-heavy tasks:

```bash
python3 .codex/skills/research-material-scout/scripts/multi_source_paper_explore.py \
  --query "<topic>" \
  --query "<alternate wording or known title>" \
  --sources arxiv,openreview,openalex,biorxiv,medrxiv,chemrxiv,venue-hints
```

Repeat `--query` for intent-query expansion. Narrow `--sources` to topic-fit lanes when domain preprint servers are likely irrelevant.

Use a dual-track exploration flow for real paper-heavy work:

1. Run the script for structured paper-lane recall and per-lane evidence.
2. In parallel, run Codex's existing web / platform / GitHub / official-doc search for project pages, repos, social/aggregator leads, implementation evidence, and missed terminology.
3. Merge the two result sets before ranking. Treat script-only hits as candidates to verify, and web-only hits as leads to trace back to primary papers / code / docs.

The script is only a recall layer; it complements rather than replaces the older exploration stack.

## Authenticated Social Link Reading

Use public metadata when sufficient; for incomplete posts, replies, or signed-in search, read the installed `ego-browser` skill and follow its current TaskSpace and API contract. Do not copy stale browser methods into this skill. Reuse the user's sign-in; inspect visible posts and original links, and close only task-owned surfaces.

Capture relevant author, date, post URL, primary-source links, read scope, and the claim to verify. Avoid unrelated recommendations, DMs, account statistics, or a bulk feed dump. Inspect needed images through supported browser/media tools; do not download remote media to work around display restrictions. Store private evidence under `.local/`. A social post can be a first-party statement of its author's claim, but reported experimental results still require the paper, code, or data protocol.

## Agent-Reach Complement

Agent-Reach (`https://github.com/Panniantong/Agent-Reach`) is an optional local scaffolding layer for source-level coverage. Check its installed capabilities before relying on it.

Use it as a design reference or optional install, not the default primary source.

What it adds:

- source-level tools rather than platform-side aggregation,
- web reading through Jina Reader,
- YouTube / Bilibili transcript extraction through `yt-dlp`,
- GitHub through `gh`,
- RSS through `feedparser`,
- Reddit / Twitter / 小红书 / 抖音 / LinkedIn via separate upstream CLIs or MCP tools,
- `agent-reach doctor` style capability diagnostics.

Use it when an installed reader adds needed coverage for a specific URL, video, repo, or thread, or when search results are too summarized to verify. Prefer an existing native reader when it already covers the source.

Do not install Agent-Reach automatically unless the user asks. It may install many dependencies and configure cookies/proxies. If installed, keep secrets/cookies local and never commit them.

## Intake Workflow

Directive convention:

- `素材：<link/text>` means intake. Read, classify, summarize, preserve the original link, and append one managed candidate through exact-read evidence, immutable content backing, authority CAS, readback, and receipt.
- `调研：<question/topic>` means active research. Use broad recall plus source verification, then write high-signal candidates and recommendations.
- `整理笔记：<link/text>` or "整理笔记 + named note/theme" means direct note integration. The output surface is `Notes/`, not the candidate library by default. Named target and source-domain taxonomy win over career priority.
- `请你读 / 精读`: use the reading-only route at the top; do not run intake.
- `读完：<material id/link/title + user notes>` means close the reading loop. Update the best `Notes/` landing before archiving unless the content is private-only. Treat user-highlighted points as retention requirements: concrete prompts, env flags, schema fields, tool/API names, figures/tables, failure cases, doubts, and comparison phrases should be preserved in the public note when safe and conceptually useful; `.local` may keep raw/private/full detail, but must not be the only landing for points the user explicitly asked to remember.
- `继续调研` means continue the latest active-research theme, but only if adding new sources or a new decision-relevant synthesis.

For each user-provided material:

0. Classify the request intent before choosing tools or files:
   - `整理笔记`: use the repository note-integration workflow. If the user named a file/section, inspect that target first; if not, classify the source's primary contribution such as model algorithm, training method, inference system, agent runtime, product strategy, or career signal, then find the matching note. Do not default to Agent infra just because the material is AI-related.
   - `素材`: intake to the current managed material authority. Do not write the legacy candidate Markdown.
   - `调研`: prioritize by the user's current confirmed Decision Context.
   - `请你读 / 精读`: use the reading protocol, not the intake steps below.

### User-Highlighted Detail Preservation

When the user provides a numbered/bulleted readout, quoted phrase, prompt snippet, schema, env var, failure case, or says "这个值得作为专题section / 概念级别 / 这个点要记", treat it as first-class source material rather than optional color.

The note-writing rules below apply to `整理笔记 / 读完`. During `请你读 / 精读`, cover the user's details in the illustrated conversation answer; do not turn detail preservation into unsolicited note edits.

- Account for every explicit user point before closing the turn: either in `Notes/`, in `.local` with a privacy/version reason, or intentionally skipped with a reason reported to the user.
- Prefer distilled-but-concrete preservation in `Notes/`: short prompt excerpts or paraphrases, tool names, env flags, schema fields, benchmark names, mode names, key tables/figures, and caveats. Do not over-compress them into only an abstract framework.
- If a detail is version-sensitive or platform-specific, label it as such and preserve the source/version boundary; do not hide it solely in `.local`.
- If the user asks for a "专题section" or "概念级别", promote or create an independent section instead of burying the point under a neighboring topic.
- `.local` is for raw cache, private URLs, full prompt copies, and sensitive/internal detail. It supplements public notes; it is not a substitute for durable `Notes/` synthesis.

1. Preserve the original link in the final note title.
   - If the URL contains disposable login tokens, access tokens, auth codes, session IDs, or other sensitive query parameters, use them only for reading and persist only the stable URL with those parameters stripped. Note that the original link was sanitized.
2. Try the best reader first:
   - 微信公众号 -> `wechat-article-reader`
   - 小红书 -> `xiaohongshu-reader`
   - 飞书 / Lark -> `lark-doc` / `lark-wiki`
   - arXiv / paper -> arXiv HTML route first, abs metadata second, PDF fallback last
   - GitHub -> GitHub tools or `gh`
   - X/Twitter concrete link -> public oEmbed first, then `ego-browser` authenticated snapshot / DOM extraction if needed
   - Web pages -> official web search / browser / Playwright as needed
3. If unreadable, mark as `Unread` and ask for pasted text, screenshot, export, or accessible copy.
4. Classify into S/A/B/Unread:
   - S: user should personally read and convert into an artifact.
   - A: Codex summary is enough unless the theme becomes active.
   - B: useful background, tool lead, or product observation.
   - Unread: not read; never pretend.
5. If Material Lifecycle is active, write exact-read evidence and staged content, then use the active project source adapter documented in `.local/material-lifecycle/README.md` to intake one candidate or revise its existing stable ref. Verify an intake adds exactly one record, or a revision preserves identity, lifecycle and membership, then create the separate Decision Context-backed ranking revision in the same workflow. Verify the disposition, ranked membership when required, authority readback, readable projection, audit receipt, and rollback path before reporting completion.
6. For verified public sources, review the public fields against the current authority, body digest and complete record digest; apply and read back the public projection in the same workflow. Check both public and private partitions. Report an unresolved review/export failure instead of treating private intake alone as completion.

## Active Research Workflow

When proactively finding materials:

1. Start from the user's current goals, not generic trends.
2. For paper-heavy or recurring themes, draft a small intent-profile plan first: tags, exact keywords, semantic queries, and source lanes. Include arXiv / OpenReview / venue lanes (`NeurIPS`, `ICLR`, `ICML`, `ACL`, `EMNLP`, `AAAI`) when relevant, and add domain preprint lanes (`bioRxiv`, `medRxiv`, `ChemRxiv`) only when the topic warrants them. Then query across at least two source types when possible: paper/code/docs/social.
3. For paper-heavy tasks, run multiple selected paper-source lanes in parallel where possible, then merge them with code/docs/social/implementation lanes. Do not make a local database or hosted search service a prerequisite for exploration.
4. Prefer fewer, higher-quality materials over broad dumps. Keep per-lane coverage visible so one popular source does not crowd out a strategically important niche source.
5. For each candidate, capture:
   - title and original URL,
   - source type and read status,
   - query/profile lane that found it,
   - one-paragraph summary,
   - evidence sentence for the ranking,
   - why it matters to the user's career goal,
   - recommended action.
6. If a social/aggregator/source-search item points to a paper or repo, follow the paper/repo before ranking.
7. End with a selection split: S/A/B/Unread plus `deep / quick / background / carryover`; carryover items must have a reason and a next trigger.

## Self-Verification

For discovery/intake (reading-only checks live in the reading protocol):

1. Verify actual source coverage: which relevant lanes were read, returned no useful results, or could not be accessed. State read scope and unresolved evidence gaps; do not repeatedly probe or report an unconfigured optional service.
2. Check at least two source types for active research whenever possible, such as paper + repo, official docs + social discussion, or product page + engineering blog.
3. For every S/A candidate, include:
   - original URL,
   - read status,
   - source type,
   - query/profile lane,
   - evidence sentence,
   - why it matters to the user's current confirmed Decision Context,
   - next action.
4. Confirm the candidate stable ref exists exactly once in the current managed catalog, the immutable content backing digest verifies, and an intake receipt records CAS/readback success.
5. For `读完` / note integration, run a user-highlighted point audit: every explicit bullet, numbered item, prompt snippet, schema field, env flag, comparison phrase, or doubt from the user is either present in `Notes/`, present only in `.local` with a privacy/version reason, or intentionally skipped with a reason reported.
6. If any source could not be read, say so explicitly and ask for paste/screenshot/export only when necessary.

## Quality Bar

Reject or demote materials that are:

- pure hype without implementation detail,
- duplicate commentary on already captured material,
- unrelated to the user's current decision and learning priorities,
- not traceable to a primary source when factual claims matter.

## Output Style

For intake and note edits, report concisely what changed, where, and the key judgment. Reading explanations follow the reading protocol; concise status reporting does not set their depth.

When writing into `Notes/`:

- Use Typora-friendly block math for real equations: `$$...$$`.
- Do not put formulas in ```text code fences; reserve code fences for schemas, field lists, commands, and pseudocode.
- If a figure from the source or user-provided material is essential to understanding the mechanism, save it into the target note's relative asset folder (for example `Notes/AI-Applied-Algorithms/`) and link it with a relative Markdown path. Prefer primary-source figures when available.
- For high-value cross-layer case studies, do not create a monolithic material section by default. First extract the general mechanism into the highest-level framework section, then add only small local deltas to existing eval / memory / runtime / tooling sections. Keep the source case as evidence, not as the organizing axis.
- Preserve user-highlighted concrete details in `Notes/` when safe: prompt snippets, command/env flags, schema fields, API/tool names, mode names, version boundaries, and failure cases. Prefer short excerpts or paraphrases over long raw prompt dumps, and mark version-sensitive/platform-specific details instead of silently dropping them.

For high-value materials, include the next concrete action, such as:

- "精读并产出一页 design delta",
- "由 Codex 先读论文 PDF 并摘要",
- "只保留为产品观察",
- "转成 agent-harness TODO / benchmark idea".
