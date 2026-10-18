# Verity methodology fact sheet

**Purpose**: factual record for drafting the PhD supervisor methodology brief.
**Query date**: 2026-10-05.
**All database facts** are from live Supabase (Postgres). Each SQL query is pasted
next to its result. Every non-database fact cites file path + line number or a
DECISIONS.md entry. "NOT FOUND" marks items absent from the repo and database.
Code/doc conflicts are flagged explicitly.

---

## 1. Scope

### Institutions in scope

**Query**
```sql
SELECT country, is_financial, COUNT(*) n
FROM institutions WHERE active = true
GROUP BY country, is_financial
ORDER BY country, is_financial;
```
**Result**

| Country | Financial | Non-financial |
|---|---:|---:|
| Bahrain | 1 | 2 |
| Kuwait | 3 | 3 |
| Oman | 4 | 1 |
| Qatar | 1 | 6 |
| Saudi Arabia | 6 | 21 |
| United Arab Emirates | 6 | 6 |
| **Total** | **21** | **39** |

```sql
SELECT COUNT(*) FROM institutions WHERE active = true;
-- Result: 60
```

Source list: May 2024 top-60-by-market-cap Middle East list.
Source: `docs/LIMITATIONS.md` ("Non-measurement limits → Scope").

**Five inactive institutions** (rows kept for audit trail, excluded from all active-scope counts):

```sql
SELECT name, country, is_financial
FROM institutions WHERE active = false ORDER BY name;
```
| Name | Country | Financial |
|---|---|---|
| ALAFCO Aviation Lease and Finance Company | Kuwait | Yes |
| Bupa Arabia for Cooperative Insurance Company | Saudi Arabia | Yes |
| Emaar The Economic City | Saudi Arabia | No |
| Saudi Electricity | Saudi Arabia | No |
| Saudi Kayan Petrochemical Company | Saudi Arabia | No |

Source: DECISIONS.md 2026-10-01 (Session 3b ALAFCO entry) and
`docs/LIMITATIONS.md` ("five were dropped from the active universe").

### Fiscal years covered

`config/verity.toml` line 2:
```toml
years = [2020, 2021, 2022, 2023, 2024, 2025]
```
Six fiscal years. Year 2020 coverage is thin because many FY2020 reports
were published after the project started (source: `docs/LIMITATIONS.md`).

### Accepted document types and how the type is decided

Only `annual` and `integrated` reports are scored.
Source: `config/verity.toml` line 79:
```toml
report_types_scored = ["annual", "integrated"]
```

**Type classification**: `backend/app/crawler/validate.py` function
`_detect_report_type()` (lines 78–96). It runs regex searches on:
- the source filename, AND
- the concatenated text of the first 3 PDF pages.

Priority order (highest wins): annual → integrated → sustainability →
financial_statements → unknown.

Regexes (lines 24–40):
- Annual: `annual\s+report|ال?تقرير\s*ال?سنوي` (case-insensitive)
- Integrated: `integrated\s+(annual\s+)?report|ال?تقرير\s*ال?متكامل`
- Sustainability: `sustainability\s+report|تقرير\s*ال?استدامة`
- Financial statements: `(financial\s+statements|consolidated\s+financial)|ال?(?:قوائم|بيانات)\s*ال?مالية`

If none match: type = `unknown`, `review_status = needs_review`.

**Session 6 priority change** (DECISIONS.md 2026-10-02, leaderboard entry):
Original priority was sustainability > integrated > annual. Changed to annual
first because covers mentioning "Sustainability" alongside "Annual Report" were
misclassified as sustainability reports (worked example: Maaden FY2025, NBB
FY2021/2024/2025).

### Arabic-only reports

Reports with fewer than 5,000 Latin-script words **or** more than 50% of
pages predominantly Arabic are flagged `processing_review_status = needs_review`
by `backend/app/services/qa_report.py` (lines 53–72) and not included in
cross-institution comparisons.

Thresholds from `config/verity.toml`:
```toml
low_latin_word_count_threshold = 5000
high_arabic_ratio_threshold = 0.50
```
Source: `backend/app/services/verity_config.py` lines 52–55.

An Arabic-only document scores near zero by design: the taxonomy is English,
so Latin-script matches are zero and Latin word count is near zero.
Source: `docs/METHODOLOGY.md` §5 ("English-only scoring of bilingual reports").

### Minimum page threshold

`backend/app/crawler/config.py` line 33:
```python
MIN_ANNUAL_REPORT_PAGES = 30
```
Annual or integrated reports under 30 pages are accepted as files but set to
`review_status = needs_review` with reason "may be a summary / highlights"
(`backend/app/crawler/validate.py` lines 163–166).

Worked example: Air Arabia PJSC FY2021 — genuine 22-page summary report, kept
in DB but not scored (source: DECISIONS.md / `docs/LIMITATIONS.md`).

---

## 2. Text pipeline

### PDF extraction

Library: PyMuPDF (`import pymupdf`, `backend/app/services/pdf_extraction.py`
line 23). Session 9 production path: PDFs are fetched as bytes from Cloudflare
R2; `pymupdf.open(stream=bytes, filetype="pdf")` avoids a tempfile round-trip
(`pipeline.py` lines 129–137).

