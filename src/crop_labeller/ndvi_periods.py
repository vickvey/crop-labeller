"""Maps NDVI_1..NDVI_14 to the fortnightly wheat-season periods they represent.

The 14-step NDVI series covers one wheat growing season, starting in the
second half of October and running through the first half of May the
following calendar year.
"""

from __future__ import annotations

# (month, half-of-month, year_offset from the season's start year)
NDVI_PERIODS: list[tuple[str, int, int]] = [
    ("October", 2, 0),
    ("November", 1, 0),
    ("November", 2, 0),
    ("December", 1, 0),
    ("December", 2, 0),
    ("January", 1, 1),
    ("January", 2, 1),
    ("February", 1, 1),
    ("February", 2, 1),
    ("March", 1, 1),
    ("March", 2, 1),
    ("April", 1, 1),
    ("April", 2, 1),
    ("May", 1, 1),
]


def _half_text(half: int) -> str:
    return "1st half" if half == 1 else "2nd half"


def period_short_label(step: int) -> str:
    """Compact x-axis label for NDVI step `step` (1-indexed), e.g. 'Oct (2nd half)'."""
    if not 1 <= step <= len(NDVI_PERIODS):
        return f"Step {step}"
    month, half, _ = NDVI_PERIODS[step - 1]
    return f"{month[:3]} ({_half_text(half)})"


def period_full_label(step: int, season_start_year: object | None = None) -> str:
    """Full descriptive label for hovers, e.g. 'January 1st half, 2022'.

    `season_start_year` is the calendar year the season started in (the
    dataset's own `year` field, e.g. 2021 for an Oct-2021-to-May-2022
    season). The year is omitted from the label when not provided.
    """
    if not 1 <= step <= len(NDVI_PERIODS):
        return f"Time step {step}"
    month, half, year_offset = NDVI_PERIODS[step - 1]
    label = f"{month} {_half_text(half)}"
    if season_start_year is not None:
        try:
            label += f", {int(season_start_year) + year_offset}"
        except (TypeError, ValueError):
            pass
    return label
