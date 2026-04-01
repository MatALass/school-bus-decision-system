"""Decision-oriented scoring and prioritization logic for V5."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class ScoreWeights:
    need: float = 0.45
    transition_gap: float = 0.35
    scale: float = 0.10
    complexity: float = 0.10


def score_profile_catalog() -> dict[str, ScoreWeights]:
    """Named weighting profiles for scenario testing."""
    return {
        "Balanced": ScoreWeights(need=0.45, transition_gap=0.35, scale=0.10, complexity=0.10),
        "Equity first": ScoreWeights(need=0.60, transition_gap=0.25, scale=0.05, complexity=0.10),
        "Deployment first": ScoreWeights(need=0.35, transition_gap=0.40, scale=0.15, complexity=0.10),
        "Scale first": ScoreWeights(need=0.30, transition_gap=0.30, scale=0.30, complexity=0.10),
    }


def _minmax(series: pd.Series) -> pd.Series:
    numeric = pd.to_numeric(series, errors="coerce")
    min_v = numeric.min(skipna=True)
    max_v = numeric.max(skipna=True)
    if pd.isna(min_v) or pd.isna(max_v) or min_v == max_v:
        return pd.Series(0.0, index=series.index)
    return (numeric - min_v) / (max_v - min_v)


def _safe_share(num: pd.Series, den: pd.Series) -> pd.Series:
    den = pd.to_numeric(den, errors="coerce").replace(0, np.nan)
    num = pd.to_numeric(num, errors="coerce")
    return num / den


def _yes_no_to_float(series: pd.Series) -> pd.Series:
    mapped = (
        series.astype(str)
        .str.strip()
        .str.lower()
        .map({"yes": 1.0, "true": 1.0, "1": 1.0, "no": 0.0, "false": 0.0, "0": 0.0})
    )
    return mapped.fillna(0.0)


def _utility_long_frame(df: pd.DataFrame) -> pd.DataFrame:
    utility_cols = [col for col in df.columns if col.startswith("9a. Utility name")]
    base_cols = [col for col in ["1a. State", "1b. LEA name", "1c. LEA ID"] if col in df.columns]
    if not utility_cols:
        return pd.DataFrame(columns=[*base_cols, "utility_name"])
    melted = df[base_cols + utility_cols].melt(
        id_vars=base_cols,
        value_vars=utility_cols,
        value_name="utility_name",
    )
    utility_name = melted["utility_name"].astype("string").str.strip()
    melted["utility_name"] = utility_name
    return melted[utility_name.notna() & utility_name.ne("")].copy()


def _bucket(series: pd.Series, labels: list[str]) -> pd.Series:
    ranked = pd.to_numeric(series, errors="coerce").rank(method="average", pct=True)
    try:
        out = pd.cut(
            ranked,
            bins=np.linspace(0, 1, len(labels) + 1),
            labels=labels,
            include_lowest=True,
            duplicates="drop",
        )
        return out.astype("string").fillna("Unknown")
    except ValueError:
        return pd.Series(["Unknown"] * len(series), index=series.index, dtype="string")


def build_decision_dataset(
    district_df: pd.DataFrame,
    bus_df: pd.DataFrame,
    utilities_df: pd.DataFrame,
    counties_df: pd.DataFrame,
    congress_df: pd.DataFrame,
    weights: ScoreWeights | None = None,
) -> pd.DataFrame:
    """Merge district, fleet, and complexity signals into a ranking-ready frame."""
    weights = weights or ScoreWeights()

    frame = district_df.copy()
    if "lea_id" not in frame.columns:
        frame["lea_id"] = np.nan

    bus_group = (
        bus_df.groupby(["state", "district", "city"], dropna=False)
        .agg(
            bus_rows=("district", "size"),
            bus_oems=("oem", "nunique"),
            funding_sources=("funding_source", "nunique"),
            charging_companies=("charging_company", "nunique"),
            avg_total_cost=("total_cost", "mean"),
            operating_bus_rows=("status", lambda s: s.astype(str).str.contains("operat", case=False, na=False).sum()),
            delivered_bus_rows=("status", lambda s: s.astype(str).str.contains("deliver|operat", case=False, na=False).sum()),
        )
        .reset_index()
    )

    util_long = _utility_long_frame(utilities_df)
    if not util_long.empty:
        util_group = (
            util_long.groupby(["1a. State", "1b. LEA name", "1c. LEA ID"], dropna=False)
            .agg(
                utility_count=("utility_name", "nunique"),
                utility_mentions=("utility_name", "size"),
            )
            .reset_index()
            .rename(columns={"1a. State": "state", "1b. LEA name": "district", "1c. LEA ID": "lea_id"})
        )
    else:
        util_group = pd.DataFrame(columns=["state", "district", "lea_id", "utility_count", "utility_mentions"])

    county_group = (
        counties_df.groupby(["1a. State", "1b. LEA name", "1c. LEA ID"], dropna=False)
        .agg(
            county_count=("10c. Number of counties in LEA", "max"),
        )
        .reset_index()
        .rename(columns={"1a. State": "state", "1b. LEA name": "district", "1c. LEA ID": "lea_id"})
    )

    congress_group = (
        congress_df.groupby(["1a. State", "1b. LEA name", "1c. LEA ID"], dropna=False)
        .agg(
            congressional_count=("11c. Number of congressional districts in LEA", "max"),
        )
        .reset_index()
        .rename(columns={"1a. State": "state", "1b. LEA name": "district", "1c. LEA ID": "lea_id"})
    )

    for aux in (bus_group, util_group, county_group, congress_group):
        if "state" in aux.columns:
            aux["state"] = aux["state"].astype(str).str.upper().str.strip()
        if "district" in aux.columns:
            aux["district"] = aux["district"].astype(str).str.strip()
        if "city" in aux.columns:
            aux["city"] = aux["city"].astype(str).str.strip()

    frame = frame.merge(bus_group, on=["state", "district", "city"], how="left")
    frame = frame.merge(util_group, on=["state", "district", "lea_id"], how="left")
    frame = frame.merge(county_group, on=["state", "district", "lea_id"], how="left")
    frame = frame.merge(congress_group, on=["state", "district", "lea_id"], how="left")

    numeric_fill = {
        "bus_rows": 0,
        "bus_oems": 0,
        "funding_sources": 0,
        "charging_companies": 0,
        "operating_bus_rows": 0,
        "delivered_bus_rows": 0,
        "utility_count": 0,
        "utility_mentions": 0,
        "county_count": 1,
        "congressional_count": 1,
    }
    for col, default in numeric_fill.items():
        if col in frame.columns:
            frame[col] = pd.to_numeric(frame[col], errors="coerce").fillna(default)

    frame["adoption_gap"] = (100 - frame["esb_adoption_rate"].fillna(0)).clip(lower=0, upper=100)
    frame["operating_gap"] = (100 - frame["operating_rate"].fillna(0)).clip(lower=0, upper=100)
    frame["fleet_scale_log"] = np.log1p(frame["total_buses"].fillna(0).clip(lower=0))

    frame["need_component"] = pd.concat(
        [
            _minmax(frame.get("pm25", pd.Series(index=frame.index, dtype=float))),
            _minmax(frame.get("pct_low_income", pd.Series(index=frame.index, dtype=float))),
            _minmax(frame.get("free_lunch_pct", pd.Series(index=frame.index, dtype=float))),
            _minmax(frame.get("poverty_pct", pd.Series(index=frame.index, dtype=float))),
            _minmax(frame.get("pct_disability", pd.Series(index=frame.index, dtype=float))),
        ],
        axis=1,
    ).mean(axis=1)

    frame["transition_gap_component"] = pd.concat(
        [
            _minmax(frame["adoption_gap"]),
            _minmax(frame["operating_gap"]),
            _minmax(frame["funding_sources"]),
        ],
        axis=1,
    ).mean(axis=1)

    frame["scale_component"] = _minmax(frame["fleet_scale_log"])

    frame["complexity_component"] = pd.concat(
        [
            _minmax(frame["utility_count"]),
            _minmax(frame["county_count"]),
            _minmax(frame["congressional_count"]),
        ],
        axis=1,
    ).mean(axis=1)

    frame["priority_score"] = 100 * (
        weights.need * frame["need_component"]
        + weights.transition_gap * frame["transition_gap_component"]
        + weights.scale * frame["scale_component"]
        + weights.complexity * frame["complexity_component"]
    )

    readiness_component = pd.concat(
        [
            _minmax(frame["delivered_bus_rows"]),
            _minmax(frame["operating_bus_rows"]),
            _minmax(frame["charging_companies"]),
            1 - frame["complexity_component"],
        ],
        axis=1,
    ).mean(axis=1)

    frame["quick_win_score"] = 100 * (
        0.35 * frame["need_component"]
        + 0.25 * _minmax(frame["scale_component"])
        + 0.25 * _minmax(frame["adoption_gap"])
        + 0.15 * readiness_component
    )

    frame["priority_score"] = frame["priority_score"].round(2)
    frame["quick_win_score"] = frame["quick_win_score"].round(2)
    frame["priority_tier"] = _bucket(frame["priority_score"], ["Watch", "Build", "Accelerate", "Critical"])
    frame["quick_win_tier"] = _bucket(frame["quick_win_score"], ["Backlog", "Ready", "Strong", "Immediate"])

    frame["epa_priority_flag"] = _yes_no_to_float(frame.get("epa_2023_priority", pd.Series(index=frame.index))).astype(int)
    frame["arp_eligible_flag"] = _yes_no_to_float(frame.get("arp_eligible", pd.Series(index=frame.index))).astype(int)
    frame["wri_pod_flag"] = _yes_no_to_float(frame.get("wri_pod", pd.Series(index=frame.index))).astype(int)

    frame["decision_segment"] = np.select(
        [
            (frame["priority_score"] >= frame["priority_score"].quantile(0.75))
            & (frame["quick_win_score"] >= frame["quick_win_score"].quantile(0.75)),
            (frame["priority_score"] >= frame["priority_score"].quantile(0.75)),
            (frame["quick_win_score"] >= frame["quick_win_score"].quantile(0.75)),
        ],
        [
            "Act now",
            "High need, harder execution",
            "Fast-track candidate",
        ],
        default="Monitor",
    )

    return frame


def build_state_decision_rollup(frame: pd.DataFrame) -> pd.DataFrame:
    grouped = (
        frame.groupby("state", dropna=False)
        .agg(
            districts=("district", "count"),
            total_buses=("total_buses", "sum"),
            committed_esb=("committed_esb", "sum"),
            avg_adoption=("esb_adoption_rate", "mean"),
            avg_priority=("priority_score", "mean"),
            avg_quick_win=("quick_win_score", "mean"),
            critical_share=("priority_tier", lambda s: (s == "Critical").mean() * 100),
            act_now_share=("decision_segment", lambda s: (s == "Act now").mean() * 100),
        )
        .reset_index()
    )
    grouped["adoption_pct"] = _safe_share(grouped["committed_esb"], grouped["total_buses"]).mul(100)
    grouped = grouped.sort_values(["avg_priority", "act_now_share"], ascending=False)
    return grouped


def methodology_table(weights: ScoreWeights | None = None) -> pd.DataFrame:
    weights = weights or ScoreWeights()
    return pd.DataFrame(
        [
            ["Need", f"{weights.need * 100:.0f}%", "PM2.5, low-income share, lunch-based disadvantage, poverty, disability", "Higher = stronger public-health and equity exposure"],
            ["Transition gap", f"{weights.transition_gap * 100:.0f}%", "Low ESB adoption, low operating conversion, fragmented funding", "Higher = bigger distance between need and realized transition"],
            ["Scale", f"{weights.scale * 100:.0f}%", "Fleet size (log-normalized)", "Larger fleets move more children and create larger transition leverage"],
            ["Complexity", f"{weights.complexity * 100:.0f}%", "Utilities, county span, congressional span", "Higher = harder coordination and implementation burden"],
        ],
        columns=["Component", "Weight", "Inputs", "Why it exists"],
    )
