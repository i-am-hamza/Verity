# Processing QA

Generated 2026-10-10T12:44:58+00:00.

Reports processed: **1205** (threshold-flagged: **823**, IQR-flagged: **0**).

IQR cohort = fiscal year. A composite more than 3xIQR from Q1/Q3 of its cohort is flagged as a processing outlier (Report.processing_review_status = needs_review). Cohorts with fewer than 5 scored reports are labelled low-confidence.

## Cohort IQR bounds

| FY | n | median | Q1 | Q3 | lower | upper | note |
|---|---|---|---|---|---|---|---|
| 2020 | 65 | 3.797 | 2.595 | 4.910 | -4.351 | 11.856 |  |
| 2021 | 65 | 4.149 | 3.209 | 5.636 | -4.072 | 12.916 |  |
| 2022 | 64 | 4.794 | 3.531 | 6.151 | -4.330 | 14.012 |  |
| 2023 | 65 | 5.120 | 3.643 | 6.482 | -4.875 | 15.000 |  |
| 2024 | 65 | 6.211 | 4.278 | 7.272 | -4.704 | 16.255 |  |
| 2025 | 65 | 6.503 | 4.682 | 7.668 | -4.274 | 16.624 |  |

## Per-report audit

| slug | FY | status | pages | Latin words | OCR frac | Ar pages | ToC pages | repeat lines | FS start | matches | all-mode extra | composite | flag |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `abdullah-al-othaim-markets` | 2020 | scored | 67 | 15229 | 0.06 | 0 | — | 64 | — | 24 | 0 | 1.598 |  |
| `abdullah-al-othaim-markets` | 2020 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `abdullah-al-othaim-markets` | 2020 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `abdullah-al-othaim-markets` | 2021 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `abdullah-al-othaim-markets` | 2021 | scored | 33 | 17209 | 0.00 | 0 | — | 246 | — | 36 | 3 | 3.187 |  |
| `abdullah-al-othaim-markets` | 2021 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `abdullah-al-othaim-markets` | 2022 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `abdullah-al-othaim-markets` | 2022 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `abdullah-al-othaim-markets` | 2022 | scored | 72 | 19305 | 0.03 | 0 | — | 69 | — | 86 | 5 | 5.971 |  |
| `abdullah-al-othaim-markets` | 2023 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `abdullah-al-othaim-markets` | 2023 | scored | 62 | 21600 | 0.00 | 0 | — | 125 | — | 78 | 5 | 6.452 |  |
| `abdullah-al-othaim-markets` | 2023 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `abdullah-al-othaim-markets` | 2024 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `abdullah-al-othaim-markets` | 2024 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `abdullah-al-othaim-markets` | 2024 | scored | 66 | 25221 | 0.05 | 0 | — | 228 | — | 94 | 3 | 6.418 |  |
| `abdullah-al-othaim-markets` | 2025 | scored | 75 | 24209 | 0.08 | 0 | — | 784 | — | 144 | 7 | 7.646 |  |
| `abdullah-al-othaim-markets` | 2025 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `abdullah-al-othaim-markets` | 2025 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `abu-dhabi-commercial-bank` | 2020 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `abu-dhabi-commercial-bank` | 2020 | scored | 144 | 98465 | 0.00 | 0 | — | 497 | 83 | 209 | 22 | 4.888 |  |
| `abu-dhabi-commercial-bank` | 2020 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `abu-dhabi-commercial-bank` | 2021 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `abu-dhabi-commercial-bank` | 2021 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `abu-dhabi-commercial-bank` | 2021 | scored | 149 | 92890 | 0.01 | 0 | — | 477 | 96 | 243 | 16 | 4.313 |  |
| `abu-dhabi-commercial-bank` | 2022 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `abu-dhabi-commercial-bank` | 2022 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `abu-dhabi-commercial-bank` | 2022 | scored | 165 | 98427 | 0.00 | 0 | — | 431 | 114 | 429 | 20 | 6.770 |  |
| `abu-dhabi-commercial-bank` | 2023 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `abu-dhabi-commercial-bank` | 2023 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `abu-dhabi-commercial-bank` | 2023 | scored | 189 | 110078 | 0.00 | 0 | — | 248 | 138 | 607 | 30 | 7.139 |  |
| `abu-dhabi-commercial-bank` | 2024 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `abu-dhabi-commercial-bank` | 2024 | scored | 202 | 126004 | 0.00 | 0 | — | 190 | 128 | 658 | 33 | 7.543 |  |
| `abu-dhabi-commercial-bank` | 2024 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `abu-dhabi-commercial-bank` | 2025 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `abu-dhabi-commercial-bank` | 2025 | scored | 203 | 129909 | 0.00 | 0 | — | 94 | 149 | 781 | 24 | 7.079 |  |
| `abu-dhabi-commercial-bank` | 2025 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `abu-dhabi-national-energy-company` | 2020 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `abu-dhabi-national-energy-company` | 2020 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `abu-dhabi-national-energy-company` | 2020 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `abu-dhabi-national-energy-company` | 2020 | scored | 124 | 49249 | 0.00 | 0 | — | 712 | 52 | 36 | 4 | 3.548 |  |
| `abu-dhabi-national-energy-company` | 2021 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `abu-dhabi-national-energy-company` | 2021 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `abu-dhabi-national-energy-company` | 2021 | scored | 174 | 52758 | 0.04 | 0 | 3 | 165 | 83 | 85 | 4 | 4.983 |  |
| `abu-dhabi-national-energy-company` | 2021 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `abu-dhabi-national-energy-company` | 2022 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `abu-dhabi-national-energy-company` | 2022 | scored | 98 | 57994 | 0.00 | 0 | — | 262 | 46 | 158 | 8 | 5.739 |  |
| `abu-dhabi-national-energy-company` | 2022 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `abu-dhabi-national-energy-company` | 2023 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `abu-dhabi-national-energy-company` | 2023 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `abu-dhabi-national-energy-company` | 2023 | scored | 129 | 65744 | 0.00 | 0 | — | 1110 | 72 | 203 | 7 | 6.297 |  |
| `abu-dhabi-national-energy-company` | 2024 | scored | 305 | 105694 | 0.00 | 1 | — | 2728 | 182 | 526 | 15 | 8.462 |  |
| `abu-dhabi-national-energy-company` | 2024 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `abu-dhabi-national-energy-company` | 2024 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `abu-dhabi-national-energy-company` | 2025 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `abu-dhabi-national-energy-company` | 2025 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `abu-dhabi-national-energy-company` | 2025 | scored | 326 | 119153 | 0.00 | 0 | — | 3022 | 189 | 689 | 15 | 8.780 |  |
| `abu-dhabi-national-oil-company-for-distribution` | 2020 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `abu-dhabi-national-oil-company-for-distribution` | 2020 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `abu-dhabi-national-oil-company-for-distribution` | 2020 | scored | 61 | 37903 | 0.02 | 0 | — | 106 | 38 | 46 | 10 | 3.565 |  |
| `abu-dhabi-national-oil-company-for-distribution` | 2020 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `abu-dhabi-national-oil-company-for-distribution` | 2021 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `abu-dhabi-national-oil-company-for-distribution` | 2021 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `abu-dhabi-national-oil-company-for-distribution` | 2021 | scored | 66 | 38683 | 0.03 | 0 | — | 86 | 44 | 71 | 9 | 3.763 |  |
| `abu-dhabi-national-oil-company-for-distribution` | 2022 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `abu-dhabi-national-oil-company-for-distribution` | 2022 | scored | 67 | 40706 | 0.01 | 0 | — | 144 | 46 | 138 | 8 | 5.189 |  |
| `abu-dhabi-national-oil-company-for-distribution` | 2022 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `abu-dhabi-national-oil-company-for-distribution` | 2023 | scored | 77 | 48813 | 0.01 | 0 | — | 202 | 52 | 170 | 6 | 6.194 |  |
| `abu-dhabi-national-oil-company-for-distribution` | 2023 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `abu-dhabi-national-oil-company-for-distribution` | 2023 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `abu-dhabi-national-oil-company-for-distribution` | 2023 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `abu-dhabi-national-oil-company-for-distribution` | 2024 | scored | 141 | 58952 | 0.00 | 0 | — | 142 | 111 | 377 | 13 | 7.449 |  |
| `abu-dhabi-national-oil-company-for-distribution` | 2024 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `abu-dhabi-national-oil-company-for-distribution` | 2024 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `abu-dhabi-national-oil-company-for-distribution` | 2025 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `abu-dhabi-national-oil-company-for-distribution` | 2025 | scored | 230 | 93637 | 0.00 | 0 | — | 231 | 182 | 738 | 13 | 8.677 |  |
| `abu-dhabi-national-oil-company-for-distribution` | 2025 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `advanced-petrochemical` | 2020 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `advanced-petrochemical` | 2020 | scored | 66 | 11038 | 0.00 | 0 | — | 90 | — | 16 | 0 | 2.139 |  |
| `advanced-petrochemical` | 2020 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `advanced-petrochemical` | 2021 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `advanced-petrochemical` | 2021 | scored | 50 | 13833 | 0.00 | 0 | — | 191 | — | 46 | 2 | 3.961 |  |
| `advanced-petrochemical` | 2021 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `advanced-petrochemical` | 2022 | uploaded | 65 | 0 | 1.00 | 0 | — | 0 | — | 0 | — | — | threshold |
| `advanced-petrochemical` | 2022 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `advanced-petrochemical` | 2022 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `advanced-petrochemical` | 2023 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `advanced-petrochemical` | 2023 | scored | 58 | 16094 | 0.00 | 0 | — | 95 | — | 81 | 1 | 5.009 |  |
| `advanced-petrochemical` | 2023 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `advanced-petrochemical` | 2024 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `advanced-petrochemical` | 2024 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `advanced-petrochemical` | 2024 | scored | 58 | 16377 | 0.00 | 0 | — | 95 | — | 84 | 1 | 5.430 |  |
| `advanced-petrochemical` | 2025 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `advanced-petrochemical` | 2025 | scored | 58 | 17128 | 0.00 | 0 | — | 391 | — | 73 | 1 | 3.694 |  |
| `advanced-petrochemical` | 2025 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `air-arabia-pjsc` | 2020 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `air-arabia-pjsc` | 2020 | scored | 28 | 7227 | 0.04 | 0 | — | 25 | — | 36 | 11 | 3.943 |  |
| `air-arabia-pjsc` | 2020 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `air-arabia-pjsc` | 2021 | scored | 22 | 10650 | 0.05 | 0 | — | 37 | — | 83 | 13 | 5.765 |  |
| `air-arabia-pjsc` | 2021 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `air-arabia-pjsc` | 2021 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `air-arabia-pjsc` | 2022 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `air-arabia-pjsc` | 2022 | scored | 44 | 12753 | 0.02 | 0 | — | 41 | — | 117 | 14 | 7.663 |  |
| `air-arabia-pjsc` | 2022 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `air-arabia-pjsc` | 2023 | scored | 100 | 31329 | 0.60 | 0 | 3 | 168 | 29 | 26 | 1 | 1.950 | threshold |
| `air-arabia-pjsc` | 2023 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `air-arabia-pjsc` | 2023 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `air-arabia-pjsc` | 2023 | uploaded | 100 | 0 | 0.60 | 0 | — | 0 | — | 0 | — | — | threshold |
| `air-arabia-pjsc` | 2024 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `air-arabia-pjsc` | 2024 | scored | 108 | 34113 | 0.60 | 0 | — | 189 | 28 | 17 | 0 | 2.002 | threshold |
| `air-arabia-pjsc` | 2024 | uploaded | 108 | 0 | 0.60 | 0 | — | 0 | — | 0 | — | — | threshold |
| `air-arabia-pjsc` | 2024 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `air-arabia-pjsc` | 2025 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `air-arabia-pjsc` | 2025 | scored | 106 | 31070 | 0.01 | 0 | 2 | 225 | 29 | 14 | 0 | 1.022 |  |
| `air-arabia-pjsc` | 2025 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `al-rajhi-bank` | 2020 | scored | 123 | 79028 | 0.05 | 0 | — | 167 | 72 | 256 | 5 | 4.347 |  |
| `al-rajhi-bank` | 2020 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `al-rajhi-bank` | 2020 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `al-rajhi-bank` | 2020 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `al-rajhi-bank` | 2021 | scored | 310 | 89613 | 0.02 | 0 | 6,7 | 2850 | 179 | 269 | 3 | 6.005 |  |
| `al-rajhi-bank` | 2021 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `al-rajhi-bank` | 2021 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `al-rajhi-bank` | 2021 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `al-rajhi-bank` | 2022 | scored | 159 | 94516 | 0.01 | 0 | 4 | 2641 | 91 | 341 | 4 | 6.478 |  |
| `al-rajhi-bank` | 2022 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `al-rajhi-bank` | 2022 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `al-rajhi-bank` | 2022 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `al-rajhi-bank` | 2023 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `al-rajhi-bank` | 2023 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `al-rajhi-bank` | 2023 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `al-rajhi-bank` | 2023 | scored | 368 | 105467 | 0.01 | 0 | 6,7,55 | 3111 | 247 | 437 | 3 | 6.787 |  |
| `al-rajhi-bank` | 2024 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `al-rajhi-bank` | 2024 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `al-rajhi-bank` | 2024 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `al-rajhi-bank` | 2024 | scored | 418 | 133899 | 0.01 | 0 | 6,7,47 | 4746 | 275 | 642 | 42 | 7.766 |  |
| `al-rajhi-bank` | 2025 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `al-rajhi-bank` | 2025 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `al-rajhi-bank` | 2025 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `al-rajhi-bank` | 2025 | scored | 432 | 134665 | 0.01 | 1 | 6,7 | 4768 | 282 | 700 | 45 | 7.998 |  |
| `aldar-properties-pjsc` | 2020 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `aldar-properties-pjsc` | 2020 | scored | 108 | 79416 | 0.01 | 0 | — | 284 | 42 | 109 | 1 | 4.253 |  |
| `aldar-properties-pjsc` | 2020 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `aldar-properties-pjsc` | 2021 | scored | 122 | 88058 | 0.01 | 0 | — | 687 | 77 | 213 | 5 | 4.493 |  |
| `aldar-properties-pjsc` | 2021 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `aldar-properties-pjsc` | 2021 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `aldar-properties-pjsc` | 2022 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `aldar-properties-pjsc` | 2022 | scored | 199 | 111758 | 0.01 | 0 | — | 7710 | 98 | 199 | 3 | 4.682 |  |
| `aldar-properties-pjsc` | 2022 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `aldar-properties-pjsc` | 2023 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `aldar-properties-pjsc` | 2023 | scored | 259 | 113561 | 0.00 | 0 | — | 5286 | 93 | 84 | 0 | 4.141 |  |
| `aldar-properties-pjsc` | 2023 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `aldar-properties-pjsc` | 2024 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `aldar-properties-pjsc` | 2024 | scored | 440 | 153277 | 0.00 | 0 | — | 2221 | 132 | 151 | 0 | 5.412 |  |
| `aldar-properties-pjsc` | 2024 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `aldar-properties-pjsc` | 2025 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `aldar-properties-pjsc` | 2025 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `aldar-properties-pjsc` | 2025 | scored | 390 | 156774 | 0.00 | 0 | — | 2590 | 112 | 199 | 1 | 5.928 |  |
| `alinma-bank` | 2020 | scored | 170 | 43203 | 0.07 | 0 | — | 174 | 73 | 61 | 0 | 3.978 |  |
| `alinma-bank` | 2020 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `alinma-bank` | 2020 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `alinma-bank` | 2021 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `alinma-bank` | 2021 | scored | 103 | 61473 | 0.00 | 0 | 5 | 645 | 58 | 73 | 0 | 2.311 |  |
| `alinma-bank` | 2021 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `alinma-bank` | 2022 | scored | 196 | 67668 | 0.01 | 0 | — | 1437 | 116 | 113 | 7 | 2.981 |  |
| `alinma-bank` | 2022 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `alinma-bank` | 2022 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `alinma-bank` | 2023 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `alinma-bank` | 2023 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `alinma-bank` | 2023 | scored | 260 | 70844 | 0.03 | 1 | 5 | 539 | 150 | 275 | 10 | 6.443 |  |
| `alinma-bank` | 2024 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `alinma-bank` | 2024 | scored | 155 | 81984 | 0.01 | 0 | — | 1051 | 92 | 355 | 12 | 6.529 |  |
| `alinma-bank` | 2024 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `alinma-bank` | 2025 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `alinma-bank` | 2025 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `alinma-bank` | 2025 | scored | 176 | 100307 | 0.00 | 0 | — | 1279 | 120 | 489 | 10 | 6.864 |  |
| `almarai` | 2020 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `almarai` | 2020 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `almarai` | 2020 | scored | 190 | 53554 | 0.01 | 0 | — | 526 | 117 | 119 | 9 | 5.851 |  |
| `almarai` | 2021 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `almarai` | 2021 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `almarai` | 2021 | scored | 192 | 54167 | 0.04 | 0 | — | 96 | 118 | 129 | 8 | 5.636 |  |
| `almarai` | 2022 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `almarai` | 2022 | scored | 195 | 57061 | 0.03 | 0 | — | 155 | 124 | 123 | 7 | 5.498 |  |
| `almarai` | 2022 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `almarai` | 2023 | scored | 194 | 55932 | 0.02 | 1 | — | 180 | 130 | 123 | 6 | 5.258 |  |
| `almarai` | 2023 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `almarai` | 2023 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `almarai` | 2024 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `almarai` | 2024 | scored | 202 | 58655 | 0.00 | 0 | — | 499 | 135 | 178 | 6 | 6.229 |  |
| `almarai` | 2024 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `almarai` | 2025 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `almarai` | 2025 | scored | 275 | 74226 | 0.00 | 0 | — | 2183 | 151 | 296 | 2 | 7.740 |  |
| `almarai` | 2025 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `aluminium-bahrain-alba` | 2020 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `aluminium-bahrain-alba` | 2020 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `aluminium-bahrain-alba` | 2020 | scored | 106 | 35940 | 0.04 | 1 | — | 305 | 48 | 33 | 1 | 2.912 |  |
| `aluminium-bahrain-alba` | 2021 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `aluminium-bahrain-alba` | 2021 | scored | 132 | 45135 | 0.04 | 0 | — | 654 | 67 | 67 | 2 | 3.290 |  |
| `aluminium-bahrain-alba` | 2021 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `aluminium-bahrain-alba` | 2022 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `aluminium-bahrain-alba` | 2022 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `aluminium-bahrain-alba` | 2022 | scored | 67 | 43331 | 0.00 | 0 | — | 318 | 35 | 104 | 5 | 3.153 |  |
| `aluminium-bahrain-alba` | 2023 | scored | 69 | 41795 | 0.00 | 0 | — | 350 | 40 | 108 | 4 | 4.416 |  |
| `aluminium-bahrain-alba` | 2023 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `aluminium-bahrain-alba` | 2023 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `aluminium-bahrain-alba` | 2024 | scored | 69 | 39520 | 0.00 | 0 | — | 355 | 40 | 110 | 7 | 4.605 |  |
| `aluminium-bahrain-alba` | 2024 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `aluminium-bahrain-alba` | 2024 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `aluminium-bahrain-alba` | 2025 | scored | 73 | 44799 | 0.00 | 0 | — | 234 | 42 | 200 | 14 | 7.560 |  |
| `aluminium-bahrain-alba` | 2025 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `aluminium-bahrain-alba` | 2025 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `bahrain-telecommunications-beyon` | 2020 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `bahrain-telecommunications-beyon` | 2020 | scored | 138 | 42770 | 0.01 | 0 | — | 426 | 86 | 62 | 5 | 4.321 |  |
| `bahrain-telecommunications-beyon` | 2020 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `bahrain-telecommunications-beyon` | 2021 | scored | 60 | 37129 | 0.02 | 0 | — | 499 | 34 | 25 | 0 | 2.397 |  |
| `bahrain-telecommunications-beyon` | 2021 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `bahrain-telecommunications-beyon` | 2021 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `bahrain-telecommunications-beyon` | 2022 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `bahrain-telecommunications-beyon` | 2022 | scored | 62 | 38474 | 0.00 | 0 | — | 340 | 37 | 47 | 3 | 3.428 |  |
| `bahrain-telecommunications-beyon` | 2022 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `bahrain-telecommunications-beyon` | 2023 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `bahrain-telecommunications-beyon` | 2023 | scored | 128 | 41444 | 0.00 | 0 | — | 469 | 78 | 45 | 5 | 3.497 |  |
| `bahrain-telecommunications-beyon` | 2023 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `bahrain-telecommunications-beyon` | 2024 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `bahrain-telecommunications-beyon` | 2024 | scored | 69 | 41908 | 0.00 | 0 | — | 233 | 44 | 91 | 4 | 4.725 |  |
| `bahrain-telecommunications-beyon` | 2024 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `bahrain-telecommunications-beyon` | 2025 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `bahrain-telecommunications-beyon` | 2025 | scored | 66 | 42583 | 0.00 | 0 | — | 208 | 42 | 89 | 5 | 4.905 |  |
| `bahrain-telecommunications-beyon` | 2025 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `baladna` | 2020 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `baladna` | 2020 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `baladna` | 2020 | scored | 146 | 42523 | 0.04 | 2 | — | 130 | 98 | 159 | 13 | 6.323 |  |
| `baladna` | 2021 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `baladna` | 2021 | scored | 158 | 47501 | 0.04 | 0 | — | 141 | 108 | 180 | 11 | 6.924 |  |
| `baladna` | 2021 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `baladna` | 2022 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `baladna` | 2022 | scored | 176 | 49131 | 0.01 | 0 | — | 171 | 124 | 205 | 14 | 7.259 |  |
| `baladna` | 2022 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `baladna` | 2023 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `baladna` | 2023 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `baladna` | 2023 | scored | 96 | 59814 | 0.01 | 0 | — | 413 | 70 | 297 | 16 | 8.084 |  |
| `baladna` | 2024 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `baladna` | 2024 | scored | 103 | 61706 | 0.01 | 0 | — | 556 | 76 | 277 | 19 | 7.337 |  |
| `baladna` | 2024 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `baladna` | 2025 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `baladna` | 2025 | scored | 117 | 71770 | 0.01 | 0 | — | 205 | 88 | 342 | 20 | 7.491 |  |
| `baladna` | 2025 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `bank-albilad` | 2020 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `bank-albilad` | 2020 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `bank-albilad` | 2020 | scored | 182 | 54542 | 0.01 | 1 | — | 348 | 97 | 108 | 7 | 4.940 |  |
| `bank-albilad` | 2021 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `bank-albilad` | 2021 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `bank-albilad` | 2021 | scored | 116 | 32127 | 0.00 | 0 | — | 290 | 102 | 105 | 2 | 4.158 |  |
| `bank-albilad` | 2022 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `bank-albilad` | 2022 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `bank-albilad` | 2022 | scored | 69 | 30707 | 0.01 | 0 | — | 212 | 59 | 98 | 1 | 3.780 |  |
| `bank-albilad` | 2023 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `bank-albilad` | 2023 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `bank-albilad` | 2023 | scored | 155 | 58183 | 0.00 | 0 | — | 176 | 83 | 145 | 7 | 4.502 |  |
| `bank-albilad` | 2024 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `bank-albilad` | 2024 | scored | 132 | 37497 | 0.01 | 0 | — | 316 | 40 | 40 | 1 | 5.670 |  |
| `bank-albilad` | 2024 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `bank-albilad` | 2025 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `bank-albilad` | 2025 | scored | 205 | 64374 | 0.00 | 0 | — | 352 | 144 | 223 | 6 | 5.730 |  |
| `bank-albilad` | 2025 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `bank-dhofar` | 2020 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `bank-dhofar` | 2020 | scored | 414 | 99368 | 0.02 | 0 | — | 1649 | 133 | 56 | 5 | 1.168 |  |
| `bank-dhofar` | 2020 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `bank-dhofar` | 2021 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `bank-dhofar` | 2021 | scored | 398 | 103260 | 0.02 | 0 | — | 1823 | 130 | 54 | 2 | 2.002 |  |
| `bank-dhofar` | 2021 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `bank-dhofar` | 2022 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `bank-dhofar` | 2022 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `bank-dhofar` | 2022 | scored | 209 | 101782 | 0.00 | 0 | — | 1915 | 68 | 54 | 3 | 1.211 |  |
| `bank-dhofar` | 2023 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `bank-dhofar` | 2023 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `bank-dhofar` | 2023 | scored | 388 | 94760 | 0.01 | 0 | — | 1755 | 126 | 66 | 2 | 2.844 |  |
| `bank-dhofar` | 2024 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `bank-dhofar` | 2024 | scored | 176 | 99828 | 0.00 | 0 | — | 616 | 65 | 82 | 3 | 2.208 |  |
| `bank-dhofar` | 2024 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `bank-dhofar` | 2025 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `bank-dhofar` | 2025 | scored | 381 | 97009 | 0.01 | 2 | — | 510 | 132 | 127 | 5 | 4.235 |  |
| `bank-dhofar` | 2025 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `bank-muscat-bkmb` | 2020 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `bank-muscat-bkmb` | 2020 | scored | 162 | 100722 | 0.01 | 0 | — | 1342 | 75 | 216 | 6 | 3.643 |  |
| `bank-muscat-bkmb` | 2020 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `bank-muscat-bkmb` | 2021 | scored | 254 | 94879 | 0.00 | 0 | — | 957 | 129 | 193 | 1 | 2.904 |  |
| `bank-muscat-bkmb` | 2021 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `bank-muscat-bkmb` | 2021 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `bank-muscat-bkmb` | 2022 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `bank-muscat-bkmb` | 2022 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `bank-muscat-bkmb` | 2022 | scored | 261 | 94170 | 0.01 | 0 | 5 | 946 | 137 | 176 | 3 | 2.990 |  |
| `bank-muscat-bkmb` | 2023 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `bank-muscat-bkmb` | 2023 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `bank-muscat-bkmb` | 2023 | scored | 278 | 100208 | 0.03 | 0 | — | 686 | 143 | 198 | 5 | 2.981 |  |
| `bank-muscat-bkmb` | 2024 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `bank-muscat-bkmb` | 2024 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `bank-muscat-bkmb` | 2024 | scored | 283 | 94753 | 0.01 | 0 | — | 960 | 158 | 207 | 5 | 3.591 |  |
| `bank-muscat-bkmb` | 2025 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `bank-muscat-bkmb` | 2025 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `bank-muscat-bkmb` | 2025 | scored | 286 | 95131 | 0.01 | 0 | — | 939 | 163 | 219 | 4 | 3.497 |  |
| `barwa-real-estate` | 2020 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `barwa-real-estate` | 2020 | scored | 90 | 57984 | 0.02 | 0 | — | 466 | 49 | 128 | 24 | 3.797 |  |
| `barwa-real-estate` | 2020 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `barwa-real-estate` | 2021 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `barwa-real-estate` | 2021 | scored | 89 | 57590 | 0.01 | 0 | — | 621 | 49 | 136 | 23 | 4.149 |  |
| `barwa-real-estate` | 2021 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `barwa-real-estate` | 2022 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `barwa-real-estate` | 2022 | scored | 87 | 55454 | 0.01 | 0 | — | 441 | 48 | 132 | 22 | 3.900 |  |
| `barwa-real-estate` | 2022 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `barwa-real-estate` | 2023 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `barwa-real-estate` | 2023 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `barwa-real-estate` | 2023 | scored | 88 | 54262 | 0.02 | 0 | — | 400 | 51 | 125 | 18 | 3.634 |  |
| `barwa-real-estate` | 2024 | scored | 179 | 55653 | 0.02 | 2 | — | 346 | 101 | 138 | 22 | 4.184 |  |
| `barwa-real-estate` | 2024 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `barwa-real-estate` | 2024 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `barwa-real-estate` | 2025 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `barwa-real-estate` | 2025 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `barwa-real-estate` | 2025 | scored | 129 | 56592 | 0.00 | 0 | — | 946 | 76 | 141 | 18 | 4.338 |  |
| `boubyan-bank` | 2020 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `boubyan-bank` | 2020 | scored | 126 | 44758 | 0.02 | 0 | — | 317 | 73 | 79 | 2 | 2.784 |  |
| `boubyan-bank` | 2020 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `boubyan-bank` | 2021 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `boubyan-bank` | 2021 | scored | 123 | 45547 | 0.02 | 0 | — | 310 | 73 | 115 | 2 | 3.316 |  |
| `boubyan-bank` | 2021 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `boubyan-bank` | 2022 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `boubyan-bank` | 2022 | scored | 129 | 50739 | 0.01 | 0 | — | 325 | 75 | 159 | 3 | 4.742 |  |
| `boubyan-bank` | 2022 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `boubyan-bank` | 2022 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `boubyan-bank` | 2023 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `boubyan-bank` | 2023 | scored | 137 | 52557 | 0.01 | 0 | — | 336 | 83 | 207 | 6 | 5.223 |  |
| `boubyan-bank` | 2023 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `boubyan-bank` | 2024 | scored | 133 | 51559 | 0.02 | 0 | — | 337 | 81 | 171 | 4 | 3.419 |  |
| `boubyan-bank` | 2024 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `boubyan-bank` | 2024 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `boubyan-bank` | 2025 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `boubyan-bank` | 2025 | scored | 65 | 50956 | 0.02 | 0 | — | 353 | 39 | 145 | 5 | 4.682 |  |
| `boubyan-bank` | 2025 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `dar-al-arkan-real-estate-development-company` | 2020 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `dar-al-arkan-real-estate-development-company` | 2020 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `dar-al-arkan-real-estate-development-company` | 2020 | scored | 70 | 34951 | 0.00 | 0 | — | 398 | 42 | 66 | 8 | 3.308 |  |
| `dar-al-arkan-real-estate-development-company` | 2021 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `dar-al-arkan-real-estate-development-company` | 2021 | scored | 78 | 35756 | 0.01 | 0 | — | 281 | 47 | 87 | 11 | 5.275 |  |
| `dar-al-arkan-real-estate-development-company` | 2021 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `dar-al-arkan-real-estate-development-company` | 2021 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `dar-al-arkan-real-estate-development-company` | 2022 | scored | 93 | 40865 | 0.01 | 0 | — | 261 | 60 | 138 | 12 | 7.775 |  |
| `dar-al-arkan-real-estate-development-company` | 2022 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `dar-al-arkan-real-estate-development-company` | 2022 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `dar-al-arkan-real-estate-development-company` | 2022 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `dar-al-arkan-real-estate-development-company` | 2023 | scored | 97 | 41668 | 0.02 | 0 | — | 192 | 70 | 166 | 10 | 8.316 |  |
| `dar-al-arkan-real-estate-development-company` | 2023 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `dar-al-arkan-real-estate-development-company` | 2023 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `dar-al-arkan-real-estate-development-company` | 2024 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `dar-al-arkan-real-estate-development-company` | 2024 | scored | 127 | 44878 | 0.02 | 0 | — | 124 | 88 | 165 | 13 | 7.328 |  |
| `dar-al-arkan-real-estate-development-company` | 2024 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `dar-al-arkan-real-estate-development-company` | 2024 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `dar-al-arkan-real-estate-development-company` | 2025 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `dar-al-arkan-real-estate-development-company` | 2025 | scored | 172 | 53367 | 0.01 | 0 | — | 169 | 124 | 291 | 13 | 8.204 |  |
| `dar-al-arkan-real-estate-development-company` | 2025 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `dubai-investment` | 2020 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `dubai-investment` | 2020 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `dubai-investment` | 2020 | scored | 100 | 30397 | 0.11 | 0 | 1 | 466 | 52 | 25 | 0 | 1.641 |  |
| `dubai-investment` | 2021 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `dubai-investment` | 2021 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `dubai-investment` | 2021 | scored | 120 | 41530 | 0.02 | 0 | — | 166 | 33 | 37 | 0 | 3.265 |  |
| `dubai-investment` | 2021 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `dubai-investment` | 2022 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `dubai-investment` | 2022 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `dubai-investment` | 2022 | scored | 130 | 42108 | 0.22 | 0 | — | 180 | 34 | 37 | 0 | 3.256 |  |
| `dubai-investment` | 2023 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `dubai-investment` | 2023 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `dubai-investment` | 2023 | scored | 158 | 49898 | 0.01 | 0 | — | 302 | 52 | 36 | 0 | 2.208 |  |
| `dubai-investment` | 2024 | scored | 92 | 47647 | 0.01 | 0 | — | 312 | 28 | 29 | 0 | 1.735 |  |
| `dubai-investment` | 2024 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `dubai-investment` | 2024 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `dubai-investment` | 2025 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `dubai-investment` | 2025 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `dubai-investment` | 2025 | scored | 92 | 48962 | 0.01 | 0 | — | 637 | 27 | 32 | 0 | 1.899 |  |
| `dubai-islamic-bank` | 2020 | scored | 114 | 37208 | 0.04 | 0 | — | 770 | 43 | 23 | 0 | 2.457 |  |
| `dubai-islamic-bank` | 2020 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `dubai-islamic-bank` | 2020 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `dubai-islamic-bank` | 2021 | scored | 207 | 59997 | 0.48 | 1 | — | 380 | 59 | 27 | 0 | 1.701 | threshold |
| `dubai-islamic-bank` | 2021 | uploaded | 207 | 0 | 0.48 | 0 | — | 0 | — | 0 | — | — | threshold |
| `dubai-islamic-bank` | 2021 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `dubai-islamic-bank` | 2021 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `dubai-islamic-bank` | 2022 | scored | 209 | 67232 | 0.02 | 0 | — | 384 | 59 | 32 | 2 | 1.856 |  |
| `dubai-islamic-bank` | 2022 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `dubai-islamic-bank` | 2022 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `dubai-islamic-bank` | 2023 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `dubai-islamic-bank` | 2023 | scored | 236 | 75850 | 0.05 | 1 | — | 268 | 61 | 26 | 0 | 0.919 |  |
| `dubai-islamic-bank` | 2023 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `dubai-islamic-bank` | 2024 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `dubai-islamic-bank` | 2024 | scored | 186 | 78890 | 0.00 | 0 | — | 1373 | 115 | 404 | 14 | 7.010 |  |
| `dubai-islamic-bank` | 2024 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `dubai-islamic-bank` | 2025 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `dubai-islamic-bank` | 2025 | scored | 205 | 80206 | 0.00 | 0 | — | 1092 | 140 | 447 | 4 | 6.503 |  |
| `dubai-islamic-bank` | 2025 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `emaar-properties` | 2020 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `emaar-properties` | 2020 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `emaar-properties` | 2020 | scored | 116 | 16751 | 0.04 | 0 | — | 212 | — | 6 | 2 | 0.911 |  |
| `emaar-properties` | 2021 | scored | 117 | 71389 | 0.00 | 0 | — | 271 | 74 | 198 | 4 | 6.031 |  |
| `emaar-properties` | 2021 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `emaar-properties` | 2021 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `emaar-properties` | 2022 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `emaar-properties` | 2022 | scored | 110 | 65967 | 0.01 | 0 | — | 1783 | 72 | 191 | 3 | 6.710 |  |
| `emaar-properties` | 2022 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `emaar-properties` | 2023 | scored | 117 | 70828 | 0.02 | 0 | — | 216 | 81 | 292 | 6 | 6.847 |  |
| `emaar-properties` | 2023 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `emaar-properties` | 2023 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `emaar-properties` | 2024 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `emaar-properties` | 2024 | scored | 197 | 75154 | 0.00 | 0 | — | 1906 | 137 | 596 | 4 | 8.050 |  |
| `emaar-properties` | 2024 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `emaar-properties` | 2025 | scored | 223 | 86175 | 0.00 | 0 | — | 2705 | 159 | 701 | 4 | 8.626 |  |
| `emaar-properties` | 2025 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `emaar-properties` | 2025 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `emirates-nbd-pjsc` | 2020 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `emirates-nbd-pjsc` | 2020 | scored | 30 | 16217 | 0.03 | 0 | — | 55 | — | 40 | 2 | 3.926 |  |
| `emirates-nbd-pjsc` | 2020 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `emirates-nbd-pjsc` | 2021 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `emirates-nbd-pjsc` | 2021 | scored | 33 | 17005 | 0.00 | 0 | — | 133 | — | 49 | 2 | 3.926 |  |
| `emirates-nbd-pjsc` | 2021 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `emirates-nbd-pjsc` | 2022 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `emirates-nbd-pjsc` | 2022 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `emirates-nbd-pjsc` | 2022 | scored | 34 | 16270 | 0.00 | 0 | — | 99 | — | 51 | 2 | 3.471 |  |
| `emirates-nbd-pjsc` | 2023 | scored | 109 | 77713 | 0.01 | 0 | — | 281 | 71 | 332 | 19 | 6.271 |  |
| `emirates-nbd-pjsc` | 2023 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `emirates-nbd-pjsc` | 2023 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `emirates-nbd-pjsc` | 2024 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `emirates-nbd-pjsc` | 2024 | scored | 121 | 85833 | 0.00 | 0 | — | 277 | 84 | 464 | 13 | 7.165 |  |
| `emirates-nbd-pjsc` | 2024 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `emirates-nbd-pjsc` | 2025 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `emirates-nbd-pjsc` | 2025 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `emirates-nbd-pjsc` | 2025 | scored | 132 | 89271 | 0.00 | 0 | — | 256 | 92 | 592 | 26 | 7.560 |  |
| `emirates-telecom-etisalat-group` | 2020 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `emirates-telecom-etisalat-group` | 2020 | scored | 96 | 70562 | 0.00 | 0 | — | 285 | 54 | 74 | 0 | 3.557 |  |
| `emirates-telecom-etisalat-group` | 2020 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `emirates-telecom-etisalat-group` | 2021 | scored | 101 | 67953 | 0.00 | 0 | — | 367 | 57 | 88 | 0 | 3.273 |  |
| `emirates-telecom-etisalat-group` | 2021 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `emirates-telecom-etisalat-group` | 2021 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `emirates-telecom-etisalat-group` | 2022 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `emirates-telecom-etisalat-group` | 2022 | scored | 81 | 58522 | 0.00 | 0 | — | 494 | 44 | 135 | 1 | 5.318 |  |
| `emirates-telecom-etisalat-group` | 2022 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `emirates-telecom-etisalat-group` | 2023 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `emirates-telecom-etisalat-group` | 2023 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `emirates-telecom-etisalat-group` | 2023 | scored | 144 | 96389 | 0.01 | 0 | — | 279 | 105 | 604 | 3 | 8.333 |  |
| `emirates-telecom-etisalat-group` | 2024 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `emirates-telecom-etisalat-group` | 2024 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `emirates-telecom-etisalat-group` | 2024 | scored | 220 | 113245 | 0.00 | 0 | — | 1533 | 167 | 832 | 7 | 9.235 |  |
| `emirates-telecom-etisalat-group` | 2025 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `emirates-telecom-etisalat-group` | 2025 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `emirates-telecom-etisalat-group` | 2025 | scored | 229 | 109411 | 0.00 | 0 | — | 1131 | 176 | 761 | 13 | 8.548 |  |
| `etihad-etisalat-mobily` | 2020 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `etihad-etisalat-mobily` | 2020 | scored | 154 | 48984 | 0.03 | 0 | — | 73 | 105 | 94 | 3 | 4.064 |  |
| `etihad-etisalat-mobily` | 2020 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `etihad-etisalat-mobily` | 2021 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `etihad-etisalat-mobily` | 2021 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `etihad-etisalat-mobily` | 2021 | scored | 190 | 60069 | 0.02 | 0 | — | 89 | 137 | 204 | 7 | 5.120 |  |
| `etihad-etisalat-mobily` | 2022 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `etihad-etisalat-mobily` | 2022 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `etihad-etisalat-mobily` | 2022 | scored | 99 | 61379 | 0.00 | 0 | — | 188 | 72 | 204 | 8 | 6.091 |  |
| `etihad-etisalat-mobily` | 2023 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `etihad-etisalat-mobily` | 2023 | scored | 107 | 77791 | 0.00 | 0 | — | 206 | 68 | 218 | 6 | 5.696 |  |
| `etihad-etisalat-mobily` | 2023 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `etihad-etisalat-mobily` | 2024 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `etihad-etisalat-mobily` | 2024 | scored | 122 | 79036 | 0.00 | 0 | — | 226 | 84 | 294 | 8 | 6.521 |  |
| `etihad-etisalat-mobily` | 2024 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `etihad-etisalat-mobily` | 2025 | scored | 144 | 82560 | 0.00 | 0 | — | 194 | 107 | 358 | 4 | 7.560 |  |
| `etihad-etisalat-mobily` | 2025 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `etihad-etisalat-mobily` | 2025 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `first-abu-dhabi-bank` | 2020 | scored | 204 | 70734 | 0.01 | 0 | — | 114 | 53 | 120 | 12 | 5.619 |  |
| `first-abu-dhabi-bank` | 2020 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `first-abu-dhabi-bank` | 2020 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `first-abu-dhabi-bank` | 2021 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `first-abu-dhabi-bank` | 2021 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `first-abu-dhabi-bank` | 2021 | scored | 74 | 38528 | 0.01 | 0 | — | 64 | — | 287 | 14 | 5.713 |  |
| `first-abu-dhabi-bank` | 2022 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `first-abu-dhabi-bank` | 2022 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `first-abu-dhabi-bank` | 2022 | scored | 83 | 45295 | 0.01 | 0 | — | 81 | — | 357 | 20 | 6.211 |  |
| `first-abu-dhabi-bank` | 2023 | scored | 134 | 79002 | 0.01 | 0 | — | 1539 | 59 | 313 | 5 | 6.959 |  |
| `first-abu-dhabi-bank` | 2023 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `first-abu-dhabi-bank` | 2023 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `first-abu-dhabi-bank` | 2024 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `first-abu-dhabi-bank` | 2024 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `first-abu-dhabi-bank` | 2024 | scored | 181 | 97344 | 0.01 | 0 | — | 347 | 107 | 550 | 10 | 8.024 |  |
| `first-abu-dhabi-bank` | 2025 | scored | 191 | 105731 | 0.00 | 0 | — | 461 | 119 | 746 | 17 | 8.729 |  |
| `first-abu-dhabi-bank` | 2025 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `first-abu-dhabi-bank` | 2025 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `gulf-hotels-group` | 2020 | scored | 75 | 17436 | 0.01 | 0 | 4 | 143 | 28 | 0 | 0 | 0.498 |  |
| `gulf-hotels-group` | 2020 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `gulf-hotels-group` | 2020 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `gulf-hotels-group` | 2021 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `gulf-hotels-group` | 2021 | scored | 84 | 19606 | 0.01 | 1 | — | 150 | 34 | 1 | 0 | 1.632 |  |
| `gulf-hotels-group` | 2021 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `gulf-hotels-group` | 2022 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `gulf-hotels-group` | 2022 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `gulf-hotels-group` | 2022 | scored | 92 | 19211 | 0.00 | 1 | — | 314 | 44 | 1 | 0 | 1.589 |  |
| `gulf-hotels-group` | 2023 | scored | 102 | 26920 | 0.01 | 2 | — | 283 | 40 | 3 | 0 | 1.443 |  |
| `gulf-hotels-group` | 2023 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `gulf-hotels-group` | 2023 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `gulf-hotels-group` | 2024 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `gulf-hotels-group` | 2024 | scored | 153 | 34579 | 0.00 | 0 | — | 548 | 96 | 87 | 6 | 6.521 |  |
| `gulf-hotels-group` | 2024 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `gulf-hotels-group` | 2025 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `gulf-hotels-group` | 2025 | scored | 69 | 37036 | 0.00 | 0 | — | 217 | 43 | 94 | 5 | 6.521 |  |
| `gulf-hotels-group` | 2025 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `gulf-international-services` | 2020 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `gulf-international-services` | 2020 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `gulf-international-services` | 2020 | scored | 85 | 27143 | 0.05 | 0 | 5 | 0 | 35 | 3 | 0 | 1.761 |  |
| `gulf-international-services` | 2021 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `gulf-international-services` | 2021 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `gulf-international-services` | 2021 | scored | 80 | 26328 | 0.00 | 0 | — | 78 | 30 | 4 | 0 | 2.079 |  |
| `gulf-international-services` | 2022 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `gulf-international-services` | 2022 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `gulf-international-services` | 2022 | scored | 105 | 29905 | 0.02 | 1 | — | 140 | 67 | 64 | 5 | 5.069 |  |
| `gulf-international-services` | 2023 | scored | 82 | 31748 | 0.01 | 0 | — | 40 | 33 | 3 | 0 | 1.890 |  |
| `gulf-international-services` | 2023 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `gulf-international-services` | 2023 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `gulf-international-services` | 2024 | scored | 98 | 31976 | 0.04 | 0 | — | 40 | 36 | 8 | 0 | 3.308 |  |
| `gulf-international-services` | 2024 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `gulf-international-services` | 2024 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `gulf-international-services` | 2025 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `gulf-international-services` | 2025 | scored | 99 | 34794 | 0.02 | 0 | — | 129 | 34 | 19 | 0 | 4.347 |  |
| `gulf-international-services` | 2025 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `industries-qatar` | 2020 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `industries-qatar` | 2020 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `industries-qatar` | 2020 | scored | 92 | 27923 | 0.01 | 0 | 5 | 91 | 37 | 3 | 0 | 1.976 |  |
| `industries-qatar` | 2021 | scored | 84 | 27005 | 0.00 | 0 | 5 | 250 | 46 | 54 | 4 | 5.782 |  |
| `industries-qatar` | 2021 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `industries-qatar` | 2021 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `industries-qatar` | 2022 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `industries-qatar` | 2022 | scored | 86 | 29917 | 0.00 | 0 | — | 255 | 43 | 58 | 6 | 4.820 |  |
| `industries-qatar` | 2022 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `industries-qatar` | 2023 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `industries-qatar` | 2023 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `industries-qatar` | 2023 | scored | 80 | 30251 | 0.01 | 0 | — | 39 | 35 | 10 | 0 | 4.081 |  |
| `industries-qatar` | 2024 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `industries-qatar` | 2024 | scored | 102 | 32830 | 0.06 | 0 | — | 45 | 44 | 16 | 0 | 5.284 |  |
| `industries-qatar` | 2024 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `industries-qatar` | 2025 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `industries-qatar` | 2025 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `industries-qatar` | 2025 | scored | 112 | 33826 | 0.04 | 2 | — | 46 | 42 | 21 | 0 | 4.476 |  |
| `jarir-marketing-co` | 2020 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `jarir-marketing-co` | 2020 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `jarir-marketing-co` | 2020 | scored | 44 | 20755 | 0.05 | 0 | 5,9 | 157 | — | 116 | 3 | 6.237 |  |
| `jarir-marketing-co` | 2021 | scored | 44 | 19715 | 0.09 | 0 | — | 130 | — | 154 | 2 | 7.457 |  |
| `jarir-marketing-co` | 2021 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `jarir-marketing-co` | 2021 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `jarir-marketing-co` | 2022 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `jarir-marketing-co` | 2022 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `jarir-marketing-co` | 2022 | scored | 44 | 20159 | 0.09 | 0 | — | 127 | — | 156 | 1 | 7.371 |  |
| `jarir-marketing-co` | 2023 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `jarir-marketing-co` | 2023 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `jarir-marketing-co` | 2023 | scored | 41 | 19049 | 0.10 | 0 | — | 114 | — | 97 | 1 | 6.065 |  |
| `jarir-marketing-co` | 2024 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `jarir-marketing-co` | 2024 | scored | 41 | 17241 | 0.07 | 0 | — | 119 | — | 93 | 1 | 5.421 |  |
| `jarir-marketing-co` | 2024 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `jarir-marketing-co` | 2025 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `jarir-marketing-co` | 2025 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `jarir-marketing-co` | 2025 | scored | 43 | 17157 | 0.05 | 0 | — | 129 | — | 89 | 1 | 5.361 |  |
| `jazeera-airways` | 2020 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `jazeera-airways` | 2020 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `jazeera-airways` | 2020 | scored | 41 | 34010 | 0.00 | 0 | — | 66 | 23 | 78 | 11 | 3.797 |  |
| `jazeera-airways` | 2021 | scored | 40 | 30855 | 0.00 | 0 | — | 62 | 23 | 68 | 9 | 5.026 |  |
| `jazeera-airways` | 2021 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `jazeera-airways` | 2021 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `jazeera-airways` | 2022 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `jazeera-airways` | 2022 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `jazeera-airways` | 2022 | scored | 38 | 26321 | 0.00 | 1 | — | 58 | 21 | 53 | 5 | 3.591 |  |
| `jazeera-airways` | 2023 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `jazeera-airways` | 2023 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `jazeera-airways` | 2023 | scored | 93 | 29348 | 0.02 | 0 | — | 66 | 55 | 84 | 3 | 6.512 |  |
| `jazeera-airways` | 2024 | scored | 76 | 25277 | 0.03 | 0 | — | 67 | 36 | 46 | 4 | 3.832 |  |
| `jazeera-airways` | 2024 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `jazeera-airways` | 2024 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `jazeera-airways` | 2025 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `jazeera-airways` | 2025 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `jazeera-airways` | 2025 | scored | 79 | 24878 | 0.01 | 0 | — | 60 | 42 | 46 | 3 | 3.471 |  |
| `jazeera-steel` | 2020 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `jazeera-steel` | 2020 | scored | 61 | 18971 | 0.02 | 0 | — | 876 | 27 | 12 | 1 | 2.551 |  |
| `jazeera-steel` | 2020 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `jazeera-steel` | 2021 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `jazeera-steel` | 2021 | scored | 60 | 18906 | 0.02 | 0 | — | 831 | 26 | 15 | 1 | 3.986 |  |
| `jazeera-steel` | 2021 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `jazeera-steel` | 2022 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `jazeera-steel` | 2022 | scored | 62 | 18982 | 0.03 | 0 | — | 845 | 28 | 14 | 2 | 3.789 |  |
| `jazeera-steel` | 2022 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `jazeera-steel` | 2023 | scored | 78 | 26438 | 0.00 | 0 | — | 1149 | 22 | 17 | 2 | 4.218 |  |
| `jazeera-steel` | 2023 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `jazeera-steel` | 2023 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `jazeera-steel` | 2024 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `jazeera-steel` | 2024 | scored | 81 | 26348 | 0.02 | 0 | — | 313 | 23 | 18 | 2 | 3.153 |  |
| `jazeera-steel` | 2024 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `jazeera-steel` | 2025 | scored | 84 | 28432 | 0.04 | 0 | — | 1249 | 24 | 20 | 2 | 4.794 |  |
| `jazeera-steel` | 2025 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `jazeera-steel` | 2025 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `kuwait-finance-house` | 2020 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `kuwait-finance-house` | 2020 | scored | 181 | 64538 | 0.02 | 0 | — | 599 | 111 | 156 | 9 | 3.677 |  |
| `kuwait-finance-house` | 2020 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `kuwait-finance-house` | 2021 | scored | 98 | 61363 | 0.05 | 1 | — | 606 | 65 | 164 | 10 | 4.192 |  |
| `kuwait-finance-house` | 2021 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `kuwait-finance-house` | 2021 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `kuwait-finance-house` | 2022 | scored | 102 | 68340 | 0.02 | 1 | — | 932 | 68 | 191 | 6 | 4.407 |  |
| `kuwait-finance-house` | 2022 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `kuwait-finance-house` | 2022 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `kuwait-finance-house` | 2023 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `kuwait-finance-house` | 2023 | scored | 113 | 41338 | 0.04 | 1 | — | 783 | 94 | 169 | 6 | 3.961 |  |
| `kuwait-finance-house` | 2023 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `kuwait-finance-house` | 2024 | scored | 115 | 66170 | 0.03 | 1 | — | 100 | 82 | 210 | 6 | 4.734 |  |
| `kuwait-finance-house` | 2024 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `kuwait-finance-house` | 2024 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `kuwait-finance-house` | 2025 | scored | 120 | 74289 | 0.02 | 0 | — | 114 | 79 | 202 | 3 | 4.158 |  |
| `kuwait-finance-house` | 2025 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `kuwait-finance-house` | 2025 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `kuwait-telecommunications-company` | 2020 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `kuwait-telecommunications-company` | 2020 | uploaded | 130 | 0 | 0.42 | 0 | — | 0 | — | 0 | — | — | threshold |
| `kuwait-telecommunications-company` | 2020 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `kuwait-telecommunications-company` | 2020 | scored | 130 | 38472 | 0.42 | 0 | — | 0 | 72 | 35 | 7 | 1.538 | threshold |
| `kuwait-telecommunications-company` | 2021 | scored | 80 | 42933 | 0.05 | 1 | — | 47 | 51 | 63 | 3 | 3.385 |  |
| `kuwait-telecommunications-company` | 2021 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `kuwait-telecommunications-company` | 2021 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `kuwait-telecommunications-company` | 2022 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `kuwait-telecommunications-company` | 2022 | scored | 88 | 43127 | 0.05 | 0 | — | 159 | 66 | 147 | 10 | 3.574 |  |
| `kuwait-telecommunications-company` | 2022 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `kuwait-telecommunications-company` | 2023 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `kuwait-telecommunications-company` | 2023 | scored | 99 | 51086 | 0.00 | 0 | — | 187 | 66 | 155 | 9 | 3.565 |  |
| `kuwait-telecommunications-company` | 2023 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `kuwait-telecommunications-company` | 2024 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `kuwait-telecommunications-company` | 2024 | scored | 93 | 50951 | 0.00 | 0 | — | 163 | 67 | 290 | 12 | 7.440 |  |
| `kuwait-telecommunications-company` | 2024 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `kuwait-telecommunications-company` | 2025 | scored | 97 | 52150 | 0.00 | 0 | — | 231 | 69 | 245 | 14 | 5.679 |  |
| `kuwait-telecommunications-company` | 2025 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `kuwait-telecommunications-company` | 2025 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `maaden` | 2020 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `maaden` | 2020 | scored | 169 | 67423 | 0.01 | 0 | — | 1466 | 64 | 69 | 1 | 5.309 |  |
| `maaden` | 2020 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `maaden` | 2021 | scored | 154 | 65028 | 0.01 | 0 | — | 1267 | 57 | 63 | 0 | 5.284 |  |
| `maaden` | 2021 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `maaden` | 2021 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `maaden` | 2022 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `maaden` | 2022 | scored | 73 | 19975 | 0.04 | 0 | — | 166 | 71 | 97 | 2 | 6.581 |  |
| `maaden` | 2022 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `maaden` | 2023 | scored | 161 | 82358 | 0.02 | 0 | — | 1570 | 57 | 132 | 2 | 6.306 |  |
| `maaden` | 2023 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `maaden` | 2023 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `maaden` | 2024 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `maaden` | 2024 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `maaden` | 2024 | scored | 156 | 83134 | 0.01 | 0 | — | 1649 | 64 | 213 | 2 | 7.337 |  |
| `maaden` | 2025 | scored | 216 | 89510 | 0.01 | 0 | — | 2209 | 112 | 289 | 0 | 8.239 |  |
| `maaden` | 2025 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `maaden` | 2025 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `mobile-telecommunications-co-saudi-arabia-zain` | 2020 | scored | 59 | 42854 | 0.00 | 0 | — | 350 | 30 | 65 | 2 | 3.222 |  |
| `mobile-telecommunications-co-saudi-arabia-zain` | 2020 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `mobile-telecommunications-co-saudi-arabia-zain` | 2020 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `mobile-telecommunications-co-saudi-arabia-zain` | 2021 | scored | 117 | 41374 | 0.03 | 0 | — | 300 | 63 | 57 | 2 | 3.694 |  |
| `mobile-telecommunications-co-saudi-arabia-zain` | 2021 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `mobile-telecommunications-co-saudi-arabia-zain` | 2021 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `mobile-telecommunications-co-saudi-arabia-zain` | 2022 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `mobile-telecommunications-co-saudi-arabia-zain` | 2022 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `mobile-telecommunications-co-saudi-arabia-zain` | 2022 | scored | 138 | 42614 | 0.00 | 0 | — | 453 | 74 | 80 | 3 | 5.051 |  |
| `mobile-telecommunications-co-saudi-arabia-zain` | 2023 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `mobile-telecommunications-co-saudi-arabia-zain` | 2023 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `mobile-telecommunications-co-saudi-arabia-zain` | 2023 | scored | 57 | 27608 | 0.02 | 0 | — | 110 | — | 143 | 3 | 6.246 |  |
| `mobile-telecommunications-co-saudi-arabia-zain` | 2024 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `mobile-telecommunications-co-saudi-arabia-zain` | 2024 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `mobile-telecommunications-co-saudi-arabia-zain` | 2024 | scored | 90 | 60013 | 0.00 | 0 | — | 270 | 58 | 213 | 5 | 6.864 |  |
| `mobile-telecommunications-co-saudi-arabia-zain` | 2025 | scored | 104 | 65577 | 0.00 | 0 | — | 196 | 73 | 249 | 7 | 8.204 |  |
| `mobile-telecommunications-co-saudi-arabia-zain` | 2025 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `mobile-telecommunications-co-saudi-arabia-zain` | 2025 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `mouwasat-medical-services-company` | 2020 | scored | 64 | 13375 | 0.02 | 0 | — | 63 | — | 34 | 3 | 2.638 |  |
| `mouwasat-medical-services-company` | 2020 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `mouwasat-medical-services-company` | 2020 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `mouwasat-medical-services-company` | 2021 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `mouwasat-medical-services-company` | 2021 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `mouwasat-medical-services-company` | 2021 | scored | 42 | 8589 | 0.00 | 0 | — | 39 | — | 31 | 5 | 3.634 |  |
| `mouwasat-medical-services-company` | 2022 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `mouwasat-medical-services-company` | 2022 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `mouwasat-medical-services-company` | 2022 | scored | 52 | 16150 | 0.00 | 0 | — | 40 | — | 71 | 8 | 4.880 |  |
| `mouwasat-medical-services-company` | 2023 | scored | 80 | 45675 | 0.00 | 0 | — | 552 | 50 | 40 | 3 | 2.534 |  |
| `mouwasat-medical-services-company` | 2023 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `mouwasat-medical-services-company` | 2023 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `mouwasat-medical-services-company` | 2024 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `mouwasat-medical-services-company` | 2024 | scored | 109 | 52053 | 0.01 | 1 | — | 309 | 77 | 79 | 0 | 3.986 |  |
| `mouwasat-medical-services-company` | 2024 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `mouwasat-medical-services-company` | 2025 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `mouwasat-medical-services-company` | 2025 | scored | 118 | 49452 | 0.02 | 0 | — | 51 | 57 | 38 | 0 | 4.682 |  |
| `mouwasat-medical-services-company` | 2025 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `national-bank-of-bahrain` | 2020 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `national-bank-of-bahrain` | 2020 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `national-bank-of-bahrain` | 2020 | scored | 80 | 72482 | 0.00 | 0 | — | 1943 | 50 | 277 | 11 | 6.435 |  |
| `national-bank-of-bahrain` | 2021 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `national-bank-of-bahrain` | 2021 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `national-bank-of-bahrain` | 2021 | scored | 182 | 83575 | 0.00 | 0 | 3 | 913 | 113 | 320 | 15 | 6.649 |  |
| `national-bank-of-bahrain` | 2022 | scored | 108 | 88492 | 0.00 | 0 | — | 642 | 71 | 549 | 16 | 6.744 |  |
| `national-bank-of-bahrain` | 2022 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `national-bank-of-bahrain` | 2022 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `national-bank-of-bahrain` | 2023 | scored | 110 | 83629 | 0.00 | 0 | — | 439 | 73 | 516 | 14 | 6.856 |  |
| `national-bank-of-bahrain` | 2023 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `national-bank-of-bahrain` | 2023 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `national-bank-of-bahrain` | 2023 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `national-bank-of-bahrain` | 2024 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `national-bank-of-bahrain` | 2024 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `national-bank-of-bahrain` | 2024 | scored | 100 | 74558 | 0.00 | 0 | — | 389 | 69 | 426 | 15 | 7.844 |  |
| `national-bank-of-bahrain` | 2024 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `national-bank-of-bahrain` | 2025 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `national-bank-of-bahrain` | 2025 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `national-bank-of-bahrain` | 2025 | scored | 103 | 80867 | 0.00 | 0 | — | 1342 | 70 | 451 | 13 | 6.804 |  |
| `national-bank-of-kuwait` | 2020 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `national-bank-of-kuwait` | 2020 | scored | 186 | 63470 | 0.05 | 1 | — | 181 | 76 | 152 | 8 | 5.215 |  |
| `national-bank-of-kuwait` | 2020 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `national-bank-of-kuwait` | 2021 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `national-bank-of-kuwait` | 2021 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `national-bank-of-kuwait` | 2021 | scored | 192 | 65456 | 0.06 | 0 | — | 189 | 82 | 194 | 4 | 5.361 |  |
| `national-bank-of-kuwait` | 2022 | scored | 192 | 68415 | 0.03 | 2 | — | 188 | 82 | 209 | 8 | 5.223 |  |
| `national-bank-of-kuwait` | 2022 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `national-bank-of-kuwait` | 2022 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `national-bank-of-kuwait` | 2023 | scored | 103 | 72019 | 0.00 | 0 | — | 654 | 47 | 257 | 7 | 6.624 |  |
| `national-bank-of-kuwait` | 2023 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `national-bank-of-kuwait` | 2023 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `national-bank-of-kuwait` | 2024 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `national-bank-of-kuwait` | 2024 | scored | 204 | 72517 | 0.05 | 0 | — | 201 | 94 | 288 | 5 | 6.246 |  |
| `national-bank-of-kuwait` | 2024 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `national-bank-of-kuwait` | 2025 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `national-bank-of-kuwait` | 2025 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `national-bank-of-kuwait` | 2025 | scored | 226 | 80612 | 0.05 | 2 | — | 225 | 116 | 432 | 9 | 7.655 |  |
| `national-industrialization-co` | 2020 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `national-industrialization-co` | 2020 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `national-industrialization-co` | 2020 | scored | 79 | 45579 | 0.01 | 0 | — | 853 | 35 | 59 | 1 | 4.837 |  |
| `national-industrialization-co` | 2021 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `national-industrialization-co` | 2021 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `national-industrialization-co` | 2021 | scored | 81 | 42280 | 0.01 | 0 | — | 831 | 41 | 43 | 1 | 3.711 |  |
| `national-industrialization-co` | 2022 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `national-industrialization-co` | 2022 | scored | 87 | 45501 | 0.01 | 0 | — | 875 | 46 | 61 | 0 | 4.021 |  |
| `national-industrialization-co` | 2022 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `national-industrialization-co` | 2023 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `national-industrialization-co` | 2023 | scored | 89 | 47335 | 0.02 | 0 | — | 1023 | 45 | 52 | 0 | 3.969 |  |
| `national-industrialization-co` | 2023 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `national-industrialization-co` | 2024 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `national-industrialization-co` | 2024 | scored | 180 | 50163 | 0.05 | 0 | — | 629 | 91 | 123 | 1 | 6.967 |  |
| `national-industrialization-co` | 2024 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `national-industrialization-co` | 2025 | scored | 93 | 51887 | 0.02 | 0 | — | 825 | 50 | 151 | 1 | 7.294 |  |
| `national-industrialization-co` | 2025 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `national-industrialization-co` | 2025 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `oman-international-development-and-investment-company` | 2020 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `oman-international-development-and-investment-company` | 2020 | scored | 146 | 43073 | 0.00 | 0 | — | 150 | 59 | 44 | 4 | 2.380 |  |
| `oman-international-development-and-investment-company` | 2020 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `oman-international-development-and-investment-company` | 2021 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `oman-international-development-and-investment-company` | 2021 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `oman-international-development-and-investment-company` | 2021 | scored | 134 | 41445 | 0.00 | 0 | — | 208 | 53 | 58 | 5 | 2.981 |  |
| `oman-international-development-and-investment-company` | 2022 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `oman-international-development-and-investment-company` | 2022 | scored | 138 | 45187 | 0.01 | 0 | — | 205 | 60 | 97 | 3 | 2.715 |  |
| `oman-international-development-and-investment-company` | 2022 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `oman-international-development-and-investment-company` | 2023 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `oman-international-development-and-investment-company` | 2023 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `oman-international-development-and-investment-company` | 2023 | scored | 74 | 47523 | 0.00 | 0 | — | 2445 | 32 | 93 | 4 | 3.127 |  |
| `oman-international-development-and-investment-company` | 2024 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `oman-international-development-and-investment-company` | 2024 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `oman-international-development-and-investment-company` | 2024 | scored | 137 | 49111 | 0.00 | 0 | — | 5403 | 62 | 78 | 2 | 3.290 |  |
| `oman-international-development-and-investment-company` | 2025 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `oman-international-development-and-investment-company` | 2025 | scored | 71 | 41557 | 0.00 | 0 | — | 186 | 33 | 119 | 1 | 3.823 |  |
| `oman-international-development-and-investment-company` | 2025 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `oman-telecommunications-company-otel` | 2020 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `oman-telecommunications-company-otel` | 2020 | scored | 154 | 40989 | 0.03 | 1 | — | 148 | 98 | 35 | 1 | 3.179 |  |
| `oman-telecommunications-company-otel` | 2020 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `oman-telecommunications-company-otel` | 2021 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `oman-telecommunications-company-otel` | 2021 | scored | 204 | 41464 | 0.02 | 0 | — | 539 | 83 | 28 | 0 | 3.076 |  |
| `oman-telecommunications-company-otel` | 2021 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `oman-telecommunications-company-otel` | 2022 | scored | 72 | 47098 | 0.06 | 0 | — | 147 | 35 | 46 | 2 | 1.357 |  |
| `oman-telecommunications-company-otel` | 2022 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `oman-telecommunications-company-otel` | 2022 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `oman-telecommunications-company-otel` | 2023 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `oman-telecommunications-company-otel` | 2023 | scored | 71 | 48444 | 0.01 | 0 | — | 259 | 33 | 56 | 4 | 3.522 |  |
| `oman-telecommunications-company-otel` | 2023 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `oman-telecommunications-company-otel` | 2024 | scored | 123 | 57282 | 0.00 | 0 | — | 967 | 68 | 156 | 5 | 7.216 |  |
| `oman-telecommunications-company-otel` | 2024 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `oman-telecommunications-company-otel` | 2024 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `oman-telecommunications-company-otel` | 2025 | scored | 191 | 55362 | 0.01 | 0 | — | 1890 | 90 | 137 | 1 | 7.070 |  |
| `oman-telecommunications-company-otel` | 2025 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `oman-telecommunications-company-otel` | 2025 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `ooredoo-q-p-s-c` | 2020 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `ooredoo-q-p-s-c` | 2020 | scored | 91 | 71847 | 0.00 | 0 | — | 168 | 44 | 158 | 20 | 4.639 |  |
| `ooredoo-q-p-s-c` | 2020 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `ooredoo-q-p-s-c` | 2021 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `ooredoo-q-p-s-c` | 2021 | scored | 90 | 77756 | 0.02 | 0 | — | 150 | 55 | 245 | 19 | 7.491 |  |
| `ooredoo-q-p-s-c` | 2021 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `ooredoo-q-p-s-c` | 2022 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `ooredoo-q-p-s-c` | 2022 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `ooredoo-q-p-s-c` | 2022 | scored | 98 | 79478 | 0.01 | 0 | — | 199 | 60 | 243 | 11 | 7.182 |  |
| `ooredoo-q-p-s-c` | 2023 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `ooredoo-q-p-s-c` | 2023 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `ooredoo-q-p-s-c` | 2023 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `ooredoo-q-p-s-c` | 2023 | scored | 77 | 71748 | 0.03 | 0 | — | 244 | 41 | 172 | 13 | 4.682 |  |
| `ooredoo-q-p-s-c` | 2024 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `ooredoo-q-p-s-c` | 2024 | scored | 78 | 71427 | 0.01 | 0 | — | 640 | 39 | 266 | 16 | 6.005 |  |
| `ooredoo-q-p-s-c` | 2024 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `ooredoo-q-p-s-c` | 2025 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `ooredoo-q-p-s-c` | 2025 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `ooredoo-q-p-s-c` | 2025 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `ooredoo-q-p-s-c` | 2025 | scored | 80 | 73146 | 0.01 | 0 | — | 626 | 40 | 303 | 12 | 6.237 |  |
| `qatar-fuel-company-woqod` | 2020 | scored | 68 | 26515 | 0.00 | 0 | — | 191 | 46 | 69 | 3 | 6.753 |  |
| `qatar-fuel-company-woqod` | 2020 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `qatar-fuel-company-woqod` | 2020 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `qatar-fuel-company-woqod` | 2020 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `qatar-fuel-company-woqod` | 2021 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `qatar-fuel-company-woqod` | 2021 | scored | 77 | 29596 | 0.00 | 0 | — | 282 | 36 | 52 | 5 | 5.275 |  |
| `qatar-fuel-company-woqod` | 2021 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `qatar-fuel-company-woqod` | 2022 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `qatar-fuel-company-woqod` | 2022 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `qatar-fuel-company-woqod` | 2022 | scored | 73 | 29528 | 0.05 | 0 | — | 347 | 37 | 45 | 4 | 5.601 |  |
| `qatar-fuel-company-woqod` | 2022 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `qatar-fuel-company-woqod` | 2023 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `qatar-fuel-company-woqod` | 2023 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `qatar-fuel-company-woqod` | 2023 | scored | 75 | 29510 | 0.01 | 0 | — | 406 | 43 | 71 | 7 | 6.357 |  |
| `qatar-fuel-company-woqod` | 2024 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `qatar-fuel-company-woqod` | 2024 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `qatar-fuel-company-woqod` | 2024 | scored | 75 | 29219 | 0.00 | 0 | — | 630 | 44 | 74 | 7 | 7.071 |  |
| `qatar-fuel-company-woqod` | 2025 | scored | 79 | 33360 | 0.00 | 0 | — | 257 | 49 | 100 | 1 | 6.950 |  |
| `qatar-fuel-company-woqod` | 2025 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `qatar-fuel-company-woqod` | 2025 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `qatar-gas-transport-co-nakilat` | 2020 | scored | 50 | 27220 | 0.02 | 0 | — | 155 | 24 | 33 | 2 | 4.991 |  |
| `qatar-gas-transport-co-nakilat` | 2020 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `qatar-gas-transport-co-nakilat` | 2020 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `qatar-gas-transport-co-nakilat` | 2021 | scored | 41 | 27709 | 0.00 | 0 | — | 182 | 17 | 54 | 4 | 7.938 |  |
| `qatar-gas-transport-co-nakilat` | 2021 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `qatar-gas-transport-co-nakilat` | 2021 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `qatar-gas-transport-co-nakilat` | 2022 | scored | 61 | 47737 | 0.03 | 0 | — | 210 | 37 | 219 | 4 | 6.753 |  |
| `qatar-gas-transport-co-nakilat` | 2022 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `qatar-gas-transport-co-nakilat` | 2022 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `qatar-gas-transport-co-nakilat` | 2023 | scored | 64 | 46758 | 0.00 | 0 | — | 139 | 41 | 213 | 10 | 6.778 |  |
| `qatar-gas-transport-co-nakilat` | 2023 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `qatar-gas-transport-co-nakilat` | 2023 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `qatar-gas-transport-co-nakilat` | 2024 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `qatar-gas-transport-co-nakilat` | 2024 | scored | 65 | 45942 | 0.00 | 0 | — | 104 | 42 | 219 | 7 | 6.830 |  |
| `qatar-gas-transport-co-nakilat` | 2024 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `qatar-gas-transport-co-nakilat` | 2025 | scored | 59 | 47667 | 0.00 | 0 | — | 135 | 39 | 220 | 8 | 6.186 |  |
| `qatar-gas-transport-co-nakilat` | 2025 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `qatar-gas-transport-co-nakilat` | 2025 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `qnb-qatar-national-bank` | 2020 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `qnb-qatar-national-bank` | 2020 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `qnb-qatar-national-bank` | 2020 | scored | 84 | 69434 | 0.00 | 0 | 3 | 1258 | 51 | 384 | 22 | 7.603 |  |
| `qnb-qatar-national-bank` | 2021 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `qnb-qatar-national-bank` | 2021 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `qnb-qatar-national-bank` | 2021 | scored | 85 | 68849 | 0.01 | 0 | — | 1086 | 51 | 433 | 28 | 8.582 |  |
| `qnb-qatar-national-bank` | 2022 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `qnb-qatar-national-bank` | 2022 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `qnb-qatar-national-bank` | 2022 | scored | 180 | 73312 | 0.03 | 0 | — | 341 | 108 | 513 | 75 | 8.273 |  |
| `qnb-qatar-national-bank` | 2023 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `qnb-qatar-national-bank` | 2023 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `qnb-qatar-national-bank` | 2023 | scored | 226 | 92950 | 0.04 | 0 | — | 1147 | 114 | 477 | 28 | 7.259 |  |
| `qnb-qatar-national-bank` | 2023 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `qnb-qatar-national-bank` | 2024 | scored | 254 | 100968 | 0.02 | 0 | — | 1352 | 129 | 533 | 26 | 7.397 |  |
| `qnb-qatar-national-bank` | 2024 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `qnb-qatar-national-bank` | 2024 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `qnb-qatar-national-bank` | 2024 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `qnb-qatar-national-bank` | 2025 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `qnb-qatar-national-bank` | 2025 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `qnb-qatar-national-bank` | 2025 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `qnb-qatar-national-bank` | 2025 | scored | 283 | 105207 | 0.05 | 2 | — | 1331 | 135 | 514 | 26 | 7.878 |  |
| `rabigh-refining-petrochemical-co` | 2020 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `rabigh-refining-petrochemical-co` | 2020 | scored | 100 | 20963 | 0.03 | 0 | 4,5 | 190 | 58 | 5 | 0 | 1.873 |  |
| `rabigh-refining-petrochemical-co` | 2020 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `rabigh-refining-petrochemical-co` | 2021 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `rabigh-refining-petrochemical-co` | 2021 | scored | 98 | 35928 | 0.02 | 0 | 5 | 160 | 27 | 42 | 0 | 6.641 |  |
| `rabigh-refining-petrochemical-co` | 2021 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `rabigh-refining-petrochemical-co` | 2022 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `rabigh-refining-petrochemical-co` | 2022 | scored | 104 | 37450 | 0.03 | 0 | 5 | 175 | 31 | 61 | 0 | 5.876 |  |
| `rabigh-refining-petrochemical-co` | 2022 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `rabigh-refining-petrochemical-co` | 2023 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `rabigh-refining-petrochemical-co` | 2023 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `rabigh-refining-petrochemical-co` | 2023 | scored | 98 | 37064 | 0.03 | 0 | 5 | 166 | 27 | 33 | 0 | 3.539 |  |
| `rabigh-refining-petrochemical-co` | 2024 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `rabigh-refining-petrochemical-co` | 2024 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `rabigh-refining-petrochemical-co` | 2024 | scored | 100 | 50145 | 0.02 | 0 | — | 97 | 78 | 126 | 5 | 3.711 |  |
| `rabigh-refining-petrochemical-co` | 2025 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `rabigh-refining-petrochemical-co` | 2025 | scored | 99 | 37606 | 0.02 | 0 | 3 | 188 | 76 | 186 | 4 | 6.134 |  |
| `rabigh-refining-petrochemical-co` | 2025 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `riyad-bank` | 2020 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `riyad-bank` | 2020 | scored | 156 | 59960 | 0.01 | 0 | — | 953 | 79 | 72 | 0 | 2.852 |  |
| `riyad-bank` | 2020 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `riyad-bank` | 2021 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `riyad-bank` | 2021 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `riyad-bank` | 2021 | scored | 208 | 65909 | 0.01 | 0 | — | 452 | 114 | 108 | 3 | 3.230 |  |
| `riyad-bank` | 2022 | scored | 106 | 67437 | 0.00 | 0 | — | 578 | 65 | 150 | 3 | 4.519 |  |
| `riyad-bank` | 2022 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `riyad-bank` | 2022 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `riyad-bank` | 2023 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `riyad-bank` | 2023 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `riyad-bank` | 2023 | scored | 115 | 68354 | 0.01 | 0 | — | 308 | 69 | 176 | 4 | 4.545 |  |
| `riyad-bank` | 2024 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `riyad-bank` | 2024 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `riyad-bank` | 2024 | scored | 130 | 75176 | 0.00 | 0 | — | 406 | 83 | 340 | 3 | 6.727 |  |
| `riyad-bank` | 2025 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `riyad-bank` | 2025 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `riyad-bank` | 2025 | scored | 143 | 80900 | 0.01 | 0 | — | 329 | 96 | 368 | 2 | 6.641 |  |
| `sabic` | 2020 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `sabic` | 2020 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `sabic` | 2020 | scored | 72 | 49586 | 0.01 | 0 | — | 182 | — | 222 | 2 | 4.931 |  |
| `sabic` | 2021 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `sabic` | 2021 | scored | 68 | 45809 | 0.01 | 0 | — | 167 | — | 231 | 7 | 5.636 |  |
| `sabic` | 2021 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `sabic` | 2022 | scored | 69 | 44162 | 0.00 | 0 | — | 171 | — | 320 | 8 | 6.933 |  |
| `sabic` | 2022 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `sabic` | 2022 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `sabic` | 2023 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `sabic` | 2023 | scored | 351 | 131500 | 0.00 | 0 | — | 6358 | 208 | 624 | 42 | 8.316 |  |
| `sabic` | 2023 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `sabic` | 2024 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `sabic` | 2024 | scored | 288 | 107362 | 0.00 | 0 | — | 5111 | 164 | 410 | 14 | 8.222 |  |
| `sabic` | 2024 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `sabic` | 2025 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `sabic` | 2025 | scored | 262 | 96488 | 0.00 | 0 | — | 3970 | 125 | 311 | 12 | 8.162 |  |
| `sabic` | 2025 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `sahara-international-petrochemical-co` | 2020 | scored | 148 | 48819 | 0.01 | 0 | 2 | 453 | 62 | 57 | 2 | 3.840 |  |
| `sahara-international-petrochemical-co` | 2020 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `sahara-international-petrochemical-co` | 2020 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `sahara-international-petrochemical-co` | 2021 | scored | 140 | 44704 | 0.01 | 0 | — | 366 | 78 | 42 | 2 | 2.474 |  |
| `sahara-international-petrochemical-co` | 2021 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `sahara-international-petrochemical-co` | 2021 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `sahara-international-petrochemical-co` | 2022 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `sahara-international-petrochemical-co` | 2022 | scored | 44 | 4214 | 0.05 | 0 | — | 109 | — | 17 | 0 | 3.608 | threshold |
| `sahara-international-petrochemical-co` | 2022 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `sahara-international-petrochemical-co` | 2023 | scored | 79 | 18174 | 0.01 | 0 | 3,4,5 | 0 | — | 61 | 2 | 4.046 |  |
| `sahara-international-petrochemical-co` | 2023 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `sahara-international-petrochemical-co` | 2023 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `sahara-international-petrochemical-co` | 2024 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `sahara-international-petrochemical-co` | 2024 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `sahara-international-petrochemical-co` | 2024 | scored | 80 | 17848 | 0.00 | 0 | — | 216 | — | 62 | 1 | 4.373 |  |
| `sahara-international-petrochemical-co` | 2025 | scored | 86 | 19087 | 0.00 | 0 | — | 269 | — | 67 | 1 | 5.060 |  |
| `sahara-international-petrochemical-co` | 2025 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `sahara-international-petrochemical-co` | 2025 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `salam-international-investment` | 2020 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `salam-international-investment` | 2020 | scored | 15 | 4044 | 0.07 | 0 | — | 28 | 9 | 0 | 0 | 0.498 | threshold |
| `salam-international-investment` | 2020 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `salam-international-investment` | 2021 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `salam-international-investment` | 2021 | scored | 29 | 3645 | 0.07 | 0 | — | 0 | 17 | 0 | 0 | 0.498 | threshold |
| `salam-international-investment` | 2021 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `salam-international-investment` | 2022 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `salam-international-investment` | 2022 | scored | 170 | 53057 | 0.02 | 0 | — | 0 | 84 | 85 | 6 | 2.895 |  |
| `salam-international-investment` | 2022 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `salam-international-investment` | 2023 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `salam-international-investment` | 2023 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `salam-international-investment` | 2023 | scored | 151 | 49714 | 0.06 | 1 | — | 0 | 58 | 72 | 6 | 3.101 |  |
| `salam-international-investment` | 2024 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `salam-international-investment` | 2024 | scored | 153 | 49062 | 0.05 | 0 | — | 0 | 58 | 71 | 3 | 3.110 |  |
| `salam-international-investment` | 2024 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `salam-international-investment` | 2025 | scored | 176 | 51482 | 0.09 | 0 | — | 176 | 96 | 74 | 2 | 2.861 |  |
| `salam-international-investment` | 2025 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `salam-international-investment` | 2025 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `saudi-airlines-catering-company-catrion` | 2020 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `saudi-airlines-catering-company-catrion` | 2020 | scored | 79 | 53700 | 0.01 | 0 | — | 189 | 58 | 102 | 4 | 3.961 |  |
| `saudi-airlines-catering-company-catrion` | 2020 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `saudi-airlines-catering-company-catrion` | 2021 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `saudi-airlines-catering-company-catrion` | 2021 | scored | 93 | 55442 | 0.00 | 0 | — | 389 | 59 | 92 | 1 | 4.184 |  |
| `saudi-airlines-catering-company-catrion` | 2021 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `saudi-airlines-catering-company-catrion` | 2022 | scored | 77 | 46744 | 0.00 | 0 | — | 180 | 54 | 114 | 2 | 4.983 |  |
| `saudi-airlines-catering-company-catrion` | 2022 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `saudi-airlines-catering-company-catrion` | 2022 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `saudi-airlines-catering-company-catrion` | 2023 | scored | 113 | 56062 | 0.04 | 0 | — | 894 | 77 | 174 | 4 | 6.366 |  |
| `saudi-airlines-catering-company-catrion` | 2023 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `saudi-airlines-catering-company-catrion` | 2023 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `saudi-airlines-catering-company-catrion` | 2024 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `saudi-airlines-catering-company-catrion` | 2024 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `saudi-airlines-catering-company-catrion` | 2024 | scored | 223 | 60830 | 0.00 | 0 | — | 502 | 168 | 217 | 4 | 6.031 |  |
| `saudi-airlines-catering-company-catrion` | 2025 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `saudi-airlines-catering-company-catrion` | 2025 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `saudi-airlines-catering-company-catrion` | 2025 | scored | 234 | 71611 | 0.00 | 0 | — | 305 | 175 | 185 | 6 | 3.471 |  |
| `saudi-arabian-fertilizer-company` | 2020 | scored | 33 | 14194 | 0.03 | 0 | — | 0 | 11 | 9 | 0 | 3.814 |  |
| `saudi-arabian-fertilizer-company` | 2020 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `saudi-arabian-fertilizer-company` | 2020 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `saudi-arabian-fertilizer-company` | 2021 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `saudi-arabian-fertilizer-company` | 2021 | scored | 38 | 21230 | 0.00 | 0 | — | 37 | — | 51 | 1 | 4.390 |  |
| `saudi-arabian-fertilizer-company` | 2021 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `saudi-arabian-fertilizer-company` | 2022 | scored | 47 | 22997 | 0.02 | 0 | — | 78 | — | 69 | 3 | 4.124 |  |
| `saudi-arabian-fertilizer-company` | 2022 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `saudi-arabian-fertilizer-company` | 2022 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `saudi-arabian-fertilizer-company` | 2023 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `saudi-arabian-fertilizer-company` | 2023 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `saudi-arabian-fertilizer-company` | 2023 | scored | 57 | 25165 | 0.02 | 0 | — | 260 | — | 91 | 4 | 6.005 |  |
| `saudi-arabian-fertilizer-company` | 2024 | scored | 47 | 25368 | 0.00 | 0 | — | 752 | — | 113 | 4 | 5.936 |  |
| `saudi-arabian-fertilizer-company` | 2024 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `saudi-arabian-fertilizer-company` | 2024 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `saudi-arabian-fertilizer-company` | 2025 | scored | 72 | 30598 | 0.00 | 0 | — | 623 | — | 185 | 5 | 7.809 |  |
| `saudi-arabian-fertilizer-company` | 2025 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `saudi-arabian-fertilizer-company` | 2025 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `saudi-aramco` | 2020 | scored | 254 | 94585 | 0.00 | 0 | 3,6,36 | 76 | 136 | 216 | 20 | 7.345 |  |
| `saudi-aramco` | 2020 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `saudi-aramco` | 2020 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `saudi-aramco` | 2021 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `saudi-aramco` | 2021 | scored | 256 | 98194 | 0.01 | 0 | 3,6,36 | 328 | 132 | 201 | 5 | 7.191 |  |
| `saudi-aramco` | 2021 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `saudi-aramco` | 2022 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `saudi-aramco` | 2022 | scored | 230 | 94756 | 0.01 | 0 | 3,6,28 | 1524 | 120 | 231 | 10 | 7.431 |  |
| `saudi-aramco` | 2022 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `saudi-aramco` | 2023 | scored | 121 | 97503 | 0.02 | 0 | 3,5,16 | 1907 | 61 | 188 | 5 | 6.598 |  |
| `saudi-aramco` | 2023 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `saudi-aramco` | 2023 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `saudi-aramco` | 2024 | scored | 238 | 97665 | 0.01 | 0 | 5,9,31 | 2278 | 121 | 205 | 5 | 6.735 |  |
| `saudi-aramco` | 2024 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `saudi-aramco` | 2024 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `saudi-aramco` | 2025 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `saudi-aramco` | 2025 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `saudi-aramco` | 2025 | scored | 246 | 99910 | 0.00 | 0 | — | 1718 | 129 | 174 | 4 | 6.125 |  |
| `saudi-cement` | 2020 | scored | 39 | 11265 | 0.00 | 0 | — | 37 | — | 22 | 0 | 2.947 |  |
| `saudi-cement` | 2020 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `saudi-cement` | 2020 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `saudi-cement` | 2021 | scored | 37 | 10615 | 0.00 | 0 | — | 35 | — | 23 | 0 | 4.038 |  |
| `saudi-cement` | 2021 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `saudi-cement` | 2021 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `saudi-cement` | 2022 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `saudi-cement` | 2022 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `saudi-cement` | 2022 | scored | 36 | 10682 | 0.03 | 0 | — | 34 | — | 24 | 1 | 4.064 |  |
| `saudi-cement` | 2023 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `saudi-cement` | 2023 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `saudi-cement` | 2023 | scored | 38 | 11220 | 0.00 | 0 | — | 37 | — | 24 | 0 | 4.235 |  |
| `saudi-cement` | 2024 | scored | 41 | 10376 | 0.05 | 0 | — | 38 | — | 24 | 0 | 3.935 |  |
| `saudi-cement` | 2024 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `saudi-cement` | 2024 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `saudi-cement` | 2025 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `saudi-cement` | 2025 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `saudi-cement` | 2025 | scored | 40 | 10068 | 0.05 | 0 | 5 | 38 | — | 32 | 0 | 5.928 |  |
| `saudi-industrial-investment-group` | 2020 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `saudi-industrial-investment-group` | 2020 | scored | 44 | 10667 | 0.11 | 1 | — | 17 | 19 | 9 | 0 | 5.696 |  |
| `saudi-industrial-investment-group` | 2020 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `saudi-industrial-investment-group` | 2021 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `saudi-industrial-investment-group` | 2021 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `saudi-industrial-investment-group` | 2021 | scored | 62 | 9034 | 0.16 | 0 | — | 26 | — | 22 | 0 | 4.330 |  |
| `saudi-industrial-investment-group` | 2022 | scored | 34 | 13060 | 0.06 | 0 | — | 28 | 26 | 13 | 0 | 1.478 |  |
| `saudi-industrial-investment-group` | 2022 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `saudi-industrial-investment-group` | 2022 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `saudi-industrial-investment-group` | 2023 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `saudi-industrial-investment-group` | 2023 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `saudi-industrial-investment-group` | 2023 | scored | 32 | 13405 | 0.03 | 0 | — | 29 | 16 | 9 | 0 | 3.651 |  |
| `saudi-industrial-investment-group` | 2024 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `saudi-industrial-investment-group` | 2024 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `saudi-industrial-investment-group` | 2024 | scored | 46 | 12528 | 0.07 | 0 | 5 | 34 | 20 | 8 | 0 | 3.583 |  |
| `saudi-industrial-investment-group` | 2025 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `saudi-industrial-investment-group` | 2025 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `saudi-industrial-investment-group` | 2025 | scored | 46 | 12157 | 0.00 | 0 | — | 40 | — | 24 | 0 | 2.517 |  |
| `saudi-telecom-company` | 2020 | scored | 119 | 59505 | 0.00 | 0 | — | 505 | 58 | 82 | 1 | 3.479 |  |
| `saudi-telecom-company` | 2020 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `saudi-telecom-company` | 2020 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `saudi-telecom-company` | 2021 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `saudi-telecom-company` | 2021 | scored | 122 | 58271 | 0.00 | 0 | — | 632 | 66 | 66 | 1 | 2.251 |  |
| `saudi-telecom-company` | 2021 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `saudi-telecom-company` | 2022 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `saudi-telecom-company` | 2022 | scored | 146 | 67140 | 0.00 | 0 | — | 724 | 44 | 71 | 3 | 3.849 |  |
| `saudi-telecom-company` | 2022 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `saudi-telecom-company` | 2023 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `saudi-telecom-company` | 2023 | scored | 134 | 77598 | 0.02 | 0 | — | 507 | 68 | 202 | 7 | 6.160 |  |
| `saudi-telecom-company` | 2023 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `saudi-telecom-company` | 2024 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `saudi-telecom-company` | 2024 | scored | 148 | 92059 | 0.01 | 0 | — | 731 | 74 | 232 | 4 | 6.117 |  |
| `saudi-telecom-company` | 2024 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `saudi-telecom-company` | 2025 | scored | 154 | 93560 | 0.02 | 0 | — | 1308 | 84 | 335 | 4 | 7.337 |  |
| `saudi-telecom-company` | 2025 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `saudi-telecom-company` | 2025 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `savola-group` | 2020 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `savola-group` | 2020 | scored | 60 | 38274 | 0.00 | 0 | — | 343 | 40 | 87 | 4 | 4.141 |  |
| `savola-group` | 2020 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `savola-group` | 2021 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `savola-group` | 2021 | scored | 64 | 36627 | 0.00 | 0 | — | 172 | 44 | 69 | 3 | 3.119 |  |
| `savola-group` | 2021 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `savola-group` | 2022 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `savola-group` | 2022 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `savola-group` | 2022 | scored | 66 | 36138 | 0.02 | 0 | — | 270 | 42 | 58 | 1 | 2.792 |  |
| `savola-group` | 2023 | scored | 92 | 62156 | 0.00 | 0 | — | 554 | 40 | 43 | 1 | 2.826 |  |
| `savola-group` | 2023 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `savola-group` | 2023 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `savola-group` | 2024 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `savola-group` | 2024 | scored | 128 | 78651 | 0.00 | 0 | — | 1169 | 38 | 96 | 2 | 6.211 |  |
| `savola-group` | 2024 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `savola-group` | 2025 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `savola-group` | 2025 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `savola-group` | 2025 | scored | 87 | 49304 | 0.00 | 0 | — | 605 | 29 | 84 | 5 | 6.452 |  |
| `sohar-international-bank` | 2020 | scored | 146 | 93714 | 0.00 | 0 | — | 2252 | 37 | 42 | 7 | 1.589 |  |
| `sohar-international-bank` | 2020 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `sohar-international-bank` | 2020 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `sohar-international-bank` | 2021 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `sohar-international-bank` | 2021 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `sohar-international-bank` | 2021 | scored | 155 | 99354 | 0.04 | 0 | — | 1069 | 39 | 59 | 9 | 1.589 |  |
| `sohar-international-bank` | 2022 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `sohar-international-bank` | 2022 | scored | 156 | 103132 | 0.04 | 0 | — | 1021 | 40 | 114 | 10 | 2.723 |  |
| `sohar-international-bank` | 2022 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `sohar-international-bank` | 2023 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `sohar-international-bank` | 2023 | scored | 143 | 97712 | 0.05 | 0 | — | 944 | 36 | 164 | 10 | 4.837 |  |
| `sohar-international-bank` | 2023 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `sohar-international-bank` | 2024 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `sohar-international-bank` | 2024 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `sohar-international-bank` | 2024 | scored | 144 | 94011 | 0.01 | 0 | — | 957 | 37 | 160 | 9 | 5.876 |  |
| `sohar-international-bank` | 2025 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `sohar-international-bank` | 2025 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `sohar-international-bank` | 2025 | scored | 148 | 96652 | 0.18 | 1 | 7 | 422 | 40 | 133 | 8 | 5.687 |  |
| `tamdeen-real-estate-company` | 2020 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `tamdeen-real-estate-company` | 2020 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `tamdeen-real-estate-company` | 2020 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `tamdeen-real-estate-company` | 2020 | scored | 58 | 21888 | 0.09 | 0 | 5 | 180 | 24 | 48 | 10 | 3.728 |  |
| `tamdeen-real-estate-company` | 2021 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `tamdeen-real-estate-company` | 2021 | scored | 62 | 22091 | 0.08 | 0 | 5 | 199 | 24 | 50 | 10 | 3.694 |  |
| `tamdeen-real-estate-company` | 2021 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `tamdeen-real-estate-company` | 2022 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `tamdeen-real-estate-company` | 2022 | scored | 62 | 22450 | 0.08 | 0 | 5 | 191 | 26 | 51 | 10 | 3.737 |  |
| `tamdeen-real-estate-company` | 2022 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `tamdeen-real-estate-company` | 2023 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `tamdeen-real-estate-company` | 2023 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `tamdeen-real-estate-company` | 2023 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `tamdeen-real-estate-company` | 2023 | scored | 62 | 23015 | 0.06 | 0 | 3 | 206 | 24 | 52 | 10 | 3.780 |  |
| `tamdeen-real-estate-company` | 2024 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `tamdeen-real-estate-company` | 2024 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `tamdeen-real-estate-company` | 2024 | scored | 60 | 22498 | 0.10 | 0 | 3 | 189 | 24 | 51 | 10 | 3.789 |  |
| `tamdeen-real-estate-company` | 2024 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `tamdeen-real-estate-company` | 2025 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `tamdeen-real-estate-company` | 2025 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `tamdeen-real-estate-company` | 2025 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `tamdeen-real-estate-company` | 2025 | scored | 60 | 22860 | 0.10 | 0 | 3 | 189 | 24 | 55 | 11 | 4.253 |  |
| `the-national-bank-of-ras-al-khaimah` | 2020 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `the-national-bank-of-ras-al-khaimah` | 2020 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `the-national-bank-of-ras-al-khaimah` | 2020 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `the-national-bank-of-ras-al-khaimah` | 2020 | scored | 139 | 78398 | 0.00 | 0 | — | 2321 | 43 | 173 | 2 | 6.795 |  |
| `the-national-bank-of-ras-al-khaimah` | 2021 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `the-national-bank-of-ras-al-khaimah` | 2021 | scored | 137 | 76873 | 0.03 | 0 | — | 2291 | 50 | 181 | 6 | 5.799 |  |
| `the-national-bank-of-ras-al-khaimah` | 2021 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `the-national-bank-of-ras-al-khaimah` | 2022 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `the-national-bank-of-ras-al-khaimah` | 2022 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `the-national-bank-of-ras-al-khaimah` | 2022 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `the-national-bank-of-ras-al-khaimah` | 2022 | scored | 133 | 71983 | 0.02 | 1 | — | 480 | 47 | 180 | 5 | 6.014 |  |
| `the-national-bank-of-ras-al-khaimah` | 2023 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `the-national-bank-of-ras-al-khaimah` | 2023 | scored | 149 | 75041 | 0.01 | 0 | — | 482 | 64 | 266 | 9 | 8.651 |  |
| `the-national-bank-of-ras-al-khaimah` | 2023 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `the-national-bank-of-ras-al-khaimah` | 2024 | scored | 141 | 69461 | 0.01 | 0 | — | 471 | 63 | 278 | 10 | 8.230 |  |
| `the-national-bank-of-ras-al-khaimah` | 2024 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `the-national-bank-of-ras-al-khaimah` | 2024 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `the-national-bank-of-ras-al-khaimah` | 2025 | scored | 138 | 38345 | 0.01 | 0 | — | 529 | 71 | 314 | 13 | 7.680 |  |
| `the-national-bank-of-ras-al-khaimah` | 2025 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `the-national-bank-of-ras-al-khaimah` | 2025 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `the-saudi-national-bank` | 2020 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `the-saudi-national-bank` | 2020 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `the-saudi-national-bank` | 2020 | scored | 92 | 75484 | 0.00 | 0 | — | 157 | 53 | 65 | 1 | 1.942 |  |
| `the-saudi-national-bank` | 2021 | scored | 105 | 82435 | 0.03 | 0 | — | 106 | 61 | 75 | 1 | 1.890 |  |
| `the-saudi-national-bank` | 2021 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `the-saudi-national-bank` | 2021 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `the-saudi-national-bank` | 2022 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `the-saudi-national-bank` | 2022 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `the-saudi-national-bank` | 2022 | scored | 218 | 77542 | 0.05 | 0 | — | 0 | 122 | 103 | 1 | 3.488 |  |
| `the-saudi-national-bank` | 2023 | scored | 111 | 80402 | 0.00 | 0 | — | 286 | 63 | 129 | 2 | 5.120 |  |
| `the-saudi-national-bank` | 2023 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `the-saudi-national-bank` | 2023 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `the-saudi-national-bank` | 2024 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `the-saudi-national-bank` | 2024 | scored | 113 | 78610 | 0.00 | 0 | — | 359 | 62 | 144 | 5 | 5.129 |  |
| `the-saudi-national-bank` | 2024 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `the-saudi-national-bank` | 2025 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `the-saudi-national-bank` | 2025 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `the-saudi-national-bank` | 2025 | scored | 109 | 76995 | 0.00 | 0 | — | 310 | 60 | 165 | 4 | 4.811 |  |
| `yanbu-cement-company` | 2020 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `yanbu-cement-company` | 2020 | scored | 59 | 13922 | 0.00 | 0 | 3,4 | 86 | — | 48 | 0 | 3.187 |  |
| `yanbu-cement-company` | 2020 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `yanbu-cement-company` | 2021 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `yanbu-cement-company` | 2021 | scored | 36 | 9425 | 0.00 | 0 | 2 | 49 | — | 27 | 1 | 3.600 |  |
| `yanbu-cement-company` | 2021 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `yanbu-cement-company` | 2022 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `yanbu-cement-company` | 2022 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `yanbu-cement-company` | 2022 | scored | 48 | 12722 | 0.00 | 0 | — | 126 | — | 61 | 2 | 5.696 |  |
| `yanbu-cement-company` | 2023 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `yanbu-cement-company` | 2023 | scored | 45 | 16094 | 0.09 | 0 | — | 30 | — | 72 | 2 | 4.261 |  |
| `yanbu-cement-company` | 2023 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `yanbu-cement-company` | 2024 | scored | 44 | 16932 | 0.02 | 0 | — | 29 | — | 89 | 3 | 4.983 |  |
| `yanbu-cement-company` | 2024 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `yanbu-cement-company` | 2024 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `yanbu-cement-company` | 2025 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `yanbu-cement-company` | 2025 | scored | 51 | 20208 | 0.06 | 1 | — | 36 | — | 151 | 4 | 7.586 |  |
| `yanbu-cement-company` | 2025 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `yanbu-national-petrochemical` | 2020 | scored | 62 | 38086 | 0.02 | 0 | — | 58 | 40 | 70 | 2 | 4.433 |  |
| `yanbu-national-petrochemical` | 2020 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `yanbu-national-petrochemical` | 2020 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `yanbu-national-petrochemical` | 2021 | scored | 42 | 21986 | 0.00 | 0 | — | 77 | — | 85 | 5 | 4.742 |  |
| `yanbu-national-petrochemical` | 2021 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `yanbu-national-petrochemical` | 2021 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `yanbu-national-petrochemical` | 2022 | scored | 42 | 19263 | 0.00 | 0 | — | 70 | — | 81 | 7 | 4.768 |  |
| `yanbu-national-petrochemical` | 2022 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `yanbu-national-petrochemical` | 2022 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `yanbu-national-petrochemical` | 2023 | scored | 46 | 22098 | 0.00 | 0 | — | 92 | — | 103 | 6 | 5.747 |  |
| `yanbu-national-petrochemical` | 2023 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `yanbu-national-petrochemical` | 2023 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `yanbu-national-petrochemical` | 2024 | scored | 54 | 25676 | 0.02 | 0 | — | 535 | 15 | 34 | 2 | 6.753 |  |
| `yanbu-national-petrochemical` | 2024 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `yanbu-national-petrochemical` | 2024 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `yanbu-national-petrochemical` | 2025 | scored | 62 | 26246 | 0.00 | 0 | — | 688 | — | 180 | 5 | 7.792 |  |
| `yanbu-national-petrochemical` | 2025 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `yanbu-national-petrochemical` | 2025 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `zain-mobile-telecommunications-company` | 2020 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `zain-mobile-telecommunications-company` | 2020 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `zain-mobile-telecommunications-company` | 2020 | scored | 109 | 80011 | 0.02 | 0 | 3 | 203 | 76 | 223 | 20 | 6.503 |  |
| `zain-mobile-telecommunications-company` | 2021 | scored | 103 | 74818 | 0.00 | 0 | — | 360 | 69 | 316 | 38 | 7.775 |  |
| `zain-mobile-telecommunications-company` | 2021 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `zain-mobile-telecommunications-company` | 2021 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `zain-mobile-telecommunications-company` | 2021 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `zain-mobile-telecommunications-company` | 2022 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `zain-mobile-telecommunications-company` | 2022 | scored | 103 | 72580 | 0.02 | 0 | — | 442 | 69 | 287 | 30 | 7.148 |  |
| `zain-mobile-telecommunications-company` | 2022 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `zain-mobile-telecommunications-company` | 2023 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `zain-mobile-telecommunications-company` | 2023 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `zain-mobile-telecommunications-company` | 2023 | scored | 99 | 76681 | 0.03 | 0 | — | 254 | 66 | 321 | 32 | 7.294 |  |
| `zain-mobile-telecommunications-company` | 2024 | scored | 93 | 51001 | 0.03 | 0 | — | 257 | 86 | 410 | 43 | 8.514 |  |
| `zain-mobile-telecommunications-company` | 2024 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `zain-mobile-telecommunications-company` | 2024 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `zain-mobile-telecommunications-company` | 2025 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |
| `zain-mobile-telecommunications-company` | 2025 | scored | 159 | 90911 | 0.01 | 0 | — | 779 | 114 | 453 | 38 | 7.878 |  |
| `zain-mobile-telecommunications-company` | 2025 | error | 0 | 0 | — | 0 | — | 0 | — | 0 | — | — | threshold |

