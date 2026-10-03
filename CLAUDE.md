# Verity: project rules

Text-based ESG disclosure scoring for Middle East companies, built for a PhD.
Scores annual reports on how thoroughly each company DISCLOSES Environmental,
Social and Governance topics. It is not a sentiment score and not a performance
score.

## Method (do not change unless asked)
- Score = weighted phrase matches per 1,000 words, per category. Categories roll up
  into pillars (Environmental / Social / Governance) through Category.pillar.
  Composite = sum(category density x category weight).
- Sentiment is ignored on purpose: "governance needs to be improved" counts the
  same as "governance is strong".
- The denominator counts only Latin-script words (tokens with at least one Latin
  letter), because the taxonomy is English. Arabic text must not dilute density.
- Every match stores page number and sentence. No score without evidence.
- Every score row stores taxonomy_version and pipeline_version.
- The financial statements section (from the independent auditor's report
  onward — statements of financial position, comprehensive income, cash
  flows, changes in equity, and the accompanying notes) is EXCLUDED from
  scoring. Those pages are tracked on source_documents.includes_financial_statements
  and reported separately, never mixed into the disclosure density. Reason:
  Ferjancic et al. (2024, Int. Review of Financial Analysis 96, 103669)
  find that including the financials inflates raw counts of ESG-adjacent
  terms (risk, control, governance) without a matching change in narrative
  disclosure, so a score that includes them measures something other than
  what "how thoroughly does the company discuss ESG" is supposed to mean.

## Data acquisition: hard limits (never relax, never work around)
1. Public pages only. No login, no account creation, no credentials, ever.
2. No paywall bypass. No CAPTCHA or bot-check solving or evasion. No rotating
   IPs or user agents to dodge a block. Obey robots.txt.
3. If a site blocks you, stop for that domain, log it, move on. It goes to the
   manual queue.
4. Aggregators: read the terms first. If one requires an account or bans automated
   download, exclude it and record why in docs/DATA_SOURCING_LOG.md.
   sustainabilityreports.com is excluded for exactly this reason.
5. Identify honestly: a descriptive User-Agent with a contact email from the env var
   VERITY_CONTACT_EMAIL (refuse to run if unset). At least 2 seconds between requests
   to one domain, one in-flight request per domain.
6. Every downloaded file gets a manifest row: source_url, final_url, http_status,
   retrieved_at (UTC), sha256, bytes, content_type. No manifest row means the file
   does not exist as far as the pipeline is concerned.
7. Never invent a URL, report, year, score, benchmark rating or citation. If you
   cannot find it, it goes in the gap report.
8. Agency ESG ratings (MSCI, Sustainalytics, LSEG, Bloomberg) are never fetched by
   code. The human supplies them as CSV; code only validates and imports.
9. Never send emails or messages. Drafts only.

## Rules
1. Config over code: institutions, years, taxonomy and report-type rules live in
   data files and config/verity.toml, never hard-coded.
2. Every pipeline stage is resumable and idempotent, keyed by sha256.
3. Run `python scripts/check.py` (ruff, mypy, pytest, and later the frontend
   checks) before reporting any task done.
4. Network code is tested against REAL saved fixtures (real HTML, dated), not
   invented ones. Invented fixtures are only for pure logic.
5. Report honestly: say what you ran, what passed, what you could not verify.
   Never say "done" about something you did not execute.
6. Python: type hints, no bare except. TypeScript: strict, no any, no ts-ignore.
   Frontend: design tokens only, no hardcoded colours, spacing or radii.
7. Every chart has Export PNG and Export CSV.
8. Keep DECISIONS.md: one line for every judgement call you make.
9. Work inside the repo. Use a virtualenv. No global installs, no deleting outside
   the repo.
