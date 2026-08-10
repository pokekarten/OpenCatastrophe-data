# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Freeze the scientific acquisition intent for the Dresden holdout.

This module intentionally does not download external bytes. Provider clients,
authentication flows and storage locations may change; the scientific meaning
of what must be acquired must not.

The initial intent records immutable source/product/time requirements and the
metadata that must be resolved before holdout target values are inspected.
Finalization accepts raw metadata inputs, invokes the repository-owned GloFAS
grid selector itself, freezes the PEGELONLINE sampling interval, and emits a
canonical hashable execution plan.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any, Iterable

from scripts.hydrology_grid_matching import GlofasGridCell, select_dresden_glofas_grid_cell
from scripts.hydrology_holdout import required_pegelonline_local_coverage
from scripts.hydrology_window import (
    DRESDEN_HOLDOUT_EXPECTED_DAYS,
    DRESDEN_HOLDOUT_FIRST_GLOFAS_TIMESTAMP_UTC,
    DRESDEN_HOLDOUT_LAST_GLOFAS_TIMESTAMP_UTC,
    expected_observations_per_24h,
)

PROFILE_VERSION = "1.0.0"
PEGELONLINE_MANIFEST = "manifests/wsv.pegelonline.elbe-dresden-discharge.2020-2023.json"
PEGELONLINE_REVIEW = "docs/source-reviews/wsv-pegelonline-elbe-dresden-discharge-2020-2023.md"
GLOFAS_MANIFEST = "manifests/copernicus.cems.glofas-historical.json"
GLOFAS_REVIEW = "docs/source-reviews/copernicus-cems-glofas-historical.md"
PEGELONLINE_STATION_NUMBER = "501060"
PEGELONLINE_STATION_UUID = "70272185-b2b3-4178-96b8-43bea330dcae"
PEGELONLINE_VARIABLE = "Q"
GLOFAS_DATASET = "cems-glofas-historical"
GLOFAS_SYSTEM_VERSION = "version_4_0"
GLOFAS_HYDROLOGICAL_MODEL = "lisflood"
GLOFAS_PRODUCT_TYPE = "consolidated"
GLOFAS_VARIABLE = "river_discharge_in_the_last_24_hours"
GLOFAS_GRID_DEGREES = 0.05
SECONDS_PER_MINUTE = 60


class AcquisitionIntentError(ValueError):
    """Raised when acquisition intent cannot be frozen safely."""


def acquisition_intent() -> dict[str, Any]:
    """Return immutable pre-target source and metadata requirements."""

    pegel_start, pegel_end = required_pegelonline_local_coverage()
    return {
        "profile_version": PROFILE_VERSION,
        "purpose": "dresden-pegelonline-glofas-v4-temporal-holdout",
        "phase": "metadata_resolution",
        "target_values_must_not_be_inspected": True,
        "pegelonline": {
            "manifest": PEGELONLINE_MANIFEST,
            "source_review": PEGELONLINE_REVIEW,
            "station_number": PEGELONLINE_STATION_NUMBER,
            "station_uuid": PEGELONLINE_STATION_UUID,
            "variable": PEGELONLINE_VARIABLE,
            "time_convention": "fixed_CET_UTC_plus_01_year_round",
            "required_local_coverage_start": pegel_start.isoformat(),
            "required_local_coverage_end_exclusive": pegel_end.isoformat(),
            "sampling_interval": {
                "status": "unresolved",
                "must_freeze_from": "retrieved_series_metadata.equidistance_minutes",
            },
        },
        "glofas": {
            "manifest": GLOFAS_MANIFEST,
            "source_review": GLOFAS_REVIEW,
            "dataset": GLOFAS_DATASET,
            "system_version": GLOFAS_SYSTEM_VERSION,
            "hydrological_model": GLOFAS_HYDROLOGICAL_MODEL,
            "product_type": GLOFAS_PRODUCT_TYPE,
            "variable": GLOFAS_VARIABLE,
            "grid_degrees": GLOFAS_GRID_DEGREES,
            "first_end_label_utc": DRESDEN_HOLDOUT_FIRST_GLOFAS_TIMESTAMP_UTC.isoformat(),
            "last_end_label_utc": DRESDEN_HOLDOUT_LAST_GLOFAS_TIMESTAMP_UTC.isoformat(),
            "expected_daily_labels": DRESDEN_HOLDOUT_EXPECTED_DAYS,
            "grid_cell": {
                "status": "unresolved",
                "must_freeze_with": "scripts/hydrology_grid_matching.py",
                "requires_upstream_area_ancillary": True,
            },
        },
        "required_external_receipt": {
            "per_file": ["logical_identity", "byte_size", "sha256"],
            "per_request": ["exact_request", "retrieved_at"],
            "forbidden_in_git": ["credentials", "cookies", "signed_urls", "external_dataset_bytes"],
        },
        "hard_stops": [
            "do_not_load_holdout_target_values_before_sampling_interval_and_grid_cell_are_frozen",
            "do_not_relax_grid_time_or_completeness_rules_after_target_inspection",
            "do_not_commit_external_dataset_bytes_without_separate_exact_asset_admission",
        ],
    }


