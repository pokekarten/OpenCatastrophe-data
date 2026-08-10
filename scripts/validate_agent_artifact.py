# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Strict dependency-free validation for OpenCatastrophe agent task/run artifacts."""
from __future__ import annotations

import argparse
import ipaddress
import json
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any
from urllib.parse import parse_qsl, urlsplit

if __package__:
    from . import validate_manifest as manifest_contract
else:
    import validate_manifest as manifest_contract

ROOT = Path(__file__).resolve().parents[1]
PROFILE_VERSION = "1.0.0"
RUN_PROFILE_V1 = "1.0.0"
RUN_PROFILE_V2 = "2.0.0"
COMMIT_RE = re.compile(r"^[a-f0-9]{40}$")
SHA256_RE = re.compile(r"^[a-f0-9]{64}$")
REPOSITORY_RE = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")
ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$")
WINDOWS_ABS_RE = re.compile(r"^[A-Za-z]:[\\/]")
TASK_STATES = {"ready", "blocked", "active", "validation_only", "research_only", "complete"}
DATA_POLICIES = {"none", "synthetic_only", "metadata_only", "admitted_public_only", "restricted_external_only"}
RUN_STATUSES = {"pass", "fail", "blocked", "not_comparable"}
INTEROP_ROLES = {"import", "export", "compare", "execute", "metadata"}
INTEROP_STATUSES = {"planned", "experimental", "tested", "unsupported", "not_comparable"}
EVIDENCE_CLASSES = {"repository_source", "external_evidence", "inference", "design_proposal"}
LOSS_STAGES = {"ground_up", "gross", "insured", "ceded", "recoverable", "net"}
COMPARISON_MODES = {"deterministic", "common_innovations", "distributional", "not_comparable"}
RUN_INPUT_KINDS_V2 = {"data", "model", "config", "code", "fixture", "literature", "other"}
DATA_ARTIFACT_KINDS_V2 = {"raw", "derived"}
DATA_SCIENTIFIC_ROLES_V2 = {"training", "calibration", "validation", "holdout", "benchmark", "context"}
RUN_ROLE_BY_KIND_V2 = {
    "model": {"model"},
    "config": {"configuration"},
    "code": {"software"},
    "fixture": {"validation", "benchmark", "context", "test_fixture"},
    "literature": {"context"},
    "other": {"context"},
}
CLAIM_REFERENCE_KINDS_V2 = {
    "input", "output", "validation", "manifest", "source_review", "repository_path", "external_uri"
}
CLAIM_SCOPE_KEYS_V2 = {"peril", "geography", "temporal", "variable", "model_context"}
SENSITIVE_QUERY_KEYS = {
    "access_key", "access_token", "api_key", "apikey", "auth", "authorization", "credential", "key",
    "secret", "sig", "signature", "token", "x-amz-credential", "x-amz-signature", "x-goog-credential",
    "x-goog-signature",
}
LOCAL_HOST_SUFFIXES = (".local", ".localhost", ".internal")


class ContractError(ValueError):
    """Raised when a machine-readable agent contract fails closed validation."""


def _reject_constant(value: str) -> None:
    raise ContractError(f"non-finite JSON number is forbidden: {value}")


def _no_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ContractError(f"duplicate JSON key is forbidden: {key}")
        result[key] = value
    return result


def load_strict_json(path: Path) -> Any:
    try:
        return json.loads(
            path.read_text(encoding="utf-8"),
            object_pairs_hook=_no_duplicates,
            parse_constant=_reject_constant,
        )
    except (OSError, UnicodeError, json.JSONDecodeError, ContractError) as exc:
        raise ContractError(f"unable to load strict JSON from {path}: {exc}") from exc


def _obj(value: Any, where: str) -> dict[str, Any]:
    if type(value) is not dict:
        raise ContractError(f"{where} must be an object")
    return value


def _arr(value: Any, where: str) -> list[Any]:
    if type(value) is not list:
        raise ContractError(f"{where} must be an array")
    return value


