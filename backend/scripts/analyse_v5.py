"""Analyse taxonomy v5 vs v4 results.

Computes and prints:
  1. Per-term frequency in the v5 corpus (new terms only), with
     relevant-report denominator.
  2. Spearman(v5, v4) for E, S, G and composite — company-year and
     company (mean-across-years) level.
  3. 10 companies whose composite rank moves most (v4→v5).

Run after seed_taxonomy_v5.py, the full batch, and compute_ranks.py.
"""
from __future__ import annotations

import sys
from collections import defaultdict
from pathlib import Path

BACKEND = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND))

from dotenv import load_dotenv  # noqa: E402

load_dotenv(BACKEND / ".env")

V4_PIPELINE = "0.4.2"
V5_PIPELINE = "0.5.0"

# New v5 terms (concept label → canonical phrases to look up in the DB)
NEW_TERM_LABELS: list[tuple[str, list[str]]] = [
    # E
    ("climate policy",             ["climate policy"]),
    ("pollution",                  ["pollution"]),
    ("resource use",               ["resource use"]),
    ("innovation",                 ["innovation"]),
    # S
    ("employee engagement",        ["employee engagement"]),
    ("employee ownership / share", ["employee ownership", "employee share ownership"]),
    ("pension benefits",           ["pension benefits"]),
    ("end of service",             ["end of service", "end-of-service"]),
    ("poverty",                    ["poverty"]),
    ("customer/client needs",      ["customer needs", "customers' needs",
                                    "client needs", "clients' needs"]),
    ("feedback",                   ["feedback"]),
    ("digital services",           ["digital services"]),
    # G
    ("board meeting(s)/variants",  ["board meeting", "meetings of directors",
                                    "meetings of the board"]),
    ("dividend policy",            ["dividend policy"]),
    ("stakeholder engagement",     ["stakeholder engagement"]),
    ("incentive plan(s)",          ["incentive plan"]),
]


def _spearman(a: list[float], b: list[float]) -> float:
    n = len(a)
    assert len(b) == n
    if n < 2:
        return float("nan")
    ra = _rank_list(a)
    rb = _rank_list(b)
    d2 = sum((ra[i] - rb[i]) ** 2 for i in range(n))
    return round(1 - 6 * d2 / (n * (n * n - 1)), 4)


