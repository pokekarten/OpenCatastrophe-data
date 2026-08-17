# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Trusted-main OpenQuake-3.14 ingestion gate for exact ESRM20 Kosovo site bytes.

This gate is intentionally narrower than a hazard calculation. It reacquires the
already-receipted Kosovo site model and exact ESRM20 GSIM logic tree, verifies
both byte identities before interpretation, then asks the frozen OpenQuake 3.14
implementation to parse the real NRML site model with ``readinput.get_site_model``.
Only counts and required field names leave the runtime. Raw provider bytes,
coordinates and attribute values never leave the transient process.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import tempfile
import time
import urllib.error
import urllib.request
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Callable

from scripts import acquire_efehr_kosovo_site_profile as _site_transport
from scripts import run_esrm20_gsim_reference_runtime as _esrm_runtime
from scripts import run_eshm20_gsim_reference_runtime as _base_runtime
from scripts.prepare_agent_action_result import LedgerError, fetch_repository_comments

REQUEST_MARKER = "<!-- oc-eq1-esrm20-kosovo-site-openquake-runtime-request-v1 -->"
RESULT_MARKER = "<!-- oc-eq1-esrm20-kosovo-site-openquake-runtime-result-v1 -->"
REQUEST_SCHEMA_VERSION = "oc-esrm20-kosovo-site-openquake-runtime-request-v1"
RESULT_SCHEMA_VERSION = "oc-esrm20-kosovo-site-openquake-runtime-result-v1"
ACTION = "esrm20_kosovo_site_openquake_runtime_ingestion"
CONTROL_ISSUE = 291
SOURCE_SCIENCE_ISSUE = 284
DATASET_ID = "efehr.esrm20.risk-inputs.v1.0"
OPENQUAKE_TAG = "v3.14.0"
OPENQUAKE_COMMIT = "9f044c93d72846421a8faa90ebf0a6afacdf3c20"
EXPECTED_SITE_COUNT = 37
EXPECTED_REQUIRED_PARAMETERS = ("geology", "region", "slope", "vs30", "xvf")

SITE_PROJECT_ID = 269
SITE_PROJECT_PATH = "efehr/esrm20"
SITE_COMMIT_SHA = "05f83bbc9df81d02ee8ddb1801d9d781355ce783"
SITE_REPOSITORY_PATH = "Vs30/Site_model_Kosovo.xml"
SITE_RECEIPT_COMMENT_ID = 5308044390
SITE_EXPECTED_BYTE_COUNT = 5_891
SITE_EXPECTED_SHA256 = "746cf75d91507da8b55a9476c61bb5d884eed42c6268a36b1179f432e8850edd"

GMM_PROJECT_ID = 269
GMM_PROJECT_PATH = "efehr/esrm20"
GMM_COMMIT_SHA = "05f83bbc9df81d02ee8ddb1801d9d781355ce783"
GMM_REPOSITORY_PATH = "Hazard/gmpe_logic_tree_5br_slope_geology.xml"
GMM_EXPECTED_BYTE_COUNT = 34_018
GMM_EXPECTED_SHA256 = "f3efd16d56189c7804824d94b20ed75d6ceefc879144d8bd697c1f9b47cf17b4"
GMM_RUNTIME_RESULT_COMMENT_ID = 5315069949
TRUSTED_RESULT_LOGIN = "github-actions[bot]"

_SHA_RE = re.compile(r"^[0-9a-f]{40}$")
_SAFE_REQUESTER_RE = re.compile(r"^[A-Za-z0-9_.:@/+ -]{1,96}$")
_REQUEST_FIELDS = {
    "schema_version",
    "action",
    "issue",
    "target_sha",
    "dataset_id",
    "requester",
}
_CANONICAL_OPEN_FIXED = _site_transport._CANONICAL_OPEN_FIXED
_CANONICAL_MONOTONIC = _site_transport._CANONICAL_MONOTONIC


class SiteOpenQuakeRuntimeError(RuntimeError):
    """Fail-closed error for the narrow runtime-ingestion evidence gate."""


class SiteRuntimeAcquisitionError(SiteOpenQuakeRuntimeError):
    """Exact site or GSIM provider bytes could not be acquired and verified."""


class SiteRuntimeIngestionError(SiteOpenQuakeRuntimeError):
    """Frozen OpenQuake rejected the exact site/GMM input pair."""


