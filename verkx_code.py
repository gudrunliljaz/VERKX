import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.linear_model import LinearRegression
import unicodedata

# Skrár
PAST_FILE = "data/GÖGN_VERKX.xlsx"
FUTURE_FILE = "data/Framtidarspa.xlsx"
SHARE_FILE = "data/markadshlutdeild.xlsx"

# Fastar
PRICE_PER_SQM = 467_308
BASE_COST_PER_SQM = 360_000
TRANSPORT_COST_PER_SQM = 92_308
UNIT_SIZE_SQM = 6.5
FIXED_COST_PER_YEAR = 37_200_000
DISCOUNT_RATE = 0.08
EFFICIENCY_FACTOR = 0.98

def normalize(text):
    nfkd = unicodedata.normalize('NFKD', str(text))
    return ''.join(c for c in nfkd if not unicodedata.combining(c)).lower().strip()

def load_excel(file_path, sheet_name):
    df = pd.read_excel(file_path, sheet_name=sheet_name, engine="openpyxl")
    df.columns = [col.strip().lower() for col in df.columns]
    return df

def filter_data(df, region, demand_column):
    df = df[df['landshluti'].str.strip().str.lower() == region.strip().lower()].copy()
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
    fig, ax = plt.subplots(figsize=(5, 3))
    totals = np.sum(sim_data, axis=1)
    ax.hist(totals, bins=40, alpha=0.7, edgecolor='black')
    ax.set_title(title, fontsize=14, color='#003366')
    ax.set_xlabel("Heildar spáð þörf")
    ax.set_ylabel("Tíðni")
    plt.tight_layout()
    return fig

def calculate_financials(sim_avg):
    avg_units_per_year = np.mean(sim_avg, axis=0)
    years = len(avg_units_per_year)
    total_revenue = []
    total_variable_cost = []
    cash_flows = []
    efficiency = 1.0

    for year in range(years):
        units = avg_units_per_year[year]
        sqm_total = units * UNIT_SIZE_SQM
        if year == 1:
            efficiency = 0.90
        elif year > 1:
            efficiency *= EFFICIENCY_FACTOR
        variable_cost_per_sqm = (BASE_COST_PER_SQM * efficiency) + TRANSPORT_COST_PER_SQM
        total_cost = variable_cost_per_sqm * sqm_total
        revenue = PRICE_PER_SQM * sqm_total
        profit = revenue - total_cost
        total_revenue.append(revenue)
        total_variable_cost.append(total_cost)
        cash_flows.append(profit)

    npv = sum(cf / ((1 + DISCOUNT_RATE) ** (i + 1)) for i, cf in enumerate(cash_flows))

    return {
        "Tekjur": sum(total_revenue),
        "Heildarkostnaður": sum(total_variable_cost),
        "Hagnaður": sum(cash_flows),
        "NPV": npv
    }

