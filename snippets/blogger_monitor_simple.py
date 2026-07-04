#!/usr/bin/env python3
"""
简化版博主监控脚本 - 只检查有手动 RSS feed 的博主
"""

import os
import json
import re
import datetime
from pathlib import Path
from urllib.request import urlopen
from urllib.parse import urljoin


class BloggerMonitorSimple:
    """简化版博主监控器"""
    
    def __init__(self):
        self.workspace = Path("/root/.openclaw/workspace/CS-Notes")
        self.notes_file = self.workspace / "Notes" / "非技术知识.md"
        self.state_file = self.workspace / ".trae" / "logs" / "blogger_monitor_state.json"
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        
        # 博主状态
        self.state = self._load_state()
        
        # 手动添加的 RSS feed 链接映射 - 只检查这些博主
        self.manual_rss_feeds = {
            "苏剑林": "https://www.kexue.fm/feed",
            "Lilian Wang": "https://lilianweng.github.io/feed.xml",
            "EzYang Blog": "https://blog.ezyang.com/feed/",
        }
        
        print(f"✅ 简化版博主监控启动")
        print(f"✅ 将检查 {len(self.manual_rss_feeds)} 个博主")
        print()
    
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
    
    def _check_rss_feed(self, name: str, feed_url: str) -> dict:
        """检查单个 RSS feed"""
        try:
            print(f"📝 检查 {name}...")
            print(f"   链接: {feed_url}")
            
            with urlopen(feed_url, timeout=15) as response:
                content = response.read().decode("utf-8", errors="ignore")
                
                # 简单解析RSS/Atom feed
                # 查找最新的条目
                title_match = re.search(
                    r'<item[^>]*>.*?<title>([^<]+)</title>.*?<link>([^<]+)</link>.*?<pubDate>([^<]+)</pubDate>.*?</item>',
                    content,
                    re.DOTALL | re.IGNORECASE
                )
                
                if not title_match:
                    # 尝试Atom格式
                    title_match = re.search(
                        r'<entry[^>]*>.*?<title>([^<]+)</title>.*?<link[^>]*href="([^"]+)"[^>]*>.*?<updated>([^<]+)</updated>.*?</entry>',
                        content,
                        re.DOTALL | re.IGNORECASE
                    )
                
                if title_match:
                    latest_title = title_match.group(1).strip()
                    latest_url = title_match.group(2).strip()
                    latest_date = title_match.group(3).strip()
                    
                    print(f"   最新文章: {latest_title[:80]}")
                    print(f"   日期: {latest_date}")
                    
                    # 检查是否有新更新
                    state_key = f"blog_{feed_url}"
                    last_title = self.state["bloggers"].get(state_key, {}).get("last_title")
                    
                    if last_title != latest_title:
                        # 有新更新
                        self.state["bloggers"][state_key] = {
                            "last_title": latest_title,
                            "last_checked": datetime.datetime.now().isoformat()
                        }
                        
                        print(f"   🎉 发现新更新！")
                        
                        return {
                            "blogger": name,
                            "platform": "blog",
                            "title": latest_title[:100],
                            "url": latest_url if latest_url.startswith("http") else urljoin(feed_url, latest_url),
                            "date": latest_date
                        }
                    else:
                        print(f"   ✅ 没有新更新")
                        return None
                else:
                    print(f"   ⚠️  无法解析 feed 内容")
                    return None
        except Exception as e:
            print(f"   ❌ 检查失败: {e}")
            return None
    
    def check_updates(self):
        """检查所有博主的更新"""
        updates = []
        
        for name, feed_url in self.manual_rss_feeds.items():
            update = self._check_rss_feed(name, feed_url)
            if update:
                updates.append(update)
            print()
        
        # 更新最后检查时间
        self.state["last_check"] = datetime.datetime.now().isoformat()
        self._save_state()
        
        return updates


def main():
    """主函数"""
    monitor = BloggerMonitorSimple()
    updates = monitor.check_updates()
    
    print()
    print("=" * 60)
    if updates:
        print(f"🎉 发现 {len(updates)} 个更新！")
        for update in updates:
            print(f"  - {update['blogger']}: {update['title']}")
            print(f"    链接: {update['url']}")
    else:
        print("✅ 没有新更新")
    print("=" * 60)


if __name__ == "__main__":
    main()
