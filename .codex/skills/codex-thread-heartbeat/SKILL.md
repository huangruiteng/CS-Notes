---
name: codex-thread-heartbeat
description: Inspect and manage guarded Codex App-native or launchd heartbeats for Codex main control threads. Use when the user wants Codex to periodically continue a specific thread only when it is idle, avoid interrupting active work, keep App-visible interactions, inspect thread status, or enable/disable project autopilot heartbeats.
metadata:
  short-description: Guarded Codex thread heartbeat automation
---

# Codex Thread Heartbeat

Use this skill to set up or inspect local heartbeats that periodically nudge a specific Codex thread, but only after an idle guard passes.

The pain it solves:

- Fixed short intervals keep the agent moving, but they can interrupt active work and waste tokens.
- Fixed long intervals are cheaper, but create annoying dead time after a task finishes.
- Codex App threads are persistent sessions, not ordinary CLI processes; blindly running `codex exec resume` can race with the App if the target thread is still active.

The bundled script reads Codex local thread metadata from `~/.codex/state_5.sqlite`, checks the target rollout JSONL for recent `final_answer`, unresolved tool calls, and cooldown, then sends a heartbeat with `codex exec resume <thread_id>` only when it is safe. This is useful as a fallback, but App-native heartbeats are preferred when the user needs the interaction to show up in the Codex App UI.

Important limitation: `codex exec resume` is a headless fallback. It writes to the correct rollout and can complete the turn, but the currently open Codex App view may not refresh because the turn did not originate from that renderer. Do not leave long-running launchd heartbeats enabled if the user expects in-App visibility; prefer Codex App's built-in heartbeat automation or an App/server transport once a working control socket is available.

## Transport Choice

Prefer this order:

1. **Codex App built-in heartbeat** via App automation records under `$CODEX_HOME/automations/`.
   - Best for user-visible main-control threads.
   - The App bundle contains a heartbeat scheduler that checks renderer eligibility, collaboration mode, permissions, thread status, active flags, and recent rollout activity before `turn/start`.
   - It blocks on states such as `waiting_on_user_input`, `waiting_on_approval`, `active_with_flags`, and recent non-terminal rollout events, so it should not inject a heartbeat while the target thread is still running.
2. **App-server control transport** if a real App server control socket is exposed.
   - Best theoretical shape: `thread/resume` then `turn/start` over the same notification stream the App can render.
   - Current local App process may only expose app-server over Electron-owned stdio, not a public control socket.
3. **Launchd + `codex exec resume`** as a headless fallback.
   - Useful for log-based automation or CLI-only workflows.
   - Keep conservative idle guards and avoid expensive prompts because the App UI may not refresh.

## Quick Commands

### App-Native Heartbeats

For user-visible controller threads, prefer the Codex App automation card or `automation_update` tool. Do not edit `$CODEX_HOME/automations/*.toml` directly unless you are only inspecting/debugging.

Known local App-native heartbeat records:

- `cs-notes-autopilot`: CS-Notes controller thread, every 120 minutes.
- `agent-harness-heartbeat`: Agent Harness controller thread.

Use App-native heartbeat when the user says they want:

- messages visible in the Codex App thread;
- no message injected while the thread is still running;
- a target thread bound by `target_thread_id`;
- normal App automation controls for pause/resume.

### Headless Launchd Fallback

Run from any repo:

```bash
~/.codex/skills/codex-thread-heartbeat/scripts/codex-thread-queue.py heartbeat-presets
```

Install built-in presets:

```bash
~/.codex/skills/codex-thread-heartbeat/scripts/codex-thread-queue.py install-preset agent-harness
~/.codex/skills/codex-thread-heartbeat/scripts/codex-thread-queue.py install-preset cs-notes
```

Enable / disable:

```bash
~/.codex/skills/codex-thread-heartbeat/scripts/codex-thread-queue.py heartbeat-disable agent-harness
~/.codex/skills/codex-thread-heartbeat/scripts/codex-thread-queue.py heartbeat-enable agent-harness
```

Inspect:

```bash
~/.codex/skills/codex-thread-heartbeat/scripts/codex-thread-queue.py heartbeat-status agent-harness
~/.codex/skills/codex-thread-heartbeat/scripts/codex-thread-queue.py --title "agent-harness 主控" --cwd /path/to/repo status
```

One-off delivery test:

```bash
~/.codex/skills/codex-thread-heartbeat/scripts/codex-thread-queue.py install-preset cs-notes-test
```

`cs-notes-test` runs every 30 seconds and disables itself after the first successful delivery.

## Safety Rules

- Prefer `status` or dry-run `heartbeat` before enabling an automation.
- Do not use direct `codex exec resume` automation without idle checks.
- Treat `cli-resume` heartbeats as headless. Confirm the user accepts log-based visibility, desktop notifications, or manual App reload before enabling them for expensive project work.
- If the user needs Codex App-visible interaction, try the built-in heartbeat automation first and keep launchd disabled until the App-visible path is verified.
- If the App exposes an app-server control socket in the future, prefer targeted `turn/start`; until then, `codex exec resume` is the practical fallback.
- Keep heartbeat prompts bounded: ask for one small verifiable step, status-only behavior when work is running, and explicit changed files / validation.

## Open Source Positioning

When packaging this skill publicly, describe it as a guarded local productivity automation for Codex power users, not as an official Codex API. Be explicit that it uses local Codex state files and conservative rollout inspection, so users should treat it as best-effort and version-sensitive.
