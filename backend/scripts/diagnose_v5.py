"""V5 taxonomy diagnostics — writes docs/term-evidence/V5_DIAGNOSTICS.md.

Four sections:
  1. Contribution: per-term total mentions and pillar share; top-3 new terms
     behind each of the 10 biggest composite rank movers.
  2. Frequency reconciliation: for every new term, hit-rate among (a) relevant
     reports, (b) all 390, (c) full raw text incl. financial-statements pages
     and filtered-out lines (pymupdf, no OCR).  Variant check for the 4 < 10%
     terms.
  3. Sensitivity: Spearman vs v4 and vs v5 for two ablations —
     (a) without "innovation"; (b) without "innovation", "feedback",
     "digital services".
  4. Matcher cross-check: confirm all 16 new term concepts are loaded;
     plain regex scan of stored MatchEvidence sentences vs matcher output;
     up to 5 missed-sentence examples per term.

Run from backend/ with the venv active:
    python scripts/diagnose_v5.py
"""
from __future__ import annotations

import re
import sys
from collections import defaultdict
from pathlib import Path

BACKEND = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND))

from dotenv import load_dotenv  # noqa: E402

load_dotenv(BACKEND / ".env")

# ---------------------------------------------------------------------------
# New v5 term definitions  (concept → [canonical phrases])
# ---------------------------------------------------------------------------

NEW_TERM_LABELS: list[tuple[str, list[str], str, str | None]] = [
    # (label, phrases, pillar, sasb_cat)
    ("climate policy",             ["climate policy"],                                     "E", "GHG Emissions"),
    ("pollution",                  ["pollution"],                                           "E", "Ecological Impacts"),
    ("resource use",               ["resource use"],                                        "E", "Materials Sourcing & Efficiency"),
    ("innovation",                 ["innovation"],                                          "E", None),
    ("employee engagement",        ["employee engagement"],                                 "S", "Employee Engagement, Diversity & Inclusion"),
    ("employee ownership/share",   ["employee ownership", "employee share ownership"],      "S", "Employee Engagement, Diversity & Inclusion"),
    ("pension benefits",           ["pension benefits"],                                    "S", "Labor Practices"),
    ("end of service",             ["end of service", "end-of-service"],                   "S", "Labor Practices"),
    ("poverty",                    ["poverty"],                                             "S", "Human Rights & Community Relations"),
    ("customer/client needs",      ["customer needs", "customers' needs",
                                    "client needs", "clients' needs"],                     "S", "Customer Welfare"),
    ("feedback",                   ["feedback"],                                            "S", None),
    ("digital services",           ["digital services"],                                   "S", "Access & Affordability"),
    ("board meeting variants",     ["board meeting", "meetings of directors",
                                    "meetings of the board"],                              "G", None),
    ("dividend policy",            ["dividend policy"],                                    "G", None),
    ("stakeholder engagement",     ["stakeholder engagement"],                             "G", None),
    ("incentive plan(s)",          ["incentive plan"],                                     "G", None),
]

# Variant patterns for the 4 below-10% terms (plain regex, case-insensitive)
VARIANT_PATTERNS: dict[str, list[str]] = {
    "climate policy": [
        r"climate[- ]change[- ]policy",
        r"climate[- ]related[- ]policy",
        r"climate[- ]risk[- ]policy",
        r"climate[- ]action[- ]plan",
        r"climate[- ]strategy",
    ],
    "employee engagement": [
        r"engagement of employees",
        r"employee[s]? survey",
        r"staff engagement",
        r"workforce engagement",
        r"employee[s]? satisfaction survey",
    ],
    "employee ownership/share": [
        r"employee share scheme",
        r"employee[s]? share plan",
        r"employee stock",
        r"ESOP\b",
        r"share ownership plan",
    ],
    "pension benefits": [
        r"\bpension\b",
        r"pension fund",
        r"pension plan",
        r"retirement benefit",
        r"post.employment benefit",
        r"end[- ]of[- ]service benefit",
    ],
}

# Slugs of the 10 biggest composite rank movers (from analyse_v5.py output)
RANK_MOVER_SLUGS = [
    "bank-albilad",
    "oman-telecommunications-company-otel",
    "mobile-telecommunications-co-saudi-arabia-zain",
    "kuwait-telecommunications-company",
    "saudi-aramco",
    "etihad-etisalat-mobily",
    "qatar-fuel-company-woqod",
    "riyad-bank",
    "aldar-properties-pjsc",
    "qatar-gas-transport-co-nakilat",
]

V4_PIPELINE = "0.4.2"
V5_PIPELINE = "0.5.0"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _spearman(a: list[float], b: list[float]) -> float:
    n = len(a)
    if n < 3:
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


