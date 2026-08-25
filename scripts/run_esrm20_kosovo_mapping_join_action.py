# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Execute the bounded Kosovo taxonomy -> ESRM20 risk-id join on trusted main.

The runner accepts only one owner-gated Issue #283 request bound to the exact
execution SHA. Before provider I/O it scans the complete bounded Issue #283
result ledger. It then transiently re-materializes the two already-receipted
EFEHR objects, re-verifies both byte identities, and invokes the reviewed pure
join kernel. Provider bytes are never persisted or returned.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

if __package__ in (None, ""):  # pragma: no cover - direct script execution path
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts import acquire_efehr_gitlab_receipt as transport
from scripts import efehr_gitlab_receipt as receipt
from scripts import join_esrm20_kosovo_taxonomy_mapping as join_kernel
from scripts import profile_efehr_esrm20_mapping_structure as mapping_source
from scripts import profile_efehr_kosovo_exposure as exposure_source
from scripts.prepare_agent_action_result import LedgerError, fetch_repository_comments

SCHEMA_VERSION = "oc-esrm20-kosovo-mapping-join-execution-v1"
REQUEST_SCHEMA_VERSION = "oc-esrm20-kosovo-mapping-join-request-v1"
REQUEST_MARKER = "<!-- oc-eq1-esrm20-kosovo-mapping-join-request-v1 -->"
RESULT_MARKER = "<!-- oc-eq1-esrm20-kosovo-mapping-join-result-v1 -->"
SOURCE_ISSUE = 283
TRUSTED_RESULT_LOGIN = "github-actions[bot]"
TOTAL_DEADLINE_SECONDS = 45.0
MAX_RESULT_UTF8_BYTES = 55_000
MAX_LEDGER_PAGES = 20
EXPECTED_TAXONOMY_COUNT = 86
EXPECTED_TAXONOMY_VALUE_SET_SHA256 = (
    "d5e6fe4e32489cdd2222b6b3facfd30937e2af61bbcf0ecead37ccf97202a945"
)

_SHA_RE = re.compile(r"^[0-9a-f]{40}$")
_REQUESTER_RE = re.compile(r"^[A-Za-z0-9_.:@/+ -]{1,96}$")
_REQUEST_FIELDS = {"schema_version", "issue", "target_sha", "requester"}

_EXPOSURE = {
    "source_issue": 282,
    "dataset_id": "efehr.esrm20.european-exposure-model.v1.0",
    "project_id": 186,
    "project_path": "efehr/esrm20_exposure",
    "commit_sha": "900433ada80fbb424c0976c34d72eeef97bab1af",
    "repository_path": "_exposure_models/Exposure_Model_Kosovo_Res.csv",
    "byte_count": 316_789,
    "sha256": "4d562ad4925c527d518834b8dcd39a083cfd3b87b622031a84958ae7b4d8c5ea",
}
_MAPPING = {
    "source_issue": 283,
    "dataset_id": "efehr.esrm20.risk-inputs.v1.0",
    "project_id": 269,
    "project_path": "efehr/esrm20",
    "commit_sha": "05f83bbc9df81d02ee8ddb1801d9d781355ce783",
    "repository_path": "Vulnerability/esrm20_exposure_vulnerability_mapping.csv",
    "byte_count": 83_585,
    "sha256": "94b9ee800e9435a346ca200ecf34d0d46c8d8b895cc56e3be85c323006b4ee4c",
}

_OPEN_FIXED = transport._open_fixed
_READ_BOUNDED = transport._read_bounded
_REMAINING = transport._remaining
_VALIDATE_RESPONSE = transport._validate_exact_response
_VALIDATE_TARGET = receipt.validate_target
_RAW_FILE_API_URL = receipt.raw_file_api_url
_JOIN = join_kernel.join_verified_kosovo_taxonomy_mapping
_JOIN_WEIGHT = join_kernel._weight
_JOIN_BOUNDED_LITERAL = join_kernel._is_bounded_literal
_FETCH_COMMENTS = fetch_repository_comments
_MONOTONIC = time.monotonic


