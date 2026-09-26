#!/usr/bin/env python3
"""Locate and read Codex threads (codex://threads/<uuid>) from local rollout files.

Codex Desktop / CLI may run with several CODEX_HOME directories (~/.codex,
~/.codex-gpt, ...). Each one stores threads as JSONL rollouts under
`sessions/YYYY/MM/DD/rollout-<ts>-<thread-id>.jsonl` (or `archived_sessions/`)
and indexes them in `state_*.sqlite` (table `threads`). Rollouts for long-running
main threads can reach hundreds of MB, so this tool streams the file and only
keeps compact projections.

Subcommands:
  locate   <ref>                 find the rollout file for a thread ref
  summary  <ref>                 metadata + counts + turn/time span
  turns    <ref> [--since ..]    one line per turn: time, user prompt, final answer
  messages <ref> [--role ..]     user prompts / final answers in order (readable)
  search   <ref> <regex>         grep prompts, answers, tool inputs/outputs
  tools    <ref>                 tool usage stats; --commands lists exec inputs
  export   <ref> [--out PATH]    write a Markdown transcript (default: .local/)

<ref> may be `codex://threads/<uuid>`, a bare uuid, a uuid prefix, or a file path.
"""
from __future__ import annotations

import argparse
import datetime as dt
import glob
import json
import os
import re
import sqlite3
import sys
from collections import Counter
from pathlib import Path

UUID_RE = re.compile(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}", re.I)
INJECTED_PREFIXES = (
    "<environment_context>",
    "<recommended_plugins>",
    "<app-context>",
    "<skill>",
    "<send_user_message_question",
    "<turn_aborted>",
    "<user_action>",
    "# AGENTS.md instructions",
    "<permissions instructions>",
    "<collaboration_mode",
)


# ----------------------------------------------------------------------------
# Locating
# ----------------------------------------------------------------------------

def codex_homes() -> list[Path]:
    homes: list[Path] = []
    env = os.environ.get("CODEX_HOME")
    if env:
        homes.append(Path(env).expanduser())
    home = Path.home()
    for p in sorted(home.glob(".codex*")):
        if p.is_dir() and (p / "sessions").exists() and p not in homes:
            homes.append(p)
    return homes


def parse_ref(ref: str) -> str:
    """Return a uuid (or prefix) from a codex:// url, bare id, or rollout path."""
    if os.path.exists(ref):
        m = UUID_RE.search(os.path.basename(ref))
        return m.group(0).lower() if m else ref
    ref = ref.strip()
    ref = re.sub(r"^codex://threads/", "", ref)
    ref = ref.split("?")[0].split("#")[0].strip("/")
    return ref.lower()


def uuid7_time(thread_id: str) -> dt.datetime | None:
    hexpart = thread_id.replace("-", "")[:12]
    if len(hexpart) < 12:
        return None
    try:
        ms = int(hexpart, 16)
        return dt.datetime.fromtimestamp(ms / 1000, dt.timezone.utc)
    except ValueError:
        return None


def locate(ref: str) -> list[dict]:
    """Return candidate rollout files across all CODEX_HOMEs (most specific first)."""
    if os.path.exists(ref) and ref.endswith(".jsonl"):
        return [{"path": os.path.abspath(ref), "home": None, "via": "path"}]
    tid = parse_ref(ref)
    hits: dict[str, dict] = {}

    for home in codex_homes():
        # 1) sqlite index (authoritative rollout_path + title)
        for db in sorted(home.glob("state_*.sqlite")):
            try:
                con = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
                rows = con.execute(
                    "select id, rollout_path, title, cwd, model, archived from threads where id like ?",
                    (tid + "%",),
                ).fetchall()
                con.close()
            except sqlite3.Error:
                continue
            for r in rows:
                hits.setdefault(r[1], {"path": r[1], "home": str(home), "via": f"sqlite:{db.name}",
                                       "id": r[0], "title": (r[2] or "")[:80], "cwd": r[3],
                                       "model": r[4], "archived": r[5]})
        # 2) filesystem glob (fast path: UUIDv7 date narrows the directory)
        pats = []
        t = uuid7_time(tid) if len(tid) >= 12 else None
        for sub in ("sessions", "archived_sessions"):
            if t:
                for d in (t, t + dt.timedelta(hours=8)):  # utc vs local-day dir
                    pats.append(str(home / sub / d.strftime("%Y/%m/%d") / f"rollout-*-{tid}*.jsonl"))
            pats.append(str(home / sub / f"**/rollout-*-{tid}*.jsonl"))
            pats.append(str(home / sub / f"rollout-*-{tid}*.jsonl"))
        for pat in pats:
            for p in glob.glob(pat, recursive=True):
                hits.setdefault(p, {"path": p, "home": str(home), "via": "glob"})
    out = [h for h in hits.values() if os.path.exists(h["path"])]
    out.sort(key=lambda h: (h["via"] == "glob", h["path"]))
    return out


