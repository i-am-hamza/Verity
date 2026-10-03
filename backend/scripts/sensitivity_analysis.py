"""Sensitivity analysis for the Session 6 leaderboard.

Tests how stable the within-sector rankings are under three perturbations:

1. Weight jitter: multiply every term weight by U(0.8, 1.2), 1000 seeded
   draws. Report per-institution median rank + 5-95 percentile interval +
   Kendall tau distribution against the baseline ranking.
2. Equal weights: set every term and category weight to 1.0. Spearman
   correlation against the baseline.
3. Switch tests: re-process each report in-memory under each toggle
   (ToC exclusion off, repeated-line removal off, matching mode = all)
   and compare rankings. Does NOT touch stored Report / CategoryScore /
   MatchEvidence rows.

Scope: every cleanly-scored institution under the latest taxonomy MINUS
the slugs in EXCLUDED_SLUGS (rabigh-refining-petrochemical-co today —
known extraction artifact, so testing its 'sensitivity' would just
measure the bug). The analyzed count is reported in the generated
summary header, not hard-coded here — the scored set grows over the
project's life.
"""
from __future__ import annotations

import csv
import sys
import time
from collections import defaultdict
from datetime import UTC, datetime
from pathlib import Path

BACKEND = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND))
sys.stdout.reconfigure(encoding="utf-8")

import numpy as np  # noqa: E402
from scipy.stats import kendalltau, spearmanr  # noqa: E402

from app.crawler import register_all_mappers  # noqa: E402

register_all_mappers()

from app.database import engine  # noqa: E402
from app.services.matcher import TaxonomyMatcher  # noqa: E402
from app.services.pdf_extraction import count_words, extract_pdf_pages  # noqa: E402
from app.services.storage import read_pdf_bytes  # noqa: E402
from app.services.text_processing import segment_sentences  # noqa: E402
from app.services.text_quality import apply_text_quality  # noqa: E402
from app.services.verity_config import VerityConfig  # noqa: E402
from sqlalchemy import text as sql_text  # noqa: E402

EXCLUDED_SLUGS = {"rabigh-refining-petrochemical-co"}
EXPORTS = BACKEND.parent / "exports"
DOCS = BACKEND.parent / "docs"
JITTER_SEED = 20261002
N_DRAWS = 1000
JITTER_LOW = 0.8
JITTER_HIGH = 1.2


# --------------------------------------------------------------------------- #
# Baseline data load
# --------------------------------------------------------------------------- #