def _pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise SiteOpenQuakeRuntimeError("duplicate JSON key")
        result[key] = value
    return result


def _reject_constant(value: str) -> Any:
    raise SiteOpenQuakeRuntimeError(f"non-finite JSON constant: {value}")


def _require_contract() -> None:
    exact = (
        (_site_transport._CANONICAL_SOURCE_ISSUE, CONTROL_ISSUE, "site content issue"),
        (_site_transport._CANONICAL_SOURCE_SCIENCE_ISSUE, SOURCE_SCIENCE_ISSUE, "science issue"),
        (_site_transport._CANONICAL_DATASET_ID, DATASET_ID, "dataset"),
        (_site_transport._CANONICAL_PROJECT_ID, SITE_PROJECT_ID, "site project"),
        (_site_transport._CANONICAL_PROJECT_PATH, SITE_PROJECT_PATH, "site project path"),
        (_site_transport._CANONICAL_COMMIT_SHA, SITE_COMMIT_SHA, "site commit"),
        (_site_transport._CANONICAL_REPOSITORY_PATH, SITE_REPOSITORY_PATH, "site path"),
        (_site_transport._CANONICAL_RECEIPT_COMMENT_ID, SITE_RECEIPT_COMMENT_ID, "site receipt"),
        (_site_transport._CANONICAL_BYTE_COUNT, SITE_EXPECTED_BYTE_COUNT, "site byte count"),
        (_site_transport._CANONICAL_SHA256, SITE_EXPECTED_SHA256, "site SHA-256"),
        (_esrm_runtime.PROJECT_ID, GMM_PROJECT_ID, "GMM project"),
        (_esrm_runtime.PROJECT_PATH, GMM_PROJECT_PATH, "GMM project path"),
        (_esrm_runtime.COMMIT_SHA, GMM_COMMIT_SHA, "GMM commit"),
        (_esrm_runtime.REPOSITORY_PATH, GMM_REPOSITORY_PATH, "GMM path"),
        (_esrm_runtime.EXPECTED_BYTE_COUNT, GMM_EXPECTED_BYTE_COUNT, "GMM byte count"),
        (_esrm_runtime.EXPECTED_SHA256, GMM_EXPECTED_SHA256, "GMM SHA-256"),
        (_esrm_runtime.OPENQUAKE_COMMIT, OPENQUAKE_COMMIT, "OpenQuake commit"),
    )
    for observed, expected, label in exact:
        if type(observed) is not type(expected) or observed != expected:
            raise SiteOpenQuakeRuntimeError(f"trusted site-runtime {label} drifted")


def _require_production_identity() -> None:
    _require_contract()
    if _site_transport._open_fixed is not _CANONICAL_OPEN_FIXED:
        raise SiteOpenQuakeRuntimeError("trusted site-runtime transport identity drifted")
    if time.monotonic is not _CANONICAL_MONOTONIC:
        raise SiteOpenQuakeRuntimeError("trusted site-runtime monotonic clock drifted")


def validate_request(body: object, *, expected_issue: int, execution_sha: str) -> dict[str, Any]:
    if type(expected_issue) is not int or expected_issue != CONTROL_ISSUE:
        raise SiteOpenQuakeRuntimeError("wrong runtime issue")
    if type(execution_sha) is not str or _SHA_RE.fullmatch(execution_sha) is None:
        raise SiteOpenQuakeRuntimeError("invalid execution SHA")
    if type(body) is not str or body.count(REQUEST_MARKER) != 1:
        raise SiteOpenQuakeRuntimeError("invalid site-runtime request marker")
    before, after = body.split(REQUEST_MARKER, 1)
    if before.strip() or not after.strip():
        raise SiteOpenQuakeRuntimeError("site-runtime request envelope is not canonical")
    try:
        request = json.loads(after.strip(), object_pairs_hook=_pairs, parse_constant=_reject_constant)
    except SiteOpenQuakeRuntimeError:
        raise
    except (json.JSONDecodeError, TypeError, ValueError) as exc:
        raise SiteOpenQuakeRuntimeError("invalid site-runtime request JSON") from exc
    if type(request) is not dict or set(request) != _REQUEST_FIELDS:
        raise SiteOpenQuakeRuntimeError("site-runtime request fields drifted")
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
            raise SiteOpenQuakeRuntimeError(f"site-runtime request {field} drifted")
    requester = request["requester"]
    if (
        type(requester) is not str
        or requester != requester.strip()
        or _SAFE_REQUESTER_RE.fullmatch(requester) is None
    ):
        raise SiteOpenQuakeRuntimeError("invalid requester identity")
    return request


