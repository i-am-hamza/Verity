"""Merge per-company reader output into data/board_size_annotations.csv.

Each reader agent writes a JSON file at:

    data/board_pages_out/<slug>.json

shape:

    {
      "slug": "<slug>",
      "rows": [
        {
          "fiscal_year": 2020,
          "board_size": 9,                 # int or null
          "basis": "stated_number_and_list",
          "pages": "p49-51, p68",
          "names": "Name A; Name B; ...",  # ';' separated or ""
          "stated_number": 9,              # int or null
          "list_count": 9,                 # int or null
          "note": "..."
        },
        ...
      ]
    }

This script:
  - Reads data/board_size_annotations.csv.
  - For each --company (slug), finds its JSON output and replaces the
    corresponding pending rows with the new rows (one per fiscal_year).
    `read` rows are left alone, even for the same slug.
  - Confidence / flag are computed deterministically from the merged
    row + the previous year's board_size (for big_change detection).
  - Writes the CSV back after each company so progress survives a crash.

Usage:
    python scripts/board_merge.py --company slug1 slug2 ...
    python scripts/board_merge.py --all
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path
from typing import Any

BACKEND = Path(__file__).resolve().parent.parent
REPO_ROOT = BACKEND.parent
sys.path.insert(0, str(BACKEND))

ANNOTATIONS_CSV = REPO_ROOT / "data" / "board_size_annotations.csv"
READER_OUT_DIR = REPO_ROOT / "data" / "board_pages_out"

CSV_FIELDS = [
    "slug", "fiscal_year", "board_size", "basis", "confidence",
    "pages", "names", "stated_number", "list_count",
    "flag", "note", "method",
]

VALID_BASIS = {"list", "stated_number_and_list", "stated_number",
               "report_date", "not_found"}


def _load_csv() -> list[dict[str, str]]:
    with ANNOTATIONS_CSV.open(encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def _write_csv(rows: list[dict[str, str]]) -> None:
    tmp = ANNOTATIONS_CSV.with_suffix(".csv.tmp")
    with tmp.open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=CSV_FIELDS)
        w.writeheader()
        for r in rows:
            w.writerow({k: (r.get(k) or "") for k in CSV_FIELDS})
    tmp.replace(ANNOTATIONS_CSV)


def _confidence(basis: str, stated: int | None, list_count: int | None,
                board_size: int | None) -> str:
    if basis == "not_found" or board_size is None:
        return "low"
    if basis in ("list", "stated_number_and_list"):
        if stated is not None and list_count is not None and stated != list_count:
            return "low"
        return "high"
    # report_date / stated_number / anything else without a verified list
    return "low"


def _flags(basis: str, stated: int | None, list_count: int | None,
           board_size: int | None, prev_size: int | None) -> list[str]:
    flags: list[str] = []
    if basis == "not_found" or board_size is None:
        return flags
    if stated is not None and list_count is not None and stated != list_count:
        flags.append("STATED_LIST_MISMATCH")
    if board_size < 3 or board_size > 20:
        flags.append("out_of_range")
    if prev_size is not None and abs(board_size - prev_size) > 3:
        flags.append("big_change")
    return flags


def _as_int(val: Any) -> int | None:
    if val is None or val == "" or val == "null":
        return None
    try:
        return int(val)
    except (TypeError, ValueError):
        return None


def _as_str(val: Any) -> str:
    """Coerce a value to a flat string: list -> '; '.join, None -> ''."""
    if val is None:
        return ""
    if isinstance(val, list):
        return "; ".join(str(v).strip() for v in val if str(v).strip())
    return str(val)


def _apply_company(all_rows: list[dict[str, str]], slug: str) -> tuple[int, int]:
    """Replace pending rows for *slug* with the ones in its JSON output.

    Returns (updated_count, kept_read_count). Mutates all_rows in place.
    """
    json_path = READER_OUT_DIR / f"{slug}.json"
    if not json_path.exists():
        print(f"[skip] no reader output for {slug}: {json_path}")
        return 0, 0
    payload = json.loads(json_path.read_text(encoding="utf-8"))
    new_rows_by_fy: dict[int, dict[str, Any]] = {
        int(r["fiscal_year"]): r for r in payload.get("rows", [])
    }

    # Figure out previous-year sizes for big_change (using existing `read` rows
    # from any year + the new rows together).
    sorted_fys = sorted(new_rows_by_fy)
    prev_size_by_fy: dict[int, int | None] = {}
    read_size_by_fy = {
        int(r["fiscal_year"]): _as_int(r.get("board_size"))
        for r in all_rows
        if r["slug"] == slug and r.get("method") == "read"
    }

    def _board_size(fy: int) -> int | None:
        if fy in new_rows_by_fy:
            return _as_int(new_rows_by_fy[fy].get("board_size"))
        return read_size_by_fy.get(fy)

    for fy in sorted_fys:
        prev_size_by_fy[fy] = _board_size(fy - 1)

    updated = 0
    kept = 0
    out: list[dict[str, str]] = []
    for row in all_rows:
        if row["slug"] != slug:
            out.append(row)
            continue
        try:
            fy = int(row["fiscal_year"])
        except (TypeError, ValueError):
            out.append(row)
            continue
        if row.get("method") == "read":
            out.append(row)
            kept += 1
            continue
        # It's a pending row. If the reader produced output for this fy, replace.
        if fy not in new_rows_by_fy:
            out.append(row)
            continue
        new = new_rows_by_fy.pop(fy)
        basis = new.get("basis") or "not_found"
        if basis not in VALID_BASIS:
            print(f"[warn] {slug} FY{fy}: unexpected basis {basis!r}; coercing to not_found")
            basis = "not_found"
        board_size = _as_int(new.get("board_size"))
        stated = _as_int(new.get("stated_number"))
        list_count = _as_int(new.get("list_count"))
        conf = _confidence(basis, stated, list_count, board_size)
        flags = _flags(basis, stated, list_count, board_size, prev_size_by_fy.get(fy))
        if basis == "not_found" and "needs_annotation" not in flags:
            flags.append("needs_annotation")
        flag_str = "; ".join(flags)
        out.append({
            "slug": slug,
            "fiscal_year": str(fy),
            "board_size": "" if board_size is None else str(board_size),
            "basis": basis,
            "confidence": conf,
            "pages": _as_str(new.get("pages")),
            "names": _as_str(new.get("names")),
            "stated_number": "" if stated is None else str(stated),
            "list_count": "" if list_count is None else str(list_count),
            "flag": flag_str,
            "note": _as_str(new.get("note")),
            "method": "read",
        })
        updated += 1
    # If the reader produced extra fiscal years we didn't ask about, warn.
    for fy in new_rows_by_fy:
        print(f"[warn] {slug} FY{fy}: reader output has no matching pending row")
    all_rows[:] = out
    return updated, kept


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--company", nargs="*", default=[])
    ap.add_argument("--all", action="store_true")
    args = ap.parse_args()

    rows = _load_csv()
    if args.all:
        slugs = sorted({r["slug"] for r in rows if r.get("method") == "pending"})
        slugs = [s for s in slugs if (READER_OUT_DIR / f"{s}.json").exists()]
    else:
        slugs = args.company
    if not slugs:
        print("no companies to merge")
        return 0

    total_updated = 0
    for slug in slugs:
        updated, kept = _apply_company(rows, slug)
        _write_csv(rows)
        total_updated += updated
        print(f"[merge] {slug}: replaced {updated} pending rows (kept {kept} read rows)")
    print(f"\nTOTAL updated rows: {total_updated}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
