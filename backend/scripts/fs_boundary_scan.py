"""
fs_boundary_scan.py  –  Classify the 60 FS_BOUNDARY_NOT_FOUND company-years.

For each PDF:
  1. Try every known boundary pattern (auditor, balance sheet, FS title …)
  2. Check context around the first "total assets" line (FS vs highlights)
  3. Look for any FS-adjacent text at all

Output: two lists
  (a) truly no FS in the PDF
  (b) FS present but current pattern missed → what text IS there
"""
from __future__ import annotations
import re, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

from pathlib import Path
BACKEND = Path(__file__).resolve().parent.parent
import sys; sys.path.insert(0, str(BACKEND))
from dotenv import load_dotenv; load_dotenv(BACKEND / ".env")

import csv
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock
import pymupdf

import app.models.institution, app.models.provenance  # noqa: F401
import app.models.report, app.models.score, app.models.run  # noqa: F401
import app.models.taxonomy, app.models.review  # noqa: F401
from app.database import SessionLocal
from app.models.provenance import SourceDocument
from app.models.institution import Institution
from sqlalchemy import select
from app.services.storage import read_pdf_bytes

# ── target cases ──────────────────────────────────────────────────────────────
CSV_PATH = BACKEND.parent / "docs" / "exports" / "financials_extracted.csv"
with open(CSV_PATH, newline="", encoding="utf-8") as f:
    all_rows = list(csv.DictReader(f))

TARGETS = [
    (r["slug"], int(r["fiscal_year"]))
    for r in all_rows
    if "FS_BOUNDARY_NOT_FOUND" in (r.get("flags") or "")
]
print(f"Targets: {len(TARGETS)} company-years")

# ── load DB manifest ──────────────────────────────────────────────────────────
db = SessionLocal()
rows = db.execute(
    select(
        Institution.slug, SourceDocument.fiscal_year, SourceDocument.file_path,
    )
    .join(SourceDocument, SourceDocument.institution_id == Institution.id)
    .where(Institution.active.is_(True))
    .where(SourceDocument.superseded_by_id.is_(None))
).all()
db.close()
by_key: dict[tuple[str, int], str] = {(s, y): fp for s, y, fp in rows}

# ── patterns ──────────────────────────────────────────────────────────────────
# Current FS-boundary patterns (same as extract_financials.py)
CURRENT = [
    re.compile(r"independent\s+auditors?[''\s]*report", re.I),
    re.compile(r"report\s+of\s+the\s+independent\s+auditors?", re.I),
    re.compile(r"(?:consolidated\s+)?statement\s+of\s+financial\s+position", re.I),
    re.compile(r"(?:consolidated\s+)?statement\s+of\s+comprehensive\s+income", re.I),
    re.compile(r"(?:consolidated\s+)?statement\s+of\s+cash\s+flows", re.I),
    re.compile(r"(?:consolidated\s+)?statement\s+of\s+changes\s+in\s+equity", re.I),
    re.compile(r"notes\s+to\s+the\s+(?:consolidated\s+)?financial\s+statements", re.I),
    # Split-line variant already in the code — check it too
    re.compile(r"^auditors?\W*report\s*$", re.I),
    re.compile(r"^independent\s*$", re.I),
]
# NEW candidate patterns to try
CANDIDATES = [
    ("external_auditor",       re.compile(r"external\s+auditors?\W*report", re.I)),
    ("report_of_ext_auditor",  re.compile(r"report\s+of\s+(?:the\s+)?external\s+auditors?", re.I)),
    ("balance_sheet",          re.compile(r"\bbalance\s+sheet\b", re.I)),
    ("financial_statements_hdr",re.compile(r"^financial\s+statements\s*$", re.I)),
    ("fs_section_hdr",         re.compile(r"^(?:the\s+)?financial\s+statements\b", re.I)),
    ("statutory_auditor",      re.compile(r"statutory\s+auditors?\W*report", re.I)),
    ("consolidated_bs",        re.compile(r"consolidated\s+balance\s+sheet", re.I)),
    ("auditors_report_bare",   re.compile(r"\bauditors?\s+report\b", re.I)),
    ("board_auditor_report",   re.compile(r"board\s+of\s+(?:directors?|auditors?)\W*report", re.I)),
]

