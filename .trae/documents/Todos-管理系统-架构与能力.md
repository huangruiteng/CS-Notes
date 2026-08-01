# Todos 管理系统 - 架构与能力

## 简介

笔记库的任务管理系统，用于跟踪和管理待办事项。以 Git 为中心的同步架构，结合火山引擎 OpenClaw 和本地 Trae，形成完整的任务执行闭环。

---

## 整体架构设计（火山引擎 + Git 同步方案）

### 核心思路

以 Git 为中心的同步架构，解决火山引擎（云端）与本地 Mac 之间的文件系统隔离问题。

### 三者交互流程

```
┌─────────┐     ┌─────────┐     ┌───────────────┐     ┌─────────┐     ┌───────────────┐
│  手机   │────▶│  Lark   │────▶│  火山引擎     │────▶│  Git    │────▶│  本地 Mac     │
│ (用户)  │     │ (飞书)  │     │  OpenClaw     │     │ 仓库    │     │  (Trae 执行)  │
└─────────┘     └─────────┘     └───────────────┘     └─────────┘     └───────────────┘
     ▲                                                                               │
     │                                                                               │
     └───────────────────────────────────────────────────────────────────────────────┘
                              任务完成通知 (通过 Lark)
```

### 各组件职责

1. **手机端**：
   - 用户通过 Lark（飞书）发送任务消息

2. **Lark 机器人**：
   - 接收手机消息，转发给火山引擎上的 OpenClaw

3. **火山引擎 OpenClaw**：
   - 运行在云端 ECS 上
   - 托管 CS-Notes 仓库的克隆
   - 通过自定义 Skill 接收 Lark 消息
   - 自动 commit & push 到远程 Git 仓库
   - 内置方舟代码模型，可直接执行编码任务

4. **Git 仓库**：
   - 作为唯一的真相源（single source of truth）
   - 同步云端和本地的所有变更

5. **本地 Mac**：
   - Trae 从 Git 拉取最新代码
   - 执行任务，处理代码
   - 执行完成后，commit & push 回远程仓库
   - 火山引擎 OpenClaw 拉取更新，通过 Lark 通知用户任务完成

### 火山引擎部署 vs 本地 Mac 部署的核心区别

| 维度 | 本地部署 | 火山引擎部署 |
|------|---------|------------|
| 文件系统访问 | 直接访问本地文件系统 | 无法直接访问本地 Mac 文件系统，必须通过 Git 同步 |
| 网络架构 | OpenClaw Gateway 运行在 127.0.0.1:18789 | OpenClaw 运行在云端服务器 |
| 飞书集成 | 需要手动配置 | 预集成飞书，零代码配置 |
| 稳定性 | 受 Mac 休眠、关机影响 | 24/7 稳定运行 |

---

## 单一数据源设定（2026-02-19 更新）

**重要：从 2026-02-19 开始，以 JSON 为单一数据源！**

### 唯一数据源

- ✅ `.trae/todos/todos.json` - 主任务文件
- ✅ `.trae/todos/archive/YYYY-MM.json` - 归档任务文件（按月份）

### 不再维护的文件

- ❌ ~~`.trae/documents/todos管理系统.md`~~ - 仅保留设计和提示，不再维护实际 todo 列表
- ❌ ~~`.trae/documents/TODO_ARCHIVE.md`~~ - 仅保留提示，不再维护归档列表

### JSON 数据结构

任务 ID 格式：`todo-YYYYMMDD-XXX`（例如：`todo-20260219-001`）

必需字段：`id`、`title`、`status`、`priority`、`assignee`、`feedback_required`、`created_at`

可选字段：`links`、`definition_of_done`、`progress`、`started_at`、`completed_at`、`dependencies`、`user_requirements`、`deliverables`

---

## OpenClaw + 方舟代码模型一体化方案

### 核心思路

利用 OpenClaw 内置的方舟代码模型直接调用编码能力，结合已有的 `cs-notes-git-sync` skill，形成完整闭环：

```
Lark 发送任务
    ↓
OpenClaw Gateway
    ↓
cs-notes-git-sync skill（写入 INBOX.md）
    ↓
方舟代码模型（执行编码任务）
    ↓
Git commit & push
    ↓
Lark 通知完成
```

### OpenClaw 可用 Skills 清单

**本地工作区中的 Skills**：
- cs-notes-git-sync - Git同步Skill，接收Lark消息并写入INBOX.md
- cs-notes-todo-sync - Todo同步Skill
- plan-generator - Plan生成器
- plan-executor - Plan执行器
- hybrid-executor - 混合执行器
- session-optimizer - 会话优化器
- todo-manager - Todo管理器
- top-lean-ai-monitor - Top Lean AI榜单监控
- trae-agent - Trae Agent集成

**系统内置 Skills**：
- feishu-doc - 飞书文档读写操作
- feishu-drive - 飞书存储空间文件管理
- feishu-perm - 飞书文档和文件权限管理
- feishu-wiki - 飞书知识库导航
- healthcheck - 主机安全加固和风险容忍度配置
- skill-creator - 创建或更新 AgentSkills
- tmux - 远程控制 tmux 会话
- weather - 获取当前天气和预报

---

## 核心概念

### 任务状态

* **Pending**：待处理
* **In Progress**：进行中
* **Completed**：已完成

### 任务字段

* **Assignee**：明确标注任务由谁执行
  * `ai`：由 Trae 自动执行
  * `user`：需要用户亲自操作
  * `user + ai`：用户和AI协作

