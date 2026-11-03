---
name: sync-notes
description: Synchronize CS-Notes Git changes and material projections when the user says 同步笔记, sync笔记, or pull CS-Notes and push. Preserve unpublished intakes and require material-specific human completion evidence before archival.
---

# 同步笔记

把工作目录、远端提交和素材 authority 同步成可继续维护的状态。先遵循当前仓库 `AGENTS.md` 与私有补充；这是普通会话，不创建 Goal、自动化或其他线程。

## 指令

| 用户说法 | 执行范围 |
| --- | --- |
| `同步笔记` / `sync笔记` / `pull CS-Notes and push` | 拉取远端、保留有效本地改动、对账素材，验证后提交并推送公开内容 |
| `同步笔记，仅检查` | 获取远端引用并生成只读计划；不改变笔记、素材 authority、提交或推送 |
| `同步笔记，提 PR` | 同步后在 `codex/` 分支提交并创建 PR；合并沿用用户另行明确的授权 |

明确的目录、材料、提交粒度或排除项优先。同步不隐含用户读完材料，不为了同步重新评分整条队列。

## 同步路径

1. 看常用目录的分支、upstream、status、staged/unstaged diff 与未跟踪文件。对将被切换、恢复或合并的文件保存可恢复副本、原 Git revision 与 digest；临时备份及审计可以留本地，执行代码放仓库工具层。读取现有完成证据与 authority 版本。
2. `git fetch` 后，固定 `HEAD`、upstream 和 merge-base。在 pull 或刷新生成文件前运行三方素材计划：

   ```sh
   python3 note-system/materials/material_reconcile.py --repo . --upstream origin/master
   ```

   实际 upstream 优先，不写死切换到 master。脚本只读已获取的引用，校验完整公开卡片，输出稳定 ID 的新增/缺失/冲突与独立排名变化；不生成 lifecycle transition。若暂存版与工作副本不同，两者都核对。
3. 无冲突时 fast-forward；脏文件按共同基线逐文件或逐 hunk 合并。保留远端脱敏与修正，同时保留本地新增。既有本地提交和远端有分歧时做可审查合并，不能 force、批量 restore/reset 或以 stash 遗留掩盖内容。确有语义冲突才问不可替代的用户判断，继续独立部分。
4. 材料 authority 与 Git 是两个状态源。公开 catalog/Markdown 是投影，不能反向覆盖 authority。若项目已激活 Material Lifecycle，使用项目的 `loopx-material` 与 source adapter 对账：
   - 先运行 `python3 note-system/materials/material_source.py status`，通过项目注册入口解析当前宿主与来源；归档走该入口的 `complete --evidence … --phase prepare` 和 `complete --plan … --phase apply`。缺配置与真实撤权分别诊断，不搜索历史 Goal 脚本或借用其他会话。普通 Codex 会话可绑定宿主已有工作区写权限，不要求另建 Bot Turn。
   - `local_addition` 保留原 ID、body backing、读取范围和排序；远端缺少它不产生归档。
   - 本地或远端缺条目时，先查 source disposition 与逐条用户声明；远端 PR 的笼统“读完”、助手 read_scope 或 Notes 中出现摘要均不证明用户完成。
   - 已核验的用户完成声明才能通过现有 owner gate / CAS / receipt 改 lifecycle；材料级声明校验由 [共享实现](../../../note-system/materials/material_completion.py)维护。
   - 远端新卡片保留真实既有读取范围，不把摘要导入说成全文阅读。独立对账 lifecycle、intake 与 ranking，保留不相关材料顺序、并发新增和全部 backing。缺材料完成证据时保留当前状态，不阻塞无关笔记同步。
   - 已审查的远端卡片通过同一入口 `reconcile --base-ref <拉取前commit> --public-ref HEAD --phase prepare`，审查计划后 `reconcile --plan <返回路径> --phase apply`。该路径只接收卡片和排序，不推断完成；来源 adapter 须显式支持，不回退历史 Goal 脚本。
5. authority 结算后重新绑定公开字段审查，执行项目入口的 prepare/apply/check，再运行：

   ```sh
   python3 note-system/materials/material_queue.py --check
   python3 -m unittest discover -s note-system/materials/tests -p 'test_material*.py'
   git diff --check
   ```

   未激活或公开克隆没有 source adapter 时，保留 Git 对账结果，明确无法结算的 source 操作，不创建替代 authority；合法的公开内容仍可按授权提交。
6. 阅读最终 diff，确认没有材料无依据消失、重复 ID、未审查状态泄露和私有内容。按主题只暂存明确路径，遵循 `git-split-commit-pr`。默认完整指令已授权公开内容 commit/push；不要求重复确认，不借该指令授权公司内容、凭证、内部来源或外部消息。
7. 推送前核对当前 GitHub 账号、上游与已有 fork 的权限。上游 `push=false` 或一次明确的 403 只说明该账号不能直推上游，不代表不能提 PR。用户已要求提 PR 时，检查当前账号的已有 fork 是否确为同一上游且 `push=true`；核对目标分支、远端 head 和原授权范围后，正常推送到已有 fork，再以明确的 `--repo 上游 --base 原基线 --head 当前账号:分支` 创建 PR。先查询同 head 的现有 PR，发送结果不明时先读回，不重复推送或建 PR。不覆盖 `origin`、不 force push、不切账号或扩大权限；没有合适的已授权 fork 时说明精确缺口。单纯同步请求不借此新建 fork 或改成 PR。
   更新已有 PR 时，先读取其真实 `headRepository / headRefName / headRefOid`，核对该仓库权限与预期 head，再正常推到它的确切来源。主仓库存在同名分支或本地 upstream 指向主仓库，不代表该分支就是 PR 来源。推送后必须读回 PR head 与本地提交一致，才可报告更新成功或继续合并。
8. 核验远端 head 和常用 checkout 的实际状态，核验材料队列读回。完成报告包含提交链接、剩余改动或具体阻塞；不能只报告独立 worktree 干净。

同步中发现已核验的流程缺陷时，把修复落到现有 owner 的 AGENTS、skill 或工具层，并用原失误的合成反例验证。稳定规则与通用代码维护在仓库，私有配置和运行证据留本地；不要为每次同步另写本机专属脚本。
