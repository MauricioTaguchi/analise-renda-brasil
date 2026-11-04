-- Compare real monthly earnings across Brazil's federal units in Q1 2026.
-- Source: IBGE/SIDRA table 6472, variable 5933. The validated staging CSV
-- contains one earnings estimate per federal unit per quarter.
-- Each estimate receives equal weight in its comparison group.
--
-- Run with the SQLite command-line shell from the repository root:
-- sqlite3 -header -column :memory: ".import --csv data/staging/income_by_state_quarter.csv income" ".read dashboard/power-bi/q1_2026_income_comparison.sql"
--
-- Expected output for the validated snapshot (scope, federal units, BRL):
-- All federal units   27   3437.41
-- Southeast            4   3971.50

WITH q1 AS (
    SELECT state_code, region, CAST(income_real_brl AS REAL) AS earnings
    FROM income
    WHERE quarter = 'Q1 2026'
)
SELECT
    'All federal units' AS scope,
    COUNT(DISTINCT state_code) AS federal_units,
    ROUND(AVG(earnings), 2) AS mean_brl
FROM q1
UNION ALL
SELECT
    'Southeast' AS scope,
    COUNT(DISTINCT state_code) AS federal_units,
    ROUND(AVG(earnings), 2) AS mean_brl
FROM q1
WHERE region = 'Southeast'
ORDER BY scope;
