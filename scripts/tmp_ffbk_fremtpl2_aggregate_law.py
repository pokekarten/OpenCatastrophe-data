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
from sklearn.linear_model import PoissonRegressor, TweedieRegressor
from sklearn.metrics import mean_poisson_deviance
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

CAS_SHA = "227fb56b8734bdb7c0327a41180e01d2ddaeaf26"
EXPECTED_SHA256 = {
    "freMTPL2freq": "82c8598513d9fa78226b6c7d271a9940eca4b8083e9e32320a75d377bdfe15a3",
    "freMTPL2sev": "78e6e5016ae046603b37e88ff8ad8ca327f5d59f827c1f75d140388de09b14b3",
}
SEED = 26090731
MC_DRAWS = 128
FREQ_ALPHAS = (0.0, 1e-4, 1e-2)
SEV_ALPHAS = (0.0, 0.01, 0.1, 1.0, 10.0)
CAT = ("VehBrand", "VehGas", "Region", "Area")
NUM = ("VehPower", "VehAge", "DrivAge", "BonusMalus", "LogDensity")
FEATURES = CAT + NUM
OUT = Path("tmp_ffbk_aggregate_law_result.json")


def fetch_rda(name: str) -> tuple[pd.DataFrame, dict]:
    url = f"https://raw.githubusercontent.com/dutangc/CASdatasets/{CAS_SHA}/data/{name}.rda"
    req = urllib.request.Request(url, headers={"User-Agent": "ffbk-aggregate-law-study/1"})
    with urllib.request.urlopen(req, timeout=120) as r:
        raw = r.read()
    sha = hashlib.sha256(raw).hexdigest()
    if sha != EXPECTED_SHA256[name]:
        raise RuntimeError(f"{name} SHA256 mismatch: {sha}")
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
        "sha256": sha,
        "bytes": len(raw),
    }


def norm_freq(df: pd.DataFrame) -> pd.DataFrame:
    x = df.copy()
    x.columns = x.columns.map(str)
    x["IDpol"] = pd.to_numeric(x["IDpol"], errors="raise").astype("int64")
    for c in x.columns:
        if c in {"VehBrand", "VehGas", "Region", "Area"}:
            x[c] = x[c].astype(str).str.strip("'")
        elif c != "IDpol":
            x[c] = pd.to_numeric(x[c], errors="raise").astype("float64")
    if x["IDpol"].duplicated().any():
        raise RuntimeError("frequency source has duplicate IDpol")
    if (x["Exposure"] <= 0).any():
        raise RuntimeError("non-positive exposure")
    if (x["ClaimNb"] < 0).any():
        raise RuntimeError("negative ClaimNb")
    x["LogDensity"] = np.log(np.maximum(x["Density"].to_numpy(float), 1e-12))
    return x


def norm_sev(df: pd.DataFrame) -> pd.DataFrame:
    x = df.copy()
    x.columns = x.columns.map(str)
    x = x[["IDpol", "ClaimAmount"]].copy()
    x["IDpol"] = pd.to_numeric(x["IDpol"], errors="raise").astype("int64")
    x["ClaimAmount"] = pd.to_numeric(x["ClaimAmount"], errors="raise").astype("float64")
    if (x["ClaimAmount"] <= 0).any():
        raise RuntimeError("non-positive ClaimAmount in freMTPL2sev")
    return x


def preprocessor() -> ColumnTransformer:
    return ColumnTransformer([
        ("cat", OneHotEncoder(handle_unknown="ignore", drop="first"), list(CAT)),
        ("num", StandardScaler(), list(NUM)),
    ])


def freq_pipe(alpha: float) -> Pipeline:
    return Pipeline([
        ("prep", preprocessor()),
        ("reg", PoissonRegressor(alpha=alpha, max_iter=500, tol=1e-8)),
    ])


def sev_pipe(power: float, alpha: float) -> Pipeline:
    return Pipeline([
        ("prep", preprocessor()),
        ("reg", TweedieRegressor(power=power, alpha=alpha, link="log", max_iter=1000, tol=1e-8)),
    ])


