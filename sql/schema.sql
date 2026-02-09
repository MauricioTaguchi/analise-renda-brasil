-- PostgreSQL-friendly schema
DROP TABLE IF EXISTS renda_brasil;

CREATE TABLE renda_brasil (
  ano INT NOT NULL,
  uf VARCHAR(2) NOT NULL,
  regiao VARCHAR(20) NOT NULL,
  renda_media NUMERIC(12,2) NOT NULL,
  populacao BIGINT NOT NULL,
  salario_minimo INT NOT NULL,
  renda_em_sal_min NUMERIC(10,2) NOT NULL,
  renda_total_estimada NUMERIC(20,2) NOT NULL
);
