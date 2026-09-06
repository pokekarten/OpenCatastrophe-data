#!/usr/bin/env python3
"""Execute the preregistered Norwegian norauto duration-transfer experiment.

Scientific contract: pokekarten/FFBK PR #1415, prereg commit
7c8939be4e861eafda011cfd9bf65a11882d241a.

The runner downloads only the prospectively pinned target bytes, validates fail-closed,
and writes result/receipt artifacts. It does not mutate source data.
"""
from __future__ import annotations

import hashlib
import json
import math
import platform
import sys
import urllib.request
from pathlib import Path

import numpy as np
import pandas as pd
import pyreadr
import scipy
import sklearn
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.linear_model import PoissonRegressor
from sklearn.model_selection import KFold, train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

SOURCE_COMMIT = "ef06f44b8669908925b5a590c8a2313723cf504c"
SOURCE_GIT_BLOB = "5e3a047ebf8f2834b021af7a68b2855ce2ebdbd7"
SOURCE_URL = (
    "https://raw.githubusercontent.com/dutangc/CASdatasets/"
    + SOURCE_COMMIT
    + "/data/norauto.rda"
)
QUESTION_FINGERPRINT = "underwriting/norauto-norway/duration-risk/meanclass/m0-m1-m2-m3a-m3b/transfer-v1"
QUESTION_SHA256 = "64f0efd9b98cfdc4086a318d7d5170b80e65d5503e839624a17ddaa7e745f4a9"
FFBK_PREREG_COMMIT = "7c8939be4e861eafda011cfd9bf65a11882d241a"
OUTER_SEEDS = [1693511641, 3113024964, 141177229]
CAT_COLS = ["DistLimit", "GeoRegion"]
BASE_NUM_COLS = ["Male", "Young"]
CAPACITY_GRID = [
    ("H1", dict(max_leaf_nodes=15, min_samples_leaf=100, max_iter=150, l2_regularization=1.0)),
    ("H2", dict(max_leaf_nodes=31, min_samples_leaf=100, max_iter=150, l2_regularization=1.0)),
    ("H3", dict(max_leaf_nodes=31, min_samples_leaf=50, max_iter=200, l2_regularization=1.0)),
    ("H4", dict(max_leaf_nodes=63, min_samples_leaf=100, max_iter=200, l2_regularization=1.0)),
]
CONTRASTS = [
    ("M1_minus_M0", "M1", "M0"),
    ("M2_minus_M1", "M2", "M1"),
    ("M3a_minus_M0", "M3a", "M0"),
    ("M3b_minus_M3a", "M3b", "M3a"),
    ("M3b_minus_M2", "M3b", "M2"),
]


def download_source(path: Path) -> bytes:
    with urllib.request.urlopen(SOURCE_URL, timeout=60) as response:
        data = response.read()
    path.write_bytes(data)
    return data


def load_source(path: Path) -> tuple[pd.DataFrame, str]:
    objects = pyreadr.read_r(str(path))
    if len(objects) != 1:
        raise RuntimeError(f"expected exactly one R object, got {list(objects)}")
    object_name, df = next(iter(objects.items()))
    if not isinstance(df, pd.DataFrame):
        raise RuntimeError(f"R object {object_name!r} is not a data frame")
    return df, str(object_name)


def validate_data(df: pd.DataFrame) -> None:
    expected = {"Male", "Young", "DistLimit", "GeoRegion", "Expo", "ClaimAmount", "NbClaim"}
    if set(df.columns) != expected:
        raise RuntimeError(f"schema mismatch: {list(df.columns)}")
    if len(df) != 183999:
        raise RuntimeError(f"row count mismatch: {len(df)} != 183999")
    for col in ["Male", "Young", "Expo", "NbClaim"]:
        x = pd.to_numeric(df[col], errors="coerce").to_numpy(dtype=float)
        if not np.all(np.isfinite(x)):
            raise RuntimeError(f"non-finite {col}")
    exposure = df["Expo"].to_numpy(dtype=float)
    claims = df["NbClaim"].to_numpy(dtype=float)
    if np.any(exposure <= 0) or np.any(exposure > 1):
        bad = np.where((exposure <= 0) | (exposure > 1))[0][:10].tolist()
        raise RuntimeError(f"Expo outside (0,1] at rows {bad}")
    if np.any(claims < 0) or np.any(np.abs(claims - np.rint(claims)) > 1e-12):
        raise RuntimeError("negative or non-integral NbClaim")
    for col in ["Male", "Young"]:
        vals = set(np.unique(df[col].to_numpy(dtype=float)).tolist())
        if not vals.issubset({0.0, 1.0}):
            raise RuntimeError(f"unexpected {col} values: {sorted(vals)[:20]}")
    for col in CAT_COLS:
        if df[col].isna().any():
            raise RuntimeError(f"missing categorical state in {col}")


