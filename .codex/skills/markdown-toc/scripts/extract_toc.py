#!/usr/bin/env python3
"""Print a Markdown heading tree with line numbers."""

from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import Iterable, List, Tuple

Heading = Tuple[int, str, int]
HEADING_RE = re.compile(r"^(#{1,6})\s+(.*\S)\s*$")


def extract_toc(path: Path) -> List[Heading]:
    headings: List[Heading] = []
    fence = None
    for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        marker = re.match(r"^ {0,3}(`{3,}|~{3,})(.*)$", line)
        if marker:
            run, tail = marker.groups()
            if fence is None:
                if run[0] == "`" and "`" in tail:
                    continue
                fence = (run[0], len(run))
            elif run[0] == fence[0] and len(run) >= fence[1] and not tail.strip():
                fence = None
            continue
        if fence is not None:
            continue
        match = HEADING_RE.match(line)
        if match:
            level = len(match.group(1))
            title = match.group(2).strip()
            headings.append((level, title, lineno))
    return headings


def render_toc(headings: Iterable[Heading]) -> str:
    rows = ["TOC", "--------------------------------------------------"]
    for level, title, lineno in headings:
        indent = "  " * (level - 1)
        rows.append(f"{indent}{'#' * level} {title} (line {lineno})")
    return "\n".join(rows)


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: python3 extract_toc.py /path/to/file.md", file=sys.stderr)
        return 1

    path = Path(sys.argv[1]).expanduser()
    if not path.exists():
        print(f"Error: file not found: {path}", file=sys.stderr)
        return 1
    if not path.is_file():
        print(f"Error: not a file: {path}", file=sys.stderr)
        return 1

    headings = extract_toc(path)
    if not headings:
        print("No headings found.")
        return 0

    print(render_toc(headings))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
