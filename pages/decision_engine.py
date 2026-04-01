"""Decision engine page with scenario-based prioritization."""

from __future__ import annotations

from pathlib import Path
import sys

import pandas as pd
import plotly.express as px
import streamlit as st

sys.path.insert(0, str(Path(__file__).parents[1]))

from src.components.ui import explain_chart, hero, insight_cards, page_story, recommendation_card, section_intro
from src.data.decision import (
    ScoreWeights,
    build_decision_dataset,
    build_state_decision_rollup,
    methodology_table,
    score_profile_catalog,
)
from src.data.loader import load_bus, load_congressional, load_counties, load_district, load_utilities
from src.data.processor import clean_bus, clean_district
from src.utils.helpers import fmt_number, fmt_pct


@st.cache_data(show_spinner=False)
def _load_base_frames() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    return (
        clean_district(load_district()),
        clean_bus(load_bus()),
        load_utilities(),
        load_counties(),
        load_congressional(),
    )


@st.cache_data(show_spinner=False)
def _build_decision_data(profile_name: str) -> tuple[pd.DataFrame, pd.DataFrame, ScoreWeights]:
    district_df, bus_df, utilities_df, counties_df, congress_df = _load_base_frames()
    weights = score_profile_catalog()[profile_name]
    decision_df = build_decision_dataset(
        district_df=district_df,
        bus_df=bus_df,
        utilities_df=utilities_df,
        counties_df=counties_df,
        congress_df=congress_df,
        weights=weights,
    )
    state_df = build_state_decision_rollup(decision_df)
    return decision_df, state_df, weights


SEGMENT_COLORS = {
    "Act now": "#b91c1c",
    "High need, harder execution": "#7c3aed",
    "Fast-track candidate": "#0f766e",
    "Monitor": "#94a3b8",
}


PROFILE_COPY = {
    "Balanced": "Best default portfolio profile. Keeps the narrative balanced across exposure, transition gap, fleet leverage, and implementation complexity.",
    "Equity first": "Pushes the model toward environmental and socioeconomic need. Useful when the decision lens is public-health fairness before delivery convenience.",
    "Deployment first": "Gives more weight to transition gap and fleet leverage. Best when the objective is rapid visible progress rather than pure vulnerability targeting.",
    "Scale first": "Privileges large fleets and rollout leverage. Useful for a statewide program trying to move more buses quickly, even if smaller districts drop in rank.",
}


