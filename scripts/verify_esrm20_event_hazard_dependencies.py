# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Verify receipted ESRM20 event-hazard root bytes before bounded parsing."""

from __future__ import annotations

import argparse
import ast
import configparser
import hashlib
import json
import os
import re
import stat
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

try:
    from scripts.openquake_config_dependencies import OpenQuakeConfigError, extract_openquake_config_references
except ModuleNotFoundError:  # pragma: no cover
    from openquake_config_dependencies import OpenQuakeConfigError, extract_openquake_config_references

SCHEMA_VERSION = "oc-esrm20-event-hazard-dependency-bridge-v1"
IMT_PROFILE_SCHEMA_VERSION = "oc-esrm20-event-hazard-imt-profile-v1"
SOURCE_ISSUE = 281
CONTROL_ISSUE = 346
DATASET_ID = "efehr.esrm20.risk-inputs.v1.0"
PROJECT_ID = 269
PROJECT_PATH = "efehr/esrm20"
COMMIT_SHA = "05f83bbc9df81d02ee8ddb1801d9d781355ce783"
PARSER_ID = "scripts.openquake_config_dependencies.extract_openquake_config_references"
IMT_OPTIONS = ("intensity_measure_types", "intensity_measure_types_and_levels")
_SAFE_IMT_RE = re.compile(r"^[A-Za-z][A-Za-z0-9_]*(?:\([0-9eE+., -]{1,64}\))?$")


@dataclass(frozen=True)
class RootSpec:
    group: int
    repository_path: str
    operation_id: str
    byte_count: int
    sha256: str
    receipt_comment_id: int


ROOT_SPECS = {
    1: RootSpec(
        group=1,
        repository_path="Configuration_files/config_event_hazard_Group1.ini",
        operation_id="esrm20-event-hazard-group1-config-v1",
        byte_count=1766,
        sha256="709168614dc4260a982fb4cc18956e1d4e236626efcc49bf1f1b9b4ff79969de",
        receipt_comment_id=5301296088,
    ),
    2: RootSpec(
        group=2,
        repository_path="Configuration_files/config_event_hazard_Group2.ini",
        operation_id="esrm20-event-hazard-group2-config-v1",
        byte_count=1673,
        sha256="eb74edd2168bad20c23d4b0e1a99f5ed97ef28606a9ebfef6b8c8191d35dd34c",
        receipt_comment_id=5301299581,
    ),
}


class VerifiedEventHazardConfigError(ValueError):
    """Raised when root bytes or bounded derived metadata violate frozen evidence."""


def _root_spec(group: int) -> RootSpec:
    if type(group) is not int or group not in ROOT_SPECS:
        raise VerifiedEventHazardConfigError("group must be exactly 1 or 2")
    spec = ROOT_SPECS[group]
    if spec.group != group:
        raise VerifiedEventHazardConfigError("frozen group identity is inconsistent")
    return spec


def _verify_payload_identity(payload: bytes, spec: RootSpec) -> str:
    if type(payload) is not bytes:
        raise VerifiedEventHazardConfigError("event-hazard payload must be immutable bytes")
    if len(payload) != spec.byte_count:
        raise VerifiedEventHazardConfigError(
            f"event-hazard byte count mismatch: observed {len(payload)}, expected {spec.byte_count}"
        )
    observed_sha256 = hashlib.sha256(payload).hexdigest()
    if observed_sha256 != spec.sha256:
        raise VerifiedEventHazardConfigError("event-hazard SHA-256 mismatch")
    return observed_sha256


def _decode_verified_payload(payload: bytes) -> str:
    try:
        return payload.decode("utf-8", errors="strict")
    except UnicodeDecodeError as exc:
        raise VerifiedEventHazardConfigError("verified event-hazard payload is not strict UTF-8") from exc


