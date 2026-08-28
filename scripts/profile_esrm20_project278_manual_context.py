# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Bounded non-text context profile for the frozen ESRM20 project-278 manual.

This trusted-main helper reuses the already-reviewed fixed PDF acquisition path and
requires the extracted-text identity from the earlier trusted content profile before
returning any context evidence. Output is restricted to page/occurrence identities,
window byte counts and SHA-256 values, and counts from a closed vocabulary. Source
text and snippets are never returned.
"""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
import re
from pathlib import Path
from typing import Any, Callable

from scripts import profile_esrm20_project278_manual as parent
from scripts.prepare_agent_action_result import LedgerError, fetch_repository_comments

REQUEST_MARKER = "<!-- oc-eq1-esrm20-project278-manual-context-profile-request-v1 -->"
RESULT_MARKER = "<!-- oc-eq1-esrm20-project278-manual-context-profile-result-v1 -->"
REQUEST_SCHEMA_VERSION = "oc-esrm20-project278-manual-context-profile-request-v1"
RESULT_SCHEMA_VERSION = "oc-esrm20-project278-manual-context-profile-result-v1"
CONTEXT_PROFILE_SCHEMA_VERSION = "oc-esrm20-project278-manual-context-profile-v1"
ACTION = "esrm20_project278_manual_context_profile"
CONTROL_ISSUE = 291
DATASET_ID = parent.DATASET_ID
TRUSTED_RESULT_LOGIN = parent.TRUSTED_RESULT_LOGIN

EXPECTED_PAGE_COUNT = 14
EXPECTED_NORMALIZED_TEXT_CHARACTER_COUNT = 20_841
EXPECTED_NORMALIZED_TEXT_SHA256 = (
    "fa8cfc6789986951c4cc440a8977f1f7def24d1702872dd8d96136b051b98d83"
)
CONTEXT_RADIUS_CHARS = 240
MAX_CONTEXT_RECORDS = 96
MAX_CONTEXT_WINDOW_UTF8_BYTES = (2 * CONTEXT_RADIUS_CHARS + 64) * 4
MAX_TERMINAL_UTF8_BYTES = 55_000

_SHA_RE = re.compile(r"^[0-9a-f]{40}$")
_DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
_SAFE_REQUESTER_RE = re.compile(r"^[A-Za-z0-9_.:@/+ -]{1,96}$")

_FOCUS_PATTERNS: dict[str, re.Pattern[str]] = {
    "exposure_to_site": re.compile(r"\bexposure\s*[- ]?\s*to\s*[- ]?\s*site\b", re.I),
    "latitude": re.compile(r"\blatitude\b", re.I),
    "longitude": re.compile(r"\blongitude\b", re.I),
    "projection": re.compile(r"\bprojection\b|\bprojected\b", re.I),
    "site_model": re.compile(r"\bsite\s+model\b", re.I),
    "slope": re.compile(r"\bslope\b", re.I),
    "vs30": re.compile(r"\bvs\s*30\b", re.I),
    "wgs84": re.compile(r"\bwgs\s*[- ]?\s*84\b", re.I),
    "xvf": re.compile(r"\bxvf\b", re.I),
}
_FOCUS_KEYS = tuple(sorted(_FOCUS_PATTERNS))

_CONTEXT_PATTERNS: dict[str, re.Pattern[str]] = {
    "arcgis": re.compile(r"\barc\s*gis\b|\barcgis\b", re.I),
    "assign": re.compile(r"\bassign(?:ed|ing|ment)?\b", re.I),
    "convert": re.compile(r"\bconvert(?:ed|ing|s|er)?\b|\bconversion\b", re.I),
    "coordinate": re.compile(r"\bcoordinates?\b", re.I),
    "coordinate_reference_system": re.compile(r"\bcoordinate\s+reference\s+system\b|\bcrs\b", re.I),
    "decimal_degrees": re.compile(r"\bdecimal\s+degrees?\b", re.I),
    "default": re.compile(r"\bdefaults?\b|\bdefaulted\b", re.I),
    "degrees": re.compile(r"\bdegrees?\b", re.I),
    "epsg": re.compile(r"\bepsg\b", re.I),
    "exposure": re.compile(r"\bexposure\b", re.I),
    "extract": re.compile(r"\bextract(?:ed|ing|ion|s)?\b", re.I),
    "geology": re.compile(r"\bgeolog(?:y|ical)\b", re.I),
    "intersect": re.compile(r"\bintersect(?:ed|ing|ion|s)?\b", re.I),
    "join": re.compile(r"\bjoin(?:ed|ing|s)?\b", re.I),
    "latitude": _FOCUS_PATTERNS["latitude"],
    "longitude": _FOCUS_PATTERNS["longitude"],
    "missing": re.compile(r"\bmissing\b", re.I),
    "nan": re.compile(r"\bnan\b", re.I),
    "nodata": re.compile(r"\bno\s*data\b|\bnodata\b", re.I),
    "projection": _FOCUS_PATTERNS["projection"],
    "python": re.compile(r"\bpython\b", re.I),
    "qgis": re.compile(r"\bqgis\b", re.I),
    "raster": re.compile(r"\braster\b", re.I),
    "reproject": re.compile(r"\breproject(?:ed|ing|ion|s)?\b", re.I),
    "sample": re.compile(r"\bsampl(?:e|ed|ing|es)\b", re.I),
    "script": re.compile(r"\bscripts?\b", re.I),
    "shapefile": re.compile(r"\bshape\s*file\b|\bshapefile\b", re.I),
    "site_amplification": re.compile(r"\bsite\s+amplification\b", re.I),
    "site_model": _FOCUS_PATTERNS["site_model"],
    "slope": _FOCUS_PATTERNS["slope"],
    "transform": re.compile(r"\btransform(?:ed|ing|ation|s)?\b", re.I),
    "vs30": _FOCUS_PATTERNS["vs30"],
    "wgs84": _FOCUS_PATTERNS["wgs84"],
    "xvf": _FOCUS_PATTERNS["xvf"],
    "zero": re.compile(r"(?<![A-Za-z0-9])zero(?:s)?(?![A-Za-z0-9])", re.I),
}
_CONTEXT_KEYS = tuple(sorted(_CONTEXT_PATTERNS))

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
    "source_profile_identity",
    "context_profiled",
    "status",
    "failure_class",
    "context_profile",
    *_AUTHORITY_FALSE_FIELDS,
}
_CONTEXT_PROFILE_FIELDS = {
    "schema_version",
    "parser",
    "source_text",
    "focus_terms",
    "vocabulary",
    "window_radius_chars",
    "focus_summary",
    "records",
    "raw_text_exposed",
    "snippets_exposed",
}


class Project278ManualContextProfileError(RuntimeError):
    """Fail-closed context-profile error."""


def _pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise Project278ManualContextProfileError("duplicate JSON key")
        result[key] = value
    return result


def _reject_constant(token: str) -> Any:
    raise Project278ManualContextProfileError(f"non-finite JSON constant: {token}")


def _load_json(text: str, *, label: str) -> Any:
    try:
        return json.loads(text, object_pairs_hook=_pairs, parse_constant=_reject_constant)
    except Project278ManualContextProfileError:
        raise
    except (json.JSONDecodeError, TypeError, ValueError) as exc:
        raise Project278ManualContextProfileError(f"invalid {label} JSON") from exc


def validate_request(body: object, *, expected_issue: int, execution_sha: str) -> dict[str, Any]:
    if type(expected_issue) is not int or expected_issue != CONTROL_ISSUE:
        raise Project278ManualContextProfileError("wrong runtime issue")
    if type(execution_sha) is not str or _SHA_RE.fullmatch(execution_sha) is None:
        raise Project278ManualContextProfileError("invalid execution SHA")
    if type(body) is not str or body.count(REQUEST_MARKER) != 1:
        raise Project278ManualContextProfileError("invalid context-profile request marker")
    before, after = body.split(REQUEST_MARKER, 1)
    if before.strip() or not after.strip():
        raise Project278ManualContextProfileError("context-profile request envelope is not canonical")
    request = _load_json(after.strip(), label="context-profile request")
    if type(request) is not dict or set(request) != _REQUEST_FIELDS:
        raise Project278ManualContextProfileError("context-profile request fields drifted")
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
            raise Project278ManualContextProfileError(f"context-profile request {field} drifted")
    requester = request.get("requester")
    if (
        type(requester) is not str
        or requester != requester.strip()
        or _SAFE_REQUESTER_RE.fullmatch(requester) is None
    ):
        raise Project278ManualContextProfileError("invalid requester identity")
    return request


def _require_parent_identity() -> None:
    exact = (
        (parent.CONTROL_ISSUE, CONTROL_ISSUE),
        (parent.DATASET_ID, DATASET_ID),
        (parent.PROJECT_ID, 278),
        (parent.PROJECT_PATH, "efehr/esrm20_sitemodel"),
        (parent.COMMIT_SHA, "038c91d2bf5a07f6b54ff51639aad874d6837ea9"),
        (parent.REPOSITORY_PATH, "ExposureReadme.pdf"),
        (parent.EXPECTED_BYTE_COUNT, 2_121_105),
        (
            parent.EXPECTED_SHA256,
            "6a69d92ecb7df5e9b31c3609246baadff24e0f59ea352b576e900d74ad779590",
        ),
        (parent.PARSER_PACKAGE, "pypdf"),
        (parent.EXPECTED_PARSER_VERSION, "6.16.2"),
    )
    for observed, expected in exact:
        if type(observed) is not type(expected) or observed != expected:
            raise Project278ManualContextProfileError("parent project-278 authority drifted")


def _context_profile_for_test(
    pdf_bytes: bytes,
    *,
    expected_byte_count: int,
    expected_sha256: str,
    reader_factory: Callable[..., Any],
    parser_version: str,
    expected_page_count: int,
    expected_character_count: int,
    expected_text_sha256: str,
) -> dict[str, Any]:
    if type(pdf_bytes) is not bytes or len(pdf_bytes) != expected_byte_count:
        raise Project278ManualContextProfileError("PDF byte identity drifted")
    if hashlib.sha256(pdf_bytes).hexdigest() != expected_sha256:
        raise Project278ManualContextProfileError("PDF digest drifted")
    if type(parser_version) is not str or not parser_version:
        raise Project278ManualContextProfileError("parser identity is invalid")
    if type(expected_page_count) is not int or expected_page_count <= 0:
        raise Project278ManualContextProfileError("expected page count is invalid")
    if type(expected_character_count) is not int or expected_character_count <= 0:
        raise Project278ManualContextProfileError("expected character count is invalid")
    if type(expected_text_sha256) is not str or _DIGEST_RE.fullmatch(expected_text_sha256) is None:
        raise Project278ManualContextProfileError("expected text digest is invalid")

    try:
        reader = reader_factory(io.BytesIO(pdf_bytes), strict=True)
    except Exception as exc:
        raise Project278ManualContextProfileError("PDF parser rejected exact bytes") from exc
    if bool(getattr(reader, "is_encrypted", False)):
        raise Project278ManualContextProfileError("encrypted PDF is unsupported")
    pages = getattr(reader, "pages", None)
    try:
        page_count = len(pages)
    except Exception as exc:
        raise Project278ManualContextProfileError("PDF page inventory unavailable") from exc
    if page_count != expected_page_count:
        raise Project278ManualContextProfileError("trusted PDF page count drifted")

    normalized_pages: list[str] = []
    total_chars = 0
    for page in pages:
        try:
            text = page.extract_text()
        except Exception as exc:
            raise Project278ManualContextProfileError("PDF text extraction failed") from exc
        if type(text) is not str or len(text) > parent.MAX_PAGE_TEXT_CHARS:
            raise Project278ManualContextProfileError("PDF page text is outside bounds")
        normalized = " ".join(text.split()).casefold()
        total_chars += len(normalized)
        if total_chars > parent.MAX_TOTAL_TEXT_CHARS:
            raise Project278ManualContextProfileError("PDF extracted text exceeds bound")
        normalized_pages.append(normalized)
    if total_chars != expected_character_count:
        raise Project278ManualContextProfileError("trusted extracted-text length drifted")
    normalized_blob = "\n".join(normalized_pages).encode("utf-8")
    text_sha256 = hashlib.sha256(normalized_blob).hexdigest()
    if text_sha256 != expected_text_sha256:
        raise Project278ManualContextProfileError("trusted extracted-text digest drifted")

    records: list[dict[str, Any]] = []
    focus_summary: dict[str, dict[str, Any]] = {}
    for focus in _FOCUS_KEYS:
        pattern = _FOCUS_PATTERNS[focus]
        pages_seen: list[int] = []
        focus_count = 0
        for page_number, page in enumerate(normalized_pages, start=1):
            hits = list(pattern.finditer(page))
            if hits:
                pages_seen.append(page_number)
            for occurrence, hit in enumerate(hits, start=1):
                focus_count += 1
                if len(records) >= MAX_CONTEXT_RECORDS:
                    raise Project278ManualContextProfileError("context record bound exceeded")
                start = max(0, hit.start() - CONTEXT_RADIUS_CHARS)
                end = min(len(page), hit.end() + CONTEXT_RADIUS_CHARS)
                window = page[start:end]
                window_bytes = window.encode("utf-8")
                if not window_bytes or len(window_bytes) > MAX_CONTEXT_WINDOW_UTF8_BYTES:
                    raise Project278ManualContextProfileError("context window size is outside bounds")
                nearby_terms: dict[str, int] = {}
                for label, nearby_pattern in _CONTEXT_PATTERNS.items():
                    count = len(list(nearby_pattern.finditer(window)))
                    if count:
                        nearby_terms[label] = count
                records.append(
                    {
                        "focus": focus,
                        "page": page_number,
                        "occurrence": occurrence,
                        "window_utf8_bytes": len(window_bytes),
                        "window_sha256": hashlib.sha256(window_bytes).hexdigest(),
                        "nearby_terms": nearby_terms,
                    }
                )
        if focus_count <= 0:
            raise Project278ManualContextProfileError(f"trusted focus term disappeared: {focus}")
        focus_summary[focus] = {"count": focus_count, "pages": pages_seen}

    return {
        "schema_version": CONTEXT_PROFILE_SCHEMA_VERSION,
        "parser": {"package": parent.PARSER_PACKAGE, "version": parser_version},
        "source_text": {
            "page_count": page_count,
            "normalized_text_character_count": total_chars,
            "normalized_text_sha256": text_sha256,
        },
        "focus_terms": list(_FOCUS_KEYS),
        "vocabulary": list(_CONTEXT_KEYS),
        "window_radius_chars": CONTEXT_RADIUS_CHARS,
        "focus_summary": focus_summary,
        "records": records,
        "raw_text_exposed": False,
        "snippets_exposed": False,
    }


def profile_verified_pdf_context(pdf_bytes: bytes) -> dict[str, Any]:
    _require_parent_identity()
    reader_factory, parser_version = parent._resolve_reader()
    return _context_profile_for_test(
        pdf_bytes,
        expected_byte_count=parent.EXPECTED_BYTE_COUNT,
        expected_sha256=parent.EXPECTED_SHA256,
        reader_factory=reader_factory,
        parser_version=parser_version,
        expected_page_count=EXPECTED_PAGE_COUNT,
        expected_character_count=EXPECTED_NORMALIZED_TEXT_CHARACTER_COUNT,
        expected_text_sha256=EXPECTED_NORMALIZED_TEXT_SHA256,
    )


def _manual_identity() -> dict[str, Any]:
    return {
        "project_id": parent.PROJECT_ID,
        "project_path": parent.PROJECT_PATH,
        "commit_sha": parent.COMMIT_SHA,
        "repository_path": parent.REPOSITORY_PATH,
        "byte_count": parent.EXPECTED_BYTE_COUNT,
        "sha256": parent.EXPECTED_SHA256,
    }


def _source_profile_identity() -> dict[str, Any]:
    return {
        "schema_version": parent.PROFILE_SCHEMA_VERSION,
        "page_count": EXPECTED_PAGE_COUNT,
        "normalized_text_character_count": EXPECTED_NORMALIZED_TEXT_CHARACTER_COUNT,
        "normalized_text_sha256": EXPECTED_NORMALIZED_TEXT_SHA256,
        "parser": {
            "package": parent.PARSER_PACKAGE,
            "version": parent.EXPECTED_PARSER_VERSION,
        },
    }


def _base_result(*, execution_sha: str) -> dict[str, Any]:
    result: dict[str, Any] = {
        "schema_version": RESULT_SCHEMA_VERSION,
        "action": ACTION,
        "source_issue": CONTROL_ISSUE,
        "dataset_id": DATASET_ID,
        "target_sha": execution_sha,
        "execution_sha": execution_sha,
        "manual_identity": _manual_identity(),
        "source_profile_identity": _source_profile_identity(),
        "context_profiled": False,
    }
    result.update({field: False for field in _AUTHORITY_FALSE_FIELDS})
    return result


def run_context_profile(*, execution_sha: str) -> dict[str, Any]:
    if type(execution_sha) is not str or _SHA_RE.fullmatch(execution_sha) is None:
        raise Project278ManualContextProfileError("invalid execution SHA")
    result = _base_result(execution_sha=execution_sha)
    try:
        _require_parent_identity()
        pdf_bytes = parent.acquire_verified_pdf_bytes()
    except (Project278ManualContextProfileError, parent.Project278ManualContentProfileError):
        result.update(
            {"status": "blocked", "failure_class": "acquisition_failure", "context_profile": None}
        )
        return result
    try:
        context = profile_verified_pdf_context(pdf_bytes)
    except (Project278ManualContextProfileError, parent.Project278ManualContentProfileError):
        result.update(
            {"status": "blocked", "failure_class": "context_profile_failure", "context_profile": None}
        )
        return result
    result.update(
        {
            "status": "pass",
            "failure_class": None,
            "context_profiled": True,
            "context_profile": context,
        }
    )
    return result


def _validate_context_profile(profile: object) -> None:
    if type(profile) is not dict or set(profile) != _CONTEXT_PROFILE_FIELDS:
        raise Project278ManualContextProfileError("trusted context-profile fields drifted")
    if profile.get("schema_version") != CONTEXT_PROFILE_SCHEMA_VERSION:
        raise Project278ManualContextProfileError("trusted context-profile schema drifted")
    if profile.get("parser") != {
        "package": parent.PARSER_PACKAGE,
        "version": parent.EXPECTED_PARSER_VERSION,
    }:
        raise Project278ManualContextProfileError("trusted context parser identity drifted")
    if profile.get("source_text") != {
        "page_count": EXPECTED_PAGE_COUNT,
        "normalized_text_character_count": EXPECTED_NORMALIZED_TEXT_CHARACTER_COUNT,
        "normalized_text_sha256": EXPECTED_NORMALIZED_TEXT_SHA256,
    }:
        raise Project278ManualContextProfileError("trusted context source-text identity drifted")
    if profile.get("focus_terms") != list(_FOCUS_KEYS):
        raise Project278ManualContextProfileError("trusted context focus set drifted")
    if profile.get("vocabulary") != list(_CONTEXT_KEYS):
        raise Project278ManualContextProfileError("trusted context vocabulary drifted")
    if profile.get("window_radius_chars") != CONTEXT_RADIUS_CHARS:
        raise Project278ManualContextProfileError("trusted context radius drifted")
    if profile.get("raw_text_exposed") is not False or profile.get("snippets_exposed") is not False:
        raise Project278ManualContextProfileError("trusted context profile exposed source text")

    summary = profile.get("focus_summary")
    if type(summary) is not dict or set(summary) != set(_FOCUS_KEYS):
        raise Project278ManualContextProfileError("trusted context focus summary drifted")
    for focus, value in summary.items():
        if type(value) is not dict or set(value) != {"count", "pages"}:
            raise Project278ManualContextProfileError("trusted context focus-summary shape drifted")
        count = value.get("count")
        pages = value.get("pages")
        if type(count) is not int or isinstance(count, bool) or count <= 0:
            raise Project278ManualContextProfileError("trusted context focus count is invalid")
        if (
            type(pages) is not list
            or pages != sorted(set(pages))
            or any(type(page) is not int or not (1 <= page <= EXPECTED_PAGE_COUNT) for page in pages)
        ):
            raise Project278ManualContextProfileError("trusted context focus pages are invalid")

    records = profile.get("records")
    if type(records) is not list or not (1 <= len(records) <= MAX_CONTEXT_RECORDS):
        raise Project278ManualContextProfileError("trusted context record count is invalid")
    observed_counts = {focus: 0 for focus in _FOCUS_KEYS}
    for record in records:
        if type(record) is not dict or set(record) != {
            "focus",
            "page",
            "occurrence",
            "window_utf8_bytes",
            "window_sha256",
            "nearby_terms",
        }:
            raise Project278ManualContextProfileError("trusted context record shape drifted")
        focus = record.get("focus")
        if focus not in _FOCUS_PATTERNS:
            raise Project278ManualContextProfileError("trusted context record focus drifted")
        page = record.get("page")
        occurrence = record.get("occurrence")
        window_bytes = record.get("window_utf8_bytes")
        if type(page) is not int or not (1 <= page <= EXPECTED_PAGE_COUNT):
            raise Project278ManualContextProfileError("trusted context record page is invalid")
        if type(occurrence) is not int or isinstance(occurrence, bool) or occurrence <= 0:
            raise Project278ManualContextProfileError("trusted context occurrence is invalid")
        if (
            type(window_bytes) is not int
            or isinstance(window_bytes, bool)
            or not (1 <= window_bytes <= MAX_CONTEXT_WINDOW_UTF8_BYTES)
        ):
            raise Project278ManualContextProfileError("trusted context window size is invalid")
        digest = record.get("window_sha256")
        if type(digest) is not str or _DIGEST_RE.fullmatch(digest) is None:
            raise Project278ManualContextProfileError("trusted context window digest is invalid")
        nearby = record.get("nearby_terms")
        if type(nearby) is not dict or not set(nearby).issubset(_CONTEXT_PATTERNS):
            raise Project278ManualContextProfileError("trusted context nearby vocabulary drifted")
        for count in nearby.values():
            if type(count) is not int or isinstance(count, bool) or count <= 0:
                raise Project278ManualContextProfileError("trusted context nearby count is invalid")
        observed_counts[focus] += 1
    for focus, count in observed_counts.items():
        if count != summary[focus]["count"]:
            raise Project278ManualContextProfileError("trusted context focus/record count mismatch")


def _validate_terminal_payload(result: object, *, execution_sha: str) -> bool:
    if type(result) is not dict or set(result) != _RESULT_FIELDS:
        raise Project278ManualContextProfileError("trusted context result fields drifted")
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
            raise Project278ManualContextProfileError(f"trusted context result drifted at {field}")
    if result.get("manual_identity") != _manual_identity():
        raise Project278ManualContextProfileError("trusted context manual identity drifted")
    if result.get("source_profile_identity") != _source_profile_identity():
        raise Project278ManualContextProfileError("trusted context source-profile identity drifted")
    status = result.get("status")
    if status == "pass":
        if result.get("failure_class") is not None or result.get("context_profiled") is not True:
            raise Project278ManualContextProfileError("trusted context PASS state drifted")
        _validate_context_profile(result.get("context_profile"))
        return True
    if status == "blocked":
        if result.get("context_profiled") is not False:
            raise Project278ManualContextProfileError("trusted context BLOCKED widened profile state")
        if result.get("failure_class") not in {"acquisition_failure", "context_profile_failure"}:
            raise Project278ManualContextProfileError("trusted context BLOCKED failure class drifted")
        if result.get("context_profile") is not None:
            raise Project278ManualContextProfileError("trusted context BLOCKED contains a profile")
        return True
    raise Project278ManualContextProfileError("trusted context result has non-terminal status")


def _parse_trusted_terminal_result(body: object, *, execution_sha: str) -> bool:
    if type(body) is not str or RESULT_MARKER not in body:
        return False
    try:
        encoded = body.encode("utf-8", errors="strict")
    except UnicodeEncodeError as exc:
        raise Project278ManualContextProfileError("trusted context result is not UTF-8") from exc
    if len(encoded) > MAX_TERMINAL_UTF8_BYTES:
        raise Project278ManualContextProfileError("trusted context result exceeds byte bound")
    if body.count(RESULT_MARKER) != 1:
        raise Project278ManualContextProfileError("trusted context marker is malformed")
    before, after = body.split(RESULT_MARKER, 1)
    if before.strip() or not after.strip():
        raise Project278ManualContextProfileError("trusted context envelope is malformed")
    result = _load_json(after.strip(), label="trusted context-profile result")
    return _validate_terminal_payload(result, execution_sha=execution_sha)


def has_terminal_context_profile_result(
    *,
    repository: str,
    token: str,
    execution_sha: str,
    opener: Any | None = None,
    max_pages: int = 20,
) -> bool:
    if type(execution_sha) is not str or _SHA_RE.fullmatch(execution_sha) is None:
        raise Project278ManualContextProfileError("invalid execution SHA")
    kwargs: dict[str, Any] = {"issue": CONTROL_ISSUE, "max_pages": max_pages}
    if opener is not None:
        kwargs["opener"] = opener
    try:
        comments = fetch_repository_comments(repository, token, **kwargs)
    except LedgerError as exc:
        raise Project278ManualContextProfileError("context-profile result ledger is incomplete") from exc
    seen = False
    for comment in comments:
        user = comment.get("user")
        login = user.get("login") if type(user) is dict else None
        if login != TRUSTED_RESULT_LOGIN:
            continue
        if _parse_trusted_terminal_result(comment.get("body"), execution_sha=execution_sha):
            seen = True
    return seen


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
    result = run_context_profile(execution_sha=args.execution_sha)
    _validate_terminal_payload(result, execution_sha=args.execution_sha)
    Path(args.output).write_text(
        json.dumps(result, sort_keys=True, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