def _rank_scores_0_10(values: list[float | None]) -> list[float | None]:
    indexed = [(v, i) for i, v in enumerate(values) if v is not None]
    n = len(indexed)
    if n < 2:
        return [None if v is None else 0.0 for v in values]
    result: list[float | None] = [None] * len(values)
    sorted_vals = sorted(indexed, key=lambda x: x[0])
    avg_ranks: dict[int, float] = {}
    pos = 0
    while pos < n:
        end = pos + 1
        while end < n and sorted_vals[end][0] == sorted_vals[pos][0]:
            end += 1
        avg = (pos + end + 1) / 2.0
        for k in range(pos, end):
            avg_ranks[sorted_vals[k][1]] = avg
        pos = end
    for _v, i in indexed:
        result[i] = round(10.0 * (avg_ranks[i] - 1) / (n - 1), 4)
    return result


def _dedup_reports(reports: list) -> list:
    seen: dict[tuple, int] = {}
    result: list = []
    for r in reports:
        key = (r.source_document_id, r.pipeline_version) if r.source_document_id \
            else (r.institution_id, r.fiscal_year, r.pipeline_version)
        if key in seen:
            result[seen[key]] = r
        else:
            seen[key] = len(result)
            result.append(r)
    return result


# ---------------------------------------------------------------------------
# Part 2c: raw full-text search using pymupdf (no OCR)
# ---------------------------------------------------------------------------

def _raw_text_from_pdf(file_path: str) -> str:
    """Extract all text from all pages of a PDF without OCR or any filtering."""
    import pymupdf  # type: ignore[import]
    from app.services.storage import read_pdf_bytes
    try:
        pdf_bytes = read_pdf_bytes(file_path)
        doc = pymupdf.open(stream=pdf_bytes, filetype="pdf")
        parts: list[str] = []
        for page in doc:
            parts.append(page.get_text())
        doc.close()
        return " ".join(parts).lower()
    except Exception:
        return ""


