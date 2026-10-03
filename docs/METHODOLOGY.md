# Methodology

How Verity measures what it measures, with the live-system figures that
make each claim auditable. The numbers in this document were pulled
directly from the database and `config/verity.toml` on 2026-10-03
against taxonomy version
`4948c00426fa70118328478fe6e1d782c981cb65024378fe11af6a561faef340`
(created 2026-10-02) and pipeline version `0.3.0`.

## 1. The construct

**Verity measures disclosure — not sentiment, and not performance.**
A score captures how thoroughly a company talks about Environmental,
Social, and Governance topics in its annual (or integrated) report. It
does not try to tell you whether the company does those things well.

The defining property is polarity-blindness. "Governance needs to be
improved" and "Our governance framework is best-in-class" score
identically: both contain the term *governance* in context, both are
counted. The design rationale is empirical. Loughran and McDonald
(2011) showed that general-finance sentiment dictionaries
mis-classify boilerplate and formulaic language in US 10-Ks at a rate
that swamps whatever polarity signal they recover. Verity sidesteps
the problem by not attempting sentiment classification at all; what it
produces is the density of ESG-related *disclosure*.

## 2. The formula

Every stage is a plain arithmetic operation over counts of matches
against the taxonomy. The composite method implemented in the
scoring layer (`backend/app/services/scoring.py`) is **raw_sum**:
there is no configuration toggle, no z-score alternative in code or
config — one composite method, applied consistently.

```
category density = (sum of term.weight * term.count in the category)
                 / Latin-script word count of the report * 1000

pillar score     = sum of category densities whose category.pillar
                   matches that pillar
                   (today each pillar has exactly one category, so
                   pillar score == category density; the formula is
                   structured for future category splits)

composite        = sum over categories of
                     (category.density * category.weight)
                   — raw_sum method, confirmed in scoring.py:52

institution score = mean of composite across the fiscal years for
                    which the institution was actually scored.
                    `years_covered` is reported alongside every
                    institution-level mean because a 1-year mean and
                    a 6-year mean are different confidence levels and
                    must never be presented identically.
```

### Known consequence of the raw_sum composite

Pillars with more terms and denser real-world usage can mathematically
dominate a summed composite because every match contributes directly
to the pillar density, and the composite then sums pillar densities
without re-normalisation. In the current data under the Governance
pillar's 27 terms, Environmental's 22 and Social's 18, the cumulative
weighted-density sums across the 130 scored reports under the current
taxonomy are:

| Pillar        | Σ (density × weight) across scored reports |
|---------------|---:|
| Governance    | 189.93 |
| Environmental | 167.12 |
| Social        | 47.96 |

Governance leads Environmental by about 14% and Social by about 4×.
The ordering holds within each sector:

| Pillar        | Mean weighted density, Financial cohort | Mean weighted density, Non-financial cohort |
|---------------|---:|---:|
| Governance    | 1.704 | 1.415 |
| Environmental | 1.566 | 1.179 |
| Social        | 0.382 | 0.370 |

If the taxonomy had a term that an institution routinely uses but did
not include it, that institution's composite would under-count the
pillar it belongs to. The sensitivity analysis in Section 5 is partly
there to tell us how much weight that risk carries at the current
taxonomy.

## 3. Taxonomy

**Source**: GRI Standards (Universal + Topic Standards 300 / 400
series) and SASB's Commercial Banks + Financial Sector Standards.
Per-category sourcing notes live in
`backend/seed/taxonomy_starter.json` as `_sourcing_note` fields, with
the specific GRI code or SASB disclosure topic that justified each
block of terms. Per-term GRI/SASB pointers are not uniformly recorded
and are marked `[TO VERIFY]` in `docs/LIMITATIONS.md`.

**Current state** (hash `4948c00426fa…`):

| Pillar        | Category weight | n terms |
|---------------|---:|---:|
| Environmental | 1.0 | 22 |
| Social        | 1.0 | 18 |
| Governance    | 1.0 | 27 |
| **Total**     |     | **67** |

**Evolution** — three versions, driven by evidence rather than assumption:

