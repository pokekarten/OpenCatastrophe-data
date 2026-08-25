# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Acquire byte receipts for the three frozen ESRM20 v1.0 Greece source CSVs.

The targets are the project-186 source counterparts identified for the already
receipted project-269 Greece runtime exposure. This worker is deliberately
closed to those three immutable source paths and commit. It hashes provider
bytes in memory and never returns or persists the bytes themselves.

A passing receipt establishes source byte identity only. It does not establish
source-to-runtime row lineage, replacement-cost equivalence, taxonomy or CRS
semantics, benchmark agreement, validation/holdout status, publication rights,
or model-use authority.
"""

from __future__ import annotations

import hashlib
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

from scripts.acquire_efehr_gitlab_receipt import (
    EfehrAcquisitionError,
    TOTAL_DEADLINE_SECONDS,
    _header_value,
    _open_fixed,
    _read_bounded,
    _remaining,
    _validate_exact_response,
    utc_now,
)
from scripts.efehr_gitlab_receipt import PROVIDER_HOST, PROVIDER_ROOT

SCHEMA_VERSION = "oc-esrm20-greece-source-csv-receipts-v1"
CANONICAL_ISSUE = 285
RELATED_SOURCE_ISSUE = 282
PARENT_CONSUMER_ISSUE = 287
DATASET_ID = "efehr.esrm20.european-exposure-model.v1.0"
PROJECT_ID = 186
PROJECT_PATH = "efehr/esrm20_exposure"
RELEASE_TAG = "v1.0"
COMMIT_SHA = "900433ada80fbb424c0976c34d72eeef97bab1af"
MAX_RESULT_UTF8_BYTES = 20_000

_CANONICAL_SCHEMA_VERSION = SCHEMA_VERSION
_CANONICAL_ISSUE_VALUE = CANONICAL_ISSUE
_CANONICAL_RELATED_SOURCE_ISSUE = RELATED_SOURCE_ISSUE
_CANONICAL_PARENT_CONSUMER_ISSUE = PARENT_CONSUMER_ISSUE
_CANONICAL_DATASET_ID = DATASET_ID
_CANONICAL_PROJECT_ID = PROJECT_ID
_CANONICAL_PROJECT_PATH = PROJECT_PATH
_CANONICAL_RELEASE_TAG = RELEASE_TAG
_CANONICAL_COMMIT_SHA = COMMIT_SHA
_CANONICAL_TOTAL_DEADLINE_SECONDS = TOTAL_DEADLINE_SECONDS
_CANONICAL_OPEN_FIXED = _open_fixed
_CANONICAL_UTC_NOW = utc_now
_CANONICAL_MONOTONIC = time.monotonic

# path, provider Git blob SHA-1, provider tree byte count
_CANONICAL_TARGETS = (
    (
        "_exposure_models/Exposure_Model_Greece_Com.csv",
        "fd3e96c4121efb2e62bfb4b7a96b83b739888299",
        12_578_244,
    ),
    (
        "_exposure_models/Exposure_Model_Greece_Ind.csv",
        "240d739b5b58b4d5701702d06a36e612a8c5b659",
        4_600_971,
    ),
    (
        "_exposure_models/Exposure_Model_Greece_Res.csv",
        "c6bcd2df43d23009f4fea23be3934775ebabea0b",
        9_011_434,
    ),
)
TARGETS = _CANONICAL_TARGETS

_SHA1_RE = re.compile(r"^[0-9a-f]{40}$")
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_UTC_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,6})?Z$")
_RECEIPT_FIELDS = {
    "schema_version",
    "canonical_issue",
    "related_source_issue",
    "parent_consumer_issue",
    "dataset_id",
    "provider_host",
    "project_id",
    "project_path",
    "release_tag",
    "commit_sha",
    "repository_path",
    "git_blob_sha1",
    "expected_tree_byte_count",
    "retrieved_at",
    "byte_count",
    "sha256",
    "content_type",
    "etag",
    "provider_file_bytes_read",
    "provider_file_content_profiled",
    "source_runtime_lineage_verified",
    "replacement_cost_semantics_verified",
    "taxonomy_semantics_verified",
    "crs_semantics_verified",
    "external_bytes_persisted",
    "publication_authorized",
    "model_use_authorized",
}


class GreeceSourceCsvReceiptsError(RuntimeError):
    """Raised when the fixed Greece source receipt contract drifts."""


def _require_canonical_target() -> None:
    exact = (
        (SCHEMA_VERSION, _CANONICAL_SCHEMA_VERSION, "schema version"),
        (CANONICAL_ISSUE, _CANONICAL_ISSUE_VALUE, "canonical issue"),
        (RELATED_SOURCE_ISSUE, _CANONICAL_RELATED_SOURCE_ISSUE, "source issue"),
        (PARENT_CONSUMER_ISSUE, _CANONICAL_PARENT_CONSUMER_ISSUE, "parent consumer"),
        (DATASET_ID, _CANONICAL_DATASET_ID, "dataset id"),
        (PROJECT_ID, _CANONICAL_PROJECT_ID, "project id"),
        (PROJECT_PATH, _CANONICAL_PROJECT_PATH, "project path"),
        (RELEASE_TAG, _CANONICAL_RELEASE_TAG, "release tag"),
        (COMMIT_SHA, _CANONICAL_COMMIT_SHA, "commit sha"),
        (TARGETS, _CANONICAL_TARGETS, "target set"),
    )
    for observed, expected, label in exact:
        if type(observed) is not type(expected) or observed != expected:
            raise GreeceSourceCsvReceiptsError(
                f"frozen Greece source CSV {label} authority drifted"
            )
    if PROVIDER_HOST != "gitlab.seismo.ethz.ch":
        raise GreeceSourceCsvReceiptsError("EFEHR provider host authority drifted")
    if PROVIDER_ROOT != "https://gitlab.seismo.ethz.ch":
        raise GreeceSourceCsvReceiptsError("EFEHR provider root authority drifted")
    if len(TARGETS) != 3 or len({target[0] for target in TARGETS}) != 3:
        raise GreeceSourceCsvReceiptsError("Greece source CSV target cardinality drifted")
    for path, blob_sha1, tree_bytes in TARGETS:
        if type(path) is not str or not path.startswith("_exposure_models/Exposure_Model_Greece_"):
            raise GreeceSourceCsvReceiptsError("Greece source CSV path authority drifted")
        if type(blob_sha1) is not str or _SHA1_RE.fullmatch(blob_sha1) is None:
            raise GreeceSourceCsvReceiptsError("Greece source CSV blob authority drifted")
        if type(tree_bytes) is not int or isinstance(tree_bytes, bool) or tree_bytes < 1:
            raise GreeceSourceCsvReceiptsError("Greece source CSV tree size authority drifted")


def _require_production_transport_identity() -> None:
    identities = (
        (_open_fixed, _CANONICAL_OPEN_FIXED, "transport"),
        (utc_now, _CANONICAL_UTC_NOW, "UTC clock"),
        (time.monotonic, _CANONICAL_MONOTONIC, "monotonic clock"),
    )
    for observed, expected, label in identities:
        if observed is not expected:
            raise GreeceSourceCsvReceiptsError(
                f"frozen Greece source CSV production {label} drifted"
            )


def _raw_file_url(repository_path: str) -> str:
    _require_canonical_target()
    if repository_path not in {target[0] for target in TARGETS}:
        raise GreeceSourceCsvReceiptsError(
            "Greece source CSV path left the frozen dependency set"
        )
    encoded_path = urllib.parse.quote(repository_path, safe="")
    encoded_ref = urllib.parse.quote(_CANONICAL_COMMIT_SHA, safe="")
    return (
        f"{PROVIDER_ROOT}/api/v4/projects/{_CANONICAL_PROJECT_ID}/repository/files/"
        f"{encoded_path}/raw?ref={encoded_ref}"
    )


def _validate_header_value(value: object, *, field: str) -> str | None:
    if value is None:
        return None
    if type(value) is not str or len(value.encode("utf-8")) > 1024:
        raise GreeceSourceCsvReceiptsError(f"{field} is outside the bounded policy")
    if any(ord(character) < 32 or ord(character) == 127 for character in value):
        raise GreeceSourceCsvReceiptsError(f"{field} contains control characters")
    return value


def validate_receipt(
    value: object,
    *,
    expected_target: tuple[str, str, int],
) -> dict[str, Any]:
    _require_canonical_target()
    if expected_target not in TARGETS:
        raise GreeceSourceCsvReceiptsError("receipt target left frozen dependency set")
    if type(value) is not dict or set(value) != _RECEIPT_FIELDS:
        raise GreeceSourceCsvReceiptsError("Greece source CSV receipt fields drifted")

    path, blob_sha1, tree_bytes = expected_target
    exact = (
        ("schema_version", _CANONICAL_SCHEMA_VERSION),
        ("canonical_issue", _CANONICAL_ISSUE_VALUE),
        ("related_source_issue", _CANONICAL_RELATED_SOURCE_ISSUE),
        ("parent_consumer_issue", _CANONICAL_PARENT_CONSUMER_ISSUE),
        ("dataset_id", _CANONICAL_DATASET_ID),
        ("provider_host", "gitlab.seismo.ethz.ch"),
        ("project_id", _CANONICAL_PROJECT_ID),
        ("project_path", _CANONICAL_PROJECT_PATH),
        ("release_tag", _CANONICAL_RELEASE_TAG),
        ("commit_sha", _CANONICAL_COMMIT_SHA),
        ("repository_path", path),
        ("git_blob_sha1", blob_sha1),
        ("expected_tree_byte_count", tree_bytes),
        ("byte_count", tree_bytes),
        ("provider_file_bytes_read", True),
        ("provider_file_content_profiled", False),
        ("source_runtime_lineage_verified", False),
        ("replacement_cost_semantics_verified", False),
        ("taxonomy_semantics_verified", False),
        ("crs_semantics_verified", False),
        ("external_bytes_persisted", False),
        ("publication_authorized", False),
        ("model_use_authorized", False),
    )
    for field, expected in exact:
        observed = value[field]
        if type(observed) is not type(expected) or observed != expected:
            raise GreeceSourceCsvReceiptsError(
                f"Greece source CSV receipt drifted at {field}"
            )
    if type(value["retrieved_at"]) is not str or _UTC_RE.fullmatch(value["retrieved_at"]) is None:
        raise GreeceSourceCsvReceiptsError("Greece source CSV receipt timestamp is invalid")
    if type(value["sha256"]) is not str or _SHA256_RE.fullmatch(value["sha256"]) is None:
        raise GreeceSourceCsvReceiptsError("Greece source CSV receipt SHA-256 is invalid")
    _validate_header_value(value["content_type"], field="content_type")
    _validate_header_value(value["etag"], field="etag")
    return value


def validate_receipts(value: object) -> list[dict[str, Any]]:
    _require_canonical_target()
    if type(value) is not list or len(value) != len(TARGETS):
        raise GreeceSourceCsvReceiptsError("Greece source CSV receipt bundle cardinality drifted")
    return [
        validate_receipt(receipt, expected_target=target)
        for receipt, target in zip(value, TARGETS, strict=True)
    ]


def _acquire_for_test(*, opener: Any, now: Any, monotonic: Any) -> list[dict[str, Any]]:
    _require_canonical_target()
    deadline = monotonic() + _CANONICAL_TOTAL_DEADLINE_SECONDS
    receipts: list[dict[str, Any]] = []
    for repository_path, blob_sha1, expected_tree_bytes in TARGETS:
        url = _raw_file_url(repository_path)
        request = urllib.request.Request(
            url,
            headers={
                "Accept": "text/csv,application/octet-stream;q=0.5",
                "User-Agent": "OpenCatastrophe-EFEHR-Greece-source-3CSV-receipts-v1",
            },
            method="GET",
        )
        try:
            with opener(request, timeout=_remaining(deadline, monotonic)) as response:
                _validate_exact_response(response, url)
                retrieved_at = now()
                raw = _read_bounded(
                    response,
                    deadline=deadline,
                    maximum=expected_tree_bytes,
                    monotonic=monotonic,
                )
                content_type = _header_value(response, "Content-Type")
                etag = _header_value(response, "ETag")
        except (GreeceSourceCsvReceiptsError, EfehrAcquisitionError):
            raise
        except (OSError, urllib.error.URLError, urllib.error.HTTPError, TimeoutError) as exc:
            raise EfehrAcquisitionError(
                f"EFEHR Greece source CSV retrieval failed: {type(exc).__name__}"
            ) from exc

        if type(retrieved_at) is not str or _UTC_RE.fullmatch(retrieved_at) is None:
            raise GreeceSourceCsvReceiptsError(
                "Greece source CSV retrieval timestamp is invalid"
            )
        if len(raw) != expected_tree_bytes:
            raise GreeceSourceCsvReceiptsError(
                "Greece source CSV byte count does not match frozen provider tree metadata"
            )
        receipt = {
            "schema_version": _CANONICAL_SCHEMA_VERSION,
            "canonical_issue": _CANONICAL_ISSUE_VALUE,
            "related_source_issue": _CANONICAL_RELATED_SOURCE_ISSUE,
            "parent_consumer_issue": _CANONICAL_PARENT_CONSUMER_ISSUE,
            "dataset_id": _CANONICAL_DATASET_ID,
            "provider_host": "gitlab.seismo.ethz.ch",
            "project_id": _CANONICAL_PROJECT_ID,
            "project_path": _CANONICAL_PROJECT_PATH,
            "release_tag": _CANONICAL_RELEASE_TAG,
            "commit_sha": _CANONICAL_COMMIT_SHA,
            "repository_path": repository_path,
            "git_blob_sha1": blob_sha1,
            "expected_tree_byte_count": expected_tree_bytes,
            "retrieved_at": retrieved_at,
            "byte_count": len(raw),
            "sha256": hashlib.sha256(raw).hexdigest(),
            "content_type": content_type,
            "etag": etag,
            "provider_file_bytes_read": True,
            "provider_file_content_profiled": False,
            "source_runtime_lineage_verified": False,
            "replacement_cost_semantics_verified": False,
            "taxonomy_semantics_verified": False,
            "crs_semantics_verified": False,
            "external_bytes_persisted": False,
            "publication_authorized": False,
            "model_use_authorized": False,
        }
        receipts.append(validate_receipt(receipt, expected_target=(repository_path, blob_sha1, expected_tree_bytes)))
    return validate_receipts(receipts)


def acquire_receipts() -> list[dict[str, Any]]:
    """Acquire SHA-256 receipts for exactly the three frozen project-186 Greece CSVs."""
    _require_canonical_target()
    _require_production_transport_identity()
    return _acquire_for_test(
        opener=_CANONICAL_OPEN_FIXED,
        now=_CANONICAL_UTC_NOW,
        monotonic=_CANONICAL_MONOTONIC,
    )
