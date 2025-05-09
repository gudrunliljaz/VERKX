import streamlit as st
import pandas as pd
import numpy as np
from verkx_code import main_forecast_logic, main_forecast_logic_from_excel, calculate_offer, generate_offer_pdf
import requests
from datetime import date

# Page configuration
st.set_page_config(page_title="Cubit", page_icon="andreim.png", layout="wide")

# --- Sidebar language selection ---
with st.sidebar:
    language = st.selectbox("Language", ["Íslenska", "English"], index=0)
    page = st.radio(
        "Veldu síðu/Choose page",
        ["Spálíkan", "Tilboðsreiknivél", "Rekstrarspá"] if language == "Íslenska"
        else ["Forecast Model", "Quotation Calculator", "All Markets Forecast"]
    )

# --- Labels dictionary ---
labels = {
    "Íslenska": {
        "title": "Cubit Spá",
        "housing": "Tegund húsnæðis",
        "region": "Landshluti",
        "years": "Fjöldi ára fram í tímann",
        "market": "Markaðshlutdeild (%)",
        "run": "Keyra spá",
        "loading": "Reikna spá...",
        "result_tab": "Niiðurstöður",
        "download_tab": "Sækja gögn",
        "table_title": "Cubit einingar",
        "distribution": "Dreifing",
        "download_button": "Sækja CSV",
        "download_name": "spa.csv",
        "warning": "Aðeins {} ár fundust í framtíðarspá",
        "error": "Villa kom upp"
    },
    "English": {
        "title": "Cubit Forecast",
        "housing": "Housing type",
        "region": "Region",
        "years": "Years into future",
        "market": "Market share (%)",
        "run": "Run forecast",
        "loading": "Running forecast...",
        "result_tab": "Results",
        "download_tab": "Download",
        "table_title": "Cubit units",
        "distribution": "Distribution",
        "download_button": "Download CSV",
        "download_name": "forecast.csv",
        "warning": "Only {} years found in future forecast",
        "error": "An error occurred"
    }
}

# --- Forecast model page ---
if "Spálíkan" in page or "Forecast" in page:
    st.header(labels[language]['title'])

    housing_map = {
        "Íslenska": ["Íbúðir", "Leikskólar", "Gistirými", "Elliheimili", "Atvinnuhús"],
        "English": ["Apartments", "Kindergartens", "Accommodation", "Nursing homes", "Commercial"]
    }
    housing_reverse = dict(zip(housing_map["English"], housing_map["Íslenska"]))

    region_map = {
        "Íslenska": [
            "Höfuðborgarsvæðið", "Suðurnes", "Vesturland", "Vestfirðir",
            "Norðurland vestra", "Norðurland eystra", "Austurland", "Suðurland"
        ],
        "English": [
            "Capital Region", "Southern Peninsula", "Western Region", "Westfjords",
            "Northwest", "Northeast", "East", "South"
        ]
    }
    region_reverse = dict(zip(region_map["English"], region_map["Íslenska"]))

    col1, col2 = st.columns(2)
    with col1:
        housing_display = st.selectbox(labels[language]["housing"], housing_map[language])
        housing_type = housing_reverse[housing_display] if language == "English" else housing_display
    with col2:
        region_display = st.selectbox(labels[language]["region"], region_map[language])
        region = region_reverse[region_display] if language == "English" else region_display

    col3, col4 = st.columns(2)
    with col3:
        future_years = st.number_input(labels[language]["years"], min_value=1, value=5)
    with col4:
        market_share = st.slider(labels[language]["market"], 0, 100, 50) / 100

    if st.button(labels[language]["run"]):
        with st.spinner(labels[language]["loading"]):
            try:
                df, figures, used_years = main_forecast_logic(housing_type, region, future_years, market_share)

                if used_years < future_years:
                    st.warning(labels[language]["warning"].format(used_years))

                tabs = st.tabs([labels[language]["result_tab"], labels[language]["download_tab"]])

                with tabs[0]:
                    st.subheader(labels[language]["table_title"])
                    st.dataframe(df.set_index(df.columns[0]))

                    st.subheader(labels[language]["distribution"])
                    for fig in figures:
                        st.pyplot(fig)

                with tabs[1]:
                    csv = df.to_csv(index=False).encode("utf-8-sig")
                    st.download_button(labels[language]["download_button"], csv, labels[language]["download_name"], "text/csv")

            except Exception as e:
                st.error(f"{labels[language]['error']}: {e}")

# --- All markets forecast ---
elif "Rekstrarspá" in page or "All Markets Forecast" in page:
    st.title("Rekstrarspá allra markaða" if language == "Íslenska" else "All Markets Forecast")
    margin = st.slider("Arðsemiskrafa (%)" if language == "Íslenska" else "Profit margin (%)", 0, 100, 15)
    margin_decimal = margin / 100

    if st.button("Keyra rekstrarspá" if language == "Íslenska" else "Run forecast"):
        with st.spinner("Reikna..." if language == "Íslenska" else "Calculating..."):
            try:
                df = main_forecast_logic_from_excel(
                    past_file="data/GÖGN_VERKX.xlsx",
                    future_file="data/Framtidarspa.xlsx",
                    share_file="data/markadshlutdeild.xlsx",
                    profit_margin=margin_decimal
                )
                if df is not None and not df.empty:
                    st.success("Lokii!" if language == "Íslenska" else "Done!")
                    st.dataframe(df)
                    st.download_button(
                        "Sækja CSV" if language == "Íslenska" else "Download CSV",
                        data=df.to_csv(index=False).encode("utf-8-sig"),
                        file_name="heildarspa.csv",
                        mime="text/csv"
                    )
                else:
                    st.warning("Engin gögn fundust." if language == "Íslenska" else "No data found.")
            except Exception as e:
                st.error(f"Villa: {e}" if language == "Íslenska" else f"Error: {e}")

# --- Quotation calculator stub ---
elif "Tilboðsreiknivél" in page or "Quotation" in page:
    st.warning("Tilboðsreiknivél er ekki virkjur í þessari útgáfu." if language == "Íslenska" else "Quotation calculator is not enabled in this version.")





