import streamlit as st
import pandas as pd
import numpy as np
from verkx_code import main_forecast_logic

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
            df, figures, used_years, sim_avg = main_forecast_logic(housing_type, region, future_years, final_market_share)

            st.subheader("Einingar")
            st.dataframe(df.set_index(df.columns[0]).style.format("{:.2f}"))

            st.subheader("Dreifing")
            img_cols = st.columns(len(figures))
            for col, fig in zip(img_cols, figures):
                with col:
                    st.pyplot(fig)

            #Tekjumódel
            st.subheader("Fjárhagslegt mat")

            # Forsendur
            price_per_unit = 375000 
            cost_per_unit = 360000
            fixed_cost = 3000000
            contribution_per_unit = price_per_unit - cost_per_unit
            discount_rate = 0.10

            total_demand_per_sim = np.sum(sim_avg, axis=1)  # heildar spáða þörf per simulation
            expected_total_demand = total_demand_per_sim.mean()
            expected_contribution_total = expected_total_demand * contribution_per_unit

            # Árlegt cash flow – deilt jafnt yfir notuð ár
            yearly_demand = expected_total_demand / used_years
            annual_cash_flow = yearly_demand * contribution_per_unit - fixed_cost

            # Heildar hagnaður og NPV
            total_profit = annual_cash_flow * used_years
            years = np.arange(1, used_years + 1)
            discounted_cash_flows = [annual_cash_flow / ((1 + discount_rate) ** year) for year in years]
            npv = sum(discounted_cash_flows)

            colf1, colf2 = st.columns(2)
            with colf1:
                st.metric("Heildar spáð þörf", f"{expected_total_demand:,.0f} einingar")
                st.metric("Heildar framlegð", f"{expected_contribution_total:,.0f} kr.")

            with colf2:
                st.metric("Heildar hagnaður", f"{total_profit:,.0f} kr.")
                st.metric("Núvirði (NPV)", f"{npv:,.0f} kr.")

        except Exception as e:
            st.error(f"Villa kom upp: {e}")


