"""Phase 3 step E: robustness checks on v4 scores.

Runs three weight variants (1.25, 2.0, unweighted) and one industry-adjusted
ranking variant, then reports Spearman correlations with the main 1.5-weight
composite and lists the 5 biggest movers.

Also runs the "without 5 added companies" check (Gulf Hotels, Jazeera Steel,
Salam, Barwa, Jazeera Airways).

Usage:
    python scripts/robustness_checks.py
"""
from __future__ import annotations

import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND))

from dotenv import load_dotenv  # noqa: E402

load_dotenv(BACKEND / ".env")

ADDED_5_SLUGS = {
    "gulf-hotels-group",
    "jazeera-steel",
    "salam-international-investment",
    "barwa-real-estate",
    "jazeera-airways",
}


def _spearman(a: list[float], b: list[float]) -> float:
    """Spearman rank correlation between two lists (no ties correction)."""
    n = len(a)
    assert len(b) == n
    ra = _rank_list(a)
    rb = _rank_list(b)
    d2 = sum((ra[i] - rb[i]) ** 2 for i in range(n))
    return round(1 - 6 * d2 / (n * (n * n - 1)), 4)


def _rank_list(vals: list[float]) -> list[float]:
    """1-indexed average ranks for a list."""
    n = len(vals)
    indexed = sorted(range(n), key=lambda i: vals[i])
    ranks = [0.0] * n
    pos = 0
    while pos < n:
        end = pos + 1
        while end < n and vals[indexed[end]] == vals[indexed[pos]]:
            end += 1
        avg = (pos + end + 1) / 2.0
        for k in range(pos, end):
            ranks[indexed[k]] = avg
        pos = end
    return ranks



