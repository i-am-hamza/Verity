"""Load board-size annotations and firm ages into company_year_data.

Reads:
  data/board_size_annotations.csv  — researcher-read board sizes (390 rows)
  incoming/company_ages_board_2020_2025.xlsx — researcher-supplied ages

Writes:
  DB:   one company_year_data row per (institution, fiscal_year).
        Idempotent: existing rows are updated in place.
  CSV:  docs/exports/board_size_evidence.csv — one row per company-year
        with board_size, basis, pages, names counted.
  XLSX: docs/exports/board_size_review.xlsx — flagged rows (basis='not_found',
        confidence='low', STATED_LIST_MISMATCH, out-of-range, big change)
        plus a random sample of 30 (seed 42) across the fully-annotated rows.

How the method relates to the pilot (10 reports, approved):
  - BOARD SIZE = number of board seats at fiscal year-end, from that
    year's annual report.
  - A director representing an entity counts as one.
  - Secretary, advisors, observers, committee-only members are excluded.
  - Prefer the named list of actual directors.
  - Use a stated number only if it matches the list; otherwise use the
    list and set `flag=STATED_LIST_MISMATCH`.
  - "consists of up to N" (statutory) is ignored.
  - If no list or number is found, record 'not found'.

Usage:
    python scripts/extract_board_size.py [--check-pilot]
"""
from __future__ import annotations

import csv
import random
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

BACKEND = Path(__file__).resolve().parent.parent
REPO_ROOT = BACKEND.parent
sys.path.insert(0, str(BACKEND))

from dotenv import load_dotenv  # noqa: E402
load_dotenv(BACKEND / ".env")

from app.crawler import register_all_mappers  # noqa: E402
register_all_mappers()

import openpyxl  # noqa: E402
from openpyxl.styles import Font, PatternFill, Alignment  # noqa: E402
from openpyxl.utils import get_column_letter  # noqa: E402
from sqlalchemy import select  # noqa: E402

from app.database import SessionLocal  # noqa: E402
from app.models.company_year import (  # noqa: E402
    BoardSizeBasis,
    BoardSizeConfidence,
    CompanyYearData,
)
from app.models.institution import Institution  # noqa: E402

ANNOTATIONS_CSV = REPO_ROOT / "data" / "board_size_annotations.csv"
AGES_XLSX = REPO_ROOT / "incoming" / "company_ages_board_2020_2025.xlsx"
EVIDENCE_CSV = REPO_ROOT / "docs" / "exports" / "board_size_evidence.csv"
REVIEW_XLSX = REPO_ROOT / "docs" / "exports" / "board_size_review.xlsx"

# Expected pilot values (approved; must match after re-run).
PILOT_EXPECTED: dict[tuple[str, int], int] = {
    ("al-rajhi-bank", 2023): 11,
    ("qnb-qatar-national-bank", 2021): 10,
    ("saudi-aramco", 2022): 11,
    ("emaar-properties", 2024): 9,
    ("ooredoo-q-p-s-c", 2020): 10,
    ("bank-aljazira", 2023): 9,
    ("oman-telecommunications-company-otel", 2022): 9,
    ("national-bank-of-bahrain", 2025): 11,
    ("jazeera-airways", 2021): 8,
    ("kuwait-telecommunications-company", 2020): 7,
}

# Researcher-workbook name → institution slug.
# The incoming workbook names were drafted by the researcher; most line
# up to Institution.name exactly, but a handful differ by punctuation or
# wording. We map them here rather than renaming either side.
NAME_TO_SLUG: dict[str, str] = {
    "National Bank of Bahrain": "national-bank-of-bahrain",
    "The National Bank of Ras Al Khaimah": "the-national-bank-of-ras-al-khaimah",
    "Dubai Investments PJSC": "dubai-investment",
}


@dataclass(slots=True)
class Row:
    slug: str
    fiscal_year: int
    board_size: int | None
    basis: str
    confidence: str
    pages: str
    names: str
    stated_number: int | None
    list_count: int | None
    flag: str
    note: str
    method: str


def _opt_int(x: str) -> int | None:
    x = x.strip()
    return int(x) if x else None


def _parse_names(raw: str) -> list[str] | None:
    raw = raw.strip()
    if not raw:
        return None
    # The CSV encoding uses "; " between names.
    parts = [p.strip() for p in raw.split(";")]
    return [p for p in parts if p]


