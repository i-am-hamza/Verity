"""Session 6 leaderboard builder.

Pulls scored reports under the latest taxonomy, computes per-(institution, FY)
pillar densities and composites, means-per-institution, and ranks twice:
overall across all 43 scored institutions and within-sector (financial vs
non-financial, from is_financial). Writes two CSVs and prints a readable
top/bottom-10 table plus the 17 not-yet-covered institutions with reasons.

Not applied tonight: sensitivity analysis, external-ratings benchmarking —
those are a later session's job.
"""
from __future__ import annotations

import csv
import sys
from collections import defaultdict
from datetime import UTC, datetime
from pathlib import Path

BACKEND = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND))
sys.stdout.reconfigure(encoding="utf-8")

from app.crawler import register_all_mappers  # noqa: E402

register_all_mappers()

from app.database import engine  # noqa: E402
from sqlalchemy import text as sql_text  # noqa: E402

PILLARS = ("Environmental", "Social", "Governance")
EXPORTS = BACKEND.parent / "exports"

# Known extraction artifacts: rows that LOOK like real measurements but
# aren't. Each entry = {institution_slug: (fiscal_year | None, flag_tag,
# short-reason)}. Appears as `data_quality_flag` column in both CSVs and
# an asterisk in the printed table. fiscal_year=None flags every scored
# year for that institution; a specific year flags only that one.
# Rationale and diagnostic detail live in DECISIONS.md.
KNOWN_ARTIFACTS: dict[str, tuple[int | None, str, str]] = {
    "rabigh-refining-petrochemical-co": (
        2020,
        "sentence_segmentation_artifact",
        "sentence segmentation failed on this PDF's layout; "
        "score does not reflect actual disclosure content; "
        "see DECISIONS.md 2026-10-02",
    ),
}


def _flag_for(slug: str, fy: int | None = None) -> str:
    row = KNOWN_ARTIFACTS.get(slug)
    if row is None:
        return ""
    flag_year, tag, _reason = row
    if flag_year is None or fy is None or fy == flag_year:
        return tag
    return ""


def _latest_taxonomy_hash() -> str:
    with engine.connect() as c:
        return c.execute(sql_text(
            "SELECT hash FROM taxonomy_versions ORDER BY id DESC LIMIT 1"
        )).scalar()


def _load_scored_rows(tv_hash: str):
    """Return [(inst_id, slug, name, is_financial, fy, pillar, density, composite), ...]
    joined to the 60-institution universe (active only).
    """
    sql = sql_text("""
        SELECT i.id, i.slug, i.name, i.is_financial,
               r.fiscal_year, c.pillar, cs.density_per_1000_words,
               r.composite_score
        FROM reports r
        JOIN category_scores cs ON cs.report_id = r.id
        JOIN categories c ON c.id = cs.category_id
        JOIN taxonomy_versions tv ON tv.id = cs.taxonomy_version_id
        JOIN institutions i ON i.id = r.institution_id
        WHERE tv.hash = :h AND i.active = 1
        ORDER BY i.slug, r.fiscal_year, c.pillar
    """)
    with engine.connect() as c:
        return list(c.execute(sql, {"h": tv_hash}))


def _not_yet_covered():
    """Return list[(inst_id, slug, name, is_financial, reason)] for active
    institutions with zero scored reports under the latest taxonomy.

    Reason buckets are reconstructed from the DB rather than hardcoded, so
    this stays correct even after further ingests: 'no file in storage',
    'wayback-only, all type!=annual/integrated', 'has annual auto_ok but
    page<30 (summary report)'.
    """
    tv_hash = _latest_taxonomy_hash()
    rows: list[tuple[int, str, str, bool, str]] = []
    with engine.connect() as c:
        scored_ids = {r[0] for r in c.execute(sql_text("""
            SELECT DISTINCT r.institution_id FROM reports r
            JOIN category_scores cs ON cs.report_id = r.id
            JOIN taxonomy_versions tv ON tv.id = cs.taxonomy_version_id
            WHERE tv.hash = :h
        """), {"h": tv_hash})}
        active = list(c.execute(sql_text("""
            SELECT id, slug, name, is_financial FROM institutions
            WHERE active = 1 ORDER BY rank
        """)))
        for inst_id, slug, name, is_fin in active:
            if inst_id in scored_ids:
                continue
            sd_rows = list(c.execute(sql_text("""
                SELECT source, report_type, review_status, page_count, review_note
                FROM source_documents
                WHERE institution_id = :id AND (superseded_by_id IS NULL)
            """), {"id": inst_id}))
            if not sd_rows:
                reason = "A: no file in storage at all"
            else:
                scored_types = {"annual", "integrated"}
                # D: file IS annual/integrated and page_count < 30 — a
                # short "summary" report that fails MIN_ANNUAL_REPORT_PAGES.
                page_threshold_hits = [
                    s for s in sd_rows
                    if s[1] in scored_types and (s[3] or 0) < 30
                       and "pages (<" in (s[4] or "")
                ]
                if page_threshold_hits:
                    s = page_threshold_hits[0]
                    reason = (f"D: {s[0]}-sourced {s[1]} report, "
                              f"only {s[3]} pages (< 30 threshold); genuine summary")
                else:
                    sources = sorted({s[0] for s in sd_rows})
                    reason = (f"B: {len(sd_rows)} file(s) [{','.join(sources)}], "
                              f"none passed as annual/integrated+auto_ok "
                              f"(all needs_review or wrong type)")
            rows.append((inst_id, slug, name, bool(is_fin), reason))
    return rows


