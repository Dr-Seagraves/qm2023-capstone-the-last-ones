# AI Audit Appendix (Milestone 1)

## How AI was used
ChatGPT was used to:
- Interpret the Milestone 1 requirements into an actionable checklist.
- Draft the Python data pipeline script to load, clean, and export an analysis-ready panel dataset.
- Provide debugging help for environment issues (installing pandas, using python3).

Copiolet was used to form code and help understand the data to form hypotheses. 

## What I verified myself
- Confirmed the REIT dataset file was placed in `data/raw/` and renamed to `reit_master.csv`.
- Ran the pipeline end-to-end and confirmed outputs were created in `data/final/`.
- Checked that the panel has a monthly time key and no duplicate (permno, month) rows.

## Files created/modified with AI assistance
- `code/m1_data_pipeline.py`
- `M1_data_quality_report.md`
- `AI_AUDIT_APPENDIX.md`
- Output artifacts: `data/final/m1_panel.csv`, `data/final/m1_metadata.txt`