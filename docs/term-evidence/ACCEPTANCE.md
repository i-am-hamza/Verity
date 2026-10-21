# Term Acceptance — Taxonomy v5 (Examiner Additions)

_Added at examiner's request, verified by the examiner  |  Date: 2026-10-20_
_Rule: appears in at least 10% of relevant reports AND at least 14 of 20 genuine sentences_

16 new term concepts (variants on one line = one concept).
Frequencies reported from Verity's own v5 corpus after rescoring; "relevant" = industries
where the term's SASB category is material (all 390 if SASB category = none).

| Concept | SASB category | Pillar | Decision |
|---|---|---|:---:|
| `climate policy` | GHG Emissions | E | ✅ ADDED |
| `pollution` | Ecological Impacts | E | ✅ ADDED |
| `resource use` | Materials Sourcing & Efficiency | E | ✅ ADDED |
| `innovation` | none | E | ✅ ADDED |
| `employee engagement` | Employee Engagement, Diversity & Inclusion | S | ✅ ADDED |
| `employee ownership` / `employee share ownership` | Employee Engagement, Diversity & Inclusion | S | ✅ ADDED |
| `pension benefits` | Labor Practices | S | ✅ ADDED |
| `end of service` / `end-of-service` | Labor Practices | S | ✅ ADDED |
| `poverty` | Human Rights & Community Relations | S | ✅ ADDED |
| `customer needs` / `customers' needs` / `client needs` / `clients' needs` | Customer Welfare | S | ✅ ADDED |
| `feedback` | none | S | ✅ ADDED |
| `digital services` | Access & Affordability | S | ✅ ADDED |
| `board meeting(s)` / `meetings of directors` / `meetings of the board` | none | G | ✅ ADDED |
| `dividend policy` | none | G | ✅ ADDED |
| `stakeholder engagement` | none | G | ✅ ADDED |
| `incentive plan(s)` | none | G | ✅ ADDED |

Notes:
- Terms with SASB category "none" are never material: weight = 1.0 everywhere.
- Variant phrases sharing one concept row are implemented as separate DB rows.
- `end-of-service` uses exact (case-insensitive) matching (lemma_based=False) to avoid
  spaCy's ambiguous tokenization of hyphenated compounds.
- `customers' needs` and `clients' needs` use exact matching (lemma_based=False) because
  the apostrophe disrupts spaCy's lemma patterns; the canonical `customer needs` and
  `client needs` (lemma_based=True) cover the non-apostrophe forms.
- `board meeting` (lemma_based=True) covers both "board meeting" and "board meetings";
  `incentive plan` (lemma_based=True) covers "incentive plan" and "incentive plans" —
  no separate plural row needed.
- Overlap with v4: `meetings of the board` (new, 4 tokens) vs `board of directors` (v4,
  3 tokens) overlap in "meetings of the board of directors". Longest-match-wins resolves
  it (new phrase takes priority). Both are Governance/None — no pillar or SASB impact.

---

# Taxonomy v6 — Component Restructuring

_Date: 2026-10-20 | Researcher decision after diagnostic review of v5 term contributions_

## Decision A — All 16 examiner terms retained

All 16 examiner-requested terms from the table above are kept in the taxonomy.
Sensitivity analysis (§3 of V5_DIAGNOSTICS.md) shows composite Spearman vs v4 ≥ 0.974
even without `innovation`, `feedback`, and `digital services`, confirming the
structure is robust.

## Decision B — New GENERAL component (amends Decision 3 from v4 build)

A fourth scoring component is introduced: **General ESG terms**, pillar = "General",
weight = 1.0, SASB category = none.

Composition (8 terms): ESG, sustainability, GRI, sustainable development, CSR
(previously counted separately as "generic", now scored), plus innovation,
feedback, and digital services (moved from E and S respectively).

Rationale: innovation dominated the Environmental pillar (62% of all new-term
mentions, 96.9% of E-pillar new-term mentions) and is not an environmental
topic per se. Placing it — along with feedback and digital services — in a
separate General component prevents it from distorting the E pillar while still
capturing its contribution to the composite. The five previously-generic terms
are now scored in the same General bucket rather than being silently excluded.

The Environmental term count falls from 25 → 22;
the Social term count falls from 29 → 26;
the General component has 8 terms.

## Decision C — Scoring scale changed to 0-100 (amends Decision 6 from v4 build)

All pillar scores (E, S, G, General) and the composite are now scaled **0–100**
(same ascending rank formula × 10). One decimal place stored.

Composite (0–100) = average(E, S, G, General) — four equally-weighted components.

