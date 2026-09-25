"""Convenience entry point: `uv run run.py` (or plain `python run.py`) launches the labelling app."""

import sys
from pathlib import Path

# Make `crop_labeller` importable straight from src/, so `python run.py` works
# in a plain venv with only requirements.txt installed (offline setups, no uv).
sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from crop_labeller.launcher import main  # noqa: E402

if __name__ == "__main__":
    main()
