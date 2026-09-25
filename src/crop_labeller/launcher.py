"""Launches the Streamlit app as a subprocess (so `uv run crop-labeller` just works)."""

from __future__ import annotations

import sys
from pathlib import Path

from streamlit.web import cli as stcli

# Defaults for a local, single-user, possibly offline tool. They come before any
# user-supplied flags, so those still win (the last value given for an option wins).
DEFAULT_FLAGS = [
    # Otherwise a fresh machine blocks on an interactive "Email:" prompt in the
    # terminal before the app ever opens.
    "--server.showEmailPrompt=false",
    # Bind to this machine only: no Windows Firewall "allow access?" popup, and
    # the app isn't reachable from elsewhere on the network.
    "--server.address=localhost",
    "--browser.gatherUsageStats=false",
]


def main() -> None:
    app_path = Path(__file__).resolve().parent / "app.py"
    sys.argv = ["streamlit", "run", str(app_path), *DEFAULT_FLAGS, *sys.argv[1:]]
    sys.exit(stcli.main())


if __name__ == "__main__":
    main()
