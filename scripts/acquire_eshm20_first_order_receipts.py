# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Receipt exactly the three ESHM20 first-order dependencies proven by #353.

The canonical trusted-main #353 result selected exactly three repository paths
from the exact receipted ESHM20 root configuration. This worker fixes that
three-file set in code, streams each immutable provider object only into the
reviewed receipt primitive, and returns bounded receipt metadata. Provider
bytes are never returned or persisted and callers cannot select provider,
project, ref, path, file set, parser, or dependency expansion.
"""

from __future__ import annotations

from dataclasses import dataclass
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
        TOTAL_DEADLINE_SECONDS,
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

SCHEMA_VERSION = "oc-eshm20-first-order-receipt-set-v1"
OPERATION_ID = "eshm20-first-order-dependencies-v12e-region-main-v1"
CONTROL_ISSUE = 361
SOURCE_ISSUE = 281
DATASET_ID = "efehr.eshm20"
PROJECT_ID = 197
PROJECT_PATH = "efehr/eshm20"
COMMIT_SHA = "fbd334de68f85d72669f73fc5a314a113db67317"
SELECTION_REQUEST_COMMENT_ID = 5301725105
SELECTION_RESULT_COMMENT_ID = 5301726249
SELECTION_RUN_ID = 31878511737
SELECTION_EXECUTION_SHA = "bd146a19fa4a1dc85b616288ec6d24946336a483"
MAX_ARTIFACT_BYTES = MAX_FILE_BYTES


@dataclass(frozen=True)
class DependencySpec:
    repository_path: str
    parent_section: str
    parent_option: str


DEPENDENCIES: tuple[DependencySpec, ...] = (
    DependencySpec(
        repository_path=(
            "oq_computational/oq_configuration_eshm20_v12e_region_main/"
            "eshm20_site_model_v06d.csv"
        ),
        parent_section="site_params",
        parent_option="site_model_file",
    ),
    DependencySpec(
        repository_path=(
            "oq_computational/oq_configuration_eshm20_v12e_region_main/"
            "gmpe_complete_logic_tree_5br.xml"
        ),
        parent_section="calculation",
        parent_option="gsim_logic_tree_file",
    ),
    DependencySpec(
        repository_path=(
            "oq_computational/oq_configuration_eshm20_v12e_region_main/"
            "source_model_logic_tree_eshm20_model_v12e.xml"
        ),
        parent_section="calculation",
        parent_option="source_model_logic_tree_file",
    ),
)


class Eshm20FirstOrderReceiptError(RuntimeError):
    """Raised when the fixed three-file ESHM20 receipt set cannot close safely."""


def _receipt_one(
    spec: DependencySpec,
    *,
    deadline: float,
    opener: Any,
    now: Any,
    monotonic: Any,
) -> dict[str, Any]:
    try:
        target = validate_target(
            source_issue=SOURCE_ISSUE,
            dataset_id=DATASET_ID,
            project_id=PROJECT_ID,
            commit_sha=COMMIT_SHA,
            repository_path=spec.repository_path,
        )
    except EfehrReceiptError as exc:
        raise Eshm20FirstOrderReceiptError(
            "trusted ESHM20 first-order target is invalid"
        ) from exc

    file_url = raw_file_api_url(target)
    request = urllib.request.Request(
        file_url,
        headers={
            "Accept": "text/plain,application/xml,text/xml,text/csv,application/octet-stream;q=0.8",
            "User-Agent": "OpenCatastrophe-ESHM20-first-order-receipts-v1",
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
                raise Eshm20FirstOrderReceiptError(
                    "ESHM20 first-order artifact receipt failed closed"
                ) from exc
    except Eshm20FirstOrderReceiptError:
        raise
    except EfehrAcquisitionError as exc:
        raise Eshm20FirstOrderReceiptError(
            "ESHM20 first-order artifact retrieval failed closed"
        ) from exc
    except (OSError, urllib.error.URLError, urllib.error.HTTPError, TimeoutError) as exc:
        raise Eshm20FirstOrderReceiptError(
            f"ESHM20 first-order artifact retrieval failed: {type(exc).__name__}"
        ) from exc

    if (
        receipt.get("external_bytes_persisted") is not False
        or receipt.get("publication_authorized") is not False
    ):
        raise Eshm20FirstOrderReceiptError(
            "ESHM20 first-order artifact receipt widened its authority ceiling"
        )
    return {
        **receipt,
        "parent_result_comment_id": SELECTION_RESULT_COMMENT_ID,
        "parent_section": spec.parent_section,
        "parent_option": spec.parent_option,
    }


def acquire_eshm20_first_order_receipts(
    *,
    opener: Any | None = None,
    now: Any = utc_now,
    monotonic: Any = time.monotonic,
) -> dict[str, Any]:
    """Receipt only the frozen #353 first-order dependency set.

    The operation is atomic from the caller's perspective: a failure while
    retrieving any one member raises and returns no partial receipt object.
    """

    if tuple(spec.repository_path for spec in DEPENDENCIES) != tuple(
        sorted(spec.repository_path for spec in DEPENDENCIES)
    ):
        raise Eshm20FirstOrderReceiptError(
            "frozen ESHM20 first-order dependency set is not canonically ordered"
        )
    if len(DEPENDENCIES) != 3 or len({spec.repository_path for spec in DEPENDENCIES}) != 3:
        raise Eshm20FirstOrderReceiptError(
            "frozen ESHM20 first-order dependency set identity is invalid"
        )

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
        for spec in DEPENDENCIES
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
        "selection_request_comment_id": SELECTION_REQUEST_COMMENT_ID,
        "selection_result_comment_id": SELECTION_RESULT_COMMENT_ID,
        "selection_run_id": SELECTION_RUN_ID,
        "selection_execution_sha": SELECTION_EXECUTION_SHA,
        "retrieved_at": final_retrieved_at,
        "receipts": list(receipts),
        "dependency_inventory_authorized": False,
        "external_bytes_persisted": False,
        "publication_authorized": False,
    }
