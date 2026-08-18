# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Trusted-main wrapper for the fixed Kosovo exposure/site spatial interop profile."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import Any

if __package__ in (None, ""):  # pragma: no cover
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts import profile_eq1_kosovo_spatial_interop as profile
from scripts.prepare_agent_action_result import LedgerError, fetch_repository_comments

REQUEST_MARKER = "<!-- oc-eq1-kosovo-spatial-interop-request-v1 -->"
RESULT_MARKER = "<!-- oc-eq1-kosovo-spatial-interop-result-v1 -->"
REQUEST_SCHEMA_VERSION = "oc-eq1-kosovo-spatial-interop-request-v1"
RESULT_SCHEMA_VERSION = "oc-eq1-kosovo-spatial-interop-result-v1"
SOURCE_ISSUE = 287
TRUSTED_RESULT_LOGIN = "github-actions[bot]"
MAX_LEDGER_PAGES = 20
MAX_RESULT_UTF8_BYTES = 96_000
BLOCKED_FAILURE_CLASS = "spatial_interop_profile_failure"

_SHA_RE = re.compile(r"^[0-9a-f]{40}$")
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_DECIMAL_RE = re.compile(r"^(?:0|[1-9][0-9]*)(?:\.[0-9]{1,9})?$")
_REQUESTER_RE = re.compile(r"^[A-Za-z0-9_.:@/+ -]{1,96}$")
_REQUEST_FIELDS = {"schema_version", "issue", "target_sha", "requester"}
_RESULT_FIELDS = {
    "schema_version",
    "source_issue",
    "target_sha",
    "execution_sha",
    "status",
    "failure_class",
    "profile",
    "external_bytes_persisted",
    "source_crs_datum_epsg_verified",
    "reprojection_authorized",
    "geographic_cross_source_equivalence_authorized",
    "publication_authorized",
    "model_use_authorized",
}
_PROFILE_FIELDS = {
    "schema_version",
    "source_issue",
    "reference_runtime",
    "exposure_identity",
    "site_identity",
    "profile",
    "reference_runtime_coordinate_role_verified",
    "source_crs_datum_epsg_verified",
    "reprojection_performed",
    "reprojection_authorized",
    "geographic_cross_source_equivalence_authorized",
    "raw_provider_coordinates_returned",
    "external_bytes_persisted",
    "publication_authorized",
    "model_use_authorized",
}
_INNER_FIELDS = {
    "exposure_record_count",
    "distinct_exposure_location_count",
    "site_record_count",
    "distinct_site_location_count",
    "nearest_site_distance_km",
    "threshold_diagnostics",
    "openquake_default_asset_hazard_distance_km",
    "default_distance_association",
    "raw_coordinates_returned",
}
_DISTANCE_FIELDS = {"minimum", "maximum"}
_THRESHOLD_FIELDS = {
    "threshold_km",
    "associated_exposure_record_count",
    "discarded_exposure_record_count",
    "all_exposure_records_associated",
}
_EXPECTED_THRESHOLDS = ("1", "5", "10", "15", "20", "25", "50")
_EXPECTED_RUNTIME_CONTRACT = (
    "when the supplied site-model mesh is the selected hazard mesh, exposure "
    "asset locations are associated to nearest hazard sites by zero-depth "
    "spherical Cartesian distance"
)
_EXPECTED_MESH_PRECONDITION = (
    "no higher-precedence explicit sites, sites input, hazard-curves mesh, "
    "or region_grid_spacing path overrides the supplied site-model mesh"
)

_PROFILE = profile.acquire_and_profile_kosovo_spatial_interop
_FETCH_COMMENTS = fetch_repository_comments


class KosovoSpatialInteropExecutionError(RuntimeError):
    """Fail-closed error for the dedicated trusted-main spatial action."""


def _pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise KosovoSpatialInteropExecutionError("duplicate JSON key")
        result[key] = value
    return result


def _reject_constant(value: str) -> Any:
    raise KosovoSpatialInteropExecutionError(f"non-finite JSON constant: {value}")