def _load_baseline():
    """Return a dict bundle of baseline data: reports, their match-count
    vectors keyed by term, their stored composite, institution sector, etc.
    """
    with engine.connect() as c:
        latest = c.execute(sql_text(
            "SELECT hash FROM taxonomy_versions ORDER BY id DESC LIMIT 1"
        )).scalar()
        # Term list
        terms = list(c.execute(sql_text("""
            SELECT t.id, t.phrase, t.weight, t.lemma_based, t.category_id,
                   c.pillar, c.weight
            FROM terms t JOIN categories c ON c.id = t.category_id
            ORDER BY t.id
        """)))
        term_meta = {
            t[0]: {
                "phrase": t[1], "weight": float(t[2]), "lemma_based": bool(t[3]),
                "category_id": t[4], "pillar": t[5], "cat_weight": float(t[6]),
            } for t in terms
        }
        # Reports under latest taxonomy for the included institutions.
        # Previous version used `GROUP BY r.id` to dedupe the fan-out
        # from the category_scores join. SQLite accepted that; Postgres
        # requires every non-aggregated SELECT column in GROUP BY.
        # Rewrite with EXISTS so there's no fan-out to dedupe in the
        # first place — same result on both engines, no GROUP BY needed.
        rpts = list(c.execute(sql_text(f"""
            SELECT r.id, r.institution_id, i.slug, i.name, i.is_financial,
                   r.fiscal_year, r.latin_word_count, r.file_path,
                   r.composite_score
            FROM reports r
            JOIN institutions i ON i.id = r.institution_id
            WHERE i.active
              AND i.slug NOT IN ({",".join("'" + s + "'" for s in EXCLUDED_SLUGS)})
              AND EXISTS (
                SELECT 1 FROM category_scores cs
                JOIN taxonomy_versions tv ON tv.id = cs.taxonomy_version_id
                WHERE cs.report_id = r.id AND tv.hash = '{latest}'
              )
            ORDER BY i.slug, r.fiscal_year
        """)))
        reports = {}
        for rid, iid, slug, name, is_fin, fy, lw, path, comp in rpts:
            reports[rid] = {
                "institution_id": iid, "slug": slug, "name": name,
                "is_financial": bool(is_fin), "fiscal_year": fy,
                "latin_words": int(lw or 0),
                "file_path": path, "composite_baseline": float(comp or 0.0),
            }
        # Match counts per (report, term)
        mc_rows = list(c.execute(sql_text(f"""
            SELECT me.report_id, me.term_id, COUNT(*)
            FROM match_evidence me
            JOIN category_scores cs
              ON cs.report_id = me.report_id
             AND cs.taxonomy_version_id = me.taxonomy_version_id
            JOIN taxonomy_versions tv ON tv.id = me.taxonomy_version_id
            WHERE tv.hash = '{latest}'
              AND me.report_id IN ({",".join(str(x) for x in reports)})
            GROUP BY me.report_id, me.term_id
        """)))
    match_counts: dict[int, dict[int, int]] = defaultdict(dict)
    for rid, tid, n in mc_rows:
        match_counts[rid][tid] = n
    return term_meta, reports, match_counts, latest


# --------------------------------------------------------------------------- #
# Scoring helpers
# --------------------------------------------------------------------------- #


def _composite_from_match_counts(mc: dict[int, int], latin_words: int,
                                 term_weights: dict[int, float],
                                 cat_weights: dict[int, float],
                                 term_cat: dict[int, int]) -> float:
    """Replay the scoring formula from stored match counts.

    composite = sum over categories( density * cat_weight )
    density_c = sum over terms in c( tw * n ) / latin_words * 1000
    """
    if not latin_words:
        return 0.0
    cat_raw: dict[int, float] = defaultdict(float)
    for tid, n in mc.items():
        tw = term_weights.get(tid, 1.0)
        cat_raw[term_cat[tid]] += tw * n
    total = 0.0
    for cid, raw in cat_raw.items():
        density = raw / latin_words * 1000.0
        total += density * cat_weights.get(cid, 1.0)
    return round(total, 4)


def _ranks_within_sector(mean_comp_by_inst: dict[int, float],
                         fin_set: set[int]) -> tuple[dict[int, int], dict[int, int]]:
    """Return (financial_ranks, non_financial_ranks) — rank 1 = highest composite."""
    fin = sorted([(iid, c) for iid, c in mean_comp_by_inst.items() if iid in fin_set],
                 key=lambda kv: -kv[1])
    non_fin = sorted([(iid, c) for iid, c in mean_comp_by_inst.items() if iid not in fin_set],
                     key=lambda kv: -kv[1])
    fin_r = {iid: i + 1 for i, (iid, _) in enumerate(fin)}
    non_fin_r = {iid: i + 1 for i, (iid, _) in enumerate(non_fin)}
    return fin_r, non_fin_r


def _mean_composite_per_inst(report_composites: dict[int, float],
                             reports: dict) -> dict[int, float]:
    agg: dict[int, list[float]] = defaultdict(list)
    for rid, c in report_composites.items():
        agg[reports[rid]["institution_id"]].append(c)
    return {iid: float(np.mean(cs)) for iid, cs in agg.items()}


# --------------------------------------------------------------------------- #
# Weight jitter + equal weights (fast — pure replay from stored match counts)
# --------------------------------------------------------------------------- #


