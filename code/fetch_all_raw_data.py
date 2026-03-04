from __future__ import annotations

from fetch_fred_data import fetch_fred_data
from fetch_jodi_data import fetch_jodi_data
from fetch_wdi_data import fetch_wdi_data


def main() -> None:
    steps = [
        ("JODI", lambda: fetch_jodi_data()),
        ("FRED", lambda: fetch_fred_data()),
        ("WDI", lambda: fetch_wdi_data()),
    ]

    results: list[tuple[str, str]] = []

    for name, step in steps:
        try:
            step()
            results.append((name, "success"))
        except Exception as error:
            results.append((name, f"failed: {error}"))

    print("\n=== Raw Data Fetch Summary ===")
    for name, status in results:
        print(f"- {name}: {status}")

    has_failure = any("failed" in status for _, status in results)
    if has_failure:
        raise SystemExit(1)

    print("✅ All raw dataset fetchers completed successfully")


if __name__ == "__main__":
    main()
