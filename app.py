import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from verkx_code import load_excel, filter_data, linear_forecast, monte_carlo_simulation, PAST_FILE, FUTURE_FILE

st.set_page_config(page_title="Cubit spá", layout="wide")

st.markdown(
    "<h1 style='text-align: center; color: #4CAF50;'>📈 Cubit Spá</h1>",
    unsafe_allow_html=True
)

st.markdown("---")

housing_options = ["Íbúðir", "Leikskólar", "Gistirými", "Elliheimili", "Atvinnuhúsnæði"]
housing_type = st.selectbox("Hvaða tegund húsnæðis viltu skoða?", housing_options)

region_options = [
    "Höfuðborgarsvæðið", "Suðurnes", "Vesturland", "Vestfirðir", 
    "Norðurland vestra", "Norðurland eystra", "Austurland", "Suðurland"
]
region = st.selectbox("Hvaða landshluta?", region_options)

future_years = st.number_input("Fjöldi ára fram í tímann:", min_value=1, max_value=50, value=5)
final_market_share = st.slider("Markaðshlutdeild:", min_value=0.01, max_value=1.0, value=0.3)

if st.button("🚀 Keyra spá"):
    with st.spinner('Reikna spá...'):
        try:
            sheet_name = f"{housing_type} eftir landshlutum"
            past_df = load_excel(PAST_FILE, sheet_name)
            past_data = filter_data(past_df, region, 'fjoldi eininga')

            use_forecast = housing_type.lower() in ["íbúðir", "leikskólar"]
            start_year = 2025

            if past_data.empty:
                st.error("❌ Engin fortíðargögn fundust fyrir valinn landshluta.")
            else:
                initial_share = final_market_share * np.random.uniform(0.05, 0.1)
                market_shares = np.linspace(initial_share, final_market_share, future_years)

                if use_forecast:
                    future_df = load_excel(FUTURE_FILE, sheet_name)
                    if 'sviðsmynd' in future_df.columns:
                        future_df = future_df[future_df['sviðsmynd'].str.lower() == 'miðspá']

                    future_df['ar'] = pd.to_numeric(future_df['ar'], errors='coerce')
                    future_data = filter_data(future_df, region, 'fjoldi eininga')
                    future_data = future_data[future_data['ar'] >= 2025]

                    if future_data.empty:
                        st.warning("⚠️ Engin framtíðarspágögn fundust. Notum aðeins fortíðargögn.")
                        use_forecast = False
                    else:
                        future_vals = future_data['fjoldi eininga'].values[:future_years]
                        future_years_vals = future_data['ar'].values[:future_years]

                linear_years, linear_pred = linear_forecast(past_data, 'fjoldi eininga', start_year, future_years)
                linear_pred_adj = linear_pred * market_shares

                if use_forecast and len(future_vals) >= future_years:
                    avg_vals = (linear_pred + future_vals) / 2

                    future_vals_adj = future_vals * market_shares
                    avg_vals_adj = avg_vals * market_shares

                    df_results = pd.DataFrame({
                        "Ár": future_years_vals,
                        "Fortíðargreining": linear_pred_adj,
                        "Framtíðarspá": future_vals_adj,
                        "Meðaltal": avg_vals_adj
                    })

                    st.success("✅ Spá lokið!")

                    st.subheader("Niðurstöður")
                    st.dataframe(df_results.set_index("Ár").style.format("{:.2f}"))

                    csv = df_results.to_csv(index=False).encode('utf-8')
                    st.download_button(
                        "📥 Hlaða niður niðurstöðum (CSV)",
                        data=csv,
                        file_name='spá_cubit.csv',
                        mime='text/csv'
                    )

                    # Monte Carlo hermun
                    sim_past = monte_carlo_simulation(linear_pred, market_shares)
                    sim_future = monte_carlo_simulation(future_vals, market_shares)
                    sim_avg = monte_carlo_simulation(avg_vals, market_shares)

                    st.subheader("Monte Carlo dreifing")
                    col1, col2, col3 = st.columns(3)

                    with col1:
                        fig1, ax1 = plt.subplots()
                        ax1.hist(np.sum(sim_past, axis=1), bins=40, alpha=0.7, edgecolor='black')
                        ax1.set_title("Fortíðargreining")
                        st.pyplot(fig1)

                    with col2:
                        fig2, ax2 = plt.subplots()
                        ax2.hist(np.sum(sim_future, axis=1), bins=40, alpha=0.7, edgecolor='black')
                        ax2.set_title("Framtíðarspá")
                        st.pyplot(fig2)

                    with col3:
                        fig3, ax3 = plt.subplots()
                        ax3.hist(np.sum(sim_avg, axis=1), bins=40, alpha=0.7, edgecolor='black')
                        ax3.set_title("Meðaltal")
                        st.pyplot(fig3)

                else:
                    df_results = pd.DataFrame({
                        "Ár": linear_years,
                        "Fortíðargreining": linear_pred_adj
                    })

                    st.success("✅ Spá lokið!")

                    st.subheader("Spá niðurstöður (bara fortíðargreining)")
                    st.dataframe(df_results.set_index("Ár").style.format("{:.2f}"))

                    csv = df_results.to_csv(index=False).encode('utf-8')
                    st.download_button(
                        "📥 Hlaða niður niðurstöðum (CSV)",
                        data=csv,
                        file_name='spá_cubit.csv',
                        mime='text/csv'
                    )

                    # Hér laga ég það sem vantaði:
                    sim_past = monte_carlo_simulation(linear_pred, market_shares)

                    st.subheader("Monte Carlo dreifing")
                    fig, ax = plt.subplots()
                    ax.hist(np.sum(sim_past, axis=1), bins=40, alpha=0.7, edgecolor='black')
                    ax.set_title("Fortíðargreining")
                    st.pyplot(fig)

        except Exception as e:
            st.error(f"❌ Villa kom upp: {e}")


