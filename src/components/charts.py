"""
Reusable Plotly chart builders.
Each function returns a go.Figure — no Streamlit calls here.
"""

import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np

PALETTE = {
    "primary": "#1f77b4",
    "accent": "#ff7f0e",
    "danger": "#d62728",
    "success": "#2ca02c",
    "neutral": "#7f7f7f",
    "light": "#aec7e8",
}

TEMPLATE = "plotly_white"


def kpi_indicators(values: dict, state_values: dict | None = None) -> go.Figure:
    """4 KPI indicator cards with optional delta vs state average."""
    specs = [[{"type": "indicator"}] * len(values)]
    fig = make_subplots(rows=1, cols=len(values), specs=specs)

    meta = {
        "esb_adoption_rate": ("ESB Adoption", "%", False),
        "pm25": ("Air Pollution (PM2.5)", " µg/m³", False),
        "median_income": ("Median Income", "", True),
        "free_lunch_pct": ("Free/Reduced Lunch", "%", False),
        "equity_score": ("Equity Score", "/100", False),
    }

    for col_idx, (key, val) in enumerate(values.items(), 1):
        label, suffix, is_dollar = meta.get(key, (key, "", False))
        num_fmt = {"prefix": "$", "valueformat": ",.0f"} if is_dollar else {"suffix": suffix}

        delta = None
        if state_values and key in state_values and not np.isnan(state_values[key]):
            delta = {"reference": state_values[key], "relative": False}

        trace_kw = dict(
            mode="number+delta" if delta else "number",
            value=val,
            title={"text": f"<b>{label}</b>", "font": {"size": 14}},
            number={**num_fmt, "font": {"size": 28}},
        )
        if delta:
            trace_kw["delta"] = delta

        fig.add_trace(go.Indicator(**trace_kw), 1, col_idx)

    fig.update_layout(
        template=TEMPLATE,
        height=200,
        margin=dict(t=40, b=10, l=10, r=10),
        paper_bgcolor="rgba(0,0,0,0)",
    )
    return fig


def adoption_map(df: pd.DataFrame, highlight_state: str | None = None) -> go.Figure:
    """Choropleth of ESB adoption rate by state."""
    fig = px.choropleth(
        df,
        locations="state_abbr",
        locationmode="USA-states",
        color="avg_pct_committed_pct",
        color_continuous_scale="YlGn",
        scope="usa",
        labels={"avg_pct_committed_pct": "ESB Adoption (%)"},
        hover_name="state",
        hover_data={"committed_esb": True, "avg_pct_committed_pct": ":.2f"},
        template=TEMPLATE,
    )
    fig.update_layout(
        margin=dict(l=0, r=0, t=30, b=0),
        height=420,
        coloraxis_colorbar=dict(title="Adoption %", len=0.7),
    )
    return fig


def scatter_equity_adoption(df: pd.DataFrame, x_col: str, y_col: str,
                             color_col: str, highlight_city_df=None,
                             xlab: str = "", ylab: str = "") -> go.Figure:
    """Generic scatter with optional highlight points."""
    fig = px.scatter(
        df.dropna(subset=[x_col, y_col]),
        x=x_col,
        y=y_col,
        color=color_col,
        color_continuous_scale="RdYlGn_r",
        opacity=0.5,
        size_max=10,
        hover_name="district",
        hover_data={"state": True, x_col: ":.2f", y_col: ":.2f"},
        labels={x_col: xlab or x_col, y_col: ylab or y_col},
        template=TEMPLATE,
    )
    if highlight_city_df is not None and not highlight_city_df.empty:
        fig.add_trace(go.Scatter(
            x=highlight_city_df[x_col],
            y=highlight_city_df[y_col],
            mode="markers",
            marker=dict(size=14, color=PALETTE["danger"],
                        line=dict(color="black", width=1.5)),
            name="Selected city",
            text=highlight_city_df["district"],
        ))
    fig.update_layout(height=420, margin=dict(t=30, b=0))
    return fig


def bar_comparison(city_vals: dict, state_vals: dict, city_name: str, state_name: str) -> go.Figure:
    """Grouped bar: city vs state average across multiple metrics."""
    labels = list(city_vals.keys())
    fig = go.Figure(data=[
        go.Bar(name=city_name, x=labels, y=list(city_vals.values()),
               marker_color=PALETTE["accent"], text=[f"{v:.1f}" for v in city_vals.values()],
               textposition="outside"),
        go.Bar(name=f"{state_name} avg", x=labels, y=list(state_vals.values()),
               marker_color=PALETTE["light"], text=[f"{v:.1f}" for v in state_vals.values()],
               textposition="outside"),
    ])
    fig.update_layout(barmode="group", template=TEMPLATE, height=380,
                      margin=dict(t=30, b=10))
    return fig


