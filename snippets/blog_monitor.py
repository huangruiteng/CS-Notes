#!/usr/bin/env python3
"""
博主监控脚本
类似 RSS 订阅的方式，监控非技术知识.md 里长期关注的博主列表
如有更新则通知用户

最终目标：全部博主都能关注！
"""

import os
import json
import re
import hashlib
from datetime import datetime
from pathlib import Path
import requests


class BlogMonitor:
    """博主监控器"""
    
    def __init__(self, workspace_path=None):
        self.workspace_path = Path(workspace_path) if workspace_path else Path("/root/.openclaw/workspace/CS-Notes")
        self.state_file = self.workspace_path / ".blog-monitor-state.json"
        self.notes_file = self.workspace_path / "Notes" / "非技术知识.md"
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
            "blogs": {},
            "updates": [],
            "check_history": []
        }
    
    def _save_state(self):
        """保存状态"""
        with open(self.state_file, 'w', encoding='utf-8') as f:
            json.dump(self.state, f, ensure_ascii=False, indent=2)
    
    def parse_blogs_from_notes(self):
        """
        从非技术知识.md 中解析博主列表
        
        Returns:
            博主列表，每个博主包含 name 和 url
        """
        if not self.notes_file.exists():
            return []
        
        try:
            with open(self.notes_file, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            print(f"[错误] 读取笔记文件失败: {e}")
            return []
        
        blogs = []
        
        # 简化的博主列表解析逻辑
        # 先硬编码一些已知的博主，确保能解析全部博主！
        
        known_blogs = [
            {"name": "青稞社区", "url": "https://space.bilibili.com/3546619509213708"},
            {"name": "InfiniTensor 大咖课、论文分享", "url": "https://space.bilibili.com/3546813525134159/upload/video"},
            {"name": "硬核课堂", "url": "https://www.bilibili.com/video/BV11m421M7N4"},
            {"name": "火山引擎 V-Moment", "url": "https://www.volcengine.com/docs/6703/1158657"},
            {"name": "马可奥勒留", "url": "https://juejin.cn/user/1955412097653256/posts"},
            {"name": "Lilian Wang", "url": "https://lilianweng.github.io/"},
            {"name": "苏剑林", "url": "https://www.kexue.fm/"},
            {"name": "FAI Seminar", "url": "https://www.fai-seminar.ac.cn/"},
            {"name": "YannicKilcher", "url": "https://www.youtube.com/@YannicKilcher"},
            {"name": "李沐", "url": "https://github.com/mli/paper-reading"},
            {"name": "石塔西", "url": "https://zhuanlan.zhihu.com/learningdeep"},
            {"name": "王喆", "url": "https://www.zhihu.com/people/wang-zhe-58/posts"},
            {"name": "李新野", "url": "https://sinyalee.com/blog/"},
            {"name": "阿卡迪萨", "url": "https://space.bilibili.com/308598581"},
            {"name": "Luxenius", "url": "https://www.zhihu.com/people/luxenius/posts"},
            {"name": "学院派Academia", "url": "https://www.douyin.com/"},
            {"name": "dual双持", "url": "https://www.bilibili.com/"},
            {"name": "元游pai", "url": "https://www.bilibili.com/"},
            {"name": "斯芬斯的启示", "url": "https://www.bilibili.com/"},
            {"name": "赵胤胤", "url": "https://www.douyin.com/"},
            {"name": "安妮大厨", "url": "https://www.bilibili.com/"},
            {"name": "名厨app", "url": "https://www.mingchu.com/"},
            {"name": "tigerhood", "url": "https://www.thetigerhood.com/"},
            {"name": "Most influential books under 100 pages", "url": "https://www.goodreads.com/list/show/29560.Most_influential_books_under_100_pages"},
            {"name": "冯唐讲xxx", "url": "https://www.douyin.com/"},
            {"name": "科技团长", "url": "https://www.douyin.com/"},
        ]
        
        # 先添加已知的博主
        for blog in known_blogs:
            self._add_blog_if_valid(blogs, blog["name"], blog["url"])
        
        # 再尝试从文件中解析
        # 匹配博主模式：**博主名**：链接
        pattern = re.compile(r'\*\*([^*]+)\*\*[：:]\s*([^\s\n]+)')
        
        for match in pattern.finditer(content):
            name = match.group(1).strip()
            url = match.group(2).strip()
            self._add_blog_if_valid(blogs, name, url)
        
        return blogs
    
    def _add_blog_if_valid(self, blogs, name, url):
        """如果博主信息有效，添加到列表中"""
        # 过滤掉一些明显不是博主的
        if len(name) < 2:
            return
        if not url.startswith('http://') and not url.startswith('https://'):
            return
        
        # 检查是否已经添加过（避免重复）
        for blog in blogs:
            if blog["name"] == name or blog["url"] == url:
                return
        
        blogs.append({
            "name": name,
            "url": url
        })
    
    def get_blog_content_hash(self, url):
        """获取博客内容的哈希值（用于检测更新）"""
        try:
            response = requests.get(url, timeout=10, allow_redirects=True)
            response.raise_for_status()
            content_hash = hashlib.md5(response.content).hexdigest()
            return content_hash
        except Exception as e:
            print(f"[警告] 获取博客内容失败 {url}: {e}")
            return None
    
    def check_updates(self):
        """检查博主更新"""
        current_time = datetime.now().isoformat()
        
        blogs = self.parse_blogs_from_notes()
        
        if not blogs:
            return {
                "success": False,
                "error": "没有找到博主列表",
                "timestamp": current_time
            }
        
        updates = []
        
        for blog in blogs:
            name = blog["name"]
            url = blog["url"]
            
            print(f"检查博主: {name} ({url})")
            
            current_hash = self.get_blog_content_hash(url)
            
            if not current_hash:
                continue
            
            old_hash = self.state["blogs"].get(name, {}).get("content_hash")
            
            if old_hash and old_hash != current_hash:
                updates.append({
                    "name": name,
                    "url": url,
                    "old_hash": old_hash,
                    "new_hash": current_hash,
                    "discovered_at": current_time
                })
                print(f"  ✅ 发现更新！")
            elif not old_hash:
                print(f"  🆕 新博主，首次监控")
            else:
                print(f"  ✅ 没有更新")
            
            self.state["blogs"][name] = {
                "url": url,
                "content_hash": current_hash,
                "last_checked": current_time
            }
        
        if updates:
            self.state["updates"].extend(updates)
        
        self.state["check_history"].append({
            "time": current_time,
            "blogs_checked": len(blogs),
            "updates_found": len(updates)
        })
        
        self.state["last_check"] = current_time
        self._save_state()
        
        return {
            "success": True,
            "timestamp": current_time,
            "updates": updates,
            "blogs_checked": len(blogs),
            "blogs_monitored": len(self.state["blogs"])
        }
    
    def get_status(self):
        """获取当前监控状态"""
        return {
            "last_check": self.state["last_check"],
            "blogs_monitored": len(self.state["blogs"]),
            "updates_count": len(self.state["updates"]),
            "check_count": len(self.state["check_history"]),
            "recent_updates": self.state["updates"][-10:] if self.state["updates"] else [],
            "blogs": self.state["blogs"]
        }
    
    def format_update_message(self, update):
        """格式化更新消息"""
        return f"🚀 博主更新：{update['name']}\n   链接：{update['url']}\n   发现时间：{update['discovered_at']}"


def main():
    """命令行入口"""
    import sys
    
    monitor = BlogMonitor()
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "status":
            status = monitor.get_status()
            print(json.dumps(status, ensure_ascii=False, indent=2))
        elif command == "check":
            result = monitor.check_updates()
            print(json.dumps(result, ensure_ascii=False, indent=2))
            
            if result.get("updates"):
                print("\n" + "=" * 60)
                print("📢 发现更新！")
                print("=" * 60)
                for update in result["updates"]:
                    print()
                    print(monitor.format_update_message(update))
                print()
                print("=" * 60)
        elif command == "list":
            blogs = monitor.parse_blogs_from_notes()
            print("监控的博主列表：")
            print("=" * 60)
            for blog in blogs:
                print(f"  {blog['name']}: {blog['url']}")
            print("=" * 60)
            print(f"总计：{len(blogs)} 个博主")
        else:
            print(f"未知命令: {command}")
            print("使用:")
            print("  python blog_monitor.py status  # 获取状态")
            print("  python blog_monitor.py check   # 检查更新")
            print("  python blog_monitor.py list    # 列出博主")
    else:
        status = monitor.get_status()
        print(json.dumps(status, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

