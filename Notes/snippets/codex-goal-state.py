#!/usr/bin/env python3
"""Small helper for the private CS-Notes active goal state file.

The file lives under .local/ so user feedback, private constraints, and
in-progress goal state do not leak into public notes or commits.
"""

from __future__ import annotations

import argparse
import fcntl
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo


ROOT = Path(__file__).resolve().parents[2]
STATE = ROOT / ".local" / "ACTIVE_GOAL_STATE.md"
LOCK = ROOT / ".local" / "ACTIVE_GOAL_STATE.lock"
TZ = ZoneInfo("Asia/Shanghai")


def now_text() -> str:
    return datetime.now(TZ).isoformat(timespec="seconds")


def read_state() -> str:
    try:
        return STATE.read_text(encoding="utf-8")
    except FileNotFoundError:
        return ""


def write_state(text: str) -> None:
    STATE.parent.mkdir(parents=True, exist_ok=True)
    STATE.write_text(text, encoding="utf-8")


@contextmanager
def state_lock():
    STATE.parent.mkdir(parents=True, exist_ok=True)
    with LOCK.open("w", encoding="utf-8") as lock_file:
        fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)


def ensure_state(objective: str | None = None) -> str:
    text = read_state()
    if text:
        return text
    objective = objective or "Improve CS-Notes goal-mode work quality with a stateful Goal Harness Layer"
    created = now_text()
    text = f"""---
status: active
owner_mode: goal
objective: "{objective}"
updated_at: {created}
---

# Active Goal State

## Objective

{objective}

## Non-Goals

- 不消费具体学习材料队列，除非用户明确说素材 / 调研 / 请你读 / 精读 / 读完。
- 不触碰 agent-harness，除非用户明确要求或本状态文件把它列为目标。
- 不把 .local 私有状态复制到公开笔记、飞书同步文档或提交内容。

## Acceptance Criteria

- 每次 goal tick 都先读本文件和 `codex-goal-pre-tick.py` 输出。
- 每次只推进一个可验证动作，并记录 changed files / validation / next action。
- 用户实时反馈必须转成 `Recent User Feedback` 或更新 `Next Action`。
- goal 结束时记录最终 artifact 和残余风险。

## Current Constraints

- 当前先只接入 CS-Notes，验证稳定后再考虑 multi-project adapter。
- goal mode 的价值重点是提升产物质量，不只是减少用户操作。

## Next Action

- 把 `pre_tick --mode goal` 接到本状态文件，并用一次验证确认输出包含 goal_state。

## Recent User Feedback

- {created}: 用户判断：goal mode 应读取一个 goal 状态文件；该状态文件应根据实时反馈调整。

## Progress Ledger

- {created}: 初始化 CS-Notes active goal state。
"""
    write_state(text)
    return text


def replace_frontmatter_value(text: str, key: str, value: str) -> str:
    lines = text.splitlines()
    for i, line in enumerate(lines):
        if line.startswith(f"{key}:"):
            lines[i] = f"{key}: {value}"
            return "\n".join(lines) + "\n"
    if lines and lines[0] == "---":
        lines.insert(1, f"{key}: {value}")
        return "\n".join(lines) + "\n"
    return f"---\n{key}: {value}\n---\n\n{text}"


def touch_updated_at(text: str) -> str:
    return replace_frontmatter_value(text, "updated_at", now_text())


def append_to_section(text: str, heading: str, line: str) -> str:
    marker = f"## {heading}"
    entry = f"- {now_text()}: {line}"
    if marker not in text:
        text = text.rstrip() + f"\n\n{marker}\n\n{entry}\n"
    else:
        idx = text.index(marker)
        next_idx = text.find("\n## ", idx + len(marker))
        insert_at = next_idx if next_idx != -1 else len(text)
        prefix = text[:insert_at].rstrip()
        suffix = text[insert_at:]
        text = prefix + "\n" + entry + ("\n" if suffix else "\n") + suffix
    return touch_updated_at(text)


def replace_section(text: str, heading: str, body: str) -> str:
    marker = f"## {heading}"
    block = f"{marker}\n\n{body.strip()}\n"
    if marker not in text:
        text = text.rstrip() + "\n\n" + block
    else:
        idx = text.index(marker)
        next_idx = text.find("\n## ", idx + len(marker))
        end = next_idx if next_idx != -1 else len(text)
        text = text[:idx] + block + text[end:]
    return touch_updated_at(text)


def cmd_show(_: argparse.Namespace) -> int:
    print(ensure_state().rstrip())
    return 0


def cmd_init(args: argparse.Namespace) -> int:
    with state_lock():
        if STATE.exists() and not args.force:
            print(f"exists: {STATE}")
            return 0
        if STATE.exists():
            STATE.unlink()
        ensure_state(args.objective)
    print(f"initialized: {STATE}")
    return 0


def cmd_feedback(args: argparse.Namespace) -> int:
    with state_lock():
        text = append_to_section(ensure_state(), "Recent User Feedback", args.text)
        write_state(text)
    print(f"feedback appended: {STATE}")
    return 0


def cmd_progress(args: argparse.Namespace) -> int:
    with state_lock():
        text = append_to_section(ensure_state(), "Progress Ledger", args.text)
        write_state(text)
    print(f"progress appended: {STATE}")
    return 0


def cmd_next(args: argparse.Namespace) -> int:
    with state_lock():
        text = replace_section(ensure_state(), "Next Action", f"- {args.text}")
        write_state(text)
    print(f"next action updated: {STATE}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Manage .local/ACTIVE_GOAL_STATE.md")
    sub = parser.add_subparsers(required=False)

    p = sub.add_parser("show", help="Print current active goal state, creating a default if missing.")
    p.set_defaults(func=cmd_show)

    p = sub.add_parser("init", help="Initialize active goal state.")
    p.add_argument("--objective")
    p.add_argument("--force", action="store_true")
    p.set_defaults(func=cmd_init)

    p = sub.add_parser("feedback", help="Append user feedback to the active goal state.")
    p.add_argument("text")
    p.set_defaults(func=cmd_feedback)

    p = sub.add_parser("progress", help="Append progress to the active goal state.")
    p.add_argument("text")
    p.set_defaults(func=cmd_progress)

    p = sub.add_parser("next", help="Replace the next action.")
    p.add_argument("text")
    p.set_defaults(func=cmd_next)

    args = parser.parse_args()
    if not hasattr(args, "func"):
        args.func = cmd_show
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
