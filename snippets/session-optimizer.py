#!/usr/bin/env python3
"""
OpenClaw Session 优化器
基于 OpenClaw 现有能力，不侵入内部代码
自动监控 session 状态，在需要时提醒用户切换 session

使用方法：
1. 每次对话前运行：python3 session-optimizer.py check
2. 如果看到警告，在 OpenClaw TUI 中使用 `/reset` 命令
"""

import os
import json
import re
from datetime import datetime
from pathlib import Path

class SessionOptimizer:
    def __init__(self, workspace_path=None):
        # 固定使用 CS-Notes 目录作为 workspace
        self.workspace_path = Path("/root/.openclaw/workspace/CS-Notes")
        self.state_file = self.workspace_path / ".openclaw-session-optimizer.json"
        self.todo_archive_file = self.workspace_path / ".trae/documents/TODO_ARCHIVE.md"
        self.state = self.load_state()
    
    def load_state(self):
        """加载状态，智能检测是否需要重置 session"""
        if self.state_file.exists():
            try:
                with open(self.state_file, 'r', encoding='utf-8') as f:
                    state = json.load(f)
                
                # 智能检测是否需要重置 session
                # 检查 1: session 开始时间是否太久远（超过 24 小时）
                session_start = datetime.fromisoformat(state["session_start_time"])
                session_age = (datetime.now() - session_start).total_seconds()
                
                # 检查 2: 状态文件最后修改时间是否太久远（超过 8 小时）
                # 如果状态文件很久没有更新，说明可能是新 session
                file_mtime = datetime.fromtimestamp(self.state_file.stat().st_mtime)
                file_age = (datetime.now() - file_mtime).total_seconds()
                
                # 检查 3: 是否有明确的重置信号（通过 last_reset 字段）
                # 如果 last_reset 存在且 session_start_time 早于 last_reset，说明需要重置
                
                # 智能判断：如果 session 超过 24 小时，或者状态文件超过 8 小时没有更新，
                # 或者用户明确执行了 reset 命令，就认为需要重置
                need_reset = False
                reset_reason = ""
                
                if session_age > 24 * 3600:
                    need_reset = True
                    reset_reason = f"Session 已运行 {session_age/3600:.1f} 小时（超过 24 小时）"
                elif file_age > 8 * 3600:
                    need_reset = True
                    reset_reason = f"状态文件已 {file_age/60:.1f} 分钟没有更新（可能是新 session）"
                
                if need_reset:
                    print(f"[提示] 检测到可能需要重置 session：{reset_reason}")
                    print(f"[提示] 自动重置 session...")
                    return self._reset_state(state)
                
                return state
            except Exception as e:
                print(f"[警告] 加载状态失败: {e}")
        
        # 创建新状态
        return self._create_new_state()
    
    def _create_new_state(self):
        """创建新的状态"""
        new_state = {
            "session_start_time": datetime.now().isoformat(),
            "warnings_given": [],
            "last_reset": None,
            "history": [],
            "last_archive_count": 0,
            "tasks_completed_in_session": 0,
            "last_check_time": datetime.now().isoformat()
        }
        
        # 初始化时记录当前的 archive 数量
        new_state["last_archive_count"] = self.count_archived_tasks()
        
        # 立即保存
        try:
            with open(self.state_file, 'w', encoding='utf-8') as f:
                json.dump(new_state, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"[警告] 保存状态失败: {e}")
        
        return new_state
    
    def _reset_state(self, old_state):
        """重置状态，保留历史记录"""
        # 记录历史
        if "history" not in old_state:
            old_state["history"] = []
        
        old_state["history"].append({
            "start_time": old_state["session_start_time"],
            "end_time": datetime.now().isoformat(),
            "warnings_given": old_state.get("warnings_given", []),
            "tasks_completed": old_state.get("tasks_completed_in_session", 0)
        })
        
        # 创建新状态，保留历史记录
        new_state = self._create_new_state()
        new_state["history"] = old_state["history"]
        new_state["last_reset"] = datetime.now().isoformat()
        
        # 保存
        try:
            with open(self.state_file, 'w', encoding='utf-8') as f:
                json.dump(new_state, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"[警告] 保存状态失败: {e}")
        
        return new_state
    
    def count_archived_tasks(self):
        """统计 TODO_ARCHIVE.md 中已完成的任务数量"""
        if not self.todo_archive_file.exists():
            return 0
        
        try:
            with open(self.todo_archive_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 统计所有 `- [x]` 标记的任务
            completed_tasks = re.findall(r'- \[x\]', content)
            return len(completed_tasks)
        except Exception as e:
            print(f"[警告] 统计归档任务失败: {e}")
            return 0
    
    def check_new_archived_tasks(self):
        """检查是否有新的归档任务"""
        current_count = self.count_archived_tasks()
        last_count = self.state.get("last_archive_count", 0)
        
        if current_count > last_count:
            new_tasks = current_count - last_count
            self.state["last_archive_count"] = current_count
            self.state["tasks_completed_in_session"] = self.state.get("tasks_completed_in_session", 0) + new_tasks
            self.save_state()
            return new_tasks
        
        return 0
    
    def save_state(self):
        """保存状态"""
        with open(self.state_file, 'w', encoding='utf-8') as f:
            json.dump(self.state, f, ensure_ascii=False, indent=2)
    
    def check_session(self):
        """检查 session 状态，返回是否需要切换"""
        # 更新最后检查时间
        self.state["last_check_time"] = datetime.now().isoformat()
        
        session_age = (datetime.now() - datetime.fromisoformat(self.state["session_start_time"])).total_seconds()
        
        # 计算更友好的时间显示
        hours = int(session_age // 3600)
        minutes = int((session_age % 3600) // 60)
        seconds = int(session_age % 60)
        
        # 检查是否有新的归档任务
        new_archived_tasks = self.check_new_archived_tasks()
        tasks_completed_in_session = self.state.get("tasks_completed_in_session", 0)
        
        print("=" * 60)
        print("🔍 OpenClaw Session 检查")
        print("=" * 60)
        print()
        print(f"🕐 Session 开始时间: {self.state['session_start_time']}")
        print(f"⏱️  Session 已运行: {hours}小时 {minutes}分 {seconds}秒 ({session_age/3600:.2f} 小时)")
        print(f"✅ 本 session 已完成任务: {tasks_completed_in_session} 个")
        if new_archived_tasks > 0:
            print(f"🆕 本次检查新发现: {new_archived_tasks} 个归档任务")
        print()
        
        need_reset = False
        warnings = []
        
        # 检查 1: 已完成任务数量
        if tasks_completed_in_session >= 3:
            warnings.append(f"⚠️ 本 session 已完成 {tasks_completed_in_session} 个任务，超过 3 个，建议切换 session！")
            need_reset = True
        elif tasks_completed_in_session >= 2:
            warnings.append(f"📊 本 session 已完成 {tasks_completed_in_session} 个任务")
        
        # 检查 2: 时间
        if session_age >= 24 * 3600:  # 24 小时
            warnings.append(f"⚠️ Session 已运行超过 24 小时，建议切换！")
            need_reset = True
        elif session_age >= 12 * 3600:  # 12 小时
            warnings.append(f"📊 Session 已运行 {session_age/3600:.1f} 小时")
        
        if warnings:
            print("⚠️ 警告:")
            for warning in warnings:
                print(f"  {warning}")
            print()
        
        if need_reset:
            print("🚨 建议立即切换 session！")
            print()
            print("操作步骤:")
            print("1. 在 OpenClaw TUI 中输入 `/reset`")
            print("2. 确认 session 已重置")
            print("3. 继续你的对话")
            print()
        else:
            print("✅ Session 状态良好，继续使用！")
            print()
        
        print("=" * 60)
        
        # 记录警告
        if warnings:
            self.state["warnings_given"].extend(warnings)
        
        # 保存状态（包含 last_check_time）
        self.save_state()
        
        return need_reset
    
    def reset_session(self):
        """重置 session（记录状态，实际切换在 OpenClaw TUI 中执行）"""
        print()
        print("🔄 准备重置 session...")
        print()
        print("⚠️ 重要提示：")
        print("   这个脚本只是记录状态，实际的 session 切换")
        print("   需要在 OpenClaw TUI 中执行 `/reset` 命令")
        print()
        
        # 记录历史
        self.state["history"].append({
            "start_time": self.state["session_start_time"],
            "end_time": datetime.now().isoformat(),
            "warnings_given": self.state["warnings_given"],
            "tasks_completed": self.state.get("tasks_completed_in_session", 0)
        })
        
        # 重置状态
        self.state["session_start_time"] = datetime.now().isoformat()
        self.state["warnings_given"] = []
        self.state["last_reset"] = datetime.now().isoformat()
        self.state["tasks_completed_in_session"] = 0
        self.state["last_archive_count"] = self.count_archived_tasks()
        self.save_state()
        
        print("✅ 状态已记录！")
        print()
        print("现在请在 OpenClaw TUI 中执行：")
        print("  /reset")
        print()
    
    def print_history(self):
        """打印历史记录"""
        print("=" * 60)
        print("📊 Session 历史记录")
        print("=" * 60)
        print()
        
        if not self.state["history"]:
            print("暂无历史记录")
            print()
            return
        
        for i, session in enumerate(reversed(self.state["history"][-5:])):  # 只显示最近 5 个
            print(f"Session {len(self.state['history']) - i}:")
            print(f"  开始: {session['start_time']}")
            print(f"  结束: {session['end_time']}")
            print(f"  完成任务: {session.get('tasks_completed', 0)} 个")
            print(f"  警告数: {len(session['warnings_given'])}")
            print()
        
        print("=" * 60)


def main():
    """主函数"""
    import sys
    
    optimizer = SessionOptimizer()
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "check":
            optimizer.check_session()
        elif command == "reset":
            optimizer.reset_session()
        elif command == "history":
            optimizer.print_history()
        else:
            print(f"未知命令: {command}")
            print("使用:")
            print("  python session-optimizer.py check     # 检查 session 状态")
            print("  python session-optimizer.py reset     # 准备重置 session")
            print("  python session-optimizer.py history   # 查看历史记录")
    else:
        optimizer.check_session()


if __name__ == "__main__":
    main()
