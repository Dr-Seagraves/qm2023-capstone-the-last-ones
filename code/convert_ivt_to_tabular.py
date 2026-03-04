from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import io
import json
import re
import zipfile

import pandas as pd
import requests


PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = PROJECT_ROOT / "data" / "raw"
CONVERTED_DIR = RAW_DIR / "converted"
SUMMARY_PATH = CONVERTED_DIR / "ivt_conversion_summary.json"

OIL_DOWNLOADS_PAGE = "https://www.jodidata.org/oil/database/data-downloads.aspx"
OIL_BASE = "https://www.jodidata.org"
GAS_WORLD_NEWFORMAT_ZIP = "https://www.jodidata.org/_resources/files/downloads/gas-data/GAS_world_NewFormat.zip"


@dataclass
class ConversionResult:
    ivt_source: str
    output_csv: str
    rows_written: int
    note: str


def _get_oil_year_links(kind: str) -> list[str]:
    page = requests.get(OIL_DOWNLOADS_PAGE, timeout=60)
    page.raise_for_status()

    pattern = rf"/_resources/files/downloads/oil-data/annual-csv/{kind}/\d{{4}}\.csv"
    matches = sorted(set(re.findall(pattern, page.text)))
    return [f"{OIL_BASE}{path}" for path in matches]


def _download_csv_concat(urls: list[str], source_tag: str) -> pd.DataFrame:
    frames: list[pd.DataFrame] = []
    for url in urls:
        response = requests.get(url, timeout=120)
        response.raise_for_status()
        df = pd.read_csv(io.BytesIO(response.content))
        year = Path(url).stem
        df["SOURCE_FILE_YEAR"] = year
        df["SOURCE_GROUP"] = source_tag
        frames.append(df)

    if not frames:
        return pd.DataFrame()
    return pd.concat(frames, ignore_index=True)


def _load_gas_tabular() -> pd.DataFrame:
    local_csv = RAW_DIR / "STAGING_world_NewFormat.csv"
    if local_csv.exists():
        df = pd.read_csv(local_csv)
        df["SOURCE_GROUP"] = "gas_world_newformat_local"
        return df

    response = requests.get(GAS_WORLD_NEWFORMAT_ZIP, timeout=120)
    response.raise_for_status()

    with zipfile.ZipFile(io.BytesIO(response.content)) as archive:
        csv_members = [m for m in archive.namelist() if m.lower().endswith(".csv")]
        if not csv_members:
            raise RuntimeError("No CSV found inside GAS_world_NewFormat.zip")
        with archive.open(csv_members[0]) as fh:
            df = pd.read_csv(fh)
            df["SOURCE_GROUP"] = "gas_world_newformat_zip"
            return df


def convert_ivt_to_tabular() -> list[ConversionResult]:
    CONVERTED_DIR.mkdir(parents=True, exist_ok=True)
    results: list[ConversionResult] = []

    primary_links = _get_oil_year_links("primary")
    primary_df = _download_csv_concat(primary_links, source_tag="oil_primary_annual_csv")
    primary_output = "NewProcedure_World_Primary_tabular.csv"
    primary_df.to_csv(CONVERTED_DIR / primary_output, index=False)
    results.append(
        ConversionResult(
            ivt_source="NewProcedure_World_Primary.ivt",
            output_csv=primary_output,
            rows_written=len(primary_df),
            note="Built from official JODI oil annual-csv/primary files listed on oil data-download page.",
        )
    )

    secondary_links = _get_oil_year_links("secondary")
    secondary_df = _download_csv_concat(secondary_links, source_tag="oil_secondary_annual_csv")
    secondary_output = "NewProcedure_World_Secondary_tabular.csv"
    secondary_df.to_csv(CONVERTED_DIR / secondary_output, index=False)
    results.append(
        ConversionResult(
            ivt_source="NewProcedure_World_Secondary.ivt",
            output_csv=secondary_output,
            rows_written=len(secondary_df),
            note="Built from official JODI oil annual-csv/secondary files listed on oil data-download page.",
        )
    )

    gas_df = _load_gas_tabular()
    gas_output = "NewProcedure_JODI_Gas_merged_WDB20260218_tabular.csv"
    gas_df.to_csv(CONVERTED_DIR / gas_output, index=False)
    results.append(
        ConversionResult(
            ivt_source="NewProcedure_JODI_Gas_merged_WDB20260218.ivt",
            output_csv=gas_output,
            rows_written=len(gas_df),
            note="Built from JODI GAS world NewFormat tabular CSV (local extracted file or official gas zip).",
        )
    )

    payload = {
        "converted_dir": str(CONVERTED_DIR),
        "results": [r.__dict__ for r in results],
    }
    SUMMARY_PATH.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return results


def main() -> None:
    results = convert_ivt_to_tabular()
    print(f"Converted IVT tabular files written to: {CONVERTED_DIR}")
    print(f"Summary report: {SUMMARY_PATH}")
    for item in results:
        print(f"- {item.ivt_source} -> {item.output_csv} ({item.rows_written} rows)")


if __name__ == "__main__":
    main()
