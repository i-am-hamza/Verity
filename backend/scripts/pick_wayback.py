"""One-off: pick best Wayback snapshot per (slug, FY) and write
data/approved_downloads.json. Also retries bank-dhofar and sohar-international-bank
whose CDX calls failed with a timeout last run.
"""
from __future__ import annotations

import json
import re
import sys
import time
from collections import defaultdict
from datetime import date
from pathlib import Path

# Add backend/ to sys.path and set contact email so wayback module works.
import os
os.environ.setdefault("VERITY_CONTACT_EMAIL", "ana.muhandis@protonmail.com")
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.stdout.reconfigure(encoding="utf-8")  # Windows cp1252 safety

from app.crawler.wayback import _cdx_query, _capture_in_publication_window  # noqa: E402

ROOT = Path("E:/9. Verity")
CANDIDATES_MD = ROOT / "docs" / "WAYBACK_CANDIDATES.md"
APPROVED_PATH = ROOT / "data" / "approved_downloads.json"

ANNUAL_RX = re.compile(r"(annual[-_]?report|annualreport|annual-rpt)", re.I)
INTEGRATED_RX = re.compile(r"integrated[-_]?report", re.I)
NEGATIVE_RX = re.compile(
    r"(q[1-3]|quarterly|interim|half[-_]?year|hy[12]|pillar[-_]?3|"
    r"basel|prospectus|proxy|agm|minutes|financial[-_]?statements|"
    r"press[-_]?release|notice|calendar|disclos|dividend|rating)", re.I)
# 4-digit years 2010-2029, not glued to adjacent digits. Used to detect
# a stale PDF being served under a current-looking IR page (e.g. a 2016
# AR captured in 2024 — Wayback timestamp says 2024 but the file is 2016).
_URL_YEAR_RX = re.compile(r"(?<!\d)(20[12]\d)(?!\d)")


def _has_wrong_year(url: str, target_fy: int) -> bool:
    """True if the URL contains at least one 4-digit year 20YY and NONE
    of them equals `target_fy`. A URL with no year-looking tokens
    returns False (ambiguous — we can't reject on URL text alone).
    """
    years = {int(y) for y in _URL_YEAR_RX.findall(url)}
    return bool(years) and target_fy not in years


def _parse_md(md: str) -> list[tuple[str, int, str, str, str]]:
    """Pull (slug, FY, capture_date, original_url, snapshot_url) tuples
    from the markdown table."""
    rows: list[tuple[str, int, str, str, str]] = []
    for line in md.splitlines():
        if not line.startswith("| `"):
            continue
        parts = [p.strip() for p in line.strip().strip("|").split("|")]
        if len(parts) < 5:
            continue
        slug = parts[0].strip("`")
        try:
            fy = int(parts[1])
        except ValueError:
            continue
        ts = parts[2]
        # The URL cells are markdown links; strip to the raw URL.
        orig_m = re.search(r"\(([^)]+)\)", parts[3])
        snap_m = re.search(r"\(([^)]+)\)", parts[4])
        if not orig_m or not snap_m:
            continue
        rows.append((slug, fy, ts, orig_m.group(1).replace("%7C", "|"),
                     snap_m.group(1).replace("%7C", "|")))
    return rows


def _score(url: str, ts: str, fy: int) -> int:
    """Rank candidates. Higher = better."""
    s = 0
    if _capture_in_publication_window(ts, fy):
        s += 100
    if ANNUAL_RX.search(url):
        s += 60
    elif INTEGRATED_RX.search(url):
        s += 50
    if str(fy) in url:
        s += 20
    if NEGATIVE_RX.search(url):
        s -= 60
    # Favor later captures within tier (tiebreaker as big-int suffix).
    try:
        s = s * 10**15 + int(ts[:14] or "0")
    except ValueError:
        pass
    return s


