from __future__ import annotations

import argparse
import json
import urllib.request
from dataclasses import dataclass
from datetime import UTC, datetime
from html import escape
from pathlib import Path

import pandas as pd

SIDRA_TABLE = "6472"
SIDRA_VARIABLE = "5933"
SIDRA_URL = (
    f"https://apisidra.ibge.gov.br/values/t/{SIDRA_TABLE}/n3/all/v/{SIDRA_VARIABLE}/p/last%2020?formato=json"
)

REGIONS = {
    "Rondônia": "Norte",
    "Acre": "Norte",
    "Amazonas": "Norte",
    "Roraima": "Norte",
    "Pará": "Norte",
    "Amapá": "Norte",
    "Tocantins": "Norte",
    "Maranhão": "Nordeste",
    "Piauí": "Nordeste",
    "Ceará": "Nordeste",
    "Rio Grande do Norte": "Nordeste",
    "Paraíba": "Nordeste",
    "Pernambuco": "Nordeste",
    "Alagoas": "Nordeste",
    "Sergipe": "Nordeste",
    "Bahia": "Nordeste",
    "Minas Gerais": "Sudeste",
    "Espírito Santo": "Sudeste",
    "Rio de Janeiro": "Sudeste",
    "São Paulo": "Sudeste",
    "Paraná": "Sul",
    "Santa Catarina": "Sul",
    "Rio Grande do Sul": "Sul",
    "Mato Grosso do Sul": "Centro-Oeste",
    "Mato Grosso": "Centro-Oeste",
    "Goiás": "Centro-Oeste",
    "Distrito Federal": "Centro-Oeste",
}


@dataclass(frozen=True)
class PipelinePaths:
    root: Path

    @property
    def raw(self) -> Path:
        return self.root / "data" / "raw" / "ibge_sidra_6472.json"

    @property
    def staging(self) -> Path:
        return self.root / "data" / "staging" / "income_by_state_quarter.csv"

    @property
    def ranking(self) -> Path:
        return self.root / "data" / "analytics" / "latest_income_ranking.csv"

    @property
    def trend(self) -> Path:
        return self.root / "data" / "analytics" / "national_income_trend.csv"

    @property
    def summary(self) -> Path:
        return self.root / "docs" / "EXECUTIVE_SUMMARY_OFFICIAL.md"

    @property
    def dashboard(self) -> Path:
        return self.root / "dashboard" / "index.html"


def fetch_sidra(url: str = SIDRA_URL) -> list[dict[str, str]]:
    request = urllib.request.Request(url, headers={"User-Agent": "portfolio-data-pipeline/1.0"})
    with urllib.request.urlopen(request, timeout=45) as response:
        payload = json.loads(response.read().decode("utf-8"))
    if not isinstance(payload, list) or len(payload) < 2:
        raise ValueError("A API SIDRA não retornou observações suficientes.")
    return payload


def transform(payload: list[dict[str, str]]) -> pd.DataFrame:
    records = []
    for row in payload[1:]:
        value = str(row.get("V", "")).strip()
        if row.get("D2C") != SIDRA_VARIABLE or value in {"", "-", "..."}:
            continue
        quarter_code = str(row["D3C"])
        state = str(row["D1N"]).strip()
        records.append(
            {
                "quarter_code": quarter_code,
                "quarter": str(row["D3N"]).strip(),
                "year": int(quarter_code[:4]),
                "quarter_number": int(quarter_code[-2:]),
                "state_code": str(row["D1C"]).zfill(2),
                "state": state,
                "region": REGIONS.get(state, "Não classificada"),
                "income_real_brl": float(value),
                "source_table": SIDRA_TABLE,
                "source_variable": SIDRA_VARIABLE,
            }
        )
    frame = pd.DataFrame.from_records(records)
    if frame.empty:
        raise ValueError("Nenhuma observação válida foi encontrada.")
    return frame.sort_values(["quarter_code", "state_code"]).reset_index(drop=True)


