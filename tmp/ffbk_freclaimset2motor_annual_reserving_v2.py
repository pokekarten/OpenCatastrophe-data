# Temporary public-data execution probe for FFBK/NextGen research only.
# This file is intentionally outside the OpenCatastrophe-data product surface.
from __future__ import annotations

import hashlib
import json
import math
import platform
import subprocess
import sys
import urllib.request
from pathlib import Path

import numpy as np
import pandas as pd

PARQUET_REPO = "MathiasValla/casdatasets-py"
PARQUET_COMMIT = "10af669a599c1d4d69288f62f13978be2e82b3b4"
PARQUET_PATH = "src/casdatasets/data/parquet/freclaimset2motor/claimset.parquet"
PARQUET_BLOB_SHA1 = "9f75aec12a7e2f4e32f8abf98a7670087ba48cd7"
PARQUET_SIZE = 6743477
PARQUET_URL = f"https://raw.githubusercontent.com/{PARQUET_REPO}/{PARQUET_COMMIT}/{PARQUET_PATH}"

RDATA_REPO = "dutangc/CASdatasets"
RDATA_COMMIT = "227fb56b8734bdb7c0327a41180e01d2ddaeaf26"
RDATA_PATH = "data/freclaimset2motor.rda"
RDATA_BLOB_SHA1 = "a232d3a63f0ecc7bd28e45ce8364afb660f2eb4f"
RDATA_SIZE = 9482793
RDATA_URL = f"https://raw.githubusercontent.com/{RDATA_REPO}/{RDATA_COMMIT}/{RDATA_PATH}"

EXPECTED_ROWS = 1_012_839
EXPECTED_COLUMNS = [
    "ClaimID", "OccurYear", "ManagYear", "ClaimStatus", "PaidAmount",
    "RecourseAmount", "ExpectCharge", "ExpectRecourse",
]
CALIBRATION_YEARS = list(range(2004, 2009))
EVALUATION_YEARS = list(range(2009, 2014))
DEV_BAND_CAP = 8
MIN_STRATUM_N = 50
EPS = 1e-12


def git_blob_sha1(data: bytes) -> str:
    return hashlib.sha1(f"blob {len(data)}\0".encode("ascii") + data).hexdigest()


def fetch_checked(url: str, path: Path, size: int, blob_sha1: str) -> dict:
    urllib.request.urlretrieve(url, path)
    data = path.read_bytes()
    observed_blob = git_blob_sha1(data)
    if len(data) != size:
        raise SystemExit(f"unexpected byte size for {path.name}: {len(data)} != {size}")
    if observed_blob != blob_sha1:
        raise SystemExit(f"git blob sha1 mismatch for {path.name}: {observed_blob} != {blob_sha1}")
    return {
        "bytes": len(data),
        "git_blob_sha1_expected": blob_sha1,
        "git_blob_sha1_observed": observed_blob,
        "raw_sha256": hashlib.sha256(data).hexdigest(),
    }


def normal_crps(mu: float, sigma: float, y: float) -> float:
    if not math.isfinite(sigma) or sigma <= 0:
        return abs(y - mu)
    z = (y - mu) / sigma
    phi = math.exp(-0.5 * z * z) / math.sqrt(2.0 * math.pi)
    Phi = 0.5 * (1.0 + math.erf(z / math.sqrt(2.0)))
    return sigma * (z * (2.0 * Phi - 1.0) + 2.0 * phi - 1.0 / math.sqrt(math.pi))


