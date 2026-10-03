# Smoke test — face validity of matches

Fixture: Kuwait Finance House, Annual Report 2023 (English section only).

- Source URL: `https://kfh.com/en/reports/kuwait/Annual-Reports/Annual-Report-2023/document_en/KFH%20Annual%20Report%20En%202023.pdf.pdf`
- Retrieved 2026-09-28, sha256 `3e07061259715d2856d844ff385321a65c5a05dc67dd5460488cd1ab1818fb76`, 7,182,431 bytes.
- Pipeline: pipeline_version `0.1.0`, taxonomy_version `0.1.0`.
- Report totals: 113 pages, 41,338 Latin words, 5 Arabic words, 1,418 sentences, 129 matches (post longest-wins).

## Method

`scripts/audit_matches.py --report-id 1 --seed 42 --n 25` drew 25 matches at
random (deterministic seed) from `MatchEvidence`, printed the term, page and
sentence for each. Every one was then classified by hand:

- **True** — the sentence is a topical disclosure using the term in an ESG sense
  the taxonomy legitimately intends to capture.
- **False positive** — the sentence contains the token, but the context is not
  an ESG disclosure at all (biographical prose, section header, unrelated use).

## Verdicts

| # | Term | Page | True/FP | Why |
|---|---|---|---|---|
| 1 | governance | 41 | T | Periodic review of governance and disclosure applications. |
| 2 | board of directors | 33 | T | Board remuneration disclosure (KD 1,308k). |
| 3 | governance | 67 | T | Practice improvements at subsidiaries. |
| 4 | governance | 41 | T | Three-lines-of-defence governance model. |
| 5 | governance | 41 | T | Adherence to governance principles and standards. |
| 6 | risk management | 71 | T | Operational risk management framework. |
| 7 | governance | 41 | T | Governance framework introduction. |
| 8 | risk management | 71 | T | Board-level responsibility for operational risk management. |
| 9 | governance | 37 | **FP** | Biography of Chief Internal Auditor: lists "governance processes" among his skills — not a governance disclosure by the bank. |
| 10 | governance | 67 | T | Governance process overseen by the Board. |
| 11 | risk management | 71 | T | Liquidity risk management framework. |
| 12 | risk management | 69 | T | Market risk management processes. |
| 13 | governance | 53 | T | Governance requirements as banking pillars. |
| 14 | internal control | 37 | **FP** | Biography (same executive), "internal controls" is skill list, not a control disclosure. |
| 15 | cybersecurity | 53 | T | Cyber security framework compliance. |
| 16 | code of conduct | 47 | T | Committee reviews the code of conduct. |
| 17 | governance | 31 | T | Chair's message: commitment to governance standards. |
| 18 | diversity and inclusion | 28 | T | Diversity and inclusion initiative for people with special needs. |
| 19 | governance | 70 | T | Governance and organisation section header + body sentence. |
| 20 | governance | 41 | T | Regular review of governance updates. |
| 21 | governance | 41 | T | Corporate governance policy at subsidiaries. |
| 22 | governance | 51 | T | Audit relies on the "risk management and governance control framework". |
| 23 | cybersecurity | 53 | T | Cybersecurity crisis-management simulation. |
| 24 | risk management | 69 | T | Credit risk management. |
| 25 | risk management | 53 | T | Risk department responsibilities. |

**Precision estimate: 23/25 = 0.92** (Wilson 95% CI ≈ 0.75–0.98, so the true
precision on this report might reasonably be anywhere from ~75% to ~98%; one
report is not enough to lock a tight bound).

## Where false positives came from

Both FPs on this sample came from **biographical prose about executives** — bios
in the "Board of Directors" section list "governance", "internal controls" and
"risk management" as things the person has experience in. The sentence contains
the term; the bank is not disclosing an ESG practice.

Terms most likely to hit this pattern (based on the underlying prose, not the
sample counts):

1. `governance` — appears in every executive bio's boilerplate description.
2. `internal control` — same.
3. `risk management` — same.
4. `audit committee` / `board of directors` — appear in bios as prior positions
   rather than as disclosures.

## Recommendations (not applied this session)

- **Section-aware scoping**: identify and either exclude or down-weight matches
  from executive bio / board-composition pages. Feasible with the current data
  because Report already stores per-page evidence; we would add a page-level
  "section" tag ("bio", "financials", "governance body", "other") and reweight
  in scoring.
- **Not**: sentiment or negation. The whole point of density scoring is to be
  polarity-blind (see CLAUDE.md, Method), so "governance" in a bio is not
  wrong because of sentiment — it's wrong because it's out-of-section.
- **Do not touch the taxonomy this session.** Suppressing "governance" would
  cost real signal on chair statements, framework descriptions and policy
  sections; the fix is section-aware scoping, not term deletion.

## Other observations from the run

- No matched sentences came from a contents / table-of-contents page (this
  PDF has no formal ToC that the extractor picked up).
- No matched sentences came from a line that repeats verbatim across ≥8 pages
  (running headers/footers are chopped by the segmenter before matching).
- Latin/Arabic split: 41,338 / 5 tokens — the English section is very lightly
  contaminated by OCR of the Arabic cover. On a fully bilingual report the
  Arabic count would be far higher and Latin-only denominator matters more.
- Environmental and Social densities are ~1/20 of Governance density on this
  report; expected for a bank's annual report where governance is legally
  mandated to be extensively disclosed and environmental disclosure is still
  emerging in the region.
