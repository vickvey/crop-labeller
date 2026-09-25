#!/bin/sh
# Launcher for the offline Linux packages (mainly used to smoke-test the bundle layout).
cd "$(dirname "$0")" || exit 1
if [ -x python/bin/python3 ]; then PY=python/bin/python3
elif [ -x .venv/bin/python ]; then PY=.venv/bin/python
else echo "No python/ or .venv/ found: run ./install-with-own-python.sh first." >&2; exit 1
fi
exec "$PY" -E -s run.py "$@"
