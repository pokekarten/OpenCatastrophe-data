# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Acquire one frozen CEMS Europe v3.1.1 RP10 TIFF and emit receipt-only evidence."""

from __future__ import annotations

import hashlib
import http.client
import ipaddress
import queue
import socket
import ssl
import threading
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from typing import Any, Callable

SCHEMA_VERSION = "oc-cems-europe-rp10-receipt-v1"
SOURCE_ISSUE = 793
DATASET_ID = "ec-jrc.cems.europe-mediterranean-river-flood-hazard-maps.2026"
RELEASE = "3.1.1"
RELEASE_DATE = "2026-03-05"
DOI = "10.2905/1D128B6C-A4EE-4858-9E34-6210707F3C81"
RETURN_PERIOD_YEARS = 10
FILENAME = "Europe_RP10_filled_depth.tif"
EXPECTED_HOST = "jeodpp.jrc.ec.europa.eu"
SOURCE_URL = (
    "https://jeodpp.jrc.ec.europa.eu/ftp/jrc-opendata/CEMS-EFAS/flood_hazard/"
    + FILENAME
)
ALLOWED_MEDIA_TYPES = frozenset({"image/tiff", "application/octet-stream"})
MAX_BYTES = 419_430_400
TOTAL_DEADLINE_SECONDS = 300.0
CHUNK_SIZE = 1_048_576
_TIFF_SIGNATURES = (b"II*\x00", b"MM\x00*", b"II+\x00", b"MM\x00+")


class CemsRp10ReceiptError(RuntimeError):
    """Raised when the fixed receipt cannot be produced fail-closed."""


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).strftime("%Y-%m-%dT%H:%M:%SZ")


def _remaining(deadline: float, monotonic: Callable[[], float]) -> float:
    remaining = deadline - monotonic()
    if remaining <= 0:
        raise CemsRp10ReceiptError("CEMS RP10 acquisition exceeded total deadline")
    return remaining


def _safe_source_url(url: str) -> bool:
    if url != SOURCE_URL:
        return False
    parsed = urllib.parse.urlsplit(url)
    return (
        parsed.scheme == "https"
        and parsed.hostname == EXPECTED_HOST
        and parsed.username is None
        and parsed.password is None
        and parsed.port in (None, 443)
        and parsed.query == ""
        and parsed.fragment == ""
    )


def _classify_public_sockaddrs(
    infos: list[tuple[Any, ...]],
) -> list[tuple[int, int, int, tuple[Any, ...]]]:
    admitted: list[tuple[int, int, int, tuple[Any, ...]]] = []
    seen: set[tuple[int, str]] = set()
    for family, socktype, proto, _canonname, sockaddr in infos:
        if family not in (socket.AF_INET, socket.AF_INET6) or socktype != socket.SOCK_STREAM:
            continue
        try:
            ip = ipaddress.ip_address(str(sockaddr[0]))
        except ValueError as exc:
            raise CemsRp10ReceiptError("trusted CEMS DNS returned an invalid IP address") from exc
        if not ip.is_global:
            raise CemsRp10ReceiptError("trusted CEMS DNS resolved to a non-global IP address")
        key = (family, ip.compressed)
        if key not in seen:
            seen.add(key)
            admitted.append((family, socktype, proto, sockaddr))
    if not admitted:
        raise CemsRp10ReceiptError("trusted CEMS DNS returned no globally routable address")
    return admitted


