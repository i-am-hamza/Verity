# Disclosure Scorer — Backend

Scores financial institutions' annual reports on how thoroughly they
disclose across the three ESG pillars (Environmental, Social, Governance),
based on weighted phrase density — not sentiment. See
`app/services/scoring.py` for the core logic and reasoning.

## Setup

```bash
cd backend
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate

pip install -r requirements.txt
python -m spacy download en_core_web_sm

# System dependency for OCR fallback (scanned PDFs):
#   macOS:   brew install tesseract
#   Ubuntu:  sudo apt install tesseract-ocr
#   Windows: https://github.com/UB-Mannheim/tesseract/wiki

cp .env.example .env
```

## Run

```bash
uvicorn app.main:app --reload
```

API docs (interactive): http://localhost:8000/docs

## Collecting annual reports (crawler)

`scripts/crawl_annual_reports.py` automates the legitimate part of data
collection: visiting each institution's own public Investor Relations page
(no login, ever) and downloading annual report PDFs for the target years.

```bash
python scripts/crawl_annual_reports.py \
    --config scripts/institutions_config.json \
    --output storage/reports \
    --years 2021 2022 2023 2024 2025
```

`institutions_config.json` has 16 real Middle East financial institutions
(sourced from market-cap data, not guessed). Each entry is tagged
`"verified_url"`: `true` means the IR URL was confirmed reachable and
correct during research; `false` means only the base domain is known and
the exact IR/annual-reports path still needs a human to check before the
crawler will touch it — it skips unverified entries rather than guessing.

What it will **not** do, ever: create an account, submit a login, or fetch
anything behind a paywall. If an institution's reports aren't reachable
through its public IR page, the crawler logs it under
`needs_manual_followup` in `storage/reports/crawl_summary.json` instead of
working around the wall — fall back to Tiers 3–4 in the Data Acquisition
Plan (Wayback Machine, direct email to IR) for those by hand.

Once you've registered institutions via `POST /institutions` and noted
their ids, feed the crawler's downloads into the actual pipeline:

```bash
python scripts/register_downloaded_reports.py \
    --summary storage/reports/crawl_summary.json \
    --institution-map scripts/institution_id_map.json \
    --api http://localhost:8000
```

## Seed the starter taxonomy

Loads the Environmental / Social / Governance taxonomy (sourced from GRI
Standards and SASB's Financial Sector Standard) so you can
score reports immediately instead of building the taxonomy from scratch:

```bash
python -m seed.load_taxonomy
```

Add or edit terms afterward via `POST /taxonomy/categories/{id}/terms`,
or directly in `seed/taxonomy_starter.json` before seeding.

## Typical workflow

1. `POST /institutions` — register an institution (name, country, sector)
2. `POST /reports` (multipart) — upload a PDF for that institution + fiscal year.
   This runs the full pipeline synchronously: text extraction → OCR fallback
   if needed → sentence segmentation → phrase matching → scoring.
3. `GET /scores/reports/{report_id}` — composite + per-category score for one report
4. `GET /scores/institutions/{id}` — aggregated score across all of that
   institution's uploaded years
5. `GET /scores/rankings` — full leaderboard across every institution
6. `GET /reports/{id}/evidence?term_id=` — the actual matched sentences
   (this is what makes a score defensible rather than a black box)

## Tests

```bash
pytest tests/ -v
```

`tests/test_scoring.py` covers the core logic with no DB/NLP dependency,
including a test that directly encodes the "governance needs to be
improved counts the same as a positive mention" requirement from the spec.

## Architecture notes / what to change before scaling past the pilot

| Area | Pilot (now) | At scale (100 institutions x 4 years) |
|---|---|---|
| DB | SQLite | Postgres — swap `DATABASE_URL` in `.env`, no code changes needed |
| Report processing | Synchronous, in the upload request | Move `process_report()` behind Celery/RQ/arq so uploads return instantly |
| Matching | Re-tokenizes each sentence twice (segmentation + matching) | Keep spaCy `Span` objects from segmentation, match directly on those |
| Sentiment/negation | Not implemented (density-only, by design) | Optional Phase 2: dependency-parse negation scope for true negation ("does NOT have a governance policy") — distinct from sentiment |
| Auth | None | Add before this touches anything beyond localhost |

## Project structure

```
backend/
  app/
    main.py              FastAPI app + router wiring
    config.py             Settings (env-driven)
    database.py            SQLAlchemy engine/session
    models/                 ORM models (Institution, Report, Category, Term, CategoryScore, MatchEvidence)
    schemas/                 Pydantic request/response models
    services/
      pdf_extraction.py       PyMuPDF + Tesseract OCR fallback
      text_processing.py       Cleaning + spaCy sentence segmentation
      matcher.py                 spaCy PhraseMatcher (lemma + exact)
      scoring.py                  Core scoring formulas (pure functions, well-tested)
      pipeline.py                  Orchestrates extraction -> matching -> scoring -> persistence
    api/routes/               institutions.py, taxonomy.py, reports.py, scores.py
  seed/                     Starter taxonomy JSON + loader script
  tests/                    pytest suite
```
