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

# --- Labels dictionary ---
labels = {
    "Íslenska": {
        "title": "Eftirspurnarspá",
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
        "title": "Demand Forecast",
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

# --- Forecast model ---
if ("Eftirspurnarspá" in page and language == "Íslenska") or ("Demand Forecast" in page and language == "English"):
    st.header(labels[language]['title'])

    housing_map = {
        "Íslenska": ["Íbúðir", "Leikskólar", "Gistirými", "Elliheimili", "Atvinnuhús"],
        "English": ["Apartments", "Kindergartens", "Accommodation facilities", "Nursing homes", "Commercial buildings"]
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
    if language == "Íslenska":
        st.title("Rekstrarspá allra markaða")
        button_label = "Keyra rekstrarspá"
        download_label = "Sækja CSV"
        success_msg = "Lokið! Hér að neðan eru spár fyrir alla markaði."
        warning_msg = "Engin gögn fundust."
        error_msg = "Villa við útreikning"
        margin_label = "Arðsemiskrafa eftir ári"
    else:
        st.title("All Markets Forecast")
        button_label = "Run forecast"
        download_label = "Download CSV"
        success_msg = "Done! Below are the forecasts for all markets."
        warning_msg = "No data found."
        error_msg = "Error in calculation"
        margin_label = "Profit margin per year"

    if st.button(button_label, key="run_all_markets_forecast_button"):
        with st.spinner("Reikna..." if language == "Íslenska" else "Calculating..."):
            try:
                df = main_forecast_logic_from_excel(
                    past_file="data/GÖGN_VERKX.xlsx",
                    future_file="data/Framtidarspa.xlsx",
                    share_file="data/markadshlutdeild.xlsx",
                    profit_margin=0.0  # Við notum custom margins fyrir hvert ár
                )

                if df is not None and not df.empty:
                    st.success(success_msg)

                    st.subheader(margin_label)
                    year_rates = {}
                    for year in df["Ár"]:
                        label = f"Arðsemiskrafa fyrir {year}" if language == "Íslenska" else f"Profit margin for {year}"
                        key = f"margin_{year}"
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
                        label=download_label,
                        data=df.to_csv(index=False).encode("utf-8-sig"),
                        file_name="heildarspa.csv",
                        mime="text/csv"
                    )
                else:
                    st.warning(warning_msg)
            except Exception as e:
                st.error(f"{error_msg}: {e}")

# --- Quotation calculator ---
elif "Tilboðsreiknivél" in page or "Quotation" in page:
    st.header("Tilboðsreiknivél" if language == "Íslenska" else "Quotation Calculator")

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
        if language == "Íslenska":
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                modul3 = st.number_input("Þrjár einingar", min_value=0, value=0)
            with col2:
                modul2 = st.number_input("Tvær einingar", min_value=0, value=0)
            with col3:
                modul1 = st.number_input("Ein eining", min_value=0, value=0)
            with col4:
                modul_half = st.number_input("Hálf eining", min_value=0, value=0)
        else:
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                modul3 = st.number_input("Three Modules", min_value=0, value=0)
            with col2:
                modul2 = st.number_input("Two Modules", min_value=0, value=0)
            with col3:
                modul1 = st.number_input("One Module", min_value=0, value=0)
            with col4:
                modul_half = st.number_input("Half a Module", min_value=0, value=0)
                

        afhendingarstaedir = afhendingar_map[language]
        col5, col6 = st.columns(2)
        with col5:
            if language == "Íslenska":
                stadsetning_val = st.selectbox("Afhendingarstaður", list(afhendingarstaedir.keys()))
            else: 
                stadsetning_val = st.selectbox("Delivery Location", list(afhendingarstaedir.keys())) 
        with col6:
            if stadsetning_val in ["Annað", "Other"]:
                if language == "Íslenska":
                    stadsetning = st.text_input("Sláðu inn staðsetningu")
                    km_fra_thorlakshofn = st.number_input("Km frá Þorlákshöfn", min_value=0.0)
                else:
                    stadsetning = st.text_input("Address")
                    km_fra_thorlakshofn = st.number_input("Km from Þorlákshöfn", min_value=0.0)
            else:
                stadsetning = stadsetning_val
                km_fra_thorlakshofn = afhendingarstaedir[stadsetning_val]

        if language == "Íslenska":
            verkkaupi = st.text_input("Verkkaupi")
        else:
            verkkaupi = st.text_input("Client")

        if language == "Íslenska":
            submitted = st.form_submit_button("Reikna tilboð")
        else:
            submitted = st.form_submit_button("Calculate offer")

    if submitted:
        modules = {
            "3m": modul3,
            "2m": modul2,
            "1m": modul1,
            "0.5m": modul_half
        }

        if all(v == 0 for v in modules.values()):
            if language == "Íslenska":
                st.warning("Vinsamlegast veldu einingargildi svo hægt sé að reikna tilboðið.")
            else:
                st.warning("Please select unit values in order to calculate the offer.")
        elif stadsetning_val in ["Annað", "Other"] and km_fra_thorlakshofn == 0:
            if language == "Íslenska":
                st.warning("Vinsamlegast sláðu inn km fjarlægð ef þú valdir 'Annað'.")
            else:
                st.warning("Pleaseselect km distance if you chose 'Other'.")
        else:
            try:
                response = requests.get("https://api.frankfurter.app/latest?from=EUR&to=ISK", timeout=5)
                eur_to_isk = response.json()['rates']['ISK']
            except:
                eur_to_isk = 146

            result = calculate_offer(modules, km_fra_thorlakshofn, eur_to_isk)

            st.markdown("### Niðurstöður" if language == "Íslenska" else "### Results")
            st.write(f"**Heildarfermetrar:** {result['heildarfm']:.2f} fm" if language == "Íslenska" else f"**Total area:** {result['heildarfm']:.2f} sqm")
            st.write(f"**Heildarþyngd:** {result['heildarthyngd']:,.0f} kg" if language == "Íslenska" else f"**Total weight:** {result['heildarthyngd']:,.0f} kg")
            st.write(f"**Afsláttur:** {int(result['afslattur'] * 100)}%" if language == "Íslenska" else f"**Discount:** {int(result['afslattur'] * 100)}%")
            st.write(f"**Kaupverð eininga:** {result['heildarkostnadur_einingar']:,.0f} kr." if language == "Íslenska" else f"**Unit purchase cost:** {result['heildarkostnadur_einingar']:,.0f} ISK")
            st.write(f"**Kostnaðarverð á fermetra:** {result['kostnadur_per_fm']:,.0f} kr." if language == "Íslenska" else f"**Cost per sqm:** {result['kostnadur_per_fm']:,.0f} ISK")
            st.write(f"**Flutningur til Íslands:** {result['flutningur_til_islands']:,.0f} kr." if language == "Íslenska" else f"**Shipping to Iceland:** {result['flutningur_til_islands']:,.0f} ISK")
            st.write(f"**Sendingarkostnaður innanlands:** {result['sendingarkostnadur']:,.0f} kr." if language == "Íslenska" else f"**Domestic delivery:** {result['sendingarkostnadur']:,.0f} ISK")
            st.write(f"**Samtals breytilegur kostnaður:** {result['samtals_breytilegur']:,.0f} kr." if language == "Íslenska" else f"**Total variable cost:** {result['samtals_breytilegur']:,.0f} ISK")
            st.write(f"**Úthlutaður fastur kostnaður:** {result['uthlutadur_fastur_kostnadur']:,.0f} kr." if language == "Íslenska" else f"**Allocated fixed cost:** {result['uthlutadur_fastur_kostnadur']:,.0f} ISK")
            st.write(f"**Álagsstuðull:** {result['alagsstudull']:.2f}" if language == "Íslenska" else f"**Markup factor:** {result['alagsstudull']:.2f}")
            st.write(f"**Arðsemiskrafa:** {int(result['asemiskrafa'] * 100)}%" if language == "Íslenska" else f"**Profit margin:** {int(result['asemiskrafa'] * 100)}%")
            st.write(f"**Tilboðsverð (ISK):** {result['tilbod']:,.0f} kr." if language == "Íslenska" else f"**Offer price (ISK):** {result['tilbod']:,.0f} ISK")
            st.write(f"**Tilboðsverð (EUR):** €{result['tilbod_eur']:,.2f}" if language == "Íslenska" else f"**Offer price (EUR):** €{result['tilbod_eur']:,.2f}")


            try:
                from unicodedata import normalize
                # Hreinsum öll séríslensk tákn úr strengjum
                hreinsad_nafn = normalize('NFKD', verkkaupi).encode('ascii', 'ignore').decode('ascii')
                hreinsud_stadsetning = normalize('NFKD', stadsetning).encode('ascii', 'ignore').decode('ascii')
                pdf_bytes = generate_offer_pdf(hreinsad_nafn, hreinsud_stadsetning, result)
                st.download_button(
                    label="Sækja PDF tilboð" if language == "Íslenska" else "Download offer PDF",
                    data=pdf_bytes,
                    file_name=f"tilbod_{hreinsad_nafn}.pdf",
                    mime="application/pdf"
                )
            except UnicodeEncodeError:
                st.error("Villa við útgáfu PDF skjals.")








