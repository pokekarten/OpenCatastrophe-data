# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Trusted-main ESHM20 GSIM execution in the reconstructed OQ 3.14 recipe.

A PASS proves only that this execution matched the checked reference-recipe
fields and that every frozen ESHM20 GSIM request passed the already-reviewed
OpenQuake 3.14 alias/registry/constructor gate. It is not a numerical hazard or
risk reference run and does not authorize publication or model use.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import inspect
import json
import os
import platform
import re
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

if __package__ in (None, ""):  # pragma: no cover - direct script execution path
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts import acquire_eshm20_gsim_resource_profile as gmm
from scripts import validate_eshm20_gsim_openquake_runtime as gate
from scripts import validate_eshm20_openquake_runtime as runtime
from scripts.prepare_agent_action_result import LedgerError, fetch_repository_comments

SCHEMA_VERSION = "oc-eshm20-gsim-reference-runtime-execution-v1"
REQUEST_SCHEMA_VERSION = "oc-eshm20-gsim-reference-runtime-request-v1"
REQUEST_MARKER = "<!-- oc-eq1-eshm20-gsim-reference-runtime-request-v1 -->"
RESULT_MARKER = "<!-- oc-eq1-eshm20-gsim-reference-runtime-result-v1 -->"
SOURCE_ISSUE = 432
TRUSTED_RESULT_LOGIN = "github-actions[bot]"
_OPENQUAKE_CHECKOUT_ROOT = Path("/oq-engine")
_OPENQUAKE_PACKAGE_ROOT = _OPENQUAKE_CHECKOUT_ROOT / "openquake"

_SHA_RE = re.compile(r"^[0-9a-f]{40}$")
_DIGEST_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
_REQUESTER_RE = re.compile(r"^[A-Za-z0-9_.:@/+ -]{1,96}$")
_REQUEST_FIELDS = {"schema_version", "issue", "target_sha", "requester"}

# Import-time frozen acquisition authority. Production has no caller-selected
# provider/project/ref/path/size/hash/parser/model surface.
_PROJECT_ID = gmm.PROJECT_ID
_PROJECT_PATH = gmm.PROJECT_PATH
_COMMIT_SHA = gmm.COMMIT_SHA
_REPOSITORY_PATH = gmm.REPOSITORY_PATH
_EXPECTED_BYTES = gmm.EXPECTED_BYTE_COUNT
_EXPECTED_SHA256 = gmm.EXPECTED_SHA256
_OPEN_FIXED = gmm._open_fixed
_READ_BOUNDED = gmm._read_bounded
_REMAINING = gmm._remaining
_VALIDATE_RESPONSE = gmm._validate_exact_response


class ReferenceRuntimeExecutionError(RuntimeError):
    """Fail-closed trusted execution error."""


def _pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    obj: dict[str, Any] = {}
    for key, value in pairs:
        if key in obj:
            raise ReferenceRuntimeExecutionError("duplicate JSON key")
        obj[key] = value
    return obj


def _reject_constant(value: str) -> Any:
    raise ReferenceRuntimeExecutionError(f"non-finite JSON constant: {value}")


def validate_request(
    body: object, *, expected_issue: int, execution_sha: str
) -> dict[str, Any]:
    """Validate one owner-gated request against the trusted execution SHA."""

    if type(expected_issue) is not int or expected_issue != SOURCE_ISSUE:
        raise ReferenceRuntimeExecutionError("wrong runtime issue")
    if type(execution_sha) is not str or not _SHA_RE.fullmatch(execution_sha):
        raise ReferenceRuntimeExecutionError("invalid execution SHA")
    if type(body) is not str or body.count(REQUEST_MARKER) != 1:
        raise ReferenceRuntimeExecutionError("invalid runtime request marker")
    before, after = body.split(REQUEST_MARKER, 1)
    if before.strip() or not after.strip():
        raise ReferenceRuntimeExecutionError("runtime request envelope is not canonical")
    try:
        request = json.loads(
            after.strip(),
            object_pairs_hook=_pairs,
            parse_constant=_reject_constant,
        )
    except ReferenceRuntimeExecutionError:
        raise
    except (json.JSONDecodeError, TypeError, ValueError) as exc:
        raise ReferenceRuntimeExecutionError("invalid runtime request JSON") from exc
    if type(request) is not dict or set(request) != _REQUEST_FIELDS:
        raise ReferenceRuntimeExecutionError("runtime request fields drifted")
    if request["schema_version"] != REQUEST_SCHEMA_VERSION:
        raise ReferenceRuntimeExecutionError("unsupported runtime request schema")
    if type(request["issue"]) is not int or request["issue"] != SOURCE_ISSUE:
        raise ReferenceRuntimeExecutionError("runtime request issue drifted")
    if request["target_sha"] != execution_sha:
        raise ReferenceRuntimeExecutionError("runtime request target is not trusted main")
    requester = request["requester"]
    if (
        type(requester) is not str
        or requester != requester.strip()
        or not _REQUESTER_RE.fullmatch(requester)
    ):
        raise ReferenceRuntimeExecutionError("invalid requester identity")
    return request