def _acquire_verified_site_bytes() -> bytes:
    """Acquire only the fixed receipted Kosovo XML and keep it process-local."""
    _require_production_identity()
    deadline = time.monotonic() + _site_transport.TOTAL_DEADLINE_SECONDS
    try:
        target = _site_transport.validate_target(
            source_issue=SOURCE_SCIENCE_ISSUE,
            dataset_id=DATASET_ID,
            project_id=SITE_PROJECT_ID,
            commit_sha=SITE_COMMIT_SHA,
            repository_path=SITE_REPOSITORY_PATH,
        )
        url = _site_transport.raw_file_api_url(target)
        request = urllib.request.Request(
            url,
            headers={
                "Accept": "application/xml,text/xml,text/plain;q=0.9,application/octet-stream;q=0.8",
                "User-Agent": "OpenCatastrophe-ESRM20-site-OQ314-runtime-v1",
            },
            method="GET",
        )
        with _CANONICAL_OPEN_FIXED(
            request, timeout=_site_transport._remaining(deadline, time.monotonic)
        ) as response:
            _site_transport._validate_exact_response(response, url)
            _site_transport._declared_length(response, SITE_EXPECTED_BYTE_COUNT)
            raw = bytes(
                _site_transport._read_bounded(
                    response,
                    deadline=deadline,
                    maximum=SITE_EXPECTED_BYTE_COUNT,
                    monotonic=time.monotonic,
                )
            )
    except (
        _site_transport.EfehrReceiptError,
        _site_transport.EfehrAcquisitionError,
        urllib.error.URLError,
        urllib.error.HTTPError,
        OSError,
        TimeoutError,
    ) as exc:
        raise SiteRuntimeAcquisitionError(
            f"trusted Kosovo site acquisition failed: {type(exc).__name__}"
        ) from exc
    if len(raw) != SITE_EXPECTED_BYTE_COUNT:
        raise SiteRuntimeAcquisitionError("trusted Kosovo site byte count drifted")
    if hashlib.sha256(raw).hexdigest() != SITE_EXPECTED_SHA256:
        raise SiteRuntimeAcquisitionError("trusted Kosovo site SHA-256 drifted")
    return raw


def _acquire_verified_gmm_bytes() -> bytes:
    """Reuse the reviewed fixed ESRM20 GSIM acquisition under its binding."""
    _require_contract()
    try:
        with _esrm_runtime.esrm20_binding():
            raw = bytes(_base_runtime._acquire_gmm_bytes())
    except Exception as exc:
        raise SiteRuntimeAcquisitionError(
            f"trusted ESRM20 GMM acquisition failed: {type(exc).__name__}"
        ) from exc
    if len(raw) != GMM_EXPECTED_BYTE_COUNT:
        raise SiteRuntimeAcquisitionError("trusted ESRM20 GMM byte count drifted")
    if hashlib.sha256(raw).hexdigest() != GMM_EXPECTED_SHA256:
        raise SiteRuntimeAcquisitionError("trusted ESRM20 GMM SHA-256 drifted")
    return raw


def _load_openquake_readinput() -> Any:
    _base_runtime._pin_openquake_namespace()
    try:
        from openquake.commonlib import readinput
    except Exception as exc:  # pragma: no cover - exercised only in trusted runtime
        raise SiteRuntimeIngestionError("OpenQuake readinput runtime unavailable") from exc
    if _base_runtime._observed_openquake_commit() != OPENQUAKE_COMMIT:
        raise SiteRuntimeIngestionError("OpenQuake source commit drifted")
    return readinput


