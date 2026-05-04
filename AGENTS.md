# AGENTS.md

本文件适用于 Codex CLI/App 在本仓库内工作，补充而不替代 `.trae/rules/project_rules.md` 与 `.openclaw-memory/AGENTS.md`。

如果本机存在 `.local/AGENTS.md`，必须先读取并作为本地私有补充指令执行；`.local/` 内容不提交、不同步、不外泄。

## 1. 仓库定位

`CS-Notes` 是一个复合工作系统，不只是笔记仓库：

- `Notes/`：长期知识管理
- `创作/`：写作与观点表达
- `公司项目/`：公司相关 WIP，默认视为私密内容
- `.trae/`：todo、规则、web 管理、执行控制面
- `.openclaw-memory/`、`.trae/openclaw-skills/`、`Notes/snippets/`、`.codex/`：agent / workflow / skill 实验区

工作时优先优化整个系统，而不是把文件当成彼此孤立的文档。

## 2. 默认原则

1. 先回答问题，再把结果落到最合适的位置。
2. 能自主推进就推进；只有在用户决策或手动操作不可替代时才停下。
3. 优先做真实改动，少做临时文件、演示性产物或伪完成。
4. 尊重现有结构与文风，尤其是 `Notes/`、`创作/`、`公司项目/`。
5. 重要结论尽量附上来源链接、文件路径或具体产物，保证可追溯。
6. 如果在“快速回复”和“可持续落盘”之间犹豫，优先后者。
7. 笔记整理类任务默认直接执行；高复杂度的代码/端到端任务可以先给简短 plan 供 review，或只问一两个关键问题。

## 3. Shell 与上下文

### Shell 策略

默认使用独立命令，保留并发能力：

```bash
zsh -lc 'source ~/.zshrc; <command>'
```

仓库已有 `.codex/environments/environment.toml` 配置 `script = "source ~/.zshrc"`，手动执行时也保持一致。

只有一串命令明确依赖共享 shell 状态、且反复加载 `~/.zshrc` 成本明显时，才使用：

```bash
/Users/bytedance/CS-Notes/Notes/snippets/codex-persistent-shell.sh
```

使用规则：

- 该脚本会在单个 TTY session 内只加载一次 `~/.zshrc`
- 适用于共享 cwd、env、alias、shell function、virtualenv / conda / nvm 状态
- 不要把 persistent shell 当全局默认，否则会削弱并发并增加状态污染风险

### 最小上下文

不要先通读整个仓库。按需加载：

- 常规必读：`README.md`、`.trae/rules/project_rules.md`、`.trae/documents/PROJECT_CONTEXT.md`
- workflow / memory：`.openclaw-memory/MEMORY.md`、`.openclaw-memory/AGENTS.md`、相关 memory 文件
- todo / 执行：`.trae/todos/todos.json`、相关 skill、`.trae/web-manager/WORKFLOW.md`
- 写作：先读 `创作/` 下 2-3 篇代表文章
- 笔记整合：先在 `Notes/` 广搜，再检查候选文件结构

### Markdown 文件打开

当需要在本机为用户打开 Markdown 文件时，默认使用 Typora：

```bash
open -a Typora <file.md>
```

## 4. 工作流

### A. 笔记整合

