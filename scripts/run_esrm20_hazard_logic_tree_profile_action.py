# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Receipt-bound content profile for the two ESRM20 hazard logic trees.

This action deliberately stops before recursive acquisition or runtime
instantiation. Exact receipted bytes are re-verified, then existing reviewed
parsers derive only source-model paths and GSIM request/argument-key identities.
Provider XML and GSIM argument values remain non-persistent.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

try:
    from scripts import profile_eshm20_gsim_identities as gsim_identity
    from scripts.acquire_efehr_gitlab_receipt import (
        EfehrAcquisitionError,
        TOTAL_DEADLINE_SECONDS,
        _declared_length,
        _open_fixed,
        _read_bounded,
        _remaining,
        _validate_exact_response,
    )
    from scripts.efehr_gitlab_receipt import EfehrReceiptError, raw_file_api_url, validate_target
    from scripts.openquake_source_model_logic_tree_dependencies import (
        OpenQuakeLogicTreeError,
        extract_source_model_logic_tree_dependencies,
    )
    from scripts.prepare_agent_action_result import LedgerError, fetch_repository_comments
except ModuleNotFoundError:  # pragma: no cover - module execution is required in workflows
    import profile_eshm20_gsim_identities as gsim_identity
    from acquire_efehr_gitlab_receipt import (
        EfehrAcquisitionError,
        TOTAL_DEADLINE_SECONDS,
        _declared_length,
        _open_fixed,
        _read_bounded,
        _remaining,
        _validate_exact_response,
    )
    from efehr_gitlab_receipt import EfehrReceiptError, raw_file_api_url, validate_target
    from openquake_source_model_logic_tree_dependencies import (
        OpenQuakeLogicTreeError,
        extract_source_model_logic_tree_dependencies,
    )
    from prepare_agent_action_result import LedgerError, fetch_repository_comments

REQUEST_MARKER = "<!-- oc-eq1-esrm20-hazard-logic-tree-profile-request-v1 -->"
RESULT_MARKER = "<!-- oc-eq1-esrm20-hazard-logic-tree-profile-result-v1 -->"
REQUEST_SCHEMA_VERSION = "oc-esrm20-hazard-logic-tree-profile-request-v1"
RESULT_SCHEMA_VERSION = "oc-esrm20-hazard-logic-tree-profile-result-v1"
ACTION = "esrm20_hazard_logic_tree_profile"
CONTROL_ISSUE = 481
SOURCE_SCIENCE_ISSUE = 281
RECEIPT_ISSUE = 476
RECEIPT_COMMENT_ID = 5310073582
DATASET_ID = "efehr.esrm20.risk-inputs.v1.0"
PROJECT_ID = 269
PROJECT_PATH = "efehr/esrm20"
COMMIT_SHA = "05f83bbc9df81d02ee8ddb1801d9d781355ce783"
GSIM_PATH = "Hazard/gmpe_logic_tree_5br_slope_geology.xml"
GSIM_BYTE_COUNT = 34_018
GSIM_SHA256 = "f3efd16db967efd23f6b25837565344a6056282965ed0ecdfdbcb614513471b1"
SOURCE_PATH = "Hazard/source_model_logic_tree_eshm20_v12e_collapsed_risk_model.xml"
SOURCE_BYTE_COUNT = 1_964
SOURCE_SHA256 = "caebf9140922da7f7492d8b0e55c213c70a84d5b725ae37eae31d50e1da4ac3"
TRUSTED_RESULT_LOGIN = "github-actions[bot]"
MAX_XML_BYTES = 1 * 1024 * 1024
MAX_SOURCE_DEPENDENCIES = 256
MAX_GSIM_TOKENS = 256
MAX_GSIM_ARGUMENT_KEYS = 256

_SHA_RE = re.compile(r"^[0-9a-f]{40}$")
_DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
_SAFE_REQUESTER_RE = re.compile(r"^[A-Za-z0-9_.:@/+ -]{1,96}$")
_SAFE_PATH_RE = re.compile(r"^[A-Za-z0-9_.+@/ -]{1,512}$")
_SAFE_TOKEN_RE = re.compile(r"^[A-Za-z0-9_.:+/@-]{1,256}$")
_SAFE_ARGUMENT_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]{0,127}$")
_REQUEST_FIELDS = {
    "schema_version",
    "action",
    "issue",
    "target_sha",
    "dataset_id",
    "requester",
}
_EXTERNAL_RESOURCE_SUFFIXES = ("_file", "_table")
_CANONICAL_OPEN_FIXED = _open_fixed
_CANONICAL_MONOTONIC = time.monotonic


