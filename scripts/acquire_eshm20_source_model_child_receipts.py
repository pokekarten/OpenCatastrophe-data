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

# Production authority is private. Public names remain review/back-compat aliases;
# any alias or imported primitive drift fails before provider I/O.
_CANONICAL_SCHEMA_VERSION = "oc-eshm20-source-model-child-receipt-set-v1"
_CANONICAL_OPERATION_ID = "eshm20-source-model-child-receipts-v12e-region-main-v1"
_CANONICAL_CONTROL_ISSUE = 414
_CANONICAL_SOURCE_ISSUE = 281
_CANONICAL_DATASET_ID = "efehr.eshm20"
_CANONICAL_PROVIDER_HOST = PROVIDER_HOST
_CANONICAL_PROJECT_ID = 197
_CANONICAL_PROJECT_PATH = "efehr/eshm20"
_CANONICAL_COMMIT_SHA = "fbd334de68f85d72669f73fc5a314a113db67317"
_CANONICAL_PARENT_REQUEST_COMMENT_ID = 5304431360
_CANONICAL_PARENT_RESULT_COMMENT_ID = 5304432768
_CANONICAL_PARENT_RUN_ID = 31910992436
_CANONICAL_PARENT_EXECUTION_SHA = "dac7c9ae1c391006b8272f1342143d1ace678234"
_CANONICAL_PARENT_SEMANTIC_REQUEST_ID = (
    "e96030c55952bf9b4b2c6911368c52b9353bd161860923203d115f550824c27e"
)
_CANONICAL_PARENT_SOURCE_TREE_BYTE_COUNT = 17_579
_CANONICAL_PARENT_SOURCE_TREE_SHA256 = (
    "97a37911f9eae73766f386686b112e5a4e111965da3e4e1543627c28d4201867"
)
_CANONICAL_EXPECTED_CHILD_COUNT = 51
_CANONICAL_EXPECTED_PATHS_SHA256 = (
    "2fcc885dc9fbbd8e9ee45b185dc9f2339af3654e9976ae5f07d4d097551944b7"
)
_CANONICAL_MAX_ARTIFACT_BYTES = MAX_FILE_BYTES
_CANONICAL_TOTAL_DEADLINE_SECONDS = 180.0

_CANONICAL_OPEN_FIXED = _open_fixed
_CANONICAL_UTC_NOW = utc_now
_CANONICAL_MONOTONIC = time.monotonic
_CANONICAL_VALIDATE_TARGET = validate_target
_CANONICAL_RAW_FILE_API_URL = raw_file_api_url
_CANONICAL_REMAINING = _remaining
_CANONICAL_VALIDATE_EXACT_RESPONSE = _validate_exact_response
_CANONICAL_DECLARED_LENGTH = _declared_length
_CANONICAL_RECEIPT_FROM_STREAM = receipt_from_stream
_CANONICAL_DEADLINE_STREAM = _DeadlineStream

SCHEMA_VERSION = _CANONICAL_SCHEMA_VERSION
OPERATION_ID = _CANONICAL_OPERATION_ID
CONTROL_ISSUE = _CANONICAL_CONTROL_ISSUE
SOURCE_ISSUE = _CANONICAL_SOURCE_ISSUE
DATASET_ID = _CANONICAL_DATASET_ID
PROJECT_ID = _CANONICAL_PROJECT_ID
PROJECT_PATH = _CANONICAL_PROJECT_PATH
COMMIT_SHA = _CANONICAL_COMMIT_SHA
PARENT_REQUEST_COMMENT_ID = _CANONICAL_PARENT_REQUEST_COMMENT_ID
PARENT_RESULT_COMMENT_ID = _CANONICAL_PARENT_RESULT_COMMENT_ID
PARENT_RUN_ID = _CANONICAL_PARENT_RUN_ID
PARENT_EXECUTION_SHA = _CANONICAL_PARENT_EXECUTION_SHA
PARENT_SEMANTIC_REQUEST_ID = _CANONICAL_PARENT_SEMANTIC_REQUEST_ID
PARENT_SOURCE_TREE_BYTE_COUNT = _CANONICAL_PARENT_SOURCE_TREE_BYTE_COUNT
PARENT_SOURCE_TREE_SHA256 = _CANONICAL_PARENT_SOURCE_TREE_SHA256
EXPECTED_CHILD_COUNT = _CANONICAL_EXPECTED_CHILD_COUNT
EXPECTED_PATHS_SHA256 = _CANONICAL_EXPECTED_PATHS_SHA256
MAX_ARTIFACT_BYTES = _CANONICAL_MAX_ARTIFACT_BYTES
TOTAL_DEADLINE_SECONDS = _CANONICAL_TOTAL_DEADLINE_SECONDS


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


