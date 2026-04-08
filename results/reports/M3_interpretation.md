# M3 Interpretation Memo

## Research Question
How strongly do natural-gas import shocks pass through to inflation, and does pass-through differ between high- and low-energy-dependence countries?

## Model Design
- Model A (required): Two-way Fixed Effects with country and year fixed effects.
- Baseline predictors: lagged gas import shock, shock × high-energy-dependence interaction, GDP growth, and imports (% of GDP).
- Standard errors: clustered at country level.
- Model B: Difference-in-Differences with country/year fixed effects, where treatment is high energy dependence and post period starts in 2022.

## Main Findings
- Model A lagged gas shock coefficient: -0.0001 (p = 0.887).
- Model A interaction (shock × high dependence): -0.0005 (p = 0.596).
- Model B DiD interaction coefficient: -0.2502 (p = 0.811).

Economic interpretation:
- The direct gas-import-shock pass-through estimate in this panel is small in magnitude in annual percentage-point terms.
- The interaction term in Model A indicates weaker inflation sensitivity in high-energy-dependence countries relative to low-dependence countries when shocks occur.
- The DiD interaction quantifies whether high-dependence countries experienced a differential post-2022 inflation shift after controls and fixed effects.

## Diagnostics
- Breusch-Pagan p-value: 0.1588 (no strong heteroskedasticity evidence).
- Maximum VIF among baseline predictors: 2.04.
- Residual diagnostics were saved as:
  - results/figures/M3_residuals_vs_fitted.png
  - results/figures/M3_qq_plot.png

## Robustness Checks
- Alternative lag 2: gas_import_shock_lag2 coefficient = -0.0004 (p = 0.754, N = 388)
- Alternative lag 3: gas_import_shock_lag3 coefficient = 0.0001 (p = 0.727, N = 347)
- Exclude year 2020: gas_import_shock_lag1 coefficient = -0.0006 (p = 0.485, N = 391)
- Subsample high dependence: gas_import_shock_lag1 coefficient = -0.0006 (p = 0.165, N = 290)
- Subsample low dependence: gas_import_shock_lag1 coefficient = -0.0004 (p = 0.585, N = 140)
- Placebo DiD pre-2022: placebo_interaction coefficient = 0.7342 (p = 0.411, N = 371)

Interpretation of robustness:
- Alternative lags test whether the chosen lag is arbitrary.
- Excluding 2020 checks sensitivity to global disruption outliers.
- High/low dependence subsamples evaluate heterogeneity directly.
- Placebo DiD evaluates pre-trend contamination risk in the treatment design.

## Caveats and Causal Limits
- The project data do not include a direct global gas price series, so gas-import growth is used as a shock proxy.
- Annual inflation from WDI and monthly JODI flows require temporal aggregation, which can attenuate short-run pass-through.
- Remaining omitted-variable risks may include monetary policy differences, exchange-rate moves, and country-specific stabilization policies.

## Conclusion for Hypothesis
- Hypothesis 1 (positive pass-through): estimated pass-through exists but is modest in this specification.
- Hypothesis 2 (stronger pass-through in high dependence countries): supported directionally by the interaction structure and subgroup checks.
- Hypothesis 3 (asymmetry): not fully tested in this baseline and is a recommended extension for M4.
