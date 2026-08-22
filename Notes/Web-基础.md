# Web 基础

[toc]

## PHP：超文本预处理器的本质与动机

### 动机：让网页“活”起来

最早的网页是纯 HTML，内容写死。1994 年，Rasmus Lerdorf 想在自己的个人主页统计访客、处理表单，纯 HTML 做不到；当时的 CGI 方案要把程序逻辑和 HTML 分开写，又麻烦又割裂。于是他写了一个小工具，允许把动态逻辑直接嵌进 HTML——这就是 PHP 的雏形，最初叫 Personal Home Page Tools，后来改名为 PHP: Hypertext Preprocessor（递归缩写：PHP = PHP: Hypertext Preprocessor）。

### 本质：服务器端先加工页面，再发给浏览器

PHP 是在服务器上执行的、专门用来生成 HTML 的脚本语言：

1. 浏览器请求 `.php` 页面；
2. 服务器让 PHP 解释器执行 `<?php ... ?>` 之间的代码；
3. 把执行结果和静态 HTML 拼成纯 HTML；
4. 浏览器只收到成品 HTML，永远看不到 PHP 源码。

所以叫“预处理器”：在超文本真正送出去之前先加工一遍。它更像页面模板引擎，而不是独立应用。

```text
浏览器请求 /index.php
        ↓
服务器 → PHP 解释器执行代码，输出 HTML
        ↓
浏览器收到纯 HTML，渲染页面
```

特点：

- 嵌入而非分离：HTML 与动态逻辑写在一个文件里；
- 服务器端执行：用户浏览器接触不到逻辑；
- Web 原生：`$_GET` / `$_POST` / `$_SESSION`、内置数据库接口，天生为网页请求设计；
- 门槛低：LAMP（Linux + Apache + MySQL + PHP）一套环境就能跑。

一句话：PHP 不生产网页，它是网页的加工车间。今天新项目很少首选它，但 WordPress 等大量存量网站仍由它支撑。

## 新项目用什么替代 PHP

没有单一继任者，按场景分化：

| 方向 | 代表 | 定位 |
|---|---|---|
| 低门槛全栈 | Node.js / TypeScript（Express、NestJS、Next.js） | 一门语言同时管前后端；Next.js 把 PHP 式的服务端渲染页面带回来了 |
| 好写、生态大 | Python（Django 全家桶、FastAPI 写 API） | 语法干净，适合逻辑不复杂的应用；优势在生态和易维护 |
| 性能优先 | Go（Rust / Axum 等） | 编译成二进制、并发好、部署简单，适合 API 服务和中规模后端 |
| 老牌复杂业务 | Ruby on Rails、Java / Kotlin（Spring） | Rails 曾代表更优雅的开发体验；Java/Kotlin 在大公司稳居主力 |
| 个人网站 / 博客 | 静态站生成器（Astro、Hugo）或继续用 WordPress | PHP 最初的地盘，如今很多人不再需要动态后端 |

### 范式变化：前后端分离 + 静态托管

PHP 时代的形态是“一个服务器把页面整个渲染好发给你”。现在很多新项目是：前端用 React/Vue 打包成静态页面，后端只提供 JSON API（Node/Python/Go 都行），部署到 Vercel、Netlify、Cloudflare 这类平台，甚至不用自己管服务器。

一句话总结：低门槛全栈 → Node/Next.js；好写 → Python；性能 → Go；大厂复杂业务 → Java/Kotlin。

## REST：Web API 的设计约定

REST（Representational State Transfer，表现层状态转移）不是协议，而是一套基于 HTTP 的 API 设计风格。核心思路：把业务对象抽象成「资源」，用 URL 定位资源，用 HTTP 方法表达操作，用状态码表达结果。

### 核心概念：资源、表现、无状态

- 资源（Resource）：一个可以被命名的业务对象，例如用户、订单、文章。
- URL 是名词不是动词：`GET /users/42` 表示“用户 42”，而不是 `/getUser?id=42`；URL 层级表达从属，如 `/users/42/posts`。
- 表现（Representation）：服务器返回的是资源的某种表现形式（通常 JSON），同一资源可以有多种表现。
- 无状态（Stateless）：每个请求自带全部上下文，服务器不保存客户端会话；登录态由客户端通过 Token / Cookie 携带。
- 可缓存 / 分层：GET 通常可缓存；客户端一般不关心请求是被应用服务器还是网关处理的。

### HTTP 方法与幂等

| 方法 | 语义 | 是否幂等 | 典型场景 |
|---|---|---|---|
| GET | 读取资源 | 是 | 查询列表 / 详情 |
| POST | 新建资源（或触发动作） | 否 | 创建订单 |
| PUT | 整体替换资源 | 是 | 用完整数据覆盖更新 |
| PATCH | 部分更新 | 协议不保证，常约定为可重复 | 只改一个字段 |
| DELETE | 删除资源 | 是 | 删除订单 |

幂等 = 同一个请求执行一次和多次结果一致。网络重试时只有幂等方法可以安全重放：GET / PUT / DELETE 可以，POST 不行（会创建重复资源），所以创建接口常用「客户端幂等键」或唯一约束兜底。

### 状态码速查

| 范围 | 含义 | 常见例子 |
|---|---|---|
| 2xx | 成功 | 200 OK、201 Created、204 No Content |
| 4xx | 客户端错误 | 400 参数错、401 未登录、403 无权限、404 不存在、409 冲突、422 语义校验失败 |
| 5xx | 服务端错误 | 500 内部错误、502 网关错误、503 服务不可用 |

设计惯例：错误响应也要有统一结构（error code + message + 可选的字段级详情），方便前端和调用方处理。

### REST 不是万能模板

- REST ≠ HTTP API：很多自称 RESTful 的接口只是把 CRUD 机械映射到 HTTP，没有真正按资源建模。
- 复杂动作放不进 CRUD 时，用「动作子资源」：`POST /orders/1/cancel` 比 `POST /orders/1?action=cancel` 更清晰。
- 需要按需取字段、跨实体聚合时，GraphQL 更合适；强类型、高性能的服务间调用，gRPC 更合适；REST 胜在简单、通用、浏览器和工具链天然支持。
- 团队要自己补的约定：版本化（`/v1/`）、分页（`?page=&size=`）、过滤排序、认证方式、错误格式——REST 本身不规定这些。

接口契约与前后端联调见 [Software-Engineering：前后端协作与接口联调](./Software-Engineering.md#前后端协作与接口联调)。

## 相关笔记

- [通信与网络](./通信与网络.md)：HTTP 与网络层基础
- [Software-Engineering：前后端协作与接口联调](./Software-Engineering.md#前后端协作与接口联调)
- [Database](./Database.md)：数据存储
