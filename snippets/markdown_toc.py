#!/usr/bin/env python3
"""
Markdown 目录提取工具
用于提取 Markdown 文件的目录层级结构
"""

import sys
import re


def extract_toc(file_path):
    """
    提取 Markdown 文件的目录
    
    Args:
        file_path: Markdown 文件路径
        
    Returns:
        目录列表，每个元素为 (层级, 标题, 行号)
    """
    toc = []
    
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        
    for line_num, line in enumerate(lines, start=1):
        # 匹配标题行
        match = re.match(r'^(#{1,6})\s+(.*)$', line.strip())
        if match:
            level = len(match.group(1))
            title = match.group(2).strip()
            toc.append((level, title, line_num))
            
    return toc


def print_toc(toc):
    """
    打印目录树
    
    Args:
        toc: 目录列表
    """
    if not toc:
        print("未找到标题")
        return
        
    print("目录结构：")
    print("-" * 50)
    
    for level, title, line_num in toc:
        indent = "  " * (level - 1)
        marker = "#" * level
        print(f"{indent}{marker} {title} (line {line_num})")


def main():
    if len(sys.argv) < 2:
        print("用法: python markdown_toc.py <markdown_file>")
        sys.exit(1)
        
    file_path = sys.argv[1]
    
    try:
        toc = extract_toc(file_path)
        print_toc(toc)
    except FileNotFoundError:
        print(f"错误: 文件 {file_path} 不存在")
        sys.exit(1)
    except Exception as e:
        print(f"错误: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