def extract_verified_event_hazard_dependencies(group: int, payload: bytes) -> dict[str, Any]:
    """Verify one frozen root and return only deterministic first-order dependency metadata."""

    spec = _root_spec(group)
    observed_sha256 = _verify_payload_identity(payload, spec)
    config_text = _decode_verified_payload(payload)
    try:
        references = extract_openquake_config_references(config_text, config_path=spec.repository_path)
    except OpenQuakeConfigError as exc:
        raise VerifiedEventHazardConfigError(
            f"verified event-hazard dependency parse failed: {exc}"
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
    return {
        "schema_version": SCHEMA_VERSION,
        "source_issue": SOURCE_ISSUE,
        "control_issue": CONTROL_ISSUE,
        "dataset_id": DATASET_ID,
        "project_id": PROJECT_ID,
        "project_path": PROJECT_PATH,
        "commit_sha": COMMIT_SHA,
        "group": spec.group,
        "operation_id": spec.operation_id,
        "repository_path": spec.repository_path,
        "byte_count": len(payload),
        "sha256": observed_sha256,
        "receipt_comment_id": spec.receipt_comment_id,
        "parser": PARSER_ID,
        "dependencies": dependencies,
        "dependency_inventory_authorized": False,
        "external_bytes_persisted": False,
        "publication_authorized": False,
    }


def _parse_ini(config_text: str) -> configparser.RawConfigParser:
    parser = configparser.RawConfigParser(
        interpolation=None,
        strict=True,
        empty_lines_in_values=False,
    )
    parser.optionxform = str.lower
    try:
        parser.read_string(config_text)
    except configparser.Error as exc:
        raise VerifiedEventHazardConfigError("verified event-hazard INI parse failed") from exc
    return parser


def _find_single_option(parser: configparser.RawConfigParser) -> tuple[str, str]:
    matches: list[tuple[str, str]] = []
    for section in parser.sections():
        for option in IMT_OPTIONS:
            if parser.has_option(section, option):
                matches.append((option, parser.get(section, option, raw=True)))
    if len(matches) != 1:
        raise VerifiedEventHazardConfigError(
            "verified event-hazard root must contain exactly one standard IMT option"
        )
    return matches[0]


def _validate_imt_names(names: list[str]) -> list[str]:
    if not names or len(names) > 256:
        raise VerifiedEventHazardConfigError("verified event-hazard IMT inventory is empty or unbounded")
    if len(names) != len(set(names)):
        raise VerifiedEventHazardConfigError("verified event-hazard IMT inventory contains duplicates")
    for name in names:
        if (
            type(name) is not str
            or name != name.strip()
            or len(name) > 96
            or _SAFE_IMT_RE.fullmatch(name) is None
        ):
            raise VerifiedEventHazardConfigError("verified event-hazard IMT name is not safely bounded")
    return sorted(names)


def _imt_names_from_list(raw: str) -> list[str]:
    tokens = [token for token in re.split(r"[\s,]+", raw.strip()) if token]
    return _validate_imt_names(tokens)


def _imt_names_from_mapping(raw: str) -> list[str]:
    try:
        expression = ast.parse(raw.strip(), mode="eval").body
    except (SyntaxError, ValueError) as exc:
        raise VerifiedEventHazardConfigError("verified IMT/level mapping is not valid syntax") from exc
    if not isinstance(expression, ast.Dict):
        raise VerifiedEventHazardConfigError("verified IMT/level option is not a mapping")
    names: list[str] = []
    for key in expression.keys:
        if not isinstance(key, ast.Constant) or type(key.value) is not str:
            raise VerifiedEventHazardConfigError("verified IMT/level mapping has a non-string IMT key")
        names.append(key.value)
    return _validate_imt_names(names)


def extract_openquake_imt_names(config_text: str) -> tuple[str, list[str]]:
    """Return only the standard OpenQuake IMT option name and canonical IMT keys.

    Mapping values (the intensity levels themselves) are deliberately never
    evaluated or returned.  ``ast`` is used only to inspect literal dictionary
    keys, so expressions such as ``logscale(...)`` remain opaque.
    """

    if type(config_text) is not str or not config_text:
        raise VerifiedEventHazardConfigError("event-hazard config text is absent")
    option, raw = _find_single_option(_parse_ini(config_text))
    if option == "intensity_measure_types":
        return option, _imt_names_from_list(raw)
    if option == "intensity_measure_types_and_levels":
        return option, _imt_names_from_mapping(raw)
    raise VerifiedEventHazardConfigError("unsupported event-hazard IMT option")


def extract_verified_event_hazard_imt_profile(group: int, payload: bytes) -> dict[str, Any]:
    """Verify one frozen root and return only bounded IMT-name metadata."""

    spec = _root_spec(group)
    observed_sha256 = _verify_payload_identity(payload, spec)
    option, imt_names = extract_openquake_imt_names(_decode_verified_payload(payload))
    return {
        "schema_version": IMT_PROFILE_SCHEMA_VERSION,
        "source_issue": SOURCE_ISSUE,
        "control_issue": CONTROL_ISSUE,
        "dataset_id": DATASET_ID,
        "project_id": PROJECT_ID,
        "project_path": PROJECT_PATH,
        "commit_sha": COMMIT_SHA,
        "group": spec.group,
        "operation_id": spec.operation_id,
        "repository_path": spec.repository_path,
        "byte_count": len(payload),
        "sha256": observed_sha256,
        "receipt_comment_id": spec.receipt_comment_id,
        "imt_option": option,
        "imt_names": imt_names,
        "imt_count": len(imt_names),
        "levels_returned": False,
        "raw_config_returned": False,
        "component_semantics_verified": False,
        "unit_semantics_verified": False,
        "hazard_vulnerability_imt_compatibility_verified": False,
        "external_bytes_persisted": False,
        "publication_authorized": False,
        "model_use_authorized": False,
    }


def _file_identity(info: os.stat_result) -> tuple[int, int, int, int, int]:
    return (info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns, info.st_ctime_ns)


def _read_regular_file(path: Path, spec: RootSpec) -> bytes:
    try:
        before = path.lstat()
    except OSError as exc:
        raise VerifiedEventHazardConfigError(f"cannot stat event-hazard payload: {type(exc).__name__}") from exc
    if stat.S_ISLNK(before.st_mode) or not stat.S_ISREG(before.st_mode):
        raise VerifiedEventHazardConfigError("event-hazard payload path must be a non-symlink regular file")
    if before.st_size != spec.byte_count:
        raise VerifiedEventHazardConfigError(
            f"event-hazard byte count mismatch: observed {before.st_size}, expected {spec.byte_count}"
        )

    flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0)
    try:
        fd = os.open(path, flags)
    except OSError as exc:
        raise VerifiedEventHazardConfigError(f"cannot open event-hazard payload: {type(exc).__name__}") from exc
    try:
        opened = os.fstat(fd)
        if not stat.S_ISREG(opened.st_mode) or _file_identity(opened) != _file_identity(before):
            raise VerifiedEventHazardConfigError("event-hazard payload identity changed before read")
        chunks: list[bytes] = []
        remaining = spec.byte_count + 1
        while remaining:
            chunk = os.read(fd, min(65536, remaining))
            if not chunk:
                break
            chunks.append(chunk)
            remaining -= len(chunk)
        after = os.fstat(fd)
        if _file_identity(after) != _file_identity(opened):
            raise VerifiedEventHazardConfigError("event-hazard payload identity changed during read")
    except OSError as exc:
        raise VerifiedEventHazardConfigError(f"cannot read event-hazard payload: {type(exc).__name__}") from exc
    finally:
        os.close(fd)

    payload = b"".join(chunks)
    if len(payload) != spec.byte_count:
        raise VerifiedEventHazardConfigError(
            f"event-hazard byte count mismatch: observed {len(payload)}, expected {spec.byte_count}"
        )
    return payload


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--group", required=True, type=int, choices=(1, 2))
    parser.add_argument("--input", required=True, help="Local materialized ESRM20 event-hazard INI")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        spec = _root_spec(args.group)
        result = extract_verified_event_hazard_dependencies(
            args.group,
            _read_regular_file(Path(args.input), spec),
        )
    except VerifiedEventHazardConfigError as exc:
        print(f"blocked: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(result, sort_keys=True, separators=(",", ":"), ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
