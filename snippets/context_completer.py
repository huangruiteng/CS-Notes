#!/usr/bin/env python3
"""
自动补全上下文
从最近的 git commit 历史和文件操作记录提取上下文
"""

import os
import json
import subprocess
from datetime import datetime, timedelta
from pathlib import Path


class ContextCompleter:
    """自动补全上下文"""
    
    def __init__(self, workspace_path=None):
        self.workspace_path = Path(workspace_path) if workspace_path else Path("/root/.openclaw/workspace/CS-Notes")
        self.state_file = self.workspace_path / ".context-completer-state.json"
        self.state = self._load_state()
    
    def _load_state(self):
        """加载状态"""
        if self.state_file.exists():
            try:
                with open(self.state_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"[警告] 加载状态失败: {e}")
        
        return {
            "last_check": None,
            "recent_files": [],
            "recent_commits": [],
            "context_history": []
        }
    
    def _save_state(self):
        """保存状态"""
        with open(self.state_file, 'w', encoding='utf-8') as f:
            json.dump(self.state, f, ensure_ascii=False, indent=2)
    
    def get_recent_git_commits(self, limit=10):
        """获取最近的 git commit 历史"""
        try:
            result = subprocess.run(
                ['git', 'log', f'-{limit}', '--pretty=format:%H|%s|%an|%ai'],
                cwd=self.workspace_path,
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode != 0:
                print(f"[警告] 获取 git log 失败: {result.stderr}")
                return []
            
            commits = []
            for line in result.stdout.strip().split('\n'):
                if not line:
                    continue
                parts = line.split('|', 3)
                if len(parts) == 4:
                    commits.append({
                        "hash": parts[0],
                        "message": parts[1],
                        "author": parts[2],
                        "time": parts[3]
                    })
            
            return commits
        except Exception as e:
            print(f"[警告] 获取 git commit 失败: {e}")
            return []
    
    def get_recent_files(self, limit=20):
        """获取最近修改的文件"""
        try:
            # 查找最近 24 小时内修改的文件
            cutoff_time = datetime.now() - timedelta(hours=24)
            
            recent_files = []
            
            for root, dirs, files in os.walk(self.workspace_path):
                # 跳过 .git 目录
                if '.git' in root:
                    continue
                
                for file in files:
                    file_path = Path(root) / file
                    
                    try:
                        mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
                        
                        # 检查是否在 24 小时内
                        if (datetime.now() - mtime).total_seconds() <= 24 * 3600:
                            # 获取相对路径
                            rel_path = file_path.relative_to(self.workspace_path)
                            recent_files.append({
                                "path": str(rel_path),
                                "mtime": mtime.isoformat(),
                                "size": file_path.stat().st_size
                            })
                    except Exception as e:
                        continue
            
            # 按修改时间排序，最新的在前
            recent_files.sort(key=lambda x: x["mtime"], reverse=True)
            
            return recent_files[:limit]
        except Exception as e:
            print(f"[警告] 获取最近文件失败: {e}")
            return []
    
    def generate_context_summary(self, task_description):
        """生成上下文摘要"""
        current_time = datetime.now().isoformat()
        
        # 获取最近的 git commits
        recent_commits = self.get_recent_git_commits(10)
        
        # 获取最近修改的文件
        recent_files = self.get_recent_files(20)
        
        # 生成建议
        suggestions = []
        if recent_files:
            suggestions.append(f"最近修改了 {len(recent_files)} 个文件，最新的是：{recent_files[0]['path']}")
        if recent_commits:
            suggestions.append(f"最近的 commit：{recent_commits[0]['message']}")
        if "笔记" in task_description or "整理" in task_description:
            suggestions.append("可能需要查看 Notes/ 目录下的文件")
        elif "todo" in task_description.lower() or "任务" in task_description:
            suggestions.append("可能需要查看 .trae/documents/todos管理系统.md")
        elif "plan" in task_description.lower() or "计划" in task_description:
            suggestions.append("可能需要查看 .trae/plans/ 目录下的文件")
        
        context_summary = {
            "timestamp": current_time,
            "task_description": task_description,
            "recent_commits": recent_commits,
            "recent_files": recent_files,
            "suggestions": suggestions
        }
        
        # 记录历史
        self.state["context_history"].append({
            "timestamp": current_time,
            "task_description": task_description
        })
        
        self.state["last_check"] = current_time
        self.state["recent_files"] = recent_files
        self.state["recent_commits"] = recent_commits
        self._save_state()
        
        return context_summary
    
    def format_context_as_text(self, context_summary):
        """将上下文摘要格式化为文本"""
        lines = []
        lines.append("=" * 60)
        lines.append("📝 自动补全上下文")
        lines.append("=" * 60)
        lines.append("")
        
        lines.append(f"任务描述: {context_summary['task_description']}")
        lines.append(f"生成时间: {context_summary['timestamp']}")
        lines.append("")
        
        if context_summary['suggestions']:
            lines.append("💡 上下文建议:")
            for suggestion in context_summary['suggestions']:
                lines.append(f"  - {suggestion}")
            lines.append("")
        
        if context_summary['recent_commits']:
            lines.append("📊 最近 Commits (最近 5 条):")
            for commit in context_summary['recent_commits'][:5]:
                lines.append(f"  - {commit['message']} ({commit['time']})")
            lines.append("")
        
        if context_summary['recent_files']:
            lines.append("📁 最近修改的文件 (最近 10 个):")
            for file_info in context_summary['recent_files'][:10]:
                lines.append(f"  - {file_info['path']} ({file_info['mtime']})")
            lines.append("")
        
        lines.append("=" * 60)
        
        return '\n'.join(lines)


def main():
    """命令行入口"""
    import sys
    
    completer = ContextCompleter()
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "summary":
            if len(sys.argv) < 3:
                print("使用: python context_completer.py summary <task_description>")
                return
            
            task_description = ' '.join(sys.argv[2:])
            context = completer.generate_context_summary(task_description)
            
            # 输出格式化的文本
            print(completer.format_context_as_text(context))
            
        elif command == "commits":
            commits = completer.get_recent_git_commits(10)
            print(json.dumps(commits, ensure_ascii=False, indent=2))
            
        elif command == "files":
            files = completer.get_recent_files(20)
            print(json.dumps(files, ensure_ascii=False, indent=2))
            
        elif command == "status":
            status = {
                "last_check": completer.state.get("last_check"),
                "recent_files_count": len(completer.state.get("recent_files", [])),
                "recent_commits_count": len(completer.state.get("recent_commits", [])),
                "context_history_count": len(completer.state.get("context_history", []))
            }
            print(json.dumps(status, ensure_ascii=False, indent=2))
            
        else:
            print(f"未知命令: {command}")
            print("使用:")
            print("  python context_completer.py summary <task_description>  # 生成上下文摘要")
            print("  python context_completer.py commits                          # 获取最近 commits")
            print("  python context_completer.py files                            # 获取最近文件")
            print("  python context_completer.py status                           # 获取状态")
    else:
        # 默认显示状态
        status = {
            "last_check": completer.state.get("last_check"),
            "recent_files_count": len(completer.state.get("recent_files", [])),
            "recent_commits_count": len(completer.state.get("recent_commits", [])),
            "context_history_count": len(completer.state.get("context_history", []))
        }
        print(json.dumps(status, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