**Native text first**: `page.get_text("text")` per page.
If the returned text is fewer than `ocr_trigger_char_threshold` (20) characters,
the page is treated as a scanned image and OCR is run.
Sources: `pdf_extraction.py` lines 84–96; `config.py` line 27 (default 20).

**OCR**: Tesseract via pytesseract, `ocr_langs = "eng+ara"`, DPI 300.
Source: `pdf_extraction.py` lines 93–96; `config.py` line 31.
Local tessdata at `backend/tessdata/` (ara, eng, osd) pointed to via
`TESSDATA_PREFIX` (DECISIONS.md 2026-09-28).

**OCR cap**: before running the full OCR pass, the pipeline checks what fraction
of pages lack native text (`estimate_ocr_fraction`, `text_quality.py` lines
301–329). If that fraction exceeds `ocr_max_page_ratio` (0.40), the report is
marked `processing_review_status = needs_review` with reason "heavily scanned"
and OCR is skipped.
Source: `pipeline.py` lines 140–164; `config/verity.toml` line 25.

### Text quality cleaning (applied between extraction and matching)

Three switches, applied in this order (`text_quality.py` function
`apply_text_quality`, lines 255–289):

**a) Repeated header/footer removal** (`exclude_repeated_lines = true`).
Any line whose digit-normalised form (all digit runs replaced by `#`) appears
on at least `header_footer_repeat_ratio` (0.30) of pages is removed, provided
the normalised line contains at least one Unicode letter (bare numbers, table
cells, page-number separators are excluded from the pool).
Threshold is `max(2, round(ratio × n_pages))`.
Source: `text_quality.py` lines 55–97; `config/verity.toml` line 17.

**b) Table-of-contents page detection** (`exclude_toc_pages = true`).
Pages are flagged as ToC pages when any of the following is true:
- the first 6 lines contain a known index header (e.g., "table of contents",
  "GRI content index", "SASB index") AND ≥ 3 lines end in a 1–3 digit number;
- ≥ 4 lines contain a dot-leader (`....` or `. . . .`); or
- ≥ 6 lines end in a 1–3 digit number AND ≥ 40% of non-empty lines do so.
Detection scans the first `max(10, 0.15 × n_pages)` pages only.
Detected ToC pages are excluded from matching (not from word-count denominator).
Source: `text_quality.py` lines 100–161; `config/verity.toml` line 6.

**c) Financial-statements boundary** (`exclude_financial_statement_pages = true`).
The first page, after skipping the first 25% of the document, whose
NFKC-normalised text contains any of the configured boundary markers is
identified as the FS start. Everything from that page onward is excluded.
Scanning starts after 25% because auditor-report wording also appears in ToC
entries near the front (source: `text_quality.py` lines 206–236).
Boundary markers (English + Arabic) from `config/verity.toml` lines 37–54:
`independent auditor's report`, `independent auditors' report`,
`report of the independent auditor`,
`consolidated statement of financial position`,
`consolidated statement of comprehensive income`,
`consolidated statement of cash flows`,
`consolidated statement of changes in equity`,
`statement of financial position`,
`notes to the consolidated financial statements`,
`notes to the financial statements`, plus four Arabic equivalents.

Rationale: Ferjancic et al. (2024, IRFA 96, 103669) show that including
financials inflates ESG-adjacent term counts without a matching change in
narrative disclosure.
Source: DECISIONS.md 2026-09-30 (Patch A); CLAUDE.md §Method.

**What is NOT explicitly excluded**: individual table cells that survive cleaning,
sentences containing table data. Tables are not detected or stripped as a class.

### Sentence segmentation

Library: spaCy, model `en_core_web_sm` (version 3.8.0, installed 2026-09-28).
Source: `backend/app/services/text_processing.py` lines 20–21; `app/config.py`
line 16 (`spacy_model = "en_core_web_sm"`); DECISIONS.md 2026-09-28.

The `senter` component is used if present in the loaded pipeline, otherwise
`sentencizer` is added (`text_processing.py` lines 20–21). `ner` and `parser`
components are disabled (`text_processing.py` line 20: `disable=["ner", "parser"]`).

Before segmentation, a lightweight line-level filter drops:
- lines matching `^\s*page\s+\d+\s*(of\s+\d+)?\s*$` (bare "Page N" / "Page N of M")
- lines matching `^\s*\d+\s*$` (isolated bare page numbers)
Source: `text_processing.py` lines 31–43 (`clean_page_text`).

After segmentation, sentences shorter than 3 characters are discarded
(`text_processing.py` line 58).

### Tokenisation and word-count definition

Words are counted by splitting page text on whitespace and bucketing each
token by script (`pdf_extraction.py` lines 102–117):

- **Latin token**: token containing at least one `[A-Za-z]` character
  (handles mixed tokens like "GRI300").
- **Arabic token**: token with at least one character in `[؀-ۿݐ-ݿ]`
  (Arabic Unicode blocks) and no Latin letters.
