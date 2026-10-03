# Backlog

Deferred work, grouped by where it was identified. Nothing in this file
is a bug — if something is broken we fix it. These are intentional
"not yet" items.

## Deferred in Session 7 (dashboard build)

- **Benchmark CSV upload: validation + import wiring.** The
  `/benchmark` view ships the empty-state prompt by design;
  `POST /dashboard/benchmark/upload` returns 501. Needs: parse the CSV,
  row-by-row validation, confirm-to-import flow, agency / rating-scale
  model, scatter + rho/r/CI calculation. One session's work; depends on
  a real benchmark CSV first.
- **Taxonomy edit UI → new version → reprocess trigger.** `/taxonomy`
  renders the current version read-only. The edit flow (create a term,
  tweak a weight, save, generates new hash, triggers batch runner) is
  not wired. The DB machinery is in place (append-only versions,
  `--force` reprocessing) — this is UI + API wiring.
- **Playwright E2E matrix.** Smoke `vitest` tests are in place. The
  full suite covering leaderboard filter with URL sync, institution
  page, evidence review flow, coverage drill-down, benchmark upload
  with a bad fixture row, and taxonomy edit creating a new version is
  on hold until the above feature flows exist.
- **axe accessibility pass per route.** Keyboard-nav + skip-link +
  aria-live states are in. Running `@axe-core/playwright` across every
  page is scaffolded by the Playwright infra not shipped tonight.
- **Screenshots at 390 px and 1440 px in both themes** for Overview,
  Institution, Evidence — produced by the Playwright matrix once
  that's in.
- **Bundle code-split.** `vite build` warns at ~900 kB; splitting
  Recharts off into a lazy route-level chunk brings initial payload
  below 500 kB. Not a correctness issue; worth it before deploy.

## Flagged in Session 8 (UI bug sweep)

- **Garbled / reversed Arabic text in Evidence page sentences** (visible on
  e.g. `abdullah-al-othaim-markets` rows). Root cause is PyMuPDF's text
  extraction returning Arabic characters in visual order, not logical order,
  so the string that lands in `MatchEvidence.sentence_text` is already
  reversed before the UI ever sees it. The fix is in the extraction layer
  (apply Unicode bidi algorithm after `page.get_text()` for Arabic
  spans, or switch to `get_text("dict")` which preserves run direction),
  not in the dashboard. Any UI-side CSS `direction: rtl` on a per-sentence
  basis would be papering over the real problem. Scoped for a text-
  extraction session; the matching counts are not affected because the
  taxonomy is English, but the surfaced evidence sentence is misleading
  for the human reviewer.

## Deferred in Session 7 (hardening pass)

- **`CrawlLog` extension: distinguish pre-blocked skips from real
  requests.** Add a dedicated outcome ("pre_blocked_skip") or an
  `action = "no_op"` row so `audit_hard_limits.py` can report true
  network violations unambiguously. Session 7's audit flagged 46
  rows under the current ambiguous schema.
- **Fine-grained timestamp on `crawl_log.at`.** SQLite + the default
  `func.now()` currently rounds to the second, masking sub-2s delays.
  Switching to a microsecond-precision default fixes the audit's
  politeness-delay check.
- **Playwright fetch path through `_wait`.** The `_wait` helper
  enforces the 2-second same-domain floor for the requests-based path.
  Session 7 audit suggests the Playwright render path may bypass it.
  Audit by code review before Session 8.
- **check.py release-gate.** Explicitly NOT wired tonight — the
  project isn't at release. Before submission, add a stage that fails
  if any item in `docs/INVENTORY.md` is unresolved.
- **Clean-database end-to-end rebuild.** Real but belongs before final
  submission, not tonight: drop the DB, run every migration, re-ingest
  from `storage/manifest.jsonl`, re-score, and prove the leaderboard
  reproduces to the same CSV.

## Original research-direction backlog (carried forward)

- **Arabic taxonomy.** The current taxonomy is English. Reports with
  substantial Arabic narrative score ~0 by denominator design. An
  Arabic taxonomy would need: GRI / SASB phrase translations with
  provenance notes, a tokenizer that handles Arabic morphology (not
  the current spaCy `en_core_web_sm` lemmatizer), a parallel scoring
  pass, and reconciliation of the composite score with the Latin-only
  one. Pre-requisite: subject-matter review of the proposed Arabic
  term list.
- **Sector-specific taxonomies.** The current single taxonomy is
  SASB-Financial-Sector-flavoured. Running it on non-financial sectors
  (telcos, petrochemicals, cement) is well below the materiality bar
  SASB sets for those industries. Needs: per-industry
  category/term/weight overlays, UI switch to pick which overlay
  applies, careful handling of the composite comparison across
  industries.
- **Negation-aware scoring.** The current pipeline is explicitly
  polarity-blind (CLAUDE.md Method; Loughran and McDonald 2011).
  Adding negation detection (not sentiment) — "we have NOT established
  a Scope-3 target" scored differently than "we HAVE established" —
  is a separate scope-change that would require a methodological
  justification per the design rules.

## Not on the backlog (deliberately)

- Any form of IP, UA, or CAPTCHA-related evasion. Forbidden by
  CLAUDE.md rules 2-3; blocked by the static test in
  `backend/tests/test_crawler_hard_limits.py`.
- Any paid-search API or account-based aggregator. Forbidden by
  CLAUDE.md rules 1 and 4.
- Sentiment scoring. Discussed and rejected at project design time.
  Dictionary methods against financial text produce more noise than
  signal (Loughran and McDonald, 2011); a replacement would require a
  separate methodology justification.
