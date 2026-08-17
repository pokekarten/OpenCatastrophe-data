# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Trusted-main bounded domain evaluation for the exact ESRM20 Kosovo site model.

The action reuses the already-reviewed fixed EFEHR transport primitives from the
Kosovo structure-profile lane. Provider bytes remain memory-only, are fenced to
the exact receipted byte count and SHA-256, and are then passed to the merged
count-only static-domain classifier. This is not OpenQuake runtime acceptance or
scientific site-model sufficiency.
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
from typing import Any, Callable

from scripts import acquire_efehr_kosovo_site_profile as _transport
from scripts import validate_esrm20_kosovo_site_parameter_domains as _domain
from scripts.prepare_agent_action_result import LedgerError, fetch_repository_comments

REQUEST_MARKER = "<!-- oc-eq1-esrm20-kosovo-site-domain-profile-request-v1 -->"
RESULT_MARKER = "<!-- oc-eq1-esrm20-kosovo-site-domain-profile-result-v1 -->"
REQUEST_SCHEMA_VERSION = "oc-esrm20-kosovo-site-domain-profile-request-v1"
RESULT_SCHEMA_VERSION = "oc-esrm20-kosovo-site-domain-profile-result-v1"
ACTION = "esrm20_kosovo_site_parameter_static_domain_profile"
CONTROL_ISSUE = 291
SITE_PROFILE_ISSUE = 459
SOURCE_SCIENCE_ISSUE = 284
RECEIPT_ISSUE = 342
DATASET_ID = "efehr.esrm20.risk-inputs.v1.0"
PROJECT_ID = 269
PROJECT_PATH = "efehr/esrm20"
COMMIT_SHA = "05f83bbc9df81d02ee8ddb1801d9d781355ce783"
REPOSITORY_PATH = "Vs30/Site_model_Kosovo.xml"
RECEIPT_COMMENT_ID = 5308044390
EXPECTED_BYTE_COUNT = 5_891
EXPECTED_SHA256 = "746cf75d91507da8b55a9476c61bb5d884eed42c6268a36b1179f432e8850edd"
EXPECTED_SITE_COUNT = 37
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
_CANONICAL_OPEN_FIXED = _transport._CANONICAL_OPEN_FIXED
_CANONICAL_MONOTONIC = _transport._CANONICAL_MONOTONIC
_CANONICAL_DOMAIN_PROFILER = _domain.profile_verified_kosovo_site_parameter_domains


class SiteDomainActionError(RuntimeError):
    """Fail-closed trusted site-domain action error."""


class SiteDomainAcquisitionError(SiteDomainActionError):
    """Exact provider object could not be acquired and verified."""


class SiteDomainContentError(SiteDomainActionError):
    """Exact provider bytes failed the reviewed bounded domain classifier."""


def _pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise SiteDomainActionError("duplicate JSON key")
        result[key] = value
    return result


def _reject_constant(value: str) -> Any:
    raise SiteDomainActionError(f"non-finite JSON constant: {value}")


def _require_contract() -> None:
    exact = (
        (_transport._CANONICAL_SOURCE_ISSUE, CONTROL_ISSUE, "transport content issue"),
        (_transport._CANONICAL_SOURCE_SCIENCE_ISSUE, SOURCE_SCIENCE_ISSUE, "science issue"),
        (_transport._CANONICAL_DATASET_ID, DATASET_ID, "dataset"),
        (_transport._CANONICAL_PROJECT_ID, PROJECT_ID, "project id"),
        (_transport._CANONICAL_PROJECT_PATH, PROJECT_PATH, "project path"),
        (_transport._CANONICAL_COMMIT_SHA, COMMIT_SHA, "commit"),
        (_transport._CANONICAL_REPOSITORY_PATH, REPOSITORY_PATH, "repository path"),
        (_transport._CANONICAL_RECEIPT_COMMENT_ID, RECEIPT_COMMENT_ID, "receipt comment"),
        (_transport._CANONICAL_BYTE_COUNT, EXPECTED_BYTE_COUNT, "byte count"),
        (_transport._CANONICAL_SHA256, EXPECTED_SHA256, "SHA-256"),
        (_domain.SOURCE_ISSUE, CONTROL_ISSUE, "domain source issue"),
        (_domain.SITE_PROFILE_ISSUE, SITE_PROFILE_ISSUE, "site-profile issue"),
        (_domain.EXPECTED_SITE_COUNT, EXPECTED_SITE_COUNT, "site count"),
        (_domain.OPENQUAKE_COMMIT, "9f044c93d72846421a8faa90ebf0a6afacdf3c20", "OpenQuake commit"),
    )
    for observed, expected, label in exact:
        if type(observed) is not type(expected) or observed != expected:
            raise SiteDomainActionError(f"trusted Kosovo site-domain {label} drifted")