def run_weight_jitter(term_meta, reports, match_counts, baseline_fin_rank,
                      baseline_non_fin_rank, fin_set):
    rng = np.random.default_rng(JITTER_SEED)
    term_ids = sorted(term_meta.keys())
    base_weights = np.array([term_meta[t]["weight"] for t in term_ids])
    term_cat = {t: term_meta[t]["category_id"] for t in term_ids}
    cat_weights = {t["category_id"]: t["cat_weight"] for t in term_meta.values()}

    # Collect ranks across draws.
    fin_ranks_by_inst: dict[int, list[int]] = defaultdict(list)
    non_fin_ranks_by_inst: dict[int, list[int]] = defaultdict(list)
    kendall_fin: list[float] = []
    kendall_non_fin: list[float] = []

    fin_insts = sorted(baseline_fin_rank.keys())
    non_fin_insts = sorted(baseline_non_fin_rank.keys())
    baseline_fin_arr = np.array([baseline_fin_rank[i] for i in fin_insts])
    baseline_nf_arr = np.array([baseline_non_fin_rank[i] for i in non_fin_insts])

    for _ in range(N_DRAWS):
        jitter = rng.uniform(JITTER_LOW, JITTER_HIGH, size=len(term_ids))
        jittered = {t: float(base_weights[k] * jitter[k]) for k, t in enumerate(term_ids)}
        report_comp = {
            rid: _composite_from_match_counts(
                match_counts.get(rid, {}), reports[rid]["latin_words"],
                jittered, cat_weights, term_cat,
            )
            for rid in reports
        }
        mean_c = _mean_composite_per_inst(report_comp, reports)
        fin_r, non_fin_r = _ranks_within_sector(mean_c, fin_set)
        for iid, r in fin_r.items():
            fin_ranks_by_inst[iid].append(r)
        for iid, r in non_fin_r.items():
            non_fin_ranks_by_inst[iid].append(r)
        this_fin_arr = np.array([fin_r[i] for i in fin_insts])
        this_nf_arr = np.array([non_fin_r[i] for i in non_fin_insts])
        kendall_fin.append(kendalltau(baseline_fin_arr, this_fin_arr).statistic)
        kendall_non_fin.append(kendalltau(baseline_nf_arr, this_nf_arr).statistic)

    def _summary(ranks_by_inst):
        out = {}
        for iid, rs in ranks_by_inst.items():
            arr = np.array(rs)
            out[iid] = {
                "median_rank": int(np.median(arr)),
                "p5_rank": int(np.percentile(arr, 5)),
                "p95_rank": int(np.percentile(arr, 95)),
                "interval_width": int(np.percentile(arr, 95) - np.percentile(arr, 5)),
            }
        return out

    return {
        "fin": _summary(fin_ranks_by_inst),
        "non_fin": _summary(non_fin_ranks_by_inst),
        "kendall_fin": kendall_fin,
        "kendall_non_fin": kendall_non_fin,
    }


def run_equal_weights(term_meta, reports, match_counts, baseline_fin_rank,
                      baseline_non_fin_rank, fin_set):
    eq_term_weights = {t: 1.0 for t in term_meta}
    eq_cat_weights = {t["category_id"]: 1.0 for t in term_meta.values()}
    term_cat = {t: term_meta[t]["category_id"] for t in term_meta}
    report_comp = {
        rid: _composite_from_match_counts(
            match_counts.get(rid, {}), reports[rid]["latin_words"],
            eq_term_weights, eq_cat_weights, term_cat,
        )
        for rid in reports
    }
    mean_c = _mean_composite_per_inst(report_comp, reports)
    fin_r, non_fin_r = _ranks_within_sector(mean_c, fin_set)

    fin_insts = sorted(baseline_fin_rank.keys())
    non_fin_insts = sorted(baseline_non_fin_rank.keys())
    sp_fin = spearmanr(
        [baseline_fin_rank[i] for i in fin_insts],
        [fin_r[i] for i in fin_insts],
    ).statistic
    sp_nf = spearmanr(
        [baseline_non_fin_rank[i] for i in non_fin_insts],
        [non_fin_r[i] for i in non_fin_insts],
    ).statistic
    return {"fin_rank": fin_r, "non_fin_rank": non_fin_r,
            "spearman_fin": sp_fin, "spearman_non_fin": sp_nf}


