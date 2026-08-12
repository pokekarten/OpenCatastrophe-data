# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Fail-closed primitives for bounded public EFEHR GitLab artifact receipts.

This module deliberately does not perform network I/O. It validates a closed
P0 target, constructs the exact public GitLab raw-file identity, and turns an
already-opened byte stream into a deterministic receipt. Trusted workflow
wiring is a separate Tier-2 step.
"""

from __future__ import annotations

import hashlib
import ipaddress
import re
import urllib.parse
from dataclasses import dataclass
from datetime import datetime
from typing import Any, BinaryIO, Iterable, Mapping

SCHEMA_VERSION = "oc-efehr-gitlab-artifact-receipt-v1"
PROVIDER_HOST = "gitlab.seismo.ethz.ch"
PROVIDER_ROOT = f"https://{PROVIDER_HOST}"
GIT_SHA_RE = re.compile(r"^[a-f0-9]{40}$")
SAFE_DATASET_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,159}$")
UTC_TIMESTAMP_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,6})?Z$")
MAX_PATH_BYTES = 512
MAX_HEADER_BYTES = 1024
MAX_FILE_BYTES = 64 * 1024 * 1024
CHUNK_SIZE = 64 * 1024

PROJECTS: dict[int, dict[str, Any]] = {
    197: {
        "project_path": "efehr/eshm20",
        "issues": frozenset({281}),
        "datasets": frozenset({"efehr.eshm20"}),
    },
    186: {
        "project_path": "efehr/esrm20_exposure",
        "issues": frozenset({282}),
        "datasets": frozenset({"efehr.esrm20.european-exposure-model.v1.0"}),
    },
    188: {
        "project_path": "efehr/esrm20_vulnerability",
        "issues": frozenset({283}),
        "datasets": frozenset({"efehr.esrm20.vulnerability.v1.1"}),
    },
    269: {
        "project_path": "efehr/esrm20",
        "issues": frozenset({283}),
        "datasets": frozenset({"efehr.esrm20.vulnerability.v1.1"}),
    },
}

EXACT_PATHS: dict[tuple[int, int], frozenset[str]] = {
    (282, 186): frozenset(
        {
            "_exposure_models/Exposure_Model_Kosovo_Res.csv",
            "_exposure_models/ReadMe_Exposure_Model_Format.txt",
        }
    ),
    (283, 269): frozenset(
        {
            "Vulnerability/esrm20_exposure_vulnerability_mapping.csv",
        }
    ),
}

ESHM20_PREFIX = "oq_computational/oq_configuration_eshm20_v12e_region_main/"
ESHM20_SUFFIXES = frozenset({".xml", ".ini", ".csv", ".txt", ".json"})


class EfehrReceiptError(ValueError):
    """Raised when an EFEHR receipt target or payload violates the closed policy."""


@dataclass(frozen=True)
class ArtifactTarget:
    source_issue: int
    dataset_id: str
    project_id: int
    commit_sha: str
    repository_path: str

    @property
    def project_path(self) -> str:
        return str(PROJECTS[self.project_id]["project_path"])


def _validate_repository_path(path: str) -> str:
    if type(path) is not str or not path:
        raise EfehrReceiptError("repository_path must be a non-empty string")
    if len(path.encode("utf-8")) > MAX_PATH_BYTES:
        raise EfehrReceiptError("repository_path exceeds byte-length bound")
    if path.startswith("/") or path.endswith("/") or "\\" in path:
        raise EfehrReceiptError("repository_path must be canonical repository-relative POSIX path")
    if any(ord(ch) < 0x20 or ord(ch) == 0x7F for ch in path):
        raise EfehrReceiptError("repository_path contains control characters")
    if any(ch in path for ch in ("?", "#", "%")):
        raise EfehrReceiptError("repository_path contains URL-ambiguous characters")
    parts = path.split("/")
    if any(part in ("", ".", "..") for part in parts):
        raise EfehrReceiptError("repository_path contains unsafe path segments")
    return path


def validate_target(
    *,
    source_issue: int,
    dataset_id: str,
    project_id: int,
    commit_sha: str,
    repository_path: str,
) -> ArtifactTarget:
    """Validate one immutable P0 EFEHR target and return its canonical identity."""
    if type(source_issue) is not int or source_issue not in {281, 282, 283}:
        raise EfehrReceiptError("source_issue is outside the P0 EFEHR allow-list")
    if type(dataset_id) is not str or not SAFE_DATASET_RE.fullmatch(dataset_id):
        raise EfehrReceiptError("dataset_id is invalid")
    if type(project_id) is not int or project_id not in PROJECTS:
        raise EfehrReceiptError("project_id is outside the EFEHR allow-list")
    project = PROJECTS[project_id]
    if source_issue not in project["issues"] or dataset_id not in project["datasets"]:
        raise EfehrReceiptError("issue/dataset/project binding is not allow-listed")
    if type(commit_sha) is not str or not GIT_SHA_RE.fullmatch(commit_sha):
        raise EfehrReceiptError("commit_sha must be an immutable lowercase 40-character Git SHA")
    path = _validate_repository_path(repository_path)

    exact = EXACT_PATHS.get((source_issue, project_id))
    if exact is not None:
        if path not in exact:
            raise EfehrReceiptError("repository_path is outside the exact P0 file allow-list")
    elif source_issue == 281 and project_id == 197:
        if not path.startswith(ESHM20_PREFIX):
            raise EfehrReceiptError("ESHM20 path is outside the selected computational configuration")
        lowered = path.casefold()
        if not any(lowered.endswith(suffix) for suffix in ESHM20_SUFFIXES):
            raise EfehrReceiptError("ESHM20 path has an unsupported file type")
    else:
        # Vulnerability v1.1 file IDs must first be derived from the exact mapping bytes.
        raise EfehrReceiptError("target requires an exact source-derived file allow-list before acquisition")

    return ArtifactTarget(
        source_issue=source_issue,
        dataset_id=dataset_id,
        project_id=project_id,
        commit_sha=commit_sha,
        repository_path=path,
    )


def raw_file_api_url(target: ArtifactTarget) -> str:
    """Return the exact fixed-host GitLab API raw-file URL for a validated target."""
    if type(target) is not ArtifactTarget:
        raise EfehrReceiptError("target must be a validated ArtifactTarget")
    encoded_path = urllib.parse.quote(target.repository_path, safe="")
    encoded_ref = urllib.parse.quote(target.commit_sha, safe="")
    return (
        f"{PROVIDER_ROOT}/api/v4/projects/{target.project_id}/repository/files/"
        f"{encoded_path}/raw?ref={encoded_ref}"
    )


def validate_final_url(target: ArtifactTarget, final_url: str) -> str:
    expected = raw_file_api_url(target)
    if type(final_url) is not str or final_url != expected:
        raise EfehrReceiptError("provider response identity does not match the frozen target")
    parsed = urllib.parse.urlsplit(final_url)
    if (
        parsed.scheme != "https"
        or parsed.hostname != PROVIDER_HOST
        or parsed.username is not None
        or parsed.password is not None
        or parsed.port not in (None, 443)
        or parsed.fragment
    ):
        raise EfehrReceiptError("provider response URL left the fixed HTTPS boundary")
    return final_url


def validate_public_addresses(addresses: Iterable[str]) -> tuple[str, ...]:
    """Reject non-public DNS results before a future trusted transport connects."""
    if isinstance(addresses, (str, bytes)):
        raise EfehrReceiptError("addresses must be an iterable of IP strings")
    validated: list[str] = []
    for value in addresses:
        if type(value) is not str:
            raise EfehrReceiptError("resolved address must be a string")
        try:
            address = ipaddress.ip_address(value)
        except ValueError as exc:
            raise EfehrReceiptError("resolved address is not a valid IP") from exc
        if not address.is_global:
            raise EfehrReceiptError("resolved address is not globally routable")
        validated.append(address.compressed)
    if not validated:
        raise EfehrReceiptError("provider DNS resolution returned no addresses")
    return tuple(sorted(set(validated)))


def _validate_retrieved_at(value: str) -> str:
    if type(value) is not str or not UTC_TIMESTAMP_RE.fullmatch(value):
        raise EfehrReceiptError("retrieved_at must be a canonical UTC timestamp ending in Z")
    try:
        datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError as exc:
        raise EfehrReceiptError("retrieved_at is not a valid UTC timestamp") from exc
    return value


def _header(headers: Mapping[str, Any] | None, name: str) -> str | None:
    if headers is None:
        return None
    value = None
    for key, candidate in headers.items():
        if type(key) is str and key.casefold() == name.casefold():
            value = candidate
            break
    if value is None:
        return None
    if type(value) is not str:
        raise EfehrReceiptError(f"{name} header must be a string")
    if len(value.encode("utf-8")) > MAX_HEADER_BYTES:
        raise EfehrReceiptError(f"{name} header exceeds byte-length bound")
    if any(ord(ch) < 0x20 or ord(ch) == 0x7F for ch in value):
        raise EfehrReceiptError(f"{name} header contains control characters")
    return value


def receipt_from_stream(
    target: ArtifactTarget,
    stream: BinaryIO,
    *,
    final_url: str,
    retrieved_at: str,
    headers: Mapping[str, Any] | None = None,
    max_bytes: int = MAX_FILE_BYTES,
) -> dict[str, Any]:
    """Hash one already-opened exact byte stream without persisting provider bytes."""
    if type(target) is not ArtifactTarget:
        raise EfehrReceiptError("target must be a validated ArtifactTarget")
    validate_final_url(target, final_url)
    retrieved_at = _validate_retrieved_at(retrieved_at)
    if type(max_bytes) is not int or isinstance(max_bytes, bool) or not (1 <= max_bytes <= MAX_FILE_BYTES):
        raise EfehrReceiptError("max_bytes is outside the bounded policy")
    if not hasattr(stream, "read"):
        raise EfehrReceiptError("stream must expose read()")

    declared_length = _header(headers, "Content-Length")
    declared: int | None = None
    if declared_length is not None:
        if not declared_length.isdigit():
            raise EfehrReceiptError("Content-Length is invalid")
        declared = int(declared_length)
        if not (1 <= declared <= max_bytes):
            raise EfehrReceiptError("Content-Length is outside the bounded policy")

    digest = hashlib.sha256()
    count = 0
    while True:
        chunk = stream.read(CHUNK_SIZE)
        if chunk == b"":
            break
        if type(chunk) is not bytes:
            raise EfehrReceiptError("provider stream yielded non-byte content")
        count += len(chunk)
        if count > max_bytes:
            raise EfehrReceiptError("provider payload exceeded bounded byte limit")
        digest.update(chunk)

    if count < 1:
        raise EfehrReceiptError("provider returned an empty object")
    if declared is not None and declared != count:
        raise EfehrReceiptError("Content-Length does not match streamed byte count")

    return {
        "schema_version": SCHEMA_VERSION,
        "source_issue": target.source_issue,
        "dataset_id": target.dataset_id,
        "provider_host": PROVIDER_HOST,
        "project_id": target.project_id,
        "project_path": target.project_path,
        "commit_sha": target.commit_sha,
        "repository_path": target.repository_path,
        "requested_url": raw_file_api_url(target),
        "final_url": final_url,
        "retrieved_at": retrieved_at,
        "byte_count": count,
        "sha256": digest.hexdigest(),
        "content_type": _header(headers, "Content-Type"),
        "etag": _header(headers, "ETag"),
        "external_bytes_persisted": False,
        "publication_authorized": False,
    }
