import streamlit as st
import pandas as pd
from verkx_code import main_forecast_logic, calculate_financials

st.set_page_config(page_title="Cubit Spá", layout="wide", page_icon="📊")

st.markdown("<h1 style='color:#003366'>Cubit Spá</h1><hr>", unsafe_allow_html=True)

# Valmöguleikar
col1, col2 = st.columns(2)
with col1:
    housing_type = st.selectbox("Hvaða tegund húsnæðis viltu skoða?", ["Íbúðir", "Leikskólar", "Gistirými", "Elliheimili", "Atvinnuhús"])
with col2:
    region = st.selectbox("Hvaða landshluta?", [
        "Höfuðborgarsvæðið", "Suðurnes", "Vesturland", "Vestfirðir",
        "Norðurland vestra", "Norðurland eystra", "Austurland", "Suðurland"
    ])

col3, col4 = st.columns(2)
with col3:
    future_years = st.number_input("Fjöldi ára fram í tímann:", min_value=1, max_value=100, value=5)
with col4:
    market_share_percent = st.slider("Markaðshlutdeild (%):", min_value=0, max_value=100, value=30)
    final_market_share = market_share_percent / 100

# Keyra spá
if st.button("Keyra spá"):
    with st.spinner("Reikna spá, vinsamlegast bíðið..."):
        try:
            df, figures, used_years, sim_avg = main_forecast_logic(
                housing_type, region, future_years, final_market_share
            )

            # Sýna töflu
            st.subheader("📊 Spá niðurstöður")
            st.dataframe(df.set_index(df.columns[0]).style.format("{:.2f}"))

            # Dreifingarmyndir
            st.subheader("📉 Monte Carlo dreifing")
            img_cols = st.columns(len(figures))
            for col, fig in zip(img_cols, figures):
                with col:
                    st.pyplot(fig)

            # Fjárhagsleg niðurstaða
            financials = calculate_financials(sim_avg)

            st.subheader("📈 Fjárhagslegar niðurstöður")
            st.markdown(f"""
            - **Heildarspáð einingaþörf:** {financials['expected_demand']:.0f}
            - **Heildar fermetrar:** {financials['total_sqm']:.0f} m²  
            - **Heildartekjur:** {financials['total_revenue']:,.0f} kr.
            - **Heildarkostnaður (breytilegur):** {financials['total_variable_cost']:,.0f} kr.
            - **Heildarframlegð:** {financials['total_contribution']:,.0f} kr.
            - **Hagnaður:** {financials['total_profit']:,.0f} kr.
            - **Núvirði (NPV):** {financials['npv']:,.0f} kr.
            """)

            # Hlaða niður CSV
            csv = df.to_csv(index=False).encode("utf-8")
            st.download_button(
                label="📥 Hlaða niður spá sem CSV",
                data=csv,
                file_name="spa_nidurstodur.csv",
                mime="text/csv"
            )

        except Exception as e:
            st.error(f"Villa kom upp: {e}")