_NUM = re.compile(r"\b\d[\d,.\s]{3,}\b")
_TA  = re.compile(r"total\s+assets?\b", re.I)
_NP  = re.compile(r"net\s+(profit|income)\s+for\s+the\s+(year|period)", re.I)
_TE  = re.compile(r"total\s+(equity|liabilities)\b", re.I)
_LIGMAP = str.maketrans({"ﬀ":"ff","ﬁ":"fi","ﬂ":"fl","ﬃ":"ffi","ﬄ":"ffl","ﬅ":"st","ﬆ":"st"})

# ── scan one PDF ──────────────────────────────────────────────────────────────

def _page_text(pdf: pymupdf.Document, i: int) -> str:
    try:
        return (pdf[i].get_text("text") or "").translate(_LIGMAP)
    except Exception:
        return ""


def scan_pdf(slug: str, fy: int, r2_key: str) -> dict:
    try:
        body = read_pdf_bytes(r2_key)
    except Exception as e:
        return {"slug": slug, "fy": fy, "error": str(e)}

    try:
        pdf = pymupdf.open(stream=body, filetype="pdf")
    except Exception as e:
        return {"slug": slug, "fy": fy, "error": f"open: {e}"}

    n_pages = pdf.page_count
    current_hits: list[tuple[int, str]] = []   # (page, pattern_name)
    candidate_hits: list[tuple[int, str, str]] = []  # (page, name, snippet)
    ta_pages: list[tuple[int, str]] = []       # (page, context snippet)
    np_pages: list[tuple[int, str]] = []
    other_fs_pages: list[int] = []

    # Collect all page texts first (avoid repeated R2 calls – we already have bytes)
    all_lines: list[tuple[int, str]] = []  # (page_1based, line)
    for pg in range(n_pages):
        text = _page_text(pdf, pg)
        for raw_line in text.split("\n"):
            ln = raw_line.strip()
            if ln:
                all_lines.append((pg + 1, ln))

    pdf.close()

    # Check current patterns against every line
    for page_no, line in all_lines:
        for pat in CURRENT:
            if pat.search(line):
                current_hits.append((page_no, pat.pattern[:60]))
                break

    # Check candidate patterns
    for name, pat in CANDIDATES:
        for page_no, line in all_lines:
            if pat.search(line):
                snippet = line[:80]
                candidate_hits.append((page_no, name, snippet))
                break  # first occurrence only

    # Find "Total assets" occurrences
    for page_no, line in all_lines:
        if _TA.search(line):
            # Grab context: this line + next 3
            idx = all_lines.index((page_no, line))
            ctx_lines = all_lines[idx:idx+4]
            ctx_text = " | ".join(l for _, l in ctx_lines)
            # Is there a real number?
            if _NUM.search(ctx_text):
                ta_pages.append((page_no, ctx_text[:150]))
            # Is this a FS context? Check if same page has TE or TL
            page_lines = [l for p, l in all_lines if p == page_no]
            page_text_joined = " ".join(page_lines)
            if _TE.search(page_text_joined) and _NUM.search(page_text_joined):
                if page_no not in other_fs_pages:
                    other_fs_pages.append(page_no)
            break  # first TA occurrence only

    # Find "net profit for the year" occurrences
    for page_no, line in all_lines:
        if _NP.search(line):
            idx = all_lines.index((page_no, line))
            ctx_lines = all_lines[idx:idx+4]
            ctx_text = " | ".join(l for _, l in ctx_lines)
            if _NUM.search(ctx_text):
                np_pages.append((page_no, ctx_text[:120]))
            break

    return {
        "slug": slug,
        "fy": fy,
        "n_pages": n_pages,
        "current_hits": current_hits[:5],       # first 5 matches of current patterns
        "candidate_hits": candidate_hits,
        "ta_pages": ta_pages[:3],
        "np_pages": np_pages[:2],
        "other_fs_pages": other_fs_pages[:3],
        "error": None,
    }


# ── run with threads ──────────────────────────────────────────────────────────
print_lock = Lock()
results: list[dict] = []
results_lock = Lock()

work = [(slug, fy, by_key.get((slug, fy), "")) for slug, fy in TARGETS if by_key.get((slug, fy))]
missing_key = [(s, y) for s, y in TARGETS if not by_key.get((s, y))]

print(f"  (missing R2 key: {len(missing_key)})")

