from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import hashlib
import json

import duckdb


PROJECT_ROOT = Path(__file__).resolve().parents[1]
CONVERTED_DIR = PROJECT_ROOT / "data" / "raw" / "converted"
CLEANED_DIR = PROJECT_ROOT / "data" / "raw" / "cleaned"
SUMMARY_PATH = CLEANED_DIR / "converted_ivt_cleaning_summary.json"


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


def _row_count(conn: duckdb.DuckDBPyConnection, sql: str) -> int:
    return int(conn.execute(f"SELECT COUNT(*) FROM ({sql})").fetchone()[0])


def clean_one_converted_csv(csv_path: Path) -> CleaningResult:
    conn = duckdb.connect(database=":memory:")
    read_expr = f"read_csv_auto('{csv_path.as_posix()}', all_varchar=true, ignore_errors=true)"

    required = [
        "REF_AREA",
        "TIME_PERIOD",
        "ENERGY_PRODUCT",
        "FLOW_BREAKDOWN",
        "UNIT_MEASURE",
        "OBS_VALUE",
    ]
    outlier_col = "OBS_VALUE"
    group_cols = ["ENERGY_PRODUCT", "FLOW_BREAKDOWN", "UNIT_MEASURE"]

    rows_in = _row_count(conn, f"SELECT * FROM {read_expr}")

    required_pred = " AND ".join([f"{c} IS NOT NULL" for c in required])
    required_sql = f"SELECT * FROM {read_expr} WHERE {required_pred}"
    rows_after_required = _row_count(conn, required_sql)

    filtered_sql = f"""
    WITH base AS (
        SELECT
            *,
            TRY_CAST(NULLIF(OBS_VALUE, '-') AS DOUBLE) AS obs_value_num
        FROM ({required_sql})
    ),
    bounds AS (
        SELECT
            {', '.join(group_cols)},
            quantile_cont(obs_value_num, 0.25) AS q1,
            quantile_cont(obs_value_num, 0.75) AS q3
        FROM base
        WHERE obs_value_num IS NOT NULL
        GROUP BY {', '.join(group_cols)}
    ),
    scored AS (
        SELECT
            b.*,
            bo.q1,
            bo.q3,
            (bo.q3 - bo.q1) AS iqr,
            (bo.q1 - 3.0 * (bo.q3 - bo.q1)) AS lower_bound,
            (bo.q3 + 3.0 * (bo.q3 - bo.q1)) AS upper_bound
        FROM base b
        LEFT JOIN bounds bo
        ON b.ENERGY_PRODUCT = bo.ENERGY_PRODUCT
        AND b.FLOW_BREAKDOWN = bo.FLOW_BREAKDOWN
        AND b.UNIT_MEASURE = bo.UNIT_MEASURE
    )
    SELECT * EXCLUDE(obs_value_num, q1, q3, iqr, lower_bound, upper_bound)
    FROM scored
    WHERE
        obs_value_num IS NULL
        OR iqr IS NULL
        OR iqr = 0
        OR (obs_value_num >= lower_bound AND obs_value_num <= upper_bound)
    """
    rows_after_outliers = _row_count(conn, filtered_sql)

    output_name = f"{csv_path.stem}_cleaned.csv"
    output_path = CLEANED_DIR / output_name
    conn.execute(
        f"COPY ({filtered_sql}) TO '{output_path.as_posix()}' (HEADER, DELIMITER ',')"
    )
    conn.close()

    return CleaningResult(
        source_name=csv_path.name,
        output_name=output_name,
        rows_in=rows_in,
        rows_after_required=rows_after_required,
        rows_after_outliers=rows_after_outliers,
        dropped_missing_required=rows_in - rows_after_required,
        dropped_outliers=rows_after_required - rows_after_outliers,
        required_fields=required,
        outlier_columns=[outlier_col],
        group_columns=group_cols,
    )


def dedupe_cleaned_csvs(cleaned_dir: Path) -> list[dict[str, str]]:
    by_hash: dict[str, list[Path]] = {}
    for csv_path in sorted(cleaned_dir.glob("*.csv")):
        h = hashlib.sha256()
        with csv_path.open("rb") as fh:
            for chunk in iter(lambda: fh.read(1024 * 1024), b""):
                h.update(chunk)
        by_hash.setdefault(h.hexdigest(), []).append(csv_path)

    removed: list[dict[str, str]] = []
    for same_files in by_hash.values():
        if len(same_files) <= 1:
            continue
        keep = same_files[0]
        for duplicate in same_files[1:]:
            duplicate.unlink(missing_ok=True)
            removed.append({"kept": keep.name, "removed": duplicate.name})

    return removed


def main() -> None:
    CLEANED_DIR.mkdir(parents=True, exist_ok=True)

    results: list[CleaningResult] = []
    for csv_path in sorted(CONVERTED_DIR.glob("*.csv")):
        results.append(clean_one_converted_csv(csv_path))

    dedupe_actions = dedupe_cleaned_csvs(CLEANED_DIR)

    payload = {
        "converted_dir": str(CONVERTED_DIR),
        "cleaned_dir": str(CLEANED_DIR),
        "results": [r.__dict__ for r in results],
        "dedupe_actions": dedupe_actions,
    }
    SUMMARY_PATH.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    print(f"Cleaned converted datasets written to: {CLEANED_DIR}")
    print(f"Summary report: {SUMMARY_PATH}")
    for r in results:
        print(
            f"- {r.source_name} -> {r.output_name} | "
            f"rows {r.rows_in} -> {r.rows_after_outliers} "
            f"(missing: {r.dropped_missing_required}, outliers: {r.dropped_outliers})"
        )
    if dedupe_actions:
        print("Removed duplicate CSV datasets:")
        for action in dedupe_actions:
            print(f"- removed {action['removed']} (kept {action['kept']})")
    else:
        print("No duplicate CSV datasets found.")


if __name__ == "__main__":
    main()
