# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Trusted-main typed-ingestion gate for the exact ESHM20 Region-Main site CSV.

The action deliberately proves only a narrow compatibility layer: exact input
bytes, the pinned OpenQuake 3.14 CSV/site-model parser contract, and bounded
aggregate dtype/value-range and observed-support facts. Provider rows and raw
values are never returned, and scientific/site-response/model-use authority
remains closed.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import tempfile
import time
import urllib.error
import urllib.request
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Callable

try:
    from scripts import acquire_eshm20_site_model_profile as site_authority
    from scripts.prepare_agent_action_result import LedgerError, fetch_repository_comments
except ModuleNotFoundError:  # pragma: no cover - direct script execution path
    import acquire_eshm20_site_model_profile as site_authority
    from prepare_agent_action_result import LedgerError, fetch_repository_comments

REQUEST_MARKER = "<!-- oc-eq1-eshm20-site-oq314-typed-ingestion-request-v1 -->"
RESULT_MARKER = "<!-- oc-eq1-eshm20-site-oq314-typed-ingestion-result-v1 -->"
REQUEST_SCHEMA_VERSION = "oc-eshm20-site-oq314-typed-ingestion-request-v1"
RESULT_SCHEMA_VERSION = "oc-eshm20-site-oq314-typed-ingestion-result-v1"
ACTION = "eshm20_site_model_oq314_typed_ingestion"
CONTROL_ISSUE = 281
DATASET_ID = site_authority.DATASET_ID
TRUSTED_RESULT_LOGIN = "github-actions[bot]"
SOURCE_PROFILE_RESULT_COMMENT_ID = 5376038471
SOURCE_SEMANTICS_HANDOFF_COMMENT_ID = 5376088705
OPENQUAKE_COMMIT = "9f044c93d72846421a8faa90ebf0a6afacdf3c20"
OPENQUAKE_VERSION_PREFIX = "3.14.0"
EXPECTED_RECORD_COUNT = 94_493
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
MODE_A_REQUIRED_SITE_PARAMETERS = ("region", "vs30", "vs30measured", "xvf")
EXPECTED_DTYPES = {
    "lat": "float64",
    "lon": "float64",
    "region": "uint32",
    "vs30": "float64",
    "vs30measured": "bool",
    "xvf": "float64",
    "z1pt0": "float64",
    "z2pt5": "float64",
}

_SHA_RE = re.compile(r"^[0-9a-f]{40}$")
_SHA256_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
_BOOTSTRAP_REPO_DIGEST_RE = re.compile(r"^openquake/engine@sha256:[0-9a-f]{64}$")
_SAFE_REQUESTER_RE = re.compile(r"^[A-Za-z0-9_.:@/+ -]{1,96}$")
_REQUEST_FIELDS = {
    "schema_version",
    "action",
    "issue",
    "target_sha",
    "dataset_id",
    "requester",
}
_EVIDENCE_FIELDS = {
    "parser",
    "record_count",
    "input_header",
    "typed_fields",
    "mode_a_required_site_parameters",
    "mode_a_required_fields_typed",
    "rounded_coordinate_duplicate_check_passed",
    "site_collection_construction_passed",
    "longitude_point_domain_valid",
    "latitude_point_domain_valid",
    "vs30_positive_finite",
    "vs30measured_boolean_typed",
    "region_observed_support_exact_0_through_5",
    "xvf_finite",
    "raw_values_returned",
}
_FALSE_CEILINGS = (
    "historical_environment_verified",
    "reference_base_image_byte_identity_verified",
    "wheel_byte_identity_verified",
    "crs_authorized",
    "coordinate_semantics_authorized",
    "site_response_authorized",
    "site_semantics_authorized",
    "numerical_hazard_agreement_verified",
    "full_hazard_compatibility_verified",
    "site_model_compatibility_verified",
    "reference_run_verified",
    "scientific_validity_verified",
    "external_bytes_persisted",
    "publication_authorized",
    "model_use_authorized",
)


class TypedSiteIngestionActionError(RuntimeError):
    """Fail-closed action/provenance contract error."""


class TypedSiteIngestionBlocked(RuntimeError):
    """Bounded acquisition/data/parser rejection with no raw-value disclosure."""