| Version | Created | n terms | Pillar match-count ratio E : S : G (match_evidence rows across scored reports) |
|---------|---------|---:|---|
| v1 `53c33ed8…` | 2026-09-30 | 50 | 403 : 348 : 2,601 (≈ 1 : 0.86 : 6.45) |
| v2 `b08bb207…` | 2026-10-02 | 63 (+13) | 2,214 : 761 : 2,853 (≈ 1 : 0.34 : 1.29) |
| v3 `4948c004…` | 2026-10-02 | 67 (+4) | 11,698 : 3,197 : 12,227 (≈ 1 : 0.27 : 1.05) |

v1's roughly 6 : 1 : 0.9 Governance-to-Environmental-to-Social match
ratio — observed on the first batch of 23 scored reports — looked
like a strong finding about disclosure patterns. A **recall audit**
against a sample of six real reports (`docs/RECALL_AUDIT.md`) tested
that interpretation by counting raw whole-word occurrences of ~70
ESG-adjacent candidate terms that were NOT in v1. The audit found
that the gap was taxonomy coverage, not disclosure reality: the
candidates `ESG`, `sustainability`, `GRI`, `net zero`, `zakat`, `CSR`,
`financial literacy`, `accessibility`, `supply chain`, `fraud`,
`remuneration committee`, `ESG committee` and `anti-money laundering`
each appeared tens to hundreds of times in reports that v1 was
scoring as near-zero on Environmental or Social.

Those 13 terms were added in v2 and the match ratio contracted to
roughly 1 : 0.34 : 1.29. A follow-up sample classified "sustainable"
(73% ESG precision at the raw-word level) and "nature" (33% precision
— dominated by accounting boilerplate like "nature of the
transaction") in `docs/SAMPLE_SUSTAINABLE_NATURE.md`. On that
evidence we added four narrow phrases in v3 — `sustainable
development`, `sustainable financing`, `nature-positive`,
`nature-related` — instead of the bare words. The resulting ratio is
roughly 1 : 0.27 : 1.05: Environmental and Governance now at parity,
Social still proportionally smaller.

This is a **tested** taxonomy — the pillar skew we observed in v1 was
treated as a hypothesis, falsified by a parallel probe, and corrected
in subsequent versions. It is not asserted as "the right taxonomy".
The follow-up work (sector-specific overlays, Arabic parallel
taxonomy) is in `docs/BACKLOG.md`.

## 4. Cleaning and matching

### Longest-match-wins (the "nested phrase" problem)

The taxonomy intentionally includes both specific and general forms
of the same concept — e.g. `corporate governance` and `governance`;
`internal control over financial reporting` and `internal control`.
Without arbitration, the sentence "The corporate governance framework
was reviewed" would count both the long and the short phrase,
double-counting the same disclosure. Verity resolves this with
**longest-match-wins** across all spans in a sentence
(`backend/app/services/matcher.py`, backed by
`spacy.util.filter_spans`): when two matched spans overlap, only the
longer survives.

The alternative `all` matching mode is retained as a diagnostic (set
via `[pipeline].matching_mode` in `config/verity.toml`) so a human
reviewer can see how much overlap exists. Across the sensitivity
analysis's `all_mode` switch test
(`docs/SENSITIVITY_SUMMARY.md` §3), Spearman correlation vs the
longest-wins baseline is 1.000 financial / 0.996 non-financial — the
ranking is essentially identical.

### Latin-script-only word count denominator

The density denominator counts **Latin-script tokens only**, defined
as any whitespace-delimited token containing at least one `[A-Za-z]`
character. The reason is a specific class of pathology that
alternatives create: many Middle East annual reports are bilingual,
with substantial Arabic sections. If the denominator counted Arabic
words, a report that discussed the same ESG topics equally
thoroughly in English and in Arabic would score as half the density
of its English-only sister report, because the taxonomy is English
and only matches English phrases. Latin-only denominator keeps the
density comparable across bilingual and monolingual reports.

### Financial-statements section excluded from scoring

Everything from the first page containing an "Independent Auditor's
Report" marker (or the Arabic equivalent, or any of several
`statement of financial position` / `notes to the financial
statements` phrases listed in `[pipeline].financial_statement_boundary_markers`)
to the end of the document is excluded from matching. Ferjancic et
al. (2024) find that including the financial statements and notes
inflates raw counts of ESG-adjacent terms (risk, control, governance)
without a corresponding change in narrative disclosure. The excluded
page range is tracked per report in
`Report.financial_statements_excluded_pages`.

### Contents-page and repeated-header/footer removal