def _require_production_identity() -> None:
    identities = (
        (_open_fixed, _CANONICAL_OPEN_FIXED, "transport"),
        (utc_now, _CANONICAL_UTC_NOW, "UTC clock"),
        (time.monotonic, _CANONICAL_MONOTONIC, "monotonic clock"),
        (validate_target, _CANONICAL_VALIDATE_TARGET, "target validator"),
        (raw_file_api_url, _CANONICAL_RAW_FILE_API_URL, "URL builder"),
        (_remaining, _CANONICAL_REMAINING, "deadline helper"),
        (_validate_exact_response, _CANONICAL_VALIDATE_EXACT_RESPONSE, "response validator"),
        (_declared_length, _CANONICAL_DECLARED_LENGTH, "length validator"),
        (receipt_from_stream, _CANONICAL_RECEIPT_FROM_STREAM, "receipt builder"),
        (_DeadlineStream, _CANONICAL_DEADLINE_STREAM, "bounded stream"),
    )
    for observed, expected, label in identities:
        if observed is not expected:
            raise Eshm20SourceModelChildReceiptError(
                f"frozen ESHM20 child-receipt production {label} drifted"
            )


def _require_canonical_authority() -> None:
    aliases = (
        (SCHEMA_VERSION, _CANONICAL_SCHEMA_VERSION, "schema version"),
        (OPERATION_ID, _CANONICAL_OPERATION_ID, "operation id"),
        (CONTROL_ISSUE, _CANONICAL_CONTROL_ISSUE, "control issue"),
        (SOURCE_ISSUE, _CANONICAL_SOURCE_ISSUE, "source issue"),
        (DATASET_ID, _CANONICAL_DATASET_ID, "dataset id"),
        (PROJECT_ID, _CANONICAL_PROJECT_ID, "project id"),
        (PROJECT_PATH, _CANONICAL_PROJECT_PATH, "project path"),
        (COMMIT_SHA, _CANONICAL_COMMIT_SHA, "commit"),
        (PARENT_REQUEST_COMMENT_ID, _CANONICAL_PARENT_REQUEST_COMMENT_ID, "parent request"),
        (PARENT_RESULT_COMMENT_ID, _CANONICAL_PARENT_RESULT_COMMENT_ID, "parent result"),
        (PARENT_RUN_ID, _CANONICAL_PARENT_RUN_ID, "parent run"),
        (PARENT_EXECUTION_SHA, _CANONICAL_PARENT_EXECUTION_SHA, "parent execution"),
        (PARENT_SEMANTIC_REQUEST_ID, _CANONICAL_PARENT_SEMANTIC_REQUEST_ID, "parent semantic id"),
        (PARENT_SOURCE_TREE_BYTE_COUNT, _CANONICAL_PARENT_SOURCE_TREE_BYTE_COUNT, "parent byte count"),
        (PARENT_SOURCE_TREE_SHA256, _CANONICAL_PARENT_SOURCE_TREE_SHA256, "parent SHA-256"),
        (EXPECTED_CHILD_COUNT, _CANONICAL_EXPECTED_CHILD_COUNT, "child count"),
        (EXPECTED_PATHS_SHA256, _CANONICAL_EXPECTED_PATHS_SHA256, "path fingerprint"),
        (MAX_ARTIFACT_BYTES, _CANONICAL_MAX_ARTIFACT_BYTES, "maximum bytes"),
        (TOTAL_DEADLINE_SECONDS, _CANONICAL_TOTAL_DEADLINE_SECONDS, "deadline"),
    )
    for observed, expected, label in aliases:
        if type(observed) is not type(expected) or observed != expected:
            raise Eshm20SourceModelChildReceiptError(
                f"frozen ESHM20 child-receipt {label} drifted"
            )


def _require_canonical_child_set() -> tuple[ChildSpec, ...]:
    _require_canonical_authority()
    if CHILDREN is not _CANONICAL_CHILDREN:
        raise Eshm20SourceModelChildReceiptError(
            "frozen ESHM20 source-model child set identity is invalid"
        )
    if len(CHILDREN) != _CANONICAL_EXPECTED_CHILD_COUNT:
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
    if paths != tuple(sorted(paths)) or len(set(paths)) != _CANONICAL_EXPECTED_CHILD_COUNT:
        raise Eshm20SourceModelChildReceiptError(
            "frozen ESHM20 source-model child ordering is invalid"
        )
    if _paths_fingerprint(CHILDREN) != _CANONICAL_EXPECTED_PATHS_SHA256:
        raise Eshm20SourceModelChildReceiptError(
            "frozen ESHM20 source-model child path fingerprint is invalid"
        )
    return _CANONICAL_CHILDREN