* **Feedback Required**：是否需要用户反馈/确认
  * `true`：任务执行前/中/后需要用户确认或补充信息
  * `false`：可以直接执行完成

* **Priority**：任务优先级
  * `high`：高优先级，需要尽快完成
  * `medium`：中优先级
  * `low`：低优先级

---

## 目前具备的 Todos 管理能力

### 1. Web 可视化管理

- `.trae/web-manager/index.html` - 基础 Web 界面
- `.trae/web-manager/index-enhanced.html` - 增强版 Web 界面（开发验证面板）
- 支持通过 File API 加载 `.trae/todos/todos.json`
- 支持任务筛选、搜索、排序
- 支持导出任务 JSON
- 开发验证能力：Git 集成、Markdown 解析/生成测试、任务数据验证

### 2. 后端服务

- `.trae/web-manager/server.py` - Flask 后端（Git 集成、任务解析 API）
- `.trae/web-manager/simple-server.py` - 简单 HTTP 服务器（无需 Flask）

### 3. 命令行工具

- `snippets/todo-push.sh` - Git push 标准操作流程
- `snippets/todo-pull.sh` - Git pull 标准操作流程
- `snippets/todo-push-commit.sh` - 带 commit message 的 push 脚本
- `snippets/todo_migrator.py` - Markdown → JSON 迁移工具
- `snippets/todo_sync.py` - JSON→Markdown 同步功能
- `snippets/add_todo_to_json.py` - 添加 todo 到 JSON 的工具

### 4. 任务执行能力

- `snippets/task_executor.py` - Task Executor，支持结构化日志输出、任务状态管理、阶段追踪、产物沉淀、指标计算
- `snippets/blog_monitor.py` - 博主监控脚本
- `snippets/context_completer.py` - 自动补全上下文脚本
- `snippets/speech_to_text.py` - 语音转文字脚本
- `snippets/voice_task_parser.py` - 语音任务解析器

### 5. Plan Mode 能力

- Plan Generator - 生成任务 Plan（目标、假设、改动点、验收标准、风险）
- Plan Executor - 执行 Plan
- Hybrid Executor - 混合执行方式，先生成 Plan，然后先自动执行，再用 AI 自动生成的方式
- `.trae/plans/` - Plan 存储目录

### 6. 会话优化能力

- Session Optimizer - 会话优化器，支持 todo archive 监控等功能

---

## 使用说明

### 任务执行流程（关键！避免冲突）

**重要原则**：多个执行器同时工作时，必须先标记任务为"进行中"，再开始执行。

**标准流程**：

1. **选取任务**：从 Pending 中选择一个任务
2. **原子移动**：将任务从 Pending 移动到 In Progress
3. **开始执行**：执行任务内容
4. **完成标记**：执行完成后，将任务从 In Progress 移动到 Completed

### 执行原则

* **阶段性进展即可**：任务不追求一次完美，有阶段性进展就可以标记完成当前阶段，进入下一阶段
* **小步快跑**：把大任务拆成多个小阶段，每个阶段都有明确的产出
* **快速迭代**：优先实现可用的最小版本，后续再逐步完善
* **自主推进原则**：
  * 只有需要用户做选择题（比如多个 plan 之间选一个），才找用户确认
  * 否则尽量自主推进一切事项

### AI 与用户协作最佳实践

* **主动催促用户执行Todo**：当发现用户是任务执行的重要block点时，必须主动提醒
  - **何时需要催促**：
    - Assignee 为 User 的任务长期处于 Pending 状态
    - 其他任务都依赖该 User 任务才能继续执行
  - **如何催促**：
    - 明确告知用户："这个任务是后续工作的前置条件，需要您先完成"
    - 提供清晰的操作指引
    - 询问是否遇到困难，是否需要帮助

---

## 与 OpenClaw Bot 对话参考

详细的交互指南请参考：`.trae/openclaw-skills/OPENCLAW_BOT_GUIDE.md`

### 常用对话模板

**查询可用 Skills**：
```
你有哪些可用的 Skills？
```

**使用 cs-notes-git-sync 添加任务**：
```
帮我添加一个任务：<任务内容>
优先级：high|medium|low
```

**直接编码**：
```
帮我<编码任务描述>
```

---

## 相关文档

- `.trae/documents/OpenClaw集成方案.md` - OpenClaw 集成方案
- `.trae/documents/Todos-Web-Manager-设计方案.md` - Todos Web Manager 设计方案
- `.trae/documents/Todos-Web-Manager-核心功能实现方案.md` - Todos Web Manager 核心功能实现方案
- `.trae/documents/Todos-Web-Manager-开发验证增强报告.md` - Todos Web Manager 开发验证增强报告
- `.trae/documents/Todos-Web-Manager-部署方案.md` - Todos Web Manager 部署方案
- `.trae/documents/任务执行可观测闭环设计方案.md` - 任务执行可观测闭环设计方案
- `.trae/documents/任务执行可观测闭环-实现方案.md` - 任务执行可观测闭环实现方案
- `.trae/documents/Plan-Mode-混合执行实现方案.md` - Plan Mode 混合执行实现方案
- `.trae/documents/自主推进任务机制优化方案.md` - 自主推进任务机制优化方案
- `.trae/documents/整体仓库架构设计-决策反馈与Plan能力融合.md` - 整体仓库架构设计

---

*最后更新：2026-02-19*
