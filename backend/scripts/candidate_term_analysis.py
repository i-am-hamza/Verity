"""
Phase 2: Candidate-term evidence.

Run from backend/ with the venv active:
    python scripts/candidate_term_analysis.py

READ-ONLY: fetches PDFs from R2, re-runs extraction + cleaning + matching
with the candidate terms, collects statistics and sample sentences.
No DB writes. Outputs written to docs/term-evidence/.
"""
from __future__ import annotations

import os
import random
import re
import sys
import threading
import time
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

BACKEND = Path(__file__).resolve().parent.parent
REPO_ROOT = BACKEND.parent
sys.path.insert(0, str(BACKEND))

from dotenv import load_dotenv  # noqa: E402

load_dotenv(BACKEND / ".env")

# ── Candidate terms ────────────────────────────────────────────────────────────
# (phrase, sasb_category, lemma_based)
# lemma_based=True  → LEMMA attr (handles inflections: "spills", "spilled"…)
# lemma_based=False → LOWER attr (case-insensitive exact: acronyms, proper names)
CANDIDATES: list[tuple[str, str, bool]] = [
    # Air Quality
    ("air quality",              "Air Quality", True),
    ("air emissions",            "Air Quality", True),
    ("air pollution",            "Air Quality", True),
    ("dust emissions",           "Air Quality", True),
    ("particulate matter",       "Air Quality", True),
    ("nitrogen oxides",          "Air Quality", True),
    ("sulphur dioxide",          "Air Quality", True),
    ("NOx",                      "Air Quality", False),
    ("SOx",                      "Air Quality", False),
    ("flaring",                  "Air Quality", True),
    ("volatile organic compounds", "Air Quality", True),
    # Critical Incident Risk Management
    ("process safety",            "Critical Incident Risk Management", True),
    ("asset integrity",           "Critical Incident Risk Management", True),
    ("emergency preparedness",    "Critical Incident Risk Management", True),
    ("emergency response",        "Critical Incident Risk Management", True),
    ("major accident",            "Critical Incident Risk Management", True),
    ("loss of containment",       "Critical Incident Risk Management", True),
    ("spill",                     "Critical Incident Risk Management", True),
    ("flight safety",             "Critical Incident Risk Management", True),
    ("safety management system",  "Critical Incident Risk Management", True),
    # Product Quality & Safety
    ("food safety",    "Product Quality & Safety", True),
    ("product safety", "Product Quality & Safety", True),
    ("patient safety", "Product Quality & Safety", True),
    ("quality of care","Product Quality & Safety", True),
    ("product recall", "Product Quality & Safety", True),
    # Customer Welfare
    ("nutrition",         "Customer Welfare", True),
    ("healthy products",  "Customer Welfare", True),
    ("sugar reduction",   "Customer Welfare", True),
    ("salt reduction",    "Customer Welfare", True),
    # Product Design & Lifecycle Management
    ("green building",        "Product Design & Lifecycle Management", True),
    ("LEED",                  "Product Design & Lifecycle Management", False),
    ("Estidama",              "Product Design & Lifecycle Management", False),
    ("Mostadam",              "Product Design & Lifecycle Management", False),
    ("e-waste",               "Product Design & Lifecycle Management", False),
    ("sustainable packaging", "Product Design & Lifecycle Management", True),
    ("product stewardship",   "Product Design & Lifecycle Management", True),
    # Materials Sourcing & Efficiency
    ("responsible sourcing",  "Materials Sourcing & Efficiency", True),
    ("recycled content",      "Materials Sourcing & Efficiency", True),
    ("circular economy",      "circular economy / Materials Sourcing & Efficiency", True),
    # Competitive Behavior
    ("anti-competitive", "Competitive Behavior", False),
    ("competition law",  "Competitive Behavior", True),
    ("antitrust",        "Competitive Behavior", True),
    ("net neutrality",   "Competitive Behavior", True),
    # Management of the Legal & Regulatory Environment
    ("lobbying",               "Management of the Legal & Regulatory Environment", True),
    ("public policy",          "Management of the Legal & Regulatory Environment", True),
    ("political contribution", "Management of the Legal & Regulatory Environment", True),
    # Systemic Risk Management
    ("stress testing",    "Systemic Risk Management", True),
    ("systemic risk",     "Systemic Risk Management", True),
    ("network resilience","Systemic Risk Management", True),
    ("business continuity","Systemic Risk Management", True),
    # GCC check (no SASB category)
    ("green sukuk", "GCC Check (no SASB category)", True),
]

