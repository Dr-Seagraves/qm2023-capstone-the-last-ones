"""
QM 2023 Capstone: Milestone 3 Econometric Models
Team: The Last Ones
Members: Ashlynn Comstock, Jariah Eyachabbe, Samuel Abiel, Luna Wolfe
Date: 2026-04-08

This script estimates panel regression models to identify the effect of
natural-gas import shocks on consumer inflation. We estimate:
- Model A: Two-way fixed effects panel regression (required)
- Model B: Difference-in-Differences with country and year fixed effects

Outputs are written to:
- results/tables/
- results/figures/
- results/reports/M3_interpretation.md
"""

from __future__ import annotations

import json
import importlib.util
from pathlib import Path
import textwrap
import sys
from typing import Dict, List, Tuple

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import pycountry
import seaborn as sns
import statsmodels.api as sm
import statsmodels.formula.api as smf
from linearmodels.panel import PanelOLS
from scipy import stats
from sklearn.metrics import mean_squared_error, r2_score
from statsmodels.stats.diagnostic import het_breuschpagan
from statsmodels.stats.outliers_influence import variance_inflation_factor

SCRIPT_DIR = Path(__file__).resolve().parent
CONFIG_PATH = SCRIPT_DIR / "code" / "config_paths.py"
spec = importlib.util.spec_from_file_location("capstone_config_paths", CONFIG_PATH)
config_paths = importlib.util.module_from_spec(spec)
assert spec is not None and spec.loader is not None
spec.loader.exec_module(config_paths)

FIGURES_DIR = config_paths.FIGURES_DIR
FINAL_DATA_DIR = config_paths.FINAL_DATA_DIR
REPORTS_DIR = config_paths.REPORTS_DIR
TABLES_DIR = config_paths.TABLES_DIR

sns.set_style("whitegrid")
plt.rcParams["font.size"] = 11


def significance_stars(p_value: float) -> str:
    if p_value < 0.01:
        return "***"
    if p_value < 0.05:
        return "**"
    if p_value < 0.10:
        return "*"
    return ""


def save_figure(fig: plt.Figure, filename: str) -> None:
    out = FIGURES_DIR / filename
    fig.tight_layout()
    fig.savefig(out, dpi=300, bbox_inches="tight")
    plt.close(fig)


def iso3_to_iso2(iso3: str) -> str | None:
    country = pycountry.countries.get(alpha_3=str(iso3))
    if country is not None:
        return country.alpha_2
    fallback = {
        "XKX": "XK",
    }
    return fallback.get(str(iso3))


