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
import tmp_ffbk_fremtpl2_tweedie_ri as ri

OUT = Path("tmp_ffbk_fremtpl2_tweedie_ri_fair_audit_result.json")
OUTER_SEEDS = (26090731, 26090747, 26090773)
FIXED = {
    26090731: {"freq_alpha": 1e-4, "gamma_alpha": 0.0, "ig_alpha": 0.0, "direct_p": 1.9, "direct_alpha": 0.01},
    26090747: {"freq_alpha": 1e-4, "gamma_alpha": 0.0, "ig_alpha": 0.0, "direct_p": 1.9, "direct_alpha": 1e-4},
    26090773: {"freq_alpha": 1e-4, "gamma_alpha": 0.0, "ig_alpha": 0.0, "direct_p": 1.9, "direct_alpha": 0.0},
}
FULL_M = 128
FULL_REPS = 4
BOOT_REPS = 400
CONV_M = (64, 128, 512, 2048)
CONV_SUBSET_N = 10000


def raw_fair_crps(draws: np.ndarray, y: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    m = draws.shape[1]
    if m < 2:
        raise ValueError("fair CRPS needs at least two members")
    term1 = np.mean(np.abs(draws - y[:, None]), axis=1)
    xs = np.sort(draws, axis=1)
    weights = (2.0 * np.arange(1, m + 1) - m - 1.0)
    s = xs @ weights  # sum_{i<j} |x_i-x_j|
    raw = term1 - s / (m * m)
    fair = term1 - s / (m * (m - 1.0))
    return raw, fair


def raw_fair_brier(draws: np.ndarray, y: np.ndarray, threshold: float) -> tuple[np.ndarray, np.ndarray]:
    m = draws.shape[1]
    k = np.sum(draws > threshold, axis=1).astype(float)
    event = (y > threshold).astype(float)
    p = k / m
    raw = (p - event) ** 2
    fair = raw - k * (m - k) / (m * m * (m - 1.0))
    return raw, fair


def self_check() -> None:
    d = np.array([[0.0, 1.0, 4.0], [2.0, 2.0, 5.0]])
    y = np.array([2.0, 1.5])
    raw, fair = raw_fair_crps(d, y)
    ref = base.sample_crps(d, y)
    if not np.allclose(raw, ref, rtol=0, atol=1e-12):
        raise RuntimeError(f"raw CRPS identity failed: {raw} vs {ref}")
    brute = []
    for row, yy in zip(d, y):
        m = len(row)
        t1 = np.mean(np.abs(row - yy))
        ordered = sum(abs(a - b) for i, a in enumerate(row) for j, b in enumerate(row) if i != j)
        brute.append(t1 - 0.5 * ordered / (m * (m - 1)))
    if not np.allclose(fair, brute, rtol=0, atol=1e-12):
        raise RuntimeError(f"fair CRPS identity failed: {fair} vs {brute}")

    x = np.array([[0.0, 2.0, 3.0, 5.0]])
    yy = np.array([4.0])
    rb, fb = raw_fair_brier(x, yy, 1.0)
    k = 3.0
    m = 4.0
    expected = (k / m - 1.0) ** 2 - k * (m - k) / (m * m * (m - 1.0))
    if not math.isclose(float(fb[0]), expected, rel_tol=0, abs_tol=1e-15):
        raise RuntimeError("fair Brier identity failed")


def fit_fixed(freq: pd.DataFrame, sevx: pd.DataFrame, outer_seed: int) -> dict:
    cfg = FIXED[outer_seed]
    all_ids = freq["IDpol"].to_numpy("int64")
    dev_ids, test_ids = train_test_split(all_ids, test_size=0.20, random_state=outer_seed)
    devset, testset = set(dev_ids), set(test_ids)
    fdev = freq[freq["IDpol"].isin(devset)].copy()
    ftest = freq[freq["IDpol"].isin(testset)].copy()
    sdev = sevx[sevx["IDpol"].isin(devset)].copy()

    fm = base.freq_pipe(cfg["freq_alpha"])
    ydev_rate = fdev["ClaimNb"].to_numpy(float) / fdev["Exposure"].to_numpy(float)
    fm.fit(fdev[list(base.FEATURES)], ydev_rate, reg__sample_weight=fdev["Exposure"].to_numpy(float))
    freq_rate_test = np.maximum(fm.predict(ftest[list(base.FEATURES)]), 1e-12)
    exposure_test = ftest["Exposure"].to_numpy(float)
    lam_test = freq_rate_test * exposure_test

    ysev_dev = sdev["ClaimAmount"].to_numpy(float)
    gm = base.sev_pipe(2.0, cfg["gamma_alpha"])
    im = base.sev_pipe(3.0, cfg["ig_alpha"])
    gm.fit(sdev[list(base.FEATURES)], ysev_dev)
    im.fit(sdev[list(base.FEATURES)], ysev_dev)
    mu_g_dev = np.maximum(gm.predict(sdev[list(base.FEATURES)]), 1e-12)
    mu_i_dev = np.maximum(im.predict(sdev[list(base.FEATURES)]), 1e-12)
    phi_g = base.family_phi(ysev_dev, mu_g_dev, 2.0)
    phi_i = base.family_phi(ysev_dev, mu_i_dev, 3.0)
    mu_g_test = np.maximum(gm.predict(ftest[list(base.FEATURES)]), 1e-12)
    mu_i_test = np.maximum(im.predict(ftest[list(base.FEATURES)]), 1e-12)

    p = cfg["direct_p"]
    dm = base.sev_pipe(p, cfg["direct_alpha"])
    yrate = fdev["AnnualLoss"].to_numpy(float) / fdev["Exposure"].to_numpy(float)
    wdev = fdev["Exposure"].to_numpy(float)
    dm.fit(fdev[list(base.FEATURES)], yrate, reg__sample_weight=wdev)
    mu_d_dev = np.maximum(dm.predict(fdev[list(base.FEATURES)]), 1e-12)
    phi_d = ri.exposure_phi(yrate, mu_d_dev, wdev, p)
    mu_d_test = np.maximum(dm.predict(ftest[list(base.FEATURES)]), 1e-12)

    ytest = ftest["AnnualLoss"].to_numpy(float)
    ydev = fdev["AnnualLoss"].to_numpy(float)
    thresholds = (float(np.quantile(ydev, 0.99)), float(np.quantile(ydev, 0.995)))

    return {
        "ftest": ftest,
        "y": ytest,
        "exposure": exposure_test,
        "lam": lam_test,
        "mu_g": mu_g_test,
        "phi_g": phi_g,
        "mu_i": mu_i_test,
        "phi_i": phi_i,
        "mu_d": mu_d_test,
        "phi_d": phi_d,
        "p_d": p,
        "thresholds": thresholds,
        "attachment": thresholds[0],
        "config": cfg,
    }


def draw_chunk(fit: dict, lo: int, hi: int, m: int, seeds: tuple[int, int, int, int]) -> dict[str, np.ndarray]:
    sc, sg, si, sd = seeds
    # callers pass chunk-specific RNG objects through closure; this function is not used directly
    raise AssertionError("draw_chunk should not be called")


def evaluate_full_rep(fit: dict, outer_seed: int, rep: int, keep_arrays: bool) -> dict:
    y = fit["y"]
    exposure = fit["exposure"]
    attach = fit["attachment"]
    limit = 3.0 * attach
    obs_ceded = np.clip(y - attach, 0.0, limit)
    thresholds = fit["thresholds"]

    base_seed = outer_seed + 1000 + rep * 100003
    rng_count = np.random.default_rng(base_seed)
    rng_g = np.random.default_rng(base_seed + 1)
    rng_i = np.random.default_rng(base_seed + 2)
    rng_d = np.random.default_rng(base_seed + 3)

    models = ("poisson_gamma", "poisson_ig", "direct_tweedie")
    sums = {
        name: {k: 0.0 for k in (
            "loss_raw_crps", "loss_fair_crps", "layer_raw_crps", "layer_fair_crps",
            "q99_raw_brier", "q99_fair_brier", "q995_raw_brier", "q995_fair_brier",
        )}
        for name in models
    }
    arrays = None
    if keep_arrays:
        arrays = {name: {"loss_fair": np.empty(len(y)), "layer_fair": np.empty(len(y))} for name in models}

    chunk = 5000
    for lo in range(0, len(y), chunk):
        hi = min(len(y), lo + chunk)
        counts = rng_count.poisson(fit["lam"][lo:hi, None], size=(hi - lo, FULL_M))
        draws = {
            "poisson_gamma": ri.factorized_draws(counts, fit["mu_g"][lo:hi], fit["phi_g"], "gamma", rng_g),
            "poisson_ig": ri.factorized_draws(counts, fit["mu_i"][lo:hi], fit["phi_i"], "ig", rng_i),
            "direct_tweedie": ri.direct_chunk_draws(
                fit["mu_d"][lo:hi], exposure[lo:hi], fit["phi_d"], fit["p_d"], FULL_M, rng_d
            ),
        }
        yc = y[lo:hi]
        oc = obs_ceded[lo:hi]
        for name, d in draws.items():
            lr, lf = raw_fair_crps(d, yc)
            cd = np.clip(d - attach, 0.0, limit)
            cr, cf = raw_fair_crps(cd, oc)
            b1r, b1f = raw_fair_brier(d, yc, thresholds[0])
            b2r, b2f = raw_fair_brier(d, yc, thresholds[1])
            vals = {
                "loss_raw_crps": lr, "loss_fair_crps": lf,
                "layer_raw_crps": cr, "layer_fair_crps": cf,
                "q99_raw_brier": b1r, "q99_fair_brier": b1f,
                "q995_raw_brier": b2r, "q995_fair_brier": b2f,
            }
            for k, a in vals.items():
                sums[name][k] += float(np.sum(a))
            if arrays is not None:
                arrays[name]["loss_fair"][lo:hi] = lf
                arrays[name]["layer_fair"][lo:hi] = cf

    out = {
        "rep": rep,
        "seed_base": base_seed,
        "models": {name: {k: v / len(y) for k, v in sums[name].items()} for name in models},
    }
    if arrays is not None:
        out["_arrays"] = arrays
    return out


def paired_bootstrap(arrays: dict, outer_seed: int) -> dict:
    rng = np.random.default_rng(outer_seed + 991337)
    n = len(next(iter(arrays.values()))["loss_fair"])
    pairs = (
        ("direct_tweedie", "poisson_gamma"),
        ("direct_tweedie", "poisson_ig"),
        ("poisson_ig", "poisson_gamma"),
    )
    out = {}
    for a, b in pairs:
        dl = arrays[a]["loss_fair"] - arrays[b]["loss_fair"]
        dc = arrays[a]["layer_fair"] - arrays[b]["layer_fair"]
        boot = np.empty((BOOT_REPS, 2))
        for r in range(BOOT_REPS):
            ix = rng.integers(0, n, size=n)
            boot[r, 0] = np.mean(dl[ix])
            boot[r, 1] = np.mean(dc[ix])
        out[f"{a}_minus_{b}"] = {
            "loss_fair_crps_delta": float(np.mean(dl)),
            "loss_fair_crps_ci95": [float(np.quantile(boot[:, 0], 0.025)), float(np.quantile(boot[:, 0], 0.975))],
            "layer_fair_crps_delta": float(np.mean(dc)),
            "layer_fair_crps_ci95": [float(np.quantile(boot[:, 1], 0.025)), float(np.quantile(boot[:, 1], 0.975))],
            "negative_favors_first_named_model": True,
        }
    return out


def summarize_reps(reps: list[dict]) -> dict:
    names = reps[0]["models"].keys()
    metrics = reps[0]["models"][next(iter(names))].keys()
    out = {"models": {}}
    for name in names:
        out["models"][name] = {}
        for metric in metrics:
            vals = np.array([r["models"][name][metric] for r in reps], dtype=float)
            out["models"][name][metric] = {
                "mean": float(np.mean(vals)),
                "sd_across_independent_mc_reps": float(np.std(vals, ddof=1)) if len(vals) > 1 else 0.0,
                "values": [float(x) for x in vals],
            }
    for metric in metrics:
        if metric.endswith("crps") or metric.endswith("brier"):
            out[f"winner_{metric}"] = min(
                out["models"], key=lambda n: out["models"][n][metric]["mean"]
            )
    return out


def convergence_subset(fit: dict, outer_seed: int) -> dict:
    n = len(fit["y"])
    rng_ix = np.random.default_rng(outer_seed + 778899)
    ix = np.sort(rng_ix.choice(n, size=min(CONV_SUBSET_N, n), replace=False))
    y = fit["y"][ix]
    exposure = fit["exposure"][ix]
    lam = fit["lam"][ix]
    mu_g = fit["mu_g"][ix]
    mu_i = fit["mu_i"][ix]
    mu_d = fit["mu_d"][ix]
    attach = fit["attachment"]
    limit = 3.0 * attach
    obs_ceded = np.clip(y - attach, 0.0, limit)
    thresholds = fit["thresholds"]
    max_m = max(CONV_M)

    sums = {
        m: {name: {k: 0.0 for k in (
            "loss_raw_crps", "loss_fair_crps", "layer_raw_crps", "layer_fair_crps",
            "q99_raw_brier", "q99_fair_brier", "q995_raw_brier", "q995_fair_brier",
        )} for name in ("poisson_gamma", "poisson_ig", "direct_tweedie")}
        for m in CONV_M
    }

    seed0 = outer_seed + 7000000
    rng_count = np.random.default_rng(seed0)
    rng_g = np.random.default_rng(seed0 + 1)
    rng_i = np.random.default_rng(seed0 + 2)
    rng_d = np.random.default_rng(seed0 + 3)

    chunk = 500
    for lo in range(0, len(ix), chunk):
        hi = min(len(ix), lo + chunk)
        counts = rng_count.poisson(lam[lo:hi, None], size=(hi - lo, max_m))
        draws_max = {
            "poisson_gamma": ri.factorized_draws(counts, mu_g[lo:hi], fit["phi_g"], "gamma", rng_g),
            "poisson_ig": ri.factorized_draws(counts, mu_i[lo:hi], fit["phi_i"], "ig", rng_i),
            "direct_tweedie": ri.direct_chunk_draws(mu_d[lo:hi], exposure[lo:hi], fit["phi_d"], fit["p_d"], max_m, rng_d),
        }
        yc = y[lo:hi]
        oc = obs_ceded[lo:hi]
        for m in CONV_M:
            for name, dmax in draws_max.items():
                d = dmax[:, :m]
                lr, lf = raw_fair_crps(d, yc)
                cd = np.clip(d - attach, 0.0, limit)
                cr, cf = raw_fair_crps(cd, oc)
                b1r, b1f = raw_fair_brier(d, yc, thresholds[0])
                b2r, b2f = raw_fair_brier(d, yc, thresholds[1])
                vals = {
                    "loss_raw_crps": lr, "loss_fair_crps": lf,
                    "layer_raw_crps": cr, "layer_fair_crps": cf,
                    "q99_raw_brier": b1r, "q99_fair_brier": b1f,
                    "q995_raw_brier": b2r, "q995_fair_brier": b2f,
                }
                for k, a in vals.items():
                    sums[m][name][k] += float(np.sum(a))

    out = {
        "subset_n": int(len(ix)),
        "subset_selection": "uniform without replacement from final test indices using seed outer_seed+778899; selected before any audit score calculation",
        "nested_prefix_max_m": max_m,
        "seed_base": seed0,
        "member_counts": {},
    }
    for m in CONV_M:
        out["member_counts"][str(m)] = {
            name: {k: v / len(ix) for k, v in sums[m][name].items()} for name in sums[m]
        }
    return out


def run_seed(freq: pd.DataFrame, sevx: pd.DataFrame, outer_seed: int) -> dict:
    fit = fit_fixed(freq, sevx, outer_seed)
    reps = []
    arrays = None
    for rep in range(FULL_REPS):
        rr = evaluate_full_rep(fit, outer_seed, rep, keep_arrays=(rep == 0))
        if rep == 0:
            arrays = rr.pop("_arrays")
        reps.append(rr)
    if arrays is None:
        raise RuntimeError("missing audit arrays")
    boot = paired_bootstrap(arrays, outer_seed)
    summary = summarize_reps(reps)
    conv = convergence_subset(fit, outer_seed)
    result = {
        "outer_seed": outer_seed,
        "fixed_selection": fit["config"],
        "test_policies": int(len(fit["y"])),
        "thresholds": {"q99": fit["thresholds"][0], "q995": fit["thresholds"][1]},
        "attachment": fit["attachment"],
        "full_test_member_count": FULL_M,
        "full_test_independent_reps": reps,
        "full_test_rep_summary": summary,
        "rep0_fair_paired_policy_bootstrap": boot,
        "convergence_subset": conv,
    }
    print("AUDIT_SPLIT " + json.dumps({
        "seed": outer_seed,
        "fair_loss_winner": summary["winner_loss_fair_crps"],
        "fair_layer_winner": summary["winner_layer_fair_crps"],
        "fair_q99_winner": summary["winner_q99_fair_brier"],
        "fair_q995_winner": summary["winner_q995_fair_brier"],
        "fair_loss": {n: summary["models"][n]["loss_fair_crps"]["mean"] for n in summary["models"]},
        "raw_loss": {n: summary["models"][n]["loss_raw_crps"]["mean"] for n in summary["models"]},
        "fair_q995": {n: summary["models"][n]["q995_fair_brier"]["mean"] for n in summary["models"]},
    }, sort_keys=True))
    return result


def main() -> None:
    self_check()
    freq_raw, freq_source = base.fetch_rda("freMTPL2freq")
    sev_raw, sev_source = base.fetch_rda("freMTPL2sev")
    freq = base.norm_freq(freq_raw)
    sev = base.norm_sev(sev_raw)
    matched = sev[sev["IDpol"].isin(freq["IDpol"])].copy()
    if int(round(freq["ClaimNb"].sum())) != len(matched) or len(matched) != len(sev):
        raise RuntimeError("source identity mismatch")
    total = matched.groupby("IDpol", sort=False)["ClaimAmount"].sum()
    freq["AnnualLoss"] = freq["IDpol"].map(total).fillna(0.0).astype(float)
    sevx = matched.merge(freq[["IDpol", *base.FEATURES]], on="IDpol", how="left", validate="many_to_one")
    if sevx[list(base.FEATURES)].isna().any().any():
        raise RuntimeError("severity covariate join produced missing values")

    splits = [run_seed(freq, sevx, s) for s in OUTER_SEEDS]
    out = {
        "schema": "ffbk-fremtpl2-tweedie-ri-fair-score-audit-v1",
        "status": "RETROSPECTIVE_SCORING_ONLY_FIXED_FITTED_LAWS / NO_RESELECTION / NO_PROMOTION",
        "parent_question_fingerprint": "underwriting/premium-risk/fremtpl2/direct-tweedie-vs-factorized/full-law/reinsurance-transform",
        "controlling_evidence": "FFBK merged PR #1484 / main@4153c149ba89d1ebff779136d03c5a68bb7c6c34",
        "source": {"frequency": freq_source, "severity": sev_source},
        "audit_contract": {
            "fixed_hyperparameters": FIXED,
            "full_test_member_count": FULL_M,
            "full_test_independent_mc_reps": FULL_REPS,
            "paired_policy_bootstrap_reps_on_rep0_fair_scores": BOOT_REPS,
            "convergence_subset_n": CONV_SUBSET_N,
            "convergence_member_counts": list(CONV_M),
            "fair_crps": "mean|X-y| - sum_{i<j}|Xi-Xj|/[M(M-1)]",
            "fair_brier": "raw Brier - k(M-k)/[M^2(M-1)]",
            "selection_boundary": "No model, hyperparameter, threshold or layer re-selection. Direct p/alpha, frequency alpha and severity alphas are fixed to the consumed parent execution selections.",
        },
        "splits": splits,
        "runtime": {
            "python": platform.python_version(), "numpy": np.__version__, "pandas": pd.__version__,
            "scipy": scipy.__version__, "scikit_learn": sklearn.__version__,
            "rdata": getattr(base.rdata, "__version__", "unknown"),
        },
        "limitations": [
            "retrospective scoring audit on already-consumed holdout outcomes",
            "direct-Tweedie p/alpha selection itself used raw 64-member validation CRPS and is not retrospectively re-selected here",
            "fixed fitted laws are reconstructed deterministically from the frozen data, splits and selected hyperparameters rather than serialized model objects",
            "fair finite-ensemble correction removes the known random-ensemble bias in the score estimator but does not add parameter uncertainty",
            "convergence grid uses a deterministic 10k-policy test subset to bound computation; full-test fair estimates use four independent M=128 simulations",
            "no independent source/temporal transfer target",
        ],
    }
    OUT.write_text(json.dumps(out, indent=2, sort_keys=True) + "\n")
    print("AUDIT_RESULT_PATH " + str(OUT))


if __name__ == "__main__":
    main()
