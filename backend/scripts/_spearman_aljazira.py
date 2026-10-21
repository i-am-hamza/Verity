"""Spearman rho: new pool (Aljazira) vs old pool (SIIG) for 64 common companies.

Old pool: 64 common + SIIG = 65 companies × 6 FY = 390 reports
New pool: 64 common + Aljazira = 65 companies × 6 FY = 390 reports
"""
import sys
from collections import defaultdict
from pathlib import Path

BACKEND = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND))
sys.stdout.reconfigure(encoding="utf-8")

from dotenv import load_dotenv
load_dotenv(BACKEND / ".env")
from app.crawler import register_all_mappers
register_all_mappers()

from app.database import SessionLocal
from app.models.institution import Institution
from app.models.report import Report, ReportStatus
from app.services.pipeline import PIPELINE_VERSION
from scripts.compute_ranks import _rank_scores
from sqlalchemy import select

db = SessionLocal()

# 64 common companies (all active except Aljazira)
all_active = db.query(Institution).filter(Institution.active).all()
aljazira_inst = db.execute(
    select(Institution).where(Institution.slug == "bank-aljazira")
).scalar_one()
siig_inst = db.execute(
    select(Institution).where(Institution.slug == "saudi-industrial-investment-group")
).scalar_one()

common_ids = {i.id for i in all_active if i.id != aljazira_inst.id}
print(f"Common companies: {len(common_ids)}  (expected 64)")

# Fetch all scored reports for: common + SIIG + Aljazira
relevant_inst_ids = common_ids | {siig_inst.id, aljazira_inst.id}
all_reports = (
    db.query(Report)
    .join(Institution, Institution.id == Report.institution_id)
    .filter(
        Report.pipeline_version == PIPELINE_VERSION,
        Report.status == ReportStatus.scored,
        Report.institution_id.in_(list(relevant_inst_ids)),
    )
    .all()
)

# Deduplicate by source_document_id
seen: dict = {}
reports_dedup: list = []
for r in all_reports:
    key = (r.source_document_id, PIPELINE_VERSION) if r.source_document_id else (r.institution_id, r.fiscal_year, PIPELINE_VERSION)
    if key in seen:
        reports_dedup[seen[key]] = r
    else:
        seen[key] = len(reports_dedup)
        reports_dedup.append(r)

# Build separate pools
old_pool = [r for r in reports_dedup if r.institution_id in (common_ids | {siig_inst.id})]
new_pool = [r for r in reports_dedup if r.institution_id in (common_ids | {aljazira_inst.id})]
print(f"Old pool size: {len(old_pool)}  New pool size: {len(new_pool)}")

# Compute rank scores for both pools
def rank_pool(pool: list, attr: str) -> dict[int, float | None]:
    """Return {report_id: score} for a pool."""
    densities = [getattr(r, attr) for r in pool]
    scored = _rank_scores(densities)
    return {r.id: s for r, s in zip(pool, scored)}

old_e = rank_pool(old_pool, "e_density")
old_s = rank_pool(old_pool, "s_density")
old_g = rank_pool(old_pool, "g_density")
old_gen = rank_pool(old_pool, "general_density")

new_e = rank_pool(new_pool, "e_density")
new_s = rank_pool(new_pool, "s_density")
new_g = rank_pool(new_pool, "g_density")
new_gen = rank_pool(new_pool, "general_density")

def comp(e: float | None, s: float | None, g: float | None, gen: float | None) -> float | None:
    if any(x is None for x in (e, s, g, gen)):
        return None
    return (e + s + g + gen) / 4.0  # type: ignore[operator]

# Map report ids for common companies
common_report_ids: dict[int, list[int]] = defaultdict(list)  # inst_id -> [report_ids]
for r in reports_dedup:
    if r.institution_id in common_ids:
        common_report_ids[r.institution_id].append(r.id)

# Company-year level Spearman for 64 common companies
pairs_e: list[tuple[float, float]] = []
pairs_s: list[tuple[float, float]] = []
pairs_g: list[tuple[float, float]] = []
pairs_comp: list[tuple[float, float]] = []

