#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Bounded original public BVV Oberbayern ZIP .dbf member and record-count proof.

Download ONLY the first local ZIP entry (45-byte header and 275557 compressed
bytes), via strict original HTTP 206. Decompress at most 27037426 bytes, verify
the original directory CRC32, dBase header/field/row flags and compare the DBF
row count to the SHX *directory-reported* index length. Original DBF bytes,
identifier values, SHP/SHX geometry and address data are never emitted or
persisted. DBF header date is a file-modification hint, NOT survey vintage.
"""
from __future__ import annotations

from datetime import date, datetime, timezone
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
    URL, SOURCE, NoRedirect, PrefixBlocked,
)
from research_runners.by_hausumringe_oberbayern_zip_central_v0 import TOTAL, FROZEN

NAME = b"hausumringe.dbf"
START = 0
HEADER_BYTES = 30 + len(NAME)
COMPRESSED_BYTES = 275_557
UNCOMPRESSED_BYTES = 27_037_425
MAX_READ = HEADER_BYTES + COMPRESSED_BYTES
END = MAX_READ - 1
RANGE = f"bytes=0-{END}"
ORIGINAL_CRC32 = 0x67324194
EXPECTED_SHX_RECORDS_FROM_DIRECTORY = (FROZEN["hausumringe.shx"][2] - 100) // 8
EXPECTED_DBF_RECORDS = 2_703_736
EXPECTED_HEADER_LENGTH = 65
EXPECTED_RECORD_LENGTH = 10


class DBFBlocked(PrefixBlocked):
    """Provider original, ZIP integrity, table shape or feature count changed."""


def inspect_original_dbf(raw: bytes, *, status: int, response_url: str,
                         headers) -> dict:
    if type(raw) is not bytes or len(raw) != MAX_READ:
        raise DBFBlocked("one exact 275602-byte original compressed DBF member required")
    if status != 206 or response_url != URL:
        raise DBFBlocked("fixed first-party ZIP URL and HTTP 206 are mandatory")
    if headers.get("Content-Range", "") != f"bytes 0-{END}/{TOTAL}":
        raise DBFBlocked("DBF original Range or total archive byte identity drift")
    if headers.get("Content-Length") not in (None, str(MAX_READ)):
        raise DBFBlocked("provider ignored requested exact DBF byte count")
    if headers.get("Content-Encoding", "identity").lower() != "identity":
        raise DBFBlocked("HTTP transport changed original DBF compressed bytes")
    if headers.get("Content-Type", "").split(";", 1)[0].strip().lower() not in (
        "application/zip", "application/octet-stream", "binary/octet-stream",
    ):
        raise DBFBlocked("original provider content is not a ZIP")
    if raw[:4] != b"PK\x03\x04":
        raise DBFBlocked("original DBF ZIP local header missing")
    (version, flags, method, mtime, mdate, crc, zipped,
     inflated, filename_len, extra_len) = struct.unpack_from(
        "<HHHHHIIIHH", raw, 4
    )
    if (version, flags, method, crc, zipped, inflated, filename_len, extra_len) != (
        20, 0, 8, ORIGINAL_CRC32, COMPRESSED_BYTES, UNCOMPRESSED_BYTES,
        len(NAME), 0,
    ):
        raise DBFBlocked("first original DBF local ZIP header mismatches directory")
    if raw[30:HEADER_BYTES] != NAME or MAX_READ != FROZEN["hausumringe.prj"][0]:
        raise DBFBlocked("original ZIP member boundaries/identity drift")
    compressed = raw[HEADER_BYTES:]
    compressed_sha = hashlib.sha256(compressed).hexdigest()
    try:
        decoder = zlib.decompressobj(wbits=-15)
        body = decoder.decompress(compressed, UNCOMPRESSED_BYTES + 1)
        if len(body) != UNCOMPRESSED_BYTES or decoder.unconsumed_tail:
            raise DBFBlocked("original DBF output exceeds declared source size")
        tail = decoder.flush()
    except zlib.error as exc:
        raise DBFBlocked("original compressed DBF deflate corrupted") from exc
    if (tail or not decoder.eof or decoder.unused_data or decoder.unconsumed_tail
            or len(body) != UNCOMPRESSED_BYTES):
        raise DBFBlocked("truncated or appended compressed DBF member")
    if zlib.crc32(body) != ORIGINAL_CRC32:
        raise DBFBlocked("original DBF CRC32 mismatches independent ZIP directory")
    if EXPECTED_SHX_RECORDS_FROM_DIRECTORY != EXPECTED_DBF_RECORDS:
        raise DBFBlocked("original uncompressed SHX size not consistent with DBF")
    if len(body) < EXPECTED_HEADER_LENGTH or body[0] != 0x03:
        raise DBFBlocked("not the reviewed dBase III DBF table type")
    yy, mm, dd = body[1:4]
    try:
        source_header_update = date(1900 + yy, mm, dd)
    except ValueError as exc:
        raise DBFBlocked("DBF header file update date invalid") from exc
    count, head_len, record_len = struct.unpack_from("<IHH", body, 4)
    if (count, head_len, record_len) != (
        EXPECTED_DBF_RECORDS, EXPECTED_HEADER_LENGTH, EXPECTED_RECORD_LENGTH
    ):
        raise DBFBlocked("original DBF row/header/record length changed")
    if head_len + count * record_len != len(body) or body[64] != 0x0D:
        raise DBFBlocked("DBF table content/field terminator length mismatch")
    field = body[32:64]
    label = field[:11].split(b"\x00", 1)[0]
    if (not label or len(label) > 11 or any(
        not (65 <= x <= 90 or 97 <= x <= 122 or 48 <= x <= 57 or x == 95)
        for x in label
    )):
        raise DBFBlocked("unexpected field name format")
    if field[11] not in (ord("C"), ord("N")) or field[16] != 9 or field[17] != 0:
        raise DBFBlocked("unexpected original DBF one-field character schema")
    # The dBase record's first byte is the delete marker. Do not export IDs.
    flags = body[head_len::record_len]
    active = flags.count(0x20)
    deleted = flags.count(0x2A)
    if len(flags) != count or active + deleted != count:
        raise DBFBlocked("unexpected deleted/active flags in original DBF records")
    return {
        "profile": "oc-bvv-oberbayern-original-full-compressed-dbf-only-v0",
        "source_id": SOURCE,
        "original_public_zip_url": URL,
        "source_zip_total_bytes": TOTAL,
        "original_zip_local_member": NAME.decode("ascii"),
        "original_exact_byte_range": RANGE,
        "zip_member_original_read_bytes": MAX_READ,
        "dbf_original_compressed_bytes": COMPRESSED_BYTES,
        "dbf_original_uncompressed_bytes": UNCOMPRESSED_BYTES,
        "dbf_original_compressed_sha256": compressed_sha,
        "dbf_original_uncompressed_sha256": hashlib.sha256(body).hexdigest(),
        "dbf_original_crc32_verified": f"{ORIGINAL_CRC32:08x}",
        "dbf_original_header_version": "dBase III",
        "dbf_original_header_update_date_file_metadata_only": source_header_update.isoformat(),
        "dbf_survey_vintage_verified": False,
        "dbf_original_record_count_verified": count,
        "shx_record_count_inferred_from_directory_only": EXPECTED_SHX_RECORDS_FROM_DIRECTORY,
        "dbf_original_active_records": active,
        "dbf_original_deleted_records": deleted,
        "dbf_attribute_field_count": 1,
        "dbf_attribute_value_bytes_per_record": 9,
        "shx_original_bytes_independently_downloaded": False,
        "shp_original_polygons_downloaded": False,
        "official_complete_region_geometry_verified": False,
        "raw_identifiers_or_attributes_emitted": False,
        "original_provider_bytes_persisted": False,
        "full_original_zip_sha256_verified": False,
        "model_input_approved": False,
    }


def probe() -> dict:
    req = Request(URL, method="GET", headers={
        "Range": RANGE, "Accept-Encoding": "identity", "Accept": "application/zip",
        "User-Agent": "OpenCatastrophe-BVV-DBF-Member275KiB-ReadOnly/0.1",
    })
    try:
        with build_opener(ProxyHandler({}), NoRedirect(),
                          HTTPSHandler(context=ssl.create_default_context())
                          ).open(req, timeout=25) as res:
            if res.status != 206:
                raise DBFBlocked("server ignored original DBF exact Range")
            original_bytes = res.read(MAX_READ + 1)
            receipt = inspect_original_dbf(
                original_bytes, status=res.status, response_url=res.geturl(),
                headers=res.headers,
            )
    except (HTTPError, URLError, TimeoutError, OSError) as exc:
        raise DBFBlocked("bounded original DBF member unavailable") from exc
    receipt["retrieved_at_utc"] = datetime.now(timezone.utc).isoformat()
    receipt["code_sha256"] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    return receipt


def main(argv=None) -> int:
    import argparse
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--live", action="store_true")
    args = p.parse_args(argv)
    if not args.live:
        p.error("original compressed DBF source read requires explicit opt-in")
    try:
        print(json.dumps(probe(), sort_keys=True, allow_nan=False))
        return 0
    except DBFBlocked:
        print("BLOCKED: original compressed BVV DBF source/row count failed closed",
              file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
