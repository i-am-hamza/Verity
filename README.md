# Verity

Text-based ESG disclosure scoring for Middle East companies, built as the
quantitative instrument for a PhD. Scores annual and integrated reports
on how thoroughly each company *discloses* Environmental, Social, and
Governance topics — it is not a sentiment score and not a performance
score. The design rationale, hard limits on how the data is collected,
and project rules are in [CLAUDE.md](CLAUDE.md); the methodology detail
and the scoring formula will live in `docs/METHODOLOGY.md` (generated
from a dedicated prompt that pulls real figures from the live system,
not drafted by hand).

Current state (end of Session 7):

- 60 active institutions in scope; 44 have at least one scored report
  under the current taxonomy. The 17 not-yet-scored are listed with
  explicit reasons in [`docs/INVENTORY.md`](docs/INVENTORY.md).
- 130 reports under the current taxonomy; `docs/PROCESSING_QA.md` is
  the per-report audit matrix.
- Dashboard at `/frontend/` (React + Vite + Tailwind) wired to a FastAPI
  backend. The dashboard view set is complete for the data we have
  tonight; a short list of UI follow-ups is in
  [`docs/BACKLOG.md`](docs/BACKLOG.md).

This README is a current-state snapshot, not a final handover.

## Repo layout

```
backend/            FastAPI + SQLAlchemy + Alembic. Crawler, scorer, CLI.
backend/app/        Code (routes, models, schemas, services, crawler).
backend/scripts/    One-off scripts (audits, exports, one-shot fixes).
backend/seed/       Taxonomy seed JSON + loader.
backend/tests/      Unit + integration tests.
frontend/           React dashboard (dark/light themes; token-only styling).
config/verity.toml  Pipeline + scoring switches.
data/               Institution lists, IR sources, ingest inputs.
docs/               Decisions, limitations, run book, backlog, audits.
exports/            Generated CSVs (leaderboard, scores_long, evidence, sensitivity).
storage/            Downloaded PDFs + append-only manifest.jsonl.
scripts/check.py    Orchestrates backend ruff/mypy/pytest + frontend
                    typecheck/lint/test. Returns non-zero on failure.
```

## Setup

Prerequisites common to every platform:

- Python 3.14 (what Session 1 was built against).
- Node 20+ and npm.
- Tesseract OCR with English and Arabic data (`eng.traineddata`,
  `ara.traineddata`).

### Windows

```powershell
# From the repo root (E:\9. Verity for the development machine):
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m playwright install chromium

# Database (SQLite by default).
alembic upgrade head
python -m seed.load_institutions
python -m seed.load_taxonomy

# Tesseract:
#   Install from https://github.com/UB-Mannheim/tesseract/wiki
#   Install Arabic data: Ta tessdata_fast/ara.traineddata
#   If Tesseract isn't on PATH, set in backend/.env:
#     TESSERACT_CMD="C:/Program Files/Tesseract-OCR/tesseract.exe"
#     TESSDATA_PREFIX="C:/Program Files/Tesseract-OCR/tessdata"

# Frontend
cd ..\frontend
npm install
```

### macOS

```bash
brew install tesseract tesseract-lang
cd backend
python3.14 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m playwright install chromium
alembic upgrade head
python -m seed.load_institutions
python -m seed.load_taxonomy
cd ../frontend
npm install
```

### Linux (Debian / Ubuntu)

```bash
sudo apt-get install tesseract-ocr tesseract-ocr-ara
cd backend
python3.14 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m playwright install --with-deps chromium
alembic upgrade head
python -m seed.load_institutions
python -m seed.load_taxonomy
cd ../frontend
npm install
```

### Environment variable (required for the crawler)

Any crawler invocation refuses to start without `VERITY_CONTACT_EMAIL`
set — CLAUDE.md rule 5 (identify honestly). Add to `backend/.env`:

```
VERITY_CONTACT_EMAIL=you@example.com
```

## Run

```bash
# Backend API (port 8000)
cd backend
python -m uvicorn app.main:app --port 8000

# Frontend (port 5173, proxies /api -> :8000)
cd ../frontend
npm run dev
```

Dashboard at http://localhost:5173.

## Checks

```bash
python scripts/check.py
```

Runs backend ruff + mypy + pytest and frontend typecheck + lint + test
(the latter three only when `frontend/node_modules` is already
installed). Returns non-zero on any stage failure.

## CLI entry points

See [`docs/RUNBOOK.md`](docs/RUNBOOK.md) for the common operational
scenarios. The CLI commands:

```
python -m app.cli crawl ...               # live crawler
python -m app.cli gaps wayback            # list Wayback captures (no download)
python -m app.cli gaps email-drafts       # write per-institution email drafts
python -m app.cli ingest-approved         # download URLs in data/approved_downloads.json
python -m app.cli ingest-manual           # ingest PDFs from storage/manual_inbox/<slug>/
python -m app.cli process ...             # score reports under current taxonomy
python -m app.cli write-qa                # regenerate docs/PROCESSING_QA.md
python -m app.cli export-evidence-sample  # seeded random match sample for review
python -m app.cli reproduce --sample N    # re-score N reports and assert identical output
```

## Citations

Four approved sources underpin the methodological claims:

- Loughran and McDonald (2011) on dictionary methods and sentiment in
  10-Ks.
- Berg, Kölbel and Rigobon (2022) on ESG rating-agency divergence.
- Schimanski et al. (2024) on NLP measurement of ESG communication.
- Ferjancic et al. (2024) on the inflation effect of including the
  financial-statements section.

Anything in the docs stated as fact outside those four carries
`[TO VERIFY]`.
