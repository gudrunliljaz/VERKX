import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.linear_model import LinearRegression

PAST_FILE = "/data/GÖGN_VERKX.xlsx"
FUTURE_FILE = "/data/Framtíðarspá.xlsx"

def load_excel(file_path, sheet_name):
    df = pd.read_excel(file_path, sheet_name=sheet_name, engine="openpyxl")
    df.columns = [col.strip().lower() for col in df.columns]
    return df

def filter_data(df, region, demand_column):
    df = df[df['landshluti'].str.strip() == region.strip()].copy()
    df.columns = [col.strip().lower() for col in df.columns]
    demand_column = demand_column.lower()
    if demand_column not in df.columns:
        raise KeyError(f"Dálkur '{demand_column}' fannst ekki í gögnum.")
    df['ar'] = pd.to_numeric(df['ar'], errors='coerce')
    df = df.dropna(subset=['ar', demand_column])
    df = df.sort_values('ar')
    return df[['ar', demand_column]]

def linear_forecast(df, demand_column, start_year, future_years):
    X = df[['ar']].values
    y = df[demand_column].values
    model = LinearRegression().fit(X, y)

    future_years_range = np.arange(start_year, start_year + future_years)
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

def plot_all_distributions(sim_data_list, titles):
    fig, axs = plt.subplots(1, len(sim_data_list), figsize=(5 * len(sim_data_list), 4))
    if len(sim_data_list) == 1:
        axs = [axs]
    for ax, sim, title in zip(axs, sim_data_list, titles):
        totals = np.sum(sim, axis=1)
        ax.hist(totals, bins=40, alpha=0.7, edgecolor='black')
        ax.set_title(title)
        ax.set_xlabel("Heildar spáð þörf")
        ax.set_ylabel("Tíðni")
    plt.tight_layout()
    plt.show()

def main():
    housing_type = input("Hvaða tegund húsnæðis viltu skoða? ").strip()
    housing_type_lower = housing_type.lower()
    region = input("Hvaða landshluta? ").strip()
    future_years = int(input("Fyrir hversu mörg ár fram í tímann? "))
    final_market_share = float(input("Hver er markaðshlutdeildin? (t.d. 0.3 fyrir 30%) "))

    initial_share = final_market_share * np.random.uniform(0.05, 0.1)
    market_shares = np.linspace(initial_share, final_market_share, future_years)

    sheet_name = f"{housing_type} eftir landshlutum"
    use_forecast = housing_type_lower in ["íbúðir", "leikskólar"]

    try:
        past_df = load_excel(PAST_FILE, sheet_name)
    except Exception as e:
        print(f"Villa við lestur á fortíðargögnum: {e}")
        return

    demand_column = 'fjoldi eininga'
    try:
        past_data = filter_data(past_df, region, demand_column)
    except KeyError as e:
        print(e)
        return

    if past_data.empty:
        print("Engin fortíðargögn fundust fyrir valinn landshluta.")
        return

    if use_forecast:
        try:
            future_df = load_excel(FUTURE_FILE, sheet_name)
            if 'sviðsmynd' in future_df.columns:
                future_df = future_df[future_df['sviðsmynd'].str.lower() == 'miðspá']
        except Exception as e:
            print(f"Villa við lestur á framtíðarspá: {e}")
            return

        try:
            future_df['ar'] = pd.to_numeric(future_df['ar'], errors='coerce')
            future_data = filter_data(future_df, region, 'fjoldi eininga')
            # HENDUM ÁRUM FYRIR 2025 BÚRT!!
            future_data = future_data[future_data['ar'] >= 2025]
        except KeyError as e:
            print(e)
            return

        if future_data.empty:
            print("Engin framtíðarspágögn fundust.")
            return

        future_vals = future_data['fjoldi eininga'].values
        future_years_vals = future_data['ar'].values

        start_year = 2025
        linear_years, linear_pred = linear_forecast(past_data, demand_column, start_year, future_years)

        if len(future_vals) >= future_years:
            future_vals = future_vals[:future_years]
            future_years_vals = future_years_vals[:future_years]

            linear_pred = linear_pred[:future_years]
            avg_vals = (linear_pred + future_vals) / 2

            linear_pred_adj = linear_pred * market_shares
            future_vals_adj = future_vals * market_shares
            avg_vals_adj = avg_vals * market_shares

            sim_past = monte_carlo_simulation(linear_pred, market_shares)
            sim_future = monte_carlo_simulation(future_vals, market_shares)
            sim_avg = monte_carlo_simulation(avg_vals, market_shares)

            print("\n Einingaþörf eftir ári:")
            for i, year in enumerate(future_years_vals):
                print(f"{year}: Spá útfrá fortíðargögnum = {linear_pred_adj[i]:.2f}, Framtíðarspá = {future_vals_adj[i]:.2f}, Meðaltal = {avg_vals_adj[i]:.2f}")

            mean_past = np.mean(linear_pred_adj)
            mean_future = np.mean(future_vals_adj)
            mae = abs(mean_past - mean_future)

            std_past = np.std(linear_pred_adj)
            std_future = np.std(future_vals_adj)

            print(f"\nMeðaltal fortíðargagna: {mean_past:.2f} (staðalfrávik={std_past:.2f})")
            print(f"Meðaltal framtíðarspár: {mean_future:.2f} (staðalfrávik={std_future:.2f})")
            print(f"\nMAE milli meðaltals fortíðar og framtíðar: {mae:.2f}")

            if mean_future > 5:
                accuracy = max(0, 100 - (mae / mean_future) * 100)
                print(f"Nákvæmni spár: {accuracy:.2f}%")
            else:
                print("Nákvæmni ekki marktæk þar sem meðaltal framtíðarspár er of lágt (<5 einingar að meðaltali).")

            plot_all_distributions([sim_past, sim_future, sim_avg], ["Fortíðargögn", "Framtíðarspá", "Meðaltal"])

        else:
            print("\nATH! Framtíðarspáin er of stutt. Notum aðeins fortíðargögn.")
            linear_years, linear_pred = linear_forecast(past_data, demand_column, start_year, future_years)
            market_shares = np.linspace(initial_share, final_market_share, future_years)
            past_pred_adj = linear_pred * market_shares
            sim_past = monte_carlo_simulation(linear_pred, market_shares)

            print("\n Framtíðarþörf útfrá fortíðargreiningu:")
            for year, demand in zip(linear_years, past_pred_adj):
                print(f"{year}: {demand:.2f} einingar")

            mean_past = np.mean(past_pred_adj)
            std_past = np.std(past_pred_adj)
            print(f"\n Meðaltal: {mean_past:.2f} (staðalfrávik={std_past:.2f})")

            plot_all_distributions([sim_past], ["Monte Carlo – Fortíðargögn"])

    else:
        start_year = 2025
        linear_years, linear_pred = linear_forecast(past_data, demand_column, start_year, future_years)
        market_shares = np.linspace(initial_share, final_market_share, future_years)
        past_pred_adj = linear_pred * market_shares
        sim_past = monte_carlo_simulation(linear_pred, market_shares)

        print("\n Framtíðarþörf útfrá fortíðargreiningu:")
        for year, demand in zip(linear_years, past_pred_adj):
            print(f"{year}: {demand:.2f} einingar")

        mean_past = np.mean(past_pred_adj)
        std_past = np.std(past_pred_adj)
        print(f"\n Meðaltal: {mean_past:.2f} (staðalfrávik={std_past:.2f})")

        plot_all_distributions([sim_past], ["Monte Carlo – Fortíðargögn"])

if __name__ == "__main__":
    main()












