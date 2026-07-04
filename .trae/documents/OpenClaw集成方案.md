# OpenClaw 集成方案

## 概述

本文档描述如何将 OpenClaw 与本项目的 todos 管理系统集成，实现多渠道任务输入和自动化执行。

## 方案选择：火山引擎 + Lark（飞书）

### 为什么选择火山引擎？

根据最新调研（2026-02），火山引擎是 OpenClaw 部署的最佳选择，原因如下：

1. **适配节奏快**：2026年2月2日后购买的服务器已支持最新版OpenClaw部署
2. **飞书深度协同**：部署模板中预集成了飞书AI助手方案，无需额外复杂配置就能实现飞书接入
3. **安全保障**：火山引擎提供三层纵深安全防护方案
   - 平台安全：访问控制、指令过滤、执行沙箱、技能准入扫描
   - AI助手安全：防范提示词注入、高危操作、敏感信息泄露
   - 供应链安全：Skills深度安全检测
4. **部署便捷**：实测部署耗时约15-25分钟，提供视频教程和数据迁移指南

### 火山引擎安全方案（参考）

火山引擎为OpenClaw提供以下安全保障：
- **入口层**：默认仅绑定本地端口，减少公网暴露面，强制token/密码认证及网关鉴权
- **决策层**：镜像预置提示词加固策略，自动识别并过滤恶意注入指令
- **执行层**：沙箱隔离环境，防止系统破坏
- **准入层**：Skills安全扫描，避免供应链攻击

### 部署方式对比

| 维度 | 本地部署 | 火山引擎部署 |
|------|---------|------------|
| 便捷性 | 需要手动配置 | 预集成模板，15-25分钟完成 |
| 飞书集成 | 需手动配置 | 预集成，开箱即用 |
| 安全性 | 需自行保障 | 三层纵深安全防护 |
| 稳定性 | 受本地设备限制 | 云端稳定运行 |
| 成本 | 免费 | 按需付费（2核2G配置即可） |

**推荐方案**：先本地部署测试功能，验证后再考虑火山引擎云端部署以获得更好的稳定性和安全性。

## OpenClaw 核心能力回顾

### 多渠道 Inbox
- 统一管理 WhatsApp, Telegram, Slack, Discord, Google Chat, Signal, iMessage, Microsoft Teams, Matrix, Zalo, WebChat 等消息渠道
- 支持 Lark（飞书）机器人集成

### 本地优先架构
- 控制平面运行在本地 (`ws://127.0.0.1:18789`)
- 数据隐私优先

### Skill 系统
- 内置技能 (Bundled)
- 托管技能 (Managed) - 从 ClawHub 安装
- 工作区技能 (Workspace) - 用户自定义技能

## 集成架构设计

```
Lark / Telegram / WebChat / ...
         │
         ▼
┌─────────────────────────────┐
│      OpenClaw Gateway       │
│   (ws://127.0.0.1:18789)   │
└──────────────┬──────────────┘
               │
               ├─ Todo Inbox Skill (本项目自定义)
               │   └─ 写入 .trae/documents/INBOX.md
               │
               ├─ Todo Sync Skill
               │   └─ 调用 todo-sync.sh
               │
               └─ 状态同步 Skill
                   └─ 任务状态更新通知
```

## 阶段一：Lark 机器人作为任务输入渠道

### 目标
- 从 Lark 群聊/私聊/机器人接收任务
- 自动结构化成本项目 todo 格式
- 写入 `.trae/documents/INBOX.md`

### 实现方案

#### 1. 创建 OpenClaw Workspace Skill

**位置**: `~/.openclaw/workspace/skills/cs-notes-todo/`

**目录结构**:
```
cs-notes-todo/
├── skill.json
├── main.py
└── README.md
```

#### 2. skill.json 配置

```json
{
  "name": "cs-notes-todo",
  "version": "0.1.0",
  "description": "CS-Notes 项目 Todo 管理 Skill",
  "author": "Your Name",
  "entry": "main.py",
  "capabilities": ["filesystem"]
}
```

#### 3. main.py 实现

```python
#!/usr/bin/env python3
"""
CS-Notes Todo Skill - 接收消息并写入 INBOX.md
"""

import os
from pathlib import Path
from datetime import datetime

REPO_ROOT = Path("/Users/bytedance/CS-Notes")
INBOX_PATH = REPO_ROOT / ".trae/documents/INBOX.md"

def parse_message_to_todo(message: str) -> str:
    """将消息解析为 todo 格式"""
    lines = []
    lines.append(f"- 内容：{message.strip()}")
    lines.append("  - 优先级：medium")
    lines.append("  - 关联文件：")
    lines.append("  - 参考链接：")
    lines.append("  - 截止时间：")
    return "\n".join(lines)

def write_to_inbox(todo_content: str):
    """写入 INBOX.md"""
    INBOX_PATH.parent.mkdir(parents=True, exist_ok=True)
    
    with open(INBOX_PATH, "a", encoding="utf-8") as f:
        f.write("\n")
        f.write(todo_content)
        f.write("\n")

def handle_message(message: str):
    """处理消息"""
    todo = parse_message_to_todo(message)
    write_to_inbox(todo)
    return f"已添加任务到 Inbox: {message[:50]}..."

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        message = " ".join(sys.argv[1:])
        print(handle_message(message))
```

#### 4. Lark 机器人配置

参考 `Notes/AI-Agent-Product&PE.md` 中的飞书机器人配置步骤：

1. 在飞书开放平台创建企业自建应用
2. 添加机器人能力
3. 配置权限（消息读取等）
4. 配置 OpenClaw 与 Lark 的连接

