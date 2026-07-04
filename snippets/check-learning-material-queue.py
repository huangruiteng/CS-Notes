#!/usr/bin/env python3
"""Validate the local learning-material priority queue structure."""

from __future__ import annotations

import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
CANDIDATES = ROOT / ".local" / "LEARNING_MATERIAL_CANDIDATES.md"
QUEUE_HEADING_RE = re.compile(r"^#{3,5}\s+当前\s*Top\s*30\s*列表\s*$", re.I | re.M)
QUEUE_END_RE = re.compile(r"^###\s+Top\s*30\s+外", re.I | re.M)

REQUIRED_ITEMS = [
    "`A126` Cursor",
    "`A170` Uni-Agent",
    "`A174` Agent Lightning",
    "`A165` Let It Flow / ROLL / iFlow-ROME",
    "`A17` RL Infra / FlashRL",
    "SGLang HiCache + LMCache + vLLM APC",
]


def fail(message: str) -> int:
    print(f"FAIL: {message}", file=sys.stderr)
    return 1


def main() -> int:
    if not CANDIDATES.exists():
        return fail(f"missing candidate file: {CANDIDATES}")

    text = CANDIDATES.read_text()
    if "Top20" in text:
        return fail("stale 'Top20' token remains in candidate library")

    heading = QUEUE_HEADING_RE.search(text)
    if not heading:
        return fail("missing current Top30 list heading")

    after_heading = text[heading.end():]
    end = QUEUE_END_RE.search(after_heading)
    if not end:
        return fail("missing Top30 outside/archive heading")

    section = after_heading[: end.start()]
    queue_lines = [
        match.group(0)
        for match in re.finditer(r"^[0-9]+\. .+$", section, re.M)
    ]
    numbers = [
        int(re.match(r"^([0-9]+)\. ", line).group(1))
        for line in queue_lines
    ]
    expected = list(range(1, 31))
    if numbers != expected:
        return fail(f"queue numbers are {numbers}, expected {expected}")

    queue_text = "\n".join(queue_lines)
    missing = [item for item in REQUIRED_ITEMS if item not in queue_text]
    if missing:
        return fail(f"missing required queue item(s): {missing}")

    print("learning material queue ok: Top30 is contiguous and required items are present")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
