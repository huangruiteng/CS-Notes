#!/usr/bin/env python3
"""
获取最近 3 天的 memory 文件列表，帮助 AI 提炼原则和最佳实践
"""

import os
from datetime import datetime, timedelta
from pathlib import Path

# 配置
WORKSPACE = Path("/root/.openclaw/workspace")
MEMORY_DIR = WORKSPACE / "memory"

def get_recent_memory_files(days=3):
    """获取最近几天的 memory 文件"""
    if not MEMORY_DIR.exists():
        return []
    
    files = []
    cutoff_date = datetime.now() - timedelta(days=days)
    
    for file in MEMORY_DIR.glob("*.md"):
        try:
            # 从文件名提取日期
            date_str = file.stem
            file_date = datetime.strptime(date_str, "%Y-%m-%d")
            if file_date >= cutoff_date:
                files.append(file)
        except ValueError:
            continue
    
    return sorted(files)

def main():
    print("=" * 60)
    print("📝 最近 3 天的 Memory 文件列表")
    print("=" * 60)
    print()
    
    recent_files = get_recent_memory_files(3)
    
    if not recent_files:
        print("❌ 没有找到最近 3 天的 memory 文件")
        return
    
    print(f"📂 找到 {len(recent_files)} 个最近的 memory 文件：")
    print()
    
    for i, file in enumerate(recent_files, 1):
        print(f"  {i}. {file.name}")
    
    print()
    print("=" * 60)
    print("🤖 请 AI 助手从以上文件中提炼原则和最佳实践到 MEMORY.md")
    print("=" * 60)

if __name__ == "__main__":
    main()
