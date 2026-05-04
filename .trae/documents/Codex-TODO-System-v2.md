# Codex TODO System v2

> 迁移目的：把旧 `.trae` 任务系统从“工具链堆叠”演进为适配 Codex 协作的轻量执行协议。本文用于承接一批旧的 `--progress` 流程建设任务，避免继续逐条修补 voice parser、Plan Generator、Hybrid Executor、Todos Web Manager 等老链路。

## 核心判断

旧任务系统的问题不在某个单点功能没做完，而在默认入口和执行语义已经不适合当前协作方式：

- `--progress` 不是清晰状态，很多任务长期介于 in-progress、stale、abandoned 之间。
- voice parser、Plan Generator、Hybrid Executor、Web Manager 彼此耦合，但真实使用中 Codex 对话本身已经成为更强的任务入口。
- “先生成复杂 plan 再执行”的老链路容易制造流程感，却不保证真实产物。
- Web Manager 适合可视化管理，但不应成为 Codex 推进任务的前置依赖；后续只保留 Codex 自用、localhost-only、read-only 的 TODO 控制台。
- 记忆、素材、精读、笔记整理、TODO 推进已经形成新的高频入口，应围绕这些入口收敛。

因此，Codex TODO System v2 的目标不是重建一个大型任务平台，而是让任务推进满足四点：能判断、能落盘、能收敛、能继续。

## 新入口

当前优先保留四类聊天入口：

- `素材：`：进入学习材料候选库，要求保留原始链接、读取状态、分档、摘要和后续动作。
- `整理笔记：`：直接查找合适 Markdown 落点，先看 TOC，再压缩整理。
- `精读` / `读完`：把材料阅读拆成导读、读后笔记、归档、对 agent-harness 的技术 steering。
- `推进TODO`：读取 `.trae/todos/todos.json` 与 `.local/CODEX_TODO_TRIAGE_INDEX.md`，先判断旧任务是否仍服务当前目标，再推进一个小批次。

## 兼容数据源

`.trae/todos/todos.json` 继续保留为兼容数据源，但 Codex 不再机械服从旧字段：

- `status`：保留历史语义，但允许用 `codex_triage` 给出迁移判断。
- `priority`：只作为历史参考，不等价于当前职业主线优先级。
- `assignee`：只区分大致责任，不足以表达 Codex 可做、用户阻塞、环境阻塞、已合并、已过期。
- `progress`：用于写真实推进结果，不写空泛“继续工作”。

新增的 `codex_triage` 是非破坏性元数据，用来表达：

- `merged_into_codex_todo_system_v2`：旧流程建设任务已归并，不再单独推进。
- `user_or_environment_blocked`：需要用户账号、内部环境、权限或主观判断。
- `stale_or_material_flow`：更适合转入素材管线或按需重启。
- `completed_recent_observe`：近期完成，观察后续是否需要自动化。

新增的 `user_next_action` 用来表达阻塞任务的最小用户动作：

- 只写一个下一步，不写路线图。
- 优先写可执行命令、可复制消息、二选一决策或需要贴回的最小信息。
- `feedback_required=true` 的 pending 任务原则上都应有 `user_next_action`，否则会在 triage index 里提示补齐。

新增的 `user_action_rank` 用来表达用户动作队列的真实建议顺序：

- 它可以覆盖旧 `priority`，因为旧 P1/P2 不一定仍服务当前职业主线。
- 排名越小越靠前。
- 当前原则：低成本且能增强主线能力的动作优先，例如 `gh auth login` 高于恢复旧 OpenClaw Web Manager。

## 迁移结论

以下旧方向统一停止逐条续建，合并进 v2：

- OrbitOS 式全能笔记系统：保留“复合工作系统”思想，不追逐不存在或不清晰的外部仓库。
- 自然语言与语音任务输入：保留为未来输入方式，不作为当前默认任务入口。
- Plan Mode 与批量 Review：保留“复杂任务先 plan”的工程习惯，但不维护独立 Plan 状态机。
- 语音消息完整解析：除非用户重新启用手机语音入口，否则不继续做端到端语音链路。
- LLM 优先智能解析：被 Codex 对话入口吸收，不再单独维护解析器。
- Todos Web Manager 融合：不恢复旧大而全前端；只推进 Codex 自用的只读/检查视图，详见 `.trae/documents/Codex-TODO-Web-Manager-v2.md`。
- `voice_task_parser.py` 默认化：停止作为默认任务解析方式。
- Plan Generator + Hybrid Executor 默认链路：停止作为默认执行链路；Codex 直接执行更稳。
- OpenClaw SenseVoice 插件：保留为可选输入能力，不进入当前主线。
- memos 记忆优化：保留“外部记忆库”启发，但当前以 `.local`、材料候选库、归档文件和项目文档为主。

## 执行标准

之后每次 `推进TODO` 应输出：

