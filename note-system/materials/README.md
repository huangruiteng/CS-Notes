# 素材体系维护

公开目录保存可分享的书目、阅读提示、顺序和课程；原始材料、私人批注、来源审查与执行证据由维护者本地保管。公开克隆可以独立浏览、运行课程、校验和重建目录。

```text
来源读取 → 受管 catalog（ID / lifecycle / 全局排名）
                        ↓
              按版本审查公开字段
                  ↙             ↘
        公开当前队列             私有当前队列
    catalog.json + Markdown     本地 Markdown

历史归档：仍在原 catalog / backing，不进入公开当前队列
```

公开当前队列是同一 authority revision 下完整私有排名的保序子序列：字段审查可以让
条目留在私有侧，但不能改变其余公开条目的相对顺序。每个公开条目必须一一解析到
canonical material ref；需要隐藏私有来源标识时，导出 public-safe alias，子集与顺序校验
仍在 alias 解析后的 canonical refs 上执行。公开 rank 为过滤后的连续编号，不要求等于
全局 rank。任何公开条目无法解析、映射不唯一、顺序与全局排名不一致，或私有可读投影
绑定旧 authority revision，都属于投影错误，必须在发布或读取时拒绝。

## 数据与约束

| 层 | 职责 | 可公开内容 |
| --- | --- | --- |
| 来源 adapter | 读取与验证原文 backing、接入材料 capability | 接口约定；真实路径、provider 配置留本地 |
| 受管 catalog | 稳定 ID、生命周期、全局排名 | 本次不公开混合 catalog |
| 字段审查 | 判断每条材料可公开的范围，绑定正文及完整 record digest | 通用规则；逐条审查证据留本地 |
| 队列同步器 | 完整分区、分别编号、预览、版本检查、读回、回滚 | [material_queue_sync.py](./material_queue_sync.py) |
| 三方对账 | 区分共同基线、本地新增、远端缺失与双方冲突 | [material_reconcile.py](./material_reconcile.py)，只读计划，不生成归档 |
| 生命周期校验 | 逐条用户完成依据、误归档纠正、CAS、读回和回滚 | [material_completion.py](./material_completion.py)，provider/API 由来源入口注入 |
| 公开渲染器 | 校验卡片、生成 Top30 / backlog / 其余候选 | [material_queue.py](./material_queue.py) |

公开卡片只允许 `material_ref / title / sources / tier / lifecycle / read_scope / note / queue_rank`。不接受额外的原文或 provider 字段。新增或变更的记录默认进私有侧，必须重新审查；归档记录始终排除。审核同时绑定 `entry_digest` 与完整 record 的 SHA-256，不能只凭同一个 ID 或网址沿用公开许可。

本仓库的 `素材：` 工作流默认将经核验的公开来源在当次完成字段审查与公开队列导出；私有侧是审查前的安全落点，不是公开素材的默认完成位置。内部来源、私人批注与待确认内容继续留本地。读取范围按实际证据填写，公开卡片与完整原文分开。

用户读完与助手读取是两个状态。明确的用户完成记录应通过来源 authority 归档，保留稳定 ID、原来源、正文 backing 与归档证据，并移出当前排名；明确保留的已读参考注明复习用途，放入 backlog。拉取远端后，先核验并对账远端完成记录，再刷新本地投影；禁止用旧 authority 重建已经关闭的待阅读项。

Git 对账必须先核对共同基线、本地工作副本与远端。`local_addition` 是尚未提交的入库，不能误判成远端已归档；真正的远端缺条目也只是待核验 disposition。PR 的批次摘要、助手读取与已有笔记都不能替代对应材料的用户完成声明。只读三方计划与用户完成证据分别处理。

正文 hash 由来源 adapter 验证。record 的序列化约定见同步器 `canonical_json`：ASCII JSON、键排序、两空格缩进、末尾换行。审查输入包含 `scope=current_only`、授权依据 `owner_gate_ref`，以及每条记录的分类、理由、两个 digest 和可选 `public_card`。这是维护者的人工/agent 审查结果，不是按域名自动证明公开性的分类器。

若来源 ID 含私人语义，审查记录可指定稳定的 `public_material_ref`，仅在公开导出时替换 ID；完整分区与来源验证仍使用 canonical ID，映射只留本地。别名不得重复或占用其他 canonical ID。纯书名清单可引用 `Learning-Materials/booklists/` 中的 Markdown，不附原始截图或私人收集记录。

当前投影要求每个 ranked entry 只有一条主材料；组合条目须先完成语义拆分，否则拒绝生成。原材料 ID 不变，相同 URL 不自动合并；两个队列分别连续编号，保留各自原相对顺序。公开队列 rank 不等于混合 catalog 的全局 rank。

## 操作入口

