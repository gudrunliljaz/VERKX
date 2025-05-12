import streamlit as st
import pandas as pd
import numpy as np
from verkx_code import main_forecast, main_opperational_forecast, calculate_offer, generate_offer_pdf
import requests
from datetime import date
from io import BytesIO

st.set_page_config(page_title="Cubit", page_icon="cubitlogo.png", layout="wide")

# --- Sidebar ---
with st.sidebar:
    language = st.selectbox("Language", ["Íslenska", "English"], index=0)
    page = st.radio(
        "Veldu síðu / Choose page",
        ["Eftirspurnarspá", "Tilboðsreiknivél", "Rekstrarspá"] if language == "Íslenska"
        else ["Demand Forecast", "Quotation Calculator", "Operational Forecast"]
    )

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
        "error": "Villa kom upp",
        "profitmargin": "Arðsemiskrafa (%)"
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
        "error": "An error occurred",
        "profitmargin": "Profit Margin (%)"
    }
}


if ("Eftirspurnarspá" in page and language == "Íslenska") or ("Demand Forecast" in page and language == "English"):
    st.title(labels[language]['title'])

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
                df, figures, used_years = main_forecast(housing_type, region, future_years, market_share)

                if used_years < future_years:
                    st.warning(labels[language]["warning"].format(used_years))

                tabs = st.tabs([labels[language]["result_tab"], labels[language]["download_tab"]])

                with tabs[0]:
                    st.subheader(labels[language]["table_title"])
                    if language == "English":
                        df.columns = df.columns.str.replace("Ár", "Year")
                        df.columns = df.columns.str.replace("Fortíðargögn spá", "Historical Forecast")
                        df.columns = df.columns.str.replace("Framtíðarspá", "Future Forecast")
                        df.columns = df.columns.str.replace("Meðaltal", "Average")

                    st.dataframe(df.set_index(df.columns[0]))

                    st.subheader(labels[language]["distribution"])
                    for fig in figures:
                        st.pyplot(fig)

                with tabs[1]:
                    csv = df.to_csv(index=False).encode("utf-8-sig")
                    st.download_button(labels[language]["download_button"], csv, labels[language]["download_name"], "text/csv")

            except Exception as e:
                st.error(f"{labels[language]['error']}: {e}")

elif "Rekstrarspá" in page or "Operational Forecast" in page:
    st.title("Rekstrarspá allra markaða" if language == "Íslenska" else "Operational Forecast")

    st.subheader("Arðsemiskrafa (%)" if language == "Íslenska" else "Profit Margin (%)")
    col1, col2, col3, col4 = st.columns(4)
    margin_2025 = col1.slider("2025", 0, 100, 15) / 100
    margin_2026 = col2.slider("2026", 0, 100, 15) / 100
    margin_2027 = col3.slider("2027", 0, 100, 15) / 100
    margin_2028 = col4.slider("2028", 0, 100, 15) / 100

    if st.button("Keyra rekstrarspá" if language == "Íslenska" else "Run forecast", key="run_all_markets_forecast_button"):
        with st.spinner("Reikna..." if language == "Íslenska" else "Calculating..."):
            try:
                df_units, df_cost = main_opperational_forecast(
                    past_file="data/GÖGN_VERKX.xlsx",
                    future_file="data/Framtidarspa.xlsx",
                    share_file="data/markadshlutdeild.xlsx",
                    margin_2025=margin_2025,
                    margin_2026=margin_2026,
                    margin_2027=margin_2027,
                    margin_2028=margin_2028
                )

                if df_units is not None and not df_units.empty:
                    st.success("Lokið!" if language == "Íslenska" else "Done!")

                    rename_units = {
                        'ár': "Ár" if language == "Íslenska" else "Year",
                        'einingar': "Cubit einingar" if language == "Íslenska" else "Cubit Units",
                        'heildarfermetrar': "Heildarfermetrar" if language == "Íslenska" else "Total sqm",
                        '½_módúla einingar': "Hálf eining" if language == "Íslenska" else "Half a unit",
                        '1_módúla einingar': "Ein einingar" if language == "Íslenska" else "One unit",
                        '2_módúla einingar': "Tvær einingar" if language == "Íslenska" else "Two units",
                        '3_módúla einingar': "Þrjár einingar" if language == "Íslenska" else "Three units"
                    }

                    rename_cost = {
                        'kostnaður_½_módúla': "Kostnaður - hálf eining" if language == "Íslenska" else "Cost - half a module",
                        'kostnaður_1_módúla': "Kostnaður - ein eining" if language == "Íslenska" else "Cost - one module",
                        'kostnaður_2_módúla': "Kostnaður - tvær einingarr" if language == "Íslenska" else "Cost - two modules",
                        'kostnaður_3_módúla': "Kostnaður - þrjár einingar" if language == "Íslenska" else "Cost - three modules",
                        'kostnaðarverð eininga': "Kostnaðarverð eininga" if language == "Íslenska" else "Unit cost",
                        'flutningskostnaður': "Flutningskostnaður" if language == "Íslenska" else "Shipping to Iceland",
                        'afhending innanlands': "Afhending innanlands" if language == "Íslenska" else "Domestic delivery",
                        'fastur kostnaður': "Fastur kostnaður" if language == "Íslenska" else "Fixed cost",
                        'heildarkostnaður': "Heildarkostnaður" if language == "Íslenska" else "Total cost",
                        'arðsemiskrafa': "Arðsemiskrafa" if language == "Íslenska" else "Profit margin",
                        'tekjur': "Tekjur" if language == "Íslenska" else "Revenue",
                        'hagnaður': "Hagnaður" if language == "Íslenska" else "Profit"
                    }

                    df_units_disp = df_units.rename(columns=rename_units)
                    df_cost_disp = df_cost.rename(columns=rename_cost)

                    st.subheader("1. Einingafjöldi og fermetrar" if language == "Íslenska" else "1. Units and square meters")
                    st.dataframe(df_units_disp)

                    st.subheader("2. Kostnaður, tekjur og hagnaður" if language == "Íslenska" else "2. Cost, revenue, and profit")
                    st.dataframe(df_cost_disp)

                    st.download_button("Sækja CSV (einingar)" if language == "Íslenska" else "Download CSV (units)",
                                       df_units_disp.to_csv(index=False).encode("utf-8-sig"),
                                       file_name="einingar.csv",
                                       mime="text/csv")

                    st.download_button("Sækja CSV (kostnaður)" if language == "Íslenska" else "Download CSV (cost)",
                                       df_cost_disp.to_csv(index=False).encode("utf-8-sig"),
                                       file_name="kostnadur.csv",
                                       mime="text/csv")
                else:
                    st.warning("Engin gögn fundust." if language == "Íslenska" else "No data found.")

            except Exception as e:
                st.error(f"Villa við útreikning: {e}" if language == "Íslenska" else f"Error during calculation: {e}")

