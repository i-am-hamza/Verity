# How Verity measures ESG disclosure

Verity measures how much 65 large listed companies in the GCC disclose about environmental, social and governance (ESG) topics in their annual reports, from fiscal year 2020 to 2025.

It measures **disclosure, not performance**. A sentence admitting a weakness counts the same as one describing a strength: both show the company is reporting on the topic.

---

## 1. The reports

- **65 companies** across six markets: Saudi Arabia (27), United Arab Emirates (12), Qatar (9), Kuwait (7), Oman (6) and Bahrain (4).
- **Six years each**, FY2020 to FY2025, giving **390 annual reports**: exactly one per company and year.
- **20 financial companies** (19 commercial banks and one investment company) and **45 non-financial companies**. Saudi Industrial Investment Group was replaced by Bank Aljazira (ticker 1020) because SIIG has no revenue line, making net margin calculations impossible.
- Only the **English version** of each company's annual or integrated report is used. Every report was checked by the research team for the right company and the right fiscal year.
- Five of the 65 companies were added to broaden the sample. Results with and without them are almost identical.

## 2. What text is analysed

Annual reports contain far more than ESG discussion, so Verity reads only the parts that count:

- **Narrative sections only.** Financial statements and contents pages are excluded.
- **Real sentences only.** Following Ferjančič et al. (2024), headings, table labels, lists of names and lines of figures are dropped. A sentence is kept when it starts with a capital letter, ends with a full stop, question mark or exclamation mark, has at least eight words, and is not mostly capital letters or numbers. About three-quarters of narrative text passes this filter.
- **Scanned pages** are read with text recognition (OCR). Reports that are mostly scanned were checked by hand for readable text.
- Words are matched **regardless of capitals or word form**, so "Governance", "GOVERNANCE" and "governed" are all recognised.

## 3. The term list

Verity looks for a fixed list of ESG terms drawn from the **GRI Standards** and the **SASB Standards**.

