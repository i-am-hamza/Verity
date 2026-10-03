# Processing QA

Generated 2026-10-02T17:05:47+00:00.

Reports processed: **172** (threshold-flagged: **4**, IQR-flagged: **1**).

IQR cohort = fiscal year. A composite more than 3xIQR from Q1/Q3 of its cohort is flagged as a processing outlier (Report.processing_review_status = needs_review). Cohorts with fewer than 5 scored reports are labelled low-confidence.

## Cohort IQR bounds

| FY | n | median | Q1 | Q3 | lower | upper | note |
|---|---|---|---|---|---|---|---|
| 2020 | 14 | 1.071 | 0.717 | 2.136 | -3.540 | 6.393 |  |
| 2021 | 21 | 1.953 | 1.169 | 2.651 | -3.274 | 7.094 |  |
| 2022 | 38 | 2.099 | 1.144 | 3.064 | -4.616 | 8.824 |  |
| 2023 | 29 | 3.079 | 0.907 | 3.975 | -8.299 | 13.181 |  |
| 2024 | 32 | 3.021 | 1.657 | 4.776 | -7.702 | 14.134 |  |
| 2025 | 37 | 3.427 | 2.343 | 5.238 | -6.344 | 13.924 |  |

## Per-report audit

| slug | FY | status | pages | Latin words | OCR frac | Ar pages | ToC pages | repeat lines | FS start | matches | all-mode extra | composite | flag |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `abdullah-al-othaim-markets` | 2022 | scored | 72 | 19305 | 0.03 | 0 | — | 69 | — | 85 | 5 | 4.491 |  |
| `abdullah-al-othaim-markets` | 2023 | scored | 62 | 21600 | 0.00 | 0 | — | 125 | — | 75 | 5 | 3.519 |  |
| `abu-dhabi-commercial-bank` | 2021 | scored | 149 | 92890 | 0.01 | 0 | — | 477 | 96 | 236 | 16 | 2.585 |  |
| `abu-dhabi-commercial-bank` | 2024 | scored | 202 | 126004 | 0.00 | 0 | — | 190 | 128 | 648 | 33 | 5.300 |  |
| `abu-dhabi-commercial-bank` | 2025 | scored | 203 | 129909 | 0.00 | 0 | — | 94 | 149 | 760 | 24 | 5.971 |  |
| `abu-dhabi-national-energy-company` | 2020 | scored | 124 | 49249 | 0.00 | 0 | — | 712 | 52 | 34 | 4 | 0.717 |  |
| `abu-dhabi-national-energy-company` | 2022 | scored | 98 | 57994 | 0.00 | 0 | — | 262 | 46 | 156 | 8 | 2.742 |  |
| `abu-dhabi-national-energy-company` | 2023 | scored | 129 | 65744 | 0.00 | 0 | — | 1110 | 72 | 198 | 7 | 3.079 |  |
| `abu-dhabi-national-energy-company` | 2024 | scored | 305 | 105694 | 0.00 | 1 | — | 2728 | 182 | 503 | 15 | 4.805 |  |
| `abu-dhabi-national-energy-company` | 2025 | scored | 326 | 119153 | 0.00 | 0 | — | 3022 | 189 | 662 | 15 | 5.580 |  |
| `abu-dhabi-national-oil-company-for-distribution` | 2020 | scored | 61 | 37903 | 0.02 | 0 | — | 106 | 38 | 45 | 10 | 1.222 |  |
| `abu-dhabi-national-oil-company-for-distribution` | 2021 | scored | 66 | 38683 | 0.03 | 0 | — | 86 | 44 | 68 | 9 | 1.812 |  |
| `abu-dhabi-national-oil-company-for-distribution` | 2022 | scored | 67 | 40706 | 0.01 | 0 | — | 144 | 46 | 137 | 8 | 3.417 |  |
| `abu-dhabi-national-oil-company-for-distribution` | 2023 | scored | 77 | 48813 | 0.01 | 0 | — | 202 | 52 | 167 | 6 | 3.464 |  |
| `abu-dhabi-national-oil-company-for-distribution` | 2024 | scored | 141 | 58952 | 0.00 | 0 | — | 142 | 111 | 373 | 13 | 6.373 |  |
| `al-rajhi-bank` | 2020 | scored | 123 | 79028 | 0.05 | 0 | — | 167 | 72 | 251 | 5 | 3.244 |  |
| `al-rajhi-bank` | 2021 | scored | 310 | 89613 | 0.02 | 0 | 6,7 | 4921 | 179 | 128 | 3 | 1.461 |  |
| `al-rajhi-bank` | 2021 | scored | 310 | 89613 | 0.02 | 0 | 6,7 | 2850 | 179 | 261 | 3 | 2.952 |  |
| `al-rajhi-bank` | 2021 | scored | 310 | 89613 | 0.02 | 0 | 6,7 | 2850 | 179 | 261 | 3 | 2.952 |  |
| `al-rajhi-bank` | 2022 | scored | 159 | 94516 | 0.01 | 0 | 4 | 6658 | 91 | 169 | 3 | 1.798 |  |
| `al-rajhi-bank` | 2022 | scored | 159 | 94516 | 0.01 | 0 | 4 | 2641 | 91 | 335 | 3 | 3.561 |  |
| `al-rajhi-bank` | 2022 | scored | 159 | 94516 | 0.01 | 0 | 4 | 2641 | 91 | 338 | 3 | 3.599 |  |
| `al-rajhi-bank` | 2023 | scored | 368 | 105467 | 0.01 | 0 | 6,7,55 | 4240 | 247 | 215 | 3 | 2.039 |  |
| `al-rajhi-bank` | 2023 | scored | 368 | 105467 | 0.01 | 0 | 6,7,55 | 3111 | 247 | 423 | 3 | 4.016 |  |
| `al-rajhi-bank` | 2023 | scored | 368 | 105467 | 0.01 | 0 | 6,7,55 | 3111 | 247 | 430 | 3 | 4.096 |  |
| `al-rajhi-bank` | 2025 | scored | 432 | 134665 | 0.01 | 1 | 6,7 | 6380 | 282 | 417 | 45 | 3.261 |  |
| `al-rajhi-bank` | 2025 | scored | 432 | 134665 | 0.01 | 1 | 6,7 | 4768 | 282 | 664 | 45 | 5.116 |  |
| `al-rajhi-bank` | 2025 | scored | 432 | 134665 | 0.01 | 1 | 6,7 | 4768 | 282 | 692 | 45 | 5.360 |  |
| `aldar-properties-pjsc` | 2024 | scored | 440 | 153277 | 0.00 | 0 | — | 2221 | 132 | 134 | 0 | 0.864 |  |
| `alinma-bank` | 2021 | scored | 103 | 61473 | 0.00 | 0 | 5 | 5593 | 58 | 39 | 0 | 0.646 |  |
| `alinma-bank` | 2021 | scored | 103 | 61473 | 0.00 | 0 | 5 | 645 | 58 | 70 | 0 | 1.153 |  |
| `alinma-bank` | 2021 | scored | 103 | 61473 | 0.00 | 0 | 5 | 645 | 58 | 71 | 0 | 1.171 |  |
| `alinma-bank` | 2022 | scored | 196 | 67668 | 0.01 | 0 | — | 5301 | 116 | 74 | 7 | 1.120 |  |
| `alinma-bank` | 2022 | scored | 196 | 67668 | 0.01 | 0 | — | 1437 | 116 | 112 | 7 | 1.682 |  |
| `alinma-bank` | 2022 | scored | 196 | 67668 | 0.01 | 0 | — | 1437 | 116 | 112 | 7 | 1.682 |  |
| `alinma-bank` | 2023 | scored | 260 | 70844 | 0.03 | 1 | 5 | 2885 | 150 | 155 | 10 | 2.266 |  |
| `alinma-bank` | 2023 | scored | 260 | 70844 | 0.03 | 1 | 5 | 539 | 150 | 272 | 10 | 3.918 |  |
| `alinma-bank` | 2023 | scored | 260 | 70844 | 0.03 | 1 | 5 | 539 | 150 | 273 | 10 | 3.934 |  |
| `alinma-bank` | 2024 | scored | 155 | 81984 | 0.01 | 0 | — | 5004 | 92 | 165 | 12 | 2.115 |  |
| `alinma-bank` | 2024 | scored | 155 | 81984 | 0.01 | 0 | — | 1051 | 92 | 353 | 12 | 4.455 |  |
| `alinma-bank` | 2024 | scored | 155 | 81984 | 0.01 | 0 | — | 1051 | 92 | 355 | 12 | 4.483 |  |
| `alinma-bank` | 2025 | scored | 176 | 100307 | 0.00 | 0 | — | 4020 | 120 | 273 | 10 | 2.840 |  |
| `alinma-bank` | 2025 | scored | 176 | 100307 | 0.00 | 0 | — | 1279 | 120 | 479 | 10 | 4.923 |  |
| `alinma-bank` | 2025 | scored | 176 | 100307 | 0.00 | 0 | — | 1279 | 120 | 482 | 10 | 4.959 |  |
| `almarai` | 2020 | scored | 190 | 53554 | 0.01 | 0 | — | 526 | 117 | 113 | 9 | 2.136 |  |
| `almarai` | 2021 | scored | 192 | 54167 | 0.04 | 0 | — | 96 | 118 | 127 | 8 | 2.361 |  |
| `almarai` | 2022 | scored | 195 | 57061 | 0.03 | 0 | — | 155 | 124 | 120 | 7 | 2.124 |  |
| `almarai` | 2024 | scored | 202 | 58655 | 0.00 | 0 | — | 499 | 135 | 173 | 6 | 2.968 |  |
| `almarai` | 2025 | scored | 275 | 74226 | 0.00 | 0 | — | 2183 | 151 | 256 | 2 | 3.427 |  |
| `aluminium-bahrain-alba` | 2020 | scored | 106 | 35940 | 0.04 | 1 | — | 305 | 48 | 33 | 1 | 0.921 |  |
| `aluminium-bahrain-alba` | 2021 | scored | 132 | 45135 | 0.04 | 0 | — | 654 | 67 | 63 | 2 | 1.402 |  |
| `aluminium-bahrain-alba` | 2022 | scored | 67 | 43331 | 0.00 | 0 | — | 318 | 35 | 101 | 5 | 2.368 |  |
| `aluminium-bahrain-alba` | 2024 | scored | 69 | 39520 | 0.00 | 0 | — | 355 | 40 | 104 | 7 | 2.664 |  |
| `aluminium-bahrain-alba` | 2025 | scored | 73 | 44799 | 0.00 | 0 | — | 234 | 42 | 197 | 14 | 4.464 |  |
| `bahrain-telecommunications-beyon` | 2020 | scored | 138 | 42770 | 0.01 | 0 | — | 426 | 86 | 60 | 5 | 1.438 |  |
| `bahrain-telecommunications-beyon` | 2021 | scored | 60 | 37129 | 0.02 | 0 | — | 499 | 34 | 25 | 0 | 0.679 |  |
| `bahrain-telecommunications-beyon` | 2022 | scored | 62 | 38474 | 0.00 | 0 | — | 340 | 37 | 45 | 3 | 1.188 |  |
| `bahrain-telecommunications-beyon` | 2023 | scored | 128 | 41444 | 0.00 | 0 | — | 469 | 78 | 45 | 5 | 1.124 |  |
| `bahrain-telecommunications-beyon` | 2024 | scored | 69 | 41908 | 0.00 | 0 | — | 233 | 44 | 90 | 4 | 2.200 |  |
| `baladna` | 2022 | scored | 176 | 49131 | 0.01 | 0 | — | 171 | 124 | 201 | 14 | 4.360 |  |
| `baladna` | 2023 | scored | 96 | 59814 | 0.01 | 0 | — | 413 | 70 | 281 | 16 | 4.904 |  |
| `baladna` | 2025 | scored | 117 | 71770 | 0.01 | 0 | — | 205 | 88 | 327 | 20 | 4.781 |  |
| `bank-albilad` | 2024 | scored | 132 | 37497 | 0.01 | 0 | — | 1166 | 40 | 19 | 1 | 0.504 |  |
| `bank-albilad` | 2024 | scored | 132 | 37497 | 0.01 | 0 | — | 316 | 40 | 37 | 1 | 1.016 |  |
| `bank-albilad` | 2024 | scored | 132 | 37497 | 0.01 | 0 | — | 316 | 40 | 38 | 1 | 1.045 |  |
| `bank-muscat-bkmb` | 2025 | scored | 286 | 95131 | 0.01 | 0 | — | 9483 | 163 | 126 | 4 | 1.357 |  |
| `bank-muscat-bkmb` | 2025 | scored | 286 | 95131 | 0.01 | 0 | — | 939 | 163 | 184 | 4 | 1.977 |  |
| `bank-muscat-bkmb` | 2025 | scored | 286 | 95131 | 0.01 | 0 | — | 939 | 163 | 189 | 4 | 2.035 |  |
| `bupa-arabia-for-cooperative-insurance-company` | 2022 | scored | 53 | 14737 | 0.04 | 0 | — | 570 | 26 | 7 | 4 | 0.509 |  |
| `bupa-arabia-for-cooperative-insurance-company` | 2022 | scored | 53 | 14737 | 0.04 | 0 | — | 186 | 26 | 9 | 4 | 0.645 |  |
| `bupa-arabia-for-cooperative-insurance-company` | 2022 | scored | 53 | 14737 | 0.04 | 0 | — | 186 | 26 | 9 | 4 | 0.645 |  |
| `dar-al-arkan-real-estate-development-company` | 2024 | scored | 127 | 44878 | 0.02 | 0 | — | 124 | 88 | 162 | 13 | 3.652 |  |
| `dubai-investment` | 2022 | scored | 130 | 42071 | 0.22 | 0 | — | 1578 | 34 | 30 | 0 | 0.713 |  |
| `dubai-investment` | 2022 | scored | 130 | 42071 | 0.22 | 0 | — | 180 | 34 | 37 | 0 | 0.879 |  |
| `dubai-investment` | 2022 | scored | 130 | 42071 | 0.22 | 0 | — | 180 | 34 | 37 | 0 | 0.879 |  |
| `dubai-islamic-bank` | 2021 | uploaded | 207 | 0 | 0.48 | 0 | — | 0 | — | 0 | — | — | threshold |
| `dubai-islamic-bank` | 2022 | scored | 209 | 67232 | 0.02 | 0 | — | 384 | 59 | 32 | 2 | 0.492 |  |
| `dubai-islamic-bank` | 2023 | scored | 236 | 75850 | 0.05 | 1 | — | 268 | 61 | 26 | 0 | 0.344 |  |
| `emaar-properties` | 2020 | scored | 116 | 16751 | 0.04 | 0 | — | 212 | — | 6 | 2 | 0.376 |  |
| `emaar-properties` | 2021 | scored | 117 | 71389 | 0.00 | 0 | — | 271 | 74 | 192 | 4 | 2.716 |  |
| `emaar-properties` | 2022 | scored | 110 | 65967 | 0.01 | 0 | — | 1783 | 72 | 177 | 3 | 2.679 |  |
| `emaar-properties` | 2023 | scored | 117 | 70828 | 0.02 | 0 | — | 216 | 81 | 275 | 6 | 3.885 |  |
| `emaar-properties` | 2024 | scored | 197 | 75154 | 0.00 | 0 | — | 1906 | 137 | 574 | 4 | 7.666 |  |
| `emaar-properties` | 2025 | scored | 223 | 86175 | 0.00 | 0 | — | 2705 | 159 | 666 | 4 | 7.681 |  |
| `emirates-nbd-pjsc` | 2021 | scored | 33 | 17005 | 0.00 | 0 | — | 133 | — | 41 | 2 | 2.440 |  |
| `emirates-nbd-pjsc` | 2023 | scored | 109 | 201 | 0.01 | 109 | — | 1875 | 62 | 0 | 0 | 0.000 | threshold |
| `emirates-nbd-pjsc` | 2023 | scored | 109 | 201 | 0.01 | 109 | — | 171 | 62 | 0 | 0 | 0.000 | threshold |
| `emirates-nbd-pjsc` | 2023 | scored | 109 | 201 | 0.01 | 109 | — | 171 | 62 | 0 | 0 | 0.000 | threshold |
| `emirates-nbd-pjsc` | 2023 | scored | 109 | 77713 | 0.01 | 0 | — | 281 | 71 | 326 | 19 | 4.308 |  |
| `emirates-nbd-pjsc` | 2024 | scored | 121 | 85833 | 0.00 | 0 | — | 277 | 84 | 446 | 13 | 5.307 |  |
| `emirates-nbd-pjsc` | 2025 | scored | 132 | 89271 | 0.00 | 0 | — | 256 | 92 | 575 | 26 | 6.575 |  |
| `emirates-telecom-etisalat-group` | 2020 | scored | 96 | 70562 | 0.00 | 0 | — | 285 | 54 | 63 | 0 | 0.877 |  |
| `emirates-telecom-etisalat-group` | 2021 | scored | 101 | 67953 | 0.00 | 0 | — | 367 | 57 | 80 | 0 | 1.168 |  |
| `emirates-telecom-etisalat-group` | 2022 | scored | 81 | 58522 | 0.00 | 0 | — | 494 | 44 | 133 | 1 | 2.329 |  |
| `emirates-telecom-etisalat-group` | 2023 | scored | 144 | 96389 | 0.01 | 0 | — | 279 | 105 | 584 | 3 | 6.130 |  |
| `first-abu-dhabi-bank` | 2020 | scored | 204 | 70734 | 0.01 | 0 | — | 114 | 53 | 118 | 12 | 1.715 |  |
| `first-abu-dhabi-bank` | 2021 | scored | 74 | 38528 | 0.01 | 0 | — | 64 | — | 283 | 14 | 7.511 | IQR-outlier |
| `first-abu-dhabi-bank` | 2023 | scored | 134 | 79002 | 0.01 | 0 | — | 1539 | 59 | 312 | 5 | 4.081 |  |
| `first-abu-dhabi-bank` | 2024 | scored | 181 | 97344 | 0.01 | 0 | — | 347 | 107 | 534 | 10 | 5.705 |  |
| `first-abu-dhabi-bank` | 2025 | scored | 191 | 105731 | 0.00 | 0 | — | 2299 | 119 | 331 | 16 | 3.282 |  |
| `first-abu-dhabi-bank` | 2025 | scored | 191 | 105731 | 0.00 | 0 | — | 461 | 119 | 718 | 17 | 7.006 |  |
| `first-abu-dhabi-bank` | 2025 | scored | 191 | 105731 | 0.00 | 0 | — | 461 | 119 | 734 | 17 | 7.177 |  |
| `gulf-international-services` | 2021 | scored | 80 | 26328 | 0.00 | 0 | — | 78 | 30 | 4 | 0 | 0.148 |  |
| `gulf-international-services` | 2022 | scored | 105 | 29905 | 0.02 | 1 | — | 140 | 67 | 64 | 5 | 2.468 |  |
| `gulf-international-services` | 2023 | scored | 82 | 31748 | 0.01 | 0 | — | 40 | 33 | 3 | 0 | 0.098 |  |
| `gulf-international-services` | 2024 | scored | 98 | 31976 | 0.04 | 0 | — | 40 | 36 | 7 | 0 | 0.216 |  |
| `industries-qatar` | 2020 | scored | 92 | 27923 | 0.01 | 0 | 5 | 91 | 37 | 3 | 0 | 0.111 |  |
| `industries-qatar` | 2021 | scored | 84 | 27005 | 0.00 | 0 | 5 | 250 | 46 | 52 | 4 | 2.066 |  |
| `industries-qatar` | 2022 | scored | 86 | 29917 | 0.00 | 0 | — | 255 | 43 | 56 | 6 | 1.999 |  |
| `industries-qatar` | 2023 | scored | 80 | 30251 | 0.01 | 0 | — | 39 | 35 | 8 | 0 | 0.264 |  |
| `industries-qatar` | 2024 | scored | 102 | 32830 | 0.06 | 0 | — | 45 | 44 | 14 | 0 | 0.436 |  |
| `industries-qatar` | 2025 | scored | 112 | 33826 | 0.04 | 2 | — | 46 | 42 | 19 | 0 | 0.559 |  |
| `jarir-marketing-co` | 2025 | scored | 43 | 17157 | 0.05 | 0 | — | 129 | — | 87 | 1 | 5.112 |  |
| `kuwait-finance-house` | 2022 | scored | 102 | 68340 | 0.02 | 1 | — | 3759 | 68 | 140 | 6 | 2.073 |  |
| `kuwait-finance-house` | 2022 | scored | 102 | 68340 | 0.02 | 1 | — | 932 | 68 | 182 | 6 | 2.689 |  |
| `kuwait-finance-house` | 2022 | scored | 102 | 68340 | 0.02 | 1 | — | 932 | 68 | 183 | 6 | 2.706 |  |
| `kuwait-finance-house` | 2024 | scored | 115 | 66170 | 0.03 | 1 | — | 2685 | 82 | 147 | 6 | 2.238 |  |
| `kuwait-finance-house` | 2024 | scored | 115 | 66170 | 0.03 | 1 | — | 100 | 82 | 193 | 6 | 2.939 |  |
| `kuwait-finance-house` | 2024 | scored | 115 | 66170 | 0.03 | 1 | — | 100 | 82 | 201 | 6 | 3.074 |  |
| `kuwait-finance-house` | 2025 | scored | 120 | 74289 | 0.02 | 0 | — | 2837 | 79 | 144 | 3 | 1.952 |  |
| `kuwait-finance-house` | 2025 | scored | 120 | 74289 | 0.02 | 0 | — | 114 | 79 | 192 | 3 | 2.601 |  |
| `kuwait-finance-house` | 2025 | scored | 120 | 74289 | 0.02 | 0 | — | 114 | 79 | 195 | 3 | 2.645 |  |
| `national-bank-of-kuwait` | 2022 | scored | 192 | 68415 | 0.03 | 2 | — | 2743 | 82 | 115 | 8 | 1.715 |  |
| `national-bank-of-kuwait` | 2022 | scored | 192 | 68415 | 0.03 | 2 | — | 188 | 82 | 199 | 8 | 2.963 |  |
| `national-bank-of-kuwait` | 2022 | scored | 192 | 68415 | 0.03 | 2 | — | 188 | 82 | 205 | 8 | 3.064 |  |
| `national-bank-of-kuwait` | 2023 | scored | 103 | 72019 | 0.00 | 0 | — | 4779 | 47 | 145 | 7 | 2.062 |  |
| `national-bank-of-kuwait` | 2023 | scored | 103 | 72019 | 0.00 | 0 | — | 654 | 47 | 246 | 7 | 3.478 |  |
| `national-bank-of-kuwait` | 2023 | scored | 103 | 72019 | 0.00 | 0 | — | 654 | 47 | 251 | 7 | 3.559 |  |
| `national-bank-of-kuwait` | 2024 | scored | 204 | 72517 | 0.05 | 0 | — | 2699 | 94 | 170 | 5 | 2.471 |  |
| `national-bank-of-kuwait` | 2024 | scored | 204 | 72517 | 0.05 | 0 | — | 201 | 94 | 278 | 5 | 3.971 |  |
| `national-bank-of-kuwait` | 2024 | scored | 204 | 72517 | 0.05 | 0 | — | 201 | 94 | 281 | 5 | 4.018 |  |
| `national-bank-of-kuwait` | 2025 | scored | 226 | 80612 | 0.05 | 2 | — | 2790 | 116 | 247 | 9 | 3.214 |  |
| `national-bank-of-kuwait` | 2025 | scored | 226 | 80612 | 0.05 | 2 | — | 225 | 116 | 420 | 9 | 5.378 |  |
| `national-bank-of-kuwait` | 2025 | scored | 226 | 80612 | 0.05 | 2 | — | 225 | 116 | 423 | 9 | 5.421 |  |
| `national-industrialization-co` | 2022 | scored | 87 | 45501 | 0.01 | 0 | — | 875 | 46 | 59 | 0 | 1.343 |  |
| `oman-telecommunications-company-otel` | 2020 | scored | 154 | 40989 | 0.03 | 1 | — | 148 | 98 | 33 | 1 | 0.810 |  |
| `oman-telecommunications-company-otel` | 2025 | scored | 191 | 55362 | 0.01 | 0 | — | 1890 | 90 | 137 | 1 | 2.478 |  |
| `ooredoo-q-p-s-c` | 2021 | scored | 90 | 77756 | 0.02 | 0 | — | 150 | 55 | 241 | 19 | 3.285 |  |
| `ooredoo-q-p-s-c` | 2022 | scored | 98 | 79478 | 0.01 | 0 | — | 199 | 60 | 238 | 11 | 3.203 |  |
| `ooredoo-q-p-s-c` | 2023 | scored | 77 | 71748 | 0.03 | 0 | — | 244 | 41 | 170 | 13 | 2.563 |  |
| `ooredoo-q-p-s-c` | 2024 | scored | 78 | 71427 | 0.01 | 0 | — | 640 | 39 | 264 | 16 | 3.898 |  |
| `ooredoo-q-p-s-c` | 2025 | scored | 80 | 73146 | 0.01 | 0 | — | 626 | 40 | 298 | 12 | 4.259 |  |
| `qatar-fuel-company-woqod` | 2021 | scored | 77 | 29596 | 0.00 | 0 | — | 282 | 36 | 51 | 5 | 1.953 |  |
| `qatar-fuel-company-woqod` | 2022 | scored | 73 | 29528 | 0.05 | 0 | — | 347 | 37 | 42 | 4 | 1.619 |  |
| `qatar-fuel-company-woqod` | 2024 | scored | 75 | 29219 | 0.00 | 0 | — | 630 | 44 | 73 | 7 | 2.769 |  |
| `qatar-fuel-company-woqod` | 2025 | scored | 79 | 33360 | 0.00 | 0 | — | 257 | 49 | 95 | 1 | 3.150 |  |
| `qatar-gas-transport-co-nakilat` | 2021 | scored | 41 | 27709 | 0.00 | 0 | — | 182 | 17 | 47 | 4 | 1.725 |  |
| `qatar-gas-transport-co-nakilat` | 2022 | scored | 61 | 47737 | 0.03 | 0 | — | 210 | 37 | 216 | 4 | 4.602 |  |
| `qatar-gas-transport-co-nakilat` | 2024 | scored | 65 | 45942 | 0.00 | 0 | — | 104 | 42 | 215 | 7 | 4.747 |  |
| `qatar-gas-transport-co-nakilat` | 2025 | scored | 59 | 47667 | 0.00 | 0 | — | 135 | 39 | 217 | 8 | 4.613 |  |
| `qnb-qatar-national-bank` | 2020 | scored | 84 | 69434 | 0.00 | 0 | 3 | 1258 | 51 | 370 | 22 | 5.643 |  |
| `qnb-qatar-national-bank` | 2022 | scored | 180 | 73312 | 0.03 | 0 | — | 341 | 108 | 506 | 75 | 7.367 |  |
| `qnb-qatar-national-bank` | 2023 | scored | 226 | 92950 | 0.04 | 0 | — | 1147 | 114 | 470 | 28 | 5.318 |  |
| `qnb-qatar-national-bank` | 2024 | scored | 254 | 100968 | 0.02 | 0 | — | 1352 | 129 | 524 | 26 | 5.440 |  |
| `qnb-qatar-national-bank` | 2025 | scored | 283 | 105207 | 0.05 | 2 | — | 1331 | 135 | 505 | 26 | 5.014 |  |
| `rabigh-refining-petrochemical-co` | 2020 | scored | 100 | 20963 | 0.03 | 0 | 4,5 | 190 | 58 | 1 | 0 | 0.048 |  |
| `sabic` | 2020 | scored | 72 | 49586 | 0.01 | 0 | — | 182 | — | 205 | 2 | 4.201 |  |
| `sabic` | 2022 | scored | 69 | 44162 | 0.00 | 0 | — | 171 | — | 300 | 8 | 6.913 |  |
| `sabic` | 2025 | scored | 262 | 96488 | 0.00 | 0 | — | 3970 | 125 | 277 | 12 | 2.903 |  |
| `saudi-aramco` | 2023 | scored | 121 | 97503 | 0.02 | 0 | 3,5,16 | 1907 | 61 | 177 | 5 | 1.881 |  |
| `saudi-industrial-investment-group` | 2022 | scored | 34 | 13060 | 0.06 | 0 | — | 28 | 26 | 13 | 0 | 1.026 |  |
| `saudi-industrial-investment-group` | 2024 | scored | 46 | 12528 | 0.07 | 0 | 5 | 34 | 20 | 8 | 0 | 0.663 |  |
| `saudi-industrial-investment-group` | 2025 | scored | 46 | 12157 | 0.00 | 0 | — | 40 | — | 23 | 0 | 1.941 |  |
| `savola-group` | 2023 | scored | 92 | 62156 | 0.00 | 0 | — | 554 | 40 | 43 | 1 | 0.689 |  |
| `savola-group` | 2024 | scored | 128 | 78651 | 0.00 | 0 | — | 1169 | 38 | 94 | 2 | 1.198 |  |
| `sohar-international-bank` | 2022 | scored | 156 | 103132 | 0.04 | 0 | — | 1021 | 40 | 114 | 10 | 1.144 |  |
| `sohar-international-bank` | 2023 | scored | 143 | 97712 | 0.05 | 0 | — | 944 | 36 | 164 | 10 | 1.743 |  |
| `the-national-bank-of-ras-al-khaimah` | 2021 | scored | 137 | 76873 | 0.03 | 0 | — | 2291 | 50 | 181 | 6 | 2.413 |  |
| `the-saudi-national-bank` | 2025 | scored | 109 | 76995 | 0.00 | 0 | — | 5221 | 60 | 96 | 4 | 1.284 |  |
| `the-saudi-national-bank` | 2025 | scored | 109 | 76995 | 0.00 | 0 | — | 310 | 60 | 164 | 4 | 2.191 |  |
| `the-saudi-national-bank` | 2025 | scored | 109 | 76995 | 0.00 | 0 | — | 310 | 60 | 165 | 4 | 2.207 |  |
| `zain-mobile-telecommunications-company` | 2024 | scored | 93 | 51001 | 0.03 | 0 | — | 257 | 86 | 402 | 41 | 8.053 |  |