def load_and_engineer_panel() -> pd.DataFrame:
    raw = pd.read_csv(FINAL_DATA_DIR / "m1_panel.csv", low_memory=False)

    # WDI long -> wide at country-year level.
    wdi = raw[raw["indicator_id"].notna()][["country_iso3", "year", "indicator_id", "value"]].copy()
    wdi["year"] = pd.to_numeric(wdi["year"], errors="coerce")
    wdi["value"] = pd.to_numeric(wdi["value"], errors="coerce")
    wdi = wdi.dropna(subset=["country_iso3", "year", "indicator_id", "value"])

    wdi_wide = (
        wdi.pivot_table(
            index=["country_iso3", "year"],
            columns="indicator_id",
            values="value",
            aggfunc="mean",
        )
        .reset_index()
        .rename(
            columns={
                "FP.CPI.TOTL.ZG": "inflation",
                "EG.IMP.CONS.ZS": "energy_import_share",
                "NE.IMP.GNFS.ZS": "imports_gdp",
                "NE.EXP.GNFS.ZS": "exports_gdp",
                "NY.GDP.MKTP.KD": "gdp_level",
            }
        )
    )
    wdi_wide["ref_area"] = wdi_wide["country_iso3"].map(iso3_to_iso2)

    # JODI monthly flows -> annual mean by country and flow type.
    jodi = raw[
        raw["ref_area"].notna() & raw["flow_breakdown"].isin(["TOTIMPSB", "TOTDEMC"])
    ][["ref_area", "time_period", "flow_breakdown", "obs_value"]].copy()
    jodi["obs_value"] = pd.to_numeric(jodi["obs_value"], errors="coerce")
    jodi["time"] = pd.to_datetime(jodi["time_period"], errors="coerce")
    jodi["year"] = jodi["time"].dt.year
    jodi = jodi.dropna(subset=["obs_value", "year", "ref_area"])

    jodi_wide = (
        jodi.groupby(["ref_area", "year", "flow_breakdown"], as_index=False)["obs_value"]
        .mean()
        .pivot_table(index=["ref_area", "year"], columns="flow_breakdown", values="obs_value", aggfunc="mean")
        .reset_index()
    )

    panel = wdi_wide.merge(jodi_wide, on=["ref_area", "year"], how="inner")
    panel = panel.sort_values(["country_iso3", "year"]).reset_index(drop=True)

    panel["gas_import_shock"] = panel.groupby("country_iso3")["TOTIMPSB"].pct_change() * 100
    panel["gas_demand_growth"] = panel.groupby("country_iso3")["TOTDEMC"].pct_change() * 100
    panel["gdp_growth"] = panel.groupby("country_iso3")["gdp_level"].pct_change() * 100
    panel["trade_openness"] = panel["imports_gdp"] + panel["exports_gdp"]

    for lag in [1, 2, 3]:
        panel[f"gas_import_shock_lag{lag}"] = panel.groupby("country_iso3")["gas_import_shock"].shift(lag)

    country_dep = panel.groupby("country_iso3")["energy_import_share"].median()
    dep_median = country_dep.median()
    high_dep_map = (country_dep >= dep_median).astype(int).to_dict()
    panel["high_energy_dependence"] = panel["country_iso3"].map(high_dep_map).astype(float)

    panel["post_2022"] = (panel["year"] >= 2022).astype(float)
    panel["did_interaction"] = panel["high_energy_dependence"] * panel["post_2022"]

    for lag in [1, 2, 3]:
        panel[f"shock_x_highdep_lag{lag}"] = (
            panel[f"gas_import_shock_lag{lag}"] * panel["high_energy_dependence"]
        )

    panel = panel.replace([np.inf, -np.inf], np.nan)
    return panel


def fe_sample(panel: pd.DataFrame, lag: int, subset: str = "all", exclude_year: int | None = None) -> pd.DataFrame:
    lag_col = f"gas_import_shock_lag{lag}"
    interaction_col = f"shock_x_highdep_lag{lag}"

    cols = [
        "country_iso3",
        "year",
        "inflation",
        lag_col,
        interaction_col,
        "gdp_growth",
        "imports_gdp",
        "energy_import_share",
        "high_energy_dependence",
    ]
    data = panel[cols].dropna().copy()

    if exclude_year is not None:
        data = data[data["year"] != exclude_year].copy()

    if subset == "high":
        data = data[data["high_energy_dependence"] == 1].copy()
    elif subset == "low":
        data = data[data["high_energy_dependence"] == 0].copy()

    return data


def fit_model_a_fe(panel: pd.DataFrame, lag: int = 1, subset: str = "all", exclude_year: int | None = None):
    data = fe_sample(panel, lag=lag, subset=subset, exclude_year=exclude_year)
    lag_col = f"gas_import_shock_lag{lag}"
    interaction_col = f"shock_x_highdep_lag{lag}"

    if subset == "all":
        predictors = [lag_col, interaction_col, "gdp_growth", "imports_gdp"]
    else:
        predictors = [lag_col, "gdp_growth", "imports_gdp"]

    data = data.set_index(["country_iso3", "year"])
    y = data["inflation"]
    X = data[predictors]

    model = PanelOLS(y, X, entity_effects=True, time_effects=True, drop_absorbed=True)
    results = model.fit(cov_type="clustered", cluster_entity=True)
    return results, data.reset_index(), predictors


def fit_model_b_did(panel: pd.DataFrame) -> Tuple[sm.regression.linear_model.RegressionResultsWrapper, pd.DataFrame]:
    cols = [
        "country_iso3",
        "year",
        "inflation",
        "did_interaction",
        "high_energy_dependence",
        "post_2022",
        "gas_import_shock_lag1",
        "gdp_growth",
        "imports_gdp",
    ]
    data = panel[cols].dropna().copy()

    formula = (
        "inflation ~ did_interaction + high_energy_dependence + post_2022 + "
        "gas_import_shock_lag1 + gdp_growth + imports_gdp + C(country_iso3) + C(year)"
    )
    did = smf.ols(formula, data=data).fit(cov_type="cluster", cov_kwds={"groups": data["country_iso3"]})
    return did, data


