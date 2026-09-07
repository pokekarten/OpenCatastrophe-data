#!/usr/bin/env python3
from __future__ import annotations

import json
import math
import platform
from pathlib import Path

import numpy as np
import pandas as pd
import scipy
import sklearn
from sklearn.model_selection import train_test_split

import tmp_ffbk_fremtpl2_aggregate_law as base

OUT = Path("tmp_ffbk_fremtpl2_tweedie_ri_result.json")
OUTER_SEEDS = (26090731, 26090747, 26090773)
DIRECT_POWERS = (1.3, 1.5, 1.7, 1.9)
DIRECT_ALPHAS = (0.0, 1e-4, 1e-2)
SELECTION_DRAWS = 64
FINAL_DRAWS = 128
BOOT_REPS = 400


def exposure_phi(y_rate: np.ndarray, mu_rate: np.ndarray, exposure: np.ndarray, p: float) -> float:
    phi = np.mean(exposure * (y_rate - mu_rate) ** 2 / np.maximum(mu_rate, 1e-12) ** p)
    if not np.isfinite(phi) or phi <= 0:
        raise RuntimeError(f"invalid direct Tweedie phi: {phi}")
    return float(phi)


def direct_chunk_draws(
    mu_rate: np.ndarray,
    exposure: np.ndarray,
    phi: float,
    p: float,
    draws: int,
    rng: np.random.Generator,
) -> np.ndarray:
    lam = exposure * np.maximum(mu_rate, 1e-12) ** (2.0 - p) / (phi * (2.0 - p))
    if not np.isfinite(lam).all() or (lam < 0).any():
        raise RuntimeError("invalid direct Tweedie Poisson intensity")
    n = rng.poisson(lam[:, None], size=(len(mu_rate), draws))
    out = np.zeros_like(n, dtype=float)
    mask = n > 0
    if mask.any():
        shape_unit = (2.0 - p) / (p - 1.0)
        scale_policy = phi * (p - 1.0) * np.maximum(mu_rate, 1e-12) ** (p - 1.0)
        shapes = n[mask].astype(float) * shape_unit
        scales = np.broadcast_to(scale_policy[:, None], n.shape)[mask]
        out[mask] = rng.gamma(shape=shapes, scale=scales)
    if not np.isfinite(out).all():
        raise RuntimeError("non-finite direct Tweedie draw")
    return out


def validation_direct_crps(
    model,
    train: pd.DataFrame,
    valid: pd.DataFrame,
    p: float,
    seed: int,
) -> tuple[float, float]:
    ytr = train["AnnualLoss"].to_numpy(float) / train["Exposure"].to_numpy(float)
    wtr = train["Exposure"].to_numpy(float)
    model.fit(train[list(base.FEATURES)], ytr, reg__sample_weight=wtr)
    mu_tr = np.maximum(model.predict(train[list(base.FEATURES)]), 1e-12)
    phi = exposure_phi(ytr, mu_tr, wtr, p)

    mu_va = np.maximum(model.predict(valid[list(base.FEATURES)]), 1e-12)
    wva = valid["Exposure"].to_numpy(float)
    yva = valid["AnnualLoss"].to_numpy(float)
    rng = np.random.default_rng(seed)
    crps = np.empty(len(valid))
    chunk = 5000
    for lo in range(0, len(valid), chunk):
        hi = min(len(valid), lo + chunk)
        d = direct_chunk_draws(mu_va[lo:hi], wva[lo:hi], phi, p, SELECTION_DRAWS, rng)
        crps[lo:hi] = base.sample_crps(d, yva[lo:hi])
    return float(np.mean(crps)), phi


