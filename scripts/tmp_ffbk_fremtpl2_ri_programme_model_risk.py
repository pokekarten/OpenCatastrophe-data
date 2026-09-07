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
SPLIT_SEEDS = (26090731, 26090747, 26090773)
FREQ_ALPHAS = (0.0, 1e-4, 1e-2)
SEV_ALPHAS = (0.0, 0.01, 0.1, 1.0, 10.0)
CAT = ("VehBrand", "VehGas", "Region", "Area")
NUM = ("VehPower", "VehAge", "DrivAge", "BonusMalus", "LogDensity")
FEATURES = CAT + NUM
QS_SHARE = 0.30
PILOT_POLICIES = 10_000
REPS = 3
WORLDS_PER_REP = 10_000
WORLD_BLOCK = 250
OUT = Path("tmp_ffbk_fremtpl2_ri_programme_model_risk_result.json")


def fetch_rda(name: str) -> tuple[pd.DataFrame, dict]:
    url = f"https://raw.githubusercontent.com/dutangc/CASdatasets/{CAS_SHA}/data/{name}.rda"
    req = urllib.request.Request(url, headers={"User-Agent": "ffbk-ri-programme-model-risk/1"})
    with urllib.request.urlopen(req, timeout=120) as response:
        raw = response.read()
    sha = hashlib.sha256(raw).hexdigest()
    if sha != EXPECTED_SHA256[name]:
        raise RuntimeError(f"{name} SHA256 mismatch: {sha}")
    with tempfile.NamedTemporaryFile(suffix=".rda") as handle:
        handle.write(raw)
        handle.flush()
        obj = rdata.read_rda(handle.name)
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
    for column in x.columns:
        if column in {"VehBrand", "VehGas", "Region", "Area"}:
            x[column] = x[column].astype(str).str.strip("'")
        elif column != "IDpol":
            x[column] = pd.to_numeric(x[column], errors="raise").astype("float64")
    if x["IDpol"].duplicated().any():
        raise RuntimeError("frequency source has duplicate IDpol")
    if (x["Exposure"] <= 0).any() or (x["ClaimNb"] < 0).any():
        raise RuntimeError("invalid exposure/count")
    x["LogDensity"] = np.log(np.maximum(x["Density"].to_numpy(float), 1e-12))
    return x


def norm_sev(df: pd.DataFrame) -> pd.DataFrame:
    x = df.copy()
    x.columns = x.columns.map(str)
    x = x[["IDpol", "ClaimAmount"]].copy()
    x["IDpol"] = pd.to_numeric(x["IDpol"], errors="raise").astype("int64")
    x["ClaimAmount"] = pd.to_numeric(x["ClaimAmount"], errors="raise").astype("float64")
    if (x["ClaimAmount"] <= 0).any():
        raise RuntimeError("non-positive severity")
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
    phi = float(np.mean((y - mu) ** 2 / np.maximum(mu, 1e-12) ** power))
    if not np.isfinite(phi) or phi <= 0:
        raise RuntimeError("invalid Pearson dispersion")
    return phi


def family_nll(y: np.ndarray, mu: np.ndarray, phi: float, power: float) -> float:
    if power == 2.0:
        ll = gamma_dist.logpdf(y, a=1.0 / phi, scale=phi * mu)
    elif power == 3.0:
        ll = invgauss.logpdf(y, mu=phi * mu, scale=1.0 / phi)
    else:
        raise ValueError(power)
    if not np.isfinite(ll).all():
        raise RuntimeError("non-finite severity density")
    return float(-np.mean(ll))


def select_frequency(train: pd.DataFrame, valid: pd.DataFrame) -> tuple[float, list[dict]]:
    ytr = train["ClaimNb"].to_numpy(float) / train["Exposure"].to_numpy(float)
    yva = valid["ClaimNb"].to_numpy(float) / valid["Exposure"].to_numpy(float)
    rows = []
    for alpha in FREQ_ALPHAS:
        model = freq_pipe(alpha)
        model.fit(train[list(FEATURES)], ytr, reg__sample_weight=train["Exposure"].to_numpy(float))
        pred = np.maximum(model.predict(valid[list(FEATURES)]), 1e-12)
        score = mean_poisson_deviance(yva, pred, sample_weight=valid["Exposure"].to_numpy(float))
        rows.append({"alpha": alpha, "validation_poisson_deviance": float(score)})
    best = min(rows, key=lambda row: (row["validation_poisson_deviance"], row["alpha"]))
    return float(best["alpha"]), rows