def _openquake_ingest(
    *, site_bytes: bytes, gmm_bytes: bytes, image_digest: str, readinput_module: Any | None = None
) -> dict[str, Any]:
    """Run OpenQuake's real GsimLogicTree + NRML site-model conversion path."""
    image_digest = _esrm_runtime._validate_image_digest(image_digest)
    readinput = readinput_module if readinput_module is not None else _load_openquake_readinput()
    with tempfile.TemporaryDirectory(prefix="oc-esrm20-site-runtime-") as directory:
        root = Path(directory)
        site_path = root / "Site_model_Kosovo.xml"
        gmm_path = root / "gmpe_logic_tree_5br_slope_geology.xml"
        site_path.write_bytes(site_bytes)
        gmm_path.write_bytes(gmm_bytes)
        oqparam = SimpleNamespace(
            base_path=str(root),
            inputs={
                "site_model": [str(site_path)],
                "gsim_logic_tree": gmm_path.name,
            },
            correl_model=None,
            number_of_logic_tree_samples=0,
            collapse_gsim_logic_tree=False,
        )
        try:
            gsim_lt = readinput.get_gsim_lt(oqparam)
            required = sorted(gsim_lt.req_site_params)
            site_model = readinput.get_site_model(oqparam)
        except Exception as exc:
            raise SiteRuntimeIngestionError(
                f"OpenQuake site-model ingestion rejected exact inputs: {type(exc).__name__}"
            ) from exc

    if required != list(EXPECTED_REQUIRED_PARAMETERS):
        raise SiteRuntimeIngestionError("OpenQuake GSIM required-site parameter set drifted")
    if len(site_model) != EXPECTED_SITE_COUNT:
        raise SiteRuntimeIngestionError("OpenQuake site-model row count drifted")
    dtype = getattr(site_model, "dtype", None)
    names = getattr(dtype, "names", None)
    if not isinstance(names, tuple) or not set(EXPECTED_REQUIRED_PARAMETERS).issubset(names):
        raise SiteRuntimeIngestionError("OpenQuake site-model parsed fields are insufficient")
    return {
        "openquake_reference": {"tag": OPENQUAKE_TAG, "commit": OPENQUAKE_COMMIT},
        "runtime_image_digest": image_digest,
        "parser_path": "openquake.commonlib.readinput.get_site_model",
        "site_count": EXPECTED_SITE_COUNT,
        "required_site_parameter_names": list(EXPECTED_REQUIRED_PARAMETERS),
        "runtime_value_accept_count": EXPECTED_SITE_COUNT,
        "raw_xml_returned": False,
        "raw_site_rows_returned": False,
        "raw_attribute_values_returned": False,
        "coordinates_returned": False,
        "openquake_runtime_value_acceptance_verified": True,
        "gsim_site_parameter_sufficiency_verified": True,
        "site_parameter_units_verified": False,
        "crs_coordinate_semantics_verified": False,
        "missingness_semantics_verified": False,
        "site_model_compatibility_verified": False,
        "site_adjusted_reference_authorized": False,
        "numerical_hazard_agreement_verified": False,
        "publication_authorized": False,
        "model_use_authorized": False,
    }


def _site_identity() -> dict[str, Any]:
    return {
        "project_id": SITE_PROJECT_ID,
        "project_path": SITE_PROJECT_PATH,
        "commit_sha": SITE_COMMIT_SHA,
        "repository_path": SITE_REPOSITORY_PATH,
        "byte_count": SITE_EXPECTED_BYTE_COUNT,
        "sha256": SITE_EXPECTED_SHA256,
        "receipt_comment_id": SITE_RECEIPT_COMMENT_ID,
    }


def _gmm_identity() -> dict[str, Any]:
    return {
        "project_id": GMM_PROJECT_ID,
        "project_path": GMM_PROJECT_PATH,
        "commit_sha": GMM_COMMIT_SHA,
        "repository_path": GMM_REPOSITORY_PATH,
        "byte_count": GMM_EXPECTED_BYTE_COUNT,
        "sha256": GMM_EXPECTED_SHA256,
        "runtime_result_comment_id": GMM_RUNTIME_RESULT_COMMENT_ID,
    }


def _base_result(*, execution_sha: str) -> dict[str, Any]:
    return {
        "schema_version": RESULT_SCHEMA_VERSION,
        "action": ACTION,
        "source_issue": CONTROL_ISSUE,
        "source_science_issue": SOURCE_SCIENCE_ISSUE,
        "dataset_id": DATASET_ID,
        "target_sha": execution_sha,
        "execution_sha": execution_sha,
        "site_identity": _site_identity(),
        "gmm_identity": _gmm_identity(),
        "external_bytes_persisted": False,
        "publication_authorized": False,
        "model_use_authorized": False,
    }


