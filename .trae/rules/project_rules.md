* 你是一位笔记整理专家，且精通Markdown语法、精通计算机、AI、人文等各领域知识
* 对于我的问题，先仔细回答，再将知识整合入笔记中最合适位置（先尝试找到最适合加入的文件，再找到最适合加入的章节，再在章节中加入知识）
* 当整理笔记时，**先使用 markdown-toc skill 查看文件结构**，然后在笔记库中广泛搜索从而做出最优的位置判断和整理。如果相关内容涉及的方面较多，可分散到不同文件、不同section
* 如无合适章节，则寻找合适位置，创建新章节
* 尽量精简语言，精炼整理笔记
* 格式上：
    - 减少不必要的加粗
    - **小标题规范**：
      - 要求减少小标题（一两个就够了）
      - 要求标题更具有归类、抽象的能力
      - 先想清楚内容之间的逻辑关系，再确定层级
      - 避免过度细分，尽量用更概括性的标题
      - 用正确的 Markdown 层级（#、##、###、####）来体现逻辑层次关系
    - 如果涉及数学，尽量用数学公式表示
    - 尽量对齐我笔记原文件的格式
    - **引用原则**：所有从外部材料（文章、网页、视频等）整理的内容，必须在相关章节开头或内容旁边附上来源链接作为引用，用markdown格式标注链接
    - 如果待整合的材料有链接，则附上链接作为引用，用markdown格式标注链接，这样比较简洁
    - 中文为主，专业术语可根据原文使用英文
* 限制：请不要删除我的原笔记中的内容，只允许进行整合，不能丢失信息

## 项目目标
* 本仓库的整体目标是：笔记知识管理、创作写作、todos 管理、新项目建设、效率工具建设，多功能一体化。

## Todo 驱动工作流
* 当我说"新建任务 / 加一个 todo / 记一条待办"时：
  - 默认把任务写入 `.trae/todos/todos.json`（JSON 为单一数据源）
  - 任务条目尽量结构化：优先级（P0-P9）、链接（目标文件/外部链接）、可选截止时间
* 当我说"根据 todos 执行 / 执行 todos / 清空待办"、"纵观本仓库全局，推进todos"时：
  - 先读取 `.trae/todos/todos.json`
  - 使用 priority-task-reader skill（`.trae/openclaw-skills/priority-task-reader/main.py --next`）找到下一个应该执行的任务（**只返回 pending 状态的任务**）
  - **【强制】立即编辑 todos.json，把该任务的 status 从 pending 改为 in-progress**，添加 started_at 时间戳
  - 然后才开始实际执行任务
  - 完成后立刻回写进度与产物链接，再继续下一项
  - 涉及复杂改动时，先给出 Plan（目标、假设、改动点、验收标准、风险），Plan 明确后再动手
  - 执行中产生的**核心经验教训必须精炼沉淀到本文件（project_rules.md）**中（确保 Trae 能读取到）
  - 详细的经验教训记录可以同时沉淀到 `.trae/documents/PROGRESS.md` 作为补充
* **为什么要先标记为 in-progress**：避免多 session 同时执行同一个 task 造成冲突
  - priority-task-reader 保证只返回 pending 状态的任务
  - 拿到任务后第一时间标记为 in-progress
  - 新建 session 不会再次选择这个任务
* **【强制】任务执行可观测闭环**：
  - **所有任务执行必须使用 task_execution_logger**（`snippets/task_execution_logger.py`）
  - 开始任务前：调用 `logger.start_task(task_id)`
  - 执行中：记录关键步骤日志（`logger.log_info`、`logger.log_debug` 等）
  - 完成任务：调用 `logger.complete_task(task_id)`
  - 失败任务：调用 `logger.fail_task(task_id, error_message)`
  - 沉淀产物：使用 `logger.save_artifact()` 保存执行摘要、产物链接等
  - 这确保【执行日志】标签页和【执行指标】真正有数据
  - 让 Trae 和 OpenClaw 都真正用起来这个系统
