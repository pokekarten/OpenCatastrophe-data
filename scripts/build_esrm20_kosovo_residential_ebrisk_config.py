# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Derive a deterministic Kosovo-residential ESRM20 ebrisk config.

The caller supplies the exact receipted ESRM20 v1.0 Group1 ebrisk INI bytes.
This module verifies that identity before interpretation, changes only the
provider-authorized country selectors for site and exposure, and returns a
canonical derived INI plus bounded evidence. Provider and derived bytes are not
persisted by this module.
"""

from __future__ import annotations

import configparser
import hashlib
import re
from typing import Any

from scripts import build_esrm20_kosovo_residential_exposure_wrapper as exposure_wrapper
from scripts import verify_esrm20_ebrisk_risk_config_dependencies as risk_config

_CANONICAL_SCHEMA_VERSION = "oc-esrm20-kosovo-residential-ebrisk-config-recipe-v1"
_CANONICAL_CONTROL_ISSUE = 609
_CANONICAL_UPSTREAM_WRAPPER_ISSUE = 611
_CANONICAL_SOURCE_ISSUE = 281
_CANONICAL_EXPERIMENT_LABEL = "reconstructed_experiment"
_CANONICAL_SCOPE = "kosovo_residential_only"
_CANONICAL_GROUP1_KEY = "group1"
_CANONICAL_GROUP1_PATH = "Configuration_files/config_ebrisk_Group1.ini"
_CANONICAL_GROUP1_BYTE_COUNT = 3052
_CANONICAL_GROUP1_SHA256 = (
    "be5f787954ca7e4060e4362d12efcf7cba5e50740930f3de7d7a521ebc580146"
)
_CANONICAL_PROJECT_ID = 269
_CANONICAL_PROJECT_PATH = "efehr/esrm20"
_CANONICAL_COMMIT_SHA = "05f83bbc9df81d02ee8ddb1801d9d781355ce783"
_CANONICAL_OUTPUT_LOGICAL_PATH = (
    "Configuration_files/config_ebrisk_Kosovo_Residential_Reconstructed.ini"
)
_CANONICAL_SITE_SECTION = "site_params"
_CANONICAL_SITE_OPTION = "site_model_file"
_CANONICAL_SITE_RAW_PATH = "../Vs30/Site_model_Kosovo.xml"
_CANONICAL_SITE_RESOLVED_PATH = "Vs30/Site_model_Kosovo.xml"
_CANONICAL_EXPOSURE_SECTION = "exposure"
_CANONICAL_EXPOSURE_OPTION = "exposure_file"
_CANONICAL_EXPOSURE_RAW_PATH = (
    "../Exposure/OQ_Exposure_Input_Kosovo_Residential_Reconstructed.xml"
)
_CANONICAL_EXPOSURE_RESOLVED_PATH = (
    "Exposure/OQ_Exposure_Input_Kosovo_Residential_Reconstructed.xml"
)
_CANONICAL_SOURCE_KOSOVO_EXPOSURE_RAW_PATH = "../Exposure/OQ_Exposure_Input_Kosovo.xml"
_CANONICAL_SOURCE_KOSOVO_SITE_RAW_PATH = "../Vs30/Site_model_Kosovo.xml"

_CANONICAL_SHARED_DEPENDENCIES = (
    (
        "logic_trees",
        "gsim_logic_tree_file",
        "../Hazard/gmpe_logic_tree_5br_slope_geology.xml",
        "Hazard/gmpe_logic_tree_5br_slope_geology.xml",
    ),
    (
        "logic_trees",
        "source_model_logic_tree_file",
        "../Hazard/source_model_logic_tree_eshm20_v12e_collapsed_risk_model.xml",
        "Hazard/source_model_logic_tree_eshm20_v12e_collapsed_risk_model.xml",
    ),
    (
        "exposure",
        "taxonomy_mapping_csv",
        "../Vulnerability/esrm20_exposure_vulnerability_mapping.csv",
        "Vulnerability/esrm20_exposure_vulnerability_mapping.csv",
    ),
    (
        "vulnerability",
        "occupants_vulnerability_file",
        "../Vulnerability/vulnerability_loss-of-life_ESRM20_VariousIM.xml",
        "Vulnerability/vulnerability_loss-of-life_ESRM20_VariousIM.xml",
    ),
    (
        "vulnerability",
        "structural_vulnerability_file",
        "../Vulnerability/vulnerability_total-repl-cost_ESRM20_VariousIM.xml",
        "Vulnerability/vulnerability_total-repl-cost_ESRM20_VariousIM.xml",
    ),
)

SCHEMA_VERSION = _CANONICAL_SCHEMA_VERSION
CONTROL_ISSUE = _CANONICAL_CONTROL_ISSUE
UPSTREAM_WRAPPER_ISSUE = _CANONICAL_UPSTREAM_WRAPPER_ISSUE
SOURCE_ISSUE = _CANONICAL_SOURCE_ISSUE
EXPERIMENT_LABEL = _CANONICAL_EXPERIMENT_LABEL
SCOPE = _CANONICAL_SCOPE
GROUP1_KEY = _CANONICAL_GROUP1_KEY
GROUP1_PATH = _CANONICAL_GROUP1_PATH
GROUP1_BYTE_COUNT = _CANONICAL_GROUP1_BYTE_COUNT
GROUP1_SHA256 = _CANONICAL_GROUP1_SHA256
PROJECT_ID = _CANONICAL_PROJECT_ID
PROJECT_PATH = _CANONICAL_PROJECT_PATH
COMMIT_SHA = _CANONICAL_COMMIT_SHA
OUTPUT_LOGICAL_PATH = _CANONICAL_OUTPUT_LOGICAL_PATH
SITE_SECTION = _CANONICAL_SITE_SECTION
SITE_OPTION = _CANONICAL_SITE_OPTION
SITE_RAW_PATH = _CANONICAL_SITE_RAW_PATH
SITE_RESOLVED_PATH = _CANONICAL_SITE_RESOLVED_PATH
EXPOSURE_SECTION = _CANONICAL_EXPOSURE_SECTION
EXPOSURE_OPTION = _CANONICAL_EXPOSURE_OPTION
EXPOSURE_RAW_PATH = _CANONICAL_EXPOSURE_RAW_PATH
EXPOSURE_RESOLVED_PATH = _CANONICAL_EXPOSURE_RESOLVED_PATH
SHARED_DEPENDENCIES = _CANONICAL_SHARED_DEPENDENCIES

_CANONICAL_VERIFY_PAYLOAD_IDENTITY = risk_config._verify_payload_identity  # noqa: SLF001
_CANONICAL_DECODE_VERIFIED_PAYLOAD = risk_config._decode_verified_payload  # noqa: SLF001
_CANONICAL_EXTRACT_DEPENDENCIES = risk_config.extract_dependencies_from_verified_text


class KosovoResidentialEbriskConfigError(ValueError):
    """The source Group1 config or derived Kosovo recipe is invalid."""


def _require_canonical_authority() -> None:
    identities = (
        (SCHEMA_VERSION, _CANONICAL_SCHEMA_VERSION, "schema version"),
        (CONTROL_ISSUE, _CANONICAL_CONTROL_ISSUE, "control issue"),
        (
            UPSTREAM_WRAPPER_ISSUE,
            _CANONICAL_UPSTREAM_WRAPPER_ISSUE,
            "upstream wrapper issue",
        ),
        (SOURCE_ISSUE, _CANONICAL_SOURCE_ISSUE, "source issue"),
        (EXPERIMENT_LABEL, _CANONICAL_EXPERIMENT_LABEL, "experiment label"),
        (SCOPE, _CANONICAL_SCOPE, "scope"),
        (GROUP1_KEY, _CANONICAL_GROUP1_KEY, "Group1 key"),
        (GROUP1_PATH, _CANONICAL_GROUP1_PATH, "Group1 path"),
        (GROUP1_BYTE_COUNT, _CANONICAL_GROUP1_BYTE_COUNT, "Group1 byte count"),
        (GROUP1_SHA256, _CANONICAL_GROUP1_SHA256, "Group1 SHA-256"),
        (PROJECT_ID, _CANONICAL_PROJECT_ID, "project"),
        (PROJECT_PATH, _CANONICAL_PROJECT_PATH, "project path"),
        (COMMIT_SHA, _CANONICAL_COMMIT_SHA, "commit"),
        (OUTPUT_LOGICAL_PATH, _CANONICAL_OUTPUT_LOGICAL_PATH, "output path"),
        (SITE_SECTION, _CANONICAL_SITE_SECTION, "site section"),
        (SITE_OPTION, _CANONICAL_SITE_OPTION, "site option"),
        (SITE_RAW_PATH, _CANONICAL_SITE_RAW_PATH, "site path"),
        (SITE_RESOLVED_PATH, _CANONICAL_SITE_RESOLVED_PATH, "site resolved path"),
        (EXPOSURE_SECTION, _CANONICAL_EXPOSURE_SECTION, "exposure section"),
        (EXPOSURE_OPTION, _CANONICAL_EXPOSURE_OPTION, "exposure option"),
        (EXPOSURE_RAW_PATH, _CANONICAL_EXPOSURE_RAW_PATH, "exposure path"),
        (
            EXPOSURE_RESOLVED_PATH,
            _CANONICAL_EXPOSURE_RESOLVED_PATH,
            "exposure resolved path",
        ),
        (
            SHARED_DEPENDENCIES,
            _CANONICAL_SHARED_DEPENDENCIES,
            "shared dependency set",
        ),
    )
    for observed, expected, label in identities:
        if type(observed) is not type(expected) or observed != expected:
            raise KosovoResidentialEbriskConfigError(f"{label} authority drifted")

    spec = risk_config.config_spec(_CANONICAL_GROUP1_KEY)
    spec_authority = (
        (spec.repository_path, _CANONICAL_GROUP1_PATH, "risk config path"),
        (spec.byte_count, _CANONICAL_GROUP1_BYTE_COUNT, "risk config byte count"),
        (spec.sha256, _CANONICAL_GROUP1_SHA256, "risk config SHA-256"),
        (risk_config.PROJECT_ID, _CANONICAL_PROJECT_ID, "risk config project"),
        (risk_config.PROJECT_PATH, _CANONICAL_PROJECT_PATH, "risk config project path"),
        (risk_config.COMMIT_SHA, _CANONICAL_COMMIT_SHA, "risk config commit"),
    )
    for observed, expected, label in spec_authority:
        if type(observed) is not type(expected) or observed != expected:
            raise KosovoResidentialEbriskConfigError(f"{label} authority drifted")

    if risk_config._verify_payload_identity is not _CANONICAL_VERIFY_PAYLOAD_IDENTITY:  # noqa: SLF001
        raise KosovoResidentialEbriskConfigError("risk config identity verifier drifted")
    if risk_config._decode_verified_payload is not _CANONICAL_DECODE_VERIFIED_PAYLOAD:  # noqa: SLF001
        raise KosovoResidentialEbriskConfigError("risk config decoder drifted")
    if risk_config.extract_dependencies_from_verified_text is not _CANONICAL_EXTRACT_DEPENDENCIES:
        raise KosovoResidentialEbriskConfigError("risk config dependency parser drifted")

    wrapper_authority = (
        (
            exposure_wrapper.OUTPUT_LOGICAL_PATH,
            _CANONICAL_EXPOSURE_RESOLVED_PATH,
            "residential wrapper output path",
        ),
        (
            exposure_wrapper.EXPERIMENT_LABEL,
            _CANONICAL_EXPERIMENT_LABEL,
            "residential wrapper experiment label",
        ),
        (exposure_wrapper.SCOPE, _CANONICAL_SCOPE, "residential wrapper scope"),
        (
            exposure_wrapper.CONTROL_ISSUE,
            _CANONICAL_UPSTREAM_WRAPPER_ISSUE,
            "residential wrapper control issue",
        ),
        (exposure_wrapper.PROJECT_ID, _CANONICAL_PROJECT_ID, "residential wrapper project"),
        (
            exposure_wrapper.COMMIT_SHA,
            _CANONICAL_COMMIT_SHA,
            "residential wrapper commit",
        ),
    )
    for observed, expected, label in wrapper_authority:
        if type(observed) is not type(expected) or observed != expected:
            raise KosovoResidentialEbriskConfigError(f"{label} authority drifted")


def _verify_group1_identity(source_config: bytes) -> str:
    if type(source_config) is not bytes:
        raise KosovoResidentialEbriskConfigError("source Group1 config must be bytes")
    spec = risk_config.config_spec(GROUP1_KEY)
    try:
        return risk_config._verify_payload_identity(source_config, spec)  # noqa: SLF001
    except risk_config.VerifiedEbriskConfigError as exc:
        raise KosovoResidentialEbriskConfigError(
            "source Group1 config byte identity mismatch"
        ) from exc


def _decode_group1(source_config: bytes) -> str:
    try:
        return risk_config._decode_verified_payload(source_config)  # noqa: SLF001
    except risk_config.VerifiedEbriskConfigError as exc:
        raise KosovoResidentialEbriskConfigError(
            "verified Group1 config is not strict UTF-8"
        ) from exc


def _parse_ini(config_text: str) -> configparser.ConfigParser:
    if type(config_text) is not str or not config_text:
        raise KosovoResidentialEbriskConfigError("config text is absent")
    if any(ord(char) < 32 and char not in "\n\r\t" for char in config_text):
        raise KosovoResidentialEbriskConfigError("config text contains control characters")

    parser = configparser.ConfigParser(
        interpolation=None,
        strict=True,
        empty_lines_in_values=False,
    )
    parser.optionxform = str
    try:
        parser.read_string(config_text)
    except configparser.Error as exc:
        raise KosovoResidentialEbriskConfigError("invalid INI configuration") from exc
    if not parser.sections():
        raise KosovoResidentialEbriskConfigError(
            "configuration must contain at least one section"
        )
    return parser


def _alias_identity(option: str) -> str:
    return re.sub(r"[_-]", "", option.casefold())


def _reject_target_aliases(parser: configparser.ConfigParser) -> None:
    target_options = (SITE_OPTION, EXPOSURE_OPTION)
    for option in parser.defaults():
        for target in target_options:
            if _alias_identity(option) == _alias_identity(target):
                raise KosovoResidentialEbriskConfigError(
                    f"{target} must be an explicit canonical section option"
                )

    for section in parser.sections():
        explicit = parser._sections.get(section, {})  # noqa: SLF001
        for option in explicit:
            if option == "__name__":
                continue
            for target in target_options:
                if _alias_identity(option) == _alias_identity(target) and option != target:
                    raise KosovoResidentialEbriskConfigError(
                        f"{target} alias/case drift is not allowed"
                    )


def _locate_target(
    parser: configparser.ConfigParser,
    *,
    option: str,
    expected_section: str,
) -> str:
    found: list[tuple[str, str]] = []
    for section in parser.sections():
        explicit = parser._sections.get(section, {})  # noqa: SLF001
        if option in explicit:
            found.append((section, explicit[option]))
    if len(found) != 1:
        raise KosovoResidentialEbriskConfigError(
            f"{option} must appear exactly once as an explicit option"
        )
    section, value = found[0]
    if section != expected_section:
        raise KosovoResidentialEbriskConfigError(
            f"{option} must remain in [{expected_section}]"
        )
    return value


def _semantic_map(parser: configparser.ConfigParser) -> dict[tuple[str, str], str]:
    result: dict[tuple[str, str], str] = {}
    for option, value in parser.defaults().items():
        result[("DEFAULT", option)] = value
    for section in parser.sections():
        explicit = parser._sections.get(section, {})  # noqa: SLF001
        for option, value in explicit.items():
            if option == "__name__":
                continue
            result[(section, option)] = value
    return result


def _validate_name(value: str, *, label: str, forbidden: str) -> None:
    if not value or value != value.strip():
        raise KosovoResidentialEbriskConfigError(f"{label} is not canonical")
    if any(ord(char) < 32 for char in value) or any(char in value for char in forbidden):
        raise KosovoResidentialEbriskConfigError(f"{label} is not serializable")


def _emit_option(option: str, value: str) -> list[str]:
    _validate_name(option, label="option name", forbidden="=:")
    if type(value) is not str:
        raise KosovoResidentialEbriskConfigError("option value must be text")
    if any(ord(char) < 32 and char not in "\n\t" for char in value):
        raise KosovoResidentialEbriskConfigError("option value contains control characters")
    parts = value.split("\n")
    lines = [f"{option} = {parts[0]}\n"]
    lines.extend(f"    {part}\n" for part in parts[1:])
    return lines


def _serialize_canonical(parser: configparser.ConfigParser) -> bytes:
    lines: list[str] = []
    defaults = parser.defaults()
    if defaults:
        lines.append("[DEFAULT]\n")
        for option in sorted(defaults):
            lines.extend(_emit_option(option, defaults[option]))
        lines.append("\n")

    for section in sorted(parser.sections()):
        _validate_name(section, label="section name", forbidden="[]")
        lines.append(f"[{section}]\n")
        explicit = parser._sections.get(section, {})  # noqa: SLF001
        for option in sorted(key for key in explicit if key != "__name__"):
            lines.extend(_emit_option(option, explicit[option]))
        lines.append("\n")
    return "".join(lines).encode("utf-8")


def _dependency_rows(
    config_text: str,
) -> list[dict[str, str]]:
    try:
        return risk_config.extract_dependencies_from_verified_text(
            config_text,
            repository_path=GROUP1_PATH,
        )
    except risk_config.VerifiedEbriskConfigError as exc:
        raise KosovoResidentialEbriskConfigError(
            "config dependency parse failed"
        ) from exc


def _dependency_identity(row: dict[str, str]) -> tuple[str, str, str, str]:
    return (
        row["section"],
        row["option"],
        row["raw_path"],
        row["resolved_path"],
    )


def _validate_source_dependencies(rows: list[dict[str, str]]) -> tuple[tuple[str, str, str, str], ...]:
    identities = tuple(_dependency_identity(row) for row in rows)
    source_site = (
        SITE_SECTION,
        SITE_OPTION,
        _CANONICAL_SOURCE_KOSOVO_SITE_RAW_PATH,
        SITE_RESOLVED_PATH,
    )
    source_exposure = (
        EXPOSURE_SECTION,
        EXPOSURE_OPTION,
        _CANONICAL_SOURCE_KOSOVO_EXPOSURE_RAW_PATH,
        "Exposure/OQ_Exposure_Input_Kosovo.xml",
    )
    if identities.count(source_site) != 1:
        raise KosovoResidentialEbriskConfigError(
            "source Group1 Kosovo site dependency is absent or ambiguous"
        )
    if identities.count(source_exposure) != 1:
        raise KosovoResidentialEbriskConfigError(
            "source Group1 Kosovo exposure dependency is absent or ambiguous"
        )
    shared = tuple(
        identity
        for identity in identities
        if identity[1] not in {SITE_OPTION, EXPOSURE_OPTION}
    )
    if tuple(sorted(shared)) != tuple(sorted(SHARED_DEPENDENCIES)):
        raise KosovoResidentialEbriskConfigError(
            "source Group1 shared dependency surface drifted"
        )
    return shared


def _validate_derived_dependencies(
    rows: list[dict[str, str]],
    shared: tuple[tuple[str, str, str, str], ...],
) -> None:
    expected = tuple(sorted(
        (
            *shared,
            (SITE_SECTION, SITE_OPTION, SITE_RAW_PATH, SITE_RESOLVED_PATH),
            (
                EXPOSURE_SECTION,
                EXPOSURE_OPTION,
                EXPOSURE_RAW_PATH,
                EXPOSURE_RESOLVED_PATH,
            ),
        )
    ))
    observed = tuple(sorted(_dependency_identity(row) for row in rows))
    if observed != expected:
        raise KosovoResidentialEbriskConfigError(
            "derived dependency surface is not the bounded Kosovo residential set"
        )


def _derive_from_verified_text(
    source_text: str,
    *,
    source_digest: str = _CANONICAL_GROUP1_SHA256,
) -> tuple[bytes, dict[str, Any]]:
    source_parser = _parse_ini(source_text)
    _reject_target_aliases(source_parser)
    source_site_value = _locate_target(
        source_parser,
        option=SITE_OPTION,
        expected_section=SITE_SECTION,
    )
    source_exposure_value = _locate_target(
        source_parser,
        option=EXPOSURE_OPTION,
        expected_section=EXPOSURE_SECTION,
    )
    if _CANONICAL_SOURCE_KOSOVO_SITE_RAW_PATH not in source_site_value.split():
        raise KosovoResidentialEbriskConfigError(
            "source Group1 site selector does not contain Kosovo"
        )
    if _CANONICAL_SOURCE_KOSOVO_EXPOSURE_RAW_PATH not in source_exposure_value.split():
        raise KosovoResidentialEbriskConfigError(
            "source Group1 exposure selector does not contain Kosovo"
        )

    source_dependencies = _dependency_rows(source_text)
    shared_dependencies = _validate_source_dependencies(source_dependencies)
    before = _semantic_map(source_parser)

    derived_parser = _parse_ini(source_text)
    derived_parser.set(SITE_SECTION, SITE_OPTION, SITE_RAW_PATH)
    derived_parser.set(EXPOSURE_SECTION, EXPOSURE_OPTION, EXPOSURE_RAW_PATH)
    derived_bytes = _serialize_canonical(derived_parser)
    try:
        derived_text = derived_bytes.decode("utf-8", errors="strict")
    except UnicodeDecodeError as exc:  # pragma: no cover - serializer is UTF-8 by construction
        raise KosovoResidentialEbriskConfigError(
            "derived config is not strict UTF-8"
        ) from exc

    reparsed = _parse_ini(derived_text)
    after = _semantic_map(reparsed)
    if set(before) != set(after):
        raise KosovoResidentialEbriskConfigError(
            "derived config added or removed semantic options"
        )

    changes = {
        key: (before[key], after[key])
        for key in before
        if before[key] != after[key]
    }
    expected_changes = {
        (SITE_SECTION, SITE_OPTION),
        (EXPOSURE_SECTION, EXPOSURE_OPTION),
    }
    if set(changes) != expected_changes:
        raise KosovoResidentialEbriskConfigError(
            "derived config semantic diff is not exactly the two country selectors"
        )
    if after[(SITE_SECTION, SITE_OPTION)] != SITE_RAW_PATH:
        raise KosovoResidentialEbriskConfigError("derived site selector drifted")
    if after[(EXPOSURE_SECTION, EXPOSURE_OPTION)] != EXPOSURE_RAW_PATH:
        raise KosovoResidentialEbriskConfigError("derived exposure selector drifted")

    derived_dependencies = _dependency_rows(derived_text)
    _validate_derived_dependencies(derived_dependencies, shared_dependencies)

    derived_digest = hashlib.sha256(derived_bytes).hexdigest()
    evidence: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "issues": {
            "source": SOURCE_ISSUE,
            "control": CONTROL_ISSUE,
            "upstream_wrapper": UPSTREAM_WRAPPER_ISSUE,
        },
        "source_config": {
            "project_id": PROJECT_ID,
            "project_path": PROJECT_PATH,
            "commit_sha": COMMIT_SHA,
            "candidate_key": GROUP1_KEY,
            "repository_path": GROUP1_PATH,
            "byte_count": GROUP1_BYTE_COUNT,
            "sha256": source_digest,
        },
        "output": {
            "logical_path": OUTPUT_LOGICAL_PATH,
            "media_type": "text/plain; charset=utf-8",
            "byte_count": len(derived_bytes),
            "sha256": derived_digest,
        },
        "semantic_changes": [
            {
                "section": EXPOSURE_SECTION,
                "option": EXPOSURE_OPTION,
                "derived_value": EXPOSURE_RAW_PATH,
            },
            {
                "section": SITE_SECTION,
                "option": SITE_OPTION,
                "derived_value": SITE_RAW_PATH,
            },
        ],
        "derived_dependencies": derived_dependencies,
        "semantic_change_count": 2,
        "source_dependency_count": len(source_dependencies),
        "derived_dependency_count": len(derived_dependencies),
        "full_semantic_diff_verified": True,
        "non_country_dependencies_preserved": True,
        "runtime_settings_preserved": True,
        "minimum_asset_loss_structural_preserved": True,
        "experiment_label": EXPERIMENT_LABEL,
        "scope": SCOPE,
        "source_config_bytes_returned": False,
        "derived_config_bytes_returned": True,
        "external_bytes_persisted": False,
        "historical_group_assignment_verified": False,
        "runtime_compatibility_verified": False,
        "vulnerability_horizontal_component_verified": False,
        "horizontal_component_conversion_authorized": False,
        "numerical_loss_reproduction_verified": False,
        "publication_authorized": False,
        "model_use_authorized": False,
    }
    return derived_bytes, evidence


def build_kosovo_residential_ebrisk_config(
    source_config: bytes,
) -> tuple[bytes, dict[str, Any]]:
    """Return a deterministic Kosovo-residential ebrisk config and evidence."""
    _require_canonical_authority()
    digest = _verify_group1_identity(source_config)
    source_text = _decode_group1(source_config)
    return _derive_from_verified_text(source_text, source_digest=digest)
