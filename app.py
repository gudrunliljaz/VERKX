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
        "result_tab": "Niðurstöður",
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

# --- Quotation calculator ---
elif "Tilboðsreiknivél" in page or "Quotation" in page:
    st.title("Tilboðsreiknivél" if language == "Íslenska" else "Quotation Calculator")

    afhendingar_map = {
        "Íslenska": {
            "Höfuðborgarsvæðið": 60, "Selfoss": 30, "Hveragerði": 40, "Akranes": 100,
            "Borgarnes": 150, "Stykkishólmur": 260, "Ísafjörður": 570, "Akureyri": 490,
            "Húsavík": 520, "Sauðárkrókur": 450, "Egilsstaðir": 650, "Seyðisfjörður": 670,
            "Neskaupstaður": 700, "Eskifjörður": 690, "Fáskrúðsfjörður": 680, "Höfn": 450,
            "Vestmannaeyjar": 90, "Keflavík": 90, "Annað": None
        },
        "English": {
            "Capital Region": 60, "Selfoss": 30, "Hveragerði": 40, "Akranes": 100,
            "Borgarnes": 150, "Stykkishólmur": 260, "Ísafjörður": 570, "Akureyri": 490,
            "Húsavík": 520, "Sauðárkrókur": 450, "Egilsstaðir": 650, "Seyðisfjörður": 670,
            "Neskaupstaður": 700, "Eskifjörður": 690, "Fáskrúðsfjörður": 680, "Höfn": 450,
            "Vestmannaeyjar": 90, "Keflavík": 90, "Other": None
        }
    }

    with st.form("tilbod_form"):
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            modul3 = st.number_input("3 Modules", min_value=0, value=0)
        with col2:
            modul2 = st.number_input("2 Modules", min_value=0, value=0)
        with col3:
            modul1 = st.number_input("1 Module", min_value=0, value=0)
        with col4:
            modul_half = st.number_input("0.5 Module", min_value=0, value=0)

        st.markdown("### Afhending")
        afhendingarstaedir = afhendingar_map[language]
        col5, col6 = st.columns(2)
        with col5:
            stadsetning_val = st.selectbox("Afhendingarstaður / Delivery Location", list(afhendingarstaedir.keys()))
        with col6:
            if stadsetning_val in ["Annað", "Other"]:
                stadsetning = st.text_input("Sláðu inn staðsetningu")
                km_fra_thorlakshofn = st.number_input("Km frá Þorlákshöfn", min_value=0.0)
            else:
                stadsetning = stadsetning_val
                km_fra_thorlakshofn = afhendingarstaedir[stadsetning_val]

        verkkaupi = st.text_input("Verkkaupi / Client")

        submitted = st.form_submit_button("Reikna tilboð")

    if submitted:
        modules = {
            "3m": modul3,
            "2m": modul2,
            "1m": modul1,
            "0.5m": modul_half
        }

        if all(v == 0 for v in modules.values()):
            st.warning("Vinsamlegast veldu einingargildi svo hægt sé að reikna tilboðið.")
        elif stadsetning_val in ["Annað", "Other"] and km_fra_thorlakshofn == 0:
            st.warning("Vinsamlegast sláðu inn km fjarlægð ef þú valdir 'Annað'.")
        else:
            try:
                response = requests.get("https://api.frankfurter.app/latest?from=EUR&to=ISK", timeout=5)
                eur_to_isk = response.json()['rates']['ISK']
            except:
                eur_to_isk = 146

            result = calculate_offer(modules, km_fra_thorlakshofn, eur_to_isk)

            st.markdown("### Niðurstöður")
            st.write(f"**Heildarfermetrar:** {result['heildarfm']:.2f} fm")
            st.write(f"**Heildarþyngd:** {result['heildarthyngd']:,.0f} kg")
            st.write(f"**Afsláttur:** {int(result['afslattur'] * 100)}%")
            st.write(f"**Kaupverð eininga:** {result['heildarkostnadur_einingar']:,.0f} kr.")
            st.write(f"**Kostnaðarverð á fermetra:** {result['kostnadur_per_fm']:,.0f} kr.")
            st.write(f"**Flutningur til Íslands:** {result['flutningur_til_islands']:,.0f} kr.")
            st.write(f"**Sendingarkostnaður innanlands:** {result['sendingarkostnadur']:,.0f} kr.")
            st.write(f"**Samtals breytilegur kostnaður:** {result['samtals_breytilegur']:,.0f} kr.")
            st.write(f"**Úthlutaður fastur kostnaður:** {result['uthlutadur_fastur_kostnadur']:,.0f} kr.")
            st.write(f"**Álagsstuðull:** {result['alagsstudull']:.2f}")
            st.write(f"**Arðsemiskrafa:** {int(result['asemiskrafa'] * 100)}%")
            st.write(f"**Tilboðsverð (ISK):** {result['tilbod']:,.0f} kr.")
            st.write(f"**Tilboðsverð (EUR):** €{result['tilbod_eur']:,.2f}")

            pdf_bytes = generate_offer_pdf(verkkaupi, stadsetning, result)
            st.download_button(
                label="📄 Sækja PDF tilboð" if language == "Íslenska" else "📄 Download offer PDF",
                data=pdf_bytes,
                file_name=f"tilbod_{verkkaupi}.pdf",
                mime="application/pdf"
            )