Two robustness columns added per company-year:
- `composite_3pillar`: composite from E, S, G only (no General), 0–100.
- `composite_general_no_new3`: composite where General is computed from the five
  original generic terms only (no innovation, feedback, digital services), 0–100.

---

# Term Acceptance — Phase 2 Coding Review

_Coded by: researcher  |  Coding sheet: `docs/term-evidence/coding_sheet_recode.xlsx`_
_Rule: at least 70 % "Yes" (≥ 14 of 20 coded sentences) → accepted_
_"yy" cells treated as "Yes" per researcher instruction_
_Date: 2026-10-10_

20 terms coded (the 20 PASS terms from the Phase 2 frequency test, seed=20261006,
≤ 20 sentences each, max 3 per company).

| Term | SASB category | Yes | No | yy | Total coded | % Yes | Decision |
|---|---|---:|---:|---:|---:|---:|:---:|
| `air quality` | Air Quality | 17 | 3 | 0 | 20 | 85 % | ✅ ACCEPTED |
| `NOx` | Air Quality | 13 | 5 | 0 | 18 | 72 % | ✅ ACCEPTED |
| `flaring` | Air Quality | 14 | 6 | 0 | 20 | 70 % | ✅ ACCEPTED |
| `LEED` | Product Design & Lifecycle Management | 18 | 2 | 0 | 20 | 90 % | ✅ ACCEPTED |
| `e-waste` | Product Design & Lifecycle Management | 14 | 6 | 0 | 20 | 70 % | ✅ ACCEPTED |
| `circular economy` | Materials Sourcing & Efficiency | 15 | 5 | 0 | 20 | 75 % | ✅ ACCEPTED |
| `food safety` | Product Quality & Safety | 16 | 4 | 0 | 20 | 80 % | ✅ ACCEPTED |
| `product safety` | Product Quality & Safety | 17 | 1 | 0 | 18 | 94 % | ✅ ACCEPTED |
| `responsible sourcing` | Materials Sourcing & Efficiency | 15 | 5 | 0 | 20 | 75 % | ✅ ACCEPTED |
| `process safety` | Critical Incident Risk Management | 17 | 1 | 2 | 20 | 95 % | ✅ ACCEPTED |
| `asset integrity` | Critical Incident Risk Management | 17 | 3 | 0 | 20 | 85 % | ✅ ACCEPTED |
| `emergency preparedness` | Critical Incident Risk Management | 19 | 0 | 1 | 20 | 100 % | ✅ ACCEPTED |
| `business continuity` | Systemic Risk Management | 20 | 0 | 0 | 20 | 100 % | ✅ ACCEPTED |
| `stress testing` | Systemic Risk Management | 19 | 1 | 0 | 20 | 95 % | ✅ ACCEPTED |
| `anti-competitive` | Competitive Behavior | 12 | 8 | 0 | 20 | 60 % | ❌ REJECTED |
| `emergency response` | Critical Incident Risk Management | 13 | 7 | 0 | 20 | 65 % | ❌ REJECTED |
| `nutrition` | Customer Welfare | 17 | 3 | 0 | 20 | 85 % | ❌ EXCLUDED (researcher decision A.5) |
| `public policy` | Management of the Legal & Regulatory Environment | 12 | 8 | 0 | 20 | 60 % | ❌ REJECTED |
| `spill` | Critical Incident Risk Management | 9 | 11 | 0 | 20 | 45 % | ❌ REJECTED |
| `systemic risk` | Systemic Risk Management | 9 | 11 | 0 | 20 | 45 % | ❌ REJECTED |

## Summary

- **13 accepted → added to taxonomy v4 core** (air quality, NOx, flaring, LEED, e-waste,
  circular economy, food safety, product safety, responsible sourcing, process safety,
  asset integrity, emergency preparedness, business continuity)
- **1 accepted → added to taxonomy v4 financial add-on** (stress testing)
- **4 rejected** (anti-competitive, emergency response, public policy, spill, systemic risk —
  emergency response, anti-competitive, public policy, systemic risk, spill did not reach 70 %)
- **1 accepted but excluded by researcher instruction** (nutrition — accepted at 85 % but
  the researcher's A.5 list explicitly excludes it from the taxonomy)

Notes:
- `NOx` had only 18 coded sentences (fewer than 20 sample hits with the max-3-per-company
  constraint); 72 % based on 18 sentences.
- `product safety` had 18 coded sentences for the same reason.
- `emergency preparedness` had 1 "yy" cell treated as Yes per instruction.
- `process safety` had 2 "yy" cells treated as Yes per instruction.
