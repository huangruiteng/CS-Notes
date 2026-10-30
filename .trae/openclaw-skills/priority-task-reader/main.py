#!/usr/bin/env python3
"""
按优先级读取任务 Skill - 从 todos.json 读取 in-progress 和 pending 任务，按 P0-P9 优先级排序
"""

import os
import sys
import json
import argparse
from pathlib import Path


class PriorityTaskReader:
    """按优先级读取任务"""
    
    def __init__(self, config: dict):
        """初始化"""
        self.config = config
        self.todos_json_path = Path(config.get("todos_json_path", ""))
        self.workspace = Path(config.get("workspace", ""))
        
        self.priority_order = {
            'P0': 0, 'P1': 1, 'P2': 2, 'P3': 3, 'P4': 4,
            'P5': 5, 'P6': 6, 'P7': 7, 'P8': 8, 'P9': 9,
            'high': 2, 'medium': 5, 'low': 8
        }
    
    def get_priority_score(self, priority: str) -> int:
        """获取优先级分数"""
        return self.priority_order.get(priority, 99)
    
    def load_todos(self) -> dict:
        """加载 todos.json"""
        try:
            if not self.todos_json_path.exists():
                print(f"Error: todos.json not found at {self.todos_json_path}")
                return None
            
            with open(self.todos_json_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading todos.json: {e}")
            return None
    
    def get_latest_review_time(self, task: dict) -> str:
        """获取任务的最新 review 时间"""
        # 检查 review_history
        if "review_history" in task and task["review_history"]:
            return task["review_history"][-1].get("reviewed_at", "")
        # 检查 plan_review_history
        if "plan_review_history" in task and task["plan_review_history"]:
            return task["plan_review_history"][-1].get("reviewed_at", "")
        # 如果没有 review，返回空字符串
        return ""
    
    def filter_and_sort_tasks(self, todos_data: dict) -> list:
        """过滤并排序任务
        
        优先级排序规则：
        1. 有最新 review 意见的 in-progress 任务（最高优先级）
        2. 其他 in-progress 任务
        3. 按 P0-P9 优先级排序
        4. 最后按创建时间排序
        """
        if not todos_data or "todos" not in todos_data:
            return []
        
        all_tasks = todos_data["todos"]
        
        # 筛选 in-progress 和 pending 任务
        target_tasks = [
            task for task in all_tasks
            if task.get("status") in ["in-progress", "pending"]
        ]
        
        # 排序键：
        # 1. 是否是 in-progress 且有最新 review（0 表示是，1 表示否）
        # 2. 最新 review 时间（倒序，最新的在前）- 对于有 review 的 in-progress 任务，这是最重要的
        # 3. 优先级分数（P0-P9）
        # 4. 是否是 in-progress（0 表示是，1 表示否）
        # 5. 创建时间
        sorted_tasks = sorted(
            target_tasks,
            key=lambda task: (
                # 最高优先级：in-progress 且有最新 review 意见
                0 if (task.get("status") == "in-progress" and self.get_latest_review_time(task)) else 1,
                # 最新 review 时间倒序（使用负数，因为 sorted 默认是升序）
                # 对于时间字符串，我们用反向排序
                -float(self.get_latest_review_time(task).replace("-", "").replace(":", "").replace("T", "").replace(".", "")) if self.get_latest_review_time(task) else float("inf"),
                self.get_priority_score(task.get("priority", "low")),
                0 if task.get("status") == "in-progress" else 1,
                task.get("created_at", "")
            )
        )
        
        return sorted_tasks
    
    def print_task_summary(self, tasks: list):
        """打印任务摘要"""
        print("=" * 80)
        print("📋 按优先级排序的任务列表")
        print("=" * 80)
        print()
        
        if not tasks:
            print("❌ 没有找到 in-progress 或 pending 的任务")
            return
        
        # 按优先级分组
        priority_groups = {}
        for task in tasks:
            priority = task.get("priority", "low")
            if priority not in priority_groups:
                priority_groups[priority] = []
            priority_groups[priority].append(task)
        
        # 按优先级顺序打印
        for priority in sorted(priority_groups.keys(), key=self.get_priority_score):
            group_tasks = priority_groups[priority]
            print(f"\n{'=' * 80}")
            print(f"🔸 优先级: {priority} ({len(group_tasks)} 个任务)")
            print(f"{'=' * 80}")
            
            for i, task in enumerate(group_tasks, 1):
                status_icon = "🚀" if task.get("status") == "in-progress" else "⏸️"
                assignee = task.get("assignee", "unknown")
                title = task.get("title", "")[:80]
                codex_triage = task.get("codex_triage", "")
                
                print(f"\n  {i}. {status_icon} [{task.get('id', '')}]")
                print(f"     标题: {title}")
                print(f"     负责人: {assignee}")
                if codex_triage:
                    print(f"     Codex 分类: {codex_triage}")
                if task.get("feedback_required"):
                    print(f"     ⚠️ 需要用户确认")
        
        print(f"\n{'=' * 80}")
        print(f"📊 总计: {len(tasks)} 个任务 (in-progress + pending)")
        print(f"{'=' * 80}")
    
    def get_next_tasks(self, tasks: list, count: int = 1) -> list:
        """获取下一个应该执行的任务（支持获取多个）
        
        自主推进时只返回 pending 状态的任务，避免多 session 冲突
        同时考虑 codex_triage 元数据，排除 user_or_environment_blocked 等
        """
        next_tasks = []
        for task in tasks:
            # 检查 codex_triage 元数据
            codex_triage = task.get("codex_triage", "")
            
            # 排除明确标记为阻塞或已合并的任务
            if "user_or_environment_blocked" in codex_triage or "merged_into_codex_todo_system_v2" in codex_triage:
                continue
            
            # 基本条件：AI 负责、不需要用户确认、pending 状态
            if (task.get("assignee") in ["ai", "codex"] and 
                not task.get("feedback_required") and 
                task.get("status") == "pending"):
                next_tasks.append(task)
                if len(next_tasks) >= count:
                    break
        return next_tasks
    
    def run(self, args):
        """运行"""
        print("=" * 80)
        print("🤖 按优先级读取任务")
        print("=" * 80)
        print()
        
        # 加载 todos
        print("📂 加载 todos.json...")
        todos_data = self.load_todos()
        if not todos_data:
            return
        
        # 筛选和排序任务
        print("🔍 筛选和排序任务...")
        sorted_tasks = self.filter_and_sort_tasks(todos_data)
        
        # 打印摘要
        self.print_task_summary(sorted_tasks)
        
        # 如果需要，输出 JSON 格式
        if args.json:
            print("\n" + "=" * 80)
            print("📄 JSON 格式输出")
            print("=" * 80)
            print(json.dumps(sorted_tasks, ensure_ascii=False, indent=2))
        
        # 获取下一个任务（支持获取多个）
        if args.next:
            next_count = args.next_count if hasattr(args, 'next_count') and args.next_count else 1
            next_tasks = self.get_next_tasks(sorted_tasks, next_count)
            if next_tasks:
                if len(next_tasks) == 1:
                    print("\n" + "=" * 80)
                    print("🎯 下一个应该执行的任务")
                    print("=" * 80)
                    print(json.dumps(next_tasks[0], ensure_ascii=False, indent=2))
                else:
                    print("\n" + "=" * 80)
                    print(f"🎯 接下来 {len(next_tasks)} 个应该执行的任务")
                    print("=" * 80)
                    print(json.dumps(next_tasks, ensure_ascii=False, indent=2))
            else:
                print("\n" + "=" * 80)
                print("ℹ️ 没有找到适合 AI 执行的任务")
                print("=" * 80)


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="按优先级读取任务 Skill")
    parser.add_argument("--json", action="store_true", help="输出 JSON 格式")
    parser.add_argument("--next", action="store_true", help="显示下一个应该执行的任务")
    parser.add_argument("--next-count", type=int, default=1, help="获取 K 个任务（默认 1）")
    parser.add_argument("--config", help="配置文件路径")
    args = parser.parse_args()
    
    # 加载配置
    config = {}
    if args.config:
        config_path = Path(args.config)
        if config_path.exists():
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
    
    # 使用默认配置
    if not config:
        # 自动检测当前工作目录
        current_dir = Path.cwd()
        # 检查是否在 CS-Notes 目录中
        if (current_dir / ".trae" / "todos" / "todos.json").exists():
            workspace = current_dir
        elif (current_dir / "CS-Notes" / ".trae" / "todos" / "todos.json").exists():
            workspace = current_dir / "CS-Notes"
        else:
            # 尝试使用标准路径
            workspace = Path("/root/.openclaw/workspace/CS-Notes")
        
        config = {
            "todos_json_path": str(workspace / ".trae" / "todos" / "todos.json"),
            "workspace": str(workspace)
        }
    
    # 创建读取器并运行
    reader = PriorityTaskReader(config)
    reader.run(args)


if __name__ == '__main__':
    main()
