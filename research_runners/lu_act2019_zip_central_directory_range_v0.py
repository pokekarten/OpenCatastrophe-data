#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Read only bounded ZIP directory metadata of three ACT LiDAR2019 point-cloud archives.

Original ACT index SHA-256 and exact two 100m public sites already verified on main.
Fetches HEAD + up to two carefully bounded HTTP 206 byte ranges for each ZIP.
Never reads entry data, stores ZIPs, logs original member names/URLs, or claims
a validated LAZ point, raw 2019 observation, independent VDL truth or CAT admission.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import re
import struct
from urllib.error import HTTPError, URLError
from urllib.request import Request, build_opener

from research_runners.lu_act2019_original_lidar_tile_index_v0 import (
    _reject_constant, _unique_pairs, verify_original, OriginalIndexError,
)
from research_runners.lu_act2019_three_tile_http_preflight_v0 import (
    build_site_windows, select_site_urls, RejectRedirects, validate_response_origin,
    decode_total_length, TIMEOUT_SECONDS, EXPECTED_TOTAL_SITES, TileProbeError,
)

MAX_ZIP_BYTES = 1_500_000_000
# EOCD record is 22 bytes; an optional ZIP comment is at most 65535 bytes.
MAX_EOCD_TAIL_BYTES = 65_557
MAX_CENTRAL_DIRECTORY_BYTES = 1_048_576
MAX_ENTRIES = 2_048
ZIP_EOCD_SIG = 0x06054B50
ZIP_CENTRAL_SIG = 0x02014B50
ZIP_EOCD_SIZE = 22
ZIP_CENTRAL_FIXED = 46
RANGE_DATA_LIMIT_PER_ZIP = MAX_EOCD_TAIL_BYTES + MAX_CENTRAL_DIRECTORY_BYTES
RANGE_RX = re.compile(r"^bytes ([0-9]+)-([0-9]+)/([0-9]+)$")

# Real official-provider ZIP central-directory receipts observed in successful
# GitHub Actions 41988484850. They identify only directory METADATA, never
# actual archive contents or original LAZ point data.
PINNED_DIRECTORY_RECEIPTS = {
    "luxembourg-city": [
        (449275061, "a7d96dc5a21b578e617d359f0b793e85db67de028164677ee22c39c5f472bf58"),
    ],
    "berdorf-village": [
        (410361626, "7bc9e106577a4ef7c81fc30572f8d280118c47ffe79425d5360bb2329d69ddf1"),
        (374704804, "3b7ce099b4918321030d92710dd917b873e62104903f69ab5a69608c4d4addd6"),
    ],
}

class DirectoryAuditError(ValueError):
    """Only fixed source-authored stage messages can enter public logs."""


def _bounded_http_get_range(url, *, start: int, end: int, total: int, opener):
    """Uncompressed HTTP body must be EXACTLY the declared tiny range."""
    if not (0 <= start <= end < total <= MAX_ZIP_BYTES
            and end - start + 1 <= MAX_CENTRAL_DIRECTORY_BYTES):
        raise DirectoryAuditError("Range request exceeded fixed metadata budget")
    req = Request(url, method="GET", headers={
        "Range": f"bytes={start}-{end}", "Accept-Encoding": "identity",
    })
    expected = end - start + 1
    try:
        with opener.open(req, timeout=TIMEOUT_SECONDS) as response:
            validate_response_origin(response, url)
            if response.status != 206:
                raise DirectoryAuditError("Original source did not honor exact byte range")
            header = response.headers.get("Content-Range", "")
            match = RANGE_RX.fullmatch(header.strip())
            if not match or tuple(map(int, match.groups())) != (start,end,total):
                raise DirectoryAuditError("Original source Content-Range mismatch")
            if response.headers.get("Content-Encoding", "identity").lower() != "identity":
                raise DirectoryAuditError("Unexpected compressed HTTP response body")
            data = response.read(expected + 1)
            if len(data) != expected:
                raise DirectoryAuditError("Original source range response length mismatch")
            return data
    except (HTTPError, URLError, TimeoutError, OSError, TileProbeError) as exc:
        raise DirectoryAuditError("Source original ZIP range read not verified") from exc


