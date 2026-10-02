---
name: markdown-toc
description: Extract a Markdown heading tree with line numbers before editing or integrating notes. Use when you need to inspect a long Markdown file quickly and choose the best insertion point instead of editing blind.
---

# Markdown TOC

## Use this skill when

Use this skill before editing a long Markdown file, especially when you need to:
- inspect the heading structure quickly;
- choose the best section for new content;
- avoid creating redundant sections; or
- review nearby lines before patching a note.

## Quick start

Resolve `{baseDir}` to this skill’s actual directory, then run the bundled script. It reports ATX (`#`) headings, excluding fenced code; Setext headings and full Markdown parsing are outside its scope:

```bash
python3 "{baseDir}/scripts/extract_toc.py" /absolute/path/to/file.md
```

In this repository, common targets include:

```bash
python3 "{baseDir}/scripts/extract_toc.py" Notes/Gourmet.md
python3 "{baseDir}/scripts/extract_toc.py" "Notes/AI-Agent-Product&PE.md"
```

## Workflow

1. Run the TOC script on the candidate file.
2. Read the returned heading tree and line numbers.
3. Open the most likely section neighborhood with `sed -n '<start>,<end>p'` or `nl -ba`.
4. Insert into an existing section when possible.
5. Create a new section only when the file truly lacks a clean landing spot.

## Output format

The script prints a compact tree like this:

```text
TOC
--------------------------------------------------
# Title (line 1)
  ## Section (line 20)
    ### Subsection (line 42)
```
