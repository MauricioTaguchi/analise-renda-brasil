-- PostgreSQL schema for the complementary synthetic dataset.
DROP TABLE IF EXISTS brazil_income;

CREATE TABLE brazil_income (
  year INTEGER NOT NULL,
  state_code VARCHAR(2) NOT NULL,
  region VARCHAR(20) NOT NULL,
  average_income_brl NUMERIC(12, 2) NOT NULL,
  population BIGINT NOT NULL,
  minimum_wage_brl INTEGER NOT NULL,
  income_in_minimum_wages NUMERIC(10, 2) NOT NULL,
  estimated_total_income_brl NUMERIC(20, 2) NOT NULL,
  PRIMARY KEY (year, state_code)
);
