# Run book

Operational scenarios. Every step lists the exact command and the file
or table it touches; nothing happens by magic.

## Add a new institution

1. Add the row to `data/List of Companies.xlsx` (or the current
   `Updated List of Companies.xlsx`): rank, name, ticker (bare number
   or exchange-prefix form), country, market cap, industry.
2. Reload the institution registry from the spreadsheet:
   ```
   cd backend
   python -m seed.load_institutions
   ```
   This is append-only — existing institutions are matched by ticker
   and have their name/industry/rank refreshed; new rows are added.
3. If the institution has a known IR URL, add an entry to
   `data/ir_sources.json` with `ir_status: "verified"` and
   `ir_url: ...`. Without this, the crawler won't try the institution.

## Add a new fiscal year

1. Edit `config/verity.toml`:
   ```
   [schedule]
   years = [2020, 2021, 2022, 2023, 2024, 2025, 2026]
   ```
2. Rerun the crawler for just the new year:
   ```
   python -m app.cli crawl --wave all --years 2026
   ```
3. Re-process everything under the new year window (idempotent — only
   the new reports get scored, old ones hit the dedupe check):
   ```
   python -m app.cli process --scope all
   ```

## Edit the taxonomy and reprocess

1. Edit `backend/seed/taxonomy_starter.json`. Add new terms to an
   existing category or add a whole category block.
2. Load — this registers a NEW taxonomy version (hash changes) and
   APPENDS the new terms to existing categories. Weights of existing
   terms are untouched; weight edits require a new category/term pair:
   ```
   python -m seed.load_taxonomy
   ```
3. Re-score every report under the new taxonomy version. `--force`
   bypasses the idempotency check so existing Reports get new
   CategoryScore + MatchEvidence rows under the new version. Old rows
   stay — the DB is append-only on scoring:
   ```
   python -m app.cli process --scope all --force
   ```
4. Refresh the QA tables and the evidence sample:
   ```
   python -m app.cli write-qa
   python -m app.cli export-evidence-sample
   ```
5. Rebuild the leaderboard CSV + Markdown so dashboards pick it up:
   ```
   python backend/scripts/build_leaderboard.py
   ```

## Load benchmarks

Not wired tonight; the backend ships the empty-state prompt. When the
agency-CSV import flow lands (Session 8), the shape will be:

```
institution_slug, fiscal_year, agency, pillar, rating
```

See [`docs/BACKLOG.md`](BACKLOG.md) for the deferred validation + import
flow.

## Export data

- Leaderboard (both the summary + the long tidy form):
  ```
  python backend/scripts/build_leaderboard.py
  ```
  → `exports/leaderboard_summary.csv`, `exports/scores_long.csv`
- Evidence sample (seeded, reproducible, 50 per pillar by default):
  ```
  python -m app.cli export-evidence-sample
  ```
  → `exports/evidence_sample.csv`
- Sensitivity analysis (the Session 6 outputs are frozen; regenerate
  only when weights or the switch defaults change):
  ```
  python backend/scripts/sensitivity_analysis.py
  ```
  → `exports/sensitivity_summary.csv` + `docs/SENSITIVITY_SUMMARY.md`
- Dashboard tables and charts: use the Export CSV / Export PNG buttons
  on each view. CSVs carry a header comment line with taxonomy version
  and snapshot date.

## Crawler got blocked

CLAUDE.md rule 3: stop for the domain, log it, move on. The Fetcher
implements this automatically — once a host is in its in-run
`_blocked` set, subsequent requests to the same host return
`outcome="blocked"` without touching the network. You do not retry.

What TO do:

1. Confirm the block in `data/DATA_SOURCING_LOG.md`. Add a line
   dated UTC with the domain, outcome, and the specific response
   signature that tripped detection.
2. Move the institution to a different tier (Wayback or manual drop).
3. For a Tier 3 (Wayback) attempt, see the next scenario.

What NOT to do: rotate User-Agent, rotate IP, solve CAPTCHA, or add a
hand-rolled retry loop. The static test
`backend/tests/test_crawler_hard_limits.py` will fail the build if any
of those appear in the crawler code.

## Fill a gap via Tier 3 (Wayback)

```
cd backend
python -m app.cli gaps wayback
```

Writes `docs/WAYBACK_CANDIDATES.md`. For each (slug, FY) with gap row,
the CDX API is queried for the host; the per-FY matcher is
publication-window-aware (date 2-7 months after FY-end).

If candidates are present, hand-pick (or run `scripts/pick_wayback.py`
to auto-pick with the URL-year rule from Session 5), then:

```
python -m app.cli ingest-approved
```

That reads `data/approved_downloads.json`, downloads each URL (with the
`id_` identity modifier — Wayback would otherwise serve the HTML viewer
wrapper), validates, and writes a SourceDocument row with
`source=wayback`. Then rescore:

```
python -m app.cli process --scope all
```

## Fill a gap via Tier 4 (manual drop)

1. Drop the PDF into `storage/manual_inbox/<slug>/<filename>.pdf`.
   Optional sibling `<filename>.note` captures the human context.
2. Ingest. The flow extracts the fiscal year from the filename first,
   then falls back to in-document detection — this cross-check
   prevents a Vision 2030 reference from overwriting the real year:
   ```
   python -m app.cli ingest-manual
   ```
3. If a prior crawler/wayback SourceDocument existed for the same
   (institution, FY), the manual row supersedes it (older row kept with
   `superseded_by_id` set; batch_runner filters it out of scoring).
4. Rescore:
   ```
   python -m app.cli process --scope all
   ```

## Verify reproducibility

```
cd backend
python -m app.cli reproduce --sample 3
```

Picks three random scored reports under the current taxonomy and
pipeline, re-runs the CPU-side of the pipeline against each PDF, and
asserts that recomputed match counts per (term, page) are byte-identical
to what's stored in `MatchEvidence`. Non-zero exit on any mismatch. A
row is written to the `runs` table with git commit, taxonomy +
pipeline versions, and hashes of `config/verity.toml` and
`storage/manifest.jsonl`.

## Audit provenance and hard limits

```
python backend/scripts/audit_provenance.py
python backend/scripts/audit_hard_limits.py
```

Both exit 0 only when clean. Session 7's provenance audit on the
current DB passes (zero violations); the hard-limits audit flags 46
"post-block" rows that are honest Fetcher no-ops and 92 "sub-2s delta"
rows caused by second-precision timestamp rounding — read the notes in
[`docs/INVENTORY.md`](INVENTORY.md) before concluding anything about
them.
