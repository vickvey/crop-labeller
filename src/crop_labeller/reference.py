"""Per-region-per-year NDVI reference curves (mean +/- std of wheat rows).

These are precomputed offline from the full, unfiltered regional dataset
(see scripts/build_region_reference.py) and committed to the repo as small
CSVs under `reference/`, one per region+season (e.g. `Punjab_2021.csv`),
since a season's weather can shift the typical curve meaningfully from one
year to the next. They are NOT computed from whatever CSV a researcher is
reviewing: that CSV is a small, deliberately biased sample of suspected
outliers, so a mean/std built from it would be skewed away from a
"typical" wheat curve instead of representing one.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from crop_labeller.data import CsvSchema

PROJECT_ROOT = Path(__file__).resolve().parents[2]
REFERENCE_DIR = PROJECT_ROOT / "reference"


def _normalize_year(year: object) -> str:
    try:
        return str(int(float(year)))
    except (TypeError, ValueError):
        return str(year)


def reference_key(region: object, year: object) -> str:
    """The `<region>_<year>` filename stem used for a reference CSV."""
    return f"{region}_{_normalize_year(year)}"


def compute_region_references(
    df: pd.DataFrame, schema: CsvSchema, wheat_label: object = 1
) -> dict[str, pd.DataFrame]:
    """Per-region-per-year mean/std reference curves, from wheat-only rows.

    `df`/`schema` are expected to come from concatenating one or more raw
    regional CSVs loaded via `crop_labeller.data.load_csv` (or CSVs sharing
    the same column layout). Returns {"<region>_<year>": reference_dataframe},
    where each reference dataframe has columns: region, year, step,
    ndvi_mean, ndvi_std, n_samples.
    """
    if schema.region_column is None:
        raise ValueError("Input data has no region column; cannot build reference curves.")
    if schema.year_column is None:
        raise ValueError("Input data has no year column; cannot build per-region-per-year reference curves.")

    wheat_rows = df[df[schema.label_column] == wheat_label]

    references: dict[str, pd.DataFrame] = {}
    for (region, year), group in wheat_rows.groupby([schema.region_column, schema.year_column]):
        means = group[schema.ndvi_columns].mean()
        stds = group[schema.ndvi_columns].std()
        references[reference_key(region, year)] = pd.DataFrame(
            {
                "region": region,
                "year": _normalize_year(year),
                "step": range(1, len(schema.ndvi_columns) + 1),
                "ndvi_mean": means.to_numpy(),
                "ndvi_std": stds.to_numpy(),
                "n_samples": len(group),
            }
        )
    return references


def write_region_references(references: dict[str, pd.DataFrame], output_dir: Path) -> list[Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    written = []
    for key, ref_df in references.items():
        path = output_dir / f"{key}.csv"
        ref_df.to_csv(path, index=False)
        written.append(path)
    return written


def load_region_reference(
    region: object, year: object, reference_dir: Path = REFERENCE_DIR
) -> pd.DataFrame | None:
    """The precomputed reference curve for `region` in `year`, or None if unavailable."""
    path = reference_dir / f"{reference_key(region, year)}.csv"
    if not path.exists():
        return None
    return pd.read_csv(path)