def _str(value: Any, where: str) -> str:
    if type(value) is not str or not value.strip():
        raise ContractError(f"{where} must be a non-empty string")
    return value


def _bool(value: Any, where: str) -> bool:
    if type(value) is not bool:
        raise ContractError(f"{where} must be a boolean")
    return value


def _int(value: Any, where: str, minimum: int | None = None) -> int:
    if type(value) is not int:
        raise ContractError(f"{where} must be an integer")
    if minimum is not None and value < minimum:
        raise ContractError(f"{where} must be >= {minimum}")
    return value


def _closed(obj: dict[str, Any], where: str, required: set[str], allowed: set[str]) -> None:
    missing = sorted(required - obj.keys())
    extras = sorted(obj.keys() - allowed)
    if missing:
        raise ContractError(f"{where} missing required fields: {', '.join(missing)}")
    if extras:
        raise ContractError(f"{where} has unexpected fields: {', '.join(extras)}")


def _timestamp(value: Any, where: str) -> datetime:
    text = _str(value, where)
    candidate = text[:-1] + "+00:00" if text.endswith("Z") else text
    try:
        parsed = datetime.fromisoformat(candidate)
    except ValueError as exc:
        raise ContractError(f"{where} must be an ISO-8601 timestamp") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ContractError(f"{where} must include an explicit timezone")
    return parsed


def _commit(value: Any, where: str) -> str:
    text = _str(value, where)
    if not COMMIT_RE.fullmatch(text):
        raise ContractError(f"{where} must be a full lowercase 40-character Git commit")
    return text


def _sha256(value: Any, where: str) -> str:
    text = _str(value, where)
    if not SHA256_RE.fullmatch(text):
        raise ContractError(f"{where} must be a lowercase 64-character SHA-256")
    return text


def _path(value: Any, where: str) -> str:
    text = _str(value, where)
    if "\\" in text or text.startswith("/") or WINDOWS_ABS_RE.match(text):
        raise ContractError(f"{where} must be a canonical relative POSIX path")
    if any(part in {"", ".", ".."} for part in text.split("/")) or "\x00" in text:
        raise ContractError(f"{where} contains an unsafe path segment")
    return text


def _repository_file(value: Any, where: str, *, prefix: str | None = None, suffix: str | None = None) -> str:
    text = _path(value, where)
    if prefix is not None and not text.startswith(prefix):
        raise ContractError(f"{where} must reference {prefix}")
    if suffix is not None and not text.endswith(suffix):
        raise ContractError(f"{where} must end with {suffix}")
    path = ROOT / text
    if not path.is_file():
        raise ContractError(f"{where} must resolve to an existing repository file: {text}")
    return text


def _public_external_uri(value: Any, where: str) -> str:
    text = _str(value, where)
    if any(ch.isspace() for ch in text):
        raise ContractError(f"{where} must not contain whitespace")
    if text.startswith("urn:"):
        return text
    try:
        parsed = urlsplit(text)
        hostname = parsed.hostname
        parsed.port
    except ValueError as exc:
        raise ContractError(f"{where} is malformed") from exc
    if parsed.scheme != "https" or not hostname:
        raise ContractError(f"{where} must use public https:// or urn:")
    if parsed.username is not None or parsed.password is not None:
        raise ContractError(f"{where} must not embed credentials")
    host = hostname.casefold().rstrip(".")
    if host == "localhost" or host.endswith(LOCAL_HOST_SUFFIXES):
        raise ContractError(f"{where} must not reference a local/private host")
    try:
        address = ipaddress.ip_address(host)
    except ValueError:
        address = None
    if address is not None and not address.is_global:
        raise ContractError(f"{where} must not reference a non-public IP address")
    for key, _value in parse_qsl(parsed.query, keep_blank_values=True):
        if key.casefold() in SENSITIVE_QUERY_KEYS:
            raise ContractError(f"{where} must not contain credential or signature query parameters")
    return text


