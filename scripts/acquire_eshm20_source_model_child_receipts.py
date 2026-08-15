# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Receipt exactly the 51 ESHM20 source-model children proven by #397.

Trusted-main execution result comment 5304432768 derived exactly 51 canonical,
non-HDF5 source-model paths from the already-receipted ESHM20 source-model
logic tree. This worker fixes that returned set in code and receipts only those
immutable provider objects. Provider bytes are streamed into the existing
receipt primitive and are never returned or persisted. Callers cannot select
provider, project, ref, path, file set, parser, or dependency expansion.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import time
import urllib.error
import urllib.request
from typing import Any

try:
    from scripts.acquire_efehr_gitlab_receipt import (
        EfehrAcquisitionError,
        _DeadlineStream,
        _declared_length,
        _open_fixed,
        _remaining,
        _validate_exact_response,
        utc_now,
    )
    from scripts.efehr_gitlab_receipt import (
        MAX_FILE_BYTES,
        PROVIDER_HOST,
        EfehrReceiptError,
        raw_file_api_url,
        receipt_from_stream,
        validate_target,
    )
except ModuleNotFoundError:  # pragma: no cover - direct script import path
    from acquire_efehr_gitlab_receipt import (
        EfehrAcquisitionError,
        _DeadlineStream,
        _declared_length,
        _open_fixed,
        _remaining,
        _validate_exact_response,
        utc_now,
    )
    from efehr_gitlab_receipt import (
        MAX_FILE_BYTES,
        PROVIDER_HOST,
        EfehrReceiptError,
        raw_file_api_url,
        receipt_from_stream,
        validate_target,
    )

SCHEMA_VERSION = "oc-eshm20-source-model-child-receipt-set-v1"
OPERATION_ID = "eshm20-source-model-child-receipts-v12e-region-main-v1"
CONTROL_ISSUE = 414
SOURCE_ISSUE = 281
DATASET_ID = "efehr.eshm20"
PROJECT_ID = 197
PROJECT_PATH = "efehr/eshm20"
COMMIT_SHA = "fbd334de68f85d72669f73fc5a314a113db67317"
PARENT_REQUEST_COMMENT_ID = 5304431360
PARENT_RESULT_COMMENT_ID = 5304432768
PARENT_RUN_ID = 31910992436
PARENT_EXECUTION_SHA = "dac7c9ae1c391006b8272f1342143d1ace678234"
PARENT_SEMANTIC_REQUEST_ID = (
    "e96030c55952bf9b4b2c6911368c52b9353bd161860923203d115f550824c27e"
)
PARENT_SOURCE_TREE_BYTE_COUNT = 17_579
PARENT_SOURCE_TREE_SHA256 = (
    "97a37911f9eae73766f386686b112e5a4e111965da3e4e1543627c28d4201867"
)
EXPECTED_CHILD_COUNT = 51
EXPECTED_PATHS_SHA256 = "2fcc885dc9fbbd8e9ee45b185dc9f2339af3654e9976ae5f07d4d097551944b7"
MAX_ARTIFACT_BYTES = MAX_FILE_BYTES
TOTAL_DEADLINE_SECONDS = 180.0


@dataclass(frozen=True)
class ChildSpec:
    repository_path: str


def _spec(relative_path: str) -> ChildSpec:
    return ChildSpec(
        repository_path=(
            "oq_computational/oq_configuration_eshm20_v12e_region_main/source_models/"
            + relative_path
        )
    )