def load_annotations() -> list[Row]:
    rows: list[Row] = []
    with ANNOTATIONS_CSV.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for r in reader:
            rows.append(Row(
                slug=r["slug"].strip(),
                fiscal_year=int(r["fiscal_year"]),
                board_size=_opt_int(r["board_size"]),
                basis=r["basis"].strip() or "not_found",
                confidence=r["confidence"].strip() or "low",
                pages=r["pages"].strip(),
                names=r["names"].strip(),
                stated_number=_opt_int(r["stated_number"]),
                list_count=_opt_int(r["list_count"]),
                flag=r["flag"].strip(),
                note=r["note"].strip(),
                method=r["method"].strip() or "pending",
            ))
    return rows


def load_ages() -> dict[tuple[str, int], tuple[int | None, int | None]]:
    """Map (slug, fy) → (age_since_established, age_since_listed) from the
    researcher workbook. Names that don't resolve to a slug are skipped
    with a warning (the researcher must either rename or add a mapping)."""
    wb = openpyxl.load_workbook(AGES_XLSX, data_only=True)
    ws = wb.active
    assert ws is not None
    rows = list(ws.iter_rows(values_only=True))
    header = [str(c).strip() if c else "" for c in rows[0]]
    i_name = header.index("Company")
    i_year = header.index("Year")
    i_age_est = header.index("Age since established")
    i_age_list = header.index("Age since listed")

    db = SessionLocal()
    insts = db.execute(select(Institution)).scalars().all()
    db.close()
    name_to_slug: dict[str, str] = {inst.name: inst.slug for inst in insts}
    name_to_slug.update(NAME_TO_SLUG)

    out: dict[tuple[str, int], tuple[int | None, int | None]] = {}
    unresolved: set[str] = set()
    for row in rows[1:]:
        name = str(row[i_name]).strip() if row[i_name] else ""
        if not name:
            continue
        slug = name_to_slug.get(name)
        if not slug:
            unresolved.add(name)
            continue
        year = int(row[i_year])
        age_est = int(row[i_age_est]) if row[i_age_est] is not None else None
        age_list = int(row[i_age_list]) if row[i_age_list] is not None else None
        out[(slug, year)] = (age_est, age_list)
    for n in sorted(unresolved):
        print(f"  WARN: age workbook name does not match any institution: {n!r}")
    return out


def validate_pilot(annots: list[Row]) -> None:
    by_key = {(r.slug, r.fiscal_year): r for r in annots}
    for (slug, fy), expected in PILOT_EXPECTED.items():
        row = by_key.get((slug, fy))
        if row is None:
            raise SystemExit(
                f"PILOT CHECK FAILED: no annotation row for {slug} FY{fy}"
            )
        if row.board_size != expected:
            raise SystemExit(
                f"PILOT CHECK FAILED: {slug} FY{fy} expected {expected}, "
                f"got {row.board_size} (basis={row.basis})"
            )
    print(f"Pilot check: all {len(PILOT_EXPECTED)} values match.")


def write_db(annots: list[Row],
             ages: dict[tuple[str, int], tuple[int | None, int | None]]) -> int:
    db = SessionLocal()
    try:
        slug_to_id = {
            inst.slug: inst.id
            for inst in db.execute(select(Institution)).scalars()
        }
        wrote = 0
        for r in annots:
            iid = slug_to_id.get(r.slug)
            if iid is None:
                print(f"  WARN: unknown slug in annotations CSV: {r.slug!r}")
                continue
            cyd = db.execute(
                select(CompanyYearData).where(
                    CompanyYearData.institution_id == iid,
                    CompanyYearData.fiscal_year == r.fiscal_year,
                )
            ).scalar_one_or_none()
            age_est, age_list = ages.get((r.slug, r.fiscal_year), (None, None))
            if cyd is None:
                cyd = CompanyYearData(
                    institution_id=iid, fiscal_year=r.fiscal_year,
                )
                db.add(cyd)
            cyd.board_size = r.board_size
            cyd.board_size_basis = BoardSizeBasis(r.basis)
            cyd.board_size_confidence = BoardSizeConfidence(r.confidence)
            cyd.board_size_pages = r.pages or None
            cyd.board_size_names = _parse_names(r.names)
            cyd.board_size_stated_number = r.stated_number
            cyd.board_size_list_count = r.list_count
            cyd.board_size_flag = r.flag or None
            cyd.board_size_note = r.note or None
            cyd.board_size_method = r.method or None
            cyd.age_since_established = age_est
            cyd.age_since_listed = age_list
            wrote += 1
        db.commit()
        return wrote
    finally:
        db.close()