def timeline_adoptions(bus_df: pd.DataFrame) -> go.Figure:
    """Cumulative ESB adoptions over time (by year)."""
    yearly = (
        bus_df.dropna(subset=["year_awarded"])
        .groupby("year_awarded")
        .size()
        .reset_index(name="buses")
    )
    yearly["cumulative"] = yearly["buses"].cumsum()

    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(go.Bar(x=yearly["year_awarded"], y=yearly["buses"],
                         name="New buses", marker_color=PALETTE["light"]), secondary_y=False)
    fig.add_trace(go.Scatter(x=yearly["year_awarded"], y=yearly["cumulative"],
                              name="Cumulative", mode="lines+markers",
                              line=dict(color=PALETTE["primary"], width=2.5)),
                  secondary_y=True)
    fig.update_layout(template=TEMPLATE, height=380,
                      xaxis_title="Year", margin=dict(t=30, b=10))
    fig.update_yaxes(title_text="New buses / year", secondary_y=False)
    fig.update_yaxes(title_text="Cumulative total", secondary_y=True)
    return fig


def oem_market_share(bus_df: pd.DataFrame, top_n: int = 8) -> go.Figure:
    oem_counts = bus_df["oem"].value_counts().head(top_n)
    fig = px.bar(
        x=oem_counts.values,
        y=oem_counts.index,
        orientation="h",
        labels={"x": "Number of ESBs", "y": "Manufacturer"},
        color=oem_counts.values,
        color_continuous_scale="Blues",
        template=TEMPLATE,
    )
    fig.update_layout(height=380, showlegend=False, coloraxis_showscale=False,
                      margin=dict(t=30, b=10))
    return fig


def funding_breakdown(bus_df: pd.DataFrame) -> go.Figure:
    src = bus_df["funding_category"].value_counts().head(10)
    fig = px.pie(
        values=src.values,
        names=src.index,
        hole=0.45,
        color_discrete_sequence=px.colors.qualitative.Set2,
        template=TEMPLATE,
    )
    fig.update_traces(textinfo="percent+label", textposition="outside")
    fig.update_layout(height=400, showlegend=False, margin=dict(t=30, b=10))
    return fig


def cost_distribution(bus_df: pd.DataFrame) -> go.Figure:
    df_c = bus_df.dropna(subset=["bus_cost"])
    fig = px.histogram(
        df_c, x="bus_cost", nbins=50,
        color="bus_type_label",
        labels={"bus_cost": "Bus cost ($)", "bus_type_label": "Type"},
        template=TEMPLATE,
        barmode="overlay",
        opacity=0.75,
    )
    fig.update_layout(height=380, margin=dict(t=30, b=10))
    return fig


def equity_heatmap_state(df: pd.DataFrame) -> go.Figure:
    """Average equity metrics grouped by state (top 20 by ESB count)."""
    top_states = df.groupby("state")["committed_esb"].sum().nlargest(20).index
    state_agg = (
        df[df["state"].isin(top_states)]
        .groupby("state")[["pm25", "pct_nonwhite_hispanic", "pct_low_income", "free_lunch_pct"]]
        .mean()
        .round(2)
    )
    fig = px.imshow(
        state_agg.T,
        color_continuous_scale="RdYlGn_r",
        labels=dict(color="Value"),
        aspect="auto",
        template=TEMPLATE,
    )
    fig.update_layout(height=380, margin=dict(t=30, b=10),
                      xaxis_title="State", yaxis_title="Metric")
    return fig


def district_ranking(df: pd.DataFrame, col: str, ascending: bool = False,
                      label: str = "", top_n: int = 15) -> go.Figure:
    sub = df[["district", "state", col]].dropna().sort_values(col, ascending=ascending).head(top_n)
    fig = px.bar(
        sub, y="district", x=col, orientation="h",
        color=col, color_continuous_scale="Blues" if not ascending else "Reds_r",
        labels={col: label or col, "district": ""},
        hover_data={"state": True},
        template=TEMPLATE,
    )
    fig.update_layout(height=max(380, top_n * 26), showlegend=False,
                      coloraxis_showscale=False, margin=dict(t=30, b=10))
    return fig
