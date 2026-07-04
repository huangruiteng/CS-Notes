- 完整文档: https://docs.openclaw.ai/cli
- Gateway 文档: https://docs.openclaw.ai/cli/gateway
- TUI 文档: https://docs.openclaw.ai/cli/tui
- 社区: https://discord.com/invite/clawd
- 技能中心: https://clawhub.com

Openclaw常用命令
📌 Shell 命令行
核心管理
  # 查看版本和帮助
  openclaw --version
  openclaw help

  # Gateway 服务管理
  openclaw gateway status          # 查看服务状态
  openclaw gateway start           # 启动服务
  openclaw gateway stop            # 停止服务
  openclaw gateway restart         # 重启服务
  openclaw gateway install         # 安装为系统服务
  openclaw gateway --force         # 强制启动（杀死占用端口的进程）

  # 健康检查
  openclaw gateway health          # 检查 Gateway 健康状态
  openclaw gateway probe           # 发现和探测所有 Gateway
  openclaw health                  # 快速健康检查
配置管理
  # 配置向导
  openclaw configure               # 交互式配置（凭证、设备、默认值）
  openclaw config                  # 配置助手（get/set/unset）
  openclaw config get              # 查看当前配置
  openclaw config set key value    # 设置配置项

  # 模型配置
  openclaw models                  # 查看和配置模型
消息发送
  # 发送消息到指定渠道
  openclaw message send --channel telegram --target @username --message "Hello"
  openclaw message send --channel whatsapp --target +8613800138000 --message "Hi"

  # 发送富文本/卡片消息
  openclaw message send --target @username --message "内容" --json

  # 查看消息状态
  openclaw status                  # 查看渠道健康状态和最近会话
会话管理
  # 列出会话
  openclaw sessions                # 列出所有存储的会话

  # 运行 Agent
  openclaw agent --to +8613800138000 --message "帮我总结" --deliver
  openclaw agent --local "写一段 Python 代码"  # 本地运行，不通过 Gateway
记忆和搜索
  # 搜索记忆
  openclaw memory search "关键词"  # 搜索 MEMORY.md 和 memory/*.md
  openclaw memory get path         # 获取指定记忆文件
Skill管理
  # 列出和管理技能
  openclaw skills list             # 列出已安装技能
  openclaw skills install <name>   # 安装技能
  openclaw skills update <name>    # 更新技能
其他实用命令
  # 日志查看
  openclaw logs                    # 查看 Gateway 日志

  # 浏览器管理
  openclaw browser status          # 查看浏览器状态
  openclaw browser start           # 启动浏览器

  # 定时任务
  openclaw cron list               # 列出定时任务
  openclaw cron status             # 查看定时任务状态

  # 节点管理
  openclaw nodes status            # 查看配对节点状态

  # 诊断和修复
  openclaw doctor                  # 健康检查 + 快速修复
 🖥️ TUI 快捷指令
 进入 TUI 后，你可以使用以下快捷指令（以 / 开头）：
Session会话控制
  /new           # 创建新会话
  /sessions      # 列出所有会话
  /switch <key>  # 切换到指定会话
  /clear         # 清空当前会话历史
  /delete        # 删除当前会话
Model模型和配置
  /model <name>  # 切换模型（如 /model gpt-4）
  /models        # 列出可用模型
  /reasoning     # 切换推理模式（显示/隐藏思考过程）
  /verbose       # 切换详细模式
系统操作
  /status        # 显示详细状态（使用量、成本、时间）
  /restart       # 重启 Gateway
memory记忆管理
  /memory <query> # 搜索记忆
  /memories       # 列出所有记忆文件
辅助功能
  /help          # 显示帮助信息
  /exit          # 退出 TUI
  /quit          # 退出 TUI（同 /exit）
特殊功能
  /think <level> # 设置思考级别（off|on|stream）
常用组合示例
  # 1. 启快速开发环境
  openclaw --dev gateway          # 启动开发 Gateway（隔离状态，端口 19001）

  # 2. 带消息启动 TUI
  openclaw tui --message "帮我总结今天的工作"

  # 3. 跨会话发送消息
  openclaw agent --to other-session --message "检查一下进度"

  # 4. 定时任务示例
  openclaw cron add --name "daily-report" --schedule "0 9 * * *" --message "生成日报"

  # 5. 查看使用成本
  openclaw gateway usage-cost      # 查看会话成本汇总