def _require_production_identity() -> None:
    _require_contract()
    if _transport._open_fixed is not _CANONICAL_OPEN_FIXED:
        raise SiteDomainActionError("trusted Kosovo site-domain transport identity drifted")
    if time.monotonic is not _CANONICAL_MONOTONIC:
        raise SiteDomainActionError("trusted Kosovo site-domain monotonic clock drifted")
    if _domain.profile_verified_kosovo_site_parameter_domains is not _CANONICAL_DOMAIN_PROFILER:
        raise SiteDomainActionError("trusted Kosovo site-domain profiler identity drifted")


def validate_request(body: object, *, expected_issue: int, execution_sha: str) -> dict[str, Any]:
    if type(expected_issue) is not int or expected_issue != CONTROL_ISSUE:
        raise SiteDomainActionError("wrong runtime issue")
    if type(execution_sha) is not str or _SHA_RE.fullmatch(execution_sha) is None:
        raise SiteDomainActionError("invalid execution SHA")
    if type(body) is not str or body.count(REQUEST_MARKER) != 1:
        raise SiteDomainActionError("invalid site-domain request marker")
    before, after = body.split(REQUEST_MARKER, 1)
    if before.strip() or not after.strip():
        raise SiteDomainActionError("site-domain request envelope is not canonical")
    try:
        request = json.loads(after.strip(), object_pairs_hook=_pairs, parse_constant=_reject_constant)
    except SiteDomainActionError:
        raise
    except (json.JSONDecodeError, TypeError, ValueError) as exc:
        raise SiteDomainActionError("invalid site-domain request JSON") from exc
    if type(request) is not dict or set(request) != _REQUEST_FIELDS:
        raise SiteDomainActionError("site-domain request fields drifted")
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
            raise SiteDomainActionError(f"site-domain request {field} drifted")
    requester = request["requester"]
    if (
        type(requester) is not str
        or requester != requester.strip()
        or _SAFE_REQUESTER_RE.fullmatch(requester) is None
    ):
        raise SiteDomainActionError("invalid requester identity")
    return request


def _bounded_count(value: object, *, label: str) -> int:
    if type(value) is not int or isinstance(value, bool) or not 0 <= value <= EXPECTED_SITE_COUNT:
        raise SiteDomainActionError(f"site-domain {label} is outside bounded policy")
    return value


def _validate_common_counts(row: object, *, expected_keys: set[str], label: str) -> dict[str, Any]:
    if type(row) is not dict or set(row) != expected_keys:
        raise SiteDomainActionError(f"site-domain {label} fields drifted")
    occurrence = _bounded_count(row.get("occurrence_count"), label=f"{label}.occurrence_count")
    if occurrence != EXPECTED_SITE_COUNT:
        raise SiteDomainActionError(f"site-domain {label} occurrence count drifted")
    matches = _bounded_count(row.get("static_domain_match_count"), label=f"{label}.match_count")
    rejects = _bounded_count(row.get("static_domain_reject_count"), label=f"{label}.reject_count")
    if matches + rejects != EXPECTED_SITE_COUNT:
        raise SiteDomainActionError(f"site-domain {label} match/reject partition drifted")
    return row


