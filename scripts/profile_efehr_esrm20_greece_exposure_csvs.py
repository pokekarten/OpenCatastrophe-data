# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Receipt-bound structural profiler for the three Greece exposure CSVs.

The immutable byte identities are established by trusted-main issue #285
terminal comment 5397480571.  This module does not acquire provider data.  It
accepts only those three source-declared objects and verifies exact byte count
and SHA-256 before any decoding or CSV parsing.

The output is deliberately interpretation-light: headers, record counts,
missingness counts, decimal-shape summaries, and exact value-set fingerprints.
It does not return raw rows or exact field values and does not designate any
column as taxonomy, CRS, replacement cost, or other model semantics.
"""

from __future__ import annotations

import csv
import hashlib
import io
from decimal import Decimal, InvalidOperation
from typing import Any

SCHEMA_VERSION = "oc-esrm20-greece-exposure-3csv-content-profile-v0"
SOURCE_ISSUE = 285
PARENT_CONSUMER_ISSUE = 287
DATASET_ID = "efehr.esrm20.risk-inputs.v1.0"
PROJECT_ID = 269
PROJECT_PATH = "efehr/esrm20"
RELEASE_TAG = "v1.0"
COMMIT_SHA = "05f83bbc9df81d02ee8ddb1801d9d781355ce783"
CONSUMER_EVENT_ID = "Greece_07-9-1999"
PARENT_EXPOSURE_PATH = "Exposure/OQ_Exposure_Input_Greece.xml"
RECEIPT_COMMENT_ID = 5397480571
RECEIPT_EXECUTION_SHA = "4b1d3c41a5df739b9686303eb753577ca39ec58e"

RECEIPTS: tuple[tuple[str, int, str], ...] = (
    (
        "Exposure/OQ_Exposure_Input_Greece_Com.csv",
        7_672_810,
        "2281f079a6e0b2215fab696d442f9d98b9b0ba94a2b4b24f23f1fff4018d1b57",
    ),
    (
        "Exposure/OQ_Exposure_Input_Greece_Ind.csv",
        2_822_653,
        "ad6698199d84002d017b41668dc204a2d53835a4b2429bc7e8eea56b328549c7",
    ),
    (
        "Exposure/OQ_Exposure_Input_Greece_Res.csv",
        5_263_604,
        "928ac7f069dfc3181a936f73caafb951a5c2437f70379fa29518c002bbd3ef28",
    ),
)

DELIMITER = ","
MIN_COLUMNS = 2
MAX_COLUMNS = 128
MAX_HEADER_UTF8_BYTES = 256


class GreeceExposureCsvProfileError(ValueError):
    """Raised when receipt identity or bounded CSV structure fails closed."""


def _receipt_map() -> dict[str, tuple[int, str]]:
    result: dict[str, tuple[int, str]] = {}
    for path, byte_count, sha256 in RECEIPTS:
        if path in result:
            raise GreeceExposureCsvProfileError("duplicate frozen Greece exposure CSV path")
        if type(path) is not str or not path:
            raise GreeceExposureCsvProfileError("invalid frozen Greece exposure CSV path")
        if type(byte_count) is not int or isinstance(byte_count, bool) or byte_count < 1:
            raise GreeceExposureCsvProfileError("invalid frozen Greece exposure CSV byte count")
        if (
            type(sha256) is not str
            or len(sha256) != 64
            or any(character not in "0123456789abcdef" for character in sha256)
        ):
            raise GreeceExposureCsvProfileError("invalid frozen Greece exposure CSV SHA-256")
        result[path] = (byte_count, sha256)
    if len(result) != 3:
        raise GreeceExposureCsvProfileError("frozen Greece exposure CSV receipt set drifted")
    return result


def _value_set_sha256(values: set[str]) -> str:
    digest = hashlib.sha256()
    for value in sorted(values):
        encoded = value.encode("utf-8")
        digest.update(len(encoded).to_bytes(8, "big"))
        digest.update(encoded)
    return digest.hexdigest()


def _line_ending_profile(raw: bytes) -> dict[str, int]:
    crlf = raw.count(b"\r\n")
    without_crlf = raw.replace(b"\r\n", b"")
    return {
        "crlf_count": crlf,
        "lf_count": without_crlf.count(b"\n"),
        "cr_count": without_crlf.count(b"\r"),
    }


def _new_column_state() -> dict[str, Any]:
    return {
        "distinct": set(),
        "empty_count": 0,
        "nonempty_count": 0,
        "finite_decimal_count": 0,
        "leading_or_trailing_whitespace_count": 0,
    }


def _observe_value(state: dict[str, Any], value: str) -> None:
    state["distinct"].add(value)
    if value == "":
        state["empty_count"] += 1
        return

    state["nonempty_count"] += 1
    if value != value.strip():
        state["leading_or_trailing_whitespace_count"] += 1
        return
    try:
        number = Decimal(value)
    except InvalidOperation:
        return
    if number.is_finite():
        state["finite_decimal_count"] += 1


def _profile_receipt_verified_csv(
    raw: bytes,
    *,
    expected_byte_count: int,
    expected_sha256: str,
) -> dict[str, Any]:
    """Verify exact bytes first, then derive bounded structure-only evidence."""

    if type(raw) is not bytes:
        raise GreeceExposureCsvProfileError("exposure input must be immutable bytes")
    if type(expected_byte_count) is not int or isinstance(expected_byte_count, bool):
        raise GreeceExposureCsvProfileError("expected byte count must be an integer")
    if expected_byte_count < 1:
        raise GreeceExposureCsvProfileError("expected byte count must be positive")
    if (
        type(expected_sha256) is not str
        or len(expected_sha256) != 64
        or any(character not in "0123456789abcdef" for character in expected_sha256)
    ):
        raise GreeceExposureCsvProfileError(
            "expected SHA-256 must be 64 lowercase hex characters"
        )

    # Scientific boundary: no decode or parse is allowed before both receipt
    # identity checks have passed.
    if len(raw) != expected_byte_count:
        raise GreeceExposureCsvProfileError("exposure byte count does not match trusted receipt")
    if hashlib.sha256(raw).hexdigest() != expected_sha256:
        raise GreeceExposureCsvProfileError("exposure SHA-256 does not match trusted receipt")

    bom_present = raw.startswith(b"\xef\xbb\xbf")
    try:
        text = raw.decode("utf-8-sig" if bom_present else "utf-8", errors="strict")
    except UnicodeDecodeError as exc:
        raise GreeceExposureCsvProfileError(
            "verified exposure object is not valid UTF-8"
        ) from exc
    if "\x00" in text:
        raise GreeceExposureCsvProfileError("verified exposure object contains NUL characters")

    reader = csv.reader(io.StringIO(text, newline=""), delimiter=DELIMITER, strict=True)
    try:
        header = next(reader)
    except StopIteration as exc:
        raise GreeceExposureCsvProfileError("verified exposure CSV has no header") from exc
    except csv.Error as exc:
        raise GreeceExposureCsvProfileError("verified exposure CSV header is malformed") from exc

    if not (MIN_COLUMNS <= len(header) <= MAX_COLUMNS):
        raise GreeceExposureCsvProfileError(
            "verified exposure CSV column count is outside bounded policy"
        )
    if any(name == "" for name in header):
        raise GreeceExposureCsvProfileError("verified exposure CSV contains an empty header")
    if len(set(header)) != len(header):
        raise GreeceExposureCsvProfileError("verified exposure CSV contains duplicate headers")
    if any(len(name.encode("utf-8")) > MAX_HEADER_UTF8_BYTES for name in header):
        raise GreeceExposureCsvProfileError("verified exposure CSV header exceeds bounded policy")
    if any(
        any(ord(character) < 32 or ord(character) == 127 for character in name)
        for name in header
    ):
        raise GreeceExposureCsvProfileError(
            "verified exposure CSV header contains control characters"
        )

    states = [_new_column_state() for _ in header]
    record_count = 0
    try:
        for row in reader:
            if len(row) != len(header):
                raise GreeceExposureCsvProfileError("verified exposure CSV contains a ragged row")
            record_count += 1
            for state, value in zip(states, row, strict=True):
                _observe_value(state, value)
    except csv.Error as exc:
        raise GreeceExposureCsvProfileError("verified exposure CSV is malformed") from exc

    if record_count < 1:
        raise GreeceExposureCsvProfileError("verified exposure CSV contains no data records")

    columns: list[dict[str, Any]] = []
    for name, state in zip(header, states, strict=True):
        distinct = state.pop("distinct")
        nonempty_count = state["nonempty_count"]
        finite_decimal_count = state["finite_decimal_count"]
        columns.append(
            {
                "name": name,
                "record_count": record_count,
                "empty_count": state["empty_count"],
                "nonempty_count": nonempty_count,
                "distinct_count": len(distinct),
                "exact_value_set_sha256": _value_set_sha256(distinct),
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
        "schema_version": SCHEMA_VERSION,
        "parser": {
            "encoding": "utf-8-sig" if bom_present else "utf-8",
            "bom_present": bom_present,
            "delimiter": DELIMITER,
            "line_endings": _line_ending_profile(raw),
        },
        "record_count": record_count,
        "header": header,
        "columns": columns,
        "raw_rows_returned": False,
        "exact_field_values_returned": False,
        "external_bytes_persisted": False,
        "publication_authorized": False,
    }


def profile_verified_csv_bytes(raw: bytes, *, repository_path: str) -> dict[str, Any]:
    """Profile one of the three exact source-declared Greece exposure CSVs."""

    receipts = _receipt_map()
    if type(repository_path) is not str or repository_path not in receipts:
        raise GreeceExposureCsvProfileError(
            "Greece exposure CSV path left frozen three-object receipt set"
        )
    expected_byte_count, expected_sha256 = receipts[repository_path]
    profile = _profile_receipt_verified_csv(
        raw,
        expected_byte_count=expected_byte_count,
        expected_sha256=expected_sha256,
    )
    return {
        "repository_path": repository_path,
        "byte_count": expected_byte_count,
        "sha256": expected_sha256,
        "profile": profile,
    }


def profile_verified_bundle(raw_by_path: dict[str, bytes]) -> dict[str, Any]:
    """Profile exactly the complete three-CSV bundle in canonical order."""

    if type(raw_by_path) is not dict:
        raise GreeceExposureCsvProfileError("Greece exposure CSV bundle must be a dict")
    receipts = _receipt_map()
    if set(raw_by_path) != set(receipts):
        raise GreeceExposureCsvProfileError(
            "Greece exposure CSV bundle does not match frozen three-object receipt set"
        )

    files = [
        profile_verified_csv_bytes(raw_by_path[path], repository_path=path)
        for path, _, _ in RECEIPTS
    ]
    return {
        "schema_version": SCHEMA_VERSION,
        "source_issue": SOURCE_ISSUE,
        "parent_consumer_issue": PARENT_CONSUMER_ISSUE,
        "dataset_id": DATASET_ID,
        "project_id": PROJECT_ID,
        "project_path": PROJECT_PATH,
        "release_tag": RELEASE_TAG,
        "commit_sha": COMMIT_SHA,
        "consumer_event_id": CONSUMER_EVENT_ID,
        "parent_exposure_path": PARENT_EXPOSURE_PATH,
        "receipt_comment_id": RECEIPT_COMMENT_ID,
        "receipt_execution_sha": RECEIPT_EXECUTION_SHA,
        "files": files,
        "provider_file_content_profiled": True,
        "content_semantics_verified": False,
        "crs_semantics_verified": False,
        "taxonomy_semantics_verified": False,
        "replacement_cost_semantics_verified": False,
        "benchmark_agreement_inspected": False,
        "independent_validation_established": False,
        "holdout_status_established": False,
        "raw_rows_returned": False,
        "exact_field_values_returned": False,
        "external_bytes_persisted": False,
        "publication_authorized": False,
        "model_use_authorized": False,
    }
