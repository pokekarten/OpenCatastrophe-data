#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Exact official Berdorf 2024 COPC-group ZIP central directories via HTTP206.

Reuses the already published fail-closed city ZIP-range parser, reading *only*
two fixed Berdorf group sources, 65,557-byte tail and <=262,144 byte directory
from each, never the actual 1.7GB archives or LAZ payloads. No member paths
or coordinates are printed. Fixed public village sites only.
"""
from __future__ import annotations
import argparse
import json
import re
import struct
from urllib.error import HTTPError, URLError
from urllib.request import build_opener
from research_runners.luxembourg_lidar2024_copc_group_resource_head_v0 import (
    OFFICIAL_API, RESOURCES, _only_publisher_url, _source_digest_from_metadata,
    ArchiveReceiptError, NoRedirect,
)
from research_runners.luxembourg_lidar2024_city_copc_zip_directory_range_v0 import (
    ZIP_TAIL_BYTES, ZipRangeError, parse_eocd, parse_directory, read_http, _request,
)

# Original JSON+HEAD full-size and reported SHA1 receipts: merged #987.
# Original exact-area tile candidates: merged #975.
SOURCES = {
    "berdorf-south": {
        "size": 1701393927,
        "sha1": "45d154470b4a06f99f569b6294a2773bab504ec9",
        "tiles": ("92500_98500", "93000_98500"),
    },
    "berdorf-north": {
        "size": 1736263124,
        "sha1": "773f6a2375e03d821149addcc5717903e54166f1",
        "tiles": ("92500_99000", "93000_99000"),
    },
}
MAX_METADATA_BYTES = 262144

class BerdorfZipError(ValueError):
    """Reject source provenance drift and unbounded/ambiguous ZIP metadata."""


def count_fixed_tiles(directory: bytes, *, members: int, tiles: tuple[str, str]) -> dict:
    """Count exact predeclared tiles after canonical ZIP parser validates all rows.

    Do not log internal names or ZIP entry offsets. Names need not end in
    .copc.laz; a .laz suffix alone does not prove COPC compatibility.
    """
    result = parse_directory(directory, count=members)
    if result["declared_original_zip_member_count"] != members:
        raise BerdorfZipError("Original source directory count drift")
    pos = 0
    seen = {tile: 0 for tile in tiles}
    for _ in range(members):
        # Structural and path/encryption/ZIP64 safety has already been
        # verified by the canonical parser on this exact byte buffer.
        parts = struct.unpack_from("<IHHHHHHIIIHHHHHII", directory, pos)
        flag, name_len, extra_len, comment_len = parts[3], parts[10], parts[11], parts[12]
        path = directory[pos + 46:pos + 46 + name_len].decode(
            "utf-8" if flag & (1 << 11) else "cp437"
        )
        for tile in tiles:
            if re.search(r"(?<![0-9])" + tile + r"(?![0-9])", path):
                if not path.lower().endswith(".laz"):
                    raise BerdorfZipError("The specific studied source tile is not named .laz")
                seen[tile] += 1
        pos += 46 + name_len + extra_len + comment_len
    if pos != len(directory):
        raise BerdorfZipError("Original parsed central directory byte count drift")
    if any(n != 1 for n in seen.values()):
        raise BerdorfZipError("Predeclared village source tile missing or duplicated")
    return {
        "declared_original_zip_member_count": members,
        "declared_original_laz_member_count": result["declared_laz_members"],
        "declared_original_copc_laz_named_members": result["declared_copc_laz_named_members"],
        "fixed_village_source_tile_names_found_exactly_once": len(seen),
        "source_tile_bodies_or_point_classes_read": False,
    }


def inspect_group(name: str, *, opener) -> dict:
    if name not in SOURCES or name not in RESOURCES:
        raise BerdorfZipError("Unreviewed source group")
    config = SOURCES[name]
    uuid, slug = RESOURCES[name]
    raw = read_http(opener, _request(OFFICIAL_API + uuid + "/"),
                    status=200, limit=MAX_METADATA_BYTES)
    try:
        data = json.loads(raw)
    except (ValueError, UnicodeError) as exc:
        raise BerdorfZipError("Invalid official resource metadata") from exc
    if not isinstance(data, dict):
        raise BerdorfZipError("Official resource is not an object")
    if isinstance(data.get("data"), dict):
        data = data["data"]
    if (data.get("id") != uuid or
        (data.get("filesize") or data.get("size")) != config["size"] or
        _source_digest_from_metadata(data).get("sha1") != config["sha1"]):
        raise BerdorfZipError("Official group UUID, original byte count or publisher SHA1 drift")
    try:
        url = _only_publisher_url(data.get("url"), slug)
    except ArchiveReceiptError as exc:
        raise BerdorfZipError("Unreviewed original source ZIP URL") from exc
    try:
        with opener.open(_request(url, method="HEAD"), timeout=25) as rsp:
            if (rsp.getcode() != 200 or
                rsp.info().get("Content-Length") != str(config["size"])):
                raise BerdorfZipError("Official source archive HEAD original byte count mismatch")
    except (HTTPError, URLError, OSError) as exc:
        raise BerdorfZipError("Original source archive HEAD unavailable") from exc
    size = config["size"]
    tail_start = size - ZIP_TAIL_BYTES
    tail = read_http(opener, _request(url, start=tail_start, end=size-1),
                     status=206, limit=ZIP_TAIL_BYTES,
                     range_expected=(tail_start, size-1, size))
    eocd = parse_eocd(tail, full_size=size)
    central = read_http(opener, _request(url, start=eocd["directory_start"],
                                        end=eocd["directory_end"]),
                        status=206, limit=eocd["directory_bytes"],
                        range_expected=(eocd["directory_start"], eocd["directory_end"], size))
    counts = count_fixed_tiles(central, members=eocd["members"], tiles=config["tiles"])
    return {
        "source_site": name,
        "official_source_resource_id": uuid,
        "original_publisher_archive_group": slug,
        "official_original_archive_head_bytes": size,
        "publisher_sha1_reported_but_not_original_verified": config["sha1"],
        "zip_tail_http206_original_bytes": ZIP_TAIL_BYTES,
        "zip_directory_http206_original_bytes": eocd["directory_bytes"],
        "original_zip_full_hash_verified": False,
        **counts,
        "original_source_zip_or_laz_payload_downloaded": False,
        "original_internal_member_names_or_offsets_exported": False,
        "source_point_class_2_5_6_measured": False,
        "cat_model_input_admitted": False,
    }


def inspect(opener=None) -> dict:
    if opener is None:
        opener = build_opener(NoRedirect())
    if set(SOURCES) != {"berdorf-south", "berdorf-north"}:
        raise BerdorfZipError("Original source scope unexpectedly expanded")
    reports = [inspect_group(name, opener=opener) for name in SOURCES]
    return {
        "schema_version": "lu-berdorf-2024-original-two-copc-group-zip-directory-http206-v0",
        "original_source_groups_checked": len(reports),
        "actual_original_zip_archive_payload_bytes_read": 0,
        "actual_laz_point_bytes_read": 0,
        "original_source_metadata_only": True,
        "source_classification_accuracy_proven": False,
        "source_licensing_model_admission_proven": False,
        "results": reports,
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args(argv)
    try:
        print(json.dumps(inspect(), sort_keys=True, indent=2, allow_nan=False))
        return 0
    except (ZipRangeError, BerdorfZipError, ArchiveReceiptError) as exc:
        parser.exit(2, "BLOCKED: " + str(exc) + "\n")


if __name__ == "__main__":
    raise SystemExit(main())
