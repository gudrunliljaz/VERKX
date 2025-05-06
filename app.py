import streamlit as st
import pandas as pd
import numpy as np
import datetime
from verkx_code import main_forecast_logic

# Page config
st.set_page_config(page_title="Cubit", page_icon="assets/logo.png", layout="wide")

# --- Tungumálaval efst ---
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

with st.sidebar:
    st.markdown('<div class="language-dropdown">', unsafe_allow_html=True)
    language = st.selectbox("Language", ["Íslenska", "English"], index=0)
    page = st.radio("Veldu síðu/Choose page", ["Spálíkan", "Tilboðsreiknivél"] if language == "Íslenska" else ["Forecast Model", "Quotation Calculator"])
    st.markdown('</div>', unsafe_allow_html=True)

# --- Þýðingar ---
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

financial_labels = {
    "Íslenska": {
        "Tekjur": "Tekjur",
        "Heildarkostnaður": "Heildarkostnaður",
        "Hagnaður": "Hagnaður",
        "NPV": "Núvirt virði (NPV)"
    },
    "English": {
        "Tekjur": "Revenue",
        "Heildarkostnaður": "Total cost",
        "Hagnaður": "Profit",
        "NPV": "Net Present Value (NPV)"
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

# --- Spálíkan ---
if ("Spálíkan" in page or "Forecast" in page):
    st.markdown(f"<h1>{labels[language]['title']}</h1><hr>", unsafe_allow_html=True)

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
        future_years = st.number_input(labels[language]["years"], min_value=1, max_value=1000, value=5)
    with col4:
        market_share_percent = st.slider(labels[language]["market"], min_value=0, max_value=100, value=50)
        final_market_share = market_share_percent / 100

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

# --- Tilboðsreiknivél ---
elif ("Tilboðsreiknivél" in page or "Quotation" in page):
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
        col5, col6, col7 = st.columns(3)
        with col5:
            verkkaupi = st.text_input(q["client"])
        with col6:
            stadsetning = st.text_input(q["location"])
        with col7:
            km_fra_thorlakshofn = st.number_input(q["distance"], min_value=0.0, value=0.0)

        submitted = st.form_submit_button(q["calculate"])

    if submitted:
        einingar = {
            "3 Modules": {"fjoldi": modul3, "fm": 19.5, "verd": 269700, "kg": 9750},
            "2 Modules": {"fjoldi": modul2, "fm": 13, "verd": 290000, "kg": 6500},
            "1 Module": {"fjoldi": modul1, "fm": 6.5, "verd": 304500, "kg": 3250},
            "0.5 Module": {"fjoldi": modul_half, "fm": 3.25, "verd": 330000, "kg": 1625},
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

            st.markdown(f"### {q['result_title']}")
            st.write(f"**{q['client']}:** {verkkaupi}")
            st.write(f"**{q['location']}:** {stadsetning}")
            st.write(f"**{q['area']}:** {heildarfm:.2f} fm")
            st.write(f"**{q['weight']}:** {heildarthyngd:,.0f} kg")
            st.write(f"**{q['shipping_is']}:** {flutningur_til_islands:,.0f} kr.")
            st.write(f"**{q['delivery']}:** {sendingarkostnadur:,.0f} kr.")
            st.write(f"**{q['variable_cost']}:** {samtals_breytilegur:,.0f} kr.")
            st.write(f"**{q['allocated_fixed']}:** {uthlutadur_fastur_kostnadur:,.0f} kr.")
            st.write(f"**{q['markup']}:** {alagsstudull:.2f}")
            st.write(f"**{q['offer_price']}:** {tilbod:,.0f} kr.")
        else:
            st.warning("Sláðu inn gildi til að reikna tilboð.")





