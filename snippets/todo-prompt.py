#!/usr/bin/env python3
"""
Todo 任务提示生成器 - 扫描 Pending 任务，生成执行清单供人工确认
"""

import re
from pathlib import Path
from datetime import datetime

REPO_ROOT = Path(__file__).parent.parent.parent
TODOS_PATH = REPO_ROOT / ".trae/documents/todos管理系统.md"
LOG_DIR = REPO_ROOT / ".trae/logs"


def parse_pending_tasks(content: str):
    """解析 Pending 中的任务"""
    tasks = []
    
    pending_match = re.search(r'### 待处理 \(Pending\)(.*?)(?=### 已完成 \(Completed\)|$)', content, re.DOTALL)
    if not pending_match:
        return tasks
    
    pending_content = pending_match.group(1)
    
    lines = pending_content.split('\n')
    current_task = None
    current_field = None
    
    for line in lines:
        line = line.rstrip()
        if line.startswith('- [ ] '):
            if current_task:
                tasks.append(current_task)
            current_task = {
                'content': line[6:].strip(),
                'priority': '',
                'links': '',
                'plan': '',
                'definition_of_done': '',
                'progress': '',
                'integration': ''
            }
            current_field = None
        elif current_task:
            if line.startswith('  - Priority：'):
                current_task['priority'] = line[13:].strip()
                current_field = 'priority'
            elif line.startswith('  - Links：'):
                current_task['links'] = line[10:].strip()
                current_field = 'links'
            elif line.startswith('  - Progress：'):
                current_task['progress'] = line[12:].strip()
                current_field = 'progress'
            elif line.startswith('  - Definition of Done：'):
                current_task['definition_of_done'] = line[21:].strip()
                current_field = 'definition_of_done'
            elif line.startswith('  - Plan：'):
                current_task['plan'] = line[9:].strip()
                current_field = 'plan'
            elif line.startswith('  - 集成思路参考：'):
                current_task['integration'] = line[11:].strip()
                current_field = 'integration'
            elif line.startswith('    - ') or line.startswith('    * '):
                if current_field:
                    if current_task[current_field]:
                        current_task[current_field] += '\n' + line
                    else:
                        current_task[current_field] = line
            elif line.strip() and line.startswith('  '):
                if current_field:
                    if current_task[current_field]:
                        current_task[current_field] += '\n' + line.strip()
                    else:
                        current_task[current_field] = line.strip()
    
    if current_task:
        tasks.append(current_task)
    
    return tasks


def format_task_for_prompt(task: dict, index: int):
    """格式化任务为提示清单"""
    lines = [f"## 任务 {index + 1}: {task['content']}"]
    
    if task['priority']:
        lines.append(f"- **优先级**: {task['priority']}")
    if task['links']:
        lines.append(f"- **链接**: {task['links']}")
    if task['progress']:
        lines.append(f"- **进度**:")
        lines.append(task['progress'])
    if task['definition_of_done']:
        lines.append(f"- **验收标准**:")
        lines.append(task['definition_of_done'])
    if task['plan']:
        lines.append(f"- **计划**:")
        lines.append(task['plan'])
    if task['integration']:
        lines.append(f"- **集成思路参考**:")
        lines.append(task['integration'])
    
    lines.append("")
    return "\n".join(lines)


def main():
    print("=" * 80)
    print("Todo 任务提示生成器")
    print(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    log_file = LOG_DIR / f"todo-prompt-{datetime.now().strftime('%Y%m%d')}.log"
    
    if not TODOS_PATH.exists():
        print(f"错误：找不到文件 {TODOS_PATH}")
        return
    
    with open(TODOS_PATH, "r", encoding="utf-8") as f:
        todos_content = f.read()
    
    tasks = parse_pending_tasks(todos_content)
    
    if not tasks:
        print("\nPending 中没有待执行的任务")
        return
    
    print(f"\n找到 {len(tasks)} 个待执行任务：\n")
    print("=" * 80)
    
    prompt_content = [
        "# 待执行任务清单",
        f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "",
        "---"
    ]
    
    for i, task in enumerate(tasks):
        print(format_task_for_prompt(task, i))
        prompt_content.append(format_task_for_prompt(task, i))
    
    print("=" * 80)
    print("\n提示:")
    print("1. 请查看上面的任务清单")
    print("2. 在 Trae 中说'执行 todo'来选择任务执行")
    print("3. 或者将上面的内容复制给 Trae 开始执行")
    
    prompt_file = LOG_DIR / f"pending-tasks-{datetime.now().strftime('%Y%m%d-%H%M%S')}.md"
    with open(prompt_file, "w", encoding="utf-8") as f:
        f.write("\n".join(prompt_content))
    
    print(f"\n任务清单已保存到: {prompt_file}")
    print(f"日志文件: {log_file}")


if __name__ == "__main__":
    main()
