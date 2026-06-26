---
name: workspace-netdrive
description: 检测并管理挂载在工作区 /root/.openclaw/workspace/ 下的网盘（TOS 存储桶挂载）。当用户提到网盘、TOS、TOS 桶、TOS bucket、存储桶、对象存储、对象存储桶、桶、bucket/buckets、bucket 名、桶列表，或需要将文件上传到 TOS、保存到 TOS 桶、保存到桶里、把结果传到 TOS、落盘到对象存储、检查挂载桶、列出可用桶时使用此技能。
metadata:
  version: "1.0.4"
  openclaw:
    emoji: "💾"
    requires: { "bins": ["df", "grep"] }
---

# 工作区网盘技能 (Workspace Netdrive Skill)

此技能帮助你检测和使用挂载在工作区内的网盘（TOS 存储桶挂载）。当用户提及文件操作时，应当优先到网盘内查找文件，用户输入的文件名不够精确时，可模糊匹配查找。

## 何时使用

当用户要求执行以下操作，或提到与网盘等价的相关词汇时使用此技能：
- "检查是否有挂载的网盘"
- "把这个文件保存到网盘/TOS"
- "将输出存储到云存储桶挂载"
- "列出可用的存储桶"
- "帮我看一下 TOS / TOS 桶 / 存储桶 / 桶 / 对象存储 / 对象存储桶"
- "把文件放到桶里 / 上传到 bucket / 保存到 buckets / 保存到 TOS 桶"
- "上传到 TOS / 把结果传到 TOS / 落盘到对象存储 / 存到桶里"
- "看下 bucket 名 / 看下桶列表 / 列一下 bucket"

如果用户提到 `TOS`、`TOS 桶`、`TOS bucket`、`存储桶`、`对象存储`、`对象存储桶`、`桶`、`bucket`、`buckets`、`bucket 名`、`桶列表`，且语义上是在说持久化存储、挂载目录、上传下载文件、查看可用桶、把结果落到桶里，也应按“网盘”场景处理。

## 检测逻辑

网盘通常挂载为 `/root/.openclaw/workspace/` 下的子目录。
检测脚本使用 `df` 和 `grep` 来检查该目录下的挂载点。

## 指令

### 1. 检测可用网盘

运行此脚本以列出所有已挂载的网盘路径和桶名称：

```bash
scripts/detect_mounts.sh
```

**输出示例:**
```text
Detected network drives (Buckets):
Bucket: my-bucket (Path: /root/.openclaw/workspace/my-bucket)
Bucket: reports-bucket (Path: /root/.openclaw/workspace/reports-bucket)
```

如果未发现网盘，输出将是：`No network drives mounted in workspace.`

> **注意：** 如果未检测到网盘，你**必须**提示用户在 **arkClaw 界面菜单栏中**配置网盘（配置TOS存储桶信息），然后才能继续。

### 2. 保存文件到网盘

一旦识别出有效的挂载路径（例如 `/root/.openclaw/workspace/my-bucket`），你可以直接将文件保存到该路径。

**复制文件:**
```bash
cp source_file.txt /root/.openclaw/workspace/my-bucket/folder/
```

**直接写入网盘:**
```bash
echo "内容" > /root/.openclaw/workspace/my-bucket/output.txt
```

### 3. 反馈

向用户反馈文件存储位置时，**请勿**使用内部文件系统路径（例如 `/root/.openclaw/workspace/...`）。
而应该反馈 **桶名称 (Bucket Name)** 和 **相对于桶的路径**。

**反馈示例:**
> "文件已成功保存。
> **桶名:** my-bucket
> **路径:** folder/source_file.txt"

这种格式方便用户在外部系统中访问这些文件。

## 禁止操作说明
- **禁止任何情况下执行umount和mount命令** 来尝试挂载或卸载网盘，这些操作会导致系统不稳定。
- **网盘路径出现IO错误时** 可提示用户检查WEB页面的网盘配置和重新确认配置来触发挂载：网盘配置 -> 更改 -> 确定，等待后台重新连接挂载，WEB页面稳定后，可重新检测网盘是否可用。
- **禁止向用户索要TOS AKSK自行挂载存储桶**，如果用户需要使用TOS存储桶，请引导用户在WEB页面配置网盘。
- **禁止操作fusedaemon、fusemonitor相关进程和系统服务**，这些进程和服务由网盘内部管理，用户不应感知或干预它们的运行状态，因此作为Agent，你也不应该执行任何与这些进程和服务相关的操作。
