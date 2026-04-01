"""
Data loading and caching layer.
All raw Excel reads happen here — nothing else should touch the file directly.
"""

import pandas as pd
import streamlit as st
from pathlib import Path

from src.school_bus_dashboard.config import RAW_DATA_FILE


@st.cache_data(show_spinner=False)
def load_district() -> pd.DataFrame:
    return pd.read_excel(RAW_DATA_FILE, sheet_name="1. District-level data")


@st.cache_data(show_spinner=False)
def load_bus() -> pd.DataFrame:
    return pd.read_excel(RAW_DATA_FILE, sheet_name="2. Bus-level data")


@st.cache_data(show_spinner=False)
def load_state() -> pd.DataFrame:
    return pd.read_excel(RAW_DATA_FILE, sheet_name="3. State-level data")


@st.cache_data(show_spinner=False)
def load_utilities() -> pd.DataFrame:
    return pd.read_excel(RAW_DATA_FILE, sheet_name="4. Utilities")


@st.cache_data(show_spinner=False)
def load_counties() -> pd.DataFrame:
    return pd.read_excel(RAW_DATA_FILE, sheet_name="5. Counties")


@st.cache_data(show_spinner=False)
def load_congressional() -> pd.DataFrame:
    return pd.read_excel(RAW_DATA_FILE, sheet_name="6. Congressional districts")
