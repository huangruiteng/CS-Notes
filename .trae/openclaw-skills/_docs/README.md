# OpenClaw Skills for CS-Notes

这是 CS-Notes 项目的 OpenClaw Skills 集合，用于管理 session、监控 Top Lean AI 榜单、管理 todo 任务等。

## Skills 列表

### 1. session-optimizer

Session 优化器 - 监控 session 状态，在需要时提醒用户切换 session。

**功能：**
- Session 状态检查
- 消息数量统计
- 运行时间监控
- 自动警告
- 历史记录

**使用方法：**
```bash
cd /root/.openclaw/workspace/CS-Notes/.trae/openclaw-skills/session-optimizer/scripts/
python3 session-optimizer.py check
```

### 2. top-lean-ai-monitor

Top Lean AI 榜单监控 - 监控 Top Lean AI 榜单的变化，记录更新历史。

**功能：**
- 榜单监控
- 更新记录
- 分析报告

**使用方法：**
```bash
cd /root/.openclaw/workspace/CS-Notes/.trae/openclaw-skills/top-lean-ai-monitor/scripts/
python3 top-lean-ai-monitor.py check
```

### 3. todo-manager

Todo 管理 - 管理 CS-Notes 项目中的 todo 任务。

**功能：**
- Todo 管理
- 优先级管理
- 状态跟踪

**使用方法：**
```bash
cd /root/.openclaw/workspace/CS-Notes/snippets/
python3 todo-manager.py
```

## Git 维护策略

这些 Skills 使用 Git 进行版本控制，存储在 CS-Notes 仓库的 `.trae/openclaw-skills/` 目录下。

通过符号链接连接到 OpenClaw 的 skill 目录：
```
/root/.openclaw/workspace/skills/session-optimizer -> /root/.openclaw/workspace/CS-Notes/.trae/openclaw-skills/session-optimizer
/root/.openclaw/workspace/skills/top-lean-ai-monitor -> /root/.openclaw/workspace/CS-Notes/.trae/openclaw-skills/top-lean-ai-monitor
/root/.openclaw/workspace/skills/todo-manager -> /root/.openclaw/workspace/CS-Notes/.trae/openclaw-skills/todo-manager
```

## Cron Jobs

配置了两个定时任务：

1. **Session Manager Check** - 每 30 分钟运行一次
2. **Top Lean AI Monitor** - 每 6 小时运行一次

## 重要原则

- 基于 OpenClaw 现有能力，不侵入内部代码
- Skills 存储在 CS-Notes 仓库中，使用 Git 版本控制
- 通过符号链接连接到 OpenClaw 的 skill 目录