class HazardLogicTreeProfileActionError(RuntimeError):
    """Fail-closed trusted hazard-profile action error."""


def _pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    obj: dict[str, Any] = {}
    for key, value in pairs:
        if key in obj:
            raise HazardLogicTreeProfileActionError("duplicate JSON key")
        obj[key] = value
    return obj


def _reject_constant(value: str) -> Any:
    raise HazardLogicTreeProfileActionError(f"non-finite JSON constant: {value}")


def validate_request(body: object, *, expected_issue: int, execution_sha: str) -> dict[str, Any]:
    if type(expected_issue) is not int or expected_issue != CONTROL_ISSUE:
        raise HazardLogicTreeProfileActionError("wrong runtime issue")
    if type(execution_sha) is not str or _SHA_RE.fullmatch(execution_sha) is None:
        raise HazardLogicTreeProfileActionError("invalid execution SHA")
    if type(body) is not str or body.count(REQUEST_MARKER) != 1:
        raise HazardLogicTreeProfileActionError("invalid hazard profile request marker")
    before, after = body.split(REQUEST_MARKER, 1)
    if before.strip() or not after.strip():
        raise HazardLogicTreeProfileActionError("hazard profile request envelope is not canonical")
    try:
        request = json.loads(after.strip(), object_pairs_hook=_pairs, parse_constant=_reject_constant)
    except HazardLogicTreeProfileActionError:
        raise
    except (json.JSONDecodeError, TypeError, ValueError) as exc:
        raise HazardLogicTreeProfileActionError("invalid hazard profile request JSON") from exc
    if type(request) is not dict or set(request) != _REQUEST_FIELDS:
        raise HazardLogicTreeProfileActionError("hazard profile request fields drifted")
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
            raise HazardLogicTreeProfileActionError(f"hazard profile request {field} drifted")
    requester = request["requester"]
    if (
        type(requester) is not str
        or requester != requester.strip()
        or _SAFE_REQUESTER_RE.fullmatch(requester) is None
    ):
        raise HazardLogicTreeProfileActionError("invalid requester identity")
    return request


def _acquire_exact_bytes(
    *,
    repository_path: str,
    expected_byte_count: int,
    expected_sha256: str,
    opener: Any,
    monotonic: Any,
) -> bytes:
    if expected_byte_count > MAX_XML_BYTES:
        raise HazardLogicTreeProfileActionError("canonical hazard payload exceeds action bound")
    deadline = monotonic() + TOTAL_DEADLINE_SECONDS
    try:
        target = validate_target(
            source_issue=SOURCE_SCIENCE_ISSUE,
            dataset_id=DATASET_ID,
            project_id=PROJECT_ID,
            commit_sha=COMMIT_SHA,
            repository_path=repository_path,
        )
    except EfehrReceiptError as exc:
        raise EfehrAcquisitionError("trusted hazard profile target is invalid") from exc
    url = raw_file_api_url(target)
    request = urllib.request.Request(
        url,
        headers={
            "Accept": "application/xml,text/xml;q=0.9,text/plain;q=0.8,application/octet-stream;q=0.7",
            "User-Agent": "OpenCatastrophe-EFEHR-hazard-profile-v1",
        },
        method="GET",
    )
    try:
        with opener(request, timeout=_remaining(deadline, monotonic)) as response:
            _validate_exact_response(response, url)
            _declared_length(response, expected_byte_count)
            raw = _read_bounded(
                response,
                deadline=deadline,
                maximum=expected_byte_count,
                monotonic=monotonic,
            )
    except EfehrAcquisitionError:
        raise
    except (OSError, urllib.error.URLError, urllib.error.HTTPError, TimeoutError) as exc:
        raise EfehrAcquisitionError(f"hazard profile retrieval failed: {type(exc).__name__}") from exc
    if len(raw) != expected_byte_count:
        raise HazardLogicTreeProfileActionError("hazard payload byte count does not match receipt")
    if hashlib.sha256(raw).hexdigest() != expected_sha256:
        raise HazardLogicTreeProfileActionError("hazard payload SHA-256 does not match receipt")
    return raw


