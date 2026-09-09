# Temporary exact-source adapter for FFBK/NextGen research execution only.
# It freezes the already-authored V2 model logic and replaces only the canonical
# RData decoder with the documented freclaimset2motor list-object contract.
from __future__ import annotations

import hashlib
import importlib.util
from pathlib import Path
import subprocess
import sys

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
V2_PATH = ROOT / "tmp" / "ffbk_freclaimset2motor_annual_reserving_v2.py"
MATERIALIZER = ROOT / "tmp" / "materialize_freclaimset2motor_exact.R"
EXPECTED_V2_GIT_BLOB_SHA1 = "9ea668f1fe42de580de3424c9d05f5a5b7181970"
EXPECTED_MATERIALIZER_GIT_BLOB_SHA1 = "966a0bb9320d0b7a338b91b582e39b3040ece710"


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

    columns = list(pd.read_csv(claims_csv, nrows=0).columns)
    claim_keys = pd.read_csv(
        claims_csv,
        usecols=["ClaimID", "OccurYear", "ManagYear"],
        low_memory=False,
    )
    aggregate = pd.read_csv(aggregate_csv, low_memory=False)
    occur = pd.to_numeric(claim_keys["OccurYear"], errors="coerce")
    management = pd.to_numeric(claim_keys["ManagYear"], errors="coerce")
    return {
        "objects_required": ["freclaimset2motor"],
        "components_required": ["claimset", "aggdata"],
        "materializer": "base_R_load_documented_list_contract",
        "materializer_stdout": completed.stdout.strip(),
        "materializer_git_blob_sha1": git_blob_sha1(MATERIALIZER),
        "frozen_v2_git_blob_sha1": git_blob_sha1(V2_PATH),
        "rows": int(len(claim_keys)),
        "aggregate_rows": int(len(aggregate)),
        "columns": [str(x) for x in columns],
        "unique_claim_ids": int(claim_keys["ClaimID"].nunique(dropna=True)),
        "rows_management_equals_occurrence": int((management == occur).sum()),
        "claims_csv_sha256": hashlib.sha256(claims_csv.read_bytes()).hexdigest(),
        "aggregate_csv_sha256": hashlib.sha256(aggregate_csv.read_bytes()).hexdigest(),
    }


def main() -> None:
    require_frozen_bytes()
    v2 = load_v2()
    v2.canonical_audit = canonical_audit_exact
    v2.main()


if __name__ == "__main__":
    main()