def _validate_domain_payload(payload: object) -> dict[str, Any]:
    outer_fields = {
        "schema_version",
        "source_issue",
        "site_profile_issue",
        "site_structure_result_comment_id",
        "required_parameter_handoff_comment_id",
        "xvf_semantics_comment_id",
        "site_identity",
        "domain_profile",
        "external_bytes_persisted",
        "publication_authorized",
        "model_use_authorized",
    }
    if type(payload) is not dict or set(payload) != outer_fields:
        raise SiteDomainActionError("site-domain payload fields drifted")
    outer_exact = (
        ("schema_version", _domain.SCHEMA_VERSION),
        ("source_issue", CONTROL_ISSUE),
        ("site_profile_issue", SITE_PROFILE_ISSUE),
        ("site_structure_result_comment_id", _domain.SITE_STRUCTURE_RESULT_COMMENT_ID),
        ("required_parameter_handoff_comment_id", _domain.REQUIRED_PARAMETER_HANDOFF_COMMENT_ID),
        ("xvf_semantics_comment_id", _domain.XVF_SEMANTICS_COMMENT_ID),
        ("external_bytes_persisted", False),
        ("publication_authorized", False),
        ("model_use_authorized", False),
    )
    for field, expected in outer_exact:
        observed = payload.get(field)
        if type(observed) is not type(expected) or observed != expected:
            raise SiteDomainActionError(f"site-domain payload drifted at {field}")

    identity = payload.get("site_identity")
    expected_identity = {
        "project_id": PROJECT_ID,
        "project_path": PROJECT_PATH,
        "commit_sha": COMMIT_SHA,
        "repository_path": REPOSITORY_PATH,
        "byte_count": EXPECTED_BYTE_COUNT,
        "sha256": EXPECTED_SHA256,
        "receipt_comment_id": RECEIPT_COMMENT_ID,
    }
    if identity != expected_identity:
        raise SiteDomainActionError("site-domain payload identity drifted")

    profile = payload.get("domain_profile")
    profile_fields = {
        "schema_version",
        "openquake_reference",
        "required_site_parameter_names",
        "site_count",
        "parameter_domains",
        "static_domain_reject_total",
        "static_domain_classification_complete",
        "raw_xml_returned",
        "raw_attribute_values_returned",
        "raw_site_rows_returned",
        "openquake_runtime_value_acceptance_verified",
        "crs_coordinate_semantics_verified",
        "missingness_semantics_verified",
        "gsim_site_parameter_sufficiency_verified",
        "site_adjusted_reference_authorized",
        "publication_authorized",
        "model_use_authorized",
    }
    if type(profile) is not dict or set(profile) != profile_fields:
        raise SiteDomainActionError("site-domain profile fields drifted")
    if profile.get("schema_version") != _domain.SCHEMA_VERSION:
        raise SiteDomainActionError("site-domain profile schema drifted")
    if profile.get("openquake_reference") != {
        "tag": _domain.OPENQUAKE_TAG,
        "commit": _domain.OPENQUAKE_COMMIT,
    }:
        raise SiteDomainActionError("site-domain OpenQuake reference drifted")
    if profile.get("required_site_parameter_names") != list(_domain.REQUIRED_PARAMETERS):
        raise SiteDomainActionError("site-domain required parameter names drifted")
    if profile.get("site_count") != EXPECTED_SITE_COUNT:
        raise SiteDomainActionError("site-domain site count drifted")
    for field in (
        "raw_xml_returned",
        "raw_attribute_values_returned",
        "raw_site_rows_returned",
        "openquake_runtime_value_acceptance_verified",
        "crs_coordinate_semantics_verified",
        "missingness_semantics_verified",
        "gsim_site_parameter_sufficiency_verified",
        "site_adjusted_reference_authorized",
        "publication_authorized",
        "model_use_authorized",
    ):
        if profile.get(field) is not False:
            raise SiteDomainActionError(f"site-domain authority widened at {field}")
    if profile.get("static_domain_classification_complete") is not True:
        raise SiteDomainActionError("site-domain classification is not complete")

    domains = profile.get("parameter_domains")
    if type(domains) is not dict or set(domains) != set(_domain.REQUIRED_PARAMETERS):
        raise SiteDomainActionError("site-domain parameter inventory drifted")

    vs30 = _validate_common_counts(
        domains.get("vs30"),
        expected_keys={
            "occurrence_count", "finite_decimal_count", "static_domain_match_count",
            "static_domain_reject_count", "positive_finite_count", "static_contract",
        },
        label="vs30",
    )
    if vs30.get("static_contract") != "finite_decimal_and_gt_zero":
        raise SiteDomainActionError("site-domain vs30 contract drifted")
    finite = _bounded_count(vs30.get("finite_decimal_count"), label="vs30.finite_decimal_count")
    positive = _bounded_count(vs30.get("positive_finite_count"), label="vs30.positive_finite_count")
    if positive != vs30["static_domain_match_count"] or positive > finite:
        raise SiteDomainActionError("site-domain vs30 count relationship drifted")

    xvf = _validate_common_counts(
        domains.get("xvf"),
        expected_keys={
            "occurrence_count", "finite_decimal_count", "static_domain_match_count",
            "static_domain_reject_count", "static_contract", "branch_specific_semantics_required",
        },
        label="xvf",
    )
    if (
        xvf.get("static_contract") != "finite_decimal_only"
        or xvf.get("branch_specific_semantics_required") is not True
    ):
        raise SiteDomainActionError("site-domain xvf semantics drifted")
    if _bounded_count(xvf.get("finite_decimal_count"), label="xvf.finite_decimal_count") != xvf["static_domain_match_count"]:
        raise SiteDomainActionError("site-domain xvf count relationship drifted")

    region = _validate_common_counts(
        domains.get("region"),
        expected_keys={
            "occurrence_count", "finite_decimal_count", "static_domain_match_count",
            "static_domain_reject_count", "integral_numeric_count", "static_contract",
            "inclusive_min", "inclusive_max",
        },
        label="region",
    )
    if (
        region.get("static_contract") != "integral_numeric_inclusive_0_to_5"
        or region.get("inclusive_min") != _domain.REGION_MIN
        or region.get("inclusive_max") != _domain.REGION_MAX
    ):
        raise SiteDomainActionError("site-domain region contract drifted")
    region_finite = _bounded_count(region.get("finite_decimal_count"), label="region.finite_decimal_count")
    integral = _bounded_count(region.get("integral_numeric_count"), label="region.integral_numeric_count")
    if not region["static_domain_match_count"] <= integral <= region_finite:
        raise SiteDomainActionError("site-domain region count relationship drifted")

    slope = _validate_common_counts(
        domains.get("slope"),
        expected_keys={
            "occurrence_count", "finite_decimal_count", "static_domain_match_count",
            "static_domain_reject_count", "below_clamp_floor_count",
            "within_clamp_interval_count", "above_clamp_ceiling_count", "static_contract",
            "clamp_floor", "clamp_ceiling",
        },
        label="slope",
    )
    if (
        slope.get("static_contract") != "finite_decimal_with_model_clamping"
        or slope.get("clamp_floor") != str(_domain.SLOPE_CLAMP_FLOOR)
        or slope.get("clamp_ceiling") != str(_domain.SLOPE_CLAMP_CEILING)
    ):
        raise SiteDomainActionError("site-domain slope contract drifted")
    slope_finite = _bounded_count(slope.get("finite_decimal_count"), label="slope.finite_decimal_count")
    buckets = sum(
        _bounded_count(slope.get(field), label=f"slope.{field}")
        for field in (
            "below_clamp_floor_count",
            "within_clamp_interval_count",
            "above_clamp_ceiling_count",
        )
    )
    if slope_finite != slope["static_domain_match_count"] or buckets != slope_finite:
        raise SiteDomainActionError("site-domain slope count relationship drifted")

    geology = _validate_common_counts(
        domains.get("geology"),
        expected_keys={
            "occurrence_count", "nonempty_count", "recognized_calibrated_label_count",
            "fixed_effects_fallback_label_count", "static_domain_match_count",
            "static_domain_reject_count", "static_contract", "recognized_calibrated_labels",
        },
        label="geology",
    )
    if (
        geology.get("static_contract") != "nonempty_label_with_fixed_effects_fallback"
        or geology.get("recognized_calibrated_labels") != sorted(_domain.RECOGNIZED_GEOLOGY_LABELS)
    ):
        raise SiteDomainActionError("site-domain geology contract drifted")
    nonempty = _bounded_count(geology.get("nonempty_count"), label="geology.nonempty_count")
    calibrated = _bounded_count(
        geology.get("recognized_calibrated_label_count"), label="geology.recognized_count"
    )
    fallback = _bounded_count(
        geology.get("fixed_effects_fallback_label_count"), label="geology.fallback_count"
    )
    if nonempty != geology["static_domain_match_count"] or calibrated + fallback != nonempty:
        raise SiteDomainActionError("site-domain geology count relationship drifted")

    reject_total = profile.get("static_domain_reject_total")
    if type(reject_total) is not int or isinstance(reject_total, bool) or not 0 <= reject_total <= 5 * EXPECTED_SITE_COUNT:
        raise SiteDomainActionError("site-domain reject total is outside bounded policy")
    if reject_total != sum(domains[name]["static_domain_reject_count"] for name in _domain.REQUIRED_PARAMETERS):
        raise SiteDomainActionError("site-domain reject total drifted")
    return payload


