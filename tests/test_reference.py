import pandas as pd
import pytest

from crop_labeller.data import load_csv
from crop_labeller.reference import (
    compute_region_references,
    load_region_reference,
    reference_key,
    write_region_references,
)


def test_reference_key_normalizes_year():
    assert reference_key("Punjab", 2021) == "Punjab_2021"
    assert reference_key("Punjab", "2021") == "Punjab_2021"
    assert reference_key("Punjab", 2021.0) == "Punjab_2021"


def test_compute_region_references_is_wheat_only_and_per_region_per_year(tmp_path):
    df = pd.DataFrame(
        {
            "sample_id": [1, 2, 3, 4, 5],
            "label": [1, 1, 0, 1, 1],
            "region": ["Punjab", "Punjab", "Punjab", "Punjab", "Haryana"],
            "year": [2021, 2021, 2021, 2022, 2021],
            "NDVI_1": [0.2, 0.4, 999.0, 0.9, 0.6],
            "NDVI_2": [0.6, 0.8, 999.0, 0.1, 0.4],
        }
    )
    path = tmp_path / "combined.csv"
    df.to_csv(path, index=False)
    loaded_df, schema = load_csv(path)

    references = compute_region_references(loaded_df, schema)

    # Separate keys per region+year, not merged across years.
    assert set(references) == {"Punjab_2021", "Punjab_2022", "Haryana_2021"}

    punjab_2021 = references["Punjab_2021"]
    assert list(punjab_2021["step"]) == [1, 2]
    # Only the two wheat (label==1) Punjab/2021 rows contribute; the label==0 row is excluded.
    assert punjab_2021["ndvi_mean"].tolist() == pytest.approx([0.3, 0.7])
    assert punjab_2021["n_samples"].iloc[0] == 2
    assert punjab_2021["region"].iloc[0] == "Punjab"
    assert punjab_2021["year"].iloc[0] == "2021"

    punjab_2022 = references["Punjab_2022"]
    assert punjab_2022["ndvi_mean"].tolist() == pytest.approx([0.9, 0.1])
    assert punjab_2022["n_samples"].iloc[0] == 1

    haryana_2021 = references["Haryana_2021"]
    assert haryana_2021["ndvi_mean"].tolist() == pytest.approx([0.6, 0.4])


def test_write_and_load_region_reference(tmp_path):
    references = {
        "Punjab_2021": pd.DataFrame(
            {
                "region": "Punjab",
                "year": "2021",
                "step": [1, 2],
                "ndvi_mean": [0.3, 0.7],
                "ndvi_std": [0.1, 0.05],
                "n_samples": [2, 2],
            }
        )
    }
    write_region_references(references, tmp_path)

    loaded = load_region_reference("Punjab", 2021, reference_dir=tmp_path)
    assert loaded is not None
    assert loaded["ndvi_mean"].tolist() == [0.3, 0.7]

    assert load_region_reference("Punjab", 2022, reference_dir=tmp_path) is None
    assert load_region_reference("Gujarat", 2021, reference_dir=tmp_path) is None
