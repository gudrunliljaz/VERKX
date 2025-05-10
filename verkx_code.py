import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.linear_model import LinearRegression
import unicodedata
from datetime import date
from fpdf import FPDF
from io import BytesIO

PAST_FILE = "data/GÖGN_VERKX.xlsx"
FUTURE_FILE = "data/Framtidarspa.xlsx"
SHARE_FILE = "data/markadshlutdeild.xlsx"

UNIT_SIZE_SQM = 6.5
FIXED_COST_PER_YEAR = 37_200_000

def normalize(text):
    nfkd = unicodedata.normalize('NFKD', str(text))
    return ''.join(c for c in nfkd if not unicodedata.combining(c)).lower().strip()

def load_excel(file_path, sheet_name):
    df = pd.read_excel(file_path, sheet_name=sheet_name, engine="openpyxl")
    df.columns = [col.strip().lower() for col in df.columns]
    return df

def filter_data(df, region, demand_column):
    df = df[df['landshluti'].str.strip().map(normalize) == normalize(region)].copy()
    df.columns = [col.strip().lower() for col in df.columns]
    demand_column = demand_column.lower()
    if demand_column not in df.columns:
        raise KeyError(f"'{demand_column}' fannst ekki.")
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
            use_forecast = False

    if not use_forecast:
        linear_years, linear_pred = linear_forecast(past_data, demand_column, 2025, future_years)
        market_shares = np.linspace(initial_share, final_market_share, future_years)
        past_pred_adj = linear_pred * market_shares
        sim_past = monte_carlo_simulation(linear_pred, market_shares)
        df = pd.DataFrame({'Ár': linear_years, 'Spá útfrá fortíðargögnum': past_pred_adj})
        figures = [plot_distribution(sim_past, "Monte Carlo - Fortíðargögn")]
        return df, figures, future_years
    else:
        future_vals = future_data['fjoldi eininga'].values[:future_years]
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
        return df, figures, len(future_vals)

def main_forecast_logic_from_excel(past_file, future_file, share_file):
    xl = pd.ExcelFile(share_file, engine="openpyxl")
    all_rows = []

    for sheet in xl.sheet_names:
        df_share = xl.parse(sheet)
        df_share.columns = [normalize(c) for c in df_share.columns]
        df_share['landshluti'] = df_share['landshluti'].map(normalize)
        if 'markaðshlutdeild' not in df_share.columns or 'landshluti' not in df_share.columns:
            continue

        housing_type = sheet.strip()
        sheet_name = f"{housing_type} eftir landshlutum"

        for _, row in df_share.iterrows():
            landshluti = row['landshluti']
            share = row['markaðshlutdeild']

            try:
                df_past = pd.read_excel(past_file, sheet_name=sheet_name, engine="openpyxl")
                df_past.columns = [normalize(c) for c in df_past.columns]
                past = filter_data(df_past, landshluti, "fjoldi eininga")
                if past.empty:
                    continue
                years, pred = linear_forecast(past, "fjoldi eininga", 2025, 5)
                adj_pred = pred * share
                df_adj = pd.DataFrame({"Ár": years, "Meðaltal": adj_pred})
                all_rows.append(df_adj)
            except Exception:
                continue

    if not all_rows:
        return None

    df_all = pd.concat(all_rows)
    summary = df_all.groupby("Ár")["Meðaltal"].sum().reset_index()
    summary["Fermetrar"] = summary["Meðaltal"].round(0).astype(int) * UNIT_SIZE_SQM

    for key in MODULE_SHARES:
        col_name = f'kostnaður_{key}'
        summary[col_name] = summary['Fermetrar'] * MODULE_SHARES[key] * MODULE_COSTS[key] * MODULE_FM[key]

    mod_cols = [f'kostnaður_{k}' for k in MODULE_SHARES]
    summary["Kostnaðarverð eininga"] = summary[mod_cols].sum(axis=1)

    summary["Flutningskostnaður"] = (
        summary["Fermetrar"] * 0.19 * 19.5 +
        summary["Fermetrar"] * 0.80 * 13 +
        summary["Fermetrar"] * 0.01 * 6.5
    ) * 74000

    summary["Afhending innanlands"] = (
        summary["Fermetrar"] * 0.19 * 19.5 +
        summary["Fermetrar"] * 0.80 * 13 +
        summary["Fermetrar"] * 0.01 * 6.5
    ) * 80 * 8

    summary["Fastur kostnaður"] = FIXED_COST_PER_YEAR

    summary["Heildarkostnaður"] = summary[[
        "Kostnaðarverð eininga",
        "Flutningskostnaður",
        "Afhending innanlands",
        "Fastur kostnaður"
    ]].sum(axis=1)

    return summary