def _acquire_domain_profile(*, opener: Any, monotonic: Any) -> dict[str, Any]:
    """Acquire the fixed object with the reviewed transport and return counts only."""

    _require_contract()
    deadline = monotonic() + _transport.TOTAL_DEADLINE_SECONDS
    try:
        target = _transport.validate_target(
            source_issue=SOURCE_SCIENCE_ISSUE,
            dataset_id=DATASET_ID,
            project_id=PROJECT_ID,
            commit_sha=COMMIT_SHA,
            repository_path=REPOSITORY_PATH,
        )
    except _transport.EfehrReceiptError as exc:
        raise SiteDomainActionError("trusted Kosovo site-domain target is invalid") from exc
    file_url = _transport.raw_file_api_url(target)
    request = urllib.request.Request(
        file_url,
        headers={
            "Accept": "application/xml,text/xml,text/plain;q=0.9,application/octet-stream;q=0.8",
            "User-Agent": "OpenCatastrophe-EFEHR-site-domain-profile-v1",
        },
        method="GET",
    )
    try:
        with opener(request, timeout=_transport._remaining(deadline, monotonic)) as response:
            _transport._validate_exact_response(response, file_url)
            _transport._declared_length(response, EXPECTED_BYTE_COUNT)
            raw = _transport._read_bounded(
                response,
                deadline=deadline,
                maximum=EXPECTED_BYTE_COUNT,
                monotonic=monotonic,
            )
    except _transport.EfehrAcquisitionError as exc:
        raise SiteDomainAcquisitionError("Kosovo site-domain retrieval failed closed") from exc
    except (OSError, urllib.error.URLError, urllib.error.HTTPError, TimeoutError) as exc:
        raise SiteDomainAcquisitionError(
            f"Kosovo site-domain retrieval failed: {type(exc).__name__}"
        ) from exc
    if len(raw) != EXPECTED_BYTE_COUNT or hashlib.sha256(raw).hexdigest() != EXPECTED_SHA256:
        raise SiteDomainAcquisitionError("Kosovo site-domain byte identity drifted")
    try:
        payload = _CANONICAL_DOMAIN_PROFILER(raw)
    except _domain.KosovoSiteDomainError as exc:
        raise SiteDomainContentError("verified Kosovo bytes failed domain classification") from exc
    return _validate_domain_payload(payload)


