"""Import data/alafco_gaps.json into the gaps table.

Idempotent: the gaps table has a unique constraint on
(institution_id, fiscal_year), so a row's existing values are updated
rather than duplicated on re-run.

Why this exists as its own loader rather than being read by Session 4
directly: `data/alafco_gaps.json` is a staging artefact from the
Session 3b IR review, not a long-lived input. Importing it into the gaps
table makes ALAFCO look like any other gap to the pipeline — Session 4's
Wayback helper reads from the gaps table (per the provenance model in
app/models/provenance.py) and doesn't need to know about this file.

Run from backend/:
    python -m seed.import_alafco_gaps
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
from app.models.institution import Institution
from app.models.provenance import Gap, GapReason

REPO_ROOT = Path(__file__).resolve().parents[2]
GAPS_FILE = REPO_ROOT / "data" / "alafco_gaps.json"


def import_rows() -> dict[str, int]:
    rows = json.loads(GAPS_FILE.read_text(encoding="utf-8"))
    created, updated = 0, 0
    db = SessionLocal()
    try:
        for row in rows:
            inst = db.query(Institution).filter(
                Institution.slug == row["institution_slug"]
            ).one_or_none()
            if inst is None:
                raise RuntimeError(
                    f"institution slug {row['institution_slug']!r} not in DB — "
                    "run `python -m seed.load_institutions` first"
                )

            reason = GapReason(row["reason"])
            existing = db.query(Gap).filter(
                Gap.institution_id == inst.id,
                Gap.fiscal_year == row["fiscal_year"],
            ).one_or_none()

            fields = {
                "institution_id": inst.id,
                "fiscal_year": row["fiscal_year"],
                "reason": reason,
                "detail": row.get("detail"),
                "tier_tried": row.get("tier_tried"),
                "next_action": row.get("next_action"),
            }
            if existing:
                for k, v in fields.items():
                    setattr(existing, k, v)
                updated += 1
            else:
                db.add(Gap(**fields))
                created += 1

        db.commit()
    finally:
        db.close()
    return {"created": created, "updated": updated, "total": len(rows)}


def main() -> None:
    summary = import_rows()
    print(
        f"ALAFCO gap rows: {summary['total']} source rows -> "
        f"{summary['created']} created, {summary['updated']} updated"
    )

    # Print the final state so the result is auditable from the console.
    db = SessionLocal()
    try:
        inst = db.query(Institution).filter(
            Institution.slug == "alafco-aviation-lease-and-finance-company"
        ).one()
        gaps = (
            db.query(Gap)
            .filter(Gap.institution_id == inst.id)
            .order_by(Gap.fiscal_year)
            .all()
        )
        print(f"\nGap table state for ALAFCO (institution_id={inst.id}):")
        for g in gaps:
            print(
                f"  FY{g.fiscal_year}  reason={g.reason.value}  "
                f"tier_tried={g.tier_tried!r}  next_action={g.next_action!r}"
            )
    finally:
        db.close()


if __name__ == "__main__":
    main()