# --------------------------------------------------------------------------- #
# Switch tests (full in-memory re-score per toggle)
# --------------------------------------------------------------------------- #


def _switch_cfg(base: VerityConfig, *, toc=None, repeat=None, mode=None) -> VerityConfig:
    """Clone base cfg with overrides."""
    return VerityConfig(
        years=base.years, report_types_scored=base.report_types_scored,
        matching_mode=(mode if mode is not None else base.matching_mode),
        exclude_toc_pages=(toc if toc is not None else base.exclude_toc_pages),
        exclude_repeated_lines=(repeat if repeat is not None else base.exclude_repeated_lines),
        exclude_financial_statement_pages=base.exclude_financial_statement_pages,
        header_footer_repeat_ratio=base.header_footer_repeat_ratio,
        arabic_page_token_ratio=base.arabic_page_token_ratio,
        ocr_max_page_ratio=base.ocr_max_page_ratio,
        log_all_mode_diff=False,
        financial_statement_boundary_markers=base.financial_statement_boundary_markers,
        worker_count=1, iqr_multiplier=base.iqr_multiplier,
        iqr_min_cohort=base.iqr_min_cohort,
        low_latin_word_count_threshold=base.low_latin_word_count_threshold,
        high_ocr_ratio_threshold=base.high_ocr_ratio_threshold,
        high_arabic_ratio_threshold=base.high_arabic_ratio_threshold,
        evidence_sample_per_pillar=50, evidence_sample_seed=42,
        wave_order=base.wave_order,
    )


class _TermLite:
    __slots__ = ("id", "phrase", "weight", "lemma_based", "category_id")

    def __init__(self, tid, phrase, weight, lemma_based, cat_id):
        self.id, self.phrase, self.weight = tid, phrase, weight
        self.lemma_based, self.category_id = lemma_based, cat_id


def _match_count_under(matcher, sentences, mode):
    """Run matcher under forced mode, return term_id -> count."""
    from app.services import matcher as matcher_module
    original = matcher_module.load_verity_config
    try:
        matcher_module.load_verity_config = lambda path=None: VerityConfig(matching_mode=mode)
        matches = matcher.match_sentences(sentences)
    finally:
        matcher_module.load_verity_config = original
    out: dict[int, int] = defaultdict(int)
    for m in matches:
        out[m.term_id] += 1
    return dict(out)


