import streamlit as st
import pandas as pd
import numpy as np
import io
import datetime
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
        "financials": "Tekjumódel",
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



st.markdown("---")
st.subheader("Tilboðsreiknivél")

with st.form("tilbod_form"):
    st.markdown("### Gögn um einingar")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        modul3 = st.number_input("Fjöldi 3 módúla", min_value=0, value=0)
    with col2:
        modul2 = st.number_input("Fjöldi 2 módúla", min_value=0, value=0)
    with col3:
        modul1 = st.number_input("Fjöldi 1 módúla", min_value=0, value=0)
    with col4:
        modul_half = st.number_input("Fjöldi 1/2 módúla", min_value=0, value=0)

    st.markdown("### Aðrar upplýsingar")
    col5, col6, col7 = st.columns(3)
    with col5:
        verkkaupi = st.text_input("Verkkaupi")
    with col6:
        stadsetning = st.text_input("Staðsetning afhendingar")
    with col7:
        km_fra_thorlakshofn = st.number_input("Km frá Þorlákshöfn", min_value=0.0, value=0.0)

    submitted = st.form_submit_button("Reikna tilboð")

if submitted:
    einingar = {
        "3m": {"fjoldi": modul3, "fm": 19.5, "verd": 269700, "kg": 9750},
        "2m": {"fjoldi": modul2, "fm": 13, "verd": 290000, "kg": 6500},
        "1m": {"fjoldi": modul1, "fm": 6.5, "verd": 304500, "kg": 3250},
        "0.5m": {"fjoldi": modul_half, "fm": 3.25, "verd": 330000, "kg": 1625},
    }

    heildarfm = sum(e["fjoldi"] * e["fm"] for e in einingar.values())
    heildarthyngd = sum(e["fjoldi"] * e["kg"] for e in einingar.values())
    heildarkostnadur_einingar = sum(e["fjoldi"] * e["verd"] for e in einingar.values())
    kostnadur_per_fm = heildarkostnadur_einingar / heildarfm if heildarfm else 0
    flutningur_til_islands = heildarfm * 74000
    sendingarkostnadur = heildarfm * km_fra_thorlakshofn * 8
    samtals_breytilegur = heildarkostnadur_einingar + flutningur_til_islands + sendingarkostnadur

    if samtals_breytilegur > 0:
        fastur_kostnadur = 34800000
        heildarfm_arsins = 2400
        uthlutadur_fastur_kostnadur = (heildarfm / heildarfm_arsins) * fastur_kostnadur
        alagsstudull = 1 + (uthlutadur_fastur_kostnadur / samtals_breytilegur)
        tilbod = samtals_breytilegur * alagsstudull * 1.15

        st.markdown("### Niðurstöður")
        st.write(f"**Dagsetning:** {datetime.date.today()}")
        st.write(f"**Verkkaupi:** {verkkaupi}")
        st.write(f"**Afhendingarstaður:** {stadsetning}")
        st.write(f"**Heildarfermetrar:** {heildarfm:.2f} fm")
        st.write(f"**Heildarþyngd:** {heildarthyngd:,.0f} kg")
        st.write(f"**Kostnaðarverð á fermetra:** {kostnadur_per_fm:,.0f} kr.")
        st.write(f"**Flutningur til Íslands:** {flutningur_til_islands:,.0f} kr.")
        st.write(f"**Sendingarkostnaður:** {sendingarkostnadur:,.0f} kr.")
        st.write(f"**Samtals breytilegur kostnaður:** {samtals_breytilegur:,.0f} kr.")
        st.write(f"**Úthlutaður fastur kostnaður:** {uthlutadur_fastur_kostnadur:,.0f} kr.")
        st.write(f"**Álagsstuðull:** {alagsstudull:.2f}")
        st.write(f"**Tilboðsverð (með 15% ásemiskröfu):** {tilbod:,.0f} kr.")
    else:
        st.warning("Vinsamlegast sláðu inn gildi fyrir einingar til að reikna tilboð.")