自然语言入口是 [sync-notes](../../.codex/skills/sync-notes/SKILL.md)：`sync笔记` 默认同步后提交并 push 公开内容，`sync笔记，仅检查` 输出计划，`sync笔记，提 PR` 创建 PR。同步发现的已核验错误直接修复并回写默认流程。

维护者使用统一来源入口，不从历史任务脚本猜测当前身份：

```bash
python3 note-system/materials/material_source.py status
python3 note-system/materials/material_source.py complete --evidence <私有逐条完成声明.json> --phase prepare
# 检查预览，再使用输出的 plan_file；不能改成另一份计划。
python3 note-system/materials/material_source.py complete --plan <plan_file> --phase apply
python3 note-system/materials/material_source.py check
```

普通投影更新仍走同一入口的 `prepare / apply / check`。入口只读取项目显式注册的私有
source binding；缺失时报告 `material_source_not_configured`，不回退旧 Goal、借用其他
会话或创建临时 Goal。私有 adapter 负责既有 store、正文 backing、Core project context
与宿主授权的绑定；公开克隆不含这些配置，仍可使用下方纯公开校验。

原生 Codex 路径先读取真实宿主的活动 Turn 和现有工作区写策略，再由来源 adapter
映射到 Core 的普通项目上下文。此映射不创建 Bot Session 或授予新的文件权限；来源
profile 必须由 owner 显式启用，绑定工作区、store、操作范围与撤销状态。短期 gate
另绑定当前线程/Turn、具体操作、版本和有效期；staging 与 publication 内部再次核验，
不能只在入口检查一次。通用实现见 [来源 gate](./material_source_gate.py)。

归档保留全部原始记录、正文和剩余排名项的标题、阅读提示、证据及 entry ID，仅移除
已读项并连续编号；Top30、backlog 与计数随之刷新。人工补充的私有阅读页应按已核验的
素材身份合并，不能用一个简略的重生成页面覆盖旧批注。

fetch 后、pull 或刷新生成文件前，运行只读计划；upstream 使用当前实际引用：

```bash
python3 note-system/materials/material_reconcile.py --repo . --upstream origin/master
```

它绑定 merge-base、HEAD、已获取的 upstream commit、工作副本与暂存版摘要，完整校验三份卡片，分别输出 membership/metadata 差异及排名变化。输出 `lifecycle_transitions=[]`；它不 fetch、不写工作区、不验证用户是否读完，也不替代来源 authority。后续执行须重新核对这些 snapshot；发生并发变化时重新计划。

来源 adapter 合并已接受的远端顺序时，可复用 `material_reconcile.merge_ranked_orders`：本地独有条目沿用相邻的既有公共锚点，不按公开/私有数量比例重新穿插。只有新增时保留完整旧序列；远端明确重排共有条目时，遵循已接受的远端顺序并保留本地独有条目的相对顺序。调用前先解析 canonical alias、核验 lifecycle；远端缺失本身不删除材料，已归档材料也不因旧公开卡片而重写原始 backing。

公开克隆只需 Python 3.9+：

```bash
python3 note-system/materials/material_queue.py --check
python3 -m unittest discover -s note-system/materials/tests -p 'test_material*.py'
```

要修改公开渲染，在修改 `catalog.json` 后运行不带 `--check` 的渲染命令。本仓库维护者应先更新来源 authority 与审查，再同步投影；直接改公开副本会在下次同步中被检测为变化，不能代替来源更新。

连接来源时，由私有入口构造 `QueuePublisher(adapter)` 并调用 `.main()`。adapter 提供：

| 成员 | 约定 |
| --- | --- |
| `root / reviews / targets` | 私有工作目录、审查 JSON、四个输出的路径；配置不进入 Git |
| `current_pointer()` | 返回含 `authority_revision` 的当前指针 |
| `load_catalog(revision)` | 验证并读取该 revision；含 records 与 ranked entries |
| `load_material_content(catalog)` | 验证全部正文 backing，返回按 ID 索引的对象，提供私有标题 `.heading` |
| `build_projection(queue, contents, revision, count, now, name)` | 交给来源 capability 验证队列覆盖，返回 `(rendered, receipt)` |

连通后的入口支持 `prepare`、`apply`、`check`、`rollback --expected-queue-revision …`。可运行的合成 adapter 与故障用例见 [测试](./tests/test_material_queue_sync.py)；本机入口及具体回滚路径只记录在私有维护文档。

1. **Prepare**：读 catalog 与已审查字段，验证全部 backing；生成两队列预览、输出 hash 和源版本，绑定当前目标文件与投影指针。
2. **Apply**：同一发布锁内检查源版本、审查、目标文件与指针；先备份并演练恢复，再逐文件原子替换，读回后更新投影指针。重复 apply 返回 `no_change`。这里的“发布”仅指写入本机投影文件，不执行 Git commit、push 或 PR。
3. **Check**：检测源/审查过期或输出被编辑。修改文件后，应先比较差异，再重新 prepare，不能用刷新覆盖未审查的改动。
4. **Rollback**：指定当前投影 revision，先验证全部备份与旧指针，再恢复；不回滚 catalog 的 intake、生命周期或排名。