class KosovoMappingJoinExecutionError(RuntimeError):
    """Fail-closed trusted execution error."""


def _pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise KosovoMappingJoinExecutionError("duplicate JSON key")
        result[key] = value
    return result


def _reject_constant(value: str) -> Any:
    raise KosovoMappingJoinExecutionError(f"non-finite JSON constant: {value}")


def validate_request(
    body: object, *, expected_issue: int, execution_sha: str
) -> dict[str, Any]:
    if type(expected_issue) is not int or expected_issue != SOURCE_ISSUE:
        raise KosovoMappingJoinExecutionError("wrong mapping-join issue")
    if type(execution_sha) is not str or not _SHA_RE.fullmatch(execution_sha):
        raise KosovoMappingJoinExecutionError("invalid execution SHA")
    if type(body) is not str or body.count(REQUEST_MARKER) != 1:
        raise KosovoMappingJoinExecutionError("invalid mapping-join request marker")
    before, after = body.split(REQUEST_MARKER, 1)
    if before.strip() or not after.strip():
        raise KosovoMappingJoinExecutionError("mapping-join request envelope is not canonical")
    try:
        request = json.loads(
            after.strip(),
            object_pairs_hook=_pairs,
            parse_constant=_reject_constant,
        )
    except KosovoMappingJoinExecutionError:
        raise
    except (json.JSONDecodeError, TypeError, ValueError) as exc:
        raise KosovoMappingJoinExecutionError("invalid mapping-join request JSON") from exc
    if type(request) is not dict or set(request) != _REQUEST_FIELDS:
        raise KosovoMappingJoinExecutionError("mapping-join request fields drifted")
    if request["schema_version"] != REQUEST_SCHEMA_VERSION:
        raise KosovoMappingJoinExecutionError("unsupported mapping-join request schema")
    if type(request["issue"]) is not int or request["issue"] != SOURCE_ISSUE:
        raise KosovoMappingJoinExecutionError("mapping-join request issue drifted")
    if request["target_sha"] != execution_sha:
        raise KosovoMappingJoinExecutionError("mapping-join request target is not trusted main")
    requester = request["requester"]
    if (
        type(requester) is not str
        or requester != requester.strip()
        or not _REQUESTER_RE.fullmatch(requester)
    ):
        raise KosovoMappingJoinExecutionError("invalid requester identity")
    return request


def _require_authority() -> None:
    identities = (
        (transport._open_fixed, _OPEN_FIXED, "transport"),
        (transport._read_bounded, _READ_BOUNDED, "bounded reader"),
        (transport._remaining, _REMAINING, "deadline helper"),
        (transport._validate_exact_response, _VALIDATE_RESPONSE, "response validator"),
        (receipt.validate_target, _VALIDATE_TARGET, "target validator"),
        (receipt.raw_file_api_url, _RAW_FILE_API_URL, "raw URL builder"),
        (join_kernel.join_verified_kosovo_taxonomy_mapping, _JOIN, "join kernel"),
        (join_kernel._weight, _JOIN_WEIGHT, "join weight parser"),
        (join_kernel._is_bounded_literal, _JOIN_BOUNDED_LITERAL, "join literal validator"),
        (fetch_repository_comments, _FETCH_COMMENTS, "ledger reader"),
        (time.monotonic, _MONOTONIC, "monotonic clock"),
    )
    for observed, expected, label in identities:
        if observed is not expected:
            raise KosovoMappingJoinExecutionError(
                f"trusted mapping-join {label} authority drifted"
            )

    module_values = (
        (exposure_source.SOURCE_ISSUE, _EXPOSURE["source_issue"], "exposure source issue"),
        (exposure_source.DATASET_ID, _EXPOSURE["dataset_id"], "exposure dataset"),
        (exposure_source.PROJECT_ID, _EXPOSURE["project_id"], "exposure project"),
        (exposure_source.PROJECT_PATH, _EXPOSURE["project_path"], "exposure project path"),
        (exposure_source.COMMIT_SHA, _EXPOSURE["commit_sha"], "exposure commit"),
        (exposure_source.REPOSITORY_PATH, _EXPOSURE["repository_path"], "exposure path"),
        (exposure_source.EXPECTED_BYTE_COUNT, _EXPOSURE["byte_count"], "exposure byte count"),
        (exposure_source.EXPECTED_SHA256, _EXPOSURE["sha256"], "exposure SHA-256"),
        (mapping_source.SOURCE_ISSUE, _MAPPING["source_issue"], "mapping source issue"),
        (mapping_source.DATASET_ID, _MAPPING["dataset_id"], "mapping dataset"),
        (mapping_source.PROJECT_ID, _MAPPING["project_id"], "mapping project"),
        (mapping_source.PROJECT_PATH, _MAPPING["project_path"], "mapping project path"),
        (mapping_source.COMMIT_SHA, _MAPPING["commit_sha"], "mapping commit"),
        (mapping_source.REPOSITORY_PATH, _MAPPING["repository_path"], "mapping path"),
        (mapping_source.EXPECTED_BYTE_COUNT, _MAPPING["byte_count"], "mapping byte count"),
        (mapping_source.EXPECTED_SHA256, _MAPPING["sha256"], "mapping SHA-256"),
    )
    for observed, expected, label in module_values:
        if type(observed) is not type(expected) or observed != expected:
            raise KosovoMappingJoinExecutionError(f"trusted {label} drifted")


