#!/usr/bin/env python3
"""
口述式任务模板解析器
支持自然语言口述任务，自动解析为结构化 todo 格式
包含 LLM 智能解析功能，支持更自然的口述方式
"""

import re
import json
from datetime import datetime, timedelta
from typing import Optional, Dict, Any


class VoiceTaskParser:
    def __init__(self):
        # 定义解析模板（用于快速匹配）
        self.patterns = [
            # 模板一：优先级 + 内容
            {
                "name": "priority_content",
                "regex": r'^(高|中|低)优先级[：:]\s*(.+)$',
                "handler": self._handle_priority_content
            },
            # 模板二：优先级 + 内容 + 链接
            {
                "name": "priority_content_link",
                "regex": r'^(高|中|低)优先级[：:]\s*(.+?)[，,]\s*关联链接\s*(.+)$',
                "handler": self._handle_priority_content_link
            },
            # 模板三：优先级 + 内容 + 截止日期
            {
                "name": "priority_content_due",
                "regex": r'^(高|中|低)优先级[：:]\s*(.+?)[，,]\s*(.+?)前完成$',
                "handler": self._handle_priority_content_due
            },
            # 模板四：完整模板
            {
                "name": "full_template",
                "regex": r'^(高|中|低)优先级[：:]\s*(.+?)[，,]\s*关联链接\s*(.+?)[，,]\s*(.+?)前完成$',
                "handler": self._handle_full_template
            },
            # 模板五：标签 + 内容
            {
                "name": "tag_content",
                "regex": r'^标签[：:]\s*(.+?)[，,]\s*(.+)$',
                "handler": self._handle_tag_content
            },
            # 模板六：优先级 + 标签 + 内容
            {
                "name": "priority_tag_content",
                "regex": r'^(高|中|低)优先级[：:]\s*标签[：:]\s*(.+?)[，,]\s*(.+)$',
                "handler": self._handle_priority_tag_content
            },
            # 模板七：优先级 + 内容 + 标签 + 链接
            {
                "name": "priority_content_tag_link",
                "regex": r'^(高|中|低)优先级[：:]\s*(.+?)[，,]\s*标签[：:]\s*(.+?)[，,]\s*关联链接\s*(.+)$',
                "handler": self._handle_priority_content_tag_link
            }
        ]
    
    def _handle_priority_content(self, match):
        """处理优先级 + 内容"""
        priority_map = {"高": "high", "中": "medium", "低": "low"}
        return {
            "priority": priority_map[match[1]],
            "content": match[2].strip(),
            "links": [],
            "due": None
        }
    
    def _handle_priority_content_link(self, match):
        """处理优先级 + 内容 + 链接"""
        priority_map = {"高": "high", "中": "medium", "低": "low"}
        return {
            "priority": priority_map[match[1]],
            "content": match[2].strip(),
            "links": [match[3].strip()],
            "due": None
        }
    
    def _handle_priority_content_due(self, match):
        """处理优先级 + 内容 + 截止日期"""
        priority_map = {"高": "high", "中": "medium", "低": "low"}
        return {
            "priority": priority_map[match[1]],
            "content": match[2].strip(),
            "links": [],
            "due": self._parse_due_date(match[3].strip())
        }
    
    def _handle_full_template(self, match):
        """处理完整模板"""
        priority_map = {"高": "high", "中": "medium", "低": "low"}
        return {
            "priority": priority_map[match[1]],
            "content": match[2].strip(),
            "links": [match[3].strip()],
            "due": self._parse_due_date(match[4].strip()),
            "tags": []
        }
    
    def _handle_tag_content(self, match):
        """处理标签 + 内容"""
        return {
            "priority": "medium",
            "content": match[2].strip(),
            "links": [],
            "due": None,
            "tags": [t.strip() for t in match[1].split("，")]
        }
    
    def _handle_priority_tag_content(self, match):
        """处理优先级 + 标签 + 内容"""
        priority_map = {"高": "high", "中": "medium", "低": "low"}
        return {
            "priority": priority_map[match[1]],
            "content": match[3].strip(),
            "links": [],
            "due": None,
            "tags": [t.strip() for t in match[2].split("，")]
        }
    
    def _handle_priority_content_tag_link(self, match):
        """处理优先级 + 内容 + 标签 + 链接"""
        priority_map = {"高": "high", "中": "medium", "低": "low"}
        return {
            "priority": priority_map[match[1]],
            "content": match[2].strip(),
            "links": [match[4].strip()],
            "due": None,
            "tags": [t.strip() for t in match[3].split("，")]
        }
    
    def _parse_due_date(self, due_text):
        """解析截止日期"""
        due_text = due_text.strip()
        
        # 今天
        if "今天" in due_text:
            return datetime.now().strftime("%Y-%m-%d")
        
        # 明天
        if "明天" in due_text:
            return (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        
        # 后天
        if "后天" in due_text:
            return (datetime.now() + timedelta(days=2)).strftime("%Y-%m-%d")
        
        # 下周
        if "下周" in due_text:
            return (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")
        
        # 默认返回原文
        return due_text
    
    def parse(self, text):
        """
        解析口述文本
        
        Args:
            text: 口述的文本内容
        
        Returns:
            dict: 结构化的任务信息
        """
        text = text.strip()
        
        # 尝试匹配每个模板
        for pattern in self.patterns:
            match = re.match(pattern["regex"], text)
            if match:
                return {
                    "success": True,
                    "template": pattern["name"],
                    "task": pattern["handler"](match)
                }
        
        # 如果没有匹配到任何模板，返回原始内容
        return {
            "success": False,
            "template": None,
            "task": {
                "priority": "medium",
                "content": text,
                "links": [],
                "due": None
            }
        }
    
    def llm_parse(self, text: str) -> Dict[str, Any]:
        """
        使用 LLM 智能解析口述任务
        
        Args:
            text: 口述的自然语言文本
        
        Returns:
            dict: 结构化的任务信息
        """
        # 这里我们使用一个基于规则的智能解析器作为 LLM 的简化版本
        # 实际使用时可以调用真实的 LLM API
        
        text = text.strip()
        
        # 智能解析优先级
        priority = "medium"
        if "高优先级" in text or "重要" in text or "紧急" in text:
            priority = "high"
        elif "低优先级" in text or "不急" in text or "慢慢" in text:
            priority = "low"
        
        # 智能提取内容
        content = text
        
        # 移除优先级标记
        content = re.sub(r'^(高|中|低)优先级[：:]\s*', '', content)
        content = re.sub(r'^(高|中|低)优先级', '', content)
        content = content.strip()
        
        # 智能提取链接
        links = []
        url_pattern = r'https?://[^\s，,]+'
        urls = re.findall(url_pattern, content)
        if urls:
            links = urls
            # 从内容中移除链接
            for url in urls:
                content = content.replace(url, '')
            content = re.sub(r'[，,]\s*关联链接\s*', '', content)
            content = re.sub(r'关联链接\s*', '', content)
            content = content.strip()
        
        # 智能提取截止日期
        due = None
        due_patterns = [
            r'(.+?)前完成',
            r'(.+?)之前完成',
            r'截止到(.+)',
            r'(.+)截止'
        ]
        
        for pattern in due_patterns:
            match = re.search(pattern, content)
            if match:
                due_text = match.group(1).strip()
                due = self._parse_due_date(due_text)
                # 从内容中移除截止日期
                content = re.sub(pattern, '', content).strip()
                break
        
        # 智能提取标签
        tags = []
        tag_patterns = [
            r'标签[：:]\s*(.+?)[，,]',
            r'标签[：:]\s*(.+?)$',
        ]
        
        for pattern in tag_patterns:
            match = re.search(pattern, content)
            if match:
                tag_text = match.group(1).strip()
                tags = [t.strip() for t in tag_text.split('，')]
                # 从内容中移除标签
                content = re.sub(pattern, '', content).strip()
                break
        
        # 清理内容
        content = re.sub(r'[，,]\s*$', '', content).strip()
        
        return {
            "success": True,
            "template": "llm_intelligent",
            "task": {
                "priority": priority,
                "content": content,
                "links": links,
                "due": due,
                "tags": tags
            }
        }
    
    def parse_with_llm(self, text: str) -> Dict[str, Any]:
        """
        综合解析：先用模板快速匹配，失败后用 LLM 智能解析
        
        Args:
            text: 口述的文本内容
        
        Returns:
            dict: 结构化的任务信息
        """
        # 先用模板快速匹配
        result = self.parse(text)
        
        # 如果模板匹配成功，直接返回
        if result["success"]:
            return result
        
        # 如果模板匹配失败，用 LLM 智能解析
        print(f"⚠️  模板匹配失败，使用 LLM 智能解析...")
        return self.llm_parse(text)
    
    def format_to_todo(self, parsed_task):
        """
        将解析结果格式化为 todo 格式
        
        Args:
            parsed_task: parse() 方法返回的结果
        
        Returns:
            str: Markdown 格式的 todo
        """
        task = parsed_task["task"]
        
        lines = []
        lines.append(f"* [ ] {task['content']}")
        lines.append(f"  - Priority：{task['priority']}")
        lines.append(f"  - Assignee：AI")
        lines.append(f"  - Feedback Required：否")
        
        if task.get("tags"):
            lines.append(f"  - Tags：{', '.join(task['tags'])}")
        
        if task["links"]:
            lines.append(f"  - Links：{', '.join(task['links'])}")
        
        if task["due"]:
            lines.append(f"  - Due：{task['due']}")
        
        return "\n".join(lines)


def main():
    """测试解析器"""
    import sys
    
    parser = VoiceTaskParser()
    
    # 测试用例（模板匹配）
    template_test_cases = [
        "高优先级：评估 trae-agent 的能力",
        "高优先级：评估 trae-agent 的能力，关联链接 https://github.com/bytedance/trae-agent",
        "高优先级：评估 trae-agent 的能力，明天前完成",
        "高优先级：评估 trae-agent 的能力，关联链接 https://github.com/bytedance/trae-agent，明天前完成",
        "标签：AI, Agent，研究 AI Agent 产品",
        "高优先级：标签：AI, Agent，研究 AI Agent 产品",
        "高优先级：研究 AI Agent 产品，标签：AI, Agent，关联链接 Notes/AI-Agent-Product&amp;PE.md",
    ]
    
    # 测试用例（LLM 智能解析 - 更自然的口述方式）
    llm_test_cases = [
        "这个很重要，帮我评估一下 trae-agent 的能力",
        "紧急！需要研究 AI Agent 产品，关联这个链接 Notes/AI-Agent-Product&amp;PE.md",
        "慢慢做就行，整理一下笔记，截止到后天",
        "帮我看看这个事情，挺重要的，关联 https://github.com/bytedance/trae-agent，标签：AI, Agent，明天前完成",
        "这是一个非常自然的口述方式，没有固定模板，看看能不能解析"
    ]
    
    print("=" * 60)
    print("🎤 口述式任务模板解析器 - 测试")
    print("=" * 60)
    print()
    
    # 第一部分：模板匹配测试
    print("📋 第一部分：模板匹配测试")
    print("-" * 60)
    print()
    
    for i, test_case in enumerate(template_test_cases, 1):
        print(f"测试用例 {i}:")
        print(f"  输入: {test_case}")
        
        result = parser.parse(test_case)
        
        if result["success"]:
            print(f"  ✅ 匹配模板: {result['template']}")
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
        else:
            print(f"  ⚠️  未匹配模板")
        
        print()
        print("-" * 60)
        print()
    
    # 第二部分：LLM 智能解析测试
    print()
    print("🧠 第二部分：LLM 智能解析测试")
    print("-" * 60)
    print()
    
    for i, test_case in enumerate(llm_test_cases, 1):
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


if __name__ == "__main__":
    main()

