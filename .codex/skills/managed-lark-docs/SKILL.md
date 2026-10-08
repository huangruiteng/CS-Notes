---
name: managed-lark-docs
description: Maintain and patch existing Lark/Feishu documents while preserving comments, highlights, citations, and newer remote edits. Use for iterative document updates, local-mirror sync, or durable project ownership; LoopX integration is optional.
---

# Managed Lark Docs

This skill manages a Lark document as a durable project material, not as a
one-off text-editing target. It is repository-neutral and works without LoopX.
Project-specific document conventions come from the owning project.

## Core Model

A managed Lark document has four distinct surfaces:

1. **Remote source:** the Lark doc and its current revision, comments, rich-text
   marks, cites, title, and outline.
2. **Project authority:** the owning project's document policy and, when already
   connected to LoopX, its goal and redacted authority source registration.
3. **Local working state:** an ignored mirror and manifest under the owning
   project's `.local/` directory.
4. **Publication surface:** any intentionally tracked, shared, or public
   derivative. This is opt-in and must pass the project's privacy boundary.

Do not collapse these surfaces. In particular, a local mirror is not
automatically a Git artifact, and a registry entry stores lineage and authority,
not the private body or raw source URL.

## Non-Negotiable Defaults

- Resolve the owning project before creating a mirror. Resolve a LoopX
  `goal_id` only when the project already uses LoopX for this material.
- When the project is connected to LoopX, register the source with
  `loopx register-authority-source`; do not rely on chat memory or a repository-
  specific document catalog alone.
- Store private or internal mirrors under
  `<project-root>/.local/managed-lark-docs/<source-id>/` by default.
- In a Git project, verify the target path with `git check-ignore -v` before
  writing. Stop if it is not ignored. Outside Git, use an owner-approved private
  directory rather than a published or shared folder.
- Never put a new private managed document in a tracked `docs/` path merely to
  obtain a diff or registry entry.
- A Git-tracked mirror is allowed only when the user explicitly asks for one,
  the repository declares that document family as tracked authority, and the
  content is safe for that repository's audience.
- Treat the remote Lark doc as current truth unless the user explicitly names a
  canonical local source. A local canonical source still does not authorize
  erasing newer remote edits or reviewer signal.
- Preserve unresolved comments, highlights, manual emphasis, native cites, and
  clearer remote-only section boundaries.
- Use the narrowest safe remote write and fetch again after writing.
- Never store credentials, access tokens, raw private source bodies, or private
  operational links in Git or public-safe LoopX projections.

## Required Skills

- Read and follow `lark-doc` before fetching or updating a document.
- Use `lark-drive` for comments, title metadata, permissions, and comment
  anchor checks.
- Use `lark-shared` for identity, authentication, and missing scopes.
- When the project is connected to LoopX, read and follow
  `loopx-doc-registry` and [LoopX integration](references/loopx-integration.md).
- When editing this skill, use `skill-creator` and run its validator.

If an official `lark-*` skill is absent, try the installed CLI
`lark-cli skills read <skill-or-reference-path>` for its bundled instructions.
If neither source is available, report the missing prerequisite and hold the
affected operation. Do not install tools, change authorization, or invent API
parameters merely to make this skill available.

## Project And Authority Resolution

Find the owning repository from the user's named project, target document
context, or current working directory. Reuse its current document policy and
choose a stable, public-safe `source_id`; keep private names and raw URLs only
in the local manifest. Do not pick a project from historical usage.

For a project already connected to LoopX, follow
[LoopX integration](references/loopx-integration.md). Otherwise keep the private
mirror and manifest without requiring a Goal or registry. Do not bootstrap or
connect a project as a side effect of document editing.

## Local Layout

Use this default layout:

```text
<project-root>/.local/managed-lark-docs/<source-id>/
├── manifest.json
├── mirror.lark.md
└── drafts/                 # only when a separate review draft is useful
```

The mirror filename may use XML or another loss-aware format when Markdown
cannot represent the document faithfully. The manifest should contain only
local/private state and use a small contract such as the following. Omit
`goal_id` for projects without LoopX:

```json
{
  "schema_version": "managed_lark_doc_local_manifest_v0",
  "source_id": "stable-source-id",
  "goal_id": "owning-goal-id",
  "boundary": "local_private",
  "source_url": "raw private URL allowed only in .local",
  "remote_revision": 12,
  "remote_revision_observed_at": "ISO-8601 timestamp",
  "mirror_path": ".local/managed-lark-docs/stable-source-id/mirror.lark.md",
  "mirror_sha256": "sha256",
  "mirror_status": "remote_readback_verified",
  "git_policy": "ignored_local_only",
  "conflict_rule": "Remote/current-code authority rule"
}
```

After every remote update, refresh the revision, timestamp, digest, status, and
any local supporting-artifact references. Do not copy raw private values from
this manifest into LoopX's public-safe status or Git artifacts.

## Managed Update Workflow

### 1. Establish Freshness

Before drafting or writing:

1. Fetch the current title, revision, and outline.
2. Fetch only the relevant sections when the request is narrow; fetch the full
   document when a broad rewrite or structural comparison requires it.
3. Check unresolved comments and nearby rich-text marks when the change touches
   reviewed content.
4. Compare the remote revision and outline with the local manifest and mirror.
5. Classify remote-only changes as `preserve`, `merge`, `ask_user`, or
   `explicit_replace`. Default to `preserve` or `ask_user`.

