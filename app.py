import streamlit as st
import pandas as pd
import numpy as np
import io
from verkx_code import main_forecast_logic

# Page config – verður að vera fyrst
st.set_page_config(
    page_title="Cubit Spá",
    page_icon="assets/logo.png",
    layout="wide"
)

# Tungumálaval í efra hægra horni
st.markdown("""
    <style>
    div[data-testid="stSidebar"] div.language-dropdown {
        position: absolute;
        top: 10px;
        right: 20px;
        z-index: 9999;
    }
    div.language-dropdown select {
        font-size: 13px !important;
        padding: 2px 6px !important;
        border-radius: 4px;
        border: 1px solid #ccc;
    }
    </style>
""", unsafe_allow_html=True)

with st.container():
    st.markdown('<div class="language-dropdown">', unsafe_allow_html=True)
    language = st.selectbox("Language", ["Íslenska", "English"], label_visibility="collapsed", index=0)
    st.markdown('</div>', unsafe_allow_html=True)

# Þýðingar
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
        "financials": "Tekjumódel",
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
        "financials": "Revenue model",
        "download_button": "Download CSV file",
        "download_name": "forecast_results.csv",
        "warning": "Only {} years found in future data — using only those.",
        "error": "An error occurred"
    }
}

# Fjárhagsniðurstöður – þýðingar
financial_labels = {
    "Íslenska": {
        "Einingar": "Einingar",
        "Fermetrar": "Fermetrar",
        "Tekjur": "Tekjur",
        "Heildarkostnaður": "Heildarkostnaður",
        "Hagnaður": "Hagnaður",
        "NPV": "Núvirt virði (NPV)"
    },
    "English": {
        "Einingar": "Units",
        "Fermetrar": "Square meters",
        "Tekjur": "Revenue",
        "Heildarkostnaður": "Total cost",
        "Hagnaður": "Profit",
        "NPV": "Net Present Value (NPV)"
    }
}

# Titill
st.markdown(f"<h1>{labels[language]['title']}</h1><hr>", unsafe_allow_html=True)

# Housing mappings
housing_map = {
    "Íslenska": ["Íbúðir", "Leikskólar", "Gistirými", "Elliheimili", "Atvinnuhús"],
    "English": ["Apartments", "Kindergartens", "Accommodation facilities", "Nursing homes", "Commercial buildings"]
}
housing_reverse = dict(zip(housing_map["English"], housing_map["Íslenska"]))

# Region mappings
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

# Inputs
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

# Keyra
if st.button(labels[language]["run"]):
    with st.spinner(labels[language]["loading"]):
        try:
            df, figures, used_years, financials = main_forecast_logic(housing_type, region, future_years, final_market_share)

            if used_years < future_years:
                st.warning(labels[language]["warning"].format(used_years))

            if language == "English":
                df = df.rename(columns={
                    "Ár": "Year",
                    "Fortíðargögn spá": "Historical Forecast",
                    "Framtíðarspá": "Future Forecast",
                    "Meðaltal": "Average",
                    "Spá útfrá fortíðargögnum": "Forecast from historical data"
                })

            tabs = st.tabs([labels[language]["result_tab"], labels[language]["download_tab"]])

            with tabs[0]:
                st.subheader(labels[language]["table_title"])
                index_col = "Ár" if language == "Íslenska" else "Year"
                st.dataframe(df.set_index(index_col).style.format("{:.2f}"))

                st.subheader(labels[language]["distribution"])
                img_cols = st.columns(len(figures))
                for col, fig in zip(img_cols, figures):
                    with col:
                        st.pyplot(fig)

                st.subheader(labels[language]["financials"])
                for key, value in financials.items():
                    label = financial_labels[language].get(key, key)
                    st.write(f"**{label}:** {value:,.0f} kr.")

            with tabs[1]:
                csv = df.to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig")
                st.download_button(
                    label=labels[language]["download_button"],
                    data=csv,
                    file_name=labels[language]["download_name"],
                    mime="text/csv"
                )

        except Exception as e:
            st.error(f"{labels[language]['error']}: {e}")



