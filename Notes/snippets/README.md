# Snippets

这个目录放可复用的脚本、prompt 和工作流片段。长期笔记中沉淀出的可执行 prompt，优先在这里保留一份独立入口，方便复制到 Codex / Claude Code / code review 流程中。

## 新增 Snippet 约定

- 可复用脚本、prompt、checklist 放在这里；一次性导出、临时结果和敏感配置不要放这里。
- 新增脚本 / prompt 后，在本 README 加一个入口或模式说明，避免变成隐形资产。
- 命名优先使用功能前缀：`code-reading-*`、`gpu-*`、`codex-*`、`todo-*`、`trusted_*`、`*_checklist.md`。
- 涉及外部服务、飞书、launchd 或本机自动化的脚本，README 中要说明触发场景和边界；账号、token、私有路径留在 `.local/`。
- 新增后至少运行一次 `python3 Notes/snippets/check-snippet-links.py`；脚本类按风险运行 `--help`、dry-run 或语法检查。

## 常用校验

```bash
python3 Notes/snippets/check-snippet-links.py
python3 Notes/snippets/check-learning-material-queue.py
```

- 第一条检查 snippets README / checklist 中的本地链接。
- 第二条检查 `.local/LEARNING_MATERIAL_CANDIDATES.md` 的 Top30 队列编号、残留 Top20 文案和关键保留项。

## Workflow Checklists

- [read-done-closure-checklist.md](read-done-closure-checklist.md)：`读完` 材料后的固定闭环清单，避免漏掉上层同步、归档、主控转发稿和下一步动作。
- [lark-derived-doc-sync-checklist.md](lark-derived-doc-sync-checklist.md)：从本地 canonical section 同步派生飞书文档时的检查清单，覆盖 revision、标题层级、公式/图片和远端校验。

## Workflow Utilities

- [markdown_toc.py](markdown_toc.py)：Markdown heading tree 提取工具，修改长笔记前优先用它定位插入点。
- [codex-persistent-shell.sh](codex-persistent-shell.sh)：需要共享 shell 状态、避免反复加载 `~/.zshrc` 时使用；不要当全局默认。
- [codex-thread-queue.py](codex-thread-queue.py)：Codex App 主控线程 heartbeat / queue 工具，用于 idle guard、launchd preset 和线程续航。
- [codex-goal-pre-tick.py](codex-goal-pre-tick.py)：CS-Notes Goal Harness Layer 的只读 pre-tick 门控；在 goal / heartbeat / 手动自主推进前输出一个推荐动作、门控状态、安全边界和 `.local/ACTIVE_GOAL_STATE.md` 摘要。
- [codex-goal-state.py](codex-goal-state.py)：维护 `.local/ACTIVE_GOAL_STATE.md` 的轻量助手；用于把用户实时反馈、下一步动作和 progress ledger 写回 goal 状态文件。
- [claude-to-im-health.py](claude-to-im-health.py)：检查本机 Lark / claude-to-im bridge、残留 `codex exec` 子进程和近期日志；默认只读，会识别 Codex provider、skill load、Feishu streaming card / WS 异常；确认卡死后再用 `--kill-stale` 或 `--restart-unhealthy` 自愈。
- [codex_todo_triage.py](codex_todo_triage.py)：CS-Notes TODO triage / index 辅助脚本。
- [check-snippet-links.py](check-snippet-links.py)：检查 snippets Markdown 中的本地链接是否仍存在，新增入口后可直接运行。
- [check-learning-material-queue.py](check-learning-material-queue.py)：检查 `.local/LEARNING_MATERIAL_CANDIDATES.md` 的 Top30 队列编号、残留 Top20 文案和关键保留项。
- [todo-pull.sh](todo-pull.sh)、[todo-push.sh](todo-push.sh)、[todo-push-commit.sh](todo-push-commit.sh)：TODO 相关 git 同步脚本，执行前仍要检查 diff 和禁推文件。
- [extract_trusted_material_sources.py](extract_trusted_material_sources.py)：从长期关注来源中抽取 trusted source radar 的候选。
- [trusted_source_scan.py](trusted_source_scan.py)：围绕 trusted sources 做轻量扫描，服务材料探索能力；不要替代具体材料精读。

## Reusable Prompts

- [agent-engineering-quality-prompt.md](agent-engineering-quality-prompt.md)：面向 coding agent 的工程质量约束，覆盖 fail-fast、KISS、DRY、YAGNI、小步可回滚和验证闭环。
- [prompt-openclaw.md](prompt-openclaw.md)：OpenClaw 相关 prompt。
- [code-reading-intro.md](code-reading-intro.md)：代码阅读起步提示。
- [code-reading-trae-agent.md](code-reading-trae-agent.md)：Trae Agent 代码阅读提示。

## Code Reading / Profiling Entrypoints

- `code-reading-*.py|*.md|*.cc`：按项目 / 框架沉淀的源码阅读入口；新增源码阅读材料时优先复用这个命名。
- `gpu-*.py|*.cc|*.sh`、`cpu-profiling.sh`、`nvidia-triton-*.py`：GPU / CPU / Triton profiling 与底层系统实验片段。
