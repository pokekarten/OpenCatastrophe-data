# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Profile only the canonical receipted ESHM20 site-model CSV.

The worker is intentionally descriptive rather than interpretive. It reuses the
code-owned #361 first-order site target as the only network capability, verifies
the exact receipted bytes before decoding, and emits bounded structural evidence.
No field name, value distribution, or exact-value-set fingerprint authorizes CRS,
coordinate, Vs30, site-response, admission, publication, or model-use semantics.
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
    from scripts import acquire_eshm20_first_order_receipts as first_order_authority
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
    import acquire_eshm20_first_order_receipts as first_order_authority
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

SCHEMA_VERSION = "oc-eshm20-site-model-structural-profile-v2"
SOURCE_ISSUE = 281
CONTROL_ISSUE = 372
RECEIPT_SOURCE_ISSUE = 361
DATASET_ID = "efehr.eshm20"
PROJECT_PATH = "efehr/eshm20"

# Reuse the already-reviewed first-order capability rather than declaring a
# second independent provider target. Identity, not merely value equality,
# binds this profiler to the exact #361-selected site-model object.
_CANONICAL_SITE_SPEC = first_order_authority._SITE_MODEL
_CANONICAL_PROJECT_ID = first_order_authority.PROJECT_ID
_CANONICAL_COMMIT_SHA = first_order_authority.COMMIT_SHA
_CANONICAL_REPOSITORY_PATH = _CANONICAL_SITE_SPEC.repository_path
_CANONICAL_EXPECTED_BYTE_COUNT = 3_873_324
_CANONICAL_EXPECTED_SHA256 = (
    "d4d95f3e482a0361a90d1b0796545eaf075d0e212d66d025f975973497b29529"
)

# Public aliases remain useful to review/tests, but the active network target
# below is taken only from the private canonical bindings after an exact guard.
PROJECT_ID = _CANONICAL_PROJECT_ID
COMMIT_SHA = _CANONICAL_COMMIT_SHA
REPOSITORY_PATH = _CANONICAL_REPOSITORY_PATH
EXPECTED_BYTE_COUNT = _CANONICAL_EXPECTED_BYTE_COUNT
EXPECTED_SHA256 = _CANONICAL_EXPECTED_SHA256

ROOT_DEPENDENCY_RESULT_COMMENT_ID = first_order_authority.SELECTION_RESULT_COMMENT_ID
ROOT_DEPENDENCY_SECTION = _CANONICAL_SITE_SPEC.parent_section
ROOT_DEPENDENCY_OPTION = _CANONICAL_SITE_SPEC.parent_option
FIRST_ORDER_RECEIPT_REQUEST_COMMENT_ID = 5301857400
FIRST_ORDER_RECEIPT_RUN_ID = 31880089623
FIRST_ORDER_RECEIPT_EXECUTION_SHA = "ab66e3e4c58c9b8f18587f1a8a51cf67cf9851b1"

DELIMITER = ","
MIN_COLUMNS = 2
MAX_COLUMNS = 128
MAX_HEADER_UTF8_BYTES = 256


class Eshm20SiteModelProfileError(RuntimeError):
    """Raised when the fixed site-model profile cannot close safely."""


def _require_canonical_target() -> object:
    """Fail before provider work if any published fixed-target alias drifts."""

    if first_order_authority._SITE_MODEL is not _CANONICAL_SITE_SPEC:
        raise Eshm20SiteModelProfileError(
            "canonical #361 ESHM20 site-model capability identity drifted"
        )
    try:
        authorized = first_order_authority._require_authorized_spec(
            _CANONICAL_SITE_SPEC
        )
    except first_order_authority.Eshm20FirstOrderReceiptError as exc:
        raise Eshm20SiteModelProfileError(
            "canonical #361 ESHM20 site-model capability is no longer authorized"
        ) from exc
    if authorized is not _CANONICAL_SITE_SPEC:
        raise Eshm20SiteModelProfileError(
            "canonical #361 ESHM20 site-model capability identity is invalid"
        )

    exact_aliases = (
        (PROJECT_ID, _CANONICAL_PROJECT_ID, "project id"),
        (COMMIT_SHA, _CANONICAL_COMMIT_SHA, "commit"),
        (REPOSITORY_PATH, _CANONICAL_REPOSITORY_PATH, "repository path"),
        (
            EXPECTED_BYTE_COUNT,
            _CANONICAL_EXPECTED_BYTE_COUNT,
            "expected byte count",
        ),
        (EXPECTED_SHA256, _CANONICAL_EXPECTED_SHA256, "expected SHA-256"),
    )
    for observed, expected, label in exact_aliases:
        if type(observed) is not type(expected) or observed != expected:
            raise Eshm20SiteModelProfileError(
                f"frozen ESHM20 site-model {label} drifted"
            )
    return _CANONICAL_SITE_SPEC