## Threshold flags

- `emirates-nbd-pjsc` FY2023: very low Latin word count (201 < 5000); high Arabic ratio (100% of pages > 50%)
- `emirates-nbd-pjsc` FY2023: very low Latin word count (201 < 5000); high Arabic ratio (100% of pages > 50%)
- `emirates-nbd-pjsc` FY2023: very low Latin word count (201 < 5000); high Arabic ratio (100% of pages > 50%)
- `dubai-islamic-bank` FY2021: very low Latin word count (0 < 5000); high OCR ratio (48% > 30%)

## IQR outliers

- `first-abu-dhabi-bank` FY2021: composite 7.511 outside [-3.274, 7.094] for FY2021

## Pipeline-flagged needs_review (non-IQR)

- `dubai-islamic-bank` FY2021: heavily scanned: 48% of 207 pages would need OCR (> 40% cap); skipped to avoid multi-hour run
- `emirates-nbd-pjsc` FY2023: very low Latin word count (201 < 5000); high Arabic ratio (100% of pages > 50%)
- `emirates-nbd-pjsc` FY2023: very low Latin word count (201 < 5000); high Arabic ratio (100% of pages > 50%)
- `emirates-nbd-pjsc` FY2023: very low Latin word count (201 < 5000); high Arabic ratio (100% of pages > 50%)
