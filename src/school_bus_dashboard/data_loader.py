from __future__ import annotations

from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]
RAW_DATA_PATH = PROJECT_ROOT / "data" / "raw" / "data.xlsx"

TARGET_SHEET_NAME = "1. District-level data"

RAW_TO_STANDARD_COLUMNS = {
    "0a. Has committed ESBs?": "has_committed_esbs",
    "1a. State": "state_code",
    "1b. Local Education Agency (LEA) or entity name": "district",
    "1c. LEA ID": "district_id",
    "1d. Street address 1": "street_address_1",
    "1e. Street address 2": "street_address_2",
    "1f. City": "city",
    "1g. State": "state",
    "1h. ZIP code": "zip_code",
    "1i. Website": "website",
    "1j. Has LEA ID?": "has_lea_id",
    "1k. LEA type (number)": "lea_type_number",
    "1l. LEA type (name)": "lea_type_name",
    "1m. Supervisory union LEA ID": "supervisory_union_lea_id",
    "1n. Locale (full number)": "locale_full_number",
    "1o. Locale broad type (number)": "locale_broad_type_number",
    "1p. Locale broad type (name)": "locale_broad_type_name",
    "1q. Census Region": "census_region",
    "1r. Census Division": "census_division",
    "1s. Latitude": "latitude",
    "1t. Longitude": "longitude",
    "2a. Total number of buses": "total_buses",
    "2b. Contractor used for some or all of buses?": "contractor_used",
    "3a. Number of ESBs committed": "electric_buses",
    "3b. Number of delivered or operating ESBs": "delivered_or_operating_esbs",
    "3c. Number of ESBs awarded": "esbs_awarded",
    "3d. Number of ESBs ordered": "esbs_ordered",
    "3e. Number of ESBs delivered": "esbs_delivered",
    "3f. Number of ESBs operating": "esbs_operating",
    "3g. Number of batches": "number_of_batches",
    "3i. Percent of fleet that is electric": "fleet_electric_pct",
    "3j. Government agency involved (non-funding)": "government_agency_involved",
    "3k. Utility/energy company involved 1": "utility_company_1",
    "3k. Utility/energy company involved 2": "utility_company_2",
    "3k. Utility/energy company involved 3": "utility_company_3",
    "3l. Other groups involved 1": "other_group_1",
    "3l. Other groups involved 2": "other_group_2",
    "3l. Other groups involved 3": "other_group_3",
    "3m. Other notes": "other_notes",
    "4a. Tribal school district?": "tribal_school_district",
    "4b. Number of students in district": "student_count",
    "4c. Number of schools in district": "school_count",
    "4d. Percentage of schools in district that are Title I schoolwide eligible": "title_i_schoolwide_pct",
    "4e. Percentage of students in district eligible for free or reduced price lunch": "free_or_reduced_lunch_pct",
    "4f. Median household income": "median_income",
    "4g. Percent of population below the poverty level": "poverty_pct",
    "4h. Percent one race: White": "pct_one_race_white",
    "4i. Percent race alone or multiracial: White": "pct_white_any",
    "4j. Percent one race: Black or African American": "pct_one_race_black",
    "4k. Percent race alone or multiracial: Black or African American": "pct_black_any",
    "4l. Percent one race: American Indian and Alaska Native": "pct_one_race_native",
    "4m. Percent race alone or multiracial: American Indian and Alaska Native": "pct_native_any",
    "4n. Percent one race: Asian": "pct_one_race_asian",
    "4o. Percent race alone or multiracial: Asian": "pct_asian_any",
    "4p. Percent one race: Native Hawaiian and Other Pacific Islander": "pct_one_race_pacific",
    "4q. Percent race alone or multiracial: Native Hawaiian and Other Pacific Islander": "pct_pacific_any",
    "4r. Percent one race: some other race": "pct_one_race_other",
    "4s. Percent race alone or multiracial: Some other race": "pct_other_any",
    "4t. Percent two or more races": "pct_two_or_more_races",
    "4u. Percent Hispanic or Latino (of any race)": "pct_hispanic_or_latino",
    "5a. EPA Region": "epa_region",
    "5b. Percent non-white and/or Hispanic": "pct_non_white_or_hispanic",
    "5c. Quartile: percent non-white and/or Hispanic": "quartile_non_white_or_hispanic",
    "5d. Percent low-income (200% of federal poverty level)": "low_income_pct",
    "5e. Quartile: percent low-income": "quartile_low_income",
    "5f. PM2.5 concentration": "pm25",
    "5g. Quartile: PM2.5 concentration": "quartile_pm25",
    "5h. Ozone concentration": "ozone",
    "5i. Quartile: ozone concentration": "quartile_ozone",
    "5j. Percent of school children with a disability": "children_disability_pct",
    "5k. Quartile: percent of school children with a disability": "quartile_children_disability",
    "5l. Average rate of asthma among adults aged 18 and older": "adult_asthma_rate",
    "5m. Quartile: average rate of asthma": "quartile_asthma",
    "5n. Qualified for American Rescue Plan funding?": "qualified_arp_funding",
    "5o. EPA 2022 Clean School Bus Rebate Program prioritized school district?": "epa_2022_priority_district",
    "5p. EPA 2023 Clean School Bus Grant & Rebate Programs prioritized school district?": "epa_2023_priority_district",
    "5q. WRI Priority Outreach District (POD)?": "wri_priority_outreach_district",
    "6a. Has any expression of interest in ESBs?": "has_expression_of_interest",
    "6b. ARP 2021 waitlist position": "arp_2021_waitlist_position",
    "6c. DERA school bus rebates 2020 waitlist position": "dera_2020_waitlist_position",
    "6d. DERA school bus rebates 2021 waitlist position": "dera_2021_waitlist_position",
    "6e. Applied for ESB funding but not awarded": "applied_not_awarded",
}

