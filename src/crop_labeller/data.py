"""CSV discovery and NDVI column parsing helpers."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

NDVI_COL_RE = re.compile(r"^NDVI_(\d+)$", re.IGNORECASE)
NDVI_SMOOTH_COL_RE = re.compile(r"^NDVI_smooth_(\d+)$", re.IGNORECASE)

# Columns that plausibly hold the "class" a researcher is reviewing, in
# priority order. The first match present in the CSV is used.
LABEL_COL_CANDIDATES = ("label", "class", "class_id")

# A companion text column that mirrors the label (e.g. class_name), if any.
LABEL_TEXT_COL_CANDIDATES = ("class_name", "class_label")

# A stable per-row identifier, in priority order.
ID_COL_CANDIDATES = ("sample_id", "id", "row_id")

# A column identifying the geographic region a row belongs to, used to look
# up a matching precomputed reference NDVI curve (see reference.py).
REGION_COL_CANDIDATES = ("region",)

# A column identifying the season/year a row belongs to, used together with
# region to look up a matching precomputed reference NDVI curve.
YEAR_COL_CANDIDATES = ("year",)

# Outlier/confidence scoring columns produced by the shift-tolerant
# profile-matching pipeline (score_wheat_profile_confidence.py), if present.
CONFIDENCE_COL_CANDIDATES = ("label_confidence_score",)
FLAG_COL_CANDIDATES = ("flag",)


@dataclass(frozen=True)
class CsvSchema:
    """Structural info about a loaded CSV, derived from its own columns."""

    columns: list[str]
    """Columns as they exist in the working dataframe (may include a
    synthetic id column that is NOT part of the original file)."""

    original_columns: list[str]
    """Exact column set/order of the source CSV, used when writing outputs."""

    ndvi_columns: list[str]
    ndvi_smooth_columns: list[str]
    """Savitzky-Golay smoothed counterpart of ndvi_columns, e.g. NDVI_smooth_1..N.
    Empty if the CSV doesn't have them (older exports)."""

    id_column: str
    id_column_is_synthetic: bool
    label_column: str
    label_text_column: str | None
    # label value -> most common companion text value, e.g. {0: "non_wheat", 1: "wheat"}
    label_text_map: dict[object, str]
    region_column: str | None
    year_column: str | None
    confidence_column: str | None
    """label_confidence_score in [0, 1]: how well this row's label matches its
    NDVI shape (per the shift-tolerant profile-matching scoring), if present."""
    flag_column: str | None
    """Categorical outlier flag ("ok", "labeled_wheat_atypical_profile",
    "labeled_nonwheat_wheatlike_profile"), if present."""


def list_csv_files(data_dir: Path) -> list[Path]:
    if not data_dir.exists():
        return []
    return sorted(p for p in data_dir.glob("*.csv") if p.is_file())


def _first_present(columns: list[str], candidates: tuple[str, ...]) -> str | None:
    lower_map = {c.lower(): c for c in columns}
    for candidate in candidates:
        if candidate in lower_map:
            return lower_map[candidate]
    return None


def _columns_matching(columns: list[str], pattern: re.Pattern) -> list[str]:
    matches = [(c, pattern.match(c)) for c in columns]
    found = [(c, int(m.group(1))) for c, m in matches if m]
    found.sort(key=lambda pair: pair[1])
    return [c for c, _ in found]


def load_csv(path: Path) -> tuple[pd.DataFrame, CsvSchema]:
    df = pd.read_csv(path)
    original_columns = list(df.columns)
    columns = list(df.columns)

    ndvi_columns = _columns_matching(columns, NDVI_COL_RE)
    if not ndvi_columns:
        raise ValueError(
            f"No NDVI_<n> columns found in {path.name}. "
            "Expected columns like NDVI_1, NDVI_2, ..."
        )
    ndvi_smooth_columns = _columns_matching(columns, NDVI_SMOOTH_COL_RE)

    id_column = _first_present(columns, ID_COL_CANDIDATES)
    id_column_is_synthetic = id_column is None
    if id_column is None:
        # Fall back to the dataframe's positional index as a stable id.
        df = df.reset_index(drop=True)
        df.insert(0, "row_id", df.index)
        id_column = "row_id"
        columns = list(df.columns)

    label_column = _first_present(columns, LABEL_COL_CANDIDATES)
    if label_column is None:
        raise ValueError(
            f"No label column found in {path.name}. "
            f"Expected one of: {', '.join(LABEL_COL_CANDIDATES)}"
        )

    label_text_column = _first_present(columns, LABEL_TEXT_COL_CANDIDATES)
    label_text_map: dict[object, str] = {}
    if label_text_column is not None:
        grouped = df.groupby(label_column)[label_text_column].agg(
            lambda s: s.mode().iloc[0]
        )
        label_text_map = grouped.to_dict()

    region_column = _first_present(columns, REGION_COL_CANDIDATES)
    year_column = _first_present(columns, YEAR_COL_CANDIDATES)
    confidence_column = _first_present(columns, CONFIDENCE_COL_CANDIDATES)
    flag_column = _first_present(columns, FLAG_COL_CANDIDATES)

    schema = CsvSchema(
        columns=columns,
        original_columns=original_columns,
        ndvi_columns=ndvi_columns,
        ndvi_smooth_columns=ndvi_smooth_columns,
        id_column=id_column,
        id_column_is_synthetic=id_column_is_synthetic,
        label_column=label_column,
        label_text_column=label_text_column,
        label_text_map=label_text_map,
        region_column=region_column,
        year_column=year_column,
        confidence_column=confidence_column,
        flag_column=flag_column,
    )
    return df, schema


def label_options(schema: CsvSchema, df: pd.DataFrame) -> list[object]:
    """Distinct label values seen in the data, sorted, for a picker widget."""
    values = sorted(df[schema.label_column].dropna().unique().tolist())
    return values


def label_display(schema: CsvSchema, value: object) -> str:
    text = schema.label_text_map.get(value)
    return f"{value} ({text})" if text else str(value)
