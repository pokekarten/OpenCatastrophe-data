# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Receipt-bound exact-Decimal Greece project-186/project-269 comparison.

This is deliberately an offline comparator. A trusted caller supplies bytes;
this module proves the frozen receipt identities before parsing and emits only
bounded aggregate comparison evidence. It has no network or action surface and
never returns provider rows or literal business values.

A passing comparison does not itself verify source-to-runtime lineage,
replacement-cost semantics, CRS/EPSG, insured-value semantics, publication,
model use, benchmark agreement, independent validation, or holdout status.
"""

from __future__ import annotations

import csv
import hashlib
import io
from decimal import Decimal, Inexact, Rounded, localcontext
from typing import Any

from scripts import profile_efehr_kosovo_exposure as generic_csv
from scripts import profile_efehr_kosovo_exposure_value_spatial as source_value

SCHEMA_VERSION = "oc-esrm20-greece-source-runtime-decimal-comparison-v0"
SOURCE_ISSUE = 285
PARENT_CONSUMER_ISSUE = 287
SOURCE_PROJECT_ID = 186
SOURCE_PROJECT_PATH = "efehr/esrm20_exposure"
SOURCE_COMMIT_SHA = "900433ada80fbb424c0976c34d72eeef97bab1af"
SOURCE_RECEIPT_COMMENT_ID = 5423879080
SOURCE_RECEIPT_EXECUTION_SHA = "0babfcf9aa9b6f6ede911217f99e2252428e95db"
RUNTIME_PROJECT_ID = 269
RUNTIME_PROJECT_PATH = "efehr/esrm20"
RUNTIME_COMMIT_SHA = "05f83bbc9df81d02ee8ddb1801d9d781355ce783"
RUNTIME_RECEIPT_COMMENT_ID = 5397480571
RUNTIME_RECEIPT_EXECUTION_SHA = "4b1d3c41a5df739b9686303eb753577ca39ec58e"

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
    "id_3",
    "id_3_left",
    "name_3",
    "id_3_right",
    "id_1",
    "name_1",
    "id_2",
    "name_2",
)

SECTOR_SPECS: dict[str, dict[str, Any]] = {
    "commercial": {
        "source_path": "_exposure_models/Exposure_Model_Greece_Com.csv",
        "source_byte_count": 12_578_244,
        "source_sha256": (
            "54c689673ba7160a2cf116af44cae20fe4c74c69ebf3bf192c7dd1bccfc94125"
        ),
        "runtime_path": "Exposure/OQ_Exposure_Input_Greece_Com.csv",
        "runtime_byte_count": 7_672_810,
        "runtime_sha256": (
            "2281f079a6e0b2215fab696d442f9d98b9b0ba94a2b4b24f23f1fff4018d1b57"
        ),
        "expected_record_count": 37_290,
    },
    "industrial": {
        "source_path": "_exposure_models/Exposure_Model_Greece_Ind.csv",
        "source_byte_count": 4_600_971,
        "source_sha256": (
            "491fe2b4dfbb36418582c41818a41c8e521e64b5a4b6c369816d175469b55165"
        ),
        "runtime_path": "Exposure/OQ_Exposure_Input_Greece_Ind.csv",
        "runtime_byte_count": 2_822_653,
        "runtime_sha256": (
            "ad6698199d84002d017b41668dc204a2d53835a4b2429bc7e8eea56b328549c7"
        ),
        "expected_record_count": 13_264,
    },
    "residential": {
        "source_path": "_exposure_models/Exposure_Model_Greece_Res.csv",
        "source_byte_count": 9_011_434,
        "source_sha256": (
            "1104b73d2d4e5b5b89d8c3a9575fe1f348662dd7f706c7a322c70a3240dc4e3b"
        ),
        "runtime_path": "Exposure/OQ_Exposure_Input_Greece_Res.csv",
        "runtime_byte_count": 5_263_604,
        "runtime_sha256": (
            "928ac7f069dfc3181a936f73caafb951a5c2437f70379fa29518c002bbd3ef28"
        ),
        "expected_record_count": 24_057,
    },
}

# Literal projection identity only; never promoted to a provider business key.
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

# COST_STRUCTURAL_EUR is intentionally a falsification candidate, not a
# substitute for the predeclared TOTAL_REPL_COST_EUR lineage candidate.
NUMERIC_FIELD_PAIRS = (
    ("BUILDINGS", "number", "projection_candidate"),
    (
        "TOTAL_REPL_COST_EUR",
        "structural",
        "total_replacement_cost_lineage_candidate",
    ),
    (
        "COST_STRUCTURAL_EUR",
        "structural",
        "structural_component_falsification_candidate",
    ),
    ("OCCUPANTS_PER_ASSET_DAY", "day", "projection_candidate"),
    ("OCCUPANTS_PER_ASSET_NIGHT", "night", "projection_candidate"),
    ("OCCUPANTS_PER_ASSET_TRANSIT", "transit", "projection_candidate"),
)

_KEY_DOMAIN = b"OpenCatastrophe/EQ1/GreeceExposureProjectionKey/v1\x00"
_KEYSET_DOMAIN = b"OpenCatastrophe/EQ1/GreeceExposureProjectionKeySet/v1\x00"
_RELATION_DOMAIN = b"OpenCatastrophe/EQ1/GreeceExposureDecimalRelation/v1\x00"


class GreeceExposureRuntimeComparisonError(RuntimeError):
    """Raised when a receipt-bound Greece comparison cannot be proved safely."""


def _validate_sector(sector: object) -> dict[str, Any]:
    if type(sector) is not str or sector not in SECTOR_SPECS:
        raise GreeceExposureRuntimeComparisonError(
            "sector left frozen Greece comparison set"
        )
    return SECTOR_SPECS[sector]


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
        key_digest = _framed_digest(_KEY_DOMAIN, key)
        previous = framed.get(key_digest)
        if previous is not None and previous != key:
            raise GreeceExposureRuntimeComparisonError(
                "SHA-256 collision in comparison key"
            )
        framed[key_digest] = key
    digest = hashlib.sha256()
    digest.update(_KEYSET_DOMAIN)
    for key_digest in sorted(framed):
        digest.update(key_digest)
    return digest.hexdigest()


def _parse_verified_rows(
    raw: bytes,
    *,
    expected_byte_count: int,
    expected_sha256: str,
    expected_header: tuple[str, ...],
    expected_record_count: int,
    label: str,
) -> list[dict[str, str]]:
    try:
        profile = generic_csv.profile_verified_csv_bytes(
            raw,
            expected_byte_count=expected_byte_count,
            expected_sha256=expected_sha256,
        )
    except generic_csv.ExposureProfileError as exc:
        raise GreeceExposureRuntimeComparisonError(
            f"{label} receipt/structure gate failed"
        ) from exc
    if tuple(profile.get("header", ())) != expected_header:
        raise GreeceExposureRuntimeComparisonError(f"{label} header drifted")
    if profile.get("record_count") != expected_record_count:
        raise GreeceExposureRuntimeComparisonError(f"{label} record count drifted")
    if profile.get("external_bytes_persisted") is not False:
        raise GreeceExposureRuntimeComparisonError(
            f"{label} profile widened persistence authority"
        )
    if profile.get("raw_rows_returned") is not False:
        raise GreeceExposureRuntimeComparisonError(
            f"{label} profile exposed raw rows"
        )

    try:
        text = raw.decode(profile["parser"]["encoding"])
    except UnicodeDecodeError as exc:
        raise GreeceExposureRuntimeComparisonError(f"{label} decode drifted") from exc
    reader = csv.DictReader(io.StringIO(text, newline=""), delimiter=",", strict=True)
    if tuple(reader.fieldnames or ()) != expected_header:
        raise GreeceExposureRuntimeComparisonError(
            f"{label} header changed during re-read"
        )
    rows: list[dict[str, str]] = []
    try:
        for row in reader:
            if None in row or set(row) != set(expected_header):
                raise GreeceExposureRuntimeComparisonError(
                    f"{label} contains ragged row"
                )
            if any(type(value) is not str for value in row.values()):
                raise GreeceExposureRuntimeComparisonError(
                    f"{label} contains non-text field"
                )
            rows.append({field: row[field] for field in expected_header})
    except csv.Error as exc:
        raise GreeceExposureRuntimeComparisonError(
            f"{label} CSV re-read failed"
        ) from exc
    if len(rows) != expected_record_count:
        raise GreeceExposureRuntimeComparisonError(
            f"{label} record count changed during re-read"
        )
    return rows


def _build_unique_bridge(
    rows: list[dict[str, str]], *, fields: tuple[str, ...], label: str
) -> dict[tuple[str, ...], dict[str, str]]:
    bridge: dict[tuple[str, ...], dict[str, str]] = {}
    for row in rows:
        key = tuple(row[field] for field in fields)
        if key in bridge:
            raise GreeceExposureRuntimeComparisonError(
                f"{label} comparison key is not unique"
            )
        bridge[key] = row
    return bridge


def _exact_abs_difference(left: Decimal, right: Decimal) -> Decimal:
    try:
        with localcontext(source_value._EXACT_DECIMAL_CONTEXT) as context:
            return abs(context.subtract(left, right))
    except (Inexact, Rounded) as exc:
        raise GreeceExposureRuntimeComparisonError(
            "decimal difference exceeded exact working bound"
        ) from exc


def _relation_sha256(
    sector: str,
    source_field: str,
    runtime_field: str,
    rows: list[tuple[tuple[str, ...], Decimal, Decimal]],
) -> str:
    digest = hashlib.sha256()
    digest.update(_RELATION_DOMAIN)
    for discriminator in (sector, source_field, runtime_field):
        encoded = discriminator.encode("ascii")
        digest.update(len(encoded).to_bytes(8, "big"))
        digest.update(encoded)
    framed: list[tuple[bytes, str, str]] = []
    seen: dict[bytes, tuple[str, ...]] = {}
    for key, source_number, runtime_number in rows:
        key_digest = _framed_digest(_KEY_DOMAIN, key)
        previous = seen.get(key_digest)
        if previous is not None and previous != key:
            raise GreeceExposureRuntimeComparisonError(
                "SHA-256 collision in relation key"
            )
        seen[key_digest] = key
        framed.append(
            (
                key_digest,
                source_value._canonical_decimal(source_number),
                source_value._canonical_decimal(runtime_number),
            )
        )
    for key_digest, source_text, runtime_text in sorted(
        framed, key=lambda item: item[0]
    ):
        digest.update(key_digest)
        for value in (source_text, runtime_text):
            encoded = value.encode("ascii")
            digest.update(len(encoded).to_bytes(8, "big"))
            digest.update(encoded)
    return digest.hexdigest()


def _identity(
    *,
    canonical: bool,
    project_id: int,
    project_path: str,
    commit_sha: str,
    repository_path: str,
    byte_count: int,
    sha256: str,
) -> dict[str, Any]:
    result: dict[str, Any] = {
        "canonical_receipt_verified": canonical,
        "byte_count": byte_count,
        "sha256": sha256,
    }
    if canonical:
        result.update(
            {
                "project_id": project_id,
                "project_path": project_path,
                "commit_sha": commit_sha,
                "repository_path": repository_path,
            }
        )
    return result


def compare_verified_sector_bytes(
    source_raw: bytes,
    runtime_raw: bytes,
    *,
    sector: str,
    source_expected_byte_count: int | None = None,
    source_expected_sha256: str | None = None,
    runtime_expected_byte_count: int | None = None,
    runtime_expected_sha256: str | None = None,
    expected_record_count: int | None = None,
) -> dict[str, Any]:
    """Compare one Greece sector after exact caller-bound receipt gates."""

    spec = _validate_sector(sector)
    source_count = (
        spec["source_byte_count"]
        if source_expected_byte_count is None
        else source_expected_byte_count
    )
    source_sha = (
        spec["source_sha256"]
        if source_expected_sha256 is None
        else source_expected_sha256
    )
    runtime_count = (
        spec["runtime_byte_count"]
        if runtime_expected_byte_count is None
        else runtime_expected_byte_count
    )
    runtime_sha = (
        spec["runtime_sha256"]
        if runtime_expected_sha256 is None
        else runtime_expected_sha256
    )
    record_count = (
        spec["expected_record_count"]
        if expected_record_count is None
        else expected_record_count
    )
    if (
        type(record_count) is not int
        or isinstance(record_count, bool)
        or record_count < 1
    ):
        raise GreeceExposureRuntimeComparisonError(
            "expected record count is invalid"
        )

    source_rows = _parse_verified_rows(
        source_raw,
        expected_byte_count=source_count,
        expected_sha256=source_sha,
        expected_header=SOURCE_HEADER,
        expected_record_count=record_count,
        label=f"{sector} source exposure",
    )
    runtime_rows = _parse_verified_rows(
        runtime_raw,
        expected_byte_count=runtime_count,
        expected_sha256=runtime_sha,
        expected_header=RUNTIME_HEADER,
        expected_record_count=record_count,
        label=f"{sector} runtime exposure",
    )

    source_canonical = (
        source_count == spec["source_byte_count"]
        and source_sha == spec["source_sha256"]
    )
    runtime_canonical = (
        runtime_count == spec["runtime_byte_count"]
        and runtime_sha == spec["runtime_sha256"]
    )

    source_key_fields = tuple(left for left, _right in KEY_FIELD_PAIRS)
    runtime_key_fields = tuple(right for _left, right in KEY_FIELD_PAIRS)
    source_bridge = _build_unique_bridge(
        source_rows, fields=source_key_fields, label="source"
    )
    runtime_bridge = _build_unique_bridge(
        runtime_rows, fields=runtime_key_fields, label="runtime"
    )
    source_keys = set(source_bridge)
    runtime_keys = set(runtime_bridge)
    source_keyset_sha256 = _keyset_sha256(source_keys)
    runtime_keyset_sha256 = _keyset_sha256(runtime_keys)
    if source_keys != runtime_keys:
        raise GreeceExposureRuntimeComparisonError(
            "source/runtime comparison key sets differ"
        )
    if source_keyset_sha256 != runtime_keyset_sha256:
        raise GreeceExposureRuntimeComparisonError(
            "source/runtime comparison key fingerprints differ"
        )

    comparisons: list[dict[str, Any]] = []
    for source_field, runtime_field, role in NUMERIC_FIELD_PAIRS:
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
                raise GreeceExposureRuntimeComparisonError(
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
                "role": role,
                "record_count": record_count,
                "exact_decimal_equal_count": equal_count,
                "non_equal_count": record_count - equal_count,
                "all_exact_decimal_equal": equal_count == record_count,
                "maximum_absolute_difference": source_value._canonical_decimal(
                    max_abs_difference
                ),
                "relation_sha256": _relation_sha256(
                    sector, source_field, runtime_field, relation_rows
                ),
            }
        )

    return {
        "schema_version": SCHEMA_VERSION,
        "sector": sector,
        "record_count": record_count,
        "canonical_receipt_pair_verified": source_canonical and runtime_canonical,
        "source_identity": _identity(
            canonical=source_canonical,
            project_id=SOURCE_PROJECT_ID,
            project_path=SOURCE_PROJECT_PATH,
            commit_sha=SOURCE_COMMIT_SHA,
            repository_path=spec["source_path"],
            byte_count=source_count,
            sha256=source_sha,
        ),
        "runtime_identity": _identity(
            canonical=runtime_canonical,
            project_id=RUNTIME_PROJECT_ID,
            project_path=RUNTIME_PROJECT_PATH,
            commit_sha=RUNTIME_COMMIT_SHA,
            repository_path=spec["runtime_path"],
            byte_count=runtime_count,
            sha256=runtime_sha,
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
        "source_runtime_lineage_verified": False,
        "total_replacement_cost_to_structural_verified": False,
        "cost_structural_to_structural_verified": False,
        "source_crs_datum_epsg_verified": False,
        "insured_value_semantics_verified": False,
        "benchmark_agreement_inspected": False,
        "independent_validation_established": False,
        "holdout_status_established": False,
        "external_bytes_persisted": False,
        "raw_rows_returned": False,
        "publication_authorized": False,
        "model_use_authorized": False,
    }


def compare_verified_bundle_bytes(
    source_raw_by_sector: dict[str, bytes],
    runtime_raw_by_sector: dict[str, bytes],
) -> dict[str, Any]:
    """Compare exactly the canonical Com/Ind/Res receipt bundle, offline."""

    expected = set(SECTOR_SPECS)
    if type(source_raw_by_sector) is not dict or set(source_raw_by_sector) != expected:
        raise GreeceExposureRuntimeComparisonError(
            "source bundle left frozen sector set"
        )
    if type(runtime_raw_by_sector) is not dict or set(runtime_raw_by_sector) != expected:
        raise GreeceExposureRuntimeComparisonError(
            "runtime bundle left frozen sector set"
        )
    sectors = [
        compare_verified_sector_bytes(
            source_raw_by_sector[sector],
            runtime_raw_by_sector[sector],
            sector=sector,
        )
        for sector in SECTOR_SPECS
    ]
    if not all(item["canonical_receipt_pair_verified"] is True for item in sectors):
        raise GreeceExposureRuntimeComparisonError(
            "canonical Greece receipt bundle was not proven"
        )
    return {
        "schema_version": SCHEMA_VERSION,
        "source_issue": SOURCE_ISSUE,
        "parent_consumer_issue": PARENT_CONSUMER_ISSUE,
        "source_receipt_comment_id": SOURCE_RECEIPT_COMMENT_ID,
        "source_receipt_execution_sha": SOURCE_RECEIPT_EXECUTION_SHA,
        "runtime_receipt_comment_id": RUNTIME_RECEIPT_COMMENT_ID,
        "runtime_receipt_execution_sha": RUNTIME_RECEIPT_EXECUTION_SHA,
        "canonical_receipt_bundle_verified": True,
        "sectors": sectors,
        "source_runtime_lineage_verified": False,
        "total_replacement_cost_to_structural_verified": False,
        "cost_structural_to_structural_verified": False,
        "source_crs_datum_epsg_verified": False,
        "insured_value_semantics_verified": False,
        "benchmark_agreement_inspected": False,
        "independent_validation_established": False,
        "holdout_status_established": False,
        "external_bytes_persisted": False,
        "raw_rows_returned": False,
        "publication_authorized": False,
        "model_use_authorized": False,
    }