_CANONICAL_CHILDREN: tuple[ChildSpec, ...] = tuple(
    _spec(path)
    for path in (
        "asm_v12e/asm_ver12e_winGT_fs017_hi_abgrs_maxmag_low.xml",
        "asm_v12e/asm_ver12e_winGT_fs017_hi_abgrs_maxmag_mid.xml",
        "asm_v12e/asm_ver12e_winGT_fs017_hi_abgrs_maxmag_upp.xml",
        "asm_v12e/asm_ver12e_winGT_fs017_lo_abgrs_maxmag_low.xml",
        "asm_v12e/asm_ver12e_winGT_fs017_lo_abgrs_maxmag_mid.xml",
        "asm_v12e/asm_ver12e_winGT_fs017_lo_abgrs_maxmag_upp.xml",
        "asm_v12e/asm_ver12e_winGT_fs017_mid_abgrs_maxmag_low.xml",
        "asm_v12e/asm_ver12e_winGT_fs017_mid_abgrs_maxmag_mid.xml",
        "asm_v12e/asm_ver12e_winGT_fs017_mid_abgrs_maxmag_upp.xml",
        "asm_v12e/asm_ver12e_winGT_fs017_pareto_abgrs_cornermag_low.xml",
        "asm_v12e/asm_ver12e_winGT_fs017_pareto_abgrs_cornermag_mid.xml",
        "asm_v12e/asm_ver12e_winGT_fs017_pareto_abgrs_cornermag_upp.xml",
        "asm_v12e/asm_ver12e_winGT_fs017_twingr.xml",
        "deep_v12e/asm_deep_ver12e_winGT_fs017_hi_abgrs_maxmag_low.xml",
        "deep_v12e/asm_deep_ver12e_winGT_fs017_hi_abgrs_maxmag_mid.xml",
        "deep_v12e/asm_deep_ver12e_winGT_fs017_hi_abgrs_maxmag_upp.xml",
        "deep_v12e/asm_deep_ver12e_winGT_fs017_lo_abgrs_maxmag_low.xml",
        "deep_v12e/asm_deep_ver12e_winGT_fs017_lo_abgrs_maxmag_mid.xml",
        "deep_v12e/asm_deep_ver12e_winGT_fs017_lo_abgrs_maxmag_upp.xml",
        "deep_v12e/asm_deep_ver12e_winGT_fs017_mid_abgrs_maxmag_low.xml",
        "deep_v12e/asm_deep_ver12e_winGT_fs017_mid_abgrs_maxmag_mid.xml",
        "deep_v12e/asm_deep_ver12e_winGT_fs017_mid_abgrs_maxmag_upp.xml",
        "deep_v12e/asm_deep_ver12e_winGT_fs017_pareto_abgrs_cornermag_low.xml",
        "deep_v12e/asm_deep_ver12e_winGT_fs017_pareto_abgrs_cornermag_mid.xml",
        "deep_v12e/asm_deep_ver12e_winGT_fs017_pareto_abgrs_cornermag_upp.xml",
        "fsm_v09/fs_ver09e_model_aGR_SRA_MA_fMthr.xml",
        "fsm_v09/fs_ver09e_model_aGR_SRA_ML_fMthr.xml",
        "fsm_v09/fs_ver09e_model_aGR_SRA_MU_fMthr.xml",
        "fsm_v09/fs_ver09e_model_aGR_SRL_MA_fMthr.xml",
        "fsm_v09/fs_ver09e_model_aGR_SRL_ML_fMthr.xml",
        "fsm_v09/fs_ver09e_model_aGR_SRL_MU_fMthr.xml",
        "fsm_v09/fs_ver09e_model_aGR_SRU_MA_fMthr.xml",
        "fsm_v09/fs_ver09e_model_aGR_SRU_ML_fMthr.xml",
        "fsm_v09/fs_ver09e_model_aGR_SRU_MU_fMthr.xml",
        "interface_v12b/CaA_IF2222222_M40.xml",
        "interface_v12b/CyA_IF2222222_M40.xml",
        "interface_v12b/GiA_IF2222222_M40.xml",
        "interface_v12b/HeA_IF2222222_M40.xml",
        "ssm_v09/seis_ver12b_fMthr_asm_ver12e_winGT_fs017_agbrs_point.xml",
        "volcanic_v12e/asm_volcanic_ver12e_winGT_fs017_hi_abgrs_maxmag_low.xml",
        "volcanic_v12e/asm_volcanic_ver12e_winGT_fs017_hi_abgrs_maxmag_mid.xml",
        "volcanic_v12e/asm_volcanic_ver12e_winGT_fs017_hi_abgrs_maxmag_upp.xml",
        "volcanic_v12e/asm_volcanic_ver12e_winGT_fs017_lo_abgrs_maxmag_low.xml",
        "volcanic_v12e/asm_volcanic_ver12e_winGT_fs017_lo_abgrs_maxmag_mid.xml",
        "volcanic_v12e/asm_volcanic_ver12e_winGT_fs017_lo_abgrs_maxmag_upp.xml",
        "volcanic_v12e/asm_volcanic_ver12e_winGT_fs017_mid_abgrs_maxmag_low.xml",
        "volcanic_v12e/asm_volcanic_ver12e_winGT_fs017_mid_abgrs_maxmag_mid.xml",
        "volcanic_v12e/asm_volcanic_ver12e_winGT_fs017_mid_abgrs_maxmag_upp.xml",
        "volcanic_v12e/asm_volcanic_ver12e_winGT_fs017_pareto_abgrs_cornermag_low.xml",
        "volcanic_v12e/asm_volcanic_ver12e_winGT_fs017_pareto_abgrs_cornermag_mid.xml",
        "volcanic_v12e/asm_volcanic_ver12e_winGT_fs017_pareto_abgrs_cornermag_upp.xml",
    )
)
CHILDREN = _CANONICAL_CHILDREN


