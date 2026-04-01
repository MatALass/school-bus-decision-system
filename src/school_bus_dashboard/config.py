from __future__ import annotations

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]

DATA_DIR = PROJECT_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
SAMPLE_DIR = DATA_DIR / "sample"
PROCESSED_DIR = DATA_DIR / "processed"
ASSETS_DIR = PROJECT_ROOT / "assets"

RAW_DATA_FILE = RAW_DIR / "data.xlsx"

DEFAULT_SAMPLE_FILE = SAMPLE_DIR / "sample_school_bus_data.csv"

DEFAULT_SHEET_NAME = "1. District-level data"