def _pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    value: dict[str, Any] = {}
    for key, item in pairs:
        if key in value:
            raise TypedSiteIngestionActionError("duplicate JSON key")
        value[key] = item
    return value


def _reject_constant(value: str) -> Any:
    raise TypedSiteIngestionActionError(f"non-finite JSON constant: {value}")


def validate_request(
    body: object, *, expected_issue: int, execution_sha: str
) -> dict[str, Any]:
    if type(expected_issue) is not int or expected_issue != CONTROL_ISSUE:
        raise TypedSiteIngestionActionError("wrong runtime issue")
    if type(execution_sha) is not str or not _SHA_RE.fullmatch(execution_sha):
        raise TypedSiteIngestionActionError("invalid execution SHA")
    if type(body) is not str or body.count(REQUEST_MARKER) != 1:
        raise TypedSiteIngestionActionError("invalid typed-ingestion request marker")
    before, after = body.split(REQUEST_MARKER, 1)
    if before.strip() or not after.strip():
        raise TypedSiteIngestionActionError(
            "typed-ingestion request envelope is not canonical"
        )
    try:
        request = json.loads(
            after.strip(), object_pairs_hook=_pairs, parse_constant=_reject_constant
        )
    except TypedSiteIngestionActionError:
        raise
    except (json.JSONDecodeError, TypeError, ValueError) as exc:
        raise TypedSiteIngestionActionError(
            "invalid typed-ingestion request JSON"
        ) from exc
    if type(request) is not dict or set(request) != _REQUEST_FIELDS:
        raise TypedSiteIngestionActionError("typed-ingestion request fields drifted")
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
            raise TypedSiteIngestionActionError(
                f"typed-ingestion request {field} drifted"
            )
    requester = request["requester"]
    if (
        type(requester) is not str
        or requester != requester.strip()
        or not _SAFE_REQUESTER_RE.fullmatch(requester)
    ):
        raise TypedSiteIngestionActionError("invalid requester identity")
    return request


def acquire_exact_site_model_payload(
    *, opener: Any | None = None, monotonic: Any = time.monotonic
) -> bytes:
    """Fetch only the existing fixed #361 site target and re-prove its bytes."""

    site_spec = site_authority._require_canonical_target()
    try:
        target = site_authority.validate_target(
            source_issue=site_authority.SOURCE_ISSUE,
            dataset_id=site_authority.DATASET_ID,
            project_id=site_authority.PROJECT_ID,
            commit_sha=site_authority.COMMIT_SHA,
            repository_path=site_spec.repository_path,
        )
    except Exception as exc:
        raise TypedSiteIngestionActionError(
            "trusted fixed site target drifted"
        ) from exc

    file_url = site_authority.raw_file_api_url(target)
    request = urllib.request.Request(
        file_url,
        headers={
            "Accept": "text/csv,text/plain;q=0.9,application/octet-stream;q=0.8",
            "User-Agent": "OpenCatastrophe-ESHM20-OQ314-typed-site-ingestion-v1",
        },
        method="GET",
    )
    deadline = monotonic() + site_authority.TOTAL_DEADLINE_SECONDS
    open_response = opener or site_authority._open_fixed
    try:
        with open_response(
            request, timeout=site_authority._remaining(deadline, monotonic)
        ) as response:
            site_authority._validate_exact_response(response, file_url)
            raw = site_authority._read_bounded(
                response,
                deadline=deadline,
                maximum=site_authority.EXPECTED_BYTE_COUNT,
                monotonic=monotonic,
            )
    except site_authority.Eshm20SiteModelProfileError:
        raise
    except site_authority.EfehrAcquisitionError as exc:
        raise TypedSiteIngestionBlocked("fixed site retrieval rejected") from exc
    except (
        OSError,
        urllib.error.URLError,
        urllib.error.HTTPError,
        TimeoutError,
    ) as exc:
        raise TypedSiteIngestionBlocked("fixed site retrieval failed") from exc

    site_authority._verify_payload_identity(raw)
    return raw