def family_phi(y: np.ndarray, mu: np.ndarray, power: float) -> float:
    v = np.mean((y - mu) ** 2 / np.maximum(mu, 1e-12) ** power)
    if not np.isfinite(v) or v <= 0:
        raise RuntimeError("invalid Pearson phi")
    return float(v)


def family_nll(y: np.ndarray, mu: np.ndarray, phi: float, power: float) -> float:
    if power == 2.0:
        ll = gamma_dist.logpdf(y, a=1.0 / phi, scale=phi * mu)
    elif power == 3.0:
        ll = invgauss.logpdf(y, mu=phi * mu, scale=1.0 / phi)
    else:
        raise ValueError(power)
    if not np.isfinite(ll).all():
        raise RuntimeError("non-finite severity log density")
    return float(-np.mean(ll))


def select_frequency(train: pd.DataFrame, valid: pd.DataFrame) -> tuple[float, list[dict]]:
    ytr = train["ClaimNb"].to_numpy(float) / train["Exposure"].to_numpy(float)
    yva = valid["ClaimNb"].to_numpy(float) / valid["Exposure"].to_numpy(float)
    rows = []
    for alpha in FREQ_ALPHAS:
        m = freq_pipe(alpha)
        m.fit(train[list(FEATURES)], ytr, reg__sample_weight=train["Exposure"].to_numpy(float))
        p = np.maximum(m.predict(valid[list(FEATURES)]), 1e-12)
        score = mean_poisson_deviance(
            yva, p, sample_weight=valid["Exposure"].to_numpy(float)
        )
        rows.append({"alpha": alpha, "validation_poisson_deviance": float(score)})
    best = min(rows, key=lambda r: (r["validation_poisson_deviance"], r["alpha"]))
    return float(best["alpha"]), rows


def select_severity(train: pd.DataFrame, valid: pd.DataFrame, power: float) -> tuple[float, list[dict]]:
    ytr = train["ClaimAmount"].to_numpy(float)
    yva = valid["ClaimAmount"].to_numpy(float)
    rows = []
    for alpha in SEV_ALPHAS:
        m = sev_pipe(power, alpha)
        m.fit(train[list(FEATURES)], ytr)
        mu_tr = np.maximum(m.predict(train[list(FEATURES)]), 1e-12)
        mu_va = np.maximum(m.predict(valid[list(FEATURES)]), 1e-12)
        phi = family_phi(ytr, mu_tr, power)
        rows.append({
            "alpha": alpha,
            "train_pearson_phi": phi,
            "validation_mean_nll": family_nll(yva, mu_va, phi, power),
        })
    best = min(rows, key=lambda r: (r["validation_mean_nll"], r["alpha"]))
    return float(best["alpha"]), rows


def sample_crps(draws: np.ndarray, y: np.ndarray) -> np.ndarray:
    m = draws.shape[1]
    first = np.mean(np.abs(draws - y[:, None]), axis=1)
    s = np.sort(draws, axis=1)
    coef = (2 * np.arange(1, m + 1) - m - 1).astype(float)
    second = np.sum(s * coef[None, :], axis=1) / (m * m)
    return first - second


