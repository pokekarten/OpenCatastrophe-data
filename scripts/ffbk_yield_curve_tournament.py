# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Execute FFBK's preregistered H.15 yield-curve model-family tournament.

Execution-only public runner for pokekarten/FFBK research:
research/capital-modeling/yield-curve-dynamic-model-family-challenge-v0.md

The model set, split, horizons, DNS lambda and primary metrics are frozen by
that document. This runner adds only explicit transport/month-end semantics,
HAC lag h-1, and a 120-month rolling-window sensitivity before observing the
outcomes.
"""
from __future__ import annotations

import csv
import hashlib
import io
import json
import math
import platform
import sys
import urllib.request
from dataclasses import dataclass
from datetime import date

import numpy as np

SOURCE_URL = (
    "https://www.federalreserve.gov/datadownload/Output.aspx?"
    "rel=H15&series=bf17364827e38702b42a58cf8eaa3f78&lastobs=&from=&to=&"
    "filetype=csv&label=include&layout=seriescolumn&type=package"
)
SERIES = [
    "RIFLGFCM03_N.B",
    "RIFLGFCM06_N.B",
    "RIFLGFCY01_N.B",
    "RIFLGFCY02_N.B",
    "RIFLGFCY03_N.B",
    "RIFLGFCY05_N.B",
    "RIFLGFCY07_N.B",
    "RIFLGFCY10_N.B",
]
MATURITY_MONTHS = np.array([3.0, 6.0, 12.0, 24.0, 36.0, 60.0, 84.0, 120.0])
DNS_LAMBDA = 0.0609
FIRST_MONTH = "1990-01"
LAST_COMPLETE_MONTH = "2026-08"
TRAIN_END = "2010-12"
VALIDATION_START = "2011-01"
VALIDATION_END = "2019-12"
FINAL_START = "2020-01"
HORIZONS = (1, 12)
ROLLING_MONTHS = 120
MODELS = ("RW", "YieldAR1", "DNSAR1", "PCA3AR1")


def _download() -> bytes:
    req = urllib.request.Request(
        SOURCE_URL,
        headers={"User-Agent": "FFBK-NextGen-research/1.0 (+https://github.com/pokekarten/FFBK)"},
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        data = resp.read()
    if len(data) < 100_000:
        raise RuntimeError(f"H.15 package unexpectedly small: {len(data)} bytes")
    return data


def _parse_daily(raw: bytes) -> list[tuple[date, np.ndarray]]:
    text = raw.decode("utf-8-sig")
    rows = list(csv.reader(io.StringIO(text)))
    header_idx = None
    col_idx: dict[str, int] = {}
    for i, row in enumerate(rows[:30]):
        normalized = [c.strip().split("/")[-1] for c in row]
        found = {s: normalized.index(s) for s in SERIES if s in normalized}
        if len(found) == len(SERIES):
            header_idx = i
            col_idx = found
            break
    if header_idx is None:
        preview = "\n".join(",".join(r[:5]) for r in rows[:10])
        raise RuntimeError(f"Could not locate H.15 series header. Preview:\n{preview}")

    out: list[tuple[date, np.ndarray]] = []
    for row in rows[header_idx + 1 :]:
        if not row:
            continue
        d = None
        for cell in row[:2]:
            cell = cell.strip()
            for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%m/%d/%y"):
                try:
                    import datetime as _dt
                    d = _dt.datetime.strptime(cell, fmt).date()
                    break
                except ValueError:
                    pass
            if d is not None:
                break
        if d is None:
            continue
        vals = []
        complete = True
        for s in SERIES:
            j = col_idx[s]
            if j >= len(row):
                complete = False
                break
            cell = row[j].strip()
            if cell in {"", "ND", ".", "NA", "N/A"}:
                complete = False
                break
            try:
                vals.append(float(cell))
            except ValueError:
                complete = False
                break
        if complete:
            out.append((d, np.array(vals, dtype=float)))
    if not out:
        raise RuntimeError("No complete H.15 daily observations parsed")
    return sorted(out, key=lambda x: x[0])


def _monthly_last_common(daily: list[tuple[date, np.ndarray]]) -> tuple[list[str], np.ndarray, list[str]]:
    by_month: dict[str, tuple[date, np.ndarray]] = {}
    for d, vals in daily:
        month = f"{d.year:04d}-{d.month:02d}"
        if FIRST_MONTH <= month <= LAST_COMPLETE_MONTH:
            prior = by_month.get(month)
            if prior is None or d > prior[0]:
                by_month[month] = (d, vals)
    expected = []
    y, m = map(int, FIRST_MONTH.split("-"))
    ey, em = map(int, LAST_COMPLETE_MONTH.split("-"))
    while (y, m) <= (ey, em):
        expected.append(f"{y:04d}-{m:02d}")
        m += 1
        if m == 13:
            y += 1
            m = 1
    missing = [x for x in expected if x not in by_month]
    if missing:
        raise RuntimeError(f"Missing complete monthly H.15 observations: {missing[:20]}")
    months = expected
    values = np.vstack([by_month[x][1] for x in months])
    dates = [by_month[x][0].isoformat() for x in months]
    return months, values, dates


def _fit_ar1(x: np.ndarray) -> tuple[float, float]:
    x = np.asarray(x, dtype=float)
    if x.size < 3:
        raise ValueError("AR(1) requires at least 3 observations")
    X = np.column_stack([np.ones(x.size - 1), x[:-1]])
    beta, *_ = np.linalg.lstsq(X, x[1:], rcond=None)
    return float(beta[0]), float(beta[1])


def _ar_h_forecast(x: np.ndarray, h: int) -> float:
    a, b = _fit_ar1(x)
    v = float(x[-1])
    for _ in range(h):
        v = a + b * v
    return v


def _dns_loadings() -> np.ndarray:
    t = MATURITY_MONTHS
    lam = DNS_LAMBDA
    x = (1.0 - np.exp(-lam * t)) / (lam * t)
    return np.column_stack([np.ones_like(t), x, x - np.exp(-lam * t)])


DNS_LOADINGS = _dns_loadings()
DNS_PINV = np.linalg.pinv(DNS_LOADINGS)


def _forecast_model(history: np.ndarray, h: int, model: str) -> np.ndarray:
    if model == "RW":
        return history[-1].copy()
    if model == "YieldAR1":
        return np.array([_ar_h_forecast(history[:, j], h) for j in range(history.shape[1])])
    if model == "DNSAR1":
        factors = history @ DNS_PINV.T
        fhat = np.array([_ar_h_forecast(factors[:, j], h) for j in range(3)])
        return DNS_LOADINGS @ fhat
    if model == "PCA3AR1":
        mean = history.mean(axis=0)
        centered = history - mean
        _, _, vt = np.linalg.svd(centered, full_matrices=False)
        comps = vt[:3]
        scores = centered @ comps.T
        shat = np.array([_ar_h_forecast(scores[:, j], h) for j in range(3)])
        return mean + shat @ comps
    raise ValueError(model)


@dataclass
class ForecastSet:
    months: list[str]
    actual: np.ndarray
    preds: dict[str, np.ndarray]


def _forecast_period(months: list[str], values: np.ndarray, start: str, end: str, h: int, window: int | None) -> ForecastSet:
    idx = {m: i for i, m in enumerate(months)}
    targets = [m for m in months if start <= m <= end]
    actual = []
    pred_rows = {model: [] for model in MODELS}
    for target in targets:
        ti = idx[target]
        origin = ti - h
        if origin < 2:
            raise RuntimeError("Insufficient history")
        hs = 0 if window is None else max(0, origin + 1 - window)
        hist = values[hs : origin + 1]
        actual.append(values[ti])
        for model in MODELS:
            pred_rows[model].append(_forecast_model(hist, h, model))
    return ForecastSet(targets, np.vstack(actual), {k: np.vstack(v) for k, v in pred_rows.items()})


def _rmse(x: np.ndarray) -> float:
    return float(np.sqrt(np.mean(np.square(x))))


def _mae(x: np.ndarray) -> float:
    return float(np.mean(np.abs(x)))


def _hac_mean_ci(d: np.ndarray, lag: int) -> dict[str, float | int]:
    d = np.asarray(d, dtype=float)
    n = len(d)
    mean = float(np.mean(d))
    u = d - mean
    gamma0 = float(np.dot(u, u) / n)
    lrv = gamma0
    for k in range(1, min(lag, n - 1) + 1):
        gamma = float(np.dot(u[k:], u[:-k]) / n)
        weight = 1.0 - k / (lag + 1.0)
        lrv += 2.0 * weight * gamma
    lrv = max(lrv, 0.0)
    se = math.sqrt(lrv / n)
    return {
        "n": n,
        "lag": lag,
        "mean_difference": mean,
        "hac_se": se,
        "ci95_low": mean - 1.96 * se,
        "ci95_high": mean + 1.96 * se,
    }


def _metrics(fs: ForecastSet, h: int) -> dict:
    out: dict[str, dict] = {}
    actual_bp = fs.actual * 100.0
    for model, p in fs.preds.items():
        pred_bp = p * 100.0
        err = pred_bp - actual_bp
        slope_err = (pred_bp[:, 7] - pred_bp[:, 3]) - (actual_bp[:, 7] - actual_bp[:, 3])
        out[model] = {
            "aggregate": {"rmsfe_bp": _rmse(err), "mae_bp": _mae(err)},
            "maturity": {
                SERIES[j]: {"rmsfe_bp": _rmse(err[:, j]), "mae_bp": _mae(err[:, j])}
                for j in range(len(SERIES))
            },
            "ten_year": {"rmsfe_bp": _rmse(err[:, 7]), "mae_bp": _mae(err[:, 7])},
            "ten_year_minus_two_year_slope": {"rmsfe_bp": _rmse(slope_err), "mae_bp": _mae(slope_err)},
        }
    rw_err = fs.preds["RW"] * 100.0 - actual_bp
    rw_mse = np.mean(np.square(rw_err), axis=1)
    rw_ae = np.mean(np.abs(rw_err), axis=1)
    paired = {}
    for model in MODELS[1:]:
        err = fs.preds[model] * 100.0 - actual_bp
        mse_d = np.mean(np.square(err), axis=1) - rw_mse
        ae_d = np.mean(np.abs(err), axis=1) - rw_ae
        paired[model] = {
            "mean_cross_maturity_squared_error_bp2_minus_rw": _hac_mean_ci(mse_d, h - 1),
            "mean_cross_maturity_absolute_error_bp_minus_rw": _hac_mean_ci(ae_d, h - 1),
        }
    return {"n_targets": len(fs.months), "models": out, "paired_vs_rw": paired}


def _slice(fs: ForecastSet, start: str, end: str) -> ForecastSet:
    keep = [i for i, m in enumerate(fs.months) if start <= m <= end]
    return ForecastSet(
        [fs.months[i] for i in keep],
        fs.actual[keep],
        {k: v[keep] for k, v in fs.preds.items()},
    )


def main() -> None:
    raw = _download()
    raw_sha = hashlib.sha256(raw).hexdigest()
    daily = _parse_daily(raw)
    months, values, source_dates = _monthly_last_common(daily)
    if months[0] != FIRST_MONTH or months[-1] != LAST_COMPLETE_MONTH:
        raise RuntimeError((months[0], months[-1]))

    result: dict = {
        "research_fingerprint": "economic-scenario/yield-curve/dynamic-model-family/h15/temporal-holdout-v0",
        "source": {
            "authority": "Board of Governors H.15 Data Download Program",
            "url": SOURCE_URL,
            "package_series_hash": "bf17364827e38702b42a58cf8eaa3f78",
            "retrieved_raw_sha256": raw_sha,
            "retrieved_bytes": len(raw),
            "units": "percent per annum, not seasonally adjusted",
            "frequency": "daily source; last complete common business-day observation per calendar month",
            "first_month": months[0],
            "last_complete_month": months[-1],
            "monthly_observations": len(months),
            "last_month_source_date": source_dates[-1],
            "series": SERIES,
        },
        "protocol": {
            "training_history": [FIRST_MONTH, TRAIN_END],
            "validation": [VALIDATION_START, VALIDATION_END],
            "final_untouched_target_period": [FINAL_START, LAST_COMPLETE_MONTH],
            "horizons_months": list(HORIZONS),
            "models": list(MODELS),
            "dns_lambda_month_units": DNS_LAMBDA,
            "pca_components": 3,
            "expanding_window_primary": True,
            "rolling_sensitivity_months": ROLLING_MONTHS,
            "hac_lag_rule": "horizon_minus_one",
        },
        "runtime": {"python": sys.version.split()[0], "numpy": np.__version__, "platform": platform.platform()},
        "results": {},
    }

    for h in HORIZONS:
        val = _forecast_period(months, values, VALIDATION_START, VALIDATION_END, h, None)
        final = _forecast_period(months, values, FINAL_START, LAST_COMPLETE_MONTH, h, None)
        rolling_final = _forecast_period(months, values, FINAL_START, LAST_COMPLETE_MONTH, h, ROLLING_MONTHS)
        result["results"][str(h)] = {
            "validation_expanding": _metrics(val, h),
            "final_expanding": _metrics(final, h),
            "final_regime_2020_2021": _metrics(_slice(final, "2020-01", "2021-12"), h),
            "final_regime_2022_latest": _metrics(_slice(final, "2022-01", LAST_COMPLETE_MONTH), h),
            "final_rolling_120m_sensitivity": _metrics(rolling_final, h),
        }

    print("FFBK_YIELD_CURVE_TOURNAMENT_RESULT_BEGIN")
    print(json.dumps(result, sort_keys=True, indent=2))
    print("FFBK_YIELD_CURVE_TOURNAMENT_RESULT_END")


if __name__ == "__main__":
    main()
