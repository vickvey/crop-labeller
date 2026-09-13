# Crop Labeller

A small, fully local/offline web app for reviewing and correcting crop
labels from NDVI time-series CSV data. Built for a handful of researchers
to manually review NDVI curves, confirm/correct the label, and leave notes
on unusual cases — with progress tracked and safely resumable.

## 1. Install `uv`

`uv` is a fast Python package/project manager. Install it once:

```bash
# macOS / Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows (PowerShell)
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

See https://docs.astral.sh/uv/getting-started/installation/ for other options.
No manual Python install or virtualenv setup is needed — `uv` handles both.

## 2. Clone and set up

```bash
git clone <repo-url>
cd crop-labeller
uv sync
```

## 3. Add input data

Place one or more CSV files in the `data/csv/` directory. Each CSV is
expected to have:

- A set of `NDVI_1, NDVI_2, ..., NDVI_n` columns (the time series).
- A `label` column (or `class`/`class_id`) holding the current label.
- Ideally a `sample_id`/`id` column that uniquely identifies each row
  (used to track review progress per row; if missing, row position is
  used instead).

Any other columns (region, coordinates, cover area, etc.) are shown as
read-only context while reviewing. Two kinds of columns get special
treatment automatically, if present:

- **`NDVI_smooth_1..n`** — a Savitzky-Golay-smoothed counterpart of the raw
  NDVI series, plotted as a second curve alongside the original.
- **`label_confidence_score`** (0-1) and **`flag`** — output of the
  outlier/label-confidence scoring pipeline. Shown as a confidence badge and
  a warning banner explaining what looks off, to help prioritize review.

`data/` also holds `plots/` (diagnostic PNGs from that scoring pipeline)
and a `confidence_check_summary_*.csv`; neither is read by the app.

## 4. Run the app

```bash
uv run run.py
# or
uv run crop-labeller
```

This starts a local Streamlit server and opens the app in your browser
(typically at http://localhost:8501). Everything runs on your machine —
no internet connection or external service is used.

## 5. Using the labelling interface

1. If `data/csv/` contains more than one CSV, pick one from the sidebar.
2. Each screen shows one row: an interactive NDVI time-series plot,
   contextual fields (region, coordinates, etc.), and the current label.
3. Pick the correct label and optionally add a comment (e.g. for
   unusual/outlier curves), then click **Save & Next**.
4. Use **Previous** / **Next**, **Jump to row**, or **Next unreviewed** to
   navigate.
5. The sidebar shows live review progress (reviewed count, percentage,
   remaining), which persists across restarts — closing and reopening the
   app resumes exactly where you left off.

## 6. Outputs

Nothing is ever written to the original file in `data/csv/`. For an input
file `data/csv/<name>.csv`, the app writes to `output/`:

- **`<name>_labelled.csv`** — a full copy of the input with the same
  columns/order, with reviewed rows' labels updated in place.
- **`<name>_review_meta.csv`** — one row per reviewed sample: row id,
  original label, updated label, comment, and review timestamp.
- **`<name>.reviews.json`** — internal progress/state file the app uses to
  resume; the two CSVs above are regenerated from it on every save.

Multiple researchers reviewing the same CSV should use separate copies of
`output/` (e.g. by working in separate clones/checkouts) since review
state is not merged automatically.

## Project layout

```text
crop-labeller/
├── data/
│   └── csv/                 # input CSVs (not modified by the app)
├── reference/                # precomputed regional mean/std NDVI curves
├── output/                  # generated labelled CSVs + review metadata
├── scripts/                 # offline/dev tools (e.g. build reference curves)
├── src/crop_labeller/       # app source
├── tests/                   # pytest tests
├── pyproject.toml
├── run.py                   # `uv run run.py` launches the app
└── README.md
```

## Development

```bash
uv run pytest
```
