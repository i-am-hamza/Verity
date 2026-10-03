"""Session 9: rewrite source_documents.file_path and reports.file_path
from Windows-absolute paths like

    E:\\9. Verity\\backend\\storage\\reports\\al-rajhi-bank\\2025_integrated_e66e4adf.pdf

to R2 object keys like

    al-rajhi-bank/2025_integrated_e66e4adf.pdf

Every rewritten row is then validated against R2 via head_object; if the
object doesn't exist, the row is left alone and reported for manual
review. The script is idempotent — paths already in R2-key form pass
through unchanged, and a second run is a no-op.
"""
from __future__ import annotations

import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND))

from dotenv import load_dotenv  # noqa: E402

load_dotenv(BACKEND / ".env")

from sqlalchemy import text  # noqa: E402

from app.database import engine  # noqa: E402
from app.services.storage import (  # noqa: E402
    file_path_to_r2_key,
    pdf_exists,
    r2_enabled,
)


def _normalize_table(table: str) -> tuple[int, int, int]:
    """Return (seen, updated, missing_on_r2)."""
    seen = updated = missing = 0
    with engine.connect() as c:
        rows = c.execute(
            text(f'SELECT id, file_path FROM {table} WHERE file_path IS NOT NULL')
        ).all()
    for row_id, current in rows:
        seen += 1
        new_key = file_path_to_r2_key(current)
        if new_key == current:
            # Already an R2 key.
            if not pdf_exists(new_key):
                missing += 1
                print(f"  {table} id={row_id}  MISSING in R2  key={new_key}")
            continue
        if not pdf_exists(new_key):
            missing += 1
            print(f"  {table} id={row_id}  WOULD-REWRITE but MISSING in R2  "
                  f"key={new_key}  from={current}")
            continue
        with engine.begin() as c:
            c.execute(
                text(f'UPDATE {table} SET file_path = :p WHERE id = :id'),
                {"p": new_key, "id": row_id},
            )
        updated += 1
    return seen, updated, missing


def main() -> int:
    if not r2_enabled():
        print("R2 env vars not set — refusing to normalize.")
        return 2
    print("Normalising file_path -> R2 object key")
    for table in ("source_documents", "reports"):
        seen, updated, missing = _normalize_table(table)
        print(f"  {table:<20} seen={seen:4d}  updated={updated:4d}  "
              f"missing-in-r2={missing:4d}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
