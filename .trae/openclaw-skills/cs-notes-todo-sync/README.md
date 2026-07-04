# CS-Notes Todo Sync Skill

OpenClaw Skill，用于拉取 Git、扫描任务、生成执行提示。

## 功能

- 调用 `snippets/todo-pull.sh`
- 拉取 Git 最新代码
- 扫描 Inbox 中的新任务
- 生成待执行任务提示清单

## 安装

1. 将此目录复制到 `~/.openclaw/workspace/skills/cs-notes-todo-sync/`
2. 确保 CS-Notes 仓库已克隆到 `~/.openclaw/workspace/CS-Notes/`

## 使用

```bash
python main.py
```

## 目录结构

```
cs-notes-todo-sync/
├── skill.json    # Skill 配置文件
├── main.py       # 主程序
└── README.md     # 说明文档
```