| Group | Terms | How it is used |
|---|---|---|
| Environmental | 24 | Counts towards the Environmental score |
| Social | 22 | Counts towards the Social score (27 search phrases: some concepts have multiple spellings, e.g. *customer needs / customers' needs / client needs*) |
| Governance | 34 | Counts towards the Governance score (36 search phrases: two abbreviation pairs, *ICOFR* and *ITGC*, each counted as one concept) |
| General ESG terms | 8 | Counts towards the General score (*ESG*, *sustainability*, *GRI*, *sustainable development*, *CSR*, *innovation*, *feedback*, *digital services*) |
| Banking terms | 9 | Scored separately, for the 20 financial companies only (for example *financial inclusion*, *responsible lending*, *stress testing*) |

**How new terms were added.** Terms were added in two rounds. First, fourteen terms were added based on an analysis of the full corpus (thirteen in the three pillars and stress testing in the banking terms), such as *air quality*, *process safety* and *food safety*, to cover topics that matter for industrial companies. Second, sixteen further terms were added at the examiner's request and verified by the examiner against the same acceptance tests, covering topics such as *climate policy*, *employee engagement*, *board meetings* and *stakeholder engagement*. Each candidate had to pass two tests set in advance:

1. It appears in at least **10%** of reports from the industries where its topic matters.
2. At least **14 of 20** randomly chosen sentences containing it are genuinely about that ESG topic, as judged by the researcher.

Candidates that failed either test were not added.

## 4. Weighting by importance to the industry

Not every topic matters equally to every business. Water matters more to a cement maker than to a bank.

Each company is assigned to one of SASB's 77 industries. A term counts **1.5** when SASB treats its topic as important (*material*) for that industry, and **1.0** otherwise. For example, *health and safety* counts 1.5 for a cement company and 1.0 for a bank.

The rankings were also calculated with weights of 1.25, 2.0 and no weighting at all. They are almost identical, so the results do not depend on the exact weight chosen.

## 5. How the scores are calculated

1. **Density.** For each report and each component (Environmental, Social, Governance, General): weighted term mentions per 1,000 words of analysed text.
2. **Score out of 100.** Each component's density is converted to a 0–100 score by its rank among all 390 reports, all years together. **100** is the most disclosure in the sample and **0** the least.
3. **Composite.** The average of the Environmental, Social, Governance and General scores, also out of 100.
4. **Company score.** The average of a company's six yearly scores.

Because scores are based on rank, they show **where a company stands within this sample**, not against an absolute standard.

## 6. Checks on the results

- **Robustness.** The rankings were recalculated in several ways: (a) using a three-pillar composite without the General component; (b) using a General component that includes only the five original generic terms, excluding innovation, feedback and digital services; (c) with different SASB materiality weights (1.0, 1.25, 2.0); (d) adjusted for each company's sector (following Ferjančič et al., 2024); and (e) without the five companies added later. In each case the ranking stays very similar.
- **Hand checks.** For sample reports, term counts were recounted by hand and reconciled with Verity's counts.
- **Data-quality flags.** Reports with unusually little analysed text, or unusually high or low scores, are flagged for attention. They are not removed.

## 7. Governance and firm-age variables (not part of the ESG score)

Alongside the ESG scores, Verity records two kinds of non-score variables for each company-year:

- **Board size** — number of board seats at fiscal year-end, from that year's annual report. Board size was read from the board section of each annual report using an assisted reading process; every value is recorded with page numbers and the directors counted, and was reviewed by the researcher on a random sample and all flagged cases. Secretary, advisors, observers and committee-only members are excluded. A director representing an entity ("QNB, represented by Mr X") counts as one. The named list of actual directors is preferred over any statutory number in the articles ("consists of up to N"); when a stated number and the list disagree, the list is used and the row is flagged.
- **Age since established** and **age since listed** — supplied by the researcher.

Neither variable is part of the ESG score. Both are exported alongside the scores (Excel and CSV) and shown on each company page so the data can be used by future analyses.

## 8. Research dataset and financial measures (researcher-supplied)

The site publishes a 390-row dataset (one per company-year) with 21 columns. Twelve of them are the ESG scores and the governance / firm-age variables described above. The remaining columns come from the researcher's financial dataset and from a workbook of total assets and liabilities compiled from the audited financial statements:

| Column | Source | Note |
|---|---|---|
| **Company**, **Ticker**, **Country**, **Fiscal year** | Verity institution registry | Primary listing. |
| **Environmental**, **Social**, **Governance** | Verity pipeline | 0–100 rank-normalised; see §5. |
| **Composite ESG score** | Verity pipeline | Mean of E, S, G and General, 0–100. |
| **Board size** | Researcher (assisted reading of annual reports) | §7. |
| **Age since established**, **Age since listing** | Researcher | §7. |
| **Market cap (USD million)**, **EPS**, **Leverage (debt/equity)**, **Net margin (%)**, **RoE (%)**, **RoA (%)** | Researcher's financial data (Data_20_10_2026.xlsx) | Four researcher corrections applied before publication: Saudi Aramco 2024 and 2025 RoA / RoE were swapped in the source and are restored; Sahara Petrochemical 2025 net margin is set to the audited loss (−12.6%); Bank Aljazira 2020 EPS is set to the post-adjustment value (0.03). |
| **Total assets (USD million)**, **Total liabilities (USD million)** | Researcher (company_assets_liabilities_2020_2025_USD.xlsx) | Audited year-end balance-sheet items, converted to USD at year-end FX. |
| **Tobin's Q** | Derived | (Market cap + Total liabilities) ÷ Total assets. |
| **Price-to-book** | Derived | Market cap ÷ (Total assets − Total liabilities). Left blank if book equity is zero or negative. |

Growth is not reported — the growth column in the source file is empty — so it is not included in the dataset.

## 9. ESG & Financials analysis

The ESG & Financials page uses the dataset above to ask whether companies that disclose more about ESG are also more profitable or more highly valued. **It is an association study, not a causal one.** We report six profitability-and-value measures (RoA, RoE, net margin, EPS, Tobin's Q, price-to-book), with ESG composite (0–100) as the single explanatory measure, and the following controls:

- `ln(total assets)` for firm size,
- leverage (debt/equity) for capital structure,
- board size for governance,
- `ln(1 + age since established)` for firm maturity.

Models add year, industry, country or company effects depending on the design (see "How the models work" on the page). Standard errors are clustered by company. β is reported per **+10 ESG points**.

### Diagnostics

- **Hausman test** — compares the within-company (fixed-effects) and random-effects estimators for each measure and group. p &lt; 0.05 means the within-company design is preferred; otherwise the random-effects estimator is reported.
- **Variance-inflation factors (VIF)** — for ESG composite and the four controls, per group. All values below 2, well under the usual 10-threshold rule of thumb.
- **Two-stage least squares (2SLS)** — ESG is instrumented by the average ESG score of same-sector companies in **other** countries in the same year. The first-stage F is below 10 for every measure in this sample, so IV estimates are only indicative and reported for completeness; the preferred main estimates are A2 (across companies, with country effects) and B (within companies, with year effects).

## 10. Limitations

- Verity measures **how much** a company discloses, not how good its ESG performance is or how credible its claims are.
- Only **English** text is analysed.
- A word list can miss meaning that a reader would catch, and occasionally count a word used in an unrelated sense. The term tests above limit this.
- Scores are **relative to this sample** of 65 companies.
- The scores have **not yet been compared with external ESG ratings** such as MSCI, LSEG or Sustainalytics.

## 11. References

- Ferjančič, U., Ichev, R., Lončarski, I., Montariol, S., Pelicon, A., Pollak, S., Sitar Šuštar, K., Toman, A., Valentinčič, A. and Žnidaršič, M. (2024). Textual analysis of corporate sustainability reporting and corporate ESG scores. *International Review of Financial Analysis*, 96, 103669.
- Global Reporting Initiative. *GRI Standards*.
- Loughran, T. and McDonald, B. (2011). When is a liability not a liability? Textual analysis, dictionaries, and 10-Ks. *Journal of Finance*, 66(1), 35–65.
- IFRS Foundation. *SASB Standards*.
