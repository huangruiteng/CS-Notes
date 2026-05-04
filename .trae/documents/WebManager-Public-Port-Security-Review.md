# Todos Web Manager 公网暴露安全审查

> 结论：当前 `.trae/web-manager` 只能作为本机开发工具使用，不应直接开放公网端口。若确实需要远程访问，优先使用 SSH tunnel / Tailscale / 内网 VPN；若必须公网访问，至少需要反向代理鉴权、IP allowlist、关闭 debug、限制 CORS、禁用 Git 写操作和 CSRF / Origin 防护。

## 执行摘要

Todos Web Manager 不是生产级 Web 服务。它同时具备读取 TODO、修改 TODO、删除任务、审批任务、执行 `git add / commit / push / pull`、读取 diff / log、读取执行日志等能力。一旦暴露到公网，攻击者不需要登录就可能修改本仓库、触发 Git 操作、读取任务内容、获取执行日志，甚至在 Flask debug 暴露时触发远程代码执行风险。

因此当前建议是：

- **默认不要开公网端口。**
- 本机访问只绑定 `127.0.0.1`。
- 手机或外部设备临时访问时，用 SSH tunnel、Tailscale、内网 VPN 或 Cloudflare Access 这类带身份层的通道。
- 如果未来要保留 Web Manager，应该先做“只读模式 + 鉴权 + 本地绑定”三件事，再考虑其它功能。

## High / Critical Findings

### WMP-001：Flask debug + `0.0.0.0` 暴露风险

- Severity: Critical
- Location: `.trae/web-manager/server.py:1186`
- Evidence: `app.run(host='0.0.0.0', port=5000, debug=True)`
- Impact: Flask debug server 不应作为公网服务。`debug=True` 的交互式调试器一旦被外部访问，风险接近远程代码执行；`0.0.0.0` 又会让服务监听所有网卡。
- Fix:
  - 默认改为 `host='127.0.0.1'`。
  - 默认 `debug=False`。
  - 需要远程访问时通过 SSH tunnel / VPN 暴露 localhost，而不是让 Flask 自己监听公网。
- Mitigation: 若必须临时监听 `0.0.0.0`，也必须放在内网 VPN / Tailscale / SSH tunnel 后，并确保没有 debug。

### WMP-002：无鉴权的仓库写操作 API

- Severity: Critical
- Location: `.trae/web-manager/server.py:147-173`
- Evidence: `/api/git/add`、`/api/git/commit`、`/api/git/push`、`/api/git/pull` 均无鉴权。
- Impact: 攻击者可以对仓库执行 Git 写操作，最坏情况下把本地变更推到远端，或通过 pull 引入非预期状态。即使没有 shell 注入，业务权限本身已经过大。
- Fix:
  - 公网场景下默认禁用全部 Git mutation API。
  - 本机开发也建议加 `WEB_MANAGER_ENABLE_GIT_WRITE=1` 显式开关。
  - 若保留，必须有强鉴权、IP allowlist、审计日志和二次确认。

### WMP-003：无鉴权的 TODO / Plan 写操作 API

- Severity: High
- Location: `.trae/web-manager/server.py:455-542`、`.trae/web-manager/server.py:656-805`
- Evidence: `POST /api/tasks`、`PUT /api/tasks/<id>`、`PUT /api/tasks/<id>/status`、`POST /api/tasks/<id>/review`、`DELETE /api/tasks/<id>` 均无鉴权。
- Impact: 攻击者可以创建、篡改、删除任务，污染 TODO 系统；也可以把恶意内容写进 `progress` / `comment` 等字段，后续被 agent 或浏览器消费。
- Fix:
  - 公网场景下默认只读。
  - 写操作加鉴权、CSRF / Origin 校验、字段校验和审计。
  - 对 HTML 展示层保持转义，避免把写入内容变成 XSS 二次入口。

### WMP-004：全局 CORS 放开

