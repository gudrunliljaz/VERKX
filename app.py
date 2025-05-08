import streamlit as st
import pandas as pd
import numpy as np
from verkx_code import main_forecast_logic, main_forecast_logic_from_excel
from datetime import date
import requests
from io import BytesIO
from fpdf import FPDF

# --- Page config ---
st.set_page_config(page_title="Cubit", page_icon="andreim.png", layout="wide")

# --- Sidebar ---
with st.sidebar:
    language = st.selectbox("Language", ["Íslenska", "English"], index=0)
    page = st.radio("Veldu síðu/Choose page",
        ["Spálíkan", "Tilboðsreiknivél", "Heildarspá"] if language == "Íslenska"
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

        afhendingarstaedir = {
            "Höfuðborgarsvæðið": 60, "Selfoss": 30, "Hveragerði": 40, "Akranes": 100,
            "Borgarnes": 150, "Stykkishólmur": 260, "Ísafjörður": 570, "Akureyri": 490,
            "Húsavík": 520, "Sauðárkrókur": 450, "Egilsstaðir": 650, "Seyðisfjörður": 670,
            "Neskaupsstaður": 700, "Eskifjörður": 690, "Fáskrúðsfjörður": 680, "Höfn": 450,
            "Vestmannaeyjar": 90, "Keflavík": 90, "Annað": None
        }

        with col6:
            stadsetning_val = st.selectbox("Afhendingarstaður", list(afhendingarstaedir.keys()))
            if stadsetning_val == "Annað":
                stadsetning = st.text_input("Skrifaðu nafnið á afhendingarstað")
                km_fra_thorlakshofn = st.number_input(f"Hversu margir km eru í {stadsetning} frá Þorlákshöfn?", min_value=0.0, value=0.0)
            else:
                stadsetning = stadsetning_val
                km_fra_thorlakshofn = afhendingarstaedir[stadsetning]

        submitted = st.form_submit_button(q["calculate"])

    if submitted:
        try:
            response = requests.get("https://api.frankfurter.app/latest?from=EUR&to=ISK", timeout=5)
            eur_to_isk = response.json()['rates']['ISK']
        except:
            eur_to_isk = 146.0

        einingar = {
            "3m": {"fjoldi": modul3, "fm": 19.5, "verd_eur": 1800, "kg": 9750},
            "2m": {"fjoldi": modul2, "fm": 13, "verd_eur": 1950, "kg": 6500},
            "1m": {"fjoldi": modul1, "fm": 6.5, "verd_eur": 2050, "kg": 3250},
            "0.5m": {"fjoldi": modul_half, "fm": 3.25, "verd_eur": 2175, "kg": 1625},
        }

        heildarfm = sum(e["fjoldi"] * e["fm"] for e in einingar.values())
        heildarthyngd = sum(e["fjoldi"] * e["kg"] for e in einingar.values())

        afslattur = 0
        if heildarfm >= 650:
            afslattur = 0.10
        if heildarfm >= 1300:
            afslattur = 0.15 + ((heildarfm - 1300) // 325) * 0.01
            afslattur = min(afslattur, 0.18)

        heildarkostnadur_einingar = sum(
            e["fjoldi"] * e["fm"] * e["verd_eur"] * eur_to_isk * (1 - afslattur)
            for e in einingar.values()
        )
        kostnadur_per_fm = heildarkostnadur_einingar / heildarfm if heildarfm else 0

        flutningur_til_islands = heildarfm * 74000
        sendingarkostnadur = heildarfm * km_fra_thorlakshofn * 8
        samtals_breytilegur = heildarkostnadur_einingar + flutningur_til_islands + sendingarkostnadur

        fastur_kostnadur = 34800000
        heildarfm_arsins = 2400
        uthlutadur_fastur_kostnadur = (heildarfm / heildarfm_arsins) * fastur_kostnadur
        alagsstudull = 1 + (uthlutadur_fastur_kostnadur / samtals_breytilegur)
        asemiskrafa = 0.15
        tilbod = samtals_breytilegur * alagsstudull * (1 + asemiskrafa)
        tilbod_eur = tilbod / eur_to_isk

        st.markdown(f"### {q['result_title']}")
        st.write(f"**{q['client']}:** {verkkaupi}")
        st.write(f"**{q['location']}:** {stadsetning}")
        st.write(f"**{q['area']}:** {heildarfm:.2f} fm")
        st.write(f"**{q['weight']}:** {heildarthyngd:,.0f} kg")
        st.write(f"**Magnafsláttur:** {int(afslattur * 100)}%")
        st.write(f"**Kaupverð eininga:** {heildarkostnadur_einingar:,.0f} kr.")
        st.write(f"**Kostnaðarverð á fermetra:** {kostnadur_per_fm:,.0f} kr.")
        st.write(f"**{q['shipping_is']}:** {flutningur_til_islands:,.0f} kr.")
        st.write(f"**{q['delivery']}:** {sendingarkostnadur:,.0f} kr.")
        st.write(f"**{q['variable_cost']}:** {samtals_breytilegur:,.0f} kr.")
        st.write(f"**{q['allocated_fixed']}:** {uthlutadur_fastur_kostnadur:,.0f} kr.")
        st.write(f"**{q['markup']}:** {alagsstudull:.2f}")
        st.write(f"**Arðsemiskrafa:** {asemiskrafa*100:.0f}%")
        st.write(f"**{q['offer_price']}:** {tilbod:,.0f} kr. / €{tilbod_eur:,.2f}")

        # PDF útgáfa
        def to_latin1(s):
            return s.encode("latin-1", errors="replace").decode("latin-1")

        pdf = FPDF()
        pdf.add_page()
        try:
            pdf.image("assets/logo.png", x=10, y=8, w=40)
        except:
            pass

        pdf.set_font("Arial", "B", 16)
        pdf.ln(15)
        pdf.cell(200, 10, txt=to_latin1("Tilboð frá Cubit"), ln=True, align='C')

        pdf.set_font("Arial", size=12)
        pdf.ln(10)
        pdf.cell(200, 10, txt=to_latin1(f"Verkkaupi: {verkkaupi}"), ln=True)
        pdf.cell(200, 10, txt=to_latin1(f"Afhendingarstaður: {stadsetning}"), ln=True)
        pdf.cell(200, 10, txt=f"Dags: {date.today()}", ln=True)

        pdf.ln(10)
        data = [
            ("Heildarfermetrar", f"{heildarfm:.2f} fm"),
            ("Heildarþyngd", f"{heildarthyngd:,.0f} kg"),
            ("Kaupverð eininga", f"{heildarkostnadur_einingar:,.0f} kr"),
            ("Kostnaðarverð á fm", f"{kostnadur_per_fm:,.0f} kr"),
            ("Magnafsláttur", f"{int(afslattur * 100)}%"),
            ("Flutningur til Íslands", f"{flutningur_til_islands:,.0f} kr"),
            ("Sendingarkostnaður innanlands", f"{sendingarkostnadur:,.0f} kr"),
            ("Samtals breytilegur kostnaður", f"{samtals_breytilegur:,.0f} kr"),
            ("Úthlutaður fastur kostnaður", f"{uthlutadur_fastur_kostnadur:,.0f} kr"),
            ("Álagsstuðull", f"{alagsstudull:.2f}"),
            ("Arðsemiskrafa", f"{int(asemiskrafa * 100)}%"),
            ("Tilboðsverð (ISK)", f"{tilbod:,.0f} kr"),
            ("Tilboðsverð (EUR)", f"€{tilbod_eur:,.2f}")
        ]

        for label, value in data:
            pdf.cell(200, 10, txt=to_latin1(f"{label}: {value}"), ln=True)

        buffer = BytesIO()
        pdf.output(dest='S').encode('latin-1')
        buffer.write(pdf.output(dest='S').encode('latin-1'))

        st.download_button(
            label="📄 Sækja PDF tilboð",
            data=buffer.getvalue(),
            file_name=f"tilbod_{verkkaupi}.pdf",
            mime="application/pdf"
        )



# 3. All Markets Forecast
# =====================
# 3. All Markets Forecast
elif "Rekstrarspáspá" in page or "All Markets Forecast" in page:
    st.title("Rekstrarspá allra markaða")
    
    margin = st.slider("Arðsemiskrafa / Profit margin (%)", 0, 100, 15) / 100

    if st.button("Keyra heildarspá"):
        with st.spinner("Reikna..."):
            try:
                df = main_forecast_logic_from_excel(
                    past_file="data/GÖGN_VERKX.xlsx",
                    future_file="data/Framtidarspa.xlsx",
                    share_file="data/markadshlutdeild.xlsx",
                    profit_margin=margin
                )
                if df is not None:
                    st.success("Heildarspá lokið.")
                    st.dataframe(df.set_index("ár"))
                    csv = df.to_csv(index=False).encode("utf-8-sig")
                    st.download_button(
                        "Sækja CSV",
                        data=csv,
                        file_name="heildarspa.csv",
                        mime="text/csv"
                    )
                else:
                    st.warning("Engin gögn fundust til að spá.")
            except Exception as e:
                st.error(f"Villa við útreikning: {e}")