def _trusted_terminal_result_execution_sha(body: object) -> str | None:
    """Return a trusted result envelope's own SHA after fail-closed identity checks."""

    if type(body) is not str or RESULT_MARKER not in body:
        return None
    if body.count(RESULT_MARKER) != 1:
        raise ReferenceRuntimeExecutionError("trusted runtime result marker is malformed")
    before, after = body.split(RESULT_MARKER, 1)
    if before.strip() or not after.strip():
        raise ReferenceRuntimeExecutionError("trusted runtime result envelope is malformed")
    try:
        result = json.loads(
            after.strip(),
            object_pairs_hook=_pairs,
            parse_constant=_reject_constant,
        )
    except ReferenceRuntimeExecutionError:
        raise
    except (json.JSONDecodeError, TypeError, ValueError) as exc:
        raise ReferenceRuntimeExecutionError("trusted runtime result JSON is malformed") from exc
    if type(result) is not dict:
        raise ReferenceRuntimeExecutionError("trusted runtime result is not an object")
    exact = (
        ("schema_version", SCHEMA_VERSION),
        ("source_issue", SOURCE_ISSUE),
        ("dataset_id", gmm.DATASET_ID),
        ("status", "pass"),
    )
    for field, expected in exact:
        observed = result.get(field)
        if type(observed) is not type(expected) or observed != expected:
            raise ReferenceRuntimeExecutionError(
                f"trusted runtime result drifted at {field}"
            )
    target_sha = result.get("target_sha")
    execution_sha = result.get("execution_sha")
    if type(target_sha) is not str or _SHA_RE.fullmatch(target_sha) is None:
        raise ReferenceRuntimeExecutionError("trusted runtime result target SHA is invalid")
    if type(execution_sha) is not str or _SHA_RE.fullmatch(execution_sha) is None:
        raise ReferenceRuntimeExecutionError("trusted runtime result execution SHA is invalid")
    if target_sha != execution_sha:
        raise ReferenceRuntimeExecutionError(
            "trusted runtime result target/execution SHA mismatch"
        )
    return execution_sha


def _parse_trusted_terminal_result(body: object, *, execution_sha: str) -> bool:
    """Validate one trusted-bot terminal result for exact-SHA deduplication."""

    if type(body) is not str or RESULT_MARKER not in body:
        return False
    if body.count(RESULT_MARKER) != 1:
        raise ReferenceRuntimeExecutionError("trusted runtime result marker is malformed")
    before, after = body.split(RESULT_MARKER, 1)
    if before.strip() or not after.strip():
        raise ReferenceRuntimeExecutionError("trusted runtime result envelope is malformed")
    try:
        result = json.loads(
            after.strip(),
            object_pairs_hook=_pairs,
            parse_constant=_reject_constant,
        )
    except ReferenceRuntimeExecutionError:
        raise
    except (json.JSONDecodeError, TypeError, ValueError) as exc:
        raise ReferenceRuntimeExecutionError("trusted runtime result JSON is malformed") from exc
    if type(result) is not dict:
        raise ReferenceRuntimeExecutionError("trusted runtime result is not an object")
    exact = (
        ("schema_version", SCHEMA_VERSION),
        ("source_issue", SOURCE_ISSUE),
        ("dataset_id", gmm.DATASET_ID),
        ("status", "pass"),
        ("target_sha", execution_sha),
        ("execution_sha", execution_sha),
        ("same_process_runtime_observation_collected", True),
        ("executing_environment_matches_reconstructed_reference_recipe_fields", True),
        ("gsim_request_reference_recipe_runtime_compatibility_verified", True),
        ("historical_environment_verified", False),
        ("reference_base_image_byte_identity_verified", False),
        ("wheel_byte_identity_verified", False),
        ("numerical_hazard_agreement_verified", False),
        ("imt_component_unit_compatibility_verified", False),
        ("full_hazard_compatibility_verified", False),
        ("site_model_compatibility_verified", False),
        ("vulnerability_compatibility_verified", False),
        ("reference_run_verified", False),
        ("scientific_validity_verified", False),
        ("external_bytes_persisted", False),
        ("publication_authorized", False),
        ("model_use_authorized", False),
    )
    for field, expected in exact:
        observed = result.get(field)
        if type(observed) is not type(expected) or observed != expected:
            raise ReferenceRuntimeExecutionError(
                f"trusted runtime result drifted at {field}"
            )
    image_digest = result.get("execution_container_image_digest")
    if type(image_digest) is not str or not _DIGEST_RE.fullmatch(image_digest):
        raise ReferenceRuntimeExecutionError("trusted runtime image digest is invalid")
    branch_count = result.get("branch_count")
    branches = result.get("branches")
    if (
        type(branch_count) is not int
        or isinstance(branch_count, bool)
        or branch_count <= 0
        or type(branches) is not list
        or len(branches) != branch_count
        or any(
            type(branch) is not dict or branch.get("constructor_accepted") is not True
            for branch in branches
        )
    ):
        raise ReferenceRuntimeExecutionError("trusted runtime branch evidence is invalid")
    return True


