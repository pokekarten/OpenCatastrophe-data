#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Verify one original publicly licensed BVV Hausumringe SHX ZIP member only.

Exact HTTP Range returns 45-byte local ZIP header plus 7,851,126 compressed
bytes. Raw DEFLATE yields the 21,629,988-byte original Shapefile *index*.
Check original ZIP CRC, SHX header, file size, EPSG-independent map extent
sanity, every two-longword offset/record-length pair, contiguity and final
offset matching directory-REPORTED SHP byte length. No actual SHP, geometry,
feature IDs, raw indexes, reference positions or survey vintage are exported.
"""
from __future__ import annotations

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
    URL, SOURCE, NoRedirect, PrefixBlocked
)
from research_runners.by_hausumringe_oberbayern_zip_central_v0 import (
    TOTAL, FROZEN, CENTRAL_START
)
from research_runners.by_hausumringe_oberbayern_dbf_v0 import EXPECTED_DBF_RECORDS

NAME = b"hausumringe.shx"
START = 166_448_184
ZIP_LOCAL_HEADER_BYTES = 30 + len(NAME)
COMPRESSED = 7_851_126
UNCOMPRESSED = 21_629_988
READ_BYTES = ZIP_LOCAL_HEADER_BYTES + COMPRESSED
END = START + READ_BYTES - 1
RANGE = f"bytes={START}-{END}"
ORIGINAL_CRC32 = 0xF6D2BBB8
SHAPE_TYPE_POLYGON = 5
SHX_HEADER_BYTES = 100
RECORD_BYTES = 8
EXPECTED_SHX_ENTRIES = 2_703_736
# The whole 501MB compressed Shape polygon member is still NOT read or hashed.
EXPECTED_SHP_LENGTH_CLAIM_ONLY = 501_212_696


class SHXBlocked(PrefixBlocked):
    """Original index identity or source-format consistency failure."""


def inspect_original_shx(raw: bytes, *, status: int, response_url: str,
                         headers) -> dict:
    if type(raw) is not bytes or len(raw) != READ_BYTES:
        raise SHXBlocked("exact original ZIP index single-member byte cap violated")
    if status != 206 or response_url != URL:
        raise SHXBlocked("original publicly licensed ZIP URL/206 required")
    if headers.get("Content-Range", "") != f"bytes {START}-{END}/{TOTAL}":
        raise SHXBlocked("original SHX member Range or total ZIP identity changed")
    if headers.get("Content-Length") not in (None, str(READ_BYTES)):
        raise SHXBlocked("original source index Content-Length drift")
    if headers.get("Content-Encoding", "identity").lower() != "identity":
        raise SHXBlocked("HTTP encoding changes ZIP original bytes")
    if headers.get("Content-Type", "").split(";", 1)[0].strip().lower() not in (
        "application/zip", "application/octet-stream", "binary/octet-stream"
    ):
        raise SHXBlocked("ZIP source MIME identity changed")
    if raw[:4] != b"PK\x03\x04":
        raise SHXBlocked("original index local ZIP signature missing")
    (version, flags, method, mtime, mdate, crc, zipped, inflated,
     name_len, extra_len) = struct.unpack_from("<HHHHHIIIHH", raw, 4)
    if (version, flags, method, crc, zipped, inflated, name_len, extra_len) != (
        20, 0, 8, ORIGINAL_CRC32, COMPRESSED, UNCOMPRESSED, len(NAME), 0
    ):
        raise SHXBlocked("original SHX local ZIP header differs from central directory")
    if (raw[30:ZIP_LOCAL_HEADER_BYTES] != NAME
            or FROZEN["hausumringe.shx"] != (START,COMPRESSED,UNCOMPRESSED)
            or END + 1 != CENTRAL_START):
        raise SHXBlocked("SHX directory member name/boundaries drift")
    compressed = raw[ZIP_LOCAL_HEADER_BYTES:]
    try:
        decoder=zlib.decompressobj(wbits=-15)
        data=decoder.decompress(compressed,UNCOMPRESSED+1)
        if len(data) != UNCOMPRESSED or decoder.unconsumed_tail:
            raise SHXBlocked("index output count outside approved memory bound")
        tail=decoder.flush()
    except zlib.error as exc:
        raise SHXBlocked("SHX original raw deflate cannot decode") from exc
    if (tail or not decoder.eof or decoder.unused_data or decoder.unconsumed_tail
            or len(data) != UNCOMPRESSED or zlib.crc32(data) != ORIGINAL_CRC32):
        raise SHXBlocked("original compressed index truncated, appended or CRC drift")
    if (UNCOMPRESSED-SHX_HEADER_BYTES)%RECORD_BYTES:
        raise SHXBlocked("non-integer Shapefile index entries")
    count=(UNCOMPRESSED-SHX_HEADER_BYTES)//RECORD_BYTES
    if count != EXPECTED_SHX_ENTRIES or count != EXPECTED_DBF_RECORDS:
        raise SHXBlocked("index entry count differs from original verified DBF")
    file_code=struct.unpack_from(">I",data,0)[0]
    reserved=struct.unpack_from(">5I",data,4)
    file_words=struct.unpack_from(">I",data,24)[0]
    version,shape_type=struct.unpack_from("<II",data,28)
    if (file_code != 9994 or any(reserved)
            or file_words*2 != UNCOMPRESSED
            or version != 1000 or shape_type != SHAPE_TYPE_POLYGON):
        raise SHXBlocked("original index big/little-endian Shape header malformed")
    x_min,y_min,x_max,y_max=struct.unpack_from("<4d",data,36)
    if not (all(math.isfinite(v) for v in (x_min,y_min,x_max,y_max))
            and 250_000 < x_min < x_max < 950_000
            and 5_000_000 < y_min < y_max < 5_900_000):
        raise SHXBlocked("original index spatial reference extent unexpected")
    # No per-feature positions are emitted. Check every true source index entry
    # monotonically and exactly against contiguous uncompressed SHP records.
    expected_word_offset=SHX_HEADER_BYTES//2
    smallest=None
    largest=0
    n=0
    for offset_words,content_words in struct.iter_unpack(
        ">II",memoryview(data)[SHX_HEADER_BYTES:]
    ):
        if offset_words != expected_word_offset or not 1 <= content_words <= 1_000_000:
            raise SHXBlocked("original .shx feature pointer/count not contiguous")
        size_bytes=content_words*2
        smallest=size_bytes if smallest is None else min(smallest,size_bytes)
        largest=max(largest,size_bytes)
        expected_word_offset+=4+content_words
        n+=1
    if (n != count or expected_word_offset*2 != EXPECTED_SHP_LENGTH_CLAIM_ONLY
            or FROZEN["hausumringe.shp"][2] != EXPECTED_SHP_LENGTH_CLAIM_ONLY):
        raise SHXBlocked("last index record does not terminate at declared SHP size")
    return {
        "profile":"oc-bvv-oberbayern-original-shx-index-crc-all-records-v0",
        "source_id":SOURCE,
        "official_public_original_zip_url":URL,
        "original_zip_total_bytes":TOTAL,
        "original_source_range":RANGE,
        "original_http_range_sha256":hashlib.sha256(raw).hexdigest(),
        "original_shx_compressed_sha256":hashlib.sha256(compressed).hexdigest(),
        "original_shx_uncompressed_sha256":hashlib.sha256(data).hexdigest(),
        "original_shx_decompressed_bytes_verified":len(data),
        "original_zip_crc32_verified":f"{ORIGINAL_CRC32:08x}",
        "original_shx_header_shape_type":"Polygon (5)",
        "original_shx_file_code":file_code,
        "original_shx_version":version,
        "original_index_entries_verified":count,
        "verified_dbf_row_count_reference":EXPECTED_DBF_RECORDS,
        "index_records_contiguous_no_gaps":True,
        "first_index_record_starts_at_shp_byte_100":True,
        "last_index_record_ends_at_shp_byte_claim":EXPECTED_SHP_LENGTH_CLAIM_ONLY,
        "min_index_record_content_bytes":smallest,
        "max_index_record_content_bytes":largest,
        "header_bbox_broad_epsg25832_extent_sanity":True,
        "source_shp_polygon_bytes_fetched":False,
        "source_feature_positions_persisted":False,
        "source_feature_ids_or_geometry_emitted":False,
        "original_shp_sha256_verified":False,
        "original_full_zip_sha256_verified":False,
        "source_capture_survey_vintage_verified":False,
        "model_input_approved":False,
    }


def probe() -> dict:
    req=Request(URL,method="GET",headers={
        "Range":RANGE,"Accept-Encoding":"identity","Accept":"application/zip",
        "User-Agent":"OpenCatastrophe-BVV-OriginalSHX7MiB-ReadOnly/0.1",
    })
    try:
        with build_opener(
            ProxyHandler({}),NoRedirect(),HTTPSHandler(context=ssl.create_default_context())
        ).open(req,timeout=45) as res:
            if res.status != 206:
                raise SHXBlocked("original provider did not honour SHX Range")
            raw=res.read(READ_BYTES+1)
            result=inspect_original_shx(raw,status=res.status,
                                        response_url=res.geturl(),headers=res.headers)
    except (HTTPError, URLError, TimeoutError, OSError) as exc:
        raise SHXBlocked("bounded original SHX file read unavailable") from exc
    result["retrieved_at_utc"]=datetime.now(timezone.utc).isoformat()
    result["reviewed_script_sha256"]=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    return result


def main(argv=None):
    import argparse
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--live",action="store_true")
    args=p.parse_args(argv)
    if not args.live:
        p.error("original SHX network read is explicit trusted-main-only opt-in")
    try:
        print(json.dumps(probe(),sort_keys=True,allow_nan=False))
        return 0
    except SHXBlocked:
        print("BLOCKED: original Bavarian SHX member consistency unavailable",file=sys.stderr)
        return 2


if __name__=="__main__":
    raise SystemExit(main())
