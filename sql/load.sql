-- Run from the repository root with psql.
\copy brazil_income FROM 'data/brazil_income_clean.csv' WITH (FORMAT csv, HEADER true);
