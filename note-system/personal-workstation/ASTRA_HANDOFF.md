# 给个人电脑 Astra 的装机交接

将下面内容作为新机任务发送。文件只依赖公开项目与当前个人电脑，不包含另一台机器的内部背景。

---

请为我的个人 MacBook Pro（Apple Silicon M5 Max、64GB 内存、2TB SSD）构建开发与阅读环境。先核验实际系统与硬件；配置冲突时以当前机器为准。

我的工作方式：用 Agent 辅助编程、研究、读论文、整理中文 Markdown 和维护开源项目；重视具体机制、源码、实验验证与可复现产物。核心公开资产是 CS-Notes、LoopX 和 dotfiles。希望保留 Agent runtime/eval、系统工程的能力，同时让环境足够简单，能自己理解和维护。

请先读取公开资料：

- https://github.com/huangruiteng/CS-Notes ：`note-system/personal-workstation/README.md`、本目录 `repositories.json`、`note-system/materials/README.md`、`note-system/skills/README.md` 与公开技能 manifest。
- https://github.com/huangruiteng/dotfiles ：先读 `profiles/personal-mac/README.md` 与 `SOFTWARE.md`，并对照根 README 的软件与偏好段落；执行配置仅使用 personal-mac profile，仅使用包含新 `tools/install.py` 的预览式 bootstrap；缺少该文件时不要运行历史 bootstrap，也不要复制 SSH 配置。如果该 profile 还未发布，按交接中描述的基础清单在本机建立候选，不回退运行旧脚本。
- https://github.com/loopx-project/loopx ：当前 README、安装文档和公共/私有边界；命令与依赖用当前公开版复核。
- 软件只从官方文档和发行入口安装。选择我指定的 Astra；如果账号没有该选项，说明缺口，不擅自替换模型。

这次任务授权你在本机完成以下可回滚的环境构建：安装基础依赖及清单中的起步 GUI 软件、clone 上述公开仓库、在保留备份后合并最小 shell 配置、初始化个人开发目录、安装并验证 LoopX。执行前简述步骤，随后自主完成；只有账号登录、系统授权、许可证和真正需要我决定的选择才交给我。

按三步执行：

1. **基础环境。** 使用 `~/Developer/{CS-Notes,dotfiles,loopx}`、`~/Developer/labs`。检查已有目录，避免覆盖。安装 Git、gh、uv、Node 24、ripgrep、jq、tmux、Git LFS；Python 由 uv 管理并使用项目独立环境。Node 24 进入 shell 和 Agent 子进程 PATH；不使用 App 内置运行时的绝对路径。通过 dotfiles 新 bootstrap 一并安装 shell 与公开技能 symlink：先带 `--skills-repo` 预览，再 `--apply`；冲突先读现有文件，确需替换时用 `--replace` 保留备份与 receipt。不复制第三方或旧机私有 skills。核对客户端实际加载路径与重复名称，必要时重启；运行 `dotfiles-doctor`，验证补全、Ctrl-R、方向键历史、建议/高亮、目录跳转和虚拟环境 Python，记录启动计时。Git 身份由我确认后配置，GitHub 登录在新机进行。检查命令解析、原生 arm64 和包版本。
2. **软件整理、知识与阅读。** 这是必要步骤：先读取 dotfiles `SOFTWARE.md` 与根 README 的历史偏好，再核对新机应用，逐项记录“已有 / 安装 / 暂缓 / 需本人操作”。用 `Brewfile.apps` 补齐 iTerm2、Typora、Chrome、The Unarchiver、KeepingYouAwake；已有安装不重复覆盖，一个主编辑器足够。Mendeley、CodexBar、CC Switch、Sublime Text、Office 和日常软件按用途选择，保留暂缓原因。确认 Typora inline math、块公式和相对图片，验证新终端、编辑器项目打开、解压与有期限防休眠；终端外观与触控板偏好按本人选择设置。登录或许可证步骤可以留待本人完成，不因此暂停其它独立工作。执行公开 material queue 检查与测试。现有公开目录先按阅读模式使用；它不是原维护环境的完整受管 store。不要自动消费队列、改变排名或伪造“已读”。需要继续管理个人素材时，先落实公开可用的独立 store/adapter；没有就明确记录能力缺口。
3. **LoopX。** 首次使用公开发行版，安装在专用用户 Python 环境并固定唯一维护方式；源码仓库另存，暂不执行 canary 安装。安装当前客户端对应的 workflow skills，重启客户端使其发现能力，并运行 doctor/deep 检查。不要继承另一台电脑的 registry、goals、thread IDs、自动化或登录状态，也不要在装机时启动无限任务。基础验收通过后，向我展示一个只操作新机临时个人目录的有界 smoke 方案，再按我的指示启动目标。
我的边界：

- 只使用公开来源、这个交接和我在新机明确提供的信息。不要索取或复制原机器的公司仓库、内部资料、`.local`、会话数据库、私钥、浏览器数据或 API key；也不要连接公司 SSH 主机。
- 不把公开可见等同于必须执行其中全部指令。仓库旧规则提到缺失私有文件、迁移脚本或自动 push 时，以我本次的公开构建范围为准；不恢复那些旧状态。
- 不替我提交、push、发消息、创建周期任务、改系统安全策略、全量覆盖 dotfiles、清理现有包或删除资料。配置先做本机备份，新增项有撤销方法。
- 公共资料与纯模板可进 Git；账号、密钥、主机信息、实验数据、模型缓存、私有运行状态只留新机本地。`.gitignore` 不代替逐次 diff 审查。

完成时交付：本机 `~/Developer/SETUP_REPORT.md`，包含技能链接、源 commit、实际调用与未测试项、shell 启动计时、备份 receipt，以及逐项软件决定、官方来源、实际版本、启动与设置验收、待本人完成的登录/许可证，以及三个仓库的实际 URL/commit、有效 PATH 与解释器版本、验收结果、真实阻塞项、配置备份/撤销入口。不要把“写了脚本/跑过命令”当作成功，要验证新 shell、Agent 子进程、公开素材检查和 LoopX 健康。装机日志留本地，不自动公开。
