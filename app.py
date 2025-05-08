import streamlit as st
import pandas as pd
import numpy as np
from datetime import date
from fpdf import FPDF
from io import BytesIO
import requests
from verkx_code import main_forecast_logic, main_forecast_logic_from_excel

# Page config
st.set_page_config(page_title="Cubit", page_icon="andreim.png", layout="wide")

# Language and Page selection
st.sidebar.title("Stillingar / Settings")
language = st.sidebar.selectbox("Language", ["Íslenska", "English"], index=0)
page = st.sidebar.radio("Veldu síðu / Choose page", ["Spálíkan", "Tilboðsreiknivél", "Heildarspá"] if language == "Íslenska" else ["Forecast Model", "Quotation Calculator", "All Markets Forecast"])

# Labels
labels = {
    "Íslenska": {
        "title": "Cubit Spá",
        "housing": "Tegund húsnæðis",
        "region": "Landshluti",
        "years": "Fjöldi ára fram í tímann",
        "market": "Markaðshlutdeild (%)",
        "run": "Keyra spá",
        "loading": "Reikna spá, vinsamlegast bíðið...",
        "result_tab": "Niðurstöður",
        "download_tab": "Vista niðurstöður",
        "table_title": "Cubit einingar",
        "distribution": "Dreifing",
        "download_button": "Hlaða niður CSV skrá",
        "download_name": "spa_nidurstodur.csv",
        "warning": "Aðeins {} ár fundust í framtíðarspá — notum bara þau ár.",
        "error": "Villa kom upp"
    },
    "English": {
        "title": "Cubit Forecast",
        "housing": "Housing type",
        "region": "Region",
        "years": "Years into the future",
        "market": "Market share (%)",
        "run": "Run forecast",
        "loading": "Running forecast, please wait...",
        "result_tab": "Results",
        "download_tab": "Download",
        "table_title": "Cubit units",
        "distribution": "Distribution",
        "download_button": "Download CSV file",
        "download_name": "forecast_results.csv",
        "warning": "Only {} years found in future data — using only those.",
        "error": "An error occurred"
    }
}

# Forecast Page
if ("Spálíkan" in page or "Forecast" in page):
    st.title(labels[language]["title"])
    housing_map = {
        "Íslenska": ["Íbúðir", "Leikskólar", "Gistirými", "Elliheimili", "Atvinnuhús"],
        "English": ["Apartments", "Kindergartens", "Accommodation facilities", "Nursing homes", "Commercial buildings"]
    }
    housing_reverse = dict(zip(housing_map["English"], housing_map["Íslenska"]))
    region_map = {
        "Íslenska": ["Höfuðborgarsvæðið", "Suðurnes", "Vesturland", "Vestfirðir", "Norðurland vestra", "Norðurland eystra", "Austurland", "Suðurland"],
        "English": ["Capital Region", "Southern Peninsula", "Western Region", "Westfjords", "Northwestern Region", "Northeastern Region", "Eastern Region", "Southern Region"]
    }
    region_reverse = dict(zip(region_map["English"], region_map["Íslenska"]))

    col1, col2 = st.columns(2)
    with col1:
        housing_display = st.selectbox(labels[language]["housing"], housing_map[language])
        housing_type = housing_reverse.get(housing_display, housing_display)
    with col2:
        region_display = st.selectbox(labels[language]["region"], region_map[language])
        region = region_reverse.get(region_display, region_display)

    col3, col4 = st.columns(2)
    with col3:
        future_years = st.number_input(labels[language]["years"], min_value=1, max_value=1000, value=5)
    with col4:
        market_share_percent = st.slider(labels[language]["market"], min_value=0, max_value=100, value=50)
        final_market_share = market_share_percent / 100

    if st.button(labels[language]["run"]):
        with st.spinner(labels[language]["loading"]):
            try:
                df, figures, used_years = main_forecast_logic(housing_type, region, future_years, final_market_share)
                if used_years < future_years:
                    st.warning(labels[language]["warning"].format(used_years))

                tabs = st.tabs([labels[language]["result_tab"], labels[language]["download_tab"]])
                with tabs[0]:
                    st.subheader(labels[language]["table_title"])
                    st.dataframe(df.set_index("Ár"))
                    st.subheader(labels[language]["distribution"])
                    for fig in figures:
                        st.pyplot(fig)
                with tabs[1]:
                    st.download_button(
                        label=labels[language]["download_button"],
                        data=df.to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig"),
                        file_name=labels[language]["download_name"],
                        mime="text/csv"
                    )
            except Exception as e:
                st.error(f"{labels[language]['error']}: {e}")

