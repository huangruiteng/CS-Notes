# 个人开发电脑：从公开资料重建

目标是形成可以重复搭建的个人开发与阅读环境。配置层在 [dotfiles 的 personal-mac profile](https://github.com/huangruiteng/dotfiles/tree/master/profiles/personal-mac)，知识与工作方式在本仓库，长程执行机制来自 [LoopX](https://github.com/loopx-project/loopx)。使用前确认相关 PR 已合并；若尚未合并，按 PR 指明的分支读取并记录 commit，不执行缺失 profile 的替代脚本。skills 链接安装还需 dotfiles 中的 `tools/install.py` 与本仓库的技能 manifest 同时存在；缺一项就先更新到相应已审查版本。

## 本人先做，随后交给 Astra

1. 完成 macOS 更新、个人 Apple 账号、密码管理和备份设置。开发目录使用 `~/Developer`，不要放进自动同步的文档目录。
2. 从 [OpenAI 官方桌面入口](https://learn.chatgpt.com/docs/app) 安装客户端，用个人账号登录并打开 Codex 工作界面，选择账号当前可用的 Astra。模型由客户端提供，不需要下载 Astra 模型权重；不要迁移另一台机器的 App 数据目录或登录文件。
3. 用系统 Terminal 执行 `xcode-select --install`，完成系统提示。按 [Homebrew 官方安装页](https://docs.brew.sh/Installation) 安装，并执行安装器给出的 shell 初始化命令。
4. 阅读习惯所需软件：[iTerm2](https://iterm2.com/)、[Typora](https://typora.io/)、一个代码编辑器（默认 [VS Code](https://code.visualstudio.com/docs/setup/mac)，已有偏好可换 Cursor）。它们可由 Astra 协助安装，本人只处理登录、授权和许可证。延续 Chrome 浏览偏好，并补 The Unarchiver、KeepingYouAwake；具体按下面的软件整理步骤执行。
5. 只 clone 三个基础仓库，或让 Astra 代做；把 [ASTRA_HANDOFF.md](./ASTRA_HANDOFF.md) 作为明确任务发送给新机 Astra。

```sh
mkdir -p "$HOME/Developer"
git clone https://github.com/huangruiteng/CS-Notes.git "$HOME/Developer/CS-Notes"
git clone https://github.com/huangruiteng/dotfiles.git "$HOME/Developer/dotfiles"
git clone https://github.com/loopx-project/loopx.git "$HOME/Developer/loopx"
```

若目录已经存在，先检查 Git remote 与状态，不覆盖，不再次套一层目录。HTTPS clone 公开仓库不需要先配置 SSH；写入 GitHub 的个人认证另行完成。

## 软件分层

| 层 | 起步选择 | 何时补充 |
| --- | --- | --- |
| Agent | 一个官方桌面客户端与个人账号 | 需要另一个模型或运行时再装 Claude Code 等 |
| 基础开发 | Git、gh、uv、Node 24、ripgrep、jq、tmux、Git LFS | 版本按目标仓库约束验证 |
| 阅读写作 | Typora、公开 CS-Notes 与 Learning-Materials | PDF 提取用 poppler；OCR 用 tesseract |
| 构建 | Python 项目独立 venv，Node 项目锁文件 | Rust、Go、CMake、Ninja 按源码需要装 |
| 容器 | 起步不要求常驻 VM | 有 Dockerfile 或测试依赖时用 Colima + Docker CLI；其他容器桌面二选一 |

LoopX 的公开安装文档目前要求 Python 3.11+、Node 22.22.3+，推荐 Node 24 LTS。先使用专用 Python 环境安装公开发行版，运行 `loopx workflow-skills --install` 与 `loopx doctor --deep`；源码 checkout 留作阅读和贡献。具体命令先核对 [安装文档](https://github.com/loopx-project/loopx/blob/main/docs/guides/installing-loopx.md)，选一个安装方式作为唯一维护入口，不把源码 canary 和发行版混装。

## 实用软件整理是装机必要步骤

先读 dotfiles 的 [软件与偏好清单](https://github.com/huangruiteng/dotfiles/blob/master/profiles/personal-mac/SOFTWARE.md)，同时对照根 README 中的软件与偏好段落。清单纳入终端、Typora、Chrome、解压、防休眠、文献管理、额度查看、多 provider 管理、办公及日常软件；根 README 只作历史参考，不执行旧安装与身份配置。

Astra 先盘点新机已有软件，逐项写出“已有 / 安装 / 暂缓 / 需本人操作”，再执行缺项安装。起步 GUI 用独立的 `Brewfile.apps`；Mendeley、CodexBar、CC Switch、Sublime Text、Office、个人通讯等按实际用途补充。同类编辑器选一个；搁置的 Hammerspoon / Karabiner 不自动恢复，来源未确认的同名工具先暂缓。

不仅安装软件，还要验收阅读和操作习惯：Typora inline math、块公式与相对图片；iTerm2 新 shell 与可选 Meslo / Pastel 外观；触控板轻点；编辑器打开项目；解压与有期限防休眠。原 README 的无限回看、旧浏览器扩展与整套 shell 插件是历史偏好，需要重新判断，不能批量导入。账号、许可证、浏览器 profile、应用数据库和组织托管设置在新机单独处理。

## Skills 与 shell 一起安装

读取 [技能选集](../skills/README.md)，通过 dotfiles `bootstrap.sh --skills-repo "$HOME/Developer/CS-Notes"` 预览，确认后加 `--apply`。技能用 symlink 指向仓库源文件，后续优化进入 Git diff；不用整目录迁移旧机 skills。已有配置冲突先审查，再按安装器的备份/回滚流程处理。

新版 dotfiles 直接加载 shell 插件并保留补全缓存。安装基础 Brewfile 后，验证 Ctrl-R、上下方向键、命令建议与高亮、`j` 目录跳转、虚拟环境 Python 和新 shell 的 PATH；用 `dotfiles-doctor` 与启动计时工具记录实际结果。软件偏好整理仍是必要步骤。

## 数据、素材与 Agent 状态

公开 clone 可以直接读笔记与队列，并运行：

```sh
python3 note-system/materials/material_queue.py --check
python3 -m unittest discover -s note-system/materials/tests -p 'test_material_queue*.py'
```

这不等于 clone 了完整素材 authority。`Learning-Materials/catalog.json` 是经审查的公开投影；原维护环境的混合 catalog、私有 adapter、内部来源和收据不在 Git 中。新机先以公开阅读模式运行，不能直接修改表格来伪造受管入库。若需要独立管理个人素材，使用公开的 LoopX Material Lifecycle 与 [adapter 契约](../materials/README.md) 初始化新的个人 store；确有公开启动能力缺口时记录缺口，不以复制另一台机器的私有目录补齐。

同样，公开 skill 可以重新安装，设备账号、密钥、浏览器会话、Codex 历史、全局 registry、旧自动任务和项目私有状态不能由 dotfiles 同步。个人机的新目标和周期任务在基础验收后按用户意图建立。

公开仓库中的操作示例不是本次执行授权。先看目标文件与脚本；缺少旧路径、旧工具或私有依赖时，不自动追到原电脑查找。安装过程中保留一个本机日志，完成后给出实际版本、通过项、阻塞项与回滚方法。
