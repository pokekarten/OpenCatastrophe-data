# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Closed request/result envelope for the fixed Kosovo OQ3.13 ebrisk runner.

This module does not acquire provider inputs or construct a runtime. A trusted-main
workflow must stage the already-authorized exact Group1 config and runtime receipts,
then invoke this envelope. The request cannot select provider identity, input paths,
runtime identity, command, thresholds, or scientific semantics.

On a successful native run, the action additionally isolates the OpenQuake datastore
inside a fresh temporary ``OQ_DATADIR`` and projects the one completed calculation
through the already-reviewed datastore selector and numerical receipt projector.
The datastore itself remains ephemeral; only the deterministic receipt is surfaced.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import tempfile
from pathlib import Path
from typing import Any, Callable

try:
    from scripts import run_esrm20_kosovo_residential_ebrisk_openquake313 as runner
    from scripts import select_oq313_risk_by_event_rows as datastore_selector
    from scripts import project_oq313_risk_by_event_receipt as numerical_contract
except ModuleNotFoundError:  # pragma: no cover - direct script execution path
    import run_esrm20_kosovo_residential_ebrisk_openquake313 as runner
    import select_oq313_risk_by_event_rows as datastore_selector
    import project_oq313_risk_by_event_receipt as numerical_contract

REQUEST_MARKER = "<!-- oc-eq1-esrm20-kosovo-oq313-run-request-v1 -->"
RESULT_MARKER = "<!-- oc-eq1-esrm20-kosovo-oq313-run-result-v1 -->"
REQUEST_SCHEMA_VERSION = "oc-esrm20-kosovo-oq313-run-request-v1"
RESULT_SCHEMA_VERSION = "oc-esrm20-kosovo-oq313-run-result-v1"
ACTION = "esrm20_kosovo_residential_oq313_run"
CONTROL_ISSUE = 609
PARENT_CONSUMER_ISSUE = 287
DATASET_ID = "efehr.esrm20.risk-inputs.v1.0"
OQ_DATADIR_ENV = "OQ_DATADIR"
MAX_PUBLIC_NUMERICAL_RECEIPT_BYTES = 32_768

