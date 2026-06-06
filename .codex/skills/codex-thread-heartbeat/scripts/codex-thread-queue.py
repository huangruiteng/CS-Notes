#!/usr/bin/env python3
"""
Inspect Codex App/CLI thread metadata and manage guarded heartbeat prompts for
long-running Codex control threads.

This is intentionally conservative:
- locating threads and counting local queues is read-only SQLite access;
- enqueue requires the app-server control socket to exist;
- `heartbeat --transport cli-resume` is a headless fallback: it writes to the
  target rollout and runs correctly, but the currently open Codex App view may
  not refresh because the turn did not originate inside that App renderer;
- the legacy `codex debug app-server send-message-v2` path is not used because
  it has no thread-id argument and may target the currently focused App thread.
"""

from __future__ import annotations

import argparse
import json
import os
import plistlib
import shutil
import sqlite3
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any


CODEX_HOME = Path(os.environ.get("CODEX_HOME", Path.home() / ".codex")).expanduser()
STATE_DB = CODEX_HOME / "state_5.sqlite"
DEV_DB = CODEX_HOME / "sqlite" / "codex-dev.db"
CONTROL_SOCK = CODEX_HOME / "app-server-control" / "app-server-control.sock"
LAUNCH_AGENTS_DIR = Path.home() / "Library" / "LaunchAgents"
LAUNCHD_LOG_DIR = CODEX_HOME / "logs" / "thread-heartbeats"

HEARTBEAT_PRESETS: dict[str, dict[str, Any]] = {
    "agent-harness": {
        "aliases": ["agent-memory"],
        "label": "com.codex.thread-heartbeat.agent-harness",
        "interval": 600,
        "title": "agent-harness 主控",
        "cwd": "/Users/bytedance/Documents/agent-harness",
        "min_idle_seconds": 120,
        "message": (
            "继续推进 Agent Harness 项目：先读最新上下文与 git 状态，按 AGENTS.md 和 docs/TODO.md "
            "的优先级推进当前主线；可按 AGENTS.md 判断是否需要启动只读 sub-agent；优先跑/分析 "
            "TAU2/OpenViking memory 实验、更新必要 artifact、保持证据边界清晰。每次输出要说明做了什么、"
            "当前结论、下一步。"
        ),
    },
    "cs-notes": {
        "aliases": ["csnotes"],
        "label": "com.codex.thread-heartbeat.cs-notes",
        "interval": 7200,
        "title": "CS-Notes主控",
        "cwd": "/Users/bytedance/CS-Notes",
        "min_idle_seconds": 120,
        "message": (
            "Continue improving the CS-Notes work system with one small, verifiable, low-risk step: "
            "workflow/process optimization, note structure cleanup, todo/index hygiene, skill/script "
            "improvement, or material exploration capability. Do not consume the concrete learning material "
            "queue unless the user explicitly asked for 素材, 调研, 精读, or 读完. Keep changes scoped, "
            "verify them, and report changed files, validation, and the next safe action."
        ),
    },
    "cs-notes-test": {
        "aliases": ["csnotes-test"],
        "label": "com.codex.thread-heartbeat.cs-notes-test",
        "interval": 30,
        "title": "CS-Notes主控",
        "cwd": "/Users/bytedance/CS-Notes",
        "min_idle_seconds": 5,
        "message": (
            "[heartbeat delivery test] 这是一次 CS-Notes 主控 heartbeat 投递测试。如果你看到这条消息，"
            "说明 launchd -> idle guard -> codex exec resume 已成功打到当前主控线程。请只回复一句："
            "heartbeat test received，并不要修改文件。"
        ),
        "disable_after_send": True,
    },
}


@dataclass
class ThreadRow:
    id: str
    title: str
    cwd: str
    rollout_path: str
    source: str
    archived: int
    updated_at_ms: int | None
    model: str | None
    reasoning_effort: str | None


