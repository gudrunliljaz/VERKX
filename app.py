import streamlit as st
import pandas as pd
import numpy as np
from verkx_code import main_forecast_logic, main_forecast_logic_from_excel, calculate_offer, generate_offer_pdf  
import requests


# --- Page config ---
st.set_page_config(page_title="Cubit", page_icon="andreim.png", layout="wide")

# --- Sidebar ---
with st.sidebar:
    language = st.selectbox("Language", ["Íslenska", "English"], index=0)
    page = st.radio("Veldu síðu/Choose page",
        ["Spálíkan", "Tilboðsreiknivél", "Rekstrarspá"] if language == "Íslenska"
        else ["Forecast Model", "Quotation Calculator", "All Markets Forecast"])

# --- Labels ---
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

quotation_labels = {
    "Íslenska": {
        "title": "Tilboðsreiknivél",
        "form_title": "Gögn um einingar",
        "input_section": "Aðrar upplýsingar",
        "3 Modules": "Þrjár einingar",
        "2 Modules": "Tvær einingar",
        "1 Module": "Ein eining",
        "0.5 Module": "Hálf eining",
        "calculate": "Reikna tilboð",
        "result_title": "Niðurstöður",
        "client": "Verkkaupi",
        "location": "Staðsetning afhendingar",
        "distance": "Km frá Þorlákshöfn",
        "area": "Heildarfermetrar",
        "weight": "Heildarþyngd",
        "shipping_is": "Flutningur til Íslands",
        "delivery": "Sendingarkostnaður innanlands",
        "variable_cost": "Samtals breytilegur kostnaður",
        "allocated_fixed": "Úthlutaður fastur kostnaður",
        "markup": "Álagsstuðull",
        "offer_price": "Tilboðsverð"
    },
    "English": {
        "title": "Quotation Calculator",
        "form_title": "Unit data",
        "input_section": "Other information",
        "3 Modules": "Three Modules",
        "2 Modules": "Two Modules",
        "1 Module": "One Module",
        "0.5 Module": "Half Module",
        "calculate": "Calculate offer",
        "result_title": "Results",
        "client": "Client",
        "location": "Delivery location",
        "distance": "Km from Þorlákshöfn",
        "area": "Total sqm",
        "weight": "Total weight",
        "shipping_is": "Shipping to Iceland",
        "delivery": "Domestic delivery",
        "variable_cost": "Total variable cost",
        "allocated_fixed": "Allocated fixed cost",
        "markup": "Markup factor",
        "offer_price": "Offer price"
    }
}

# --- Forecast Model ---
if "Spálíkan" in page or "Forecast" in page:
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

# 2.--- Tilboðsreiknivél ---
if ("Tilboðsreiknivél" in page or "Quotation" in page):
    q = quotation_labels[language]
    st.markdown(f"<h1>{q['title']}</h1><hr>", unsafe_allow_html=True)

    afhendingar_map = {
        "Íslenska": {
            "Höfuðborgarsvæðið": 60, "Selfoss": 30, "Hveragerði": 40, "Akranes": 100,
            "Borgarnes": 150, "Stykkishólmur": 260, "Ísafjörður": 570, "Akureyri": 490,
            "Húsavík": 520, "Sauðárkrókur": 450, "Egilsstaðir": 650, "Seyðisfjörður": 670,
            "Neskaupsstaður": 700, "Eskifjörður": 690, "Fáskrúðsfjörður": 680, "Höfn": 450,
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
        st.markdown(f"### {q['form_title']}")
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            modul3 = st.number_input(q["3 Modules"], min_value=0, value=0)
        with col2:
            modul2 = st.number_input(q["2 Modules"], min_value=0, value=0)
        with col3:
            modul1 = st.number_input(q["1 Module"], min_value=0, value=0)
        with col4:
            modul_half = st.number_input(q["0.5 Module"], min_value=0, value=0)

        st.markdown(f"### {q['input_section']}")
        col5, col6 = st.columns(2)
        with col5:
            verkkaupi = st.text_input(q["client"])

        afhendingarstaedir = afhendingar_map[language]
        with col6:
            stadsetning_val = st.selectbox(q["location"], list(afhendingarstaedir.keys()))
            if stadsetning_val in ["Annað", "Other"]:
                stadsetning = st.text_input(q["location"])
                km_fra_thorlakshofn = st.number_input("Km frá Þorlákshöfn", min_value=0.0)
            else:
                stadsetning = stadsetning_val
                km_fra_thorlakshofn = afhendingarstaedir[stadsetning]

        submitted = st.form_submit_button(q["calculate"])

    if submitted:
        modules = {
            "3m": modul3,
            "2m": modul2,
            "1m": modul1,
            "0.5m": modul_half
        }

        if all(v == 0 for v in modules.values()):
            st.warning("Vinsamlegast veldu einingargildi svo hægt sé að reikna tilboðið.")
        elif stadsetning_val == "Annað" and km_fra_thorlakshofn == 0:
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
            label="📄 Sækja PDF tilboð",
            data=pdf_bytes,
            file_name=f"tilbod_{verkkaupi}.pdf",
            mime="application/pdf"
        )




# 3. All Markets Forecast
# =====================
elif "Rekstrarspá" in page or "All Markets Forecast" in page:
    if language == "Íslenska":
        st.title("Rekstrarspá allra markaða")
        st.markdown("Þessi spá notar meðaltöl fortíðar- og framtíðarspáa með aðlögun fyrir markaðshlutdeild og sviðsmynd.")
        button_label = "Keyra rekstrarspá"
        download_label = "Sækja CSV"
        success_msg = "Lokið! Hér að neðan eru spár fyrir alla markaði."
        warning_msg = "Engin gögn fundust eða ekkert sniðug spá tiltæk."
        error_msg = "Villa við útreikning"
        slider_label = "Arðsemiskrafa (%)"
    else:
        st.title("All Markets Forecast")
        st.markdown("This forecast uses adjusted averages of past and future predictions, based on market share and scenario.")
        button_label = "Run forecast"
        download_label = "Download CSV"
        success_msg = "Done! Below are the forecasts for all markets."
        warning_msg = "No data found or no valid forecast available."
        error_msg = "Error in calculation"
        slider_label = "Profit margin (%)"

    margin = st.slider(slider_label, 0, 100, 15)
    margin_decimal = margin / 100

    if st.button(button_label, key="run_all_markets_forecast_button"):
        with st.spinner("Reikna..." if language == "Íslenska" else "Calculating..."):
            try:
                df = main_forecast_logic_from_excel(
                    past_file="data/GÖGN_VERKX.xlsx",
                    future_file="data/Framtidarspa.xlsx",
                    share_file="data/markadshlutdeild.xlsx",
                    profit_margin=margin_decimal
                )
                if df is not None and not df.empty:
                    st.success(success_msg)
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