- Tokens with neither (bare numbers, punctuation, whitespace fragments): discarded.

**Denominator**: `latin_word_count` from the **full document** (before
text-quality cleaning). Cleaning changes which sentences reach the matcher;
it does not change the denominator.
Source: `pipeline.py` lines 179–180 (count on raw pages) and line 218
(score call uses `counts.latin`); DECISIONS.md 2026-09-28 (Latin/Arabic
bucketing rule); CLAUDE.md §Method.

`total_word_count` (Latin + Arabic) is stored on the `Report` row for reference
but is not used in density calculations (`report.py` lines 45–48;
DECISIONS.md 2026-09-28).

---

## 3. Matching

### Matcher used

Two `spacy.PhraseMatcher` passes per sentence, one for each matching attribute:
1. `LEMMA` attribute: for terms where `lemma_based = True`.
   Patterns are built with `nlp(term.phrase)` (full pipeline) so LEMMA tokens
   are populated. Matches inflected forms: "governed", "governing",
   "governance" all match a `governance` pattern.
2. `LOWER` attribute (case-insensitive exact): for terms where `lemma_based = False`.

Source: `backend/app/services/matcher.py` lines 52–63.

### Overlap handling and matching mode

Default mode: `matching_mode = "longest"` (`config/verity.toml` line 5).

In longest mode: `spacy.util.filter_spans` is applied to the combined span
list from both matchers. This keeps the longest span at each position; on ties
it keeps the earlier span. Cross-matcher overlaps are resolved in a single pass.
Source: `matcher.py` lines 88–100; DECISIONS.md 2026-09-28.

Diagnostic mode `all` retains every match including overlapping ones. It is
not used for scoring; the pipeline runs a shadow all-mode pass to log
`all_mode_extra_matches` per report when `log_all_mode_diff = true`
(`pipeline.py` lines 210–212).

### Multi-word terms

Matched as a complete phrase by PhraseMatcher. A pattern like
`board of directors` must appear as consecutive tokens to match.

### Repeat mentions and what is counted

**Unit counted**: each matched span (a single occurrence of a term in a sentence)
contributes one `MatchEvidence` row and adds `term.weight` to the
`raw_weighted_count` for that category.
Source: `scoring.py` lines 37–40; `score.py` lines 48–66.

If the same term appears non-overlappingly twice in one sentence, both
occurrences are counted separately (two spans, neither overlapping, both
survive `filter_spans`).

If the same term appears in two different sentences on the same page, both
are counted. There is no deduplication of cross-sentence occurrences.

**Known limitation**: spaCy's lemmatiser does not lower-case the first token of
a sentence, so sentence-initial "Governance" has lemma "Governance" (not
"governance"), causing LEMMA-mode patterns to miss it.
Impact was assessed as small on KFH FY2023 (most hits were mid-sentence).
Fix is deferred. Source: DECISIONS.md 2026-09-28.

---

## 4. Scoring

### Exact code path (quoted)

**Step 1 — category density** (`backend/app/services/scoring.py` lines 28–48):
```python
def score_report_categories(matches, term_lookup, total_words):
    weighted_by_category: dict[int, float] = defaultdict(float)
    for m in matches:
        term = term_lookup[m.term_id]
        weighted_by_category[term.category_id] += term.weight

    return [
        CategoryScoreResult(
            category_id=category_id,
            raw_weighted_count=raw,
            density_per_1000_words=(raw / total_words) * 1000,
        )
        for category_id, raw in weighted_by_category.items()
    ]
```
`total_words` is `Report.latin_word_count` (full-document Latin token count,
before cleaning). Source: `pipeline.py` line 218.

**Step 2 — composite** (`scoring.py` lines 52–58):
```python
def composite_score(category_scores, category_weights):
    total = sum(
        cs.density_per_1000_words * category_weights.get(cs.category_id, 1.0)
        for cs in category_scores
    )
    return round(total, 3)
```
All category weights are currently 1.0 (see §3 taxonomy); composite therefore
equals the sum of the three pillar densities.

**Step 3 — pillar score** (`scoring.py` lines 61–82):
Grouped sum of `density_per_1000_words × category.weight` per pillar. With
one category per pillar and weight 1.0, pillar score = category density.

**Step 4 — institution score** (`scoring.py` lines 85–102):
Equal-weighted mean of composite across all scored fiscal years for that
institution. Recency weighting is not applied (default `recency_weighted=False`).
Source: `build_leaderboard.py` lines 159–162 (direct sum / count, no weighting).

### Normalisation

Per 1,000 Latin-script words of the full document. Not normalised across
institutions or fiscal years (no z-score, no cross-institution normalisation).

### Pillar weights (all equal)
```sql
SELECT name, pillar, weight FROM categories ORDER BY pillar;
```
| Category name | Pillar | Weight |
|---|---|---|
| Environmental | Environmental | 1.0 |
| Governance | Governance | 1.0 |
| Social | Social | 1.0 |

### Multiple documents in one year

Idempotency key: `(source_document.sha256, taxonomy_version_id, pipeline_version)`.
An existing `Report` row under that key is skipped unless `--force` is passed.
Source: `pipeline.py` lines 321–336.

