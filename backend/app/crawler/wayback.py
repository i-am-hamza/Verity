"""Tier 3: Wayback Machine CDX candidate lister.

Public, no account. Rate: 1 request per second (we take 2s to be safe,
same budget as our normal politeness floor).

Behaviour:
- For each `Gap` row with an institution that has an ir_url (or
  exchange_company_url) in data/ir_sources.json, query the CDX API for
  captures whose `original` URL starts with that root.
- Emit docs/WAYBACK_CANDIDATES.md listing capture_date, original URL,
  snapshot URL. The caller (human) copies entries into
  data/approved_downloads.json; nothing is downloaded here.
"""
from __future__ import annotations

import json
import logging
import time
from dataclasses import dataclass
from datetime import UTC, date, datetime
from pathlib import Path
from urllib.parse import urlparse

import requests

from app.crawler.config import (
    WAYBACK_CANDIDATES_PATH,
    make_user_agent,
)
from app.models.institution import Institution
from app.models.provenance import Gap

log = logging.getLogger("verity.crawler.wayback")

CDX_URL = "https://web.archive.org/cdx/search/cdx"
# Match PDF captures first; otherwise capture pages that could lead to a report.
PDF_FILTER = "mimetype:application/pdf"


@dataclass
class WaybackCandidate:
    institution_slug: str
    fiscal_year: int
    original_url: str
    capture_date: str  # YYYYMMDDHHMMSS from CDX
    snapshot_url: str


def _cdx_query(url_prefix: str, timeout: int = 30) -> list[dict]:
    """Query CDX for PDF captures anywhere on the host that `url_prefix`
    points to. We used to use the full IR URL as a prefix match, but most
    banks host their report PDFs on a completely different path from the
    IR landing page (`/-/media/...`, `/content/dam/...`, etc.), so a
    prefix match returned zero. Switching to domain-match (host + wildcard)
    sweeps the whole hostname and lets the per-FY filter downstream do
    the narrowing. CDX caps responses with `limit`; we raise it since the
    broader query returns more rows per host.
    """
    host = urlparse(url_prefix).hostname or ""
    if not host:
        return []
    params = {
        "url": f"{host}/*",
        "output": "json",
        "filter": PDF_FILTER,
        "collapse": "digest",
        "limit": "1000",
    }
    headers = {"User-Agent": make_user_agent()}
    resp = requests.get(CDX_URL, params=params, headers=headers, timeout=timeout)
    resp.raise_for_status()
    rows = resp.json()
    if not rows or len(rows) < 2:
        return []
    header, *data = rows
    return [dict(zip(header, r, strict=False)) for r in data]


def gather_wayback_candidates(gaps: list[Gap], institutions: dict[int, Institution],
                              ir_sources: dict[str, dict]) -> list[WaybackCandidate]:
    out: list[WaybackCandidate] = []
    # Dedupe queries by institution: one CDX call per institution per source
    # URL, not per gap year — the result is filtered to year.
    queried: dict[tuple[str, str], list[dict]] = {}
    for gap in gaps:
        inst = institutions.get(gap.institution_id)
        if inst is None:
            continue
        src_info = ir_sources.get(inst.slug) or {}
        candidate_roots: list[tuple[str, str]] = []
        if src_info.get("ir_url"):
            candidate_roots.append((inst.slug, src_info["ir_url"]))
        if src_info.get("exchange_company_url"):
            candidate_roots.append((inst.slug, src_info["exchange_company_url"]))

        for slug, root in candidate_roots:
            key = (slug, root)
            if key not in queried:
                time.sleep(2.0)  # 1 req/sec policy — err safe
                try:
                    queried[key] = _cdx_query(root)
                except (requests.RequestException, json.JSONDecodeError) as exc:
                    log.warning("Wayback CDX failed for %s: %s", root, exc)
                    queried[key] = []

            for row in queried[key]:
                orig = row.get("original") or ""
                ts = row.get("timestamp") or ""
                # Accept the capture if EITHER the fiscal-year string shows
                # up in the URL / timestamp (old behaviour — handles
                # "annual-report-2023.pdf"), OR the capture date falls in
                # the typical publication window for that FY. The window
                # catches sites that host "latest annual report" at a
                # year-less path (`.../annual-report.pdf`) and overwrite
                # it each year — those were silently dropped before.
                yr = str(gap.fiscal_year)
                if (yr in orig or yr in ts
                        or _capture_in_publication_window(ts, gap.fiscal_year)):
                    snap = f"https://web.archive.org/web/{ts}id_/{orig}"
                    out.append(WaybackCandidate(
                        institution_slug=inst.slug, fiscal_year=gap.fiscal_year,
                        original_url=orig, capture_date=ts, snapshot_url=snap,
                    ))
    return out


def _capture_in_publication_window(ts: str, fy: int) -> bool:
    """A capture timestamped `ts` (CDX YYYYMMDDHHMMSS) belongs to fiscal
    year `fy` if the snapshot date is 2-7 months after FY-end. Assumes
    FY ends 31 December (true for the vast majority of ME listed
    companies on calendar-year reporting). Inclusive at both ends.
    """
    try:
        y, m, d = int(ts[:4]), int(ts[4:6]), int(ts[6:8])
        captured = date(y, m, d)
    except (ValueError, TypeError):
        return False
    window_start = date(fy + 1, 3, 1)   # FY-end + 2 months
    window_end = date(fy + 1, 7, 31)    # FY-end + 7 months
    return window_start <= captured <= window_end


def write_wayback_candidates(cands: list[WaybackCandidate]) -> Path:
    WAYBACK_CANDIDATES_PATH.parent.mkdir(parents=True, exist_ok=True)
    lines: list[str] = []
    lines.append("# Wayback Machine candidates")
    lines.append("")
    lines.append(f"Generated {datetime.now(UTC).isoformat(timespec='seconds')} via `python -m app.cli gaps wayback`.")
    lines.append("")
    lines.append("This tool lists captures. **It does not download anything.** Review each entry; if "
                 "it's a legitimate match, copy the row's details into `data/approved_downloads.json` "
                 "and run `python -m app.cli ingest-approved`. That path downloads with `source=wayback` "
                 "and goes through the same validation + manifest as a live crawl.")
    lines.append("")
    if not cands:
        lines.append("_No candidates returned — the gaps either have no CDX hits in the filter window, "
                     "or no IR / exchange URL is on file to query._")
    else:
        lines.append("| institution | FY | capture date | original URL | snapshot URL |")
        lines.append("|---|---|---|---|---|")
        for c in cands:
            # Markdown table escaping — URLs may contain |
            orig = c.original_url.replace("|", "%7C")
            snap = c.snapshot_url.replace("|", "%7C")
            lines.append(
                f"| `{c.institution_slug}` | {c.fiscal_year} | {c.capture_date} | "
                f"[original]({orig}) | [snapshot]({snap}) |"
            )

    WAYBACK_CANDIDATES_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return WAYBACK_CANDIDATES_PATH


def run_wayback(db) -> Path:
    from app.crawler.config import IR_SOURCES_PATH
    gaps = db.query(Gap).all()
    inst_map = {i.id: i for i in db.query(Institution).all()}
    ir_sources = {r["slug"]: r for r in json.loads(IR_SOURCES_PATH.read_text(encoding="utf-8"))}
    cands = gather_wayback_candidates(gaps, inst_map, ir_sources)
    return write_wayback_candidates(cands)
