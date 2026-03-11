# AI Audit Appendix (Milestone 1)

## How AI was used
GPT Codex in Github Copiolet was used to:
-Help import data and create seperate and merged fetch files for each dataset
-Convert binary datasets into tabular and readable csv files
-Clean each dataset and standardize date and format
-Create a consolodated data dictionary 
-Help understand the data and form hypotheses

## What I verified myself
- Checked the raw folder for the raw csv datasets appear as they were fetched
- Visually combed through the datasets pre and post cleaning decisions
-Renamed and created folders to keep organized through cleaning and finalizing process
-Compared the agent outputs to the M1 capstone document in Harvey
-Read what the agent was doing at each step to ensure it interpreted my prompts correctly
-provbided supplamentry links to help the agent pull data

## Files created/modified with AI assistance

---

## Session: March 11, 2026 — Data Cleanup & Pipeline Hardening

### What AI did
- Inspected `data/final/m1_panel.csv` to identify columns with no data across all rows
- Identified `obs_status` as fully empty (0 non-null values out of 323,359 rows)
- Dropped `obs_status` from `m1_panel.csv`, reducing the file from 20 to 19 columns, to prepare it for commit
- Added automatic empty-column dropping logic to `code/merge_final_panel.py` so this decision is applied every time the pipeline runs, and the dropped column names are logged to metadata
- Updated `data/final/m1_metadata.txt` to reflect the correct column count (19) and document the `obs_status` drop under "Cleaning decisions"

### What I verified myself
- Confirmed `obs_status` was truly empty before approving the drop
- Reviewed the pipeline code change to ensure it only drops fully-null columns and logs the decision
- Directed where the cleaning decision should be recorded (m1_metadata.txt)

### Files modified
- `data/final/m1_panel.csv` — removed empty column `obs_status`
- `data/final/m1_metadata.txt` — updated column count and added cleaning decision entry
- `code/merge_final_panel.py` — added `dropna(axis=1, how='all')` step with metadata logging

---

## Session: March 11, 2026 — Git Push Fix & Repository Cleanup

### What AI did
- Diagnosed a `pack-objects died of signal 15` git push failure caused by large files (up to 809MB) included in 4 unpushed commits
- Performed a `git reset --soft origin/main` to rewind the unpushed commits while preserving all file changes on disk
- Updated `.gitignore` to permanently exclude `data/raw/converted/`, `data/raw/cleaned/`, and `data/processed/cleaned/` from future commits
- Unstaged all large raw/converted CSV files from the index
- Force-added the `data/final/` output files (`m1_panel.csv`, `m1_metadata.txt`, `m1_data_dictionary.csv`) which were previously gitignored
- Created a clean single commit and successfully pushed to GitHub (`main -> main`)

### What I verified myself
- Approved the soft-reset plan before it was executed
- Confirmed the final commit contents looked correct before push
- Verified the push succeeded on GitHub

### Files modified
- `.gitignore` — added exclusions for `data/raw/converted/`, `data/raw/cleaned/`
- `data/final/m1_panel.csv`, `data/final/m1_metadata.txt`, `data/final/m1_data_dictionary.csv` — added to repo for first time
- `code/consolidate_datasets.py`, `code/merge_final_panel.py`, `code/run_full_pipeline.py` — added to repo for first time
