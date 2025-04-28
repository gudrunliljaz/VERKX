import streamlit as st
import pandas as pd
import numpy as np
import io
from verkx_code import main_forecast_logic

# Set page config
st.set_page_config(page_title="Cubit spá", layout="wide", page_icon="📊")

# Custom CSS
st.markdown("""
    <style>
    .stSlider > div > div > div > div {
        background: #add8e6;  /* Ljósblár slider */
    }
    div.stButton > button {
        background-color: #add8e6; /* Ljósblár takki */
        color: black;
        font-weight: bold;
        border: none;
        height: 3em;
        width: 100%;
        font-size: 18px;
        border-radius: 10px;
    }
    </style>
""", unsafe_allow_html=True)

# Titill
st.markdown("<h1 style='text-align: center; color: #4CAF50;'>📈 Cubit Spá</h1>", unsafe_allow_html=True)
st.markdown("---")

# Valmöguleikar
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

# Takki til að keyra spá
if st.button("🚀 Keyra spá"):
    with st.spinner('🔄 Reikna spá, vinsamlegast bíðið...'):
        try:
            df, figures, used_years = main_forecast_logic(housing_type, region, future_years, final_market_share)

            if used_years < future_years:
                st.warning(f"Aðeins {used_years} ár fundust í framtíðarspá — notum bara þau ár.")

            # Flipar (Tabs) fyrir niðurstöður og niðurhal
            tabs = st.tabs(["📊 Niðurstöður", "📥 Hlaða niður"])

            with tabs[0]:
                st.subheader("📊 Niðurstöður Tafla")
                st.dataframe(df.set_index("Ár").style.format("{:.2f}"))

                st.subheader("🎯 Monte Carlo dreifing")

                # Myndir hlið við hlið
                img_cols = st.columns(len(figures))

                for col, fig in zip(img_cols, figures):
                    with col:
                        st.pyplot(fig)

            with tabs[1]:
                st.subheader("📥 Sækja niðurstöður sem Excel")

                buffer = io.BytesIO()
                with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
                    df.to_excel(writer, index=False)
                    writer.save()

                st.download_button(
                    label="📥 Hlaða niður spá niðurstöðum",
                    data=buffer,
                    file_name="spa_nidurstodur.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )

        except Exception as e:
            st.error(f"🛑 Villa kom upp: {e}")








