import pandas as pd

from crop_labeller.app import outlier_row_ids_for_percentile
from crop_labeller.data import load_csv


def _scored_csv(tmp_path):
    # 10 wheat rows (label=1) with confidence 0.1..1.0, 10 non-wheat rows
    # (label=0) with confidence 0.05..0.95 — distinct ranges so it's easy
    # to tell the two populations' results apart.
    df = pd.DataFrame(
        {
            "sample_id": list(range(1, 21)),
            "label": [1] * 10 + [0] * 10,
            "region": ["Punjab"] * 20,
            "year": [2021] * 20,
            "NDVI_1": [0.1] * 20,
            "label_confidence_score": [round(0.1 * i, 2) for i in range(1, 11)]
            + [round(0.05 + 0.1 * i, 2) for i in range(10)],
            "flag": ["ok"] * 20,
        }
    )
    path = tmp_path / "scored.csv"
    df.to_csv(path, index=False)
    return path


def test_outlier_row_ids_for_percentile_picks_bottom_fraction_within_population(tmp_path):
    df, schema = load_csv(_scored_csv(tmp_path))

    # Bottom 20% of 10 wheat rows -> the 2 lowest-confidence wheat samples.
    matched_ids, matched_count, population_count = outlier_row_ids_for_percentile(df, schema, 1, 20)

    assert population_count == 10
    assert matched_count == 2
    assert matched_ids == {1, 2}  # sample_ids with confidence 0.1, 0.2


def test_outlier_row_ids_for_percentile_is_scoped_to_one_label_population(tmp_path):
    df, schema = load_csv(_scored_csv(tmp_path))

    wheat_ids, _, _ = outlier_row_ids_for_percentile(df, schema, 1, 100)
    nonwheat_ids, _, _ = outlier_row_ids_for_percentile(df, schema, 0, 100)

    # Even at the 100th percentile (everyone), the two populations never mix.
    assert wheat_ids == set(range(1, 11))
    assert nonwheat_ids == set(range(11, 21))
    assert wheat_ids.isdisjoint(nonwheat_ids)


def test_outlier_row_ids_for_percentile_handles_all_nan_population(tmp_path):
    df, schema = load_csv(_scored_csv(tmp_path))
    df.loc[df["label"] == 1, "label_confidence_score"] = float("nan")

    matched_ids, matched_count, population_count = outlier_row_ids_for_percentile(df, schema, 1, 20)

    assert population_count == 10
    assert matched_count == 0
    assert matched_ids == set()
