from __future__ import annotations

REQUIRED_STANDARD_COLUMNS = [
    "district",
    "city",
    "state",
    "latitude",
    "longitude",
    "total_buses",
    "committed_esb",
    "free_lunch_pct",
    "pm25",
    "median_income",
]

LEGACY_EXCEL_MAPPING = {
    "1b. Local Education Agency (LEA) or entity name": "district",
    "1f. City": "city",
    "1a. State": "state",
    "1s. Latitude": "latitude",
    "1t. Longitude ": "longitude",
    "2a. Total number of buses": "total_buses",
    "3a. Number of ESBs committed ": "committed_esb",
    "4e. Percentage of students in district eligible for free or reduced price lunch": "free_lunch_pct",
    "5f. PM2.5 concentration": "pm25",
    "4f. Median household income": "median_income",
}

STANDARD_COLUMN_DESCRIPTIONS = {
    "district": "District or local education agency name",
    "city": "City of the district",
    "state": "State name",
    "latitude": "Latitude coordinate",
    "longitude": "Longitude coordinate",
    "total_buses": "Total school bus fleet size",
    "committed_esb": "Number of committed electric school buses",
    "free_lunch_pct": "Share of students eligible for free/reduced lunch, in percent",
    "pm25": "PM2.5 concentration",
    "median_income": "Median household income in USD",
}