写入门禁应绑定实际调用宿主的活动 Turn，不能把普通 Codex 会话误当成“缺少 Bot Turn”。[Codex 宿主上下文读取器](./material_host_context.py)只读校验环境中的线程 ID、宿主索引、会话来源、工作区、活动 Turn 与写入策略，不创建 Session、Turn 或授权。来源 adapter 仍须核验当前 owner 与 App／工作区 grant，并把宿主上下文绑定到有期限、限定操作的 gate；换 Turn、撤权、只读或宿主信息不一致时拒绝，不回退借用其他宿主。真实线程信息和审计证据留在私有侧，不进入公开目录。

[授权证据读取器](./material_authority_read.py)将超时、连接故障、无效 JSON 和服务异常保留为 `AuthorityReadUnavailable`，将 HTTP 401/403 保留为 `AuthorityReadDenied`。两者都阻止依赖写入，且不自动重试；不将临时读失败吞成 verifier 的 `False`，也不向错误消息带出 URL、响应正文或底层异常中的私有信息。恢复后仍须重新读取同一 owner 的当前授权，不能用缓存 grant、旧 gate 或成功连通代替授权核验。

远端新增素材的同步使用同一注册来源入口：先保存拉取前的 Git commit，完成三方审查和 Git 合并后，运行 `material_source.py reconcile --base-ref <拉取前的commit> --public-ref HEAD --phase prepare`，审查返回的计划，再用 `reconcile --plan <私有计划路径> --phase apply`。adapter 必须显式支持这两个操作，并使用当前宿主权限；不能回退调用历史 Goal 脚本。[共享对账逻辑](./material_source_reconcile.py)分别形成 intake 和 ranking 版本，保留原始 backing、本地批注及未被远端收录的材料，用 Git 卡片记录已有读取范围，不冒充重读原文。旧归档不复活；其他 lifecycle 分歧需单独完成证据。apply 校验来源、审查记录与工作副本的 CAS，失败恢复来源、审查及投影；不保证强杀或掉电时多文件原子性。

可捕获的部分写入失败会恢复原文件；合成测试覆盖这条路径。多文件替换不是一个数据库事务，不承诺进程强杀或掉电时整体原子性，也不阻止绕过发布锁的手动编辑。发生此类中断时先检查私有备份、目标文件和指针，再修复投影；不得因此修改或覆盖来源 authority。

## 生命周期与经验复用

通用生命周期实现也在本目录。私有入口通过 `material_completion.settle(source, plan_path, phase, api)` 复用：source 负责 context、当前 gate、immutable catalog、正文核验与 authority CAS，api 提供序列化、inventory/receipt helpers 和既有 QueuePublisher。模块不导入 LoopX、不连接 Core、不创建身份或授权；实际能力与写入范围仍由调用 source verifier 限定。本机接入、正文、审查、备份与执行证据留本地。

完成计划绑定 source scope、authority revision、逐条 record digest 及私有 evidence digest。evidence 使用 `material_lifecycle_decisions_v1`，decisions 与 transitions 的 material ref 一一对应。归档为 `action=user_completed / actor=human_user / kind=user_statement`，附 statement 与 source_ref；核验后的远端声明用 `verified_remote_user_statement`，另附原 human message ref 与 remote commit。字段检查不能证明声明真实性；调用者仍须读取原声明，不能把助手的 PR 文案改标为用户话语。

纠正误归档绑定原 archive ref 与错误 completion evidence ref，只恢复原 archive 中的 lifecycle 和正文；保留旧审计，先恢复 backlog membership，再通过独立排名结算与重新公开字段审查。prepare 不改变 authority，apply 使用原生 gate/CAS 并验证投影；晚期发布或回执失败会恢复原 authority 与可验证输出。

通用代码和合成测试维护在仓库，不为每次同步另写本机专属脚本。公开测试覆盖未提交入库、远端删除仍需完成证据、冲突识别、错误批次证据拒绝、归档/纠正/回滚与晚期失败恢复，无需私有配置或已安装的 LoopX。

## 是否需要 LoopX 原生多队列

当前公开/私有分区共用生命周期、全局排名和维护者，现有 readable projection capability 已能分别验证两队列，无需修改核心。通用分区与文件同步逻辑公开，来源解析、材料内容、分类证据和个人排序依据保留本地。

如果以后出现独立 owner、独立生命周期/排序政策或不同 provider，再为 LoopX 增加一等 queue identity、membership 与授权契约。不要把当前两个展示分区当成独立权限系统，也不要把 receipt 的 `public_safe` 当作正文已经脱敏。
