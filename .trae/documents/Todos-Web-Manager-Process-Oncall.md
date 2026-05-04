# Todos Web Manager 进程不常驻 Oncall

> 对应 TODO：`todo-20260225-002`。结论：原问题不是单个 crash，而是旧启动方式本来就不是 daemon 化方案；同时 Flask debug reloader 与 `0.0.0.0` 会带来稳定性和安全问题。已将默认启动改为 localhost + debug off，并补充 launchd 常驻脚本。

## 现象

- 当前本机没有 `server.py` / `simple-server.py` 常驻进程。
- `lsof -nP -iTCP:5000 -sTCP:LISTEN` 没有监听者。
- `launchctl list` 中没有 `todos-web-manager` 相关 LaunchAgent。
- `.trae/web-manager/server.log` 只记录到一次 2026-04-07 的 Flask debug server 启动和一次 `POST /api/tasks`，没有 daemon supervisor 的生命周期日志。

## 根因判断

1. **旧方式是手动前台进程，不是常驻服务**
   - 文档和代码里主要写的是 `cd .trae/web-manager && python3 server.py`。
   - 这类进程会随 terminal/session 退出而退出，不具备登录后自动拉起、异常退出自动重启、日志固定落盘等 daemon 能力。

2. **Flask debug reloader 不适合当后台服务**
   - 旧代码使用 `app.run(host='0.0.0.0', port=5000, debug=True)`。
   - debug 模式会启用 reloader，启动时出现 `Restarting with stat`，进程模型变成 parent + child；用 `nohup`、shell background 或简单进程检查时容易误判，也更容易受文件变化影响重启。

3. **公网暴露风险和常驻方案必须一起修**
   - 之前的安全审查已经确认：Web Manager 有 TODO/Git 写操作 API，不能裸开公网。
   - 常驻方案应默认绑定 `127.0.0.1`，而不是为了“手机访问方便”直接监听 `0.0.0.0`。

## 已做改造

- `.trae/web-manager/server.py`
  - 默认 `WEB_MANAGER_HOST=127.0.0.1`
  - 默认 `WEB_MANAGER_PORT=5000`
  - 默认 `WEB_MANAGER_DEBUG=0`
  - 仅当显式设置 `WEB_MANAGER_DEBUG=1` 时开启 debug/reloader

- `Notes/snippets/todos-web-manager/start.sh`
  - 统一本地启动入口
  - 启动前检查 `flask` / `flask_cors` 是否存在
  - 默认只绑定 localhost
  - 日志目录：`.local/todos-web-manager/logs/`

- `Notes/snippets/todos-web-manager/launchd/com.huangrt.csnotes.todos-web-manager.plist`
  - `RunAtLoad=true`
  - `KeepAlive.SuccessfulExit=false`
  - `ThrottleInterval=30`
  - stdout/stderr 固定写入 `.local/todos-web-manager/logs/`

- `Notes/snippets/todos-web-manager/install-launchd.sh`
  - 安装并加载 LaunchAgent

- `Notes/snippets/todos-web-manager/uninstall-launchd.sh`
  - 卸载 LaunchAgent

## 使用方式

手动前台启动：

```bash
Notes/snippets/todos-web-manager/start.sh
```

安装为 macOS 登录后常驻服务：

```bash
Notes/snippets/todos-web-manager/install-launchd.sh
```

查看状态：

```bash
launchctl print gui/$(id -u)/com.huangrt.csnotes.todos-web-manager
lsof -nP -iTCP:5000 -sTCP:LISTEN
tail -f .local/todos-web-manager/logs/launchd.out.log
tail -f .local/todos-web-manager/logs/launchd.err.log
```

卸载：

```bash
Notes/snippets/todos-web-manager/uninstall-launchd.sh
```

## 后续建议

- 短期：只有明确需要 Web UI 时再安装 launchd；Codex 推进 TODO 不依赖 Web Manager。
- 中期：如果 Web Manager 继续保留，应做 read-only 默认模式、token 鉴权、CORS allowlist、静态文件 allowlist。
- 长期：Web Manager 更适合变成只读/观测控制面；任务执行主入口应继续迁移到 Codex 对话 + `.local/CODEX_TODO_TRIAGE_INDEX.md`。
