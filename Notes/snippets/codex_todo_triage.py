#!/usr/bin/env python3
"""
Generate a Codex-oriented TODO triage index from .trae/todos/todos.json.

By default this is a one-way view. With --apply-codex-triage, it annotates
todos.json with non-destructive `codex_triage` metadata, but still does not
change the legacy `status` field. The goal is to help Codex decide what still
matters, what is user-blocked, and which old Trae/OpenClaw tasks should be
merged into the newer Codex workflow.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
TODOS_JSON = REPO_ROOT / ".trae" / "todos" / "todos.json"
DEFAULT_OUTPUT = REPO_ROOT / ".local" / "CODEX_TODO_TRIAGE_INDEX.md"
LEARNING_MATERIALS = REPO_ROOT / ".local" / "LEARNING_MATERIAL_CANDIDATES.md"


USER_BLOCKED_KEYWORDS = [
    "公网",
    "配置gh",
    "OpenClaw Web Manager",
    "公司内部",
    "ECS",
    "SSH",
    "询问",
    "oncall",
    "创作文件夹",
]

FLOW_EVOLUTION_KEYWORDS = [
    "OrbitOS",
    "任务系统",
    "Plan Mode",
    "批量 Review",
    "自然语言",
    "语音",
    "voice",
    "LLM 优先",
    "Todos Web Manager",
    "Plan Generator",
    "Hybrid Executor",
    "同步脚本",
    "memos",
]

MATERIAL_OR_TOOL_KEYWORDS = [
    "PDF",
    "YouTube",
    "公众号",
    "千帆",
    "skills",
    "Numerical Precision",
    "阅读",
    "下载",
]


def load_todos(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def dump_todos(path: Path, data: dict[str, Any]) -> None:
    path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def text_of(todo: dict[str, Any]) -> str:
    parts: list[str] = []
    for key in ("title", "progress", "background"):
        value = todo.get(key)
        if isinstance(value, str):
            parts.append(value)
    for key in ("definition_of_done", "user_requirements", "dependencies", "links"):
        value = todo.get(key)
        if isinstance(value, list):
            parts.extend(str(x) for x in value)
    return "\n".join(parts)


def has_any(text: str, keywords: list[str]) -> bool:
    return any(k.lower() in text.lower() for k in keywords)


def classify(todo: dict[str, Any]) -> tuple[str, str, str]:
    """Return category, judgment, recommended action."""
    status = todo.get("status", "")
    assignee = todo.get("assignee", "")
    text = text_of(todo)

    if status == "completed":
        if str(todo.get("id", "")).startswith("todo-202605"):
            return (
                "E. 已完成但要吸收经验",
                "近期完成，应保留经验并观察是否需要后续自动化。",
                "复盘经验；不要回到旧执行链路。",
            )
        return (
            "F. 已完成历史任务",
            "已完成，默认不进入 Codex 推进队列。",
            "只在相关能力回归或需要复盘时查看。",
        )

    if assignee == "user" or has_any(text, USER_BLOCKED_KEYWORDS):
        return (
            "C. 用户手动 / 内部环境阻塞",
            "需要用户账号、公司内部环境、机器权限或主观判断。",
            "保留为 user-blocked；用户重新激活后再拆 Codex 可执行部分。",
        )

    if has_any(text, FLOW_EVOLUTION_KEYWORDS):
        return (
            "B. 流程演进类：合并成 Codex TODO System v2",
            "本质是旧 Trae/OpenClaw 执行链路建设，不应逐条修补。",
            "合并到 Codex TODO System v2；默认按 3-5 个低风险小切口做批推进。",
        )

    if has_any(text, MATERIAL_OR_TOOL_KEYWORDS):
        return (
            "D. 可归档 / 可取消候选",
            "更适合转入素材管线或按需重启，不应长期挂在 TODO。",
            "需要时用 `素材：` 重新进入材料流；否则归档或取消。",
        )

    if status in {"pending", "--progress", "in-progress"}:
        return (
            "A. Codex 可独立推进",
            "Codex 可以推进，但应先重写成更小、更贴近当前目标的任务。",
            "优先组成同目标小批次，写出可验证产物后再回写 TODO 状态。",
        )

    return (
        "Z. 状态异常 / 需人工复核",
        f"未知状态 `{status}`。",
        "先修正状态，再决定是否推进。",
    )


def triage_metadata(todo: dict[str, Any], today: str) -> dict[str, str]:
    category, judgment, action = classify(todo)
    if category == "A. Codex 可独立推进":
        code = "codex_candidate"
        recommended_status = "rewrite-before-execute"
        merge_target = ""
    elif category == "B. 流程演进类：合并成 Codex TODO System v2":
        code = "merged_into_codex_todo_system_v2"
        recommended_status = "merged"
        merge_target = "Codex TODO System v2"
    elif category == "C. 用户手动 / 内部环境阻塞":
        code = "user_or_environment_blocked"
        recommended_status = "user-blocked"
        merge_target = ""
    elif category == "D. 可归档 / 可取消候选":
        code = "stale_or_material_flow"
        recommended_status = "archive-or-reinput-as-material"
        merge_target = "material pipeline or on-demand skill install"
    elif category == "E. 已完成但要吸收经验":
        code = "completed_recent_observe"
        recommended_status = "completed-observe"
        merge_target = ""
    elif category == "F. 已完成历史任务":
        code = "completed_historical"
        recommended_status = "completed"
        merge_target = ""
    else:
        code = "needs_manual_review"
        recommended_status = "review"
        merge_target = ""

    metadata = {
        "triaged_at": today,
        "category": code,
        "recommended_status": recommended_status,
        "judgment": judgment,
        "recommended_action": action,
    }
    if merge_target:
        metadata["merge_target"] = merge_target
    return metadata


def short_progress(todo: dict[str, Any], max_len: int = 90) -> str:
    progress = str(todo.get("progress", "")).replace("\n", " ").strip()
    if not progress:
        return ""
    return progress[:max_len] + ("..." if len(progress) > max_len else "")


def pending_feedback_todos(todos: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        t
        for t in todos
        if t.get("status") in {"pending", "in-progress", "--progress"}
        and t.get("feedback_required")
    ]


def active_todos(todos: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [t for t in todos if t.get("status") in {"pending", "in-progress", "--progress"}]


def empty_queue_lines() -> list[str]:
    return [
        "当前没有 pending / in-progress / user-blocked TODO。",
        "",
        "空队列时，`推进TODO` 不硬编旧任务，按这个顺序找下一批：",
        "",
        "1. 复盘最近 3-5 条 completed TODO，沉淀流程、脚本或 AGENTS.md 规则。",
        "2. 查看 `.local/LEARNING_MATERIAL_CANDIDATES.md` 的当前建议阅读顺序，把已读/待读材料转成可执行小任务。",
        "3. 查看 agent-harness 主控是否需要转发 steering、schema、benchmark 或实验设计。",
        "4. 只在发现明确小切口时新增 TODO；否则明确回复“队列为空，下一步应由材料/项目状态触发”。",
    ]


def current_reading_queue(limit: int = 5) -> list[dict[str, str]]:
    """Extract the top material queue from the local candidates file.

    The material file is intentionally human-edited Markdown, so keep this
    parser conservative: only read the numbered rows in the explicit current
    reading-order section and ignore the long item bodies below.
    """
    if not LEARNING_MATERIALS.exists():
        return []

    lines = LEARNING_MATERIALS.read_text(encoding="utf-8").splitlines()
    start = None
    for index, line in enumerate(lines):
        if line.startswith("## 当前建议阅读顺序"):
            start = index + 1
            break
    if start is None:
        return []

    items: list[dict[str, str]] = []
    current: dict[str, str] | None = None
    for raw in lines[start:]:
        if raw.startswith("## ") and not raw.startswith("## 当前建议阅读顺序"):
            break
        stripped = raw.strip()
        if not stripped:
            continue
        if stripped[0:1].isdigit() and ". `" in stripped:
            if current:
                items.append(current)
                if len(items) >= limit:
                    return items
            _, rest = stripped.split(". ", 1)
            title = rest
            material_id = ""
            if rest.startswith("`") and "`" in rest[1:]:
                material_id = rest.split("`", 2)[1]
                title = rest.split("`", 2)[2].strip()
            current = {"id": material_id, "title": title, "why": "", "output": ""}
            continue
        if current and stripped.startswith("- 为什么今天读："):
            current["why"] = stripped.removeprefix("- 为什么今天读：").strip()
        elif current and stripped.startswith("- 产出："):
            current["output"] = stripped.removeprefix("- 产出：").strip()

    if current and len(items) < limit:
        items.append(current)
    return items[:limit]


def priority_rank(value: Any) -> int:
    text = str(value or "")
    if text.startswith("P") and text[1:].isdigit():
        return int(text[1:])
    if text == "high":
        return 1
    return 99


DEFAULT_ACTION_RANK = {
    "todo-20260225-016": 10,
    "todo-20260223-034039": 20,
    "todo-20260225-001": 21,
    "todo-20260219-004": 40,
    "todo-20260220-010": 41,
    "todo-20260219-027": 60,
}


def action_rank(todo: dict[str, Any]) -> int:
    value = todo.get("user_action_rank")
    if isinstance(value, int):
        return value
    if isinstance(value, str) and value.isdigit():
        return int(value)
    return DEFAULT_ACTION_RANK.get(str(todo.get("id", "")), 999)


def sorted_user_action_todos(data: dict[str, Any]) -> list[dict[str, Any]]:
    return sorted(
        pending_feedback_todos(data.get("todos", [])),
        key=lambda t: (
            action_rank(t),
            priority_rank(t.get("priority")),
            str(t.get("created_at", "")),
        ),
    )


def render_user_actions(data: dict[str, Any]) -> str:
    todos = sorted_user_action_todos(data)
    lines = ["# TODO 用户动作队列", ""]
    if not todos:
        lines.append("当前没有 pending 且 feedback_required=true 的任务。")
        active = active_todos(data.get("todos", []))
        if active:
            lines.append("")
            lines.append("但仍存在 Codex 可推进的 active TODO：")
            for todo in active[:5]:
                lines.append(f"- `{todo.get('id')}` [{todo.get('status')}] {todo.get('title')}")
        else:
            lines.append("")
            lines.extend(empty_queue_lines())
        return "\n".join(lines)

    lines.append("这些任务已经推进到 Codex 可自动完成部分的边界，下一步需要用户动作：")
    lines.append("")
    for index, todo in enumerate(todos, 1):
        lines.append(f"{index}. `{todo.get('id')}` [rank={action_rank(todo)} / {todo.get('priority')}] {todo.get('title')}")
        next_action = todo.get("user_next_action")
        if isinstance(next_action, str) and next_action.strip():
            lines.append(f"   下一步：{next_action.strip()}")
        else:
            lines.append("   下一步：补充 `user_next_action`。")
        links = todo.get("links")
        if isinstance(links, list) and links:
            lines.append(f"   参考：{links[0]}")
        lines.append("")
    return "\n".join(lines).rstrip()


def render_next_action(data: dict[str, Any]) -> str:
    todos = sorted_user_action_todos(data)
    lines = ["# TODO 下一步", ""]
    if not todos:
        lines.append("当前没有 pending 且 feedback_required=true 的任务。")
        active = active_todos(data.get("todos", []))
        if active:
            todo = active[0]
            lines.append("")
            lines.append(f"当前 Codex 可继续推进：`{todo.get('id')}` [{todo.get('status')}] {todo.get('title')}")
        else:
            lines.append("")
            lines.extend(empty_queue_lines())
        return "\n".join(lines)

    todo = todos[0]
    lines.append(f"`{todo.get('id')}` [rank={action_rank(todo)} / {todo.get('priority')}] {todo.get('title')}")
    next_action = todo.get("user_next_action")
    if isinstance(next_action, str) and next_action.strip():
        lines.append("")
        lines.append(f"下一步：{next_action.strip()}")

    check_by_id = {todo_id: (status, message) for todo_id, status, message in blocker_checks(data)}
    status_message = check_by_id.get(str(todo.get("id")))
    if status_message:
        status, message = status_message
        lines.append("")
        lines.append(f"当前检查：[{status}] {message}")

    links = todo.get("links")
    if isinstance(links, list) and links:
        lines.append("")
        lines.append(f"参考：{links[0]}")
    return "\n".join(lines)


def render_batch_plan(data: dict[str, Any]) -> str:
    lines = ["# TODO 批推进建议", ""]
    active = sorted(
        active_todos(data.get("todos", [])),
        key=lambda t: (
            priority_rank(t.get("priority")),
            str(t.get("created_at", "")),
        ),
    )
    if active:
        lines.append("当前存在 active TODO，建议先围绕它形成 batch：")
        lines.append("")
        for todo in active[:5]:
            lines.append(f"- `{todo.get('id')}` [{todo.get('status')} / {todo.get('priority')}] {todo.get('title')}")
        lines.append("")
        lines.append("批推进检查：")
        lines.append("")
        lines.append("1. 主任务是否可拆成 3-5 个低风险小切口。")
        lines.append("2. 是否需要同步更新 AGENTS.md / `.local` 指令 / v2 文档 / triage 脚本。")
        lines.append("3. 是否有值得发给 agent-harness 主控的转发稿。")
        lines.append("4. 完成后是否能刷新 `.local/CODEX_TODO_TRIAGE_INDEX.md` 并回写 progress。")
        return "\n".join(lines)

    lines.extend(empty_queue_lines())
    lines.append("")
    queue = current_reading_queue(limit=5)
    if queue:
        lines.append("当前材料队列可转成 TODO 的前几项：")
        lines.append("")
        for index, item in enumerate(queue, 1):
            material_id = item.get("id") or "material"
            title = item.get("title") or ""
            lines.append(f"{index}. `{material_id}` {title}")
            if item.get("why"):
                lines.append(f"   - 为什么现在：{item['why']}")
            if item.get("output"):
                lines.append(f"   - 可验证产物：{item['output']}")
        lines.append("")
    lines.append("推荐空队列 batch 模板：")
    lines.append("")
    lines.append("- 流程沉淀 batch：从最近 completed 中抽 1 条经验，更新 AGENTS.md / v2 文档 / 脚本输出。")
    lines.append("- 材料转行动 batch：从当前阅读顺序选 1 篇，生成精读导读、读后模板、agent-harness steering 占位。")
    lines.append("- 项目同步 batch：检查 agent-harness / CS-Notes 状态，产出 1 段转发稿或 1 个 schema/TODO 草案。")
    return "\n".join(lines)


def run_check(command: list[str], timeout: int = 8) -> tuple[bool, str]:
    try:
        proc = subprocess.run(
            command,
            cwd=REPO_ROOT,
            text=True,
            capture_output=True,
            timeout=timeout,
            check=False,
        )
    except FileNotFoundError:
        return False, f"command not found: {command[0]}"
    except subprocess.TimeoutExpired:
        return False, f"timeout after {timeout}s: {' '.join(command)}"

    output = "\n".join(x.strip() for x in (proc.stdout, proc.stderr) if x.strip())
    return proc.returncode == 0, output.splitlines()[0] if output else f"exit={proc.returncode}"


def find_executable(name: str) -> str | None:
    path = shutil.which(name)
    if path:
        return path
    for candidate in (
        Path("/opt/homebrew/bin") / name,
        Path("/usr/local/bin") / name,
        Path.home() / ".local" / "bin" / name,
    ):
        if candidate.exists() and os.access(candidate, os.X_OK):
            return str(candidate)
    return None


def blocker_checks(data: dict[str, Any]) -> list[tuple[str, str, str]]:
    active_statuses = {"pending", "in-progress", "--progress"}
    todos_by_id = {
        todo.get("id"): todo
        for todo in data.get("todos", [])
        if todo.get("status") in active_statuses
    }
    checks: list[tuple[str, str, str]] = []

    if "todo-20260225-016" in todos_by_id:
        gh_path = find_executable("gh")
        if not gh_path:
            checks.append(("todo-20260225-016", "blocked", "`gh` 未安装。"))
        else:
            ok, message = run_check([gh_path, "auth", "status"])
            if ok:
                search_script = REPO_ROOT / "Notes" / "snippets" / "github-search.sh"
                if search_script.exists() and search_script.stat().st_mode & 0o111:
                    checks.append(("todo-20260225-016", "maybe-unblocked", "`gh auth status` 已通过；可运行 github-search 验证 JSON 输出。"))
                else:
                    checks.append(("todo-20260225-016", "blocked", "`gh` 已登录，但 `Notes/snippets/github-search.sh` 不存在或不可执行。"))
            else:
                checks.append(("todo-20260225-016", "blocked", f"`gh` 已安装但未登录：{message}"))

    if "todo-20260223-034039" in todos_by_id or "todo-20260225-001" in todos_by_id:
        if shutil.which("trae"):
            checks.append(("todo-20260223-034039", "local-baseline-ok", "`trae` CLI 存在；仍需内部 owner 确认非交互/trace/proactive 能力。"))
            checks.append(("todo-20260225-001", "local-baseline-ok", "`trae chat --mode agent` 入口已知；仍需内部 owner 确认 daemon/scheduler/resume。"))
        else:
            checks.append(("todo-20260223-034039", "blocked", "本机未找到 `trae` CLI。"))
            checks.append(("todo-20260225-001", "blocked", "本机未找到 `trae` CLI。"))

    if "todo-20260220-010" in todos_by_id:
        if shutil.which("ssh"):
            checks.append(("todo-20260220-010", "needs-user-input", "`ssh` 可用；需要用户提供 host/user 与 `ssh -vvv` 脱敏报错。"))
        else:
            checks.append(("todo-20260220-010", "blocked", "本机未找到 `ssh`。"))

    if "todo-20260219-004" in todos_by_id:
        checks.append(("todo-20260219-004", "needs-user-input", "需要当前 OpenClaw Web Manager URL、报错或 ECS 信息；本地无法复现火山环境。"))

    if "todo-20260219-027" in todos_by_id:
        checks.append(("todo-20260219-027", "needs-user-decision", "涉及 `公司项目/` 私密内容，需要用户明确授权范围或改为非敏感提纲。"))

    return checks


def render_blocker_checks(data: dict[str, Any]) -> str:
    checks = blocker_checks(data)
    lines = ["# TODO 阻塞检查", ""]
    if not checks:
        lines.append("当前没有可自动检查的阻塞项。")
        return "\n".join(lines)

    for todo_id, status, message in checks:
        lines.append(f"- `{todo_id}` [{status}] {message}")
    return "\n".join(lines)


def render(data: dict[str, Any]) -> str:
    now = datetime.now().strftime("%Y-%m-%d")
    todos = data.get("todos", [])
    status_counter = Counter(t.get("status", "") for t in todos)
    priority_counter = Counter(t.get("priority", "") for t in todos)
    assignee_counter = Counter(t.get("assignee", "") for t in todos)
    feedback_todos = pending_feedback_todos(todos)

    buckets: dict[str, list[tuple[dict[str, Any], str, str]]] = defaultdict(list)
    for todo in todos:
        category, judgment, action = classify(todo)
        if category == "F. 已完成历史任务":
            continue
        buckets[category].append((todo, judgment, action))

    lines: list[str] = []
    lines.append("# Codex TODO Triage Index")
    lines.append("")
    lines.append(f"更新时间：{now}")
    lines.append("")
    lines.append(
        "这个文件是 Codex 版 TODO 推进的轻量索引。它不替代 `.trae/todos/todos.json`，"
        "而是在迁移期给 Codex 一个更合适的执行视角：先判断任务是否仍然服务当前目标，"
        "再决定推进、合并、重写、交给用户或归档。"
    )
    lines.append("")

    lines.append("## 当前状态")
    lines.append("")
    lines.append(f"`.trae/todos/todos.json` 当前共有 {len(todos)} 条：")
    lines.append("")
    for key, count in status_counter.most_common():
        lines.append(f"- {key}：{count}")
    lines.append("")
    lines.append("补充统计：")
    lines.append("")
    lines.append(f"- priority：{dict(priority_counter)}")
    lines.append(f"- assignee：{dict(assignee_counter)}")
    lines.append(f"- pending feedback_required：{len(feedback_todos)}")
    lines.append("")
    if not active_todos(todos):
        lines.append("### 空队列协议")
        lines.append("")
        lines.extend(empty_queue_lines())
        lines.append("")
    lines.append("旧系统的主要问题：")
    lines.append("")
    lines.append("- `status` 不稳定：`--progress` 不是清晰状态，很多任务介于 in-progress / stale / abandoned 之间。")
    lines.append("- priority 过时：早期 P0/P1 不再等价于今天的职业主线优先级。")
    lines.append("- assignee 粗糙：`ai` / `user` 不足以表达 Codex 可独立推进、用户阻塞、内部环境阻塞、已被新流程取代。")
    lines.append("- 任务粒度混杂：feature、调研、系统设计、素材阅读和临时想法混在一起。")
    lines.append("- 缺少与当前主线的连接：Agent Harness、memory routing、材料库、AI 热点自动化、职业 deep dive 没有被统一纳入队列。")
    lines.append("")

    lines.append("## 新分类")
    lines.append("")
    category_order = [
        "A. Codex 可独立推进",
        "B. 流程演进类：合并成 Codex TODO System v2",
        "C. 用户手动 / 内部环境阻塞",
        "D. 可归档 / 可取消候选",
        "E. 已完成但要吸收经验",
        "Z. 状态异常 / 需人工复核",
    ]
    for category in category_order:
        items = buckets.get(category, [])
        if not items:
            continue
        lines.append(f"### {category}")
        lines.append("")
        for todo, judgment, action in items:
            lines.append(f"- `{todo.get('id')}`：{todo.get('title')}")
            lines.append(f"  - 状态：`{todo.get('status')}`；优先级：`{todo.get('priority')}`；负责人：`{todo.get('assignee')}`")
            codex_triage = todo.get("codex_triage")
            if isinstance(codex_triage, dict):
                recommended_status = codex_triage.get("recommended_status", "")
                category_code = codex_triage.get("category", "")
                lines.append(f"  - Codex triage：`{category_code}` / `{recommended_status}`")
            lines.append(f"  - 判断：{judgment}")
            lines.append(f"  - 推荐动作：{action}")
            progress = short_progress(todo)
            if progress:
                lines.append(f"  - 当前进度摘录：{progress}")
            user_next_action = todo.get("user_next_action")
            if isinstance(user_next_action, str) and user_next_action.strip():
                lines.append(f"  - 用户下一步：{user_next_action.strip()}")
            lines.append("")

    if feedback_todos:
        lines.append("## 用户动作队列")
        lines.append("")
        lines.append(
            "以下条目已经推进到 Codex 可自动完成部分的边界，下一步需要用户授权、内部信息、环境输入或明确取舍。"
        )
        lines.append("")
        for todo in feedback_todos:
            lines.append(f"- `{todo.get('id')}`：{todo.get('title')}")
            next_action = todo.get("user_next_action")
            if isinstance(next_action, str) and next_action.strip():
                lines.append(f"  - 下一步：{next_action.strip()}")
            else:
                lines.append("  - 下一步：补充 `user_next_action`，不要让阻塞任务只停留在 progress 文字里。")
            lines.append("")

    lines.append("## Codex TODO System v2 合并目标")
    lines.append("")
    lines.append(
        "> 以聊天指令为主入口，以 `.local` 私有判断 + `.trae/todos.json` 兼容数据源 "
        "+ Markdown triage index 为过渡形态，逐步替代旧 Web Manager / voice parser / plan generator 的碎片化链路。"
    )
    lines.append("")
    lines.append("优先实现顺序：")
    lines.append("")
    lines.append("1. `推进TODO` 协议稳定化。")
    lines.append("2. `Codex TODO Triage Index` 常规化：由本脚本生成，不靠手写。")
    lines.append("3. `推进TODO` 默认批推进：一次处理 3-5 个同目标、低风险、可 checkpoint 的小切口。")
    lines.append("4. completed / stale / user-blocked 的批量 review。")
    lines.append("5. 需要时再做同步脚本、可视化或 Web Manager 接入。")
    lines.append("")

    lines.append("## 下一步推荐")
    lines.append("")
    lines.append("1. **先做 TODO cleanup，不做大重构**：把 `--progress` 状态统一转成 stale / user-blocked / merged 的等价视图。")
    lines.append("2. **把旧流程类任务合并**：不逐条修 voice parser / plan generator / web manager，而是推进 `Codex TODO System v2` 的小批次。")
    lines.append("3. **短期不要继续修 Web Manager**：除非用户明确要前端，否则优先用 Markdown index + Codex 指令协议替代。")
    lines.append("4. **把新任务入口收敛到四类**：`素材：`、`整理笔记：`、`精读 / 读完`、`推进TODO`。")
    lines.append("")

    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate Codex TODO triage Markdown index.")
    parser.add_argument("--todos", type=Path, default=TODOS_JSON, help="Path to todos.json")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT, help="Output Markdown path")
    parser.add_argument("--stdout", action="store_true", help="Print to stdout instead of writing")
    parser.add_argument(
        "--user-actions",
        action="store_true",
        help="Print only pending user actions and do not write the triage index.",
    )
    parser.add_argument(
        "--next-action",
        action="store_true",
        help="Print the single highest-ranked pending user action with blocker status.",
    )
    parser.add_argument(
        "--batch-plan",
        action="store_true",
        help="Print the recommended batch for the next 推进TODO turn.",
    )
    parser.add_argument(
        "--check-blockers",
        action="store_true",
        help="Run lightweight local checks for known blocked TODOs.",
    )
    parser.add_argument(
        "--apply-codex-triage",
        action="store_true",
        help="Annotate todos.json with non-destructive codex_triage metadata.",
    )
    args = parser.parse_args()

    data = load_todos(args.todos)
    if args.apply_codex_triage:
        today = datetime.now().strftime("%Y-%m-%d")
        for todo in data.get("todos", []):
            category, _, _ = classify(todo)
            if category == "F. 已完成历史任务":
                todo.pop("codex_triage", None)
            else:
                todo["codex_triage"] = triage_metadata(todo, today)
        dump_todos(args.todos, data)

    if args.user_actions:
        print(render_user_actions(data))
        return

    if args.next_action:
        print(render_next_action(data))
        return

    if args.batch_plan:
        print(render_batch_plan(data))
        return

    if args.check_blockers:
        print(render_blocker_checks(data))
        return

    content = render(data)
    if args.stdout:
        print(content)
        return

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(content + "\n", encoding="utf-8")
    print(f"Generated {args.output}")


if __name__ == "__main__":
    main()
