#!/usr/bin/env python3
"""Parallel paper-source exploration for research-material-scout.

This is a recall helper, not a truth source. It searches several public paper
lanes for the same query, normalizes metadata into one JSON payload, and leaves
ranking / verification to Codex.

Default lanes:
- arXiv Atom API
- OpenReview public notes search API
- OpenAlex works API
- bioRxiv / medRxiv metadata APIs with local query filtering
- ChemRxiv public dashboard dataset mirror with local query filtering
- venue search hints for conference/proceedings lanes

The script uses only Python standard library modules.
"""

from __future__ import annotations

import argparse
import bz2
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone
import html
import json
import re
import time
from typing import Any, Callable
from urllib.parse import quote, urlencode
from urllib.request import Request, urlopen
import xml.etree.ElementTree as ET


DEFAULT_SOURCES = "arxiv,openreview,openalex,biorxiv,medrxiv,chemrxiv,venue-hints"
CHEMRXIV_DASHBOARD_DATA_URL = (
    "https://raw.githubusercontent.com/chemrxiv-dashboard/"
    "chemrxiv-dashboard.github.io/master/data/allchemrxiv_data.json.bz2"
)
USER_AGENT = "CS-Notes research-material-scout multi-source paper explorer"
STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "by",
    "for",
    "from",
    "in",
    "into",
    "is",
    "of",
    "on",
    "or",
    "the",
    "to",
    "with",
}


@dataclass
class PaperResult:
    source: str
    lane: str
    title: str
    url: str
    query: str = ""
    date: str = ""
    venue: str = ""
    authors: list[str] | None = None
    abstract: str = ""
    evidence: str = ""
    kind: str = "paper"
    raw_id: str = ""


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def http_json(url: str, timeout: int) -> Any:
    req = Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/json"})
    with urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8", errors="replace"))


def http_bytes(url: str, timeout: int) -> bytes:
    req = Request(url, headers={"User-Agent": USER_AGENT, "Accept": "*/*"})
    with urlopen(req, timeout=timeout) as resp:
        return resp.read()


def clean_text(value: Any, limit: int = 900) -> str:
    text = html.unescape(str(value or ""))
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    if limit and len(text) > limit:
        return text[: limit - 1].rstrip() + "..."
    return text


def tokens(query: str) -> list[str]:
    out: list[str] = []
    seen = set()
    for item in re.findall(r"[A-Za-z][A-Za-z0-9_-]{1,}", query.lower()):
        if item in STOPWORDS or item in seen:
            continue
        seen.add(item)
        out.append(item)
    return out


def text_match_score(query_terms: list[str], *fields: str) -> int:
    hay = " ".join(fields).lower()
    return sum(1 for term in query_terms if term in hay)


def parse_date(value: Any) -> datetime | None:
    text = str(value or "").strip()
    if not text:
        return None
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", text):
        text += "T00:00:00+00:00"
    try:
        dt = datetime.fromisoformat(text)
    except Exception:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def is_future_date(value: Any) -> bool:
    dt = parse_date(value)
    return bool(dt and dt > now_utc() + timedelta(days=1))


def arxiv_query(query: str) -> str:
    terms = tokens(query)[:7]
    if not terms:
        return f'all:"{query}"'
    return " AND ".join(f"all:{term}" for term in terms)


