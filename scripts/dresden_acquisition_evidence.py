# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Exact pre-admission acquisition evidence for the Dresden hydrology pilot.

This module bridges the frozen acquisition intent and later dataset-manifest
admission without committing external provider bytes. It records two stages:

1. metadata-resolution evidence binds the exact request/response artifacts used
   to resolve PEGELONLINE cadence/coordinates and GloFAS upstream-area metadata;
2. target-acquisition evidence binds the exact request/data artifacts returned
   for the frozen PEGELONLINE-Q and GloFAS-dis24 holdout.

Artifact descriptors intentionally use the same ``byte_size``, ``sha256`` and
``storage_reference`` shape as dataset-manifest raw/derived artifacts so a
reviewed target data artifact can later be promoted without inventing a second
identity.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Any

from scripts.dresden_acquisition_intent import (
    GLOFAS_MANIFEST,
    PEGELONLINE_MANIFEST,
    acquisition_intent,
    acquisition_intent_sha256,
)

PROFILE_VERSION = "1.0.0"
SHA256_RE = re.compile(r"^[a-f0-9]{64}$")
EXTERNAL_RE = re.compile(r"^external://[A-Za-z0-9][A-Za-z0-9._/-]*$")
RFC3339_RE = re.compile(
    r"^\d{4}-\d{2}-\d{2}[Tt]\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:[Zz]|[+-]\d{2}:\d{2})$"
)
ARTIFACT_KEYS = {"byte_size", "sha256", "storage_reference"}
METADATA_ARTIFACT_KEYS = {
    "pegelonline_metadata_request",
    "pegelonline_metadata_response",
    "glofas_upstream_area_request",
    "glofas_upstream_area_response",
}
TARGET_RETRIEVAL_KEYS = {"pegelonline_q", "glofas_dis24"}


class AcquisitionEvidenceError(ValueError):
    """Raised when acquisition evidence cannot be trusted or reproduced."""


def _closed(obj: dict[str, Any], allowed: set[str], required: set[str], where: str) -> None:
    unknown = sorted(set(obj) - allowed)
    missing = sorted(required - set(obj))
    if unknown:
        raise AcquisitionEvidenceError(f"{where} contains unexpected fields: {', '.join(unknown)}")
    if missing:
        raise AcquisitionEvidenceError(f"{where} is missing fields: {', '.join(missing)}")


def _require_timestamp(value: Any, where: str) -> str:
    if type(value) is not str or not value or value != value.strip() or not RFC3339_RE.fullmatch(value):
        raise AcquisitionEvidenceError(f"{where} must be RFC-3339 with an explicit timezone")
    normalized = value[:-1] + "+00:00" if value[-1:] in {"Z", "z"} else value
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError as exc:
        raise AcquisitionEvidenceError(f"{where} is not a valid date-time") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise AcquisitionEvidenceError(f"{where} must include a timezone")
    return value


def _require_external_reference(value: Any, where: str) -> str:
    if type(value) is not str or value != value.strip() or not EXTERNAL_RE.fullmatch(value):
        raise AcquisitionEvidenceError(f"{where} must be a canonical external:// reference")
    segments = value[len("external://") :].split("/")
    if any(segment in {"", ".", ".."} for segment in segments):
        raise AcquisitionEvidenceError(f"{where} must not contain empty, dot, or parent segments")
    return value


def validate_artifact_descriptor(value: Any, where: str = "artifact") -> dict[str, Any]:
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
    """Hash one external regular file without following a symlink.

    The file is stat'ed before and after hashing. Size, mtime and inode/device
    identity must remain stable so a concurrent replacement cannot silently
    produce a receipt for an ambiguous byte object.
    """

    if not isinstance(path, Path):
        raise AcquisitionEvidenceError("path must be a pathlib.Path")
    _require_external_reference(storage_reference, "storage_reference")
    try:
        before = path.lstat()
    except OSError as exc:
        raise AcquisitionEvidenceError(f"cannot stat external artifact: {exc}") from exc
    if path.is_symlink() or not path.is_file():
        raise AcquisitionEvidenceError("external artifact must be a regular non-symlink file")
    if before.st_size <= 0:
        raise AcquisitionEvidenceError("external artifact must not be empty")

    digest = hashlib.sha256()
    byte_size = 0
    try:
        with path.open("rb") as handle:
            while True:
                chunk = handle.read(1024 * 1024)
                if not chunk:
                    break
                digest.update(chunk)
                byte_size += len(chunk)
    except OSError as exc:
        raise AcquisitionEvidenceError(f"cannot read external artifact: {exc}") from exc

    try:
        after = path.lstat()
    except OSError as exc:
        raise AcquisitionEvidenceError(f"cannot restat external artifact: {exc}") from exc
    before_identity = (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns)
    after_identity = (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns)
    if before_identity != after_identity or byte_size != after.st_size:
        raise AcquisitionEvidenceError("external artifact changed while being fingerprinted")

    return {
        "byte_size": byte_size,
        "sha256": digest.hexdigest(),
        "storage_reference": storage_reference,
    }


