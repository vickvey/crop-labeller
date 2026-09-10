# Crop Labeller Project

Build a **fully local/offline web app** for some (atmax 5) researchers to review and correct crop labels from NDVI time-series CSV data.

## Goal

Researchers should be able to:

1. Select an input CSV from a local `data/` directory.
2. View each datapoint/row as a beautiful interactive NDVI time-series graph.
3. Review and update the existing label.
4. Optionally add a comment for unusual/outlier cases.
5. See clear progress of how much of the dataset has been reviewed.
6. Save all reviewed/modified datapoints without modifying the original CSV.

## Workflow

### 1. Input

- Look for CSV files inside `data/`.
- If multiple CSVs exist, show a simple file-selection screen.
- Preserve the **exact original column structure/signature** of the selected CSV.

### 2. Labelling UI

For each row/datapoint:

- Display its NDVI time series using a clean interactive graph (Plotly or similar).
- Clearly display the current label.
- Provide an easy way to change/update the label.
- Provide an optional comment field.
- Provide navigation such as:
  - Previous
  - Next
  - Jump to row/index.

### 3. Progress

Show clear annotation progress so researchers can track their work, for example:

```text
Reviewed: 427 / 2000
Progress: 21.4%
Remaining: 1573
```

Also display a visual progress bar.

Progress should update whenever a datapoint is reviewed/saved and should persist if the application is restarted.

### 4. Outputs

Never modify the original input CSV.

Create two output files:

**A. Main labelled CSV**

- Same columns and column order as the input CSV.
- Updated labels are written back into the appropriate label column.
- No unnecessary changes to the original data.

**B. Review metadata/comments file**

- Store information such as:
  - datapoint/row identifier
  - original label
  - updated label
  - comment
  - optionally review status/timestamp if useful

The metadata file can contain additional fields that are not present in the original dataset.

## Technical Requirements

- Fully local and offline.
- No external API, database, cloud service, or internet dependency at runtime.
- Python project managed with **uv**.
- Keep dependencies minimal.
- Prefer a lightweight local web framework such as **Streamlit** unless there is a strong reason to use something else.
- Use Plotly for interactive NDVI plots.
- The app should run on Windows, Linux, and macOS.
- Researchers should not need to understand Python or manually create environments.

## Repository Structure

Keep the project simple and maintainable. For example:

```text
crop-labeller/
├── data/
├── output/
├── src/
├── tests/
├── pyproject.toml
├── uv.lock
├── README.md
└── run.py
```

The exact structure can be adjusted if there is a simpler approach.

## Setup / Usage

The intended user experience should be approximately:

```bash
git clone <repo>
cd crop-labeller
uv sync
uv run ...
```

Ideally provide a single obvious command/script to launch the application locally.

The README should contain concise instructions for:

- Installing `uv`
- Cloning the repository
- Running the application
- Where to place input CSVs
- Where outputs are generated
- Basic usage of the labelling interface

## Important Design Principles

- **Keep it simple.**
- This is a research labelling utility, not a large production system.
- Optimize for fast manual review of many datapoints.
- Do not introduce unnecessary abstractions, databases, authentication, Docker, or cloud infrastructure.
- Preserve input data exactly.
- Make the application robust against accidentally closing/restarting it during annotation if this can be achieved simply.
- Code should be clean, readable, and easy for another researcher to modify.

Before implementing, inspect the expected CSV structure and design the NDVI parsing/plotting logic around the actual data format rather than making assumptions.
