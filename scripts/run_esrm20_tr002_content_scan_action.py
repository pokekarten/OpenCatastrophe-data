# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Locate predeclared component terms in the exact receipted ESRM20 TR002 v1.0 PDF.

This is a bounded evidence-location worker, not a scientific interpretation worker.
It reacquires one fixed provider object, re-proves its trusted byte identity, extracts
text transiently with ``pdftotext``, and returns only extractor identity, text/page
fingerprints, and counts/page numbers for four predeclared terms. Provider bytes,
page text, snippets, scientific applicability and model-use authority remain out of
scope.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import tempfile
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Callable

try:
    from scripts.acquire_efehr_gitlab_receipt import (
        EfehrAcquisitionError,
        TOTAL_DEADLINE_SECONDS,
        _DeadlineStream,
        _declared_length,
        _open_fixed,
        _remaining,
        _validate_exact_response,
        utc_now,
    )
    from scripts.efehr_gitlab_receipt import EfehrReceiptError, raw_file_api_url, validate_target
    from scripts.prepare_agent_action_result import LedgerError, fetch_repository_comments
except ModuleNotFoundError:  # pragma: no cover - direct script execution path
    from acquire_efehr_gitlab_receipt import (
        EfehrAcquisitionError,
        TOTAL_DEADLINE_SECONDS,
        _DeadlineStream,
        _declared_length,
        _open_fixed,
        _remaining,
        _validate_exact_response,
        utc_now,
    )
    from efehr_gitlab_receipt import EfehrReceiptError, raw_file_api_url, validate_target
    from prepare_agent_action_result import LedgerError, fetch_repository_comments

REQUEST_MARKER = "<!-- oc-eq1-esrm20-tr002-content-scan-request-v1 -->"
RESULT_MARKER = "<!-- oc-eq1-esrm20-tr002-content-scan-result-v1 -->"
REQUEST_SCHEMA_VERSION = "oc-esrm20-tr002-content-scan-request-v1"
RESULT_SCHEMA_VERSION = "oc-esrm20-tr002-content-scan-result-v1"
SCAN_SCHEMA_VERSION = "oc-esrm20-tr002-content-scan-v1"
ACTION = "esrm20_tr002_exact_content_scan"
CONTROL_ISSUE = 596
SOURCE_SCIENCE_ISSUE = 281
PARENT_CONSUMER_ISSUE = 287
DATASET_ID = "efehr.esrm20.risk-inputs.v1.0"
PROJECT_ID = 269
PROJECT_PATH = "efehr/esrm20"
COMMIT_SHA = "05f83bbc9df81d02ee8ddb1801d9d781355ce783"
REPOSITORY_PATH = "Documentation/EFEHR_TR002_ESRM20.pdf"
EXPECTED_BYTE_COUNT = 19_153_998
EXPECTED_SHA256 = "b4b533e673a542ee796cc6e80db4d7a4232ead9220afd2d1a4fa5a3fa4bedf3d"
MAX_PDF_BYTES = EXPECTED_BYTE_COUNT
MAX_TEXT_BYTES = 16 * 1024 * 1024
MAX_PAGES = 512
PDFTOTEXT = "pdftotext"
TRUSTED_RESULT_LOGIN = "github-actions[bot]"

_SHA_RE = re.compile(r"^[0-9a-f]{40}$")
_DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
_REQUESTER_RE = re.compile(r"^[A-Za-z0-9_.:@/+ -]{1,96}$")
_REQUEST_FIELDS = {"schema_version", "action", "issue", "target_sha", "dataset_id", "requester"}
_TERM_PATTERNS: dict[str, re.Pattern[str]] = {
    "geometric_mean": re.compile(r"(?<![A-Za-z0-9])geometric\s+mean(?![A-Za-z0-9])", re.IGNORECASE),
    "horizontal": re.compile(r"(?<![A-Za-z0-9])horizontal(?![A-Za-z0-9])", re.IGNORECASE),
    "rotd": re.compile(r"(?<![A-Za-z0-9])RotD(?![A-Za-z0-9])", re.IGNORECASE),
    "rotd50": re.compile(r"(?<![A-Za-z0-9])RotD50(?![A-Za-z0-9])", re.IGNORECASE),
}

