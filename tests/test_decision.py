from __future__ import annotations

import pandas as pd

from src.data.decision import (
    ScoreWeights,
    _bucket,
    _minmax,
    _safe_share,
    _utility_long_frame,
    _yes_no_to_float,
    build_decision_dataset,
    build_state_decision_rollup,
    methodology_table,
    score_profile_catalog,
)


def _district_frame() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "state": ["CA", "TX", "NY"],
            "district": ["A", "B", "C"],
            "city": ["Los Angeles", "Houston", "Albany"],
            "lea_id": ["1", "2", "3"],
            "esb_adoption_rate": [5.0, 30.0, 60.0],
            "operating_rate": [10.0, 40.0, 70.0],
            "total_buses": [100, 200, 50],
            "committed_esb": [5, 60, 30],
            "pm25": [12.0, 9.0, 7.0],
            "pct_low_income": [80.0, 50.0, 25.0],
            "free_lunch_pct": [70.0, 40.0, 20.0],
            "poverty_pct": [25.0, 15.0, 10.0],
            "pct_disability": [12.0, 10.0, 8.0],
            "arp_eligible": ["Yes", "No", "Yes"],
            "epa_2023_priority": ["Yes", "No", "No"],
            "wri_pod": ["No", "Yes", "No"],
        }
    )


def _bus_frame() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "state": ["CA", "CA", "TX", "NY"],
            "district": ["A", "A", "B", "C"],
            "city": ["Los Angeles", "Los Angeles", "Houston", "Albany"],
            "oem": ["OEM1", "OEM2", "OEM1", "OEM3"],
            "funding_source": ["EPA", "State", "EPA", "Utility"],
            "charging_company": ["Charge1", "Charge2", "Charge1", "Charge3"],
            "total_cost": [100.0, 120.0, 90.0, 80.0],
            "status": ["Operating", "Delivered", "Awarded", "Operating"],
        }
    )


def _utilities_frame() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "1a. State": ["CA", "TX", "NY"],
            "1b. LEA name": ["A", "B", "C"],
            "1c. LEA ID": ["1", "2", "3"],
            "9a. Utility name 1": ["Utility A", "Utility B", "Utility C"],
            "9a. Utility name 2": ["Utility A2", None, None],
        }
    )


def _counties_frame() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "1a. State": ["CA", "TX", "NY"],
            "1b. LEA name": ["A", "B", "C"],
            "1c. LEA ID": ["1", "2", "3"],
            "10c. Number of counties in LEA": [2, 1, 1],
        }
    )


def _congress_frame() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "1a. State": ["CA", "TX", "NY"],
            "1b. LEA name": ["A", "B", "C"],
            "1c. LEA ID": ["1", "2", "3"],
            "11c. Number of congressional districts in LEA": [2, 1, 1],
        }
    )


def test_score_profiles_are_complete_and_sum_to_one() -> None:
    profiles = score_profile_catalog()

    assert set(profiles) == {"Balanced", "Equity first", "Deployment first", "Scale first"}
    for weights in profiles.values():
        total = weights.need + weights.transition_gap + weights.scale + weights.complexity
        assert round(total, 10) == 1.0


def test_internal_helpers_handle_edge_cases() -> None:
    assert _minmax(pd.Series([5.0, 5.0, 5.0])).tolist() == [0.0, 0.0, 0.0]
    assert _safe_share(pd.Series([1, 2]), pd.Series([0, 4])).isna().tolist() == [True, False]
    assert _yes_no_to_float(pd.Series(["Yes", "no", "TRUE", "0", None])).tolist() == [1.0, 0.0, 1.0, 0.0, 0.0]


def test_utility_long_frame_excludes_blank_and_missing_names() -> None:
    raw = pd.DataFrame(
        {
            "1a. State": ["CA"],
            "1b. LEA name": ["A"],
            "1c. LEA ID": ["1"],
            "9a. Utility name 1": ["Utility A"],
            "9a. Utility name 2": [None],
            "9a. Utility name 3": ["   "],
        }
    )

    long_df = _utility_long_frame(raw)

    assert len(long_df) == 1
    assert long_df.iloc[0]["utility_name"] == "Utility A"


def test_bucket_returns_consistent_label_for_constant_series() -> None:
    bucketed = _bucket(pd.Series([10.0, 10.0, 10.0]), ["Low", "Medium", "High", "Critical"])
    assert len(set(bucketed)) == 1
    assert bucketed.iloc[0] in {"Low", "Medium", "High", "Critical", "Unknown"}


def test_build_decision_dataset_outputs_expected_fields_and_ranges() -> None:
    decision_df = build_decision_dataset(
        district_df=_district_frame(),
        bus_df=_bus_frame(),
        utilities_df=_utilities_frame(),
        counties_df=_counties_frame(),
        congress_df=_congress_frame(),
        weights=ScoreWeights(),
    )

    assert len(decision_df) == 3
    assert decision_df["priority_score"].between(0, 100).all()
    assert decision_df["quick_win_score"].between(0, 100).all()
    assert set(decision_df["priority_tier"].dropna()) <= {"Watch", "Build", "Accelerate", "Critical", "Unknown"}
    assert set(decision_df["quick_win_tier"].dropna()) <= {"Backlog", "Ready", "Strong", "Immediate", "Unknown"}
    assert set(decision_df["decision_segment"].dropna()) <= {
        "Act now",
        "High need, harder execution",
        "Fast-track candidate",
        "Monitor",
    }
    assert {"epa_priority_flag", "arp_eligible_flag", "wri_pod_flag"}.issubset(decision_df.columns)


def test_higher_need_district_scores_above_lower_need_district() -> None:
    decision_df = build_decision_dataset(
        district_df=_district_frame(),
        bus_df=_bus_frame(),
        utilities_df=_utilities_frame(),
        counties_df=_counties_frame(),
        congress_df=_congress_frame(),
    )

    scores = decision_df.set_index("district")["priority_score"]
    assert scores["A"] > scores["C"]


def test_state_rollup_and_methodology_table_are_consistent() -> None:
    decision_df = build_decision_dataset(
        district_df=_district_frame(),
        bus_df=_bus_frame(),
        utilities_df=_utilities_frame(),
        counties_df=_counties_frame(),
        congress_df=_congress_frame(),
    )

    state_df = build_state_decision_rollup(decision_df)
    method_df = methodology_table()

    assert len(state_df) == 3
    assert state_df["adoption_pct"].between(0, 100).all()
    assert list(method_df.columns) == ["Component", "Weight", "Inputs", "Why it exists"]
    assert set(method_df["Component"]) == {"Need", "Transition gap", "Scale", "Complexity"}