def _resolve_with_timeout(
    host: str,
    port: int,
    timeout: float,
    resolver: Callable[..., Any] = socket.getaddrinfo,
) -> list[tuple[int, int, int, tuple[Any, ...]]]:
    if host != EXPECTED_HOST or port != 443:
        raise CemsRp10ReceiptError("trusted CEMS DNS target left the frozen provider boundary")
    if timeout <= 0:
        raise CemsRp10ReceiptError("CEMS RP10 acquisition exceeded total deadline")
    result: queue.Queue[tuple[str, Any]] = queue.Queue(maxsize=1)

    def run() -> None:
        try:
            infos = resolver(host, port, type=socket.SOCK_STREAM)
        except Exception as exc:  # pragma: no cover - exercised through wrapper behavior
            result.put(("error", exc))
        else:
            result.put(("ok", infos))

    thread = threading.Thread(target=run, name="oc-cems-rp10-dns", daemon=True)
    thread.start()
    try:
        kind, payload = result.get(timeout=timeout)
    except queue.Empty as exc:
        raise CemsRp10ReceiptError("trusted CEMS DNS resolution exceeded total deadline") from exc
    if kind == "error":
        raise CemsRp10ReceiptError("trusted CEMS DNS resolution failed") from payload
    return _classify_public_sockaddrs(payload)


class PublicOnlyHTTPSConnection(http.client.HTTPSConnection):
    """HTTPS connection pinned directly to one prevalidated public DNS answer."""

    def connect(self) -> None:
        if self.host != EXPECTED_HOST or self.port != 443:
            raise CemsRp10ReceiptError("HTTPS connection left the frozen CEMS provider")
        if self._tunnel_host:
            raise CemsRp10ReceiptError("HTTP tunneling/proxies are forbidden for the frozen CEMS source")
        budget = float(self.timeout)
        started = time.monotonic()
        addresses = _resolve_with_timeout(self.host, self.port, budget)
        last_error: OSError | None = None
        raw_sock: socket.socket | None = None
        for family, socktype, proto, sockaddr in addresses:
            remaining = budget - (time.monotonic() - started)
            if remaining <= 0:
                raise CemsRp10ReceiptError("CEMS RP10 acquisition exceeded total deadline")
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
            raise CemsRp10ReceiptError("trusted CEMS connection failed") from last_error
        try:
            remaining = budget - (time.monotonic() - started)
            if remaining <= 0:
                raise CemsRp10ReceiptError("CEMS RP10 acquisition exceeded total deadline")
            raw_sock.settimeout(remaining)
            self.sock = self._context.wrap_socket(raw_sock, server_hostname=self.host)
            peer_ip = ipaddress.ip_address(str(self.sock.getpeername()[0]))
            if not peer_ip.is_global:
                raise CemsRp10ReceiptError("trusted CEMS peer is not globally routable")
        except Exception:
            raw_sock.close()
            raise


class FixedHTTPSHandler(urllib.request.HTTPSHandler):
    def https_open(self, req):  # noqa: ANN001
        return self.do_open(PublicOnlyHTTPSConnection, req, context=self._context)