def _safe_path(value: object) -> str:
    if type(value) is not str or _SAFE_PATH_RE.fullmatch(value) is None:
        raise HazardLogicTreeProfileActionError("derived source dependency path is not bounded")
    return value


def _derive_profile(*, gsim_xml_text: str, source_xml_text: str) -> dict[str, Any]:
    """Pure parser composition for exact already-verified XML text."""
    try:
        source_dependencies = extract_source_model_logic_tree_dependencies(
            source_xml_text,
            logic_tree_path=SOURCE_PATH,
        )
    except OpenQuakeLogicTreeError as exc:
        raise HazardLogicTreeProfileActionError("collapsed source logic tree failed reviewed parser") from exc
    if len(source_dependencies) > MAX_SOURCE_DEPENDENCIES:
        raise HazardLogicTreeProfileActionError("source dependency count exceeds bound")
    source_rows: list[dict[str, Any]] = []
    for dependency in source_dependencies:
        if dependency.is_hdf5_companion:
            raise HazardLogicTreeProfileActionError(
                "source parser emitted an HDF5 companion without explicit inventory"
            )
        origins = [
            {
                "uncertainty_type": origin.uncertainty_type,
                "branch_id": origin.branch_id,
            }
            for origin in dependency.origins
        ]
        source_rows.append(
            {
                "resolved_path": _safe_path(dependency.resolved_path),
                "is_hdf5_companion": False,
                "origins": origins,
            }
        )
    if not source_rows:
        raise HazardLogicTreeProfileActionError("collapsed source logic tree exposed no source dependency")

    try:
        gsim_profile = gsim_identity._profile_xml_text(gsim_xml_text)
    except gsim_identity.Eshm20GsimIdentityProfileError as exc:
        raise HazardLogicTreeProfileActionError("GSIM logic tree failed reviewed structural parser") from exc
    branch_set_count = gsim_profile.get("branch_set_count")
    branch_count = gsim_profile.get("branch_count")
    tokens = gsim_profile.get("unique_requested_gsim_tokens")
    keys = gsim_profile.get("unique_argument_keys")
    if (
        type(branch_set_count) is not int
        or isinstance(branch_set_count, bool)
        or not (1 <= branch_set_count <= gsim_identity.MAX_BRANCH_SETS)
        or type(branch_count) is not int
        or isinstance(branch_count, bool)
        or not (1 <= branch_count <= gsim_identity.MAX_BRANCHES)
        or type(tokens) is not list
        or not (1 <= len(tokens) <= MAX_GSIM_TOKENS)
        or type(keys) is not list
        or len(keys) > MAX_GSIM_ARGUMENT_KEYS
    ):
        raise HazardLogicTreeProfileActionError("GSIM structural profile is outside bounded policy")
    normalized_tokens: list[str] = []
    for token in tokens:
        if type(token) is not str or _SAFE_TOKEN_RE.fullmatch(token) is None:
            raise HazardLogicTreeProfileActionError("GSIM requested token is not bounded")
        normalized_tokens.append(token)
    normalized_keys: list[str] = []
    for key in keys:
        if type(key) is not str or _SAFE_ARGUMENT_RE.fullmatch(key) is None:
            raise HazardLogicTreeProfileActionError("GSIM argument key is not bounded")
        normalized_keys.append(key)
    if normalized_tokens != sorted(set(normalized_tokens)):
        raise HazardLogicTreeProfileActionError("GSIM requested-token set is not canonical")
    if normalized_keys != sorted(set(normalized_keys)):
        raise HazardLogicTreeProfileActionError("GSIM argument-key set is not canonical")
    external_keys = sorted(
        key
        for key in normalized_keys
        if key == "gmpe_table" or key.endswith(_EXTERNAL_RESOURCE_SUFFIXES)
    )
    return {
        "receipt_issue": RECEIPT_ISSUE,
        "receipt_comment_id": RECEIPT_COMMENT_ID,
        "provider_identity": {
            "project_id": PROJECT_ID,
            "project_path": PROJECT_PATH,
            "commit_sha": COMMIT_SHA,
        },
        "gsim_tree": {
            "repository_path": GSIM_PATH,
            "byte_count": GSIM_BYTE_COUNT,
            "sha256": GSIM_SHA256,
            "branch_set_count": branch_set_count,
            "branch_count": branch_count,
            "unique_requested_gsim_tokens": normalized_tokens,
            "unique_argument_keys": normalized_keys,
            "external_resource_argument_keys": external_keys,
            "argument_values_returned": False,
        },
        "source_tree": {
            "repository_path": SOURCE_PATH,
            "byte_count": SOURCE_BYTE_COUNT,
            "sha256": SOURCE_SHA256,
            "dependency_count": len(source_rows),
            "dependencies": source_rows,
            "explicit_repository_inventory_used": False,
        },
        "raw_xml_returned": False,
    }