def resolve(ref: str) -> str:
    cands = locate(ref)
    if not cands:
        sys.exit(f"thread not found in {[str(h) for h in codex_homes()]}: {ref}")
    if len(cands) > 1 and len({c["path"] for c in cands}) > 1:
        print("multiple candidates, using first:", file=sys.stderr)
        for c in cands:
            print(f"  {c['path']}  ({c['via']})", file=sys.stderr)
    return cands[0]["path"]


# ----------------------------------------------------------------------------
# Parsing
# ----------------------------------------------------------------------------

def iter_records(path: str):
    with open(path, "r", encoding="utf-8", errors="replace") as fh:
        for i, line in enumerate(fh):
            line = line.strip()
            if not line:
                continue
            try:
                yield i, json.loads(line)
            except json.JSONDecodeError:
                continue


def text_of(content) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for c in content:
            if isinstance(c, dict):
                if c.get("type") in ("input_text", "output_text", "text") and c.get("text") is not None:
                    parts.append(c["text"])
                elif c.get("type") in ("input_image", "image"):
                    parts.append("[image]")
        return "\n".join(parts)
    return ""


AMBIENT_BLOCK_RE = re.compile(
    r"<(in-app-browser-context|environment_context|app-context|recommended_plugins|permissions instructions|"
    r"collaboration_mode[^>]*|turn_aborted|user_action)\b[^>]*>.*?</\1>\s*",
    re.S,
)
REQUEST_HEADER_RE = re.compile(r"^\s*##\s*My request:\s*", re.I)


def clean_user_text(text: str) -> str:
    """Strip ambient blocks the app injects around the real user prompt."""
    t = AMBIENT_BLOCK_RE.sub("", text)
    t = REQUEST_HEADER_RE.sub("", t)
    return t.strip()


def is_injected(text: str) -> bool:
    s = text.lstrip()
    return not s or s.startswith(INJECTED_PREFIXES)


def ts_local(ts: str | None) -> str:
    if not ts:
        return ""
    try:
        d = dt.datetime.fromisoformat(ts.replace("Z", "+00:00")).astimezone()
        return d.strftime("%Y-%m-%d %H:%M")
    except ValueError:
        return ts[:16]