def connect_readonly(path: Path) -> sqlite3.Connection:
    if not path.exists():
        raise FileNotFoundError(path)
    uri = f"file:{path}?mode=ro"
    conn = sqlite3.connect(uri, uri=True)
    conn.row_factory = sqlite3.Row
    return conn


def find_threads(title: str | None, cwd: str | None, thread_id: str | None, limit: int) -> list[ThreadRow]:
    where: list[str] = ["archived = 0"]
    params: list[Any] = []
    if thread_id:
        where.append("id = ?")
        params.append(thread_id)
    if title:
        where.append("title like ?")
        params.append(f"%{title}%")
    if cwd:
        where.append("cwd = ?")
        params.append(cwd)

    sql = f"""
        select id, title, cwd, rollout_path, source, archived, updated_at_ms, model, reasoning_effort
        from threads
        where {' and '.join(where)}
        order by
          case
            when source = 'vscode' then 0
            when source = 'cli' then 1
            when source = 'appServer' then 2
            else 3
          end,
          updated_at_ms desc
        limit ?
    """
    params.append(limit)
    with connect_readonly(STATE_DB) as conn:
        rows = conn.execute(sql, params).fetchall()
    return [ThreadRow(**dict(row)) for row in rows]


def resolve_one_thread(args: argparse.Namespace) -> ThreadRow:
    rows = find_threads(args.title, args.cwd, args.thread_id, limit=args.limit)
    if not rows:
        raise SystemExit("No matching non-archived Codex thread found.")
    return rows[0]


def count_agent_job_items(thread_id: str) -> dict[str, int]:
    if not STATE_DB.exists():
        return {}
    sql = """
        select status, count(*) as n
        from agent_job_items
        where assigned_thread_id = ?
        group by status
        order by status
    """
    with connect_readonly(STATE_DB) as conn:
        return {row["status"]: int(row["n"]) for row in conn.execute(sql, (thread_id,))}


def count_unread_inbox(thread_id: str) -> int | None:
    if not DEV_DB.exists():
        return None
    sql = "select count(*) as n from inbox_items where thread_id = ? and read_at is null"
    with connect_readonly(DEV_DB) as conn:
        return int(conn.execute(sql, (thread_id,)).fetchone()["n"])


def parse_ts(ts: str | None) -> float | None:
    if not ts:
        return None
    if ts.endswith("Z"):
        ts = ts[:-1] + "+00:00"
    try:
        return __import__("datetime").datetime.fromisoformat(ts).timestamp()
    except ValueError:
        return None


def rollout_idle_state(rollout_path: str, min_idle_seconds: int) -> dict[str, Any]:
    path = Path(rollout_path)
    if not path.exists():
        return {
            "state": "unknown",
            "reason": f"rollout file not found: {path}",
            "can_send": False,
        }

    latest_event_ts: str | None = None
    latest_user_ts: str | None = None
    latest_final_ts: str | None = None
    latest_agent_phase: str | None = None
    latest_payload_type: str | None = None
    pending_function_calls: set[str] = set()

    with path.open("r", encoding="utf-8") as fh:
        for line in fh:
            if not line.strip():
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                continue
            ts = obj.get("timestamp")
            if ts:
                latest_event_ts = ts
            payload = obj.get("payload") or {}
            payload_type = payload.get("type")
            if payload_type:
                latest_payload_type = payload_type

            if obj.get("type") == "response_item":
                if payload_type == "function_call":
                    call_id = payload.get("call_id")
                    if call_id:
                        pending_function_calls.add(call_id)
                elif payload_type == "function_call_output":
                    call_id = payload.get("call_id")
                    if call_id:
                        pending_function_calls.discard(call_id)
                elif payload_type == "message" and payload.get("role") == "assistant":
                    phase = payload.get("phase")
                    latest_agent_phase = phase
                    if phase == "final_answer":
                        latest_final_ts = ts

            if obj.get("type") == "event_msg":
                if payload_type == "user_message":
                    latest_user_ts = ts
                elif payload_type == "agent_message":
                    phase = payload.get("phase")
                    latest_agent_phase = phase
                    if phase == "final_answer":
                        latest_final_ts = ts

    now = time.time()
    latest_event_epoch = parse_ts(latest_event_ts)
    latest_user_epoch = parse_ts(latest_user_ts)
    latest_final_epoch = parse_ts(latest_final_ts)
    idle_for_seconds = None if latest_event_epoch is None else max(0, int(now - latest_event_epoch))

    result = {
        "state": "unknown",
        "can_send": False,
        "reason": "",
        "latest_event_ts": latest_event_ts,
        "latest_user_ts": latest_user_ts,
        "latest_final_ts": latest_final_ts,
        "latest_agent_phase": latest_agent_phase,
        "latest_payload_type": latest_payload_type,
        "pending_function_call_count": len(pending_function_calls),
        "idle_for_seconds": idle_for_seconds,
        "min_idle_seconds": min_idle_seconds,
    }

    if pending_function_calls:
        result.update(state="active", reason="there are function_call items without matching outputs")
        return result
    if latest_user_epoch is not None and (latest_final_epoch is None or latest_final_epoch < latest_user_epoch):
        result.update(state="active", reason="latest user_message has no later final_answer")
        return result
    if latest_final_epoch is None:
        result.update(state="unknown", reason="no final_answer found in rollout; refusing to send")
        return result
    if idle_for_seconds is None or idle_for_seconds < min_idle_seconds:
        result.update(state="cooldown", reason="thread looks complete but cooldown has not elapsed")
        return result

    result.update(state="idle", can_send=True, reason="latest user turn has a final_answer and cooldown elapsed")
    return result


