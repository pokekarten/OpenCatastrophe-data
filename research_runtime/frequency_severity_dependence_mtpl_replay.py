#!/usr/bin/env python3
"""Prospective Dutch-MTPL replication for frequency-severity dependence.

Research-only. The target protocol compares an independent frequency/severity
model against a count-conditioned severity challenger on held-out policy total
loss. It never uses the realized held-out claim count as a predictor: future
count is integrated out under the fitted Poisson frequency law.

Expected source schema (insurancerating::MTPL):
    age_policyholder, nclaims, exposure, amount, power, bm, zip

Dependencies: numpy, pandas, scipy, statsmodels.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm
from scipy.special import gammaln, logsumexp

SOURCE_ROWS = 30_000
SOURCE_GIT_BLOB = "f40daffb76ad9b92034f4e6af41024327fa1f696"
SOURCE_UPSTREAM_COMMIT = "688e4208dec8c096552a2447fd1c246bc95a03a8"
SOURCE_CRAN_COMMIT = "5fe40e5d5e425820ace87b4f961dfffad2a99589"
SOURCE_RDA_SIZE = 99_111
SOURCE_RDA_MD5 = "591c5cf616aa5b946395674fdf67a192"
SPLIT_SEED = 20260907
COUNT_MAX = 20
BOOTSTRAP_SEED = 20260908
N_BOOTSTRAP = 1_000
EPS = 1e-12

REQUIRED = {
    "age_policyholder",
    "nclaims",
    "exposure",
    "amount",
    "power",
    "bm",
    "zip",
}


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def deterministic_partition(n: int) -> np.ndarray:
    """Return target-independent 0=train, 1=selection, 2=final split labels."""
    labels = np.empty(n, dtype=np.int8)
    for i in range(n):
        digest = hashlib.blake2b(
            f"{SPLIT_SEED}:{i}".encode(), digest_size=8
        ).digest()
        u = int.from_bytes(digest, "big") / 2**64
        labels[i] = 0 if u < 0.70 else (1 if u < 0.85 else 2)
    return labels


def _design(df: pd.DataFrame, columns: list[str] | None = None) -> pd.DataFrame:
    base = pd.DataFrame(
        {
            "age": pd.to_numeric(df["age_policyholder"], errors="raise"),
            "power": pd.to_numeric(df["power"], errors="raise"),
            "bm": pd.to_numeric(df["bm"], errors="raise"),
            "zip": df["zip"].astype(str),
        }
    )
    # Fixed nonlinear transforms chosen before target access. They reduce the
    # chance that a count term merely proxies an obvious nonlinear risk effect.
    for name in ("age", "power", "bm"):
        x = base[name].astype(float)
        base[f"{name}_log1p"] = np.log1p(np.maximum(x, 0.0))
        base[f"{name}_sqrt"] = np.sqrt(np.maximum(x, 0.0))
    base = base.drop(columns=["zip"])
    zip_dummies = pd.get_dummies(df["zip"].astype(str), prefix="zip", dtype=float)
    out = pd.concat([base.reset_index(drop=True), zip_dummies.reset_index(drop=True)], axis=1)
    out = sm.add_constant(out.astype(float), has_constant="add")
    if columns is not None:
        for column in columns:
            if column not in out:
                out[column] = 0.0
        out = out.reindex(columns=columns, fill_value=0.0)
    return out


def validate_source(df: pd.DataFrame) -> None:
    missing = sorted(REQUIRED - set(df.columns))
    if missing:
        raise ValueError(f"missing required columns: {missing}")
    if len(df) != SOURCE_ROWS:
        raise ValueError(f"expected {SOURCE_ROWS} rows, found {len(df)}")
    exposure = pd.to_numeric(df["exposure"], errors="raise").to_numpy(float)
    count = pd.to_numeric(df["nclaims"], errors="raise").to_numpy(float)
    amount = pd.to_numeric(df["amount"], errors="raise").to_numpy(float)
    if np.any(~np.isfinite(exposure)) or np.any(exposure <= 0):
        raise ValueError("exposure must be finite and strictly positive")
    if np.any(count < 0) or np.any(count != np.floor(count)):
        raise ValueError("nclaims must be non-negative integers")
    if np.any(~np.isfinite(amount)) or np.any(amount < 0):
        raise ValueError("amount must be finite and non-negative")
    if np.any((count == 0) & (amount != 0)):
        raise ValueError("positive amount with zero nclaims violates source semantics")


def fit_models(train: pd.DataFrame, dependent: bool):
    x = _design(train)
    count = train["nclaims"].to_numpy(float)
    exposure = train["exposure"].to_numpy(float)
    freq = sm.GLM(
        count,
        x,
        family=sm.families.Poisson(),
        offset=np.log(exposure),
    ).fit()

    pos = count > 0
    sev_x = x.loc[pos].copy()
    if dependent:
        sev_x["count"] = count[pos]
    avg = train.loc[pos, "amount"].to_numpy(float) / count[pos]
    if np.any(avg <= 0):
        raise ValueError("positive-count rows must have positive average severity")
    # Lognormal average-severity law matches the existing synthetic probe and
    # permits an exact mixture density over latent future counts.
    sev = sm.OLS(np.log(avg), sev_x).fit()
    sigma = float(np.sqrt(np.mean(np.asarray(sev.resid) ** 2)))
    return freq, sev, sigma, list(x.columns)


def score_policy_totals(
    test: pd.DataFrame, freq, sev, sigma: float, x_columns: list[str], dependent: bool
) -> tuple[np.ndarray, np.ndarray]:
    x = _design(test, columns=x_columns)
    linear = np.asarray(freq.predict(x, which="linear"))
    exposure = test["exposure"].to_numpy(float)
    lam = np.exp(linear + np.log(exposure))
    amount = test["amount"].to_numpy(float)

    beta = float(sev.params.get("count", 0.0))
    base_columns = [c for c in x_columns if c in sev.params.index]
    eta = np.asarray(x[base_columns]) @ np.asarray(sev.params[base_columns])

    # Prospectively integrate future count out of expected aggregate loss.
    # For Poisson N and m(N,X)=exp(eta + beta*N):
    # E[N*m(N,X)] = exp(eta) * lambda * exp(beta) *
    #               exp(lambda*(exp(beta)-1)).
    t = math.exp(beta) if dependent else 1.0
    expected_loss = np.exp(eta) * lam * t * np.exp(lam * (t - 1.0))

    score = np.empty(len(test), dtype=float)
    zero = amount == 0
    score[zero] = -lam[zero]
    n_grid = np.arange(1, COUNT_MAX + 1, dtype=float)
    log_fact = gammaln(n_grid + 1.0)

    for j in np.flatnonzero(~zero):
        log_pn = -lam[j] + n_grid * np.log(max(lam[j], EPS)) - log_fact
        mu = eta[j] + (beta * n_grid if dependent else 0.0)
        avg_amount = amount[j] / n_grid
        log_sev = (
            -np.log(avg_amount * sigma * np.sqrt(2.0 * np.pi))
            - 0.5 * ((np.log(avg_amount) - mu) / sigma) ** 2
        )
        # Jacobian from average severity to policy total: A = n * avg.
        score[j] = logsumexp(log_pn + log_sev - np.log(n_grid))

    return score, expected_loss


def run(df: pd.DataFrame) -> dict:
    validate_source(df)
    split = deterministic_partition(len(df))
    # Selection remains unused in v0: no target-tuned hyperparameters. Keeping
    # it isolated protects a later frequency-family or mean-surface challenger.
    train = df.iloc[np.flatnonzero(split == 0)].reset_index(drop=True)
    final = df.iloc[np.flatnonzero(split == 2)].reset_index(drop=True)

    rows = []
    score_vectors = []
    for dependent in (False, True):
        freq, sev, sigma, columns = fit_models(train, dependent=dependent)
        log_score, expected_loss = score_policy_totals(
            final, freq, sev, sigma, columns, dependent=dependent
        )
        observed = final["amount"].to_numpy(float)
        score_vectors.append(log_score)
        rows.append(
            {
                "model": "dependent_count_conditioned" if dependent else "independent",
                "mean_policy_total_log_score": float(np.mean(log_score)),
                "aggregate_ae": float(np.sum(observed) / np.sum(expected_loss)),
                "mean_beta_count": float(sev.params.get("count", 0.0)),
                "n_final": int(len(final)),
            }
        )

    score_delta = score_vectors[1] - score_vectors[0]
    delta = float(np.mean(score_delta))
    rng = np.random.default_rng(BOOTSTRAP_SEED)
    n = len(score_delta)
    boot = np.empty(N_BOOTSTRAP, dtype=float)
    for b in range(N_BOOTSTRAP):
        idx = rng.integers(0, n, size=n)
        boot[b] = float(np.mean(score_delta[idx]))
    ci_low, ci_high = np.quantile(boot, [0.025, 0.975])
    return {
        "status": "EXECUTED_TARGET_RESULT_NO_AUTOMATIC_PROMOTION",
        "split_seed": SPLIT_SEED,
        "source_rows": len(df),
        "models": rows,
        "dependent_minus_independent_log_score": delta,
        "paired_policy_bootstrap_95pct": [float(ci_low), float(ci_high)],
        "bootstrap_seed": BOOTSTRAP_SEED,
        "n_bootstrap": N_BOOTSTRAP,
    }


def _synthetic(n: int = SOURCE_ROWS, beta: float = 0.35, seed: int = 9117) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    age = rng.integers(18, 90, size=n)
    power = rng.integers(25, 160, size=n)
    bm = rng.integers(0, 23, size=n)
    zip_code = rng.integers(0, 4, size=n)
    exposure = rng.uniform(0.45, 1.0, size=n)
    x = (age - 50) / 20
    lam = np.exp(-1.5 + 0.25 * x + 0.08 * zip_code + np.log(exposure))
    count = rng.poisson(lam)
    mean_log = 7.0 + 0.12 * x + 0.03 * zip_code + beta * count
    avg = np.zeros(n)
    pos = count > 0
    avg[pos] = rng.lognormal(mean_log[pos], 0.55)
    amount = count * avg
    return pd.DataFrame(
        {
            "age_policyholder": age,
            "nclaims": count,
            "exposure": exposure,
            "amount": amount,
            "power": power,
            "bm": bm,
            "zip": zip_code,
        }
    )


def self_check() -> dict:
    null_result = run(_synthetic(beta=0.0, seed=901))
    dep_result = run(_synthetic(beta=0.35, seed=902))
    null_delta = null_result["dependent_minus_independent_log_score"]
    dep_delta = dep_result["dependent_minus_independent_log_score"]
    if dep_delta <= 0.0:
        raise AssertionError("positive-control dependence challenger did not improve log score")
    if abs(null_delta) > 0.01:
        raise AssertionError(f"null-world score delta unexpectedly large: {null_delta}")
    return {"null": null_result, "positive_control": dep_result, "status": "SELF_CHECK_PASS"}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--csv", type=Path)
    parser.add_argument("--expected-sha256")
    parser.add_argument("--self-check", action="store_true")
    args = parser.parse_args()

    if args.self_check:
        print(json.dumps(self_check(), indent=2, sort_keys=True))
        return
    if args.csv is None or args.expected_sha256 is None:
        parser.error("target execution requires --csv and --expected-sha256")
    actual = sha256_file(args.csv)
    if actual.lower() != args.expected_sha256.lower():
        raise SystemExit(f"CSV SHA-256 mismatch: expected {args.expected_sha256}, got {actual}")
    result = run(pd.read_csv(args.csv))
    result["csv_sha256"] = actual
    result["source_git_blob"] = SOURCE_GIT_BLOB
    result["source_upstream_commit"] = SOURCE_UPSTREAM_COMMIT
    result["source_cran_commit"] = SOURCE_CRAN_COMMIT
    result["source_rda_size"] = SOURCE_RDA_SIZE
    result["source_rda_md5"] = SOURCE_RDA_MD5
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