def run_diagnostics(model_a_results, model_a_data: pd.DataFrame, predictors: List[str]) -> Dict[str, float]:
    # Breusch-Pagan uses an OLS proxy with identical predictors.
    y = model_a_data["inflation"]
    X = model_a_data[predictors]
    X_const = sm.add_constant(X, has_constant="add")
    proxy_ols = sm.OLS(y, X_const).fit()
    bp_stat, bp_pvalue, f_stat, f_pvalue = het_breuschpagan(proxy_ols.resid, X_const)

    vif_df = pd.DataFrame({
        "variable": predictors,
        "vif": [variance_inflation_factor(X.values, i) for i in range(X.shape[1])],
    })
    vif_df.to_csv(TABLES_DIR / "M3_vif_table.csv", index=False)

    # Residual diagnostic plots from FE model.
    fitted = np.asarray(model_a_results.fitted_values).reshape(-1)
    resid = np.asarray(model_a_results.resids).reshape(-1)

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.scatter(fitted, resid, alpha=0.35)
    ax.axhline(0, color="red", linestyle="--", linewidth=1)
    ax.set_title("M3: Residuals vs Fitted (Model A FE)")
    ax.set_xlabel("Fitted Values")
    ax.set_ylabel("Residuals")
    save_figure(fig, "M3_residuals_vs_fitted.png")

    fig = plt.figure(figsize=(7, 5))
    stats.probplot(resid, dist="norm", plot=plt)
    plt.title("M3: Q-Q Plot (Model A FE Residuals)")
    save_figure(fig, "M3_qq_plot.png")

    return {
        "bp_stat": float(bp_stat),
        "bp_pvalue": float(bp_pvalue),
        "bp_f_stat": float(f_stat),
        "bp_f_pvalue": float(f_pvalue),
        "max_vif": float(vif_df["vif"].max()),
    }


