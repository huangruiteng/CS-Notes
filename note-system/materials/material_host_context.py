"""Read a local native agent host's active Turn without creating or mutating sessions.

This supplies host provenance, not publication approval. The source adapter must
still verify its OS owner, live App/workspace grant, operation intent and CAS.
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


def _canonical_uuid(value, *, label):
    try:
        if not isinstance(value, str) or str(uuid.UUID(value)) != value:
            raise ValueError("noncanonical UUID")
    except (ValueError, TypeError, AttributeError):
        raise ValueError(f"{label} identity is missing or invalid") from None
    return value


def _workspace_digest(workspace):
    return hashlib.sha256(str(workspace).encode()).hexdigest()


def _detect_host_families(env):
    families = []
    if env.get("CODEX_THREAD_ID") or env.get("CODEX_SESSION_ID"):
        families.append("codex")
    if env.get("ANTIGRAVITY_AGENT") or env.get("ANTIGRAVITY_CONVERSATION_ID"):
        families.append("antigravity")
    if env.get("CLAUDECODE") or env.get("CLAUDE_SESSION_ID"):
        families.append("claude-code")
    return families


def has_native_host_env(environ=None):
    """Return whether caller environment declares a supported local agent host."""
    env = os.environ if environ is None else environ
    return bool(_detect_host_families(env))


def _active_codex_turn(rollout, thread_id, workspace):
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
        "workspace_digest": _workspace_digest(workspace),
        "write_policy": policy,
    }


def _resolve_codex_owner_turn(workspace, env, homes=None):
    thread_id = _canonical_uuid(env.get("CODEX_THREAD_ID"), label="native Codex thread")
    if env.get("CODEX_SESSION_ID", thread_id) != thread_id:
        raise ValueError("native Codex session/thread identity mismatch")
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
            matches.append(_active_codex_turn(rollout, thread_id, workspace))
    if len(matches) != 1:
        raise ValueError("native Codex owner Turn is missing or ambiguous")
    return matches[0]


def _planner_step_has_tool_calls(record):
    if bool(record.get("tool_calls")):
        return True
    truncated = record.get("truncated_fields")
    return isinstance(truncated, list) and "tool_calls" in truncated


def _resolve_antigravity_owner_turn(workspace, env, app_data_dir=None):
    if env.get("ANTIGRAVITY_AGENT") != "1":
        raise ValueError("native Antigravity agent marker is missing")
    conversation_id = _canonical_uuid(
        env.get("ANTIGRAVITY_CONVERSATION_ID"),
        label="native Antigravity conversation",
    )
    raw_meta = env.get("ANTIGRAVITY_SOURCE_METADATA")
    if not isinstance(raw_meta, str) or not raw_meta.strip():
        raise ValueError("native Antigravity tool provenance metadata is missing")
    try:
        meta = json.loads(raw_meta)
    except json.JSONDecodeError:
        raise ValueError("native Antigravity tool provenance metadata is invalid") from None
    tool = meta.get("tool") if isinstance(meta, dict) else None
    step_index = tool.get("stepIndex") if isinstance(tool, dict) else None
    if (
        not isinstance(tool, dict)
        or tool.get("conversationId") != conversation_id
        or type(step_index) is not int
        or step_index < 0
    ):
        raise ValueError("native Antigravity conversation/step provenance mismatch")

    explicit_ws = env.get("ANTIGRAVITY_WORKSPACE_PATH")
    if isinstance(explicit_ws, str) and explicit_ws.strip() and explicit_ws != "outside-of-project":
        bound_ws = Path(explicit_ws).resolve()
        if not (workspace == bound_ws or workspace.is_relative_to(bound_ws)):
            raise ValueError("native Antigravity session belongs to another workspace")

    if app_data_dir is not None:
        app_root = Path(app_data_dir).resolve()
    else:
        raw_app_dir = env.get("ANTIGRAVITY_APP_DATA_DIR")
        if not isinstance(raw_app_dir, str) or not raw_app_dir.strip():
            raise ValueError("native Antigravity app data directory is missing")
        app_root = Path(raw_app_dir).resolve()
        expected_parent = (Path.home() / ".gemini").resolve()
        if not app_root.is_relative_to(expected_parent):
            raise ValueError("native Antigravity app data directory is outside ~/.gemini")

    if not app_root.is_dir() or app_root.stat().st_uid != os.getuid():
        raise ValueError("native Antigravity app data directory is missing or belongs to another OS owner")

    transcript = (app_root / "brain" / conversation_id / ".system_generated" / "logs" / "transcript.jsonl").resolve()
    if not transcript.is_relative_to(app_root / "brain") or not transcript.is_file():
        raise ValueError("native Antigravity transcript is missing or outside brain store")
    if transcript.stat().st_uid != os.getuid():
        raise ValueError("native Antigravity transcript belongs to another OS owner")

    latest_user_step = None
    latest_planner = None
    seen_steps = set()

    with transcript.open(encoding="utf-8") as stream:
        for line in stream:
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                raise ValueError("native host metadata is incomplete; retry after host flush") from None
            if not isinstance(record, dict):
                raise ValueError("native host metadata record is malformed")
            idx = record.get("step_index")
            if type(idx) is not int:
                continue
            seen_steps.add(idx)
            rtype = record.get("type")
            if rtype == "USER_INPUT":
                latest_user_step = idx if latest_user_step is None else max(latest_user_step, idx)
            elif rtype == "PLANNER_RESPONSE":
                if latest_planner is None or idx > latest_planner["step_index"]:
                    latest_planner = record

    if (
        latest_user_step is None
        or latest_planner is None
        or latest_planner["step_index"] <= latest_user_step
        or not _planner_step_has_tool_calls(latest_planner)
        or step_index <= latest_planner["step_index"]
        or step_index in seen_steps
    ):
        raise ValueError("native Antigravity owner Turn is not active")

    planner_calls = latest_planner.get("tool_calls")
    if isinstance(planner_calls, list) and planner_calls:
        if step_index > latest_planner["step_index"] + len(planner_calls) + 4:
            raise ValueError("native Antigravity step index exceeds active tool batch")

    return {
        "host_surface": "antigravity",
        "thread_id": conversation_id,
        "turn_id": f"antigravity:{conversation_id}:u{latest_user_step}",
        "workspace_digest": _workspace_digest(workspace),
        "write_policy": "workspace-write",
    }


def _active_claude_session(transcript, workspace):
    session_id = None
    cwd_matched = False
    latest_user_uuid = None
    active_tool_turn = False
    with transcript.open(encoding="utf-8") as stream:
        for line in stream:
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                raise ValueError("native host metadata is incomplete; retry after host flush") from None
            if not isinstance(record, dict):
                raise ValueError("native host metadata record is malformed")
            sid = record.get("sessionId")
            if isinstance(sid, str) and sid:
                session_id = sid
            rec_cwd = record.get("cwd")
            if isinstance(rec_cwd, str) and rec_cwd:
                if Path(rec_cwd).resolve() != workspace:
                    raise ValueError("native Claude session belongs to another workspace")
                cwd_matched = True
            rtype = record.get("type")
            if rtype == "user":
                msg = record.get("message") if isinstance(record.get("message"), dict) else {}
                content = msg.get("content")
                is_tool_result = isinstance(content, list) and any(
                    isinstance(item, dict) and item.get("type") == "tool_result" for item in content
                )
                if not is_tool_result:
                    latest_user_uuid = str(record.get("uuid") or "user")
                active_tool_turn = False
            elif rtype == "assistant":
                msg = record.get("message") if isinstance(record.get("message"), dict) else {}
                content = msg.get("content")
                has_tool_use = isinstance(content, list) and any(
                    isinstance(item, dict) and item.get("type") == "tool_use" for item in content
                )
                active_tool_turn = has_tool_use
    if not session_id or not cwd_matched or not latest_user_uuid or not active_tool_turn:
        return None
    return {
        "host_surface": "claude-code",
        "thread_id": session_id,
        "turn_id": f"claude:{session_id}:{latest_user_uuid}",
        "workspace_digest": _workspace_digest(workspace),
        "write_policy": "workspace-write",
    }


def _resolve_claude_owner_turn(workspace, env, claude_home=None):
    if env.get("CLAUDECODE") != "1":
        raise ValueError("native Claude Code agent marker is missing")
    root = Path(claude_home).resolve() if claude_home is not None else (Path.home() / ".claude").resolve()
    projects_dir = root / "projects"
    if not projects_dir.is_dir() or projects_dir.stat().st_uid != os.getuid():
        raise ValueError("native Claude session store is missing or belongs to another OS owner")

    explicit_session = env.get("CLAUDE_SESSION_ID")
    if explicit_session is not None:
        _canonical_uuid(explicit_session, label="native Claude session")

    candidates = []
    for path in sorted(projects_dir.glob("*/*.jsonl")):
        resolved = path.resolve()
        if not resolved.is_relative_to(projects_dir):
            continue
        if resolved.stat().st_uid != os.getuid():
            raise ValueError("native Claude session belongs to another OS owner")
        if explicit_session and resolved.stem != explicit_session:
            continue
        try:
            active = _active_claude_session(resolved, workspace)
        except ValueError as exc:
            if explicit_session or "incomplete" in str(exc) or "malformed" in str(exc):
                raise
            continue
        if active is not None:
            if explicit_session and active["thread_id"] != explicit_session:
                raise ValueError("native Claude session identity mismatch")
            candidates.append(active)

    if len(candidates) != 1:
        raise ValueError("native Claude owner Turn is missing or ambiguous")
    return candidates[0]


def resolve_native_owner_turn(
    workspace,
    *,
    environ=None,
    homes=None,
    antigravity_app_dir=None,
    claude_home=None,
):
    """Resolve the caller's real active Turn across verified local agent hosts."""
    env = os.environ if environ is None else environ
    workspace = Path(workspace).resolve()
    families = _detect_host_families(env)
    if len(families) > 1:
        raise ValueError("ambiguous native agent host environment")
    if not families:
        raise ValueError("native host identity is missing or invalid")
    family = families[0]
    if family == "codex":
        return _resolve_codex_owner_turn(workspace, env, homes=homes)
    if family == "antigravity":
        return _resolve_antigravity_owner_turn(workspace, env, app_data_dir=antigravity_app_dir)
    return _resolve_claude_owner_turn(workspace, env, claude_home=claude_home)