def fit_direct(train: pd.DataFrame, valid: pd.DataFrame, dev: pd.DataFrame, outer_seed: int) -> dict:
    selection = []
    idx = 0
    for p in DIRECT_POWERS:
        for alpha in DIRECT_ALPHAS:
            m = base.sev_pipe(p, alpha)
            mean_crps, phi_train = validation_direct_crps(
                m, train, valid, p, outer_seed + 20000 + idx * 101
            )
            selection.append({
                "p": p,
                "alpha": alpha,
                "validation_mean_crps_eur": mean_crps,
                "train_exposure_pearson_phi": phi_train,
            })
            idx += 1
    best = min(selection, key=lambda r: (r["validation_mean_crps_eur"], r["p"], r["alpha"]))
    p = float(best["p"])
    alpha = float(best["alpha"])
    model = base.sev_pipe(p, alpha)
    ydev_rate = dev["AnnualLoss"].to_numpy(float) / dev["Exposure"].to_numpy(float)
    wdev = dev["Exposure"].to_numpy(float)
    model.fit(dev[list(base.FEATURES)], ydev_rate, reg__sample_weight=wdev)
    mu_dev = np.maximum(model.predict(dev[list(base.FEATURES)]), 1e-12)
    phi_dev = exposure_phi(ydev_rate, mu_dev, wdev, p)
    return {
        "model": model,
        "p": p,
        "alpha": alpha,
        "phi": phi_dev,
        "selection": selection,
        "power_grid_boundary": bool(p in (min(DIRECT_POWERS), max(DIRECT_POWERS))),
        "alpha_grid_boundary": bool(alpha in (min(DIRECT_ALPHAS), max(DIRECT_ALPHAS))),
    }


def factorized_draws(
    counts: np.ndarray,
    mu: np.ndarray,
    phi: float,
    family: str,
    rng: np.random.Generator,
) -> np.ndarray:
    out = np.zeros_like(counts, dtype=float)
    mask = counts > 0
    if not mask.any():
        return out
    nn = counts[mask].astype(float)
    mub = np.broadcast_to(mu[:, None], counts.shape)[mask]
    if family == "gamma":
        out[mask] = rng.gamma(shape=nn / phi, scale=phi * mub)
    elif family == "ig":
        out[mask] = rng.wald(mean=nn * mub, scale=(nn * nn) / phi)
    else:
        raise ValueError(family)
    if not np.isfinite(out).all():
        raise RuntimeError(f"non-finite factorized {family} draw")
    return out


def final_scores(
    lam: np.ndarray,
    mu_g: np.ndarray,
    phi_g: float,
    mu_i: np.ndarray,
    phi_i: float,
    mu_d: np.ndarray,
    exposure: np.ndarray,
    phi_d: float,
    p_d: float,
    y: np.ndarray,
    thresholds: tuple[float, float],
    attachment: float,
    seed: int,
) -> dict:
    names = ("poisson_gamma", "poisson_ig", "direct_tweedie")
    crps_loss = {n: np.empty(len(y)) for n in names}
    crps_ceded = {n: np.empty(len(y)) for n in names}
    tail_probs = {n: [np.empty(len(y)), np.empty(len(y))] for n in names}
    ceded_mean = {n: np.empty(len(y)) for n in names}

    rng_count = np.random.default_rng(seed)
    rng_g = np.random.default_rng(seed + 1)
    rng_i = np.random.default_rng(seed + 2)
    rng_d = np.random.default_rng(seed + 3)
    limit = 3.0 * attachment
    observed_ceded = np.clip(y - attachment, 0.0, limit)

    chunk = 5000
    for lo in range(0, len(y), chunk):
        hi = min(len(y), lo + chunk)
        counts = rng_count.poisson(lam[lo:hi, None], size=(hi - lo, FINAL_DRAWS))
        draws = {
            "poisson_gamma": factorized_draws(counts, mu_g[lo:hi], phi_g, "gamma", rng_g),
            "poisson_ig": factorized_draws(counts, mu_i[lo:hi], phi_i, "ig", rng_i),
            "direct_tweedie": direct_chunk_draws(
                mu_d[lo:hi], exposure[lo:hi], phi_d, p_d, FINAL_DRAWS, rng_d
            ),
        }
        yc = y[lo:hi]
        occ = observed_ceded[lo:hi]
        for name, d in draws.items():
            crps_loss[name][lo:hi] = base.sample_crps(d, yc)
            cd = np.clip(d - attachment, 0.0, limit)
            crps_ceded[name][lo:hi] = base.sample_crps(cd, occ)
            ceded_mean[name][lo:hi] = np.mean(cd, axis=1)
            for j, t in enumerate(thresholds):
                tail_probs[name][j][lo:hi] = np.mean(d > t, axis=1)

    pred_loss_mean = {
        "poisson_gamma": lam * mu_g,
        "poisson_ig": lam * mu_i,
        "direct_tweedie": exposure * mu_d,
    }
    metrics = {}
    for name in names:
        m = {
            "mean_loss_crps_eur": float(np.mean(crps_loss[name])),
            "mean_ceded_crps_eur": float(np.mean(crps_ceded[name])),
            "observed_over_predicted_loss_mean": float(np.sum(y) / np.sum(pred_loss_mean[name])),
            "predicted_total_loss": float(np.sum(pred_loss_mean[name])),
            "observed_total_loss": float(np.sum(y)),
            "predicted_total_ceded": float(np.sum(ceded_mean[name])),
            "observed_total_ceded": float(np.sum(observed_ceded)),
            "observed_over_predicted_ceded": float(
                np.sum(observed_ceded) / max(np.sum(ceded_mean[name]), 1e-12)
            ),
            "predicted_total_retained": float(np.sum(pred_loss_mean[name]) - np.sum(ceded_mean[name])),
            "observed_total_retained": float(np.sum(y) - np.sum(observed_ceded)),
        }
        for j, t in enumerate(thresholds):
            event = (y > t).astype(float)
            pr = tail_probs[name][j]
            m[f"tail_{j+1}_threshold_eur"] = float(t)
            m[f"tail_{j+1}_brier"] = float(np.mean((pr - event) ** 2))
            m[f"tail_{j+1}_observed_rate"] = float(np.mean(event))
            m[f"tail_{j+1}_predicted_rate"] = float(np.mean(pr))
        metrics[name] = m

    rng_b = np.random.default_rng(seed + 99)
    pairs = (
        ("direct_tweedie", "poisson_gamma"),
        ("direct_tweedie", "poisson_ig"),
        ("poisson_ig", "poisson_gamma"),
    )
    contrasts = {}
    for a, b in pairs:
        dl = crps_loss[a] - crps_loss[b]
        dc = crps_ceded[a] - crps_ceded[b]
        boot = np.empty((BOOT_REPS, 2))
        for r in range(BOOT_REPS):
            ix = rng_b.integers(0, len(y), size=len(y))
            boot[r, 0] = np.mean(dl[ix])
            boot[r, 1] = np.mean(dc[ix])
        contrasts[f"{a}_minus_{b}"] = {
            "loss_crps_delta_eur": float(np.mean(dl)),
            "loss_crps_ci95_eur": [float(np.quantile(boot[:, 0], .025)), float(np.quantile(boot[:, 0], .975))],
            "ceded_crps_delta_eur": float(np.mean(dc)),
            "ceded_crps_ci95_eur": [float(np.quantile(boot[:, 1], .025)), float(np.quantile(boot[:, 1], .975))],
            "negative_favors_first_named_model": True,
        }

    return {
        "models": metrics,
        "paired_contrasts": contrasts,
        "layer": {"attachment_eur": attachment, "limit_eur": limit, "form": "3A xs A on annual policy loss"},
    }


