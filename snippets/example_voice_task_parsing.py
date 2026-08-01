#!/usr/bin/env python3
"""
示例任务 - 展示如何使用 voice_task_parser.py
让 voice_task_parser.py 真正用起来！
"""

import sys
from pathlib import Path

# 添加父目录到 sys.path，以便导入 voice_task_parser
sys.path.insert(0, str(Path(__file__).parent))

from voice_task_parser import VoiceTaskParser


def example_voice_task_parsing():
    """示例任务 - 展示如何使用 voice_task_parser.py"""
    
    parser = VoiceTaskParser()
    
    print("=" * 60)
    print("🎤 示例任务 - 使用 voice_task_parser.py")
    print("=" * 60)
    print()
    
    # 测试用例
    test_cases = [
        "高优先级：评估 trae-agent 的能力",
        "高优先级：评估 trae-agent 的能力，关联链接 https://github.com/bytedance/trae-agent",
        "高优先级：评估 trae-agent 的能力，明天前完成",
        "高优先级：评估 trae-agent 的能力，关联链接 https://github.com/bytedance/trae-agent，明天前完成",
        "这个很重要，帮我评估一下 trae-agent 的能力",
        "紧急！需要研究 AI Agent 产品，关联这个链接 Notes/AI-Agent-Product&PE.md",
        "慢慢做就行，整理一下笔记，截止到后天",
        "帮我看看这个事情，挺重要的，关联 https://github.com/bytedance/trae-agent，标签：AI, Agent，明天前完成",
        "这是一个非常自然的口述方式，没有固定模板，看看能不能解析"
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"测试用例 {i}:")
        print(f"  输入: {test_case}")
        
        # 先用模板匹配试试
        template_result = parser.parse(test_case)
        
        if template_result["success"]:
            print(f"  ✅ 模板匹配成功: {template_result['template']}")
        else:
            print(f"  ⚠️  模板匹配失败，使用 LLM 智能解析")
        
        # 用综合解析（模板 + LLM）
        result = parser.parse_with_llm(test_case)
        
        print(f"  解析结果:")
        print(f"    优先级: {result['task']['priority']}")
        print(f"    内容: {result['task']['content']}")
        if result['task'].get('tags'):
            print(f"    标签: {', '.join(result['task']['tags'])}")
        if result['task']['links']:
            print(f"    链接: {', '.join(result['task']['links'])}")
        if result['task']['due']:
            print(f"    截止日期: {result['task']['due']}")
        
        print(f"  Todo 格式:")
        print(parser.format_to_todo(result))
        
        print()
        print("-" * 60)
        print()
    
    print("=" * 60)
    print("✅ 示例任务完成！")
    print("=" * 60)


def main():
    """主函数"""
    example_voice_task_parsing()


if __name__ == "__main__":
    main()
