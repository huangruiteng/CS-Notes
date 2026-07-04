#!/usr/bin/env python3
"""
测试 Playwright 抓取 GitHub 页面
"""

import asyncio
from playwright.async_api import async_playwright

async def scrape_github():
    """抓取 GitHub 页面"""
    async with async_playwright() as p:
        # 启动浏览器
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        # 访问 GitHub
        print("访问 GitHub...")
        await page.goto("https://github.com", wait_until="networkidle")
        
        # 获取页面标题
        title = await page.title()
        print(f"页面标题: {title}")
        
        # 获取页面内容
        content = await page.content()
        print(f"页面内容长度: {len(content)}")
        
        # 截图
        await page.screenshot(path="/tmp/github-screenshot.png")
        print("截图已保存: /tmp/github-screenshot.png")
        
        await browser.close()
        print("✅ GitHub 页面抓取成功！")

if __name__ == "__main__":
    asyncio.run(scrape_github())
