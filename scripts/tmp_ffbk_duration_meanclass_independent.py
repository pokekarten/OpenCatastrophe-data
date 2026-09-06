#!/usr/bin/env python3
"""Temporary independent execution of the frozen FFBK freMTPL2 duration mean-class contract.

This is an execution-surface replica, not production OpenCatastrophe code and not a copy
of the private FFBK implementation. The scientific contract is identified by its frozen
question SHA. Results are written as a machine-readable receipt for later FFBK review.
"""
from __future__ import annotations

import hashlib
import json
import platform
import sys
import urllib.request
from pathlib import Path

import numpy as np
import pandas as pd

FREQ_ID = 41214
FREQ_VERSION = 1
FREQ_MD5 = "f8875568bf0ca622929105197e2db613"
QUESTION_FINGERPRINT = "underwriting/fremtpl2/duration-risk/meanclass/m0-m1-m2-m3a-m3b/v1"
QUESTION_SHA256 = "9fd5d48fef5528d1112401df64e8c74b881a413f0d92ac518d2a14786d312ed8"
OUTER_SEEDS = (2681590927, 4015335633, 287572447)
GLM_ALPHA = 1e-4
OUT = Path("tmp_ffbk_duration_meanclass_result.json")
CAT_COLS = ("VehBrand", "VehPower", "VehGas", "Region", "Area")
DURATION_BANDS = (
    (0.0, 0.25, "(0,.25]"),
    (0.25, 0.50, "(.25,.50]"),
    (0.50, 0.75, "(.50,.75]"),
    (0.75, 1.00, "(.75,1]"),
)
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


def openml_meta() -> dict:
    url = f"https://www.openml.org/api/v1/json/data/{FREQ_ID}"
    with urllib.request.urlopen(url, timeout=60) as r:
        d = json.loads(r.read().decode())["data_set_description"]
    meta = {
        "data_id": int(d["id"]),
        "name": d.get("name"),
        "version": int(d["version"]),
        "md5_checksum": d.get("md5_checksum"),
        "status": d.get("status"),
        "url": d.get("url"),
        "parquet_url": d.get("parquet_url"),
    }
    if (meta["data_id"], meta["version"], meta["md5_checksum"]) != (FREQ_ID, FREQ_VERSION, FREQ_MD5):
        raise RuntimeError(f"OpenML identity mismatch: {meta}")
    return meta


def load_data(*, cap_claimnb: bool = True) -> tuple[pd.DataFrame, dict]:
    from sklearn.datasets import fetch_openml

    meta = openml_meta()
    d = fetch_openml(data_id=FREQ_ID, as_frame=True).data.copy()
    for c in d.columns:
        if d[c].dtype == object or isinstance(d[c].dtype, pd.CategoricalDtype):
            d[c] = d[c].astype(str).str.strip("'")
    d["IDpol"] = d["IDpol"].astype("int64")
    if d["IDpol"].duplicated().any():
        raise RuntimeError("IDpol must be unique")
    d["ClaimNb"] = d["ClaimNb"].astype(float)
    if cap_claimnb:
        d["ClaimNb"] = d["ClaimNb"].clip(upper=4)
    d["Exposure"] = d["Exposure"].astype(float).clip(upper=1)
    if not (d["Exposure"] > 0).all():
        raise RuntimeError("Exposure must be strictly positive")
    d["Frequency"] = d["ClaimNb"] / d["Exposure"]
    d["logExposure"] = np.log(d["Exposure"])
    d["logDensity"] = np.log(d["Density"].astype(float))
    return d.reset_index(drop=True), meta


def glm_preprocessor(extra_numeric=()):
    from sklearn.compose import ColumnTransformer
    from sklearn.pipeline import make_pipeline
    from sklearn.preprocessing import FunctionTransformer, KBinsDiscretizer, OneHotEncoder, StandardScaler

    transforms = [
        ("bin", KBinsDiscretizer(n_bins=10, quantile_method="averaged_inverted_cdf", random_state=0), ["VehAge", "DrivAge"]),
        ("cat", OneHotEncoder(handle_unknown="ignore"), ["VehBrand", "VehPower", "VehGas", "Region", "Area"]),
        ("num", "passthrough", ["BonusMalus"]),
        ("density", make_pipeline(FunctionTransformer(func=np.log), StandardScaler()), ["Density"]),
    ]
    extra_numeric = list(extra_numeric)
    if extra_numeric:
        transforms.append(("extra", StandardScaler(), extra_numeric))
    return ColumnTransformer(transforms)