def _rank_list(vals: list[float]) -> list[float]:
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
    import app.models.institution
    import app.models.provenance
    import app.models.report
    import app.models.score
    import app.models.taxonomy  # noqa: F401
    from app.database import SessionLocal
    from app.models.institution import Institution
    from app.models.report import Report, ReportStatus
    from app.models.score import MatchEvidence
    from app.models.taxonomy import TaxonomyVersion, Term
    from app.services.sasb_materiality import _norm, material_categories_for

    db = SessionLocal()

    # ------------------------------------------------------------------
    # Load taxonomy versions
    # ------------------------------------------------------------------
    tv_v4 = db.query(TaxonomyVersion).filter(
        TaxonomyVersion.hash.like("313c0eabe0%")
    ).first()
    tv_v5 = db.query(TaxonomyVersion).filter(
        TaxonomyVersion.note.like("v5:%")
    ).first()
    if not tv_v4 or not tv_v5:
        print("ERROR: could not find v4 or v5 taxonomy version in DB")
        db.close()
        return 1
    print(f"v4 taxonomy: id={tv_v4.id}  hash={tv_v4.hash[:16]}...")
    print(f"v5 taxonomy: id={tv_v5.id}  hash={tv_v5.hash[:16]}...")
    print()

    # ------------------------------------------------------------------
    # Deduplicate helper
    # ------------------------------------------------------------------
    def _dedup(reports_raw: list) -> list:
        seen: dict[tuple, int] = {}
        result: list = []
        for r in reports_raw:
            key = (r.source_document_id, r.pipeline_version) if r.source_document_id \
                else (r.institution_id, r.fiscal_year, r.pipeline_version)
            if key in seen:
                result[seen[key]] = r
            else:
                seen[key] = len(result)
                result.append(r)
        return result

    # ------------------------------------------------------------------
    # Load v4 and v5 scored reports
    # ------------------------------------------------------------------
    def _load_reports(pipeline: str) -> list:
        raw = (
            db.query(Report)
            .join(Institution, Institution.id == Report.institution_id)
            .filter(
                Report.status == ReportStatus.scored,
                Report.pipeline_version == pipeline,
                Institution.active.is_(True),
            )
            .order_by(Institution.id, Report.fiscal_year, Report.id)
            .all()
        )
        return _dedup(raw)

    v4_reports = _load_reports(V4_PIPELINE)
    v5_reports = _load_reports(V5_PIPELINE)
    print(f"v4 scored reports: {len(v4_reports)}")
    print(f"v5 scored reports: {len(v5_reports)}")
    if len(v5_reports) == 0:
        print("ERROR: no v5 reports found -- run the batch scorer first")
        db.close()
        return 1
    print()

    inst_map = {i.id: i for i in db.query(Institution).filter(Institution.active.is_(True)).all()}

    # ------------------------------------------------------------------
    # 1. Per-term frequency for new v5 terms
    # ------------------------------------------------------------------
    print("=" * 70)
    print("NEW TERM FREQUENCIES (v5 corpus)")
    print("=" * 70)

    # Load v5 term phrase → term_id
    v5_terms = db.query(Term).all()
    phrase_to_id: dict[str, int] = {t.phrase: t.id for t in v5_terms}

    v5_report_ids = [r.id for r in v5_reports]

    # Load MatchEvidence for v5 corpus (group by report_id, term_id)
    me_v5 = (
        db.query(MatchEvidence.report_id, MatchEvidence.term_id)
        .filter(
            MatchEvidence.pipeline_version == V5_PIPELINE,
            MatchEvidence.taxonomy_version_id == tv_v5.id,
            MatchEvidence.report_id.in_(v5_report_ids),
        )
        .distinct()
        .all()
    )
    # term_id → set of report_ids that contain it
    term_reports: dict[int, set[int]] = defaultdict(set)
    for row in me_v5:
        term_reports[row.term_id].add(row.report_id)

    # report_id → institution
    report_inst: dict[int, Institution] = {
        r.id: inst_map[r.institution_id] for r in v5_reports
        if r.institution_id in inst_map
    }

    print(f"{'Concept':<40} {'SASB cat':<42} {'Rel':>4} {'Hit':>4} {'%':>6}  {'Flag'}")
    print("-" * 110)

    for label, phrases in NEW_TERM_LABELS:
        # Collect term IDs for this concept's phrases
        tids = [phrase_to_id[p] for p in phrases if p in phrase_to_id]
        if not tids:
            print(f"  WARNING: no term IDs found for {label!r}")
            continue

        # Get SASB category of first phrase with one
        sasb_cats: list[str] = []
        for t in v5_terms:
            if t.phrase in phrases and t.sasb_category_primary:
                sasb_cats.append(t.sasb_category_primary)
                break
        sasb_cat_str = sasb_cats[0] if sasb_cats else "none"

        # Reports that contain at least one of this concept's phrases
        hit_report_ids: set[int] = set()
        for tid in tids:
            hit_report_ids |= term_reports.get(tid, set())

        # Relevant reports: those whose institution's SASB industry makes
        # this category material.  If no SASB category ("none"), all 390 relevant.
        if sasb_cat_str == "none":
            relevant_ids = {r.id for r in v5_reports}
        else:
            norm_cat = _norm(sasb_cat_str)
            relevant_ids = set()
            for r in v5_reports:
                inst = report_inst.get(r.id)
                if inst and norm_cat in material_categories_for(inst.sasb_industry):
                    relevant_ids.add(r.id)

        n_rel = len(relevant_ids)
        n_hit = len(hit_report_ids & relevant_ids)
        pct = 100.0 * n_hit / n_rel if n_rel > 0 else 0.0
        flag = " *** BELOW 10%" if pct < 10.0 else ""
        print(f"  {label:<38} {sasb_cat_str:<42} {n_rel:>4} {n_hit:>4} {pct:>5.1f}%{flag}")

    print()

    # ------------------------------------------------------------------
    # 2. Spearman v5 vs v4 (company-year and company level)
    # ------------------------------------------------------------------
    print("=" * 70)
    print("SPEARMAN CORRELATION: v5 vs v4")
    print("=" * 70)

    # Align v4 and v5 by (institution_id, fiscal_year)
    v4_key: dict[tuple[int, int], Report] = {
        (r.institution_id, r.fiscal_year): r for r in v4_reports
    }
    v5_key: dict[tuple[int, int], Report] = {
        (r.institution_id, r.fiscal_year): r for r in v5_reports
    }
    common_keys = sorted(set(v4_key) & set(v5_key))

    if not common_keys:
        print("ERROR: no matching (institution, fiscal_year) pairs between v4 and v5")
        db.close()
        return 1

    pairs: list[tuple[Report, Report]] = [(v4_key[k], v5_key[k]) for k in common_keys]

    def _cy_spearman(field: str) -> tuple[float, int]:
        vals = [(getattr(p4, field), getattr(p5, field)) for p4, p5 in pairs
                if getattr(p4, field) is not None and getattr(p5, field) is not None]
        if len(vals) < 3:
            return float("nan"), 0
        a, b = zip(*vals, strict=False)
        return _spearman(list(a), list(b)), len(vals)

    def _co_spearman(field: str) -> tuple[float, int]:
        by_inst_v4: dict[int, list[float]] = defaultdict(list)
        by_inst_v5: dict[int, list[float]] = defaultdict(list)
        for p4, p5 in pairs:
            v4_val = getattr(p4, field)
            v5_val = getattr(p5, field)
            if v4_val is not None and v5_val is not None:
                by_inst_v4[p4.institution_id].append(v4_val)
                by_inst_v5[p5.institution_id].append(v5_val)
        common = sorted(set(by_inst_v4) & set(by_inst_v5))
        if len(common) < 3:
            return float("nan"), 0
        a = [sum(by_inst_v4[i]) / len(by_inst_v4[i]) for i in common]
        b = [sum(by_inst_v5[i]) / len(by_inst_v5[i]) for i in common]
        return _spearman(a, b), len(common)

    print(f"  {'Metric':<30} {'Company-year':>14}  {'Company':>12}")
    print("  " + "-" * 60)
    for score_field, label in [
        ("e_score", "Environmental"),
        ("s_score", "Social"),
        ("g_score", "Governance"),
        ("composite_score", "Composite"),
    ]:
        cy_r, cy_n = _cy_spearman(score_field)
        co_r, co_n = _co_spearman(score_field)
        print(f"  {label:<30}  r={cy_r:.4f} (n={cy_n})  r={co_r:.4f} (n={co_n})")
    print()

    # ------------------------------------------------------------------
    # 3. 10 companies whose composite rank moves most (v4→v5)
    # ------------------------------------------------------------------
    print("=" * 70)
    print("COMPOSITE RANK MOVERS (v4 -> v5, company-level mean)")
    print("=" * 70)

    by_inst_comp_v4: dict[int, list[float]] = defaultdict(list)
    by_inst_comp_v5: dict[int, list[float]] = defaultdict(list)
    for p4, p5 in pairs:
        if p4.composite_score is not None:
            by_inst_comp_v4[p4.institution_id].append(p4.composite_score)
        if p5.composite_score is not None:
            by_inst_comp_v5[p5.institution_id].append(p5.composite_score)

    v4_avg = {i: sum(v)/len(v) for i, v in by_inst_comp_v4.items()}
    v5_avg = {i: sum(v)/len(v) for i, v in by_inst_comp_v5.items()}
    common_inst = sorted(set(v4_avg) & set(v5_avg))

    # Rank within each version (ascending)
    def _rank_dict(d: dict[int, float]) -> dict[int, float]:
        keys = sorted(d, key=lambda k: d[k])
        ranks: dict[int, float] = {}
        pos = 0
        while pos < len(keys):
            end = pos + 1
            while end < len(keys) and d[keys[end]] == d[keys[pos]]:
                end += 1
            avg = (pos + end + 1) / 2.0
            for k in range(pos, end):
                ranks[keys[k]] = avg
            pos = end
        return ranks

    v4_ranks = _rank_dict({i: v4_avg[i] for i in common_inst})
    v5_ranks = _rank_dict({i: v5_avg[i] for i in common_inst})

    rank_changes = sorted(
        [(v5_ranks[i] - v4_ranks[i], i) for i in common_inst],
        key=lambda x: abs(x[0]),
        reverse=True,
    )

    print(f"  {'Company':<44} {'v4_avg':>7} {'v5_avg':>7} {'v4_rank':>8} {'v5_rank':>8} {'drank':>7}")
    print("  " + "-" * 95)
    for delta, iid in rank_changes[:10]:
        slug = inst_map[iid].slug if iid in inst_map else str(iid)
        print(f"  {slug:<44} {v4_avg[iid]:>7.3f} {v5_avg[iid]:>7.3f} "
              f"{v4_ranks[iid]:>8.1f} {v5_ranks[iid]:>8.1f} {delta:>+7.1f}")

    db.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