def validate_request(body: object, *, expected_issue: int, execution_sha: str) -> dict[str, Any]:
    if type(expected_issue) is not int or expected_issue != SOURCE_ISSUE:
        raise KosovoSpatialInteropExecutionError("wrong spatial-interoperability issue")
    if type(execution_sha) is not str or _SHA_RE.fullmatch(execution_sha) is None:
        raise KosovoSpatialInteropExecutionError("invalid execution SHA")
    if type(body) is not str or body.count(REQUEST_MARKER) != 1:
        raise KosovoSpatialInteropExecutionError("invalid spatial-interoperability request marker")
    before, after = body.split(REQUEST_MARKER, 1)
    if before.strip() or not after.strip():
        raise KosovoSpatialInteropExecutionError("spatial-interoperability request envelope is not canonical")
    try:
        request = json.loads(after.strip(), object_pairs_hook=_pairs, parse_constant=_reject_constant)
    except KosovoSpatialInteropExecutionError:
        raise
    except (json.JSONDecodeError, TypeError, ValueError) as exc:
        raise KosovoSpatialInteropExecutionError("invalid spatial-interoperability request JSON") from exc
    if type(request) is not dict or set(request) != _REQUEST_FIELDS:
        raise KosovoSpatialInteropExecutionError("spatial-interoperability request fields drifted")
    if request["schema_version"] != REQUEST_SCHEMA_VERSION:
        raise KosovoSpatialInteropExecutionError("spatial-interoperability request schema drifted")
    if type(request["issue"]) is not int or request["issue"] != SOURCE_ISSUE:
        raise KosovoSpatialInteropExecutionError("spatial-interoperability request issue drifted")
    if request["target_sha"] != execution_sha:
        raise KosovoSpatialInteropExecutionError("spatial-interoperability request target is not trusted main")
    requester = request["requester"]
    if type(requester) is not str or requester != requester.strip() or _REQUESTER_RE.fullmatch(requester) is None:
        raise KosovoSpatialInteropExecutionError("invalid requester identity")
    return request


def _exact(value: object, expected: object, *, field: str) -> None:
    if type(value) is not type(expected) or value != expected:
        raise KosovoSpatialInteropExecutionError(f"spatial-interoperability profile drifted at {field}")


def _nonnegative_int(value: object, *, field: str, maximum: int) -> int:
    if type(value) is not int or isinstance(value, bool) or not 0 <= value <= maximum:
        raise KosovoSpatialInteropExecutionError(f"{field} is outside bounded policy")
    return value


def _positive_int(value: object, *, field: str, maximum: int) -> int:
    observed = _nonnegative_int(value, field=field, maximum=maximum)
    if observed == 0:
        raise KosovoSpatialInteropExecutionError(f"{field} must be positive")
    return observed


def _decimal(value: object, *, field: str) -> str:
    if type(value) is not str or _DECIMAL_RE.fullmatch(value) is None:
        raise KosovoSpatialInteropExecutionError(f"{field} is not canonical decimal text")
    return value


def _validate_identity(value: object, *, exposure: bool) -> dict[str, Any]:
    if type(value) is not dict or set(value) != {
        "dataset_id",
        "project_id",
        "project_path",
        "commit_sha",
        "repository_path",
        "byte_count",
        "sha256",
    }:
        raise KosovoSpatialInteropExecutionError("spatial input identity shape drifted")
    if exposure:
        expected = {
            "dataset_id": profile._CANONICAL_EXPOSURE_DATASET_ID,
            "project_id": profile._CANONICAL_EXPOSURE_PROJECT_ID,
            "project_path": profile._CANONICAL_EXPOSURE_PROJECT_PATH,
            "commit_sha": profile._CANONICAL_EXPOSURE_COMMIT_SHA,
            "repository_path": profile._CANONICAL_EXPOSURE_REPOSITORY_PATH,
            "byte_count": profile._CANONICAL_EXPOSURE_BYTE_COUNT,
            "sha256": profile._CANONICAL_EXPOSURE_SHA256,
        }
    else:
        expected = {
            "dataset_id": profile._CANONICAL_SITE_DATASET_ID,
            "project_id": profile._CANONICAL_SITE_PROJECT_ID,
            "project_path": profile._CANONICAL_SITE_PROJECT_PATH,
            "commit_sha": profile._CANONICAL_SITE_COMMIT_SHA,
            "repository_path": profile._CANONICAL_SITE_REPOSITORY_PATH,
            "byte_count": profile._CANONICAL_SITE_BYTE_COUNT,
            "sha256": profile._CANONICAL_SITE_SHA256,
        }
    for field, expected_value in expected.items():
        _exact(value[field], expected_value, field=f"{'exposure' if exposure else 'site'} identity {field}")
    return value


