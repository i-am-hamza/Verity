# IR + exchange source review

Current state: **Session 3b** (2026-10-01). Session 3 did WebFetch-based discovery; Session 3b retried everything blocked at that layer with Playwright (Chromium + the VerityResearchBot UA from CLAUDE.md), closed the deferred non-financial exchange work, and resolved ALAFCO's path.

## Statuses

- **verified** — the URL was fetched (Session 3 via WebFetch or Session 3b via Playwright) and the page's content / title / preserved final URL confirmed it was the intended IR or exchange-company page.
- **unreachable** — the URL was fetched and the site returned a definitive block (403 / 404 / 500 / 523) or redirected to a dead end. For exchange URLs this includes Tadawul (saudiexchange.sa) and Boursa Kuwait `/stock/<id>/profile`, which both 403 even to Playwright + the honest VerityResearchBot UA — Akamai-style bot detection that trips on the UA string. Per CLAUDE.md rule 3 we stop for those domains and move on; they go to Tier 3/4.
- **needs_human** — no verified fetch, no definitive block. Three rows remain here after Session 3b because no live URL has been identified at all (Jarir Marketing; Tamdeen Real Estate; Oman International Development and Investment IR page).

## What changed from Session 3

- Tadawul (24 slugs) and Boursa Kuwait numeric-id profile URLs (6 slugs) now `exchange_status = unreachable` with Playwright evidence, not `needs_human`.
- ADX / DFM / QSE / MSX / Bahrain Bourse per-company URLs verified via Playwright — 27 total `exchange_status = verified` rows (up from 10).
- SNB (`alahli.com`) was Session-3-unreachable due to a cert error — Playwright returned 200 with title "Investor Relations | Saudi National Bank". Session 3's cert error was Claude-tool-specific.
- 19 of the 24 deferred `needs_human` IR rows upgraded to `verified`; 6 downgraded to `unreachable` (403/500 or redirect-to-homepage).
- ALAFCO: both sides `unreachable`, with a dedicated Wayback plan — 5 gap rows now live in the `gaps` table (imported via `seed/import_alafco_gaps.py`) so Session 4's Wayback helper picks them up directly from the DB. `data/alafco_gaps.json` is now a staging artefact.

## Pilot gate note for Session 4

**Do not include ALAFCO in Session 4's 3-institution financial-wave pilot gate.** ALAFCO is a Wayback-only path, not a live-crawl test; including it would make the pilot's pass/fail signal ambiguous between "live crawler works" and "Wayback helper works". Pick any 3 of the 22 other financial-wave institutions that have at least one verified live source.

## Per-institution table

