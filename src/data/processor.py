"""
Data transformation and feature engineering.
Keeps all business logic in one place, separate from UI and loading.
"""

import pandas as pd
import numpy as np


# ---------------------------------------------------------------------------
# District-level clean & enrich
# ---------------------------------------------------------------------------

DISTRICT_RENAME = {
    "0a. Has committed ESBs?": "has_esb",
    "1a. State": "state",
    "1b. Local Education Agency (LEA) or entity name": "district",
    "1c. LEA ID": "lea_id",
    "1f. City": "city",
    "1p. Locale broad type (name)": "locale_type",
    "1q. Census Region": "census_region",
    "1s. Latitude": "latitude",
    "1t. Longitude ": "longitude",
    "2a. Total number of buses": "total_buses",
    "3a. Number of ESBs committed ": "committed_esb",
    "3b. Number of delivered or operating ESBs": "delivered_esb",
    "3f. Number of ESBs operating": "operating_esb",
    "3i. Percent of fleet that is electric": "pct_electric",
    "4b. Number of students in district": "num_students",
    "4c. Number of schools in district": "num_schools",
    "4d. Percentage of schools in district that are Title I schoolwide eligible": "title1_pct",
    "4e. Percentage of students in district eligible for free or reduced price lunch": "free_lunch_pct",
    "4f. Median household income": "median_income",
    "4g. Percent of population below the poverty level": "poverty_pct",
    "4h. Percent one race: White ": "pct_white",
    "4j. Percent one race: Black or African American ": "pct_black",
    "4n. Percent one race: Asian ": "pct_asian",
    "4u. Percent Hispanic or Latino (of any race) ": "pct_hispanic",
    "5b. Percent non-white and/or Hispanic": "pct_nonwhite_hispanic",
    "5d. Percent low-income (200% of federal poverty level)": "pct_low_income",
    "5f. PM2.5 concentration": "pm25",
    "5h. Ozone concentration": "ozone",
    "5j. Percent of school children with a disability": "pct_disability",
    "5l. Average rate of asthma among adults aged 18 and older": "asthma_rate",
    "5n. Qualified for American Rescue Plan funding? ": "arp_eligible",
    "5o. EPA 2022 Clean School Bus Rebate Program prioritized school district?": "epa_2022_priority",
    "5p. EPA 2023 Clean School Bus Grant & Rebate Programs prioritized school district?": "epa_2023_priority",
    "5q. WRI Priority Outreach District (POD)?": "wri_pod",
}


def clean_district(df_raw: pd.DataFrame) -> pd.DataFrame:
    cols = {k: v for k, v in DISTRICT_RENAME.items() if k in df_raw.columns}
    df = df_raw[list(cols.keys())].rename(columns=cols).copy()

    # Percentage fix (0-1 → 0-100)
    pct_cols = [
        "free_lunch_pct", "title1_pct", "poverty_pct",
        "pct_white", "pct_black", "pct_asian", "pct_hispanic",
        "pct_nonwhite_hispanic", "pct_low_income", "pct_disability", "asthma_rate",
    ]
    for c in pct_cols:
        if c in df.columns and df[c].max() <= 1.5:
            df[c] = df[c] * 100

    # Derived features
    df["esb_adoption_rate"] = (
        df["committed_esb"] / df["total_buses"].replace(0, np.nan) * 100
    ).clip(0, 100)

    df["operating_rate"] = (
        df["operating_esb"] / df["committed_esb"].replace(0, np.nan) * 100
    ).clip(0, 100)

    df["buses_per_student"] = df["total_buses"] / df["num_students"].replace(0, np.nan)

    # Equity score (composite, higher = more disadvantaged)
    # Normalized 0–100 per axis then averaged
    for col in ["pct_nonwhite_hispanic", "pct_low_income", "pm25"]:
        if col in df.columns:
            mn, mx = df[col].min(), df[col].max()
            df[f"{col}_norm"] = (df[col] - mn) / (mx - mn + 1e-9) * 100

    equity_components = [
        c for c in ["pct_nonwhite_hispanic_norm", "pct_low_income_norm", "pm25_norm"]
        if c in df.columns
    ]
    if equity_components:
        df["equity_score"] = df[equity_components].mean(axis=1)

    df["state"] = df["state"].str.upper().str.strip()
    df["city"] = df["city"].str.strip()

    return df


# ---------------------------------------------------------------------------
# Bus-level clean
# ---------------------------------------------------------------------------

BUS_RENAME = {
    "1a. State": "state",
    "1b. LEA or entity name": "district",
    "1f. City": "city",
    "3a. Number of ESBs committed ": "committed_esb",
    "3n. Current status of bus": "status",
    "3p. Quarter awarded": "quarter_awarded",
    "3q. Quarter ordered": "quarter_ordered",
    "3r. Quarter delivered": "quarter_delivered",
    "3s. Quarter first operating": "quarter_operating",
    "3t. Bus OEM": "oem",
    "3u. Electric powertrain manufacturer": "powertrain_mfr",
    "3v. Model": "model",
    "3w. Type": "bus_type",
    "3z. Funding source 1": "funding_source",
    "3ab. Dollar amount toward bus": "bus_cost",
    "3ac. Charging company": "charging_company",
    "3ae. Dollar amount toward charger": "charger_cost",
}

BUS_TYPE_LABELS = {"A": "Type A (Mini)", "B": "Type B (Small)", "C": "Type C (Standard)", "D": "Type D (Large)"}


def clean_bus(df_raw: pd.DataFrame) -> pd.DataFrame:
    cols = {k: v for k, v in BUS_RENAME.items() if k in df_raw.columns}
    df = df_raw[list(cols.keys())].rename(columns=cols).copy()
    df["state"] = df["state"].str.upper().str.strip()
    df["bus_type_label"] = df["bus_type"].map(BUS_TYPE_LABELS).fillna(df["bus_type"])

    # Parse year from quarter strings like "2022 Q3"
    df["year_awarded"] = (
        df["quarter_awarded"]
        .astype(str)
        .str.extract(r"(\d{4})", expand=False)
        .astype(float)
    )

    df["total_cost"] = df["bus_cost"].fillna(0) + df["charger_cost"].fillna(0)
    df["funding_category"] = df["funding_source"].str.slice(0, 40)

    return df


# ---------------------------------------------------------------------------
# State-level clean
# ---------------------------------------------------------------------------

STATE_RENAME = {
    "1a. State": "state",
    "2a. Total number of school buses (WRI 2024)": "total_buses",
    "3a. Number of committed ESBs": "committed_esb",
    "3i. Average of percentages of committed ESBs (Atlas, SBF, FHWA, WRI)": "avg_pct_committed",
    "8a. Approximate total number of students riding ESBs": "students_on_esb",
    "8b. Number of persons, mode to school: school bus": "bus_riders",
    "8c. Percent of persons, mode to school: school bus": "pct_bus_riders",
}


def clean_state(df_raw: pd.DataFrame) -> pd.DataFrame:
    cols = {k: v for k, v in STATE_RENAME.items() if k in df_raw.columns}
    df = df_raw[list(cols.keys())].rename(columns=cols).copy()
    df["state"] = df["state"].str.upper().str.strip()
    df["avg_pct_committed_pct"] = df["avg_pct_committed"] * 100
    return df