def _runtime_identity(
    *, runtime_image_digest: str, bootstrap_repo_digest: str
) -> dict[str, str]:
    if (
        type(runtime_image_digest) is not str
        or not _SHA256_RE.fullmatch(runtime_image_digest)
    ):
        raise TypedSiteIngestionActionError("invalid runtime image digest")
    if (
        type(bootstrap_repo_digest) is not str
        or not _BOOTSTRAP_REPO_DIGEST_RE.fullmatch(bootstrap_repo_digest)
    ):
        raise TypedSiteIngestionActionError("invalid bootstrap repository digest")
    if os.environ.get("OPENBLAS_NUM_THREADS") != "1":
        raise TypedSiteIngestionActionError(
            "OPENBLAS_NUM_THREADS must be set before OpenQuake import"
        )
    try:
        observed = subprocess.run(
            ["git", "-C", "/oq-engine", "rev-parse", "HEAD"],
            check=True,
            capture_output=True,
            text=True,
            timeout=15,
        ).stdout.strip()
    except (OSError, subprocess.SubprocessError) as exc:
        raise TypedSiteIngestionActionError(
            "cannot verify OpenQuake source checkout"
        ) from exc
    if observed != OPENQUAKE_COMMIT:
        raise TypedSiteIngestionActionError("OpenQuake source commit drifted")

    try:
        from openquake import baselib
    except Exception as exc:  # pragma: no cover - reconstructed runtime only
        raise TypedSiteIngestionActionError(
            "cannot import pinned OpenQuake runtime"
        ) from exc
    version = getattr(baselib, "__version__", None)
    if type(version) is not str or not version.startswith(OPENQUAKE_VERSION_PREFIX):
        raise TypedSiteIngestionActionError("OpenQuake runtime version drifted")
    return {
        "commit": observed,
        "version": version,
        "runtime_image_digest": runtime_image_digest,
        "bootstrap_repo_digest": bootstrap_repo_digest,
    }


def _all_finite(np: Any, values: Any) -> bool:
    return bool(np.isfinite(values).all())


