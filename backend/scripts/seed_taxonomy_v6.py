"""Seed taxonomy v6: introduce a GENERAL component.

Changes from v5:
  - New category "General ESG terms" (pillar="General", weight=1.0).
  - Five formerly-generic terms (ESG, sustainability, GRI, sustainable development, CSR)
    move into the General category with group="core" so they contribute to general_density.
  - "innovation" (was Environmental core) moves to General category.
  - "feedback" and "digital services" (were Social core) move to General category.
  - A new TaxonomyVersion is registered with note="v6: General component".

Run once before the v6 batch rescore:
    python scripts/seed_taxonomy_v6.py
"""
from __future__ import annotations

import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND))

from dotenv import load_dotenv  # noqa: E402

load_dotenv(BACKEND / ".env")

# Phrases that move from "generic" group (old) → "core" group in General category
GENERIC_PHRASES: list[str] = [
    "ESG",
    "sustainability",
    "GRI",
    "sustainable development",
    "CSR",
]

# Phrases that move from their old E/S category → General category (group stays "core")
MOVE_TO_GENERAL: list[str] = [
    "innovation",
    "feedback",
    "digital services",
]

GENERAL_CATEGORY_NAME = "General ESG terms"


def main() -> int:
    import app.models.institution  # noqa: F401
    import app.models.provenance   # noqa: F401
    import app.models.report       # noqa: F401
    import app.models.score        # noqa: F401
    from app.database import SessionLocal
    from app.models.taxonomy import Category, TaxonomyVersion
    from app.models.taxonomy import Term
    from app.services.taxonomy_hash import compute_taxonomy_hash

    db = SessionLocal()

    # ------------------------------------------------------------------
    # 1. Create (or reuse) the General category
    # ------------------------------------------------------------------
    gen_cat = db.query(Category).filter(Category.name == GENERAL_CATEGORY_NAME).first()
    if gen_cat is None:
        gen_cat = Category(
            name=GENERAL_CATEGORY_NAME,
            pillar="General",
            weight=1.0,
        )
        db.add(gen_cat)
        db.flush()
        print(f"Created category '{GENERAL_CATEGORY_NAME}' id={gen_cat.id}")
    else:
        print(f"Category '{GENERAL_CATEGORY_NAME}' already exists id={gen_cat.id}")

    # ------------------------------------------------------------------
    # 2. Move formerly-generic terms to General category, group → "core"
    # ------------------------------------------------------------------
    for phrase in GENERIC_PHRASES:
        terms = db.query(Term).filter(Term.phrase == phrase).all()
        if not terms:
            print(f"  WARNING: phrase '{phrase}' not found")
            continue
        for t in terms:
            old_cat = t.category_id
            old_group = t.group
            t.category_id = gen_cat.id
            t.group = "core"
            print(f"  '{phrase}': cat {old_cat}->{gen_cat.id}  group '{old_group}'->'core'")

    # ------------------------------------------------------------------
    # 3. Move innovation / feedback / digital services to General category
    # ------------------------------------------------------------------
    for phrase in MOVE_TO_GENERAL:
        terms = db.query(Term).filter(Term.phrase == phrase).all()
        if not terms:
            print(f"  WARNING: phrase '{phrase}' not found")
            continue
        for t in terms:
            old_cat = t.category_id
            t.category_id = gen_cat.id
            # group stays "core"
            print(f"  '{phrase}': cat {old_cat}->{gen_cat.id}  (group '{t.group}' unchanged)")

    db.flush()

    # ------------------------------------------------------------------
    # 4. Compute the new taxonomy hash and register TaxonomyVersion v6
    # ------------------------------------------------------------------
    categories = db.query(Category).all()
    payload = [
        {
            "name": c.name,
            "pillar": c.pillar,
            "weight": c.weight,
            "terms": [
                {"phrase": t.phrase, "weight": t.weight, "lemma_based": t.lemma_based}
                for t in c.terms
            ],
        }
        for c in categories
    ]
    h = compute_taxonomy_hash(payload)

    existing_tv = db.query(TaxonomyVersion).filter(TaxonomyVersion.hash == h).first()
    if existing_tv:
        print(f"\nTaxonomyVersion already registered: hash={h[:16]}…  id={existing_tv.id}")
        if not existing_tv.note or not existing_tv.note.startswith("v6:"):
            existing_tv.note = "v6: General component; innovation/feedback/digital services moved; 0-100 scoring"
            print("  Updated note to v6.")
    else:
        tv = TaxonomyVersion(
            hash=h,
            note="v6: General component; innovation/feedback/digital services moved; 0-100 scoring",
        )
        db.add(tv)
        db.flush()
        print(f"\nRegistered TaxonomyVersion v6: hash={h[:16]}…  id={tv.id}")

    db.commit()
    print("\nDone. Re-run the full batch (python -m app.cli process --scope all) and then compute_ranks.py.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
