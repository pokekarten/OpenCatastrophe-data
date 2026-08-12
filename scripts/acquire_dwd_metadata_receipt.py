# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Acquire the one frozen DWD station-00003 metadata ZIP ephemerally."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import ssl
import stat
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request
import zipfile
from pathlib import Path, PurePosixPath
from typing import Any

try:
    from scripts.acquire_dwd_extreme_wind_receipt import (
        AcquisitionError,
        FrozenHTTPSHandler,
        _header_value,
        _remaining,
        _set_response_timeout,
        _validate_member_crc,
        _validate_member_name,
        utc_now,
    )
    from scripts.inspect_dwd_metadata_zip import InspectionError, STATION_ID_RE, inspect_zip
except ModuleNotFoundError:  # pragma: no cover - direct script execution path
    from acquire_dwd_extreme_wind_receipt import (
        AcquisitionError,
        FrozenHTTPSHandler,
        _header_value,
        _remaining,
        _set_response_timeout,
        _validate_member_crc,
        _validate_member_name,
        utc_now,
    )
    from inspect_dwd_metadata_zip import InspectionError, STATION_ID_RE, inspect_zip

SCHEMA_VERSION = "oc-dwd-metadata-receipt-v1"
DATASET_ID = "dwd.cdc.obsgermany-climate-10min-extreme-wind.v24.03"
SOURCE_ISSUE = 211
FILENAME = "Meta_Daten_zehn_min_fx_00003.zip"
SOURCE_URL = (
    "https://opendata.dwd.de/climate_environment/CDC/observations_germany/climate/"
    "10_minutes/extreme_wind/meta_data/" + FILENAME
)
EXPECTED_HOST = "opendata.dwd.de"
EXPECTED_STATION_ID = "00003"
PROVIDER_FAMILY_PREFIXES = {
    "equipment": "metadaten_geraete",
    "geography": "metadaten_geographie",
    "parameter": "metadaten_parameter",
}
REQUIRED_METADATA_FAMILIES = frozenset(PROVIDER_FAMILY_PREFIXES)
MAX_BYTES = 5_242_880
MAX_ARCHIVE_MEMBERS = 128
MAX_UNCOMPRESSED_BYTES = 20_971_520
TOTAL_DEADLINE_SECONDS = 60.0
CHUNK_SIZE = 65_536
ALLOWED_COMPRESSION_METHODS = frozenset({zipfile.ZIP_STORED, zipfile.ZIP_DEFLATED})


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


def _provider_family_for_path(path: str) -> str | None:
    """Return only exact provider-native basename-prefix family evidence."""
    basename = PurePosixPath(path).name.casefold()
    matches: list[str] = []
    for family, prefix in PROVIDER_FAMILY_PREFIXES.items():
        if not basename.startswith(prefix):
            continue
        suffix = basename[len(prefix):]
        if not suffix or suffix[0] in "_.-":
            matches.append(family)
    if len(matches) > 1:
        raise AcquisitionError("metadata member has ambiguous provider-family prefix")
    return matches[0] if matches else None


