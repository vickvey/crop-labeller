import pandas as pd

from crop_labeller.data import load_csv
from crop_labeller.state import ReviewState, write_outputs


def test_review_state_roundtrip(tmp_path, sample_csv):
    state = ReviewState.load_or_create(tmp_path, sample_csv, total_rows=3)
    assert state.reviewed_count() == 0
    assert state.progress_fraction() == 0.0

    state.set_review(1, original_label=1, new_label=0, comment="looks off")
    state.save()

    reloaded = ReviewState.load_or_create(tmp_path, sample_csv, total_rows=3)
    assert reloaded.reviewed_count() == 1
    assert reloaded.is_reviewed(1)
    assert reloaded.get(1)["comment"] == "looks off"
    assert reloaded.get(1)["updated_label"] == 0


def test_write_outputs_preserves_columns_and_applies_edits(tmp_path, sample_csv):
    df, schema = load_csv(sample_csv)
    state = ReviewState.load_or_create(tmp_path, sample_csv, total_rows=len(df))
    state.set_review(1, original_label=1, new_label=0, comment="reclassified")

    labelled_path, meta_path = write_outputs(df, schema, state, tmp_path, sample_csv)

    labelled = pd.read_csv(labelled_path)
    assert list(labelled.columns) == schema.original_columns
    edited_row = labelled[labelled["sample_id"] == 1].iloc[0]
    assert edited_row["label"] == 0
    assert edited_row["class_name"] == "non_wheat"

    untouched_row = labelled[labelled["sample_id"] == 2].iloc[0]
    assert untouched_row["label"] == 0
    assert untouched_row["class_name"] == "non_wheat"

    meta = pd.read_csv(meta_path)
    assert len(meta) == 1
    assert meta.iloc[0]["comment"] == "reclassified"

    # Original input file must never be modified.
    original = pd.read_csv(sample_csv)
    assert original.loc[original["sample_id"] == 1, "label"].item() == 1
