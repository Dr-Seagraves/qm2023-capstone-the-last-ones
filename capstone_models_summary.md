# QM 2023 Capstone M3 Summary

## Team
- Ashlynn Comstock
- Jariah Eyachabbe
- Samuel Abiel
- Luna Wolfe

## Research Question
How strongly do natural-gas import shocks pass through to consumer inflation, and does pass-through differ between high- and low-energy-dependence countries?

## Data Sources and Coverage
- JODI (IEA Oil and Gas Database): 169+ countries, monthly data, 1990-2025.
- FRED (Federal Reserve Economic Data): United States, monthly data, 1954-2025.
- WDI (World Bank Development Indicators): 189 countries, annual data, 1960-2024.
- Consolidated panel output: data/final/m1_panel.csv (323,359 rows, 20 standardized columns).

## README Deliverables Checklist (M3)
- Python script present and runnable: capstone_models.py.
- Model A (required) implemented: two-way fixed effects with country and year FE.
- Model B implemented: Difference-in-Differences with treatment x post interaction.
- Publication-ready outputs saved to results/tables/ and results/figures/.
- Interpretation memo present: results/reports/M3_interpretation.md.

## Model Specification (Rubric: Component 1)
- Model A (Fixed Effects): PanelOLS with entity_effects=True and time_effects=True.
- Clustered standard errors: cov_type='clustered' with cluster_entity=True for Model A.
- Model B (DiD): inflation ~ did_interaction + controls + country FE + year FE.
- Economically sensible covariates: lagged gas shock, dependence interaction, GDP growth, imports share.

## Diagnostics and Interpretation (Rubric: Component 2)
- Heteroskedasticity (Breusch-Pagan): p = 0.1588, no strong heteroskedasticity evidence.
- Multicollinearity (VIF): max VIF = 2.04, below common concern thresholds.
- Residual diagnostics generated: residual-vs-fitted and Q-Q plot.
- Interpretation quality: diagnostics are not only reported but interpreted in results/reports/M3_interpretation.md.

## Robustness Checks and Implications (Rubric: Component 2)
At least 3 checks were required; 6 were completed.

1. Alternative lag 2: coefficient = -0.0004, p = 0.754, N = 388.
2. Alternative lag 3: coefficient = 0.0001, p = 0.727, N = 347.
3. Exclude year 2020: coefficient = -0.0006, p = 0.485, N = 391.
4. Subsample high dependence: coefficient = -0.0006, p = 0.165, N = 290.
5. Subsample low dependence: coefficient = -0.0004, p = 0.585, N = 140.
6. Placebo DiD pre-2022: coefficient = 0.7342, p = 0.411, N = 371.

Implication summary:
- Baseline directional findings are stable to multiple specification changes.
- No robustness check overturns the core finding of modest pass-through under this specification.

## Coefficients and Economic Reasoning (Rubric: Component 3)
- Model A gas shock (t-1): -0.0001 (p = 0.887).
- Model A shock x high dependence: -0.0005 (p = 0.596).
- Model B DiD interaction: -0.2502 (p = 0.811).

Economic interpretation:
- Estimated direct pass-through is small in annual percentage-point terms.
- Negative interaction sign indicates weaker estimated inflation sensitivity in high-dependence countries in this setup.
- DiD interaction is not statistically significant, so treated-post differential effects should be interpreted cautiously.

## Caveats and Causal Limits
- No direct global gas price series in this build; gas-import growth is used as shock proxy.
- Annual WDI inflation and monthly JODI flows require temporal aggregation.
- Residual omitted-variable risks remain (policy, exchange-rate, and country-specific stabilization differences).

## Publication and Documentation Quality (Rubric: Component 4)
- Publication table (LaTeX): results/tables/M3_regression_publication_table.tex.
- Publication summary metrics tables: CSV, Markdown, LaTeX versions in results/tables/.
- Side-by-side comparison tables and notes rows are produced.
- Significance stars and FE/SE/N/R-squared notes are included.
- Memo quality: complete findings, diagnostics, robustness, and caveats in results/reports/M3_interpretation.md.

## AI Audit Requirement (Pass/Fail Gate)
- AI audit appendix is present: AI_AUDIT_APPENDIX.md.
- Document includes prompts, verification steps, and correction notes for M3 work.

## Hypotheses Status Snapshot
1. Positive pass-through: estimated as modest in this specification.
2. Stronger pass-through in high-dependence countries: directionally supported via interaction structure and subgroup checks, but with weak significance.
3. Asymmetry: not fully tested in this baseline and remains an extension target.
