import pathlib
import sys

import pandas as pd


PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import capstone_models as m3


def test_panel_build_has_required_columns():
    panel = m3.load_and_engineer_panel()

    required = {
        "country_iso3",
        "year",
        "inflation",
        "gas_import_shock_lag1",
        "shock_x_highdep_lag1",
        "gdp_growth",
        "imports_gdp",
        "high_energy_dependence",
        "did_interaction",
    }

    assert isinstance(panel, pd.DataFrame)
    assert panel.shape[0] > 0
    assert required.issubset(set(panel.columns))


def test_models_fit_and_return_key_coefficients():
    panel = m3.load_and_engineer_panel()

    model_a, _, _ = m3.fit_model_a_fe(panel, lag=1)
    model_b, _ = m3.fit_model_b_did(panel)

    assert "gas_import_shock_lag1" in model_a.params.index
    assert "shock_x_highdep_lag1" in model_a.params.index
    assert "did_interaction" in model_b.params.index