def canonical_audit(rdata_path: Path) -> dict:
    claims_csv = Path("/tmp/freclaimset2motor-canonical-claimset.csv")
    aggregate_csv = Path("/tmp/freclaimset2motor-canonical-aggdata.csv")
    r_code = r'''
args <- commandArgs(trailingOnly = TRUE)
source_rda <- args[[1L]]
claims_csv <- args[[2L]]
aggregate_csv <- args[[3L]]
env <- new.env(parent = baseenv())
loaded <- load(source_rda, envir = env)
required <- c("claimset", "aggdata")
if (!all(required %in% loaded)) {
  stop(sprintf("source .rda missing required objects: %s", paste(setdiff(required, loaded), collapse = ",")))
}
claimset <- get("claimset", envir = env, inherits = FALSE)
aggdata <- get("aggdata", envir = env, inherits = FALSE)
if (!is.data.frame(claimset) || !is.data.frame(aggdata)) {
  stop("claimset and aggdata must both be data.frames")
}
write.table(claimset, file = claims_csv, sep = ",", row.names = FALSE, col.names = TRUE,
            quote = TRUE, na = "NA", qmethod = "double", eol = "\n", fileEncoding = "UTF-8")
write.table(aggdata, file = aggregate_csv, sep = ",", row.names = FALSE, col.names = TRUE,
            quote = TRUE, na = "NA", qmethod = "double", eol = "\n", fileEncoding = "UTF-8")
cat(sprintf("loaded=%s claim_rows=%d agg_rows=%d\n", paste(sort(loaded), collapse = ","), nrow(claimset), nrow(aggdata)))
'''
    completed = subprocess.run(
        ["Rscript", "--vanilla", "-e", r_code, str(rdata_path), str(claims_csv), str(aggregate_csv)],
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0:
        raise SystemExit(f"canonical RData materialization failed: {completed.stderr.strip()}")
    if not claims_csv.is_file() or not aggregate_csv.is_file():
        raise SystemExit("canonical RData materialization did not produce both CSV transports")

    columns = list(pd.read_csv(claims_csv, nrows=0).columns)
    rdf = pd.read_csv(claims_csv, usecols=["ClaimID", "OccurYear", "ManagYear"], low_memory=False)
    agg_rows = sum(1 for _ in open(aggregate_csv, "r", encoding="utf-8")) - 1
    return {
        "objects_required": ["claimset", "aggdata"],
        "materializer": "base_R_load_isolated_environment",
        "materializer_stdout": completed.stdout.strip(),
        "rows": int(len(rdf)),
        "aggregate_rows": int(agg_rows),
        "columns": [str(x) for x in columns],
        "unique_claim_ids": int(rdf["ClaimID"].nunique(dropna=True)),
        "rows_management_equals_occurrence": int((pd.to_numeric(rdf["ManagYear"], errors="coerce") == pd.to_numeric(rdf["OccurYear"], errors="coerce")).sum()),
        "claims_csv_sha256": hashlib.sha256(claims_csv.read_bytes()).hexdigest(),
        "aggregate_csv_sha256": hashlib.sha256(aggregate_csv.read_bytes()).hexdigest(),
    }


def prepare_parquet(path: Path) -> tuple[pd.DataFrame, dict]:
    df = pd.read_parquet(path)
    if len(df) != EXPECTED_ROWS:
        raise SystemExit(f"unexpected Parquet row count: {len(df)}")
    if list(df.columns) != EXPECTED_COLUMNS:
        raise SystemExit(f"unexpected Parquet columns: {list(df.columns)}")

    for col in ["OccurYear", "ManagYear"]:
        df[col] = pd.to_numeric(df[col], errors="raise").astype(int)
    for col in ["PaidAmount", "RecourseAmount", "ExpectCharge", "ExpectRecourse"]:
        df[col] = pd.to_numeric(df[col], errors="raise").astype(float)
    df["status_norm"] = df["ClaimStatus"].astype(str).str.strip().str.lower()

    duplicate_claim_year_rows = int(df.duplicated(["ClaimID", "ManagYear"], keep=False).sum())
    occurrence_cardinality = df.groupby("ClaimID", sort=False)["OccurYear"].nunique(dropna=False)
    inconsistent_occurrence_claims = int((occurrence_cardinality != 1).sum())
    negative_development_rows = int((df["ManagYear"] < df["OccurYear"]).sum())
    claims_with_occurrence_year_row = int(
        df.loc[df["ManagYear"] == df["OccurYear"], "ClaimID"].nunique()
    )
    all_claims = int(df["ClaimID"].nunique())
    claims_without_occurrence_year_row = all_claims - claims_with_occurrence_year_row

    first = (
        df.sort_values(["ClaimID", "ManagYear"], kind="mergesort")
        .groupby("ClaimID", sort=False)
        .first()[["OccurYear", "ManagYear"]]
    )
    first_delay = first["ManagYear"] - first["OccurYear"]

    df = df.sort_values(["ClaimID", "ManagYear"], kind="mergesort").reset_index(drop=True)
    df["dev_age"] = df["ManagYear"] - df["OccurYear"]
    valid = df[df["dev_age"] >= 0].copy()
    valid["dev_band"] = np.minimum(valid["dev_age"].to_numpy(), DEV_BAND_CAP)

    g = valid.groupby("ClaimID", sort=False)
    next_year = g["ManagYear"].shift(-1)
    next_paid = g["PaidAmount"].shift(-1)
    valid["has_exact_next_year"] = next_year.eq(valid["ManagYear"] + 1)
    valid["one_year_increment"] = np.where(
        valid["has_exact_next_year"], next_paid - valid["PaidAmount"], 0.0
    ).astype(float)

    prev_year = g["ManagYear"].shift(1)
    valid["gap_from_prev"] = valid["ManagYear"] - prev_year
    nonconsecutive_followup_rows = int(
        (valid["gap_from_prev"].notna() & (valid["gap_from_prev"] != 1)).sum()
    )
    negative_one_year_rows = int((valid["one_year_increment"] < 0).sum())

    delay_counts = first_delay.value_counts().sort_index()
    audit = {
        "rows": int(len(df)),
        "valid_nonnegative_development_rows": int(len(valid)),
        "unique_claim_ids": all_claims,
        "claims_with_occurrence_year_row": claims_with_occurrence_year_row,
        "claims_without_occurrence_year_row": claims_without_occurrence_year_row,
        "first_report_delay_years": {str(int(k)): int(v) for k, v in delay_counts.items()},
        "duplicate_claim_management_year_rows": duplicate_claim_year_rows,
        "claims_with_inconsistent_occurrence_year": inconsistent_occurrence_claims,
        "negative_development_rows": negative_development_rows,
        "nonconsecutive_followup_rows": nonconsecutive_followup_rows,
        "negative_one_year_increment_rows": negative_one_year_rows,
        "negative_one_year_increment_share": float(negative_one_year_rows / len(valid)),
        "statuses": {str(k): int(v) for k, v in valid["status_norm"].value_counts().to_dict().items()},
        "min_occurrence_year": int(df["OccurYear"].min()),
        "max_occurrence_year": int(df["OccurYear"].max()),
        "min_management_year": int(df["ManagYear"].min()),
        "max_management_year": int(df["ManagYear"].max()),
    }
    return valid, audit


def fit_predict(train: pd.DataFrame, current: pd.DataFrame) -> tuple[dict[str, float], dict]:
    global_mean = float(train["one_year_increment"].mean()) if len(train) else 0.0

    dev_stats = train.groupby("dev_band", observed=True).agg(
        mean_increment=("one_year_increment", "mean"),
        sum_increment=("one_year_increment", "sum"),
        sum_paid=("PaidAmount", "sum"),
        n=("one_year_increment", "size"),
    )
    status_dev = (
        train.groupby(["status_norm", "dev_band"], observed=True)["one_year_increment"]
        .agg(["mean", "count"])
    )

    total_paid = float(train["PaidAmount"].sum())
    global_factor = 1.0 + (float(train["one_year_increment"].sum()) / total_paid if abs(total_paid) > EPS else 0.0)

    paid_factor_pred = 0.0
    dev_mean_pred = 0.0
    status_dev_pred = 0.0
    coverage = {"status_dev_exact": 0, "status_dev_fallback_dev": 0, "status_dev_fallback_global": 0, "paid_factor_dev": 0, "paid_factor_global": 0}

    for row in current[["status_norm", "dev_band", "PaidAmount"]].itertuples(index=False):
        d = int(row.dev_band)
        paid = float(row.PaidAmount)

        if d in dev_stats.index and abs(float(dev_stats.loc[d, "sum_paid"])) > EPS:
            factor = 1.0 + float(dev_stats.loc[d, "sum_increment"]) / float(dev_stats.loc[d, "sum_paid"])
            coverage["paid_factor_dev"] += 1
        else:
            factor = global_factor
            coverage["paid_factor_global"] += 1
        paid_factor_pred += paid * (factor - 1.0)

        if d in dev_stats.index:
            dev_mean = float(dev_stats.loc[d, "mean_increment"])
        else:
            dev_mean = global_mean
        dev_mean_pred += dev_mean

        key = (row.status_norm, d)
        if key in status_dev.index and int(status_dev.loc[key, "count"]) >= MIN_STRATUM_N:
            m = float(status_dev.loc[key, "mean"])
            coverage["status_dev_exact"] += 1
        elif d in dev_stats.index:
            m = float(dev_stats.loc[d, "mean_increment"])
            coverage["status_dev_fallback_dev"] += 1
        else:
            m = global_mean
            coverage["status_dev_fallback_global"] += 1
        status_dev_pred += m

    return {
        "aggregate_paid_factor_prediction": float(paid_factor_pred),
        "aggregate_dev_mean_prediction": float(dev_mean_pred),
        "individual_status_dev_mean_prediction": float(status_dev_pred),
    }, coverage


def summarize(rows: list[dict], years: list[int], model: str, sigma: float) -> dict:
    selected = [r for r in rows if r["valuation_year"] in years]
    pred_key = f"{model}_prediction"
    errs = np.asarray([r[pred_key] - r["actual_reported_cohort_increment"] for r in selected], dtype=float)
    crps = [normal_crps(r[pred_key], sigma, r["actual_reported_cohort_increment"]) for r in selected]
    return {
        "n_years": len(selected),
        "mae": float(np.mean(np.abs(errs))),
        "rmse": float(np.sqrt(np.mean(errs * errs))),
        "bias": float(np.mean(errs)),
        "fixed_calibration_error_sd": float(sigma),
        "mean_crps": float(np.mean(crps)),
    }


def main() -> None:
    parquet_file = Path("/tmp/freclaimset2motor-claimset.parquet")
    rdata_file = Path("/tmp/freclaimset2motor.rda")
    parquet_identity = fetch_checked(PARQUET_URL, parquet_file, PARQUET_SIZE, PARQUET_BLOB_SHA1)
    rdata_identity = fetch_checked(RDATA_URL, rdata_file, RDATA_SIZE, RDATA_BLOB_SHA1)

    canonical = canonical_audit(rdata_file)
    df, audit = prepare_parquet(parquet_file)

    years = CALIBRATION_YEARS + EVALUATION_YEARS
    rows: list[dict] = []
    for valuation_year in years:
        # Training endpoints are fully visible by valuation_year. This makes
        # zero next-year movement observable without conditioning on later continuation.
        train = df[df["ManagYear"] + 1 <= valuation_year].copy()
        current = df[df["ManagYear"] == valuation_year].copy()
        predictions, coverage = fit_predict(train, current)
        actual = float(current["one_year_increment"].sum())
        exact_next = int(current["has_exact_next_year"].sum())
        row = {
            "valuation_year": valuation_year,
            "target_management_year": valuation_year + 1,
            "current_reported_claim_rows": int(len(current)),
            "current_claims_with_exact_next_year_row": exact_next,
            "current_claims_without_exact_next_year_row": int(len(current) - exact_next),
            "actual_reported_cohort_increment": actual,
            **predictions,
            "coverage": coverage,
        }
        for model in ["aggregate_paid_factor", "aggregate_dev_mean", "individual_status_dev_mean"]:
            row[f"{model}_error"] = float(row[f"{model}_prediction"] - actual)
        rows.append(row)

    calibration = [r for r in rows if r["valuation_year"] in CALIBRATION_YEARS]
    sigmas: dict[str, float] = {}
    for model in ["aggregate_paid_factor", "aggregate_dev_mean", "individual_status_dev_mean"]:
        errs = np.asarray([r[f"{model}_error"] for r in calibration], dtype=float)
        sigmas[model] = float(np.std(errs, ddof=1))

    evaluation = {
        model: summarize(rows, EVALUATION_YEARS, model, sigmas[model])
        for model in ["aggregate_paid_factor", "aggregate_dev_mean", "individual_status_dev_mean"]
    }
    best_aggregate = min(["aggregate_paid_factor", "aggregate_dev_mean"], key=lambda m: evaluation[m]["mae"])
    status = evaluation["individual_status_dev_mean"]
    agg = evaluation[best_aggregate]

    result = {
        "verdict_basis": "corrected_real_data_rolling_annual_same_reported_claim_cohort_gate",
        "source": {
            "parquet": {"repository": PARQUET_REPO, "commit": PARQUET_COMMIT, "path": PARQUET_PATH, **parquet_identity},
            "canonical_rdata": {"repository": RDATA_REPO, "commit": RDATA_COMMIT, "path": RDATA_PATH, **rdata_identity},
        },
        "runtime": {
            "python": sys.version.split()[0],
            "platform": platform.platform(),
            "pandas": pd.__version__,
            "numpy": np.__version__,
            "canonical_materializer": "Rscript/base-R load",
        },
        "canonical_rdata_audit": canonical,
        "parquet_audit": audit,
        "provenance_comparison": {
            "same_row_count": bool(canonical.get("rows") == audit["rows"]),
            "same_unique_claim_count": bool(canonical.get("unique_claim_ids") == audit["unique_claim_ids"]) if "unique_claim_ids" in canonical else None,
            "official_documented_claim_count": 735079,
            "parquet_unique_claim_ids": audit["unique_claim_ids"],
            "claims_with_occurrence_year_row": audit["claims_with_occurrence_year_row"],
            "note": "The official package documentation's 735,079 ClaimNb total is compared to exact source cardinalities; no semantic equivalence is assumed from labels alone.",
        },
        "protocol": {
            "consumer": "one-year aggregate paid movement of the claim cohort already reported/observed at the annual valuation date",
            "target": "for each claim row at valuation year t, PaidAmount(t+1)-PaidAmount(t) if an exact t+1 row exists, else zero; summed over the t cohort",
            "training_rule": "only rows whose one-year endpoint t+1 is at or before the valuation year; missing exact t+1 is a zero observed one-year movement, not a dropped transition",
            "aggregate_paid_factor": "development-band aggregate paid age-to-age factor applied to current cumulative paid; fallback global factor",
            "aggregate_dev_mean": "development-band mean one-year increment per observed claim applied to current claim count; no status/identity in prediction",
            "individual_status_dev_mean": "status x development-band mean one-year increment; minimum stratum n=50; development/global fallback",
            "development_band_cap": DEV_BAND_CAP,
            "minimum_status_development_stratum_n": MIN_STRATUM_N,
            "calibration_years": CALIBRATION_YEARS,
            "evaluation_years": EVALUATION_YEARS,
            "uncertainty": "fixed Normal aggregate predictive scale from calibration-period aggregate errors only; diagnostic proper score, not a promoted predictive distribution",
            "v1_disposition": "DISCARDED_PROTOCOL_INVALID: total next-year observed movement included newly/late-reported claims absent from the individual prediction cohort, and transition fitting conditioned on exact continuation",
            "unsupported_consumers": ["IBNR/new-report emergence", "total outstanding reserve", "monthly or daily cash timing", "payment count", "transaction-level or per-payment reinsurance", "liquidity timing"],
        },
        "rolling_rows": rows,
        "evaluation": evaluation,
        "comparison": {
            "best_aggregate_by_holdout_mae": best_aggregate,
            "status_vs_best_aggregate_mae_ratio": float(status["mae"] / agg["mae"]),
            "status_vs_best_aggregate_rmse_ratio": float(status["rmse"] / agg["rmse"]),
            "status_vs_best_aggregate_crps_ratio": float(status["mean_crps"] / agg["mean_crps"]),
            "status_holdout_years_lower_absolute_error_than_best_aggregate": int(sum(
                abs(r["individual_status_dev_mean_error"]) < abs(r[f"{best_aggregate}_error"])
                for r in rows if r["valuation_year"] in EVALUATION_YEARS
            )),
        },
        "limitations": [
            "Only five untouched annual evaluation transitions (valuation years 2009-2013) are available under the frozen split.",
            "The individual challenger is deliberately simple and does not represent full recurrent-event, Aalen-Johansen, neural, or Bayesian individual-reserving families.",
            "The reported-claim cohort target deliberately excludes newly reported/IBNR claims, so this is not a total reserve adequacy test.",
            "Annual management-year snapshots cannot validate intra-year payment timing, payment count, monthly/daily liquidity, or transaction-level treaty response.",
            "A missing exact t+1 row is treated as zero observed one-year movement; later reopening after a gap is outside that annual endpoint and is separately audited.",
            "Normal error scales are fixed calibration devices for CRPS comparability, not promoted reserving distributions.",
            "No final model-family promotion is warranted from one dataset and five holdout years.",
        ],
    }
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
