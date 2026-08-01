#!/usr/bin/env python3
"""Check local Markdown links in snippets docs."""

from __future__ import annotations

import re
import sys
from pathlib import Path


LINK_RE = re.compile(r"\[[^\]]+\]\(([^)]+)\)")
SCHEME_RE = re.compile(r"^[a-zA-Z][a-zA-Z0-9+.-]*:")


def is_local_link(link: str) -> bool:
    return not (
        SCHEME_RE.match(link)
        or link.startswith("#")
        or link.startswith("/")
    )


def strip_fragment(link: str) -> str:
    return link.split("#", 1)[0].split("?", 1)[0]


def check_file(path: Path) -> list[str]:
    missing: list[str] = []
    text = path.read_text()
    for raw_link in LINK_RE.findall(text):
        link = raw_link.strip()
        if not is_local_link(link):
            continue
        target = strip_fragment(link)
        if not target:
            continue
        if not (path.parent / target).exists():
            missing.append(f"{path}: missing {raw_link}")
    return missing


def main() -> int:
    root = Path(__file__).resolve().parent
    files = [Path(arg) for arg in sys.argv[1:]] or sorted(root.glob("*.md"))
    all_missing: list[str] = []
    for path in files:
        all_missing.extend(check_file(path))

    if all_missing:
        print("\n".join(all_missing))
        return 1

    print(f"checked {len(files)} file(s), all local links exist")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
