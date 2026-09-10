# Temporary public-data execution probe for FFBK/NextGen research only.
# This file is intentionally outside the OpenCatastrophe-data product surface and
# must not be merged. It tests only a bounded claim-level paid-loss transform.
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
SOURCE_SHA256 = "a00ca7ecb1a3323e2a242a462d4ce0503624a140f16e7f1a55e1303f95db4596"
SOURCE_SIZE = 6_743_477
SOURCE_PATH = "src/casdatasets/data/parquet/freclaimset2motor/claimset.parquet"
SOURCE_URL = (
    "https://raw.githubusercontent.com/MathiasValla/casdatasets-py/"
    + SOURCE_COMMIT
    + "/"
    + SOURCE_PATH
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
CLOSED_STATUSES = {"fully closed", "closed without further action"}
CALIBRATION_OCCURRENCE_YEARS = tuple(range(1995, 2005))
EVALUATION_OCCURRENCE_YEARS = tuple(range(2005, 2010))
CANONICAL_RDATA_SHA256 = "4409adb022d18e24a3a0e724523706616e707c53e55f8625ce9fc122a20185d6"
CANONICAL_EQUIVALENCE_EVIDENCE = "pokekarten/FFBK#1543"


def git_blob_sha1(data: bytes) -> str:
    return hashlib.sha1(f"blob {len(data)}\0".encode("ascii") + data).hexdigest()


def nearest_rank(values: np.ndarray, numerator: int, denominator: int) -> float:
    if values.ndim != 1 or len(values) == 0:
        raise ValueError("nearest-rank input must be a non-empty vector")
    if not 0 < numerator < denominator:
        raise ValueError("nearest-rank probability invalid")
    ordered = np.sort(values, kind="mergesort")
    rank = math.ceil(len(ordered) * numerator / denominator)
    return float(ordered[rank - 1])


def status_norm(series: pd.Series) -> pd.Series:
    return series.astype(str).str.strip().str.lower()


def finite_numeric(series: pd.Series, field: str) -> pd.Series:
    converted = pd.to_numeric(series, errors="raise").astype(float)
    finite = np.isfinite(converted.to_numpy())
    if not bool(finite.all()):
        raise RuntimeError(f"non-finite values in {field}")
    return converted


def terminal_observations(frame: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, int]]:
    """Return unambiguous last-observed claim states without inventing a tie order.

    A claim may have multiple rows at its maximum management year. Such a claim is
    admitted only when all relevant terminal-state fields are exactly identical
    across those rows. Conflicting same-year terminal states are excluded and
    counted rather than resolved by physical row order.
    """

    max_year = frame.groupby("ClaimID", sort=False)["ManagYear"].transform("max")
    terminal = frame.loc[frame["ManagYear"].eq(max_year)].copy()
    state_columns = [
        "OccurYear",
        "ManagYear",
        "ClaimStatus",
        "PaidAmount",
        "RecourseAmount",
        "ExpectCharge",
        "ExpectRecourse",
    ]

    group_sizes = terminal.groupby("ClaimID", sort=False).size()
    duplicate_ids = group_sizes[group_sizes > 1].index
    duplicate_terminal = terminal[terminal["ClaimID"].isin(duplicate_ids)]

    ambiguous: set[str] = set()
    identical_duplicate_claims = 0
    for claim_id, group in duplicate_terminal.groupby("ClaimID", sort=False):
        reference = group.iloc[0][state_columns]
        if all(bool(group[column].eq(reference[column]).all()) for column in state_columns):
            identical_duplicate_claims += 1
        else:
            ambiguous.add(str(claim_id))

    terminal = terminal[~terminal["ClaimID"].astype(str).isin(ambiguous)]
    terminal = terminal.drop_duplicates(subset=["ClaimID"], keep="first").copy()
    if terminal["ClaimID"].duplicated().any():
        raise RuntimeError("terminal claim identity is not unique after tie gate")

    diagnostics = {
        "claims_with_multiple_rows_at_terminal_management_year": int(len(duplicate_ids)),
        "terminal_duplicate_claims_identical_on_consumer_state": int(identical_duplicate_claims),
        "terminal_duplicate_claims_conflicting_and_excluded": int(len(ambiguous)),
        "terminal_claim_rows_after_tie_gate": int(len(terminal)),
    }
    return terminal, diagnostics


