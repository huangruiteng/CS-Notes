#!/usr/bin/env python3
"""
博主监控脚本 - 优化版
只检查已知能正常工作的RSS feeds
"""

import os
import json
import re
import datetime
from pathlib import Path


class BloggerMonitor:
    """博主监控器"""
    
    def __init__(self):
        self.workspace = Path("/root/.openclaw/workspace/CS-Notes")
        self.state_file = self.workspace / ".trae" / "logs" / "blogger_monitor_state.json"
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        
        # 加载状态
        self.state = self._load_state()
        
        # 可正常工作的博主列表
        self.bloggers = [
            {
                "name": "苏剑林",
                "url": "https://www.kexue.fm/",
                "rss_url": "https://www.kexue.fm/feed",
                "platform": "blog"
            },
            {
                "name": "李新野",
                "url": "https://sinyalee.com/blog/",
                "rss_url": "https://sinyalee.com/blog/feed",
                "platform": "blog"
            }
        ]
    
    def _load_state(self):
        """加载状态"""
        if self.state_file.exists():
            with open(self.state_file, "r", encoding="utf-8") as f:
                return json.load(f)
        return {
            "last_check": None,
            "bloggers": {}
        }
    
    def _save_state(self):
        """保存状态"""
        with open(self.state_file, "w", encoding="utf-8") as f:
            json.dump(self.state, f, ensure_ascii=False, indent=2)
    
    def check_updates(self):
        """检查更新"""
        from urllib.request import urlopen
        from urllib.parse import urljoin
        
        updates = []
        
        for blogger in self.bloggers:
            print(f"\n📝 检查 {blogger['name']}...")
            try:
                with urlopen(blogger['rss_url'], timeout=10) as response:
                    content = response.read().decode("utf-8", errors="ignore")
                    
                    # 解析RSS feed
                    title_match = re.search(
                        r'<item[^>]*>.*?<title>([^<]+)</title>.*?<link>([^<]+)</link>.*?<pubDate>([^<]+)</pubDate>.*?</item>',
                        content,
                        re.DOTALL | re.IGNORECASE
                    )
                    
                    if not title_match:
                        title_match = re.search(
                            r'<entry[^>]*>.*?<title>([^<]+)</title>.*?<link[^>]*href="([^"]+)"[^>]*>.*?<updated>([^<]+)</updated>.*?</entry>',
                            content,
                            re.DOTALL | re.IGNORECASE
                        )
                    
                    if title_match:
                        latest_title = title_match.group(1).strip()
                        latest_url = title_match.group(2).strip()
                        latest_date = title_match.group(3).strip()
                        
                        print(f"   最新文章: {latest_title}")
                        
                        state_key = f"blog_{blogger['url']}"
                        last_title = self.state["bloggers"].get(state_key, {}).get("last_title")
                        
                        if last_title != latest_title:
                            print(f"   🎉 有新更新!")
                            self.state["bloggers"][state_key] = {
                                "last_title": latest_title,
                                "last_checked": datetime.datetime.now().isoformat()
                            }
                            updates.append({
                                "blogger": blogger["name"],
                                "platform": blogger["platform"],
                                "title": latest_title[:100],
                                "url": latest_url if latest_url.startswith("http") else urljoin(blogger["url"], latest_url),
                                "date": latest_date
                            })
                        else:
                            print(f"   ✅ 没有新更新")
                    else:
                        print(f"   ⚠️  无法解析RSS feed")
            except Exception as e:
                print(f"   ❌ 检查失败: {e}")
        
        # 更新最后检查时间
        self.state["last_check"] = datetime.datetime.now().isoformat()
        self._save_state()
        
        return updates


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="优化版博主监控脚本")
    parser.add_argument("--check", action="store_true", help="检查更新")
    parser.add_argument("--status", action="store_true", help="查看状态")
    
    args = parser.parse_args()
    
    monitor = BloggerMonitor()
    
    if args.check:
        print("🔍 检查博主更新...")
        updates = monitor.check_updates()
        
        print(f"\n{'='*50}")
        if updates:
            print(f"🎉 发现 {len(updates)} 个更新!")
            for update in updates:
                print(f"\n  - {update['blogger']}:")
                print(f"    标题: {update['title']}")
                print(f"    链接: {update['url']}")
                if update.get('date'):
                    print(f"    日期: {update['date']}")
        else:
            print("✅ 没有新更新")
        print(f"{'='*50}")
        
    elif args.status:
        print("📊 博主监控状态")
        print(f"  最后检查: {monitor.state.get('last_check')}")
        print(f"  博主列表:")
        for blogger in monitor.bloggers:
            state_key = f"blog_{blogger['url']}"
            state = monitor.state["bloggers"].get(state_key, {})
            print(f"    - {blogger['name']}:")
            if state:
                print(f"      最新文章: {state.get('last_title', 'N/A')}")
                print(f"      最后检查: {state.get('last_checked', 'N/A')}")
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
