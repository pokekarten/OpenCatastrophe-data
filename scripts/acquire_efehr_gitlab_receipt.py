# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Trusted transport primitive for one bounded EFEHR GitLab acquisition canary.

The first operation intentionally fetches only the ESRM20 exposure-format README.
No caller-controlled host, project, release tag, repository path or operation
selection enters this module. Agent Action wiring is deliberately separate.
"""

from __future__ import annotations

import http.client
import ipaddress
import json
import queue
import socket
import ssl
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from typing import Any

try:
    from scripts.efehr_gitlab_receipt import (
        EfehrReceiptError,
        PROVIDER_HOST,
        PROVIDER_ROOT,
        raw_file_api_url,
        receipt_from_stream,
        validate_target,
    )
except ModuleNotFoundError:  # pragma: no cover - direct script import path
    from efehr_gitlab_receipt import (
        EfehrReceiptError,
        PROVIDER_HOST,
        PROVIDER_ROOT,
        raw_file_api_url,
        receipt_from_stream,
        validate_target,
    )

SCHEMA_VERSION = "oc-efehr-trusted-acquisition-v1"
OPERATION_ID = "esrm20-exposure-format-readme-v1"
SOURCE_ISSUE = 282
DATASET_ID = "efehr.esrm20.european-exposure-model.v1.0"
PROJECT_ID = 186
RELEASE_TAG = "v1.0"
REPOSITORY_PATH = "_exposure_models/ReadMe_Exposure_Model_Format.txt"
TAG_API_URL = (
    f"{PROVIDER_ROOT}/api/v4/projects/{PROJECT_ID}/repository/tags/"
    f"{urllib.parse.quote(RELEASE_TAG, safe='')}"
)
TOTAL_DEADLINE_SECONDS = 30.0
MAX_TAG_RESPONSE_BYTES = 65_536
MAX_CANARY_BYTES = 1_048_576
CHUNK_SIZE = 65_536


class EfehrAcquisitionError(RuntimeError):
    """Raised when the bounded EFEHR transport cannot produce trusted evidence."""


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).strftime("%Y-%m-%dT%H:%M:%SZ")


def _remaining(deadline: float, monotonic: Any = time.monotonic) -> float:
    remaining = deadline - monotonic()
    if remaining <= 0:
        raise EfehrAcquisitionError("EFEHR acquisition exceeded total deadline")
    return remaining


def _classify_public_sockaddrs(
    infos: list[tuple[Any, ...]],
) -> list[tuple[int, int, int, tuple[Any, ...]]]:
    admitted: list[tuple[int, int, int, tuple[Any, ...]]] = []
    seen: set[tuple[int, str]] = set()
    for family, socktype, proto, _canonname, sockaddr in infos:
        if family not in (socket.AF_INET, socket.AF_INET6) or socktype != socket.SOCK_STREAM:
            continue
        try:
            address = ipaddress.ip_address(str(sockaddr[0]))
        except ValueError as exc:
            raise EfehrAcquisitionError("EFEHR DNS returned an invalid IP address") from exc
        if not address.is_global:
            raise EfehrAcquisitionError("EFEHR DNS resolved to a non-global IP address")
        key = (family, address.compressed)
        if key not in seen:
            seen.add(key)
            admitted.append((family, socktype, proto, sockaddr))
    if not admitted:
        raise EfehrAcquisitionError("EFEHR DNS returned no globally routable address")
    return admitted


def _resolve_with_timeout(
    host: str,
    port: int,
    timeout: float,
    resolver: Any = socket.getaddrinfo,
) -> list[tuple[int, int, int, tuple[Any, ...]]]:
    if host != PROVIDER_HOST or port != 443:
        raise EfehrAcquisitionError("EFEHR DNS target left the fixed provider boundary")
    if timeout <= 0:
        raise EfehrAcquisitionError("EFEHR acquisition exceeded total deadline")
    result: queue.Queue[tuple[str, Any]] = queue.Queue(maxsize=1)

    def run() -> None:
        try:
            infos = resolver(host, port, type=socket.SOCK_STREAM)
        except Exception as exc:
            result.put(("error", exc))
        else:
            result.put(("ok", infos))

    thread = threading.Thread(target=run, name="oc-efehr-dns", daemon=True)
    thread.start()
    try:
        kind, payload = result.get(timeout=timeout)
    except queue.Empty as exc:
        raise EfehrAcquisitionError("EFEHR DNS resolution exceeded total deadline") from exc
    if kind == "error":
        raise EfehrAcquisitionError("EFEHR DNS resolution failed") from payload
    return _classify_public_sockaddrs(payload)


class PublicOnlyHTTPSConnection(http.client.HTTPSConnection):
    """HTTPS connection pinned to one prevalidated public DNS answer."""

    def connect(self) -> None:
        if self.host != PROVIDER_HOST or self.port != 443:
            raise EfehrAcquisitionError("HTTPS connection left the fixed EFEHR provider")
        if self._tunnel_host:
            raise EfehrAcquisitionError("HTTP tunneling/proxies are forbidden for EFEHR")
        budget = float(self.timeout)
        started = time.monotonic()
        addresses = _resolve_with_timeout(self.host, self.port, budget)
        last_error: OSError | None = None
        raw_sock: socket.socket | None = None
        for family, socktype, proto, sockaddr in addresses:
            remaining = budget - (time.monotonic() - started)
            if remaining <= 0:
                raise EfehrAcquisitionError("EFEHR acquisition exceeded total deadline")
            candidate = socket.socket(family, socktype, proto)
            try:
                candidate.settimeout(remaining)
                candidate.connect(sockaddr)
                raw_sock = candidate
                break
            except OSError as exc:
                last_error = exc
                candidate.close()
        if raw_sock is None:
            raise EfehrAcquisitionError("EFEHR provider connection failed") from last_error
        try:
            remaining = budget - (time.monotonic() - started)
            if remaining <= 0:
                raise EfehrAcquisitionError("EFEHR acquisition exceeded total deadline")
            raw_sock.settimeout(remaining)
            self.sock = self._context.wrap_socket(raw_sock, server_hostname=self.host)
            peer = ipaddress.ip_address(str(self.sock.getpeername()[0]))
            if not peer.is_global:
                raise EfehrAcquisitionError("EFEHR provider peer is not globally routable")
        except Exception:
            raw_sock.close()
            raise


class FixedHTTPSHandler(urllib.request.HTTPSHandler):
    def https_open(self, req):  # noqa: ANN001
        return self.do_open(PublicOnlyHTTPSConnection, req, context=self._context)


class RejectRedirectHandler(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):  # noqa: ANN001
        raise EfehrAcquisitionError("EFEHR redirects are forbidden")


def _validate_provider_url(url: str) -> str:
    if type(url) is not str:
        raise EfehrAcquisitionError("EFEHR URL must be text")
    try:
        parsed = urllib.parse.urlsplit(url)
        port = parsed.port
    except ValueError as exc:
        raise EfehrAcquisitionError("EFEHR URL is malformed") from exc
    if (
        parsed.scheme != "https"
        or parsed.hostname != PROVIDER_HOST
        or parsed.username is not None
        or parsed.password is not None
        or port not in (None, 443)
        or parsed.fragment
    ):
        raise EfehrAcquisitionError("EFEHR URL left the fixed HTTPS provider boundary")
    return url


def _open_fixed(request: urllib.request.Request, timeout: float):
    _validate_provider_url(request.full_url)
    opener = urllib.request.build_opener(
        urllib.request.ProxyHandler({}),
        RejectRedirectHandler(),
        FixedHTTPSHandler(context=ssl.create_default_context()),
    )
    return opener.open(request, timeout=timeout)


def _header_value(response: Any, name: str) -> str | None:
    headers = getattr(response, "headers", None)
    if headers is None:
        return None
    value = headers.get(name)
    if value is None:
        return None
    if type(value) is not str:
        value = str(value)
    if len(value.encode("utf-8")) > 1024:
        raise EfehrAcquisitionError(f"{name} header exceeds bounded policy")
    if any(ord(character) < 32 or ord(character) == 127 for character in value):
        raise EfehrAcquisitionError(f"{name} header contains control characters")
    return value


def _declared_length(response: Any, maximum: int) -> int | None:
    value = _header_value(response, "Content-Length")
    if value is None:
        return None
    if not value.isdigit():
        raise EfehrAcquisitionError("Content-Length is invalid")
    parsed = int(value)
    if not (1 <= parsed <= maximum):
        raise EfehrAcquisitionError("Content-Length is outside bounded policy")
    return parsed


def _set_response_timeout(response: Any, timeout: float) -> None:
    try:
        response.fp.raw._sock.settimeout(timeout)
    except AttributeError:
        return


def _read_bounded(
    response: Any,
    *,
    deadline: float,
    maximum: int,
    monotonic: Any,
) -> bytes:
    declared = _declared_length(response, maximum)
    chunks: list[bytes] = []
    count = 0
    while True:
        remaining = _remaining(deadline, monotonic)
        _set_response_timeout(response, remaining)
        chunk = response.read(CHUNK_SIZE)
        _remaining(deadline, monotonic)
        if chunk == b"":
            break
        if type(chunk) is not bytes:
            raise EfehrAcquisitionError("EFEHR provider returned non-byte content")
        count += len(chunk)
        if count > maximum:
            raise EfehrAcquisitionError("EFEHR response exceeded bounded byte limit")
        chunks.append(chunk)
    if count < 1:
        raise EfehrAcquisitionError("EFEHR provider returned an empty object")
    if declared is not None and declared != count:
        raise EfehrAcquisitionError("Content-Length does not match streamed byte count")
    return b"".join(chunks)


def _strict_json_object(raw: bytes) -> dict[str, Any]:
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise EfehrAcquisitionError("EFEHR tag response is not UTF-8") from exc

    def reject_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in pairs:
            if key in result:
                raise EfehrAcquisitionError(f"duplicate tag-response JSON key: {key}")
            result[key] = value
        return result

    try:
        payload = json.loads(
            text,
            object_pairs_hook=reject_duplicates,
            parse_constant=lambda token: (_ for _ in ()).throw(
                EfehrAcquisitionError(f"non-finite tag-response JSON value: {token}")
            ),
        )
    except json.JSONDecodeError as exc:
        raise EfehrAcquisitionError("EFEHR tag response is not valid JSON") from exc
    if type(payload) is not dict:
        raise EfehrAcquisitionError("EFEHR tag response must be a JSON object")
    return payload


def _validate_exact_response(response: Any, expected_url: str) -> None:
    status = getattr(response, "status", 200)
    if type(status) is not int or status != 200:
        raise EfehrAcquisitionError("EFEHR provider response status is not 200")
    final_url = response.geturl()
    if type(final_url) is not str or final_url != expected_url:
        raise EfehrAcquisitionError("EFEHR provider response identity drifted")
    _validate_provider_url(final_url)


def resolve_release_commit(
    *,
    opener: Any | None = None,
    deadline: float,
    monotonic: Any = time.monotonic,
) -> str:
    """Resolve the one trusted release tag to a full immutable commit SHA."""

    open_response = opener or _open_fixed
    request = urllib.request.Request(
        TAG_API_URL,
        headers={
            "Accept": "application/json",
            "User-Agent": "OpenCatastrophe-EFEHR-acquisition-v1",
        },
        method="GET",
    )
    try:
        with open_response(request, timeout=_remaining(deadline, monotonic)) as response:
            _validate_exact_response(response, TAG_API_URL)
            raw = _read_bounded(
                response,
                deadline=deadline,
                maximum=MAX_TAG_RESPONSE_BYTES,
                monotonic=monotonic,
            )
    except EfehrAcquisitionError:
        raise
    except (OSError, urllib.error.URLError, urllib.error.HTTPError, TimeoutError) as exc:
        raise EfehrAcquisitionError(
            f"EFEHR tag resolution failed: {type(exc).__name__}"
        ) from exc

    payload = _strict_json_object(raw)
    if payload.get("name") != RELEASE_TAG:
        raise EfehrAcquisitionError("EFEHR tag response does not match trusted release")
    commit = payload.get("commit")
    commit_sha = commit.get("id") if type(commit) is dict else None
    if type(commit_sha) is not str or len(commit_sha) != 40:
        raise EfehrAcquisitionError("EFEHR tag response lacks a full commit SHA")
    try:
        target = validate_target(
            source_issue=SOURCE_ISSUE,
            dataset_id=DATASET_ID,
            project_id=PROJECT_ID,
            commit_sha=commit_sha,
            repository_path=REPOSITORY_PATH,
        )
    except EfehrReceiptError as exc:
        raise EfehrAcquisitionError(f"resolved EFEHR target is invalid: {exc}") from exc
    return target.commit_sha


class _DeadlineStream:
    def __init__(self, response: Any, *, deadline: float, monotonic: Any):
        self._response = response
        self._deadline = deadline
        self._monotonic = monotonic

    def read(self, size: int = -1) -> bytes:
        remaining = _remaining(self._deadline, self._monotonic)
        _set_response_timeout(self._response, remaining)
        chunk = self._response.read(size)
        _remaining(self._deadline, self._monotonic)
        return chunk


def acquire_canary(
    *,
    opener: Any | None = None,
    now: Any = utc_now,
    monotonic: Any = time.monotonic,
) -> dict[str, Any]:
    """Acquire only the trusted exposure-format README and return bounded evidence."""

    deadline = monotonic() + TOTAL_DEADLINE_SECONDS
    open_response = opener or _open_fixed
    commit_sha = resolve_release_commit(
        opener=open_response,
        deadline=deadline,
        monotonic=monotonic,
    )
    try:
        target = validate_target(
            source_issue=SOURCE_ISSUE,
            dataset_id=DATASET_ID,
            project_id=PROJECT_ID,
            commit_sha=commit_sha,
            repository_path=REPOSITORY_PATH,
        )
    except EfehrReceiptError as exc:
        raise EfehrAcquisitionError(f"trusted EFEHR target is invalid: {exc}") from exc
    file_url = raw_file_api_url(target)
    request = urllib.request.Request(
        file_url,
        headers={
            "Accept": "text/plain",
            "User-Agent": "OpenCatastrophe-EFEHR-acquisition-v1",
        },
        method="GET",
    )

    try:
        with open_response(request, timeout=_remaining(deadline, monotonic)) as response:
            _validate_exact_response(response, file_url)
            _declared_length(response, MAX_CANARY_BYTES)
            retrieved_at = now()
            try:
                core_receipt = receipt_from_stream(
                    target,
                    _DeadlineStream(
                        response,
                        deadline=deadline,
                        monotonic=monotonic,
                    ),
                    final_url=file_url,
                    retrieved_at=retrieved_at,
                    headers=getattr(response, "headers", None),
                    max_bytes=MAX_CANARY_BYTES,
                )
            except EfehrReceiptError as exc:
                raise EfehrAcquisitionError(f"EFEHR artifact receipt failed: {exc}") from exc
    except EfehrAcquisitionError:
        raise
    except (OSError, urllib.error.URLError, urllib.error.HTTPError, TimeoutError) as exc:
        raise EfehrAcquisitionError(
            f"EFEHR artifact retrieval failed: {type(exc).__name__}"
        ) from exc

    result = dict(core_receipt)
    result["schema_version"] = SCHEMA_VERSION
    result["operation_id"] = OPERATION_ID
    result["release_tag"] = RELEASE_TAG
    result["tag_api_url"] = TAG_API_URL
    return {
        "schema_version": result["schema_version"],
        "operation_id": result["operation_id"],
        "release_tag": result["release_tag"],
        "tag_api_url": result["tag_api_url"],
        "source_issue": result["source_issue"],
        "dataset_id": result["dataset_id"],
        "provider_host": result["provider_host"],
        "project_id": result["project_id"],
        "project_path": result["project_path"],
        "commit_sha": result["commit_sha"],
        "repository_path": result["repository_path"],
        "requested_url": result["requested_url"],
        "final_url": result["final_url"],
        "retrieved_at": result["retrieved_at"],
        "byte_count": result["byte_count"],
        "sha256": result["sha256"],
        "content_type": result["content_type"],
        "etag": result["etag"],
        "external_bytes_persisted": result["external_bytes_persisted"],
        "publication_authorized": result["publication_authorized"],
    }