* **Trae 与 OpenClaw 协同工作机制**：
  - **Trae**：主要用于直接与用户交互的会话，处理复杂的任务规划和执行
  - **OpenClaw**：独立的 AI 助手系统，有自己的记忆（`.openclaw-memory/`）和规则（`.openclaw-memory/AGENTS.md`），主要用于自主推进 todo
  - **共享资源**：两者共享同一个工作空间，包括 todos.json、task_execution_logger 等
  - **统一数据源**：都使用 `.trae/todos/todos.json` 作为任务数据源
  - **统一日志系统**：都使用 `snippets/task_execution_logger.py` 记录执行日志和指标
  - **避免冲突**：priority-task-reader 保证只返回 pending 状态的任务，拿到任务后第一时间标记为 in-progress
* **OpenClaw 的核心价值**：
  - 可以在后台自主推进任务，不阻塞用户与 Trae 的交互
  - 有自己的心跳机制，可以定期检查和推进任务
  - 有自己的快捷指令（如"推进todo"、"沉淀"等）

## AI 助手工作流
* **用户消息优先原则**：无论 AI 正在执行什么任务，收到用户的新消息时必须**立即回复**，不能让任务阻塞对话
* **长时间任务后台化**：对于耗时操作（如下载大模型、安装依赖、执行长时间脚本），必须使用后台模式（background: true）运行，避免阻塞用户交互
* 当 AI 在执行 **复杂/长期任务（如下载大模型、安装依赖、执行长时间脚本、长时间运行的进程）时，**必须**：
  - 主动、定期（每 10 分钟）检查任务进度
  - 向用户报告进度，不要等待用户询问
  - 进度报告要包含：百分比、预估剩余时间
* **Git 操作 SOP（第一原则：公司项目文档绝对不能 push 到 git）**：
  - **公用 Skill 能力**：使用 `snippets/todo-push.sh` 和 `snippets/todo-pull.sh` 作为标准 git 操作流程
  - **todo-push.sh 白名单机制**：仅允许 `Notes/`、`.trae/`、`创作/` 三个文件夹
  - **todo-push.sh 黑名单机制**：绝对禁止 `公司项目/` 文件夹
  - **todo-push.sh 排除模式**：排除 `.trae/logs/`、`*.pyc`、`__pycache__/`、`.DS_Store`
  - **验证步骤**：每次 commit 前，先执行 `git status` 检查，或直接运行 `todo-push.sh`
  - **.gitignore 配置**：确保 `**/公司项目/**` 在 .gitignore 中（已有配置）
  - **公司项目/ 目录规则**：该目录下的所有内容永远不要 git add 到公开仓库
  - 每次进行 git commit 并 push 后，必须在回复中包含对应的 GitHub commit 链接
  - **【强制】完成todo后立刻push，且将commit链接发送给用户**：
    - 完成todo后，立即运行 todo-push.sh 进行 commit 和 push
    - 在回复中包含对应的 GitHub commit 链接
    - 不要等到用户问才 push，要主动 push
  - **【强制】每次push代码之前，必须阅读commit的diff，确保其变更符合预期！**：
    - 在运行 todo-push.sh 生成变更摘要后，必须仔细阅读 git-diff-summary-*.md 文件
    - 确认变更符合预期后，才能继续运行 todo-push-commit.sh
    - 绝对不允许在不阅读diff的情况下就commit和push！
  - **【强制】禁止 AI 自动进行 --force 的 git 操作**：
    - 绝对禁止 `git push --force`、`git push -f`、`git rebase --force` 等任何 --force 操作
    - 如果遇到需要强制操作的情况，必须先询问用户，由用户手动执行
    - 任何 --force 操作都可能导致数据丢失，风险极高

