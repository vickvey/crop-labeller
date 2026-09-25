#!/bin/sh
# One-time setup for the Linux "own-python" package (smoke-test counterpart of
# install-with-own-python.bat): .venv from a Python 3.12 plus the included wheels, offline.
set -e
cd "$(dirname "$0")"
PY="${1:-python3.12}"
"$PY" -c 'import sys; sys.exit(0 if sys.version_info[:2] == (3, 12) else 1)' \
  || { echo "$PY is not Python 3.12" >&2; exit 1; }
rm -rf .venv
"$PY" -m venv .venv
.venv/bin/python -E -m pip install --no-index --find-links wheelhouse -r requirements.txt --disable-pip-version-check --quiet
.venv/bin/python -E -c "import streamlit, pandas, plotly"
echo "Setup finished. Run ./start-crop-labeller.sh to start the app."