## Threshold flags

- `baladna` FY2023: very low Latin word count (0 < 5000)
- `mobile-telecommunications-co-saudi-arabia-zain` FY2021: very low Latin word count (0 < 5000)
- `sahara-international-petrochemical-co` FY2024: very low Latin word count (0 < 5000)
- `aluminium-bahrain-alba` FY2025: very low Latin word count (0 < 5000)
- `emirates-nbd-pjsc` FY2024: very low Latin word count (0 < 5000)
- `emirates-telecom-etisalat-group` FY2021: very low Latin word count (0 < 5000)
- `baladna` FY2024: very low Latin word count (0 < 5000)
- `emirates-telecom-etisalat-group` FY2022: very low Latin word count (0 < 5000)
- `emirates-telecom-etisalat-group` FY2020: very low Latin word count (0 < 5000)
- `zain-mobile-telecommunications-company` FY2023: very low Latin word count (0 < 5000)
- `bahrain-telecommunications-beyon` FY2025: very low Latin word count (0 < 5000)
- `abu-dhabi-commercial-bank` FY2025: very low Latin word count (0 < 5000)
- `sahara-international-petrochemical-co` FY2025: very low Latin word count (0 < 5000)
- `bahrain-telecommunications-beyon` FY2023: very low Latin word count (0 < 5000)
- `emirates-nbd-pjsc` FY2023: very low Latin word count (0 < 5000)
- `maaden` FY2025: very low Latin word count (0 < 5000)
- `abu-dhabi-commercial-bank` FY2024: very low Latin word count (0 < 5000)
- `bahrain-telecommunications-beyon` FY2024: very low Latin word count (0 < 5000)
- `bank-albilad` FY2022: very low Latin word count (0 < 5000)
- `bahrain-telecommunications-beyon` FY2022: very low Latin word count (0 < 5000)
- `abdullah-al-othaim-markets` FY2025: very low Latin word count (0 < 5000)
- `bank-dhofar` FY2020: very low Latin word count (0 < 5000)
- `abu-dhabi-commercial-bank` FY2022: very low Latin word count (0 < 5000)
- `saudi-airlines-catering-company-catrion` FY2021: very low Latin word count (0 < 5000)
- `abu-dhabi-commercial-bank` FY2023: very low Latin word count (0 < 5000)
- `mobile-telecommunications-co-saudi-arabia-zain` FY2023: very low Latin word count (0 < 5000)
- `emaar-properties` FY2025: very low Latin word count (0 < 5000)
- `maaden` FY2024: very low Latin word count (0 < 5000)
- `emirates-nbd-pjsc` FY2025: very low Latin word count (0 < 5000)
- `baladna` FY2021: very low Latin word count (0 < 5000)
- `emirates-nbd-pjsc` FY2022: very low Latin word count (0 < 5000)
- `mouwasat-medical-services-company` FY2020: very low Latin word count (0 < 5000)
- `saudi-airlines-catering-company-catrion` FY2022: very low Latin word count (0 < 5000)
- `jazeera-steel` FY2024: very low Latin word count (0 < 5000)
- `mobile-telecommunications-co-saudi-arabia-zain` FY2022: very low Latin word count (0 < 5000)
- `maaden` FY2021: very low Latin word count (0 < 5000)
- `baladna` FY2025: very low Latin word count (0 < 5000)
- `salam-international-investment` FY2024: very low Latin word count (0 < 5000)
- `aluminium-bahrain-alba` FY2023: very low Latin word count (0 < 5000)
- `maaden` FY2023: very low Latin word count (0 < 5000)
- `etihad-etisalat-mobily` FY2020: very low Latin word count (0 < 5000)
- `emaar-properties` FY2023: very low Latin word count (0 < 5000)
- `abu-dhabi-national-oil-company-for-distribution` FY2022: very low Latin word count (0 < 5000)
- `bahrain-telecommunications-beyon` FY2021: very low Latin word count (0 < 5000)
- `mobile-telecommunications-co-saudi-arabia-zain` FY2020: very low Latin word count (0 < 5000)
- `abu-dhabi-national-energy-company` FY2022: very low Latin word count (0 < 5000)
- `zain-mobile-telecommunications-company` FY2024: very low Latin word count (0 < 5000)
- `abu-dhabi-national-oil-company-for-distribution` FY2021: very low Latin word count (0 < 5000)
- `tamdeen-real-estate-company` FY2020: very low Latin word count (0 < 5000)
- `emaar-properties` FY2024: very low Latin word count (0 < 5000)
- `salam-international-investment` FY2022: very low Latin word count (0 < 5000)
- `salam-international-investment` FY2023: very low Latin word count (0 < 5000)
- `sohar-international-bank` FY2025: very low Latin word count (0 < 5000)
- `maaden` FY2022: very low Latin word count (0 < 5000)
- `salam-international-investment` FY2025: very low Latin word count (0 < 5000)
- `sohar-international-bank` FY2023: very low Latin word count (0 < 5000)
- `sohar-international-bank` FY2024: very low Latin word count (0 < 5000)
- `abu-dhabi-national-energy-company` FY2024: very low Latin word count (0 < 5000)
- `baladna` FY2020: very low Latin word count (0 < 5000)
- `baladna` FY2022: very low Latin word count (0 < 5000)
- `bank-albilad` FY2020: very low Latin word count (0 < 5000)
- `abu-dhabi-national-energy-company` FY2023: very low Latin word count (0 < 5000)
- `bank-albilad` FY2021: very low Latin word count (0 < 5000)
- `emirates-nbd-pjsc` FY2021: very low Latin word count (0 < 5000)
- `salam-international-investment` FY2021: very low Latin word count (0 < 5000)
- `aluminium-bahrain-alba` FY2024: very low Latin word count (0 < 5000)
- `saudi-airlines-catering-company-catrion` FY2020: very low Latin word count (0 < 5000)
- `ooredoo-q-p-s-c` FY2023: very low Latin word count (0 < 5000)
- `tamdeen-real-estate-company` FY2024: very low Latin word count (0 < 5000)
- `boubyan-bank` FY2024: very low Latin word count (0 < 5000)
- `abu-dhabi-national-oil-company-for-distribution` FY2020: very low Latin word count (0 < 5000)
- `al-rajhi-bank` FY2024: very low Latin word count (0 < 5000)
- `sohar-international-bank` FY2022: very low Latin word count (0 < 5000)
- `ooredoo-q-p-s-c` FY2024: very low Latin word count (0 < 5000)
- `mobile-telecommunications-co-saudi-arabia-zain` FY2025: very low Latin word count (0 < 5000)
- `boubyan-bank` FY2023: very low Latin word count (0 < 5000)
- `abu-dhabi-national-energy-company` FY2025: very low Latin word count (0 < 5000)
- `etihad-etisalat-mobily` FY2024: very low Latin word count (0 < 5000)
- `boubyan-bank` FY2025: very low Latin word count (0 < 5000)
- `abu-dhabi-national-oil-company-for-distribution` FY2023: very low Latin word count (0 < 5000)
- `sohar-international-bank` FY2020: very low Latin word count (0 < 5000)
- `riyad-bank` FY2021: very low Latin word count (0 < 5000)
- `almarai` FY2022: very low Latin word count (0 < 5000)
- `air-arabia-pjsc` FY2025: very low Latin word count (0 < 5000)
- `tamdeen-real-estate-company` FY2022: very low Latin word count (0 < 5000)
- `qnb-qatar-national-bank` FY2021: very low Latin word count (0 < 5000)
- `dubai-investment` FY2021: very low Latin word count (0 < 5000)
- `abu-dhabi-national-oil-company-for-distribution` FY2025: very low Latin word count (0 < 5000)
- `zain-mobile-telecommunications-company` FY2021: very low Latin word count (0 < 5000)
- `qnb-qatar-national-bank` FY2023: very low Latin word count (0 < 5000)
- `gulf-international-services` FY2024: very low Latin word count (0 < 5000)
- `tamdeen-real-estate-company` FY2025: very low Latin word count (0 < 5000)
- `qnb-qatar-national-bank` FY2025: very low Latin word count (0 < 5000)
- `kuwait-telecommunications-company` FY2022: very low Latin word count (0 < 5000)
- `boubyan-bank` FY2022: very low Latin word count (0 < 5000)
- `savola-group` FY2025: very low Latin word count (0 < 5000)
- `saudi-aramco` FY2021: very low Latin word count (0 < 5000)
- `national-bank-of-bahrain` FY2022: very low Latin word count (0 < 5000)
- `qnb-qatar-national-bank` FY2024: very low Latin word count (0 < 5000)
- `abdullah-al-othaim-markets` FY2024: very low Latin word count (0 < 5000)
- `gulf-international-services` FY2022: very low Latin word count (0 < 5000)
- `boubyan-bank` FY2020: very low Latin word count (0 < 5000)
- `aldar-properties-pjsc` FY2024: very low Latin word count (0 < 5000)
- `abu-dhabi-national-energy-company` FY2021: very low Latin word count (0 < 5000)
- `savola-group` FY2023: very low Latin word count (0 < 5000)
- `national-bank-of-kuwait` FY2020: very low Latin word count (0 < 5000)
- `the-national-bank-of-ras-al-khaimah` FY2020: very low Latin word count (0 < 5000)
- `saudi-arabian-fertilizer-company` FY2025: very low Latin word count (0 < 5000)
- `rabigh-refining-petrochemical-co` FY2020: very low Latin word count (0 < 5000)
- `aldar-properties-pjsc` FY2025: very low Latin word count (0 < 5000)
- `air-arabia-pjsc` FY2022: very low Latin word count (0 < 5000)
- `savola-group` FY2024: very low Latin word count (0 < 5000)
- `dar-al-arkan-real-estate-development-company` FY2021: very low Latin word count (0 < 5000)
- `qatar-fuel-company-woqod` FY2020: very low Latin word count (0 < 5000)
- `abu-dhabi-national-energy-company` FY2020: very low Latin word count (0 < 5000)
- `kuwait-finance-house` FY2025: very low Latin word count (0 < 5000)
- `gulf-hotels-group` FY2025: very low Latin word count (0 < 5000)
- `barwa-real-estate` FY2025: very low Latin word count (0 < 5000)
- `alinma-bank` FY2025: very low Latin word count (0 < 5000)
- `barwa-real-estate` FY2023: very low Latin word count (0 < 5000)
- `advanced-petrochemical` FY2022: very low Latin word count (0 < 5000)
- `kuwait-telecommunications-company` FY2021: very low Latin word count (0 < 5000)
- `gulf-international-services` FY2025: very low Latin word count (0 < 5000)
- `the-national-bank-of-ras-al-khaimah` FY2022: very low Latin word count (0 < 5000)
- `bahrain-telecommunications-beyon` FY2020: very low Latin word count (0 < 5000)
- `abdullah-al-othaim-markets` FY2023: very low Latin word count (0 < 5000)
- `national-industrialization-co` FY2024: very low Latin word count (0 < 5000)
- `emirates-telecom-etisalat-group` FY2023: very low Latin word count (0 < 5000)
- `barwa-real-estate` FY2024: very low Latin word count (0 < 5000)
- `al-rajhi-bank` FY2020: very low Latin word count (0 < 5000)
- `the-saudi-national-bank` FY2021: very low Latin word count (0 < 5000)
- `emirates-telecom-etisalat-group` FY2024: very low Latin word count (0 < 5000)
- `maaden` FY2020: very low Latin word count (0 < 5000)
- `gulf-hotels-group` FY2023: very low Latin word count (0 < 5000)
- `dar-al-arkan-real-estate-development-company` FY2024: very low Latin word count (0 < 5000)
- `sabic` FY2025: very low Latin word count (0 < 5000)
- `oman-international-development-and-investment-company` FY2021: very low Latin word count (0 < 5000)
- `aluminium-bahrain-alba` FY2022: very low Latin word count (0 < 5000)
- `the-national-bank-of-ras-al-khaimah` FY2024: very low Latin word count (0 < 5000)
- `national-industrialization-co` FY2025: very low Latin word count (0 < 5000)
- `kuwait-telecommunications-company` FY2023: very low Latin word count (0 < 5000)
- `alinma-bank` FY2020: very low Latin word count (0 < 5000)
- `sohar-international-bank` FY2021: very low Latin word count (0 < 5000)
- `oman-international-development-and-investment-company` FY2022: very low Latin word count (0 < 5000)
- `kuwait-finance-house` FY2021: very low Latin word count (0 < 5000)
- `dar-al-arkan-real-estate-development-company` FY2023: very low Latin word count (0 < 5000)
- `dar-al-arkan-real-estate-development-company` FY2025: very low Latin word count (0 < 5000)
- `air-arabia-pjsc` FY2021: very low Latin word count (0 < 5000)
- `the-national-bank-of-ras-al-khaimah` FY2021: very low Latin word count (0 < 5000)
- `the-national-bank-of-ras-al-khaimah` FY2025: very low Latin word count (0 < 5000)
- `saudi-cement` FY2020: very low Latin word count (0 < 5000)
- `sabic` FY2022: very low Latin word count (0 < 5000)
- `dar-al-arkan-real-estate-development-company` FY2022: very low Latin word count (0 < 5000)
- `saudi-cement` FY2022: very low Latin word count (0 < 5000)
- `barwa-real-estate` FY2022: very low Latin word count (0 < 5000)
- `savola-group` FY2022: very low Latin word count (0 < 5000)
- `the-national-bank-of-ras-al-khaimah` FY2023: very low Latin word count (0 < 5000)
- `national-industrialization-co` FY2023: very low Latin word count (0 < 5000)
- `national-industrialization-co` FY2022: very low Latin word count (0 < 5000)
- `etihad-etisalat-mobily` FY2025: very low Latin word count (0 < 5000)
- `sabic` FY2024: very low Latin word count (0 < 5000)
- `sabic` FY2020: very low Latin word count (0 < 5000)
- `alinma-bank` FY2021: very low Latin word count (0 < 5000)
- `zain-mobile-telecommunications-company` FY2022: very low Latin word count (0 < 5000)
- `savola-group` FY2020: very low Latin word count (0 < 5000)
- `saudi-aramco` FY2025: very low Latin word count (0 < 5000)
- `oman-telecommunications-company-otel` FY2021: very low Latin word count (0 < 5000)
- `dubai-investment` FY2022: very low Latin word count (0 < 5000)
- `saudi-arabian-fertilizer-company` FY2020: very low Latin word count (0 < 5000)
- `the-saudi-national-bank` FY2022: very low Latin word count (0 < 5000)
- `saudi-telecom-company` FY2025: very low Latin word count (0 < 5000)
- `riyad-bank` FY2025: very low Latin word count (0 < 5000)
- `jazeera-steel` FY2021: very low Latin word count (0 < 5000)
- `sahara-international-petrochemical-co` FY2021: very low Latin word count (0 < 5000)
- `kuwait-finance-house` FY2023: very low Latin word count (0 < 5000)
- `aldar-properties-pjsc` FY2020: very low Latin word count (0 < 5000)
- `saudi-aramco` FY2024: very low Latin word count (0 < 5000)
- `first-abu-dhabi-bank` FY2020: very low Latin word count (0 < 5000)
- `dubai-investment` FY2023: very low Latin word count (0 < 5000)
- `saudi-industrial-investment-group` FY2021: very low Latin word count (0 < 5000)
- `qnb-qatar-national-bank` FY2022: very low Latin word count (0 < 5000)
- `mouwasat-medical-services-company` FY2024: very low Latin word count (0 < 5000)
- `barwa-real-estate` FY2021: very low Latin word count (0 < 5000)
- `the-saudi-national-bank` FY2020: very low Latin word count (0 < 5000)
- `gulf-hotels-group` FY2024: very low Latin word count (0 < 5000)
- `dubai-islamic-bank` FY2022: very low Latin word count (0 < 5000)
- `saudi-airlines-catering-company-catrion` FY2024: very low Latin word count (0 < 5000)
- `first-abu-dhabi-bank` FY2021: very low Latin word count (0 < 5000)
- `yanbu-cement-company` FY2025: very low Latin word count (0 < 5000)
- `jazeera-steel` FY2020: very low Latin word count (0 < 5000)
- `riyad-bank` FY2024: very low Latin word count (0 < 5000)
- `dubai-investment` FY2025: very low Latin word count (0 < 5000)
- `almarai` FY2024: very low Latin word count (0 < 5000)
- `abu-dhabi-commercial-bank` FY2021: very low Latin word count (0 < 5000)
- `yanbu-cement-company` FY2024: very low Latin word count (0 < 5000)
- `aluminium-bahrain-alba` FY2021: very low Latin word count (0 < 5000)
- `al-rajhi-bank` FY2022: very low Latin word count (0 < 5000)
- `yanbu-national-petrochemical` FY2020: very low Latin word count (0 < 5000)
- `riyad-bank` FY2023: very low Latin word count (0 < 5000)
- `barwa-real-estate` FY2020: very low Latin word count (0 < 5000)
- `abu-dhabi-commercial-bank` FY2020: very low Latin word count (0 < 5000)
- `yanbu-cement-company` FY2023: very low Latin word count (0 < 5000)
- `oman-international-development-and-investment-company` FY2023: very low Latin word count (0 < 5000)
- `national-industrialization-co` FY2020: very low Latin word count (0 < 5000)
- `advanced-petrochemical` FY2024: very low Latin word count (0 < 5000)
- `saudi-cement` FY2024: very low Latin word count (0 < 5000)
- `jazeera-airways` FY2025: very low Latin word count (0 < 5000)
- `gulf-hotels-group` FY2021: very low Latin word count (0 < 5000)
- `saudi-cement` FY2023: very low Latin word count (0 < 5000)
- `dubai-islamic-bank` FY2025: very low Latin word count (0 < 5000)
- `alinma-bank` FY2022: very low Latin word count (0 < 5000)
- `jazeera-airways` FY2023: very low Latin word count (0 < 5000)
- `bank-dhofar` FY2021: very low Latin word count (0 < 5000)
- `kuwait-finance-house` FY2024: very low Latin word count (0 < 5000)
- `saudi-aramco` FY2022: very low Latin word count (0 < 5000)
- `national-bank-of-bahrain` FY2021: very low Latin word count (0 < 5000)
- `jazeera-airways` FY2024: very low Latin word count (0 < 5000)
- `bank-muscat-bkmb` FY2024: very low Latin word count (0 < 5000)
- `oman-international-development-and-investment-company` FY2025: very low Latin word count (0 < 5000)
- `national-bank-of-bahrain` FY2020: very low Latin word count (0 < 5000)
- `aluminium-bahrain-alba` FY2020: very low Latin word count (0 < 5000)
- `saudi-arabian-fertilizer-company` FY2022: very low Latin word count (0 < 5000)
- `kuwait-telecommunications-company` FY2025: very low Latin word count (0 < 5000)
- `saudi-cement` FY2025: very low Latin word count (0 < 5000)
- `national-bank-of-kuwait` FY2025: very low Latin word count (0 < 5000)
- `etihad-etisalat-mobily` FY2023: very low Latin word count (0 < 5000)
- `emirates-telecom-etisalat-group` FY2025: very low Latin word count (0 < 5000)
- `bank-dhofar` FY2025: very low Latin word count (0 < 5000)
- `dar-al-arkan-real-estate-development-company` FY2020: very low Latin word count (0 < 5000)
- `bank-albilad` FY2024: very low Latin word count (0 < 5000)
- `almarai` FY2021: very low Latin word count (0 < 5000)
- `oman-telecommunications-company-otel` FY2020: very low Latin word count (0 < 5000)
- `national-bank-of-bahrain` FY2025: very low Latin word count (0 < 5000)
- `saudi-industrial-investment-group` FY2020: very low Latin word count (0 < 5000)
- `saudi-arabian-fertilizer-company` FY2024: very low Latin word count (0 < 5000)
- `aldar-properties-pjsc` FY2023: very low Latin word count (0 < 5000)
- `saudi-industrial-investment-group` FY2022: very low Latin word count (0 < 5000)
- `industries-qatar` FY2020: very low Latin word count (0 < 5000)
- `etihad-etisalat-mobily` FY2022: very low Latin word count (0 < 5000)
- `alinma-bank` FY2024: very low Latin word count (0 < 5000)
- `yanbu-national-petrochemical` FY2022: very low Latin word count (0 < 5000)
- `saudi-cement` FY2021: very low Latin word count (0 < 5000)
- `al-rajhi-bank` FY2021: very low Latin word count (0 < 5000)
- `qnb-qatar-national-bank` FY2020: very low Latin word count (0 < 5000)
- `oman-telecommunications-company-otel` FY2022: very low Latin word count (0 < 5000)
- `alinma-bank` FY2023: very low Latin word count (0 < 5000)
- `etihad-etisalat-mobily` FY2021: very low Latin word count (0 < 5000)
- `yanbu-national-petrochemical` FY2025: very low Latin word count (0 < 5000)
- `jazeera-steel` FY2022: very low Latin word count (0 < 5000)
- `jazeera-airways` FY2022: very low Latin word count (0 < 5000)
- `qatar-gas-transport-co-nakilat` FY2025: very low Latin word count (0 < 5000)
- `ooredoo-q-p-s-c` FY2021: very low Latin word count (0 < 5000)
- `kuwait-finance-house` FY2022: very low Latin word count (0 < 5000)
- `yanbu-national-petrochemical` FY2021: very low Latin word count (0 < 5000)
- `jazeera-airways` FY2020: very low Latin word count (0 < 5000)
- `qatar-gas-transport-co-nakilat` FY2023: very low Latin word count (0 < 5000)
- `the-saudi-national-bank` FY2025: very low Latin word count (0 < 5000)
- `saudi-airlines-catering-company-catrion` FY2025: very low Latin word count (0 < 5000)
- `aldar-properties-pjsc` FY2022: very low Latin word count (0 < 5000)
- `qatar-gas-transport-co-nakilat` FY2024: very low Latin word count (0 < 5000)
- `bank-dhofar` FY2022: very low Latin word count (0 < 5000)
- `national-bank-of-kuwait` FY2021: very low Latin word count (0 < 5000)
- `mouwasat-medical-services-company` FY2022: very low Latin word count (0 < 5000)
- `kuwait-finance-house` FY2020: very low Latin word count (0 < 5000)
- `jarir-marketing-co` FY2025: very low Latin word count (0 < 5000)
- `boubyan-bank` FY2021: very low Latin word count (0 < 5000)
- `abdullah-al-othaim-markets` FY2022: very low Latin word count (0 < 5000)
- `sahara-international-petrochemical-co` FY2023: very low Latin word count (0 < 5000)
- `dubai-investment` FY2020: very low Latin word count (0 < 5000)
- `almarai` FY2020: very low Latin word count (0 < 5000)
- `jarir-marketing-co` FY2023: very low Latin word count (0 < 5000)
- `bank-muscat-bkmb` FY2022: very low Latin word count (0 < 5000)
- `advanced-petrochemical` FY2021: very low Latin word count (0 < 5000)
- `kuwait-telecommunications-company` FY2020: very low Latin word count (0 < 5000)
- `emaar-properties` FY2020: very low Latin word count (0 < 5000)
- `tamdeen-real-estate-company` FY2023: very low Latin word count (0 < 5000)
- `salam-international-investment` FY2020: very low Latin word count (0 < 5000)
- `jazeera-steel` FY2025: very low Latin word count (0 < 5000)
- `jarir-marketing-co` FY2024: very low Latin word count (0 < 5000)
- `yanbu-cement-company` FY2020: very low Latin word count (0 < 5000)
- `saudi-aramco` FY2023: very low Latin word count (0 < 5000)
- `saudi-arabian-fertilizer-company` FY2021: very low Latin word count (0 < 5000)
- `sabic` FY2021: very low Latin word count (0 < 5000)
- `saudi-telecom-company` FY2021: very low Latin word count (0 < 5000)
- `national-industrialization-co` FY2021: very low Latin word count (0 < 5000)
- `first-abu-dhabi-bank` FY2022: very low Latin word count (0 < 5000)
- `advanced-petrochemical` FY2023: very low Latin word count (0 < 5000)
- `yanbu-cement-company` FY2022: very low Latin word count (0 < 5000)
- `almarai` FY2023: very low Latin word count (0 < 5000)
- `yanbu-national-petrochemical` FY2024: very low Latin word count (0 < 5000)
- `mouwasat-medical-services-company` FY2021: very low Latin word count (0 < 5000)
- `rabigh-refining-petrochemical-co` FY2024: very low Latin word count (0 < 5000)
- `bank-muscat-bkmb` FY2021: very low Latin word count (0 < 5000)
- `almarai` FY2025: very low Latin word count (0 < 5000)
- `abdullah-al-othaim-markets` FY2021: very low Latin word count (0 < 5000)
- `saudi-industrial-investment-group` FY2024: very low Latin word count (0 < 5000)
- `riyad-bank` FY2022: very low Latin word count (0 < 5000)
- `dubai-islamic-bank` FY2024: very low Latin word count (0 < 5000)
- `saudi-industrial-investment-group` FY2023: very low Latin word count (0 < 5000)
- `saudi-industrial-investment-group` FY2025: very low Latin word count (0 < 5000)
- `first-abu-dhabi-bank` FY2024: very low Latin word count (0 < 5000)
- `abdullah-al-othaim-markets` FY2020: very low Latin word count (0 < 5000)
- `qatar-gas-transport-co-nakilat` FY2022: very low Latin word count (0 < 5000)
- `first-abu-dhabi-bank` FY2023: very low Latin word count (0 < 5000)
- `dubai-islamic-bank` FY2021: very low Latin word count (0 < 5000)
- `al-rajhi-bank` FY2023: very low Latin word count (0 < 5000)
- `jazeera-airways` FY2021: very low Latin word count (0 < 5000)
- `first-abu-dhabi-bank` FY2025: very low Latin word count (0 < 5000)
- `rabigh-refining-petrochemical-co` FY2023: very low Latin word count (0 < 5000)
- `qatar-gas-transport-co-nakilat` FY2020: very low Latin word count (0 < 5000)
- `kuwait-telecommunications-company` FY2024: very low Latin word count (0 < 5000)
- `bank-albilad` FY2025: very low Latin word count (0 < 5000)
- `jazeera-steel` FY2023: very low Latin word count (0 < 5000)
- `emaar-properties` FY2021: very low Latin word count (0 < 5000)
- `emirates-nbd-pjsc` FY2020: very low Latin word count (0 < 5000)
- `saudi-aramco` FY2020: very low Latin word count (0 < 5000)
- `jarir-marketing-co` FY2022: very low Latin word count (0 < 5000)
- `abu-dhabi-national-oil-company-for-distribution` FY2024: very low Latin word count (0 < 5000)
- `saudi-telecom-company` FY2020: very low Latin word count (0 < 5000)
- `rabigh-refining-petrochemical-co` FY2025: very low Latin word count (0 < 5000)
- `gulf-international-services` FY2021: very low Latin word count (0 < 5000)
- `bank-muscat-bkmb` FY2020: very low Latin word count (0 < 5000)
- `qatar-fuel-company-woqod` FY2025: very low Latin word count (0 < 5000)
- `jarir-marketing-co` FY2020: very low Latin word count (0 < 5000)
- `air-arabia-pjsc` FY2024: very low Latin word count (0 < 5000)
- `dubai-islamic-bank` FY2023: very low Latin word count (0 < 5000)
- `saudi-arabian-fertilizer-company` FY2023: very low Latin word count (0 < 5000)
- `qatar-fuel-company-woqod` FY2023: very low Latin word count (0 < 5000)
- `mouwasat-medical-services-company` FY2023: very low Latin word count (0 < 5000)
- `the-saudi-national-bank` FY2024: very low Latin word count (0 < 5000)
- `riyad-bank` FY2020: very low Latin word count (0 < 5000)
- `dubai-islamic-bank` FY2020: very low Latin word count (0 < 5000)
- `yanbu-national-petrochemical` FY2023: very low Latin word count (0 < 5000)
- `qatar-fuel-company-woqod` FY2024: very low Latin word count (0 < 5000)
- `gulf-hotels-group` FY2022: very low Latin word count (0 < 5000)
- `saudi-telecom-company` FY2022: very low Latin word count (0 < 5000)
- `industries-qatar` FY2025: very low Latin word count (0 < 5000)
- `bank-dhofar` FY2023: very low Latin word count (0 < 5000)
- `air-arabia-pjsc` FY2023: very low Latin word count (0 < 5000)
- `zain-mobile-telecommunications-company` FY2020: very low Latin word count (0 < 5000)
- `savola-group` FY2021: very low Latin word count (0 < 5000)
- `industries-qatar` FY2023: very low Latin word count (0 < 5000)
- `bank-dhofar` FY2024: very low Latin word count (0 < 5000)
- `gulf-international-services` FY2023: very low Latin word count (0 < 5000)
- `industries-qatar` FY2024: very low Latin word count (0 < 5000)
- `bank-muscat-bkmb` FY2023: very low Latin word count (0 < 5000)
- `gulf-international-services` FY2020: very low Latin word count (0 < 5000)
- `sahara-international-petrochemical-co` FY2022: very low Latin word count (0 < 5000)
- `dubai-investment` FY2024: very low Latin word count (0 < 5000)
- `the-saudi-national-bank` FY2023: very low Latin word count (0 < 5000)
- `industries-qatar` FY2021: very low Latin word count (0 < 5000)
- `gulf-hotels-group` FY2020: very low Latin word count (0 < 5000)
- `bank-albilad` FY2023: very low Latin word count (0 < 5000)
- `advanced-petrochemical` FY2020: very low Latin word count (0 < 5000)
- `mobile-telecommunications-co-saudi-arabia-zain` FY2024: very low Latin word count (0 < 5000)
- `oman-telecommunications-company-otel` FY2023: very low Latin word count (0 < 5000)
- `national-bank-of-kuwait` FY2022: very low Latin word count (0 < 5000)
- `ooredoo-q-p-s-c` FY2022: very low Latin word count (0 < 5000)
- `oman-international-development-and-investment-company` FY2020: very low Latin word count (0 < 5000)
- `qatar-gas-transport-co-nakilat` FY2021: very low Latin word count (0 < 5000)
- `ooredoo-q-p-s-c` FY2020: very low Latin word count (0 < 5000)
- `al-rajhi-bank` FY2025: very low Latin word count (0 < 5000)
- `aldar-properties-pjsc` FY2021: very low Latin word count (0 < 5000)
- `sahara-international-petrochemical-co` FY2020: very low Latin word count (0 < 5000)
- `rabigh-refining-petrochemical-co` FY2022: very low Latin word count (0 < 5000)
- `jarir-marketing-co` FY2021: very low Latin word count (0 < 5000)
- `qatar-fuel-company-woqod` FY2022: very low Latin word count (0 < 5000)
- `oman-telecommunications-company-otel` FY2024: very low Latin word count (0 < 5000)
- `mouwasat-medical-services-company` FY2025: very low Latin word count (0 < 5000)
- `saudi-telecom-company` FY2024: very low Latin word count (0 < 5000)
- `national-bank-of-kuwait` FY2023: very low Latin word count (0 < 5000)
- `industries-qatar` FY2022: very low Latin word count (0 < 5000)
- `rabigh-refining-petrochemical-co` FY2021: very low Latin word count (0 < 5000)
- `qatar-fuel-company-woqod` FY2021: very low Latin word count (0 < 5000)
- `national-bank-of-bahrain` FY2024: very low Latin word count (0 < 5000)
- `advanced-petrochemical` FY2025: very low Latin word count (0 < 5000)
- `saudi-airlines-catering-company-catrion` FY2023: very low Latin word count (0 < 5000)
- `tamdeen-real-estate-company` FY2021: very low Latin word count (0 < 5000)
- `bank-muscat-bkmb` FY2025: very low Latin word count (0 < 5000)
- `air-arabia-pjsc` FY2020: very low Latin word count (0 < 5000)
- `yanbu-cement-company` FY2021: very low Latin word count (0 < 5000)
- `sabic` FY2023: very low Latin word count (0 < 5000)
- `national-bank-of-kuwait` FY2024: very low Latin word count (0 < 5000)
- `ooredoo-q-p-s-c` FY2025: very low Latin word count (0 < 5000)
- `national-bank-of-bahrain` FY2023: very low Latin word count (0 < 5000)
- `oman-international-development-and-investment-company` FY2024: very low Latin word count (0 < 5000)
- `emaar-properties` FY2022: very low Latin word count (0 < 5000)
- `saudi-telecom-company` FY2023: very low Latin word count (0 < 5000)
- `oman-telecommunications-company-otel` FY2025: very low Latin word count (0 < 5000)
- `zain-mobile-telecommunications-company` FY2025: very low Latin word count (0 < 5000)
- `tamdeen-real-estate-company` FY2023: very low Latin word count (0 < 5000)
- `qnb-qatar-national-bank` FY2025: very low Latin word count (0 < 5000)
- `dar-al-arkan-real-estate-development-company` FY2022: very low Latin word count (0 < 5000)
- `qatar-fuel-company-woqod` FY2022: very low Latin word count (0 < 5000)
- `qnb-qatar-national-bank` FY2024: very low Latin word count (0 < 5000)
- `abu-dhabi-national-oil-company-for-distribution` FY2023: very low Latin word count (0 < 5000)
- `qatar-fuel-company-woqod` FY2020: very low Latin word count (0 < 5000)
- `national-bank-of-bahrain` FY2024: very low Latin word count (0 < 5000)
- `boubyan-bank` FY2022: very low Latin word count (0 < 5000)
- `zain-mobile-telecommunications-company` FY2021: very low Latin word count (0 < 5000)
- `tamdeen-real-estate-company` FY2025: very low Latin word count (0 < 5000)
- `tamdeen-real-estate-company` FY2024: very low Latin word count (0 < 5000)
- `qnb-qatar-national-bank` FY2023: very low Latin word count (0 < 5000)
- `dubai-investment` FY2021: very low Latin word count (0 < 5000)
- `abu-dhabi-national-energy-company` FY2021: very low Latin word count (0 < 5000)
- `the-national-bank-of-ras-al-khaimah` FY2020: very low Latin word count (0 < 5000)
- `national-bank-of-bahrain` FY2023: very low Latin word count (0 < 5000)
- `tamdeen-real-estate-company` FY2020: very low Latin word count (0 < 5000)
- `ooredoo-q-p-s-c` FY2025: very low Latin word count (0 < 5000)
- `dar-al-arkan-real-estate-development-company` FY2024: very low Latin word count (0 < 5000)
- `abu-dhabi-national-energy-company` FY2020: very low Latin word count (0 < 5000)
- `dar-al-arkan-real-estate-development-company` FY2021: very low Latin word count (0 < 5000)
- `abu-dhabi-national-oil-company-for-distribution` FY2020: very low Latin word count (0 < 5000)
- `the-national-bank-of-ras-al-khaimah` FY2022: very low Latin word count (0 < 5000)
- `ooredoo-q-p-s-c` FY2023: very low Latin word count (0 < 5000)
- `mobile-telecommunications-co-saudi-arabia-zain` FY2020: very low Latin word count (0 < 5000)
- `saudi-cement` FY2020: very low Latin word count (0 < 5000)
- `sahara-international-petrochemical-co` FY2023: very low Latin word count (0 < 5000)
- `baladna` FY2020: very low Latin word count (0 < 5000)
- `jazeera-steel` FY2024: very low Latin word count (0 < 5000)
- `boubyan-bank` FY2022: very low Latin word count (0 < 5000)
- `baladna` FY2021: very low Latin word count (0 < 5000)
- `al-rajhi-bank` FY2022: very low Latin word count (0 < 5000)
- `almarai` FY2020: very low Latin word count (0 < 5000)
- `al-rajhi-bank` FY2020: very low Latin word count (0 < 5000)
- `kuwait-finance-house` FY2022: very low Latin word count (0 < 5000)
- `abu-dhabi-national-oil-company-for-distribution` FY2020: very low Latin word count (0 < 5000)
- `abu-dhabi-national-energy-company` FY2021: very low Latin word count (0 < 5000)
- `alinma-bank` FY2023: very low Latin word count (0 < 5000)
- `mouwasat-medical-services-company` FY2023: very low Latin word count (0 < 5000)
- `etihad-etisalat-mobily` FY2025: very low Latin word count (0 < 5000)
- `etihad-etisalat-mobily` FY2023: very low Latin word count (0 < 5000)
- `bahrain-telecommunications-beyon` FY2023: very low Latin word count (0 < 5000)
- `abu-dhabi-national-energy-company` FY2020: very low Latin word count (0 < 5000)
- `gulf-hotels-group` FY2022: very low Latin word count (0 < 5000)
- `aluminium-bahrain-alba` FY2020: very low Latin word count (0 < 5000)
- `salam-international-investment` FY2020: very low Latin word count (0 < 5000)
- `emirates-telecom-etisalat-group` FY2024: very low Latin word count (0 < 5000)
- `first-abu-dhabi-bank` FY2023: very low Latin word count (0 < 5000)
- `abu-dhabi-national-energy-company` FY2025: very low Latin word count (0 < 5000)
- `bahrain-telecommunications-beyon` FY2021: very low Latin word count (0 < 5000)
- `sahara-international-petrochemical-co` FY2022: very low Latin word count (0 < 5000)
- `kuwait-telecommunications-company` FY2025: very low Latin word count (0 < 5000)
- `sabic` FY2025: very low Latin word count (0 < 5000)
- `first-abu-dhabi-bank` FY2020: very low Latin word count (0 < 5000)
- `industries-qatar` FY2020: very low Latin word count (0 < 5000)
- `emirates-nbd-pjsc` FY2021: very low Latin word count (0 < 5000)
- `bank-albilad` FY2023: very low Latin word count (0 < 5000)
- `bahrain-telecommunications-beyon` FY2020: very low Latin word count (0 < 5000)
- `almarai` FY2022: very low Latin word count (0 < 5000)
- `air-arabia-pjsc` FY2022: very low Latin word count (0 < 5000)
- `gulf-international-services` FY2023: very low Latin word count (0 < 5000)
- `etihad-etisalat-mobily` FY2020: very low Latin word count (0 < 5000)
- `saudi-airlines-catering-company-catrion` FY2022: very low Latin word count (0 < 5000)
- `mouwasat-medical-services-company` FY2025: very low Latin word count (0 < 5000)
- `mobile-telecommunications-co-saudi-arabia-zain` FY2025: very low Latin word count (0 < 5000)
- `alinma-bank` FY2025: very low Latin word count (0 < 5000)
- `abu-dhabi-commercial-bank` FY2025: very low Latin word count (0 < 5000)
- `air-arabia-pjsc` FY2020: very low Latin word count (0 < 5000)
- `saudi-cement` FY2022: very low Latin word count (0 < 5000)
- `kuwait-finance-house` FY2021: very low Latin word count (0 < 5000)
- `al-rajhi-bank` FY2023: very low Latin word count (0 < 5000)
- `al-rajhi-bank` FY2021: very low Latin word count (0 < 5000)
- `national-bank-of-bahrain` FY2021: very low Latin word count (0 < 5000)
- `gulf-hotels-group` FY2025: very low Latin word count (0 < 5000)
- `etihad-etisalat-mobily` FY2021: very low Latin word count (0 < 5000)
- `emirates-nbd-pjsc` FY2025: very low Latin word count (0 < 5000)
- `abu-dhabi-commercial-bank` FY2024: very low Latin word count (0 < 5000)
- `salam-international-investment` FY2022: very low Latin word count (0 < 5000)
- `emirates-telecom-etisalat-group` FY2022: very low Latin word count (0 < 5000)
- `alinma-bank` FY2024: very low Latin word count (0 < 5000)
- `air-arabia-pjsc` FY2023: very low Latin word count (0 < 5000)
- `baladna` FY2022: very low Latin word count (0 < 5000)
- `aldar-properties-pjsc` FY2025: very low Latin word count (0 < 5000)
- `maaden` FY2021: very low Latin word count (0 < 5000)
- `emirates-telecom-etisalat-group` FY2023: very low Latin word count (0 < 5000)
- `salam-international-investment` FY2021: very low Latin word count (0 < 5000)
- `aluminium-bahrain-alba` FY2023: very low Latin word count (0 < 5000)
- `maaden` FY2020: very low Latin word count (0 < 5000)
- `bank-albilad` FY2020: very low Latin word count (0 < 5000)
- `aluminium-bahrain-alba` FY2021: very low Latin word count (0 < 5000)
- `advanced-petrochemical` FY2023: very low Latin word count (0 < 5000)
- `saudi-aramco` FY2023: very low Latin word count (0 < 5000)
- `kuwait-finance-house` FY2025: very low Latin word count (0 < 5000)
- `abdullah-al-othaim-markets` FY2025: very low Latin word count (0 < 5000)
- `alinma-bank` FY2021: very low Latin word count (0 < 5000)
- `almarai` FY2023: very low Latin word count (0 < 5000)
- `emaar-properties` FY2025: very low Latin word count (0 < 5000)
- `air-arabia-pjsc` FY2024: very low Latin word count (0 < 5000)
- `national-bank-of-bahrain` FY2022: very low Latin word count (0 < 5000)
- `abu-dhabi-commercial-bank` FY2021: very low Latin word count (0 < 5000)
- `kuwait-finance-house` FY2023: very low Latin word count (0 < 5000)
- `aldar-properties-pjsc` FY2022: very low Latin word count (0 < 5000)
- `sahara-international-petrochemical-co` FY2024: very low Latin word count (0 < 5000)
- `emaar-properties` FY2023: very low Latin word count (0 < 5000)
- `maaden` FY2022: very low Latin word count (0 < 5000)
- `gulf-hotels-group` FY2021: very low Latin word count (0 < 5000)
- `abu-dhabi-commercial-bank` FY2020: very low Latin word count (0 < 5000)
- `saudi-aramco` FY2024: very low Latin word count (0 < 5000)
- `emirates-telecom-etisalat-group` FY2020: very low Latin word count (0 < 5000)
- `salam-international-investment` FY2025: very low Latin word count (0 < 5000)
- `first-abu-dhabi-bank` FY2024: very low Latin word count (0 < 5000)
- `aldar-properties-pjsc` FY2021: very low Latin word count (0 < 5000)
- `baladna` FY2024: very low Latin word count (0 < 5000)
- `emirates-telecom-etisalat-group` FY2025: very low Latin word count (0 < 5000)
- `emirates-telecom-etisalat-group` FY2021: very low Latin word count (0 < 5000)
- `aldar-properties-pjsc` FY2020: very low Latin word count (0 < 5000)
- `etihad-etisalat-mobily` FY2022: very low Latin word count (0 < 5000)
- `emaar-properties` FY2024: very low Latin word count (0 < 5000)
- `bank-dhofar` FY2020: very low Latin word count (0 < 5000)
- `aluminium-bahrain-alba` FY2022: very low Latin word count (0 < 5000)
- `national-bank-of-kuwait` FY2020: very low Latin word count (0 < 5000)
- `saudi-industrial-investment-group` FY2020: very low Latin word count (0 < 5000)
- `mobile-telecommunications-co-saudi-arabia-zain` FY2022: very low Latin word count (0 < 5000)
- `mouwasat-medical-services-company` FY2024: very low Latin word count (0 < 5000)
- `kuwait-finance-house` FY2024: very low Latin word count (0 < 5000)
- `gulf-hotels-group` FY2024: very low Latin word count (0 < 5000)
- `maaden` FY2024: very low Latin word count (0 < 5000)
- `bahrain-telecommunications-beyon` FY2022: very low Latin word count (0 < 5000)
- `aluminium-bahrain-alba` FY2024: very low Latin word count (0 < 5000)
- `kuwait-telecommunications-company` FY2022: very low Latin word count (0 < 5000)
- `industries-qatar` FY2021: very low Latin word count (0 < 5000)
- `bahrain-telecommunications-beyon` FY2025: very low Latin word count (0 < 5000)
- `maaden` FY2023: very low Latin word count (0 < 5000)
- `kuwait-telecommunications-company` FY2020: very low Latin word count (0 < 5000)
- `gulf-hotels-group` FY2020: very low Latin word count (0 < 5000)
- `mobile-telecommunications-co-saudi-arabia-zain` FY2024: very low Latin word count (0 < 5000)
- `almarai` FY2025: very low Latin word count (0 < 5000)
- `maaden` FY2025: very low Latin word count (0 < 5000)
- `alinma-bank` FY2020: very low Latin word count (0 < 5000)
- `mobile-telecommunications-co-saudi-arabia-zain` FY2023: very low Latin word count (0 < 5000)
- `first-abu-dhabi-bank` FY2022: very low Latin word count (0 < 5000)
- `kuwait-telecommunications-company` FY2021: very low Latin word count (0 < 5000)
- `gulf-international-services` FY2021: very low Latin word count (0 < 5000)
- `mouwasat-medical-services-company` FY2022: very low Latin word count (0 < 5000)
- `first-abu-dhabi-bank` FY2021: very low Latin word count (0 < 5000)
- `gulf-international-services` FY2024: very low Latin word count (0 < 5000)
- `etihad-etisalat-mobily` FY2024: very low Latin word count (0 < 5000)
- `baladna` FY2023: very low Latin word count (0 < 5000)
- `emirates-nbd-pjsc` FY2024: very low Latin word count (0 < 5000)
- `aluminium-bahrain-alba` FY2025: very low Latin word count (0 < 5000)
- `saudi-aramco` FY2025: very low Latin word count (0 < 5000)
- `salam-international-investment` FY2024: very low Latin word count (0 < 5000)
- `industries-qatar` FY2022: very low Latin word count (0 < 5000)
- `mouwasat-medical-services-company` FY2020: very low Latin word count (0 < 5000)
- `gulf-hotels-group` FY2023: very low Latin word count (0 < 5000)
- `almarai` FY2024: very low Latin word count (0 < 5000)
- `kuwait-telecommunications-company` FY2024: very low Latin word count (0 < 5000)
- `aldar-properties-pjsc` FY2024: very low Latin word count (0 < 5000)
- `advanced-petrochemical` FY2025: very low Latin word count (0 < 5000)
- `sabic` FY2023: very low Latin word count (0 < 5000)
- `mobile-telecommunications-co-saudi-arabia-zain` FY2021: very low Latin word count (0 < 5000)
- `kuwait-telecommunications-company` FY2023: very low Latin word count (0 < 5000)
- `baladna` FY2025: very low Latin word count (0 < 5000)
- `al-rajhi-bank` FY2025: very low Latin word count (0 < 5000)
- `sahara-international-petrochemical-co` FY2025: very low Latin word count (0 < 5000)
- `almarai` FY2021: very low Latin word count (0 < 5000)
- `first-abu-dhabi-bank` FY2025: very low Latin word count (0 < 5000)
- `al-rajhi-bank` FY2024: very low Latin word count (0 < 5000)
- `sabic` FY2024: very low Latin word count (0 < 5000)
- `kuwait-finance-house` FY2020: very low Latin word count (0 < 5000)
- `jazeera-steel` FY2023: very low Latin word count (0 < 5000)
- `saudi-airlines-catering-company-catrion` FY2021: very low Latin word count (0 < 5000)
- `sahara-international-petrochemical-co` FY2021: very low Latin word count (0 < 5000)
- `bank-albilad` FY2022: very low Latin word count (0 < 5000)
- `abu-dhabi-national-energy-company` FY2022: very low Latin word count (0 < 5000)
- `jarir-marketing-co` FY2020: very low Latin word count (0 < 5000)
- `gulf-international-services` FY2020: very low Latin word count (0 < 5000)
- `bahrain-telecommunications-beyon` FY2024: very low Latin word count (0 < 5000)
- `abdullah-al-othaim-markets` FY2020: very low Latin word count (0 < 5000)
- `advanced-petrochemical` FY2022: very low Latin word count (0 < 5000)
- `aldar-properties-pjsc` FY2023: very low Latin word count (0 < 5000)
- `alinma-bank` FY2022: very low Latin word count (0 < 5000)
- `mouwasat-medical-services-company` FY2021: very low Latin word count (0 < 5000)
- `air-arabia-pjsc` FY2021: very low Latin word count (0 < 5000)
- `national-bank-of-bahrain` FY2020: very low Latin word count (0 < 5000)
- `advanced-petrochemical` FY2024: very low Latin word count (0 < 5000)
- `salam-international-investment` FY2023: very low Latin word count (0 < 5000)
- `emirates-nbd-pjsc` FY2023: very low Latin word count (0 < 5000)
- `saudi-arabian-fertilizer-company` FY2020: very low Latin word count (0 < 5000)
- `jazeera-steel` FY2022: very low Latin word count (0 < 5000)
- `abu-dhabi-national-energy-company` FY2024: very low Latin word count (0 < 5000)
- `emirates-nbd-pjsc` FY2022: very low Latin word count (0 < 5000)
- `bank-albilad` FY2021: very low Latin word count (0 < 5000)
- `gulf-international-services` FY2025: very low Latin word count (0 < 5000)
- `air-arabia-pjsc` FY2025: very low Latin word count (0 < 5000)
- `saudi-airlines-catering-company-catrion` FY2020: very low Latin word count (0 < 5000)
- `gulf-international-services` FY2022: very low Latin word count (0 < 5000)
- `abu-dhabi-national-energy-company` FY2023: very low Latin word count (0 < 5000)
- `tamdeen-real-estate-company` FY2023: very low Latin word count (0 < 5000)
- `qnb-qatar-national-bank` FY2025: very low Latin word count (0 < 5000)
- `dar-al-arkan-real-estate-development-company` FY2022: very low Latin word count (0 < 5000)
- `qatar-fuel-company-woqod` FY2022: very low Latin word count (0 < 5000)
- `national-bank-of-bahrain` FY2024: very low Latin word count (0 < 5000)
- `dar-al-arkan-real-estate-development-company` FY2020: very low Latin word count (0 < 5000)
- `abu-dhabi-national-oil-company-for-distribution` FY2023: very low Latin word count (0 < 5000)
- `tamdeen-real-estate-company` FY2024: very low Latin word count (0 < 5000)
- `qatar-fuel-company-woqod` FY2020: very low Latin word count (0 < 5000)
- `tamdeen-real-estate-company` FY2025: very low Latin word count (0 < 5000)
- `saudi-cement` FY2021: very low Latin word count (0 < 5000)
- `qnb-qatar-national-bank` FY2023: very low Latin word count (0 < 5000)
- `national-bank-of-bahrain` FY2023: very low Latin word count (0 < 5000)
- `saudi-arabian-fertilizer-company` FY2024: very low Latin word count (0 < 5000)
- `rabigh-refining-petrochemical-co` FY2020: very low Latin word count (0 < 5000)
- `tamdeen-real-estate-company` FY2020: very low Latin word count (0 < 5000)
- `ooredoo-q-p-s-c` FY2025: very low Latin word count (0 < 5000)
- `dubai-investment` FY2021: very low Latin word count (0 < 5000)
- `the-national-bank-of-ras-al-khaimah` FY2020: very low Latin word count (0 < 5000)
- `national-bank-of-bahrain` FY2025: very low Latin word count (0 < 5000)
- `ooredoo-q-p-s-c` FY2023: very low Latin word count (0 < 5000)
- `boubyan-bank` FY2025: very low Latin word count (0 < 5000)
- `rabigh-refining-petrochemical-co` FY2022: very low Latin word count (0 < 5000)
- `dar-al-arkan-real-estate-development-company` FY2024: very low Latin word count (0 < 5000)
- `sohar-international-bank` FY2022: very low Latin word count (0 < 5000)
- `ooredoo-q-p-s-c` FY2024: very low Latin word count (0 < 5000)
- `dar-al-arkan-real-estate-development-company` FY2021: very low Latin word count (0 < 5000)
- `the-saudi-national-bank` FY2021: very low Latin word count (0 < 5000)
- `dar-al-arkan-real-estate-development-company` FY2025: very low Latin word count (0 < 5000)
- `sohar-international-bank` FY2020: very low Latin word count (0 < 5000)
- `zain-mobile-telecommunications-company` FY2024: very low Latin word count (0 < 5000)
- `the-national-bank-of-ras-al-khaimah` FY2022: very low Latin word count (0 < 5000)
- `qnb-qatar-national-bank` FY2022: very low Latin word count (0 < 5000)
- `national-industrialization-co` FY2025: very low Latin word count (0 < 5000)
- `dar-al-arkan-real-estate-development-company` FY2023: very low Latin word count (0 < 5000)
- `the-national-bank-of-ras-al-khaimah` FY2021: very low Latin word count (0 < 5000)
- `riyad-bank` FY2021: very low Latin word count (0 < 5000)
- `boubyan-bank` FY2023: very low Latin word count (0 < 5000)
- `savola-group` FY2025: very low Latin word count (0 < 5000)
- `dubai-investment` FY2022: very low Latin word count (0 < 5000)
- `boubyan-bank` FY2020: very low Latin word count (0 < 5000)
- `savola-group` FY2023: very low Latin word count (0 < 5000)
- `rabigh-refining-petrochemical-co` FY2024: very low Latin word count (0 < 5000)
- `national-industrialization-co` FY2023: very low Latin word count (0 < 5000)
- `rabigh-refining-petrochemical-co` FY2021: very low Latin word count (0 < 5000)
- `savola-group` FY2024: very low Latin word count (0 < 5000)
- `dubai-investment` FY2020: very low Latin word count (0 < 5000)
- `the-national-bank-of-ras-al-khaimah` FY2025: very low Latin word count (0 < 5000)
- `abdullah-al-othaim-markets` FY2024: very low Latin word count (0 < 5000)
- `dubai-islamic-bank` FY2021: very low Latin word count (0 < 5000)
- `barwa-real-estate` FY2025: very low Latin word count (0 < 5000)
- `advanced-petrochemical` FY2021: very low Latin word count (0 < 5000)
- `the-saudi-national-bank` FY2020: very low Latin word count (0 < 5000)
- `saudi-airlines-catering-company-catrion` FY2023: very low Latin word count (0 < 5000)
- `sahara-international-petrochemical-co` FY2020: very low Latin word count (0 < 5000)
- `tamdeen-real-estate-company` FY2022: very low Latin word count (0 < 5000)
- `oman-international-development-and-investment-company` FY2022: very low Latin word count (0 < 5000)
- `barwa-real-estate` FY2023: very low Latin word count (0 < 5000)
- `the-national-bank-of-ras-al-khaimah` FY2023: very low Latin word count (0 < 5000)
- `oman-international-development-and-investment-company` FY2020: very low Latin word count (0 < 5000)
- `barwa-real-estate` FY2024: very low Latin word count (0 < 5000)
- `saudi-aramco` FY2020: very low Latin word count (0 < 5000)
- `the-saudi-national-bank` FY2022: very low Latin word count (0 < 5000)
- `saudi-arabian-fertilizer-company` FY2021: very low Latin word count (0 < 5000)
- `oman-international-development-and-investment-company` FY2021: very low Latin word count (0 < 5000)
- `saudi-arabian-fertilizer-company` FY2022: very low Latin word count (0 < 5000)
- `abdullah-al-othaim-markets` FY2023: very low Latin word count (0 < 5000)
- `national-industrialization-co` FY2024: very low Latin word count (0 < 5000)
- `sohar-international-bank` FY2021: very low Latin word count (0 < 5000)
- `yanbu-cement-company` FY2021: very low Latin word count (0 < 5000)
- `qnb-qatar-national-bank` FY2024: very low Latin word count (0 < 5000)
- `sabic` FY2022: very low Latin word count (0 < 5000)
- `advanced-petrochemical` FY2020: very low Latin word count (0 < 5000)
- `zain-mobile-telecommunications-company` FY2023: very low Latin word count (0 < 5000)
- `savola-group` FY2022: very low Latin word count (0 < 5000)
- `oman-international-development-and-investment-company` FY2024: very low Latin word count (0 < 5000)
- `savola-group` FY2020: very low Latin word count (0 < 5000)
- `sabic` FY2020: very low Latin word count (0 < 5000)
- `dubai-islamic-bank` FY2022: very low Latin word count (0 < 5000)
- `zain-mobile-telecommunications-company` FY2022: very low Latin word count (0 < 5000)
- `oman-international-development-and-investment-company` FY2023: very low Latin word count (0 < 5000)
- `bank-muscat-bkmb` FY2024: very low Latin word count (0 < 5000)
- `abu-dhabi-national-oil-company-for-distribution` FY2024: very low Latin word count (0 < 5000)
- `oman-international-development-and-investment-company` FY2025: very low Latin word count (0 < 5000)
- `abu-dhabi-commercial-bank` FY2022: very low Latin word count (0 < 5000)
- `saudi-cement` FY2025: very low Latin word count (0 < 5000)
- `national-industrialization-co` FY2020: very low Latin word count (0 < 5000)
- `emaar-properties` FY2021: very low Latin word count (0 < 5000)
- `jazeera-steel` FY2025: very low Latin word count (0 < 5000)
- `saudi-cement` FY2023: very low Latin word count (0 < 5000)
- `bank-muscat-bkmb` FY2025: very low Latin word count (0 < 5000)
- `abu-dhabi-commercial-bank` FY2023: very low Latin word count (0 < 5000)
- `saudi-arabian-fertilizer-company` FY2023: very low Latin word count (0 < 5000)
- `zain-mobile-telecommunications-company` FY2021: very low Latin word count (0 < 5000)
- `yanbu-national-petrochemical` FY2020: very low Latin word count (0 < 5000)
- `jazeera-steel` FY2020: very low Latin word count (0 < 5000)
- `dubai-islamic-bank` FY2023: very low Latin word count (0 < 5000)
- `oman-telecommunications-company-otel` FY2020: very low Latin word count (0 < 5000)
- `saudi-cement` FY2024: very low Latin word count (0 < 5000)
- `riyad-bank` FY2025: very low Latin word count (0 < 5000)
- `emirates-nbd-pjsc` FY2020: very low Latin word count (0 < 5000)
- `saudi-industrial-investment-group` FY2021: very low Latin word count (0 < 5000)
- `national-industrialization-co` FY2022: very low Latin word count (0 < 5000)
- `saudi-industrial-investment-group` FY2022: very low Latin word count (0 < 5000)
- `jazeera-airways` FY2025: very low Latin word count (0 < 5000)
- `bank-muscat-bkmb` FY2023: very low Latin word count (0 < 5000)
- `national-bank-of-kuwait` FY2023: very low Latin word count (0 < 5000)
- `zain-mobile-telecommunications-company` FY2020: very low Latin word count (0 < 5000)
- `jazeera-airways` FY2023: very low Latin word count (0 < 5000)
- `bank-dhofar` FY2021: very low Latin word count (0 < 5000)
- `abu-dhabi-national-oil-company-for-distribution` FY2025: very low Latin word count (0 < 5000)
- `riyad-bank` FY2024: very low Latin word count (0 < 5000)
- `bank-albilad` FY2025: very low Latin word count (0 < 5000)
- `jazeera-airways` FY2024: very low Latin word count (0 < 5000)
- `yanbu-cement-company` FY2025: very low Latin word count (0 < 5000)
- `riyad-bank` FY2023: very low Latin word count (0 < 5000)
- `bank-dhofar` FY2022: very low Latin word count (0 < 5000)
- `boubyan-bank` FY2024: very low Latin word count (0 < 5000)
- `saudi-telecom-company` FY2021: very low Latin word count (0 < 5000)
- `yanbu-cement-company` FY2023: very low Latin word count (0 < 5000)
- `oman-telecommunications-company-otel` FY2021: very low Latin word count (0 < 5000)
- `ooredoo-q-p-s-c` FY2021: very low Latin word count (0 < 5000)
- `yanbu-cement-company` FY2024: very low Latin word count (0 < 5000)
- `national-bank-of-kuwait` FY2024: very low Latin word count (0 < 5000)
- `boubyan-bank` FY2021: very low Latin word count (0 < 5000)
- `riyad-bank` FY2022: very low Latin word count (0 < 5000)
- `qnb-qatar-national-bank` FY2020: very low Latin word count (0 < 5000)
- `jazeera-steel` FY2021: very low Latin word count (0 < 5000)
- `barwa-real-estate` FY2020: very low Latin word count (0 < 5000)
- `emaar-properties` FY2022: very low Latin word count (0 < 5000)
- `the-national-bank-of-ras-al-khaimah` FY2024: very low Latin word count (0 < 5000)
- `saudi-industrial-investment-group` FY2024: very low Latin word count (0 < 5000)
- `saudi-aramco` FY2022: very low Latin word count (0 < 5000)
- `jazeera-airways` FY2022: very low Latin word count (0 < 5000)
- `qatar-gas-transport-co-nakilat` FY2025: very low Latin word count (0 < 5000)
- `jazeera-airways` FY2020: very low Latin word count (0 < 5000)
- `bank-dhofar` FY2024: very low Latin word count (0 < 5000)
- `abdullah-al-othaim-markets` FY2022: very low Latin word count (0 < 5000)
- `qatar-gas-transport-co-nakilat` FY2023: very low Latin word count (0 < 5000)
- `dubai-islamic-bank` FY2025: very low Latin word count (0 < 5000)
- `qatar-gas-transport-co-nakilat` FY2024: very low Latin word count (0 < 5000)
- `saudi-industrial-investment-group` FY2023: very low Latin word count (0 < 5000)
- `yanbu-national-petrochemical` FY2025: very low Latin word count (0 < 5000)
- `saudi-industrial-investment-group` FY2025: very low Latin word count (0 < 5000)
- `jarir-marketing-co` FY2025: very low Latin word count (0 < 5000)
- `yanbu-national-petrochemical` FY2021: very low Latin word count (0 < 5000)
- `emaar-properties` FY2020: very low Latin word count (0 < 5000)
- `jarir-marketing-co` FY2023: very low Latin word count (0 < 5000)
- `jarir-marketing-co` FY2024: very low Latin word count (0 < 5000)
- `saudi-telecom-company` FY2020: very low Latin word count (0 < 5000)
- `saudi-airlines-catering-company-catrion` FY2024: very low Latin word count (0 < 5000)
- `abdullah-al-othaim-markets` FY2021: very low Latin word count (0 < 5000)
- `saudi-airlines-catering-company-catrion` FY2025: very low Latin word count (0 < 5000)
- `oman-telecommunications-company-otel` FY2024: very low Latin word count (0 < 5000)
- `saudi-aramco` FY2021: very low Latin word count (0 < 5000)
- `sabic` FY2021: very low Latin word count (0 < 5000)
- `qnb-qatar-national-bank` FY2021: very low Latin word count (0 < 5000)
- `bank-muscat-bkmb` FY2022: very low Latin word count (0 < 5000)
- `saudi-telecom-company` FY2022: very low Latin word count (0 < 5000)
- `bank-muscat-bkmb` FY2021: very low Latin word count (0 < 5000)
- `savola-group` FY2021: very low Latin word count (0 < 5000)
- `abu-dhabi-national-oil-company-for-distribution` FY2022: very low Latin word count (0 < 5000)
- `qatar-gas-transport-co-nakilat` FY2022: very low Latin word count (0 < 5000)
- `national-bank-of-kuwait` FY2021: very low Latin word count (0 < 5000)
- `bank-dhofar` FY2025: very low Latin word count (0 < 5000)
- `jazeera-airways` FY2021: very low Latin word count (0 < 5000)
- `qatar-gas-transport-co-nakilat` FY2020: very low Latin word count (0 < 5000)
- `oman-telecommunications-company-otel` FY2023: very low Latin word count (0 < 5000)
- `national-bank-of-kuwait` FY2025: very low Latin word count (0 < 5000)
- `yanbu-cement-company` FY2020: very low Latin word count (0 < 5000)
- `oman-telecommunications-company-otel` FY2025: very low Latin word count (0 < 5000)
- `bank-muscat-bkmb` FY2020: very low Latin word count (0 < 5000)
- `dubai-islamic-bank` FY2024: very low Latin word count (0 < 5000)
- `yanbu-cement-company` FY2022: very low Latin word count (0 < 5000)
- `jarir-marketing-co` FY2022: very low Latin word count (0 < 5000)
- `abu-dhabi-national-oil-company-for-distribution` FY2021: very low Latin word count (0 < 5000)
- `qatar-fuel-company-woqod` FY2025: very low Latin word count (0 < 5000)
- `jarir-marketing-co` FY2021: very low Latin word count (0 < 5000)
- `dubai-investment` FY2023: very low Latin word count (0 < 5000)
- `dubai-islamic-bank` FY2020: very low Latin word count (0 < 5000)
- `qatar-fuel-company-woqod` FY2023: very low Latin word count (0 < 5000)
- `riyad-bank` FY2020: very low Latin word count (0 < 5000)
- `qatar-fuel-company-woqod` FY2024: very low Latin word count (0 < 5000)
- `ooredoo-q-p-s-c` FY2020: very low Latin word count (0 < 5000)
- `yanbu-national-petrochemical` FY2023: very low Latin word count (0 < 5000)
- `the-saudi-national-bank` FY2025: very low Latin word count (0 < 5000)
- `industries-qatar` FY2025: very low Latin word count (0 < 5000)
- `tamdeen-real-estate-company` FY2021: very low Latin word count (0 < 5000)
- `national-industrialization-co` FY2021: very low Latin word count (0 < 5000)
- `industries-qatar` FY2023: very low Latin word count (0 < 5000)
- `dubai-investment` FY2024: very low Latin word count (0 < 5000)
- `yanbu-national-petrochemical` FY2022: very low Latin word count (0 < 5000)
- `oman-telecommunications-company-otel` FY2022: very low Latin word count (0 < 5000)
- `yanbu-national-petrochemical` FY2024: very low Latin word count (0 < 5000)
- `saudi-telecom-company` FY2024: very low Latin word count (0 < 5000)
- `rabigh-refining-petrochemical-co` FY2025: very low Latin word count (0 < 5000)
- `sohar-international-bank` FY2025: very low Latin word count (0 < 5000)
- `saudi-telecom-company` FY2023: very low Latin word count (0 < 5000)
- `ooredoo-q-p-s-c` FY2022: very low Latin word count (0 < 5000)
- `national-bank-of-kuwait` FY2022: very low Latin word count (0 < 5000)
- `qatar-fuel-company-woqod` FY2021: very low Latin word count (0 < 5000)
- `bank-dhofar` FY2023: very low Latin word count (0 < 5000)
- `sohar-international-bank` FY2023: very low Latin word count (0 < 5000)
- `the-saudi-national-bank` FY2023: very low Latin word count (0 < 5000)
- `the-saudi-national-bank` FY2024: very low Latin word count (0 < 5000)
- `bank-albilad` FY2024: very low Latin word count (0 < 5000)
- `sohar-international-bank` FY2024: very low Latin word count (0 < 5000)
- `barwa-real-estate` FY2022: very low Latin word count (0 < 5000)
- `qatar-gas-transport-co-nakilat` FY2021: very low Latin word count (0 < 5000)
- `industries-qatar` FY2024: very low Latin word count (0 < 5000)
- `dubai-investment` FY2025: very low Latin word count (0 < 5000)
- `saudi-telecom-company` FY2025: very low Latin word count (0 < 5000)
- `barwa-real-estate` FY2021: very low Latin word count (0 < 5000)
- `saudi-arabian-fertilizer-company` FY2025: very low Latin word count (0 < 5000)
- `rabigh-refining-petrochemical-co` FY2023: very low Latin word count (0 < 5000)
- `zain-mobile-telecommunications-company` FY2025: very low Latin word count (0 < 5000)
- `al-rajhi-bank` FY2020: very low Latin word count (0 < 5000)
- `al-rajhi-bank` FY2021: very low Latin word count (0 < 5000)
- `al-rajhi-bank` FY2022: very low Latin word count (0 < 5000)
- `al-rajhi-bank` FY2023: very low Latin word count (0 < 5000)
- `al-rajhi-bank` FY2024: very low Latin word count (0 < 5000)
- `al-rajhi-bank` FY2025: very low Latin word count (0 < 5000)
- `air-arabia-pjsc` FY2023: very low Latin word count (0 < 5000); high OCR ratio (60% > 30%)
- `advanced-petrochemical` FY2022: very low Latin word count (0 < 5000); high OCR ratio (100% > 30%)
- `air-arabia-pjsc` FY2024: very low Latin word count (0 < 5000); high OCR ratio (60% > 30%)
- `dubai-islamic-bank` FY2021: very low Latin word count (0 < 5000); high OCR ratio (48% > 30%)
- `kuwait-telecommunications-company` FY2020: very low Latin word count (0 < 5000); high OCR ratio (42% > 30%)
- `sahara-international-petrochemical-co` FY2022: very low Latin word count (4214 < 5000)
- `salam-international-investment` FY2020: very low Latin word count (4044 < 5000)
- `salam-international-investment` FY2021: very low Latin word count (3645 < 5000)
- `kuwait-telecommunications-company` FY2020: high OCR ratio (42% > 30%)
- `air-arabia-pjsc` FY2024: high OCR ratio (60% > 30%)
- `air-arabia-pjsc` FY2023: high OCR ratio (60% > 30%)
- `dubai-islamic-bank` FY2021: high OCR ratio (48% > 30%)

