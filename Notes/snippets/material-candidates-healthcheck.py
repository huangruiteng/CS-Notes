#!/usr/bin/env python3
"""Read-only healthcheck for the private learning material candidate library."""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CANDIDATES = ROOT / ".local" / "LEARNING_MATERIAL_CANDIDATES.md"

URL_RE = re.compile(r"https?://[^\s)；;，,。]+")
ID_RE = re.compile(r"(?<![A-Za-z0-9_])([SABP]\d{1,3})(?![A-Za-z0-9_])")
HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*$")
DEFINITION_RE = re.compile(r"^#{3,6}\s+([SABP]\d{1,3})[.．\s:：]")
TOP30_HEADING_RE = re.compile(r"^#{3,5}\s+当前\s*Top\s*30\s*列表\s*$", re.I)
NUMBERED_ITEM_RE = re.compile(r"^(\d+)\.\s+(.+?)\s*$")
FENCE_RE = re.compile(r"^\s*(```|~~~)")
SENSITIVE_PARAM_RE = re.compile(
    r"(?i)(?:^|[?&])"
    r"([^=\s&]*(?:token|secret|auth)[^=\s&]*|disposable_login_token|"
    r"pwd_less_login_auth|access_token|refresh_token)="
)
RAW_ASSIGNMENT_RE = re.compile(
    r"(?i)\b(disposable_login_token|pwd_less_login_auth|access_token|"
    r"refresh_token|secret|token)=[^&\s)；;，,。]+"
)
DUPLICATE_SEVERITY_ORDER = {
    "action_required": 0,
    "warning": 1,
    "historical_batch": 2,
}
ACTIVE_QUEUE_CONTEXT_RE = re.compile(r"(?:^| > )P\d+\.")
HIGH_PRIORITY_CONTEXT_RE = re.compile(r"(?:^| > )P[12]\.")
HISTORICAL_CONTEXT_RE = re.compile(
    r"(20\d{2}-\d{2}-\d{2}|AI\s*日报|AI\s*Hotspot|AI\s*热点日报|"
    r"历史|归档|后续阅读候选|新增候选|新增素材|用户投喂素材|近期专项素材入库记录)",
    re.I,
)


@dataclass
class Finding:
    line: int
    text: str


@dataclass
class Entry:
    candidate_id: str
    line: int
    text: str
    context: str
    body: list[str]


@dataclass
class DuplicateDefinitionReport:
    candidate_id: str
    severity: str
    reason: str
    items: list[Entry]


def read_lines(path: Path) -> list[str]:
    return path.read_text(encoding="utf-8").splitlines()


def iter_non_fenced(lines: list[str]):
    in_fence = False
    for idx, line in enumerate(lines, start=1):
        if FENCE_RE.match(line):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        yield idx, line


def short_text(text: str, limit: int = 140) -> str:
    text = URL_RE.sub("[url]", text)
    text = re.sub(r"\s+", " ", text).strip()
    if len(text) <= limit:
        return text
    return text[: limit - 3] + "..."


def strip_inline_markup(text: str) -> str:
    text = re.sub(r"`([^`]*)`", r"\1", text)
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
    return text.strip()


def candidate_id_sort_key(candidate_id: str) -> tuple[str, int, str]:
    match = re.match(r"^([SABP])(\d+)$", candidate_id)
    if not match:
        return candidate_id, -1, candidate_id
    return match.group(1), int(match.group(2)), candidate_id


def extract_top30(lines: list[str]) -> tuple[int | None, list[Finding]]:
    start = None
    for idx, line in iter_non_fenced(lines):
        if TOP30_HEADING_RE.match(line):
            start = idx
            break
    if start is None:
        return None, []

    items: list[Finding] = []
    for idx in range(start + 1, len(lines) + 1):
        line = lines[idx - 1]
        if idx > start + 1 and re.match(r"^##\s+", line):
            break
        match = NUMBERED_ITEM_RE.match(line)
        if match:
            items.append(Finding(line=idx, text=line))
    return start, items


