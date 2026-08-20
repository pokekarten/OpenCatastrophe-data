# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Trusted-main fixed-source semantic probe for the ESRM20 Exposure-to-Site tool.

The action reads exactly three source/documentation files whose Git blob identities
were already established by the project-278 candidate-tree receipt on #291. It
verifies canonical Git blob SHA-1 before decoding or parsing, returns only bounded
content-derived facts, and never returns or persists provider source bytes.

This is evidence discovery only. Token/AST facts do not prove the historical Kosovo
generator invocation, CRS/datum, missingness semantics, site compatibility,
publication rights, or model-use authority.
"""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import os
from pathlib import Path
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

if __package__ in (None, ""):  # pragma: no cover
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts import acquire_efehr_gitlab_receipt as transport
from scripts.efehr_gitlab_receipt import PROVIDER_ROOT
from scripts.prepare_agent_action_result import LedgerError, fetch_repository_comments

REQUEST_MARKER = "<!-- oc-eq1-esrm20-sitemodel-source-semantics-request-v1 -->"
RESULT_MARKER = "<!-- oc-eq1-esrm20-sitemodel-source-semantics-result-v1 -->"
REQUEST_SCHEMA_VERSION = "oc-esrm20-sitemodel-source-semantics-request-v1"
RESULT_SCHEMA_VERSION = "oc-esrm20-sitemodel-source-semantics-result-v1"
PROFILE_SCHEMA_VERSION = "oc-esrm20-sitemodel-source-semantics-profile-v1"
SOURCE_ISSUE = 291
SCIENCE_PARENT = 284
PROJECT_ID = 278
PROJECT_PATH = "efehr/esrm20_sitemodel"
SOURCE_REF = "038c91d2bf5a07f6b54ff51639aad874d6837ea9"
TRUSTED_RESULT_LOGIN = "github-actions[bot]"
MAX_LEDGER_PAGES = 20
MAX_FILE_BYTES = 1_048_576
MAX_TOTAL_BYTES = 2_500_000
MAX_RESULT_UTF8_BYTES = 60_000
TOTAL_DEADLINE_SECONDS = 120.0
CHUNK_SIZE = 64 * 1024
MAX_TOKEN_LINES = 32
MAX_IMPORT_ROOTS = 64

SOURCE_TARGETS = (
    ("README.md", "5077a169d3fd540c53e027c4f1943e07bfce213d", "text"),
    (
        "exposure2site/exposure_to_site_tools.py",
        "e00104344b608ba528a46d84f61269f8000b385a",
        "python",
    ),
    (
        "exposure2site/node_handler.py",
        "14ee7c80d8b69a89fc669a6fc265e3e40c0358a7",
        "python",
    ),
)

PROBE_TOKENS = (
    "epsg",
    "crs",
    "wgs84",
    "projection",
    "reproject",
    "longitude",
    "latitude",
    "nodata",
    "no_data",
    "missing",
    "unknown",
    "nan",
    "none",
    "vs30",
    "xvf",
    "geology",
    "region",
    "slope",
)

_LITERAL_KEYS = (
    "epsg_4326_literal",
    "epsg_3035_literal",
    "wgs84_literal",
    "unknown_literal",
    "nan_literal",
    "nodata_literal",
    "negative_9999_literal",
    "negative_999_literal",
)

_SHA_RE = re.compile(r"^[0-9a-f]{40}$")
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_REQUESTER_RE = re.compile(r"^[A-Za-z0-9_.:@/+ -]{1,96}$")
_IMPORT_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]{0,63}$")
_REQUEST_FIELDS = {"schema_version", "issue", "target_sha", "requester"}
_PROBE_FIELDS = {"token", "count", "line_numbers", "line_numbers_complete"}
_FILE_FIELDS = {
    "repository_path",
    "expected_git_blob_sha1",
    "observed_git_blob_sha1",
    "byte_count",
    "sha256",
    "line_count",
    "kind",
    "utf8_decoded",
    "python_ast_parsed",
    "import_roots",
    "probes",
    "literal_flags",
}
_PROFILE_FIELDS = {
    "schema_version",
    "source_issue",
    "science_parent",
    "project_id",
    "project_path",
    "source_ref",
    "source_paths",
    "files",
    "file_count",
    "total_byte_count",
    "provider_source_bytes_read",
    "raw_source_returned",
    "source_semantics_profiled",
    "external_bytes_persisted",
    "exact_kosovo_generator_commit_verified",
    "crs_coordinate_semantics_verified",
    "missingness_semantics_verified",
    "site_model_compatibility_verified",
    "publication_authorized",
    "model_use_authorized",
}
_RESULT_FIELDS = {
    "schema_version",
    "source_issue",
    "science_parent",
    "target_sha",
    "execution_sha",
    "status",
    "failure_class",
    "profile",
    "provider_source_bytes_read",
    "raw_source_returned",
    "source_semantics_profiled",
    "external_bytes_persisted",
    "exact_kosovo_generator_commit_verified",
    "crs_coordinate_semantics_verified",
    "missingness_semantics_verified",
    "site_model_compatibility_verified",
    "publication_authorized",
    "model_use_authorized",
}

_OPEN_FIXED = transport._open_fixed
_VALIDATE_RESPONSE = transport._validate_exact_response
_REMAINING = transport._remaining
_SET_RESPONSE_TIMEOUT = transport._set_response_timeout
_DECLARED_LENGTH = transport._declared_length
_MONOTONIC = time.monotonic
_FETCH_COMMENTS = fetch_repository_comments


class SiteModelSourceSemanticsError(RuntimeError):
    """Fail-closed error for the fixed project-278 source semantic probe."""


def _pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise SiteModelSourceSemanticsError("duplicate JSON key")
        result[key] = value
    return result


def _reject_constant(value: str) -> Any:
    raise SiteModelSourceSemanticsError(f"non-finite JSON constant: {value}")


def _reject_float_overflow(value: str) -> float:
    parsed = float(value)
    if not (-float("inf") < parsed < float("inf")):
        raise SiteModelSourceSemanticsError("non-finite JSON number")
    return parsed


def _strict_json(text: str) -> Any:
    try:
        return json.loads(
            text,
            object_pairs_hook=_pairs,
            parse_constant=_reject_constant,
            parse_float=_reject_float_overflow,
        )
    except SiteModelSourceSemanticsError:
        raise
    except (json.JSONDecodeError, TypeError, ValueError) as exc:
        raise SiteModelSourceSemanticsError("invalid JSON") from exc


def _target(path: str) -> tuple[str, str]:
    for expected_path, blob_sha, kind in SOURCE_TARGETS:
        if path == expected_path:
            return blob_sha, kind
    raise SiteModelSourceSemanticsError("source path is outside the fixed allow-list")


def _raw_url(path: str) -> str:
    _target(path)
    encoded_path = urllib.parse.quote(path, safe="")
    encoded_ref = urllib.parse.quote(SOURCE_REF, safe="")
    return (
        f"{PROVIDER_ROOT}/api/v4/projects/{PROJECT_ID}/repository/files/"
        f"{encoded_path}/raw?ref={encoded_ref}"
    )


def _git_blob_sha1(data: bytes) -> str:
    header = f"blob {len(data)}\0".encode("ascii")
    return hashlib.sha1(header + data).hexdigest()


def _read_source(
    path: str,
    *,
    deadline: float,
    opener: Any = _OPEN_FIXED,
    monotonic: Any = _MONOTONIC,
) -> bytes:
    expected_blob, _ = _target(path)
    url = _raw_url(path)
    request = urllib.request.Request(
        url,
        headers={
            "Accept": "text/plain",
            "User-Agent": "OpenCatastrophe-ESRM20-sitemodel-source-semantics-v1",
        },
        method="GET",
    )
    try:
        with opener(request, timeout=_REMAINING(deadline, monotonic)) as response:
            _VALIDATE_RESPONSE(response, url)
            declared = _DECLARED_LENGTH(response, MAX_FILE_BYTES)
            data = bytearray()
            while True:
                remaining_budget = MAX_FILE_BYTES - len(data)
                if remaining_budget <= 0:
                    raise SiteModelSourceSemanticsError("source file exceeds byte policy")
                _SET_RESPONSE_TIMEOUT(response, _REMAINING(deadline, monotonic))
                chunk = response.read(min(CHUNK_SIZE, remaining_budget + 1))
                _REMAINING(deadline, monotonic)
                if chunk == b"":
                    break
                if type(chunk) is not bytes:
                    raise SiteModelSourceSemanticsError("provider returned non-byte source content")
                data.extend(chunk)
                if len(data) > MAX_FILE_BYTES:
                    raise SiteModelSourceSemanticsError("source file exceeds byte policy")
    except (SiteModelSourceSemanticsError, transport.EfehrAcquisitionError):
        raise
    except (OSError, urllib.error.URLError, urllib.error.HTTPError, TimeoutError) as exc:
        raise SiteModelSourceSemanticsError("fixed source acquisition failed") from exc
    result = bytes(data)
    if not result:
        raise SiteModelSourceSemanticsError("provider returned empty source file")
    if declared is not None and declared != len(result):
        raise SiteModelSourceSemanticsError("source Content-Length disagrees with bytes")
    if _git_blob_sha1(result) != expected_blob:
        raise SiteModelSourceSemanticsError("source Git blob identity drifted")
    return result


def _token_probe(lines: list[str], text_casefold: str, token: str) -> dict[str, Any]:
    count = text_casefold.count(token)
    line_numbers = [
        number
        for number, line in enumerate(lines, start=1)
        if token in line.casefold()
    ]
    return {
        "token": token,
        "count": count,
        "line_numbers": line_numbers[:MAX_TOKEN_LINES],
        "line_numbers_complete": len(line_numbers) <= MAX_TOKEN_LINES,
    }


def _literal_flags(text: str, tree: ast.AST | None) -> dict[str, bool]:
    lower = text.casefold()
    numeric_values: set[int | float] = set()
    if tree is not None:
        for node in ast.walk(tree):
            if isinstance(node, ast.Constant) and type(node.value) in (int, float):
                numeric_values.add(node.value)
            elif (
                isinstance(node, ast.UnaryOp)
                and isinstance(node.op, ast.USub)
                and isinstance(node.operand, ast.Constant)
                and type(node.operand.value) in (int, float)
            ):
                numeric_values.add(-node.operand.value)
    return {
        "epsg_4326_literal": "epsg:4326" in lower or "epsg=4326" in lower,
        "epsg_3035_literal": "epsg:3035" in lower or "epsg=3035" in lower,
        "wgs84_literal": "wgs84" in lower or "wgs 84" in lower,
        "unknown_literal": "unknown" in lower,
        "nan_literal": "nan" in lower,
        "nodata_literal": "nodata" in lower or "no_data" in lower,
        "negative_9999_literal": -9999 in numeric_values,
        "negative_999_literal": -999 in numeric_values,
    }


def _import_roots(tree: ast.AST | None) -> list[str]:
    if tree is None:
        return []
    roots: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names = [alias.name for alias in node.names]
        elif isinstance(node, ast.ImportFrom):
            names = [node.module] if node.module else []
        else:
            continue
        for name in names:
            root = name.split(".", 1)[0]
            if not _IMPORT_RE.fullmatch(root):
                raise SiteModelSourceSemanticsError("Python import root is outside policy")
            roots.add(root)
    if len(roots) > MAX_IMPORT_ROOTS:
        raise SiteModelSourceSemanticsError("Python import root set exceeds policy")
    return sorted(roots)


def _profile_file(path: str, data: bytes) -> dict[str, Any]:
    expected_blob, kind = _target(path)
    if _git_blob_sha1(data) != expected_blob:
        raise SiteModelSourceSemanticsError("source Git blob identity changed before parsing")
    try:
        text = data.decode("utf-8", errors="strict")
    except UnicodeDecodeError as exc:
        raise SiteModelSourceSemanticsError("fixed source file is not UTF-8") from exc
    if "\x00" in text:
        raise SiteModelSourceSemanticsError("fixed source file contains NUL")
    lines = text.splitlines()
    tree: ast.AST | None = None
    if kind == "python":
        try:
            tree = ast.parse(text, filename=path)
        except SyntaxError as exc:
            raise SiteModelSourceSemanticsError("fixed Python source does not parse") from exc
    probes = [_token_probe(lines, text.casefold(), token) for token in PROBE_TOKENS]
    result = {
        "repository_path": path,
        "expected_git_blob_sha1": expected_blob,
        "observed_git_blob_sha1": _git_blob_sha1(data),
        "byte_count": len(data),
        "sha256": hashlib.sha256(data).hexdigest(),
        "line_count": len(lines),
        "kind": kind,
        "utf8_decoded": True,
        "python_ast_parsed": kind == "python",
        "import_roots": _import_roots(tree),
        "probes": probes,
        "literal_flags": _literal_flags(text, tree),
    }
    _validate_file_profile(result, expected_path=path)
    return result


def profile_source_semantics(
    *,
    opener: Any = _OPEN_FIXED,
    monotonic: Any = _MONOTONIC,
) -> dict[str, Any]:
    if opener is _OPEN_FIXED and transport._open_fixed is not _OPEN_FIXED:
        raise SiteModelSourceSemanticsError("trusted EFEHR transport identity drifted")
    if (
        PROJECT_ID != 278
        or PROJECT_PATH != "efehr/esrm20_sitemodel"
        or SOURCE_REF != "038c91d2bf5a07f6b54ff51639aad874d6837ea9"
    ):
        raise SiteModelSourceSemanticsError("fixed project-278 source authority drifted")
    deadline = monotonic() + TOTAL_DEADLINE_SECONDS
    files: list[dict[str, Any]] = []
    total = 0
    for path, _, _ in SOURCE_TARGETS:
        data = _read_source(path, deadline=deadline, opener=opener, monotonic=monotonic)
        total += len(data)
        if total > MAX_TOTAL_BYTES:
            raise SiteModelSourceSemanticsError("fixed source set exceeds total byte policy")
        files.append(_profile_file(path, data))
    profile = {
        "schema_version": PROFILE_SCHEMA_VERSION,
        "source_issue": SOURCE_ISSUE,
        "science_parent": SCIENCE_PARENT,
        "project_id": PROJECT_ID,
        "project_path": PROJECT_PATH,
        "source_ref": SOURCE_REF,
        "source_paths": [item[0] for item in SOURCE_TARGETS],
        "files": files,
        "file_count": len(files),
        "total_byte_count": total,
        "provider_source_bytes_read": True,
        "raw_source_returned": False,
        "source_semantics_profiled": True,
        "external_bytes_persisted": False,
        "exact_kosovo_generator_commit_verified": False,
        "crs_coordinate_semantics_verified": False,
        "missingness_semantics_verified": False,
        "site_model_compatibility_verified": False,
        "publication_authorized": False,
        "model_use_authorized": False,
    }
    validate_profile(profile)
    return profile


def validate_request(body: object, *, expected_issue: int, execution_sha: str) -> dict[str, Any]:
    if type(expected_issue) is not int or expected_issue != SOURCE_ISSUE:
        raise SiteModelSourceSemanticsError("wrong source-semantics issue")
    if type(execution_sha) is not str or _SHA_RE.fullmatch(execution_sha) is None:
        raise SiteModelSourceSemanticsError("invalid execution SHA")
    if type(body) is not str or body.count(REQUEST_MARKER) != 1:
        raise SiteModelSourceSemanticsError("invalid source-semantics request marker")
    before, after = body.split(REQUEST_MARKER, 1)
    if before.strip() or not after.strip():
        raise SiteModelSourceSemanticsError("source-semantics request envelope is not canonical")
    request = _strict_json(after.strip())
    if type(request) is not dict or set(request) != _REQUEST_FIELDS:
        raise SiteModelSourceSemanticsError("source-semantics request fields drifted")
    if request["schema_version"] != REQUEST_SCHEMA_VERSION:
        raise SiteModelSourceSemanticsError("source-semantics request schema drifted")
    if type(request["issue"]) is not int or request["issue"] != SOURCE_ISSUE:
        raise SiteModelSourceSemanticsError("source-semantics request issue drifted")
    if request["target_sha"] != execution_sha:
        raise SiteModelSourceSemanticsError("source-semantics target is not trusted main")
    requester = request["requester"]
    if (
        type(requester) is not str
        or requester != requester.strip()
        or _REQUESTER_RE.fullmatch(requester) is None
    ):
        raise SiteModelSourceSemanticsError("invalid requester identity")
    return request


def _validate_file_profile(value: object, *, expected_path: str) -> dict[str, Any]:
    if type(value) is not dict or set(value) != _FILE_FIELDS:
        raise SiteModelSourceSemanticsError("source file profile fields drifted")
    expected_blob, expected_kind = _target(expected_path)
    exact = (
        ("repository_path", expected_path),
        ("expected_git_blob_sha1", expected_blob),
        ("observed_git_blob_sha1", expected_blob),
        ("kind", expected_kind),
        ("utf8_decoded", True),
        ("python_ast_parsed", expected_kind == "python"),
    )
    for field, expected in exact:
        if type(value.get(field)) is not type(expected) or value.get(field) != expected:
            raise SiteModelSourceSemanticsError(f"source file profile drifted at {field}")
    if type(value["byte_count"]) is not int or isinstance(value["byte_count"], bool) or not (
        1 <= value["byte_count"] <= MAX_FILE_BYTES
    ):
        raise SiteModelSourceSemanticsError("source file byte count is invalid")
    if type(value["sha256"]) is not str or _SHA256_RE.fullmatch(value["sha256"]) is None:
        raise SiteModelSourceSemanticsError("source file SHA-256 is invalid")
    if type(value["line_count"]) is not int or isinstance(value["line_count"], bool) or not (
        1 <= value["line_count"] <= MAX_FILE_BYTES
    ):
        raise SiteModelSourceSemanticsError("source file line count is invalid")
    roots = value["import_roots"]
    if type(roots) is not list or len(roots) > MAX_IMPORT_ROOTS or roots != sorted(set(roots)):
        raise SiteModelSourceSemanticsError("source import roots are not canonical")
    for root in roots:
        if type(root) is not str or _IMPORT_RE.fullmatch(root) is None:
            raise SiteModelSourceSemanticsError("source import root is invalid")
    if expected_kind == "text" and roots:
        raise SiteModelSourceSemanticsError("README unexpectedly carries import roots")
    probes = value["probes"]
    if type(probes) is not list or len(probes) != len(PROBE_TOKENS):
        raise SiteModelSourceSemanticsError("source probe count drifted")
    for expected_token, probe in zip(PROBE_TOKENS, probes):
        if type(probe) is not dict or set(probe) != _PROBE_FIELDS:
            raise SiteModelSourceSemanticsError("source probe shape drifted")
        if probe["token"] != expected_token:
            raise SiteModelSourceSemanticsError("source probe token order drifted")
        count = probe["count"]
        line_numbers = probe["line_numbers"]
        complete = probe["line_numbers_complete"]
        if type(count) is not int or isinstance(count, bool) or not (0 <= count <= MAX_FILE_BYTES):
            raise SiteModelSourceSemanticsError("source probe count is invalid")
        if type(line_numbers) is not list or len(line_numbers) > MAX_TOKEN_LINES:
            raise SiteModelSourceSemanticsError("source probe line list exceeds policy")
        if type(complete) is not bool:
            raise SiteModelSourceSemanticsError("source probe completeness flag is invalid")
        if line_numbers != sorted(set(line_numbers)):
            raise SiteModelSourceSemanticsError("source probe line numbers are not canonical")
        for line in line_numbers:
            if type(line) is not int or isinstance(line, bool) or not (1 <= line <= value["line_count"]):
                raise SiteModelSourceSemanticsError("source probe line number is invalid")
        if count == 0 and line_numbers:
            raise SiteModelSourceSemanticsError("zero-count source probe carries line numbers")
        if complete and count > 0 and not line_numbers:
            raise SiteModelSourceSemanticsError("complete nonzero source probe lacks a line")
    flags = value["literal_flags"]
    if type(flags) is not dict or set(flags) != set(_LITERAL_KEYS):
        raise SiteModelSourceSemanticsError("source literal flags drifted")
    if any(type(flags[key]) is not bool for key in _LITERAL_KEYS):
        raise SiteModelSourceSemanticsError("source literal flag is not boolean")
    return value


def validate_profile(value: object) -> dict[str, Any]:
    if type(value) is not dict or set(value) != _PROFILE_FIELDS:
        raise SiteModelSourceSemanticsError("source-semantics profile fields drifted")
    exact = (
        ("schema_version", PROFILE_SCHEMA_VERSION),
        ("source_issue", SOURCE_ISSUE),
        ("science_parent", SCIENCE_PARENT),
        ("project_id", PROJECT_ID),
        ("project_path", PROJECT_PATH),
        ("source_ref", SOURCE_REF),
        ("source_paths", [item[0] for item in SOURCE_TARGETS]),
        ("file_count", len(SOURCE_TARGETS)),
        ("provider_source_bytes_read", True),
        ("raw_source_returned", False),
        ("source_semantics_profiled", True),
        ("external_bytes_persisted", False),
        ("exact_kosovo_generator_commit_verified", False),
        ("crs_coordinate_semantics_verified", False),
        ("missingness_semantics_verified", False),
        ("site_model_compatibility_verified", False),
        ("publication_authorized", False),
        ("model_use_authorized", False),
    )
    for field, expected in exact:
        if type(value.get(field)) is not type(expected) or value.get(field) != expected:
            raise SiteModelSourceSemanticsError(f"source-semantics profile drifted at {field}")
    files = value["files"]
    if type(files) is not list or len(files) != len(SOURCE_TARGETS):
        raise SiteModelSourceSemanticsError("source-semantics file count drifted")
    for file_profile, (path, _, _) in zip(files, SOURCE_TARGETS):
        _validate_file_profile(file_profile, expected_path=path)
    total = value["total_byte_count"]
    if type(total) is not int or isinstance(total, bool) or not (1 <= total <= MAX_TOTAL_BYTES):
        raise SiteModelSourceSemanticsError("source-semantics total bytes are invalid")
    if total != sum(item["byte_count"] for item in files):
        raise SiteModelSourceSemanticsError("source-semantics total bytes disagree")
    return value


def _base_result(*, execution_sha: str) -> dict[str, Any]:
    return {
        "schema_version": RESULT_SCHEMA_VERSION,
        "source_issue": SOURCE_ISSUE,
        "science_parent": SCIENCE_PARENT,
        "target_sha": execution_sha,
        "execution_sha": execution_sha,
        "provider_source_bytes_read": False,
        "raw_source_returned": False,
        "source_semantics_profiled": False,
        "external_bytes_persisted": False,
        "exact_kosovo_generator_commit_verified": False,
        "crs_coordinate_semantics_verified": False,
        "missingness_semantics_verified": False,
        "site_model_compatibility_verified": False,
        "publication_authorized": False,
        "model_use_authorized": False,
    }


def parse_terminal_result(body: object, *, execution_sha: str) -> bool:
    if type(execution_sha) is not str or _SHA_RE.fullmatch(execution_sha) is None:
        raise SiteModelSourceSemanticsError("invalid execution SHA")
    if type(body) is not str or RESULT_MARKER not in body:
        return False
    if body.count(RESULT_MARKER) != 1:
        raise SiteModelSourceSemanticsError("source-semantics result marker is malformed")
    before, after = body.split(RESULT_MARKER, 1)
    if before.strip() or not after.strip():
        raise SiteModelSourceSemanticsError("source-semantics result envelope is malformed")
    result = _strict_json(after.strip())
    if type(result) is not dict or set(result) != _RESULT_FIELDS:
        raise SiteModelSourceSemanticsError("source-semantics result fields drifted")
    target = result["target_sha"]
    observed_execution = result["execution_sha"]
    if (
        type(target) is not str
        or _SHA_RE.fullmatch(target) is None
        or type(observed_execution) is not str
        or _SHA_RE.fullmatch(observed_execution) is None
        or target != observed_execution
    ):
        raise SiteModelSourceSemanticsError("source-semantics result SHA binding is invalid")
    own_sha = target
    for field, expected in _base_result(execution_sha=own_sha).items():
        if field in {"provider_source_bytes_read", "source_semantics_profiled"}:
            continue
        if result.get(field) != expected or type(result.get(field)) is not type(expected):
            raise SiteModelSourceSemanticsError(f"source-semantics result drifted at {field}")
    status = result["status"]
    if status == "pass":
        if result["failure_class"] is not None:
            raise SiteModelSourceSemanticsError("source-semantics PASS carries failure")
        validate_profile(result["profile"])
        if (
            result["provider_source_bytes_read"] is not True
            or result["source_semantics_profiled"] is not True
        ):
            raise SiteModelSourceSemanticsError("source-semantics PASS did not bind provider evidence")
    elif status == "blocked":
        if (
            result["provider_source_bytes_read"] is not False
            or result["source_semantics_profiled"] is not False
        ):
            raise SiteModelSourceSemanticsError("source-semantics BLOCKED widened provider evidence")
        if result["failure_class"] not in {
            "source_acquisition_or_profile_failure",
            "result_publication_limit",
        } or result["profile"] is not None:
            raise SiteModelSourceSemanticsError("source-semantics blocked result widened evidence")
    elif status == "duplicate":
        if (
            result["provider_source_bytes_read"] is not False
            or result["source_semantics_profiled"] is not False
        ):
            raise SiteModelSourceSemanticsError("source-semantics duplicate widened provider evidence")
        if result["failure_class"] is not None or result["profile"] is not None:
            raise SiteModelSourceSemanticsError("source-semantics duplicate carries evidence")
    else:
        raise SiteModelSourceSemanticsError("source-semantics result has non-terminal status")
    return own_sha == execution_sha


def has_terminal_result(*, repository: str, token: str, execution_sha: str) -> bool:
    try:
        comments = _FETCH_COMMENTS(
            repository, token, issue=SOURCE_ISSUE, max_pages=MAX_LEDGER_PAGES
        )
    except LedgerError as exc:
        raise SiteModelSourceSemanticsError("source-semantics result ledger is incomplete") from exc
    match_seen = False
    for comment in comments:
        if type(comment) is not dict:
            raise SiteModelSourceSemanticsError("source-semantics ledger contains non-object")
        user = comment.get("user")
        login = user.get("login") if type(user) is dict else None
        if login != TRUSTED_RESULT_LOGIN:
            continue
        if parse_terminal_result(comment.get("body"), execution_sha=execution_sha):
            match_seen = True
    return match_seen


def execute_profile(*, repository: str, token: str, execution_sha: str) -> dict[str, Any]:
    if (
        transport._open_fixed is not _OPEN_FIXED
        or fetch_repository_comments is not _FETCH_COMMENTS
    ):
        raise SiteModelSourceSemanticsError("trusted source-semantics authority drifted")
    if has_terminal_result(repository=repository, token=token, execution_sha=execution_sha):
        return {
            **_base_result(execution_sha=execution_sha),
            "status": "duplicate",
            "failure_class": None,
            "profile": None,
        }
    try:
        source_profile = profile_source_semantics()
        validate_profile(source_profile)
        result = {
            **_base_result(execution_sha=execution_sha),
            "status": "pass",
            "failure_class": None,
            "profile": source_profile,
            "provider_source_bytes_read": True,
            "source_semantics_profiled": True,
        }
    except (SiteModelSourceSemanticsError, transport.EfehrAcquisitionError):
        result = {
            **_base_result(execution_sha=execution_sha),
            "status": "blocked",
            "failure_class": "source_acquisition_or_profile_failure",
            "profile": None,
        }
    encoded = json.dumps(result, sort_keys=True, separators=(",", ":")).encode("utf-8")
    if len(RESULT_MARKER.encode("utf-8")) + 1 + len(encoded) > MAX_RESULT_UTF8_BYTES:
        result = {
            **_base_result(execution_sha=execution_sha),
            "status": "blocked",
            "failure_class": "result_publication_limit",
            "profile": None,
        }
        encoded = json.dumps(result, sort_keys=True, separators=(",", ":")).encode("utf-8")
    parse_terminal_result(
        RESULT_MARKER + "\n" + encoded.decode("utf-8"), execution_sha=execution_sha
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
        raise SiteModelSourceSemanticsError("GitHub token is unavailable")
    result = execute_profile(
        repository=args.repository, token=token, execution_sha=args.execution_sha
    )
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(result, sort_keys=True, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
