import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.linear_model import LinearRegression

PAST_FILE = "data/GÖGN_VERKX.xlsx"
FUTURE_FILE = "data/Framtidarspa.xlsx"

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

    if use_forecast:
        future_df = load_excel(FUTURE_FILE, sheet_name)
        if 'sviðsmynd' in future_df.columns:
            future_df = future_df[future_df['sviðsmynd'].str.lower() == 'miðspá']

        future_df['ar'] = pd.to_numeric(future_df['ar'], errors='coerce')
        future_data = filter_data(future_df, region, demand_column)
        future_data = future_data[future_data['ar'] > past_data['ar'].max()]

        if len(future_data) < future_years:
            # Ekki nóg framtíðargögn - notum bara fortíðargreiningu
            use_forecast = False

    if not use_forecast:
        # Aðeins fortíðargreining
        linear_years, linear_pred = linear_forecast(past_data, demand_column, start_year=2025, future_years=future_years)
        market_shares = np.linspace(initial_share, final_market_share, future_years)
        past_pred_adj = linear_pred * market_shares

        df = pd.DataFrame({
            'Ár': linear_years,
            'Spá útfrá fortíðargögnum': past_pred_adj
        })

        figures = [plot_distribution(monte_carlo_simulation(linear_pred, market_shares), "Monte Carlo - Fortíðargögn")]

        return df, figures, future_years

    else:
        # Bæði fortíð + framtíð
        future_vals = future_data['fjoldi eininga'].values[:future_years]
        future_years_vals = future_data['ar'].values[:future_years]
        market_shares = np.linspace(initial_share, final_market_share, len(future_vals))

        linear_years, linear_pred = linear_forecast(past_data, demand_column, start_year=2025, future_years=len(future_vals))
        linear_pred = linear_pred[:len(future_vals)]

        avg_vals = (linear_pred + future_vals) / 2

        linear_pred_adj = linear_pred * market_shares
        future_vals_adj = future_vals * market_shares
        avg_vals_adj = avg_vals * market_shares

        df = pd.DataFrame({
            'Ár': future_years_vals,
            'Fortíðargögn spá': linear_pred_adj,
            'Framtíðarspá': future_vals_adj,
            'Meðaltal': avg_vals_adj
        })

        figures = [
            plot_distribution(monte_carlo_simulation(linear_pred, market_shares), "Monte Carlo - Fortíðargögn"),
            plot_distribution(monte_carlo_simulation(future_vals, market_shares), "Monte Carlo - Framtíðarspá"),
            plot_distribution(monte_carlo_simulation(avg_vals, market_shares), "Monte Carlo - Meðaltal"),
        ]

        return df, figures, len(future_vals)


















