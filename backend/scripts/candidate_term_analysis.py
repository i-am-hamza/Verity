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
import time
from collections import defaultdict
from dataclasses import dataclass, field
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

# ── Industry materiality: SASB category → set of SASB industries ─────────────
# Built from docs/methodology/Verity_SASB_Mapping_Signed.xlsx
# "Industry materiality" sheet.  Normalise names for comparison.
def _norm(s: str) -> str:
    """Lowercase + collapse non-alphanumeric to space for fuzzy matching."""
    return re.sub(r"[^a-z0-9]+", " ", s.lower()).strip()


def load_materiality(workbook_path: Path) -> tuple[
    dict[str, str],          # slug -> sasb_industry (normalised)
    dict[str, set[str]],     # normed_category -> set of normed industries
]:
    import openpyxl
    wb = openpyxl.load_workbook(str(workbook_path), data_only=True)

    # Company industries: col B = company name, col C = symbol (unused),
    # col D = country (unused), col H = SASB industry
    ws_co = wb["Company industries"]
    # row 0 = header; slug computed identically to how load_institutions.py does it
    def _slugify(name: str) -> str:
        s = name.lower()
        s = re.sub(r"[^a-z0-9\s]", "", s)
        return re.sub(r"\s+", "-", s).strip("-")

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

def load_scored_docs(db_url: str) -> list[dict]:
    """Return list of dicts with id, file_path, fiscal_year, slug, name, industry,
    latin_word_count (from existing Report row, so we don't re-compute it)."""
    import psycopg
    conn = psycopg.connect(db_url)
    cur = conn.cursor()
    cur.execute("""
        SELECT sd.id, sd.file_path, sd.fiscal_year,
               i.slug, i.name, i.industry,
               r.latin_word_count
        FROM source_documents sd
        JOIN institutions i ON i.id = sd.institution_id
        JOIN reports r ON r.source_document_id = sd.id
        WHERE i.active = true
          AND sd.review_status = 'auto_ok'
          AND sd.superseded_by_id IS NULL
          AND sd.report_type IN ('annual', 'integrated')
          AND r.status = 'scored'
        ORDER BY i.slug, sd.fiscal_year
    """)
    rows = cur.fetchall()
    conn.close()
    # De-duplicate: if a source_document has multiple reports (re-processing),
    # take the one with the highest id (most recent).
    seen_sdid: dict[int, dict] = {}
    for sd_id, file_path, fy, slug, name, industry, latin_wc in rows:
        if sd_id not in seen_sdid:
            seen_sdid[sd_id] = dict(
                id=sd_id, file_path=file_path, fiscal_year=fy,
                slug=slug, name=name,
                industry=_norm(str(industry)) if industry else "",
                latin_word_count=latin_wc or 0,
            )
    return list(seen_sdid.values())


# ── Term class for TaxonomyMatcher ────────────────────────────────────────────

class _CandidateTerm:
    __slots__ = ("id", "phrase", "lemma_based", "weight", "category_id", "category_weight")
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


