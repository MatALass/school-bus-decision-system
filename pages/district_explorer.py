"""District explorer page."""

from pathlib import Path
import sys

import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st

sys.path.insert(0, str(Path(__file__).parents[1]))

from src.components.charts import bar_comparison, kpi_indicators, scatter_equity_adoption
from src.components.ui import explain_chart, page_story, section_intro
from src.data.loader import load_bus, load_counties, load_district
from src.data.processor import clean_bus, clean_district
from src.utils.helpers import filter_by_state_city, fmt_dollar, fmt_pct


def render() -> None:
    st.header("District explorer")
    section_intro(
        "This page moves from national averages to implementation reality on the ground. It is designed to benchmark one city against its state context and reveal whether local rollout is ahead, in line, or falling behind local need."
    )

    df = clean_district(load_district())
    bus_df = clean_bus(load_bus())
    counties_df = load_counties()

    with st.sidebar:
        st.subheader("Location filters")
        states = sorted(df["state"].dropna().unique())
        default_state_idx = states.index("CALIFORNIA") if "CALIFORNIA" in states else 0
        selected_state = st.selectbox("State", states, index=default_state_idx)

        cities = sorted(df[df["state"] == selected_state]["city"].dropna().unique())
        default_city = "Bakersfield" if "Bakersfield" in cities else cities[0]
        selected_city = st.selectbox("City", cities, index=cities.index(default_city))

    state_df = df[df["state"] == selected_state]
    city_df = filter_by_state_city(df, selected_state, selected_city)
    bus_city = bus_df[(bus_df["state"] == selected_state) & (bus_df["city"].str.lower() == selected_city.lower())]

    if city_df.empty:
        st.warning("No data found for this city.")
        return

    def agg(sub: pd.DataFrame, col: str) -> float:
        return sub[col].mean() if col in sub.columns else np.nan

    city_vals = {
        "esb_adoption_rate": city_df["esb_adoption_rate"].mean(),
        "pm25": city_df["pm25"].mean(),
        "median_income": city_df["median_income"].mean(),
        "free_lunch_pct": city_df["free_lunch_pct"].mean(),
        "equity_score": city_df["equity_score"].mean(),
    }
    state_vals = {k: agg(state_df, k) for k in city_vals}

    adoption_delta = city_vals["esb_adoption_rate"] - state_vals["esb_adoption_rate"]
    pm25_delta = city_vals["pm25"] - state_vals["pm25"]
    income_delta = city_vals["median_income"] - state_vals["median_income"]

    county_match = counties_df[
        (counties_df["1a. State"].astype(str).str.upper() == selected_state)
        & (counties_df["1b. LEA name"].isin(city_df["district"]))
    ]
    multi_county_share = (
        (county_match["10c. Number of counties in LEA"].fillna(0) > 1).mean() * 100
        if not county_match.empty
        else np.nan
    )

    page_story(
        kpi_title=f"Adoption gap for {selected_city} versus {selected_state.title()} average",
        kpi_value=fmt_pct(adoption_delta, 2),
        observation=(
            f"{selected_city} averages {city_vals['esb_adoption_rate']:.2f}% ESB adoption against {state_vals['esb_adoption_rate']:.2f}% statewide. "
            f"At the same time, PM2.5 is {pm25_delta:+.2f} µg/m³ versus the state average and median income is {fmt_dollar(income_delta)} from the state benchmark."
        ),
        implication=(
            "This is the type of local mismatch decision-makers care about: if a city faces dirtier air or higher social pressure but still underperforms on adoption, the problem is implementation alignment, not just funding scarcity in the abstract."
        ),
    )

    st.subheader(f"{selected_city}, {selected_state}")
    st.plotly_chart(kpi_indicators(city_vals, state_vals), width='stretch')
    explain_chart(
        "These indicators summarize the city's district profile and compare it directly with the state average on adoption, pollution, income, lunch-based disadvantage, and the composite equity score.",
        "This is the fast executive view. It tells you whether the city is behind on deployment, facing tougher conditions, or both at the same time.",
        preset="benchmark",
    )

    summary_cols = st.columns(4)
    summary_cols[0].metric("Districts in city view", f"{len(city_df):,}")
    summary_cols[1].metric("Committed ESBs", f"{int(city_df['committed_esb'].sum()):,}")
    summary_cols[2].metric("Operating ESBs", f"{int(city_df['operating_esb'].fillna(0).sum()):,}")
    summary_cols[3].metric("Multi-county LEAs", f"{multi_county_share:.1f}%" if not np.isnan(multi_county_share) else "N/A")

    geo_df = city_df.dropna(subset=["latitude", "longitude"])
    if not geo_df.empty:
        st.subheader("District map")
        fig_map = px.scatter_mapbox(
            geo_df,
            lat="latitude",
            lon="longitude",
            color="esb_adoption_rate",
            size=geo_df["committed_esb"].clip(lower=1),
            hover_name="district",
            hover_data={"committed_esb": True, "total_buses": True, "esb_adoption_rate": ":.1f", "pm25": ":.2f"},
            color_continuous_scale="YlGn",
            zoom=9,
            mapbox_style="carto-positron",
            labels={"esb_adoption_rate": "ESB adoption (%)"},
            template="plotly_white",
        )
        fig_map.update_layout(height=420, margin=dict(t=20, b=0))
        st.plotly_chart(fig_map, width='stretch')
        explain_chart(
            "The city does not behave as one block. The map shows where commitments are geographically concentrated and where districts remain effectively absent from the transition.",
            "This is often where the most useful story sits: not whether a city has some ESBs, but whether adoption is spatially broad or concentrated in a few pockets.",
            preset="pattern",
        )

    st.subheader(f"{selected_city} versus state average")
    tab1, tab2, tab3 = st.tabs(["ESB and air quality", "Economic profile", "Demographics"])

    with tab1:
        col1, col2 = st.columns(2)
        with col1:
            metrics = {
                "ESB adoption (%)": city_vals["esb_adoption_rate"],
                "PM2.5 (µg/m³)": city_vals["pm25"],
                "Ozone": city_df["ozone"].mean() if "ozone" in city_df else np.nan,
            }
            state_metrics = {
                "ESB adoption (%)": state_vals["esb_adoption_rate"],
                "PM2.5 (µg/m³)": state_vals["pm25"],
                "Ozone": state_df["ozone"].mean() if "ozone" in state_df else np.nan,
            }
            valid = [k for k in metrics if not np.isnan(metrics[k]) and not np.isnan(state_metrics[k])]
            if valid:
                st.plotly_chart(
                    bar_comparison({k: metrics[k] for k in valid}, {k: state_metrics[k] for k in valid}, selected_city, selected_state),
                    width='stretch',
                )
                explain_chart(
                    "This comparison puts local deployment next to local environmental burden. That makes it easy to see whether a more polluted city is also being served more aggressively by electrification.",
                    "A city that is dirtier than the state average but less electrified is a clear candidate for policy reprioritization or execution review.",
                    preset="focus",
                )

        with col2:
            state_scatter = df[df["state"] == selected_state]
            fig_sc = scatter_equity_adoption(
                state_scatter,
                "pm25",
                "esb_adoption_rate",
                "median_income",
                highlight_city_df=city_df,
                xlab="PM2.5 (µg/m³)",
                ylab="ESB adoption (%)",
            )
            fig_sc.update_layout(height=380, title=f"State distribution with {selected_city} highlighted")
            st.plotly_chart(fig_sc, width='stretch')
            explain_chart(
                f"The highlighted points show where {selected_city} sits inside the statewide distribution rather than in isolation.",
                "That benchmark matters more than raw local numbers. It shows whether the city is genuinely unusual or simply reflects the broader state pattern.",
                preset="reading",
            )

    with tab2:
        col1, col2 = st.columns(2)
        with col1:
            eco_m = {
                "Median income ($)": city_vals["median_income"],
                "Free lunch eligible (%)": city_vals["free_lunch_pct"],
                "Poverty rate (%)": city_df["poverty_pct"].mean() if "poverty_pct" in city_df else np.nan,
            }
            eco_s = {
                "Median income ($)": state_vals["median_income"],
                "Free lunch eligible (%)": state_vals["free_lunch_pct"],
                "Poverty rate (%)": state_df["poverty_pct"].mean() if "poverty_pct" in state_df else np.nan,
            }
            valid = [k for k in eco_m if not np.isnan(eco_m[k]) and not np.isnan(eco_s[k])]
            if valid:
                city_norm = {k: eco_m[k] / eco_s[k] * 100 for k in valid}
                state_norm = {k: 100.0 for k in valid}
                st.plotly_chart(bar_comparison(city_norm, state_norm, selected_city, "State baseline"), width='stretch')
                explain_chart(
                    "Indexing the city to a state baseline of 100 makes the socioeconomic profile immediately readable, even though the underlying units differ.",
                    "That is useful because rollout performance should be interpreted relative to local conditions. Underperformance is more concerning when the social burden is above the state baseline.",
                    preset="benchmark",
                )

        with col2:
            inc_df = city_df["median_income"].dropna()
            if len(inc_df) > 1:
                fig_inc = px.histogram(
                    inc_df,
                    nbins=20,
                    labels={"value": "Median income ($)", "count": "District count"},
                    template="plotly_white",
                )
                fig_inc.add_vline(x=inc_df.mean(), line_dash="dash", line_color="red", annotation_text=f"City average: ${inc_df.mean():,.0f}")
                fig_inc.update_layout(height=340, margin=dict(t=20, b=0))
                st.plotly_chart(fig_inc, width='stretch')
                explain_chart(
                    "The city average hides internal dispersion. This histogram shows whether the city is relatively homogeneous or contains very different district realities under the same city label.",
                    "That matters because a uniform city-wide policy is less defensible when district-level conditions are highly uneven.",
                    preset="signal",
                )
            else:
                st.info(f"Single district in view. Median income: {fmt_dollar(inc_df.iloc[0])}")

    with tab3:
        race_cols = {
            "% White": "pct_white",
            "% Black": "pct_black",
            "% Asian": "pct_asian",
            "% Hispanic": "pct_hispanic",
        }
        city_race = {label: city_df[col].mean() for label, col in race_cols.items() if col in city_df}
        state_race = {label: state_df[col].mean() for label, col in race_cols.items() if col in state_df}
        valid = [k for k in city_race if not np.isnan(city_race[k]) and not np.isnan(state_race[k])]
        if valid:
            st.plotly_chart(
                bar_comparison({k: city_race[k] for k in valid}, {k: state_race[k] for k in valid}, selected_city, selected_state),
                width='stretch',
            )
            explain_chart(
                "This demographic comparison is not an ornamental layer. It provides the local context required to interpret whether adoption is aligned with the communities most exposed to the transition's public-health benefits.",
                "It makes the city narrative more defensible: deployment is being read against who lives there, not only against fleet numbers.",
                preset="pattern",
            )

    st.subheader("Local leaderboard")
    local_rank = city_df[["district", "committed_esb", "operating_esb", "esb_adoption_rate", "pm25", "free_lunch_pct", "median_income"]].copy()
    local_rank = local_rank.sort_values(["esb_adoption_rate", "committed_esb"], ascending=[False, False])
    st.dataframe(local_rank.round(2), width='stretch', hide_index=True)

    if not bus_city.empty:
        st.caption(
            f"Bus-level rows available for the selected city: {len(bus_city):,}. Average bus cost in this local slice: {fmt_dollar(bus_city['bus_cost'].mean())}."
        )
