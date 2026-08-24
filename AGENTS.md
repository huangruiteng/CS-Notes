# AGENTS.md

本文件适用于 Codex CLI/App 在本仓库内工作，补充而不替代 `.trae/rules/project_rules.md` 与 `.openclaw-memory/AGENTS.md`。

如果本机存在 `.local/AGENTS.md`，必须先读取并作为本地私有补充指令执行；`.local/` 内容不提交、不同步、不外泄。

## 1. 仓库定位

`CS-Notes` 是一个复合工作系统，不只是笔记仓库：

- `Notes/`：长期知识管理
- `创作/`：写作与观点表达
- `公司项目/`：公司相关 WIP，默认视为私密内容
- `.trae/`：todo、规则、web 管理、执行控制面
- `.openclaw-memory/`、`.trae/openclaw-skills/`、`snippets/`、`prompts/`、`.codex/`：agent / workflow / skill 实验区

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
snippets/codex-persistent-shell.sh
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

1. 先做“落点判定”，不要把职业主线或 Agent infra 当成默认落点。
   - 用户显式点名文件、目录、section 或主题时，点名目标优先；例如用户说 `AI-Algorithms`，就先按模型算法笔记处理，而不是自动映射到 Agent infra。
   - 用户没有点名时，先判断材料自身的主贡献：模型能力 / 训练算法 / 推理系统 / agent runtime / 产品设计 / 组织观点 / 职业信号等，再去 `Notes/` 中找对应落点。
   - 只有当材料本身就是 agent harness、agent runtime、memory、eval、workflow，或用户明确要求映射到当前职业主线时，才优先找 Agent infra / runtime 落点。
   - 如果材料跨多个主题，拆分落点；如果主领域不确定，先给 1 个简短候选落点判断再写，不要带着单一路线硬落盘。
2. 再在 `Notes/` 中广搜最佳落点，并优先比较用户点名目标与材料主领域是否一致。
3. 修改 Markdown 前先看结构，优先用 `snippets/markdown_toc.py`。
4. 优先插入现有 section；确实没有合适位置再新增小节。
5. 语言尽量压缩，不为“更整洁”而删除用户原内容。
6. 外部材料必须附来源链接。
   - 如果结论来自开源仓库、官方文档、prompt 或代码文件，不要只写仓库名或文件名；尽量附到具体文件 / section 的可点击链接。
   - 对 GitHub 源码或 prompt 做机制沉淀时，优先使用 commit-pinned permalink，并在 `.local` archive 中保留读取 commit，方便以后复核。
