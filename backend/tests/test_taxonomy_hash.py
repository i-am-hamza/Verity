"""
Hash stability:
- Same taxonomy in different key order -> same hash.
- Changing a term's weight -> different hash.
- Adding a term -> different hash.
- Flipping a lemma_based flag -> different hash.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.taxonomy_hash import compute_taxonomy_hash

BASE = [
    {
        "name": "Environmental",
        "pillar": "Environmental",
        "weight": 1.0,
        "terms": [
            {"phrase": "climate risk", "weight": 1.2, "lemma_based": True},
            {"phrase": "carbon emissions", "weight": 1.2, "lemma_based": True},
        ],
    },
    {
        "name": "Governance",
        "pillar": "Governance",
        "weight": 1.0,
        "terms": [
            {"phrase": "corporate governance", "weight": 1.2, "lemma_based": True},
            {"phrase": "ICOFR", "weight": 1.4, "lemma_based": False},
        ],
    },
]


def test_key_and_list_order_do_not_affect_hash():
    h_base = compute_taxonomy_hash(BASE)

    # Categories reversed, terms reversed, dict key order shuffled.
    reordered = list(reversed([
        {
            "terms": list(reversed(cat["terms"])),
            "pillar": cat["pillar"],
            "name": cat["name"],
            "weight": cat["weight"],
        }
        for cat in BASE
    ]))
    assert compute_taxonomy_hash(reordered) == h_base


def test_changing_a_term_weight_changes_the_hash():
    h_base = compute_taxonomy_hash(BASE)
    tweaked = [
        {**cat, "terms": [dict(t) for t in cat["terms"]]}
        for cat in BASE
    ]
    tweaked[0]["terms"][0]["weight"] = 1.25  # was 1.2
    assert compute_taxonomy_hash(tweaked) != h_base


def test_adding_a_term_changes_the_hash():
    h_base = compute_taxonomy_hash(BASE)
    grown = [
        {**cat, "terms": [dict(t) for t in cat["terms"]]}
        for cat in BASE
    ]
    grown[1]["terms"].append({"phrase": "audit committee", "weight": 1.1, "lemma_based": True})
    assert compute_taxonomy_hash(grown) != h_base


def test_flipping_lemma_flag_changes_the_hash():
    h_base = compute_taxonomy_hash(BASE)
    flipped = [
        {**cat, "terms": [dict(t) for t in cat["terms"]]}
        for cat in BASE
    ]
    flipped[1]["terms"][1]["lemma_based"] = True  # ICOFR was False
    assert compute_taxonomy_hash(flipped) != h_base


def test_changing_a_category_pillar_changes_the_hash():
    """A future taxonomy restructuring that moves a category to a
    different pillar (e.g. Governance -> Social for social-governance
    hybrid categories) MUST bump the version — otherwise scores would
    silently reassign to a new pillar without a new hash.
    Session 2 didn't cover this; Patch A adds it."""
    h_base = compute_taxonomy_hash(BASE)
    moved = [
        {**cat, "terms": [dict(t) for t in cat["terms"]]}
        for cat in BASE
    ]
    moved[1]["pillar"] = "Social"  # Governance -> Social; name and terms unchanged
    assert compute_taxonomy_hash(moved) != h_base


def test_extra_metadata_fields_do_not_affect_hash():
    """Sourcing notes, timestamps, ids and other bookkeeping keys must not
    change the hash — canonicalise() strips everything that isn't semantic."""
    h_base = compute_taxonomy_hash(BASE)
    noisy = [
        {**cat, "_sourcing_note": "GRI 300 / SASB", "id": 42, "created_at": "2024-01-01"}
        for cat in BASE
    ]
    assert compute_taxonomy_hash(noisy) == h_base
