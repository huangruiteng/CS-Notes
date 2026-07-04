# Lark Derived Doc Sync Checklist

当飞书文档是从本地 canonical section 派生出来的，例如 `Notes/AI-Applied-Algorithms.md` 中的综述同步到飞书文档，按这个清单执行。

## 同步前

1. 明确 source of truth：
   - canonical local path
   - section heading
   - target Lark URL / token

2. 先 fetch 远端状态：
   - `docs +fetch --api-version v2 --scope outline`
   - 记录当前 `revision_id`

3. 检查远端评论：
   - 如果目标文档有未解决评论，不要直接 `overwrite`。
   - 先判断评论锚点是否会被改写；能局部更新就用 `block_insert_after` / `block_replace`，不能保锚点时先让用户确认。
   - 没有未解决评论时，派生综述类文档才适合从 canonical local section 整篇覆盖。

4. 生成 clean sync body：
   - 标题层级从 `#` 开始归一化
   - 去掉 draft-only frontmatter / review comments
   - 保留论文、repo、dataset、OpenReview 等来源链接
   - local-only 图片改成公开 URL 或“本地资源路径”说明
   - 块级公式转成 Lark 稳定格式，避免 `$$` 被误识别为标题

## 写入

1. 用最新 `revision_id` 做基准写入。
2. 优先使用 `--content @relative_file.md`，不要把长正文塞进 shell 参数。
3. 如果 Lark CLI 返回版本提示，记录但不要把它当失败。
4. `@file` 必须是当前工作目录内的相对路径；如果同步稿在 `/tmp/sync_body.md`，就 `cd /tmp` 后用 `@sync_body.md`，不要传绝对路径。

命令模板：

```bash
lark-cli docs +fetch --api-version v2 \
  --doc "$LARK_DOC_URL" \
  --scope outline --max-depth 3

lark-cli drive file.comments list \
  --params '{"file_token":"<DOC_TOKEN>","file_type":"docx","is_solved":false}'

lark-cli docs +update --api-version v2 \
  --doc "$LARK_DOC_URL" \
  --command overwrite \
  --doc-format markdown \
  --content @sync_body.md \
  --revision-id "$REVISION_ID"
```

## 同步后

1. 再 fetch outline，确认目录正常。
2. 用 1-3 个关键词 fetch，确认新增内容真的进入远端正文。
3. 对公式 / 图片密集段落做一次 keyword fetch，确认没有污染标题或掉成错误 block。
4. 回写本地同步证据：
   - 更新对应 local mirror 的 `source_revision_id`、`synced_at`、`sync_direction`。
   - 如果 mirror 是新目标，把它登记到 `MANIFEST.md` / registry 类文件。
   - 在 manifest 追加一条简短同步日志，记录同步原因、远端 revision、验证结果和特殊处理。
5. 在最终反馈中记录：
   - local canonical path
   - target Lark URL
   - remote revision
   - validation result

校验模板：

```bash
lark-cli docs +fetch --api-version v2 \
  --doc "$LARK_DOC_URL" \
  --scope keyword \
  --keyword "关键词1|关键词2" \
  --doc-format markdown \
  --context-before 1 \
  --context-after 1
```

## 常见坑

- `lark-cli` 如果在普通 shell 里找不到，先 `source ~/.zshrc`；不要把这类环境问题误判成飞书权限问题。
- `docs +update` 不支持 `--format json`；写入命令看退出码和返回 JSON 即可。
- `docs +update --content @file` 只接受当前工作目录内的相对路径。同步稿在 `/tmp` 时，先 `cd /tmp` 再传 `@sync_body.md`。
- 如果 overwrite 后 outline 里出现公式标题，通常是块级 `$$...$$` 被 Markdown 转换误识别；把飞书同步稿中的块级公式改成 `text` 代码块再写入。