## 阶段二：任务状态同步到 Lark

### 目标
- 任务开始/完成时自动在 Lark 通知
- 支持卡片展示

### 实现方案

通过 OpenClaw 的 `message send` 命令发送通知：

```bash
openclaw message send --to "lark:user_id" --message "任务已完成: xxx"
```

## 阶段三：Skill 包装

### 目标
将本项目 snippets 包装成 OpenClaw Skills：

1. **cs-notes-git-sync Skill**: 接收 Lark 消息，同步到 Git（已创建）
2. **todo-sync Skill**: 调用 `todo-sync.sh`
3. **todo-push Skill**: 调用 `todo-push.sh` 和 `todo-push-commit.sh`
4. **todo-prompt Skill**: 调用 `todo-prompt.py`
5. **todo-manager Skill**: 调用 `todo-manager.py`

### 已创建的 Skill

#### cs-notes-git-sync Skill

**位置**: `.trae/openclaw-skills/cs-notes-git-sync/`

**功能**:
- 接收 Lark 消息并解析为 todo 格式
- 克隆/拉取 CS-Notes 仓库
- 写入 INBOX.md 并自动 commit & push

**使用**:
```bash
python main.py "这是一条测试任务"
```

### 待包装的 Skills

#### todo-sync Skill

**目标**: 调用 `snippets/todo-sync.sh`，从 Git 拉取最新代码并扫描新任务

**目录结构**:
```
cs-notes-todo-sync/
├── skill.json
├── main.py
└── README.md
```

#### todo-push Skill

**目标**: 调用 `snippets/todo-push.sh` 和 `todo-push-commit.sh`，将本地更改推送到 Git

#### todo-prompt Skill

**目标**: 调用 `snippets/todo-prompt.py`，生成任务执行的 prompt

#### todo-manager Skill

**目标**: 调用 `snippets/todo-manager.py`，管理 todos 的状态

## 完整闭环流程设计

### 端到端流程

```
┌─────────────┐
│   用户手机   │
│   (Lark)    │
└──────┬──────┘
       │
       │ 发送任务消息
       ▼
┌───────────────────────┐
│  火山引擎 OpenClaw    │
│  Gateway + Lark Bot   │
└──────┬────────────────┘
       │
       │ cs-notes-git-sync Skill
       │ 1. 解析消息
       │ 2. Git pull
       │ 3. 写入 INBOX.md
       │ 4. Git commit & push
       ▼
┌───────────────────────┐
│     Git 仓库         │
│  (Single Source of    │
│   Truth)              │
└──────┬────────────────┘
       │
       │ Git pull (本地 Mac)
       ▼
┌───────────────────────┐
│   本地 Mac Trae       │
│ 1. todo-sync.sh 扫描   │
│ 2. 执行任务            │
│ 3. 回写进度            │
│ 4. Git commit & push  │
└──────┬────────────────┘
       │
       │ Git pull (火山引擎)
       ▼
┌───────────────────────┐
│  火山引擎 OpenClaw    │
│ 1. 检测到更新         │
│ 2. 通过 Lark 通知用户 │
└──────┬────────────────┘
       │
       │ 任务完成通知
       ▼
┌─────────────┐
│   用户手机   │
│   (Lark)    │
└─────────────┘
```

### 任务状态同步机制

**本地 Mac 端**:
- 任务开始时，通过 `openclaw message send` 发送 "任务开始" 通知
- 任务完成时，发送 "任务完成" 通知，包含执行摘要和产物链接

**火山引擎端**:
- 定期轮询 Git 仓库（或通过 Git webhook）检测更新
- 检测到更新后，解析提交信息，通过 Lark 发送通知

## 快速开始

### 方案一：本地部署（推荐用于测试）

#### 1. 安装 OpenClaw

```bash
npm install -g openclaw@latest
openclaw onboard --install-daemon
```

#### 2. 启动 Gateway

```bash
openclaw gateway --port 18789 --verbose
```

#### 3. 访问 Web 控制台

打开 `http://127.0.0.1:18789`

---

### 方案二：火山引擎云端部署（推荐用于生产）

#### 1. 准备工作

- 注册火山引擎账号：https://www.volcengine.com/
- 准备飞书账号（用于创建机器人）

#### 2. 部署 OpenClaw

1. 登录火山引擎控制台
2. 选择 ECS 云服务器（推荐配置：2核2G内存、40G+系统盘）
3. 选择 OpenClaw 预集成部署模板（2026年2月2日后可用）
4. 按照向导完成配置（约15-25分钟）

#### 3. 配置飞书（零代码方式）

火山引擎预集成模板支持零代码配置飞书：

1. 访问 OpenClaw WebChat 页面
2. 在对话框中输入：`帮我接飞书`
3. 按照 AI 指引完成以下步骤：
   - 创建飞书企业自建应用
   - 获取 App ID 和 App Secret
   - 配置权限（im:message、contact:user.base:readonly等）
   - 配置事件订阅

#### 4. 安全配置（重要）

火山引擎提供的安全配置：
- 确保网关鉴权启用
- 配置访问控制策略
- 启用指令过滤
- 定期进行 Skills 安全扫描

---

## 飞书机器人配置详细步骤（本地部署）

## 相关链接

- OpenClaw GitHub: https://github.com/openclaw/openclaw
- OpenClaw Docs: https://docs.openclaw.ai
- 参考文章: https://mp.weixin.qq.com/s/Mkbbqdvxh-95pVlnLv9Wig
