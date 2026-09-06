#!/usr/bin/env python3
from __future__ import annotations

from collections import Counter
import hashlib
import json
from pathlib import Path
import struct
import tempfile
import urllib.request

import numpy as np
import pandas as pd
import rdata
from scipy.stats import gamma as gamma_dist
from scipy.stats import invgauss
from sklearn.compose import ColumnTransformer
from sklearn.datasets import fetch_openml
from sklearn.linear_model import TweedieRegressor
from sklearn.metrics import mean_tweedie_deviance
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

CAS_SHA = "227fb56b8734bdb7c0327a41180e01d2ddaeaf26"
FREQ_ID = 41214
SEV_ID = 41215
EXPECTED_CURRENT_SHA256 = {
    "frequency": "82c8598513d9fa78226b6c7d271a9940eca4b8083e9e32320a75d377bdfe15a3",
    "severity": "78e6e5016ae046603b37e88ff8ad8ca327f5d59f827c1f75d140388de09b14b3",
}
PRE_FIT_RUN = 34035461439
SEEDS = (26090601, 26090617, 26090643)
ALPHAS = (0.0, 0.01, 0.1, 1.0, 10.0)
CAT = ("VehBrand", "VehGas", "Region", "Area")
NUM = ("VehPower", "VehAge", "DrivAge", "BonusMalus", "LogDensity")
FEATURES = ("VehPower", "VehAge", "DrivAge", "BonusMalus", "VehBrand", "VehGas", "Area", "Density", "Region")
OUT = Path("tmp_ffbk_severity_transfer_result.json")


def fetch_bytes(url: str) -> tuple[bytes, str]:
    req = urllib.request.Request(url, headers={"User-Agent": "ffbk-research-severity/1"})
    with urllib.request.urlopen(req, timeout=120) as r:
        data = r.read()
    return data, hashlib.sha256(data).hexdigest()


def read_current_rda(name: str, expected_sha256: str) -> tuple[pd.DataFrame, dict]:
    url = f"https://raw.githubusercontent.com/dutangc/CASdatasets/{CAS_SHA}/data/{name}.rda"
    raw, sha256 = fetch_bytes(url)
    if sha256 != expected_sha256:
        raise RuntimeError(f"unexpected {name} SHA256: {sha256}")
    with tempfile.NamedTemporaryFile(suffix=".rda") as f:
        f.write(raw)
        f.flush()
        obj = rdata.read_rda(f.name)
    if name not in obj:
        raise RuntimeError(f"{name} absent from RData")
    return pd.DataFrame(obj[name]).copy(), {
        "repository": "dutangc/CASdatasets",
        "commit": CAS_SHA,
        "path": f"data/{name}.rda",
        "bytes": len(raw),
        "sha256": sha256,
    }


def norm_freq(df: pd.DataFrame) -> pd.DataFrame:
    x = df.copy()
    x["IDpol"] = pd.to_numeric(x["IDpol"], errors="raise").astype("int64")
    for c in x.columns:
        if c == "IDpol":
            continue
        if c in {"VehBrand", "VehGas", "Area", "Region"}:
            x[c] = x[c].astype(str).str.strip("'")
        else:
            x[c] = pd.to_numeric(x[c], errors="raise")
    return x


def norm_sev(df: pd.DataFrame) -> pd.DataFrame:
    x = df[["IDpol", "ClaimAmount"]].copy()
    x["IDpol"] = pd.to_numeric(x["IDpol"], errors="raise").astype("int64")
    x["ClaimAmount"] = pd.to_numeric(x["ClaimAmount"], errors="raise").astype("float64")
    return x[x["ClaimAmount"] > 0].copy()


def float_bits(x: float) -> int:
    return int(np.asarray([x], dtype=np.float64).view(np.uint64)[0])


def claim_counter(df: pd.DataFrame) -> Counter:
    return Counter((int(i), float_bits(float(a))) for i, a in zip(df["IDpol"], df["ClaimAmount"]))