def _validate_threshold(value: object, *, exposure_count: int, expected_threshold: str) -> dict[str, Any]:
    if type(value) is not dict or set(value) != _THRESHOLD_FIELDS:
        raise KosovoSpatialInteropExecutionError("threshold diagnostic shape drifted")
    _exact(value["threshold_km"], expected_threshold, field="threshold_km")
    associated = _nonnegative_int(
        value["associated_exposure_record_count"],
        field="associated exposure count",
        maximum=exposure_count,
    )
    discarded = _nonnegative_int(
        value["discarded_exposure_record_count"],
        field="discarded exposure count",
        maximum=exposure_count,
    )
    if associated + discarded != exposure_count:
        raise KosovoSpatialInteropExecutionError("threshold association counts do not reconcile")
    all_associated = value["all_exposure_records_associated"]
    if type(all_associated) is not bool or all_associated != (associated == exposure_count):
        raise KosovoSpatialInteropExecutionError("threshold all-associated flag drifted")
    return value


def validate_profile(value: object) -> dict[str, Any]:
    if type(value) is not dict or set(value) != _PROFILE_FIELDS:
        raise KosovoSpatialInteropExecutionError("spatial-interoperability profile fields drifted")
    exact = (
        (value["schema_version"], profile.SCHEMA_VERSION, "schema_version"),
        (value["source_issue"], SOURCE_ISSUE, "source_issue"),
        (value["reference_runtime_coordinate_role_verified"], True, "reference_runtime_coordinate_role_verified"),
        (value["source_crs_datum_epsg_verified"], False, "source_crs_datum_epsg_verified"),
        (value["reprojection_performed"], False, "reprojection_performed"),
        (value["reprojection_authorized"], False, "reprojection_authorized"),
        (value["geographic_cross_source_equivalence_authorized"], False, "geographic_cross_source_equivalence_authorized"),
        (value["raw_provider_coordinates_returned"], False, "raw_provider_coordinates_returned"),
        (value["external_bytes_persisted"], False, "external_bytes_persisted"),
        (value["publication_authorized"], False, "publication_authorized"),
        (value["model_use_authorized"], False, "model_use_authorized"),
    )
    for observed, expected, field in exact:
        _exact(observed, expected, field=field)

    runtime = value["reference_runtime"]
    if type(runtime) is not dict or set(runtime) != {
        "repository", "tag", "commit_sha", "association_contract", "hazard_mesh_precondition"
    }:
        raise KosovoSpatialInteropExecutionError("reference runtime shape drifted")
    for field, expected in (
        ("repository", "gem/oq-engine"),
        ("tag", profile.OPENQUAKE_REFERENCE_TAG),
        ("commit_sha", profile.OPENQUAKE_REFERENCE_COMMIT),
        ("association_contract", _EXPECTED_RUNTIME_CONTRACT),
        ("hazard_mesh_precondition", _EXPECTED_MESH_PRECONDITION),
    ):
        _exact(runtime[field], expected, field=f"reference runtime {field}")

    _validate_identity(value["exposure_identity"], exposure=True)
    _validate_identity(value["site_identity"], exposure=False)

    inner = value["profile"]
    if type(inner) is not dict or set(inner) != _INNER_FIELDS:
        raise KosovoSpatialInteropExecutionError("spatial aggregate profile shape drifted")
    exposure_count = _positive_int(
        inner["exposure_record_count"],
        field="exposure record count",
        maximum=profile.MAX_EXPOSURE_RECORDS,
    )
    distinct_exposure = _positive_int(
        inner["distinct_exposure_location_count"],
        field="distinct exposure location count",
        maximum=exposure_count,
    )
    if distinct_exposure > exposure_count:
        raise KosovoSpatialInteropExecutionError("distinct exposure count exceeds record count")
    site_count = _positive_int(
        inner["site_record_count"], field="site record count", maximum=profile.MAX_SITE_RECORDS
    )
    distinct_site = _positive_int(
        inner["distinct_site_location_count"], field="distinct site location count", maximum=site_count
    )
    if distinct_site > site_count:
        raise KosovoSpatialInteropExecutionError("distinct site count exceeds record count")

    nearest = inner["nearest_site_distance_km"]
    if type(nearest) is not dict or set(nearest) != _DISTANCE_FIELDS:
        raise KosovoSpatialInteropExecutionError("nearest-site distance shape drifted")
    minimum = float(_decimal(nearest["minimum"], field="minimum nearest-site distance"))
    maximum = float(_decimal(nearest["maximum"], field="maximum nearest-site distance"))
    if minimum < 0 or maximum < minimum:
        raise KosovoSpatialInteropExecutionError("nearest-site distance range is invalid")

    diagnostics = inner["threshold_diagnostics"]
    if type(diagnostics) is not list or len(diagnostics) != len(_EXPECTED_THRESHOLDS):
        raise KosovoSpatialInteropExecutionError("threshold diagnostics length drifted")
    validated = [
        _validate_threshold(item, exposure_count=exposure_count, expected_threshold=threshold)
        for item, threshold in zip(diagnostics, _EXPECTED_THRESHOLDS)
    ]
    associated_counts = [item["associated_exposure_record_count"] for item in validated]
    if associated_counts != sorted(associated_counts):
        raise KosovoSpatialInteropExecutionError("threshold association counts are not monotonic")

    _exact(
        inner["openquake_default_asset_hazard_distance_km"],
        "15",
        field="OpenQuake default asset-hazard distance",
    )
    default = _validate_threshold(
        inner["default_distance_association"],
        exposure_count=exposure_count,
        expected_threshold="15",
    )
    if default != validated[3]:
        raise KosovoSpatialInteropExecutionError("default distance diagnostic disagrees with threshold table")
    _exact(inner["raw_coordinates_returned"], False, field="raw_coordinates_returned")
    return value