def select_severity(train: pd.DataFrame, valid: pd.DataFrame, power: float) -> tuple[float, list[dict]]:
    ytr = train["ClaimAmount"].to_numpy(float)
    yva = valid["ClaimAmount"].to_numpy(float)
    rows = []
    for alpha in SEV_ALPHAS:
        model = sev_pipe(power, alpha)
        model.fit(train[list(FEATURES)], ytr)
        mu_tr = np.maximum(model.predict(train[list(FEATURES)]), 1e-12)
        mu_va = np.maximum(model.predict(valid[list(FEATURES)]), 1e-12)
        phi = family_phi(ytr, mu_tr, power)
        rows.append({
            "alpha": alpha,
            "train_pearson_phi": phi,
            "validation_mean_nll": family_nll(yva, mu_va, phi, power),
        })
    best = min(rows, key=lambda row: (row["validation_mean_nll"], row["alpha"]))
    return float(best["alpha"]), rows


def empirical_xol_contract(dev_claims: np.ndarray) -> dict:
    total = float(np.sum(dev_claims))
    limit = float(np.max(dev_claims))
    target = QS_SHARE * total
    lo, hi = 0.0, limit
    for _ in range(100):
        attachment = (lo + hi) / 2.0
        ceded = float(np.minimum(np.maximum(dev_claims - attachment, 0.0), limit).sum())
        if ceded > target:
            lo = attachment
        else:
            hi = attachment
    attachment = (lo + hi) / 2.0
    xol = np.minimum(np.maximum(dev_claims - attachment, 0.0), limit)
    xol_ratio = float(np.sum(xol) / total)
    if abs(xol_ratio - QS_SHARE) > 1e-10:
        raise RuntimeError(f"development pure-loss match failed: {xol_ratio}")
    return {
        "programme_a": {"type": "quota_share", "share": QS_SHARE},
        "programme_b": {
            "type": "per_loss_xol",
            "attachment_eur": attachment,
            "limit_eur": limit,
        },
        "development_empirical_ceded_ratio_a": QS_SHARE,
        "development_empirical_ceded_ratio_b": xol_ratio,
        "development_claim_count": int(len(dev_claims)),
        "development_claim_total_eur": total,
    }


def left_var(x: np.ndarray, q: float) -> float:
    s = np.sort(x)
    idx = int(np.ceil(q * len(s))) - 1
    idx = min(max(idx, 0), len(s) - 1)
    return float(s[idx])


def es_above_var(x: np.ndarray, q: float) -> float:
    v = left_var(x, q)
    tail = x[x >= v]
    return float(np.mean(tail))


