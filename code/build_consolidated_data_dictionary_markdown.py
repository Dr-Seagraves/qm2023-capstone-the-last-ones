from __future__ import annotations

from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
FINAL_DIR = PROJECT_ROOT / "data" / "final"
INPUT_CSV = FINAL_DIR / "consolidated_data_dictionary.csv"
OUTPUT_MD = FINAL_DIR / "consolidated_data_dictionary.md"


def clean_text(value: object) -> str:
    if pd.isna(value):
        return ""
    text = str(value).strip()
    return text.replace("|", "\\|")


def main() -> None:
    if not INPUT_CSV.exists():
        raise FileNotFoundError(f"Missing input dictionary: {INPUT_CSV}")

    df = pd.read_csv(INPUT_CSV)
    df = df.sort_values(["dataset", "variable"]).reset_index(drop=True)

    lines: list[str] = []
    lines.append("# Consolidated Data Dictionary")
    lines.append("")
    lines.append("This is a concise, human-readable dictionary for datasets in `data/final`.")
    lines.append("Detailed profiling fields remain in `consolidated_data_dictionary.csv`.")
    lines.append("")

    for dataset in df["dataset"].dropna().unique():
        sub = df[df["dataset"] == dataset].copy()
        source = clean_text(sub["source"].dropna().iloc[0]) if not sub.empty else ""
        row_count = int(sub["rows_total"].dropna().iloc[0]) if "rows_total" in sub and not sub["rows_total"].dropna().empty else None

        lines.append(f"## {dataset}")
        lines.append("")
        meta = f"- Source: {source}" if source else "- Source:"
        lines.append(meta)
        if row_count is not None:
            lines.append(f"- Rows: {row_count:,}")
        lines.append("")
        lines.append("| Variable | Type | Description | Category | Unit |")
        lines.append("|---|---|---|---|---|")

        for _, row in sub.iterrows():
            variable = clean_text(row.get("variable", ""))
            dtype = clean_text(row.get("dtype", ""))
            description = clean_text(row.get("description", ""))
            category = clean_text(row.get("category", ""))
            unit = clean_text(row.get("unit", ""))
            lines.append(f"| {variable} | {dtype} | {description} | {category} | {unit} |")

        lines.append("")

    OUTPUT_MD.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote markdown dictionary: {OUTPUT_MD}")


if __name__ == "__main__":
    main()
