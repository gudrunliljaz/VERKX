import streamlit as st
import pandas as pd
import numpy as np
from verkx_code import main_forecast_logic, main_forecast_logic_from_excel, calculate_offer, generate_offer_pdf
import requests
from datetime import date
from io import BytesIO

# Page configuration
st.set_page_config(page_title="Cubit", page_icon="cubitlogo.png", layout="wide")

# --- Sidebar language selection ---
with st.sidebar:
    language = st.selectbox("Language", ["Íslenska", "English"], index=0)
    page = st.radio(
        "Veldu síðu / Choose page",
        ["Eftirspurnarspá", "Tilboðsreiknivél", "Rekstrarspá"] if language == "Íslenska"
        else ["Demand Forecast", "Quotation Calculator", "All Markets Forecast"]
    )

# --- Forecast model ---
if ("Eftirspurnarspá" in page and language == "Íslenska") or ("Demand Forecast" in page and language == "English"):
    if language == "Íslenska":
        button_label = "Keyra spá"
        download_label = "Sækja CSV"
        success_msg = "Lokið! Hér að neðan eru spár."
        warning_msg = "Engin gögn fundust."
        error_msg = "Villa við útreikning"
    else:
        button_label = "Run forecast"
        download_label = "Download CSV"
        success_msg = "Done! Below are the forecasts."
        warning_msg = "No data found."
        error_msg = "Error in calculation"

    if st.button(button_label, key="run_demand_forecast_button"):
        with st.spinner("Reikna..." if language == "Íslenska" else "Calculating..."):
            try:
                df = main_forecast_logic_from_excel(
                    past_file="data/GÖGN_VERKX.xlsx",
                    future_file="data/Framtidarspa.xlsx",
                    share_file="data/markadshlutdeild.xlsx"
                )

                if df is not None and not df.empty:
                    st.success(success_msg)

                    st.subheader("Arðsemiskrafa eftir ári" if language == "Íslenska" else "Profit margin per year")
                    year_rates = {}
                    for year in df["Ár"]:
                        label = f"Arðsemiskrafa fyrir árið {year}" if language == "Íslenska" else f"Profit margin for year {year}"
                        key = f"margin_{year}_demand"
                        year_rates[year] = st.number_input(
                            label,
                            min_value=0.0,
                            max_value=1.0,
                            value=0.15,
                            step=0.01,
                            key=key
                        )

                    df["Arðsemiskrafa"] = df["Ár"].map(year_rates)
                    df["Tekjur"] = df["Heildarkostnaður"] * (1 + df["Arðsemiskrafa"])
                    df["Hagnaður"] = df["Tekjur"] - df["Heildarkostnaður"]

                    st.dataframe(df)

                    st.download_button(
                        download_label,
                        data=df.to_csv(index=False).encode("utf-8-sig"),
                        file_name="heildarspa.csv",
                        mime="text/csv"
                    )
                else:
                    st.warning(warning_msg)
            except Exception as e:
                st.error(f"{error_msg}: {e}")




