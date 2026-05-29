#!/usr/bin/env python3
"""Extract trusted material sources from Notes/非技术知识.md.

The source list is used as a trusted discovery layer for learning-material
scouting. This script only parses and classifies sources; it does not fetch
articles or require platform credentials.
"""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable


DEFAULT_NOTES = Path(__file__).resolve().parents[1] / "非技术知识.md"


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


SOURCE_OVERRIDES = {
    "GPU-Mode Channel": {
        "url": "https://www.youtube.com/channel/UCJgIbYl6C5no72a0NUAPcTA",
        "platform": "youtube",
        "fallback": "Also inspect https://github.com/gpu-mode for code/resources; use video transcript tooling before treating talks as read.",
    },
    "GPU MODE": {
        "url": "https://www.youtube.com/channel/UCJgIbYl6C5no72a0NUAPcTA",
        "platform": "youtube",
        "fallback": "Also inspect https://github.com/gpu-mode for code/resources; use video transcript tooling before treating talks as read.",
    },
    "ez-encoder": {
        "url": "https://ez-encoder-academy.gitbook.io/my-ai-journey",
        "platform": "blog",
        "fallback": "Use the GitBook as canonical profile; Bilibili Ilya Top 30 videos can be discovered by querying ez-encoder + Ilya Top 30.",
    },
    "zartbot 公众号": {
        "platform": "wechat",
        "fallback": "No stable public URL in note. Use WeChat reader/search; if blocked, ask user for article text/export.",
    },
    "大猿搬砖日记 公众号": {
        "platform": "wechat",
        "fallback": "No stable public URL in note. Use WeChat reader/search; if blocked, ask user for article text/export.",
    },
    "王焱": {
        "platform": "xiaohongshu",
        "fallback": "No stable Xiaohongshu profile URL in note. Use xiaohongshu-reader/search if available; otherwise ask user for a share link.",
    },
}


ALIASES = {
    "Channel": "PyTorch Channel",
    "Dev Discuss": "PyTorch Dev Discuss",
}


def apply_source_overrides(name: str, url: str, platform: str, fallback: str) -> tuple[str, str, str, str]:
    name = ALIASES.get(name, name)
    override = SOURCE_OVERRIDES.get(name)
    if not override:
        return name, url, platform, fallback
    url = override.get("url", url)
    platform = override.get("platform", platform)
    fallback = override.get("fallback", fallback)
    return name, url, platform, fallback


def detect_platform(name: str, url: str, raw: str) -> str:
    text = f"{name} {url} {raw}".lower()
    if "bilibili.com" in text or "b站" in raw:
        return "bilibili"
    if "youtube.com" in text or "youtu.be" in text:
        return "youtube"
    if "github.com" in text:
        return "github"
    if "zhihu.com" in text or "知乎" in raw:
        return "zhihu"
    if "xiaohongshu" in text or "xhs" in text or "小红书" in raw:
        return "xiaohongshu"
    if "juejin.cn" in text:
        return "juejin"
    if "kexue.fm" in text or "lilianweng.github.io" in text or "blog" in text:
        return "blog"
    if "volcengine.com" in text:
        return "official_docs"
    if "公众号" in raw or "vx" in raw.lower():
        return "wechat"
    if "seminar" in text:
        return "seminar"
    return "web"


def classify_access(platform: str, url: str) -> tuple[str, str]:
    if platform in {"blog", "github", "official_docs", "seminar", "juejin"}:
        return "auto_readable", "Use web/GitHub/RSS reader first; verify primary links before ranking."
    if platform in {"youtube", "bilibili"}:
        return "metadata_or_transcript", "Use video metadata/transcript tooling; fallback to user-provided notes when subtitles fail."
    if platform == "zhihu":
        return "login_or_browser_may_be_needed", "Use browser/reader; mark Unread if blocked by login or anti-bot."
    if platform in {"wechat", "xiaohongshu"}:
        return "reader_or_user_export", "Use platform reader if available; otherwise ask for pasted text, screenshots, or export."
    return "manual_check", "Inspect source-specific access path before claiming read status."


def priority_for(category: str, name: str, platform: str) -> str:
    high_signal = {
        "Lilian Wang",
        "GPU-Mode Channel",
        "InfiniTensor 大咖课、论文分享",
        "硬核课堂",
        "EzYang Blog",
        "FAI Seminar",
        "苏剑林",
        "火山引擎 V-Moment",
        "字节（知乎）",
    }
    if name in high_signal:
        return "P0"
    if category in {"MLSys", "ML 算法", "AI 编程 & 效率工具"}:
        return "P1"
    if category in {"商业、AI 产品", "ToB、云原生"}:
        return "P2"
    return "P3"


