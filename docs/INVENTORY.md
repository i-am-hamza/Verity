# Inventory of unresolved items

Generated 2026-10-03. Session 7 hardening pass — this is the full list
of what's unverified, flagged for review, or open-gap under the
current taxonomy (`4948c004…`).

The project is NOT at release and `scripts/check.py` deliberately does
not fail on these — the gate goes in before submission, not tonight.

## [TO VERIFY] claims in documentation

Grep across `docs/*.md` for the exact string `[TO VERIFY]`:

- `docs/LIMITATIONS.md` — three items, all methodological:
  - whether the financial-statements exclusion boundary our detector
    draws coincides with Ferjancic et al. (2024)
  - per-term GRI / SASB provenance pointer for every taxonomy entry
  - direction and magnitude of the LLM-vs-dictionary gap in Schimanski
    et al. (2024) against this specific taxonomy

## [CITATION NEEDED] markers

Zero. Everything that is currently stated as fact either cites one of
the four approved sources or carries `[TO VERIFY]`. If a reader sees a
claim that neither cites nor flags, that is itself a reportable issue.

## needs_review source_documents (not superseded)

| source   | count | note |
|----------|------:|------|
| crawler  |     3 | Pre-Session-6 colleague-ingest flow surfaced three year-mismatch flags from Session 2/3b. |
| manual   |    10 | Mostly colleague PDFs whose first-three-pages text disagrees with the filename year (year_mismatch); one is Air Arabia FY2021 at 22 pages. |
| wayback  |    45 | The post-fix Session 5 remainder: picker chose a document that validates OK but isn't annual/integrated (short summaries, interim statements, exchange-side filings with the correct cover but wrong report-type phrasing). |

## processing_review_status = needs_review reports

Six reports under the current taxonomy. Reasons from
`Report.processing_review_reason`:

- 1 "heavily scanned" (`emirates-nbd-pjsc FY2023` and one from Session 6
  reprocess) — OCR fraction over the 40% cap, body text too sparse.
- 2 outlier flags (very low Latin word count, high Arabic ratio) that
  came through the QA pass.
- 3 single-year reports (`advanced-petrochemical FY2024` etc.) with
  text-year inconsistency the Session 6 in-window-expected-year rule
  cleared for scoring but still carries the review tag for audit.

Full list is in `docs/PROCESSING_QA.md`.

## Open gap rows

| reason       | count |
|--------------|------:|
| not_found    |    89 |
| unreachable  |     5 |

The 94 open gaps are the per-FY cells for the 17 institutions in the
"not yet covered" bucket plus a handful of years for institutions that
are partially covered. `docs/GAP_REPORT.md` lists them per
institution + FY with next-tier action.

## Audit script findings worth flagging

Session 7's `scripts/audit_hard_limits.py` output (full run captured in
my hardening report) raised two categories that need honest reading:

- **46 "post-block" rows in crawl_log.** These are NOT network
  violations — the Fetcher's `_blocked` set correctly refuses to re-
  request a blocked host (verified in `app/crawler/fetch.py`); the log
  entry is the Fetcher recording a would-have-been-made attempt with
  `outcome="blocked"` before any socket opens. The audit script cannot
  distinguish "network request made" from "pre-blocked log line" from
  the schema alone. A later session should extend `CrawlLog` with a
  dedicated `pre_blocked_skip` outcome to make this unambiguous.
- **92 "sub-2s delta" rows.** `CrawlLog.at` is a timezone-aware
  TIMESTAMP whose SQLite representation rounds to the second. Actual
  delays could be anywhere from 1.0s to 2.9s; the subset showing
  `delta=0.00s` (same-second logging) is strongly suggestive of a
  burst, but the current audit cannot prove the actual sub-second
  interval. A Playwright-render path that bypasses the Fetcher's
  `_wait` helper is the most likely source — flagged for a Session 8
  code review (see [BACKLOG.md](BACKLOG.md)).
