#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""One fixed 4KiB ZIP *suffix* read: central directory, not building geometries.

The original 174,299,765-byte official BVV Oberbayern ZIP and its central
directory offsets were individually observed in bounded public HTTP Ranges.
Verify exact bytes/transport/ZIP structures before any full asset acquisition.
Never download source members, decompress archives or infer survey vintage.
Run live only from reviewed main/explicitly dispatched trusted GitHub code.
"""
from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import ssl
import struct
import sys
from urllib.error import HTTPError, URLError
from urllib.request import Request, ProxyHandler, HTTPSHandler, build_opener

from research_runners.by_hausumringe_oberbayern_zip_prefix_v0 import (
    URL, INDEX, SOURCE, PrefixBlocked, NoRedirect,
)

TOTAL = 174_299_765
LIMIT = 4096
START = TOTAL - LIMIT
END = TOTAL - 1
RANGE = f"bytes={START}-{END}"
CENTRAL_START = 174_299_355
CENTRAL_SIZE = 388
# These are first-party ZIP *directory claims*, not verified uncompressed files.
FROZEN = {
    "hausumringe.dbf": (0, 275_557, 27_037_425),
    "hausumringe.prj": (275_602, 256, 388),
    "hausumringe.shp": (275_903, 166_172_236, 501_212_696),
    "hausumringe.shx": (166_448_184, 7_851_126, 21_629_988),
}


class CentralBlocked(PrefixBlocked):
    """Source identity, ZIP consistency or bounded transport failure."""


def _u16(data: bytes, i: int) -> int:
    return struct.unpack_from("<H", data, i)[0]


def _u32(data: bytes, i: int) -> int:
    return struct.unpack_from("<I", data, i)[0]


def inspect_suffix(raw: bytes, *, status: int, response_url: str, headers) -> dict:
    if type(raw) is not bytes or len(raw) != LIMIT:
        raise CentralBlocked("exactly four KiB of original ZIP suffix are required")
    if status != 206 or response_url != URL:
        raise CentralBlocked("original public ZIP Range must be HTTP 206 without redirect")
    if headers.get("Content-Range", "") != f"bytes {START}-{END}/{TOTAL}":
        raise CentralBlocked("wrong original source length/Range identity")
    if headers.get("Content-Length") not in (None, str(LIMIT)):
        raise CentralBlocked("wrong exact suffix Content-Length")
    if headers.get("Content-Encoding", "identity").lower() != "identity":
        raise CentralBlocked("ZIP bytes cannot be HTTP compressed")
    if headers.get("Content-Type", "").split(";", 1)[0].strip().lower() not in (
        "application/zip", "application/octet-stream", "binary/octet-stream"
    ):
        raise CentralBlocked("provider returned non-ZIP MIME")

    # EOCD must be exactly at the end: 22-byte fixed record, no ZIP comment
    # and no multi-disk, ZIP64, appended data or unreviewed central directory.
    tail = LIMIT - 22
    if raw[tail:tail+4] != b"PK\x05\x06":
        raise CentralBlocked("ZIP EOCD not at the reviewed original byte offset")
    disk, cd_disk, disk_entries, entries, size, offset, comment = (
        struct.unpack_from("<HHHHIIH", raw, tail+4)
    )
    if (disk, cd_disk, disk_entries, entries, size, offset, comment) != (
        0, 0, 4, 4, CENTRAL_SIZE, CENTRAL_START, 0
    ):
        raise CentralBlocked("ZIP central directory size, offset or cardinailty drift")
    pos = CENTRAL_START - START
    if pos < 0 or pos + CENTRAL_SIZE != tail:
        raise CentralBlocked("ZIP directory does not fit exact bounded suffix")

    records = []
    for _ in range(4):
        if pos + 46 > tail or raw[pos:pos+4] != b"PK\x01\x02":
            raise CentralBlocked("ZIP central directory truncated or wrong signature")
        (creator, needed, flags, method, dos_time, dos_date,
         crc, compressed, inflated, name_len, extra_len,
         comment_len, diskstart, int_attrs, ext_attrs, local_offset) = (
            struct.unpack_from("<HHHHHHIIIHHHHHII", raw, pos+4)
        )
        if (needed > 20 or flags != 0 or method != 8 or diskstart != 0
                or name_len != 15 or extra_len != 0 or comment_len != 0
                or compressed <= 0 or inflated <= 0):
            raise CentralBlocked("ZIP encryption, ZIP64 or unexpected member encoding")
        finish = pos+46+name_len
        if finish > tail:
            raise CentralBlocked("ZIP file name outside fixed suffix")
        try:
            name = raw[pos+46:finish].decode("ascii")
        except UnicodeDecodeError as exc:
            raise CentralBlocked("ZIP file member not original ASCII") from exc
        if name not in FROZEN or (local_offset, compressed, inflated) != FROZEN[name]:
            raise CentralBlocked("original Shapefile member name, length or offset drift")
        records.append({
            "name": name,
            "compression": "deflate",
            "directory_claim_compressed_bytes": compressed,
            "directory_claim_uncompressed_bytes": inflated,
            "directory_claim_local_header_offset": local_offset,
            "directory_crc32_claim": f"{crc:08x}",
        })
        pos = finish
    if pos != tail or set(x["name"] for x in records) != set(FROZEN):
        raise CentralBlocked("four expected original Shapefile members not exhausted")
    ordered = sorted(records, key=lambda x:x["directory_claim_local_header_offset"])
    for i, record in enumerate(ordered):
        next_start = (ordered[i+1]["directory_claim_local_header_offset"]
                      if i+1 < 4 else CENTRAL_START)
        expected = record["directory_claim_local_header_offset"] + 30 + 15 + record["directory_claim_compressed_bytes"]
        if next_start != expected:
            raise CentralBlocked("ZIP source member offsets not contiguous")

    return {
        "profile": "oc-bvv-oberbayern-original-zip-4k-central-directory-t1-v0",
        "source_id": SOURCE,
        "official_original_public_zip_url": URL,
        "original_public_index": INDEX,
        "http_status": status,
        "exact_source_bytes_total_transport": TOTAL,
        "checked_original_range": RANGE,
        "response_bytes": LIMIT,
        "original_suffix_sha256": hashlib.sha256(raw).hexdigest(),
        "central_directory_offset": CENTRAL_START,
        "central_directory_bytes": CENTRAL_SIZE,
        "original_expected_members": records,
        "archive_entries_original_directory_claim_only": True,
        "original_member_crc32_verified_against_full_bytes": False,
        "complete_archive_sha256_verified": False,
        "original_prj_epsg_verified": False,
        "original_shp_geometries_retrieved": False,
        "source_observation_date_verified": False,
        "source_bytes_persisted": False,
        "model_input_approved": False,
    }


def probe() -> dict:
    req = Request(URL, method="GET", headers={
        "Range": RANGE,
        "Accept-Encoding": "identity",
        "Accept": "application/zip",
        "User-Agent": "OpenCatastrophe-BVV-ZIP-Central4KiB-ReadOnly/0.1",
    })
    try:
        with build_opener(
            ProxyHandler({}), NoRedirect(),
            HTTPSHandler(context=ssl.create_default_context()),
        ).open(req, timeout=25) as res:
            if res.status != 206:
                raise CentralBlocked("server ignored exact ZIP suffix Range")
            data = res.read(LIMIT+1)
            receipt = inspect_suffix(data, status=res.status,
                                     response_url=res.geturl(), headers=res.headers)
    except (HTTPError, URLError, TimeoutError, OSError) as exc:
        raise CentralBlocked("bounded original ZIP central directory unavailable") from exc
    receipt["retrieved_at_utc"] = datetime.now(timezone.utc).isoformat()
    receipt["code_sha256"] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    return receipt


def main(argv=None) -> int:
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--live", action="store_true")
    args = parser.parse_args(argv)
    if not args.live:
        parser.error("original source network probe is explicit opt-in")
    try:
        print(json.dumps(probe(), sort_keys=True))
        return 0
    except CentralBlocked:
        print("BLOCKED: original BVV ZIP central directory identity unavailable",
              file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
