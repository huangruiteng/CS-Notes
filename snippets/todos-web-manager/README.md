# Todos Web Manager Scripts

本目录收纳 CS-Notes/Codex 自用 TODO Web Manager 的本地启动和 launchd 常驻脚本。

- `start.sh`：前台启动本地 Web Manager，默认 `127.0.0.1:5000`。
- `install-launchd.sh`：安装并加载 macOS LaunchAgent。
- `uninstall-launchd.sh`：卸载 macOS LaunchAgent。
- `launchd/com.huangrt.csnotes.todos-web-manager.plist`：LaunchAgent 模板。

默认只绑定 localhost；不要把 Web Manager 直接暴露到公网。