class Thread:
    """Streaming projection of a rollout into turns."""

    def __init__(self, path: str, keep_tool_text: bool = False):
        self.path = path
        self.meta: dict = {}
        self.turns: list[dict] = []
        self._by_id: dict[str, dict] = {}
        self.counts: Counter = Counter()
        self.tool_names: Counter = Counter()
        self.compactions = 0
        self.last_ts = None
        self.models: Counter = Counter()
        self.total_tokens = 0
        self.keep_tool_text = keep_tool_text
        self._parse()

    def _turn(self, turn_id: str | None, ts: str | None) -> dict:
        key = turn_id or "unknown"
        t = self._by_id.get(key)
        if t is None:
            t = {"turn_id": key, "started": ts, "ended": ts, "user": [], "final": [],
                 "commentary": [], "tool_calls": 0, "tools": Counter(), "cmds": [],
                 "tool_out": [], "aborted": False, "files": 0, "web": 0, "line": None}
            self._by_id[key] = t
            self.turns.append(t)
        if ts:
            t["ended"] = ts
        return t

    def _parse(self):
        cur_turn = None
        for lineno, o in iter_records(self.path):
            t = o.get("type")
            p = o.get("payload") or {}
            ts = o.get("timestamp")
            self.last_ts = ts or self.last_ts
            self.counts[t] += 1
            if t == "session_meta":
                self.meta = {k: v for k, v in p.items() if k != "base_instructions"}
                self.meta["base_instructions_head"] = ((p.get("base_instructions") or {}).get("text") or "")[:200]
                continue
            if t == "compacted":
                self.compactions += 1
                continue
            if t == "turn_context":
                cur_turn = p.get("turn_id") or cur_turn
                tt = self._turn(cur_turn, ts)
                tt["line"] = tt["line"] or lineno
                tt["model"] = p.get("model")
                tt["cwd"] = p.get("cwd")
                if p.get("model"):
                    self.models[p["model"]] += 1
                continue
            if t == "token_usage_record":
                u = (p.get("usage") or {})
                self.total_tokens += u.get("total_tokens") or 0
                continue
            if t == "event_msg":
                et = p.get("type")
                tid = p.get("turn_id")
                if et == "task_started":
                    cur_turn = tid
                    tt = self._turn(tid, ts)
                    tt["line"] = tt["line"] or lineno
                elif et == "item_completed":
                    item = p.get("item") or {}
                    tt = self._turn(tid or cur_turn, ts)
                    it = item.get("type")
                    if it == "UserMessage":
                        txt = clean_user_text(text_of(item.get("content")))
                        if txt and not is_injected(txt) and txt not in tt["user"]:
                            tt["user"].append(txt)
                    elif it == "FileChange":
                        tt["files"] += 1
                    elif it == "WebSearch":
                        tt["web"] += 1
                elif et == "task_complete":
                    tt = self._turn(tid, ts)
                    lam = p.get("last_agent_message")
                    if lam and lam not in tt["final"]:
                        tt["final"].append(lam)
                elif et == "turn_aborted":
                    self._turn(tid, ts)["aborted"] = True
                continue
            if t == "response_item":
                pt = p.get("type")
                meta = p.get("internal_chat_message_metadata_passthrough") or {}
                tid = meta.get("turn_id") or cur_turn
                tt = self._turn(tid, ts)
                if pt == "message":
                    role = p.get("role")
                    txt = text_of(p.get("content"))
                    if role == "assistant":
                        if p.get("phase") == "final_answer":
                            if txt not in tt["final"]:
                                tt["final"].append(txt)
                        else:
                            tt["commentary"].append(txt)
                    elif role == "user":
                        # fallback if item_completed events are missing (older CLIs)
                        txt = clean_user_text(txt)
                        if txt and not is_injected(txt) and txt not in tt["user"]:
                            tt["user"].append(txt)
                elif pt in ("custom_tool_call", "function_call"):
                    name = p.get("name") or "?"
                    tt["tool_calls"] += 1
                    tt["tools"][name] += 1
                    self.tool_names[name] += 1
                    arg = p.get("input") if pt == "custom_tool_call" else p.get("arguments")
                    if isinstance(arg, str):
                        tt["cmds"].append((name, arg))
                elif pt in ("custom_tool_call_output", "function_call_output") and self.keep_tool_text:
                    tt["tool_out"].append(text_of(p.get("output")) if not isinstance(p.get("output"), str) else p["output"])

    # -- helpers ---------------------------------------------------------
    @property
    def thread_id(self) -> str:
        return self.meta.get("id") or self.meta.get("session_id") or parse_ref(self.path)

    def real_turns(self) -> list[dict]:
        return [t for t in self.turns if t["user"] or t["final"] or t["tool_calls"]]


def one_line(s: str, n: int) -> str:
    s = " ".join(s.split())
    return s if len(s) <= n else s[: n - 1] + "…"


# ----------------------------------------------------------------------------
# Commands
# ----------------------------------------------------------------------------

def cmd_locate(a):
    cands = locate(a.ref)
    if not cands:
        t = uuid7_time(parse_ref(a.ref))
        hint = f" (uuid7 time ≈ {t.astimezone().strftime('%Y-%m-%d %H:%M %Z')})" if t else ""
        sys.exit(f"not found{hint}; searched homes: {[str(h) for h in codex_homes()]}")
    for c in cands:
        size = os.path.getsize(c["path"]) / 1e6
        print(f"{c['path']}\n  home={c['home']} via={c['via']} size={size:.1f}MB"
              + (f" title={c.get('title')!r}" if c.get("title") else "")
              + (f" model={c.get('model')}" if c.get("model") else ""))


def cmd_summary(a):
    path = resolve(a.ref)
    th = Thread(path)
    m = th.meta
    turns = th.real_turns()
    print(f"thread_id : {th.thread_id}")
    print(f"file      : {path}  ({os.path.getsize(path)/1e6:.1f} MB, {sum(th.counts.values())} records)")
    print(f"cwd       : {m.get('cwd')}")
    print(f"origin    : {m.get('originator')} / source={m.get('source')} / cli={m.get('cli_version')} / provider={m.get('model_provider')}")
    print(f"models    : {dict(th.models.most_common(3))}")
    print(f"created   : {ts_local(m.get('timestamp'))}    last: {ts_local(th.last_ts)}")
    print(f"turns     : {len(turns)} (aborted {sum(t['aborted'] for t in turns)})   compactions: {th.compactions}   tokens≈{th.total_tokens:,}")
    print(f"tool calls: {sum(th.tool_names.values())}  {dict(th.tool_names.most_common(6))}")
    print(f"records   : {dict(th.counts)}")
    if turns:
        print("\nfirst prompt:", one_line(turns[0]["user"][0] if turns[0]["user"] else "", 300))
        last = next((t for t in reversed(turns) if t["user"]), None)
        if last:
            print("last prompt :", one_line(last["user"][-1], 300))
    print(f"\nnext: turns {th.thread_id}   |   messages {th.thread_id} --since YYYY-MM-DD   |   search {th.thread_id} '<regex>'")