def process_document(
    doc: dict,
    matcher,  # TaxonomyMatcher
    id_to_phrase: dict[int, str],
    id_to_cat: dict[int, str],
    cfg,
) -> list[HitRow]:
    from app.services.storage import read_pdf_bytes
    from app.services.pdf_extraction import extract_pdf_pages
    from app.services.text_quality import apply_text_quality
    from app.services.text_processing import segment_sentences

    try:
        pdf_bytes = read_pdf_bytes(doc["file_path"])
    except Exception as exc:
        # R2 NoSuchKey → try local fallback (PDFs ingested before R2 upload completed)
        if "NoSuchKey" in str(exc):
            local_p = BACKEND / "storage" / "reports" / doc["file_path"].replace("/", os.sep)
            if local_p.exists():
                pdf_bytes = local_p.read_bytes()
            else:
                print(f"  SKIP {doc['slug']} FY{doc['fiscal_year']}: fetch failed: {exc}")
                return []
        else:
            print(f"  SKIP {doc['slug']} FY{doc['fiscal_year']}: fetch failed: {exc}")
            return []

    try:
        pages = extract_pdf_pages(pdf_bytes)
    except Exception as exc:
        print(f"  SKIP {doc['slug']} FY{doc['fiscal_year']}: extract failed: {exc}")
        return []

    try:
        cleaned = apply_text_quality(pages, cfg)
    except Exception as exc:
        print(f"  SKIP {doc['slug']} FY{doc['fiscal_year']}: text quality failed: {exc}")
        return []

    try:
        sentences = segment_sentences(cleaned.pages)
    except Exception as exc:
        print(f"  SKIP {doc['slug']} FY{doc['fiscal_year']}: segment failed: {exc}")
        return []

    try:
        matches = matcher.match_sentences(sentences)
    except Exception as exc:
        print(f"  SKIP {doc['slug']} FY{doc['fiscal_year']}: match failed: {exc}")
        return []

    return [
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


# ── Statistics ─────────────────────────────────────────────────────────────────

def compute_stats(
    hits: list[HitRow],
    docs: list[dict],
    name_to_industry: dict[str, str],
    cat_industries: dict[str, set[str]],
) -> dict:
    """Returns per-term stats dict."""
    # Total Latin words across all scored docs
    total_latin = sum(d["latin_word_count"] for d in docs)
    total_docs = len(docs)

    # Build mapping: term_phrase -> list[HitRow]
    by_term: dict[str, list[HitRow]] = defaultdict(list)
    for h in hits:
        by_term[h.term_phrase].append(h)

    stats: dict[str, dict] = {}
    for phrase, cat, _ in CANDIDATES:
        term_hits = by_term.get(phrase, [])

        # Reports (not sentences) containing this term
        docs_with_hit: set[tuple[str, int]] = {(h.slug, h.fiscal_year) for h in term_hits}
        n_reports = len(docs_with_hit)
        pct_all = n_reports / total_docs * 100 if total_docs else 0.0

        # Within-material-industry stats
        cat_norm = _norm(cat.split(" / ")[-1])  # last segment: "circular economy / Materials Sourcing & Efficiency" → correct category
        mat_industries = cat_industries.get(cat_norm, set())
        if mat_industries:
            mat_docs = [d for d in docs if d["industry"] in mat_industries]
            mat_hits = [h for h in term_hits if h.industry in mat_industries]
            mat_docs_with_hit: set[tuple[str, int]] = {(h.slug, h.fiscal_year) for h in mat_hits}
            n_mat_reports = len(mat_docs_with_hit)
            pct_material = n_mat_reports / len(mat_docs) * 100 if mat_docs else 0.0
            n_mat_docs = len(mat_docs)
        else:
            n_mat_reports = n_reports
            pct_material = pct_all
            n_mat_docs = total_docs  # GCC check: all industries

        total_mentions = len(term_hits)
        per_1000 = total_mentions / total_latin * 1000 if total_latin else 0.0

        # Top industries by mention count
        ind_counts: dict[str, int] = defaultdict(int)
        for h in term_hits:
            ind_counts[h.industry] += 1
        top_industries = sorted(ind_counts.items(), key=lambda x: -x[1])[:3]

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
            "hits": term_hits,
        }
    return stats


# ── Sampling ──────────────────────────────────────────────────────────────────

def sample_hits(stats: dict) -> dict[str, list[HitRow]]:
    rng = random.Random(SAMPLE_SEED)
    samples: dict[str, list[HitRow]] = {}
    for phrase, s in stats.items():
        hits = s["hits"]
        if len(hits) <= SAMPLE_N:
            samples[phrase] = list(hits)
        else:
            samples[phrase] = rng.sample(hits, SAMPLE_N)
    return samples


# ── Output: CANDIDATES.md ─────────────────────────────────────────────────────