def finalize_acquisition_intent(
    *,
    pegelonline_station_number: str,
    pegelonline_station_uuid: str,
    pegelonline_equidistance_minutes: int,
    station_latitude: float | int,
    station_longitude: float | int,
    glofas_candidate_cells: Iterable[GlofasGridCell],
) -> dict[str, Any]:
    """Freeze metadata-only resolution and return the executable acquisition intent.

    PEGELONLINE documents ``equidistance`` in minutes. The function accepts that
    source-native unit explicitly, converts it once to seconds for the repository
    window utilities, and records both values in the frozen intent. Retrieved
    station identity must match the preregistered Dresden station before its
    coordinates may influence GloFAS grid selection.

    The function deliberately invokes the canonical grid selector itself rather
    than accepting a caller-constructed match receipt.
    """

    if pegelonline_station_number != PEGELONLINE_STATION_NUMBER:
        raise AcquisitionIntentError("PEGELONLINE station_number does not match the frozen Dresden station")
    if pegelonline_station_uuid != PEGELONLINE_STATION_UUID:
        raise AcquisitionIntentError("PEGELONLINE station_uuid does not match the frozen Dresden station")
    if type(pegelonline_equidistance_minutes) is not int or pegelonline_equidistance_minutes <= 0:
        raise AcquisitionIntentError("PEGELONLINE equidistance_minutes must be a positive integer")
    pegelonline_sampling_interval_seconds = pegelonline_equidistance_minutes * SECONDS_PER_MINUTE

    try:
        expected_source_observations_per_day = expected_observations_per_24h(
            pegelonline_sampling_interval_seconds
        )
    except ValueError as exc:
        raise AcquisitionIntentError(f"invalid PEGELONLINE sampling interval: {exc}") from exc

    try:
        grid_match = select_dresden_glofas_grid_cell(
            station_latitude=station_latitude,
            station_longitude=station_longitude,
            candidates=glofas_candidate_cells,
        )
    except ValueError as exc:
        raise AcquisitionIntentError(f"unable to freeze GloFAS grid cell: {exc}") from exc

    plan = acquisition_intent()
    plan["phase"] = "target_acquisition"
    plan["target_values_must_not_be_inspected"] = False
    plan["metadata_resolution"] = {
        "pegelonline_station_number": pegelonline_station_number,
        "pegelonline_station_uuid": pegelonline_station_uuid,
        "pegelonline_equidistance_minutes": pegelonline_equidistance_minutes,
        "pegelonline_sampling_interval_seconds": pegelonline_sampling_interval_seconds,
        "expected_source_observations_per_24h": expected_source_observations_per_day,
        "station_coordinate_wgs84": {
            "latitude": float(station_latitude),
            "longitude": float(station_longitude),
        },
        "glofas_grid_match": {
            "latitude": grid_match.cell.latitude,
            "longitude": grid_match.cell.longitude,
            "upstream_area_km2": grid_match.cell.upstream_area_km2,
            "angular_distance_degrees": grid_match.angular_distance_degrees,
            "relative_drainage_area_mismatch": grid_match.relative_drainage_area_mismatch,
        },
    }
    plan["pegelonline"]["sampling_interval"] = {
        "status": "frozen",
        "equidistance_minutes": pegelonline_equidistance_minutes,
        "seconds": pegelonline_sampling_interval_seconds,
        "expected_observations_per_24h": expected_source_observations_per_day,
        "source": "retrieved_series_metadata.equidistance_minutes",
    }
    plan["glofas"]["grid_cell"] = {
        "status": "frozen",
        "latitude": grid_match.cell.latitude,
        "longitude": grid_match.cell.longitude,
        "upstream_area_km2": grid_match.cell.upstream_area_km2,
    }
    plan["hard_stops"] = [
        "do_not_relax_grid_time_or_completeness_rules_after_target_inspection",
        "do_not_commit_external_dataset_bytes_without_separate_exact_asset_admission",
        "acquired_bytes_must_receive_exact_size_sha256_and_manifest_artifact_identity_before_model_use",
    ]
    return plan


def canonical_intent_bytes(intent: dict[str, Any]) -> bytes:
    """Return stable canonical JSON bytes for provenance hashing."""

    if type(intent) is not dict:
        raise AcquisitionIntentError("intent must be an object")
    try:
        return json.dumps(
            intent,
            ensure_ascii=False,
            allow_nan=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise AcquisitionIntentError(f"intent is not canonical JSON data: {exc}") from exc


def acquisition_intent_sha256(intent: dict[str, Any]) -> str:
    """Return the stable SHA-256 identity of one acquisition intent."""

    return hashlib.sha256(canonical_intent_bytes(intent)).hexdigest()
