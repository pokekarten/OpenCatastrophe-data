# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Fail-closed offline content-contract validation for one EQ1 Kosovo OQ3.13 terminal.

The trusted action already validates the runtime and numerical receipt before publishing.
This module gives an external consumer a network-free second boundary over a *supplied*
result-comment body: exact outer fields, adapter self-consistency, authority ceilings and
(when present) the canonical risk_by_event receipt are revalidated.

This content-only boundary does **not** authenticate the GitHub comment actor/origin and
does not independently establish the nested adapter's provenance. A consumer must obtain
the body from the canonical public #609 ``github-actions[bot]`` terminal, or establish an
equivalently trusted acquisition channel, before treating declared terminal identities as
provenance evidence.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts import run_esrm20_kosovo_residential_ebrisk_openquake313_action as action

_SHA_RE = re.compile(r"^[0-9a-f]{40}$")
_BASE_FIELDS = {
    "schema_version",
    "action",
    "source_issue",
    "parent_consumer_issue",
    "dataset_id",
    "execution_sha",
    "status",
    "adapter_receipt",
    "adapter_result",
    "external_provider_bytes_persisted",
    "historical_reproduction_verified",
    "scientific_validity_verified",
    "publication_authorized",
    "model_use_authorized",
    "oq_datastore_persisted",
    "numerical_receipt_emitted",
}
_NUMERICAL_FAILURE_FIELDS = {
    "numerical_receipt_failure_stage",
    "numerical_receipt_failure_code",
}
_NUMERICAL_SUCCESS_FIELDS = _NUMERICAL_FAILURE_FIELDS | {
    "numerical_receipt_identity",
    "numerical_receipt",
}
_NUMERICAL_FAILURE_CODES = {
    "calculation_datastore_discovery_failed",
    "calculation_datastore_cardinality_invalid",
    "calculation_datastore_path_invalid",
    "risk_by_event_selection_failed",
    "numerical_receipt_publication_budget_exceeded",
    "numerical_receipt_validation_failed",
}
_OUTER_FALSE_FIELDS = (
    "external_provider_bytes_persisted",
    "historical_reproduction_verified",
    "scientific_validity_verified",
    "publication_authorized",
    "model_use_authorized",
    "oq_datastore_persisted",
)
_VALIDATION_SCOPE = "terminal_body_contract_only"
_ORIGIN_PRECONDITION = (
    "canonical_public_issue_609_github_actions_bot_or_separately_trusted_channel"
)


class EQ1OQ313TerminalValidationError(ValueError):
    """The supplied OQ3.13 terminal body is not the exact closed content contract."""


