import streamlit as st
import pandas as pd
import numpy as np
from verkx_code import main_forecast_logic

st.set_page_config(page_title="Cubit spá", layout="wide", page_icon="📊")

with st.container():
    st.markdown(
        "<h1 style='text-align: center; color: #4CAF50;'>📈 Cubit Spá</h1>",
        unsafe_allow_html=True
    )
    st.markdown("---")

    col1, col2 = st.columns(2)

    with col1:
        housing_options = ["Íbúðir", "Leikskólar", "Gistirými", "Elliheimili", "Atvinnuhúsnæði"]
        housing_type = st.selectbox("Hvaða tegund húsnæðis viltu skoða?", housing_options)

    with col2:
        region_options = [
            "Höfuðborgarsvæðið", "Suðurnes", "Vesturland", "Vestfirðir",
            "Norðurland vestra", "Norðurland eystra", "Austurland", "Suðurland"
        ]
        region = st.selectbox("Hvaða landshluta?", region_options)

    col3, col4 = st.columns(2)

    with col3:
        future_years = st.number_input("Fjöldi ára fram í tímann:", min_value=1, max_value=50, value=5)

    with col4:
        final_market_share = st.slider("Markaðshlutdeild:", min_value=0.01, max_value=1.0, value=0.3)

    if st.button("🚀 Keyra spá"):
        try:
            df, figures = main_forecast_logic(housing_type, region, future_years, final_market_share)

            st.subheader("Niðurstöður")
            st.dataframe(df.set_index("Ár").style.format("{:.2f}"))

            st.subheader("Monte Carlo dreifing")
            for fig in figures:
                st.pyplot(fig)

        except Exception as e:
            st.error(f"🛑 Villa kom upp: {e}")





