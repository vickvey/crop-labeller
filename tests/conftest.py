import pandas as pd
import pytest


@pytest.fixture
def sample_csv(tmp_path):
    df = pd.DataFrame(
        {
            "sample_id": [1, 2, 3],
            "class_name": ["wheat", "non_wheat", "wheat"],
            "label": [1, 0, 1],
            "region": ["Punjab", "Punjab", "Punjab"],
            "year": [2021, 2021, 2021],
            "NDVI_1": [0.1, 0.2, 0.3],
            "NDVI_2": [0.4, 0.5, 0.6],
            "NDVI_3": [0.7, 0.8, 0.9],
        }
    )
    path = tmp_path / "sample.csv"
    df.to_csv(path, index=False)
    return path


@pytest.fixture
def sample_csv_with_scoring(tmp_path):
    """A CSV with the Savitzky-Golay smoothed columns and confidence/flag
    scoring columns produced by the outlier-scoring pipeline."""
    df = pd.DataFrame(
        {
            "sample_id": [1, 2, 3],
            "class_name": ["wheat", "non_wheat", "wheat"],
            "label": [1, 0, 1],
            "region": ["Punjab", "Punjab", "Punjab"],
            "year": [2021, 2021, 2021],
            "NDVI_1": [0.1, 0.2, 0.3],
            "NDVI_2": [0.4, 0.5, 0.6],
            "NDVI_3": [0.7, 0.8, 0.9],
            "NDVI_smooth_1": [0.12, 0.22, 0.28],
            "NDVI_smooth_2": [0.38, 0.48, 0.58],
            "NDVI_smooth_3": [0.68, 0.78, 0.88],
            "profile_correlation": [0.95, 0.4, 0.9],
            "profile_rmse": [0.02, 0.3, 0.03],
            "best_shift": [0, 1, -1],
            "wheat_similarity_score": [0.9, 0.2, 0.85],
            "label_confidence_score": [0.9, 0.2, 0.85],
            "flag": ["ok", "labeled_nonwheat_wheatlike_profile", "ok"],
        }
    )
    path = tmp_path / "sample_scored.csv"
    df.to_csv(path, index=False)
    return path
