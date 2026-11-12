#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Verify exact ORIGINAL 301-byte HU-BY Oberbayern ZIP local .prj member in place.

Single HTTP 206 range: 45-byte ZIP local header plus exactly 256 bytes of
raw-DEFLATE projection file. The ZIP directory says 388 original bytes.
Check exact source identity, local header, compressed/raw SHA256, CRC32,
WKT format and independently parsed pyproj EPSG:25832. No .shp data,
coordinates, archive download, source persistence or model admission.
"""
from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import ssl
import struct
import sys
import zlib
from urllib.error import HTTPError, URLError
from urllib.request import Request, ProxyHandler, HTTPSHandler, build_opener

from research_runners.by_hausumringe_oberbayern_zip_prefix_v0 import (
    URL, SOURCE, NoRedirect, PrefixBlocked
)
from research_runners.by_hausumringe_oberbayern_zip_central_v0 import TOTAL

START = 275_602
LIMIT = 301
END = START + LIMIT - 1
RANGE = f"bytes={START}-{END}"
NAME = b"hausumringe.prj"
EXPECTED_CRC32 = 0xD49ECECB
EXPECTED_COMPRESSED = 256
EXPECTED_UNCOMPRESSED = 388
SOURCE_DEFLATE_SHA256 = "055f581691a9def92166569c959a0713d4c0e34cf746d1238821ad18caaea2c8"
SOURCE_WKT_SHA256 = "03c412dbe0da64f769d15d4de5ee08309680542a54630d3e8baf8d82d0091670"


class ProjectionBlocked(PrefixBlocked):
    """Projection original bytes or CRS fail strict first-party source review."""


def inspect_projection(raw: bytes, *, status: int, response_url: str, headers: dict) -> dict:
    if type(raw) is not bytes or len(raw) != LIMIT:
        raise ProjectionBlocked("expected one exact 301-byte original local ZIP member")
    if status != 206 or response_url != URL:
        raise ProjectionBlocked("ZIP .prj must be HTTP 206 from immutable first-party URL")
    if headers.get("Content-Range") != f"bytes {START}-{END}/{TOTAL}":
        raise ProjectionBlocked("original ZIP .prj member offset/total size changed")
    if headers.get("Content-Length") not in (None, str(LIMIT)):
        raise ProjectionBlocked("unexpected original .prj range Content-Length")
    if headers.get("Content-Encoding", "identity").lower() != "identity":
        raise ProjectionBlocked("ZIP transport must preserve raw original deflate")
    if headers.get("Content-Type", "").split(";", 1)[0].lower().strip() not in (
        "application/zip", "application/octet-stream", "binary/octet-stream"
    ):
        raise ProjectionBlocked("original ZIP media type changed")
    if raw[:4] != b"PK\x03\x04":
        raise ProjectionBlocked("original .prj local ZIP signature mismatched")
    (version, flags, method, mtime, mdate, crc,
     compressed, inflated, name_len, extra_len) = struct.unpack_from(
        "<HHHHHIIIHH", raw, 4
    )
    if (version, flags, method, crc, compressed, inflated, name_len, extra_len) != (
        20, 0, 8, EXPECTED_CRC32, EXPECTED_COMPRESSED,
        EXPECTED_UNCOMPRESSED, len(NAME), 0
    ):
        raise ProjectionBlocked("original .prj ZIP member metadata drift")
    if raw[30:30+len(NAME)] != NAME:
        raise ProjectionBlocked("original .prj ZIP member name changed")
    data = raw[30+len(NAME):]
    if len(data) != EXPECTED_COMPRESSED or hashlib.sha256(data).hexdigest() != SOURCE_DEFLATE_SHA256:
        raise ProjectionBlocked("original projection compressed bytes changed")
    try:
        decoder = zlib.decompressobj(wbits=-15)
        wkt = decoder.decompress(data, EXPECTED_UNCOMPRESSED + 1)
        tail = decoder.flush()
    except zlib.error as exc:
        raise ProjectionBlocked("original ZIP .prj raw DEFLATE invalid") from exc
    if (tail or not decoder.eof or decoder.unconsumed_tail or decoder.unused_data
            or len(wkt) != EXPECTED_UNCOMPRESSED):
        raise ProjectionBlocked("original projection payload not exactly complete and bounded")
    if zlib.crc32(wkt) != EXPECTED_CRC32:
        raise ProjectionBlocked("original .prj CRC32 not equal ZIP directory")
    if hashlib.sha256(wkt).hexdigest() != SOURCE_WKT_SHA256:
        raise ProjectionBlocked("original WKT byte SHA256 mismatch")
    try:
        original_wkt = wkt.decode("ascii")
    except UnicodeDecodeError as exc:
        raise ProjectionBlocked("unexpected original .prj WKT encoding") from exc
    if (not original_wkt.startswith('PROJCS["ETRS89_UTM_zone_32N"')
        or '"GCS_ETRS_1989"' not in original_wkt
        or '"Transverse_Mercator"' not in original_wkt):
        raise ProjectionBlocked("original WKT map projection identity changed")
    try:
        from pyproj import CRS
        crs = CRS.from_wkt(original_wkt)
        epsg = crs.to_epsg()
    except (ImportError, ValueError, RuntimeError) as exc:
        raise ProjectionBlocked("independent PROJ/pyproj original WKT verification failed") from exc
    if epsg != 25832 or not crs.is_projected:
        raise ProjectionBlocked("projection not independently identified as EPSG:25832")
    return {
        "profile": "oc-bvv-hu-by-oberbayern-original-301b-prj-crs-v0",
        "source_id": SOURCE,
        "original_zip_url": URL,
        "http_status": status,
        "original_zip_total_bytes": TOTAL,
        "original_exact_prj_byte_range": RANGE,
        "original_local_header_plus_compressed_bytes": LIMIT,
        "original_compressed_projection_sha256": SOURCE_DEFLATE_SHA256,
        "original_uncompressed_wkt_sha256": SOURCE_WKT_SHA256,
        "original_wkt_bytes_verified": len(wkt),
        "original_zip_member_crc32_verified": f"{EXPECTED_CRC32:08x}",
        "source_projection": "ETRS89 / UTM zone 32N",
        "independent_pyproj_epsg": epsg,
        "original_projection_member_complete": True,
        "original_polygon_coordinates_retrieved": False,
        "complete_zip_sha256_verified": False,
        "source_survey_snapshot_verified": False,
        "provider_bytes_persisted": False,
        "model_input_approved": False,
    }


def probe() -> dict:
    req = Request(URL, method="GET", headers={
        "Range": RANGE, "Accept-Encoding": "identity", "Accept": "application/zip",
        "User-Agent": "OpenCatastrophe-BVV-PRJ-301Byte-Original-Only/0.1",
    })
    try:
        with build_opener(
            ProxyHandler({}), NoRedirect(),
            HTTPSHandler(context=ssl.create_default_context()),
        ).open(req, timeout=25) as res:
            if res.status != 206:
                raise ProjectionBlocked("provider ignored bounded projection HTTP Range")
            body = res.read(LIMIT+1)
            result = inspect_projection(body, status=res.status,
                                        response_url=res.geturl(), headers=res.headers)
    except (HTTPError, URLError, TimeoutError, OSError) as exc:
        raise ProjectionBlocked("original BVV projection single-member request unavailable") from exc
    result["retrieved_at_utc"] = datetime.now(timezone.utc).isoformat()
    result["runner_sha256"] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    return result


def main(argv=None):
    import argparse
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--live",action="store_true")
    args=p.parse_args(argv)
    if not args.live:
        p.error("original projection network read is opt-in")
    try:
        print(json.dumps(probe(),sort_keys=True))
        return 0
    except ProjectionBlocked:
        print("BLOCKED: original HU-BY .prj source projection not verified",file=sys.stderr)
        return 2


if __name__=="__main__":
    raise SystemExit(main())
