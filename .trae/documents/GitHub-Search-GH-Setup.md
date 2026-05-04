# GitHub 搜索能力配置

> 对应 TODO：`todo-20260225-016`。本轮已安装 `gh` 并封装搜索脚本；剩余阻塞是 GitHub 账号授权，需要用户本人执行 `gh auth login`。

## 当前状态

- `gh` 已通过 Homebrew 安装：`gh version 2.86.0`。
- 用户已完成 `gh auth login`。
- `Notes/snippets/github-search.sh status` 已验证登录成功。
- repo / issue 搜索已完成烟测并返回结构化 JSON。

## 一次性授权

```bash
gh auth login
```

推荐选择：

- `GitHub.com`
- `HTTPS`
- `Login with a web browser`

登录状态验证：

```bash
Notes/snippets/github-search.sh status
```

## Codex / 本仓库可用搜索入口

封装脚本：

```bash
Notes/snippets/github-search.sh
```

示例：

```bash
# 搜开源仓库
Notes/snippets/github-search.sh repos "agent memory llm" 10

# 在指定仓库里搜代码
Notes/snippets/github-search.sh code "memory router" openai/codex 10

# 搜 issue
Notes/snippets/github-search.sh issues "memory" openai/codex 10

# 搜 PR
Notes/snippets/github-search.sh prs "eval" openai/codex 10
```

脚本行为：

- 会自动查找 `gh`、`/opt/homebrew/bin/gh`、`/usr/local/bin/gh`、`~/.local/bin/gh`。
- 未安装 `gh`：提示 `brew install gh`。
- 未登录：提示 `gh auth login`，退出码 `78`。
- 已登录：输出 JSON，方便 Codex 后续解析、筛选、落盘。
- `status` 子命令：打印 `gh --version` 与 `gh auth status`，用于登录前后自检。

## 对当前职业主线的价值

- 研究 Agent Harness / OpenViking / memory routing 时，可以快速检索相关 GitHub repo、issue、PR。
- 做开源贡献时，可以先搜 issue / PR，避免重复工作。
- 调研 vLLM / SGLang / verl / Ray 等 infra 项目时，可以直接把 GitHub 搜索结果接入学习材料管线。

## 后续

如果未来换机器、token 过期或搜索异常，重新执行：

```bash
Notes/snippets/github-search.sh status
Notes/snippets/github-search.sh repos "agent memory llm" 3
```

如果返回 JSON，说明 GitHub 搜索能力可用。
