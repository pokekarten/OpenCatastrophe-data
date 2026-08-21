# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Trusted-main OpenQuake 3.14 parser/value-domain gate for the fixed ESHM20 site CSV.

This action is deliberately narrower than a hazard run. It re-materializes only
the already-receipted ESHM20 Region-Main site CSV, verifies the frozen byte
identity before parsing, then executes the exact OpenQuake 3.14 site dtype
reader. It emits bounded derived pass/block evidence only; provider rows never
leave the process and no CRS, numerical-fidelity, publication, or model-use
authority is created.
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
from typing import Any, Callable

try:
    from scripts import acquire_eshm20_site_model_profile as source
    from scripts.prepare_agent_action_result import LedgerError, fetch_repository_comments
except ModuleNotFoundError:  # pragma: no cover - direct script execution
    import acquire_eshm20_site_model_profile as source
    from prepare_agent_action_result import LedgerError, fetch_repository_comments

REQUEST_MARKER = "<!-- oc-eq1-eshm20-site-model-oq314-ingestion-request-v1 -->"
RESULT_MARKER = "<!-- oc-eq1-eshm20-site-model-oq314-ingestion-result-v1 -->"
REQUEST_SCHEMA_VERSION = "oc-eshm20-site-model-oq314-ingestion-request-v1"
RESULT_SCHEMA_VERSION = "oc-eshm20-site-model-oq314-ingestion-result-v1"
ACTION = "eshm20_site_model_oq314_ingestion"
CONTROL_ISSUE = 281
DATASET_ID = source.DATASET_ID
OQ_ENGINE_TAG = "v3.14.0"
OQ_ENGINE_COMMIT = "9f044c93d72846421a8faa90ebf0a6afacdf3c20"
EXPECTED_HEADER = (
    "lat",
    "lon",
    "region",
    "vs30",
    "vs30measured",
    "xvf",
    "z1pt0",
    "z2pt5",
)
REQUIRED_MODE_A_FIELDS = ("region", "vs30", "vs30measured", "xvf")
SUPPORTED_REGION_CODES = frozenset({0, 1, 2, 3, 4, 5})
TRUSTED_RESULT_LOGIN = "github-actions[bot]"
_SHA_RE = re.compile(r"^[0-9a-f]{40}$")
_IMAGE_ID_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
_REPO_DIGEST_RE = re.compile(r"^openquake/engine@sha256:[0-9a-f]{64}$")
_SAFE_REQUESTER_RE = re.compile(r"^[A-Za-z0-9_.:@/+ -]{1,96}$")
_REQUEST_FIELDS = {
    "schema_version",
    "action",
    "issue",
    "target_sha",
    "dataset_id",
    "requester",
}
_FALSE_CEILINGS = (
    "crs_authorized",
    "coordinate_semantics_authorized",
    "site_response_authorized",
    "numerical_hazard_agreement_verified",
    "reference_run_verified",
    "independent_validation_verified",
    "external_bytes_persisted",
    "raw_rows_returned",
    "publication_authorized",
    "model_use_authorized",
)


class SiteModelOq314IngestionError(RuntimeError):
    """Fail-closed fixed ESHM20/OQ3.14 ingestion-gate error."""


def _pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    obj: dict[str, Any] = {}
    for key, value in pairs:
        if key in obj:
            raise SiteModelOq314IngestionError("duplicate JSON key")
        obj[key] = value
    return obj


def _reject_constant(value: str) -> Any:
    raise SiteModelOq314IngestionError(f"non-finite JSON constant: {value}")