def fit_glm(train: pd.DataFrame, extra_numeric=()):
    from sklearn.linear_model import PoissonRegressor

    pre = glm_preprocessor(extra_numeric)
    x = pre.fit_transform(train)
    model = PoissonRegressor(alpha=GLM_ALPHA, solver="newton-cholesky").fit(
        x, train["Frequency"], sample_weight=train["Exposure"]
    )
    return pre, model


def pred_glm(bundle, frame: pd.DataFrame) -> np.ndarray:
    pre, model = bundle
    return np.asarray(model.predict(pre.transform(frame)), dtype=float)


def crossfit_m0(train: pd.DataFrame, seed: int) -> np.ndarray:
    from sklearn.model_selection import KFold

    out = np.full(len(train), np.nan)
    rs = (seed + 30000) % (2**32 - 1)
    for fit_idx, val_idx in KFold(n_splits=5, shuffle=True, random_state=rs).split(train):
        m = fit_glm(train.iloc[fit_idx])
        out[val_idx] = pred_glm(m, train.iloc[val_idx])
    if np.isnan(out).any() or np.any(out <= 0):
        raise RuntimeError("invalid cross-fitted M0 scores")
    return out


def add_m2_state(train: pd.DataFrame, test: pd.DataFrame, m0, seed: int):
    tr = train.copy()
    te = test.copy()
    oof = crossfit_m0(tr, seed)
    lr = np.log(oof)
    mean = float(lr.mean())
    sd = float(lr.std(ddof=0))
    if not np.isfinite(sd) or sd <= 0:
        raise RuntimeError("M0 score SD invalid")
    ztr = (lr - mean) / sd
    pte = pred_glm(m0, te)
    zte = (np.log(pte) - mean) / sd
    tr["durationRiskInteraction"] = tr["logExposure"].to_numpy(float) * ztr
    te["durationRiskInteraction"] = te["logExposure"].to_numpy(float) * zte
    return tr, te, {
        "crossfit_folds": 5,
        "crossfit_random_state": int((seed + 30000) % (2**32 - 1)),
        "log_risk_mean": mean,
        "log_risk_sd": sd,
        "oof_sha256": hashlib.sha256(np.asarray(oof, dtype="<f8").tobytes()).hexdigest(),
    }


def hgb_frames(train: pd.DataFrame, other: pd.DataFrame, *, duration: bool):
    nums = ["VehAge", "DrivAge", "BonusMalus", "logDensity"] + (["logExposure"] if duration else [])
    tr = pd.DataFrame(index=train.index)
    ot = pd.DataFrame(index=other.index)
    for c in nums:
        tr[c] = train[c].astype(float)
        ot[c] = other[c].astype(float)
    levels = {}
    for c in CAT_COLS:
        cats = sorted(pd.Series(train[c].astype(str).unique()).tolist())
        levels[c] = cats
        tr[c] = pd.Categorical(train[c].astype(str), categories=cats)
        ot[c] = pd.Categorical(other[c].astype(str), categories=cats)
    return tr, ot, levels


def hgb(config: dict):
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


def choose_hgb(train: pd.DataFrame, seed: int) -> dict:
    from sklearn.metrics import mean_poisson_deviance
    from sklearn.model_selection import train_test_split

    fit_idx, val_idx = train_test_split(
        np.arange(len(train)), test_size=0.20, random_state=(seed + 20000) % (2**32 - 1)
    )
    fit, val = train.iloc[fit_idx], train.iloc[val_idx]
    xfit, xval, _ = hgb_frames(fit, val, duration=False)
    scores = {}
    for cid, cfg in HGB_CONFIGS:
        model = hgb(cfg).fit(xfit, fit["Frequency"], sample_weight=fit["Exposure"])
        scores[cid] = float(mean_poisson_deviance(
            val["Frequency"], model.predict(xval), sample_weight=val["Exposure"]
        ))
    chosen = min((cid for cid, _ in HGB_CONFIGS), key=lambda c: (scores[c], c))
    return {
        "selected": chosen,
        "config": dict(dict(HGB_CONFIGS)[chosen]),
        "scores": scores,
        "inner_random_state": int((seed + 20000) % (2**32 - 1)),
    }