def save_model_tables(model_a_results, did_results, diagnostics: Dict[str, float]) -> Dict[str, float]:
    model_a_tbl = pd.DataFrame(
        {
            "variable": model_a_results.params.index,
            "coef_model_a": model_a_results.params.values,
            "se_model_a": model_a_results.std_errors.values,
            "t_model_a": model_a_results.tstats.values,
            "p_model_a": model_a_results.pvalues.values,
        }
    )
    model_a_tbl["coef_model_a_fmt"] = model_a_tbl.apply(
        lambda r: f"{r['coef_model_a']:.4f}{significance_stars(r['p_model_a'])}", axis=1
    )

    did_rows = pd.DataFrame(
        {
            "variable": [
                "did_interaction",
                "high_energy_dependence",
                "post_2022",
                "gas_import_shock_lag1",
                "gdp_growth",
                "imports_gdp",
            ]
        }
    )
    did_rows["coef_model_b"] = did_rows["variable"].map(did_results.params)
    did_rows["se_model_b"] = did_rows["variable"].map(did_results.bse)
    did_rows["t_model_b"] = did_rows["variable"].map(did_results.tvalues)
    did_rows["p_model_b"] = did_rows["variable"].map(did_results.pvalues)
    did_rows["coef_model_b_fmt"] = did_rows.apply(
        lambda r: f"{r['coef_model_b']:.4f}{significance_stars(r['p_model_b'])}", axis=1
    )

    comparison = model_a_tbl.merge(did_rows, on="variable", how="outer")
    comparison = comparison.sort_values("variable").reset_index(drop=True)

    notes = pd.DataFrame(
        {
            "metric": [
                "Model A entity FE",
                "Model A time FE",
                "Model A clustered SE",
                "Model A observations",
                "Model A R2 within",
                "Model B country FE",
                "Model B year FE",
                "Model B clustered SE",
                "Model B observations",
                "Model B R2",
                "BP p-value",
                "Max VIF",
            ],
            "value": [
                "Yes",
                "Yes",
                "Yes (entity)",
                int(model_a_results.nobs),
                float(model_a_results.rsquared_within),
                "Yes",
                "Yes",
                "Yes (country)",
                int(did_results.nobs),
                float(did_results.rsquared),
                diagnostics["bp_pvalue"],
                diagnostics["max_vif"],
            ],
        }
    )

    comparison.to_csv(TABLES_DIR / "M3_regression_comparison_table.csv", index=False)
    notes.to_csv(TABLES_DIR / "M3_model_notes.csv", index=False)

    # Publication-style table: one model per column, with standard errors on separate rows.
    variable_labels = {
        "gas_import_shock_lag1": "Gas import shock (t-1)",
        "shock_x_highdep_lag1": "Shock x high energy dependence",
        "did_interaction": "High dependence x Post-2022",
        "high_energy_dependence": "High energy dependence",
        "post_2022": "Post-2022",
        "gdp_growth": "GDP growth",
        "imports_gdp": "Imports (% GDP)",
    }
    variable_order = [
        "gas_import_shock_lag1",
        "shock_x_highdep_lag1",
        "did_interaction",
        "high_energy_dependence",
        "post_2022",
        "gdp_growth",
        "imports_gdp",
    ]

    def coef_with_stars(coef: float | None, pval: float | None) -> str:
        if coef is None or pval is None or pd.isna(coef) or pd.isna(pval):
            return ""
        return f"{coef:.4f}{significance_stars(float(pval))}"

    def se_in_parentheses(se: float | None) -> str:
        if se is None or pd.isna(se):
            return ""
        return f"({float(se):.4f})"

    pub_rows: List[Dict[str, str | int | float]] = []
    for variable in variable_order:
        label = variable_labels[variable]

        a_coef = model_a_results.params.get(variable, np.nan)
        a_p = model_a_results.pvalues.get(variable, np.nan)
        a_se = model_a_results.std_errors.get(variable, np.nan)

        b_coef = did_results.params.get(variable, np.nan)
        b_p = did_results.pvalues.get(variable, np.nan)
        b_se = did_results.bse.get(variable, np.nan)

        pub_rows.append(
            {
                "Term": label,
                "Model (1) FE": coef_with_stars(a_coef, a_p),
                "Model (2) DiD": coef_with_stars(b_coef, b_p),
            }
        )
        pub_rows.append(
            {
                "Term": "",
                "Model (1) FE": se_in_parentheses(a_se),
                "Model (2) DiD": se_in_parentheses(b_se),
            }
        )

    pub_rows.extend(
        [
            {"Term": "Country fixed effects", "Model (1) FE": "Yes", "Model (2) DiD": "Yes"},
            {"Term": "Year fixed effects", "Model (1) FE": "Yes", "Model (2) DiD": "Yes"},
            {"Term": "Clustered standard errors", "Model (1) FE": "Country", "Model (2) DiD": "Country"},
            {"Term": "Observations", "Model (1) FE": int(model_a_results.nobs), "Model (2) DiD": int(did_results.nobs)},
            {
                "Term": "R-squared",
                "Model (1) FE": f"{float(model_a_results.rsquared_within):.4f}",
                "Model (2) DiD": f"{float(did_results.rsquared):.4f}",
            },
        ]
    )

    publication_table = pd.DataFrame(pub_rows)
    publication_table.to_csv(TABLES_DIR / "M3_regression_publication_table.csv", index=False)
    publication_table.to_latex(
        TABLES_DIR / "M3_regression_publication_table.tex",
        index=False,
        escape=False,
        column_format="p{7.0cm}cc",
        caption="Inflation Regressions: Fixed Effects and Difference-in-Differences",
        label="tab:m3_regressions",
    )

    # Hand-crafted LaTeX improves readability while preserving source estimates.
    regression_latex = textwrap.dedent(
        f"""
        \\begin{{table}}[!htbp]
        \\centering
        \\caption{{Inflation Regressions: Fixed Effects and Difference-in-Differences}}
        \\label{{tab:m3_regressions}}
        \\begin{{tabular}}{{p{{7.0cm}}cc}}
        \\toprule
        & Model (1) FE & Model (2) DiD \\\\
        \\midrule
        Gas import shock (t-1) & {coef_with_stars(model_a_results.params.get('gas_import_shock_lag1', np.nan), model_a_results.pvalues.get('gas_import_shock_lag1', np.nan))} & {coef_with_stars(did_results.params.get('gas_import_shock_lag1', np.nan), did_results.pvalues.get('gas_import_shock_lag1', np.nan))} \\\\
         & {se_in_parentheses(model_a_results.std_errors.get('gas_import_shock_lag1', np.nan))} & {se_in_parentheses(did_results.bse.get('gas_import_shock_lag1', np.nan))} \\\\
        Shock x high energy dependence & {coef_with_stars(model_a_results.params.get('shock_x_highdep_lag1', np.nan), model_a_results.pvalues.get('shock_x_highdep_lag1', np.nan))} &  \\\\
         & {se_in_parentheses(model_a_results.std_errors.get('shock_x_highdep_lag1', np.nan))} &  \\\\
        High dependence x Post-2022 &  & {coef_with_stars(did_results.params.get('did_interaction', np.nan), did_results.pvalues.get('did_interaction', np.nan))} \\\\
         &  & {se_in_parentheses(did_results.bse.get('did_interaction', np.nan))} \\\\
        High energy dependence &  & {coef_with_stars(did_results.params.get('high_energy_dependence', np.nan), did_results.pvalues.get('high_energy_dependence', np.nan))} \\\\
         &  & {se_in_parentheses(did_results.bse.get('high_energy_dependence', np.nan))} \\\\
        Post-2022 &  & {coef_with_stars(did_results.params.get('post_2022', np.nan), did_results.pvalues.get('post_2022', np.nan))} \\\\
         &  & {se_in_parentheses(did_results.bse.get('post_2022', np.nan))} \\\\
        GDP growth & {coef_with_stars(model_a_results.params.get('gdp_growth', np.nan), model_a_results.pvalues.get('gdp_growth', np.nan))} & {coef_with_stars(did_results.params.get('gdp_growth', np.nan), did_results.pvalues.get('gdp_growth', np.nan))} \\\\
         & {se_in_parentheses(model_a_results.std_errors.get('gdp_growth', np.nan))} & {se_in_parentheses(did_results.bse.get('gdp_growth', np.nan))} \\\\
        Imports (\\% GDP) & {coef_with_stars(model_a_results.params.get('imports_gdp', np.nan), model_a_results.pvalues.get('imports_gdp', np.nan))} & {coef_with_stars(did_results.params.get('imports_gdp', np.nan), did_results.pvalues.get('imports_gdp', np.nan))} \\\\
         & {se_in_parentheses(model_a_results.std_errors.get('imports_gdp', np.nan))} & {se_in_parentheses(did_results.bse.get('imports_gdp', np.nan))} \\\\
        \\midrule
        Country fixed effects & Yes & Yes \\\\
        Year fixed effects & Yes & Yes \\\\
        Clustered standard errors & Country & Country \\\\
        Observations & {int(model_a_results.nobs)} & {int(did_results.nobs)} \\\\
        R-squared & {float(model_a_results.rsquared_within):.4f} & {float(did_results.rsquared):.4f} \\\\
        \\bottomrule
        \\end{{tabular}}
        \\vspace{{0.3em}}

        \\begin{{minipage}}{{0.95\\linewidth}}
        \\footnotesize
        Notes: Standard errors (clustered by country) are in parentheses. Model (1) reports within-$R^2$ from two-way fixed effects. Model (2) reports overall $R^2$ from DiD with country and year fixed effects. Significance: * $p<0.10$, ** $p<0.05$, *** $p<0.01$.
        \\end{{minipage}}
        \\end{{table}}
        """
    ).strip() + "\n"
    (TABLES_DIR / "M3_regression_publication_table.tex").write_text(regression_latex, encoding="utf-8")

    return {
        "model_a_r2_within": float(model_a_results.rsquared_within),
        "model_a_n": float(model_a_results.nobs),
        "model_b_r2": float(did_results.rsquared),
        "model_b_n": float(did_results.nobs),
        "coef_a_shock": float(model_a_results.params.get("gas_import_shock_lag1", np.nan)),
        "p_a_shock": float(model_a_results.pvalues.get("gas_import_shock_lag1", np.nan)),
        "coef_a_interaction": float(model_a_results.params.get("shock_x_highdep_lag1", np.nan)),
        "p_a_interaction": float(model_a_results.pvalues.get("shock_x_highdep_lag1", np.nan)),
        "coef_b_did": float(did_results.params.get("did_interaction", np.nan)),
        "p_b_did": float(did_results.pvalues.get("did_interaction", np.nan)),
    }


