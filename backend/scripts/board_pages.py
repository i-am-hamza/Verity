"""Materialise board-section page text for every pending annotation row.

Reads data/board_size_annotations.csv, picks the rows whose `flag` column
contains "needs_annotation", resolves each (slug, fiscal_year) to a PDF
in R2 via the source_documents table (read-only), scores each page by
board-composition keywords, and writes the top-6 pages' plain text to:

    data/board_pages/<slug>_<year>.txt

with page-number markers and a leading header that records any stated
counts (e.g. "consists of (9) members") found anywhere in the report by
pattern. The .txt file is the only input the per-company reader agents
consume; the directory is excluded from git.

Idempotent: re-running skips reports whose .txt file already exists
(use --force to rebuild). Each report is a single serial PDF read —
the point of this script is to pre-materialise, not to parallelise.

Usage:
    python scripts/board_pages.py [--only slug1,slug2] [--force]
"""
from __future__ import annotations

import argparse
import io
import re
import sys
import csv
from pathlib import Path
from typing import Iterable

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

BACKEND = Path(__file__).resolve().parent.parent
REPO_ROOT = BACKEND.parent
sys.path.insert(0, str(BACKEND))

from dotenv import load_dotenv  # noqa: E402

load_dotenv(BACKEND / ".env")

from app.crawler import register_all_mappers  # noqa: E402

register_all_mappers()

import pymupdf  # type: ignore  # noqa: E402
from sqlalchemy import select  # noqa: E402

from app.database import SessionLocal  # noqa: E402
from app.models.company_year import CompanyYearData  # noqa: F401, E402
from app.models.institution import Institution  # noqa: E402
from app.models.provenance import SourceDocument  # noqa: E402
from app.services.storage import read_pdf_bytes  # noqa: E402

ANNOTATIONS_CSV = REPO_ROOT / "data" / "board_size_annotations.csv"
BOARD_PAGES_DIR = REPO_ROOT / "data" / "board_pages"

# User-supplied scoring keywords. Case-insensitive regex, word-aware.
BOARD_KEYWORDS: list[tuple[str, int]] = [
    (r"board\s+of\s+directors?", 5),
    (r"composition\s+of\s+the\s+board", 5),
    (r"board\s+members?", 3),
    (r"meetings?\s+of\s+the\s+board", 3),
    (r"\bchairman\b", 2),
    (r"\bvice[\s-]?chairman\b", 2),
    (r"\bdeputy\s+chairman\b", 2),
    (r"\bchairwoman\b", 2),
    (r"\bchair\s+of\s+the\s+board\b", 2),
    (r"\bindependent\b", 1),
    (r"\bnon[\s-]?executive\b", 1),
    (r"\battendance\b", 1),
]

# Numeric phrases that quote a stated board size.
STATED_PATTERNS: list[str] = [
    r"(?:board\s+(?:of\s+directors\s+)?(?:is\s+)?(?:composed|comprised?s?|consist(?:s|ing)?|comprising))\s+of\s+\(?(\d+|\w+(?:-\w+)?)\)?\s+(?:members?|directors?|non-executive\s+directors?)",
    r"(?:comprising\s+of|composed\s+of|consist(?:s|ing)?\s+of|comprises?)\s+\(?(\d+|\w+(?:-\w+)?)\)?\s+(?:members?|directors?)",
    r"board\s+(?:is\s+)?composed\s+of\s+(\d+|\w+(?:-\w+)?)",
    r"board\s+comprises\s+(\d+|\w+(?:-\w+)?)",
    r"(?:consisting|comprising)\s+of\s+(\d+|\w+(?:-\w+)?)\s+members",
    r"(?:a|the)\s+board\s+of\s+(\d+|\w+(?:-\w+)?)\s+(?:members?|directors?)",
]


def _needs_annotation_rows() -> list[tuple[str, int]]:
    """Return sorted unique (slug, fy) pairs still awaiting researcher review."""
    pairs: set[tuple[str, int]] = set()
    with ANNOTATIONS_CSV.open(encoding="utf-8", newline="") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            if "needs_annotation" not in (row.get("flag") or ""):
                continue
            try:
                fy = int(row["fiscal_year"])
            except (TypeError, ValueError):
                continue
            pairs.add((row["slug"], fy))
    return sorted(pairs)


def _resolve_r2_keys(pairs: Iterable[tuple[str, int]]) -> dict[tuple[str, int], str]:
    """Resolve one R2 key per (slug, fy); prefer annual over financial_statements.

    Reads from the DB only — never writes.
    """
    want: dict[tuple[str, int], str] = {}
    slugs = sorted({slug for slug, _ in pairs})
    db = SessionLocal()
    try:
        rows = db.execute(
            select(Institution.slug, SourceDocument.fiscal_year,
                   SourceDocument.report_type, SourceDocument.file_path)
            .join(SourceDocument, SourceDocument.institution_id == Institution.id)
            .where(Institution.slug.in_(slugs))
        ).all()
    finally:
        db.close()
    by_pair: dict[tuple[str, int], list[tuple[str, str]]] = {}
    for slug, fy, rtype, path in rows:
        by_pair.setdefault((slug, fy), []).append((str(rtype) if rtype else "", path))
    for pair, candidates in by_pair.items():
        # Prefer annual report; fall back to financial_statements; then anything else.
        annual = next((p for rt, p in candidates if rt == "annual"), None)
        fin = next((p for rt, p in candidates if rt == "financial_statements"), None)
        want[pair] = annual or fin or candidates[0][1]
    return want