def acquire_and_profile() -> dict[str, Any]:
    """Reacquire both exact receipt objects and derive bounded content evidence."""
    if _open_fixed is not _CANONICAL_OPEN_FIXED or time.monotonic is not _CANONICAL_MONOTONIC:
        raise EfehrAcquisitionError("hazard profile production transport identity drifted")
    gsim_raw = _acquire_exact_bytes(
        repository_path=GSIM_PATH,
        expected_byte_count=GSIM_BYTE_COUNT,
        expected_sha256=GSIM_SHA256,
        opener=_CANONICAL_OPEN_FIXED,
        monotonic=_CANONICAL_MONOTONIC,
    )
    source_raw = _acquire_exact_bytes(
        repository_path=SOURCE_PATH,
        expected_byte_count=SOURCE_BYTE_COUNT,
        expected_sha256=SOURCE_SHA256,
        opener=_CANONICAL_OPEN_FIXED,
        monotonic=_CANONICAL_MONOTONIC,
    )
    try:
        gsim_text = gsim_raw.decode("utf-8", errors="strict")
        source_text = source_raw.decode("utf-8", errors="strict")
    except UnicodeDecodeError as exc:
        raise HazardLogicTreeProfileActionError("receipted hazard XML is not strict UTF-8") from exc
    return _derive_profile(gsim_xml_text=gsim_text, source_xml_text=source_text)