When the remote revision is newer, it becomes the base for that sync. Do not
overwrite it from an older local mirror.

### 2. Plan The Change

Write for the reader, not as a work log:

- integrate evidence into stable sections;
- preserve useful original claims and citations;
- distinguish verified fact, inference, proposal, and open gate;
- avoid timestamped assistant logs unless the document is itself an execution
  log;
- prefer replacing or compressing stale material over endlessly appending;
- keep private evidence in `.local` and expose only generalized conclusions on
  shareable surfaces.

Use the target document's voice by default. Apply a personal style corpus such
as CS-Notes only when the user requests it or the document family declares it.
Sample enough representative writing to infer structure and rhythm; do not
mechanically copy private phrasing.

### 3. Update The Local Review Surface

Update `mirror.lark.md` first when the user wants a reviewable local diff. A
separate draft is optional and should be created only when:

- the user asks to see a draft first;
- the rewrite is broad and remote sync is not yet approved;
- a standalone memo is the requested artifact; or
- the mirror format is too loss-aware or noisy for comfortable review.

For private documents, the review surface remains in `.local`; reviewability
does not require Git.

### 4. Respect The Remote Write Gate

If the user asked only to draft, refine locally, or show a preview, stop before
the Lark write. If the current request explicitly says to update/sync the Lark
document, that is sufficient intent for the scoped write after freshness and
boundary checks.

Summarize the planned sections, protected anchors, and unresolved ambiguity
before a broad rewrite. Ask only when the ambiguity affects authorship,
authority, privacy, or destructive replacement.

### 5. Apply The Narrowest Safe Write

Read the official `lark-doc` update and format references for the installed CLI.
Fetch the affected XML with full detail before a preservation-sensitive edit.
Build a small patch plan from the current remote state and revision.
Use the observed base revision when the installed API supports it. If a write
reports a revision conflict, fetch and merge the new remote state before retrying.

Prefer, in order:

1. exact inline replacement in an unprotected block;
2. block insertion around protected content;
3. block replacement of an unprotected section;
4. whole-document overwrite only when the document has no protected reviewer
   signal and the user explicitly approved replacement.

Never use a Markdown overwrite merely because it is convenient. A request to
"sync", "polish", or "reorganize" does not authorize clearing the document.
Native doc cites should remain cites; comments and marked text are not
disposable formatting.

`str_replace` searches the whole document: verify every match and choose block
operations when the text is ambiguous or spans multiple blocks. Read back after
each patch round before planning another structural edit; replacement can
invalidate block IDs. A successful response is not proof that anchors survived.
Inspect `partial_success`, warnings, and actual remote state before retrying;
never replay a partially applied batch blindly.

Read `references/comment-preserving-sync.md` before changing content with
comments, highlights, manual emphasis, tables with review anchors, or native
Lark cites.

### 6. Verify And Write Back

After writing:

1. Fetch the new revision and affected sections.
2. Fetch the outline and confirm protected section boundaries still exist.
3. Recheck unresolved comments and touched anchors where applicable.
4. Confirm native cites and marked spans survived.
5. Refresh the ignored mirror and local manifest.
6. When already integrated with LoopX, update the registered source revision
   and relevant state through its existing owners. See
   [LoopX integration](references/loopx-integration.md).

Do not claim `synced` when only one section was updated while other mirror
sections remain local-only. Report a precise partial-sync status instead.

## Privacy And Git Decision

| Situation | Default location | Git? |
| --- | --- | --- |
| Private/internal Lark body | project `.local/managed-lark-docs/` | No |
| Raw URL/token/revision manifest | same ignored local directory | No |
| Redacted source identity and authority | project LoopX registry | Registry only |
| Generalized reusable conclusion | project docs, after boundary review | Explicit decision |
| Existing tracked document family | repository-declared path | Only if its profile and audience permit |

Before any tracked write, scan for internal actors, private links, raw tokens,
credentials, local absolute paths, screenshots, and source bodies. If a private
mirror was mistakenly committed, move the live mirror to the owning project's
ignored local state, remove the current Git projection through a normal review
change, and report that prior Git history still retains it. Never rewrite
history without explicit owner approval and coordination.

## Writing Guardrails

- Write as if the document is authored by the user or project, not as if an
  assistant is explaining its edits.
- Remove drafting phrases such as `建议改写`, `给你 review`, `这里应该`, and
  process narration from the final body.
- Prefer direct claims over correction frames like `不是 X，而是 Y` when a
  positive statement is clearer.
- Explain abstract systems with one concrete end-to-end or failure case.
- Keep links and citations near the claims they support.
- Preserve enough context for a new reader; do not assume prior chat history.
- Keep evidence boundaries explicit and avoid turning hypotheses into shipped
  facts.
- Do a whole-document phrase and privacy scan before remote sync.

## Output Standard

Report:

- owning project and stable `source_id`;
- LoopX goal and redacted authority topic only when already integrated;
- local mirror/manifest paths and proof they are ignored;
- remote revision before and after;
- sections changed and protected signal preserved;
- any partial-sync, access, privacy, or history-retention caveat;
- tracked repository changes, if any, as a separate explicit surface.

Do not expose raw private URLs, tokens, source bodies, credentials, or local
private evidence in public summaries.
