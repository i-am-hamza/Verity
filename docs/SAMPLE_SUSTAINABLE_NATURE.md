# Candidate-term sample: `sustainable` + `nature`

15 random sentences per term across the 6 recall-audit reports. Seed 42.
Classifications are my judgement — intentionally conservative on "ESG" so you
see the generic uses that would be matched if the term were added raw.

## `sustainable` — ESG 11/15 (73%), Generic 4/15

| # | slug | FY | sentence (truncated) | verdict |
|---|---|---|---|---|
| 1 | `al-rajhi-bank` | 2025 | "...environmental stewardship and climate action **sustainable development**..." | **ESG** (section header around disclosures) |
| 2 | `al-rajhi-bank` | 2025 | "...diversity and inclusion ... environmental stewardship ... **sustainable development** alrajhi bank continued to invest significantly in its L&D..." | **ESG** (same section) |
| 3 | `bank-muscat-bkmb` | 2025 | "...Recovery and Resolution Planning (RRP) document to formalize a process of self-propelled, stable and **sustainable recovery** in an extreme eventuality." | **Generic** (financial recovery, not ESG) |
| 4 | `first-abu-dhabi-bank` | 2025 | "Delivered key capabilities and platforms supporting **sustainable revenue generation**." | **Generic** (business language) |
| 5 | `first-abu-dhabi-bank` | 2025 | "...sustainability objectives... **Sustainable Finance Framework**, ESG Policy and E&S Risk Policy." | **ESG** (explicit framework) |
| 6 | `al-rajhi-bank` | 2025 | "...**sustainable financing at alrajhi bank** customer engagement and responsible banking community development..." | **ESG** (section anchor) |
| 7 | `kuwait-finance-house` | 2024 | "...achieve **sustainable growth** by providing innovative investment solutions..." | **Generic** (growth language) |
| 8 | `al-rajhi-bank` | 2025 | "...resilient, secure, and trustworthy technology ecosystem that supports **sustainable growth**." | **Generic** (IT risk context) |
| 9 | `al-rajhi-bank` | 2025 | "...long-term source of **sustainable funding** for impactful social initiatives." | **ESG** (modifying social-impact funding) |
| 10 | `al-rajhi-bank` | 2025 | "...**sustainable development** environmental performance ... greenhouse gas emissions, water management, waste handling, biodiversity..." | **ESG** |
| 11 | `al-rajhi-bank` | 2025 | "...**sustainable financing at alrajhi bank** customer engagement and responsible banking..." | **ESG** (same anchor) |
| 12 | `al-rajhi-bank` | 2025 | "...focus on **sustainable/ESG financing**, and a rise in SME financing opportunities..." | **ESG** (explicit) |
| 13 | `al-rajhi-bank` | 2025 | "KSA Vision 2030 ... KSA Net Zero 2030 Total **sustainable financing** USD 6.9 Bn." | **ESG** |
| 14 | `the-saudi-national-bank` | 2025 | "...new **sustainable product development** workstreams were launched ... sustainability-linked financial solutions..." | **ESG** |
| 15 | `first-abu-dhabi-bank` | 2025 | "...infrastructure and **sustainable finance**, and the continued digitisation..." | **ESG** |

## `nature` — ESG 5/15 (33%), Generic 10/15

| # | slug | FY | sentence (truncated) | verdict |
|---|---|---|---|---|
| 1 | `first-abu-dhabi-bank` | 2025 | "...expanded its internal methodologies to identify **nature-sensitive sectors** across its portfolios." | **ESG** (TNFD-style phrasing) |
| 2 | `first-abu-dhabi-bank` | 2025 | "...the **nature of the benefit**, which is a lump sum payable on exit..." | **Generic** (accounting) |
| 3 | `first-abu-dhabi-bank` | 2025 | "...the effects... will be longer term in **nature**..." | **Generic** (idiomatic) |
| 4 | `first-abu-dhabi-bank` | 2025 | "...Supporting the global transition to a low-carbon and **nature-positive** future..." | **ESG** |
| 5 | `first-abu-dhabi-bank` | 2025 | "We provided a platform for UAE SMEs with **nature-positive innovations**..." | **ESG** |
| 6 | `first-abu-dhabi-bank` | 2025 | "...climate and **nature-related risks** and expectations around the transition..." | **ESG** (TNFD) |
| 7 | `first-abu-dhabi-bank` | 2025 | "The Group may be Wakil or Muwakkil depending on the **nature of the transaction**." | **Generic** |
| 8 | `bank-muscat-bkmb` | 2025 | "...wide range of business relationships and **nature of existing contractual agreements**..." | **Generic** |
| 9 | `first-abu-dhabi-bank` | 2025 | "'Advancing **Nature** and Water Sustainability in MENA'..." | **ESG** |
| 10 | `bank-muscat-bkmb` | 2025 | "...**Nature of assets** Residential / commercial property..." | **Generic** (table header) |
| 11 | `the-saudi-national-bank` | 2025 | "...the Group has determined classes of assets... on the basis of their **nature, characteristics and risks**..." | **Generic** |
| 12 | `the-saudi-national-bank` | 2025 | "...identification of the hedging instrument, the related hedged item, the **nature of risk being hedged**..." | **Generic** |
| 13 | `bank-muscat-bkmb` | 2025 | "...the hedged item, the **nature of the risk being hedged** and how the entity will assess..." | **Generic** |
| 14 | `al-rajhi-bank` | 2025 | "...determined based on the **nature of the business**, its risks..." | **Generic** |
| 15 | `first-abu-dhabi-bank` | 2025 | "...these engagements, including the **nature and amounts**, shall be reported..." | **Generic** |

## Verdict summary

- **`sustainable`** — 11/15 (73%) ESG. Legitimate signal across chair statements,
  section headers ("sustainable development", "sustainable financing"), and framework
  references ("Sustainable Finance Framework"). Generic failures are all "sustainable
  growth" / "sustainable revenue" business-speak. **Decision point**: add as a bare
  term and accept ~25% false-positive rate, OR add as narrower multi-word phrases
  (`sustainable finance` is already in Env; `sustainable development`, `sustainable
  financing` would catch most of the real signal with much higher precision).
- **`nature`** — only 5/15 (33%) ESG. 10/15 are accounting boilerplate ("nature of
  the X"). Adding bare `nature` would inflate Env with noise. **However**, all 5
  ESG uses are compound phrases: `nature-sensitive`, `nature-positive`,
  `nature-related`, `Nature and Water`. **Recommendation**: don't add bare `nature`
  — add `nature-positive` (+ optionally `nature-related` / `TNFD`) which track the
  real signal.
