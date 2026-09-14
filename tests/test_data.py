from crop_labeller.data import label_display, label_options, list_csv_files, load_csv


def test_load_csv_detects_schema(sample_csv):
    df, schema = load_csv(sample_csv)

    assert len(df) == 3
    assert schema.ndvi_columns == ["NDVI_1", "NDVI_2", "NDVI_3"]
    assert schema.id_column == "sample_id"
    assert schema.id_column_is_synthetic is False
    assert schema.label_column == "label"
    assert schema.label_text_column == "class_name"
    assert schema.label_text_map == {0: "non_wheat", 1: "wheat"}
    assert schema.original_columns == list(df.columns)
    assert schema.region_column == "region"
    assert schema.year_column == "year"
    assert schema.ndvi_smooth_columns == []
    assert schema.confidence_column is None
    assert schema.flag_column is None


def test_load_csv_detects_smoothing_and_confidence_scoring(sample_csv_with_scoring):
    df, schema = load_csv(sample_csv_with_scoring)

    assert schema.ndvi_smooth_columns == ["NDVI_smooth_1", "NDVI_smooth_2", "NDVI_smooth_3"]
    assert schema.confidence_column == "label_confidence_score"
    assert schema.flag_column == "flag"
    # Smoothed/scoring columns must not be mistaken for the raw NDVI series.
    assert schema.ndvi_columns == ["NDVI_1", "NDVI_2", "NDVI_3"]


def test_label_options_and_display(sample_csv):
    df, schema = load_csv(sample_csv)

    assert label_options(schema, df) == [0, 1]
    assert label_display(schema, 1) == "1 (wheat)"
    assert label_display(schema, 0) == "0 (non_wheat)"


def test_list_csv_files_excludes_confidence_summary_reports(tmp_path):
    import pandas as pd

    pd.DataFrame({"sample_id": [1], "label": [1], "NDVI_1": [0.1]}).to_csv(
        tmp_path / "Punjab_wheat_2021_outlier.csv", index=False
    )
    pd.DataFrame({"region": ["Punjab"], "total_samples": [9985]}).to_csv(
        tmp_path / "confidence_check_summary_wheat.csv", index=False
    )

    files = list_csv_files(tmp_path)

    assert [p.name for p in files] == ["Punjab_wheat_2021_outlier.csv"]


def test_load_csv_without_id_column_falls_back(tmp_path):
    import pandas as pd

    df = pd.DataFrame({"label": [1, 0], "NDVI_1": [0.1, 0.2], "NDVI_2": [0.3, 0.4]})
    path = tmp_path / "no_id.csv"
    df.to_csv(path, index=False)

    loaded_df, schema = load_csv(path)
    assert schema.id_column == "row_id"
    assert schema.id_column_is_synthetic is True
    assert schema.original_columns == ["label", "NDVI_1", "NDVI_2"]
    assert list(loaded_df["row_id"]) == [0, 1]
