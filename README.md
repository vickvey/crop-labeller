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

> **Offline machine (no internet, so no `uv`)?** Use the Windows zips from
> the latest release: one has Python built in, the other installs into your
> own Python 3.12. See [Offline install](#offline-install-no-uv) below.

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

**Without `uv`:** plain pip works too, with Python ≥ 3.10.
`requirements.txt` is the pinned dependency set exported from `uv.lock`,
and `run.py` puts `src/` on `sys.path` itself, so the project doesn't need
to be installed:

```bash
python -m venv .venv
.venv/bin/python -m pip install -r requirements.txt     # Windows: .venv\Scripts\python ...
.venv/bin/python run.py
```

Any environment with `streamlit>=1.38`, `pandas>=2.2` and `plotly>=5.24`
works (conda, Poetry, offline wheels, and so on). See
[USAGE-GUIDELINES.md, Option D](USAGE-GUIDELINES.md#option-d--from-the-source-code-your-own-way-any-computer).

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
├── .github/workflows/        # builds, Windows-tests and releases the offline zips
├── packaging/                # launchers + release notes for the offline zips
├── scripts/                  # dev tools: reference curves, offline zips, smoke test, PDF
├── src/crop_labeller/        # app source
├── tests/                    # pytest tests
├── pyproject.toml
├── requirements.txt          # pinned deps (exported from uv.lock) for offline pip installs
├── run.py                    # `uv run run.py` (or `python run.py`) launches the app
├── README.md                 # this file (technical/setup reference)
└── USAGE-GUIDELINES.md       # step-by-step guide for researchers
```

## Offline install (no `uv`)

For air-gapped Windows machines, each
[GitHub release](https://github.com/vickvey/crop-labeller/releases) has two zips:

- **`crop-labeller-<version>-windows-offline.zip`** (recommended): the app
  plus a private Python 3.12 (python-build-standalone) with every dependency
  preinstalled. Unzip it and double-click `start-crop-labeller.bat`. There's
  no install step, and whatever Python the machine has doesn't matter.
- **`crop-labeller-<version>-windows-offline-own-python.zip`**: the app plus a
  `wheelhouse/` of the exact pinned `cp312-win_amd64` wheels, for machines
  that must use their own Python 3.12. `install-with-own-python.bat [path\to\python.exe]`
  builds a `.venv` and installs offline. After that, `start-crop-labeller.bat`
  runs the app. The launcher uses `python\` if present, else `.venv\`.

The researcher-facing steps, including fully manual pip/uv commands, are in
[USAGE-GUIDELINES.md §1–2](USAGE-GUIDELINES.md#1-pick-your-setup).

`scripts/build_offline_bundle.py` builds both zips. It:

- **Refuses to build from uncommitted changes**, and takes the app files from
  `git archive HEAD`, so the commit recorded in each zip's `VERSION.txt` is
  exactly what's inside. `--allow-dirty` is for local testing only, and marks
  the build "TEST BUILD, not for release".
- **Refuses if `requirements.txt` is out of date with `uv.lock`.** Regenerate
  it with
  `uv export --no-dev --no-hashes --no-emit-project --format requirements-txt -o requirements.txt`.
- **Resolves dependencies for the *target* platform.** Plain
  `pip download --platform` evaluates markers like `sys_platform == 'win32'`
  against the build host, which silently drops Windows-only deps such as
  `tzdata`.
- **Refuses any path in the zip over 140 characters**, because Windows'
  260-character `MAX_PATH` breaks Explorer's "Extract All". It also refuses
  filenames with spaces.
- **Writes `dist/SHA256SUMS.txt`.**

Some pieces apply however the app is launched. `run.py` puts `src/` on
`sys.path` itself, so the project never has to be pip-installed (that would
need `hatchling` offline). `crop_labeller/launcher.py` turns off Streamlit's
first-run email prompt, which otherwise blocks a fresh machine at `Email:`,
and usage stats. It also binds to `localhost`, so there's no Windows Firewall
popup.

To test locally, build the Linux equivalents and smoke-test an extracted copy:

```bash
uv run python scripts/build_offline_bundle.py --platform linux --allow-dirty
unzip -q dist/crop-labeller-*-linux-offline.zip -d /tmp/t && python3 scripts/smoke_test_install.py /tmp/t/crop-labeller
```

## Releasing

The `offline-packages` GitHub Actions workflow runs on every push to `main`
and on tags:

1. Runs the tests on Python 3.12.
2. Builds both Windows zips on Linux.
3. On a **real Windows runner**, extracts each zip with `Expand-Archive` and
   runs `scripts/smoke_test_install.py` against it. For own-python, this
   covers both the installer's auto-detection and an explicit `python.exe`
   path. The test renders the app on a sample CSV and starts
   `start-crop-labeller.bat` until the server answers its health check.
4. Tests the source installs the same way, with `python run.py`:
   - Option D (venv + `pip install -r requirements.txt`) on Windows, macOS
     and Linux, with Python 3.10, 3.12 and 3.14.
   - Option C (`uv`) on Windows and macOS.
5. **For a `v*` tag only**, and only if all of the above passed, publishes a
   GitHub release with the zips, `SHA256SUMS.txt` and
   `packaging/release-notes.md`.

To cut a release:

```bash
# bump `version` in pyproject.toml, then:
uv lock && git commit -am "Release vX.Y.Z" && git push origin main
git tag -a vX.Y.Z -m "Crop Labeller X.Y.Z" && git push origin vX.Y.Z   # separately: a combined push didn't trigger the tag run
```

The workflow fails if the tag doesn't match `pyproject.toml`'s version.

## Development

```bash
uv run pytest
```

After editing `USAGE-GUIDELINES.md`, regenerate the PDF that ships next to it
(and in the offline zips). It uses [md-to-pdf](https://github.com/simonhaenisch/md-to-pdf),
which renders through headless Chrome:

```bash
scripts/pdf/build-usage-pdf.sh
```

The script uses an installed Chrome/Chromium if it finds one, and fails if
the PDF wasn't actually rewritten. Don't call `md-to-pdf` directly from a
pipe or script: it reads stdin first, and then either hangs or writes the
PDF to stdout instead of the file.
