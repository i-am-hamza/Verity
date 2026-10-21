"""Compute 0-100 rank scores for all v6 reports.

Run after the full scoring batch to populate e_score, s_score, g_score,
general_score, composite_score, composite_3pillar, composite_general_no_new3,
and addon_rank on every Report row.

Formula (spec B.4, updated for 0-100):
  score = 100 * (rank - 1) / (N - 1)   ascending average rank, N = pool size
  stored to one decimal place.

Pools:
  E/S/G/General pillars: all scored reports in the 390 company-year universe.
  Add-on: only the financial company-years.

Composites:
  composite_score          = average(e_score, s_score, g_score, general_score)  [0-100]
  composite_3pillar        = average(e_score, s_score, g_score)                  [0-100]
  composite_general_no_new3 = average(e_score, s_score, g_score,
                               general_no_new3_score)  where general_no_new3
                               excludes innovation/feedback/digital_services.    [0-100]

Safe to re-run: scores are overwritten in place, no new rows created.

Usage:
    python scripts/compute_ranks.py [--dry-run]
"""
from __future__ import annotations

import argparse
import sys
from collections import defaultdict
from pathlib import Path

BACKEND = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND))

from dotenv import load_dotenv  # noqa: E402

load_dotenv(BACKEND / ".env")

# Phrases that make up the "new 3" in the General component.
# composite_general_no_new3 excludes their density contribution.
NEW_3_PHRASES = {"innovation", "feedback", "digital services"}


def _rank_scores(values: list[float | None]) -> list[float | None]:
    """Convert densities to 0-100 scores using ascending average rank.

    None entries stay None (report not scored / not applicable).
    Ties receive the average of the ranks they share.
    Result stored to one decimal place.
    """
    indexed = [(v, i) for i, v in enumerate(values) if v is not None]
    if not indexed:
        return [None] * len(values)

    n = len(indexed)
    result: list[float | None] = [None] * len(values)

    if n == 1:
        result[indexed[0][1]] = 0.0
        return result

    sorted_vals = sorted(indexed, key=lambda x: x[0])
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
        result[i] = round(100.0 * (avg_ranks[i] - 1) / (n - 1), 1)
    return result


