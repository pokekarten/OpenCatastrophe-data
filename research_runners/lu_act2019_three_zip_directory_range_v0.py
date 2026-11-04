#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Bounded ZIP end-of-central-directory preflight for three verified ACT 2019 tiles.

The full original index is SHA-pinned; remote archives remain unacquired.
Read no more than 65,557 ZIP tail bytes + 262,144 central directory bytes per
tile, after earlier strict HEAD and four-byte ZIP signature checks.
No raw archive names, tile URLs, feature IDs, coordinates or point bytes logged.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import struct
from urllib.error import HTTPError, URLError
from urllib.request import Request, build_opener

from research_runners.lu_act2019_original_lidar_tile_index_v0 import (
    _unique_pairs, _reject_constant, OriginalIndexError, verify_original,
)
from research_runners.lu_act2019_three_tile_http_preflight_v0 import (
    TileProbeError, RejectRedirects, build_site_windows, probe_one,
    select_site_urls, validate_response_origin, TIMEOUT_SECONDS,
)

# These are only *HTTP-advertised* total byte lengths from original run 41903085731,
# NOT full archive checksums or verified 2019 LAS/LAZ contents.
ORIGINAL_SIZE_BY_SITE = {
    "luxembourg-city": (449275061,),
    "berdorf-village": (410361626, 374704804),
}
MAX_TAIL = 65_557  # 22-byte classic ZIP EOCD plus max 65535-byte comment
MAX_CENTRAL = 262_144
MAX_ENTRIES = 256
MAX_NAME = 1_024
EOCD_STRUCT = struct.Struct("<4s4H2IH")
CENTRAL_STRUCT = struct.Struct("<4s6H3I5H2I")
EXTENSIONS = ("laz", "las", "txt", "xml", "json", "prj", "other")
MAX_NETWORK_BYTES_PER_TILE = 4 + MAX_TAIL + MAX_CENTRAL + 1


class DirectoryError(ValueError):
    """Self-authored stage error; never contains unreviewed provider bytes."""


def safe_range(url: str, *, start: int, length: int, total: int, opener=None) -> bytes:
    """One exact HTTP206 range, no redirects and never an unbounded body read."""
    if (not all(type(v) is int for v in (start, length, total))
            or length < 1 or length > MAX_CENTRAL
            or start < 0 or total < 1 or start + length > total):
        raise DirectoryError("Range request exceeds reviewed byte window")
    if opener is None:
        opener = build_opener(RejectRedirects())
    end = start + length - 1
    req = Request(url, method="GET", headers={
        "Range": f"bytes={start}-{end}", "Accept-Encoding": "identity",
    })
    try:
        with opener.open(req, timeout=TIMEOUT_SECONDS) as response:
            validate_response_origin(response, url)
            if response.status != 206:
                raise DirectoryError("Original server did not honor exact byte range")
            if response.headers.get("Content-Range", "").strip() != f"bytes {start}-{end}/{total}":
                raise DirectoryError("Original Content-Range offset or total mismatch")
            encoding = response.headers.get("Content-Encoding", "identity").lower()
            if encoding != "identity":
                raise DirectoryError("Unexpected archive byte content encoding")
            advertised = response.headers.get("Content-Length")
            if advertised is not None and advertised != str(length):
                raise DirectoryError("Partial response content length differs")
            part = response.read(length + 1)
            if len(part) != length:
                raise DirectoryError("Truncated or oversized original byte-range response")
            return part
    except (HTTPError, URLError, TimeoutError, OSError, TileProbeError) as exc:
        raise DirectoryError("Original archive range not accessible") from exc


