#!/usr/bin/env python3
"""
Todo 工具函数 - 用于更新 todos.json，自动添加 commit_hash 等
"""

import os
import sys
import json
import subprocess
from pathlib import Path
from datetime import datetime


def get_repo_root():
    """获取仓库根目录"""
    return Path(__file__).parent.parent.parent


def get_todos_file_path():
    """获取 todos.json 文件路径"""
    return get_repo_root() / ".trae" / "todos" / "todos.json"


def get_current_commit_hash():
    """获取当前 git commit hash"""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=get_repo_root(),
            capture_output=True,
            text=True,
            timeout=30
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except Exception as e:
        print(f"⚠️ 获取 commit hash 失败: {e}", file=sys.stderr)
    return None


def load_todos():
    """加载 todos.json"""
    todos_file = get_todos_file_path()
    if not todos_file.exists():
        return {
            "version": "1.0.0",
            "updated_at": datetime.now().isoformat(),
            "todos": []
        }
    try:
        with open(todos_file, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"⚠️ 加载 todos.json 失败: {e}", file=sys.stderr)
        return {
            "version": "1.0.0",
            "updated_at": datetime.now().isoformat(),
            "todos": []
        }


def save_todos(data):
    """保存 todos.json"""
    todos_file = get_todos_file_path()
    try:
        data["updated_at"] = datetime.now().isoformat()
        with open(todos_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"⚠️ 保存 todos.json 失败: {e}", file=sys.stderr)
        return False


def update_task_status(task_id, new_status, progress=None, completed_at=None):
    """
    更新任务状态，自动添加 commit_hash（当状态变为 completed 时）
    
    Args:
        task_id: 任务 ID
        new_status: 新状态（pending/in-progress/completed）
        progress: 可选，更新进度
        completed_at: 可选，完成时间
    
    Returns:
        bool: 是否成功
    """
    data = load_todos()
    tasks = data.get("todos", [])
    
    task_found = False
    for i, task in enumerate(tasks):
        if task.get("id") == task_id:
            old_status = task.get("status")
            tasks[i]["status"] = new_status
            
            if progress is not None:
                tasks[i]["progress"] = progress
            
            if new_status == "in-progress" and not task.get("started_at"):
                tasks[i]["started_at"] = datetime.now().isoformat()
            
            if new_status == "completed" and old_status != "completed":
                if completed_at:
                    tasks[i]["completed_at"] = completed_at
                else:
                    tasks[i]["completed_at"] = datetime.now().isoformat()
                
                commit_hash = get_current_commit_hash()
                if commit_hash:
                    tasks[i]["commit_hash"] = commit_hash
                    print(f"✅ 已自动添加 commit_hash: {commit_hash[:7]}")
            
            task_found = True
            break
    
    if not task_found:
        print(f"⚠️ 任务 {task_id} 不存在", file=sys.stderr)
        return False
    
    return save_todos(data)


def mark_task_completed(task_id, progress=None):
    """
    标记任务为完成，自动添加 commit_hash
    
    Args:
        task_id: 任务 ID
        progress: 可选，更新进度
    
    Returns:
        bool: 是否成功
    """
    return update_task_status(task_id, "completed", progress=progress)


def add_task(title, priority="P5", assignee="ai", description="", links=None, definition_of_done=None):
    """
    添加新任务
    
    Args:
        title: 任务标题
        priority: 优先级
        assignee: 负责人
        description: 描述
        links: 相关链接
        definition_of_done: 完成标准
    
    Returns:
        str: 新任务 ID
    """
    data = load_todos()
    tasks = data.get("todos", [])
    
    today = datetime.now().strftime("%Y%m%d")
    existing_ids = [t.get("id", "") for t in tasks]
    max_seq = 0
    for task_id in existing_ids:
        if task_id.startswith(f"todo-{today}-"):
            try:
                seq = int(task_id.split("-")[-1])
                max_seq = max(max_seq, seq)
            except ValueError:
                pass
    
    new_task_id = f"todo-{today}-{max_seq + 1:03d}"
    
    new_task = {
        "id": new_task_id,
        "title": title,
        "status": "pending",
        "priority": priority,
        "assignee": assignee,
        "feedback_required": False,
        "created_at": datetime.now().isoformat(),
        "links": links or [],
        "definition_of_done": definition_of_done or [],
        "progress": description
    }
    
    tasks.append(new_task)
    data["todos"] = tasks
    
    if save_todos(data):
        print(f"✅ 任务已添加: {new_task_id}")
        return new_task_id
    else:
        return None


def get_task(task_id):
    """获取任务详情"""
    data = load_todos()
    tasks = data.get("todos", [])
    for task in tasks:
        if task.get("id") == task_id:
            return task
    return None


if __name__ == "__main__":
    print("=" * 60)
    print("Todo 工具函数")
    print("=" * 60)
    print()
    print("可用函数:")
    print("  - mark_task_completed(task_id, progress=None) - 标记任务为完成")
    print("  - update_task_status(task_id, new_status, progress=None) - 更新任务状态")
    print("  - add_task(title, ...) - 添加新任务")
    print("  - get_task(task_id) - 获取任务详情")
    print()
    print("示例:")
    print("  from Notes.snippets.todo_utils import mark_task_completed")
    print("  mark_task_completed('todo-20260223-001')")
    print()
    print("=" * 60)
