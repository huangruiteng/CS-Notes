---
name: research-material-scout
description: Use when the user asks Codex to research, find learning materials, process "素材：" links, "请你读" / "精读" a material, build a material radar, or use SenSight-like broad information retrieval for career learning and Agent infra tracking. Do not use the career/Agent-infra routing bias for user-directed `整理笔记` into a named note.
---

# Research Material Scout

Use this skill when the user asks for research, material discovery, learning-material triage, or sends links with the `素材：` prefix. Treat `调研：` as the explicit active-research directive.

## Mission

Build a high-signal learning and career material pipeline for the user.

The material pipeline serves the user's broader career development goal, not a single artifact. The current north star is to position the user as an LLM / Agent infra engineer at the intersection of RecSys, ToB platform work, benchmark/eval, and agent memory-context-runtime systems.

This career north star applies to `素材：`, `调研：`, material radar, Top30, and career-learning prioritization. It must not override user-directed note integration. When the user says `整理笔记`, names a note such as `AI-Algorithms`, or points to a specific section/theme, route by the user's target and the source material's primary domain before considering Agent infra / career mapping.

The user's current priority stack:

1. Agent infra / Agent Harness / OpenClaw / ArkClaw / OpenViking / agent memory.
2. RL infra / agent runner bridge / verl / Ray rollout / agentic RL.
3. Inference serving anchor / vLLM / SGLang / agent workload serving constraints.
4. RecSys + LLM / search and recommendation infra as a differentiating background.
5. Career narrative / interview deep dives / market sensing / personal technical taste and distribution.

## Source Strategy

Prefer primary sources for technical conclusions:

- Papers: arXiv, conference pages, official PDFs.
- Code: GitHub repositories, README, issues, releases.
- Products: official docs, release notes, engineering blogs.
- Internal/user links: Lark/ByteTech only when accessible through user-provided context or approved local tools.

Use social media, 微信公众号, 小红书, X/Twitter, 微博, and aggregators as discovery signals, not final truth.

When extracting mechanisms from a repo, quickstart, prompt, or code file, include file-level links in the user-facing answer and persisted notes/archive. For GitHub sources, prefer commit-pinned permalinks and record the commit read; avoid writing only a repo name or bare filename when a concrete source file drove the claim.

Use SenSight as the primary broad-recall backend when it is available:

- recent AI/Agent/RL/serving dynamics,
- social-platform opinions,
- author/researcher recent posts,
- link reading across 微信公众号 / 小红书 / X / 微博,
- keyword monitoring.

Codex remains responsible for verification, ranking, summarization, and local persistence.

Use ordinary web search, platform-specific readers, and Agent-Reach-like local tools as fallback or source-level readers, not as the primary discovery layer.

### Implementation-First Catalogs

For Agent Harness / agent infra exploration, use implementation-first catalogs as a source-discovery layer before broad web search when available.

Current primary catalog:

- `Agent Harness Engineering implementation-first catalog`: `https://github.com/Picrew/awesome-agent-harness`

Use it as an index, not as evidence by itself:

1. Pick the relevant ETCLOVG layer first: execution, tooling, context, lifecycle, observability, verification, or governance.
2. Inspect the candidate repo's README, docs, releases, issues, or paper before ranking it.
3. Prefer implementation entries that can change the user's artifacts: sandbox boundary, tool registry/schema, state/context contract, handoff/workflow loop, trace/eval schema, policy/audit layer.
4. Do not dump many frameworks into Top30. Write only high-signal projects into `.local/LEARNING_MATERIAL_CANDIDATES.md`, with read status and concrete artifact deltas.
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

### Paper / Research Reading Protocol

For papers, research reports, benchmark papers, method repos, arXiv / OpenReview links, and paper collections, `请你读` / `精读` must use the protocol in `references/paper-reading-protocol.md`.

Use it as a progressive-disclosure reference rather than copying it into every answer. It synthesizes Keshav's three-pass method, CMU 11-785's paper-reading recitation, and academic / PhD / AI research lenses into a concrete output contract, plus selected ideas from a local scan of research-related skills.

Operational defaults:

- `请你读` = read first, then answer with Keshav pass 1 plus targeted pass 2 on decision-relevant sections; escalate selected parts to pass 3 only when the material is high-value.
- `精读` = same output schema, but default to pass 2 plus selective pass 3: virtually reimplement the method, challenge assumptions, and produce artifact deltas.
- For paper radars or collections, first triage all visible papers with pass 1, then deep-read only the highest-leverage subset.
- Always state what was actually read: HTML, TeX source, PDF, repo paths, figures/tables, appendix, code, or only metadata.

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
- SenSight / social / aggregators as broad recall, never as final fact sources.

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
2. In parallel, run Codex's existing web / SenSight / GitHub / official-doc search for project pages, repos, social/aggregator leads, implementation evidence, and missed terminology.
3. Merge the two result sets before ranking. Treat script-only hits as candidates to verify, and web-only hits as leads to trace back to primary papers / code / docs.

The script is only a recall layer; it complements rather than replaces the older exploration stack.

## SenSight Backend

The SenSight OpenClaw skill has been downloaded locally for Codex adaptation:

```text
/Users/bytedance/CS-Notes/.local/sensight-skill-source/sensight
```

This source directory is private and ignored by git. It contains:

```text
SKILL.md
scripts/sensight.py
scripts/auth.py
scripts/init.sh
scripts/calc_time.sh
references/workflows.md
references/author-posts-guide.md
references/daily-pulse-filters.md
```

Before using SenSight, check that the directory exists. If missing, install it into the private cache, not global OpenClaw:

```bash
# Use an approved private skill source, then install into the ignored local cache.
<private-skill-installer> --skill sensight --dir /Users/bytedance/CS-Notes/.local/sensight-skill-source
```

Run SenSight commands from its source directory:

```bash
cd /Users/bytedance/CS-Notes/.local/sensight-skill-source/sensight
python3 scripts/sensight.py <action> [args]
```

If the command returns an auth-required response, do not treat it as data. Tell the user SenSight needs one-time device authorization and wait for confirmation before retrying. Do not expose internal API endpoints, raw service JSON, client IDs, or stale auth URLs in final answers.

### Useful Actions

Use these actions as retrieval, not as final authority:

| Need | SenSight action |
| --- | --- |
| AI industry deep dive / high-quality articles | `retrieve_summarize` |
| Latest AI papers | `daily_paper` |
| Latest AI/company technical blogs | `daily_blog` |
| Weekly model releases | `weekly_model` |
| Model reputation / user sentiment | `model_sentiment` |
| Hot events, general news, trend search | `search_events` |
| Platform hot lists | `get_event_board` |
| Social semantic search across X/小红书/微博/公众号 | `social_search` |
| Recent posts from a specific author/account | `search_author_posts` |

Examples:

```bash
python3 scripts/sensight.py retrieve_summarize \
  --query "Agent infra 最新进展" \
  --enhance_query "最近一周 Agent infra、OpenClaw、Claude Code、agent memory、long-running coding agent 的高质量技术动态" \
  --size 20 \
  --result_form article_summary

python3 scripts/sensight.py social_search \
  --query "GPT 5.4 评价" \
  --platforms 1 2 3 4 \
  --size 20

python3 scripts/sensight.py search_author_posts \
  --platform 1 \
  --author_name "Anthropic"
```

Known limitation from the downloaded version: the local source currently reports `version: 0.3.1`, while the user-provided article mentions `0.3.2` with direct social-link reading. If direct link reading is needed and unavailable, fall back to existing Codex readers (`wechat-article-reader`, `xiaohongshu-reader`, browser/web tools) and note the version gap.

## Authenticated Social Link Reading

For concrete X/Twitter links, use a layered route before marking the material unread:

1. Try lightweight public metadata first:
   - `https://publish.twitter.com/oembed?omit_script=1&url=<encoded-url>` for author, timestamp, and main post text.
   - `https://cdn.syndication.twimg.com/tweet-result?id=<tweet-id>&lang=en` only as a best-effort fallback; it often returns `{}`.