def _unique_strings(value: Any, where: str) -> list[str]:
    result = [_str(item, f"{where}[{i}]") for i, item in enumerate(_arr(value, where))]
    if len(result) != len(set(result)):
        raise ContractError(f"{where} must not contain duplicates")
    return result


def _commands(value: Any, where: str) -> None:
    commands = _arr(value, where)
    if not commands:
        raise ContractError(f"{where} must contain at least one command")
    for i, item in enumerate(commands):
        command = _obj(item, f"{where}[{i}]")
        _closed(command, f"{where}[{i}]", {"argv", "purpose"}, {"argv", "purpose", "cwd"})
        argv = _arr(command["argv"], f"{where}[{i}].argv")
        if not argv:
            raise ContractError(f"{where}[{i}].argv must not be empty")
        for j, arg in enumerate(argv):
            _str(arg, f"{where}[{i}].argv[{j}]")
        _str(command["purpose"], f"{where}[{i}].purpose")
        if "cwd" in command:
            _path(command["cwd"], f"{where}[{i}].cwd")


def validate_task(payload: Any, *, expected_repository: str | None = None, expected_main_sha: str | None = None) -> None:
    task = _obj(payload, "task")
    required = {
        "profile_version", "task_id", "repository", "state", "agent_ready", "workstream",
        "reviewed_against", "shared_surfaces", "dependencies", "next_action", "hard_stop", "acceptance",
    }
    _closed(task, "task", required, required | {"external_sources", "data_boundary"})
    if _str(task["profile_version"], "task.profile_version") != PROFILE_VERSION:
        raise ContractError(f"task.profile_version must equal {PROFILE_VERSION}")
    if not ID_RE.fullmatch(_str(task["task_id"], "task.task_id")):
        raise ContractError("task.task_id has an invalid format")
    repository = _str(task["repository"], "task.repository")
    if not REPOSITORY_RE.fullmatch(repository):
        raise ContractError("task.repository must be in owner/name form")
    if expected_repository and repository != expected_repository:
        raise ContractError(f"task.repository is {repository}, expected {expected_repository}")
    state = _str(task["state"], "task.state")
    if state not in TASK_STATES:
        raise ContractError(f"task.state is unsupported: {state}")
    agent_ready = _bool(task["agent_ready"], "task.agent_ready")
    if state in {"blocked", "complete"} and agent_ready:
        raise ContractError(f"task.agent_ready must be false when task.state is {state}")
    _str(task["workstream"], "task.workstream")
    reviewed = _obj(task["reviewed_against"], "task.reviewed_against")
    _closed(reviewed, "task.reviewed_against", {"ref", "commit", "checked_at"}, {"ref", "commit", "checked_at"})
    if _str(reviewed["ref"], "task.reviewed_against.ref") != "refs/heads/main":
        raise ContractError("task.reviewed_against.ref must be refs/heads/main")
    reviewed_sha = _commit(reviewed["commit"], "task.reviewed_against.commit")
    _timestamp(reviewed["checked_at"], "task.reviewed_against.checked_at")
    if expected_main_sha and reviewed_sha != _commit(expected_main_sha, "expected_main_sha"):
        raise ContractError(f"task is stale: reviewed_against {reviewed_sha}, current main {expected_main_sha}")
    surfaces = [_path(item, f"task.shared_surfaces[{i}]") for i, item in enumerate(_arr(task["shared_surfaces"], "task.shared_surfaces"))]
    if len(surfaces) != len(set(surfaces)):
        raise ContractError("task.shared_surfaces must not contain duplicates")
    _unique_strings(task["dependencies"], "task.dependencies")
    _str(task["next_action"], "task.next_action")
    _str(task["hard_stop"], "task.hard_stop")
    acceptance = _obj(task["acceptance"], "task.acceptance")
    _closed(acceptance, "task.acceptance", {"criteria", "commands", "evidence"}, {"criteria", "commands", "evidence"})
    if not _unique_strings(acceptance["criteria"], "task.acceptance.criteria"):
        raise ContractError("task.acceptance.criteria must not be empty")
    _commands(acceptance["commands"], "task.acceptance.commands")
    for i, evidence in enumerate(_arr(acceptance["evidence"], "task.acceptance.evidence")):
        _path(evidence, f"task.acceptance.evidence[{i}]")
    if "data_boundary" in task:
        boundary = _obj(task["data_boundary"], "task.data_boundary")
        _closed(boundary, "task.data_boundary", {"bytes_policy"}, {"bytes_policy", "source_identity"})
        if _str(boundary["bytes_policy"], "task.data_boundary.bytes_policy") not in DATA_POLICIES:
            raise ContractError("unsupported task.data_boundary.bytes_policy")
        if "source_identity" in boundary:
            _str(boundary["source_identity"], "task.data_boundary.source_identity")
    if "external_sources" in task:
        for i, item in enumerate(_arr(task["external_sources"], "task.external_sources")):
            source = _obj(item, f"task.external_sources[{i}]")
            _closed(source, f"task.external_sources[{i}]", {"uri", "role", "reviewed_at"}, {"uri", "role", "reviewed_at", "version"})
            _public_external_uri(source["uri"], f"task.external_sources[{i}].uri")
            _str(source["role"], f"task.external_sources[{i}].role")
            _timestamp(source["reviewed_at"], f"task.external_sources[{i}].reviewed_at")
            if "version" in source and _str(source["version"], f"task.external_sources[{i}].version").lower() == "latest":
                raise ContractError("external source version must not be mutable 'latest'")