def fit_hgb_pair(train: pd.DataFrame, test: pd.DataFrame, selection: dict):
    xa, xat, levels_a = hgb_frames(train, test, duration=False)
    xb, xbt, levels_b = hgb_frames(train, test, duration=True)
    if levels_a != levels_b or "logExposure" in xa.columns or "logExposure" not in xb.columns:
        raise RuntimeError("M3a/M3b feature boundary violated")
    ma = hgb(selection["config"]).fit(xa, train["Frequency"], sample_weight=train["Exposure"])
    mb = hgb(selection["config"]).fit(xb, train["Frequency"], sample_weight=train["Exposure"])
    return np.asarray(ma.predict(xat), float), np.asarray(mb.predict(xbt), float), {
        "m3a_features": list(xa.columns),
        "m3b_features": list(xb.columns),
        "category_levels": {k: len(v) for k, v in levels_a.items()},
    }


def dev_contrib(y: np.ndarray, pred: np.ndarray) -> np.ndarray:
    y = np.asarray(y, float)
    pred = np.asarray(pred, float)
    z = y == 0
    out = np.empty_like(y)
    out[z] = 2 * pred[z]
    nz = ~z
    out[nz] = 2 * (y[nz] * np.log(y[nz] / pred[nz]) - (y[nz] - pred[nz]))
    return out


def score(frame: pd.DataFrame, pred: np.ndarray) -> float:
    w = frame["Exposure"].to_numpy(float)
    return float(np.sum(w * dev_contrib(frame["Frequency"].to_numpy(float), pred)) / w.sum())


def po_ratio(frame: pd.DataFrame, pred: np.ndarray, mask: np.ndarray) -> float | None:
    obs = float(frame["ClaimNb"].to_numpy(float)[mask].sum())
    fitted = float(np.sum(frame["Exposure"].to_numpy(float)[mask] * pred[mask]))
    return None if obs <= 0 else fitted / obs


def risk_groups(train_pred: np.ndarray, test_pred: np.ndarray):
    cuts = np.quantile(train_pred, [0.25, 0.50, 0.75], method="linear")
    if not np.all(np.diff(cuts) > 0):
        raise RuntimeError("risk cutpoints not distinct")
    return [float(x) for x in cuts], np.searchsorted(cuts, test_pred, side="right")


def calibration(frame: pd.DataFrame, pred: np.ndarray, groups: np.ndarray) -> dict:
    exposure = frame["Exposure"].to_numpy(float)
    allmask = np.ones(len(frame), dtype=bool)
    out = {"total": po_ratio(frame, pred, allmask), "duration": {}, "risk": {}, "duration_x_risk": {}}
    duration_masks = {}
    for lo, hi, label in DURATION_BANDS:
        m = (exposure > lo) & (exposure <= hi)
        duration_masks[label] = m
        out["duration"][label] = {"rows": int(m.sum()), "observed_claims": float(frame["ClaimNb"].to_numpy(float)[m].sum()), "po_ratio": po_ratio(frame, pred, m)}
    for r in range(4):
        m = groups == r
        out["risk"][str(r + 1)] = {"rows": int(m.sum()), "observed_claims": float(frame["ClaimNb"].to_numpy(float)[m].sum()), "po_ratio": po_ratio(frame, pred, m)}
    for label, dm in duration_masks.items():
        for r in range(4):
            m = dm & (groups == r)
            out["duration_x_risk"][f"{label}|Q{r+1}"] = {"rows": int(m.sum()), "observed_claims": float(frame["ClaimNb"].to_numpy(float)[m].sum()), "po_ratio": po_ratio(frame, pred, m)}
    return out


