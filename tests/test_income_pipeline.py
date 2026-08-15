import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

import pandas as pd

from src.income_pipeline import (
    REGIONS,
    SIDRA_VARIABLE,
    build_analytics,
    fetch_sidra,
    format_brl,
    load_sidra_snapshot,
    render_dashboard,
    render_summary,
    run,
    transform,
    validate,
)


def sidra_row(state: str, state_code: str, quarter: str, value: str) -> dict[str, str]:
    quarter_number = int(quarter[-2:])
    return {
        "D1N": state,
        "D1C": state_code,
        "D2C": SIDRA_VARIABLE,
        "D3C": quarter,
        "D3N": f"Source quarter {quarter_number}, {quarter[:4]}",
        "V": value,
    }


def complete_payload(quarters: tuple[str, ...] = ("202301", "202302", "202303", "202304", "202401")):
    payload: list[dict[str, str]] = [{"NC": "Territorial level code"}]
    for quarter_index, quarter in enumerate(quarters):
        for state_index, state in enumerate(REGIONS, start=1):
            value = 2000 + state_index * 10 + quarter_index * 100
            payload.append(sidra_row(state, str(state_index), quarter, str(value)))
    return payload


class IncomePipelineTest(unittest.TestCase):
    def test_transform_normalizes_sidra_payload(self) -> None:
        frame = transform(
            [
                {"NC": "Territorial level code"},
                sidra_row("São Paulo", "35", "202401", "3500"),
                sidra_row("São Paulo", "35", "202402", "..."),
            ]
        )

        self.assertEqual(frame.loc[0, "state"], "São Paulo")
        self.assertEqual(frame.loc[0, "region"], "Southeast")
        self.assertEqual(frame.loc[0, "quarter"], "Q1 2024")
        self.assertEqual(frame.loc[0, "quarter_number"], 1)
        self.assertEqual(frame.loc[0, "income_real_brl"], 3500.0)

    def test_transform_rejects_empty_observations(self) -> None:
        with self.assertRaisesRegex(ValueError, "No valid observations"):
            transform([{"header": "only"}])

    def test_validation_accepts_complete_frame_and_rejects_duplicate(self) -> None:
        frame = transform(complete_payload(("202401",)))
        validate(frame)

        duplicate = pd.concat([frame, frame.iloc[[0]]], ignore_index=True)
        with self.assertRaisesRegex(ValueError, "Duplicate observations"):
            validate(duplicate)

    def test_validation_rejects_incomplete_latest_quarter(self) -> None:
        frame = transform(complete_payload(("202401",))).iloc[:-1]
        with self.assertRaisesRegex(ValueError, "27 Brazilian federative units"):
            validate(frame)

    def test_analytics_calculates_four_quarter_change(self) -> None:
        frame = transform(complete_payload())
        ranking, trend = build_analytics(frame)

        self.assertGreater(ranking.loc[ranking["state"] == "Acre", "yoy_pct"].iloc[0], 0)
        self.assertEqual(ranking.iloc[0]["rank"], 1)
        self.assertEqual(trend.iloc[-1]["quarter_code"], "202401")

    def test_renderers_create_readable_outputs(self) -> None:
        ranking, _ = build_analytics(transform(complete_payload()))

        summary = render_summary(ranking, "2026-01-01T00:00:00+00:00")
        dashboard = render_dashboard(ranking)

        self.assertIn("Executive Summary", summary)
        self.assertIn("R$", summary)
        self.assertIn("Complete ranking", dashboard)
        self.assertIn('lang="en"', dashboard)
        self.assertEqual(format_brl(1234.5), "1,234.50")

    def test_run_persists_all_layers(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            run(root, complete_payload())

            self.assertTrue((root / "data/raw/ibge_sidra_6472.json").exists())
            self.assertTrue((root / "data/staging/income_by_state_quarter.csv").exists())
            self.assertTrue((root / "data/analytics/latest_income_ranking.csv").exists())
            self.assertTrue((root / "docs/EXECUTIVE_SUMMARY.md").exists())
            self.assertTrue((root / "dashboard/index.html").exists())

    def test_load_sidra_snapshot_validates_saved_payload(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            snapshot = Path(directory) / "sidra.json"
            snapshot.write_text(json.dumps(complete_payload(("202401",))), encoding="utf-8")
            self.assertGreater(len(load_sidra_snapshot(snapshot)), 1)

            snapshot.write_text("[]", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "snapshot does not contain enough observations"):
                load_sidra_snapshot(snapshot)

    @patch("src.income_pipeline.urllib.request.urlopen")
    def test_fetch_sidra_parses_json_and_validates_shape(self, urlopen: MagicMock) -> None:
        response = MagicMock()
        response.read.return_value = json.dumps(complete_payload(("202401",))).encode()
        urlopen.return_value.__enter__.return_value = response
        self.assertGreater(len(fetch_sidra("https://example.test")), 1)

        response.read.return_value = b"[]"
        with self.assertRaisesRegex(ValueError, "enough observations"):
            fetch_sidra("https://example.test")


if __name__ == "__main__":
    unittest.main()