def search_arxiv(query: str, limit: int, days: int, timeout: int) -> list[PaperResult]:
    params = urlencode(
        {
            "search_query": arxiv_query(query),
            "start": 0,
            "max_results": max(int(limit), 1),
            "sortBy": "submittedDate",
            "sortOrder": "descending",
        }
    )
    raw = http_bytes(f"https://export.arxiv.org/api/query?{params}", timeout)
    root = ET.fromstring(raw)
    ns = {"atom": "http://www.w3.org/2005/Atom"}
    out: list[PaperResult] = []
    for entry in root.findall("atom:entry", ns):
        title = clean_text(entry.findtext("atom:title", default="", namespaces=ns))
        abstract = clean_text(entry.findtext("atom:summary", default="", namespaces=ns))
        date = clean_text(entry.findtext("atom:published", default="", namespaces=ns), limit=80)
        raw_id = clean_text(entry.findtext("atom:id", default="", namespaces=ns), limit=200)
        authors = [
            clean_text(a.findtext("atom:name", default="", namespaces=ns), limit=120)
            for a in entry.findall("atom:author", ns)
        ]
        authors = [a for a in authors if a]
        url = raw_id
        if is_future_date(date):
            continue
        out.append(
            PaperResult(
                source="arxiv",
                lane="arXiv",
                title=title,
                url=url,
                date=date,
                authors=authors,
                abstract=abstract,
                evidence=f"arXiv API match for query terms: {', '.join(tokens(query)[:5])}",
                raw_id=raw_id,
            )
        )
    return out


def content_value(content: dict[str, Any], key: str) -> Any:
    raw = content.get(key)
    if isinstance(raw, dict) and "value" in raw:
        return raw.get("value")
    return raw


def normalize_authors(raw: Any) -> list[str]:
    if isinstance(raw, list):
        return [clean_text(x, limit=120) for x in raw if clean_text(x, limit=120)]
    if isinstance(raw, str):
        return [clean_text(x, limit=120) for x in re.split(r"[;,]", raw) if clean_text(x, limit=120)]
    return []


def search_openreview(query: str, limit: int, days: int, timeout: int) -> list[PaperResult]:
    params = urlencode(
        {
            "term": query,
            "group": "all",
            "source": "all",
            "content": "all",
            "limit": max(int(limit), 1),
        }
    )
    data = http_json(f"https://api2.openreview.net/notes/search?{params}", timeout)
    out: list[PaperResult] = []
    query_terms = tokens(query)
    min_score = max(1, min(2, len(query_terms)))
    for note in data.get("notes") or []:
        if not isinstance(note, dict):
            continue
        content = note.get("content") if isinstance(note.get("content"), dict) else {}
        title = clean_text(content_value(content, "title"))
        if not title:
            continue
        if title.lower().startswith("review:"):
            continue
        abstract = clean_text(content_value(content, "abstract") or content_value(content, "TLDR"))
        pdf = clean_text(content_value(content, "pdf"), limit=300)
        if not abstract and not pdf:
            continue
        forum = clean_text(note.get("forum") or note.get("id"), limit=120)
        venue = clean_text(content_value(content, "venue") or content_value(content, "venueid"), limit=160)
        score = text_match_score(query_terms, title, abstract, venue)
        if score < min_score:
            continue
        date = ""
        for key in ("pdate", "cdate", "tcdate"):
            value = note.get(key)
            if isinstance(value, (int, float)) and value > 0:
                date = datetime.fromtimestamp(value / 1000.0, tz=timezone.utc).date().isoformat()
                break
        out.append(
            PaperResult(
                source="openreview",
                lane="OpenReview",
                title=title,
                url=f"https://openreview.net/forum?id={forum}" if forum else "https://openreview.net/search",
                date=date,
                venue=venue,
                authors=normalize_authors(content_value(content, "authors")),
                abstract=abstract,
                evidence=f"OpenReview public notes search hit with local-filter score {score}/{len(query_terms)}; verify paper/forum page.",
                raw_id=forum,
            )
        )
    return out


def reconstruct_openalex_abstract(index: Any) -> str:
    if not isinstance(index, dict):
        return ""
    pairs: list[tuple[int, str]] = []
    for word, positions in index.items():
        if not isinstance(positions, list):
            continue
        for pos in positions:
            try:
                pairs.append((int(pos), str(word)))
            except Exception:
                pass
    pairs.sort()
    return clean_text(" ".join(word for _, word in pairs))


