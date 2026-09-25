# Crop Labeller — Researcher Guide

This guide is for reviewing wheat NDVI labels — no coding or "developer"
background needed. You already know wheat when you see its curve; this
just walks you through the screen, click by click.

You'll only touch the terminal (the black/blue text window, sometimes
called "command prompt" or "PowerShell") for **one thing**: pasting a
single command to start the app. Everything else — picking your file,
looking at data, saving your work — happens by clicking in your web
browser, same as any website.

---

## 1. One-time setup

Do this once, the first time you use the tool.

### Step 1 — Install `uv`

`uv` is a small helper program that sets up everything else automatically
(you will not need to separately install Python).

> **Computer with no internet access?** Installing `uv` needs the
> internet. Skip Sections 1 and 2 and follow
> [Section 8 — Offline computers](#8-offline-computers-no-internet-no-uv)
> instead. It's a ready-made package: unzip it and double-click.

1. Open a terminal:
   - **Windows**: press the Start button, type `PowerShell`, and open
     **Windows PowerShell**.
   - **Mac**: open **Terminal** (search for it with Spotlight, `Cmd+Space`).
2. Copy-paste one of these into the window and press **Enter**:

   **Windows (PowerShell):**
   ```
   powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
   ```

   **Mac:**
   ```
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```
3. Wait for it to finish (a few seconds). You can close this window now —
   you won't need to repeat this step again on this computer.

### Step 2 — Get the project folder

You'll receive this either as a link to download, or a `.zip` file
directly. Either way:

1. Download the `.zip` file.
2. In **File Explorer** (Windows) or **Finder** (Mac), find the downloaded
   `.zip`, right-click it, and choose **Extract All** (Windows) or
   double-click it (Mac) to unzip it.
3. You'll get a folder named something like `crop-labeller`. Put it
   somewhere easy to find, like your Desktop.

That's it for one-time setup.

---

## 2. Every time you want to review data

### Step 1 — Put your CSV file in the `data` folder

1. Open the `crop-labeller` folder you extracted.
2. Open the `data` folder inside it.
3. Drag and drop your assigned CSV file (the one with the datapoints you
   need to review) into this `data` folder — just like copying any file
   in Windows/Mac.

That's the only file-handling step. You never need to open or edit the
CSV yourself.

### Step 2 — Open a terminal right there

The easiest way, so you don't need to type any folder paths:

- **Windows**: inside the `crop-labeller` folder (not inside `data`, the
  folder one level up), hold **Shift** and **right-click** on empty space,
  then choose **Open PowerShell window here** (or **Open Terminal here**
  on Windows 11).
- **Mac**: right-click the `crop-labeller` folder and choose
  **New Terminal at Folder** (or open Terminal and drag the folder into
  it, then press Enter).

### Step 3 — Start the app

In that terminal window, paste this and press **Enter**:

```
uv run run.py
```

The first time, this takes a minute or two — it's quietly installing
everything the app needs. Every time after that, it starts in a few
seconds.

A browser tab should open automatically showing the app. If it doesn't,
look in the terminal for a line like `Local URL: http://localhost:8501`
and paste that address into your browser.

**Leave the terminal window open** while you work — closing it stops the
app. You can minimize it and ignore it otherwise.

---

## 3. Understanding the screen

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

## 4. Reviewing a row, step by step

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

## 5. Finishing up

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

## 6. Stopping the app

Go back to the terminal window and press **Ctrl+C** (or just close the
window). To work again later, repeat [Section 2](#2-every-time-you-want-to-review-data) —
your progress will still be there.

---

## 7. Troubleshooting

**"No CSV files found in `data`"** — you haven't put a CSV file directly
in the `data` folder yet (not in a subfolder). Add it and reload the page
(F5 in your browser).

**"Couldn't read `<file>`..."** — the file isn't in the expected format.
Double check it's the CSV you were given, and that it wasn't accidentally
edited or renamed. If you have more than one CSV in `data/`, make sure the
right one is selected in the sidebar.

**The browser didn't open automatically** — copy the
`http://localhost:8501`-style address printed in the terminal and paste it
into your browser's address bar.

**I closed the terminal by accident** — no problem, nothing is lost. Just
repeat [Section 2](#2-every-time-you-want-to-review-data) to start again;
your saved progress is still there.

**The app looks broken/stuck** — reload the page (F5). If that doesn't
help, close the terminal, reopen it in the `crop-labeller` folder, and run
`uv run run.py` again.

**I want to review a different file** — either remove the current CSV
from `data/` and add the new one, or keep both in `data/` and pick the one
you want from the dropdown that appears in the sidebar.


---

## 8. Offline computers (no internet, no `uv`)

Use this if your computer can't reach the internet. There are two ready-made
downloads. Neither needs the internet on the computer that runs it:

| Download | Use it if | Setup |
|---|---|---|
| **`crop-labeller-<version>-windows-offline.zip`** (recommended) | You just want it to work | None. Python is built in, and it doesn't matter which Python (if any) the computer has. |
| `crop-labeller-<version>-windows-offline-own-python.zip` | Your computer must use its **own** Python **3.12 (64-bit)** | Run `install-with-own-python.bat` once. |

Both are on <https://github.com/vickvey/crop-labeller/releases/latest>
(under **Assets**), or you can get them from whoever gave you this tool.

### Getting the zip onto the computer (both downloads)

1. **Download** the zip on any computer with internet, and copy it to the
   offline computer, e.g. with a USB drive.
2. **Unblock it.** Right-click the zip → **Properties** → at the bottom,
   tick **Unblock** → **OK**. (If there's no Unblock box, skip this.) This
   stops Windows from showing warnings about the files inside.
3. **Extract it.** Right-click the zip → **Extract All...** → **Extract**.
   The suggested location is fine. You'll get a folder containing
   `crop-labeller`. Move that `crop-labeller` folder wherever you like, for
   example your Documents.

   Don't double-click files *inside* the zip without extracting it first.
   It won't work from there.

**With the recommended download, that's all the setup.** Skip to
[Every time you want to review data](#every-time-you-want-to-review-data).

### Only for the own-python download: one-time install

Double-click **`install-with-own-python.bat`** in the `crop-labeller`
folder. It finds your Python 3.12, creates a private `.venv` folder next to
it, and installs the included packages (from the `wheelhouse` folder, offline).
When it says **Setup finished**, press a key to close it. You only do this
once, or again if you move to a different Python.

If it says it **couldn't find a 64-bit Python 3.12**, give it the exact
path. Open PowerShell in the `crop-labeller` folder (see
[Section 2, Step 2](#step-2--open-a-terminal-right-there)) and run it with
the full path to your `python.exe`, e.g.:

```
.\install-with-own-python.bat C:\Users\you\AppData\Local\Programs\Python\Python312\python.exe
```

(To find the path, run `py -3.12 -c "import sys; print(sys.executable)"`,
or look at where Python was installed.)

**Prefer to do it by hand?** These are the same steps as the `.bat`, run in
PowerShell in the `crop-labeller` folder:

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

### Every time you want to review data

1. Put your CSV file(s) in the `data` folder inside `crop-labeller`
   (the same as [Section 2, Step 1](#step-1--put-your-csv-file-in-the-data-folder)).
2. Double-click **`start-crop-labeller.bat`** in the `crop-labeller` folder.
   A black window opens, and a few seconds later the app opens in your
   browser.
3. **Leave the black window open** while you work. Closing it stops the
   app. Your saved results appear in the `output` folder, and your progress
   is still there next time.

Everything in Sections 3–5 works exactly the same. Wherever the guide says
"run `uv run run.py`", double-click `start-crop-labeller.bat` instead.

### If something goes wrong

**"Windows protected your PC"** when you double-click a `.bat` → click
**More info** → **Run anyway**. (Unblocking the zip before extracting
prevents this.)

**"Can't find python\python.exe next to this file"** → you ran it from
inside the zip, or only copied some of the files. Extract the whole zip and
run the `.bat` inside the extracted `crop-labeller` folder.

**"Setup hasn't been run yet"** (own-python download) → double-click
`install-with-own-python.bat` first.

**The install stops with an error about a package or version** (own-python
download) → your Python must be **3.12, 64-bit**. Check with
`py -3.12 -c "import sys, struct; print(sys.version, struct.calcsize('P') * 8, 'bit')"`.
If it's a different version, use the recommended download instead. It has
its own Python.

**Extracting fails with "path too long" or "file name too long"** → extract
to a shorter place instead, e.g. type `C:\cl` as the destination in
**Extract All**.

**Which version do I have?** Open `VERSION.txt` in the `crop-labeller`
folder, and include it if you report a problem.

---

Questions or something not working as described here? Reach out to
whoever gave you this tool.
