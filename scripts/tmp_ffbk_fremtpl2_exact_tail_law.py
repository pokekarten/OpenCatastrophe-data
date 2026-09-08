#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
from scipy.stats import gamma as gamma_dist
from scipy.stats import invgauss

import tmp_ffbk_fremtpl2_aggregate_law as study

SEEDS = (26090731, 26090747, 26090773)
OUT = Path("tmp_ffbk_fremtpl2_exact_tail_law_result.json")
POISSON_TAIL_TOL = 1.0e-12
MAX_N = 64

# Published fair-M=128 IG-minus-Gamma Brier deltas from merged FFBK #1487.
FAIR_M128_Q995 = {
    26090731: -2.996873e-06,
    26090747: -1.947106e-06,
    26090773: -1.057933e-06,
}


def _ig_sum_params(mu: np.ndarray, phi: float, n: int) -> tuple[np.ndarray, float]:
    """SciPy invgauss parameters matching Wald(mean=n*mu, scale=n^2/phi)."""
    return phi * mu / n, (n * n) / phi


def _assert_ig_parameterization() -> None:
    mu = np.array([1000.0, 5000.0])
    phi = 2.5e-4
    for n in (1, 2, 7):
        shape, scale = _ig_sum_params(mu, phi, n)
        got_mean = invgauss.mean(shape, scale=scale)
        got_var = invgauss.var(shape, scale=scale)
        want_mean = n * mu
        want_var = n * phi * mu**3
        if not np.allclose(got_mean, want_mean, rtol=1e-12, atol=1e-9):
            raise RuntimeError("inverse-Gaussian aggregate mean parameterization mismatch")
        if not np.allclose(got_var, want_var, rtol=1e-12, atol=1e-6):
            raise RuntimeError("inverse-Gaussian aggregate variance parameterization mismatch")


def exact_exceedance(
    lam: np.ndarray,
    mu: np.ndarray,
    phi: float,
    threshold: float,
    family: str,
) -> tuple[np.ndarray, dict]:
    """Compound-Poisson exceedance by conditioning on N and summing its mass."""
    lam = np.asarray(lam, dtype=float)
    mu = np.asarray(mu, dtype=float)
    if np.any(lam < 0) or np.any(mu <= 0) or phi <= 0:
        raise RuntimeError("invalid compound-distribution parameters")

    p_n = np.exp(-lam)
    mass = p_n.copy()
    exceed = np.zeros_like(lam)
    used_n = 0

    for n in range(1, MAX_N + 1):
        p_n = p_n * lam / n
        if family == "gamma":
            sf = gamma_dist.sf(threshold, a=n / phi, scale=phi * mu)
        elif family == "inverse_gaussian":
            shape, scale = _ig_sum_params(mu, phi, n)
            sf = invgauss.sf(threshold, shape, scale=scale)
        else:
            raise ValueError(family)
        if not np.isfinite(sf).all():
            raise RuntimeError(f"non-finite {family} survival probabilities")
        exceed += p_n * sf
        mass += p_n
        used_n = n
        residual = np.maximum(0.0, 1.0 - mass)
        if float(np.max(residual)) <= POISSON_TAIL_TOL:
            break

    residual = np.maximum(0.0, 1.0 - mass)
    max_residual = float(np.max(residual))
    if max_residual > POISSON_TAIL_TOL:
        raise RuntimeError(
            f"Poisson mixture truncation did not converge: max residual={max_residual} at n={used_n}"
        )
    if np.any(exceed < -1e-14) or np.any(exceed > 1.0 + max_residual + 1e-14):
        raise RuntimeError("invalid exceedance probability")
    return np.clip(exceed, 0.0, 1.0), {
        "family": family,
        "terms_through_n": used_n,
        "max_unallocated_poisson_mass": max_residual,
        "tail_tolerance": POISSON_TAIL_TOL,
    }


def paired_summary(delta: np.ndarray) -> dict:
    n = len(delta)
    mean = float(np.mean(delta))
    se = float(np.std(delta, ddof=1) / np.sqrt(n))
    return {
        "mean": mean,
        "paired_normal_se": se,
        "paired_normal_ci95": [mean - 1.959963984540054 * se, mean + 1.959963984540054 * se],
        "negative_favors_inverse_gaussian": True,
        "uncertainty_scope": "policy-sampling normal approximation conditional on frozen fitted models; no Monte-Carlo ensemble noise remains",
    }


