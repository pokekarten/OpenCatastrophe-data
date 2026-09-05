#!/usr/bin/env python3
"""Complete the freMTPL2 raw tournament with data-cleaning sensitivity receipts.

Research only. This wrapper deliberately reuses the fitted-model machinery in
``underwriting_fremtpl_raw_tournament`` and changes only declared data-preparation
sensitivities. Outer split IDs are held fixed across variants.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path

import numpy as np
import pandas as pd

try:
    from scripts import underwriting_fremtpl_raw_tournament as base
except ModuleNotFoundError:  # direct: python scripts/underwriting_fremtpl_raw_sensitivity.py
    import underwriting_fremtpl_raw_tournament as base

REFERENCE_CLAIM_AMOUNT_CAP = 200000.0
REFERENCE_CLAIMNB_CAP = 4.0


def joined_raw(freq: pd.DataFrame, sev: pd.DataFrame) -> pd.DataFrame:
    """Join policy rows to aggregated severity without target cleaning."""
    f = freq.copy()
    for c in f.columns:
        if f[c].dtype == object or isinstance(f[c].dtype, pd.CategoricalDtype):
            f[c] = f[c].astype(str).str.strip("'")
    amounts = sev.groupby("IDpol", sort=False)["ClaimAmount"].sum()
    d = f.set_index("IDpol")
    d["ClaimAmount"] = d.index.to_series().map(amounts).fillna(0.0).astype(float)
    return d


def prepare_variant(
    freq: pd.DataFrame,
    sev: pd.DataFrame,
    *,
    claim_amount_cap: float | None,
    claimnb_cap: float | None = REFERENCE_CLAIMNB_CAP,
) -> pd.DataFrame:
    """Apply reference cleaning while isolating one declared cap sensitivity."""
    d = joined_raw(freq, sev)
    d["ClaimNb"] = d["ClaimNb"].astype(float)
    if claimnb_cap is not None:
        d["ClaimNb"] = d["ClaimNb"].clip(upper=float(claimnb_cap))
    d["Exposure"] = d["Exposure"].astype(float).clip(upper=1)
    if claim_amount_cap is not None:
        d["ClaimAmount"] = d["ClaimAmount"].clip(upper=float(claim_amount_cap))
    d.loc[(d["ClaimAmount"] == 0) & (d["ClaimNb"] >= 1), "ClaimNb"] = 0
    if not (d["Exposure"] > 0).all():
        raise ValueError("Exposure must stay positive")
    d["PurePremium"] = d["ClaimAmount"] / d["Exposure"]
    d["Frequency"] = d["ClaimNb"] / d["Exposure"]
    d["AvgClaimAmount"] = d["ClaimAmount"] / np.fmax(d["ClaimNb"], 1)
    return d


def cleaning_receipt(freq: pd.DataFrame, sev: pd.DataFrame) -> dict:
    """Quantify each fixed target/data edit before any model fit."""
    raw = joined_raw(freq, sev)
    claimnb = raw["ClaimNb"].astype(float)
    exposure = raw["Exposure"].astype(float)
    amount = raw["ClaimAmount"].astype(float)
    claimnb_capped = claimnb.clip(upper=REFERENCE_CLAIMNB_CAP)
    zero_reset = (amount == 0) & (claimnb_capped >= 1)
    amount_capped = amount.clip(upper=REFERENCE_CLAIM_AMOUNT_CAP)
    return {
        "frequency_idpol_unique": bool(freq["IDpol"].is_unique),
        "frequency_idpol_unique_count": int(freq["IDpol"].nunique()),
        "frequency_idpol_duplicate_rows": int(freq["IDpol"].duplicated(keep=False).sum()),
        "claimnb_cap": {
            "cap": REFERENCE_CLAIMNB_CAP,
            "rows_changed": int((claimnb > REFERENCE_CLAIMNB_CAP).sum()),
            "claims_removed": float((claimnb - claimnb_capped).sum()),
        },
        "exposure_cap": {
            "rows_changed": int((exposure > 1).sum()),
            "exposure_removed": float((exposure - exposure.clip(upper=1)).sum()),
        },
        "claim_amount_cap_eur": {
            "cap": REFERENCE_CLAIM_AMOUNT_CAP,
            "policy_rows_changed": int((amount > REFERENCE_CLAIM_AMOUNT_CAP).sum()),
            "euros_removed": float((amount - amount_capped).sum()),
        },
        "zero_amount_claimnb_reset": {
            "rows_changed": int(zero_reset.sum()),
            "claims_removed_after_claimnb_cap": float(claimnb_capped[zero_reset].sum()),
        },
        "raw_joined_total_claim_amount": float(amount.sum()),
        "reference_capped_total_claim_amount": float(amount_capped.sum()),
    }


def split_id_receipts(d: pd.DataFrame, seeds: tuple[int, ...]) -> list[dict]:
    """Hash exact outer policy-ID membership; no outcome enters the split."""
    from sklearn.model_selection import train_test_split

    ids = d.index.to_numpy(dtype=np.int64)
    positions = np.arange(len(d))
    out = []
    for seed in seeds:
        i, j = train_test_split(positions, test_size=0.25, random_state=int(seed))
        train_ids = np.sort(ids[i])
        test_ids = np.sort(ids[j])
        out.append(
            {
                "seed": int(seed),
                "train_rows": int(len(i)),
                "test_rows": int(len(j)),
                "train_id_sha256": hashlib.sha256(train_ids.tobytes()).hexdigest(),
                "test_id_sha256": hashlib.sha256(test_ids.tobytes()).hexdigest(),
            }
        )
    return out


def variant_result(d: pd.DataFrame, seeds: tuple[int, ...]) -> dict:
    splits = [base.one_split(d, int(seed)) for seed in seeds]
    return {
        "prepared_policy_rows": int(len(d)),
        "prepared_positive_claim_rows": int((d["ClaimAmount"] > 0).sum()),
        "prepared_total_exposure": float(d["Exposure"].sum()),
        "prepared_total_claim_amount": float(d["ClaimAmount"].sum()),
        "splits": splits,
        "summary": base.summarize(splits),
    }


def sensitivity_deltas(reference: dict, uncapped: dict) -> dict:
    """Legacy direct-minus-componentwise-product sensitivity contract."""
    out = {}
    ref = reference["summary"]["direct_vs_product"]
    raw = uncapped["summary"]["direct_vs_product"]
    for model in sorted(ref):
        by_seed = []
        for a, b in zip(ref[model], raw[model], strict=True):
            if a["seed"] != b["seed"]:
                raise ValueError("variant seed mismatch")
            by_seed.append(
                {
                    "seed": int(a["seed"]),
                    "variant_minus_reference_abs_calibration_gap": float(
                        b["abs_calibration_error_difference_direct_minus_product"]
                        - a["abs_calibration_error_difference_direct_minus_product"]
                    ),
                    "variant_minus_reference_gini_gap": float(
                        b["ordered_gini_difference_direct_minus_product"]
                        - a["ordered_gini_difference_direct_minus_product"]
                    ),
                    "variant_minus_reference_deviance_gap": {
                        p: float(
                            b["deviance_difference_direct_minus_product"][p]
                            - a["deviance_difference_direct_minus_product"][p]
                        )
                        for p in a["deviance_difference_direct_minus_product"]
                    },
                }
            )
        out[model] = by_seed
    return out


def _comparison_group_deltas(
    reference: dict,
    variant: dict,
    *,
    group: str,
    prefix: str,
) -> dict:
    """Compare model-gap rows across cleaning variants for one comparison group."""
    ref_group = reference["summary"][group]
    variant_group = variant["summary"][group]
    if set(ref_group) != set(variant_group):
        raise ValueError(f"comparison model set drift in {group}")
    out = {}
    cal_key = f"abs_calibration_error_difference_{prefix}"
    gini_key = f"ordered_gini_difference_{prefix}"
    dev_key = f"deviance_difference_{prefix}"
    band_key = f"exposure_band_abs_calibration_error_difference_{prefix}"
    for model in sorted(ref_group):
        rows = []
        for a, b in zip(ref_group[model], variant_group[model], strict=True):
            if a["seed"] != b["seed"]:
                raise ValueError("variant seed mismatch")
            row = {
                "seed": int(a["seed"]),
                "variant_minus_reference_abs_calibration_gap": float(
                    b[cal_key] - a[cal_key]
                ),
                "variant_minus_reference_gini_gap": float(b[gini_key] - a[gini_key]),
                "variant_minus_reference_deviance_gap": {
                    p: float(b[dev_key][p] - a[dev_key][p]) for p in a[dev_key]
                },
            }
            if band_key in a and band_key in b:
                row["variant_minus_reference_exposure_band_abs_calibration_gap"] = {
                    band: (
                        None
                        if a[band_key][band] is None or b[band_key][band] is None
                        else float(b[band_key][band] - a[band_key][band])
                    )
                    for band in a[band_key]
                }
            if "selection_power" in a or "selection_power" in b:
                if a.get("selection_power") != b.get("selection_power"):
                    raise ValueError("selection power drift across cleaning variants")
                row["selection_power"] = a.get("selection_power")
            rows.append(row)
        out[model] = rows
    return out


def comparison_sensitivity_deltas(reference: dict, variant: dict) -> dict:
    """Preserve cleaning sensitivity for componentwise and joint product challengers."""
    return {
        "direct_vs_componentwise_product": _comparison_group_deltas(
            reference,
            variant,
            group="direct_vs_product",
            prefix="direct_minus_product",
        ),
        "direct_vs_joint_product_same_power": _comparison_group_deltas(
            reference,
            variant,
            group="direct_vs_joint_product_same_power",
            prefix="direct_minus_joint_product",
        ),
    }


def _max_numeric_delta(left, right, path: str = "root") -> float:
    if isinstance(left, dict) and isinstance(right, dict):
        if set(left) != set(right):
            raise ValueError(f"metric schema drift at {path}")
        return max(
            (_max_numeric_delta(left[k], right[k], f"{path}.{k}") for k in left),
            default=0.0,
        )
    if left is None or right is None:
        if left is right:
            return 0.0
        raise ValueError(f"null/non-null metric drift at {path}")
    if isinstance(left, (int, float, np.number)) and isinstance(
        right, (int, float, np.number)
    ):
        a, b = float(left), float(right)
        if not (math.isfinite(a) and math.isfinite(b)):
            if a == b:
                return 0.0
            raise ValueError(f"non-finite metric drift at {path}")
        return abs(a - b)
    if left != right:
        raise ValueError(f"non-numeric metric drift at {path}: {left!r} != {right!r}")
    return 0.0


def assert_direct_tweedie_metric_invariance(
    reference: dict,
    raw_claimnb: dict,
    *,
    atol: float = 1e-12,
) -> dict:
    """Fail closed if the ClaimNb-only sensitivity moves direct Tweedie evidence.

    Direct Tweedie uses PurePremium and Exposure, both unchanged by removing only
    the ClaimNb cap. The base payload does not retain prediction vectors, so this
    receipt binds model selection and all retained held-out direct-Tweedie metrics.
    """
    if len(reference["splits"]) != len(raw_claimnb["splits"]):
        raise ValueError("direct Tweedie split-count drift")
    max_delta = 0.0
    checked = 0
    for a, b in zip(reference["splits"], raw_claimnb["splits"], strict=True):
        if a["seed"] != b["seed"]:
            raise ValueError("direct Tweedie seed drift")
        for power in base.FIT_POWERS:
            key = str(power)
            name = f"direct_tweedie_p{power}"
            if a["selected"]["tweedie_by_power"][key] != b["selected"]["tweedie_by_power"][key]:
                raise AssertionError(
                    f"ClaimNb-only sensitivity changed direct Tweedie selection: seed={a['seed']} power={power}"
                )
            delta = _max_numeric_delta(
                a["metrics"][name], b["metrics"][name], f"seed={a['seed']}.{name}"
            )
            max_delta = max(max_delta, delta)
            checked += 1
    if max_delta > atol:
        raise AssertionError(
            f"ClaimNb-only sensitivity changed retained direct Tweedie metrics: {max_delta} > {atol}"
        )
    return {
        "status": "PASS",
        "checked_seed_power_pairs": checked,
        "absolute_tolerance": float(atol),
        "max_abs_retained_metric_delta": float(max_delta),
        "scope": "selection + retained held-out metrics; prediction vectors are not retained by base payload",
    }


def run(seeds: tuple[int, ...]) -> dict:
    freq, sev, meta = base.load_raw()
    receipt = cleaning_receipt(freq, sev)
    if not receipt["frequency_idpol_unique"]:
        raise ValueError("frequency IDpol must be unique before policy-row splitting")

    reference = prepare_variant(
        freq,
        sev,
        claim_amount_cap=REFERENCE_CLAIM_AMOUNT_CAP,
        claimnb_cap=REFERENCE_CLAIMNB_CAP,
    )
    # Fail closed if the reused wrapper accidentally drifts from the original
    # scikit-learn-reference preparation implemented by the base branch.
    pd.testing.assert_frame_equal(reference, base.prepare(freq, sev))

    uncapped_amount = prepare_variant(
        freq,
        sev,
        claim_amount_cap=None,
        claimnb_cap=REFERENCE_CLAIMNB_CAP,
    )
    raw_claimnb = prepare_variant(
        freq,
        sev,
        claim_amount_cap=REFERENCE_CLAIM_AMOUNT_CAP,
        claimnb_cap=None,
    )
    for candidate in (uncapped_amount, raw_claimnb):
        if not reference.index.equals(candidate.index):
            raise ValueError("sensitivity must preserve exact policy-row identity/order")

    split_receipts = split_id_receipts(reference, seeds)
    variants = {
        "reference_cleaned": variant_result(reference, seeds),
        "uncapped_joined_claim_amount": variant_result(uncapped_amount, seeds),
        "raw_claimnb_reference_amount_cap": variant_result(raw_claimnb, seeds),
    }
    direct_claimnb_invariance = assert_direct_tweedie_metric_invariance(
        variants["reference_cleaned"], variants["raw_claimnb_reference_amount_cap"]
    )
    payload = {
        "schema_version": 3,
        "research_boundary": (
            "pure-premium mean-model repeated holdout and isolated fixed data-cleaning "
            "sensitivities only; no predictive tail-law, capital, or default claim"
        ),
        "data": {
            "openml": meta,
            "diagnostics_before_reconciliation": base.reconciliation(freq, sev),
            "cleaning_receipt": receipt,
        },
        "settings": {
            "outer_seeds": list(map(int, seeds)),
            "outer_test_fraction": 0.25,
            "same_outer_policy_ids_across_variants": True,
            "split_policy_rows_before_learned_preprocessing": True,
            "tweedie_power_rule": (
                "powers 1.5 and 1.9 are predeclared fit sensitivities; never "
                "selected by comparing deviances across different powers"
            ),
            "claim_amount_sensitivity_rule": (
                "remove only the fixed EUR 200000 aggregated-policy amount cap; "
                "retain ClaimNb<=4 and do not tune on held-out outcomes"
            ),
            "claimnb_sensitivity_rule": (
                "remove only the fixed ClaimNb<=4 cap; retain the EUR 200000 amount "
                "cap, exposure/reconciliation rules, policy IDs, splits and consumers; "
                "do not tune the cleaning choice on held-out outcomes"
            ),
        },
        "outer_split_id_receipts": split_receipts,
        "variants": variants,
        "direct_tweedie_claimnb_invariance": direct_claimnb_invariance,
    }
    # Preserve the pre-existing amount-sensitivity field while adding a complete
    # comparison surface for both componentwise and consumer-aligned products.
    payload["sensitivity_uncapped_minus_reference"] = sensitivity_deltas(
        variants["reference_cleaned"],
        variants["uncapped_joined_claim_amount"],
    )
    payload["comparison_sensitivity"] = {
        "uncapped_claim_amount_minus_reference": comparison_sensitivity_deltas(
            variants["reference_cleaned"],
            variants["uncapped_joined_claim_amount"],
        ),
        "raw_claimnb_minus_reference": comparison_sensitivity_deltas(
            variants["reference_cleaned"],
            variants["raw_claimnb_reference_amount_cap"],
        ),
    }
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False)
    payload["semantic_receipt_sha256"] = hashlib.sha256(canonical.encode()).hexdigest()
    return payload


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", default=",".join(map(str, base.SEEDS)))
    ap.add_argument("--output", type=Path)
    args = ap.parse_args()
    seeds = tuple(int(x) for x in args.seeds.split(",") if x.strip())
    if len(seeds) < 2:
        raise SystemExit("need at least two outer seeds")
    payload = run(seeds)
    text = json.dumps(payload, indent=2, sort_keys=True)
    if args.output:
        args.output.write_text(text + "\n", encoding="utf-8")
    print(text)
    print(
        "UNDERWRITING_FREMTPL_RAW_SENSITIVITY_OK "
        f"seeds={len(seeds)} receipt={payload['semantic_receipt_sha256']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
