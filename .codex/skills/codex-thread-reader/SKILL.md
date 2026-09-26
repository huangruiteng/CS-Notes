---
name: codex-thread-reader
description: Locate and read a Codex thread by a codex thread link, thread id, or rollout path across all local CODEX_HOME directories (~/.codex, ~/.codex-gpt, ...). Use when the user pastes a codex:// link, asks to understand the 前因后果 of a Codex session, wants a timeline of what a long-running main thread did, or needs to search / export a past Codex conversation.
---

# Codex Thread Reader

## Use this skill when

- The user gives a `codex://threads/<uuid>` link, a bare thread uuid, or asks about "那个 codex 线程 / 主控线程 / session".
- You need the context of a previous Codex run (what was asked, what was decided, what got merged) before continuing work.
- You need to grep a huge rollout (hundreds of MB) without loading it into context.

Do not `cat`, `head`, or `rg` the rollout file directly: main threads are 100–500 MB
JSONL with encrypted reasoning blobs and full tool outputs. Always go through the script.

## Where threads live

- Codex Desktop / CLI can run with several `CODEX_HOME`s on this machine:
  `~/.codex`, `~/.codex-work`, `~/.codex-personal`, ...
  A `codex://threads/<id>` link does not say which home owns it; the script searches all of them.
- Each home stores a thread as `sessions/YYYY/MM/DD/rollout-<local-ts>-<thread-id>.jsonl`
  (archived: `archived_sessions/`), and indexes it in `state_*.sqlite` table `threads`
  (`id, rollout_path, title, cwd, model, archived, ...`).
- Thread ids are UUIDv7: the first 12 hex chars are a unix-ms timestamp, so the date directory can be derived even when the sqlite index is stale.
- Rollout record types: `session_meta`, `turn_context`, `event_msg` (`task_started`, `item_completed`, `task_complete`, `turn_aborted`, `token_count`),
  `response_item` (`message` with `role` + `phase` = `commentary|final_answer`, `custom_tool_call`, `function_call`, `reasoning`), `compacted`, `world_state`, `token_usage_record`.
  Real user prompts are `item_completed` → `UserMessage`; the app wraps them in ambient blocks (`<in-app-browser-context>`, `<environment_context>`, `## My request:`) that the script strips.
  The final answer of a turn is `task_complete.last_agent_message` (also `message` with `phase=final_answer`).

## Quick start

```bash
S="{baseDir}/scripts/codex_thread.py"
THREAD_REF="codex://threads/<thread-id>"  # replace with the target thread link
python3 "$S" locate  "$THREAD_REF"   # which home / file / size / title
python3 "$S" summary "$THREAD_REF"                   # cwd, models, span, turns, compactions, tools
python3 "$S" turns   "$THREAD_REF" --width 160                                    # one block per turn: time, prompt, final answer
python3 "$S" turns   "$THREAD_REF" --since 2026-09-20 --last 15
python3 "$S" messages "$THREAD_REF" --turn 104,185 --full                         # full prompt + final answer of chosen turns
python3 "$S" messages "$THREAD_REF" --since 2026-09-24 --role user --full         # what the user asked recently
python3 "$S" search  "$THREAD_REF" 'PR #?\d+|self-?merge' --max 50                # regex over prompts/answers
python3 "$S" search  "$THREAD_REF" 'git status' --tools                          # also tool inputs/outputs (slower)
python3 "$S" tools   "$THREAD_REF" --commands --turn 185 --width 240              # every exec input in a turn
python3 "$S" export  "$THREAD_REF" --repo /path/to/repo               # Markdown transcript -> .local/codex-thread-dumps/<id>.md
```

A uuid prefix is enough as long as it is unique. `--since/--until/--last/--turn` share the turn
numbering printed by `turns`. All commands stream the file; a 420 MB rollout takes ~1–3 s.

## Recommended reading workflow for "了解前因后果"

1. `locate` + `summary`: confirm the right home/file, cwd, time span, model, number of turns and compactions.
2. `turns` over the whole thread: skim first-line prompts and final answers to build a timeline; note turn numbers of pivotal moments (decisions, merges, incidents, changes of direction).
3. `messages --turn ... --full` for those pivotal turns; add `--commentary` only when you need the agent's intermediate reasoning notes.
4. `search` for the specific entities you care about (PR numbers, file paths, people, project names, error strings). Use `--tools` when you need to know what commands actually ran.
5. If the thread will be referenced again, `export` it once into `.local/codex-thread-dumps/` and read the Markdown; never copy the dump into `Notes/` or any tracked file.

## Privacy and boundaries

- Main threads usually contain career, company, legal, and personal content. Treat everything read as `.local`-only material: summarize into tracked files only after 脱敏, following `AGENTS.md` §4.A.10 and §5.
- Default export location is `<repo>/.local/codex-thread-dumps/`, which is git-ignored. Do not pass `--out` to a tracked path.
- Reasoning blobs are encrypted and are not decoded; tool outputs may contain tokens or internal URLs, so keep `search --tools` output out of tracked files.
- Never modify rollout files or the sqlite indexes; the script opens sqlite read-only.

## Troubleshooting

- `not found`: the thread may belong to a home not under `~/.codex*` (set `CODEX_HOME=...`), or the id may be a remote/cloud thread with no local rollout. The error prints the UUIDv7 timestamp so you can check that day's `sessions/` directory manually.
- Multiple candidates: the sqlite hit is preferred over glob hits; a thread forked/moved between homes can appear twice. Check `size` and `title`.
- Turn without a user prompt: automation / heartbeat runs or turns whose prompt was only an attachment; use `messages --commentary` to see what happened.
- Stale numbers after the thread keeps running: turn indices are recomputed on every call, so re-run `turns` before citing a number.