def cohort_summary(frame: pd.DataFrame, attachment: float, limit: float) -> dict[str, object]:
    loss = frame["PaidAmount"].to_numpy(dtype=float)
    ceded = np.minimum(np.maximum(loss - attachment, 0.0), limit)
    net = loss - ceded
    if np.any(ceded < -1e-9) or np.any(net < -1e-9):
        raise RuntimeError("loss transform produced negative ceded/net amount")
    if not np.allclose(loss, ceded + net, rtol=0.0, atol=1e-9):
        raise RuntimeError("gross/ceded/net transform does not reconcile")

    gross_total = float(loss.sum())
    ceded_total = float(ceded.sum())
    net_total = float(net.sum())
    return {
        "claim_count": int(len(frame)),
        "positive_paid_claim_count": int((loss > 0).sum()),
        "claims_with_positive_cession": int((ceded > 0).sum()),
        "gross_observed_paid_eur": gross_total,
        "ceded_layer_eur": ceded_total,
        "net_observed_paid_eur": net_total,
        "gross_ceded_net_residual_eur": float(gross_total - ceded_total - net_total),
        "ceded_share_of_gross_paid": (ceded_total / gross_total if gross_total > 0 else None),
        "technical_break_even_premium_eur": ceded_total,
        "meaning_of_break_even": (
            "Premium at which gross observed paid minus layer cession plus premium equals "
            "gross observed paid for this cohort; excludes commission, default, expenses, "
            "timing, capital and all market pricing effects."
        ),
    }


