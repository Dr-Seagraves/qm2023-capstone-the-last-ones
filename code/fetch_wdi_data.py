from __future__ import annotations

import csv
from datetime import UTC, datetime

import requests

from config_paths import RAW_DATA_DIR


WDI_BASE_URL = "https://api.worldbank.org/v2/country/all/indicator/{indicator}"

INDICATORS = {
    "EG.IMP.CONS.ZS": "energy_imports_net_percent_energy_use",
    "NY.GDP.MKTP.KD": "gdp_constant_2015_usd",
    "FP.CPI.TOTL.ZG": "inflation_consumer_prices_annual_percent",
    "NE.EXP.GNFS.ZS": "exports_goods_services_percent_gdp",
    "NE.IMP.GNFS.ZS": "imports_goods_services_percent_gdp",
}


def _fetch_indicator_rows(indicator_code: str) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    page = 1

    while True:
        url = WDI_BASE_URL.format(indicator=indicator_code)
        response = requests.get(
            url,
            params={"format": "json", "per_page": 20000, "page": page},
            timeout=120,
        )
        response.raise_for_status()
        payload = response.json()

        if not isinstance(payload, list) or len(payload) < 2:
            break

        meta, records = payload[0], payload[1]
        for record in records:
            rows.append(
                {
                    "indicator_id": indicator_code,
                    "indicator_label": INDICATORS[indicator_code],
                    "country_iso3": record.get("countryiso3code") or "",
                    "country_name": (record.get("country") or {}).get("value", ""),
                    "year": record.get("date") or "",
                    "value": "" if record.get("value") is None else str(record.get("value")),
                    "obs_status": record.get("obs_status") or "",
                    "decimal": "" if record.get("decimal") is None else str(record.get("decimal")),
                    "fetched_at_utc": datetime.now(UTC).isoformat(timespec="seconds"),
                }
            )

        if page >= int(meta.get("pages", 1)):
            break
        page += 1

    return rows


def fetch_wdi_data() -> list[dict[str, str]]:
    all_rows: list[dict[str, str]] = []

    for indicator in INDICATORS:
        indicator_rows = _fetch_indicator_rows(indicator)
        all_rows.extend(indicator_rows)
        print(f"Downloaded {indicator}: {len(indicator_rows)} rows")

    out_path = RAW_DATA_DIR / "world_bank_wdi_raw.csv"
    fieldnames = [
        "indicator_id",
        "indicator_label",
        "country_iso3",
        "country_name",
        "year",
        "value",
        "obs_status",
        "decimal",
        "fetched_at_utc",
    ]

    with open(out_path, "w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(all_rows)

    print("Saved:", out_path)
    print("Rows:", len(all_rows))
    return all_rows


def main() -> None:
    fetch_wdi_data()
    print("✅ WDI fetch complete")


if __name__ == "__main__":
    main()
