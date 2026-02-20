# code/m1_data_pipeline.py

from __future__ import annotations
import pandas as pd
from config_paths import RAW_DATA_DIR, FINAL_DATA_DIR


def month_from_ym(ym: pd.Series) -> pd.Series:
    """
    Your dataset uses ym like "2003m10" (not 200310).
    Convert "YYYYmM" -> datetime month start "YYYY-MM-01".
    """
    s = ym.astype(str).str.strip().str.lower()
    year = s.str.extract(r"(\d{4})", expand=False)
    month = s.str.extract(r"m(\d{1,2})", expand=False).str.zfill(2)
    return pd.to_datetime(year + "-" + month + "-01", errors="coerce")


def main():
    # 1) Load REIT data (you renamed the file to reit_master.csv ✅)
    reit_path = RAW_DATA_DIR / "reit_master.csv"
    df = pd.read_csv(reit_path)

    # 2) Build month key
    if "ym" not in df.columns:
        raise ValueError("Column 'ym' not found. Open the CSV and confirm the column name.")
    df["month"] = month_from_ym(df["ym"])
    df = df.dropna(subset=["month"])

    # 3) Keep important columns (these exist in your file from the screenshot)
    keep = [
        "permno", "ticker", "connam", "rtype", "ptype", "psub",
        "date", "caldt", "ym", "usdret", "usdprc",
        "market_equity", "assets", "sales", "month"
    ]
    keep = [c for c in keep if c in df.columns]
    df = df[keep].copy()

    # 4) Cleaning (simple + defendable)
    # Drop rows where return is missing
    if "usdret" in df.columns:
        before = len(df)
        df = df.dropna(subset=["usdret"])
        dropped_ret = before - len(df)
    else:
        dropped_ret = 0

    # 5) Ensure one row per (permno, month)
    if "permno" not in df.columns:
        raise ValueError("Column 'permno' not found. Open the CSV and confirm the column name.")
    dupes = df.duplicated(subset=["permno", "month"]).sum()
    if dupes > 0:
        raise ValueError(f"Duplicate (permno, month) rows found: {dupes}")

    # 6) Save final panel
    out_csv = FINAL_DATA_DIR / "m1_panel.csv"
    df.to_csv(out_csv, index=False)

    # 7) Save metadata
    meta_path = FINAL_DATA_DIR / "m1_metadata.txt"
    meta = []
    meta.append("Milestone 1: Data Pipeline Metadata\n\n")
    meta.append(f"Input file: {reit_path}\n")
    meta.append(f"Output file: {out_csv}\n")
    meta.append("Panel structure: Entity=permno (REIT), Time=month\n\n")
    meta.append(f"Rows: {len(df)}\n")
    meta.append(f"Unique REITs: {df['permno'].nunique()}\n")
    meta.append(f"Date range: {df['month'].min().date()} to {df['month'].max().date()}\n\n")
    meta.append("Cleaning decisions:\n")
    meta.append("- Dropped rows with invalid month parsed from ym\n")
    meta.append(f"- Dropped rows with missing usdret (monthly return): {dropped_ret}\n")
    meta_path.write_text("".join(meta), encoding="utf-8")

    print("✅ Milestone 1 complete!")
    print("Saved:", out_csv)
    print("Saved:", meta_path)


if __name__ == "__main__":
    main()