def main() -> None:
    path = Path("/tmp/freclaimset2motor-claim-loss-transform.parquet")
    urllib.request.urlretrieve(SOURCE_URL, path)
    data = path.read_bytes()
    if len(data) != SOURCE_SIZE:
        raise SystemExit(f"unexpected byte size: {len(data)} != {SOURCE_SIZE}")
    observed_blob = git_blob_sha1(data)
    if observed_blob != SOURCE_BLOB_SHA1:
        raise SystemExit(f"git blob mismatch: {observed_blob} != {SOURCE_BLOB_SHA1}")
    observed_sha = hashlib.sha256(data).hexdigest()
    if observed_sha != SOURCE_SHA256:
        raise SystemExit(f"sha256 mismatch: {observed_sha} != {SOURCE_SHA256}")

    df = pd.read_parquet(path)
    if len(df) != EXPECTED_ROWS:
        raise SystemExit(f"unexpected row count: {len(df)} != {EXPECTED_ROWS}")
    if list(df.columns) != EXPECTED_COLUMNS:
        raise SystemExit(f"unexpected columns: {list(df.columns)!r}")

    df["ClaimID"] = df["ClaimID"].astype(str)
    df["OccurYear"] = pd.to_numeric(df["OccurYear"], errors="raise").astype(int)
    df["ManagYear"] = pd.to_numeric(df["ManagYear"], errors="raise").astype(int)
    for field in ("PaidAmount", "RecourseAmount", "ExpectCharge", "ExpectRecourse"):
        df[field] = finite_numeric(df[field], field)
    df["status_norm"] = status_norm(df["ClaimStatus"])

    terminal, tie_diagnostics = terminal_observations(df)
    terminal["is_closed_status"] = terminal["status_norm"].isin(CLOSED_STATUSES)
    terminal["paid_nonnegative"] = terminal["PaidAmount"].ge(0.0)

    bounded = terminal[
        terminal["is_closed_status"]
        & terminal["paid_nonnegative"]
        & terminal["OccurYear"].isin(
            CALIBRATION_OCCURRENCE_YEARS + EVALUATION_OCCURRENCE_YEARS
        )
    ].copy()

    calibration = bounded[bounded["OccurYear"].isin(CALIBRATION_OCCURRENCE_YEARS)].copy()
    evaluation = bounded[bounded["OccurYear"].isin(EVALUATION_OCCURRENCE_YEARS)].copy()
    positive_calibration = calibration.loc[calibration["PaidAmount"].gt(0), "PaidAmount"].to_numpy(
        dtype=float
    )
    if len(positive_calibration) < 100:
        raise RuntimeError("insufficient positive calibration claims for frozen layer")

    attachment = nearest_rank(positive_calibration, 90, 100)
    exhaustion = nearest_rank(positive_calibration, 99, 100)
    limit = exhaustion - attachment
    if not math.isfinite(attachment) or not math.isfinite(exhaustion) or limit <= 0:
        raise RuntimeError("invalid train-only q90/q99 layer")

    evaluation_by_year = {
        str(year): cohort_summary(
            evaluation[evaluation["OccurYear"].eq(year)], attachment, limit
        )
        for year in EVALUATION_OCCURRENCE_YEARS
    }
    all_evaluation = cohort_summary(evaluation, attachment, limit)

    terminal_negative_paid = int(terminal["PaidAmount"].lt(0).sum())
    terminal_nonclosed = int((~terminal["is_closed_status"]).sum())
    result = {
        "status": "BOUNDED_CLAIM_LEVEL_LOSS_TRANSFORM_EXECUTED_NO_TREATY_PROMOTION",
        "classification": "RESEARCH_ONLY_CONSUMER_SUFFICIENCY_PROBE",
        "source": {
            "repository": "MathiasValla/casdatasets-py",
            "commit": SOURCE_COMMIT,
            "path": SOURCE_PATH,
            "bytes": len(data),
            "git_blob_sha1": observed_blob,
            "sha256": observed_sha,
            "canonical_rdata_sha256": CANONICAL_RDATA_SHA256,
            "canonical_transport_equivalence_evidence": CANONICAL_EQUIVALENCE_EVIDENCE,
        },
        "runtime": {
            "python": sys.version,
            "platform": platform.platform(),
            "pandas": pd.__version__,
            "numpy": np.__version__,
        },
        "consumer_boundary": {
            "loss_measure": "last archive-observed cumulative PaidAmount for bounded closed-status claim cohort",
            "claim_identity": "ClaimID",
            "occurrence_resolution": "OccurYear only",
            "terminal_tie_rule": (
                "At maximum ManagYear, duplicate rows are accepted only when all consumer-state "
                "fields are identical; conflicting terminal duplicates are excluded."
            ),
            "closed_statuses": sorted(CLOSED_STATUSES),
            "negative_terminal_paid_handling": "excluded from bounded nonnegative-loss transform; count reported",
            "recourse_used_in_loss": False,
            "expected_charge_used_in_loss": False,
            "claim_status_used_only_for_bounded_cohort_selection": True,
            "archive_terminal_is_claimed_as_true_ultimate": False,
            "policy_or_event_coverage_inferred": False,
            "event_grouping_inferred": False,
            "market_treaty_price_inferred": False,
            "reinsurance_counterparty_inferred": False,
            "payment_date_inferred": False,
        },
        "population": {
            "all_rows": int(len(df)),
            "unique_claim_ids": int(df["ClaimID"].nunique()),
            **tie_diagnostics,
            "terminal_closed_status_claims": int(terminal["is_closed_status"].sum()),
            "terminal_nonclosed_status_claims": terminal_nonclosed,
            "terminal_negative_paid_claims": terminal_negative_paid,
            "bounded_calibration_claims": int(len(calibration)),
            "bounded_evaluation_claims": int(len(evaluation)),
        },
        "frozen_train_only_layer": {
            "calibration_occurrence_years": list(CALIBRATION_OCCURRENCE_YEARS),
            "evaluation_occurrence_years": list(EVALUATION_OCCURRENCE_YEARS),
            "calibration_positive_paid_claims": int(len(positive_calibration)),
            "quantile_convention": "nearest-rank on positive bounded calibration PaidAmount; stable mergesort",
            "attachment_definition": "calibration positive PaidAmount q90",
            "exhaustion_definition": "calibration positive PaidAmount q99",
            "attachment_eur": attachment,
            "exhaustion_eur": exhaustion,
            "limit_eur": limit,
            "transform": "ceded=min(max(PaidAmount-attachment,0),limit); net=PaidAmount-ceded",
        },
        "evaluation_all": all_evaluation,
        "evaluation_by_occurrence_year": evaluation_by_year,
        "consumer_disposition": {
            "exact_source_transport": "PASS_VIA_FFBK_1543_AND_REVERIFIED_PARQUET_BYTES",
            "observed_annual_claim_state": "BOUNDED_USABLE_WITH_EXPLICIT_MISSINGNESS_SEMANTICS",
            "simple_claim_level_paid_loss_transform": "BOUNDED_EXECUTABLE_ON_DECLARED_COHORT",
            "true_ultimate_claim_severity": "NOT_CLAIMED",
            "one_year_reserving_with_missing_t_plus_1_zero_imputation": "SENSITIVITY_ONLY_NOT_IDENTIFIED",
            "occurrence_or_event_reinsurance": "NOT_IDENTIFIED_NO_EVENT_GROUPING_OR_COVERAGE",
            "market_reinsurance_pricing": "NOT_IDENTIFIED_NO_QUOTES_OR_TREATY_PRICE",
            "dated_liquidity": "NOT_IDENTIFIED_NO_PAYMENT_DATES",
            "counterparty_or_recoverable_lifecycle": "NOT_IDENTIFIED",
        },
        "decision_interpretation": (
            "The result establishes only that a transparent per-ClaimID paid-loss layer can be "
            "computed on a declared archive-observed closed-status cohort and that its technical "
            "break-even premium can be reported without inventing a market price. It does not "
            "qualify occurrence XL, true ultimate severity, one-year reserve development, liquidity, "
            "counterparty/default or an RI strategy ranking."
        ),
    }
    print(json.dumps(result, indent=2, sort_keys=True, allow_nan=False))


if __name__ == "__main__":
    main()