def summarize_worlds(gross: np.ndarray, ceded_qs: np.ndarray, ceded_xol: np.ndarray) -> dict:
    retained_qs = gross - ceded_qs
    retained_xol = gross - ceded_xol
    if np.max(np.abs(gross - ceded_qs - retained_qs)) > 1e-8:
        raise RuntimeError("QS conservation failure")
    if np.max(np.abs(gross - ceded_xol - retained_xol)) > 1e-8:
        raise RuntimeError("XoL conservation failure")
    gross_var = left_var(gross, 0.995)
    gross_es = es_above_var(gross, 0.995)

    def programme(ceded: np.ndarray, retained: np.ndarray) -> dict:
        expected_ceded = float(np.mean(ceded))
        retained_var = left_var(retained, 0.995)
        retained_es = es_above_var(retained, 0.995)
        return {
            "expected_ceded_pure_loss_eur": expected_ceded,
            "expected_retained_loss_eur": float(np.mean(retained)),
            "retained_var_995_eur": retained_var,
            "retained_es_995_eur": retained_es,
            "var995_relief_per_expected_ceded": float((gross_var - retained_var) / expected_ceded),
            "es995_relief_per_expected_ceded": float((gross_es - retained_es) / expected_ceded),
        }

    a = programme(ceded_qs, retained_qs)
    b = programme(ceded_xol, retained_xol)
    return {
        "worlds": int(len(gross)),
        "gross": {
            "expected_loss_eur": float(np.mean(gross)),
            "var_995_eur": gross_var,
            "es_995_eur": gross_es,
        },
        "programme_a_quota_share": a,
        "programme_b_per_loss_xol": b,
        "b_minus_a": {
            "expected_ceded_pure_loss_eur": float(b["expected_ceded_pure_loss_eur"] - a["expected_ceded_pure_loss_eur"]),
            "retained_var_995_eur": float(b["retained_var_995_eur"] - a["retained_var_995_eur"]),
            "retained_es_995_eur": float(b["retained_es_995_eur"] - a["retained_es_995_eur"]),
            "var995_relief_efficiency": float(b["var995_relief_per_expected_ceded"] - a["var995_relief_per_expected_ceded"]),
            "es995_relief_efficiency": float(b["es995_relief_per_expected_ceded"] - a["es995_relief_per_expected_ceded"]),
            "negative_retained_delta_favors_xol": True,
        },
        "lower_retained_var995": "programme_b_per_loss_xol" if b["retained_var_995_eur"] < a["retained_var_995_eur"] else "programme_a_quota_share",
        "lower_retained_es995": "programme_b_per_loss_xol" if b["retained_es_995_eur"] < a["retained_es_995_eur"] else "programme_a_quota_share",
    }


def simulate_models(
    lam: np.ndarray,
    models: dict[str, tuple[np.ndarray, float, str]],
    attachment: float,
    limit: float,
    seed: int,
) -> dict:
    total_lambda = float(np.sum(lam))
    if total_lambda <= 0:
        raise RuntimeError("non-positive pilot lambda")
    weights = lam / total_lambda
    all_results: dict[str, dict[str, list[np.ndarray]]] = {
        name: {"gross": [], "ceded_qs": [], "ceded_xol": []} for name in models
    }
    rep_summaries: dict[str, list[dict]] = {name: [] for name in models}

    for rep in range(REPS):
        common_rng = np.random.default_rng(seed + rep * 10_000)
        sev_rngs = {
            name: np.random.default_rng(seed + rep * 10_000 + 100 + j * 1000)
            for j, name in enumerate(models)
        }
        rep_arrays = {
            name: {
                "gross": np.empty(WORLDS_PER_REP),
                "ceded_qs": np.empty(WORLDS_PER_REP),
                "ceded_xol": np.empty(WORLDS_PER_REP),
            }
            for name in models
        }
        for lo in range(0, WORLDS_PER_REP, WORLD_BLOCK):
            hi = min(WORLDS_PER_REP, lo + WORLD_BLOCK)
            m = hi - lo
            counts = common_rng.poisson(total_lambda, size=m)
            total_claims = int(np.sum(counts))
            if total_claims == 0:
                for name in models:
                    for key in rep_arrays[name]:
                        rep_arrays[name][key][lo:hi] = 0.0
                continue
            policy_idx = common_rng.choice(len(lam), size=total_claims, replace=True, p=weights)
            world_idx = np.repeat(np.arange(m), counts)
            for name, (mu, phi, family) in models.items():
                rng = sev_rngs[name]
                selected_mu = mu[policy_idx]
                if family == "gamma":
                    severity = rng.gamma(shape=1.0 / phi, scale=phi * selected_mu)
                elif family == "ig":
                    severity = rng.wald(mean=selected_mu, scale=np.full(total_claims, 1.0 / phi))
                else:
                    raise ValueError(family)
                if not np.isfinite(severity).all() or (severity <= 0).any():
                    raise RuntimeError(f"invalid severity draw for {name}")
                gross = np.bincount(world_idx, weights=severity, minlength=m)
                xol_claim = np.minimum(np.maximum(severity - attachment, 0.0), limit)
                ceded_xol = np.bincount(world_idx, weights=xol_claim, minlength=m)
                ceded_qs = QS_SHARE * gross
                rep_arrays[name]["gross"][lo:hi] = gross
                rep_arrays[name]["ceded_qs"][lo:hi] = ceded_qs
                rep_arrays[name]["ceded_xol"][lo:hi] = ceded_xol
        for name in models:
            rep_summary = summarize_worlds(
                rep_arrays[name]["gross"],
                rep_arrays[name]["ceded_qs"],
                rep_arrays[name]["ceded_xol"],
            )
            rep_summaries[name].append(rep_summary)
            for key in rep_arrays[name]:
                all_results[name][key].append(rep_arrays[name][key])

    out = {}
    for name in models:
        gross = np.concatenate(all_results[name]["gross"])
        ceded_qs = np.concatenate(all_results[name]["ceded_qs"])
        ceded_xol = np.concatenate(all_results[name]["ceded_xol"])
        combined = summarize_worlds(gross, ceded_qs, ceded_xol)
        deltas_var = np.array([r["b_minus_a"]["retained_var_995_eur"] for r in rep_summaries[name]])
        deltas_es = np.array([r["b_minus_a"]["retained_es_995_eur"] for r in rep_summaries[name]])
        combined["replicate_diagnostics"] = {
            "replicates": REPS,
            "worlds_per_rep": WORLDS_PER_REP,
            "b_minus_a_retained_var995_by_rep_eur": deltas_var.tolist(),
            "b_minus_a_retained_es995_by_rep_eur": deltas_es.tolist(),
            "same_var_ranking_all_reps": bool(np.all(np.sign(deltas_var) == np.sign(deltas_var[0]))),
            "same_es_ranking_all_reps": bool(np.all(np.sign(deltas_es) == np.sign(deltas_es[0]))),
        }
        out[name] = combined
    return out