## IQR outliers

_(none)_

## Pipeline-flagged needs_review (non-IQR)

- `abdullah-al-othaim-markets` FY2020: very low Latin word count (0 < 5000)
- `abdullah-al-othaim-markets` FY2020: very low Latin word count (0 < 5000)
- `abdullah-al-othaim-markets` FY2021: very low Latin word count (0 < 5000)
- `abdullah-al-othaim-markets` FY2021: very low Latin word count (0 < 5000)
- `abdullah-al-othaim-markets` FY2022: very low Latin word count (0 < 5000)
- `abdullah-al-othaim-markets` FY2022: very low Latin word count (0 < 5000)
- `abdullah-al-othaim-markets` FY2023: very low Latin word count (0 < 5000)
- `abdullah-al-othaim-markets` FY2023: very low Latin word count (0 < 5000)
- `abdullah-al-othaim-markets` FY2024: very low Latin word count (0 < 5000)
- `abdullah-al-othaim-markets` FY2024: very low Latin word count (0 < 5000)
- `abdullah-al-othaim-markets` FY2025: very low Latin word count (0 < 5000)
- `abdullah-al-othaim-markets` FY2025: very low Latin word count (0 < 5000)
- `abu-dhabi-commercial-bank` FY2020: very low Latin word count (0 < 5000)
- `abu-dhabi-commercial-bank` FY2020: very low Latin word count (0 < 5000)
- `abu-dhabi-commercial-bank` FY2021: very low Latin word count (0 < 5000)
- `abu-dhabi-commercial-bank` FY2021: very low Latin word count (0 < 5000)
- `abu-dhabi-commercial-bank` FY2022: very low Latin word count (0 < 5000)
- `abu-dhabi-commercial-bank` FY2022: very low Latin word count (0 < 5000)
- `abu-dhabi-commercial-bank` FY2023: very low Latin word count (0 < 5000)
- `abu-dhabi-commercial-bank` FY2023: very low Latin word count (0 < 5000)
- `abu-dhabi-commercial-bank` FY2024: very low Latin word count (0 < 5000)
- `abu-dhabi-commercial-bank` FY2024: very low Latin word count (0 < 5000)
- `abu-dhabi-commercial-bank` FY2025: very low Latin word count (0 < 5000)
- `abu-dhabi-commercial-bank` FY2025: very low Latin word count (0 < 5000)
- `abu-dhabi-national-energy-company` FY2020: very low Latin word count (0 < 5000)
- `abu-dhabi-national-energy-company` FY2020: very low Latin word count (0 < 5000)
- `abu-dhabi-national-energy-company` FY2020: very low Latin word count (0 < 5000)
- `abu-dhabi-national-energy-company` FY2021: very low Latin word count (0 < 5000)
- `abu-dhabi-national-energy-company` FY2021: very low Latin word count (0 < 5000)
- `abu-dhabi-national-energy-company` FY2021: very low Latin word count (0 < 5000)
- `abu-dhabi-national-energy-company` FY2022: very low Latin word count (0 < 5000)
- `abu-dhabi-national-energy-company` FY2022: very low Latin word count (0 < 5000)
- `abu-dhabi-national-energy-company` FY2023: very low Latin word count (0 < 5000)
- `abu-dhabi-national-energy-company` FY2023: very low Latin word count (0 < 5000)
- `abu-dhabi-national-energy-company` FY2024: very low Latin word count (0 < 5000)
- `abu-dhabi-national-energy-company` FY2024: very low Latin word count (0 < 5000)
- `abu-dhabi-national-energy-company` FY2025: very low Latin word count (0 < 5000)
- `abu-dhabi-national-energy-company` FY2025: very low Latin word count (0 < 5000)
- `abu-dhabi-national-oil-company-for-distribution` FY2020: very low Latin word count (0 < 5000)
- `abu-dhabi-national-oil-company-for-distribution` FY2020: very low Latin word count (0 < 5000)
- `abu-dhabi-national-oil-company-for-distribution` FY2020: very low Latin word count (0 < 5000)
- `abu-dhabi-national-oil-company-for-distribution` FY2021: very low Latin word count (0 < 5000)
- `abu-dhabi-national-oil-company-for-distribution` FY2021: very low Latin word count (0 < 5000)
- `abu-dhabi-national-oil-company-for-distribution` FY2022: very low Latin word count (0 < 5000)
- `abu-dhabi-national-oil-company-for-distribution` FY2022: very low Latin word count (0 < 5000)
- `abu-dhabi-national-oil-company-for-distribution` FY2023: very low Latin word count (0 < 5000)
- `abu-dhabi-national-oil-company-for-distribution` FY2023: very low Latin word count (0 < 5000)
- `abu-dhabi-national-oil-company-for-distribution` FY2023: very low Latin word count (0 < 5000)
- `abu-dhabi-national-oil-company-for-distribution` FY2024: very low Latin word count (0 < 5000)
- `abu-dhabi-national-oil-company-for-distribution` FY2024: very low Latin word count (0 < 5000)
- `abu-dhabi-national-oil-company-for-distribution` FY2025: very low Latin word count (0 < 5000)
- `abu-dhabi-national-oil-company-for-distribution` FY2025: very low Latin word count (0 < 5000)
- `advanced-petrochemical` FY2020: very low Latin word count (0 < 5000)
- `advanced-petrochemical` FY2020: very low Latin word count (0 < 5000)
- `advanced-petrochemical` FY2021: very low Latin word count (0 < 5000)
- `advanced-petrochemical` FY2021: very low Latin word count (0 < 5000)
- `advanced-petrochemical` FY2022: heavily scanned: 100% of 65 pages would need OCR (> 40% cap); skipped to avoid multi-hour run
- `advanced-petrochemical` FY2022: very low Latin word count (0 < 5000)
- `advanced-petrochemical` FY2022: very low Latin word count (0 < 5000)
- `advanced-petrochemical` FY2023: very low Latin word count (0 < 5000)
- `advanced-petrochemical` FY2023: very low Latin word count (0 < 5000)
- `advanced-petrochemical` FY2024: very low Latin word count (0 < 5000)
- `advanced-petrochemical` FY2024: very low Latin word count (0 < 5000)
- `advanced-petrochemical` FY2025: very low Latin word count (0 < 5000)
- `advanced-petrochemical` FY2025: very low Latin word count (0 < 5000)
- `air-arabia-pjsc` FY2020: very low Latin word count (0 < 5000)
- `air-arabia-pjsc` FY2020: very low Latin word count (0 < 5000)
- `air-arabia-pjsc` FY2021: very low Latin word count (0 < 5000)
- `air-arabia-pjsc` FY2021: very low Latin word count (0 < 5000)
- `air-arabia-pjsc` FY2022: very low Latin word count (0 < 5000)
- `air-arabia-pjsc` FY2022: very low Latin word count (0 < 5000)
- `air-arabia-pjsc` FY2023: high OCR ratio (60% > 30%)
- `air-arabia-pjsc` FY2023: very low Latin word count (0 < 5000)
- `air-arabia-pjsc` FY2023: very low Latin word count (0 < 5000)
- `air-arabia-pjsc` FY2023: heavily scanned: 60% of 100 pages would need OCR (> 40% cap); skipped to avoid multi-hour run
- `air-arabia-pjsc` FY2024: very low Latin word count (0 < 5000)
- `air-arabia-pjsc` FY2024: high OCR ratio (60% > 30%)
- `air-arabia-pjsc` FY2024: heavily scanned: 60% of 108 pages would need OCR (> 40% cap); skipped to avoid multi-hour run
- `air-arabia-pjsc` FY2024: very low Latin word count (0 < 5000)
- `air-arabia-pjsc` FY2025: very low Latin word count (0 < 5000)
- `air-arabia-pjsc` FY2025: very low Latin word count (0 < 5000)
- `al-rajhi-bank` FY2020: very low Latin word count (0 < 5000)
- `al-rajhi-bank` FY2020: very low Latin word count (0 < 5000)
- `al-rajhi-bank` FY2020: very low Latin word count (0 < 5000)
- `al-rajhi-bank` FY2021: very low Latin word count (0 < 5000)
- `al-rajhi-bank` FY2021: very low Latin word count (0 < 5000)
- `al-rajhi-bank` FY2021: very low Latin word count (0 < 5000)
- `al-rajhi-bank` FY2022: very low Latin word count (0 < 5000)
- `al-rajhi-bank` FY2022: very low Latin word count (0 < 5000)
- `al-rajhi-bank` FY2022: very low Latin word count (0 < 5000)
- `al-rajhi-bank` FY2023: very low Latin word count (0 < 5000)
- `al-rajhi-bank` FY2023: very low Latin word count (0 < 5000)
- `al-rajhi-bank` FY2023: very low Latin word count (0 < 5000)
- `al-rajhi-bank` FY2024: very low Latin word count (0 < 5000)
- `al-rajhi-bank` FY2024: very low Latin word count (0 < 5000)
- `al-rajhi-bank` FY2024: very low Latin word count (0 < 5000)
- `al-rajhi-bank` FY2025: very low Latin word count (0 < 5000)
- `al-rajhi-bank` FY2025: very low Latin word count (0 < 5000)
- `al-rajhi-bank` FY2025: very low Latin word count (0 < 5000)
- `aldar-properties-pjsc` FY2020: very low Latin word count (0 < 5000)
- `aldar-properties-pjsc` FY2020: very low Latin word count (0 < 5000)
- `aldar-properties-pjsc` FY2021: very low Latin word count (0 < 5000)
- `aldar-properties-pjsc` FY2021: very low Latin word count (0 < 5000)
- `aldar-properties-pjsc` FY2022: very low Latin word count (0 < 5000)
- `aldar-properties-pjsc` FY2022: very low Latin word count (0 < 5000)
- `aldar-properties-pjsc` FY2023: very low Latin word count (0 < 5000)
- `aldar-properties-pjsc` FY2023: very low Latin word count (0 < 5000)
- `aldar-properties-pjsc` FY2024: very low Latin word count (0 < 5000)
- `aldar-properties-pjsc` FY2024: very low Latin word count (0 < 5000)
- `aldar-properties-pjsc` FY2025: very low Latin word count (0 < 5000)
- `aldar-properties-pjsc` FY2025: very low Latin word count (0 < 5000)
- `alinma-bank` FY2020: very low Latin word count (0 < 5000)
- `alinma-bank` FY2020: very low Latin word count (0 < 5000)
- `alinma-bank` FY2021: very low Latin word count (0 < 5000)
- `alinma-bank` FY2021: very low Latin word count (0 < 5000)
- `alinma-bank` FY2022: very low Latin word count (0 < 5000)
- `alinma-bank` FY2022: very low Latin word count (0 < 5000)
- `alinma-bank` FY2023: very low Latin word count (0 < 5000)
- `alinma-bank` FY2023: very low Latin word count (0 < 5000)
- `alinma-bank` FY2024: very low Latin word count (0 < 5000)
- `alinma-bank` FY2024: very low Latin word count (0 < 5000)
- `alinma-bank` FY2025: very low Latin word count (0 < 5000)
- `alinma-bank` FY2025: very low Latin word count (0 < 5000)
- `almarai` FY2020: very low Latin word count (0 < 5000)
- `almarai` FY2020: very low Latin word count (0 < 5000)
- `almarai` FY2021: very low Latin word count (0 < 5000)
- `almarai` FY2021: very low Latin word count (0 < 5000)
- `almarai` FY2022: very low Latin word count (0 < 5000)
- `almarai` FY2022: very low Latin word count (0 < 5000)
- `almarai` FY2023: very low Latin word count (0 < 5000)
- `almarai` FY2023: very low Latin word count (0 < 5000)
- `almarai` FY2024: very low Latin word count (0 < 5000)
- `almarai` FY2024: very low Latin word count (0 < 5000)
- `almarai` FY2025: very low Latin word count (0 < 5000)
- `almarai` FY2025: very low Latin word count (0 < 5000)
- `aluminium-bahrain-alba` FY2020: very low Latin word count (0 < 5000)
- `aluminium-bahrain-alba` FY2020: very low Latin word count (0 < 5000)
- `aluminium-bahrain-alba` FY2021: very low Latin word count (0 < 5000)
- `aluminium-bahrain-alba` FY2021: very low Latin word count (0 < 5000)
- `aluminium-bahrain-alba` FY2022: very low Latin word count (0 < 5000)
- `aluminium-bahrain-alba` FY2022: very low Latin word count (0 < 5000)
- `aluminium-bahrain-alba` FY2023: very low Latin word count (0 < 5000)
- `aluminium-bahrain-alba` FY2023: very low Latin word count (0 < 5000)
- `aluminium-bahrain-alba` FY2024: very low Latin word count (0 < 5000)
- `aluminium-bahrain-alba` FY2024: very low Latin word count (0 < 5000)
- `aluminium-bahrain-alba` FY2025: very low Latin word count (0 < 5000)
- `aluminium-bahrain-alba` FY2025: very low Latin word count (0 < 5000)
- `bahrain-telecommunications-beyon` FY2020: very low Latin word count (0 < 5000)
- `bahrain-telecommunications-beyon` FY2020: very low Latin word count (0 < 5000)
- `bahrain-telecommunications-beyon` FY2021: very low Latin word count (0 < 5000)
- `bahrain-telecommunications-beyon` FY2021: very low Latin word count (0 < 5000)
- `bahrain-telecommunications-beyon` FY2022: very low Latin word count (0 < 5000)
- `bahrain-telecommunications-beyon` FY2022: very low Latin word count (0 < 5000)
- `bahrain-telecommunications-beyon` FY2023: very low Latin word count (0 < 5000)
- `bahrain-telecommunications-beyon` FY2023: very low Latin word count (0 < 5000)
- `bahrain-telecommunications-beyon` FY2024: very low Latin word count (0 < 5000)
- `bahrain-telecommunications-beyon` FY2024: very low Latin word count (0 < 5000)
- `bahrain-telecommunications-beyon` FY2025: very low Latin word count (0 < 5000)
- `bahrain-telecommunications-beyon` FY2025: very low Latin word count (0 < 5000)
- `baladna` FY2020: very low Latin word count (0 < 5000)
- `baladna` FY2020: very low Latin word count (0 < 5000)
- `baladna` FY2021: very low Latin word count (0 < 5000)
- `baladna` FY2021: very low Latin word count (0 < 5000)
- `baladna` FY2022: very low Latin word count (0 < 5000)
- `baladna` FY2022: very low Latin word count (0 < 5000)
- `baladna` FY2023: very low Latin word count (0 < 5000)
- `baladna` FY2023: very low Latin word count (0 < 5000)
- `baladna` FY2024: very low Latin word count (0 < 5000)
- `baladna` FY2024: very low Latin word count (0 < 5000)
- `baladna` FY2025: very low Latin word count (0 < 5000)
- `baladna` FY2025: very low Latin word count (0 < 5000)
- `bank-albilad` FY2020: very low Latin word count (0 < 5000)
- `bank-albilad` FY2020: very low Latin word count (0 < 5000)
- `bank-albilad` FY2021: very low Latin word count (0 < 5000)
- `bank-albilad` FY2021: very low Latin word count (0 < 5000)
- `bank-albilad` FY2022: very low Latin word count (0 < 5000)
- `bank-albilad` FY2022: very low Latin word count (0 < 5000)
- `bank-albilad` FY2023: very low Latin word count (0 < 5000)
- `bank-albilad` FY2023: very low Latin word count (0 < 5000)
- `bank-albilad` FY2024: very low Latin word count (0 < 5000)
- `bank-albilad` FY2024: very low Latin word count (0 < 5000)
- `bank-albilad` FY2025: very low Latin word count (0 < 5000)
- `bank-albilad` FY2025: very low Latin word count (0 < 5000)
- `bank-dhofar` FY2020: very low Latin word count (0 < 5000)
- `bank-dhofar` FY2020: very low Latin word count (0 < 5000)
- `bank-dhofar` FY2021: very low Latin word count (0 < 5000)
- `bank-dhofar` FY2021: very low Latin word count (0 < 5000)
- `bank-dhofar` FY2022: very low Latin word count (0 < 5000)
- `bank-dhofar` FY2022: very low Latin word count (0 < 5000)
- `bank-dhofar` FY2023: very low Latin word count (0 < 5000)
- `bank-dhofar` FY2023: very low Latin word count (0 < 5000)
- `bank-dhofar` FY2024: very low Latin word count (0 < 5000)
- `bank-dhofar` FY2024: very low Latin word count (0 < 5000)
- `bank-dhofar` FY2025: very low Latin word count (0 < 5000)
- `bank-dhofar` FY2025: very low Latin word count (0 < 5000)
- `bank-muscat-bkmb` FY2020: very low Latin word count (0 < 5000)
- `bank-muscat-bkmb` FY2020: very low Latin word count (0 < 5000)
- `bank-muscat-bkmb` FY2021: very low Latin word count (0 < 5000)
- `bank-muscat-bkmb` FY2021: very low Latin word count (0 < 5000)
- `bank-muscat-bkmb` FY2022: very low Latin word count (0 < 5000)
- `bank-muscat-bkmb` FY2022: very low Latin word count (0 < 5000)
- `bank-muscat-bkmb` FY2023: very low Latin word count (0 < 5000)
- `bank-muscat-bkmb` FY2023: very low Latin word count (0 < 5000)
- `bank-muscat-bkmb` FY2024: very low Latin word count (0 < 5000)
- `bank-muscat-bkmb` FY2024: very low Latin word count (0 < 5000)
- `bank-muscat-bkmb` FY2025: very low Latin word count (0 < 5000)
- `bank-muscat-bkmb` FY2025: very low Latin word count (0 < 5000)
- `barwa-real-estate` FY2020: very low Latin word count (0 < 5000)
- `barwa-real-estate` FY2020: very low Latin word count (0 < 5000)
- `barwa-real-estate` FY2021: very low Latin word count (0 < 5000)
- `barwa-real-estate` FY2021: very low Latin word count (0 < 5000)
- `barwa-real-estate` FY2022: very low Latin word count (0 < 5000)
- `barwa-real-estate` FY2022: very low Latin word count (0 < 5000)
- `barwa-real-estate` FY2023: very low Latin word count (0 < 5000)
- `barwa-real-estate` FY2023: very low Latin word count (0 < 5000)
- `barwa-real-estate` FY2024: very low Latin word count (0 < 5000)
- `barwa-real-estate` FY2024: very low Latin word count (0 < 5000)
- `barwa-real-estate` FY2025: very low Latin word count (0 < 5000)
- `barwa-real-estate` FY2025: very low Latin word count (0 < 5000)
- `boubyan-bank` FY2020: very low Latin word count (0 < 5000)
- `boubyan-bank` FY2020: very low Latin word count (0 < 5000)
- `boubyan-bank` FY2021: very low Latin word count (0 < 5000)
- `boubyan-bank` FY2021: very low Latin word count (0 < 5000)
- `boubyan-bank` FY2022: very low Latin word count (0 < 5000)
- `boubyan-bank` FY2022: very low Latin word count (0 < 5000)
- `boubyan-bank` FY2022: very low Latin word count (0 < 5000)
- `boubyan-bank` FY2023: very low Latin word count (0 < 5000)
- `boubyan-bank` FY2023: very low Latin word count (0 < 5000)
- `boubyan-bank` FY2024: very low Latin word count (0 < 5000)
- `boubyan-bank` FY2024: very low Latin word count (0 < 5000)
- `boubyan-bank` FY2025: very low Latin word count (0 < 5000)
- `boubyan-bank` FY2025: very low Latin word count (0 < 5000)
- `dar-al-arkan-real-estate-development-company` FY2020: very low Latin word count (0 < 5000)
- `dar-al-arkan-real-estate-development-company` FY2020: very low Latin word count (0 < 5000)
- `dar-al-arkan-real-estate-development-company` FY2021: very low Latin word count (0 < 5000)
- `dar-al-arkan-real-estate-development-company` FY2021: very low Latin word count (0 < 5000)
- `dar-al-arkan-real-estate-development-company` FY2021: very low Latin word count (0 < 5000)
- `dar-al-arkan-real-estate-development-company` FY2022: very low Latin word count (0 < 5000)
- `dar-al-arkan-real-estate-development-company` FY2022: very low Latin word count (0 < 5000)
- `dar-al-arkan-real-estate-development-company` FY2022: very low Latin word count (0 < 5000)
- `dar-al-arkan-real-estate-development-company` FY2023: very low Latin word count (0 < 5000)
- `dar-al-arkan-real-estate-development-company` FY2023: very low Latin word count (0 < 5000)
- `dar-al-arkan-real-estate-development-company` FY2024: very low Latin word count (0 < 5000)
- `dar-al-arkan-real-estate-development-company` FY2024: very low Latin word count (0 < 5000)
- `dar-al-arkan-real-estate-development-company` FY2024: very low Latin word count (0 < 5000)
- `dar-al-arkan-real-estate-development-company` FY2025: very low Latin word count (0 < 5000)
- `dar-al-arkan-real-estate-development-company` FY2025: very low Latin word count (0 < 5000)
- `dubai-investment` FY2020: very low Latin word count (0 < 5000)
- `dubai-investment` FY2020: very low Latin word count (0 < 5000)
- `dubai-investment` FY2021: very low Latin word count (0 < 5000)
- `dubai-investment` FY2021: very low Latin word count (0 < 5000)
- `dubai-investment` FY2021: very low Latin word count (0 < 5000)
- `dubai-investment` FY2022: very low Latin word count (0 < 5000)
- `dubai-investment` FY2022: very low Latin word count (0 < 5000)
- `dubai-investment` FY2023: very low Latin word count (0 < 5000)
- `dubai-investment` FY2023: very low Latin word count (0 < 5000)
- `dubai-investment` FY2024: very low Latin word count (0 < 5000)
- `dubai-investment` FY2024: very low Latin word count (0 < 5000)
- `dubai-investment` FY2025: very low Latin word count (0 < 5000)
- `dubai-investment` FY2025: very low Latin word count (0 < 5000)
- `dubai-islamic-bank` FY2020: very low Latin word count (0 < 5000)
- `dubai-islamic-bank` FY2020: very low Latin word count (0 < 5000)
- `dubai-islamic-bank` FY2021: high OCR ratio (48% > 30%)
- `dubai-islamic-bank` FY2021: heavily scanned: 48% of 207 pages would need OCR (> 40% cap); skipped to avoid multi-hour run
- `dubai-islamic-bank` FY2021: very low Latin word count (0 < 5000)
- `dubai-islamic-bank` FY2021: very low Latin word count (0 < 5000)
- `dubai-islamic-bank` FY2022: very low Latin word count (0 < 5000)
- `dubai-islamic-bank` FY2022: very low Latin word count (0 < 5000)
- `dubai-islamic-bank` FY2023: very low Latin word count (0 < 5000)
- `dubai-islamic-bank` FY2023: very low Latin word count (0 < 5000)
- `dubai-islamic-bank` FY2024: very low Latin word count (0 < 5000)
- `dubai-islamic-bank` FY2024: very low Latin word count (0 < 5000)
- `dubai-islamic-bank` FY2025: very low Latin word count (0 < 5000)
- `dubai-islamic-bank` FY2025: very low Latin word count (0 < 5000)
- `emaar-properties` FY2020: very low Latin word count (0 < 5000)
- `emaar-properties` FY2020: very low Latin word count (0 < 5000)
- `emaar-properties` FY2021: very low Latin word count (0 < 5000)
- `emaar-properties` FY2021: very low Latin word count (0 < 5000)
- `emaar-properties` FY2022: very low Latin word count (0 < 5000)
- `emaar-properties` FY2022: very low Latin word count (0 < 5000)
- `emaar-properties` FY2023: very low Latin word count (0 < 5000)
- `emaar-properties` FY2023: very low Latin word count (0 < 5000)
- `emaar-properties` FY2024: very low Latin word count (0 < 5000)
- `emaar-properties` FY2024: very low Latin word count (0 < 5000)
- `emaar-properties` FY2025: very low Latin word count (0 < 5000)
- `emaar-properties` FY2025: very low Latin word count (0 < 5000)
- `emirates-nbd-pjsc` FY2020: very low Latin word count (0 < 5000)
- `emirates-nbd-pjsc` FY2020: very low Latin word count (0 < 5000)
- `emirates-nbd-pjsc` FY2021: very low Latin word count (0 < 5000)
- `emirates-nbd-pjsc` FY2021: very low Latin word count (0 < 5000)
- `emirates-nbd-pjsc` FY2022: very low Latin word count (0 < 5000)
- `emirates-nbd-pjsc` FY2022: very low Latin word count (0 < 5000)
- `emirates-nbd-pjsc` FY2023: very low Latin word count (0 < 5000)
- `emirates-nbd-pjsc` FY2023: very low Latin word count (0 < 5000)
- `emirates-nbd-pjsc` FY2024: very low Latin word count (0 < 5000)
- `emirates-nbd-pjsc` FY2024: very low Latin word count (0 < 5000)
- `emirates-nbd-pjsc` FY2025: very low Latin word count (0 < 5000)
- `emirates-nbd-pjsc` FY2025: very low Latin word count (0 < 5000)
- `emirates-telecom-etisalat-group` FY2020: very low Latin word count (0 < 5000)
- `emirates-telecom-etisalat-group` FY2020: very low Latin word count (0 < 5000)
- `emirates-telecom-etisalat-group` FY2021: very low Latin word count (0 < 5000)
- `emirates-telecom-etisalat-group` FY2021: very low Latin word count (0 < 5000)
- `emirates-telecom-etisalat-group` FY2022: very low Latin word count (0 < 5000)
- `emirates-telecom-etisalat-group` FY2022: very low Latin word count (0 < 5000)
- `emirates-telecom-etisalat-group` FY2023: very low Latin word count (0 < 5000)
- `emirates-telecom-etisalat-group` FY2023: very low Latin word count (0 < 5000)
- `emirates-telecom-etisalat-group` FY2024: very low Latin word count (0 < 5000)
- `emirates-telecom-etisalat-group` FY2024: very low Latin word count (0 < 5000)
- `emirates-telecom-etisalat-group` FY2025: very low Latin word count (0 < 5000)
- `emirates-telecom-etisalat-group` FY2025: very low Latin word count (0 < 5000)
- `etihad-etisalat-mobily` FY2020: very low Latin word count (0 < 5000)
- `etihad-etisalat-mobily` FY2020: very low Latin word count (0 < 5000)
- `etihad-etisalat-mobily` FY2021: very low Latin word count (0 < 5000)
- `etihad-etisalat-mobily` FY2021: very low Latin word count (0 < 5000)
- `etihad-etisalat-mobily` FY2022: very low Latin word count (0 < 5000)
- `etihad-etisalat-mobily` FY2022: very low Latin word count (0 < 5000)
- `etihad-etisalat-mobily` FY2023: very low Latin word count (0 < 5000)
- `etihad-etisalat-mobily` FY2023: very low Latin word count (0 < 5000)
- `etihad-etisalat-mobily` FY2024: very low Latin word count (0 < 5000)
- `etihad-etisalat-mobily` FY2024: very low Latin word count (0 < 5000)
- `etihad-etisalat-mobily` FY2025: very low Latin word count (0 < 5000)
- `etihad-etisalat-mobily` FY2025: very low Latin word count (0 < 5000)
- `first-abu-dhabi-bank` FY2020: very low Latin word count (0 < 5000)
- `first-abu-dhabi-bank` FY2020: very low Latin word count (0 < 5000)
- `first-abu-dhabi-bank` FY2021: very low Latin word count (0 < 5000)
- `first-abu-dhabi-bank` FY2021: very low Latin word count (0 < 5000)
- `first-abu-dhabi-bank` FY2022: very low Latin word count (0 < 5000)
- `first-abu-dhabi-bank` FY2022: very low Latin word count (0 < 5000)
- `first-abu-dhabi-bank` FY2023: very low Latin word count (0 < 5000)
- `first-abu-dhabi-bank` FY2023: very low Latin word count (0 < 5000)
- `first-abu-dhabi-bank` FY2024: very low Latin word count (0 < 5000)
- `first-abu-dhabi-bank` FY2024: very low Latin word count (0 < 5000)
- `first-abu-dhabi-bank` FY2025: very low Latin word count (0 < 5000)
- `first-abu-dhabi-bank` FY2025: very low Latin word count (0 < 5000)
- `gulf-hotels-group` FY2020: very low Latin word count (0 < 5000)
- `gulf-hotels-group` FY2020: very low Latin word count (0 < 5000)
- `gulf-hotels-group` FY2021: very low Latin word count (0 < 5000)
- `gulf-hotels-group` FY2021: very low Latin word count (0 < 5000)
- `gulf-hotels-group` FY2022: very low Latin word count (0 < 5000)
- `gulf-hotels-group` FY2022: very low Latin word count (0 < 5000)
- `gulf-hotels-group` FY2023: very low Latin word count (0 < 5000)
- `gulf-hotels-group` FY2023: very low Latin word count (0 < 5000)
- `gulf-hotels-group` FY2024: very low Latin word count (0 < 5000)
- `gulf-hotels-group` FY2024: very low Latin word count (0 < 5000)
- `gulf-hotels-group` FY2025: very low Latin word count (0 < 5000)
- `gulf-hotels-group` FY2025: very low Latin word count (0 < 5000)
- `gulf-international-services` FY2020: very low Latin word count (0 < 5000)
- `gulf-international-services` FY2020: very low Latin word count (0 < 5000)
- `gulf-international-services` FY2021: very low Latin word count (0 < 5000)
- `gulf-international-services` FY2021: very low Latin word count (0 < 5000)
- `gulf-international-services` FY2022: very low Latin word count (0 < 5000)
- `gulf-international-services` FY2022: very low Latin word count (0 < 5000)
- `gulf-international-services` FY2023: very low Latin word count (0 < 5000)
- `gulf-international-services` FY2023: very low Latin word count (0 < 5000)
- `gulf-international-services` FY2024: very low Latin word count (0 < 5000)
- `gulf-international-services` FY2024: very low Latin word count (0 < 5000)
- `gulf-international-services` FY2025: very low Latin word count (0 < 5000)
- `gulf-international-services` FY2025: very low Latin word count (0 < 5000)
- `industries-qatar` FY2020: very low Latin word count (0 < 5000)
- `industries-qatar` FY2020: very low Latin word count (0 < 5000)
- `industries-qatar` FY2021: very low Latin word count (0 < 5000)
- `industries-qatar` FY2021: very low Latin word count (0 < 5000)
- `industries-qatar` FY2022: very low Latin word count (0 < 5000)
- `industries-qatar` FY2022: very low Latin word count (0 < 5000)
- `industries-qatar` FY2023: very low Latin word count (0 < 5000)
- `industries-qatar` FY2023: very low Latin word count (0 < 5000)
- `industries-qatar` FY2024: very low Latin word count (0 < 5000)
- `industries-qatar` FY2024: very low Latin word count (0 < 5000)
- `industries-qatar` FY2025: very low Latin word count (0 < 5000)
- `industries-qatar` FY2025: very low Latin word count (0 < 5000)
- `jarir-marketing-co` FY2020: very low Latin word count (0 < 5000)
- `jarir-marketing-co` FY2020: very low Latin word count (0 < 5000)
- `jarir-marketing-co` FY2021: very low Latin word count (0 < 5000)
- `jarir-marketing-co` FY2021: very low Latin word count (0 < 5000)
- `jarir-marketing-co` FY2022: very low Latin word count (0 < 5000)
- `jarir-marketing-co` FY2022: very low Latin word count (0 < 5000)
- `jarir-marketing-co` FY2023: very low Latin word count (0 < 5000)
- `jarir-marketing-co` FY2023: very low Latin word count (0 < 5000)
- `jarir-marketing-co` FY2024: very low Latin word count (0 < 5000)
- `jarir-marketing-co` FY2024: very low Latin word count (0 < 5000)
- `jarir-marketing-co` FY2025: very low Latin word count (0 < 5000)
- `jarir-marketing-co` FY2025: very low Latin word count (0 < 5000)
- `jazeera-airways` FY2020: very low Latin word count (0 < 5000)
- `jazeera-airways` FY2020: very low Latin word count (0 < 5000)
- `jazeera-airways` FY2021: very low Latin word count (0 < 5000)
- `jazeera-airways` FY2021: very low Latin word count (0 < 5000)
- `jazeera-airways` FY2022: very low Latin word count (0 < 5000)
- `jazeera-airways` FY2022: very low Latin word count (0 < 5000)
- `jazeera-airways` FY2023: very low Latin word count (0 < 5000)
- `jazeera-airways` FY2023: very low Latin word count (0 < 5000)
- `jazeera-airways` FY2024: very low Latin word count (0 < 5000)
- `jazeera-airways` FY2024: very low Latin word count (0 < 5000)
- `jazeera-airways` FY2025: very low Latin word count (0 < 5000)
- `jazeera-airways` FY2025: very low Latin word count (0 < 5000)
- `jazeera-steel` FY2020: very low Latin word count (0 < 5000)
- `jazeera-steel` FY2020: very low Latin word count (0 < 5000)
- `jazeera-steel` FY2021: very low Latin word count (0 < 5000)
- `jazeera-steel` FY2021: very low Latin word count (0 < 5000)
- `jazeera-steel` FY2022: very low Latin word count (0 < 5000)
- `jazeera-steel` FY2022: very low Latin word count (0 < 5000)
- `jazeera-steel` FY2023: very low Latin word count (0 < 5000)
- `jazeera-steel` FY2023: very low Latin word count (0 < 5000)
- `jazeera-steel` FY2024: very low Latin word count (0 < 5000)
- `jazeera-steel` FY2024: very low Latin word count (0 < 5000)
- `jazeera-steel` FY2025: very low Latin word count (0 < 5000)
- `jazeera-steel` FY2025: very low Latin word count (0 < 5000)
- `kuwait-finance-house` FY2020: very low Latin word count (0 < 5000)
- `kuwait-finance-house` FY2020: very low Latin word count (0 < 5000)
- `kuwait-finance-house` FY2021: very low Latin word count (0 < 5000)
- `kuwait-finance-house` FY2021: very low Latin word count (0 < 5000)
- `kuwait-finance-house` FY2022: very low Latin word count (0 < 5000)
- `kuwait-finance-house` FY2022: very low Latin word count (0 < 5000)
- `kuwait-finance-house` FY2023: very low Latin word count (0 < 5000)
- `kuwait-finance-house` FY2023: very low Latin word count (0 < 5000)
- `kuwait-finance-house` FY2024: very low Latin word count (0 < 5000)
- `kuwait-finance-house` FY2024: very low Latin word count (0 < 5000)
- `kuwait-finance-house` FY2025: very low Latin word count (0 < 5000)
- `kuwait-finance-house` FY2025: very low Latin word count (0 < 5000)
- `kuwait-telecommunications-company` FY2020: very low Latin word count (0 < 5000)
- `kuwait-telecommunications-company` FY2020: heavily scanned: 42% of 130 pages would need OCR (> 40% cap); skipped to avoid multi-hour run
- `kuwait-telecommunications-company` FY2020: very low Latin word count (0 < 5000)
- `kuwait-telecommunications-company` FY2020: high OCR ratio (42% > 30%)
- `kuwait-telecommunications-company` FY2021: very low Latin word count (0 < 5000)
- `kuwait-telecommunications-company` FY2021: very low Latin word count (0 < 5000)
- `kuwait-telecommunications-company` FY2022: very low Latin word count (0 < 5000)
- `kuwait-telecommunications-company` FY2022: very low Latin word count (0 < 5000)
- `kuwait-telecommunications-company` FY2023: very low Latin word count (0 < 5000)
- `kuwait-telecommunications-company` FY2023: very low Latin word count (0 < 5000)
- `kuwait-telecommunications-company` FY2024: very low Latin word count (0 < 5000)
- `kuwait-telecommunications-company` FY2024: very low Latin word count (0 < 5000)
- `kuwait-telecommunications-company` FY2025: very low Latin word count (0 < 5000)
- `kuwait-telecommunications-company` FY2025: very low Latin word count (0 < 5000)
- `maaden` FY2020: very low Latin word count (0 < 5000)
- `maaden` FY2020: very low Latin word count (0 < 5000)
- `maaden` FY2021: very low Latin word count (0 < 5000)
- `maaden` FY2021: very low Latin word count (0 < 5000)
- `maaden` FY2022: very low Latin word count (0 < 5000)
- `maaden` FY2022: very low Latin word count (0 < 5000)
- `maaden` FY2023: very low Latin word count (0 < 5000)
- `maaden` FY2023: very low Latin word count (0 < 5000)
- `maaden` FY2024: very low Latin word count (0 < 5000)
- `maaden` FY2024: very low Latin word count (0 < 5000)
- `maaden` FY2025: very low Latin word count (0 < 5000)
- `maaden` FY2025: very low Latin word count (0 < 5000)
- `mobile-telecommunications-co-saudi-arabia-zain` FY2020: very low Latin word count (0 < 5000)
- `mobile-telecommunications-co-saudi-arabia-zain` FY2020: very low Latin word count (0 < 5000)
- `mobile-telecommunications-co-saudi-arabia-zain` FY2021: very low Latin word count (0 < 5000)
- `mobile-telecommunications-co-saudi-arabia-zain` FY2021: very low Latin word count (0 < 5000)
- `mobile-telecommunications-co-saudi-arabia-zain` FY2022: very low Latin word count (0 < 5000)
- `mobile-telecommunications-co-saudi-arabia-zain` FY2022: very low Latin word count (0 < 5000)
- `mobile-telecommunications-co-saudi-arabia-zain` FY2023: very low Latin word count (0 < 5000)
- `mobile-telecommunications-co-saudi-arabia-zain` FY2023: very low Latin word count (0 < 5000)
- `mobile-telecommunications-co-saudi-arabia-zain` FY2024: very low Latin word count (0 < 5000)
- `mobile-telecommunications-co-saudi-arabia-zain` FY2024: very low Latin word count (0 < 5000)
- `mobile-telecommunications-co-saudi-arabia-zain` FY2025: very low Latin word count (0 < 5000)
- `mobile-telecommunications-co-saudi-arabia-zain` FY2025: very low Latin word count (0 < 5000)
- `mouwasat-medical-services-company` FY2020: very low Latin word count (0 < 5000)
- `mouwasat-medical-services-company` FY2020: very low Latin word count (0 < 5000)
- `mouwasat-medical-services-company` FY2021: very low Latin word count (0 < 5000)
- `mouwasat-medical-services-company` FY2021: very low Latin word count (0 < 5000)
- `mouwasat-medical-services-company` FY2022: very low Latin word count (0 < 5000)
- `mouwasat-medical-services-company` FY2022: very low Latin word count (0 < 5000)
- `mouwasat-medical-services-company` FY2023: very low Latin word count (0 < 5000)
- `mouwasat-medical-services-company` FY2023: very low Latin word count (0 < 5000)
- `mouwasat-medical-services-company` FY2024: very low Latin word count (0 < 5000)
- `mouwasat-medical-services-company` FY2024: very low Latin word count (0 < 5000)
- `mouwasat-medical-services-company` FY2025: very low Latin word count (0 < 5000)
- `mouwasat-medical-services-company` FY2025: very low Latin word count (0 < 5000)
- `national-bank-of-bahrain` FY2020: very low Latin word count (0 < 5000)
- `national-bank-of-bahrain` FY2020: very low Latin word count (0 < 5000)
- `national-bank-of-bahrain` FY2021: very low Latin word count (0 < 5000)
- `national-bank-of-bahrain` FY2021: very low Latin word count (0 < 5000)
- `national-bank-of-bahrain` FY2022: very low Latin word count (0 < 5000)
- `national-bank-of-bahrain` FY2022: very low Latin word count (0 < 5000)
- `national-bank-of-bahrain` FY2023: very low Latin word count (0 < 5000)
- `national-bank-of-bahrain` FY2023: very low Latin word count (0 < 5000)
- `national-bank-of-bahrain` FY2023: very low Latin word count (0 < 5000)
- `national-bank-of-bahrain` FY2024: very low Latin word count (0 < 5000)
- `national-bank-of-bahrain` FY2024: very low Latin word count (0 < 5000)
- `national-bank-of-bahrain` FY2024: very low Latin word count (0 < 5000)
- `national-bank-of-bahrain` FY2025: very low Latin word count (0 < 5000)
- `national-bank-of-bahrain` FY2025: very low Latin word count (0 < 5000)
- `national-bank-of-kuwait` FY2020: very low Latin word count (0 < 5000)
- `national-bank-of-kuwait` FY2020: very low Latin word count (0 < 5000)
- `national-bank-of-kuwait` FY2021: very low Latin word count (0 < 5000)
- `national-bank-of-kuwait` FY2021: very low Latin word count (0 < 5000)
- `national-bank-of-kuwait` FY2022: very low Latin word count (0 < 5000)
- `national-bank-of-kuwait` FY2022: very low Latin word count (0 < 5000)
- `national-bank-of-kuwait` FY2023: very low Latin word count (0 < 5000)
- `national-bank-of-kuwait` FY2023: very low Latin word count (0 < 5000)
- `national-bank-of-kuwait` FY2024: very low Latin word count (0 < 5000)
- `national-bank-of-kuwait` FY2024: very low Latin word count (0 < 5000)
- `national-bank-of-kuwait` FY2025: very low Latin word count (0 < 5000)
- `national-bank-of-kuwait` FY2025: very low Latin word count (0 < 5000)
- `national-industrialization-co` FY2020: very low Latin word count (0 < 5000)
- `national-industrialization-co` FY2020: very low Latin word count (0 < 5000)
- `national-industrialization-co` FY2021: very low Latin word count (0 < 5000)
- `national-industrialization-co` FY2021: very low Latin word count (0 < 5000)
- `national-industrialization-co` FY2022: very low Latin word count (0 < 5000)
- `national-industrialization-co` FY2022: very low Latin word count (0 < 5000)
- `national-industrialization-co` FY2023: very low Latin word count (0 < 5000)
- `national-industrialization-co` FY2023: very low Latin word count (0 < 5000)
- `national-industrialization-co` FY2024: very low Latin word count (0 < 5000)
- `national-industrialization-co` FY2024: very low Latin word count (0 < 5000)
- `national-industrialization-co` FY2025: very low Latin word count (0 < 5000)
- `national-industrialization-co` FY2025: very low Latin word count (0 < 5000)
- `oman-international-development-and-investment-company` FY2020: very low Latin word count (0 < 5000)
- `oman-international-development-and-investment-company` FY2020: very low Latin word count (0 < 5000)
- `oman-international-development-and-investment-company` FY2021: very low Latin word count (0 < 5000)
- `oman-international-development-and-investment-company` FY2021: very low Latin word count (0 < 5000)
- `oman-international-development-and-investment-company` FY2022: very low Latin word count (0 < 5000)
- `oman-international-development-and-investment-company` FY2022: very low Latin word count (0 < 5000)
- `oman-international-development-and-investment-company` FY2023: very low Latin word count (0 < 5000)
- `oman-international-development-and-investment-company` FY2023: very low Latin word count (0 < 5000)
- `oman-international-development-and-investment-company` FY2024: very low Latin word count (0 < 5000)
- `oman-international-development-and-investment-company` FY2024: very low Latin word count (0 < 5000)
- `oman-international-development-and-investment-company` FY2025: very low Latin word count (0 < 5000)
- `oman-international-development-and-investment-company` FY2025: very low Latin word count (0 < 5000)
- `oman-telecommunications-company-otel` FY2020: very low Latin word count (0 < 5000)
- `oman-telecommunications-company-otel` FY2020: very low Latin word count (0 < 5000)
- `oman-telecommunications-company-otel` FY2021: very low Latin word count (0 < 5000)
- `oman-telecommunications-company-otel` FY2021: very low Latin word count (0 < 5000)
- `oman-telecommunications-company-otel` FY2022: very low Latin word count (0 < 5000)
- `oman-telecommunications-company-otel` FY2022: very low Latin word count (0 < 5000)
- `oman-telecommunications-company-otel` FY2023: very low Latin word count (0 < 5000)
- `oman-telecommunications-company-otel` FY2023: very low Latin word count (0 < 5000)
- `oman-telecommunications-company-otel` FY2024: very low Latin word count (0 < 5000)
- `oman-telecommunications-company-otel` FY2024: very low Latin word count (0 < 5000)
- `oman-telecommunications-company-otel` FY2025: very low Latin word count (0 < 5000)
- `oman-telecommunications-company-otel` FY2025: very low Latin word count (0 < 5000)
- `ooredoo-q-p-s-c` FY2020: very low Latin word count (0 < 5000)
- `ooredoo-q-p-s-c` FY2020: very low Latin word count (0 < 5000)
- `ooredoo-q-p-s-c` FY2021: very low Latin word count (0 < 5000)
- `ooredoo-q-p-s-c` FY2021: very low Latin word count (0 < 5000)
- `ooredoo-q-p-s-c` FY2022: very low Latin word count (0 < 5000)
- `ooredoo-q-p-s-c` FY2022: very low Latin word count (0 < 5000)
- `ooredoo-q-p-s-c` FY2023: very low Latin word count (0 < 5000)
- `ooredoo-q-p-s-c` FY2023: very low Latin word count (0 < 5000)
- `ooredoo-q-p-s-c` FY2023: very low Latin word count (0 < 5000)
- `ooredoo-q-p-s-c` FY2024: very low Latin word count (0 < 5000)
- `ooredoo-q-p-s-c` FY2024: very low Latin word count (0 < 5000)
- `ooredoo-q-p-s-c` FY2025: very low Latin word count (0 < 5000)
- `ooredoo-q-p-s-c` FY2025: very low Latin word count (0 < 5000)
- `ooredoo-q-p-s-c` FY2025: very low Latin word count (0 < 5000)
- `qatar-fuel-company-woqod` FY2020: very low Latin word count (0 < 5000)
- `qatar-fuel-company-woqod` FY2020: very low Latin word count (0 < 5000)
- `qatar-fuel-company-woqod` FY2020: very low Latin word count (0 < 5000)
- `qatar-fuel-company-woqod` FY2021: very low Latin word count (0 < 5000)
- `qatar-fuel-company-woqod` FY2021: very low Latin word count (0 < 5000)
- `qatar-fuel-company-woqod` FY2022: very low Latin word count (0 < 5000)
- `qatar-fuel-company-woqod` FY2022: very low Latin word count (0 < 5000)
- `qatar-fuel-company-woqod` FY2022: very low Latin word count (0 < 5000)
- `qatar-fuel-company-woqod` FY2023: very low Latin word count (0 < 5000)
- `qatar-fuel-company-woqod` FY2023: very low Latin word count (0 < 5000)
- `qatar-fuel-company-woqod` FY2024: very low Latin word count (0 < 5000)
- `qatar-fuel-company-woqod` FY2024: very low Latin word count (0 < 5000)
- `qatar-fuel-company-woqod` FY2025: very low Latin word count (0 < 5000)
- `qatar-fuel-company-woqod` FY2025: very low Latin word count (0 < 5000)
- `qatar-gas-transport-co-nakilat` FY2020: very low Latin word count (0 < 5000)
- `qatar-gas-transport-co-nakilat` FY2020: very low Latin word count (0 < 5000)
- `qatar-gas-transport-co-nakilat` FY2021: very low Latin word count (0 < 5000)
- `qatar-gas-transport-co-nakilat` FY2021: very low Latin word count (0 < 5000)
- `qatar-gas-transport-co-nakilat` FY2022: very low Latin word count (0 < 5000)
- `qatar-gas-transport-co-nakilat` FY2022: very low Latin word count (0 < 5000)
- `qatar-gas-transport-co-nakilat` FY2023: very low Latin word count (0 < 5000)
- `qatar-gas-transport-co-nakilat` FY2023: very low Latin word count (0 < 5000)
- `qatar-gas-transport-co-nakilat` FY2024: very low Latin word count (0 < 5000)
- `qatar-gas-transport-co-nakilat` FY2024: very low Latin word count (0 < 5000)
- `qatar-gas-transport-co-nakilat` FY2025: very low Latin word count (0 < 5000)
- `qatar-gas-transport-co-nakilat` FY2025: very low Latin word count (0 < 5000)
- `qnb-qatar-national-bank` FY2020: very low Latin word count (0 < 5000)
- `qnb-qatar-national-bank` FY2020: very low Latin word count (0 < 5000)
- `qnb-qatar-national-bank` FY2021: very low Latin word count (0 < 5000)
- `qnb-qatar-national-bank` FY2021: very low Latin word count (0 < 5000)
- `qnb-qatar-national-bank` FY2022: very low Latin word count (0 < 5000)
- `qnb-qatar-national-bank` FY2022: very low Latin word count (0 < 5000)
- `qnb-qatar-national-bank` FY2023: very low Latin word count (0 < 5000)
- `qnb-qatar-national-bank` FY2023: very low Latin word count (0 < 5000)
- `qnb-qatar-national-bank` FY2023: very low Latin word count (0 < 5000)
- `qnb-qatar-national-bank` FY2024: very low Latin word count (0 < 5000)
- `qnb-qatar-national-bank` FY2024: very low Latin word count (0 < 5000)
- `qnb-qatar-national-bank` FY2024: very low Latin word count (0 < 5000)
- `qnb-qatar-national-bank` FY2025: very low Latin word count (0 < 5000)
- `qnb-qatar-national-bank` FY2025: very low Latin word count (0 < 5000)
- `qnb-qatar-national-bank` FY2025: very low Latin word count (0 < 5000)
- `rabigh-refining-petrochemical-co` FY2020: very low Latin word count (0 < 5000)
- `rabigh-refining-petrochemical-co` FY2020: very low Latin word count (0 < 5000)
- `rabigh-refining-petrochemical-co` FY2021: very low Latin word count (0 < 5000)
- `rabigh-refining-petrochemical-co` FY2021: very low Latin word count (0 < 5000)
- `rabigh-refining-petrochemical-co` FY2022: very low Latin word count (0 < 5000)
- `rabigh-refining-petrochemical-co` FY2022: very low Latin word count (0 < 5000)
- `rabigh-refining-petrochemical-co` FY2023: very low Latin word count (0 < 5000)
- `rabigh-refining-petrochemical-co` FY2023: very low Latin word count (0 < 5000)
- `rabigh-refining-petrochemical-co` FY2024: very low Latin word count (0 < 5000)
- `rabigh-refining-petrochemical-co` FY2024: very low Latin word count (0 < 5000)
- `rabigh-refining-petrochemical-co` FY2025: very low Latin word count (0 < 5000)
- `rabigh-refining-petrochemical-co` FY2025: very low Latin word count (0 < 5000)
- `riyad-bank` FY2020: very low Latin word count (0 < 5000)
- `riyad-bank` FY2020: very low Latin word count (0 < 5000)
- `riyad-bank` FY2021: very low Latin word count (0 < 5000)
- `riyad-bank` FY2021: very low Latin word count (0 < 5000)
- `riyad-bank` FY2022: very low Latin word count (0 < 5000)
- `riyad-bank` FY2022: very low Latin word count (0 < 5000)
- `riyad-bank` FY2023: very low Latin word count (0 < 5000)
- `riyad-bank` FY2023: very low Latin word count (0 < 5000)
- `riyad-bank` FY2024: very low Latin word count (0 < 5000)
- `riyad-bank` FY2024: very low Latin word count (0 < 5000)
- `riyad-bank` FY2025: very low Latin word count (0 < 5000)
- `riyad-bank` FY2025: very low Latin word count (0 < 5000)
- `sabic` FY2020: very low Latin word count (0 < 5000)
- `sabic` FY2020: very low Latin word count (0 < 5000)
- `sabic` FY2021: very low Latin word count (0 < 5000)
- `sabic` FY2021: very low Latin word count (0 < 5000)
- `sabic` FY2022: very low Latin word count (0 < 5000)
- `sabic` FY2022: very low Latin word count (0 < 5000)
- `sabic` FY2023: very low Latin word count (0 < 5000)
- `sabic` FY2023: very low Latin word count (0 < 5000)
- `sabic` FY2024: very low Latin word count (0 < 5000)
- `sabic` FY2024: very low Latin word count (0 < 5000)
- `sabic` FY2025: very low Latin word count (0 < 5000)
- `sabic` FY2025: very low Latin word count (0 < 5000)
- `sahara-international-petrochemical-co` FY2020: very low Latin word count (0 < 5000)
- `sahara-international-petrochemical-co` FY2020: very low Latin word count (0 < 5000)
- `sahara-international-petrochemical-co` FY2021: very low Latin word count (0 < 5000)
- `sahara-international-petrochemical-co` FY2021: very low Latin word count (0 < 5000)
- `sahara-international-petrochemical-co` FY2022: very low Latin word count (0 < 5000)
- `sahara-international-petrochemical-co` FY2022: very low Latin word count (4214 < 5000)
- `sahara-international-petrochemical-co` FY2022: very low Latin word count (0 < 5000)
- `sahara-international-petrochemical-co` FY2023: very low Latin word count (0 < 5000)
- `sahara-international-petrochemical-co` FY2023: very low Latin word count (0 < 5000)
- `sahara-international-petrochemical-co` FY2024: very low Latin word count (0 < 5000)
- `sahara-international-petrochemical-co` FY2024: very low Latin word count (0 < 5000)
- `sahara-international-petrochemical-co` FY2025: very low Latin word count (0 < 5000)
- `sahara-international-petrochemical-co` FY2025: very low Latin word count (0 < 5000)
- `salam-international-investment` FY2020: very low Latin word count (0 < 5000)
- `salam-international-investment` FY2020: very low Latin word count (4044 < 5000)
- `salam-international-investment` FY2020: very low Latin word count (0 < 5000)
- `salam-international-investment` FY2021: very low Latin word count (0 < 5000)
- `salam-international-investment` FY2021: very low Latin word count (3645 < 5000)
- `salam-international-investment` FY2021: very low Latin word count (0 < 5000)
- `salam-international-investment` FY2022: very low Latin word count (0 < 5000)
- `salam-international-investment` FY2022: very low Latin word count (0 < 5000)
- `salam-international-investment` FY2023: very low Latin word count (0 < 5000)
- `salam-international-investment` FY2023: very low Latin word count (0 < 5000)
- `salam-international-investment` FY2024: very low Latin word count (0 < 5000)
- `salam-international-investment` FY2024: very low Latin word count (0 < 5000)
- `salam-international-investment` FY2025: very low Latin word count (0 < 5000)
- `salam-international-investment` FY2025: very low Latin word count (0 < 5000)
- `saudi-airlines-catering-company-catrion` FY2020: very low Latin word count (0 < 5000)
- `saudi-airlines-catering-company-catrion` FY2020: very low Latin word count (0 < 5000)
- `saudi-airlines-catering-company-catrion` FY2021: very low Latin word count (0 < 5000)
- `saudi-airlines-catering-company-catrion` FY2021: very low Latin word count (0 < 5000)
- `saudi-airlines-catering-company-catrion` FY2022: very low Latin word count (0 < 5000)
- `saudi-airlines-catering-company-catrion` FY2022: very low Latin word count (0 < 5000)
- `saudi-airlines-catering-company-catrion` FY2023: very low Latin word count (0 < 5000)
- `saudi-airlines-catering-company-catrion` FY2023: very low Latin word count (0 < 5000)
- `saudi-airlines-catering-company-catrion` FY2024: very low Latin word count (0 < 5000)
- `saudi-airlines-catering-company-catrion` FY2024: very low Latin word count (0 < 5000)
- `saudi-airlines-catering-company-catrion` FY2025: very low Latin word count (0 < 5000)
- `saudi-airlines-catering-company-catrion` FY2025: very low Latin word count (0 < 5000)
- `saudi-arabian-fertilizer-company` FY2020: very low Latin word count (0 < 5000)
- `saudi-arabian-fertilizer-company` FY2020: very low Latin word count (0 < 5000)
- `saudi-arabian-fertilizer-company` FY2021: very low Latin word count (0 < 5000)
- `saudi-arabian-fertilizer-company` FY2021: very low Latin word count (0 < 5000)
- `saudi-arabian-fertilizer-company` FY2022: very low Latin word count (0 < 5000)
- `saudi-arabian-fertilizer-company` FY2022: very low Latin word count (0 < 5000)
- `saudi-arabian-fertilizer-company` FY2023: very low Latin word count (0 < 5000)
- `saudi-arabian-fertilizer-company` FY2023: very low Latin word count (0 < 5000)
- `saudi-arabian-fertilizer-company` FY2024: very low Latin word count (0 < 5000)
- `saudi-arabian-fertilizer-company` FY2024: very low Latin word count (0 < 5000)
- `saudi-arabian-fertilizer-company` FY2025: very low Latin word count (0 < 5000)
- `saudi-arabian-fertilizer-company` FY2025: very low Latin word count (0 < 5000)
- `saudi-aramco` FY2020: very low Latin word count (0 < 5000)
- `saudi-aramco` FY2020: very low Latin word count (0 < 5000)
- `saudi-aramco` FY2021: very low Latin word count (0 < 5000)
- `saudi-aramco` FY2021: very low Latin word count (0 < 5000)
- `saudi-aramco` FY2022: very low Latin word count (0 < 5000)
- `saudi-aramco` FY2022: very low Latin word count (0 < 5000)
- `saudi-aramco` FY2023: very low Latin word count (0 < 5000)
- `saudi-aramco` FY2023: very low Latin word count (0 < 5000)
- `saudi-aramco` FY2024: very low Latin word count (0 < 5000)
- `saudi-aramco` FY2024: very low Latin word count (0 < 5000)
- `saudi-aramco` FY2025: very low Latin word count (0 < 5000)
- `saudi-aramco` FY2025: very low Latin word count (0 < 5000)
- `saudi-cement` FY2020: very low Latin word count (0 < 5000)
- `saudi-cement` FY2020: very low Latin word count (0 < 5000)
- `saudi-cement` FY2021: very low Latin word count (0 < 5000)
- `saudi-cement` FY2021: very low Latin word count (0 < 5000)
- `saudi-cement` FY2022: very low Latin word count (0 < 5000)
- `saudi-cement` FY2022: very low Latin word count (0 < 5000)
- `saudi-cement` FY2023: very low Latin word count (0 < 5000)
- `saudi-cement` FY2023: very low Latin word count (0 < 5000)
- `saudi-cement` FY2024: very low Latin word count (0 < 5000)
- `saudi-cement` FY2024: very low Latin word count (0 < 5000)
- `saudi-cement` FY2025: very low Latin word count (0 < 5000)
- `saudi-cement` FY2025: very low Latin word count (0 < 5000)
- `saudi-industrial-investment-group` FY2020: very low Latin word count (0 < 5000)
- `saudi-industrial-investment-group` FY2020: very low Latin word count (0 < 5000)
- `saudi-industrial-investment-group` FY2021: very low Latin word count (0 < 5000)
- `saudi-industrial-investment-group` FY2021: very low Latin word count (0 < 5000)
- `saudi-industrial-investment-group` FY2022: very low Latin word count (0 < 5000)
- `saudi-industrial-investment-group` FY2022: very low Latin word count (0 < 5000)
- `saudi-industrial-investment-group` FY2023: very low Latin word count (0 < 5000)
- `saudi-industrial-investment-group` FY2023: very low Latin word count (0 < 5000)
- `saudi-industrial-investment-group` FY2024: very low Latin word count (0 < 5000)
- `saudi-industrial-investment-group` FY2024: very low Latin word count (0 < 5000)
- `saudi-industrial-investment-group` FY2025: very low Latin word count (0 < 5000)
- `saudi-industrial-investment-group` FY2025: very low Latin word count (0 < 5000)
- `saudi-telecom-company` FY2020: very low Latin word count (0 < 5000)
- `saudi-telecom-company` FY2020: very low Latin word count (0 < 5000)
- `saudi-telecom-company` FY2021: very low Latin word count (0 < 5000)
- `saudi-telecom-company` FY2021: very low Latin word count (0 < 5000)
- `saudi-telecom-company` FY2022: very low Latin word count (0 < 5000)
- `saudi-telecom-company` FY2022: very low Latin word count (0 < 5000)
- `saudi-telecom-company` FY2023: very low Latin word count (0 < 5000)
- `saudi-telecom-company` FY2023: very low Latin word count (0 < 5000)
- `saudi-telecom-company` FY2024: very low Latin word count (0 < 5000)
- `saudi-telecom-company` FY2024: very low Latin word count (0 < 5000)
- `saudi-telecom-company` FY2025: very low Latin word count (0 < 5000)
- `saudi-telecom-company` FY2025: very low Latin word count (0 < 5000)
- `savola-group` FY2020: very low Latin word count (0 < 5000)
- `savola-group` FY2020: very low Latin word count (0 < 5000)
- `savola-group` FY2021: very low Latin word count (0 < 5000)
- `savola-group` FY2021: very low Latin word count (0 < 5000)
- `savola-group` FY2022: very low Latin word count (0 < 5000)
- `savola-group` FY2022: very low Latin word count (0 < 5000)
- `savola-group` FY2023: very low Latin word count (0 < 5000)
- `savola-group` FY2023: very low Latin word count (0 < 5000)
- `savola-group` FY2024: very low Latin word count (0 < 5000)
- `savola-group` FY2024: very low Latin word count (0 < 5000)
- `savola-group` FY2025: very low Latin word count (0 < 5000)
- `savola-group` FY2025: very low Latin word count (0 < 5000)
- `sohar-international-bank` FY2020: very low Latin word count (0 < 5000)
- `sohar-international-bank` FY2020: very low Latin word count (0 < 5000)
- `sohar-international-bank` FY2021: very low Latin word count (0 < 5000)
- `sohar-international-bank` FY2021: very low Latin word count (0 < 5000)
- `sohar-international-bank` FY2022: very low Latin word count (0 < 5000)
- `sohar-international-bank` FY2022: very low Latin word count (0 < 5000)
- `sohar-international-bank` FY2023: very low Latin word count (0 < 5000)
- `sohar-international-bank` FY2023: very low Latin word count (0 < 5000)
- `sohar-international-bank` FY2024: very low Latin word count (0 < 5000)
- `sohar-international-bank` FY2024: very low Latin word count (0 < 5000)
- `sohar-international-bank` FY2025: very low Latin word count (0 < 5000)
- `sohar-international-bank` FY2025: very low Latin word count (0 < 5000)
- `tamdeen-real-estate-company` FY2020: very low Latin word count (0 < 5000)
- `tamdeen-real-estate-company` FY2020: very low Latin word count (0 < 5000)
- `tamdeen-real-estate-company` FY2020: very low Latin word count (0 < 5000)
- `tamdeen-real-estate-company` FY2021: very low Latin word count (0 < 5000)
- `tamdeen-real-estate-company` FY2021: very low Latin word count (0 < 5000)
- `tamdeen-real-estate-company` FY2022: very low Latin word count (0 < 5000)
- `tamdeen-real-estate-company` FY2022: very low Latin word count (0 < 5000)
- `tamdeen-real-estate-company` FY2023: very low Latin word count (0 < 5000)
- `tamdeen-real-estate-company` FY2023: very low Latin word count (0 < 5000)
- `tamdeen-real-estate-company` FY2023: very low Latin word count (0 < 5000)
- `tamdeen-real-estate-company` FY2024: very low Latin word count (0 < 5000)
- `tamdeen-real-estate-company` FY2024: very low Latin word count (0 < 5000)
- `tamdeen-real-estate-company` FY2024: very low Latin word count (0 < 5000)
- `tamdeen-real-estate-company` FY2025: very low Latin word count (0 < 5000)
- `tamdeen-real-estate-company` FY2025: very low Latin word count (0 < 5000)
- `tamdeen-real-estate-company` FY2025: very low Latin word count (0 < 5000)
- `the-national-bank-of-ras-al-khaimah` FY2020: very low Latin word count (0 < 5000)
- `the-national-bank-of-ras-al-khaimah` FY2020: very low Latin word count (0 < 5000)
- `the-national-bank-of-ras-al-khaimah` FY2020: very low Latin word count (0 < 5000)
- `the-national-bank-of-ras-al-khaimah` FY2021: very low Latin word count (0 < 5000)
- `the-national-bank-of-ras-al-khaimah` FY2021: very low Latin word count (0 < 5000)
- `the-national-bank-of-ras-al-khaimah` FY2022: very low Latin word count (0 < 5000)
- `the-national-bank-of-ras-al-khaimah` FY2022: very low Latin word count (0 < 5000)
- `the-national-bank-of-ras-al-khaimah` FY2022: very low Latin word count (0 < 5000)
- `the-national-bank-of-ras-al-khaimah` FY2023: very low Latin word count (0 < 5000)
- `the-national-bank-of-ras-al-khaimah` FY2023: very low Latin word count (0 < 5000)
- `the-national-bank-of-ras-al-khaimah` FY2024: very low Latin word count (0 < 5000)
- `the-national-bank-of-ras-al-khaimah` FY2024: very low Latin word count (0 < 5000)
- `the-national-bank-of-ras-al-khaimah` FY2025: very low Latin word count (0 < 5000)
- `the-national-bank-of-ras-al-khaimah` FY2025: very low Latin word count (0 < 5000)
- `the-saudi-national-bank` FY2020: very low Latin word count (0 < 5000)
- `the-saudi-national-bank` FY2020: very low Latin word count (0 < 5000)
- `the-saudi-national-bank` FY2021: very low Latin word count (0 < 5000)
- `the-saudi-national-bank` FY2021: very low Latin word count (0 < 5000)
- `the-saudi-national-bank` FY2022: very low Latin word count (0 < 5000)
- `the-saudi-national-bank` FY2022: very low Latin word count (0 < 5000)
- `the-saudi-national-bank` FY2023: very low Latin word count (0 < 5000)
- `the-saudi-national-bank` FY2023: very low Latin word count (0 < 5000)
- `the-saudi-national-bank` FY2024: very low Latin word count (0 < 5000)
- `the-saudi-national-bank` FY2024: very low Latin word count (0 < 5000)
- `the-saudi-national-bank` FY2025: very low Latin word count (0 < 5000)
- `the-saudi-national-bank` FY2025: very low Latin word count (0 < 5000)
- `yanbu-cement-company` FY2020: very low Latin word count (0 < 5000)
- `yanbu-cement-company` FY2020: very low Latin word count (0 < 5000)
- `yanbu-cement-company` FY2021: very low Latin word count (0 < 5000)
- `yanbu-cement-company` FY2021: very low Latin word count (0 < 5000)
- `yanbu-cement-company` FY2022: very low Latin word count (0 < 5000)
- `yanbu-cement-company` FY2022: very low Latin word count (0 < 5000)
- `yanbu-cement-company` FY2023: very low Latin word count (0 < 5000)
- `yanbu-cement-company` FY2023: very low Latin word count (0 < 5000)
- `yanbu-cement-company` FY2024: very low Latin word count (0 < 5000)
- `yanbu-cement-company` FY2024: very low Latin word count (0 < 5000)
- `yanbu-cement-company` FY2025: very low Latin word count (0 < 5000)
- `yanbu-cement-company` FY2025: very low Latin word count (0 < 5000)
- `yanbu-national-petrochemical` FY2020: very low Latin word count (0 < 5000)
- `yanbu-national-petrochemical` FY2020: very low Latin word count (0 < 5000)
- `yanbu-national-petrochemical` FY2021: very low Latin word count (0 < 5000)
- `yanbu-national-petrochemical` FY2021: very low Latin word count (0 < 5000)
- `yanbu-national-petrochemical` FY2022: very low Latin word count (0 < 5000)
- `yanbu-national-petrochemical` FY2022: very low Latin word count (0 < 5000)
- `yanbu-national-petrochemical` FY2023: very low Latin word count (0 < 5000)
- `yanbu-national-petrochemical` FY2023: very low Latin word count (0 < 5000)
- `yanbu-national-petrochemical` FY2024: very low Latin word count (0 < 5000)
- `yanbu-national-petrochemical` FY2024: very low Latin word count (0 < 5000)
- `yanbu-national-petrochemical` FY2025: very low Latin word count (0 < 5000)
- `yanbu-national-petrochemical` FY2025: very low Latin word count (0 < 5000)
- `zain-mobile-telecommunications-company` FY2020: very low Latin word count (0 < 5000)
- `zain-mobile-telecommunications-company` FY2020: very low Latin word count (0 < 5000)
- `zain-mobile-telecommunications-company` FY2021: very low Latin word count (0 < 5000)
- `zain-mobile-telecommunications-company` FY2021: very low Latin word count (0 < 5000)
- `zain-mobile-telecommunications-company` FY2021: very low Latin word count (0 < 5000)
- `zain-mobile-telecommunications-company` FY2022: very low Latin word count (0 < 5000)
- `zain-mobile-telecommunications-company` FY2022: very low Latin word count (0 < 5000)
- `zain-mobile-telecommunications-company` FY2023: very low Latin word count (0 < 5000)
- `zain-mobile-telecommunications-company` FY2023: very low Latin word count (0 < 5000)
- `zain-mobile-telecommunications-company` FY2024: very low Latin word count (0 < 5000)
- `zain-mobile-telecommunications-company` FY2024: very low Latin word count (0 < 5000)
- `zain-mobile-telecommunications-company` FY2025: very low Latin word count (0 < 5000)
- `zain-mobile-telecommunications-company` FY2025: very low Latin word count (0 < 5000)
