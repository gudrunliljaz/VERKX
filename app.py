import streamlit as st
import pandas as pd
import numpy as np
from verkx_code import main_forecast_logic, main_forecast_logic_from_excel, calculate_offer, generate_offer_pdf
import requests
from datetime import date
from io import BytesIO
import unicodedata

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

# --- All markets forecast ---
elif ("Rekstrarspá" in page and language == "Íslenska") or ("All Markets Forecast" in page and language == "English"):
    if language == "Íslenska":
        st.title("Rekstrarspá allra markaða")
        button_label = "Keyra rekstrarspá"
        download_label = "Sækja CSV"
        success_msg = "Lokið! Hér að neðan eru spár fyrir alla markaði."
        warning_msg = "Engin gögn fundust."
        error_msg = "Villa við útreikning"
        margin_label = "Veldu arðsemiskröfu fyrir hvert ár"
    else:
        st.title("All Markets Forecast")
        button_label = "Run forecast"
        download_label = "Download CSV"
        success_msg = "Done! Below are the forecasts for all markets."
        warning_msg = "No data found."
        error_msg = "Error in calculation"
        margin_label = "Set profit margin for each year"

    st.subheader(margin_label)
    year_rates = {}
    for y in range(2025, 2030):
        label = f"Arðsemiskrafa fyrir árið {y}" if language == "Íslenska" else f"Profit margin for year {y}"
        year_rates[y] = st.number_input(label, min_value=0.0, max_value=1.0, value=0.15, step=0.01, key=f"rate_{y}")

    if st.button(button_label, key="run_all_markets_forecast_button"):
        with st.spinner("Reikna..." if language == "Íslenska" else "Calculating..."):
            try:
                df = main_forecast_logic_from_excel(
                    past_file="data/GÖGN_VERKX.xlsx",
                    future_file="data/Framtidarspa.xlsx",
                    share_file="data/markadshlutdeild.xlsx"
                )

                if df is not None and not df.empty:
                    df["Arðsemiskrafa"] = df["Ár"].map(year_rates)
                    df["Tekjur"] = df["Heildarkostnaður"] * (1 + df["Arðsemiskrafa"])
                    df["Hagnaður"] = df["Tekjur"] - df["Heildarkostnaður"]
                    st.success(success_msg)
                    st.dataframe(df)

                    st.download_button(
                        download_label,
                        data=df.to_csv(index=False).encode("utf-8-sig"),
                        file_name="rekstrarspa.csv",
                        mime="text/csv"
                    )
                else:
                    st.warning(warning_msg)
            except Exception as e:
                st.error(f"{error_msg}: {e}")

# --- Quotation calculator ---
elif ("Tilboðsreiknivél" in page and language == "Íslenska") or ("Quotation Calculator" in page and language == "English"):
    st.header("Tilboðsreiknivél" if language == "Íslenska" else "Quotation Calculator")

    afh_map = {
        "Íslenska": {
            "Höfuðborgarsvæðið": 60, "Selfoss": 30, "Akranes": 100,
            "Akureyri": 490, "Egilsstaðir": 650, "Keflavík": 90,
            "Annað": None
        },
        "English": {
            "Capital Region": 60, "Selfoss": 30, "Akranes": 100,
            "Akureyri": 490, "Egilsstaðir": 650, "Keflavík": 90,
            "Other": None
        }
    }

    with st.form("form_offer"):
        col1, col2, col3, col4 = st.columns(4)
        modul3 = col1.number_input("Þrjár einingar" if language == "Íslenska" else "Three Modules", min_value=0, value=0)
        modul2 = col2.number_input("Tvær einingar" if language == "Íslenska" else "Two Modules", min_value=0, value=0)
        modul1 = col3.number_input("Ein eining" if language == "Íslenska" else "One Module", min_value=0, value=0)
        modul_half = col4.number_input("Hálf eining" if language == "Íslenska" else "Half Module", min_value=0, value=0)

        locs = afh_map[language]
        col5, col6 = st.columns(2)
        place = col5.selectbox("Afhendingarstaður" if language == "Íslenska" else "Delivery location", list(locs))
        if place in ["Annað", "Other"]:
            addr = col5.text_input("Staðsetning" if language == "Íslenska" else "Location")
            dist = col6.number_input("Fjarlægð frá Þorlákshöfn (km)" if language == "Íslenska" else "Distance from Þorlákshöfn (km)", min_value=0.0)
        else:
            addr = place
            dist = locs[place]

        client = st.text_input("Verkkaupi" if language == "Íslenska" else "Client")
        submit = st.form_submit_button("Reikna tilboð" if language == "Íslenska" else "Calculate offer")

    if submit:
        modules = {"3m": modul3, "2m": modul2, "1m": modul1, "0.5m": modul_half}
        if all(v == 0 for v in modules.values()):
            st.warning("Veldu einingar" if language == "Íslenska" else "Select modules")
        elif dist == 0:
            st.warning("Settu inn fjarlægð" if language == "Íslenska" else "Enter distance")
        else:
            try:
                rate = requests.get("https://api.frankfurter.app/latest?from=EUR&to=ISK", timeout=5)
                eur_to_isk = rate.json()['rates']['ISK']
            except:
                eur_to_isk = 146

            result = calculate_offer(modules, dist, eur_to_isk)

            st.write(f"**Tilboðsverð (ISK):** {result['tilbod']:,.0f}" if language == "Íslenska" else f"**Offer price (ISK):** {result['tilbod']:,.0f}")
            st.write(f"**Tilboðsverð (EUR):** €{result['tilbod_eur']:,.2f}" if language == "Íslenska" else f"**Offer price (EUR):** €{result['tilbod_eur']:,.2f}")

            try:
                nafn = unicodedata.normalize('NFKD', client).encode('ascii', 'ignore').decode('ascii')
                stadur = unicodedata.normalize('NFKD', addr).encode('ascii', 'ignore').decode('ascii')
                pdf_bytes = generate_offer_pdf(nafn, stadur, result)
                st.download_button("Sækja PDF tilboð" if language == "Íslenska" else "Download offer PDF", pdf_bytes, file_name=f"tilbod_{nafn}.pdf", mime="application/pdf")
            except:
                st.error("Villa við útgáfu PDF.")






