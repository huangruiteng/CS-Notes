"""Read a Codex-owned active Turn without creating a session or changing its state.

This supplies host provenance, not publication approval. The source adapter must
still verify its owner, live App/workspace grant, operation intent and CAS.
Only host metadata and lifecycle records are inspected; messages and tool
payloads are neither returned nor written to receipts.
"""

import hashlib
from contextlib import closing
import json
import os
from pathlib import Path
import sqlite3
import uuid


def _active_turn(rollout, thread_id, workspace):
    metadata = None
    active = None
    context = None
    with rollout.open(encoding="utf-8") as stream:
        for line in stream:
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                raise ValueError("native host metadata is incomplete; retry after host flush") from None
            payload = record.get("payload", {})
            if record.get("type") == "session_meta":
                metadata = payload
            elif record.get("type") == "event_msg":
                event = payload.get("type")
                if event == "task_started":
                    active = payload.get("turn_id")
                    context = None
                elif event in {"task_complete", "turn_aborted"}:
                    if not payload.get("turn_id") or payload["turn_id"] == active:
                        active = None
                        context = None
            elif record.get("type") == "turn_context":
                if active and payload.get("turn_id") == active:
                    context = payload
    if not metadata or metadata.get("id") != thread_id:
        raise ValueError("native host session identity mismatch")
    # LoopX uses the native Codex app-server with its own client originator.
    # That label is provenance only; the indexed active Turn/write checks remain.
    origins = (("vscode", "Codex Desktop"), ("vscode", "loopx_chat"), ("cli", "codex_cli_rs"))
    if (metadata.get("source"), metadata.get("originator")) not in origins:
        raise ValueError("unsupported native Codex host")
    if Path(metadata.get("cwd", "")).resolve() != workspace:
        raise ValueError("native host session belongs to another workspace")
    if not active or not context:
        raise ValueError("native Codex owner Turn is not active")
    if Path(context.get("cwd", "")).resolve() != workspace:
        raise ValueError("native host Turn belongs to another workspace")
    policy = context.get("sandbox_policy", {}).get("type")
    if policy not in {"workspace-write", "danger-full-access"}:
        raise ValueError("native host Turn does not grant workspace writes")
    return {
        "host_surface": "codex-app" if metadata["source"] == "vscode" else "codex-cli",
        "thread_id": thread_id,
        "turn_id": active,
        "workspace_digest": hashlib.sha256(str(workspace).encode()).hexdigest(),
        "write_policy": policy,
    }


def resolve_native_owner_turn(workspace, *, environ=None, homes=None):
    """Resolve the caller's real indexed Turn; an environment ID alone is insufficient."""
    env = os.environ if environ is None else environ
    thread_id = env.get("CODEX_THREAD_ID")
    try:
        if str(uuid.UUID(thread_id)) != thread_id:
            raise ValueError("noncanonical UUID")
    except (ValueError, TypeError, AttributeError):
        raise ValueError("native Codex thread identity is missing or invalid") from None
    if env.get("CODEX_SESSION_ID", thread_id) != thread_id:
        raise ValueError("native Codex session/thread identity mismatch")
    workspace = Path(workspace).resolve()
    if homes is None:
        homes = [Path(env["CODEX_HOME"])] if env.get("CODEX_HOME") else sorted(Path.home().glob(".codex*"))
    matches = []
    for home in homes:
        home = Path(home).resolve()
        for index in sorted(home.glob("state_*.sqlite")):
            if index.stat().st_uid != os.getuid():
                raise ValueError("native host index belongs to another OS owner")
            try:
                with closing(sqlite3.connect(index.as_uri() + "?mode=ro", uri=True)) as connection:
                    row = connection.execute(
                        "SELECT cwd, rollout_path, archived FROM threads WHERE id = ?",
                        (thread_id,),
                    ).fetchone()
            except sqlite3.Error:
                raise ValueError("native host index is unavailable or incompatible") from None
            if row is None:
                continue
            cwd, path, archived = row
            if archived or Path(cwd).resolve() != workspace:
                raise ValueError("native thread is archived or belongs to another workspace")
            rollout = Path(path).resolve()
            if not rollout.is_relative_to(home / "sessions"):
                raise ValueError("native rollout is outside the active host session store")
            if rollout.stat().st_uid != os.getuid():
                raise ValueError("native host session belongs to another OS owner")
            matches.append(_active_turn(rollout, thread_id, workspace))
    if len(matches) != 1:
        raise ValueError("native Codex owner Turn is missing or ambiguous")
    return matches[0]
