#!/usr/bin/env python3
"""Leakage-aware freMTPL2 mean-model tournament (research only)."""
from __future__ import annotations

import argparse
import hashlib
import json
import urllib.request
from pathlib import Path

import numpy as np
import pandas as pd

FREQ_ID, SEV_ID = 41214, 41215
SEEDS = (0, 17, 42)
EVAL_POWERS = (1.5, 1.7, 1.8, 1.9)
FIT_POWERS = (1.5, 1.9)
FREQ_ALPHAS = (1e-4, 1e-3)
SEV_ALPHAS = (1.0, 10.0)
TW_ALPHAS = (0.05, 0.1, 0.5)
EXPOSURE_BANDS = (
    (0.0, 0.25, "(0,0.25]"),
    (0.25, 0.50, "(0.25,0.50]"),
    (0.50, 0.75, "(0.50,0.75]"),
    (0.75, 1.00, "(0.75,1.00]"),
)


def openml_meta(data_id: int) -> dict:
    url = f"https://www.openml.org/api/v1/json/data/{data_id}"
    with urllib.request.urlopen(url, timeout=60) as r:
        d = json.loads(r.read().decode())["data_set_description"]
    return {
        "data_id": int(d["id"]),
        "name": d.get("name"),
        "version": int(d["version"]) if d.get("version") else None,
        "md5_checksum": d.get("md5_checksum"),
        "status": d.get("status"),
    }


def load_raw():
    from sklearn.datasets import fetch_openml

    freq = fetch_openml(data_id=FREQ_ID, as_frame=True).data.copy()
    sev = fetch_openml(data_id=SEV_ID, as_frame=True).data.copy()
    freq["IDpol"] = freq["IDpol"].astype("int64")
    sev["IDpol"] = sev["IDpol"].astype("int64")
    sev["ClaimAmount"] = sev["ClaimAmount"].astype(float)
    return freq, sev, {"frequency": openml_meta(FREQ_ID), "severity": openml_meta(SEV_ID)}


def reconciliation(freq: pd.DataFrame, sev: pd.DataFrame) -> dict:
    counts = sev.groupby("IDpol", sort=False).size()
    matched = freq["IDpol"].map(counts).fillna(0).astype("int64")
    return {
        "frequency_rows": int(len(freq)),
        "severity_rows": int(len(sev)),
        "severity_rows_without_policy": int((~sev["IDpol"].isin(freq["IDpol"])).sum()),
        "policies_claimnb_vs_severity_count_mismatch": int(
            (freq["ClaimNb"].astype("int64").to_numpy() != matched.to_numpy()).sum()
        ),
    }


def prepare(freq: pd.DataFrame, sev: pd.DataFrame) -> pd.DataFrame:
    f = freq.copy()
    for c in f.columns:
        if f[c].dtype == object or isinstance(f[c].dtype, pd.CategoricalDtype):
            f[c] = f[c].astype(str).str.strip("'")
    amounts = sev.groupby("IDpol", sort=False)["ClaimAmount"].sum()
    d = f.set_index("IDpol")
    d["ClaimAmount"] = d.index.to_series().map(amounts).fillna(0.0).astype(float)
    d["ClaimNb"] = d["ClaimNb"].astype(float).clip(upper=4)
    d["Exposure"] = d["Exposure"].astype(float).clip(upper=1)
    d["ClaimAmount"] = d["ClaimAmount"].clip(upper=200000)
    d.loc[(d["ClaimAmount"] == 0) & (d["ClaimNb"] >= 1), "ClaimNb"] = 0
    if not (d["Exposure"] > 0).all():
        raise ValueError("Exposure must stay positive")
    d["PurePremium"] = d["ClaimAmount"] / d["Exposure"]
    d["Frequency"] = d["ClaimNb"] / d["Exposure"]
    d["AvgClaimAmount"] = d["ClaimAmount"] / np.fmax(d["ClaimNb"], 1)
    return d


def preprocessor():
    from sklearn.compose import ColumnTransformer
    from sklearn.pipeline import make_pipeline
    from sklearn.preprocessing import (
        FunctionTransformer,
        KBinsDiscretizer,
        OneHotEncoder,
        StandardScaler,
    )

    return ColumnTransformer(
        [
            (
                "bin",
                KBinsDiscretizer(
                    n_bins=10,
                    quantile_method="averaged_inverted_cdf",
                    random_state=0,
                ),
                ["VehAge", "DrivAge"],
            ),
            (
                "cat",
                OneHotEncoder(handle_unknown="ignore"),
                ["VehBrand", "VehPower", "VehGas", "Region", "Area"],
            ),
            ("num", "passthrough", ["BonusMalus"]),
            (
                "density",
                make_pipeline(FunctionTransformer(func=np.log), StandardScaler()),
                ["Density"],
            ),
        ]
    )


