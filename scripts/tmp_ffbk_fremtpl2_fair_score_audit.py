#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

import numpy as np

import tmp_ffbk_fremtpl2_aggregate_law as study

# Direct retrospective handoff from the frozen three-split #1479 experiment.
# Do not tune from target outcomes.
SEEDS = (26090731, 26090747, 26090773)
MC_DRAWS = 128
OUT = Path("tmp_ffbk_fair_score_audit_result.json")

# Published #1479 raw deltas, rounded to six decimals in the durable FFBK note.
# This is a regression guard only; fair-score conclusions use the fresh full-precision run.
EXPECTED_RAW_ROUNDED = {
    26090731: (-0.647445, -0.762417),
    26090747: (-0.718002, -0.775913),
    26090773: (-0.655631, -0.769869),
}


def sample_crps_raw_fair(draws: np.ndarray, y: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Return ordinary empirical and Ferro-style fair CRPS for iid ensembles."""
    m = draws.shape[1]
    if m < 2:
        raise ValueError("fair CRPS requires at least two ensemble members")
    first = np.mean(np.abs(draws - y[:, None]), axis=1)
    s = np.sort(draws, axis=1)
    coef = (2 * np.arange(1, m + 1) - m - 1).astype(float)
    weighted = np.sum(s * coef[None, :], axis=1)
    raw = first - weighted / (m * m)
    fair = first - weighted / (m * (m - 1))
    return raw, fair


def fair_brier(raw: np.ndarray, p_hat: np.ndarray, m: int) -> np.ndarray:
    """Ferro fair Brier correction for iid random ensembles."""
    if m < 2:
        raise ValueError("fair Brier requires at least two ensemble members")
    return raw - p_hat * (1.0 - p_hat) / (m - 1)


def simulate_scores_fair(
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
    """Frozen #1479 simulator with additive fair-score diagnostics only."""
    if study.MC_DRAWS != MC_DRAWS:
        raise RuntimeError(f"unexpected frozen ensemble size: {study.MC_DRAWS}")

    n = len(y)
    crps_g = np.empty(n)
    crps_i = np.empty(n)
    crps_im = np.empty(n)
    fair_crps_g = np.empty(n)
    fair_crps_i = np.empty(n)
    fair_crps_im = np.empty(n)
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
        crps_g[lo:hi], fair_crps_g[lo:hi] = sample_crps_raw_fair(dg, yc)
        crps_i[lo:hi], fair_crps_i[lo:hi] = sample_crps_raw_fair(di, yc)
        crps_im[lo:hi], fair_crps_im[lo:hi] = sample_crps_raw_fair(dim, yc)

        for j, t in enumerate(thresholds):
            probs["gamma"][j][lo:hi] = np.mean(dg > t, axis=1)
            probs["ig"][j][lo:hi] = np.mean(di > t, axis=1)
            probs["ig_mean_matched"][j][lo:hi] = np.mean(dim > t, axis=1)

    def metrics(
        name: str,
        crps: np.ndarray,
        fair_crps: np.ndarray,
        pred_mean: np.ndarray,
    ) -> dict:
        out = {
            "mean_crps_eur": float(np.mean(crps)),
            "mean_crps_positive_observed_policy_eur": float(np.mean(crps[y > 0])),
            "fair_mean_crps_eur": float(np.mean(fair_crps)),
            "fair_mean_crps_positive_observed_policy_eur": float(np.mean(fair_crps[y > 0])),
            "observed_over_predicted_aggregate_mean": float(np.sum(y) / np.sum(pred_mean)),
            "predicted_total_loss": float(np.sum(pred_mean)),
            "observed_total_loss": float(np.sum(y)),
        }
        for j, t in enumerate(thresholds):
            event = (y > t).astype(float)
            pr = probs[name][j]
            raw_policy = (pr - event) ** 2
            fair_policy = fair_brier(raw_policy, pr, MC_DRAWS)
            out[f"tail_{j+1}_threshold_eur"] = float(t)
            out[f"tail_{j+1}_brier"] = float(np.mean(raw_policy))
            out[f"tail_{j+1}_fair_brier"] = float(np.mean(fair_policy))
            out[f"tail_{j+1}_fair_minus_raw_brier"] = float(np.mean(fair_policy - raw_policy))
            out[f"tail_{j+1}_observed_rate"] = float(np.mean(event))
            out[f"tail_{j+1}_predicted_rate"] = float(np.mean(pr))
        return out

    pred_g = lam * mu_g
    pred_i = lam * mu_i
    pred_im = lam * mu_i_matched
    delta = crps_i - crps_g
    delta_im = crps_im - crps_g
    fair_delta = fair_crps_i - fair_crps_g
    fair_delta_im = fair_crps_im - fair_crps_g

    rng_b = np.random.default_rng(seed + 99)
    reps = 400
    boot = np.empty((reps, 4))
    for b in range(reps):
        idx = rng_b.integers(0, n, size=n)
        boot[b, 0] = np.mean(delta[idx])
        boot[b, 1] = np.mean(delta_im[idx])
        boot[b, 2] = np.mean(fair_delta[idx])
        boot[b, 3] = np.mean(fair_delta_im[idx])

    gamma = metrics("gamma", crps_g, fair_crps_g, pred_g)
    inverse_gaussian = metrics("ig", crps_i, fair_crps_i, pred_i)
    mean_matched = metrics("ig_mean_matched", crps_im, fair_crps_im, pred_im)

    mg = float(np.mean(crps_g))
    mi = float(np.mean(crps_i))
    mim = float(np.mean(crps_im))
    fmg = float(np.mean(fair_crps_g))
    fmi = float(np.mean(fair_crps_i))
    fmim = float(np.mean(fair_crps_im))

    return {
        "gamma": gamma,
        "inverse_gaussian": inverse_gaussian,
        "inverse_gaussian_mean_matched_to_gamma": mean_matched,
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
            "fair_ig_minus_gamma_eur": float(np.mean(fair_delta)),
            "fair_ig_minus_gamma_relative_pct": float(100.0 * (fmi / fmg - 1.0)),
            "fair_ig_minus_gamma_bootstrap_ci95_eur": [
                float(np.quantile(boot[:, 2], 0.025)),
                float(np.quantile(boot[:, 2], 0.975)),
            ],
            "fair_mean_matched_ig_minus_gamma_eur": float(np.mean(fair_delta_im)),
            "fair_mean_matched_ig_minus_gamma_relative_pct": float(100.0 * (fmim / fmg - 1.0)),
            "fair_mean_matched_ig_minus_gamma_bootstrap_ci95_eur": [
                float(np.quantile(boot[:, 3], 0.025)),
                float(np.quantile(boot[:, 3], 0.975)),
            ],
            "bootstrap_reps": reps,
            "bootstrap_unit": "policy",
            "negative_delta_favors_inverse_gaussian": True,
            "bootstrap_scope": "policy sampling conditional on the realised finite Monte Carlo ensembles; Monte Carlo resampling uncertainty is not included",
        },
        "finite_ensemble_score_audit": {
            "ensemble_members": MC_DRAWS,
            "ensemble_interpretation": "iid random draws from each fitted predictive law",
            "raw_crps_pair_denominator": "M^2",
            "fair_crps_pair_denominator": "M*(M-1)",
            "fair_brier_correction": "raw - p_hat*(1-p_hat)/(M-1)",
            "retrospective": True,
            "model_selection_or_refit_changed": False,
            "member_count_convergence_tested": False,
        },
    }