def extract_entries(lines: list[str]) -> list[Entry]:
    heads: list[tuple[int, str, str]] = []
    context_by_line: dict[int, str] = {}
    stack: list[tuple[int, str]] = []
    for idx, line in iter_non_fenced(lines):
        match = DEFINITION_RE.match(line)
        if match:
            context_by_line[idx] = " > ".join(title for _, title in stack)
            heads.append((idx, match.group(1), line))
            continue

        heading = HEADING_RE.match(line)
        if heading:
            level = len(heading.group(1))
            title = strip_inline_markup(heading.group(2))
            while stack and stack[-1][0] >= level:
                stack.pop()
            stack.append((level, title))

    entries: list[Entry] = []
    for pos, (line_no, candidate_id, text) in enumerate(heads):
        next_line = heads[pos + 1][0] if pos + 1 < len(heads) else len(lines) + 1
        body = lines[line_no: next_line - 1]
        context = context_by_line.get(line_no, "")
        entries.append(Entry(candidate_id=candidate_id, line=line_no, text=text, context=context, body=body))
    return entries


def duplicate_definition_reports(entries: list[Entry]) -> list[DuplicateDefinitionReport]:
    buckets: dict[str, list[Entry]] = {}
    for entry in entries:
        buckets.setdefault(entry.candidate_id, []).append(entry)

    reports: list[DuplicateDefinitionReport] = []
    for candidate_id, items in sorted(buckets.items(), key=lambda item: candidate_id_sort_key(item[0])):
        if len(items) <= 1:
            continue
        severity, reason = classify_duplicate_definition_group(items)
        reports.append(
            DuplicateDefinitionReport(
                candidate_id=candidate_id,
                severity=severity,
                reason=reason,
                items=items,
            )
        )

    reports.sort(
        key=lambda report: (
            DUPLICATE_SEVERITY_ORDER.get(report.severity, 99),
            candidate_id_sort_key(report.candidate_id),
        )
    )
    return reports


def duplicate_definition_ids(
    reports: list[DuplicateDefinitionReport],
    max_findings: int,
    severity_filter: str = "all",
) -> list[str]:
    total_counts = {severity: 0 for severity in DUPLICATE_SEVERITY_ORDER}
    for report in reports:
        total_counts[report.severity] = total_counts.get(report.severity, 0) + 1

    if severity_filter != "all":
        reports = [report for report in reports if report.severity == severity_filter]
    if not reports:
        return []

    if severity_filter == "all":
        summary = ", ".join(f"{severity}={total_counts.get(severity, 0)}" for severity in DUPLICATE_SEVERITY_ORDER)
        findings = [f"- summary: {summary}"]
    else:
        total_summary = ", ".join(
            f"{severity}={total_counts.get(severity, 0)}" for severity in DUPLICATE_SEVERITY_ORDER
        )
        findings = [
            f"- selected_summary: {severity_filter}={len(reports)}",
            f"- total_by_severity: {total_summary}",
        ]
    for report in reports[:max_findings]:
        locations = []
        for item in report.items[:8]:
            context = short_text(item.context or "root", 80)
            locations.append(f"{item.line} ({context})")
        suffix = " ..." if len(report.items) > 8 else ""
        findings.append(
            f"- [{report.severity}] `{report.candidate_id}` definition appears {len(report.items)} times "
            f"({report.reason}): "
            + "; ".join(locations)
            + suffix
        )
    return findings


def action_required_duplicate_queue(reports: list[DuplicateDefinitionReport], max_findings: int) -> list[str]:
    actionable = [report for report in reports if report.severity == "action_required"]
    if not actionable:
        return []

    findings = [f"- count: {len(actionable)}"]
    for report in actionable[:max_findings]:
        lines = ", ".join(str(item.line) for item in report.items[:8])
        contexts = " | ".join(short_text(item.context or "root", 60) for item in report.items[:3])
        suffix = " ..." if len(report.items) > 8 else ""
        findings.append(
            f"- [ ] `{report.candidate_id}` ({len(report.items)} definitions): "
            f"lines {lines}{suffix}; reason={report.reason}; contexts={contexts}"
        )
    return findings


def duplicate_severity_counts(reports: list[DuplicateDefinitionReport]) -> dict[str, int]:
    counts = {severity: 0 for severity in DUPLICATE_SEVERITY_ORDER}
    for report in reports:
        counts[report.severity] = counts.get(report.severity, 0) + 1
    return counts


def action_required_duplicate_items(
    reports: list[DuplicateDefinitionReport],
    max_findings: int | None = None,
) -> list[dict[str, object]]:
    actionable = [report for report in reports if report.severity == "action_required"]
    if max_findings is not None:
        actionable = actionable[:max_findings]
    return [
        {
            "candidate_id": report.candidate_id,
            "definition_count": len(report.items),
            "lines": [item.line for item in report.items],
            "reason": report.reason,
            "contexts": [short_text(item.context or "root", 120) for item in report.items[:3]],
        }
        for report in actionable
    ]


