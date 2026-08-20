# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Project bounded runtime scalars from exact receipted ESRM20 Group1 config bytes.

This helper closes only a narrow consumer-reproducibility evidence gap. It first
reuses the canonical Group1 byte-count/SHA-256 authority, then parses the exact
INI text without interpolation and returns only explicitly configured runtime
scalars needed before a ground-up loss diagnostic. Missing settings remain
missing; no OpenQuake defaults are supplied or inferred.
"""

from __future__ import annotations

import ast
import configparser
from decimal import Decimal, InvalidOperation
import re
from typing import Any

from scripts import verify_esrm20_ebrisk_risk_config_dependencies as risk_config

SCHEMA_VERSION = "oc-esrm20-group1-risk-runtime-scalars-v1"
CONTROL_ISSUE = 579
SOURCE_ISSUE = risk_config.SOURCE_ISSUE
DATASET_ID = risk_config.DATASET_ID
PROJECT_ID = risk_config.PROJECT_ID
PROJECT_PATH = risk_config.PROJECT_PATH
COMMIT_SHA = risk_config.COMMIT_SHA
GROUP1_KEY = "group1"
GROUP1_SPEC = risk_config.config_spec(GROUP1_KEY)

# Frozen OpenQuake 3.14 configuration names/purposes relevant to this gate.
OPENQUAKE_REPOSITORY = "gem/oq-engine"
OPENQUAKE_TAG = "v3.14.0"
OPENQUAKE_COMMIT = "9f044c93d72846421a8faa90ebf0a6afacdf3c20"
_CALCULATION_MODE = "calculation_mode"
_MINIMUM_ASSET_LOSS = "minimum_asset_loss"
_IGNORE_MASTER_SEED = "ignore_master_seed"
_SEED_PURPOSES = {
    "master_seed": "vulnerability_epsilon_sampling",
    "random_seed": "logic_tree_sampling",
    "ses_seed": "ground_motion_field_generation",
}
_SEED_KEYS = frozenset(_SEED_PURPOSES)
_RELEVANT_KEYS = (
    frozenset({_CALCULATION_MODE, _MINIMUM_ASSET_LOSS, _IGNORE_MASTER_SEED})
    | _SEED_KEYS
)
_CALCULATION_MODES = frozenset(
    {
        "classical_risk",
        "classical_damage",
        "classical",
        "event_based",
        "scenario",
        "post_risk",
        "ebrisk",
        "scenario_risk",
        "event_based_risk",
        "disaggregation",
        "multi_risk",
        "classical_bcr",
        "preclassical",
        "conditional_spectrum",
        "event_based_damage",
        "scenario_damage",
    }
)
_OQ314_BOOLEAN_VALUES = {
    "": False,
    "0": False,
    "1": True,
    "false": False,
    "true": True,
}


class RiskRuntimeScalarError(ValueError):
    """Raised when exact Group1 runtime scalar projection cannot close safely."""


def _alias_identity(option: str) -> str:
    return re.sub(r"[_-]", "", option.casefold())


def _reject_runtime_alias(option: str) -> None:
    identity = _alias_identity(option)
    for canonical in _RELEVANT_KEYS:
        if identity == _alias_identity(canonical) and option != canonical:
            raise RiskRuntimeScalarError(
                f"runtime option alias/case drift is not allowed: {option}"
            )
    if "seed" in identity and option not in _RELEVANT_KEYS:
        raise RiskRuntimeScalarError(
            f"unsupported seed-like runtime option cannot be ignored: {option}"
        )


def _parse_ini(config_text: str) -> configparser.ConfigParser:
    if type(config_text) is not str or not config_text:
        raise RiskRuntimeScalarError("verified Group1 config text is absent")
    if any(ord(char) < 32 and char not in "\n\r\t" for char in config_text):
        raise RiskRuntimeScalarError("Group1 config contains control characters")

    parser = configparser.ConfigParser(
        interpolation=None,
        strict=True,
        empty_lines_in_values=False,
    )
    parser.optionxform = str
    try:
        parser.read_string(config_text)
    except configparser.Error as exc:
        raise RiskRuntimeScalarError(f"invalid Group1 INI configuration: {exc}") from exc
    if not parser.sections():
        raise RiskRuntimeScalarError("Group1 config must contain at least one section")

    for option in parser.defaults():
        _reject_runtime_alias(option)
        if option in _RELEVANT_KEYS:
            raise RiskRuntimeScalarError(
                f"runtime option {option} must not be inherited from DEFAULT"
            )
    return parser


def _collect_explicit_runtime_options(
    parser: configparser.ConfigParser,
) -> dict[str, tuple[str, str]]:
    found: dict[str, tuple[str, str]] = {}
    for section in parser.sections():
        # ConfigParser.items() merges DEFAULT values. Reading the explicit
        # section mapping is intentional so inherited runtime values cannot be
        # mistaken for source-declared values.
        explicit = parser._sections.get(section, {})  # noqa: SLF001
        for option, value in explicit.items():
            if option == "__name__":
                continue
            _reject_runtime_alias(option)
            if option not in _RELEVANT_KEYS:
                continue
            if option in found:
                previous = found[option][0]
                raise RiskRuntimeScalarError(
                    f"runtime option {option} appears in multiple sections: "
                    f"{previous}, {section}"
                )
            if type(value) is not str or value != value.strip():
                raise RiskRuntimeScalarError(
                    f"runtime option {option} must be trimmed text"
                )
            if not value and option != _IGNORE_MASTER_SEED:
                raise RiskRuntimeScalarError(
                    f"runtime option {option} must be non-empty"
                )
            found[option] = (section, value)
    return found


def _parse_mode(value: str) -> str:
    if value not in _CALCULATION_MODES:
        raise RiskRuntimeScalarError(
            "calculation_mode is outside the frozen OpenQuake 3.14 choices"
        )
    return value


def _parse_seed(value: str, key: str) -> int:
    # Mirror the pinned OpenQuake 3.14 ``valid.positiveint`` validator for
    # explicitly configured seeds: true/false map to 1/0, otherwise Python's
    # integer parser is used and only negative results are rejected.
    lowered = value.lower()
    if lowered == "true":
        return 1
    if lowered == "false":
        return 0
    try:
        parsed = int(lowered)
    except (TypeError, ValueError) as exc:
        raise RiskRuntimeScalarError(
            f"{key} must use frozen OpenQuake positiveint syntax"
        ) from exc
    if parsed < 0:
        raise RiskRuntimeScalarError(f"{key} must be non-negative")
    return parsed


def _parse_boolean(value: str, key: str) -> bool:
    try:
        return _OQ314_BOOLEAN_VALUES[value.casefold()]
    except KeyError as exc:
        raise RiskRuntimeScalarError(
            f"{key} must use frozen OpenQuake boolean syntax: empty, 0, 1, true or false"
        ) from exc


def _decimal_from_value(value: object) -> Decimal:
    if isinstance(value, bool):
        raise RiskRuntimeScalarError("minimum_asset_loss structural value cannot be boolean")
    if isinstance(value, (int, float, str, Decimal)):
        try:
            parsed = Decimal(str(value))
        except (InvalidOperation, ValueError) as exc:
            raise RiskRuntimeScalarError(
                "minimum_asset_loss structural value is not decimal"
            ) from exc
        if not parsed.is_finite() or parsed < 0:
            raise RiskRuntimeScalarError(
                "minimum_asset_loss structural value must be finite and non-negative"
            )
        return parsed
    raise RiskRuntimeScalarError("minimum_asset_loss structural value has unsupported type")


def _mapping_structural_value(value: str) -> Decimal:
    try:
        expression = ast.parse(value, mode="eval")
    except SyntaxError as exc:
        raise RiskRuntimeScalarError("minimum_asset_loss mapping is malformed") from exc
    if not isinstance(expression.body, ast.Dict):
        raise RiskRuntimeScalarError("minimum_asset_loss must be a decimal or mapping literal")

    keys: list[str] = []
    structural: object | None = None
    default: object | None = None
    for key_node, value_node in zip(expression.body.keys, expression.body.values, strict=True):
        try:
            key = ast.literal_eval(key_node)
        except (ValueError, SyntaxError) as exc:
            raise RiskRuntimeScalarError("minimum_asset_loss mapping key is invalid") from exc
        if type(key) is not str or not key:
            raise RiskRuntimeScalarError("minimum_asset_loss mapping keys must be strings")
        if key in keys:
            raise RiskRuntimeScalarError(f"duplicate minimum_asset_loss mapping key: {key}")
        keys.append(key)
        if key in {"structural", "default"}:
            try:
                parsed_value = ast.literal_eval(value_node)
            except (ValueError, SyntaxError) as exc:
                raise RiskRuntimeScalarError(
                    f"minimum_asset_loss {key} value is invalid"
                ) from exc
            if key == "structural":
                structural = parsed_value
            else:
                default = parsed_value

    selected = structural if structural is not None else default
    if selected is None:
        raise RiskRuntimeScalarError(
            "minimum_asset_loss mapping does not contain structural or default"
        )
    return _decimal_from_value(selected)


def _parse_minimum_asset_loss(value: str) -> Decimal:
    if value.startswith("{"):
        return _mapping_structural_value(value)
    return _decimal_from_value(value)


def _canonical_decimal(value: Decimal) -> str:
    text = format(value, "f")
    if "." in text:
        text = text.rstrip("0").rstrip(".")
    return text or "0"


def project_runtime_scalars_from_verified_text(config_text: str) -> dict[str, Any]:
    """Project only explicit runtime scalars from already identity-verified text."""

    options = _collect_explicit_runtime_options(_parse_ini(config_text))

    mode_entry = options.get(_CALCULATION_MODE)
    mode = _parse_mode(mode_entry[1]) if mode_entry is not None else None

    seed_settings = []
    for key in sorted(_SEED_KEYS):
        entry = options.get(key)
        if entry is None:
            continue
        seed_settings.append(
            {
                "key": key,
                "purpose": _SEED_PURPOSES[key],
                "section": entry[0],
                "value": _parse_seed(entry[1], key),
            }
        )

    ignore_entry = options.get(_IGNORE_MASTER_SEED)
    ignore_master_seed = (
        _parse_boolean(ignore_entry[1], _IGNORE_MASTER_SEED)
        if ignore_entry is not None
        else None
    )

    min_loss_entry = options.get(_MINIMUM_ASSET_LOSS)
    min_loss = (
        _canonical_decimal(_parse_minimum_asset_loss(min_loss_entry[1]))
        if min_loss_entry is not None
        else None
    )

    return {
        "calculation_mode": mode,
        "calculation_mode_present": mode_entry is not None,
        "configured_seed_settings": seed_settings,
        "seed_setting_present": bool(seed_settings),
        "ignore_master_seed": ignore_master_seed,
        "ignore_master_seed_present": ignore_entry is not None,
        "minimum_asset_loss_structural": min_loss,
        "minimum_asset_loss_structural_present": min_loss_entry is not None,
        "defaults_inferred": False,
        "vulnerability_sampling_seed_semantics_verified": False,
    }


def project_group1_risk_runtime_scalars(payload: bytes) -> dict[str, Any]:
    """Verify exact Group1 bytes before returning bounded scalar evidence."""

    digest = risk_config._verify_payload_identity(payload, GROUP1_SPEC)  # noqa: SLF001
    text = risk_config._decode_verified_payload(payload)  # noqa: SLF001
    scalars = project_runtime_scalars_from_verified_text(text)
    return {
        "schema_version": SCHEMA_VERSION,
        "control_issue": CONTROL_ISSUE,
        "source_issue": SOURCE_ISSUE,
        "dataset_id": DATASET_ID,
        "project_id": PROJECT_ID,
        "project_path": PROJECT_PATH,
        "commit_sha": COMMIT_SHA,
        "candidate_key": GROUP1_KEY,
        "repository_path": GROUP1_SPEC.repository_path,
        "byte_count": len(payload),
        "sha256": digest,
        "receipt_comment_id": risk_config.RECEIPT_COMMENT_ID,
        "openquake_reference": {
            "repository": OPENQUAKE_REPOSITORY,
            "tag": OPENQUAKE_TAG,
            "commit_sha": OPENQUAKE_COMMIT,
        },
        "runtime_scalars": scalars,
        "raw_config_returned": False,
        "historical_group_assignment_verified": False,
        "runtime_compatibility_verified": False,
        "numerical_loss_reproduction_verified": False,
        "external_bytes_persisted": False,
        "publication_authorized": False,
        "model_use_authorized": False,
    }