def app_server_running() -> bool:
    try:
        out = subprocess.check_output(["pgrep", "-af", "codex app-server"], text=True)
    except subprocess.CalledProcessError:
        return False
    return bool(out.strip())


def rpc(method: str, params: dict[str, Any], request_id: int = 1) -> dict[str, Any]:
    if not CONTROL_SOCK.exists():
        raise RuntimeError(f"Codex app-server control socket not found: {CONTROL_SOCK}")
    payload = {"jsonrpc": "2.0", "id": request_id, "method": method, "params": params}
    proc = subprocess.run(
        ["codex", "app-server", "proxy"],
        input=json.dumps(payload, ensure_ascii=False) + "\n",
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.strip() or proc.stdout.strip())
    lines = [line for line in proc.stdout.splitlines() if line.strip()]
    if not lines:
        return {}
    return json.loads(lines[-1])


def print_json(obj: Any) -> None:
    print(json.dumps(obj, ensure_ascii=False, indent=2), flush=True)


def preset_for(name: str) -> dict[str, Any]:
    if name in HEARTBEAT_PRESETS:
        return HEARTBEAT_PRESETS[name]
    for preset_name, preset in HEARTBEAT_PRESETS.items():
        if name in preset.get("aliases", []):
            resolved = dict(preset)
            resolved["resolved_name"] = preset_name
            return resolved
    choices = ", ".join(sorted(HEARTBEAT_PRESETS))
    raise SystemExit(f"Unknown heartbeat preset {name!r}. Available: {choices}")


def codex_bin() -> str:
    found = shutil.which("codex")
    if found:
        return found
    for path in ["/opt/homebrew/bin/codex", "/usr/local/bin/codex"]:
        if Path(path).exists():
            return path
    return "codex"


def launchd_domain() -> str:
    return f"gui/{os.getuid()}"


def launchd_plist_path(label: str) -> Path:
    return LAUNCH_AGENTS_DIR / f"{label}.plist"


def run_launchctl(args: list[str], check: bool = False) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["launchctl", *args],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=check,
    )


def launchd_loaded(label: str) -> bool:
    proc = run_launchctl(["print", f"{launchd_domain()}/{label}"])
    return proc.returncode == 0