def locate_eocd(tail: bytes, *, tail_start: int, total: int) -> dict:
    """Accept only classic non-spanned, non-ZIP64 end-of-central-directory."""
    if not isinstance(tail, bytes) or not 22 <= len(tail) <= MAX_TAIL:
        raise DirectoryError("Invalid bounded ZIP tail")
    if tail_start < 0 or tail_start + len(tail) != total:
        raise DirectoryError("ZIP tail offset does not conserve original size")
    for pos in range(len(tail) - 22, -1, -1):
        if tail[pos:pos+4] != b"PK\x05\x06":
            continue
        (_signature, disk, directory_disk, disk_files, all_files,
         central_size, central_offset, comment_len) = EOCD_STRUCT.unpack_from(tail, pos)
        if pos + 22 + comment_len != len(tail):
            continue
        if disk != 0 or directory_disk != 0 or disk_files != all_files:
            raise DirectoryError("Spanned ZIP archive is unsupported")
        if (all_files in (0, 0xffff) or central_size in (0, 0xffffffff)
                or central_offset == 0xffffffff):
            raise DirectoryError("Empty or ZIP64 central directory requires new review")
        if all_files > MAX_ENTRIES or central_size > MAX_CENTRAL:
            raise DirectoryError("ZIP central directory exceeds bounded audit budget")
        absolute_eocd = tail_start + pos
        if central_offset + central_size != absolute_eocd:
            raise DirectoryError("ZIP central directory offset does not meet EOCD")
        return {"offset": central_offset, "size": central_size,
                "entries": all_files, "eocd_comment_bytes": comment_len}
    raise DirectoryError("No valid original classic ZIP end-of-directory record")


def summarize_central(directory: bytes, *, entries: int, archive_size: int,
                      directory_offset: int) -> dict:
    """Parse only fixed ZIP central headers; aggregate types without names."""
    if (not isinstance(directory, bytes) or len(directory) > MAX_CENTRAL
            or not 1 <= entries <= MAX_ENTRIES or directory_offset < 0):
        raise DirectoryError("Invalid central-directory parse bounds")
    counts = Counter({ext: 0 for ext in EXTENSIONS})
    methods = Counter()
    compressed_sum = 0
    uncompressed_sum = 0
    encrypted_count = 0
    directory_entries = 0
    pos = 0
    for _ in range(entries):
        if pos + CENTRAL_STRUCT.size > len(directory):
            raise DirectoryError("Truncated ZIP central file header")
        fields = CENTRAL_STRUCT.unpack_from(directory, pos)
        (signature, _made, _needed, flags, method, _time, _date,
         _crc, compressed, uncompressed, name_len, extra_len, comment_len,
         disk, _intattr, _extattr, local_offset) = fields
        if signature != b"PK\x01\x02":
            raise DirectoryError("Original central file signature invalid")
        body = name_len + extra_len + comment_len
        if (not 1 <= name_len <= MAX_NAME or body < 1
                or pos + CENTRAL_STRUCT.size + body > len(directory)):
            raise DirectoryError("ZIP file metadata length exceeds buffer")
        name = directory[pos + CENTRAL_STRUCT.size:pos + CENTRAL_STRUCT.size + name_len]
        # No extraction, but reject source archive name anomalies anyway.
        if (b"\x00" in name or name.startswith((b"/", b"\\"))
                or b"\\" in name or b".." in name.split(b"/") or
                any(c < 32 or c == 127 for c in name)):
            raise DirectoryError("Unreviewed ZIP member naming syntax")
        if (disk != 0 or compressed == 0xffffffff or
                uncompressed == 0xffffffff or local_offset == 0xffffffff):
            raise DirectoryError("ZIP64 or split-file member requires separate review")
        if local_offset >= directory_offset or compressed > archive_size:
            raise DirectoryError("Original ZIP member offsets/sizes out of bounds")
        if flags & 1:
            encrypted_count += 1
        if name.endswith(b"/"):
            directory_entries += 1
        else:
            last = name.rsplit(b"/", 1)[-1].lower()
            ext = last.rsplit(b".", 1)[-1] if b"." in last else b""
            label = ext.decode("ascii") if ext in (
                b"laz", b"las", b"txt", b"xml", b"json", b"prj") else "other"
            counts[label] += 1
        methods[str(method)] += 1
        compressed_sum += compressed
        uncompressed_sum += uncompressed
        pos += CENTRAL_STRUCT.size + body
    if pos != len(directory) or sum(counts.values()) + directory_entries != entries:
        raise DirectoryError("ZIP central entry population not conserved")
    return {
        "central_member_total": entries,
        "member_extension_counts": {ext: counts[ext] for ext in EXTENSIONS},
        "directory_records": directory_entries,
        "zip_method_code_counts": dict(sorted(methods.items())),
        "encrypted_flag_count": encrypted_count,
        "central_compressed_bytes_reported": compressed_sum,
        "central_uncompressed_bytes_reported": uncompressed_sum,
        "central_directory_sha256_partial_metadata_only": hashlib.sha256(directory).hexdigest(),
        "zip_directory_metadata_verified_not_payload": True,
        "original_zip_full_sha256_verified": False,
        "archive_members_extracted_or_read": False,
        "actual_laz_or_las_points_verified": False,
    }


