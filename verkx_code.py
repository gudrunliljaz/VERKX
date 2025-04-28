### verkx_code.py

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.linear_model import LinearRegression

PAST_FILE = "data/GÖGN_VERKX.xlsx"
FUTURE_FILE = "data/Framtíðarspá.xlsx"

def load_excel(file_path, sheet_name):
    df = pd.read_excel(file_path, sheet_name=sheet_name, engine="openpyxl")
    df.columns = [col.strip().lower() for col in df.columns]
    return df

def filter_data(df, region, demand_column):
    df = df[df['landshluti'].str.strip() == region.strip()].copy()
    df.columns = [col.strip().lower() for col in df.columns]
    demand_column = demand_column.lower()
    if demand_column not in df.columns:
        raise KeyError(f"Dálkur '{demand_column}' fannst ekki.")
    df['ar'] = pd.to_numeric(df['ar'], errors='coerce')
    df = df.dropna(subset=['ar', demand_column])
    df = df.sort_values('ar')
    return df[['ar', demand_column]]

def linear_forecast(df, demand_column, start_year, future_years):
    X = df[['ar']].values
    y = df[demand_column].values
    model = LinearRegression().fit(X, y)
    future_years_range = np.array(range(start_year, start_year + future_years))
    predictions = model.predict(future_years_range.reshape(-1, 1))
    return future_years_range, predictions

def monte_carlo_simulation(values, market_shares, simulations=10000, volatility=0.1):
    mean_val = np.mean(values)
    scale = abs(mean_val * volatility)
    results = []
    for _ in range(simulations):
        noise = np.random.normal(0, scale, len(values))
        simulated = (values + noise) * market_shares
        results.append(simulated)
    return np.array(results)

def plot_distribution(sim_data, title):
    fig, ax = plt.subplots(figsize=(6, 4))
    totals = np.sum(sim_data, axis=1)
    ax.hist(totals, bins=40, alpha=0.7, edgecolor='black')
    ax.set_title(title)
    ax.set_xlabel("Heildar spáð þörf")
    ax.set_ylabel("Tíðni")
    plt.tight_layout()
    return fig

def main_forecast_logic(housing_type, region, future_years, final_market_share):
    sheet_name = f"{housing_type} eftir landshlutum"
    use_forecast = housing_type.lower() in ["íbúðir", "leikskólar"]

    past_df = load_excel(PAST_FILE, sheet_name)
    demand_column = 'fjoldi eininga'
    past_data = filter_data(past_df, region, demand_column)

    if past_data.empty:
        raise ValueError("Engin fortíðargögn fundust fyrir valinn landshluta.")

    initial_share = final_market_share * np.random.uniform(0.05, 0.1)
    market_shares = np.linspace(initial_share, final_market_share, future_years)

    if use_forecast:
        future_df = load_excel(FUTURE_FILE, sheet_name)
        if 'sviðsmynd' in future_df.columns:
            future_df = future_df[future_df['sviðsmynd'].str.lower() == 'íðspá']

        future_df['ar'] = pd.to_numeric(future_df['ar'], errors='coerce')
        future_data = filter_data(future_df, region, demand_column)

        future_data = future_data[future_data['ar'] > past_data['ar'].max()]
        future_vals = future_data['fjoldi eininga'].values[:future_years]
        future_years_vals = future_data['ar'].values[:future_years]

        linear_years, linear_pred = linear_forecast(past_data, demand_column, start_year=2025, future_years=future_years)
        linear_pred = linear_pred[:len(future_vals)]

        avg_vals = (linear_pred + future_vals) / 2

        linear_pred_adj = linear_pred * market_shares
        future_vals_adj = future_vals * market_shares
        avg_vals_adj = avg_vals * market_shares

        import pandas as pd
        df = pd.DataFrame({
            'Ár': future_years_vals,
            'Fortíðargögn spá': linear_pred_adj,
            'Framtíðarspá': future_vals_adj,
            'Meðaltal': avg_vals_adj
        })

        figures = []
        figures.append(plot_distribution(monte_carlo_simulation(linear_pred, market_shares), "Monte Carlo - Fortíðargögn"))
        figures.append(plot_distribution(monte_carlo_simulation(future_vals, market_shares), "Monte Carlo - Framtíðarspá"))
        figures.append(plot_distribution(monte_carlo_simulation(avg_vals, market_shares), "Monte Carlo - Meðaltal"))

        return df, figures

    else:
        linear_years, linear_pred = linear_forecast(past_data, demand_column, start_year=2025, future_years=future_years)
        past_pred_adj = linear_pred * market_shares

        df = pd.DataFrame({
            'Ár': linear_years,
            'Spá útfrá fortíðargögnum': past_pred_adj
        })

        figures = []
        figures.append(plot_distribution(monte_carlo_simulation(linear_pred, market_shares), "Monte Carlo - Fortíðargögn"))

        return df, figures


### app.py

import streamlit as st
import pandas as pd
import numpy as np
from verkx_code import main_forecast_logic

st.set_page_config(page_title="Cubit spá", layout="wide", page_icon="📊")

with st.container():
    st.title("Cubit spá")

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

    if st.button("Keyra spá"):
        try:
            df, figures = main_forecast_logic(housing_type, region, future_years, final_market_share)

            st.subheader("Níðurstöður")
            st.dataframe(df.set_index("Ár").style.format("{:.2f}"))

            st.subheader("Monte Carlo dreifing")
            for fig in figures:
                st.pyplot(fig)

        except Exception as e:
            st.error(f"🛑 Villa kom upp: {e}")














