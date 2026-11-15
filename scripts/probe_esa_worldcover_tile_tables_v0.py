#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""One fixed original WorldCover TIFF tile-directory sample (10368 bytes).

Only requests bytes 13644..24011 of the single reviewed N48E009 v200 Map
TIFF. No raster pixels, alternate tile, full GET, arbitrary URL/ranges,
source byte persistence, scientific admission, or database writes.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import ssl
import struct
import sys
from urllib import error, request

from scripts.validate_source_access import validate_path
from scripts.probe_esa_worldcover_tile_head_v0 import (
    CONTRACT_PATH, EXPECTED_MEDIA, OBJECT_PATH, SERVICE_ROOT, SOURCE, URL,
    NoRedirect,
)

OPERATION = "sample_exact_v200_tile_tables_10368"
FROM_BYTE = 13_644
TO_BYTE = 24_011
TOTAL_SOURCE_BYTES = 94_851_935
ENTRIES = 1296
EACH_TABLE_BYTES = ENTRIES * 4
SAMPLE_BYTES = TO_BYTE - FROM_BYTE + 1
SELECTED_BLOCK = 5 * 36 + 5  # Synthetic point 9.5E/50.5N: tile block (5,5).
MAX_COMPRESSED_BLOCK_BYTES = 8 * 1024 * 1024
RANGE = f"bytes={FROM_BYTE}-{TO_BYTE}"
EXPECTED_CONTENT_RANGE = f"bytes {FROM_BYTE}-{TO_BYTE}/{TOTAL_SOURCE_BYTES}"


class TableSampleBlocked(ValueError):
    """Unsafe source contract, range response, or original TIFF block table."""


def reviewed_contract(path: Path = CONTRACT_PATH) -> tuple[int, str]:
    contract = validate_path(path)
    if (
        contract["access_id"] != SOURCE
        or contract["source_ids"] != [SOURCE]
        or contract["status"] != "probe_ready"
        or contract["interface_type"] != "object_store"
        or contract["service_root"] != SERVICE_ROOT
        or contract["authentication"]["mode"] != "none"
        or contract["rights_and_policy"]["dataset_rights_status"] != "verified"
        or contract["rights_and_policy"]["api_terms_status"] != "separate_reviewed"
        or contract["rights_and_policy"]["commercial_automation_status"] != "allowed"
        or contract["request_contract"]["allowed_operations"].count(OPERATION) != 1
        or OBJECT_PATH not in contract["request_contract"]["path_templates"]
        or not EXPECTED_MEDIA.issubset(
            set(contract["response_contract"]["expected_media_types"])
        )
        or URL != SERVICE_ROOT + OBJECT_PATH
    ):
        raise TableSampleBlocked("reviewed exact TIFF tile-directory contract drift")
    max_bytes = contract["operational_constraints"]["max_probe_bytes"]
    timeout = contract["operational_constraints"]["timeout_seconds"]
    if (type(max_bytes) is not int or max_bytes < SAMPLE_BYTES or max_bytes > 65536
            or type(timeout) is not int or not 0 < timeout <= 60):
        raise TableSampleBlocked("unsafe source length/timeout constraints")
    return timeout, hashlib.sha256(path.read_bytes()).hexdigest()


def inspect_tables(raw: bytes) -> dict:
    """Validate 1296 exact TIFF LONG pairs, never return source arrays."""
    if type(raw) is not bytes or len(raw) != SAMPLE_BYTES:
        raise TableSampleBlocked("tile table sample must have exact original length")
    offsets = struct.unpack("<" + str(ENTRIES) + "I", raw[:EACH_TABLE_BYTES])
    counts = struct.unpack("<" + str(ENTRIES) + "I", raw[EACH_TABLE_BYTES:])
    used = []
    missing = 0
    compressed_total = 0
    for i, (offset, count) in enumerate(zip(offsets, counts)):
        if offset == 0 and count == 0:
            missing += 1
            continue
        if (offset <= TO_BYTE or count == 0 or count > MAX_COMPRESSED_BLOCK_BYTES
                or offset >= TOTAL_SOURCE_BYTES
                or count > TOTAL_SOURCE_BYTES - offset):
            raise TableSampleBlocked("invalid, missing or out-of-bounds TIFF compressed block")
        used.append((offset, offset + count - 1, i))
        compressed_total += count
    if not used:
        raise TableSampleBlocked("no valid nonempty TIFF tile blocks")
    used.sort()
    for a, b in zip(used, used[1:]):
        if b[0] <= a[1]:
            raise TableSampleBlocked("overlapping or duplicate compressed TIFF block ranges")

    chosen_offset, chosen_count = offsets[SELECTED_BLOCK], counts[SELECTED_BLOCK]
    return {
        "table_format": "two_1296_element_uint32_little_endian_arrays",
        "declared_tiff_blocks": ENTRIES,
        "nonempty_block_count": len(used),
        "zero_offset_zero_count_block_count": missing,
        "nonoverlapping_block_ranges": True,
        "total_reported_compressed_block_bytes": compressed_total,
        "minimum_compressed_block_bytes": min(counts[i] for _, _, i in used),
        "maximum_compressed_block_bytes": max(counts[i] for _, _, i in used),
        "selected_block_index": SELECTED_BLOCK,
        "selected_internal_block_row": 5,
        "selected_internal_block_column": 5,
        "selected_block_present": chosen_count > 0,
        "selected_block_source_byte_range_if_present":
            [chosen_offset, chosen_offset + chosen_count - 1] if chosen_count else None,
        "selected_block_compressed_bytes_if_present": chosen_count or None,
    }


