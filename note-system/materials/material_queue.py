#!/usr/bin/env python3
"""Validate and render a reviewed public learning queue using only stdlib.

This consumes published cards, never private source ledgers. Classification
and publication review belong to the local source adapter, not this renderer.
"""

import argparse
import ipaddress
import json
import re
from pathlib import Path
from urllib.parse import parse_qsl, unquote, urlsplit

SCHEMA = "learning_material_queue_v1"
CARD_FIELDS = {
    "material_ref",
    "title",
    "sources",
    "tier",
    "lifecycle",
    "read_scope",
    "note",
    "queue_rank",
}
READ_SCOPES = {
    "unread",
    "metadata",
    "abstract",
    "recorded_review",
    "full_text",
    "executable_tested",
}


def text_field(value, name, limit=600):
    if not isinstance(value, str) or not value.strip() or len(value) > limit:
        raise ValueError(f"invalid {name}")
    if any(c in value for c in "\n\r\0<"):
        raise ValueError(f"{name} contains control or markup characters")
    if re.search(r"(^|[\s(])(?:/Users/|/home/)|file://|\.local/|公司项目/", value):
        raise ValueError(f"{name} contains a private/local locator")


def validate_source(source):
    text_field(source, "source", 2048)
    if ">" in source:
        raise_suspicious_source()
    p = urlsplit(source)
    if not p.scheme:
        path = unquote(p.path)
        if not path.startswith("./distributed-systems-for-loopx/"):
            raise ValueError("local sources must be reviewable course artifacts")
        if ".." in Path(path).parts or p.netloc or p.query or p.fragment:
            raise_suspicious_source()
        return
    if p.scheme not in ("http", "https") or not p.hostname or p.username or p.password:
        raise_suspicious_source()
    if p.port or p.fragment or "\\" in source:
        raise_suspicious_source()
    if p.hostname == "localhost" or p.hostname.endswith((".local", ".internal")):
        raise_suspicious_source()
    try:
        ipaddress.ip_address(p.hostname)
    except ValueError:
        pass
    else:
        raise_suspicious_source()
    # Only identity parameters needed by these public source services survive.
    allowed = {
        "www.youtube.com": {"v"},
        "openreview.net": {"id"},
        "news.ycombinator.com": {"id"},
        "qwen.ai": {"id"},
    }.get(p.hostname, set())
    if any(k not in allowed for k, _ in parse_qsl(p.query, keep_blank_values=True)):
        raise ValueError("unreviewed query parameter in source")


def raise_suspicious_source():
    raise ValueError(
        "source must be a credential-free public URL or approved relative artifact"
    )


def validate(catalog):
    if set(catalog) != {"schema_version", "queue_id", "top_window_size", "entries"}:
        raise ValueError("unknown catalog fields")
    if catalog["schema_version"] != SCHEMA or catalog["queue_id"] != "external":
        raise ValueError("unsupported public queue schema")
    window = catalog["top_window_size"]
    if type(window) is not int or window < 1:
        raise ValueError("top_window_size must be positive")
    if not isinstance(catalog["entries"], list):
        raise TypeError("entries must be a list")
    refs, ranks = [], []
    for card in catalog["entries"]:
        if set(card) != CARD_FIELDS:
            raise ValueError("unknown or missing card fields")
        ref = card["material_ref"]
        if not isinstance(ref, str) or not re.fullmatch(r"material-[a-z0-9-]+", ref):
            raise ValueError("invalid material_ref")
        refs.append(ref)
        text_field(card["title"], "title", 300)
        if card["note"]:
            text_field(card["note"], "note")
        elif card["note"] != "":
            raise ValueError("note must be text")
        if card["tier"] not in ("S", "A", "B", "U"):
            raise ValueError("invalid tier")
        if card["lifecycle"] not in ("candidate", "unread", "active", "carryover"):
            raise ValueError("public catalog includes an archived or invalid record")
        if card["read_scope"] not in READ_SCOPES:
            raise ValueError("invalid read scope")
        if not isinstance(card["sources"], list) or not card["sources"]:
            raise ValueError("at least one source required")
        for source in card["sources"]:
            validate_source(source)
        rank = card["queue_rank"]
        if rank is not None:
            if type(rank) is not int or rank < 1:
                raise ValueError("invalid rank")
            ranks.append(rank)
    if len(refs) != len(set(refs)):
        raise ValueError("duplicate material_ref")
    if sorted(ranks) != list(range(1, len(ranks) + 1)):
        raise ValueError("queue ranks must be unique and contiguous")
    return {
        "materials": len(refs),
        "ranked": len(ranks),
        "unranked": len(refs) - len(ranks),
        "top_window": min(window, len(ranks)),
    }