def _validate_profile(profile: object) -> dict[str, Any]:
    if type(profile) is not dict or set(profile) != {
        "receipt_issue", "receipt_comment_id", "provider_identity", "gsim_tree", "source_tree", "raw_xml_returned"
    }:
        raise HazardLogicTreeProfileActionError("hazard profile fields drifted")
    if profile.get("receipt_issue") != RECEIPT_ISSUE or profile.get("receipt_comment_id") != RECEIPT_COMMENT_ID:
        raise HazardLogicTreeProfileActionError("hazard profile receipt provenance drifted")
    if profile.get("provider_identity") != {
        "project_id": PROJECT_ID,
        "project_path": PROJECT_PATH,
        "commit_sha": COMMIT_SHA,
    }:
        raise HazardLogicTreeProfileActionError("hazard profile provider identity drifted")
    if profile.get("raw_xml_returned") is not False:
        raise HazardLogicTreeProfileActionError("hazard profile widened raw XML output")
    gsim = profile.get("gsim_tree")
    source = profile.get("source_tree")
    if type(gsim) is not dict or set(gsim) != {
        "repository_path", "byte_count", "sha256", "branch_set_count", "branch_count",
        "unique_requested_gsim_tokens", "unique_argument_keys", "external_resource_argument_keys",
        "argument_values_returned"
    }:
        raise HazardLogicTreeProfileActionError("GSIM durable profile fields drifted")
    if (
        gsim.get("repository_path") != GSIM_PATH
        or gsim.get("byte_count") != GSIM_BYTE_COUNT
        or gsim.get("sha256") != GSIM_SHA256
        or gsim.get("argument_values_returned") is not False
    ):
        raise HazardLogicTreeProfileActionError("GSIM durable identity/ceiling drifted")
    tokens = gsim.get("unique_requested_gsim_tokens")
    keys = gsim.get("unique_argument_keys")
    external = gsim.get("external_resource_argument_keys")
    if (
        type(tokens) is not list or not tokens or tokens != sorted(set(tokens))
        or type(keys) is not list or keys != sorted(set(keys))
        or type(external) is not list or external != sorted(set(external))
        or any(type(token) is not str or _SAFE_TOKEN_RE.fullmatch(token) is None for token in tokens)
        or any(type(key) is not str or _SAFE_ARGUMENT_RE.fullmatch(key) is None for key in keys)
        or any(key not in keys for key in external)
        or any(not (key == "gmpe_table" or key.endswith(_EXTERNAL_RESOURCE_SUFFIXES)) for key in external)
    ):
        raise HazardLogicTreeProfileActionError("GSIM durable sets are invalid")
    if type(source) is not dict or set(source) != {
        "repository_path", "byte_count", "sha256", "dependency_count", "dependencies", "explicit_repository_inventory_used"
    }:
        raise HazardLogicTreeProfileActionError("source durable profile fields drifted")
    dependencies = source.get("dependencies")
    if (
        source.get("repository_path") != SOURCE_PATH
        or source.get("byte_count") != SOURCE_BYTE_COUNT
        or source.get("sha256") != SOURCE_SHA256
        or source.get("explicit_repository_inventory_used") is not False
        or type(dependencies) is not list
        or not dependencies
        or source.get("dependency_count") != len(dependencies)
        or len(dependencies) > MAX_SOURCE_DEPENDENCIES
    ):
        raise HazardLogicTreeProfileActionError("source durable identity/dependencies drifted")
    observed_paths: list[str] = []
    for row in dependencies:
        if type(row) is not dict or set(row) != {"resolved_path", "is_hdf5_companion", "origins"}:
            raise HazardLogicTreeProfileActionError("source dependency row fields drifted")
        path = _safe_path(row.get("resolved_path"))
        if row.get("is_hdf5_companion") is not False:
            raise HazardLogicTreeProfileActionError("unproven HDF5 companion entered durable profile")
        origins = row.get("origins")
        if type(origins) is not list or not origins:
            raise HazardLogicTreeProfileActionError("source dependency lacks origin")
        for origin in origins:
            if type(origin) is not dict or set(origin) != {"uncertainty_type", "branch_id"}:
                raise HazardLogicTreeProfileActionError("source dependency origin fields drifted")
            if origin.get("uncertainty_type") not in {"sourceModel", "extendModel"}:
                raise HazardLogicTreeProfileActionError("source dependency origin type drifted")
            if type(origin.get("branch_id")) is not str or not origin["branch_id"]:
                raise HazardLogicTreeProfileActionError("source dependency branch ID is invalid")
        observed_paths.append(path)
    if observed_paths != sorted(set(observed_paths)):
        raise HazardLogicTreeProfileActionError("source dependency paths are not canonical")
    return profile


def _base_result(*, execution_sha: str) -> dict[str, Any]:
    return {
        "schema_version": RESULT_SCHEMA_VERSION,
        "action": ACTION,
        "source_issue": CONTROL_ISSUE,
        "source_science_issue": SOURCE_SCIENCE_ISSUE,
        "dataset_id": DATASET_ID,
        "target_sha": execution_sha,
        "execution_sha": execution_sha,
        "byte_identity_verified": False,
        "content_profile_verified": False,
        "transitive_dependency_byte_closure_verified": False,
        "runtime_compatibility_verified": False,
        "external_bytes_persisted": False,
        "publication_authorized": False,
        "model_use_authorized": False,
    }