def calculate_offer(modules, distance_km, eur_to_isk, markup=0.15, annual_sqm=10000, fixed_cost=37_200_000):
    quotation_labels_dict = {
        "3m": {"fm": 39, "verd_eur": 475, "kg": 6000},
        "2m": {"fm": 26, "verd_eur": 415, "kg": 4100},
        "1m": {"fm": 13, "verd_eur": 380, "kg": 2200},
        "0.5m": {"fm": 6.5, "verd_eur": 370, "kg": 1100},
    }

    einingar = {
        key: {
            "fjoldi": modules.get(key, 0),
            "fm": quotation_labels_dict[key]["fm"],
            "verd_eur": quotation_labels_dict[key]["verd_eur"],
            "kg": quotation_labels_dict[key]["kg"]
        }
        for key in quotation_labels_dict
    }

    heildarfm = sum(e["fjoldi"] * e["fm"] for e in einingar.values())
    heildarthyngd = sum(e["fjoldi"] * e["kg"] for e in einingar.values())

    afslattur = 0
    if heildarfm >= 650:
        afslattur = 0.10
    if heildarfm >= 1300:
        afslattur = 0.15 + ((heildarfm - 1300) // 325) * 0.01
        afslattur = min(afslattur, 0.18)

    heildarkostnadur_einingar = sum(
        e["fjoldi"] * e["fm"] * e["verd_eur"] * eur_to_isk * (1 - afslattur)
        for e in einingar.values()
    )
    kostnadur_per_fm = heildarkostnadur_einingar / heildarfm if heildarfm else 0

    flutningur_til_islands = heildarfm * 43424
    sendingarkostnadur = heildarfm * distance_km * 8
    samtals_breytilegur = heildarkostnadur_einingar + flutningur_til_islands + sendingarkostnadur

    uthlutadur_fastur_kostnadur = (heildarfm / annual_sqm) * fixed_cost if heildarfm else 0
    alagsstudull = 1 + (uthlutadur_fastur_kostnadur / samtals_breytilegur) if samtals_breytilegur else 0

    tilbod = samtals_breytilegur * alagsstudull * (1 + markup)
    tilbod_eur = tilbod / eur_to_isk if eur_to_isk else 0

    return {
        "heildarfm": heildarfm,
        "heildarthyngd": heildarthyngd,
        "afslattur": afslattur,
        "heildarkostnadur_einingar": heildarkostnadur_einingar,
        "kostnadur_per_fm": kostnadur_per_fm,
        "flutningur_til_islands": flutningur_til_islands,
        "sendingarkostnadur": sendingarkostnadur,
        "samtals_breytilegur": samtals_breytilegur,
        "uthlutadur_fastur_kostnadur": uthlutadur_fastur_kostnadur,
        "alagsstudull": alagsstudull,
        "asemiskrafa": markup,
        "tilbod": tilbod,
        "tilbod_eur": tilbod_eur,
        "dags": date.today()
    }

def generate_offer_pdf(verkkaupi, stadsetning, result):
    from fpdf import FPDF

    pdf = FPDF()
    pdf.add_page()
    pdf.add_font('DejaVu', '', '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', uni=True)
    pdf.set_font('DejaVu', '', 12)

    pdf.cell(0, 10, f"Tilboð fyrir: {verkkaupi}", ln=True)
    pdf.cell(0, 10, f"Afhendingarstaður: {stadsetning}", ln=True)
    pdf.cell(0, 10, f"Heildarfermetrar: {result['heildarfm']:.2f} fm", ln=True)
    pdf.cell(0, 10, f"Heildarþyngd: {result['heildarthyngd']:,.0f} kg", ln=True)
    pdf.cell(0, 10, f"Afsláttur: {int(result['afslattur'] * 100)}%", ln=True)
    pdf.cell(0, 10, f"Tilboðsverð (ISK): {result['tilbod']:,.0f} kr.", ln=True)
    pdf.cell(0, 10, f"Tilboðsverð (EUR): €{result['tilbod_eur']:,.2f}", ln=True)

    # Skila PDF sem byte array
    pdf_bytes = pdf.output(dest='S').encode('latin-1')
    return pdf_bytes

