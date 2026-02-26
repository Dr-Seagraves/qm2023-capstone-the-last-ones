from __future__ import annotations

import pandas as pd

from config_paths import FINAL_DATA_DIR, PROCESSED_DATA_DIR, RAW_DATA_DIR


def build_data_dictionary(df: pd.DataFrame, out_path) -> None:
    source_dictionary_path = RAW_DATA_DIR / "REIT_data_dictionary.csv"
    source_dictionary = pd.read_csv(source_dictionary_path)

    final_columns = list(df.columns)
    subset = source_dictionary[source_dictionary["variable"].isin(final_columns)].copy()

    fallback_descriptions = {
        "month": "Month key parsed from ym (YYYY-MM-01)",
    }

    missing_columns = [column for column in final_columns if column not in subset["variable"].tolist()]
    if missing_columns:
        fallback_rows = pd.DataFrame(
            {
                "variable": missing_columns,
                "dtype": [str(df[column].dtype) for column in missing_columns],
                "description": [fallback_descriptions.get(column, "Variable included in final panel") for column in missing_columns],
                "source": ["Derived" for _ in missing_columns],
                "category": ["Derived" for _ in missing_columns],
                "unit": ["" for _ in missing_columns],
                "missing_pct": ["" for _ in missing_columns],
                "min": ["" for _ in missing_columns],
                "max": ["" for _ in missing_columns],
                "example": ["" for _ in missing_columns],
                "notes": ["" for _ in missing_columns],
            }
        )
        subset = pd.concat([subset, fallback_rows], ignore_index=True)

    subset["_order"] = subset["variable"].map({name: idx for idx, name in enumerate(final_columns)})
    subset = subset.sort_values("_order").drop(columns=["_order"])

    keep_columns = [
        "variable",
        "dtype",
        "description",
        "source",
        "category",
        "unit",
        "notes",
    ]
    subset = subset[[column for column in keep_columns if column in subset.columns]]
    subset.to_csv(out_path, index=False)


def merge_final_panel() -> pd.DataFrame:
    in_path = PROCESSED_DATA_DIR / "m1_reit_base.csv"
    out_csv = FINAL_DATA_DIR / "m1_panel.csv"
    meta_path = FINAL_DATA_DIR / "m1_metadata.txt"
    dictionary_path = FINAL_DATA_DIR / "m1_data_dictionary.csv"

    df = pd.read_csv(in_path)

    if "usdret" in df.columns:
        before = len(df)
        df = df.dropna(subset=["usdret"]).copy()
        dropped_ret = before - len(df)
    else:
        dropped_ret = 0

    if "permno" not in df.columns:
        raise ValueError("Column 'permno' not found. Open the CSV and confirm the column name.")
    dupes = int(df.duplicated(subset=["permno", "month"]).sum())
    if dupes > 0:
        raise ValueError(f"Duplicate (permno, month) rows found: {dupes}")

    df = df.sort_values(["permno", "month"]).reset_index(drop=True)
    df.to_csv(out_csv, index=False)

    meta = []
    meta.append("Milestone 1: Data Pipeline Metadata\n\n")
    meta.append(f"Input file: {in_path}\n")
    meta.append(f"Output file: {out_csv}\n")
    meta.append("Panel structure: Entity=permno (REIT), Time=month\n\n")
    meta.append(f"Rows: {len(df)}\n")
    meta.append(f"Unique REITs: {df['permno'].nunique()}\n")
    meta.append(f"Date range: {pd.to_datetime(df['month']).min().date()} to {pd.to_datetime(df['month']).max().date()}\n\n")
    meta.append("Cleaning decisions:\n")
    meta.append(f"- Dropped rows with missing usdret (monthly return): {dropped_ret}\n")
    meta.append("- Enforced one row per (permno, month)\n")
    meta_path.write_text("".join(meta), encoding="utf-8")

    build_data_dictionary(df, dictionary_path)
    return df


def main() -> None:
    df = merge_final_panel()
    print("✅ Merge step complete")
    print("Saved:", FINAL_DATA_DIR / "m1_panel.csv")
    print("Saved:", FINAL_DATA_DIR / "m1_metadata.txt")
    print("Saved:", FINAL_DATA_DIR / "m1_data_dictionary.csv")
    print("Rows:", len(df))


if __name__ == "__main__":
    main()