def annualized_targets(df: pd.DataFrame):
    w = df["Expo"].to_numpy(dtype=float)
    n = df["NbClaim"].to_numpy(dtype=float)
    return n / w, w, n


def make_glm(extra_numeric: list[str] | None = None) -> Pipeline:
    extra_numeric = extra_numeric or []
    prep = ColumnTransformer(
        transformers=[
            ("cat", OneHotEncoder(handle_unknown="ignore"), CAT_COLS),
            ("num", "passthrough", BASE_NUM_COLS + extra_numeric),
        ],
        remainder="drop",
    )
    model = PoissonRegressor(alpha=1e-4, solver="newton-cholesky", max_iter=1000)
    return Pipeline([("prep", prep), ("model", model)])


def fit_glm(train: pd.DataFrame, extra_numeric: list[str] | None = None) -> Pipeline:
    y, w, _ = annualized_targets(train)
    pipe = make_glm(extra_numeric)
    pipe.fit(train, y, model__sample_weight=w)
    return pipe


def add_logw(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["logExposure"] = np.log(out["Expo"].to_numpy(dtype=float))
    return out


def prepare_hgb(train: pd.DataFrame, other: pd.DataFrame, include_logw: bool):
    cols = BASE_NUM_COLS + CAT_COLS + (["logExposure"] if include_logw else [])
    a = train[cols].copy()
    b = other[cols].copy()
    for c in CAT_COLS:
        categories = sorted(pd.Series(a[c]).dropna().unique().tolist(), key=lambda x: str(x))
        dtype = pd.CategoricalDtype(categories=categories, ordered=False)
        a[c] = a[c].astype(dtype)
        b[c] = b[c].astype(dtype)
    return a, b


def fit_hgb(train: pd.DataFrame, params: dict, include_logw: bool):
    y, w, _ = annualized_targets(train)
    xtrain, _ = prepare_hgb(train, train.iloc[:0].copy(), include_logw)
    model = HistGradientBoostingRegressor(
        loss="poisson", learning_rate=0.05, early_stopping=False,
        random_state=0, categorical_features="from_dtype", **params,
    )
    model.fit(xtrain, y, sample_weight=w)
    return model


def predict_hgb(model, train_reference: pd.DataFrame, test: pd.DataFrame, include_logw: bool):
    _, xtest = prepare_hgb(train_reference, test, include_logw)
    return np.maximum(model.predict(xtest), 1e-12)


def deviance_contrib(y: np.ndarray, mu: np.ndarray) -> np.ndarray:
    mu = np.maximum(mu, 1e-12)
    out = np.empty_like(y, dtype=float)
    zero = y == 0
    out[zero] = 2.0 * mu[zero]
    nz = ~zero
    out[nz] = 2.0 * (y[nz] * np.log(y[nz] / mu[nz]) - y[nz] + mu[nz])
    return out


def weighted_mean(values: np.ndarray, w: np.ndarray) -> float:
    return float(np.sum(values * w) / np.sum(w))


def po_dev(y: np.ndarray, pred: np.ndarray, w: np.ndarray) -> float:
    return weighted_mean(deviance_contrib(y, pred), w)


def ratios_by_group(n: np.ndarray, pred_count: np.ndarray, group: np.ndarray, ngroups: int):
    out = []
    for g in range(ngroups):
        mask = group == g
        obs = float(n[mask].sum())
        pred = float(pred_count[mask].sum())
        out.append({"group": int(g), "rows": int(mask.sum()), "observed": obs,
                    "predicted": pred, "po": None if obs <= 0 else pred / obs})
    return out


def ratios_cross(n, pred_count, duration_group, risk_group):
    out = []
    for d in range(4):
        for r in range(4):
            mask = (duration_group == d) & (risk_group == r)
            obs = float(n[mask].sum())
            pred = float(pred_count[mask].sum())
            out.append({"duration_group": d, "risk_group": r, "rows": int(mask.sum()),
                        "observed": obs, "predicted": pred,
                        "po": None if obs <= 0 else pred / obs})
    return out


def max_calibration_worsening(challenger, reference) -> float:
    worst = -math.inf
    for view in ["duration", "risk"]:
        for ci, ri in zip(challenger[view], reference[view]):
            if ci["po"] is None or ri["po"] is None:
                continue
            worst = max(worst, abs(ci["po"] - 1.0) - abs(ri["po"] - 1.0))
    return float(worst if math.isfinite(worst) else 0.0)


def bootstrap_intervals(diff_contribs: dict[str, np.ndarray], w: np.ndarray, seed: int):
    rng = np.random.default_rng(seed)
    n = len(w)
    vals = {k: [] for k in diff_contribs}
    remaining = 1000
    while remaining:
        m = min(20, remaining)
        idx = rng.integers(0, n, size=(m, n), dtype=np.int32)
        bw = w[idx]
        den = bw.sum(axis=1)
        for k, diff in diff_contribs.items():
            vals[k].extend(((bw * diff[idx]).sum(axis=1) / den).tolist())
        remaining -= m
    return {k: {"q025": float(np.quantile(v, 0.025)),
                "q500": float(np.quantile(v, 0.500)),
                "q975": float(np.quantile(v, 0.975))} for k, v in vals.items()}


def run_split(df: pd.DataFrame, outer_seed: int):
    all_idx = np.arange(len(df))
    train_idx, test_idx = train_test_split(all_idx, test_size=0.25,
                                            random_state=outer_seed, shuffle=True)
    train = add_logw(df.iloc[train_idx].reset_index(drop=True))
    test = add_logw(df.iloc[test_idx].reset_index(drop=True))
    _, wtr, ntr = annualized_targets(train)
    yte, wte, nte = annualized_targets(test)

    m0 = fit_glm(train)
    p0_train = np.maximum(m0.predict(train), 1e-12)
    p0_test = np.maximum(m0.predict(test), 1e-12)

    m1 = fit_glm(train, ["logExposure"])
    p1_test = np.maximum(m1.predict(test), 1e-12)

    oof = np.empty(len(train), dtype=float)
    kf = KFold(n_splits=5, shuffle=True, random_state=outer_seed + 10000)
    for fit_pos, val_pos in kf.split(np.arange(len(train))):
        fm0 = fit_glm(train.iloc[fit_pos])
        oof[val_pos] = np.maximum(fm0.predict(train.iloc[val_pos]), 1e-12)
    log_oof = np.log(oof)
    risk_mean = float(log_oof.mean())
    risk_sd = float(log_oof.std(ddof=0))
    if not np.isfinite(risk_sd) or risk_sd <= 0:
        raise RuntimeError("M2 OOF risk SD is non-positive")
    train_m2 = train.copy(); test_m2 = test.copy()
    train_m2["durationRiskInteraction"] = train_m2["logExposure"] * ((log_oof-risk_mean)/risk_sd)
    test_m2["durationRiskInteraction"] = test_m2["logExposure"] * ((np.log(p0_test)-risk_mean)/risk_sd)
    m2 = fit_glm(train_m2, ["logExposure", "durationRiskInteraction"])
    p2_test = np.maximum(m2.predict(test_m2), 1e-12)

    inner_fit_pos, inner_val_pos = train_test_split(
        np.arange(len(train)), test_size=0.20, random_state=outer_seed + 20000, shuffle=True)
    inner_train = train.iloc[inner_fit_pos]; inner_val = train.iloc[inner_val_pos]
    yiv, wiv, _ = annualized_targets(inner_val)
    capacity_scores = []
    for cid, params in CAPACITY_GRID:
        model = fit_hgb(inner_train, params, include_logw=False)
        pred = predict_hgb(model, inner_train, inner_val, include_logw=False)
        capacity_scores.append({"id": cid, "deviance": po_dev(yiv, pred, wiv), **params})
    order = [x[0] for x in CAPACITY_GRID]
    winner = min(capacity_scores, key=lambda x: (x["deviance"], order.index(x["id"])))
    win_params = next(params for cid, params in CAPACITY_GRID if cid == winner["id"])

    m3a = fit_hgb(train, win_params, include_logw=False)
    p3a_test = predict_hgb(m3a, train, test, include_logw=False)
    m3b = fit_hgb(train, win_params, include_logw=True)
    p3b_test = predict_hgb(m3b, train, test, include_logw=True)

    preds = {"M0": p0_test, "M1": p1_test, "M2": p2_test, "M3a": p3a_test, "M3b": p3b_test}
    devc = {k: deviance_contrib(yte, v) for k, v in preds.items()}
    scores = {k: weighted_mean(v, wte) for k, v in devc.items()}

    risk_cuts = np.quantile(p0_train, [0.25, 0.50, 0.75])
    risk_group = np.searchsorted(risk_cuts, p0_test, side="right").astype(int)
    duration_group = pd.cut(test["Expo"], bins=[0.0,0.25,0.50,0.75,1.0],
                            labels=False, right=True, include_lowest=False).to_numpy()
    if np.any(pd.isna(duration_group)):
        raise RuntimeError("duration group assignment failed")
    duration_group = duration_group.astype(int)

    calibration = {}
    for name, pred_rate in preds.items():
        pred_count = wte * pred_rate
        calibration[name] = {
            "total": {"observed": float(nte.sum()), "predicted": float(pred_count.sum()),
                      "po": None if nte.sum() <= 0 else float(pred_count.sum()/nte.sum())},
            "duration": ratios_by_group(nte, pred_count, duration_group, 4),
            "risk": ratios_by_group(nte, pred_count, risk_group, 4),
            "duration_x_risk": ratios_cross(nte, pred_count, duration_group, risk_group),
        }

    diff_contribs = {name: devc[ch] - devc[ref] for name, ch, ref in CONTRASTS}
    intervals = bootstrap_intervals(diff_contribs, wte, outer_seed ^ 0x5A17)
    contrasts = {}
    for name, ch, ref in CONTRASTS:
        diff = scores[ch] - scores[ref]
        rel = (scores[ref] - scores[ch]) / scores[ref]
        contrasts[name] = {
            "challenger": ch, "reference": ref,
            "deviance_difference": float(diff),
            "relative_improvement": float(rel),
            "relative_improvement_pct": float(100.0*rel),
            "max_calibration_worsening": max_calibration_worsening(calibration[ch], calibration[ref]),
            "direction_favorable": bool(diff < 0),
            "bootstrap": intervals[name],
        }

    return {
        "outer_seed": outer_seed, "train_rows": int(len(train)), "test_rows": int(len(test)),
        "train_claims": float(ntr.sum()), "test_claims": float(nte.sum()),
        "train_exposure": float(wtr.sum()), "test_exposure": float(wte.sum()),
        "m2_oof": {"log_risk_mean": risk_mean, "log_risk_sd": risk_sd,
                   "seed": outer_seed + 10000},
        "hgb": {"inner_seed": outer_seed + 20000, "selected_capacity": winner["id"],
                "capacity_scores": capacity_scores,
                "m3a_feature_columns": BASE_NUM_COLS + CAT_COLS,
                "m3b_feature_columns": BASE_NUM_COLS + CAT_COLS + ["logExposure"]},
        "risk_quartile_cutpoints": [float(x) for x in risk_cuts],
        "scores": scores, "calibration": calibration, "contrasts": contrasts,
    }


def summarize_gate(split_results: list[dict], contrast_name: str):
    c = [s["contrasts"][contrast_name] for s in split_results]
    all_favorable = all(x["direction_favorable"] for x in c)
    mean_rel = float(np.mean([x["relative_improvement"] for x in c]))
    max_worsening = float(max(x["max_calibration_worsening"] for x in c))
    gate = bool(all_favorable and mean_rel >= 0.005 and max_worsening <= 0.10)
    return {"all_three_direction_favorable": all_favorable,
            "mean_relative_improvement": mean_rel,
            "mean_relative_improvement_pct": 100.0*mean_rel,
            "max_calibration_worsening_across_splits": max_worsening,
            "threshold_relative_improvement": 0.005,
            "threshold_max_calibration_worsening": 0.10,
            "gate_passed": gate}


def main():
    out_dir = Path("norauto_duration_transfer_artifact")
    out_dir.mkdir(exist_ok=True)
    source_path = out_dir / "norauto.rda"
    raw = download_source(source_path)
    source_sha = hashlib.sha256(raw).hexdigest()
    df, object_name = load_source(source_path)
    validate_data(df)

    # Normalize only documented column types; no row filtering or target cleaning.
    df = df.copy()
    for c in ["Male", "Young", "Expo", "NbClaim"]:
        df[c] = pd.to_numeric(df[c], errors="raise")
    for c in CAT_COLS:
        df[c] = df[c].astype(str)

    splits = []
    for seed in OUTER_SEEDS:
        print(f"RUN_SPLIT {seed}", flush=True)
        splits.append(run_split(df, seed))

    gates = {name: summarize_gate(splits, name) for name, _, _ in CONTRASTS}
    primary = gates["M3b_minus_M3a"]
    result = {
        "status": "EXECUTED",
        "question_fingerprint": QUESTION_FINGERPRINT,
        "question_sha256": QUESTION_SHA256,
        "ffbk_prereg_commit": FFBK_PREREG_COMMIT,
        "source": {
            "url": SOURCE_URL, "repository": "dutangc/CASdatasets",
            "path": "data/norauto.rda", "path_commit": SOURCE_COMMIT,
            "git_blob_sha": SOURCE_GIT_BLOB, "downloaded_byte_sha256": source_sha,
            "bytes": len(raw), "r_object": object_name, "rows": int(len(df)),
            "columns": list(df.columns), "dtypes": {c: str(df[c].dtype) for c in df.columns},
            "claim_count_total": float(df["NbClaim"].sum()),
            "positive_claim_policies": int((df["NbClaim"] > 0).sum()),
            "exposure_total": float(df["Expo"].sum()),
            "min_exposure": float(df["Expo"].min()), "max_exposure": float(df["Expo"].max()),
            "max_claim_count": int(df["NbClaim"].max()),
        },
        "environment": {"python": sys.version, "platform": platform.platform(),
                        "numpy": np.__version__, "pandas": pd.__version__,
                        "pyreadr": pyreadr.__version__, "scipy": scipy.__version__,
                        "scikit_learn": sklearn.__version__},
        "outer_seeds": OUTER_SEEDS, "splits": splits, "gates": gates,
        "primary_transfer_gate": primary,
        "bounded_verdict": ("SUPPORTED_SECOND_INDEPENDENT_GEOGRAPHY_SOURCE_TRANSFER"
                            if primary["gate_passed"] else "WEAKENED_OR_INCONCLUSIVE_SECOND_SOURCE_TRANSFER"),
        "authority_boundary": "No causal duration law, OOT stability, dispersion law, predictive tail, reinsurance/capital transport, or NextGen default is authorized by this experiment.",
    }
    result_path = out_dir / "result.json"
    result_path.write_text(json.dumps(result, indent=2, sort_keys=True)+"\n", encoding="utf-8")
    result_sha = hashlib.sha256(result_path.read_bytes()).hexdigest()
    summary = {
        "verdict": result["bounded_verdict"], "primary_gate": primary,
        "source_sha256": source_sha, "result_sha256": result_sha,
        "rows": len(df), "claims": float(df["NbClaim"].sum()),
        "exposure": float(df["Expo"].sum()),
        "selected_hgb": {str(s["outer_seed"]): s["hgb"]["selected_capacity"] for s in splits},
    }
    (out_dir/"summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True)+"\n", encoding="utf-8")
    (out_dir/"receipt.txt").write_text(f"DATA_SHA256={source_sha}\nRESULT_SHA256={result_sha}\n", encoding="utf-8")
    print(json.dumps(summary, indent=2), flush=True)


if __name__ == "__main__":
    main()