def exposure_diagnostics(
    dev: pd.DataFrame,
    test: pd.DataFrame,
    predictions: dict[str, np.ndarray],
) -> dict:
    cuts = np.quantile(dev["Exposure"].to_numpy(float), [0.25, 0.5, 0.75])
    w = test["Exposure"].to_numpy(float)
    y = test["AnnualLoss"].to_numpy(float)
    bins = np.digitize(w, cuts, right=True)
    out = {"development_exposure_quartile_cuts": [float(x) for x in cuts], "models": {}}
    for name, pred in predictions.items():
        rows = []
        for b in range(4):
            mask = bins == b
            rows.append({
                "bin": b,
                "n": int(mask.sum()),
                "observed_total": float(y[mask].sum()),
                "predicted_total": float(pred[mask].sum()),
                "observed_over_predicted": float(y[mask].sum() / max(pred[mask].sum(), 1e-12)),
            })
        out["models"][name] = rows
    return out


def run_seed(freq: pd.DataFrame, sevx: pd.DataFrame, outer_seed: int) -> dict:
    all_ids = freq["IDpol"].to_numpy("int64")
    dev_ids, test_ids = train_test_split(all_ids, test_size=0.20, random_state=outer_seed)
    tr_ids, va_ids = train_test_split(dev_ids, test_size=0.25, random_state=outer_seed + 1)
    trset, vaset, devset, teset = map(set, (tr_ids, va_ids, dev_ids, test_ids))
    ftr = freq[freq["IDpol"].isin(trset)].copy()
    fva = freq[freq["IDpol"].isin(vaset)].copy()
    fdev = freq[freq["IDpol"].isin(devset)].copy()
    ftest = freq[freq["IDpol"].isin(teset)].copy()
    strn = sevx[sevx["IDpol"].isin(trset)].copy()
    sval = sevx[sevx["IDpol"].isin(vaset)].copy()
    sdev = sevx[sevx["IDpol"].isin(devset)].copy()

    freq_alpha, freq_sel = base.select_frequency(ftr, fva)
    fm = base.freq_pipe(freq_alpha)
    ydev_rate = fdev["ClaimNb"].to_numpy(float) / fdev["Exposure"].to_numpy(float)
    fm.fit(fdev[list(base.FEATURES)], ydev_rate, reg__sample_weight=fdev["Exposure"].to_numpy(float))
    freq_rate_test = np.maximum(fm.predict(ftest[list(base.FEATURES)]), 1e-12)
    exposure_test = ftest["Exposure"].to_numpy(float)
    lam_test = freq_rate_test * exposure_test

    g_alpha, g_sel = base.select_severity(strn, sval, 2.0)
    i_alpha, i_sel = base.select_severity(strn, sval, 3.0)
    gm = base.sev_pipe(2.0, g_alpha)
    im = base.sev_pipe(3.0, i_alpha)
    ysev_dev = sdev["ClaimAmount"].to_numpy(float)
    gm.fit(sdev[list(base.FEATURES)], ysev_dev)
    im.fit(sdev[list(base.FEATURES)], ysev_dev)
    mu_g_dev = np.maximum(gm.predict(sdev[list(base.FEATURES)]), 1e-12)
    mu_i_dev = np.maximum(im.predict(sdev[list(base.FEATURES)]), 1e-12)
    phi_g = base.family_phi(ysev_dev, mu_g_dev, 2.0)
    phi_i = base.family_phi(ysev_dev, mu_i_dev, 3.0)
    mu_g_test = np.maximum(gm.predict(ftest[list(base.FEATURES)]), 1e-12)
    mu_i_test = np.maximum(im.predict(ftest[list(base.FEATURES)]), 1e-12)

    direct = fit_direct(ftr, fva, fdev, outer_seed)
    mu_d_test = np.maximum(direct["model"].predict(ftest[list(base.FEATURES)]), 1e-12)

    ytest = ftest["AnnualLoss"].to_numpy(float)
    ydev = fdev["AnnualLoss"].to_numpy(float)
    thresholds = (float(np.quantile(ydev, .99)), float(np.quantile(ydev, .995)))
    attachment = thresholds[0]
    scores = final_scores(
        lam_test, mu_g_test, phi_g, mu_i_test, phi_i,
        mu_d_test, exposure_test, direct["phi"], direct["p"],
        ytest, thresholds, attachment, outer_seed + 1000,
    )

    pred = {
        "poisson_gamma": lam_test * mu_g_test,
        "poisson_ig": lam_test * mu_i_test,
        "direct_tweedie": exposure_test * mu_d_test,
    }
    exp_diag = exposure_diagnostics(fdev, ftest, pred)

    result = {
        "outer_seed": outer_seed,
        "counts": {
            "train_policies": int(len(ftr)), "validation_policies": int(len(fva)),
            "development_policies": int(len(fdev)), "test_policies": int(len(ftest)),
            "development_claim_rows": int(len(sdev)), "test_positive_loss_policies": int((ytest > 0).sum()),
        },
        "frequency": {"selected_alpha": freq_alpha, "selection": freq_sel},
        "gamma": {"selected_alpha": g_alpha, "selection": g_sel, "development_phi": phi_g},
        "inverse_gaussian": {"selected_alpha": i_alpha, "selection": i_sel, "development_phi": phi_i},
        "direct_tweedie": {
            "selected_power": direct["p"], "selected_alpha": direct["alpha"],
            "development_exposure_pearson_phi": direct["phi"],
            "power_grid_boundary": direct["power_grid_boundary"],
            "alpha_grid_boundary": direct["alpha_grid_boundary"],
            "selection": direct["selection"],
        },
        "scores": scores,
        "exposure_diagnostics": exp_diag,
    }
    print("SPLIT_SUMMARY " + json.dumps({
        "seed": outer_seed,
        "direct_p": direct["p"],
        "direct_alpha": direct["alpha"],
        "direct_phi": direct["phi"],
        "loss_crps": {k: v["mean_loss_crps_eur"] for k, v in scores["models"].items()},
        "ceded_crps": {k: v["mean_ceded_crps_eur"] for k, v in scores["models"].items()},
        "q995_brier": {k: v["tail_2_brier"] for k, v in scores["models"].items()},
        "ceded_ae": {k: v["observed_over_predicted_ceded"] for k, v in scores["models"].items()},
    }, sort_keys=True))
    return result