def _open(req: request.Request, timeout: int):
    client = request.build_opener(
        request.ProxyHandler({}),
        NoRedirect(),
        request.HTTPSHandler(context=ssl.create_default_context()),
    )
    return client.open(req, timeout=timeout)


def probe(*, open_request=_open, contract_path: Path = CONTRACT_PATH) -> dict:
    timeout, contract_sha = reviewed_contract(contract_path)
    req = request.Request(
        URL, method="GET",
        headers={
            "Range": RANGE,
            "Accept": "image/tiff,application/octet-stream,binary/octet-stream",
            "Accept-Encoding": "identity",
            "User-Agent": "OpenCatastrophe-WorldCover-Tile-Tables/0.1",
        },
    )
    try:
        with open_request(req, timeout) as reply:
            if reply.geturl() != URL or reply.status != 206:
                raise TableSampleBlocked("source did not return exact HTTP 206")
            media = reply.headers.get("Content-Type", "").split(";", 1)[0].strip().lower()
            if media not in EXPECTED_MEDIA:
                raise TableSampleBlocked("unsupported tile table response media type")
            if reply.headers.get("Content-Encoding", "identity").lower() != "identity":
                raise TableSampleBlocked("non-identity transfer coding changes raw source range")
            if reply.headers.get("Content-Range", "") != EXPECTED_CONTENT_RANGE:
                raise TableSampleBlocked("Content-Range or original source size drift")
            if reply.headers.get("Content-Length", "") != str(SAMPLE_BYTES):
                raise TableSampleBlocked("unexpected Content-Length for exact table sample")
            raw = reply.read(SAMPLE_BYTES + 1)
    except TableSampleBlocked:
        raise
    except (error.HTTPError, error.URLError, OSError, TimeoutError) as exc:
        raise TableSampleBlocked("reviewed source tile-table Range request unavailable") from exc
    details = inspect_tables(raw)
    return {
        "profile": "oc-esa-worldcover-tile-tables-v0",
        "source_id": SOURCE,
        "tile_id": "N48E009",
        "operation": OPERATION,
        "retrieved_utc": datetime.now(timezone.utc).isoformat(),
        "http_status": 206,
        "transport_media_type": media,
        "source_object_total_bytes_from_range": TOTAL_SOURCE_BYTES,
        "source_original_sample_range": RANGE,
        "sample_bytes": len(raw),
        "sample_sha256": hashlib.sha256(raw).hexdigest(),
        "request_sha256": hashlib.sha256(
            ("GET " + URL + " Range:" + RANGE).encode("ascii")
        ).hexdigest(),
        "access_contract_sha256": contract_sha,
        "code_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        **details,
        "source_bytes_persisted": False,
        "raster_pixels_downloaded": False,
        "selected_block_bytes_downloaded": False,
        "source_wide_sha256_verified": False,
        "cog_layout_verified": False,
        "raster_classes_verified": False,
        "model_input_approved": False,
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--live", action="store_true")
    args = parser.parse_args(argv)
    if not args.live:
        parser.error("network is disabled by default; --live required")
    try:
        print(json.dumps(probe(), sort_keys=True, allow_nan=False))
    except (TableSampleBlocked, OSError, ValueError) as exc:
        print(json.dumps({"status": "BLOCKED", "reason": str(exc),
                          "model_input_approved": False}), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
