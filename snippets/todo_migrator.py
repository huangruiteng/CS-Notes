#!/usr/bin/env python3
"""
Todos 迁移工具（Phase 2）
从 Markdown 格式迁移到 JSON 格式
"""

import re
import json
from pathlib import Path
from datetime import datetime

# 配置路径
REPO_ROOT = Path("/root/.openclaw/workspace/CS-Notes")
TODOS_MD = REPO_ROOT / ".trae/documents/todos管理系统.md"
ARCHIVE_MD = REPO_ROOT / ".trae/documents/TODO_ARCHIVE.md"
TODOS_JSON = REPO_ROOT / ".trae/todos/todos.json"
ARCHIVE_DIR = REPO_ROOT / ".trae/todos/archive"

# 非任务 section 的关键词
NON_TASK_SECTIONS = [
    "## 快速使用",
    "## 使用说明",
    "## 简介",
    "## 整体架构设计",
    "## 核心思路",
    "## 三者交互流程",
    "## 各组件职责",
    "## 火山引擎部署",
    "## OpenClaw",
    "## 手机端提交任务",
    "## 电脑端同步任务"
]

def generate_todo_id(index):
    """生成唯一的 todo ID"""
    today = datetime.now().strftime("%Y%m%d")
    # 自增 ID，从 001 开始
    return f"todo-{today}-{index+1:03d}"

def parse_todo_line(line, index):
    """解析 todo 行"""
    # 检查是否是 todo 开始
    task_match = re.match(r'^\s*\* \[([x ])\]', line)
    if not task_match:
        return None
    
    is_completed = task_match.group(1) == 'x'
    # 提取标题
    title = line[task_match.end():].strip()
    
    return {
        "id": generate_todo_id(index),
        "title": title,
        "status": "completed" if is_completed else "pending",
        "priority": "medium",  # 默认优先级
        "assignee": "ai",  # 默认执行者
        "feedback_required": False,
        "created_at": datetime.now().isoformat()
    }

def parse_todos_md():
    """解析 todos管理系统.md"""
    with open(TODOS_MD, 'r', encoding='utf-8') as f:
        content = f.read()
    
    todos = []
    lines = content.split('\n')
    
    current_todo = None
    in_pending = False
    in_in_progress = False
    in_completed = False
    todo_index = 0
    current_key = None
    
    for line in lines:
        # 检查 section
        if '### 待处理' in line:
            in_pending = True
            in_in_progress = False
            in_completed = False
            continue
        elif '### 进行中' in line:
            in_pending = False
            in_in_progress = True
            in_completed = False
            continue
        elif '### 已完成' in line:
            in_pending = False
            in_in_progress = False
            in_completed = True
            continue
        
        # 解析 todo
        todo = parse_todo_line(line, todo_index)
        if todo:
            # 设置状态
            if in_pending:
                todo['status'] = 'pending'
            elif in_in_progress:
                todo['status'] = 'in_progress'
            elif in_completed:
                todo['status'] = 'completed'
            
            todos.append(todo)
            current_todo = todo
            current_key = None
            todo_index += 1
        elif current_todo:
            # 解析属性
            attr_match = re.match(r'^\s*-\s*([^：]+)[:：]\s*(.*)$', line)
            if attr_match:
                key = attr_match.group(1).strip()
                value = attr_match.group(2).strip()
                current_key = key
                
                # 映射属性
                if key == 'Priority':
                    current_todo['priority'] = value.lower()
                elif key == 'Assignee':
                    current_todo['assignee'] = value.lower()
                elif key == 'Feedback Required':
                    current_todo['feedback_required'] = value == '是'
                elif key == 'Links':
                    if 'links' not in current_todo:
                        current_todo['links'] = []
                    if value:
                        current_todo['links'].append(value)
                elif key == 'Definition of Done':
                    if 'definition_of_done' not in current_todo:
                        current_todo['definition_of_done'] = []
                    if value:
                        current_todo['definition_of_done'].append(value)
                elif key == 'Progress':
                    current_todo['progress'] = value
                elif key == 'Started At':
                    current_todo['started_at'] = value
                elif key == 'Completed At':
                    current_todo['completed_at'] = value
                elif key == 'Next Steps':
                    if 'next_steps' not in current_todo:
                        current_todo['next_steps'] = []
                    if value:
                        current_todo['next_steps'].append(value)
                elif key == '前置依赖':
                    if 'dependencies' not in current_todo:
                        current_todo['dependencies'] = []
                    if value:
                        current_todo['dependencies'].append(value)
                elif key == '背景':
                    if 'background' not in current_todo:
                        current_todo['background'] = ''
                    if value:
                        current_todo['background'] = value
                elif key == '用户要求':
                    if 'user_requirements' not in current_todo:
                        current_todo['user_requirements'] = []
                    if value:
                        current_todo['user_requirements'].append(value)
            elif current_key:
                # 继续添加到当前 key
                stripped_line = line.strip()
                if stripped_line:
                    # 检查是否是列表项
                    list_match = re.match(r'^\s*\*\s*(.*)$', stripped_line)
                    if list_match:
                        value = list_match.group(1).strip()
                    else:
                        value = stripped_line
                    
                    if current_key == 'Links' and 'links' in current_todo:
                        current_todo['links'].append(value)
                    elif current_key == 'Definition of Done' and 'definition_of_done' in current_todo:
                        current_todo['definition_of_done'].append(value)
                    elif current_key == 'Next Steps' and 'next_steps' in current_todo:
                        current_todo['next_steps'].append(value)
                    elif current_key == '前置依赖' and 'dependencies' in current_todo:
                        current_todo['dependencies'].append(value)
                    elif current_key == '用户要求' and 'user_requirements' in current_todo:
                        current_todo['user_requirements'].append(value)
                    elif current_key == '背景' and 'background' in current_todo:
                        if current_todo['background']:
                            current_todo['background'] += '\n' + value
                        else:
                            current_todo['background'] = value
    
    return todos

