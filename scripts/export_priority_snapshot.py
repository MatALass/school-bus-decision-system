"""Export V5 decision-engine outputs to CSV for portfolio/demo use."""

from __future__ import annotations

from pathlib import Path
import sys

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.data.decision import build_decision_dataset, build_state_decision_rollup
from src.data.processor import clean_bus, clean_district
from src.school_bus_dashboard.config import RAW_DATA_FILE

OUT_DIR = ROOT / "data" / "processed"


def main() -> None:
    district_df = clean_district(pd.read_excel(RAW_DATA_FILE, sheet_name="1. District-level data"))
    bus_df = clean_bus(pd.read_excel(RAW_DATA_FILE, sheet_name="2. Bus-level data"))
    utilities_df = pd.read_excel(RAW_DATA_FILE, sheet_name="4. Utilities")
    counties_df = pd.read_excel(RAW_DATA_FILE, sheet_name="5. Counties")
    congress_df = pd.read_excel(RAW_DATA_FILE, sheet_name="6. Congressional districts")

    decision_df = build_decision_dataset(
        district_df=district_df,
        bus_df=bus_df,
        utilities_df=utilities_df,
        counties_df=counties_df,
        congress_df=congress_df,
    )
    state_df = build_state_decision_rollup(decision_df)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    decision_df.sort_values(["priority_score", "quick_win_score"], ascending=False).to_csv(
        OUT_DIR / "district_priority_snapshot.csv", index=False
    )
    state_df.to_csv(OUT_DIR / "state_priority_snapshot.csv", index=False)
    print(f"Exported: {OUT_DIR / 'district_priority_snapshot.csv'}")
    print(f"Exported: {OUT_DIR / 'state_priority_snapshot.csv'}")


if __name__ == "__main__":
    main()
