# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Bounded OpenQuake 3.13 runner adapter for the EQ1 Kosovo ebrisk experiment.

This module deliberately does not acquire provider inputs or publish numerical
results. A trusted execution environment must stage the already-authorized fixed
input envelope at the repository-defined logical paths and provide a source/runtime
identity probe. The adapter then verifies the exact derived configuration, checks
the pre-run OpenQuake/scalar boundary, injects the required child-process
environment, and invokes only ``oq engine --run`` for that one config.

A PASS means only that the fixed native OpenQuake process exited successfully under
the receipted runtime boundary. It is not a historical reproduction, numerical
validation, benchmark, publication approval, insured-loss result, or model-use
authorization.
"""

from __future__ import annotations

import ast
import configparser
import hashlib
import json
import os
import re
import subprocess
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from scripts import build_esrm20_kosovo_residential_ebrisk_config as config_builder
from scripts import project_oq313_risk_by_event_receipt as risk_receipt

SCHEMA_VERSION = "oc-esrm20-kosovo-residential-oq313-run-adapter-v1"
CONTROL_ISSUE = 609
PARENT_CONSUMER_ISSUE = 287
EXPERIMENT_LABEL = "reconstructed_experiment"
SCOPE = "kosovo_residential_only"

OPENQUAKE_REPOSITORY = "gem/oq-engine"
OPENQUAKE_VERSION = "3.13.0"
OPENQUAKE_SOURCE_VERSION = "3.13.0-git16dd69ecea"
OPENQUAKE_COMMIT_SHA = "16dd69ecea0c6dcaf49c22ca12edc9da3f024889"
OPENQUAKE_SOURCE_OVERLAY = "/oq-engine"
PYTHON_MAJOR_MINOR = "3.8"
OPENBLAS_NUM_THREADS = "1"
OQ_DISTRIBUTE = "no"

CONFIG_LOGICAL_PATH = (
    "Configuration_files/config_ebrisk_Kosovo_Residential_Reconstructed.ini"
)
MINIMUM_ASSET_LOSS_STRUCTURAL = 2000
RANDOM_SEED = 113
OPENQUAKE_DEFAULT_SES_SEED = 42
LOSS_TYPE = "structural"
UNIT = "EUR"
QUANTITY = "thresholded_ground_up_structural_replacement_cost_loss"
THRESHOLD_PREDICATE = "asset_event_loss > minimum_asset_loss_structural"
LOSS_STAGE = "thresholded_ground_up"

COMMAND = ("oq", "engine", "--run", CONFIG_LOGICAL_PATH)
NATIVE_STDERR_HASH_CHUNK_BYTES = 64 * 1024

EXPECTED_DEPENDENCY_VERSIONS = {
    "h5py": "3.1.0",
    "numpy": "1.20.0",
    "pandas": "1.1.5",
    "psutil": "5.6.7",
    "pyzmq": "19.0.0",
    "scipy": "1.4.1",
    "shapely": "1.7.1",
}

_RUNTIME_IDENTITY_FIELDS = frozenset(
    {
        "repository",
        "commit_sha",
        "openquake_version",
        "python_major_minor",
        "dependency_versions",
        "source_commit_verified",
        "bootstrap_image_digest",
        "execution_image_id",
    }
)
_RESOLVED_RUNTIME_FIELDS = frozenset(
    {
        "calculation_mode",
        "random_seed",
        "random_seed_provenance",
        "ignore_master_seed",
        "ignore_master_seed_provenance",
        "ses_seed",
        "ses_seed_provenance",
        "minimum_asset_loss_structural",
        "minimum_asset_loss_provenance",
        "concurrent_tasks",
    }
)
_IMAGE_DIGEST_RE = re.compile(r"^sha256:[0-9a-f]{64}$")


class KosovoResidentialOQ313RunError(RuntimeError):
    """The fixed OQ3.13 execution contract was not satisfied."""


class _NativeExitCode(int):
    """Integer exit code carrying bounded non-content failure evidence."""

    diagnostic: dict[str, object]

    def __new__(cls, value: int, diagnostic: dict[str, object]) -> _NativeExitCode:
        instance = int.__new__(cls, value)
        instance.diagnostic = diagnostic
        return instance


def _require_authority() -> None:
    exact = (
        (config_builder.CONTROL_ISSUE, CONTROL_ISSUE, "config control issue"),
        (config_builder.EXPERIMENT_LABEL, EXPERIMENT_LABEL, "experiment label"),
        (config_builder.SCOPE, SCOPE, "scope"),
        (config_builder.OUTPUT_LOGICAL_PATH, CONFIG_LOGICAL_PATH, "config path"),
        (
            risk_receipt.OPENQUAKE_VERSION,
            OPENQUAKE_VERSION,
            "risk receipt OpenQuake version",
        ),
        (
            risk_receipt.OPENQUAKE_COMMIT_SHA,
            OPENQUAKE_COMMIT_SHA,
            "risk receipt OpenQuake commit",
        ),
        (
            risk_receipt.MINIMUM_ASSET_LOSS_STRUCTURAL,
            MINIMUM_ASSET_LOSS_STRUCTURAL,
            "risk receipt threshold",
        ),
        (risk_receipt.LOSS_TYPE, LOSS_TYPE, "risk receipt loss type"),
        (risk_receipt.UNIT, UNIT, "risk receipt unit"),
        (risk_receipt.QUANTITY, QUANTITY, "risk receipt quantity"),
    )
    for observed, expected, label in exact:
        if type(observed) is not type(expected) or observed != expected:
            raise KosovoResidentialOQ313RunError(f"{label} authority drifted")


def _require_mapping(
    value: object,
    *,
    fields: frozenset[str],
    label: str,
) -> dict[str, object]:
    if not isinstance(value, Mapping):
        raise KosovoResidentialOQ313RunError(f"{label} must be a mapping")
    normalized = dict(value)
    if set(normalized) != fields:
        raise KosovoResidentialOQ313RunError(f"{label} fields drifted")
    return normalized


def _validate_runtime_identity(value: object) -> dict[str, Any]:
    identity = _require_mapping(
        value,
        fields=_RUNTIME_IDENTITY_FIELDS,
        label="runtime identity",
    )
    exact = (
        ("repository", OPENQUAKE_REPOSITORY),
        ("commit_sha", OPENQUAKE_COMMIT_SHA),
        ("openquake_version", OPENQUAKE_SOURCE_VERSION),
        ("python_major_minor", PYTHON_MAJOR_MINOR),
        ("source_commit_verified", True),
    )
    for field, expected in exact:
        observed = identity[field]
        if type(observed) is not type(expected) or observed != expected:
            raise KosovoResidentialOQ313RunError(
                f"runtime identity {field} drifted"
            )

    dependencies = identity["dependency_versions"]
    if type(dependencies) is not dict or dependencies != EXPECTED_DEPENDENCY_VERSIONS:
        raise KosovoResidentialOQ313RunError(
            "runtime dependency version receipt drifted"
        )

    for field in ("bootstrap_image_digest", "execution_image_id"):
        digest = identity[field]
        if type(digest) is not str or _IMAGE_DIGEST_RE.fullmatch(digest) is None:
            raise KosovoResidentialOQ313RunError(
                f"runtime identity {field} must be an immutable sha256 digest"
            )
    return identity


def _validate_resolved_runtime(value: object) -> dict[str, Any]:
    runtime = _require_mapping(
        value,
        fields=_RESOLVED_RUNTIME_FIELDS,
        label="resolved runtime",
    )
    exact = (
        ("calculation_mode", "ebrisk"),
        ("random_seed", RANDOM_SEED),
        ("random_seed_provenance", "source_declared"),
        ("ignore_master_seed", True),
        ("ignore_master_seed_provenance", "source_declared"),
        (
            "ses_seed_provenance",
            "openquake_default_resolved_from_source_absence",
        ),
        (
            "minimum_asset_loss_structural",
            MINIMUM_ASSET_LOSS_STRUCTURAL,
        ),
        ("minimum_asset_loss_provenance", "source_declared"),
    )
    for field, expected in exact:
        observed = runtime[field]
        if type(observed) is not type(expected) or observed != expected:
            raise KosovoResidentialOQ313RunError(
                f"resolved runtime {field} drifted"
            )

    ses_seed = runtime["ses_seed"]
    if type(ses_seed) is not int or ses_seed != OPENQUAKE_DEFAULT_SES_SEED:
        raise KosovoResidentialOQ313RunError(
            "resolved runtime ses_seed must equal the pinned OpenQuake 3.13 default"
        )
    concurrent_tasks = runtime["concurrent_tasks"]
    if type(concurrent_tasks) is not int or concurrent_tasks < 0:
        raise KosovoResidentialOQ313RunError(
            "resolved runtime concurrent_tasks must be a non-negative integer"
        )
    return runtime


def _parse_derived_ini(payload: bytes) -> configparser.ConfigParser:
    if type(payload) is not bytes or not payload:
        raise KosovoResidentialOQ313RunError("derived config must be non-empty bytes")
    try:
        text = payload.decode("utf-8", errors="strict")
    except UnicodeDecodeError as exc:
        raise KosovoResidentialOQ313RunError(
            "derived config must be strict UTF-8"
        ) from exc
    parser = configparser.ConfigParser(
        interpolation=None,
        strict=True,
        empty_lines_in_values=False,
    )
    parser.optionxform = str
    try:
        parser.read_string(text)
    except configparser.Error as exc:
        raise KosovoResidentialOQ313RunError("derived config is invalid INI") from exc
    return parser


def _alias_identity(option: str) -> str:
    return option.casefold().replace("_", "").replace("-", "")


def _explicit_values(parser: configparser.ConfigParser, option: str) -> list[str]:
    values: list[str] = []
    if option in parser.defaults():
        raise KosovoResidentialOQ313RunError(
            f"runtime option {option} must not be inherited from DEFAULT"
        )
    target_identity = _alias_identity(option)
    for section in parser.sections():
        explicit = parser._sections.get(section, {})  # noqa: SLF001
        for key, value in explicit.items():
            if key == "__name__":
                continue
            if _alias_identity(key) == target_identity and key != option:
                raise KosovoResidentialOQ313RunError(
                    f"runtime option {option} alias/case drifted"
                )
            if key == option:
                values.append(value)
    return values


def _one_explicit(parser: configparser.ConfigParser, option: str) -> str:
    values = _explicit_values(parser, option)
    if len(values) != 1:
        raise KosovoResidentialOQ313RunError(
            f"runtime option {option} must appear exactly once"
        )
    value = values[0]
    if type(value) is not str or value != value.strip():
        raise KosovoResidentialOQ313RunError(
            f"runtime option {option} must be canonical text"
        )
    return value


def _validate_source_runtime_declarations(payload: bytes) -> dict[str, Any]:
    parser = _parse_derived_ini(payload)

    calculation_mode = _one_explicit(parser, "calculation_mode")
    if calculation_mode != "ebrisk":
        raise KosovoResidentialOQ313RunError(
            "source calculation_mode must be exactly ebrisk"
        )

    random_seed_text = _one_explicit(parser, "random_seed")
    try:
        random_seed = int(random_seed_text)
    except ValueError as exc:
        raise KosovoResidentialOQ313RunError(
            "source random_seed must be an integer"
        ) from exc
    if random_seed != RANDOM_SEED:
        raise KosovoResidentialOQ313RunError("source random_seed drifted")

    ignore_master_seed_text = _one_explicit(parser, "ignore_master_seed")
    if ignore_master_seed_text.casefold() != "true":
        raise KosovoResidentialOQ313RunError("source ignore_master_seed drifted")

    if _explicit_values(parser, "ses_seed"):
        raise KosovoResidentialOQ313RunError(
            "source ses_seed must remain absent for default-derived provenance"
        )

    minimum_text = _one_explicit(parser, "minimum_asset_loss")
    try:
        minimum = ast.literal_eval(minimum_text)
    except (SyntaxError, ValueError) as exc:
        raise KosovoResidentialOQ313RunError(
            "source minimum_asset_loss is not a literal mapping"
        ) from exc
    if (
        type(minimum) is not dict
        or "structural" not in minimum
        or type(minimum["structural"]) is not int
        or minimum["structural"] != MINIMUM_ASSET_LOSS_STRUCTURAL
    ):
        raise KosovoResidentialOQ313RunError(
            "source minimum_asset_loss structural threshold drifted"
        )

    return {
        "calculation_mode": calculation_mode,
        "random_seed": random_seed,
        "random_seed_provenance": "source_declared",
        "ignore_master_seed": True,
        "ignore_master_seed_provenance": "source_declared",
        "ses_seed_source_present": False,
        "minimum_asset_loss_structural": MINIMUM_ASSET_LOSS_STRUCTURAL,
        "minimum_asset_loss_provenance": "source_declared",
    }


def _validate_config_evidence(
    derived_config: bytes,
    evidence: object,
) -> dict[str, Any]:
    if type(evidence) is not dict:
        raise KosovoResidentialOQ313RunError("config evidence must be a mapping")
    output = evidence.get("output")
    if type(output) is not dict:
        raise KosovoResidentialOQ313RunError("config evidence output is missing")

    digest = hashlib.sha256(derived_config).hexdigest()
    exact = (
        (output.get("logical_path"), CONFIG_LOGICAL_PATH, "logical path"),
        (output.get("byte_count"), len(derived_config), "byte count"),
        (output.get("sha256"), digest, "SHA-256"),
        (
            evidence.get("experiment_label"),
            EXPERIMENT_LABEL,
            "experiment label",
        ),
        (evidence.get("scope"), SCOPE, "scope"),
        (
            evidence.get("full_semantic_diff_verified"),
            True,
            "semantic diff verification",
        ),
        (
            evidence.get("runtime_settings_preserved"),
            True,
            "runtime settings preservation",
        ),
        (
            evidence.get("minimum_asset_loss_structural_preserved"),
            True,
            "threshold preservation",
        ),
    )
    for observed, expected, label in exact:
        if type(observed) is not type(expected) or observed != expected:
            raise KosovoResidentialOQ313RunError(
                f"config evidence {label} drifted"
            )

    for field in (
        "historical_group_assignment_verified",
        "runtime_compatibility_verified",
        "vulnerability_horizontal_component_verified",
        "horizontal_component_conversion_authorized",
        "numerical_loss_reproduction_verified",
        "publication_authorized",
        "model_use_authorized",
    ):
        if evidence.get(field) is not False:
            raise KosovoResidentialOQ313RunError(
                f"config evidence authority boundary {field} drifted"
            )
    return evidence


def _read_staged_config() -> bytes:
    try:
        return Path(CONFIG_LOGICAL_PATH).read_bytes()
    except OSError as exc:
        raise KosovoResidentialOQ313RunError(
            "fixed derived config is not staged at its canonical path"
        ) from exc


def _stderr_diagnostic(stderr_stream: Any) -> dict[str, object]:
    byte_count = 0
    digest = hashlib.sha256()
    while True:
        chunk = stderr_stream.read(NATIVE_STDERR_HASH_CHUNK_BYTES)
        if not chunk:
            break
        if type(chunk) is not bytes:
            raise KosovoResidentialOQ313RunError(
                "OpenQuake stderr stream returned non-byte content"
            )
        byte_count += len(chunk)
        digest.update(chunk)
    return {
        "byte_count": byte_count,
        "sha256": digest.hexdigest(),
        "content_exposed": False,
    }


def _execute_native(command: Sequence[str], env: Mapping[str, str]) -> int:
    with subprocess.Popen(
        list(command),
        env=dict(env),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
    ) as process:
        stderr_stream = process.stderr
        if stderr_stream is None:
            raise KosovoResidentialOQ313RunError(
                "OpenQuake subprocess stderr pipe is unavailable"
            )
        diagnostic = _stderr_diagnostic(stderr_stream)
        returncode = process.wait()

    if type(returncode) is not int:
        raise KosovoResidentialOQ313RunError(
            "OpenQuake subprocess returned a non-integer exit code"
        )
    if returncode == 0:
        return returncode
    return _NativeExitCode(returncode, diagnostic)


def _canonical_payload(document: dict[str, Any]) -> tuple[bytes, dict[str, Any]]:
    payload = (
        json.dumps(
            document,
            ensure_ascii=True,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")
        + b"\n"
    )
    return payload, {
        "byte_count": len(payload),
        "sha256": hashlib.sha256(payload).hexdigest(),
    }


def _run_derived_config(
    derived_config: bytes,
    config_evidence: object,
    *,
    runtime_identity: object,
    resolved_runtime: object,
) -> tuple[bytes, dict[str, Any]]:
    identity = _validate_runtime_identity(runtime_identity)
    runtime = _validate_resolved_runtime(resolved_runtime)
    evidence = _validate_config_evidence(derived_config, config_evidence)
    source_runtime = _validate_source_runtime_declarations(derived_config)

    staged = _read_staged_config()
    if staged != derived_config:
        raise KosovoResidentialOQ313RunError(
            "staged derived config byte identity does not match the verified recipe"
        )

    env = os.environ.copy()
    env["OPENBLAS_NUM_THREADS"] = OPENBLAS_NUM_THREADS
    env["OQ_DISTRIBUTE"] = OQ_DISTRIBUTE
    env["PYTHONPATH"] = OPENQUAKE_SOURCE_OVERLAY

    returncode = _execute_native(COMMAND, env)
    if not isinstance(returncode, int) or isinstance(returncode, bool):
        raise KosovoResidentialOQ313RunError(
            "OpenQuake runner returned a non-integer exit code"
        )
    native_failure_diagnostic = getattr(returncode, "diagnostic", None)
    exit_code = int(returncode)

    status = "pass" if exit_code == 0 else "blocked"
    document = {
        "schema_version": SCHEMA_VERSION,
        "issues": {
            "control": CONTROL_ISSUE,
            "parent_consumer": PARENT_CONSUMER_ISSUE,
        },
        "experiment_label": EXPERIMENT_LABEL,
        "scope": SCOPE,
        "openquake": {
            "repository": OPENQUAKE_REPOSITORY,
            "version": OPENQUAKE_VERSION,
            "source_version": OPENQUAKE_SOURCE_VERSION,
            "commit_sha": OPENQUAKE_COMMIT_SHA,
        },
        "config": {
            "logical_path": CONFIG_LOGICAL_PATH,
            "byte_count": len(derived_config),
            "sha256": evidence["output"]["sha256"],
            "staged_byte_identity_verified": True,
        },
        "loss_semantics": {
            "loss_stage": LOSS_STAGE,
            "loss_type": LOSS_TYPE,
            "quantity": QUANTITY,
            "unit": UNIT,
            "minimum_asset_loss_structural": MINIMUM_ASSET_LOSS_STRUCTURAL,
            "threshold_predicate": THRESHOLD_PREDICATE,
            "threshold_source": "exact_group1_provider_config",
            "threshold_is_deductible": False,
        },
        "source_runtime": source_runtime,
        "resolved_runtime": {
            "calculation_mode": runtime["calculation_mode"],
            "random_seed": runtime["random_seed"],
            "random_seed_provenance": runtime["random_seed_provenance"],
            "ignore_master_seed": runtime["ignore_master_seed"],
            "ignore_master_seed_provenance": runtime[
                "ignore_master_seed_provenance"
            ],
            "ses_seed": runtime["ses_seed"],
            "ses_seed_provenance": runtime["ses_seed_provenance"],
            "minimum_asset_loss_structural": runtime[
                "minimum_asset_loss_structural"
            ],
            "minimum_asset_loss_provenance": runtime[
                "minimum_asset_loss_provenance"
            ],
            "concurrent_tasks": runtime["concurrent_tasks"],
        },
        "execution": {
            "command": list(COMMAND),
            "exit_code": exit_code,
            "openblas_num_threads": OPENBLAS_NUM_THREADS,
            "oq_distribute": OQ_DISTRIBUTE,
            "pythonpath": OPENQUAKE_SOURCE_OVERLAY,
            "bootstrap_image_digest": identity["bootstrap_image_digest"],
            "execution_image_id": identity["execution_image_id"],
            "python_major_minor": identity["python_major_minor"],
            "dependency_versions": dict(identity["dependency_versions"]),
            "runtime_source_commit_verified": identity["source_commit_verified"],
            "preprocess_openblas_injected": True,
            "preprocess_oq_distribute_injected": True,
            "source_overlay_injected": True,
            "distribution_state_receipted": True,
            "numerical_execution_attempted": True,
        },
        "status": status,
        "failure_stage": None if status == "pass" else "openquake_run",
        "failure_code": None if status == "pass" else "openquake_run_failed",
        "external_provider_bytes_persisted": False,
        "risk_by_event_receipt_emitted": False,
        "historical_environment_verified": False,
        "reference_base_image_byte_identity_verified": False,
        "wheel_byte_identity_verified": False,
        "historical_group_assignment_verified": False,
        "vulnerability_horizontal_component_verified": False,
        "horizontal_component_conversion_authorized": False,
        "project186_value_structural_equivalence_verified": False,
        "numerical_reference_loss_verified": False,
        "independent_validation_established": False,
        "publication_authorized": False,
        "model_use_authorized": False,
    }
    if status == "blocked" and native_failure_diagnostic is not None:
        if type(native_failure_diagnostic) is not dict or set(native_failure_diagnostic) != {
            "byte_count",
            "sha256",
            "content_exposed",
        }:
            raise KosovoResidentialOQ313RunError(
                "native failure diagnostic fields drifted"
            )
        byte_count = native_failure_diagnostic["byte_count"]
        digest = native_failure_diagnostic["sha256"]
        exposed = native_failure_diagnostic["content_exposed"]
        if type(byte_count) is not int or byte_count < 0:
            raise KosovoResidentialOQ313RunError(
                "native failure diagnostic byte count drifted"
            )
        if type(digest) is not str or re.fullmatch(r"[0-9a-f]{64}", digest) is None:
            raise KosovoResidentialOQ313RunError(
                "native failure diagnostic digest drifted"
            )
        if exposed is not False:
            raise KosovoResidentialOQ313RunError(
                "native failure diagnostic content boundary drifted"
            )
        document["native_failure_diagnostic"] = dict(native_failure_diagnostic)
    return _canonical_payload(document)


def run_kosovo_residential_ebrisk_openquake313(
    source_group1_config: bytes,
    *,
    runtime_identity: object,
    resolved_runtime: object,
) -> tuple[bytes, dict[str, Any]]:
    """Execute the fixed OQ3.13 ebrisk command after all bounded gates pass."""

    _require_authority()
    derived_config, evidence = config_builder.build_kosovo_residential_ebrisk_config(
        source_group1_config
    )
    return _run_derived_config(
        derived_config,
        evidence,
        runtime_identity=runtime_identity,
        resolved_runtime=resolved_runtime,
    )