def claim_digest(counter: Counter) -> str:
    h = hashlib.sha256()
    for (idpol, amount_bits), n in sorted(counter.items()):
        h.update(struct.pack(">qQI", idpol, amount_bits, n))
    return h.hexdigest()


def canonicalize_and_gate(current_freq: pd.DataFrame, current_sev: pd.DataFrame, openml_freq: pd.DataFrame, openml_sev: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    openml_matched = openml_sev[openml_sev["IDpol"].isin(openml_freq["IDpol"])].copy()
    cc = claim_counter(current_sev)
    oc = claim_counter(openml_matched)
    if cc != oc:
        raise RuntimeError("current severity is not exact OpenML matched claim multiset")

    common = sorted(set(current_freq["IDpol"]) & set(openml_freq["IDpol"]))
    ci = current_freq.set_index("IDpol").loc[common].sort_index()
    oi = openml_freq.set_index("IDpol").loc[common].sort_index()
    pairs = pd.DataFrame({"current": ci["Region"].astype(str), "openml": oi["Region"].astype(str)})
    if (pairs.groupby("current")["openml"].nunique() != 1).any() or (pairs.groupby("openml")["current"].nunique() != 1).any():
        raise RuntimeError("Region version change is not a bijective relabel")
    region_map = pairs.drop_duplicates().set_index("current")["openml"].to_dict()

    cf = current_freq.copy()
    cf["Region"] = cf["Region"].map(region_map)
    if cf["Region"].isna().any():
        raise RuntimeError("Region canonicalization left missing values")

    claim_ids = sorted(current_sev["IDpol"].unique())
    cfi = cf.set_index("IDpol").loc[claim_ids].sort_index()
    ofi = openml_freq.set_index("IDpol").loc[claim_ids].sort_index()
    mismatch = {}
    for col in FEATURES:
        a = cfi[col]
        b = ofi[col]
        if pd.api.types.is_numeric_dtype(a) and pd.api.types.is_numeric_dtype(b):
            same = (a.to_numpy() == b.to_numpy()) | (pd.isna(a.to_numpy()) & pd.isna(b.to_numpy()))
        else:
            same = a.astype(str).to_numpy() == b.astype(str).to_numpy()
        mismatch[col] = int((~same).sum())
    if any(mismatch.values()):
        raise RuntimeError(f"severity feature inputs still differ after canonicalization: {mismatch}")

    d = current_sev.merge(cf[["IDpol", *FEATURES]], on="IDpol", how="left", validate="many_to_one")
    if d[list(FEATURES)].isna().any().any():
        raise RuntimeError("current paired publisher data lost severity covariates")
    d["LogDensity"] = np.log(d["Density"].astype(float))

    return d, {
        "pre_fit_reconciliation_run": PRE_FIT_RUN,
        "current_claim_rows": int(len(current_sev)),
        "current_claim_policy_ids": int(current_sev["IDpol"].nunique()),
        "openml_positive_claim_rows": int(len(openml_sev)),
        "openml_orphan_claim_rows": int((~openml_sev["IDpol"].isin(openml_freq["IDpol"])).sum()),
        "exact_claim_multiset_equal_to_openml_matched": True,
        "claim_multiset_sha256": claim_digest(cc),
        "region_mapping_is_bijective": True,
        "region_mapping_current_to_openml": dict(sorted(region_map.items())),
        "severity_feature_mismatches_after_region_canonicalization": mismatch,
        "canonicalization_rule": "map current CASdatasets human-readable Region labels to their unique OpenML Rxx code using the all-policy bijection; no claim outcome or model result is used",
    }


def make_pipe(power: float, alpha: float) -> Pipeline:
    prep = ColumnTransformer([
        ("cat", OneHotEncoder(handle_unknown="ignore", drop="first"), list(CAT)),
        ("num", StandardScaler(), list(NUM)),
    ])
    reg = TweedieRegressor(power=power, alpha=alpha, link="log", max_iter=1000, tol=1e-8)
    return Pipeline([("prep", prep), ("reg", reg)])


def select_alpha(train: pd.DataFrame, valid: pd.DataFrame, power: float) -> tuple[float, list[dict]]:
    Xtr, ytr = train[list(CAT + NUM)], train["ClaimAmount"].to_numpy(float)
    Xva, yva = valid[list(CAT + NUM)], valid["ClaimAmount"].to_numpy(float)
    rows = []
    for alpha in ALPHAS:
        m = make_pipe(power, alpha)
        m.fit(Xtr, ytr)
        p = m.predict(Xva)
        rows.append({"alpha": alpha, "validation_family_deviance": float(mean_tweedie_deviance(yva, p, power=power))})
    best = min(rows, key=lambda r: (r["validation_family_deviance"], r["alpha"]))
    return float(best["alpha"]), rows


def pearson_phi(y: np.ndarray, mu: np.ndarray, power: float) -> float:
    return max(float(np.mean((y - mu) ** 2 / np.maximum(mu, 1e-12) ** power)), 1e-12)


def family_logloss(y: np.ndarray, mu: np.ndarray, phi: float, power: float) -> np.ndarray:
    if power == 2.0:
        ll = gamma_dist.logpdf(y, a=1.0 / phi, scale=phi * mu)
    elif power == 3.0:
        ll = invgauss.logpdf(y, mu=phi * mu, scale=1.0 / phi)
    else:
        raise ValueError(power)
    if not np.isfinite(ll).all():
        raise RuntimeError("non-finite held-out log density")
    return -ll


def family_quantile(mu: np.ndarray, phi: float, power: float, q: float) -> np.ndarray:
    if power == 2.0:
        return gamma_dist.ppf(q, a=1.0 / phi, scale=phi * mu)
    return invgauss.ppf(q, mu=phi * mu, scale=1.0 / phi)


def fit_family(dev_train: pd.DataFrame, inner_valid: pd.DataFrame, dev_all: pd.DataFrame, test: pd.DataFrame, power: float) -> tuple[dict, np.ndarray]:
    alpha, alpha_rows = select_alpha(dev_train, inner_valid, power)
    Xdev, ydev = dev_all[list(CAT + NUM)], dev_all["ClaimAmount"].to_numpy(float)
    Xtest, ytest = test[list(CAT + NUM)], test["ClaimAmount"].to_numpy(float)
    m = make_pipe(power, alpha)
    m.fit(Xdev, ydev)
    mu_dev = m.predict(Xdev)
    mu_test = m.predict(Xtest)
    phi = pearson_phi(ydev, mu_dev, power)
    losses = family_logloss(ytest, mu_test, phi, power)
    q95 = family_quantile(mu_test, phi, power, 0.95)
    q99 = family_quantile(mu_test, phi, power, 0.99)
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


def policy_bootstrap(ids: np.ndarray, gamma_loss: np.ndarray, ig_loss: np.ndarray, seed: int, reps: int = 500) -> dict:
    x = pd.DataFrame({"IDpol": ids, "g": gamma_loss, "ig": ig_loss})
    grp = x.groupby("IDpol", sort=False).agg(g=("g", "sum"), ig=("ig", "sum"), n=("g", "size"))
    g, ig, n = grp["g"].to_numpy(float), grp["ig"].to_numpy(float), grp["n"].to_numpy(float)
    point = float((ig.sum() - g.sum()) / n.sum())
    rng = np.random.default_rng(seed)
    vals = np.empty(reps)
    for b in range(reps):
        idx = rng.integers(0, len(grp), size=len(grp))
        vals[b] = (ig[idx].sum() - g[idx].sum()) / n[idx].sum()
    return {
        "delta_nll_ig_minus_gamma": point,
        "ci95": [float(np.quantile(vals, 0.025)), float(np.quantile(vals, 0.975))],
        "bootstrap_reps": reps,
        "bootstrap_unit": "policy_IDpol",
        "negative_delta_favors_inverse_gaussian": True,
    }


def main() -> None:
    current_freq_raw, freq_src = read_current_rda("freMTPL2freq", EXPECTED_CURRENT_SHA256["frequency"])
    current_sev_raw, sev_src = read_current_rda("freMTPL2sev", EXPECTED_CURRENT_SHA256["severity"])
    current_freq, current_sev = norm_freq(current_freq_raw), norm_sev(current_sev_raw)
    openml_freq = norm_freq(fetch_openml(data_id=FREQ_ID, as_frame=True).data.copy())
    openml_sev = norm_sev(fetch_openml(data_id=SEV_ID, as_frame=True).data.copy())

    d, gate = canonicalize_and_gate(current_freq, current_sev, openml_freq, openml_sev)

    results = []
    all_ids = np.array(sorted(d["IDpol"].unique()))
    for seed in SEEDS:
        dev_ids, test_ids = train_test_split(all_ids, test_size=0.20, random_state=seed)
        tr_ids, va_ids = train_test_split(dev_ids, test_size=0.25, random_state=seed + 1)
        dev_train = d[d["IDpol"].isin(tr_ids)].copy()
        inner_valid = d[d["IDpol"].isin(va_ids)].copy()
        dev_all = d[d["IDpol"].isin(dev_ids)].copy()
        test = d[d["IDpol"].isin(test_ids)].copy()
        gamma, lg = fit_family(dev_train, inner_valid, dev_all, test, 2.0)
        ig, lig = fit_family(dev_train, inner_valid, dev_all, test, 3.0)
        paired = policy_bootstrap(test["IDpol"].to_numpy("int64"), lg, lig, seed + 777)
        results.append({
            "seed": seed,
            "split_counts": {
                "development_policy_ids": int(len(dev_ids)),
                "test_policy_ids": int(len(test_ids)),
                "development_claim_rows": int(len(dev_all)),
                "test_claim_rows": int(len(test)),
            },
            "gamma": gamma,
            "inverse_gaussian": ig,
            "paired_logscore": paired,
        })

    deltas = [r["paired_logscore"]["delta_nll_ig_minus_gamma"] for r in results]
    cis = [r["paired_logscore"]["ci95"] for r in results]
    payload = {
        "status": "FAMILY_COMPARISON_EXECUTED_AFTER_PRE_FIT_DATA_CONTRACT_RESOLUTION",
        "research_question": "On the current paired CASdatasets freMTPL2 claim-level severity population, does Inverse Gaussian outperform Gamma under the previously frozen leakage-safe protocol?",
        "source": {"frequency": freq_src, "severity": sev_src},
        "pre_fit_gate": gate,
        "protocol": {
            "frozen_before_any_target_family_result": True,
            "seeds": list(SEEDS),
            "alphas": list(ALPHAS),
            "outer_split": "80/20 unique policy IDpol",
            "inner_split": "75/25 of development unique policy IDs",
            "primary_target": "raw positive claim-level ClaimAmount; no EUR 200000 cap",
            "features": {"categorical": list(CAT), "numeric": list(NUM), "LogDensity": "log(Density)"},
            "families": {"gamma": 2, "inverse_gaussian": 3},
            "primary_family_discriminator": "held-out family negative log-likelihood; paired policy bootstrap",
            "cross_family_raw_deviance_is_not_winner_criterion": True,
        },
        "results": results,
        "summary": {
            "delta_nll_ig_minus_gamma_by_seed": deltas,
            "mean_delta_nll_ig_minus_gamma": float(np.mean(deltas)),
            "inverse_gaussian_better_point_estimate_seed_count": int(sum(x < 0 for x in deltas)),
            "gamma_better_point_estimate_seed_count": int(sum(x > 0 for x in deltas)),
            "ci95_excludes_zero_in_favor_of_ig_seed_count": int(sum(hi < 0 for lo, hi in cis)),
            "ci95_excludes_zero_in_favor_of_gamma_seed_count": int(sum(lo > 0 for lo, hi in cis)),
        },
        "consumer_boundary": "conditional positive claim-level severity with observed rating covariates; not all legacy orphan claims, not aggregate pure premium, not occurrence-reinsurance or capital validation",
    }
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    payload["receipt_sha256_without_receipt_field"] = hashlib.sha256(canonical).hexdigest()
    OUT.write_text(json.dumps(payload, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2, sort_keys=True, allow_nan=False))


if __name__ == "__main__":
    main()