def has_terminal_runtime_result(
    *,
    repository: str,
    token: str,
    execution_sha: str,
    opener: Any | None = None,
    max_pages: int = 20,
) -> bool:
    """Fail closed unless the complete bounded Issue #432 ledger is known."""

    if type(execution_sha) is not str or not _SHA_RE.fullmatch(execution_sha):
        raise ReferenceRuntimeExecutionError("invalid execution SHA")
    kwargs: dict[str, Any] = {"issue": SOURCE_ISSUE, "max_pages": max_pages}
    if opener is not None:
        kwargs["opener"] = opener
    try:
        comments = fetch_repository_comments(repository, token, **kwargs)
    except LedgerError as exc:
        raise ReferenceRuntimeExecutionError("runtime result ledger is incomplete") from exc
    for comment in comments:
        user = comment.get("user")
        login = user.get("login") if type(user) is dict else None
        if login != TRUSTED_RESULT_LOGIN:
            continue
        body = comment.get("body")
        own_execution_sha = _trusted_terminal_result_execution_sha(body)
        if own_execution_sha is None:
            continue
        terminal = _parse_trusted_terminal_result(
            body, execution_sha=own_execution_sha
        )
        if own_execution_sha != execution_sha:
            continue
        if terminal:
            return True
    return False


def _acquire_exact_gmm() -> bytes:
    """Transiently acquire only the already-receipted exact GMM object."""

    if (
        gmm.PROJECT_ID != _PROJECT_ID
        or gmm.PROJECT_PATH != _PROJECT_PATH
        or gmm.COMMIT_SHA != _COMMIT_SHA
        or gmm.REPOSITORY_PATH != _REPOSITORY_PATH
        or gmm.EXPECTED_BYTE_COUNT != _EXPECTED_BYTES
        or gmm.EXPECTED_SHA256 != _EXPECTED_SHA256
        or gmm._open_fixed is not _OPEN_FIXED
        or gmm._read_bounded is not _READ_BOUNDED
        or gmm._remaining is not _REMAINING
        or gmm._validate_exact_response is not _VALIDATE_RESPONSE
    ):
        raise ReferenceRuntimeExecutionError("trusted GMM acquisition authority drifted")
    try:
        target = gmm.validate_target(
            source_issue=gmm.SOURCE_ISSUE,
            dataset_id=gmm.DATASET_ID,
            project_id=_PROJECT_ID,
            commit_sha=_COMMIT_SHA,
            repository_path=_REPOSITORY_PATH,
        )
        url = gmm.raw_file_api_url(target)
        request = urllib.request.Request(
            url,
            headers={
                "Accept": "application/xml,text/xml,text/plain;q=0.9,application/octet-stream;q=0.8",
                "User-Agent": "OpenCatastrophe-ESHM20-GSIM-reference-runtime-v1",
            },
            method="GET",
        )
        monotonic = time.monotonic
        deadline = monotonic() + gmm.TOTAL_DEADLINE_SECONDS
        with _OPEN_FIXED(request, timeout=_REMAINING(deadline, monotonic)) as response:
            _VALIDATE_RESPONSE(response, url)
            payload = bytes(
                _READ_BOUNDED(
                    response,
                    deadline=deadline,
                    maximum=_EXPECTED_BYTES,
                    monotonic=monotonic,
                )
            )
    except (
        gmm.EfehrAcquisitionError,
        urllib.error.URLError,
        urllib.error.HTTPError,
        OSError,
        TimeoutError,
    ):
        raise ReferenceRuntimeExecutionError("trusted GMM acquisition failed closed") from None

    if len(payload) != _EXPECTED_BYTES:
        raise ReferenceRuntimeExecutionError("trusted GMM byte count drifted")
    if hashlib.sha256(payload).hexdigest() != _EXPECTED_SHA256:
        raise ReferenceRuntimeExecutionError("trusted GMM SHA-256 drifted")
    return payload


