#!/usr/bin/env python3
"""Healthcheck for the local claude-to-im / Lark bridge.

Default mode is read-only. Use --kill-stale only after confirming a Codex child
has stopped producing output and the bridge is no longer replying.
"""

from __future__ import annotations

import argparse
import json
import os
import signal
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path


BRIDGE_HOME = Path.home() / ".claude-to-im"
STATUS_JSON = BRIDGE_HOME / "runtime" / "status.json"
LOG_FILE = BRIDGE_HOME / "logs" / "bridge.log"
DEFAULT_STALE_MINUTES = 30
DEFAULT_SCAN_LINES = 200

UNHEALTHY_PATTERNS = {
    "codex_provider_error": "[codex-provider] Error",
    "codex_skill_load_error": "failed to load skill",
    "feishu_streaming_card_error": "Failed to create streaming card",
    "feishu_ws_timeout": "timeout of 15000ms exceeded",
    "feishu_ws_connect_failed": "ws connect failed",
    "feishu_ws_send_failed": "send data failed",
}

IGNORED_ERROR_PATTERNS = [
    "DeprecationWarning",
]


@dataclass
class Proc:
    pid: int
    ppid: int
    started: datetime | None
    command: str

    @property
    def age_minutes(self) -> float | None:
        if self.started is None:
            return None
        return max(0.0, (datetime.now() - self.started).total_seconds() / 60.0)


def run(args: list[str]) -> str:
    return subprocess.check_output(args, text=True, stderr=subprocess.DEVNULL)


def run_visible(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)


def parse_lstart(fields: list[str]) -> datetime | None:
    try:
        # macOS ps lstart format: Sat May 23 14:47:09 2026
        return datetime.strptime(" ".join(fields), "%a %b %d %H:%M:%S %Y")
    except Exception:
        return None


def load_processes() -> list[Proc]:
    try:
        out = run(["ps", "-axo", "pid=,ppid=,lstart=,command="])
    except Exception as exc:
        print(f"ERROR: failed to run ps: {exc}", file=sys.stderr)
        return []

    procs: list[Proc] = []
    for line in out.splitlines():
        parts = line.split(maxsplit=8)
        if len(parts) < 9:
            continue
        try:
            pid = int(parts[0])
            ppid = int(parts[1])
        except ValueError:
            continue
        started = parse_lstart(parts[2:7])
        command = parts[8]
        procs.append(Proc(pid=pid, ppid=ppid, started=started, command=command))
    return procs


def descendants(procs: list[Proc], root_pid: int) -> list[Proc]:
    by_parent: dict[int, list[Proc]] = {}
    for proc in procs:
        by_parent.setdefault(proc.ppid, []).append(proc)

    found: list[Proc] = []
    stack = list(by_parent.get(root_pid, []))
    while stack:
        proc = stack.pop()
        found.append(proc)
        stack.extend(by_parent.get(proc.pid, []))
    return found


def load_bridge_pid() -> int | None:
    if STATUS_JSON.exists():
        try:
            data = json.loads(STATUS_JSON.read_text())
            pid = data.get("pid")
            if isinstance(pid, int):
                return pid
        except Exception:
            pass

    try:
        out = run(["launchctl", "list"])
        for line in out.splitlines():
            if "com.claude-to-im.bridge" not in line:
                continue
            first = line.split()[0]
            return int(first) if first.isdigit() else None
    except Exception:
        return None
    return None


def load_started_at() -> datetime | None:
    if not STATUS_JSON.exists():
        return None
    try:
        data = json.loads(STATUS_JSON.read_text())
        value = data.get("startedAt")
        if not isinstance(value, str):
            return None
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except Exception:
        return None


def print_recent_log(limit: int) -> None:
    if limit <= 0 or not LOG_FILE.exists():
        return
    lines = LOG_FILE.read_text(errors="replace").splitlines()[-limit:]
    print(f"\nRecent bridge log tail ({limit} lines):")
    for line in lines:
        print(line)


def recent_log_lines(limit: int) -> list[str]:
    if limit <= 0 or not LOG_FILE.exists():
        return []
    return LOG_FILE.read_text(errors="replace").splitlines()[-limit:]