def heartbeat_plist(
    name: str,
    preset: dict[str, Any],
    *,
    interval_seconds: int | None = None,
    message: str | None = None,
    min_idle_seconds: int | None = None,
    disable_after_send: bool = False,
) -> dict[str, Any]:
    script = str(Path(__file__).resolve())
    out_log = LAUNCHD_LOG_DIR / f"{name}.out.log"
    err_log = LAUNCHD_LOG_DIR / f"{name}.err.log"
    program_args = [
        script,
        "--title",
        preset["title"],
        "--cwd",
        preset["cwd"],
        "--min-idle-seconds",
        str(min_idle_seconds if min_idle_seconds is not None else preset["min_idle_seconds"]),
        "heartbeat",
        "--send",
        message if message is not None else preset["message"],
    ]
    if disable_after_send or bool(preset.get("disable_after_send")):
        program_args.extend(["--disable-launchd-name-after-send", name])
    return {
        "Label": preset["label"],
        "ProgramArguments": program_args,
        "StartInterval": int(interval_seconds if interval_seconds is not None else preset["interval"]),
        "WorkingDirectory": preset["cwd"],
        "EnvironmentVariables": {
            "PATH": f"{Path(codex_bin()).parent}:/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin",
            "CODEX_HOME": str(CODEX_HOME),
        },
        "StandardOutPath": str(out_log),
        "StandardErrorPath": str(err_log),
    }


