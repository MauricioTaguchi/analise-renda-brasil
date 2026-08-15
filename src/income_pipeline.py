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
    "Rondônia": "North",
    "Acre": "North",
    "Amazonas": "North",
    "Roraima": "North",
    "Pará": "North",
    "Amapá": "North",
    "Tocantins": "North",
    "Maranhão": "Northeast",
    "Piauí": "Northeast",
    "Ceará": "Northeast",
    "Rio Grande do Norte": "Northeast",
    "Paraíba": "Northeast",
    "Pernambuco": "Northeast",
    "Alagoas": "Northeast",
    "Sergipe": "Northeast",
    "Bahia": "Northeast",
    "Minas Gerais": "Southeast",
    "Espírito Santo": "Southeast",
    "Rio de Janeiro": "Southeast",
    "São Paulo": "Southeast",
    "Paraná": "South",
    "Santa Catarina": "South",
    "Rio Grande do Sul": "South",
    "Mato Grosso do Sul": "Central-West",
    "Mato Grosso": "Central-West",
    "Goiás": "Central-West",
    "Distrito Federal": "Central-West",
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
        return self.root / "docs" / "EXECUTIVE_SUMMARY.md"

    @property
    def dashboard(self) -> Path:
        return self.root / "dashboard" / "index.html"


def fetch_sidra(url: str = SIDRA_URL) -> list[dict[str, str]]:
    request = urllib.request.Request(url, headers={"User-Agent": "portfolio-data-pipeline/1.0"})
    with urllib.request.urlopen(request, timeout=45) as response:
        payload = json.loads(response.read().decode("utf-8"))
    if not isinstance(payload, list) or len(payload) < 2:
        raise ValueError("The SIDRA API did not return enough observations.")
    return payload


def load_sidra_snapshot(path: Path) -> list[dict[str, str]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, list) or len(payload) < 2:
        raise ValueError("The SIDRA snapshot does not contain enough observations.")
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
                "quarter": f"Q{int(quarter_code[-2:])} {quarter_code[:4]}",
                "year": int(quarter_code[:4]),
                "quarter_number": int(quarter_code[-2:]),
                "state_code": str(row["D1C"]).zfill(2),
                "state": state,
                "region": REGIONS.get(state, "Unclassified"),
                "income_real_brl": float(value),
                "source_table": SIDRA_TABLE,
                "source_variable": SIDRA_VARIABLE,
            }
        )
    frame = pd.DataFrame.from_records(records)
    if frame.empty:
        raise ValueError("No valid observations were found.")
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
        raise ValueError(f"Missing required columns: {sorted(missing)}")
    if frame[list(required)].isnull().any().any():
        raise ValueError("The staging layer contains null values in required fields.")
    if (frame["income_real_brl"] <= 0).any():
        raise ValueError("Non-positive income values were found.")
    if frame.duplicated(["quarter_code", "state_code"]).any():
        raise ValueError("Duplicate observations were found for the same federative unit and quarter.")
    latest = frame[frame["quarter_code"] == frame["quarter_code"].max()]
    if latest["state_code"].nunique() != 27:
        raise ValueError("The latest quarter does not contain all 27 Brazilian federative units.")
    if (frame["region"] == "Unclassified").any():
        raise ValueError("At least one federative unit has no region classification.")


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


def format_brl(value: float) -> str:
    return f"{value:,.2f}"


def render_summary(ranking: pd.DataFrame, extracted_at: str) -> str:
    highest = ranking.iloc[0]
    lowest = ranking.iloc[-1]
    average = ranking["income_real_brl"].mean()
    valid_yoy = ranking.dropna(subset=["yoy_pct"]).sort_values("yoy_pct", ascending=False)
    growth_line = ""
    if not valid_yoy.empty:
        growth = valid_yoy.iloc[0]
        growth_line = f"- Highest 12-month change: **{growth['state']} ({growth['yoy_pct']:.2f}%)**.\n"
    return f"""# Executive Summary — Official Continuous PNAD

Source: **IBGE SIDRA, table {SIDRA_TABLE}, variable {SIDRA_VARIABLE}**.
UTC extraction time: **{extracted_at}**. Latest period: **{highest["quarter"]}**.

## Key findings

- Highest real average monthly income: **{highest["state"]} — R$ {format_brl(highest["income_real_brl"])}**.
- Lowest real average monthly income: **{lowest["state"]} — R$ {format_brl(lowest["income_real_brl"])}**.
- Simple average across the 27 federative units: **R$ {format_brl(average)}**.
{growth_line}
## Responsible interpretation

The indicator represents the real average monthly income usually received from all jobs by employed
people with labor income. The simple average across federative units is a descriptive territorial
measure and does not replace the official population-weighted national estimate published by IBGE.
Methodological revisions and Continuous PNAD updates may change the historical series.
"""


