#!/usr/bin/env python3
"""
OpenClaw Session 监控脚本
用于监控 session 长度和 token 使用情况，提供优化建议

⚠️ 重要原则：基于 OpenClaw 现有能力，不侵入内部代码！
- 不修改 OpenClaw 源代码
- 不修改 OpenClaw 配置文件
- 仅使用 OpenClaw 已提供的功能
- 推荐使用 OpenClaw 内置的 `/reset` 命令
"""

import os
import json
from datetime import datetime
from pathlib import Path

class SessionMonitor:
    def __init__(self, workspace_path=None):
        self.workspace_path = Path(workspace_path) if workspace_path else Path.cwd()
        self.memory_path = self.workspace_path / "MEMORY.md"
        self.state_file = self.workspace_path / ".openclaw-session-state.json"
        self.state = self.load_state()
    
    def load_state(self):
        """加载状态"""
        if self.state_file.exists():
            with open(self.state_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {
            "sessions": [],
            "current_session": {
                "start_time": datetime.now().isoformat(),
                "message_count": 0,
                "token_estimate": 0,
                "warnings": []
            },
            "total_tokens_today": 0,
            "last_reset": None
        }
    
    def save_state(self):
        """保存状态"""
        with open(self.state_file, 'w', encoding='utf-8') as f:
            json.dump(self.state, f, ensure_ascii=False, indent=2)
    
    def log_message(self, token_estimate=0):
        """记录一条消息"""
        self.state["current_session"]["message_count"] += 1
        self.state["current_session"]["token_estimate"] += token_estimate
        self.state["total_tokens_today"] += token_estimate
        self.save_state()
        
        # 检查是否需要警告
        return self.check_warnings()
    
    def check_warnings(self):
        """检查是否需要警告"""
        warnings = []
        session = self.state["current_session"]
        
        # 消息数量警告
        if session["message_count"] >= 50:
            warnings.append(f"⚠️ Session 已包含 {session['message_count']} 条消息，建议使用 `/reset` 命令切换新 session")
        elif session["message_count"] >= 30:
            warnings.append(f"📊 Session 已包含 {session['message_count']} 条消息")
        
        # Token 使用警告（估算）
        if session["token_estimate"] >= 80000:  # 假设 100k 是上限
            warnings.append(f"🚨 Token 使用量已达 {session['token_estimate']:,}，强烈建议使用 `/reset` 命令切换新 session")
        elif session["token_estimate"] >= 50000:
            warnings.append(f"⚠️ Token 使用量已达 {session['token_estimate']:,}，建议考虑使用 `/reset` 命令")
        
        # 今日总 token 警告
        if self.state["total_tokens_today"] >= 10000000:  # 10M
            warnings.append(f"💰 今日 Token 使用量已达 {self.state['total_tokens_today']:,}，请注意成本")
        
        if warnings:
            session["warnings"].extend(warnings)
            self.save_state()
        
        return warnings
    
    def reset_session(self):
        """重置 session（推荐使用 OpenClaw 内置的 `/reset` 命令）"""
        print("⚠️ 推荐使用 OpenClaw 内置的 `/reset` 命令！")
        print("   这个脚本的 reset 功能仅用于演示，建议在 OpenClaw TUI 中使用 `/reset`")
        print()
        
        # 归档当前 session
        if self.state["current_session"]["message_count"] > 0:
            self.state["current_session"]["end_time"] = datetime.now().isoformat()
            self.state["sessions"].append(self.state["current_session"])
        
        # 创建新 session
        self.state["current_session"] = {
            "start_time": datetime.now().isoformat(),
            "message_count": 0,
            "token_estimate": 0,
            "warnings": []
        }
        self.state["last_reset"] = datetime.now().isoformat()
        self.save_state()
        
        return "✅ Session 已重置，新 session 已开始（建议在 OpenClaw TUI 中使用 `/reset` 命令）"
    
    def get_status(self):
        """获取当前状态"""
        session = self.state["current_session"]
        return {
            "current_session": {
                "start_time": session["start_time"],
                "message_count": session["message_count"],
                "token_estimate": session["token_estimate"],
                "warnings": session["warnings"]
            },
            "total_tokens_today": self.state["total_tokens_today"],
            "sessions_count": len(self.state["sessions"]),
            "last_reset": self.state.get("last_reset")
        }
    
    def print_report(self):
        """打印报告"""
        status = self.get_status()
        
        print("=" * 60)
        print("📊 OpenClaw Session 状态报告")
        print("=" * 60)
        print()
        print("⚠️  重要原则：基于 OpenClaw 现有能力，不侵入内部代码！")
        print("   - 不修改 OpenClaw 源代码")
        print("   - 不修改 OpenClaw 配置文件")
        print("   - 仅使用 OpenClaw 已提供的功能")
        print("   - 推荐使用 OpenClaw 内置的 `/reset` 命令")
        print()
        
        print(f"🕐 当前 Session 开始时间: {status['current_session']['start_time']}")
        print(f"💬 消息数量: {status['current_session']['message_count']}")
        print(f"🎟️ Token 估算: {status['current_session']['token_estimate']:,}")
        print()
        
        print(f"💰 今日总 Token 使用: {status['total_tokens_today']:,}")
        print(f"📚 历史 Session 数量: {status['sessions_count']}")
        if status['last_reset']:
            print(f"🔄 上次重置: {status['last_reset']}")
        print()
        
        if status['current_session']['warnings']:
            print("⚠️ 警告:")
            for warning in status['current_session']['warnings'][-5:]:  # 只显示最近 5 条
                print(f"  {warning}")
            print()
        
        print("=" * 60)


def main():
    """主函数"""
    import sys
    
    monitor = SessionMonitor()
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "status":
            monitor.print_report()
        elif command == "reset":
            result = monitor.reset_session()
            print(result)
            monitor.print_report()
        elif command == "log":
            token_estimate = int(sys.argv[2]) if len(sys.argv) > 2 else 1000
            warnings = monitor.log_message(token_estimate)
            if warnings:
                print("\n".join(warnings))
            monitor.print_report()
        else:
            print(f"未知命令: {command}")
            print("使用:")
            print("  python session-monitor.py status    # 查看状态")
            print("  python session-monitor.py reset     # 重置 session（推荐使用 OpenClaw 内置的 `/reset` 命令）")
            print("  python session-monitor.py log [tokens]  # 记录消息")
    else:
        monitor.print_report()


if __name__ == "__main__":
    main()