def run_switch_tests(term_meta, reports, baseline_fin_rank, baseline_non_fin_rank,
                     fin_set, base_cfg: VerityConfig):
    """Three variants:
       1. toc_off    — exclude_toc_pages=False
       2. repeat_off — exclude_repeated_lines=False
       3. all_mode   — matching_mode='all'
    Each variant: re-extract, re-clean, re-match, re-score. Baseline is
    the stored composites (no re-run needed).
    """
    terms_light = [
        _TermLite(tid, m["phrase"], m["weight"], m["lemma_based"], m["category_id"])
        for tid, m in term_meta.items()
    ]
    matcher = TaxonomyMatcher(terms_light)
    term_cat = {t: term_meta[t]["category_id"] for t in term_meta}
    cat_weights = {m["category_id"]: m["cat_weight"] for m in term_meta.values()}
    term_weights = {t: term_meta[t]["weight"] for t in term_meta}

    variants = {
        "toc_off": _switch_cfg(base_cfg, toc=False),
        "repeat_off": _switch_cfg(base_cfg, repeat=False),
        "all_mode": _switch_cfg(base_cfg, mode="all"),
    }
    composites_by_variant: dict[str, dict[int, float]] = {k: {} for k in variants}

    # Cache: extract per PDF once, then run 3 variants against the same pages.
    report_items = list(reports.items())
    print(f"re-scoring {len(report_items)} reports under 3 switches ...")
    t0 = time.monotonic()
    for idx, (rid, meta) in enumerate(report_items, start=1):
        try:
            # Session 9: PDFs live in R2 keyed by the stored file_path.
            # read_pdf_bytes handles both R2 and the local-disk dev
            # fallback transparently; extract_pdf_pages accepts bytes.
            pages = extract_pdf_pages(read_pdf_bytes(meta["file_path"]))
        except Exception as exc:
            print(f"  [{idx}/{len(report_items)}] {meta['slug']} FY{meta['fiscal_year']}:"
                  f" extraction failed: {exc}")
            for vname in variants:
                composites_by_variant[vname][rid] = meta["composite_baseline"]
            continue
        counts = count_words(pages)
        latin_words = counts.latin
        for vname, vcfg in variants.items():
            cleaned = apply_text_quality(pages, vcfg)
            sentences = segment_sentences(cleaned.pages)
            match_mode = "all" if vname == "all_mode" else "longest"
            mc = _match_count_under(matcher, sentences, match_mode)
            comp = _composite_from_match_counts(mc, latin_words, term_weights,
                                                cat_weights, term_cat)
            composites_by_variant[vname][rid] = comp
        if idx % 10 == 0 or idx == len(report_items):
            dt = time.monotonic() - t0
            print(f"  [{idx}/{len(report_items)}] {meta['slug']} FY{meta['fiscal_year']}  "
                  f"(elapsed {dt:.0f}s)", flush=True)

    # Per variant: ranks + Spearman vs baseline
    fin_insts = sorted(baseline_fin_rank.keys())
    non_fin_insts = sorted(baseline_non_fin_rank.keys())
    out = {}
    for vname, rc in composites_by_variant.items():
        mean_c = _mean_composite_per_inst(rc, reports)
        fin_r, non_fin_r = _ranks_within_sector(mean_c, fin_set)
        sp_f = spearmanr([baseline_fin_rank[i] for i in fin_insts],
                         [fin_r[i] for i in fin_insts]).statistic
        sp_nf = spearmanr([baseline_non_fin_rank[i] for i in non_fin_insts],
                          [non_fin_r[i] for i in non_fin_insts]).statistic
        out[vname] = {
            "fin_rank": fin_r, "non_fin_rank": non_fin_r,
            "spearman_fin": sp_f, "spearman_non_fin": sp_nf,
        }
    return out


# --------------------------------------------------------------------------- #
# Reporting
# --------------------------------------------------------------------------- #