def po_ratio(y, pred, w) -> float:
    obs = float(np.sum(np.asarray(w) * np.asarray(y)))
    if obs <= 0:
        raise ValueError("positive observed total required")
    return float(np.sum(np.asarray(w) * np.asarray(pred))) / obs


def exposure_band_calibration(test: pd.DataFrame, pred) -> dict:
    """Outcome-independent duration-band calibration on held-out policies."""
    y = test["PurePremium"].to_numpy(float)
    w = test["Exposure"].to_numpy(float)
    p = np.asarray(pred, float)
    if len(p) != len(test):
        raise ValueError("prediction length mismatch")
    out = {}
    for lo, hi, label in EXPOSURE_BANDS:
        mask = (w > lo) & (w <= hi)
        obs = float(np.sum(w[mask] * y[mask]))
        fitted = float(np.sum(w[mask] * p[mask]))
        ratio = None if obs <= 0 else fitted / obs
        out[label] = {
            "policy_rows": int(mask.sum()),
            "positive_claim_rows": int(
                (test.loc[mask, "ClaimAmount"].to_numpy(float) > 0).sum()
            ),
            "observed_total_claim_amount": obs,
            "predicted_total_claim_amount": fitted,
            "predicted_observed_total_ratio": ratio,
            "absolute_calibration_error": None if ratio is None else abs(ratio - 1.0),
        }
    return out


def gini(y, pred, w) -> float:
    """Weighted Lorenz Gini with exact prediction ties treated as one score group."""
    y, pred, w = map(lambda x: np.asarray(x, float), (y, pred, w))
    if np.any(w < 0) or w.sum() <= 0 or np.sum(w * y) <= 0:
        raise ValueError("positive loss/exposure required")
    order = np.argsort(pred, kind="stable")
    sorted_pred = pred[order]
    sorted_w = w[order]
    sorted_loss = (w * y)[order]
    starts = np.r_[0, 1 + np.flatnonzero(sorted_pred[1:] != sorted_pred[:-1])]
    group_w = np.add.reduceat(sorted_w, starts)
    group_loss = np.add.reduceat(sorted_loss, starts)
    cw = np.r_[0.0, np.cumsum(group_w) / w.sum()]
    cl = np.r_[0.0, np.cumsum(group_loss) / np.sum(w * y)]
    return float(1 - 2 * np.trapezoid(cl, cw))


def _pair_key(frequency_alpha: float, severity_alpha: float) -> str:
    return f"frequency_alpha={frequency_alpha}|severity_alpha={severity_alpha}"


def consumer_aligned_product_tuning(
    validation: pd.DataFrame,
    frequency_predictions: dict[float, np.ndarray],
    severity_predictions: dict[float, np.ndarray],
) -> dict:
    """Select product regularization on inner validation, separately per power.

    This is deliberately a *selection* sensitivity, not a new outer-test metric.
    Every candidate is fit without outer-test rows; no winner is selected across
    different Tweedie powers.
    """
    from sklearn.metrics import mean_tweedie_deviance

    y = validation["PurePremium"].to_numpy(float)
    w = validation["Exposure"].to_numpy(float)
    out = {}
    for power in FIT_POWERS:
        scores = {}
        pairs = []
        for frequency_alpha in FREQ_ALPHAS:
            for severity_alpha in SEV_ALPHAS:
                pair = (frequency_alpha, severity_alpha)
                pairs.append(pair)
                prediction = (
                    np.asarray(frequency_predictions[frequency_alpha], float)
                    * np.asarray(severity_predictions[severity_alpha], float)
                )
                scores[_pair_key(*pair)] = float(
                    mean_tweedie_deviance(
                        y,
                        prediction,
                        sample_weight=w,
                        power=power,
                    )
                )
        selected = min(
            pairs,
            key=lambda pair: (scores[_pair_key(*pair)], pair[0], pair[1]),
        )
        out[str(power)] = {
            "frequency_alpha": selected[0],
            "severity_alpha": selected[1],
            "validation_deviance_same_power": scores,
        }
    return out


