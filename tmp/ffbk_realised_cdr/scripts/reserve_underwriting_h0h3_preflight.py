#!/usr/bin/env python3
"""Offline preflight for the FFBK UW↔reserve H0/H1/H2/H3 challenger.

This is deliberately a *protocol / discrimination harness*, not a production
calibration.  It enforces the post-#1546 target boundary: reserve-side input
must be a realised one-year CDR, not raw incurred emergence.

The runner consumes a small, already-materialised panel with columns:

    company,lob,year,uw,cdr[,shared_driver]

and evaluates deterministic temporal and leave-one-company-out holdouts under:

H0  conditional independence with intercept-only marginals
H1  one globally pooled residual Gaussian correlation
H2  Fisher-z partial pooling of company×LoB residual correlations
H3  explicit numeric shared-driver marginals + conditional independence

The scores are bivariate Gaussian negative log predictive scores.  They are a
bounded model-comparison surface only.  No 99.5% capital, copula-family, or
hierarchical default is promoted by this script.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

EPS = 1e-12


@dataclass(frozen=True)
class Row:
    company: str
    lob: str
    year: int
    uw: float
    cdr: float
    shared_driver: float | None = None

    @property
    def group(self) -> tuple[str, str]:
        return (self.company, self.lob)


def _finite(value: float, name: str) -> float:
    if not math.isfinite(value):
        raise ValueError(f"{name} must be finite")
    return value


def file_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def read_panel(path: Path) -> list[Row]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        required = {"company", "lob", "year", "uw", "cdr"}
        missing = required - set(reader.fieldnames or ())
        if missing:
            raise ValueError(f"missing required columns: {sorted(missing)}")
        has_driver = "shared_driver" in (reader.fieldnames or ())
        rows: list[Row] = []
        seen: set[tuple[str, str, int]] = set()
        for lineno, raw in enumerate(reader, start=2):
            company = (raw.get("company") or "").strip()
            lob = (raw.get("lob") or "").strip()
            if not company or not lob:
                raise ValueError(f"line {lineno}: company/lob required")
            year = int(raw["year"])
            key = (company, lob, year)
            if key in seen:
                raise ValueError(f"duplicate company/lob/year: {key}")
            seen.add(key)
            driver: float | None = None
            if has_driver and (raw.get("shared_driver") or "").strip() != "":
                driver = _finite(float(raw["shared_driver"]), "shared_driver")
            rows.append(
                Row(
                    company=company,
                    lob=lob,
                    year=year,
                    uw=_finite(float(raw["uw"]), "uw"),
                    cdr=_finite(float(raw["cdr"]), "cdr"),
                    shared_driver=driver,
                )
            )
    if not rows:
        raise ValueError("panel is empty")
    return sorted(rows, key=lambda r: (r.company, r.lob, r.year))


def validate_target_kind(target_kind: str) -> None:
    if target_kind != "REALISED_CDR":
        raise ValueError(
            "reserve target must be REALISED_CDR; legacy incurred-emergence proxy is not admissible"
        )


def mean(values: Iterable[float]) -> float:
    xs = list(values)
    if not xs:
        raise ValueError("empty mean")
    return sum(xs) / len(xs)


def sample_sd(values: Iterable[float]) -> float:
    xs = list(values)
    if len(xs) < 2:
        raise ValueError("at least two values required")
    m = mean(xs)
    v = sum((x - m) ** 2 for x in xs) / (len(xs) - 1)
    return math.sqrt(max(v, EPS))


def pearson(xs: list[float], ys: list[float]) -> float:
    if len(xs) != len(ys) or len(xs) < 2:
        raise ValueError("correlation requires paired observations")
    mx, my = mean(xs), mean(ys)
    sxx = sum((x - mx) ** 2 for x in xs)
    syy = sum((y - my) ** 2 for y in ys)
    if sxx <= EPS or syy <= EPS:
        return 0.0
    r = sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / math.sqrt(sxx * syy)
    return max(-0.999999, min(0.999999, r))


def fit_linear(xs: list[float], ys: list[float]) -> tuple[float, float]:
    if len(xs) != len(ys) or len(xs) < 2:
        raise ValueError("linear fit requires paired observations")
    mx, my = mean(xs), mean(ys)
    denom = sum((x - mx) ** 2 for x in xs)
    slope = 0.0 if denom <= EPS else sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / denom
    return my - slope * mx, slope


def bivar_nll(x: float, y: float, mx: float, my: float, sx: float, sy: float, rho: float) -> float:
    rho = max(-0.999, min(0.999, rho))
    sx, sy = max(sx, EPS), max(sy, EPS)
    zx, zy = (x - mx) / sx, (y - my) / sy
    one_minus = 1.0 - rho * rho
    quad = (zx * zx - 2.0 * rho * zx * zy + zy * zy) / one_minus
    return (
        math.log(2.0 * math.pi)
        + math.log(sx)
        + math.log(sy)
        + 0.5 * math.log(one_minus)
        + 0.5 * quad
    )


def fit_intercept_marginals(train: list[Row]) -> dict[str, float]:
    ux = [r.uw for r in train]
    cy = [r.cdr for r in train]
    return {"mx": mean(ux), "my": mean(cy), "sx": sample_sd(ux), "sy": sample_sd(cy)}


def fit_driver_marginals(train: list[Row]) -> dict[str, float]:
    if any(r.shared_driver is None for r in train):
        raise ValueError("H3 requires shared_driver for every training row")
    d = [float(r.shared_driver) for r in train]
    ux = [r.uw for r in train]
    cy = [r.cdr for r in train]
    au, bu = fit_linear(d, ux)
    ac, bc = fit_linear(d, cy)
    ur = [u - (au + bu * x) for u, x in zip(ux, d)]
    cr = [c - (ac + bc * x) for c, x in zip(cy, d)]
    return {
        "uw_intercept": au,
        "uw_slope": bu,
        "cdr_intercept": ac,
        "cdr_slope": bc,
        "sx": sample_sd(ur),
        "sy": sample_sd(cr),
    }


def global_residual_rho(train: list[Row], marg: dict[str, float]) -> float:
    ux = [(r.uw - marg["mx"]) / marg["sx"] for r in train]
    cy = [(r.cdr - marg["my"]) / marg["sy"] for r in train]
    return pearson(ux, cy)


def fisher_partial_pool(train: list[Row], global_rho: float) -> dict[tuple[str, str], float]:
    by_group: dict[tuple[str, str], list[Row]] = {}
    for r in train:
        by_group.setdefault(r.group, []).append(r)
    effects: list[tuple[tuple[str, str], float, float]] = []
    for group, rows in by_group.items():
        if len(rows) < 4:
            continue
        rg = pearson([r.uw for r in rows], [r.cdr for r in rows])
        z = math.atanh(max(-0.999999, min(0.999999, rg)))
        v = 1.0 / (len(rows) - 3)
        effects.append((group, z, v))
    if not effects:
        return {}
    weights = [1.0 / v for _, _, v in effects]
    zbar = sum(w * z for w, (_, z, _) in zip(weights, effects)) / sum(weights)
    q = sum(w * (z - zbar) ** 2 for w, (_, z, _) in zip(weights, effects))
    c = sum(weights) - sum(w * w for w in weights) / sum(weights)
    tau2 = max(0.0, (q - (len(effects) - 1)) / c) if c > EPS else 0.0
    prior_z = math.atanh(max(-0.999999, min(0.999999, global_rho)))
    out: dict[tuple[str, str], float] = {}
    for group, z, v in effects:
        if tau2 <= EPS:
            post = prior_z
        else:
            precision_data = 1.0 / v
            precision_prior = 1.0 / tau2
            post = (precision_data * z + precision_prior * prior_z) / (precision_data + precision_prior)
        out[group] = math.tanh(post)
    return out


def temporal_split(rows: list[Row]) -> tuple[list[Row], list[Row]]:
    latest: dict[tuple[str, str], int] = {}
    for r in rows:
        latest[r.group] = max(latest.get(r.group, r.year), r.year)
    test = [r for r in rows if r.year == latest[r.group]]
    train = [r for r in rows if r.year != latest[r.group]]
    if len(train) < 4 or not test:
        raise ValueError("insufficient temporal split")
    return train, test


def score_models(train: list[Row], test: list[Row]) -> dict[str, dict[str, float | int | str]]:
    marg = fit_intercept_marginals(train)
    rho1 = global_residual_rho(train, marg)
    pooled = fisher_partial_pool(train, rho1)

    totals = {"H0": 0.0, "H1": 0.0, "H2": 0.0}
    for r in test:
        totals["H0"] += bivar_nll(r.uw, r.cdr, marg["mx"], marg["my"], marg["sx"], marg["sy"], 0.0)
        totals["H1"] += bivar_nll(r.uw, r.cdr, marg["mx"], marg["my"], marg["sx"], marg["sy"], rho1)
        rho2 = pooled.get(r.group, rho1)
        totals["H2"] += bivar_nll(r.uw, r.cdr, marg["mx"], marg["my"], marg["sx"], marg["sy"], rho2)

    out: dict[str, dict[str, float | int | str]] = {
        key: {"n_test": len(test), "total_nll": value, "mean_nll": value / len(test)}
        for key, value in totals.items()
    }
    out["H1"]["rho"] = rho1
    out["H2"]["fitted_group_count"] = len(pooled)

    if all(r.shared_driver is not None for r in train + test):
        dfit = fit_driver_marginals(train)
        total = 0.0
        for r in test:
            d = float(r.shared_driver)
            mx = dfit["uw_intercept"] + dfit["uw_slope"] * d
            my = dfit["cdr_intercept"] + dfit["cdr_slope"] * d
            total += bivar_nll(r.uw, r.cdr, mx, my, dfit["sx"], dfit["sy"], 0.0)
        out["H3"] = {"n_test": len(test), "total_nll": total, "mean_nll": total / len(test), "status": "EVALUATED"}
    else:
        out["H3"] = {"n_test": len(test), "total_nll": float("nan"), "mean_nll": float("nan"), "status": "BLOCKED_BY_SHARED_DRIVER_DATA"}
    return out


def leave_one_company_out(rows: list[Row]) -> list[dict[str, object]]:
    companies = sorted({r.company for r in rows})
    results: list[dict[str, object]] = []
    for company in companies:
        train = [r for r in rows if r.company != company]
        test = [r for r in rows if r.company == company]
        if len(train) < 4 or len(test) < 1:
            continue
        scores = score_models(train, test)
        results.append({"held_out_company": company, "n_test": len(test), "scores": scores})
    return results


def run(path: Path, target_kind: str, expected_input_sha256: str | None = None) -> dict[str, object]:
    validate_target_kind(target_kind)
    digest = file_sha256(path)
    if expected_input_sha256 and digest != expected_input_sha256:
        raise ValueError("input SHA-256 mismatch")
    rows = read_panel(path)
    train, test = temporal_split(rows)
    temporal = score_models(train, test)
    company_holdouts = leave_one_company_out(rows)
    return {
        "schema": "ffbk.uw_reserve_h0h3_preflight.v0",
        "scope": "protocol/preflight only; realised CDR required; no model promotion",
        "input": {"path": path.name, "sha256": digest, "rows": len(rows)},
        "target_kind": target_kind,
        "temporal_holdout": {"train_rows": len(train), "test_rows": len(test), "scores": temporal},
        "company_holdouts": company_holdouts,
        "verdict": {
            "empirical_winner_claimed": False,
            "global_scalar_promoted": False,
            "hierarchical_model_promoted": False,
            "shared_driver_model_promoted": False,
            "reason": "This harness only makes the pre-registered comparison executable; model promotion requires source-qualified real-panel execution and independent review.",
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("panel", type=Path)
    parser.add_argument("--target-kind", required=True, choices=["REALISED_CDR", "LEGACY_INCURRED_EMERGENCE"])
    parser.add_argument("--expected-input-sha256")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    payload = run(args.panel, args.target_kind, args.expected_input_sha256)
    text = json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=True) + "\n"
    if args.output:
        args.output.write_text(text, encoding="utf-8")
    else:
        print(text, end="")


if __name__ == "__main__":
    main()
