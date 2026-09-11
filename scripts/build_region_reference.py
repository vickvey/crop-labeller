"""Build per-region-per-year NDVI reference curves (mean +/- std of wheat rows).

This is a developer-only, offline tool. Run it against the full,
unfiltered regional NDVI dataset (never against the small outlier CSVs
handed to researchers) whenever that dataset changes, and commit the
resulting small CSVs under `reference/` to the repo — one file per
region+season, e.g. `Punjab_2021.csv`, since a season's weather can shift
the typical curve from one year to the next.

Usage:
    uv run python scripts/build_region_reference.py \\
        --input ~/SUFALAM_DATA/wheat_ndvi --output reference/
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from crop_labeller.data import list_csv_files, load_csv
from crop_labeller.reference import compute_region_references, write_region_references


def load_and_concat(csv_paths: list[Path]) -> pd.DataFrame:
    """Load and concatenate CSVs that must all share the same NDVI/label/region/year columns."""
    frames = []
    first_schema = None
    for path in csv_paths:
        df, schema = load_csv(path)
        if first_schema is None:
            first_schema = schema
        elif (
            schema.ndvi_columns != first_schema.ndvi_columns
            or schema.label_column != first_schema.label_column
            or schema.region_column != first_schema.region_column
            or schema.year_column != first_schema.year_column
        ):
            raise ValueError(
                f"{path.name} has a different NDVI/label/region/year column layout than "
                f"{csv_paths[0].name}; refusing to combine mismatched datasets."
            )
        frames.append(df)
    return pd.concat(frames, ignore_index=True), first_schema


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--input", type=Path, required=True, help="Directory of full regional NDVI CSVs")
    parser.add_argument(
        "--output",
        type=Path,
        default=Path(__file__).resolve().parents[1] / "reference",
        help="Output directory for reference CSVs (default: reference/)",
    )
    args = parser.parse_args()

    csv_paths = list_csv_files(args.input)
    if not csv_paths:
        raise SystemExit(f"No CSV files found in {args.input}")

    print(f"Loading {len(csv_paths)} file(s) from {args.input} ...")
    combined_df, schema = load_and_concat(csv_paths)

    if schema.region_column is None:
        raise SystemExit("Input data has no 'region' column; cannot build reference curves.")
    if schema.year_column is None:
        raise SystemExit("Input data has no 'year' column; cannot build per-region-per-year references.")

    references = compute_region_references(combined_df, schema)
    written = write_region_references(references, args.output)

    for path in sorted(written):
        n = references[path.stem]["n_samples"].iloc[0]
        print(f"Wrote {path} ({n} wheat samples)")


if __name__ == "__main__":
    main()