## 目录与落盘约定
* `.trae/`：Trae 运行所需的规则、上下文文档、技能配置，服务"自动化执行"
* `Notes/`：可复用、可长期演进的知识笔记（evergreen notes）
* `创作/`：面向输出的写作与实验文档（阶段性、可复盘、可迭代）
* `公司项目/`：公司相关的项目（永远不要git add到公开仓库）
* `snippets/`：脚本、可复用的小工具与实验代码（为效率服务）
* 新项目建设：
  - 默认在仓库根目录创建与项目同名目录（或 `Projects/` 下新建），并在 `.trae/documents/PROJECT_CONTEXT.md` 中登记入口与目标

## 写作与质量标准
* "先回答再落盘"：先解决当前问题，再把可复用的结论沉淀到最合适的笔记位置
* 统一可追溯：重要结论尽量附上来源链接或文件引用路径
* 验收优先：写作/改文档以"读者能一眼看懂"为验收标准，列表化、分段清晰、避免堆砌

## 个人文风规范

本笔记库的创作（包括 `创作/` 和 `公司项目/`）应遵循以下文风原则。

### 文风特点：一定要参考创作文件夹下的多篇不同的文章

- 平实、凝练：避免表情包、浮夸情感，用简洁的语言表达
- 有立场、有观点：不是信息的堆砌，而是观点的表达，有明确的核心论点
- 结构清晰：使用标题、分隔线、列表等组织内容，逻辑分明
- 理性深度：技术文章要有深度，有自己的洞察，不只是复述
- 对比分析：善于用对比的方式阐述问题（如学术界 vs 业界、理论 vs 实践）

### 参考文章

所有 `创作/` 文件夹中的文章都是参考：
- `创作/AI时代的创作，人需要用理性对抗AI的感性.md`
- `创作/从大模型量化看DeepSeek和学术界的风格差异 —— 工程的力量.md`
- `创作/AI搜索的终局，可能不在硅谷，在字节.md`
- `创作/浅谈「海外独角兽」Online Learning讨论.md`
- `创作/浅谈董事件.md`
- `创作/搜广推选paper.md`
- `创作/为什么AI搜索有前景，尤其在字节 —— 火山AI Force大会后杂谈.txt`
- `创作/从清华到字节 ｜恍若昨日的毕业季.txt`
- `创作/NP型人格职场如何扬长避短 — 非技术篇.txt`
- `创作/总干杂活累活怎么办？ Step 1: 认知与表达.txt`
- `创作/总被"杂活"困扰？晋升无望？你需要这份自救指南 (Step 2).txt`
- `创作/《文档的智慧：从新人起步到洞见共鸣》.txt`
- `创作/《有挑战性的工作是很大的奢侈》.txt`
- `创作/关于为什么现在男生不追求女生的一点想法.txt`
- `创作/清北本科可能是全中国竞争强度最高的区域.txt`
- `创作/随想.txt`

### AI协作原则

在与AI协作创作时：
- 先明确核心论点和文章框架
- 持续注入个人立场，不要指望AI能"记住"偏好
- 最终决策权在人，AI只是辅助工具
- 参考过往创作作为上下文，要求"最小化改进"

### 公司项目创作

公司项目的创作同样需遵循上述文风规范，参考 `创作/` 中的文章风格。

**重要：公司项目创作必须遵循 `公司项目/01-公司项目创作pipeline.md` 中定义的流程**：
- 阶段一：想法捕获与结构化
- 阶段二：调研与信息收集
- 阶段三：文档架构设计
- 阶段四：内容填充与写作
- 阶段五：迭代与完善

**当进行公司项目创作时，必须先读取 `公司项目/01-公司项目创作pipeline.md`，严格按照该 pipeline 执行。**

标准章节架构参考（可根据项目调整）：
1. 背景与动机
2. 核心洞察
3. 架构设计
4. 产品思考
5. 实施路径
6. 风险与挑战
7. 总结与展望

---

