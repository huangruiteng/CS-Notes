#!/usr/bin/env python3
"""
添加 todo 到 JSON 文件
"""

import json
from pathlib import Path
from datetime import datetime

# 配置路径
REPO_ROOT = Path("/root/.openclaw/workspace/CS-Notes")
TODOS_JSON = REPO_ROOT / ".trae/todos/todos.json"

def generate_todo_id(index):
    """生成唯一的 todo ID"""
    today = datetime.now().strftime("%Y%m%d")
    return f"todo-{today}-{index:03d}"

def add_todo_to_json():
    """添加 todo 到 JSON 文件"""
    # 读取现有的 JSON
    with open(TODOS_JSON, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # 生成新 todo 的 ID
    new_index = len(data['todos']) + 1
    new_todo = {
        "id": generate_todo_id(new_index),
        "title": "修复 Flask 安装问题，修复 blinker 包冲突，使 server.py 可以正常启动",
        "status": "pending",
        "priority": "high",
        "assignee": "ai",
        "feedback_required": False,
        "created_at": datetime.now().isoformat(),
        "links": [
            "`.trae/documents/Flask-安装问题-复现与修复方案.md",
            "`.trae/web-manager/server.py"
        ],
        "definition_of_done": [
            "找到可靠的 Flask 安装方法",
            "修复 blinker 包冲突问题",
            "验证 server.py 可以正常启动",
            "测试所有 API 端点正常工作"
        ],
        "progress": "问题已记录，待修复"
    }
    
    # 添加到列表
    data['todos'].append(new_todo)
    data['updated_at'] = datetime.now().isoformat()
    
    # 保存
    with open(TODOS_JSON, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"✅ 已添加新 todo 到 {TODOS_JSON}")
    print(f"   - ID: {new_todo['id']}")
    print(f"   - 标题: {new_todo['title']}")

if __name__ == "__main__":
    add_todo_to_json()