def _validate_source_identity(
    observed: object, expected: dict[str, Any], *, taxonomy: bool = False
) -> None:
    if type(observed) is not dict:
        raise KosovoMappingJoinExecutionError("trusted join source identity is absent")
    required_fields = (
        "dataset_id",
        "project_id",
        "project_path",
        "commit_sha",
        "repository_path",
        "byte_count",
        "sha256",
    )
    for field in required_fields:
        value = observed.get(field)
        required = expected[field]
        if type(value) is not type(required) or value != required:
            raise KosovoMappingJoinExecutionError(
                f"trusted join source identity drifted at {field}"
            )
    if taxonomy:
        taxonomy_count = observed.get("taxonomy_count")
        if type(taxonomy_count) is not int or taxonomy_count != EXPECTED_TAXONOMY_COUNT:
            raise KosovoMappingJoinExecutionError("trusted taxonomy count drifted")
        if observed.get("taxonomy_value_set_sha256") != EXPECTED_TAXONOMY_VALUE_SET_SHA256:
            raise KosovoMappingJoinExecutionError("trusted taxonomy value-set identity drifted")
    else:
        if observed.get("headers") != list(join_kernel.EXPECTED_MAPPING_HEADER):
            raise KosovoMappingJoinExecutionError("trusted mapping header identity drifted")


