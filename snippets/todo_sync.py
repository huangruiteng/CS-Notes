#!/usr/bin/env python3
"""
Todos 同步工具
双向同步：JSON ↔ Markdown
"""

import re
import json
from pathlib import Path
from datetime import datetime

# 配置路径
REPO_ROOT = Path("/root/.openclaw/workspace/CS-Notes")
TODOS_MD = REPO_ROOT / ".trae/documents/todos管理系统.md"
TODOS_JSON = REPO_ROOT / ".trae/todos/todos.json"

def load_todos_json():
    """从 JSON 加载 todos"""
    with open(TODOS_JSON, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data['todos']

def save_todos_json(todos):
    """保存 todos 到 JSON 文件"""
    data = {
        "version": "1.0.0",
        "updated_at": datetime.now().isoformat(),
        "todos": todos
    }
    with open(TODOS_JSON, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"✅ 已保存 {len(todos)} 个 todos 到 {TODOS_JSON}")

def format_todo_markdown(todo, index):
    """格式化单个 todo 为 Markdown"""
    lines = []
    
    # 状态
    status_mark = 'x' if todo['status'] == 'completed' else ' '
    lines.append(f"* [{status_mark}] {todo['title']}")
    
    # 属性
    if 'priority' in todo:
        lines.append(f"  - Priority：{todo['priority'].capitalize()}")
    if 'assignee' in todo:
        lines.append(f"  - Assignee：{todo['assignee'].capitalize()}")
    if 'feedback_required' in todo:
        lines.append(f"  - Feedback Required：{'是' if todo['feedback_required'] else '否'}")
    if 'links' in todo and todo['links']:
        lines.append(f"  - Links：{', '.join(todo['links'])}")
    if 'definition_of_done' in todo and todo['definition_of_done']:
        lines.append("  - Definition of Done：")
        for item in todo['definition_of_done']:
            lines.append(f"    * {item}")
    if 'progress' in todo:
        lines.append(f"  - Progress：{todo['progress']}")
    if 'started_at' in todo:
        lines.append(f"  - Started At：{todo['started_at']}")
    if 'completed_at' in todo:
        lines.append(f"  - Completed At：{todo['completed_at']}")
    if 'next_steps' in todo and todo['next_steps']:
        lines.append("  - Next Steps：")
        for item in todo['next_steps']:
            lines.append(f"    * {item}")
    if 'dependencies' in todo and todo['dependencies']:
        lines.append("  - 前置依赖：")
        for item in todo['dependencies']:
            lines.append(f"    * {item}")
    if 'background' in todo:
        lines.append(f"  - 背景：{todo['background']}")
    if 'user_requirements' in todo and todo['user_requirements']:
        lines.append("  - 用户要求：")
        for item in todo['user_requirements']:
            lines.append(f"    * {item}")
    
    return '\n'.join(lines)

def json_to_markdown(todos):
    """将 JSON 格式的 todos 转换为 Markdown 格式"""
    lines = []
    
    # 头部
    lines.append("# Todos 管理系统\n")
    lines.append("## 进行中 (In Progress)\n")
    
    # 进行中的 todos
    in_progress_todos = [t for t in todos if t['status'] == 'in_progress']
    for i, todo in enumerate(in_progress_todos):
        lines.append(format_todo_markdown(todo, i))
        lines.append("")
    
    # 待处理的 todos
    lines.append("## 待处理 (Pending)\n")
    lines.append("### AI 需要做的任务（优先执行）\n")
    
    pending_todos = [t for t in todos if t['status'] == 'pending']
    ai_pending_todos = [t for t in pending_todos if t.get('assignee', '').lower() == 'ai']
    for i, todo in enumerate(ai_pending_todos):
        lines.append(format_todo_markdown(todo, i))
        lines.append("")
    
    lines.append("### User 需要做的任务\n")
    user_pending_todos = [t for t in pending_todos if t.get('assignee', '').lower() != 'ai']
    for i, todo in enumerate(user_pending_todos):
        lines.append(format_todo_markdown(todo, i))
        lines.append("")
    
    # 已完成的 todos
    lines.append("## 已完成 (Completed)\n")
    completed_todos = [t for t in todos if t['status'] == 'completed']
    for i, todo in enumerate(completed_todos):
        lines.append(format_todo_markdown(todo, i))
        lines.append("")
    
    return '\n'.join(lines)

def save_todos_markdown(content):
    """保存 todos 到 Markdown 文件"""
    with open(TODOS_MD, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"✅ 已保存 todos 到 {TODOS_MD}")

def main():
    """主函数"""
    print("开始同步 todos (JSON → Markdown)...")
    
    # 从 JSON 加载 todos
    todos = load_todos_json()
    print(f"✅ 已加载 {len(todos)} 个 todos（来自 JSON）")
    
    # 转换为 Markdown
    markdown_content = json_to_markdown(todos)
    
    # 保存到 Markdown
    save_todos_markdown(markdown_content)
    
    print("\n✅ 同步完成！")

if __name__ == "__main__":
    main()
