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

## 数据与约束

| 层 | 职责 | 可公开内容 |
| --- | --- | --- |
| 来源 adapter | 读取与验证原文 backing、接入材料 capability | 接口约定；真实路径、provider 配置留本地 |
| 受管 catalog | 稳定 ID、生命周期、全局排名 | 本次不公开混合 catalog |
| 字段审查 | 判断每条材料可公开的范围，绑定正文及完整 record digest | 通用规则；逐条审查证据留本地 |
| 队列同步器 | 完整分区、分别编号、预览、版本检查、读回、回滚 | [material_queue_sync.py](./material_queue_sync.py) |
| 公开渲染器 | 校验卡片、生成 Top30 / backlog / 其余候选 | [material_queue.py](./material_queue.py) |

公开卡片只允许 `material_ref / title / sources / tier / lifecycle / read_scope / note / queue_rank`。不接受额外的原文或 provider 字段。新增或变更的记录默认进私有侧，必须重新审查；归档记录始终排除。审核同时绑定 `entry_digest` 与完整 record 的 SHA-256，不能只凭同一个 ID 或网址沿用公开许可。

正文 hash 由来源 adapter 验证。record 的序列化约定见同步器 `canonical_json`：ASCII JSON、键排序、两空格缩进、末尾换行。审查输入包含 `scope=current_only`、授权依据 `owner_gate_ref`，以及每条记录的分类、理由、两个 digest 和可选 `public_card`。这是维护者的人工/agent 审查结果，不是按域名自动证明公开性的分类器。

若来源 ID 含私人语义，审查记录可指定稳定的 `public_material_ref`，仅在公开导出时替换 ID；完整分区与来源验证仍使用 canonical ID，映射只留本地。别名不得重复或占用其他 canonical ID。纯书名清单可引用 `Learning-Materials/booklists/` 中的 Markdown，不附原始截图或私人收集记录。

当前投影要求每个 ranked entry 只有一条主材料；组合条目须先完成语义拆分，否则拒绝生成。原材料 ID 不变，相同 URL 不自动合并；两个队列分别连续编号，保留各自原相对顺序。公开队列 rank 不等于混合 catalog 的全局 rank。

## 操作入口

公开克隆只需 Python 3.9+：

```bash
python3 note-system/materials/material_queue.py --check
python3 -m unittest discover -s note-system/materials/tests -p 'test_material_queue*.py'
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

可捕获的部分写入失败会恢复原文件；合成测试覆盖这条路径。多文件替换不是一个数据库事务，不承诺进程强杀或掉电时整体原子性，也不阻止绕过发布锁的手动编辑。发生此类中断时先检查私有备份、目标文件和指针，再修复投影；不得因此修改或覆盖来源 authority。

## 是否需要 LoopX 原生多队列

当前公开/私有分区共用生命周期、全局排名和维护者，现有 readable projection capability 已能分别验证两队列，无需修改核心。通用分区与文件同步逻辑公开，来源解析、材料内容、分类证据和个人排序依据保留本地。

如果以后出现独立 owner、独立生命周期/排序政策或不同 provider，再为 LoopX 增加一等 queue identity、membership 与授权契约。不要把当前两个展示分区当成独立权限系统，也不要把 receipt 的 `public_safe` 当作正文已经脱敏。
