"""End-to-end checks that the app degrades gracefully on bad/edge-case input.

These write temp files directly into the project's real data/csv/ (the
app's DATA_DIR is a hardcoded project-relative path, not injectable), and
always clean up afterwards even if an assertion fails.
"""

from __future__ import annotations

import contextlib
from pathlib import Path

import pandas as pd
import pytest
from streamlit.testing.v1 import AppTest

APP_PATH = Path(__file__).resolve().parents[1] / "src" / "crop_labeller" / "app.py"
DATA_CSV_DIR = Path(__file__).resolve().parents[1] / "data" / "csv"


@contextlib.contextmanager
def temp_input_csv(filename: str, df: pd.DataFrame):
    DATA_CSV_DIR.mkdir(parents=True, exist_ok=True)
    path = DATA_CSV_DIR / filename
    df.to_csv(path, index=False)
    try:
        yield path
    finally:
        path.unlink(missing_ok=True)


def _select(at: AppTest, filename: str) -> AppTest:
    """Pick `filename` in the sidebar if a selector is present (multiple CSVs)."""
    if at.selectbox:
        at.selectbox[0].set_value(filename).run(timeout=30)
    return at


def test_malformed_csv_shows_friendly_error_not_a_crash():
    df = pd.DataFrame({"not_ndvi": [1, 2]})
    with temp_input_csv("zzz_test_malformed.csv", df):
        at = AppTest.from_file(str(APP_PATH))
        at.run(timeout=30)
        _select(at, "zzz_test_malformed.csv")

        assert not at.exception
        assert any("Couldn't read" in e.value for e in at.error)


def test_empty_csv_shows_friendly_error_not_a_crash():
    df = pd.DataFrame(columns=["sample_id", "label", "NDVI_1", "NDVI_2"])
    with temp_input_csv("zzz_test_empty.csv", df):
        at = AppTest.from_file(str(APP_PATH))
        at.run(timeout=30)
        _select(at, "zzz_test_empty.csv")

        assert not at.exception
        assert any("no data rows" in e.value for e in at.error)


def test_nan_confidence_and_flag_are_hidden_not_shown_as_nan():
    df = pd.DataFrame(
        {
            "sample_id": [1],
            "label": [1],
            "region": ["Punjab"],
            "year": [2021],
            "NDVI_1": [0.1],
            "NDVI_2": [0.2],
            "label_confidence_score": [float("nan")],
            "flag": [float("nan")],
        }
    )
    with temp_input_csv("zzz_test_nan_scoring.csv", df):
        at = AppTest.from_file(str(APP_PATH))
        at.run(timeout=30)
        _select(at, "zzz_test_nan_scoring.csv")

        assert not at.exception
        assert not any("confident" in m.value for m in at.markdown)
        assert not at.warning
