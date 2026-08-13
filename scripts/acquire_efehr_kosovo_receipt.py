# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Trusted acquisition worker for the one frozen ESRM20 Kosovo exposure object.

This module deliberately adds no provider-selection surface.  It reuses the
reviewed EFEHR transport and receipt primitives while fixing project, commit,
repository path, dataset identity, and operation identity in code.
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

SCHEMA_VERSION = "oc-efehr-trusted-acquisition-v1"
OPERATION_ID = "esrm20-kosovo-residential-exposure-v1"
SOURCE_ISSUE = 282
DATASET_ID = "efehr.esrm20.european-exposure-model.v1.0"
PROJECT_ID = 186
COMMIT_SHA = "900433ada80fbb424c0976c34d72eeef97bab1af"
REPOSITORY_PATH = "_exposure_models/Exposure_Model_Kosovo_Res.csv"


def acquire_kosovo_receipt(
    *,
    opener: Any | None = None,
    now: Any = utc_now,
    monotonic: Any = time.monotonic,
) -> dict[str, Any]:
    """Fetch only the frozen Kosovo residential exposure object and hash it.

    Provider bytes are streamed into the receipt primitive and are not returned
    or persisted by this worker.  The immutable commit is the execution
    authority; no mutable tag or branch is resolved here.
    """

    deadline = monotonic() + TOTAL_DEADLINE_SECONDS
    open_response = opener or _open_fixed
    try:
        target = validate_target(
            source_issue=SOURCE_ISSUE,
            dataset_id=DATASET_ID,
            project_id=PROJECT_ID,
            commit_sha=COMMIT_SHA,
            repository_path=REPOSITORY_PATH,
        )
    except EfehrReceiptError as exc:
        raise EfehrAcquisitionError(f"trusted EFEHR target is invalid: {exc}") from exc

    file_url = raw_file_api_url(target)
    request = urllib.request.Request(
        file_url,
        headers={
            "Accept": "text/csv,text/plain;q=0.9",
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
                raise EfehrAcquisitionError(f"EFEHR artifact receipt failed: {exc}") from exc
    except EfehrAcquisitionError:
        raise
    except (OSError, urllib.error.URLError, urllib.error.HTTPError, TimeoutError) as exc:
        raise EfehrAcquisitionError(
            f"EFEHR artifact retrieval failed: {type(exc).__name__}"
        ) from exc

    result = dict(core_receipt)
    result["schema_version"] = SCHEMA_VERSION
    result["operation_id"] = OPERATION_ID
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
