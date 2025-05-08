import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
import unicodedata

# Skrár
PAST_FILE = "data/GÖGN_VERKX.xlsx"
FUTURE_FILE = "data/Framtidarspa.xlsx"
SHARE_FILE = "data/markadshlutdeild.xlsx"

# Fastar
DEMAND_COLUMN = 'fjöldi eininga'
ARDSEMISKRAFA = 0.15
MODULE_SHARES = {
    '3_módúla': 0.19,
    '2_módúla': 0.80,
    '1_módúla': 0.01,
    '½_módúla': 0.001,
}
MODULE_COSTS = {
    '3_módúla': 269_700,
    '2_módúla': 290_000,
    '1_módúla': 304_500,
    '½_módúla': 330_000,
}
MODULE_FM = {
    '3_módúla': 19.5,
    '2_módúla': 13,
    '1_módúla': 6.5,
    '½_módúla': 3.25,
}
SCENARIO_SHARE = {
    'lágspá': 0.01,
    'miðspá': 0.03,
    'háspá': 0.05,
}

def normalize(text):
    nfkd = unicodedata.normalize('NFKD', str(text))
    return ''.join(c for c in nfkd if not unicodedata.combining(c)).lower().strip()

def load_excel(path, sheet_name):
    book = pd.ExcelFile(path, engine="openpyxl")
    target = normalize(sheet_name)
    for sheet in book.sheet_names:
        if normalize(sheet) == target:
            return pd.read_excel(path, sheet_name=sheet, engine="openpyxl")
    raise ValueError(f"Sheet '{sheet_name}' fannst ekki.")

def filter_data(df, region, col):
    df = df.copy()
    df.columns = [normalize(c) for c in df.columns]
    df = df[df['landshluti'].map(normalize) == normalize(region)]
    df.loc[:, 'ar'] = pd.to_numeric(df['ar'], errors='coerce')
    demand = normalize(col)
    df = df.dropna(subset=['ar', demand]).sort_values('ar')
    return df[['ar', demand]]

def linear_forecast(df, col, start_year, n_years):
    if df.empty:
        return np.array([]), np.array([])
    X = df[['ar']].values
    y = df[col].values
    model = LinearRegression().fit(X, y)
    years = np.arange(start_year, start_year + n_years)
    preds = model.predict(years.reshape(-1,1))
    preds = np.maximum(0, preds)
    return years, preds

def load_combined_share_file(filepath):
    df = pd.read_excel(filepath, engine="openpyxl")
    df.columns = [normalize(c) for c in df.columns]
    df['landshluti'] = df['landshluti'].map(normalize)
    df['tegund'] = df['tegund'].map(normalize)
    return df

def main_forecast_logic_from_excel(past_file, future_file, share_file, profit_margin=ARDSEMISKRAFA):
    share_df = load_combined_share_file(share_file)
    required_cols = {"tegund", "landshluti", "markaðshlutdeild"}
    if not required_cols.issubset(set(share_df.columns)):
        raise ValueError("Excel-skráin verður að innihalda dálkana: 'tegund', 'landshluti', 'markaðshlutdeild'")

    markets = share_df.to_dict("records")
    all_forecasts = []
    future_years = 5

    for market in markets:
        housing = market["tegund"]
        region = market["landshluti"]
        share = market["markaðshlutdeild"]
        sheet = f"{housing} eftir landshlutum"
        use_future = housing in ['íbúðir', 'leikskólar']
        scenarios = ['miðspá'] if use_future else ['']

        for scen in scenarios:
            df_past = load_excel(past_file, sheet)
            past = filter_data(df_past, region, DEMAND_COLUMN)
            years, past_pred = linear_forecast(past, DEMAND_COLUMN, 2025, future_years)
            if years.size == 0:
                continue

            df_res = pd.DataFrame({'ár': years, 'fortíð': past_pred})

            if scen:
                df_fut = load_excel(future_file, sheet)
                fut = df_fut[df_fut['sviðsmynd'].str.lower().map(normalize) == scen]
                fut = filter_data(fut, region, DEMAND_COLUMN)
                _, fut_pred = linear_forecast(fut, DEMAND_COLUMN, 2025, future_years)
                if fut_pred.size:
                    df_res['framtíð'] = fut_pred
                    df_res['meðaltal'] = (df_res['fortíð'] + df_res['framtíð']) / 2

            factor = SCENARIO_SHARE.get(normalize(scen), 1)
            df_res['adj_meðaltal'] = df_res.get('meðaltal', df_res['fortíð']) * share * factor
            all_forecasts.append(df_res[['ár', 'adj_meðaltal']])

    if not all_forecasts:
        return None

    combined = pd.concat(all_forecasts)
    summary = combined.groupby("ár")["adj_meðaltal"].sum().reset_index()
    summary['fermetrar'] = summary['adj_meðaltal'].round(0).astype(int)

    # Kostnaður eftir módúlum
    for key in MODULE_SHARES:
        col_name = f'kostnaður_{key}'
        summary[col_name] = summary['fermetrar'] * MODULE_SHARES[key] * MODULE_COSTS[key] * MODULE_FM[key]

    mod_cols = [f'kostnaður_{k}' for k in MODULE_SHARES]
    summary['kostnaðarverð eininga'] = summary[mod_cols].sum(axis=1)
    summary['Flutningskostnaður'] = summary['fermetrar'] * 74000
    summary['Afhending innanlands'] = summary['fermetrar'] * 80 * 8
    summary['Fastur kostnaður'] = 34_800_000

    summary['Heildarkostnaður'] = summary[
        ['kostnaðarverð eininga', 'Flutningskostnaður', 'Afhending innanlands', 'Fastur kostnaður']
    ].sum(axis=1)
    summary['Tekjur'] = summary['Heildarkostnaður'] * (1 + profit_margin)
    summary['Hagnaður'] = summary['Tekjur'] - summary['Heildarkostnaður']

    return summary





