def main_forecast_logic_from_excel(past_file, future_file, share_file, profit_margin=0.15):
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
                df_adj = pd.DataFrame({"ár": years, "meðaltal": adj_pred})
                all_rows.append(df_adj)
            except Exception as e:
                continue  # quietly skip if sheet/data isn't usable

    if not all_rows:
        return None

    df_all = pd.concat(all_rows)
    summary = df_all.groupby("ár")["meðaltal"].sum().reset_index()
    summary["fermetrar"] = summary["meðaltal"].round(0).astype(int) * UNIT_SIZE_SQM
    summary["kostnaðarverð eininga"] = summary["fermetrar"] * (0.19*269700 + 0.80*290000 + 0.01*304500 + 0.001*330000)
    summary["Flutningskostnaður"] = summary["fermetrar"] * 74000
    summary["Afhending innanlands"] = summary["fermetrar"] * 80 * 8
    summary["Fastur kostnaður"] = FIXED_COST_PER_YEAR
    summary["Heildarkostnaður"] = summary[["kostnaðarverð eininga", "Flutningskostnaður", "Afhending innanlands", "Fastur kostnaður"]].sum(axis=1)
    summary["Tekjur"] = summary["Heildarkostnaður"] * (1 + profit_margin)
    summary["Hagnaður"] = summary["Tekjur"] - summary["Heildarkostnaður"]
    return summary