def bootstrap(frame: pd.DataFrame, predictions: dict[str, np.ndarray], seed: int, reps: int = 1000) -> dict:
    y = frame["Frequency"].to_numpy(float)
    w = frame["Exposure"].to_numpy(float)
    deltas = []
    names = []
    for cname, challenger, reference in CONTRASTS:
        names.append(cname)
        deltas.append(w * (dev_contrib(y, predictions[challenger]) - dev_contrib(y, predictions[reference])))
    delta = np.column_stack(deltas)
    rng = np.random.default_rng(seed ^ 0x5A17)
    p = np.full(len(frame), 1.0 / len(frame))
    samples = np.empty((reps, len(names)))
    for b in range(reps):
        counts = rng.multinomial(len(frame), p)
        samples[b] = (counts @ delta) / float(counts @ w)
    return {name: {
        "mean": float(samples[:, j].mean()),
        "q025": float(np.quantile(samples[:, j], 0.025)),
        "q975": float(np.quantile(samples[:, j], 0.975)),
    } for j, name in enumerate(names)}


def run_split(d: pd.DataFrame, seed: int) -> dict:
    from sklearn.model_selection import train_test_split

    tr_idx, te_idx = train_test_split(np.arange(len(d)), test_size=0.25, random_state=seed)
    train, test = d.iloc[tr_idx].copy(), d.iloc[te_idx].copy()

    m0 = fit_glm(train)
    p0_tr = pred_glm(m0, train)
    p0 = pred_glm(m0, test)
    m1 = fit_glm(train, ["logExposure"])
    p1 = pred_glm(m1, test)
    tr2, te2, nesting = add_m2_state(train, test, m0, seed)
    m2 = fit_glm(tr2, ["logExposure", "durationRiskInteraction"])
    p2 = pred_glm(m2, te2)
    selection = choose_hgb(train, seed)
    p3a, p3b, feature_receipt = fit_hgb_pair(train, test, selection)

    predictions = {"M0": p0, "M1": p1, "M2": p2, "M3a": p3a, "M3b": p3b}
    cuts, groups = risk_groups(p0_tr, p0)
    scores = {k: score(test, v) for k, v in predictions.items()}
    contrasts = {}
    for cname, challenger, reference in CONTRASTS:
        diff = scores[challenger] - scores[reference]
        contrasts[cname] = {
            "deviance_difference": diff,
            "relative_improvement": (scores[reference] - scores[challenger]) / scores[reference],
        }
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
        "hgb_selection": selection,
        "hgb_feature_receipt": feature_receipt,
        "scores": scores,
        "contrasts": contrasts,
        "calibration": {k: calibration(test, v, groups) for k, v in predictions.items()},
        "paired_bootstrap": bootstrap(test, predictions, seed, 1000),
    }


def runtime() -> dict:
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


def main() -> None:
    if hashlib.sha256(QUESTION_FINGERPRINT.encode()).hexdigest() != QUESTION_SHA256:
        raise RuntimeError("question SHA mismatch")
    d, meta = load_data(cap_claimnb=True)
    results = [run_split(d, s) for s in OUTER_SEEDS]
    payload = {
        "experiment": "independent-underwriting-fremtpl2-duration-risk-meanclass-v0",
        "classification": "INDEPENDENT_REPLICATION / MODERN_MODEL_RESEARCH",
        "question_fingerprint": QUESTION_FINGERPRINT,
        "question_sha256": QUESTION_SHA256,
        "openml": meta,
        "data": {
            "rows": int(len(d)),
            "unique_policy_ids": bool(not d["IDpol"].duplicated().any()),
            "exposure_sum": float(d["Exposure"].sum()),
            "claim_count": float(d["ClaimNb"].sum()),
            "cap_claimnb": True,
            "policies_claimnb_gt4_after_prepare": int((d["ClaimNb"] > 4).sum()),
        },
        "runtime": runtime(),
        "outer_seeds": list(OUTER_SEEDS),
        "protocol": {
            "target": "standalone freMTPL2freq.ClaimNb",
            "outer_test_fraction": 0.25,
            "bootstrap_reps": 1000,
            "glm_alpha": GLM_ALPHA,
            "hgb_learning_rate": 0.05,
            "hgb_early_stopping": False,
            "hgb_random_state": 0,
            "hgb_max_bins": 255,
            "hgb_capacity_grid": [{"id": cid, **cfg} for cid, cfg in HGB_CONFIGS],
        },
        "results": results,
        "nextgen_promotion": "NONE",
    }
    core = json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    payload["result_payload_sha256_without_receipt"] = hashlib.sha256(core).hexdigest()
    OUT.write_text(json.dumps(payload, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")
    print(json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False))


if __name__ == "__main__":
    main()
