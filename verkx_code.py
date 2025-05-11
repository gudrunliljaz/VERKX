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
FIXED_COST = 37200000

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
    mean_value = np.mean(values)
    scale = abs(mean_value * volatility)
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

def main_forecast(housing_type, region, future_years, final_market_share):
    sheet_name = f"{housing_type} eftir landshlutum"
    use_forecast = housing_type.lower() in ["íbúðir", "leikskólar"]

    past_df = load_excel(PAST_FILE, sheet_name)
    demand_column = 'fjoldi eininga'
    past_data = filter_data(past_df, region, demand_column)
    if past_data.empty:
        raise ValueError("Engin fortíðargögn fundust.")

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
        future_values = future_data['fjoldi eininga'].values[:future_years]
        future_years_vals = future_data['ar'].values[:future_years]
        market_shares = np.linspace(initial_share, final_market_share, len(future_values))
        linear_years, linear_pred = linear_forecast(past_data, demand_column, 2025, len(future_values))
        linear_pred = linear_pred[:len(future_values)]
        avg_vals = (linear_pred + future_values) / 2
        linear_pred_adj = linear_pred * market_shares
        future_values_adj = future_values * market_shares
        avg_vals_adj = avg_vals * market_shares
        sim_avg = monte_carlo_simulation(avg_vals, market_shares)
        df = pd.DataFrame({
            'Ár': future_years_vals,
            'Fortíðargögn spá': linear_pred_adj,
            'Framtíðarspá': future_values_adj,
            'Meðaltal': avg_vals_adj
        })
        figures = [
            plot_distribution(monte_carlo_simulation(linear_pred, market_shares), "Monte Carlo - Fortíðargögn"),
            plot_distribution(monte_carlo_simulation(future_values, market_shares), "Monte Carlo - Framtíðarspá"),
            plot_distribution(sim_avg, "Monte Carlo - Meðaltal")
        ]
        return df, figures, len(future_values)

def main_opperational_forecast(past_file, future_file, share_file, margin_2025=0.15, margin_2026=0.15, margin_2027=0.15, margin_2028=0.15):
    SCENARIO_SHARE = {'lágspá': 0.01, 'miðspá': 0.03, 'háspá': 0.05}
    MODULE_SIZES = {'3_módúla': 19.5, '2_módúla': 13, '1_módúla': 6.5, '½_módúla': 3.25}
    MODULE_SHARES = {'3_módúla': 0.19, '2_módúla': 0.80, '1_módúla': 0.01, '½_módúla': 0.001}
    MODULE_COSTS = {'3_módúla': 269_700, '2_módúla': 290_000, '1_módúla': 304_500, '½_módúla': 330_000}
    FIXED_COST = 34_800_000

    share_df = pd.read_excel(share_file, engine="openpyxl")
    share_df.columns = [normalize(c) for c in share_df.columns]
    share_map = {normalize(row['landshluti']): row['markaðshlutdeild'] for _, row in share_df.iterrows()}

    past_xl = pd.ExcelFile(past_file, engine="openpyxl")
    suffix = " eftir landshlutum"
    types = [s[:-len(suffix)] for s in past_xl.sheet_names if s.endswith(suffix)]
    regions = list(share_map.keys())

    all_rows = []
    for housing in types:
        sheet_name = f"{housing} eftir landshlutum"
        use_future = normalize(housing) in ['íbúðir', 'leikskólar']
        scenarios = ['miðspá'] if use_future else ['']

        for region in regions:
            share = share_map.get(region, 0)
            for scen in scenarios:
                df_past = load_excel(past_file, sheet_name)
                past = filter_data(df_past, region, "fjoldi eininga")
                years, past_pred = linear_forecast(past, "fjoldi eininga", 2025, 4)
                df_result = pd.DataFrame({'ár': years, 'fortíð': past_pred})

                if scen:
                    df_fut = load_excel(future_file, sheet_name)
                    df_fut = df_fut[df_fut['sviðsmynd'].str.lower() == scen]
                    future = filter_data(df_fut, region, "fjoldi eininga")
                    _, fut_pred = linear_forecast(future, "fjoldi eininga", 2025, 4)
                    if len(fut_pred) == 4:
                        df_result['framtíð'] = fut_pred
                        df_result['meðaltal'] = (df_result['fortíð'] + df_result['framtíð']) / 2

                base = df_result['meðaltal'] if 'meðaltal' in df_result.columns else df_result['fortíð']
                factor = SCENARIO_SHARE.get(scen, 1)
                df_result['einingar'] = base * share * factor
                df_result['ár'] = years
                all_rows.append(df_result[['ár', 'einingar']])

    df_all = pd.concat(all_rows)
    yearly_units = df_all.groupby("ár")["einingar"].sum().reset_index()
    yearly_units['heildarfermetrar'] = yearly_units['einingar'] * 6.5

    # Útreikningur á fjölda móduleininga út frá fermetrum og hlutfalli
    for key in MODULE_SHARES:
        share = MODULE_SHARES[key]
        size = MODULE_SIZES[key]
        yearly_units[f"{key} einingar"] = (yearly_units['heildarfermetrar'] * share / size).round(0)

    # Kostnaðarútreikningur
    cost_df = yearly_units[['ár']].copy()
    for key in MODULE_SHARES:
        col_name = f"kostnaður_{key}"
        cost_df[col_name] = yearly_units[f"{key} einingar"] * MODULE_SIZES[key] * MODULE_COSTS[key]

    mod_cols = [f"kostnaður_{k}" for k in MODULE_SHARES]
    cost_df['kostnaðarverð eininga'] = cost_df[mod_cols].sum(axis=1)
    cost_df['flutningskostnaður'] = yearly_units['heildarfermetrar'] * 74_000
    cost_df['afhending innanlands'] = yearly_units['heildarfermetrar'] * 80 * 8
    cost_df['fastur kostnaður'] = FIXED_COST
    cost_df['heildarkostnaður'] = cost_df[['kostnaðarverð eininga', 'flutningskostnaður', 'afhending innanlands', 'fastur kostnaður']].sum(axis=1)

    # Tekjur og hagnaður
    margin_map = {2025: margin_2025, 2026: margin_2026, 2027: margin_2027, 2028: margin_2028}
    cost_df['arðsemiskrafa'] = cost_df['ár'].map(margin_map)
    cost_df['tekjur'] = cost_df['heildarkostnaður'] * (1 + cost_df['arðsemiskrafa'])
    cost_df['hagnaður'] = cost_df['tekjur'] - cost_df['heildarkostnaður']

    return yearly_units, cost_df


