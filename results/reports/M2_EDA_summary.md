# M2 EDA Summary

## Key Findings
- The macro heatmap shows policy rate and industrial production are negatively associated (r = -0.49), consistent with tighter policy slowing real activity.
- Industrial production exhibits a long-run rising trend with visible cyclical drawdowns, indicating both trend and business-cycle components in the outcome variable.
- Lag analysis suggests the strongest policy-rate relationship appears around lag 12 months (|r| = 0.55), supporting delayed transmission from policy to activity.
- Natural gas flow distributions vary substantially across flow categories (TOTIMPSB, INDPROD, TOTDEMC, IMPPIP are most frequent), indicating heteroskedasticity risk across flow types.
- Country-level demand-import sensitivity is heterogeneous (computed for 57 countries), supporting interaction terms in M3.

## Hypotheses for M3
1. **Driver Effect Hypothesis**: Higher policy rates reduce industrial production with a lagged effect.  
   - Model spec: outcome_t = alpha + beta * policy_rate_(t-12) + controls + e_t  
   - Expected sign: beta < 0  
   - Mechanism: borrowing-cost and demand channels transmit monetary tightening into lower real output.
2. **Control Premium Hypothesis**: Inflation pressure (CPI) is associated with production dynamics after controlling for policy stance.  
   - Model spec: add CPI as macro control in fixed-effects or time-series regression.  
   - Expected sign: ambiguous in short run; depends on demand pull vs. cost push regimes.
3. **Group Heterogeneity Hypothesis**: Natural-gas demand/import relationships differ systematically across countries and flow structures.  
   - Model spec: include country or flow interaction terms with key drivers.  
   - Expected sign: stronger import-demand coupling for structurally import-dependent countries.

## Data Quality Flags
- **Sparse merged panel structure**: macro variables exist for 432 rows while energy panel variables dominate row count (273,119 rows), requiring block-specific modeling choices.
- **Potential outliers**: flow-level boxplots show long tails; M3 should test winsorization or robust regression.
- **Missingness concentration**: many columns are block-specific and structurally missing in other blocks; avoid listwise deletion over full merged table.
- **Heteroskedasticity risk**: dispersion differs by flow category and country; use robust standard errors.
- **Multicollinearity check needed**: correlations among macro controls should be monitored (VIF diagnostics before final M3 specs).