def cell(value):
    return (
        value.replace("\\", "\\\\")
        .replace("|", "\\|")
        .replace("[", "\\[")
        .replace("]", "\\]")
    )


def row(card, position):
    links = " · ".join(
        f"[来源 {i}](<{url}>)" for i, url in enumerate(card["sources"][1:], 2)
    )
    title = f"[{cell(card['title'])}](<{card['sources'][0]}>)"
    label = {
        "unread": "未读",
        "metadata": "仅元信息",
        "abstract": "公开摘要页已核验",
        "recorded_review": "沿用既有阅读记录",
        "full_text": "本次全文审查",
        "executable_tested": "本次运行通过",
    }[card["read_scope"]]
    note = cell(card["note"])
    return f"| {position} | {title}{(' · ' + links) if links else ''} | {card['tier']} | {label}{('；' + note) if note else ''} |"


def render(catalog):
    counts = validate(catalog)
    ranked = sorted(
        (c for c in catalog["entries"] if c["queue_rank"] is not None),
        key=lambda c: c["queue_rank"],
    )
    candidates = [c for c in catalog["entries"] if c["queue_rank"] is None]
    header = ["| 顺序 | 材料 | 档位 | 读取范围与备注 |", "| --- | --- | --- | --- |"]
    queue = [
        "# 外部材料学习队列",
        "",
        "[说明与维护](./README.md) · [其余候选](./CANDIDATES.md)",
        "",
        "排名是建议阅读顺序，不代表已读或同时开工承诺。按材料 ID 保留重复来源；当前队列不含历史归档。",
        "",
        "## Top 30",
        "",
        *header,
    ]
    for card in ranked[: catalog["top_window_size"]]:
        queue.append(row(card, card["queue_rank"]))
    queue += ["", "## Ranked backlog", "", *header]
    for card in ranked[catalog["top_window_size"] :]:
        queue.append(row(card, card["queue_rank"]))
    backlog = [
        "# 外部候选材料",
        "",
        "[返回有排名的队列](./QUEUE.md) · [说明](./README.md)",
        "",
        "以下记录尚未进入正式排名。序号仅便于浏览，保留原 catalog 的记录顺序，不表示优先级。",
        "",
        *header,
    ]
    backlog.extend(row(card, i) for i, card in enumerate(candidates, 1))
    return {
        "QUEUE.md": "\n".join(queue) + "\n",
        "CANDIDATES.md": "\n".join(backlog) + "\n",
    }, counts


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(__file__).resolve().parents[2] / "Learning-Materials",
    )
    parser.add_argument(
        "--check", action="store_true", help="verify without changing files"
    )
    args = parser.parse_args()
    catalog = json.loads((args.root / "catalog.json").read_text())
    outputs, counts = render(catalog)
    for card in catalog["entries"]:
        for source in card["sources"]:
            if source.startswith("./") and not (args.root / source).is_file():
                raise ValueError("missing local source artifact")
    for name, text in outputs.items():
        path = args.root / name
        if args.check:
            if not path.exists() or path.read_text() != text:
                raise ValueError(f"{name} is stale; rerun without --check")
        else:
            path.write_text(text)
    print(json.dumps(counts, ensure_ascii=False))


if __name__ == "__main__":
    main()
