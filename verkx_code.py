import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.linear_model import LinearRegression

PAST_FILE = "data/GÖGN_VERKX.xlsx"
FUTURE_FILE = "data/Framtíðarspá.xlsx"

PRICE_PER_UNIT = 375000
COST_PER_UNIT = 360000
FIXED_COST_YEARLY = 3_000_000

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

def calculate_total_profit(sim_data):
    totals = np.sum(sim_data, axis=1)
    revenue = totals * PRICE_PER_UNIT
    variable_costs = totals * COST_PER_UNIT
    total_costs = variable_costs + FIXED_COST_YEARLY
    profit = revenue - total_costs
    return profit




