SAMPLE_SEED = 20261006
SAMPLE_N    = 20
FREQ_THRESHOLD = 10.0  # PASS if pct_material >= this

# ── Industry materiality: SASB category → set of SASB industries ─────────────
# Built from docs/methodology/Verity_SASB_Mapping_Signed.xlsx
# "Industry materiality" sheet.  Normalise names for comparison.
def _norm(s: str) -> str:
    """Lowercase + collapse non-alphanumeric to space for fuzzy matching."""
    return re.sub(r"[^a-z0-9]+", " ", s.lower()).strip()


def load_materiality(workbook_path: Path) -> tuple[
    dict[str, str],          # company name -> sasb_industry (normalised)
    dict[str, set[str]],     # normed_category -> set of normed industries
]:
    import openpyxl
    wb = openpyxl.load_workbook(str(workbook_path), data_only=True)

    # Company industries: col B = company name, col H = SASB industry
    ws_co = wb["Company industries"]
    name_to_industry: dict[str, str] = {}
    for row in list(ws_co.iter_rows(values_only=True))[1:]:
        company_name = row[1]
        sasb_industry = row[7]  # column H (0-indexed col 7)
        if company_name and sasb_industry:
            name_to_industry[str(company_name).strip()] = _norm(str(sasb_industry))

    # Industry materiality: col A = SASB industry, col C = SASB category (General)
    ws_mat = wb["Industry materiality"]
    cat_industries: dict[str, set[str]] = defaultdict(set)
    for row in list(ws_mat.iter_rows(values_only=True))[1:]:
        industry = row[0]
        category = row[2]
        if industry and category:
            cat_industries[_norm(str(category))].add(_norm(str(industry)))

    return name_to_industry, dict(cat_industries)


# ── DB query ──────────────────────────────────────────────────────────────────

def load_all_docs(db_url: str) -> list[dict]:
    """Return all eligible source_documents (auto_ok, annual/integrated, not superseded).

    Does NOT join with reports — that table may be empty. latin_word_count is
    initialised to 0 and populated during process_document.
    """
    import psycopg
    conn = psycopg.connect(db_url)
    cur = conn.cursor()
    cur.execute("""
        SELECT sd.id, sd.file_path, sd.fiscal_year,
               i.slug, i.name, i.industry
        FROM source_documents sd
        JOIN institutions i ON i.id = sd.institution_id
        WHERE i.active = true
          AND sd.review_status = 'auto_ok'
          AND sd.superseded_by_id IS NULL
          AND sd.report_type IN ('annual', 'integrated')
        ORDER BY i.slug, sd.fiscal_year
    """)
    rows = cur.fetchall()
    conn.close()
    return [
        dict(
            id=sd_id,
            file_path=file_path,
            fiscal_year=fy,
            slug=slug,
            name=name,
            industry=_norm(str(industry)) if industry else "",
            latin_word_count=0,
        )
        for sd_id, file_path, fy, slug, name, industry in rows
    ]


# ── Term class for TaxonomyMatcher ────────────────────────────────────────────

class _CandidateTerm:
    __slots__ = ("category_id", "category_weight", "id", "lemma_based", "phrase", "weight")
    def __init__(self, tid: int, phrase: str, lemma_based: bool) -> None:
        self.id           = tid
        self.phrase       = phrase
        self.lemma_based  = lemma_based
        self.weight       = 1.0
        self.category_id  = 0
        self.category_weight = 1.0


# ── Per-document processing ────────────────────────────────────────────────────

@dataclass
class HitRow:
    term_phrase: str
    sasb_category: str
    slug: str
    company_name: str
    fiscal_year: int
    industry: str
    page_number: int
    sentence: str


_MAX_PAGE_CHARS = 20_000  # guard against pathological pages slowing spaCy
_DOC_TIMEOUT_SECS = 300  # skip documents that take more than 5 minutes


