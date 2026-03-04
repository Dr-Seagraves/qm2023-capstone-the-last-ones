from __future__ import annotations

from pathlib import Path
import csv

import duckdb
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
FINAL_DIR = PROJECT_ROOT / "data" / "final"
OUTPUT_PATH = FINAL_DIR / "consolidated_data_dictionary.csv"


FIELD_INFO: dict[str, dict[str, str]] = {
    "date": {
        "description": "Observation date (standardized to YYYY-MM-DD)",
        "category": "Date",
        "unit": "YYYY-MM-DD",
        "notes": "Harmonized common date key",
    },
    "fetched_date": {
        "description": "Date when source record was fetched",
        "category": "Metadata",
        "unit": "YYYY-MM-DD",
        "notes": "Derived from source fetch timestamp",
    },
    "ref_area": {
        "description": "Reference area / reporting economy code",
        "category": "Identifier",
        "unit": "ISO-like country code",
        "notes": "JODI reporting area",
    },
    "time_period": {
        "description": "Original source time period",
        "category": "Date",
        "unit": "Source date period",
        "notes": "Retained in some source versions",
    },
    "energy_product": {
        "description": "Energy commodity/product code",
        "category": "Energy",
        "unit": "Code",
        "notes": "JODI product taxonomy",
    },
    "flow_breakdown": {
        "description": "Supply/use flow classification code",
        "category": "Energy",
        "unit": "Code",
        "notes": "JODI flow breakdown",
    },
    "unit_measure": {
        "description": "Measurement unit code",
        "category": "Measurement",
        "unit": "Code",
        "notes": "Examples: M3, KBBL, KL, CONVBBL",
    },
    "obs_value": {
        "description": "Observed value for the series",
        "category": "Measurement",
        "unit": "Varies by unit_measure",
        "notes": "Numeric or placeholder '-' in raw-like sources",
    },
    "assessment_code": {
        "description": "Data assessment quality/status code",
        "category": "Metadata",
        "unit": "Code",
        "notes": "Source-defined quality marker",
    },
    "source_file_year": {
        "description": "Year of source annual CSV file",
        "category": "Metadata",
        "unit": "YYYY",
        "notes": "Added during IVT-tabular conversion",
    },
    "source_group": {
        "description": "Source extraction/conversion group tag",
        "category": "Metadata",
        "unit": "Text",
        "notes": "Added during conversion pipeline",
    },
    "cpi_all_items": {
        "description": "Consumer Price Index, all items",
        "category": "Macro",
        "unit": "Index",
        "notes": "FRED macro series",
    },
    "policy_rate": {
        "description": "Policy interest rate",
        "category": "Macro",
        "unit": "Percent",
        "notes": "FRED macro series",
    },
    "industrial_production": {
        "description": "Industrial production index",
        "category": "Macro",
        "unit": "Index",
        "notes": "FRED macro series",
    },
    "indicator_id": {
        "description": "World Bank indicator identifier",
        "category": "Identifier",
        "unit": "Code",
        "notes": "WDI indicator key",
    },
    "indicator_label": {
        "description": "World Bank indicator descriptive name",
        "category": "Metadata",
        "unit": "Text",
        "notes": "Snake_case label from fetch script",
    },
    "country_iso3": {
        "description": "Country/economy ISO3 code",
        "category": "Identifier",
        "unit": "ISO3",
        "notes": "WDI economy key",
    },
    "country_name": {
        "description": "Country/economy name",
        "category": "Identifier",
        "unit": "Text",
        "notes": "WDI economy name",
    },
    "value": {
        "description": "Observed indicator value",
        "category": "Measurement",
        "unit": "Indicator-specific",
        "notes": "WDI indicator value",
    },
    "obs_status": {
        "description": "Observation status flag",
        "category": "Metadata",
        "unit": "Code/text",
        "notes": "Source-defined status marker",
    },
    "decimal": {
        "description": "Suggested number of decimal places",
        "category": "Metadata",
        "unit": "Count",
        "notes": "WDI metadata field",
    },
}


def dataset_source(dataset_name: str) -> str:
    name = dataset_name.lower()
    if "world_bank" in name:
        return "World Bank WDI"
    if "fred" in name:
        return "FRED"
    return "JODI"


def infer_dtype(series: pd.Series) -> str:
    dtype = str(series.dtype)
    if dtype != "object":
        return dtype

    numeric = pd.to_numeric(series, errors="coerce")
    if numeric.notna().sum() == series.notna().sum() and series.notna().sum() > 0:
        return "numeric"
    return "string"


def main() -> None:
    csv_files = sorted(
        [
            p
            for p in FINAL_DIR.glob("*.csv")
            if p.name != "m1_data_dictionary.csv" and p.name != "consolidated_data_dictionary.csv"
        ]
    )

    records: list[dict[str, object]] = []
    conn = duckdb.connect(database=":memory:")

    for dataset_path in csv_files:
        dataset_name = dataset_path.name
        source_name = dataset_source(dataset_name)

        preview_df = pd.read_csv(dataset_path, nrows=25000)
        total_rows = int(
            conn.execute(
                f"SELECT COUNT(*) FROM read_csv_auto('{dataset_path.as_posix()}', all_varchar=true, ignore_errors=true)"
            ).fetchone()[0]
        )

        for column in preview_df.columns:
            col_series = preview_df[column]
            non_null = int(col_series.notna().sum())
            missing = int(col_series.isna().sum())
            preview_rows = len(preview_df)
            missing_pct_preview = (missing / preview_rows * 100.0) if preview_rows else 0.0

            non_null_values = col_series.dropna().astype(str)
            example_values = "; ".join(non_null_values.head(3).tolist()) if not non_null_values.empty else ""

            info = FIELD_INFO.get(
                column.lower(),
                {
                    "description": f"Field '{column}' from {dataset_name}",
                    "category": "Other",
                    "unit": "",
                    "notes": "Review for project-specific semantics",
                },
            )

            records.append(
                {
                    "dataset": dataset_name,
                    "variable": column,
                    "dtype": infer_dtype(col_series),
                    "description": info["description"],
                    "source": source_name,
                    "category": info["category"],
                    "unit": info["unit"],
                    "notes": info["notes"],
                    "rows_total": total_rows,
                    "rows_profiled": preview_rows,
                    "non_null_profiled": non_null,
                    "missing_profiled": missing,
                    "missing_pct_profiled": round(missing_pct_preview, 4),
                    "example_values": example_values,
                }
            )

    out_df = pd.DataFrame(records)
    out_df = out_df.sort_values(["dataset", "variable"]).reset_index(drop=True)
    out_df.to_csv(OUTPUT_PATH, index=False, quoting=csv.QUOTE_MINIMAL)

    print(f"Wrote consolidated dictionary: {OUTPUT_PATH}")
    print(f"Datasets covered: {len(csv_files)}")
    print(f"Variables documented: {len(out_df)}")


if __name__ == "__main__":
    main()
