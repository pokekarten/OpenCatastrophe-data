#!/usr/bin/env python3
"""Post-exposure paired uncertainty diagnostic for FFBK PR #1319.

Disposable execution-only code. It extends the already-audited independent
freMTPL2 runner on the same data lineage. It does not create a new holdout,
refit a duration-aware challenger, or provide independent-data validation.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np

import independent_fremtpl_runner as base

EXPECTED = {
    0: {1.5: 0.102820, 1.9: 0.028295},
    17: {1.5: 0.217462, 1.9: 0.031424},
    42: {1.5: 0.318360, 1.9: 0.093491},
}
BOOTSTRAP_REPS = 1000
BOOTSTRAP_SEED = 20260905


def unit_tweedie_deviance(y: np.ndarray, mu: np.ndarray, power: float) -> np.ndarray:
    """Per-policy unit deviance for 1 < power < 2, matching sklearn."""
    y = np.asarray(y, dtype=float)
    mu = np.asarray(mu, dtype=float)
    if not (1.0 < power < 2.0):
        raise ValueError("this diagnostic is bounded to powers in (1,2)")
    if np.any(y < 0) or np.any(mu <= 0):
        raise ValueError("invalid Tweedie support")
    y_term = np.zeros_like(y)
    positive = y > 0
    y_term[positive] = y[positive] ** (2.0 - power) / (
        (1.0 - power) * (2.0 - power)
    )
    return 2.0 * (
        y_term
        - y * mu ** (1.0 - power) / (1.0 - power)
        + mu ** (2.0 - power) / (2.0 - power)
    )


def paired_bootstrap(
    weight: np.ndarray,
    deltas: dict[float, np.ndarray],
    *,
    seed: int,
    reps: int = BOOTSTRAP_REPS,
    batch: int = 10,
) -> dict[str, dict]:
    """Paired nonparametric policy-row bootstrap with original exposure weights."""
    rng = np.random.default_rng(seed)
    n = len(weight)
    out = {q: np.empty(reps, dtype=float) for q in deltas}
    weighted = {q: weight * v for q, v in deltas.items()}
    done = 0
    while done < reps:
        b = min(batch, reps - done)
        idx = rng.integers(0, n, size=(b, n), dtype=np.int32)
        den = weight[idx].sum(axis=1)
        for q, arr in weighted.items():
            out[q][done : done + b] = arr[idx].sum(axis=1) / den
        done += b

    result: dict[str, dict] = {}
    mean_w = float(np.mean(weight))
    for q, samples in out.items():
        point = float(np.sum(weighted[q]) / np.sum(weight))
        influence = weight * (deltas[q] - point) / mean_w
        se = float(np.std(influence, ddof=1) / np.sqrt(n))
        result[str(q)] = {
            "point": point,
            "bootstrap_reps": reps,
            "bootstrap_q025": float(np.quantile(samples, 0.025)),
            "bootstrap_median": float(np.quantile(samples, 0.5)),
            "bootstrap_q975": float(np.quantile(samples, 0.975)),
            "bootstrap_fraction_le_zero": float(np.mean(samples <= 0.0)),
            "influence_se": se,
            "normal_q025": point - 1.959963984540054 * se,
            "normal_q975": point + 1.959963984540054 * se,
        }
    return result


def one_split(d, seed: int) -> dict:
    from sklearn.linear_model import GammaRegressor, PoissonRegressor, TweedieRegressor
    from sklearn.metrics import mean_gamma_deviance, mean_poisson_deviance, mean_tweedie_deviance
    from sklearn.model_selection import train_test_split

    outer_train, outer_test = train_test_split(
        np.arange(len(d)), test_size=0.25, random_state=seed
    )
    tr, te = d.iloc[outer_train], d.iloc[outer_test]
    inner_fit, inner_val = train_test_split(
        np.arange(len(tr)), test_size=0.2, random_state=seed + 10000
    )
    a, b = tr.iloc[inner_fit], tr.iloc[inner_val]

    prep_inner = base.preprocessor()
    xa = prep_inner.fit_transform(a)
    xb = prep_inner.transform(b)

    freq_pred: dict[float, np.ndarray] = {}
    freq_score: dict[float, float] = {}
    for alpha in base.FREQ_ALPHAS:
        model = PoissonRegressor(alpha=alpha, solver="newton-cholesky").fit(
            xa, a.Frequency, sample_weight=a.Exposure
        )
        freq_pred[alpha] = model.predict(xb)
        freq_score[alpha] = float(
            mean_poisson_deviance(
                b.Frequency, freq_pred[alpha], sample_weight=b.Exposure
            )
        )

    fit_pos = a.ClaimAmount.to_numpy() > 0
    val_pos = b.ClaimAmount.to_numpy() > 0
    sev_pred: dict[float, np.ndarray] = {}
    sev_score: dict[float, float] = {}
    for alpha in base.SEV_ALPHAS:
        model = GammaRegressor(alpha=alpha, solver="newton-cholesky").fit(
            xa[fit_pos],
            a.loc[fit_pos, "AvgClaimAmount"],
            sample_weight=a.loc[fit_pos, "ClaimNb"],
        )
        sev_pred[alpha] = model.predict(xb)
        sev_score[alpha] = float(
            mean_gamma_deviance(
                b.loc[val_pos, "AvgClaimAmount"],
                sev_pred[alpha][val_pos],
                sample_weight=b.loc[val_pos, "ClaimNb"],
            )
        )

    y_val = b.PurePremium.to_numpy(float)
    w_val = b.Exposure.to_numpy(float)
    joint: dict[float, tuple[float, float]] = {}
    for power in base.FIT_POWERS:
        scores = {
            (fa, sa): float(
                mean_tweedie_deviance(
                    y_val,
                    freq_pred[fa] * sev_pred[sa],
                    sample_weight=w_val,
                    power=power,
                )
            )
            for fa in base.FREQ_ALPHAS
            for sa in base.SEV_ALPHAS
        }
        joint[power] = min(scores, key=lambda z: (scores[z], z[0], z[1]))

    direct_alpha: dict[float, float] = {}
    for power in base.FIT_POWERS:
        scores = {}
        for alpha in base.TW_ALPHAS:
            model = TweedieRegressor(
                power=power, alpha=alpha, solver="newton-cholesky"
            ).fit(xa, a.PurePremium, sample_weight=a.Exposure)
            scores[alpha] = float(
                mean_tweedie_deviance(
                    y_val,
                    model.predict(xb),
                    sample_weight=w_val,
                    power=power,
                )
            )
        direct_alpha[power] = min(scores, key=lambda z: (scores[z], z))

    prep_outer = base.preprocessor()
    xtr = prep_outer.fit_transform(tr)
    xte = prep_outer.transform(te)
    freq_outer = {
        alpha: PoissonRegressor(alpha=alpha, solver="newton-cholesky")
        .fit(xtr, tr.Frequency, sample_weight=tr.Exposure)
        .predict(xte)
        for alpha in base.FREQ_ALPHAS
    }
    tr_pos = tr.ClaimAmount.to_numpy() > 0
    sev_outer = {
        alpha: GammaRegressor(alpha=alpha, solver="newton-cholesky")
        .fit(
            xtr[tr_pos],
            tr.loc[tr_pos, "AvgClaimAmount"],
            sample_weight=tr.loc[tr_pos, "ClaimNb"],
        )
        .predict(xte)
        for alpha in base.SEV_ALPHAS
    }

    y = te.PurePremium.to_numpy(float)
    w = te.Exposure.to_numpy(float)
    deltas: dict[float, np.ndarray] = {}
    aggregate: dict[str, dict] = {}
    for power in base.FIT_POWERS:
        fa, sa = joint[power]
        product = freq_outer[fa] * sev_outer[sa]
        direct = TweedieRegressor(
            power=power,
            alpha=direct_alpha[power],
            solver="newton-cholesky",
        ).fit(xtr, tr.PurePremium, sample_weight=tr.Exposure).predict(xte)

        direct_dev = unit_tweedie_deviance(y, direct, power)
        product_dev = unit_tweedie_deviance(y, product, power)
        direct_mean = float(np.average(direct_dev, weights=w))
        product_mean = float(np.average(product_dev, weights=w))
        sklearn_direct = float(
            mean_tweedie_deviance(y, direct, sample_weight=w, power=power)
        )
        sklearn_product = float(
            mean_tweedie_deviance(y, product, sample_weight=w, power=power)
        )
        if abs(direct_mean - sklearn_direct) > 1e-10 or abs(product_mean - sklearn_product) > 1e-10:
            raise AssertionError("unit deviance does not reproduce sklearn aggregate")
        point = direct_mean - product_mean
        if abs(point - EXPECTED[seed][power]) > 5e-6:
            raise AssertionError(
                f"point delta drift seed={seed} power={power}: {point} vs {EXPECTED[seed][power]}"
            )
        deltas[power] = direct_dev - product_dev
        aggregate[str(power)] = {
            "direct_mean_deviance": direct_mean,
            "product_mean_deviance": product_mean,
            "direct_minus_product": point,
            "joint_frequency_alpha": fa,
            "joint_severity_alpha": sa,
            "direct_alpha": direct_alpha[power],
        }

    ids = np.sort(d.index.to_numpy(np.int64)[outer_test])
    uncertainty = paired_bootstrap(
        w,
        deltas,
        seed=BOOTSTRAP_SEED + seed,
        reps=BOOTSTRAP_REPS,
    )
    return {
        "seed": seed,
        "test_rows": len(te),
        "test_positive_claim_rows": int((te.ClaimAmount > 0).sum()),
        "test_id_sha256": hashlib.sha256(ids.tobytes()).hexdigest(),
        "aggregate": aggregate,
        "paired_policy_bootstrap": uncertainty,
    }


def main() -> None:
    output = Path("ffbk1319-paired-uncertainty.json")
    freq, sev, meta = base.load()
    d, receipt = base.prepare(freq, sev, True)
    splits = [one_split(d, seed) for seed in base.SEEDS]
    result = {
        "schema": 1,
        "question": "post-exposure paired policy-row uncertainty for FFBK PR #1319 mean-model deviance gap",
        "protocol_source": "extends audited OpenCatastrophe-data independent runner commit 22b35856804c03944b41e5b424b071abc7714b45",
        "validation_boundary": "conditional on fitted models and already-observed outer splits; not a new holdout; does not propagate fit/tuning/split/cluster uncertainty",
        "bootstrap": {
            "method": "paired nonparametric policy-row bootstrap with replacement; original Exposure weights retained inside each resample",
            "reps": BOOTSTRAP_REPS,
            "seed": BOOTSTRAP_SEED,
        },
        "openml": meta,
        "data_receipt": receipt,
        "splits": splits,
    }
    payload = json.dumps(result, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    result["canonical_sha256"] = hashlib.sha256(payload).hexdigest()
    output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"result": str(output), "receipt": result["canonical_sha256"]}, sort_keys=True))


if __name__ == "__main__":
    main()