def assert_raw_regression(seed: int, result: dict) -> None:
    paired = result["scores"]["paired_crps"]
    got = (
        float(paired["ig_minus_gamma_eur"]),
        float(paired["mean_matched_ig_minus_gamma_eur"]),
    )
    expected = EXPECTED_RAW_ROUNDED[seed]
    for observed, published in zip(got, expected):
        if abs(observed - published) > 1.0e-6:
            raise RuntimeError(
                f"raw #1479 regression mismatch for seed {seed}: observed={got}, expected_rounded={expected}"
            )


def main() -> None:
    original_simulate_scores = study.simulate_scores
    if study.MC_DRAWS != MC_DRAWS:
        raise RuntimeError(f"frozen #1479 MC_DRAWS changed: {study.MC_DRAWS}")
    study.simulate_scores = simulate_scores_fair

    runs = []
    try:
        for seed in SEEDS:
            path = Path(f"tmp_ffbk_fair_score_audit_{seed}.json")
            study.SEED = seed
            study.OUT = path
            study.main()
            result = json.loads(path.read_text())
            assert_raw_regression(seed, result)
            runs.append(result)
    finally:
        study.simulate_scores = original_simulate_scores

    def model(run: dict, key: str) -> dict:
        return run["scores"][key]

    def paired(run: dict) -> dict:
        return run["scores"]["paired_crps"]

    summary = {
        "schema": "ffbk-fremtpl2-fair-score-audit-v1",
        "research_role": "retrospective scoring-only audit of frozen #1479 target; no model-family promotion",
        "seeds": list(SEEDS),
        "ensemble_members": MC_DRAWS,
        "raw_regression_guard_passed": True,
        "fair_crps_ig_wins": sum(paired(r)["fair_ig_minus_gamma_eur"] < 0 for r in runs),
        "fair_crps_ig_bootstrap_ci_excludes_zero_favourably": sum(
            paired(r)["fair_ig_minus_gamma_bootstrap_ci95_eur"][1] < 0 for r in runs
        ),
        "fair_crps_mean_matched_ig_wins": sum(
            paired(r)["fair_mean_matched_ig_minus_gamma_eur"] < 0 for r in runs
        ),
        "fair_crps_mean_matched_ig_bootstrap_ci_excludes_zero_favourably": sum(
            paired(r)["fair_mean_matched_ig_minus_gamma_bootstrap_ci95_eur"][1] < 0 for r in runs
        ),
        "fair_ig_minus_gamma_crps_eur": [
            float(paired(r)["fair_ig_minus_gamma_eur"]) for r in runs
        ],
        "fair_mean_matched_ig_minus_gamma_crps_eur": [
            float(paired(r)["fair_mean_matched_ig_minus_gamma_eur"]) for r in runs
        ],
        "tail_brier_ig_wins": {
            "raw_q99": sum(
                model(r, "inverse_gaussian")["tail_1_brier"] < model(r, "gamma")["tail_1_brier"]
                for r in runs
            ),
            "fair_q99": sum(
                model(r, "inverse_gaussian")["tail_1_fair_brier"] < model(r, "gamma")["tail_1_fair_brier"]
                for r in runs
            ),
            "raw_q995": sum(
                model(r, "inverse_gaussian")["tail_2_brier"] < model(r, "gamma")["tail_2_brier"]
                for r in runs
            ),
            "fair_q995": sum(
                model(r, "inverse_gaussian")["tail_2_fair_brier"] < model(r, "gamma")["tail_2_fair_brier"]
                for r in runs
            ),
        },
        "tail_brier_mean_matched_ig_wins": {
            "raw_q99": sum(
                model(r, "inverse_gaussian_mean_matched_to_gamma")["tail_1_brier"] < model(r, "gamma")["tail_1_brier"]
                for r in runs
            ),
            "fair_q99": sum(
                model(r, "inverse_gaussian_mean_matched_to_gamma")["tail_1_fair_brier"] < model(r, "gamma")["tail_1_fair_brier"]
                for r in runs
            ),
            "raw_q995": sum(
                model(r, "inverse_gaussian_mean_matched_to_gamma")["tail_2_brier"] < model(r, "gamma")["tail_2_brier"]
                for r in runs
            ),
            "fair_q995": sum(
                model(r, "inverse_gaussian_mean_matched_to_gamma")["tail_2_fair_brier"] < model(r, "gamma")["tail_2_fair_brier"]
                for r in runs
            ),
        },
        "per_seed": [
            {
                "seed": int(r["design"]["seed"]),
                "raw_ig_minus_gamma_crps_eur": float(paired(r)["ig_minus_gamma_eur"]),
                "fair_ig_minus_gamma_crps_eur": float(paired(r)["fair_ig_minus_gamma_eur"]),
                "raw_mean_matched_ig_minus_gamma_crps_eur": float(paired(r)["mean_matched_ig_minus_gamma_eur"]),
                "fair_mean_matched_ig_minus_gamma_crps_eur": float(paired(r)["fair_mean_matched_ig_minus_gamma_eur"]),
                "raw_q99_brier_delta_ig_minus_gamma": float(
                    model(r, "inverse_gaussian")["tail_1_brier"] - model(r, "gamma")["tail_1_brier"]
                ),
                "fair_q99_brier_delta_ig_minus_gamma": float(
                    model(r, "inverse_gaussian")["tail_1_fair_brier"] - model(r, "gamma")["tail_1_fair_brier"]
                ),
                "raw_q995_brier_delta_ig_minus_gamma": float(
                    model(r, "inverse_gaussian")["tail_2_brier"] - model(r, "gamma")["tail_2_brier"]
                ),
                "fair_q995_brier_delta_ig_minus_gamma": float(
                    model(r, "inverse_gaussian")["tail_2_fair_brier"] - model(r, "gamma")["tail_2_fair_brier"]
                ),
            }
            for r in runs
        ],
        "limitations": [
            "Fair corrections remove expected iid finite-ensemble score bias at M=128 but do not establish member-count convergence.",
            "Policy bootstrap intervals are conditional on the realised Monte Carlo ensembles and omit Monte Carlo resampling uncertainty.",
            "The evaluation target was already consumed by #1479; this audit can weaken or rehabilitate interpretation but cannot promote a model family.",
        ],
    }

    OUT.write_text(json.dumps({"summary": summary, "runs": runs}, indent=2, sort_keys=True) + "\n")
    print("FREMTPL2_FAIR_SCORE_AUDIT_OK")
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