def write_plist(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    LAUNCHD_LOG_DIR.mkdir(parents=True, exist_ok=True)
    with path.open("wb") as fh:
        plistlib.dump(payload, fh, sort_keys=False)


def cmd_list(args: argparse.Namespace) -> None:
    rows = find_threads(args.title, args.cwd, args.thread_id, limit=args.limit)
    print_json(
        [
            {
                "id": row.id,
                "title": row.title,
                "cwd": row.cwd,
                "rollout_path": row.rollout_path,
                "source": row.source,
                "updated_at_ms": row.updated_at_ms,
                "model": row.model,
                "reasoning_effort": row.reasoning_effort,
            }
            for row in rows
        ]
    )


def cmd_status(args: argparse.Namespace) -> None:
    row = resolve_one_thread(args)
    agent_job_counts = count_agent_job_items(row.id)
    unread_inbox = count_unread_inbox(row.id)

    status: dict[str, Any] = {
        "thread": {
            "id": row.id,
            "title": row.title,
            "cwd": row.cwd,
            "rollout_path": row.rollout_path,
            "source": row.source,
            "updated_at_ms": row.updated_at_ms,
            "model": row.model,
            "reasoning_effort": row.reasoning_effort,
        },
        "app_server": {
            "running": app_server_running(),
            "control_socket": str(CONTROL_SOCK),
            "control_socket_exists": CONTROL_SOCK.exists(),
        },
        "local_counts": {
            "inbox_unread_for_thread": unread_inbox,
            "agent_job_items_by_status_for_thread": agent_job_counts,
            "ui_pending_user_message_count": None,
            "ui_pending_user_message_count_reason": (
                "Not persisted in state_5.sqlite/codex-dev.db and not queryable unless "
                "the running App exposes an app-server control socket."
            ),
        },
        "rollout_idle_state": rollout_idle_state(row.rollout_path, args.min_idle_seconds),
    }

    if CONTROL_SOCK.exists():
        try:
            status["app_server"]["thread_read"] = rpc(
                "thread/read", {"threadId": row.id, "includeTurns": False}
            )
        except Exception as exc:  # noqa: BLE001 - diagnostic script
            status["app_server"]["thread_read_error"] = str(exc)

    print_json(status)


def cmd_enqueue(args: argparse.Namespace) -> None:
    row = resolve_one_thread(args)
    params = {
        "threadId": row.id,
        "input": [{"type": "text", "text": args.message}],
    }
    if args.cwd_override:
        params["cwd"] = args.cwd_override
    if args.effort:
        params["effort"] = args.effort

    result = rpc("turn/start", params, request_id=int(time.time()))
    print_json(
        {
            "target_thread": {"id": row.id, "title": row.title, "cwd": row.cwd},
            "result": result,
        }
    )


def cmd_heartbeat(args: argparse.Namespace) -> None:
    row = resolve_one_thread(args)
    idle = rollout_idle_state(row.rollout_path, args.min_idle_seconds)
    base = {
        "target_thread": {"id": row.id, "title": row.title, "cwd": row.cwd},
        "idle_check": idle,
        "transport": args.transport,
        "ui_visibility": (
            "app-visible-if-control-socket-works"
            if args.transport == "app-server"
            else "headless-cli-resume; Codex App may not refresh"
        ),
        "sent": False,
        "dry_run": not args.send,
    }
    if not idle.get("can_send"):
        base["decision"] = "skip_not_idle"
        print_json(base)
        return
    if not args.send:
        base["decision"] = "dry_run_would_send"
        print_json(base)
        return

    if args.transport == "app-server":
        params = {"threadId": row.id, "input": [{"type": "text", "text": args.message}]}
        base["result"] = rpc("turn/start", params, request_id=int(time.time()))
        base["sent"] = True
        base["decision"] = "sent_app_server"
        if args.disable_launchd_name_after_send:
            base["will_disable_launchd_name_after_send"] = args.disable_launchd_name_after_send
            print_json(base)
            cmd_heartbeat_disable(argparse.Namespace(name=args.disable_launchd_name_after_send))
            return
        print_json(base)
        return

    cmd = ["codex", "exec", "resume", row.id, args.message]
    if args.json:
        cmd.insert(3, "--json")
    proc = subprocess.run(
        cmd,
        cwd=row.cwd,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    base["result"] = {
        "returncode": proc.returncode,
        "stdout_tail": proc.stdout[-4000:],
        "stderr_tail": proc.stderr[-4000:],
    }
    base["sent"] = proc.returncode == 0
    base["decision"] = "sent_cli_resume" if proc.returncode == 0 else "cli_resume_failed"
    if base["sent"] and args.disable_launchd_name_after_send:
        base["will_disable_launchd_name_after_send"] = args.disable_launchd_name_after_send
        print_json(base)
        cmd_heartbeat_disable(argparse.Namespace(name=args.disable_launchd_name_after_send))
        return
    print_json(base)


def cmd_install_preset(args: argparse.Namespace) -> None:
    preset = preset_for(args.name)
    name = preset.get("resolved_name", args.name)
    label = preset["label"]
    path = launchd_plist_path(label)
    if launchd_loaded(label):
        run_launchctl(["bootout", launchd_domain(), str(path)])
    write_plist(
        path,
        heartbeat_plist(
            name,
            preset,
            interval_seconds=args.interval_seconds,
            message=args.message,
            min_idle_seconds=args.min_idle_seconds_override,
            disable_after_send=args.disable_after_send,
        ),
    )
    if not args.no_load:
        proc = run_launchctl(["bootstrap", launchd_domain(), str(path)])
        if proc.returncode != 0 and "already bootstrapped" not in proc.stderr:
            raise RuntimeError(proc.stderr.strip() or proc.stdout.strip())
    print_json(
        {
            "installed": True,
            "name": name,
            "label": label,
            "plist": str(path),
            "loaded": launchd_loaded(label),
            "interval_seconds": preset["interval"],
            "installed_interval_seconds": args.interval_seconds or preset["interval"],
            "target": {"title": preset["title"], "cwd": preset["cwd"]},
            "transport": "cli-resume",
            "ui_visibility": "headless; Codex App may not refresh until reloaded",
            "logs": {
                "stdout": str(LAUNCHD_LOG_DIR / f"{name}.out.log"),
                "stderr": str(LAUNCHD_LOG_DIR / f"{name}.err.log"),
            },
        }
    )


def cmd_heartbeat_enable(args: argparse.Namespace) -> None:
    preset = preset_for(args.name)
    name = preset.get("resolved_name", args.name)
    label = preset["label"]
    path = launchd_plist_path(label)
    if not path.exists():
        write_plist(path, heartbeat_plist(name, preset))
    if not launchd_loaded(label):
        proc = run_launchctl(["bootstrap", launchd_domain(), str(path)])
        if proc.returncode != 0 and "already bootstrapped" not in proc.stderr:
            raise RuntimeError(proc.stderr.strip() or proc.stdout.strip())
    print_json({"name": name, "label": label, "enabled": True, "loaded": launchd_loaded(label)})


def cmd_heartbeat_disable(args: argparse.Namespace) -> None:
    preset = preset_for(args.name)
    name = preset.get("resolved_name", args.name)
    label = preset["label"]
    path = launchd_plist_path(label)
    if launchd_loaded(label):
        proc = run_launchctl(["bootout", launchd_domain(), str(path)])
        if proc.returncode != 0:
            raise RuntimeError(proc.stderr.strip() or proc.stdout.strip())
    print_json({"name": name, "label": label, "enabled": False, "loaded": launchd_loaded(label)})


def cmd_heartbeat_kick(args: argparse.Namespace) -> None:
    preset = preset_for(args.name)
    name = preset.get("resolved_name", args.name)
    label = preset["label"]
    if not launchd_loaded(label):
        raise RuntimeError(f"{label} is not loaded; run heartbeat-enable {name} first")
    proc = run_launchctl(["kickstart", "-k", f"{launchd_domain()}/{label}"])
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.strip() or proc.stdout.strip())
    print_json({"name": name, "label": label, "kicked": True})


def cmd_heartbeat_status(args: argparse.Namespace) -> None:
    preset = preset_for(args.name)
    name = preset.get("resolved_name", args.name)
    label = preset["label"]
    path = launchd_plist_path(label)
    proc = run_launchctl(["print", f"{launchd_domain()}/{label}"])
    print_json(
        {
            "name": name,
            "label": label,
            "plist": str(path),
            "plist_exists": path.exists(),
            "loaded": proc.returncode == 0,
            "interval_seconds": preset["interval"],
            "target": {"title": preset["title"], "cwd": preset["cwd"]},
            "transport": "cli-resume",
            "ui_visibility": "headless; Codex App may not refresh until reloaded",
            "launchctl_print_tail": (proc.stdout or proc.stderr)[-4000:],
            "logs": {
                "stdout": str(LAUNCHD_LOG_DIR / f"{name}.out.log"),
                "stderr": str(LAUNCHD_LOG_DIR / f"{name}.err.log"),
            },
        }
    )


def cmd_heartbeat_uninstall(args: argparse.Namespace) -> None:
    preset = preset_for(args.name)
    name = preset.get("resolved_name", args.name)
    label = preset["label"]
    path = launchd_plist_path(label)
    if launchd_loaded(label):
        run_launchctl(["bootout", launchd_domain(), str(path)])
    if path.exists():
        path.unlink()
    print_json({"name": name, "label": label, "uninstalled": True, "plist_exists": path.exists()})


def cmd_heartbeat_presets(_args: argparse.Namespace) -> None:
    data = {}
    for name, preset in HEARTBEAT_PRESETS.items():
        label = preset["label"]
        data[name] = {
            "aliases": preset.get("aliases", []),
            "label": label,
            "interval_seconds": preset["interval"],
            "target": {"title": preset["title"], "cwd": preset["cwd"]},
            "transport": "cli-resume",
            "ui_visibility": "headless; Codex App may not refresh until reloaded",
            "plist": str(launchd_plist_path(label)),
            "loaded": launchd_loaded(label),
        }
    print_json(data)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--thread-id", help="Exact Codex thread id.")
    parser.add_argument("--title", default="主控", help="Substring match on thread title.")
    parser.add_argument("--cwd", help="Exact cwd match.")
    parser.add_argument("--limit", type=int, default=20)
    parser.add_argument("--min-idle-seconds", type=int, default=120)

    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("list", help="List matching threads from the local state DB.").set_defaults(func=cmd_list)
    sub.add_parser("status", help="Inspect target thread and local queue-like counts.").set_defaults(func=cmd_status)

    enqueue = sub.add_parser("enqueue", help="Start/steer a turn on the target thread via app-server RPC.")
    enqueue.add_argument("message")
    enqueue.add_argument("--cwd-override", help="Optional cwd override for this and subsequent turns.")
    enqueue.add_argument("--effort", choices=["none", "minimal", "low", "medium", "high", "xhigh"])
    enqueue.set_defaults(func=cmd_enqueue)

    heartbeat = sub.add_parser(
        "heartbeat",
        help=(
            "If the target thread is idle, send a heartbeat prompt. Defaults to dry-run. "
            "Use --send to actually send."
        ),
    )
    heartbeat.add_argument("message")
    heartbeat.add_argument("--send", action="store_true")
    heartbeat.add_argument("--transport", choices=["cli-resume", "app-server"], default="cli-resume")
    heartbeat.add_argument("--json", action="store_true", help="Pass --json to `codex exec resume`.")
    heartbeat.add_argument(
        "--disable-launchd-name-after-send",
        help="After a successful send, unload the named heartbeat preset from launchd.",
    )
    heartbeat.set_defaults(func=cmd_heartbeat)

    install_preset = sub.add_parser("install-preset", help="Install a named launchd heartbeat preset.")
    install_preset.add_argument(
        "name", choices=sorted(set(HEARTBEAT_PRESETS) | {"agent-memory", "csnotes", "csnotes-test"})
    )
    install_preset.add_argument("--no-load", action="store_true", help="Write plist but do not bootstrap it.")
    install_preset.add_argument("--interval-seconds", type=int, help="Override the preset interval.")
    install_preset.add_argument("--message", help="Override the preset heartbeat message.")
    install_preset.add_argument("--min-idle-seconds-override", type=int, help="Override the preset idle cooldown.")
    install_preset.add_argument(
        "--disable-after-send",
        action="store_true",
        help="Generate a temporary heartbeat that disables itself after one successful send.",
    )
    install_preset.set_defaults(func=cmd_install_preset)

    hb_enable = sub.add_parser("heartbeat-enable", help="Load a named launchd heartbeat preset.")
    hb_enable.add_argument("name", choices=sorted(set(HEARTBEAT_PRESETS) | {"agent-memory", "csnotes", "csnotes-test"}))
    hb_enable.set_defaults(func=cmd_heartbeat_enable)

    hb_disable = sub.add_parser("heartbeat-disable", help="Unload a named launchd heartbeat preset.")
    hb_disable.add_argument("name", choices=sorted(set(HEARTBEAT_PRESETS) | {"agent-memory", "csnotes", "csnotes-test"}))
    hb_disable.set_defaults(func=cmd_heartbeat_disable)

    hb_status = sub.add_parser("heartbeat-status", help="Show launchd status for a named heartbeat preset.")
    hb_status.add_argument("name", choices=sorted(set(HEARTBEAT_PRESETS) | {"agent-memory", "csnotes", "csnotes-test"}))
    hb_status.set_defaults(func=cmd_heartbeat_status)

    hb_kick = sub.add_parser("heartbeat-kick", help="Run a loaded heartbeat immediately via launchd.")
    hb_kick.add_argument("name", choices=sorted(set(HEARTBEAT_PRESETS) | {"agent-memory", "csnotes", "csnotes-test"}))
    hb_kick.set_defaults(func=cmd_heartbeat_kick)

    hb_uninstall = sub.add_parser("heartbeat-uninstall", help="Unload and remove a named heartbeat plist.")
    hb_uninstall.add_argument(
        "name", choices=sorted(set(HEARTBEAT_PRESETS) | {"agent-memory", "csnotes", "csnotes-test"})
    )
    hb_uninstall.set_defaults(func=cmd_heartbeat_uninstall)

    sub.add_parser("heartbeat-presets", help="List heartbeat presets and loaded state.").set_defaults(
        func=cmd_heartbeat_presets
    )
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    try:
        args.func(args)
    except Exception as exc:  # noqa: BLE001 - CLI diagnostic
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
