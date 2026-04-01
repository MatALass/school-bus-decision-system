"""Methodology and caveats page for V6."""

from __future__ import annotations

from pathlib import Path
import sys

import pandas as pd
import plotly.express as px
import streamlit as st

sys.path.insert(0, str(Path(__file__).parents[1]))

from src.components.ui import explain_chart, hero, insight_cards, page_story, recommendation_card, section_intro
from src.data.decision import build_decision_dataset, methodology_table
from src.data.loader import load_bus, load_congressional, load_counties, load_district, load_utilities
from src.data.processor import clean_bus, clean_district


@st.cache_data(show_spinner=False)
def _build_frame() -> pd.DataFrame:
    district_df = clean_district(load_district())
    bus_df = clean_bus(load_bus())
    return build_decision_dataset(
        district_df=district_df,
        bus_df=bus_df,
        utilities_df=load_utilities(),
        counties_df=load_counties(),
        congress_df=load_congressional(),
    )


def render() -> None:
    hero(
        "Methodology and caveats",
        "V6 is stronger because it is explicit about how the scoring works, what it captures, and what it does not. That matters more in an interview than pretending a ranked output is objective truth.",
    )

    decision_df = _build_frame()
    adoption_missing = float(decision_df["esb_adoption_rate"].isna().mean() * 100)
    pm25_missing = float(decision_df["pm25"].isna().mean() * 100)
    utilities_missing = float((decision_df["utility_count"].fillna(0) == 0).mean() * 100)

    page_story(
        kpi_title="Median district priority score",
        kpi_value=f"{decision_df['priority_score'].median():.1f}",
        observation=(
            "The score is a prioritization aid, not a ground-truth label. It is designed to be inspectable and debatable, which is a strength in analytical work where the weighting itself is part of the reasoning."
        ),
        implication=(
            "The right way to read the output is comparative, not absolute: which districts consistently surface under transparent assumptions, and which only rise under a narrow lens."
        ),
    )

    insight_cards(
        [
            (
                "Transparency",
                "Weighted model",
                "Need, transition gap, scale, and complexity are visible components rather than hidden feature engineering."
            ),
            (
                "Trade-off",
                "Signal over precision",
                "The goal is triage quality and explainability, not the illusion of perfect causal attribution."
            ),
            (
                "Portfolio value",
                "Defendable logic",
                "This is stronger than a generic dashboard because the ranking can be challenged, adjusted, and exported."
            ),
        ]
    )

    col1, col2 = st.columns([1.05, 1.15])
    with col1:
        st.subheader("Score design")
        st.dataframe(methodology_table(), width='stretch', hide_index=True)
        recommendation_card(
            "Why this design",
            "A transparent weighted score is the correct level of ambition here",
            "A black-box model would look more advanced but would be weaker analytically because the dataset is not rich enough to justify predictive theater. This framing is more credible for BI, analytics engineering, and decision-support work.",
        )
    with col2:
        st.subheader("Distribution of priority scores")
        fig = px.histogram(
            decision_df,
            x="priority_score",
            nbins=30,
            template="plotly_white",
            labels={"priority_score": "Priority score"},
        )
        fig.update_layout(height=360, margin=dict(t=20, b=0))
        st.plotly_chart(fig, width='stretch')
        explain_chart(
            "The distribution is broad enough to differentiate districts meaningfully, which is what makes the prioritization usable. If everything clustered into the same narrow band, the score would have little operational value.",
            "What matters is not picking a magical threshold. It is identifying the upper tail that repeatedly surfaces as materially more urgent than the median district.",
            preset="pattern",
        )

    st.divider()
    section_intro(
        "A portfolio-grade project should also state its limitations directly. The points below are not weaknesses to hide. They are part of the analytical discipline of the project."
    )

    c1, c2 = st.columns(2)
    with c1:
        recommendation_card(
            "Caveat 01",
            "The score is relative to the workbook",
            "Districts are ranked against the available national dataset, not against a full operational ground truth. A district can score lower here and still deserve action under local policy constraints not captured in the workbook.",
        )
        recommendation_card(
            "Caveat 02",
            "Missingness is uneven across variables",
            f"Approximate missingness remains non-trivial on some fields: PM2.5 about {pm25_missing:.1f}%, adoption about {adoption_missing:.1f}%, and zero captured utility-count for about {utilities_missing:.1f}% of rows. That should shape how hard one pushes any downstream interpretation.",
        )
    with c2:
        recommendation_card(
            "Caveat 03",
            "Readiness is only partially observed",
            "Quick-win logic uses delivered, operating, charging, and complexity signals, but it is still a proxy. It does not directly observe utility upgrade lead times, procurement governance quality, or local political friction.",
        )
        recommendation_card(
            "Caveat 04",
            "The system is descriptive, not predictive",
            "The decision engine is best positioned as a prioritization layer for analysts and decision-makers. It should not be presented as a model forecasting exact deployment success without more granular operational data.",
        )

    st.subheader("What would make a V7 legitimately stronger")
    roadmap = pd.DataFrame(
        {
            "upgrade": [
                "Scenario-based weighting profiles",
                "State-level policy overlays",
                "District clustering / typology",
                "Export-ready briefing pack",
            ],
            "why_it_matters": [
                "Lets the user compare equity-first, execution-first, and scale-first strategies.",
                "Brings external policy reality into the prioritization logic.",
                "Moves from ranking to archetype-based intervention design.",
                "Turns the dashboard into a deliverable that mimics consulting workflow output.",
            ],
        }
    )
    st.dataframe(roadmap, width='stretch', hide_index=True)