7. 一份材料跨多个主题时，拆分落到多个位置，不强塞进一个文件。
8. `Notes/` 内的数学公式默认面向 Typora 阅读：真正的公式用块级 `$$...$$`，不要用 ```text 代码块伪装公式；普通 schema / 字段列表才用代码块。
9. 如果用户提供或原文包含对理解机制确有必要的关键图，优先保存到目标 Markdown 同名资源目录（如 `Notes/AI-Applied-Algorithms/`），再用相对路径链接（如 `![...](./AI-Applied-Algorithms/xxx.png)`）；不要只依赖聊天截图或外链。
10. 对内部飞书 / ByteTech / 公司文档做笔记时，写入 git 关联笔记库前必须脱敏：不要写内部 URL、临时 token、内部人员/团队细节或非公开实现；优先引用公开论文、开源仓库、官方文档、release note。若材料来自内部文档但也有公开实现，公开笔记只能写“基于公开/开源材料分析”，完整内部来源和私有判断只放 `.local/`。
11. `S21`、`A89` 这类材料候选库编号只用于 `.local/LEARNING_MATERIAL_CANDIDATES.md` / `.local/LEARNING_MATERIAL_ARCHIVE.md` 的追踪；写入 `Notes/` 的长期笔记标题时不要带这些编号，标题应面向主题本身。
12. 笔记整理和 `读完` 闭环完成前，必须做一次“上层 high-level 同步检查”：判断新材料是否改变目录页、领域框架、综述表、概念地图、路线图或跨材料排序；若改变，就适当更新上层笔记，而不是只把内容塞进局部 section。
13. `读完` 闭环中，用户明确强调的要点必须进入 `Notes/` 主体笔记，不能只落到 `.local/LEARNING_MATERIAL_ARCHIVE.md`。公开主笔记可以压缩成框架化表达，但每个用户抓手都要在 `Notes/` 中有可检索锚点：可以是正文小节、表格行、schema 字段、cross-reference、脚注式来源说明或一句明确判断；`.local` archive 只作为原文细节、私密来源、过长证据和读取记录的补充，不能替代主笔记落盘。
14. `读完` 完成前必须做“用户抓手覆盖检查”：先列出用户强调的每个关键机制、benchmark、schema、figure/table、failure case、术语判断、质疑点或对比句，再逐项标注其 `Notes/` 落点；若某个抓手因安全、隐私或不适合公开而不能原样写入 `Notes/`，也必须写入脱敏后的通用表达，并说明完整细节保留在 `.local` 的原因。
15. 新增、重命名或删除 `Notes/` 下文件后，同步刷新 `README.md` 的「笔记目录」树：按主题归类（计算机基础 / 算法与编程 / 编程语言与工具 / 数据与分布式 / AI·机器学习 / 软件工程与开源 / 通用与生活），保持 `├── / └──` 树形缩进与同主题 `/` 并排写法；不列 `tmp*` 等临时目录；同名子目录（图片/资源）不单独列出，只在目录开头统一说明。

### B. 写作与公司项目

- 文风要求：平实、凝练、有立场、结构清晰、重分析与比较，避免 AI 套话。
- 做较大写作前，先读 `创作/` 下 2-3 篇文章对齐语气。
- 涉及 `公司项目/` 时，先读 `公司项目/01-公司项目创作pipeline.md`，并按该 pipeline 执行。

### C. Todo 驱动执行

- 单一数据源：`.trae/todos/todos.json`
- 用户说 `推进项目` / `推进TODO` / `推进todo` 时，默认优先关注 **本仓库** 的 TODO、文档、脚本和笔记工作流；不要主动把重心滑到 `agent-harness` 仓库。
- 只有当本仓库 TODO 明确指向 `agent-harness`、用户明确要求查看 `agent-harness`、或需要生成给 `agent-harness` 主控的转发稿时，才读取/引用 `agent-harness` 状态。
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
- `推进TODO` 的默认目标是让本仓库工作系统更好，而不是消费 `.local/LEARNING_MATERIAL_CANDIDATES.md` 队列中的具体材料。优先从流程优化、机制优化、效率优化、素材探索能力、笔记重构、脚本/skill 改进、索引治理、用户动作队列压缩中找切口；只有用户明确说 `素材：`、`调研`、`请你读`、`精读`、`读完` 或点名某个材料时，才处理具体 material。
- 推进 TODO 时，如果发现值得同步给 `agent-harness` 主控 agent 的设计判断、实验建议、数据字段、benchmark 变体或风险提醒，必须生成一段可直接转发的 `Agent Harness 主控转发稿` 给用户；不要假设 Codex 可以直接指挥另一个仓库的主控 agent。
- `Agent Harness 主控转发稿` 应该短、明确、可执行，包含：背景、建议动作、验收标准、相关文件/链接；如果只是想法而非行动，不要打扰主控 agent。

### D. Tooling / agent / web-manager

重点目录：`.trae/openclaw-skills/`、`.trae/web-manager/`、`.trae/web-manager/templates/`、`.openclaw-memory/`、`snippets/`、`prompts/`、`.codex/`

处理这些目录时：

1. 保持 Codex、Trae、OpenClaw 的互通性。
2. 优先改善默认工作路径，而不是只做 demo。
3. 涉及模板、迁移、打包时，检查模板和脚本是否需要同步更新。
4. 注意区分“项目定制改动”与“通用模板改动”，避免写错层级。

### E. 调研 / 找素材

当用户说“素材：”“调研”“找素材”“材料雷达”“学习材料”时，默认按素材管线处理：

若当前项目已显式启用 LoopX Material Lifecycle，通用的 snapshot /
inventory、生命周期迁移、无损 ranked-entry rebuild、bounded rerank、
owner-gated apply 与 rollback 统一遵循项目级受管的 `loopx-material` skill。
本文只保留 CS-Notes 的来源读取、私有落点、主题分类、职业优先级和笔记写作规则；
项目规则可以收紧但不能削弱 `loopx-material` 的无损、exact-read 和 authority 门禁。

本仓库已经启用该能力：当
`.local/material-lifecycle/authority/current.json` 指向 `managed_catalog`
时，`.local/LEARNING_MATERIAL_CANDIDATES.md` 与
`.local/LEARNING_MATERIAL_ARCHIVE.md` 仅作为原 777 条记录的只读内容
backing / rollback source。任何线程都不得直接向旧文件追加材料、修改生命周期或
编辑其中的旧 Top30；新素材必须走 exact-read evidence -> managed candidate
intake -> authority CAS/readback/receipt -> Decision Context-backed ranking
settlement。`素材：`授权 candidate intake 与同一工作流内的排序结算；两者仍使用
独立 receipt，发生排序变化时使用独立 authority revision，以保留 CAS、预览、回滚
和审计边界。

每次 intake 都必须给出 `top_window | ranked_backlog | no_change` disposition。
高价值素材（由材料证据、S/A/B 分层、当前 Decision Context、重复度和可转化 artifact
共同判断，不只看分档）必须进入 Top30 或显式 ranked backlog，不能只停在未排序候选；
非高价值或与现有条目高度重复时可以 `no_change`，但必须写明理由。Top30 已满时，
被替换条目下沉 ranked backlog，不得丢失；受保护锚点除非用户明确要求或 Decision
Context 已改变，否则不动。ranking apply / readback / projection / audit 未闭环前，
不得把高价值素材 intake 报告为完成。

**指令约定**

- `素材：<链接/文本>`：用户投喂材料。读取、保留原始链接、分档、摘要；本仓库通过项目级 `loopx-material` 将 exact-read 结果写入 managed candidate store，并在同一工作流完成 ranking disposition。高价值材料进入 Top30 或 ranked backlog；读不到则保留 Unread 状态并说明需要用户补正文/截图/导出。
- `调研：<问题/方向>`：主动调研指令。围绕问题做多源召回、追一手来源、去噪分档，并给出下一步学习/产出建议。
- `整理笔记：<链接/文本>` 或“整理笔记 + 点名文件 / 主题”：直接进入 `Notes/` 笔记整合流程。用户点名目标和材料主领域优先，不默认入候选库，也不默认映射到 Agent infra / 职业主线。
- `请你读：<材料 id / 链接 / 标题>`：Codex 先读原文 / repo / 数据入口，再给精要内容、核心设计、用户本人是否需要继续读、对当前 artifact 的改造点；输出时必须区分“材料值得 Codex 读透 / 落成设计语言”和“用户本人需要亲自精读原文”，并尽量细分到 section / figure / table / code / doc page 粒度，不要把二者混成一个判断；若判断“读 Codex 摘要即可 / 用户不用亲读”，摘要必须达到替代用户首读的密度，覆盖核心机制、关键字段 / schema、实验或证据、局限和 artifact 映射，而不是只给结论；若材料有关键数学机制或指标定义，在原有讲解基础上补核心公式 / 数学直觉，但不要为了公式而公式；`精读` 保留为兼容别名。
- `继续调研`：沿用最近一次 `调研：` 的主题继续扩展，但必须补充新来源或新判断，不能重复已有候选。

1. 先判断意图和输出面：`整理笔记` 写长期笔记；`素材` 入候选库；`调研` 围绕当前职业主线找高价值材料；`请你读 / 精读` 先读后给机制摘要和读法建议。不要把这四类混成同一条 Agent infra 管线。
2. 优先使用已有专用读取能力：微信公众号、小红书、飞书文档、GitHub、arXiv、官方文档等；读不到就明确标为待读，不假装读过。
3. 对近期动态、社媒评价、热点追踪、作者动态这类广域召回需求，SenSight 优先作为主召回层；Codex 负责二次验证、去噪、分档和落盘。
4. Agent-Reach 这类本地互联网工具脚手架作为补位：适合读具体 URL、视频字幕、GitHub、RSS、Reddit 等 source-level 内容；不替代 SenSight 的跨平台聚合与质量筛选。
5. 召回后必须追一手来源：论文、官方文档、代码仓库、release note、原始访谈或产品页优先；社媒和公众号只作为线索或二级解读。
6. 入库先检查 managed authority：本仓库默认写受管 catalog 与 immutable managed-native content backing，并生成 intake receipt；随后基于当前 Decision Context 生成并应用 ranking settlement，验证 membership / readback / projection / audit。只有未启用 Material Lifecycle 的其他项目才回退到其旧候选库。
7. 对用户最重要的固定方向：Agent infra / OpenClaw / ArkClaw / Agent Harness / OpenViking / agent memory / RL infra / verl / Ray / vLLM / SGLang / RecSys+LLM。

**SenSight 调研执行流**

- SenSight 的定位是“广域雷达”，不是事实来源；它负责发现近期动态、社媒线索和跨平台讨论，最终事实必须回到 arXiv、GitHub、官方文档、release note、作者原文或一手访谈核验。
- 主动调研默认三段式：
  1. 召回：`social_search` 看社媒和近期讨论，`retrieve_summarize` 看 AI 技术长文聚合，`daily_paper` / `daily_blog` 若为空不算失败，`search_events` 更适合热点追踪而不是精确技术材料。
  2. 验真：对高价值线索追一手来源；找不到一手来源的社媒观点只能作为 B 档、Unread 或线索，不写成确定事实。
  3. 价值输出：每个候选写清楚 S/A/B、原始链接、读取状态、为什么对当前 70/20/10 路线有价值、能转成哪个 artifact / schema / TODO；同时说明哪些材料不该现在读。
- 一次 `调研：` 完成标准：说明 SenSight 或降级路径状态，至少检查两个不同来源类型，给出新增候选或“不入库”的理由；若产生候选，确认 managed authority 已包含该 stable material ref 且 receipt/readback 成功。
- 调研结果优先更新阅读顺序和行动优先级，而不是只把材料追加到文件尾。

**自验证要求**

- 每次 `调研：` 完成前，检查至少两个不同来源类型；如果 SenSight 不可用，明确记录降级路径。
- 每个高价值候选必须有原始链接、读取状态、来源类型和一句“为什么值得你看/为什么只需我摘要”的判断。
- 社媒/公众号观点不能直接当事实，涉及技术事实时必须追论文、代码、官方文档、release note 或一手访谈。
- 完成前确认新增条目已进入当前 managed authority；不得以旧 Markdown 中出现一段文本代替受管入库。

### F. AI 热点日报

当用户说“AI热点”“AI 日报”“AI hot topics”或要求每天早上的 AI 热点报告时，默认使用 `.codex/skills/ai-hotspots/`：

1. 从指定 AI/news 聚合源召回新内容，优先找 AI 产品、论文、观点、认知更新。
2. 只选最值得看的 10 条；长内容压缩成不超过 100 字摘要并保留链接。
3. 聚合站只作为发现入口；事实判断必须尽量追一手来源。
4. 默认把中英文双语 HTML 日报保存为本地页面文件；聊天里只给精简 Markdown 摘要、文件路径、source coverage / unread 说明，不直接贴整页 HTML 源码。
5. 如果用户明确要“每天早上自动发”，先确认具体时间，再创建 automation。

### G. 飞书 CLI / Lark 工作流

当任务涉及飞书 / Lark 的文档、知识库、云盘、表格、多维表格、日历、会议、妙记、IM、邮箱、任务或通讯录时，默认把 `lark-cli` 视为 Agent 的操作手臂：优先用已安装的 `lark-*` skills 或 `.codex/skills/lark-cli-workflow/` 路由到正确业务域，而不是把飞书链接当普通网页读。

1. 先识别对象与身份：URL / token 先解析真实类型；wiki 节点先解包到真实 docx / sheet / bitable 等对象；个人资源默认使用 `--as user`，应用资源才用 `--as bot`。
2. 读之前先缩小范围：云文档优先用 `docs +fetch --api-version v2 --scope outline/keyword/section`；遇到嵌入表格、多维表格、画板等资源，提取 token 后切到对应 skill 下钻。
3. 写之前先确认写入面：优先做 block / section 级局部更新，保留评论、标注、权限和 reviewer-visible 信号；全量覆盖、删除、批量发送、权限变更等高风险动作必须有明确意图或 dry-run 预览。
4. 权限与授权按最小权限处理：缺 scope 时根据 CLI 提示补 `auth login --scope ...`；不要记录或外泄临时授权 URL、token、内部文档链接、内部人员 / 团队细节。
5. 输出要落到真实工作对象：能直接创建 / 更新飞书文档、表格、任务或消息时，不只给用户复制粘贴文本；公开仓库只沉淀脱敏后的通用经验，完整内部来源和私有判断放 `.local/`。

## 5. Git、安全与边界

### 禁止外泄

绝不提交或暴露：

- `公司项目/` 下任何内容
- 密钥、token、密码、AK/SK、私有链接
- 环境文件或其他敏感配置

### Git 工作流

优先使用：

- `snippets/todo-pull.sh`
- `snippets/todo-push.sh`
- `snippets/todo-push-commit.sh`

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