def _verify_payload_identity(payload: bytes) -> str:
    if type(payload) is not bytes:
        raise Eshm20SiteModelProfileError("site-model payload must be immutable bytes")
    if len(payload) != _CANONICAL_EXPECTED_BYTE_COUNT:
        raise Eshm20SiteModelProfileError(
            "site-model byte count does not match the trusted #361 receipt"
        )
    observed_sha256 = hashlib.sha256(payload).hexdigest()
    if observed_sha256 != _CANONICAL_EXPECTED_SHA256:
        raise Eshm20SiteModelProfileError(
            "site-model SHA-256 does not match the trusted #361 receipt"
        )
    return observed_sha256


def _value_set_sha256(values: set[str]) -> str:
    digest = hashlib.sha256()
    for value in sorted(values):
        encoded = value.encode("utf-8")
        digest.update(len(encoded).to_bytes(8, "big"))
        digest.update(encoded)
    return digest.hexdigest()


def _line_ending_profile(raw: bytes) -> dict[str, int]:
    crlf_count = raw.count(b"\r\n")
    without_crlf = raw.replace(b"\r\n", b"")
    return {
        "crlf_count": crlf_count,
        "lf_count": without_crlf.count(b"\n"),
        "cr_count": without_crlf.count(b"\r"),
    }


def _profile_csv_text(text: str) -> dict[str, Any]:
    if "\x00" in text:
        raise Eshm20SiteModelProfileError(
            "verified site-model CSV contains NUL characters"
        )

    reader = csv.reader(
        io.StringIO(text, newline=""),
        delimiter=DELIMITER,
        strict=True,
    )
    try:
        header = next(reader)
    except StopIteration as exc:
        raise Eshm20SiteModelProfileError(
            "verified site-model CSV has no header"
        ) from exc
    except csv.Error as exc:
        raise Eshm20SiteModelProfileError(
            "verified site-model CSV header is malformed"
        ) from exc

    if not (MIN_COLUMNS <= len(header) <= MAX_COLUMNS):
        raise Eshm20SiteModelProfileError(
            "site-model CSV column count is outside bounded policy"
        )
    if any(
        type(name) is not str
        or not name.strip()
        or len(name.encode("utf-8")) > MAX_HEADER_UTF8_BYTES
        for name in header
    ):
        raise Eshm20SiteModelProfileError(
            "site-model CSV contains an empty or oversized header"
        )
    if len(set(header)) != len(header):
        raise Eshm20SiteModelProfileError(
            "site-model CSV contains duplicate headers"
        )
    if any(
        any(ord(character) < 32 or ord(character) == 127 for character in name)
        for name in header
    ):
        raise Eshm20SiteModelProfileError(
            "site-model CSV header contains control characters"
        )

    states = [
        {
            "empty_count": 0,
            "nonempty_count": 0,
            "distinct_values": set(),
            "finite_decimal_count": 0,
            "leading_or_trailing_whitespace_count": 0,
        }
        for _ in header
    ]
    record_count = 0

    try:
        for row in reader:
            if len(row) != len(header):
                raise Eshm20SiteModelProfileError(
                    "site-model CSV row width differs from the header"
                )
            record_count += 1
            for index, value in enumerate(row):
                state = states[index]
                state["distinct_values"].add(value)
                if value == "":
                    state["empty_count"] += 1
                    continue
                state["nonempty_count"] += 1
                if value != value.strip():
                    state["leading_or_trailing_whitespace_count"] += 1
                    continue
                try:
                    numeric = Decimal(value)
                except InvalidOperation:
                    continue
                if numeric.is_finite():
                    state["finite_decimal_count"] += 1
    except csv.Error as exc:
        raise Eshm20SiteModelProfileError(
            "verified site-model CSV is malformed"
        ) from exc

    if record_count < 1:
        raise Eshm20SiteModelProfileError(
            "verified site-model CSV contains no data records"
        )

    columns: list[dict[str, Any]] = []
    for name, state in zip(header, states, strict=True):
        distinct_values = state.pop("distinct_values")
        if type(distinct_values) is not set:
            raise Eshm20SiteModelProfileError(
                "internal site-model distinct-value state is invalid"
            )
        nonempty_count = state["nonempty_count"]
        finite_decimal_count = state["finite_decimal_count"]
        columns.append(
            {
                "name": name,
                "record_count": record_count,
                "empty_count": state["empty_count"],
                "nonempty_count": nonempty_count,
                "distinct_count": len(distinct_values),
                "exact_value_set_sha256": _value_set_sha256(distinct_values),
                "decimal_summary": {
                    "all_nonempty_decimal": bool(nonempty_count)
                    and finite_decimal_count == nonempty_count,
                    "finite_decimal_count": finite_decimal_count,
                    "leading_or_trailing_whitespace_count": state[
                        "leading_or_trailing_whitespace_count"
                    ],
                },
            }
        )

    return {
        "delimiter": DELIMITER,
        "record_count": record_count,
        "header": list(header),
        "columns": columns,
    }


