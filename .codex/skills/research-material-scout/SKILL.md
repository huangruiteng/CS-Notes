---
name: research-material-scout
description: Use when the user asks Codex to research, find learning materials, process "素材：" links, "精读" a material, build a material radar, or use SenSight-like broad information retrieval for career learning and Agent infra tracking.
---

# Research Material Scout

Use this skill when the user asks for research, material discovery, learning-material triage, or sends links with the `素材：` prefix. Treat `调研：` as the explicit active-research directive.

## Mission

Build a high-signal learning and career material pipeline for the user.

The material pipeline serves the user's broader career development goal, not a single artifact. The current north star is to position the user as an LLM / Agent infra engineer at the intersection of RecSys, ToB platform work, benchmark/eval, and agent memory-context-runtime systems.

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

Use SenSight as the primary broad-recall backend when it is available:

- recent AI/Agent/RL/serving dynamics,
- social-platform opinions,
- author/researcher recent posts,
- link reading across 微信公众号 / 小红书 / X / 微博,
- keyword monitoring.

Codex remains responsible for verification, ranking, summarization, and local persistence.

Use ordinary web search, platform-specific readers, and Agent-Reach-like local tools as fallback or source-level readers, not as the primary discovery layer.

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
4. Fall back to PDF only when HTML is missing, blocked, malformed, or lacks the needed figures/tables.
5. If using PDF fallback, extract text into `.local/paper-cache/` and explicitly say that the read path was PDF fallback.

Why this matters:

- arXiv HTML preserves section anchors, table/figure order, equation context, and is easier for user-side parallel reading.
- PDF extraction can lose figures, captions, math, and table structure; it is acceptable for quick scanning but weaker for `精读`.
- For `精读`, always provide the user-facing HTML link when it exists, even if Codex also used the PDF for extraction.

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
npx -y --registry https://bnpm.byted.org @tiktok-fe/skills add zengduju/skills \
  --skill sensight --source local --dir /Users/bytedance/CS-Notes/.local/sensight-skill-source
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
- `继续调研` means continue the latest active-research theme, but only if adding new sources or a new decision-relevant synthesis.

For each user-provided material:

1. Preserve the original link in the final note title.
2. Try the best reader first:
   - 微信公众号 -> `wechat-article-reader`
   - 小红书 -> `xiaohongshu-reader`
   - 飞书 / Lark -> `lark-doc` / `lark-wiki`
   - arXiv / paper -> arXiv HTML route first, abs metadata second, PDF fallback last
   - GitHub -> GitHub tools or `gh`
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
2. Query across at least two source types when possible: paper/code/docs/social.
3. Prefer fewer, higher-quality materials over broad dumps.
4. For each candidate, capture:
   - title and original URL,
   - source type and read status,
   - one-paragraph summary,
   - why it matters to the user's career goal,
   - recommended action.
5. If a social/aggregator item points to a paper or repo, follow the paper/repo before ranking.

## Self-Verification

Before reporting that a research task is done:

1. Verify the retrieval backend state:
   - SenSight result received, or
   - SenSight auth-blocked and fallback source path used, or
   - SenSight not relevant for this specific URL/material.
2. Check at least two source types for active research whenever possible, such as paper + repo, official docs + social discussion, or product page + engineering blog.
3. For every S/A candidate, include:
   - original URL,
   - read status,
   - source type,
   - why it matters to the user's 70/20/10 career plan,
   - next action.
4. Run a local search to confirm the candidate entry exists in `.local/LEARNING_MATERIAL_CANDIDATES.md`.
5. If any source could not be read, say so explicitly and ask for paste/screenshot/export only when necessary.

## Quality Bar

Reject or demote materials that are:

- pure hype without implementation detail,
- duplicate commentary on already captured material,
- unrelated to the user's current 70/20/10 priority split,
- not traceable to a primary source when factual claims matter.

## Output Style

Be concise. Tell the user what was added, where it was added, and the key judgment.

For `精读`, use a mechanism-first guide rather than a broad reading plan:

1. 一句话判断.
2. 核心机制: 3-6 numbered mechanisms, each with "what the author does/proves" and "how the user should interpret it".
3. 对用户 artifact 的直接改造: schema, feedback signal, benchmark variant, TODO, steering, or interview/deep-dive line.
4. 边读边核验的问题: 3-6 sharp checks, especially leakage, counterfactual reliability, metric validity, transferability to Agent Harness / TAU2.
5. 阅读路径 only if needed; do not default to a 30/60/90 plan.
6. Do not archive during `精读`; archive only after the user says `读完`.

For high-value materials, include the next concrete action, such as:

- "精读并产出一页 design delta",
- "由 Codex 先读论文 PDF 并摘要",
- "只保留为产品观察",
- "转成 agent-harness TODO / benchmark idea".
