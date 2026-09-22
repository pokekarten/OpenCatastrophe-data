#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Metadata-only provenance check for the ESRM20 Country Viewer result link.

This diagnostic does not download the provider CSV body. It follows the exact
legacy viewer-linked raw URL with HEAD only, verifies the canonical public
project identity, and asks GitLab's repository-files HEAD endpoint for the
current main-branch Git blob identity. The resulting blob identity is compared
with the already trusted-main-bound ESRM20 v1.0 country-risk blob.

No numerical provider value is read or interpreted.
"""

from __future__ import annotations

import json
import re
from typing import Any, Mapping
import urllib.error
import urllib.parse
import urllib.request

PROVIDER_HOST = "gitlab.seismo.ethz.ch"
PROVIDER_ROOT = f"https://{PROVIDER_HOST}"

LEGACY_PROJECT_PATH = "efehr/esrm20_openquake"
CANONICAL_PROJECT_ID = 269
CANONICAL_PROJECT_PATH = "efehr/esrm20"
DEFAULT_BRANCH = "main"
COUNTRY_RISK_PATH = "Risk/European_Risk_Country.csv"

# Trusted-main #778 result from 2026-09-22.
FROZEN_V10_BLOB_SHA1 = "17465680342d46de4e29c90cfaab018e63faafd3"
FROZEN_V10_SHA256 = "95584a1de1fce1f65e29ea0f8beb5ff87b9489c9e9cca71949791427482312fb"
FROZEN_V10_BYTE_COUNT = 4225
FROZEN_V10_COMMIT = "05f83bbc9df81d02ee8ddb1801d9d781355ce783"

MAX_PROJECT_METADATA_BYTES = 64 * 1024
GIT_SHA_RE = re.compile(r"^[a-f0-9]{40}$")
SHA256_RE = re.compile(r"^[a-f0-9]{64}$")

LEGACY_VIEWER_RAW_URL = (
    f"{PROVIDER_ROOT}/{LEGACY_PROJECT_PATH}/-/raw/{DEFAULT_BRANCH}/"
    "Risk/European_Risk_Country.csv?inline=false"
)
CANONICAL_VIEWER_RAW_PATH = (
    f"/{CANONICAL_PROJECT_PATH}/-/raw/{DEFAULT_BRANCH}/{COUNTRY_RISK_PATH}"
)
CANONICAL_PROJECT_API_URL = f"{PROVIDER_ROOT}/api/v4/projects/{CANONICAL_PROJECT_ID}"
CANONICAL_FILE_HEAD_URL = (
    f"{PROVIDER_ROOT}/api/v4/projects/{CANONICAL_PROJECT_ID}/repository/files/"
    f"{urllib.parse.quote(COUNTRY_RISK_PATH, safe='')}?ref={DEFAULT_BRANCH}"
)


class ViewerProvenanceError(RuntimeError):
    """Raised when provider metadata violates the bounded provenance contract."""


def _validate_https_provider_url(url: str) -> urllib.parse.SplitResult:
    if type(url) is not str or not url:
        raise ViewerProvenanceError("provider URL is missing")
    parsed = urllib.parse.urlsplit(url)
    if (
        parsed.scheme != "https"
        or parsed.hostname != PROVIDER_HOST
        or parsed.username is not None
        or parsed.password is not None
        or parsed.port not in (None, 443)
        or parsed.fragment
    ):
        raise ViewerProvenanceError("provider response left the fixed HTTPS host boundary")
    return parsed


def _parse_project_metadata(payload: bytes) -> dict[str, Any]:
    if type(payload) is not bytes or not payload:
        raise ViewerProvenanceError("project metadata payload is empty")
    if len(payload) > MAX_PROJECT_METADATA_BYTES:
        raise ViewerProvenanceError("project metadata payload exceeds bounded policy")
    try:
        value = json.loads(payload.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ViewerProvenanceError("project metadata is not valid UTF-8 JSON") from exc
    if type(value) is not dict:
        raise ViewerProvenanceError("project metadata must be a JSON object")

    required = ("id", "path_with_namespace", "default_branch", "web_url")
    if any(field not in value for field in required):
        raise ViewerProvenanceError("project metadata is missing required identity fields")
    if value["id"] != CANONICAL_PROJECT_ID:
        raise ViewerProvenanceError("canonical project id drifted")
    if value["path_with_namespace"] != CANONICAL_PROJECT_PATH:
        raise ViewerProvenanceError("canonical project path drifted")
    if value["default_branch"] != DEFAULT_BRANCH:
        raise ViewerProvenanceError("canonical default branch drifted")
    expected_web_url = f"{PROVIDER_ROOT}/{CANONICAL_PROJECT_PATH}"
    if value["web_url"] != expected_web_url:
        raise ViewerProvenanceError("canonical project web URL drifted")

    return {
        "project_id": CANONICAL_PROJECT_ID,
        "project_path": CANONICAL_PROJECT_PATH,
        "default_branch": DEFAULT_BRANCH,
        "web_url": expected_web_url,
    }


def _header(headers: Mapping[str, Any], name: str) -> str | None:
    value = None
    for key, candidate in headers.items():
        if type(key) is str and key.casefold() == name.casefold():
            value = candidate
            break
    if value is None:
        return None
    if type(value) is not str:
        value = str(value)
    if any(ord(ch) < 0x20 or ord(ch) == 0x7F for ch in value):
        raise ViewerProvenanceError(f"{name} contains control characters")
    return value.strip()


def _parse_file_head(headers: Mapping[str, Any]) -> dict[str, Any]:
    blob_id = _header(headers, "X-Gitlab-Blob-Id")
    content_sha256 = _header(headers, "X-Gitlab-Content-Sha256")
    size_text = _header(headers, "X-Gitlab-Size")
    ref = _header(headers, "X-Gitlab-Ref")
    file_path = _header(headers, "X-Gitlab-File-Path")
    commit_id = _header(headers, "X-Gitlab-Commit-Id")
    last_commit_id = _header(headers, "X-Gitlab-Last-Commit-Id")

    if blob_id is None or not GIT_SHA_RE.fullmatch(blob_id):
        raise ViewerProvenanceError("GitLab file HEAD lacks a valid blob id")
    if content_sha256 is not None and not SHA256_RE.fullmatch(content_sha256):
        raise ViewerProvenanceError("GitLab file HEAD has an invalid content SHA-256")
    if size_text is None or not size_text.isdigit():
        raise ViewerProvenanceError("GitLab file HEAD lacks a valid byte size")
    size = int(size_text)
    if size < 1 or size > 10_000_000:
        raise ViewerProvenanceError("GitLab file HEAD byte size is outside bounded policy")
    if ref != DEFAULT_BRANCH:
        raise ViewerProvenanceError("GitLab file HEAD ref drifted")
    if file_path != COUNTRY_RISK_PATH:
        raise ViewerProvenanceError("GitLab file HEAD path drifted")
    for field, value in (("commit_id", commit_id), ("last_commit_id", last_commit_id)):
        if value is not None and not GIT_SHA_RE.fullmatch(value):
            raise ViewerProvenanceError(f"GitLab file HEAD {field} is invalid")

    return {
        "blob_id": blob_id,
        "content_sha256": content_sha256,
        "size": size,
        "ref": ref,
        "file_path": file_path,
        "commit_id": commit_id,
        "last_commit_id": last_commit_id,
    }


def _is_canonical_viewer_raw_url(url: str) -> bool:
    parsed = _validate_https_provider_url(url)
    if parsed.path != CANONICAL_VIEWER_RAW_PATH:
        return False
    query = urllib.parse.parse_qs(parsed.query, keep_blank_values=True)
    return query in ({}, {"inline": ["false"]})


def _legacy_redirect_matches(final_url: str, redirect_chain: list[str] | None = None) -> bool:
    candidates = list(redirect_chain or []) + [final_url]
    return any(_is_canonical_viewer_raw_url(url) for url in candidates)


def build_result(
    *,
    legacy_final_url: str,
    legacy_redirect_chain: list[str] | None = None,
    project_metadata: dict[str, Any],
    file_metadata: dict[str, Any],
) -> dict[str, Any]:
    canonical_project_verified = (
        project_metadata.get("project_id") == CANONICAL_PROJECT_ID
        and project_metadata.get("project_path") == CANONICAL_PROJECT_PATH
        and project_metadata.get("default_branch") == DEFAULT_BRANCH
    )
    legacy_redirect_chain = list(legacy_redirect_chain or [])
    legacy_raw_redirects_to_canonical = _legacy_redirect_matches(
        legacy_final_url, legacy_redirect_chain
    )
    main_blob_matches_frozen = (
        file_metadata.get("blob_id") == FROZEN_V10_BLOB_SHA1
        and file_metadata.get("size") == FROZEN_V10_BYTE_COUNT
    )
    main_content_sha256_matches_frozen = (
        file_metadata.get("content_sha256") == FROZEN_V10_SHA256
    )
    exact_equivalence = (
        canonical_project_verified
        and legacy_raw_redirects_to_canonical
        and main_blob_matches_frozen
    )

    if not canonical_project_verified:
        conclusion = "CANONICAL_PROJECT_IDENTITY_BLOCKED"
    elif not legacy_raw_redirects_to_canonical:
        conclusion = "LEGACY_VIEWER_RAW_TARGET_NOT_CANONICALIZED"
    elif not main_blob_matches_frozen:
        conclusion = "VIEWER_MAIN_BLOB_DIFFERS_FROM_FROZEN_V1_0"
    else:
        conclusion = "VIEWER_MAIN_BLOB_IDENTICAL_TO_FROZEN_V1_0"

    return {
        "schema_version": "oc-esrm20-country-viewer-provenance-v1",
        "status": "PROVENANCE_DIAGNOSTIC_ONLY",
        "question": (
            "Does the official legacy Country Viewer result link resolve to canonical "
            "ESRM20 Project 269 main, and is that main file the same Git blob as the "
            "trusted frozen v1.0 country-risk artifact?"
        ),
        "legacy_viewer_raw_url": LEGACY_VIEWER_RAW_URL,
        "legacy_viewer_raw_final_url": legacy_final_url,
        "legacy_viewer_raw_redirect_chain": legacy_redirect_chain,
        "legacy_raw_redirects_to_canonical": legacy_raw_redirects_to_canonical,
        "canonical_project": project_metadata,
        "canonical_project_verified": canonical_project_verified,
        "main_file_metadata": file_metadata,
        "frozen_v10": {
            "commit_sha": FROZEN_V10_COMMIT,
            "blob_sha1": FROZEN_V10_BLOB_SHA1,
            "sha256": FROZEN_V10_SHA256,
            "byte_count": FROZEN_V10_BYTE_COUNT,
        },
        "main_blob_matches_frozen": main_blob_matches_frozen,
        "main_content_sha256_matches_frozen": main_content_sha256_matches_frozen,
        "viewer_main_byte_equivalence_verified": exact_equivalence,
        "provider_file_body_read": False,
        "external_bytes_persisted": False,
        "provider_numeric_values_interpreted": False,
        "denominator_semantics_verified": False,
        "threshold_compatibility_verified": False,
        "reference_loss_agreement_verified": False,
        "publication_authorized": False,
        "model_use_authorized": False,
        "conclusion": conclusion,
    }


class _RedirectRecorder(urllib.request.HTTPRedirectHandler):
    def __init__(self) -> None:
        super().__init__()
        self.locations: list[str] = []

    def redirect_request(
        self,
        req: urllib.request.Request,
        fp: Any,
        code: int,
        msg: str,
        headers: Mapping[str, Any],
        newurl: str,
    ) -> urllib.request.Request | None:
        _validate_https_provider_url(newurl)
        self.locations.append(newurl)
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def _open_head(url: str) -> tuple[str, Mapping[str, Any], list[str]]:
    request = urllib.request.Request(
        url,
        method="HEAD",
        headers={"User-Agent": "OpenCatastrophe-data provenance diagnostic"},
    )
    recorder = _RedirectRecorder()
    opener = urllib.request.build_opener(recorder)
    with opener.open(request, timeout=60) as response:
        if getattr(response, "status", 200) != 200:
            raise ViewerProvenanceError("provider HEAD request did not return HTTP 200")
        final_url = response.geturl()
        _validate_https_provider_url(final_url)
        return final_url, response.headers, recorder.locations


def _open_project_metadata() -> bytes:
    request = urllib.request.Request(
        CANONICAL_PROJECT_API_URL,
        method="GET",
        headers={
            "Accept": "application/json",
            "User-Agent": "OpenCatastrophe-data provenance diagnostic",
        },
    )
    with urllib.request.urlopen(request, timeout=60) as response:
        if getattr(response, "status", 200) != 200:
            raise ViewerProvenanceError("canonical project metadata did not return HTTP 200")
        _validate_https_provider_url(response.geturl())
        payload = response.read(MAX_PROJECT_METADATA_BYTES + 1)
    if len(payload) > MAX_PROJECT_METADATA_BYTES:
        raise ViewerProvenanceError("canonical project metadata exceeds bounded policy")
    return payload


def run() -> dict[str, Any]:
    legacy_final_url, _, legacy_redirect_chain = _open_head(LEGACY_VIEWER_RAW_URL)
    project_metadata = _parse_project_metadata(_open_project_metadata())
    file_final_url, file_headers, file_redirect_chain = _open_head(CANONICAL_FILE_HEAD_URL)
    if file_redirect_chain:
        raise ViewerProvenanceError("canonical file metadata request redirected unexpectedly")
    expected_file_api_path = urllib.parse.urlsplit(CANONICAL_FILE_HEAD_URL).path
    if urllib.parse.urlsplit(file_final_url).path != expected_file_api_path:
        raise ViewerProvenanceError("canonical file metadata request redirected unexpectedly")
    file_metadata = _parse_file_head(file_headers)
    return build_result(
        legacy_final_url=legacy_final_url,
        legacy_redirect_chain=legacy_redirect_chain,
        project_metadata=project_metadata,
        file_metadata=file_metadata,
    )


def main() -> int:
    try:
        result = run()
    except (ViewerProvenanceError, urllib.error.URLError) as exc:
        print(
            json.dumps(
                {
                    "schema_version": "oc-esrm20-country-viewer-provenance-v1",
                    "status": "BLOCKED",
                    "error": str(exc),
                    "provider_file_body_read": False,
                    "external_bytes_persisted": False,
                    "reference_loss_agreement_verified": False,
                },
                sort_keys=True,
            )
        )
        return 2
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