def run_robustness(panel: pd.DataFrame) -> pd.DataFrame:
    rows: List[Dict[str, float | str]] = []

    # 1) Alternative lag structures.
    for lag in [2, 3]:
        res, _, _ = fit_model_a_fe(panel, lag=lag)
        rows.append(
            {
                "check": f"Alternative lag {lag}",
                "variable": f"gas_import_shock_lag{lag}",
                "coef": float(res.params.get(f"gas_import_shock_lag{lag}", np.nan)),
                "p_value": float(res.pvalues.get(f"gas_import_shock_lag{lag}", np.nan)),
                "nobs": float(res.nobs),
            }
        )

    # 2) Exclude 2020 global disruption year.
    ex2020, _, _ = fit_model_a_fe(panel, lag=1, exclude_year=2020)
    rows.append(
        {
            "check": "Exclude year 2020",
            "variable": "gas_import_shock_lag1",
            "coef": float(ex2020.params.get("gas_import_shock_lag1", np.nan)),
            "p_value": float(ex2020.pvalues.get("gas_import_shock_lag1", np.nan)),
            "nobs": float(ex2020.nobs),
        }
    )

    # 3) Subsample by energy dependence.
    for subgroup in ["high", "low"]:
        sub_res, _, _ = fit_model_a_fe(panel, lag=1, subset=subgroup)
        rows.append(
            {
                "check": f"Subsample {subgroup} dependence",
                "variable": "gas_import_shock_lag1",
                "coef": float(sub_res.params.get("gas_import_shock_lag1", np.nan)),
                "p_value": float(sub_res.pvalues.get("gas_import_shock_lag1", np.nan)),
                "nobs": float(sub_res.nobs),
            }
        )

    # 4) Placebo DiD in pre-treatment period only.
    did_data = panel[
        [
            "country_iso3",
            "year",
            "inflation",
            "high_energy_dependence",
            "gas_import_shock_lag1",
            "gdp_growth",
            "imports_gdp",
        ]
    ].dropna()
    pre = did_data[did_data["year"] < 2022].copy()
    pre["placebo_post_2018"] = (pre["year"] >= 2018).astype(float)
    pre["placebo_interaction"] = pre["high_energy_dependence"] * pre["placebo_post_2018"]

    placebo = smf.ols(
        "inflation ~ placebo_interaction + high_energy_dependence + placebo_post_2018 + "
        "gas_import_shock_lag1 + gdp_growth + imports_gdp + C(country_iso3) + C(year)",
        data=pre,
    ).fit(cov_type="cluster", cov_kwds={"groups": pre["country_iso3"]})

    rows.append(
        {
            "check": "Placebo DiD pre-2022",
            "variable": "placebo_interaction",
            "coef": float(placebo.params.get("placebo_interaction", np.nan)),
            "p_value": float(placebo.pvalues.get("placebo_interaction", np.nan)),
            "nobs": float(placebo.nobs),
        }
    )

    out = pd.DataFrame(rows)
    out.to_csv(TABLES_DIR / "M3_robustness_checks.csv", index=False)
    return out


