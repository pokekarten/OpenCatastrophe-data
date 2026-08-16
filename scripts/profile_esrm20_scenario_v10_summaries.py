# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Byte-ground two fixed ESRM20 scenario-test v1.0 summary CSVs.

The provider bytes are read transiently from exactly two predeclared files at
the immutable v1.0 commit. Only bounded structure and exact scenario/event
identity literals are returned. Raw rows, scenario payloads, event selection,
publication and model-use authority remain outside this profile.
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
import re
import time
import urllib.parse
import urllib.request
from typing import Any

from scripts import acquire_efehr_gitlab_receipt as transport
from scripts.efehr_gitlab_receipt import PROVIDER_ROOT

SCHEMA_VERSION = "oc-esrm20-scenario-v10-summaries-profile-v1"
SOURCE_ISSUE = 488
PARENT_SCIENCE_ISSUE = 285
PROJECT_ID = 273
PROJECT_PATH = "efehr/esrm20_scenario_tests"
RELEASE_TAG = "v1.0"
COMMIT_SHA = "041f90d950d6ff84180b2faa11319a42c66c74cc"
SUMMARY_PATHS = (
    "scenario_ruptures_output_summary.csv",
    "scenario_shakemaps_output_summary.csv",
)
DATASET_ATTRIBUTION = {
    "dataset_title": "Earthquake Scenario Loss Testing Repository",
    "dataset_version": "v1.0",
    "license_identifier": "CC-BY-4.0",
    "citation": (
        "H. Crowley, J. Dabbeek, L. Danciu, P. Kalakonas, E. Riga, V. Silva, "
        "E. Veliu, G. Weatherill (2021). Earthquake Scenario Loss Testing "
        "Repository (v1.0) [Data set]. Zenodo. "
        "https://doi.org/10.5281/zenodo.5728008"
    ),
    "doi": "10.5281/zenodo.5728008",
}

MAX_FILE_BYTES = 2 * 1024 * 1024
MAX_ROWS = 20_000
MAX_COLUMNS = 128
MAX_CELL_UTF8_BYTES = 8 * 1024
MAX_IDENTITY_VALUES_PER_COLUMN = 512
TOTAL_DEADLINE_SECONDS = 60.0

IDENTITY_HEADER_TOKENS = frozenset(
    {
        "scenario",
        "scenario_id",
        "scenario_name",
        "event",
        "event_id",
        "event_name",
        "earthquake",
        "earthquake_id",
        "earthquake_name",
    }
)
_DELIMITERS = ((",", "comma"), (";", "semicolon"), ("\t", "tab"))
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")

_OPEN_FIXED = transport._open_fixed
_READ_BOUNDED = transport._read_bounded
_VALIDATE_RESPONSE = transport._validate_exact_response
_REMAINING = transport._remaining
_MONOTONIC = time.monotonic
_NOW = transport.utc_now


class ScenarioSummaryProfileError(RuntimeError):
    """Raised when fixed scenario summary evidence cannot be proven safely."""


def _bounded_cell(value: object, *, field: str) -> str:
    if type(value) is not str:
        raise ScenarioSummaryProfileError(f"{field} is not text")
    try:
        encoded = value.encode("utf-8")
    except UnicodeEncodeError as exc:
        raise ScenarioSummaryProfileError(f"{field} is not UTF-8 encodable") from exc
    if len(encoded) > MAX_CELL_UTF8_BYTES:
        raise ScenarioSummaryProfileError(f"{field} exceeds bounded policy")
    if any(ord(ch) < 32 or ord(ch) == 127 for ch in value):
        raise ScenarioSummaryProfileError(f"{field} contains forbidden control characters")
    return value


def _raw_url(path: str) -> str:
    if path not in SUMMARY_PATHS:
        raise ScenarioSummaryProfileError("scenario summary path is outside exact allow-list")
    encoded_path = urllib.parse.quote(path, safe="")
    encoded_ref = urllib.parse.quote(COMMIT_SHA, safe="")
    return (
        f"{PROVIDER_ROOT}/api/v4/projects/{PROJECT_ID}/repository/files/"
        f"{encoded_path}/raw?ref={encoded_ref}"
    )


