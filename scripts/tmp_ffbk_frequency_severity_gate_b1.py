#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import platform
import tempfile
import urllib.request
from pathlib import Path

import numpy as np
import pandas as pd
import rdata
import scipy
import sklearn
from scipy.stats import gamma as gamma_dist
from scipy.stats import invgauss
from sklearn.compose import ColumnTransformer
from sklearn.linear_model import TweedieRegressor
from sklearn.metrics import mean_tweedie_deviance
from sklearn.model_selection import KFold, train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

CAS_SHA = "227fb56b8734bdb7c0327a41180e01d2ddaeaf26"
EXPECTED_SHA256 = {
    "freMTPL2freq": "82c8598513d9fa78226b6c7d271a9940eca4b8083e9e32320a75d377bdfe15a3",
    "freMTPL2sev": "78e6e5016ae046603b37e88ff8ad8ca327f5d59f827c1f75d140388de09b14b3",
}
BASE_CAT = ("VehBrand", "VehGas", "Region", "Area")
BASE_NUM = ("VehPower", "VehAge", "DrivAge", "BonusMalus", "LogDensity")
SOURCE_FEATURES = ("VehPower", "VehAge", "DrivAge", "BonusMalus", "VehBrand", "VehGas", "Area", "Density", "Region", "ClaimNb")
ALPHAS = (0.0, 0.01, 0.1, 1.0, 10.0)
OUTER_SEED = 26090801
BOOTSTRAP_SEED = 26090891
N_FOLDS = 5
BOOTSTRAP_REPS = 1000
OUT = Path("ffbk_frequency_severity_gate_b1_result.json")


def fetch_bytes(url: str) -> tuple[bytes, str]:
    req = urllib.request.Request(url, headers={"User-Agent": "ffbk-research-gate-b1/1"})
    with urllib.request.urlopen(req, timeout=120) as response:
        raw = response.read()
    return raw, hashlib.sha256(raw).hexdigest()


def read_rda(name: str) -> tuple[pd.DataFrame, dict]:
    url = f"https://raw.githubusercontent.com/dutangc/CASdatasets/{CAS_SHA}/data/{name}.rda"
    raw, sha = fetch_bytes(url)
    expected = EXPECTED_SHA256[name]
    if sha != expected:
        raise RuntimeError(f"{name} SHA256 mismatch: got {sha}, expected {expected}")
    with tempfile.NamedTemporaryFile(suffix=".rda") as f:
        f.write(raw)
        f.flush()
        obj = rdata.read_rda(f.name)
    if name not in obj:
        raise RuntimeError(f"{name} object absent from RData: {list(obj)}")
    return pd.DataFrame(obj[name]).copy(), {
        "repository": "dutangc/CASdatasets",
        "commit": CAS_SHA,
        "path": f"data/{name}.rda",
        "bytes": len(raw),
        "sha256": sha,
    }


def normalize_freq(df: pd.DataFrame) -> pd.DataFrame:
    x = df.copy()
    x.columns = x.columns.map(str)
    x["IDpol"] = pd.to_numeric(x["IDpol"], errors="raise").astype("int64")
    for c in x.columns:
        if c == "IDpol":
            continue
        if c in {"VehBrand", "VehGas", "Area", "Region"}:
            x[c] = x[c].astype(str).str.strip("'")
        else:
            x[c] = pd.to_numeric(x[c], errors="raise")
    if x["IDpol"].duplicated().any():
        raise RuntimeError("frequency source has duplicate IDpol")
    return x


def normalize_sev(df: pd.DataFrame) -> pd.DataFrame:
    x = df.copy()
    x.columns = x.columns.map(str)
    x = x[["IDpol", "ClaimAmount"]].copy()
    x["IDpol"] = pd.to_numeric(x["IDpol"], errors="raise").astype("int64")
    x["ClaimAmount"] = pd.to_numeric(x["ClaimAmount"], errors="raise").astype("float64")
    return x[x["ClaimAmount"] > 0].copy()