- Severity: High
- Location: `.trae/web-manager/server.py:103`、`.trae/web-manager/simple-server.py:19-23`
- Evidence: `CORS(app)` 与 `Access-Control-Allow-Origin: *`
- Impact: 任意来源页面都可以从浏览器侧访问 Web Manager API。当前没有鉴权时，本身已经危险；未来如果加 cookie / token 鉴权而 CORS 仍全开，会进一步放大跨站请求风险。
- Fix:
  - 默认关闭 CORS。
  - 如果前后端分离，只允许固定 origin，例如 `http://127.0.0.1:5000`。
  - 写操作额外检查 `Origin` / `Referer`，并使用 CSRF token 或 bearer token。

## Medium Findings

### WMP-005：静态文件服务暴露 Web Manager 目录

- Severity: Medium
- Location: `.trae/web-manager/server.py:1150-1153`、`.trae/web-manager/simple-server.py:43`
- Evidence: `send_from_directory('.', path)`；`SimpleHTTPRequestHandler` 服务整个 `.trae/web-manager` 目录。
- Impact: 已知文件名可被读取，包括 `server.py`、`server.log`、历史 tar.gz 打包产物、配置文件等。SimpleHTTP 还可能提供目录列表。公网场景下这会暴露工具实现、日志和迁移包。
- Fix:
  - 只服务明确 allowlist 的前端文件，例如 `index-enhanced.html`、CSS、JS。
  - 不要把 `.py`、`.log`、`.tar.gz`、配置文件作为静态资源暴露。
  - 关闭目录列表。

### WMP-006：缺少 CSRF / Origin 防护

- Severity: Medium
- Location: 所有 state-changing route：`.trae/web-manager/server.py:147-173`、`.trae/web-manager/server.py:455-805`
- Evidence: 写操作直接读取 `request.json` 并执行，无 CSRF token、无 Origin 校验。
- Impact: 如果未来引入 cookie/session 鉴权，攻击者可诱导已登录浏览器发起跨站写请求。
- Fix:
  - 对所有 POST / PUT / DELETE 检查 Origin。
  - 使用 CSRF token 或 bearer token。
  - 将敏感写操作做成显式确认流程。

## 推荐部署模式

### 允许

```bash
python3 .trae/web-manager/server.py
# 只绑定 127.0.0.1，浏览器本机访问
```

或者：

```bash
ssh -L 5000:127.0.0.1:5000 <your-host>
# 本地浏览器访问 http://127.0.0.1:5000
```

### 不允许

```bash
python3 .trae/web-manager/server.py
# 同时 debug=True + host=0.0.0.0
```

```bash
ngrok http 5000
# 若没有额外鉴权，相当于把本地仓库管理 API 暴露给互联网
```

## 最小改造建议

1. 默认绑定 localhost：`WEB_MANAGER_HOST=127.0.0.1`。
2. 默认关闭 debug：`WEB_MANAGER_DEBUG=0`。
3. 新增只读模式：默认禁用 Git mutation 和 TODO mutation。
4. 新增 token：`WEB_MANAGER_TOKEN`，所有 API 请求必须带 `Authorization: Bearer ...`。
5. 限制 CORS：默认不开；必要时只允许配置的本地 origin。
6. 静态文件 allowlist：只暴露前端入口，不暴露 `.py`、`.log`、`.tar.gz`。
7. 如果还要远程访问，用 VPN / SSH tunnel / Cloudflare Access 做第一层身份边界。

## 当前 TODO 结论

`todo-20260225-021` 可以视为调研完成：当前 Web Manager 裸开公网端口有明确安全隐患，不建议继续推进公网暴露；若用户未来重新激活 Web Manager，应先做 localhost-only / read-only / auth-token 三件最小改造。

## 2026-05-04 跟进

`todo-20260225-002` 推进时已完成第一步最小改造：`.trae/web-manager/server.py` 默认改为 `127.0.0.1` + `debug=False`，并增加 launchd 常驻脚本。这个改动只解决“本地常驻”和 WMP-001 的默认暴露问题；TODO/Git 写 API、CORS、静态文件 allowlist、鉴权仍未完成，因此结论仍然是不应裸开公网端口。