def _decode_csv(payload: bytes) -> str:
    if type(payload) is not bytes or not (1 <= len(payload) <= MAX_FILE_BYTES):
        raise ScenarioSummaryProfileError("scenario summary byte size is outside bounded policy")
    if b"\x00" in payload:
        raise ScenarioSummaryProfileError("scenario summary contains NUL bytes")
    try:
        text = payload.decode("utf-8-sig", errors="strict")
    except UnicodeDecodeError as exc:
        raise ScenarioSummaryProfileError("scenario summary must be UTF-8") from exc
    if "\r" in text.replace("\r\n", ""):
        raise ScenarioSummaryProfileError("scenario summary contains bare carriage returns")
    return text


def _parse_with_delimiter(text: str, delimiter: str) -> tuple[list[str], list[list[str]]]:
    try:
        rows = list(csv.reader(io.StringIO(text, newline=""), delimiter=delimiter, strict=True))
    except csv.Error as exc:
        raise ScenarioSummaryProfileError("scenario summary CSV parse failed") from exc
    if not rows:
        raise ScenarioSummaryProfileError("scenario summary CSV is empty")
    if len(rows) > MAX_ROWS + 1:
        raise ScenarioSummaryProfileError("scenario summary row count exceeds bounded policy")
    width = len(rows[0])
    if not (2 <= width <= MAX_COLUMNS):
        raise ScenarioSummaryProfileError("scenario summary column count is outside bounded policy")
    if any(len(row) != width for row in rows):
        raise ScenarioSummaryProfileError("scenario summary contains ragged rows")
    header = [_bounded_cell(value, field="scenario summary header") for value in rows[0]]
    if any(not value or value != value.strip() for value in header):
        raise ScenarioSummaryProfileError("scenario summary headers must be non-empty and trimmed")
    folded = [value.casefold() for value in header]
    if len(set(folded)) != len(folded):
        raise ScenarioSummaryProfileError("scenario summary headers are not unique")
    data_rows = rows[1:]
    if not data_rows:
        raise ScenarioSummaryProfileError("scenario summary contains no data rows")
    for row in data_rows:
        for value in row:
            _bounded_cell(value, field="scenario summary cell")
    return header, data_rows


def _parse_csv(text: str) -> tuple[str, list[str], list[list[str]]]:
    candidates: list[tuple[str, list[str], list[list[str]]]] = []
    for delimiter, delimiter_name in _DELIMITERS:
        try:
            header, rows = _parse_with_delimiter(text, delimiter)
        except ScenarioSummaryProfileError:
            continue
        candidates.append((delimiter_name, header, rows))
    if len(candidates) != 1:
        raise ScenarioSummaryProfileError(
            "scenario summary delimiter is ambiguous or outside the closed delimiter set"
        )
    return candidates[0]