def simulate_scores_exact(
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
    _assert_ig_parameterization()
    out: dict[str, object] = {
        "exact_tail_law": {
            "method": "conditional compound-Poisson mixture over claim count",
            "gamma_conditional_sum": "Gamma(shape=n/phi, scale=phi*mu)",
            "inverse_gaussian_conditional_sum": "Wald(mean=n*mu, scale=n^2/phi)",
            "finite_random_ensemble_used": False,
        },
        "thresholds": [],
        "paired_crps": {
            "status": "NOT_COMPUTED_IN_THIS_TAIL_ONLY_AUDIT",
            "reason": "question is exact q99/q99.5 Brier-law ordering after #1487; CRPS direction already survived fair scoring 3/3",
        },
    }

    for j, threshold in enumerate(thresholds):
        event = (y > threshold).astype(float)
        pg, dg = exact_exceedance(lam, mu_g, phi_g, threshold, "gamma")
        pi, di = exact_exceedance(lam, mu_i, phi_i, threshold, "inverse_gaussian")
        pim, dim = exact_exceedance(
            lam, mu_i_matched, phi_i_matched, threshold, "inverse_gaussian"
        )

        sg = (pg - event) ** 2
        si = (pi - event) ** 2
        sim = (pim - event) ** 2
        delta = si - sg
        delta_m = sim - sg

        row = {
            "quantile_label": "q99" if j == 0 else "q99.5",
            "threshold_eur": float(threshold),
            "observed_event_rate": float(np.mean(event)),
            "predicted_event_rate": {
                "gamma": float(np.mean(pg)),
                "inverse_gaussian": float(np.mean(pi)),
                "inverse_gaussian_mean_matched_to_gamma": float(np.mean(pim)),
            },
            "exact_brier": {
                "gamma": float(np.mean(sg)),
                "inverse_gaussian": float(np.mean(si)),
                "inverse_gaussian_mean_matched_to_gamma": float(np.mean(sim)),
            },
            "ig_minus_gamma": paired_summary(delta),
            "mean_matched_ig_minus_gamma": paired_summary(delta_m),
            "mixture_diagnostics": {
                "gamma": dg,
                "inverse_gaussian": di,
                "inverse_gaussian_mean_matched_to_gamma": dim,
            },
        }
        if j == 1:
            row["published_fair_m128_ig_minus_gamma_brier"] = FAIR_M128_Q995[study.SEED]
            row["exact_minus_published_fair_m128_delta"] = (
                row["ig_minus_gamma"]["mean"] - FAIR_M128_Q995[study.SEED]
            )
            row["same_direction_as_published_fair_m128"] = (
                row["ig_minus_gamma"]["mean"] < 0
            ) == (FAIR_M128_Q995[study.SEED] < 0)
        out["thresholds"].append(row)
    return out


def main() -> None:
    original = study.simulate_scores
    runs = []
    try:
        study.simulate_scores = simulate_scores_exact
        for seed in SEEDS:
            study.SEED = seed
            path = Path(f"tmp_ffbk_fremtpl2_exact_tail_law_{seed}.json")
            study.OUT = path
            study.main()
            result = json.loads(path.read_text())
            runs.append(result)
    finally:
        study.simulate_scores = original

    q995 = [r["scores"]["thresholds"][1] for r in runs]
    q99 = [r["scores"]["thresholds"][0] for r in runs]
    summary = {
        "schema": "ffbk-fremtpl2-exact-tail-law-v1",
        "research_role": "retrospective exact-scoring falsification of fair-M128 tail ordering; frozen fits/splits/thresholds; no model promotion",
        "seeds": list(SEEDS),
        "q99_exact_ig_wins": sum(x["ig_minus_gamma"]["mean"] < 0 for x in q99),
        "q995_exact_ig_wins": sum(x["ig_minus_gamma"]["mean"] < 0 for x in q995),
        "q995_exact_mean_matched_ig_wins": sum(
            x["mean_matched_ig_minus_gamma"]["mean"] < 0 for x in q995
        ),
        "q995_same_direction_as_fair_m128": sum(
            x["same_direction_as_published_fair_m128"] for x in q995
        ),
        "q995_exact_ig_minus_gamma_brier": [x["ig_minus_gamma"]["mean"] for x in q995],
        "q995_exact_ig_minus_gamma_ci95": [x["ig_minus_gamma"]["paired_normal_ci95"] for x in q995],
        "q995_exact_minus_fair_m128_delta": [
            x["exact_minus_published_fair_m128_delta"] for x in q995
        ],
        "runs": runs,
    }
    OUT.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
    print(json.dumps({k: v for k, v in summary.items() if k != "runs"}, indent=2))


if __name__ == "__main__":
    main()
