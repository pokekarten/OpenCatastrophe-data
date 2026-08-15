# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Profile only the exact receipted ESHM20 site-model CSV.

The worker is intentionally descriptive rather than interpretive. It verifies
byte identity before decoding, then emits bounded CSV structure and numeric
range metadata. Header names or numeric ranges never authorize CRS, coordinate,
site-response, admission, publication, or model-use semantics.
"""

from __future__ import annotations

import csv
import hashlib
import io
import time
import urllib.error
import urllib.request
from decimal import Decimal, InvalidOperation
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
except ModuleNotFoundError:  # pragma: no cover - direct script import path
    from acquire_efehr_gitlab_receipt import (  # type: ignore[no-redef]
        EfehrAcquisitionError,
        TOTAL_DEADLINE_SECONDS,
        _open_fixed,
        _read_bounded,
        _remaining,
        _validate_exact_response,
    )
    from efehr_gitlab_receipt import (  # type: ignore[no-redef]
        EfehrReceiptError,
        raw_file_api_url,
        validate_target,
    )

SCHEMA_VERSION = "oc-eshm20-site-model-structural-profile-v1"
SOURCE_ISSUE = 281
CONTROL_ISSUE = 372
DATASET_ID = "efehr.eshm20"
PROJECT_ID = 197
PROJECT_PATH = "efehr/eshm20"
COMMIT_SHA = "fbd334de68f85d72669f73fc5a314a113db67317"
REPOSITORY_PATH = (
    "oq_computational/oq_configuration_eshm20_v12e_region_main/"
    "eshm20_site_model_v06d.csv"
)
EXPECTED_BYTE_COUNT = 3_873_324
EXPECTED_SHA256 = "d4d95f3e482a0361a90d1b0796545eaf075d0e212d66d025f975973497b29529"
ROOT_DEPENDENCY_RESULT_COMMENT_ID = 5301726249
ROOT_DEPENDENCY_SECTION = "site_params"
ROOT_DEPENDENCY_OPTION = "site_model_file"
FIRST_ORDER_RECEIPT_REQUEST_COMMENT_ID = 5301857400
FIRST_ORDER_RECEIPT_RESULT_COMMENT_ID = 5301858821
FIRST_ORDER_RECEIPT_RUN_ID = 31880089623
FIRST_ORDER_RECEIPT_EXECUTION_SHA = "ab66e3e4c58c9b8f18587f1a8a51cf67cf9851b1"
INVENTORY_RECEIPT_COMMENT_ID = 5290449064
MAX_COLUMNS = 128
MAX_HEADER_UTF8_BYTES = 512


class Eshm20SiteModelProfileError(RuntimeError):
    """Raised when the fixed site-model profile cannot close safely."""


def _verify_payload_identity(payload: bytes) -> str:
    if type(payload) is not bytes:
        raise Eshm20SiteModelProfileError("site-model payload must be immutable bytes")
    if len(payload) != EXPECTED_BYTE_COUNT:
        raise Eshm20SiteModelProfileError(
            "site-model byte count does not match the trusted receipt"
        )
    observed_sha256 = hashlib.sha256(payload).hexdigest()
    if observed_sha256 != EXPECTED_SHA256:
        raise Eshm20SiteModelProfileError(
            "site-model SHA-256 does not match the trusted receipt"
        )
    return observed_sha256


def _canonical_decimal(value: Decimal) -> str:
    if value == 0:
        return "0"
    return str(value.normalize())


def _profile_csv_text(text: str) -> dict[str, Any]:
    if "\x00" in text:
        raise Eshm20SiteModelProfileError("verified site-model CSV contains NUL bytes")

    reader = csv.reader(io.StringIO(text, newline=""), strict=True)
    try:
        header = next(reader)
    except StopIteration as exc:
        raise Eshm20SiteModelProfileError("verified site-model CSV is empty") from exc
    except csv.Error as exc:
        raise Eshm20SiteModelProfileError("verified site-model CSV header is malformed") from exc

    if not (1 <= len(header) <= MAX_COLUMNS):
        raise Eshm20SiteModelProfileError("site-model CSV column count is outside bounded policy")
    if any(
        type(name) is not str
        or not name.strip()
        or len(name.encode("utf-8")) > MAX_HEADER_UTF8_BYTES
        for name in header
    ):
        raise Eshm20SiteModelProfileError("site-model CSV contains an empty or oversized header")
    if len(set(header)) != len(header):
        raise Eshm20SiteModelProfileError("site-model CSV contains duplicate headers")

    profiles = [
        {
            "name": name,
            "nonempty_count": 0,
            "numeric_count": 0,
            "numeric_min": None,
            "numeric_max": None,
        }
        for name in header
    ]
    minima: list[Decimal | None] = [None] * len(header)
    maxima: list[Decimal | None] = [None] * len(header)
    row_count = 0

    try:
        for row in reader:
            if len(row) != len(header):
                raise Eshm20SiteModelProfileError(
                    "site-model CSV row width differs from the header"
                )
            row_count += 1
            for index, raw_value in enumerate(row):
                value = raw_value.strip()
                if not value:
                    continue
                profiles[index]["nonempty_count"] += 1
                try:
                    numeric = Decimal(value)
                except InvalidOperation:
                    continue
                if not numeric.is_finite():
                    raise Eshm20SiteModelProfileError(
                        "site-model CSV contains a non-finite numeric token"
                    )
                profiles[index]["numeric_count"] += 1
                if minima[index] is None or numeric < minima[index]:
                    minima[index] = numeric
                if maxima[index] is None or numeric > maxima[index]:
                    maxima[index] = numeric
    except csv.Error as exc:
        raise Eshm20SiteModelProfileError("verified site-model CSV is malformed") from exc

    if row_count < 1:
        raise Eshm20SiteModelProfileError("verified site-model CSV contains no data rows")

    for index, profile in enumerate(profiles):
        minimum = minima[index]
        maximum = maxima[index]
        if minimum is not None and maximum is not None:
            profile["numeric_min"] = _canonical_decimal(minimum)
            profile["numeric_max"] = _canonical_decimal(maximum)

    return {
        "header": list(header),
        "column_count": len(header),
        "data_row_count": row_count,
        "columns": profiles,
    }


def extract_verified_site_model_profile(payload: bytes) -> dict[str, Any]:
    """Verify the exact receipt before decoding and descriptive CSV profiling."""

    observed_sha256 = _verify_payload_identity(payload)
    utf8_bom_present = payload.startswith(b"\xef\xbb\xbf")
    try:
        text = payload.decode("utf-8-sig", errors="strict")
    except UnicodeDecodeError as exc:
        raise Eshm20SiteModelProfileError(
            "verified site-model payload is not strict UTF-8"
        ) from exc

    profile = _profile_csv_text(text)
    return {
        "schema_version": SCHEMA_VERSION,
        "source_issue": SOURCE_ISSUE,
        "control_issue": CONTROL_ISSUE,
        "dataset_id": DATASET_ID,
        "project_id": PROJECT_ID,
        "project_path": PROJECT_PATH,
        "commit_sha": COMMIT_SHA,
        "repository_path": REPOSITORY_PATH,
        "byte_count": len(payload),
        "sha256": observed_sha256,
        "utf8_bom_present": utf8_bom_present,
        "inventory_receipt_comment_id": INVENTORY_RECEIPT_COMMENT_ID,
        "root_dependency_result_comment_id": ROOT_DEPENDENCY_RESULT_COMMENT_ID,
        "root_dependency_section": ROOT_DEPENDENCY_SECTION,
        "root_dependency_option": ROOT_DEPENDENCY_OPTION,
        "first_order_receipt_request_comment_id": FIRST_ORDER_RECEIPT_REQUEST_COMMENT_ID,
        "first_order_receipt_result_comment_id": FIRST_ORDER_RECEIPT_RESULT_COMMENT_ID,
        "first_order_receipt_run_id": FIRST_ORDER_RECEIPT_RUN_ID,
        "first_order_receipt_execution_sha": FIRST_ORDER_RECEIPT_EXECUTION_SHA,
        "profile": profile,
        "schema_interpretation_authorized": False,
        "crs_authorized": False,
        "coordinate_semantics_authorized": False,
        "site_response_authorized": False,
        "external_bytes_persisted": False,
        "publication_authorized": False,
        "model_use_authorized": False,
    }


def acquire_eshm20_site_model_profile(
    *, opener: Any | None = None, monotonic: Any = time.monotonic
) -> dict[str, Any]:
    """Re-materialize and structurally profile only the fixed receipted site CSV."""

    try:
        target = validate_target(
            source_issue=SOURCE_ISSUE,
            dataset_id=DATASET_ID,
            project_id=PROJECT_ID,
            commit_sha=COMMIT_SHA,
            repository_path=REPOSITORY_PATH,
        )
    except EfehrReceiptError as exc:
        raise Eshm20SiteModelProfileError("trusted ESHM20 site-model target is invalid") from exc

    file_url = raw_file_api_url(target)
    request = urllib.request.Request(
        file_url,
        headers={
            "Accept": "text/csv,text/plain;q=0.9,application/octet-stream;q=0.8",
            "User-Agent": "OpenCatastrophe-ESHM20-site-model-structural-profile-v1",
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
                maximum=EXPECTED_BYTE_COUNT,
                monotonic=monotonic,
            )
    except Eshm20SiteModelProfileError:
        raise
    except EfehrAcquisitionError as exc:
        raise Eshm20SiteModelProfileError("ESHM20 site-model retrieval failed closed") from exc
    except (OSError, urllib.error.URLError, urllib.error.HTTPError, TimeoutError) as exc:
        raise Eshm20SiteModelProfileError(
            f"ESHM20 site-model retrieval failed: {type(exc).__name__}"
        ) from exc

    result = extract_verified_site_model_profile(raw)
    ceilings = (
        "schema_interpretation_authorized",
        "crs_authorized",
        "coordinate_semantics_authorized",
        "site_response_authorized",
        "external_bytes_persisted",
        "publication_authorized",
        "model_use_authorized",
    )
    if any(result.get(field) is not False for field in ceilings):
        raise Eshm20SiteModelProfileError(
            "verified ESHM20 site-model result widened its authority ceiling"
        )
    return result


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(
        "This worker is library-only until separately reviewed trusted-main action wiring exists."
    )
