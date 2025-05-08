import streamlit as st
import pandas as pd
import numpy as np
from verkx_code import main_forecast_logic, main_forecast_logic_from_excel
from datetime import date
import requests
from io import BytesIO
from fpdf import FPDF

# Page config
st.set_page_config(page_title="Cubit", page_icon="andreim.png", layout="wide")

# --- Sidebar language and page selection ---
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
        "download_button": "Download CSV file",
        "download_name": "forecast_results.csv",
        "warning": "Only {} years found in future data — using only those.",
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
        "offer_price": "Tilboðsverð (með 15% ásemiskröfu)"
    },
    "English": {
        "title": "Quotation Calculator",
        "form_title": "Unit data",
        "input_section": "Other information",
        "3 Modules": "Three Modules",
        "2 Modules": "Two Modules",
        "1 Module": "One Module",
        "0.5 Module": "Half a Module",
        "calculate": "Calculate offer",
        "result_title": "Results",
        "client": "Client",
        "location": "Delivery location",
        "distance": "Km from Þorlákshöfn",
        "area": "Total square meters",
        "weight": "Total weight",
        "shipping_is": "Shipping to Iceland",
        "delivery": "Domestic delivery cost",
        "variable_cost": "Total variable cost",
        "allocated_fixed": "Allocated fixed cost",
        "markup": "Markup factor",
        "offer_price": "Offer price (with 15% markup)"
    }
}

# --- Quotation Calculator ---
if "Tilboðsreiknivél" in page or "Quotation" in page:
    q = quotation_labels[language]
    st.header(q["title"])

    delivery_options = {
        "Höfuðborgarsvæðið": 60,
        "Selfoss": 30,
        "Hveragerði": 40,
        "Akranes": 100,
        "Borgarnes": 150,
        "Stykkishólmur": 260,
        "Ísafjörður": 570,
        "Akureyri": 490,
        "Húsavík": 520,
        "Sauðárkrókur": 450,
        "Egilsstaðir": 650,
        "Seyðisfjörður": 670,
        "Neskaupsstaður": 700,
        "Eskifjörður": 690,
        "Fáskrúðsfjörður": 680,
        "Höfn": 450,
        "Vestmannaeyjar": 90,
        "Keflavík": 90,
        "Annað": None
    }

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

        with col7:
            loc_select = st.selectbox("Afhendingarstaður", delivery_options.keys())
            if loc_select == "Annað":
                location = st.text_input("Skrifaðu staðsetningu")
                km = st.number_input("Km frá Þorlákshöfn", min_value=0.0, value=0.0)
            else:
                location = loc_select
                km = delivery_options[loc_select]

        submitted = st.form_submit_button(q["calculate"])

        if submitted:
            if loc_select == "Annað" and km == 0:
                st.warning("Vinsamlegast sláðu inn fjarlægð í km áður en þú heldur áfram.")
            else:
                modules = {
                    "3m": {"count": m3, "sqm": 19.5, "eur": 1800, "kg": 9750},
                    "2m": {"count": m2, "sqm": 13.0, "eur": 1950, "kg": 6500},
                    "1m": {"count": m1, "sqm": 6.5, "eur": 2050, "kg": 3250},
                    "0.5m": {"count": m05, "sqm": 3.25, "eur": 2175, "kg": 1625},
                }

                sqm_total = sum(m["count"] * m["sqm"] for m in modules.values())
                weight = sum(m["count"] * m["kg"] for m in modules.values())

                try:
                    fx = requests.get("https://api.frankfurter.app/latest?from=EUR&to=ISK", timeout=5).json()
                    eur_to_isk = fx["rates"]["ISK"]
                except:
                    eur_to_isk = 146

                discount = 0.10 if sqm_total >= 650 else 0
                if sqm_total >= 1300:
                    discount = min(0.15 + ((sqm_total - 1300) // 325) * 0.01, 0.18)

                unit_cost = sum(m["count"] * m["sqm"] * m["eur"] * eur_to_isk * (1 - discount) for m in modules.values())
                shipping = sqm_total * 74000
                delivery = sqm_total * km * 8
                variable_total = unit_cost + shipping + delivery

                if variable_total > 0:
                    fixed = (sqm_total / 2400) * 34800000
                    markup = 1 + (fixed / variable_total)
                    final_price = variable_total * markup * 1.15
                    price_eur = final_price / eur_to_isk

                    st.success(f"**{q['client']}:** {client}")
                    st.write(f"**{q['location']}:** {location}")
                    st.write(f"**{q['area']}:** {sqm_total:.2f} fm")
                    st.write(f"**{q['weight']}:** {weight:,.0f} kg")
                    st.write(f"**Afsláttur:** {int(discount*100)}%")
                    st.write(f"**{q['shipping_is']}:** {shipping:,.0f} kr")
                    st.write(f"**{q['delivery']}:** {delivery:,.0f} kr")
                    st.write(f"**{q['variable_cost']}:** {variable_total:,.0f} kr")
                    st.write(f"**{q['allocated_fixed']}:** {fixed:,.0f} kr")
                    st.write(f"**{q['markup']}:** {markup:.2f}")
                    st.write(f"**{q['offer_price']}:** {final_price:,.0f} kr / €{price_eur:,.2f}")


