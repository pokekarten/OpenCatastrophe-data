#!/usr/bin/env python3
"""Temporary freMTPL2 duration-aware frequency challenger for FFBK research.

Execution-only code on a disposable public branch. It does not belong to the
OpenCatastrophe-data product. The model class and fresh confirmation seeds were
predeclared in FFBK issue #1318 before target execution.

Consumer: expected claim count / annualised claim frequency conditional on
policy covariates and observed duration (Exposure).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import platform
import urllib.request
from pathlib import Path

import numpy as np
import pandas as pd

QUESTION_FINGERPRINT = "underwriting/fremtpl2/duration/pro-rata/frequency-mean/fresh-confirmation"
EXPLORATORY_SEEDS = (0, 17, 42)
CONFIRMATION_SEEDS = (1669415631, 689796627, 1599413584)
FREQ_ALPHAS = (1e-4, 1e-3)
DURATION_FORMS = ("log", "spline")
BANDS = (
    (0.0, 0.25, "(0,0.25]"),
    (0.25, 0.50, "(0.25,0.50]"),
    (0.50, 0.75, "(0.50,0.75]"),
    (0.75, 1.00, "(0.75,1.00]"),
)


def _meta(data_id: int) -> dict:
    with urllib.request.urlopen(
        f"https://www.openml.org/api/v1/json/data/{data_id}", timeout=60
    ) as response:
        desc = json.load(response)["data_set_description"]
    return {
        key: desc.get(key)
        for key in (
            "id",
            "name",
            "version",
            "file_id",
            "md5_checksum",
            "status",
            "url",
            "parquet_url",
        )
    }


def load_target() -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    from sklearn.datasets import fetch_openml

    frequency = fetch_openml(data_id=41214, as_frame=True).data.copy()
    severity = fetch_openml(data_id=41215, as_frame=True).data.copy()
    frequency["IDpol"] = frequency["IDpol"].astype("int64")
    severity["IDpol"] = severity["IDpol"].astype("int64")
    severity["ClaimAmount"] = severity["ClaimAmount"].astype(float)
    return frequency, severity, {
        "frequency": _meta(41214),
        "severity": _meta(41215),
    }


def prepare(
    frequency: pd.DataFrame,
    severity: pd.DataFrame,
    *,
    raw_claimnb: bool,
) -> tuple[pd.DataFrame, dict]:
    """Match the #1319 reference decomposition except for isolated ClaimNb mode."""
    x = frequency.copy()
    for column in x.columns:
        if x[column].dtype == object or isinstance(x[column].dtype, pd.CategoricalDtype):
            x[column] = x[column].astype(str).str.strip("'")

    amounts = severity.groupby("IDpol", sort=False)["ClaimAmount"].sum()
    data = x.set_index("IDpol")
    raw_nb = data["ClaimNb"].astype(float).copy()
    raw_exposure = data["Exposure"].astype(float).copy()
    data["ClaimAmount"] = (
        data.index.to_series().map(amounts).fillna(0.0).astype(float).clip(upper=200000.0)
    )
    data["ClaimNb"] = raw_nb if raw_claimnb else raw_nb.clip(upper=4)
    data["Exposure"] = raw_exposure.clip(upper=1)

    reset = (data["ClaimAmount"] == 0.0) & (data["ClaimNb"] >= 1.0)
    data.loc[reset, "ClaimNb"] = 0.0
    if not bool((data["Exposure"] > 0).all()):
        raise ValueError("non-positive Exposure after preparation")

    data["Frequency"] = data["ClaimNb"] / data["Exposure"]
    receipt = {
        "rows": int(len(data)),
        "idpol_unique": bool(data.index.is_unique),
        "severity_rows": int(len(severity)),
        "severity_orphans": int((~severity["IDpol"].isin(frequency["IDpol"])).sum()),
        "raw_claimnb_gt4_rows": int((raw_nb > 4).sum()),
        "raw_claimnb_gt4_excess_count": float((raw_nb - raw_nb.clip(upper=4)).sum()),
        "exposure_gt1_rows": int((raw_exposure > 1).sum()),
        "zero_amount_reset_rows": int(reset.sum()),
        "prepared_total_exposure": float(data["Exposure"].sum()),
        "prepared_total_claimnb": float(data["ClaimNb"].sum()),
        "raw_claimnb": bool(raw_claimnb),
    }
    return data, receipt