class NoRedirectHandler(urllib.request.HTTPRedirectHandler):
    """Reject every redirect so final identity cannot drift from the frozen URL."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):  # noqa: ANN001
        raise CemsRp10ReceiptError("provider redirect is forbidden for the frozen CEMS source")


def _open_frozen_source(request: urllib.request.Request, timeout: float):
    opener = urllib.request.build_opener(
        urllib.request.ProxyHandler({}),
        NoRedirectHandler(),
        FixedHTTPSHandler(context=ssl.create_default_context()),
    )
    return opener.open(request, timeout=timeout)


def _parse_content_length(value: str | None) -> int | None:
    if value is None:
        return None
    if not value.isascii() or not value.isdigit():
        raise CemsRp10ReceiptError("CEMS Content-Length is not a canonical non-negative integer")
    parsed = int(value)
    if parsed <= 0 or parsed > MAX_BYTES:
        raise CemsRp10ReceiptError("CEMS Content-Length is outside the bounded asset size")
    return parsed


def _set_response_timeout(response: Any, timeout: float) -> None:
    if timeout <= 0:
        raise CemsRp10ReceiptError("CEMS RP10 acquisition exceeded total deadline")
    try:
        response_socket = response.fp.raw._sock
    except AttributeError as exc:
        raise CemsRp10ReceiptError(
            "CEMS response socket cannot enforce the total deadline"
        ) from exc
    try:
        response_socket.settimeout(timeout)
    except (OSError, ValueError) as exc:
        raise CemsRp10ReceiptError("CEMS response socket timeout update failed") from exc


def acquire_cems_rp10_receipt(
    *,
    opener: Callable[[urllib.request.Request, float], Any] = _open_frozen_source,
    clock: Callable[[], str] = utc_now,
    monotonic: Callable[[], float] = time.monotonic,
) -> dict[str, Any]:
    """Stream the exact frozen RP10 asset and retain no provider payload bytes."""
    if not _safe_source_url(SOURCE_URL):
        raise CemsRp10ReceiptError("frozen CEMS source identity is invalid")

    started = monotonic()
    deadline = started + TOTAL_DEADLINE_SECONDS
    request = urllib.request.Request(
        SOURCE_URL,
        method="GET",
        headers={"Accept": "image/tiff, application/octet-stream", "Accept-Encoding": "identity"},
    )
    try:
        response_cm = opener(request, _remaining(deadline, monotonic))
        with response_cm as response:
            if type(response.status) is not int or response.status != 200:
                raise CemsRp10ReceiptError("CEMS response status is not exact HTTP 200")
            final_url = response.geturl()
            if type(final_url) is not str or final_url != SOURCE_URL:
                raise CemsRp10ReceiptError("CEMS final URL drifted from frozen source identity")

            content_encoding = response.headers.get("Content-Encoding")
            if content_encoding not in (None, "", "identity"):
                raise CemsRp10ReceiptError("CEMS response used unexpected content encoding")
            media_type_raw = response.headers.get("Content-Type")
            if type(media_type_raw) is not str:
                raise CemsRp10ReceiptError("CEMS response media type is missing")
            media_type = media_type_raw.split(";", 1)[0].strip().lower()
            if media_type not in ALLOWED_MEDIA_TYPES:
                raise CemsRp10ReceiptError("CEMS response media type is outside the fixed contract")
            declared_length = _parse_content_length(response.headers.get("Content-Length"))

            digest = hashlib.sha256()
            byte_count = 0
            prefix = bytearray()
            while True:
                remaining = _remaining(deadline, monotonic)
                _set_response_timeout(response, remaining)
                chunk = response.read(CHUNK_SIZE)
                _remaining(deadline, monotonic)
                if not chunk:
                    break
                if type(chunk) is not bytes:
                    raise CemsRp10ReceiptError("CEMS response stream returned non-byte content")
                byte_count += len(chunk)
                if byte_count > MAX_BYTES:
                    raise CemsRp10ReceiptError("CEMS RP10 asset exceeded bounded byte size")
                if len(prefix) < 4:
                    prefix.extend(chunk[: 4 - len(prefix)])
                digest.update(chunk)

            if byte_count == 0:
                raise CemsRp10ReceiptError("CEMS RP10 asset was empty")
            if declared_length is not None and byte_count != declared_length:
                raise CemsRp10ReceiptError("CEMS response byte count disagrees with Content-Length")
            if bytes(prefix) not in _TIFF_SIGNATURES:
                raise CemsRp10ReceiptError("CEMS RP10 payload does not have a TIFF/BigTIFF signature")
    except CemsRp10ReceiptError:
        raise
    except Exception as exc:
        raise CemsRp10ReceiptError("CEMS RP10 acquisition failed") from exc

    return {
        "schema_version": SCHEMA_VERSION,
        "dataset_id": DATASET_ID,
        "source_issue": SOURCE_ISSUE,
        "release": RELEASE,
        "release_date": RELEASE_DATE,
        "doi": DOI,
        "return_period_years": RETURN_PERIOD_YEARS,
        "filename": FILENAME,
        "requested_url": SOURCE_URL,
        "final_url": SOURCE_URL,
        "retrieved_at": clock(),
        "http_status": 200,
        "media_type": media_type,
        "content_length_header": declared_length,
        "byte_count": byte_count,
        "sha256": digest.hexdigest(),
        "external_bytes_persisted": False,
        "geotiff_semantics_verified": False,
        "benchmark_use_authorized": False,
        "publication_authorized": False,
        "model_use_authorized": False,
    }
