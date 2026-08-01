#!/usr/bin/env python3
"""Read-only Markdown section hygiene checker for long-lived CS-Notes files."""

from __future__ import annotations

import argparse
import json
import re
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path


HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*$")
FENCE_RE = re.compile(r"^\s*(```|~~~)")
TEMPORARY_NOTE_RE = re.compile(
    r"(当前明确不读|当前不读|不主动读|不建议读|素材入库|已入库|Unread|当前明确不读|当前明确不读：|暂不主动读)",
    re.I,
)

DEFAULT_LEVEL_LIMITS = {
    1: 800,
    2: 520,
    3: 280,
    4: 180,
    5: 120,
    6: 90,
}

GENERIC_DUPLICATE_TITLES = {
    "intro",
    "introduction",
    "literature review",
    "related work",
    "background",
    "references",
    "参考资料",
    "参考文献",
}


@dataclass
class Heading:
    level: int
    title: str
    line: int
    parent: str
    span_lines: int = 0


def strip_inline_markup(text: str) -> str:
    text = re.sub(r"`([^`]*)`", r"\1", text)
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
    text = text.replace("*", "").replace("_", "")
    return text.strip()


def normalize_title(title: str) -> str:
    title = strip_inline_markup(title).lower()
    title = re.sub(r"^\d+[.)、]\s*", "", title)
    title = re.sub(r"\s+", " ", title)
    title = re.sub(r"[：:，,。.!！?？（）()\[\]【】<>《》\"'`]+", "", title)
    return title.strip()


def read_lines(path: Path) -> list[str]:
    return path.read_text(encoding="utf-8").splitlines()


def extract_headings(lines: list[str]) -> list[Heading]:
    headings: list[Heading] = []
    stack: list[Heading] = []
    in_fence = False

    for idx, line in enumerate(lines, start=1):
        if FENCE_RE.match(line):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        match = HEADING_RE.match(line)
        if not match:
            continue
        level = len(match.group(1))
        title = strip_inline_markup(match.group(2).strip())
        while stack and stack[-1].level >= level:
            stack.pop()
        parent = " > ".join(item.title for item in stack)
        heading = Heading(level=level, title=title, line=idx, parent=parent)
        headings.append(heading)
        stack.append(heading)

    for i, heading in enumerate(headings):
        next_line = len(lines) + 1
        for candidate in headings[i + 1 :]:
            if candidate.level <= heading.level:
                next_line = candidate.line
                break
        heading.span_lines = max(0, next_line - heading.line)

    return headings


def format_heading(heading: Heading, path: Path) -> str:
    parent = f" parent={heading.parent}" if heading.parent else ""
    return f"{path}:{heading.line} h{heading.level} {heading.title}{parent}"


def long_sections(headings: list[Heading], path: Path, max_findings: int) -> list[str]:
    findings = []
    for heading in headings:
        limit = DEFAULT_LEVEL_LIMITS.get(heading.level, 120)
        if heading.span_lines > limit:
            findings.append(
                f"- {format_heading(heading, path)} span={heading.span_lines} lines limit={limit}"
            )
    findings.sort(key=lambda item: int(re.search(r"span=(\d+)", item).group(1)), reverse=True)
    return findings[:max_findings]


def duplicate_headings(headings: list[Heading], path: Path, max_findings: int) -> list[str]:
    buckets: dict[str, list[Heading]] = defaultdict(list)
    for heading in headings:
        key = normalize_title(heading.title)
        if key:
            buckets[key].append(heading)

    findings = []
    for key, items in sorted(buckets.items(), key=lambda kv: (-len(kv[1]), kv[0])):
        if len(items) <= 1:
            continue
        lines = ", ".join(str(item.line) for item in items[:8])
        title = items[0].title
        findings.append(f"- {path}: duplicate title `{title}` count={len(items)} lines={lines}")
    return findings[:max_findings]


def deep_headings(headings: list[Heading], path: Path, max_level: int, max_findings: int) -> list[str]:
    findings = []
    for heading in headings:
        if heading.level > max_level:
            findings.append(f"- {format_heading(heading, path)} exceeds h{max_level}")
    return findings[:max_findings]


def temporary_note_lines(lines: list[str], path: Path, max_findings: int) -> list[str]:
    findings = []
    in_fence = False
    for idx, line in enumerate(lines, start=1):
        if FENCE_RE.match(line):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        if TEMPORARY_NOTE_RE.search(line):
            snippet = strip_inline_markup(line).strip()
            if len(snippet) > 140:
                snippet = snippet[:137] + "..."
            findings.append(f"- {path}:{idx} {snippet}")
    return findings[:max_findings]