def main_forecast_logic(housing_type, region, future_years, final_market_share):
    sheet_name = f"{housing_type} eftir landshlutum"
    use_forecast = housing_type.lower() in ["íbúðir", "leikskólar"]
    past_df = load_excel(PAST_FILE, sheet_name)
    demand_column = 'fjöldi eininga'
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
            use_forecast = False

    if not use_forecast:
        linear_years, linear_pred = linear_forecast(past_data, demand_column, 2025, future_years)
        market_shares = np.linspace(initial_share, final_market_share, future_years)
        past_pred_adj = linear_pred * market_shares
        sim_past = monte_carlo_simulation(linear_pred, market_shares)
        df = pd.DataFrame({'Ár': linear_years, 'Spá útfrá fortíðargögnum': past_pred_adj})
        figures = [plot_distribution(sim_past, "Monte Carlo - Fortíðargögn")]
        financials = calculate_financials(sim_past)
        return df, figures, future_years, financials
    else:
        future_vals = future_data['fjöldi eininga'].values[:future_years]
        future_years_vals = future_data['ar'].values[:future_years]
        market_shares = np.linspace(initial_share, final_market_share, len(future_vals))
        linear_years, linear_pred = linear_forecast(past_data, demand_column, 2025, len(future_vals))
        linear_pred = linear_pred[:len(future_vals)]
        avg_vals = (linear_pred + future_vals) / 2
        linear_pred_adj = linear_pred * market_shares
        future_vals_adj = future_vals * market_shares
        avg_vals_adj = avg_vals * market_shares
        sim_avg = monte_carlo_simulation(avg_vals, market_shares)
        df = pd.DataFrame({
            'Ár': future_years_vals,
            'Fortíðargögn spá': linear_pred_adj,
            'Framtíðarspá': future_vals_adj,
            'Meðaltal': avg_vals_adj
        })
        figures = [
            plot_distribution(monte_carlo_simulation(linear_pred, market_shares), "Monte Carlo - Fortíðargögn"),
            plot_distribution(monte_carlo_simulation(future_vals, market_shares), "Monte Carlo - Framtíðarspá"),
            plot_distribution(sim_avg, "Monte Carlo - Meðaltal")
        ]
        financials = calculate_financials(sim_avg)
        return df, figures, len(future_vals), financials

def main_forecast_logic_from_excel(past_file, future_file, share_file, profit_margin=0.15):
    # Finna rétta flipann í markaðshlutdeildarskránni
    xl = pd.ExcelFile(share_file, engine="openpyxl")
    for sheet in xl.sheet_names:
        df = xl.parse(sheet)
        df.columns = [normalize(c) for c in df.columns]
        if {"tegund", "landshluti", "markaðshlutdeild"}.issubset(df.columns):
            share_df = df
            break
    else:
        raise ValueError("Fann engan flip með dálkunum 'tegund', 'landshluti', 'markaðshlutdeild'")

    markets = share_df.to_dict("records")
    all_forecasts = []

    for market in markets:
        housing = normalize(market["tegund"])
        region = normalize(market["landshluti"])
        share = market["markaðshlutdeild"]
        sheet_name = f"{housing} eftir landshlutum"

        try:
            past = pd.read_excel(past_file, sheet_name=sheet_name, engine="openpyxl")
            past_filtered = filter_data(past, region, 'fjöldi eininga')
            if past_filtered.empty:
                continue
        except Exception:
            continue

        years, pred = linear_forecast(past_filtered, 'fjöldi eininga', 2025, 5)
        adj_pred = pred * share
        df = pd.DataFrame({'ár': years, 'meðaltal': adj_pred})
        all_forecasts.append(df)

    if not all_forecasts:
        return None

    full = pd.concat(all_forecasts)
    summary = full.groupby("ár")["meðaltal"].sum().reset_index()
    summary['einingar'] = summary['meðaltal'].round(0).astype(int)
    summary['fermetrar'] = summary['einingar'] * UNIT_SIZE_SQM

    # Hlutföll módúla og kostnaður
    m1 = 0.19 * 269_700
    m2 = 0.80 * 290_000
    m3 = 0.01 * 304_500
    m4 = 0.001 * 330_000
    einingakostnaður = m1 + m2 + m3 + m4
    summary['kostnaðarverð eininga'] = summary['fermetrar'] * einingakostnaður

    summary['Flutningskostnaður'] = summary['fermetrar'] * 74000
    summary['Afhending innanlands'] = summary['fermetrar'] * 80 * 8
    summary['Fastur kostnaður'] = FIXED_COST_PER_YEAR

    summary['Heildarkostnaður'] = summary[['kostnaðarverð eininga', 'Flutningskostnaður', 'Afhending innanlands', 'Fastur kostnaður']].sum(axis=1)
    summary['Tekjur'] = summary['Heildarkostnaður'] * (1 + profit_margin)
    summary['Hagnaður'] = summary['Tekjur'] - summary['Heildarkostnaður']

    return summary


