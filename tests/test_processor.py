from __future__ import annotations

import pandas as pd

from src.data.processor import clean_bus, clean_district, clean_state


def test_clean_district_normalizes_percentages_and_builds_rates() -> None:
    raw = pd.DataFrame(
        {
            "1a. State": [" ca "],
            "1b. Local Education Agency (LEA) or entity name": ["Demo District"],
            "1c. LEA ID": ["001"],
            "1f. City": [" Los Angeles "],
            "2a. Total number of buses": [100],
            "3a. Number of ESBs committed ": [20],
            "3f. Number of ESBs operating": [10],
            "4b. Number of students in district": [1000],
            "4d. Percentage of schools in district that are Title I schoolwide eligible": [0.4],
            "4e. Percentage of students in district eligible for free or reduced price lunch": [0.5],
            "4g. Percent of population below the poverty level": [0.2],
            "4h. Percent one race: White ": [0.3],
            "4j. Percent one race: Black or African American ": [0.2],
            "4n. Percent one race: Asian ": [0.1],
            "4u. Percent Hispanic or Latino (of any race) ": [0.4],
            "5b. Percent non-white and/or Hispanic": [0.7],
            "5d. Percent low-income (200% of federal poverty level)": [0.6],
            "5f. PM2.5 concentration": [12.0],
            "5j. Percent of school children with a disability": [0.08],
            "5l. Average rate of asthma among adults aged 18 and older": [0.11],
        }
    )

    cleaned = clean_district(raw)
    row = cleaned.iloc[0]

    assert row["state"] == "CA"
    assert row["city"] == "Los Angeles"
    assert row["free_lunch_pct"] == 50.0
    assert row["title1_pct"] == 40.0
    assert row["pct_low_income"] == 60.0
    assert row["esb_adoption_rate"] == 20.0
    assert row["operating_rate"] == 50.0
    assert row["buses_per_student"] == 0.1
    assert "equity_score" in cleaned.columns


def test_clean_district_handles_missing_optional_columns_without_crashing() -> None:
    raw = pd.DataFrame(
        {
            "1a. State": ["tx"],
            "1f. City": [" Houston "],
            "2a. Total number of buses": [0],
            "3a. Number of ESBs committed ": [0],
        }
    )

    cleaned = clean_district(raw)
    row = cleaned.iloc[0]

    assert row["state"] == "TX"
    assert row["city"] == "Houston"
    assert pd.isna(row["esb_adoption_rate"])
    assert pd.isna(row["operating_rate"])
    assert pd.isna(row["buses_per_student"])


def test_clean_bus_builds_cost_and_year_fields() -> None:
    raw = pd.DataFrame(
        {
            "1a. State": [" ny "],
            "1b. LEA or entity name": ["District A"],
            "1f. City": ["Albany"],
            "3n. Current status of bus": ["Operating"],
            "3p. Quarter awarded": ["2024 Q3"],
            "3w. Type": ["C"],
            "3z. Funding source 1": ["EPA Clean School Bus Program"],
            "3ab. Dollar amount toward bus": [250000],
            "3ac. Charging company": ["ChargeCo"],
            "3ae. Dollar amount toward charger": [50000],
        }
    )

    cleaned = clean_bus(raw)
    row = cleaned.iloc[0]

    assert row["state"] == "NY"
    assert row["bus_type_label"] == "Type C (Standard)"
    assert row["year_awarded"] == 2024.0
    assert row["total_cost"] == 300000
    assert row["funding_category"].startswith("EPA Clean School Bus")


def test_clean_bus_handles_missing_optional_columns() -> None:
    raw = pd.DataFrame(
        {
            "1a. State": ["ca"],
            "1b. LEA or entity name": ["District B"],
        }
    )

    cleaned = clean_bus(raw)
    row = cleaned.iloc[0]

    assert row["state"] == "CA"
    assert pd.isna(row["year_awarded"])
    assert row["total_cost"] == 0


def test_clean_state_uppercases_and_converts_percentage() -> None:
    raw = pd.DataFrame(
        {
            "1a. State": [" ca "],
            "3i. Average of percentages of committed ESBs (Atlas, SBF, FHWA, WRI)": [0.12],
        }
    )

    cleaned = clean_state(raw)
    row = cleaned.iloc[0]

    assert row["state"] == "CA"
    assert row["avg_pct_committed_pct"] == 12.0