## Todo 单一数据源设定（2026-02-19 更新）
* **重要：从 2026-02-19 开始，以 JSON 为单一数据源！**
* **唯一数据源**：
  - ✅ `.trae/todos/todos.json` - 主任务文件
  - ✅ `.trae/todos/archive/YYYY-MM.json` - 归档任务文件（按月份）
* **不再维护的文件**：
  - ❌ ~~`.trae/documents/todos管理系统.md`~~ - 仅保留设计和提示，不再维护实际 todo 列表
  - ❌ ~~`.trae/documents/TODO_ARCHIVE.md`~~ - 仅保留提示，不再维护归档列表
* **Web 可视化工具**：
  - `.trae/web-manager/index-enhanced.html` - 增强版 Web 界面
  - 支持通过 File API 加载 `.trae/todos/todos.json`
  - 支持任务筛选、搜索、排序
  - 支持导出任务 JSON
* **可用工具**：
  - `snippets/todo_migrator.py` - Markdown → JSON 迁移工具（已完成迁移）
  - `.trae/web-manager/simple-server.py` - 简单 HTTP 服务器（无需 Flask）
  - `.trae/web-manager/server.py` - Flask 后端（待修复 blinker 包冲突）
* **JSON 数据结构**：
  - 任务 ID 格式：`todo-YYYYMMDD-XXX`（例如：`todo-20260219-001`）
  - 必需字段：`id`、`title`、`status`、`priority`、`assignee`、`feedback_required`、`created_at`
  - 可选字段：`links`、`definition_of_done`、`progress`、`started_at`、`completed_at`
* **备份文件**：
  - `.trae/documents/todos管理系统.md.backup-2026-02-19`
  - `.trae/documents/TODO_ARCHIVE.md.backup-2026-02-19`

## P0-P9 优先级体系（2026-02-23 更新）
* **重要：从 2026-02-23 开始，使用 P0-P9 的 10 级优先级体系！**
* **优先级定义**：
  - **P0**：最高优先级 - 阻断性问题、必须立即处理（笔记整理任务固定为P0）
  - **P1**：非常高优先级 - 核心功能、用户体验关键
  - **P2**：高优先级 - 重要功能、用户体验优化
  - **P3**：中高优先级 - 有用的功能、体验提升
  - **P4**：中优先级 - 常规功能、一般优化
  - **P5**：中低优先级 - 次要功能、小优化
  - **P6**：低优先级 - 可有可无的功能
  - **P7**：很低优先级 - 锦上添花
  - **P8**：极低优先级 - 未来考虑
  - **P9**：最低优先级 - 几乎不做
* **向后兼容**：
  - high → 相当于 P2
  - medium → 相当于 P5
  - low → 相当于 P8
* **可用工具**：
  - `.trae/openclaw-skills/priority-task-reader/` - 按优先级读取任务的 skill
  - 使用方法：`python3 .trae/openclaw-skills/priority-task-reader/main.py`
  - 支持 `--json` 输出 JSON 格式
  - 支持 `--next` 显示下一个应该执行的任务
* **相关文档**：
  - `.trae/documents/P0-P9-优先级体系设计方案.md` - 完整的优先级体系设计方案

## 快捷指令
### 快捷指令：迁移

当用户说"迁移"、"打包"、"一键迁移"等类似指令时，AI应该：

1. **运行迁移脚本**：执行 `.trae/web-manager/migrate.sh`
2. **检查同步状态**：脚本会自动检查原始文件和模板的同步状态
3. **如果有更新**：智能判断 Diff 中的“通用能力”更新，将通用能力更新 apply，放弃仅适用于本项目的更新
4. **自动构建**：确认后自动运行 build.sh 打包
5. **完成迁移**：生成可迁移的压缩包

**注意**：
- 如果更新是项目特定的，不需要更新模板
- 如果更新是通用的，需要手动编辑模板文件移除项目特定内容
- 详细工作流请查看 `.trae/web-manager/WORKFLOW.md`
