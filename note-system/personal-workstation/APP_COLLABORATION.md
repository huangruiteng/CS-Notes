# 个人电脑的 App 协同交接

实现与完整步骤在 [dotfiles / APP_WORKFLOW.md](https://github.com/huangruiteng/dotfiles/blob/master/profiles/personal-mac/APP_WORKFLOW.md)：`tools/personal-apps`、`tools/personal_apps.py`、`shell/apps.zsh`。缺文件时更新到包含该功能的已审查分支并记录 commit，不回退到原电脑的私有脚本。

| 入口 | 用途 | Astra 验收 |
| --- | --- | --- |
| `codex app` | GPT 主窗口：开发、判断、研究、交接 | 个人账号和指定模型；重复调用只恢复同一窗口 |
| `codex ds app` | DS 独立窗口 | 正确模型、一次有界请求；GPT 配置与窗口不变 |
| `codex …` / `codex ds …` | 对应 home 的原生 CLI | 参数透传、CLI 与相应窗口状态根一致 |
| `loopx app` | 个人长程工作台 | Desktop readiness、配套 runtime 与终端 CLI 匹配 |
| `ego app` / `ego lite app` | Agent 浏览器 | `ego-browser` CLI、公开 skill 和公开页面操作 |
| `typora app` / `typora <file.md>` | 阅读与编辑笔记 | 实际文件、公式、相对配图、许可证 |

不安装 codex secondary。多词命令是 dotfiles 的 Zsh functions；`command codex` / `command loopx` 保留原生入口。只用公开资料重建，不拷贝原电脑的配置、账号、浏览器或会话。

## 新机执行顺序

1. 对照 dotfiles 软件清单与根 README 偏好，记录“已有 / 安装 / 暂缓 / 需本人操作”。Codex、LoopX Desktop、Ego Lite 从官方入口安装，Typora 用 `Brewfile.apps`。LoopX Desktop 不包含在 Python 包里。
2. 基础 Brewfile 包含 Python 3.12。新版 bootstrap 预览、链接 shell/App 命令/公开 skills，开新 shell 核对 `whence -v codex loopx ego typora` 与 `command -v personal-apps`。再执行 `personal-apps init` 预览、`init --apply`，不覆写本机已有设置。
3. GPT 默认 `~/.codex-gpt`，DS 默认 `~/.codex-ds`，前端也独立。已有 `~/.codex` 保持原会话所有权，装机 Astra 可继续在那里工作，之后在新 GPT 路由另建任务。不能复制 rollout/SQLite、跨 home 恢复或重绑旧任务。
4. GPT 本人登录、选择模型。DS 按当前 [官方集成说明](https://api-docs.deepseek.com/quick_start/agent_integrations/codex/) 在 DS home 建立 model catalog；key 由本人在新机本地输入，配置保持 600 权限。不直接运行默认覆写 `~/.codex` 的一键脚本。缺 key 时留本人待办，继续其它验收。
5. 每个 App 先 `--dry-run`，再开窗和验证行为。Codex 重复启动按 PID 聚焦，不按共享 bundle ID 猜窗口；在窗口内选择项目。跨 shell 用 `personal-apps open <role>`。
6. 需要 Dock 时预览、执行 `personal-apps shortcuts --apply`，生成 `~/Applications/Codex GPT Personal.app` 与 `Codex DS Personal.app`，已有入口保留。它们只调用脚本，不克隆或修改厂商 App；厂商图标仍走默认路由。

多个个人 OpenAI 账号仅按需配置：`personal-apps init --account a` 预览、加 `--apply` 创建，再 `codex app --account a` 登录。每标签独立历史，不交换认证，不导入旧机账号槽位映射或远端同步。只需一个个人账号时不扩展。

## 三个软件的补充步骤

**LoopX Desktop**：从 [Releases](https://github.com/loopx-project/loopx/releases) 选择 Apple Silicon DMG、核验桌面 checksum，读 [Desktop README](https://github.com/loopx-project/loopx/blob/main/apps/desktop/loopx-control-plane/README.md)。默认先以 App 的配套 runtime 为维护入口，fresh install 时 App 可准备 runtime；已有另一安装时保留并记录版本提示、本人选择。App 内更新处理 Desktop 和匹配 runtime，不另装 canary 抢 PATH。分别验证 App readiness、CLI 解析/版本/doctor，安装当前客户端的 workflow skills。不导入 registry、不创建周期任务。

**Ego Lite**：从 [官网](https://lite.ego.app/) 安装，本人完成 onboarding、选择新机个人 Chrome profile，不搬旧浏览器数据。App 提供 CLI/skill，按 [公开仓库](https://github.com/citrolabs/ego-lite) 补齐；核对 GPT/DS 的技能发现与重名。运行 `ego-browser nodejs -e 'console.log("ego-browser ready")'`，再按当前 skill 用一个 TaskSpace 打开公开页面，最后 `finish({keep: []})`。GUI 已打开不等于 Agent 集成成功。

**Typora**：通过命令打开一篇含公式、相对配图的公开笔记，验收 inline math、块公式、图片和许可证，不读取或提交激活数据。

## 证据与撤销

在新机 `~/Developer/SETUP_REPORT.md` 记录源 commit、版本、命令解析、GPT/DS home 与前端、模型和请求、重复聚焦、Dock、LoopX 版本匹配、Ego CLI/skill/页面、Typora 公式/图片及本人动作。安装、配置就绪、进程启动、GUI ready、模型请求分开判断；双 Codex 前端参数是自定义集成，上游升级后重新验收。

链接用 bootstrap receipt 回滚。init 不覆盖旧文件，新增路径另行列出且不在链接 receipt 内；撤销只审查新建且未承载数据的配置，已有登录/会话的 home 保留。新 launcher 关闭后可移到废纸篓。账号、密钥、profile、registry、任务状态和完整报告只留新机本地。