def inspect_one_zip(url: str, *, expected_size: int, opener=None) -> dict:
    """Only HEAD/4-byte probe plus ZIP tail and bounded central-dir bytes."""
    if opener is None:
        opener = build_opener(RejectRedirects())
    prior = probe_one(url, opener=opener)
    if (prior["head_http"] != 200 or prior["range_http"] != 206
            or not prior["range_206_supported"]
            or not prior["range_full_size_matches_head"]
            or not prior["first_four_bytes_zip_local_header"]
            or prior["head_content_length_bytes"] != expected_size):
        raise DirectoryError("Pinned original archive HEAD/ZIP signature drifted")
    tail_size = min(MAX_TAIL, expected_size)
    tail_start = expected_size - tail_size
    tail = safe_range(url, start=tail_start, length=tail_size,
                      total=expected_size, opener=opener)
    info = locate_eocd(tail, tail_start=tail_start, total=expected_size)
    start, length = info["offset"], info["size"]
    if start >= tail_start and start + length <= expected_size:
        directory = tail[start-tail_start:start-tail_start+length]
    else:
        directory = safe_range(url, start=start, length=length,
                               total=expected_size, opener=opener)
    report = summarize_central(directory, entries=info["entries"],
                               archive_size=expected_size, directory_offset=start)
    return {
        "original_archive_head_length_bytes": expected_size,
        "zip_eocd_comment_bytes": info["eocd_comment_bytes"],
        "zip_central_directory_offset": start,
        "zip_central_directory_length": length,
        **report,
        "max_requested_response_bytes": MAX_NETWORK_BYTES_PER_TILE,
        "complete_original_zip_archive_downloaded": False,
        "independent_building_identity_proven": False,
        "cat_exposure_model_input_admitted": False,
    }


def run(index: Path, *, opener=None) -> dict:
    receipt = verify_original(index)
    try:
        source = json.loads(index.read_text(encoding="utf-8"),
                            object_pairs_hook=_unique_pairs,
                            parse_constant=_reject_constant)
    except (ValueError, UnicodeError) as exc:
        raise DirectoryError("Exact source index could not be reloaded") from exc
    urls = select_site_urls(source, build_site_windows())
    results = {}
    for site, expected_sizes in ORIGINAL_SIZE_BY_SITE.items():
        selected = urls[site]
        if len(selected) != len(expected_sizes):
            raise DirectoryError("Original pinned site count changed")
        results[site] = {
            "original_index_tiles": len(selected),
            "ordered_archive_central_directory": [
                inspect_one_zip(url, expected_size=size, opener=opener)
                for url, size in zip(selected, expected_sizes, strict=True)
            ],
        }
    return {
        "profile": "lu-act2019-three-zip-range-central-directory-v0",
        "original_index_sha256": receipt["original_index_sha256"],
        "selected_original_archives": 3,
        "sites": results,
        "archive_bytes_downloaded": False,
        "full_original_archives_sha256_verified": False,
        "point_cloud_class6_points_inspected": False,
        "independent_2019_versus_2026_building_truth_proven": False,
        "reuse_rights_review_completed": False,
        "cat_model_input_admitted": False,
        "raw_zip_member_names_or_tile_urls_logged": False,
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--original-index", required=True, type=Path)
    args = parser.parse_args(argv)
    try:
        result = run(args.original_index)
    except DirectoryError as exc:
        # All self-authored fixed stage labels only; no original source values.
        print("BLOCKED: reviewed ZIP source stage: " + str(exc))
        return 2
    except (OriginalIndexError, TileProbeError, OSError, ValueError, TypeError,
            struct.error):
        print("BLOCKED: original ZIP range / fixed study-area contract failed")
        return 2
    print(json.dumps(result, indent=2, sort_keys=True, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
