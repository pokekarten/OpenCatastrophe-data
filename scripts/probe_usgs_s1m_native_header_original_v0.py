#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""One reviewed original USGS S1M TIFF HTTP 206 64 KiB prefix; no pixels or import.

This is a bounded source-native research receipt, NOT a full-file hash,
per-pixel elevation proof, vertical-datum verification or CAT model admission.
No caller controls host, URL, range, size, redirect, headers or credentials.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import ssl
import struct
import sys
from typing import Any, Callable
from urllib import error, request

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.validate_source_access import validate_path

ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = ROOT / "access/usgs.3dep.s1m.florida-native-tiff-prefix.json"
HOST = "https://prd-tnm.s3.amazonaws.com"
PATH = "/StagedProducts/Elevation/S1M/n04e15/n0450e1510/S1M_n0450e1510_20260821.tif"
URL = HOST + PATH
OPERATION = "probe_exact_florida_s1m_header_65536"
BYTE_COUNT = 65536
BYTE_RANGE = "bytes=0-65535"
TIMEOUT = 25
MAX_FILE_BYTES = 1024 * 1024 * 1024
MIN_FILE_BYTES = 1024 * 1024
PROFILE = "oc-usgs-3dep-s1m-florida-original-prefix-t1-v0"
EXPECTED_MEDIA = {"image/tiff", "application/x-tiff",
                  "application/octet-stream", "binary/octet-stream"}
RANGE_PATTERN = re.compile(r"bytes 0-65535/([1-9][0-9]{0,12})\Z")
# Exact original HTTP206 source receipt: GitHub run 43948359780 job 133583989829.
# This is NOT a checksum of the whole 447MB provider GeoTIFF.
EXPECTED_ORIGINAL_PREFIX_SHA256 = "56d8d147056fcd28ad916799cd6b917c57d9d08b3e07dfe06931f2a4d5edb2f2"
EXPECTED_ORIGINAL_TOTAL_BYTES = 447032917


class Blocked(ValueError):
    """A source request/response or scientific identity is outside reviewed scope."""


def frozen_contract(contract_path: Path = CONTRACT_PATH) -> tuple[dict[str, Any], str]:
    original_contract_bytes = contract_path.read_bytes()
    c = validate_path(contract_path)
    rights = c["rights_and_policy"]
    a = c["authentication"]
    p = c["probe_contract"]
    if (
        c["access_id"] != "usgs.3dep.s1m.florida-native-tiff-prefix"
        or c["source_ids"] != ["usgs.3dep.seamless-1m.s1m"]
        or c["status"] != "probe_ready"
        or c["service_root"] != HOST
        or c["interface_type"] != "http_file"
        or c["request_contract"]["allowed_operations"] != [OPERATION]
        or c["request_contract"]["path_templates"] != [PATH]
        or BYTE_RANGE not in c["request_contract"]["parameter_rules"]
        or c["access_scope"] != ["sample"]
        or c["operational_constraints"]["timeout_seconds"] != TIMEOUT
        or c["operational_constraints"]["max_probe_bytes"] != BYTE_COUNT
        or c["operational_constraints"]["retry_policy"] != "none"
        or a["mode"] != "none"
        or a["credential_reference"] is not None
        or p["mode"] != "provider_specific"
        or p["operation"] != OPERATION
        or p["requires_credentials"] is not False
        or rights["dataset_rights_status"] != "verified"
        or rights["api_terms_status"] != "same_as_dataset"
        or rights["commercial_automation_status"] != "allowed"
        or rights["redistribution_status"] != "unknown"
        or c["implementation_decision"] != "build_adapter_now"
    ):
        raise Blocked("original USGS S1M prefix review changed; fail closed")
    if set(c["response_contract"]["expected_media_types"]) != EXPECTED_MEDIA:
        raise Blocked("response media review changed")
    return c, hashlib.sha256(original_contract_bytes).hexdigest()