def search_openalex(query: str, limit: int, days: int, timeout: int) -> list[PaperResult]:
    params = urlencode(
        {
            "search": query,
            "per-page": max(int(limit), 1),
            "sort": "publication_date:desc",
        }
    )
    data = http_json(f"https://api.openalex.org/works?{params}", timeout)
    out: list[PaperResult] = []
    query_terms = tokens(query)
    min_score = max(1, min(2, len(query_terms)))
    for work in data.get("results") or []:
        if not isinstance(work, dict):
            continue
        title = clean_text(work.get("display_name") or work.get("title"))
        if not title:
            continue
        abstract = reconstruct_openalex_abstract(work.get("abstract_inverted_index"))
        score = text_match_score(query_terms, title, abstract)
        if score < min_score:
            continue
        date = clean_text(work.get("publication_date"), limit=40)
        if is_future_date(date):
            continue
        primary = work.get("primary_location") if isinstance(work.get("primary_location"), dict) else {}
        url = (
            clean_text(primary.get("landing_page_url"), limit=300)
            or clean_text((work.get("ids") or {}).get("doi") if isinstance(work.get("ids"), dict) else "", limit=300)
            or clean_text(work.get("id"), limit=300)
        )
        authorships = work.get("authorships") if isinstance(work.get("authorships"), list) else []
        authors: list[str] = []
        for item in authorships[:10]:
            author = item.get("author") if isinstance(item, dict) and isinstance(item.get("author"), dict) else {}
            name = clean_text(author.get("display_name"), limit=120)
            if name:
                authors.append(name)
        source = primary.get("source") if isinstance(primary.get("source"), dict) else {}
        out.append(
            PaperResult(
                source="openalex",
                lane="OpenAlex",
                title=title,
                url=url,
                date=date,
                venue=clean_text(source.get("display_name"), limit=160),
                authors=authors,
                abstract=abstract,
                evidence=f"OpenAlex works search hit with local-filter score {score}/{len(query_terms)}; verify against original venue/paper page.",
                raw_id=clean_text(work.get("id"), limit=180),
            )
        )
    return out


def bio_endpoint(server: str, start: datetime, end: datetime, cursor: int) -> str:
    return f"https://api.biorxiv.org/details/{server}/{start.date().isoformat()}/{end.date().isoformat()}/{cursor}"


def search_bio_server(server: str, query: str, limit: int, days: int, timeout: int, max_pages: int) -> list[PaperResult]:
    end = now_utc()
    start = end - timedelta(days=max(int(days), 1))
    query_terms = tokens(query)
    min_score = max(1, min(2, len(query_terms)))
    cursor = 0
    page_size = 100
    out: list[PaperResult] = []
    seen: set[str] = set()
    for _ in range(max(int(max_pages), 1)):
        data = http_json(bio_endpoint(server, start, end, cursor), timeout)
        messages = data.get("messages") or []
        if messages and isinstance(messages[0], dict):
            try:
                page_size = max(int(messages[0].get("count") or page_size), 1)
            except Exception:
                pass
        collection = data.get("collection") or []
        if not collection:
            break
        for raw in collection:
            if not isinstance(raw, dict):
                continue
            title = clean_text(raw.get("title"))
            abstract = clean_text(raw.get("abstract"))
            score = text_match_score(query_terms, title, abstract)
            if score < min_score:
                continue
            doi = clean_text(raw.get("doi"), limit=160)
            version = clean_text(raw.get("version") or "1", limit=20)
            key = f"{doi}:{version}"
            if not doi or key in seen:
                continue
            seen.add(key)
            date = clean_text(raw.get("date"), limit=40)
            out.append(
                PaperResult(
                    source=server,
                    lane=server,
                    title=title,
                    url=f"https://www.{server}.org/content/{doi}v{version}",
                    date=date,
                    venue=server,
                    authors=normalize_authors(raw.get("authors")),
                    abstract=abstract,
                    evidence=f"{server} API local-filter hit: {score}/{len(query_terms)} query terms.",
                    raw_id=doi,
                )
            )
            if len(out) >= limit:
                return out
        cursor += page_size
    return out