class Eshm20SourceModelChildReceiptError(RuntimeError):
    """Raised when the fixed 51-child receipt set cannot close safely."""


def _paths_fingerprint(specs: tuple[ChildSpec, ...]) -> str:
    payload = "".join(f"{spec.repository_path}\n" for spec in specs).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _require_authorized_spec(spec: object) -> ChildSpec:
    if type(spec) is not ChildSpec or not any(
        spec is candidate for candidate in _CANONICAL_CHILDREN
    ):
        raise Eshm20SourceModelChildReceiptError(
            "ESHM20 source-model child spec is not an authorized fixed target"
        )
    return spec


def _require_canonical_child_set() -> tuple[ChildSpec, ...]:
    if CHILDREN is not _CANONICAL_CHILDREN:
        raise Eshm20SourceModelChildReceiptError(
            "frozen ESHM20 source-model child set identity is invalid"
        )
    if len(CHILDREN) != EXPECTED_CHILD_COUNT:
        raise Eshm20SourceModelChildReceiptError(
            "frozen ESHM20 source-model child count is invalid"
        )
    if any(
        active is not expected
        for active, expected in zip(CHILDREN, _CANONICAL_CHILDREN, strict=True)
    ):
        raise Eshm20SourceModelChildReceiptError(
            "frozen ESHM20 source-model child set identity is invalid"
        )
    paths = tuple(spec.repository_path for spec in CHILDREN)
    if paths != tuple(sorted(paths)) or len(set(paths)) != EXPECTED_CHILD_COUNT:
        raise Eshm20SourceModelChildReceiptError(
            "frozen ESHM20 source-model child ordering is invalid"
        )
    if _paths_fingerprint(CHILDREN) != EXPECTED_PATHS_SHA256:
        raise Eshm20SourceModelChildReceiptError(
            "frozen ESHM20 source-model child path fingerprint is invalid"
        )
    return _CANONICAL_CHILDREN


