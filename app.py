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

# =====================
# 2. Quotation Calculator
# =====================
elif "Tilboðsreiknivél" in page or "Quotation" in page:
    q = quotation_labels[language]
    st.header(q["title"])

    with st.form("tilbod_form"):
        st.subheader(q["form_title"])
        col1, col2, col3, col4 = st.columns(4)
        with col1: m3 = st.number_input(q["3 Modules"], 0, value=0)
        with col2: m2 = st.number_input(q["2 Modules"], 0, value=0)
        with col3: m1 = st.number_input(q["1 Module"], 0, value=0)
        with col4: m05 = st.number_input(q["0.5 Module"], 0, value=0)

        st.subheader(q["input_section"])
        col5, col6, col7 = st.columns(3)
        with col5: client = st.text_input(q["client"])
        with col6: location_input = st.text_input(q["location"])

        loc_options = {
            "Höfuðborgarsvæðið": 60, "Selfoss": 30, "Hveragerði": 40, "Akranes": 100,
            "Borgarnes": 150, "Stykkishólmur": 260, "Ísafjörður": 570, "Akureyri": 490,
            "Húsavík": 520, "Sauðárkrókur": 450, "Egilsstaðir": 650, "Seyðisfjörður": 670,
            "Neskaupsstaður": 700, "Eskifjörður": 690, "Fáskrúðsfjörður": 680,
            "Höfn": 450, "Vestmannaeyjar": 90, "Keflavík": 90, "Annað": None
        }

        with col7:
            if loc_sel == "Annað":
                location = st.text_input("Nafn staðar")
                km = st.number_input("Fjarlægð frá Þorlákshöfn (km)", 0.0, value=0.0)
            else:
                location = loc_sel
                km = loc_options[loc_sel]

        submitted = st.form_submit_button(q["calculate"])

    # === Skilyrði: ekki reikna ef valið er 'Annað' og km er 0
    if submitted and (loc_sel != "Annað" or km > 0):
        try:
            fx = requests.get("https://api.frankfurter.app/latest?from=EUR&to=ISK", timeout=5).json()
            eur = fx["rates"]["ISK"]
        except:
            eur = 146

        mods = {
            "3m": {"n": m3, "fm": 19.5, "verð": 1800, "kg": 9750},
            "2m": {"n": m2, "fm": 13.0, "verð": 1950, "kg": 6500},
            "1m": {"n": m1, "fm": 6.5, "verð": 2050, "kg": 3250},
            "0.5m": {"n": m05, "fm": 3.25, "verð": 2175, "kg": 1625},
        }

        fm = sum(m["n"] * m["fm"] for m in mods.values())
        kg = sum(m["n"] * m["kg"] for m in mods.values())
        afsl = 0.10 if fm >= 650 else 0
        if fm >= 1300:
            afsl = min(0.15 + ((fm - 1300) // 325) * 0.01, 0.18)

        einingakostn = sum(m["n"] * m["fm"] * m["verð"] * eur * (1 - afsl) for m in mods.values())
        flutn = fm * 74000
        sending = fm * km * 8
        breytilegur = einingakostn + flutn + sending
        fastur = (fm / 2400) * 34800000
        markup = 1 + (fastur / breytilegur)
        verð = breytilegur * markup * 1.15
        verð_eur = verð / eur

        st.success(f"Tilboð fyrir {client}")
        st.write(f"**{q['location']}:** {location}")
        st.write(f"**{q['area']}:** {fm:.2f} fm")
        st.write(f"**{q['weight']}:** {kg:,.0f} kg")
        st.write(f"**Afsláttur:** {int(afsl * 100)}%")
        st.write(f"**{q['shipping_is']}:** {flutn:,.0f} kr")
        st.write(f"**{q['delivery']}:** {sending:,.0f} kr")
        st.write(f"**{q['variable_cost']}:** {breytilegur:,.0f} kr")
        st.write(f"**{q['allocated_fixed']}:** {fastur:,.0f} kr")
        st.write(f"**{q['markup']}:** {markup:.2f}")
        st.write(f"**{q['offer_price']}:** {verð:,.0f} kr / €{verð_eur:,.2f}")
    
    elif submitted:
        st.warning("Vinsamlegast sláðu inn km fjarlægð ef þú valdir 'Annað'.")

# 3. All Markets Forecast
# =====================
elif "Heildarspá" in page or "All Markets Forecast" in page:
    st.title("📊 Heildarspá")
    margin = st.slider("Álag / profit margin (%)", 0, 100, 15) / 100
    if st.button("Keyra heildarspá"):
        with st.spinner("Reikna..."):
            try:
                df = main_forecast_logic_from_excel(
                    "data/GÖGN_VERKX.xlsx",
                    "data/Framtidarspa.xlsx",
                    "data/markadshlutdeild.xlsx",
                    profit_margin=margin
                )
                if df is not None:
                    st.success("Lokið!")
                    st.dataframe(df.set_index("ár"))
                    st.download_button("Sækja CSV", df.to_csv(index=False).encode("utf-8-sig"),
                                       "heildarspa.csv", "text/csv")
                else:
                    st.warning("Engin gögn fundust.")
            except Exception as e:
                st.error(f"Villa: {e}")




