# 笔记管理系统

这里集中维护笔记库的管理代码、规则与验证，不放学习材料正文。当前先收拢素材队列管理；后续笔记索引、整理校验等能力有实际改动时再逐步迁入。

| 位置 | 内容 |
| --- | --- |
| [materials/](./materials/README.md) | 素材公开/私有分区、目录校验、Markdown 生成、同步与回滚 |
| [personal-workstation/](./personal-workstation/README.md) | 从公开仓库重建开发环境、Codex GPT/DS 与 App 协同、软件清单及 Astra 交接 |
| [Learning-Materials/](../Learning-Materials/README.md) | 当前公开素材目录、阅读顺序、讲义与实验 |
| [Notes/](../Notes/) | 整理后的长期知识笔记 |
| [skills/](./skills/README.md) | 可移植技能选集、公开审查清单与 dotfiles 链接安装 |
| 维护者本地状态 | 私有来源、混合 catalog、审查记录与运行证据，不进入 Git |

从仓库根目录验证：

```bash
python3 note-system/materials/material_queue.py --check
python3 -m unittest discover -s note-system/materials/tests -p 'test_material_queue*.py'
```

通用代码与合成测试必须能在公开克隆中运行，不能隐式依赖维护者本机目录、登录状态或 LoopX 安装。接入真实来源所需的 adapter 由本地配置提供；公开/私有边界和具体接口见 [materials 维护说明](./materials/README.md)。
