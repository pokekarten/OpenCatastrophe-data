#!/usr/bin/env python3
"""Post-exposure sensitivity for FFBK #1319 frequency target semantics.

This deliberately reuses the already-executed duration challenger implementation
and already-inspected confirmation splits. It is NOT a new confirmatory holdout.
The only scientific change is that freMTPL2freq ClaimNb remains authoritative for
the frequency consumer: the existing ClaimNb<=4 and Exposure<=1 caps are retained,
but ClaimNb is not reset to zero merely because the severity join has no positive
ClaimAmount for that policy.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

import independent_fremtpl_duration_frequency_runner as base


def prepare_frequency_authoritative(
    frequency: pd.DataFrame,
    severity: pd.DataFrame,
) -> tuple[pd.DataFrame, dict]:
    data = frequency.copy()
    for column in data.columns:
        if data[column].dtype == object or isinstance(data[column].dtype, pd.CategoricalDtype):
            data[column] = data[column].astype(str).str.strip("'")

    data = data.set_index("IDpol")
    raw_nb = data["ClaimNb"].astype(float).copy()
    raw_exposure = data["Exposure"].astype(float).copy()
    data["ClaimNb"] = raw_nb.clip(upper=4)
    data["Exposure"] = raw_exposure.clip(upper=1)
    if not bool((data["Exposure"] > 0).all()):
        raise ValueError("non-positive Exposure after preparation")
    data["Frequency"] = data["ClaimNb"] / data["Exposure"]

    amounts = severity.groupby("IDpol", sort=False)["ClaimAmount"].sum()
    matched_amount = data.index.to_series().map(amounts).fillna(0.0).astype(float)
    would_reset = (matched_amount == 0.0) & (data["ClaimNb"] >= 1.0)

    receipt = {
        "rows": int(len(data)),
        "idpol_unique": bool(data.index.is_unique),
        "prepared_total_exposure": float(data["Exposure"].sum()),
        "frequency_authoritative_claimnb_after_cap": float(data["ClaimNb"].sum()),
        "would_have_severity_zero_reset_rows": int(would_reset.sum()),
        "would_have_severity_zero_reset_claimnb_after_cap": float(data.loc[would_reset, "ClaimNb"].sum()),
        "raw_claimnb_gt4_rows": int((raw_nb > 4).sum()),
        "raw_claimnb_gt4_excess_count": float((raw_nb - raw_nb.clip(upper=4)).sum()),
        "exposure_gt1_rows": int((raw_exposure > 1).sum()),
        "severity_rows": int(len(severity)),
        "severity_orphans": int((~severity["IDpol"].isin(frequency["IDpol"])).sum()),
        "target_semantics": "freMTPL2freq ClaimNb authoritative; retain ClaimNb<=4 and Exposure<=1; no severity-based ClaimNb reset",
    }
    return data, receipt


def canonical_hash(payload: dict) -> str:
    body = dict(payload)
    body.pop("canonical_sha256", None)
    raw = json.dumps(body, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    return hashlib.sha256(raw).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    frequency, severity, openml = base.load_target()
    data, receipt = prepare_frequency_authoritative(frequency, severity)

    # These splits/model forms were already observed. This is a controlled target
    # definition sensitivity, not fresh confirmation.
    splits = [
        base.one_split(data, seed, "post_exposure_target_definition_sensitivity")
        for seed in base.CONFIRMATION_SEEDS
    ]

    payload = {
        "schema": 1,
        "question": "Does the duration-aware frequency advantage survive when freMTPL2freq ClaimNb, rather than the severity join, defines the frequency target?",
        "validation_status": "post_exposure_sensitivity_only; confirmation seeds and model class already inspected",
        "confirmation_seeds_reused_exploratorily": list(base.CONFIRMATION_SEEDS),
        "data_receipt": receipt,
        "openml": openml,
        "environment": base.environment_receipt(),
        "splits": splits,
    }
    payload["canonical_sha256"] = canonical_hash(payload)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "canonical_sha256": payload["canonical_sha256"],
        "claimnb_total": receipt["frequency_authoritative_claimnb_after_cap"],
        "would_reset_rows": receipt["would_have_severity_zero_reset_rows"],
        "would_reset_claimnb": receipt["would_have_severity_zero_reset_claimnb_after_cap"],
        "deltas": [s["outer_test"]["baseline_minus_challenger_deviance"] for s in splits],
        "selected": [s["selected"]["duration_challenger"] for s in splits],
    }, sort_keys=True))


if __name__ == "__main__":
    main()
