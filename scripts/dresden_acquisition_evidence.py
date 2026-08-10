# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Exact pre-admission acquisition evidence for the Dresden hydrology pilot.

The frozen acquisition intent defines what may be acquired. Authoritative
builders in this module fingerprint real external files themselves and bind the
complete GloFAS candidate set used for deterministic grid selection. Serialized
validators remain pure and never claim that a caller-supplied digest proves
bytes were observed by the builder.

External provider bytes stay outside Git. Public evidence contains only
canonical ``external://`` identities, byte sizes, SHA-256 digests, timestamps,
candidate metadata and intent/evidence hashes.
"""

from __future__ import annotations

import hashlib
import json
import math
import os
import re
import stat
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable

from scripts.dresden_acquisition_intent import (
    GLOFAS_MANIFEST,
    PEGELONLINE_MANIFEST,
    AcquisitionIntentError,
    acquisition_intent,
    acquisition_intent_sha256,
)
from scripts.hydrology_grid_matching import (
    GlofasGridCell,
    GridMatchError,
    select_dresden_glofas_grid_cell,
)

PROFILE_VERSION = "2.0.0"
SHA256_RE = re.compile(r"^[a-f0-9]{64}$")
EXTERNAL_RE = re.compile(r"^external://[A-Za-z0-9][A-Za-z0-9._/-]*$")
RFC3339_RE = re.compile(
    r"^\d{4}-\d{2}-\d{2}[Tt]\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:[Zz]|[+-]\d{2}:\d{2})$"
)
ARTIFACT_KEYS = {"byte_size", "sha256", "storage_reference"}
CANDIDATE_KEYS = {"latitude", "longitude", "upstream_area_km2"}
METADATA_ARTIFACT_KEYS = {
    "pegelonline_metadata_request",
    "pegelonline_metadata_response",
    "glofas_upstream_area_request",
    "glofas_upstream_area_response",
}
TARGET_RETRIEVAL_KEYS = {"pegelonline_q", "glofas_dis24"}


class AcquisitionEvidenceError(ValueError):
    """Raised when acquisition evidence cannot be trusted or reproduced."""


@dataclass(frozen=True, slots=True)
class ExternalArtifactFile:
    """One external file that the authoritative evidence builder must fingerprint."""

    path: Path
    storage_reference: str


def _closed(obj: dict[str, Any], allowed: set[str], required: set[str], where: str) -> None:
    unknown = sorted(set(obj) - allowed)
    missing = sorted(required - set(obj))
    if unknown:
        raise AcquisitionEvidenceError(f"{where} contains unexpected fields: {', '.join(unknown)}")
    if missing:
        raise AcquisitionEvidenceError(f"{where} is missing fields: {', '.join(missing)}")


def _parse_timestamp(value: Any, where: str) -> datetime:
    if type(value) is not str or not value or value != value.strip() or not RFC3339_RE.fullmatch(value):
        raise AcquisitionEvidenceError(f"{where} must be RFC-3339 with an explicit timezone")
    normalized = value[:-1] + "+00:00" if value[-1:] in {"Z", "z"} else value
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError as exc:
        raise AcquisitionEvidenceError(f"{where} is not a valid date-time") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise AcquisitionEvidenceError(f"{where} must include a timezone")
    return parsed


def _require_external_reference(value: Any, where: str) -> str:
    if type(value) is not str or value != value.strip() or not EXTERNAL_RE.fullmatch(value):
        raise AcquisitionEvidenceError(f"{where} must be a canonical external:// reference")
    segments = value[len("external://") :].split("/")
    if any(segment in {"", ".", ".."} for segment in segments):
        raise AcquisitionEvidenceError(f"{where} must not contain empty, dot, or parent segments")
    return value


def validate_artifact_descriptor(value: Any, where: str = "artifact") -> dict[str, Any]:
    """Validate a serialized manifest-compatible external artifact identity."""

    if type(value) is not dict:
        raise AcquisitionEvidenceError(f"{where} must be an object")
    _closed(value, ARTIFACT_KEYS, ARTIFACT_KEYS, where)
    byte_size = value["byte_size"]
    if type(byte_size) is not int or byte_size <= 0:
        raise AcquisitionEvidenceError(f"{where}.byte_size must be a positive integer")
    digest = value["sha256"]
    if type(digest) is not str or not SHA256_RE.fullmatch(digest):
        raise AcquisitionEvidenceError(f"{where}.sha256 must be a lowercase SHA-256")
    _require_external_reference(value["storage_reference"], f"{where}.storage_reference")
    return value


def fingerprint_external_file(path: Path, *, storage_reference: str) -> dict[str, Any]:
    """Derive size/SHA-256 from one stable regular external file.

    The path is checked before opening, the opened file descriptor is bound to
    the same device/inode/size/mtime identity, and the path is checked again
    after hashing. A symlink, replacement or in-place mutation fails closed.
    """

    if not isinstance(path, Path):
        raise AcquisitionEvidenceError("path must be a pathlib.Path")
    _require_external_reference(storage_reference, "storage_reference")
    try:
        before = path.lstat()
    except OSError as exc:
        raise AcquisitionEvidenceError(f"cannot stat external artifact: {exc}") from exc
    if stat.S_ISLNK(before.st_mode) or not stat.S_ISREG(before.st_mode):
        raise AcquisitionEvidenceError("external artifact must be a regular non-symlink file")
    if before.st_size <= 0:
        raise AcquisitionEvidenceError("external artifact must not be empty")

    identity_before = (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns)
    digest = hashlib.sha256()
    byte_size = 0
    try:
        with path.open("rb") as handle:
            opened = os.fstat(handle.fileno())
            identity_opened = (opened.st_dev, opened.st_ino, opened.st_size, opened.st_mtime_ns)
            if not stat.S_ISREG(opened.st_mode) or identity_opened != identity_before:
                raise AcquisitionEvidenceError("external artifact changed before it could be opened safely")
            while True:
                chunk = handle.read(1024 * 1024)
                if not chunk:
                    break
                digest.update(chunk)
                byte_size += len(chunk)
    except AcquisitionEvidenceError:
        raise
    except OSError as exc:
        raise AcquisitionEvidenceError(f"cannot read external artifact: {exc}") from exc

    try:
        after = path.lstat()
    except OSError as exc:
        raise AcquisitionEvidenceError(f"cannot restat external artifact: {exc}") from exc
    identity_after = (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns)
    if identity_after != identity_before or byte_size != after.st_size:
        raise AcquisitionEvidenceError("external artifact changed while being fingerprinted")

    return {
        "byte_size": byte_size,
        "sha256": digest.hexdigest(),
        "storage_reference": storage_reference,
    }


def _fingerprint_external_input(value: Any, where: str) -> dict[str, Any]:
    if type(value) is not ExternalArtifactFile:
        raise AcquisitionEvidenceError(
            f"{where} must be an ExternalArtifactFile so the builder fingerprints real bytes"
        )
    return fingerprint_external_file(value.path, storage_reference=value.storage_reference)


def _finite_number(value: Any, where: str) -> float:
    if type(value) not in {int, float}:
        raise AcquisitionEvidenceError(f"{where} must be a finite numeric value and not boolean")
    try:
        number = float(value)
    except OverflowError as exc:
        raise AcquisitionEvidenceError(f"{where} must be finite") from exc
    if not math.isfinite(number):
        raise AcquisitionEvidenceError(f"{where} must be finite")
    return number


def _require_finalized_intent(intent: Any) -> dict[str, Any]:
    """Require the exact repository-owned finalized intent contract."""

    if type(intent) is not dict:
        raise AcquisitionEvidenceError("finalized_intent must be an object")
    if intent.get("phase") != "target_acquisition":
        raise AcquisitionEvidenceError("finalized intent must be in target_acquisition phase")
    try:
        acquisition_intent_sha256(intent)
    except AcquisitionIntentError as exc:
        raise AcquisitionEvidenceError(f"finalized intent is not canonical: {exc}") from exc
    resolution = intent.get("metadata_resolution")
    if type(resolution) is not dict:
        raise AcquisitionEvidenceError("finalized intent is missing metadata_resolution")
    station_coordinate = resolution.get("station_coordinate_wgs84")
    if type(station_coordinate) is not dict or set(station_coordinate) != {"latitude", "longitude"}:
        raise AcquisitionEvidenceError("metadata_resolution station_coordinate_wgs84 is invalid")
    latitude = _finite_number(station_coordinate["latitude"], "station latitude")
    longitude = _finite_number(station_coordinate["longitude"], "station longitude")
    if not -90.0 <= latitude <= 90.0 or not -180.0 <= longitude < 180.0:
        raise AcquisitionEvidenceError("metadata_resolution station coordinate is outside canonical WGS84 range")
    return intent


def _candidate_records(
    finalized_intent: dict[str, Any],
    candidates: Iterable[GlofasGridCell],
) -> list[dict[str, float]]:
    try:
        cells = list(candidates)
    except TypeError as exc:
        raise AcquisitionEvidenceError("glofas_candidate_cells must be iterable") from exc
    if not cells:
        raise AcquisitionEvidenceError("glofas_candidate_cells must not be empty")

    resolution = finalized_intent["metadata_resolution"]
    station = resolution["station_coordinate_wgs84"]
    try:
        replayed = select_dresden_glofas_grid_cell(
            station_latitude=station["latitude"],
            station_longitude=station["longitude"],
            candidates=cells,
        )
    except (GridMatchError, ValueError) as exc:
        raise AcquisitionEvidenceError(f"complete GloFAS candidate set is invalid: {exc}") from exc

    expected_match = resolution.get("glofas_grid_match")
    actual_match = {
        "latitude": replayed.cell.latitude,
        "longitude": replayed.cell.longitude,
        "upstream_area_km2": replayed.cell.upstream_area_km2,
        "angular_distance_degrees": replayed.angular_distance_degrees,
        "relative_drainage_area_mismatch": replayed.relative_drainage_area_mismatch,
    }
    if expected_match != actual_match:
        raise AcquisitionEvidenceError(
            "complete GloFAS candidate set does not reproduce the finalized grid selection"
        )

    records = [
        {
            "latitude": float(cell.latitude),
            "longitude": float(cell.longitude),
            "upstream_area_km2": float(cell.upstream_area_km2),
        }
        for cell in cells
    ]
    return sorted(
        records,
        key=lambda item: (item["latitude"], item["longitude"], item["upstream_area_km2"]),
    )


def _candidate_cells_from_evidence(
    value: Any,
    *,
    finalized_intent: dict[str, Any],
) -> list[GlofasGridCell]:
    if type(value) is not list or not value:
        raise AcquisitionEvidenceError("glofas_candidate_cells must be a non-empty array")
    cells: list[GlofasGridCell] = []
    records: list[dict[str, float]] = []
    for index, record in enumerate(value):
        where = f"glofas_candidate_cells[{index}]"
        if type(record) is not dict:
            raise AcquisitionEvidenceError(f"{where} must be an object")
        _closed(record, CANDIDATE_KEYS, CANDIDATE_KEYS, where)
        latitude = _finite_number(record["latitude"], f"{where}.latitude")
        longitude = _finite_number(record["longitude"], f"{where}.longitude")
        upstream_area = _finite_number(record["upstream_area_km2"], f"{where}.upstream_area_km2")
        cell = GlofasGridCell(latitude, longitude, upstream_area)
        cells.append(cell)
        records.append(
            {
                "latitude": latitude,
                "longitude": longitude,
                "upstream_area_km2": upstream_area,
            }
        )
    canonical = sorted(
        records,
        key=lambda item: (item["latitude"], item["longitude"], item["upstream_area_km2"]),
    )
    if records != canonical:
        raise AcquisitionEvidenceError("glofas_candidate_cells must be in canonical sorted order")
    _candidate_records(finalized_intent, cells)
    return cells


def _validate_unique_artifacts(artifacts: list[dict[str, Any]], where: str) -> None:
    references = [artifact["storage_reference"] for artifact in artifacts]
    if len(references) != len(set(references)):
        raise AcquisitionEvidenceError(f"{where} must use unique external storage references")
    content_identities = [(artifact["byte_size"], artifact["sha256"]) for artifact in artifacts]
    if len(content_identities) != len(set(content_identities)):
        raise AcquisitionEvidenceError(f"{where} must use unique byte-content identities")


def metadata_resolution_evidence(
    *,
    finalized_intent: dict[str, Any],
    resolved_at: str,
    glofas_candidate_cells: Iterable[GlofasGridCell],
    pegelonline_metadata_request: ExternalArtifactFile,
    pegelonline_metadata_response: ExternalArtifactFile,
    glofas_upstream_area_request: ExternalArtifactFile,
    glofas_upstream_area_response: ExternalArtifactFile,
) -> dict[str, Any]:
    """Build metadata evidence by hashing real files and replaying full grid selection."""

    final = _require_finalized_intent(finalized_intent)
    _parse_timestamp(resolved_at, "resolved_at")
    candidates = _candidate_records(final, glofas_candidate_cells)
    inputs = {
        "pegelonline_metadata_request": pegelonline_metadata_request,
        "pegelonline_metadata_response": pegelonline_metadata_response,
        "glofas_upstream_area_request": glofas_upstream_area_request,
        "glofas_upstream_area_response": glofas_upstream_area_response,
    }
    artifacts = {
        name: _fingerprint_external_input(value, f"inputs.{name}")
        for name, value in inputs.items()
    }
    _validate_unique_artifacts(list(artifacts.values()), "metadata artifacts")
    evidence = {
        "profile_version": PROFILE_VERSION,
        "evidence_type": "dresden_metadata_resolution",
        "resolved_at": resolved_at,
        "initial_intent_sha256": acquisition_intent_sha256(acquisition_intent()),
        "finalized_intent_sha256": acquisition_intent_sha256(final),
        "artifacts": artifacts,
        "glofas_candidate_cells": candidates,
        "resolved_metadata": final["metadata_resolution"],
    }
    validate_metadata_resolution_evidence(evidence, finalized_intent=final)
    return evidence


def validate_metadata_resolution_evidence(
    evidence: Any,
    *,
    finalized_intent: dict[str, Any],
) -> dict[str, Any]:
    final = _require_finalized_intent(finalized_intent)
    if type(evidence) is not dict:
        raise AcquisitionEvidenceError("metadata evidence must be an object")
    required = {
        "profile_version",
        "evidence_type",
        "resolved_at",
        "initial_intent_sha256",
        "finalized_intent_sha256",
        "artifacts",
        "glofas_candidate_cells",
        "resolved_metadata",
    }
    _closed(evidence, required, required, "metadata evidence")
    if evidence["profile_version"] != PROFILE_VERSION or evidence["evidence_type"] != "dresden_metadata_resolution":
        raise AcquisitionEvidenceError("unsupported metadata evidence profile/type")
    _parse_timestamp(evidence["resolved_at"], "resolved_at")
    if evidence["initial_intent_sha256"] != acquisition_intent_sha256(acquisition_intent()):
        raise AcquisitionEvidenceError("metadata evidence is not bound to the canonical initial intent")
    if evidence["finalized_intent_sha256"] != acquisition_intent_sha256(final):
        raise AcquisitionEvidenceError("metadata evidence is not bound to the supplied finalized intent")
    if evidence["resolved_metadata"] != final["metadata_resolution"]:
        raise AcquisitionEvidenceError("metadata evidence resolved_metadata differs from finalized intent")
    _candidate_cells_from_evidence(evidence["glofas_candidate_cells"], finalized_intent=final)

    artifacts = evidence["artifacts"]
    if type(artifacts) is not dict:
        raise AcquisitionEvidenceError("metadata evidence artifacts must be an object")
    _closed(artifacts, METADATA_ARTIFACT_KEYS, METADATA_ARTIFACT_KEYS, "metadata evidence artifacts")
    validated = [
        validate_artifact_descriptor(value, f"artifacts.{name}")
        for name, value in artifacts.items()
    ]
    _validate_unique_artifacts(validated, "metadata artifacts")
    return evidence


def target_acquisition_evidence(
    *,
    finalized_intent: dict[str, Any],
    metadata_evidence: dict[str, Any],
    pegelonline_retrieved_at: str,
    pegelonline_request_artifact: ExternalArtifactFile,
    pegelonline_data_artifact: ExternalArtifactFile,
    glofas_retrieved_at: str,
    glofas_request_artifact: ExternalArtifactFile,
    glofas_data_artifact: ExternalArtifactFile,
) -> dict[str, Any]:
    """Build target evidence by fingerprinting exact request/data files."""

    final = _require_finalized_intent(finalized_intent)
    validate_metadata_resolution_evidence(metadata_evidence, finalized_intent=final)
    retrieval_inputs = {
        "pegelonline_q": {
            "manifest": PEGELONLINE_MANIFEST,
            "retrieved_at": pegelonline_retrieved_at,
            "request": pegelonline_request_artifact,
            "data": pegelonline_data_artifact,
        },
        "glofas_dis24": {
            "manifest": GLOFAS_MANIFEST,
            "retrieved_at": glofas_retrieved_at,
            "request": glofas_request_artifact,
            "data": glofas_data_artifact,
        },
    }
    retrievals: dict[str, Any] = {}
    for name, source in retrieval_inputs.items():
        retrievals[name] = {
            "manifest": source["manifest"],
            "retrieved_at": source["retrieved_at"],
            "request_artifact": _fingerprint_external_input(
                source["request"], f"inputs.{name}.request_artifact"
            ),
            "data_artifact": _fingerprint_external_input(
                source["data"], f"inputs.{name}.data_artifact"
            ),
        }

    evidence = {
        "profile_version": PROFILE_VERSION,
        "evidence_type": "dresden_target_acquisition",
        "finalized_intent_sha256": acquisition_intent_sha256(final),
        "metadata_resolution_evidence_sha256": acquisition_evidence_sha256(metadata_evidence),
        "retrievals": retrievals,
        "manifest_raw_artifact_candidates": [
            {
                "manifest": PEGELONLINE_MANIFEST,
                "raw_artifact": retrievals["pegelonline_q"]["data_artifact"],
            },
            {
                "manifest": GLOFAS_MANIFEST,
                "raw_artifact": retrievals["glofas_dis24"]["data_artifact"],
            },
        ],
    }
    validate_target_acquisition_evidence(
        evidence,
        finalized_intent=final,
        metadata_evidence=metadata_evidence,
    )
    return evidence


def validate_target_acquisition_evidence(
    evidence: Any,
    *,
    finalized_intent: dict[str, Any],
    metadata_evidence: dict[str, Any],
) -> dict[str, Any]:
    final = _require_finalized_intent(finalized_intent)
    validate_metadata_resolution_evidence(metadata_evidence, finalized_intent=final)
    if type(evidence) is not dict:
        raise AcquisitionEvidenceError("target evidence must be an object")
    required = {
        "profile_version",
        "evidence_type",
        "finalized_intent_sha256",
        "metadata_resolution_evidence_sha256",
        "retrievals",
        "manifest_raw_artifact_candidates",
    }
    _closed(evidence, required, required, "target evidence")
    if evidence["profile_version"] != PROFILE_VERSION or evidence["evidence_type"] != "dresden_target_acquisition":
        raise AcquisitionEvidenceError("unsupported target evidence profile/type")
    if evidence["finalized_intent_sha256"] != acquisition_intent_sha256(final):
        raise AcquisitionEvidenceError("target evidence is not bound to the supplied finalized intent")
    if evidence["metadata_resolution_evidence_sha256"] != acquisition_evidence_sha256(metadata_evidence):
        raise AcquisitionEvidenceError("target evidence is not bound to the supplied metadata evidence")

    resolved_at = _parse_timestamp(metadata_evidence["resolved_at"], "metadata_evidence.resolved_at")
    retrievals = evidence["retrievals"]
    if type(retrievals) is not dict:
        raise AcquisitionEvidenceError("target retrievals must be an object")
    _closed(retrievals, TARGET_RETRIEVAL_KEYS, TARGET_RETRIEVAL_KEYS, "target retrievals")
    expected_manifests = {"pegelonline_q": PEGELONLINE_MANIFEST, "glofas_dis24": GLOFAS_MANIFEST}
    target_artifacts: list[dict[str, Any]] = []
    for name, expected_manifest in expected_manifests.items():
        retrieval = retrievals[name]
        if type(retrieval) is not dict:
            raise AcquisitionEvidenceError(f"retrievals.{name} must be an object")
        keys = {"manifest", "retrieved_at", "request_artifact", "data_artifact"}
        _closed(retrieval, keys, keys, f"retrievals.{name}")
        if retrieval["manifest"] != expected_manifest:
            raise AcquisitionEvidenceError(f"retrievals.{name}.manifest does not match the frozen source")
        retrieved_at = _parse_timestamp(retrieval["retrieved_at"], f"retrievals.{name}.retrieved_at")
        if retrieved_at < resolved_at:
            raise AcquisitionEvidenceError(f"retrievals.{name} predates metadata resolution")
        request_artifact = validate_artifact_descriptor(
            retrieval["request_artifact"], f"retrievals.{name}.request_artifact"
        )
        data_artifact = validate_artifact_descriptor(
            retrieval["data_artifact"], f"retrievals.{name}.data_artifact"
        )
        target_artifacts.extend((request_artifact, data_artifact))

    metadata_artifacts = [
        validate_artifact_descriptor(value, f"metadata_artifacts.{name}")
        for name, value in metadata_evidence["artifacts"].items()
    ]
    _validate_unique_artifacts(
        metadata_artifacts + target_artifacts,
        "all Dresden acquisition artifacts",
    )

    expected_candidates = [
        {
            "manifest": PEGELONLINE_MANIFEST,
            "raw_artifact": retrievals["pegelonline_q"]["data_artifact"],
        },
        {
            "manifest": GLOFAS_MANIFEST,
            "raw_artifact": retrievals["glofas_dis24"]["data_artifact"],
        },
    ]
    if evidence["manifest_raw_artifact_candidates"] != expected_candidates:
        raise AcquisitionEvidenceError("manifest raw-artifact candidates do not match target data artifacts")
    return evidence


def canonical_evidence_bytes(evidence: dict[str, Any]) -> bytes:
    if type(evidence) is not dict:
        raise AcquisitionEvidenceError("evidence must be an object")
    try:
        return json.dumps(
            evidence,
            ensure_ascii=False,
            allow_nan=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise AcquisitionEvidenceError(f"evidence is not canonical JSON data: {exc}") from exc


def acquisition_evidence_sha256(evidence: dict[str, Any]) -> str:
    return hashlib.sha256(canonical_evidence_bytes(evidence)).hexdigest()
