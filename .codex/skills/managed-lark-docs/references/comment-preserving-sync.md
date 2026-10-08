# Comment-Preserving Lark Sync

Read this reference when a managed Lark document has unresolved comments,
highlights, colored text, manual emphasis, reviewed tables, native cites, or
remote-only structure that must survive an update.

## Before Writing

1. Fetch the latest revision and outline.
2. Fetch the affected sections in XML with block IDs and full detail.
3. Fetch unresolved comments through the Drive comment API.
4. Map each comment quote and rich-text mark to its nearest block or text run.
5. Mark those blocks, inline spans, table cells, cites, and remote-only section
   boundaries as protected.
6. Diff the remote base against the local mirror. Preserve user edits, newer
   facts, reviewer responses, and clearer structure.

## Safe Operations

- Prefer insertion immediately before or after a protected block.
- Use exact text replacement only in an unprotected text run.
- Use block replacement only when no comment, mark, cite, or protected boundary
  is attached to that block or its descendants.
- For a commented table cell or inline value, inspect descendant text runs and
  preserve `comment_ids` on the original text element. If the API cannot do so,
  stop and report the blocker.
- Treat title metadata separately from body headings.

Do not use whole-document overwrite, broad Markdown replacement, or block
deletion across protected anchors unless the user explicitly accepts the loss.

## Partial Failure

Block operations may partially succeed. On an API error:

1. fetch the remote state again;
2. identify which operations landed;
3. resume from the first uncommitted operation;
4. never replay the entire script blindly;
5. record the warning in the local manifest and final report.

## Verification

After the write:

1. fetch the new revision and changed blocks;
2. compare the outline with the protected pre-write outline;
3. confirm unresolved comments still exist;
4. confirm comment anchors remain on the intended text/block, not only that the
   comment card count is unchanged;
5. confirm highlights, manual emphasis, table styling, and native cites remain;
6. update the local mirror and manifest from the verified remote state.

If a Markdown mirror cannot encode rich marks, record that those marks remain
Lark-only and keep the remote document authoritative for presentation.
