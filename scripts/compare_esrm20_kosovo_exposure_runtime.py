# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Compare frozen ESRM20 Kosovo source/runtime exposure values without raw output.

This worker is deliberately narrower than an exposure converter.  It binds the
already-receipted project-186 source CSV and project-269 OpenQuake runtime CSV,
proves both byte identities before parsing, and then asks one falsifiable
question: do the exact lexical fields already shown to survive the projection
form a unique row bridge, and are selected numeric fields equal as exact
Decimals across that bridge?

No caller can select a provider target.  The result contains only aggregate
counts, field names and SHA-256 fingerprints; provider rows and raw field values
are never returned.  Canonical provider locator metadata is emitted only when
the compared bytes match the frozen receipt identities.  A successful
comparison does not authorize CRS promotion, insured-value semantics,
publication, model use, or full file equivalence.
"""

from __future__ import annotations

import csv
import hashlib
import io
import time
import urllib.error
import urllib.request
from decimal import Decimal, Inexact, Rounded, localcontext
from typing import Any

try:
    from scripts import profile_efehr_kosovo_exposure as source_profile
    from scripts import profile_efehr_kosovo_exposure_value_spatial as source_value
    from scripts import profile_esrm20_runtime_residential_csv as runtime_profile
    from scripts.acquire_efehr_gitlab_receipt import (
        EfehrAcquisitionError,
        TOTAL_DEADLINE_SECONDS,
        _open_fixed,
        _read_bounded,
        _remaining,
        _validate_exact_response,
    )
    from scripts.efehr_gitlab_receipt import EfehrReceiptError, raw_file_api_url, validate_target
except ModuleNotFoundError:  # pragma: no cover - direct script import path
    import profile_efehr_kosovo_exposure as source_profile
    import profile_efehr_kosovo_exposure_value_spatial as source_value
    import profile_esrm20_runtime_residential_csv as runtime_profile
    from acquire_efehr_gitlab_receipt import (
        EfehrAcquisitionError,
        TOTAL_DEADLINE_SECONDS,
        _open_fixed,
        _read_bounded,
        _remaining,
        _validate_exact_response,
    )
    from efehr_gitlab_receipt import EfehrReceiptError, raw_file_api_url, validate_target

SCHEMA_VERSION = "oc-esrm20-kosovo-source-runtime-decimal-comparison-v0"
EXPECTED_RECORD_COUNT = 1093

SOURCE_HEADER = source_value.EXPECTED_HEADER
RUNTIME_HEADER = (
    "id",
    "lon",
    "lat",
    "taxonomy",
    "number",
    "structural",
    "night",
    "day",
    "transit",
    "occupancy",
    "name_2",
    "id_2",
    "id_1",
    "name_1",
)

# These fields are the exact raw-string projections already established by the
# two trusted structure profiles.  They are deliberately used only as a
# comparison identity, not promoted to a provider/business key.
KEY_FIELD_PAIRS = (
    ("LONGITUDE", "lon"),
    ("LATITUDE", "lat"),
    ("TAXONOMY", "taxonomy"),
    ("OCCUPANCY", "occupancy"),
    ("NAME_2", "name_2"),
    ("ID_2", "id_2"),
    ("ID_1", "id_1"),
    ("NAME_1", "name_1"),
)

NUMERIC_FIELD_PAIRS = (
    ("BUILDINGS", "number"),
    ("TOTAL_REPL_COST_EUR", "structural"),
    ("OCCUPANTS_PER_ASSET_DAY", "day"),
    ("OCCUPANTS_PER_ASSET_NIGHT", "night"),
    ("OCCUPANTS_PER_ASSET_TRANSIT", "transit"),
)

_KEY_DIGEST_DOMAIN = b"OpenCatastrophe/EQ1/KosovoExposureProjectionKey/v1\x00"
_KEYSET_DIGEST_DOMAIN = b"OpenCatastrophe/EQ1/KosovoExposureProjectionKeySet/v1\x00"
_RELATION_DIGEST_DOMAIN = b"OpenCatastrophe/EQ1/KosovoExposureDecimalRelation/v1\x00"

_CANONICAL_OPEN_FIXED = _open_fixed
_CANONICAL_MONOTONIC = time.monotonic


class ExposureRuntimeComparisonError(RuntimeError):
    """Raised when the fixed cross-release comparison cannot be proved safely."""


def _framed_digest(domain: bytes, values: tuple[str, ...]) -> bytes:
    digest = hashlib.sha256()
    digest.update(domain)
    for value in values:
        encoded = value.encode("utf-8")
        digest.update(len(encoded).to_bytes(8, "big"))
        digest.update(encoded)
    return digest.digest()


def _keyset_sha256(keys: set[tuple[str, ...]]) -> str:
    framed: dict[bytes, tuple[str, ...]] = {}
    for key in keys:
        key_digest = _framed_digest(_KEY_DIGEST_DOMAIN, key)
        previous = framed.get(key_digest)
        if previous is not None and previous != key:
            raise ExposureRuntimeComparisonError("SHA-256 collision in comparison key")
        framed[key_digest] = key
    digest = hashlib.sha256()
    digest.update(_KEYSET_DIGEST_DOMAIN)
    for key_digest in sorted(framed):
        digest.update(key_digest)
    return digest.hexdigest()


def _parse_verified_rows(
    raw: bytes,
    *,
    expected_byte_count: int,
    expected_sha256: str,
    expected_header: tuple[str, ...],
    label: str,
) -> list[dict[str, str]]:
    try:
        structure = source_profile.profile_verified_csv_bytes(
            raw,
            expected_byte_count=expected_byte_count,
            expected_sha256=expected_sha256,
        )
    except source_profile.ExposureProfileError as exc:
        raise ExposureRuntimeComparisonError(f"{label} receipt/structure gate failed") from exc
    if tuple(structure.get("header", ())) != expected_header:
        raise ExposureRuntimeComparisonError(f"{label} header drifted")
    if structure.get("record_count") != EXPECTED_RECORD_COUNT:
        raise ExposureRuntimeComparisonError(f"{label} record count drifted")
    if structure.get("external_bytes_persisted") is not False:
        raise ExposureRuntimeComparisonError(f"{label} profile widened persistence authority")
    if structure.get("raw_rows_returned") is not False:
        raise ExposureRuntimeComparisonError(f"{label} profile exposed raw rows")

    encoding = structure["parser"]["encoding"]
    try:
        text = raw.decode(encoding)
    except UnicodeDecodeError as exc:  # defensive; structure profiler checked it
        raise ExposureRuntimeComparisonError(f"{label} decode drifted") from exc

    reader = csv.DictReader(io.StringIO(text, newline=""), delimiter=",", strict=True)
    if tuple(reader.fieldnames or ()) != expected_header:
        raise ExposureRuntimeComparisonError(f"{label} header changed during re-read")
    rows: list[dict[str, str]] = []
    try:
        for row in reader:
            if None in row or set(row) != set(expected_header):
                raise ExposureRuntimeComparisonError(f"{label} contains ragged row")
            if any(type(value) is not str for value in row.values()):
                raise ExposureRuntimeComparisonError(f"{label} contains non-text field")
            rows.append({field: row[field] for field in expected_header})
    except csv.Error as exc:
        raise ExposureRuntimeComparisonError(f"{label} CSV re-read failed") from exc
    if len(rows) != EXPECTED_RECORD_COUNT:
        raise ExposureRuntimeComparisonError(f"{label} record count changed during re-read")
    return rows


def _build_unique_bridge(
    rows: list[dict[str, str]],
    *,
    fields: tuple[str, ...],
    label: str,
) -> dict[tuple[str, ...], dict[str, str]]:
    bridge: dict[tuple[str, ...], dict[str, str]] = {}
    for row in rows:
        key = tuple(row[field] for field in fields)
        if key in bridge:
            raise ExposureRuntimeComparisonError(f"{label} comparison key is not unique")
        bridge[key] = row
    return bridge


def _exact_abs_difference(left: Decimal, right: Decimal) -> Decimal:
    try:
        with localcontext(source_value._EXACT_DECIMAL_CONTEXT) as context:
            return abs(context.subtract(left, right))
    except (Inexact, Rounded) as exc:
        raise ExposureRuntimeComparisonError("decimal difference exceeded exact working bound") from exc


def _relation_fingerprint(
    rows: list[tuple[tuple[str, ...], Decimal, Decimal]],
) -> str:
    digest = hashlib.sha256()
    digest.update(_RELATION_DIGEST_DOMAIN)
    framed: list[tuple[bytes, str, str]] = []
    seen: dict[bytes, tuple[str, ...]] = {}
    for key, source_value_decimal, runtime_value_decimal in rows:
        key_digest = _framed_digest(_KEY_DIGEST_DOMAIN, key)
        previous = seen.get(key_digest)
        if previous is not None and previous != key:
            raise ExposureRuntimeComparisonError("SHA-256 collision in relation key")
        seen[key_digest] = key
        framed.append(
            (
                key_digest,
                source_value._canonical_decimal(source_value_decimal),
                source_value._canonical_decimal(runtime_value_decimal),
            )
        )
    for key_digest, source_text, runtime_text in sorted(framed, key=lambda item: item[0]):
        digest.update(key_digest)
        for value in (source_text, runtime_text):
            encoded = value.encode("ascii")
            digest.update(len(encoded).to_bytes(8, "big"))
            digest.update(encoded)
    return digest.hexdigest()


def _comparison_identity(
    *,
    canonical: bool,
    project_id: int,
    project_path: str,
    commit_sha: str,
    repository_path: str,
    byte_count: int,
    sha256: str,
) -> dict[str, Any]:
    identity: dict[str, Any] = {
        "canonical_receipt_verified": canonical,
        "byte_count": byte_count,
        "sha256": sha256,
    }
    if canonical:
        identity.update(
            {
                "project_id": project_id,
                "project_path": project_path,
                "commit_sha": commit_sha,
                "repository_path": repository_path,
            }
        )
    return identity


def compare_verified_exposure_bytes(
    source_raw: bytes,
    runtime_raw: bytes,
    *,
    source_expected_byte_count: int = source_profile.EXPECTED_BYTE_COUNT,
    source_expected_sha256: str = source_profile.EXPECTED_SHA256,
    runtime_expected_byte_count: int = runtime_profile.EXPECTED_BYTE_COUNT,
    runtime_expected_sha256: str = runtime_profile.EXPECTED_SHA256,
) -> dict[str, Any]:
    """Verify both byte objects, prove a unique bridge, then compare exact Decimals."""

    source_rows = _parse_verified_rows(
        source_raw,
        expected_byte_count=source_expected_byte_count,
        expected_sha256=source_expected_sha256,
        expected_header=SOURCE_HEADER,
        label="source exposure",
    )
    runtime_rows = _parse_verified_rows(
        runtime_raw,
        expected_byte_count=runtime_expected_byte_count,
        expected_sha256=runtime_expected_sha256,
        expected_header=RUNTIME_HEADER,
        label="runtime exposure",
    )

    source_receipt_is_canonical = (
        source_expected_byte_count == source_profile.EXPECTED_BYTE_COUNT
        and source_expected_sha256 == source_profile.EXPECTED_SHA256
    )
    runtime_receipt_is_canonical = (
        runtime_expected_byte_count == runtime_profile.EXPECTED_BYTE_COUNT
        and runtime_expected_sha256 == runtime_profile.EXPECTED_SHA256
    )
    canonical_receipt_pair_verified = (
        source_receipt_is_canonical and runtime_receipt_is_canonical
    )

    source_key_fields = tuple(source for source, _runtime in KEY_FIELD_PAIRS)
    runtime_key_fields = tuple(runtime for _source, runtime in KEY_FIELD_PAIRS)
    source_bridge = _build_unique_bridge(source_rows, fields=source_key_fields, label="source")
    runtime_bridge = _build_unique_bridge(runtime_rows, fields=runtime_key_fields, label="runtime")

    source_keys = set(source_bridge)
    runtime_keys = set(runtime_bridge)
    source_keyset_sha256 = _keyset_sha256(source_keys)
    runtime_keyset_sha256 = _keyset_sha256(runtime_keys)
    if source_keys != runtime_keys:
        raise ExposureRuntimeComparisonError("source/runtime comparison key sets differ")
    if source_keyset_sha256 != runtime_keyset_sha256:  # defensive
        raise ExposureRuntimeComparisonError("source/runtime comparison key fingerprints differ")

    comparisons: list[dict[str, Any]] = []
    for source_field, runtime_field in NUMERIC_FIELD_PAIRS:
        equal_count = 0
        max_abs_difference = Decimal(0)
        relation_rows: list[tuple[tuple[str, ...], Decimal, Decimal]] = []
        for key in source_bridge:
            try:
                source_number = source_value._parse_decimal(
                    source_bridge[key][source_field], field=source_field
                )
                runtime_number = source_value._parse_decimal(
                    runtime_bridge[key][runtime_field], field=runtime_field
                )
            except source_value.ExposureValueSpatialProfileError as exc:
                raise ExposureRuntimeComparisonError(
                    f"numeric comparison failed at {source_field}->{runtime_field}"
                ) from exc
            difference = _exact_abs_difference(source_number, runtime_number)
            if difference == 0:
                equal_count += 1
            else:
                max_abs_difference = max(max_abs_difference, difference)
            relation_rows.append((key, source_number, runtime_number))

        comparisons.append(
            {
                "source_field": source_field,
                "runtime_field": runtime_field,
                "record_count": EXPECTED_RECORD_COUNT,
                "exact_decimal_equal_count": equal_count,
                "non_equal_count": EXPECTED_RECORD_COUNT - equal_count,
                "all_exact_decimal_equal": equal_count == EXPECTED_RECORD_COUNT,
                "maximum_absolute_difference": source_value._canonical_decimal(
                    max_abs_difference
                ),
                "relation_sha256": _relation_fingerprint(relation_rows),
            }
        )

    return {
        "schema_version": SCHEMA_VERSION,
        "record_count": EXPECTED_RECORD_COUNT,
        "canonical_receipt_pair_verified": canonical_receipt_pair_verified,
        "source_identity": _comparison_identity(
            canonical=source_receipt_is_canonical,
            project_id=source_profile.PROJECT_ID,
            project_path=source_profile.PROJECT_PATH,
            commit_sha=source_profile.COMMIT_SHA,
            repository_path=source_profile.REPOSITORY_PATH,
            byte_count=source_expected_byte_count,
            sha256=source_expected_sha256,
        ),
        "runtime_identity": _comparison_identity(
            canonical=runtime_receipt_is_canonical,
            project_id=runtime_profile.PROJECT_ID,
            project_path=runtime_profile.PROJECT_PATH,
            commit_sha=runtime_profile.COMMIT_SHA,
            repository_path=runtime_profile.REPOSITORY_PATH,
            byte_count=runtime_expected_byte_count,
            sha256=runtime_expected_sha256,
        ),
        "comparison_key": {
            "source_fields": list(source_key_fields),
            "runtime_fields": list(runtime_key_fields),
            "provider_business_key_authorized": False,
            "source_unique_count": len(source_bridge),
            "runtime_unique_count": len(runtime_bridge),
            "exact_key_set_equal": True,
            "key_set_sha256": source_keyset_sha256,
        },
        "numeric_comparisons": comparisons,
        "project186_equivalence_verified": False,
        "value_structural_wiring_verified": False,
        "source_crs_datum_epsg_verified": False,
        "insured_value_semantics_verified": False,
        "external_bytes_persisted": False,
        "raw_rows_returned": False,
        "publication_authorized": False,
        "model_use_authorized": False,
    }


def _fetch_fixed_payload(
    *,
    dataset_id: str,
    project_id: int,
    commit_sha: str,
    repository_path: str,
    maximum: int,
    opener: Any,
    monotonic: Any,
) -> bytes:
    try:
        target = validate_target(
            source_issue=282,
            dataset_id=dataset_id,
            project_id=project_id,
            commit_sha=commit_sha,
            repository_path=repository_path,
        )
        url = raw_file_api_url(target)
    except EfehrReceiptError as exc:
        raise ExposureRuntimeComparisonError("fixed comparison target is invalid") from exc

    deadline = monotonic() + TOTAL_DEADLINE_SECONDS
    request = urllib.request.Request(
        url,
        headers={
            "Accept": "text/csv,text/plain;q=0.9,application/octet-stream;q=0.8",
            "User-Agent": "OpenCatastrophe-EFEHR-source-runtime-compare-v0",
        },
        method="GET",
    )
    try:
        with opener(request, timeout=_remaining(deadline, monotonic)) as response:
            _validate_exact_response(response, url)
            return _read_bounded(
                response,
                deadline=deadline,
                maximum=maximum,
                monotonic=monotonic,
            )
    except ExposureRuntimeComparisonError:
        raise
    except EfehrAcquisitionError as exc:
        raise ExposureRuntimeComparisonError("fixed comparison acquisition failed closed") from exc
    except (OSError, urllib.error.URLError, urllib.error.HTTPError, TimeoutError) as exc:
        raise ExposureRuntimeComparisonError(
            f"fixed comparison retrieval failed: {type(exc).__name__}"
        ) from exc


def acquire_and_compare_kosovo_exposure_runtime(
    *,
    opener: Any = _CANONICAL_OPEN_FIXED,
    monotonic: Any = _CANONICAL_MONOTONIC,
) -> dict[str, Any]:
    """Fetch only both frozen receipt targets and return a bounded comparison."""

    if opener is _CANONICAL_OPEN_FIXED:
        if _open_fixed is not _CANONICAL_OPEN_FIXED:
            raise ExposureRuntimeComparisonError("production transport drifted")
        if monotonic is not _CANONICAL_MONOTONIC or time.monotonic is not _CANONICAL_MONOTONIC:
            raise ExposureRuntimeComparisonError("production monotonic clock drifted")

    source_raw = _fetch_fixed_payload(
        dataset_id=source_profile.DATASET_ID,
        project_id=source_profile.PROJECT_ID,
        commit_sha=source_profile.COMMIT_SHA,
        repository_path=source_profile.REPOSITORY_PATH,
        maximum=source_profile.EXPECTED_BYTE_COUNT,
        opener=opener,
        monotonic=monotonic,
    )
    runtime_raw = _fetch_fixed_payload(
        dataset_id=runtime_profile.DATASET_ID,
        project_id=runtime_profile.PROJECT_ID,
        commit_sha=runtime_profile.COMMIT_SHA,
        repository_path=runtime_profile.REPOSITORY_PATH,
        maximum=runtime_profile.EXPECTED_BYTE_COUNT,
        opener=opener,
        monotonic=monotonic,
    )
    result = compare_verified_exposure_bytes(source_raw, runtime_raw)
    if result.get("canonical_receipt_pair_verified") is not True:
        raise ExposureRuntimeComparisonError(
            "fixed comparison did not prove the canonical receipt pair"
        )
    return result