def validate_request(body: object, *, expected_issue: int, execution_sha: str) -> dict[str, Any]:
    if type(expected_issue) is not int or expected_issue != CONTROL_ISSUE:
        raise SiteModelOq314IngestionError("wrong runtime issue")
    if type(execution_sha) is not str or not _SHA_RE.fullmatch(execution_sha):
        raise SiteModelOq314IngestionError("invalid execution SHA")
    if type(body) is not str or body.count(REQUEST_MARKER) != 1:
        raise SiteModelOq314IngestionError("invalid OQ3.14 site-ingestion request marker")
    before, after = body.split(REQUEST_MARKER, 1)
    if before.strip() or not after.strip():
        raise SiteModelOq314IngestionError("site-ingestion request envelope is not canonical")
    try:
        request = json.loads(
            after.strip(), object_pairs_hook=_pairs, parse_constant=_reject_constant
        )
    except SiteModelOq314IngestionError:
        raise
    except (json.JSONDecodeError, TypeError, ValueError) as exc:
        raise SiteModelOq314IngestionError("invalid site-ingestion request JSON") from exc
    if type(request) is not dict or set(request) != _REQUEST_FIELDS:
        raise SiteModelOq314IngestionError("site-ingestion request fields drifted")
    expected = (
        ("schema_version", REQUEST_SCHEMA_VERSION),
        ("action", ACTION),
        ("issue", CONTROL_ISSUE),
        ("target_sha", execution_sha),
        ("dataset_id", DATASET_ID),
    )
    for field, exact in expected:
        observed = request.get(field)
        if type(observed) is not type(exact) or observed != exact:
            raise SiteModelOq314IngestionError(f"site-ingestion request {field} drifted")
    requester = request["requester"]
    if (
        type(requester) is not str
        or requester != requester.strip()
        or not _SAFE_REQUESTER_RE.fullmatch(requester)
    ):
        raise SiteModelOq314IngestionError("invalid requester identity")
    return request


def _acquire_verified_payload(
    *, opener: Any | None = None, monotonic: Callable[[], float] = time.monotonic
) -> bytes:
    """Fetch only the frozen #361 target and return verified bytes transiently."""
    site_spec = source._require_canonical_target()
    try:
        target = source.validate_target(
            source_issue=source.SOURCE_ISSUE,
            dataset_id=source.DATASET_ID,
            project_id=source.PROJECT_ID,
            commit_sha=source.COMMIT_SHA,
            repository_path=site_spec.repository_path,
        )
    except source.EfehrReceiptError as exc:
        raise SiteModelOq314IngestionError("trusted site-model target is invalid") from exc

    file_url = source.raw_file_api_url(target)
    request = urllib.request.Request(
        file_url,
        headers={
            "Accept": "text/csv,text/plain;q=0.9,application/octet-stream;q=0.8",
            "User-Agent": "OpenCatastrophe-ESHM20-OQ314-site-ingestion-v1",
        },
        method="GET",
    )
    deadline = monotonic() + source.TOTAL_DEADLINE_SECONDS
    open_response = opener or source._open_fixed
    try:
        with open_response(
            request, timeout=source._remaining(deadline, monotonic)
        ) as response:
            source._validate_exact_response(response, file_url)
            raw = source._read_bounded(
                response,
                deadline=deadline,
                maximum=source.EXPECTED_BYTE_COUNT,
                monotonic=monotonic,
            )
    except source.EfehrAcquisitionError as exc:
        raise SiteModelOq314IngestionError("site-model retrieval failed closed") from exc
    except (OSError, urllib.error.URLError, urllib.error.HTTPError, TimeoutError) as exc:
        raise SiteModelOq314IngestionError(
            f"site-model retrieval failed: {type(exc).__name__}"
        ) from exc

    try:
        observed_sha256 = source._verify_payload_identity(raw)
    except source.Eshm20SiteModelProfileError as exc:
        raise SiteModelOq314IngestionError("site-model receipt identity drifted") from exc
    if observed_sha256 != source.EXPECTED_SHA256:
        raise SiteModelOq314IngestionError("site-model SHA-256 drifted after verification")
    return raw


