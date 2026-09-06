#!/usr/bin/env python3
"""Independent Loss-ALAE policy-limit censoring replication probe.

This probe intentionally separates source verification, observation semantics,
model-family comparison, predictive scoring and downstream tail/layer sensitivity.
It is research evidence only; it does not select a production severity default.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import urllib.request
from dataclasses import asdict, dataclass
from pathlib import Path

import numpy as np
from scipy import integrate
from scipy.stats import CensoredData, lognorm, lomax, weibull_min

SOURCE_COMMIT = "a5799b49a41fe5e8c31ce0a501c1b11fc055f39f"
SOURCE_PATH = "public/docs/1-claims-modelling/m5-copulas/LossData-FV.csv"
SOURCE_URL = (
    "https://raw.githubusercontent.com/UniMelb-Actuarial/"
    "ACTL20004-ACTL90021-2024/"
    f"{SOURCE_COMMIT}/{SOURCE_PATH}"
)
EXPECTED_GIT_BLOB_SHA1 = "565763a20b07d76d8c46003757ce0c75ff867f3b"
EXPECTED_ROWS = 1500
EXPECTED_CENSORED = 34
EXPECTED_KNOWN_LIMITS = 1352
FOLDS = 5
FOLD_SEED = 20260906
Q = 0.995
LAYER_ATTACHMENT = 250_000.0
LAYER_LIMIT = 750_000.0


@dataclass(frozen=True)
class FitResult:
    model: str
    params: list[float]
    full_loglik: float
    aic: float
    q995: float
    expected_750k_xs_250k: float
    oof_mean_log_score: float
    fold_mean_log_scores: list[float]


def git_blob_sha1(payload: bytes) -> str:
    header = f"blob {len(payload)}\0".encode("ascii")
    return hashlib.sha1(header + payload).hexdigest()


def load_payload(csv_path: Path | None) -> tuple[bytes, str]:
    if csv_path is not None:
        payload = csv_path.read_bytes()
        source = str(csv_path)
    else:
        with urllib.request.urlopen(SOURCE_URL, timeout=30) as response:
            payload = response.read()
        source = SOURCE_URL
    return payload, source


def parse(payload: bytes) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    text = payload.decode("utf-8")
    reader = csv.DictReader(io.StringIO(text))
    required = ["LOSS", "ALAE", "LIMIT", "CENSOR"]
    if reader.fieldnames != required:
        raise ValueError(f"unexpected columns: {reader.fieldnames!r}")

    loss, limit, censored = [], [], []
    for row in reader:
        loss.append(float(row["LOSS"]))
        limit.append(float(row["LIMIT"]))
        censored.append(bool(int(row["CENSOR"])))

    x = np.asarray(loss, dtype=float)
    l = np.asarray(limit, dtype=float)
    c = np.asarray(censored, dtype=bool)

    if len(x) != EXPECTED_ROWS:
        raise ValueError(f"expected {EXPECTED_ROWS} rows, got {len(x)}")
    if int(c.sum()) != EXPECTED_CENSORED:
        raise ValueError(f"expected {EXPECTED_CENSORED} censored rows, got {int(c.sum())}")
    if int((l > 0).sum()) != EXPECTED_KNOWN_LIMITS:
        raise ValueError(
            f"expected {EXPECTED_KNOWN_LIMITS} known positive limits, got {int((l > 0).sum())}"
        )
    if np.any(c & (l <= 0)):
        raise ValueError("censored rows must have a known positive policy limit")
    if not np.allclose(x[c], l[c], rtol=0.0, atol=0.0):
        raise ValueError("censored LOSS must equal LIMIT in this benchmark")
    if np.any(x <= 0):
        raise ValueError("severity models in this probe require strictly positive losses")
    return x, l, c


MODELS = {
    "naive_lognormal": (lognorm, False),
    "censor_aware_lognormal": (lognorm, True),
    "censor_aware_weibull": (weibull_min, True),
    "censor_aware_lomax": (lomax, True),
}


def fit_model(name: str, x: np.ndarray, c: np.ndarray) -> tuple[object, tuple[float, ...]]:
    dist, aware = MODELS[name]
    if aware:
        data = CensoredData.right_censored(x, c)
        params = dist.fit(data, floc=0)
    else:
        params = dist.fit(x, floc=0)
    return dist, tuple(float(v) for v in params)


def observed_log_scores(dist, params: tuple[float, ...], x: np.ndarray, c: np.ndarray) -> np.ndarray:
    shape = params[:-2]
    loc, scale = params[-2:]
    out = np.empty(len(x), dtype=float)
    out[~c] = dist.logpdf(x[~c], *shape, loc=loc, scale=scale)
    out[c] = dist.logsf(x[c], *shape, loc=loc, scale=scale)
    if not np.all(np.isfinite(out)):
        raise FloatingPointError("non-finite observed-data log score")
    return out


def expected_layer_loss(dist, params: tuple[float, ...]) -> float:
    shape = params[:-2]
    loc, scale = params[-2:]
    a = LAYER_ATTACHMENT
    b = LAYER_ATTACHMENT + LAYER_LIMIT
    val, _ = integrate.quad(
        lambda z: float(dist.sf(z, *shape, loc=loc, scale=scale)),
        a,
        b,
        epsabs=1e-6,
        epsrel=1e-8,
        limit=200,
    )
    return float(val)


def stratified_folds(c: np.ndarray) -> np.ndarray:
    rng = np.random.default_rng(FOLD_SEED)
    fold = np.empty(len(c), dtype=int)
    for mask in (c, ~c):
        idx = np.flatnonzero(mask)
        idx = idx[rng.permutation(len(idx))]
        fold[idx] = np.arange(len(idx)) % FOLDS
    return fold


def evaluate(name: str, x: np.ndarray, c: np.ndarray, folds: np.ndarray) -> FitResult:
    dist, full_params = fit_model(name, x, c)
    full_scores = observed_log_scores(dist, full_params, x, c)
    k = len(full_params) - 1  # loc is fixed at zero; all other returned params are estimated.
    full_ll = float(full_scores.sum())

    fold_means: list[float] = []
    all_scores = np.empty(len(x), dtype=float)
    for fold_id in range(FOLDS):
        test = folds == fold_id
        train = ~test
        fold_dist, params = fit_model(name, x[train], c[train])
        scores = observed_log_scores(fold_dist, params, x[test], c[test])
        all_scores[test] = scores
        fold_means.append(float(scores.mean()))

    shape = full_params[:-2]
    loc, scale = full_params[-2:]
    q995 = float(dist.ppf(Q, *shape, loc=loc, scale=scale))

    return FitResult(
        model=name,
        params=list(full_params),
        full_loglik=full_ll,
        aic=float(2 * k - 2 * full_ll),
        q995=q995,
        expected_750k_xs_250k=expected_layer_loss(dist, full_params),
        oof_mean_log_score=float(all_scores.mean()),
        fold_mean_log_scores=fold_means,
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--csv", type=Path, help="Optional local copy of the pinned CSV")
    parser.add_argument("--output", type=Path, help="Optional JSON result path")
    args = parser.parse_args()

    payload, source = load_payload(args.csv)
    blob_sha = git_blob_sha1(payload)
    if blob_sha != EXPECTED_GIT_BLOB_SHA1:
        raise ValueError(
            f"source identity mismatch: expected git blob {EXPECTED_GIT_BLOB_SHA1}, got {blob_sha}"
        )

    x, limits, c = parse(payload)
    folds = stratified_folds(c)
    results = [evaluate(name, x, c, folds) for name in MODELS]

    receipt = {
        "status": "RESEARCH_ONLY_NO_PROMOTION",
        "source": source,
        "source_commit": SOURCE_COMMIT,
        "source_path": SOURCE_PATH,
        "git_blob_sha1": blob_sha,
        "rows": int(len(x)),
        "censored_rows": int(c.sum()),
        "known_limits": int((limits > 0).sum()),
        "censoring_fraction": float(c.mean()),
        "validation": {
            "design": "5-fold stratified out-of-fold observed-data log score",
            "folds": FOLDS,
            "seed": FOLD_SEED,
            "stratification": "CENSOR only; no severity-value stratification",
            "candidate_set_frozen": list(MODELS),
            "selection_note": "No hyperparameter/model tuning; no untouched final holdout; no promotion claim.",
        },
        "downstream_consumer": {
            "q": Q,
            "layer_attachment": LAYER_ATTACHMENT,
            "layer_limit": LAYER_LIMIT,
        },
        "results": [asdict(r) for r in results],
    }

    encoded = json.dumps(receipt, indent=2, sort_keys=True)
    print(encoded)
    if args.output:
        args.output.write_text(encoded + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