def _base_result(*, execution_sha: str) -> dict[str, Any]:
    return {
        "schema_version": RESULT_SCHEMA_VERSION,
        "source_issue": SOURCE_ISSUE,
        "target_sha": execution_sha,
        "execution_sha": execution_sha,
        "external_bytes_persisted": False,
        "source_crs_datum_epsg_verified": False,
        "reprojection_authorized": False,
        "geographic_cross_source_equivalence_authorized": False,
        "publication_authorized": False,
        "model_use_authorized": False,
    }


def _parse_result(body: object) -> dict[str, Any] | None:
    if type(body) is not str or RESULT_MARKER not in body:
        return None
    if body.count(RESULT_MARKER) != 1:
        raise KosovoSpatialInteropExecutionError("spatial-interoperability result marker is malformed")
    before, after = body.split(RESULT_MARKER, 1)
    if before.strip() or not after.strip():
        raise KosovoSpatialInteropExecutionError("spatial-interoperability result envelope is malformed")
    try:
        result = json.loads(after.strip(), object_pairs_hook=_pairs, parse_constant=_reject_constant)
    except KosovoSpatialInteropExecutionError:
        raise
    except (json.JSONDecodeError, TypeError, ValueError) as exc:
        raise KosovoSpatialInteropExecutionError("spatial-interoperability result JSON is malformed") from exc
    if type(result) is not dict or set(result) != _RESULT_FIELDS:
        raise KosovoSpatialInteropExecutionError("spatial-interoperability result fields drifted")
    if result["schema_version"] != RESULT_SCHEMA_VERSION:
        raise KosovoSpatialInteropExecutionError("spatial-interoperability result schema drifted")
    return result


def _terminal_execution_sha(body: object) -> str | None:
    result = _parse_result(body)
    if result is None:
        return None
    target_sha = result.get("target_sha")
    execution_sha = result.get("execution_sha")
    if type(result.get("source_issue")) is not int or result["source_issue"] != SOURCE_ISSUE:
        raise KosovoSpatialInteropExecutionError("spatial-interoperability result issue drifted")
    if type(target_sha) is not str or _SHA_RE.fullmatch(target_sha) is None:
        raise KosovoSpatialInteropExecutionError("spatial-interoperability result target SHA is invalid")
    if type(execution_sha) is not str or _SHA_RE.fullmatch(execution_sha) is None:
        raise KosovoSpatialInteropExecutionError("spatial-interoperability result execution SHA is invalid")
    if target_sha != execution_sha:
        raise KosovoSpatialInteropExecutionError("spatial-interoperability result target/execution SHA mismatch")
    return execution_sha


