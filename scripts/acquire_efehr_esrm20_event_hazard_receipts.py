# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Trusted receipt workers for frozen ESRM20 v1.0 event-hazard inputs.

The public entry points expose no provider-target selector. Project, commit,
repository path, dataset identity and operation identity are fixed in trusted
code. A successful receipt proves byte identity only; dependency closure and
scientific interpretation remain post-receipt #281 work.
"""

from __future__ import annotations

import time
import urllib.error
import urllib.request
from typing import Any

try:
    from scripts.acquire_efehr_gitlab_receipt import (
        EfehrAcquisitionError,
        TOTAL_DEADLINE_SECONDS,
        _DeadlineStream,
        _declared_length,
        _open_fixed,
        _remaining,
        _validate_exact_response,
        utc_now,
    )
    from scripts.efehr_gitlab_receipt import (
        EfehrReceiptError,
        raw_file_api_url,
        receipt_from_stream,
        validate_target,
    )
except ModuleNotFoundError:  # pragma: no cover - direct script import path
    from acquire_efehr_gitlab_receipt import (
        EfehrAcquisitionError,
        TOTAL_DEADLINE_SECONDS,
        _DeadlineStream,
        _declared_length,
        _open_fixed,
        _remaining,
        _validate_exact_response,
        utc_now,
    )
    from efehr_gitlab_receipt import (
        EfehrReceiptError,
        raw_file_api_url,
        receipt_from_stream,
        validate_target,
    )

SCHEMA_VERSION = "oc-efehr-trusted-acquisition-v1"
SOURCE_ISSUE = 281
DATASET_ID = "efehr.esrm20.risk-inputs.v1.0"
PROJECT_ID = 269
COMMIT_SHA = "05f83bbc9df81d02ee8ddb1801d9d781355ce783"
GROUP1_REPOSITORY_PATH = "Configuration_files/config_event_hazard_Group1.ini"
GROUP2_REPOSITORY_PATH = "Configuration_files/config_event_hazard_Group2.ini"
GSIM_LOGIC_TREE_REPOSITORY_PATH = "Hazard/gmpe_logic_tree_5br_slope_geology.xml"
SOURCE_MODEL_LOGIC_TREE_REPOSITORY_PATH = (
    "Hazard/source_model_logic_tree_eshm20_v12e_collapsed_risk_model.xml"
)
GROUP1_OPERATION_ID = "esrm20-event-hazard-group1-config-v1"
GROUP2_OPERATION_ID = "esrm20-event-hazard-group2-config-v1"
GSIM_LOGIC_TREE_OPERATION_ID = "esrm20-event-hazard-gsim-logic-tree-v1"
SOURCE_MODEL_LOGIC_TREE_OPERATION_ID = "esrm20-event-hazard-collapsed-source-logic-tree-v1"
MAX_CONFIG_BYTES = 1024 * 1024


def _acquire_config_receipt(
    *,
    repository_path: str,
    operation_id: str,
    opener: Any | None,
    now: Any,
    monotonic: Any,
) -> dict[str, Any]:
    deadline = monotonic() + TOTAL_DEADLINE_SECONDS
    open_response = opener or _open_fixed
    try:
        target = validate_target(
            source_issue=SOURCE_ISSUE,
            dataset_id=DATASET_ID,
            project_id=PROJECT_ID,
            commit_sha=COMMIT_SHA,
            repository_path=repository_path,
        )
    except EfehrReceiptError as exc:
        raise EfehrAcquisitionError(f"trusted EFEHR target is invalid: {exc}") from exc

    file_url = raw_file_api_url(target)
    request = urllib.request.Request(
        file_url,
        headers={
            "Accept": "application/xml,text/xml;q=0.9,text/plain;q=0.8,text/x-ini;q=0.7,application/octet-stream;q=0.6",
            "User-Agent": "OpenCatastrophe-EFEHR-acquisition-v1",
        },
        method="GET",
    )
    try:
        with open_response(request, timeout=_remaining(deadline, monotonic)) as response:
            _validate_exact_response(response, file_url)
            _declared_length(response, MAX_CONFIG_BYTES)
            retrieved_at = now()
            try:
                core_receipt = receipt_from_stream(
                    target,
                    _DeadlineStream(response, deadline=deadline, monotonic=monotonic),
                    final_url=file_url,
                    retrieved_at=retrieved_at,
                    headers=getattr(response, "headers", None),
                    max_bytes=MAX_CONFIG_BYTES,
                )
            except EfehrReceiptError as exc:
                raise EfehrAcquisitionError(f"EFEHR artifact receipt failed: {exc}") from exc
    except EfehrAcquisitionError:
        raise
    except (OSError, urllib.error.URLError, urllib.error.HTTPError, TimeoutError) as exc:
        raise EfehrAcquisitionError(
            f"EFEHR artifact retrieval failed: {type(exc).__name__}"
        ) from exc

    result = dict(core_receipt)
    result["schema_version"] = SCHEMA_VERSION
    result["operation_id"] = operation_id
    return {
        "schema_version": result["schema_version"],
        "operation_id": result["operation_id"],
        "source_issue": result["source_issue"],
        "dataset_id": result["dataset_id"],
        "provider_host": result["provider_host"],
        "project_id": result["project_id"],
        "project_path": result["project_path"],
        "commit_sha": result["commit_sha"],
        "repository_path": result["repository_path"],
        "requested_url": result["requested_url"],
        "final_url": result["final_url"],
        "retrieved_at": result["retrieved_at"],
        "byte_count": result["byte_count"],
        "sha256": result["sha256"],
        "content_type": result["content_type"],
        "etag": result["etag"],
        "external_bytes_persisted": result["external_bytes_persisted"],
        "publication_authorized": result["publication_authorized"],
    }


def acquire_event_hazard_group1_receipt(
    *, opener: Any | None = None, now: Any = utc_now, monotonic: Any = time.monotonic
) -> dict[str, Any]:
    """Receipt only the frozen ESRM20 v1.0 Group1 event-hazard INI."""
    return _acquire_config_receipt(
        repository_path=GROUP1_REPOSITORY_PATH,
        operation_id=GROUP1_OPERATION_ID,
        opener=opener,
        now=now,
        monotonic=monotonic,
    )


def acquire_event_hazard_group2_receipt(
    *, opener: Any | None = None, now: Any = utc_now, monotonic: Any = time.monotonic
) -> dict[str, Any]:
    """Receipt only the frozen ESRM20 v1.0 Group2 event-hazard INI."""
    return _acquire_config_receipt(
        repository_path=GROUP2_REPOSITORY_PATH,
        operation_id=GROUP2_OPERATION_ID,
        opener=opener,
        now=now,
        monotonic=monotonic,
    )


def acquire_event_hazard_gsim_logic_tree_receipt(
    *, opener: Any | None = None, now: Any = utc_now, monotonic: Any = time.monotonic
) -> dict[str, Any]:
    """Receipt only the Group1/Group2 source-derived ESRM20 GSIM logic tree."""
    return _acquire_config_receipt(
        repository_path=GSIM_LOGIC_TREE_REPOSITORY_PATH,
        operation_id=GSIM_LOGIC_TREE_OPERATION_ID,
        opener=opener,
        now=now,
        monotonic=monotonic,
    )


def acquire_event_hazard_source_model_logic_tree_receipt(
    *, opener: Any | None = None, now: Any = utc_now, monotonic: Any = time.monotonic
) -> dict[str, Any]:
    """Receipt only the source-derived collapsed ESRM20 source-model logic tree."""
    return _acquire_config_receipt(
        repository_path=SOURCE_MODEL_LOGIC_TREE_REPOSITORY_PATH,
        operation_id=SOURCE_MODEL_LOGIC_TREE_OPERATION_ID,
        opener=opener,
        now=now,
        monotonic=monotonic,
    )