def _evaluate_site_array(array: Any) -> dict[str, Any]:
    """Evaluate only the bounded OQ3.14 parser/value-domain gate."""
    import numpy

    names = getattr(getattr(array, "dtype", None), "names", None)
    if tuple(names or ()) != EXPECTED_HEADER:
        raise SiteModelOq314IngestionError("OQ3.14 parsed site fields drifted")
    record_count = len(array)
    if type(record_count) is not int or record_count != 94_493:
        raise SiteModelOq314IngestionError("OQ3.14 parsed record count drifted")

    lon = array["lon"]
    lat = array["lat"]
    if lon.dtype != numpy.dtype(numpy.float64) or lat.dtype != numpy.dtype(numpy.float64):
        raise SiteModelOq314IngestionError("OQ3.14 coordinate dtype drifted")
    if not numpy.isfinite(lon).all() or not numpy.isfinite(lat).all():
        raise SiteModelOq314IngestionError("non-finite coordinates rejected")
    if not ((lon >= -180.0) & (lon <= 180.0)).all():
        raise SiteModelOq314IngestionError("longitude outside OQ geographic bounds")
    if not ((lat >= -90.0) & (lat <= 90.0)).all():
        raise SiteModelOq314IngestionError("latitude outside OQ geographic bounds")

    rounded = numpy.empty(record_count, dtype=[("lon", "<f8"), ("lat", "<f8")])
    rounded["lon"] = numpy.round(lon, 5)
    rounded["lat"] = numpy.round(lat, 5)
    unique_coordinate_count = int(len(numpy.unique(rounded)))
    duplicate_coordinate_count = record_count - unique_coordinate_count
    if duplicate_coordinate_count:
        raise SiteModelOq314IngestionError(
            "duplicate coordinates after OQ3.14 five-decimal rounding"
        )

    region = array["region"]
    if region.dtype != numpy.dtype(numpy.uint32):
        raise SiteModelOq314IngestionError("OQ3.14 region dtype drifted")
    region_values = {int(value) for value in numpy.unique(region)}
    if not region_values or not region_values.issubset(SUPPORTED_REGION_CODES):
        raise SiteModelOq314IngestionError("region values exceed supported OQ3.14 domain")

    vs30 = array["vs30"]
    if vs30.dtype != numpy.dtype(numpy.float64):
        raise SiteModelOq314IngestionError("OQ3.14 vs30 dtype drifted")
    if not numpy.isfinite(vs30).all() or not (vs30 > 0.0).all():
        raise SiteModelOq314IngestionError("vs30 must be positive finite")

    measured = array["vs30measured"]
    if measured.dtype != numpy.dtype(bool):
        raise SiteModelOq314IngestionError("OQ3.14 vs30measured bool dtype drifted")

    xvf = array["xvf"]
    if xvf.dtype != numpy.dtype(numpy.float64):
        raise SiteModelOq314IngestionError("OQ3.14 xvf dtype drifted")
    if not numpy.isfinite(xvf).all():
        raise SiteModelOq314IngestionError("xvf must be finite")

    return {
        "record_count": record_count,
        "parsed_header": list(EXPECTED_HEADER),
        "required_mode_a_fields": list(REQUIRED_MODE_A_FIELDS),
        "oq314_site_dtype_parse_verified": True,
        "lon_lat_finite_and_in_bounds": True,
        "coordinate_rounding_decimals": 5,
        "duplicate_coordinate_count_after_rounding": 0,
        "region_uint32_parse_verified": True,
        "region_supported_domain_verified": True,
        "region_distinct_count": len(region_values),
        "vs30_positive_finite_verified": True,
        "vs30measured_bool_parse_verified": True,
        "vs30measured_distinct_count": int(len(numpy.unique(measured))),
        "xvf_finite_verified": True,
    }


