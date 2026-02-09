# Data Dictionary

**Source:** Synthetic dataset for portfolio (structure inspired by IBGE/PNAD indicators).

| Column | Type | Description |
|---|---|---|
| ano | int | Reference year |
| uf | string | Brazilian state (UF) |
| regiao | string | Brazilian macro-region |
| renda_media | float | Estimated average monthly income (R$) |
| populacao | int | Estimated population |
| salario_minimo | int | Reference minimum wage (R$) |
| renda_em_sal_min | float | renda_media / salario_minimo |
| renda_total_estimada | float | renda_media * populacao (proxy for total income) |