1. 先在 `Notes/` 中广搜最佳落点。
2. 修改 Markdown 前先看结构，优先用 `Notes/snippets/markdown_toc.py`。
3. 优先插入现有 section；确实没有合适位置再新增小节。
4. 语言尽量压缩，不为“更整洁”而删除用户原内容。
5. 外部材料必须附来源链接。
6. 一份材料跨多个主题时，拆分落到多个位置，不强塞进一个文件。
7. `Notes/` 内的数学公式默认面向 Typora 阅读：真正的公式用块级 `$$...$$`，不要用 ```text 代码块伪装公式；普通 schema / 字段列表才用代码块。
8. 如果用户提供或原文包含对理解机制确有必要的关键图，优先保存到目标 Markdown 同名资源目录（如 `Notes/AI-Applied-Algorithms/`），再用相对路径链接（如 `![...](./AI-Applied-Algorithms/xxx.png)`）；不要只依赖聊天截图或外链。
9. 对内部飞书 / ByteTech / 公司文档做笔记时，写入 git 关联笔记库前必须脱敏：不要写内部 URL、临时 token、内部人员/团队细节或非公开实现；优先引用公开论文、开源仓库、官方文档、release note。若材料来自内部文档但也有公开实现，公开笔记只能写“基于公开/开源材料分析”，完整内部来源和私有判断只放 `.local/`。

### B. 写作与公司项目

- 文风要求：平实、凝练、有立场、结构清晰、重分析与比较，避免 AI 套话。
- 做较大写作前，先读 `创作/` 下 2-3 篇文章对齐语气。
- 涉及 `公司项目/` 时，先读 `公司项目/01-公司项目创作pipeline.md`，并按该 pipeline 执行。

### C. Todo 驱动执行

- 单一数据源：`.trae/todos/todos.json`
- 新增 todo：优先使用 `todo-adder`
- 执行 todo：优先走 `priority-task-reader`
- 真正开工前，先把任务改成 `in-progress` 并写入 `started_at`
- 推进任务必须带来真实产物，不要只改状态文本
- 明确区分：AI 可独立完成的任务 vs 必须等待用户动作的任务
- 用户说 `推进TODO` / `推进todo` 时，默认不是只做一个小修，而是做一次 **批推进**：
  - 目标批量：3-5 个低风险小切口，或 1 个主任务 + 2-4 个配套的文档/脚本/状态/规则更新。
  - 先列出本轮 batch，确认它们共享同一目标、写入范围不冲突、不会触碰公司私密内容或高风险 git 操作。
  - 对每个子切口都要有可验证产物；如果只够推进 1 个，必须说明为什么不能批推进。
  - 批推进完成后，统一回写 `.trae/todos/todos.json`、刷新 `.local/CODEX_TODO_TRIAGE_INDEX.md`，并汇总实际产物。
  - 这条规则服务长程 agent 目标：把 TODO 推进变成 plan -> batch execution -> checkpoint -> replayable record，而不是零散单步响应。
- 推进 TODO 时，如果发现值得同步给 `agent-harness` 主控 agent 的设计判断、实验建议、数据字段、benchmark 变体或风险提醒，必须生成一段可直接转发的 `Agent Harness 主控转发稿` 给用户；不要假设 Codex 可以直接指挥另一个仓库的主控 agent。
- `Agent Harness 主控转发稿` 应该短、明确、可执行，包含：背景、建议动作、验收标准、相关文件/链接；如果只是想法而非行动，不要打扰主控 agent。

### D. Tooling / agent / web-manager

重点目录：`.trae/openclaw-skills/`、`.trae/web-manager/`、`.trae/web-manager/templates/`、`.openclaw-memory/`、`Notes/snippets/`、`.codex/`

处理这些目录时：

1. 保持 Codex、Trae、OpenClaw 的互通性。
2. 优先改善默认工作路径，而不是只做 demo。
3. 涉及模板、迁移、打包时，检查模板和脚本是否需要同步更新。
4. 注意区分“项目定制改动”与“通用模板改动”，避免写错层级。

### E. 调研 / 找素材

当用户说“素材：”“调研”“找素材”“材料雷达”“学习材料”时，默认按素材管线处理：

**指令约定**

- `素材：<链接/文本>`：用户投喂材料。读取、保留原始链接、分档、摘要并写入候选库；读不到就标记 Unread 并说明需要用户补正文/截图/导出。
- `调研：<问题/方向>`：主动调研指令。围绕问题做多源召回、追一手来源、去噪分档，并给出下一步学习/产出建议。
- `继续调研`：沿用最近一次 `调研：` 的主题继续扩展，但必须补充新来源或新判断，不能重复已有候选。

1. 先判断意图：用户投喂的链接要进入候选库；用户让主动调研时，要围绕当前职业主线找高价值材料。
2. 优先使用已有专用读取能力：微信公众号、小红书、飞书文档、GitHub、arXiv、官方文档等；读不到就明确标为待读，不假装读过。
3. 对近期动态、社媒评价、热点追踪、作者动态这类广域召回需求，SenSight 优先作为主召回层；Codex 负责二次验证、去噪、分档和落盘。
4. Agent-Reach 这类本地互联网工具脚手架作为补位：适合读具体 URL、视频字幕、GitHub、RSS、Reddit 等 source-level 内容；不替代 SenSight 的跨平台聚合与质量筛选。
5. 召回后必须追一手来源：论文、官方文档、代码仓库、release note、原始访谈或产品页优先；社媒和公众号只作为线索或二级解读。
6. 入库默认写 `.local/LEARNING_MATERIAL_CANDIDATES.md`，并给出 S/A/B/Unread 分档、摘要、对用户职业主线的价值、后续动作。
7. 对用户最重要的固定方向：Agent infra / OpenClaw / ArkClaw / Agent Harness / OpenViking / agent memory / RL infra / verl / Ray / vLLM / SGLang / RecSys+LLM。

**SenSight 调研执行流**

- SenSight 的定位是“广域雷达”，不是事实来源；它负责发现近期动态、社媒线索和跨平台讨论，最终事实必须回到 arXiv、GitHub、官方文档、release note、作者原文或一手访谈核验。
- 主动调研默认三段式：
  1. 召回：`social_search` 看社媒和近期讨论，`retrieve_summarize` 看 AI 技术长文聚合，`daily_paper` / `daily_blog` 若为空不算失败，`search_events` 更适合热点追踪而不是精确技术材料。
  2. 验真：对高价值线索追一手来源；找不到一手来源的社媒观点只能作为 B 档、Unread 或线索，不写成确定事实。
  3. 价值输出：每个候选写清楚 S/A/B、原始链接、读取状态、为什么对当前 70/20/10 路线有价值、能转成哪个 artifact / schema / TODO；同时说明哪些材料不该现在读。
- 一次 `调研：` 完成标准：说明 SenSight 或降级路径状态，至少检查两个不同来源类型，给出新增候选或“不入库”的理由，并确认候选已经落到 `.local/LEARNING_MATERIAL_CANDIDATES.md`。
- 调研结果优先更新阅读顺序和行动优先级，而不是只把材料追加到文件尾。

**自验证要求**

- 每次 `调研：` 完成前，检查至少两个不同来源类型；如果 SenSight 不可用，明确记录降级路径。
- 每个高价值候选必须有原始链接、读取状态、来源类型和一句“为什么值得你看/为什么只需我摘要”的判断。
- 社媒/公众号观点不能直接当事实，涉及技术事实时必须追论文、代码、官方文档、release note 或一手访谈。
- 完成前用搜索确认新增条目已写入候选库；如果没有落盘，不算完成。

### F. AI 热点日报

当用户说“AI热点”“AI 日报”“AI hot topics”或要求每天早上的 AI 热点报告时，默认使用 `.codex/skills/ai-hotspots/`：

1. 从指定 AI/news 聚合源召回新内容，优先找 AI 产品、论文、观点、认知更新。
2. 只选最值得看的 10 条；长内容压缩成不超过 100 字摘要并保留链接。
3. 聚合站只作为发现入口；事实判断必须尽量追一手来源。
4. 默认把中英文双语 HTML 日报保存为本地页面文件；聊天里只给精简 Markdown 摘要、文件路径、source coverage / unread 说明，不直接贴整页 HTML 源码。
5. 如果用户明确要“每天早上自动发”，先确认具体时间，再创建 automation。

## 5. Git、安全与边界

### 禁止外泄

绝不提交或暴露：

- `公司项目/` 下任何内容
- 密钥、token、密码、AK/SK、私有链接
- 环境文件或其他敏感配置

### Git 工作流

优先使用：

- `Notes/snippets/todo-pull.sh`
- `Notes/snippets/todo-push.sh`
- `Notes/snippets/todo-push-commit.sh`

commit / push 前必须：

1. 看 `git status`
2. 看 `git diff`
3. 如果使用 `todo-push.sh`，还要看 `git-diff-summary-*.md`
4. 确认没有带上禁推文件
5. 确认没有误删有价值的用户内容

禁止使用 force push 或其他高风险破坏性 git 操作，除非用户明确要求。

### Symlink 注意事项

`.openclaw-memory/` 下文件可能是其他工作区的 symlink 目标。修改时原地编辑，不要轻易删除重建。

## 6. 沟通风格与完成标准

- 默认中文，直接、简洁、少废话。
- 简单任务简答，复杂任务给清晰进展和关键决策。
- 卡住时说明具体 blocker，以及下一步需要用户做的不可替代动作。
- 尽量给出明确文件路径、产物路径和结论。

一个好的结果通常应满足：

- 放在正确文件，而不是随便找个地方
- 与现有结构和文风一致
- 有来源或路径支撑，可追溯
- 真正能接入当前工作流
- 安全、可继续、可提交