def _run_runtime_gate(
    *,
    execution_sha: str,
    runtime_image_id: str,
    base_image_repo_digest: str,
    acquirer: Callable[[], bytes] = _acquire_verified_payload,
) -> dict[str, Any]:
    if type(execution_sha) is not str or not _SHA_RE.fullmatch(execution_sha):
        raise SiteModelOq314IngestionError("invalid execution SHA")
    if type(runtime_image_id) is not str or not _IMAGE_ID_RE.fullmatch(runtime_image_id):
        raise SiteModelOq314IngestionError("invalid OQ3.14 runtime image ID")
    if (
        type(base_image_repo_digest) is not str
        or not _REPO_DIGEST_RE.fullmatch(base_image_repo_digest)
    ):
        raise SiteModelOq314IngestionError("invalid OQ3.14 base image repo digest")

    try:
        from openquake.baselib import hdf5
        from openquake.hazardlib import site
    except Exception as exc:  # pragma: no cover - only exact runtime owns this import
        raise SiteModelOq314IngestionError("OpenQuake 3.14 runtime import failed") from exc

    raw = acquirer()
    if type(raw) is not bytes:
        raise SiteModelOq314IngestionError("site-model acquirer returned non-bytes")
    if len(raw) != source.EXPECTED_BYTE_COUNT:
        raise SiteModelOq314IngestionError("site-model byte count drifted before OQ parse")
    if hashlib.sha256(raw).hexdigest() != source.EXPECTED_SHA256:
        raise SiteModelOq314IngestionError("site-model SHA-256 drifted before OQ parse")

    temp_path: str | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="wb", suffix=".csv", prefix="oc-eshm20-site-", delete=False
        ) as handle:
            handle.write(raw)
            temp_path = handle.name
        del raw
        parsed = hdf5.read_csv(temp_path, site.site_param_dt)
        gate = _evaluate_site_array(parsed)
    except SiteModelOq314IngestionError:
        raise
    except Exception as exc:
        raise SiteModelOq314IngestionError(
            f"OQ3.14 site-model parser rejected exact bytes: {type(exc).__name__}"
        ) from exc
    finally:
        if temp_path is not None:
            try:
                os.remove(temp_path)
            except FileNotFoundError:
                pass

    result = {
        "schema_version": RESULT_SCHEMA_VERSION,
        "action": ACTION,
        "source_issue": CONTROL_ISSUE,
        "dataset_id": DATASET_ID,
        "target_sha": execution_sha,
        "execution_sha": execution_sha,
        "source_identity": {
            "project_id": source.PROJECT_ID,
            "project_path": source.PROJECT_PATH,
            "commit_sha": source.COMMIT_SHA,
            "repository_path": source.REPOSITORY_PATH,
            "byte_count": source.EXPECTED_BYTE_COUNT,
            "sha256": source.EXPECTED_SHA256,
        },
        "runtime": {
            "oq_engine_tag": OQ_ENGINE_TAG,
            "oq_engine_commit": OQ_ENGINE_COMMIT,
            "base_image_repo_digest": base_image_repo_digest,
            "runtime_image_id": runtime_image_id,
            "openblas_num_threads": 1,
        },
        "gate": gate,
        "historical_environment_verified": False,
        "full_site_compatibility_verified": False,
        "crs_authorized": False,
        "coordinate_semantics_authorized": False,
        "site_response_authorized": False,
        "numerical_hazard_agreement_verified": False,
        "reference_run_verified": False,
        "independent_validation_verified": False,
        "external_bytes_persisted": False,
        "raw_rows_returned": False,
        "publication_authorized": False,
        "model_use_authorized": False,
        "status": "pass",
        "failure_class": None,
    }
    _validate_terminal_result(result, execution_sha=execution_sha)
    return result


def _base_result(*, execution_sha: str) -> dict[str, Any]:
    return {
        "schema_version": RESULT_SCHEMA_VERSION,
        "action": ACTION,
        "source_issue": CONTROL_ISSUE,
        "dataset_id": DATASET_ID,
        "target_sha": execution_sha,
        "execution_sha": execution_sha,
        "historical_environment_verified": False,
        "full_site_compatibility_verified": False,
        "crs_authorized": False,
        "coordinate_semantics_authorized": False,
        "site_response_authorized": False,
        "numerical_hazard_agreement_verified": False,
        "reference_run_verified": False,
        "independent_validation_verified": False,
        "external_bytes_persisted": False,
        "raw_rows_returned": False,
        "publication_authorized": False,
        "model_use_authorized": False,
    }


def _blocked_result(*, execution_sha: str) -> dict[str, Any]:
    result = {
        **_base_result(execution_sha=execution_sha),
        "source_identity": None,
        "runtime": None,
        "gate": None,
        "status": "blocked",
        "failure_class": "oq314_site_model_ingestion_failure",
    }
    _validate_terminal_result(result, execution_sha=execution_sha)
    return result