def _ingest_payload_with_oq314(payload: bytes) -> dict[str, Any]:
    """Execute the exact OQ3.14 site-model CSV path and bounded checks."""

    site_authority._verify_payload_identity(payload)
    try:
        import numpy as np
        from openquake.commonlib import readinput
        from openquake.hazardlib import site
    except Exception as exc:  # pragma: no cover - runtime-only dependency
        raise TypedSiteIngestionActionError(
            "pinned OpenQuake parser imports failed"
        ) from exc

    tmp_path: str | None = None
    original_get_gsim_lt = readinput.get_gsim_lt
    try:
        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as handle:
            handle.write(payload)
            tmp_path = handle.name

        # get_site_model asks the GMM tree only for req_site_params before its
        # CSV branch. That exact Mode-A set is already evidence-bound on #281;
        # injecting only it keeps this gate independent of a second GMM fetch.
        required = set(MODE_A_REQUIRED_SITE_PARAMETERS)
        readinput.get_gsim_lt = lambda _oqparam: SimpleNamespace(
            req_site_params=set(required)
        )
        oqparam = SimpleNamespace(inputs={"site_model": [tmp_path]})
        sm = readinput.get_site_model(oqparam)
    except TypedSiteIngestionActionError:
        raise
    except Exception as exc:
        raise TypedSiteIngestionBlocked(
            "OpenQuake typed site ingestion rejected the exact CSV"
        ) from exc
    finally:
        readinput.get_gsim_lt = original_get_gsim_lt
        if tmp_path is not None:
            try:
                os.unlink(tmp_path)
            except FileNotFoundError:
                pass

    if type(sm) is not np.ndarray or sm.dtype.names is None:
        raise TypedSiteIngestionActionError(
            "OpenQuake site parser returned an invalid array"
        )
    if len(sm) != EXPECTED_RECORD_COUNT:
        raise TypedSiteIngestionBlocked("typed record count drifted")
    if set(sm.dtype.names) != set(EXPECTED_HEADER):
        raise TypedSiteIngestionBlocked("typed site fields drifted")

    typed_fields: list[dict[str, str]] = []
    for name in EXPECTED_HEADER:
        observed = np.dtype(sm.dtype[name]).name
        expected = EXPECTED_DTYPES[name]
        if observed != expected:
            raise TypedSiteIngestionBlocked("typed site dtype drifted")
        typed_fields.append({"name": name, "dtype": observed})

    lon = sm["lon"]
    lat = sm["lat"]
    vs30 = sm["vs30"]
    xvf = sm["xvf"]
    region = sm["region"]
    checks = {
        "longitude_point_domain_valid": _all_finite(np, lon)
        and bool(((lon >= -180.0) & (lon <= 180.0)).all()),
        "latitude_point_domain_valid": _all_finite(np, lat)
        and bool(((lat >= -90.0) & (lat <= 90.0)).all()),
        "vs30_positive_finite": _all_finite(np, vs30)
        and bool((vs30 > 0.0).all()),
        "vs30measured_boolean_typed": (
            np.dtype(sm.dtype["vs30measured"]).name == "bool"
        ),
        "region_observed_support_exact_0_through_5": (
            set(int(value) for value in np.unique(region)) == {0, 1, 2, 3, 4, 5}
        ),
        "xvf_finite": _all_finite(np, xvf),
    }
    if not all(checks.values()):
        raise TypedSiteIngestionBlocked(
            "bounded typed-site value/support check rejected the exact CSV"
        )

    try:
        sitecol = site.SiteCollection.from_points(
            lon,
            lat,
            sitemodel=sm,
            req_site_params=set(MODE_A_REQUIRED_SITE_PARAMETERS),
        )
    except Exception as exc:
        raise TypedSiteIngestionBlocked(
            "OpenQuake SiteCollection rejected the typed site model"
        ) from exc
    if len(sitecol) != EXPECTED_RECORD_COUNT:
        raise TypedSiteIngestionBlocked(
            "OpenQuake SiteCollection record count drifted"
        )
    if not set(MODE_A_REQUIRED_SITE_PARAMETERS).issubset(
        sitecol.array.dtype.names
    ):
        raise TypedSiteIngestionBlocked(
            "OpenQuake SiteCollection lost a required Mode-A field"
        )

    return {
        "parser": "openquake.commonlib.readinput.get_site_model/csv",
        "record_count": EXPECTED_RECORD_COUNT,
        "input_header": list(EXPECTED_HEADER),
        "typed_fields": typed_fields,
        "mode_a_required_site_parameters": list(MODE_A_REQUIRED_SITE_PARAMETERS),
        "mode_a_required_fields_typed": True,
        "rounded_coordinate_duplicate_check_passed": True,
        "site_collection_construction_passed": True,
        **checks,
        "raw_values_returned": False,
    }


def _validate_evidence(value: object) -> dict[str, Any]:
    if type(value) is not dict or set(value) != _EVIDENCE_FIELDS:
        raise TypedSiteIngestionActionError(
            "typed-ingestion evidence fields drifted"
        )
    exact = {
        "parser": "openquake.commonlib.readinput.get_site_model/csv",
        "record_count": EXPECTED_RECORD_COUNT,
        "input_header": list(EXPECTED_HEADER),
        "mode_a_required_site_parameters": list(MODE_A_REQUIRED_SITE_PARAMETERS),
        "mode_a_required_fields_typed": True,
        "rounded_coordinate_duplicate_check_passed": True,
        "site_collection_construction_passed": True,
        "longitude_point_domain_valid": True,
        "latitude_point_domain_valid": True,
        "vs30_positive_finite": True,
        "vs30measured_boolean_typed": True,
        "region_observed_support_exact_0_through_5": True,
        "xvf_finite": True,
        "raw_values_returned": False,
    }
    for field, expected in exact.items():
        observed = value.get(field)
        if type(observed) is not type(expected) or observed != expected:
            raise TypedSiteIngestionActionError(
                f"typed-ingestion evidence drifted at {field}"
            )
    typed = value["typed_fields"]
    expected_typed = [
        {"name": name, "dtype": EXPECTED_DTYPES[name]} for name in EXPECTED_HEADER
    ]
    if type(typed) is not list or typed != expected_typed:
        raise TypedSiteIngestionActionError("typed field dtype inventory drifted")
    return value