def _is_lower_sha256(value: object) -> bool:
    return (
        type(value) is str
        and len(value) == 64
        and all(character in "0123456789abcdef" for character in value)
    )


_CORE_RECEIPT_FIELDS = {
    "schema_version",
    "source_issue",
    "dataset_id",
    "provider_host",
    "project_id",
    "project_path",
    "commit_sha",
    "repository_path",
    "requested_url",
    "final_url",
    "retrieved_at",
    "byte_count",
    "sha256",
    "content_type",
    "etag",
    "external_bytes_persisted",
    "publication_authorized",
}

_CHILD_RECEIPT_FIELDS = {
    "repository_path",
    "retrieved_at",
    "byte_count",
    "sha256",
    "project_id",
    "project_path",
    "commit_sha",
    "parent_result_comment_id",
    "external_bytes_persisted",
    "publication_authorized",
    "model_use_authorized",
}


def _project_core_receipt(
    receipt: object,
    *,
    spec: ChildSpec,
    file_url: str,
) -> dict[str, Any]:
    if type(receipt) is not dict or set(receipt) != _CORE_RECEIPT_FIELDS:
        raise Eshm20SourceModelChildReceiptError(
            "ESHM20 source-model child core receipt fields drifted"
        )
    exact = (
        ("source_issue", _CANONICAL_SOURCE_ISSUE),
        ("dataset_id", _CANONICAL_DATASET_ID),
        ("provider_host", _CANONICAL_PROVIDER_HOST),
        ("project_id", _CANONICAL_PROJECT_ID),
        ("project_path", _CANONICAL_PROJECT_PATH),
        ("commit_sha", _CANONICAL_COMMIT_SHA),
        ("repository_path", spec.repository_path),
        ("requested_url", file_url),
        ("final_url", file_url),
        ("external_bytes_persisted", False),
        ("publication_authorized", False),
    )
    for field, expected in exact:
        observed = receipt[field]
        if type(observed) is not type(expected) or observed != expected:
            raise Eshm20SourceModelChildReceiptError(
                f"ESHM20 source-model child receipt identity drifted at {field}"
            )
    retrieved_at = receipt["retrieved_at"]
    if type(retrieved_at) is not str or not retrieved_at:
        raise Eshm20SourceModelChildReceiptError(
            "ESHM20 source-model child retrieval time is invalid"
        )
    byte_count = receipt["byte_count"]
    if (
        type(byte_count) is not int
        or isinstance(byte_count, bool)
        or byte_count <= 0
        or byte_count > _CANONICAL_MAX_ARTIFACT_BYTES
    ):
        raise Eshm20SourceModelChildReceiptError(
            "ESHM20 source-model child byte count is invalid"
        )
    if not _is_lower_sha256(receipt["sha256"]):
        raise Eshm20SourceModelChildReceiptError(
            "ESHM20 source-model child SHA-256 is invalid"
        )
    for field, value in receipt.items():
        if (field.endswith("_authorized") or field.endswith("_persisted")) and value is not False:
            raise Eshm20SourceModelChildReceiptError(
                f"ESHM20 source-model child receipt widened authority at {field}"
            )
    return {
        "repository_path": spec.repository_path,
        "retrieved_at": retrieved_at,
        "byte_count": byte_count,
        "sha256": receipt["sha256"],
        "project_id": _CANONICAL_PROJECT_ID,
        "project_path": _CANONICAL_PROJECT_PATH,
        "commit_sha": _CANONICAL_COMMIT_SHA,
        "parent_result_comment_id": _CANONICAL_PARENT_RESULT_COMMENT_ID,
        "external_bytes_persisted": False,
        "publication_authorized": False,
        "model_use_authorized": False,
    }