def search_biorxiv(query: str, limit: int, days: int, timeout: int, max_pages: int) -> list[PaperResult]:
    return search_bio_server("biorxiv", query, limit, days, timeout, max_pages)


def search_medrxiv(query: str, limit: int, days: int, timeout: int, max_pages: int) -> list[PaperResult]:
    return search_bio_server("medrxiv", query, limit, days, timeout, max_pages)


def normalize_chemrxiv_authors(raw: Any) -> list[str]:
    if not isinstance(raw, list):
        return []
    out: list[str] = []
    for item in raw:
        if not isinstance(item, dict):
            continue
        name = " ".join(
            part
            for part in (
                clean_text(item.get("firstName"), limit=80),
                clean_text(item.get("lastName"), limit=80),
            )
            if part
        )
        if name:
            out.append(name)
    return out


def search_chemrxiv(query: str, limit: int, days: int, timeout: int) -> list[PaperResult]:
    raw = http_bytes(CHEMRXIV_DASHBOARD_DATA_URL, timeout)
    payload = json.loads(bz2.decompress(raw))
    if not isinstance(payload, dict):
        return []
    query_terms = tokens(query)
    min_score = max(1, min(2, len(query_terms)))
    cutoff = now_utc() - timedelta(days=max(int(days), 1))
    out: list[PaperResult] = []
    for item in payload.values():
        if not isinstance(item, dict):
            continue
        title = clean_text(item.get("title"))
        abstract = clean_text(item.get("abstract"))
        score = text_match_score(query_terms, title, abstract)
        if score < min_score:
            continue
        date = clean_text(item.get("publishedDate") or item.get("approvedDate"), limit=50)
        dt = parse_date(date)
        if dt and dt < cutoff:
            continue
        item_id = clean_text(item.get("id"), limit=120)
        if not title or not item_id:
            continue
        out.append(
            PaperResult(
                source="chemrxiv",
                lane="ChemRxiv",
                title=title,
                url=f"https://chemrxiv.org/engage/chemrxiv/article-details/{item_id}",
                date=date,
                venue="ChemRxiv",
                authors=normalize_chemrxiv_authors(item.get("authors")),
                abstract=abstract,
                evidence=f"ChemRxiv dashboard dataset local-filter hit: {score}/{len(query_terms)} query terms.",
                raw_id=item_id,
            )
        )
        if len(out) >= limit:
            break
    return out


def venue_hints(query: str, limit: int, days: int, timeout: int) -> list[PaperResult]:
    encoded = quote(query)
    hints = [
        ("OpenReview search", f"https://openreview.net/search?term={encoded}"),
        ("ACL Anthology search", f"https://aclanthology.org/search/?q={encoded}"),
        ("NeurIPS proceedings search", f"https://papers.nips.cc/search?q={encoded}"),
        ("ICML proceedings search", f"https://proceedings.mlr.press/?q={encoded}"),
        ("AAAI search", f"https://ojs.aaai.org/index.php/AAAI/search/search?query={encoded}"),
        ("Papers with Code search", f"https://paperswithcode.com/search?q={encoded}"),
    ]
    return [
        PaperResult(
            source="venue-hints",
            lane=name,
            title=f"Search {name}: {query}",
            url=url,
            kind="search_hint",
            evidence="Source-specific venue search URL; inspect manually or through browser/web tools.",
        )
        for name, url in hints[:limit]
    ]


