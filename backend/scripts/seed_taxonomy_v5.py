"""Seed taxonomy v5 (examiner additions) — ADDITIVE, keeps v4 rows intact.

Run from backend/ with the venv active:
    python scripts/seed_taxonomy_v5.py

Adds 23 new term rows to the existing categories (does NOT delete v4 terms
or MatchEvidence rows — those have FK references).  Computes a new taxonomy
hash from the full set of 104 terms and registers it as TaxonomyVersion v5.

v5 layout after this script:
  core   = 90 rows (E=25, S=29, G=36)  — +23 rows over v4
  addon  =  9 rows (unchanged)
  generic=  5 rows (unchanged)
  Total  = 104 rows

The 16 new term *concepts* (multi-variant concepts count as one):
  E (4): climate policy, pollution, resource use, innovation
  S (8): employee engagement, employee ownership/share,
         pension benefits, end of service, poverty,
         customer/client needs (4 phrases), feedback, digital services
  G (4): board meeting / meetings of directors / meetings of the board,
         dividend policy, stakeholder engagement, incentive plan

Overlap with v4:
  "meetings of the board" (new, 4 tokens) vs "board of directors"
  (v4, 3 tokens): both match in "meetings of the board of directors".
  Longest-match-wins resolves it (new phrase takes priority).
  Both are Governance/None — no pillar or SASB impact.
"""
from __future__ import annotations

import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND))

from dotenv import load_dotenv  # noqa: E402

load_dotenv(BACKEND / ".env")

# ---------------------------------------------------------------------------
# NEW v5 terms only (the 23 rows added over v4)
# (phrase, pillar, group, lemma_based, sasb_category_primary, sasb_category_secondary)
# ---------------------------------------------------------------------------

V5_NEW_TERMS: list[tuple[str, str, str, bool, str | None, str | None]] = [
    # ── Environmental — v5 new (4) ────────────────────────────────────────────
    ("climate policy",     "Environmental", "core", True,  "GHG Emissions",                    None),
    ("pollution",          "Environmental", "core", True,  "Ecological Impacts",               None),
    ("resource use",       "Environmental", "core", True,  "Materials Sourcing & Efficiency",  None),
    ("innovation",         "Environmental", "core", True,  None,                               None),

    # ── Social — v5 new (8 concepts, 13 rows) ────────────────────────────────
    ("employee engagement",      "Social", "core", True,  "Employee Engagement, Diversity & Inclusion", None),
    ("employee ownership",       "Social", "core", True,  "Employee Engagement, Diversity & Inclusion", None),
    ("employee share ownership", "Social", "core", True,  "Employee Engagement, Diversity & Inclusion", None),
    ("pension benefits",         "Social", "core", True,  "Labor Practices",                   None),
    ("end of service",           "Social", "core", True,  "Labor Practices",                   None),
    ("end-of-service",           "Social", "core", False, "Labor Practices",                   None),
    ("poverty",                  "Social", "core", True,  "Human Rights & Community Relations", None),
    ("customer needs",           "Social", "core", True,  "Customer Welfare",                  None),
    ("customers' needs",         "Social", "core", False, "Customer Welfare",                  None),
    ("client needs",             "Social", "core", True,  "Customer Welfare",                  None),
    ("clients' needs",           "Social", "core", False, "Customer Welfare",                  None),
    ("feedback",                 "Social", "core", True,  None,                                None),
    ("digital services",         "Social", "core", True,  "Access & Affordability",            None),

    # ── Governance — v5 new (4 concepts, 6 rows) ─────────────────────────────
    ("board meeting",            "Governance", "core", True,  None, None),
    ("meetings of directors",    "Governance", "core", True,  None, None),
    ("meetings of the board",    "Governance", "core", True,  None, None),
    ("dividend policy",          "Governance", "core", True,  None, None),
    ("stakeholder engagement",   "Governance", "core", True,  None, None),
    ("incentive plan",           "Governance", "core", True,  None, None),
]

assert len(V5_NEW_TERMS) == 23, f"expected 23 new rows, got {len(V5_NEW_TERMS)}"


def main() -> None:
    import app.models.institution  # noqa: F401
    import app.models.provenance   # noqa: F401
    import app.models.report       # noqa: F401
    import app.models.review       # noqa: F401
    import app.models.run          # noqa: F401
    import app.models.score        # noqa: F401
    import app.models.taxonomy     # noqa: F401
    from app.database import SessionLocal
    from app.models.taxonomy import Category, TaxonomyVersion, Term
    from app.services.taxonomy_hash import compute_taxonomy_hash

    db = SessionLocal()

    # 1. Load existing categories (created by v4 seed)
    cat_map: dict[str, Category] = {c.name: c for c in db.query(Category).all()}
    required_pillars = {"Environmental", "Social", "Governance", "Addon", "Generic"}
    missing = required_pillars - set(cat_map)
    if missing:
        raise RuntimeError(
            f"Missing categories: {missing}. Run seed_taxonomy_v4.py first."
        )
    print(f"Existing categories loaded: {sorted(cat_map)}")

    # 2. Existing phrase set (idempotency)
    existing_phrases = {t.phrase for t in db.query(Term).all()}
    print(f"Existing terms: {len(existing_phrases)}")

    # 3. Add new terms (skip any that already exist)
    added = 0
    skipped = 0
    for phrase, pillar, group, lemma_based, sasb_primary, sasb_secondary in V5_NEW_TERMS:
        if phrase in existing_phrases:
            print(f"  SKIP (already exists): {phrase!r}")
            skipped += 1
            continue
        db.add(Term(
            category_id=cat_map[pillar].id,
            phrase=phrase,
            weight=1.0,
            lemma_based=lemma_based,
            group=group,
            sasb_category_primary=sasb_primary,
            sasb_category_secondary=sasb_secondary,
        ))
        added += 1
    db.flush()
    print(f"Terms added: {added}  skipped (already exist): {skipped}")

    # 4. Compute hash from full current term set
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

    # Check this hash isn't already registered (idempotency)
    existing_tv = db.query(TaxonomyVersion).filter(TaxonomyVersion.hash == h).first()
    if existing_tv:
        print(f"TaxonomyVersion already registered: hash={h[:16]}… id={existing_tv.id}")
    else:
        note = (
            "v5: 90 core (E25 S29 G36) + 9 addon + 5 generic; "
            "+16 examiner terms (4E 8S 4G concepts, 23 new rows)"
        )
        tv = TaxonomyVersion(hash=h, note=note)
        db.add(tv)
        db.commit()
        print(f"TaxonomyVersion v5 registered: hash={h[:16]}… note={note!r}")

    db.commit()

    # 5. Verify final counts
    all_terms = db.query(Term).all()
    core_e = [t for t in all_terms if t.group == "core" and t.category.pillar == "Environmental"]
    core_s = [t for t in all_terms if t.group == "core" and t.category.pillar == "Social"]
    core_g = [t for t in all_terms if t.group == "core" and t.category.pillar == "Governance"]
    addon  = [t for t in all_terms if t.group == "addon"]
    gen    = [t for t in all_terms if t.group == "generic"]

    print()
    print("v5 taxonomy summary:")
    print(f"  Core E={len(core_e)}  S={len(core_s)}  G={len(core_g)}  total={len(core_e)+len(core_s)+len(core_g)}")
    print(f"  Add-on={len(addon)}  Generic={len(gen)}")
    print(f"  Hash={h}")

    db.close()


if __name__ == "__main__":
    main()
