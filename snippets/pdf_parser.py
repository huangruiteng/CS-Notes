#!/usr/bin/env python3
"""Parse PDFs with PyMuPDF (fitz) into Markdown/JSON quickly (less robust)."""
import argparse
import json
import os
from pathlib import Path

import fitz  # PyMuPDF


def extract_markdown(doc: fitz.Document) -> str:
    parts = []
    for i, page in enumerate(doc, start=1):
        try:
            text = page.get_text("markdown")
        except Exception:
            # Fallback for PyMuPDF versions without markdown support
            text = page.get_text("text")
        if text:
            parts.append(f"\n\n<!-- page {i} -->\n\n")
            parts.append(text)
    return "".join(parts).strip() + "\n"


def extract_json(doc: fitz.Document, lang: str) -> dict:
    pages = []
    for i, page in enumerate(doc, start=1):
        pages.append({
            "page": i,
            "text": page.get_text("text")
        })
    return {"lang": lang, "pages": pages}


def extract_images(doc: fitz.Document, outdir: Path) -> int:
    count = 0
    for i, page in enumerate(doc, start=1):
        for img_index, img in enumerate(page.get_images(full=True), start=1):
            xref = img[0]
            pix = fitz.Pixmap(doc, xref)
            if pix.n < 5:
                img_path = outdir / f"page-{i}-img-{img_index}.png"
                pix.save(img_path)
            else:
                pix = fitz.Pixmap(fitz.csRGB, pix)
                img_path = outdir / f"page-{i}-img-{img_index}.png"
                pix.save(img_path)
            count += 1
    return count


def extract_tables_basic(doc: fitz.Document) -> list:
    # PyMuPDF doesn't provide robust table extraction. This is a placeholder
    # returning line-based text per page for quick parsing.
    tables = []
    for i, page in enumerate(doc, start=1):
        text = page.get_text("text")
        tables.append({"page": i, "lines": text.splitlines()})
    return tables


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("pdf", help="Path to PDF")
    parser.add_argument("--outroot", default="./pdf-output", help="Output root dir")
    parser.add_argument("--format", default="md", choices=["md", "json", "both"], help="Output format")
    parser.add_argument("--images", action="store_true", help="Extract images")
    parser.add_argument("--tables", action="store_true", help="Extract simple tables (lines)")
    parser.add_argument("--lang", default="en", help="Language (informational only)")
    args = parser.parse_args()

    pdf_path = Path(args.pdf)
    if not pdf_path.exists():
        raise SystemExit(f"Input not found: {pdf_path}")

    outdir = Path(args.outroot) / pdf_path.stem
    outdir.mkdir(parents=True, exist_ok=True)

    with fitz.open(pdf_path) as doc:
        if args.format in ("md", "both"):
            md = extract_markdown(doc)
            (outdir / "output.md").write_text(md, encoding="utf-8")

        if args.format in ("json", "both"):
            data = extract_json(doc, args.lang)
            (outdir / "output.json").write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

        if args.images:
            img_dir = outdir / "images"
            img_dir.mkdir(exist_ok=True)
            extract_images(doc, img_dir)

        if args.tables:
            tables = extract_tables_basic(doc)
            (outdir / "tables.json").write_text(json.dumps(tables, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"Done. Output: {outdir}")


if __name__ == "__main__":
    main()
