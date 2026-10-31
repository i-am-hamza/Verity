"""Write review workbook + evidence CSV from board_size_annotations.csv.

Outputs:
  docs/exports/board_size_review.xlsx
      - sheet 'flagged': every annotation row carrying any flag
                         (STATED_LIST_MISMATCH, out_of_range, big_change,
                         needs_annotation, basis=not_found, confidence=low).
      - sheet 'sample':  30 random rows (seed 42) drawn from fully-annotated
                         rows (method=read, basis != not_found, no flags).
      - sheet 'summary': aggregate counts.
  docs/exports/board_size_evidence.csv
      - one row per (slug, fiscal_year): slug, fiscal_year, board_size,
        basis, confidence, pages, names, stated_number, list_count,
        flag, note, method.

Does NOT touch the database. Does NOT regenerate any score.

Usage:
    python scripts/board_review_exports.py
"""
from __future__ import annotations

import csv
import random
import sys
from pathlib import Path
from typing import Any

BACKEND = Path(__file__).resolve().parent.parent
REPO_ROOT = BACKEND.parent
sys.path.insert(0, str(BACKEND))

import openpyxl  # noqa: E402
from openpyxl.styles import Font, PatternFill, Alignment  # noqa: E402
from openpyxl.utils import get_column_letter  # noqa: E402

ANNOTATIONS_CSV = REPO_ROOT / "data" / "board_size_annotations.csv"
EVIDENCE_CSV = REPO_ROOT / "docs" / "exports" / "board_size_evidence.csv"
REVIEW_XLSX = REPO_ROOT / "docs" / "exports" / "board_size_review.xlsx"

CSV_FIELDS = [
    "slug", "fiscal_year", "board_size", "basis", "confidence",
    "pages", "names", "stated_number", "list_count",
    "flag", "note", "method",
]


def _load() -> list[dict[str, str]]:
    with ANNOTATIONS_CSV.open(encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def _flagged(row: dict[str, str]) -> list[str]:
    """Return the set of review-worthy flags attached to this row.

    Lifted straight from the row's existing `flag` column, plus two
    implicit flags: basis==not_found, confidence==low.
    """
    flags = {f.strip() for f in (row.get("flag") or "").split(";") if f.strip()}
    if row.get("basis") == "not_found":
        flags.add("not_found")
    if row.get("confidence") == "low":
        flags.add("low_confidence")
    return sorted(flags)


def _header_row(ws, headers: list[str]) -> None:
    ws.append(headers)
    for col_idx in range(1, len(headers) + 1):
        cell = ws.cell(row=1, column=col_idx)
        cell.font = Font(bold=True, color="FFFFFF")
        cell.fill = PatternFill("solid", fgColor="333333")
        cell.alignment = Alignment(vertical="top", wrap_text=True)


def _widen(ws, widths: dict[str, int]) -> None:
    for col, w in widths.items():
        ws.column_dimensions[col].width = w


def _write_evidence_csv(rows: list[dict[str, str]]) -> None:
    EVIDENCE_CSV.parent.mkdir(parents=True, exist_ok=True)
    with EVIDENCE_CSV.open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=CSV_FIELDS)
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in CSV_FIELDS})


def _write_review_xlsx(rows: list[dict[str, str]]) -> None:
    REVIEW_XLSX.parent.mkdir(parents=True, exist_ok=True)
    wb = openpyxl.Workbook()
    ws_fl = wb.active
    assert ws_fl is not None
    ws_fl.title = "flagged"
    headers = CSV_FIELDS + ["review_flags"]
    _header_row(ws_fl, headers)
    for r in rows:
        flags = _flagged(r)
        if not flags:
            continue
        ws_fl.append([r.get(k, "") for k in CSV_FIELDS] + ["; ".join(flags)])
    _widen(ws_fl, {"A": 42, "B": 7, "C": 10, "D": 22, "E": 11, "F": 10,
                   "G": 60, "H": 10, "I": 10, "J": 22, "K": 60, "L": 10, "M": 20})

    ws_sa = wb.create_sheet("sample")
    _header_row(ws_sa, headers)
    clean = [r for r in rows
             if r.get("method") == "read"
             and r.get("basis") != "not_found"
             and not _flagged(r)]
    rnd = random.Random(42)
    sample = rnd.sample(clean, min(30, len(clean)))
    for r in sample:
        ws_sa.append([r.get(k, "") for k in CSV_FIELDS] + [""])
    _widen(ws_sa, {"A": 42, "B": 7, "C": 10, "D": 22, "E": 11, "F": 10,
                   "G": 60, "H": 10, "I": 10, "J": 22, "K": 60, "L": 10, "M": 20})

    ws_s = wb.create_sheet("summary")
    _header_row(ws_s, ["metric", "value"])
    total = len(rows)
    read = sum(1 for r in rows if r.get("method") == "read")
    pending = sum(1 for r in rows if r.get("method") == "pending")
    not_found = sum(1 for r in rows if r.get("basis") == "not_found")
    high = sum(1 for r in rows if r.get("confidence") == "high")
    low = sum(1 for r in rows if r.get("confidence") == "low")
    mism = sum(1 for r in rows if "STATED_LIST_MISMATCH" in (r.get("flag") or ""))
    oor = sum(1 for r in rows if "out_of_range" in (r.get("flag") or ""))
    bc = sum(1 for r in rows if "big_change" in (r.get("flag") or ""))
    na = sum(1 for r in rows if "needs_annotation" in (r.get("flag") or ""))
    flagged = sum(1 for r in rows if _flagged(r))
    sizes = sorted(int(r["board_size"]) for r in rows
                   if r.get("method") == "read" and r.get("board_size"))
    med = sizes[len(sizes) // 2] if sizes else ""
    rng = f"{sizes[0]}-{sizes[-1]}" if sizes else ""
    for k, v in [
        ("total_rows", total),
        ("annotated (method=read)", read),
        ("pending", pending),
        ("not_found", not_found),
        ("high_confidence", high),
        ("low_confidence", low),
        ("STATED_LIST_MISMATCH", mism),
        ("out_of_range", oor),
        ("big_change", bc),
        ("needs_annotation", na),
        ("flagged (any)", flagged),
        ("sample_size", len(sample)),
        ("board_size range (read rows)", rng),
        ("board_size median (read rows)", med),
    ]:
        ws_s.append([k, v])
    _widen(ws_s, {"A": 40, "B": 20})

    wb.save(REVIEW_XLSX)


def main() -> int:
    rows = _load()
    _write_evidence_csv(rows)
    _write_review_xlsx(rows)
    read = sum(1 for r in rows if r.get("method") == "read")
    pending = sum(1 for r in rows if r.get("method") == "pending")
    flagged = sum(1 for r in rows if _flagged(r))
    print(f"Wrote {EVIDENCE_CSV.relative_to(REPO_ROOT)} ({len(rows)} rows)")
    print(f"Wrote {REVIEW_XLSX.relative_to(REPO_ROOT)}")
    print(f"  annotated: {read}/{len(rows)}; pending: {pending}; flagged: {flagged}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
