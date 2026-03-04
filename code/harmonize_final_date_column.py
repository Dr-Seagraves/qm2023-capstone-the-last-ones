from __future__ import annotations

from pathlib import Path
import json

import duckdb


PROJECT_ROOT = Path(__file__).resolve().parents[1]
FINAL_DIR = PROJECT_ROOT / "data" / "final"
SUMMARY_PATH = FINAL_DIR / "date_column_harmonization_summary.json"


def quote_ident(name: str) -> str:
    return '"' + name.replace('"', '""') + '"'


def build_select(columns: list[str]) -> tuple[str, list[str], list[str]]:
    lower = {c.lower(): c for c in columns}

    source_col = None
    for candidate in ["date", "time_period", "year"]:
        if candidate in lower:
            source_col = lower[candidate]
            break

    renamed: list[str] = []
    preserved: list[str] = []

    select_parts: list[str] = []
    if source_col is not None:
        select_parts.append(f"{quote_ident(source_col)} AS date")
        if source_col != "date":
            renamed.append(f"{source_col}->date")

    for column in columns:
        c_lower = column.lower()
        if source_col is not None and column == source_col:
            continue
        if c_lower == "fetched_at_utc":
            select_parts.append(f"{quote_ident(column)} AS fetched_date")
            renamed.append("fetched_at_utc->fetched_date")
            continue
        select_parts.append(quote_ident(column))
        preserved.append(column)

    return ",\n    ".join(select_parts), renamed, preserved


def main() -> None:
    conn = duckdb.connect(database=":memory:")
    results: list[dict[str, object]] = []

    for csv_path in sorted(FINAL_DIR.glob("*_date_std.csv")):
        input_sql = f"read_csv_auto('{csv_path.as_posix()}', all_varchar=true, ignore_errors=true)"
        columns = [row[0] for row in conn.execute(f"DESCRIBE SELECT * FROM {input_sql}").fetchall()]

        select_list, renamed_ops, preserved_cols = build_select(columns)
        out_name = csv_path.name.replace("_date_std.csv", "_date_harmonized.csv")
        out_path = FINAL_DIR / out_name

        conn.execute(
            f"COPY (SELECT\n    {select_list}\nFROM {input_sql}) TO '{out_path.as_posix()}' (HEADER, DELIMITER ',')"
        )

        row_count = int(conn.execute(f"SELECT COUNT(*) FROM {input_sql}").fetchone()[0])
        results.append(
            {
                "source": csv_path.name,
                "output": out_name,
                "rows": row_count,
                "renamed": renamed_ops,
                "preserved_columns": preserved_cols,
            }
        )

    payload = {
        "final_dir": str(FINAL_DIR),
        "files_processed": len(results),
        "results": results,
    }
    SUMMARY_PATH.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    print(f"Harmonized files written to: {FINAL_DIR}")
    print(f"Summary report: {SUMMARY_PATH}")
    for item in results:
        print(f"- {item['source']} -> {item['output']} ({item['rows']} rows) | renamed: {item['renamed']}")


if __name__ == "__main__":
    main()