def _pin_openquake_namespace(*, package_root: Path | None = None) -> None:
    """Restrict OpenQuake submodule lookup to the mounted frozen source checkout."""

    expected = (package_root or _OPENQUAKE_PACKAGE_ROOT).resolve()
    if not expected.is_dir():
        raise ReferenceRuntimeExecutionError(
            "fixed OpenQuake package root is unavailable"
        )
    if any(name.startswith("openquake.") for name in sys.modules):
        raise ReferenceRuntimeExecutionError(
            "OpenQuake submodule loaded before source pin"
        )
    try:
        import openquake
    except Exception as exc:
        raise ReferenceRuntimeExecutionError("OpenQuake namespace unavailable") from exc
    if getattr(openquake, "__path__", None) is None:
        raise ReferenceRuntimeExecutionError("OpenQuake namespace path unavailable")
    openquake.__path__ = [str(expected)]
    if [Path(path).resolve() for path in openquake.__path__] != [expected]:
        raise ReferenceRuntimeExecutionError("OpenQuake namespace pin failed")


def _require_fixed_openquake_source(source_file: str | Path) -> Path:
    """Require one loaded OpenQuake source file to live under the fixed checkout."""

    source_path = Path(source_file).resolve()
    package_root = _OPENQUAKE_PACKAGE_ROOT.resolve()
    try:
        source_path.relative_to(package_root)
    except ValueError as exc:
        raise ReferenceRuntimeExecutionError(
            "OpenQuake source resolved outside fixed checkout"
        ) from exc
    if not source_path.is_file():
        raise ReferenceRuntimeExecutionError("OpenQuake source identity unavailable")
    return source_path


def _observed_openquake_commit() -> str:
    try:
        from openquake.hazardlib import valid
        source_file = inspect.getsourcefile(valid.gsim)
        if source_file is None:
            raise ReferenceRuntimeExecutionError("OpenQuake source identity unavailable")
        source_path = _require_fixed_openquake_source(source_file)
        root = gate._verify_exact_openquake_checkout(source_path)
        return gate._git_text(root, "rev-parse", "HEAD")
    except gate.Eshm20GsimRuntimeCompatibilityError as exc:
        raise ReferenceRuntimeExecutionError("OpenQuake exact-source gate failed") from exc


