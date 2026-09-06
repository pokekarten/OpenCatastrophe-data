#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import urllib.request
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import gamma as gamma_dist
from scipy.stats import invgauss
from sklearn.compose import ColumnTransformer
from sklearn.datasets import fetch_openml
from sklearn.linear_model import TweedieRegressor
from sklearn.metrics import mean_tweedie_deviance
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

FREQ_ID = 41214
SEV_ID = 41215
SEEDS = (26090601, 26090617, 26090643)
ALPHAS = (0.0, 0.01, 0.1, 1.0, 10.0)
CAT = ("VehBrand", "VehGas", "Region", "Area")
NUM = ("VehPower", "VehAge", "DrivAge", "BonusMalus", "LogDensity")
MAX_UNMATCHED_SHARE = 0.005
OUT = Path("tmp_ffbk_severity_transfer_result.json")


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


def load_claim_level() -> tuple[pd.DataFrame, dict]:
    freq = fetch_openml(data_id=FREQ_ID, as_frame=True).data.copy()
    sev = fetch_openml(data_id=SEV_ID, as_frame=True).data.copy()
    freq["IDpol"] = freq["IDpol"].astype("int64")
    sev["IDpol"] = sev["IDpol"].astype("int64")
    sev["ClaimAmount"] = sev["ClaimAmount"].astype(float)
    for c in freq.columns:
        if freq[c].dtype == object or isinstance(freq[c].dtype, pd.CategoricalDtype):
            freq[c] = freq[c].astype(str).str.strip("'")

    sev_pos = sev[sev["ClaimAmount"] > 0].copy()
    unmatched = ~sev_pos["IDpol"].isin(freq["IDpol"])
    unmatched_rows = int(unmatched.sum())
    unmatched_row_share = float(unmatched.mean()) if len(sev_pos) else 0.0
    unmatched_amount = float(sev_pos.loc[unmatched, "ClaimAmount"].sum())
    total_amount = float(sev_pos["ClaimAmount"].sum())
    unmatched_amount_share = unmatched_amount / total_amount if total_amount > 0 else 0.0
    reconciliation = {
        "positive_severity_rows_raw": int(len(sev_pos)),
        "positive_severity_rows_without_policy": unmatched_rows,
        "unmatched_row_share": unmatched_row_share,
        "unmatched_claim_amount": unmatched_amount,
        "unmatched_claim_amount_share": unmatched_amount_share,
        "rule_frozen_after_pre_model_join_failure": "exclude unmatched rows only if both row and amount share <= 0.5%; otherwise stop",
    }
    if unmatched_row_share > MAX_UNMATCHED_SHARE or unmatched_amount_share > MAX_UNMATCHED_SHARE:
        raise RuntimeError(f"unmatched severity materiality gate failed: {reconciliation}")

    sev_use = sev_pos.loc[~unmatched].copy()
    keep = ["IDpol", "VehPower", "VehAge", "DrivAge", "BonusMalus", "VehBrand", "VehGas", "Area", "Density", "Region"]
    d = sev_use.merge(freq[keep], on="IDpol", how="left", validate="many_to_one")
    if d["Region"].isna().any():
        raise RuntimeError("matched severity rows lost rating covariates")
    d["LogDensity"] = np.log(d["Density"].astype(float))
    return d, {
        "openml": {"frequency": openml_meta(FREQ_ID), "severity": openml_meta(SEV_ID)},
        "reconciliation": reconciliation,
    }


def make_pipe(power: float, alpha: float) -> Pipeline:
    prep = ColumnTransformer(
        [
            ("cat", OneHotEncoder(handle_unknown="ignore", drop="first"), list(CAT)),
            ("num", StandardScaler(), list(NUM)),
        ]
    )
    reg = TweedieRegressor(power=power, alpha=alpha, link="log", max_iter=1000, tol=1e-8)
    return Pipeline([("prep", prep), ("reg", reg)])


def select_alpha(train: pd.DataFrame, valid: pd.DataFrame, power: float) -> tuple[float, list[dict]]:
    rows = []
    Xtr, ytr = train[list(CAT + NUM)], train["ClaimAmount"].to_numpy(float)
    Xva, yva = valid[list(CAT + NUM)], valid["ClaimAmount"].to_numpy(float)
    for alpha in ALPHAS:
        m = make_pipe(power, alpha)
        m.fit(Xtr, ytr)
        p = m.predict(Xva)
        rows.append({"alpha": alpha, "validation_family_deviance": float(mean_tweedie_deviance(yva, p, power=power))})
    best = min(rows, key=lambda r: (r["validation_family_deviance"], r["alpha"]))
    return float(best["alpha"]), rows


def pearson_phi(y: np.ndarray, mu: np.ndarray, power: float) -> float:
    phi = float(np.mean((y - mu) ** 2 / np.maximum(mu, 1e-12) ** power))
    return max(phi, 1e-12)


def logloss(y: np.ndarray, mu: np.ndarray, phi: float, power: float) -> np.ndarray:
    if power == 2.0:
        ll = gamma_dist.logpdf(y, a=1.0 / phi, scale=phi * mu)
    elif power == 3.0:
        ll = invgauss.logpdf(y, mu=phi * mu, scale=1.0 / phi)
    else:
        raise ValueError(power)
    if not np.isfinite(ll).all():
        raise RuntimeError("non-finite held-out log density")
    return -ll


def quantile(mu: np.ndarray, phi: float, power: float, q: float) -> np.ndarray:
    if power == 2.0:
        return gamma_dist.ppf(q, a=1.0 / phi, scale=phi * mu)
    return invgauss.ppf(q, mu=phi * mu, scale=1.0 / phi)


