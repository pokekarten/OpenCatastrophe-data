# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Acquire one frozen DWD extreme-wind ZIP ephemerally and emit metadata-only evidence."""

from __future__ import annotations

import argparse
import hashlib
import http.client
import ipaddress
import json
import math
import os
import queue
import socket
import ssl
import stat
import tempfile
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
import zipfile
from datetime import datetime, timezone
from pathlib import PurePosixPath
from typing import Any

SCHEMA_VERSION = "oc-acquisition-receipt-v1"
DATASET_ID = "dwd.cdc.obsgermany-climate-10min-extreme-wind.v24.03"
FILENAME = "10minutenwerte_extrema_wind_00003_20100101_20110331_hist.zip"
SOURCE_URL = (
    "https://opendata.dwd.de/climate_environment/CDC/observations_germany/climate/"
    "10_minutes/extreme_wind/historical/" + FILENAME
)
EXPECTED_HOST = "opendata.dwd.de"
EXPECTED_STATION_ID = "00003"
EXPECTED_BEGIN_DATE = "20100101"
EXPECTED_END_DATE = "20110331"
EXPECTED_COLUMNS = ("MESS_DATUM", "QN", "FX_10", "FNX_10", "FMX_10", "DX_10")
MAX_BYTES = 52_428_800
MAX_ARCHIVE_MEMBERS = 32
MAX_UNCOMPRESSED_BYTES = 104_857_600
TOTAL_DEADLINE_SECONDS = 60.0
CHUNK_SIZE = 65_536
MAX_ROW_BYTES = 4096
ALLOWED_COMPRESSION_METHODS = frozenset({zipfile.ZIP_STORED, zipfile.ZIP_DEFLATED})


class AcquisitionError(RuntimeError):
    """Raised when acquisition cannot produce bounded trustworthy evidence."""


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).strftime("%Y-%m-%dT%H:%M:%SZ")


def _remaining(deadline: float, monotonic: Any = time.monotonic) -> float:
    remaining = deadline - monotonic()
    if remaining <= 0:
        raise AcquisitionError("acquisition exceeded total deadline")
    return remaining


def _safe_source_url(url: str) -> bool:
    """Accept only the exact frozen HTTPS source identity."""
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
    """Admit only globally routable IPv4/IPv6 stream addresses."""
    admitted: list[tuple[int, int, int, tuple[Any, ...]]] = []
    seen: set[tuple[int, str]] = set()
    for family, socktype, proto, _canonname, sockaddr in infos:
        if family not in (socket.AF_INET, socket.AF_INET6) or socktype != socket.SOCK_STREAM:
            continue
        try:
            ip = ipaddress.ip_address(str(sockaddr[0]))
        except ValueError as exc:
            raise AcquisitionError("trusted provider DNS returned an invalid IP address") from exc
        if not ip.is_global:
            raise AcquisitionError("trusted provider DNS resolved to a non-global IP address")
        key = (family, ip.compressed)
        if key not in seen:
            seen.add(key)
            admitted.append((family, socktype, proto, sockaddr))
    if not admitted:
        raise AcquisitionError("trusted provider DNS returned no globally routable address")
    return admitted


def _resolve_with_timeout(
    host: str,
    port: int,
    timeout: float,
    resolver: Any = socket.getaddrinfo,
) -> list[tuple[int, int, int, tuple[Any, ...]]]:
    """Resolve in a daemon helper so DNS cannot hold the worker past its deadline."""
    if timeout <= 0:
        raise AcquisitionError("acquisition exceeded total deadline")
    result: queue.Queue[tuple[str, Any]] = queue.Queue(maxsize=1)

    def run() -> None:
        try:
            infos = resolver(host, port, type=socket.SOCK_STREAM)
        except Exception as exc:
            result.put(("error", exc))
        else:
            result.put(("ok", infos))

    thread = threading.Thread(target=run, name="oc-dwd-dns", daemon=True)
    thread.start()
    try:
        kind, payload = result.get(timeout=timeout)
    except queue.Empty as exc:
        raise AcquisitionError("trusted provider DNS resolution exceeded total deadline") from exc
    if kind == "error":
        raise AcquisitionError("trusted provider DNS resolution failed") from payload
    return _classify_public_sockaddrs(payload)


