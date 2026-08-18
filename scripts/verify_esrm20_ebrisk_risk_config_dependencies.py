# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Verify exact receipted ESRM20 EBRISK config bytes before bounded parsing."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Any

try:
    from scripts.openquake_config_dependencies import (
        OpenQuakeConfigError,
        extract_openquake_config_references,
    )
except ModuleNotFoundError:  # pragma: no cover - direct script import path
    from openquake_config_dependencies import (
        OpenQuakeConfigError,
        extract_openquake_config_references,
    )

SCHEMA_VERSION = "oc-esrm20-ebrisk-risk-config-dependency-profile-v1"
SOURCE_ISSUE = 281
DATASET_ID = "efehr.esrm20.risk-inputs.v1.0"
PROJECT_ID = 269
PROJECT_PATH = "efehr/esrm20"
COMMIT_SHA = "05f83bbc9df81d02ee8ddb1801d9d781355ce783"
RECEIPT_COMMENT_ID = 5328119673
PARSER_ID = "scripts.openquake_config_dependencies.extract_openquake_config_references"


@dataclass(frozen=True)
class ConfigSpec:
    key: str
    operation_id: str
    repository_path: str
    byte_count: int
    sha256: str


CONFIG_SPECS = (
    ConfigSpec(
        key="group1",
        operation_id="esrm20-ebrisk-group1-config-candidate-v1",
        repository_path="Configuration_files/config_ebrisk_Group1.ini",
        byte_count=3052,
        sha256="be5f787954ca7e4060e4362d12efcf7cba5e50740930f3de7d7a521ebc580146",
    ),
    ConfigSpec(
        key="group2",
        operation_id="esrm20-ebrisk-group2-config-candidate-v1",
        repository_path="Configuration_files/config_ebrisk_Group2.ini",
        byte_count=2832,
        sha256="80cf566003cdb5e12dde820d5cba3db8ea5a6ba2db31e7089f3453f921852625",
    ),
    ConfigSpec(
        key="iceland",
        operation_id="esrm20-ebrisk-iceland-config-candidate-v1",
        repository_path="Configuration_files/config_ebrisk_Iceland.ini",
        byte_count=1345,
        sha256="7d1f23170462a4f1b6b514518d4d35564a0ec2255072f6df38e5a5c6518b849c",
    ),
)
_SPEC_BY_KEY = {spec.key: spec for spec in CONFIG_SPECS}


class VerifiedEbriskConfigError(ValueError):
    """Raised when a receipted EBRISK config or derived metadata drifts."""


def config_spec(key: str) -> ConfigSpec:
    if type(key) is not str or key not in _SPEC_BY_KEY:
        raise VerifiedEbriskConfigError("EBRISK config key is outside frozen candidates")
    spec = _SPEC_BY_KEY[key]
    if spec.key != key:
        raise VerifiedEbriskConfigError("EBRISK config identity is inconsistent")
    return spec


def _verify_payload_identity(payload: bytes, spec: ConfigSpec) -> str:
    if type(payload) is not bytes:
        raise VerifiedEbriskConfigError("EBRISK config payload must be immutable bytes")
    if len(payload) != spec.byte_count:
        raise VerifiedEbriskConfigError(
            f"EBRISK config byte count mismatch: observed {len(payload)}, expected {spec.byte_count}"
        )
    digest = hashlib.sha256(payload).hexdigest()
    if digest != spec.sha256:
        raise VerifiedEbriskConfigError("EBRISK config SHA-256 mismatch")
    return digest


def _decode_verified_payload(payload: bytes) -> str:
    try:
        return payload.decode("utf-8", errors="strict")
    except UnicodeDecodeError as exc:
        raise VerifiedEbriskConfigError("verified EBRISK config is not strict UTF-8") from exc


def extract_dependencies_from_verified_text(
    config_text: str, *, repository_path: str
) -> list[dict[str, str]]:
    """Run the reviewed OpenQuake parser on already identity-verified text."""

    if type(config_text) is not str or not config_text:
        raise VerifiedEbriskConfigError("verified EBRISK config text is absent")
    if type(repository_path) is not str or not repository_path:
        raise VerifiedEbriskConfigError("verified EBRISK repository path is absent")
    try:
        references = extract_openquake_config_references(
            config_text, config_path=repository_path
        )
    except OpenQuakeConfigError as exc:
        raise VerifiedEbriskConfigError(
            f"verified EBRISK dependency parse failed: {exc}"
        ) from exc
    dependencies = [
        {
            "section": reference.section,
            "option": reference.option,
            "raw_path": reference.raw_path,
            "resolved_path": reference.resolved_path,
        }
        for reference in references
    ]
    if dependencies != sorted(
        dependencies,
        key=lambda row: (
            row["resolved_path"],
            row["section"],
            row["option"],
            row["raw_path"],
        ),
    ):
        raise VerifiedEbriskConfigError("reviewed dependency parser returned non-canonical order")
    return dependencies


def extract_verified_ebrisk_dependencies(key: str, payload: bytes) -> dict[str, Any]:
    """Return only first-order dependency metadata from exact receipted bytes."""

    spec = config_spec(key)
    digest = _verify_payload_identity(payload, spec)
    dependencies = extract_dependencies_from_verified_text(
        _decode_verified_payload(payload), repository_path=spec.repository_path
    )
    return {
        "schema_version": SCHEMA_VERSION,
        "source_issue": SOURCE_ISSUE,
        "dataset_id": DATASET_ID,
        "project_id": PROJECT_ID,
        "project_path": PROJECT_PATH,
        "commit_sha": COMMIT_SHA,
        "candidate_key": spec.key,
        "operation_id": spec.operation_id,
        "repository_path": spec.repository_path,
        "byte_count": len(payload),
        "sha256": digest,
        "receipt_comment_id": RECEIPT_COMMENT_ID,
        "parser": PARSER_ID,
        "dependencies": dependencies,
        "raw_config_returned": False,
        "historical_group_assignment_verified": False,
        "dependency_inventory_authorized": False,
        "runtime_compatibility_verified": False,
        "external_bytes_persisted": False,
        "publication_authorized": False,
        "model_use_authorized": False,
    }
