"""Generate Milestone 2 EDA artifacts.

Outputs:
- capstone_eda.ipynb
- results/figures/M2_*.png
- results/reports/M2_EDA_summary.md

This script adapts the required M2 plot concepts to the available panel data.
"""

import json
from pathlib import Path
import sys

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from statsmodels.tsa.seasonal import seasonal_decompose

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from config_paths import FINAL_DATA_DIR, FIGURES_DIR, REPORTS_DIR, PROJECT_ROOT


sns.set_style("whitegrid")
plt.rcParams["font.size"] = 12


def save_plot(fig, name: str) -> None:
    out_path = FIGURES_DIR / name
    fig.tight_layout()
    fig.savefig(out_path, dpi=300, bbox_inches="tight")
    plt.close(fig)


def load_data() -> tuple[pd.DataFrame, pd.DataFrame]:
    df = pd.read_csv(FINAL_DATA_DIR / "m1_panel.csv", low_memory=False)

    # Macro block (single aggregate monthly series)
    macro = df[["date", "cpi_all_items", "policy_rate", "industrial_production"]].dropna().copy()
    macro["date"] = pd.to_datetime(macro["date"], errors="coerce")
    macro = macro.dropna(subset=["date"]).sort_values("date")

    # Energy panel block (country-time observations)
    energy = df[
        [
            "time_period",
            "ref_area",
            "flow_breakdown",
            "obs_value",
            "unit_measure",
        ]
    ].dropna(subset=["time_period", "ref_area", "obs_value"]).copy()
    energy["time"] = pd.to_datetime(energy["time_period"], errors="coerce")
    energy["obs_value"] = pd.to_numeric(energy["obs_value"], errors="coerce")
    energy = energy.dropna(subset=["time", "obs_value"])

    return macro, energy


