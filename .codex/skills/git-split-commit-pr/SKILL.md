---
name: git-split-commit-pr
description: Split mixed Git changes into public-safe, reviewable commits and PRs when the user requests publication or cleanup. Preserve unrelated work; merging is separate.
---

# 拆分提交与 PR

先检查 status、分支、remote、upstream、diff 和未跟踪文件。将路径分为功能代码、公开文档、验证、私有状态、无关修改。保留用户现有内容；需要隔离时从正确基线使用干净 worktree，不靠 reset 清场。

按评审者理解的功能切分，不按修改时间分组。同一文件混杂内容时做 hunk 级补丁；不把整份脏文件覆盖到远端最新版本。小规模重构只服务当前提交，避免顺便重写无关部分。

提交前逐项检查候选文件和 staged diff：凭证、私有 URL、设备路径、账号、内部项目细节、运行日志、图片元数据和引用目标。扫描命中需要人工判断；无命中不是公开安全的证明。只暂存明确路径，保留不确定项。

运行与改动相关的测试和 `git diff --check`，核对实际 staged 内容后提交。用户已授权的 push/PR 可以直接推进；默认分支前缀 `codex/`。PR 描述围绕问题、最终行为和验证结果，诚实标注未运行项与重要限制。

提交后验证远端 head 与本地一致；可用时将 PR 附到当前任务。合并需要用户授权并满足仓库规则，不因 PR 创建成功自动合并。不 force push，不为整理提交覆盖、删除或藏匿无关修改。