def _base_result(
    *, execution_sha: str, runtime_image_digest: str, bootstrap_repo_digest: str
) -> dict[str, Any]:
    if type(execution_sha) is not str or not _SHA_RE.fullmatch(execution_sha):
        raise TypedSiteIngestionActionError("invalid execution SHA")
    if (
        type(runtime_image_digest) is not str
        or not _SHA256_RE.fullmatch(runtime_image_digest)
    ):
        raise TypedSiteIngestionActionError("invalid runtime image digest")
    if (
        type(bootstrap_repo_digest) is not str
        or not _BOOTSTRAP_REPO_DIGEST_RE.fullmatch(bootstrap_repo_digest)
    ):
        raise TypedSiteIngestionActionError("invalid bootstrap repository digest")
    return {
        "schema_version": RESULT_SCHEMA_VERSION,
        "action": ACTION,
        "source_issue": CONTROL_ISSUE,
        "dataset_id": DATASET_ID,
        "target_sha": execution_sha,
        "execution_sha": execution_sha,
        "source_profile_result_comment_id": SOURCE_PROFILE_RESULT_COMMENT_ID,
        "source_semantics_handoff_comment_id": SOURCE_SEMANTICS_HANDOFF_COMMENT_ID,
        "source_identity": {
            "project_id": site_authority.PROJECT_ID,
            "project_path": site_authority.PROJECT_PATH,
            "commit_sha": site_authority.COMMIT_SHA,
            "repository_path": site_authority.REPOSITORY_PATH,
            "byte_count": site_authority.EXPECTED_BYTE_COUNT,
            "sha256": site_authority.EXPECTED_SHA256,
        },
        "openquake_reference": {
            "commit": OPENQUAKE_COMMIT,
            "version_prefix": OPENQUAKE_VERSION_PREFIX,
            "runtime_image_digest": runtime_image_digest,
            "bootstrap_repo_digest": bootstrap_repo_digest,
        },
        "historical_environment_verified": False,
        "reference_base_image_byte_identity_verified": False,
        "wheel_byte_identity_verified": False,
        "crs_authorized": False,
        "coordinate_semantics_authorized": False,
        "site_response_authorized": False,
        "site_semantics_authorized": False,
        "numerical_hazard_agreement_verified": False,
        "full_hazard_compatibility_verified": False,
        "site_model_compatibility_verified": False,
        "reference_run_verified": False,
        "scientific_validity_verified": False,
        "external_bytes_persisted": False,
        "publication_authorized": False,
        "model_use_authorized": False,
    }


def _blocked_result(
    base: dict[str, Any], *, runtime_version: str, failure_class: str, exact_bytes: bool
) -> dict[str, Any]:
    return {
        **base,
        "status": "blocked",
        "failure_class": failure_class,
        "typed_ingestion": None,
        "openquake_runtime_version": runtime_version,
        "exact_site_bytes_verified": exact_bytes,
        "openquake_typed_ingestion_verified": False,
        "bounded_dtype_value_and_observed_support_verified": False,
    }