def main(dry_run: bool = False) -> int:
    import app.models.provenance
    import app.models.score
    import app.models.taxonomy  # noqa: F401
    from app.database import SessionLocal
    from app.models.institution import Institution
    from app.models.report import Report, ReportStatus
    from app.models.score import MatchEvidence
    from app.models.taxonomy import Term
    from app.services.pipeline import PIPELINE_VERSION

    db = SessionLocal()

    all_scored = (
        db.query(Report)
        .join(Institution, Institution.id == Report.institution_id)
        .filter(
            Report.status == ReportStatus.scored,
            Report.pipeline_version == PIPELINE_VERSION,
            Institution.active,
        )
        .order_by(Institution.id, Report.fiscal_year, Report.id)
        .all()
    )

    # Deduplicate: keep highest id per (source_document_id, pipeline_version).
    seen: dict[tuple, int] = {}
    reports_dedup: list = []
    for r in all_scored:
        key = (r.source_document_id, PIPELINE_VERSION) if r.source_document_id else (r.institution_id, r.fiscal_year, PIPELINE_VERSION)
        if key in seen:
            reports_dedup[seen[key]] = r
        else:
            seen[key] = len(reports_dedup)
            reports_dedup.append(r)
    reports = reports_dedup

    if not reports:
        print(f"No scored reports found for pipeline_version={PIPELINE_VERSION}")
        return 1

    n_raw = len(all_scored)
    n_dedup = len(reports)
    if n_raw != n_dedup:
        print(f"Found {n_raw} scored rows -> deduplicated to {n_dedup} (pipeline={PIPELINE_VERSION})")
    else:
        print(f"Found {n_dedup} scored reports (pipeline={PIPELINE_VERSION})")

    inst_map: dict[int, Institution] = {
        inst.id: inst
        for inst in db.query(Institution).filter(Institution.active).all()
    }

    financial_reports = [
        r for r in reports if inst_map.get(r.institution_id) and
        inst_map[r.institution_id].is_financial
    ]

    print(f"  Full pool: {len(reports)}  Financial pool: {len(financial_reports)}")

    # --- E/S/G/General rank scores ---
    e_scores = _rank_scores([r.e_density for r in reports])
    s_scores = _rank_scores([r.s_density for r in reports])
    g_scores = _rank_scores([r.g_density for r in reports])
    gen_scores = _rank_scores([r.general_density for r in reports])

    # --- Add-on rank scores (financial pool only) ---
    addon_scores = _rank_scores([r.addon_density for r in financial_reports])
    addon_score_by_id = {r.id: s for r, s in zip(financial_reports, addon_scores, strict=True)}

    # --- composite_general_no_new3: General density minus innovation/feedback/digital ---
    # Find term IDs for the three examiner-requested terms moved into General.
    new3_term_ids: set[int] = set()
    for t in db.query(Term).filter(Term.phrase.in_(list(NEW_3_PHRASES))).all():
        new3_term_ids.add(t.id)
    print(f"  new3 term IDs (innovation/feedback/digital services): {sorted(new3_term_ids)}")

    # Fetch MatchEvidence for all reports in the pool, filtered to new3 term IDs.
    report_ids = [r.id for r in reports]
    new3_evidence = (
        db.query(MatchEvidence)
        .filter(
            MatchEvidence.report_id.in_(report_ids),
            MatchEvidence.term_id.in_(list(new3_term_ids)),
            MatchEvidence.pipeline_version == PIPELINE_VERSION,
        )
        .all()
    )
    # Accumulate weighted count per report (weight=1.0 for all new3 terms, SASB=none)
    new3_weighted_by_report: dict[int, float] = defaultdict(float)
    for ev in new3_evidence:
        new3_weighted_by_report[ev.report_id] += 1.0  # weight=1.0 for all new3

    # Build "no_new3" densities: subtract new3 contribution from general_density
    no_new3_densities: list[float | None] = []
    for r in reports:
        if r.general_density is None or r.narrative_word_count == 0:
            no_new3_densities.append(None)
            continue
        new3_density = new3_weighted_by_report.get(r.id, 0.0) * (1000.0 / r.narrative_word_count)
        no_new3_densities.append(max(0.0, r.general_density - new3_density))

    gen_no_new3_scores = _rank_scores(no_new3_densities)

    # --- Apply scores ---
    updated = 0
    for i, report in enumerate(reports):
        e = e_scores[i]
        s = s_scores[i]
        g = g_scores[i]
        gen = gen_scores[i]
        gen_no_new3 = gen_no_new3_scores[i]

        if not dry_run:
            report.e_score = e
            report.s_score = s
            report.g_score = g
            report.general_score = gen
            if e is not None and s is not None and g is not None and gen is not None:
                report.composite_score = round((e + s + g + gen) / 4.0, 1)
            else:
                report.composite_score = None
            if e is not None and s is not None and g is not None:
                report.composite_3pillar = round((e + s + g) / 3.0, 1)
            else:
                report.composite_3pillar = None
            if e is not None and s is not None and g is not None and gen_no_new3 is not None:
                report.composite_general_no_new3 = round((e + s + g + gen_no_new3) / 4.0, 1)
            else:
                report.composite_general_no_new3 = None
            if report.id in addon_score_by_id:
                report.addon_rank = addon_score_by_id[report.id]

        updated += 1

    if not dry_run:
        db.commit()
        print(f"Updated {updated} reports.")
    else:
        print("DRY RUN -- first 10 reports:")
        print(f"{'slug':<35} {'FY':>4} {'E':>7} {'S':>7} {'G':>7} {'Gen':>7} {'comp':>7} {'3pil':>7}")
        for i, report in enumerate(reports[:10]):
            inst = inst_map.get(report.institution_id)
            slug = inst.slug if inst else "?"
            e = e_scores[i]
            s = s_scores[i]
            g = g_scores[i]
            gen = gen_scores[i]
            comp = round((e + s + g + gen) / 4, 1) if (e is not None and s is not None and g is not None and gen is not None) else None
            pil3 = round((e + s + g) / 3, 1) if (e is not None and s is not None and g is not None) else None
            print(f"{slug:<35} {report.fiscal_year:>4} "
                  f"{(e or 0):>7.1f} {(s or 0):>7.1f} {(g or 0):>7.1f} "
                  f"{(gen or 0):>7.1f} {(comp or 0):>7.1f} {(pil3 or 0):>7.1f}")

    db.close()
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true",
                        help="Print scores without writing to DB")
    args = parser.parse_args()
    sys.exit(main(dry_run=args.dry_run))
