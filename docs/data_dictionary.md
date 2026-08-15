# Data Dictionary

## Official staging dataset

`data/staging/income_by_state_quarter.csv`

| Column | Type | Description |
|---|---|---|
| quarter_code | string | SIDRA period code in `YYYYQQ` format |
| quarter | string | English display label, such as `Q1 2026` |
| year | integer | Reference year |
| quarter_number | integer | Quarter number from 1 to 4 |
| state_code | string | Two-digit IBGE federative-unit code |
| state | string | Official federative-unit name |
| region | string | Brazilian macro-region normalized to English |
| income_real_brl | float | Real average monthly income in Brazilian reais |
| source_table | string | SIDRA table identifier |
| source_variable | string | SIDRA variable identifier |

## Official ranking dataset

`data/analytics/latest_income_ranking.csv` adds:

| Column | Type | Description |
|---|---|---|
| income_year_ago_brl | float | Income for the same federative unit four quarters earlier |
| yoy_pct | float | Four-quarter percentage change |
| rank | integer | Latest-quarter income rank in descending order |

## Official trend dataset

`data/analytics/national_income_trend.csv`

| Column | Type | Description |
|---|---|---|
| quarter_code | string | SIDRA period code |
| quarter | string | English display label |
| simple_average_brl | float | Simple average across federative units |
| median_brl | float | Median across federative units |
| min_brl | float | Lowest federative-unit value |
| max_brl | float | Highest federative-unit value |

## Complementary synthetic dataset

`data/brazil_income_clean.csv`

> This portfolio dataset is synthetic. It demonstrates the analytical workflow and must not be used for real-world economic conclusions.

| Column | Type | Description |
|---|---|---|
| year | integer | Reference year |
| state_code | string | Two-letter federative-unit abbreviation |
| region | string | Brazilian macro-region in English |
| average_income_brl | float | Estimated average monthly income |
| population | integer | Estimated population |
| minimum_wage_brl | integer | Reference minimum wage |
| income_in_minimum_wages | float | Average income divided by minimum wage |
| estimated_total_income_brl | float | Income multiplied by population; analytical proxy only |
