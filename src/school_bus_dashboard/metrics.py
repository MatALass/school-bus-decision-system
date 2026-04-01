from __future__ import annotations

import numpy as np
import pandas as pd


def _safe_numeric(series: pd.Series) -> pd.Series:
    return pd.to_numeric(series, errors="coerce")


def _safe_min_max(series: pd.Series) -> pd.Series:
    numeric = _safe_numeric(series)
    min_value = numeric.min()
    max_value = numeric.max()

    if pd.isna(min_value) or pd.isna(max_value) or min_value == max_value:
        return pd.Series(0.0, index=series.index)

    return (numeric - min_value) / (max_value - min_value)


def _safe_log_min_max(series: pd.Series) -> pd.Series:
    numeric = _safe_numeric(series).fillna(0).clip(lower=0)
    logged = np.log1p(numeric)

    min_value = logged.min()
    max_value = logged.max()

    if pd.isna(min_value) or pd.isna(max_value) or min_value == max_value:
        return pd.Series(0.0, index=series.index)

    return (logged - min_value) / (max_value - min_value)


def _quantile_bucket(series: pd.Series, labels: list[str]) -> pd.Series:
    clean = _safe_numeric(series)
    non_null = clean.dropna()

    if non_null.empty or non_null.nunique() < len(labels):
        return pd.Series(["Unknown"] * len(series), index=series.index)

    try:
        ranked = clean.rank(method="average", pct=True)
        bins = np.linspace(0, 1, len(labels) + 1)
        bucketed = pd.cut(
            ranked,
            bins=bins,
            labels=labels,
            include_lowest=True,
            duplicates="drop",
        )
        return bucketed.astype("string").fillna("Unknown")
    except ValueError:
        return pd.Series(["Unknown"] * len(series), index=series.index)


def compute_metrics(df: pd.DataFrame) -> pd.DataFrame:
    metrics_df = df.copy()

    numeric_columns = [
        "total_buses",
        "electric_buses",
        "pm25",
        "low_income_pct",
        "median_income",
        "student_count",
        "poverty_pct",
        "children_disability_pct",
        "fleet_electric_pct",
    ]
    for column in numeric_columns:
        if column in metrics_df.columns:
            metrics_df[column] = _safe_numeric(metrics_df[column])

    metrics_df["total_buses"] = metrics_df["total_buses"].fillna(0)
    metrics_df["electric_buses"] = metrics_df["electric_buses"].fillna(0)

    metrics_df["adoption_rate"] = 0.0
    valid_mask = metrics_df["total_buses"] > 0
    metrics_df.loc[valid_mask, "adoption_rate"] = (
        metrics_df.loc[valid_mask, "electric_buses"]
        / metrics_df.loc[valid_mask, "total_buses"]
    )
    metrics_df["adoption_rate"] = metrics_df["adoption_rate"].clip(lower=0, upper=1)

    metrics_df["adoption_gap"] = 1 - metrics_df["adoption_rate"]

    if "fleet_electric_pct" in metrics_df.columns:
        metrics_df["fleet_electric_pct"] = (
            metrics_df["fleet_electric_pct"] / 100
            if metrics_df["fleet_electric_pct"].max(skipna=True) > 1
            else metrics_df["fleet_electric_pct"]
        )

    metrics_df["fleet_size_band"] = pd.cut(
        metrics_df["total_buses"],
        bins=[-1, 24, 99, 249, float("inf")],
        labels=["Small", "Medium", "Large", "Very large"],
    ).astype("string")

    return metrics_df


def compute_priority_score(df: pd.DataFrame) -> pd.DataFrame:
    scored_df = df.copy()

    scored_df["pm25_norm"] = _safe_min_max(scored_df["pm25"])
    scored_df["low_income_norm"] = _safe_min_max(scored_df["low_income_pct"])
    scored_df["poverty_norm"] = _safe_min_max(
        scored_df["poverty_pct"] if "poverty_pct" in scored_df.columns else pd.Series(0, index=scored_df.index)
    )
    scored_df["disability_norm"] = _safe_min_max(
        scored_df["children_disability_pct"] if "children_disability_pct" in scored_df.columns else pd.Series(0, index=scored_df.index)
    )
    scored_df["adoption_gap_norm"] = _safe_min_max(scored_df["adoption_gap"])
    scored_df["fleet_scale_norm"] = _safe_log_min_max(scored_df["total_buses"])
    scored_df["income_inverse_norm"] = 1 - _safe_min_max(
        scored_df["median_income"] if "median_income" in scored_df.columns else pd.Series(0, index=scored_df.index)
    )

    scored_df["priority_score"] = (
        0.25 * scored_df["pm25_norm"]
        + 0.20 * scored_df["low_income_norm"]
        + 0.15 * scored_df["poverty_norm"]
        + 0.10 * scored_df["disability_norm"]
        + 0.20 * scored_df["adoption_gap_norm"]
        + 0.10 * scored_df["fleet_scale_norm"]
    ) * 100

    scored_df["priority_score"] = scored_df["priority_score"].round(2)

    scored_df["priority_tier"] = _quantile_bucket(
        scored_df["priority_score"],
        ["Watch", "Moderate", "High", "Critical"],
    )

    scored_df["equity_risk_bucket"] = _quantile_bucket(
        (
            scored_df["low_income_norm"]
            + scored_df["poverty_norm"]
            + scored_df["disability_norm"]
            + scored_df["income_inverse_norm"]
        ) / 4,
        ["Low", "Moderate", "High", "Very high"],
    )

    scored_df["air_quality_bucket"] = _quantile_bucket(
        scored_df["pm25_norm"],
        ["Low", "Moderate", "High", "Very high"],
    )

    scored_df["recommendation_flag"] = (
        (scored_df["priority_tier"].isin(["High", "Critical"]))
        & (scored_df["total_buses"] >= 25)
    )

    scored_df["quick_win_flag"] = (
        (scored_df["priority_tier"].isin(["High", "Critical"]))
        & (scored_df["adoption_rate"] < 0.05)
        & (scored_df["total_buses"] >= 50)
    )

    return scored_df