def _validated_manifest_binding(manifest_ref: str, artifact_kind: str, *, where: str) -> dict[str, Any]:
    manifest_path = ROOT / manifest_ref
    try:
        manifest_payload = manifest_contract.load_manifest(manifest_path)
        manifest_contract.validate_structure(manifest_payload)
    except manifest_contract.ManifestError as exc:
        raise ContractError(f"{where}.manifest does not satisfy the dataset-manifest contract: {exc}") from exc
    if Path(manifest_ref).stem != manifest_payload["dataset_id"]:
        raise ContractError(f"{where}.manifest filename must equal its dataset_id")
    artifact = manifest_payload[f"{artifact_kind}_artifact"]
    if artifact is None:
        raise ContractError(f"{where} selected {artifact_kind} artifact is not identified by the manifest")
    return artifact


def _validate_run_v2_input(
    inp: dict[str, Any],
    *,
    index: int,
    input_ids: set[str],
    input_identities: set[str],
    input_hashes: set[str],
) -> None:
    where = f"run.inputs[{index}]"
    required = {"id", "kind", "identity", "scientific_role"}
    allowed = required | {"manifest", "artifact", "sha256", "version"}
    _closed(inp, where, required, allowed)
    input_id = _str(inp["id"], f"{where}.id")
    if input_id in input_ids:
        raise ContractError(f"duplicate run input id: {input_id}")
    input_ids.add(input_id)
    kind = _str(inp["kind"], f"{where}.kind")
    if kind not in RUN_INPUT_KINDS_V2:
        raise ContractError(f"unsupported {where}.kind: {kind}")
    identity = _str(inp["identity"], f"{where}.identity")
    if identity in input_identities:
        raise ContractError(f"duplicate exact run input identity: {identity}")
    input_identities.add(identity)
    role = _str(inp["scientific_role"], f"{where}.scientific_role")
    allowed_roles = DATA_SCIENTIFIC_ROLES_V2 if kind == "data" else RUN_ROLE_BY_KIND_V2[kind]
    if role not in allowed_roles:
        raise ContractError(f"unsupported {where}.scientific_role {role!r} for kind {kind!r}")
    if "version" in inp and _str(inp["version"], f"{where}.version").lower() == "latest":
        raise ContractError(f"{where}.version must not be mutable 'latest'")

    digest: str | None = None
    if kind == "data":
        if "manifest" not in inp or "artifact" not in inp or "sha256" not in inp:
            raise ContractError(f"{where} kind data requires manifest, raw/derived artifact and exact sha256")
        manifest_ref = _repository_file(inp["manifest"], f"{where}.manifest", prefix="manifests/", suffix=".json")
        if len(Path(manifest_ref).parts) != 2:
            raise ContractError(f"{where}.manifest must directly reference one manifests/*.json file")
        artifact_kind = _str(inp["artifact"], f"{where}.artifact")
        if artifact_kind not in DATA_ARTIFACT_KINDS_V2:
            raise ContractError(f"{where}.artifact must be raw or derived")
        artifact = _validated_manifest_binding(manifest_ref, artifact_kind, where=where)
        digest = _sha256(inp["sha256"], f"{where}.sha256")
        if artifact["sha256"] != digest:
            raise ContractError(f"{where}.sha256 does not match the selected manifest artifact")
        if artifact["storage_reference"] != identity:
            raise ContractError(f"{where}.identity must match the selected manifest artifact storage_reference")
    else:
        if "manifest" in inp or "artifact" in inp:
            raise ContractError(f"{where}.manifest/artifact are only valid for kind data")
        if "sha256" in inp:
            digest = _sha256(inp["sha256"], f"{where}.sha256")

    if digest is not None:
        if digest in input_hashes:
            raise ContractError(
                f"duplicate exact input content sha256: {digest}; split/model roles require distinct content identities"
            )
        input_hashes.add(digest)
    if kind in {"model", "config", "fixture"} and "sha256" not in inp and "version" not in inp:
        raise ContractError(f"{where} requires sha256 or exact version for kind {kind}")