def _parse_eocd(tail: bytes, *, total: int, tail_start: int):
    if not isinstance(tail,bytes) or len(tail) != total - tail_start:
        raise DirectoryAuditError("Original source tail byte interval mismatch")
    for pos in range(len(tail)-ZIP_EOCD_SIZE, -1, -1):
        if tail[pos:pos+4] != b"PK\x05\x06":
            continue
        if pos + ZIP_EOCD_SIZE > len(tail):
            continue
        fields = struct.unpack_from("<IHHHHIIH",tail,pos)
        _,disk,central_disk,disk_entries,entries,cd_len,cd_off,comment_len = fields
        if pos + ZIP_EOCD_SIZE + comment_len != len(tail):
            continue
        if (disk != 0 or central_disk != 0 or disk_entries != entries
                or entries < 1 or entries > MAX_ENTRIES
                or cd_len < ZIP_CENTRAL_FIXED
                or cd_len > MAX_CENTRAL_DIRECTORY_BYTES
                or cd_off == 0xFFFFFFFF or cd_len == 0xFFFFFFFF
                or entries == 0xFFFF):
            raise DirectoryAuditError("Multipart ZIP/ZIP64/size outside audited contract")
        # Strict classic one-disk ZIP: central directory immediately before EOCD.
        if cd_off + cd_len != tail_start + pos or cd_off < 0:
            raise DirectoryAuditError("Original central-directory offset mismatch")
        return {"entries":entries,"cd_start":cd_off,"cd_bytes":cd_len,
                "eocd_offset":tail_start+pos}
    raise DirectoryAuditError("Original classic ZIP EOCD record not established")


def _entry_kind(filename: bytes) -> str:
    if (not filename or len(filename)>512 or b"\x00" in filename
            or b"\\" in filename or filename.startswith(b"/")
            or b".." in filename.split(b"/")):
        raise DirectoryAuditError("Unsupported original ZIP member path")
    name=filename.lower()
    if name.endswith(b"/"):
        return "directory"
    if name.endswith(b".laz"):
        return "laz"
    if name.endswith(b".las"):
        return "las"
    if name.endswith(b".lax"):
        return "lax"
    if name.endswith(b".txt"):
        return "txt"
    if name.endswith(b".xml"):
        return "xml"
    return "other"


def _parse_central_directory(body: bytes, *, entries_expected: int) -> dict:
    if (not isinstance(body, bytes) or not body or len(body)>MAX_CENTRAL_DIRECTORY_BYTES
            or not 1<=entries_expected<=MAX_ENTRIES):
        raise DirectoryAuditError("Unbounded central directory input")
    offset=0
    counts=Counter()
    methods=Counter()
    compressed_total=0
    uncompressed_total=0
    encrypted=0
    for _ in range(entries_expected):
        if offset+ZIP_CENTRAL_FIXED>len(body):
            raise DirectoryAuditError("Truncated central directory member")
        h=struct.unpack_from("<IHHHHHHIIIHHHHHII",body,offset)
        (signature,version_made,version_needed,flags,method,mtime,mdate,
         crc32,compressed,uncompressed,filename_len,extra_len,comment_len,
         disk_start,internal_attr,external_attr,local_offset)=h
        if signature!=ZIP_CENTRAL_SIG:
            raise DirectoryAuditError("Bad original ZIP directory signature")
        total_len=ZIP_CENTRAL_FIXED+filename_len+extra_len+comment_len
        if total_len>MAX_CENTRAL_DIRECTORY_BYTES or offset+total_len>len(body):
            raise DirectoryAuditError("Oversized ZIP central entry")
        if (disk_start!=0 or compressed==0xFFFFFFFF or uncompressed==0xFFFFFFFF
                or local_offset==0xFFFFFFFF or version_needed>63):
            raise DirectoryAuditError("ZIP64 or multipart member requires separate review")
        if flags&0x1:
            encrypted+=1
        name=body[offset+ZIP_CENTRAL_FIXED:offset+ZIP_CENTRAL_FIXED+filename_len]
        counts[_entry_kind(name)]+=1
        methods[str(method)]+=1
        compressed_total+=compressed
        uncompressed_total+=uncompressed
        offset+=total_len
    if offset!=len(body):
        raise DirectoryAuditError("Trailing or hidden central-directory data")
    if encrypted:
        raise DirectoryAuditError("Encrypted original point-cloud archive member")
    return {
        "entry_count":entries_expected,
        "entry_type_counts":dict(sorted(counts.items())),
        "compression_method_codes":dict(sorted(methods.items())),
        "reported_total_compressed_member_bytes":compressed_total,
        "reported_total_uncompressed_member_bytes":uncompressed_total,
        "central_directory_sha256_not_full_archive":hashlib.sha256(body).hexdigest(),
        "zip64_or_multi_disk_not_seen":True,
        "member_names_or_source_identifiers_logged":False,
        "member_payload_bytes_read":False,
        "full_original_zip_sha256_verified":False,
        "actual_las_laz_headers_inspected":False,
        "building_class_six_points_inspected":False,
    }