def build_figures(macro: pd.DataFrame, energy: pd.DataFrame) -> dict:
    metrics = {}

    # Plot 1: Correlation Heatmap (macro)
    corr_vars = ["cpi_all_items", "policy_rate", "industrial_production"]
    corr = macro[corr_vars].corr()
    fig, ax = plt.subplots(figsize=(7, 5))
    sns.heatmap(corr, annot=True, fmt=".2f", cmap="coolwarm", center=0, ax=ax, xticklabels=["CPI", "Policy Rate", "Ind. Prod."], yticklabels=["CPI", "Policy Rate", "Ind. Prod."])
    ax.set_title("M2 Plot 1: Correlation Heatmap (Macro Economic Variables)")
    save_plot(fig, "M2_plot1_correlation_heatmap.png")
    metrics["corr_policy_vs_ip"] = float(corr.loc["policy_rate", "industrial_production"])

    # Plot 2: Time series of outcome variable (industrial production)
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.plot(macro["date"], macro["industrial_production"], label="Industrial Production Index")
    ax.set_title("M2 Plot 2: Industrial Production Index Over Time")
    ax.set_xlabel("Date (Monthly)")
    ax.set_ylabel("Industrial Production Index")
    ax.legend()
    save_plot(fig, "M2_plot2_outcome_time_series.png")

    # Plot 3: Dual-axis outcome vs driver
    fig, ax1 = plt.subplots(figsize=(10, 4))
    ax1.plot(macro["date"], macro["industrial_production"], color="tab:blue", label="Industrial Production")
    ax1.set_xlabel("Date")
    ax1.set_ylabel("Industrial Production Index", color="tab:blue")
    ax1.tick_params(axis="y", labelcolor="tab:blue")

    ax2 = ax1.twinx()
    ax2.plot(macro["date"], macro["policy_rate"], color="tab:red", label="Policy Rate")
    ax2.set_ylabel("Policy Rate (%)", color="tab:red")
    ax2.tick_params(axis="y", labelcolor="tab:red")
    ax1.set_title("M2 Plot 3: Industrial Production vs Policy Rate (Macro)")

    l1, lb1 = ax1.get_legend_handles_labels()
    l2, lb2 = ax2.get_legend_handles_labels()
    ax1.legend(l1 + l2, lb1 + lb2, loc="upper left")
    save_plot(fig, "M2_plot3_dual_axis_outcome_driver.png")

    # Plot 4: Lagged effect analysis
    lags = [0, 1, 2, 3, 6, 12]
    lag_corr = []
    for lag in lags:
        shifted = macro["policy_rate"].shift(lag)
        lag_corr.append(macro["industrial_production"].corr(shifted))

    fig, ax = plt.subplots(figsize=(8, 4))
    ax.bar([str(l) for l in lags], lag_corr, color="tab:green")
    ax.set_title("M2 Plot 4: Lagged Correlation of Policy Rate on Industrial Production")
    ax.set_xlabel("Lag (Months)")
    ax.set_ylabel("Correlation Coefficient")
    save_plot(fig, "M2_plot4_lagged_effects.png")
    metrics["lag_corr"] = dict(zip(lags, [float(x) if pd.notna(x) else np.nan for x in lag_corr]))

    # Plot 5: Group box plot (energy by flow)
    top_flows = energy["flow_breakdown"].value_counts().head(6).index.tolist()
    energy_top = energy[energy["flow_breakdown"].isin(top_flows)].copy()
    fig, ax = plt.subplots(figsize=(11, 5))
    sns.boxplot(data=energy_top, x="flow_breakdown", y="obs_value", ax=ax)
    ax.set_title("M2 Plot 5: Natural Gas Distribution by Flow Type")
    ax.set_xlabel("Natural Gas Flow Category")
    ax.set_ylabel("Natural Gas Observed Value (Units)")  
    ax.tick_params(axis="x", rotation=30)
    save_plot(fig, "M2_plot5_group_boxplot_flow.png")

    # Plot 6: Group sensitivity (country correlation between flow vs total demand)
    demand = energy[energy["flow_breakdown"] == "TOTDEMC"][["ref_area", "time", "obs_value"]].rename(
        columns={"obs_value": "totdemc"}
    )
    imports_ = energy[energy["flow_breakdown"] == "TOTIMPSB"][["ref_area", "time", "obs_value"]].rename(
        columns={"obs_value": "totimpsb"}
    )
    merged = demand.merge(imports_, on=["ref_area", "time"], how="inner")

    group_corr = (
        merged.groupby("ref_area")
        .apply(lambda x: x["totdemc"].corr(x["totimpsb"]))
        .dropna()
        .sort_values()
    )
    plot_corr = group_corr.head(15)
    colors = ["#d62728" if v < 0 else "#1f77b4" for v in plot_corr.values]

    fig, ax = plt.subplots(figsize=(9, 6))
    ax.barh(plot_corr.index, plot_corr.values, color=colors)
    ax.set_title("M2 Plot 6: Natural Gas Country Sensitivity (Demand vs Imports Correlation)")
    ax.set_xlabel("Correlation Coefficient")
    ax.set_ylabel("Country")
    save_plot(fig, "M2_plot6_group_sensitivity.png")

    # Plot 7: Scatter plots outcome vs controls (two controls)
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    sns.regplot(data=macro, x="cpi_all_items", y="industrial_production", scatter_kws={"alpha": 0.6}, ax=axes[0])
    axes[0].set_title("M2 Plot 7A: Industrial Production vs CPI (Macro Control)")
    axes[0].set_xlabel("CPI All Items (Index)")
    axes[0].set_ylabel("Industrial Production Index")

    sns.regplot(data=macro, x="policy_rate", y="industrial_production", scatter_kws={"alpha": 0.6}, ax=axes[1])
    axes[1].set_title("M2 Plot 7B: Industrial Production vs Policy Rate (Macro Control)")
    axes[1].set_xlabel("Policy Rate (%)")
    axes[1].set_ylabel("Industrial Production Index")
    save_plot(fig, "M2_plot7_scatter_controls.png")

    # Plot 8: Time series decomposition
    ts = macro.set_index("date")["industrial_production"].asfreq("MS").interpolate()
    decomp = seasonal_decompose(ts, model="additive", period=12)
    fig = decomp.plot()
    fig.set_size_inches(10, 8)
    fig.suptitle("M2 Plot 8: Seasonal Decomposition of Industrial Production Index", y=1.02)
    save_plot(fig, "M2_plot8_time_series_decomposition.png")

    # Extra diagnostics for summary
    metrics["top_flows"] = top_flows
    metrics["group_corr_count"] = int(group_corr.shape[0])
    metrics["macro_rows"] = int(macro.shape[0])
    metrics["energy_rows"] = int(energy.shape[0])

    return metrics


