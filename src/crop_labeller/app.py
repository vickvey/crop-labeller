"""Streamlit app for reviewing/correcting crop labels from NDVI CSVs."""

from __future__ import annotations

import html
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from crop_labeller.data import CsvSchema, label_display, label_options, list_csv_files, load_csv
from crop_labeller.ndvi_periods import NDVI_PERIODS, period_short_label
from crop_labeller.reference import load_region_reference
from crop_labeller.state import ReviewState, write_outputs

PROJECT_ROOT = Path(__file__).resolve().parents[2]
# Researchers drop their assigned CSV(s) straight into data/. That folder
# may also hold plots/ (diagnostic PNGs from the outlier-scoring pipeline)
# and a confidence_check_summary_*.csv report - list_csv_files() ignores
# the latter by name, and glob("*.csv") never descends into plots/.
DATA_DIR = PROJECT_ROOT / "data"
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


# Palest possible tints — a hint, not a highlight. Only meaningful for this
# project's wheat(1)/non-wheat(0) convention, so it's gated on the label
# text actually saying that (see inject_label_background) rather than just
# assuming any 0/1-labelled dataset means the same thing.
LABEL_BACKGROUND_TINTS = {1: "#f2f9f2", 0: "#fdf2f2"}  # pale green (wheat) / pale red (non-wheat)


def inject_label_background(schema: CsvSchema, label_value: object) -> None:
    """Tint the page background to reflect the *currently selected* label -
    an at-a-glance confirmation of what's about to be saved. Light-mode
    only: a pale wash would look wrong, not subtle, against a dark theme,
    and there's no reliable way from here to tell dark mode was chosen
    manually inside Streamlit rather than inherited from the OS.
    """
    if (
        schema.label_text_map.get(1, "").lower() != "wheat"
        or schema.label_text_map.get(0, "").lower() != "non_wheat"
    ):
        return
    color = LABEL_BACKGROUND_TINTS.get(label_value)
    if color is None:
        return
    st.markdown(
        f"""
        <style>
        @media (prefers-color-scheme: light) {{
            [data-testid="stAppViewContainer"] {{ background-color: {color}; }}
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def outlier_row_ids_for_percentile(
    df: pd.DataFrame, schema: CsvSchema, label_value: object, percentile: float
) -> tuple[set, int, int]:
    """Row ids whose confidence score is in the bottom `percentile`% *within
    rows sharing `label_value`* (the pipeline flags outliers separately per
    label population, since a "confidently wheat" score isn't comparable to
    a "confidently non-wheat" score on the same absolute scale).

    Returns (matched_ids, matched_count, population_count).
    """
    population_mask = df[schema.label_column] == label_value
    population_count = int(population_mask.sum())
    scores = df.loc[population_mask, schema.confidence_column]
    valid_scores = scores.dropna()
    if valid_scores.empty:
        return set(), 0, population_count

    threshold = valid_scores.quantile(percentile / 100)
    matched_mask = population_mask & df[schema.confidence_column].notna() & (df[schema.confidence_column] <= threshold)
    matched_ids = set(df.loc[matched_mask, schema.id_column].tolist())
    return matched_ids, int(matched_mask.sum()), population_count


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

        /* Columns sit side by side starting from the same top edge, so a
           button (e.g. the confidence-filter popover trigger) never drifts
           below/above a radio group or plain text in a neighboring column -
           without this, taller columns can vertically center shorter ones. */
        [data-testid="stHorizontalBlock"] { gap: 1.75rem; align-items: flex-start; }
        [data-testid="stVerticalBlock"] { gap: 1rem; }

        [data-testid="stRadio"], [data-testid="stTextArea"] { margin-bottom: 0.6rem; }
        </style>
        """,
        unsafe_allow_html=True,
    )