def run_typed_ingestion(
    *,
    execution_sha: str,
    runtime_image_digest: str,
    bootstrap_repo_digest: str,
    acquirer: Callable[[], bytes] = acquire_exact_site_model_payload,
    identity_verifier: Callable[[bytes], str] = site_authority._verify_payload_identity,
    runtime_inspector: Callable[..., dict[str, str]] = _runtime_identity,
    ingestor: Callable[[bytes], dict[str, Any]] = _ingest_payload_with_oq314,
) -> dict[str, Any]:
    base = _base_result(
        execution_sha=execution_sha,
        runtime_image_digest=runtime_image_digest,
        bootstrap_repo_digest=bootstrap_repo_digest,
    )
    runtime = runtime_inspector(
        runtime_image_digest=runtime_image_digest,
        bootstrap_repo_digest=bootstrap_repo_digest,
    )
    if runtime.get("commit") != OPENQUAKE_COMMIT:
        raise TypedSiteIngestionActionError(
            "runtime inspector left the exact OQ3.14 commit"
        )
    version = runtime.get("version")
    if type(version) is not str or not version.startswith(OPENQUAKE_VERSION_PREFIX):
        raise TypedSiteIngestionActionError("runtime inspector left OQ3.14")
    if runtime.get("runtime_image_digest") != runtime_image_digest:
        raise TypedSiteIngestionActionError("runtime image identity drifted")
    if runtime.get("bootstrap_repo_digest") != bootstrap_repo_digest:
        raise TypedSiteIngestionActionError("bootstrap image identity drifted")

    try:
        payload = acquirer()
        observed_sha = identity_verifier(payload)
    except (site_authority.Eshm20SiteModelProfileError, TypedSiteIngestionBlocked):
        return _blocked_result(
            base,
            runtime_version=version,
            failure_class="site_byte_identity_or_acquisition_rejected",
            exact_bytes=False,
        )
    if observed_sha != site_authority.EXPECTED_SHA256:
        raise TypedSiteIngestionActionError(
            "site payload verifier returned the wrong digest"
        )

    try:
        evidence = _validate_evidence(ingestor(payload))
    except TypedSiteIngestionBlocked:
        return _blocked_result(
            base,
            runtime_version=version,
            failure_class="typed_site_ingestion_rejected",
            exact_bytes=True,
        )

    return {
        **base,
        "status": "pass",
        "failure_class": None,
        "typed_ingestion": evidence,
        "openquake_runtime_version": version,
        "exact_site_bytes_verified": True,
        "openquake_typed_ingestion_verified": True,
        "bounded_dtype_value_and_observed_support_verified": True,
    }


def _validate_terminal_result(
    result: object, *, execution_sha: str
) -> dict[str, Any]:
    if type(result) is not dict:
        raise TypedSiteIngestionActionError(
            "typed-ingestion result must be an object"
        )
    runtime = result.get("openquake_reference")
    if type(runtime) is not dict:
        raise TypedSiteIngestionActionError(
            "typed-ingestion runtime identity missing"
        )
    base = _base_result(
        execution_sha=execution_sha,
        runtime_image_digest=runtime.get("runtime_image_digest"),
        bootstrap_repo_digest=runtime.get("bootstrap_repo_digest"),
    )
    expected_fields = set(base) | {
        "status",
        "failure_class",
        "typed_ingestion",
        "openquake_runtime_version",
        "exact_site_bytes_verified",
        "openquake_typed_ingestion_verified",
        "bounded_dtype_value_and_observed_support_verified",
    }
    if set(result) != expected_fields:
        raise TypedSiteIngestionActionError(
            "typed-ingestion result fields drifted"
        )
    for field, expected in base.items():
        observed = result.get(field)
        if type(observed) is not type(expected) or observed != expected:
            raise TypedSiteIngestionActionError(
                f"typed-ingestion result drifted at {field}"
            )
    version = result["openquake_runtime_version"]
    if type(version) is not str or not version.startswith(OPENQUAKE_VERSION_PREFIX):
        raise TypedSiteIngestionActionError(
            "typed-ingestion result runtime version drifted"
        )
    for field in _FALSE_CEILINGS:
        if result[field] is not False:
            raise TypedSiteIngestionActionError(
                f"typed-ingestion result widened {field}"
            )

    status = result["status"]
    if status == "pass":
        if result["failure_class"] is not None:
            raise TypedSiteIngestionActionError("PASS cannot carry a failure class")
        _validate_evidence(result["typed_ingestion"])
        for field in (
            "exact_site_bytes_verified",
            "openquake_typed_ingestion_verified",
            "bounded_dtype_value_and_observed_support_verified",
        ):
            if result[field] is not True:
                raise TypedSiteIngestionActionError(
                    f"PASS did not prove {field}"
                )
        return result

    if status != "blocked" or result["typed_ingestion"] is not None:
        raise TypedSiteIngestionActionError(
            "typed-ingestion result is not a bounded terminal state"
        )
    failure_class = result["failure_class"]
    if failure_class == "site_byte_identity_or_acquisition_rejected":
        expected_flags = (False, False, False)
    elif failure_class == "typed_site_ingestion_rejected":
        expected_flags = (True, False, False)
    else:
        raise TypedSiteIngestionActionError("blocked failure class drifted")
    observed_flags = (
        result["exact_site_bytes_verified"],
        result["openquake_typed_ingestion_verified"],
        result["bounded_dtype_value_and_observed_support_verified"],
    )
    if observed_flags != expected_flags or any(type(v) is not bool for v in observed_flags):
        raise TypedSiteIngestionActionError(
            "blocked verification-stage flags drifted"
        )
    return result


