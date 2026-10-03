"""Canonical hashing for the taxonomy.

The seed loader creates a new TaxonomyVersion row only when this hash
changes, so re-running the loader without edits is a no-op.

Canonicalisation:
- categories are sorted by name
- terms within a category are sorted by phrase
- only the semantic fields go into the hash: category name, pillar,
  weight; term phrase, weight, lemma_based
- JSON is dumped with sort_keys=True and ensure_ascii=True so the byte
  sequence is deterministic across runs and platforms
"""
from __future__ import annotations

import hashlib
import json
from collections.abc import Iterable, Sequence
from typing import Any


def canonicalise(categories: Sequence[dict[str, Any]]) -> list[dict[str, Any]]:
    """Return a canonical representation ready for hashing.

    Input can come from the seed JSON (dicts) or from ORM query results
    projected into dicts. Extra keys (e.g. `_sourcing_note`, ORM id fields)
    are dropped on purpose so they don't affect the hash.
    """
    canonical: list[dict[str, Any]] = []
    for cat in sorted(categories, key=lambda c: c["name"]):
        terms_in = cat.get("terms") or []
        canonical_terms = [
            {
                "phrase": t["phrase"],
                "weight": float(t.get("weight", 1.0)),
                "lemma_based": bool(t.get("lemma_based", True)),
            }
            for t in sorted(terms_in, key=lambda t: t["phrase"])
        ]
        canonical.append({
            "name": cat["name"],
            "pillar": cat["pillar"],
            "weight": float(cat.get("weight", 1.0)),
            "terms": canonical_terms,
        })
    return canonical


def compute_taxonomy_hash(categories: Iterable[dict[str, Any]]) -> str:
    """sha256 of the canonical JSON bytes."""
    canonical = canonicalise(list(categories))
    payload = json.dumps(canonical, sort_keys=True, ensure_ascii=True, separators=(",", ":")).encode(
        "utf-8"
    )
    return hashlib.sha256(payload).hexdigest()