def policy_bootstrap_delta(ids: np.ndarray, loss_gamma: np.ndarray, loss_ig: np.ndarray, seed: int, reps: int = 500) -> dict:
    tmp = pd.DataFrame({"IDpol": ids, "g": loss_gamma, "ig": loss_ig})
    grp = tmp.groupby("IDpol", sort=False).agg(g=("g", "sum"), ig=("ig", "sum"), n=("g", "size"))
    g = grp["g"].to_numpy(float)
    ig = grp["ig"].to_numpy(float)
    n = grp["n"].to_numpy(float)
    rng = np.random.default_rng(seed)
    vals = np.empty(reps)
    m = len(grp)
    for b in range(reps):
        idx = rng.integers(0, m, size=m)
        vals[b] = (ig[idx].sum() - g[idx].sum()) / n[idx].sum()
    point = float((ig.sum() - g.sum()) / n.sum())
    return {
        "delta_nll_ig_minus_gamma": point,
        "ci95": [float(np.quantile(vals, 0.025)), float(np.quantile(vals, 0.975))],
        "bootstrap_reps": reps,
        "bootstrap_unit": "policy_IDpol",
    }


def fit_family(dev_train: pd.DataFrame, inner_valid: pd.DataFrame, dev_all: pd.DataFrame, test: pd.DataFrame, power: float) -> tuple[dict, np.ndarray]:
    alpha, alpha_rows = select_alpha(dev_train, inner_valid, power)
    Xdev = dev_all[list(CAT + NUM)]
    ydev = dev_all["ClaimAmount"].to_numpy(float)
    Xtest = test[list(CAT + NUM)]
    ytest = test["ClaimAmount"].to_numpy(float)
    model = make_pipe(power, alpha)
    model.fit(Xdev, ydev)
    mu_dev = model.predict(Xdev)
    mu_test = model.predict(Xtest)
    phi = pearson_phi(ydev, mu_dev, power)
    losses = logloss(ytest, mu_test, phi, power)
    q95 = quantile(mu_test, phi, power, 0.95)
    q99 = quantile(mu_test, phi, power, 0.99)
    return {
        "power": power,
        "alpha": alpha,
        "alpha_selection": alpha_rows,
        "pearson_phi_train": phi,
        "mean_nll_test": float(np.mean(losses)),
        "actual_over_predicted_mean": float(np.sum(ytest) / np.sum(mu_test)),
        "gamma_deviance_test": float(mean_tweedie_deviance(ytest, mu_test, power=2)),
        "inverse_gaussian_deviance_test": float(mean_tweedie_deviance(ytest, mu_test, power=3)),
        "q95_exceedance_rate_test": float(np.mean(ytest > q95)),
        "q99_exceedance_rate_test": float(np.mean(ytest > q99)),
        "predicted_mean_test": float(np.mean(mu_test)),
        "observed_mean_test": float(np.mean(ytest)),
    }, losses


def main() -> None:
    d, provenance = load_claim_level()
    source_summary = {
        **provenance,
        "claim_rows_positive_used": int(len(d)),
        "unique_claim_policy_ids": int(d["IDpol"].nunique()),
        "policies_with_multiple_positive_claim_rows": int((d.groupby("IDpol").size() > 1).sum()),
        "claim_amount_summary_used": {
            "mean": float(d["ClaimAmount"].mean()),
            "p95": float(d["ClaimAmount"].quantile(0.95)),
            "p99": float(d["ClaimAmount"].quantile(0.99)),
            "max": float(d["ClaimAmount"].max()),
        },
    }
    results = []
    all_ids = np.array(sorted(d["IDpol"].unique()))
    for seed in SEEDS:
        dev_ids, test_ids = train_test_split(all_ids, test_size=0.20, random_state=seed)
        tr_ids, va_ids = train_test_split(dev_ids, test_size=0.25, random_state=seed + 1)
        dev_train = d[d["IDpol"].isin(tr_ids)].copy()
        inner_valid = d[d["IDpol"].isin(va_ids)].copy()
        dev_all = d[d["IDpol"].isin(dev_ids)].copy()
        test = d[d["IDpol"].isin(test_ids)].copy()
        g, lg = fit_family(dev_train, inner_valid, dev_all, test, 2.0)
        ig, lig = fit_family(dev_train, inner_valid, dev_all, test, 3.0)
        boot = policy_bootstrap_delta(test["IDpol"].to_numpy("int64"), lg, lig, seed + 777)
        results.append({
            "seed": seed,
            "split_counts": {
                "development_policy_ids": int(len(dev_ids)),
                "test_policy_ids": int(len(test_ids)),
                "development_claim_rows": int(len(dev_all)),
                "test_claim_rows": int(len(test)),
            },
            "gamma": g,
            "inverse_gaussian": ig,
            "paired_logscore": boot,
        })
    payload = {
        "protocol": {
            "seeds": list(SEEDS),
            "alphas": list(ALPHAS),
            "outer_split": "80/20 unique policy IDpol",
            "inner_split": "75/25 of development unique policy IDs",
            "primary_target": "raw positive claim-level ClaimAmount; no 200k cap",
            "features": {"categorical_one_hot_drop_first": list(CAT), "numeric_standardized": list(NUM), "LogDensity": "log(Density)"},
            "families": {"gamma": 2, "inverse_gaussian": 3},
            "pre_fit_reconciliation_materiality_gate": MAX_UNMATCHED_SHARE,
        },
        "source": source_summary,
        "results": results,
    }
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    payload["result_payload_sha256_without_receipt"] = hashlib.sha256(canonical).hexdigest()
    OUT.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