def _require_finalized_intent(intent: Any) -> dict[str, Any]:
    if type(intent) is not dict:
        raise AcquisitionEvidenceError("finalized_intent must be an object")
    baseline = acquisition_intent()
    if intent.get("profile_version") != baseline["profile_version"]:
        raise AcquisitionEvidenceError("finalized intent profile_version does not match the frozen profile")
    if intent.get("purpose") != baseline["purpose"]:
        raise AcquisitionEvidenceError("finalized intent purpose does not match the frozen Dresden pilot")
    if intent.get("phase") != "target_acquisition" or intent.get("target_values_must_not_be_inspected") is not False:
        raise AcquisitionEvidenceError("finalized intent must be in target_acquisition phase")

    fixed_pegel_fields = (
        "manifest",
        "source_review",
        "station_number",
        "station_uuid",
        "variable",
        "time_convention",
        "required_local_coverage_start",
        "required_local_coverage_end_exclusive",
    )
    fixed_glofas_fields = (
        "manifest",
        "source_review",
        "dataset",
        "system_version",
        "hydrological_model",
        "product_type",
        "variable",
        "grid_degrees",
        "first_end_label_utc",
        "last_end_label_utc",
        "expected_daily_labels",
    )
    pegel = intent.get("pegelonline")
    glofas = intent.get("glofas")
    if type(pegel) is not dict or type(glofas) is not dict:
        raise AcquisitionEvidenceError("finalized intent is missing source sections")
    for field in fixed_pegel_fields:
        if pegel.get(field) != baseline["pegelonline"].get(field):
            raise AcquisitionEvidenceError(f"finalized intent drifted at pegelonline.{field}")
    for field in fixed_glofas_fields:
        if glofas.get(field) != baseline["glofas"].get(field):
            raise AcquisitionEvidenceError(f"finalized intent drifted at glofas.{field}")

    if type(intent.get("metadata_resolution")) is not dict:
        raise AcquisitionEvidenceError("finalized intent must contain metadata_resolution")
    if type(pegel.get("sampling_interval")) is not dict or pegel["sampling_interval"].get("status") != "frozen":
        raise AcquisitionEvidenceError("finalized PEGELONLINE sampling interval must be frozen")
    if type(glofas.get("grid_cell")) is not dict or glofas["grid_cell"].get("status") != "frozen":
        raise AcquisitionEvidenceError("finalized GloFAS grid cell must be frozen")
    return intent


def _validate_unique_artifact_references(artifacts: list[dict[str, Any]], where: str) -> None:
    references = [artifact["storage_reference"] for artifact in artifacts]
    if len(references) != len(set(references)):
        raise AcquisitionEvidenceError(f"{where} must use unique external storage references")


def metadata_resolution_evidence(
    *,
    finalized_intent: dict[str, Any],
    resolved_at: str,
    pegelonline_metadata_request: dict[str, Any],
    pegelonline_metadata_response: dict[str, Any],
    glofas_upstream_area_request: dict[str, Any],
    glofas_upstream_area_response: dict[str, Any],
) -> dict[str, Any]:
    """Build evidence that binds exact metadata bytes to one finalized intent."""

    final = _require_finalized_intent(finalized_intent)
    _require_timestamp(resolved_at, "resolved_at")
    artifacts = {
        "pegelonline_metadata_request": pegelonline_metadata_request,
        "pegelonline_metadata_response": pegelonline_metadata_response,
        "glofas_upstream_area_request": glofas_upstream_area_request,
        "glofas_upstream_area_response": glofas_upstream_area_response,
    }
    for name, artifact in artifacts.items():
        validate_artifact_descriptor(artifact, f"artifacts.{name}")
    _validate_unique_artifact_references(list(artifacts.values()), "metadata artifacts")

    evidence = {
        "profile_version": PROFILE_VERSION,
        "evidence_type": "dresden_metadata_resolution",
        "resolved_at": resolved_at,
        "initial_intent_sha256": acquisition_intent_sha256(acquisition_intent()),
        "finalized_intent_sha256": acquisition_intent_sha256(final),
        "artifacts": artifacts,
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
        "resolved_metadata",
    }
    _closed(evidence, required, required, "metadata evidence")
    if evidence["profile_version"] != PROFILE_VERSION or evidence["evidence_type"] != "dresden_metadata_resolution":
        raise AcquisitionEvidenceError("unsupported metadata evidence profile/type")
    _require_timestamp(evidence["resolved_at"], "resolved_at")
    if evidence["initial_intent_sha256"] != acquisition_intent_sha256(acquisition_intent()):
        raise AcquisitionEvidenceError("metadata evidence is not bound to the canonical initial intent")
    if evidence["finalized_intent_sha256"] != acquisition_intent_sha256(final):
        raise AcquisitionEvidenceError("metadata evidence is not bound to the supplied finalized intent")
    if evidence["resolved_metadata"] != final["metadata_resolution"]:
        raise AcquisitionEvidenceError("metadata evidence resolved_metadata differs from finalized intent")

    artifacts = evidence["artifacts"]
    if type(artifacts) is not dict:
        raise AcquisitionEvidenceError("metadata evidence artifacts must be an object")
    _closed(artifacts, METADATA_ARTIFACT_KEYS, METADATA_ARTIFACT_KEYS, "metadata evidence artifacts")
    validated = [validate_artifact_descriptor(value, f"artifacts.{name}") for name, value in artifacts.items()]
    _validate_unique_artifact_references(validated, "metadata artifacts")
    return evidence