def classify_duplicate_definition_group(items: list[Entry]) -> tuple[str, str]:
    contexts = [item.context or "" for item in items]
    historical_count = sum(1 for context in contexts if HISTORICAL_CONTEXT_RE.search(context))
    active_count = sum(1 for context in contexts if ACTIVE_QUEUE_CONTEXT_RE.search(context))
    high_priority_count = sum(1 for context in contexts if HIGH_PRIORITY_CONTEXT_RE.search(context))

    if active_count == 0 and historical_count == len(contexts):
        return "historical_batch", "all definitions are in dated or historical intake sections"
    if active_count == 0 and historical_count > 0:
        return "historical_batch", "historical intake duplicate; keep unless it blocks references"
    if high_priority_count >= 2:
        return "action_required", "same id is reused in multiple P1/P2 active sections"
    if active_count >= 2 and historical_count == 0:
        return "action_required", "same id is reused across active non-historical sections"
    if active_count > 0 and historical_count > 0:
        return "warning", "active definition overlaps historical intake copies"
    return "warning", "same id appears multiple times outside known historical batches"


def top30_report(items: list[Finding], max_findings: int) -> tuple[list[str], list[str]]:
    numbers = []
    id_buckets: dict[str, list[int]] = {}
    for item in items:
        match = NUMBERED_ITEM_RE.match(item.text)
        if not match:
            continue
        rank = int(match.group(1))
        numbers.append(rank)
        for candidate_id in ID_RE.findall(item.text):
            id_buckets.setdefault(candidate_id, []).append(item.line)

    summary = [
        f"- count: {len(items)}",
        f"- rank_range: {numbers[0] if numbers else 'none'} -> {numbers[-1] if numbers else 'none'}",
    ]
    expected = list(range(1, 31))
    if numbers != expected:
        summary.append(f"- warning: ranks are not contiguous 1..30; observed={numbers}")
    else:
        summary.append("- ranks: contiguous 1..30")

    duplicate_ids = [
        f"- `{candidate_id}` appears in Top30 at lines {lines}"
        for candidate_id, lines in sorted(id_buckets.items())
        if len(lines) > 1
    ]
    return summary, duplicate_ids[:max_findings]


def duplicate_top30_id_map(items: list[Finding]) -> dict[str, list[int]]:
    id_buckets: dict[str, list[int]] = {}
    for item in items:
        for candidate_id in ID_RE.findall(item.text):
            id_buckets.setdefault(candidate_id, []).append(item.line)
    return {candidate_id: lines for candidate_id, lines in sorted(id_buckets.items()) if len(lines) > 1}


def unread_findings(lines: list[str], max_findings: int) -> tuple[int, list[str]]:
    findings = []
    count = 0
    for idx, line in iter_non_fenced(lines):
        if re.search(r"Unread|待读|无法读取|读不到", line, re.I):
            count += 1
            findings.append(f"- line {idx}: {short_text(line)}")
    return count, findings[:max_findings]


def sensitive_url_findings(lines: list[str], max_findings: int) -> tuple[int, list[str]]:
    findings = []
    count = 0
    for idx, line in iter_non_fenced(lines):
        urls = URL_RE.findall(line)
        url_keys = []
        for url in urls:
            url_keys.extend(match.group(1) for match in SENSITIVE_PARAM_RE.finditer(url))
        raw_keys = RAW_ASSIGNMENT_RE.findall(URL_RE.sub("", line))
        keys = sorted(set(url_keys + raw_keys))
        if keys:
            count += 1
            findings.append(f"- line {idx}: sensitive query/key signal keys={keys} urls={len(urls)}")
    return count, findings[:max_findings]


def missing_source_findings(entries: list[Entry], max_findings: int) -> tuple[int, list[str]]:
    findings = []
    count = 0
    for entry in entries:
        entry_text = "\n".join([entry.text, *entry.body[:8]])
        if URL_RE.search(entry_text):
            continue
        count += 1
        findings.append(f"- line {entry.line}: `{entry.candidate_id}` {short_text(entry.text)}")
    return count, findings[:max_findings]