def run_split(freq: pd.DataFrame, sevx: pd.DataFrame, seed: int) -> dict:
    all_ids = freq["IDpol"].to_numpy("int64")
    dev_ids, test_ids = train_test_split(all_ids, test_size=0.20, random_state=seed)
    tr_ids, va_ids = train_test_split(dev_ids, test_size=0.25, random_state=seed + 1)
    tr_set, va_set, dev_set = set(tr_ids), set(va_ids), set(dev_ids)

    ftr = freq[freq["IDpol"].isin(tr_set)].copy()
    fva = freq[freq["IDpol"].isin(va_set)].copy()
    fdev = freq[freq["IDpol"].isin(dev_set)].copy()
    strn = sevx[sevx["IDpol"].isin(tr_set)].copy()
    sval = sevx[sevx["IDpol"].isin(va_set)].copy()
    sdev = sevx[sevx["IDpol"].isin(dev_set)].copy()
    if len(strn) == 0 or len(sval) == 0:
        raise RuntimeError("empty severity split")

    freq_alpha, freq_grid = select_frequency(ftr, fva)
    gamma_alpha, gamma_grid = select_severity(strn, sval, 2.0)
    ig_alpha, ig_grid = select_severity(strn, sval, 3.0)

    fm = freq_pipe(freq_alpha)
    fm.fit(
        fdev[list(FEATURES)],
        fdev["ClaimNb"].to_numpy(float) / fdev["Exposure"].to_numpy(float),
        reg__sample_weight=fdev["Exposure"].to_numpy(float),
    )
    gm = sev_pipe(2.0, gamma_alpha)
    im = sev_pipe(3.0, ig_alpha)
    gm.fit(sdev[list(FEATURES)], sdev["ClaimAmount"].to_numpy(float))
    im.fit(sdev[list(FEATURES)], sdev["ClaimAmount"].to_numpy(float))

    ydev = sdev["ClaimAmount"].to_numpy(float)
    mu_g_dev = np.maximum(gm.predict(sdev[list(FEATURES)]), 1e-12)
    mu_i_dev = np.maximum(im.predict(sdev[list(FEATURES)]), 1e-12)
    phi_g = family_phi(ydev, mu_g_dev, 2.0)
    phi_i = family_phi(ydev, mu_i_dev, 3.0)
    phi_i_matched = family_phi(ydev, mu_g_dev, 3.0)

    contract = empirical_xol_contract(ydev)

    pilot_rng = np.random.default_rng(seed + 500_000)
    pilot_ids = np.sort(pilot_rng.choice(test_ids, size=PILOT_POLICIES, replace=False))
    pilot = freq[freq["IDpol"].isin(set(pilot_ids))].copy().sort_values("IDpol")
    if len(pilot) != PILOT_POLICIES:
        raise RuntimeError("pilot identity mismatch")
    rate = np.maximum(fm.predict(pilot[list(FEATURES)]), 1e-12)
    lam = rate * pilot["Exposure"].to_numpy(float)
    mu_g = np.maximum(gm.predict(pilot[list(FEATURES)]), 1e-12)
    mu_i = np.maximum(im.predict(pilot[list(FEATURES)]), 1e-12)

    model_metrics = simulate_models(
        lam,
        {
            "poisson_gamma": (mu_g, phi_g, "gamma"),
            "poisson_inverse_gaussian": (mu_i, phi_i, "ig"),
            "poisson_inverse_gaussian_mean_matched": (mu_g, phi_i_matched, "ig"),
        },
        contract["programme_b"]["attachment_eur"],
        contract["programme_b"]["limit_eur"],
        seed + 1_000_000,
    )

    rankings = {
        name: {
            "lower_retained_var995": metrics["lower_retained_var995"],
            "lower_retained_es995": metrics["lower_retained_es995"],
        }
        for name, metrics in model_metrics.items()
    }
    return {
        "seed": seed,
        "split_counts": {
            "development_policies": int(len(dev_ids)),
            "test_policies": int(len(test_ids)),
            "pilot_policies": int(len(pilot)),
            "development_positive_claims": int(len(sdev)),
        },
        "selected": {
            "frequency_alpha": freq_alpha,
            "gamma_alpha": gamma_alpha,
            "inverse_gaussian_alpha": ig_alpha,
            "gamma_phi": phi_g,
            "inverse_gaussian_phi": phi_i,
            "inverse_gaussian_mean_matched_phi": phi_i_matched,
        },
        "validation_grids": {
            "frequency": freq_grid,
            "gamma": gamma_grid,
            "inverse_gaussian": ig_grid,
        },
        "contract": contract,
        "pilot": {
            "id_selection": "seeded outcome-blind sample from final test policy IDs",
            "expected_claim_count_per_world": float(np.sum(lam)),
            "exposure_sum": float(np.sum(pilot["Exposure"])),
        },
        "model_metrics": model_metrics,
        "rankings": rankings,
    }


