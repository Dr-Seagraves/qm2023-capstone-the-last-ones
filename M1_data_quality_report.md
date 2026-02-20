# Milestone 1 – Data Quality Report

## Data sources
- Primary dataset: `data/raw/reit_master.csv` (REIT monthly data).
- Key fields used: permno, ym, usdret, usdprc, market_equity, assets, sales, plus identifiers.

## Pipeline overview
The Milestone 1 pipeline is implemented in `code/m1_data_pipeline.py` and produces:
- `data/final/m1_panel.csv` (analysis-ready panel)
- `data/final/m1_metadata.txt` (metadata + cleaning notes)

## Time key construction
- The dataset’s `ym` values are formatted like `YYYYmM` (e.g., 2003m10).
- The pipeline converts `ym` into a monthly datetime `month = YYYY-MM-01`.

## Cleaning decisions
- Dropped rows where `month` could not be parsed from `ym`.
- Dropped rows with missing `usdret` (monthly return).
- Verified there are no duplicate (permno, month) rows.

## Final dataset summary
- Unit of observation: REIT-month (permno, month)
- Output file: `data/final/m1_panel.csv`

## Reproducibility
Run from repo root:
```bash
python3 code/m1_data_pipeline.py