def main():
    term_meta, reports, match_counts, tv_hash = _load_baseline()
    print(f"baseline: taxonomy {tv_hash[:12]}, "
          f"{len(reports)} reports, {len(set(r['institution_id'] for r in reports.values()))} institutions")

    # Baseline ranks from stored composites.
    baseline_mean = _mean_composite_per_inst(
        {rid: r["composite_baseline"] for rid, r in reports.items()}, reports)
    fin_set = {r["institution_id"] for r in reports.values() if r["is_financial"]}
    baseline_fin_rank, baseline_non_fin_rank = _ranks_within_sector(baseline_mean, fin_set)
    inst_meta = {
        r["institution_id"]: (r["slug"], r["name"], r["is_financial"])
        for r in reports.values()
    }
    years_per_inst: dict[int, set[int]] = defaultdict(set)
    for r in reports.values():
        years_per_inst[r["institution_id"]].add(r["fiscal_year"])

    # 1. Weight jitter
    print()
    print("# 1. Weight jitter (U(0.8, 1.2), 1000 draws, seed=20261002)")
    print(f"   terms perturbed: {len(term_meta)}")
    t0 = time.monotonic()
    jitter = run_weight_jitter(term_meta, reports, match_counts,
                               baseline_fin_rank, baseline_non_fin_rank, fin_set)
    print(f"   wall clock: {time.monotonic() - t0:.1f}s")
    print(f"   Kendall tau (fin): median={np.median(jitter['kendall_fin']):.3f}  "
          f"p5={np.percentile(jitter['kendall_fin'], 5):.3f}  "
          f"p95={np.percentile(jitter['kendall_fin'], 95):.3f}")
    print(f"   Kendall tau (non-fin): median={np.median(jitter['kendall_non_fin']):.3f}  "
          f"p5={np.percentile(jitter['kendall_non_fin'], 5):.3f}  "
          f"p95={np.percentile(jitter['kendall_non_fin'], 95):.3f}")

    # 2. Equal weights
    print()
    print("# 2. Equal weights (all term + category weights = 1.0)")
    equal = run_equal_weights(term_meta, reports, match_counts,
                              baseline_fin_rank, baseline_non_fin_rank, fin_set)
    print(f"   Spearman (fin): {equal['spearman_fin']:.3f}")
    print(f"   Spearman (non-fin): {equal['spearman_non_fin']:.3f}")

    # 3. Switch tests
    print()
    print("# 3. Switch tests (in-memory re-score per toggle)")
    base_cfg_for_switches = VerityConfig()  # pulls documented defaults
    switch = run_switch_tests(term_meta, reports, baseline_fin_rank, baseline_non_fin_rank,
                              fin_set, base_cfg_for_switches)
    for vname, data in switch.items():
        print(f"   {vname}: spearman fin={data['spearman_fin']:.3f}  "
              f"non-fin={data['spearman_non_fin']:.3f}")

    # ---- CSV + MD outputs ----------------------------------------------
    EXPORTS.mkdir(parents=True, exist_ok=True)
    DOCS.mkdir(parents=True, exist_ok=True)
    # Count-strings must track the actual data: the live scored set grows
    # over the project's life, and hard-coded "42 of 43" went stale as
    # soon as Session 9 reprocessed. Compute from inst_meta (what we
    # analysed) + the DB count of scored institutions under the latest
    # taxonomy (what we started from).
    n_analysed = len(inst_meta)
    with engine.connect() as _c:
        n_scored_total = _c.execute(sql_text("""
            SELECT COUNT(DISTINCT i.id)
            FROM institutions i
            JOIN reports r ON r.institution_id = i.id
            JOIN category_scores cs ON cs.report_id = r.id
            JOIN taxonomy_versions tv ON tv.id = cs.taxonomy_version_id
            WHERE tv.hash = :h AND i.active
        """), {"h": tv_hash}).scalar() or n_analysed
    excluded_slugs_str = ", ".join(sorted(EXCLUDED_SLUGS))
    header = (
        f"# Verity sensitivity analysis  |  taxonomy={tv_hash}  |  "
        f"generated={datetime.now(UTC).isoformat(timespec='seconds')}  |  "
        f"n_institutions={n_analysed} ({n_scored_total} scored"
        f" - {excluded_slugs_str} artifact)  |  "
        f"within-sector only"
    )
    csv_path = EXPORTS / "sensitivity_summary.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as fh:
        fh.write(header + "\n")
        w = csv.writer(fh)
        w.writerow([
            "slug", "sector", "years_covered", "baseline_rank",
            "jitter_median_rank", "jitter_p5_rank", "jitter_p95_rank",
            "jitter_interval_width",
            "equal_weights_rank",
            "toc_off_rank", "repeat_off_rank", "all_mode_rank",
            "flag_single_year_high_volatility",
        ])
        for iid in sorted(inst_meta, key=lambda i: inst_meta[i][0]):
            slug, _name, is_fin = inst_meta[iid]
            base_r = baseline_fin_rank.get(iid) or baseline_non_fin_rank.get(iid)
            sector = "financial" if is_fin else "non-financial"
            j = (jitter["fin"] if is_fin else jitter["non_fin"]).get(iid, {})
            eq_r = (equal["fin_rank"] if is_fin else equal["non_fin_rank"]).get(iid)
            sw_vals = {}
            for vname in ("toc_off", "repeat_off", "all_mode"):
                sw_vals[vname] = (
                    switch[vname]["fin_rank"] if is_fin else switch[vname]["non_fin_rank"]
                ).get(iid)
            cohort = len(fin_set) if is_fin else (len(inst_meta) - len(fin_set))
            interval = j.get("interval_width", 0)
            single_year = len(years_per_inst[iid]) == 1
            volatile = interval >= max(3, cohort // 3)
            flag = "YES" if (single_year and volatile) else ""
            w.writerow([
                slug, sector, len(years_per_inst[iid]), base_r,
                j.get("median_rank"), j.get("p5_rank"), j.get("p95_rank"), interval,
                eq_r, sw_vals["toc_off"], sw_vals["repeat_off"], sw_vals["all_mode"],
                flag,
            ])
    print(f"\nwrote {csv_path}")

    # ---- Markdown narrative ----------------------------------------------
    def _rank_delta(r2: int | None, r1: int) -> str:
        if r2 is None:
            return "—"
        d = r2 - r1
        return f"{r2} ({'+' if d > 0 else ''}{d})" if d else f"{r2} (±0)"

    lines: list[str] = []
    lines.append("# Sensitivity analysis")
    lines.append("")
    lines.append(f"_{header[2:]}_")
    lines.append("")
    lines.append(
        f"Three tests, all within-sector (financial vs non-financial), {n_analysed} institutions "
        f"({n_scored_total} scored minus `{excluded_slugs_str}`, artifact-flagged)."
    )
    lines.append("")
    lines.append("## 1. Weight jitter — U(0.8, 1.2), 1000 draws")
    lines.append(f"- Seed: `{JITTER_SEED}` (reproducible).")
    lines.append(f"- Kendall tau vs baseline, financial sector: "
                 f"median = **{np.median(jitter['kendall_fin']):.3f}**, "
                 f"5-95% = [{np.percentile(jitter['kendall_fin'], 5):.3f}, "
                 f"{np.percentile(jitter['kendall_fin'], 95):.3f}].")
    lines.append(f"- Kendall tau vs baseline, non-financial sector: "
                 f"median = **{np.median(jitter['kendall_non_fin']):.3f}**, "
                 f"5-95% = [{np.percentile(jitter['kendall_non_fin'], 5):.3f}, "
                 f"{np.percentile(jitter['kendall_non_fin'], 95):.3f}].")
    lines.append("")

    # Stability tables
    for sector_name, insts, base_rank_map, summary in [
        ("Financial", sorted(baseline_fin_rank, key=baseline_fin_rank.get),
         baseline_fin_rank, jitter["fin"]),
        ("Non-financial", sorted(baseline_non_fin_rank, key=baseline_non_fin_rank.get),
         baseline_non_fin_rank, jitter["non_fin"]),
    ]:
        lines.append(f"### {sector_name} — per-institution rank stability")
        lines.append("")
        lines.append("| slug | years | baseline rank | median | 5-95% rank interval | width |")
        lines.append("|---|---:|---:|---:|---|---:|")
        for iid in insts:
            slug, _, _ = inst_meta[iid]
            s = summary[iid]
            lines.append(
                f"| `{slug}` | {len(years_per_inst[iid])} | {base_rank_map[iid]} "
                f"| {s['median_rank']} | [{s['p5_rank']}, {s['p95_rank']}] "
                f"| {s['interval_width']} |"
            )
        lines.append("")

    lines.append("## 2. Equal weights (all weights = 1.0)")
    lines.append(f"- Spearman vs baseline, financial sector: "
                 f"**{equal['spearman_fin']:.3f}**")
    lines.append(f"- Spearman vs baseline, non-financial sector: "
                 f"**{equal['spearman_non_fin']:.3f}**")
    lines.append("")
    lines.append("Rank changes under equal weights:")
    lines.append("")
    for sector_name, insts, base_rank_map, new_rank_map in [
        ("Financial", sorted(baseline_fin_rank, key=baseline_fin_rank.get),
         baseline_fin_rank, equal["fin_rank"]),
        ("Non-financial", sorted(baseline_non_fin_rank, key=baseline_non_fin_rank.get),
         baseline_non_fin_rank, equal["non_fin_rank"]),
    ]:
        lines.append(f"**{sector_name}** — moves ≥ 3 positions:")
        for iid in insts:
            slug, _, _ = inst_meta[iid]
            br = base_rank_map[iid]
            nr = new_rank_map[iid]
            if abs(nr - br) >= 3:
                lines.append(f"- `{slug}`: baseline rank {br} → equal-weights rank "
                             f"{nr} ({'+' if nr - br > 0 else ''}{nr - br})")
        lines.append("")

    lines.append("## 3. Switch tests")
    for vname, data in switch.items():
        lines.append(f"### `{vname}`")
        lines.append(f"- Spearman fin = **{data['spearman_fin']:.3f}**, "
                     f"non-fin = **{data['spearman_non_fin']:.3f}**")
        for sector_name, insts, base_rank_map, new_rank_map in [
            ("Financial", sorted(baseline_fin_rank, key=baseline_fin_rank.get),
             baseline_fin_rank, data["fin_rank"]),
            ("Non-financial", sorted(baseline_non_fin_rank, key=baseline_non_fin_rank.get),
             baseline_non_fin_rank, data["non_fin_rank"]),
        ]:
            big_moves = []
            for iid in insts:
                slug, _, _ = inst_meta[iid]
                br = base_rank_map[iid]
                nr = new_rank_map[iid]
                if abs(nr - br) >= 3:
                    big_moves.append(f"`{slug}` {br}→{nr} ({'+' if nr - br > 0 else ''}{nr - br})")
            if big_moves:
                lines.append(f"- {sector_name} moves ≥ 3: " + "; ".join(big_moves))
            else:
                lines.append(f"- {sector_name}: no moves ≥ 3 positions.")
        lines.append("")

    # Flags: single-year + high volatility
    lines.append("## Single-year institutions with high rank volatility (jitter interval ≥ cohort/3)")
    lines.append("")
    flagged = []
    for iid in sorted(inst_meta, key=lambda i: inst_meta[i][0]):
        slug, _, is_fin = inst_meta[iid]
        if len(years_per_inst[iid]) != 1:
            continue
        summary = jitter["fin"] if is_fin else jitter["non_fin"]
        cohort = len(fin_set) if is_fin else (len(inst_meta) - len(fin_set))
        if iid not in summary:
            continue
        s = summary[iid]
        if s["interval_width"] >= max(3, cohort // 3):
            yr = next(iter(years_per_inst[iid]))
            flagged.append((slug, "fin" if is_fin else "non-fin",
                            yr, s["interval_width"]))
    if not flagged:
        lines.append("_(none — no single-year institutions show high jitter volatility)_")
    else:
        lines.append("| slug | sector | year | jitter interval width |")
        lines.append("|---|---|---:|---:|")
        for slug, sec, yr, w_ in flagged:
            lines.append(f"| `{slug}` | {sec} | {yr} | {w_} |")
    lines.append("")

    (DOCS / "SENSITIVITY_SUMMARY.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"wrote {DOCS / 'SENSITIVITY_SUMMARY.md'}")


if __name__ == "__main__":
    main()
