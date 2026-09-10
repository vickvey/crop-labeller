"""Persistence for review progress and generation of output files.

All state lives in a single JSON file per input CSV
(``output/<stem>.reviews.json``). The two deliverable CSVs (labelled data +
review metadata) are regenerated from that JSON on every save, so the JSON
file is the single source of truth and the app can be closed/restarted at
any time without losing progress.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from crop_labeller.data import CsvSchema


@dataclass
class ReviewState:
    source_csv: str
    total_rows: int
    reviews: dict[str, dict] = field(default_factory=dict)
    state_path: Path | None = None

    @classmethod
    def load_or_create(cls, output_dir: Path, source_csv_path: Path, total_rows: int) -> "ReviewState":
        state_path = output_dir / f"{source_csv_path.stem}.reviews.json"
        if state_path.exists():
            payload = json.loads(state_path.read_text())
            state = cls(
                source_csv=payload.get("source_csv", source_csv_path.name),
                total_rows=total_rows,
                reviews=payload.get("reviews", {}),
                state_path=state_path,
            )
        else:
            state = cls(
                source_csv=source_csv_path.name,
                total_rows=total_rows,
                reviews={},
                state_path=state_path,
            )
        return state

    def is_reviewed(self, row_id: object) -> bool:
        return str(row_id) in self.reviews

    def get(self, row_id: object) -> dict | None:
        return self.reviews.get(str(row_id))

    def set_review(
        self,
        row_id: object,
        original_label: object,
        new_label: object,
        comment: str,
    ) -> None:
        self.reviews[str(row_id)] = {
            "row_id": row_id,
            "original_label": original_label,
            "updated_label": new_label,
            "comment": comment or "",
            "reviewed_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        }

    def reviewed_count(self) -> int:
        return len(self.reviews)

    def progress_fraction(self) -> float:
        if self.total_rows == 0:
            return 0.0
        return self.reviewed_count() / self.total_rows

    def save(self) -> None:
        if self.state_path is None:
            raise RuntimeError("state_path not set")
        self.state_path.parent.mkdir(parents=True, exist_ok=True)
        payload = {"source_csv": self.source_csv, "reviews": self.reviews}
        tmp_path = self.state_path.with_suffix(".json.tmp")
        tmp_path.write_text(json.dumps(payload, indent=2, default=str))
        tmp_path.replace(self.state_path)


def _atomic_write_csv(df: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_suffix(path.suffix + ".tmp")
    df.to_csv(tmp_path, index=False)
    tmp_path.replace(path)


def write_outputs(
    df: pd.DataFrame,
    schema: CsvSchema,
    state: ReviewState,
    output_dir: Path,
    source_csv_path: Path,
) -> tuple[Path, Path]:
    """Write the labelled CSV and the review metadata CSV. Never touches the input."""

    labelled_df = df.copy()
    id_col = schema.id_column
    labelled_df[id_col] = labelled_df[id_col].astype(str)

    for row_id, review in state.reviews.items():
        mask = labelled_df[id_col] == row_id
        if not mask.any():
            continue
        new_label = review["updated_label"]
        labelled_df.loc[mask, schema.label_column] = new_label
        if schema.label_text_column and new_label in schema.label_text_map:
            labelled_df.loc[mask, schema.label_text_column] = schema.label_text_map[new_label]

    # Restore original dtype/order and drop any synthetic id column we added.
    if not schema.id_column_is_synthetic:
        labelled_df[id_col] = labelled_df[id_col].astype(df[id_col].dtype, errors="ignore")
    labelled_df = labelled_df[schema.original_columns]

    labelled_path = output_dir / f"{source_csv_path.stem}_labelled.csv"
    _atomic_write_csv(labelled_df, labelled_path)

    meta_rows = [
        {
            "row_id": review["row_id"],
            "original_label": review["original_label"],
            "updated_label": review["updated_label"],
            "comment": review["comment"],
            "reviewed_at": review["reviewed_at"],
        }
        for review in state.reviews.values()
    ]
    meta_df = pd.DataFrame(
        meta_rows,
        columns=["row_id", "original_label", "updated_label", "comment", "reviewed_at"],
    )
    meta_path = output_dir / f"{source_csv_path.stem}_review_meta.csv"
    _atomic_write_csv(meta_df, meta_path)

    return labelled_path, meta_path