def _parse_trusted_terminal_result(body: object, *, execution_sha: str) -> bool:
    if type(body) is not str or RESULT_MARKER not in body:
        return False
    if body.count(RESULT_MARKER) != 1:
        raise TypedSiteIngestionActionError(
            "trusted typed-ingestion marker is malformed"
        )
    before, after = body.split(RESULT_MARKER, 1)
    if before.strip() or not after.strip():
        raise TypedSiteIngestionActionError(
            "trusted typed-ingestion envelope is malformed"
        )
    try:
        result = json.loads(
            after.strip(), object_pairs_hook=_pairs, parse_constant=_reject_constant
        )
    except TypedSiteIngestionActionError:
        raise
    except (json.JSONDecodeError, TypeError, ValueError) as exc:
        raise TypedSiteIngestionActionError(
            "trusted typed-ingestion JSON is malformed"
        ) from exc
    if type(result) is not dict:
        raise TypedSiteIngestionActionError(
            "trusted typed-ingestion result is not an object"
        )
    observed_sha = result.get("execution_sha")
    if type(observed_sha) is not str or not _SHA_RE.fullmatch(observed_sha):
        raise TypedSiteIngestionActionError(
            "trusted typed-ingestion execution SHA is invalid"
        )
    _validate_terminal_result(result, execution_sha=observed_sha)
    return observed_sha == execution_sha


def has_terminal_typed_ingestion_result(
    *,
    repository: str,
    token: str,
    execution_sha: str,
    opener: Any | None = None,
    max_pages: int = 20,
) -> bool:
    if type(execution_sha) is not str or not _SHA_RE.fullmatch(execution_sha):
        raise TypedSiteIngestionActionError("invalid execution SHA")
    kwargs: dict[str, Any] = {"issue": CONTROL_ISSUE, "max_pages": max_pages}
    if opener is not None:
        kwargs["opener"] = opener
    try:
        comments = fetch_repository_comments(repository, token, **kwargs)
    except LedgerError as exc:
        raise TypedSiteIngestionActionError(
            "typed-ingestion result ledger is incomplete"
        ) from exc
    for comment in comments:
        if type(comment) is not dict:
            raise TypedSiteIngestionActionError(
                "typed-ingestion ledger contains a non-object"
            )
        user = comment.get("user")
        login = user.get("login") if type(user) is dict else None
        if login != TRUSTED_RESULT_LOGIN:
            continue
        if _parse_trusted_terminal_result(
            comment.get("body"), execution_sha=execution_sha
        ):
            return True
    return False


def _env_required(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise TypedSiteIngestionActionError(
            f"required environment variable {name} is missing"
        )
    return value


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--comment-body-env", required=True)
    parser.add_argument("--expected-issue", required=True, type=int)
    parser.add_argument("--execution-sha", required=True)
    parser.add_argument("--runtime-image-digest-env")
    parser.add_argument("--bootstrap-repo-digest-env")
    parser.add_argument("--output")
    parser.add_argument("--validate-request-only", action="store_true")
    args = parser.parse_args(argv)

    body = _env_required(args.comment_body_env)
    validate_request(
        body, expected_issue=args.expected_issue, execution_sha=args.execution_sha
    )
    if args.validate_request_only:
        return 0
    if (
        not args.runtime_image_digest_env
        or not args.bootstrap_repo_digest_env
        or not args.output
    ):
        raise TypedSiteIngestionActionError(
            "runtime identity/output arguments are required"
        )

    result = run_typed_ingestion(
        execution_sha=args.execution_sha,
        runtime_image_digest=_env_required(args.runtime_image_digest_env),
        bootstrap_repo_digest=_env_required(args.bootstrap_repo_digest_env),
    )
    _validate_terminal_result(result, execution_sha=args.execution_sha)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(result, sort_keys=True, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