def _canonical_json_bytes(document: object) -> bytes:
    return (
        json.dumps(
            document,
            ensure_ascii=True,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")
        + b"\n"
    )


def _parse_terminal_body(body: object) -> dict[str, Any]:
    if type(body) is not str or body.count(action.RESULT_MARKER) != 1:
        raise EQ1OQ313TerminalValidationError("invalid result marker")
    before, after = body.split(action.RESULT_MARKER, 1)
    if before.strip() or not after.strip():
        raise EQ1OQ313TerminalValidationError("result envelope is not canonical")
    try:
        document = action._load_json_text(after.strip(), label="public result")
    except action.KosovoResidentialOQ313ActionError as exc:
        raise EQ1OQ313TerminalValidationError("invalid public result JSON") from exc
    if type(document) is not dict:
        raise EQ1OQ313TerminalValidationError("public result must be an object")
    return document


def _validate_adapter_self_consistency(result: dict[str, Any]) -> dict[str, Any]:
    """Apply the current action contract and verify the adjacent adapter receipt.

    The receipt is intentionally treated as a self-consistency check over the supplied
    adapter object, not as an independent trust anchor for its nested provenance.
    """

    adapter = result.get("adapter_result")
    try:
        validated = action._validate_adapter_document(adapter)
    except action.KosovoResidentialOQ313ActionError as exc:
        raise EQ1OQ313TerminalValidationError("adapter result contract drifted") from exc

    execution = validated.get("execution")
    if type(execution) is not dict or type(execution.get("exit_code")) is not int:
        raise EQ1OQ313TerminalValidationError("adapter execution exit code type drifted")

    receipt = result.get("adapter_receipt")
    if type(receipt) is not dict or set(receipt) != {"byte_count", "sha256"}:
        raise EQ1OQ313TerminalValidationError("adapter receipt fields drifted")
    payload = _canonical_json_bytes(validated)
    byte_count = receipt.get("byte_count")
    if type(byte_count) is not int or byte_count != len(payload):
        raise EQ1OQ313TerminalValidationError("adapter receipt byte count drifted")
    digest = receipt.get("sha256")
    if type(digest) is not str or digest != hashlib.sha256(payload).hexdigest():
        raise EQ1OQ313TerminalValidationError("adapter receipt digest drifted")
    return validated


def _bounded_summary(
    *,
    expected_execution_sha: str,
    terminal_status: str,
    numerical_receipt_emitted: bool,
    numerical_receipt_identity: dict[str, Any] | None = None,
    row_count: int | None = None,
) -> dict[str, Any]:
    """Return a machine-readable summary that cannot promote content validation."""

    summary: dict[str, Any] = {
        "validation_scope": _VALIDATION_SCOPE,
        "body_contract_validated": True,
        "trusted_origin_required": True,
        "github_comment_origin_authenticated": False,
        "origin_precondition": _ORIGIN_PRECONDITION,
        "adapter_provenance_independently_verified": False,
        "declared_execution_sha": expected_execution_sha,
        "declared_terminal_status": terminal_status,
        "numerical_receipt_emitted": numerical_receipt_emitted,
        "external_provider_bytes_persisted": False,
        "historical_reproduction_verified": False,
        "numerical_reference_loss_verified": False,
        "independent_validation_established": False,
        "scientific_validity_verified": False,
        "publication_authorized": False,
        "model_use_authorized": False,
        "oq_datastore_persisted": False,
    }
    if numerical_receipt_identity is not None:
        summary["numerical_receipt_identity"] = numerical_receipt_identity
    if row_count is not None:
        summary["row_count"] = row_count
    return summary


def validate_terminal_body(
    body: object,
    *,
    expected_execution_sha: str,
) -> dict[str, Any]:
    """Validate one supplied result body and return a bounded content-only summary."""

    if type(expected_execution_sha) is not str or _SHA_RE.fullmatch(expected_execution_sha) is None:
        raise EQ1OQ313TerminalValidationError("invalid expected execution SHA")
    result = _parse_terminal_body(body)

    exact = (
        ("schema_version", action.RESULT_SCHEMA_VERSION),
        ("action", action.ACTION),
        ("source_issue", action.CONTROL_ISSUE),
        ("parent_consumer_issue", action.PARENT_CONSUMER_ISSUE),
        ("dataset_id", action.DATASET_ID),
        ("execution_sha", expected_execution_sha),
    )
    for field, expected in exact:
        observed = result.get(field)
        if type(observed) is not type(expected) or observed != expected:
            raise EQ1OQ313TerminalValidationError(f"result {field} drifted")
    for field in _OUTER_FALSE_FIELDS:
        if result.get(field) is not False:
            raise EQ1OQ313TerminalValidationError(f"result authority boundary {field} drifted")

    adapter = _validate_adapter_self_consistency(result)
    emitted = result.get("numerical_receipt_emitted")
    if type(emitted) is not bool:
        raise EQ1OQ313TerminalValidationError("numerical receipt emitted flag drifted")

    if adapter["status"] == "blocked":
        if set(result) != _BASE_FIELDS or result.get("status") != "blocked" or emitted:
            raise EQ1OQ313TerminalValidationError("blocked adapter terminal shape drifted")
        return _bounded_summary(
            expected_execution_sha=expected_execution_sha,
            terminal_status="blocked",
            numerical_receipt_emitted=False,
        )

    if emitted:
        if set(result) != (_BASE_FIELDS | _NUMERICAL_SUCCESS_FIELDS):
            raise EQ1OQ313TerminalValidationError("PASS terminal fields drifted")
        if result.get("status") != "pass":
            raise EQ1OQ313TerminalValidationError("numerical receipt terminal status drifted")
        if result.get("numerical_receipt_failure_stage") is not None:
            raise EQ1OQ313TerminalValidationError("PASS numerical failure stage drifted")
        if result.get("numerical_receipt_failure_code") is not None:
            raise EQ1OQ313TerminalValidationError("PASS numerical failure code drifted")

        numerical = result.get("numerical_receipt")
        identity = result.get("numerical_receipt_identity")
        payload = _canonical_json_bytes(numerical)
        try:
            _, validated_identity = action._validate_numerical_receipt(
                payload,
                identity,
                expected_concurrent_tasks=action._adapter_concurrent_tasks(result),
            )
        except action.KosovoResidentialOQ313ActionError as exc:
            raise EQ1OQ313TerminalValidationError("numerical receipt contract drifted") from exc
        return _bounded_summary(
            expected_execution_sha=expected_execution_sha,
            terminal_status="pass",
            numerical_receipt_emitted=True,
            numerical_receipt_identity=validated_identity,
            row_count=len(numerical["rows"]),
        )

    if set(result) != (_BASE_FIELDS | _NUMERICAL_FAILURE_FIELDS):
        raise EQ1OQ313TerminalValidationError("numerical BLOCKED terminal fields drifted")
    if result.get("status") != "blocked":
        raise EQ1OQ313TerminalValidationError("numerical BLOCKED status drifted")
    if result.get("numerical_receipt_failure_stage") != "risk_by_event_receipt":
        raise EQ1OQ313TerminalValidationError("numerical failure stage drifted")
    if result.get("numerical_receipt_failure_code") not in _NUMERICAL_FAILURE_CODES:
        raise EQ1OQ313TerminalValidationError("numerical failure code drifted")
    return _bounded_summary(
        expected_execution_sha=expected_execution_sha,
        terminal_status="blocked",
        numerical_receipt_emitted=False,
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--expected-execution-sha", required=True)
    parser.add_argument("--input", type=Path)
    args = parser.parse_args(argv)

    try:
        body = (
            args.input.read_text(encoding="utf-8")
            if args.input is not None
            else sys.stdin.read()
        )
        summary = validate_terminal_body(
            body,
            expected_execution_sha=args.expected_execution_sha,
        )
    except (OSError, UnicodeError, EQ1OQ313TerminalValidationError) as exc:
        raise SystemExit(str(exc)) from exc
    sys.stdout.write(json.dumps(summary, sort_keys=True, separators=(",", ":")) + "\n")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
