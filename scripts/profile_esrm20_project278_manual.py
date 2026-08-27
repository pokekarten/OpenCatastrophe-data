# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Bounded trusted-main content profile for the frozen ESRM20 project-278 PDF.

The production path can acquire only one immutable provider object and verifies
its already-trusted byte count and SHA-256 before PDF parsing. The emitted
profile contains finite mention tokens and page numbers only; raw PDF text is
never returned or persisted. A PASS proves mechanical content profiling, not
scientific interpretation or CRS/site-model compatibility.
"""

from __future__ import annotations

import argparse
import hashlib
import http.client
import io
import json
import os
import re
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Callable

from scripts.acquire_efehr_gitlab_receipt import (
    EfehrAcquisitionError,
    TOTAL_DEADLINE_SECONDS,
    _DeadlineStream,
    _declared_length,
    _open_fixed,
    _remaining,
    _validate_exact_response,
)
from scripts.efehr_gitlab_receipt import (
    EfehrReceiptError,
    raw_file_api_url,
    validate_target,
)
from scripts.prepare_agent_action_result import LedgerError, fetch_repository_comments

REQUEST_MARKER = "<!-- oc-eq1-esrm20-project278-manual-content-profile-request-v1 -->"
RESULT_MARKER = "<!-- oc-eq1-esrm20-project278-manual-content-profile-result-v1 -->"
REQUEST_SCHEMA_VERSION = "oc-esrm20-project278-manual-content-profile-request-v1"
RESULT_SCHEMA_VERSION = "oc-esrm20-project278-manual-content-profile-result-v1"
PROFILE_SCHEMA_VERSION = "oc-esrm20-project278-manual-content-profile-v1"
ACTION = "esrm20_project278_manual_content_profile"
CONTROL_ISSUE = 291
DATASET_ID = "efehr.esrm20.sitemodel-source"
PROJECT_ID = 278
PROJECT_PATH = "efehr/esrm20_sitemodel"
COMMIT_SHA = "038c91d2bf5a07f6b54ff51639aad874d6837ea9"
REPOSITORY_PATH = "ExposureReadme.pdf"
EXPECTED_BYTE_COUNT = 2_121_105
EXPECTED_SHA256 = "6a69d92ecb7df5e9b31c3609246baadff24e0f59ea352b576e900d74ad779590"
PARSER_PACKAGE = "pypdf"
EXPECTED_PARSER_VERSION = "6.16.2"
TRUSTED_RESULT_LOGIN = "github-actions[bot]"
MAX_TERMINAL_UTF8_BYTES = 40_000
MAX_PAGES = 300
MAX_PAGE_TEXT_CHARS = 250_000
MAX_TOTAL_TEXT_CHARS = 2_000_000

_CANONICAL_OPEN_FIXED = _open_fixed
_CANONICAL_MONOTONIC = time.monotonic

_SHA_RE = re.compile(r"^[0-9a-f]{40}$")
_DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
_SAFE_REQUESTER_RE = re.compile(r"^[A-Za-z0-9_.:@/+ -]{1,96}$")
_REQUEST_FIELDS = {
    "schema_version",
    "action",
    "issue",
    "target_sha",
    "dataset_id",
    "requester",
}
_AUTHORITY_FALSE_FIELDS = (
    "pdf_content_interpreted",
    "crs_coordinate_semantics_verified",
    "generator_invocation_verified",
    "missingness_semantics_verified",
    "site_model_compatibility_verified",
    "external_bytes_persisted",
    "publication_authorized",
    "model_use_authorized",
)
_RESULT_FIELDS = {
    "schema_version",
    "action",
    "source_issue",
    "dataset_id",
    "target_sha",
    "execution_sha",
    "manual_identity",
    "pdf_content_profiled",
    "status",
    "failure_class",
    "content_profile",
    *_AUTHORITY_FALSE_FIELDS,
}
_PROFILE_FIELDS = {
    "schema_version",
    "parser",
    "page_count",
    "normalized_text_character_count",
    "normalized_text_sha256",
    "mention_pages",
    "raw_text_exposed",
}
_PARSER_FIELDS = {"package", "version"}
_MENTION_PATTERNS = {
    "coordinate_reference_system": re.compile(r"\bcoordinate\s+reference\s+system\b|\bcrs\b", re.I),
    "epsg": re.compile(r"\bepsg\b", re.I),
    "epsg_4326": re.compile(r"\bepsg\s*:?\s*4326\b", re.I),
    "wgs84": re.compile(r"\bwgs\s*[- ]?\s*84\b", re.I),
    "projection": re.compile(r"\bprojection\b|\bprojected\b", re.I),
    "reprojection": re.compile(r"\breproject(?:ed|ion|ing)?\b", re.I),
    "longitude_latitude": re.compile(r"\blongitude\b.{0,160}\blatitude\b|\blatitude\b.{0,160}\blongitude\b", re.I | re.S),
    "vs30": re.compile(r"\bvs\s*30\b", re.I),
    "xvf": re.compile(r"\bxvf\b", re.I),
    "slope": re.compile(r"\bslope\b", re.I),
    "geology": re.compile(r"\bgeolog(?:y|ical)\b", re.I),
    "region": re.compile(r"\bregion\b", re.I),
    "missing": re.compile(r"\bmissing\b", re.I),
    "nodata": re.compile(r"\bno\s*data\b|\bnodata\b", re.I),
    "nan": re.compile(r"\bnan\b", re.I),
    "exposure_to_site": re.compile(r"\bexposure\s*[- ]?\s*to\s*[- ]?\s*site\b", re.I),
    "site_amplification": re.compile(r"\bsite\s+amplification\b", re.I),
    "site_model": re.compile(r"\bsite\s+model\b", re.I),
    "raster": re.compile(r"\braster\b", re.I),
    "shapefile": re.compile(r"\bshape\s*file\b|\bshapefile\b", re.I),
}
_MENTION_KEYS = tuple(sorted(_MENTION_PATTERNS))


class Project278ManualContentProfileError(RuntimeError):
    """Fail-closed bounded profile error."""


def _pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    obj: dict[str, Any] = {}
    for key, value in pairs:
        if key in obj:
            raise Project278ManualContentProfileError("duplicate JSON key")
        obj[key] = value
    return obj


def _reject_constant(value: str) -> Any:
    raise Project278ManualContentProfileError(f"non-finite JSON constant: {value}")


def _load_json(text: str, *, label: str) -> Any:
    try:
        return json.loads(text, object_pairs_hook=_pairs, parse_constant=_reject_constant)
    except Project278ManualContentProfileError:
        raise
    except (json.JSONDecodeError, TypeError, ValueError) as exc:
        raise Project278ManualContentProfileError(f"invalid {label} JSON") from exc


def validate_request(body: object, *, expected_issue: int, execution_sha: str) -> dict[str, Any]:
    if type(expected_issue) is not int or expected_issue != CONTROL_ISSUE:
        raise Project278ManualContentProfileError("wrong runtime issue")
    if type(execution_sha) is not str or not _SHA_RE.fullmatch(execution_sha):
        raise Project278ManualContentProfileError("invalid execution SHA")
    if type(body) is not str or body.count(REQUEST_MARKER) != 1:
        raise Project278ManualContentProfileError("invalid content-profile request marker")
    before, after = body.split(REQUEST_MARKER, 1)
    if before.strip() or not after.strip():
        raise Project278ManualContentProfileError("content-profile request envelope is not canonical")
    request = _load_json(after.strip(), label="content-profile request")
    if type(request) is not dict or set(request) != _REQUEST_FIELDS:
        raise Project278ManualContentProfileError("content-profile request fields drifted")
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
            raise Project278ManualContentProfileError(f"content-profile request {field} drifted")
    requester = request["requester"]
    if (
        type(requester) is not str
        or requester != requester.strip()
        or not _SAFE_REQUESTER_RE.fullmatch(requester)
    ):
        raise Project278ManualContentProfileError("invalid requester identity")
    return request


def _require_production_identity() -> None:
    if _open_fixed is not _CANONICAL_OPEN_FIXED:
        raise Project278ManualContentProfileError("production transport authority drifted")
    if time.monotonic is not _CANONICAL_MONOTONIC:
        raise Project278ManualContentProfileError("production monotonic clock drifted")
    exact = (
        (PROJECT_ID, 278),
        (PROJECT_PATH, "efehr/esrm20_sitemodel"),
        (COMMIT_SHA, "038c91d2bf5a07f6b54ff51639aad874d6837ea9"),
        (REPOSITORY_PATH, "ExposureReadme.pdf"),
        (EXPECTED_BYTE_COUNT, 2_121_105),
        (EXPECTED_SHA256, "6a69d92ecb7df5e9b31c3609246baadff24e0f59ea352b576e900d74ad779590"),
    )
    for observed, expected in exact:
        if type(observed) is not type(expected) or observed != expected:
            raise Project278ManualContentProfileError("frozen project-278 authority drifted")


def _acquire_pdf_bytes_for_test(
    *,
    opener: Any,
    monotonic: Callable[[], float],
    expected_byte_count: int,
    expected_sha256: str,
) -> bytes:
    """Acquire only the frozen provider path through injected test seams."""

    if type(expected_byte_count) is not int or expected_byte_count <= 0:
        raise Project278ManualContentProfileError("invalid expected byte count")
    if type(expected_sha256) is not str or not _DIGEST_RE.fullmatch(expected_sha256):
        raise Project278ManualContentProfileError("invalid expected digest")
    try:
        target = validate_target(
            source_issue=CONTROL_ISSUE,
            dataset_id=DATASET_ID,
            project_id=PROJECT_ID,
            commit_sha=COMMIT_SHA,
            repository_path=REPOSITORY_PATH,
        )
    except EfehrReceiptError as exc:
        raise Project278ManualContentProfileError("trusted EFEHR target is invalid") from exc

    file_url = raw_file_api_url(target)
    request = urllib.request.Request(
        file_url,
        headers={
            "Accept": "application/pdf,application/octet-stream;q=0.9",
            "User-Agent": "OpenCatastrophe-EFEHR-project278-content-profile-v1",
        },
        method="GET",
    )
    deadline = monotonic() + TOTAL_DEADLINE_SECONDS
    try:
        with opener(request, timeout=_remaining(deadline, monotonic)) as response:
            _validate_exact_response(response, file_url)
            _declared_length(response, expected_byte_count)
            stream = _DeadlineStream(response, deadline=deadline, monotonic=monotonic)
            payload = bytearray()
            while True:
                chunk = stream.read(min(64 * 1024, expected_byte_count + 1 - len(payload)))
                if not chunk:
                    break
                if type(chunk) is not bytes:
                    raise Project278ManualContentProfileError("provider returned non-byte PDF data")
                payload.extend(chunk)
                if len(payload) > expected_byte_count:
                    raise Project278ManualContentProfileError("provider PDF exceeded expected byte count")
    except Project278ManualContentProfileError:
        raise
    except EfehrAcquisitionError as exc:
        raise Project278ManualContentProfileError("provider PDF acquisition failed") from exc
    except (
        OSError,
        http.client.HTTPException,
        urllib.error.URLError,
        urllib.error.HTTPError,
        TimeoutError,
    ) as exc:
        raise Project278ManualContentProfileError(
            f"provider PDF acquisition failed: {type(exc).__name__}"
        ) from exc

    pdf_bytes = bytes(payload)
    if len(pdf_bytes) != expected_byte_count:
        raise Project278ManualContentProfileError("provider PDF byte count drifted")
    if hashlib.sha256(pdf_bytes).hexdigest() != expected_sha256:
        raise Project278ManualContentProfileError("provider PDF SHA-256 drifted")
    return pdf_bytes


def acquire_verified_pdf_bytes() -> bytes:
    """Production acquisition of the one SHA-bound project-278 PDF."""

    _require_production_identity()
    return _acquire_pdf_bytes_for_test(
        opener=_CANONICAL_OPEN_FIXED,
        monotonic=_CANONICAL_MONOTONIC,
        expected_byte_count=EXPECTED_BYTE_COUNT,
        expected_sha256=EXPECTED_SHA256,
    )


def _resolve_reader() -> tuple[Callable[..., Any], str]:
    try:
        import pypdf
    except ModuleNotFoundError as exc:
        raise Project278ManualContentProfileError("pypdf dependency unavailable") from exc
    version = getattr(pypdf, "__version__", None)
    reader = getattr(pypdf, "PdfReader", None)
    if version != EXPECTED_PARSER_VERSION or reader is None:
        raise Project278ManualContentProfileError("pypdf runtime identity unavailable")
    return reader, version


def _profile_pdf_bytes_for_test(
    pdf_bytes: bytes,
    *,
    expected_byte_count: int,
    expected_sha256: str,
    reader_factory: Callable[..., Any],
    parser_version: str,
) -> dict[str, Any]:
    """Mechanically profile verified PDF bytes without returning source text."""

    if type(pdf_bytes) is not bytes:
        raise Project278ManualContentProfileError("PDF payload is not bytes")
    if len(pdf_bytes) != expected_byte_count:
        raise Project278ManualContentProfileError("PDF byte count does not match bound identity")
    if hashlib.sha256(pdf_bytes).hexdigest() != expected_sha256:
        raise Project278ManualContentProfileError("PDF digest does not match bound identity")
    if type(parser_version) is not str or not parser_version:
        raise Project278ManualContentProfileError("invalid parser version")
    try:
        reader = reader_factory(io.BytesIO(pdf_bytes), strict=True)
    except Exception as exc:
        raise Project278ManualContentProfileError("PDF parser rejected exact bytes") from exc
    if bool(getattr(reader, "is_encrypted", False)):
        raise Project278ManualContentProfileError("encrypted PDF is unsupported")
    pages = getattr(reader, "pages", None)
    try:
        page_count = len(pages)
    except Exception as exc:
        raise Project278ManualContentProfileError("PDF page inventory unavailable") from exc
    if page_count <= 0 or page_count > MAX_PAGES:
        raise Project278ManualContentProfileError("PDF page count outside bounded profile")
    mentions: dict[str, list[int]] = {key: [] for key in _MENTION_KEYS}
    normalized_pages: list[str] = []
    total_chars = 0
    for page_index, page in enumerate(pages, start=1):
        try:
            text = page.extract_text()
        except Exception as exc:
            raise Project278ManualContentProfileError("PDF text extraction failed") from exc
        if type(text) is not str:
            raise Project278ManualContentProfileError("PDF page text is not a string")
        if len(text) > MAX_PAGE_TEXT_CHARS:
            raise Project278ManualContentProfileError("PDF page text exceeds profile bound")
        normalized = " ".join(text.split()).casefold()
        total_chars += len(normalized)
        if total_chars > MAX_TOTAL_TEXT_CHARS:
            raise Project278ManualContentProfileError("PDF extracted text exceeds profile bound")
        normalized_pages.append(normalized)
        for key, pattern in _MENTION_PATTERNS.items():
            if pattern.search(normalized):
                mentions[key].append(page_index)
    if total_chars == 0:
        raise Project278ManualContentProfileError("PDF contains no extractable text")
    normalized_blob = "\n".join(normalized_pages).encode("utf-8")
    return {
        "schema_version": PROFILE_SCHEMA_VERSION,
        "parser": {"package": PARSER_PACKAGE, "version": parser_version},
        "page_count": page_count,
        "normalized_text_character_count": total_chars,
        "normalized_text_sha256": hashlib.sha256(normalized_blob).hexdigest(),
        "mention_pages": mentions,
        "raw_text_exposed": False,
    }


def profile_verified_pdf_bytes(pdf_bytes: bytes) -> dict[str, Any]:
    reader_factory, parser_version = _resolve_reader()
    return _profile_pdf_bytes_for_test(
        pdf_bytes,
        expected_byte_count=EXPECTED_BYTE_COUNT,
        expected_sha256=EXPECTED_SHA256,
        reader_factory=reader_factory,
        parser_version=parser_version,
    )


def _base_result(*, execution_sha: str) -> dict[str, Any]:
    result = {
        "schema_version": RESULT_SCHEMA_VERSION,
        "action": ACTION,
        "source_issue": CONTROL_ISSUE,
        "dataset_id": DATASET_ID,
        "target_sha": execution_sha,
        "execution_sha": execution_sha,
        "manual_identity": {
            "project_id": PROJECT_ID,
            "project_path": PROJECT_PATH,
            "commit_sha": COMMIT_SHA,
            "repository_path": REPOSITORY_PATH,
            "byte_count": EXPECTED_BYTE_COUNT,
            "sha256": EXPECTED_SHA256,
        },
        "pdf_content_profiled": False,
    }
    result.update({field: False for field in _AUTHORITY_FALSE_FIELDS})
    return result


def run_content_profile(*, execution_sha: str) -> dict[str, Any]:
    if type(execution_sha) is not str or not _SHA_RE.fullmatch(execution_sha):
        raise Project278ManualContentProfileError("invalid execution SHA")
    result = _base_result(execution_sha=execution_sha)
    try:
        pdf_bytes = acquire_verified_pdf_bytes()
    except Project278ManualContentProfileError:
        result.update({"status": "blocked", "failure_class": "acquisition_failure", "content_profile": None})
        return result
    try:
        profile = profile_verified_pdf_bytes(pdf_bytes)
    except Project278ManualContentProfileError:
        result.update({"status": "blocked", "failure_class": "pdf_parse_failure", "content_profile": None})
        return result
    result.update(
        {
            "status": "pass",
            "failure_class": None,
            "pdf_content_profiled": True,
            "content_profile": profile,
        }
    )
    return result


def _validate_terminal_payload(result: object, *, execution_sha: str) -> bool:
    if type(result) is not dict:
        raise Project278ManualContentProfileError("trusted profile result is not an object")
    if set(result) != _RESULT_FIELDS:
        raise Project278ManualContentProfileError("trusted profile result fields drifted")
    exact = (
        ("schema_version", RESULT_SCHEMA_VERSION),
        ("action", ACTION),
        ("source_issue", CONTROL_ISSUE),
        ("dataset_id", DATASET_ID),
        ("target_sha", execution_sha),
        ("execution_sha", execution_sha),
    ) + tuple((field, False) for field in _AUTHORITY_FALSE_FIELDS)
    for field, expected in exact:
        observed = result.get(field)
        if type(observed) is not type(expected) or observed != expected:
            raise Project278ManualContentProfileError(f"trusted profile result drifted at {field}")
    identity = result.get("manual_identity")
    expected_identity = {
        "project_id": PROJECT_ID,
        "project_path": PROJECT_PATH,
        "commit_sha": COMMIT_SHA,
        "repository_path": REPOSITORY_PATH,
        "byte_count": EXPECTED_BYTE_COUNT,
        "sha256": EXPECTED_SHA256,
    }
    if type(identity) is not dict or identity != expected_identity:
        raise Project278ManualContentProfileError("trusted profile manual identity drifted")
    status = result.get("status")
    if status == "pass":
        if result.get("failure_class") is not None:
            raise Project278ManualContentProfileError("trusted PASS failure class drifted")
        if result.get("pdf_content_profiled") is not True:
            raise Project278ManualContentProfileError("trusted PASS is not profiled")
        profile = result.get("content_profile")
        if type(profile) is not dict or set(profile) != _PROFILE_FIELDS:
            raise Project278ManualContentProfileError("trusted PASS content profile fields drifted")
        if profile.get("schema_version") != PROFILE_SCHEMA_VERSION:
            raise Project278ManualContentProfileError("trusted PASS content profile drifted")
        parser = profile.get("parser")
        if (
            type(parser) is not dict
            or set(parser) != _PARSER_FIELDS
            or parser.get("package") != PARSER_PACKAGE
            or parser.get("version") != EXPECTED_PARSER_VERSION
        ):
            raise Project278ManualContentProfileError("trusted PASS parser identity drifted")
        page_count = profile.get("page_count")
        if type(page_count) is not int or not (1 <= page_count <= MAX_PAGES):
            raise Project278ManualContentProfileError("trusted PASS page count invalid")
        character_count = profile.get("normalized_text_character_count")
        if (
            type(character_count) is not int
            or not (1 <= character_count <= MAX_TOTAL_TEXT_CHARS)
        ):
            raise Project278ManualContentProfileError("trusted PASS character count invalid")
        normalized_digest = profile.get("normalized_text_sha256")
        if type(normalized_digest) is not str or _DIGEST_RE.fullmatch(normalized_digest) is None:
            raise Project278ManualContentProfileError("trusted PASS text digest invalid")
        if profile.get("raw_text_exposed") is not False:
            raise Project278ManualContentProfileError("trusted PASS exposes source text")
        mention_pages = profile.get("mention_pages")
        if type(mention_pages) is not dict or set(mention_pages) != set(_MENTION_KEYS):
            raise Project278ManualContentProfileError("trusted PASS mention surface drifted")
        for pages in mention_pages.values():
            if (
                type(pages) is not list
                or pages != sorted(set(pages))
                or any(type(page) is not int or not (1 <= page <= page_count) for page in pages)
            ):
                raise Project278ManualContentProfileError("trusted PASS mention pages invalid")
        return True
    if status == "blocked":
        if result.get("pdf_content_profiled") is not False:
            raise Project278ManualContentProfileError("trusted BLOCKED widened profile state")
        if result.get("failure_class") not in {"acquisition_failure", "pdf_parse_failure"}:
            raise Project278ManualContentProfileError("trusted BLOCKED failure class drifted")
        if result.get("content_profile") is not None:
            raise Project278ManualContentProfileError("trusted BLOCKED contains a profile")
        return True
    raise Project278ManualContentProfileError("trusted profile result has non-terminal status")


def _parse_trusted_terminal_result(body: object, *, execution_sha: str) -> bool:
    if type(body) is not str or RESULT_MARKER not in body:
        return False
    try:
        encoded = body.encode("utf-8", errors="strict")
    except UnicodeEncodeError as exc:
        raise Project278ManualContentProfileError("trusted profile result is not UTF-8") from exc
    if len(encoded) > MAX_TERMINAL_UTF8_BYTES:
        raise Project278ManualContentProfileError("trusted profile result exceeds byte bound")
    if body.count(RESULT_MARKER) != 1:
        raise Project278ManualContentProfileError("trusted profile marker is malformed")
    before, after = body.split(RESULT_MARKER, 1)
    if before.strip() or not after.strip():
        raise Project278ManualContentProfileError("trusted profile envelope is malformed")
    result = _load_json(after.strip(), label="trusted content-profile result")
    return _validate_terminal_payload(result, execution_sha=execution_sha)


def has_terminal_content_profile_result(
    *, repository: str, token: str, execution_sha: str, opener: Any | None = None, max_pages: int = 20
) -> bool:
    """Deduplicate only against the complete bounded Issue #291 ledger."""

    if type(execution_sha) is not str or not _SHA_RE.fullmatch(execution_sha):
        raise Project278ManualContentProfileError("invalid execution SHA")
    kwargs: dict[str, Any] = {"issue": CONTROL_ISSUE, "max_pages": max_pages}
    if opener is not None:
        kwargs["opener"] = opener
    try:
        comments = fetch_repository_comments(repository, token, **kwargs)
    except LedgerError as exc:
        raise Project278ManualContentProfileError("content-profile result ledger is incomplete") from exc
    match_seen = False
    for comment in comments:
        user = comment.get("user")
        login = user.get("login") if type(user) is dict else None
        if login != TRUSTED_RESULT_LOGIN:
            continue
        if _parse_trusted_terminal_result(comment.get("body"), execution_sha=execution_sha):
            match_seen = True
    return match_seen


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
    result = run_content_profile(execution_sha=args.execution_sha)
    Path(args.output).write_text(
        json.dumps(result, sort_keys=True, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())