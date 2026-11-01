# Verity ESG scoring code

This folder contains the exact Python code that produces the ESG
disclosure scores reported in the thesis. Every `.py` file is a
byte-identical copy of the corresponding production module in the
`backend/` tree; `_verify_hashes.py` prints the sha256 of each pair and
exits non-zero on any mismatch.

Versions in this snapshot:

| Component | Version |
|---|---|
| Taxonomy    | v6 (General component; 8 General terms; 104 terms total) |
| Pipeline    | 0.6.0 |

The scoring measures *how thoroughly* each company **discloses**
Environmental, Social and Governance topics — not sentiment, not
performance. The denominator counts only Latin-script tokens (the
taxonomy is English) and the financial-statements section is excluded
before matching (Ferjancic et al., 2024).

---

## Method step → file & function map

| Step | What it does | File | Key function(s) |
|---|---|---|---|
| 1. Text extraction | Open the PDF, extract native text per page, fall back to Tesseract OCR for scanned pages, count Latin + Arabic tokens | `backend/app/services/pdf_extraction.py` | `extract_pdf_pages`, `count_words`, `count_latin_words_in_text` |
| 1b. Narrative detection | Strip repeated headers/footers; drop contents / GRI-index pages; detect and exclude the financial-statements section (independent auditor's report onward); cheap OCR pre-check | `backend/app/services/text_quality.py` | `apply_text_quality`, `remove_repeated_header_footer`, `detect_contents_pages`, `detect_financial_statements_start`, `estimate_ocr_fraction` |
| 2. Sentence filter | spaCy sentence segmentation + the five-test quality filter (capital start, terminal punctuation, ≥ 8 words, < 50% ALL-CAPS, < 30% non-letter chars) | `backend/app/services/text_processing.py` | `segment_sentences`, `is_sentence_quality`, `filter_sentences` |
| 3. Term matching | spaCy `PhraseMatcher` with LEMMA + LOWER passes; overlapping spans collapsed to the longest (`filter_spans`); stores page number + sentence for every hit | `backend/app/services/matcher.py` | `TaxonomyMatcher`, `TaxonomyMatcher.match_sentences` |
| 4a. SASB materiality weighting | Term weight = 1.5 if the term's primary or secondary SASB General Issue Category is material for the company's SASB industry, else 1.0 | `backend/app/services/sasb_materiality.py` | `term_weight`, `material_categories_for` |
| 4b. Density calculation | `density = (sum of weighted matches per bucket) / narrative_word_count × 1000`; bucketed into E / S / G / General / Add-on | `backend/app/services/scoring.py`, `backend/app/services/pipeline.py` | `score_report_categories`, `_run_pipeline_cpu` |
| 4c. Banking add-on | For `is_financial=True` institutions, Add-on terms (group `addon`) are counted into `addon_density`; separate from the pillars | `backend/app/services/pipeline.py` | `_run_pipeline_cpu` (addon branch) |
| 5. Rank score + composite | For each pillar, convert density → 0–100 by average rank across the 390 company-year pool; composite is the simple average of the four pillar scores | `backend/scripts/compute_ranks.py` | `_rank_scores`, `main` |
| Taxonomy loading | v6 taxonomy structure (General component + inflation of core); canonical sha256 taxonomy hash for versioning | `backend/scripts/seed_taxonomy_v6.py`, `backend/app/services/taxonomy_hash.py`, `backend/app/models/taxonomy.py` | `seed_taxonomy_v6.main`, `compute_taxonomy_hash` |
| Config | Switch definitions (TOC exclusion, header/footer ratio, OCR cap, FS boundary markers) | `backend/app/services/verity_config.py`, `config/verity.toml` | `load_verity_config` |

Every match is stored with its page number and sentence text; every
`CategoryScore` row stamps `taxonomy_version` and `pipeline_version`,
so cross-version comparisons stay honest.

---

## Formulas

Three formulas govern the whole score. Everything else is bookkeeping.

**1. Density (per report, per bucket)**

```
density_bucket = (sum of term.weight for every match in bucket) / narrative_word_count * 1000
```

- `bucket` ∈ { Environmental, Social, Governance, General, Add-on }.
- `term.weight` is the SASB-material weight (1.5 if the term's SASB
  category is material for the institution's SASB industry, else 1.0).
- `narrative_word_count` counts only Latin tokens in the sentences that
  passed the five-test quality filter — i.e. the same text that was
  matched against. Numerator and denominator cover identical text.
- Add-on density is only populated for financial-sector institutions.

**2. Rank score (per report, per bucket, 0–100)**

```
rank_score = 100 * (average_ascending_rank - 1) / (N - 1)
```

- Rank is computed across the full 390 company-year pool for E / S / G /
  General, and across the financial-only pool for Add-on.
- Ties get the average of the ranks they share.
- Stored to one decimal place.

**3. Composite score (per report, 0–100)**

```
composite_score         = average(E_score, S_score, G_score, General_score)
composite_3pillar       = average(E_score, S_score, G_score)
composite_general_no_new3 = average(E_score, S_score, G_score, General_no_new3_score)
```

`composite_general_no_new3` is the robustness variant that excludes the
three examiner-requested terms (`innovation`, `feedback`,
`digital services`) from the General density.

---

## Taxonomy

The full term list is in `taxonomy_v6_terms.csv` alongside this README.
Columns:

- `concept` — the canonical phrase stored in the `Term.phrase` column.
- `spelling_variants` — the specific `Term.phrase` strings that make up
  this concept (pipe-separated). For most concepts there is a single
  canonical phrase; inflections are handled by spaCy lemma matching at
  match time ("governed", "governing", "governance" all collapse).
- `component` — E / S / G / General / Banking.
- `sasb_category` — SASB General Issue Category (primary; secondary in
  parentheses if present).
- `industries` — SASB industries for which this term's SASB category is
  material. The term's `weight` for a given institution is 1.5 iff that
  institution's SASB industry appears here, else 1.0.

v6 totals: E = 24, S = 27, G = 36, General = 8, Banking add-on = 9
(104 terms).

---

## Python packages

The code relies on these runtime packages (versions pinned by the parent
project — see `backend/requirements.txt` for exact pins):

- `pymupdf` — native PDF text extraction (`extract_pdf_pages`).
- `pytesseract` + `Pillow` — OCR fallback for scanned pages. Requires a
  local Tesseract binary with `eng+ara` traineddata.
- `spacy` + `en_core_web_sm` — sentence segmentation, lemma attributes,
  and the `PhraseMatcher`.
- `sqlalchemy`, `psycopg[binary]`, `python-dotenv` — ORM, DB driver,
  env-var loader for term/report persistence.
- `boto3` + `botocore` — read PDF bytes from Cloudflare R2 object
  storage. Local-disk fallback is available when `VERITY_LOCAL_STORAGE=1`.
- `openpyxl` — read the SASB industry → material-category workbook.
- `pydantic`, `pydantic-settings` — settings loading.
- `tomllib` (standard library in Python ≥ 3.11) — parse `config/verity.toml`.

Python 3.11+. Everything runs CPU-only; no GPU is required.

Install (from the project root):

```bash
python -m venv backend/.venv
backend/.venv/Scripts/pip install -r backend/requirements.txt
backend/.venv/Scripts/python -m spacy download en_core_web_sm
```

---

## Running the scoring for one report

The scoring expects a report row to exist in the database (the taxonomy
and the PDF file key both come from the database). To re-score a single
report end-to-end without writing to the DB, use the shipped CPU worker:

```python
from pathlib import Path
import sys
sys.path.insert(0, "backend")

from dotenv import load_dotenv
load_dotenv("backend/.env")

import app.models.company_year, app.models.institution, app.models.provenance
import app.models.report, app.models.review, app.models.run, app.models.score
from app.database import SessionLocal
from app.models.institution import Institution
from app.models.report import Report
from app.models.taxonomy import Category, Term
from app.services.pipeline import _run_pipeline_cpu, build_terms_payload
from app.services.verity_config import load_verity_config

SLUG, FY = "al-rajhi-bank", 2023

db = SessionLocal()
inst = db.query(Institution).filter(Institution.slug == SLUG).one()
rep = (db.query(Report)
         .filter(Report.institution_id == inst.id,
                 Report.fiscal_year == FY,
                 Report.pipeline_version == "0.6.0",
                 Report.status == "scored")
         .order_by(Report.id.desc())
         .first())

payload = build_terms_payload(
    db.query(Term).all(),
    db.query(Category).all(),
    sasb_industry=inst.sasb_industry,
)
w = _run_pipeline_cpu(
    source_document_id=rep.source_document_id or 0,
    file_path=rep.file_path,
    terms_payload=payload,
    cfg=load_verity_config(),
    is_financial=bool(inst.is_financial),
)

print(f"E={w.e_density:.6f}  S={w.s_density:.6f}  G={w.g_density:.6f}  "
      f"General={w.general_density:.6f}  Add-on={w.addon_density}")
print(f"narrative words={w.narrative_word_count}  matches={w.matches_count}")
```

To compute the per-pool rank scores (E_score, S_score, G_score,
General_score) and the composite, run `compute_ranks.py` AFTER every
report in the pool has been scored:

```bash
backend/.venv/Scripts/python backend/scripts/compute_ranks.py --dry-run
```

Drop `--dry-run` to persist. Rank scores are overwritten in place; no
new rows are created.

---

## Reproducibility proof

Running the Python code in this folder against Al Rajhi Bank's FY2023
annual report reproduces the live database values exactly:

| field                | re-score    | database    | check |
|---|---|---|---|
| narrative_word_count | 49,610      | 49,610      | OK |
| matches_count        | 569         | 569         | OK |
| E_density            | 0.987704    | 0.987704    | OK |
| S_density            | 1.390849    | 1.390849    | OK |
| G_density            | 6.611570    | 6.611570    | OK |
| General_density      | 3.336021    | 3.336021    | OK |
| Add-on_density       | 0.604717    | 0.604717    | OK |

(The 0–100 rank scores — `e_score=73.5`, `s_score=77.6`, `g_score=34.2`,
`general_score=64.0`, `composite_score=62.3` — are produced by
`compute_ranks.py` from the full 390 company-year pool and therefore
can't be reproduced from a single re-score. Same inputs, same
deterministic ranking.)