def _validate_join_payload(join: object) -> None:
    if type(join) is not dict:
        raise KosovoMappingJoinExecutionError("trusted mapping-join payload is absent")
    expected_scalars = (
        ("schema_version", join_kernel.SCHEMA_VERSION),
        ("source_issue", SOURCE_ISSUE),
        ("semantic_decision_issue", 410),
        ("taxonomy_matching", "exact_literal_equality_only"),
        ("normalization_applied", False),
        ("wildcard_or_fallback_matching_applied", False),
        ("mapping_weight_rule", "positive_finite_float_sum_within_openquake_1e-7"),
        ("bounded_derived_disclosure_authorized", True),
        ("vulnerability_file_selection_authorized", False),
        ("raw_mapping_rows_returned", False),
        ("external_bytes_persisted", False),
        ("publication_authorized", False),
        ("model_use_authorized", False),
    )
    for field, required in expected_scalars:
        value = join.get(field)
        if type(value) is not type(required) or value != required:
            raise KosovoMappingJoinExecutionError(
                f"trusted mapping-join payload drifted at {field}"
            )

    _validate_source_identity(join.get("taxonomy_source"), _EXPOSURE, taxonomy=True)
    _validate_source_identity(join.get("mapping_source"), _MAPPING, taxonomy=False)

    rights = join.get("rights")
    if type(rights) is not dict or set(rights) != {
        "provider",
        "license_id",
        "attribution_required",
        "source_reviews",
        "transformation_notice",
    }:
        raise KosovoMappingJoinExecutionError("trusted mapping-join rights shape drifted")
    rights_expected = (
        ("provider", join_kernel.RIGHTS_PROVIDER),
        ("license_id", join_kernel.RIGHTS_LICENSE_ID),
        ("attribution_required", True),
        ("source_reviews", list(join_kernel.RIGHTS_SOURCE_REVIEWS)),
        ("transformation_notice", join_kernel.RIGHTS_TRANSFORMATION_NOTICE),
    )
    for field, required in rights_expected:
        value = rights.get(field)
        if type(value) is not type(required) or value != required:
            raise KosovoMappingJoinExecutionError(
                f"trusted mapping-join attribution drifted at {field}"
            )

    counts = join.get("classification_counts")
    if (
        type(counts) is not dict
        or set(counts) != {"resolved", "unsupported", "ambiguous"}
        or any(
            type(value) is not int or isinstance(value, bool) or value < 0
            for value in counts.values()
        )
        or sum(counts.values()) != EXPECTED_TAXONOMY_COUNT
    ):
        raise KosovoMappingJoinExecutionError("trusted mapping-join counts are invalid")

    records = join.get("records")
    if type(records) is not list or len(records) != EXPECTED_TAXONOMY_COUNT:
        raise KosovoMappingJoinExecutionError("trusted mapping-join record set is invalid")
    observed_counts = {status: 0 for status in ("resolved", "unsupported", "ambiguous")}
    taxonomies: list[str] = []
    ambiguous_reasons = {
        "matched_row_not_canonical",
        "duplicate_risk_id_semantics",
        "weights_outside_openquake_precision",
    }
    for record in records:
        if type(record) is not dict or set(record) != {
            "taxonomy",
            "status",
            "reason_code",
            "targets",
        }:
            raise KosovoMappingJoinExecutionError("trusted mapping-join record shape drifted")
        taxonomy = record["taxonomy"]
        if not _JOIN_BOUNDED_LITERAL(
            taxonomy, max_utf8_bytes=join_kernel.MAX_TAXONOMY_UTF8_BYTES
        ):
            raise KosovoMappingJoinExecutionError("trusted taxonomy literal is unsafe")
        taxonomies.append(taxonomy)
        status = record["status"]
        if status not in observed_counts:
            raise KosovoMappingJoinExecutionError("trusted mapping status is unknown")
        observed_counts[status] += 1
        reason = record["reason_code"]
        targets = record["targets"]
        if type(targets) is not list:
            raise KosovoMappingJoinExecutionError("trusted mapping targets are not a list")
        if status == "resolved":
            if reason != "exact_mapping_rows_valid" or not targets:
                raise KosovoMappingJoinExecutionError("trusted resolved record is incomplete")
            risk_ids: list[str] = []
            weights: list[float] = []
            for target in targets:
                if type(target) is not dict or set(target) != {"risk_id", "weight"}:
                    raise KosovoMappingJoinExecutionError("trusted mapping target shape drifted")
                risk_id = target["risk_id"]
                if (
                    not _JOIN_BOUNDED_LITERAL(
                        risk_id, max_utf8_bytes=join_kernel.MAX_RISK_ID_UTF8_BYTES
                    )
                    or risk_id != risk_id.strip()
                ):
                    raise KosovoMappingJoinExecutionError("trusted risk-id literal is unsafe")
                weight_text = target["weight"]
                weight = _JOIN_WEIGHT(weight_text)
                if weight is None:
                    raise KosovoMappingJoinExecutionError("trusted mapping weight is invalid")
                risk_ids.append(risk_id)
                weights.append(weight)
            if risk_ids != sorted(risk_ids) or len(set(risk_ids)) != len(risk_ids):
                raise KosovoMappingJoinExecutionError("trusted resolved risk IDs are not canonical")
            if abs(sum(weights) - 1.0) > join_kernel.OPENQUAKE_WEIGHT_PRECISION:
                raise KosovoMappingJoinExecutionError("trusted resolved weights fail OpenQuake precision")
        elif status == "unsupported":
            if reason != "no_exact_mapping_row" or targets:
                raise KosovoMappingJoinExecutionError("trusted unsupported record drifted")
        else:
            if reason not in ambiguous_reasons or targets:
                raise KosovoMappingJoinExecutionError("trusted ambiguous record drifted")

    if taxonomies != sorted(taxonomies) or len(set(taxonomies)) != len(taxonomies):
        raise KosovoMappingJoinExecutionError("trusted taxonomy record order is not canonical")
    if observed_counts != counts:
        raise KosovoMappingJoinExecutionError("trusted mapping-join counts disagree with records")