def is_root_long_section_finding(finding: str) -> bool:
    return bool(re.search(r":\d+\s+h1\s+", finding)) and " span=" in finding


def is_generic_duplicate_finding(finding: str) -> bool:
    match = re.search(r"duplicate title `([^`]+)`", finding)
    if not match:
        return False
    return normalize_title(match.group(1)) in GENERIC_DUPLICATE_TITLES


def actionable_top_issues(
    long_findings: list[str],
    duplicate_findings: list[str],
    deep_findings: list[str],
    max_findings: int,
) -> list[str]:
    # Counts stay complete; only the short "what to fix next" queue is ranked for actionability.
    actionable_long = [item for item in long_findings if not is_root_long_section_finding(item)]
    specific_duplicates = [item for item in duplicate_findings if not is_generic_duplicate_finding(item)]
    generic_duplicates = [item for item in duplicate_findings if is_generic_duplicate_finding(item)]
    root_long = [item for item in long_findings if is_root_long_section_finding(item)]

    ranked = actionable_long[:3] + specific_duplicates[:3] + deep_findings[:3] + generic_duplicates + root_long
    return ranked[:max_findings]


def health_for_file(path: Path, args: argparse.Namespace) -> dict[str, object]:
    lines = read_lines(path)
    headings = extract_headings(lines)
    full_limit = max(len(lines), len(headings), args.max_findings)
    duplicate_findings = duplicate_headings(headings, path, full_limit)
    long_findings = long_sections(headings, path, full_limit)
    deep_findings = deep_headings(headings, path, args.max_heading_level, full_limit)
    temp_findings = temporary_note_lines(lines, path, full_limit)
    top_issue_headings = actionable_top_issues(
        long_findings,
        duplicate_findings,
        deep_findings,
        args.max_findings,
    )

    return {
        "path": str(path),
        "lines": len(lines),
        "headings": len(headings),
        "findings": {
            "total": len(long_findings) + len(duplicate_findings) + len(deep_findings) + len(temp_findings),
            "long_sections": {
                "count": len(long_findings),
                "top": long_findings[: args.max_findings],
            },
            "duplicate_headings": {
                "count": len(duplicate_findings),
                "top": duplicate_findings[: args.max_findings],
            },
            "deep_headings": {
                "count": len(deep_findings),
                "top": deep_findings[: args.max_findings],
            },
            "temporary_lines": {
                "count": len(temp_findings),
                "top": temp_findings[: args.max_findings],
            },
            "top_issue_headings": top_issue_headings,
        },
    }


def report_for_file(path: Path, args: argparse.Namespace) -> str:
    health = health_for_file(path, args)
    findings = health["findings"]
    duplicate_findings = findings["duplicate_headings"]["top"]
    long_findings = findings["long_sections"]["top"]
    deep_findings = findings["deep_headings"]["top"]
    temp_findings = findings["temporary_lines"]["top"]

    sections = [
        ("Long Sections", long_findings),
        ("Duplicate Headings", duplicate_findings),
        ("Deep Headings", deep_findings),
        ("Temporary / Parking Lines", temp_findings),
    ]

    out = [
        f"# Note Section Healthcheck: {path}",
        "",
        f"- headings: {health['headings']}",
        f"- lines: {health['lines']}",
        f"- findings: {findings['total']}",
        "",
    ]
    for title, findings in sections:
        out.append(f"## {title}")
        if findings:
            out.extend(findings)
        else:
            out.append("- none")
        out.append("")
    return "\n".join(out).rstrip()


def summary_json(files: list[str], args: argparse.Namespace) -> str:
    payload: list[dict[str, object]] = []
    for file_name in files:
        path = Path(file_name)
        if not path.exists():
            payload.append({"path": str(path), "error": "file not found"})
            continue
        payload.append(health_for_file(path, args))
    return json.dumps({"files": payload}, ensure_ascii=False, indent=2, sort_keys=True)


def main() -> int:
    parser = argparse.ArgumentParser(description="Read-only Markdown section hygiene checker.")
    parser.add_argument("files", nargs="+", help="Markdown files to inspect.")
    parser.add_argument("--max-heading-level", type=int, default=4)
    parser.add_argument("--max-findings", type=int, default=20)
    parser.add_argument(
        "--format",
        choices=["markdown", "json"],
        default="markdown",
        help="Output a human-readable Markdown report or a machine-readable JSON summary.",
    )
    args = parser.parse_args()

    if args.format == "json":
        print(summary_json(args.files, args))
        return 0

    reports = []
    for file_name in args.files:
        path = Path(file_name)
        if not path.exists():
            reports.append(f"# Note Section Healthcheck: {path}\n\n- error: file not found")
            continue
        reports.append(report_for_file(path, args))
    print("\n\n---\n\n".join(reports))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
