# Trae CLI / Proactive 能力调研 Brief

> 对应 TODO：`todo-20260223-034039`、`todo-20260225-001`
> 更新时间：2026-05-04

## 1. 当前判断

这两个 TODO 本质上是同一个问题：Trae 是否已经具备类似 Claude Code / Codex 的 CLI agent 能力，以及它能否支持更 proactive 的长程执行工作流。

本机已确认 `trae` 可用，但它暴露出来的能力更像 Trae CN App 的编辑器 CLI + chat 入口，而不是可以直接判定为完整的 bash agent runner。真正需要内部确认的是：它的 `chat agent` 能否稳定非交互执行、输出结构化轨迹、被脚本编排、恢复长任务，并作为 OpenClaw / Agent Harness 的底层 worker 或评测对象。

## 2. 本机已验证事实

### 2.1 CLI 入口

本机可用命令：

```bash
trae
claude
codex
```

`trae` 指向：

```text
/Applications/Trae CN.app/Contents/Resources/app/bin/marscode
```

版本信息：

```text
Trae CN 3.3.53
trae --version: 1.107.1 / arm64
```

### 2.2 `trae --help` 暴露的能力

顶层能力主要包括：

- 编辑器类 CLI：打开文件、diff、merge、extension 管理、profile、status、log。
- MCP 配置：`--add-mcp <json>`。
- 子命令：
  - `chat`：在当前工作目录运行 chat session。
  - `serve-web`：通过浏览器展示 editor UI。
  - `tunnel`：安全 tunnel。

### 2.3 `trae chat --help` 暴露的能力

`trae chat` 支持：

```bash
trae chat [options] [prompt]
```

关键参数：

- `--mode ask|edit|agent|custom-mode`，默认 `agent`。
- `--add-file <path>`，把文件作为上下文。
- `--reuse-window` / `--new-window`。
- 可从 stdin 读取：`trae-cn chat <prompt> -`。

这说明它具备“从命令行启动 agent chat”的入口，但 help 中没有直接说明：

- 是否能非交互地等待任务完成并返回 exit code。
- 是否能输出 JSON / stream / trajectory。
- 是否能指定工具权限、模型、sandbox、approval policy。
- 是否能 resume session 或后台运行。

## 3. 旧评估材料的启发

已有文档：

- `.trae/documents/trae-agent-评估报告.md`
- `.trae/documents/OpenClaw-vs-Trae-Agent-对比报告.md`
- `.trae/documents/我和trae-agent公平对比报告.md`
- `Notes/snippets/code-reading-trae-agent.md`

旧评估中的 `trae-agent` 与当前 Trae App CLI 不一定是同一个产品形态，但有两个判断仍然重要：

1. **trajectory / Lakeview 这类可观测性是核心价值**
   - 对 Agent Harness 来说，能拿到结构化轨迹比“能跑起来”更重要。
   - trace / replay / eval / memory feedback 都依赖可观测性。

2. **真正的执行质量不能只看是否完成**
   - 旧对比里 Trae Agent 曾出现“看了文件但没有实际修改、却标记完成”的问题。
   - 这对 proactive agent 特别危险：长程无人值守时，false positive completion 比普通失败更难发现。

## 4. 内部需要确认的问题

可以直接把下面这段发给 Trae / internal coding agent / OpenClaw 相关 owner。

```text
我想调研 Trae 是否有类似 Claude Code / Codex 的 bash/CLI agent 能力，尤其关注是否能被脚本编排、无人值守执行、并输出结构化轨迹。有没有内部文档或 owner 可以请教？

我主要想确认这些点：
1. Trae CLI 的 `trae chat --mode agent <prompt>` 是否支持非交互执行到完成，并以 exit code 表示成功/失败？
2. 是否支持 stdout JSON / streaming event / trajectory 文件 / tool trace / token usage / step summary？
3. 是否能指定 cwd、模型、工具权限、MCP、workspace rules、AGENTS/CLAUDE 类 memory？
4. 是否支持 resume session、session id、后台运行、超时控制、崩溃恢复？
5. 是否有 proactive / daemon / scheduler / background task 能力？
6. 是否支持类似 Claude Code 的 bash + edit + test loop，或更偏 IDE chat？
7. 是否有内部推荐的 CLI agent benchmark 或最佳实践？
8. 如果要把它接入 Agent Harness 做 trace/replay/eval，最稳定的 API/CLI 入口是什么？
```

## 5. 评估矩阵

拿到内部信息后，按下面矩阵判断，不要只问“能不能用”。

| 维度 | 需要确认的问题 | 对当前主线的意义 |
|---|---|---|
| CLI surface | prompt、stdin、stdout、exit code、JSON、streaming | 决定能否被 harness 自动编排 |
| Agent loop | bash、edit、test、retry、tool policy | 决定是否是真 worker，而不只是 IDE chat |
| Observability | trajectory、tool trace、token、step summary、error | 决定能否做 trace/replay/eval |
| Long-running | session id、resume、daemon、timeout、crash recovery | 决定能否做通宵任务和 proactive TODO |
| Memory/rules | workspace rules、MCP、skills、长期记忆 | 决定能否接 personalized procedure memory |
| Security | sandbox、approval、secret redaction、权限边界 | 决定能否放心接私有仓库和公司项目 |
| Integration | Git/MR、CI、IM/Lark、web manager | 决定能否进入真实 SDLC |

## 6. 对 Agent Harness / 职业主线的价值判断

### 如果 Trae CLI 具备完整非交互 agent runner

它可以成为 Agent Harness 的一个 worker backend：

- 同一任务分别用 Codex / Claude Code / Trae agent 执行。
- 统一采集 trajectory、tool trace、diff、test result。
- 对比不同 agent 的 memory-following、false completion、修复能力、token 成本。

这会直接增强 Agent Harness 的 runtime/eval 叙事：不是做一个单 agent demo，而是在做 agent worker harness + memory routing + trace/replay substrate。

### 如果 Trae CLI 只是 IDE chat 入口

它仍然有价值，但不应作为主线：

- 可作为人工开发入口或 IDE 辅助。
- 可观察其 MCP / mode / chat 设计，为 OpenClaw / Codex workflow 取经。
- 不投入大量工程适配，避免偏离 Agent Harness 主 artifact。

## 7. 建议下一步

1. 用户把第 4 节问题发给内部 owner / 群。
2. 拿到文档或答复后，补充到本文“内部确认结果”小节。
3. Codex 再基于确认结果决定：
   - 是否新增 `trae_worker_adapter` 设计 TODO。
   - 是否把 Trae 纳入 Agent Harness worker benchmark。
   - 是否只保留为 IDE/产品观察材料。

## 8. 当前 TODO 状态建议

- `todo-20260223-034039`：本机 baseline 已完成，等待内部信息确认，不应标 completed。
- `todo-20260225-001`：已形成 proactive/CLI 调研问题清单，等待内部信息确认，不应标 completed。

