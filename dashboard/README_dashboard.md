# Power BI Dashboard — Income Analysis (Guide)

This folder contains the specification to build a professional Power BI dashboard using `data/renda_brasil_clean.csv`.

## Data Model
Single table: `renda_brasil_clean`

Recommended columns:
- ano (Year)
- uf (State)
- regiao (Region)
- renda_media (Avg income)
- populacao
- salario_minimo
- renda_em_sal_min
- renda_total_estimada

## Recommended Pages

### Page 1 — Overview
**KPIs**
- Avg Income (last year)
- Population-weighted Avg Income (last year)
- Top UF (last year)
- Bottom UF (last year)

**Charts**
- Line: Avg income by year
- Column: Avg income by region (last year)
- Bar: Top 10 UFs by income (last year)

### Page 2 — Inequality & Growth
- Bar: Std Dev of income by UF (Top 10)
- Bar: YoY growth % by UF (Top 10)
- Scatter: Income vs Population (last year)

## DAX Measures (copy/paste)

```DAX
Last Year = MAX('renda_brasil_clean'[ano])

Avg Income (Last Year) =
VAR y = [Last Year]
RETURN CALCULATE(AVERAGE('renda_brasil_clean'[renda_media]), 'renda_brasil_clean'[ano] = y)

Weighted Avg Income (Last Year) =
VAR y = [Last Year]
RETURN
DIVIDE(
    CALCULATE(SUMX('renda_brasil_clean', 'renda_brasil_clean'[renda_media] * 'renda_brasil_clean'[populacao]), 'renda_brasil_clean'[ano] = y),
    CALCULATE(SUM('renda_brasil_clean'[populacao]), 'renda_brasil_clean'[ano] = y)
)

Top UF (Last Year) =
VAR y = [Last Year]
RETURN
CONCATENATEX(
    TOPN(1,
        SUMMARIZE(FILTER('renda_brasil_clean', 'renda_brasil_clean'[ano]=y),
                  'renda_brasil_clean'[uf],
                  "income", AVERAGE('renda_brasil_clean'[renda_media])),
        [income], DESC),
    'renda_brasil_clean'[uf],
    ", "
)

Bottom UF (Last Year) =
VAR y = [Last Year]
RETURN
CONCATENATEX(
    TOPN(1,
        SUMMARIZE(FILTER('renda_brasil_clean', 'renda_brasil_clean'[ano]=y),
                  'renda_brasil_clean'[uf],
                  "income", AVERAGE('renda_brasil_clean'[renda_media])),
        [income], ASC),
    'renda_brasil_clean'[uf],
    ", "
)
```