def build_leaderboard():
    tv_hash = _latest_taxonomy_hash()
    rows = _load_scored_rows(tv_hash)

    # Per (institution, FY, pillar) density. composite_score comes from the
    # report row, same across pillars.
    per_inst_fy_pillar: dict[tuple[int, int, str], float] = {}
    composites: dict[tuple[int, int], float] = {}
    inst_meta: dict[int, tuple[str, str, bool]] = {}
    years_by_inst: dict[int, set[int]] = defaultdict(set)
    for inst_id, slug, name, is_fin, fy, pillar, density, composite in rows:
        per_inst_fy_pillar[(inst_id, fy, pillar)] = density
        composites[(inst_id, fy)] = composite
        inst_meta[inst_id] = (slug, name, bool(is_fin))
        years_by_inst[inst_id].add(fy)

    # Mean composite per institution. Sort for both ranks.
    mean_composite: dict[int, float] = {
        iid: round(sum(c for (i2, _), c in composites.items() if i2 == iid)
                   / len(years_by_inst[iid]), 3)
        for iid in inst_meta
    }

    sorted_all = sorted(mean_composite.items(), key=lambda kv: -kv[1])
    overall_rank = {iid: i + 1 for i, (iid, _) in enumerate(sorted_all)}

    # Within-sector rank.
    fin_sorted = sorted([x for x in mean_composite.items() if inst_meta[x[0]][2]],
                        key=lambda kv: -kv[1])
    non_fin_sorted = sorted([x for x in mean_composite.items() if not inst_meta[x[0]][2]],
                            key=lambda kv: -kv[1])
    within_rank: dict[int, int] = {}
    for i, (iid, _) in enumerate(fin_sorted):
        within_rank[iid] = i + 1
    for i, (iid, _) in enumerate(non_fin_sorted):
        within_rank[iid] = i + 1

    gen_date = datetime.now(UTC).isoformat(timespec="seconds")
    coverage_line = (
        f"# Verity ESG leaderboard  |  taxonomy={tv_hash}  |  "
        f"generated={gen_date}  |  "
        f"coverage=43/60 active institutions  |  "
        f"NOT YET validated against external ratings (MSCI/Sustainalytics/LSEG) "
        f"— scores are RECALL AT THIS TAXONOMY VERSION ONLY, not benchmarked."
    )

    # ---- scores_long.csv ------------------------------------------------
    EXPORTS.mkdir(parents=True, exist_ok=True)
    scores_long = EXPORTS / "scores_long.csv"
    with scores_long.open("w", newline="", encoding="utf-8") as fh:
        fh.write(coverage_line + "\n")
        w = csv.writer(fh)
        w.writerow([
            "institution_slug", "institution_name", "sector", "fiscal_year",
            "pillar", "density_per_1000_words", "composite_score",
            "mean_composite", "overall_rank", "within_sector_rank",
            "data_quality_flag",
        ])
        for (iid, fy, pillar), density in sorted(
            per_inst_fy_pillar.items(),
            key=lambda kv: (inst_meta[kv[0][0]][0], kv[0][1], kv[0][2]),
        ):
            slug, name, is_fin = inst_meta[iid]
            sector = "financial" if is_fin else "non-financial"
            w.writerow([
                slug, name, sector, fy, pillar,
                round(density, 4),
                round(composites[(iid, fy)], 3),
                mean_composite[iid],
                overall_rank[iid],
                within_rank[iid],
                _flag_for(slug, fy),
            ])

    # ---- leaderboard_summary.csv ---------------------------------------
    summary_path = EXPORTS / "leaderboard_summary.csv"
    with summary_path.open("w", newline="", encoding="utf-8") as fh:
        fh.write(coverage_line + "\n")
        w = csv.writer(fh)
        w.writerow([
            "institution_slug", "institution_name", "sector",
            "years_covered_count", "years_covered",
            "mean_composite", "overall_rank", "within_sector_rank",
            "data_quality_flag",
        ])
        for iid, mc in sorted_all:
            slug, name, is_fin = inst_meta[iid]
            sector = "financial" if is_fin else "non-financial"
            fys = sorted(years_by_inst[iid])
            years_str = f"{len(fys)} ({', '.join(str(y) for y in fys)})"
            # Institution-level flag: set if ANY of its scored FYs is flagged.
            inst_flag = ""
            for y in fys:
                f = _flag_for(slug, y)
                if f:
                    inst_flag = f
                    break
            w.writerow([slug, name, sector, len(fys), years_str,
                        mc, overall_rank[iid], within_rank[iid], inst_flag])

    # ---- readable print -------------------------------------------------
    print(coverage_line)
    print(f"\nScored active institutions: {len(inst_meta)} / 60")
    print(f"Scored reports under {tv_hash[:12]}: "
          f"{len({(iid, fy) for iid, fy in composites})}")
    print(f"\nFinancial sector: {len(fin_sorted)} institutions")
    print(f"Non-financial sector: {len(non_fin_sorted)} institutions")

    footnotes_seen: set[str] = set()

    def _table(title: str, items: list[tuple[int, float]], top_n: int = 10,
               ascending_rank: bool = False):
        print(f"\n### {title}")
        print(f"{'rk':>3}  {'slug':<50}  {'FY-covered':<20}  {'mean comp':>9}")
        for i, (iid, mc) in enumerate(items[:top_n], start=1):
            slug, _, _ = inst_meta[iid]
            fys = sorted(years_by_inst[iid])
            fy_s = f"{len(fys)} ({min(fys)}-{max(fys)})" if len(fys) > 1 else f"1 ({fys[0]})"
            # Ascending-rank tables (bottom-N) show the actual rank from
            # the bottom end rather than 1..N. The display rank for
            # bottom-N item j = N_total - j + 1 where N_total is the full
            # cohort size.
            display_slug = slug
            marker = ""
            if slug in KNOWN_ARTIFACTS and (
                KNOWN_ARTIFACTS[slug][0] is None
                or KNOWN_ARTIFACTS[slug][0] in fys
            ):
                marker = " *"
                footnotes_seen.add(slug)
            display_rank = i
            print(f"{display_rank:>3}  {display_slug + marker:<50}  {fy_s:<20}  {mc:>9.3f}")

    _table(f"TOP 10 — financial (of {len(fin_sorted)})", fin_sorted, 10)
    _table(f"BOTTOM 10 — financial (of {len(fin_sorted)})", list(reversed(fin_sorted)), 10,
           ascending_rank=True)
    _table(f"TOP 10 — non-financial (of {len(non_fin_sorted)})", non_fin_sorted, 10)
    _table(f"BOTTOM 10 — non-financial (of {len(non_fin_sorted)})",
           list(reversed(non_fin_sorted)), 10, ascending_rank=True)

    if footnotes_seen:
        print()
        print("Footnotes:")
        for slug in sorted(footnotes_seen):
            _fy, tag, reason = KNOWN_ARTIFACTS[slug]
            print(f"  * {slug}: {tag} — {reason}")

    # ---- not-yet-covered -----------------------------------------------
    not_covered = _not_yet_covered()
    assert len(not_covered) == 60 - len(inst_meta), (
        f"not-covered count {len(not_covered)} doesn't complement "
        f"scored {len(inst_meta)}"
    )
    print(f"\n### 17 active institutions not yet scored (never ranked, never zero)")
    buckets = {"A": [], "B": [], "D": [], "unknown": []}
    for _iid, slug, name, is_fin, reason in not_covered:
        tag = "A" if reason.startswith("A:") else "B" if reason.startswith("B:") \
            else "D" if reason.startswith("D:") else "unknown"
        buckets[tag].append((slug, name, "fin" if is_fin else "non-fin", reason))
    for tag, label in [("A", "No file in storage"), ("B", "Only wayback picks, none passed as annual/integrated+auto_ok"),
                       ("D", "Has annual file but below 30-page threshold"),
                       ("unknown", "Unknown — investigate")]:
        if not buckets[tag]:
            continue
        print(f"\n[{tag}] {label}  (n={len(buckets[tag])})")
        for slug, name, sector, reason in buckets[tag]:
            print(f"  - {slug} ({sector})  [{name}]  — {reason[2:].strip()}")

    print(f"\nWrote: {scores_long}")
    print(f"Wrote: {summary_path}")


if __name__ == "__main__":
    build_leaderboard()