def _filter_turns(th: Thread, a) -> list[dict]:
    turns = th.real_turns()
    if getattr(a, "since", None):
        turns = [t for t in turns if (t["started"] or "")[:10] >= a.since]
    if getattr(a, "until", None):
        turns = [t for t in turns if (t["started"] or "")[:10] <= a.until]
    if getattr(a, "last", None):
        turns = turns[-a.last:]
    if getattr(a, "turn", None):
        sel = set()
        for part in a.turn.split(","):
            if "-" in part:
                lo, hi = part.split("-")
                sel.update(range(int(lo), int(hi) + 1))
            else:
                sel.add(int(part))
        turns = [t for i, t in enumerate(th.real_turns(), 1) if i in sel]
    return turns


def cmd_turns(a):
    th = Thread(resolve(a.ref))
    all_turns = th.real_turns()
    idx = {id(t): i for i, t in enumerate(all_turns, 1)}
    for t in _filter_turns(th, a):
        u = one_line(t["user"][0], a.width) if t["user"] else "(no user prompt)"
        f = one_line(t["final"][-1], a.width) if t["final"] else ("(aborted)" if t["aborted"] else "(no final)")
        flags = f"tools={t['tool_calls']}" + (f" files={t['files']}" if t["files"] else "") + (f" web={t['web']}" if t["web"] else "")
        print(f"#{idx[id(t)]:<4} {ts_local(t['started'])}  [{flags}]")
        print(f"      U: {u}")
        print(f"      A: {f}")


def cmd_messages(a):
    th = Thread(resolve(a.ref))
    all_turns = th.real_turns()
    idx = {id(t): i for i, t in enumerate(all_turns, 1)}
    lim = None if a.full else a.width
    for t in _filter_turns(th, a):
        print(f"\n===== turn #{idx[id(t)]}  {ts_local(t['started'])} → {ts_local(t['ended'])}  tools={t['tool_calls']} =====")
        if a.role in ("user", "all"):
            for u in t["user"]:
                print("\n--- USER ---")
                print(u if lim is None else one_line(u, lim))
        if a.role in ("assistant", "all"):
            if a.commentary:
                for c in t["commentary"]:
                    print("\n--- ASSISTANT (commentary) ---")
                    print(c if lim is None else one_line(c, lim))
            for f in t["final"]:
                print("\n--- ASSISTANT (final) ---")
                print(f if lim is None else one_line(f, lim))
            if not t["final"] and t["aborted"]:
                print("\n--- ASSISTANT: turn aborted ---")


def cmd_search(a):
    th = Thread(resolve(a.ref), keep_tool_text=a.tools)
    rx = re.compile(a.pattern, re.I)
    all_turns = th.real_turns()
    n = 0
    for i, t in enumerate(all_turns, 1):
        buckets = [("U", t["user"]), ("A", t["final"]), ("A~", t["commentary"])]
        if a.tools:
            buckets.append(("T>", [f"{name}: {arg}" for name, arg in t["cmds"]]))
            buckets.append(("T<", t["tool_out"]))
        for tag, texts in buckets:
            for txt in texts:
                for m in rx.finditer(txt):
                    s = max(0, m.start() - a.context)
                    e = min(len(txt), m.end() + a.context)
                    print(f"#{i:<4} {ts_local(t['started'])} {tag}: …{one_line(txt[s:e], 2 * a.context + 60)}…")
                    n += 1
                    if n >= a.max:
                        print(f"(stopped at --max {a.max})")
                        return
    print(f"{n} matches")