# Quotation Calculator
if ("Tilboðsreiknivél" in page or "Quotation" in page):
    st.title("Tilboðsreiknivél")
    with st.form("tilbod_form"):
        st.markdown("### Veldu fjölda eininga")
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            m3 = st.number_input("3 eininga mót", min_value=0, value=0)
        with col2:
            m2 = st.number_input("2 eininga mót", min_value=0, value=0)
        with col3:
            m1 = st.number_input("1 eining", min_value=0, value=0)
        with col4:
            mhalf = st.number_input("0.5 eining", min_value=0, value=0)

        client = st.text_input("Nafn verkkaupa")
        location = st.text_input("Afhendingarstaður")
        km = st.number_input("Fjarlægð frá Þorlákshöfn (km)", min_value=0.0, value=0.0)
        submitted = st.form_submit_button("Reikna tilboð")

    if submitted:
        try:
            res = requests.get("https://api.frankfurter.app/latest?from=EUR&to=ISK", timeout=3)
            eur_to_isk = res.json()['rates']['ISK']
        except:
            eur_to_isk = 146.0

        units = {
            "3m": {"count": m3, "sqm": 19.5, "price_eur": 1800},
            "2m": {"count": m2, "sqm": 13, "price_eur": 1950},
            "1m": {"count": m1, "sqm": 6.5, "price_eur": 2050},
            "0.5m": {"count": mhalf, "sqm": 3.25, "price_eur": 2175},
        }

        total_sqm = sum(u["count"] * u["sqm"] for u in units.values())
        unit_cost = sum(u["count"] * u["sqm"] * u["price_eur"] * eur_to_isk for u in units.values())
        shipping_cost = total_sqm * 74000
        domestic_delivery = total_sqm * km * 8
        total_variable = unit_cost + shipping_cost + domestic_delivery
        fixed_cost = 34800000
        allocated_fixed = fixed_cost * (total_sqm / 2400) if total_sqm else 0
        markup = 1 + (allocated_fixed / total_variable) if total_variable else 1
        offer = total_variable * markup * 1.15
        offer_eur = offer / eur_to_isk

        st.subheader("Niðurstöður tilboðs")
        st.write(f"**Heildarfermetrar:** {total_sqm:.2f} fm")
        st.write(f"**Flutningur til Íslands:** {shipping_cost:,.0f} kr")
        st.write(f"**Sendingarkostnaður innanlands:** {domestic_delivery:,.0f} kr")
        st.write(f"**Breytilegur kostnaður:** {total_variable:,.0f} kr")
        st.write(f"**Fastur kostnaður (úthlutaður):** {allocated_fixed:,.0f} kr")
        st.write(f"**Álagsstuðull:** {markup:.2f}")
        st.write(f"**Tilboðsverð:** {offer:,.0f} kr. / €{offer_eur:,.2f}")
        st.success("Tilboð reiknað")

# All Market Forecast
if ("Heildarspá" in page or "All Markets Forecast" in page):
    st.title("📊 Heildarspá allra markaða")
    profit_margin_percent = st.slider("Arðsemiskrafa (%)", 0, 100, 15)
    profit_margin = profit_margin_percent / 100
    if st.button("Keyra heildarspá"):
        with st.spinner("Keyri heildarspá..."):
            try:
                summary = main_forecast_logic_from_excel(
                    past_file="data/GÖGN_VERKX.xlsx",
                    future_file="data/Framtidarspa.xlsx",
                    share_file="data/markadshlutdeild.xlsx",
                    profit_margin=profit_margin
                )
                if summary is not None:
                    st.dataframe(summary.set_index("ár").style.format("{:,.0f}"))
                    st.download_button(
                        "📥 Hlaða niður CSV",
                        data=summary.to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig"),
                        file_name="heildarspa.csv",
                        mime="text/csv"
                    )
                else:
                    st.warning("Engin gögn fundust.")
            except Exception as e:
                st.error(f"Villa: {e}")
