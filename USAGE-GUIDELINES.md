# Crop Labeller — Researcher Guide

This guide is for reviewing wheat NDVI labels — no coding or "developer"
background needed. You already know wheat when you see its curve; this
just walks you through setting up and then the screen, click by click.

Everything you do in the app — picking your file, looking at data, saving
your work — happens by clicking in your web browser, same as any website.
On Windows you start it by double-clicking a file; nothing needs typing.

---

## 1. Pick your setup

Choose the **first row that fits your computer**. The rows go from easiest
to most involved.

| Your computer | Use | What it takes |
|---|---|---|
| **Windows** (with or without internet) | **[Option A — Ready-made package](#option-a--ready-made-package-windows-recommended)** (recommended) | Unzip, then double-click. Nothing to install; Python is built in. |
| **Windows** that must use its **own** Python 3.12 | [Option B — Your own Python](#option-b--your-own-python-312-windows) | Unzip, then double-click an installer once. |
| **Mac**, or you already use `uv` | [Option C — Install with `uv`](#option-c--install-with-uv-mac-or-any-computer-with-internet) | Needs internet. Install `uv`, then type one command. |

Options A and B work on computers with **no internet at all**. You only
need internet somewhere to download the zip, which you can then copy over,
e.g. on a USB drive.

---

## 2. One-time setup

Do only the option you picked above.

### Option A — Ready-made package (Windows, recommended)

1. **Download** `crop-labeller-<version>-windows-offline.zip` from
   <https://github.com/vickvey/crop-labeller/releases/latest> (under
   **Assets**), or get it from whoever gave you this tool. If the computer
   you'll use has no internet, download it elsewhere and copy it over.
2. **Unblock it.** Right-click the zip → **Properties** → at the bottom,
   tick **Unblock** → **OK**. (If there's no Unblock box, skip this.) This
   stops Windows from showing warnings about the files inside.
3. **Extract it.** Right-click the zip → **Extract All...** → **Extract**.
   The suggested location is fine. You'll get a folder containing
   `crop-labeller`. Move that `crop-labeller` folder wherever you like, for
   example your Documents.

   Don't double-click files *inside* the zip without extracting it first.
   It won't work from there.

**That's all the setup.** Go to
[Section 3](#3-every-time-you-want-to-review-data).

### Option B — Your own Python 3.12 (Windows)

For computers that must use the Python already installed on them. It must
be **Python 3.12, 64-bit**.

1. Do steps 1–3 of [Option A](#option-a--ready-made-package-windows-recommended),
   but download **`crop-labeller-<version>-windows-offline-own-python.zip`**
   instead.
2. In the extracted `crop-labeller` folder, double-click
   **`install-with-own-python.bat`**. It finds your Python 3.12, creates a
   private `.venv` folder, and installs the included packages from the
   `wheelhouse` folder, offline. When it says **Setup finished**, press a
   key to close it. You only do this once, or again if you switch to a
   different Python.

**That's all the setup.** Go to
[Section 3](#3-every-time-you-want-to-review-data).

**If it says it couldn't find a 64-bit Python 3.12**, tell it exactly
which Python to use:

1. Open PowerShell in the `crop-labeller` folder. Hold **Shift**,
   **right-click** empty space inside the folder, and choose **Open
   PowerShell window here** (on Windows 11: **Open in Terminal**).
2. Run the installer with the full path to your `python.exe`, e.g.:

   ```
   .\install-with-own-python.bat C:\Users\you\AppData\Local\Programs\Python\Python312\python.exe
   ```

   To find the path, run `py -3.12 -c "import sys; print(sys.executable)"`,
   or look at where Python was installed.

**Prefer to install by hand?** These are the same steps as the installer,
run in PowerShell in the `crop-labeller` folder:

```
py -3.12 -m venv .venv
.venv\Scripts\python -m pip install --no-index --find-links wheelhouse -r requirements.txt
.venv\Scripts\python run.py
```

`requirements.txt` pins the exact versions that are in `wheelhouse` and
that the app is tested with.

- **Using wheels you downloaded yourself** instead of the included
  `wheelhouse`? Point `--find-links` at your folder, and install by name so
  pip picks versions from what you have:
  `.venv\Scripts\python -m pip install --no-index --find-links C:\path\to\your\wheels streamlit pandas plotly`.
  The app needs Streamlit ≥ 1.38, pandas ≥ 2.2 and Plotly ≥ 5.24.
- **Using `uv`** (already installed offline)? Run
  `uv venv --python C:\path\to\python.exe`, then
  `uv pip install --offline --no-index --find-links wheelhouse -r requirements.txt`,
  then `.venv\Scripts\python run.py`. (Plain `uv run run.py` won't work
  offline: it tries to download packages.)

### Option C — Install with `uv` (Mac, or any computer with internet)

`uv` is a small helper program that sets up everything else automatically,
so you don't need to install Python separately. It needs internet.

1. **Install `uv`.** Open a terminal:
   - **Mac**: open **Terminal** (search for it with Spotlight, `Cmd+Space`).
   - **Windows**: press the Start button, type `PowerShell`, and open
     **Windows PowerShell**.

   Copy-paste the line for your computer and press **Enter**:

   **Mac:**
   ```
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

   **Windows (PowerShell):**
   ```
   powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
   ```

   It takes a few seconds. You won't need to do this again on this computer.
2. **Get the project folder.** Download it as a `.zip` (from the link you
   were given, or **Code → Download ZIP** on the GitHub page). Unzip it:
   double-click it on a Mac, or right-click → **Extract All** on Windows.
   You'll get a folder named something like `crop-labeller`. Put it
   somewhere easy to find, like your Desktop.

**That's all the setup.** Go to
[Section 3](#3-every-time-you-want-to-review-data).

---

## 3. Every time you want to review data

### Step 1 — Put your CSV file in the `data` folder

1. Open the `crop-labeller` folder.
2. Open the `data` folder inside it.
3. Drag and drop your assigned CSV file (the one with the datapoints you
   need to review) into this `data` folder — just like copying any file.

That's the only file-handling step. You never need to open or edit the
CSV yourself.

### Step 2 — Start the app

**Option A or B (Windows package):** double-click
**`start-crop-labeller.bat`** in the `crop-labeller` folder. A black window
opens.

**Option C (`uv`):** open a terminal in the `crop-labeller` folder (not
inside `data`):

- **Mac**: right-click the `crop-labeller` folder and choose **New Terminal
  at Folder** (or open Terminal, drag the folder into it, and press Enter).
- **Windows**: inside the `crop-labeller` folder, hold **Shift**,
  **right-click** empty space, and choose **Open PowerShell window here**
  (on Windows 11: **Open in Terminal**).

Then paste this and press **Enter**:

```
uv run run.py
```

The first time, this takes a minute or two while it installs everything
the app needs. After that it starts in a few seconds.

**Either way**, a browser tab opens with the app a few seconds later. If
it doesn't, look in the black/terminal window for a line like
`URL: http://localhost:8501` and paste that address into your browser.

**Leave that window open** while you work. Closing it stops the app. You
can minimize it and ignore it otherwise.

---

## 4. Understanding the screen

### Top of the page

- **🌾 Crop Labeller** — the app name, top left.
- **📄 Working on `<filename>`** — top right, confirms which CSV you're
  currently reviewing (useful if more than one file is in `data/`).
- If more than one CSV is in `data/`, a dropdown in the left sidebar lets
  you pick which one to work on.

### Left sidebar

- **Progress** — how many rows you've reviewed out of the total, as a
  count, a percentage, and a progress bar. This is saved automatically —
  closing and reopening the app later picks up exactly where you left off.
- **This file** — a quick summary of what's in the CSV: how many rows are
  currently labelled wheat vs. non-wheat, and (if available) how many rows
  an automated check flagged as possibly mislabelled.

### The two filter rows

- **Show**: `All` / `Unreviewed` / `Reviewed`. Switch to **Unreviewed** to
  only step through rows you haven't gotten to yet — the most useful
  setting for a normal review session.
- **🎯 Confidence filter** (only appears if the file has confidence
  scoring): click it to open a small panel where you can:
  - Turn the filter on/off.
  - Choose whether to look at the **wheat** rows or the **non-wheat**
    rows.
  - Drag a slider to pick a percentage (e.g. 10%) — this shows only the
    rows whose "how well does this match a typical curve" score is in the
    bottom N% for that group, i.e. the most suspicious/least confident
    ones. A live count tells you how many rows that is.

  This is a good way to triage: turn it on, start with a low percentage
  like 5–10%, and work through the most questionable rows first before
  moving to a general pass.

Whatever's on the right side of the top row (e.g. `4454 / 9934 · sample
1695 · Not yet reviewed`) tells you exactly where you are and, if a
filter is active, your position within the filtered set too.

### The main plot

For the row currently on screen, you'll see a chart with the growing
season along the bottom (October through May, in half-month steps) and
NDVI values (a measure of how "green"/vegetated the ground looked from
satellite) up the side. Up to three lines can appear:

- **Original** (solid, with dots) — the row's actual recorded values.
  This is the real data point you're judging.
- **Smoothed** (thinner blue line, if available) — the same curve with
  noise smoothed out, useful for seeing the overall shape more clearly.
- **Regional mean** + a shaded band (if available) — what a *typical*
  wheat curve looks like for this region and season, ± one standard
  deviation. Compare your row's curve against this band: a wheat-labelled
  row that looks nothing like it, or a non-wheat row that matches it
  closely, is worth a second look. A caption under the chart tells you how
  many samples that reference curve is based on — treat a reference built
  from very few samples with a bit more caution.

Hover your mouse anywhere on the chart to see the exact values for that
time period across all the lines at once, with a line marking exactly
where you're pointing.

Below the chart, an **Other fields** section (click to expand) shows any
extra columns from the CSV — coordinates, region, cover area, and so on —
for additional context if you need it.

### The review panel (right side)

- **Original label** — what the row is currently labelled as in the file.
- **Label confidence** (if available) — a colored badge (green/orange/red)
  showing how well an automated check thinks the current label matches
  the curve's shape. Low confidence doesn't mean it's wrong, just that
  it's worth a closer look.
- A **warning banner** (if available) explains specifically what looks
  off, e.g. *"Labeled non-wheat, but its NDVI shape looks like a typical
  wheat curve."*
- **Label** — click **wheat** or **non-wheat** to set what you believe the
  correct label is. The whole page background tints a very pale green or
  red to match your current choice — a quick visual double-check before
  you save.
- **Comment** (optional) — a text box for notes, e.g. why you think a
  label is wrong, or anything unusual about the curve.
- If you've changed something but haven't clicked Save yet, a small
  **🖊️ Unsaved change** note appears as a reminder.
- **Prev** / **Next** — move to the previous/next row (respecting
  whatever Show/Confidence filters are active).
- **Save** — saves your label and comment for this row, and automatically
  moves to the next row.
- **Jump to row** — type a row number to go straight to it.

---

## 5. Reviewing a row, step by step

1. Look at the **Original** curve and, if shown, the **Regional mean**
   band and **Smoothed** curve.
2. Check the **Original label** and, if shown, the **confidence badge**
   and **warning banner**.
3. Decide: does the curve genuinely look like wheat, or not?
4. Click **wheat** or **non-wheat** under **Label** (leave it unchanged if
   you agree with the original).
5. Optionally, type a note in **Comment** — especially useful for
   borderline or unusual cases, so whoever looks at this later understands
   your reasoning.
6. Click **Save**. You'll move automatically to the next row (unless
   you're already on the last row matching your current filters, in which
   case you'll stay put — your save still went through).
7. Repeat. Use the **Show** and **Confidence filter** controls any time to
   change which rows you're stepping through.

---

## 6. Finishing up

Your work is saved continuously — every click of **Save** writes to disk
immediately, so there's no separate "submit" step and nothing is lost if
you close the app partway through.

When you're done (or want to hand off progress), look in the `output`
folder inside `crop-labeller`. For a file named e.g. `MyFile.csv`, you'll
find:

- **`MyFile_labelled.csv`** — the full dataset with your corrected labels.
- **`MyFile_review_meta.csv`** — a log of every row you reviewed: the
  original label, your label, your comment, and when you reviewed it.

Send both of these files back (however you were asked to — email, shared
drive, etc.). Your original input CSV in `data/` is never changed.

---

## 7. Stopping the app

Close the black/terminal window (or click into it and press **Ctrl+C**).
To work again later, repeat [Section 3](#3-every-time-you-want-to-review-data).
Your progress will still be there.

---

## 8. Troubleshooting

### Setting up and starting

**"Windows protected your PC"** when you double-click a `.bat` → click
**More info** → **Run anyway**. (Unblocking the zip before extracting, in
Option A step 2, prevents this.)

**"Can't find python\python.exe next to this file"** → you ran it from
inside the zip, or only copied some of the files. Extract the whole zip and
run the `.bat` inside the extracted `crop-labeller` folder.

**"Setup hasn't been run yet"** (Option B) → double-click
`install-with-own-python.bat` first.

**The install stops with an error about a package or version** (Option B)
→ your Python must be **3.12, 64-bit**. Check with
`py -3.12 -c "import sys, struct; print(sys.version, struct.calcsize('P') * 8, 'bit')"`.
If it's a different version, use Option A instead. It has its own Python.

**Extracting fails with "path too long" or "file name too long"** → extract
to a shorter place instead, e.g. type `C:\cl` as the destination in
**Extract All**.

**The browser didn't open automatically** → copy the
`http://localhost:8501`-style address printed in the black/terminal window
and paste it into your browser's address bar.

**Which version do I have?** (Options A and B) Open `VERSION.txt` in the
`crop-labeller` folder, and include it if you report a problem.

### While using the app

**"No CSV files found in `data`"** → you haven't put a CSV file directly
in the `data` folder yet (not in a subfolder). Add it and reload the page
(F5 in your browser).

**"Couldn't read `<file>`..."** → the file isn't in the expected format.
Double check it's the CSV you were given, and that it wasn't accidentally
edited or renamed. If you have more than one CSV in `data/`, make sure the
right one is selected in the sidebar.

**I closed the black/terminal window by accident** → no problem, nothing
is lost. Start the app again ([Section 3, Step 2](#step-2--start-the-app));
your saved progress is still there.

**The app looks broken/stuck** → reload the page (F5). If that doesn't
help, close the black/terminal window and start the app again
([Section 3, Step 2](#step-2--start-the-app)).

**I want to review a different file** → either remove the current CSV
from `data/` and add the new one, or keep both in `data/` and pick the one
you want from the dropdown that appears in the sidebar.

---

Questions or something not working as described here? Reach out to
whoever gave you this tool.
