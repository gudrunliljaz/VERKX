# --- verkx_code.py ---

import pandas as pd
import numpy as np

def load_excel(file_path, sheet_name):
    return pd.read_excel(file_path, sheet_name=sheet_name)

def filter_data(df, region, demand_column):
    if 'landshluti' in df.columns:
        return df[df['landshluti'].str.lower() == region.lower()][['ar', demand_column]].dropna()
    else:
        raise ValueError("Gagnasettið inniheldur ekki 'landshluti' döflu.")

def linear_forecast(past_data, demand_column, future_years):
    x = past_data['ar'].values.reshape(-1, 1)
    y = past_data[demand_column].values
    model = np.polyfit(x.flatten(), y, 1)
    slope, intercept = model

    future_x = np.arange(past_data['ar'].max() + 1, past_data['ar'].max() + 1 + future_years)
    predictions = slope * future_x + intercept

    return future_x, predictions

def monte_carlo_simulation(predictions, market_shares, simulations=1000):
    results = []
    for _ in range(simulations):
        noise = np.random.normal(0, 0.1, size=predictions.shape)
        simulated = predictions * (1 + noise) * market_shares
        results.append(simulated)
    return np.array(results)

def plot_distribution(sim_data, title):
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(figsize=(6, 4))
    totals = np.sum(sim_data, axis=1)
    ax.hist(totals, bins=40, alpha=0.7, edgecolor='black')
    ax.set_title(title)
    ax.set_xlabel("Heildar spáð þörf")
    ax.set_ylabel("Tíðni")
    plt.tight_layout()
    return fig

def main_forecast_logic(housing_type, region, future_years, final_market_share):
    PAST_FILE = "data/GÖGN_VERKX.xlsx"
    FUTURE_FILE = "data/Framtíðarspá.xlsx"

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
            future_df = future_df[future_df['sviðsmynd'].str.lower() == 'miðspá']

        future_df['ar'] = pd.to_numeric(future_df['ar'], errors='coerce')
        future_data = filter_data(future_df, region, demand_column)
        future_data = future_data[future_data['ar'] > past_data['ar'].max()]

        future_vals = future_data['fjoldi eininga'].values[:future_years]
        future_years_vals = future_data['ar'].values[:future_years]

        linear_years, linear_pred = linear_forecast(past_data, demand_column, future_years)
        linear_pred = linear_pred[:len(future_vals)]

        avg_vals = (linear_pred + future_vals) / 2

        linear_pred_adj = linear_pred * market_shares
        future_vals_adj = future_vals * market_shares
        avg_vals_adj = avg_vals * market_shares

        sim_past = monte_carlo_simulation(linear_pred, market_shares)
        sim_future = monte_carlo_simulation(future_vals, market_shares)
        sim_avg = monte_carlo_simulation(avg_vals, market_shares)

        df = pd.DataFrame({
            'Ár': future_years_vals,
            'Fortíðargögn spá': linear_pred_adj,
            'Framtíðarspá': future_vals_adj,
            'Meðaltal': avg_vals_adj
        })

        figures = [
            plot_distribution(sim_past, "Monte Carlo - Fortíðargögn"),
            plot_distribution(sim_future, "Monte Carlo - Framtíðarspá"),
            plot_distribution(sim_avg, "Monte Carlo - Meðaltal")
        ]

        return df, figures

    else:
        linear_years, linear_pred = linear_forecast(past_data, demand_column, future_years)
        past_pred_adj = linear_pred * market_shares

        sim_past = monte_carlo_simulation(linear_pred, market_shares)

        df = pd.DataFrame({
            'Ár': linear_years,
            'Spá útfrá fortíðargögnum': past_pred_adj
        })

        figures = [plot_distribution(sim_past, "Monte Carlo - Fortíðargögn")]

        return df, figures













