# Temporary exact-source adapter for FFBK/NextGen research execution only.
# It freezes the already-authored V2 model logic and replaces only the canonical
# RData decoder with the documented freclaimset2motor list-object contract.
from __future__ import annotations

import hashlib
import importlib.util
from pathlib import Path
import subprocess
import sys

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
V2_PATH = ROOT / "tmp" / "ffbk_freclaimset2motor_annual_reserving_v2.py"
MATERIALIZER = ROOT / "tmp" / "materialize_freclaimset2motor_exact.R"
PARQUET_PATH = Path("/tmp/freclaimset2motor-claimset.parquet")
EXPECTED_V2_GIT_BLOB_SHA1 = "9ea668f1fe42de580de3424c9d05f5a5b7181970"
EXPECTED_MATERIALIZER_GIT_BLOB_SHA1 = "966a0bb9320d0b7a338b91b582e39b3040ece710"
CLAIM_COLUMNS = [
    "ClaimID",
    "OccurYear",
    "ManagYear",
    "ClaimStatus",
    "PaidAmount",
    "RecourseAmount",
    "ExpectCharge",
    "ExpectRecourse",
]
STRING_COLUMNS = ["ClaimID", "ClaimStatus"]
YEAR_COLUMNS = ["OccurYear", "ManagYear"]
MONEY_COLUMNS = ["PaidAmount", "RecourseAmount", "ExpectCharge", "ExpectRecourse"]
MONEY_ATOL = 1e-9


def git_blob_sha1(path: Path) -> str:
    data = path.read_bytes()
    return hashlib.sha1(f"blob {len(data)}\0".encode("ascii") + data).hexdigest()


def require_frozen_bytes() -> None:
    observed_v2 = git_blob_sha1(V2_PATH)
    observed_materializer = git_blob_sha1(MATERIALIZER)
    if observed_v2 != EXPECTED_V2_GIT_BLOB_SHA1:
        raise SystemExit(
            f"V2 Git blob mismatch: {observed_v2} != {EXPECTED_V2_GIT_BLOB_SHA1}"
        )
    if observed_materializer != EXPECTED_MATERIALIZER_GIT_BLOB_SHA1:
        raise SystemExit(
            "materializer Git blob mismatch: "
            f"{observed_materializer} != {EXPECTED_MATERIALIZER_GIT_BLOB_SHA1}"
        )


def load_v2():
    spec = importlib.util.spec_from_file_location("ffbk_annual_reserving_v2_frozen", V2_PATH)
    if spec is None or spec.loader is None:
        raise SystemExit("cannot load frozen V2 module")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def normalize_claim_frame(frame: pd.DataFrame) -> pd.DataFrame:
    if list(frame.columns) != CLAIM_COLUMNS:
        raise SystemExit(f"claim transport columns mismatch: {list(frame.columns)}")
    out = frame.loc[:, CLAIM_COLUMNS].copy()
    for col in STRING_COLUMNS:
        out[col] = out[col].astype(str)
    for col in YEAR_COLUMNS:
        out[col] = pd.to_numeric(out[col], errors="raise").astype(np.int64)
    for col in MONEY_COLUMNS:
        out[col] = pd.to_numeric(out[col], errors="raise").astype(np.float64)
    return out.sort_values(CLAIM_COLUMNS, kind="mergesort").reset_index(drop=True)


def compare_claim_transports(canonical: pd.DataFrame, parquet: pd.DataFrame) -> dict:
    if len(canonical) != len(parquet):
        raise SystemExit(f"canonical/parquet row mismatch: {len(canonical)} != {len(parquet)}")
    left = normalize_claim_frame(canonical)
    right = normalize_claim_frame(parquet)

    exact_column_matches = {
        col: bool(left[col].equals(right[col]))
        for col in [*STRING_COLUMNS, *YEAR_COLUMNS]
    }
    money_max_abs_diff = {}
    money_all_close = {}
    for col in MONEY_COLUMNS:
        diff = np.abs(left[col].to_numpy() - right[col].to_numpy())
        max_diff = float(np.nanmax(diff)) if len(diff) else 0.0
        close = bool(np.allclose(left[col].to_numpy(), right[col].to_numpy(), rtol=0.0, atol=MONEY_ATOL, equal_nan=True))
        money_max_abs_diff[col] = max_diff
        money_all_close[col] = close

    equivalent = bool(all(exact_column_matches.values()) and all(money_all_close.values()))
    receipt = {
        "canonical_rows": int(len(left)),
        "parquet_rows": int(len(right)),
        "exact_column_matches": exact_column_matches,
        "money_atol": MONEY_ATOL,
        "money_max_abs_diff": money_max_abs_diff,
        "money_all_close": money_all_close,
        "equivalent": equivalent,
    }
    if not equivalent:
        raise SystemExit("canonical RData claimset and pinned Parquet transport are not equivalent: " + str(receipt))
    return receipt


def canonical_audit_exact(rdata_path: Path) -> dict:
    claims_csv = Path("/tmp/freclaimset2motor-canonical-claimset.csv")
    aggregate_csv = Path("/tmp/freclaimset2motor-canonical-aggdata.csv")
    completed = subprocess.run(
        [
            "Rscript",
            "--vanilla",
            str(MATERIALIZER),
            str(rdata_path),
            str(claims_csv),
            str(aggregate_csv),
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0:
        raise SystemExit(
            "canonical RData materialization failed: " + completed.stderr.strip()
        )
    if not claims_csv.is_file() or not aggregate_csv.is_file():
        raise SystemExit("canonical materialization did not produce both CSV transports")
    if not PARQUET_PATH.is_file():
        raise SystemExit("pinned Parquet transport is missing before equivalence gate")

    canonical_claims = pd.read_csv(claims_csv, low_memory=False)
    parquet_claims = pd.read_parquet(PARQUET_PATH)
    transport_equivalence = compare_claim_transports(canonical_claims, parquet_claims)
    aggregate = pd.read_csv(aggregate_csv, low_memory=False)
    occur = pd.to_numeric(canonical_claims["OccurYear"], errors="coerce")
    management = pd.to_numeric(canonical_claims["ManagYear"], errors="coerce")
    return {
        "objects_required": ["freclaimset2motor"],
        "components_required": ["claimset", "aggdata"],
        "materializer": "base_R_load_documented_list_contract",
        "materializer_stdout": completed.stdout.strip(),
        "materializer_git_blob_sha1": git_blob_sha1(MATERIALIZER),
        "frozen_v2_git_blob_sha1": git_blob_sha1(V2_PATH),
        "rows": int(len(canonical_claims)),
        "aggregate_rows": int(len(aggregate)),
        "columns": [str(x) for x in canonical_claims.columns],
        "unique_claim_ids": int(canonical_claims["ClaimID"].nunique(dropna=True)),
        "rows_management_equals_occurrence": int((management == occur).sum()),
        "claims_csv_sha256": hashlib.sha256(claims_csv.read_bytes()).hexdigest(),
        "aggregate_csv_sha256": hashlib.sha256(aggregate_csv.read_bytes()).hexdigest(),
        "pinned_parquet_transport_equivalence": transport_equivalence,
    }


def main() -> None:
    require_frozen_bytes()
    v2 = load_v2()
    v2.canonical_audit = canonical_audit_exact
    v2.main()


if __name__ == "__main__":
    main()