def save_summary_publication_tables(summary: Dict[str, float], diagnostics: Dict[str, float]) -> None:
    summary_rows = [
        {
            "Section": "Model fit",
            "Metric": "Model (1) FE within R-squared",
            "Value": f"{summary['model_a_r2_within']:.4f}",
            "Interpretation": "Share of within-country inflation variation explained by FE model.",
        },
        {
            "Section": "Model fit",
            "Metric": "Model (1) FE observations",
            "Value": f"{int(summary['model_a_n'])}",
            "Interpretation": "Country-year observations used in Model (1).",
        },
        {
            "Section": "Model fit",
            "Metric": "Model (2) DiD R-squared",
            "Value": f"{summary['model_b_r2']:.4f}",
            "Interpretation": "Overall fit for DiD model with fixed effects.",
        },
        {
            "Section": "Model fit",
            "Metric": "Model (2) DiD observations",
            "Value": f"{int(summary['model_b_n'])}",
            "Interpretation": "Country-year observations used in Model (2).",
        },
        {
            "Section": "Core coefficients",
            "Metric": "Model (1) gas shock (t-1)",
            "Value": f"{summary['coef_a_shock']:.4f}",
            "Interpretation": "Marginal pass-through of lagged gas-import shock.",
        },
        {
            "Section": "Core coefficients",
            "Metric": "Model (1) gas shock p-value",
            "Value": f"{summary['p_a_shock']:.3f}",
            "Interpretation": "Statistical significance for Model (1) shock coefficient.",
        },
        {
            "Section": "Core coefficients",
            "Metric": "Model (1) shock x high dependence",
            "Value": f"{summary['coef_a_interaction']:.4f}",
            "Interpretation": "Incremental shock effect in high-dependence countries.",
        },
        {
            "Section": "Core coefficients",
            "Metric": "Model (1) interaction p-value",
            "Value": f"{summary['p_a_interaction']:.3f}",
            "Interpretation": "Statistical significance for interaction in Model (1).",
        },
        {
            "Section": "Core coefficients",
            "Metric": "Model (2) DiD interaction",
            "Value": f"{summary['coef_b_did']:.4f}",
            "Interpretation": "Differential post-2022 inflation shift for treated group.",
        },
        {
            "Section": "Core coefficients",
            "Metric": "Model (2) DiD p-value",
            "Value": f"{summary['p_b_did']:.3f}",
            "Interpretation": "Statistical significance for DiD interaction.",
        },
        {
            "Section": "Diagnostics",
            "Metric": "Breusch-Pagan p-value",
            "Value": f"{diagnostics['bp_pvalue']:.4f}",
            "Interpretation": "Higher values indicate weaker evidence of heteroskedasticity.",
        },
        {
            "Section": "Diagnostics",
            "Metric": "Maximum VIF",
            "Value": f"{diagnostics['max_vif']:.2f}",
            "Interpretation": "Largest multicollinearity indicator among baseline covariates.",
        },
    ]

    summary_df = pd.DataFrame(summary_rows)
    summary_df.to_csv(TABLES_DIR / "M3_summary_metrics_publication_table.csv", index=False)
    md_lines = [
        "| Section | Metric | Value | Interpretation |",
        "|---|---|---:|---|",
    ]
    for _, row in summary_df.iterrows():
        section = str(row["Section"]).replace("|", "\\|")
        metric = str(row["Metric"]).replace("|", "\\|")
        value = str(row["Value"]).replace("|", "\\|")
        interp = str(row["Interpretation"]).replace("|", "\\|")
        md_lines.append(f"| {section} | {metric} | {value} | {interp} |")
    (TABLES_DIR / "M3_summary_metrics_publication_table.md").write_text("\n".join(md_lines) + "\n", encoding="utf-8")
    summary_df.to_latex(
        TABLES_DIR / "M3_summary_metrics_publication_table.tex",
        index=False,
        escape=False,
        column_format="lp{5.6cm}lp{6.2cm}",
        caption="M3 Summary Metrics and Diagnostics",
        label="tab:m3_summary_metrics",
    )


