# Temporary public-data execution probe for FFBK research only.
# This file is intentionally outside the OpenCatastrophe-data product surface.
from __future__ import annotations

import hashlib
import json
import math
import platform
import sys
import urllib.request
from pathlib import Path

import numpy as np
import pandas as pd

SOURCE_COMMIT = "10af669a599c1d4d69288f62f13978be2e82b3b4"
SOURCE_BLOB_SHA1 = "9f75aec12a7e2f4e32f8abf98a7670087ba48cd7"
SOURCE_SIZE = 6743477
SOURCE_URL = (
    "https://raw.githubusercontent.com/MathiasValla/casdatasets-py/"
    + SOURCE_COMMIT
    + "/src/casdatasets/data/parquet/freclaimset2motor/claimset.parquet"
)
EXPECTED_ROWS = 1_012_839
EXPECTED_COLUMNS = [
    "ClaimID",
    "OccurYear",
    "ManagYear",
    "ClaimStatus",
    "PaidAmount",
    "RecourseAmount",
    "ExpectCharge",
    "ExpectRecourse",
]
CALIBRATION_YEARS = list(range(2004, 2009))
EVALUATION_YEARS = list(range(2009, 2014))
MIN_ORIGIN = 1995
DEV_BAND_CAP = 8
MIN_STRATUM_N = 50


def git_blob_sha1(data: bytes) -> str:
    header = f"blob {len(data)}\0".encode("ascii")
    return hashlib.sha1(header + data).hexdigest()


def normal_crps(mu: float, sigma: float, y: float) -> float:
    if not math.isfinite(sigma) or sigma <= 0:
        return abs(y - mu)
    z = (y - mu) / sigma
    phi = math.exp(-0.5 * z * z) / math.sqrt(2.0 * math.pi)
    Phi = 0.5 * (1.0 + math.erf(z / math.sqrt(2.0)))
    return sigma * (z * (2.0 * Phi - 1.0) + 2.0 * phi - 1.0 / math.sqrt(math.pi))


def chain_ladder_prediction(cum: pd.DataFrame, valuation_year: int) -> float:
    origins = [int(x) for x in cum.index if int(x) <= valuation_year]
    if len(origins) < 3:
        return float("nan")
    factors: dict[int, float] = {}
    max_dev = valuation_year - min(origins)
    for j in range(max_dev):
        eligible = [i for i in origins if i + j + 1 <= valuation_year and j + 1 in cum.columns]
        if not eligible:
            continue
        prev = cum.loc[eligible, j].astype(float)
        nxt = cum.loc[eligible, j + 1].astype(float)
        mask = prev.notna() & nxt.notna() & (prev != 0.0)
        denom = float(prev[mask].sum())
        if mask.sum() == 0 or denom == 0.0:
            continue
        factors[j] = float(nxt[mask].sum() / denom)

    pred = 0.0
    # Exclude the oldest origin: under the finite observed triangle it has no
    # estimable next development factor. The target uses the same origin set.
    for i in origins:
        if i <= MIN_ORIGIN:
            continue
        j = valuation_year - i
        f = factors.get(j)
        if f is None or j not in cum.columns:
            continue
        c = cum.loc[i, j]
        if pd.notna(c):
            pred += float(c) * (float(f) - 1.0)
    return pred


def state_prediction(df: pd.DataFrame, valuation_year: int) -> tuple[float, dict[str, int]]:
    # Fit only transitions whose next management-year endpoint is already
    # observed by the valuation date. This prevents future leakage.
    train = df[(df["ManagYear"] + 1 <= valuation_year) & df["has_consecutive_next"]].copy()
    train = train[(train["OccurYear"] > MIN_ORIGIN) & (train["OccurYear"] <= valuation_year)]
    train["dev_band"] = np.minimum(train["dev_age"].to_numpy(), DEV_BAND_CAP)

    by_state_dev = (
        train.groupby(["status_norm", "dev_band"], observed=True)["next_increment"]
        .agg(["mean", "count"])
    )
    by_dev = train.groupby("dev_band", observed=True)["next_increment"].mean()
    global_mean = float(train["next_increment"].mean()) if len(train) else 0.0

    current = df[
        (df["ManagYear"] == valuation_year)
        & (df["OccurYear"] > MIN_ORIGIN)
        & (df["OccurYear"] <= valuation_year)
    ].copy()
    current["dev_band"] = np.minimum(current["dev_age"].to_numpy(), DEV_BAND_CAP)

    pred = 0.0
    exact = 0
    fallback_dev = 0
    fallback_global = 0
    for row in current[["status_norm", "dev_band"]].itertuples(index=False):
        key = (row.status_norm, int(row.dev_band))
        if key in by_state_dev.index and int(by_state_dev.loc[key, "count"]) >= MIN_STRATUM_N:
            m = float(by_state_dev.loc[key, "mean"])
            exact += 1
        elif int(row.dev_band) in by_dev.index:
            m = float(by_dev.loc[int(row.dev_band)])
            fallback_dev += 1
        else:
            m = global_mean
            fallback_global += 1
        pred += m
    return pred, {
        "current_rows": int(len(current)),
        "exact_stratum": exact,
        "fallback_dev": fallback_dev,
        "fallback_global": fallback_global,
    }


