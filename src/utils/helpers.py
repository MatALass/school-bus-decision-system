"""
Shared utility functions (formatting, filtering, state abbreviations).
"""

import pandas as pd

# US state name → 2-letter abbreviation mapping
STATE_ABBR = {
    "ALABAMA": "AL", "ALASKA": "AK", "ARIZONA": "AZ", "ARKANSAS": "AR",
    "CALIFORNIA": "CA", "COLORADO": "CO", "CONNECTICUT": "CT", "DELAWARE": "DE",
    "DISTRICT OF COLUMBIA": "DC", "FLORIDA": "FL", "GEORGIA": "GA", "HAWAII": "HI",
    "IDAHO": "ID", "ILLINOIS": "IL", "INDIANA": "IN", "IOWA": "IA", "KANSAS": "KS",
    "KENTUCKY": "KY", "LOUISIANA": "LA", "MAINE": "ME", "MARYLAND": "MD",
    "MASSACHUSETTS": "MA", "MICHIGAN": "MI", "MINNESOTA": "MN", "MISSISSIPPI": "MS",
    "MISSOURI": "MO", "MONTANA": "MT", "NEBRASKA": "NE", "NEVADA": "NV",
    "NEW HAMPSHIRE": "NH", "NEW JERSEY": "NJ", "NEW MEXICO": "NM", "NEW YORK": "NY",
    "NORTH CAROLINA": "NC", "NORTH DAKOTA": "ND", "OHIO": "OH", "OKLAHOMA": "OK",
    "OREGON": "OR", "PENNSYLVANIA": "PA", "RHODE ISLAND": "RI",
    "SOUTH CAROLINA": "SC", "SOUTH DAKOTA": "SD", "TENNESSEE": "TN", "TEXAS": "TX",
    "UTAH": "UT", "VERMONT": "VT", "VIRGINIA": "VA", "WASHINGTON": "WA",
    "WEST VIRGINIA": "WV", "WISCONSIN": "WI", "WYOMING": "WY",
    "AMERICAN SAMOA": "AS", "GUAM": "GU", "NORTHERN MARIANA ISLANDS": "MP",
    "PUERTO RICO": "PR", "VIRGIN ISLANDS": "VI",
}


def add_state_abbr(df: pd.DataFrame, state_col: str = "state") -> pd.DataFrame:
    df = df.copy()
    df["state_abbr"] = df[state_col].map(STATE_ABBR)
    return df


def fmt_pct(val: float, decimals: int = 1) -> str:
    if pd.isna(val):
        return "N/A"
    return f"{val:.{decimals}f}%"


def fmt_dollar(val: float) -> str:
    if pd.isna(val):
        return "N/A"
    if val >= 1_000_000:
        return f"${val / 1_000_000:.1f}M"
    if val >= 1_000:
        return f"${val / 1_000:.0f}k"
    return f"${val:.0f}"


def fmt_number(val: float) -> str:
    if pd.isna(val):
        return "N/A"
    return f"{int(val):,}"


def filter_by_state_city(df: pd.DataFrame, state: str, city: str) -> pd.DataFrame:
    return df[
        (df["state"].str.upper() == state.upper()) &
        (df["city"].str.lower() == city.lower())
    ]
