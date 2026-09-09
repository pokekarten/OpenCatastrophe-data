# Temporary observation-process audit for FFBK/NextGen research only.
# No model is fitted. This quantifies whether absent exact t+1 rows can safely be
# interpreted as observed zero movement in the annual panel.
from __future__ import annotations

import hashlib
import json
import urllib.request
from pathlib import Path

import pandas as pd

SOURCE_COMMIT = "10af669a599c1d4d69288f62f13978be2e82b3b4"
SOURCE_BLOB_SHA1 = "9f75aec12a7e2f4e32f8abf98a7670087ba48cd7"
SOURCE_SIZE = 6743477
SOURCE_PATH = "src/casdatasets/data/parquet/freclaimset2motor/claimset.parquet"
SOURCE_URL = f"https://raw.githubusercontent.com/MathiasValla/casdatasets-py/{SOURCE_COMMIT}/{SOURCE_PATH}"
YEARS = list(range(2004, 2014))
EPS = 1e-12
CLOSED_STATUSES = {"fully closed", "closed without further action"}


def git_blob_sha1(data: bytes) -> str:
    return hashlib.sha1(f"blob {len(data)}\0".encode("ascii") + data).hexdigest()


def status_counts(frame: pd.DataFrame) -> dict[str, int]:
    return {
        str(k): int(v)
        for k, v in frame["status_norm"].value_counts(dropna=False).sort_index().to_dict().items()
    }


def summarize_slice(frame: pd.DataFrame) -> dict:
    exact = frame[frame["has_exact_next"]]
    missing = frame[~frame["has_exact_next"]]
    same_year_duplicate_next = missing[missing["has_same_year_duplicate_next"]]
    later_gap = missing[missing["has_later_gap"]]
    terminal = missing[missing["is_terminal_no_next_row"]]
    terminal_open_like = terminal[~terminal["status_norm"].isin(CLOSED_STATUSES)]
    return {
        "rows": int(len(frame)),
        "exact_t_plus_1_rows": int(len(exact)),
        "exact_t_plus_1_by_current_status": status_counts(exact),
        "missing_exact_t_plus_1_rows": int(len(missing)),
        "missing_exact_t_plus_1_share": float(len(missing) / len(frame)) if len(frame) else None,
        "missing_by_current_status": status_counts(missing),
        "same_year_duplicate_next_rows": int(len(same_year_duplicate_next)),
        "missing_with_later_gap_gt_1": int(len(later_gap)),
        "missing_terminal_no_next_row": int(len(terminal)),
        "terminal_missing_by_current_status": status_counts(terminal),
        "terminal_missing_open_like_rows": int(len(terminal_open_like)),
        "later_gap_with_nonzero_paid_change": int(
            (later_gap["next_observed_paid_change"].abs() > EPS).sum()
        ),
        "later_gap_years": {
            str(int(k)): int(v)
            for k, v in later_gap["next_observed_gap"].value_counts().sort_index().to_dict().items()
        },
    }


def main() -> None:
    path = Path("/tmp/freclaimset2motor-observation-audit.parquet")
    urllib.request.urlretrieve(SOURCE_URL, path)
    data = path.read_bytes()
    if len(data) != SOURCE_SIZE:
        raise SystemExit(f"unexpected byte size: {len(data)} != {SOURCE_SIZE}")
    observed_blob = git_blob_sha1(data)
    if observed_blob != SOURCE_BLOB_SHA1:
        raise SystemExit(f"git blob mismatch: {observed_blob} != {SOURCE_BLOB_SHA1}")

    df = pd.read_parquet(path)
    required = {"ClaimID", "OccurYear", "ManagYear", "ClaimStatus", "PaidAmount"}
    if not required.issubset(df.columns):
        raise SystemExit(f"missing columns: {sorted(required - set(df.columns))}")
    df["OccurYear"] = pd.to_numeric(df["OccurYear"], errors="raise").astype(int)
    df["ManagYear"] = pd.to_numeric(df["ManagYear"], errors="raise").astype(int)
    df["PaidAmount"] = pd.to_numeric(df["PaidAmount"], errors="raise").astype(float)
    df["status_norm"] = df["ClaimStatus"].astype(str).str.strip().str.lower()
    df = df.sort_values(["ClaimID", "ManagYear"], kind="mergesort").reset_index(drop=True)

    grouped = df.groupby("ClaimID", sort=False)
    next_year = grouped["ManagYear"].shift(-1)
    next_paid = grouped["PaidAmount"].shift(-1)
    df["next_observed_year"] = next_year
    df["next_observed_gap"] = next_year - df["ManagYear"]
    df["has_exact_next"] = df["next_observed_gap"].eq(1)
    df["has_same_year_duplicate_next"] = df["next_observed_gap"].eq(0)
    df["has_later_gap"] = df["next_observed_gap"].gt(1)
    df["is_terminal_no_next_row"] = next_year.isna()
    df["next_observed_paid_change"] = next_paid - df["PaidAmount"]

    all_missing = df[~df["has_exact_next"]]
    later_gap_missing = all_missing[all_missing["has_later_gap"]]

    by_year = {
        str(year): summarize_slice(df[df["ManagYear"] == year])
        for year in YEARS
    }

    result = {
        "status": "OBSERVATION_PROCESS_AUDIT_ONLY",
        "source": {
            "repository": "MathiasValla/casdatasets-py",
            "commit": SOURCE_COMMIT,
            "path": SOURCE_PATH,
            "bytes": len(data),
            "git_blob_sha1": observed_blob,
            "sha256": hashlib.sha256(data).hexdigest(),
        },
        "population": {
            "rows": int(len(df)),
            "unique_claim_ids": int(df["ClaimID"].nunique()),
        },
        "all_rows": summarize_slice(df),
        "all_later_gap_missing_by_current_status": status_counts(later_gap_missing),
        "years_2004_2013": by_year,
        "identification_boundary": {
            "missing_exact_t_plus_1_is_observed_zero": False,
            "reason": (
                "An absent exact t+1 row does not itself reveal the unobserved within-gap path. "
                "Rows with a later management-year reappearance (gap > 1), especially with changed cumulative paid, "
                "directly show that row absence and observed economic zero movement are distinct concepts. "
                "Same-year duplicate rows are tracked separately and are not called later reappearance. "
                "Terminal absence may be consistent with closure but is not converted into an observed t+1 cash fact by this audit."
            ),
            "model_use": "sensitivity_only_until_observation_semantics_are_independently_justified",
        },
    }
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