If a colleague-supplied file supersedes a crawler-sourced file for the same
(institution, FY), the older row retains `superseded_by_id` pointing to the
newer one. The batch runner skips rows with a non-null `superseded_by_id`.
Source: `provenance.py` lines 109–113.

The leaderboard builder (`build_leaderboard.py` line 153) keeps the last row
seen for each `(institution_id, fiscal_year)` from the SQL result set, which
is ordered by `slug, fiscal_year, pillar` — not explicitly by
taxonomy/pipeline version. If multiple Report rows exist for the same
(institution, FY) under the same taxonomy hash, the leaderboard composite is
whichever is returned last by the database. This is a known but unmeasured
risk; in practice there is one scored report per (institution, FY, taxonomy).

### Multiple years per institution

Equal-weighted mean of the per-year composites. No minimum-year requirement
for inclusion in the leaderboard.
Source: `build_leaderboard.py` lines 159–162; `scoring.py` lines 85–102.

### Pipeline version

`PIPELINE_VERSION = "0.3.0"` (module-level constant).
Source: `backend/app/services/pipeline.py` line 39.
Bumped in the same commit as cleaning/matching logic changes.
Source: DECISIONS.md 2026-09-30 (PIPELINE_VERSION is a code constant, not
in config).

Every `CategoryScore` and `MatchEvidence` row stores both `taxonomy_version_id`
(FK) and `pipeline_version` (string). Reprocessing under a new version
**appends** new rows; it does not delete old ones.
Source: DECISIONS.md 2026-09-30 (reprocessing appends).

---

## 5. Taxonomy

### Full term list, grouped by pillar

Sourced from `backend/seed/taxonomy_starter.json`. GRI/SASB references are
recorded at the **category** level in `_sourcing_note` fields, not per-term
(see NOT FOUND list at end).

Default for `lemma_based` is `True` when not specified.

**Environmental (22 terms, category weight 1.0)**
GRI 300 series + SASB Commercial Banks Standard.
Session 5 recall-audit additions: ESG, sustainability, GRI, net zero.
Session 5 precision-sample additions: sustainable development, sustainable
financing, nature-positive, nature-related.

| Phrase | Weight | lemma_based |
|---|---|---|
| climate change | 1.1 | True |
| climate risk | 1.2 | True |
| carbon emissions | 1.2 | True |
| carbon footprint | 1.0 | True |
| greenhouse gas | 1.2 | True |
| renewable energy | 1.0 | True |
| energy efficiency | 0.9 | True |
| green financing | 1.3 | True |
| green bond | 1.3 | True |
| sustainable finance | 1.2 | True |
| environmental risk | 1.1 | True |
| water management | 0.8 | True |
| waste management | 0.8 | True |
| biodiversity | 0.9 | True |
| ESG | 1.0 | **False** |
| sustainability | 1.0 | True |
| GRI | 1.0 | **False** |
| net zero | 1.2 | True |
| sustainable development | 1.1 | True |
| sustainable financing | 1.2 | True |
| nature-positive | 1.1 | True |
| nature-related | 1.1 | True |

**Social (18 terms, category weight 1.0)**
GRI 400 series + SASB Financial Sector Standard.
Session 5 additions: zakat, CSR, financial literacy, accessibility, supply chain.

| Phrase | Weight | lemma_based |
|---|---|---|
| diversity and inclusion | 1.1 | True |
| gender diversity | 1.0 | True |
| human rights | 1.1 | True |
| employee wellbeing | 0.9 | True |
| employee training | 0.8 | True |
| health and safety | 0.9 | True |
| community investment | 1.0 | True |
| community development | 1.0 | True |
| financial inclusion | 1.3 | True |
| responsible lending | 1.2 | True |
| fair lending | 1.2 | True |
| customer privacy | 1.1 | True |
| customer satisfaction | 0.8 | True |
| zakat | 1.1 | True |
| CSR | 1.0 | **False** |
| financial literacy | 1.2 | True |
| accessibility | 1.0 | True |
| supply chain | 1.0 | True |

**Governance (27 terms, category weight 1.0)**
GRI 2 (general disclosures: governance) + GRI 205 (anti-corruption).
Session 5 additions: fraud, remuneration committee, ESG committee,
anti-money laundering.

| Phrase | Weight | lemma_based |
|---|---|---|
| corporate governance | 1.2 | True |
| governance | 1.0 | True |
| board of directors | 1.0 | True |
| board independence | 1.3 | True |
| audit committee | 1.1 | True |
| risk committee | 1.1 | True |
| risk management | 1.0 | True |
| code of conduct | 0.9 | True |
| whistleblower | 1.2 | True |
| anti-corruption | 1.2 | True |
| business ethics | 1.0 | True |
| executive compensation | 1.0 | True |
| shareholder rights | 1.0 | True |
| internal control | 1.0 | True |
| internal control over financial reporting | 1.4 | **False** |
| ICOFR | 1.4 | **False** |
| material weakness | 1.3 | True |
| IT general control | 1.3 | True |
| ITGC | 1.3 | **False** |
| IT governance | 1.1 | True |
| information security | 1.0 | True |
| cybersecurity | 1.0 | True |
| data protection | 0.9 | True |
| fraud | 1.0 | True |
| remuneration committee | 1.0 | True |
| ESG committee | 1.1 | True |
| anti-money laundering | 1.1 | True |

