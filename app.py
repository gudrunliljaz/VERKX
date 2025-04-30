import streamlit as st
from verkx_code import main_forecast_logic

st.set_page_config(page_title="Cubit Spá", layout="wide", page_icon="📊")

st.markdown("<h1 style='color:#003366'>Cubit Spá</h1><hr>", unsafe_allow_html=True)

# Notandainntak
col1, col2 = st.columns(2)
with col1:
    housing_type = st.selectbox("Tegund húsnæðis:", ["Íbúðir", "Leikskólar", "Gistirými", "Elliheimili", "Atvinnuhús"])
with col2:
    region = st.selectbox("Landshluti:", [
        "Höfuðborgarsvæðið", "Suðurnes", "Vesturland", "Vestfirðir",
        "Norðurland vestra", "Norðurland eystra", "Austurland", "Suðurland"
    ])

col3, col4 = st.columns(2)
with col3:
    future_years = st.number_input("Árafjöldi í framtíðinni:", min_value=1, max_value=100, value=5)
with col4:
    market_share_percent = st.slider("Markaðshlutdeild (%):", 0, 100, 30)
    final_market_share = market_share_percent / 100

# Keyra spá
if st.button("Keyra spá"):
    with st.spinner("Vinsamlegast bíðið..."):
        try:
            df, figures, used_years, financials = main_forecast_logic(housing_type, region, future_years, final_market_share)
            
            # Tölur
            st.subheader("📊 Spá niðurstöður")
            st.dataframe(df.set_index(df.columns[0]).style.format("{:.2f}"))

            # Myndir
            st.subheader("📉 Dreifing")
            cols = st.columns(len(figures))
            for col, fig in zip(cols, figures):
                with col:
                    st.pyplot(fig)

            

            st.subheader("💰 Fjárhagslegar niðurstöður")
            st.metric("Heildareiningar", f"{financials['Total Units']:.0f}")
            st.metric("Tekjur", f"{financials['Revenue']:,.0f} kr.")
            st.metric("Heildarkostnaður", f"{financials['Total Cost']:,.0f} kr.")
            st.metric("Framlegð", f"{financials['Contribution Margin']:,.0f} kr.")
            st.metric("Hagnaður", f"{financials['Profit']:,.0f} kr.")
            st.metric("NPV", f"{financials['NPV']:,.0f} kr.")

            # CSV niðurhal
            csv = df.to_csv(index=False).encode("utf-8")
            st.download_button("📥 Hlaða niður CSV", csv, file_name="spa_nidurstodur.csv", mime="text/csv")

        except Exception as e:
            st.error(f"Villa kom upp: {e}")