_CANONICAL_OPEN_FIXED = _open_fixed
_CANONICAL_MONOTONIC = time.monotonic
_CANONICAL_SUBPROCESS_RUN = subprocess.run


class Tr002ContentScanError(RuntimeError):
    """Base error for fail-closed TR002 content scanning."""


class Tr002ContentScanAcquisitionError(Tr002ContentScanError):
    """The exact immutable provider object could not be reacquired and verified."""


class Tr002ContentScanExtractionError(Tr002ContentScanError):
    """The verified PDF could not be converted into bounded text evidence."""


def _pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise Tr002ContentScanError("duplicate JSON key")
        result[key] = value
    return result


def _reject_constant(value: str) -> Any:
    raise Tr002ContentScanError(f"non-finite JSON constant: {value}")


def validate_request(body: object, *, expected_issue: int, execution_sha: str) -> dict[str, Any]:
    if type(expected_issue) is not int or expected_issue != CONTROL_ISSUE:
        raise Tr002ContentScanError("wrong runtime issue")
    if type(execution_sha) is not str or _SHA_RE.fullmatch(execution_sha) is None:
        raise Tr002ContentScanError("invalid execution SHA")
    if type(body) is not str or body.count(REQUEST_MARKER) != 1:
        raise Tr002ContentScanError("invalid TR002 content-scan request marker")
    before, after = body.split(REQUEST_MARKER, 1)
    if before.strip() or not after.strip():
        raise Tr002ContentScanError("TR002 content-scan request envelope is not canonical")
    try:
        request = json.loads(after.strip(), object_pairs_hook=_pairs, parse_constant=_reject_constant)
    except Tr002ContentScanError:
        raise
    except (json.JSONDecodeError, TypeError, ValueError) as exc:
        raise Tr002ContentScanError("invalid TR002 content-scan request JSON") from exc
    if type(request) is not dict or set(request) != _REQUEST_FIELDS:
        raise Tr002ContentScanError("TR002 content-scan request fields drifted")
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
            raise Tr002ContentScanError(f"TR002 content-scan request {field} drifted")
    requester = request["requester"]
    if type(requester) is not str or requester != requester.strip() or _REQUESTER_RE.fullmatch(requester) is None:
        raise Tr002ContentScanError("invalid requester identity")
    return request