def extract_verified_site_model_profile(payload: bytes) -> dict[str, Any]:
    """Verify exact #361 bytes before decoding and structural profiling."""

    observed_sha256 = _verify_payload_identity(payload)
    utf8_bom_present = payload.startswith(b"\xef\xbb\xbf")
    try:
        text = payload.decode(
            "utf-8-sig" if utf8_bom_present else "utf-8",
            errors="strict",
        )
    except UnicodeDecodeError as exc:
        raise Eshm20SiteModelProfileError(
            "verified site-model payload is not strict UTF-8"
        ) from exc

    profile = _profile_csv_text(text)
    return {
        "schema_version": SCHEMA_VERSION,
        "source_issue": SOURCE_ISSUE,
        "control_issue": CONTROL_ISSUE,
        "receipt_source_issue": RECEIPT_SOURCE_ISSUE,
        "dataset_id": DATASET_ID,
        "project_id": _CANONICAL_PROJECT_ID,
        "project_path": PROJECT_PATH,
        "commit_sha": _CANONICAL_COMMIT_SHA,
        "repository_path": _CANONICAL_REPOSITORY_PATH,
        "byte_count": len(payload),
        "sha256": observed_sha256,
        "parser": {
            "encoding": "utf-8-sig" if utf8_bom_present else "utf-8",
            "bom_present": utf8_bom_present,
            "line_endings": _line_ending_profile(payload),
        },
        "inventory_receipt_comment_id": first_order_authority.SELECTION_RESULT_COMMENT_ID,
        "root_dependency_result_comment_id": ROOT_DEPENDENCY_RESULT_COMMENT_ID,
        "root_dependency_section": ROOT_DEPENDENCY_SECTION,
        "root_dependency_option": ROOT_DEPENDENCY_OPTION,
        "first_order_receipt_request_comment_id": FIRST_ORDER_RECEIPT_REQUEST_COMMENT_ID,
        "first_order_receipt_run_id": FIRST_ORDER_RECEIPT_RUN_ID,
        "first_order_receipt_execution_sha": FIRST_ORDER_RECEIPT_EXECUTION_SHA,
        "profile": profile,
        "raw_rows_returned": False,
        "schema_interpretation_authorized": False,
        "crs_authorized": False,
        "coordinate_semantics_authorized": False,
        "site_response_authorized": False,
        "site_semantics_authorized": False,
        "external_bytes_persisted": False,
        "publication_authorized": False,
        "model_use_authorized": False,
    }


def acquire_eshm20_site_model_profile(
    *, opener: Any | None = None, monotonic: Any = time.monotonic
) -> dict[str, Any]:
    """Re-materialize and structurally profile only the fixed #361 site object."""

    site_spec = _require_canonical_target()
    try:
        target = validate_target(
            source_issue=SOURCE_ISSUE,
            dataset_id=DATASET_ID,
            project_id=_CANONICAL_PROJECT_ID,
            commit_sha=_CANONICAL_COMMIT_SHA,
            repository_path=site_spec.repository_path,
        )
    except EfehrReceiptError as exc:
        raise Eshm20SiteModelProfileError(
            "trusted ESHM20 site-model target is invalid"
        ) from exc

    file_url = raw_file_api_url(target)
    request = urllib.request.Request(
        file_url,
        headers={
            "Accept": "text/csv,text/plain;q=0.9,application/octet-stream;q=0.8",
            "User-Agent": "OpenCatastrophe-ESHM20-site-model-structural-profile-v2",
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
                maximum=_CANONICAL_EXPECTED_BYTE_COUNT,
                monotonic=monotonic,
            )
    except Eshm20SiteModelProfileError:
        raise
    except EfehrAcquisitionError as exc:
        raise Eshm20SiteModelProfileError(
            "ESHM20 site-model retrieval failed closed"
        ) from exc
    except (OSError, urllib.error.URLError, urllib.error.HTTPError, TimeoutError) as exc:
        raise Eshm20SiteModelProfileError(
            f"ESHM20 site-model retrieval failed: {type(exc).__name__}"
        ) from exc

    result = extract_verified_site_model_profile(raw)
    ceilings = (
        "raw_rows_returned",
        "schema_interpretation_authorized",
        "crs_authorized",
        "coordinate_semantics_authorized",
        "site_response_authorized",
        "site_semantics_authorized",
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