def _score_page(text: str) -> int:
    low = text.lower()
    score = 0
    for pat, weight in BOARD_KEYWORDS:
        score += len(re.findall(pat, low, re.IGNORECASE)) * weight
    if "statement of financial position" in low or "consolidated statement of" in low:
        score -= 8
    latin_words = sum(1 for tok in text.split() if re.search(r"[A-Za-z]", tok))
    if latin_words < 50:
        score -= 2
    return score


def _find_stated(text: str) -> list[tuple[str, str]]:
    out: list[tuple[str, str]] = []
    for pat in STATED_PATTERNS:
        for m in re.finditer(pat, text, re.IGNORECASE):
            phrase = re.sub(r"\s+", " ", m.group(0)).strip()
            out.append((phrase, m.group(1)))
    return out


def _slug_safe(slug: str) -> str:
    return re.sub(r"[^a-z0-9._-]", "-", slug.lower())


def _write_board_file(slug: str, fy: int, r2_key: str, top: int = 6) -> dict:
    """Download the PDF, score pages, write top-N page text to disk.

    Returns {"status": ...} dict for logging.
    """
    out_path = BOARD_PAGES_DIR / f"{_slug_safe(slug)}_{fy}.txt"
    try:
        body = read_pdf_bytes(r2_key)
    except FileNotFoundError as exc:
        return {"status": "missing_r2", "slug": slug, "fy": fy, "key": r2_key, "err": str(exc)}
    try:
        doc = pymupdf.open(stream=body, filetype="pdf")
    except Exception as exc:  # noqa: BLE001
        return {"status": "pdf_open_fail", "slug": slug, "fy": fy, "key": r2_key, "err": str(exc)}
    pages: list[tuple[int, str]] = []
    for i, page in enumerate(doc, start=1):
        pages.append((i, page.get_text("text") or ""))
    doc.close()
    if not pages:
        return {"status": "empty_pdf", "slug": slug, "fy": fy}
    scored = [(pn, _score_page(txt), txt) for pn, txt in pages]
    scored_desc = sorted(scored, key=lambda x: x[1], reverse=True)
    top_pages = scored_desc[:top]
    top_pages_in_order = sorted(top_pages, key=lambda x: x[0])

    stated: list[tuple[int, str, str]] = []
    for pn, _, txt in scored:
        for phrase, num in _find_stated(txt):
            stated.append((pn, phrase, num))

    BOARD_PAGES_DIR.mkdir(parents=True, exist_ok=True)
    lines: list[str] = []
    lines.append(f"# slug: {slug}")
    lines.append(f"# fiscal_year: {fy}")
    lines.append(f"# r2_key: {r2_key}")
    lines.append(f"# total_pages: {len(pages)}")
    lines.append(f"# top_pages (page: score): "
                 + ", ".join(f"{pn}:{sc}" for pn, sc, _ in top_pages))
    lines.append("# stated_count_matches:")
    if not stated:
        lines.append("#   (none)")
    else:
        for pn, phrase, num in stated:
            lines.append(f"#   p{pn}: {phrase!r} -> {num}")
    lines.append("")
    for pn, score, txt in top_pages_in_order:
        lines.append(f"=== PAGE {pn} (score={score}) ===")
        lines.append(txt.rstrip())
        lines.append("")
    out_path.write_text("\n".join(lines), encoding="utf-8")
    return {
        "status": "ok",
        "slug": slug,
        "fy": fy,
        "pages": [pn for pn, _, _ in top_pages_in_order],
        "stated_count": len(stated),
        "file": str(out_path.relative_to(REPO_ROOT)),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", help="comma-separated list of slugs to process")
    ap.add_argument("--force", action="store_true",
                    help="rebuild .txt files that already exist")
    ap.add_argument("--top", type=int, default=6)
    args = ap.parse_args()

    pairs = _needs_annotation_rows()
    if args.only:
        wanted = {s.strip() for s in args.only.split(",") if s.strip()}
        pairs = [p for p in pairs if p[0] in wanted]
    print(f"needs_annotation (slug, fy) pairs: {len(pairs)}")
    if not pairs:
        return 0

    r2 = _resolve_r2_keys(pairs)
    missing_source = [p for p in pairs if p not in r2]
    if missing_source:
        print(f"WARN: {len(missing_source)} pairs have no source_document in DB.")
        for s, fy in missing_source[:20]:
            print(f"  no source for {s} FY{fy}")

    done = skipped = failed = 0
    for slug, fy in pairs:
        if (slug, fy) not in r2:
            failed += 1
            continue
        out_path = BOARD_PAGES_DIR / f"{_slug_safe(slug)}_{fy}.txt"
        if out_path.exists() and not args.force:
            skipped += 1
            continue
        res = _write_board_file(slug, fy, r2[(slug, fy)], top=args.top)
        if res["status"] == "ok":
            done += 1
            print(f"[ok] {slug} FY{fy} -> {res['file']}  pages={res['pages']}  stated={res['stated_count']}")
        else:
            failed += 1
            print(f"[{res['status']}] {slug} FY{fy}: {res.get('err','')}")
    print(f"\nSUMMARY: wrote={done} skipped={skipped} failed={failed}")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