def acquire_and_profile_kosovo_site_domains() -> dict[str, Any]:
    """Run the fixed production transport and return bounded count evidence only."""

    _require_production_identity()
    return _acquire_domain_profile(opener=_CANONICAL_OPEN_FIXED, monotonic=_CANONICAL_MONOTONIC)


def _base_result(*, execution_sha: str) -> dict[str, Any]:
    return {
        "schema_version": RESULT_SCHEMA_VERSION,
        "action": ACTION,
        "source_issue": CONTROL_ISSUE,
        "site_profile_issue": SITE_PROFILE_ISSUE,
        "source_science_issue": SOURCE_SCIENCE_ISSUE,
        "receipt_issue": RECEIPT_ISSUE,
        "dataset_id": DATASET_ID,
        "target_sha": execution_sha,
        "execution_sha": execution_sha,
        "external_bytes_persisted": False,
        "openquake_runtime_value_acceptance_verified": False,
        "crs_coordinate_semantics_verified": False,
        "missingness_semantics_verified": False,
        "gsim_site_parameter_sufficiency_verified": False,
        "site_adjusted_reference_authorized": False,
        "publication_authorized": False,
        "model_use_authorized": False,
    }


def _validate_terminal_result(result: object, *, execution_sha: str) -> dict[str, Any]:
    base = _base_result(execution_sha=execution_sha)
    if type(result) is not dict or set(result) != set(base) | {"status", "failure_class", "profile"}:
        raise SiteDomainActionError("trusted site-domain result fields drifted")
    for field, expected in base.items():
        observed = result.get(field)
        if type(observed) is not type(expected) or observed != expected:
            raise SiteDomainActionError(f"trusted site-domain result drifted at {field}")
    status = result.get("status")
    if status == "pass":
        if result.get("failure_class") is not None:
            raise SiteDomainActionError("site-domain PASS cannot carry failure_class")
        _validate_domain_payload(result.get("profile"))
        return result
    if status == "blocked":
        if (
            result.get("failure_class") not in {"acquisition_failure", "domain_profile_failure"}
            or result.get("profile") is not None
        ):
            raise SiteDomainActionError("blocked site-domain result is not safely bounded")
        return result
    raise SiteDomainActionError("trusted site-domain result has non-terminal status")


