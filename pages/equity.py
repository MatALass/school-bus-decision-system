"""Equity and environment page."""

from pathlib import Path
import sys

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

sys.path.insert(0, str(Path(__file__).parents[1]))

from src.components.charts import equity_heatmap_state, scatter_equity_adoption
from src.components.ui import explain_chart, page_story, section_intro
from src.data.loader import load_district
from src.data.processor import clean_district
from src.utils.helpers import fmt_pct


def render() -> None:
    st.header("Equity and environment")
    section_intro(
        "This page tests whether the ESB rollout is aligned with need. The objective is not to prove causality, but to check whether cleaner buses are reaching districts that face higher pollution, lower income, and greater social vulnerability."
    )

    df = clean_district(load_district())

    with st.sidebar:
        st.subheader("Equity filters")
        regions = sorted(df["census_region"].dropna().unique())
        selected_regions = st.multiselect("Census region", regions, default=regions)
        locale_types = sorted(df["locale_type"].dropna().unique())
        selected_locales = st.multiselect("Locale type", locale_types, default=locale_types)
        min_buses = st.slider("Minimum total buses", 0, int(df["total_buses"].fillna(0).max()), 1)

    filt = df.copy()
    if selected_regions:
        filt = filt[filt["census_region"].isin(selected_regions)]
    if selected_locales:
        filt = filt[filt["locale_type"].isin(selected_locales)]
    filt = filt[filt["total_buses"].fillna(0) >= min_buses]

    corr_income = filt[["median_income", "esb_adoption_rate"]].dropna().corr().iloc[0, 1]
    corr_pm25 = filt[["pm25", "esb_adoption_rate"]].dropna().corr().iloc[0, 1]
    top_q = filt["equity_score"].quantile(0.75)
    bottom_q = filt["equity_score"].quantile(0.25)
    top_need = filt[filt["equity_score"] >= top_q]["esb_adoption_rate"].mean()
    low_need = filt[filt["equity_score"] <= bottom_q]["esb_adoption_rate"].mean()
    adoption_gap = top_need - low_need

    page_story(
        kpi_title="Adoption gap between highest-need and lowest-need districts",
        kpi_value=fmt_pct(adoption_gap, 2),
        observation=(
            f"High-need districts average {top_need:.2f}% ESB adoption versus {low_need:.2f}% in the lowest-need quartile. "
            f"Income correlation is {corr_income:.3f}; pollution correlation is {corr_pm25:.3f}."
        ),
        implication=(
            "The important point is not just direction but strength. Weak correlations mean the rollout is only loosely aligned with vulnerability, even when the sign looks favorable on paper."
        ),
    )

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Districts in scope", f"{len(filt):,}")
    c2.metric("Average equity score", f"{filt['equity_score'].mean():.1f}/100")
    c3.metric("Income ↔ adoption", f"{corr_income:.3f}")
    c4.metric("PM2.5 ↔ adoption", f"{corr_pm25:.3f}")

    st.subheader("State-level equity profile")
    st.plotly_chart(equity_heatmap_state(filt), width='stretch')
    explain_chart(
        "This heatmap compares states across the main need dimensions used in the dashboard: pollution exposure, racialized concentration, low-income share, and lunch-based disadvantage.",
        "It is useful because deployment should be read against context. A state with modest ESB volume may still deserve more attention if its vulnerability profile is systematically higher.",
        preset="benchmark",
    )

    st.subheader("Income and adoption")
    plot_df = filt.dropna(subset=["median_income", "esb_adoption_rate", "pm25"]).copy()
    fig = px.scatter(
        plot_df,
        x="median_income",
        y="esb_adoption_rate",
        color="pm25",
        opacity=0.55,
        color_continuous_scale="RdYlGn_r",
        hover_name="district",
        hover_data={"state": True, "city": True, "median_income": ":,.0f", "esb_adoption_rate": ":.2f", "pm25": ":.2f"},
        labels={
            "median_income": "Median household income ($)",
            "esb_adoption_rate": "ESB adoption rate (%)",
            "pm25": "PM2.5 (µg/m³)",
        },
        template="plotly_white",
    )
    valid = plot_df[["median_income", "esb_adoption_rate"]].dropna()
    if len(valid) > 10:
        z = np.polyfit(valid["median_income"], valid["esb_adoption_rate"], 1)
        p = np.poly1d(z)
        x_range = np.linspace(valid["median_income"].min(), valid["median_income"].max(), 100)
        fig.add_trace(
            go.Scatter(
                x=x_range,
                y=p(x_range),
                mode="lines",
                line=dict(color="black", dash="dash", width=1.5),
                name="Trend",
            )
        )
    fig.update_layout(height=440, margin=dict(t=20, b=0))
    st.plotly_chart(fig, width='stretch')
    explain_chart(
        "The cloud is broad and the trend line is shallow. In this filtered view, richer districts do not massively dominate adoption, but the relationship is not strongly pro-equity either.",
        "This is exactly the kind of nuanced result worth surfacing in a portfolio project: the rollout is neither clearly income-progressive nor clearly income-captured. It looks mixed and inconsistent.",
        preset="signal",
    )

    st.subheader("Adoption by income quartile")
    df_q = filt.dropna(subset=["median_income", "esb_adoption_rate"]).copy()
    df_q["income_quartile"] = pd.qcut(df_q["median_income"], q=4, labels=["Q1 lowest", "Q2", "Q3", "Q4 highest"])
    q_agg = (
        df_q.groupby("income_quartile", observed=True)
        .agg(avg_adoption=("esb_adoption_rate", "mean"), n_districts=("district", "count"), avg_pm25=("pm25", "mean"))
        .reset_index()
    )
    fig_q = px.bar(
        q_agg,
        x="income_quartile",
        y="avg_adoption",
        color="avg_pm25",
        color_continuous_scale="RdYlGn_r",
        labels={"income_quartile": "Income quartile", "avg_adoption": "Average ESB adoption (%)", "avg_pm25": "Average PM2.5"},
        text=q_agg["avg_adoption"].round(2).astype(str) + "%",
        template="plotly_white",
    )
    fig_q.update_traces(textposition="outside")
    fig_q.update_layout(height=380, margin=dict(t=20, b=0))
    st.plotly_chart(fig_q, width='stretch')
    explain_chart(
        "Quartiles make the distribution easier to read than the raw scatter. They show whether adoption changes meaningfully when moving from lower-income to higher-income districts, while the bar color keeps the pollution burden visible.",
        "This is the cleaner decision view. It tells you whether the rollout pattern is structurally tilted, not just whether a few extreme districts distort the scatterplot.",
        preset="reading",
    )

    st.subheader("Air pollution versus adoption")
    fig_pm = scatter_equity_adoption(
        filt,
        "pm25",
        "esb_adoption_rate",
        "pct_nonwhite_hispanic",
        xlab="PM2.5 concentration (µg/m³)",
        ylab="ESB adoption rate (%)",
    )
    st.plotly_chart(fig_pm, width='stretch')
    explain_chart(
        "The right side of the chart represents districts with heavier fine-particle pollution exposure. If targeting were strongly environmental, more of those districts would cluster toward the top of the chart.",
        "The relationship is weak. That suggests the environmental logic for ESBs is present rhetorically, but only partially visible in the realized deployment pattern.",
        preset="focus",
    )

    st.subheader("Demographic gradients")
    col_l, col_r = st.columns(2)
    with col_l:
        df_race = filt.dropna(subset=["pct_nonwhite_hispanic", "esb_adoption_rate"]).copy()
        df_race["race_quartile"] = pd.qcut(
            df_race["pct_nonwhite_hispanic"],
            q=4,
            labels=["Q1 least diverse", "Q2", "Q3", "Q4 most diverse"],
        )
        race_agg = df_race.groupby("race_quartile", observed=True)["esb_adoption_rate"].mean().reset_index()
        fig_race = px.bar(
            race_agg,
            x="race_quartile",
            y="esb_adoption_rate",
            color="esb_adoption_rate",
            color_continuous_scale="Blues",
            labels={"race_quartile": "Demographic quartile", "esb_adoption_rate": "Average ESB adoption (%)"},
            template="plotly_white",
        )
        fig_race.update_layout(height=320, showlegend=False, coloraxis_showscale=False, margin=dict(t=20, b=0))
        st.plotly_chart(fig_race, width='stretch')
        explain_chart(
            "This view compresses district-level demographic diversity into four comparable groups and asks whether adoption rises with diversity instead of falling behind it.",
            "It is a more defensible equity lens than anecdotal case studies because it tests the structure of the distribution, not a few selected examples.",
            preset="pattern",
        )

    with col_r:
        df_lunch = filt.dropna(subset=["free_lunch_pct", "esb_adoption_rate"]).copy()
        df_lunch["lunch_quartile"] = pd.qcut(
            df_lunch["free_lunch_pct"],
            q=4,
            labels=["Q1 least poor", "Q2", "Q3", "Q4 most poor"],
        )
        lunch_agg = df_lunch.groupby("lunch_quartile", observed=True)["esb_adoption_rate"].mean().reset_index()
        fig_lunch = px.bar(
            lunch_agg,
            x="lunch_quartile",
            y="esb_adoption_rate",
            color="esb_adoption_rate",
            color_continuous_scale="Oranges",
            labels={"lunch_quartile": "Poverty quartile", "esb_adoption_rate": "Average ESB adoption (%)"},
            template="plotly_white",
        )
        fig_lunch.update_layout(height=320, showlegend=False, coloraxis_showscale=False, margin=dict(t=20, b=0))
        st.plotly_chart(fig_lunch, width='stretch')
        explain_chart(
            "Free and reduced lunch is used here as a poverty proxy. The question is whether adoption is reaching student populations with greater socioeconomic exposure.",
            "That matters because the policy case for ESBs is not only emissions reduction. It is also about where public investment improves day-to-day school transport conditions first.",
            preset="benchmark",
        )

    st.subheader("Health vulnerability and ESB access")
    col1, col2 = st.columns(2)
    with col1:
        fig_asthma = px.scatter(
            filt.dropna(subset=["asthma_rate", "esb_adoption_rate"]),
            x="asthma_rate",
            y="esb_adoption_rate",
            opacity=0.4,
            trendline="ols",
            labels={"asthma_rate": "Adult asthma rate", "esb_adoption_rate": "ESB adoption (%)"},
            template="plotly_white",
        )
        fig_asthma.update_layout(height=320, margin=dict(t=20, b=0))
        st.plotly_chart(fig_asthma, width='stretch')
        explain_chart(
            "High-asthma districts do not clearly separate themselves from the rest of the sample on adoption. The relationship appears weak and noisy.",
            "That weak signal is itself informative: a health-based targeting story would likely produce a stronger visible gradient.",
            preset="signal",
        )

    with col2:
        fig_dis = px.scatter(
            filt.dropna(subset=["pct_disability", "esb_adoption_rate"]),
            x="pct_disability",
            y="esb_adoption_rate",
            opacity=0.4,
            trendline="ols",
            labels={"pct_disability": "Students with disability (%)", "esb_adoption_rate": "ESB adoption (%)"},
            template="plotly_white",
        )
        fig_dis.update_layout(height=320, margin=dict(t=20, b=0))
        st.plotly_chart(fig_dis, width='stretch')
        explain_chart(
            "Disability prevalence is shown here as an additional vulnerability lens rather than a direct causal driver of bus electrification.",
            "Including it strengthens the portfolio narrative because it shows the analysis is testing several dimensions of need, not relying on a single equity variable.",
            preset="reading",
        )

    st.subheader("EPA priority districts")
    if "epa_2023_priority" in filt.columns:
        priority_compare = (
            filt.groupby("epa_2023_priority")
            .agg(
                avg_adoption=("esb_adoption_rate", "mean"),
                count=("district", "count"),
                avg_pm25=("pm25", "mean"),
                avg_income=("median_income", "mean"),
            )
            .reset_index()
        )
        priority_compare.columns = ["EPA 2023 priority", "Average adoption (%)", "District count", "Average PM2.5", "Average income ($)"]
        priority_compare = priority_compare.dropna(subset=["EPA 2023 priority"])
        st.dataframe(priority_compare.round(2), width='stretch', hide_index=True)
        explain_chart(
            "This table checks whether official prioritization is visible in realized outcomes, not only in program design.",
            "A useful policy dashboard should always compare stated targeting with observed deployment. Otherwise, priority labels risk becoming performative rather than operational.",
            preset="focus",
        )

