#!/usr/bin/env python3
"""Held-out freMTPLfreq duration/pro-rata replication.

Research-only. The scientific comparison is prospectively frozen in FFBK #1318.
It compares the same flexible Poisson GBM risk model with and without log(policy
exposure) as an explicit predictor while retaining Exposure as the frequency
sample weight. Data are downloaded from an exact CASdatasets Git commit.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import platform
import tempfile
import urllib.request
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.metrics import mean_poisson_deviance
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OrdinalEncoder

DATA_COMMIT = "227fb56b8734bdb7c0327a41180e01d2ddaeaf26"
DATA_URL = (
    "https://raw.githubusercontent.com/dutangc/CASdatasets/"
    + DATA_COMMIT
    + "/data/freMTPLfreq.rda"
)
EXPECTED_ROWS = 413_169
OUTER_SEEDS = (3434773802, 2255464811, 4262288853)
QUESTION_FINGERPRINT = "underwriting/fremtplfreq/independent-data/oos-duration-pro-rata/replication"
QUESTION_SHA256 = "ccba7d2a866fa96bfe0d5dd56d943dec334d1707beea2ceebbcd904deeabe64d"
CATEGORICAL = ("Power", "Brand", "Gas", "Region")
NUMERIC = ("CarAge", "DriverAge", "Density")
DURATION_BANDS = (
    ("(0,.25]", 0.0, 0.25),
    ("(.25,.50]", 0.25, 0.50),
    ("(.50,.75]", 0.50, 0.75),
    ("(.75,1]", 0.75, 1.0),
    (">1", 1.0, float("inf")),
)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _download(url: str, path: Path) -> None:
    req = urllib.request.Request(url, headers={"User-Agent": "ffbk-research-replication/1"})
    with urllib.request.urlopen(req, timeout=120) as response, path.open("wb") as out:
        while True:
            chunk = response.read(1024 * 1024)
            if not chunk:
                break
            out.write(chunk)


def load_canonical_dataset(data_path: Path | None = None) -> tuple[pd.DataFrame, dict]:
    try:
        import pyreadr
    except ImportError as exc:  # pragma: no cover - runner dependency gate
        raise RuntimeError("pyreadr is required to read the pinned CASdatasets .rda") from exc

    owned_tmp = None
    if data_path is None:
        owned_tmp = tempfile.TemporaryDirectory(prefix="fremtplfreq-")
        data_path = Path(owned_tmp.name) / "freMTPLfreq.rda"
        _download(DATA_URL, data_path)
    else:
        data_path = Path(data_path)

    digest = sha256_file(data_path)
    objects = pyreadr.read_r(str(data_path))
    if "freMTPLfreq" in objects:
        df = objects["freMTPLfreq"]
    elif len(objects) == 1:
        df = next(iter(objects.values()))
    else:
        raise ValueError(f"unexpected R objects: {list(objects)}")

    df = df.copy()
    if "Gaz" in df.columns and "Gas" not in df.columns:
        df = df.rename(columns={"Gaz": "Gas"})
    required = {"PolicyID", "ClaimNb", "Exposure", *CATEGORICAL, *NUMERIC}
    missing = sorted(required.difference(df.columns))
    if missing:
        raise ValueError(f"missing required columns: {missing}")
    if len(df) != EXPECTED_ROWS:
        raise ValueError(f"unexpected row count {len(df)} != {EXPECTED_ROWS}")
    if not np.all(np.isfinite(df["Exposure"].astype(float))):
        raise ValueError("non-finite Exposure")
    if np.any(df["Exposure"].astype(float) <= 0):
        raise ValueError("non-positive Exposure")
    claim = df["ClaimNb"].astype(float).to_numpy()
    if np.any(claim < 0) or np.any(claim != np.floor(claim)):
        raise ValueError("ClaimNb must be non-negative integer-valued")

    identity = {
        "source": DATA_URL,
        "commit": DATA_COMMIT,
        "sha256": digest,
        "rows": int(len(df)),
        "claim_count": float(df["ClaimNb"].astype(float).sum()),
        "max_claim_nb": float(df["ClaimNb"].astype(float).max()),
        "exposure_sum": float(df["Exposure"].astype(float).sum()),
        "exposure_max": float(df["Exposure"].astype(float).max()),
        "exposure_le_1_fraction": float((df["Exposure"].astype(float) <= 1.0).mean()),
        "exposure_eq_1_fraction": float(np.isclose(df["Exposure"].astype(float), 1.0).mean()),
    }
    if owned_tmp is not None:
        owned_tmp.cleanup()
    return df, identity


def make_model(include_duration: bool, seed: int) -> Pipeline:
    numeric = list(NUMERIC) + (["LogExposure"] if include_duration else [])
    pre = ColumnTransformer(
        [
            (
                "categorical",
                OrdinalEncoder(handle_unknown="use_encoded_value", unknown_value=-1),
                list(CATEGORICAL),
            ),
            ("numeric", "passthrough", numeric),
        ],
        remainder="drop",
    )
    reg = HistGradientBoostingRegressor(
        loss="poisson",
        learning_rate=0.05,
        max_iter=192,
        max_leaf_nodes=31,
        min_samples_leaf=50,
        l2_regularization=1.0,
        early_stopping=False,
        random_state=int(seed % (2**32 - 1)),
    )
    return Pipeline([("preprocessor", pre), ("regressor", reg)])


def duration_calibration(exposure: np.ndarray, claims: np.ndarray, pred_frequency: np.ndarray) -> dict:
    out = {}
    pred_counts = pred_frequency * exposure
    for name, low, high in DURATION_BANDS:
        if np.isinf(high):
            mask = exposure > low
        else:
            mask = (exposure > low) & (exposure <= high)
        n = int(mask.sum())
        observed = float(claims[mask].sum())
        predicted = float(pred_counts[mask].sum())
        out[name] = {
            "rows": n,
            "observed_claims": observed,
            "predicted_claims": predicted,
            "predicted_over_observed": None if observed == 0 else predicted / observed,
        }
    return out


def band_absolute_error(calibration: dict) -> float:
    total_obs = sum(float(v["observed_claims"]) for v in calibration.values())
    if total_obs <= 0:
        return float("nan")
    return sum(abs(float(v["predicted_claims"]) - float(v["observed_claims"])) for v in calibration.values()) / total_obs


def evaluate_one_split(df: pd.DataFrame, seed: int) -> dict:
    work = df[["ClaimNb", "Exposure", *CATEGORICAL, *NUMERIC]].copy()
    work["LogExposure"] = np.log(work["Exposure"].astype(float))
    train, test = train_test_split(work, test_size=0.20, random_state=seed, shuffle=True)

    y_train = train["ClaimNb"].to_numpy(float) / train["Exposure"].to_numpy(float)
    w_train = train["Exposure"].to_numpy(float)
    y_test = test["ClaimNb"].to_numpy(float) / test["Exposure"].to_numpy(float)
    w_test = test["Exposure"].to_numpy(float)
    claim_test = test["ClaimNb"].to_numpy(float)

    results = {}
    for name, include_duration in (("pro_rata", False), ("duration_aware", True)):
        model = make_model(include_duration, seed)
        model.fit(train, y_train, regressor__sample_weight=w_train)
        pred = model.predict(test)
        dev = float(mean_poisson_deviance(y_test, pred, sample_weight=w_test))
        cal = duration_calibration(w_test, claim_test, pred)
        pred_count = float(np.sum(pred * w_test))
        obs_count = float(np.sum(claim_test))
        results[name] = {
            "weighted_mean_poisson_deviance": dev,
            "predicted_claims": pred_count,
            "observed_claims": obs_count,
            "predicted_over_observed": pred_count / obs_count,
            "duration_band_absolute_error_over_total_observed": band_absolute_error(cal),
            "duration_calibration": cal,
        }

    results["delta_pro_rata_minus_duration_deviance"] = (
        results["pro_rata"]["weighted_mean_poisson_deviance"]
        - results["duration_aware"]["weighted_mean_poisson_deviance"]
    )
    results["delta_band_abs_error_pro_rata_minus_duration"] = (
        results["pro_rata"]["duration_band_absolute_error_over_total_observed"]
        - results["duration_aware"]["duration_band_absolute_error_over_total_observed"]
    )
    results["seed"] = int(seed)
    results["train_rows"] = int(len(train))
    results["test_rows"] = int(len(test))
    return results


def run(df: pd.DataFrame, identity: dict) -> dict:
    splits = [evaluate_one_split(df, seed) for seed in OUTER_SEEDS]
    devtas = [x["delta_pro_rata_minus_duration_deviance"] for x in splits]
    caltas = [x["delta_band_abs_error_pro_rata_minus_duration"] for x in splits]
    if all(x > 0 for x in devtas) and all(x > 0 for x in caltas):
        bounded_verdict = "SUPPORTED_ON_DISTINCT_HELDOUT_DATA"
    elif all(x <= 0 for x in devtas):
        bounded_verdict = "FALSIFIED_FOR_DECLARED_REPLICATION"
    else:
        bounded_verdict = "MIXED_OR_INCONCLUSIVE"
    return {
        "research_status": bounded_verdict,
        "question_fingerprint": QUESTION_FINGERPRINT,
        "question_sha256": QUESTION_SHA256,
        "outer_seeds": list(OUTER_SEEDS),
        "dataset": identity,
        "model_contract": {
            "consumer": "annualised claim frequency / expected claim count",
            "pro_rata": "Exposure is sample weight only; no duration predictor",
            "duration_aware": "same model plus LogExposure predictor; Exposure remains sample weight",
            "estimator": "sklearn HistGradientBoostingRegressor(loss=poisson)",
            "fixed_parameters": {
                "learning_rate": 0.05,
                "max_iter": 192,
                "max_leaf_nodes": 31,
                "min_samples_leaf": 50,
                "l2_regularization": 1.0,
                "early_stopping": False,
            },
        },
        "splits": splits,
        "mean_delta_pro_rata_minus_duration_deviance": float(np.mean(devtas)),
        "mean_delta_band_abs_error_pro_rata_minus_duration": float(np.mean(caltas)),
        "environment": {
            "python": platform.python_version(),
            "numpy": np.__version__,
            "pandas": pd.__version__,
        },
        "authority": {
            "independent_data_confirmation": bounded_verdict == "SUPPORTED_ON_DISTINCT_HELDOUT_DATA",
            "out_of_time_confirmation": False,
            "predictive_variance_authorized": False,
            "tail_transport_authorized": False,
            "nextgen_promotion": "none",
        },
    }


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--data", type=Path, default=None)
    p.add_argument("--output", type=Path, default=Path("fremtplfreq_oos_duration_result.json"))
    args = p.parse_args()
    df, identity = load_canonical_dataset(args.data)
    result = run(df, identity)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
