from __future__ import annotations

from pathlib import Path
import csv
import json

import duckdb


PROJECT_ROOT = Path(__file__).resolve().parents[1]
INPUT_DIR = PROJECT_ROOT / "data" / "processed" / "cleaned"
FINAL_DIR = PROJECT_ROOT / "data" / "final"
SUMMARY_PATH = FINAL_DIR / "date_standardization_summary.json"


def quote_ident(name: str) -> str:
    return '"' + name.replace('"', '""') + '"'


def read_header(csv_path: Path) -> list[str]:
    with csv_path.open("r", encoding="utf-8", newline="") as fh:
        reader = csv.reader(fh)
        return next(reader)


def standardized_expr(column_name: str) -> str:
    q = quote_ident(column_name)
    lower = column_name.lower()

    if lower == "date":
        return (
            "COALESCE(" 
            f"strftime(try_strptime({q}, '%Y-%m-%d'), '%Y-%m-%d'),"
            f"strftime(try_strptime({q}, '%Y-%m'), '%Y-%m-01'),"
            f"strftime(try_strptime({q}, '%Y/%m/%d'), '%Y-%m-%d'),"
            f"strftime(try_strptime({q}, '%Y/%m'), '%Y-%m-01')"
            ") AS " + q
        )

    if lower == "time_period":
        return (
            "COALESCE(" 
            f"strftime(try_strptime({q}, '%Y-%m-%d'), '%Y-%m-%d'),"
            f"strftime(try_strptime({q}, '%Y-%m'), '%Y-%m-01'),"
            f"strftime(try_strptime({q}, '%Y/%m/%d'), '%Y-%m-%d'),"
            f"strftime(try_strptime({q}, '%Y/%m'), '%Y-%m-01')"
            ") AS " + q
        )

    if lower == "year":
        return (
            f"CASE WHEN regexp_full_match(trim(CAST({q} AS VARCHAR)), '^[0-9]{{4}}$') "
            f"THEN trim(CAST({q} AS VARCHAR)) || '-01-01' "
            f"ELSE {q} END AS {q}"
        )

    if lower == "fetched_at_utc":
        return (
            f"COALESCE(strftime(try_strptime({q}, '%Y-%m-%dT%H:%M:%S%z'), '%Y-%m-%d'), "
            f"strftime(try_cast({q} AS TIMESTAMP), '%Y-%m-%d'), {q}) AS {q}"
        )

    return q


def main() -> None:
    FINAL_DIR.mkdir(parents=True, exist_ok=True)
    conn = duckdb.connect(database=":memory:")

    results: list[dict[str, object]] = []
    input_files = sorted(INPUT_DIR.glob("*.csv"))

    for csv_path in input_files:
        columns = read_header(csv_path)
        select_list = ",\n    ".join(standardized_expr(c) for c in columns)

        input_sql = f"read_csv_auto('{csv_path.as_posix()}', all_varchar=true, ignore_errors=true)"
        output_name = f"{csv_path.stem}_date_std.csv"
        output_path = FINAL_DIR / output_name

        sql = f"SELECT\n    {select_list}\nFROM {input_sql}"
        conn.execute(
            f"COPY ({sql}) TO '{output_path.as_posix()}' (HEADER, DELIMITER ',')"
        )

        row_count = int(conn.execute(f"SELECT COUNT(*) FROM {input_sql}").fetchone()[0])

        standardized_columns = [
            c for c in columns if c.lower() in {"date", "time_period", "year", "fetched_at_utc"}
        ]
        results.append(
            {
                "source": csv_path.name,
                "output": output_name,
                "rows": row_count,
                "standardized_date_columns": standardized_columns,
            }
        )

    summary = {
        "input_dir": str(INPUT_DIR),
        "final_dir": str(FINAL_DIR),
        "file_count": len(results),
        "results": results,
    }
    SUMMARY_PATH.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    print(f"Date-standardized files written to: {FINAL_DIR}")
    print(f"Summary report: {SUMMARY_PATH}")
    for item in results:
        print(
            f"- {item['source']} -> {item['output']} ({item['rows']} rows); "
            f"columns: {item['standardized_date_columns']}"
        )


if __name__ == "__main__":
    main()
