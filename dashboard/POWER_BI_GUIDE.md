# Power BI Dashboard — Brazil Income Analysis

This guide describes a professional Power BI dashboard built from `data/brazil_income_clean.csv`.

> The underlying dataset is synthetic and exists only to demonstrate an analytical workflow. Its values do not represent official Brazilian statistics.

## Data model

Single table: `brazil_income_clean`

Recommended columns:

- `year`
- `state_code`
- `region`
- `average_income_brl`
- `population`
- `minimum_wage_brl`
- `income_in_minimum_wages`
- `estimated_total_income_brl`

## Recommended pages

### Page 1 — Overview

**Key performance indicators**

- Average income for the latest year
- Population-weighted average income for the latest year
- Highest-income federative unit
- Lowest-income federative unit

**Charts**

- Line chart: average income by year
- Column chart: average income by region for the latest year
- Bar chart: top 10 federative units by income for the latest year

### Page 2 — Inequality and growth

- Bar chart: top 10 federative units by income standard deviation
- Bar chart: top 10 federative units by year-over-year growth
- Scatter plot: income versus population for the latest year

## DAX measures

```DAX
Latest Year = MAX('brazil_income_clean'[year])

Average Income (Latest Year) =
VAR selected_year = [Latest Year]
RETURN
CALCULATE(
    AVERAGE('brazil_income_clean'[average_income_brl]),
    'brazil_income_clean'[year] = selected_year
)

Weighted Average Income (Latest Year) =
VAR selected_year = [Latest Year]
RETURN
DIVIDE(
    CALCULATE(
        SUMX(
            'brazil_income_clean',
            'brazil_income_clean'[average_income_brl] * 'brazil_income_clean'[population]
        ),
        'brazil_income_clean'[year] = selected_year
    ),
    CALCULATE(
        SUM('brazil_income_clean'[population]),
        'brazil_income_clean'[year] = selected_year
    )
)

Highest-Income State (Latest Year) =
VAR selected_year = [Latest Year]
RETURN
CONCATENATEX(
    TOPN(
        1,
        SUMMARIZE(
            FILTER('brazil_income_clean', 'brazil_income_clean'[year] = selected_year),
            'brazil_income_clean'[state_code],
            "income", AVERAGE('brazil_income_clean'[average_income_brl])
        ),
        [income],
        DESC
    ),
    'brazil_income_clean'[state_code],
    ", "
)

Lowest-Income State (Latest Year) =
VAR selected_year = [Latest Year]
RETURN
CONCATENATEX(
    TOPN(
        1,
        SUMMARIZE(
            FILTER('brazil_income_clean', 'brazil_income_clean'[year] = selected_year),
            'brazil_income_clean'[state_code],
            "income", AVERAGE('brazil_income_clean'[average_income_brl])
        ),
        [income],
        ASC
    ),
    'brazil_income_clean'[state_code],
    ", "
)
```
