import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.linear_model import LinearRegression

PAST_FILE = "data/GÖGN_VERKX.xlsx"
FUTURE_FILE = "data/Framtíðarspá.xlsx"

# Kostnaðar- og tekjuforsendur
PRICE_PER_SQM = 467_308
COST_PER_SQM = 452_308
TRANSPORT_COST_PER_SQM = 92_308
UNIT_SIZE_SQM = 6.5
FIXED_COST = 37_200_000
DISCOUNT_RATE = 0.08

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

def calculate_financials(sim_avg, used_years):
    total_units = np.mean(np.sum(sim_avg, axis=1))
    total_sqm = total_units * UNIT_SIZE_SQM

    revenue = total_sqm * PRICE_PER_SQM
    cost = total_sqm * (COST_PER_SQM + TRANSPORT_COST_PER_SQM)
    total_cost = cost + FIXED_COST
    profit = revenue - total_cost
    contribution_margin = revenue - cost

    annual_cashflow = profit
    npv = sum([annual_cashflow / (1 + DISCOUNT_RATE) ** t for t in range(1, used_years + 1)])

    return {
        "Heildareiningar": round(total_units),
        "Fermetrar": round(total_sqm),
        "Tekjur": round(revenue),
        "Kostnaður": round(total_cost),
        "Framlegð": round(contribution_margin),
        "Hagnaður": round(profit),
        "NPV": round(npv)
    }

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
            future_df = future_df[future_df['sviðsmynd'].str.lower() == 'miðspá']

        future_df['ar'] = pd.to_numeric(future_df['ar'], errors='coerce')
        future_data = filter_data(future_df, region, demand_column)
        future_data = future_data[future_data['ar'] > past_data['ar'].max()]

        available_years = min(len(future_data), future_years)
        future_vals = future_data['fjoldi eininga'].values[:available_years]
        future_years_vals = future_data['ar'].values[:available_years]
        market_shares = np.linspace(initial_share, final_market_share, available_years)

        linear_years, linear_pred = linear_forecast(past_data, demand_column, start_year=2025, future_years=available_years)
        linear_pred = linear_pred[:available_years]
        avg_vals = (linear_pred + future_vals) / 2
        avg_vals_adj = avg_vals * market_shares

        df = pd.DataFrame({
            'Ár': future_years_vals,
            'Fortíðargögn spá': linear_pred * market_shares,
            'Framtíðarspá': future_vals * market_shares,
            'Meðaltal': avg_vals_adj
        })

        sim_avg = monte_carlo_simulation(avg_vals, market_shares)
        figures = [plot_distribution(sim_avg, "Monte Carlo - Meðaltal")]

    else:
        linear_years, linear_pred = linear_forecast(past_data, demand_column, start_year=2025, future_years=future_years)
        avg_vals_adj = linear_pred * market_shares
        df = pd.DataFrame({
            'Ár': linear_years,
            'Spá útfrá fortíðargögnum': avg_vals_adj
        })
        sim_avg = monte_carlo_simulation(linear_pred, market_shares)
        figures = [plot_distribution(sim_avg, "Monte Carlo - Fortíðargreining")]
        available_years = future_years

    financials = calculate_financials(sim_avg, available_years)

    return df, figures, available_years, financials



