def parse_terminal_result(body: object, *, execution_sha: str) -> bool:
    result = _parse_result(body)
    if result is None:
        return False
    for field, expected in _base_result(execution_sha=execution_sha).items():
        observed = result[field]
        if type(observed) is not type(expected) or observed != expected:
            raise KosovoSpatialInteropExecutionError(f"spatial-interoperability result drifted at {field}")
    if result["status"] == "pass":
        if result["failure_class"] is not None:
            raise KosovoSpatialInteropExecutionError("spatial-interoperability PASS carries failure class")
        validate_profile(result["profile"])
        return True
    if result["status"] == "blocked":
        if result["failure_class"] != BLOCKED_FAILURE_CLASS or result["profile"] is not None:
            raise KosovoSpatialInteropExecutionError("spatial-interoperability blocked result widened evidence")
        return True
    if result["status"] == "duplicate":
        if result["failure_class"] is not None or result["profile"] is not None:
            raise KosovoSpatialInteropExecutionError("spatial-interoperability duplicate result carries evidence")
        return True
    raise KosovoSpatialInteropExecutionError("spatial-interoperability result has non-terminal status")


def has_terminal_result(*, repository: str, token: str, execution_sha: str) -> bool:
    if type(execution_sha) is not str or _SHA_RE.fullmatch(execution_sha) is None:
        raise KosovoSpatialInteropExecutionError("invalid execution SHA")
    try:
        comments = _FETCH_COMMENTS(repository, token, issue=SOURCE_ISSUE, max_pages=MAX_LEDGER_PAGES)
    except LedgerError as exc:
        raise KosovoSpatialInteropExecutionError("spatial-interoperability result ledger is incomplete") from exc
    for comment in comments:
        if type(comment) is not dict:
            raise KosovoSpatialInteropExecutionError("spatial-interoperability ledger contains non-object")
        user = comment.get("user")
        login = user.get("login") if type(user) is dict else None
        if login != TRUSTED_RESULT_LOGIN:
            continue
        body = comment.get("body")
        own_execution_sha = _terminal_execution_sha(body)
        if own_execution_sha is None:
            continue
        terminal = parse_terminal_result(body, execution_sha=own_execution_sha)
        if own_execution_sha == execution_sha and terminal:
            return True
    return False


def execute_profile(*, repository: str, token: str, execution_sha: str) -> dict[str, Any]:
    if profile.acquire_and_profile_kosovo_spatial_interop is not _PROFILE or fetch_repository_comments is not _FETCH_COMMENTS:
        raise KosovoSpatialInteropExecutionError("trusted spatial-interoperability execution authority drifted")
    if has_terminal_result(repository=repository, token=token, execution_sha=execution_sha):
        return {
            **_base_result(execution_sha=execution_sha),
            "status": "duplicate",
            "failure_class": None,
            "profile": None,
        }
    try:
        spatial_profile = _PROFILE()
        validate_profile(spatial_profile)
        result = {
            **_base_result(execution_sha=execution_sha),
            "status": "pass",
            "failure_class": None,
            "profile": spatial_profile,
        }
    except profile.SpatialInteropProfileError:
        result = {
            **_base_result(execution_sha=execution_sha),
            "status": "blocked",
            "failure_class": BLOCKED_FAILURE_CLASS,
            "profile": None,
        }
    encoded = json.dumps(result, sort_keys=True, separators=(",", ":")).encode("utf-8")
    if len(encoded) > MAX_RESULT_UTF8_BYTES:
        raise KosovoSpatialInteropExecutionError("spatial-interoperability result exceeds publication limit")
    parse_terminal_result(RESULT_MARKER + "\n" + encoded.decode("utf-8"), execution_sha=execution_sha)
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--comment-body-env", required=True)
    parser.add_argument("--expected-issue", type=int, required=True)
    parser.add_argument("--execution-sha", required=True)
    parser.add_argument("--repository")
    parser.add_argument("--token-env")
    parser.add_argument("--output")
    parser.add_argument("--validate-request-only", action="store_true")
    args = parser.parse_args(argv)

    validate_request(
        os.environ.get(args.comment_body_env),
        expected_issue=args.expected_issue,
        execution_sha=args.execution_sha,
    )
    if args.validate_request_only:
        return 0
    if not args.repository or not args.token_env or not args.output:
        parser.error("--repository, --token-env and --output are required for execution")
    token = os.environ.get(args.token_env)
    if not token:
        raise KosovoSpatialInteropExecutionError("GitHub ledger token is absent")
    result = execute_profile(repository=args.repository, token=token, execution_sha=args.execution_sha)
    Path(args.output).write_text(
        json.dumps(result, sort_keys=True, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
