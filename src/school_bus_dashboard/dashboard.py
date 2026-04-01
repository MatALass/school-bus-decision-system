from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st

from school_bus_dashboard.charts import (
    make_benchmark_bar,
    make_distribution,
    make_kpi_figure,
    make_map,
    make_priority_ranking,
    make_priority_scatter,
)
from school_bus_dashboard.config import ASSETS_DIR
from school_bus_dashboard.data_loader import load_dataset
from school_bus_dashboard.insights import build_methodology_table, build_summary_lines
from school_bus_dashboard.metrics import compute_priority_scores, compute_state_benchmarks, summarize_scope
from school_bus_dashboard.preprocessing import clean_dataset, filter_state_city


@st.cache_data
def get_prepared_dataset() -> tuple[pd.DataFrame, str, str]:
    loaded = load_dataset()
    cleaned = clean_dataset(loaded.frame)
    scored = compute_priority_scores(cleaned)
    return scored, loaded.source_label, loaded.source_path


def _render_header(source_label: str, source_path: str) -> None:
    logo_path = ASSETS_DIR / "logo.svg"

    left, right = st.columns([0.12, 0.88])
    with left:
        if logo_path.exists():
            st.image(str(logo_path), width=96)
    with right:
        st.title("School Bus Electrification Intelligence Dashboard")
        st.caption(
            "Decision-support dashboard for comparing districts, surfacing equity and pollution risks, "
            "and prioritizing electric school bus deployment."
        )

    source_text = (
        f"Dataset source: `{source_label}` — `{source_path}`. "
        "If the original Excel file is placed in `data/raw/data.xlsx`, the app uses it automatically."
    )
    st.info(source_text)


def _render_sidebar(frame: pd.DataFrame) -> tuple[str, str]:
    st.sidebar.header("Filters")
    states = sorted(frame["state"].dropna().unique().tolist())
    state = st.sidebar.selectbox("State", states, index=0)

    state_cities = sorted(frame.loc[frame["state"] == state, "city"].dropna().unique().tolist())
    city = st.sidebar.selectbox("City scope", ["All cities", *state_cities], index=0)

    st.sidebar.markdown("---")
    st.sidebar.caption("The dashboard compares the selected scope against the full state benchmark.")
    return state, city


def _render_overview(state_df: pd.DataFrame, scope_df: pd.DataFrame, scope_label: str, benchmark_label: str) -> None:
    scope_metrics = summarize_scope(scope_df)
    benchmark_metrics = summarize_scope(state_df)

    st.plotly_chart(make_kpi_figure(scope_metrics), use_container_width=True)
    st.plotly_chart(
        make_benchmark_bar(scope_metrics, benchmark_metrics, scope_label, benchmark_label),
        use_container_width=True,
    )

    lines = build_summary_lines(scope_label, scope_metrics, benchmark_metrics)
    for line in lines:
        st.markdown(f"- {line}")


def _render_prioritization(state_df: pd.DataFrame, city: str) -> None:
    st.subheader("Priority map")
    st.plotly_chart(make_map(state_df), use_container_width=True)

    st.subheader("Priority ranking")
    st.plotly_chart(make_priority_ranking(state_df), use_container_width=True)

    columns = [
        "district",
        "city",
        "total_buses",
        "committed_esb",
        "esb_adoption_rate",
        "pm25",
        "free_lunch_pct",
        "median_income",
        "priority_score",
    ]
    st.dataframe(
        state_df[columns].head(25).reset_index(drop=True),
        use_container_width=True,
        hide_index=True,
    )

    st.subheader("Pollution vs adoption")
    st.plotly_chart(make_priority_scatter(state_df, city if city != "All cities" else None), use_container_width=True)


def _render_explorer(state_df: pd.DataFrame) -> None:
    st.subheader("Adoption rate distribution")
    st.plotly_chart(make_distribution(state_df), use_container_width=True)

    st.subheader("Detailed district table")
    st.dataframe(state_df.reset_index(drop=True), use_container_width=True, hide_index=True)


def _render_methodology() -> None:
    st.subheader("Prioritization logic")
    st.dataframe(build_methodology_table(), use_container_width=True, hide_index=True)

    st.markdown(
        """
        **Notes**
        - Higher PM2.5 and higher free/reduced lunch share increase urgency.
        - Lower ESB adoption increases the adoption gap score.
        - Lower income increases the income need score.
        - The current weighting is a defendable default, not an objective truth. It should be adjusted if the policy goal changes.
        """
    )


def main() -> None:
    st.set_page_config(page_title="School Bus Electrification Dashboard", layout="wide")

    frame, source_label, source_path = get_prepared_dataset()
    _render_header(source_label, source_path)

    state, city = _render_sidebar(frame)
    state_df = frame[frame["state"] == state].copy()
    scope_df = filter_state_city(frame, state, city)

    scope_label = f"{city}, {state}" if city != "All cities" else f"All cities in {state}"
    benchmark_label = f"{state} benchmark"

    overview_tab, prioritization_tab, explorer_tab, methodology_tab = st.tabs(
        ["Overview", "Prioritization", "Explorer", "Methodology"]
    )

    with overview_tab:
        _render_overview(state_df, scope_df, scope_label, benchmark_label)

    with prioritization_tab:
        _render_prioritization(state_df, city)

    with explorer_tab:
        _render_explorer(state_df)

    with methodology_tab:
        _render_methodology()
