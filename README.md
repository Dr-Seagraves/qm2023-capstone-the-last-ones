[![Review Assignment Due Date](https://classroom.github.com/assets/deadline-readme-button-22041afd0340ce965d47ae6ef1cefeee28c7c493a6346c4f15d667ab976d596c.svg)](https://classroom.github.com/a/gp9US0IQ)
[![Open in Visual Studio Code](https://classroom.github.com/assets/open-in-vscode-2e0aaae1b6195c2367325f4f02e2d04e9abb55f0b24a779b69b11b9e10269abc.svg)](https://classroom.github.com/online_ide?assignment_repo_id=22639722&assignment_repo_type=AssignmentRepo)
# QM 2023 Capstone Project

Semester-long capstone for Statistics II: Data Analytics.

## Project Structure

- **code/** — Python scripts and notebooks. Use `config_paths.py` for paths.
- **data/raw/** — Original data (read-only)
- **data/processed/** — Intermediate cleaning outputs
- **data/final/** — M1 output: analysis-ready panel
- **results/figures/** — Visualizations
- **results/tables/** — Regression tables, summary stats
- **results/reports/** — Milestone memos
- **tests/** — Autograding test suite

Run `python code/config_paths.py` to verify paths.

# QM 2023 Capstone Project: [The Last Ones]
## Team Members
- [Ashlynn Comstock] 
- [Jariah Eyachabbe] 
- [Samuel Abiel] 
- [Luna Wolfe] 
## Research Question
["How strongly do oil and gas price shocks pass through to consumer inflation, and does pass-through differ between high- and low-energy-dependence countries?"] 
## Data Sources & Coverage

### 1. JODI (IEA Oil & Gas Database)
- **Source:** International Energy Agency's Joint Oil Data Initiative
- **Variables:** Oil/gas production, consumption, trade flows, prices
- **Coverage:** 169+ countries | Monthly | 1990-2025
- **Format:** Energy data in tabular (STAGING world newformat) and binary (IVT) formats
- **Observations:** 273,119 rows after cleaning

### 2. FRED (Federal Reserve Economic Data)
- **Source:** Federal Reserve Bank of St. Louis
- **Variables:** Economic indicators (inflation, policy rates, industrial production)
- **Coverage:** USA | Monthly | 1954-2025
- **API:** Automatically fetched via FRED API
- **Observations:** 432 rows after cleaning

### 3. WDI (World Bank Development Indicators)
- **Source:** World Bank Open Data
- **Variables:** GDP, imports/exports, energy consumption, economic development metrics
- **Coverage:** 189 countries | Annual | 1960-2024
- **API:** Automatically fetched via World Bank API
- **Indicators:** EG.IMP.CONS.ZS, NY.GDP.MKTP.KD, FP.CPI.TOTL.ZG, NE.EXP.GNFS.ZS, NE.IMP.GNFS.ZS
- **Observations:** 49,808 rows after cleaning

### Final Consolidated Panel
- **Total Rows:** 323,359 (FRED + JODI + WDI concatenated)
- **Total Columns:** 20 standardized variables
- **Output:** `data/final/m1_panel.csv`
## Hypotheses (Preliminary)
1. [Positive oil and gas price shocks increase inflation in the current and subsequent months]
2. [Pass-through is stronger in high-energy-dependence countries than low-dependence countries.]
3. [passthrough is asymethric, where passthrough is larger after positive shocks than negative shocks]
## Repository Structure

## Data Pipeline

The data pipeline automates all steps from raw downloads to analysis-ready datasets:

```
RAW DATA                CONVERSION           CLEANING           CONSOLIDATION      FINALIZATION
(Download from          (Binary→CSV)         (QA Filters)       (Merge Sources)    (Analysis-Ready)
APIs & files)           
  ↓                        ↓                    ↓                  ↓                 ↓
JODI/FRED/WDI    →  IVT→Tabular       →  Outlier removal  →  m1_reit_base.csv →  m1_panel.csv
  (raw/)              (raw/converted/)    (raw/cleaned/)      (processed/)         (final/)
```

### Pipeline Stages

1. **FETCH** — Download from APIs and extract archives
   - FRED: ~434 macro observations
   - JODI: ~300K energy observations (multiple formats)
   - WDI: ~88K development observations

2. **CONVERT** — Transform binary IVT files to CSV
   - Parses JODI binary format
   - Extracts structured energy data

3. **CLEAN** — Apply data quality filters
   - Remove rows with missing required fields
   - Remove statistical outliers (IQR method, multiplier=3)
   - Result: 323,359 clean observations

4. **CONSOLIDATE** — Merge all three sources
   - Combine FRED + JODI + WDI
   - Standardize column names (lowercase)
   - Create `m1_reit_base.csv`

5. **STANDARDIZE** — Harmonize date formats
   - Convert all dates to YYYY-MM-DD format
   - Handle multiple input formats (YYYY-MM, YYYY-MM-DD, etc.)

6. **MERGE** — Create final analysis panel
   - Remove duplicates and all-NA rows
   - Generate metadata and data dictionary
   - Output: `m1_panel.csv` + documentation

## How to Run

### Quick Start (Recommended)
Run the complete data pipeline in one command:
```bash
python code/run_full_pipeline.py
```

This executes all 6 stages automatically and creates:
- `data/final/m1_panel.csv` — 323,359 rows × 20 columns (ready for analysis)
- `data/final/m1_metadata.txt` — Processing documentation
- `data/final/m1_data_dictionary.csv` — Column descriptions and metadata

### Run Individual Pipeline Steps
If you need to run or debug specific stages:
```bash
# Stage 1: Fetch raw data from APIs
python code/fetch_all_raw_data.py

# Stage 2: Convert IVT binary format to CSV
python code/convert_ivt_to_tabular.py

# Stage 3: Clean raw datasets (remove outliers, missing values)
python code/clean_raw_data.py

# Stage 4: Consolidate cleaned datasets
python code/consolidate_datasets.py

# Stage 5: Standardize date columns
python code/standardize_dates_to_final.py

# Stage 6: Create final analysis panel
python code/merge_final_panel.py
```

### Verify Installation
```bash
python code/config_paths.py
```
This confirms that the project structure is correct and all paths are accessible.