def target_acquisition_evidence(
    *,
    finalized_intent: dict[str, Any],
    metadata_evidence: dict[str, Any],
    pegelonline_retrieved_at: str,
    pegelonline_request_artifact: dict[str, Any],
    pegelonline_data_artifact: dict[str, Any],
    glofas_retrieved_at: str,
    glofas_request_artifact: dict[str, Any],
    glofas_data_artifact: dict[str, Any],
) -> dict[str, Any]:
    """Build pre-admission evidence for the two exact holdout data artifacts."""

    final = _require_finalized_intent(finalized_intent)
    validate_metadata_resolution_evidence(metadata_evidence, finalized_intent=final)
    pegel_retrieval = {
        "manifest": PEGELONLINE_MANIFEST,
        "retrieved_at": pegelonline_retrieved_at,
        "request_artifact": pegelonline_request_artifact,
        "data_artifact": pegelonline_data_artifact,
    }
    glofas_retrieval = {
        "manifest": GLOFAS_MANIFEST,
        "retrieved_at": glofas_retrieved_at,
        "request_artifact": glofas_request_artifact,
        "data_artifact": glofas_data_artifact,
    }
    evidence = {
        "profile_version": PROFILE_VERSION,
        "evidence_type": "dresden_target_acquisition",
        "finalized_intent_sha256": acquisition_intent_sha256(final),
        "metadata_resolution_evidence_sha256": acquisition_evidence_sha256(metadata_evidence),
        "retrievals": {
            "pegelonline_q": pegel_retrieval,
            "glofas_dis24": glofas_retrieval,
        },
        "manifest_raw_artifact_candidates": [
            {"manifest": PEGELONLINE_MANIFEST, "raw_artifact": pegelonline_data_artifact},
            {"manifest": GLOFAS_MANIFEST, "raw_artifact": glofas_data_artifact},
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

    retrievals = evidence["retrievals"]
    if type(retrievals) is not dict:
        raise AcquisitionEvidenceError("target retrievals must be an object")
    _closed(retrievals, TARGET_RETRIEVAL_KEYS, TARGET_RETRIEVAL_KEYS, "target retrievals")
    expected_manifests = {
        "pegelonline_q": PEGELONLINE_MANIFEST,
        "glofas_dis24": GLOFAS_MANIFEST,
    }
    all_artifacts: list[dict[str, Any]] = []
    for name, expected_manifest in expected_manifests.items():
        retrieval = retrievals[name]
        if type(retrieval) is not dict:
            raise AcquisitionEvidenceError(f"retrievals.{name} must be an object")
        retrieval_keys = {"manifest", "retrieved_at", "request_artifact", "data_artifact"}
        _closed(retrieval, retrieval_keys, retrieval_keys, f"retrievals.{name}")
        if retrieval["manifest"] != expected_manifest:
            raise AcquisitionEvidenceError(f"retrievals.{name}.manifest does not match the frozen source")
        _require_timestamp(retrieval["retrieved_at"], f"retrievals.{name}.retrieved_at")
        request_artifact = validate_artifact_descriptor(
            retrieval["request_artifact"], f"retrievals.{name}.request_artifact"
        )
        data_artifact = validate_artifact_descriptor(
            retrieval["data_artifact"], f"retrievals.{name}.data_artifact"
        )
        if request_artifact["storage_reference"] == data_artifact["storage_reference"]:
            raise AcquisitionEvidenceError(f"retrievals.{name} request and data must have distinct identities")
        all_artifacts.extend((request_artifact, data_artifact))
    _validate_unique_artifact_references(all_artifacts, "target artifacts")

    expected_candidates = [
        {"manifest": PEGELONLINE_MANIFEST, "raw_artifact": retrievals["pegelonline_q"]["data_artifact"]},
        {"manifest": GLOFAS_MANIFEST, "raw_artifact": retrievals["glofas_dis24"]["data_artifact"]},
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