def save_todos_json(todos):
    """保存 todos 到 JSON 文件"""
    # 确保目录存在
    TODOS_JSON.parent.mkdir(parents=True, exist_ok=True)
    
    data = {
        "version": "1.0.0",
        "updated_at": datetime.now().isoformat(),
        "todos": todos
    }
    
    with open(TODOS_JSON, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"✅ 已保存 {len(todos)} 个 todos 到 {TODOS_JSON}")

def parse_archive_md():
    """解析 TODO_ARCHIVE.md"""
    with open(ARCHIVE_MD, 'r', encoding='utf-8') as f:
        content = f.read()
    
    todos = []
    lines = content.split('\n')
    
    current_todo = None
    in_non_task_section = False
    todo_index = 0
    current_key = None
    
    for line in lines:
        # 检查是否是非任务 section
        is_non_task = False
        for keyword in NON_TASK_SECTIONS:
            if keyword in line:
                is_non_task = True
                break
        
        if is_non_task:
            in_non_task_section = True
            continue
        
        # 解析 todo
        todo = parse_todo_line(line, todo_index)
        if todo:
            todos.append(todo)
            current_todo = todo
            current_key = None
            todo_index += 1
        elif current_todo:
            # 解析属性
            attr_match = re.match(r'^\s*-\s*([^：]+)[:：]\s*(.*)$', line)
            if attr_match:
                key = attr_match.group(1).strip()
                value = attr_match.group(2).strip()
                current_key = key
                
                # 映射属性
                if key == 'Priority':
                    current_todo['priority'] = value.lower()
                elif key == 'Assignee':
                    current_todo['assignee'] = value.lower()
                elif key == 'Feedback Required':
                    current_todo['feedback_required'] = value == '是'
                elif key == 'Links':
                    if 'links' not in current_todo:
                        current_todo['links'] = []
                    if value:
                        current_todo['links'].append(value)
                elif key == 'Definition of Done':
                    if 'definition_of_done' not in current_todo:
                        current_todo['definition_of_done'] = []
                    if value:
                        current_todo['definition_of_done'].append(value)
                elif key == 'Progress':
                    current_todo['progress'] = value
                elif key == 'Started At':
                    current_todo['started_at'] = value
                elif key == 'Completed At':
                    current_todo['completed_at'] = value
                elif key == 'Next Steps':
                    if 'next_steps' not in current_todo:
                        current_todo['next_steps'] = []
                    if value:
                        current_todo['next_steps'].append(value)
                elif key == '前置依赖':
                    if 'dependencies' not in current_todo:
                        current_todo['dependencies'] = []
                    if value:
                        current_todo['dependencies'].append(value)
                elif key == '背景':
                    if 'background' not in current_todo:
                        current_todo['background'] = ''
                    if value:
                        current_todo['background'] = value
                elif key == '用户要求':
                    if 'user_requirements' not in current_todo:
                        current_todo['user_requirements'] = []
                    if value:
                        current_todo['user_requirements'].append(value)
            elif current_key:
                # 继续添加到当前 key
                stripped_line = line.strip()
                if stripped_line:
                    # 检查是否是列表项
                    list_match = re.match(r'^\s*\*\s*(.*)$', stripped_line)
                    if list_match:
                        value = list_match.group(1).strip()
                    else:
                        value = stripped_line
                    
                    if current_key == 'Links' and 'links' in current_todo:
                        current_todo['links'].append(value)
                    elif current_key == 'Definition of Done' and 'definition_of_done' in current_todo:
                        current_todo['definition_of_done'].append(value)
                    elif current_key == 'Next Steps' and 'next_steps' in current_todo:
                        current_todo['next_steps'].append(value)
                    elif current_key == '前置依赖' and 'dependencies' in current_todo:
                        current_todo['dependencies'].append(value)
                    elif current_key == '用户要求' and 'user_requirements' in current_todo:
                        current_todo['user_requirements'].append(value)
                    elif current_key == '背景' and 'background' in current_todo:
                        if current_todo['background']:
                            current_todo['background'] += '\n' + value
                        else:
                            current_todo['background'] = value
    
    return todos

def save_archive_json(todos):
    """保存归档 todos 到 JSON 文件"""
    # 确保目录存在
    ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)
    
    # 按月份归档
    today = datetime.now()
    month_str = today.strftime("%Y-%m")
    archive_path = ARCHIVE_DIR / f"{month_str}.json"
    
    data = {
        "version": "1.0.0",
        "updated_at": datetime.now().isoformat(),
        "todos": todos
    }
    
    with open(archive_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"✅ 已保存 {len(todos)} 个归档 todos 到 {archive_path}")

def main():
    """主函数"""
    print("开始迁移 todos...")
    
    # 解析 todos管理系统.md
    todos = parse_todos_md()
    print(f"✅ 已解析 {len(todos)} 个 todos（来自 todos管理系统.md）")
    
    # 解析 TODO_ARCHIVE.md
    archive_todos = parse_archive_md()
    print(f"✅ 已解析 {len(archive_todos)} 个归档 todos（来自 TODO_ARCHIVE.md）")
    
    # 保存到 JSON
    save_todos_json(todos)
    if archive_todos:
        save_archive_json(archive_todos)
    
    print("\n✅ 迁移完成！")

if __name__ == "__main__":
    main()
