# Recall audit (Session 1b)

Generated 2026-10-02T11:04:52+00:00.

Purpose: find ESG-adjacent terms that appear in the actual report text but are NOT in the current taxonomy, so we can see whether the Governance-vs-Environmental/Social score skew is a taxonomy-coverage artefact rather than a real disclosure difference.

Method: for each candidate term, count case-insensitive whole-word (or whole-phrase) occurrences in the full extracted text of a sample of scored reports. The scoring pipeline is NOT touched — this is a parallel ground-truth scan, not a rescore.

Sample (6 reports across institutions / countries / sectors):

- `al-rajhi-bank` FY2025  (2025_integrated_e66e4adf.pdf)
- `kuwait-finance-house` FY2024  (2024_annual_1dc3a852.pdf)
- `first-abu-dhabi-bank` FY2025  (2025_annual_e510ca45.pdf)
- `bank-muscat-bkmb` FY2025  (2025_annual_de736b4a.pdf)
- `the-saudi-national-bank` FY2025  (2025_annual_29c1c170.pdf)
- `bupa-arabia-for-cooperative-insurance-company` FY2022  (2022_annual_7497b716.pdf)

## Environmental (candidates)

| term | total hits (6 reports) | in reports |
|---|---|---|
| `sustainable` | 876 | 5/6 |
| `ESG` | 402 | 5/6 |
| `sustainability` | 258 | 5/6 |
| `nature` | 127 | 6/6 |
| `GRI` | 63 | 4/6 |
| `net zero` | 50 | 3/6 |
| `GHG` | 26 | 3/6 |
| `ESG rating` | 21 | 3/6 |
| `scope 1` | 15 | 3/6 |
| `scope 2` | 13 | 3/6 |
| `solar` | 11 | 3/6 |
| `sustainability report` | 7 | 3/6 |
| `net-zero` | 7 | 4/6 |
| `water consumption` | 7 | 1/6 |
| `decarbonisation` | 6 | 2/6 |
| `ESG framework` | 6 | 3/6 |
| `TCFD` | 5 | 1/6 |
| `wind` | 4 | 3/6 |
| `SASB` | 3 | 3/6 |
| `physical risk` | 3 | 1/6 |
| `scope 3` | 2 | 2/6 |
| `transition risk` | 2 | 2/6 |
| `circular economy` | 1 | 1/6 |
| `renewables` | 1 | 1/6 |
| `green building` | 1 | 1/6 |
| `LEED` | 1 | 1/6 |

## Social (candidates)

| term | total hits (6 reports) | in reports |
|---|---|---|
| `zakat` | 168 | 6/6 |
| `CSR` | 48 | 4/6 |
| `financial literacy` | 41 | 5/6 |
| `accessibility` | 37 | 5/6 |
| `employee engagement` | 31 | 3/6 |
| `supply chain` | 27 | 5/6 |
| `charitable` | 25 | 3/6 |
| `corporate social responsibility` | 16 | 4/6 |
| `donation` | 15 | 2/6 |
| `volunteerism` | 13 | 5/6 |
| `community engagement` | 11 | 4/6 |
| `donations` | 10 | 4/6 |
| `disability` | 9 | 3/6 |
| `volunteering` | 9 | 3/6 |
| `sponsorship` | 7 | 3/6 |
| `attrition` | 6 | 2/6 |
| `nationalization` | 5 | 2/6 |
| `financial education` | 5 | 2/6 |
| `Kuwaitization` | 2 | 1/6 |
| `women empowerment` | 2 | 1/6 |
| `gender equality` | 2 | 2/6 |
| `modern slavery` | 2 | 1/6 |
| `philanthropy` | 1 | 1/6 |
| `Saudization` | 1 | 1/6 |
| `pay equity` | 1 | 1/6 |
| `workplace safety` | 1 | 1/6 |
| `customer complaints` | 1 | 1/6 |

## Governance (candidates)

| term | total hits (6 reports) | in reports |
|---|---|---|
| `fraud` | 143 | 5/6 |
| `remuneration committee` | 58 | 4/6 |
| `ESG committee` | 44 | 2/6 |
| `AML` | 27 | 5/6 |
| `money laundering` | 26 | 5/6 |
| `bribery` | 24 | 4/6 |
| `sanctions` | 21 | 5/6 |
| `succession planning` | 21 | 4/6 |
| `enterprise risk management` | 20 | 5/6 |
| `related party transactions` | 19 | 6/6 |
| `annual general meeting` | 19 | 2/6 |
| `sustainability committee` | 15 | 2/6 |
| `stress test` | 14 | 3/6 |
| `anti-money laundering` | 13 | 5/6 |
| `three lines of defence` | 13 | 3/6 |
| `ESG governance` | 12 | 3/6 |
| `KYC` | 9 | 4/6 |
| `ERM` | 6 | 3/6 |
| `related-party` | 4 | 1/6 |
| `privacy policy` | 3 | 2/6 |
| `data breach` | 3 | 1/6 |
| `independent directors` | 3 | 2/6 |
| `GDPR` | 2 | 1/6 |
| `disclosure committee` | 1 | 1/6 |
| `resolution plan` | 1 | 1/6 |
| `fit and proper` | 1 | 1/6 |

## Known-in-taxonomy (sanity)

| term | total hits (6 reports) | in reports |
|---|---|---|
| `governance` | 928 | 6/6 |
| `risk management` | 671 | 6/6 |
| `corporate governance` | 401 | 6/6 |
| `audit committee` | 218 | 6/6 |
| `cybersecurity` | 115 | 5/6 |
| `financial inclusion` | 68 | 4/6 |
| `renewable energy` | 28 | 3/6 |
| `diversity and inclusion` | 12 | 2/6 |
| `waste management` | 2 | 2/6 |

## Per-report totals

| report | candidate-term hits | known-term hits |
|---|---|---|
| `al-rajhi-bank` FY2025 | 1317 | 1018 |
| `kuwait-finance-house` FY2024 | 174 | 263 |
| `first-abu-dhabi-bank` FY2025 | 909 | 573 |
| `bank-muscat-bkmb` FY2025 | 201 | 266 |
| `the-saudi-national-bank` FY2025 | 306 | 309 |
| `bupa-arabia-for-cooperative-insurance-company` FY2022 | 29 | 14 |

## Takeaway

- Candidate-term hits across all 6 reports: Environmental = 1918, Social = 496, Governance = 522.
- Known-term hits (sanity): 2443.

The Governance pillar's lead in the scored output (2,601 matches vs 403 / 348) partly reflects the term list size (23 Gov vs 14 Env / 13 Soc) and partly reflects a known regional pattern: banks' annual reports extensively narrate regulatory governance obligations, with much lighter E/S narrative. Any candidate above with a hit count comparable to an in-taxonomy term is a direct recall gap — look at `sustainability`, `ESG`, `CSR`, `nationalization`-family and pillar-committee terms first.
