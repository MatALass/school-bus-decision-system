"""Fleet and technology page."""

from pathlib import Path
import sys

import pandas as pd
import plotly.express as px
import streamlit as st

sys.path.insert(0, str(Path(__file__).parents[1]))

from src.components.charts import cost_distribution, oem_market_share, timeline_adoptions
from src.components.ui import explain_chart, page_story, section_intro
from src.data.loader import load_bus, load_utilities
from src.data.processor import clean_bus
from src.utils.helpers import fmt_dollar, fmt_number


OWNERSHIP_COLUMNS = {
    "Investor-owned": "9d. Investor ownership",
    "Cooperative": "9b. Cooperative ownership",
    "Municipal": "9e. Municipal ownership",
    "Federal": "9c. Federal ownership",
    "Political subdivision": "9g. Political subdivision",
    "Municipal marketing authority": "9f. Municipal marketing authority",
    "State-owned": "9h. State ownership",
    "Wholesale": "9i. Wholesale",
    "Not available": "9j. Not available",
}


def render() -> None:
    st.header("Fleet and technology")
    section_intro(
        "This page looks at industrial structure rather than social targeting: manufacturer concentration, vehicle mix, procurement costs, charging ecosystem, and utility footprint. It is the right lens for assessing whether the ESB market is scaling on a broad base or still relying on a narrow set of actors."
    )

    bus_df = clean_bus(load_bus())
    utilities_df = load_utilities()

    with st.sidebar:
        st.subheader("Fleet filters")
        selected_states = st.multiselect("State", options=sorted(bus_df["state"].dropna().unique()), default=[])
        selected_status = st.multiselect(
            "Bus status",
            options=bus_df["status"].dropna().unique().tolist(),
            default=bus_df["status"].dropna().unique().tolist(),
        )
        year_range = st.slider(
            "Award year",
            int(bus_df["year_awarded"].dropna().min()),
            int(bus_df["year_awarded"].dropna().max()),
            (2017, int(bus_df["year_awarded"].dropna().max())),
        )

    filt = bus_df.copy()
    if selected_states:
        filt = filt[filt["state"].isin(selected_states)]
    if selected_status:
        filt = filt[filt["status"].isin(selected_status)]
    filt = filt[(filt["year_awarded"].isna()) | ((filt["year_awarded"] >= year_range[0]) & (filt["year_awarded"] <= year_range[1]))]

    utility_name_cols = [c for c in utilities_df.columns if c.startswith("9a. Utility name")]
    utility_series = pd.Series(utilities_df[utility_name_cols].values.ravel()).dropna().astype(str).str.strip()
    utility_series = utility_series[utility_series.ne("")]

    oem_top5_share = filt["oem"].value_counts(normalize=True).head(5).sum() * 100 if len(filt) else 0
    fund_top3_share = filt["funding_source"].value_counts(normalize=True).head(3).sum() * 100 if len(filt) else 0

    page_story(
        kpi_title="Share of filtered buses accounted for by the top five OEMs",
        kpi_value=f"{oem_top5_share:.1f}%",
        observation=(
            f"The supply side remains concentrated, and the same pattern appears on the finance side: the top three funding channels represent about {fund_top3_share:.1f}% of buses in the current slice."
        ),
        implication=(
            "This is not yet a deeply diversified market. Portfolio-grade analysis should frame ESB deployment as a scaling system that depends on industrial capacity, infrastructure partners, and policy concentration at the same time."
        ),
    )

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("ESBs in scope", fmt_number(len(filt)))
    c2.metric("OEMs represented", fmt_number(filt["oem"].nunique()))
    c3.metric("Average bus cost", fmt_dollar(filt["bus_cost"].mean()))
    c4.metric("Total bus + charger investment", fmt_dollar(filt["total_cost"].sum()))
    c5.metric("Unique utility names", fmt_number(utility_series.nunique()))

    st.subheader("Deployment timeline")
    st.plotly_chart(timeline_adoptions(filt), width='stretch')
    explain_chart(
        "The recent years dominate the cumulative build-up, which confirms that the market expansion is recent rather than the product of a long steady ramp.",
        "That matters for forecasting. The observed market shape is consistent with policy acceleration, so it should not be extrapolated mechanically as if it were a mature organic trend.",
        preset="signal",
    )

    st.subheader("Manufacturer concentration")
    col1, col2 = st.columns(2)
    with col1:
        st.plotly_chart(oem_market_share(filt, top_n=10), width='stretch')
        explain_chart(
            "The supplier leaderboard shows whether the filtered market is broadening or collapsing toward a small set of manufacturers.",
            "In an early-stage transition, concentration is normal. The strategic question is whether concentration is beginning to ease as volumes rise, or whether scaling still depends on a very small vendor base.",
            preset="focus",
        )

    with col2:
        oem_time = (
            filt.dropna(subset=["year_awarded", "oem"])
            .groupby(["year_awarded", "oem"])
            .size()
            .reset_index(name="count")
        )
        top_oems = filt["oem"].value_counts().head(6).index.tolist()
        oem_time_top = oem_time[oem_time["oem"].isin(top_oems)]
        fig_oem_time = px.line(
            oem_time_top,
            x="year_awarded",
            y="count",
            color="oem",
            markers=True,
            labels={"year_awarded": "Year", "count": "ESBs", "oem": "Manufacturer"},
            template="plotly_white",
        )
        fig_oem_time.update_layout(height=380, margin=dict(t=20, b=0), title="Top OEMs over time")
        st.plotly_chart(fig_oem_time, width='stretch')
        explain_chart(
            "The lines show whether incumbents are defending share over time or whether the market is becoming more competitive as deployment expands.",
            "A flat or declining leader alongside growing peers would indicate diversification. Parallel growth across the same incumbents suggests scale is rising faster than competition.",
            preset="reading",
        )

    st.subheader("Fleet mix")
    col1, col2, col3 = st.columns(3)
    type_counts = filt["bus_type_label"].value_counts().reset_index()
    type_counts.columns = ["Type", "Count"]
    with col1:
        fig_type = px.pie(
            type_counts,
            values="Count",
            names="Type",
            hole=0.4,
            color_discrete_sequence=px.colors.qualitative.Pastel,
            template="plotly_white",
        )
        fig_type.update_traces(textinfo="percent+label")
        fig_type.update_layout(height=300, showlegend=False, margin=dict(t=20, b=0))
        st.plotly_chart(fig_type, width='stretch')
        explain_chart(
            "The filtered fleet is still dominated by standard Type C buses, with Type D and Type A trailing behind.",
            "That pattern suggests the market is scaling first in the most common operational segment rather than solving all route types evenly at once.",
            preset="pattern",
        )

    with col2:
        cost_type = filt.groupby("bus_type_label")["bus_cost"].agg(["mean", "median"]).reset_index()
        cost_type.columns = ["Type", "Average cost ($)", "Median cost ($)"]
        fig_cost_type = px.bar(
            cost_type.melt(id_vars="Type"),
            x="Type",
            y="value",
            color="variable",
            barmode="group",
            labels={"value": "Cost ($)", "variable": "Metric"},
            template="plotly_white",
        )
        fig_cost_type.update_layout(height=300, margin=dict(t=20, b=0), title="Cost by bus type")
        st.plotly_chart(fig_cost_type, width='stretch')
        explain_chart(
            "Using both average and median cost helps separate typical procurement levels from outlier-heavy contracts.",
            "That distinction is important in dashboards meant for decision support. Means alone often overstate the practical price point districts are most likely to face.",
            preset="benchmark",
        )

    with col3:
        oem_type = filt.dropna(subset=["oem", "bus_type_label"]).groupby(["oem", "bus_type_label"]).size().reset_index(name="count")
        top_oems_5 = filt["oem"].value_counts().head(5).index
        fig_oem_type = px.bar(
            oem_type[oem_type["oem"].isin(top_oems_5)],
            x="oem",
            y="count",
            color="bus_type_label",
            barmode="stack",
            labels={"oem": "OEM", "count": "ESBs", "bus_type_label": "Type"},
            template="plotly_white",
        )
        fig_oem_type.update_layout(height=300, margin=dict(t=20, b=0), xaxis_tickangle=-30, title="OEM specialization")
        st.plotly_chart(fig_oem_type, width='stretch')
        explain_chart(
            "This view shows whether leading manufacturers are diversified across formats or concentrated on a smaller set of vehicle types.",
            "If each major supplier specializes narrowly, route electrification flexibility remains constrained even when total bus counts rise.",
            preset="focus",
        )

    st.subheader("Cost and funding")
    col1, col2 = st.columns(2)
    with col1:
        st.plotly_chart(cost_distribution(filt), width='stretch')
        explain_chart(
            "The cost distribution is wide, which means there is no single 'true' ESB price visible in the sample. Vehicle category and contract context still matter a lot.",
            "This is the right message to surface in a portfolio project: dashboards should help users resist false precision, not encourage it.",
            preset="signal",
        )

    with col2:
        cost_time = filt.dropna(subset=["year_awarded", "bus_cost"])
        cost_yr = cost_time.groupby("year_awarded")["bus_cost"].agg(["mean", "median"]).reset_index()
        cost_yr.columns = ["Year", "Average cost ($)", "Median cost ($)"]
        fig_cost_time = px.line(
            cost_yr.melt(id_vars="Year"),
            x="Year",
            y="value",
            color="variable",
            labels={"value": "Cost ($)", "variable": "Metric"},
            markers=True,
            template="plotly_white",
        )
        fig_cost_time.update_layout(height=380, margin=dict(t=20, b=0), title="Cost evolution over time")
        st.plotly_chart(fig_cost_time, width='stretch')
        explain_chart(
            "Average and median move together only when the market itself is shifting. When they diverge, a small number of atypical procurements are probably doing the work.",
            "That distinction helps avoid overinterpreting noisy year-on-year cost movements as structural learning or inflation effects.",
            preset="reading",
        )

    st.subheader("Funding and infrastructure ecosystem")
    col1, col2 = st.columns(2)
    with col1:
        fund = filt["funding_source"].value_counts().head(12)
        fig_fund = px.bar(
            x=fund.values,
            y=fund.index,
            orientation="h",
            labels={"x": "ESBs", "y": "Funding source"},
            color=fund.values,
            color_continuous_scale="Blues",
            template="plotly_white",
        )
        fig_fund.update_layout(height=420, showlegend=False, coloraxis_showscale=False, margin=dict(t=20, b=0))
        st.plotly_chart(fig_fund, width='stretch')
        explain_chart(
            "The funding ranking shows which public programs are actually underwriting deployment in practice, not only which ones exist in theory.",
            "If one or two channels dominate, the market remains exposed to grant timing and policy continuity. That is a financing concentration issue, not just a budget detail.",
            preset="pattern",
        )

    with col2:
        charger = filt["charging_company"].value_counts().head(10)
        fig_charger = px.bar(
            x=charger.values,
            y=charger.index,
            orientation="h",
            labels={"x": "Deployments", "y": "Charging company"},
            color=charger.values,
            color_continuous_scale="Greens",
            template="plotly_white",
        )
        fig_charger.update_layout(height=420, showlegend=False, coloraxis_showscale=False, margin=dict(t=20, b=0))
        st.plotly_chart(fig_charger, width='stretch')
        explain_chart(
            "The infrastructure side has its own concentration pattern. Charging vendors do not appear evenly distributed across deployments.",
            "That matters because electrification can bottleneck on charger delivery and grid integration just as much as on bus availability.",
            preset="focus",
        )

    st.subheader("Utility footprint from the workbook")
    col1, col2 = st.columns(2)
    with col1:
        utility_counts = utility_series.value_counts().head(12)
        fig_utility = px.bar(
            x=utility_counts.values,
            y=utility_counts.index,
            orientation="h",
            labels={"x": "Mentions across LEAs", "y": "Utility"},
            color=utility_counts.values,
            color_continuous_scale="Tealgrn",
            template="plotly_white",
        )
        fig_utility.update_layout(height=440, showlegend=False, coloraxis_showscale=False, margin=dict(t=20, b=0))
        st.plotly_chart(fig_utility, width='stretch')
        explain_chart(
            "The utilities sheet adds a layer the bus table alone cannot show: which grid actors appear most often across the school entities represented in the workbook.",
            "That makes the dashboard stronger analytically. ESB scaling is a coordination problem with utilities, not just a procurement problem with OEMs.",
            preset="benchmark",
        )

    with col2:
        ownership_data = pd.DataFrame(
            {
                "Ownership type": list(OWNERSHIP_COLUMNS.keys()),
                "LEAs": [int((utilities_df[col].astype(str).str.lower() == "yes").sum()) for col in OWNERSHIP_COLUMNS.values()],
            }
        ).sort_values("LEAs", ascending=False)
        fig_owner = px.bar(
            ownership_data,
            x="LEAs",
            y="Ownership type",
            orientation="h",
            color="LEAs",
            color_continuous_scale="Purples",
            template="plotly_white",
        )
        fig_owner.update_layout(height=440, showlegend=False, coloraxis_showscale=False, margin=dict(t=20, b=0), title="Utility ownership structure")
        st.plotly_chart(fig_owner, width='stretch')
        explain_chart(
            "Investor-owned, cooperative, and municipal utilities dominate the workbook's utility relationships. The grid context is therefore operationally fragmented rather than governed by a single utility model.",
            "That is important for rollout realism. Utility engagement strategies are unlikely to be one-size-fits-all across the country.",
            preset="reading",
        )

    with st.expander("View raw bus data"):
        st.dataframe(filt.head(500), width='stretch')