def first_ifd(prefix: bytes) -> dict[str, Any]:
    """Read only source-TIFF header/first IFD when wholly inside reviewed range."""
    if type(prefix) is not bytes or len(prefix) != BYTE_COUNT or prefix[:2] not in (b"II", b"MM"):
        raise Blocked("original prefix is not a complete TIFF-ordered 64 KiB sample")
    endian = "<" if prefix[:2] == b"II" else ">"
    magic = struct.unpack_from(endian + "H", prefix, 2)[0]
    if magic == 42:
        ifd_offset = struct.unpack_from(endian + "I", prefix, 4)[0]
        count_size, entry_size, trailer, value_size = 2, 12, 4, 4
        kind = "classic_tiff"
    elif magic == 43:
        if struct.unpack_from(endian + "HH", prefix, 4) != (8, 0):
            raise Blocked("unsupported BigTIFF offset-size/reserved fields")
        ifd_offset = struct.unpack_from(endian + "Q", prefix, 8)[0]
        count_size, entry_size, trailer, value_size = 8, 20, 8, 8
        kind = "bigtiff"
    else:
        raise Blocked("source prefix lacks classic TIFF / BigTIFF signature")
    out = {
        "source_tiff_magic_verified": True,
        "tiff_format": kind,
        "byte_order": "little" if endian == "<" else "big",
        "first_ifd_offset": ifd_offset,
        "first_ifd_fully_in_prefix": False,
        "first_ifd_entry_count": None,
        "width_from_original_ifd": None,
        "height_from_original_ifd": None,
        "geokey_tag_present": False,
        "gdal_nodata_tag_present": False,
        "model_pixel_scale_tag_present": False,
        "original_epsg_6350_verified": False,
        "original_geoid18_verified": False,
        "original_pixel_values_verified": False,
        "native_raster_science_admitted": False,
    }
    if ifd_offset < (8 if kind == "classic_tiff" else 16):
        raise Blocked("first TIFF IFD offset falls inside header")
    if ifd_offset + count_size > len(prefix):
        return out
    count = struct.unpack_from(endian + ("H" if kind == "classic_tiff" else "Q"), prefix, ifd_offset)[0]
    if not 0 < count <= 512:
        raise Blocked("first TIFF IFD entry count is invalid or unbounded")
    end = ifd_offset + count_size + count * entry_size + trailer
    if end > len(prefix):
        return out
    tags: dict[int, tuple[int, int, bytes]] = {}
    for index in range(count):
        off = ifd_offset + count_size + index * entry_size
        if kind == "classic_tiff":
            tag, dtype, num = struct.unpack_from(endian + "HHI", prefix, off)
            val = prefix[off + 8:off + 12]
        else:
            tag, dtype, num = struct.unpack_from(endian + "HHQ", prefix, off)
            val = prefix[off + 12:off + 20]
        if tag in tags:
            raise Blocked("duplicate original TIFF IFD tag")
        tags[tag] = (dtype, num, val)
    for tag, label in ((256, "width_from_original_ifd"), (257, "height_from_original_ifd")):
        if tag not in tags:
            continue
        dtype, num, inline = tags[tag]
        if num != 1 or dtype not in (3, 4, 16):
            raise Blocked("original TIFF first IFD width/height not an inline integer")
        if dtype == 16 and len(inline) != 8:
            raise Blocked("unreadable TIFF LONG8 dimensions")
        if dtype == 3:
            value = struct.unpack_from(endian + "H", inline)[0]
        elif dtype == 4:
            value = struct.unpack_from(endian + "I", inline)[0]
        else:
            value = struct.unpack_from(endian + "Q", inline)[0]
        if not 1 <= value <= 100000:
            raise Blocked("unreasonable original S1M TIFF first-IFD dimensions")
        out[label] = value
    out.update({
        "first_ifd_fully_in_prefix": True,
        "first_ifd_entry_count": count,
        "geokey_tag_present": 34735 in tags,
        "gdal_nodata_tag_present": 42113 in tags,
        "model_pixel_scale_tag_present": 33550 in tags,
    })
    return out