_SHA_RE = re.compile(r"^[0-9a-f]{40}$")
_DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
_REQUESTER_RE = re.compile(r"^[A-Za-z0-9_.:@/+ -]{1,96}$")
_CALC_DATASTORE_RE = re.compile(r"^calc_[0-9]+\.hdf5$")
_REQUEST_FIELDS = {
    "schema_version",
    "action",
    "issue",
    "target_sha",
    "dataset_id",
    "requester",
}
_NUMERICAL_RECEIPT_FIELDS = {
    "experiment_label",
    "insurance_scope",
    "openquake",
    "quantity",
    "rows",
    "runtime",
    "schema_version",
    "selection",
    "source_dataset",
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
    if digest != hashlib.sha256(adapter_payload).hexdigest():
        raise KosovoResidentialOQ313ActionError("adapter receipt digest drifted")

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


def _project_exact_datastore(path: Path) -> tuple[bytes, dict[str, Any]]:
    if path.is_symlink() or not path.is_file():
        raise KosovoResidentialOQ313ActionError(
            "OpenQuake calculation datastore must be one regular file"
        )
    try:
        from openquake.commonlib import datastore as oq_datastore
    except ImportError as exc:  # pragma: no cover - only available in runtime image
        raise KosovoResidentialOQ313ActionError(
            "OpenQuake datastore runtime is unavailable"
        ) from exc

    dstore = None
    primary_error_active = False
    try:
        dstore = oq_datastore.read(str(path), mode="r")
        oq = dstore["oqparam"]
        return datastore_selector.select_oq313_risk_by_event_receipt(dstore, oq)
    except datastore_selector.OQ313DatastoreSelectionError as exc:
        primary_error_active = True
        raise KosovoResidentialOQ313ActionError(
            "completed OpenQuake datastore failed numerical receipt selection"
        ) from exc
    except (KeyError, OSError, TypeError, ValueError) as exc:
        primary_error_active = True
        raise KosovoResidentialOQ313ActionError(
            "cannot consume completed OpenQuake datastore"
        ) from exc
    finally:
        if dstore is not None:
            try:
                dstore.close()
            except (OSError, RuntimeError, ValueError) as exc:
                if not primary_error_active:
                    raise KosovoResidentialOQ313ActionError(
                        "cannot close completed OpenQuake datastore"
                    ) from exc


def _adapter_concurrent_tasks(result: object) -> int:
    if type(result) is not dict:
        raise KosovoResidentialOQ313ActionError("canonical result must be an object")
    adapter = result.get("adapter_result")
    if type(adapter) is not dict:
        raise KosovoResidentialOQ313ActionError("adapter result is missing")
    resolved = adapter.get("resolved_runtime")
    if type(resolved) is not dict:
        raise KosovoResidentialOQ313ActionError("adapter resolved runtime is missing")
    tasks = resolved.get("concurrent_tasks")
    if type(tasks) is not int or tasks < 0:
        raise KosovoResidentialOQ313ActionError(
            "adapter resolved runtime concurrent_tasks drifted"
        )
    return tasks


def _validate_numerical_receipt(
    payload: object,
    receipt: object,
    *,
    expected_concurrent_tasks: int,
) -> tuple[dict[str, Any], dict[str, Any]]:
    if type(payload) is not bytes or not payload:
        raise KosovoResidentialOQ313ActionError(
            "numerical receipt payload must be non-empty bytes"
        )
    if type(receipt) is not dict or set(receipt) != {"byte_count", "sha256"}:
        raise KosovoResidentialOQ313ActionError(
            "numerical receipt identity fields drifted"
        )
    byte_count = receipt.get("byte_count")
    digest = receipt.get("sha256")
    if type(byte_count) is not int or byte_count != len(payload):
        raise KosovoResidentialOQ313ActionError(
            "numerical receipt byte count drifted"
        )
    if type(digest) is not str or _DIGEST_RE.fullmatch(digest) is None:
        raise KosovoResidentialOQ313ActionError(
            "numerical receipt digest is invalid"
        )
    if digest != hashlib.sha256(payload).hexdigest():
        raise KosovoResidentialOQ313ActionError(
            "numerical receipt digest drifted"
        )
    try:
        text = payload.decode("utf-8", errors="strict")
    except UnicodeDecodeError as exc:
        raise KosovoResidentialOQ313ActionError(
            "numerical receipt payload is not UTF-8"
        ) from exc
    document = _load_json_text(text, label="numerical receipt")
    if type(document) is not dict or set(document) != _NUMERICAL_RECEIPT_FIELDS:
        raise KosovoResidentialOQ313ActionError(
            "numerical receipt top-level fields drifted"
        )

    exact = (
        ("schema_version", numerical_contract.SCHEMA_VERSION),
        ("experiment_label", numerical_contract.EXPERIMENT_LABEL),
        ("source_dataset", numerical_contract.SOURCE_DATASET),
        ("insurance_scope", "none"),
    )
    for field, expected in exact:
        observed = document.get(field)
        if type(observed) is not type(expected) or observed != expected:
            raise KosovoResidentialOQ313ActionError(
                f"numerical receipt {field} drifted"
            )

    openquake = document.get("openquake")
    quantity = document.get("quantity")
    runtime = document.get("runtime")
    selection = document.get("selection")
    rows = document.get("rows")
    if type(openquake) is not dict or set(openquake) != {"commit_sha", "version"}:
        raise KosovoResidentialOQ313ActionError(
            "numerical receipt OpenQuake fields drifted"
        )
    if type(quantity) is not dict or set(quantity) != {
        "loss_type",
        "minimum_asset_loss_structural",
        "name",
        "threshold_predicate",
        "unit",
    }:
        raise KosovoResidentialOQ313ActionError(
            "numerical receipt quantity fields drifted"
        )
    if type(runtime) is not dict or set(runtime) != {"concurrent_tasks"}:
        raise KosovoResidentialOQ313ActionError(
            "numerical receipt runtime fields drifted"
        )
    if type(selection) is not dict or set(selection) != {
        "portfolio_agg_id",
        "structural_loss_id",
    }:
        raise KosovoResidentialOQ313ActionError(
            "numerical receipt selection fields drifted"
        )
    if type(rows) is not list or not rows:
        raise KosovoResidentialOQ313ActionError(
            "numerical receipt rows must be a non-empty list"
        )

    if openquake["version"] != runner.OPENQUAKE_VERSION:
        raise KosovoResidentialOQ313ActionError(
            "numerical receipt OpenQuake version drifted"
        )
    if openquake["commit_sha"] != runner.OPENQUAKE_COMMIT_SHA:
        raise KosovoResidentialOQ313ActionError(
            "numerical receipt OpenQuake commit drifted"
        )
    if runtime["concurrent_tasks"] != expected_concurrent_tasks:
        raise KosovoResidentialOQ313ActionError(
            "numerical receipt concurrent_tasks drifted from adapter runtime"
        )

    try:
        regenerated_payload, regenerated_identity = (
            numerical_contract.project_oq313_risk_by_event_receipt(
                rows,
                portfolio_agg_id=selection["portfolio_agg_id"],
                structural_loss_id=selection["structural_loss_id"],
                concurrent_tasks=runtime["concurrent_tasks"],
                loss_type=quantity["loss_type"],
                unit=quantity["unit"],
                minimum_asset_loss_structural=quantity[
                    "minimum_asset_loss_structural"
                ],
                experiment_label=document["experiment_label"],
                policy_present=False,
                insured_loss_present=False,
            )
        )
    except numerical_contract.OQ313RiskByEventReceiptError as exc:
        raise KosovoResidentialOQ313ActionError(
            "numerical receipt violates the reviewed projector contract"
        ) from exc
    if regenerated_payload != payload or regenerated_identity != receipt:
        raise KosovoResidentialOQ313ActionError(
            "numerical receipt canonical projector contract drifted"
        )
    return document, dict(receipt)


def _block_numerical_receipt(
    result: dict[str, Any],
    *,
    code: str,
) -> dict[str, Any]:
    result["status"] = "blocked"
    result["numerical_receipt_emitted"] = False
    result["numerical_receipt_failure_stage"] = "risk_by_event_receipt"
    result["numerical_receipt_failure_code"] = code
    return result


def run_action_with_numerical_receipt(
    *,
    execution_sha: str,
    source_group1_config: bytes,
    runtime_identity: object,
    resolved_runtime: object,
    execute: Callable[..., tuple[bytes, dict[str, Any]]] = runner.run_kosovo_residential_ebrisk_openquake313,
    project_datastore: Callable[[Path], tuple[bytes, dict[str, Any]]] = _project_exact_datastore,
) -> dict[str, Any]:
    """Run the closed action and consume exactly one ephemeral completed datastore."""

    previous_datadir = os.environ.get(OQ_DATADIR_ENV)
    with tempfile.TemporaryDirectory(prefix="oc-oq313-") as temporary_datadir:
        datadir = Path(temporary_datadir)
        if any(datadir.iterdir()):
            raise KosovoResidentialOQ313ActionError(
                "isolated OpenQuake datadir must start empty"
            )
        os.environ[OQ_DATADIR_ENV] = str(datadir)
        try:
            result = run_action(
                execution_sha=execution_sha,
                source_group1_config=source_group1_config,
                runtime_identity=runtime_identity,
                resolved_runtime=resolved_runtime,
                execute=execute,
            )
        finally:
            if previous_datadir is None:
                os.environ.pop(OQ_DATADIR_ENV, None)
            else:
                os.environ[OQ_DATADIR_ENV] = previous_datadir

        result["oq_datastore_persisted"] = False
        if result["status"] != "pass":
            result["numerical_receipt_emitted"] = False
            return result

        try:
            calc_paths = sorted(
                path
                for path in datadir.iterdir()
                if _CALC_DATASTORE_RE.fullmatch(path.name) is not None
            )
        except OSError:
            return _block_numerical_receipt(
                result,
                code="calculation_datastore_discovery_failed",
            )
        if len(calc_paths) != 1:
            return _block_numerical_receipt(
                result,
                code="calculation_datastore_cardinality_invalid",
            )
        calc_path = calc_paths[0]
        if calc_path.is_symlink() or not calc_path.is_file():
            return _block_numerical_receipt(
                result,
                code="calculation_datastore_path_invalid",
            )

        try:
            numerical_payload, numerical_identity = project_datastore(calc_path)
        except KosovoResidentialOQ313ActionError:
            return _block_numerical_receipt(
                result,
                code="risk_by_event_selection_failed",
            )
        if len(numerical_payload) > MAX_PUBLIC_NUMERICAL_RECEIPT_BYTES:
            return _block_numerical_receipt(
                result,
                code="numerical_receipt_publication_budget_exceeded",
            )
        try:
            numerical_document, numerical_identity = _validate_numerical_receipt(
                numerical_payload,
                numerical_identity,
                expected_concurrent_tasks=_adapter_concurrent_tasks(result),
            )
        except KosovoResidentialOQ313ActionError:
            return _block_numerical_receipt(
                result,
                code="numerical_receipt_validation_failed",
            )
        result["numerical_receipt_emitted"] = True
        result["numerical_receipt_failure_stage"] = None
        result["numerical_receipt_failure_code"] = None
        result["numerical_receipt_identity"] = numerical_identity
        result["numerical_receipt"] = numerical_document
        return result


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

    result = run_action_with_numerical_receipt(
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