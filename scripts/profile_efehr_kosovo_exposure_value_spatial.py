# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Receipt-bound numeric/spatial summary profiler for the frozen Kosovo exposure CSV.

The profiler extends the already-reviewed structure-only content profile with
measured aggregate diagnostics needed before a ground-up loss reference run.
It never returns raw rows, never interprets a CRS or valuation vintage, and
does not authorize publication or model use.
"""

from __future__ import annotations

import csv
import hashlib
import io
import time
import urllib.error
import urllib.request
from decimal import Context, Decimal, Inexact, InvalidOperation, Rounded, localcontext
from typing import Any

try:
    from scripts import profile_efehr_kosovo_exposure as exposure
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
    import profile_efehr_kosovo_exposure as exposure
    from acquire_efehr_gitlab_receipt import (
        EfehrAcquisitionError,
        TOTAL_DEADLINE_SECONDS,
        _open_fixed,
        _read_bounded,
        _remaining,
        _validate_exact_response,
    )
    from efehr_gitlab_receipt import EfehrReceiptError, raw_file_api_url, validate_target


SCHEMA_VERSION = "oc-esrm20-exposure-value-spatial-profile-v0"
SOURCE_ISSUE = exposure.SOURCE_ISSUE
DATASET_ID = exposure.DATASET_ID
PROJECT_ID = exposure.PROJECT_ID
PROJECT_PATH = exposure.PROJECT_PATH
COMMIT_SHA = exposure.COMMIT_SHA
REPOSITORY_PATH = exposure.REPOSITORY_PATH
RECEIPT_COMMENT_ID = exposure.RECEIPT_COMMENT_ID
RECEIPT_EXECUTION_SHA = exposure.RECEIPT_EXECUTION_SHA
EXPECTED_BYTE_COUNT = exposure.EXPECTED_BYTE_COUNT
EXPECTED_SHA256 = exposure.EXPECTED_SHA256

EXPECTED_HEADER = (
    "LONGITUDE",
    "LATITUDE",
    "TAXONOMY",
    "MACRO_TAXONOMY",
    "BUILDINGS",
    "DWELLINGS",
    "OCCUPANCY",
    "OCCUPANCY_TYPE",
    "SETTLEMENT_TYPE",
    "AREA_PER_DWELLING_SQM",
    "COST_PER_AREA_EUR",
    "TOTAL_REPL_COST_EUR",
    "COST_STRUCTURAL_EUR",
    "COST_NONSTRUCTURAL_EUR",
    "COST_CONTENTS_EUR",
    "OCCUPANTS_PER_ASSET",
    "OCCUPANTS_PER_ASSET_DAY",
    "OCCUPANTS_PER_ASSET_NIGHT",
    "OCCUPANTS_PER_ASSET_TRANSIT",
    "OCCUPANTS_PER_ASSET_AVERAGE",
    "ID_2",
    "NAME_2",
    "ID_1",
    "NAME_1",
)

NUMERIC_FIELDS = (
    "LONGITUDE",
    "LATITUDE",
    "BUILDINGS",
    "DWELLINGS",
    "AREA_PER_DWELLING_SQM",
    "COST_PER_AREA_EUR",
    "TOTAL_REPL_COST_EUR",
    "COST_STRUCTURAL_EUR",
    "COST_NONSTRUCTURAL_EUR",
    "COST_CONTENTS_EUR",
    "OCCUPANTS_PER_ASSET",
    "OCCUPANTS_PER_ASSET_DAY",
    "OCCUPANTS_PER_ASSET_NIGHT",
    "OCCUPANTS_PER_ASSET_TRANSIT",
    "OCCUPANTS_PER_ASSET_AVERAGE",
)

CANDIDATE_KEY_FIELDS = ("LONGITUDE", "LATITUDE", "TAXONOMY")
_ROW_DIGEST_DOMAIN = b"OpenCatastrophe/EQ1/KosovoExposureRow/v1\x00"
MAX_NUMERIC_UTF8_BYTES = 128
MAX_DECIMAL_ADJUSTED_EXPONENT = 100

# Accepted values have at most 128 coefficient digits and adjusted exponents in
# [-100, 100]. Aligning four such operands requires fewer than 330 significant
# digits, so this fixed context keeps the residual exact with explicit headroom.
DECIMAL_ARITHMETIC_PRECISION = 512
_EXACT_DECIMAL_CONTEXT = Context(
    prec=DECIMAL_ARITHMETIC_PRECISION,
    Emin=-999_999,
    Emax=999_999,
)
_EXACT_DECIMAL_CONTEXT.traps[Inexact] = True
_EXACT_DECIMAL_CONTEXT.traps[Rounded] = True


class ExposureValueSpatialProfileError(RuntimeError):
    """Raised when receipt-bound value/spatial profiling fails closed."""


def _canonical_decimal(value: Decimal) -> str:
    if not value.is_finite():
        raise ExposureValueSpatialProfileError("numeric summary contains non-finite Decimal")
    if value == 0:
        return "0"
    # Decimal.normalize() applies the ambient Context and can silently round
    # accepted high-precision values. Fixed-point formatting without a precision
    # specifier preserves the exact Decimal coefficient/exponent instead.
    text = format(value, "f")
    if "." in text:
        text = text.rstrip("0").rstrip(".")
    return text


def _parse_decimal(value: str, *, field: str) -> Decimal:
    if value == "" or value != value.strip():
        raise ExposureValueSpatialProfileError(f"{field} contains empty or padded numeric value")
    if len(value.encode("utf-8")) > MAX_NUMERIC_UTF8_BYTES:
        raise ExposureValueSpatialProfileError(f"{field} numeric value exceeds bounded policy")
    try:
        number = Decimal(value)
    except InvalidOperation as exc:
        raise ExposureValueSpatialProfileError(f"{field} contains non-decimal value") from exc
    if not number.is_finite():
        raise ExposureValueSpatialProfileError(f"{field} contains non-finite value")
    if len(number.as_tuple().digits) > MAX_NUMERIC_UTF8_BYTES:
        raise ExposureValueSpatialProfileError(f"{field} numeric precision exceeds bounded policy")
    if number != 0 and abs(number.adjusted()) > MAX_DECIMAL_ADJUSTED_EXPONENT:
        raise ExposureValueSpatialProfileError(f"{field} numeric exponent exceeds bounded policy")
    return number


def _replacement_cost_residual(parsed: dict[str, Decimal]) -> Decimal:
    """Return the exact replacement-cost component residual independent of ambient context."""

    try:
        with localcontext(_EXACT_DECIMAL_CONTEXT) as context:
            component_sum = context.add(
                parsed["COST_STRUCTURAL_EUR"],
                parsed["COST_NONSTRUCTURAL_EUR"],
            )
            component_sum = context.add(component_sum, parsed["COST_CONTENTS_EUR"])
            return context.subtract(parsed["TOTAL_REPL_COST_EUR"], component_sum)
    except (Inexact, Rounded) as exc:
        raise ExposureValueSpatialProfileError(
            "replacement-cost residual exceeds exact decimal working bound"
        ) from exc


def _row_identity(row: list[str]) -> bytes:
    digest = hashlib.sha256()
    digest.update(_ROW_DIGEST_DOMAIN)
    for value in row:
        encoded = value.encode("utf-8")
        digest.update(len(encoded).to_bytes(8, "big"))
        digest.update(encoded)
    return digest.digest()


def _numeric_summary(values: list[Decimal]) -> dict[str, Any]:
    if not values:
        raise ExposureValueSpatialProfileError("numeric summary is empty")
    return {
        "minimum": _canonical_decimal(min(values)),
        "maximum": _canonical_decimal(max(values)),
        "negative_count": sum(value < 0 for value in values),
        "zero_count": sum(value == 0 for value in values),
        "positive_count": sum(value > 0 for value in values),
        "finite_count": len(values),
    }


def _duplicate_summary(keys: list[bytes]) -> dict[str, int]:
    unique = len(set(keys))
    return {
        "record_count": len(keys),
        "unique_identity_count": unique,
        "duplicate_record_count": len(keys) - unique,
    }


def profile_verified_exposure_value_spatial(
    raw: bytes,
    *,
    expected_byte_count: int,
    expected_sha256: str,
) -> dict[str, Any]:
    """Verify a caller-bound receipt, then emit identity-neutral diagnostics."""

    try:
        structure = exposure.profile_verified_csv_bytes(
            raw,
            expected_byte_count=expected_byte_count,
            expected_sha256=expected_sha256,
        )
    except exposure.ExposureProfileError as exc:
        raise ExposureValueSpatialProfileError(
            "verified receipt/structure gate failed"
        ) from exc
    if tuple(structure["header"]) != EXPECTED_HEADER:
        raise ExposureValueSpatialProfileError(
            "verified Kosovo exposure header drifted from exact reviewed contract"
        )

    encoding = structure["parser"]["encoding"]
    try:
        text = raw.decode(encoding)
    except UnicodeDecodeError as exc:  # defensive; base profiler already checked
        raise ExposureValueSpatialProfileError("verified exposure decode drifted") from exc

    reader = csv.reader(io.StringIO(text, newline=""), delimiter=",", strict=True)
    try:
        header = next(reader)
    except (StopIteration, csv.Error) as exc:  # defensive; base profiler already checked
        raise ExposureValueSpatialProfileError("verified exposure header cannot be re-read") from exc
    if tuple(header) != EXPECTED_HEADER:
        raise ExposureValueSpatialProfileError("verified exposure header changed during re-read")

    index = {name: position for position, name in enumerate(header)}
    numeric_values: dict[str, list[Decimal]] = {name: [] for name in NUMERIC_FIELDS}
    full_row_identities: list[bytes] = []
    full_row_identity_rows: dict[bytes, tuple[str, ...]] = {}
    candidate_identities: list[bytes] = []
    candidate_identity_rows: dict[bytes, tuple[str, ...]] = {}
    component_nonzero_residual_count = 0
    component_max_abs_residual = Decimal(0)
    record_count = 0

    try:
        for row in reader:
            if len(row) != len(header):
                raise ExposureValueSpatialProfileError("verified exposure contains ragged row")
            record_count += 1

            row_identity = _row_identity(row)
            row_tuple = tuple(row)
            existing = full_row_identity_rows.get(row_identity)
            if existing is not None and existing != row_tuple:
                raise ExposureValueSpatialProfileError("SHA-256 collision in full-row identity")
            full_row_identity_rows[row_identity] = row_tuple
            full_row_identities.append(row_identity)

            candidate_row = [row[index[name]] for name in CANDIDATE_KEY_FIELDS]
            candidate_identity = _row_identity(candidate_row)
            candidate_tuple = tuple(candidate_row)
            candidate_existing = candidate_identity_rows.get(candidate_identity)
            if candidate_existing is not None and candidate_existing != candidate_tuple:
                raise ExposureValueSpatialProfileError(
                    "SHA-256 collision in candidate-key identity"
                )
            candidate_identity_rows[candidate_identity] = candidate_tuple
            candidate_identities.append(candidate_identity)

            parsed: dict[str, Decimal] = {}
            for field in NUMERIC_FIELDS:
                number = _parse_decimal(row[index[field]], field=field)
                parsed[field] = number
                numeric_values[field].append(number)

            residual = _replacement_cost_residual(parsed)
            if residual != 0:
                component_nonzero_residual_count += 1
                component_max_abs_residual = max(
                    component_max_abs_residual,
                    residual.copy_abs(),
                )
    except csv.Error as exc:
        raise ExposureValueSpatialProfileError("verified exposure CSV re-read failed") from exc

    if record_count != structure["record_count"]:
        raise ExposureValueSpatialProfileError("record count drifted between verified parse passes")

    longitude = numeric_values["LONGITUDE"]
    latitude = numeric_values["LATITUDE"]
    coordinate_range_counts = {
        "longitude_outside_minus180_plus180_count": sum(
            value < -180 or value > 180 for value in longitude
        ),
        "latitude_outside_minus90_plus90_count": sum(
            value < -90 or value > 90 for value in latitude
        ),
    }

    return {
        "schema_version": SCHEMA_VERSION,
        "record_count": record_count,
        "numeric_fields": {
            field: _numeric_summary(numeric_values[field]) for field in NUMERIC_FIELDS
        },
        "coordinate_range_diagnostics": coordinate_range_counts,
        "full_row_duplicates": _duplicate_summary(full_row_identities),
        "candidate_key_diagnostics": {
            "fields": list(CANDIDATE_KEY_FIELDS),
            "provider_business_key_authorized": False,
            **_duplicate_summary(candidate_identities),
        },
        "replacement_cost_component_diagnostic": {
            "equation_measured": (
                "TOTAL_REPL_COST_EUR - "
                "(COST_STRUCTURAL_EUR + COST_NONSTRUCTURAL_EUR + COST_CONTENTS_EUR)"
            ),
            "zero_residual_count": record_count - component_nonzero_residual_count,
            "nonzero_residual_count": component_nonzero_residual_count,
            "maximum_absolute_residual_eur": _canonical_decimal(component_max_abs_residual),
            "semantic_identity_authorized": False,
        },
        "crs_identifier_verified": False,
        "valuation_vintage_verified": False,
        "sentinel_semantics_verified": False,
        "row_business_key_verified": False,
        "raw_rows_returned": False,
        "external_bytes_persisted": False,
        "publication_authorized": False,
        "model_use_authorized": False,
    }


def acquire_and_profile_kosovo_exposure_value_spatial(
    *,
    opener: Any | None = None,
    monotonic: Any = time.monotonic,
) -> dict[str, Any]:
    """Acquire only the frozen Kosovo CSV and run the receipt-bound summary profiler."""

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
        raise ExposureValueSpatialProfileError("trusted Kosovo exposure target is invalid") from exc

    file_url = raw_file_api_url(target)
    request = urllib.request.Request(
        file_url,
        headers={
            "Accept": "text/csv,text/plain;q=0.9",
            "User-Agent": "OpenCatastrophe-EFEHR-value-spatial-profile-v0",
        },
        method="GET",
    )
    try:
        with open_response(request, timeout=_remaining(deadline, monotonic)) as response:
            _validate_exact_response(response, file_url)
            raw = _read_bounded(
                response,
                deadline=deadline,
                maximum=EXPECTED_BYTE_COUNT,
                monotonic=monotonic,
            )
    except ExposureValueSpatialProfileError:
        raise
    except EfehrAcquisitionError as exc:
        raise ExposureValueSpatialProfileError(
            "Kosovo exposure value/spatial retrieval failed closed"
        ) from exc
    except (OSError, urllib.error.URLError, urllib.error.HTTPError, TimeoutError) as exc:
        raise ExposureValueSpatialProfileError(
            f"Kosovo exposure value/spatial retrieval failed: {type(exc).__name__}"
        ) from exc

    summary = profile_verified_exposure_value_spatial(
        raw,
        expected_byte_count=EXPECTED_BYTE_COUNT,
        expected_sha256=EXPECTED_SHA256,
    )
    return {
        "schema_version": summary["schema_version"],
        "source_issue": SOURCE_ISSUE,
        "dataset_id": DATASET_ID,
        "project_id": PROJECT_ID,
        "project_path": PROJECT_PATH,
        "commit_sha": COMMIT_SHA,
        "repository_path": REPOSITORY_PATH,
        "receipt_comment_id": RECEIPT_COMMENT_ID,
        "receipt_execution_sha": RECEIPT_EXECUTION_SHA,
        "byte_count": EXPECTED_BYTE_COUNT,
        "sha256": EXPECTED_SHA256,
        "summary": summary,
        "external_bytes_persisted": False,
        "publication_authorized": False,
        "model_use_authorized": False,
    }
