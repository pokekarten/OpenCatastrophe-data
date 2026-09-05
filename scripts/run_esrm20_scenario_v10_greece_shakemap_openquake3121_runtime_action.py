# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Trusted-main native OpenQuake 3.12.1 reader gate for the fixed Greece ShakeMap pair.

A PASS proves only that the exact already-receipted ESRM20 v1.0 Greece grid and
uncertainty XML objects are accepted by the exact OpenQuake 3.12.1 ShakeMap XML
reader and satisfy a small set of bounded structural postconditions.  It does not
establish scenario selection, validation, holdout status, numerical model
agreement, publication permission, or model-use authority.
"""

from __future__ import annotations

import argparse
import hashlib
import inspect
import json
import os
import re
import subprocess
import tempfile
from pathlib import Path
from typing import Any, Callable

try:
    from scripts import run_esrm20_scenario_v10_greece_shakemap_profile_action as base
except ModuleNotFoundError:  # pragma: no cover - direct script execution
    import run_esrm20_scenario_v10_greece_shakemap_profile_action as base

REQUEST_MARKER = "<!-- oc-eq1-esrm20-scenario-v10-greece-shakemap-openquake3121-runtime-request-v1 -->"
RESULT_MARKER = "<!-- oc-eq1-esrm20-scenario-v10-greece-shakemap-openquake3121-runtime-result-v1 -->"
REQUEST_SCHEMA_VERSION = "oc-esrm20-scenario-v10-greece-shakemap-openquake3121-runtime-request-v1"
RESULT_SCHEMA_VERSION = "oc-esrm20-scenario-v10-greece-shakemap-openquake3121-runtime-result-v1"
ACTION = "esrm20_scenario_v10_greece_shakemap_openquake3121_runtime"
TRUSTED_RESULT_LOGIN = "github-actions[bot]"
MAX_REQUEST_UTF8_BYTES = 4096
MAX_TERMINAL_UTF8_BYTES = 9000
MAX_LEDGER_PAGES = 20

_SOURCE_ISSUE = 285
_DATASET_ID = "efehr.esrm20.scenario-tests.v1.0"
_GRID_SHA256 = "3c2fe7a2a7182fac999442ce3d88ddfd99004b7f999462ef2327f2eebc1ccd9f"
_UNCERTAINTY_SHA256 = "eb08df5ff78f265fb45bf31dbd3dddf4f01bf10632382d4156a2bdf016e46417"
_EXPECTED_ROW_COUNT = 96_525
_EXPECTED_TOP_LEVEL_FIELDS = ("lon", "lat", "vs30", "val", "std")
_EXPECTED_IMTS = ("MMI", "PGA", "SA(0.3)", "SA(1.0)", "SA(3.0)")
_OPENQUAKE_REPOSITORY = "gem/oq-engine"
_OPENQUAKE_TAG = "v3.12.1"
_OPENQUAKE_COMMIT = "0bb8441aa202cd6ec075bf2044dd4aaeb26919b9"
_OPENQUAKE_PARSER_PATH = "openquake.hazardlib.shakemap.parsers.get_array(usgs_xml)"
_OPENQUAKE_ROOT = Path("/oq-engine")
_OPENQUAKE_PACKAGE_ROOT = _OPENQUAKE_ROOT / "openquake"
_OPENQUAKE_REFERENCE = {
    "repository": _OPENQUAKE_REPOSITORY,
    "tag": _OPENQUAKE_TAG,
    "commit": _OPENQUAKE_COMMIT,
    "parser_path": _OPENQUAKE_PARSER_PATH,
}

_SHA1_RE = re.compile(r"^[0-9a-f]{40}$")
_DIGEST_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
_REQUESTER_RE = re.compile(r"^[A-Za-z0-9_.:@/+ -]{1,96}$")
_REQUEST_FIELDS = {
    "schema_version",
    "action",
    "issue",
    "target_sha",
    "dataset_id",
    "grid_receipt_sha256",
    "uncertainty_receipt_sha256",
    "requester",
}
_RESULT_FIELDS = {
    "schema_version",
    "action",
    "source_issue",
    "dataset_id",
    "target_sha",
    "execution_sha",
    "shakemap_identity",
    "openquake_reference",
    "execution_container_image_digest",
    "status",
    "failure_stage",
    "failure_code",
    "runtime_source_commit_verified",
    "provider_file_bytes_read",
    "byte_identity_verified",
    "trusted_profile_precondition_verified",
    "native_reader_attempted",
    "native_reader_acceptance_verified",
    "native_row_count",
    "native_top_level_fields",
    "native_value_imts",
    "native_stddev_imts",
    "native_grid_uncertainty_coordinate_match_verified",
    "output_payload_bytes_read",
    "external_bytes_persisted",
    "historical_environment_verified",
    "event_location_inference_authorized",
    "scenario_selection_authorized",
    "scientific_validity_verified",
    "independent_validation_established",
    "holdout_status_established",
    "publication_authorized",
    "model_use_authorized",
}
_FAILURES = {
    "runtime_identity": "runtime_identity_rejected",
    "acquisition": "acquisition_failed",
    "byte_identity": "byte_identity_mismatch",
    "profile_precondition": "profile_precondition_rejected",
    "native_reader": "native_reader_rejected",
}


class GreeceShakeMapOpenQuake3121RuntimeError(RuntimeError):
    """The native-runtime request, execution, or evidence contract drifted."""


class NativeReaderRejected(RuntimeError):
    """The exact pair was not accepted by the bounded native reader contract."""


def _pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    value: dict[str, Any] = {}
    for key, item in pairs:
        if key in value:
            raise GreeceShakeMapOpenQuake3121RuntimeError("duplicate JSON key")
        value[key] = item
    return value


def _reject_constant(value: str) -> Any:
    raise GreeceShakeMapOpenQuake3121RuntimeError(
        f"non-finite JSON constant: {value}"
    )


def _strict_loads(text: str, *, label: str) -> Any:
    try:
        return json.loads(
            text,
            object_pairs_hook=_pairs,
            parse_constant=_reject_constant,
        )
    except GreeceShakeMapOpenQuake3121RuntimeError:
        raise
    except (json.JSONDecodeError, TypeError, ValueError) as exc:
        raise GreeceShakeMapOpenQuake3121RuntimeError(
            f"invalid {label} JSON"
        ) from exc


def _utf8_size(value: str) -> int:
    try:
        return len(value.encode("utf-8", errors="strict"))
    except UnicodeEncodeError as exc:
        raise GreeceShakeMapOpenQuake3121RuntimeError(
            "text is not UTF-8 encodable"
        ) from exc


def _require_authority() -> None:
    base._require_canonical_authority()
    exact = (
        (base.SOURCE_ISSUE, _SOURCE_ISSUE, "source issue"),
        (base.DATASET_ID, _DATASET_ID, "dataset id"),
        (base.GRID_SHA256, _GRID_SHA256, "grid sha256"),
        (base.UNCERTAINTY_SHA256, _UNCERTAINTY_SHA256, "uncertainty sha256"),
    )
    for observed, expected, label in exact:
        if type(observed) is not type(expected) or observed != expected:
            raise GreeceShakeMapOpenQuake3121RuntimeError(
                f"native runtime {label} drifted"
            )


def validate_request(
    body: object,
    *,
    expected_issue: int,
    execution_sha: str,
) -> dict[str, Any]:
    _require_authority()
    if type(expected_issue) is not int or expected_issue != _SOURCE_ISSUE:
        raise GreeceShakeMapOpenQuake3121RuntimeError("wrong issue")
    if type(execution_sha) is not str or _SHA1_RE.fullmatch(execution_sha) is None:
        raise GreeceShakeMapOpenQuake3121RuntimeError("invalid execution SHA")
    if (
        type(body) is not str
        or _utf8_size(body) > MAX_REQUEST_UTF8_BYTES
        or body.count(REQUEST_MARKER) != 1
    ):
        raise GreeceShakeMapOpenQuake3121RuntimeError("invalid request envelope")
    before, after = body.split(REQUEST_MARKER, 1)
    if before.strip() or not after.strip():
        raise GreeceShakeMapOpenQuake3121RuntimeError(
            "non-canonical request envelope"
        )
    request = _strict_loads(after.strip(), label="request")
    if type(request) is not dict or set(request) != _REQUEST_FIELDS:
        raise GreeceShakeMapOpenQuake3121RuntimeError("request fields drifted")
    exact = (
        ("schema_version", REQUEST_SCHEMA_VERSION),
        ("action", ACTION),
        ("issue", _SOURCE_ISSUE),
        ("target_sha", execution_sha),
        ("dataset_id", _DATASET_ID),
        ("grid_receipt_sha256", _GRID_SHA256),
        ("uncertainty_receipt_sha256", _UNCERTAINTY_SHA256),
    )
    for field, expected in exact:
        observed = request.get(field)
        if type(observed) is not type(expected) or observed != expected:
            raise GreeceShakeMapOpenQuake3121RuntimeError(
                f"request {field} drifted"
            )
    requester = request["requester"]
    if (
        type(requester) is not str
        or requester != requester.strip()
        or _REQUESTER_RE.fullmatch(requester) is None
    ):
        raise GreeceShakeMapOpenQuake3121RuntimeError("invalid requester")
    return request


def _base_result(*, execution_sha: str, image_digest: str) -> dict[str, Any]:
    return {
        "schema_version": RESULT_SCHEMA_VERSION,
        "action": ACTION,
        "source_issue": _SOURCE_ISSUE,
        "dataset_id": _DATASET_ID,
        "target_sha": execution_sha,
        "execution_sha": execution_sha,
        "shakemap_identity": base._identity(),
        "openquake_reference": dict(_OPENQUAKE_REFERENCE),
        "execution_container_image_digest": image_digest,
        "status": "blocked",
        "failure_stage": "runtime_identity",
        "failure_code": _FAILURES["runtime_identity"],
        "runtime_source_commit_verified": False,
        "provider_file_bytes_read": False,
        "byte_identity_verified": False,
        "trusted_profile_precondition_verified": False,
        "native_reader_attempted": False,
        "native_reader_acceptance_verified": False,
        "native_row_count": None,
        "native_top_level_fields": None,
        "native_value_imts": None,
        "native_stddev_imts": None,
        "native_grid_uncertainty_coordinate_match_verified": False,
        "output_payload_bytes_read": False,
        "external_bytes_persisted": False,
        "historical_environment_verified": False,
        "event_location_inference_authorized": False,
        "scenario_selection_authorized": False,
        "scientific_validity_verified": False,
        "independent_validation_established": False,
        "holdout_status_established": False,
        "publication_authorized": False,
        "model_use_authorized": False,
    }


def _validate_terminal_result(result: object) -> str:
    _require_authority()
    if type(result) is not dict or set(result) != _RESULT_FIELDS:
        raise GreeceShakeMapOpenQuake3121RuntimeError("result fields drifted")
    execution_sha = result.get("execution_sha")
    if type(execution_sha) is not str or _SHA1_RE.fullmatch(execution_sha) is None:
        raise GreeceShakeMapOpenQuake3121RuntimeError("invalid result SHA")
    image_digest = result.get("execution_container_image_digest")
    if type(image_digest) is not str or _DIGEST_RE.fullmatch(image_digest) is None:
        raise GreeceShakeMapOpenQuake3121RuntimeError("invalid image digest")
    exact = (
        ("schema_version", RESULT_SCHEMA_VERSION),
        ("action", ACTION),
        ("source_issue", _SOURCE_ISSUE),
        ("dataset_id", _DATASET_ID),
        ("target_sha", execution_sha),
        ("shakemap_identity", base._identity()),
        ("openquake_reference", _OPENQUAKE_REFERENCE),
        ("output_payload_bytes_read", False),
        ("external_bytes_persisted", False),
        ("historical_environment_verified", False),
        ("event_location_inference_authorized", False),
        ("scenario_selection_authorized", False),
        ("scientific_validity_verified", False),
        ("independent_validation_established", False),
        ("holdout_status_established", False),
        ("publication_authorized", False),
        ("model_use_authorized", False),
    )
    for field, expected in exact:
        if result.get(field) != expected:
            raise GreeceShakeMapOpenQuake3121RuntimeError(
                f"result {field} drifted"
            )

    bool_fields = (
        "runtime_source_commit_verified",
        "provider_file_bytes_read",
        "byte_identity_verified",
        "trusted_profile_precondition_verified",
        "native_reader_attempted",
        "native_reader_acceptance_verified",
        "native_grid_uncertainty_coordinate_match_verified",
    )
    if any(type(result.get(field)) is not bool for field in bool_fields):
        raise GreeceShakeMapOpenQuake3121RuntimeError(
            "runtime result boolean evidence drifted"
        )

    status = result.get("status")
    stage = result.get("failure_stage")
    code = result.get("failure_code")
    bounded_native = (
        result.get("native_row_count"),
        result.get("native_top_level_fields"),
        result.get("native_value_imts"),
        result.get("native_stddev_imts"),
    )
    if status == "pass":
        expected_native = (
            _EXPECTED_ROW_COUNT,
            list(_EXPECTED_TOP_LEVEL_FIELDS),
            list(_EXPECTED_IMTS),
            list(_EXPECTED_IMTS),
        )
        if (
            stage is not None
            or code is not None
            or result["runtime_source_commit_verified"] is not True
            or result["provider_file_bytes_read"] is not True
            or result["byte_identity_verified"] is not True
            or result["trusted_profile_precondition_verified"] is not True
            or result["native_reader_attempted"] is not True
            or result["native_reader_acceptance_verified"] is not True
            or result["native_grid_uncertainty_coordinate_match_verified"] is not True
            or bounded_native != expected_native
        ):
            raise GreeceShakeMapOpenQuake3121RuntimeError("invalid PASS state")
    elif status == "blocked":
        if stage not in _FAILURES or code != _FAILURES[stage]:
            raise GreeceShakeMapOpenQuake3121RuntimeError(
                "invalid blocked failure state"
            )
        expected_prefixes = {
            "runtime_identity": {(False, False, False, False, False)},
            "acquisition": {
                (True, False, False, False, False),
                (True, True, False, False, False),
            },
            "byte_identity": {(True, True, False, False, False)},
            "profile_precondition": {(True, True, True, False, False)},
            "native_reader": {(True, True, True, True, True)},
        }[stage]
        observed_prefix = (
            result["runtime_source_commit_verified"],
            result["provider_file_bytes_read"],
            result["byte_identity_verified"],
            result["trusted_profile_precondition_verified"],
            result["native_reader_attempted"],
        )
        if observed_prefix not in expected_prefixes:
            raise GreeceShakeMapOpenQuake3121RuntimeError(
                "blocked stage evidence drifted"
            )
        if (
            result["native_reader_acceptance_verified"] is not False
            or result["native_grid_uncertainty_coordinate_match_verified"] is not False
            or any(value is not None for value in bounded_native)
        ):
            raise GreeceShakeMapOpenQuake3121RuntimeError(
                "blocked result widened native evidence"
            )
    else:
        raise GreeceShakeMapOpenQuake3121RuntimeError("non-terminal status")
    return execution_sha


def parse_terminal_result(body: object) -> str | None:
    if type(body) is not str or RESULT_MARKER not in body:
        return None
    if _utf8_size(body) > MAX_TERMINAL_UTF8_BYTES or body.count(RESULT_MARKER) != 1:
        raise GreeceShakeMapOpenQuake3121RuntimeError("invalid result envelope")
    before, after = body.split(RESULT_MARKER, 1)
    if before.strip() or not after.strip():
        raise GreeceShakeMapOpenQuake3121RuntimeError(
            "non-canonical result envelope"
        )
    return _validate_terminal_result(_strict_loads(after.strip(), label="result"))


def has_terminal_result(
    *,
    repository: str,
    token: str,
    execution_sha: str,
    opener: Any | None = None,
) -> bool:
    if type(execution_sha) is not str or _SHA1_RE.fullmatch(execution_sha) is None:
        raise GreeceShakeMapOpenQuake3121RuntimeError("invalid execution SHA")
    kwargs: dict[str, Any] = {"issue": _SOURCE_ISSUE, "max_pages": MAX_LEDGER_PAGES}
    if opener is not None:
        kwargs["opener"] = opener
    try:
        comments = base.fetch_repository_comments(repository, token, **kwargs)
    except base.LedgerError as exc:
        raise GreeceShakeMapOpenQuake3121RuntimeError(
            "runtime result ledger is incomplete"
        ) from exc
    found = False
    for comment in comments:
        user = comment.get("user")
        login = user.get("login") if type(user) is dict else None
        if login != TRUSTED_RESULT_LOGIN:
            continue
        if parse_terminal_result(comment.get("body")) == execution_sha:
            found = True
    return found


def _require_source_path(source_file: str | Path, *, package_root: Path) -> Path:
    source_path = Path(source_file).resolve()
    expected_root = package_root.resolve()
    try:
        source_path.relative_to(expected_root)
    except ValueError as exc:
        raise GreeceShakeMapOpenQuake3121RuntimeError(
            "OpenQuake reader resolved outside exact checkout"
        ) from exc
    if not source_path.is_file():
        raise GreeceShakeMapOpenQuake3121RuntimeError(
            "OpenQuake reader source identity unavailable"
        )
    return source_path


def verify_runtime_source_identity(
    *,
    checkout_root: Path = _OPENQUAKE_ROOT,
) -> None:
    root = checkout_root.resolve()
    package_root = root / "openquake"
    if not package_root.is_dir():
        raise GreeceShakeMapOpenQuake3121RuntimeError(
            "exact OpenQuake package root unavailable"
        )
    try:
        observed = subprocess.run(
            ["git", "-C", str(root), "rev-parse", "HEAD"],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
            timeout=10,
        ).stdout.strip()
    except (OSError, subprocess.SubprocessError):
        raise GreeceShakeMapOpenQuake3121RuntimeError(
            "OpenQuake source commit observation failed"
        ) from None
    if observed != _OPENQUAKE_COMMIT:
        raise GreeceShakeMapOpenQuake3121RuntimeError(
            "OpenQuake source commit drifted"
        )
    try:
        from openquake.hazardlib.shakemap import parsers
    except Exception:
        raise GreeceShakeMapOpenQuake3121RuntimeError(
            "OpenQuake 3.12.1 ShakeMap parser unavailable"
        ) from None
    source_file = inspect.getsourcefile(parsers.get_array_usgs_xml)
    if source_file is None:
        raise GreeceShakeMapOpenQuake3121RuntimeError(
            "OpenQuake reader source identity unavailable"
        )
    _require_source_path(source_file, package_root=package_root)


def validate_fixed_bytes(grid_data: bytes, uncertainty_data: bytes) -> None:
    if type(grid_data) is not bytes or type(uncertainty_data) is not bytes:
        raise TypeError("ShakeMap payloads must be bytes")
    if (
        len(grid_data) != base.GRID_BYTE_COUNT
        or hashlib.sha256(grid_data).hexdigest() != _GRID_SHA256
        or len(uncertainty_data) != base.UNCERTAINTY_BYTE_COUNT
        or hashlib.sha256(uncertainty_data).hexdigest() != _UNCERTAINTY_SHA256
    ):
        raise base.ShakeMapByteIdentityError("fixed ShakeMap byte identity mismatch")


def _validate_native_array(data: Any) -> dict[str, Any]:
    try:
        import numpy
    except Exception:
        raise NativeReaderRejected("native_reader_rejected") from None
    try:
        top_fields = tuple(data.dtype.names or ())
        val_imts = tuple(sorted(data["val"].dtype.names or ()))
        std_imts = tuple(sorted(data["std"].dtype.names or ()))
        row_count = len(data)
        finite_coordinates = bool(
            numpy.isfinite(data["lon"]).all()
            and numpy.isfinite(data["lat"]).all()
        )
    except Exception:
        raise NativeReaderRejected("native_reader_rejected") from None
    if (
        top_fields != _EXPECTED_TOP_LEVEL_FIELDS
        or val_imts != _EXPECTED_IMTS
        or std_imts != _EXPECTED_IMTS
        or row_count != _EXPECTED_ROW_COUNT
        or not finite_coordinates
    ):
        raise NativeReaderRejected("native_reader_rejected")
    return {
        "native_row_count": row_count,
        "native_top_level_fields": list(top_fields),
        "native_value_imts": list(val_imts),
        "native_stddev_imts": list(std_imts),
        "native_grid_uncertainty_coordinate_match_verified": True,
    }


def _native_read_unbound(
    grid_data: bytes,
    uncertainty_data: bytes,
    *,
    reader: Callable[..., Any],
) -> dict[str, Any]:
    try:
        with tempfile.TemporaryDirectory(prefix="oc-oq3121-shakemap-") as directory:
            grid_path = Path(directory) / "grid.xml"
            uncertainty_path = Path(directory) / "uncertainty.xml"
            grid_path.write_bytes(grid_data)
            uncertainty_path.write_bytes(uncertainty_data)
            data = reader("usgs_xml", str(grid_path), str(uncertainty_path))
    except Exception:
        raise NativeReaderRejected("native_reader_rejected") from None
    return _validate_native_array(data)


def native_read_fixed_bytes(
    grid_data: bytes,
    uncertainty_data: bytes,
) -> dict[str, Any]:
    validate_fixed_bytes(grid_data, uncertainty_data)
    try:
        from openquake.hazardlib.shakemap import parsers
    except Exception:
        raise NativeReaderRejected("native_reader_rejected") from None
    source_file = inspect.getsourcefile(parsers.get_array_usgs_xml)
    if source_file is None:
        raise NativeReaderRejected("native_reader_rejected")
    try:
        _require_source_path(source_file, package_root=_OPENQUAKE_PACKAGE_ROOT)
    except GreeceShakeMapOpenQuake3121RuntimeError:
        raise NativeReaderRejected("native_reader_rejected") from None
    return _native_read_unbound(
        grid_data,
        uncertainty_data,
        reader=parsers.get_array,
    )


def _run_native_with(
    *,
    execution_sha: str,
    image_digest: str,
    runtime_verifier: Callable[[], None],
    fetcher: Callable[[], tuple[tuple[bytes, bytes], dict[str, Any]]],
    identity_checker: Callable[[bytes, bytes], None],
    profile_checker: Callable[[bytes, bytes], dict[str, object]],
    native_reader: Callable[[bytes, bytes], dict[str, Any]],
) -> dict[str, Any]:
    if type(execution_sha) is not str or _SHA1_RE.fullmatch(execution_sha) is None:
        raise GreeceShakeMapOpenQuake3121RuntimeError("invalid execution SHA")
    if type(image_digest) is not str or _DIGEST_RE.fullmatch(image_digest) is None:
        raise GreeceShakeMapOpenQuake3121RuntimeError("invalid image digest")
    _require_authority()
    result = _base_result(execution_sha=execution_sha, image_digest=image_digest)

    try:
        runtime_verifier()
    except GreeceShakeMapOpenQuake3121RuntimeError:
        _validate_terminal_result(result)
        return result
    result["runtime_source_commit_verified"] = True
    result.update(
        {"failure_stage": "acquisition", "failure_code": _FAILURES["acquisition"]}
    )

    try:
        (grid_raw, uncertainty_raw), receipts = fetcher()
    except base.ShakeMapByteIdentityError:
        result.update(
            {
                "failure_stage": "byte_identity",
                "failure_code": _FAILURES["byte_identity"],
                "provider_file_bytes_read": True,
            }
        )
        _validate_terminal_result(result)
        return result
    except base.ShakeMapAcquisitionError as exc:
        result["provider_file_bytes_read"] = exc.completed_files > 0
        _validate_terminal_result(result)
        return result

    base._validate_receipts(receipts)
    result["provider_file_bytes_read"] = True
    try:
        identity_checker(grid_raw, uncertainty_raw)
    except base.ShakeMapByteIdentityError:
        result.update(
            {"failure_stage": "byte_identity", "failure_code": _FAILURES["byte_identity"]}
        )
        _validate_terminal_result(result)
        return result
    result["byte_identity_verified"] = True
    result.update(
        {
            "failure_stage": "profile_precondition",
            "failure_code": _FAILURES["profile_precondition"],
        }
    )

    try:
        profile = profile_checker(grid_raw, uncertainty_raw)
        base._validate_profile(profile)
    except (base.ShakeMapProfileError, base.GreeceShakeMapProfileActionError):
        _validate_terminal_result(result)
        return result
    result["trusted_profile_precondition_verified"] = True
    result.update(
        {
            "failure_stage": "native_reader",
            "failure_code": _FAILURES["native_reader"],
            "native_reader_attempted": True,
        }
    )

    try:
        native = native_reader(grid_raw, uncertainty_raw)
    except (NativeReaderRejected, base.ShakeMapByteIdentityError):
        _validate_terminal_result(result)
        return result
    expected_keys = {
        "native_row_count",
        "native_top_level_fields",
        "native_value_imts",
        "native_stddev_imts",
        "native_grid_uncertainty_coordinate_match_verified",
    }
    if type(native) is not dict or set(native) != expected_keys:
        raise GreeceShakeMapOpenQuake3121RuntimeError(
            "native reader returned invalid fields"
        )

    result.update(
        {
            "status": "pass",
            "failure_stage": None,
            "failure_code": None,
            "native_reader_acceptance_verified": True,
            **native,
        }
    )
    _validate_terminal_result(result)
    return result


def run_native_acceptance(*, execution_sha: str, image_digest: str) -> dict[str, Any]:
    return _run_native_with(
        execution_sha=execution_sha,
        image_digest=image_digest,
        runtime_verifier=verify_runtime_source_identity,
        fetcher=base._acquire_fixed_shakemap_pair,
        identity_checker=validate_fixed_bytes,
        profile_checker=base.profile_fixed_greece_shakemap_pair,
        native_reader=native_read_fixed_bytes,
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--comment-body-env", required=True)
    parser.add_argument("--expected-issue", type=int, required=True)
    parser.add_argument("--execution-sha", required=True)
    parser.add_argument("--image-digest")
    parser.add_argument("--validate-request-only", action="store_true")
    parser.add_argument("--output")
    args = parser.parse_args(argv)
    validate_request(
        os.environ.get(args.comment_body_env),
        expected_issue=args.expected_issue,
        execution_sha=args.execution_sha,
    )
    if args.validate_request_only:
        return 0
    if not args.output or not args.image_digest:
        raise GreeceShakeMapOpenQuake3121RuntimeError(
            "output path and image digest are required"
        )
    result = run_native_acceptance(
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
