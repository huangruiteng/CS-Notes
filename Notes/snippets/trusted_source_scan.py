#!/usr/bin/env python3
"""Plan a trusted-source material scan from the local source snapshot.

This helper does not claim to read sources. It selects the next sources to
inspect, records the correct access route, and emits a reusable scan report
template. The actual reading still happens through web/GitHub/platform readers
and must be written back to LEARNING_MATERIAL_CANDIDATES.md with read status.
"""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Iterable


REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SOURCES = REPO_ROOT / ".local" / "TRUSTED_MATERIAL_SOURCES.json"
DEFAULT_SCAN_REPORT = REPO_ROOT / ".local" / f"TRUSTED_SOURCE_SCAN_PLAN_{date.today():%Y%m%d}.md"


@dataclass
class Source:
    name: str
    category: str
    url: str
    platform: str
    access_level: str
    material_priority: str
    line: int
    fallback: str

    @classmethod
    def from_dict(cls, data: dict) -> "Source":
        return cls(
            name=str(data.get("name", "")),
            category=str(data.get("category", "")),
            url=str(data.get("url", "")),
            platform=str(data.get("platform", "")),
            access_level=str(data.get("access_level", "")),
            material_priority=str(data.get("material_priority", "")),
            line=int(data.get("line", 0) or 0),
            fallback=str(data.get("fallback", "")),
        )


PLATFORM_ROUTES = {
    "blog": "Open the latest/archive page, then verify with the article permalink and author page.",
    "github": "Inspect README, releases, issues, and recent commits; prefer primary docs over social summaries.",
    "official_docs": "Read official docs/release notes and record version/date.",
    "seminar": "Read event pages/slides when available; do not treat a talk as read without notes or transcript.",
    "juejin": "Use article reader/browser; preserve permalink and read status.",
    "web": "Use browser/web search to locate the stable article, docs, or category page.",
    "youtube": "Inspect title/description/transcript first; if no transcript, mark metadata-only.",
    "bilibili": "Inspect title/description/subtitles first; if no subtitles, mark metadata-only.",
    "zhihu": "Use browser/reader; if login blocks content, mark Unread and ask for export.",
    "wechat": "Use wechat-article-reader/search; if blocked, ask for pasted text/export.",
    "xiaohongshu": "Use xiaohongshu-reader/share link; if no stable URL, ask user for a share link.",
}


def load_sources(path: Path) -> list[Source]:
    data = json.loads(path.read_text(encoding="utf-8"))
    return [Source.from_dict(item) for item in data]


def normalize_terms(topic: str) -> list[str]:
    return [term for term in re.split(r"[\s,;/|]+", topic.lower()) if term]


def source_text(source: Source) -> str:
    return " ".join([
        source.name,
        source.category,
        source.platform,
        source.access_level,
        source.url,
        source.fallback,
    ]).lower()


def priority_rank(priority: str) -> int:
    match = re.search(r"\d+", priority)
    return int(match.group(0)) if match else 99


def select_sources(
    sources: Iterable[Source],
    topic: str,
    priorities: set[str],
    limit: int,
    include_blocked: bool,
) -> list[Source]:
    terms = normalize_terms(topic)
    selected = []
    for source in sources:
        if priorities and source.material_priority not in priorities:
            continue
        if not include_blocked and source.access_level in {"reader_or_user_export", "login_or_browser_may_be_needed"}:
            continue
        if terms and not any(term in source_text(source) for term in terms):
            continue
        selected.append(source)

    selected.sort(key=lambda s: (priority_rank(s.material_priority), s.category, s.name))
    return selected[:limit]


def route_for(source: Source) -> str:
    return PLATFORM_ROUTES.get(source.platform, source.fallback or "Inspect access path before claiming read status.")


def render_markdown(sources: list[Source], topic: str) -> str:
    today = date.today().isoformat()
    lines = [
        f"# Trusted Source Scan Plan {today}",
        "",
        f"Topic filter: `{topic or 'none'}`",
        "",
        "Purpose: pick trusted sources to inspect next. This file is a scan plan, not a reading result. Only after a source is actually opened/read should it become an S/A/B/Unread entry in `.local/LEARNING_MATERIAL_CANDIDATES.md`.",
        "",
        "## Selected Sources",
        "",
    ]
    if not sources:
        lines.append("No sources matched the filter.")
        return "\n".join(lines) + "\n"

    for idx, source in enumerate(sources, start=1):
        url = source.url or "no stable URL in note"
        lines.extend([
            f"### {idx}. {source.name}",
            "",
            f"- priority/category: {source.material_priority} / {source.category}",
            f"- platform/access: {source.platform} / {source.access_level}",
            f"- source: {url}",
            f"- route: {route_for(source)}",
            f"- fallback: {source.fallback}",
            "- candidate decision after reading: `S/A/B/Unread`",
            "- candidate writeback template:",
            "",
            "```markdown",
            f"#### <S/A/B/Unread>. {source.name}: <material title>（<stable original link>）",
            "",
            "来源状态：",
            "",
            "- <已读正文 / 只读摘要 / metadata-only / unread reason>",
            f"- trusted source: {source.name}; platform: {source.platform}; access: {source.access_level}",
            "",
            "摘要：",
            "",
            "- <1-3 bullets>",
            "",
            "判断：",
            "",
            "- <why this matters for Agent infra / MLSys / career artifact>",
            "",
            "后续动作：",
            "",
            "- <artifact/checklist/schema/reading action>",
            "```",
            "",
        ])
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--sources", type=Path, default=DEFAULT_SOURCES)
    parser.add_argument("--topic", default="", help="Filter terms, matched against name/category/platform/fallback/url.")
    parser.add_argument("--priorities", default="P0,P1", help="Comma-separated priorities. Empty means all.")
    parser.add_argument("--limit", type=int, default=5)
    parser.add_argument("--include-blocked", action="store_true", help="Include sources that likely need login/export.")
    parser.add_argument("--output", type=Path, default=None)
    args = parser.parse_args()

    priorities = {item.strip() for item in args.priorities.split(",") if item.strip()}
    sources = load_sources(args.sources)
    selected = select_sources(
        sources=sources,
        topic=args.topic,
        priorities=priorities,
        limit=args.limit,
        include_blocked=args.include_blocked,
    )
    rendered = render_markdown(selected, args.topic)
    output = args.output
    if output:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(rendered, encoding="utf-8")
    else:
        print(rendered)


if __name__ == "__main__":
    main()
