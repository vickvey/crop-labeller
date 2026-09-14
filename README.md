# Crop Labeller

A small, fully local/offline web app for reviewing and correcting crop
labels from NDVI time-series CSV data. Built for a handful of researchers
to manually review NDVI curves, confirm/correct the label, and leave notes
on unusual cases — with progress tracked and safely resumable.

> **Researcher reviewing crop labels and new to this kind of tool?** Skip
> this file and read **[USAGE-GUIDELINES.md](USAGE-GUIDELINES.md)** instead —
> a plain-language, step-by-step, Windows-first walkthrough with no
> assumed technical background. This README is the technical/setup
> reference.

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

## 2. Get the code

```bash
git clone <repo-url>
cd crop-labeller
```

(Or download/extract a ZIP of the repo and open a terminal in that folder —
no `git` required either way.)

## 3. Add input data

Place one or more CSV files directly in the `data/` directory. Each CSV is
expected to have:

- A set of `NDVI_1, NDVI_2, ..., NDVI_n` columns (the time series).
- A `label` column (or `class`/`class_id`) holding the current label.
- Ideally a `sample_id`/`id` column that uniquely identifies each row
  (used to track review progress per row; if missing, row position is
  used instead).

Any other columns (region, coordinates, cover area, etc.) are shown as
read-only context while reviewing. A few kinds of columns get special
treatment automatically, if present:

- **`region`** + **`year`** — used to look up a precomputed regional
  reference curve (see `reference/`) and to label the plot's x-axis with
  actual Oct–May fortnight periods instead of bare step numbers.
- **`NDVI_smooth_1..n`** — a Savitzky-Golay-smoothed counterpart of the raw
  NDVI series, plotted as a second curve alongside the original.
- **`label_confidence_score`** (0-1) and **`flag`** — output of the
  outlier/label-confidence scoring pipeline. Shown as a confidence badge,
  a warning banner explaining what looks off, a page-background tint
  matching the selected label, and an optional confidence-percentile
  filter in the UI — all to help prioritize and cross-check review.

`data/` may also hold `plots/` (diagnostic PNGs from that scoring pipeline)
and a `confidence_check_summary_*.csv` report; the app ignores both — it
never offers a `confidence_check_summary_*.csv` as something to review,
and only ever looks at files directly in `data/`, not subfolders.

## 4. Run the app

```bash
uv run run.py
```

This installs/updates dependencies automatically on first run (no separate
`uv sync` step needed — `uv run` does that itself), then starts a local
Streamlit server and opens the app in your browser (typically at
http://localhost:8501). Everything runs on your machine — no internet
connection or external service is used. `uv run crop-labeller` is
equivalent.

## 5. Using the labelling interface

1. If `data/` contains more than one CSV, pick one from the sidebar. The
   sidebar also shows review progress and a quick breakdown of the file
   (class balance, how many rows the scoring pipeline flagged).
2. Each screen shows one row: an interactive NDVI plot (the row's own
   curve, its smoothed version if available, and a shaded regional
   mean ± 1 std-dev reference band if available), contextual fields, the
   current label, and — if the CSV has confidence scoring — a confidence
   badge and warning banner for that row.
3. **Show** (top left) filters which rows you step through: All /
   Unreviewed / Reviewed. A **Confidence filter** below it can further
   restrict to the bottom N% least-confident rows within the wheat or
   non-wheat population, with a live count of matches.
4. Pick the correct label (the page background tints pale green/red to
   match your current selection) and optionally add a comment, then
   click **Save**. An "Unsaved change" note appears if you've edited a
   row but haven't saved it yet.
5. Use **Prev** / **Next** / **Jump to row** to navigate — both respect
   whatever filters are active.
6. Progress persists across restarts — closing and reopening the app
   resumes exactly where you left off.

## 6. Outputs

Nothing is ever written to the original file in `data/`. For an input file
`data/<name>.csv`, the app writes to `output/`:

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
├── data/                     # input CSVs go directly here (not modified by the app)
├── reference/                # precomputed regional mean/std NDVI curves
├── output/                   # generated labelled CSVs + review metadata
├── scripts/                  # offline/dev tools (e.g. build reference curves)
├── src/crop_labeller/        # app source
├── tests/                    # pytest tests
├── pyproject.toml
├── run.py                    # `uv run run.py` launches the app
├── README.md                 # this file (technical/setup reference)
└── USAGE-GUIDELINES.md       # step-by-step guide for researchers
```

## Development

```bash
uv run pytest
```
