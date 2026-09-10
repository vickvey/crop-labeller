"""Launches the Streamlit app as a subprocess (so `uv run crop-labeller` just works)."""

from __future__ import annotations

import sys
from pathlib import Path

from streamlit.web import cli as stcli


def main() -> None:
    app_path = Path(__file__).resolve().parent / "app.py"
    sys.argv = ["streamlit", "run", str(app_path), *sys.argv[1:]]
    sys.exit(stcli.main())


if __name__ == "__main__":
    main()