def tune(train: pd.DataFrame, seed: int) -> dict:
    from sklearn.linear_model import GammaRegressor, PoissonRegressor, TweedieRegressor
    from sklearn.metrics import (
        mean_gamma_deviance,
        mean_poisson_deviance,
        mean_tweedie_deviance,
    )
    from sklearn.model_selection import train_test_split

    i, v = train_test_split(
        np.arange(len(train)), test_size=.2, random_state=seed + 10000
    )
    a, b = train.iloc[i], train.iloc[v]
    pre = preprocessor()
    xa = pre.fit_transform(a)
    xb = pre.transform(b)

    fs = {}
    frequency_predictions = {}
    for alpha in FREQ_ALPHAS:
        m = PoissonRegressor(alpha=alpha, solver="newton-cholesky").fit(
            xa,
            a["Frequency"],
            sample_weight=a["Exposure"],
        )
        prediction = m.predict(xb)
        frequency_predictions[alpha] = prediction
        fs[str(alpha)] = float(
            mean_poisson_deviance(
                b["Frequency"], prediction, sample_weight=b["Exposure"]
            )
        )

    ps = a["ClaimAmount"].to_numpy() > 0
    qs = b["ClaimAmount"].to_numpy() > 0
    ss = {}
    severity_predictions = {}
    for alpha in SEV_ALPHAS:
        m = GammaRegressor(alpha=alpha, solver="newton-cholesky").fit(
            xa[ps],
            a.loc[ps, "AvgClaimAmount"],
            sample_weight=a.loc[ps, "ClaimNb"],
        )
        prediction = m.predict(xb)
        severity_predictions[alpha] = prediction
        ss[str(alpha)] = float(
            mean_gamma_deviance(
                b.loc[qs, "AvgClaimAmount"],
                prediction[qs],
                sample_weight=b.loc[qs, "ClaimNb"],
            )
        )

    product_joint = consumer_aligned_product_tuning(
        b, frequency_predictions, severity_predictions
    )

    tw = {}
    for power in FIT_POWERS:
        scores = {}
        for alpha in TW_ALPHAS:
            m = TweedieRegressor(
                power=power, alpha=alpha, solver="newton-cholesky"
            ).fit(
                xa,
                a["PurePremium"],
                sample_weight=a["Exposure"],
            )
            scores[str(alpha)] = float(
                mean_tweedie_deviance(
                    b["PurePremium"],
                    m.predict(xb),
                    sample_weight=b["Exposure"],
                    power=power,
                )
            )
        tw[str(power)] = {
            "alpha": min(TW_ALPHAS, key=lambda x: scores[str(x)]),
            "validation_deviance_same_power": scores,
        }
    return {
        "frequency": {
            "alpha": min(FREQ_ALPHAS, key=lambda x: fs[str(x)]),
            "validation_poisson_deviance": fs,
        },
        "severity": {
            "alpha": min(SEV_ALPHAS, key=lambda x: ss[str(x)]),
            "validation_gamma_deviance": ss,
        },
        "product_joint_by_power": product_joint,
        "tweedie_by_power": tw,
    }


def metrics(test: pd.DataFrame, predictions: dict) -> dict:
    from sklearn.metrics import mean_tweedie_deviance

    y = test["PurePremium"].to_numpy(float)
    w = test["Exposure"].to_numpy(float)
    out = {}
    for name, pred in predictions.items():
        r = po_ratio(y, pred, w)
        out[name] = {
            "predicted_observed_total_ratio": r,
            "absolute_calibration_error": abs(r - 1),
            "exposure_band_calibration": exposure_band_calibration(test, pred),
            "ordered_gini": gini(y, pred, w),
            "mean_tweedie_deviance": {
                str(p): float(
                    mean_tweedie_deviance(y, pred, sample_weight=w, power=p)
                )
                for p in EVAL_POWERS
            },
        }
    return out


def _fit_product(
    xtr,
    xeval,
    tr: pd.DataFrame,
    frequency_alpha: float,
    severity_alpha: float,
):
    from sklearn.linear_model import GammaRegressor, PoissonRegressor

    frequency = PoissonRegressor(
        alpha=frequency_alpha, solver="newton-cholesky"
    ).fit(xtr, tr["Frequency"], sample_weight=tr["Exposure"])
    pos = tr["ClaimAmount"].to_numpy() > 0
    severity = GammaRegressor(
        alpha=severity_alpha, solver="newton-cholesky"
    ).fit(
        xtr[pos],
        tr.loc[pos, "AvgClaimAmount"],
        sample_weight=tr.loc[pos, "ClaimNb"],
    )
    return frequency.predict(xeval) * severity.predict(xeval)