def _validate_terminal_result(result: object, *, execution_sha: str) -> dict[str, Any]:
    base = _base_result(execution_sha=execution_sha)
    expected_fields = set(base) | {
        "source_identity",
        "runtime",
        "gate",
        "status",
        "failure_class",
    }
    if type(result) is not dict or set(result) != expected_fields:
        raise SiteModelOq314IngestionError("trusted OQ3.14 ingestion result fields drifted")
    for field, exact in base.items():
        observed = result.get(field)
        if type(observed) is not type(exact) or observed != exact:
            raise SiteModelOq314IngestionError(f"trusted result drifted at {field}")
    for field in _FALSE_CEILINGS:
        if result[field] is not False:
            raise SiteModelOq314IngestionError(f"authority ceiling widened at {field}")

    if result["status"] == "blocked":
        if (
            result["failure_class"] != "oq314_site_model_ingestion_failure"
            or result["source_identity"] is not None
            or result["runtime"] is not None
            or result["gate"] is not None
        ):
            raise SiteModelOq314IngestionError("blocked result is not safely bounded")
        return result
    if result["status"] != "pass" or result["failure_class"] is not None:
        raise SiteModelOq314IngestionError("result status is invalid")

    identity = result["source_identity"]
    expected_identity = {
        "project_id": source.PROJECT_ID,
        "project_path": source.PROJECT_PATH,
        "commit_sha": source.COMMIT_SHA,
        "repository_path": source.REPOSITORY_PATH,
        "byte_count": source.EXPECTED_BYTE_COUNT,
        "sha256": source.EXPECTED_SHA256,
    }
    if identity != expected_identity:
        raise SiteModelOq314IngestionError("source identity drifted")

    runtime = result["runtime"]
    if type(runtime) is not dict or set(runtime) != {
        "oq_engine_tag",
        "oq_engine_commit",
        "base_image_repo_digest",
        "runtime_image_id",
        "openblas_num_threads",
    }:
        raise SiteModelOq314IngestionError("runtime identity fields drifted")
    if runtime["oq_engine_tag"] != OQ_ENGINE_TAG or runtime["oq_engine_commit"] != OQ_ENGINE_COMMIT:
        raise SiteModelOq314IngestionError("OpenQuake runtime ref drifted")
    if (
        type(runtime["base_image_repo_digest"]) is not str
        or not _REPO_DIGEST_RE.fullmatch(runtime["base_image_repo_digest"])
    ):
        raise SiteModelOq314IngestionError("base image repo digest is invalid")
    if (
        type(runtime["runtime_image_id"]) is not str
        or not _IMAGE_ID_RE.fullmatch(runtime["runtime_image_id"])
    ):
        raise SiteModelOq314IngestionError("runtime image ID is invalid")
    if type(runtime["openblas_num_threads"]) is not int or runtime["openblas_num_threads"] != 1:
        raise SiteModelOq314IngestionError("OpenBLAS thread fence drifted")

    gate = result["gate"]
    if type(gate) is not dict or set(gate) != {
        "record_count",
        "parsed_header",
        "required_mode_a_fields",
        "oq314_site_dtype_parse_verified",
        "lon_lat_finite_and_in_bounds",
        "coordinate_rounding_decimals",
        "duplicate_coordinate_count_after_rounding",
        "region_uint32_parse_verified",
        "region_supported_domain_verified",
        "region_distinct_count",
        "vs30_positive_finite_verified",
        "vs30measured_bool_parse_verified",
        "vs30measured_distinct_count",
        "xvf_finite_verified",
    }:
        raise SiteModelOq314IngestionError("gate fields drifted")
    if gate["record_count"] != 94_493 or type(gate["record_count"]) is not int:
        raise SiteModelOq314IngestionError("gate record count drifted")
    if gate["parsed_header"] != list(EXPECTED_HEADER):
        raise SiteModelOq314IngestionError("gate header drifted")
    if gate["required_mode_a_fields"] != list(REQUIRED_MODE_A_FIELDS):
        raise SiteModelOq314IngestionError("gate required-field set drifted")
    for field in (
        "oq314_site_dtype_parse_verified",
        "lon_lat_finite_and_in_bounds",
        "region_uint32_parse_verified",
        "region_supported_domain_verified",
        "vs30_positive_finite_verified",
        "vs30measured_bool_parse_verified",
        "xvf_finite_verified",
    ):
        if gate[field] is not True:
            raise SiteModelOq314IngestionError(f"gate did not verify {field}")
    if gate["coordinate_rounding_decimals"] != 5 or type(gate["coordinate_rounding_decimals"]) is not int:
        raise SiteModelOq314IngestionError("coordinate rounding contract drifted")
    if gate["duplicate_coordinate_count_after_rounding"] != 0:
        raise SiteModelOq314IngestionError("duplicate-coordinate gate drifted")
    if (
        type(gate["region_distinct_count"]) is not int
        or not 1 <= gate["region_distinct_count"] <= len(SUPPORTED_REGION_CODES)
    ):
        raise SiteModelOq314IngestionError("region distinct count is invalid")
    if (
        type(gate["vs30measured_distinct_count"]) is not int
        or not 1 <= gate["vs30measured_distinct_count"] <= 2
    ):
        raise SiteModelOq314IngestionError("vs30measured distinct count is invalid")
    return result