def _validate_v2_claim_reference(
    value: Any,
    *,
    where: str,
    input_ids: set[str],
    output_paths: set[str],
    validation_checks: set[str],
) -> tuple[str, str]:
    reference = _obj(value, where)
    _closed(reference, where, {"kind", "ref"}, {"kind", "ref"})
    kind = _str(reference["kind"], f"{where}.kind")
    if kind not in CLAIM_REFERENCE_KINDS_V2:
        raise ContractError(f"unsupported {where}.kind: {kind}")
    ref = _str(reference["ref"], f"{where}.ref")
    if kind == "input":
        if ref not in input_ids:
            raise ContractError(f"{where}.ref does not resolve to a run input id: {ref}")
    elif kind == "output":
        if ref not in output_paths:
            raise ContractError(f"{where}.ref does not resolve to a run output path: {ref}")
    elif kind == "validation":
        if ref not in validation_checks:
            raise ContractError(f"{where}.ref does not resolve to a validation check: {ref}")
    elif kind == "manifest":
        manifest = _repository_file(ref, f"{where}.ref", prefix="manifests/", suffix=".json")
        if len(Path(manifest).parts) != 2:
            raise ContractError(f"{where}.ref must directly reference one manifests/*.json file")
    elif kind == "source_review":
        review = _repository_file(ref, f"{where}.ref", prefix="docs/source-reviews/", suffix=".md")
        if Path(review).name == "README.md" or len(Path(review).parts) != 3:
            raise ContractError(f"{where}.ref must reference one canonical source-review document")
    elif kind == "repository_path":
        _repository_file(ref, f"{where}.ref")
    else:
        _public_external_uri(ref, f"{where}.ref")
    return kind, ref


