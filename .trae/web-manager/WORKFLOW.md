# Todo Web Manager - 更新与同步工作流

## 📋 目录

1. [分层架构](#分层架构)
2. [更新工作流](#更新工作流)
3. [通用更新 vs 特定更新](#通用更新-vs-特定更新)
4. [使用指南](#使用指南)

---

## 分层架构

### 文件体系

```
CS-Notes/
├── .openclaw-memory/              # CS-Notes 专用（原始文件）
│   ├── MEMORY.md
│   ├── AGENTS.md
│   └── SOUL.md
├── .trae/
│   ├── rules/
│   │   └── project_rules.md       # CS-Notes 专用（原始文件）
│   └── web-manager/
│       ├── templates/              # 通用化模板（用于迁移）
│       │   ├── MEMORY-generic.md
│       │   ├── AGENTS-generic.md
│       │   └── project_rules-generic.md
│       ├── build.sh                # 构建脚本（使用模板）
│       ├── sync-templates.sh       # 同步检查脚本
│       ├── migrate.sh              # 一键迁移脚本（推荐）
│       └── WORKFLOW.md             # 本文档
```

### 分层策略

| 层级 | 位置 | 用途 | 更新频率 |
|------|------|------|----------|
| 原始文件 | `.openclaw-memory/`, `.trae/rules/` | CS-Notes 项目专用 | 高（日常更新） |
| 通用模板 | `.trae/web-manager/templates/` | 用于迁移到新项目 | 中（有通用更新时） |
| 构建产物 | `.trae/web-manager/todos-web-manager-package/` | 可迁移包 | 低（需要发布时） |

---

## 更新工作流

### 方式一：一键迁移（推荐）⭐

使用 `migrate.sh` 脚本，一句话搞定！

```bash
cd .trae/web-manager
./migrate.sh
```

或者直接对我说：**"迁移"** 或 **"打包"**，我会自动帮你运行！

**migrate.sh 会自动：**
1. 检查原始文件和模板的同步状态
2. 如果有更新，提示你编辑模板
3. 自动打开模板目录（macOS/Linux）
4. 确认后自动运行 build.sh 打包

---

### 方式二：手动分步

#### 完整流程

```
1. 更新原始文件
        ↓
2. 判断：通用更新？
        ├─ 是 → 3. 更新模板文件
        │         ↓
        │      4. 运行 build.sh 重新打包
        │
        └─ 否 → 结束（CS-Notes 专用，不影响模板）
```

#### 详细步骤

##### 步骤 1：在 CS-Notes 中更新

正常在以下位置更新：
- `.openclaw-memory/MEMORY.md`
- `.openclaw-memory/AGENTS.md`
- `.trae/rules/project_rules.md`

##### 步骤 2：运行同步检查

```bash
cd .trae/web-manager
./sync-templates.sh
```

这会检查原始文件和模板文件的修改时间，提示是否需要更新模板。

##### 步骤 3：判断更新类型

**通用更新**（需要同步到模板）：
- ✅ 添加新的最佳实践
- ✅ 改进工作流程
- ✅ 修复通用 bug
- ✅ 添加新的快捷指令
- ✅ 优化 P0-P9 优先级体系

**特定更新**（不需要同步到模板）：
- ❌ 修改 CS-Notes 特定的目录结构
- ❌ 添加 CS-Notes 专用的笔记整理规则
- ❌ 修改 CS-Notes 特定的文风规范
- ❌ 添加 CS-Notes 专用的项目目标

##### 步骤 4：更新模板（如果是通用更新）

手动编辑对应的模板文件：
- `templates/MEMORY-generic.md`
- `templates/AGENTS-generic.md`
- `templates/project_rules-generic.md`

确保：
1. 移除所有 CS-Notes 特定的内容
2. 使用占位符替代项目特定路径
3. 保持通用化的语言

##### 步骤 5：重新构建

```bash
./build.sh
```

生成新的可迁移包。

---

## 通用更新 vs 特定更新

### 示例对比

#### MEMORY.md - 通用更新

**原始文件（CS-Notes）：**
```markdown
### Git 操作 SOP
- 使用 snippets/todo-push.sh 和 snippets/todo-pull.sh
- 白名单：Notes/、.trae/、创作/
```

**通用模板：**
```markdown
### Git 操作 SOP
- 使用项目提供的 git 脚本（如果有）或遵循团队约定
- 根据项目需求配置白名单/黑名单
```

#### AGENTS.md - 通用更新

**原始文件（CS-Notes）：**
```markdown
- P0：最高优先级（笔记整理任务固定为 P0）
```

**通用模板：**
```markdown
- P0：最高优先级
```

#### project_rules.md - 通用更新

**原始文件（CS-Notes）：**
```markdown
* 你是一位笔记整理专家
* Notes/：可复用知识笔记
* 创作/：面向输出的写作
```

**通用模板：**
```markdown
* 请在此处定义你的项目角色和能力
* 请在此定义你的项目目录结构
```

---

## 使用指南

### 日常使用（CS-Notes 开发）

1. 直接更新原始文件
2. 不需要每次都更新模板
3. 只有当你确定更新是通用的，才更新模板

### 发布新版本（迁移到新项目）

1. 确保所有通用更新都已同步到模板
2. 运行 `./sync-templates.sh` 检查
3. 运行 `./build.sh` 构建
4. 使用生成的压缩包

### 新项目初始化

1. 解压构建产物到新项目根目录
2. 编辑 `.openclaw-memory/USER.md` 填入个人信息
3. 根据需要定制 `.trae/rules/project/project_rules.md`
4. 可选：进一步定制 `.openclaw-memory/MEMORY.md` 和 `AGENTS.md`

---

## 快速参考

| 任务 | 命令 | 推荐 |
|------|------|------|
| 一键迁移（推荐） | `./migrate.sh` | ⭐⭐⭐ |
| 检查模板同步状态 | `./sync-templates.sh` | |
| 直接构建可迁移包 | `./build.sh` | |
| 构建到指定目录 | `./build.sh /path/to/output` | |
| 对 AI 说："迁移" 或 "打包" | - | ⭐⭐⭐ |

---

## 最佳实践

1. **先更新原始文件**：始终在 CS-Notes 中先验证更新
2. **审慎更新模板**：确保更新是真正通用的才同步
3. **保留注释**：在模板中保留清晰的注释，说明哪里需要定制
4. **定期检查**：每周运行一次 `sync-templates.sh`，看看是否有遗漏的通用更新
5. **版本记录**：在模板文件末尾记录重要的更新历史
