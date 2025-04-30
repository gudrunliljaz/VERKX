import streamlit as st
import pandas as pd
import numpy as np
import io
from verkx_code import main_forecast_logic

st.set_page_config(
    page_title="Cubit Spá",
    page_icon="assets/logo.png",
    layout="wide"
)

st.markdown("""
    <style>
    .language-dropdown {
        position: absolute;
        top: 10px;
        right: 20px;
        z-index: 9999;
    }
    .language-dropdown select {
        font-size: 13px !important;
        padding: 2px 6px !important;
        border-radius: 4px;
        border: 1px solid #ccc;
    }
    </style>
""", unsafe_allow_html=True)

# Language select box
with st.container():
    st.markdown('<div class="language-dropdown">', unsafe_allow_html=True)
    language = st.selectbox("Language", ["Íslenska", "English"], label_visibility="collapsed", index=0)
    st.markdown('</div>', unsafe_allow_html=True)

labels = {
    "Íslenska": {
        "title": "Cubit Spá",
        "housing": "Hvaða tegund húsnæðis viltu skoða?",
        "region": "Hvaða landshluta?",
        "years": "Fjöldi ára fram í tímann:",
        "market": "Markaðshlutdeild (%):",
        "run": "Keyra spá",
        "loading": "Reikna spá, vinsamlegast bíðið...",
        "result_tab": "Niðurstöður",
        "download_tab": "Vista niðurstöður",
        "table_title": "Cubit einingar",
        "distribution": "Dreifing",
        "download_button": "Hlaða niður CSV skrá",
        "download_name": "spa_nidurstodur.csv",
        "warning": "Aðeins {} ár fundust í framtíðarspá — notum bara þau ár.",
        "error": "Villa kom upp",
        "profit": "Áætlaður hagnaður"
    },
    "English": {
        "title": "Cubit Forecast",
        "housing": "Which housing type do you want to view?",
        "region": "Which region?",
        "years": "How many years into the future?",
        "market": "Market share (%):",
        "run": "Run forecast",
        "loading": "Running forecast, please wait...",
        "result_tab": "Results",
        "download_tab": "Download",
        "table_title": "Cubit units",
        "distribution": "Distribution",
        "download_button": "Download CSV file",
        "download_name": "forecast_results.csv",
        "warning": "Only {} years found in future data — using only those.",
        "error": "An error occurred",
        "profit": "Estimated profit"
    }
}

# Titill
st.markdown(f"<h1>{labels[language]['title']}</h1><hr>", unsafe_allow_html=True)

housing_map = {
    "Íslenska": ["Íbúðir", "Leikskólar", "Gistirými", "Elliheimili", "Atvinnuhús"],
    "English": ["Apartments", "Kindergartens", "Accommodation", "Nursing homes", "Commercial buildings"]
}
housing_reverse = dict(zip(housing_map["English"], housing_map["Íslenska"]))

region_map = {
    "Íslenska": [
        "Höfuðborgarsvæðið", "Suðurnes", "Vesturland", "Vestfirðir",
        "Norðurland vestra", "Norðurland eystra", "Austurland", "Suðurland"
    ],
    "English": [
        "Capital Region", "Southern Peninsula", "Western Region", "Westfjords",
        "Northwestern Region", "Northeastern Region", "Eastern Region", "Southern Region"
    ]
}
region_reverse = dict(zip(region_map["English"], region_map["Íslenska"]))

# Input
col1, col2 = st.columns(2)
with col1:
    housing_display = st.selectbox(labels[language]["housing"], housing_map[language])
    housing_type = housing_reverse[housing_display] if language == "English" else housing_display

with col2:
    region_display = st.selectbox(labels[language]["region"], region_map[language])
    region = region_reverse[region_display] if language == "English" else region_display

col3, col4 = st.columns(2)
with col3:
    future_years = st.number_input(labels[language]["years"], min_value=1, max_value=1000, value=5)
with col4:
    market_share_percent = st.slider(labels[language]["market"], min_value=0, max_value=100, value=50)
    final_market_share = market_share_percent / 100

# Spá takki
if st.button(labels[language]["run"]):
    with st.spinner(labels[language]["loading"]):
        try:
            # --- Forspá og niðurstöður ---
            sheet_name = f"{housing_type} eftir landshlutum"
            use_forecast = housing_type.lower() in ["íbúðir", "leikskólar"]
            past_df = load_excel(PAST_FILE, sheet_name)
            past_data = filter_data(past_df, region, "fjoldi eininga")

            start_year = 2025
            initial_share = final_market_share * np.random.uniform(0.05, 0.1)
            market_shares = np.linspace(initial_share, final_market_share, future_years)

            linear_years, linear_pred = linear_forecast(past_data, "fjoldi eininga", start_year, future_years)
            sim_demand = monte_carlo_simulation(linear_pred, market_shares)

            # --- Hagnaður ---
            profit = calculate_total_profit(sim_demand)
            avg_profit = np.mean(profit)
            st.success(f"{labels[language]['profit']}: {avg_profit:,.0f} kr.")

        except Exception as e:
            st.error(f"{labels[language]['error']}: {e}")