def summarize(rows: list[dict], years: list[int], model: str, sigma: float) -> dict:
    chosen = [r for r in rows if r["valuation_year"] in years]
    errors = np.array([r[f"{model}_prediction"] - r["actual"] for r in chosen], dtype=float)
    crps = [normal_crps(r[f"{model}_prediction"], sigma, r["actual"]) for r in chosen]
    return {
        "n_years": len(chosen),
        "mae": float(np.mean(np.abs(errors))),
        "rmse": float(np.sqrt(np.mean(errors * errors))),
        "bias": float(np.mean(errors)),
        "fixed_calibration_sd": float(sigma),
        "mean_crps": float(np.mean(crps)),
    }


def main() -> None:
    path = Path("/tmp/freclaimset2motor-claimset.parquet")
    urllib.request.urlretrieve(SOURCE_URL, path)
    data = path.read_bytes()
    if len(data) != SOURCE_SIZE:
        raise SystemExit(f"unexpected byte size: {len(data)} != {SOURCE_SIZE}")
    blob_sha = git_blob_sha1(data)
    if blob_sha != SOURCE_BLOB_SHA1:
        raise SystemExit(f"git blob sha1 mismatch: {blob_sha}")
    raw_sha256 = hashlib.sha256(data).hexdigest()

    df = pd.read_parquet(path)
    if len(df) != EXPECTED_ROWS:
        raise SystemExit(f"unexpected row count: {len(df)}")
    if list(df.columns) != EXPECTED_COLUMNS:
        raise SystemExit(f"unexpected columns: {list(df.columns)}")

    for col in ["OccurYear", "ManagYear"]:
        df[col] = df[col].astype(int)
    for col in ["PaidAmount", "RecourseAmount", "ExpectCharge", "ExpectRecourse"]:
        df[col] = pd.to_numeric(df[col], errors="raise").astype(float)
    df["status_norm"] = df["ClaimStatus"].astype(str).str.strip().str.lower()
    df = df.sort_values(["ClaimID", "ManagYear"], kind="mergesort").reset_index(drop=True)
    df["dev_age"] = df["ManagYear"] - df["OccurYear"]

    g = df.groupby("ClaimID", sort=False)
    prev_paid = g["PaidAmount"].shift(1)
    prev_year = g["ManagYear"].shift(1)
    next_paid = g["PaidAmount"].shift(-1)
    next_year = g["ManagYear"].shift(-1)
    df["row_increment"] = df["PaidAmount"] - prev_paid.fillna(0.0)
    df["gap_from_prev"] = df["ManagYear"] - prev_year
    df["has_consecutive_next"] = next_year.eq(df["ManagYear"] + 1)
    df["next_increment"] = next_paid - df["PaidAmount"]

    # Aggregate incremental observations into a paid triangle. Any gap is
    # explicitly audited below; the row_increment is recorded at its observed
    # management year rather than inventing unobserved intra-gap timing.
    inc = (
        df.groupby(["OccurYear", "dev_age"], observed=True)["row_increment"]
        .sum()
        .unstack("dev_age")
        .sort_index()
        .sort_index(axis=1)
    )
    all_devs = list(range(int(inc.columns.max()) + 1))
    inc = inc.reindex(columns=all_devs, fill_value=0.0)
    cum = inc.cumsum(axis=1)

    years = CALIBRATION_YEARS + EVALUATION_YEARS
    rows: list[dict] = []
    for y in years:
        cl = chain_ladder_prediction(cum, y)
        state, coverage = state_prediction(df, y)
        actual = float(
            df.loc[
                (df["ManagYear"] == y + 1)
                & (df["OccurYear"] > MIN_ORIGIN)
                & (df["OccurYear"] <= y),
                "row_increment",
            ].sum()
        )
        rows.append(
            {
                "valuation_year": y,
                "target_management_year": y + 1,
                "actual": actual,
                "chain_ladder_prediction": float(cl),
                "state_dev_prediction": float(state),
                "chain_ladder_error": float(cl - actual),
                "state_dev_error": float(state - actual),
                "state_coverage": coverage,
            }
        )

    calib = [r for r in rows if r["valuation_year"] in CALIBRATION_YEARS]
    cl_calib_errors = np.array([r["chain_ladder_error"] for r in calib], dtype=float)
    st_calib_errors = np.array([r["state_dev_error"] for r in calib], dtype=float)
    cl_sd = float(np.std(cl_calib_errors, ddof=1))
    st_sd = float(np.std(st_calib_errors, ddof=1))

    cl_summary = summarize(rows, EVALUATION_YEARS, "chain_ladder", cl_sd)
    st_summary = summarize(rows, EVALUATION_YEARS, "state_dev", st_sd)

    gaps = df.loc[df["gap_from_prev"].notna() & (df["gap_from_prev"] != 1)]
    negative = df[df["row_increment"] < 0]
    first_rows = g.cumcount().eq(0)
    first_year_mismatch = df.loc[first_rows & (df["ManagYear"] != df["OccurYear"])]

    result = {
        "verdict_basis": "real_data_rolling_annual_same_observation_gate",
        "source": {
            "repository": "MathiasValla/casdatasets-py",
            "commit": SOURCE_COMMIT,
            "path": "src/casdatasets/data/parquet/freclaimset2motor/claimset.parquet",
            "git_blob_sha1_expected": SOURCE_BLOB_SHA1,
            "git_blob_sha1_observed": blob_sha,
            "raw_sha256": raw_sha256,
            "bytes": len(data),
        },
        "runtime": {
            "python": sys.version.split()[0],
            "platform": platform.platform(),
            "pandas": pd.__version__,
            "numpy": np.__version__,
        },
        "data_audit": {
            "rows": int(len(df)),
            "unique_claims": int(df["ClaimID"].nunique()),
            "min_occurrence_year": int(df["OccurYear"].min()),
            "max_occurrence_year": int(df["OccurYear"].max()),
            "min_management_year": int(df["ManagYear"].min()),
            "max_management_year": int(df["ManagYear"].max()),
            "statuses": {str(k): int(v) for k, v in df["status_norm"].value_counts().to_dict().items()},
            "nonconsecutive_followup_rows": int(len(gaps)),
            "first_row_not_occurrence_year": int(len(first_year_mismatch)),
            "negative_annual_adjustment_rows": int(len(negative)),
            "negative_annual_adjustment_share": float(len(negative) / len(df)),
        },
        "protocol": {
            "consumer": "existing-claim one-year aggregate paid movement at annual valuation resolution",
            "same_target_origin_rule": "OccurYear > 1995 and OccurYear <= valuation year",
            "aggregate_baseline": "volume-weighted paid Chain Ladder next diagonal",
            "individual_challenger": "nonparametric annual mean next-paid transition by observed ClaimStatus and development-age band; dev band capped at 8; minimum stratum n=50; development/global fallback",
            "training_rule": "challenger uses only exact consecutive annual transitions with next endpoint <= valuation year",
            "calibration_years": CALIBRATION_YEARS,
            "evaluation_years": EVALUATION_YEARS,
            "uncertainty": "fixed Normal aggregate predictive scale calibrated only from 2004-2008 rolling aggregate errors; no claim cross-dependence or parameter uncertainty",
            "unsupported_consumers": ["monthly cash timing", "daily liquidity", "payment count", "per-payment reinsurance"],
        },
        "rolling_rows": rows,
        "evaluation": {
            "chain_ladder": cl_summary,
            "state_dev": st_summary,
            "state_vs_chain_ladder_mae_ratio": float(st_summary["mae"] / cl_summary["mae"]),
            "state_vs_chain_ladder_rmse_ratio": float(st_summary["rmse"] / cl_summary["rmse"]),
            "state_vs_chain_ladder_crps_ratio": float(st_summary["mean_crps"] / cl_summary["mean_crps"]),
        },
        "limitations": [
            "Only five final annual evaluation transitions are available under the fixed split.",
            "The individual challenger is deliberately simple and does not represent the full multi-state/nonlinear literature.",
            "Normal aggregate predictive scales are calibration devices, not a promoted reserving distribution.",
            "Annual management-year data cannot validate intra-year timing, payment counts, monthly liquidity, or transaction-level treaty response.",
            "Observed management-year gaps, if any, are not imputed into unobserved years.",
        ],
    }
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
