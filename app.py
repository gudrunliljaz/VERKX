import streamlit as st
import pandas as pd
import numpy as np
from verkx_code import main_forecast_logic, main_forecast_logic_from_excel

# Page config
st.set_page_config(page_title="Cubit", page_icon="andreim.png", layout="wide")

# Sidebar – language and page selection
with st.sidebar:
    language = st.selectbox("Language", ["Íslenska", "English"], index=0)
    page = st.radio(
        "Veldu síðu / Choose page",
        ["Spálíkan", "Heildarspá"] if language == "Íslenska" else ["Forecast Model", "All Markets Forecast"]
    )

# Translation dictionary
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
        "download_tab": "Vista niðurstöður",
        "table_title": "Spágildi",
        "distribution": "Dreifing",
        "download_button": "Hlaða niður CSV",
        "download_name": "spa_nidurstodur.csv",
        "warning": "Aðeins {} ár fundust í framtíðarspá.",
        "error": "Villa kom upp"
    },
    "English": {
        "title": "Cubit Forecast",
        "housing": "Housing type",
        "region": "Region",
        "years": "Years to forecast",
        "market": "Market share (%)",
        "run": "Run forecast",
        "loading": "Running forecast...",
        "result_tab": "Results",
        "download_tab": "Download",
        "table_title": "Forecast values",
        "distribution": "Distributions",
        "download_button": "Download CSV",
        "download_name": "forecast_results.csv",
        "warning": "Only {} years found in future data.",
        "error": "An error occurred"
    }
}

# Housing and region mappings
housing_map = {
    "Íslenska": ["Íbúðir", "Leikskólar", "Gistirými", "Elliheimili", "Atvinnuhús"],
    "English": ["Apartments", "Kindergartens", "Accommodation", "Nursing homes", "Commercial"]
}
housing_reverse = dict(zip(housing_map["English"], housing_map["Íslenska"]))

region_map = {
    "Íslenska": [
        "Höfuðborgarsvæðið", "Suðurnes", "Vesturland", "Vestfirðir",
        "Norðurland vestra", "Norðurland eystra", "Austurland", "Suðurland"
    ],
    "English": [
        "Capital Region", "Southern Peninsula", "Western", "Westfjords",
        "Northwest", "Northeast", "East", "South"
    ]
}
region_reverse = dict(zip(region_map["English"], region_map["Íslenska"]))

# Forecast page
if ("Spálíkan" in page or "Forecast" in page):
    st.title(labels[language]["title"])

    col1, col2 = st.columns(2)
    with col1:
        housing_display = st.selectbox(labels[language]["housing"], housing_map[language])
        housing_type = housing_reverse[housing_display] if language == "English" else housing_display

    with col2:
        region_display = st.selectbox(labels[language]["region"], region_map[language])
        region = region_reverse[region_display] if language == "English" else region_display

    col3, col4 = st.columns(2)
    with col3:
        future_years = st.number_input(labels[language]["years"], min_value=1, max_value=20, value=5)
    with col4:
        market_share_percent = st.slider(labels[language]["market"], 0, 100, 50)
        final_market_share = market_share_percent / 100

    if st.button(labels[language]["run"]):
        with st.spinner(labels[language]["loading"]):
            try:
                df, figures, used_years = main_forecast_logic(housing_type, region, future_years, final_market_share)

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
                    cols = st.columns(len(figures))
                    for col, fig in zip(cols, figures):
                        with col:
                            st.pyplot(fig)

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

# All Markets Forecast
elif ("Heildarspá" in page or "All Markets Forecast" in page):
    st.title("📊 " + ("Heildarspá allra markaða" if language == "Íslenska" else "Forecast for all markets"))

    profit_margin_percent = st.slider(
        "Arðsemiskrafa (%)" if language == "Íslenska" else "Profit margin (%)", 0, 100, 15
    )
    profit_margin = profit_margin_percent / 100

    if st.button("Keyra heildarspá" if language == "Íslenska" else "Run all market forecast"):
        with st.spinner("Reikna spá..." if language == "Íslenska" else "Running forecast..."):
            try:
                summary_df = main_forecast_logic_from_excel(
                    past_file="data/GÖGN_VERKX.xlsx",
                    future_file="data/Framtidarspa.xlsx",
                    share_file="data/markadshlutdeild.xlsx",
                    profit_margin=profit_margin
                )

                if summary_df is not None:
                    st.success("Spá kláruð!" if language == "Íslenska" else "Forecast complete!")
                    st.subheader("Niðurstöður" if language == "Íslenska" else "Results")
                    st.dataframe(summary_df.set_index("ár").style.format("{:,.0f}"))

                    csv = summary_df.to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig")
                    st.download_button(
                        label="📥 Hlaða niður niðurstöðum (CSV)" if language == "Íslenska" else "📥 Download results (CSV)",
                        data=csv,
                        file_name="heildarspa.csv",
                        mime="text/csv"
                    )
                else:
                    st.warning("Engin gögn fundust." if language == "Íslenska" else "No valid data found.")
            except Exception as e:
                st.error(f"Villa: {e}" if language == "Íslenska" else f"Error: {e}")