2. If public metadata is incomplete, use `ego-browser` because it can reuse the user's logged-in browser state. Open the original URL in a task space, run `snapshotText()` for accessible text, and then use one `js(String.raw\`...\`)` extraction over `document.querySelectorAll("article")` to capture visible post/reply text, links, and image nodes.
3. For X images, the visible media may appear as a background image or as an image only on `/photo/1`. Use browser-side DOM inspection to find `pbs.twimg.com/media/...` URLs. If shell `curl` is reset, retry with Python `urllib` plus `User-Agent` and `Referer: https://x.com/`.
4. Store screenshots/media only under ignored local cache paths such as `.local/source-cache/x-materials/`; do not put social screenshots into public `Notes/` unless the user explicitly asks and the content is safe to publish.
5. Treat X content as social/product signal unless it points to a primary source. For technical claims, follow links to papers, repos, official docs, release notes, or author long-form posts before ranking as S/A.

## Agent-Reach Complement

Agent-Reach (`https://github.com/Panniantong/Agent-Reach`) is useful as a complementary local scaffolding layer, especially when SenSight is unavailable, too aggregated, or lacks a channel.

Use it as a design reference or optional install, not the default primary source.

What it adds:

- source-level tools rather than platform-side aggregation,
- web reading through Jina Reader,
- YouTube / Bilibili transcript extraction through `yt-dlp`,
- GitHub through `gh`,
- RSS through `feedparser`,
- Reddit / Twitter / 小红书 / 抖音 / LinkedIn via separate upstream CLIs or MCP tools,
- `agent-reach doctor` style capability diagnostics.

When it helps more than SenSight:

- Need to inspect a specific URL/video/repo/thread, not just discover candidates.
- Need an open-source, auditable local route.
- Need video subtitles, RSS feeds, GitHub issues/PRs, or Reddit threads.
- SenSight auth is unavailable or results are too summarized.

When SenSight should stay primary:

- Broad topic discovery.
- Recent social sentiment.
- Cross-platform opinion summaries.
- AI papers/blogs/model-release radar.
- Low-maintenance material scouting.

Do not install Agent-Reach automatically unless the user asks. It may install many dependencies and configure cookies/proxies. If installed, keep secrets/cookies local and never commit them.

## Intake Workflow

Directive convention:

- `素材：<link/text>` means intake. Read, classify, summarize, preserve the original link, and write to the candidate library.
- `调研：<question/topic>` means active research. Use broad recall plus source verification, then write high-signal candidates and recommendations.
- `整理笔记：<link/text>` or "整理笔记 + named note/theme" means direct note integration. The output surface is `Notes/`, not the candidate library by default. Named target and source-domain taxonomy win over career priority.
- `请你读：<material id/link/title>` means Codex reads first, then returns both a mechanism-first summary and a reader map for the user. For papers / research artifacts, load `references/paper-reading-protocol.md` and follow its output contract. `精读` is a compatibility alias with the same output requirements, but defaults to deeper pass-3 reconstruction when the material warrants it.
- `继续调研` means continue the latest active-research theme, but only if adding new sources or a new decision-relevant synthesis.

For each user-provided material:

0. Classify the request intent before choosing tools or files:
   - `整理笔记`: use the repository note-integration workflow. If the user named a file/section, inspect that target first; if not, classify the source's primary contribution such as model algorithm, training method, inference system, agent runtime, product strategy, or career signal, then find the matching note. Do not default to Agent infra just because the material is AI-related.
   - `素材`: intake to `.local/LEARNING_MATERIAL_CANDIDATES.md`.
   - `调研`: prioritize by the user's 70/20/10 career plan.
   - `请你读 / 精读`: read first, then decide whether the result should be summarized only, integrated into notes, or later archived.

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
5. Write the result into `.local/LEARNING_MATERIAL_CANDIDATES.md`.

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

Before reporting that a research task is done:

1. Verify the retrieval backend state:
   - paper-source lanes checked, skipped as not relevant, or unavailable;
   - SenSight result received, or
   - SenSight auth-blocked and fallback source path used, or
   - SenSight not relevant for this specific URL/material.
