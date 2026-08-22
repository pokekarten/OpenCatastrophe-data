# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Closed request/result envelope for the fixed Kosovo OQ3.13 ebrisk runner.

This module does not acquire provider inputs or construct a runtime. A future
trusted-main workflow must stage the already-authorized exact Group1 config and
runtime receipts, then invoke this envelope. The request cannot select provider
identity, input paths, runtime identity, command, thresholds, or scientific
semantics.
"""

from __future__ import annotations

import argparse
import json
import os
import re
from pathlib import Path
from typing import Any, Callable

try:
    from scripts import run_esrm20_kosovo_residential_ebrisk_openquake313 as runner
except ModuleNotFoundError:  # pragma: no cover - direct script execution path
    import run_esrm20_kosovo_residential_ebrisk_openquake313 as runner

REQUEST_MARKER = "<!-- oc-eq1-esrm20-kosovo-oq313-run-request-v1 -->"
RESULT_MARKER = "<!-- oc-eq1-esrm20-kosovo-oq313-run-result-v1 -->"
REQUEST_SCHEMA_VERSION = "oc-esrm20-kosovo-oq313-run-request-v1"
RESULT_SCHEMA_VERSION = "oc-esrm20-kosovo-oq313-run-result-v1"
ACTION = "esrm20_kosovo_residential_oq313_run"
CONTROL_ISSUE = 609
PARENT_CONSUMER_ISSUE = 287
DATASET_ID = "efehr.esrm20.risk-inputs.v1.0"

_SHA_RE = re.compile(r"^[0-9a-f]{40}$")
_DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
_REQUESTER_RE = re.compile(r"^[A-Za-z0-9_.:@/+ -]{1,96}$")
_REQUEST_FIELDS = {
    "schema_version",
    "action",
    "issue",
    "target_sha",
    "dataset_id",
    "requester",
}

_AUTHORITY_FALSE_FIELDS = (
    "historical_environment_verified",
    "reference_base_image_byte_identity_verified",
    "wheel_byte_identity_verified",
    "historical_group_assignment_verified",
    "vulnerability_horizontal_component_verified",
    "horizontal_component_conversion_authorized",
    "project186_value_structural_equivalence_verified",
    "numerical_reference_loss_verified",
    "independent_validation_established",
    "publication_authorized",
    "model_use_authorized",
)


class KosovoResidentialOQ313ActionError(RuntimeError):
    """The closed trusted execution envelope was violated."""


def _pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise KosovoResidentialOQ313ActionError("duplicate JSON key")
        result[key] = value
    return result


def _reject_constant(value: str) -> Any:
    raise KosovoResidentialOQ313ActionError(f"non-finite JSON constant: {value}")


def _load_json_text(text: str, *, label: str) -> object:
    try:
        return json.loads(
            text,
            object_pairs_hook=_pairs,
            parse_constant=_reject_constant,
        )
    except KosovoResidentialOQ313ActionError:
        raise
    except (json.JSONDecodeError, TypeError, ValueError) as exc:
        raise KosovoResidentialOQ313ActionError(f"invalid {label} JSON") from exc


def validate_request(
    body: object,
    *,
    expected_issue: int,
    execution_sha: str,
) -> dict[str, Any]:
    if type(expected_issue) is not int or expected_issue != CONTROL_ISSUE:
        raise KosovoResidentialOQ313ActionError("wrong runtime issue")
    if type(execution_sha) is not str or _SHA_RE.fullmatch(execution_sha) is None:
        raise KosovoResidentialOQ313ActionError("invalid execution SHA")
    if type(body) is not str or body.count(REQUEST_MARKER) != 1:
        raise KosovoResidentialOQ313ActionError("invalid request marker")

    before, after = body.split(REQUEST_MARKER, 1)
    if before.strip() or not after.strip():
        raise KosovoResidentialOQ313ActionError("request envelope is not canonical")
    request = _load_json_text(after.strip(), label="request")
    if type(request) is not dict or set(request) != _REQUEST_FIELDS:
        raise KosovoResidentialOQ313ActionError("request fields drifted")

    exact = (
        ("schema_version", REQUEST_SCHEMA_VERSION),
        ("action", ACTION),
        ("issue", CONTROL_ISSUE),
        ("target_sha", execution_sha),
        ("dataset_id", DATASET_ID),
    )
    for field, expected in exact:
        observed = request.get(field)
        if type(observed) is not type(expected) or observed != expected:
            raise KosovoResidentialOQ313ActionError(f"request {field} drifted")

    requester = request["requester"]
    if (
        type(requester) is not str
        or requester != requester.strip()
        or _REQUESTER_RE.fullmatch(requester) is None
    ):
        raise KosovoResidentialOQ313ActionError("invalid requester identity")
    return request


def _read_bytes(path: Path, *, label: str) -> bytes:
    try:
        payload = path.read_bytes()
    except OSError as exc:
        raise KosovoResidentialOQ313ActionError(f"cannot read {label}") from exc
    if not payload:
        raise KosovoResidentialOQ313ActionError(f"{label} must be non-empty")
    return payload


def _read_json(path: Path, *, label: str) -> object:
    payload = _read_bytes(path, label=label)
    try:
        text = payload.decode("utf-8", errors="strict")
    except UnicodeDecodeError as exc:
        raise KosovoResidentialOQ313ActionError(f"{label} must be UTF-8") from exc
    return _load_json_text(text, label=label)


def _validate_adapter_document(document: object) -> dict[str, Any]:
    if type(document) is not dict:
        raise KosovoResidentialOQ313ActionError("adapter result must be an object")
    exact = (
        ("schema_version", runner.SCHEMA_VERSION),
        ("experiment_label", runner.EXPERIMENT_LABEL),
        ("scope", runner.SCOPE),
        ("external_provider_bytes_persisted", False),
        ("risk_by_event_receipt_emitted", False),
    )
    for field, expected in exact:
        observed = document.get(field)
        if type(observed) is not type(expected) or observed != expected:
            raise KosovoResidentialOQ313ActionError(
                f"adapter result {field} drifted"
            )

    status = document.get("status")
    if status not in {"pass", "blocked"}:
        raise KosovoResidentialOQ313ActionError("adapter status is not terminal")
    execution = document.get("execution")
    if type(execution) is not dict or execution.get("command") != list(runner.COMMAND):
        raise KosovoResidentialOQ313ActionError("adapter command drifted")
    if execution.get("numerical_execution_attempted") is not True:
        raise KosovoResidentialOQ313ActionError("adapter execution flag drifted")

    if status == "pass":
        if document.get("failure_stage") is not None or document.get("failure_code") is not None:
            raise KosovoResidentialOQ313ActionError("PASS has failure metadata")
        if execution.get("exit_code") != 0:
            raise KosovoResidentialOQ313ActionError("PASS has non-zero exit code")
    else:
        if document.get("failure_stage") != "openquake_run":
            raise KosovoResidentialOQ313ActionError("BLOCKED failure stage drifted")
        if document.get("failure_code") != "openquake_run_failed":
            raise KosovoResidentialOQ313ActionError("BLOCKED failure code drifted")
        exit_code = execution.get("exit_code")
        if type(exit_code) is not int or exit_code == 0:
            raise KosovoResidentialOQ313ActionError("BLOCKED exit code drifted")

    for field in _AUTHORITY_FALSE_FIELDS:
        if document.get(field) is not False:
            raise KosovoResidentialOQ313ActionError(
                f"adapter authority boundary {field} drifted"
            )
    return document


def _canonical_result(
    *,
    execution_sha: str,
    adapter_payload: bytes,
    adapter_receipt: dict[str, Any],
) -> dict[str, Any]:
    try:
        adapter_text = adapter_payload.decode("utf-8", errors="strict")
    except UnicodeDecodeError as exc:
        raise KosovoResidentialOQ313ActionError("adapter payload is not UTF-8") from exc
    adapter_document = _load_json_text(adapter_text, label="adapter result")
    validated = _validate_adapter_document(adapter_document)

    if type(adapter_receipt) is not dict or set(adapter_receipt) != {
        "byte_count",
        "sha256",
    }:
        raise KosovoResidentialOQ313ActionError("adapter receipt fields drifted")
    if adapter_receipt.get("byte_count") != len(adapter_payload):
        raise KosovoResidentialOQ313ActionError("adapter receipt byte count drifted")
    digest = adapter_receipt.get("sha256")
    if type(digest) is not str or _DIGEST_RE.fullmatch(digest) is None:
        raise KosovoResidentialOQ313ActionError("adapter receipt digest is invalid")

    return {
        "schema_version": RESULT_SCHEMA_VERSION,
        "action": ACTION,
        "source_issue": CONTROL_ISSUE,
        "parent_consumer_issue": PARENT_CONSUMER_ISSUE,
        "dataset_id": DATASET_ID,
        "execution_sha": execution_sha,
        "status": validated["status"],
        "adapter_receipt": dict(adapter_receipt),
        "adapter_result": validated,
        "external_provider_bytes_persisted": False,
        "historical_reproduction_verified": False,
        "scientific_validity_verified": False,
        "publication_authorized": False,
        "model_use_authorized": False,
    }


def run_action(
    *,
    execution_sha: str,
    source_group1_config: bytes,
    runtime_identity: object,
    resolved_runtime: object,
    execute: Callable[..., tuple[bytes, dict[str, Any]]] = runner.run_kosovo_residential_ebrisk_openquake313,
) -> dict[str, Any]:
    adapter_payload, adapter_receipt = execute(
        source_group1_config,
        runtime_identity=runtime_identity,
        resolved_runtime=resolved_runtime,
    )
    if type(adapter_payload) is not bytes or not adapter_payload:
        raise KosovoResidentialOQ313ActionError("adapter returned invalid payload")
    return _canonical_result(
        execution_sha=execution_sha,
        adapter_payload=adapter_payload,
        adapter_receipt=adapter_receipt,
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--comment-body-env", required=True)
    parser.add_argument("--expected-issue", required=True, type=int)
    parser.add_argument("--execution-sha", required=True)
    parser.add_argument("--validate-request-only", action="store_true")
    parser.add_argument("--source-group1-config", type=Path)
    parser.add_argument("--runtime-identity", type=Path)
    parser.add_argument("--resolved-runtime", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)

    body = os.environ.get(args.comment_body_env)
    validate_request(
        body,
        expected_issue=args.expected_issue,
        execution_sha=args.execution_sha,
    )
    if args.validate_request_only:
        return 0

    required = (
        args.source_group1_config,
        args.runtime_identity,
        args.resolved_runtime,
        args.output,
    )
    if any(value is None for value in required):
        raise KosovoResidentialOQ313ActionError(
            "execution requires all fixed staging arguments"
        )

    result = run_action(
        execution_sha=args.execution_sha,
        source_group1_config=_read_bytes(
            args.source_group1_config,
            label="source Group1 config",
        ),
        runtime_identity=_read_json(args.runtime_identity, label="runtime identity"),
        resolved_runtime=_read_json(args.resolved_runtime, label="resolved runtime"),
    )
    payload = json.dumps(result, sort_keys=True, separators=(",", ":")) + "\n"
    args.output.write_text(payload, encoding="utf-8")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