def _parse_terminal_result(body: object, *, execution_sha: str) -> bool:
    if type(body) is not str or RESULT_MARKER not in body:
        return False
    if body.count(RESULT_MARKER) != 1:
        raise KosovoMappingJoinExecutionError("trusted mapping-join result marker is malformed")
    before, after = body.split(RESULT_MARKER, 1)
    if before.strip() or not after.strip():
        raise KosovoMappingJoinExecutionError("trusted mapping-join result envelope is malformed")
    try:
        result = json.loads(
            after.strip(),
            object_pairs_hook=_pairs,
            parse_constant=_reject_constant,
        )
    except KosovoMappingJoinExecutionError:
        raise
    except (json.JSONDecodeError, TypeError, ValueError) as exc:
        raise KosovoMappingJoinExecutionError("trusted mapping-join result JSON is malformed") from exc
    if type(result) is not dict or set(result) != {
        "schema_version",
        "source_issue",
        "status",
        "target_sha",
        "execution_sha",
        "join",
        "external_bytes_persisted",
        "publication_authorized",
        "model_use_authorized",
    }:
        raise KosovoMappingJoinExecutionError("trusted mapping-join execution shape drifted")
    expected = (
        ("schema_version", SCHEMA_VERSION),
        ("source_issue", SOURCE_ISSUE),
        ("status", "pass"),
        ("target_sha", execution_sha),
        ("execution_sha", execution_sha),
        ("external_bytes_persisted", False),
        ("publication_authorized", False),
        ("model_use_authorized", False),
    )
    for field, required in expected:
        observed = result.get(field)
        if type(observed) is not type(required) or observed != required:
            raise KosovoMappingJoinExecutionError(
                f"trusted mapping-join result drifted at {field}"
            )
    _validate_join_payload(result.get("join"))
    return True


def has_terminal_result(
    *, repository: str, token: str, execution_sha: str, opener: Any | None = None
) -> bool:
    kwargs: dict[str, Any] = {"issue": SOURCE_ISSUE, "max_pages": MAX_LEDGER_PAGES}
    if opener is not None:
        kwargs["opener"] = opener
    try:
        comments = _FETCH_COMMENTS(repository, token, **kwargs)
    except LedgerError as exc:
        raise KosovoMappingJoinExecutionError("mapping-join result ledger is incomplete") from exc
    for comment in comments:
        if type(comment) is not dict:
            raise KosovoMappingJoinExecutionError("mapping-join ledger contains a non-object")
        user = comment.get("user")
        login = user.get("login") if type(user) is dict else None
        if login != TRUSTED_RESULT_LOGIN:
            continue
        if _parse_terminal_result(comment.get("body"), execution_sha=execution_sha):
            return True
    return False