#tilboðsreiknivél
def calculate_offer(modules, distance_km, eur_to_isk, markup=0.15, annual_sqm=10000, fixed_cost=37_200_000):
    data = {
        "3m": {"fm": 19.5, "verd_eur": 475, "kg": 6000},
        "2m": {"fm": 13, "verd_eur": 415, "kg": 4100},
        "1m": {"fm": 6.5, "verd_eur": 380, "kg": 2200},
        "0.5m": {"fm": 3.25, "verd_eur": 370, "kg": 1100},
    }

    einingar = {
        k: {
            "fjoldi": modules.get(k, 0),
            "fm": data[k]["fm"],
            "verd_eur": data[k]["verd_eur"],
            "kg": data[k]["kg"]
        } for k in data
    }

    heildarfm = sum(e["fjoldi"] * e["fm"] for e in einingar.values())
    heildarthyngd = sum(e["fjoldi"] * e["kg"] for e in einingar.values())

    afslattur = 0
    if heildarfm >= 650:
        afslattur = 0.10
    if heildarfm >= 1300:
        afslattur = min(0.18, 0.15 + ((heildarfm - 1300) // 325) * 0.01)

    einingakostnadur = sum(
        e["fjoldi"] * e["fm"] * e["verd_eur"] * eur_to_isk * (1 - afslattur)
        for e in einingar.values()
    )
    kostnadur_per_fm = einingakostnadur / heildarfm if heildarfm else 0
    flutningskostn = heildarfm * 43424
    sendingarkostn = heildarfm * distance_km * 8
    breytilegur = einingakostnadur + flutningskostn + sendingarkostn
    fastur_kostn = (heildarfm / annual_sqm) * fixed_cost if heildarfm else 0
    alagsstudull = 1 + (fastur_kostn / breytilegur) if breytilegur else 0
    tilbod = breytilegur * alagsstudull * (1 + markup)
    tilbod_eur = tilbod / eur_to_isk if eur_to_isk else 0

    return {
        "heildarfm": heildarfm,
        "heildarthyngd": heildarthyngd,
        "afslattur": afslattur,
        "heildarkostnadur_einingar": einingakostnadur,
        "kostnadur_per_fm": kostnadur_per_fm,
        "flutningur_til_islands": flutningskostn,
        "sendingarkostnadur": sendingarkostn,
        "samtals_breytilegur": breytilegur,
        "uthlutadur_fastur_kostnadur": fastur_kostn,
        "alagsstudull": alagsstudull,
        "arðsemiskrafa": markup,
        "tilbod": tilbod,
        "tilbod_eur": tilbod_eur,
        "dags": date.today()
    }




def generate_offer_pdf(verkkaupi, stadsetning, result, language="Íslenska"):
    pdf = FPDF()
    pdf.add_page()
    pdf.add_font('DejaVu', '', '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', uni=True)
    pdf.set_font('DejaVu', '', 12)
    pdf.image("cubitlogo.png", x=10, y=8, w=30)

    pdf.set_xy(50, 10)
    pdf.set_font('DejaVu', '', 16)
    title = "Tilboð - Cubit" if language == "Íslenska" else "Offer - Cubit"
    pdf.cell(0, 10, title, ln=True)

    pdf.set_font('DejaVu', '', 10)
    pdf.set_xy(50, 20)
    today = date.today().strftime('%d.%m.%Y')
    label_date = "Dagsetning" if language == "Íslenska" else "Date"
    pdf.cell(0, 10, f"{label_date}: {today}", ln=True)

    pdf.ln(20)
    pdf.set_font('DejaVu', '', 12)

    # Labels eftir tungumáli
    labels = {
        "Íslenska": [
            ("Tilboð fyrir", verkkaupi),
            ("Afhendingarstaður", stadsetning),
            ("Heildarfermetrar", f"{result['heildarfm']:.2f} fm"),
            ("Heildarþyngd", f"{result['heildarthyngd']:,.0f} kg"),
            ("Afsláttur", f"{int(result['afslattur'] * 100)}%"),
            ("Kaupverð eininga", f"{result['heildarkostnadur_einingar']:,.0f} kr."),
            ("Kostnaðarverð á fermetra", f"{result['kostnadur_per_fm']:,.0f} kr."),
            ("Flutningur til Íslands", f"{result['flutningur_til_islands']:,.0f} kr."),
            ("Sendingarkostnaður innanlands", f"{result['sendingarkostnadur']:,.0f} kr."),
            ("Samtals breytilegur kostnaður", f"{result['samtals_breytilegur']:,.0f} kr."),
            ("Úthlutaður fastur kostnaður", f"{result['uthlutadur_fastur_kostnadur']:,.0f} kr."),
            ("Álagsstuðull", f"{result['alagsstudull']:.2f}"),
            ("Arðsemiskrafa", f"{int(result['arðsemiskrafa'] * 100)}%"),
            ("Tilboðsverð (ISK)", f"{result['tilbod']:,.0f} kr."),
            ("Tilboðsverð (EUR)", f"€{result['tilbod_eur']:,.2f}")
        ],
        "English": [
            ("Offer for", verkkaupi),
            ("Delivery location", stadsetning),
            ("Total area", f"{result['heildarfm']:.2f} sqm"),
            ("Total weight", f"{result['heildarthyngd']:,.0f} kg"),
            ("Discount", f"{int(result['afslattur'] * 100)}%"),
            ("Unit purchase cost", f"{result['heildarkostnadur_einingar']:,.0f} ISK"),
            ("Cost per sqm", f"{result['kostnadur_per_fm']:,.0f} ISK"),
            ("Shipping to Iceland", f"{result['flutningur_til_islands']:,.0f} ISK"),
            ("Domestic delivery", f"{result['sendingarkostnadur']:,.0f} ISK"),
            ("Total variable cost", f"{result['samtals_breytilegur']:,.0f} ISK"),
            ("Allocated fixed cost", f"{result['uthlutadur_fastur_kostnadur']:,.0f} ISK"),
            ("Markup factor", f"{result['alagsstudull']:.2f}"),
            ("Profit margin", f"{int(result['arðsemiskrafa'] * 100)}%"),
            ("Offer price (ISK)", f"{result['tilbod']:,.0f} ISK"),
            ("Offer price (EUR)", f"€{result['tilbod_eur']:,.2f}")
        ]
    }

    for label, value in labels[language]:
        pdf.cell(0, 10, f"{label}: {value}", ln=True)

    return pdf.output(dest="S").encode("latin-1")