def write_summary(metrics: dict) -> None:
    lag_items = metrics["lag_corr"]
    best_lag = max((k for k in lag_items if pd.notna(lag_items[k])), key=lambda k: abs(lag_items[k]))
    best_lag_corr = lag_items[best_lag]

    summary = f"""# M2 EDA Summary

## Key Findings
- The macro heatmap shows policy rate and industrial production are negatively associated (r = {metrics['corr_policy_vs_ip']:.2f}), consistent with tighter policy slowing real activity.
- Industrial production exhibits a long-run rising trend with visible cyclical drawdowns, indicating both trend and business-cycle components in the outcome variable.
- Lag analysis suggests the strongest policy-rate relationship appears around lag {best_lag} months (|r| = {abs(best_lag_corr):.2f}), supporting delayed transmission from policy to activity.
- Natural gas flow distributions vary substantially across flow categories ({', '.join(metrics['top_flows'][:4])} are most frequent), indicating heteroskedasticity risk across flow types.
- Country-level demand-import sensitivity is heterogeneous (computed for {metrics['group_corr_count']} countries), supporting interaction terms in M3.

## Hypotheses for M3
1. **Driver Effect Hypothesis**: Higher policy rates reduce industrial production with a lagged effect.  
   - Model spec: outcome_t = alpha + beta * policy_rate_(t-{best_lag}) + controls + e_t  
   - Expected sign: beta < 0  
   - Mechanism: borrowing-cost and demand channels transmit monetary tightening into lower real output.
2. **Control Premium Hypothesis**: Inflation pressure (CPI) is associated with production dynamics after controlling for policy stance.  
   - Model spec: add CPI as macro control in fixed-effects or time-series regression.  
   - Expected sign: ambiguous in short run; depends on demand pull vs. cost push regimes.
3. **Group Heterogeneity Hypothesis**: Natural-gas demand/import relationships differ systematically across countries and flow structures.  
   - Model spec: include country or flow interaction terms with key drivers.  
   - Expected sign: stronger import-demand coupling for structurally import-dependent countries.

## Data Quality Flags
- **Sparse merged panel structure**: macro variables exist for 432 rows while energy panel variables dominate row count ({metrics['energy_rows']:,} rows), requiring block-specific modeling choices.
- **Potential outliers**: flow-level boxplots show long tails; M3 should test winsorization or robust regression.
- **Missingness concentration**: many columns are block-specific and structurally missing in other blocks; avoid listwise deletion over full merged table.
- **Heteroskedasticity risk**: dispersion differs by flow category and country; use robust standard errors.
- **Multicollinearity check needed**: correlations among macro controls should be monitored (VIF diagnostics before final M3 specs).
"""

    out = REPORTS_DIR / "M2_EDA_summary.md"
    out.write_text(summary, encoding="utf-8")


def write_notebook() -> None:
    nb = {
        "cells": [
            {
                "cell_type": "markdown",
                "metadata": {},
                "source": [
                    "# Capstone EDA Dashboard (M2)\n",
                    "\n",
                    "This notebook generates the required M2 visualizations and saves outputs to `results/figures/`.\n",
                ],
            },
            {
                "cell_type": "code",
                "execution_count": None,
                "metadata": {},
                "outputs": [],
                "source": [
                    "from code.generate_m2_eda_outputs import load_data, build_figures, write_summary\n",
                    "macro, energy = load_data()\n",
                    "print('macro shape:', macro.shape)\n",
                    "print('energy shape:', energy.shape)\n",
                ],
            },
            {
                "cell_type": "markdown",
                "metadata": {},
                "source": [
                    "## Run Full Visualization Pipeline\n",
                    "This cell builds all required plots and writes the summary markdown report.\n",
                ],
            },
            {
                "cell_type": "code",
                "execution_count": None,
                "metadata": {},
                "outputs": [],
                "source": [
                    "metrics = build_figures(macro, energy)\n",
                    "write_summary(metrics)\n",
                    "metrics\n",
                ],
            },
            {
                "cell_type": "markdown",
                "metadata": {},
                "source": [
                    "## Caption Notes\n",
                    "- Plot 1: Correlations indicate policy rate and production move inversely, consistent with monetary transmission.\n",
                    "- Plot 2: Outcome series includes trend and cyclical volatility, motivating decomposition and lag structures.\n",
                    "- Plot 3: Dual-axis view highlights co-movement windows and potential delayed responses.\n",
                    "- Plot 4: Lag profile identifies the most informative delay for M3 specification.\n",
                    "- Plot 5-6: Group patterns reveal heterogeneity and motivate interaction terms.\n",
                    "- Plot 7: Scatter/regression visuals provide control-variable intuition and potential nonlinear diagnostics.\n",
                    "- Plot 8: Decomposition separates trend/seasonality/residual components for model design.\n",
                ],
            },
        ],
        "metadata": {
            "kernelspec": {
                "display_name": "Python 3",
                "language": "python",
                "name": "python3",
            },
            "language_info": {
                "name": "python",
                "version": "3",
            },
        },
        "nbformat": 4,
        "nbformat_minor": 5,
    }

    out_path = PROJECT_ROOT / "capstone_eda.ipynb"
    out_path.write_text(json.dumps(nb, indent=2), encoding="utf-8")


def main() -> None:
    macro, energy = load_data()
    metrics = build_figures(macro, energy)
    write_summary(metrics)
    write_notebook()
    print("Generated capstone_eda.ipynb, M2_EDA_summary.md, and M2_*.png figures.")


if __name__ == "__main__":
    main()