def _extractor_identity(*, runner: Callable[..., Any]) -> str:
    try:
        completed = runner(
            [PDFTOTEXT, "-v"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=5,
            check=False,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        raise Tr002ContentScanExtractionError("pdftotext capability is unavailable") from exc
    if completed.returncode != 0:
        raise Tr002ContentScanExtractionError("pdftotext version probe failed")
    output = bytes(completed.stderr or b"") + b"\n" + bytes(completed.stdout or b"")
    try:
        lines = [line.strip() for line in output.decode("utf-8", errors="strict").splitlines() if line.strip()]
    except UnicodeDecodeError as exc:
        raise Tr002ContentScanExtractionError("pdftotext version output is not UTF-8") from exc
    if not lines or not lines[0].startswith("pdftotext version "):
        raise Tr002ContentScanExtractionError("pdftotext identity is not recognized")
    identity = lines[0]
    if len(identity.encode("utf-8")) > 160 or any(ord(char) < 32 or ord(char) == 127 for char in identity):
        raise Tr002ContentScanExtractionError("pdftotext identity is unsafe")
    return identity


def _extract_pages(
    pdf_path: Path, *, runner: Callable[..., Any]
) -> tuple[list[str], int, str, str]:
    identity = _extractor_identity(runner=runner)
    try:
        completed = runner(
            [PDFTOTEXT, "-enc", "UTF-8", "-layout", str(pdf_path), "-"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=90,
            check=False,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        raise Tr002ContentScanExtractionError("pdftotext extraction failed") from exc
    if completed.returncode != 0:
        raise Tr002ContentScanExtractionError("pdftotext returned non-zero")
    raw = bytes(completed.stdout or b"")
    if not raw or len(raw) > MAX_TEXT_BYTES:
        raise Tr002ContentScanExtractionError("pdftotext output size is outside bounds")
    if b"\x00" in raw:
        raise Tr002ContentScanExtractionError("pdftotext output contains NUL")
    try:
        text = raw.decode("utf-8", errors="strict")
    except UnicodeDecodeError as exc:
        raise Tr002ContentScanExtractionError("pdftotext output is not strict UTF-8") from exc
    pages = text.split("\f")
    while pages and not pages[-1].strip():
        pages.pop()
    if not pages or len(pages) > MAX_PAGES:
        raise Tr002ContentScanExtractionError("pdftotext page count is outside bounds")
    return pages, len(raw), hashlib.sha256(raw).hexdigest(), identity


def summarize_pages(
    pages: object,
    *,
    extracted_text_bytes: int,
    extracted_text_sha256: str,
    extractor_identity: str,
) -> dict[str, Any]:
    if type(pages) is not list or not pages or len(pages) > MAX_PAGES:
        raise Tr002ContentScanExtractionError("extracted pages are outside bounds")
    if any(type(page) is not str for page in pages):
        raise Tr002ContentScanExtractionError("extracted page is not text")
    if type(extracted_text_bytes) is not int or isinstance(extracted_text_bytes, bool) or not (1 <= extracted_text_bytes <= MAX_TEXT_BYTES):
        raise Tr002ContentScanExtractionError("extracted text byte count is invalid")
    if type(extracted_text_sha256) is not str or _DIGEST_RE.fullmatch(extracted_text_sha256) is None:
        raise Tr002ContentScanExtractionError("extracted text digest is invalid")
    if type(extractor_identity) is not str or not extractor_identity.startswith("pdftotext version "):
        raise Tr002ContentScanExtractionError("extractor identity is invalid")

    terms: dict[str, dict[str, Any]] = {}
    for label, pattern in _TERM_PATTERNS.items():
        hit_pages: list[int] = []
        count = 0
        for page_number, page in enumerate(pages, start=1):
            hits = list(pattern.finditer(page))
            if hits:
                hit_pages.append(page_number)
                count += len(hits)
        terms[label] = {"count": count, "pages": hit_pages}

    return {
        "schema_version": SCAN_SCHEMA_VERSION,
        "extractor_identity": extractor_identity,
        "page_count": len(pages),
        "extracted_text_bytes": extracted_text_bytes,
        "extracted_text_sha256": extracted_text_sha256,
        "terms": terms,
        "page_text_returned": False,
        "snippets_returned": False,
    }


def _scan_exact_pdf(*, opener: Callable[..., Any], monotonic: Callable[[], float], runner: Callable[..., Any]) -> dict[str, Any]:
    deadline = monotonic() + TOTAL_DEADLINE_SECONDS
    try:
        target = validate_target(
            source_issue=SOURCE_SCIENCE_ISSUE,
            dataset_id=DATASET_ID,
            project_id=PROJECT_ID,
            commit_sha=COMMIT_SHA,
            repository_path=REPOSITORY_PATH,
        )
        if target.project_path != PROJECT_PATH:
            raise Tr002ContentScanAcquisitionError("provider project path drifted")
        url = raw_file_api_url(target)
        request = urllib.request.Request(
            url,
            headers={
                "Accept": "application/pdf,application/octet-stream;q=0.9",
                "User-Agent": "OpenCatastrophe-EFEHR-TR002-content-scan-v1",
            },
            method="GET",
        )
        with tempfile.TemporaryDirectory(prefix="oc-tr002-") as tmpdir:
            pdf_path = Path(tmpdir) / "tr002-v1.0.pdf"
            with opener(request, timeout=_remaining(deadline, monotonic)) as response:
                _validate_exact_response(response, url)
                declared = _declared_length(response, MAX_PDF_BYTES)
                if declared is not None and declared != EXPECTED_BYTE_COUNT:
                    raise Tr002ContentScanAcquisitionError("TR002 declared byte count differs from trusted receipt")
                retrieved_at = utc_now()
                stream = _DeadlineStream(response, deadline=deadline, monotonic=monotonic)
                digest = hashlib.sha256()
                byte_count = 0
                prefix = b""
                with pdf_path.open("wb") as handle:
                    while True:
                        chunk = stream.read(64 * 1024)
                        if not chunk:
                            break
                        if type(chunk) is not bytes:
                            raise Tr002ContentScanAcquisitionError("provider stream returned non-bytes")
                        byte_count += len(chunk)
                        if byte_count > EXPECTED_BYTE_COUNT:
                            raise Tr002ContentScanAcquisitionError("TR002 byte count exceeded trusted receipt")
                        if len(prefix) < 5:
                            prefix = (prefix + chunk)[:5]
                        digest.update(chunk)
                        handle.write(chunk)
                if prefix != b"%PDF-":
                    raise Tr002ContentScanAcquisitionError("TR002 provider payload lacks PDF magic")
                if byte_count != EXPECTED_BYTE_COUNT:
                    raise Tr002ContentScanAcquisitionError("TR002 byte count does not match trusted receipt")
                observed_digest = digest.hexdigest()
                if observed_digest != EXPECTED_SHA256:
                    raise Tr002ContentScanAcquisitionError("TR002 SHA-256 does not match trusted receipt")

            pages, text_bytes, text_digest, extractor_identity = _extract_pages(pdf_path, runner=runner)
            scan = summarize_pages(
                pages,
                extracted_text_bytes=text_bytes,
                extracted_text_sha256=text_digest,
                extractor_identity=extractor_identity,
            )
            scan["source"] = {
                "dataset_id": DATASET_ID,
                "project_id": PROJECT_ID,
                "project_path": PROJECT_PATH,
                "commit_sha": COMMIT_SHA,
                "repository_path": REPOSITORY_PATH,
                "retrieved_at": retrieved_at,
                "byte_count": byte_count,
                "sha256": observed_digest,
            }
            return scan
    except Tr002ContentScanError:
        raise
    except (EfehrAcquisitionError, EfehrReceiptError, OSError, urllib.error.URLError, urllib.error.HTTPError, TimeoutError) as exc:
        raise Tr002ContentScanAcquisitionError(f"TR002 acquisition failed: {type(exc).__name__}") from exc


def scan_exact_tr002() -> dict[str, Any]:
    if _open_fixed is not _CANONICAL_OPEN_FIXED or time.monotonic is not _CANONICAL_MONOTONIC:
        raise Tr002ContentScanAcquisitionError("TR002 production transport identity drifted")
    if subprocess.run is not _CANONICAL_SUBPROCESS_RUN:
        raise Tr002ContentScanExtractionError("TR002 extractor process authority drifted")
    return _scan_exact_pdf(
        opener=_CANONICAL_OPEN_FIXED,
        monotonic=_CANONICAL_MONOTONIC,
        runner=_CANONICAL_SUBPROCESS_RUN,
    )


def _validate_scan(scan: object) -> dict[str, Any]:
    if type(scan) is not dict:
        raise Tr002ContentScanError("scan payload is absent")
    for field, expected in (
        ("schema_version", SCAN_SCHEMA_VERSION),
        ("page_text_returned", False),
        ("snippets_returned", False),
    ):
        observed = scan.get(field)
        if type(observed) is not type(expected) or observed != expected:
            raise Tr002ContentScanError(f"scan payload drifted at {field}")
    identity = scan.get("extractor_identity")
    if type(identity) is not str or not identity.startswith("pdftotext version ") or len(identity.encode("utf-8")) > 160:
        raise Tr002ContentScanError("scan extractor identity is invalid")
    page_count = scan.get("page_count")
    if type(page_count) is not int or isinstance(page_count, bool) or not (1 <= page_count <= MAX_PAGES):
        raise Tr002ContentScanError("scan page count is invalid")
    text_bytes = scan.get("extracted_text_bytes")
    if type(text_bytes) is not int or isinstance(text_bytes, bool) or not (1 <= text_bytes <= MAX_TEXT_BYTES):
        raise Tr002ContentScanError("scan text byte count is invalid")
    text_digest = scan.get("extracted_text_sha256")
    if type(text_digest) is not str or _DIGEST_RE.fullmatch(text_digest) is None:
        raise Tr002ContentScanError("scan text digest is invalid")

    terms = scan.get("terms")
    if type(terms) is not dict or set(terms) != set(_TERM_PATTERNS):
        raise Tr002ContentScanError("scan term set drifted")
    for label in sorted(_TERM_PATTERNS):
        record = terms[label]
        if type(record) is not dict or set(record) != {"count", "pages"}:
            raise Tr002ContentScanError("scan term record shape drifted")
        count = record["count"]
        hit_pages = record["pages"]
        if type(count) is not int or isinstance(count, bool) or count < 0:
            raise Tr002ContentScanError("scan term count is invalid")
        if type(hit_pages) is not list or hit_pages != sorted(set(hit_pages)):
            raise Tr002ContentScanError("scan term pages are not sorted unique")
        if any(type(page) is not int or isinstance(page, bool) or not (1 <= page <= page_count) for page in hit_pages):
            raise Tr002ContentScanError("scan term page is outside bounds")
        if count < len(hit_pages):
            raise Tr002ContentScanError("scan term count cannot be smaller than hit-page count")

    source = scan.get("source")
    expected_keys = {
        "dataset_id", "project_id", "project_path", "commit_sha", "repository_path",
        "retrieved_at", "byte_count", "sha256",
    }
    if type(source) is not dict or set(source) != expected_keys:
        raise Tr002ContentScanError("scan source shape drifted")
    for field, expected in (
        ("dataset_id", DATASET_ID),
        ("project_id", PROJECT_ID),
        ("project_path", PROJECT_PATH),
        ("commit_sha", COMMIT_SHA),
        ("repository_path", REPOSITORY_PATH),
        ("byte_count", EXPECTED_BYTE_COUNT),
        ("sha256", EXPECTED_SHA256),
    ):
        observed = source.get(field)
        if type(observed) is not type(expected) or observed != expected:
            raise Tr002ContentScanError(f"scan source drifted at {field}")
    if type(source.get("retrieved_at")) is not str or not source["retrieved_at"]:
        raise Tr002ContentScanError("scan retrieval time is invalid")
    return scan


def _base_result(*, execution_sha: str) -> dict[str, Any]:
    return {
        "schema_version": RESULT_SCHEMA_VERSION,
        "action": ACTION,
        "source_issue": CONTROL_ISSUE,
        "source_science_issue": SOURCE_SCIENCE_ISSUE,
        "parent_consumer_issue": PARENT_CONSUMER_ISSUE,
        "dataset_id": DATASET_ID,
        "target_sha": execution_sha,
        "execution_sha": execution_sha,
        "component_semantics_verified": False,
        "horizontal_component_interoperability_authorized": False,
        "external_bytes_persisted": False,
        "publication_authorized": False,
        "model_use_authorized": False,
    }


def run_scan(*, execution_sha: str, scanner: Callable[[], dict[str, Any]] = scan_exact_tr002) -> dict[str, Any]:
    if type(execution_sha) is not str or _SHA_RE.fullmatch(execution_sha) is None:
        raise Tr002ContentScanError("invalid execution SHA")
    result = _base_result(execution_sha=execution_sha)
    try:
        scan = _validate_scan(scanner())
    except Tr002ContentScanAcquisitionError:
        result.update({
            "status": "blocked",
            "failure_class": "acquisition_failure",
            "byte_identity_verified": False,
            "text_location_scan_verified": False,
            "scan": None,
        })
        return result
    except Tr002ContentScanExtractionError:
        result.update({
            "status": "blocked",
            "failure_class": "content_extraction_failure",
            "byte_identity_verified": True,
            "text_location_scan_verified": False,
            "scan": None,
        })
        return result
    result.update({
        "status": "pass",
        "failure_class": None,
        "byte_identity_verified": True,
        "text_location_scan_verified": True,
        "scan": scan,
    })
    return result


def _parse_terminal_result(body: object, *, execution_sha: str) -> bool:
    if type(body) is not str or RESULT_MARKER not in body:
        return False
    if type(execution_sha) is not str or _SHA_RE.fullmatch(execution_sha) is None:
        raise Tr002ContentScanError("invalid execution SHA")
    if body.count(RESULT_MARKER) != 1:
        raise Tr002ContentScanError("trusted result marker is malformed")
    before, after = body.split(RESULT_MARKER, 1)
    if before.strip() or not after.strip():
        raise Tr002ContentScanError("trusted result envelope is malformed")
    try:
        result = json.loads(after.strip(), object_pairs_hook=_pairs, parse_constant=_reject_constant)
    except Tr002ContentScanError:
        raise
    except (json.JSONDecodeError, TypeError, ValueError) as exc:
        raise Tr002ContentScanError("trusted result JSON is malformed") from exc
    if type(result) is not dict:
        raise Tr002ContentScanError("trusted result is not an object")
    result_execution_sha = result.get("execution_sha")
    if type(result_execution_sha) is not str or _SHA_RE.fullmatch(result_execution_sha) is None:
        raise Tr002ContentScanError("trusted result execution SHA is invalid")
    for field, expected in _base_result(execution_sha=result_execution_sha).items():
        observed = result.get(field)
        if type(observed) is not type(expected) or observed != expected:
            raise Tr002ContentScanError(f"trusted result drifted at {field}")
    status = result.get("status")
    if status == "pass":
        if result.get("failure_class") is not None:
            raise Tr002ContentScanError("trusted PASS has failure class")
        if result.get("byte_identity_verified") is not True or result.get("text_location_scan_verified") is not True:
            raise Tr002ContentScanError("trusted PASS lacks verified scan gates")
        _validate_scan(result.get("scan"))
        return result_execution_sha == execution_sha
    if status == "blocked":
        failure = result.get("failure_class")
        if failure == "acquisition_failure":
            expected_gates = (False, False)
        elif failure == "content_extraction_failure":
            expected_gates = (True, False)
        else:
            raise Tr002ContentScanError("trusted blocked result has invalid failure class")
        if (result.get("byte_identity_verified"), result.get("text_location_scan_verified")) != expected_gates:
            raise Tr002ContentScanError("trusted blocked result has invalid verification gates")
        if result.get("scan") is not None:
            raise Tr002ContentScanError("trusted blocked result leaked scan evidence")
        return result_execution_sha == execution_sha
    raise Tr002ContentScanError("trusted result has non-terminal status")


def has_terminal_result(
    *, repository: str, token: str, execution_sha: str, opener: Any | None = None, max_pages: int = 20
) -> bool:
    if type(execution_sha) is not str or _SHA_RE.fullmatch(execution_sha) is None:
        raise Tr002ContentScanError("invalid execution SHA")
    kwargs: dict[str, Any] = {"issue": CONTROL_ISSUE, "max_pages": max_pages}
    if opener is not None:
        kwargs["opener"] = opener
    try:
        comments = fetch_repository_comments(repository, token, **kwargs)
    except LedgerError as exc:
        raise Tr002ContentScanError("result ledger is incomplete") from exc
    for comment in comments:
        user = comment.get("user")
        login = user.get("login") if type(user) is dict else None
        if login != TRUSTED_RESULT_LOGIN:
            continue
        if _parse_terminal_result(comment.get("body"), execution_sha=execution_sha):
            return True
    return False


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
        raise Tr002ContentScanError("--output is required for execution")
    result = run_scan(execution_sha=args.execution_sha)
    Path(args.output).write_text(
        json.dumps(result, sort_keys=True, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
