#!/usr/bin/env python3
"""Correct the FFBK #1319 duration-by-risk diagnostic only.

This is a post-exposure diagnostic on the already-observed reference target and
confirmation seeds. Risk cut points come from baseline outer-training predictions
and each outer-test policy receives ONE baseline-risk group from the baseline
prediction. That fixed group is reused for both baseline and challenger summaries.
No new model class, seed, target definition or promotion claim is introduced.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np

import independent_fremtpl_duration_frequency_runner as base


def fixed_summary(test, pred, fixed_risk):
    exposure = test["Exposure"].to_numpy(float)
    observed = test["ClaimNb"].to_numpy(float)
    predicted_count = exposure * np.asarray(pred, float)
    fixed_risk = np.asarray(fixed_risk, int)

    def summarize(mask):
        obs = float(observed[mask].sum())
        fit = float(predicted_count[mask].sum())
        return {
            "rows": int(mask.sum()),
            "observed_claims": obs,
            "predicted_claims": fit,
            "predicted_over_observed": None if obs <= 0 else fit / obs,
        }

    bands = {}
    band_risk = {}
    for lo, hi, label in base.BANDS:
        band_mask = (exposure > lo) & (exposure <= hi)
        bands[label] = summarize(band_mask)
        band_risk[label] = {
            str(group): summarize(band_mask & (fixed_risk == group))
            for group in range(4)
        }
    return {
        "overall": summarize(np.ones(len(test), dtype=bool)),
        "duration_bands": bands,
        "duration_by_fixed_baseline_risk_quartile": band_risk,
    }


def one_split(data, seed):
    from sklearn.linear_model import PoissonRegressor
    from sklearn.metrics import mean_poisson_deviance
    from sklearn.model_selection import train_test_split

    outer_train_idx, outer_test_idx = train_test_split(
        np.arange(len(data)), test_size=0.25, random_state=seed
    )
    outer_train = data.iloc[outer_train_idx]
    outer_test = data.iloc[outer_test_idx]
    inner_fit_idx, inner_val_idx = train_test_split(
        np.arange(len(outer_train)), test_size=0.20, random_state=seed + 10000
    )
    inner_fit = outer_train.iloc[inner_fit_idx]
    inner_val = outer_train.iloc[inner_val_idx]

    validation = base._validation_scores(
        inner_fit, inner_val, forms=("none",) + base.DURATION_FORMS
    )
    baseline_form, baseline_alpha, _ = base._select(validation, ("none",))
    challenger_form, challenger_alpha, _ = base._select(validation, base.DURATION_FORMS)

    btr = base.preprocessor(baseline_form)
    bx_train = btr.fit_transform(outer_train)
    bx_test = btr.transform(outer_test)
    bm = PoissonRegressor(alpha=baseline_alpha, solver="newton-cholesky")
    bm.fit(bx_train, outer_train["Frequency"], sample_weight=outer_train["Exposure"])
    baseline_train_pred = bm.predict(bx_train)
    baseline_test_pred = bm.predict(bx_test)

    ctr = base.preprocessor(challenger_form)
    cx_train = ctr.fit_transform(outer_train)
    cx_test = ctr.transform(outer_test)
    cm = PoissonRegressor(alpha=challenger_alpha, solver="newton-cholesky")
    cm.fit(cx_train, outer_train["Frequency"], sample_weight=outer_train["Exposure"])
    challenger_test_pred = cm.predict(cx_test)

    risk_edges = base._risk_edges(baseline_train_pred)
    fixed_risk = np.searchsorted(
        np.asarray(risk_edges), np.asarray(baseline_test_pred, float), side="right"
    )
    test_ids = np.sort(data.index.to_numpy(np.int64)[outer_test_idx])

    baseline_dev = float(mean_poisson_deviance(
        outer_test["Frequency"], baseline_test_pred, sample_weight=outer_test["Exposure"]
    ))
    challenger_dev = float(mean_poisson_deviance(
        outer_test["Frequency"], challenger_test_pred, sample_weight=outer_test["Exposure"]
    ))

    baseline_summary = fixed_summary(outer_test, baseline_test_pred, fixed_risk)
    challenger_summary = fixed_summary(outer_test, challenger_test_pred, fixed_risk)

    # Fail closed: every duration x risk cell must have identical policy membership.
    for _, _, label in base.BANDS:
        for group in range(4):
            key = str(group)
            br = baseline_summary["duration_by_fixed_baseline_risk_quartile"][label][key]["rows"]
            cr = challenger_summary["duration_by_fixed_baseline_risk_quartile"][label][key]["rows"]
            if br != cr:
                raise AssertionError(f"fixed membership violated {label}/{key}: {br} != {cr}")

    return {
        "seed": int(seed),
        "test_id_sha256": hashlib.sha256(test_ids.tobytes()).hexdigest(),
        "selected": {
            "baseline": {"form": baseline_form, "alpha": baseline_alpha},
            "duration_challenger": {"form": challenger_form, "alpha": challenger_alpha},
        },
        "baseline_poisson_deviance": baseline_dev,
        "duration_challenger_poisson_deviance": challenger_dev,
        "baseline_minus_challenger_deviance": baseline_dev - challenger_dev,
        "train_baseline_risk_quartile_edges": risk_edges,
        "baseline": baseline_summary,
        "duration_challenger": challenger_summary,
    }


def canonical_hash(payload):
    body = dict(payload)
    body.pop("canonical_sha256", None)
    raw = json.dumps(body, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    return hashlib.sha256(raw).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    frequency, severity, openml = base.load_target()
    data, receipt = base.prepare(frequency, severity, raw_claimnb=False)
    splits = [one_split(data, seed) for seed in base.CONFIRMATION_SEEDS]
    payload = {
        "schema": 1,
        "diagnostic": "fixed baseline-risk strata correction for FFBK #1319",
        "validation_status": "post_exposure_diagnostic_only; same reference target, model class and exposed confirmation seeds",
        "confirmation_seeds_reused_exploratorily": list(base.CONFIRMATION_SEEDS),
        "openml": openml,
        "data_receipt": receipt,
        "environment": base.environment_receipt(),
        "splits": splits,
    }
    payload["canonical_sha256"] = canonical_hash(payload)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")

    compact = []
    for split in splits:
        s = split["seed"]
        for label in ("(0,0.25]", "(0.75,1.00]"):
            b = split["baseline"]["duration_by_fixed_baseline_risk_quartile"][label]["3"]
            c = split["duration_challenger"]["duration_by_fixed_baseline_risk_quartile"][label]["3"]
            compact.append({
                "seed": s, "band": label, "rows": b["rows"],
                "baseline_po": b["predicted_over_observed"],
                "challenger_po": c["predicted_over_observed"],
            })
    print(json.dumps({"canonical_sha256": payload["canonical_sha256"], "high_risk": compact}, sort_keys=True))


if __name__ == "__main__":
    main()