def build_claim_data(freq: pd.DataFrame, sev: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    missing_ids = sorted(set(sev["IDpol"]) - set(freq["IDpol"]))
    if missing_ids:
        raise RuntimeError(f"referential integrity failed: {len(missing_ids)} severity IDs absent from frequency")
    keep = ["IDpol", *SOURCE_FEATURES]
    d = sev.merge(freq[keep], on="IDpol", how="left", validate="many_to_one")
    if d[list(SOURCE_FEATURES)].isna().any().any():
        raise RuntimeError("claim rows lost frequency/rating-state fields")
    if (d["ClaimNb"] < 1).any():
        raise RuntimeError("positive severity row linked to ClaimNb < 1")
    d["LogDensity"] = np.log(d["Density"].astype(float))
    if not np.isfinite(d["LogDensity"]).all():
        raise RuntimeError("non-finite LogDensity")
    d["ClaimCountBand"] = np.where(d["ClaimNb"] >= 3, "3+", d["ClaimNb"].astype(int).astype(str))
    if not set(d["ClaimCountBand"]).issubset({"1", "2", "3+"}):
        raise RuntimeError(f"unexpected claim-count bands: {sorted(set(d['ClaimCountBand']))}")
    by_policy = d.groupby("IDpol", sort=False).agg(
        observed_claim_rows=("ClaimAmount", "size"),
        source_claim_count=("ClaimNb", "first"),
        count_band=("ClaimCountBand", "first"),
    )
    by_policy["source_minus_observed"] = by_policy["source_claim_count"] - by_policy["observed_claim_rows"]
    support = {}
    for band in ("1", "2", "3+"):
        z = d[d["ClaimCountBand"] == band]
        support[band] = {
            "policy_ids": int(z["IDpol"].nunique()),
            "claim_rows": int(len(z)),
            "claim_amount_sum": float(z["ClaimAmount"].sum()),
            "claim_amount_mean": float(z["ClaimAmount"].mean()) if len(z) else None,
        }
    receipt = {
        "claim_rows": int(len(d)),
        "claim_policy_ids": int(d["IDpol"].nunique()),
        "count_support": support,
        "policy_claim_count_vs_positive_severity_row_count": {
            "policies_equal": int((by_policy["source_minus_observed"] == 0).sum()),
            "policies_unequal": int((by_policy["source_minus_observed"] != 0).sum()),
            "min_source_minus_observed": float(by_policy["source_minus_observed"].min()),
            "max_source_minus_observed": float(by_policy["source_minus_observed"].max()),
        },
    }
    return d, receipt


def make_pipe(power: float, alpha: float, with_count: bool) -> Pipeline:
    cats = list(BASE_CAT) + (["ClaimCountBand"] if with_count else [])
    prep = ColumnTransformer([
        ("cat", OneHotEncoder(handle_unknown="error", drop="first"), cats),
        ("num", StandardScaler(), list(BASE_NUM)),
    ])
    reg = TweedieRegressor(power=power, alpha=alpha, link="log", max_iter=2000, tol=1e-9)
    return Pipeline([("prep", prep), ("reg", reg)])


def feature_columns(with_count: bool) -> list[str]:
    return list(BASE_CAT + BASE_NUM) + (["ClaimCountBand"] if with_count else [])


def choose_alpha(inner_train: pd.DataFrame, inner_valid: pd.DataFrame, power: float) -> tuple[float, list[dict]]:
    Xtr = inner_train[feature_columns(False)]
    ytr = inner_train["ClaimAmount"].to_numpy(float)
    Xva = inner_valid[feature_columns(False)]
    yva = inner_valid["ClaimAmount"].to_numpy(float)
    rows = []
    for alpha in ALPHAS:
        m = make_pipe(power, alpha, False)
        m.fit(Xtr, ytr)
        pred = m.predict(Xva)
        rows.append({
            "alpha": alpha,
            "validation_family_deviance": float(mean_tweedie_deviance(yva, pred, power=power)),
        })
    best = min(rows, key=lambda r: (r["validation_family_deviance"], r["alpha"]))
    return float(best["alpha"]), rows


def pearson_phi(y: np.ndarray, mu: np.ndarray, power: float) -> float:
    return max(float(np.mean((y - mu) ** 2 / np.maximum(mu, 1e-12) ** power)), 1e-12)


def nll(y: np.ndarray, mu: np.ndarray, phi: float, power: float) -> np.ndarray:
    if power == 2.0:
        ll = gamma_dist.logpdf(y, a=1.0 / phi, scale=phi * mu)
    elif power == 3.0:
        ll = invgauss.logpdf(y, mu=phi * mu, scale=1.0 / phi)
    else:
        raise ValueError(power)
    if not np.isfinite(ll).all():
        raise RuntimeError("non-finite held-out log density")
    return -ll


def qpred(mu: np.ndarray, phi: float, power: float, q: float) -> np.ndarray:
    if power == 2.0:
        return gamma_dist.ppf(q, a=1.0 / phi, scale=phi * mu)
    return invgauss.ppf(q, mu=phi * mu, scale=1.0 / phi)


def count_effects(model: Pipeline) -> dict[str, float]:
    names = model.named_steps["prep"].get_feature_names_out()
    coefs = model.named_steps["reg"].coef_
    out = {}
    for name, coef in zip(names, coefs):
        if "ClaimCountBand_" in name:
            level = name.split("ClaimCountBand_", 1)[1]
            out[level] = float(np.exp(coef))
    return out


def fit_model(train: pd.DataFrame, test: pd.DataFrame, power: float, alpha: float, with_count: bool) -> tuple[dict, np.ndarray]:
    Xtr = train[feature_columns(with_count)]
    ytr = train["ClaimAmount"].to_numpy(float)
    Xte = test[feature_columns(with_count)]
    yte = test["ClaimAmount"].to_numpy(float)
    model = make_pipe(power, alpha, with_count)
    model.fit(Xtr, ytr)
    mu_tr = model.predict(Xtr)
    mu_te = model.predict(Xte)
    phi = pearson_phi(ytr, mu_tr, power)
    losses = nll(yte, mu_te, phi, power)
    q95 = qpred(mu_te, phi, power, 0.95)
    q99 = qpred(mu_te, phi, power, 0.99)
    return {
        "alpha": alpha,
        "pearson_phi_train": phi,
        "mean_nll_test": float(np.mean(losses)),
        "actual_over_predicted_mean": float(np.sum(yte) / np.sum(mu_te)),
        "q95_exceedance_rate_test": float(np.mean(yte > q95)),
        "q99_exceedance_rate_test": float(np.mean(yte > q99)),
        "count_mean_relativities_vs_N1": count_effects(model) if with_count else {},
    }, losses


def paired_policy_bootstrap(frame: pd.DataFrame, delta_col: str, seed: int) -> dict:
    grp = frame.groupby("IDpol", sort=False).agg(delta_sum=(delta_col, "sum"), n=(delta_col, "size"))
    point = float(grp["delta_sum"].sum() / grp["n"].sum())
    rng = np.random.default_rng(seed)
    ds = grp["delta_sum"].to_numpy(float)
    ns = grp["n"].to_numpy(float)
    vals = np.empty(BOOTSTRAP_REPS)
    for b in range(BOOTSTRAP_REPS):
        idx = rng.integers(0, len(grp), size=len(grp))
        vals[b] = ds[idx].sum() / ns[idx].sum()
    return {
        "delta_nll_M1_minus_M0": point,
        "ci95": [float(np.quantile(vals, 0.025)), float(np.quantile(vals, 0.975))],
        "bootstrap_reps": BOOTSTRAP_REPS,
        "bootstrap_unit": "policy_IDpol",
        "negative_delta_favors_M1_count_conditioning": True,
        "policy_ids": int(len(grp)),
        "claim_rows": int(grp["n"].sum()),
    }


def main() -> None:
    freq_raw, freq_source = read_rda("freMTPL2freq")
    sev_raw, sev_source = read_rda("freMTPL2sev")
    freq, sev = normalize_freq(freq_raw), normalize_sev(sev_raw)
    d, source_gate = build_claim_data(freq, sev)

    unique_ids = np.array(sorted(d["IDpol"].unique()), dtype=np.int64)
    outer = KFold(n_splits=N_FOLDS, shuffle=True, random_state=OUTER_SEED)
    family_specs = {"gamma": 2.0, "inverse_gaussian": 3.0}
    fold_results = {name: [] for name in family_specs}
    held = []

    for fold, (train_ix, test_ix) in enumerate(outer.split(unique_ids), start=1):
        train_ids = unique_ids[train_ix]
        test_ids = unique_ids[test_ix]
        inner_train_ids, inner_valid_ids = train_test_split(
            train_ids, test_size=0.20, random_state=OUTER_SEED + fold
        )
        train = d[d["IDpol"].isin(train_ids)].copy()
        test = d[d["IDpol"].isin(test_ids)].copy()
        inner_train = d[d["IDpol"].isin(inner_train_ids)].copy()
        inner_valid = d[d["IDpol"].isin(inner_valid_ids)].copy()

        missing_train_bands = {"1", "2", "3+"} - set(train["ClaimCountBand"])
        if missing_train_bands:
            raise RuntimeError(f"fold {fold} M1 training lacks count bands: {missing_train_bands}")

        fold_frame = test[["IDpol", "ClaimCountBand", "ClaimAmount"]].copy()
        fold_frame["fold"] = fold

        for family_name, power in family_specs.items():
            alpha, alpha_path = choose_alpha(inner_train, inner_valid, power)
            m0, l0 = fit_model(train, test, power, alpha, False)
            m1, l1 = fit_model(train, test, power, alpha, True)
            fold_frame[f"{family_name}_m0_nll"] = l0
            fold_frame[f"{family_name}_m1_nll"] = l1
            fold_frame[f"{family_name}_delta"] = l1 - l0
            fold_results[family_name].append({
                "fold": fold,
                "train_policy_ids": int(len(train_ids)),
                "test_policy_ids": int(len(test_ids)),
                "train_claim_rows": int(len(train)),
                "test_claim_rows": int(len(test)),
                "alpha_selected_on_M0_inner_validation": alpha,
                "alpha_selection_path": alpha_path,
                "M0": m0,
                "M1": m1,
                "mean_delta_nll_M1_minus_M0": float(np.mean(l1 - l0)),
            })
        held.append(fold_frame)

    heldout = pd.concat(held, ignore_index=True)
    results = {}
    for fi, family_name in enumerate(family_specs):
        delta_col = f"{family_name}_delta"
        pooled = paired_policy_bootstrap(heldout, delta_col, BOOTSTRAP_SEED + fi * 1000)
        bands = {}
        for bi, band in enumerate(("1", "2", "3+")):
            z = heldout[heldout["ClaimCountBand"] == band]
            bands[band] = paired_policy_bootstrap(z, delta_col, BOOTSTRAP_SEED + fi * 1000 + bi + 1)
        fold_deltas = [float(x["mean_delta_nll_M1_minus_M0"]) for x in fold_results[family_name]]
        effect_paths = {
            "N2_vs_N1": [float(x["M1"]["count_mean_relativities_vs_N1"].get("2", np.nan)) for x in fold_results[family_name]],
            "N3plus_vs_N1": [float(x["M1"]["count_mean_relativities_vs_N1"].get("3+", np.nan)) for x in fold_results[family_name]],
        }
        results[family_name] = {
            "folds": fold_results[family_name],
            "pooled_policy_bootstrap": pooled,
            "by_count_band_policy_bootstrap": bands,
            "fold_delta_nll_M1_minus_M0": fold_deltas,
            "negative_delta_fold_count": int(sum(x < 0 for x in fold_deltas)),
            "count_mean_relativity_paths": effect_paths,
        }

    payload = {
        "status": "REAL_FREMTP2_GATE_B1_EXECUTED",
        "research_question": (
            "On current-source freMTPL2 individual positive claims, after controlling pre-claim rating state, "
            "does realized policy claim count add held-out severity information once policy-average aggregation is removed?"
        ),
        "source": {"frequency": freq_source, "severity": sev_source},
        "source_gate": source_gate,
        "protocol": {
            "target": "raw uncapped positive individual ClaimAmount",
            "split_unit": "policy IDpol",
            "outer_split": f"{N_FOLDS}-fold shuffled KFold over unique policy IDs",
            "outer_seed": OUTER_SEED,
            "families": {"gamma": "Tweedie variance power 2", "inverse_gaussian": "Tweedie variance power 3"},
            "M0": "pre-claim rating state only",
            "M1": "same family, rating basis and alpha as M0 plus categorical ClaimNb bands 1/2/3+",
            "base_categorical_features": list(BASE_CAT),
            "base_numeric_features": list(BASE_NUM),
            "alpha_grid": list(ALPHAS),
            "alpha_selection": "M0-only inner validation family deviance; selected alpha frozen for paired M0/M1 fit",
            "dispersion": "Pearson phi estimated on each outer-training fit only",
            "primary_discriminator": "held-out individual-claim NLL delta M1-M0 with paired policy bootstrap",
            "required_count_diagnostics": ["1", "2", "3+"],
            "bootstrap_reps": BOOTSTRAP_REPS,
            "interpretation": {
                "both_families_stable_negative_score_delta": "H0 weakened; still no prospective pricing promotion",
                "neither_family_stable_negative_score_delta": "H1 weakened at claim level",
                "family_specific": "MIXED; severity-law misspecification remains live",
                "sparse_multi_claim_support": "INCONCLUSIVE for that count region"
            }
        },
        "results": results,
        "software": {
            "python": platform.python_version(),
            "numpy": np.__version__,
            "pandas": pd.__version__,
            "scipy": scipy.__version__,
            "scikit_learn": sklearn.__version__,
            "rdata": getattr(rdata, "__version__", "unknown")
        }
    }
    OUT.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": payload["status"],
        "source_gate": payload["source_gate"],
        "gamma": payload["results"]["gamma"]["pooled_policy_bootstrap"],
        "inverse_gaussian": payload["results"]["inverse_gaussian"]["pooled_policy_bootstrap"]
    }, indent=2))


if __name__ == "__main__":
    main()