def write_candidates_md(
    stats: dict,
    samples: dict[str, list[HitRow]],
    docs: list[dict],
    out_path: Path,
    cfg_matching_mode: str,
) -> None:
    lines: list[str] = [
        "# Candidate Term Evidence",
        "",
        f"_Generated: 2026-10-06  |  corpus: all scored annual/integrated reports of 65 active companies_",
        f"_Matching settings: lemma_based (LEMMA attr) or exact (LOWER attr) per term; "
        f"overlap_resolution={cfg_matching_mode}; financial-statements and ToC pages excluded_",
        f"_Sample seed: {SAMPLE_SEED}  |  sample_n: {SAMPLE_N}_",
        f"_Scored reports in corpus: {len(docs)}_",
        f"_Total Latin narrative words: {sum(d['latin_word_count'] for d in docs):,}_",
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
                "| Term | Match | Reports (all) | % all | Reports (material) | % material | Material denominator | Mentions | per 1,000 w | Top industries |",
                "|---|---|---:|---:|---:|---:|---:|---:|---:|---|",
            ]
        match_type = "lemma" if lemma_based else "exact"
        top3 = "; ".join(f"{ind} ({n})" for ind, n in s["top_industries"]) if s["top_industries"] else "—"
        flag = "" if s["total_mentions"] > 0 else " ⚠️ ZERO"
        few_flag = " ⚠️ FEW (<5)" if 0 < s["total_mentions"] < 5 else ""
        lines.append(
            f"| `{phrase}`{flag}{few_flag} | {match_type} | {s['n_reports']} | {s['pct_all']:.1f}% "
            f"| {s['n_mat_reports']} | {s['pct_material']:.1f}% | {s['n_mat_docs']} "
            f"| {s['total_mentions']} | {s['per_1000_words']:.4f} | {top3} |"
        )

    # Sample sentences section
    lines += ["", "---", "", "## Sample sentences (≤20 per term, seed=20261006)", ""]
    for phrase, cat, _ in CANDIDATES:
        sents = samples.get(phrase, [])
        lines += [f"### `{phrase}` — {cat}", ""]
        if not sents:
            lines += ["_No matches in corpus._", ""]
            continue
        lines.append(f"_{len(sents)} sentence(s) shown (of {stats[phrase]['total_mentions']} total)_")
        lines.append("")
        for h in sents:
            # Truncate long sentences for readability
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
    samples: dict[str, list[HitRow]],
    out_path: Path,
) -> None:
    import openpyxl
    from openpyxl.styles import Font, PatternFill, Alignment

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "coding_sheet"

    headers = [
        "term", "sasb_category", "company", "fiscal_year",
        "page", "sentence",
        "ESG-relevant? (Yes/No)", "Comment",
    ]
    ws.append(headers)

    # Style header row
    header_fill = PatternFill("solid", fgColor="4472C4")
    header_font = Font(bold=True, color="FFFFFF")
    coder_fill  = PatternFill("solid", fgColor="FFF2CC")  # light yellow for coder cols
    for col_idx, cell in enumerate(ws[1], start=1):
        cell.font      = header_font
        cell.fill      = header_fill
        cell.alignment = Alignment(wrap_text=True, vertical="center")
        if col_idx >= 7:
            cell.fill = PatternFill("solid", fgColor="2E74B5")  # darker blue for coder

    def _clean(s: str) -> str:
        """Strip control characters that openpyxl rejects; collapse whitespace."""
        s = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", " ", s)
        return re.sub(r"[\t\n\r]+", " ", s).strip()

    row_num = 2
    for phrase, cat, _ in CANDIDATES:
        for h in samples.get(phrase, []):
            ws.append([
                phrase,
                h.sasb_category,
                h.company_name,
                h.fiscal_year,
                h.page_number,
                _clean(h.sentence),
                "",  # ESG-relevant — EMPTY for human coder
                "",  # Comment    — EMPTY for human coder
            ])
            # Highlight coder columns
            ws.cell(row=row_num, column=7).fill = coder_fill
            ws.cell(row=row_num, column=8).fill = coder_fill
            row_num += 1

    # Column widths
    ws.column_dimensions["A"].width = 28
    ws.column_dimensions["B"].width = 40
    ws.column_dimensions["C"].width = 38
    ws.column_dimensions["D"].width = 10
    ws.column_dimensions["E"].width =  8
    ws.column_dimensions["F"].width = 90
    ws.column_dimensions["G"].width = 22
    ws.column_dimensions["H"].width = 30

    # Wrap sentence column
    for row in ws.iter_rows(min_row=2, min_col=6, max_col=6):
        for cell in row:
            cell.alignment = Alignment(wrap_text=True, vertical="top")

    wb.save(str(out_path))
    print(f"Wrote {out_path}  ({row_num - 2} data rows)")


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    from app.crawler import register_all_mappers
    from app.services.matcher import TaxonomyMatcher
    from app.services.verity_config import load_verity_config
    register_all_mappers()

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

    print("Querying scored documents from DB…")
    docs = load_scored_docs(db_url)
    print(f"  {len(docs)} scored source_documents")

    # Attach normalised industry from workbook (overrides DB industry if available)
    for d in docs:
        matched = name_to_industry.get(d["name"])
        if matched:
            d["industry"] = matched
        # else keep d["industry"] from DB (already normalised)

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
    t0 = time.monotonic()
    for idx, doc in enumerate(docs, start=1):
        t_doc = time.monotonic()
        hits = process_document(doc, matcher, id_to_phrase, id_to_cat, cfg)
        elapsed = time.monotonic() - t_doc
        all_hits.extend(hits)
        if idx % 10 == 0 or idx == len(docs):
            print(
                f"  [{idx}/{len(docs)}] {doc['slug']} FY{doc['fiscal_year']}: "
                f"{len(hits)} hits in {elapsed:.1f}s  (total elapsed {time.monotonic()-t0:.0f}s)"
            )

    print(f"Total hits: {len(all_hits)}")
    print("Computing statistics…")
    stats = compute_stats(all_hits, docs, name_to_industry, cat_industries)
    samples = sample_hits(stats)

    # Zero / few flags
    n_zero = sum(1 for s in stats.values() if s["total_mentions"] == 0)
    n_few  = sum(1 for s in stats.values() if 0 < s["total_mentions"] < 5)
    print(f"  {n_zero} terms with ZERO matches, {n_few} terms with < 5 matches")

    print("Writing outputs…")
    write_candidates_md(
        stats, samples, docs, out_dir / "CANDIDATES.md",
        cfg_matching_mode=cfg.matching_mode,
    )
    write_coding_sheet(samples, out_dir / "coding_sheet.xlsx")

    print("\nDone.")


if __name__ == "__main__":
    main()
