from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import io
import json
import zipfile

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = PROJECT_ROOT / "data" / "raw"
CLEAN_DIR = RAW_DIR / "cleaned"
REPORT_PATH = CLEAN_DIR / "cleaning_summary.json"


@dataclass
class CleaningResult:
    source_name: str
    output_name: str
    rows_in: int
    rows_after_required: int
    rows_after_outliers: int
    dropped_missing_required: int
    dropped_outliers: int
    required_fields: list[str]
    outlier_columns: list[str]
    group_columns: list[str]


def dataset_rules(columns: list[str], dataset_name: str) -> tuple[list[str], list[str], list[str], list[str]]:
    lower_to_actual = {c.lower(): c for c in columns}

    required: list[str] = []
    outlier_cols: list[str] = []
    group_cols: list[str] = []
    exclude_outlier: list[str] = []

    if "fred_macro_raw" in dataset_name:
        required = [
            lower_to_actual.get("date", "date"),
            lower_to_actual.get("cpi_all_items", "cpi_all_items"),
            lower_to_actual.get("policy_rate", "policy_rate"),
            lower_to_actual.get("industrial_production", "industrial_production"),
        ]
        outlier_cols = [
            c for c in required if c.lower() in {"cpi_all_items", "policy_rate", "industrial_production"}
        ]
    elif "staging_world_newformat" in dataset_name:
        required = [
            lower_to_actual.get("ref_area", "REF_AREA"),
            lower_to_actual.get("time_period", "TIME_PERIOD"),
            lower_to_actual.get("energy_product", "ENERGY_PRODUCT"),
            lower_to_actual.get("flow_breakdown", "FLOW_BREAKDOWN"),
            lower_to_actual.get("unit_measure", "UNIT_MEASURE"),
            lower_to_actual.get("obs_value", "OBS_VALUE"),
        ]
        outlier_cols = [lower_to_actual.get("obs_value", "OBS_VALUE")]
        group_cols = [
            lower_to_actual.get("energy_product", "ENERGY_PRODUCT"),
            lower_to_actual.get("flow_breakdown", "FLOW_BREAKDOWN"),
            lower_to_actual.get("unit_measure", "UNIT_MEASURE"),
        ]
    elif "world_bank_wdi_raw" in dataset_name:
        required = [
            lower_to_actual.get("indicator_id", "indicator_id"),
            lower_to_actual.get("country_iso3", "country_iso3"),
            lower_to_actual.get("year", "year"),
            lower_to_actual.get("value", "value"),
        ]
        outlier_cols = [lower_to_actual.get("value", "value")]
        group_cols = [lower_to_actual.get("indicator_id", "indicator_id")]
    else:
        required_candidates = [
            "date",
            "year",
            "time_period",
            "country_iso3",
            "ref_area",
            "indicator_id",
            "obs_value",
            "value",
        ]
        required = [lower_to_actual[c] for c in required_candidates if c in lower_to_actual]
        numeric_default = [
            c
            for c in columns
            if c.lower() not in {"year", "decimal", "assessment_code", "obs_status"}
        ]
        outlier_cols = [c for c in numeric_default if c.lower() in {"value", "obs_value"}]
        if not outlier_cols:
            outlier_cols = numeric_default

    required = [c for c in required if c in columns]
    outlier_cols = [c for c in outlier_cols if c in columns and c not in exclude_outlier]
    group_cols = [c for c in group_cols if c in columns]
    return required, outlier_cols, group_cols, exclude_outlier


def iqr_keep_mask(series: pd.Series, multiplier: float = 3.0) -> pd.Series:
    clean = pd.to_numeric(series, errors="coerce")
    q1 = clean.quantile(0.25)
    q3 = clean.quantile(0.75)
    iqr = q3 - q1

    if pd.isna(iqr) or iqr == 0:
        return pd.Series([True] * len(series), index=series.index)

    lower = q1 - multiplier * iqr
    upper = q3 + multiplier * iqr
    return clean.isna() | ((clean >= lower) & (clean <= upper))