def dedupe_results(results: list[PaperResult]) -> list[dict[str, Any]]:
    buckets: dict[str, dict[str, Any]] = {}
    for result in results:
        title_key = re.sub(r"\W+", " ", result.title.lower()).strip()
        key = title_key or result.url
        data = asdict(result)
        data["authors"] = data.get("authors") or []
        if key not in buckets:
            data["lanes"] = [result.lane]
            data["sources"] = [result.source]
            data["queries"] = [result.query] if result.query else []
            data["lane_count"] = 1
            buckets[key] = data
            continue
        target = buckets[key]
        if result.lane not in target["lanes"]:
            target["lanes"].append(result.lane)
        if result.source not in target["sources"]:
            target["sources"].append(result.source)
        if result.query and result.query not in target["queries"]:
            target["queries"].append(result.query)
        target["lane_count"] = len(target["lanes"])
        if not target.get("abstract") and result.abstract:
            target["abstract"] = result.abstract
        if not target.get("date") and result.date:
            target["date"] = result.date
        if not target.get("venue") and result.venue:
            target["venue"] = result.venue
    return sorted(
        buckets.values(),
        key=lambda item: (
            item.get("kind") == "search_hint",
            -int(item.get("lane_count") or 1),
            item.get("date") or "",
            item.get("title") or "",
        ),
        reverse=False,
    )


def run_source(
    source: str,
    query: str,
    limit: int,
    days: int,
    timeout: int,
    max_pages: int,
) -> tuple[str, list[PaperResult], str, float]:
    started = time.time()
    try:
        if source == "arxiv":
            return source, search_arxiv(query, limit, days, timeout), "", time.time() - started
        if source == "openreview":
            return source, search_openreview(query, limit, days, timeout), "", time.time() - started
        if source == "openalex":
            return source, search_openalex(query, limit, days, timeout), "", time.time() - started
        if source == "biorxiv":
            return source, search_biorxiv(query, limit, days, timeout, max_pages), "", time.time() - started
        if source == "medrxiv":
            return source, search_medrxiv(query, limit, days, timeout, max_pages), "", time.time() - started
        if source == "chemrxiv":
            return source, search_chemrxiv(query, limit, days, timeout), "", time.time() - started
        if source in {"venue-hints", "venues"}:
            return source, venue_hints(query, limit, days, timeout), "", time.time() - started
        return source, [], f"unknown source: {source}", time.time() - started
    except Exception as exc:
        return source, [], f"{type(exc).__name__}: {exc}", time.time() - started


def main() -> None:
    parser = argparse.ArgumentParser(description="Search multiple paper-source lanes in parallel.")
    parser.add_argument("--query", required=True, action="append", help="Search query. Repeat for intent-query expansion.")
    parser.add_argument("--sources", default=DEFAULT_SOURCES, help=f"Comma-separated sources. Default: {DEFAULT_SOURCES}")
    parser.add_argument("--limit", type=int, default=8, help="Max results per source.")
    parser.add_argument("--days", type=int, default=365, help="Recent window for source APIs that require a date range.")
    parser.add_argument("--timeout", type=int, default=20, help="Per-request timeout in seconds.")
    parser.add_argument("--max-pages", type=int, default=3, help="Max bioRxiv/medRxiv pages to scan.")
    parser.add_argument("--workers", type=int, default=6, help="Parallel source workers.")
    args = parser.parse_args()

    sources = [s.strip().lower() for s in args.sources.split(",") if s.strip()]
    queries = [q.strip() for q in args.query if q.strip()]
    all_results: list[PaperResult] = []
    source_stats: dict[str, Any] = {}
    with ThreadPoolExecutor(max_workers=max(int(args.workers or 1), 1)) as pool:
        futures = {
            pool.submit(run_source, source, query, args.limit, args.days, args.timeout, args.max_pages): (source, query)
            for source in sources
            for query in queries
        }
        for future in as_completed(futures):
            source, results, error, elapsed = future.result()
            _, query = futures[future]
            for result in results:
                result.query = query
            all_results.extend(results)
            stat_key = source if len(queries) == 1 else f"{source} :: {query}"
            source_stats[stat_key] = {
                "source": source,
                "query": query,
                "hits": len(results),
                "error": error,
                "elapsed_seconds": round(elapsed, 3),
            }

    payload = {
        "query": queries[0] if len(queries) == 1 else "",
        "queries": queries,
        "generated_at": now_utc().isoformat(),
        "sources_requested": sources,
        "source_stats": source_stats,
        "unique_results": dedupe_results(all_results),
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
