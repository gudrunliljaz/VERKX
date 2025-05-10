import pandas as pd
import numpy as np
import unicodedata
from sklearn.linear_model import LinearRegression

PAST_FILE = "data/GÖGN_VERKX.xlsx"
FUTURE_FILE = "data/Framtidarspa.xlsx"
SHARE_FILE = "data/markadshlutdeild.xlsx"
UNIT_SIZE_SQM = 6.5
FIXED_COST_PER_YEAR = 37_200_000

MODULE_SHARES = {
    '3_módúla': 0.19,
    '2_módúla': 0.80,
    '1_módúla': 0.01,
    '½_módúla': 0.001,
}
MODULE_COSTS = {
    '3_módúla': 269700,
    '2_módúla': 290000,
    '1_módúla': 304500,
    '½_módúla': 330000,
}
MODULE_FM = {
    '3_módúla': 19.5,
    '2_módúla': 13,
    '1_módúla': 6.5,
    '½_módúla': 3.25,
}

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

def main_forecast_logic_from_excel(
    past_file,
    future_file,
    share_file,
    margin_2025=0.15,
    margin_2026=0.15,
    margin_2027=0.15,
    margin_2028=0.15
):
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
                years, pred = linear_forecast(past, "fjoldi eininga", 2025, 4)
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
    summary["Kostnaðarverð eininga"] = summary["Fermetrar"] * (0.19*269700 + 0.80*290000 + 0.01*304500 + 0.001*330000)
    summary["Flutningskostnaður"] = summary["Fermetrar"] * 43424
    summary["Afhending innanlands"] = summary["Fermetrar"] * 80 * 8
    summary["Fastur kostnaður"] = FIXED_COST_PER_YEAR
    summary["Heildarkostnaður"] = summary[["Kostnaðarverð eininga", "Flutningskostnaður", "Afhending innanlands", "Fastur kostnaður"]].sum(axis=1)

    # Mismunandi arðsemiskrafa eftir ári
    margin_map = {
        2025: margin_2025,
        2026: margin_2026,
        2027: margin_2027,
        2028: margin_2028
    }
    summary["Arðsemiskrafa"] = summary["Ár"].map(margin_map)
    summary["Tekjur"] = summary["Heildarkostnaður"] * (1 + summary["Arðsemiskrafa"])
    summary["Hagnaður"] = summary["Tekjur"] - summary["Heildarkostnaður"]

    return summary