2. Check at least two source types for active research whenever possible, such as paper + repo, official docs + social discussion, or product page + engineering blog.
3. For every S/A candidate, include:
   - original URL,
   - read status,
   - source type,
   - query/profile lane,
   - evidence sentence,
   - why it matters to the user's 70/20/10 career plan,
   - next action.
4. Run a local search to confirm the candidate entry exists in `.local/LEARNING_MATERIAL_CANDIDATES.md`.
5. For `请你读` / `精读`, check the final answer follows `references/paper-reading-protocol.md` when the material is a paper or research artifact, and contains a concrete "用户本人还需要读什么" reader map. If the answer is "不用读原文", still say which sections were inspected and why they are skippable, and provide a richer substitute-quality digest so the user does not lose meaningful value by skipping the original.
6. For tool / standard / API / framework bundles, check that the answer starts with background and workflow introduction: why this thing exists, what pain it solves, what breaks without it, and how each component is positioned. Then explain each component as a standalone material before mapping to Agent Harness / OpenViking. Do not start directly from jargon, fields, or claim maps, and do not let the project mapping crowd out the source-content explanation.
7. If any source could not be read, say so explicitly and ask for paste/screenshot/export only when necessary.

## Quality Bar

Reject or demote materials that are:

- pure hype without implementation detail,
- duplicate commentary on already captured material,
- unrelated to the user's current 70/20/10 priority split,
- not traceable to a primary source when factual claims matter.

## Output Style

Be concise. Tell the user what was added, where it was added, and the key judgment.

When writing into `Notes/`:

- Use Typora-friendly block math for real equations: `$$...$$`.
- Do not put formulas in ```text code fences; reserve code fences for schemas, field lists, commands, and pseudocode.
- If a figure from the source or user-provided material is essential to understanding the mechanism, save it into the target note's relative asset folder (for example `Notes/AI-Applied-Algorithms/`) and link it with a relative Markdown path. Prefer primary-source figures when available.
- For high-value cross-layer case studies, do not create a monolithic material section by default. First extract the general mechanism into the highest-level framework section, then add only small local deltas to existing eval / memory / runtime / tooling sections. Keep the source case as evidence, not as the organizing axis.

For `请你读` / `精读`, Codex should read first and then provide a mechanism-first guide rather than a broad reading plan. Because personal original-reading recommendations are conservative, `Codex-summary-enough` answers must be more detailed, not thinner: include enough background, source-content explanation, core design, fields/schemas, evidence, artifact mapping, and caveats to substitute for the user's first-pass read. Use a two-focus structure: first explain the material itself, then map it to the user's current artifact. For papers / research artifacts, load `references/paper-reading-protocol.md`; the short form below is the minimum answer shape:

1. 一句话判断.
2. 背景和工作流介绍: why this material exists, what pain it solves, and where it sits in the broader ecosystem.
3. 我实际读了什么: HTML/PDF/repo/code/figures/tables/appendix, plus unread parts.
4. 原材料内容卡: for each paper/tool/standard/repo in the bundle, explain its standalone purpose, core abstraction, important fields/APIs, common usage, and limits.
5. Claim map: main claims, evidence, confidence, and what would make each claim false.
6. 精要内容和核心设计: problem, boundary, input/output, data/interface format, workflow, metrics, baselines, main results, limitations, and key figure/table/code path.
7. 核心机制: 3-6 numbered mechanisms, each with "what the author does/proves" and "how the user should interpret it".
8. 对用户 artifact 的直接改造: schema, feedback signal, benchmark variant, TODO, steering, or interview/deep-dive line.
9. 用户本人还需要读什么: mandatory reader map with concrete original sections, figures, tables, code paths, and a decision for each: `must-read`, `optional`, or `skippable`. Do not only say "读摘要即可"; name the exact parts that justify that decision.
10. 边读边核验的问题: 3-6 sharp checks, especially leakage, counterfactual reliability, metric validity, transferability to Agent Harness / TAU2.
11. Do not archive during `请你读` / `精读`; archive only after the user says `读完`.

For high-value materials, include the next concrete action, such as:

- "精读并产出一页 design delta",
- "由 Codex 先读论文 PDF 并摘要",
- "只保留为产品观察",
- "转成 agent-harness TODO / benchmark idea".
