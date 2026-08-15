-- 1) National indicators by year: simple and population-weighted averages.
SELECT
  year,
  AVG(average_income_brl) AS simple_average_income_brl,
  SUM(average_income_brl * population) / SUM(population) AS weighted_average_income_brl
FROM brazil_income
GROUP BY year
ORDER BY year;

-- 2) Federative-unit ranking for the latest year.
WITH latest_year AS (
  SELECT MAX(year) AS year
  FROM brazil_income
)
SELECT
  state_code,
  region,
  AVG(average_income_brl) AS average_income_brl
FROM brazil_income
WHERE year = (SELECT year FROM latest_year)
GROUP BY state_code, region
ORDER BY average_income_brl DESC;

-- 3) Year-over-year growth by federative unit.
WITH annual_income AS (
  SELECT
    state_code,
    year,
    AVG(average_income_brl) AS average_income_brl,
    LAG(AVG(average_income_brl)) OVER (
      PARTITION BY state_code
      ORDER BY year
    ) AS previous_income_brl
  FROM brazil_income
  GROUP BY state_code, year
)
SELECT
  state_code,
  year,
  average_income_brl,
  previous_income_brl,
  CASE
    WHEN previous_income_brl IS NULL THEN NULL
    ELSE (average_income_brl - previous_income_brl) / previous_income_brl * 100
  END AS yoy_growth_pct
FROM annual_income
WHERE year = (SELECT MAX(year) FROM brazil_income)
ORDER BY yoy_growth_pct DESC NULLS LAST;

-- 4) Income variability by federative unit.
SELECT
  state_code,
  STDDEV(average_income_brl) AS income_standard_deviation_brl
FROM brazil_income
GROUP BY state_code
ORDER BY income_standard_deviation_brl DESC;

-- 5) Regional comparison by year.
SELECT
  year,
  region,
  AVG(average_income_brl) AS average_income_brl
FROM brazil_income
GROUP BY year, region
ORDER BY year, region;
