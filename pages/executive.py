"""Executive briefing page."""

from __future__ import annotations

from pathlib import Path
import sys

import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st

sys.path.insert(0, str(Path(__file__).parents[1]))

from src.components.ui import (
    explain_chart,
    hero,
    insight_cards,
    page_story,
    recommendation_card,
    section_intro,
)
from src.data.loader import (
    load_bus,
    load_congressional,
    load_counties,
    load_district,
    load_state,
    load_utilities,
)
from src.data.processor import clean_bus, clean_district, clean_state
from src.utils.helpers import add_state_abbr, fmt_number, fmt_pct


def _utility_long_frame(df: pd.DataFrame) -> pd.DataFrame:
    util_cols = [c for c in df.columns if c.startswith("9a. Utility name")]
    id_cols = [c for c in ["1a. State", "1b. LEA name", "1c. LEA ID"] if c in df.columns]
    melted = df[id_cols + util_cols].melt(
        id_vars=id_cols,
        value_vars=util_cols,
        value_name="utility_name",
    )
    melted = melted.dropna(subset=["utility_name"]).copy()
    melted["utility_name"] = melted["utility_name"].astype(str).str.strip()
    melted = melted[melted["utility_name"] != ""]
    return melted


def render() -> None:
    hero(
        "Executive briefing",
        "A compact, recruiter-ready reading of the electric school bus market: scale, equity alignment, industrial concentration, and where deployment still looks structurally behind need.",
    )

    district_df = clean_district(load_district())
    bus_df = clean_bus(load_bus())
    state_df = clean_state(load_state())
    utilities_df = load_utilities()
    counties_df = load_counties()
    congress_df = load_congressional()

    total_buses = district_df["total_buses"].fillna(0).sum()
    total_esb = district_df["committed_esb"].fillna(0).sum()
    adoption = total_esb / total_buses * 100 if total_buses else np.nan

    gap_df = district_df.dropna(subset=["equity_score", "esb_adoption_rate"]).copy()
    eq_median = gap_df["equity_score"].median()
    adop_median = gap_df["esb_adoption_rate"].median()
    underserved = gap_df[
        (gap_df["equity_score"] >= eq_median)
        & (gap_df["esb_adoption_rate"] < adop_median)
    ].copy()

    state_rollup = (
        district_df.groupby("state")
        .agg(committed=("committed_esb", "sum"), total=("total_buses", "sum"), districts=("district", "count"))
        .reset_index()
    )
    state_rollup = state_rollup[state_rollup["total"] > 0].copy()
    state_rollup["adoption_pct"] = state_rollup["committed"] / state_rollup["total"] * 100
    state_rollup = add_state_abbr(state_rollup, "state")

    top_volume = state_rollup.sort_values("committed", ascending=False).iloc[0]
    top_intensity = state_rollup.sort_values("adoption_pct", ascending=False).iloc[0]

    util_long = _utility_long_frame(utilities_df)
    utility_count = util_long["utility_name"].nunique()
    utility_top10_share = util_long["utility_name"].value_counts(normalize=True).head(10).sum() * 100 if not util_long.empty else np.nan

    county_multi = counties_df["10c. Number of counties in LEA"].fillna(1)
    county_multi_share = (county_multi.gt(1).mean() * 100) if len(county_multi) else np.nan
    congress_multi = congress_df["11c. Number of congressional districts in LEA"].fillna(1)
    congress_multi_share = (congress_multi.gt(1).mean() * 100) if len(congress_multi) else np.nan

    fund_concentration = bus_df["funding_source"].value_counts(normalize=True).head(3).sum() * 100 if len(bus_df) else np.nan
    oem_concentration = bus_df["oem"].value_counts(normalize=True).head(5).sum() * 100 if len(bus_df) else np.nan

    page_story(
        kpi_title="Recorded national fleet already committed to electric buses",
        kpi_value=fmt_pct(adoption),
        observation=(
            f"The transition is visible but still early. {top_volume['state'].title()} leads in absolute volume "
            f"({fmt_number(top_volume['committed'])} committed buses), while {top_intensity['state'].title()} leads in fleet penetration "
            f"({top_intensity['adoption_pct']:.1f}%)."
        ),
        implication=(
            "This is not one story but three at once: scale leaders, penetration leaders, underserved districts, and underlying execution complexity. A strong dashboard should keep those lenses separate instead of collapsing them into one ranking."
        ),
    )

    insight_cards(
        [
            (
                "Scale",
                fmt_number(total_esb),
                "Committed ESBs recorded across district-level data. The market has moved beyond pilots, but national penetration remains low relative to the size of the legacy fleet."
            ),
            (
                "Misalignment",
                f"{(len(underserved) / len(gap_df) * 100):.1f}%",
                "Share of districts sitting in the high-need / low-adoption quadrant. This is the clearest signal that deployment is not yet fully aligned with vulnerability."
            ),
            (
                "Execution complexity",
                f"{county_multi_share:.1f}%",
                "Share of county records associated with multi-county LEAs. Electrification is not only a vehicle problem; governance and service geography add operational complexity."
            ),
        ]
    )

    st.subheader("What stands out first")
    col1, col2, col3 = st.columns(3)
    with col1:
        recommendation_card(
            "Insight 01",
            "The market is still policy-shaped, not mature",
            f"Top-three funding channels account for about {fund_concentration:.1f}% of recorded buses. That means growth is still strongly tied to grant architecture and public program continuity."
        )
    with col2:
        recommendation_card(
            "Insight 02",
            "Industrial depth remains narrow",
            f"Top-five OEMs represent roughly {oem_concentration:.1f}% of bus records. Early concentration is normal, but it also means scale-up remains exposed to a limited supplier base."
        )
    with col3:
        recommendation_card(
            "Insight 03",
            "Infrastructure coordination is fragmented",
            f"The utilities sheet references {fmt_number(utility_count)} distinct utility names, yet the top ten names cover only about {utility_top10_share:.1f}% of utility mentions. Deployment coordination is geographically fragmented rather than controlled by a small national set of providers."
        )

    st.divider()
    section_intro(
        "The next visuals are not there to repeat the KPI cards. They show where the transition is concentrated, where vulnerability and adoption diverge, and where operational complexity is likely to slow rollout."
    )

    col_l, col_r = st.columns([1.15, 0.85])
    with col_l:
        st.subheader("Where the transition is materially visible")
        fig_map = px.choropleth(
            state_rollup,
            locations="state_abbr",
            locationmode="USA-states",
            color="adoption_pct",
            color_continuous_scale="YlGn",
            scope="usa",
            hover_name="state",
            hover_data={"committed": ":,", "total": ":,", "adoption_pct": ":.2f"},
            labels={"adoption_pct": "Adoption (%)"},
            template="plotly_white",
        )
        fig_map.update_layout(height=430, margin=dict(l=0, r=0, t=20, b=0), coloraxis_colorbar=dict(title="Adoption %", len=0.7))
        st.plotly_chart(fig_map, width='stretch')
        explain_chart(
            "The map is intentionally normalized by fleet size. It distinguishes states with large procurement volume from states where electrification is already becoming material relative to the installed fleet.",
            "That distinction is crucial in portfolio work. Without normalization, large states dominate the narrative even when their transition depth remains modest.",
            preset="benchmark",
        )

    with col_r:
        st.subheader("Need versus deployment")
        quad = pd.DataFrame(
            {
                "segment": [
                    "High need / low ESB",
                    "High need / has ESBs",
                    "Low need / has ESBs",
                    "Low need / low ESB",
                ],
                "count": [
                    int(((gap_df["equity_score"] >= eq_median) & (gap_df["esb_adoption_rate"] < adop_median)).sum()),
                    int(((gap_df["equity_score"] >= eq_median) & (gap_df["esb_adoption_rate"] >= adop_median)).sum()),
                    int(((gap_df["equity_score"] < eq_median) & (gap_df["esb_adoption_rate"] >= adop_median)).sum()),
                    int(((gap_df["equity_score"] < eq_median) & (gap_df["esb_adoption_rate"] < adop_median)).sum()),
                ],
            }
        )
        color_map = {
            "High need / low ESB": "#dc2626",
            "High need / has ESBs": "#16a34a",
            "Low need / has ESBs": "#2563eb",
            "Low need / low ESB": "#cbd5e1",
        }
        fig_quad = px.pie(
            quad,
            values="count",
            names="segment",
            hole=0.48,
            color="segment",
            color_discrete_map=color_map,
            template="plotly_white",
        )
        fig_quad.update_traces(textinfo="percent+label")
        fig_quad.update_layout(height=430, margin=dict(t=20, b=0), showlegend=False)
        st.plotly_chart(fig_quad, width='stretch')
        explain_chart(
            "The red slice is the core targeting problem: districts where measured need is high but adoption still lags the national median.",
            "This compresses a complex dataset into a decision lens. It is the most actionable segmentation in the entire dashboard because it links vulnerability to rollout shortfall.",
            preset="focus",
        )

    st.subheader("System constraints behind deployment")
    c1, c2 = st.columns(2)
    with c1:
        oem = bus_df["oem"].value_counts().head(10).reset_index()
        oem.columns = ["OEM", "Buses"]
        fig_oem = px.bar(
            oem.sort_values("Buses"),
            x="Buses",
            y="OEM",
            orientation="h",
            color="Buses",
            color_continuous_scale="Blues",
            template="plotly_white",
        )
        fig_oem.update_layout(height=380, showlegend=False, coloraxis_showscale=False, margin=dict(t=20, b=0))
        st.plotly_chart(fig_oem, width='stretch')
        explain_chart(
            "The manufacturer distribution confirms that early deployment is not evenly spread across the industrial base.",
            "A concentrated supplier landscape can accelerate a young market, but it also raises the strategic risk that scaling timelines remain tied to a handful of firms.",
            preset="risk",
        )

    with c2:
        top_rto = utilities_df["9k. RTO/ISO"].fillna("Not specified").value_counts().head(8).reset_index()
        top_rto.columns = ["RTO / ISO", "District rows"]
        fig_rto = px.bar(
            top_rto.sort_values("District rows"),
            x="District rows",
            y="RTO / ISO",
            orientation="h",
            color="District rows",
            color_continuous_scale="Tealgrn",
            template="plotly_white",
        )
        fig_rto.update_layout(height=380, showlegend=False, coloraxis_showscale=False, margin=dict(t=20, b=0))
        st.plotly_chart(fig_rto, width='stretch')
        explain_chart(
            "Utility and grid context is uneven across the country. The RTO / ISO split shows that electrification is unfolding across very different energy-system environments.",
            "That matters because vehicle deployment alone is not the full implementation story. Charging strategy, interconnection friction, and utility engagement vary by regional market structure.",
            preset="pattern",
        )

    st.subheader("Operational complexity hidden behind district labels")
    metric_cols = st.columns(4)
    metric_cols[0].metric("States in dataset", fmt_number(state_rollup["state"].nunique()))
    metric_cols[1].metric("Utility names referenced", fmt_number(utility_count))
    metric_cols[2].metric("Multi-county LEA share", fmt_pct(county_multi_share))
    metric_cols[3].metric("Multi-congressional LEA share", fmt_pct(congress_multi_share))

    complexity = pd.DataFrame(
        {
            "Layer": ["Multi-county LEAs", "Multi-congressional LEAs", "Utility top-10 share"],
            "Value": [county_multi_share, congress_multi_share, utility_top10_share],
        }
    )
    fig_complexity = px.bar(
        complexity,
        x="Layer",
        y="Value",
        color="Value",
        color_continuous_scale="Sunsetdark",
        labels={"Value": "Share (%)"},
        template="plotly_white",
    )
    fig_complexity.update_layout(height=320, showlegend=False, coloraxis_showscale=False, margin=dict(t=20, b=0))
    st.plotly_chart(fig_complexity, width='stretch')
    explain_chart(
        "This last view makes the workbook feel more real. District electrification often spans multiple counties, multiple congressional districts, and a fragmented utility environment.",
        "That is why rollout cannot be read as a simple procurement exercise. The dataset supports a richer interpretation: deployment quality depends on coordination capacity as much as on funding availability.",
        preset="reading",
    )