### GRI/SASB reference per term

Per-term GRI/SASB pointers are **NOT uniformly recorded**. They exist at the
category level only (as `_sourcing_note` fields in `taxonomy_starter.json`).
Source: `docs/LIMITATIONS.md` §Methodological boundaries [TO VERIFY]:
"not every term has an explicit disclosure-code pointer."

### Current taxonomy hash

Hash: `4948c00426fa70118328478fe6e1d782c981cb65024378fe11af6a561faef340`
(taxonomy_versions.id = 3).
```sql
SELECT id, hash, created_at, note FROM taxonomy_versions ORDER BY created_at;
```
| id | hash (first 12) | created_at | note |
|---|---|---|---|
| 1 | `53c33ed8d08c` | 2026-09-30 14:46:45 UTC | seed loader |
| 2 | `b08bb2073c84` | 2026-10-02 15:12:01 UTC | seed loader |
| 3 | `4948c00426fa` | 2026-10-02 15:38:20 UTC | seed loader |

Hash computation: SHA-256 of canonical JSON.
Canonical form: categories sorted by name; terms within category sorted by
phrase; only fields: `{name, pillar, weight, terms: [{phrase, weight, lemma_based}]}`.
`_sourcing_note`, ORM ids, and timestamps are excluded from the hash.
Source: `backend/app/services/taxonomy_hash.py`; DECISIONS.md 2026-09-30
(taxonomy hash canonicalisation).

The hash includes `pillar`. A category moving from one pillar to another (same
name, terms, weights) produces a new hash.
Source: DECISIONS.md 2026-09-30 (taxonomy hash includes pillar).

### Version history: what was added, the evidence behind it

**v1 → v2 (+13 terms)**: ESG, sustainability, GRI, net zero, zakat, CSR,
financial literacy, accessibility, supply chain, fraud, remuneration committee,
ESG committee, anti-money laundering.
Evidence: recall audit (`docs/RECALL_AUDIT.md`), run against 6 scored reports
(see §6). These 13 candidate terms each appeared tens-to-hundreds of times in
reports where v1 scored near zero on Environmental or Social.
Source: `docs/METHODOLOGY.md` §3 (taxonomy); `docs/RECALL_AUDIT.md`.

**v2 → v3 (+4 terms)**: sustainable development, sustainable financing,
nature-positive, nature-related.
Evidence: precision sample (`docs/SAMPLE_SUSTAINABLE_NATURE.md`). 15 random
sentences per candidate term (seed 42) were classified by one human coder:
- "sustainable" (bare word): 11/15 ESG (73%), 4/15 generic — added as
  narrower multi-word phrases instead of bare word.
- "nature" (bare word): 5/15 ESG (33%), 10/15 accounting boilerplate —
  added as `nature-positive` and `nature-related` only.
Source: `docs/SAMPLE_SUSTAINABLE_NATURE.md`; DECISIONS.md (taxonomy_starter.json
`_sourcing_note` fields for Session 5 follow-up additions).

---

## 6. Validation done so far

### Recall audit

**Method**: for each candidate term (70+ terms grouped by pillar), count
case-insensitive whole-word (or whole-phrase) regex occurrences in the full
raw PyMuPDF text of each sample report. The scoring pipeline was not run —
this is a parallel raw-count probe.
Source: `backend/scripts/recall_audit.py` lines 12–15, 131–137.

**Sample size**: 6 reports.

**Sample documents** (source: `docs/RECALL_AUDIT.md`):
| Slug | FY | Filename |
|---|---|---|
| al-rajhi-bank | 2025 | 2025_integrated_e66e4adf.pdf |
| kuwait-finance-house | 2024 | 2024_annual_1dc3a852.pdf |
| first-abu-dhabi-bank | 2025 | 2025_annual_e510ca45.pdf |
| bank-muscat-bkmb | 2025 | 2025_annual_de736b4a.pdf |
| the-saudi-national-bank | 2025 | 2025_annual_29c1c170.pdf |
| bupa-arabia-for-cooperative-insurance-company | 2022 | 2022_annual_7497b716.pdf |

**Selection protocol**: manually chosen, documented as "diverse across
institutions / countries / sectors" in `recall_audit.py` TARGET_SAMPLE
(lines 85–92). No formal selection protocol (e.g., stratified random sampling)
is recorded.

**Results** (candidate-term hits across all 6 reports, `docs/RECALL_AUDIT.md`):
- Environmental candidates: 1,918 hits
- Social candidates: 496 hits
- Governance candidates: 522 hits
- Known-in-taxonomy (sanity check): 2,443 hits

**Was PRECISION (false positives) ever measured?**
Yes, for two terms only:
- "sustainable": 15-sentence random sample (seed 42), one human coder —
  11/15 (73%) ESG, 4/15 generic.
