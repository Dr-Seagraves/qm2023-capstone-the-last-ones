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
- [Ashlynn Comstock] - [Role 1, e.g., Data Engineer]
- [Jariah Eyachabbe] - [Role 2, e.g., Analyst]
- [Samuel Abiel] - [Role 3, e.g., Visualizer]
- [Luna Wolfe] - [Role 4, e.g., Writer]
## Research Question
["How strongly do oil and gas price shocks pass through to consumer inflation, and does pass-through differ between high- and low-energy-dependence countries?"]
## Dataset Overview
- **Primary Dataset:** [Name, source, coverage]
- Entities: [N] | Time: [frequency] | Period: [date range]
- **Supplementary Data:** [List 3-5 key supplementary variables]
- FRED: FEDFUNDS, MORTGAGE30US, CPIAUCSL, UNRATE
- [Other]: [Description]
## Hypotheses (Preliminary)
1. [Hypothesis 1]
2. [Hypothesis 2]
3. [Hypothesis 3]
## Repository Structure
[Copy the folder structure tree from above]
## How to Run
1. Clone repository
2. Open in GitHub Codespaces
3. Run fetch scripts: `python code/fetch_[dataset1]_data.py`, `python
code/fetch_[dataset2]_data.py`
4. Run merge script: `python code/merge_final_panel.py`
5. Check output: `data/final/[dataset]_analysis_panel.csv`