| # | slug | wave | country | ir | exchange | evidence sample |
|---|---|---|---|---|---|---|
| 1 | `al-rajhi-bank` | financial | Saudi Arabia | verified | unreachable | https://objectstorage.me-jeddah-1.oraclecloud.com/n/ax0k7s74wvl7/b/Marketing_Email_Imag... |
| 2 | `the-saudi-national-bank` | financial | Saudi Arabia | verified | unreachable | https://www.alahli.com/-/media/project/snb/snb-web/about-us/02-1-investor-relations/fin... |
| 3 | `riyad-bank` | financial | Saudi Arabia | verified | unreachable | https://www.riyadbank.com/documents/20121/0/Riyad+Bank+Annual+Report+2024+with+FS+-+Eng... |
| 4 | `alinma-bank` | financial | Saudi Arabia | verified | unreachable | https://ir.alinma.com/en/investor-relations/financial-information/?query=annual-reports... |
| 5 | `bank-albilad` | financial | Saudi Arabia | verified | unreachable | https://www.bankalbilad.com.sa/Documents/boardscv2019/Albilad%20Annual%20Report%202018_... |
| 6 | `bupa-arabia-for-cooperative-insurance-company` | financial | Saudi Arabia | unreachable | unreachable | — |
| 7 | `saudi-industrial-investment-group` | financial | Saudi Arabia | verified | unreachable | https://siig.com.sa/investors-presentation/ |
| 8 | `first-abu-dhabi-bank` | financial | United Arab Emirates | verified | verified | https://www.bankfab.com/-/media/fab-uds/about-fab/investor-relations/reports-and-presen... |
| 9 | `abu-dhabi-commercial-bank` | financial | United Arab Emirates | unreachable | verified | https://www.adcb.com/en/about-us/investor-relations/annual-report/2024 |
| 10 | `the-national-bank-of-ras-al-khaimah` | financial | United Arab Emirates | verified | verified | https://agm.rakbank.ae/2025/ |
| 11 | `dubai-islamic-bank` | financial | United Arab Emirates | verified | verified | https://www.dib.ae/docs/default-source/financial-reports/dib-fs-ye-2025-en.pdf?sfvrsn=a... |
| 12 | `dubai-investment` | financial | United Arab Emirates | verified | verified | https://diweb.blob.core.windows.net/dubaiinvestmentcontainer/dip-images/public/1134/DI_... |
| 13 | `emirates-nbd-pjsc` | financial | United Arab Emirates | verified | verified | https://www.emiratesnbd.com/en/investor-relations/financial-information/annual-reports |
| 14 | `qnb-qatar-national-bank` | financial | Qatar | verified | verified | https://www.qnb.com/cs/Satellite/QNBQatar/en_QA/InvestorRelations/enAnnualReports |
| 15 | `kuwait-finance-house` | financial | Kuwait | verified | unreachable | https://kfh.com/en/reports/kuwait/Annual-Reports/Annual-Report-2025/document_en/KFH%20A... |
| 16 | `national-bank-of-kuwait` | financial | Kuwait | verified | unreachable | https://www.nbk.com/dam/jcr:73b1509e-5280-4ef3-a29a-392c1b565299/nbk-annual-report-2025... |
| 17 | `boubyan-bank` | financial | Kuwait | verified | unreachable | https://www.bankboubyan.com/en/investor-relations#annual-reports |
| 18 | `alafco-aviation-lease-and-finance-company` **(ALAFCO — Tier 3 path)** | financial | Kuwait | unreachable | unreachable | https://web.archive.org/web/2*/alafco.com/en/investors |
| 19 | `bank-muscat-bkmb` | financial | Oman | verified | verified | https://www.bankmuscat.om/en/investorrelations/AnnualReports/BM_AFS_2025_Audited_BM_Web... |
| 20 | `oman-international-development-and-investment-company` | financial | Oman | needs_human | verified | — |
| 21 | `sohar-international-bank` | financial | Oman | verified | verified | https://res.cloudinary.com/dtqjagydd/image/upload/v1775368385/Sohar_Int_Annual_Report20... |
| 22 | `bank-dhofar` | financial | Oman | unreachable | verified | https://www.bankdhofar.com/media/4edbsroz/annual-report-2023-en.pdf |
| 23 | `national-bank-of-bahrain` | financial | Bahrain | unreachable | verified | https://nbbonline.com/wp-content/uploads/2026/03/Annual-Financial-and-Sustainability-Re... |
| 24 | `saudi-aramco` | other | Saudi Arabia | verified | unreachable | https://www.aramco.com/-/media/publications/corporate-reports/reports-and-presentations... |
| 25 | `sabic` | other | Saudi Arabia | unreachable | unreachable | https://www.sabic.com/en/Images/SABIC-Integrated-Annual-Report-2025-EN_tcm1010-49452.pdf |
| 26 | `saudi-telecom-company` | other | Saudi Arabia | verified | unreachable | https://www.stc.com.sa/content/dam/stc/stc-annual-report-2023/ |
| 27 | `maaden` | other | Saudi Arabia | verified | unreachable | — |
| 28 | `saudi-electricity` | other | Saudi Arabia | unreachable | unreachable | https://www.se.com.sa/-/media/sec/Investors/Finance/SEC_Annual_Report_EN_23_V2.ashx |
| 29 | `yanbu-cement-company` | other | Saudi Arabia | verified | unreachable | https://www.saudiexchange.sa/Resources/fsPdf/428_0_2024-03-20_11-26-43_En.pdf |
| 30 | `saudi-arabian-fertilizer-company` | other | Saudi Arabia | unreachable | unreachable | — |
| 31 | `almarai` | other | Saudi Arabia | unreachable | unreachable | https://annualreport.almarai.com/assets/img/pdfs/Almarai%20AR%202024-English.pdf |
| 32 | `etihad-etisalat-mobily` | other | Saudi Arabia | verified | unreachable | https://www.mobily.com.sa/wps/wcm/connect/b619d237-477d-473f-b8aa-d2b59c662260/Earnings... |
| 33 | `savola-group` | other | Saudi Arabia | verified | unreachable | https://savola.blob.core.windows.net/website/docs/default-source/annual-reports/2026033... |
| 34 | `yanbu-national-petrochemical` | other | Saudi Arabia | unreachable | unreachable | https://www.yansab.com.sa/en/Images/YANSAB%20Annual%20Report%202025%20EN_tcm1047-49427.pdf |
| 35 | `dar-al-arkan-real-estate-development-company` | other | Saudi Arabia | verified | unreachable | https://cdn.daralarkan.com/DAR_annual_report_2025_EN_d044f7afc3.pdf |
| 36 | `emaar-the-economic-city` | other | Saudi Arabia | unreachable | unreachable | https://www.kaec.net/wp-content/uploads/2024/04/En-KAEC-Annual-Report-2023.pdf |
| 37 | `advanced-petrochemical` | other | Saudi Arabia | verified | unreachable | https://ir.advancedpetrochem.com/media/mbeiem5u/advanced_annual-report_2025_eng.pdf |
| 38 | `saudi-kayan-petrochemical-company` | other | Saudi Arabia | unreachable | unreachable | https://www.saudikayan.com/en/Images/Annual%20Report%202024%20SK_tcm1043-46850.pdf |
| 39 | `mouwasat-medical-services-company` | other | Saudi Arabia | verified | unreachable | https://www.mouwasat.com/en/annual-reports |
| 40 | `saudi-airlines-catering-company-catrion` | other | Saudi Arabia | verified | unreachable | https://www.catrion.com/application/files/4117/7565/9117/CATRION_En_AR25_07042026_compr... |
| 41 | `national-industrialization-co` | other | Saudi Arabia | unreachable | unreachable | https://www.tasnee.com/media/oxfi0ltt/tasnee-q2-2025-eng.pdf |
| 42 | `rabigh-refining-petrochemical-co` | other | Saudi Arabia | unreachable | unreachable | — |
| 43 | `sahara-international-petrochemical-co` | other | Saudi Arabia | verified | unreachable | https://www.sipchem.com/sites/default/files/annual-reports/28656b51-9878-49d3-8115-aff5... |
| 44 | `mobile-telecommunications-co-saudi-arabia-zain` | other | Saudi Arabia | verified | unreachable | — |
| 45 | `jarir-marketing-co` | other | Saudi Arabia | needs_human | unreachable | — |
| 46 | `saudi-cement` | other | Saudi Arabia | verified | unreachable | https://saudicement.com.sa/wp-content/themes/scc001/file-download.php?path=statement-fi... |
| 47 | `abdullah-al-othaim-markets` | other | Saudi Arabia | verified | unreachable | https://othaim-markets.eurolandir.com/media/g5glig4d/%D8%A7%D9%84%D8%AA%D9%82%D8%B1%D9%... |
| 48 | `abu-dhabi-national-oil-company-for-distribution` | other | United Arab Emirates | unreachable | verified | — |
| 49 | `emirates-telecom-etisalat-group` | other | United Arab Emirates | verified | verified | https://eand.com/en/system/com/assets/docs/annual-report/2022/en-2022-eand-group-annual... |
| 50 | `abu-dhabi-national-energy-company` | other | United Arab Emirates | verified | verified | https://www.taqa.com/wp-content/uploads/2020/06/20200420_TAQA-2019-Annual-Report-En-vWe... |
| 51 | `aldar-properties-pjsc` | other | United Arab Emirates | unreachable | verified | https://cdn.aldar.com/-/media/project/aldar-tenant/aldar2/investors-documents/aldar-pro... |
| 52 | `emaar-properties` | other | United Arab Emirates | verified | verified | — |
| 53 | `air-arabia-pjsc` | other | United Arab Emirates | verified | verified | https://www.airarabia.com/-/media/investor-relations/2024/annualreport_2024.pdf |
| 54 | `industries-qatar` | other | Qatar | verified | verified | https://iq.com.qa/media/eusnovi0/iq-annual-report-2023-en-5.pdf |
| 55 | `ooredoo-q-p-s-c` | other | Qatar | verified | verified | https://www.ooredoo.com/wp-content/uploads/2025/03/Ooredoo_Annual-Report_2024_English.pdf |
| 56 | `qatar-fuel-company-woqod` | other | Qatar | verified | verified | — |
| 57 | `baladna` | other | Qatar | verified | verified | https://baladna.com/2024/baladna/ |
| 58 | `gulf-international-services` | other | Qatar | verified | verified | https://www.gis.com.qa/media/cqvjhu05/gis_-ir-presentation-ye-25-eng.pdf |
| 59 | `qatar-gas-transport-co-nakilat` | other | Qatar | verified | verified | https://www.nakilat.com/wp-content/uploads/2026/02/Annual-Report-2025-English.pdf |
| 60 | `zain-mobile-telecommunications-company` | other | Kuwait | verified | unreachable | — |
| 61 | `kuwait-telecommunications-company` | other | Kuwait | unreachable | unreachable | https://cws.stc.com.kw/DigitalStatic/AnnualReport2022/Digital-Annual-Report-2022-En.html |
| 62 | `tamdeen-real-estate-company` | other | Kuwait | needs_human | unreachable | — |
| 63 | `oman-telecommunications-company-otel` | other | Oman | unreachable | verified | https://ir.omantel.om/media/ku4l2bbt/annual-report-2022-en.pdf |
| 64 | `bahrain-telecommunications-beyon` | other | Bahrain | verified | verified | https://beyon.com/wp-content/uploads/2026/03/Beyon_AR2025_English.pdf |
| 65 | `aluminium-bahrain-alba` | other | Bahrain | verified | verified | https://www.albasmelter.com/uploads/Alba_Annual_Report_2025_1.pdf |