def probe_one_zip(url, *, opener=None) -> dict:
    """Return aggregate inspected central-directory fields or an explicit block."""
    from research_runners.lu_act2019_original_lidar_tile_index_v0 import _validate_asset_url
    _validate_asset_url(url)
    if opener is None:
        opener=build_opener(RejectRedirects())
    head=Request(url,method="HEAD",headers={"Accept-Encoding":"identity"})
    try:
        with opener.open(head,timeout=TIMEOUT_SECONDS) as response:
            validate_response_origin(response,url)
            if response.status!=200:
                raise DirectoryAuditError("Original ZIP HEAD not accepted")
            total=decode_total_length(response.headers.get("Content-Length"))
    except (HTTPError,URLError,TimeoutError,OSError,TileProbeError) as exc:
        raise DirectoryAuditError("Original ZIP HEAD not available") from exc
    if total is None:
        raise DirectoryAuditError("Remote source size unavailable or exceeds limit")
    start=max(0,total-MAX_EOCD_TAIL_BYTES)
    tail=_bounded_http_get_range(url,start=start,end=total-1,total=total,opener=opener)
    eocd=_parse_eocd(tail,total=total,tail_start=start)
    cd_start=eocd["cd_start"]
    cd_end=cd_start+eocd["cd_bytes"]
    if cd_start>=start and cd_end<=total:
        body=tail[cd_start-start:cd_end-start]
        range_gets=1
        bytes_received=len(tail)
    else:
        body=_bounded_http_get_range(url,start=cd_start,end=cd_end-1,
                                     total=total,opener=opener)
        range_gets=2
        bytes_received=len(tail)+len(body)
    out=_parse_central_directory(body,entries_expected=eocd["entries"])
    return {
        "http_provider_reported_zip_bytes":total,
        "zip_metadata_exact_range_get_count":range_gets,
        "zip_metadata_total_range_response_bytes":bytes_received,
        "http_range_receipts_verified":True,
        **out,
    }


def verify_directory_metadata_receipts(site_reports: dict) -> None:
    """Pin real HTTP-reported size + directory bytes fingerprint, NOT full ZIP."""
    if not isinstance(site_reports,dict) or set(site_reports)!=set(PINNED_DIRECTORY_RECEIPTS):
        raise DirectoryAuditError("Original archive site receipt population drifted")
    for site,entries in site_reports.items():
        pinned=PINNED_DIRECTORY_RECEIPTS[site]
        if len(entries)!=len(pinned):
            raise DirectoryAuditError("Original archive directory count drifted")
        for item,(size,directory_hash) in zip(entries,pinned,strict=True):
            if (item.get("http_provider_reported_zip_bytes") != size
                    or item.get("central_directory_sha256_not_full_archive") != directory_hash
                    or item.get("entry_count") != 9
                    or item.get("entry_type_counts") != {"laz":9}
                    or item.get("compression_method_codes") != {"8":9}
                    or item.get("zip_metadata_exact_range_get_count") != 1):
                raise DirectoryAuditError("Pinned original ZIP directory metadata drifted")


def run(index_path: Path, *, opener=None):
    original=verify_original(index_path)
    try:
        obj=json.loads(index_path.read_text(encoding="utf-8"),
                       object_pairs_hook=_unique_pairs,parse_constant=_reject_constant)
    except (ValueError, UnicodeError) as exc:
        raise DirectoryAuditError("Original index reparse failed") from exc
    targets=select_site_urls(obj,build_site_windows())
    if sum(len(x) for x in targets.values())!=EXPECTED_TOTAL_SITES:
        raise DirectoryAuditError("Expected exactly three selected source archives")
    result={s:[probe_one_zip(url,opener=opener) for url in urls]
            for s,urls in targets.items()}
    verify_directory_metadata_receipts(result)
    return {
        "profile":"lu-act2019-3-tile-zip-central-directory-range-only-v0",
        "source_index_original_sha256":original["original_index_sha256"],
        "source_original_tile_zip_count":EXPECTED_TOTAL_SITES,
        "sites":result,
        "full_tile_zip_bytes_acquired":False,
        "original_las_laz_point_counts_or_accuracy_validated":False,
        "scientific_independence_from_vdl_verified":False,
        "licence_review_completed":False,
        "insured_exposure_or_cat_input_admitted":False,
        "original_url_or_member_names_exported":False,
    }


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--original-index",required=True,type=Path)
    args=p.parse_args(argv)
    try:
        out=run(args.original_index)
    except (OriginalIndexError,TileProbeError,DirectoryAuditError,OSError,ValueError,TypeError):
        print("BLOCKED: strict original LiDAR2019 archive directory byte-range gate")
        return 2
    print(json.dumps(out,sort_keys=True,indent=2,allow_nan=False))
    return 0


if __name__=="__main__":
    raise SystemExit(main())
