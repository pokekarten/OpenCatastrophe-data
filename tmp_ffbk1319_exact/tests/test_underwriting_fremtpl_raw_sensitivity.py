from __future__ import annotations

import pandas as pd

from scripts import underwriting_fremtpl_raw_sensitivity as probe


def tiny_data():
    freq = pd.DataFrame(
        {
            "IDpol": [1, 2, 3],
            "ClaimNb": [7, 1, 0],
            "Exposure": [1.5, 0.5, 1.0],
            "VehPower": [5, 6, 7],
            "VehAge": [1, 2, 3],
            "DrivAge": [30, 40, 50],
            "BonusMalus": [50, 60, 70],
            "VehBrand": ["'B1'", "'B2'", "'B3'"],
            "VehGas": ["'Diesel'", "'Regular'", "'Diesel'"],
            "Area": ["'A'", "'B'", "'C'"],
            "Density": [100, 200, 300],
            "Region": ["'R1'", "'R2'", "'R3'"],
        }
    )
    sev = pd.DataFrame(
        {"IDpol": [1, 1], "ClaimAmount": [150000.0, 100000.0]}
    )
    return freq, sev


def test_cleaning_receipt_quantifies_each_rule():
    freq, sev = tiny_data()
    r = probe.cleaning_receipt(freq, sev)
    assert r["frequency_idpol_unique"] is True
    assert r["frequency_idpol_duplicate_rows"] == 0
    assert r["claimnb_cap"]["cap"] == 4
    assert r["claimnb_cap"]["rows_changed"] == 1
    assert r["claimnb_cap"]["claims_removed"] == 3
    assert r["exposure_cap"]["rows_changed"] == 1
    assert r["exposure_cap"]["exposure_removed"] == 0.5
    assert r["claim_amount_cap_eur"]["policy_rows_changed"] == 1
    assert r["claim_amount_cap_eur"]["euros_removed"] == 50000
    assert r["zero_amount_claimnb_reset"]["rows_changed"] == 1
    assert r["zero_amount_claimnb_reset"]["claims_removed_after_claimnb_cap"] == 1


def test_uncapped_amount_sensitivity_changes_only_amount_related_targets():
    freq, sev = tiny_data()
    capped = probe.prepare_variant(
        freq, sev, claim_amount_cap=200000, claimnb_cap=4
    )
    uncapped = probe.prepare_variant(
        freq, sev, claim_amount_cap=None, claimnb_cap=4
    )
    assert capped.index.equals(uncapped.index)
    assert capped.loc[1, "ClaimAmount"] == 200000
    assert uncapped.loc[1, "ClaimAmount"] == 250000
    assert capped.loc[1, "ClaimNb"] == uncapped.loc[1, "ClaimNb"] == 4
    assert capped.loc[1, "Exposure"] == uncapped.loc[1, "Exposure"] == 1
    assert uncapped.loc[1, "PurePremium"] > capped.loc[1, "PurePremium"]


def test_raw_claimnb_sensitivity_isolates_product_decomposition():
    freq, sev = tiny_data()
    capped = probe.prepare_variant(
        freq, sev, claim_amount_cap=200000, claimnb_cap=4
    )
    raw = probe.prepare_variant(
        freq, sev, claim_amount_cap=200000, claimnb_cap=None
    )
    assert capped.index.equals(raw.index)
    assert capped.loc[1, "ClaimAmount"] == raw.loc[1, "ClaimAmount"] == 200000
    assert capped.loc[1, "Exposure"] == raw.loc[1, "Exposure"] == 1
    assert capped.loc[1, "PurePremium"] == raw.loc[1, "PurePremium"] == 200000
    assert capped.loc[1, "ClaimNb"] == 4
    assert raw.loc[1, "ClaimNb"] == 7
    assert capped.loc[1, "Frequency"] == 4
    assert raw.loc[1, "Frequency"] == 7
    assert raw.loc[1, "AvgClaimAmount"] < capped.loc[1, "AvgClaimAmount"]


def test_split_receipts_are_deterministic_and_seed_specific():
    d = pd.DataFrame(index=pd.Index(range(1, 101), name="IDpol"))
    a = probe.split_id_receipts(d, (0, 17))
    b = probe.split_id_receipts(d, (0, 17))
    assert a == b
    assert a[0]["test_id_sha256"] != a[1]["test_id_sha256"]
    assert a[0]["train_rows"] == 75
    assert a[0]["test_rows"] == 25


def _direct_metric(value: float) -> dict:
    return {
        "predicted_observed_total_ratio": value,
        "absolute_calibration_error": abs(value - 1.0),
        "ordered_gini": 0.2,
        "mean_tweedie_deviance": {"1.5": 5.0, "1.7": 4.0, "1.8": 3.0, "1.9": 2.0},
    }


def _variant_with_direct_metric(value: float) -> dict:
    selected = {
        "1.5": {"alpha": 0.1, "validation_deviance_same_power": {"0.1": 1.0}},
        "1.9": {"alpha": 0.1, "validation_deviance_same_power": {"0.1": 2.0}},
    }
    return {
        "splits": [
            {
                "seed": 0,
                "selected": {"tweedie_by_power": selected},
                "metrics": {
                    "direct_tweedie_p1.5": _direct_metric(value),
                    "direct_tweedie_p1.9": _direct_metric(value),
                },
            }
        ]
    }


def test_direct_tweedie_metric_invariance_receipt_passes_and_fails_closed():
    reference = _variant_with_direct_metric(1.01)
    same = _variant_with_direct_metric(1.01)
    receipt = probe.assert_direct_tweedie_metric_invariance(reference, same)
    assert receipt["status"] == "PASS"
    assert receipt["checked_seed_power_pairs"] == 2
    assert receipt["max_abs_retained_metric_delta"] == 0.0

    changed = _variant_with_direct_metric(1.02)
    try:
        probe.assert_direct_tweedie_metric_invariance(reference, changed)
    except AssertionError as exc:
        assert "changed retained direct Tweedie metrics" in str(exc)
    else:
        raise AssertionError("ClaimNb-only direct Tweedie drift must fail closed")
