from __future__ import annotations

import pandas as pd


def preprocess_data(df: pd.DataFrame) -> pd.DataFrame:
    clean_df = df.copy()

    clean_df = clean_df.dropna(subset=["district", "city", "state"]).copy()

    clean_df["district"] = clean_df["district"].astype(str).str.strip()
    clean_df["city"] = clean_df["city"].astype(str).str.strip()
    clean_df["state"] = clean_df["state"].astype(str).str.strip()

    for column in [
        "total_buses",
        "electric_buses",
        "pm25",
        "low_income_pct",
        "median_income",
        "student_count",
        "poverty_pct",
        "fleet_electric_pct",
    ]:
        if column in clean_df.columns:
            clean_df[column] = pd.to_numeric(clean_df[column], errors="coerce")

    clean_df["total_buses"] = clean_df["total_buses"].fillna(0)
    clean_df["electric_buses"] = clean_df["electric_buses"].fillna(0)

    clean_df = clean_df[clean_df["total_buses"] >= 0].copy()
    clean_df = clean_df[clean_df["electric_buses"] >= 0].copy()

    clean_df = clean_df.drop_duplicates().reset_index(drop=True)

    return clean_df