def process_document(
    doc: dict,
    matcher,  # TaxonomyMatcher
    id_to_phrase: dict[int, str],
    id_to_cat: dict[int, str],
    cfg,
) -> tuple[list[HitRow], int]:
    """Returns (hits, latin_word_count).

    latin_word_count is counted from cleaned pages (FS and ToC excluded),
    matching the scoring pipeline's denominator exactly.
    """
    from app.services.pdf_extraction import PageText, count_words, extract_pdf_pages
    from app.services.storage import read_pdf_bytes
    from app.services.text_processing import segment_sentences
    from app.services.text_quality import apply_text_quality

    try:
        pdf_bytes = read_pdf_bytes(doc["file_path"])
    except Exception as exc:
        print(f"  SKIP {doc['slug']} FY{doc['fiscal_year']}: fetch failed: {exc}")
        return [], 0

    try:
        pages = extract_pdf_pages(pdf_bytes)
    except Exception as exc:
        print(f"  SKIP {doc['slug']} FY{doc['fiscal_year']}: extract failed: {exc}")
        return [], 0

    try:
        cleaned = apply_text_quality(pages, cfg)
    except Exception as exc:
        print(f"  SKIP {doc['slug']} FY{doc['fiscal_year']}: text quality failed: {exc}")
        return [], 0

    latin_word_count = count_words(cleaned.pages).latin

    # Truncate very long pages before spaCy to avoid quadratic slowdown on
    # dense table/boilerplate pages. 20k chars ≈ 3,000 words, more than enough
    # to capture any candidate term that would appear in running prose.
    capped = [
        PageText(page_number=p.page_number, text=p.text[:_MAX_PAGE_CHARS], used_ocr=p.used_ocr)
        if len(p.text) > _MAX_PAGE_CHARS else p
        for p in cleaned.pages
    ]

    try:
        sentences = segment_sentences(capped)
    except Exception as exc:
        print(f"  SKIP {doc['slug']} FY{doc['fiscal_year']}: segment failed: {exc}")
        return [], latin_word_count

    try:
        matches = matcher.match_sentences(sentences)
    except Exception as exc:
        print(f"  SKIP {doc['slug']} FY{doc['fiscal_year']}: match failed: {exc}")
        return [], latin_word_count

    hits = [
        HitRow(
            term_phrase=id_to_phrase[m.term_id],
            sasb_category=id_to_cat[m.term_id],
            slug=doc["slug"],
            company_name=doc["name"],
            fiscal_year=doc["fiscal_year"],
            industry=doc["industry"],
            page_number=m.page_number,
            sentence=m.sentence_text,
        )
        for m in matches
    ]
    return hits, latin_word_count


# ── Statistics ─────────────────────────────────────────────────────────────────

def compute_stats(
    hits: list[HitRow],
    docs: list[dict],
    name_to_industry: dict[str, str],
    cat_industries: dict[str, set[str]],
    total_latin: int,
) -> dict:
    """Returns per-term stats dict, including pass_fail based on FREQ_THRESHOLD."""
    total_docs = len(docs)

    by_term: dict[str, list[HitRow]] = defaultdict(list)
    for h in hits:
        by_term[h.term_phrase].append(h)

    stats: dict[str, dict] = {}
    for phrase, cat, _ in CANDIDATES:
        term_hits = by_term.get(phrase, [])

        docs_with_hit: set[tuple[str, int]] = {(h.slug, h.fiscal_year) for h in term_hits}
        n_reports = len(docs_with_hit)
        pct_all = n_reports / total_docs * 100 if total_docs else 0.0

        # Within-material-industry stats
        # "circular economy / Materials Sourcing & Efficiency" → last segment
        cat_norm = _norm(cat.split(" / ")[-1])
        mat_industries = cat_industries.get(cat_norm, set())
        if mat_industries:
            mat_docs = [d for d in docs if d["industry"] in mat_industries]
            mat_hits = [h for h in term_hits if h.industry in mat_industries]
            mat_docs_with_hit: set[tuple[str, int]] = {(h.slug, h.fiscal_year) for h in mat_hits}
            n_mat_reports = len(mat_docs_with_hit)
            pct_material = n_mat_reports / len(mat_docs) * 100 if mat_docs else 0.0
            n_mat_docs = len(mat_docs)
        else:
            # GCC check: treat all 390 as the denominator
            n_mat_reports = n_reports
            pct_material = pct_all
            n_mat_docs = total_docs

        total_mentions = len(term_hits)
        per_1000 = total_mentions / total_latin * 1000 if total_latin else 0.0

        ind_counts: dict[str, int] = defaultdict(int)
        for h in term_hits:
            ind_counts[h.industry] += 1
        top_industries = sorted(ind_counts.items(), key=lambda x: -x[1])[:3]

        pass_fail = "pass" if pct_material >= FREQ_THRESHOLD else "fail"

        stats[phrase] = {
            "phrase": phrase,
            "category": cat,
            "n_reports": n_reports,
            "pct_all": pct_all,
            "n_mat_reports": n_mat_reports,
            "n_mat_docs": n_mat_docs,
            "pct_material": pct_material,
            "total_mentions": total_mentions,
            "per_1000_words": per_1000,
            "top_industries": top_industries,
            "pass_fail": pass_fail,
            "hits": term_hits,
        }
    return stats