def preprocessor(duration_form: str):
    from sklearn.compose import ColumnTransformer
    from sklearn.pipeline import make_pipeline
    from sklearn.preprocessing import (
        FunctionTransformer,
        KBinsDiscretizer,
        OneHotEncoder,
        SplineTransformer,
        StandardScaler,
    )

    transforms = [
        (
            "bin",
            KBinsDiscretizer(
                n_bins=10,
                quantile_method="averaged_inverted_cdf",
                random_state=0,
            ),
            ["VehAge", "DrivAge"],
        ),
        (
            "cat",
            OneHotEncoder(handle_unknown="ignore"),
            ["VehBrand", "VehPower", "VehGas", "Region", "Area"],
        ),
        ("num", "passthrough", ["BonusMalus"]),
        (
            "density",
            make_pipeline(
                FunctionTransformer(func=np.log, feature_names_out="one-to-one"),
                StandardScaler(),
            ),
            ["Density"],
        ),
    ]
    if duration_form == "log":
        transforms.append(
            (
                "duration_log",
                make_pipeline(
                    FunctionTransformer(func=np.log, feature_names_out="one-to-one"),
                    StandardScaler(),
                ),
                ["Exposure"],
            )
        )
    elif duration_form == "spline":
        transforms.append(
            (
                "duration_spline",
                SplineTransformer(
                    n_knots=4,
                    degree=2,
                    knots="quantile",
                    include_bias=False,
                ),
                ["Exposure"],
            )
        )
    elif duration_form != "none":
        raise ValueError(f"unknown duration form: {duration_form}")
    return ColumnTransformer(transforms)


def _poisson_fit_predict(train, target, duration_form: str, alpha: float):
    from sklearn.linear_model import PoissonRegressor

    transformer = preprocessor(duration_form)
    x_train = transformer.fit_transform(train)
    x_target = transformer.transform(target)
    model = PoissonRegressor(alpha=alpha, solver="newton-cholesky")
    model.fit(
        x_train,
        train["Frequency"],
        sample_weight=train["Exposure"],
    )
    return model.predict(x_target), model.predict(x_train)


def _validation_scores(inner_fit, inner_val, forms: tuple[str, ...]) -> dict:
    from sklearn.linear_model import PoissonRegressor
    from sklearn.metrics import mean_poisson_deviance

    result: dict[str, dict[str, float]] = {}
    for form in forms:
        transformer = preprocessor(form)
        x_fit = transformer.fit_transform(inner_fit)
        x_val = transformer.transform(inner_val)
        scores: dict[str, float] = {}
        for alpha in FREQ_ALPHAS:
            model = PoissonRegressor(alpha=alpha, solver="newton-cholesky")
            model.fit(
                x_fit,
                inner_fit["Frequency"],
                sample_weight=inner_fit["Exposure"],
            )
            pred = model.predict(x_val)
            scores[str(alpha)] = float(
                mean_poisson_deviance(
                    inner_val["Frequency"],
                    pred,
                    sample_weight=inner_val["Exposure"],
                )
            )
        result[form] = scores
    return result


def _select(scores: dict, forms: tuple[str, ...]) -> tuple[str, float, float]:
    complexity_rank = {"none": 0, "log": 1, "spline": 2}
    candidates = []
    for form in forms:
        for alpha_text, score in scores[form].items():
            alpha = float(alpha_text)
            candidates.append((float(score), complexity_rank[form], alpha, form))
    score, _, alpha, form = min(candidates)
    return form, alpha, score


def _risk_edges(train_pred: np.ndarray) -> list[float]:
    return [float(x) for x in np.quantile(train_pred, [0.25, 0.50, 0.75])]


def _cell_summary(test: pd.DataFrame, pred: np.ndarray, risk_edges: list[float]) -> dict:
    exposure = test["Exposure"].to_numpy(float)
    observed = test["ClaimNb"].to_numpy(float)
    predicted_count = exposure * np.asarray(pred, float)
    risk = np.searchsorted(np.asarray(risk_edges), np.asarray(pred, float), side="right")

    def summarize(mask: np.ndarray) -> dict:
        obs = float(observed[mask].sum())
        fit = float(predicted_count[mask].sum())
        return {
            "rows": int(mask.sum()),
            "observed_claims": obs,
            "predicted_claims": fit,
            "predicted_over_observed": None if obs <= 0 else fit / obs,
        }

    bands: dict[str, dict] = {}
    band_risk: dict[str, dict] = {}
    for lo, hi, label in BANDS:
        band_mask = (exposure > lo) & (exposure <= hi)
        bands[label] = summarize(band_mask)
        band_risk[label] = {
            str(group): summarize(band_mask & (risk == group)) for group in range(4)
        }
    return {
        "overall": summarize(np.ones(len(test), dtype=bool)),
        "duration_bands": bands,
        "duration_by_train_baseline_risk_quartile": band_risk,
    }