Running headers, running footers, and table-of-contents pages are
dropped from matching. These are both ToC chips (section labels like
"Context", "Overview", "ESG Report" that appear on every page as
navigation) and page-furniture (the small "Annual Report 2024 | 25"
header that recurs on every page). The repeated-line rule removes
any line whose digit-normalised form appears on at least 30% of the
report's pages, provided the normalised line contains at least one
letter (so bare table-cell numbers like `120,000` or `0` are not
counted as "repeated boilerplate" — a tightening that landed in
Session 5 after an early version inflated the removed-line count by
~20× by lumping numeric cells in with headers).

**Al Rajhi Bank — worked example of a validated filter.** The
Session 6 sensitivity analysis found exactly one real rank-move
under the `repeat_off` switch test: Al Rajhi's financial-sector rank
jumped from 7 to 2 (−5) when repeated-line removal was disabled. The
natural suspicion was that the filter was removing real content. We
investigated:

- Top five "repeated lines" dropped from Al Rajhi's reports (aggregate
  page count across the 2020-2025 reports):
  1. `Context` — 1,013 pages
  2. `Overview` — 1,011 pages
  3. `Supplementary` — 1,010 pages
  4. `Financial Statements` — 840 pages
  5. `ESG Report` — 798 pages
- Each of these is a per-page navigation chip in Al Rajhi's
  integrated-report layout: the section-tabs sidebar lists every
  chapter title on every page. The "ESG Report" chip in particular,
  once the taxonomy added `ESG` as a term in v3, would inject
  roughly 800 phantom E matches per Al Rajhi report if left in.
- Removing them is correct. The sentences in Al Rajhi's actual ESG
  narrative — the ones that should score — do not contain those
  words as isolated navigation chips.

The filter does what it is supposed to do; the rank-7 position is
the honest one. This is documented in `DECISIONS.md` as the "repeat
filter validated" entry. The `all_mode` and `toc_off` switches
produce no Spearman movement at all (≥0.996 both sectors; 1.000 for
`toc_off`); `repeat_off` produces the one validated finding.

### OCR cap

Pages lacking native text are OCR'd via Tesseract. If more than
`[pipeline].ocr_max_page_ratio` (0.40) of the pages in a report would
need OCR, the report is marked `processing_review_status =
needs_review` with reason "heavily scanned" and skipped — a
scanned-image report has unreliable Latin-token counts anyway and
would under-count density relative to peers with native text.

## 5. Coverage and limitations

Numbers in this section were queried against the live database on
2026-10-03.

### Current scope and coverage

- **60** active institutions in scope.
- **44** of 60 have at least one scored report under the current
  taxonomy — **16** do not.
- **130** scored reports total under the current taxonomy.
- **6** reports carry `processing_review_status = needs_review`
  (threshold / IQR / heavily-scanned flags). **58** source documents
  are still `needs_review` and not scored (3 crawler + 10 manual + 45
  wayback). **94** open gap rows across the (institution × fiscal
  year) matrix (89 `not_found`, 5 `unreachable`).

### The 17 institutions not yet scored (one is flagged, not unranked)

| Reason bucket | n | What it means |
|---|---:|---|
| A — No file in storage | 12 | Never crawled under the current scope, no colleague file. Mostly Saudi non-financials (telecoms, cement, petrochemicals). |
| B — Wayback picks only, none passed as annual/integrated + auto_ok | 4 | The Session 5 Wayback picker returned candidates whose `report_type` detector returned "unknown" from first-three-pages text (typically Arabic-only cover pages on exchange hosts). |
| D — Below the 30-page minimum | 1 | `air-arabia-pjsc` FY2021 — a genuine **22-page** summary report (confirmed by inspection: page 1 reads "ANNUAL REPORT 2021"), caught by the `MIN_ANNUAL_REPORT_PAGES` threshold that distinguishes annual reports from highlights decks. |

**`rabigh-refining-petrochemical-co` FY2020 is scored but visibly
flagged** as a known extraction artifact in every output (CSV
`data_quality_flag=sentence_segmentation_artifact`, asterisk +
footnote on printed tables, dedicated entry in `DECISIONS.md`
2026-10-02 explaining why). The pipeline recorded `matches_count=1`
and composite 0.048 on 100 pages / 20,963 Latin words / financial-
statements boundary at page 58. A raw-text probe of the scored page
range (pages 1-57) found ≈ 35 taxonomy-term occurrences the pipeline
missed (26 raw hits of "board of directors" with 0 matched). The
PDF's board-bio layout breaks spaCy's sentence segmenter so most
sentences never reach the matcher. The row is kept, not silently
dropped or silently included.