def one_split(d: pd.DataFrame, seed: int) -> dict:
    from sklearn.linear_model import TweedieRegressor
    from sklearn.model_selection import train_test_split

    i, j = train_test_split(np.arange(len(d)), test_size=.25, random_state=seed)
    tr, te = d.iloc[i], d.iloc[j]
    sel = tune(tr, seed)
    pre = preprocessor()
    xtr = pre.fit_transform(tr)
    xte = pre.transform(te)

    pred = {
        "product_poisson_gamma": _fit_product(
            xtr,
            xte,
            tr,
            sel["frequency"]["alpha"],
            sel["severity"]["alpha"],
        )
    }
    for power in FIT_POWERS:
        joint = sel["product_joint_by_power"][str(power)]
        pred[f"product_poisson_gamma_joint_p{power}"] = _fit_product(
            xtr,
            xte,
            tr,
            joint["frequency_alpha"],
            joint["severity_alpha"],
        )
        m = TweedieRegressor(
            power=power,
            alpha=sel["tweedie_by_power"][str(power)]["alpha"],
            solver="newton-cholesky",
        ).fit(xtr, tr["PurePremium"], sample_weight=tr["Exposure"])
        pred[f"direct_tweedie_p{power}"] = m.predict(xte)
    return {
        "seed": seed,
        "train_rows": len(tr),
        "test_rows": len(te),
        "test_positive_claim_rows": int((te["ClaimAmount"] > 0).sum()),
        "selected": sel,
        "metrics": metrics(te, pred),
    }


def _mean_non_null(values):
    values = [v for v in values if v is not None]
    return None if not values else float(np.mean(values))


def _comparison_row(seed: int, left: dict, right: dict, prefix: str) -> dict:
    row = {
        "seed": seed,
        f"abs_calibration_error_difference_{prefix}": (
            left["absolute_calibration_error"] - right["absolute_calibration_error"]
        ),
        f"ordered_gini_difference_{prefix}": left["ordered_gini"] - right["ordered_gini"],
        f"deviance_difference_{prefix}": {
            str(p): left["mean_tweedie_deviance"][str(p)]
            - right["mean_tweedie_deviance"][str(p)]
            for p in EVAL_POWERS
        },
    }
    if "exposure_band_calibration" in left and "exposure_band_calibration" in right:
        row[f"exposure_band_abs_calibration_error_difference_{prefix}"] = {
            label: (
                None
                if left["exposure_band_calibration"][label]["absolute_calibration_error"]
                is None
                or right["exposure_band_calibration"][label]["absolute_calibration_error"]
                is None
                else left["exposure_band_calibration"][label]["absolute_calibration_error"]
                - right["exposure_band_calibration"][label]["absolute_calibration_error"]
            )
            for _, _, label in EXPOSURE_BANDS
        }
    return row


def summarize(splits: list[dict]) -> dict:
    names = list(splits[0]["metrics"])
    out = {
        "models": {},
        "direct_vs_product": {},
        "joint_product_vs_componentwise": {},
        "direct_vs_joint_product_same_power": {},
    }
    for name in names:
        rows = [s["metrics"][name] for s in splits]
        model_summary = {
            "predicted_observed_total_ratio_mean": float(
                np.mean([r["predicted_observed_total_ratio"] for r in rows])
            ),
            "absolute_calibration_error_mean": float(
                np.mean([r["absolute_calibration_error"] for r in rows])
            ),
            "ordered_gini_mean": float(np.mean([r["ordered_gini"] for r in rows])),
            "mean_tweedie_deviance_mean": {
                str(p): float(
                    np.mean([r["mean_tweedie_deviance"][str(p)] for r in rows])
                )
                for p in EVAL_POWERS
            },
        }
        if all("exposure_band_calibration" in r for r in rows):
            model_summary["exposure_band_predicted_observed_ratio_mean"] = {
                label: _mean_non_null(
                    [
                        r["exposure_band_calibration"][label][
                            "predicted_observed_total_ratio"
                        ]
                        for r in rows
                    ]
                )
                for _, _, label in EXPOSURE_BANDS
            }
            model_summary["exposure_band_absolute_calibration_error_mean"] = {
                label: _mean_non_null(
                    [
                        r["exposure_band_calibration"][label][
                            "absolute_calibration_error"
                        ]
                        for r in rows
                    ]
                )
                for _, _, label in EXPOSURE_BANDS
            }
        out["models"][name] = model_summary

    componentwise = "product_poisson_gamma"
    for power in FIT_POWERS:
        direct = f"direct_tweedie_p{power}"
        joint = f"product_poisson_gamma_joint_p{power}"
        if direct in names:
            out["direct_vs_product"][direct] = [
                _comparison_row(
                    s["seed"],
                    s["metrics"][direct],
                    s["metrics"][componentwise],
                    "direct_minus_product",
                )
                for s in splits
            ]
        if joint in names:
            out["joint_product_vs_componentwise"][joint] = [
                _comparison_row(
                    s["seed"],
                    s["metrics"][joint],
                    s["metrics"][componentwise],
                    "joint_minus_componentwise",
                )
                for s in splits
            ]
        if direct in names and joint in names:
            out["direct_vs_joint_product_same_power"][direct] = [
                {
                    "selection_power": power,
                    **_comparison_row(
                        s["seed"],
                        s["metrics"][direct],
                        s["metrics"][joint],
                        "direct_minus_joint_product",
                    ),
                }
                for s in splits
            ]
    return out