## Counts

### By wave

| wave | rows | ir verified | ir unreachable | ir needs_human | exch verified | exch unreachable | exch needs_human |
|---|---|---|---|---|---|---|---|
| financial | 23 | 17 | 5 | 1 | 12 | 11 | 0 |
| other | 42 | 27 | 13 | 2 | 15 | 27 | 0 |
| total | 65 | 44 | 18 | 3 | 27 | 38 | 0 |

### Combined coverage (ALAFCO reported separately)

Of the 64 non-ALAFCO institutions:

| combination | count |
|---|---|
| both | 20 |
| ir_only | 24 |
| exchange_only | 7 |
| neither | 13 |

**ALAFCO** (reported separately): both IR and exchange `unreachable`, but with a documented Tier-3 path — Wayback Machine has 36 captures of alafco.com/en/investors between 2021-03-05 and 2025-05-23. Delisted from Boursa Kuwait on 2025-03-05 before FY2025 closed. See `data/alafco_gaps.json` for one gap row per target year with `tier_tried = live, next_action = Tier 3 Wayback Machine` (and FY2025 marked as confirmed non-existent).

### `neither` breakdown (the real Tier 3/4 backlog)

| slug | wave | country | ir status | exchange status | why |
|---|---|---|---|---|---|
| `almarai` | other | Saudi Arabia | unreachable | unreachable | WebFetch 406 on primary URL; search evidence has canonical 2024 PDF. annualreport.almarai.com host loads in... |
| `bupa-arabia-for-cooperative-insurance-company` | financial | Saudi Arabia | unreachable | unreachable | WAF rejects WebFetch UA; Session 4 crawler with descriptive UA may or may not clear it. |
| `emaar-the-economic-city` | other | Saudi Arabia | unreachable | unreachable | Registered on Tadawul as 'Emaar The Economic City' but branded as KAEC (King Abdullah Economic City). |
| `jarir-marketing-co` | other | Saudi Arabia | needs_human | unreachable | Search returned no clear IR page on jarirbookstore.com or jarir.com.sa — only third-party sources (marketsc... |
| `kuwait-telecommunications-company` | other | Kuwait | unreachable | unreachable | STC Kuwait, formerly VIVA. Majority owned by Saudi STC Group. |
| `national-industrialization-co` | other | Saudi Arabia | unreachable | unreachable | Also known as TASNEE. |
| `rabigh-refining-petrochemical-co` | other | Saudi Arabia | unreachable | unreachable | Also known as Petro Rabigh. |
| `sabic` | other | Saudi Arabia | unreachable | unreachable | WebFetch failed with 'too many redirects'. Search evidence has canonical PDFs. |
| `saudi-arabian-fertilizer-company` | other | Saudi Arabia | unreachable | unreachable | Also known as SABIC Agri-Nutrients; may also be at sabic-agrinutrients.com. |
| `saudi-electricity` | other | Saudi Arabia | unreachable | unreachable | Rebranded to Saudi Energy Feb 2026 per press coverage. |
| `saudi-kayan-petrochemical-company` | other | Saudi Arabia | unreachable | unreachable | WebFetch ECONNREFUSED; search evidence has canonical PDFs. |
| `tamdeen-real-estate-company` | other | Kuwait | needs_human | unreachable | Search did not surface a Tamdeen Real Estate IR page on tamdeen.com; parent 'Tamdeen Group' has the tamdeen... |
| `yanbu-national-petrochemical` | other | Saudi Arabia | unreachable | unreachable | News page loads but PDF list needs JS; search evidence surfaced canonical PDFs. |
