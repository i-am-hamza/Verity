"""Seed taxonomy v4 and populate institution SASB industries.

Run from backend/ with the venv active:
    python scripts/seed_taxonomy_v4.py

Clears all existing categories and terms, inserts v4 taxonomy, registers
the taxonomy hash, and populates institutions.sasb_industry from the
workbook.

v4 layout:
  core   = 67 terms (E=21, S=16, G=30)  — contribute to E/S/G pillar density
  addon  =  9 terms (financial companies only)
  generic=  5 terms (counted separately, excluded from pillars)
  Total  = 81 terms in DB
"""
from __future__ import annotations

import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parent.parent
REPO_ROOT = BACKEND.parent
sys.path.insert(0, str(BACKEND))

from dotenv import load_dotenv  # noqa: E402

load_dotenv(BACKEND / ".env")

# ---------------------------------------------------------------------------
# v4 Term definitions
# (phrase, pillar, group, lemma_based, sasb_category_primary, sasb_category_secondary)
# pillar: "Environmental" | "Social" | "Governance" | "Addon" | "Generic"
# group:  "core" | "addon" | "generic"
# ---------------------------------------------------------------------------

V4_TERMS: list[tuple[str, str, str, bool, str | None, str | None]] = [
    # ── Environmental — Core (21) ────────────────────────────────────────────
    ("climate change",     "Environmental", "core", True,  "GHG Emissions",                    "Physical Impacts of Climate Change"),
    ("climate risk",       "Environmental", "core", True,  "Physical Impacts of Climate Change","Business Model Resilience"),
    ("carbon emissions",   "Environmental", "core", True,  "GHG Emissions",                    None),
    ("carbon footprint",   "Environmental", "core", True,  "GHG Emissions",                    None),
    ("greenhouse gas",     "Environmental", "core", True,  "GHG Emissions",                    None),
    ("net zero",           "Environmental", "core", True,  "GHG Emissions",                    None),
    ("renewable energy",   "Environmental", "core", True,  "Energy Management",                None),
    ("energy efficiency",  "Environmental", "core", True,  "Energy Management",                None),
    ("water management",   "Environmental", "core", True,  "Water & Wastewater Management",    None),
    ("waste management",   "Environmental", "core", True,  "Waste & Hazardous Materials Management", None),
    ("biodiversity",       "Environmental", "core", True,  "Ecological Impacts",               None),
    ("nature-positive",    "Environmental", "core", True,  "Ecological Impacts",               None),
    ("nature-related",     "Environmental", "core", True,  "Ecological Impacts",               None),
    ("green bond",         "Environmental", "core", True,  None,                               None),
    ("environmental risk", "Environmental", "core", True,  None,                               None),
    # new v4 Environmental core terms
    ("air quality",        "Environmental", "core", True,  "Air Quality",                      None),
    ("NOx",                "Environmental", "core", False, "Air Quality",                      None),
    ("flaring",            "Environmental", "core", True,  "Air Quality",                      None),
    ("LEED",               "Environmental", "core", False, "Product Design & Lifecycle Management", None),
    ("e-waste",            "Environmental", "core", False, "Product Design & Lifecycle Management", None),
    ("circular economy",   "Environmental", "core", True,  "Materials Sourcing & Efficiency",  None),

    # ── Social — Core (16) ──────────────────────────────────────────────────
    ("diversity and inclusion",  "Social", "core", True,  "Employee Engagement, Diversity & Inclusion", None),
    ("gender diversity",         "Social", "core", True,  "Employee Engagement, Diversity & Inclusion", None),
    ("employee training",        "Social", "core", True,  "Employee Engagement, Diversity & Inclusion", None),
    ("human rights",             "Social", "core", True,  "Human Rights & Community Relations", None),
    ("community investment",     "Social", "core", True,  "Human Rights & Community Relations", None),
    ("community development",    "Social", "core", True,  "Human Rights & Community Relations", "Access & Affordability"),
    ("employee wellbeing",       "Social", "core", True,  "Employee Health & Safety",          "Labor Practices"),
    ("health and safety",        "Social", "core", True,  "Employee Health & Safety",          "Product Quality & Safety"),
    ("customer privacy",         "Social", "core", True,  "Customer Privacy",                  None),
    ("supply chain",             "Social", "core", True,  "Supply Chain Management",           None),
    ("accessibility",            "Social", "core", True,  "Access & Affordability",            None),
    ("customer satisfaction",    "Social", "core", True,  None,                                None),
    ("zakat",                    "Social", "core", True,  None,                                None),
    # new v4 Social core terms
    ("food safety",              "Social", "core", True,  "Product Quality & Safety",          None),
    ("product safety",           "Social", "core", True,  "Product Quality & Safety",          None),
    ("responsible sourcing",     "Social", "core", True,  "Materials Sourcing & Efficiency",   None),

    # ── Governance — Core (30) ──────────────────────────────────────────────
    ("corporate governance",                  "Governance", "core", True,  None, None),
    ("governance",                            "Governance", "core", True,  None, None),
    ("board of directors",                    "Governance", "core", True,  None, None),
    ("board independence",                    "Governance", "core", True,  None, None),
    ("audit committee",                       "Governance", "core", True,  None, None),
    ("risk committee",                        "Governance", "core", True,  None, None),
    ("risk management",                       "Governance", "core", True,  None, None),
    ("executive compensation",                "Governance", "core", True,  None, None),
    ("shareholder rights",                    "Governance", "core", True,  None, None),
    ("internal control",                      "Governance", "core", True,  None, None),
    ("internal control over financial reporting", "Governance", "core", False, None, None),
    ("ICOFR",                                 "Governance", "core", False, None, None),
    ("material weakness",                     "Governance", "core", True,  None, None),
    ("IT general control",                    "Governance", "core", True,  None, None),
    ("ITGC",                                  "Governance", "core", False, None, None),
    ("remuneration committee",                "Governance", "core", True,  None, None),
    ("ESG committee",                         "Governance", "core", True,  None, None),
    ("code of conduct",                       "Governance", "core", True,  "Business Ethics",  None),
    ("whistleblower",                         "Governance", "core", True,  "Business Ethics",  None),
    ("anti-corruption",                       "Governance", "core", True,  "Business Ethics",  None),
    ("business ethics",                       "Governance", "core", True,  "Business Ethics",  None),
    ("fraud",                                 "Governance", "core", True,  "Business Ethics",  None),
    ("IT governance",                         "Governance", "core", True,  "Data Security",    None),
    ("information security",                  "Governance", "core", True,  "Data Security",    None),
    ("cybersecurity",                         "Governance", "core", True,  "Data Security",    None),
    ("data protection",                       "Governance", "core", True,  "Customer Privacy", "Data Security"),
    # new v4 Governance core terms
    ("process safety",           "Governance", "core", True,  "Critical Incident Risk Management", None),
    ("asset integrity",          "Governance", "core", True,  "Critical Incident Risk Management", None),
    ("emergency preparedness",   "Governance", "core", True,  "Critical Incident Risk Management", None),
    ("business continuity",      "Governance", "core", True,  "Systemic Risk Management",          None),

    # ── Financial Add-on (9, scored for 19 financial companies only) ─────────
    ("green financing",       "Addon", "addon", True,  "Product Design & Lifecycle Management", None),
    ("sustainable finance",   "Addon", "addon", True,  "Product Design & Lifecycle Management", None),
    ("sustainable financing", "Addon", "addon", True,  "Product Design & Lifecycle Management", None),
    ("financial inclusion",   "Addon", "addon", True,  "Access & Affordability",                None),
    ("responsible lending",   "Addon", "addon", True,  "Selling Practices & Product Labeling",  None),
    ("fair lending",          "Addon", "addon", True,  "Access & Affordability",                "Selling Practices & Product Labeling"),
    ("financial literacy",    "Addon", "addon", True,  "Access & Affordability",                None),
    ("anti-money laundering", "Addon", "addon", True,  "Business Ethics",                       None),
    ("stress testing",        "Addon", "addon", True,  "Systemic Risk Management",              None),

    # ── Generic (5, counted separately; excluded from E/S/G and composite) ───
    ("ESG",                  "Generic", "generic", False, None, None),
    ("sustainability",       "Generic", "generic", True,  None, None),
    ("GRI",                  "Generic", "generic", False, None, None),
    ("sustainable development", "Generic", "generic", True, None, None),
    ("CSR",                  "Generic", "generic", False, None, None),
]

