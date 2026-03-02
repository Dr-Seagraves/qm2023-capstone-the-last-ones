from __future__ import annotations

import csv
import os
from datetime import datetime
from io import StringIO

import requests

from config_paths import RAW_DATA_DIR


SERIES = {
    "CPIAUCSL": "cpi_all_items",
    "FEDFUNDS": "policy_rate",
    "INDPRO": "industrial_production",
}


def _fetch_with_pandas_datareader(start_date: str, end_date: str):
    from pandas_datareader import data as web

    symbols = list(SERIES.keys())
    df = web.DataReader(symbols, "fred", start=start_date, end=end_date).reset_index()
    return df.rename(columns={"DATE": "date", **SERIES})


def _fetch_with_fred_api(start_date: str, end_date: str, api_key: str) -> list[dict[str, str]]:
    by_date: dict[str, dict[str, str]] = {}

    for symbol, label in SERIES.items():
        response = requests.get(
            "https://api.stlouisfed.org/fred/series/observations",
            params={
                "series_id": symbol,
                "api_key": api_key,
                "file_type": "json",
                "observation_start": start_date,
                "observation_end": end_date,
            },
            timeout=60,
        )
        response.raise_for_status()
        payload = response.json()

        for obs in payload.get("observations", []):
            date_str = obs.get("date", "")
            value = obs.get("value", "")

            if date_str not in by_date:
                by_date[date_str] = {"date": date_str}
            by_date[date_str][label] = value

    return [by_date[key] for key in sorted(by_date)]


def _fetch_with_fred_csv_endpoint(start_date: str, end_date: str) -> list[dict[str, str]]:
    start_dt = datetime.fromisoformat(start_date)
    end_dt = datetime.fromisoformat(end_date)
    by_date: dict[str, dict[str, str]] = {}

    for symbol, label in SERIES.items():
        url = f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={symbol}"
        response = requests.get(url, timeout=60)
        response.raise_for_status()

        reader = csv.DictReader(StringIO(response.text))
        for row in reader:
            date_str = row.get("DATE") or row.get("observation_date") or ""
            value = row.get(symbol, "")
            try:
                date_dt = datetime.fromisoformat(date_str)
            except ValueError:
                continue

            if date_dt < start_dt or date_dt > end_dt:
                continue

            if date_str not in by_date:
                by_date[date_str] = {"date": date_str}
            by_date[date_str][label] = value

    rows = [by_date[key] for key in sorted(by_date)]
    return rows


def fetch_fred_data(
    start_date: str = "1990-01-01",
    end_date: str = "2026-12-31",
    api_key: str | None = None,
) -> list[dict[str, str]]:
    api_key = api_key or os.getenv("FRED_API_KEY")

    out_path = RAW_DATA_DIR / "fred_macro_raw.csv"

    if api_key:
        rows = _fetch_with_fred_api(start_date=start_date, end_date=end_date, api_key=api_key)
        source_method = "fred_api_key"
    else:
        try:
            df = _fetch_with_pandas_datareader(start_date=start_date, end_date=end_date)
            source_method = "pandas_datareader"
            df.to_csv(out_path, index=False)
            rows = df.to_dict(orient="records")
        except Exception:
            rows = _fetch_with_fred_csv_endpoint(start_date=start_date, end_date=end_date)
            source_method = "fred_csv_endpoint"

    if source_method != "pandas_datareader":
        fieldnames = ["date", *SERIES.values()]
        with open(out_path, "w", newline="", encoding="utf-8") as file:
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)

    row_count = len(rows)

    print("Saved:", out_path)
    print("Source method:", source_method)
    print("Rows:", row_count)
    return rows


def main() -> None:
    fetch_fred_data()
    print("✅ FRED fetch complete")


if __name__ == "__main__":
    main()
