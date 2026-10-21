# ESG & Financial Performance Analysis

Reproduces every table, chart and figure in the final analysis from two inputs.

## Run

```bash
python esg_financial_analysis.py \
    --esg verity_esg_scores.xlsx \
    --financials Data_20_10_2026.xlsx \
    --out results/
```

## Inputs

1. `verity_esg_scores.xlsx` — the Verity ESG export (sheet "Scores by year"): one row per company-year with E, S, G, General and composite scores on a 0-100 scale.
2. `Data_20_10_2026.xlsx` — the researcher's financial data (sheet "Ali Data"): one row per company-year with market cap, EPS, leverage, net margin, RoE and RoA.

## Outputs (in `--out`)

| File | Description |
|---|---|
| `ESG_vs_Financials_Results.xlsx` | All tables, ready for the thesis |
| `esg_financials_results.json` | The same results, for the Verity web page |
| `chart_*.png` | Figures |

## Dependencies

```bash
pip install -r requirements.txt
```