class FrozenMetadataRedirectHandler(urllib.request.HTTPRedirectHandler):
    """Reject every redirect before urllib can leave the frozen metadata object."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):  # noqa: ANN001
        raise AcquisitionError("provider redirect is forbidden for the frozen metadata source")


def _open_frozen_source(request: urllib.request.Request, timeout: float):
    opener = urllib.request.build_opener(
        urllib.request.ProxyHandler({}),
        FrozenMetadataRedirectHandler(),
        FrozenHTTPSHandler(context=ssl.create_default_context()),
    )
    return opener.open(request, timeout=timeout)


def _inspection_evidence(path: str, *, deadline: float, monotonic: Any) -> dict[str, Any]:
    """Validate archive safety and bind exact station/provider-family evidence."""
    try:
        archive_bytes = os.path.getsize(path)
    except OSError as exc:
        raise AcquisitionError("metadata archive size cannot be read") from exc
    if not (1 <= archive_bytes <= MAX_BYTES):
        raise AcquisitionError("metadata archive compressed bytes are outside the bounded policy")

    try:
        with zipfile.ZipFile(path) as archive:
            members = archive.infolist()
            if not (1 <= len(members) <= MAX_ARCHIVE_MEMBERS):
                raise AcquisitionError("metadata archive member count is outside the bounded policy")
            total_uncompressed = 0
            total_compressed = 0
            for member in members:
                _remaining(deadline, monotonic)
                _validate_member_name(member.filename)
                mode = (member.external_attr >> 16) & 0o170000
                if mode not in (0, stat.S_IFREG, stat.S_IFDIR):
                    raise AcquisitionError("metadata archive contains a forbidden Unix special-file type")
                if member.flag_bits & 0x1:
                    raise AcquisitionError("encrypted metadata archive members are forbidden")
                if member.file_size < 0 or member.compress_size < 0:
                    raise AcquisitionError("metadata archive member sizes are invalid")
                if member.compress_type not in ALLOWED_COMPRESSION_METHODS:
                    raise AcquisitionError("metadata archive uses an unsupported compression method")
                total_compressed += member.compress_size
                if total_compressed > MAX_BYTES:
                    raise AcquisitionError("metadata archive compressed-member total exceeds bounded policy")
                total_uncompressed += member.file_size
                if total_uncompressed > MAX_UNCOMPRESSED_BYTES:
                    raise AcquisitionError("metadata archive exceeds uncompressed-size bound")
            if total_uncompressed < 1:
                raise AcquisitionError("metadata archive uncompressed payload is empty")
            for member in members:
                _validate_member_crc(archive, member, deadline=deadline, monotonic=monotonic)
    except AcquisitionError:
        raise
    except (OSError, zipfile.BadZipFile, zipfile.LargeZipFile) as exc:
        raise AcquisitionError("downloaded metadata object is not a valid ZIP archive") from exc

    try:
        inspection = inspect_zip(Path(path))
    except InspectionError as exc:
        raise AcquisitionError(f"metadata ZIP inspection failed: {exc}") from exc

    observed = inspection.get("observed")
    zip_evidence = inspection.get("zip")
    if type(observed) is not dict or type(zip_evidence) is not dict:
        raise AcquisitionError("metadata inspector returned an invalid evidence shape")
    station_ids = observed.get("station_ids")
    if station_ids != [EXPECTED_STATION_ID]:
        raise AcquisitionError("metadata archive station identity is not exactly frozen station 00003")

    member_records = zip_evidence.get("members")
    if type(member_records) is not list:
        raise AcquisitionError("metadata inspector returned invalid member evidence")
    bindings: list[dict[str, str]] = []
    for record in member_records:
        if type(record) is not dict or type(record.get("path")) is not str:
            raise AcquisitionError("metadata inspector returned invalid member record")
        member_path = record["path"]
        family = _provider_family_for_path(member_path)
        if family is None:
            continue
        member_station_ids = STATION_ID_RE.findall(PurePosixPath(member_path).name)
        if member_station_ids != [EXPECTED_STATION_ID]:
            raise AcquisitionError("required metadata-family member is not bound exactly to station 00003")
        bindings.append({"path": member_path, "family": family})
    bindings.sort(key=lambda item: (item["family"], item["path"]))
    if {item["family"] for item in bindings} != REQUIRED_METADATA_FAMILIES:
        missing = sorted(REQUIRED_METADATA_FAMILIES - {item["family"] for item in bindings})
        raise AcquisitionError(f"metadata archive lacks required provider families: {missing}")

    member_count = zip_evidence.get("member_count")
    inspected_total = zip_evidence.get("total_uncompressed_bytes")
    if type(member_count) is not int or member_count != len(members):
        raise AcquisitionError("metadata inspector member count does not match validated archive")
    if type(inspected_total) is not int or inspected_total != total_uncompressed:
        raise AcquisitionError("metadata inspector size total does not match validated archive")

    return {
        "archive_member_count": member_count,
        "archive_uncompressed_bytes": total_uncompressed,
        "station_id": EXPECTED_STATION_ID,
        "required_metadata_families": sorted(REQUIRED_METADATA_FAMILIES),
        "metadata_members": bindings,
        "temporal_coverage_status": "unverified",
    }


def acquire(
    *,
    opener: Any | None = None,
    now: Any = utc_now,
    monotonic: Any = time.monotonic,
) -> dict[str, Any]:
    """Download only the frozen metadata ZIP and return a small metadata-only receipt."""
    if not _safe_source_url(SOURCE_URL):
        raise AcquisitionError("trusted metadata source recipe is invalid")
    deadline = monotonic() + TOTAL_DEADLINE_SECONDS
    open_response = opener or _open_frozen_source
    request = urllib.request.Request(
        SOURCE_URL,
        headers={"Accept": "application/zip", "User-Agent": "OpenCatastrophe-dwd-metadata-receipt-v1"},
        method="GET",
    )
    sha256 = hashlib.sha256()
    byte_count = 0
    final_url: str | None = None
    content_type: str | None = None
    last_modified: str | None = None
    etag: str | None = None
    declared_length: int | None = None

    with tempfile.TemporaryDirectory(prefix="oc-dwd-metadata-") as tmpdir:
        target = os.path.join(tmpdir, FILENAME)
        try:
            with open_response(request, timeout=_remaining(deadline, monotonic)) as response:
                _remaining(deadline, monotonic)
                status_code = getattr(response, "status", 200)
                if type(status_code) is not int or status_code != 200:
                    raise AcquisitionError("provider metadata response status is not 200")
                final_url = response.geturl()
                if type(final_url) is not str or not _safe_source_url(final_url):
                    raise AcquisitionError("provider metadata response left the frozen source identity")
                content_length = _header_value(response, "Content-Length")
                if content_length is not None:
                    try:
                        declared_length = int(content_length)
                    except ValueError as exc:
                        raise AcquisitionError("provider metadata Content-Length is invalid") from exc
                    if declared_length < 1 or declared_length > MAX_BYTES:
                        raise AcquisitionError("provider metadata Content-Length exceeds bounded policy")
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
                            raise AcquisitionError("provider metadata response yielded non-byte content")
                        byte_count += len(chunk)
                        if byte_count > MAX_BYTES:
                            raise AcquisitionError("metadata download exceeded bounded byte limit")
                        sha256.update(chunk)
                        output.write(chunk)
        except AcquisitionError:
            raise
        except (OSError, urllib.error.URLError, urllib.error.HTTPError, TimeoutError) as exc:
            raise AcquisitionError(f"provider metadata download failed: {type(exc).__name__}") from exc

        if byte_count < 1:
            raise AcquisitionError("provider returned an empty metadata object")
        if declared_length is not None and declared_length != byte_count:
            raise AcquisitionError("provider metadata Content-Length does not match streamed byte count")
        _remaining(deadline, monotonic)
        archive_evidence = _inspection_evidence(target, deadline=deadline, monotonic=monotonic)
        _remaining(deadline, monotonic)
        retrieved_at = now()

    return {
        "schema_version": SCHEMA_VERSION,
        "dataset_id": DATASET_ID,
        "source_issue": SOURCE_ISSUE,
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
        print(json.dumps({"status": "blocked", "failure": str(exc)}, sort_keys=True, separators=(",", ":")))
        return 2
    print(json.dumps(receipt, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
