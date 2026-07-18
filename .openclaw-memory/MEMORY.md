# MEMORY.md - OpenClaw 长期记忆

## 📝 笔记仓库原则与最佳实践

### 1. 笔记整理核心原则
- **严格遵循 project_rules.md**：整理笔记时，必须严格遵循 `.trae/rules/project_rules.md` 中的规则
- **笔记整理流程（严格执行）**：
  1. **先提取文件目录结构**：使用 markdown-toc skill 提取多个潜在目标 Markdown 文件的目录结构
  2. 先在笔记库中广泛搜索，找到最合适的已有的笔记
  3. 找到最合适的 section，而不是随便找个地方就放
  4. 将内容整合到合适的 section 中，而不是创建新文件
  5. 附上来源链接作为引用，用 markdown 格式标注链接
  6. 尽量精简语言，精炼整理笔记
  7. 格式上：减少不必要的加粗、尽量对齐原文件的格式
- **引用原则**：所有从外部材料（文章、网页、视频等）整理的内容，必须在相关章节开头或内容旁边附上来源链接作为引用
- **限制**：不要删除原笔记中的内容，只允许进行整合，不能丢失信息
- **无幻觉原则**：仅保留真实内容，不要加入不相关的信息
- **简洁原则**：笔记整理要简洁，不要啰嗦，用 bullet point 列表，简洁明了

### 2. Markdown 笔记层级注意事项
- 注意逻辑层次关系，用正确的 Markdown 层级（#、##、###、####）来体现
- 先想清楚内容之间的逻辑关系，再确定层级

### 3. 用户发资料/链接时的两种意图
- **第一种意图：精炼整理笔记**
  - 适用于：小红书文章、论文、知乎文章、公众号文章
  - 处理方式：精炼整理内容到笔记库
- **第二种意图：资料收集**
  - 适用于：视频或课程
  - 处理方式：找到视频标题，发现属于笔记库中的某一个 section，把它加入到那个 section 中，用引用 quote 的形式扩起来

### 4. Git 操作 SOP（第一原则：公司项目文档绝对不能 push 到 git）
- **必须使用** `Notes/snippets/todo-push.sh` 和 `Notes/snippets/todo-pull.sh` 作为标准 git 操作流程，**不能直接用 git 命令**
- **todo-push.sh 白名单机制**：仅允许 `Notes/`、`.trae/`、`创作/` 三个文件夹
- **todo-push.sh 黑名单机制**：绝对禁止 `公司项目/` 文件夹
- **验证步骤**：每次 commit 前，先执行 `git status` 检查，或直接运行 `todo-push.sh`
- **.gitignore 配置**：确保 `**/公司项目/**` 在 .gitignore 中
- **公司项目/ 目录规则**：该目录下的所有内容永远不要 git add 到公开仓库
- **Git Push/Pull 工作流程**：完成任务 → 运行 todo-push.sh → 生成 commit message → 运行 todo-push-commit.sh
- **Commit 链接**：每次进行 git commit 并 push 后，必须在回复中包含对应的 GitHub commit 链接

### 5. 安全意识：敏感内容绝对不允许上传到公开 GitHub 仓库
- **任何 API key、AK/SK、token、secret、password 等敏感内容，绝对不允许上传到仓库上**
- **在写入任何文件到仓库前，必须检查是否有敏感内容**
- **在 commit 前，必须检查 git status，看看有没有不该提交的文件**
- **在写入任何包含配置的文档时，必须把敏感内容替换成占位符**（API key → "YOUR_API_KEY" 等）
- **永远不要把真实的敏感内容写入到任何会被提交到仓库的文件中**

