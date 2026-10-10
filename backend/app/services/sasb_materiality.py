"""SASB materiality lookup for v4 term weighting.

Loads the industry→{SASB categories} mapping from the signed workbook
and answers: "is SASB category C material for industry I?"

Weight rule (B.3):
  1.5  if term's primary OR secondary SASB category is material for
       the company's SASB industry
  1.0  otherwise (including terms with no SASB category)
"""
from __future__ import annotations

import re
from collections import defaultdict
from functools import lru_cache
from pathlib import Path

_WORKBOOK_PATH = (
    Path(__file__).resolve().parents[3]
    / "docs" / "methodology" / "Verity_SASB_Mapping_Signed.xlsx"
)

MATERIAL_WEIGHT: float = 1.5
DEFAULT_WEIGHT: float = 1.0


def _norm(s: str) -> str:
    """Lowercase + collapse non-alphanumeric to single space."""
    return re.sub(r"[^a-z0-9]+", " ", s.lower()).strip()


@lru_cache(maxsize=1)
def _load_mapping() -> dict[str, set[str]]:
    """Return {normalised_industry: {normalised_category, ...}}.

    Loaded once per process; the lru_cache makes repeated calls free.
    """
    import openpyxl
    wb = openpyxl.load_workbook(str(_WORKBOOK_PATH), data_only=True)
    ws = wb["Industry materiality"]
    mapping: dict[str, set[str]] = defaultdict(set)
    for row in list(ws.iter_rows(values_only=True))[1:]:
        industry_raw = row[0]
        category_raw = row[2]
        if industry_raw and category_raw:
            mapping[_norm(str(industry_raw))].add(_norm(str(category_raw)))
    return dict(mapping)


def material_categories_for(sasb_industry: str | None) -> set[str]:
    """Return the set of normalised SASB categories that are material
    for the given SASB industry (normalised).  Empty set if unknown."""
    if not sasb_industry:
        return set()
    return _load_mapping().get(_norm(sasb_industry), set())


def term_weight(
    sasb_category_primary: str | None,
    sasb_category_secondary: str | None,
    sasb_industry: str | None,
) -> float:
    """Compute v4 weight for a single term given the scoring institution.

    Returns 1.5 if either SASB category of the term is material for
    the institution's SASB industry; otherwise 1.0.
    """
    if not (sasb_category_primary or sasb_category_secondary):
        return DEFAULT_WEIGHT
    mat = material_categories_for(sasb_industry)
    if not mat:
        return DEFAULT_WEIGHT
    p = _norm(sasb_category_primary) if sasb_category_primary else None
    s = _norm(sasb_category_secondary) if sasb_category_secondary else None
    if (p and p in mat) or (s and s in mat):
        return MATERIAL_WEIGHT
    return DEFAULT_WEIGHT
