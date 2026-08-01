# CS-Notes 项目上下文

## 目标
- 知识管理：把零散信息沉淀为可复用、可检索的笔记
- 创作输出：把实验/观察/方法论整理为可分享的文档
- Todo 管理：把想法与任务快速落盘，驱动后续执行
- 新项目建设：在仓库内孵化新的工程/工具/实验
- 效率工具：沉淀脚本、工作流与可重复使用的自动化

## 目录约定
- `Notes/`：长期演进的知识笔记（evergreen）
- `创作/`：面向输出的写作、实验文档与复盘
- `snippets/`：脚本、可复用小工具、实验代码
- `.trae/`：Trae 的规则、上下文与任务系统（用于自动化执行）

## Todo 驱动约定
- 任务统一入口：`.trae/documents/todos管理系统.md`
- 快速收集入口：`.trae/documents/INBOX.md`
- 经验沉淀入口：`.trae/documents/PROGRESS.md`

## 常用操作（给 Trae 的指令习惯）
- “新建任务：……”：写入 Inbox，并补齐优先级/链接/截止时间
- “归档 TODO ARCHIVE 并继续执行 todos”：从 Pending 选取一项执行，产物与复盘回写到任务条目
- “整理进笔记”：优先选择 `Notes/` 中最合适的位置，必要时新建章节
- “写一篇创作”：输出到 `创作/`，并在末尾标注数据、脚本、链接等引用
- “pull” 或 “拉取”：执行 todo-pull.sh，拉取 git、扫描新任务、生成执行提示
- “push” 或 “推送”：执行 todo-push.sh，分析变更、生成 commit message、确认后提交

## Git 同步工作流（自然语言交互）

### Pull（拉取）
- 指令：“pull” 或 “拉取”
- 执行：`./snippets/todo-pull.sh`
- 功能：
  - git pull 最新代码
  - 扫描 Inbox 新任务
  - 生成待执行任务提示清单

### Push（推送）
- 指令：“push” 或 “推送”
- 执行：
  1. `./snippets/todo-push.sh`（生成变更摘要）
  2. AI 分析变更摘要，生成 commit message
  3. 向用户展示：commit message + 变更文件列表
  4. 用户确认后执行：`./snippets/todo-push-commit.sh "<commit-message>"`
- 隐私保护：
  - 仅允许：Notes/、.trae/、创作/
  - 绝对禁止：公司项目/
  - 排除：日志文件、临时文件等

## 验收标准（通用）
- 可追溯：关键结论有引用（链接或文件路径）
- 可复用：重要方法形成模板/清单/脚本
- 可执行：todo 描述清晰且能被拆分、能被验证