# ── Sampling ──────────────────────────────────────────────────────────────────

def sample_hits(stats: dict) -> dict[str, list[HitRow]]:
    """Sample ≤SAMPLE_N hits per PASS term, max 3 from the same company slug."""
    rng = random.Random(SAMPLE_SEED)
    samples: dict[str, list[HitRow]] = {}
    for phrase, s in stats.items():
        if s["pass_fail"] != "pass":
            continue
        hits = list(s["hits"])
        if not hits:
            samples[phrase] = []
            continue
        rng.shuffle(hits)
        per_company: dict[str, int] = defaultdict(int)
        selected: list[HitRow] = []
        for h in hits:
            if per_company[h.slug] < 3:
                selected.append(h)
                per_company[h.slug] += 1
        if len(selected) > SAMPLE_N:
            selected = rng.sample(selected, SAMPLE_N)
        samples[phrase] = selected
    return samples


# ── Output: CANDIDATES.md ─────────────────────────────────────────────────────

def write_candidates_md(
    stats: dict,
    samples: dict[str, list[HitRow]],
    docs: list[dict],
    out_path: Path,
    total_latin: int,
    cfg_matching_mode: str,
) -> None:
    n_pass = sum(1 for s in stats.values() if s["pass_fail"] == "pass")
    n_fail = sum(1 for s in stats.values() if s["pass_fail"] == "fail")
    lines: list[str] = [
        "# Candidate Term Evidence",
        "",
        "_Generated: 2026-10-09  |  corpus: 390 source_documents (annual/integrated, auto_ok, not superseded) across 65 active companies_",
        f"_Matching settings: lemma_based (LEMMA attr) or exact (LOWER attr) per term; "
        f"overlap_resolution={cfg_matching_mode}; financial-statements and ToC pages excluded_",
        f"_Sample seed: {SAMPLE_SEED}  |  sample_n: {SAMPLE_N}  |  max 3 sentences per company_",
        f"_FREQUENCY TEST: PASS if % material-industry reports ≥ {FREQ_THRESHOLD:.0f}%  |  {n_pass} PASS / {n_fail} FAIL_",
        f"_Reports in corpus: {len(docs)}_",
        f"_Total Latin narrative words: {total_latin:,}_",
        "",
    ]

    current_cat = None
    for phrase, cat, lemma_based in CANDIDATES:
        s = stats[phrase]
        if cat != current_cat:
            current_cat = cat
            lines += [
                f"## {cat}",
                "",
                "| Term | PASS/FAIL | Match | Reports (all) | % all | Reports (material) | % material | Material denominator | Mentions | per 1,000 w | Top industries |",
                "|---|:---:|---|---:|---:|---:|---:|---:|---:|---:|---|",
            ]
        match_type = "lemma" if lemma_based else "exact"
        top3 = "; ".join(f"{ind} ({n})" for ind, n in s["top_industries"]) if s["top_industries"] else "—"
        pf_badge = "✅ PASS" if s["pass_fail"] == "pass" else "❌ FAIL"
        lines.append(
            f"| `{phrase}` | {pf_badge} | {match_type} | {s['n_reports']} | {s['pct_all']:.1f}% "
            f"| {s['n_mat_reports']} | {s['pct_material']:.1f}% | {s['n_mat_docs']} "
            f"| {s['total_mentions']} | {s['per_1000_words']:.4f} | {top3} |"
        )

    # Sample sentences (all terms, for analyst reference)
    lines += ["", "---", "", "## Sample sentences (PASS terms only; ≤20 per term, max 3 per company, seed=20261006)", ""]
    for phrase, cat, _ in CANDIDATES:
        s = stats[phrase]
        if s["pass_fail"] != "pass":
            continue
        sents = samples.get(phrase, [])
        lines += [f"### `{phrase}` — {cat}", ""]
        if not sents:
            lines += ["_No matches in corpus._", ""]
            continue
        lines.append(f"_{len(sents)} sentence(s) shown (of {s['total_mentions']} total)_")
        lines.append("")
        for h in sents:
            text = h.sentence[:300] + ("…" if len(h.sentence) > 300 else "")
            lines.append(
                f"- **{h.company_name}** FY{h.fiscal_year} p.{h.page_number}: "
                f"_{text}_"
            )
        lines.append("")

    out_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {out_path}")