def _build_term_patterns() -> dict[str, re.Pattern[str]]:
    """Build regex patterns for all new term phrases (plain word-boundary search)."""
    patterns: dict[str, re.Pattern[str]] = {}
    for label, phrases, _pillar, _sasb in NEW_TERM_LABELS:
        combined = "|".join(
            re.escape(ph.replace("'", "'?'?").replace("-", "[-]?"))
            for ph in phrases
        )
        patterns[label] = re.compile(r"\b(" + combined + r")\b", re.IGNORECASE)
    return patterns


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    import app.models.institution
    import app.models.provenance
    import app.models.report
    import app.models.review
    import app.models.run
    import app.models.score
    import app.models.taxonomy
    from app.database import SessionLocal
    from app.models.institution import Institution
    from app.models.provenance import SourceDocument
    from app.models.report import Report, ReportStatus
    from app.models.score import MatchEvidence
    from app.models.taxonomy import TaxonomyVersion, Term
    from app.services.matcher import TaxonomyMatcher
    from app.services.sasb_materiality import _norm, material_categories_for

    db = SessionLocal()

    # ------------------------------------------------------------------
    # Load taxonomy versions + report lists
    # ------------------------------------------------------------------
    tv_v4 = db.query(TaxonomyVersion).filter(TaxonomyVersion.hash.like("313c0eabe0%")).first()
    tv_v5 = db.query(TaxonomyVersion).filter(TaxonomyVersion.note.like("v5:%")).first()
    assert tv_v4 and tv_v5, "Could not find v4/v5 taxonomy versions"

    def _load_reports(pipeline: str) -> list:
        raw = (
            db.query(Report)
            .join(Institution)
            .filter(
                Report.status == ReportStatus.scored,
                Report.pipeline_version == pipeline,
                Institution.active.is_(True),
            )
            .order_by(Institution.id, Report.fiscal_year, Report.id)
            .all()
        )
        return _dedup_reports(raw)

    v4_reports = _load_reports(V4_PIPELINE)
    v5_reports = _load_reports(V5_PIPELINE)
    print(f"v4 reports: {len(v4_reports)}  v5 reports: {len(v5_reports)}")

    inst_map: dict[int, Institution] = {
        i.id: i for i in db.query(Institution).filter(Institution.active.is_(True)).all()
    }
    v5_report_ids = [r.id for r in v5_reports]
    v5_by_rid: dict[int, Report] = {r.id: r for r in v5_reports}

    # Term phrase -> Term id/object mapping
    all_terms = db.query(Term).all()
    phrase_to_tid: dict[str, int] = {t.phrase: t.id for t in all_terms}
    tid_to_term: dict[int, Term] = {t.id: t for t in all_terms}

    # New-term IDs: all phrase IDs belonging to new v5 term concepts
    new_tids_by_label: dict[str, list[int]] = {}
    all_new_tids: set[int] = set()
    for label, phrases, _p, _s in NEW_TERM_LABELS:
        tids = [phrase_to_tid[ph] for ph in phrases if ph in phrase_to_tid]
        new_tids_by_label[label] = tids
        all_new_tids.update(tids)

    # ------------------------------------------------------------------
    # Load MatchEvidence for v5 new terms
    # ------------------------------------------------------------------
    print("Loading new-term MatchEvidence...")
    me_new = (
        db.query(MatchEvidence)
        .filter(
            MatchEvidence.pipeline_version == V5_PIPELINE,
            MatchEvidence.taxonomy_version_id == tv_v5.id,
            MatchEvidence.report_id.in_(v5_report_ids),
            MatchEvidence.term_id.in_(list(all_new_tids)),
        )
        .all()
    )
    # new-term matches: report_id -> {term_id -> count}
    new_me_by_report: dict[int, dict[int, int]] = defaultdict(lambda: defaultdict(int))
    new_me_by_tid: dict[int, list[MatchEvidence]] = defaultdict(list)
    for me in me_new:
        new_me_by_report[me.report_id][me.term_id] += 1
        new_me_by_tid[me.term_id].append(me)

    # Load ALL MatchEvidence sentences (v5) for the cross-check corpus
    print("Loading all v5 MatchEvidence sentences (for cross-check)...")
    me_all_v5 = (
        db.query(MatchEvidence.report_id, MatchEvidence.term_id, MatchEvidence.sentence_text)
        .filter(
            MatchEvidence.pipeline_version == V5_PIPELINE,
            MatchEvidence.taxonomy_version_id == tv_v5.id,
            MatchEvidence.report_id.in_(v5_report_ids),
        )
        .all()
    )
    # Set of (report_id, term_id) already matched
    matched_pairs: set[tuple[int, int]] = {(me.report_id, me.term_id) for me in me_all_v5}
    # All sentences per report (for cross-check)
    sentences_by_report: dict[int, list[str]] = defaultdict(list)
    for me in me_all_v5:
        sentences_by_report[me.report_id].append(me.sentence_text.lower())

    # ------------------------------------------------------------------
    # SASB relevance helper
    # ------------------------------------------------------------------
    def relevant_report_ids(sasb_cat: str | None) -> set[int]:
        if not sasb_cat:
            return set(v5_report_ids)
        norm = _norm(sasb_cat)
        return {
            r.id for r in v5_reports
            if r.institution_id in inst_map
            and norm in material_categories_for(inst_map[r.institution_id].sasb_industry)
        }

    # ------------------------------------------------------------------
    # PART 1: Contribution
    # ------------------------------------------------------------------
    print("Part 1: Contribution...")

    # total mentions per new term concept
    contribution: list[tuple[str, str, int, set[int]]] = []
    grand_total = sum(len(rows) for rows in new_me_by_tid.values())
    for label, phrases, pillar, _sasb in NEW_TERM_LABELS:
        tids = new_tids_by_label[label]
        total_m = sum(len(new_me_by_tid[tid]) for tid in tids)
        hit_reports = set()
        for tid in tids:
            hit_reports |= {me.report_id for me in new_me_by_tid[tid]}
        contribution.append((label, pillar, total_m, hit_reports))

    grand_by_pillar = {"E": 0, "S": 0, "G": 0}
    for _, pillar, total_m, _ in contribution:
        grand_by_pillar[pillar] += total_m

    # Top-3 new terms per rank mover
    slug_to_iid = {inst.slug: iid for iid, inst in inst_map.items()}
    mover_data: list[dict] = []
    for slug in RANK_MOVER_SLUGS:
        iid = slug_to_iid.get(slug)
        if iid is None:
            continue
        company_reports = [r for r in v5_reports if r.institution_id == iid]
        term_counts: dict[str, int] = defaultdict(int)
        for r in company_reports:
            for label, phrases, _p, _s in NEW_TERM_LABELS:
                tids = new_tids_by_label[label]
                for tid in tids:
                    term_counts[label] += new_me_by_report[r.id].get(tid, 0)
        top3 = sorted(term_counts.items(), key=lambda x: x[1], reverse=True)[:3]
        # Get v4->v5 rank delta (reconstruct from stored composite scores)
        v4_reps = [r for r in v4_reports if r.institution_id == iid]
        v5_reps = [r for r in v5_reports if r.institution_id == iid]
        v4_avg = (sum(r.composite_score for r in v4_reps if r.composite_score is not None) /
                  len([r for r in v4_reps if r.composite_score is not None])) if v4_reps else None
        v5_avg = (sum(r.composite_score for r in v5_reps if r.composite_score is not None) /
                  len([r for r in v5_reps if r.composite_score is not None])) if v5_reps else None
        mover_data.append({
            "slug": slug, "top3": top3,
            "v4_avg": v4_avg, "v5_avg": v5_avg,
        })

    # Compute actual rank delta from company-level averages
    by_inst_v4: dict[int, list[float]] = defaultdict(list)
    by_inst_v5: dict[int, list[float]] = defaultdict(list)
    for r in v4_reports:
        if r.composite_score is not None:
            by_inst_v4[r.institution_id].append(r.composite_score)
    for r in v5_reports:
        if r.composite_score is not None:
            by_inst_v5[r.institution_id].append(r.composite_score)

    def _avg_rank(d: dict[int, list[float]]) -> dict[int, float]:
        avgs = {i: sum(v) / len(v) for i, v in d.items()}
        keys = sorted(avgs, key=lambda k: avgs[k])
        ranks: dict[int, float] = {}
        pos = 0
        while pos < len(keys):
            end = pos + 1
            while end < len(keys) and avgs[keys[end]] == avgs[keys[pos]]:
                end += 1
            avg = (pos + end + 1) / 2.0
            for k in range(pos, end):
                ranks[keys[k]] = avg
            pos = end
        return ranks

    v4_ranks = _avg_rank(by_inst_v4)
    v5_ranks = _avg_rank(by_inst_v5)
    for md in mover_data:
        slug = md["slug"]
        iid = slug_to_iid.get(slug, -1)
        delta = v5_ranks.get(iid, 0) - v4_ranks.get(iid, 0)
        md["delta"] = delta

    # ------------------------------------------------------------------
    # PART 2a/2b: Frequency from DB
    # ------------------------------------------------------------------
    print("Part 2a/2b: Frequency from DB...")
    freq_data: list[dict] = []
    for label, phrases, _pillar, sasb_cat in NEW_TERM_LABELS:
        tids = new_tids_by_label[label]
        rel_ids = relevant_report_ids(sasb_cat)
        hit_ids: set[int] = set()
        total_mentions = 0
        for tid in tids:
            for me in new_me_by_tid[tid]:
                hit_ids.add(me.report_id)
                total_mentions += 1
        a_n = len(rel_ids)
        a_hit = len(hit_ids & rel_ids)
        b_hit = len(hit_ids)
        freq_data.append({
            "label": label, "phrases": phrases,
            "sasb_cat": sasb_cat or "none",
            "a_n": a_n, "a_hit": a_hit,
            "b_hit": b_hit, "total_mentions": total_mentions,
        })

    # ------------------------------------------------------------------
    # PART 2c: Full-text scan using pymupdf (all pages, no filtering)
    # ------------------------------------------------------------------
    print("Part 2c: Full-text scan of all 390 PDFs...")
    term_patterns = _build_term_patterns()

    # load source document file paths
    sd_map: dict[int, SourceDocument] = {}
    all_sds = db.query(SourceDocument).filter(
        SourceDocument.id.in_([r.source_document_id for r in v5_reports if r.source_document_id])
    ).all()
    for sd in all_sds:
        sd_map[sd.id] = sd

    # Full-text hit counts: label -> set of report IDs with >= 1 raw hit
    fulltext_hits: dict[str, set[int]] = {label: set() for label, *_ in NEW_TERM_LABELS}
    fulltext_mention_counts: dict[str, int] = {label: 0 for label, *_ in NEW_TERM_LABELS}

    # Also collect variant hits for 4 below-10% terms
    variant_hits: dict[str, dict[str, int]] = {
        label: {v: 0 for v in variants}
        for label, variants in VARIANT_PATTERNS.items()
    }
    variant_compiled: dict[str, list[tuple[str, re.Pattern[str]]]] = {
        label: [(v, re.compile(v, re.IGNORECASE)) for v in variants]
        for label, variants in VARIANT_PATTERNS.items()
    }

    done = 0
    for r in v5_reports:
        sd = sd_map.get(r.source_document_id) if r.source_document_id else None
        if sd is None:
            done += 1
            continue
        raw = _raw_text_from_pdf(sd.file_path)
        if not raw:
            done += 1
            continue
        for label, pat in term_patterns.items():
            hits = pat.findall(raw)
            if hits:
                fulltext_hits[label].add(r.id)
                fulltext_mention_counts[label] += len(hits)
        for label, vlist in variant_compiled.items():
            for vstr, vpat in vlist:
                if vpat.search(raw):
                    variant_hits[label][vstr] += 1
        done += 1
        if done % 50 == 0:
            print(f"  {done}/{len(v5_reports)} PDFs scanned")

    print(f"  {done}/{len(v5_reports)} PDFs scanned (done)")

    # ------------------------------------------------------------------
    # PART 3: Sensitivity analysis
    # ------------------------------------------------------------------
    print("Part 3: Sensitivity analysis...")

    # Build per-report density adjustments
    # new term contributions to densities
    innovation_tids = set(new_tids_by_label["innovation"])
    feedback_tids = set(new_tids_by_label["feedback"])
    digital_tids = set(new_tids_by_label["digital services"])

    def _term_contribution(report: Report, tids: set[int]) -> float:
        """Density contribution of the given term IDs to the report (per 1000 words)."""
        if not report.narrative_word_count:
            return 0.0
        count = sum(new_me_by_report[report.id].get(tid, 0) for tid in tids)
        return count / report.narrative_word_count * 1000.0

    # Build adjusted densities for all reports
    # scen_a: without innovation (affects E)
    # scen_b: without innovation + feedback + digital (affects E and S)
    adj_e_a: list[float | None] = []
    adj_e_b: list[float | None] = []
    adj_s_b: list[float | None] = []
    base_e: list[float | None] = []
    base_s: list[float | None] = []
    base_g: list[float | None] = []

    for r in v5_reports:
        base_e.append(r.e_density)
        base_s.append(r.s_density)
        base_g.append(r.g_density)
        innov_c = _term_contribution(r, innovation_tids)
        feed_c = _term_contribution(r, feedback_tids)
        dig_c = _term_contribution(r, digital_tids)
        e_a = (r.e_density - innov_c) if r.e_density is not None else None
        e_b = e_a
        s_b = (r.s_density - feed_c - dig_c) if r.s_density is not None else None
        adj_e_a.append(max(0.0, e_a) if e_a is not None else None)
        adj_e_b.append(max(0.0, e_b) if e_b is not None else None)
        adj_s_b.append(max(0.0, s_b) if s_b is not None else None)

    def _composite_scores(
        e_dens: list[float | None],
        s_dens: list[float | None],
        g_dens: list[float | None],
    ) -> list[float | None]:
        e_sc = _rank_scores_0_10(e_dens)
        s_sc = _rank_scores_0_10(s_dens)
        g_sc = _rank_scores_0_10(g_dens)
        result: list[float | None] = []
        for e, s, g in zip(e_sc, s_sc, g_sc, strict=False):
            if e is not None and s is not None and g is not None:
                result.append(round((e + s + g) / 3.0, 4))
            else:
                result.append(None)
        return result

    def _company_level(
        reports: list, scores: list[float | None]
    ) -> tuple[list[float], list[float], list[int]]:
        by_inst: dict[int, list[float]] = defaultdict(list)
        for r, sc in zip(reports, scores, strict=False):
            if sc is not None:
                by_inst[r.institution_id].append(sc)
        common_inst = sorted(set(by_inst))
        avgs = [sum(by_inst[i]) / len(by_inst[i]) for i in common_inst]
        return avgs, avgs, common_inst  # return inst list too

    # Scenario a: without innovation
    comp_a = _composite_scores(adj_e_a, base_s, base_g)
    # Scenario b: without innovation + feedback + digital
    comp_b = _composite_scores(adj_e_b, adj_s_b, base_g)
    # v5 baseline and v4 baselines
    comp_v5 = [r.composite_score for r in v5_reports]

    # Get v4 composite scores aligned with v5 reports by (inst_id, fiscal_year)
    v4_key: dict[tuple[int, int], float | None] = {
        (r.institution_id, r.fiscal_year): r.composite_score
        for r in v4_reports
    }

    def _sensitivity_spearman(
        adj_comp: list[float | None],
        compare_a: list[float | None],  # v4 composite aligned
        compare_b: list[float | None],  # v5 composite
        reports: list,
        label_a: str,
        label_b: str,
    ) -> dict[str, float]:
        # company-year level
        pairs_a = [(a, c) for a, c in zip(adj_comp, compare_a, strict=False)
                   if a is not None and c is not None]
        pairs_b = [(a, c) for a, c in zip(adj_comp, compare_b, strict=False)
                   if a is not None and c is not None]
        cy_vs_v4 = _spearman([p[0] for p in pairs_a], [p[1] for p in pairs_a])
        cy_vs_v5 = _spearman([p[0] for p in pairs_b], [p[1] for p in pairs_b])

        # company level
        by_adj: dict[int, list[float]] = defaultdict(list)
        by_cv4: dict[int, list[float]] = defaultdict(list)
        by_cv5: dict[int, list[float]] = defaultdict(list)
        for r, adj, ca, cb in zip(reports, adj_comp, compare_a, compare_b, strict=False):
            if adj is not None:
                by_adj[r.institution_id].append(adj)
            if ca is not None:
                by_cv4[r.institution_id].append(ca)
            if cb is not None:
                by_cv5[r.institution_id].append(cb)
        common_a = sorted(set(by_adj) & set(by_cv4))
        common_b = sorted(set(by_adj) & set(by_cv5))
        co_vs_v4 = _spearman(
            [sum(by_adj[i]) / len(by_adj[i]) for i in common_a],
            [sum(by_cv4[i]) / len(by_cv4[i]) for i in common_a],
        )
        co_vs_v5 = _spearman(
            [sum(by_adj[i]) / len(by_adj[i]) for i in common_b],
            [sum(by_cv5[i]) / len(by_cv5[i]) for i in common_b],
        )
        return {
            "cy_vs_v4": cy_vs_v4, "cy_vs_v5": cy_vs_v5,
            "co_vs_v4": co_vs_v4, "co_vs_v5": co_vs_v5,
            "n_cy": len(pairs_a), "n_co_a": len(common_a), "n_co_b": len(common_b),
        }

    # Also need E, S, G pillar sensitivity
    def _pillar_spearman_scen(
        adj_dens: list[float | None],
        base_dens_v4: list[float | None],
        base_dens_v5: list[float | None],
        reports: list,
    ) -> tuple[float, float, float, float]:
        pairs_v4 = [(a, b) for a, b in zip(adj_dens, base_dens_v4, strict=False)
                    if a is not None and b is not None]
        pairs_v5 = [(a, b) for a, b in zip(adj_dens, base_dens_v5, strict=False)
                    if a is not None and b is not None]
        cy_v4 = _spearman([p[0] for p in pairs_v4], [p[1] for p in pairs_v4])
        cy_v5 = _spearman([p[0] for p in pairs_v5], [p[1] for p in pairs_v5])
        # company level
        by_adj: dict[int, list[float]] = defaultdict(list)
        by_v4: dict[int, list[float]] = defaultdict(list)
        by_v5: dict[int, list[float]] = defaultdict(list)
        for r, a, b4, b5 in zip(reports, adj_dens, base_dens_v4, base_dens_v5, strict=False):
            if a is not None:
                by_adj[r.institution_id].append(a)
            if b4 is not None:
                by_v4[r.institution_id].append(b4)
            if b5 is not None:
                by_v5[r.institution_id].append(b5)
        c_v4 = sorted(set(by_adj) & set(by_v4))
        c_v5 = sorted(set(by_adj) & set(by_v5))
        co_v4 = _spearman(
            [sum(by_adj[i]) / len(by_adj[i]) for i in c_v4],
            [sum(by_v4[i]) / len(by_v4[i]) for i in c_v4],
        )
        co_v5 = _spearman(
            [sum(by_adj[i]) / len(by_adj[i]) for i in c_v5],
            [sum(by_v5[i]) / len(by_v5[i]) for i in c_v5],
        )
        return cy_v4, cy_v5, co_v4, co_v5

    v4_e = [v4_key.get((r.institution_id, r.fiscal_year), None) and
            next((rv.e_density for rv in v4_reports
                  if rv.institution_id == r.institution_id and rv.fiscal_year == r.fiscal_year),
                 None)
            for r in v5_reports]
    v4_s = [next((rv.s_density for rv in v4_reports
                  if rv.institution_id == r.institution_id and rv.fiscal_year == r.fiscal_year),
                 None)
            for r in v5_reports]
    v4_g = [next((rv.g_density for rv in v4_reports
                  if rv.institution_id == r.institution_id and rv.fiscal_year == r.fiscal_year),
                 None)
            for r in v5_reports]
    v4_comp_aligned = [v4_key.get((r.institution_id, r.fiscal_year)) for r in v5_reports]

    scen_a_stats = _sensitivity_spearman(comp_a, v4_comp_aligned, comp_v5, v5_reports,
                                          "v4_comp", "v5_comp")
    scen_b_stats = _sensitivity_spearman(comp_b, v4_comp_aligned, comp_v5, v5_reports,
                                          "v4_comp", "v5_comp")

    # Pillar-level sensitivity (scenario a: E only; scenario b: E and S)
    sa_e_cy_v4, sa_e_cy_v5, sa_e_co_v4, sa_e_co_v5 = _pillar_spearman_scen(
        adj_e_a, v4_e, base_e, v5_reports)
    sb_e_cy_v4, sb_e_cy_v5, sb_e_co_v4, sb_e_co_v5 = _pillar_spearman_scen(
        adj_e_b, v4_e, base_e, v5_reports)
    sb_s_cy_v4, sb_s_cy_v5, sb_s_co_v4, sb_s_co_v5 = _pillar_spearman_scen(
        adj_s_b, v4_s, base_s, v5_reports)

    # ------------------------------------------------------------------
    # PART 4: Matcher cross-check
    # ------------------------------------------------------------------
    print("Part 4: Matcher cross-check...")

    # Confirm all 16 new term concepts are loaded in the v5 matcher
    v5_terms_all = db.query(Term).all()
    matcher = TaxonomyMatcher(v5_terms_all)
    loaded_phrases = set()
    for label_str, tid in matcher.term_by_label.items():
        term = tid_to_term.get(tid)
        if term:
            loaded_phrases.add(term.phrase)

    # For each new term concept, check if all its phrases are loaded
    matcher_check: list[tuple[str, list[str], list[bool]]] = []
    for label, phrases, _p, _s in NEW_TERM_LABELS:
        loaded = [ph in loaded_phrases for ph in phrases]
        matcher_check.append((label, phrases, loaded))

    # Plain-text cross-check: for each new term, regex-search all v5
    # sentences stored in MatchEvidence (any term), compare with ME counts
    cross_check: list[dict] = []
    for label, phrases, _pillar, _sasb in NEW_TERM_LABELS:
        tids = new_tids_by_label[label]
        # Regex pattern: match any of the phrases case-insensitively
        pat_str = "|".join(
            r"\b" + re.escape(ph.replace("'", "['’]?")) + r"\b"
            for ph in phrases
        )
        pat = re.compile(pat_str, re.IGNORECASE)

        # Count sentences found by regex in the corpus
        regex_hit_reports: set[int] = set()
        missed_examples: list[tuple[int, str]] = []

        for rid, sents in sentences_by_report.items():
            for sent in sents:
                if pat.search(sent):
                    regex_hit_reports.add(rid)
                    # Check if this (report, term) pair is already in MatchEvidence
                    for tid in tids:
                        if (rid, tid) not in matched_pairs:
                            if len(missed_examples) < 5:
                                missed_examples.append((rid, sent[:200]))
                            break

        matcher_hit_count = len({me.report_id for tid in tids for me in new_me_by_tid[tid]})
        cross_check.append({
            "label": label,
            "phrases": phrases,
            "regex_hits": len(regex_hit_reports),
            "matcher_hits": matcher_hit_count,
            "missed_examples": missed_examples,
        })

    db.close()

    # ------------------------------------------------------------------
    # Write V5_DIAGNOSTICS.md
    # ------------------------------------------------------------------
    print("Writing V5_DIAGNOSTICS.md...")
    out_path = BACKEND.parent / "docs" / "term-evidence" / "V5_DIAGNOSTICS.md"
    lines: list[str] = []

    def w(s: str = "") -> None:
        lines.append(s)

    w("# V5 Taxonomy Diagnostics")
    w()
    w("Generated: 2026-10-20  |  Pipeline: 0.5.0  |  Taxonomy v5: 15242b4c  |  N = 390 company-years")
    w()
    w("---")
    w()

    # ---- Part 1 --------------------------------------------------------
    w("## 1. Term contribution")
    w()
    w("### 1.1 New-term mentions across all 390 reports")
    w()
    w("| Concept | Pillar | Total mentions | Share of new-term mentions | Pillar share |")
    w("|---|---|---|---|---|")
    for label, pillar, total_m, _ in contribution:
        share_all = f"{100 * total_m / grand_total:.1f}%" if grand_total else "—"
        share_pil = f"{100 * total_m / grand_by_pillar[pillar]:.1f}%" if grand_by_pillar[pillar] else "—"
        w(f"| {label} | {pillar} | {total_m:,} | {share_all} | {share_pil} |")
    w(f"| **TOTAL** | | **{grand_total:,}** | 100.0% | |")
    w()
    w(f"New-term grand total: {grand_total:,} mentions "
      f"(E: {grand_by_pillar['E']:,} / S: {grand_by_pillar['S']:,} / G: {grand_by_pillar['G']:,})")
    w()

    w("### 1.2 New-term mentions behind top-10 composite rank movers")
    w()
    w("| Company | delta-rank | Top-1 term | mentions | Top-2 term | mentions | Top-3 term | mentions |")
    w("|---|---|---|---|---|---|---|---|")
    for md in mover_data:
        delta = md.get("delta", 0.0)
        delta_str = f"{delta:+.1f}"
        t3 = md["top3"]
        cells = []
        for i in range(3):
            if i < len(t3):
                cells += [t3[i][0], str(t3[i][1])]
            else:
                cells += ["—", "—"]
        w(f"| {md['slug']} | {delta_str} | {cells[0]} | {cells[1]} | {cells[2]} | {cells[3]} | {cells[4]} | {cells[5]} |")
    w()

    # ---- Part 2 --------------------------------------------------------
    w("## 2. Frequency reconciliation")
    w()
    w("Columns: **(a)** reports containing term / relevant reports (SASB-material industries);")
    w("**(b)** reports containing term / all 390; **(c)** reports with at least one")
    w("raw-text hit (all PDF pages incl. financial statements and filtered-out lines,")
    w("pymupdf extraction, no OCR fallback).")
    w()
    w("| Concept | SASB category | (a) rel hit | (a) % | (b) all hit | (b) % | (c) full-text hit | (c) % |")
    w("|---|---|---|---|---|---|---|---|")
    for fd in freq_data:
        a_pct = f"{100 * fd['a_hit'] / fd['a_n']:.1f}%" if fd['a_n'] else "—"
        b_pct = f"{100 * fd['b_hit'] / 390:.1f}%"
        c_hit = len(fulltext_hits[fd['label']])
        c_pct = f"{100 * c_hit / 390:.1f}%"
        flag_a = " ***" if (fd['a_hit'] / fd['a_n'] < 0.10 if fd['a_n'] else False) else ""
        w(f"| {fd['label']} | {fd['sasb_cat']} | {fd['a_hit']}/{fd['a_n']} | {a_pct}{flag_a} | "
          f"{fd['b_hit']}/390 | {b_pct} | {c_hit}/390 | {c_pct} |")
    w()
    w("*** = below 10 % threshold on (a).")
    w()

    w("### 2.1 Variant check for 4 below-10% terms")
    w()
    w("For each variant: number of reports with at least one raw-text hit "
      "(full PDF text, case-insensitive regex).")
    w()
    below10 = [label for label, _, _, sasb_cat in NEW_TERM_LABELS
               if any(fd["label"] == label and
                      (fd["a_hit"] / fd["a_n"] < 0.10 if fd["a_n"] else False)
                      for fd in freq_data)]
    for label in list(VARIANT_PATTERNS.keys()):
        w(f"**{label}**")
        w()
        w("| Variant pattern | Reports with hit |")
        w("|---|---|")
        # canonical term itself
        c_hit = len(fulltext_hits[label])
        w(f"| *(canonical)* | {c_hit}/390 |")
        for vstr, vhits in variant_hits[label].items():
            w(f"| `{vstr}` | {vhits}/390 |")
        w()

    # ---- Part 3 --------------------------------------------------------
    w("## 3. Sensitivity analysis")
    w()
    w("Spearman rho comparing adjusted composite with v4 and v5 baselines.")
    w("Densities are re-computed by subtracting the excluded term(s)'")
    w("contribution from each report's stored density, then re-ranked.")
    w()
    w("### 3.1 Without 'innovation' (E pillar only)")
    w()
    w("| Metric | vs v4 company-year | vs v5 company-year | vs v4 company | vs v5 company |")
    w("|---|---|---|---|---|")
    w(f"| E density | {sa_e_cy_v4:.4f} | {sa_e_cy_v5:.4f} | {sa_e_co_v4:.4f} | {sa_e_co_v5:.4f} |")
    w(f"| S density | — (unchanged) | — | — | — |")
    w(f"| G density | — (unchanged) | — | — | — |")
    w(f"| Composite | {scen_a_stats['cy_vs_v4']:.4f} (n={scen_a_stats['n_cy']}) | "
      f"{scen_a_stats['cy_vs_v5']:.4f} | "
      f"{scen_a_stats['co_vs_v4']:.4f} (n={scen_a_stats['n_co_a']}) | "
      f"{scen_a_stats['co_vs_v5']:.4f} |")
    w()

    w("### 3.2 Without 'innovation', 'feedback', 'digital services'")
    w()
    w("| Metric | vs v4 company-year | vs v5 company-year | vs v4 company | vs v5 company |")
    w("|---|---|---|---|---|")
    w(f"| E density | {sb_e_cy_v4:.4f} | {sb_e_cy_v5:.4f} | {sb_e_co_v4:.4f} | {sb_e_co_v5:.4f} |")
    w(f"| S density | {sb_s_cy_v4:.4f} | {sb_s_cy_v5:.4f} | {sb_s_co_v4:.4f} | {sb_s_co_v5:.4f} |")
    w(f"| G density | — (unchanged) | — | — | — |")
    w(f"| Composite | {scen_b_stats['cy_vs_v4']:.4f} (n={scen_b_stats['n_cy']}) | "
      f"{scen_b_stats['cy_vs_v5']:.4f} | "
      f"{scen_b_stats['co_vs_v4']:.4f} (n={scen_b_stats['n_co_b']}) | "
      f"{scen_b_stats['co_vs_v5']:.4f} |")
    w()

    # ---- Part 4 --------------------------------------------------------
    w("## 4. Matcher cross-check")
    w()
    w("### 4.1 V5 terms confirmed in matcher")
    w()
    w("| Concept | Phrases | All loaded? |")
    w("|---|---|---|")
    for label, phrases, loaded_list in matcher_check:
        all_ok = all(loaded_list)
        status = "YES" if all_ok else "**PARTIAL — see below**"
        ph_str = ", ".join(
            f"`{ph}` ({'OK' if ok else '**MISSING**'})"
            for ph, ok in zip(phrases, loaded_list, strict=False)
        )
        w(f"| {label} | {ph_str} | {status} |")
    w()

    w("### 4.2 Plain-text vs matcher comparison")
    w()
    w("Method: regex search on all sentences stored in v5 MatchEvidence "
      "(any term, ~all kept narrative sentences), compared with the matcher's "
      "MatchEvidence rows for each new term.  A *miss* is a sentence that "
      "contains the term as a plain string but has no MatchEvidence row for "
      "that term in that report.  Note: this corpus covers sentences that "
      "matched *some* v5 term; sentences with no term match at all are not "
      "included (but see column (c) in §2 for full-text counts).")
    w()
    w("| Concept | Regex hits (reports) | Matcher hits (reports) | Misses (reports) |")
    w("|---|---|---|---|")
    has_misses = False
    for cc in cross_check:
        misses = cc["regex_hits"] - cc["matcher_hits"]
        if misses != 0:
            has_misses = True
        w(f"| {cc['label']} | {cc['regex_hits']} | {cc['matcher_hits']} | "
          f"{'**' + str(misses) + '** (investigate)' if misses > 0 else str(misses)} |")
    w()

    if has_misses:
        w("#### 4.2.1 Missed-sentence examples")
        w()
        for cc in cross_check:
            if not cc["missed_examples"]:
                continue
            w(f"**{cc['label']}** — up to 5 sentences found by regex but no matcher row "
              f"for this term in that report:")
            w()
            for rid, sent in cc["missed_examples"]:
                inst = inst_map.get(v5_by_rid[rid].institution_id, None) if rid in v5_by_rid else None
                slug = inst.slug if inst else str(rid)
                w(f"> *report {slug}*: {sent}")
                w()
    else:
        w("No misses detected in the MatchEvidence sentence corpus for any new term.")
    w()
    w("*Cross-check coverage note*: the sentence corpus above covers sentences that "
      "matched at least one v5 term.  Any occurrence of a new term in a sentence "
      "that matched *no* other term would not appear here; the full-text counts in "
      "§2 column (c) provide the upper-bound check for those cases.")
    w()

    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Written: {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
