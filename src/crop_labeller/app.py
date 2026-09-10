"""Streamlit app for reviewing/correcting crop labels from NDVI CSVs."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from crop_labeller.data import CsvSchema, label_display, label_options, list_csv_files, load_csv
from crop_labeller.state import ReviewState, write_outputs

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data"
OUTPUT_DIR = PROJECT_ROOT / "output"

st.set_page_config(page_title="Crop Labeller", page_icon="🌾", layout="wide")


@st.cache_data(show_spinner=False)
def _cached_load_csv(path_str: str, mtime: float) -> tuple[pd.DataFrame, CsvSchema]:
    return load_csv(Path(path_str))


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


def render_metadata_panel(row: pd.Series, schema: CsvSchema) -> None:
    skip = set(schema.ndvi_columns) | {schema.id_column, schema.label_column}
    if schema.label_text_column:
        skip.add(schema.label_text_column)
    context_cols = [c for c in schema.original_columns if c not in skip]
    if not context_cols:
        return
    values = [format_value(row[c]) for c in context_cols]
    context_df = pd.DataFrame({"field": context_cols, "value": values})
    st.dataframe(context_df, hide_index=True, width="stretch", height=min(38 * len(context_cols) + 38, 320))


def render_ndvi_plot(row: pd.Series, schema: CsvSchema, row_id: object) -> None:
    x = list(range(1, len(schema.ndvi_columns) + 1))
    y = [row[c] for c in schema.ndvi_columns]
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=x,
            y=y,
            mode="lines+markers",
            line=dict(color="#2e7d32", width=3),
            marker=dict(size=7),
            hovertemplate="Time step %{x}<br>NDVI %{y:.3f}<extra></extra>",
        )
    )
    fig.update_layout(
        title=f"NDVI time series — sample {row_id}",
        xaxis_title="NDVI time steps",
        yaxis_title="NDVI values",
        xaxis=dict(tickmode="linear", tick0=x[0], dtick=1, range=[x[0] - 0.3, x[-1] + 0.3]),
        yaxis_range=[-0.05, 1.0],
        template="plotly_white",
        height=360,
        margin=dict(l=40, r=20, t=50, b=40),
    )
    st.plotly_chart(fig, width="stretch")


def inject_css() -> None:
    st.markdown(
        """
        <style>
        html, body, [data-testid="stAppViewContainer"] { font-size: 17px; }

        [data-testid="stMainBlockContainer"], .block-container {
            max-width: 1200px;
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

    # --- Compact top bar: filter, row status, jump-to-row — one line, no
    # scrolling needed to reach it. Previous/Next/Save live further down,
    # right next to the plot and label controls, since that's where your
    # eyes and mouse already are while reviewing a row. ---
    mode_col, status_col, jump_col = st.columns([1.4, 2.2, 1])
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
    with jump_col:
        st.caption("Jump to row")
        st.number_input(
            "Jump to row",
            min_value=1,
            max_value=total_rows,
            key="jump_input",
            on_change=jump_callback,
            label_visibility="collapsed",
        )

    if not filtered:
        st.info("No rows match the current filter.")

    # --- Plot + review controls, side by side, so both fit on screen at once. ---
    plot_col, review_col = st.columns([2, 1])
    with plot_col:
        render_ndvi_plot(row, schema, row_id)
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

        prev_btn_col, save_col, next_btn_col = st.columns([1, 1.5, 1])
        with prev_btn_col:
            if st.button("⬅ Prev", disabled=prev_target is None, width="stretch"):
                go_to(prev_target)
                st.rerun()
        with next_btn_col:
            if st.button("Next ➡", disabled=next_target is None, width="stretch"):
                go_to(next_target)
                st.rerun()
        with save_col:
            if st.button("💾 Save", type="primary", width="stretch"):
                state.set_review(row_id, original_label, chosen_label, comment)
                state.save()
                write_outputs(df, schema, state, OUTPUT_DIR, selected_path)
                st.toast(f"Saved sample {row_id}", icon="✅")
                if next_target is not None:
                    go_to(next_target)
                st.rerun()


if __name__ == "__main__":
    main()