def _retry_missing(gaps_slug_fys: set[tuple[str, int]], already_covered: set[tuple[str, int]]) -> list[tuple[str, int, str, str, str]]:
    """Direct CDX query for bank-dhofar + sohar-international-bank, which
    timed out in the main run."""
    retry_hosts = {
        "bank-dhofar": "https://www.bankdhofar.com/investor-relations/financial-reports/",
        "sohar-international-bank": "https://www.sib.om/investor-relations",
    }
    out: list[tuple[str, int, str, str, str]] = []
    for slug, url in retry_hosts.items():
        time.sleep(2.0)
        try:
            rows = _cdx_query(url, timeout=60)
        except Exception as exc:
            print(f"  retry CDX for {slug} failed: {exc}")
            continue
        print(f"  retry CDX for {slug}: {len(rows)} rows")
        for r in rows:
            orig = r.get("original") or ""
            ts = r.get("timestamp") or ""
            for fy in range(2021, 2026):
                if (slug, fy) not in gaps_slug_fys:
                    continue
                if str(fy) in orig or str(fy) in ts or _capture_in_publication_window(ts, fy):
                    snap = f"https://web.archive.org/web/{ts}/{orig}"
                    out.append((slug, fy, ts, orig, snap))
    return out


def main() -> None:
    md = CANDIDATES_MD.read_text(encoding="utf-8")
    rows = _parse_md(md)
    print(f"candidates parsed from markdown: {len(rows)}")

    # Load the real gap set from DB for the retry targets.
    import importlib
    _ = importlib.import_module("app.models.institution")
    _ = importlib.import_module("app.models.provenance")
    from app.database import engine
    from sqlalchemy import text
    with engine.connect() as c:
        gaps = {(r[0], r[1]) for r in c.execute(text(
            "SELECT i.slug, g.fiscal_year FROM gaps g "
            "JOIN institutions i ON i.id=g.institution_id "
            "WHERE i.wave='financial'"))}
    print(f"financial-wave gaps: {len(gaps)}")

    # Retry the two timeout-victim hosts.
    print("retrying bank-dhofar + sohar-international-bank CDX...")
    retry_rows = _retry_missing(gaps, set())
    rows.extend(retry_rows)
    print(f"candidates after retry: {len(rows)}")

    # Group by (slug, FY) and keep best per group.
    by_key: dict[tuple[str, int], list[tuple[str, int, str, str, str]]] = defaultdict(list)
    for r in rows:
        by_key[(r[0], r[1])].append(r)

    picks: list[dict] = []
    rejected_wrong_year = 0
    for key, cands in by_key.items():
        if key not in gaps:
            continue
        fy = key[1]
        # Fix (a): drop candidates whose URL carries year tokens that
        # don't include the gap FY — those are stale PDFs from a prior
        # year still being served (and captured) at the current site.
        kept = [c for c in cands if not _has_wrong_year(c[3], fy)]
        rejected_wrong_year += len(cands) - len(kept)
        if not kept:
            continue
        best = max(kept, key=lambda r: _score(r[3], r[2], r[1]))
        slug, _, ts, orig, snap = best
        picks.append({
            "institution_slug": slug,
            "fiscal_year": fy,
            "source_url": snap,
            "note": f"wayback pick ts={ts} orig={orig}",
        })
    print(f"candidates dropped by wrong-year filter: {rejected_wrong_year}")

    # Deterministic ordering.
    picks.sort(key=lambda p: (p["institution_slug"], p["fiscal_year"]))
    APPROVED_PATH.write_text(json.dumps(picks, indent=2), encoding="utf-8")
    print(f"wrote {len(picks)} picks to {APPROVED_PATH}")

    # Report any gaps that got zero candidates.
    picked_keys = {(p["institution_slug"], p["fiscal_year"]) for p in picks}
    still_zero = sorted(gaps - picked_keys)
    print(f"gaps with zero candidate even after retry: {len(still_zero)}")
    for g in still_zero:
        print(f"  {g[0]} FY{g[1]}")


if __name__ == "__main__":
    main()