### Measurement limits (as distinct from the construct boundary)

**Disclosure, not performance.** Section 1 established this as the
construct. Stated here again as a limitation: a high composite score
means "writes extensively about ESG topics", not "has strong ESG
performance". A low score likewise does not establish weak
performance. Any downstream use must preserve the distinction.

**Finance-sector taxonomy applied across all 60 institutions,
including non-financials.** The taxonomy is sourced from GRI
Universal + SASB Financial Sector Standard. Applied to the current
scored set, the non-financial cohort (26 institutions) shows mean
weighted densities of Env 1.179 / Soc 0.370 / Gov 1.415; the
financial cohort (18 institutions) shows Env 1.566 / Soc 0.382 / Gov
1.704. The pattern is preserved — Governance leads Environmental by
roughly 20% in both sectors, Social is small in both — but the
non-financial scale is roughly 25% lower, consistent with either
(a) non-financial companies producing less dense ESG disclosure in
these particular terms, or (b) the taxonomy under-sampling the
industry-specific terminology (product safety for petrochem, water
intensity for cement, network reliability for telcos) that SASB's
sector-specific standards cover. We cannot distinguish (a) from (b)
without a sector-specific taxonomy overlay. The within-sector rank
is the one safe to present; cross-sector rank carries this caveat
and the dashboard shows a persistent "Cross-sector comparison: read
with care" banner when the cohort filter is set to "All".

**English-only scoring of bilingual reports.** The Latin-only
denominator correctly handles bilingual reports where English and
Arabic sections exist in parallel. For reports that are
substantially Arabic-only, the behavior is also correct but needs
explaining: the taxonomy is English, so an Arabic-only PDF will
produce near-zero matches and near-zero Latin word count. The
Session 5-era case — Emirates NBD FY2023 scoring 0.000 on an
Arabic-only Wayback-sourced file — demonstrated this working as
designed. In the current data that specific case has been resolved
by the Session 6 colleague-ingest flow, which supplied an English PDF
that superseded the Arabic file (Emirates NBD FY2023 now scores
composite 4.308 on 77,713 Latin words). The remaining Arabic-dominant
files are caught by the `low_latin_word_count_threshold` (5,000) and
the `high_arabic_ratio_threshold` (0.50 of pages mostly Arabic) and
appear in `docs/INVENTORY.md` as `needs_review` rather than being
scored. The downside is that institutions whose only available
report is Arabic-only remain uncovered — a parallel Arabic taxonomy
is the proper fix and is on the backlog.

**Report-type classification is validated, not assumed correct.**
A worked example from Session 6: four reports (Maaden FY2025 and
National Bank of Bahrain FY2021, FY2024, FY2025) were initially
classified as `sustainability` and excluded from scoring because
their covers prominently mentioned the word "Sustainability" — an
early regex priority gave sustainability precedence over annual.
These were genuine annual reports whose covers happened to lead with
sustainability wording. The regex priority was reordered
(annual > integrated > sustainability > financial statements), each
file was re-validated against the stored bytes, and all four moved
to `report_type ∈ {annual, integrated}` and scored successfully. The
fix is in `backend/app/crawler/validate.py`; the validator tests
pin the new behaviour. This is a worked example of catch-and-fix,
not an abstract risk — the current pipeline has it right because the
earlier version was wrong and we corrected it.

### Sensitivity (from `docs/SENSITIVITY_SUMMARY.md`)

Tested on the 42 cleanly-scored institutions (43 scored minus Rabigh,
whose score is a flagged artifact and whose "sensitivity" would just
measure the extraction bug).

- **Weight jitter**: term weights multiplied by U(0.8, 1.2) across
  1,000 seeded draws. Kendall tau vs the baseline ranking has
  median = 0.985 (5-95% = [0.970, 0.985]) in the financial sector,
  and median = 0.973 (5-95% = [0.947, 0.993]) in non-financial. Per-
  institution rank intervals are 0-2 ranks wide. Rankings are
  strongly robust to a ±20% perturbation of every term weight.
