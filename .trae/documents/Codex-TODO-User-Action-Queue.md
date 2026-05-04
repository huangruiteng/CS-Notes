# Codex TODO 用户动作队列

> 更新时间：2026-05-04
> 目的：把剩余 `pending` TODO 中 Codex 不能替用户完成的部分，压缩成可执行的下一步动作。这个文件不替代 `.trae/todos/todos.json`，只作为 `推进TODO` 的阻塞面板。

## 当前结论

用户已确认三条旧线降噪：

- OpenClaw Web Manager 不继续搞。
- ECS SSH 随 OpenClaw Web Manager 旧链路归档。
- 公司项目融合暂不考虑，并继续保证不上 git。
- Trae CLI / proactive 内部调研优先级不高，后续默认优先使用 Codex CLI。

用户已完成 `gh auth login`，当前没有 pending 且 `feedback_required=true` 的阻塞任务。

## 1. GitHub 搜索授权（已完成）

对应 TODO：`todo-20260225-016`

当前 Codex 已完成：

- 安装 `gh 2.86.0`。
- 新增 `Notes/snippets/github-search.sh`。
- 新增 `.trae/documents/GitHub-Search-GH-Setup.md`。

已验证命令：

```bash
Notes/snippets/github-search.sh status
Notes/snippets/github-search.sh repos "agent memory llm" 3
```

成功标准：返回合法 JSON。该 TODO 已关闭。

## 2. 已归档旧阻塞项

以下 TODO 已按用户最新判断归档，不再进入用户动作队列：

- `todo-20260219-004`：解决火山引擎 OpenClaw Web Manager 访问问题。
- `todo-20260220-010`：节后解决 ECS 的 SSH 问题。
- `todo-20260219-027`：公司项目 OpenClaw × AI 推荐融合，暂不考虑并保证不上 git。
- `todo-20260223-034039`：公司内部 coding bash CLI 调研。
- `todo-20260225-001`：Trae proactive / CLI 能力调研。

## 3. Trae CLI / proactive 内部调研留档

对应 TODO：

- `todo-20260223-034039`
- `todo-20260225-001`

当前 Codex 已完成：

- 确认本机 `trae` 是 Trae CN App CLI。
- 确认存在 `trae chat --mode agent` 入口。
- 产出 `.trae/documents/Trae-CLI-Proactive-Research-Brief.md`。

当前状态：已归档为背景资料。后续默认优先使用 Codex CLI；除非未来要做 Trae adapter/eval，再重新启用。

如果未来要重启，可把下面这段发给内部相关 owner / 群。

```text
我想调研 Trae 是否有类似 Claude Code / Codex 的 bash/CLI agent 能力，尤其关注是否能被脚本编排、无人值守执行、并输出结构化轨迹。有没有内部文档或 owner 可以请教？

我主要想确认这些点：
1. Trae CLI 的 `trae chat --mode agent <prompt>` 是否支持非交互执行到完成，并以 exit code 表示成功/失败？
2. 是否支持 stdout JSON / streaming event / trajectory 文件 / tool trace / token usage / step summary？
3. 是否能指定 cwd、模型、工具权限、MCP、workspace rules、AGENTS/CLAUDE 类 memory？
4. 是否支持 resume session、session id、后台运行、超时控制、崩溃恢复？
5. 是否有 proactive / daemon / scheduler / background task 能力？
6. 是否支持类似 Claude Code 的 bash + edit + test loop，或更偏 IDE chat？
7. 是否有内部推荐的 CLI agent benchmark 或最佳实践？
8. 如果要把它接入 Agent Harness 做 trace/replay/eval，最稳定的 API/CLI 入口是什么？
```

拿到答复后，Codex 再决定是否新增 `trae_worker_adapter` 设计 TODO。

## 建议解除阻塞顺序

当前无用户阻塞动作。下一轮 `推进TODO` 应先生成新的候选任务，或从近期职业主线中挑一个明确小切口。
