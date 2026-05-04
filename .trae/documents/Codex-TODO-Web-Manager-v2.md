# Codex TODO Web Manager v2

> 目标：只保留 CS-Notes / Codex 自用 TODO 控制台，不再推进火山 OpenClaw Web Manager 访问链路。

## 边界

- **不再推进**：`todo-20260219-004` 火山 OpenClaw Web Manager 访问问题。
- **不再推进**：`todo-20260220-010` ECS SSH 旧前置链路。
- **暂不推进**：`todo-20260219-027` 公司项目融合；Codex 不读取、不写入 `公司项目/`，也不把相关内容带上 git。
- **可以推进**：本仓库自用的 TODO 控制台，用来服务 `推进TODO`、阻塞队列和下一步决策。

## 核心判断

旧 `.trae/web-manager/` 是一个偏完整任务管理站点，但对 Codex 当前协作来说太重，也暴露了几个风险：

- 写接口太多，容易把“看板”变成新的状态源。
- Git / TODO 写操作如果没有 token 和只读模式，默认风险过高。
- 前端功能很多，但 Codex 真正需要的是“下一步做什么”和“哪里被用户阻塞”。
- OpenClaw Web Manager、Todos Web Manager、Codex TODO System v2 曾经混在一起，后续必须分层。

因此 v2 不做大而全的任务系统，只做一个本地只读控制台。

## MVP

### 1. 只读 Dashboard

首页只展示四块：

- TODO 总览：pending / completed / feedback_required 数量。
- Next Action：复用 `python3 Notes/snippets/codex_todo_triage.py --next-action`。
- User Action Queue：复用 `python3 Notes/snippets/codex_todo_triage.py --user-actions`。
- Blocker Checks：复用 `python3 Notes/snippets/codex_todo_triage.py --check-blockers`。

这比完整 CRUD 更符合当前合作模式：Codex 先判断，再推进一个真实小切口。

### 2. 本地优先

默认只能监听本机：

```bash
WEB_MANAGER_HOST=127.0.0.1
WEB_MANAGER_PORT=5000
WEB_MANAGER_DEBUG=0
WEB_MANAGER_READ_ONLY=1
```

不提供公网暴露方案。确实需要局域网访问时，必须先补 token、CORS 白名单、POST 禁用或鉴权。

### 3. 不做默认写接口

MVP 不新增这些能力：

- 不在 UI 里直接改 `.trae/todos/todos.json`。
- 不在 UI 里触发 git commit / push。
- 不读取或展示 `公司项目/`。
- 不把 `.local/` 内容暴露到前端。

需要写操作时仍通过 Codex 对话执行，由 Codex 解释意图、检查 diff、再落盘。

## API Plan

已在 `.trae/web-manager/server.py` 增加只读接口：

```text
GET /api/codex/summary
GET /api/codex/next-action
GET /api/codex/user-actions
GET /api/codex/check-blockers
```

实现方式优先调用或复用：

```bash
python3 Notes/snippets/codex_todo_triage.py --next-action
python3 Notes/snippets/codex_todo_triage.py --user-actions
python3 Notes/snippets/codex_todo_triage.py --check-blockers
```

返回 JSON 时可以先用简单结构：

```json
{
  "ok": true,
  "generated_at": "2026-05-04T03:20:00+08:00",
  "markdown": "..."
}
```

这样前端先渲染 Markdown 文本，后续再结构化成卡片。

实现状态：

- `GET /api/codex/summary`：已实现，直接读取 `.trae/todos/todos.json` 的数量摘要。
- `GET /api/codex/next-action`：已实现，调用 `codex_todo_triage.py --next-action`。
- `GET /api/codex/user-actions`：已实现，调用 `codex_todo_triage.py --user-actions`。
- `GET /api/codex/check-blockers`：已实现，调用 `codex_todo_triage.py --check-blockers`。

## 前端 Plan

已在 `index-enhanced.html` 增加一个 “Codex 控制台” tab：

- `Next`：最高优先级用户动作或 Codex 下一步。
- `Blocked`：当前阻塞检查。
- `Queue`：用户动作队列。
- `Runbook`：链接到本文和 `Codex-TODO-System-v2.md`。

样式保持朴素，不做复杂看板。

实现状态：

- 主导航已增加 `Codex 控制台`。
- 进入该 tab 后隐藏旧筛选、统计和新增任务入口。
- 前端并发请求 `/api/codex/summary`、`/api/codex/next-action`、`/api/codex/user-actions`、`/api/codex/check-blockers`。
- 渲染方式为只读卡片和 Markdown 文本，不提供 TODO 写操作。

## 参考旧文档如何吸收

- `Todos-Web-Manager-本质化结构设计.md`：保留“人需要关注的内容”和“AI 工作流”分离的判断。
- `Todos-Web-Manager-Process-Oncall.md`：保留 localhost/debug off/launchd 脚本，但不急着常驻。
- `WebManager-Public-Port-Security-Review.md`：作为硬边界，默认不公网、不写接口、不无鉴权 Git 操作。

## 下一步

1. 本地启动验证 `http://127.0.0.1:5000` 能看到 Next Action / User Queue / Blocker Checks。
2. 如果稳定，再考虑 launchd 常驻；否则保持按需启动。
3. 若未来需要写操作，先补 `WEB_MANAGER_READ_ONLY=1` 的硬开关和 token，再开放极少量 POST。