def apply_outlier_filter(df: pd.DataFrame, outlier_cols: list[str], group_cols: list[str]) -> pd.DataFrame:
    if not outlier_cols:
        return df

    keep_mask = pd.Series([True] * len(df), index=df.index)
    numeric_cols = [c for c in outlier_cols if c in df.columns]

    if not numeric_cols:
        return df

    if group_cols:
        grouped = df.groupby(group_cols, dropna=False, sort=False)
        for col in numeric_cols:
            col_keep = grouped[col].transform(lambda s: iqr_keep_mask(s, multiplier=3.0))
            keep_mask &= col_keep.fillna(True)
    else:
        for col in numeric_cols:
            keep_mask &= iqr_keep_mask(df[col], multiplier=3.0)

    return df.loc[keep_mask].copy()


def clean_dataframe(df: pd.DataFrame, source_name: str, output_name: str) -> tuple[pd.DataFrame, CleaningResult]:
    rows_in = len(df)
    required, outlier_cols, group_cols, _ = dataset_rules(list(df.columns), source_name.lower())

    required = [c for c in required if c in df.columns]
    df_required = df.dropna(subset=required) if required else df.copy()
    rows_after_required = len(df_required)

    df_out = apply_outlier_filter(df_required, outlier_cols=outlier_cols, group_cols=group_cols)
    rows_after_outliers = len(df_out)

    result = CleaningResult(
        source_name=source_name,
        output_name=output_name,
        rows_in=rows_in,
        rows_after_required=rows_after_required,
        rows_after_outliers=rows_after_outliers,
        dropped_missing_required=rows_in - rows_after_required,
        dropped_outliers=rows_after_required - rows_after_outliers,
        required_fields=required,
        outlier_columns=outlier_cols,
        group_columns=group_cols,
    )
    return df_out, result


def clean_csv_file(csv_path: Path) -> CleaningResult:
    df = pd.read_csv(csv_path)
    output_name = f"{csv_path.stem}_cleaned.csv"
    clean_df, result = clean_dataframe(df, source_name=csv_path.name, output_name=output_name)
    clean_df.to_csv(CLEAN_DIR / output_name, index=False)
    return result


def clean_csv_inside_zip(zip_path: Path, member_name: str) -> CleaningResult:
    with zipfile.ZipFile(zip_path) as zf:
        with zf.open(member_name) as fh:
            raw_bytes = fh.read()

    df = pd.read_csv(io.BytesIO(raw_bytes))
    member_stem = Path(member_name).stem
    output_name = f"{zip_path.stem}__{member_stem}_cleaned.csv"
    clean_df, result = clean_dataframe(
        df,
        source_name=f"{zip_path.name}:{member_name}",
        output_name=output_name,
    )
    clean_df.to_csv(CLEAN_DIR / output_name, index=False)
    return result


def main() -> None:
    CLEAN_DIR.mkdir(parents=True, exist_ok=True)
    results: list[CleaningResult] = []
    skipped_binary: list[str] = []

    for path in sorted(RAW_DIR.iterdir()):
        if path.is_dir():
            continue

        suffix = path.suffix.lower()

        if suffix == ".csv":
            results.append(clean_csv_file(path))
        elif suffix == ".zip":
            with zipfile.ZipFile(path) as zf:
                members = [n for n in zf.namelist() if n.lower().endswith(".csv")]
            for member in members:
                results.append(clean_csv_inside_zip(path, member))
        elif suffix == ".ivt":
            skipped_binary.append(path.name)

    payload = {
        "raw_dir": str(RAW_DIR),
        "clean_dir": str(CLEAN_DIR),
        "results": [r.__dict__ for r in results],
        "skipped_binary_files": skipped_binary,
    }
    REPORT_PATH.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    print(f"Cleaned datasets written to: {CLEAN_DIR}")
    print(f"Summary report: {REPORT_PATH}")
    for r in results:
        print(
            f"- {r.source_name} -> {r.output_name} | "
            f"rows {r.rows_in} -> {r.rows_after_outliers} "
            f"(missing: {r.dropped_missing_required}, outliers: {r.dropped_outliers})"
        )
    if skipped_binary:
        print("Skipped non-tabular binary files:")
        for name in skipped_binary:
            print(f"- {name}")


if __name__ == "__main__":
    main()