# ── Output: coding_sheet.xlsx ─────────────────────────────────────────────────

def write_coding_sheet(
    stats: dict,
    samples: dict[str, list[HitRow]],
    out_path: Path,
) -> None:
    import openpyxl
    from openpyxl.styles import Alignment, Font, PatternFill

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "coding_sheet"

    headers = [
        "term", "sasb_category", "company", "fiscal_year",
        "page", "sentence",
        "ESG-relevant? (Yes/No)", "Comment",
    ]
    ws.append(headers)

    header_fill = PatternFill("solid", fgColor="4472C4")
    header_font = Font(bold=True, color="FFFFFF")
    coder_fill  = PatternFill("solid", fgColor="FFF2CC")
    for col_idx, cell in enumerate(ws[1], start=1):
        cell.font      = header_font
        cell.fill      = header_fill
        cell.alignment = Alignment(wrap_text=True, vertical="center")
        if col_idx >= 7:
            cell.fill = PatternFill("solid", fgColor="2E74B5")

    def _clean(s: str) -> str:
        s = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", " ", s)
        return re.sub(r"[\t\n\r]+", " ", s).strip()

    row_num = 2
    for phrase, _cat, _ in CANDIDATES:
        if stats.get(phrase, {}).get("pass_fail") != "pass":
            continue
        for h in samples.get(phrase, []):
            ws.append([
                phrase,
                h.sasb_category,
                h.company_name,
                h.fiscal_year,
                h.page_number,
                _clean(h.sentence),
                "",
                "",
            ])
            ws.cell(row=row_num, column=7).fill = coder_fill
            ws.cell(row=row_num, column=8).fill = coder_fill
            row_num += 1

    ws.column_dimensions["A"].width = 28
    ws.column_dimensions["B"].width = 40
    ws.column_dimensions["C"].width = 38
    ws.column_dimensions["D"].width = 10
    ws.column_dimensions["E"].width =  8
    ws.column_dimensions["F"].width = 90
    ws.column_dimensions["G"].width = 22
    ws.column_dimensions["H"].width = 30

    for row in ws.iter_rows(min_row=2, min_col=6, max_col=6):
        for cell in row:
            cell.alignment = Alignment(wrap_text=True, vertical="top")

    wb.save(str(out_path))
    print(f"Wrote {out_path}  ({row_num - 2} data rows)")


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    from app.config import settings as app_settings
    from app.crawler import register_all_mappers
    from app.services.matcher import TaxonomyMatcher
    from app.services.verity_config import load_verity_config
    register_all_mappers()

    # Disable OCR for this read-only analysis: candidate terms are English phrases
    # that won't appear in scanned/Arabic pages. Tesseract on a scanned MENA
    # annual report page can take minutes per page, blocking the whole run.
    # Setting the threshold to 0 means every page passes the native-text check,
    # so extract_pdf_pages never falls back to Tesseract.
    app_settings.ocr_trigger_char_threshold = 0

    db_url = os.environ.get("DATABASE_URL", "")
    if not db_url:
        raise RuntimeError("DATABASE_URL not set")

    workbook_path = REPO_ROOT / "docs" / "methodology" / "Verity_SASB_Mapping_Signed.xlsx"
    if not workbook_path.exists():
        raise RuntimeError(f"Workbook not found: {workbook_path}")

    out_dir = REPO_ROOT / "docs" / "term-evidence"
    out_dir.mkdir(parents=True, exist_ok=True)

    print("Loading workbook industry mappings…")
    name_to_industry, cat_industries = load_materiality(workbook_path)

    print("Querying eligible source_documents from DB…")
    docs = load_all_docs(db_url)
    print(f"  {len(docs)} source_documents")

    # Attach normalised industry from workbook (overrides DB value when available)
    for d in docs:
        matched = name_to_industry.get(d["name"])
        if matched:
            d["industry"] = matched

    cfg = load_verity_config()
    print(f"  matching_mode from config: {cfg.matching_mode}")

    print("Building TaxonomyMatcher with candidate terms…")
    id_to_phrase: dict[int, str] = {}
    id_to_cat: dict[int, str] = {}
    term_objs = []
    for tid, (phrase, cat, lemma_based) in enumerate(CANDIDATES, start=1):
        id_to_phrase[tid] = phrase
        id_to_cat[tid]    = cat
        term_objs.append(_CandidateTerm(tid, phrase, lemma_based))
    matcher = TaxonomyMatcher(term_objs)

    print(f"Processing {len(docs)} documents…")
    all_hits: list[HitRow] = []
    total_latin = 0
    t0 = time.monotonic()
    for idx, doc in enumerate(docs, start=1):
        t_doc = time.monotonic()
        # Run in a daemon thread with a timeout so a hung document (e.g. a very
        # large PDF that causes spaCy to take >5 min) doesn't block the whole run.
        _result: list[tuple[list[HitRow], int] | None] = [None]
        _done = threading.Event()
        def _worker(_doc=doc, _r=_result, _e=_done) -> None:
            _r[0] = process_document(_doc, matcher, id_to_phrase, id_to_cat, cfg)
            _e.set()
        _t = threading.Thread(target=_worker, daemon=True)
        _t.start()
        if not _done.wait(timeout=_DOC_TIMEOUT_SECS):
            print(f"  TIMEOUT {doc['slug']} FY{doc['fiscal_year']}: exceeded {_DOC_TIMEOUT_SECS}s")
            hits, latin_wc = [], 0
        else:
            hits, latin_wc = _result[0]  # type: ignore[misc]
        elapsed = time.monotonic() - t_doc
        doc["latin_word_count"] = latin_wc
        total_latin += latin_wc
        all_hits.extend(hits)
        if idx % 10 == 0 or idx == len(docs):
            print(
                f"  [{idx}/{len(docs)}] {doc['slug']} FY{doc['fiscal_year']}: "
                f"{len(hits)} hits in {elapsed:.1f}s  (total elapsed {time.monotonic()-t0:.0f}s)"
            )

    print(f"Total hits: {len(all_hits)}")
    print(f"Total Latin narrative words: {total_latin:,}")
    print("Computing statistics…")
    stats = compute_stats(all_hits, docs, name_to_industry, cat_industries, total_latin)

    n_pass = sum(1 for s in stats.values() if s["pass_fail"] == "pass")
    n_fail = sum(1 for s in stats.values() if s["pass_fail"] == "fail")
    print(f"  FREQUENCY TEST ({FREQ_THRESHOLD:.0f}% threshold): {n_pass} PASS / {n_fail} FAIL")
    for phrase, s in stats.items():
        marker = "PASS" if s["pass_fail"] == "pass" else "FAIL"
        print(f"    [{marker}] {phrase!r:45s}  {s['pct_material']:.1f}% of material reports  ({s['n_mat_reports']}/{s['n_mat_docs']})")

    samples = sample_hits(stats)
    coding_rows = sum(len(v) for v in samples.values())
    print(f"  Coding sheet: {coding_rows} rows across {len(samples)} PASS terms")

    print("Writing outputs…")
    write_candidates_md(
        stats, samples, docs, out_dir / "CANDIDATES.md",
        total_latin=total_latin,
        cfg_matching_mode=cfg.matching_mode,
    )
    write_coding_sheet(stats, samples, out_dir / "coding_sheet.xlsx")

    print(f"\nDone.  PASS={n_pass}  FAIL={n_fail}  coding_sheet_rows={coding_rows}")


if __name__ == "__main__":
    main()