def display_path(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT))
    except ValueError:
        return str(path)


def report(path: Path, max_findings: int, duplicate_severity: str = "all") -> str:
    lines = read_lines(path)
    top30_start, top30_items = extract_top30(lines)
    entries = extract_entries(lines)
    top30_summary, duplicate_top30_ids = top30_report(top30_items, max_findings)
    duplicate_reports = duplicate_definition_reports(entries)
    action_required_defs = action_required_duplicate_queue(duplicate_reports, max_findings)
    duplicate_defs = duplicate_definition_ids(duplicate_reports, max_findings, duplicate_severity)
    unread_count, unread = unread_findings(lines, max_findings)
    sensitive_count, sensitive = sensitive_url_findings(lines, max_findings)
    missing_count, missing_sources = missing_source_findings(entries, max_findings)
    shown_path = display_path(path)

    out = [
        f"# Material Candidates Healthcheck: {shown_path}",
        "",
        f"- lines: {len(lines)}",
        f"- candidate_definitions: {len(entries)}",
        f"- top30_heading_line: {top30_start if top30_start is not None else 'missing'}",
        f"- unread_signals: {unread_count}",
        f"- sensitive_url_signals: {sensitive_count}",
        f"- definitions_missing_source_url: {missing_count}",
        "",
        "## Top30",
        *top30_summary,
        "",
        "## Action Required Duplicate Definition Queue",
        *(action_required_defs or ["- none"]),
        "",
        "## Duplicate Definition IDs",
        *(duplicate_defs or ["- none"]),
        "",
        "## Duplicate Top30 IDs",
        *(duplicate_top30_ids or ["- none"]),
        "",
        "## Unread Signals",
        *(unread or ["- none"]),
        "",
        "## Sensitive URL Signals",
        *(sensitive or ["- none"]),
        "",
        "## Definitions Missing Source URL",
        *(missing_sources or ["- none"]),
    ]
    return "\n".join(out)


def summary_json(path: Path, max_findings: int) -> str:
    lines = read_lines(path)
    top30_start, top30_items = extract_top30(lines)
    entries = extract_entries(lines)
    duplicate_reports = duplicate_definition_reports(entries)
    unread_count, _ = unread_findings(lines, max_findings)
    sensitive_count, _ = sensitive_url_findings(lines, max_findings)
    missing_count, _ = missing_source_findings(entries, max_findings)
    duplicate_top30_ids = duplicate_top30_id_map(top30_items)

    payload = {
        "path": display_path(path),
        "lines": len(lines),
        "candidate_definitions": len(entries),
        "top30": {
            "heading_line": top30_start,
            "count": len(top30_items),
            "ranks_contiguous_1_30": [int(NUMBERED_ITEM_RE.match(item.text).group(1)) for item in top30_items]
            == list(range(1, 31)),
            "duplicate_id_count": len(duplicate_top30_ids),
            "duplicate_ids": duplicate_top30_ids,
        },
        "duplicate_definitions": {
            "severity_counts": duplicate_severity_counts(duplicate_reports),
            "action_required_ids": [item["candidate_id"] for item in action_required_duplicate_items(duplicate_reports)],
            "action_required": action_required_duplicate_items(duplicate_reports, max_findings),
        },
        "signals": {
            "unread": unread_count,
            "sensitive_url": sensitive_count,
            "definitions_missing_source_url": missing_count,
        },
    }
    return json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Read-only sanity checker for .local/LEARNING_MATERIAL_CANDIDATES.md."
    )
    parser.add_argument("file", nargs="?", default=str(DEFAULT_CANDIDATES))
    parser.add_argument("--max-findings", type=int, default=20)
    parser.add_argument(
        "--duplicate-severity",
        choices=["all", *DUPLICATE_SEVERITY_ORDER.keys()],
        default="all",
        help="Filter the Duplicate Definition IDs section by severity.",
    )
    parser.add_argument(
        "--format",
        choices=["markdown", "json"],
        default="markdown",
        help="Output a human-readable Markdown report or a machine-readable JSON summary.",
    )
    args = parser.parse_args()

    path = Path(args.file)
    if not path.exists():
        print(f"# Material Candidates Healthcheck: {display_path(path)}\n\n- error: file not found")
        return 1
    if args.format == "json":
        print(summary_json(path, args.max_findings))
    else:
        print(report(path, args.max_findings, args.duplicate_severity))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
