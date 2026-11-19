#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""First original Bavarian HU-BY open Shapefile Polygon, bounded ZIP prefix.

Read exactly 49,197 original ZIP bytes at a frozen ZIP-local-member offset:
one 45-byte hausumringe.shp ZIP header + 49,152 source DEFLATE bytes.
Incrementally decode only a bounded prefix of the original .shp member.
Check native SHP file header and the FIRST complete Polygon record's binary
structure, ring closure and bbox consistency, with no original coordinates,
record IDs, per-feature metrics, source bytes or geometries emitted/stored.

This does NOT check all 2.7m original records or original ZIP/SHP CRC and is
not independent proof of complete 2020/2026 footprints, original survey date,
insured assets, GHSL overlap, damage or CAT model input.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import ssl
import struct
import sys
import zlib
from urllib.error import HTTPError, URLError
from urllib.request import Request, ProxyHandler, HTTPSHandler, build_opener

from research_runners.by_hausumringe_oberbayern_zip_prefix_v0 import (
    URL, SOURCE, NoRedirect, PrefixBlocked,
)
from research_runners.by_hausumringe_oberbayern_zip_central_v0 import (
    TOTAL, FROZEN,
)
from research_runners.by_hausumringe_oberbayern_shx_v0 import (
    EXPECTED_SHX_ENTRIES, EXPECTED_SHP_LENGTH_CLAIM_ONLY,
)

START = 275_903
NAME = b"hausumringe.shp"
ZIP_HEADER_BYTES = 30 + len(NAME)
COMPRESSED_MEMBER_BYTES = 166_172_236
UNCOMPRESSED_SHP_BYTES = 501_212_696
ORIGINAL_DIRECTORY_CRC32_CLAIM = 0x55540A66
PREVIEW_COMPRESSED_BYTES = 49_152
READ_BYTES = ZIP_HEADER_BYTES + PREVIEW_COMPRESSED_BYTES
END = START + READ_BYTES - 1
RANGE = f"bytes={START}-{END}"
MAX_INFLATED_PREVIEW = 4_000_000
REVIEWED_SHAPE_TYPE = 5  # ESRI Shapefile Polygon
SHP_HEADER_BYTES = 100
RECORD_HEADER_BYTES = 8


class BVVShpPreviewBlocked(PrefixBlocked):
    """Source original bytes, SHP binary format or bounded geometry invalid."""


