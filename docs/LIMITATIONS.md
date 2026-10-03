# Limitations

What Verity measures, what it does NOT measure, and the things a reader
of its leaderboard should know before quoting a number.

## What this measures

Density of ESG-adjacent *phrases* in the narrative sections of annual
and integrated reports, weighted by a GRI-/SASB-sourced taxonomy. It is
a measure of *how much the company talks about ESG topics*, not whether
the company does them well. The design-level rationale for ignoring
sentiment is in [CLAUDE.md](../CLAUDE.md) ("Method"): the ESG-disclosure
literature's recurring finding is that sentiment classifiers imported
from general finance NLP mis-classify boilerplate at a rate that
swamps the signal (Loughran and McDonald, 2011).

## What this does NOT measure

- **Performance.** A high score means lots of disclosure wording, not
  low emissions, strong governance or good labour practices.
- **Materiality.** All phrases carry a static weight; the taxonomy does
  not know that *water management* matters more for a cement producer
  than for a bank.
- **Negation / forward-looking vs retrospective.** "We have not yet
  established a Scope-3 target" scores the same as "We have met our
  Scope-3 target."
- **Agreement with external ratings.** The empirical lesson from Berg,
  Koelbel and Rigobon (2022) is that ESG rating agencies disagree
  sharply with each other even on the same reports; Verity has not been
  benchmarked against any agency yet (see [BACKLOG.md](BACKLOG.md)).

## Known failure modes that are already visible in tonight's output

### Extraction artifacts (1 report)

`rabigh-refining-petrochemical-co` FY2020 shows composite 0.048,
lowest in the dataset. Raw-text probe of pages 1-57 (the range scored
before the financial-statements boundary) found ≥35 taxonomy-term
occurrences the pipeline missed — most striking being 26 raw hits of
"board of directors" with 0 matched. The PDF's layout breaks spaCy's
sentence segmenter so most sentences never reach the matcher. The row
is kept in the leaderboard with a `data_quality_flag` column and an
asterisk + footnote on the printed tables. See
[DECISIONS.md](../DECISIONS.md) 2026-10-02.

### Coverage holes (17 institutions have no scored report under the
current taxonomy)

- 12 have no file in storage at all. These were never crawled under the
  updated 60-institution scope and the colleague-supplied drop didn't
  cover them.
- 4 have only Wayback captures whose `report_type` detection returned
  "unknown" from the first three pages. Mostly Arabic-only cover pages
  on Oman and Kuwait exchange hosts.
- 1 is Air Arabia PJSC FY2021 — a genuine 22-page summary report under
  the 30-page minimum used to distinguish annual reports from
  highlights decks.

### Needs-review backlog

- Source documents still `needs_review`: 3 `crawler` + 10 `manual`
  + 45 `wayback`.
- Reports flagged `processing_review_status=needs_review` after Session 5
  QA: 6 (one heavily-scanned FY2021, one text-extraction-sparse
  Emirates NBD FY2023 at 201 Latin words, four others surfaced by
  the IQR / threshold rules in `qa_report.py`).
- Open gap rows: 94 (89 `not_found`, 5 `unreachable`).

## Methodological boundaries [TO VERIFY]

- The decision to EXCLUDE the financial-statements section is justified
  from the leaderboard-design side on the Ferjancic et al. (2024)
  finding that including financials inflates raw counts of
  ESG-adjacent terms. Whether the exclusion boundary our detector
  draws coincides with the one those authors drew [TO VERIFY].
- Taxonomy weights were seeded from GRI / SASB tags. The exact mapping
  from standard-code to phrase is in `backend/seed/taxonomy_starter.json`
  as `_sourcing_note` fields but not every term has an explicit
  disclosure-code pointer. [TO VERIFY] per-term provenance before this
  table is cited externally.
- Schimanski et al. (2024) finds that LLM / embedding approaches
  outperform dictionary methods on climate-disclosure classification.
  Verity's dictionary approach is a deliberate choice for transparency
  and reproducibility, not an argument that dictionaries are the
  state of the art. [TO VERIFY] the direction of magnitude of that
  precision/recall gap against this specific taxonomy before Session 8.

## Non-measurement limits

- **Scope**: 60 institutions from the May 2024 top-60-by-market-cap
  Middle-East list. Five were later rebranded (Session 6 scope
  correction); five were dropped from the active universe but their
  prior data is retained for audit.
- **Years**: fiscal 2020 through 2025. 2020 coverage is thin because
  many reports were only published after this project started.
- **Language**: taxonomy is English. Arabic-only reports score ~0 by
  design (Latin-word denominator). The 11 reports flagged as
  heavily-Arabic / low-Latin by QA are in that category.
- **Benchmark comparison**: not done. The `/benchmark` dashboard view
  shows the empty-state prompt by design tonight.

## Citations

- Berg, F., Kölbel, J. F., and Rigobon, R. (2022). Aggregate confusion:
  The divergence of ESG ratings. *Review of Finance*, 26(6), 1315-1344.
- Ferjancic, U., Ichev, R., and Lončarski, I. (2024). What can we learn
  about ESG from financial disclosures? *International Review of
  Financial Analysis*, 96, 103669.
- Loughran, T. and McDonald, B. (2011). When is a liability not a
  liability? Textual analysis, dictionaries, and 10-Ks. *Journal of
  Finance*, 66(1), 35-65.
- Schimanski, T., Reding, A., Reding, N., Bingler, J., Kraus, M., and
  Leippold, M. (2024). Bridging the gap in ESG measurement: Using NLP
  to quantify environmental, social, and governance communication.
  *Finance Research Letters*, 61, 104979.

Any claim stated as fact in this document that is NOT tied to one of
these four citations carries [TO VERIFY] and should be verified
against a specific source before being cited.
