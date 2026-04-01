from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


def make_kpi_figure(metrics: dict[str, float]) -> go.Figure:
    fig = go.Figure()
    values = [
        ("Adoption rate (%)", metrics["adoption_rate"], "%"),
        ("PM2.5", metrics["avg_pm25"], " µg/m³"),
        ("Median income", metrics["avg_income"], " $"),
        ("Free/reduced lunch", metrics["avg_free_lunch_pct"], "%"),
    ]

    for index, (label, value, suffix) in enumerate(values, start=1):
        fig.add_trace(
            go.Indicator(
                mode="number",
                value=value,
                number={"suffix": suffix},
                title={"text": label},
                domain={"row": 0, "column": index - 1},
            )
        )

    fig.update_layout(grid={"rows": 1, "columns": 4, "pattern": "independent"}, height=220)
    return fig


def make_benchmark_bar(scope_metrics: dict[str, float], benchmark_metrics: dict[str, float], scope_label: str, benchmark_label: str) -> go.Figure:
    categories = ["Adoption rate", "PM2.5", "Median income", "Free/reduced lunch"]
    fig = go.Figure()
    fig.add_bar(
        name=scope_label,
        x=categories,
        y=[
            scope_metrics["adoption_rate"],
            scope_metrics["avg_pm25"],
            scope_metrics["avg_income"],
            scope_metrics["avg_free_lunch_pct"],
        ],
    )
    fig.add_bar(
        name=benchmark_label,
        x=categories,
        y=[
            benchmark_metrics["adoption_rate"],
            benchmark_metrics["avg_pm25"],
            benchmark_metrics["avg_income"],
            benchmark_metrics["avg_free_lunch_pct"],
        ],
    )
    fig.update_layout(barmode="group", height=420)
    return fig


def make_map(frame: pd.DataFrame) -> go.Figure:
    hover_data = {
        "district": True,
        "city": True,
        "state": True,
        "esb_adoption_rate": ":.1f",
        "pm25": ":.2f",
        "free_lunch_pct": ":.1f",
        "priority_score": ":.1f" if "priority_score" in frame.columns else False,
    }
    fig = px.scatter_map(
        frame.dropna(subset=["latitude", "longitude"]),
        lat="latitude",
        lon="longitude",
        hover_name="district",
        hover_data=hover_data,
        zoom=4,
        height=500,
    )
    fig.update_layout(margin=dict(l=0, r=0, t=0, b=0))
    return fig


def make_priority_scatter(frame: pd.DataFrame, highlight_city: str | None = None) -> go.Figure:
    plot_df = frame.copy()
    plot_df["is_highlight"] = plot_df["city"] == highlight_city if highlight_city else False

    fig = px.scatter(
        plot_df,
        x="pm25",
        y="esb_adoption_rate",
        size="total_buses",
        hover_name="district",
        hover_data=["city", "priority_score", "free_lunch_pct", "median_income"],
        symbol="is_highlight",
        height=520,
        labels={
            "pm25": "PM2.5",
            "esb_adoption_rate": "ESB adoption rate (%)",
            "total_buses": "Total buses",
        },
    )
    return fig


def make_priority_ranking(frame: pd.DataFrame) -> go.Figure:
    top_df = frame.head(15).sort_values("priority_score", ascending=True)
    fig = px.bar(
        top_df,
        x="priority_score",
        y="district",
        orientation="h",
        hover_data=["city", "pm25", "free_lunch_pct", "esb_adoption_rate", "median_income"],
        height=600,
    )
    fig.update_layout(yaxis_title="", xaxis_title="Priority score")
    return fig


def make_distribution(frame: pd.DataFrame) -> go.Figure:
    fig = px.histogram(
        frame,
        x="esb_adoption_rate",
        nbins=20,
        marginal="box",
        height=450,
        labels={"esb_adoption_rate": "ESB adoption rate (%)"},
    )
    return fig