def inspect_bounded_shp_preview(decoded: bytes) -> dict:
    """Validate only header + first real Polygon record, without output geometry."""
    if (type(decoded) is not bytes or not 160 <= len(decoded) <= MAX_INFLATED_PREVIEW):
        raise BVVShpPreviewBlocked("original SHP preview size outside reviewed cap")
    if (struct.unpack_from(">I", decoded, 0)[0] != 9994
            or any(struct.unpack_from(">5I", decoded, 4))
            or struct.unpack_from(">I", decoded, 24)[0]*2 != UNCOMPRESSED_SHP_BYTES
            or struct.unpack_from("<II", decoded, 28) != (1000, REVIEWED_SHAPE_TYPE)):
        raise BVVShpPreviewBlocked("original .shp 100-byte header structure changed")
    x_min, y_min, x_max, y_max = struct.unpack_from("<4d", decoded, 36)
    if not (all(math.isfinite(v) for v in (x_min,y_min,x_max,y_max))
            and 250_000 < x_min < x_max < 950_000
            and 5_000_000 < y_min < y_max < 5_900_000):
        raise BVVShpPreviewBlocked("source header's UTM32 spatial envelope invalid")
    first = SHP_HEADER_BYTES
    recno, content_words = struct.unpack_from(">II", decoded, first)
    content_bytes = content_words*2
    if (recno != 1 or not 64 <= content_bytes <= MAX_INFLATED_PREVIEW
            or first+RECORD_HEADER_BYTES+content_bytes > len(decoded)):
        raise BVVShpPreviewBlocked("complete original first Polygon record not in bounded prefix")
    content = memoryview(decoded)[first+RECORD_HEADER_BYTES:
                                  first+RECORD_HEADER_BYTES+content_bytes]
    if struct.unpack_from("<I", content, 0)[0] != REVIEWED_SHAPE_TYPE:
        raise BVVShpPreviewBlocked("first record not original Polygon (5)")
    bx0, by0, bx1, by1 = struct.unpack_from("<4d", content, 4)
    parts, points = struct.unpack_from("<II", content, 36)
    if (not 1 <= parts <= 1000 or not 4 <= points <= 100_000
            or 44+4*parts+16*points != content_bytes
            or not all(math.isfinite(z) for z in (bx0,by0,bx1,by1))
            or not (x_min <= bx0 < bx1 <= x_max and y_min <= by0 < by1 <= y_max)):
        raise BVVShpPreviewBlocked("first Polygon geometry/size/bounding box malformed")
    offsets = struct.unpack_from("<" + "I"*parts, content, 44)
    if offsets[0] != 0 or any(offsets[i] >= offsets[i+1] for i in range(parts-1)):
        raise BVVShpPreviewBlocked("original first Polygon part offsets invalid")
    starts = tuple(offsets)+(points,)
    points_offset=44+4*parts
    actual_min_x=actual_min_y=float("inf")
    actual_max_x=actual_max_y=float("-inf")
    for i in range(parts):
        if starts[i+1]-starts[i]<4:
            raise BVVShpPreviewBlocked("original SHP Polygon ring too short")
        first_xy=last_xy=None
        for j in range(starts[i],starts[i+1]):
            x,y=struct.unpack_from("<dd",content,points_offset+16*j)
            if not (math.isfinite(x) and math.isfinite(y)
                    and x_min <= x <= x_max and y_min <= y <= y_max):
                raise BVVShpPreviewBlocked("invalid original Polygon coordinate range")
            if first_xy is None:
                first_xy=(x,y)
            last_xy=(x,y)
            actual_min_x=min(actual_min_x,x);actual_max_x=max(actual_max_x,x)
            actual_min_y=min(actual_min_y,y);actual_max_y=max(actual_max_y,y)
        if first_xy != last_xy:
            raise BVVShpPreviewBlocked("original Polygon ring is not closed")
    if (not math.isclose(actual_min_x,bx0,rel_tol=0,abs_tol=1e-6)
            or not math.isclose(actual_max_x,bx1,rel_tol=0,abs_tol=1e-6)
            or not math.isclose(actual_min_y,by0,rel_tol=0,abs_tol=1e-6)
            or not math.isclose(actual_max_y,by1,rel_tol=0,abs_tol=1e-6)):
        raise BVVShpPreviewBlocked("original first record bbox and vertex extrema disagree")
    return {
        "first_original_shape_record_complete": True,
        "original_shape_header_file_code": 9994,
        "original_shape_header_version": 1000,
        "original_shape_header_type": "Polygon (5)",
        "original_shape_header_reported_length_bytes": UNCOMPRESSED_SHP_BYTES,
        "original_shape_header_bbox_broad_utm32_sanity": True,
        "original_first_record_type": "Polygon (5)",
        "original_first_record_parts": parts,
        "original_first_record_points": points,
        "original_first_record_rings_closed": True,
        "original_first_record_bbox_matches_all_vertices": True,
        "original_first_record_content_sha256": hashlib.sha256(content).hexdigest(),
        "original_first_record_geometry_or_coordinates_persisted": False,
        "independent_geos_polygon_validity_checked": False,
        "full_original_shp_crc32_or_sha256_verified": False,
        "source_survey_vintage_verified": False,
        "model_input_approved": False,
    }


