from crop_labeller.data import label_display, label_options, load_csv


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


def test_label_options_and_display(sample_csv):
    df, schema = load_csv(sample_csv)

    assert label_options(schema, df) == [0, 1]
    assert label_display(schema, 1) == "1 (wheat)"
    assert label_display(schema, 0) == "0 (non_wheat)"


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