def run(seeds) -> dict:
    freq, sev, meta = load_raw()
    diag = reconciliation(freq, sev)
    d = prepare(freq, sev)
    splits = [one_split(d, int(seed)) for seed in seeds]
    payload = {
        "schema_version": 3,
        "research_boundary": (
            "duration-marginalized pure-premium mean-model repeated holdout plus "
            "exposure-band calibration and train-only product-tuning sensitivity; "
            "no proof of E[Y|X,W] duration adequacy, predictive dispersion/tail-law, "
            "capital, or reinsurance superiority"
        ),
        "data": {
            "openml": meta,
            "diagnostics_before_reconciliation": diag,
            "prepared_policy_rows": len(d),
            "prepared_positive_claim_rows": int((d["ClaimAmount"] > 0).sum()),
            "prepared_total_exposure": float(d["Exposure"].sum()),
            "prepared_total_claim_amount": float(d["ClaimAmount"].sum()),
        },
        "settings": {
            "outer_seeds": list(map(int, seeds)),
            "outer_test_fraction": .25,
            "inner_validation_fraction_of_outer_train": .2,
            "eval_powers": list(EVAL_POWERS),
            "tweedie_fit_powers": list(FIT_POWERS),
            "frequency_alphas": list(FREQ_ALPHAS),
            "severity_alphas": list(SEV_ALPHAS),
            "tweedie_alphas": list(TW_ALPHAS),
            "exposure_calibration_bands": [
                {"lower_open": lo, "upper_closed": hi, "label": label}
                for lo, hi, label in EXPOSURE_BANDS
            ],
            "power_selection_rule": (
                "NO cross-power selection; Tweedie alpha and consumer-aligned "
                "product pair are selected within each fixed power only"
            ),
            "product_tuning_rule": (
                "retain componentwise Poisson/Gamma-tuned structural reference; "
                "add joint frequency/severity alpha sensitivity selected on inner-"
                "validation PurePremium Tweedie deviance separately at each fixed "
                "power; outer test outcomes never select hyperparameters"
            ),
            "preprocessing_rule": (
                "split policy rows first; fit learned transforms on inner-fit or "
                "outer-train only"
            ),
            "duration_diagnostic_rule": (
                "fixed outcome-independent exposure bands are evaluated on outer "
                "test only; Exposure is not a predictor, so pooled scores do not "
                "establish E[Y|X,W] adequacy"
            ),
            "reconciliation_rule": (
                "sum severity by IDpol; left join; missing amount=0; clip "
                "ClaimNb<=4, Exposure<=1, ClaimAmount<=200000; set ClaimNb=0 "
                "where amount=0 and ClaimNb>=1"
            ),
        },
        "splits": splits,
    }
    payload["summary"] = summarize(splits)
    canonical = json.dumps(
        payload, sort_keys=True, separators=(",", ":"), allow_nan=False
    )
    payload["semantic_receipt_sha256"] = hashlib.sha256(canonical.encode()).hexdigest()
    return payload


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", default=",".join(map(str, SEEDS)))
    ap.add_argument("--output", type=Path)
    a = ap.parse_args()
    seeds = tuple(int(x) for x in a.seeds.split(",") if x.strip())
    if len(seeds) < 2:
        raise SystemExit("need at least two outer seeds")
    payload = run(seeds)
    text = json.dumps(payload, indent=2, sort_keys=True)
    if a.output:
        a.output.write_text(text + "\n", encoding="utf-8")
    print(text)
    print(
        "UNDERWRITING_FREMTPL_RAW_TOURNAMENT_OK "
        f"seeds={len(seeds)} receipt={payload['semantic_receipt_sha256']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())