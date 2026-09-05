from __future__ import annotations

import numpy as np
import pandas as pd

from scripts import underwriting_fremtpl_raw_tournament as probe


def test_po_ratio():
    y = np.array([10.0, 20.0])
    p = np.array([10.0, 30.0])
    w = np.array([1.0, 2.0])
    assert np.isclose(probe.po_ratio(y, p, w), 70.0 / 50.0)


def test_exposure_band_calibration_uses_fixed_heldout_bands():
    test = pd.DataFrame(
        {
            "Exposure": [0.10, 0.40, 0.60, 0.90],
            "PurePremium": [100.0, 50.0, 25.0, 10.0],
            "ClaimAmount": [10.0, 20.0, 15.0, 9.0],
        }
    )
    pred = np.array([100.0, 25.0, 50.0, 10.0])
    out = probe.exposure_band_calibration(test, pred)
    assert out["(0,0.25]"]["predicted_observed_total_ratio"] == 1.0
    assert out["(0.25,0.50]"]["predicted_observed_total_ratio"] == 0.5
    assert out["(0.50,0.75]"]["predicted_observed_total_ratio"] == 2.0
    assert out["(0.75,1.00]"]["predicted_observed_total_ratio"] == 1.0
    assert all(v["policy_rows"] == 1 for v in out.values())


def test_exposure_band_calibration_reports_null_when_band_has_no_observed_loss():
    test = pd.DataFrame(
        {
            "Exposure": [0.10, 0.40],
            "PurePremium": [0.0, 50.0],
            "ClaimAmount": [0.0, 20.0],
        }
    )
    out = probe.exposure_band_calibration(test, np.array([10.0, 50.0]))
    assert out["(0,0.25]"]["predicted_observed_total_ratio"] is None
    assert out["(0,0.25]"]["absolute_calibration_error"] is None


def test_gini_prefers_correct_order():
    y = np.array([0.0, 1.0, 10.0, 100.0])
    w = np.ones(4)
    good = probe.gini(y, np.array([0.0, 1.0, 10.0, 100.0]), w)
    bad = probe.gini(y, np.array([100.0, 10.0, 1.0, 0.0]), w)
    assert good > bad


def test_gini_all_equal_predictions_are_neutral_and_permutation_invariant():
    y = np.array([0.0, 100.0])
    pred = np.ones(2)
    w = np.ones(2)
    original = probe.gini(y, pred, w)
    swapped = probe.gini(y[::-1], pred[::-1], w[::-1])
    assert original == 0.0
    assert swapped == 0.0


def test_gini_tied_predictions_are_permutation_invariant_with_case_weights():
    y = np.array([0.0, 50.0, 100.0])
    pred = np.array([1.0, 1.0, 2.0])
    w = np.array([1.0, 2.0, 3.0])
    permutation = np.array([1, 0, 2])
    original = probe.gini(y, pred, w)
    reordered = probe.gini(y[permutation], pred[permutation], w[permutation])
    assert np.isclose(original, 0.25)
    assert np.isclose(reordered, original)


def test_gini_strict_order_keeps_previous_weighted_lorenz_semantics():
    y = np.array([0.0, 100.0])
    pred = np.array([1.0, 2.0])
    w = np.ones(2)
    assert probe.gini(y, pred, w) == 0.5


def test_reconciliation():
    freq = pd.DataFrame(
        {"IDpol": [1, 2, 3], "ClaimNb": [1, 0, 2], "Exposure": [1.0, 1.0, 1.0]}
    )
    sev = pd.DataFrame(
        {"IDpol": [1, 3, 4], "ClaimAmount": [100.0, 200.0, 300.0]}
    )
    d = probe.reconciliation(freq, sev)
    assert d["severity_rows_without_policy"] == 1
    assert d["policies_claimnb_vs_severity_count_mismatch"] == 1


def test_prepare_reconciliation_and_clips():
    freq = pd.DataFrame(
        {
            "IDpol": [1, 2],
            "ClaimNb": [7, 1],
            "Exposure": [1.5, 0.5],
            "VehPower": [5, 6],
            "VehAge": [1, 2],
            "DrivAge": [30, 40],
            "BonusMalus": [50, 60],
            "VehBrand": ["'B1'", "'B2'"],
            "VehGas": ["'Diesel'", "'Regular'"],
            "Area": ["'A'", "'B'"],
            "Density": [100, 200],
            "Region": ["'R1'", "'R2'"],
        }
    )
    sev = pd.DataFrame({"IDpol": [1], "ClaimAmount": [250000.0]})
    df = probe.prepare(freq, sev)
    assert df.loc[1, "ClaimNb"] == 4
    assert df.loc[1, "Exposure"] == 1
    assert df.loc[1, "ClaimAmount"] == 200000
    assert df.loc[2, "ClaimNb"] == 0
    assert df.loc[2, "ClaimAmount"] == 0
    assert df.loc[1, "VehBrand"] == "B1"