class PublicOnlyHTTPSConnection(http.client.HTTPSConnection):
    """HTTPS connection pinned directly to one prevalidated public DNS answer."""

    def connect(self) -> None:
        if self._tunnel_host:
            raise AcquisitionError("HTTP tunneling/proxies are forbidden for the frozen source")
        budget = float(self.timeout)
        started = time.monotonic()
        addresses = _resolve_with_timeout(self.host, self.port, budget)
        last_error: OSError | None = None
        raw_sock: socket.socket | None = None
        for family, socktype, proto, sockaddr in addresses:
            remaining = budget - (time.monotonic() - started)
            if remaining <= 0:
                raise AcquisitionError("acquisition exceeded total deadline")
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
            raise AcquisitionError("trusted provider connection failed") from last_error
        try:
            remaining = budget - (time.monotonic() - started)
            if remaining <= 0:
                raise AcquisitionError("acquisition exceeded total deadline")
            raw_sock.settimeout(remaining)
            self.sock = self._context.wrap_socket(raw_sock, server_hostname=self.host)
            peer_ip = ipaddress.ip_address(str(self.sock.getpeername()[0]))
            if not peer_ip.is_global:
                raise AcquisitionError("trusted provider peer is not globally routable")
        except Exception:
            raw_sock.close()
            raise


class FrozenHTTPSHandler(urllib.request.HTTPSHandler):
    def https_open(self, req):  # noqa: ANN001
        return self.do_open(PublicOnlyHTTPSConnection, req, context=self._context)