def _parse_trusted_terminal_result(body: object, *, execution_sha: str) -> bool:
    if type(body) is not str or RESULT_MARKER not in body:
        return False
    if body.count(RESULT_MARKER) != 1:
        raise HazardLogicTreeProfileActionError("trusted hazard profile marker is malformed")
    before, after = body.split(RESULT_MARKER, 1)
    if before.strip() or not after.strip():
        raise HazardLogicTreeProfileActionError("trusted hazard profile envelope is malformed")
    try:
        result = json.loads(after.strip(), object_pairs_hook=_pairs, parse_constant=_reject_constant)
    except HazardLogicTreeProfileActionError:
        raise
    except (json.JSONDecodeError, TypeError, ValueError) as exc:
        raise HazardLogicTreeProfileActionError("trusted hazard profile JSON is malformed") from exc
    if type(result) is not dict:
        raise HazardLogicTreeProfileActionError("trusted hazard profile result is not an object")
    for field, expected in _base_result(execution_sha=execution_sha).items():
        if field in {"byte_identity_verified", "content_profile_verified"}:
            continue
        observed = result.get(field)
        if type(observed) is not type(expected) or observed != expected:
            raise HazardLogicTreeProfileActionError(f"trusted hazard result drifted at {field}")
    if result.get("status") == "pass":
        if result.get("byte_identity_verified") is not True or result.get("content_profile_verified") is not True:
            raise HazardLogicTreeProfileActionError("trusted hazard PASS lacks closed evidence gates")
        _validate_profile(result.get("profile"))
        return True
    if result.get("status") == "blocked":
        if result.get("failure_class") not in {"acquisition_failure", "profile_failure"}:
            raise HazardLogicTreeProfileActionError("trusted hazard blocked failure class drifted")
        if result.get("profile") is not None:
            raise HazardLogicTreeProfileActionError("trusted hazard blocked result leaked profile")
        if result.get("byte_identity_verified") is not False or result.get("content_profile_verified") is not False:
            raise HazardLogicTreeProfileActionError("trusted hazard blocked result widened evidence")
        return True
    raise HazardLogicTreeProfileActionError("trusted hazard result has non-terminal status")


def has_terminal_result(
    *, repository: str, token: str, execution_sha: str, opener: Any | None = None, max_pages: int = 20
) -> bool:
    if type(execution_sha) is not str or _SHA_RE.fullmatch(execution_sha) is None:
        raise HazardLogicTreeProfileActionError("invalid execution SHA")
    kwargs: dict[str, Any] = {"issue": CONTROL_ISSUE, "max_pages": max_pages}
    if opener is not None:
        kwargs["opener"] = opener
    try:
        comments = fetch_repository_comments(repository, token, **kwargs)
    except LedgerError as exc:
        raise HazardLogicTreeProfileActionError("result ledger is incomplete") from exc
    for comment in comments:
        user = comment.get("user")
        login = user.get("login") if type(user) is dict else None
        if login != TRUSTED_RESULT_LOGIN:
            continue
        if _parse_trusted_terminal_result(comment.get("body"), execution_sha=execution_sha):
            return True
    return False


def run_profile(*, execution_sha: str) -> dict[str, Any]:
    if type(execution_sha) is not str or _SHA_RE.fullmatch(execution_sha) is None:
        raise HazardLogicTreeProfileActionError("invalid execution SHA")
    result = _base_result(execution_sha=execution_sha)
    try:
        profile = acquire_and_profile()
    except EfehrAcquisitionError:
        result.update({"status": "blocked", "failure_class": "acquisition_failure", "profile": None})
        return result
    except HazardLogicTreeProfileActionError:
        result.update({"status": "blocked", "failure_class": "profile_failure", "profile": None})
        return result
    try:
        profile = _validate_profile(profile)
    except HazardLogicTreeProfileActionError:
        result.update({"status": "blocked", "failure_class": "profile_failure", "profile": None})
        return result
    result.update(
        {
            "status": "pass",
            "failure_class": None,
            "profile": profile,
            "byte_identity_verified": True,
            "content_profile_verified": True,
        }
    )
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--comment-body-env", required=True)
    parser.add_argument("--expected-issue", type=int, required=True)
    parser.add_argument("--execution-sha", required=True)
    parser.add_argument("--validate-request-only", action="store_true")
    parser.add_argument("--output")
    args = parser.parse_args(argv)
    body = os.environ.get(args.comment_body_env)
    validate_request(body, expected_issue=args.expected_issue, execution_sha=args.execution_sha)
    if args.validate_request_only:
        return 0
    if not args.output:
        raise HazardLogicTreeProfileActionError("--output is required for execution")
    result = run_profile(execution_sha=args.execution_sha)
    Path(args.output).write_text(
        json.dumps(result, sort_keys=True, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
