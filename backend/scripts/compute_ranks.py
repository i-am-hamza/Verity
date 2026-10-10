"""Compute 0-10 rank scores for all v4 reports.

Run after the full scoring batch to populate e_score, s_score, g_score,
composite_score, and addon_rank on every Report row.

Formula (spec B.4):
  score = 10 * (rank - 1) / (N - 1)   ascending average rank, N = pool size

Pools:
  E/S/G pillars: all scored reports in the 390 company-year universe, N=390.
  Add-on: only the 114 financial company-years (19 companies x 6 years).

Composite: simple average(e_score, s_score, g_score).

Safe to re-run: scores are overwritten in place, no new rows created.

Usage:
    python scripts/compute_ranks.py [--dry-run]
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND))

from dotenv import load_dotenv  # noqa: E402

load_dotenv(BACKEND / ".env")


def _rank_scores(values: list[float | None]) -> list[float | None]:
    """Convert a list of densities to 0-10 scores using ascending average rank.

    None entries stay None (report not scored / not applicable).
    Ties receive the average of the ranks they share (standard competition
    ranking for academic research).
    """
    indexed = [(v, i) for i, v in enumerate(values) if v is not None]
    if not indexed:
        return [None] * len(values)

    n = len(indexed)
    result: list[float | None] = [None] * len(values)

    if n == 1:
        result[indexed[0][1]] = 0.0
        return result

    # Sort ascending, assign average rank to ties
    sorted_vals = sorted(indexed, key=lambda x: x[0])
    # avg_rank_by_original_index
    avg_ranks: dict[int, float] = {}
    pos = 0
    while pos < n:
        run_end = pos + 1
        while run_end < n and sorted_vals[run_end][0] == sorted_vals[pos][0]:
            run_end += 1
        avg_rank = (pos + run_end + 1) / 2.0  # 1-indexed average rank
        for k in range(pos, run_end):
            avg_ranks[sorted_vals[k][1]] = avg_rank
        pos = run_end

    for _v, i in indexed:
        result[i] = round(10.0 * (avg_ranks[i] - 1) / (n - 1), 4)
    return result


def main(dry_run: bool = False) -> int:
    import app.models.provenance
    import app.models.score
    import app.models.taxonomy  # noqa: F401
    from app.database import SessionLocal
    from app.models.institution import Institution
    from app.models.report import Report, ReportStatus
    from app.services.pipeline import PIPELINE_VERSION

    db = SessionLocal()

    # Load all scored reports under the current pipeline version
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
        print(f"No scored reports found for pipeline_version={PIPELINE_VERSION}")
        return 1

    print(f"Found {len(reports)} scored reports (pipeline={PIPELINE_VERSION})")

    # Load institution lookup for is_financial check
    inst_map: dict[int, Institution] = {
        inst.id: inst
        for inst in db.query(Institution).filter(Institution.active).all()
    }

    # Split into full pool and financial-only pool
    financial_reports = [
        r for r in reports if inst_map.get(r.institution_id) and
        inst_map[r.institution_id].is_financial
    ]

    print(f"  Full pool: {len(reports)}  Financial pool: {len(financial_reports)}")

    # --- E/S/G rank scores across full pool ---
    e_densities = [r.e_density for r in reports]
    s_densities = [r.s_density for r in reports]
    g_densities = [r.g_density for r in reports]

    e_scores = _rank_scores(e_densities)
    s_scores = _rank_scores(s_densities)
    g_scores = _rank_scores(g_densities)

    # --- Add-on rank scores across financial-only pool ---
    addon_densities = [r.addon_density for r in financial_reports]
    addon_scores = _rank_scores(addon_densities)
    addon_score_by_id = {r.id: s for r, s in zip(financial_reports, addon_scores, strict=True)}

    # --- Apply scores ---
    updated = 0
    for i, report in enumerate(reports):
        e = e_scores[i]
        s = s_scores[i]
        g = g_scores[i]

        if not dry_run:
            report.e_score = e
            report.s_score = s
            report.g_score = g
            if e is not None and s is not None and g is not None:
                report.composite_score = round((e + s + g) / 3.0, 4)
            else:
                report.composite_score = None
            if report.id in addon_score_by_id:
                report.addon_rank = addon_score_by_id[report.id]

        updated += 1

    if not dry_run:
        db.commit()
        print(f"Updated {updated} reports.")
    else:
        print("DRY RUN -- first 10 reports:")
        print(f"{'slug':<35} {'FY':>4} {'E':>7} {'S':>7} {'G':>7} {'comp':>7} {'addon':>7}")
        for i, report in enumerate(reports[:10]):
            inst = inst_map.get(report.institution_id)
            slug = inst.slug if inst else "?"
            e = e_scores[i]
            s = s_scores[i]
            g = g_scores[i]
            comp = round((e + s + g) / 3, 4) if (e is not None and s is not None and g is not None) else None
            addon = addon_score_by_id.get(report.id)
            print(f"{slug:<35} {report.fiscal_year:>4} "
                  f"{(e or 0):>7.3f} {(s or 0):>7.3f} {(g or 0):>7.3f} "
                  f"{(comp or 0):>7.3f} {(addon or 0):>7.3f}")

    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true",
                        help="Print scores without writing to DB")
    args = parser.parse_args()
    sys.exit(main(dry_run=args.dry_run))
