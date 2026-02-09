-- 1) KPI nacional por ano (média simples e ponderada por população)
SELECT
  ano,
  AVG(renda_media) AS renda_media_simples,
  SUM(renda_media * populacao) / SUM(populacao) AS renda_media_ponderada
FROM renda_brasil
GROUP BY ano
ORDER BY ano;

-- 2) Ranking de UFs no último ano
WITH last_year AS (SELECT MAX(ano) AS ano FROM renda_brasil)
SELECT uf, regiao, AVG(renda_media) AS renda_media
FROM renda_brasil
WHERE ano = (SELECT ano FROM last_year)
GROUP BY uf, regiao
ORDER BY renda_media DESC;

-- 3) Crescimento YoY por UF (último ano vs anterior)
WITH t AS (
  SELECT
    uf,
    ano,
    AVG(renda_media) AS renda_media,
    LAG(AVG(renda_media)) OVER (PARTITION BY uf ORDER BY ano) AS renda_prev
  FROM renda_brasil
  GROUP BY uf, ano
)
SELECT
  uf,
  ano,
  renda_media,
  renda_prev,
  CASE WHEN renda_prev IS NULL THEN NULL
       ELSE (renda_media - renda_prev) / renda_prev * 100 END AS crescimento_pct
FROM t
WHERE ano = (SELECT MAX(ano) FROM renda_brasil)
ORDER BY crescimento_pct DESC NULLS LAST;

-- 4) Desigualdade: variabilidade por UF
SELECT uf, STDDEV(renda_media) AS desvio_padrao
FROM renda_brasil
GROUP BY uf
ORDER BY desvio_padrao DESC;

-- 5) Comparação por região e ano
SELECT ano, regiao, AVG(renda_media) AS renda_media
FROM renda_brasil
GROUP BY ano, regiao
ORDER BY ano, regiao;