def _parse_trusted_terminal_result(body: object, *, execution_sha: str) -> bool:
    if type(body) is not str or RESULT_MARKER not in body:
        return False
    if body.count(RESULT_MARKER) != 1:
        raise SiteDomainActionError("trusted site-domain result marker is malformed")
    before, after = body.split(RESULT_MARKER, 1)
    if before.strip() or not after.strip():
        raise SiteDomainActionError("trusted site-domain result envelope is malformed")
    try:
        result = json.loads(after.strip(), object_pairs_hook=_pairs, parse_constant=_reject_constant)
    except SiteDomainActionError:
        raise
    except (json.JSONDecodeError, TypeError, ValueError) as exc:
        raise SiteDomainActionError("trusted site-domain result JSON is malformed") from exc
    _validate_terminal_result(result, execution_sha=execution_sha)
    return True


def has_terminal_site_domain_result(
    *,
    repository: str,
    token: str,
    execution_sha: str,
    opener: Any | None = None,
    max_pages: int = 20,
) -> bool:
    """Fail closed unless the complete bounded #291 result ledger is known."""

    if type(execution_sha) is not str or _SHA_RE.fullmatch(execution_sha) is None:
        raise SiteDomainActionError("invalid execution SHA")
    kwargs: dict[str, Any] = {"issue": CONTROL_ISSUE, "max_pages": max_pages}
    if opener is not None:
        kwargs["opener"] = opener
    try:
        comments = fetch_repository_comments(repository, token, **kwargs)
    except LedgerError as exc:
        raise SiteDomainActionError("site-domain result ledger is incomplete") from exc
    for comment in comments:
        if type(comment) is not dict:
            raise SiteDomainActionError("site-domain ledger contains a non-object comment")
        user = comment.get("user")
        login = user.get("login") if type(user) is dict else None
        if login != TRUSTED_RESULT_LOGIN:
            continue
        if _parse_trusted_terminal_result(comment.get("body"), execution_sha=execution_sha):
            return True
    return False


def _run_site_domain(
    *, execution_sha: str, acquirer: Callable[[], dict[str, Any]]
) -> dict[str, Any]:
    result = _base_result(execution_sha=execution_sha)
    try:
        payload = acquirer()
    except SiteDomainAcquisitionError:
        result.update({"status": "blocked", "failure_class": "acquisition_failure", "profile": None})
        return _validate_terminal_result(result, execution_sha=execution_sha)
    except SiteDomainContentError:
        result.update({"status": "blocked", "failure_class": "domain_profile_failure", "profile": None})
        return _validate_terminal_result(result, execution_sha=execution_sha)
    payload = _validate_domain_payload(payload)
    result.update({"status": "pass", "failure_class": None, "profile": payload})
    return _validate_terminal_result(result, execution_sha=execution_sha)


def run_site_domain(*, execution_sha: str) -> dict[str, Any]:
    return _run_site_domain(execution_sha=execution_sha, acquirer=acquire_and_profile_kosovo_site_domains)


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
        parser.error("--output is required for execution")
    result = run_site_domain(execution_sha=args.execution_sha)
    Path(args.output).write_text(
        json.dumps(result, sort_keys=True, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
