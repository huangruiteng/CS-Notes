# 学习素材

这里保存当前学习队列中的公开材料：论文、代码、官方文档、公开文章，以及可分享的自制讲义。长期知识结论仍归入 [Notes](../Notes/)。

- [学习队列：Top30 与 ranked backlog](./QUEUE.md)：建议阅读顺序，每条是独立学习单元。
- [其余候选](./CANDIDATES.md)：已收录但尚未排名，不把浏览序号当优先级。
- [机器可读目录](./catalog.json)：稳定材料 ID、来源、档位、生命周期、读取范围与队列内排名。
- [数据库与分布式系统补课](./distributed-systems-for-loopx/补课讲义.md)：17 节讲义，配套[练习与四周路线](./distributed-systems-for-loopx/练习与讨论.md)和[可运行实验](./distributed-systems-for-loopx/recovery_lab.py)。

S 表示优先亲读，A 表示先读摘要、按需追原文，B 表示背景索引，U 表示未读。这是学习分档，不是事实可信度评级。来源为二手观点或未核实线索时，仍需回到一手材料验证。

公开版只收录经过字段审查的书目、学习提示和公开链接。公司材料、私人批注、原始截图及无法确认公开性的资源留在私有队列；历史归档不在本目录展示。同一材料同时有公开论文和内部讨论时，公开版只引用可核验的公开来源。

“沿用既有阅读记录”表示迁移时保留原有材料入口，不表示本次重新精读了原文，更不表示学习者已掌握。正文未读、只看元信息、公开摘要页核验、全文审查和实验运行是不同状态。链接中的分享与登录参数已去除；旧链接可能失效，迁移不保证所有外链目前可访问。

公开目录是受管 catalog 的审查后投影；私有原文和审计证据不会从这里反向恢复。相同链接可能对应不同历史记录或阅读单元，按稳定 ID 保留，不静默去重。内外队列分别连续编号，保留各自原有相对顺序。

## 阅读与维护

从仓库根目录运行实验：

```bash
python3 Learning-Materials/distributed-systems-for-loopx/recovery_lab.py
```

从公开目录重建或检查 Markdown，不需要 LoopX 及维护者私有状态：

```bash
python3 note-system/materials/material_queue.py
python3 --no-user-site note-system/materials/material_queue.py --check
python3 -m unittest discover -s note-system/materials/tests -p 'test_material_queue*.py'
```

`catalog.json` 是公开副本的渲染输入，`QUEUE.md` 和 `CANDIDATES.md` 是生成文件。维护者新增、归档或调序时，先更新受管 catalog，再审查公开字段并刷新投影；不能只手改生成表格。未经审查的新记录、正文版本变化或材料重新激活，默认保留在私有侧，不能继承旧版本的公开许可。

分区、预览、版本检查、恢复与测试的通用代码也在仓库中，见[素材体系维护](../note-system/materials/README.md)；真实来源绑定与逐条审查记录留在本地。

目前两个队列共用材料生命周期与全局阅读顺序，再按公开范围筛选。它们不是独立的多租户权限系统，也没有第二套归档 authority。未来若需要不同 owner、独立排序政策或不同存储 provider，应再扩展 LoopX 的 queue identity 与授权契约；当前无需为展示分区重写核心 capability。