def render() -> None:
    hero(
        "Decision engine",
        "This is the page where the project stops being a dashboard and becomes a decision system. The objective is not just to describe adoption, but to show how prioritization changes under explicit scoring assumptions.",
    )

    available_profiles = list(score_profile_catalog().keys())
    profile_name = st.selectbox(
        "Scoring profile",
        available_profiles,
        index=0,
        help="Switch weighting assumptions to see how the shortlist changes without hiding the model logic.",
    )
    decision_df, state_df, weights = _build_decision_data(profile_name)

    page_story(
        kpi_title="Districts simultaneously ranking high on structural priority and execution readiness",
        kpi_value=fmt_pct((decision_df["decision_segment"] == "Act now").mean() * 100),
        observation=(
            "The strongest shift in this project is methodological: the workbook is converted into a triage layer with named districts, state pressure signals, and explicit trade-offs."
        ),
        implication=(
            "Instead of pretending there is one universally correct ranking, the page exposes the weighting logic and lets the shortlist move when the decision objective changes."
        ),
    )

    insight_cards(
        [
            (
                "Active profile",
                profile_name,
                PROFILE_COPY[profile_name],
            ),
            (
                "Median priority",
                f"{decision_df['priority_score'].median():.1f}",
                "Composite urgency score built from need, transition gap, scale, and implementation complexity.",
            ),
            (
                "Act-now districts",
                fmt_number((decision_df["decision_segment"] == "Act now").sum()),
                "Districts where urgency and relative execution viability overlap under the current profile.",
            ),
        ]
    )

    st.subheader("Scoring logic")
    col_left, col_right = st.columns([1.0, 1.25])
    with col_left:
        st.dataframe(methodology_table(weights), width='stretch', hide_index=True)
        recommendation_card(
            "Why this is stronger",
            "The model is adjustable without becoming opaque",
            "That is the right compromise for portfolio work. It keeps the system inspectable, but still shows that rankings depend on policy intent rather than on one frozen scoring recipe.",
        )
    with col_right:
        component_means = pd.DataFrame(
            {
                "component": ["Need", "Transition gap", "Scale", "Complexity"],
                "value": [
                    decision_df["need_component"].mean() * 100,
                    decision_df["transition_gap_component"].mean() * 100,
                    decision_df["scale_component"].mean() * 100,
                    decision_df["complexity_component"].mean() * 100,
                ],
            }
        )
        fig_comp = px.bar(
            component_means,
            x="component",
            y="value",
            color="value",
            color_continuous_scale="Tealgrn",
            template="plotly_white",
            labels={"component": "Score block", "value": "Average normalized contribution"},
        )
        fig_comp.update_layout(height=340, showlegend=False, coloraxis_showscale=False, margin=dict(t=20, b=0))
        st.plotly_chart(fig_comp, width='stretch')
        explain_chart(
            "The bar heights are not there to prove one block is universally dominant. They show how the current profile distributes analytical attention across need, transition friction, fleet leverage, and coordination burden.",
            "That matters because a ranking should reflect strategy, not just mathematics. Making the weighting visible turns a static score into a defensible decision instrument.",
            preset="signal",
        )

    st.divider()
    section_intro(
        "Use the three views below in order: first identify where structural pressure is highest at state level, then review the district shortlist, then examine the urgency-versus-readiness matrix to understand what kind of intervention each segment actually requires."
    )

    tab_state, tab_district, tab_matrix = st.tabs(["State triage", "District shortlist", "Priority vs readiness"])

    with tab_state:
        st.subheader("Where strategic pressure is highest")
        fig_state = px.bar(
            state_df.head(15),
            x="state",
            y="avg_priority",
            color="act_now_share",
            color_continuous_scale="YlOrRd",
            template="plotly_white",
            hover_data={
                "districts": True,
                "adoption_pct": ":.2f",
                "avg_quick_win": ":.2f",
                "critical_share": ":.2f",
                "act_now_share": ":.2f",
            },
            labels={"avg_priority": "Average priority score", "act_now_share": "Act-now share (%)", "state": "State"},
        )
        fig_state.update_layout(height=410, xaxis_tickangle=-45, margin=dict(t=20, b=0))
        st.plotly_chart(fig_state, width='stretch')
        top_state = state_df.iloc[0]
        explain_chart(
            f"{top_state['state'].title()} rises to the top under the {profile_name.lower()} profile because its district mix combines strong average urgency with a meaningful concentration of high-action candidates.",
            "This is more useful than a simple adoption league table. It highlights where unmet transition pressure is structurally stronger, not just where there are many buses in absolute terms.",
            preset="benchmark",
        )
        st.dataframe(
            state_df[["state", "avg_priority", "avg_quick_win", "adoption_pct", "critical_share", "act_now_share", "districts"]]
            .rename(columns={
                "state": "State",
                "avg_priority": "Avg priority",
                "avg_quick_win": "Avg quick-win",
                "adoption_pct": "Adoption (%)",
                "critical_share": "Critical districts (%)",
                "act_now_share": "Act-now share (%)",
                "districts": "Districts",
            })
            .round(2),
            width='stretch',
            hide_index=True,
        )

    with tab_district:
        st.subheader("Districts to move first")
        col1, col2, col3 = st.columns([1, 1, 1.2])
        with col1:
            selected_state = st.selectbox("State filter", ["All states", *sorted(decision_df["state"].dropna().unique())], index=0)
        with col2:
            selected_segment = st.selectbox("Segment", ["All segments", *SEGMENT_COLORS.keys()], index=0)
        with col3:
            sort_mode = st.selectbox(
                "Ranking lens",
                ["Priority score", "Quick-win score", "Fleet size", "PM2.5", "Low-income share"],
                index=0,
            )

        filtered = decision_df.copy()
        if selected_state != "All states":
            filtered = filtered[filtered["state"] == selected_state]
        if selected_segment != "All segments":
            filtered = filtered[filtered["decision_segment"] == selected_segment]

        sort_col = {
            "Priority score": "priority_score",
            "Quick-win score": "quick_win_score",
            "Fleet size": "total_buses",
            "PM2.5": "pm25",
            "Low-income share": "pct_low_income",
        }[sort_mode]

        shortlist = filtered.sort_values(sort_col, ascending=False).head(25).copy()
        fig_short = px.bar(
            shortlist.sort_values(sort_col),
            x=sort_col,
            y="district",
            orientation="h",
            color="decision_segment",
            color_discrete_map=SEGMENT_COLORS,
            hover_data={
                "state": True,
                "city": True,
                "priority_score": ":.2f",
                "quick_win_score": ":.2f",
                "pm25": ":.2f",
                "pct_low_income": ":.2f",
            },
            template="plotly_white",
            labels={sort_col: sort_mode, "district": "District"},
        )
        fig_short.update_layout(height=max(520, 26 * len(shortlist)), margin=dict(t=20, b=0), legend_title_text="Segment")
        st.plotly_chart(fig_short, width='stretch')
        explain_chart(
            "This shortlist is the practical output of the whole project. It turns a national workbook into a named set of districts that can be defended in terms of urgency, equity exposure, and implementation burden.",
            "That is the step where descriptive BI becomes decision support. A stakeholder can now debate action sequencing, not just react to a chart.",
            preset="focus",
        )
        export_cols = [
            "district", "state", "city", "priority_score", "quick_win_score", "decision_segment", "priority_tier", "total_buses",
            "committed_esb", "esb_adoption_rate", "pm25", "pct_low_income", "utility_count", "county_count", "congressional_count",
        ]
        st.download_button(
            "Download shortlist as CSV",
            shortlist[export_cols].to_csv(index=False).encode("utf-8"),
            file_name=f"district_shortlist_{profile_name.lower().replace(' ', '_')}.csv",
            mime="text/csv",
        )
        st.dataframe(
            shortlist[export_cols]
            .rename(columns={
                "district": "District",
                "state": "State",
                "city": "City",
                "priority_score": "Priority",
                "quick_win_score": "Quick-win",
                "decision_segment": "Segment",
                "priority_tier": "Tier",
                "total_buses": "Fleet size",
                "committed_esb": "Committed ESBs",
                "esb_adoption_rate": "Adoption (%)",
                "pm25": "PM2.5",
                "pct_low_income": "Low-income (%)",
                "utility_count": "Utilities",
                "county_count": "Counties",
                "congressional_count": "Congressional districts",
            })
            .round(2),
            width='stretch',
            hide_index=True,
        )

    with tab_matrix:
        st.subheader("Urgency versus execution speed")
        matrix = decision_df.dropna(subset=["priority_score", "quick_win_score", "pm25", "total_buses"]).copy()
        fig_matrix = px.scatter(
            matrix,
            x="quick_win_score",
            y="priority_score",
            color="decision_segment",
            size="total_buses",
            hover_name="district",
            hover_data={
                "state": True,
                "city": True,
                "pm25": ":.2f",
                "esb_adoption_rate": ":.2f",
                "utility_count": True,
                "county_count": True,
            },
            color_discrete_map=SEGMENT_COLORS,
            template="plotly_white",
            labels={"quick_win_score": "Execution readiness / quick-win score", "priority_score": "Structural priority score"},
            opacity=0.62,
        )
        fig_matrix.add_vline(x=matrix["quick_win_score"].quantile(0.75), line_dash="dot", line_color="gray")
        fig_matrix.add_hline(y=matrix["priority_score"].quantile(0.75), line_dash="dot", line_color="gray")
        fig_matrix.update_layout(height=500, margin=dict(t=20, b=0), legend_title_text="Segment")
        st.plotly_chart(fig_matrix, width='stretch')
        explain_chart(
            "Top-right districts are the cleanest intervention candidates: high urgency and comparatively strong execution conditions. Top-left districts remain important, but the path will likely involve more coordination, more utilities, and more institutional friction.",
            "That distinction is operationally useful. It prevents the ranking from implying that every high-need district should be handled with the same deployment playbook.",
            preset="pattern",
        )

        hard_cases = (
            matrix[matrix["decision_segment"] == "High need, harder execution"]
            .sort_values(["priority_score", "complexity_component"], ascending=False)
            .head(15)
        )
        st.subheader("Hard cases worth funding, without pretending they are easy")
        st.dataframe(
            hard_cases[[
                "district", "state", "city", "priority_score", "quick_win_score", "utility_count", "county_count",
                "congressional_count", "adoption_gap", "pm25",
            ]]
            .rename(columns={
                "district": "District",
                "state": "State",
                "city": "City",
                "priority_score": "Priority",
                "quick_win_score": "Quick-win",
                "utility_count": "Utilities",
                "county_count": "Counties",
                "congressional_count": "Congressional districts",
                "adoption_gap": "Adoption gap",
                "pm25": "PM2.5",
            })
            .round(2),
            width='stretch',
            hide_index=True,
        )
        recommendation_card(
            "Portfolio implication",
            "The project is stronger because it preserves trade-offs",
            "A mature analytics product does not hide friction. It shows that some districts rank high precisely because they are urgent, even when delivery conditions imply a slower and more coordinated intervention path.",
        )
