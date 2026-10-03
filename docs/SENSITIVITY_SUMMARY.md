# Sensitivity analysis

_Verity sensitivity analysis  |  taxonomy=4948c00426fa70118328478fe6e1d782c981cb65024378fe11af6a561faef340  |  generated=2026-10-02T20:07:38+00:00  |  n_institutions=42 (43 scored - rabigh-refining-petrochemical-co artifact)  |  within-sector only_

Three tests, all within-sector (financial vs non-financial), 42 institutions (43 scored minus `rabigh-refining-petrochemical-co`, artifact-flagged).

## 1. Weight jitter — U(0.8, 1.2), 1000 draws
- Seed: `20261002` (reproducible).
- Kendall tau vs baseline, financial sector: median = **0.985**, 5-95% = [0.970, 0.985].
- Kendall tau vs baseline, non-financial sector: median = **0.973**, 5-95% = [0.947, 0.993].

### Financial — per-institution rank stability

| slug | years | baseline rank | median | 5-95% rank interval | width |
|---|---:|---:|---:|---|---:|
| `qnb-qatar-national-bank` | 5 | 1 | 1 | [1, 1] | 0 |
| `first-abu-dhabi-bank` | 5 | 2 | 2 | [2, 3] | 1 |
| `national-bank-of-bahrain` | 3 | 3 | 3 | [2, 3] | 1 |
| `emirates-nbd-pjsc` | 4 | 4 | 4 | [4, 5] | 1 |
| `abu-dhabi-commercial-bank` | 3 | 5 | 5 | [4, 5] | 1 |
| `national-bank-of-kuwait` | 4 | 6 | 6 | [6, 6] | 0 |
| `al-rajhi-bank` | 5 | 7 | 7 | [7, 7] | 0 |
| `alinma-bank` | 5 | 8 | 8 | [8, 8] | 0 |
| `kuwait-finance-house` | 3 | 9 | 9 | [9, 9] | 0 |
| `the-national-bank-of-ras-al-khaimah` | 1 | 10 | 10 | [10, 10] | 0 |
| `the-saudi-national-bank` | 1 | 11 | 11 | [11, 11] | 0 |
| `bank-muscat-bkmb` | 1 | 12 | 12 | [12, 12] | 0 |
| `sohar-international-bank` | 2 | 13 | 13 | [13, 13] | 0 |
| `saudi-industrial-investment-group` | 3 | 14 | 14 | [14, 14] | 0 |
| `bank-albilad` | 1 | 15 | 15 | [15, 15] | 0 |
| `dubai-investment` | 1 | 16 | 17 | [17, 17] | 0 |
| `dubai-islamic-bank` | 2 | 17 | 16 | [16, 16] | 0 |

### Non-financial — per-institution rank stability

| slug | years | baseline rank | median | 5-95% rank interval | width |
|---|---:|---:|---:|---|---:|
| `zain-mobile-telecommunications-company` | 1 | 1 | 1 | [1, 1] | 0 |
| `jarir-marketing-co` | 1 | 2 | 2 | [2, 4] | 2 |
| `advanced-petrochemical` | 1 | 3 | 3 | [2, 4] | 2 |
| `baladna` | 3 | 4 | 4 | [3, 5] | 2 |
| `sabic` | 3 | 5 | 5 | [4, 5] | 1 |
| `emaar-properties` | 6 | 6 | 6 | [6, 8] | 2 |
| `abdullah-al-othaim-markets` | 2 | 7 | 7 | [6, 8] | 2 |
| `qatar-gas-transport-co-nakilat` | 4 | 8 | 8 | [7, 9] | 2 |
| `maaden` | 2 | 9 | 9 | [7, 9] | 2 |
| `dar-al-arkan-real-estate-development-company` | 1 | 10 | 10 | [10, 10] | 0 |
| `ooredoo-q-p-s-c` | 5 | 11 | 11 | [11, 12] | 1 |
| `abu-dhabi-national-energy-company` | 5 | 12 | 12 | [11, 12] | 1 |
| `abu-dhabi-national-oil-company-for-distribution` | 5 | 13 | 13 | [13, 13] | 0 |
| `emirates-telecom-etisalat-group` | 4 | 14 | 14 | [14, 15] | 1 |
| `almarai` | 5 | 15 | 15 | [14, 15] | 1 |
| `qatar-fuel-company-woqod` | 4 | 16 | 16 | [16, 17] | 1 |
| `aluminium-bahrain-alba` | 5 | 17 | 17 | [16, 17] | 1 |
| `saudi-aramco` | 1 | 18 | 18 | [18, 18] | 0 |
| `oman-telecommunications-company-otel` | 2 | 19 | 19 | [19, 19] | 0 |
| `national-industrialization-co` | 1 | 20 | 20 | [20, 21] | 1 |
| `bahrain-telecommunications-beyon` | 5 | 21 | 21 | [20, 21] | 1 |
| `savola-group` | 2 | 22 | 22 | [22, 22] | 0 |
| `industries-qatar` | 6 | 23 | 24 | [23, 24] | 1 |
| `aldar-properties-pjsc` | 1 | 24 | 23 | [23, 24] | 1 |
| `gulf-international-services` | 4 | 25 | 25 | [25, 25] | 0 |

## 2. Equal weights (all weights = 1.0)
- Spearman vs baseline, financial sector: **0.998**
- Spearman vs baseline, non-financial sector: **0.997**

Rank changes under equal weights:

**Financial** — moves ≥ 3 positions:

**Non-financial** — moves ≥ 3 positions:

## 3. Switch tests
### `toc_off`
- Spearman fin = **1.000**, non-fin = **1.000**
- Financial: no moves ≥ 3 positions.
- Non-financial: no moves ≥ 3 positions.

### `repeat_off`
- Spearman fin = **0.961**, non-fin = **0.995**
- Financial moves ≥ 3: `al-rajhi-bank` 7→2 (-5)
- Non-financial: no moves ≥ 3 positions.

### `all_mode`
- Spearman fin = **1.000**, non-fin = **0.996**
- Financial: no moves ≥ 3 positions.
- Non-financial: no moves ≥ 3 positions.

## Single-year institutions with high rank volatility (jitter interval ≥ cohort/3)

_(none — no single-year institutions show high jitter volatility)_

