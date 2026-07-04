# Prompts

这个目录和 `snippets/` 并列，用来沉淀可复用 prompt。

`snippets/` 偏脚本、代码片段、一次性工具；`prompts/` 偏可以直接复制到 Codex / Claude / ChatGPT / Trae / Lark bot 的任务指令、系统指令、评审清单和输出模板。

## 分类

| 目录 | 用途 |
| --- | --- |
| `coding/` | 代码阅读、代码修改、code review、工程质量、AGENTS.md / system prompt |
| `agent/` | Agent / OpenClaw / automation 使用案例和操作型 prompt |
| `writing/` | 小红书、公众号、长文、改写、评价 |
| `knowledge/` | 笔记整合、论文阅读、材料吸收 |
| `structured-output/` | JSON / schema / 分类抽取类 prompt |
| `domain/` | 垂直领域 prompt，例如美食、菜单、品鉴 |
| `meta/` | 生成和迭代 prompt 的 meta-prompt |

## 首批内容

- Agent / OpenClaw 使用案例、代码阅读、代码修改、code review、工程质量和最小化改动
- 小红书写作、评价与改写
- 笔记整合、论文阅读、结构化 JSON 输出
- 美食菜单品鉴和 meta-prompt

## 维护原则

- 每个 prompt 文件都要写明适用场景和正文；不强制标来源，除非来源本身是使用边界的一部分。
- 能直接复用的 prompt 才放这里；理论笔记、技巧摘要仍留在对应 Markdown 笔记里。
- 同一 prompt 如果要针对 Codex / Claude / 飞书机器人微调，可以新增同目录变体，不要覆盖原版。
- 后续从笔记中搬迁 prompt 时，优先搬“已经在真实工作中用过”的版本。