def simulate_scores(
    lam: np.ndarray,
    mu_g: np.ndarray,
    phi_g: float,
    mu_i: np.ndarray,
    phi_i: float,
    mu_i_matched: np.ndarray,
    phi_i_matched: float,
    y: np.ndarray,
    thresholds: tuple[float, float],
    seed: int,
) -> dict:
    n = len(y)
    crps_g = np.empty(n)
    crps_i = np.empty(n)
    crps_im = np.empty(n)
    probs = {
        "gamma": [np.empty(n), np.empty(n)],
        "ig": [np.empty(n), np.empty(n)],
        "ig_mean_matched": [np.empty(n), np.empty(n)],
    }
    rng_count = np.random.default_rng(seed)
    rng_g = np.random.default_rng(seed + 1)
    rng_i = np.random.default_rng(seed + 2)
    rng_im = np.random.default_rng(seed + 3)
    chunk = 5000
    for lo in range(0, n, chunk):
        hi = min(n, lo + chunk)
        lc = lam[lo:hi]
        counts = rng_count.poisson(lc[:, None], size=(hi - lo, MC_DRAWS))
        dg = np.zeros_like(counts, dtype=float)
        di = np.zeros_like(counts, dtype=float)
        dim = np.zeros_like(counts, dtype=float)
        mask = counts > 0
        nn = counts[mask].astype(float)

        mug = np.broadcast_to(mu_g[lo:hi, None], counts.shape)[mask]
        mui = np.broadcast_to(mu_i[lo:hi, None], counts.shape)[mask]
        muim = np.broadcast_to(mu_i_matched[lo:hi, None], counts.shape)[mask]

        dg[mask] = rng_g.gamma(shape=nn / phi_g, scale=phi_g * mug)
        di[mask] = rng_i.wald(mean=nn * mui, scale=(nn * nn) / phi_i)
        dim[mask] = rng_im.wald(mean=nn * muim, scale=(nn * nn) / phi_i_matched)

        if not (np.isfinite(dg).all() and np.isfinite(di).all() and np.isfinite(dim).all()):
            raise RuntimeError("non-finite aggregate simulation")

        yc = y[lo:hi]
        crps_g[lo:hi] = sample_crps(dg, yc)
        crps_i[lo:hi] = sample_crps(di, yc)
        crps_im[lo:hi] = sample_crps(dim, yc)
        for j, t in enumerate(thresholds):
            probs["gamma"][j][lo:hi] = np.mean(dg > t, axis=1)
            probs["ig"][j][lo:hi] = np.mean(di > t, axis=1)
            probs["ig_mean_matched"][j][lo:hi] = np.mean(dim > t, axis=1)

    def metrics(name: str, crps: np.ndarray, pred_mean: np.ndarray) -> dict:
        out = {
            "mean_crps_eur": float(np.mean(crps)),
            "mean_crps_positive_observed_policy_eur": float(np.mean(crps[y > 0])),
            "observed_over_predicted_aggregate_mean": float(np.sum(y) / np.sum(pred_mean)),
            "predicted_total_loss": float(np.sum(pred_mean)),
            "observed_total_loss": float(np.sum(y)),
        }
        for j, t in enumerate(thresholds):
            event = (y > t).astype(float)
            pr = probs[name][j]
            out[f"tail_{j+1}_threshold_eur"] = float(t)
            out[f"tail_{j+1}_brier"] = float(np.mean((pr - event) ** 2))
            out[f"tail_{j+1}_observed_rate"] = float(np.mean(event))
            out[f"tail_{j+1}_predicted_rate"] = float(np.mean(pr))
        return out

    pred_g = lam * mu_g
    pred_i = lam * mu_i
    pred_im = lam * mu_i_matched
    delta = crps_i - crps_g
    delta_im = crps_im - crps_g
    rng_b = np.random.default_rng(seed + 99)
    reps = 400
    boot = np.empty((reps, 2))
    for b in range(reps):
        idx = rng_b.integers(0, n, size=n)
        boot[b, 0] = np.mean(delta[idx])
        boot[b, 1] = np.mean(delta_im[idx])

    mg = float(np.mean(crps_g))
    mi = float(np.mean(crps_i))
    mim = float(np.mean(crps_im))
    return {
        "gamma": metrics("gamma", crps_g, pred_g),
        "inverse_gaussian": metrics("ig", crps_i, pred_i),
        "inverse_gaussian_mean_matched_to_gamma": metrics("ig_mean_matched", crps_im, pred_im),
        "paired_crps": {
            "ig_minus_gamma_eur": float(np.mean(delta)),
            "ig_minus_gamma_relative_pct": float(100.0 * (mi / mg - 1.0)),
            "ig_minus_gamma_bootstrap_ci95_eur": [
                float(np.quantile(boot[:, 0], 0.025)),
                float(np.quantile(boot[:, 0], 0.975)),
            ],
            "mean_matched_ig_minus_gamma_eur": float(np.mean(delta_im)),
            "mean_matched_ig_minus_gamma_relative_pct": float(100.0 * (mim / mg - 1.0)),
            "mean_matched_ig_minus_gamma_bootstrap_ci95_eur": [
                float(np.quantile(boot[:, 1], 0.025)),
                float(np.quantile(boot[:, 1], 0.975)),
            ],
            "bootstrap_reps": reps,
            "bootstrap_unit": "policy",
            "negative_delta_favors_inverse_gaussian": True,
        },
    }


