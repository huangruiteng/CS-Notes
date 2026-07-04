#!/usr/bin/env python3
"""Read-only pre-tick gate for the CS-Notes Goal Harness Layer.

The script intentionally does not mutate files. It inspects cheap local signals
and returns one recommended next action so Codex goal/heartbeat runs start from
the same control-plane state instead of re-deciding from scratch.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo


ROOT = Path(__file__).resolve().parents[2]
LOCAL = ROOT / ".local"
GOAL_STATE_FILE = LOCAL / "ACTIVE_GOAL_STATE.md"
CAPABILITY_BACKLOG_FILE = LOCAL / "CS_NOTES_CAPABILITY_BACKLOG.md"
MATERIAL_HEALTHCHECK_SCRIPT = ROOT / "snippets/material-candidates-healthcheck.py"
NOTE_SECTION_HEALTHCHECK_SCRIPT = ROOT / "snippets/note-section-healthcheck.py"
NOTE_STRUCTURE_HEALTH_TARGETS = [
    ROOT / "Notes/AI-Applied-Algorithms.md",
]
SHA_TZ = ZoneInfo("Asia/Shanghai")

GOAL_TICK_OUTPUT_PROTOCOL = [
    {
        "name": "artifact",
        "requirement": "Produce one concrete artifact or state why this tick is status-only.",
    },
    {
        "name": "validation",
        "requirement": "Run one cheap validation command and report what it checked.",
    },
    {
        "name": "critic",
        "requirement": "Write a brief self-critique: quality, residual risk, and whether the result advances the active goal.",
    },
    {
        "name": "writeback",
        "requirement": "Update .local/ACTIVE_GOAL_STATE.md progress/next action when the active goal changes.",
    },
]


@dataclass
class Gate:
    name: str
    due: bool
    reason: str


@dataclass
class PreTick:
    mode: str
    now: str
    recommended_action: str
    reason: str
    gates: list[Gate]
    guards: list[str]
    signals: dict[str, object]


def run(cmd: list[str]) -> str:
    return subprocess.run(
        cmd,
        cwd=ROOT,
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
    ).stdout.strip()


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return ""


def parse_date(value: str) -> datetime | None:
    for fmt in ("%Y-%m-%d", "%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%dT%H:%M:%S"):
        try:
            dt = datetime.strptime(value.strip(), fmt)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=SHA_TZ)
            return dt.astimezone(SHA_TZ)
        except ValueError:
            pass
    return None


def days_since(date_text: str, now: datetime) -> int | None:
    dt = parse_date(date_text)
    if not dt:
        return None
    return (now.date() - dt.date()).days


def career_review_age(now: datetime) -> int | None:
    text = read_text(LOCAL / "CAREER_EVIDENCE_LEDGER.md")
    match = re.search(r"^last_reviewed_at:\s*([0-9T:+-]+)", text, re.M)
    if match:
        return days_since(match.group(1), now)
    path = LOCAL / "CAREER_EVIDENCE_LEDGER.md"
    if path.exists():
        modified = datetime.fromtimestamp(path.stat().st_mtime, tz=SHA_TZ)
        return (now.date() - modified.date()).days
    return None


def top30_last_event_age(now: datetime) -> int | None:
    text = read_text(LOCAL / "LEARNING_MATERIAL_CANDIDATES.md")
    dates = re.findall(r"^(20\d{2}-\d{2}-\d{2})\s*(?:[^：\n]{0,20})?(?:微调|读完闭环|入库|探索源升级)", text, re.M)
    if not dates:
        match = re.search(r"^最后更新：\s*(20\d{2}-\d{2}-\d{2})", text, re.M)
        dates = [match.group(1)] if match else []
    parsed = [parse_date(d) for d in dates]
    parsed = [d for d in parsed if d]
    if not parsed:
        return None
    return (now.date() - max(parsed).date()).days


def todo_summary() -> dict[str, int]:
    try:
        data = json.loads((ROOT / ".trae/todos/todos.json").read_text(encoding="utf-8"))
        todos = data.get("todos", [])
    except Exception:
        return {"total": 0, "pending": 0, "in_progress": 0, "blocked": 0}

    counts = {"total": len(todos), "pending": 0, "in_progress": 0, "blocked": 0}
    for item in todos:
        status = str(item.get("status", "")).lower()
        if status in counts:
            counts[status] += 1
    return counts


def git_signals() -> dict[str, object]:
    lines = [line for line in run(["git", "status", "--short", "--untracked-files=all"]).splitlines() if line]
    return {
        "dirty_count": len(lines),
        "sample": lines[:12],
    }


def frontmatter_value(text: str, key: str) -> str | None:
    match = re.search(rf"^{re.escape(key)}:\s*(.+)$", text, re.M)
    if not match:
        return None
    return match.group(1).strip().strip('"')


def section_lines(text: str, heading: str, limit: int = 6) -> list[str]:
    pattern = rf"^## {re.escape(heading)}\s*$"
    match = re.search(pattern, text, re.M)
    if not match:
        return []
    start = match.end()
    next_heading = re.search(r"^##\s+", text[start:], re.M)
    end = start + next_heading.start() if next_heading else len(text)
    lines = []
    for line in text[start:end].splitlines():
        line = line.strip()
        if line:
            lines.append(line)
        if len(lines) >= limit:
            break
    return lines


def plain_markdown(text: str) -> str:
    text = re.sub(r"`([^`]*)`", r"\1", text)
    text = text.replace("**", "")
    return text.strip()


def capability_backlog_signals() -> dict[str, object]:
    path = CAPABILITY_BACKLOG_FILE
    text = read_text(path)
    rel_path = str(path.relative_to(ROOT))
    if not text:
        return {
            "exists": False,
            "path": rel_path,
        }

    current_lines = section_lines(text, "Current Top Action", limit=14)
    top_action: str | None = None
    reasons: list[str] = []
    acceptance: list[str] = []
    bucket: str | None = None
    for raw_line in current_lines:
        line = plain_markdown(raw_line)
        if line.startswith("下一刀"):
            top_action = line.split("：", 1)[-1].strip().rstrip("。")
        elif line.startswith("理由"):
            bucket = "reasons"
        elif line.startswith("验收"):
            bucket = "acceptance"
        elif line.startswith("-"):
            item = line.lstrip("-").strip()
            if bucket == "reasons":
                reasons.append(item)
            elif bucket == "acceptance":
                acceptance.append(item)

    capability_areas: list[str] = []
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line.startswith("| "):
            continue
        if line.startswith("| 能力区") or line.startswith("| ---"):
            continue
        cells = [plain_markdown(cell) for cell in line.strip("|").split("|")]
        if cells and cells[0]:
            capability_areas.append(cells[0])

    return {
        "exists": True,
        "path": rel_path,
        "updated_at": frontmatter_value(text, "updated_at"),
        "status": frontmatter_value(text, "status"),
        "current_top_action": top_action,
        "top_action_reasons": reasons[:3],
        "top_action_acceptance": acceptance[:3],
        "capability_areas": capability_areas[:10],
    }


def material_candidate_health_signals() -> dict[str, object]:
    rel_path = str(MATERIAL_HEALTHCHECK_SCRIPT.relative_to(ROOT))
    if not MATERIAL_HEALTHCHECK_SCRIPT.exists():
        return {
            "available": False,
            "path": rel_path,
            "error": "healthcheck script missing",
        }

    result = subprocess.run(
        [
            "python3",
            str(MATERIAL_HEALTHCHECK_SCRIPT),
            "--format",
            "json",
            "--max-findings",
            "10",
        ],
        cwd=ROOT,
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        timeout=20,
    )
    if result.returncode != 0:
        return {
            "available": False,
            "path": rel_path,
            "error": f"healthcheck exited with {result.returncode}",
        }

    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError:
        return {
            "available": False,
            "path": rel_path,
            "error": "healthcheck emitted invalid json",
        }

    duplicate_definitions = payload.get("duplicate_definitions") or {}
    return {
        "available": True,
        "path": rel_path,
        "candidate_file": payload.get("path"),
        "top30": payload.get("top30"),
        "duplicate_definitions": {
            "severity_counts": duplicate_definitions.get("severity_counts"),
            "action_required_ids": duplicate_definitions.get("action_required_ids"),
        },
        "signals": payload.get("signals"),
    }


def note_structure_health_signals() -> dict[str, object]:
    rel_path = str(NOTE_SECTION_HEALTHCHECK_SCRIPT.relative_to(ROOT))
    if not NOTE_SECTION_HEALTHCHECK_SCRIPT.exists():
        return {
            "available": False,
            "path": rel_path,
            "error": "healthcheck script missing",
        }

    targets = [str(path.relative_to(ROOT)) for path in NOTE_STRUCTURE_HEALTH_TARGETS if path.exists()]
    missing_targets = [
        str(path.relative_to(ROOT)) for path in NOTE_STRUCTURE_HEALTH_TARGETS if not path.exists()
    ]
    if not targets:
        return {
            "available": False,
            "path": rel_path,
            "error": "no configured note health targets exist",
            "missing_targets": missing_targets,
        }

    result = subprocess.run(
        [
            "python3",
            str(NOTE_SECTION_HEALTHCHECK_SCRIPT),
            "--format",
            "json",
            "--max-findings",
            "5",
            *targets,
        ],
        cwd=ROOT,
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        timeout=20,
    )
    if result.returncode != 0:
        return {
            "available": False,
            "path": rel_path,
            "error": f"healthcheck exited with {result.returncode}",
            "targets": targets,
            "missing_targets": missing_targets,
        }

    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError:
        return {
            "available": False,
            "path": rel_path,
            "error": "healthcheck emitted invalid json",
            "targets": targets,
            "missing_targets": missing_targets,
        }

    files: list[dict[str, object]] = []
    for item in payload.get("files") or []:
        findings = item.get("findings") or {}
        long_sections = findings.get("long_sections") or {}
        duplicate_headings = findings.get("duplicate_headings") or {}
        deep_headings = findings.get("deep_headings") or {}
        temporary_lines = findings.get("temporary_lines") or {}
        files.append(
            {
                "path": item.get("path"),
                "lines": item.get("lines"),
                "headings": item.get("headings"),
                "findings_total": findings.get("total"),
                "long_sections": long_sections.get("count"),
                "duplicate_headings": duplicate_headings.get("count"),
                "deep_headings": deep_headings.get("count"),
                "temporary_lines": temporary_lines.get("count"),
                "top_issue_headings": (findings.get("top_issue_headings") or [])[:5],
            }
        )

    return {
        "available": True,
        "path": rel_path,
        "targets": targets,
        "missing_targets": missing_targets,
        "files": files,
    }


def goal_state_signals(now: datetime) -> dict[str, object]:
    path = GOAL_STATE_FILE
    text = read_text(path)
    if not text:
        return {
            "exists": False,
            "path": str(path.relative_to(ROOT)),
            "recommendation": "initialize .local/ACTIVE_GOAL_STATE.md before long-running goal work",
        }

    modified = datetime.fromtimestamp(path.stat().st_mtime, tz=SHA_TZ)
    updated_at = frontmatter_value(text, "updated_at")
    updated_dt = parse_date(updated_at) if updated_at else modified
    feedback_lines = [line for line in section_lines(text, "Recent User Feedback", limit=8) if line.startswith("-")]
    checkpoint_lines = [line for line in section_lines(text, "Progress Ledger", limit=8) if line.startswith("-")]

    return {
        "exists": True,
        "path": str(path.relative_to(ROOT)),
        "status": frontmatter_value(text, "status"),
        "objective": frontmatter_value(text, "objective"),
        "owner_mode": frontmatter_value(text, "owner_mode"),
        "updated_at": updated_dt.isoformat(timespec="seconds") if updated_dt else None,
        "age_minutes": round((now - updated_dt).total_seconds() / 60, 1) if updated_dt else None,
        "next_action": section_lines(text, "Next Action", limit=3),
        "acceptance": section_lines(text, "Acceptance Criteria", limit=5),
        "recent_feedback": feedback_lines[-5:],
        "recent_progress": checkpoint_lines[-5:],
    }


def build_pre_tick(mode: str, intent: str | None) -> PreTick:
    now = datetime.now(SHA_TZ)
    career_age = career_review_age(now)
    top30_age = top30_last_event_age(now)
    goal_state = goal_state_signals(now)

    is_sunday_evening = now.weekday() == 6 and now.hour >= 18
    is_monday_morning = now.weekday() == 0 and now.hour < 12
    is_monday_day = now.weekday() == 0 and 8 <= now.hour < 20

    weekly_due = career_age is not None and career_age >= 7 and (is_sunday_evening or is_monday_morning)
    top30_due = top30_age is not None and top30_age >= 14 and is_monday_day

    gates = [
        Gate(
            "weekly_career_evidence_audit",
            weekly_due,
            f"career ledger age={career_age}; requires Sunday evening or Monday morning",
        ),
        Gate(
            "biweekly_top30_calibration",
            top30_due,
            f"top30 event age={top30_age}; requires Monday daytime",
        ),
    ]

    if mode == "heartbeat":
        if weekly_due:
            action = "weekly_career_evidence_audit"
            reason = "scheduled gate is due"
        elif top30_due:
            action = "biweekly_top30_calibration"
            reason = "scheduled gate is due"
        else:
            action = "normal_cs_notes_autopilot"
            reason = "no scheduled gate is due; choose exactly one low-risk CS-Notes improvement"
    elif mode == "goal":
        if goal_state.get("exists"):
            action = "advance_active_goal_from_state_file"
            reason = "goal mode should read .local/ACTIVE_GOAL_STATE.md, follow its next action, update feedback/progress, and validate one artifact"
        else:
            action = "initialize_active_goal_state"
            reason = "goal mode needs .local/ACTIVE_GOAL_STATE.md before reliable long-running work"
    else:
        action = "manual_request_first"
        reason = "manual user instruction overrides scheduled gates"

    if intent:
        reason = f"{reason}; user_intent={intent}"

    guards = [
        "do not touch agent-harness unless the user explicitly asks",
        "do not consume the material queue unless the user said 素材 / 调研 / 请你读 / 精读 / 读完",
        "choose at most one action before reporting",
        "preserve private .local content; do not copy it into public notes",
        "validate with a cheap command before final response",
    ]

    signals = {
        "career_review_age_days": career_age,
        "top30_last_event_age_days": top30_age,
        "todo": todo_summary(),
        "git": git_signals(),
        "goal_state": goal_state,
        "capability_backlog": capability_backlog_signals(),
        "material_candidate_health": material_candidate_health_signals(),
        "note_structure_health": note_structure_health_signals(),
        "goal_tick_output_protocol": GOAL_TICK_OUTPUT_PROTOCOL,
    }

    return PreTick(
        mode=mode,
        now=now.isoformat(timespec="seconds"),
        recommended_action=action,
        reason=reason,
        gates=gates,
        guards=guards,
        signals=signals,
    )


def render_material_candidate_health(health: object) -> list[str]:
    if not isinstance(health, dict):
        return []

    lines = ["", "## Material Candidate Health"]
    if not health.get("available"):
        lines.append(f"- unavailable: {health.get('error', 'unknown error')}")
        lines.append(f"- path: `{health.get('path')}`")
        return lines

    top30 = health.get("top30") or {}
    duplicate_definitions = health.get("duplicate_definitions") or {}
    severity_counts = duplicate_definitions.get("severity_counts") or {}
    action_required_ids = duplicate_definitions.get("action_required_ids") or []
    signals = health.get("signals") or {}
    action_required_text = ", ".join(f"`{item}`" for item in action_required_ids) if action_required_ids else "none"

    lines.append(f"- candidate_file: `{health.get('candidate_file')}`")
    lines.append(
        "- Top30: "
        f"count={top30.get('count')}, "
        f"duplicate_ids={top30.get('duplicate_id_count')}, "
        f"contiguous_1_30={top30.get('ranks_contiguous_1_30')}"
    )
    lines.append(
        "- duplicate definitions: "
        f"action_required={severity_counts.get('action_required', 0)}, "
        f"warning={severity_counts.get('warning', 0)}, "
        f"historical_batch={severity_counts.get('historical_batch', 0)}"
    )
    lines.append(f"- action_required_ids: {action_required_text}")
    lines.append(
        "- signals: "
        f"sensitive_url={signals.get('sensitive_url')}, "
        f"unread={signals.get('unread')}, "
        f"missing_source={signals.get('definitions_missing_source_url')}"
    )
    return lines


def render_note_structure_health(health: object) -> list[str]:
    if not isinstance(health, dict):
        return []

    lines = ["", "## Note Structure Health"]
    if not health.get("available"):
        lines.append(f"- unavailable: {health.get('error', 'unknown error')}")
        lines.append(f"- path: `{health.get('path')}`")
        return lines

    files = health.get("files") or []
    if not files:
        lines.append("- no files returned")
        return lines

    for item in files:
        lines.append(f"- target: `{item.get('path')}`")
        lines.append(
            "- summary: "
            f"headings={item.get('headings')}, "
            f"lines={item.get('lines')}, "
            f"findings={item.get('findings_total')}"
        )
        lines.append(
            "- findings: "
            f"long_sections={item.get('long_sections')}, "
            f"duplicate_headings={item.get('duplicate_headings')}, "
            f"deep_headings={item.get('deep_headings')}, "
            f"temporary_lines={item.get('temporary_lines')}"
        )
        top_issue_headings = item.get("top_issue_headings") or []
        if top_issue_headings:
            lines.append("- top_issue_headings:")
            for issue in top_issue_headings[:3]:
                issue_text = re.sub(r"^-\s+", "", str(issue)).strip()
                lines.append(f"  - {issue_text}")
    return lines


def render_markdown(pre: PreTick) -> str:
    lines = [
        "# CS-Notes Goal Pre-Tick",
        "",
        f"- mode: `{pre.mode}`",
        f"- now: `{pre.now}`",
        f"- recommended_action: `{pre.recommended_action}`",
        f"- reason: {pre.reason}",
        "",
        "## Gates",
    ]
    for gate in pre.gates:
        status = "DUE" if gate.due else "skip"
        lines.append(f"- `{gate.name}`: {status} - {gate.reason}")
    lines.extend(["", "## Guards"])
    lines.extend(f"- {guard}" for guard in pre.guards)
    protocol = pre.signals.get("goal_tick_output_protocol")
    if protocol:
        lines.extend(["", "## Goal Tick Output Protocol"])
        for item in protocol:
            lines.append(f"- `{item['name']}`: {item['requirement']}")
    backlog = pre.signals.get("capability_backlog")
    if backlog:
        lines.extend(["", "## Capability Backlog"])
        if backlog.get("exists"):
            lines.append(f"- path: `{backlog.get('path')}`")
            lines.append(f"- current_top_action: {backlog.get('current_top_action')}")
            reasons = backlog.get("top_action_reasons") or []
            for reason in reasons[:2]:
                lines.append(f"- why: {reason}")
        else:
            lines.append(f"- missing: `{backlog.get('path')}`")
    lines.extend(render_material_candidate_health(pre.signals.get("material_candidate_health")))
    lines.extend(render_note_structure_health(pre.signals.get("note_structure_health")))
    lines.extend(["", "## Signals", "```json", json.dumps(pre.signals, ensure_ascii=False, indent=2), "```"])
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="CS-Notes goal/heartbeat pre-tick gate.")
    parser.add_argument("--mode", choices=["manual", "heartbeat", "goal"], default="manual")
    parser.add_argument("--intent", help="Short user-facing intent label for this tick.")
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of Markdown.")
    args = parser.parse_args()

    pre = build_pre_tick(args.mode, args.intent)
    if args.json:
        print(json.dumps(asdict(pre), ensure_ascii=False, indent=2))
    else:
        print(render_markdown(pre))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
