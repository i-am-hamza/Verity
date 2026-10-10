# How Verity measures ESG disclosure

Verity measures how much 65 large listed companies in the GCC disclose about environmental, social and governance (ESG) topics in their annual reports, from fiscal year 2020 to 2025.

It measures **disclosure, not performance**. A sentence admitting a weakness counts the same as one describing a strength: both show the company is reporting on the topic.

---

## 1. The reports

- **65 companies** across six markets: Saudi Arabia (27), United Arab Emirates (12), Qatar (9), Kuwait (7), Oman (6) and Bahrain (4).
- **Six years each**, FY2020 to FY2025, giving **390 annual reports**: exactly one per company and year.
- **19 financial companies** (18 commercial banks and one investment company) and **46 non-financial companies**.
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
| Environmental | 21 | Counts towards the Environmental score |
| Social | 16 | Counts towards the Social score |
| Governance | 30 | Counts towards the Governance score |
| Banking terms | 9 | Scored separately, for the 19 financial companies only (for example *financial inclusion*, *responsible lending*, *stress testing*) |
| General ESG terms | 5 | Counted separately and kept out of all three scores (*ESG*, *sustainability*, *GRI*, *sustainable development*, *CSR*) |

**How new terms were added.** Fourteen terms were added in the current version (thirteen in the three pillars and stress testing in the banking terms), such as *air quality*, *process safety* and *food safety*, to cover topics that matter for industrial companies. Each candidate had to pass two tests set in advance:

1. It appears in at least **10%** of reports from the industries where its topic matters.
2. At least **14 of 20** randomly chosen sentences containing it are genuinely about that ESG topic, as judged by the researcher.

Candidates that failed either test were not added.

## 4. Weighting by importance to the industry

Not every topic matters equally to every business. Water matters more to a cement maker than to a bank.

Each company is assigned to one of SASB's 77 industries. A term counts **1.5** when SASB treats its topic as important (*material*) for that industry, and **1.0** otherwise. For example, *health and safety* counts 1.5 for a cement company and 1.0 for a bank.

The rankings were also calculated with weights of 1.25, 2.0 and no weighting at all. They are almost identical, so the results do not depend on the exact weight chosen.

## 5. How the scores are calculated

1. **Density.** For each report and each pillar: weighted term mentions per 1,000 words of analysed text.
2. **Score out of 10.** Each pillar's density is converted to a 0–10 score by its rank among all 390 reports, all years together. **10** is the most disclosure in the sample and **0** the least.
3. **Composite.** The average of the Environmental, Social and Governance scores, also out of 10.
4. **Company score.** The average of a company's six yearly scores.

Because scores are based on rank, they show **where a company stands within this sample**, not against an absolute standard.

## 6. Checks on the results

- **Robustness.** The rankings were recalculated with different weights, adjusted for each company's sector (following Ferjančič et al., 2024), and without the five added companies. In each case the ranking stays very similar.
- **Hand checks.** For sample reports, term counts were recounted by hand and reconciled with Verity's counts.
- **Data-quality flags.** Reports with unusually little analysed text, or unusually high or low scores, are flagged for attention. They are not removed.

## 7. Limitations

- Verity measures **how much** a company discloses, not how good its ESG performance is or how credible its claims are.
- Only **English** text is analysed.
- A word list can miss meaning that a reader would catch, and occasionally count a word used in an unrelated sense. The term tests above limit this.
- Scores are **relative to this sample** of 65 companies.
- The scores have **not yet been compared with external ESG ratings** such as MSCI, LSEG or Sustainalytics.

## References

- Ferjančič, U., Ichev, R., Lončarski, I., Montariol, S., Pelicon, A., Pollak, S., Sitar Šuštar, K., Toman, A., Valentinčič, A. and Žnidaršič, M. (2024). Textual analysis of corporate sustainability reporting and corporate ESG scores. *International Review of Financial Analysis*, 96, 103669.
- Global Reporting Initiative. *GRI Standards*.
- Loughran, T. and McDonald, B. (2011). When is a liability not a liability? Textual analysis, dictionaries, and 10-Ks. *Journal of Finance*, 66(1), 35–65.
- IFRS Foundation. *SASB Standards*.
