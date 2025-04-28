import streamlit as st
import pandas as pd
import numpy as np
import io
from verkx_code import main_forecast_logic

# Stillum síðuna
st.set_page_config(page_title="Cubit Spá", layout="wide")

# Custom stíll fyrir dökkbláan titil
st.markdown("""
    <style>
    h1 {
        color: #003366;
        text-align: center;
    }
    </style>
""", unsafe_allow_html=True)

# Dökkblár titill
st.markdown("<h1>Cubit Spá</h1>", unsafe_allow_html=True)
st.markdown("---")

# Valmöguleikar
col1, col2 = st.columns(2)

with col1:
    housing_options = ["Íbúðir", "Leikskólar", "Gistirými", "Elliheimili", "Atvinnuhús"]
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

# Keyra spá takki
if st.button("Keyra spá"):
    with st.spinner('Reikna spá, vinsamlegast bíðið...'):
        try:
            df, figures, used_years = main_forecast_logic(housing_type, region, future_years, final_market_share)

            if used_years < future_years:
                st.warning(f"Aðeins {used_years} ár fundust í framtíðarspá — notum bara þau ár.")

            # Flipar: Niðurstöður og Hlaða niður
            tabs = st.tabs(["Niðurstöður", "Vista niðurstöður"])

            with tabs[0]:
                st.subheader("Einingar")
                st.dataframe(df.set_index("Ár").style.format("{:.2f}"))

                st.subheader("Monte Carlo dreifing")
                img_cols = st.columns(len(figures))
                for col, fig in zip(img_cols, figures):
                    with col:
                        st.pyplot(fig)

            with tabs[1]:
                st.subheader("Hlaða niður CSV skrá")

                csv = df.to_csv(index=False).encode('utf-8')

                st.download_button(
                    label="Hlaða niður CSV skránni",
                    data=csv,
                    file_name="spa_nidurstodur.csv",
                    mime="text/csv"
                )

        except Exception as e:
            st.error(f"Villa kom upp: {e}")