def _validate_runtime_payload(payload: object) -> dict[str, Any]:
    fields = {
        "openquake_reference", "runtime_image_digest", "parser_path", "site_count",
        "required_site_parameter_names", "runtime_value_accept_count", "raw_xml_returned",
        "raw_site_rows_returned", "raw_attribute_values_returned", "coordinates_returned",
        "openquake_runtime_value_acceptance_verified", "gsim_site_parameter_sufficiency_verified",
        "site_parameter_units_verified", "crs_coordinate_semantics_verified",
        "missingness_semantics_verified", "site_model_compatibility_verified",
        "site_adjusted_reference_authorized", "numerical_hazard_agreement_verified",
        "publication_authorized", "model_use_authorized",
    }
    if type(payload) is not dict or set(payload) != fields:
        raise SiteOpenQuakeRuntimeError("site-runtime payload fields drifted")
    if payload.get("openquake_reference") != {"tag": OPENQUAKE_TAG, "commit": OPENQUAKE_COMMIT}:
        raise SiteOpenQuakeRuntimeError("site-runtime OpenQuake identity drifted")
    _esrm_runtime._validate_image_digest(payload.get("runtime_image_digest"))
    if payload.get("parser_path") != "openquake.commonlib.readinput.get_site_model":
        raise SiteOpenQuakeRuntimeError("site-runtime parser path drifted")
    if payload.get("site_count") != EXPECTED_SITE_COUNT or payload.get("runtime_value_accept_count") != EXPECTED_SITE_COUNT:
        raise SiteOpenQuakeRuntimeError("site-runtime accepted site count drifted")
    if payload.get("required_site_parameter_names") != list(EXPECTED_REQUIRED_PARAMETERS):
        raise SiteOpenQuakeRuntimeError("site-runtime required parameter names drifted")
    for field in (
        "raw_xml_returned", "raw_site_rows_returned", "raw_attribute_values_returned",
        "coordinates_returned", "site_parameter_units_verified", "crs_coordinate_semantics_verified",
        "missingness_semantics_verified", "site_model_compatibility_verified",
        "site_adjusted_reference_authorized", "numerical_hazard_agreement_verified",
        "publication_authorized", "model_use_authorized",
    ):
        if payload.get(field) is not False:
            raise SiteOpenQuakeRuntimeError(f"site-runtime authority widened at {field}")
    for field in ("openquake_runtime_value_acceptance_verified", "gsim_site_parameter_sufficiency_verified"):
        if payload.get(field) is not True:
            raise SiteOpenQuakeRuntimeError(f"site-runtime did not establish {field}")
    return payload


def _validate_terminal_result(result: object, *, execution_sha: str) -> dict[str, Any]:
    base = _base_result(execution_sha=execution_sha)
    expected_fields = set(base) | {"status", "failure_class", "runtime"}
    if type(result) is not dict or set(result) != expected_fields:
        raise SiteOpenQuakeRuntimeError("trusted site-runtime result fields drifted")
    for field, expected in base.items():
        observed = result.get(field)
        if type(observed) is not type(expected) or observed != expected:
            raise SiteOpenQuakeRuntimeError(f"trusted site-runtime result drifted at {field}")
    status = result.get("status")
    if status == "pass":
        if result.get("failure_class") is not None:
            raise SiteOpenQuakeRuntimeError("site-runtime PASS cannot carry failure_class")
        _validate_runtime_payload(result.get("runtime"))
        return result
    if status == "blocked":
        if result.get("failure_class") not in {"site_acquisition_failure", "gmm_acquisition_failure", "runtime_ingestion_failure"} or result.get("runtime") is not None:
            raise SiteOpenQuakeRuntimeError("blocked site-runtime result is not safely bounded")
        return result
    raise SiteOpenQuakeRuntimeError("trusted site-runtime result has non-terminal status")


def _parse_trusted_terminal_result(body: object, *, execution_sha: str) -> bool:
    if type(body) is not str or RESULT_MARKER not in body:
        return False
    if body.count(RESULT_MARKER) != 1:
        raise SiteOpenQuakeRuntimeError("trusted site-runtime result marker is malformed")
    before, after = body.split(RESULT_MARKER, 1)
    if before.strip() or not after.strip():
        raise SiteOpenQuakeRuntimeError("trusted site-runtime result envelope is malformed")
    try:
        result = json.loads(after.strip(), object_pairs_hook=_pairs, parse_constant=_reject_constant)
    except SiteOpenQuakeRuntimeError:
        raise
    except (json.JSONDecodeError, TypeError, ValueError) as exc:
        raise SiteOpenQuakeRuntimeError("trusted site-runtime result JSON is malformed") from exc
    if type(result) is not dict:
        raise SiteOpenQuakeRuntimeError("trusted site-runtime result is not an object")
    target = result.get("target_sha")
    observed = result.get("execution_sha")
    if type(target) is not str or _SHA_RE.fullmatch(target) is None or type(observed) is not str or _SHA_RE.fullmatch(observed) is None or target != observed:
        raise SiteOpenQuakeRuntimeError("trusted site-runtime historical SHA identity is inconsistent")
    _validate_terminal_result(result, execution_sha=observed)
    return observed == execution_sha


