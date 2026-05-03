---
name: ai-hotspots
description: Track and synthesize current AI hotspots into a bilingual HTML daily report. Use when the user says "AI热点", asks for AI日报/AI日报 HTML/AI hot topics, or wants the best recent AI products, papers, viewpoints, and cognition-shifting items from AI/news aggregators.
---

# AI Hotspots

Use this skill to produce a high-signal AI daily report, not a raw hot-list dump.

## Trigger

When the user says `AI热点`, treat it as:

```text
Find new AI-related products, papers, viewpoints, and cognition-shifting materials from the tracked sources. Pick the best 10. If an item is longer than 1000 Chinese characters or roughly 700 English words, summarize it in <=100 Chinese characters plus the link. Return a detailed bilingual AI daily report in HTML page format.
```

Default delivery: do not paste the full HTML source into chat. Save a polished HTML report under `.local/ai-hotspots/reports/ai-daily-YYYY-MM-DD.html`, then respond with a compact Markdown digest and a file link. Paste raw HTML only if the user explicitly asks for source code.

If the user asks to schedule it every morning, create an automation only after the wake-up time is clear.

## Sources

Read `references/source-list.md` for the default source set and source roles.

Use the listed aggregators as discovery surfaces. For factual or technical claims, follow primary sources before ranking when possible:

- product pages, launch posts, docs, release notes;
- papers, arXiv pages, conference pages;
- official repos, issues, PRs, changelogs;
- original interviews or first-party engineering blogs.

Do not treat social posts or aggregator summaries as final truth.

## Selection Rules

Pick exactly 10 items unless the user asks for another count. Prefer:

- new products or features with credible adoption or differentiated UX;
- papers/repos that change agent infra, model behavior, evaluation, memory, RL, inference, or developer tooling;
- sharp viewpoints from credible builders/researchers;
- cognition updates that alter how the user should think, build, evaluate, or invest attention.

Rank for the user's current priorities:

1. Agent infra, coding agents, memory/context/runtime/eval.
2. RL infra, agent runner, rollout/replay/reward.
3. LLM serving constraints for agent runtime, vLLM, SGLang, Ray, verl.
4. AI product interfaces and RecSys/search + LLM.

Demote items that are only funding/news hype, duplicate commentary, thin product marketing, or unverifiable rumor.

## Workflow

1. Check the current date and browse live sources; this skill depends on recent information.
2. Scan at least two different source types when possible: aggregator + primary source, paper + repo, product page + social reaction.
3. Deduplicate the same event across sources and keep the strongest original link.
4. Classify each candidate as Product, Paper, Viewpoint, Cognition, Tool/Repo, or Company/Market.
5. For long articles, write a <=100 Chinese character summary and keep the original link.
6. Produce a polished HTML document as a local file, then answer with a short Markdown digest: top 5 items, 3 trends, 1-3 actions, report path, and unread/access-blocked notes.

## HTML Output Contract

Create a complete HTML page. Keep it readable as a standalone browser page, not as a code snippet in chat.

Required sections:

- title: `AI Daily / AI 日报 - YYYY-MM-DD`;
- metadata: generated time, source window, source coverage, unread/access-blocked notes;
- top 10 list: each item has rank, category, Chinese title, English title, source link, why it matters, bilingual summary, and suggested action;
- pattern synthesis: 3-5 cross-item trends;
- user's action queue: 1-3 concrete next actions mapped to the user's Agent infra career line.

Visual requirements:

- Use a restrained editorial layout: max-width content, clear hero, compact metadata, two-column desktop cards that become one column on narrow screens.
- Each item card should expose rank, category, source, one-line Chinese judgment, short English note, and action. Avoid dense paragraphs.
- Use neutral background, white cards, thin borders, and one accent color. Do not use raw tables for the main report.
- Include a small source coverage block at the bottom so unread sources do not pollute the main reading flow.
- Make links visible and scannable with source names, not bare URLs.

Use concise Chinese first, English second. Do not pad bilingual text if English adds no value; translate the core judgment, not every word mechanically.

## Persistence

If the report includes materials that deserve later reading, also add them to `.local/LEARNING_MATERIAL_CANDIDATES.md` using the existing S/A/B/Unread convention from the research material workflow.

If access fails, mark the source or item as unread. Never pretend a source was read.
