# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Acquire and profile only the frozen receipted ESHM20 root configuration.

The canonical trusted-main receipt already binds the exact root byte identity.
This worker re-materializes that one immutable root transiently, delegates exact
byte verification and first-order dependency interpretation to the reviewed
bridge, then discards provider bytes. No caller can select provider/project/ref,
repository path, parser, or dependency expansion.
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
        _open_fixed,
        _read_bounded,
        _remaining,
        _validate_exact_response,
    )
    from scripts.efehr_gitlab_receipt import (
        EfehrReceiptError,
        raw_file_api_url,
        validate_target,
    )
    from scripts import verify_eshm20_root_config_dependencies as bridge
except ModuleNotFoundError:  # pragma: no cover - direct script import path
    from acquire_efehr_gitlab_receipt import (
        EfehrAcquisitionError,
        TOTAL_DEADLINE_SECONDS,
        _open_fixed,
        _read_bounded,
        _remaining,
        _validate_exact_response,
    )
    from efehr_gitlab_receipt import (
        EfehrReceiptError,
        raw_file_api_url,
        validate_target,
    )
    import verify_eshm20_root_config_dependencies as bridge

ROOT_RECEIPT_COMMENT_ID = 5299422143
ROOT_RECEIPT_RUN_ID = 31853044582
ROOT_RECEIPT_EXECUTION_SHA = "0e28297e784e7cac590c068d66fde519c292abdb"


class Eshm20RootDependencyAcquisitionError(RuntimeError):
    """Raised when the one fixed receipted ESHM20 root cannot be safely profiled."""


def acquire_eshm20_root_dependencies(
    *, opener: Any | None = None, monotonic: Any = time.monotonic
) -> dict[str, Any]:
    """Re-materialize and profile only the frozen ESHM20 root configuration."""

    try:
        target = validate_target(
            source_issue=bridge.SOURCE_ISSUE,
            dataset_id=bridge.DATASET_ID,
            project_id=bridge.PROJECT_ID,
            commit_sha=bridge.COMMIT_SHA,
            repository_path=bridge.REPOSITORY_PATH,
        )
    except EfehrReceiptError as exc:
        raise Eshm20RootDependencyAcquisitionError(
            "trusted ESHM20 root dependency target is invalid"
        ) from exc

    file_url = raw_file_api_url(target)
    request = urllib.request.Request(
        file_url,
        headers={
            "Accept": "text/plain,text/x-ini;q=0.9,application/octet-stream;q=0.8",
            "User-Agent": "OpenCatastrophe-ESHM20-root-dependency-profile-v1",
        },
        method="GET",
    )
    deadline = monotonic() + TOTAL_DEADLINE_SECONDS
    open_response = opener or _open_fixed

    try:
        with open_response(request, timeout=_remaining(deadline, monotonic)) as response:
            _validate_exact_response(response, file_url)
            raw = _read_bounded(
                response,
                deadline=deadline,
                maximum=bridge.EXPECTED_BYTE_COUNT,
                monotonic=monotonic,
            )
    except Eshm20RootDependencyAcquisitionError:
        raise
    except EfehrAcquisitionError as exc:
        raise Eshm20RootDependencyAcquisitionError(
            "ESHM20 root dependency retrieval failed closed"
        ) from exc
    except (OSError, urllib.error.URLError, urllib.error.HTTPError, TimeoutError) as exc:
        raise Eshm20RootDependencyAcquisitionError(
            f"ESHM20 root dependency retrieval failed: {type(exc).__name__}"
        ) from exc

    try:
        result = bridge.extract_verified_root_dependencies(raw)
    except bridge.VerifiedRootConfigError as exc:
        raise Eshm20RootDependencyAcquisitionError(
            "ESHM20 root dependency verification failed closed"
        ) from exc

    if (
        result.get("external_bytes_persisted") is not False
        or result.get("publication_authorized") is not False
    ):
        raise Eshm20RootDependencyAcquisitionError(
            "verified ESHM20 root dependency result widened its authority ceiling"
        )

    return {
        **result,
        "root_receipt_comment_id": ROOT_RECEIPT_COMMENT_ID,
        "root_receipt_run_id": ROOT_RECEIPT_RUN_ID,
        "root_receipt_execution_sha": ROOT_RECEIPT_EXECUTION_SHA,
        "dependency_inventory_authorized": False,
    }