- "nature": 15-sentence random sample (seed 42), one human coder —
  5/15 (33%) ESG, 10/15 accounting boilerplate.
Source: `docs/SAMPLE_SUSTAINABLE_NATURE.md`.

Precision has NOT been measured systematically across all 67 current taxonomy
terms. Source: NOT FOUND in any doc or script.

**Inter-rater agreement / reliability check**: NOT FOUND. No second coder or
kappa score is recorded anywhere in the repo.

**Systematic manual annotation / full coding**: NOT FOUND. The recall audit
is a raw occurrence count, not human annotation of match correctness.

### Data quality flags

One hard-coded extraction artifact:
- `rabigh-refining-petrochemical-co` FY2020: composite 0.048, `matches_count = 1`,
  `data_quality_flag = sentence_segmentation_artifact`. Root cause: PDF board-bio
  layout breaks spaCy's sentence segmenter; 26 raw hits of "board of directors"
  matched 0 by the pipeline. Score kept but flagged in every output.
  Source: DECISIONS.md 2026-10-02; `build_leaderboard.py` lines 40–48.

### Current `processing_review_status = needs_review` count (scored reports)

```sql
SELECT processing_review_status, COUNT(*) n
FROM reports WHERE status = 'scored'
GROUP BY processing_review_status;
```
| processing_review_status | n |
|---|---|
| auto_ok | 173 |
| needs_review | 4 |

Breakdown of the 4 needs_review rows:
```sql
SELECT i.slug, r.fiscal_year, r.processing_review_reason
FROM reports r JOIN institutions i ON i.id = r.institution_id
WHERE r.processing_review_status = 'needs_review' AND r.status = 'scored'
ORDER BY i.slug, r.fiscal_year;
```
| Slug | FY | Reason |
|---|---|---|
| emirates-nbd-pjsc | 2023 | very low Latin word count (201 < 5000); high Arabic ratio (100% > 50%) |
| emirates-nbd-pjsc | 2023 | (duplicate row — same file under earlier taxonomy version) |
| emirates-nbd-pjsc | 2023 | (duplicate row — same file under earlier taxonomy version) |
| first-abu-dhabi-bank | 2021 | composite 7.511 outside [−3.274, 7.094] for FY2021 (IQR outlier) |

Note: the 3 emirates-nbd-pjsc FY2023 rows are the same Arabic-only PDF scored
under three taxonomy versions (v1, v2, v3). Under the current taxonomy (v3)
there is 1 such report.

### IQR outlier detection method

Cohort = fiscal year. A composite more than `iqr_multiplier` (3.0) × IQR
from Q1/Q3 of its FY cohort is flagged. Cohorts with fewer than
`iqr_min_cohort` (5) scored reports are labelled "low-confidence".
Source: `backend/app/services/qa_report.py` lines 80–105;
`config/verity.toml` lines 60–64.

---

## 7. Coverage (live database)

All numbers from queries run on 2026-10-05.

### Institutions scored vs in scope

```sql
-- Active institutions
SELECT COUNT(*) FROM institutions WHERE active = true;
-- 60

-- Institutions with at least one scored report under current taxonomy (v3)
SELECT i.is_financial, COUNT(DISTINCT i.id) n
FROM institutions i
JOIN reports r ON r.institution_id = i.id
JOIN category_scores cs ON cs.report_id = r.id
WHERE i.active = true AND r.status = 'scored' AND cs.taxonomy_version_id = 3
GROUP BY i.is_financial;
```
| is_financial | n |
|---|---|
| False (non-financial) | 26 |
| True (financial) | 17 |
| **Total** | **43** |

**CONFLICT**: `docs/METHODOLOGY.md` (generated 2026-10-03) states "44 of 60
have at least one scored report under the current taxonomy — 16 do not."
Live query on 2026-10-05 finds 43 scored / 17 not scored. Difference = 1
institution. The stale count in METHODOLOGY.md has not been reconciled. Both
figures are reported here.

### Scored reports under current taxonomy (v3)

```sql
SELECT COUNT(DISTINCT r.id)
FROM reports r JOIN category_scores cs ON cs.report_id = r.id
WHERE r.status = 'scored' AND cs.taxonomy_version_id = 3;
-- 130
```

### By country (current taxonomy)

```sql
SELECT i.country,
       COUNT(DISTINCT i.id) scored_institutions,
       COUNT(DISTINCT r.id) scored_reports
FROM institutions i
JOIN reports r ON r.institution_id = i.id
JOIN category_scores cs ON cs.report_id = r.id
WHERE i.active = true AND r.status = 'scored' AND cs.taxonomy_version_id = 3
GROUP BY i.country ORDER BY i.country;
```
(Reports figure from separate Q25 query; combined here for readability.)

| Country | Scored institutions | Scored reports |
|---|---:|---:|
| Bahrain | 3 | 13 |
| Kuwait | 3 | 8 |
| Oman | 3 | 5 |
| Qatar | 7 | 31 |
| Saudi Arabia | 16 | 35 |
| United Arab Emirates | 11 | 37 |
| **Total** | **43** | **129** |