def main() -> int:
    from collections import defaultdict

    import app.models.provenance  # noqa: F401 — resolve SQLAlchemy relationships
    from app.database import SessionLocal
    from app.models.institution import Institution
    from app.models.report import Report, ReportStatus
    from app.models.score import MatchEvidence
    from app.models.taxonomy import Term
    from app.services.pipeline import PIPELINE_VERSION
    from app.services.sasb_materiality import DEFAULT_WEIGHT, _norm, material_categories_for

    db = SessionLocal()

    # Load all scored reports
    reports = (
        db.query(Report)
        .join(Institution, Institution.id == Report.institution_id)
        .filter(
            Report.status == ReportStatus.scored,
            Report.pipeline_version == PIPELINE_VERSION,
            Institution.active,
            Report.e_score.isnot(None),
        )
        .order_by(Institution.id, Report.fiscal_year)
        .all()
    )

    if not reports:
        print("No ranked reports found. Run compute_ranks.py first.")
        return 1

    inst_map = {i.id: i for i in db.query(Institution).filter(Institution.active).all()}
    terms = db.query(Term).all()
    term_sasb = {t.id: (t.sasb_category_primary, t.sasb_category_secondary) for t in terms}
    term_group = {t.id: t.group for t in terms}
    term_pillar = {t.id: t.category.pillar for t in terms}

    print(f"Robustness checks on {len(reports)} ranked reports (pipeline={PIPELINE_VERSION})")
    print()

    # Main composite scores (0-10 rank-normalized)
    main_composite = [r.composite_score for r in reports]
    report_ids = [r.id for r in reports]

    # ---- Helper: recompute composite densities from MatchEvidence ----
    # Loads all MatchEvidence for these reports, applies alternative weights,
    # recomputes pillar densities, re-ranks, and returns composite.
    def _recompute_composites(material_w: float) -> list[float | None]:
        """Recompute composite for each report using `material_w` for material terms."""
        from scripts.compute_ranks import _rank_scores

        # Load all match evidence for the current pipeline
        evidence = (
            db.query(MatchEvidence)
            .filter(
                MatchEvidence.report_id.in_(report_ids),
                MatchEvidence.pipeline_version == PIPELINE_VERSION,
            )
            .all()
        )
        # Group by report_id
        by_report: dict[int, list] = defaultdict(list)
        for ev in evidence:
            by_report[ev.report_id].append(ev)

        e_dens: list[float | None] = []
        s_dens: list[float | None] = []
        g_dens: list[float | None] = []

        for r in reports:
            inst = inst_map.get(r.institution_id)
            wc = r.narrative_word_count
            if not wc or not inst:
                e_dens.append(None)
                s_dens.append(None)
                g_dens.append(None)
                continue
            mat = material_categories_for(inst.sasb_industry)
            e_raw = s_raw = g_raw = 0.0
            for ev in by_report.get(r.id, []):
                tid = ev.term_id
                group = term_group.get(tid, "")
                if group != "core":
                    continue
                pillar = term_pillar.get(tid, "")
                p_raw, s_raw_cat = term_sasb.get(tid, (None, None))
                # Apply material_w or 1.0
                pn = _norm(p_raw) if p_raw else None
                sn = _norm(s_raw_cat) if s_raw_cat else None
                w = material_w if mat and ((pn and pn in mat) or (sn and sn in mat)) else DEFAULT_WEIGHT
                if pillar == "Environmental":
                    e_raw += w
                elif pillar == "Social":
                    s_raw += w
                elif pillar == "Governance":
                    g_raw += w
            k = 1000.0 / wc
            e_dens.append(e_raw * k)
            s_dens.append(s_raw * k)
            g_dens.append(g_raw * k)

        e_sc = _rank_scores(e_dens)
        s_sc = _rank_scores(s_dens)
        g_sc = _rank_scores(g_dens)

        composites: list[float | None] = []
        for e, s, g in zip(e_sc, s_sc, g_sc, strict=True):
            if e is not None and s is not None and g is not None:
                composites.append((e + s + g) / 3.0)
            else:
                composites.append(None)
        return composites

    weight_variants = [
        ("unweighted (1.0/1.0)", 1.0),
        ("w=1.25",               1.25),
        ("main (w=1.5)",         1.5),
        ("w=2.0",                2.0),
    ]

    print("Weight sensitivity (Spearman rho vs main 1.5 composite):")
    print(f"  {'variant':<28} {'rho':>8}  top-5 movers")
    alt_composites: dict[str, list[float | None]] = {}
    for label, mw in weight_variants:
        if mw == 1.5:
            alt_composites[label] = main_composite
            print(f"  {label:<28} {'baseline':>8}")
            continue
        alt = _recompute_composites(mw)
        alt_composites[label] = alt
        # Spearman on non-null pairs
        pairs = [(m, a) for m, a in zip(main_composite, alt, strict=True)
                 if m is not None and a is not None]
        if len(pairs) < 2:
            print(f"  {label:<28} {'N/A':>8}")
            continue
        ms, als = zip(*pairs, strict=True)
        rho = _spearman(list(ms), list(als))
        # Top 5 movers (absolute change in composite)
        diffs = [(abs(a - m), i) for i, (m, a) in enumerate(zip(main_composite, alt, strict=True))
                 if m is not None and a is not None]
        diffs.sort(reverse=True)
        movers = []
        for _, i in diffs[:5]:
            inst = inst_map.get(reports[i].institution_id)
            sl = inst.slug if inst else "?"
            movers.append(f"{sl} FY{reports[i].fiscal_year} ({main_composite[i]:.2f}->{alt[i]:.2f})")
        print(f"  {label:<28} {rho:>8.4f}  {', '.join(movers[:2])}")
    print()

    # ---- Industry-adjusted ranking ----
    # Instead of pooling all 390, rank within each SASB industry separately,
    # then rescale to 0-10 within that pool.
    print("Industry-adjusted ranking (rank within SASB industry, then pool Spearman):")
    from collections import defaultdict as dd2

    from scripts.compute_ranks import _rank_scores

    industry_groups: dict[str, list[int]] = dd2(list)
    for i, r in enumerate(reports):
        inst = inst_map.get(r.institution_id)
        ind = inst.sasb_industry if inst else "Unknown"
        industry_groups[ind or "Unknown"].append(i)

    e_ind = [None] * len(reports)
    s_ind = [None] * len(reports)
    g_ind = [None] * len(reports)

    for _ind, idxs in industry_groups.items():
        ev = [reports[i].e_density for i in idxs]
        sv = [reports[i].s_density for i in idxs]
        gv = [reports[i].g_density for i in idxs]
        er = _rank_scores(ev)
        sr = _rank_scores(sv)
        gr = _rank_scores(gv)
        for k, idx in enumerate(idxs):
            e_ind[idx] = er[k]
            s_ind[idx] = sr[k]
            g_ind[idx] = gr[k]

    ind_comp = []
    for e, s, g in zip(e_ind, s_ind, g_ind, strict=True):
        if e is not None and s is not None and g is not None:
            ind_comp.append((e + s + g) / 3.0)
        else:
            ind_comp.append(None)

    pairs = [(m, a) for m, a in zip(main_composite, ind_comp, strict=True)
             if m is not None and a is not None]
    if pairs:
        ms, als = zip(*pairs, strict=True)
        rho = _spearman(list(ms), list(als))
        print(f"  Spearman rho (main pool vs industry-adjusted): {rho:.4f}")
        diffs = [(abs(a - m), i) for i, (m, a) in enumerate(zip(main_composite, ind_comp, strict=True))
                 if m is not None and a is not None]
        diffs.sort(reverse=True)
        print("  Top 5 movers under industry-adjusted ranking:")
        for _, i in diffs[:5]:
            inst = inst_map.get(reports[i].institution_id)
            sl = inst.slug if inst else "?"
            print(f"    {sl:<40} FY{reports[i].fiscal_year}  "
                  f"main={main_composite[i]:.3f}  ind-adj={ind_comp[i]:.3f}")
    print()

    # ---- Without 5 added companies ----
    print("Without 5 added companies (Gulf Hotels, Jazeera Steel, Salam, Barwa, Jazeera Airways):")
    keep_idxs = [i for i, r in enumerate(reports)
                 if inst_map.get(r.institution_id) and
                 inst_map[r.institution_id].slug not in ADDED_5_SLUGS]
    sub_reports = [reports[i] for i in keep_idxs]
    sub_e = _rank_scores([r.e_density for r in sub_reports])
    sub_s = _rank_scores([r.s_density for r in sub_reports])
    sub_g = _rank_scores([r.g_density for r in sub_reports])
    sub_comp = [(e + s + g) / 3.0 if e is not None and s is not None and g is not None else None
                for e, s, g in zip(sub_e, sub_s, sub_g, strict=True)]

    # Map back to full list for Spearman
    sub_comp_full: list[float | None] = [None] * len(reports)
    for k, i in enumerate(keep_idxs):
        sub_comp_full[i] = sub_comp[k]

    pairs = [(m, a) for m, a in zip(main_composite, sub_comp_full, strict=True)
             if m is not None and a is not None]
    if pairs:
        ms, als = zip(*pairs, strict=True)
        rho = _spearman(list(ms), list(als))
        print(f"  N without 5 = {len(sub_reports)}  Spearman rho: {rho:.4f}")
        diffs = [(abs(a - m), i) for i, (m, a) in enumerate(zip(main_composite, sub_comp_full, strict=True))
                 if m is not None and a is not None]
        diffs.sort(reverse=True)
        print("  Top 5 movers when 5 companies dropped:")
        for _, i in diffs[:5]:
            inst = inst_map.get(reports[i].institution_id)
            sl = inst.slug if inst else "?"
            print(f"    {sl:<40} FY{reports[i].fiscal_year}  "
                  f"main={main_composite[i]:.3f}  minus5={sub_comp_full[i]:.3f}")

    print()
    print("Robustness checks complete.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