def main() -> None:
    inject_css()

    # Belt-and-braces: make sure these exist even if git didn't check out an
    # empty data/csv/ (it's gitignored) or output/ was deleted by hand.
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    csv_files = list_csv_files(DATA_DIR)
    if not csv_files:
        st.title("🌾 Crop Labeller")
        st.warning(f"No CSV files found in `{DATA_DIR}`. Add one and reload the page.")
        return

    if len(csv_files) == 1:
        selected_path = csv_files[0]
        st.sidebar.caption(f"Input file: **{selected_path.name}**")
    else:
        names = [p.name for p in csv_files]
        chosen = st.sidebar.selectbox("Input CSV", names, key="selected_csv_name")
        selected_path = DATA_DIR / chosen

    # Title and "which file" share one row (title left, filename flush
    # right) instead of stacking, to reclaim a full line of vertical space.
    title_col, file_col = st.columns([2, 3])
    with title_col:
        st.title("🌾 Crop Labeller")
    with file_col:
        st.markdown(
            '<div style="text-align:right; padding-top:1.3rem; font-size:1.3rem;">'
            f"📄 Working on <strong><code>{html.escape(selected_path.name)}</code></strong>"
            "</div>",
            unsafe_allow_html=True,
        )

    if st.session_state.get("_active_csv") != selected_path.name:
        st.session_state["_active_csv"] = selected_path.name
        st.session_state["row_idx"] = 0

    try:
        df, schema = _cached_load_csv(str(selected_path), selected_path.stat().st_mtime)
    except (ValueError, OSError, pd.errors.ParserError) as e:
        st.error(
            f"Couldn't read `{selected_path.name}`: {e}\n\n"
            "If more than one CSV is available, pick a different one above; "
            "otherwise check that this file matches the expected format."
        )
        return

    total_rows = len(df)
    if total_rows == 0:
        st.error(f"`{selected_path.name}` has no data rows to review.")
        return

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

    # --- Sidebar: what's actually in this file, at a glance ---
    st.sidebar.subheader("This file")
    label_counts = df[schema.label_column].value_counts()
    st.sidebar.markdown(
        "  \n".join(f"{label_display(schema, val)}: **{count}**" for val, count in label_counts.items())
    )
    if schema.flag_column:
        flag_col = df[schema.flag_column]
        flagged = int((flag_col.notna() & (flag_col != "ok")).sum())
        if flagged:
            st.sidebar.caption(f"⚠️ {flagged} row{'s' if flagged != 1 else ''} flagged by outlier scoring")

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

    # --- Top bar, two rows:
    #   Row 1: Show-filter (left) and row status (flush right), justify-
    #          between style, one line, no scrolling needed to reach it.
    #   Row 2: the confidence-outlier filter, narrow and left-aligned like
    #          the Show control above it — kept on its own row since it can
    #          grow taller (checkbox -> radio -> slider -> match count) and
    #          would otherwise squeeze/misalign the other two.
    # Previous/Next/Save/Jump-to-row live further down, right next to the
    # plot and label controls, since that's where your eyes and mouse
    # already are while reviewing a row. ---

    # The confidence-filter widgets render below (row 2), but the results
    # are needed above (row 1) for the status line — read prior state here;
    # widgets bound to the same keys further down just reflect it back.
    outlier_row_ids: set | None = None
    outlier_desc: str | None = None
    outlier_enabled = bool(schema.confidence_column) and st.session_state.get("outlier_filter_enabled", False)
    if outlier_enabled:
        pct_now = st.session_state.get("outlier_pct", 10)
        pop_now = st.session_state.get("outlier_population", 1)
        outlier_row_ids, _, _ = outlier_row_ids_for_percentile(df, schema, pop_now, pct_now)
        outlier_desc = f"bottom {pct_now}% ({label_display(schema, pop_now)})"

    mode_col, status_col = st.columns([1.3, 2.3])
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
    if outlier_row_ids is not None:
        filtered = [i for i in filtered if ids[i] in outlier_row_ids]
    prev_target = step(filtered, row_idx, -1)
    next_target = step(filtered, row_idx, 1)

    with status_col:
        # Built as real HTML throughout (not Streamlit markdown syntax like
        # **bold**/:green[...]) — those extensions aren't applied inside a
        # raw HTML block, so mixing them in here would print the literal
        # "**"/"`"/":green[...]" characters instead of styling anything.
        badge_color = "#2e7d32" if is_reviewed else "#1565c0"
        badge_text = "Reviewed" if is_reviewed else "Not yet reviewed"
        status_html = (
            f"<strong>{row_idx + 1} / {total_rows}</strong> &middot; sample "
            f"<code>{html.escape(str(row_id))}</code> &middot; "
            f"<span style='color:{badge_color}'>{badge_text}</span>"
        )
        if len(filtered) != total_rows:
            filter_parts = [p for p in (nav_mode.lower() if nav_mode != "All" else None, outlier_desc) if p]
            filter_label = html.escape(" + ".join(filter_parts) if filter_parts else "filter")
            if row_idx in filtered:
                match_text = f"{filter_label}: {filtered.index(row_idx) + 1} / {len(filtered)}"
            else:
                # Active filter, but the row on screen isn't one of the matches
                # (e.g. it was just turned on) — say so explicitly instead of
                # silently showing nothing, which reads as "filter did nothing".
                plural = "es" if len(filtered) != 1 else ""
                match_text = f"{filter_label}: {len(filtered)} match{plural} (current row not included)"
            status_html += f"<br><span style='color:#888'>{match_text}</span>"
        st.markdown(f'<div style="text-align:right">{status_html}</div>', unsafe_allow_html=True)

    if not filtered:
        st.info("No rows match the current filter.")

    # Row 2: confidence-outlier filter, narrow and left-aligned like "Show"
    # above it, with empty space to its right rather than stretching wide.
    if schema.confidence_column:
        conf_col, _ = st.columns([1.3, 2.3])
        with conf_col:
            popover_label = "🎯 Confidence filter"
            if outlier_enabled:
                popover_label += f" · {outlier_desc}"
            with st.popover(popover_label):
                enabled = st.checkbox("Filter by confidence outliers", key="outlier_filter_enabled")
                if enabled:
                    population_choice = st.radio(
                        "Among",
                        options=sorted(label_options(schema, df), reverse=True),  # wheat (1) first
                        format_func=lambda v: label_display(schema, v),
                        key="outlier_population",
                    )
                    pct = st.slider(
                        "Bottom percentile by confidence",
                        min_value=1,
                        max_value=50,
                        value=10,
                        key="outlier_pct",
                    )
                    _, matched_count, population_count = outlier_row_ids_for_percentile(
                        df, schema, population_choice, pct
                    )
                    st.caption(f"{matched_count} of {population_count} rows match")

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
        if reference_df is not None:
            n_samples = int(reference_df["n_samples"].iloc[0])
            # A reference built from a handful of samples is much noisier
            # than one from thousands — worth knowing before trusting the band.
            confidence_note = " (small sample — treat with caution)" if n_samples < 1000 else ""
            st.caption(f"Reference: {region_value} {year_value} · {n_samples} wheat samples{confidence_note}")
        elif region_value is not None and year_value is not None:
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

        if schema.confidence_column and pd.notna(row[schema.confidence_column]):
            st.markdown(f"Label confidence: {confidence_badge(row[schema.confidence_column])}")
        if schema.flag_column and pd.notna(row[schema.flag_column]):
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
        inject_label_background(schema, chosen_label)
        comment = st.text_area(
            "Comment (optional)",
            value=default_comment,
            key=f"comment_{row_id}",
            height=70,
        )

        if chosen_label != default_label or comment != default_comment:
            # The label/comment widgets remember whatever was last typed for
            # this row even after navigating away without saving (Streamlit
            # keeps widget state by key) - without this, that looks identical
            # to a properly saved edit until you notice the badge above still
            # says "Not yet reviewed".
            st.caption("🖊️ Unsaved change — click Save to keep it.")

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
