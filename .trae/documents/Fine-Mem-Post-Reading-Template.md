# Fine-Mem 读后流程模板

> 用途：用户精读 Fine-Mem 后，执行此流程，把 schema 和 attribution 逻辑落到 Agent Harness / OpenViking 设计上。

## 前置条件

- 用户已完成 A101: Fine-Mem 的精读。
- 已读完 Fine-Mem-Reading-Guide.md 中的边读边核验的问题。
- 已确认 Fine-Mem 的核心机制对 Agent Harness 的价值。

## 步骤

### 1. 整理笔记到 Notes/AI-Applied-Algorithms.md

1. 在 Notes/AI-Applied-Algorithms.md 中找到最合适的 section。
2. 优先插入现有 section；确实没有合适位置再新增小节。
3. 语言尽量压缩，不为“更整洁”而删除用户原内容。
4. 附上来源链接：https://arxiv.org/abs/2601.08435。
5. 笔记内容应包括：
   - 一句话判断：Fine-Mem 最值得读的点不是“又一个 memory 方法”，而是它把 long-horizon agent 的最终成败拆回到细粒度 memory operation。
   - 核心机制：chunk-level step reward、evidence-anchored attribution、read/write/update 分开建模。
   - 对 Agent Harness 的直接改造：建议给 memory_ranking_dataset_v0 增加哪些字段。
   - 边读边核验的问题的答案。

### 2. 生成给 Agent Harness 主控的 steering 文档

1. 创建一个新的文档：.trae/documents/Fine-Mem-Agent-Harness-Steering.md。
2. 文档内容应包括：
   - 一句话判断：Fine-Mem 直接决定 memory_ranking_dataset_v0 不能只存 task-level pass/fail，而要存 step-level evidence、operation type 和 attribution。
   - 对 Agent Harness 的直接改造：建议给 memory_ranking_dataset_v0 增加哪些字段。
   - 建议的下一步动作：不要立刻做 RL policy，而是先实现 fine_grained_memory_feedback_v0。
   - 可直接转发给 agent-harness 主控的 steering 稿。

### 3. 更新 .local/LEARNING_MATERIAL_CANDIDATES.md

1. 把 A101: Fine-Mem 从当前阅读顺序移到已读部分。
2. 更新当前阅读顺序，把下一个最值得读的材料放到第一位。
3. 确认 Fine-Mem 的读取状态已更新为“已完成精读”。

### 4. 可选：新增 Agent Harness / OpenViking integration TODO

如果 Fine-Mem 的内容明确需要新增 TODO，则：
1. 使用 todo-adder 新增一个 TODO。
2. TODO 的 definition_of_done 应明确可验证产物。
3. TODO 的 progress 应记录真实推进结果。

## 验收标准

- Notes/AI-Applied-Algorithms.md 中已新增 Fine-Mem 的内容。
- 已生成 .trae/documents/Fine-Mem-Agent-Harness-Steering.md。
- .local/LEARNING_MATERIAL_CANDIDATES.md 已更新。
- （可选）已新增相关 TODO。