def _acquire_exact(spec: dict[str, Any], *, deadline: float) -> bytes:
    try:
        target = _VALIDATE_TARGET(
            source_issue=spec["source_issue"],
            dataset_id=spec["dataset_id"],
            project_id=spec["project_id"],
            commit_sha=spec["commit_sha"],
            repository_path=spec["repository_path"],
        )
        if target.project_path != spec["project_path"]:
            raise KosovoMappingJoinExecutionError("trusted provider project path drifted")
        url = _RAW_FILE_API_URL(target)
        request = urllib.request.Request(
            url,
            headers={
                "Accept": "text/csv,text/plain;q=0.9,application/octet-stream;q=0.8",
                "User-Agent": "OpenCatastrophe-ESRM20-Kosovo-mapping-join-v1",
            },
            method="GET",
        )
        with _OPEN_FIXED(request, timeout=_REMAINING(deadline, _MONOTONIC)) as response:
            _VALIDATE_RESPONSE(response, url)
            payload = bytes(
                _READ_BOUNDED(
                    response,
                    deadline=deadline,
                    maximum=spec["byte_count"],
                    monotonic=_MONOTONIC,
                )
            )
    except KosovoMappingJoinExecutionError:
        raise
    except (
        transport.EfehrAcquisitionError,
        receipt.EfehrReceiptError,
        urllib.error.URLError,
        urllib.error.HTTPError,
        OSError,
        TimeoutError,
    ):
        raise KosovoMappingJoinExecutionError("trusted EFEHR acquisition failed closed") from None
    if len(payload) != spec["byte_count"]:
        raise KosovoMappingJoinExecutionError("trusted EFEHR byte count drifted")
    if hashlib.sha256(payload).hexdigest() != spec["sha256"]:
        raise KosovoMappingJoinExecutionError("trusted EFEHR SHA-256 drifted")
    return payload


def execute_join(
    *, repository: str, token: str, execution_sha: str
) -> dict[str, Any]:
    _require_authority()
    if has_terminal_result(
        repository=repository, token=token, execution_sha=execution_sha
    ):
        return {
            "schema_version": SCHEMA_VERSION,
            "source_issue": SOURCE_ISSUE,
            "status": "duplicate",
            "target_sha": execution_sha,
            "execution_sha": execution_sha,
            "external_bytes_persisted": False,
            "publication_authorized": False,
            "model_use_authorized": False,
        }

    deadline = _MONOTONIC() + TOTAL_DEADLINE_SECONDS
    exposure_raw = _acquire_exact(_EXPOSURE, deadline=deadline)
    mapping_raw = _acquire_exact(_MAPPING, deadline=deadline)
    try:
        join = _JOIN(exposure_raw, mapping_raw)
    except join_kernel.KosovoMappingJoinError as exc:
        raise KosovoMappingJoinExecutionError("verified mapping join failed closed") from exc
    finally:
        exposure_raw = b""
        mapping_raw = b""

    _validate_join_payload(join)
    result = {
        "schema_version": SCHEMA_VERSION,
        "source_issue": SOURCE_ISSUE,
        "status": "pass",
        "target_sha": execution_sha,
        "execution_sha": execution_sha,
        "join": join,
        "external_bytes_persisted": False,
        "publication_authorized": False,
        "model_use_authorized": False,
    }
    encoded = json.dumps(result, sort_keys=True, separators=(",", ":")).encode("utf-8")
    if len(encoded) > MAX_RESULT_UTF8_BYTES:
        raise KosovoMappingJoinExecutionError("bounded mapping-join result exceeds publication limit")
    _parse_terminal_result(
        RESULT_MARKER + "\n" + encoded.decode("utf-8"),
        execution_sha=execution_sha,
    )
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

    body = os.environ.get(args.comment_body_env)
    validate_request(
        body,
        expected_issue=args.expected_issue,
        execution_sha=args.execution_sha,
    )
    if args.validate_request_only:
        return 0
    if not args.repository or not args.token_env or not args.output:
        parser.error("--repository, --token-env and --output are required for execution")
    token = os.environ.get(args.token_env)
    if not token:
        raise KosovoMappingJoinExecutionError("GitHub ledger token is absent")

    result = execute_join(
        repository=args.repository,
        token=token,
        execution_sha=args.execution_sha,
    )
    Path(args.output).write_text(
        json.dumps(result, sort_keys=True, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())