import streamlit as st
from verkx_code import main_forecast_logic

st.set_page_config(page_title="Cubit Spá", layout="wide", page_icon="📊")

st.markdown("<h1 style='color:#003366'>Cubit Spá</h1><hr>", unsafe_allow_html=True)

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

if st.button("Keyra spá"):
    with st.spinner("Reikna spá..."):
        try:
            df, figures, used_years, financials = main_forecast_logic(
                housing_type, region, future_years, final_market_share
            )

            st.subheader("📊 Spá niðurstöður")
            st.dataframe(df.set_index(df.columns[0]).style.format("{:.2f}"))

            st.subheader("📉 Monte Carlo dreifing")
            cols = st.columns(len(figures))
            for col, fig in zip(cols, figures):
                with col:
                    st.pyplot(fig)

            st.subheader("📈 Fjárhagsleg niðurstaða")
            for k, v in financials.items():
                st.write(f"**{k}:** {v:,.0f} kr.")

            csv = df.to_csv(index=False).encode("utf-8")
            st.download_button("📥 Hlaða niður CSV", csv, file_name="spa_nidurstodur.csv", mime="text/csv")

        except Exception as e:
            st.error(f"Villa kom upp: {e}")