def has_terminal_runtime_result(*, repository: str, token: str, execution_sha: str, opener: Any | None = None, max_pages: int = 20) -> bool:
    if type(execution_sha) is not str or _SHA_RE.fullmatch(execution_sha) is None:
        raise SiteOpenQuakeRuntimeError("invalid execution SHA")
    kwargs: dict[str, Any] = {"issue": CONTROL_ISSUE, "max_pages": max_pages}
    if opener is not None:
        kwargs["opener"] = opener
    try:
        comments = fetch_repository_comments(repository, token, **kwargs)
    except LedgerError as exc:
        raise SiteOpenQuakeRuntimeError("site-runtime result ledger is incomplete") from exc
    for comment in comments:
        if type(comment) is not dict:
            raise SiteOpenQuakeRuntimeError("site-runtime ledger contains non-object comment")
        user = comment.get("user")
        login = user.get("login") if type(user) is dict else None
        if login != TRUSTED_RESULT_LOGIN:
            continue
        if _parse_trusted_terminal_result(comment.get("body"), execution_sha=execution_sha):
            return True
    return False


def _run_runtime(
    *,
    execution_sha: str,
    image_digest: str,
    site_acquirer: Callable[[], bytes],
    gmm_acquirer: Callable[[], bytes],
    runtime_ingester: Callable[..., dict[str, Any]],
) -> dict[str, Any]:
    result = _base_result(execution_sha=execution_sha)
    try:
        site_bytes = site_acquirer()
    except SiteRuntimeAcquisitionError:
        result.update({"status": "blocked", "failure_class": "site_acquisition_failure", "runtime": None})
        return _validate_terminal_result(result, execution_sha=execution_sha)
    try:
        gmm_bytes = gmm_acquirer()
    except SiteRuntimeAcquisitionError:
        result.update({"status": "blocked", "failure_class": "gmm_acquisition_failure", "runtime": None})
        return _validate_terminal_result(result, execution_sha=execution_sha)
    try:
        payload = runtime_ingester(site_bytes=site_bytes, gmm_bytes=gmm_bytes, image_digest=image_digest)
    except SiteRuntimeIngestionError:
        result.update({"status": "blocked", "failure_class": "runtime_ingestion_failure", "runtime": None})
        return _validate_terminal_result(result, execution_sha=execution_sha)
    result.update({"status": "pass", "failure_class": None, "runtime": _validate_runtime_payload(payload)})
    return _validate_terminal_result(result, execution_sha=execution_sha)


def run_runtime(*, execution_sha: str, image_digest: str) -> dict[str, Any]:
    _require_production_identity()
    return _run_runtime(
        execution_sha=execution_sha,
        image_digest=image_digest,
        site_acquirer=_acquire_verified_site_bytes,
        gmm_acquirer=_acquire_verified_gmm_bytes,
        runtime_ingester=_openquake_ingest,
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--comment-body-env", required=True)
    parser.add_argument("--expected-issue", type=int, required=True)
    parser.add_argument("--execution-sha", required=True)
    parser.add_argument("--runtime-image-digest-env")
    parser.add_argument("--validate-request-only", action="store_true")
    parser.add_argument("--output")
    args = parser.parse_args(argv)

    body = os.environ.get(args.comment_body_env)
    validate_request(body, expected_issue=args.expected_issue, execution_sha=args.execution_sha)
    if args.validate_request_only:
        return 0
    if not args.output or not args.runtime_image_digest_env:
        raise SiteOpenQuakeRuntimeError("--output and --runtime-image-digest-env are required")
    image_digest = os.environ.get(args.runtime_image_digest_env)
    if type(image_digest) is not str:
        raise SiteOpenQuakeRuntimeError("runtime image digest environment value is absent")
    result = run_runtime(execution_sha=args.execution_sha, image_digest=image_digest)
    Path(args.output).write_text(
        json.dumps(result, sort_keys=True, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