1. 当前 TODO 系统判断：本轮处理的是真实任务、流程演进、用户阻塞还是归档清理。
2. 选中的 batch：说明为什么这些任务/子切口可以一起推进，为什么现在做。
3. 实际产物：文件、脚本、笔记、状态变更、可运行配置或可转发 steering。
4. 状态回写：只在有真实产物或明确归并结论时更新 `.trae/todos/todos.json`。
5. 下一步：给一个最小后续动作，不堆路线图。

## 批推进协议

`推进TODO` 的默认执行单位应从“一个小任务”升级为“一个小批次”，以贴近 agent-harness 长程任务目标：一次请求内完成 plan -> batch execution -> checkpoint -> replayable record。

默认批量：

- 3-5 个低风险小切口；或
- 1 个主任务 + 2-4 个配套动作，例如文档、脚本、规则、索引、状态回写、转发稿。

批推进的约束：

1. **同目标**：同一批必须服务同一个上层目标，例如 TODO 系统演进、材料库排序、agent-harness steering、AI 热点自动化。
2. **低冲突**：写入范围要么 disjoint，要么属于同一小模块；不能把互相影响很大的重构塞进同一批。
3. **可 checkpoint**：每个子切口都要能说明产物和验证方式。
4. **可降级**：如果遇到权限、公司私密内容、高风险 git 操作或需要用户判断，则把该子切口转为 user-blocked，继续推进批次里其他安全项。
5. **可复盘**：完成后必须刷新 triage index，并在 TODO progress 中记录 batch 做了哪些子切口。

如果本轮只能推进 1 个切口，也可以，但必须说明原因，例如：当前任务高风险、上下文不足、需要用户确认、或只存在一个明确可执行项。

## 空队列协议

当 `.trae/todos/todos.json` 中没有 `pending` / `in-progress` / `--progress` 任务，且没有 `feedback_required=true` 的用户动作时，`推进TODO` 不应为了维持仪式感硬编旧任务。

空队列时按这个顺序找下一批：

1. **复盘近期 completed TODO**：优先看最近 3-5 条完成项，判断是否需要沉淀到 AGENTS.md、skill、脚本、oncall 文档或材料流程。
2. **回到材料/项目状态触发**：查看 `.local/LEARNING_MATERIAL_CANDIDATES.md` 的当前建议阅读顺序、agent-harness 主控反馈、近期笔记状态，找能转成小产物的下一步。
3. **只新增明确小切口**：新 TODO 必须有可验证产物，例如 schema、脚本、文档、转发稿、实验设计或笔记落点；不要新增“继续优化系统”这类空任务。
4. **允许明确报告队列为空**：如果没有真实小切口，应直接告诉用户当前 TODO 队列为空，并给出最小触发条件，例如“读完 S16 后再触发 `读完`”或“agent-harness 有新回复后再推进”。

这条协议的目标是保护 `推进TODO` 的信用：每次推进要么产生真实产物，要么诚实说明没有可推进任务。

## 当前保留的工具

- `Notes/snippets/codex_todo_triage.py`：生成 Codex 视角的 TODO triage index，并可写入 `codex_triage` 元数据。
  - `python3 Notes/snippets/codex_todo_triage.py`：刷新 `.local/CODEX_TODO_TRIAGE_INDEX.md`。
  - `python3 Notes/snippets/codex_todo_triage.py --user-actions`：只打印当前 pending 阻塞任务的用户动作队列。
  - `python3 Notes/snippets/codex_todo_triage.py --next-action`：只打印当前最推荐的一个用户动作，并附带轻量 blocker 检查结果。
  - `python3 Notes/snippets/codex_todo_triage.py --batch-plan`：输出下一轮 `推进TODO` 的推荐批次；如果 active 队列为空，则读取 `.local/LEARNING_MATERIAL_CANDIDATES.md` 的“当前建议阅读顺序”，把前几项材料转成可验证小产物建议。
  - `python3 Notes/snippets/codex_todo_triage.py --check-blockers`：对已知阻塞项做轻量本机检查，例如 `gh auth status`、`trae` CLI、`ssh`、搜索脚本是否可用。
- `.local/CODEX_TODO_TRIAGE_INDEX.md`：本地私有索引，不提交、不公开。
- `.trae/documents/Codex-TODO-User-Action-Queue.md`：剩余 user-blocked TODO 的用户动作队列，把每个阻塞任务压缩成一个命令、一个问题或一个明确选择。
- `Notes/snippets/generate-ai-hotspots-daily.sh` 等 launchd 脚本：作为“可落地自动化任务”的示例。

## 暂不推进

- 不重启旧大而全 Todos Web Manager 前端；只允许推进 Codex 自用的 localhost-only 只读控制台。
- 不继续把 voice parser 作为默认入口。
- 不做 Markdown ↔ JSON 双向同步。
- 不把每个素材、笔记、阅读任务都强行变成 `.trae` TODO。
