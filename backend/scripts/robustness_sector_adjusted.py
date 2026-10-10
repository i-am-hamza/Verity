"""Sector-adjusted robustness check for v4 scores.

Formula (Ferjancic et al., 2024):
  adjusted_density = (density - sector_avg_density) / sector_avg_density

Sectors are the 11 SASB sectors, not the 22 industries used in the first pass.
The adjusted values are ranked 0-10 across all company-years pooled.
Composite = mean(e_score, s_score, g_score).

Reports:
  - Spearman rho vs main composite (company-level average)
  - 5 biggest movers up and down (company level)
  - Average main composite per SASB sector with n
"""
from __future__ import annotations

import sys
from collections import defaultdict
from pathlib import Path

BACKEND = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND))

from dotenv import load_dotenv  # noqa: E402

load_dotenv(BACKEND / ".env")

# SASB industry → sector mapping
INDUSTRY_TO_SECTOR: dict[str, str] = {
    # Financials
    "Commercial Banks": "Financials",
    "Asset Management & Custody Activities": "Financials",
    "Insurance": "Financials",
    "Consumer Finance": "Financials",
    "Investment Banking & Brokerage": "Financials",
    "Mortgage Finance": "Financials",
    "Security & Commodity Exchanges": "Financials",
    # Resource Transformation
    "Chemicals": "Resource Transformation",
    "Iron & Steel Producers": "Resource Transformation",
    "Metals & Mining": "Resource Transformation",
    "Containers & Packaging": "Resource Transformation",
    "Aerospace & Defense": "Resource Transformation",
    "Electrical & Electronic Equipment": "Resource Transformation",
    "Industrial Machinery & Goods": "Resource Transformation",
    # Extractives & Minerals Processing
    "Oil & Gas – Exploration & Production": "Extractives & Minerals Processing",  # noqa: RUF001
    "Oil & Gas – Refining & Marketing": "Extractives & Minerals Processing",  # noqa: RUF001
    "Oil & Gas – Services": "Extractives & Minerals Processing",  # noqa: RUF001
    "Oil & Gas – Midstream": "Extractives & Minerals Processing",  # noqa: RUF001
    "Coal Operations": "Extractives & Minerals Processing",
    "Construction Materials": "Extractives & Minerals Processing",
    # Technology & Communications
    "Telecommunication Services": "Technology & Communications",
    "Software & IT Services": "Technology & Communications",
    "Semiconductors": "Technology & Communications",
    "Hardware": "Technology & Communications",
    "Internet Media & Services": "Technology & Communications",
    "Electronic Manufacturing Services & Original Design Manufacturing": "Technology & Communications",
    # Services
    "Hotels & Lodging": "Services",
    "Casinos & Gaming": "Services",
    "Education": "Services",
    "Media & Entertainment": "Services",
    "Professional & Commercial Services": "Services",
    "Leisure Facilities": "Services",
    "Advertising & Marketing": "Services",
    "Restaurants": "Services",
    # Food & Beverage
    "Meat, Poultry & Dairy": "Food & Beverage",
    "Food Retailers & Distributors": "Food & Beverage",
    "Processed Foods": "Food & Beverage",
    "Agricultural Products": "Food & Beverage",
    "Alcoholic Beverages": "Food & Beverage",
    "Non-Alcoholic Beverages": "Food & Beverage",
    "Tobacco": "Food & Beverage",
    # Infrastructure
    "Real Estate": "Infrastructure",
    "Home Builders": "Infrastructure",
    "Electric Utilities & Power Generators": "Infrastructure",
    "Engineering & Construction Services": "Infrastructure",
    "Gas Utilities & Distributors": "Infrastructure",
    "Real Estate Services": "Infrastructure",
    "Waste Management": "Infrastructure",
    "Water Utilities": "Infrastructure",
    # Consumer Goods
    "Multiline and Specialty Retailers & Distributors": "Consumer Goods",
    "Apparel, Accessories & Footwear": "Consumer Goods",
    "Household & Personal Products": "Consumer Goods",
    "Toys & Sporting Goods": "Consumer Goods",
    "Building Products & Furnishings": "Consumer Goods",
    "E-Commerce": "Consumer Goods",
    # Transportation
    "Airlines": "Transportation",
    "Marine Transportation": "Transportation",
    "Auto Parts": "Transportation",
    "Automobiles": "Transportation",
    "Air Freight & Logistics": "Transportation",
    "Cruise Lines": "Transportation",
    "Rail Transportation": "Transportation",
    "Road Transportation": "Transportation",
    "Car Rental & Leasing": "Transportation",
    # Health Care
    "Health Care Delivery": "Health Care",
    "Biotechnology & Pharmaceuticals": "Health Care",
    "Drug Retailers": "Health Care",
    "Health Care Distributors": "Health Care",
    "Medical Equipment & Supplies": "Health Care",
    "Managed Care": "Health Care",
    # Renewable Resources & Alternative Energy
    "Biofuels": "Renewable Resources & Alternative Energy",
    "Forestry Management": "Renewable Resources & Alternative Energy",
    "Fuel Cells & Industrial Batteries": "Renewable Resources & Alternative Energy",
    "Pulp & Paper Products": "Renewable Resources & Alternative Energy",
    "Solar Technology & Project Developers": "Renewable Resources & Alternative Energy",
    "Wind Technology & Project Developers": "Renewable Resources & Alternative Energy",
}


