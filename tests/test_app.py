"""End-to-end checks that the app degrades gracefully on bad/edge-case input.

These write temp files directly into the project's real data/ (the app's
DATA_DIR is a hardcoded project-relative path, not injectable), and always
clean up afterwards even if an assertion fails.
"""

from __future__ import annotations

import contextlib
from pathlib import Path

import pandas as pd
from streamlit.testing.v1 import AppTest

APP_PATH = Path(__file__).resolve().parents[1] / "src" / "crop_labeller" / "app.py"
DATA_CSV_DIR = Path(__file__).resolve().parents[1] / "data"


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


def test_confidence_outlier_filter_restricts_navigation():
    # Descending confidence so the one low-confidence (matching) wheat row
    # sits *last*, not at the default starting row — this actually
    # exercises "Next skips past non-matching rows to reach it".
    df = pd.DataFrame(
        {
            "sample_id": list(range(1, 21)),
            "label": [1] * 10 + [0] * 10,
            "region": ["Punjab"] * 20,
            "year": [2021] * 20,
            "NDVI_1": [0.1] * 20,
            "label_confidence_score": [round(1.1 - 0.1 * i, 2) for i in range(1, 11)] + [0.9] * 10,
            "flag": ["ok"] * 20,
        }
    )
    with temp_input_csv("zzz_test_confidence_filter.csv", df):
        at = AppTest.from_file(str(APP_PATH))
        at.run(timeout=30)
        _select(at, "zzz_test_confidence_filter.csv")

        checkbox = at.checkbox[0]
        checkbox.set_value(True).run(timeout=30)
        assert not at.exception

        # Default: wheat (label=1), bottom 10% of 10 wheat rows -> 1 row.
        assert any("1 of 10 rows match" in c.value for c in at.caption)

        buttons = {b.label: b for b in at.button}
        buttons["Next ➡"].click().run(timeout=30)
        assert not at.exception
        # Landed on the single matching row; nowhere else to go.
        buttons = {b.label: b for b in at.button}
        assert buttons["Next ➡"].disabled


def test_sidebar_shows_class_balance_and_flagged_count():
    df = pd.DataFrame(
        {
            "sample_id": list(range(1, 6)),
            "label": [1, 1, 0, 0, 0],
            "class_name": ["wheat", "wheat", "non_wheat", "non_wheat", "non_wheat"],
            "region": ["Punjab"] * 5,
            "year": [2021] * 5,
            "NDVI_1": [0.1] * 5,
            "flag": ["ok", "labeled_wheat_atypical_profile", "ok", "ok", "ok"],
        }
    )
    with temp_input_csv("zzz_test_sidebar_summary.csv", df):
        at = AppTest.from_file(str(APP_PATH))
        at.run(timeout=30)
        _select(at, "zzz_test_sidebar_summary.csv")

        assert not at.exception
        sidebar_text = " ".join(m.value for m in at.sidebar.markdown)
        assert "wheat" in sidebar_text and "2" in sidebar_text
        assert "non_wheat" in sidebar_text and "3" in sidebar_text
        assert any("1 row flagged" in c.value for c in at.sidebar.caption)


def test_unsaved_change_indicator_appears_and_clears_on_save():
    # Two label values must exist in the file for "1" to be a selectable
    # option on row 1 at all (label_options() is derived from the data).
    df = pd.DataFrame(
        {
            "sample_id": [1, 2],
            "label": [0, 1],
            "region": ["Punjab"] * 2,
            "year": [2021] * 2,
            "NDVI_1": [0.1, 0.1],
            "NDVI_2": [0.2, 0.2],
        }
    )
    with temp_input_csv("zzz_test_unsaved_indicator.csv", df):
        at = AppTest.from_file(str(APP_PATH))
        at.run(timeout=30)
        _select(at, "zzz_test_unsaved_indicator.csv")

        assert not any("Unsaved change" in c.value for c in at.caption)

        label_radio = [r for r in at.radio if r.label == "Label"][0]
        label_radio.set_value(1).run(timeout=30)
        assert not at.exception
        assert any("Unsaved change" in c.value for c in at.caption)

        save_btn = [b for b in at.button if "Save" in b.label][0]
        save_btn.click().run(timeout=30)
        assert not at.exception
        assert not any("Unsaved change" in c.value for c in at.caption)


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