def render_dashboard(ranking: pd.DataFrame) -> str:
    top = ranking.head(10)
    max_value = float(top["income_real_brl"].max())
    bars = "".join(
        f'<div class="bar-row"><span>{escape(row.state)}</span>'
        f'<div class="track"><div class="bar" style="width:{row.income_real_brl / max_value * 100:.1f}%"></div></div>'
        f"<strong>R$ {format_brl(row.income_real_brl)}</strong></div>"
        for row in top.itertuples()
    )
    rows = "".join(
        f"<tr><td>{int(row.rank)}</td><td>{escape(row.state)}</td><td>{escape(row.region)}</td>"
        f"<td>R$ {format_brl(row.income_real_brl)}</td><td>{'—' if pd.isna(row.yoy_pct) else f'{row.yoy_pct:.2f}%'}</td></tr>"
        for row in ranking.itertuples()
    )
    latest = escape(str(ranking.iloc[0]["quarter"]))
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>Income by Federative Unit — Continuous PNAD</title>
<style>body{{font-family:Inter,system-ui,sans-serif;margin:0;background:#07111f;color:#e7eef8}}main{{max-width:1100px;margin:auto;padding:40px 20px}}.eyebrow{{color:#67e8f9;text-transform:uppercase;letter-spacing:.12em}}h1{{font-size:clamp(2rem,5vw,4rem);margin:.3rem 0}}.card{{background:#0f1d2f;border:1px solid #24364d;border-radius:18px;padding:24px;margin:22px 0}}.bar-row{{display:grid;grid-template-columns:170px 1fr 120px;gap:14px;align-items:center;margin:12px 0}}.track{{height:16px;background:#1c2d43;border-radius:99px;overflow:hidden}}.bar{{height:100%;background:linear-gradient(90deg,#22d3ee,#38bdf8);border-radius:99px}}table{{width:100%;border-collapse:collapse}}th,td{{padding:12px;border-bottom:1px solid #24364d;text-align:left}}small{{color:#9fb1c7}}@media(max-width:650px){{main{{padding:28px 14px}}.card{{padding:18px 14px}}.bar-row{{grid-template-columns:90px 1fr 88px;gap:8px;font-size:.78rem}}.table-wrap{{overflow:auto}}th,td{{padding:8px 4px;font-size:.75rem}}}}</style></head>
<body><main><p class="eyebrow">IBGE SIDRA · table {SIDRA_TABLE}</p><h1>Real income by Brazilian federative unit</h1><p>Latest period: {latest}. The project pipeline produces this static, reproducible dashboard.</p>
<section class="card"><h2>Top 10 federative units</h2>{bars}</section><section class="card table-wrap"><h2>Complete ranking</h2><table><thead><tr><th>#</th><th>Unit</th><th>Region</th><th>Income</th><th>YoY</th></tr></thead><tbody>{rows}</tbody></table></section>
<small>Official indicator: real average monthly income usually received from all jobs. See the repository for methodological limitations.</small></main></body></html>"""


def run(root: Path, payload: list[dict[str, str]] | None = None) -> None:
    paths = PipelinePaths(root)
    if payload is None:
        payload = fetch_sidra()
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
    parser = argparse.ArgumentParser(description="Official Continuous PNAD income pipeline powered by SIDRA.")
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument(
        "--input",
        type=Path,
        help="Read a saved SIDRA JSON snapshot instead of calling the public API.",
    )
    args = parser.parse_args()
    payload = load_sidra_snapshot(args.input.resolve()) if args.input else None
    run(args.root.resolve(), payload)


if __name__ == "__main__":
    main()