def one_split(data: pd.DataFrame, seed: int, label: str) -> dict:
    from sklearn.linear_model import PoissonRegressor
    from sklearn.metrics import mean_poisson_deviance
    from sklearn.model_selection import train_test_split

    outer_train_idx, outer_test_idx = train_test_split(
        np.arange(len(data)), test_size=0.25, random_state=seed
    )
    outer_train = data.iloc[outer_train_idx]
    outer_test = data.iloc[outer_test_idx]
    inner_fit_idx, inner_val_idx = train_test_split(
        np.arange(len(outer_train)), test_size=0.20, random_state=seed + 10000
    )
    inner_fit = outer_train.iloc[inner_fit_idx]
    inner_val = outer_train.iloc[inner_val_idx]

    validation = _validation_scores(
        inner_fit,
        inner_val,
        forms=("none",) + DURATION_FORMS,
    )
    baseline_form, baseline_alpha, baseline_val = _select(validation, ("none",))
    challenger_form, challenger_alpha, challenger_val = _select(validation, DURATION_FORMS)

    baseline_transformer = preprocessor(baseline_form)
    baseline_x_train = baseline_transformer.fit_transform(outer_train)
    baseline_x_test = baseline_transformer.transform(outer_test)
    baseline_model = PoissonRegressor(alpha=baseline_alpha, solver="newton-cholesky")
    baseline_model.fit(
        baseline_x_train,
        outer_train["Frequency"],
        sample_weight=outer_train["Exposure"],
    )
    baseline_test_pred = baseline_model.predict(baseline_x_test)
    baseline_train_pred = baseline_model.predict(baseline_x_train)

    challenger_transformer = preprocessor(challenger_form)
    challenger_x_train = challenger_transformer.fit_transform(outer_train)
    challenger_x_test = challenger_transformer.transform(outer_test)
    challenger_model = PoissonRegressor(alpha=challenger_alpha, solver="newton-cholesky")
    challenger_model.fit(
        challenger_x_train,
        outer_train["Frequency"],
        sample_weight=outer_train["Exposure"],
    )
    challenger_test_pred = challenger_model.predict(challenger_x_test)

    baseline_dev = float(
        mean_poisson_deviance(
            outer_test["Frequency"],
            baseline_test_pred,
            sample_weight=outer_test["Exposure"],
        )
    )
    challenger_dev = float(
        mean_poisson_deviance(
            outer_test["Frequency"],
            challenger_test_pred,
            sample_weight=outer_test["Exposure"],
        )
    )
    risk_edges = _risk_edges(baseline_train_pred)
    test_ids = np.sort(data.index.to_numpy(np.int64)[outer_test_idx])

    return {
        "seed": int(seed),
        "validation_label": label,
        "train_rows": int(len(outer_train)),
        "test_rows": int(len(outer_test)),
        "test_id_sha256": hashlib.sha256(test_ids.tobytes()).hexdigest(),
        "selected": {
            "baseline": {
                "form": baseline_form,
                "alpha": baseline_alpha,
                "inner_validation_deviance": baseline_val,
            },
            "duration_challenger": {
                "form": challenger_form,
                "alpha": challenger_alpha,
                "inner_validation_deviance": challenger_val,
            },
        },
        "inner_validation_scores": validation,
        "outer_test": {
            "baseline_poisson_deviance": baseline_dev,
            "duration_challenger_poisson_deviance": challenger_dev,
            "baseline_minus_challenger_deviance": baseline_dev - challenger_dev,
            "baseline": _cell_summary(outer_test, baseline_test_pred, risk_edges),
            "duration_challenger": _cell_summary(
                outer_test, challenger_test_pred, risk_edges
            ),
            "train_baseline_risk_quartile_edges": risk_edges,
        },
    }


def environment_receipt() -> dict:
    import scipy
    import sklearn

    return {
        "python": platform.python_version(),
        "numpy": np.__version__,
        "pandas": pd.__version__,
        "scipy": scipy.__version__,
        "sklearn": sklearn.__version__,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--claimnb",
        choices=("reference", "raw"),
        required=True,
        help="reference applies ClaimNb<=4; raw removes only that cap",
    )
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    frequency, severity, openml = load_target()
    data, data_receipt = prepare(
        frequency,
        severity,
        raw_claimnb=args.claimnb == "raw",
    )
    splits = [
        one_split(data, seed, "exploratory_exposed") for seed in EXPLORATORY_SEEDS
    ] + [
        one_split(data, seed, "prospective_same_lineage_confirmation")
        for seed in CONFIRMATION_SEEDS
    ]

    payload = {
        "schema": 1,
        "question_fingerprint": QUESTION_FINGERPRINT,
        "model_design_status": (
            "adaptive_followup_to_observed_1319_duration_bands; "
            "fresh confirmation seeds predeclared before this target execution"
        ),
        "confirmation_seed_derivation": (
            "first three big-endian uint32 SHA-256 chunks of question_fingerprint, "
            "masked to signed-31-bit"
        ),
        "exploratory_seeds": list(EXPLORATORY_SEEDS),
        "confirmation_seeds": list(CONFIRMATION_SEEDS),
        "claimnb_variant": args.claimnb,
        "openml": openml,
        "environment": environment_receipt(),
        "data_receipt": data_receipt,
        "splits": splits,
        "interpretation_boundary": (
            "Fresh seeds are prospective same-dataset holdouts, not independent-data evidence. "
            "Seeds 0/17/42 are exploratory because their duration bands motivated the challenger."
        ),
    }
    payload["canonical_sha256"] = hashlib.sha256(
        json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode()
    ).hexdigest()
    args.output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    print(
        json.dumps(
            {
                "claimnb": args.claimnb,
                "receipt": payload["canonical_sha256"],
                "rows": len(data),
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