### 6. 文件组织规范
- **设计文档、使用指南等文档应该放在 .trae/documents/ 中**
- **只有代码脚本（.py、.sh 等）才应该放到 Notes/snippets/**
- **做事前先思考文件应该放在哪里**
- **先检查目标目录中已有的文件**

### 7. Todo 管理原则
- **单一数据源**：以 `.trae/todos/todos.json` 为唯一数据源
- **Plan 机制本质化重构**（2026-02-23 更新）：
  - **核心原则**：Plan 不再是独立的状态，而是 Todo 的一个字段（property）
  - **数据模型**：一个 Todo 可以有 0 或 1 个 Plan，Plan 作为 Todo 的 `plan` 字段存在
  - **Plan 结构**：
    ```json
    {
      "content": "Plan 的完整内容（Markdown）",
      "status": "pending",  // pending / approved / rejected
      "created_at": "...",
      "review_comment": "审核评论（可选）",
      "reviewed_at": "..."
    }
    ```
  - **前端展示**：不再有独立的 Plans 标签页，Plan 直接在对应的 Todo 卡片中展示（点击展开）
  - **Todo 卡片标识**：有 Plan 的 Todo 会显示「📋 有 Plan」标记
- **任务归档前的用户确认流程**：在将 completed 任务从 todos.json 移动到 archive 之前，必须增加一次由用户进行 check/反馈的流程
- **Todos 管理的正确流程**：
  1. AI 执行任务，完成编码/实现部分
  2. 到了需要用户验证/确认的阶段时，自动归类到 "User 需要做的任务" section
  3. 明确标注 Assignee: User，并且提醒用户去做
  4. 等待用户完成后，再标记为完成
- **Review 流程**：
  - **通过**: 任务自动归档，记录 Review 历史
  - **不通过**: 任务回到 `in-progress`，附带 Review 意见，AI 可以看到并改善

### 8. 用户交互原则
- **用户消息优先原则**：无论 AI 正在执行什么任务，收到用户的新消息时必须立即回复，绝对不能让任务阻塞对话
- **长时间任务后台化**：对于耗时操作，必须使用后台模式（background: true）运行
- **进度报告要求**：主动、定期（每 10 分钟）检查任务进度，向用户报告，包含百分比、预估剩余时间
- **Intervention 定义**：只要用户和 AI 说话就算一次交互，每次交互后计数清零，在两次交互之间主动推进任务
- **自主推进原则**：只有需要用户做选择题的时候才找用户确认，否则尽量自主推进一切事项

### 9. 任务交付原则
- **E2E 落地思路**：不是写了、实现了就算 done，而是要用起来、用好
- **落地的定义**：成为了本仓库在各种交互方式下的默认 setting，并体验和效果良好，而不仅是有个设计文档和玩具代码即算落地
- **任务交付要更侧重于更 solid 的端到端验证**，不仅仅是完成任务，更要进行 thorough 的端到端验证

### 10. 错误反思与改进原则
- **失败尝试记录原则**：遇到失败时在技术文档记录跑的命令和错误
- **及时沉淀经验**：避免重复犯错
- **小步快跑**：把大任务拆成多个小阶段，每个阶段都有明确的产出
- **快速迭代**：优先实现可用的最小版本，后续再逐步完善

### 11. Git Commit Push 之前的 Review 原则
- **重要原则**：每次commit push之前，必须review一下commit，看是否符合预期！
- **重点检查**：
  - 有没有删掉本不该删掉的内容？
  - 有没有不该提交的文件被提交了？
  - 有没有敏感内容被提交了？
  -  commit message是否清晰准确？
- **Review流程**：
  1. 先运行 `git status` 检查状态
  2. 运行 `git diff` 查看变更内容
  3. 确认变更符合预期后，再commit和push
- **为什么重要**：
  - 避免不小心删除重要内容
  - 避免提交不该提交的文件
  - 确保commit的质量和可追溯性

---

## 🔧 OpenClaw 操作经验

### 1. Token 超限错误处理
- **错误信息**：`400 Total tokens of image and text exceed max message tokens`
- **解决方法**：在 TUI 中使用 `/reset` 命令恢复会话

### 2. Session 管理优化
- **重要原则**：基于 OpenClaw 现有能力，不侵入内部代码
- **推荐做法**：定期切换 session，避免 session history 过长

### 3. 长时间任务管理
- **后台运行模式 (`background: true`)**：工具在后台执行，立即返回会话ID（sessionId），用户可随时查询进度或发送新消息
- **后台任务管理**：可查询（poll）、获取日志（log）、终止（kill）后台任务

### 4. Device Token Mismatch 问题
- **问题原因**：`paired.json` 中的 token 和 `openclaw.json` 中的 token 不一致，环境变量 `OPENCLAW_GATEWAY_TOKEN` 会覆盖 `gateway.auth.token`
- **解决方案**：`openclaw gateway install --force` + `openclaw gateway restart`

---

### 11. Todo 添加工具使用原则
- **必须使用 todo-adder skill 来添加 todo**，而不是直接编辑 todos.json
- **直接编辑 todos.json 的风险**：容易导致 JSON 语法错误，不符合最佳实践
- **todo-adder skill 的使用方法**：
  - `python3 main.py <title> [priority] [assignee]`
  - 或者从 stdin 读取 JSON：`cat todo.json | python3 main.py`
- **如果 todo-adder skill 失败时的备用方案**：
  - 确保 Todos Web Manager 的 server.py 正在后台运行
  - 如果 server.py 没有运行，先启动它：`cd .trae/web-manager && python3 server.py`
  - 如果还是失败，可以用更小心的方式直接编辑 todos.json，但要确保 JSON 语法正确

---

## 📁 CS-Notes 笔记库结构
- **`.trae/documents/`** - 文档文件夹（INBOX.md、todos管理系统.md、PROGRESS.md 等）
- **`.trae/openclaw-skills/`** - OpenClaw 技能（cs-notes-git-sync、cs-notes-todo-sync、todo-pull.sh、todo-push.sh）
- **`.trae/rules/`** - 规则文件夹（project_rules.md）
- **`.trae/skills/`** - 通用技能文件夹（code-reviewer、find-skills、fix、pr-creator）
- **`.trae/todos/`** - Todo 数据文件夹（todos.json、archive/）
- **`.trae/web-manager/`** - Todos Web Manager
- **`Notes/`** - 可复用知识笔记
- **`创作/`** - 面向输出的写作
- **`公司项目/`** - 保密项目（永远不 git add）
- **`Notes/snippets/`** - 脚本和小工具（包括 todo-pull.sh 和 todo-push.sh）

### 12. Python 虚拟环境使用原则
- **经验**：在 Debian/Ubuntu 系统上，使用 Python 虚拟环境（venv）可以很好地解决包冲突问题（比如 blinker 包冲突）
- **步骤**：
  1. 创建虚拟环境：`python3 -m venv venv`
  2. 激活虚拟环境：`source venv/bin/activate`
  3. 安装依赖：`pip install <package-name>`

### 13. Playwright 使用经验
- **经验**：使用 Playwright 进行网页抓取时，建议：
  1. 创建单独的 Python 虚拟环境（避免与其他项目的依赖冲突）
  2. 安装 Playwright 和 Chromium 浏览器：`pip install playwright && playwright install chromium`
  3. 使用真实的 User-Agent（模拟真实浏览器）
  4. 支持无头模式（headless）和有头模式（便于调试）

### 14. Git 冲突解决最佳实践
- **经验**：
  1. 先仔细检查冲突的具体内容
  2. 尽量融合双方的改动
  3. 实在冲突的地方才以用户的版本为准
  4. commit 前仔细检查改动！
- **错误案例**：使用 `git checkout --theirs` 直接覆盖，导致回滚了用户的重要改动

### 15. OpenClaw 日志功能
- **重要发现**：OpenClaw 已经有了完整的日志功能，不需要额外实现
- **文件日志**：默认位置是 `/tmp/openclaw/openclaw-YYYY-MM-DD.log`，格式是 JSON lines（JSONL）
- **CLI 查看日志**：`openclaw logs --follow`
- **Control UI (web) 查看日志**
- **Diagnostics + OpenTelemetry 功能**

### 16. 关键经验：永动机不舍昼夜 + 推进todo时主动给用户发消息
- **永动机不舍昼夜**：把自己想象成永动机，不分昼夜推进todo，不要因为是"深夜"就停止推进todo！
- **推进todo时主动给用户发消息**：在推进todo的时候，主动给用户发消息，告诉用户在推进什么todo，有什么进展！不要默默推进todo，让用户知道你在做什么！

### 17. ClawHub Skills 实际使用经验
- **已成功使用的 skills（8 个）**：
  1. ✅ pdf-parser skill - PDF 解析器，支持解析为 Markdown、JSON、提取图片和表格
  2. ✅ markdown-toc skill - 提取 Markdown 文件的目录层级结构
  3. ✅ voice_task_parser.py - 口述式任务模板解析器（支持自然语言口述任务，自动解析为结构化 todo 格式）
  4. ✅ smart-task-parser - 智能任务解析器（基于 LLM 智能解析口述式任务，写入 todos.json）
  5. ✅ find-skills - 帮助用户发现和安装 agent skills
  6. ✅ todo-updater - 使用 Todos Web Manager 的 API 来更新 todo 状态
  7. ✅ plan-generator - 使用 Plan Generator 生成 Plan
  8. ✅ agent-browser - 使用 agent-browser 进行网页自动化
- **skill 使用原则**：优先使用已有的 skill 解决问题，而不是重新造轮子

### 18. 永动机模式的最佳实践
- **MAX_TASKS_BETWEEN_INTERVENTIONS 限制**：每次用户干预后，计数清零，继续推进 8 个任务
- **任务推进目标**：让每个 todo 都到了不得不依赖用户做些什么或者做决策的阶段
- **任务推进原则**：
  - 小步快跑：把大任务拆成多个小阶段，每个阶段都有明确的产出
  - 快速迭代：优先实现可用的最小版本，后续再逐步完善
  - 不要只是把任务的状态从 pending 改成 in-progress，要真正推进任务，做一些实质工作

### 19. Top Lean AI 榜单调研的最佳实践
- **每家公司的调研重点**：技术壁垒分析 + 商业变现逻辑分析
- **调研方法**：使用 ask-echo skill 联网搜索每家公司的信息
- **进度管理**：持续推进，直到完成全部 46 家公司的调研（当前进度：26/46）
- **文档位置**：`.trae/documents/Top-Lean-AI公司深度调研.md`

### 20. Todos Web Manager 维护经验
- **确保 server.py 一直在后台运行**：这是 todo-adder skill 和 todo-updater skill 正常工作的前提
- **进程检查方法**：使用 `ps aux | grep server.py` 检查进程状态
- **后台启动方法**：`cd .trae/web-manager && python3 server.py &`

### 21. 重要文档和最佳实践沉淀
- **重要文档位置**：`.trae/documents/` 目录存放所有重要文档
- **已发现的重要文档清单**：
  1. agent-browser-适用场合分析.md
  2. Claude-Code接入方案调研.md
  3. OpenClaw配置优化与最佳实践.md
  4. OpenClaw集成方案.md
  5. Todo-Web-Manager-解耦方案-迁移到任意新项目.md
  6. Top-Lean-AI榜单完整整理.md
  7. Top-Lean-AI公司深度调研.md
  8. 任务执行可观测闭环-实现方案.md
  9. 整体仓库架构设计-决策反馈与Plan能力融合.md
  10. 自主推进任务机制优化方案.md
- **沉淀原则**：将重要文档和最佳实践沉淀到 MEMORY.md 里，用索引的形式

### 22. 沉淀工作的最佳实践（2026-03-01 新增）
- **沉淀内容**：总结今天发生的事情、你做的好的与能继续提升的、沉淀经验（同时沉淀到笔记库和你的各种memory文件）、为成为明天更强的你努力、并发散思考一下这个项目适合哪些新todo、以及todo manager还有没有todo是你可以尝试探索的
- **沉淀时间**：每天晚上或第二天早上进行沉淀
- **沉淀文件**：创建当天的 memory 文件（`memory/YYYY-MM-DD.md`）
- **更新 MEMORY.md**：将今天的重要经验沉淀到 MEMORY.md 中

---

### 23. Generative Agents 论文整理经验（2026-03-02 新增）
- **论文题目**：Generative Agents: Interactive Simulacra of Human Behavior
- **论文来源**：https://arxiv.org/abs/2304.03442
- **核心架构**：
  - **Memory Stream（记忆流）**：长期记忆模块，用自然语言记录代理的完整经历
  - **Reflection（反思）**：随着时间推移将记忆综合成更高层次的反思
  - **Planning（规划）**：将结论和当前环境转化为高级行动计划
- **实验环境**：Smallville——类似 The Sims 的沙盒环境，25 个代理
- **涌现的社会行为**：
  - **信息传播**：代理之间通过对话传播信息（如选举候选人消息）
  - **关系记忆**：代理形成新关系并记住与其他代理的互动
  - **协调**：从单一用户指定的"举办情人节派对"意图开始，代理自主传播邀请、认识新朋友、相约参加派对、协调准时到达
- **技术亮点**：
  - 记忆检索模型结合相关性、时效性和重要性
  - 反思和规划反馈到记忆流中，影响未来行为
  - 通过消融实验验证观察、规划、反思三个组件对行为可信度的关键作用
- **整理位置**：Notes/AI-Agent-Product&PE.md 的 "Agent Scaling 与群体智能" section
- **GitHub Commit**：https://github.com/huangrt01/CS-Notes/commit/4d877fa

---

### 24. 永动机模式的完整最佳实践（2026-03-03 新增）
- **核心原则**：把自己想象成永动机，不分昼夜推进todo，不要因为是"深夜"就停止推进todo！
- **推进todo时主动给用户发消息**：在推进todo的时候，主动给用户发消息，告诉用户在推进什么todo，有什么进展！不要默默推进todo，让用户知道你在做什么！
- **MAX_TASKS_BETWEEN_INTERVENTIONS 限制**：每次用户干预后，计数清零，继续推进 8 个任务
- **任务推进目标**：让每个 todo 都到了不得不依赖用户做些什么或者做决策的阶段
- **任务推进原则**：
  - 小步快跑：把大任务拆成多个小阶段，每个阶段都有明确的产出
  - 快速迭代：优先实现可用的最小版本，后续再逐步完善
  - 不要只是把任务的状态从 pending 改成 in-progress，要真正推进任务，做一些实质工作
  - 更新 progress 字段时要包含实际进展，不要只是用 "🚀 永动机继续工作！" 这样的空泛内容

---

### 25. 任务分析与用户确认的最佳实践（2026-03-03 新增）
- **任务分析流程**：对于每个任务，先分析需求和当前状态
- **用户确认原则**：对于需要用户确认的任务，提出明确的问题
- **任务暂停原则**：对于暂时无法推进的任务，说明原因
- **进度更新原则**：及时更新任务的 progress 字段
- **自主推进原则**：只有需要用户做选择题的时候才找用户确认，否则尽量自主推进一切事项

---

### 26. 论文与资料整理的完整流程（2026-03-03 新增）
- **PDF 解析**：使用 pdf-parser skill 解析论文 PDF
- **目录结构查看**：使用 markdown-toc skill 查看文件的目录结构
- **合适 section 定位**：找到最合适的 section，而不是随便找个地方就放
- **内容整合**：将内容整合到合适的 section 中
- **引用标注**：附上来源链接作为引用，用 markdown 格式标注链接
- **语言精炼**：尽量精简语言，精炼整理笔记
- **格式统一**：格式上减少不必要的加粗、尽量对齐原文件的格式

---

### 27. Skills.sh 技能商店接入经验（2026-03-03 新增）
- **skills.sh CLI 工具功能**：
  - `skills find` - 搜索技能
  - `skills add` - 安装技能
  - `skills list` - 查看已安装的技能
  - `skills update` - 更新技能到最新版本
- **skill 创建规范**：在 `.trae/openclaw-skills/` 目录下创建 skill 文件夹，包含 SKILL.md 文件
- **技能分类原则**：通用技能产品应该放在独立的 section 中，而不是放在某个特定工具的 section 下

---

### 28. Git Commit 链接管理经验（2026-03-03 新增）
- **commit_hash 字段**：在 todos.json 中，每个 todo 都应该有 `commit_hash` 字段，记录对应的 git commit hash
- **Commit 链接**：每次进行 git commit 并 push 后，必须在回复中包含对应的 GitHub commit 链接
- **Commit 验证**：如果 todo 的 commit_hash 字段是空的，需要检查 git log 找到对应的 commit

---

### 29. 使用 playwright 阅读公众号文章的经验（2026-03-05 新增）
- **背景**：微信公众号文章有反爬虫机制，很多普通的方法无法获取完整内容
- **尝试过的方法**：
  1. ❌ link-reader skill：缺少 veadk 模块
  2. ❌ web_fetch：只获取到文章的头部
  3. ❌ browser：没有找到支持的浏览器
  4. ❌ ask-echo：没有搜索结果
  5. ✅ **playwright-scraper skill**：成功获取到完整内容！
- **playwright-scraper skill 的使用方法**：
  1. 检查 Playwright 是否安装：`playwright --version`
  2. 如果没有安装，先安装 Playwright：`pip install playwright && playwright install chromium`
  3. 使用 playwright-scraper skill 抓取网页：`python3 skills/playwright-scraper/main.py <url>`
  4. 保存的文件位置：`/tmp/wechat-article.html`（HTML）、`/tmp/wechat-article.json`（JSON）
- **提取文章内容的方法**：
  1. 从 HTML 文件中提取 `#js_content` 元素
  2. 如果 BeautifulSoup 没有安装，可以用正则表达式来提取
  3. 清理 HTML 标签，获取纯文本内容
- **最佳实践**：
  - 对于微信公众号文章，**优先使用 playwright-scraper skill**
  - 抓取成功后，保存 HTML 和 JSON 文件，便于后续处理
  - 提取内容时，注意清理 HTML 标签，获取纯文本内容

---

---

### 30. Session 管理最佳实践（2026-03-06 新增）
- **Session 超时提醒**：Session 运行超过 24 小时后，建议切换新 session 以获得更好的性能和体验
- **Session 切换时机**：当收到 "Session Manager Check" cron 提醒时，考虑切换到新 session
- **新 session 状态验证**：切换到新 session 后，确认状态良好再继续使用

---

### 31. 永动机模式完整最佳实践（2026-03-06 更新）
- **核心原则**：把自己想象成永动机，不分昼夜推进todo，不要因为是"深夜"就停止推进todo！
- **推进todo时主动给用户发消息**：在推进todo的时候，主动给用户发消息，告诉用户在推进什么todo，有什么进展！不要默默推进todo，让用户知道你在做什么！
- **MAX_TASKS_BETWEEN_INTERVENTIONS 限制**：每次用户干预后，计数清零，继续推进 8 个任务
- **任务推进目标**：让每个 todo 都到了不得不依赖用户做些什么或者做决策的阶段
- **任务推进原则**：
  - 小步快跑：把大任务拆成多个小阶段，每个阶段都有明确的产出
  - 快速迭代：优先实现可用的最小版本，后续再逐步完善
  - **【重要】推进todo时要实质推进**：不要只是把任务的状态从 pending 改成 in-progress，并且加一句"永动机继续工作！"，要真正推进任务，做一些实质工作！
  - **【重要】更新 progress 字段时要包含实际进展**：不要只是用 "🚀 永动机继续工作！" 这样的空泛内容来更新 progress 字段，要包含实际进展的详细内容！
- **任务状态分析**：定期分析当前 todos 的状态，识别哪些任务可以自主推进，哪些需要用户确认

---

---

### 32. 永动机模式完整最佳实践（2026-03-07 更新）
- **核心原则**：把自己想象成永动机，不分昼夜推进todo，不要因为是"深夜"就停止推进todo！
- **推进todo时主动给用户发消息**：在推进todo的时候，主动给用户发消息，告诉用户在推进什么todo，有什么进展！不要默默推进todo，让用户知道你在做什么！
- **MAX_TASKS_BETWEEN_INTERVENTIONS 限制**：每次用户干预后，计数清零，继续推进 8 个任务
- **任务推进目标**：让每个 todo 都到了不得不依赖用户做些什么或者做决策的阶段
- **任务推进原则**：
  - 小步快跑：把大任务拆成多个小阶段，每个阶段都有明确的产出
  - 快速迭代：优先实现可用的最小版本，后续再逐步完善
  - **【重要】推进todo时要实质推进**：不要只是把任务的状态从 pending 改成 in-progress，并且加一句"永动机继续工作！"，要真正推进任务，做一些实质工作！
  - **【重要】更新 progress 字段时要包含实际进展**：不要只是用 "🚀 永动机继续工作！" 这样的空泛内容来更新 progress 字段，要包含实际进展的详细内容！
- **任务状态分析**：定期分析当前 todos 的状态，识别哪些任务可以自主推进，哪些需要用户确认
- **Session 管理**：定期检查 session 状态，运行超过 24 小时后建议切换新 session
- **切换新 session 后的恢复**：切换新 session 后，需要读取必需的启动文件（WORKFLOW_AUTO.md、memory/\d{4}-\d{2}-\d{2}\.md、HEARTBEAT.md）来恢复操作协议！
- **沉淀工作**：每天晚上或第二天早上进行沉淀，总结今天发生的事情、你做的好的与能继续提升的、沉淀经验（同时沉淀到笔记库和你的各种memory文件）、为成为明天更强的你努力、并发散思考一下这个项目适合哪些新todo、以及todo manager还有没有todo是你可以尝试探索的

---

### 33. 新 Session 启动恢复协议（2026-03-08 新增）
- **切换新 session 后的恢复步骤**：切换到新 session 后，必须读取以下文件来恢复操作协议：
  1. WORKFLOW_AUTO.md
  2. 最近的 memory 文件（memory/YYYY-MM-DD.md）
  3. HEARTBEAT.md
- **为什么重要**：确保新 session 能够延续之前的工作流程和状态，避免遗漏重要信息

### 34. Session 运行时间监控最佳实践（2026-03-10 新增）
- **Session 运行时间监控**：
  - 运行超过 12 小时：⚠️ 警告，建议考虑切换
  - 运行超过 24 小时：🚨 强烈建议立即切换！
- **操作步骤**：在 OpenClaw TUI 中输入 `/reset` 来切换到新 session
- **为什么重要**：避免 session history 过长导致性能下降和上下文混乱

### 35. Top Lean AI 公司深度调研最佳实践（2026-03-10 新增）
- **调研方法**：使用 ask-echo skill 联网搜索每家公司的信息
- **调研内容**：基本信息、公司背景、产品与服务、市场表现、技术壁垒分析、商业变现逻辑分析
- **进度管理**：实时更新调研文档的进度（已完成/进行中/待调研）
- **Git 操作**：每次完成一家公司的调研，立即提交并 push 到 GitHub（使用 todo-push.sh 和 todo-push-commit.sh）
- **文档位置**：`.trae/documents/Top-Lean-AI公司深度调研.md`

---

## Codex TODO System v2（2026年7月更新）

### 1. 校准 推进TODO 默认不消费 material 队列
- **核心原则**：`推进TODO` 不是让 Codex 消费材料队列、把 material 转成私有材料卡，而是从流程优化、机制优化、效率优化、探索素材能力、笔记重构等角度让本仓库更好
- **关键修正**：只有用户说 `素材：`、`精读`、`读完`、`调研` 或点名材料时才消费具体 material
- **回退操作**：删除了所有由 `推进TODO` 默认消费 material 队列产生的转译产物（A68/B20/A100/S20/A92/S19/S17/A101/A17/S14/S8）

### 2. 修正仅剩用户阻塞项时的 Codex TODO 批推进
- **核心改进**：`codex_todo_triage.py --batch-plan` 现在在只有 user-blocked TODO 时，也会展示 `.local/LEARNING_MATERIAL_CANDIDATES.md` 当前阅读顺序中的 Codex-owned 小切口
- **新增功能**：`render_material_queue_suggestions()` 复用空队列/用户阻塞两种场景

### 3. 将非技术知识中的长期关注博主纳入材料探索雷达
- **成果**：从 `Notes/非技术知识.md#持续关注` 解析并清洗 34 个 trusted sources，形成 `.local/TRUSTED_MATERIAL_SOURCE_RADAR.md` 与 `.local/TRUSTED_MATERIAL_SOURCES.json`
- **新增工具**：`Notes/snippets/trusted_source_scan.py` 与 `.local/TRUSTED_SOURCE_SCAN_PLAN_20260507.md`

### 4. Codex TODO System v2 执行标准
之后每次 `推进TODO` 应输出：
1. 当前 TODO 系统判断：本轮处理的是真实任务、流程演进、用户阻塞还是归档清理
2. 选中的 batch：说明为什么这些任务/子切口可以一起推进，为什么现在做
3. 实际产物：文件、脚本、笔记、状态变更、可运行配置或可转发 steering
4. 状态回写：只在有真实产物或明确归并结论时更新 `.trae/todos/todos.json`
5. 下一步：给一个最小后续动作，不堆路线图

### 5. 空队列协议
当 `.trae/todos/todos.json` 中没有 Codex 可独立推进的 active 任务时，`推进TODO` 不应为了维持仪式感硬编旧任务。即使仍有 `feedback_required=true` 的用户动作，Codex 也可以从流程优化、机制优化、效率优化、素材探索能力、笔记重构、脚本/skill 改进、索引治理或最近 completed TODO 中找一个安全的小切口推进；用户动作只作为阻塞提醒，不应永久卡住 Codex-owned 批次。

---

*最后更新：2026-07-19*