def main() -> None:
    freq_raw, freq_source = fetch_rda("freMTPL2freq")
    sev_raw, sev_source = fetch_rda("freMTPL2sev")
    freq = norm_freq(freq_raw)
    sev = norm_sev(sev_raw)
    matched = sev[sev["IDpol"].isin(freq["IDpol"])].copy()
    if len(matched) != len(sev):
        raise RuntimeError("orphan severity row")
    if int(round(freq["ClaimNb"].sum())) != len(matched):
        raise RuntimeError("ClaimNb/severity-row mismatch")
    sevx = matched.merge(freq[["IDpol", *FEATURES]], on="IDpol", how="left", validate="many_to_one")
    if sevx[list(FEATURES)].isna().any().any():
        raise RuntimeError("severity feature join produced missing values")

    splits = [run_split(freq, sevx, seed) for seed in SPLIT_SEEDS]
    model_names = list(splits[0]["model_metrics"])
    summary = {}
    for model in model_names:
        var_winners = [s["rankings"][model]["lower_retained_var995"] for s in splits]
        es_winners = [s["rankings"][model]["lower_retained_es995"] for s in splits]
        var_deltas = [s["model_metrics"][model]["b_minus_a"]["retained_var_995_eur"] for s in splits]
        es_deltas = [s["model_metrics"][model]["b_minus_a"]["retained_es_995_eur"] for s in splits]
        expected_ceded_deltas = [s["model_metrics"][model]["b_minus_a"]["expected_ceded_pure_loss_eur"] for s in splits]
        summary[model] = {
            "var995_winners": var_winners,
            "es995_winners": es_winners,
            "xol_wins_var995_splits": int(sum(w == "programme_b_per_loss_xol" for w in var_winners)),
            "xol_wins_es995_splits": int(sum(w == "programme_b_per_loss_xol" for w in es_winners)),
            "mean_b_minus_a_retained_var995_eur": float(np.mean(var_deltas)),
            "mean_b_minus_a_retained_es995_eur": float(np.mean(es_deltas)),
            "mean_b_minus_a_expected_ceded_eur": float(np.mean(expected_ceded_deltas)),
        }
    cross_model = {
        "same_var995_winner_gamma_vs_ig_all_splits": all(
            s["rankings"]["poisson_gamma"]["lower_retained_var995"]
            == s["rankings"]["poisson_inverse_gaussian"]["lower_retained_var995"]
            for s in splits
        ),
        "same_es995_winner_gamma_vs_ig_all_splits": all(
            s["rankings"]["poisson_gamma"]["lower_retained_es995"]
            == s["rankings"]["poisson_inverse_gaussian"]["lower_retained_es995"]
            for s in splits
        ),
        "same_var995_winner_gamma_vs_mean_matched_ig_all_splits": all(
            s["rankings"]["poisson_gamma"]["lower_retained_var995"]
            == s["rankings"]["poisson_inverse_gaussian_mean_matched"]["lower_retained_var995"]
            for s in splits
        ),
        "same_es995_winner_gamma_vs_mean_matched_ig_all_splits": all(
            s["rankings"]["poisson_gamma"]["lower_retained_es995"]
            == s["rankings"]["poisson_inverse_gaussian_mean_matched"]["lower_retained_es995"]
            for s in splits
        ),
    }

    result = {
        "question": "Does a development-pure-cost-matched quota-share versus per-loss XoL programme ordering remain stable across Gamma and inverse-Gaussian severity models on a fixed freMTPL2 pilot?",
        "classification": "retrospective real-data-calibrated predictive decision sensitivity; no market pricing or empirical RI outcome validation",
        "source": {"frequency": freq_source, "severity": sev_source},
        "data_integrity": {
            "policies": int(len(freq)),
            "positive_claim_rows": int(len(sev)),
            "claimnb_sum": int(round(freq["ClaimNb"].sum())),
        },
        "protocol": {
            "split_seeds": list(SPLIT_SEEDS),
            "outer_split": "80% development / 20% test by policy ID",
            "development_split": "75% train / 25% validation",
            "pilot_policy_selection": "10000 outcome-blind policy IDs sampled from each test split after model/contract freeze",
            "programme_a": "30% quota share per loss",
            "programme_b": "per-loss XoL; attachment solved on development raw claims so empirical ceded pure-loss ratio equals 30%; finite limit equals development maximum observed claim",
            "model_families": ["Poisson-Gamma", "Poisson-Inverse-Gaussian", "Poisson-Inverse-Gaussian mean-matched to Gamma"],
            "worlds_per_model_split": REPS * WORLDS_PER_REP,
            "replicates": REPS,
            "worlds_per_rep": WORLDS_PER_REP,
            "primary_decision_consumers": ["retained VaR99.5", "retained ES99.5"],
            "secondary": ["expected ceded pure loss", "tail relief per expected ceded pure loss"],
            "pricing_boundary": "expected ceded loss is a pure-loss cost proxy only; no market quote/loading/reinstatement/counterparty/cash timing",
        },
        "splits": splits,
        "summary": summary,
        "cross_model_ranking_stability": cross_model,
        "runtime": {
            "python": platform.python_version(),
            "numpy": np.__version__,
            "pandas": pd.__version__,
            "scipy": scipy.__version__,
            "sklearn": sklearn.__version__,
            "rdata": getattr(rdata, "__version__", "unknown"),
            "platform": platform.platform(),
        },
    }
    OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "result_file": str(OUT),
        "cross_model_ranking_stability": cross_model,
        "summary": summary,
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
