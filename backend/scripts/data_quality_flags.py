"""Phase 3 step F: data-quality flags on v4 scored reports.

Flags two conditions per spec:
  1. Narrative words < 25% of the company's own 6-year median
  2. IQR outliers per pillar density (outside 1.5x IQR fence)

Prints a summary table. Does NOT modify any Report rows.

Usage:
    python scripts/data_quality_flags.py
"""
from __future__ import annotations

import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND))

from dotenv import load_dotenv  # noqa: E402

load_dotenv(BACKEND / ".env")


def _median(vals: list[float]) -> float:
    s = sorted(vals)
    n = len(s)
    if n == 0:
        return 0.0
    mid = n // 2
    return s[mid] if n % 2 else (s[mid - 1] + s[mid]) / 2.0


def _iqr_fences(vals: list[float]) -> tuple[float, float]:
    s = sorted(vals)
    n = len(s)
    if n < 4:
        return float("-inf"), float("inf")
    q1 = s[n // 4]
    q3 = s[(3 * n) // 4]
    iqr = q3 - q1
    return q1 - 1.5 * iqr, q3 + 1.5 * iqr


def main() -> int:
    from collections import defaultdict

    import app.models.provenance
    import app.models.score
    import app.models.taxonomy  # noqa: F401
    from app.database import SessionLocal
    from app.models.institution import Institution
    from app.models.report import Report, ReportStatus
    from app.services.pipeline import PIPELINE_VERSION

    db = SessionLocal()

    reports = (
        db.query(Report)
        .join(Institution, Institution.id == Report.institution_id)
        .filter(
            Report.status == ReportStatus.scored,
            Report.pipeline_version == PIPELINE_VERSION,
            Institution.active,
        )
        .order_by(Institution.id, Report.fiscal_year)
        .all()
    )

    if not reports:
        print("No scored reports found.")
        return 1

    inst_map = {i.id: i for i in db.query(Institution).filter(Institution.active).all()}
    print(f"Checking {len(reports)} scored reports (pipeline={PIPELINE_VERSION})")
    print()

    # --- Flag 1: narrative_word_count < 25% of company median ---
    by_company: dict[int, list[Report]] = defaultdict(list)
    for r in reports:
        by_company[r.institution_id].append(r)

    flag1_rows: list[tuple[str, int, int, float, float]] = []
    for iid, rpts in by_company.items():
        wcs = [r.narrative_word_count for r in rpts if r.narrative_word_count > 0]
        if not wcs:
            continue
        med = _median([float(w) for w in wcs])
        threshold = 0.25 * med
        for r in rpts:
            if r.narrative_word_count < threshold:
                inst = inst_map.get(iid)
                slug = inst.slug if inst else "?"
                flag1_rows.append((slug, r.fiscal_year, r.narrative_word_count, med, threshold))

    print(f"Flag 1: narrative_word_count < 25% of company median  ({len(flag1_rows)} flagged)")
    if flag1_rows:
        print(f"  {'slug':<40} {'FY':>4} {'narrative_wc':>14} {'company_med':>12} {'threshold':>10}")
        for slug, fy, wc, med, thr in sorted(flag1_rows):
            print(f"  {slug:<40} {fy:>4} {wc:>14,} {med:>12,.0f} {thr:>10,.0f}")
    print()

    # --- Flag 2: IQR outliers per pillar density (across all 390) ---
    pillar_fields = [("E", "e_density"), ("S", "s_density"), ("G", "g_density")]
    flag2_rows: list[tuple[str, str, int, float, float, float]] = []

    for pillar, field in pillar_fields:
        vals = [getattr(r, field) for r in reports if getattr(r, field) is not None]
        if len(vals) < 4:
            continue
        lo, hi = _iqr_fences(vals)
        for r in reports:
            v = getattr(r, field)
            if v is None:
                continue
            if v < lo or v > hi:
                inst = inst_map.get(r.institution_id)
                slug = inst.slug if inst else "?"
                flag2_rows.append((pillar, slug, r.fiscal_year, v, lo, hi))

    print(f"Flag 2: IQR outliers per pillar density (1.5x IQR fence)  ({len(flag2_rows)} flagged)")
    if flag2_rows:
        print(f"  {'P':<2} {'slug':<40} {'FY':>4} {'density':>9} {'lo_fence':>10} {'hi_fence':>10}")
        for pillar, slug, fy, v, lo, hi in sorted(flag2_rows, key=lambda x: (x[0], x[1], x[2])):
            side = "LOW" if v < lo else "HIGH"
            print(f"  {pillar:<2} {slug:<40} {fy:>4} {v:>9.4f} {lo:>10.4f} {hi:>10.4f}  {side}")
    print()

    # Unique (slug, fy) across both flags
    flagged_keys: set[tuple[str, int]] = set()
    for slug, fy, *_ in flag1_rows:
        flagged_keys.add((slug, fy))
    for _, slug, fy, *_ in flag2_rows:
        flagged_keys.add((slug, fy))
    print(f"Total unique flagged company-years: {len(flagged_keys)} / {len(reports)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