- **Equal weights** (all term and category weights set to 1.0).
  Spearman vs baseline is **0.998** financial, **0.997**
  non-financial. **Zero** institutions move three or more positions.
  This is **double-edged** and must be stated honestly as such: on
  one hand it demonstrates robustness, on the other hand it means
  the current per-term weight scheme carries little independent
  signal at the current sample size and taxonomy. If weights were
  doing substantial work, equal-weighting would move things; it
  doesn't. The density-of-matches signal dominates the composite,
  which is a defensible position — but it means the weight choices
  shouldn't be oversold.
- **Switch tests**: `toc_off` and `all_mode` produce Spearman ≥ 0.996
  both sectors and no rank movement ≥ 3. `repeat_off` produces the
  single rank move (Al Rajhi 7 → 2 financial, Spearman 0.961); this
  is the "repeat filter removing boilerplate" finding documented
  above, not a defect.
- **Single-year institutions and compounding volatility.** Nine of
  the 42 institutions have `years_covered = 1`. Sensitivity testing
  found that none of them shows a jitter interval wider than
  cohort/3 — the single-year × high-volatility compounding we were
  watching for does not occur in the current data. Confidence in a
  single-year mean is still lower than in a multi-year mean by
  construction, and the leaderboard displays `years_covered`
  alongside every mean to make the distinction visible.

### Ratings disagree with each other too

Verity has limitations. So does every other construct in this
space. Berg, Kölbel and Rigobon (2022) show that major ESG rating
agencies (MSCI, Sustainalytics, Refinitiv, S&P Global, KLD, MSCI
IVA) disagree substantially even on the same firms — the authors
report pair-wise correlations of roughly 0.3-0.6 between agencies
and attribute the gap to differences in scope, measurement and
weighting. Verity's weighting scheme (equal pillar weights, equal
term weights within pillar, equal category weights) is deliberately
transparent so that the exact source of any disagreement with an
external rating is auditable, not a black box. Framed within
Berg-Kölbel-Rigobon's own result: no construct of ESG today is
"calibrated" against an uncontested external truth — Verity's
disclosure-density measurement is one explicit choice in that
space, with the limitations above declared rather than hidden.

### No benchmark validation has been performed yet

Verity composites have **not** been correlated against any external
ESG rating (MSCI, Sustainalytics, LSEG, Bloomberg, or the Islamic
Finance Services Board). The reason is practical: no ratings data
has been obtained. The dashboard carries an explicit upload-prompt
on `/benchmark` for exactly this purpose; the server-side CSV
validation + import flow is in `docs/BACKLOG.md`. Treat the
leaderboard as a measurement of disclosure density on this taxonomy
only until such a comparison is completed. Any claim that Verity's
rank "agrees" or "disagrees" with an agency rating is unsupported by
the current state of the project.

**NLP methods beyond dictionaries.** Schimanski et al. (2024) report
that fine-tuned climate-NLP classifiers outperform dictionary
methods on climate-disclosure classification tasks. Verity's choice
of a dictionary approach is a transparency-and-reproducibility
decision, not an argument that dictionaries dominate the literature.
Direct magnitude of the LLM-vs-dictionary gap on this specific
taxonomy is `[TO VERIFY]` and recorded as such in
`docs/LIMITATIONS.md`.

## 6. Citations

- Berg, F., Kölbel, J. F., and Rigobon, R. (2022). Aggregate
  confusion: The divergence of ESG ratings. *Review of Finance*,
  26(6), 1315-1344.
- Ferjancic, U., Ichev, R., and Lončarski, I. (2024). What can we
  learn about ESG from financial disclosures? *International Review
  of Financial Analysis*, 96, 103669.
- Loughran, T. and McDonald, B. (2011). When is a liability not a
  liability? Textual analysis, dictionaries, and 10-Ks. *Journal of
  Finance*, 66(1), 35-65.
- Schimanski, T., Reding, A., Reding, N., Bingler, J., Kraus, M., and
  Leippold, M. (2024). Bridging the gap in ESG measurement: Using
  NLP to quantify environmental, social, and governance
  communication. *Finance Research Letters*, 61, 104979.

Any claim in this document stated as fact and not tied to one of
these four citations is marked `[TO VERIFY]` and should be verified
against a specific source before being cited externally.