# Verify counts before writing anything
_core  = [t for t in V4_TERMS if t[2] == "core"]
_addon = [t for t in V4_TERMS if t[2] == "addon"]
_gen   = [t for t in V4_TERMS if t[2] == "generic"]
_core_e = [t for t in _core if t[1] == "Environmental"]
_core_s = [t for t in _core if t[1] == "Social"]
_core_g = [t for t in _core if t[1] == "Governance"]

assert len(_core)  == 67, f"core={len(_core)}, expected 67"
assert len(_core_e) == 21, f"core E={len(_core_e)}, expected 21"
assert len(_core_s) == 16, f"core S={len(_core_s)}, expected 16"
assert len(_core_g) == 30, f"core G={len(_core_g)}, expected 30"
assert len(_addon) ==  9, f"addon={len(_addon)}, expected 9"
assert len(_gen)   ==  5, f"generic={len(_gen)}, expected 5"


# ---------------------------------------------------------------------------
# Company → SASB industry mapping
# ---------------------------------------------------------------------------

def _load_sasb_industries() -> dict[str, str]:
    """Return {company_name: sasb_industry} from the workbook."""
    import openpyxl
    wb = openpyxl.load_workbook(
        str(REPO_ROOT / "docs" / "methodology" / "Verity_SASB_Mapping_Signed.xlsx"),
        data_only=True,
    )
    ws = wb["Company industries"]
    rows = list(ws.iter_rows(values_only=True))[1:]
    result = {}
    for row in rows:
        company_name = row[1]
        sasb_industry = row[7]
        if company_name and sasb_industry:
            result[str(company_name).strip()] = str(sasb_industry).strip()
    return result


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    import app.models.provenance
    import app.models.report
    import app.models.score  # noqa: F401
    from app.database import SessionLocal
    from app.models.institution import Institution
    from app.models.taxonomy import Category, TaxonomyVersion, Term
    from app.services.taxonomy_hash import compute_taxonomy_hash

    db = SessionLocal()

    # 1. Clear existing taxonomy
    print("Clearing existing terms and categories…")
    db.query(Term).delete()
    db.query(Category).delete()
    db.query(TaxonomyVersion).delete()
    db.commit()

    # 2. Create categories
    pillars = ["Environmental", "Social", "Governance", "Addon", "Generic"]
    cat_map: dict[str, Category] = {}
    for pillar in pillars:
        cat = Category(name=pillar, pillar=pillar, weight=1.0)
        db.add(cat)
        cat_map[pillar] = cat
    db.flush()

    # 3. Insert terms
    for phrase, pillar, group, lemma_based, sasb_primary, sasb_secondary in V4_TERMS:
        t = Term(
            category_id=cat_map[pillar].id,
            phrase=phrase,
            weight=1.0,          # static weight is 1.0; runtime weight is dynamic (1.5/1.0)
            lemma_based=lemma_based,
            group=group,
            sasb_category_primary=sasb_primary,
            sasb_category_secondary=sasb_secondary,
        )
        db.add(t)
    db.flush()

    # 4. Register taxonomy version
    cats = db.query(Category).all()
    payload = [
        {
            "name": c.name,
            "pillar": c.pillar,
            "weight": c.weight,
            "terms": [
                {
                    "phrase": t.phrase,
                    "weight": t.weight,
                    "lemma_based": t.lemma_based,
                    "group": t.group,
                    "sasb_category_primary": t.sasb_category_primary,
                    "sasb_category_secondary": t.sasb_category_secondary,
                }
                for t in sorted(c.terms, key=lambda x: x.phrase)
            ],
        }
        for c in sorted(cats, key=lambda x: x.name)
    ]
    h = compute_taxonomy_hash(payload)
    tv = TaxonomyVersion(hash=h, note="v4: 67 core (E21 S16 G30) + 9 addon + 5 generic")
    db.add(tv)
    db.commit()
    print(f"Taxonomy v4 registered: hash={h}")

    # 5. Populate institution SASB industries
    print("Populating institution SASB industries…")
    name_to_industry = _load_sasb_industries()
    institutions = db.query(Institution).filter(Institution.active).all()
    matched = 0
    unmatched = []
    for inst in institutions:
        if inst.name in name_to_industry:
            inst.sasb_industry = name_to_industry[inst.name]
            matched += 1
        else:
            # Try to find by partial match
            candidates = [n for n in name_to_industry if inst.name in n or n in inst.name]
            if len(candidates) == 1:
                inst.sasb_industry = name_to_industry[candidates[0]]
                matched += 1
            else:
                unmatched.append(inst.name)
    db.commit()
    print(f"  Matched {matched} institutions; {len(unmatched)} unmatched:")
    for u in unmatched:
        print(f"    UNMATCHED: {u!r}")

    # Report
    print()
    print("v4 taxonomy summary:")
    print(f"  Core E={len(_core_e)}  S={len(_core_s)}  G={len(_core_g)}  total={len(_core)}")
    print(f"  Add-on={len(_addon)}  Generic={len(_gen)}")
    print(f"  Hash={h}")


if __name__ == "__main__":
    main()