def compute_flags(annots: list[Row]) -> list[tuple[Row, list[str]]]:
    """Return (row, flags) tuples for every row, with per-rule flags.

    Flags, per the task spec:
      - out_of_range:          board_size < 3 or > 20
      - big_change:            |board_size - prev_year's| > 3
      - stated_list_mismatch:  flag column contains STATED_LIST_MISMATCH
      - not_found:             basis == 'not_found'
      - low_confidence:        confidence == 'low'
      - needs_annotation:      flag column contains needs_annotation
    """
    by_slug: dict[str, list[Row]] = {}
    for r in annots:
        by_slug.setdefault(r.slug, []).append(r)
    for xs in by_slug.values():
        xs.sort(key=lambda r: r.fiscal_year)
    prev: dict[str, Row] = {}

    out: list[tuple[Row, list[str]]] = []
    for slug in by_slug:
        for r in by_slug[slug]:
            flags: list[str] = []
            if r.basis == "not_found":
                flags.append("not_found")
            elif r.board_size is not None and (r.board_size < 3 or r.board_size > 20):
                flags.append("out_of_range")
            if (
                r.board_size is not None
                and slug in prev
                and prev[slug].board_size is not None
                and abs(r.board_size - prev[slug].board_size) > 3
            ):
                flags.append("big_change")
            if "STATED_LIST_MISMATCH" in r.flag:
                flags.append("stated_list_mismatch")
            if r.confidence == "low":
                flags.append("low_confidence")
            if "needs_annotation" in r.flag:
                flags.append("needs_annotation")
            prev[slug] = r
            out.append((r, flags))
    return out


def write_evidence_csv(annots: list[Row]) -> None:
    EVIDENCE_CSV.parent.mkdir(parents=True, exist_ok=True)
    with EVIDENCE_CSV.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow([
            "slug", "fiscal_year", "board_size", "basis", "confidence",
            "pages", "names_counted", "stated_number", "list_count",
            "flag", "note", "method",
        ])
        for r in sorted(annots, key=lambda x: (x.slug, x.fiscal_year)):
            w.writerow([
                r.slug, r.fiscal_year,
                r.board_size if r.board_size is not None else "",
                r.basis, r.confidence, r.pages, r.names,
                r.stated_number if r.stated_number is not None else "",
                r.list_count if r.list_count is not None else "",
                r.flag, r.note, r.method,
            ])


