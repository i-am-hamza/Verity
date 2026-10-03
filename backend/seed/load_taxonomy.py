"""Load seed/taxonomy_starter.json into the database.

Also records a TaxonomyVersion row whose hash is the sha256 of the canonical
JSON (see app.services.taxonomy_hash). A new version row is created only
when the hash changes; rerunning the loader without edits is a no-op for
the versions table.

Usage (from backend/):
    python -m seed.load_taxonomy
"""
from __future__ import annotations

import json
from pathlib import Path

from app.database import SessionLocal
from app.models import (  # noqa: F401 — force mapper registration
    institution as _institution,
    provenance as _provenance,
    report as _report,
    score as _score,
    taxonomy as _taxonomy,
)
from app.models.taxonomy import PILLARS, Category, TaxonomyVersion, Term
from app.services.taxonomy_hash import compute_taxonomy_hash


def _ensure_taxonomy_version(db, categories_json: list[dict]) -> tuple[TaxonomyVersion, bool]:
    """Return (row, created?) for the taxonomy version identified by hash."""
    h = compute_taxonomy_hash(categories_json)
    existing = db.query(TaxonomyVersion).filter(TaxonomyVersion.hash == h).first()
    if existing:
        return existing, False
    row = TaxonomyVersion(hash=h, note="seed loader")
    db.add(row)
    db.flush()
    return row, True


def load() -> None:
    db = SessionLocal()

    data_path = Path(__file__).parent / "taxonomy_starter.json"
    categories_json = json.loads(data_path.read_text(encoding="utf-8"))

    version_row, created = _ensure_taxonomy_version(db, categories_json)
    if created:
        print(f"Registered new taxonomy version {version_row.hash[:12]}...")
    else:
        print(f"Taxonomy version {version_row.hash[:12]}... already registered (id={version_row.id})")

    for cat_data in categories_json:
        pillar = cat_data["pillar"]
        if pillar not in PILLARS:
            raise ValueError(f"'{cat_data['name']}' has pillar '{pillar}', must be one of {PILLARS}")

        existing = db.query(Category).filter(Category.name == cat_data["name"]).first()
        if existing is None:
            category = Category(
                name=cat_data["name"], pillar=pillar, weight=cat_data.get("weight", 1.0)
            )
            db.add(category)
            db.flush()
            for term_data in cat_data["terms"]:
                db.add(Term(
                    category_id=category.id,
                    phrase=term_data["phrase"],
                    weight=term_data.get("weight", 1.0),
                    lemma_based=term_data.get("lemma_based", True),
                ))
            print(f"Loaded '{cat_data['name']}' with {len(cat_data['terms'])} terms")
            continue

        # Category exists — add any NEW terms within it. Phrases are the
        # natural key; identical phrases are untouched so existing weights
        # or lemma flags aren't silently overwritten (the loader is append-
        # only; weight edits must go through a new taxonomy version).
        have = {t.phrase for t in existing.terms}
        added = 0
        for term_data in cat_data["terms"]:
            if term_data["phrase"] in have:
                continue
            db.add(Term(
                category_id=existing.id,
                phrase=term_data["phrase"],
                weight=term_data.get("weight", 1.0),
                lemma_based=term_data.get("lemma_based", True),
            ))
            added += 1
        if added:
            print(f"Added {added} new term(s) to existing category '{cat_data['name']}'")
        else:
            print(f"No changes to '{cat_data['name']}' — all terms already present")

    db.commit()
    db.close()


if __name__ == "__main__":
    load()
