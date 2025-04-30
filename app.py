import streamlit as st
import pandas as pd
import numpy as np
import io
from verkx_code import main_forecast_logic

# Þarf að vera fyrst
st.set_page_config(page_title="Cubit Spá", page_icon="assets/logo.png", layout="wide")

# Tungumálaval efst í hægra horni
top_left, top_right = st.columns([6, 1])
with top_right:
    st.markdown("<div style='font-weight:500;'>Language</div>", unsafe_allow_html=True)
    language = st.selectbox("", ["Íslenska", "English"])

# Texti eftir tungumáli
labels = {
    "Íslenska": {
        "title": "Cubit Spá",
        "housing": "Hvaða tegund húsnæðis viltu skoða?",
        "region": "Hvaða landshluta?",
        "years": "Fjöldi ára fram í tímann:",
        "market_share": "Markaðshlutdeild (%):",
        "run": "Keyra spá",
        "loading": "Reikna spá, vinsamlegast bíðið...",
        "years_warning": "Aðeins {used} ár fundust í framtíðarspá — notum bara þau ár.",
        "results": "Niðurstöður",
        "download": "Vista niðurstöður",
        "table": "Cubit einingar",
        "distribution": "Dreifing",
        "csv": "Hlaða niður CSV skrá",
        "error": "Villa kom upp"
    },
    "English": {
        "title": "Cubit Forecast",
        "housing": "What type of housing do you want to view?",
        "region": "Which region?",
        "years": "Number of years into the future:",
        "market_share": "Market share (%):",
        "run": "Run forecast",
        "loading": "Calculating forecast, please wait...",
        "years_warning": "Only {used} years found in forecast — using those years only.",
        "results": "Results",
        "download": "Download results",
        "table": "Cubit units",
        "distribution": "Distribution",
        "csv": "Download CSV file",
        "error": "An error occurred"
    }
}

# Titill
st.markdown(f"""
    <style>
    h1 {{
        color: #003366;
        text-align: center;
    }}
    </style>
    <h1>{labels[language]["title"]}</h1>
""", unsafe_allow_html=True)
st.markdown("---")

# Húsnæðistegundir á báðum tungumálum
housing_options_map = {
    "Íslenska": ["Íbúðir", "Leikskólar", "Gistirými", "Elliheimili", "Atvinnuhús"],
    "English":  ["Apartments", "Preschools", "Accommodation", "Nursing Homes", "Commercial Buildings"]
}

# Svæðin eru þau sömu
region_options = [
    "Höfuðborgarsvæðið", "Suðurnes", "Vesturland", "Vestfirðir",
    "Norðurland vestra", "Norðurland eystra", "Austurland", "Suðurland"
]

# Valform
col1, col2 = st.columns(2)

with col1:
    display_housing_options = housing_options_map[language]
    housing_selection = st.selectbox(labels[language]["housing"], display_housing_options)

with col2:
    region = st.selectbox(labels[language]["region"], region_options)

col3, col4 = st.columns(2)

with col3:
    future_years = st.number_input(labels[language]["years"], min_value=1, max_value=1000, value=5)

with col4:
    market_share_percent = st.slider(labels[language]["market_share"], min_value=0, max_value=100, value=50)
    final_market_share = market_share_percent / 100

# Breyta yfir í íslenskt nafn fyrir Excel-sheet
reverse_map = dict(zip(housing_options_map[language], housing_options_map["Íslenska"]))
housing_type = reverse_map[housing_selection]

# Keyra spá
if st.button(labels[language]["run"]):
    with st.spinner(labels[language]["loading"]):
        try:
            df, figures, used_years = main_forecast_logic(housing_type, region, future_years, final_market_share)

            if used_years < future_years:
                st.warning(labels[language]["years_warning"].format(used=used_years))

            tabs = st.tabs([labels[language]["results"], labels[language]["download"]])

            with tabs[0]:
                st.subheader(labels[language]["table"])
                st.dataframe(df.set_index("Ár").style.format("{:.2f}"))

                st.subheader(labels[language]["distribution"])
                img_cols = st.columns(len(figures))
                for col, fig in zip(img_cols, figures):
                    with col:
                        st.pyplot(fig)

            with tabs[1]:
                csv = df.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label=labels[language]["csv"],
                    data=csv,
                    file_name="spa_nidurstodur.csv",
                    mime="text/csv"
                )

        except Exception as e:
            st.error(f"{labels[language]['error']]}: {e}")