def main() -> None:
    freq_raw, freq_source = base.fetch_rda("freMTPL2freq")
    sev_raw, sev_source = base.fetch_rda("freMTPL2sev")
    freq = base.norm_freq(freq_raw)
    sev = base.norm_sev(sev_raw)
    matched = sev[sev["IDpol"].isin(freq["IDpol"])].copy()
    orphan_rows = int(len(sev) - len(matched))
    claim_count_sum = int(round(freq["ClaimNb"].sum()))
    if claim_count_sum != len(matched) or orphan_rows != 0:
        raise RuntimeError(f"source identity mismatch claim_count={claim_count_sum} matched={len(matched)} orphan={orphan_rows}")
    total = matched.groupby("IDpol", sort=False)["ClaimAmount"].sum()
    freq["AnnualLoss"] = freq["IDpol"].map(total).fillna(0.0).astype(float)
    sevx = matched.merge(freq[["IDpol", *base.FEATURES]], on="IDpol", how="left", validate="many_to_one")
    if sevx[list(base.FEATURES)].isna().any().any():
        raise RuntimeError("severity covariate join produced missing values")

    splits = [run_seed(freq, sevx, s) for s in OUTER_SEEDS]
    result = {
        "schema": "ffbk-fremtpl2-direct-tweedie-vs-factorized-ri-v1",
        "question_fingerprint": "underwriting/premium-risk/fremtpl2/direct-tweedie-vs-factorized/full-law/reinsurance-transform",
        "source": {
            "frequency": freq_source, "severity": sev_source,
            "policy_rows": int(len(freq)), "severity_rows": int(len(sev)),
            "matched_severity_rows": int(len(matched)), "orphan_severity_rows": orphan_rows,
            "claimnb_sum": claim_count_sum,
        },
        "frozen_design": {
            "outer_seeds": list(OUTER_SEEDS),
            "direct_power_grid": list(DIRECT_POWERS),
            "direct_alpha_grid": list(DIRECT_ALPHAS),
            "selection_draws_per_validation_policy": SELECTION_DRAWS,
            "final_draws_per_test_policy": FINAL_DRAWS,
            "bootstrap_reps": BOOT_REPS,
            "primary": "policy annual-loss CRPS",
            "secondary_tail": "development q99/q99.5 Brier",
            "nonlinear_consumer": "policy annual finite aggregate layer 3A xs A with A=development q99; transformed-law CRPS",
            "direct_dispersion": "mean(W*(Y-mu)^2/mu^p) on annualised rate Y=AnnualLoss/W",
            "target_status": "reused #1479 holdout memberships; new direct-Tweedie arm and layer transform were preregistered before this lane scored them",
        },
        "splits": splits,
        "runtime": {
            "python": platform.python_version(), "numpy": np.__version__, "pandas": pd.__version__,
            "scipy": scipy.__version__, "scikit_learn": sklearn.__version__,
            "rdata": getattr(base.rdata, "__version__", "unknown"),
        },
        "limitations": [
            "one public French motor source family and reused outer holdout memberships",
            "no temporal holdout and no independent transfer dataset in this run",
            "process uncertainty conditional on fitted parameters only; coefficient/power/dispersion parameter uncertainty not propagated",
            "Poisson-Gamma and Poisson-IG impose frequency-severity conditional independence; direct Tweedie is compound Poisson-Gamma",
            "policy losses are conditionally independent; no common shock or portfolio dependence",
            "3A xs A is a bounded annual-policy-loss transform for nonlinear consumer discrimination, not an empirical treaty pricing benchmark",
            "finite Monte Carlo CRPS and Brier probabilities",
        ],
    }
    OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    winners = {
        "loss_crps": [min(s["scores"]["models"], key=lambda k: s["scores"]["models"][k]["mean_loss_crps_eur"]) for s in splits],
        "ceded_crps": [min(s["scores"]["models"], key=lambda k: s["scores"]["models"][k]["mean_ceded_crps_eur"]) for s in splits],
        "q995_brier": [min(s["scores"]["models"], key=lambda k: s["scores"]["models"][k]["tail_2_brier"]) for s in splits],
    }
    print("FINAL_WINNERS " + json.dumps(winners, sort_keys=True))
    print("RESULT_PATH " + str(OUT))


if __name__ == "__main__":
    main()
