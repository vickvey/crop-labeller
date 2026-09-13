"""Streamlit app for reviewing/correcting crop labels from NDVI CSVs."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from crop_labeller.data import CsvSchema, label_display, label_options, list_csv_files, load_csv
from crop_labeller.ndvi_periods import NDVI_PERIODS, period_short_label
from crop_labeller.reference import load_region_reference
from crop_labeller.state import ReviewState, write_outputs

PROJECT_ROOT = Path(__file__).resolve().parents[2]
# Input CSVs live under data/csv/ — data/ also holds plots/ (diagnostic PNGs
# from the outlier-scoring pipeline) and a confidence_check_summary_*.csv
# that aren't per-row datapoint files, so we scan the csv/ subfolder
# specifically rather than data/ itself.
DATA_DIR = PROJECT_ROOT / "data" / "csv"
OUTPUT_DIR = PROJECT_ROOT / "output"

# Human-readable explanations for the outlier-scoring pipeline's flag values.
# None means "nothing suspicious, don't show a warning".
FLAG_DESCRIPTIONS: dict[str, str | None] = {
    "ok": None,
    "labeled_wheat_atypical_profile": (
        "Labeled **wheat**, but its NDVI shape looks atypical for wheat in this region/year."
    ),
    "labeled_nonwheat_wheatlike_profile": (
        "Labeled **non-wheat**, but its NDVI shape looks like a typical wheat curve."
    ),
}


st.set_page_config(page_title="Crop Labeller", page_icon="🌾", layout="wide")


@st.cache_data(show_spinner=False)
def _cached_load_csv(path_str: str, mtime: float) -> tuple[pd.DataFrame, CsvSchema]:
    return load_csv(Path(path_str))


@st.cache_data(show_spinner=False)
def _cached_region_reference(region: str, year: str) -> pd.DataFrame | None:
    return load_region_reference(region, year)


def get_review_state(csv_path: Path, total_rows: int) -> ReviewState:
    key = f"review_state::{csv_path.name}"
    cached = st.session_state.get(key)
    if cached is None:
        cached = ReviewState.load_or_create(OUTPUT_DIR, csv_path, total_rows)
        st.session_state[key] = cached
    return cached


def format_value(value: object) -> str:
    if isinstance(value, float):
        return f"{value:.6g}"
    return str(value)


def confidence_badge(score: float) -> str:
    pct = f"{score * 100:.0f}%"
    if score >= 0.7:
        return f":green[{pct} confident]"
    if score >= 0.4:
        return f":orange[{pct} confident]"
    return f":red[{pct} confident]"


def render_metadata_panel(row: pd.Series, schema: CsvSchema) -> None:
    skip = (
        set(schema.ndvi_columns)
        | set(schema.ndvi_smooth_columns)
        | {schema.id_column, schema.label_column}
    )
    if schema.label_text_column:
        skip.add(schema.label_text_column)
    if schema.confidence_column:
        skip.add(schema.confidence_column)
    if schema.flag_column:
        skip.add(schema.flag_column)
    context_cols = [c for c in schema.original_columns if c not in skip]
    if not context_cols:
        return
    values = [format_value(row[c]) for c in context_cols]
    context_df = pd.DataFrame({"field": context_cols, "value": values})
    st.dataframe(context_df, hide_index=True, width="stretch", height=min(38 * len(context_cols) + 38, 320))


def render_ndvi_plot(
    row: pd.Series, schema: CsvSchema, row_id: object, reference_df: pd.DataFrame | None = None
) -> None:
    x = list(range(1, len(schema.ndvi_columns) + 1))
    y = [row[c] for c in schema.ndvi_columns]

    # The Oct-to-May fortnight mapping only makes sense for the standard
    # 14-step wheat season; anything else falls back to plain step numbers.
    use_periods = len(schema.ndvi_columns) == len(NDVI_PERIODS)
    season_start_year = next((row[c] for c in row.index if c.lower() == "year"), None)

    # Plot against the period labels themselves (as a categorical axis)
    # rather than bare step numbers. That gives every trace a shared x
    # position to align on, which is what lets a single hover show a
    # vertical line cutting through the sample, the regional mean, and the
    # std-dev band all at once, labelled by the period being pointed at.
    x_labels = [period_short_label(i) if use_periods else str(i) for i in x]
    year_suffix = f", {int(season_start_year) + 1}" if use_periods and season_start_year is not None else ""

    # Only trust the smoothed series if it's the same length as the raw one
    # (i.e. actually aligned, step for step) — otherwise skip it silently.
    has_smoothed = len(schema.ndvi_smooth_columns) == len(schema.ndvi_columns) and schema.ndvi_smooth_columns
    smooth_y = [row[c] for c in schema.ndvi_smooth_columns] if has_smoothed else None

    fig = go.Figure()

    show_legend = reference_df is not None or has_smoothed
    if reference_df is not None:
        ref_x = reference_df["step"].tolist()
        ref_labels = [period_short_label(i) if use_periods else str(i) for i in ref_x]
        upper = (reference_df["ndvi_mean"] + reference_df["ndvi_std"]).tolist()
        lower = (reference_df["ndvi_mean"] - reference_df["ndvi_std"]).tolist()
        fig.add_trace(
            go.Scatter(
                x=ref_labels, y=upper, mode="lines", line=dict(width=0), hoverinfo="skip", showlegend=False
            )
        )
        fig.add_trace(
            go.Scatter(
                x=ref_labels,
                y=lower,
                mode="lines",
                line=dict(width=0),
                fill="tonexty",
                fillcolor="rgba(120,120,120,0.18)",
                name="±1 std range",
                hoverinfo="skip",
            )
        )
        fig.add_trace(
            go.Scatter(
                x=ref_labels,
                y=reference_df["ndvi_mean"].tolist(),
                mode="lines",
                line=dict(color="#666666", width=2, dash="dash"),
                name="Regional mean",
                hovertemplate="Regional mean NDVI %{y:.3f}<extra></extra>",
            )
        )

    if smooth_y is not None:
        fig.add_trace(
            go.Scatter(
                x=x_labels,
                y=smooth_y,
                mode="lines",
                line=dict(color="#1565c0", width=2.5),
                name="Smoothed (Savitzky–Golay)",
                hovertemplate="Smoothed NDVI %{y:.3f}<extra></extra>",
            )
        )

    fig.add_trace(
        go.Scatter(
            x=x_labels,
            y=y,
            mode="lines+markers",
            line=dict(color="#2e7d32", width=3),
            marker=dict(size=7),
            name="Original",
            hovertemplate="NDVI %{y:.3f}<extra></extra>",
        )
    )
    fig.update_layout(
        title=f"NDVI time series — sample {row_id}",
        xaxis_title="Wheat-season fortnight" if use_periods else "NDVI time steps",
        yaxis_title="NDVI values",
        xaxis=dict(
            type="category",
            categoryorder="array",
            categoryarray=x_labels,
            tickangle=-45,
            showspikes=True,
            spikemode="across",
            spikesnap="hovered data",  # jump to the whole fortnight slot, not the raw cursor pixel
            spikethickness=2,  # a real crosshair, not a fake band — spikes draw *above*
            # traces, so anything thick enough to look like a shaded region would
            # paint over the curves it's meant to help you read.
            spikedash="solid",
            spikecolor="rgba(46,125,50,0.7)",
        ),
        yaxis_range=[-0.05, 1.0],
        template="plotly_white",
        height=560,
        margin=dict(l=40, r=20, t=50, b=40),
        showlegend=show_legend,
        hovermode="x unified",
        hoverlabel=dict(font_size=13),
        legend=dict(
            orientation="h",
            yanchor="top",
            y=-0.35,
            xanchor="center",
            x=0.5,
            font=dict(size=12),
        ),
    )
    if use_periods and season_start_year is not None:
        # x unified's shared header shows the short category label (e.g.
        # "Jan (1st half)"); this note spells out the actual calendar year
        # split it represents, once, instead of cluttering every hover.
        fig.add_annotation(
            text=f"Oct–Dec {int(season_start_year)} · Jan–May{year_suffix}",
            xref="paper",
            yref="paper",
            x=1,
            y=1.08,
            showarrow=False,
            font=dict(size=11, color="#888888"),
            xanchor="right",
        )
    st.plotly_chart(fig, width="stretch")


def inject_css() -> None:
    st.markdown(
        """
        <style>
        html, body, [data-testid="stAppViewContainer"] { font-size: 17px; }

        [data-testid="stMainBlockContainer"], .block-container {
            max-width: 1440px;
            margin: 0 auto;
            padding-top: 2rem;
        }

        h1 { font-size: 2.1rem !important; }
        h3 { font-size: 1.35rem !important; }

        [data-testid="stCaptionContainer"] p { font-size: 0.95rem !important; }
        [data-testid="stMarkdownContainer"] p { font-size: 1.05rem !important; line-height: 1.6 !important; }

        [data-testid="stRadio"] label p { font-size: 1.05rem !important; }
        [data-testid="stTextArea"] textarea { font-size: 1.05rem !important; }
        [data-testid="stNumberInput"] input { font-size: 1.05rem !important; }

        [data-testid="stButton"] button {
            font-size: 1.05rem !important;
            padding: 0.55rem 1rem !important;
        }
        [data-testid="stButton"] { margin-top: 0.3rem; }

        [data-testid="stHorizontalBlock"] { gap: 1.75rem; }
        [data-testid="stVerticalBlock"] { gap: 1rem; }

        [data-testid="stRadio"], [data-testid="stTextArea"] { margin-bottom: 0.6rem; }
        </style>
        """,
        unsafe_allow_html=True,
    )


def main() -> None:
    inject_css()
    st.title("🌾 Crop Labeller")

    csv_files = list_csv_files(DATA_DIR)
    if not csv_files:
        st.warning(f"No CSV files found in `{DATA_DIR}`. Add one and reload the page.")
        return

    if len(csv_files) == 1:
        selected_path = csv_files[0]
        st.sidebar.caption(f"Input file: **{selected_path.name}**")
    else:
        names = [p.name for p in csv_files]
        chosen = st.sidebar.selectbox("Input CSV", names, key="selected_csv_name")
        selected_path = DATA_DIR / chosen

    st.caption(f"📄 Working on **`{selected_path.name}`**")

    if st.session_state.get("_active_csv") != selected_path.name:
        st.session_state["_active_csv"] = selected_path.name
        st.session_state["row_idx"] = 0

    df, schema = _cached_load_csv(str(selected_path), selected_path.stat().st_mtime)
    total_rows = len(df)
    state = get_review_state(selected_path, total_rows)

    # --- Sidebar: progress ---
    reviewed = state.reviewed_count()
    fraction = state.progress_fraction()
    st.sidebar.subheader("Progress")
    st.sidebar.markdown(
        f"Reviewed: **{reviewed} / {total_rows}**  \n"
        f"Progress: **{fraction * 100:.1f}%**  \n"
        f"Remaining: **{total_rows - reviewed}**"
    )
    st.sidebar.progress(fraction)

    # --- Navigation state ---
    row_idx = st.session_state.get("row_idx", 0)
    row_idx = max(0, min(row_idx, total_rows - 1))
    # Sync the "Jump to row" box to the current row *before* that widget is
    # instantiated below. Session state for a keyed widget can only be set
    # before its widget is created in a given run, so this must happen here,
    # not inside a button handler that runs after the widget already exists.
    st.session_state["jump_input"] = row_idx + 1

    def go_to(idx: int) -> None:
        st.session_state["row_idx"] = max(0, min(idx, total_rows - 1))

    def jump_callback() -> None:
        go_to(st.session_state["jump_input"] - 1)

    ids = df[schema.id_column].tolist()
    reviewed_mask = [state.is_reviewed(i) for i in ids]

    def filtered_indices(mode: str) -> list[int]:
        if mode == "Unreviewed":
            return [i for i in range(total_rows) if not reviewed_mask[i]]
        if mode == "Reviewed":
            return [i for i in range(total_rows) if reviewed_mask[i]]
        return list(range(total_rows))

    def step(filtered: list[int], idx: int, direction: int) -> int | None:
        """Next/previous index within `filtered`, relative to `idx`.

        `idx` need not itself be in `filtered` (e.g. its review status just
        changed, or the filter was just switched) — in that case we look for
        the nearest filtered entry strictly in the requested direction,
        rather than snapping to whichever end is closer.
        """
        if idx in filtered:
            new_pos = filtered.index(idx) + direction
            return filtered[new_pos] if 0 <= new_pos < len(filtered) else None
        if direction > 0:
            after = [i for i in filtered if i > idx]
            return after[0] if after else None
        before = [i for i in filtered if i < idx]
        return before[-1] if before else None

    row = df.iloc[row_idx]
    row_id = row[schema.id_column]
    is_reviewed = state.is_reviewed(row_id)

    # --- Compact top bar: just the filter + row status, one line, no
    # scrolling needed to reach it. Previous/Next/Save/Jump-to-row live
    # further down, right next to the plot and label controls, since
    # that's where your eyes and mouse already are while reviewing a row. ---
    mode_col, status_col = st.columns([1.4, 2.6])
    with mode_col:
        st.caption("Show")
        nav_mode = st.radio(
            "Show",
            options=["All", "Unreviewed", "Reviewed"],
            key="nav_mode",
            horizontal=True,
            label_visibility="collapsed",
        )

    filtered = filtered_indices(nav_mode)
    prev_target = step(filtered, row_idx, -1)
    next_target = step(filtered, row_idx, 1)

    with status_col:
        st.caption("Row")
        badge = ":green[Reviewed]" if is_reviewed else ":blue[Not yet reviewed]"
        status_line = f"**{row_idx + 1} / {total_rows}** &middot; sample `{row_id}` &middot; {badge}"
        if nav_mode != "All" and row_idx in filtered:
            status_line += f"  \n{nav_mode.lower()} {filtered.index(row_idx) + 1} / {len(filtered)}"
        st.markdown(status_line)

    if not filtered:
        st.info("No rows match the current filter.")

    # --- Plot + review controls, side by side, so both fit on screen at once. ---
    region_value = row[schema.region_column] if schema.region_column else None
    year_value = row[schema.year_column] if schema.year_column else None
    reference_df = (
        _cached_region_reference(str(region_value), str(year_value))
        if region_value is not None and year_value is not None
        else None
    )

    plot_col, review_col = st.columns([2.8, 1])
    with plot_col:
        render_ndvi_plot(row, schema, row_id, reference_df)
        if region_value is not None and year_value is not None and reference_df is None:
            st.caption(f"No reference available for {region_value} ({year_value}).")
        with st.expander("Other fields"):
            render_metadata_panel(row, schema)

    with review_col:
        original_label = row[schema.label_column]
        existing_review = state.get(row_id)
        default_label = existing_review["updated_label"] if existing_review else original_label
        default_comment = existing_review["comment"] if existing_review else ""

        options = label_options(schema, df)
        try:
            default_index = options.index(default_label)
        except ValueError:
            default_index = 0

        st.caption(f"Original label: {label_display(schema, original_label)}")

        if schema.confidence_column:
            confidence_value = row[schema.confidence_column]
            st.markdown(f"Label confidence: {confidence_badge(confidence_value)}")
        if schema.flag_column:
            flag_value = row[schema.flag_column]
            flag_message = FLAG_DESCRIPTIONS.get(flag_value, f"Flagged: `{flag_value}`")
            if flag_message:
                st.warning(flag_message, icon="⚠️")

        chosen_label = st.radio(
            "Label",
            options=options,
            index=default_index,
            format_func=lambda v: label_display(schema, v),
            key=f"label_{row_id}",
            horizontal=True,
        )
        comment = st.text_area(
            "Comment (optional)",
            value=default_comment,
            key=f"comment_{row_id}",
            height=70,
        )

        prev_btn_col, next_btn_col = st.columns(2)
        with prev_btn_col:
            if st.button("⬅ Prev", disabled=prev_target is None, width="stretch"):
                go_to(prev_target)
                st.rerun()
        with next_btn_col:
            if st.button("Next ➡", disabled=next_target is None, width="stretch"):
                go_to(next_target)
                st.rerun()

        if st.button("💾 Save", type="primary", width="stretch"):
            state.set_review(row_id, original_label, chosen_label, comment)
            state.save()
            write_outputs(df, schema, state, OUTPUT_DIR, selected_path)
            st.toast(f"Saved sample {row_id}", icon="✅")
            if next_target is not None:
                go_to(next_target)
            st.rerun()

        st.number_input(
            "Jump to row",
            min_value=1,
            max_value=total_rows,
            key="jump_input",
            on_change=jump_callback,
        )


if __name__ == "__main__":
    main()