def validate(frame: pd.DataFrame) -> None:
    required = {
        "quarter_code",
        "state_code",
        "state",
        "region",
        "income_real_brl",
        "source_table",
        "source_variable",
    }
    missing = required.difference(frame.columns)
    if missing:
        raise ValueError(f"Colunas obrigatórias ausentes: {sorted(missing)}")
    if frame[list(required)].isnull().any().any():
        raise ValueError("A camada staging contém valores nulos em campos obrigatórios.")
    if (frame["income_real_brl"] <= 0).any():
        raise ValueError("Foram encontrados rendimentos não positivos.")
    if frame.duplicated(["quarter_code", "state_code"]).any():
        raise ValueError("Existem observações duplicadas por UF e trimestre.")
    latest = frame[frame["quarter_code"] == frame["quarter_code"].max()]
    if latest["state_code"].nunique() != 27:
        raise ValueError("O trimestre mais recente não contém as 27 UFs.")
    if (frame["region"] == "Não classificada").any():
        raise ValueError("Há UFs sem região classificada.")


def build_analytics(frame: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    ordered = frame.sort_values(["state_code", "quarter_code"]).copy()
    ordered["income_year_ago_brl"] = ordered.groupby("state_code")["income_real_brl"].shift(4)
    ordered["yoy_pct"] = ((ordered["income_real_brl"] / ordered["income_year_ago_brl"] - 1) * 100).round(2)
    latest_code = ordered["quarter_code"].max()
    ranking = ordered[ordered["quarter_code"] == latest_code].copy()
    ranking["rank"] = ranking["income_real_brl"].rank(method="dense", ascending=False).astype(int)
    ranking = ranking.sort_values("rank")

    trend = (
        frame.groupby(["quarter_code", "quarter"], as_index=False)
        .agg(
            simple_average_brl=("income_real_brl", "mean"),
            median_brl=("income_real_brl", "median"),
            min_brl=("income_real_brl", "min"),
            max_brl=("income_real_brl", "max"),
        )
        .sort_values("quarter_code")
    )
    for column in ["simple_average_brl", "median_brl", "min_brl", "max_brl"]:
        trend[column] = trend[column].round(2)
    return ranking, trend


def brl(value: float) -> str:
    return f"{value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def render_summary(ranking: pd.DataFrame, extracted_at: str) -> str:
    highest = ranking.iloc[0]
    lowest = ranking.iloc[-1]
    average = ranking["income_real_brl"].mean()
    valid_yoy = ranking.dropna(subset=["yoy_pct"]).sort_values("yoy_pct", ascending=False)
    growth_line = ""
    if not valid_yoy.empty:
        growth = valid_yoy.iloc[0]
        growth_line = f"- Maior variação em 12 meses: **{growth['state']} ({growth['yoy_pct']:.2f}%)**.\n"
    return f"""# Resumo executivo — PNAD Contínua oficial

Fonte: **IBGE SIDRA, tabela {SIDRA_TABLE}, variável {SIDRA_VARIABLE}**.  
Extração UTC: **{extracted_at}**. Período mais recente: **{highest["quarter"]}**.

## Principais resultados

- Maior rendimento médio mensal real: **{highest["state"]} — R$ {brl(highest["income_real_brl"])}**.
- Menor rendimento médio mensal real: **{lowest["state"]} — R$ {brl(lowest["income_real_brl"])}**.
- Média simples entre as 27 UFs: **R$ {brl(average)}**.
{growth_line}
## Leitura responsável

O indicador representa o rendimento médio mensal real das pessoas ocupadas com rendimento de
trabalho, habitualmente recebido em todos os trabalhos. A média simples entre UFs é uma medida
descritiva do recorte territorial e não substitui a estimativa nacional ponderada publicada pelo IBGE.
Revisões metodológicas e atualizações da PNAD Contínua podem alterar a série.
"""


def render_dashboard(ranking: pd.DataFrame) -> str:
    top = ranking.head(10)
    max_value = float(top["income_real_brl"].max())
    bars = "".join(
        f'<div class="bar-row"><span>{escape(row.state)}</span>'
        f'<div class="track"><div class="bar" style="width:{row.income_real_brl / max_value * 100:.1f}%"></div></div>'
        f"<strong>R$ {brl(row.income_real_brl)}</strong></div>"
        for row in top.itertuples()
    )
    rows = "".join(
        f"<tr><td>{int(row.rank)}</td><td>{escape(row.state)}</td><td>{escape(row.region)}</td>"
        f"<td>R$ {brl(row.income_real_brl)}</td><td>{'—' if pd.isna(row.yoy_pct) else f'{row.yoy_pct:.2f}%'}</td></tr>"
        for row in ranking.itertuples()
    )
    latest = escape(str(ranking.iloc[0]["quarter"]))
    return f"""<!doctype html><html lang="pt-BR"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>Renda por UF — PNAD Contínua</title>
<style>body{{font-family:Inter,system-ui,sans-serif;margin:0;background:#07111f;color:#e7eef8}}main{{max-width:1100px;margin:auto;padding:40px 20px}}.eyebrow{{color:#67e8f9;text-transform:uppercase;letter-spacing:.12em}}h1{{font-size:clamp(2rem,5vw,4rem);margin:.3rem 0}}.card{{background:#0f1d2f;border:1px solid #24364d;border-radius:18px;padding:24px;margin:22px 0}}.bar-row{{display:grid;grid-template-columns:170px 1fr 120px;gap:14px;align-items:center;margin:12px 0}}.track{{height:16px;background:#1c2d43;border-radius:99px;overflow:hidden}}.bar{{height:100%;background:linear-gradient(90deg,#22d3ee,#38bdf8);border-radius:99px}}table{{width:100%;border-collapse:collapse}}th,td{{padding:12px;border-bottom:1px solid #24364d;text-align:left}}small{{color:#9fb1c7}}@media(max-width:650px){{.bar-row{{grid-template-columns:90px 1fr 95px;font-size:.8rem}}.table-wrap{{overflow:auto}}}}</style></head>
<body><main><p class="eyebrow">IBGE SIDRA · tabela {SIDRA_TABLE}</p><h1>Renda real por unidade da federação</h1><p>Recorte mais recente: {latest}. Dashboard estático e reproduzível, gerado pelo pipeline do projeto.</p>
<section class="card"><h2>Top 10 UFs</h2>{bars}</section><section class="card table-wrap"><h2>Ranking completo</h2><table><thead><tr><th>#</th><th>UF</th><th>Região</th><th>Rendimento</th><th>YoY</th></tr></thead><tbody>{rows}</tbody></table></section>
<small>Indicador oficial: rendimento médio mensal real habitual em todos os trabalhos. Consulte as limitações metodológicas no repositório.</small></main></body></html>"""


def run(root: Path, payload: list[dict[str, str]] | None = None) -> None:
    paths = PipelinePaths(root)
    payload = payload or fetch_sidra()
    extracted_at = datetime.now(UTC).isoformat()
    frame = transform(payload)
    validate(frame)
    ranking, trend = build_analytics(frame)

    for path in [paths.raw, paths.staging, paths.ranking, paths.trend, paths.summary, paths.dashboard]:
        path.parent.mkdir(parents=True, exist_ok=True)
    paths.raw.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    frame.to_csv(paths.staging, index=False)
    ranking.to_csv(paths.ranking, index=False)
    trend.to_csv(paths.trend, index=False)
    paths.summary.write_text(render_summary(ranking, extracted_at), encoding="utf-8")
    paths.dashboard.write_text(render_dashboard(ranking), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Pipeline oficial de renda PNAD Contínua via SIDRA.")
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    run(args.root.resolve())


if __name__ == "__main__":
    main()
