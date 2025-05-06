import streamlit as st
import pandas as pd
import numpy as np
import datetime
from verkx_code import main_forecast_logic

# Page config
st.set_page_config(page_title="Cubit", page_icon="assets/logo.png", layout="wide")

# Sidebar – Flipaval
page = st.sidebar.radio("Veldu síðu / Select page", ["📈 Spálíkan", "📄 Tilboðsreiknivél"])

# Tungumálaval
st.sidebar.markdown("---")
language = st.sidebar.selectbox("Tungumál / Language", ["Íslenska", "English"], index=0)

# Þýðingar
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
        "download_tab": "Sækja CSV",
        "table_title": "Cubit einingar",
        "distribution": "Dreifing",
        "financials": "Tekjumódel",
        "download_button": "Hlaða niður",
        "download_name": "spa_nidurstodur.csv",
        "warning": "Aðeins {} ár fundust — notum bara þau.",
        "error": "Villa kom upp"
    },
    "English": {
        "title": "Cubit Forecast",
        "housing": "Housing type",
        "region": "Region",
        "years": "Years into the future",
        "market": "Market share (%)",
        "run": "Run forecast",
        "loading": "Running forecast...",
        "result_tab": "Results",
        "download_tab": "Download CSV",
        "table_title": "Cubit units",
        "distribution": "Distribution",
        "financials": "Revenue model",
        "download_button": "Download",
        "download_name": "forecast_results.csv",
        "warning": "Only {} years found — using only those.",
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

# ----- FLIPI 1: SPÁLÍKAN -----
if page == "📈 Spálíkan":
    st.title(labels[language]["title"])

    # Valmöguleikar
    housing_map = {
        "Íslenska": ["Íbúðir", "Leikskólar", "Gistirými", "Elliheimili", "Atvinnuhús"],
        "English": ["Apartments", "Kindergartens", "Accommodation", "Nursing homes", "Commercial buildings"]
    }
    housing_reverse = dict(zip(housing_map["English"], housing_map["Íslenska"]))

    region_map = {
        "Íslenska": [
            "Höfuðborgarsvæðið", "Suðurnes", "Vesturland", "Vestfirðir",
            "Norðurland vestra", "Norðurland eystra", "Austurland", "Suðurland"
        ],
        "English": [
            "Capital Region", "Southern Peninsula", "Western Region", "Westfjords",
            "Northwest", "Northeast", "East", "South"
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
        future_years = st.number_input(labels[language]["years"], 1, 1000, 5)
    with col4:
        market_share_percent = st.slider(labels[language]["market"], 0, 100, 50)
        final_market_share = market_share_percent / 100

    if st.button(labels[language]["run"]):
        with st.spinner(labels[language]["loading"]):
            try:
                df, figures, used_years, financials = main_forecast_logic(
                    housing_type, region, future_years, final_market_share
                )

                if used_years < future_years:
                    st.warning(labels[language]["warning"].format(used_years))

                if language == "English":
                    df = df.rename(columns={
                        "Ár": "Year",
                        "Fortíðargögn spá": "Historical Forecast",
                        "Framtíðarspá": "Future Forecast",
                        "Meðaltal": "Average",
                        "Spá útfrá fortíðargögnum": "Forecast from past"
                    })

                tab1, tab2 = st.tabs([labels[language]["result_tab"], labels[language]["download_tab"]])

                with tab1:
                    st.subheader(labels[language]["table_title"])
                    index_col = "Ár" if language == "Íslenska" else "Year"
                    st.dataframe(df.set_index(index_col).style.format("{:.2f}"))

                    st.subheader(labels[language]["distribution"])
                    col_figs = st.columns(len(figures))
                    for c, fig in zip(col_figs, figures):
                        with c:
                            st.pyplot(fig)

                    st.subheader(labels[language]["financials"])
                    for key, value in financials.items():
                        label = financial_labels[language].get(key, key)
                        st.write(f"**{label}:** {value:,.0f} kr.")

                with tab2:
                    csv = df.to_csv(index=False).encode("utf-8-sig")
                    st.download_button(
                        label=labels[language]["download_button"],
                        data=csv,
                        file_name=labels[language]["download_name"],
                        mime="text/csv"
                    )
            except Exception as e:
                st.error(f"{labels[language]['error']}: {e}")

# ----- FLIPI 2: TILBOÐ -----
elif page == "📄 Tilboðsreiknivél":
    st.title("Tilboðsreiknivél")

    with st.form("tilbod_form"):
        st.markdown("### Gögn um einingar")
        col1, col2, col3, col4 = st.columns(4)
        modul3 = col1.number_input("3 Módúla (19,5 fm)", 0, value=0)
        modul2 = col2.number_input("2 Módúla (13 fm)", 0, value=0)
        modul1 = col3.number_input("1 Módúl (6,5 fm)", 0, value=0)
        modul_half = col4.number_input("0,5 Módúl (3,25 fm)", 0, value=0)

        st.markdown("### Aðrar upplýsingar")
        col5, col6, col7 = st.columns(3)
        verkkaupi = col5.text_input("Verkkaupi")
        stadsetning = col6.text_input("Staðsetning afhendingar")
        km = col7.number_input("Km frá Þorlákshöfn", 0.0, value=0.0)

        submitted = st.form_submit_button("Reikna tilboð")

    if submitted:
        einingar = {
            "3m": {"fjoldi": modul3, "fm": 19.5, "verd": 269700, "kg": 9750},
            "2m": {"fjoldi": modul2, "fm": 13.0, "verd": 290000, "kg": 6500},
            "1m": {"fjoldi": modul1, "fm": 6.5, "verd": 304500, "kg": 3250},
            "0.5m": {"fjoldi": modul_half, "fm": 3.25, "verd": 330000, "kg": 1625}
        }

        heildarfm = sum(e["fjoldi"] * e["fm"] for e in einingar.values())
        heildarkostnadur = sum(e["fjoldi"] * e["verd"] for e in einingar.values())
        flutningur = heildarfm * 74000
        sending = heildarfm * km * 8
        breytilegur = heildarkostnadur + flutningur + sending
        heildarthyngd = sum(e["fjoldi"] * e["kg"] for e in einingar.values())

        fastur = 34_800_000
        u_fm = 2400
        uthlutun = (heildarfm / u_fm) * fastur if heildarfm else 0
        alag = 1 + (uthlutun / breytilegur) if breytilegur else 0
        tilbod = breytilegur * alag * 1.15 if breytilegur else 0

        st.markdown("### Niðurstöður")
        st.write(f"**Dagsetning:** {datetime.date.today()}")
        st.write(f"**Verkkaupi:** {verkkaupi}")
        st.write(f"**Staðsetning:** {stadsetning}")
        st.write(f"**Heildarfermetrar:** {heildarfm:.2f} fm")
        st.write(f"**Heildarþyngd:** {heildarthyngd:,.0f} kg")
        st.write(f"**Flutningskostnaður til Íslands:** {flutningur:,.0f} kr.")
        st.write(f"**Sendingarkostnaður innanlands:** {sending:,.0f} kr.")
        st.write(f"**Samtals breytilegur kostnaður:** {breytilegur:,.0f} kr.")
        st.write(f"**Úthlutaður fastur kostnaður:** {uthlutun:,.0f} kr.")
        st.write(f"**Álagsstuðull:** {alag:.2f}")
        st.write(f"**Tilboðsverð (með 15% ásemiskröfu):** {tilbod:,.0f} kr.")



