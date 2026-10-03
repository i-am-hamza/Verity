"""Session 6 scope correction: apply the 60-institution universe.

- Four renames (name + nothing else; institution_id preserved so prior
  reports/documents still link cleanly).
- Five drops marked `active=False` + rank cleared (keeps audit trail —
  prior reports, wayback picks, gap rows all remain readable).
- Rank column reset for the 60 active rows from the new file's `No.`
  column. We null everyone's rank first so the UNIQUE(rank) constraint
  can't collide with an old value during the per-row update loop.

Idempotent: re-running after the first apply converges on the same state.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND))
sys.stdout.reconfigure(encoding="utf-8")

import openpyxl  # noqa: E402

from app.crawler import register_all_mappers  # noqa: E402

register_all_mappers()
from app.database import SessionLocal  # noqa: E402
from app.models.institution import Institution  # noqa: E402

UPDATED_PATH = BACKEND.parent / "data" / "Updated List of Companies.xlsx"
_TICKER_SUFFIX_RX = re.compile(r"\.(SR|KW|BH|OM|AE|QA|DU)$", re.IGNORECASE)


def _norm_ticker(s: object) -> str | None:
    if s is None:
        return None
    s = str(s).strip().upper()
    return _TICKER_SUFFIX_RX.sub("", s)


def _load_updated_rows() -> list[dict]:
    wb = openpyxl.load_workbook(UPDATED_PATH)
    ws = wb["Companies"]
    rows = []
    # Header is row 2 per the file layout; data starts row 3.
    for raw in ws.iter_rows(values_only=True, min_row=3):
        if raw[0] is None:
            continue
        rows.append({
            "rank": int(raw[0]),
            "name": (raw[1] or "").strip(),
            "ticker": _norm_ticker(raw[2]),
            "country": (raw[3] or "").strip(),
            "market_cap": raw[4],
            "industry": (raw[5] or "").strip() if raw[5] else None,
        })
    return rows


def main() -> int:
    if not UPDATED_PATH.exists():
        print(f"ERROR: {UPDATED_PATH} not found")
        return 2

    new_rows = _load_updated_rows()
    if len(new_rows) != 60:
        print(f"ERROR: expected 60 rows in updated xlsx, got {len(new_rows)}")
        return 2
    new_by_ticker = {r["ticker"]: r for r in new_rows}

    db = SessionLocal()
    try:
        inst_rows = db.query(Institution).all()
        print(f"existing institutions: {len(inst_rows)}")

        # Step 1: clear every rank first so unique(rank) can't collide
        # mid-loop when we reassign new values below.
        for inst in inst_rows:
            inst.rank = None
        db.flush()

        matched = 0
        renamed = 0
        deactivated = 0
        reactivated = 0
        unknown: list[tuple[str, str | None]] = []
        for inst in inst_rows:
            key = _norm_ticker(inst.ticker)
            new = new_by_ticker.get(key)
            if new is None:
                # Not in the updated 60 — mark inactive but keep the row.
                if inst.active:
                    inst.active = False
                    deactivated += 1
                continue
            # In the updated 60.
            matched += 1
            if not inst.active:
                inst.active = True
                reactivated += 1
            if inst.name != new["name"]:
                print(f"  rename ticker={key}: {inst.name!r} -> {new['name']!r}")
                inst.name = new["name"]
                renamed += 1
            inst.rank = new["rank"]
            if new.get("industry"):
                inst.industry = new["industry"]

        db.commit()

        # Sanity checks for the user before reporting.
        n_active = db.query(Institution).filter(Institution.active).count()
        n_inactive = db.query(Institution).filter(~Institution.active).count()

        # Make sure every rank in [1..60] is now taken exactly once.
        ranks = sorted(
            r.rank for r in db.query(Institution).filter(Institution.active).all()
            if r.rank is not None
        )
        gap_report = [i for i in range(1, 61) if i not in set(ranks)]
        dup_report = [r for r in set(ranks) if ranks.count(r) > 1]

        print()
        print(f"matched by ticker       : {matched}")
        print(f"renames applied         : {renamed}")
        print(f"deactivated             : {deactivated}")
        print(f"re-activated            : {reactivated}")
        print(f"active total            : {n_active}")
        print(f"inactive total (audit)  : {n_inactive}")
        if gap_report:
            print(f"MISSING RANKS           : {gap_report}")
        if dup_report:
            print(f"DUPLICATE RANKS         : {dup_report}")
        unknown_targets = [t for t in new_by_ticker if t not in {_norm_ticker(i.ticker) for i in inst_rows}]
        if unknown_targets:
            print(f"UPDATED-XLSX TICKERS NOT IN DB: {unknown_targets}")
        return 0
    finally:
        db.close()


if __name__ == "__main__":
    sys.exit(main())