with ThreadPoolExecutor(max_workers=12) as pool:
    futures = {pool.submit(scan_pdf, s, y, k): (s, y) for s, y, k in work}
    done = 0
    for fut in as_completed(futures):
        r = fut.result()
        with results_lock:
            results.append(r)
        done += 1
        if done % 10 == 0:
            with print_lock:
                print(f"  ... {done}/{len(work)} done", flush=True)

results.sort(key=lambda x: (x["slug"], x["fy"]))

# ── classify and report ───────────────────────────────────────────────────────
truly_no_fs: list[tuple[str, int, str]] = []   # (slug, fy, reason)
has_fs: list[tuple[str, int, str, list]] = []  # (slug, fy, what_found, candidate_hits)

SEP = "=" * 90

print(f"\n{SEP}")
print("DETAILED SCAN RESULTS")
print(SEP)

for r in results:
    if r.get("error"):
        print(f"\n{r['slug']} FY{r['fy']}: ERROR {r['error']}")
        truly_no_fs.append((r["slug"], r["fy"], f"error: {r['error']}"))
        continue

    current = r["current_hits"]
    cands   = r["candidate_hits"]
    ta      = r["ta_pages"]
    np_     = r["np_pages"]
    fs_pg   = r["other_fs_pages"]

    has_any = bool(current or cands or fs_pg or ta or np_)

    # Classify
    if current:
        # Current patterns DO fire — shouldn't be in this list? Edge case.
        reason = f"CURRENT_PATTERN_FOUND (p.{current[0][0]}): {current[0][1]}"
        has_fs.append((r["slug"], r["fy"], reason, cands))
    elif cands:
        reason = f"CANDIDATE_FOUND: {', '.join(f'{n}@p{p}' for p,n,_ in cands[:3])}"
        has_fs.append((r["slug"], r["fy"], reason, cands))
    elif fs_pg:
        reason = f"FS_PAGE_INFERRED (total_assets + liabilities on same page): p.{fs_pg[0]}"
        has_fs.append((r["slug"], r["fy"], reason, cands))
    elif ta and np_:
        reason = f"BOTH_TA_AND_NP_FOUND: TA@p{ta[0][0]}, NP@p{np_[0][0]}"
        has_fs.append((r["slug"], r["fy"], reason, cands))
    else:
        notes = []
        if ta:   notes.append(f"TA_only@p{ta[0][0]}")
        if np_:  notes.append(f"NP_only@p{np_[0][0]}")
        reason = "NO_FS_CONTENT" + (f" ({', '.join(notes)})" if notes else "")
        truly_no_fs.append((r["slug"], r["fy"], reason))

    # Detailed print
    print(f"\n{'─'*70}")
    print(f"  {r['slug']}  FY{r['fy']}  ({r['n_pages']} pages)")
    if current:
        for pg, pat in current[:2]:
            print(f"    CURRENT MATCH  p.{pg:<4}  {pat}")
    for pg, name, snip in cands[:4]:
        print(f"    CANDIDATE  {name:<30}  p.{pg:<4}  {snip[:60]}")
    for pg, ctx in (ta or [])[:2]:
        print(f"    TOTAL_ASSETS  p.{pg:<4}  {ctx[:80]}")
    for pg, ctx in (np_ or [])[:1]:
        print(f"    NET_PROFIT    p.{pg:<4}  {ctx[:80]}")
    if fs_pg:
        print(f"    FS_INFERRED   pages: {fs_pg}")

# ── Summary tables ─────────────────────────────────────────────────────────────
print(f"\n{SEP}")
print(f"(a) TRULY NO FINANCIAL STATEMENTS IN PDF  ({len(truly_no_fs)} cases)")
print(SEP)
for slug, fy, reason in sorted(truly_no_fs):
    print(f"  {slug:<55}  FY{fy}  {reason}")

print(f"\n{SEP}")
print(f"(b) FS PRESENT BUT BOUNDARY MISSED  ({len(has_fs)} cases)")
print(SEP)
# Group candidate hits to find the most common new patterns
from collections import Counter
cand_counter: Counter = Counter()
for _, _, _, cands in has_fs:
    for _, name, _ in cands:
        cand_counter[name] += 1

print(f"  Candidate patterns by frequency:")
for name, cnt in cand_counter.most_common():
    print(f"    {name:<35} {cnt}")

print()
for slug, fy, reason, cands in sorted(has_fs, key=lambda x: x[0]):
    cand_str = ", ".join(f"{n}@p{p}" for p,n,_ in cands[:2])
    print(f"  {slug:<55}  FY{fy}  {reason[:60]}")
