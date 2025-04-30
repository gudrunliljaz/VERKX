import streamlit as st
import pandas as pd
import numpy as np
import io
from verkx_code import main_forecast_logic

# Page config
st.set_page_config(page_title="Cubit Forecast", page_icon="📊", layout="wide")

# Language toggle top right
language = st.sidebar.selectbox("Language / Tungumál", ["Íslenska", "English"])

# Labels
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
        "error": "Villa kom upp"
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
        "error": "An error occurred"
    }
}

# Title (centered + dark blue)
st.markdown(f"""
    <style>
        h1 {{
            color: #003366;
            text-align: center;
        }}
    </style>
    <h1>{labels[language]["title"]}</h1>
    <hr>
""", unsafe_allow_html=True)

# Housing + region selection
col1, col2 = st.columns(2)

housing_options = {
    "Íslenska": ["Íbúðir", "Leikskólar", "Gistirými", "Elliheimili", "Atvinnuhús"],
    "English": ["Apartments", "Preschools", "Guesthouses", "Nursing homes", "Commercial"]
}

region_options = [
    "Höfuðborgarsvæðið", "Suðurnes", "Vesturland", "Vestfirðir",
    "Norðurland vestra", "Norðurland eystra", "Austurland", "Suðurland"
]

with col1:
    housing_type = st.selectbox(labels[language]["housing"], housing_options[language])

with col2:
    region = st.selectbox(labels[language]["region"], region_options)

# Forecast params
col3, col4 = st.columns(2)

with col3:
    future_years = st.number_input(labels[language]["years"], min_value=1, max_value=1000, value=5)

with col4:
    market_share_percent = st.slider(labels[language]["market"], min_value=0, max_value=100, value=50)
    final_market_share = market_share_percent / 100

# Run forecast
if st.button(labels[language]["run"]):
    with st.spinner(labels[language]["loading"]):
        try:
            df, figures, used_years = main_forecast_logic(housing_type, region, future_years, final_market_share)

            if used_years < future_years:
                st.warning(labels[language]["warning"].format(used_years))

            tabs = st.tabs([labels[language]["result_tab"], labels[language]["download_tab"]])

            with tabs[0]:
                st.subheader(labels[language]["table_title"])
                st.dataframe(df.set_index("Ár").style.format("{:.2f}"))

                st.subheader(labels[language]["distribution"])
                img_cols = st.columns(len(figures))
                for col, fig in zip(img_cols, figures):
                    with col:
                        st.pyplot(fig)

            with tabs[1]:
                csv = df.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label=labels[language]["download_button"],
                    data=csv,
                    file_name=labels[language]["download_name"],
                    mime="text/csv"
                )

        except Exception as e:
            st.error(f"{labels[language]['error']}: {e}")