elif "Tilboðsreiknivél" in page or "Quotation Calculator" in page:
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
            modul3 = st.number_input("Þrjár einingar" if language == "Íslenska" else "Three Modules", min_value=0, value=0)
        with col2:
            modul2 = st.number_input("Tvær einingar" if language == "Íslenska" else "Two Modules", min_value=0, value=0)
        with col3:
            modul1 = st.number_input("Ein eining" if language == "Íslenska" else "One Module", min_value=0, value=0)
        with col4:
            modul_half = st.number_input("Hálf eining" if language == "Íslenska" else "Half a Module", min_value=0, value=0)

        afhendingarstaedir = afhendingar_map[language]
        col5, col6 = st.columns(2)
        with col5:
            stadsetning_val = st.selectbox("Afhendingarstaður" if language == "Íslenska" else "Delivery Location", list(afhendingarstaedir.keys()))
        with col6:
            if stadsetning_val in ["Annað", "Other"]:
                stadsetning = st.text_input("Sláðu inn staðsetningu" if language == "Íslenska" else "Please enter location")
                km_fra_thorlakshofn = st.number_input("Km frá Þorlákshöfn" if language == "Íslenska" else "Km from Þorlákshöfn", min_value=0.0)
            else:
                stadsetning = stadsetning_val
                km_fra_thorlakshofn = afhendingarstaedir[stadsetning_val]

        verkkaupi = st.text_input("Verkkaupi" if language == "Íslenska" else "Client")
        submitted = st.form_submit_button("Reikna tilboð" if language == "Íslenska" else "Calculate offer")

    if submitted:
        modules = {"3m": modul3, "2m": modul2, "1m": modul1, "0.5m": modul_half}
        if all(v == 0 for v in modules.values()):
            st.warning("Vinsamlegast veldu einingar." if language == "Íslenska" else "Please select modules.")
        elif stadsetning_val in ["Annað", "Other"] and km_fra_thorlakshofn == 0:
            st.warning("Vinsamlegast sláðu inn km." if language == "Íslenska" else "Please enter km.")
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
            st.write(f"**Arðsemiskrafa:** {int(result['arðsemiskrafa'] * 100)}%" if language == "Íslenska" else f"**Profit margin:** {int(result['arðsemiskrafa'] * 100)}%")
            st.write(f"**Tilboðsverð (ISK):** {result['tilbod']:,.0f} kr." if language == "Íslenska" else f"**Offer price (ISK):** {result['tilbod']:,.0f} ISK")
            st.write(f"**Tilboðsverð (EUR):** €{result['tilbod_eur']:,.2f}" if language == "Íslenska" else f"**Offer price (EUR):** €{result['tilbod_eur']:,.2f}")


            try:
                from unicodedata import normalize
                hreinsadur_verkkaupi = normalize('NFKD', verkkaupi).encode('ascii', 'ignore').decode('ascii')
                hreinsud_stadsetning = normalize('NFKD', stadsetning).encode('ascii', 'ignore').decode('ascii')
                pdf_bytes = generate_offer_pdf(hreinsadur_verkkaupi, hreinsud_stadsetning, result, language)
                st.download_button(
                    label="Sækja PDF tilboð" if language == "Íslenska" else "Download offer PDF",
                    data=pdf_bytes,
                    file_name=f"tilbod_{hreinsadur_verkkaupi}.pdf",
                    mime="application/pdf"
                )
            except UnicodeEncodeError:
                st.error("Villa við útgáfu PDF" if language == "Íslenska" else "PDF generation error")








