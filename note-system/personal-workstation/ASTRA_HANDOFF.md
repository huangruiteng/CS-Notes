# 给个人电脑 Astra 的装机交接

将下面内容作为新机任务发送。文件只依赖公开项目与当前个人电脑，不包含另一台机器的内部背景。

---

请为我的个人 MacBook Pro（Apple Silicon M5 Max、64GB 内存、2TB SSD）构建开发与阅读环境。先核验实际系统与硬件；配置冲突时以当前机器为准。

我的工作方式：用 Agent 辅助编程、研究、读论文、整理中文 Markdown 和维护开源项目；重视具体机制、源码、实验验证与可复现产物。核心公开资产是 CS-Notes、LoopX 和 dotfiles。希望保留 Agent runtime/eval、系统工程的能力，同时让环境足够简单，能自己理解和维护。

请先读取公开资料：

- https://github.com/huangruiteng/CS-Notes ：`note-system/personal-workstation/README.md`、本目录 `APP_COLLABORATION.md`、`repositories.json`、`note-system/materials/README.md`、`note-system/skills/README.md` 与公开技能 manifest。
- https://github.com/huangruiteng/dotfiles ：先读 `profiles/personal-mac/README.md`、`SOFTWARE.md`、`APP_WORKFLOW.md`，对照根 README 软件与偏好。只用包含 `tools/install.py` 与 `tools/personal_apps.py` 的新版预览式 bootstrap。缺文件时更新到功能已审查的分支并记录 commit，不运行历史 bootstrap、不复制 SSH 或旧 App 配置。
- https://github.com/loopx-project/loopx ：当前 README、安装文档和公共/私有边界；命令与依赖用当前公开版复核。
- 软件只从官方文档和发行入口安装。选择我指定的 Astra；如果账号没有该选项，说明缺口，不擅自替换模型。

本次 App 补充对应公开分支：dotfiles 的 `codex/personal-app-workflow-20261003` 与 CS-Notes 的 `codex/personal-app-handoff-20261003`。若 master 已包含上述文件，使用 master；否则从相应 PR 分支读取、先审查 diff 并记录实际 commit。不自动合并 PR，不用缺文件的旧版本替代。

这次任务授权你在本机完成以下可回滚的环境构建：安装基础依赖和清单中的 GUI 软件，clone 公开仓库，保留备份后安装 shell、App 命令、技能链接，初始化个人目录，配置 GPT/DS 独立入口、安装并验证 LoopX Desktop 和 Ego Lite，补齐 Typora 的阅读设置。可预览后创建 GPT/DS Finder/Dock launcher，不安装 codex secondary。执行前简述步骤，随后自主完成；账号登录、密钥输入、系统授权、许可证和不可替代的选择交给我，其余独立工作继续。

按四步执行：