def main() -> None:
    freq_raw, freq_source = fetch_rda("freMTPL2freq")
    sev_raw, sev_source = fetch_rda("freMTPL2sev")
    freq = norm_freq(freq_raw)
    sev = norm_sev(sev_raw)

    matched = sev[sev["IDpol"].isin(freq["IDpol"])].copy()
    orphan_rows = int(len(sev) - len(matched))
    claim_count_sum = int(round(freq["ClaimNb"].sum()))
    if abs(freq["ClaimNb"].sum() - claim_count_sum) > 1e-9:
        raise RuntimeError("ClaimNb is not integer-valued in aggregate")
    if claim_count_sum != len(matched):
        raise RuntimeError(
            f"ClaimNb/severity-row mismatch: ClaimNb sum={claim_count_sum}, matched severity={len(matched)}, orphan={orphan_rows}"
        )

    total = matched.groupby("IDpol", sort=False)["ClaimAmount"].sum()
    freq["AnnualLoss"] = freq["IDpol"].map(total).fillna(0.0).astype(float)
    sevx = matched.merge(freq[["IDpol", *FEATURES]], on="IDpol", how="left", validate="many_to_one")
    if sevx[list(FEATURES)].isna().any().any():
        raise RuntimeError("severity covariate join produced missing values")

    all_ids = freq["IDpol"].to_numpy("int64")
    dev_ids, test_ids = train_test_split(all_ids, test_size=0.20, random_state=SEED)
    tr_ids, va_ids = train_test_split(dev_ids, test_size=0.25, random_state=SEED + 1)
    trset, vaset, devset, teset = map(set, (tr_ids, va_ids, dev_ids, test_ids))
    ftr = freq[freq["IDpol"].isin(trset)].copy()
    fva = freq[freq["IDpol"].isin(vaset)].copy()
    fdev = freq[freq["IDpol"].isin(devset)].copy()
    ftest = freq[freq["IDpol"].isin(teset)].copy()
    strn = sevx[sevx["IDpol"].isin(trset)].copy()
    sval = sevx[sevx["IDpol"].isin(vaset)].copy()
    sdev = sevx[sevx["IDpol"].isin(devset)].copy()

    freq_alpha, freq_sel = select_frequency(ftr, fva)
    fm = freq_pipe(freq_alpha)
    ydev_rate = fdev["ClaimNb"].to_numpy(float) / fdev["Exposure"].to_numpy(float)
    fm.fit(fdev[list(FEATURES)], ydev_rate, reg__sample_weight=fdev["Exposure"].to_numpy(float))
    freq_rate_test = np.maximum(fm.predict(ftest[list(FEATURES)]), 1e-12)
    lam_test = freq_rate_test * ftest["Exposure"].to_numpy(float)

    g_alpha, g_sel = select_severity(strn, sval, 2.0)
    i_alpha, i_sel = select_severity(strn, sval, 3.0)
    gm = sev_pipe(2.0, g_alpha)
    im = sev_pipe(3.0, i_alpha)
    ysev_dev = sdev["ClaimAmount"].to_numpy(float)
    gm.fit(sdev[list(FEATURES)], ysev_dev)
    im.fit(sdev[list(FEATURES)], ysev_dev)
    mu_g_dev = np.maximum(gm.predict(sdev[list(FEATURES)]), 1e-12)
    mu_i_dev = np.maximum(im.predict(sdev[list(FEATURES)]), 1e-12)
    phi_g = family_phi(ysev_dev, mu_g_dev, 2.0)
    phi_i = family_phi(ysev_dev, mu_i_dev, 3.0)
    phi_i_matched = family_phi(ysev_dev, mu_g_dev, 3.0)

    Xtest = ftest[list(FEATURES)]
    mu_g_test = np.maximum(gm.predict(Xtest), 1e-12)
    mu_i_test = np.maximum(im.predict(Xtest), 1e-12)
    ytest = ftest["AnnualLoss"].to_numpy(float)
    thresholds = (
        float(np.quantile(fdev["AnnualLoss"].to_numpy(float), 0.99)),
        float(np.quantile(fdev["AnnualLoss"].to_numpy(float), 0.995)),
    )
    if not (thresholds[0] > 0 and thresholds[1] >= thresholds[0]):
        raise RuntimeError(f"invalid development tail thresholds: {thresholds}")

    scores = simulate_scores(
        lam_test,
        mu_g_test,
        phi_g,
        mu_i_test,
        phi_i,
        mu_g_test,
        phi_i_matched,
        ytest,
        thresholds,
        SEED + 1000,
    )

    result = {
        "schema": "ffbk-fremtpl2-aggregate-law-v1",
        "research_question": "Does inverse-Gaussian severity improve the full annual policy aggregate-loss law over Gamma severity when frequency is held to the same fitted Poisson model?",
        "design": {
            "development_test_split": "policy ID, 80/20; development internally 75/25 for hyperparameter selection",
            "seed": SEED,
            "monte_carlo_draws_per_test_policy": MC_DRAWS,
            "frequency_held_common": True,
            "baseline": "Poisson frequency x Gamma severity",
            "challenger": "same Poisson frequency x inverse-Gaussian severity",
            "controlled_challenger": "same Poisson frequency x inverse-Gaussian law using Gamma-fitted conditional severity mean; only dispersion/law changes",
            "primary_score": "policy-level sample CRPS on annual aggregate loss",
            "tail_scores": "Brier scores at development-sample 99.0% and 99.5% annual-loss thresholds",
            "outcome_leakage_rule": "test outcomes are not used for model selection, dispersion estimation, or tail-threshold definition",
        },
        "source": {
            "frequency": freq_source,
            "severity": sev_source,
            "policy_rows": int(len(freq)),
            "severity_rows": int(len(sev)),
            "matched_severity_rows": int(len(matched)),
            "orphan_severity_rows": orphan_rows,
            "claimnb_sum": claim_count_sum,
        },
        "split_counts": {
            "train_policies": int(len(ftr)),
            "validation_policies": int(len(fva)),
            "development_policies": int(len(fdev)),
            "test_policies": int(len(ftest)),
            "train_claim_rows": int(len(strn)),
            "validation_claim_rows": int(len(sval)),
            "development_claim_rows": int(len(sdev)),
            "test_positive_loss_policies": int(np.sum(ytest > 0)),
        },
        "frequency_fit": {
            "selected_alpha": freq_alpha,
            "selection": freq_sel,
            "test_observed_claims_over_predicted": float(
                ftest["ClaimNb"].sum() / np.sum(lam_test)
            ),
        },
        "severity_fit": {
            "gamma": {
                "selected_alpha": g_alpha,
                "selection": g_sel,
                "development_phi": phi_g,
                "development_mean_nll": family_nll(ysev_dev, mu_g_dev, phi_g, 2.0),
            },
            "inverse_gaussian": {
                "selected_alpha": i_alpha,
                "selection": i_sel,
                "development_phi": phi_i,
                "development_mean_nll": family_nll(ysev_dev, mu_i_dev, phi_i, 3.0),
            },
            "inverse_gaussian_mean_matched_to_gamma": {
                "development_phi": phi_i_matched,
                "development_mean_nll": family_nll(ysev_dev, mu_g_dev, phi_i_matched, 3.0),
            },
        },
        "scores": scores,
        "runtime": {
            "python": platform.python_version(),
            "numpy": np.__version__,
            "pandas": pd.__version__,
            "scipy": scipy.__version__,
            "scikit_learn": sklearn.__version__,
            "rdata": getattr(rdata, "__version__", "unknown"),
        },
        "limitations": [
            "single public French motor benchmark; no temporal holdout",
            "conditional independence of frequency and severity is imposed",
            "Monte Carlo CRPS uses finite predictive draws",
            "policy-level annual loss is sparse and does not validate portfolio dependence",
            "mean-matched inverse-Gaussian dispersion is Pearson-estimated, not full maximum likelihood",
        ],
    }
    OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result["scores"]["paired_crps"], indent=2))


if __name__ == "__main__":
    main()