def write_interpretation_memo(summary: Dict[str, float], diagnostics: Dict[str, float], robustness: pd.DataFrame) -> None:
    robust_lines = []
    for _, row in robustness.iterrows():
        robust_lines.append(
            f"- {row['check']}: {row['variable']} coefficient = {row['coef']:.4f} (p = {row['p_value']:.3f}, N = {int(row['nobs'])})"
        )

    bp_flag = "evidence of heteroskedasticity" if diagnostics["bp_pvalue"] < 0.05 else "no strong heteroskedasticity evidence"
    interaction_direction = "stronger" if summary["coef_a_interaction"] > 0 else "weaker"
    shock_direction = "positive" if summary["coef_a_shock"] > 0 else "negative"

    def hypothesis_assessment(coef: float, p_value: float, expected_positive: bool) -> str:
        direction_matches = (coef > 0) if expected_positive else (coef < 0)
        if p_value < 0.05 and direction_matches:
            return "supported"
        if p_value < 0.10 and direction_matches:
            return "weakly supported"
        if p_value < 0.05 and not direction_matches:
            return "not supported (estimate is statistically significant in the opposite direction)"
        return "not supported"

    h1_assessment = hypothesis_assessment(summary["coef_a_shock"], summary["p_a_shock"], expected_positive=True)
    h2_a_assessment = hypothesis_assessment(
        summary["coef_a_interaction"], summary["p_a_interaction"], expected_positive=True
    )
    h2_b_assessment = hypothesis_assessment(summary["coef_b_did"], summary["p_b_did"], expected_positive=True)

    memo = f"""# M3 Interpretation Memo

## Research Question
How strongly do natural-gas import shocks pass through to inflation, and does pass-through differ between high- and low-energy-dependence countries?

## Model Design
- Model A (required): Two-way Fixed Effects with country and year fixed effects.
- Baseline predictors: lagged gas import shock, shock × high-energy-dependence interaction, GDP growth, and imports (% of GDP).
- Standard errors: clustered at country level.
- Model B: Difference-in-Differences with country/year fixed effects, where treatment is high energy dependence and post period starts in 2022.

## Main Findings
- Model A lagged gas shock coefficient: {summary['coef_a_shock']:.4f} (p = {summary['p_a_shock']:.3f}).
- Model A interaction (shock × high dependence): {summary['coef_a_interaction']:.4f} (p = {summary['p_a_interaction']:.3f}).
- Model B DiD interaction coefficient: {summary['coef_b_did']:.4f} (p = {summary['p_b_did']:.3f}).

Economic interpretation:
- The direct gas-import-shock pass-through estimate in this panel is small in magnitude and {shock_direction} in annual percentage-point terms.
- The interaction term in Model A indicates {interaction_direction} inflation sensitivity in high-energy-dependence countries relative to low-dependence countries when shocks occur.
- The DiD interaction quantifies whether high-dependence countries experienced a differential post-2022 inflation shift after controls and fixed effects.

## Diagnostics
- Breusch-Pagan p-value: {diagnostics['bp_pvalue']:.4f} ({bp_flag}).
- Maximum VIF among baseline predictors: {diagnostics['max_vif']:.2f}.
- Residual diagnostics were saved as:
  - results/figures/M3_residuals_vs_fitted.png
  - results/figures/M3_qq_plot.png

## Robustness Checks
{chr(10).join(robust_lines)}

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
- Hypothesis 1 (positive pass-through): {h1_assessment} in this baseline specification.
- Hypothesis 2 (stronger pass-through in high dependence countries): {h2_a_assessment} by Model A interaction and {h2_b_assessment} by DiD interaction.
- Hypothesis 3 (asymmetry): not fully tested in this baseline and is a recommended extension for M4.
"""

    (REPORTS_DIR / "M3_interpretation.md").write_text(memo, encoding="utf-8")


