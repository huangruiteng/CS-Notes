---
name: lark-cli-workflow
description: Coordinate Lark/Feishu CLI tasks from Codex. Use when a request involves Feishu/Lark docs, wiki, Drive files, Sheets, Base, Calendar, Minutes, IM, Mail, Tasks, Contacts, Slides, whiteboards, approvals, attendance, or when a Lark URL/token must be read, edited, summarized, routed, or turned into a real work artifact.
---

# Lark CLI Workflow

This is a thin routing skill. Prefer the official `lark-*` skills and `lark-cli` shortcuts for domain details; use this skill to choose the right path, identity, safety level, and final artifact shape.

## Default Route

1. Classify the object and action.
   - Docs / Wiki text: `lark-doc`, with `docs +fetch --api-version v2`.
   - Wiki hierarchy / members: `lark-wiki`.
   - Drive files, file permissions, comments, import/export: `lark-drive`.
   - Sheets: `lark-sheets`.
   - Base / Bitable: `lark-base`.
   - Calendar / meeting-room scheduling: `lark-calendar`.
   - Past meetings and transcripts: `lark-vc` or `lark-minutes`.
   - IM messages, groups, files in chats: `lark-im`.
   - Mail: `lark-mail`.
   - Contacts / people resolution: `lark-contact`.
   - Tasks, OKR, approval, attendance, slides, whiteboard: use the matching `lark-*` skill.
2. For any Lark URL or opaque token, inspect or unwrap it before acting.
   - Wiki URLs often point to a node wrapper; resolve the real object token before document fetch/update.
   - Do not assume a docx token, sheet token, bitable token, wiki node token, and drive file token are interchangeable.
3. Pick identity deliberately.
   - Use `--as user` for personal docs, Drive, calendar, mail, IM history, wiki spaces, and most user-owned resources.
   - Use `--as bot` only for app-owned resources or when the user explicitly wants an app identity.
   - If a command returns missing scopes, follow the CLI hint and request the minimum needed `auth login --scope ...`.

## Read Pattern

- Start narrow: outline, keyword, section, or metadata before full document fetch.
- For Docx v2, always pass `--api-version v2`.
- Use JSON output when the result will feed another command.
- If a document contains embedded sheets, bitables, synced blocks, media, or whiteboards, extract the referenced token and switch to the matching skill instead of summarizing the tag itself.
- Treat internal links, auth URLs, media URLs, access tokens, user IDs, and chat IDs as private unless the user explicitly asks for them in chat.

## Write Pattern

- Prefer real work artifacts: create or update the Lark doc, Base record, Sheet range, task, calendar event, email draft, or IM message instead of only producing copy-paste text.
- Before writing, identify the intended object, block/range/record, and command.
- Prefer block-level or section-level updates over whole-document overwrite.
- Preserve comments, highlights, citations, permissions, reviewer-visible formatting, and document structure unless the user asks to replace them.
- High-risk actions need explicit intent or a dry run first: delete, overwrite, permission change, bulk send, group membership change, task closeout, or external sharing.

## Repo Safety

- Do not write internal Lark URLs, temporary media/auth URLs, access tokens, chat IDs, internal people/team details, or non-public implementation details into tracked repository files.
- If an internal source has reusable public lessons, write only the generalized lesson and cite public/open sources when available, such as the Lark CLI public repository: https://github.com/larksuite/cli
- Put private source notes, exact internal links, and sensitive judgments under `.local/` when a local record is useful.
- For CS-Notes tasks, update `AGENTS.md`, `.trae/`, `.codex/skills/`, or `Notes/` only when the result improves the durable workflow; avoid demo-only files.

## Completion Check

- Say which Lark object was read or changed, using a safe title or type when links are sensitive.
- Report identity used (`user` or `bot`) when it matters.
- Mention missing permissions, unread embedded resources, or skipped high-risk actions.
- If `lark-cli` suggests an update, finish the current task first, then tell the user the update is available.