def _identity_evidence(
    header: list[str], rows: list[list[str]]
) -> tuple[list[str], dict[str, list[str]], str]:
    identity_columns = [
        name for name in header if name.casefold() in IDENTITY_HEADER_TOKENS
    ]
    identity_values: dict[str, list[str]] = {}
    for name in identity_columns:
        index = header.index(name)
        values = sorted({row[index] for row in rows if row[index] != ""})
        if len(values) > MAX_IDENTITY_VALUES_PER_COLUMN:
            raise ScenarioSummaryProfileError(
                "scenario identity value count exceeds bounded policy"
            )
        for value in values:
            _bounded_cell(value, field="scenario identity value")
        identity_values[name] = values

    canonical = json.dumps(
        identity_values,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
    return identity_columns, identity_values, hashlib.sha256(canonical).hexdigest()


def profile_summary_bytes(path: str, payload: bytes, *, retrieved_at: str) -> dict[str, Any]:
    """Profile one of the two exact summary files from already-fetched bytes."""
    if path not in SUMMARY_PATHS:
        raise ScenarioSummaryProfileError("scenario summary path is outside exact allow-list")
    if type(retrieved_at) is not str or not retrieved_at.endswith("Z"):
        raise ScenarioSummaryProfileError("scenario summary retrieval timestamp is invalid")
    text = _decode_csv(payload)
    delimiter, header, rows = _parse_csv(text)
    identity_columns, identity_values, identity_sha = _identity_evidence(header, rows)
    return {
        "repository_path": path,
        "retrieved_at": retrieved_at,
        "byte_count": len(payload),
        "sha256": hashlib.sha256(payload).hexdigest(),
        "encoding": "utf-8",
        "delimiter": delimiter,
        "column_count": len(header),
        "row_count": len(rows),
        "headers": header,
        "identity_columns": identity_columns,
        "identity_values": identity_values,
        "identity_set_sha256": identity_sha,
        "raw_rows_returned": False,
    }


def _validate_profile_receipt_shape(value: object, *, path: str) -> dict[str, Any]:
    if type(value) is not dict:
        raise ScenarioSummaryProfileError("scenario summary profile is not an object")
    if value.get("repository_path") != path:
        raise ScenarioSummaryProfileError("scenario summary path drifted")
    if type(value.get("byte_count")) is not int or isinstance(value["byte_count"], bool):
        raise ScenarioSummaryProfileError("scenario summary byte count is invalid")
    if not (1 <= value["byte_count"] <= MAX_FILE_BYTES):
        raise ScenarioSummaryProfileError("scenario summary byte count exceeds policy")
    sha256 = value.get("sha256")
    if type(sha256) is not str or _SHA256_RE.fullmatch(sha256) is None:
        raise ScenarioSummaryProfileError("scenario summary SHA-256 is invalid")
    return value


def _aggregate_identity_sha256(files: list[dict[str, Any]]) -> str:
    canonical = {
        item["repository_path"]: item["identity_values"]
        for item in sorted(files, key=lambda item: item["repository_path"])
    }
    encoded = json.dumps(
        canonical, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def acquire_and_profile_summaries(
    *,
    opener: Any | None = None,
    now: Any | None = None,
    monotonic: Any | None = None,
) -> dict[str, Any]:
    """Fetch exactly two fixed provider summaries and return bounded evidence."""
    if (
        transport._open_fixed is not _OPEN_FIXED
        or transport._read_bounded is not _READ_BOUNDED
        or transport._validate_exact_response is not _VALIDATE_RESPONSE
        or transport._remaining is not _REMAINING
        or transport.utc_now is not _NOW
        or time.monotonic is not _MONOTONIC
    ):
        raise ScenarioSummaryProfileError("trusted EFEHR transport authority drifted")

    open_response = opener or _OPEN_FIXED
    clock = monotonic or _MONOTONIC
    now_utc = now or _NOW
    deadline = clock() + TOTAL_DEADLINE_SECONDS
    profiles: list[dict[str, Any]] = []

    for path in SUMMARY_PATHS:
        url = _raw_url(path)
        request = urllib.request.Request(
            url,
            headers={
                "Accept": "text/csv,text/plain;q=0.9,*/*;q=0.1",
                "User-Agent": "OpenCatastrophe-ESRM20-scenario-v10-summaries-v1",
            },
            method="GET",
        )
        try:
            with open_response(request, timeout=_REMAINING(deadline, clock)) as response:
                _VALIDATE_RESPONSE(response, url)
                payload = _READ_BOUNDED(
                    response,
                    deadline=deadline,
                    maximum=MAX_FILE_BYTES,
                    monotonic=clock,
                )
        except ScenarioSummaryProfileError:
            raise
        except (OSError, TimeoutError, transport.EfehrAcquisitionError) as exc:
            raise ScenarioSummaryProfileError(
                "scenario summary acquisition failed closed"
            ) from exc

        retrieved_at = now_utc()
        profile = profile_summary_bytes(path, payload, retrieved_at=retrieved_at)
        profiles.append(_validate_profile_receipt_shape(profile, path=path))

    if [item["repository_path"] for item in profiles] != list(SUMMARY_PATHS):
        raise ScenarioSummaryProfileError("scenario summary acquisition order drifted")
    identity_value_count = sum(
        len(values)
        for item in profiles
        for values in item["identity_values"].values()
    )
    return {
        "schema_version": SCHEMA_VERSION,
        "source_issue": SOURCE_ISSUE,
        "parent_science_issue": PARENT_SCIENCE_ISSUE,
        "project_id": PROJECT_ID,
        "project_path": PROJECT_PATH,
        "release_tag": RELEASE_TAG,
        "commit_sha": COMMIT_SHA,
        "summary_paths": list(SUMMARY_PATHS),
        "dataset_attribution": dict(DATASET_ATTRIBUTION),
        "summaries": profiles,
        "identity_value_count": identity_value_count,
        "identity_set_sha256": _aggregate_identity_sha256(profiles),
        "provider_file_bytes_read": True,
        "external_bytes_persisted": False,
        "scenario_payload_bytes_read": False,
        "scenario_selection_authorized": False,
        "publication_authorized": False,
        "model_use_authorized": False,
    }