def collect_runtime_observation(image_digest: object) -> dict[str, Any]:
    """Observe the recipe fields in the same process that runs the GSIM gate."""

    if type(image_digest) is not str or not _DIGEST_RE.fullmatch(image_digest):
        raise ReferenceRuntimeExecutionError("invalid execution image digest")
    _pin_openquake_namespace()
    try:
        from openquake import baselib
    except Exception as exc:
        raise ReferenceRuntimeExecutionError("OpenQuake runtime unavailable") from exc

    packages: dict[str, str] = {}
    for name, _ in runtime._REFERENCE_PACKAGES:
        try:
            packages[name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError as exc:
            raise ReferenceRuntimeExecutionError(
                f"missing reference package: {name}"
            ) from exc

    return {
        "engine_commit": _observed_openquake_commit(),
        "engine_version": getattr(baselib, "__version__", None),
        "python_version": platform.python_version(),
        "platform_system": platform.system(),
        "platform_machine": platform.machine(),
        "openblas_num_threads": os.environ.get("OPENBLAS_NUM_THREADS"),
        "packages": packages,
        "container_image_digest": image_digest,
    }


def _bounded_result(
    gate_result: object, *, execution_sha: str, image_digest: str
) -> dict[str, Any]:
    if type(gate_result) is not dict:
        raise ReferenceRuntimeExecutionError("runtime gate result is not an object")
    required_true = (
        "engine_source_commit_verified",
        "reference_runtime_observation_validated",
        "alias_resolution_verified",
        "registry_resolution_verified",
        "constructor_compatibility_verified",
        "exact_source_constructor_compatibility_verified",
    )
    required_false = (
        "gsim_request_runtime_compatibility_verified",
        "full_hazard_compatibility_verified",
        "site_model_compatibility_verified",
        "vulnerability_compatibility_verified",
        "reference_run_verified",
        "scientific_validity_verified",
        "external_bytes_persisted",
        "publication_authorized",
        "model_use_authorized",
    )
    if any(gate_result.get(field) is not True for field in required_true):
        raise ReferenceRuntimeExecutionError("exact-source GSIM gate did not fully pass")
    if any(gate_result.get(field) is not False for field in required_false):
        raise ReferenceRuntimeExecutionError("exact-source GSIM gate widened authority")

    fingerprint = gate_result.get("reference_runtime_fingerprint")
    if (
        type(fingerprint) is not dict
        or fingerprint.get("reference_recipe_match") is not True
        or type(fingerprint.get("observation")) is not dict
        or fingerprint["observation"].get("container_image_digest") != image_digest
    ):
        raise ReferenceRuntimeExecutionError("same-process runtime fingerprint is unbound")

    branches = gate_result.get("branches")
    branch_count = gate_result.get("branch_count")
    if (
        type(branches) is not list
        or not branches
        or type(branch_count) is not int
        or type(branch_count) is bool
        or branch_count != len(branches)
        or any(
            type(branch) is not dict or branch.get("constructor_accepted") is not True
            for branch in branches
        )
    ):
        raise ReferenceRuntimeExecutionError("bounded branch evidence is incomplete")

    return {
        "schema_version": SCHEMA_VERSION,
        "source_issue": SOURCE_ISSUE,
        "dataset_id": gmm.DATASET_ID,
        "status": "pass",
        "target_sha": execution_sha,
        "execution_sha": execution_sha,
        "execution_container_image_digest": image_digest,
        "gmm_identity": gate_result["gmm_identity"],
        "openquake_reference": gate_result["openquake_reference"],
        "reference_runtime_fingerprint": fingerprint,
        "branch_count": branch_count,
        "branches": branches,
        "unique_resolved_gsim_classes": gate_result["unique_resolved_gsim_classes"],
        "alias_requested_tokens": gate_result["alias_requested_tokens"],
        "same_process_runtime_observation_collected": True,
        "executing_environment_matches_reconstructed_reference_recipe_fields": True,
        "gsim_request_reference_recipe_runtime_compatibility_verified": True,
        "historical_environment_verified": False,
        "reference_base_image_byte_identity_verified": False,
        "wheel_byte_identity_verified": False,
        "numerical_hazard_agreement_verified": False,
        "imt_component_unit_compatibility_verified": False,
        "full_hazard_compatibility_verified": False,
        "site_model_compatibility_verified": False,
        "vulnerability_compatibility_verified": False,
        "reference_run_verified": False,
        "scientific_validity_verified": False,
        "external_bytes_persisted": False,
        "publication_authorized": False,
        "model_use_authorized": False,
    }


def run_reference_runtime(
    *, execution_sha: str, image_digest: str
) -> dict[str, Any]:
    payload = _acquire_exact_gmm()
    try:
        observation = collect_runtime_observation(image_digest)
        result = gate.validate_verified_gsim_runtime(payload, observation)
        return _bounded_result(
            result, execution_sha=execution_sha, image_digest=image_digest
        )
    finally:
        payload = b""


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--comment-body-env", required=True)
    parser.add_argument("--expected-issue", type=int, required=True)
    parser.add_argument("--execution-sha", required=True)
    parser.add_argument("--validate-request-only", action="store_true")
    parser.add_argument("--image-digest")
    parser.add_argument("--output")
    args = parser.parse_args(argv)

    body = os.environ.get(args.comment_body_env)
    validate_request(
        body,
        expected_issue=args.expected_issue,
        execution_sha=args.execution_sha,
    )
    if args.validate_request_only:
        return 0
    if not args.image_digest or not args.output:
        parser.error("--image-digest and --output are required for execution")

    result = run_reference_runtime(
        execution_sha=args.execution_sha,
        image_digest=args.image_digest,
    )
    Path(args.output).write_text(
        json.dumps(result, sort_keys=True, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