def test_consumer_aligned_product_tuning_is_fixed_power_and_train_validation_only():
    validation = pd.DataFrame(
        {
            "PurePremium": [0.0, 100.0, 400.0, 0.0, 200.0],
            "Exposure": [1.0, 1.0, 1.0, 1.0, 1.0],
        }
    )
    frequency_predictions = {
        1e-4: np.array([0.05, 0.20, 0.30, 0.05, 0.25]),
        1e-3: np.array([0.10, 0.40, 0.70, 0.10, 0.50]),
    }
    severity_predictions = {
        1.0: np.full(5, 800.0),
        10.0: np.full(5, 500.0),
    }

    out = probe.consumer_aligned_product_tuning(
        validation, frequency_predictions, severity_predictions
    )

    assert set(out) == {"1.5", "1.9"}
    assert (out["1.5"]["frequency_alpha"], out["1.5"]["severity_alpha"]) == (
        1e-4,
        1.0,
    )
    assert (out["1.9"]["frequency_alpha"], out["1.9"]["severity_alpha"]) == (
        1e-4,
        10.0,
    )
    for power, result in out.items():
        selected_key = probe._pair_key(
            result["frequency_alpha"], result["severity_alpha"]
        )
        assert result["validation_deviance_same_power"][selected_key] == min(
            result["validation_deviance_same_power"].values()
        )


def _metric(ratio, cal, gini, base_deviance):
    return {
        "predicted_observed_total_ratio": ratio,
        "absolute_calibration_error": cal,
        "ordered_gini": gini,
        "mean_tweedie_deviance": {
            "1.5": base_deviance + 3.0,
            "1.7": base_deviance + 2.0,
            "1.8": base_deviance + 1.0,
            "1.9": base_deviance,
        },
    }


def test_summarize_preserves_componentwise_reference_and_separates_joint_sensitivity():
    splits = []
    for seed in (0, 1):
        splits.append(
            {
                "seed": seed,
                "metrics": {
                    "product_poisson_gamma": _metric(1.01, 0.01, 0.20, 7.0),
                    "product_poisson_gamma_joint_p1.9": _metric(
                        1.005, 0.005, 0.205, 6.7
                    ),
                    "direct_tweedie_p1.9": _metric(1.02, 0.02, 0.21, 6.5),
                },
            }
        )

    summary = probe.summarize(splits)
    legacy = summary["direct_vs_product"]["direct_tweedie_p1.9"][0]
    joint = summary["joint_product_vs_componentwise"][
        "product_poisson_gamma_joint_p1.9"
    ][0]
    direct_joint = summary["direct_vs_joint_product_same_power"][
        "direct_tweedie_p1.9"
    ][0]

    # Keep the pre-existing field contract used by the cleaning-sensitivity wrapper.
    assert legacy["abs_calibration_error_difference_direct_minus_product"] == 0.01
    assert legacy["deviance_difference_direct_minus_product"]["1.9"] == -0.5
    assert np.isclose(
        joint["deviance_difference_joint_minus_componentwise"]["1.9"], -0.3
    )
    assert direct_joint["selection_power"] == 1.9
    assert np.isclose(
        direct_joint["deviance_difference_direct_minus_joint_product"]["1.9"], -0.2
    )


def test_summarize_signs():
    splits = []
    for seed, product_cal, direct_cal, product_g, direct_g in [
        (0, 0.01, 0.02, 0.20, 0.21),
        (1, 0.03, 0.01, 0.22, 0.23),
    ]:
        p_ratio = 1 + product_cal
        d_ratio = 1 + direct_cal
        splits.append(
            {
                "seed": seed,
                "metrics": {
                    "product_poisson_gamma": {
                        "predicted_observed_total_ratio": p_ratio,
                        "absolute_calibration_error": product_cal,
                        "ordered_gini": product_g,
                        "mean_tweedie_deviance": {
                            "1.5": 10.0,
                            "1.7": 9.0,
                            "1.8": 8.0,
                            "1.9": 7.0,
                        },
                    },
                    "direct_tweedie_p1.9": {
                        "predicted_observed_total_ratio": d_ratio,
                        "absolute_calibration_error": direct_cal,
                        "ordered_gini": direct_g,
                        "mean_tweedie_deviance": {
                            "1.5": 9.5,
                            "1.7": 8.5,
                            "1.8": 7.5,
                            "1.9": 6.5,
                        },
                    },
                },
            }
        )
    summary = probe.summarize(splits)
    rows = summary["direct_vs_product"]["direct_tweedie_p1.9"]
    assert rows[0]["deviance_difference_direct_minus_product"]["1.9"] == -0.5
    assert rows[0]["ordered_gini_difference_direct_minus_product"] > 0