def inspect_original_shp_prefix(raw: bytes, *, status: int, response_url: str, headers) -> dict:
    if type(raw) is not bytes or len(raw) != READ_BYTES:
        raise BVVShpPreviewBlocked("exact original 49,197 byte ZIP source Range required")
    if status != 206 or response_url != URL:
        raise BVVShpPreviewBlocked("source must return original HTTP 206 without redirects")
    if headers.get("Content-Range") != f"bytes {START}-{END}/{TOTAL}":
        raise BVVShpPreviewBlocked("original compressed SHP source file/offset changed")
    if headers.get("Content-Length") not in (None,str(READ_BYTES)):
        raise BVVShpPreviewBlocked("original provider response size mismatch")
    if headers.get("Content-Encoding","identity").lower() != "identity":
        raise BVVShpPreviewBlocked("unexpected HTTP-level content compression")
    if headers.get("Content-Type","").split(";",1)[0].strip().lower() not in (
        "application/zip","application/octet-stream","binary/octet-stream"
    ):
        raise BVVShpPreviewBlocked("source MIME no longer reviewed original ZIP")
    if raw[:4] != b"PK\x03\x04":
        raise BVVShpPreviewBlocked("original local ZIP header signature absent")
    version, flags, method, mtime, mdate, crc, compressed, uncompressed, name_len, extra_len = (
        struct.unpack_from("<HHHHHIIIHH", raw, 4)
    )
    if (version,flags,method,crc,compressed,uncompressed,name_len,extra_len) != (
        20,0,8,ORIGINAL_DIRECTORY_CRC32_CLAIM,COMPRESSED_MEMBER_BYTES,
        UNCOMPRESSED_SHP_BYTES,len(NAME),0
    ):
        raise BVVShpPreviewBlocked("original SHP ZIP local header disagrees with frozen central directory")
    if (raw[30:ZIP_HEADER_BYTES] != NAME
            or FROZEN["hausumringe.shp"] != (START, COMPRESSED_MEMBER_BYTES, UNCOMPRESSED_SHP_BYTES)
            or UNCOMPRESSED_SHP_BYTES != EXPECTED_SHP_LENGTH_CLAIM_ONLY
            or EXPECTED_SHX_ENTRIES != 2_703_736):
        raise BVVShpPreviewBlocked("original source filename/size or SHX reference drift")
    compressed_prefix = raw[ZIP_HEADER_BYTES:]
    try:
        inflater = zlib.decompressobj(wbits=-15)
        decoded = inflater.decompress(compressed_prefix, MAX_INFLATED_PREVIEW+1)
    except zlib.error as exc:
        raise BVVShpPreviewBlocked("original partial raw DEFLATE cannot decode") from exc
    if (len(decoded) > MAX_INFLATED_PREVIEW or inflater.unconsumed_tail
            or inflater.unused_data or inflater.eof):
        raise BVVShpPreviewBlocked("unreviewed inflation, trailing data, or unexpectedly completed full SHP")
    # This is only a leading PREVIEW of the original 501 MB SHP, so
    # full-member DEFLATE EOF, CRC32 and complete archive SHA must NOT pass.
    geometry = inspect_bounded_shp_preview(decoded)
    return {
        "profile": "oc-bvv-oberbayern-original-shp-first-49k-prefix-and-polygon-v0",
        "source_id": SOURCE,
        "official_public_zip_url": URL,
        "original_source_range": RANGE,
        "original_source_response_bytes": READ_BYTES,
        "original_http_response_sha256": hashlib.sha256(raw).hexdigest(),
        "original_zip_compressed_shp_prefix_sha256": hashlib.sha256(compressed_prefix).hexdigest(),
        "original_partial_shp_uncompressed_bytes": len(decoded),
        "original_partial_shp_uncompressed_sha256": hashlib.sha256(decoded).hexdigest(),
        "original_100_byte_shp_header_sha256": hashlib.sha256(decoded[:100]).hexdigest(),
        "zip_member_declared_full_original_crc32_unverified": f"{ORIGINAL_DIRECTORY_CRC32_CLAIM:08x}",
        "full_original_shape_polygon_count_verified": False,
        "full_original_zip_or_shp_sha256_verified": False,
        "original_shp_member_bytes_or_geometries_persisted": False,
        "original_shp_file_crs_from_separately_verified_prj": "EPSG:25832",
        "source_reference_is_2026_public_bavaria_not_2020_ghsl_truth": True,
        "model_input_approved": False,
        **geometry,
    }


def probe() -> dict:
    req = Request(URL,method="GET",headers={
        "Range": RANGE, "Accept-Encoding": "identity", "Accept":"application/zip",
        "User-Agent":"OpenCatastrophe-BVV-OriginalSHP-FirstPolygon-49KiB/0.1",
    })
    try:
        with build_opener(ProxyHandler({}),NoRedirect(),
                          HTTPSHandler(context=ssl.create_default_context())
                          ).open(req,timeout=40) as res:
            if res.status != 206:
                raise BVVShpPreviewBlocked("original provider ignored bounded Range")
            raw = res.read(READ_BYTES+1)
            result=inspect_original_shp_prefix(raw,status=res.status,
                    response_url=res.geturl(),headers=res.headers)
    except (HTTPError,URLError,OSError,TimeoutError) as exc:
        raise BVVShpPreviewBlocked("original ZIP SHP 49KiB Range unavailable") from exc
    result["retrieved_at_utc"]=datetime.now(timezone.utc).isoformat()
    result["reviewed_script_sha256"]=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    return result


def main(argv=None) -> int:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--live",action="store_true")
    args=parser.parse_args(argv)
    if not args.live:
        parser.error("explicit trusted-main --live required for original SHP source")
    try:
        print(json.dumps(probe(),sort_keys=True,allow_nan=False))
        return 0
    except BVVShpPreviewBlocked:
        print("BLOCKED: exact original BVV first Shapefile Polygon unavailable",
              file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