def clean_name(text: str) -> str:
    text = re.sub(r"\[[^\]]+\]\([^)]+\)", lambda m: m.group(0).split("](")[0][1:], text)
    text = re.sub(r"https?://\S+", "", text)
    text = text.replace("**", "")
    text = re.split(r"[：:，,（(【\\[]", text, maxsplit=1)[0]
    return text.strip(" -*\t")


def extract_urls(text: str) -> list[str]:
    urls = re.findall(r"https?://[^\s)）]+", text)
    md_urls = re.findall(r"\[[^\]]+\]\((https?://[^)]+)\)", text)
    ordered = []
    for url in md_urls + urls:
        if url not in ordered:
            ordered.append(url)
    return ordered


def extract_md_names(text: str) -> list[str]:
    return [name.strip() for name in re.findall(r"\[([^\]]+)\]\(https?://[^)]+\)", text)]


def source_like_without_url(line: str) -> bool:
    markers = [
        "公众号",
        "小红书",
        "Channel",
        "Blog",
        "Seminar",
        "社区",
        "知乎",
    ]
    if any(marker in line for marker in markers):
        return True
    if re.search(r"\*\*[^*]+\*\*", line):
        return True
    return False


def iter_sustained_attention_lines(path: Path) -> Iterable[tuple[int, str, str]]:
    category = ""
    in_section = False
    skip_lower_heading = False
    for line_no, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        stripped = raw.strip()
        if stripped.startswith("### 持续关注"):
            in_section = True
            continue
        if in_section and re.match(r"^###\s+", stripped) and not stripped.startswith("### 持续关注"):
            break
        if not in_section:
            continue
        if re.match(r"^####\s+", stripped):
            category = re.sub(r"^#+\s*", "", stripped).strip()
            skip_lower_heading = False
            continue
        if re.match(r"^#####\s+", stripped):
            skip_lower_heading = True
            continue
        if skip_lower_heading:
            continue
        if not stripped.startswith("*"):
            continue
        yield line_no, category, stripped


def parse_sources(path: Path) -> list[Source]:
    sources: list[Source] = []
    seen: set[tuple[str, str]] = set()
    for line_no, category, line in iter_sustained_attention_lines(path):
        urls = extract_urls(line)
        md_names = extract_md_names(line)
        if urls:
            for idx, url in enumerate(urls):
                name = md_names[idx] if idx < len(md_names) else clean_name(line)
                if not name:
                    name = url
                platform = detect_platform(name, url, line)
                access, fallback = classify_access(platform, url)
                name, url, platform, fallback = apply_source_overrides(name, url, platform, fallback)
                access, default_fallback = classify_access(platform, url)
                if fallback == default_fallback:
                    _, fallback = classify_access(platform, url)
                key = (name, url)
                if key in seen:
                    continue
                seen.add(key)
                sources.append(Source(
                    name=name,
                    category=category or "未分类",
                    url=url,
                    platform=platform,
                    access_level=access,
                    material_priority=priority_for(category, name, platform),
                    line=line_no,
                    fallback=fallback,
                ))
        elif source_like_without_url(line):
            name = clean_name(line)
            if not name:
                continue
            platform = detect_platform(name, "", line)
            access, fallback = classify_access(platform, "")
            name, url, platform, fallback = apply_source_overrides(name, "", platform, fallback)
            access, _ = classify_access(platform, url)
            key = (name, "")
            if key in seen:
                continue
            seen.add(key)
            sources.append(Source(
                name=name,
                category=category or "未分类",
                url=url,
                platform=platform,
                access_level=access,
                material_priority=priority_for(category, name, platform),
                line=line_no,
                fallback=fallback,
            ))
    return sources


def render_markdown(sources: list[Source]) -> str:
    rows = [
        "| priority | category | name | platform | access | url/status |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for s in sorted(sources, key=lambda x: (x.material_priority, x.category, x.name)):
        url = s.url or "no stable URL in note"
        rows.append(
            f"| {s.material_priority} | {s.category} | {s.name} | {s.platform} | {s.access_level} | {url} |"
        )
    return "\n".join(rows)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--notes", type=Path, default=DEFAULT_NOTES)
    parser.add_argument("--format", choices=["json", "markdown"], default="markdown")
    parser.add_argument("--output", type=Path, help="Optional output file.")
    args = parser.parse_args()

    sources = parse_sources(args.notes)
    if args.format == "json":
        rendered = json.dumps([asdict(s) for s in sources], ensure_ascii=False, indent=2)
    else:
        rendered = render_markdown(sources)

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered + "\n", encoding="utf-8")
    else:
        print(rendered)


if __name__ == "__main__":
    main()
