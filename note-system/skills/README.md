# 可移植的个人 skills

公开源文件维护在 `.codex/skills/`；[manifest.json](./manifest.json) 只列审查过的 11 个 skill 与每个文件的 SHA-256。这个清单是个人装机选集，不是整台电脑的技能备份。

| Skill | 保留的价值 | 本轮优化 |
| --- | --- | --- |
| [cs-notes-writing-style](../../.codex/skills/cs-notes-writing-style/SKILL.md) | 凝练、重机制与证据的中文写作 | 去掉特定项目历史与设备渲染路径，保留原意、协作标记和证据边界 |
| [help-me-review](../../.codex/skills/help-me-review/SKILL.md) | 沿调用链带读，解释为什么这样实现 | 分清发现与教学，移除私人项目专属检查项 |
| [git-split-commit-pr](../../.codex/skills/git-split-commit-pr/SKILL.md) | 脏工作区拆分、公开审查、独立 PR | 删除特定机器的合并例外，保留无关修改 |
| [cli-creator](../../.codex/skills/cli-creator/SKILL.md) | 可组合命令、稳定 JSON、认证与安装验收 | 按已装工具链选择语言，保留原 Apache 许可与参考文件 |
| [external-research](../../.codex/skills/external-research/SKILL.md) | 问题驱动研究，区分声称、观察、测试与推断 | 专项研究按需读 references，浏览器能力不是硬依赖 |
| [markdown-toc](../../.codex/skills/markdown-toc/SKILL.md) | 修改前看结构、行号和落点 | 路径正确引用，跳过代码围栏里的假标题 |
| [gourmet-organizer](../../.codex/skills/gourmet-organizer/SKILL.md) | 菜单归档、品鉴分析与真实经历对照 | 不编造实际感受，支持用户指定笔记，旧入口统一转向此版本 |
| [github-gh-cli](../../.codex/skills/github-gh-cli/SKILL.md) | GitHub 查询与结构化结果 | 保留小而清晰的工具入口 |
| [ai-hotspots](../../.codex/skills/ai-hotspots/SKILL.md) | 追一手来源的双语 HTML 日报 | 不为凑十条降低证据要求，不直接写旧素材队列 |
| [wechat-article-reader](../../.codex/skills/wechat-article-reader/SKILL.md) | 微信文章正文与关键图阅读 | 通过现有宿主读取，移除旧队列写入及专机脚本依赖 |
| [xiaohongshu-reader](../../.codex/skills/xiaohongshu-reader/SKILL.md) | 图片笔记阅读与来源核验 | 不自动提取登录态、安装第三方读取器或批量下载图片 |

两种社媒 reader 是工作流指引，需要客户端已有网页/浏览器读取能力；没有该能力或遇到访问限制时，必须报告缺口。它们不是已通过在线平台回归测试的独立爬虫。

## 从 dotfiles 安装链接

在稳定路径 clone 本仓库与 dotfiles。dotfiles 的 `bootstrap.sh` 负责 shell 与 skills 的统一安装；先预览，再执行：

```sh
cd "$HOME/Developer/dotfiles"
sh bootstrap.sh --skills-repo "$HOME/Developer/CS-Notes"
sh bootstrap.sh --skills-repo "$HOME/Developer/CS-Notes" --apply
```

只安装技能可加 `--skills-only`。默认链接到 `~/.agents/skills/<name>`；需要兼容旧客户端时用 `--skills-dir` 指定实际受支持目录，不要同时在多个发现目录创建同名副本。安装器不会下载插件、读取旧会话或覆盖冲突；已存在的目录需先审查，再用 `--replace` 做备份与替换。回滚入口在安装返回的本机 receipt 中。

[Codex 官方技能说明](https://learn.chatgpt.com/docs/build-skills#where-codex-loads-local-skills) 当前支持用户目录与技能目录 symlink。安装后在客户端核对发现结果；未刷新再重启。检查实际加载路径，尤其注意旧客户端可能也识别仓库 `.codex/skills`，不要让同名本地副本掩盖来源。

编辑已安装路径会修改本 checkout，直接出现在 `git diff`。这也意味着 checkout 后续变化立即影响运行：保持仓库可信，不自动 pull 或自动执行来源中的新命令。公开前审查正文、资源、引用与脚本；随后执行：

```sh
python3 note-system/skills/check.py --refresh
python3 note-system/skills/check.py
```

`--refresh` 只是重算文件清单与摘要，不是自动安全审查或发布许可。不要将凭证、私人材料或运行缓存放进 skill 目录。安装时会拒绝摘要不符、额外文件和源目录内的 symlink。

## 其余能力的处置

- LoopX 生成的 workflow skills 从公开 LoopX 安装器维护；不在这里复制一套分叉。
- 文档、浏览器、截图、开发工具等第三方能力从已确认的上游或客户端插件安装，保留许可证和各自维护入口，不搬整份安装缓存。
- 材料管线保留项目级 authority；这组选集不导出混合 catalog、私人排序背景或旧素材库。新机先阅读公开队列。
- 与组织平台、私有服务、旧会话恢复或专机运行环境绑定的 skills 留在原机。通用方法只有经过独立改写与验证才加入选集。
- 旧 Trae 工作流、实验性提示词和自带运行时暂不安装；确有需求再复核，避免重复触发与无用依赖。

## Astra 验收

核对 manifest、11 个链接与源 commit；确认改一个测试副本会进入对应 checkout 的 diff，测试后还原测试副本。检查客户端发现路径，试用一次 Markdown 标题提取、一次短文改写与一次只读代码带读。校验脚本通过不代表所有自然语言工作流效果已验证；报告实际调用和未测试范围。
