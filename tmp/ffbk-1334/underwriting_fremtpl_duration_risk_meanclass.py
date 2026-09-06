#!/usr/bin/env python3
"""Prospectively frozen freMTPL2 duration × risk mean-class tournament.

Research-only executable for FFBK PR #1327 follow-up. It compares:
M0 strict pro-rata GLM, M1 global log-duration GLM,
M2 nested/cross-fitted duration×risk GLM,
M3a flexible Poisson HGB without duration, and paired M3b with log-duration.

No predictive-law, reinsurance, capital, or NextGen-default claim is authorized.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import platform
import sys
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd

FREQ_ID = 41214
FREQ_VERSION = 1
FREQ_MD5 = "f8875568bf0ca622929105197e2db613"
QUESTION_FINGERPRINT = "underwriting/fremtpl2/duration-risk/meanclass/m0-m1-m2-m3a-m3b/v1"
QUESTION_SHA256 = "9fd5d48fef5528d1112401df64e8c74b881a413f0d92ac518d2a14786d312ed8"
OUTER_SEEDS = (2681590927, 4015335633, 287572447)
GLM_ALPHA = 1e-4
DURATION_BANDS = (
    (0.0, 0.25, "(0,.25]"),
    (0.25, 0.50, "(.25,.50]"),
    (0.50, 0.75, "(.50,.75]"),
    (0.75, 1.00, "(.75,1]"),
)
CAT_COLS = ("VehBrand", "VehPower", "VehGas", "Region", "Area")
HGB_CONFIGS = (
    ("H1", {"max_leaf_nodes": 15, "min_samples_leaf": 100, "max_iter": 150, "l2_regularization": 1.0}),
    ("H2", {"max_leaf_nodes": 31, "min_samples_leaf": 100, "max_iter": 150, "l2_regularization": 1.0}),
    ("H3", {"max_leaf_nodes": 31, "min_samples_leaf": 50, "max_iter": 200, "l2_regularization": 1.0}),
    ("H4", {"max_leaf_nodes": 63, "min_samples_leaf": 100, "max_iter": 200, "l2_regularization": 1.0}),
)
CONTRASTS = (
    ("M1-M0", "M1", "M0"),
    ("M2-M1", "M2", "M1"),
    ("M3a-M0", "M3a", "M0"),
    ("M3b-M3a", "M3b", "M3a"),
    ("M3b-M2", "M3b", "M2"),
)


def openml_meta(data_id: int) -> dict:
    url = f"https://www.openml.org/api/v1/json/data/{data_id}"
    with urllib.request.urlopen(url, timeout=60) as response:
        d = json.loads(response.read().decode())["data_set_description"]
    return {
        "data_id": int(d["id"]),
        "name": d.get("name"),
        "version": int(d["version"]) if d.get("version") else None,
        "md5_checksum": d.get("md5_checksum"),
        "status": d.get("status"),
        "url": d.get("url"),
        "parquet_url": d.get("parquet_url"),
    }


def load_openml_frequency() -> tuple[pd.DataFrame, dict]:
    from sklearn.datasets import fetch_openml

    meta = openml_meta(FREQ_ID)
    if meta["data_id"] != FREQ_ID or meta["version"] != FREQ_VERSION or meta["md5_checksum"] != FREQ_MD5:
        raise RuntimeError(f"OpenML identity mismatch: {meta}")
    d = fetch_openml(data_id=FREQ_ID, as_frame=True).data.copy()
    return d, meta


def prepare_frequency(raw: pd.DataFrame, *, cap_claimnb: bool = True) -> pd.DataFrame:
    d = raw.copy()
    for c in d.columns:
        if d[c].dtype == object or isinstance(d[c].dtype, pd.CategoricalDtype):
            d[c] = d[c].astype(str).str.strip("'")
    d["IDpol"] = d["IDpol"].astype("int64")
    if d["IDpol"].duplicated().any():
        raise ValueError("IDpol must be unique")
    d["ClaimNb"] = d["ClaimNb"].astype(float)
    if cap_claimnb:
        d["ClaimNb"] = d["ClaimNb"].clip(upper=4)
    d["Exposure"] = d["Exposure"].astype(float).clip(upper=1)
    if not (d["Exposure"] > 0).all():
        raise ValueError("Exposure must stay positive")
    d["Frequency"] = d["ClaimNb"] / d["Exposure"]
    d["logExposure"] = np.log(d["Exposure"])
    d["logDensity"] = np.log(d["Density"].astype(float))
    return d.reset_index(drop=True)


def glm_preprocessor(extra_numeric: Iterable[str] = ()):
    from sklearn.compose import ColumnTransformer
    from sklearn.pipeline import make_pipeline
    from sklearn.preprocessing import FunctionTransformer, KBinsDiscretizer, OneHotEncoder, StandardScaler

    transforms = [
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
    extra_numeric = list(extra_numeric)
    if extra_numeric:
        transforms.append(("extra", StandardScaler(), extra_numeric))
    return ColumnTransformer(transforms)


@dataclass
class GLMBundle:
    pre: object
    model: object


def fit_glm(train: pd.DataFrame, extra_numeric: Iterable[str] = ()) -> GLMBundle:
    from sklearn.linear_model import PoissonRegressor

    pre = glm_preprocessor(extra_numeric)
    x = pre.fit_transform(train)
    model = PoissonRegressor(alpha=GLM_ALPHA, solver="newton-cholesky").fit(
        x,
        train["Frequency"],
        sample_weight=train["Exposure"],
    )
    return GLMBundle(pre=pre, model=model)


def predict_glm(bundle: GLMBundle, frame: pd.DataFrame) -> np.ndarray:
    return np.asarray(bundle.model.predict(bundle.pre.transform(frame)), dtype=float)


def crossfit_m0_scores(train: pd.DataFrame, seed: int, n_splits: int = 5) -> np.ndarray:
    from sklearn.model_selection import KFold

    out = np.full(len(train), np.nan, dtype=float)
    kf = KFold(n_splits=n_splits, shuffle=True, random_state=(seed + 30000) % (2**32 - 1))
    for fit_idx, val_idx in kf.split(train):
        bundle = fit_glm(train.iloc[fit_idx])
        out[val_idx] = predict_glm(bundle, train.iloc[val_idx])
    if np.isnan(out).any() or np.any(out <= 0):
        raise RuntimeError("invalid OOF M0 risk scores")
    return out


def add_m2_interaction(
    train: pd.DataFrame,
    test: pd.DataFrame,
    full_m0: GLMBundle,
    seed: int,
) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    train2, test2 = train.copy(), test.copy()
    oof = crossfit_m0_scores(train2, seed)
    train_logrisk = np.log(oof)
    mean = float(np.mean(train_logrisk))
    sd = float(np.std(train_logrisk, ddof=0))
    if not np.isfinite(sd) or sd <= 0:
        raise RuntimeError("M0 risk-score SD must be positive")
    train_z = (train_logrisk - mean) / sd

    test_score = predict_glm(full_m0, test2)
    if np.any(test_score <= 0):
        raise RuntimeError("M0 test risk scores must be positive")
    test_z = (np.log(test_score) - mean) / sd

    train2["durationRiskInteraction"] = train2["logExposure"].to_numpy(float) * train_z
    test2["durationRiskInteraction"] = test2["logExposure"].to_numpy(float) * test_z
    return train2, test2, {
        "crossfit_folds": 5,
        "crossfit_random_state": int((seed + 30000) % (2**32 - 1)),
        "log_risk_mean": mean,
        "log_risk_sd": sd,
        "oof_sha256": hashlib.sha256(np.asarray(oof, dtype="<f8").tobytes()).hexdigest(),
    }


def hgb_frames(
    train: pd.DataFrame,
    other: pd.DataFrame,
    *,
    include_duration: bool,
) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    numeric = ["VehAge", "DrivAge", "BonusMalus", "logDensity"]
    if include_duration:
        numeric.append("logExposure")

    tr = pd.DataFrame(index=train.index)
    ot = pd.DataFrame(index=other.index)
    for c in numeric:
        tr[c] = train[c].astype(float)
        ot[c] = other[c].astype(float)

    categories: dict[str, list[str]] = {}
    for c in CAT_COLS:
        vals = sorted(pd.Series(train[c].astype(str).unique()).tolist())
        categories[c] = vals
        tr[c] = pd.Categorical(train[c].astype(str), categories=vals)
        ot[c] = pd.Categorical(other[c].astype(str), categories=vals)
    return tr, ot, categories


def hgb_model(config: dict):
    from sklearn.ensemble import HistGradientBoostingRegressor

    return HistGradientBoostingRegressor(
        loss="poisson",
        learning_rate=0.05,
        early_stopping=False,
        random_state=0,
        categorical_features="from_dtype",
        max_bins=255,
        **config,
    )


def select_hgb_capacity(train: pd.DataFrame, seed: int) -> dict:
    from sklearn.metrics import mean_poisson_deviance
    from sklearn.model_selection import train_test_split

    idx_fit, idx_val = train_test_split(
        np.arange(len(train)),
        test_size=0.20,
        random_state=(seed + 20000) % (2**32 - 1),
    )
    fit, val = train.iloc[idx_fit], train.iloc[idx_val]
    xfit, xval, _ = hgb_frames(fit, val, include_duration=False)
    scores = {}
    for cid, cfg in HGB_CONFIGS:
        model = hgb_model(cfg).fit(
            xfit,
            fit["Frequency"],
            sample_weight=fit["Exposure"],
        )
        pred = model.predict(xval)
        scores[cid] = float(
            mean_poisson_deviance(
                val["Frequency"],
                pred,
                sample_weight=val["Exposure"],
            )
        )
    selected = min((cid for cid, _ in HGB_CONFIGS), key=lambda cid: (scores[cid], cid))
    config = dict(dict(HGB_CONFIGS)[selected])
    return {
        "selected": selected,
        "config": config,
        "scores": scores,
        "inner_random_state": int((seed + 20000) % (2**32 - 1)),
    }


def fit_hgb_pair(
    train: pd.DataFrame,
    test: pd.DataFrame,
    selection: dict,
) -> tuple[np.ndarray, np.ndarray, dict]:
    xtr_a, xte_a, cats_a = hgb_frames(train, test, include_duration=False)
    xtr_b, xte_b, cats_b = hgb_frames(train, test, include_duration=True)
    if cats_a != cats_b:
        raise RuntimeError("M3a/M3b category state diverged")
    if "logExposure" in xtr_a.columns or "logExposure" not in xtr_b.columns:
        raise RuntimeError("duration feature boundary violated")
    cfg = selection["config"]
    a = hgb_model(cfg).fit(xtr_a, train["Frequency"], sample_weight=train["Exposure"])
    b = hgb_model(cfg).fit(xtr_b, train["Frequency"], sample_weight=train["Exposure"])
    return np.asarray(a.predict(xte_a), float), np.asarray(b.predict(xte_b), float), {
        "m3a_features": list(xtr_a.columns),
        "m3b_features": list(xtr_b.columns),
        "category_levels": {k: len(v) for k, v in cats_a.items()},
    }


def poisson_deviance_contrib(y: np.ndarray, pred: np.ndarray) -> np.ndarray:
    y = np.asarray(y, float)
    pred = np.asarray(pred, float)
    if np.any(y < 0) or np.any(pred <= 0):
        raise ValueError("Poisson target must be nonnegative and prediction positive")
    out = np.empty_like(y)
    zero = y == 0
    out[zero] = 2.0 * pred[zero]
    nz = ~zero
    out[nz] = 2.0 * (y[nz] * np.log(y[nz] / pred[nz]) - (y[nz] - pred[nz]))
    return out


def weighted_deviance(frame: pd.DataFrame, pred: np.ndarray) -> float:
    w = frame["Exposure"].to_numpy(float)
    d = poisson_deviance_contrib(frame["Frequency"].to_numpy(float), pred)
    return float(np.sum(w * d) / np.sum(w))


def calibration_ratio(frame: pd.DataFrame, pred: np.ndarray, mask: np.ndarray | None = None):
    if mask is None:
        mask = np.ones(len(frame), dtype=bool)
    w = frame["Exposure"].to_numpy(float)[mask]
    obs = float(np.sum(frame["ClaimNb"].to_numpy(float)[mask]))
    fitted = float(np.sum(w * np.asarray(pred, float)[mask]))
    return None if obs <= 0 else fitted / obs


def risk_cutpoints_and_groups(
    train_pred: np.ndarray,
    test_pred: np.ndarray,
) -> tuple[list[float], np.ndarray]:
    cuts = np.quantile(np.asarray(train_pred, float), [0.25, 0.50, 0.75], method="linear")
    if not np.all(np.diff(cuts) > 0):
        raise RuntimeError(f"non-distinct baseline-risk cutpoints: {cuts}")
    groups = np.searchsorted(cuts, np.asarray(test_pred, float), side="right")
    return [float(x) for x in cuts], groups.astype(int)


def calibration_views(frame: pd.DataFrame, pred: np.ndarray, risk_groups: np.ndarray) -> dict:
    exposure = frame["Exposure"].to_numpy(float)
    out = {"total": calibration_ratio(frame, pred), "duration": {}, "risk": {}, "duration_x_risk": {}}
    duration_masks = {}
    for lo, hi, label in DURATION_BANDS:
        mask = (exposure > lo) & (exposure <= hi)
        duration_masks[label] = mask
        out["duration"][label] = {
            "rows": int(mask.sum()),
            "observed_claims": float(frame["ClaimNb"].to_numpy(float)[mask].sum()),
            "po_ratio": calibration_ratio(frame, pred, mask),
        }
    for r in range(4):
        mask = risk_groups == r
        out["risk"][str(r + 1)] = {
            "rows": int(mask.sum()),
            "observed_claims": float(frame["ClaimNb"].to_numpy(float)[mask].sum()),
            "po_ratio": calibration_ratio(frame, pred, mask),
        }
    for dlabel, dmask in duration_masks.items():
        for r in range(4):
            mask = dmask & (risk_groups == r)
            key = f"{dlabel}|Q{r+1}"
            out["duration_x_risk"][key] = {
                "rows": int(mask.sum()),
                "observed_claims": float(frame["ClaimNb"].to_numpy(float)[mask].sum()),
                "po_ratio": calibration_ratio(frame, pred, mask),
            }
    return out


def paired_bootstrap(
    frame: pd.DataFrame,
    predictions: dict[str, np.ndarray],
    seed: int,
    n_boot: int = 1000,
) -> dict:
    y = frame["Frequency"].to_numpy(float)
    w = frame["Exposure"].to_numpy(float)
    names = []
    delta_cols = []
    for name, challenger, reference in CONTRASTS:
        names.append(name)
        dc = poisson_deviance_contrib(y, predictions[challenger])
        dr = poisson_deviance_contrib(y, predictions[reference])
        delta_cols.append(w * (dc - dr))
    delta = np.column_stack(delta_cols)

    rng = np.random.default_rng(seed ^ 0x5A17)
    p = np.full(len(frame), 1.0 / len(frame), dtype=float)
    samples = np.empty((n_boot, len(names)), dtype=float)
    for b in range(n_boot):
        counts = rng.multinomial(len(frame), p)
        denom = float(counts @ w)
        samples[b] = (counts @ delta) / denom
    result = {}
    for j, name in enumerate(names):
        result[name] = {
            "mean": float(samples[:, j].mean()),
            "q025": float(np.quantile(samples[:, j], 0.025)),
            "q975": float(np.quantile(samples[:, j], 0.975)),
        }
    return result


def one_split(d: pd.DataFrame, seed: int, *, n_boot: int = 1000) -> dict:
    from sklearn.model_selection import train_test_split

    fit_idx, test_idx = train_test_split(
        np.arange(len(d)),
        test_size=0.25,
        random_state=seed,
    )
    train, test = d.iloc[fit_idx].copy(), d.iloc[test_idx].copy()

    m0 = fit_glm(train)
    m0_train_pred = predict_glm(m0, train)
    p0 = predict_glm(m0, test)

    m1 = fit_glm(train, ["logExposure"])
    p1 = predict_glm(m1, test)

    train_m2, test_m2, nesting = add_m2_interaction(train, test, m0, seed)
    m2 = fit_glm(train_m2, ["logExposure", "durationRiskInteraction"])
    p2 = predict_glm(m2, test_m2)

    hgb_selection = select_hgb_capacity(train, seed)
    p3a, p3b, hgb_receipt = fit_hgb_pair(train, test, hgb_selection)

    predictions = {"M0": p0, "M1": p1, "M2": p2, "M3a": p3a, "M3b": p3b}
    cuts, groups = risk_cutpoints_and_groups(m0_train_pred, p0)

    scores = {name: weighted_deviance(test, pred) for name, pred in predictions.items()}
    calibrations = {name: calibration_views(test, pred, groups) for name, pred in predictions.items()}
    contrasts = {}
    for cname, challenger, reference in CONTRASTS:
        diff = scores[challenger] - scores[reference]
        rel = (scores[reference] - scores[challenger]) / scores[reference]
        contrasts[cname] = {"deviance_difference": diff, "relative_improvement": rel}

    return {
        "seed": int(seed),
        "train_rows": int(len(train)),
        "test_rows": int(len(test)),
        "train_exposure": float(train["Exposure"].sum()),
        "test_exposure": float(test["Exposure"].sum()),
        "train_claims": float(train["ClaimNb"].sum()),
        "test_claims": float(test["ClaimNb"].sum()),
        "risk_cutpoints": cuts,
        "m2_nesting": nesting,
        "hgb_selection": hgb_selection,
        "hgb_feature_receipt": hgb_receipt,
        "scores": scores,
        "contrasts": contrasts,
        "calibration": calibrations,
        "paired_bootstrap": paired_bootstrap(test, predictions, seed, n_boot=n_boot),
    }


def runtime_receipt() -> dict:
    import scipy
    import sklearn

    return {
        "python": sys.version,
        "platform": platform.platform(),
        "numpy": np.__version__,
        "pandas": pd.__version__,
        "scipy": scipy.__version__,
        "sklearn": sklearn.__version__,
    }


def data_receipt(d: pd.DataFrame, cap_claimnb: bool) -> dict:
    return {
        "rows": int(len(d)),
        "unique_policy_ids": bool(not d["IDpol"].duplicated().any()),
        "exposure_sum": float(d["Exposure"].sum()),
        "claim_count": float(d["ClaimNb"].sum()),
        "policies_claimnb_gt4_after_prepare": int((d["ClaimNb"] > 4).sum()),
        "cap_claimnb": bool(cap_claimnb),
    }


def run_target(*, cap_claimnb: bool, n_boot: int = 1000) -> dict:
    raw, meta = load_openml_frequency()
    d = prepare_frequency(raw, cap_claimnb=cap_claimnb)
    results = [one_split(d, seed, n_boot=n_boot) for seed in OUTER_SEEDS]
    return {
        "experiment": "underwriting-fremtpl2-duration-risk-meanclass-v0",
        "classification": "MODERN_MODEL_RESEARCH",
        "question_fingerprint": QUESTION_FINGERPRINT,
        "question_sha256": QUESTION_SHA256,
        "outer_seeds": list(OUTER_SEEDS),
        "target": "freMTPL2freq.ClaimNb",
        "openml": meta,
        "data": data_receipt(d, cap_claimnb),
        "runtime": runtime_receipt(),
        "hgb_contract": {
            "learning_rate": 0.05,
            "early_stopping": False,
            "random_state": 0,
            "categorical_features": "from_dtype",
            "max_bins": 255,
            "capacity_grid": [{"id": cid, **cfg} for cid, cfg in HGB_CONFIGS],
            "selection": "M3a inner-validation deviance; same selected capacity reused for M3b",
        },
        "results": results,
        "nextgen_promotion": "NONE",
    }


def synthetic_fixture(n: int = 5000, seed: int = 123) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    exposure = rng.uniform(0.05, 1.0, n)
    risk = rng.normal(0, 0.6, n)
    veh_age = rng.integers(0, 20, n)
    driv_age = rng.integers(18, 85, n)
    bonus = rng.uniform(50, 150, n)
    density = np.exp(rng.normal(5.5, 1.0, n))
    area = rng.choice(list("ABCDEF"), n)
    brand = rng.choice(["B1", "B2", "B3", "B4"], n)
    power = rng.choice(["4", "5", "6", "7"], n)
    gas = rng.choice(["Diesel", "Regular"], n)
    region = rng.choice(["R1", "R2", "R3"], n)
    log_rate = -3.2 + risk + 0.18 * np.log(exposure) + 0.20 * np.log(exposure) * risk
    count = rng.poisson(exposure * np.exp(log_rate))
    raw = pd.DataFrame(
        {
            "IDpol": np.arange(1, n + 1),
            "ClaimNb": count,
            "Exposure": exposure,
            "Area": area,
            "VehPower": power,
            "VehAge": veh_age,
            "DrivAge": driv_age,
            "BonusMalus": bonus,
            "VehBrand": brand,
            "VehGas": gas,
            "Density": density,
            "Region": region,
        }
    )
    return prepare_frequency(raw, cap_claimnb=False)


def check_contract() -> dict:
    expected = hashlib.sha256(QUESTION_FINGERPRINT.encode()).hexdigest()
    if expected != QUESTION_SHA256:
        raise RuntimeError("question fingerprint digest mismatch")
    words = [
        int.from_bytes(bytes.fromhex(QUESTION_SHA256)[i * 4 : (i + 1) * 4], "big")
        for i in range(3)
    ]
    if tuple(words) != OUTER_SEEDS:
        raise RuntimeError(f"outer-seed derivation mismatch: {words}")

    d = synthetic_fixture()
    r = one_split(d, OUTER_SEEDS[2], n_boot=20)
    if "logExposure" in r["hgb_feature_receipt"]["m3a_features"]:
        raise RuntimeError("M3a leaked duration")
    if "logExposure" not in r["hgb_feature_receipt"]["m3b_features"]:
        raise RuntimeError("M3b missing duration")
    if r["m2_nesting"]["crossfit_folds"] != 5:
        raise RuntimeError("M2 nesting contract broken")
    return {
        "pass": True,
        "question_sha256": QUESTION_SHA256,
        "outer_seeds": list(OUTER_SEEDS),
        "selected_hgb": r["hgb_selection"]["selected"],
        "m3a_features": r["hgb_feature_receipt"]["m3a_features"],
        "m3b_features": r["hgb_feature_receipt"]["m3b_features"],
        "scores": r["scores"],
    }


def canonical_json(obj: dict) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), allow_nan=False)


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--output", type=Path)
    p.add_argument("--check", action="store_true")
    p.add_argument("--no-count-cap", action="store_true")
    p.add_argument("--bootstrap", type=int, default=1000)
    args = p.parse_args()

    if args.check:
        result = check_contract()
    else:
        result = run_target(cap_claimnb=not args.no_count_cap, n_boot=args.bootstrap)

    text = canonical_json(result)
    if args.output:
        args.output.write_text(text + "\n", encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