def cmd_tools(a):
    th = Thread(resolve(a.ref))
    print("tool usage:", dict(th.tool_names.most_common()))
    all_turns = th.real_turns()
    idx = {id(t): i for i, t in enumerate(all_turns, 1)}
    if a.commands:
        for t in _filter_turns(th, a):
            for name, arg in t["cmds"]:
                print(f"#{idx[id(t)]:<4} {ts_local(t['started'])} {name}: {one_line(arg, a.width)}")
    else:
        busiest = sorted(all_turns, key=lambda t: -t["tool_calls"])[:10]
        print("\nbusiest turns:")
        for t in busiest:
            print(f"  #{idx[id(t)]:<4} {ts_local(t['started'])} tools={t['tool_calls']}  U: {one_line(t['user'][0] if t['user'] else '', 100)}")


def cmd_export(a):
    path = resolve(a.ref)
    th = Thread(path)
    out = a.out
    if not out:
        base = Path(a.repo or os.getcwd()) / ".local" / "codex-thread-dumps"
        base.mkdir(parents=True, exist_ok=True)
        out = str(base / f"{th.thread_id}.md")
    turns = _filter_turns(th, a)
    all_turns = th.real_turns()
    idx = {id(t): i for i, t in enumerate(all_turns, 1)}
    with open(out, "w", encoding="utf-8") as fh:
        m = th.meta
        fh.write(f"# Codex thread {th.thread_id}\n\n")
        fh.write(f"- rollout: `{path}`\n- cwd: `{m.get('cwd')}`\n- created: {ts_local(m.get('timestamp'))}  last: {ts_local(th.last_ts)}\n")
        fh.write(f"- turns: {len(all_turns)}  compactions: {th.compactions}  tool calls: {sum(th.tool_names.values())}\n\n")
        for t in turns:
            fh.write(f"\n## turn #{idx[id(t)]} — {ts_local(t['started'])} (tools={t['tool_calls']})\n\n")
            for u in t["user"]:
                fh.write("**User**\n\n" + u.strip() + "\n\n")
            if a.commentary:
                for c in t["commentary"]:
                    fh.write("*Assistant (commentary)*\n\n" + c.strip() + "\n\n")
            for f in t["final"]:
                fh.write("**Assistant**\n\n" + f.strip() + "\n\n")
            if t["aborted"] and not t["final"]:
                fh.write("*(turn aborted)*\n\n")
    print(f"wrote {out}  ({os.path.getsize(out)/1e3:.0f} KB, {len(turns)} turns)")


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    def common(sp, rng=True):
        sp.add_argument("ref", help="codex://threads/<uuid> | uuid | uuid prefix | rollout path")
        if rng:
            sp.add_argument("--since", help="YYYY-MM-DD (UTC date of turn start)")
            sp.add_argument("--until", help="YYYY-MM-DD")
            sp.add_argument("--last", type=int, help="only the last N turns")
            sp.add_argument("--turn", help="turn numbers, e.g. 3,7-9 (numbers from `turns`)")

    common(sub.add_parser("locate", help="find rollout file(s)"), rng=False)
    common(sub.add_parser("summary", help="metadata and counts"), rng=False)

    sp = sub.add_parser("turns", help="one entry per turn")
    common(sp); sp.add_argument("--width", type=int, default=160)

    sp = sub.add_parser("messages", help="readable prompts and answers")
    common(sp)
    sp.add_argument("--role", choices=["user", "assistant", "all"], default="all")
    sp.add_argument("--full", action="store_true", help="do not truncate")
    sp.add_argument("--width", type=int, default=800)
    sp.add_argument("--commentary", action="store_true", help="include assistant progress notes")

    sp = sub.add_parser("search", help="regex search")
    common(sp, rng=False)
    sp.add_argument("pattern")
    sp.add_argument("--tools", action="store_true", help="also search tool inputs/outputs (slower, more memory)")
    sp.add_argument("--context", type=int, default=120)
    sp.add_argument("--max", type=int, default=200)

    sp = sub.add_parser("tools", help="tool usage")
    common(sp)
    sp.add_argument("--commands", action="store_true", help="list exec/tool inputs per turn")
    sp.add_argument("--width", type=int, default=200)

    sp = sub.add_parser("export", help="write Markdown transcript")
    common(sp)
    sp.add_argument("--out", help="output path (default <repo>/.local/codex-thread-dumps/<id>.md)")
    sp.add_argument("--repo", help="repo root used for the default output dir")
    sp.add_argument("--commentary", action="store_true")

    a = ap.parse_args(argv)
    {"locate": cmd_locate, "summary": cmd_summary, "turns": cmd_turns, "messages": cmd_messages,
     "search": cmd_search, "tools": cmd_tools, "export": cmd_export}[a.cmd](a)


if __name__ == "__main__":
    main()