def write_review_xlsx(annots: list[Row]) -> dict[str, Any]:
    rows_with_flags = compute_flags(annots)

    # "All flagged" means ANY flag; sample of 30 drawn from the rest with
    # a fixed seed so the file is reproducible.
    flagged = [(r, fs) for r, fs in rows_with_flags if fs]
    annotated_clean = [
        (r, fs) for r, fs in rows_with_flags
        if not fs and r.basis != "not_found" and r.method == "read"
    ]
    rng = random.Random(42)
    sample = rng.sample(annotated_clean, min(30, len(annotated_clean)))

    wb = openpyxl.Workbook()

    def _header(ws, cols: list[str]) -> None:
        ws.append(cols)
        for cell in ws[1]:
            cell.font = Font(bold=True, color="FFFFFF")
            cell.fill = PatternFill("solid", fgColor="1F3864")
            cell.alignment = Alignment(horizontal="center", wrap_text=True)

    def _auto_width(ws) -> None:
        for col in ws.columns:
            header = str(col[0].value or "")
            max_data = max((len(str(c.value or "")) for c in col[1:50]), default=0)
            ws.column_dimensions[col[0].column_letter].width = min(
                max(len(header), max_data) + 2, 60
            )

    # Flagged sheet
    ws_f = wb.active
    assert ws_f is not None
    ws_f.title = "Flagged"
    cols = [
        "Slug", "Fiscal year", "Board size", "Basis", "Confidence",
        "Pages", "Names counted", "Stated number", "List count",
        "Flag column", "Review flags", "Note", "Method",
    ]
    _header(ws_f, cols)
    for r, fs in sorted(flagged, key=lambda x: (x[0].slug, x[0].fiscal_year)):
        ws_f.append([
            r.slug, r.fiscal_year,
            r.board_size if r.board_size is not None else "",
            r.basis, r.confidence, r.pages, r.names,
            r.stated_number if r.stated_number is not None else "",
            r.list_count if r.list_count is not None else "",
            r.flag, ", ".join(fs), r.note, r.method,
        ])
    ws_f.freeze_panes = "A2"
    ws_f.auto_filter.ref = f"A1:{get_column_letter(len(cols))}1"
    _auto_width(ws_f)

    # Random sample sheet
    ws_s = wb.create_sheet("Random sample (seed=42)")
    _header(ws_s, cols)
    for r, fs in sorted(sample, key=lambda x: (x[0].slug, x[0].fiscal_year)):
        ws_s.append([
            r.slug, r.fiscal_year,
            r.board_size if r.board_size is not None else "",
            r.basis, r.confidence, r.pages, r.names,
            r.stated_number if r.stated_number is not None else "",
            r.list_count if r.list_count is not None else "",
            r.flag, ", ".join(fs) or "(none)", r.note, r.method,
        ])
    ws_s.freeze_panes = "A2"
    ws_s.auto_filter.ref = f"A1:{get_column_letter(len(cols))}1"
    _auto_width(ws_s)

    # Summary sheet
    ws_sum = wb.create_sheet("Summary")
    ws_sum.append(["Metric", "Count"])
    ws_sum["A1"].font = Font(bold=True)
    ws_sum["B1"].font = Font(bold=True)
    total = len(annots)
    found = sum(1 for r in annots if r.basis != "not_found")
    high = sum(1 for r in annots if r.confidence == "high")
    low = sum(1 for r in annots if r.confidence == "low")
    needs_ann = sum(1 for r in annots if "needs_annotation" in r.flag)
    bigchg = sum(1 for r, fs in rows_with_flags if "big_change" in fs)
    oor = sum(1 for r, fs in rows_with_flags if "out_of_range" in fs)
    mism = sum(1 for r, fs in rows_with_flags if "stated_list_mismatch" in fs)
    not_found = sum(1 for r, fs in rows_with_flags if "not_found" in fs)
    for name, val in [
        ("Total company-years", total),
        ("Board size found", found),
        ("Not found", not_found),
        ("High confidence", high),
        ("Low confidence", low),
        ("Needs annotation (pending)", needs_ann),
        ("Big change (>3 seats)", bigchg),
        ("Out of range (<3 or >20)", oor),
        ("STATED_LIST_MISMATCH", mism),
    ]:
        ws_sum.append([name, val])
    _auto_width(ws_sum)

    REVIEW_XLSX.parent.mkdir(parents=True, exist_ok=True)
    wb.save(str(REVIEW_XLSX))

    return {
        "total": total, "found": found, "not_found": not_found,
        "high_confidence": high, "low_confidence": low,
        "needs_annotation": needs_ann, "big_change": bigchg,
        "out_of_range": oor, "stated_list_mismatch": mism,
        "flagged_rows": len(flagged), "random_sample": len(sample),
    }


def main() -> int:
    annots = load_annotations()
    print(f"Loaded {len(annots)} rows from {ANNOTATIONS_CSV.relative_to(REPO_ROOT)}")

    if "--check-pilot" in sys.argv:
        validate_pilot(annots)
        return 0

    validate_pilot(annots)

    ages = load_ages()
    print(f"Loaded {len(ages)} firm-age rows from "
          f"{AGES_XLSX.relative_to(REPO_ROOT)}")

    wrote = write_db(annots, ages)
    print(f"Wrote {wrote} company_year_data rows")

    write_evidence_csv(annots)
    print(f"Wrote {EVIDENCE_CSV.relative_to(REPO_ROOT)}")

    summary = write_review_xlsx(annots)
    print(f"Wrote {REVIEW_XLSX.relative_to(REPO_ROOT)}")

    # Range + median of found values.
    sizes = sorted(r.board_size for r in annots if r.board_size is not None)
    if sizes:
        median = sizes[len(sizes) // 2]
        print()
        print(f"Coverage: {summary['found']}/{summary['total']} found "
              f"({summary['found'] / summary['total']:.0%}); "
              f"{summary['not_found']} not found; "
              f"{summary['needs_annotation']} awaiting researcher review.")
        print(f"Confidence: {summary['high_confidence']} high, "
              f"{summary['low_confidence']} low.")
        print(f"Board size (found rows): range {sizes[0]}–{sizes[-1]}, "
              f"median {median}, n={len(sizes)}.")
        print(f"Flags: out_of_range={summary['out_of_range']}, "
              f"big_change={summary['big_change']}, "
              f"stated_list_mismatch={summary['stated_list_mismatch']}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