Note: totals to 129 not 130 here because one report has `i.active = false`
in the Q25 sub-query. Full count is 130.

### By fiscal year (all pipeline versions)

```sql
SELECT fiscal_year, COUNT(*) n
FROM reports WHERE status = 'scored'
GROUP BY fiscal_year ORDER BY fiscal_year;
```
| FY | n |
|---|---|
| 2020 | 14 |
| 2021 | 22 |
| 2022 | 39 |
| 2023 | 29 |
| 2024 | 34 |
| 2025 | 39 |

### 17 institutions not scored under current taxonomy

```sql
SELECT i.name, i.country, i.is_financial
FROM institutions i
WHERE i.active = true
AND NOT EXISTS (
    SELECT 1 FROM reports r
    JOIN category_scores cs ON cs.report_id = r.id
    WHERE r.institution_id = i.id
    AND r.status = 'scored'
    AND cs.taxonomy_version_id = 3
)
ORDER BY i.is_financial DESC, i.name;
```

**Financial (4)**
| Name | Country |
|---|---|
| Bank Dhofar | Oman |
| Boubyan Bank | Kuwait |
| Oman International Development and Investment Company | Oman |
| Riyad Bank | Saudi Arabia |

**Non-financial (13)**
| Name | Country |
|---|---|
| Air Arabia PJSC | UAE |
| Etihad Etisalat (Mobily) | Saudi Arabia |
| Kuwait Telecommunications Company | Kuwait |
| Mobile Telecommunications Co. Saudi Arabia (Zain) | Saudi Arabia |
| Mouwasat Medical Services Company | Saudi Arabia |
| SABIC Agri-Nutrients Company | Saudi Arabia |
| Sahara International Petrochemical Co. | Saudi Arabia |
| Saudi Airlines Catering Company CATRION | Saudi Arabia |
| Saudi Cement | Saudi Arabia |
| Saudi Telecom Company | Saudi Arabia |
| Tamdeen Real Estate Company | Kuwait |
| Yanbu Cement Company | Saudi Arabia |
| Yanbu National Petrochemical Co | Saudi Arabia |

Reason categories (from `build_leaderboard.py` `_not_yet_covered()`):
- **A — No file in storage at all**: institution never crawled under the
  current 60-institution scope and no colleague-supplied file exists.
  Applies to most Saudi non-financials and telecom companies.
- **B — File(s) exist but none passed as annual/integrated + auto_ok**:
  Wayback captures with `report_type = unknown` (typically Arabic-only
  cover pages on exchange hosts). Applies to some Oman / Kuwait institutions.
- **D — Below 30-page threshold**: Air Arabia PJSC FY2021, 22-page summary
  report. Genuine annual report confirmed; too short by pipeline rules.

Source: `docs/LIMITATIONS.md` §Coverage holes; `build_leaderboard.py`
lines 119–138.

### Gap rows

```sql
SELECT reason, COUNT(*) n FROM gaps GROUP BY reason ORDER BY n DESC;
```
| Reason | n |
|---|---|
| not_found | 89 |
| unreachable | 5 |
| **Total** | **94** |

### Source documents needing review (not yet scored)

```sql
SELECT sd.source, sd.report_type, COUNT(*) n
FROM source_documents sd
WHERE sd.review_status = 'needs_review'
AND NOT EXISTS (
    SELECT 1 FROM reports r2
    WHERE r2.source_document_id = sd.id AND r2.status = 'scored'
)
GROUP BY sd.source, sd.report_type
ORDER BY sd.source, sd.report_type;
```
| Source | Report type | n |
|---|---|---|
| crawler | unknown | 3 |
| manual | annual | 3 |
| manual | integrated | 3 |
| manual | sustainability | 3 |
| manual | unknown | 1 |
| wayback | annual | 4 |
| wayback | financial_statements | 5 |
| wayback | unknown | 50 |

---

## 8. DECISIONS.md entries that affect methodology

One entry per item; date and effect on scoring/results.

