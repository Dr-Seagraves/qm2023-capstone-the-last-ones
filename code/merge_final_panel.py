"""
Merge final panel after cleaning and consolidation.

Reads from data/processed/m1_reit_base.csv and creates final analysis-ready panel
in data/final/ with metadata and data dictionary.
"""

from __future__ import annotations

import pandas as pd
from config_paths import FINAL_DATA_DIR, PROCESSED_DATA_DIR, RAW_DATA_DIR


def build_data_dictionary(df: pd.DataFrame, out_path) -> None:
    """Build data dictionary from the final dataframe and source dictionary."""
    source_dictionary_path = RAW_DATA_DIR / "REIT_data_dictionary.csv"
    
    # Try to load source dictionary if it exists
    try:
        source_dictionary = pd.read_csv(source_dictionary_path)
    except FileNotFoundError:
        # Create a minimal data dictionary if source doesn't exist
        source_dictionary = pd.DataFrame()
    
    final_columns = list(df.columns)
    
    if not source_dictionary.empty:
        subset = source_dictionary[source_dictionary["variable"].isin(final_columns)].copy()
        
        missing_columns = [column for column in final_columns if column not in subset["variable"].tolist()]
        if missing_columns:
            fallback_rows = pd.DataFrame(
                {
                    "variable": missing_columns,
                    "dtype": [str(df[column].dtype) for column in missing_columns],
                    "description": ["Variable included in final panel" for _ in missing_columns],
                    "source": ["Derived" for _ in missing_columns],
                    "category": ["Derived" for _ in missing_columns],
                    "unit": ["" for _ in missing_columns],
                    "notes": ["" for _ in missing_columns],
                }
            )
            subset = pd.concat([subset, fallback_rows], ignore_index=True)
    else:
        # Create basic data dictionary from dataframe
        subset = pd.DataFrame(
            {
                "variable": final_columns,
                "dtype": [str(df[column].dtype) for column in final_columns],
                "description": ["Variable included in final panel" for _ in final_columns],
                "source": ["Consolidated Data" for _ in final_columns],
                "category": ["Data" for _ in final_columns],
                "unit": ["" for _ in final_columns],
                "notes": ["" for _ in final_columns],
            }
        )
    
    if not subset.empty and "variable" in subset.columns:
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
    """Merge final panel from processed data."""
    in_path = PROCESSED_DATA_DIR / "m1_reit_base.csv"
    out_csv = FINAL_DATA_DIR / "m1_panel.csv"
    meta_path = FINAL_DATA_DIR / "m1_metadata.txt"
    dictionary_path = FINAL_DATA_DIR / "m1_data_dictionary.csv"

    df = pd.read_csv(in_path)

    # Remove rows with all NaN values
    before = len(df)
    df = df.dropna(how='all').copy()
    dropped_all_na = before - len(df)

    # Drop columns that are entirely empty
    empty_cols = df.columns[df.isnull().all()].tolist()
    if empty_cols:
        df = df.drop(columns=empty_cols)

    # Sort and deduplicate
    df = df.sort_values(df.columns.tolist(), na_position='last').reset_index(drop=True)
    
    # Remove exact duplicates
    dupes = int(df.duplicated().sum())
    if dupes > 0:
        df = df.drop_duplicates().copy()

    df.to_csv(out_csv, index=False)

    # Create metadata
    meta = []
    meta.append("Milestone 1: Data Pipeline Metadata\n\n")
    meta.append(f"Input file: {in_path}\n")
    meta.append(f"Output file: {out_csv}\n")
    meta.append("Panel structure: Consolidated energy + macro + development indicators\n\n")
    meta.append(f"Rows: {len(df)}\n")
    meta.append(f"Columns: {len(df.columns)}\n\n")
    meta.append("Data Sources:\n")
    meta.append("- FRED: Federal Reserve macro indicators\n")
    meta.append("- JODI: IEA oil and gas production data\n")
    meta.append("- WDI: World Bank development indicators\n\n")
    meta.append("Cleaning decisions:\n")
    meta.append(f"- Dropped rows with all missing values: {dropped_all_na}\n")
    meta.append(f"- Removed duplicate rows: {dupes}\n")
    meta.append(f"- Dropped fully-empty columns ({len(empty_cols)}): {empty_cols if empty_cols else 'none'}\n")
    meta.append("- Standardized column names to lowercase\n")
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