REQUIRED_STANDARD_COLUMNS = [
    "district",
    "city",
    "state",
    "total_buses",
    "electric_buses",
    "pm25",
    "low_income_pct",
]


def _normalize_column_name(column: str) -> str:
    return " ".join(str(column).strip().split())


def _coerce_numeric(df: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    for column in columns:
        if column in df.columns:
            df[column] = pd.to_numeric(df[column], errors="coerce")
    return df


def load_data(path: str | Path | None = None) -> pd.DataFrame:
    data_path = Path(path) if path is not None else RAW_DATA_PATH

    if not data_path.exists():
        raise FileNotFoundError(
            f"Dataset not found at: {data_path}\n"
            "Expected location: data/raw/data.xlsx"
        )

    raw_df = pd.read_excel(data_path, sheet_name=TARGET_SHEET_NAME)
    raw_df.columns = [_normalize_column_name(col) for col in raw_df.columns]

    renamed_df = raw_df.rename(columns=RAW_TO_STANDARD_COLUMNS)

    missing_columns = [
        column for column in REQUIRED_STANDARD_COLUMNS if column not in renamed_df.columns
    ]
    if missing_columns:
        raise ValueError(
            "The dataset could not be standardized correctly.\n"
            f"Missing required columns: {missing_columns}\n"
            f"Available columns: {list(renamed_df.columns)}"
        )

    numeric_columns = [
        "latitude",
        "longitude",
        "total_buses",
        "electric_buses",
        "delivered_or_operating_esbs",
        "esbs_awarded",
        "esbs_ordered",
        "esbs_delivered",
        "esbs_operating",
        "number_of_batches",
        "fleet_electric_pct",
        "student_count",
        "school_count",
        "title_i_schoolwide_pct",
        "free_or_reduced_lunch_pct",
        "median_income",
        "poverty_pct",
        "pct_non_white_or_hispanic",
        "low_income_pct",
        "pm25",
        "ozone",
        "children_disability_pct",
        "adult_asthma_rate",
        "arp_2021_waitlist_position",
        "dera_2020_waitlist_position",
        "dera_2021_waitlist_position",
    ]
    renamed_df = _coerce_numeric(renamed_df, numeric_columns)

    text_columns = ["district", "city", "state", "state_code", "district_id", "zip_code", "website"]
    for column in text_columns:
        if column in renamed_df.columns:
            renamed_df[column] = renamed_df[column].astype("string").str.strip()

    return renamed_df