| Date | Entry summary | Effect |
|---|---|---|
| 2026-09-28 | Longest-match-wins across both matchers using `spacy.util.filter_spans` | Prevents double-counting when both short and long forms of a concept are in the taxonomy |
| 2026-09-28 | Latin/Arabic bucketing: whitespace-split token with any `[A-Za-z]` = Latin; any Arabic-block (no Latin) = Arabic; else dropped | Defines word-count denominator; Arabic tokens do not dilute density |
| 2026-09-28 | `total_word_count` kept alongside `latin_word_count`; density uses `latin_word_count` exclusively | Density denominates on Latin only |
| 2026-09-28 | Taxonomy hash canonicalisation: only semantic fields (name/pillar/weight; phrase/weight/lemma_based); bookkeeping excluded | Two taxonomies with identical content but different timestamps or notes share the same version |
| 2026-09-28 | Reprocessing appends CategoryScore + MatchEvidence rows; does not delete old ones | Historical scores under earlier taxonomy/pipeline versions stay traceable |
| 2026-09-28 | `PIPELINE_VERSION` is a module-level constant (`pipeline.py`), not a config key | Version bumps are atomically tied to code changes, not config-file drift |
| 2026-09-28 | spaCy capitalised first-token lemma bug: sentence-initial "Governance" keeps lemma "Governance" — LEMMA patterns miss it | Small undercount of terms appearing sentence-initially; fix deferred |
| 2026-09-28 | spaCy `en_core_web_sm` 3.8.0 on Python 3.14; `ner` and `parser` disabled | Segmentation model and its limitations |
| 2026-09-30 (Patch A) | Financial-statements section excluded (auditor's report onward); rationale: Ferjancic et al. 2024 | Narrative-section-only scoring; boundary detection starts after first 25% of document |
| 2026-09-30 (Patch A) | Taxonomy hash must include `pillar`; moving a category to a different pillar must bump the version | Cross-pillar moves that leave term text unchanged would otherwise be invisible in versioning |
| 2026-09-30 (Patch A) | Score endpoint's per-report fallback (return latest version when requested version returns nothing) is unsafe for aggregation across reports | Do not use that fallback for cross-institution comparison; pin explicit `taxonomy_version_id` |
| 2026-09-30 | `settings.matching_mode` is a fallback only; matcher reads `config/verity.toml` on every run | `verity.toml` is the single source of truth for matching mode |
| 2026-10-01 (parser design) | Sustainability-report links detected and classified but filtered out before crawl; pipeline only ingests `annual \| integrated` | Sustainability reports are visible in the DB but not scored |
| 2026-10-02 (Session 6 leaderboard) | Rabigh FY2020 composite 0.048 is a known extraction artifact; sentence segmenter fails on its layout; score kept but flagged | One scored row is a measurement failure, not a measurement |
| 2026-10-02 (DECISIONS.md, repeat filter validated) | Al Rajhi's navigation chips ("ESG Report", "Context", "Overview") were being removed by the repeated-line filter — confirmed correct removal after investigation; filter does not remove real content | Filter removes per-page navigation text injected by the integrated-report layout, not narrative ESG text |
| 2026-10-03 (Session 10) | Production deployment ships without user authentication | No access control on scores API; CORS restricted to Vercel origin |

---

## NOT FOUND and code/doc conflicts

### NOT FOUND

1. **Per-term GRI/SASB disclosure code**: GRI and SASB references exist only at
   the category level (`_sourcing_note` in `taxonomy_starter.json`). No
   systematic per-term pointers are recorded.

2. **Systematic precision measurement** across all 67 taxonomy terms. Only
   "sustainable" (73%) and "nature" (33%) have a precision estimate, based on
   15-sentence samples by one human coder.

3. **Inter-rater reliability or kappa score**: no second coder, no disagreement
   analysis, no kappa in any file.

4. **Systematic manual annotation / full coding** of any report: none. The
   recall audit is a raw-count probe, not annotation of whether each match is
   a true ESG disclosure.

5. **Benchmark validation against external ratings** (MSCI, Sustainalytics,
   LSEG, Bloomberg): no ratings data has been obtained and no comparison has
   been run. Explicit statement: `docs/METHODOLOGY.md` §5
   ("No benchmark validation has been performed yet").

6. **Recall audit document selection protocol**: sample was hand-picked (six
   institutions, unspecified criteria for why those six). No stratified random
   selection or coverage-weighted protocol is documented.

7. **The exact sentence-segmentation failure mode on Rabigh FY2020** beyond
   "board-bio layout breaks spaCy's sentencizer" — the root cause in the PDF
   structure is not documented.

8. **v1 term count source**: `docs/METHODOLOGY.md` states v1 had 50 terms. No
   explicit term list for v1 exists in the repo (it was replaced by the seed
   loader before a snapshot was saved). The count is taken from METHODOLOGY.md
   on trust.

### Code / doc conflicts

1. **Scored institution count** (current taxonomy):
   - `docs/METHODOLOGY.md` (generated 2026-10-03): "44 of 60 have at least one
     scored report under the current taxonomy — 16 do not."
   - Live query (2026-10-05):
     `SELECT COUNT(DISTINCT i.id) ... WHERE cs.taxonomy_version_id = 3` → **43**;
     `NOT EXISTS` query for unscored institutions → **17** institutions, meaning
     **60 − 17 = 43** scored.
   - Discrepancy: 1 institution. Likely explains a data change between when
     METHODOLOGY.md was generated and the current state. Both figures are
     reported; live query takes precedence.

2. **`matching_mode` default value**: `app/config.py` line 39 declares
   `matching_mode: str = "longest"` as a pydantic `Settings` field. But
   DECISIONS.md 2026-09-30 states "`settings.matching_mode` is now a fallback
   only; the matcher reads `config/verity.toml` via `load_verity_config()` on
   every run." In practice, `matcher.py` line 81 calls `load_verity_config().matching_mode`,
   so the `Settings` value is never read by the matcher. The `config.py` value
   is technically dead code for this purpose. This is consistent with intended
   design but could confuse a reader who looks at `config.py` only.

---

*End of fact sheet.*
