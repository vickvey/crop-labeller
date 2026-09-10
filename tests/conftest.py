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
            "NDVI_1": [0.1, 0.2, 0.3],
            "NDVI_2": [0.4, 0.5, 0.6],
            "NDVI_3": [0.7, 0.8, 0.9],
        }
    )
    path = tmp_path / "sample.csv"
    df.to_csv(path, index=False)
    return path