def _spearman(a: list[float], b: list[float]) -> float:
    n = len(a)
    assert len(b) == n
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
    from app.services.pipeline import PIPELINE_VERSION
    from scripts.compute_ranks import _rank_scores

    db = SessionLocal()
    all_reports = (
        db.query(Report)
        .join(Institution, Institution.id == Report.institution_id)
        .filter(
            Report.status == ReportStatus.scored,
            Report.pipeline_version == PIPELINE_VERSION,
            Institution.active,
            Report.e_score.isnot(None),
        )
        .order_by(Institution.id, Report.fiscal_year, Report.id)
        .all()
    )
    seen_sd: dict[tuple, int] = {}
    reports_list: list = []
    for r in all_reports:
        key = (r.source_document_id, PIPELINE_VERSION) if r.source_document_id else (r.institution_id, r.fiscal_year, PIPELINE_VERSION)
        if key in seen_sd:
            reports_list[seen_sd[key]] = r
        else:
            seen_sd[key] = len(reports_list)
            reports_list.append(r)
    reports = reports_list
    inst_map = {i.id: i for i in db.query(Institution).filter(Institution.active).all()}

    print(f"Sector-adjusted robustness: {len(reports)} scored reports (pipeline={PIPELINE_VERSION})")
    print()

    # Map each report to a SASB sector
    def sector_for(r: Report) -> str:
        inst = inst_map.get(r.institution_id)
        ind = inst.sasb_industry if inst else None
        return INDUSTRY_TO_SECTOR.get(ind or "", "Unknown")

    sectors = [sector_for(r) for r in reports]

    # Compute sector average density per pillar
    sector_e: dict[str, list[float]] = defaultdict(list)
    sector_s: dict[str, list[float]] = defaultdict(list)
    sector_g: dict[str, list[float]] = defaultdict(list)
    for r, sec in zip(reports, sectors, strict=False):
        if r.e_density is not None:
            sector_e[sec].append(r.e_density)
        if r.s_density is not None:
            sector_s[sec].append(r.s_density)
        if r.g_density is not None:
            sector_g[sec].append(r.g_density)

    sector_e_avg = {s: sum(v)/len(v) for s, v in sector_e.items()}
    sector_s_avg = {s: sum(v)/len(v) for s, v in sector_s.items()}
    sector_g_avg = {s: sum(v)/len(v) for s, v in sector_g.items()}

    # Compute adjusted densities: (density - sector_avg) / sector_avg
    adj_e: list[float | None] = []
    adj_s: list[float | None] = []
    adj_g: list[float | None] = []
    for r, sec in zip(reports, sectors, strict=False):
        ea = sector_e_avg.get(sec, 0.0)
        sa = sector_s_avg.get(sec, 0.0)
        ga = sector_g_avg.get(sec, 0.0)
        adj_e.append((r.e_density - ea) / ea if r.e_density is not None and ea > 0 else None)
        adj_s.append((r.s_density - sa) / sa if r.s_density is not None and sa > 0 else None)
        adj_g.append((r.g_density - ga) / ga if r.g_density is not None and ga > 0 else None)

    # Rank adjusted values 0-10 across all company-years pooled
    e_sc = _rank_scores(adj_e)
    s_sc = _rank_scores(adj_s)
    g_sc = _rank_scores(adj_g)
    sec_comp = [
        (e + s + g) / 3.0 if e is not None and s is not None and g is not None else None
        for e, s, g in zip(e_sc, s_sc, g_sc, strict=False)
    ]

    # Company-level averages
    def company_avg(composites: list) -> dict[int, float]:
        by_inst: dict = defaultdict(list)
        for r, c in zip(reports, composites, strict=False):
            if c is not None:
                by_inst[r.institution_id].append(c)
        return {iid: sum(vs) / len(vs) for iid, vs in by_inst.items()}

    main_by_inst = company_avg([r.composite_score for r in reports])
    sec_by_inst = company_avg(sec_comp)

    # Spearman rho (company level)
    common = sorted(set(main_by_inst) & set(sec_by_inst))
    m_vals = [main_by_inst[i] for i in common]
    s_vals = [sec_by_inst[i] for i in common]
    rho = _spearman(m_vals, s_vals)
    print(f"Spearman rho (main composite vs sector-adjusted, company level): {rho:.4f}")
    print()

    # Movers
    diffs = sorted([(sec_by_inst[i] - main_by_inst[i], i) for i in common])
    print("5 movers DOWN:")
    for delta, iid in diffs[:5]:
        print(f"  {inst_map[iid].slug:<42} main={main_by_inst[iid]:.3f}  sector-adj={sec_by_inst[iid]:.3f}  d={delta:+.3f}")
    print()
    print("5 movers UP:")
    for delta, iid in diffs[-5:][::-1]:
        print(f"  {inst_map[iid].slug:<42} main={main_by_inst[iid]:.3f}  sector-adj={sec_by_inst[iid]:.3f}  d={delta:+.3f}")
    print()

    # Average MAIN composite per sector
    sector_main: dict[str, list[float]] = defaultdict(list)
    for r, sec in zip(reports, sectors, strict=False):
        if r.composite_score is not None:
            sector_main[sec].append(r.composite_score)

    print("Average MAIN composite per SASB sector:")
    print(f"  {'sector':<45} {'n':>4}  avg_main_composite")
    for sec in sorted(sector_main):
        vals = sector_main[sec]
        print(f"  {sec:<45} {len(vals):>4}  {sum(vals)/len(vals):.3f}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