class FrozenSourceRedirectHandler(urllib.request.HTTPRedirectHandler):
    """Reject redirects before urllib follows them to any alternate resource."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):  # noqa: ANN001
        resolved = urllib.parse.urljoin(req.full_url, newurl)
        if resolved != SOURCE_URL:
            raise AcquisitionError("provider redirect left the frozen source identity")
        raise AcquisitionError("provider redirect is forbidden for the frozen source identity")


def _open_frozen_source(request: urllib.request.Request, timeout: float):
    opener = urllib.request.build_opener(
        urllib.request.ProxyHandler({}),
        FrozenSourceRedirectHandler(),
        FrozenHTTPSHandler(context=ssl.create_default_context()),
    )
    return opener.open(request, timeout=timeout)


def _validate_member_name(name: str) -> None:
    if not name or len(name) > 512 or "\\" in name or "\x00" in name:
        raise AcquisitionError("archive contains an unsafe member name")
    path = PurePosixPath(name)
    if path.is_absolute() or any(part in {"", ".", ".."} for part in path.parts):
        raise AcquisitionError("archive contains an unsafe member path")


def _normalized_columns(header_line: str) -> list[str]:
    return [part.strip().strip('"') for part in header_line.rstrip("\r\n").split(";")]


def _member_matches_product_header(
    archive: zipfile.ZipFile,
    member: zipfile.ZipInfo,
    *,
    deadline: float,
    monotonic: Any,
) -> bool:
    """Identify a product member from its bounded DWD header, never its provider filename."""
    if member.is_dir() or PurePosixPath(member.filename).suffix.casefold() != ".txt":
        return False
    try:
        with archive.open(member, "r") as raw:
            _remaining(deadline, monotonic)
            header_bytes = raw.readline(MAX_ROW_BYTES + 1)
            _remaining(deadline, monotonic)
    except RuntimeError as exc:
        raise AcquisitionError("archive text member could not be inspected") from exc
    if not header_bytes or len(header_bytes) > MAX_ROW_BYTES:
        return False
    try:
        header = header_bytes.decode("utf-8-sig")
    except UnicodeDecodeError:
        return False
    columns = _normalized_columns(header)
    return "STATIONS_ID" in columns and all(column in columns for column in EXPECTED_COLUMNS)


def _validate_member_crc(
    archive: zipfile.ZipFile,
    member: zipfile.ZipInfo,
    *,
    deadline: float,
    monotonic: Any,
) -> None:
    """CRC/decompress one member in bounded chunks inside the total deadline."""
    if member.compress_type not in ALLOWED_COMPRESSION_METHODS:
        raise AcquisitionError("archive uses an unsupported compression method")
    if member.is_dir():
        if member.file_size != 0:
            raise AcquisitionError("archive directory member has non-zero payload size")
        return
    observed = 0
    try:
        with archive.open(member, "r") as raw:
            while True:
                _remaining(deadline, monotonic)
                chunk = raw.read(CHUNK_SIZE)
                _remaining(deadline, monotonic)
                if not chunk:
                    break
                observed += len(chunk)
                if observed > member.file_size:
                    raise AcquisitionError("archive member expanded beyond declared size")
    except AcquisitionError:
        raise
    except RuntimeError as exc:
        raise AcquisitionError("archive member CRC/decompression validation failed") from exc
    if observed != member.file_size:
        raise AcquisitionError("archive member size does not match decompressed bytes")


def _validate_product_shape(
    archive: zipfile.ZipFile,
    member: zipfile.ZipInfo,
    *,
    deadline: float,
    monotonic: Any,
) -> dict[str, Any]:
    """Validate station/time/header structure without retaining measurement values."""
    try:
        with archive.open(member, "r") as raw:
            _remaining(deadline, monotonic)
            header_bytes = raw.readline(MAX_ROW_BYTES + 1)
            _remaining(deadline, monotonic)
            if not header_bytes:
                raise AcquisitionError("product header is missing")
            if len(header_bytes) > MAX_ROW_BYTES:
                raise AcquisitionError("product header exceeds bounded size")
            try:
                header = header_bytes.decode("utf-8-sig")
            except UnicodeDecodeError as exc:
                raise AcquisitionError("product header is not UTF-8 text") from exc
            columns = _normalized_columns(header)
            if any(column not in columns for column in EXPECTED_COLUMNS):
                raise AcquisitionError(
                    "product header does not match DWD extreme-wind v24.03 columns"
                )
            if "STATIONS_ID" not in columns:
                raise AcquisitionError("product header does not expose station identity")
            station_index = columns.index("STATIONS_ID")
            time_index = columns.index("MESS_DATUM")
            numeric_indexes = [
                columns.index(column)
                for column in EXPECTED_COLUMNS
                if column != "MESS_DATUM"
            ]
            min_fields = max([station_index, time_index, *numeric_indexes]) + 1
            first_timestamp: str | None = None
            last_timestamp: str | None = None
            row_count = 0
            while True:
                _remaining(deadline, monotonic)
                raw_line = raw.readline(MAX_ROW_BYTES + 1)
                _remaining(deadline, monotonic)
                if not raw_line:
                    break
                if len(raw_line) > MAX_ROW_BYTES:
                    raise AcquisitionError("product row exceeds bounded structural size")
                if not raw_line.strip():
                    continue
                try:
                    line = raw_line.decode("utf-8")
                except UnicodeDecodeError as exc:
                    raise AcquisitionError("product rows are not UTF-8 text") from exc
                fields = line.rstrip("\r\n").split(";")
                if len(fields) < min_fields or len(fields) < len(columns):
                    raise AcquisitionError("product row does not match declared header")
                station = fields[station_index].strip().strip('"')
                timestamp = fields[time_index].strip().strip('"')
                for index in numeric_indexes:
                    try:
                        value = float(fields[index].strip().strip('"'))
                    except ValueError as exc:
                        raise AcquisitionError(
                            "product row contains a non-numeric declared measurement"
                        ) from exc
                    if not math.isfinite(value):
                        raise AcquisitionError(
                            "product row contains a non-finite declared measurement"
                        )
                if station.lstrip("0") != EXPECTED_STATION_ID.lstrip("0"):
                    raise AcquisitionError("product row station does not match frozen station")
                if len(timestamp) != 12 or not timestamp.isdigit():
                    raise AcquisitionError("product timestamp is not YYYYMMDDHHMM")
                try:
                    datetime.strptime(timestamp, "%Y%m%d%H%M")
                except ValueError as exc:
                    raise AcquisitionError(
                        "product timestamp is not a valid calendar time"
                    ) from exc
                date = timestamp[:8]
                if date < EXPECTED_BEGIN_DATE or date > EXPECTED_END_DATE:
                    raise AcquisitionError(
                        "product timestamp falls outside frozen historical scope"
                    )
                if last_timestamp is not None and timestamp < last_timestamp:
                    raise AcquisitionError("product timestamps are not monotonic")
                if first_timestamp is None:
                    first_timestamp = timestamp
                last_timestamp = timestamp
                row_count += 1
                if row_count > 1_000_000:
                    raise AcquisitionError(
                        "product row count exceeds bounded structural policy"
                    )
            if row_count < 1 or first_timestamp is None or last_timestamp is None:
                raise AcquisitionError("product contains no data rows")
            if not first_timestamp.startswith(EXPECTED_BEGIN_DATE):
                raise AcquisitionError("product does not begin in frozen begin date")
            if not last_timestamp.startswith(EXPECTED_END_DATE):
                raise AcquisitionError("product does not end in frozen end date")
            return {
                "product_station_id": EXPECTED_STATION_ID,
                "product_begin_date": EXPECTED_BEGIN_DATE,
                "product_end_date": EXPECTED_END_DATE,
                "product_row_count": row_count,
                "product_structure_validated": True,
            }
    except AcquisitionError:
        raise
    except RuntimeError as exc:
        raise AcquisitionError("product member could not be read") from exc


def _validate_zip(path: str, *, deadline: float, monotonic: Any) -> dict[str, Any]:
    try:
        with zipfile.ZipFile(path) as archive:
            members = archive.infolist()
            if not (1 <= len(members) <= MAX_ARCHIVE_MEMBERS):
                raise AcquisitionError(
                    "archive member count is outside the bounded policy"
                )
            total_uncompressed = 0
            for member in members:
                _remaining(deadline, monotonic)
                _validate_member_name(member.filename)
                mode = (member.external_attr >> 16) & 0o170000
                if mode not in (0, stat.S_IFREG, stat.S_IFDIR):
                    raise AcquisitionError(
                        "archive contains a forbidden Unix special-file type"
                    )
                if member.flag_bits & 0x1:
                    raise AcquisitionError("encrypted archive members are forbidden")
                if member.file_size < 0 or member.compress_size < 0:
                    raise AcquisitionError("archive member sizes are invalid")
                if member.compress_type not in ALLOWED_COMPRESSION_METHODS:
                    raise AcquisitionError("archive uses an unsupported compression method")
                total_uncompressed += member.file_size
                if total_uncompressed > MAX_UNCOMPRESSED_BYTES:
                    raise AcquisitionError("archive exceeds uncompressed-size bound")
            if total_uncompressed < 1:
                raise AcquisitionError("archive uncompressed payload is empty")
            for member in members:
                _validate_member_crc(
                    archive,
                    member,
                    deadline=deadline,
                    monotonic=monotonic,
                )
            text_members = [
                member
                for member in members
                if not member.is_dir()
                and PurePosixPath(member.filename).suffix.casefold() == ".txt"
            ]
            product_members = [
                member
                for member in text_members
                if _member_matches_product_header(
                    archive,
                    member,
                    deadline=deadline,
                    monotonic=monotonic,
                )
            ]
            if (
                not product_members
                and len(text_members) == 1
                and PurePosixPath(text_members[0].filename).name.startswith(
                    "produkt_extrema_wind_"
                )
            ):
                product_members = text_members
            if len(product_members) != 1:
                raise AcquisitionError(
                    "archive must contain exactly one text member matching the DWD extreme-wind product header"
                )
            product_evidence = _validate_product_shape(
                archive,
                product_members[0],
                deadline=deadline,
                monotonic=monotonic,
            )
    except (OSError, zipfile.BadZipFile) as exc:
        raise AcquisitionError("downloaded object is not a valid ZIP archive") from exc
    return {
        "archive_member_count": len(members),
        "archive_uncompressed_bytes": total_uncompressed,
        "product_member": product_members[0].filename,
        **product_evidence,
    }


def _header_value(response: Any, name: str) -> str | None:
    headers = getattr(response, "headers", None)
    if headers is None:
        return None
    value = headers.get(name)
    if value is None:
        return None
    value = str(value).strip()
    return value[:512] if value else None


def _set_response_timeout(response: Any, timeout: float) -> None:
    """Tighten the live socket timeout to the remaining total deadline when available."""
    try:
        response.fp.raw._sock.settimeout(timeout)
    except AttributeError:
        # Injected test responses may not expose urllib's socket internals.
        return


def acquire(
    *,
    opener: Any | None = None,
    now: Any = utc_now,
    monotonic: Any = time.monotonic,
) -> dict[str, Any]:
    """Download only the frozen DWD ZIP, validate it, then return a strict small receipt."""
    if not _safe_source_url(SOURCE_URL):
        raise AcquisitionError("trusted source recipe is invalid")
    deadline = monotonic() + TOTAL_DEADLINE_SECONDS
    open_response = opener or _open_frozen_source
    request = urllib.request.Request(
        SOURCE_URL,
        headers={
            "Accept": "application/zip",
            "User-Agent": "OpenCatastrophe-acquisition-receipt-v1",
        },
        method="GET",
    )
    sha256 = hashlib.sha256()
    byte_count = 0
    final_url: str | None = None
    content_type: str | None = None
    last_modified: str | None = None
    etag: str | None = None
    declared_length: int | None = None

    with tempfile.TemporaryDirectory(prefix="oc-dwd-acquisition-") as tmpdir:
        target = os.path.join(tmpdir, FILENAME)
        try:
            with open_response(
                request,
                timeout=_remaining(deadline, monotonic),
            ) as response:
                _remaining(deadline, monotonic)
                status_code = getattr(response, "status", 200)
                if type(status_code) is not int or status_code != 200:
                    raise AcquisitionError("provider response status is not 200")
                final_url = response.geturl()
                if type(final_url) is not str or not _safe_source_url(final_url):
                    raise AcquisitionError(
                        "provider redirected outside the frozen source identity"
                    )
                content_length = _header_value(response, "Content-Length")
                if content_length is not None:
                    try:
                        declared_length = int(content_length)
                    except ValueError as exc:
                        raise AcquisitionError(
                            "provider Content-Length is invalid"
                        ) from exc
                    if declared_length < 1 or declared_length > MAX_BYTES:
                        raise AcquisitionError(
                            "provider Content-Length exceeds bounded policy"
                        )
                content_type = _header_value(response, "Content-Type")
                last_modified = _header_value(response, "Last-Modified")
                etag = _header_value(response, "ETag")
                with open(target, "wb") as output:
                    while True:
                        remaining = _remaining(deadline, monotonic)
                        _set_response_timeout(response, remaining)
                        chunk = response.read(CHUNK_SIZE)
                        if not chunk:
                            break
                        if type(chunk) is not bytes:
                            raise AcquisitionError(
                                "provider response yielded non-byte content"
                            )
                        byte_count += len(chunk)
                        if byte_count > MAX_BYTES:
                            raise AcquisitionError(
                                "download exceeded bounded byte limit"
                            )
                        sha256.update(chunk)
                        output.write(chunk)
        except AcquisitionError:
            raise
        except (
            OSError,
            urllib.error.URLError,
            urllib.error.HTTPError,
            TimeoutError,
        ) as exc:
            raise AcquisitionError(
                f"provider download failed: {type(exc).__name__}"
            ) from exc

        if byte_count < 1:
            raise AcquisitionError("provider returned an empty object")
        if declared_length is not None and declared_length != byte_count:
            raise AcquisitionError(
                "provider Content-Length does not match streamed byte count"
            )
        _remaining(deadline, monotonic)
        archive_evidence = _validate_zip(
            target,
            deadline=deadline,
            monotonic=monotonic,
        )
        _remaining(deadline, monotonic)
        retrieved_at = now()

    return {
        "schema_version": SCHEMA_VERSION,
        "dataset_id": DATASET_ID,
        "source_issue": 162,
        "requested_url": SOURCE_URL,
        "final_url": final_url,
        "filename": FILENAME,
        "retrieved_at": retrieved_at,
        "byte_count": byte_count,
        "sha256": sha256.hexdigest(),
        "content_type": content_type,
        "last_modified": last_modified,
        "etag": etag,
        **archive_evidence,
        "external_bytes_persisted": False,
        "publication_authorized": False,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.parse_args(argv)
    try:
        receipt = acquire()
    except AcquisitionError as exc:
        print(
            json.dumps(
                {"status": "blocked", "failure": str(exc)},
                sort_keys=True,
                separators=(",", ":"),
            )
        )
        return 2
    print(json.dumps(receipt, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
