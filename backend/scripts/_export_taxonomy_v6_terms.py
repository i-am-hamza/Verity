"""One-shot export of the live taxonomy v6 term list to CSV.

Columns:
    concept           — distinct conceptual phrase (Term.phrase)
    spelling_variants — the exact `Term.phrase` strings that make up the
                        concept, pipe-separated. For most concepts there is
                        a single canonical phrase; the matcher already
                        normalises inflections through lemma matching.
    component         — pillar bucket: E / S / G / General / Banking.
                        E/S/G = Term in core group AND Category.pillar.
                        General = Term in core group AND pillar == General.
                        Banking = Term.group == "addon" (financial add-on).
    sasb_category     — SASB General Issue Category (primary; secondary in
                        parentheses if set).
    industries        — comma-separated SASB industry names for which this
                        term's SASB category is material (empty if the term
                        has no SASB category).

Writes to docs/scoring_code/taxonomy_v6_terms.csv.
"""
from __future__ import annotations

import csv
import re
import sys
from collections import defaultdict
from pathlib import Path

BACKEND = Path(__file__).resolve().parent.parent
REPO = BACKEND.parent
sys.path.insert(0, str(BACKEND))

from dotenv import load_dotenv  # noqa: E402

load_dotenv(BACKEND / ".env")

OUT_PATH = REPO / "docs" / "scoring_code" / "taxonomy_v6_terms.csv"


def _norm(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", s.lower()).strip()


def industries_for_sasb_category(sasb_cat: str | None, mapping: dict[str, set[str]]) -> list[str]:
    if not sasb_cat:
        return []
    target = _norm(sasb_cat)
    return sorted(ind for ind, cats in mapping.items() if target in cats)


def main() -> int:
    import app.models.company_year  # noqa: F401
    import app.models.institution   # noqa: F401
    import app.models.provenance    # noqa: F401
    import app.models.report        # noqa: F401
    import app.models.review        # noqa: F401
    import app.models.run           # noqa: F401
    import app.models.score         # noqa: F401
    from app.database import SessionLocal
    from app.models.taxonomy import Category, Term

    import openpyxl
    workbook_path = REPO / "docs" / "methodology" / "Verity_SASB_Mapping_Signed.xlsx"
    wb = openpyxl.load_workbook(str(workbook_path), data_only=True)
    ws = wb["Industry materiality"]
    industry_norm_to_display: dict[str, str] = {}
    industry_cats: dict[str, set[str]] = defaultdict(set)
    for row in list(ws.iter_rows(values_only=True))[1:]:
        industry_raw = row[0]
        category_raw = row[2]
        if industry_raw and category_raw:
            n = _norm(str(industry_raw))
            industry_cats[n].add(_norm(str(category_raw)))
            industry_norm_to_display.setdefault(n, str(industry_raw).strip())

    db = SessionLocal()
    cats = {c.id: c for c in db.query(Category).all()}
    terms = db.query(Term).order_by(Term.category_id, Term.phrase).all()

    rows: list[dict[str, str]] = []
    for t in terms:
        cat: Category = cats[t.category_id]
        pillar = cat.pillar
        if t.group == "addon":
            component = "Banking"
        elif pillar == "Environmental":
            component = "E"
        elif pillar == "Social":
            component = "S"
        elif pillar == "Governance":
            component = "G"
        elif pillar == "General":
            component = "General"
        else:
            component = pillar

        sasb_primary = t.sasb_category_primary
        sasb_secondary = t.sasb_category_secondary
        sasb_display = ""
        if sasb_primary and sasb_secondary:
            sasb_display = f"{sasb_primary} ({sasb_secondary})"
        elif sasb_primary:
            sasb_display = sasb_primary

        inds_norm = set()
        for cat_label in (sasb_primary, sasb_secondary):
            for n in industries_for_sasb_category(cat_label, industry_cats):
                inds_norm.add(n)
        industries = ", ".join(sorted(industry_norm_to_display[n] for n in inds_norm))

        rows.append({
            "concept": t.phrase,
            "spelling_variants": t.phrase,
            "component": component,
            "sasb_category": sasb_display,
            "industries": industries,
        })

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with OUT_PATH.open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(
            fh,
            fieldnames=["concept", "spelling_variants", "component",
                        "sasb_category", "industries"],
        )
        w.writeheader()
        w.writerows(rows)

    by_component: dict[str, int] = defaultdict(int)
    for r in rows:
        by_component[r["component"]] += 1
    print(f"Wrote {len(rows)} terms to {OUT_PATH.relative_to(REPO)}")
    for comp, n in sorted(by_component.items()):
        print(f"  {comp:<10} {n}")
    db.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