def main() -> None:
    panel = load_and_engineer_panel()

    model_a, model_a_data, predictors = fit_model_a_fe(panel, lag=1)
    model_b, _ = fit_model_b_did(panel)

    diagnostics = run_diagnostics(model_a, model_a_data, predictors)
    summary = save_model_tables(model_a, model_b, diagnostics)
    robustness = run_robustness(panel)
    save_summary_publication_tables(summary, diagnostics)

    write_interpretation_memo(summary, diagnostics, robustness)

    with open(TABLES_DIR / "M3_summary_metrics.json", "w", encoding="utf-8") as f:
        json.dump({"summary": summary, "diagnostics": diagnostics}, f, indent=2)

    print("Milestone 3 outputs generated:")
    print(f"- {TABLES_DIR / 'M3_regression_comparison_table.csv'}")
    print(f"- {TABLES_DIR / 'M3_regression_publication_table.csv'}")
    print(f"- {TABLES_DIR / 'M3_regression_publication_table.tex'}")
    print(f"- {TABLES_DIR / 'M3_robustness_checks.csv'}")
    print(f"- {TABLES_DIR / 'M3_summary_metrics_publication_table.csv'}")
    print(f"- {TABLES_DIR / 'M3_summary_metrics_publication_table.md'}")
    print(f"- {TABLES_DIR / 'M3_summary_metrics_publication_table.tex'}")
    print(f"- {TABLES_DIR / 'M3_vif_table.csv'}")
    print(f"- {FIGURES_DIR / 'M3_residuals_vs_fitted.png'}")
    print(f"- {FIGURES_DIR / 'M3_qq_plot.png'}")
    print(f"- {REPORTS_DIR / 'M3_interpretation.md'}")


if __name__ == "__main__":
    main()