def _receipt_one(
    spec: ChildSpec,
    *,
    deadline: float,
    opener: Any,
    now: Any,
    monotonic: Any,
    receipt_builder: Any = _CANONICAL_RECEIPT_FROM_STREAM,
) -> dict[str, Any]:
    spec = _require_authorized_spec(spec)
    try:
        target = _CANONICAL_VALIDATE_TARGET(
            source_issue=_CANONICAL_SOURCE_ISSUE,
            dataset_id=_CANONICAL_DATASET_ID,
            project_id=_CANONICAL_PROJECT_ID,
            commit_sha=_CANONICAL_COMMIT_SHA,
            repository_path=spec.repository_path,
        )
    except EfehrReceiptError as exc:
        raise Eshm20SourceModelChildReceiptError(
            "trusted ESHM20 source-model child target is invalid"
        ) from exc

    file_url = _CANONICAL_RAW_FILE_API_URL(target)
    request = urllib.request.Request(
        file_url,
        headers={
            "Accept": "application/xml,text/xml,text/plain,application/octet-stream;q=0.8",
            "User-Agent": "OpenCatastrophe-ESHM20-source-model-child-receipts-v1",
        },
        method="GET",
    )
    try:
        with opener(request, timeout=_CANONICAL_REMAINING(deadline, monotonic)) as response:
            _CANONICAL_VALIDATE_EXACT_RESPONSE(response, file_url)
            _CANONICAL_DECLARED_LENGTH(response, _CANONICAL_MAX_ARTIFACT_BYTES)
            try:
                receipt = receipt_builder(
                    target,
                    _CANONICAL_DEADLINE_STREAM(
                        response,
                        deadline=deadline,
                        monotonic=monotonic,
                    ),
                    final_url=file_url,
                    retrieved_at=now(),
                    headers=getattr(response, "headers", None),
                    max_bytes=_CANONICAL_MAX_ARTIFACT_BYTES,
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
    return _project_core_receipt(receipt, spec=spec, file_url=file_url)


def _acquire_eshm20_source_model_child_receipts(
    *,
    opener: Any,
    now: Any,
    monotonic: Any,
    receipt_builder: Any = _CANONICAL_RECEIPT_FROM_STREAM,
) -> dict[str, Any]:
    """Private injectable helper for deterministic offline falsification tests."""

    children = _require_canonical_child_set()
    deadline = monotonic() + _CANONICAL_TOTAL_DEADLINE_SECONDS
    receipts = tuple(
        _receipt_one(
            spec,
            deadline=deadline,
            opener=opener,
            now=now,
            monotonic=monotonic,
            receipt_builder=receipt_builder,
        )
        for spec in children
    )
    final_retrieved_at = receipts[-1]["retrieved_at"]
    return {
        "schema_version": _CANONICAL_SCHEMA_VERSION,
        "operation_id": _CANONICAL_OPERATION_ID,
        "control_issue": _CANONICAL_CONTROL_ISSUE,
        "source_issue": _CANONICAL_SOURCE_ISSUE,
        "dataset_id": _CANONICAL_DATASET_ID,
        "provider_host": _CANONICAL_PROVIDER_HOST,
        "project_id": _CANONICAL_PROJECT_ID,
        "project_path": _CANONICAL_PROJECT_PATH,
        "commit_sha": _CANONICAL_COMMIT_SHA,
        "parent_request_comment_id": _CANONICAL_PARENT_REQUEST_COMMENT_ID,
        "parent_result_comment_id": _CANONICAL_PARENT_RESULT_COMMENT_ID,
        "parent_run_id": _CANONICAL_PARENT_RUN_ID,
        "parent_execution_sha": _CANONICAL_PARENT_EXECUTION_SHA,
        "parent_semantic_request_id": _CANONICAL_PARENT_SEMANTIC_REQUEST_ID,
        "parent_source_tree_byte_count": _CANONICAL_PARENT_SOURCE_TREE_BYTE_COUNT,
        "parent_source_tree_sha256": _CANONICAL_PARENT_SOURCE_TREE_SHA256,
        "child_count": _CANONICAL_EXPECTED_CHILD_COUNT,
        "child_paths_sha256": _CANONICAL_EXPECTED_PATHS_SHA256,
        "retrieved_at": final_retrieved_at,
        "receipts": list(receipts),
        "dependency_inventory_authorized": False,
        "dependency_receipt_authorized": False,
        "external_bytes_persisted": False,
        "publication_authorized": False,
        "model_use_authorized": False,
    }


def acquire_eshm20_source_model_child_receipts() -> dict[str, Any]:
    """Receipt the frozen 51-child set with code-owned production authority."""

    _require_production_identity()
    return _acquire_eshm20_source_model_child_receipts(
        opener=_CANONICAL_OPEN_FIXED,
        now=_CANONICAL_UTC_NOW,
        monotonic=_CANONICAL_MONOTONIC,
    )