def parse_log_time(line: str) -> datetime | None:
    if not line.startswith("[") or "]" not in line:
        return None
    value = line[1:line.index("]")]
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except Exception:
        return None


def scan_recent_log(limit: int, since: datetime | None) -> dict[str, int]:
    counts = {name: 0 for name in UNHEALTHY_PATTERNS}
    for line in recent_log_lines(limit):
        if since:
            line_time = parse_log_time(line)
            if line_time and line_time < since:
                continue
        if any(pattern in line for pattern in IGNORED_ERROR_PATTERNS):
            continue
        for name, pattern in UNHEALTHY_PATTERNS.items():
            if pattern in line:
                counts[name] += 1
    return {name: count for name, count in counts.items() if count}


def restart_bridge() -> int:
    skill_dir = Path.home() / ".codex" / "skills" / "claude-to-im"
    daemon = skill_dir / "scripts" / "daemon.sh"
    if not daemon.exists():
        print(f"ERROR: daemon script not found: {daemon}", file=sys.stderr)
        return 2

    print("restarting bridge via daemon.sh stop/start")
    stop = run_visible(["bash", str(daemon), "stop"])
    print(stop.stdout.rstrip())
    start = run_visible(["bash", str(daemon), "start"])
    print(start.stdout.rstrip())
    return start.returncode


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Check local claude-to-im bridge daemon and stale Codex children."
    )
    parser.add_argument("--stale-minutes", type=int, default=DEFAULT_STALE_MINUTES)
    parser.add_argument("--kill-stale", action="store_true")
    parser.add_argument("--scan-lines", type=int, default=DEFAULT_SCAN_LINES)
    parser.add_argument("--restart-unhealthy", action="store_true")
    parser.add_argument("--log-lines", type=int, default=12)
    args = parser.parse_args()

    bridge_pid = load_bridge_pid()
    started_at = load_started_at()
    print(f"bridge_status_file={STATUS_JSON}")
    print(f"bridge_pid={bridge_pid or 'unknown'}")
    print(f"bridge_started_at={started_at.astimezone(timezone.utc).isoformat() if started_at else 'unknown'}")

    procs = load_processes()
    bridge_proc = next((p for p in procs if p.pid == bridge_pid), None)
    if bridge_proc:
        age = bridge_proc.age_minutes
        age_s = f"{age:.1f}m" if age is not None else "unknown"
        print(f"bridge_running=true age={age_s} cmd={bridge_proc.command}")
    else:
        print("bridge_running=false")

    if bridge_pid is None:
        print_recent_log(args.log_lines)
        return 2

    children = descendants(procs, bridge_pid)
    codex_children = [p for p in children if "codex exec" in p.command]
    print(f"codex_children={len(codex_children)}")

    stale: list[Proc] = []
    for proc in codex_children:
        age = proc.age_minutes
        age_s = f"{age:.1f}m" if age is not None else "unknown"
        is_stale = age is not None and age >= args.stale_minutes
        label = "STALE" if is_stale else "active"
        print(f"- {label} pid={proc.pid} age={age_s} cmd={proc.command}")
        if is_stale:
            stale.append(proc)

    log_issues = scan_recent_log(args.scan_lines, started_at)
    print(f"log_scan_lines={args.scan_lines}")
    if log_issues:
        print("log_health=unhealthy")
        for name, count in log_issues.items():
            print(f"- {name}: {count}")
    else:
        print("log_health=ok")

    if args.kill_stale and stale:
        for proc in stale:
            print(f"killing stale codex child pid={proc.pid}")
            try:
                os.kill(proc.pid, signal.SIGTERM)
            except ProcessLookupError:
                pass
        print("sent SIGTERM to stale Codex children; rerun healthcheck in a few seconds")

    unhealthy = bool(stale or log_issues)
    if args.restart_unhealthy and unhealthy:
        return restart_bridge()

    print_recent_log(args.log_lines)
    return 1 if unhealthy else 0


if __name__ == "__main__":
    raise SystemExit(main())