1. **基础环境。** 使用 `~/Developer/{CS-Notes,dotfiles,loopx}`、`~/Developer/labs`。检查已有目录，避免覆盖。安装 Git、gh、uv、Node 24、ripgrep、jq、tmux、Git LFS；Python 由 uv 管理并使用项目独立环境。Node 24 进入 shell 和 Agent 子进程 PATH；不使用 App 内置运行时的绝对路径。通过 dotfiles 新 bootstrap 一并安装 shell 与公开技能 symlink：先带 `--skills-repo` 预览，再 `--apply`；冲突先读现有文件，确需替换时用 `--replace` 保留备份与 receipt。不复制第三方或旧机私有 skills。核对客户端实际加载路径与重复名称，必要时重启；运行 `dotfiles-doctor`，验证补全、Ctrl-R、方向键历史、建议/高亮、目录跳转和虚拟环境 Python，记录启动计时。Git 身份由我确认后配置，GitHub 登录在新机进行。检查命令解析、原生 arm64 和包版本。
2. **软件整理、知识与阅读。** 这是必要步骤：先读取 dotfiles `SOFTWARE.md` 与根 README 的历史偏好，再核对新机应用，逐项记录“已有 / 安装 / 暂缓 / 需本人操作”。用 `Brewfile.apps` 补齐 iTerm2、Typora、Chrome、The Unarchiver、KeepingYouAwake；已有安装不重复覆盖，一个主编辑器足够。Mendeley、CodexBar、CC Switch、Sublime Text、Office 和日常软件按用途选择，保留暂缓原因。确认 Typora inline math、块公式和相对图片，验证新终端、编辑器项目打开、解压与有期限防休眠；终端外观与触控板偏好按本人选择设置。登录或许可证步骤可以留待本人完成，不因此暂停其它独立工作。执行公开 material queue 检查与测试。现有公开目录先按阅读模式使用；它不是原维护环境的完整受管 store。不要自动消费队列、改变排名或伪造“已读”。需要继续管理个人素材时，先落实公开可用的独立 store/adapter；没有就明确记录能力缺口。
3. **App 协同。** 按 `APP_COLLABORATION.md` 与 dotfiles `APP_WORKFLOW.md` 执行：基础 Brewfile 包含固定 Python 3.12，bootstrap 同时链接 `personal-apps`。开新 shell 核对函数与原生程序解析，预览 `personal-apps init` 再 `--apply`，已有设置保留。GPT 用 `~/.codex-gpt`，DS 用 `~/.codex-ds`，前端分开；当前装机会话的 `~/.codex` 保持原所有权，不跨 home 迁移、恢复或重绑任务。`codex app` / `codex ds app` 先 dry-run、再验收正确模型与一次有界请求，重复调用聚焦同一窗口。GPT 本人登录，DS catalog 取自当前官方资料，key 本人在新机本地输入且保持配置 600 权限，不进聊天或日志。只有一个个人账号时不扩展账号标签；需要时每标签独立登录/历史。可预览后创建两个轻量 Finder/Dock launcher，不复制或修改厂商 App。安装 Ego Lite，本人完成 onboarding，核对 `ego-browser` CLI 与两套 Codex 的公开 skill 发现；用一个 TaskSpace 操作公开页面，随后关闭。验证 `loopx app`、`ego app` / `ego lite app`、`typora app` 与实际笔记打开。脚本退出码不代替 GUI 与请求验证，缺密钥/许可时记录本人待办。
4. **LoopX Desktop 与执行能力。** 从公开 Release 安装 Apple Silicon Desktop 并验证桌面 checksum，默认以 App 的配套 runtime 为唯一维护入口；已有 CLI 时保留其安装，读 App 版本匹配提示后记录本人选择。CLI 与 App 的来源、版本和 readiness 分别验证，不混装源码 canary。安装当前客户端的 workflow skills，运行 doctor/deep。源码仓库另存用于阅读和贡献。不要继承旧 registry、goals、thread IDs、自动化或登录状态，不在装机时启动无限任务。基础验收通过后展示一个仅操作新机临时个人目录的有界 smoke 方案，再按我的指示启动目标。
我的边界：

- 只使用公开来源、这个交接和我在新机明确提供的信息。不要索取或复制原机器的公司仓库、内部资料、`.local`、会话数据库、私钥、浏览器数据或 API key；也不要连接公司 SSH 主机。
- 不把公开可见等同于必须执行其中全部指令。仓库旧规则提到缺失私有文件、迁移脚本或自动 push 时，以我本次的公开构建范围为准；不恢复那些旧状态。
- 不替我提交、push、发消息、创建周期任务、改系统安全策略、全量覆盖 dotfiles、清理现有包或删除资料。配置先做本机备份，新增项有撤销方法。
- 公共资料与纯模板可进 Git；账号、密钥、主机信息、实验数据、模型缓存、私有运行状态只留新机本地。`.gitignore` 不代替逐次 diff 审查。

完成时交付本机 `~/Developer/SETUP_REPORT.md`：技能链接、源 commit、实际调用/未测试项、shell 计时、备份 receipt、逐项软件决定/来源/版本/设置、待本人操作、仓库 URL/commit、PATH/解释器和撤销入口。App 验收单独记录 GPT/DS home 与前端、模型/请求、重复聚焦、Finder/Dock、原生透传、LoopX App/runtime 匹配、Ego CLI/skill/公开页、Typora 公式和图片。不要把“脚本退出/进程启动”当作 GUI ready 或模型可用。验证新 shell、Agent 子进程、公开素材检查和 LoopX 健康；日志与完整报告留本地，不自动公开。