class NoRedirect(request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise Blocked("redirect disallowed for pinned USGS original range")


def _open(req: request.Request, timeout: int):
    opener = request.build_opener(
        request.ProxyHandler({}),
        NoRedirect(),
        request.HTTPSHandler(context=ssl.create_default_context()),
    )
    return opener.open(req, timeout=timeout)


def observe(
    *,
    open_request: Callable[[request.Request, int], Any] = _open,
    contract_path: Path = CONTRACT_PATH,
    clock: Callable[[], datetime] = lambda: datetime.now(timezone.utc),
) -> dict[str, Any]:
    _, contract_hash = frozen_contract(contract_path)
    req = request.Request(
        URL, method="GET", headers={
            "Range": BYTE_RANGE,
            "Accept": "application/octet-stream",
            "Accept-Encoding": "identity",
            "User-Agent": "OpenCatastrophe-USGS-S1M-Original-Prefix/0.1",
        }
    )
    try:
        with open_request(req, TIMEOUT) as response:
            if response.geturl() != URL or type(response.status) is not int or response.status != 206:
                raise Blocked("original USGS endpoint did not return exact HTTP 206 without redirect")
            content_range = response.headers.get("Content-Range", "").strip()
            found = RANGE_PATTERN.fullmatch(content_range)
            if found is None:
                raise Blocked("missing or mismatched exact USGS original Content-Range")
            total = int(found.group(1))
            if not MIN_FILE_BYTES <= total <= MAX_FILE_BYTES:
                raise Blocked("advertised original full-TIFF byte count outside reviewed bounds")
            media = response.headers.get("Content-Type", "").split(";", 1)[0].lower().strip()
            if media not in EXPECTED_MEDIA:
                raise Blocked("unreviewed USGS original response MIME type")
            if response.headers.get("Content-Encoding", "identity").strip().lower() != "identity":
                raise Blocked("source sent unreviewed compressed transfer encoding")
            length = response.headers.get("Content-Length")
            if length is not None and (not length.isascii() or not length.isdecimal() or int(length) != BYTE_COUNT):
                raise Blocked("source original Content-Length differs from reviewed range")
            raw = response.read(BYTE_COUNT + 1)
            if len(raw) != BYTE_COUNT:
                raise Blocked("bounded USGS original source range byte count mismatch")
    except Blocked:
        raise
    except (error.HTTPError, error.URLError, OSError, TimeoutError) as exc:
        raise Blocked("fixed USGS original prefix request unavailable") from exc

    observed_prefix_sha = hashlib.sha256(raw).hexdigest()
    if total != EXPECTED_ORIGINAL_TOTAL_BYTES or observed_prefix_sha != EXPECTED_ORIGINAL_PREFIX_SHA256:
        raise Blocked("pinned USGS S1M original prefix SHA or complete-object size drift")
    headers = first_ifd(raw)
    ts = clock()
    if not isinstance(ts, datetime) or ts.utcoffset() is None:
        raise Blocked("source observation lacks timezone-aware UTC")
    return {
        "status": "source_original_partial_prefix_only",
        "profile": PROFILE,
        "source_id": "usgs.3dep.seamless-1m.s1m",
        "original_tiff_public_url": URL,
        "observation_utc": ts.astimezone(timezone.utc).isoformat(),
        "request_sha256": hashlib.sha256(
            ("GET " + URL + "\nRange: " + BYTE_RANGE + "\n").encode("ascii")
        ).hexdigest(),
        "contract_sha256": contract_hash,
        "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "original_http_status": 206,
        "original_content_range": content_range,
        "original_prefix_bytes": len(raw),
        "original_prefix_sha256": observed_prefix_sha,
        "original_total_bytes_advertised_not_full_sha": total,
        **headers,
        "full_original_tiff_sha256_verified": False,
        "original_source_lineage_geopackage_verified": False,
        "original_source_bytes_persisted": False,
        "neon_write_performed": False,
        "cat_model_input_approved": False,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--live", action="store_true", help="one exact original 64KiB GET, no other download")
    options = parser.parse_args(argv)
    if not options.live:
        parser.error("the bounded original provider request requires explicit --live")
    try:
        print(json.dumps(observe(), sort_keys=True, allow_nan=False))
    except (Blocked, OSError, ValueError) as exc:
        print("BLOCKED: " + str(exc), file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
