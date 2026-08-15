# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Receipt only the three ESHM20 files proven by the exact root config.

The trusted-main #353 root dependency profile is the selection authority for
these paths. This module deliberately exposes no caller-controlled project,
commit, path, dependency role, or provider selector. Provider bytes are streamed
into the existing receipt primitive and are never returned or persisted.
"""

from __future__ import annotations

import time
import urllib.error
import urllib.request
from dataclasses import dataclass
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
        MAX_FILE_BYTES,
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
        MAX_FILE_BYTES,
        raw_file_api_url,
        receipt_from_stream,
        validate_target,
    )

SCHEMA_VERSION = "oc-efehr-eshm20-first-order-receipt-v1"
SOURCE_ISSUE = 281
DATASET_ID = "efehr.eshm20"
PROJECT_ID = 197
COMMIT_SHA = "fbd334de68f85d72669f73fc5a314a113db67317"
ROOT_REPOSITORY_PATH = (
    "oq_computational/oq_configuration_eshm20_v12e_region_main/"
    "config_eshm20_v12e_main_region.ini"
)
DEPENDENCY_PREFIX = "oq_computational/oq_configuration_eshm20_v12e_region_main/"

# Canonical trusted-main selection evidence. This result proves only that the
# exact root names these three first-order paths; it is not their byte receipt.
DISCOVERY_ISSUE = 353
DISCOVERY_REQUEST_COMMENT_ID = 5301725105
DISCOVERY_RESULT_COMMENT_ID = 5301726249
DISCOVERY_RUN_ID = 31878511737
DISCOVERY_EXECUTION_SHA = "bd146a19fa4a1dc85b616288ec6d24946336a483"


@dataclass(frozen=True)
class _DependencySpec:
    operation_id: str
    scientific_role: str
    repository_path: str
    parent_section: str
    parent_option: str
    accept: str


_SITE_MODEL = _DependencySpec(
    operation_id="eshm20-site-model-v06d-receipt-v1",
    scientific_role="site_model",
    repository_path=DEPENDENCY_PREFIX + "eshm20_site_model_v06d.csv",
    parent_section="site_params",
    parent_option="site_model_file",
    accept="text/csv,text/plain;q=0.9,application/octet-stream;q=0.8",
)
_GMPE_LOGIC_TREE = _DependencySpec(
    operation_id="eshm20-gmpe-complete-logic-tree-5br-receipt-v1",
    scientific_role="ground_motion_logic_tree",
    repository_path=DEPENDENCY_PREFIX + "gmpe_complete_logic_tree_5br.xml",
    parent_section="calculation",
    parent_option="gsim_logic_tree_file",
    accept="application/xml,text/xml;q=0.9,text/plain;q=0.8,application/octet-stream;q=0.7",
)
_SOURCE_MODEL_LOGIC_TREE = _DependencySpec(
    operation_id="eshm20-source-model-logic-tree-v12e-receipt-v1",
    scientific_role="source_model_logic_tree",
    repository_path=DEPENDENCY_PREFIX + "source_model_logic_tree_eshm20_model_v12e.xml",
    parent_section="calculation",
    parent_option="source_model_logic_tree_file",
    accept="application/xml,text/xml;q=0.9,text/plain;q=0.8,application/octet-stream;q=0.7",
)


def _acquire_dependency_receipt(
    spec: _DependencySpec,
    *,
    opener: Any | None,
    now: Any,
    monotonic: Any,
) -> dict[str, Any]:
    if type(spec) is not _DependencySpec or (
        spec is not _SITE_MODEL
        and spec is not _GMPE_LOGIC_TREE
        and spec is not _SOURCE_MODEL_LOGIC_TREE
    ):
        raise EfehrAcquisitionError(
            "ESHM20 dependency spec is not an authorized first-order target"
        )

    deadline = monotonic() + TOTAL_DEADLINE_SECONDS
    open_response = opener or _open_fixed
    try:
        target = validate_target(
            source_issue=SOURCE_ISSUE,
            dataset_id=DATASET_ID,
            project_id=PROJECT_ID,
            commit_sha=COMMIT_SHA,
            repository_path=spec.repository_path,
        )
    except EfehrReceiptError as exc:
        raise EfehrAcquisitionError(f"trusted EFEHR dependency target is invalid: {exc}") from exc

    file_url = raw_file_api_url(target)
    request = urllib.request.Request(
        file_url,
        headers={
            "Accept": spec.accept,
            "User-Agent": "OpenCatastrophe-EFEHR-acquisition-v1",
        },
        method="GET",
    )

    try:
        with open_response(request, timeout=_remaining(deadline, monotonic)) as response:
            _validate_exact_response(response, file_url)
            _declared_length(response, MAX_FILE_BYTES)
            retrieved_at = now()
            try:
                core_receipt = receipt_from_stream(
                    target,
                    _DeadlineStream(
                        response,
                        deadline=deadline,
                        monotonic=monotonic,
                    ),
                    final_url=file_url,
                    retrieved_at=retrieved_at,
                    headers=getattr(response, "headers", None),
                    max_bytes=MAX_FILE_BYTES,
                )
            except EfehrReceiptError as exc:
                raise EfehrAcquisitionError(f"EFEHR dependency receipt failed: {exc}") from exc
    except EfehrAcquisitionError:
        raise
    except (OSError, urllib.error.URLError, urllib.error.HTTPError, TimeoutError) as exc:
        raise EfehrAcquisitionError(
            f"EFEHR dependency retrieval failed: {type(exc).__name__}"
        ) from exc

    if core_receipt.get("external_bytes_persisted") is not False:
        raise EfehrAcquisitionError("dependency receipt widened byte-persistence authority")
    if core_receipt.get("publication_authorized") is not False:
        raise EfehrAcquisitionError("dependency receipt widened publication authority")

    return {
        "schema_version": SCHEMA_VERSION,
        "operation_id": spec.operation_id,
        "scientific_role": spec.scientific_role,
        "source_issue": core_receipt["source_issue"],
        "dataset_id": core_receipt["dataset_id"],
        "provider_host": core_receipt["provider_host"],
        "project_id": core_receipt["project_id"],
        "project_path": core_receipt["project_path"],
        "commit_sha": core_receipt["commit_sha"],
        "repository_path": core_receipt["repository_path"],
        "requested_url": core_receipt["requested_url"],
        "final_url": core_receipt["final_url"],
        "retrieved_at": core_receipt["retrieved_at"],
        "byte_count": core_receipt["byte_count"],
        "sha256": core_receipt["sha256"],
        "content_type": core_receipt["content_type"],
        "etag": core_receipt["etag"],
        "parent_repository_path": ROOT_REPOSITORY_PATH,
        "parent_section": spec.parent_section,
        "parent_option": spec.parent_option,
        "discovery_issue": DISCOVERY_ISSUE,
        "discovery_request_comment_id": DISCOVERY_REQUEST_COMMENT_ID,
        "discovery_result_comment_id": DISCOVERY_RESULT_COMMENT_ID,
        "discovery_run_id": DISCOVERY_RUN_ID,
        "discovery_execution_sha": DISCOVERY_EXECUTION_SHA,
        "dependency_inventory_authorized": False,
        "external_bytes_persisted": False,
        "publication_authorized": False,
    }


def acquire_eshm20_site_model_receipt(
    *,
    opener: Any | None = None,
    now: Any = utc_now,
    monotonic: Any = time.monotonic,
) -> dict[str, Any]:
    """Receipt only the exact site-model CSV named by the trusted root."""

    return _acquire_dependency_receipt(
        _SITE_MODEL,
        opener=opener,
        now=now,
        monotonic=monotonic,
    )


def acquire_eshm20_gmpe_logic_tree_receipt(
    *,
    opener: Any | None = None,
    now: Any = utc_now,
    monotonic: Any = time.monotonic,
) -> dict[str, Any]:
    """Receipt only the exact GMPE/GMM logic-tree XML named by the trusted root."""

    return _acquire_dependency_receipt(
        _GMPE_LOGIC_TREE,
        opener=opener,
        now=now,
        monotonic=monotonic,
    )


def acquire_eshm20_source_model_logic_tree_receipt(
    *,
    opener: Any | None = None,
    now: Any = utc_now,
    monotonic: Any = time.monotonic,
) -> dict[str, Any]:
    """Receipt only the exact source-model logic-tree XML named by the root."""

    return _acquire_dependency_receipt(
        _SOURCE_MODEL_LOGIC_TREE,
        opener=opener,
        now=now,
        monotonic=monotonic,
    )