def validate_run(payload: Any, *, expected_repository: str | None = None) -> None:
    run = _obj(payload, "run")
    required = {"profile_version", "run_id", "repository", "execution", "inputs", "randomness", "outputs", "validation", "status", "claims", "limitations"}
    _closed(run, "run", required, required | {"environment", "semantics", "interoperability"})
    profile_version = _str(run["profile_version"], "run.profile_version")
    if profile_version not in {RUN_PROFILE_V1, RUN_PROFILE_V2}:
        raise ContractError(f"run.profile_version must equal {RUN_PROFILE_V1} or {RUN_PROFILE_V2}")
    is_v2 = profile_version == RUN_PROFILE_V2
    if not ID_RE.fullmatch(_str(run["run_id"], "run.run_id")):
        raise ContractError("run.run_id has an invalid format")
    repository = _obj(run["repository"], "run.repository")
    _closed(repository, "run.repository", {"name", "commit", "dirty"}, {"name", "commit", "tree", "dirty"})
    name = _str(repository["name"], "run.repository.name")
    if not REPOSITORY_RE.fullmatch(name):
        raise ContractError("run.repository.name must be in owner/name form")
    if expected_repository and name != expected_repository:
        raise ContractError(f"run.repository.name is {name}, expected {expected_repository}")
    _commit(repository["commit"], "run.repository.commit")
    _bool(repository["dirty"], "run.repository.dirty")
    if "tree" in repository:
        _commit(repository["tree"], "run.repository.tree")
    execution = _obj(run["execution"], "run.execution")
    _closed(execution, "run.execution", {"commands", "started_at", "ended_at", "exit_code"}, {"commands", "started_at", "ended_at", "exit_code"})
    _commands(execution["commands"], "run.execution.commands")
    started = _timestamp(execution["started_at"], "run.execution.started_at")
    ended = _timestamp(execution["ended_at"], "run.execution.ended_at")
    if ended < started:
        raise ContractError("run.execution.ended_at must not precede started_at")
    exit_code = _int(execution["exit_code"], "run.execution.exit_code")
    input_ids: set[str] = set()
    input_identities: set[str] = set()
    input_hashes: set[str] = set()
    for i, item in enumerate(_arr(run["inputs"], "run.inputs")):
        inp = _obj(item, f"run.inputs[{i}]")
        if is_v2:
            _validate_run_v2_input(
                inp,
                index=i,
                input_ids=input_ids,
                input_identities=input_identities,
                input_hashes=input_hashes,
            )
            continue
        _closed(inp, f"run.inputs[{i}]", {"id", "kind", "identity"}, {"id", "kind", "identity", "sha256", "version"})
        input_id = _str(inp["id"], f"run.inputs[{i}].id")
        if input_id in input_ids:
            raise ContractError(f"duplicate run input id: {input_id}")
        input_ids.add(input_id)
        kind = _str(inp["kind"], f"run.inputs[{i}].kind")
        _str(inp["identity"], f"run.inputs[{i}].identity")
        if "sha256" in inp:
            _sha256(inp["sha256"], f"run.inputs[{i}].sha256")
        if "version" in inp and _str(inp["version"], f"run.inputs[{i}].version").lower() == "latest":
            raise ContractError(f"run.inputs[{i}].version must not be mutable 'latest'")
        if kind in {"config", "data", "model", "fixture"} and "sha256" not in inp and "version" not in inp:
            raise ContractError(f"run.inputs[{i}] requires sha256 or exact version for kind {kind}")
    randomness = _obj(run["randomness"], "run.randomness")
    mode = _str(randomness.get("mode"), "run.randomness.mode")
    if mode == "deterministic":
        _closed(randomness, "run.randomness", {"mode"}, {"mode"})
    elif mode == "stochastic":
        keys = {"mode", "algorithm", "implementation", "seed_material", "stream_identity", "draw_protocol"}
        _closed(randomness, "run.randomness", keys, keys)
        for key in keys - {"mode"}:
            _str(randomness[key], f"run.randomness.{key}")
    else:
        raise ContractError("run.randomness.mode must be deterministic or stochastic")
    output_paths: set[str] = set()
    for i, item in enumerate(_arr(run["outputs"], "run.outputs")):
        out = _obj(item, f"run.outputs[{i}]")
        _closed(out, f"run.outputs[{i}]", {"path", "sha256", "byte_size", "media_type"}, {"path", "sha256", "byte_size", "media_type"})
        path = _path(out["path"], f"run.outputs[{i}].path")
        if path in output_paths:
            raise ContractError(f"duplicate run output path: {path}")
        output_paths.add(path)
        _sha256(out["sha256"], f"run.outputs[{i}].sha256")
        _int(out["byte_size"], f"run.outputs[{i}].byte_size", 0)
        _str(out["media_type"], f"run.outputs[{i}].media_type")
    validation_statuses: list[str] = []
    validation_checks: set[str] = set()
    validations = _arr(run["validation"], "run.validation")
    if not validations:
        raise ContractError("run.validation must contain at least one check")
    for i, item in enumerate(validations):
        check = _obj(item, f"run.validation[{i}]")
        _closed(check, f"run.validation[{i}]", {"check", "status"}, {"check", "status", "evidence"})
        check_id = _str(check["check"], f"run.validation[{i}].check")
        if is_v2 and check_id in validation_checks:
            raise ContractError(f"duplicate run validation check: {check_id}")
        validation_checks.add(check_id)
        check_status = _str(check["status"], f"run.validation[{i}].status")
        if check_status not in RUN_STATUSES:
            raise ContractError(f"unsupported run.validation[{i}].status: {check_status}")
        validation_statuses.append(check_status)
        if "evidence" in check:
            _str(check["evidence"], f"run.validation[{i}].evidence")
    status = _str(run["status"], "run.status")
    if status not in RUN_STATUSES:
        raise ContractError(f"unsupported run.status: {status}")
    if status == "pass" and exit_code != 0:
        raise ContractError("run.status pass requires execution.exit_code 0")
    if status == "pass" and any(value != "pass" for value in validation_statuses):
        raise ContractError("run.status pass requires every validation check to pass")
    if status in {"fail", "blocked", "not_comparable"} and status not in validation_statuses:
        raise ContractError(f"run.status {status} requires at least one {status} validation")
    for i, item in enumerate(_arr(run["claims"], "run.claims")):
        claim = _obj(item, f"run.claims[{i}]")
        if not is_v2:
            _closed(claim, f"run.claims[{i}]", {"statement", "evidence_class", "references"}, {"statement", "evidence_class", "references"})
            _str(claim["statement"], f"run.claims[{i}].statement")
            evidence_class = _str(claim["evidence_class"], f"run.claims[{i}].evidence_class")
            if evidence_class not in EVIDENCE_CLASSES:
                raise ContractError(f"unsupported evidence class: {evidence_class}")
            refs = _unique_strings(claim["references"], f"run.claims[{i}].references")
            if evidence_class == "external_evidence" and not refs:
                raise ContractError("external_evidence claims require at least one reference")
            continue
        claim_required = {"statement", "evidence_class", "references", "scope", "limitations"}
        _closed(claim, f"run.claims[{i}]", claim_required, claim_required)
        _str(claim["statement"], f"run.claims[{i}].statement")
        evidence_class = _str(claim["evidence_class"], f"run.claims[{i}].evidence_class")
        if evidence_class not in EVIDENCE_CLASSES:
            raise ContractError(f"unsupported evidence class: {evidence_class}")
        raw_refs = _arr(claim["references"], f"run.claims[{i}].references")
        if not raw_refs:
            raise ContractError(f"run.claims[{i}].references must contain at least one resolvable reference")
        resolved_refs: list[tuple[str, str]] = []
        for j, reference in enumerate(raw_refs):
            resolved_refs.append(
                _validate_v2_claim_reference(
                    reference,
                    where=f"run.claims[{i}].references[{j}]",
                    input_ids=input_ids,
                    output_paths=output_paths,
                    validation_checks=validation_checks,
                )
            )
        if len(resolved_refs) != len(set(resolved_refs)):
            raise ContractError(f"run.claims[{i}].references must not contain duplicates")
        if evidence_class == "external_evidence" and not any(
            kind in {"manifest", "source_review", "repository_path", "external_uri"} for kind, _ref in resolved_refs
        ):
            raise ContractError("external_evidence claims require an external/repository evidence reference")
        scope = _obj(claim["scope"], f"run.claims[{i}].scope")
        _closed(scope, f"run.claims[{i}].scope", set(), CLAIM_SCOPE_KEYS_V2)
        if not scope:
            raise ContractError(f"run.claims[{i}].scope must contain at least one bounded scope field")
        for key, value in scope.items():
            _str(value, f"run.claims[{i}].scope.{key}")
        _unique_strings(claim["limitations"], f"run.claims[{i}].limitations")
    if is_v2:
        _unique_strings(run["limitations"], "run.limitations")
    else:
        for i, limitation in enumerate(_arr(run["limitations"], "run.limitations")):
            _str(limitation, f"run.limitations[{i}]")
    if "environment" in run:
        env = _obj(run["environment"], "run.environment")
        _closed(env, "run.environment", {"os", "architecture", "runtime"}, {"os", "architecture", "runtime", "dependency_lock_sha256"})
        for key in ("os", "architecture", "runtime"):
            _str(env[key], f"run.environment.{key}")
        if "dependency_lock_sha256" in env:
            _sha256(env["dependency_lock_sha256"], "run.environment.dependency_lock_sha256")
    if "semantics" in run:
        semantics = _obj(run["semantics"], "run.semantics")
        allowed = {"currency", "loss_stage", "horizon", "valuation_basis", "model_view"}
        _closed(semantics, "run.semantics", set(), allowed)
        for key, value in semantics.items():
            _str(value, f"run.semantics.{key}")
        if "loss_stage" in semantics and semantics["loss_stage"] not in LOSS_STAGES:
            raise ContractError(f"unsupported run.semantics.loss_stage: {semantics['loss_stage']}")
    if "interoperability" in run:
        for i, item in enumerate(_arr(run["interoperability"], "run.interoperability")):
            interop = _obj(item, f"run.interoperability[{i}]")
            required_interop = {"target", "version", "role", "status", "evidence"}
            _closed(interop, f"run.interoperability[{i}]", required_interop, required_interop | {"profile", "comparison_mode"})
            _str(interop["target"], f"run.interoperability[{i}].target")
            version = _str(interop["version"], f"run.interoperability[{i}].version")
            role = _str(interop["role"], f"run.interoperability[{i}].role")
            interop_status = _str(interop["status"], f"run.interoperability[{i}].status")
            if role not in INTEROP_ROLES or interop_status not in INTEROP_STATUSES:
                raise ContractError("unsupported interoperability role/status")
            evidence = _unique_strings(interop["evidence"], f"run.interoperability[{i}].evidence")
            if interop_status == "tested" and (version.lower() == "latest" or not evidence):
                raise ContractError("tested interoperability requires an exact version and explicit evidence")
            if "profile" in interop:
                _str(interop["profile"], f"run.interoperability[{i}].profile")
            if "comparison_mode" in interop and _str(
                interop["comparison_mode"], f"run.interoperability[{i}].comparison_mode"
            ) not in COMPARISON_MODES:
                raise ContractError("unsupported interoperability comparison mode")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("kind", choices=["task", "run"])
    parser.add_argument("path", type=Path)
    parser.add_argument("--expected-repository")
    parser.add_argument("--expected-main-sha")
    args = parser.parse_args(argv)
    try:
        payload = load_strict_json(args.path)
        if args.kind == "task":
            validate_task(payload, expected_repository=args.expected_repository, expected_main_sha=args.expected_main_sha)
        else:
            if args.expected_main_sha is not None:
                raise ContractError("--expected-main-sha applies only to task validation")
            validate_run(payload, expected_repository=args.expected_repository)
    except ContractError as exc:
        print(f"BLOCKED: {exc}")
        return 1
    print(f"PASS: valid {args.kind} artifact: {args.path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
