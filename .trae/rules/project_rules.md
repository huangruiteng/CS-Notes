# Trae 项目入口

本仓库统一遵循根目录 [AGENTS.md](../../AGENTS.md)，不在此维护第二套笔记、素材或 Git 流程。
若根规则已在当前上下文中，不重复读取；私有补充见 `.local/AGENTS.md`。

- 普通问答、阅读、整理笔记直接处理，不自动创建 TODO，也不调用任务日志器。
- 用户明确推进 TODO 时，`.trae/todos/todos.json` 是任务入口；先标 in-progress，完成产物后回写。
- 只有处理 web-manager / 模板 / 迁移时才读对应 WORKFLOW；区分项目定制与通用模板。
- 不默认读取 OpenClaw 记忆、职业背景或其他仓库。
- 同步使用 sync-notes；删除旧的“完成任何任务立刻 push”和通用 todo-push 默认路径。