def _parse_trusted_terminal_result(body: object, *, execution_sha: str) -> bool:
    if type(body) is not str or RESULT_MARKER not in body:
        return False
    if body.count(RESULT_MARKER) != 1:
        raise SiteModelOq314IngestionError("trusted result marker is malformed")
    before, after = body.split(RESULT_MARKER, 1)
    if before.strip() or not after.strip():
        raise SiteModelOq314IngestionError("trusted result envelope is malformed")
    try:
        result = json.loads(
            after.strip(), object_pairs_hook=_pairs, parse_constant=_reject_constant
        )
    except SiteModelOq314IngestionError:
        raise
    except (json.JSONDecodeError, TypeError, ValueError) as exc:
        raise SiteModelOq314IngestionError("trusted result JSON is malformed") from exc
    if type(result) is not dict:
        raise SiteModelOq314IngestionError("trusted result is not an object")
    result_sha = result.get("execution_sha")
    if type(result_sha) is not str or not _SHA_RE.fullmatch(result_sha):
        raise SiteModelOq314IngestionError("trusted result execution SHA is invalid")
    _validate_terminal_result(result, execution_sha=result_sha)
    return result_sha == execution_sha


def has_terminal_result(
    *,
    repository: str,
    token: str,
    execution_sha: str,
    opener: Any | None = None,
    max_pages: int = 20,
) -> bool:
    if type(execution_sha) is not str or not _SHA_RE.fullmatch(execution_sha):
        raise SiteModelOq314IngestionError("invalid execution SHA")
    kwargs: dict[str, Any] = {"issue": CONTROL_ISSUE, "max_pages": max_pages}
    if opener is not None:
        kwargs["opener"] = opener
    try:
        comments = fetch_repository_comments(repository, token, **kwargs)
    except LedgerError as exc:
        raise SiteModelOq314IngestionError("site-ingestion result ledger is incomplete") from exc
    for comment in comments:
        if type(comment) is not dict:
            raise SiteModelOq314IngestionError("result ledger contains a non-object comment")
        user = comment.get("user")
        login = user.get("login") if type(user) is dict else None
        if login != TRUSTED_RESULT_LOGIN:
            continue
        if _parse_trusted_terminal_result(comment.get("body"), execution_sha=execution_sha):
            return True
    return False


def execute(
    *,
    execution_sha: str,
    runtime_image_id: str,
    base_image_repo_digest: str,
    acquirer: Callable[[], bytes] = _acquire_verified_payload,
) -> dict[str, Any]:
    try:
        return _run_runtime_gate(
            execution_sha=execution_sha,
            runtime_image_id=runtime_image_id,
            base_image_repo_digest=base_image_repo_digest,
            acquirer=acquirer,
        )
    except SiteModelOq314IngestionError:
        return _blocked_result(execution_sha=execution_sha)


def _request_body_from_env(name: str) -> str:
    value = os.environ.get(name)
    if value is None:
        raise SiteModelOq314IngestionError(f"missing request environment variable: {name}")
    return value


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--comment-body-env", required=True)
    parser.add_argument("--expected-issue", required=True, type=int)
    parser.add_argument("--execution-sha", required=True)
    parser.add_argument("--runtime-image-id")
    parser.add_argument("--base-image-repo-digest")
    parser.add_argument("--validate-request-only", action="store_true")
    parser.add_argument("--output")
    args = parser.parse_args(argv)

    body = _request_body_from_env(args.comment_body_env)
    validate_request(
        body,
        expected_issue=args.expected_issue,
        execution_sha=args.execution_sha,
    )
    if args.validate_request_only:
        if args.runtime_image_id or args.base_image_repo_digest or args.output:
            raise SiteModelOq314IngestionError("validation-only invocation widened")
        return 0
    if not args.runtime_image_id or not args.base_image_repo_digest or not args.output:
        raise SiteModelOq314IngestionError("runtime invocation is incomplete")
    result = execute(
        execution_sha=args.execution_sha,
        runtime_image_id=args.runtime_image_id,
        base_image_repo_digest=args.base_image_repo_digest,
    )
    Path(args.output).write_text(
        json.dumps(result, sort_keys=True, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