def _receipt_one(
    spec: ChildSpec,
    *,
    deadline: float,
    opener: Any,
    now: Any,
    monotonic: Any,
) -> dict[str, Any]:
    spec = _require_authorized_spec(spec)
    try:
        target = validate_target(
            source_issue=SOURCE_ISSUE,
            dataset_id=DATASET_ID,
            project_id=PROJECT_ID,
            commit_sha=COMMIT_SHA,
            repository_path=spec.repository_path,
        )
    except EfehrReceiptError as exc:
        raise Eshm20SourceModelChildReceiptError(
            "trusted ESHM20 source-model child target is invalid"
        ) from exc

    file_url = raw_file_api_url(target)
    request = urllib.request.Request(
        file_url,
        headers={
            "Accept": "application/xml,text/xml,text/plain,application/octet-stream;q=0.8",
            "User-Agent": "OpenCatastrophe-ESHM20-source-model-child-receipts-v1",
        },
        method="GET",
    )
    try:
        with opener(request, timeout=_remaining(deadline, monotonic)) as response:
            _validate_exact_response(response, file_url)
            _declared_length(response, MAX_ARTIFACT_BYTES)
            try:
                receipt = receipt_from_stream(
                    target,
                    _DeadlineStream(
                        response,
                        deadline=deadline,
                        monotonic=monotonic,
                    ),
                    final_url=file_url,
                    retrieved_at=now(),
                    headers=getattr(response, "headers", None),
                    max_bytes=MAX_ARTIFACT_BYTES,
                )
            except EfehrReceiptError as exc:
                raise Eshm20SourceModelChildReceiptError(
                    "ESHM20 source-model child receipt failed closed"
                ) from exc
    except Eshm20SourceModelChildReceiptError:
        raise
    except EfehrAcquisitionError as exc:
        raise Eshm20SourceModelChildReceiptError(
            "ESHM20 source-model child retrieval failed closed"
        ) from exc
    except (OSError, urllib.error.URLError, urllib.error.HTTPError, TimeoutError) as exc:
        raise Eshm20SourceModelChildReceiptError(
            f"ESHM20 source-model child retrieval failed: {type(exc).__name__}"
        ) from exc

    if (
        receipt.get("external_bytes_persisted") is not False
        or receipt.get("publication_authorized") is not False
    ):
        raise Eshm20SourceModelChildReceiptError(
            "ESHM20 source-model child receipt widened its authority ceiling"
        )
    return {
        **receipt,
        "parent_result_comment_id": PARENT_RESULT_COMMENT_ID,
    }


def acquire_eshm20_source_model_child_receipts(
    *,
    opener: Any | None = None,
    now: Any = utc_now,
    monotonic: Any = time.monotonic,
) -> dict[str, Any]:
    """Receipt only the exact 51-child set returned by trusted-main #397.

    The operation is atomic from the caller's perspective: failure while
    retrieving any member raises and returns no partial receipt object.
    """

    children = _require_canonical_child_set()
    deadline = monotonic() + TOTAL_DEADLINE_SECONDS
    open_response = opener or _open_fixed
    receipts = tuple(
        _receipt_one(
            spec,
            deadline=deadline,
            opener=open_response,
            now=now,
            monotonic=monotonic,
        )
        for spec in children
    )
    final_retrieved_at = receipts[-1]["retrieved_at"]
    return {
        "schema_version": SCHEMA_VERSION,
        "operation_id": OPERATION_ID,
        "control_issue": CONTROL_ISSUE,
        "source_issue": SOURCE_ISSUE,
        "dataset_id": DATASET_ID,
        "provider_host": PROVIDER_HOST,
        "project_id": PROJECT_ID,
        "project_path": PROJECT_PATH,
        "commit_sha": COMMIT_SHA,
        "parent_request_comment_id": PARENT_REQUEST_COMMENT_ID,
        "parent_result_comment_id": PARENT_RESULT_COMMENT_ID,
        "parent_run_id": PARENT_RUN_ID,
        "parent_execution_sha": PARENT_EXECUTION_SHA,
        "parent_semantic_request_id": PARENT_SEMANTIC_REQUEST_ID,
        "parent_source_tree_byte_count": PARENT_SOURCE_TREE_BYTE_COUNT,
        "parent_source_tree_sha256": PARENT_SOURCE_TREE_SHA256,
        "child_count": EXPECTED_CHILD_COUNT,
        "child_paths_sha256": EXPECTED_PATHS_SHA256,
        "retrieved_at": final_retrieved_at,
        "receipts": list(receipts),
        "dependency_inventory_authorized": False,
        "dependency_receipt_authorized": False,
        "external_bytes_persisted": False,
        "publication_authorized": False,
        "model_use_authorized": False,
    }
