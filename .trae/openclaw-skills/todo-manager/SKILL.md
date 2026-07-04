---
name: todo-manager
description: Todo 管理 - 管理 CS-Notes 项目中的 todo 任务，包括任务创建、状态更新、优先级管理等功能。
---

# Todo Manager Skill

管理 CS-Notes 项目中的 todo 任务，包括任务创建、状态更新、优先级管理等功能。

## 核心功能

1. **Todo 管理** - 读取、创建、更新 todo 任务
2. **优先级管理** - 管理任务优先级（high/medium/low）
3. **状态跟踪** - 跟踪任务状态（todo/in-progress/done）

## 使用方法

### 运行 Todo 管理

```bash
cd /root/.openclaw/workspace/CS-Notes/snippets/
python3 todo-manager.py
```

### Todo 推送

```bash
./todo-push.sh
```

### Todo 拉取

```bash
./todo-pull.sh
```

## 重要原则

- 第一原则：公司项目文档绝对不能 push 到 git
- todo-push.sh 白名单机制：仅允许 `Notes/`、`.trae/`、`创作/` 三个文件夹
- todo-push.sh 黑名单机制：绝对禁止 `公司项目/` 文件夹
- 公司项目/ 目录规则：该目录下的所有内容永远不要 git add 到公开仓库
