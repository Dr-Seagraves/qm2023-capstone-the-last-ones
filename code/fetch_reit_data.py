from __future__ import annotations

import pandas as pd

from config_paths import PROCESSED_DATA_DIR, RAW_DATA_DIR


def month_from_ym(ym: pd.Series) -> pd.Series:
    s = ym.astype(str).str.strip().str.lower()
    year = s.str.extract(r"(\d{4})", expand=False)
    month = s.str.extract(r"m(\d{1,2})", expand=False).str.zfill(2)
    return pd.to_datetime(year + "-" + month + "-01", errors="coerce")


def fetch_reit_data() -> tuple[pd.DataFrame, int]:
    reit_path = RAW_DATA_DIR / "reit_master.csv"
    out_path = PROCESSED_DATA_DIR / "m1_reit_base.csv"

    df = pd.read_csv(reit_path)

    if "ym" not in df.columns:
        raise ValueError("Column 'ym' not found. Open the CSV and confirm the column name.")

    df["month"] = month_from_ym(df["ym"])
    invalid_month_rows = int(df["month"].isna().sum())
    df = df.dropna(subset=["month"]).copy()

    keep = [
        "permno",
        "ticker",
        "connam",
        "rtype",
        "ptype",
        "psub",
        "date",
        "caldt",
        "ym",
        "usdret",
        "usdprc",
        "market_equity",
        "assets",
        "sales",
        "month",
    ]
    keep = [column for column in keep if column in df.columns]
    df = df[keep].copy()

    df.to_csv(out_path, index=False)
    return df, invalid_month_rows


def main() -> None:
    df, invalid_month_rows = fetch_reit_data()
    out_path = PROCESSED_DATA_DIR / "m1_reit_base.csv"

    print("✅ Fetch step complete")
    print("Saved:", out_path)
    print("Rows:", len(df))
    print("Dropped rows with invalid month parsed from ym:", invalid_month_rows)


if __name__ == "__main__":
    main()