for inst_id, rids in common_report_ids.items():
    for rid in rids:
        oe = old_e.get(rid)
        os = old_s.get(rid)
        og = old_g.get(rid)
        ogen = old_gen.get(rid)
        ne = new_e.get(rid)
        ns = new_s.get(rid)
        ng = new_g.get(rid)
        ngen = new_gen.get(rid)
        oc = comp(oe, os, og, ogen)
        nc = comp(ne, ns, ng, ngen)
        if oe is not None and ne is not None:
            pairs_e.append((oe, ne))
        if os is not None and ns is not None:
            pairs_s.append((os, ns))
        if og is not None and ng is not None:
            pairs_g.append((og, ng))
        if oc is not None and nc is not None:
            pairs_comp.append((oc, nc))

# Company-level (average) Spearman
def avg_by_inst(pool: list, score_map: dict[int, float | None]) -> dict[int, float]:
    d: dict[int, list[float]] = defaultdict(list)
    for r in pool:
        if r.institution_id in common_ids:
            s = score_map.get(r.id)
            if s is not None:
                d[r.institution_id].append(s)
    return {iid: sum(v) / len(v) for iid, v in d.items()}

old_comp_by_rid = {r.id: comp(old_e.get(r.id), old_s.get(r.id), old_g.get(r.id), old_gen.get(r.id))
                   for r in old_pool}
new_comp_by_rid = {r.id: comp(new_e.get(r.id), new_s.get(r.id), new_g.get(r.id), new_gen.get(r.id))
                   for r in new_pool}

old_e_inst = avg_by_inst(old_pool, old_e)
old_s_inst = avg_by_inst(old_pool, old_s)
old_g_inst = avg_by_inst(old_pool, old_g)
old_comp_inst = avg_by_inst(old_pool, old_comp_by_rid)
new_e_inst = avg_by_inst(new_pool, new_e)
new_s_inst = avg_by_inst(new_pool, new_s)
new_g_inst = avg_by_inst(new_pool, new_g)
new_comp_inst = avg_by_inst(new_pool, new_comp_by_rid)

def spearman(pairs: list[tuple[float, float]]) -> float:
    n = len(pairs)
    if n < 2:
        return float("nan")
    a = [x for x, _ in pairs]
    b = [y for _, y in pairs]
    # rank a
    def rank(v: list[float]) -> list[float]:
        indexed = sorted(range(len(v)), key=lambda i: v[i])
        ranks = [0.0] * len(v)
        pos = 0
        while pos < len(v):
            end = pos + 1
            while end < len(v) and v[indexed[end]] == v[indexed[pos]]:
                end += 1
            avg = (pos + end + 1) / 2.0
            for k in range(pos, end):
                ranks[indexed[k]] = avg
            pos = end
        return ranks
    ra, rb = rank(a), rank(b)
    d2 = sum((ra[i] - rb[i]) ** 2 for i in range(n))
    return round(1 - 6 * d2 / (n * (n * n - 1)), 4)

# Company-year Spearman
rho_e_cy = spearman(pairs_e)
rho_s_cy = spearman(pairs_s)
rho_g_cy = spearman(pairs_g)
rho_comp_cy = spearman(pairs_comp)

# Company-level Spearman
common_iids_both = sorted(set(old_comp_inst) & set(new_comp_inst))
inst_pairs_e = [(old_e_inst[i], new_e_inst[i]) for i in common_iids_both if i in old_e_inst and i in new_e_inst]
inst_pairs_s = [(old_s_inst[i], new_s_inst[i]) for i in common_iids_both if i in old_s_inst and i in new_s_inst]
inst_pairs_g = [(old_g_inst[i], new_g_inst[i]) for i in common_iids_both if i in old_g_inst and i in new_g_inst]
inst_pairs_comp = [(old_comp_inst[i], new_comp_inst[i]) for i in common_iids_both]

rho_e_inst = spearman(inst_pairs_e)
rho_s_inst = spearman(inst_pairs_s)
rho_g_inst = spearman(inst_pairs_g)
rho_comp_inst = spearman(inst_pairs_comp)

print(f"\n=== Spearman rho: new pool (Aljazira) vs old pool (SIIG), 64 common companies ===")
print(f"  {'Metric':<20} {'company':>10} {'company-year':>14}")
print(f"  {'Composite':<20} {rho_comp_inst:>10.4f} {rho_comp_cy:>14.4f}")
print(f"  {'Environmental':<20} {rho_e_inst:>10.4f} {rho_e_cy:>14.4f}")
print(f"  {'Social':<20} {rho_s_inst:>10.4f} {rho_s_cy:>14.4f}")
print(f"  {'Governance':<20} {rho_g_inst:>10.4f} {rho_g_cy:>14.4f}")

db.close()
