# Read-Done Closure Checklist

当用户说 `读完`、`读后感`、`我读完这篇 paper 了` 时，先按这个清单收尾，避免只做摘要或只改一个局部笔记。

## 必交付

1. **已落盘位置**
   - 公开笔记路径。
   - 私有归档路径。
   - 关键图片 / 附件路径。

2. **笔记精炼版**
   - 用用户读后判断作为一手信号。
   - 组织成 `结论 -> 机制 -> 对当前系统的设计影响`。

3. **Material 状态变化**
   - 从 `.local/LEARNING_MATERIAL_CANDIDATES.md` 移除 active 队列。
   - 写入 `.local/LEARNING_MATERIAL_ARCHIVE.md`。
   - 如果阅读顺序变化，说明下一项是什么。

4. **上层 high-level 同步检查**
   - 检查是否需要更新领域框架、综述表、路线图、概念地图或跨材料排序。
   - 如果更新了，明确指出更新点；如果不更新，说明“不改变上层框架”。
   - 如果材料有 OpenReview、rebuttal、issue discussion、postmortem 或公开评审记录，单独做“置信度校准”：区分原文 claim、评审/社区质疑、作者回应和自己的判断；必要时更新该材料在领域框架中的证据权重，而不是只更新内容摘要。

5. **派生文档同步校验**
   - 如果本次改动同步到了飞书、Wiki、公开综述或其他派生文档，必须做一次远端校验。
   - 最低校验包括：目录/outline 正常、关键词能命中新内容、公式/图片没有污染标题或丢成错误 block。
   - 如果派生文档是从本地 canonical section 生成的，记录 canonical path、远端链接和远端 revision / 更新时间。
   - 本地 canonical section 同步飞书时，按 [lark-derived-doc-sync-checklist.md](lark-derived-doc-sync-checklist.md) 执行。

6. **Agent Harness 主控转发稿**
   - 只有材料改变 Agent Harness / OpenViking / tau2 / memory feedback / runner bridge 设计判断时输出。
   - 包含：背景、建议动作、验收标准、claim boundary、相关链接/文件。

7. **用户可复用表达**
   - 2-4 句用于同事讨论、面试 deep dive、读书会或写作的话。

8. **下一步建议**
   - 最多 1-3 个动作。
   - 阅读本身不算完成；下一步必须连接到 schema、benchmark、设计文档、case taxonomy、代码或汇报材料。

## 输出顺序

```text
1. 已落盘位置
2. 笔记精炼版
3. material 状态变化
4. 上层 high-level 同步检查
5. 派生文档同步校验
6. Agent Harness 主控转发稿
7. 用户可复用表达
8. 下一步建议
```
