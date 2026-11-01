#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""One frozen ESA WorldCover N48E009 block: read and validate actual class bytes.

Fetches only the exact reviewed 4KiB TIFF header, 10368-byte tile tables,
and block185 56442-byte compressed payload. Verifies pinned originals,
per-response HTTP range identity, bounded zlib/uint8 coding, WorldCover 2021
classes. Source/pixel bytes never persisted, exported or used as CAT inputs.
"""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import ssl
import struct
import sys
from urllib import error, request
import zlib

from scripts.validate_source_access import validate_path
from scripts.probe_esa_worldcover_tile_head_v0 import (
    CONTRACT_PATH, EXPECTED_MEDIA, OBJECT_PATH, SERVICE_ROOT, SOURCE, URL,
    NoRedirect,
)
from scripts.probe_esa_worldcover_tiff_header_v0 import (
    inspect_tiff_header, HeaderBlocked,
)
from scripts.parse_worldcover_geotiff_grid_v0 import (
    inspect_geotiff_grid, GeoGridBlocked,
)
from scripts.inspect_worldcover_tile_table_preflight_v0 import (
    inspect_tile_table_locations, TileTableBlocked,
)
from scripts.probe_esa_worldcover_tile_tables_v0 import (
    inspect_tables, TableSampleBlocked,
)

OPERATION = "sample_exact_v200_block185_56442"
SOURCE_TOTAL = 94_851_935
HEADER_RANGE = (0, 4095)
TABLE_RANGE = (13_644, 24_011)
BLOCK_RANGE = (43_278_196, 43_334_637)
HEADER_SHA256 = "a74fc1ff4733c3afff09328e014c0731eba2f1912f3f5cbc330ed0700f3f3529"
TABLE_SHA256 = "7de08710b64cad350b81da83a81fcfc0c74f5285e20e28b0a3e42d19151885ba"
BYTES_PER_TILE_SIDE = 1024
UNCOMPRESSED_LIMIT = BYTES_PER_TILE_SIDE ** 2
ALLOWED_CLASSES = frozenset((0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 95, 100))
GRID_POINT_BLOCK_LOCAL_INDEX = 880 * BYTES_PER_TILE_SIDE + 880  # 9.5 E, 50.5 N


class PixelBlockBlocked(ValueError):
    """One fixed source sample, format, or class-validation gate failed."""


def reviewed_contract(path: Path = CONTRACT_PATH) -> tuple[int, str]:
    obj = validate_path(path)
    if (
        obj["access_id"] != SOURCE
        or obj["source_ids"] != [SOURCE]
        or obj["status"] != "probe_ready"
        or obj["interface_type"] != "object_store"
        or obj["service_root"] != SERVICE_ROOT
        or obj["authentication"]["mode"] != "none"
        or obj["rights_and_policy"]["dataset_rights_status"] != "verified"
        or obj["rights_and_policy"]["api_terms_status"] != "separate_reviewed"
        or obj["rights_and_policy"]["commercial_automation_status"] != "allowed"
        or obj["request_contract"]["allowed_operations"].count(OPERATION) != 1
        or OBJECT_PATH not in obj["request_contract"]["path_templates"]
        or not EXPECTED_MEDIA.issubset(
            set(obj["response_contract"]["expected_media_types"])
        )
        or URL != SERVICE_ROOT + OBJECT_PATH
    ):
        raise PixelBlockBlocked("unreviewed single-block source access contract")
    max_bytes = obj["operational_constraints"]["max_probe_bytes"]
    timeout = obj["operational_constraints"]["timeout_seconds"]
    if (type(max_bytes) is not int or max_bytes < BLOCK_RANGE[1]-BLOCK_RANGE[0]+1
            or max_bytes > 65536 or type(timeout) is not int
            or not 0 < timeout <= 60):
        raise PixelBlockBlocked("invalid reviewed byte/timeout caps")
    return timeout, hashlib.sha256(path.read_bytes()).hexdigest()


def _open(req: request.Request, timeout: int):
    opener = request.build_opener(
        request.ProxyHandler({}),
        NoRedirect(),
        request.HTTPSHandler(context=ssl.create_default_context()),
    )
    return opener.open(req, timeout=timeout)


def _read_one(*, bounds: tuple[int, int], open_request, timeout: int) -> bytes:
    first, last = bounds
    length = last - first + 1
    if bounds not in (HEADER_RANGE, TABLE_RANGE, BLOCK_RANGE):
        raise PixelBlockBlocked("unreviewed external byte range requested")
    req = request.Request(
        URL, method="GET",
        headers={
            "Range": f"bytes={first}-{last}",
            "Accept": "image/tiff,application/octet-stream,binary/octet-stream",
            "Accept-Encoding": "identity",
            "User-Agent": "OpenCatastrophe-WorldCover-One-Block/0.1",
        },
    )
    try:
        with open_request(req, timeout) as response:
            if response.status != 206 or response.geturl() != URL:
                raise PixelBlockBlocked("source HTTP status/URL or redirect drift")
            mime = response.headers.get("Content-Type", "").split(";", 1)[0].strip().lower()
            if mime not in EXPECTED_MEDIA:
                raise PixelBlockBlocked("unexpected source media type")
            if response.headers.get("Content-Encoding", "identity").lower() != "identity":
                raise PixelBlockBlocked("source HTTP transfer coding not identity")
            if response.headers.get("Content-Range", "") != (
                f"bytes {first}-{last}/{SOURCE_TOTAL}"
            ):
                raise PixelBlockBlocked("source Content-Range or object size drift")
            if response.headers.get("Content-Length", "") != str(length):
                raise PixelBlockBlocked("source returned wrong range body size")
            raw = response.read(length + 1)
    except PixelBlockBlocked:
        raise
    except (error.HTTPError, error.URLError, TimeoutError, OSError) as exc:
        raise PixelBlockBlocked("one reviewed original source range unavailable") from exc
    if len(raw) != length:
        raise PixelBlockBlocked("source returned short/long original byte range")
    return raw


def tiff_sample_coding(header: bytes) -> dict[str, int]:
    """Require classic little-endian one-band 8bit DEFALTE TIFF coding."""
    try:
        summary = inspect_tiff_header(header)
        geo = inspect_geotiff_grid(
            header, width=summary["image_width_if_inline"],
            height=summary["image_length_if_inline"],
        )
        tables = inspect_tile_table_locations(header, header=summary)
    except (HeaderBlocked, GeoGridBlocked, TileTableBlocked) as exc:
        raise PixelBlockBlocked("TIFF header or geo/block-table identity mismatch") from exc
    if (hashlib.sha256(header).hexdigest() != HEADER_SHA256
            or not geo["geo_grid_verified_from_prefix_only"]
            or tables["tile_offsets_table_original_byte_range"] != [13644, 18827]
            or tables["tile_bytecounts_table_original_byte_range"] != [18828, 24011]
            or summary["compression_code_if_inline"] != 8
            or summary["samples_per_pixel_if_inline"] != 1
            or summary["tile_width_if_inline"] != BYTES_PER_TILE_SIDE
            or summary["tile_length_if_inline"] != BYTES_PER_TILE_SIDE):
        raise PixelBlockBlocked("frozen TIFF source integrity or coding drift")

    entries = {}
    first_ifd = struct.unpack_from("<I", header, 4)[0]
    n = struct.unpack_from("<H", header, first_ifd)[0]
    for i in range(n):
        tag, dtype, count, value = struct.unpack_from(
            "<HHII", header, first_ifd + 2 + 12*i
        )
        if tag not in (258, 317, 339, 284):
            continue
        if tag in entries or dtype != 3 or count != 1:
            raise PixelBlockBlocked("unsupported or duplicate TIFF sample coding tag")
        entries[tag] = value & 0xffff

    # TIFF defaults: Predictor=1, SampleFormat=1, PlanarConfiguration=1.
    # BitsPerSample MUST explicitly equal 8 for uint8 classification values.
    bits = entries.get(258)
    predictor = entries.get(317, 1)
    sample_format = entries.get(339, 1)
    planar = entries.get(284, 1)
    if bits != 8 or predictor not in (1, 2) or sample_format != 1 or planar != 1:
        raise PixelBlockBlocked("TIFF source block not reviewed uint8/Deflate coding")
    return {"bits_per_sample": bits, "predictor": predictor,
            "sample_format": sample_format, "planar": planar}


def decode_original_block(raw: bytes, *, predictor: int,
                          expected_compressed_bytes: int = BLOCK_RANGE[1]-BLOCK_RANGE[0]+1,
                          synthetic_polygon_overlap: bool = False) -> dict:
    """Bounded DEFLATE decompress plus optional TIFF horizontal predictor undo."""
    if (type(raw) is not bytes or type(expected_compressed_bytes) is not int
            or not 0 < expected_compressed_bytes <= 65536
            or len(raw) != expected_compressed_bytes):
        raise PixelBlockBlocked("wrong compressed source block identity or length")
    if predictor not in (1, 2):
        raise PixelBlockBlocked("unexpected TIFF predictor")
    try:
        decoder = zlib.decompressobj()
        unpacked = decoder.decompress(raw, UNCOMPRESSED_LIMIT + 1)
        if (len(unpacked) != UNCOMPRESSED_LIMIT or not decoder.eof
                or decoder.unused_data or decoder.unconsumed_tail):
            raise PixelBlockBlocked("DEFLATE payload exceeds, truncates or trails pixel data")
    except zlib.error as exc:
        raise PixelBlockBlocked("invalid original TIFF Deflate compression") from exc
    if predictor == 2:
        restored = bytearray(unpacked)
        for row in range(BYTES_PER_TILE_SIDE):
            start = row * BYTES_PER_TILE_SIDE
            for col in range(1, BYTES_PER_TILE_SIDE):
                off = start + col
                restored[off] = (restored[off] + restored[off - 1]) & 0xff
        pixels = bytes(restored)
    else:
        pixels = unpacked

    counts = Counter(pixels)
    if not set(counts).issubset(ALLOWED_CLASSES) or sum(counts.values()) != UNCOMPRESSED_LIMIT:
        raise PixelBlockBlocked("unexpected ESA WorldCover 2021 class code(s)")
    synthetic_overlap = {}
    if synthetic_polygon_overlap:
        from scripts.worldcover_synthetic_polygon_overlap_v0 import (
            PolygonOverlapBlocked, evaluate_synthetic_polygon_in_block,
        )
        try:
            # Exact geometry-to-source-pixel overlay is evaluated transiently.
            # The fixed polygon is fabricated, never a source building asset.
            synthetic_overlap = {
                "synthetic_polygon_overlay": evaluate_synthetic_polygon_in_block(pixels)
            }
        except PolygonOverlapBlocked as exc:
            raise PixelBlockBlocked("synthetic polygon-to-pixel overlap rejected") from exc
    return {
        "decompressed_uint8_pixel_count": UNCOMPRESSED_LIMIT,
        "class_code_counts": {str(k): counts[k] for k in sorted(counts)},
        "synthetic_test_location_class_code": pixels[GRID_POINT_BLOCK_LOCAL_INDEX],
        "decoded_block_sha256": hashlib.sha256(pixels).hexdigest(),
        "class_code_whitelist_verified": True,
        **synthetic_overlap,
    }


def probe(*, open_request=_open, contract_path: Path = CONTRACT_PATH,
          synthetic_polygon_overlap: bool = False) -> dict:
    timeout, contract_sha = reviewed_contract(contract_path)
    header = _read_one(bounds=HEADER_RANGE, open_request=open_request, timeout=timeout)
    coding = tiff_sample_coding(header)
    tables = _read_one(bounds=TABLE_RANGE, open_request=open_request, timeout=timeout)
    if hashlib.sha256(tables).hexdigest() != TABLE_SHA256:
        raise PixelBlockBlocked("original TIFF tile-array contents changed")
    try:
        table_meta = inspect_tables(tables)
    except TableSampleBlocked as exc:
        raise PixelBlockBlocked("source block table consistency drift") from exc
    if (table_meta["selected_block_index"] != 185
            or table_meta["selected_block_source_byte_range_if_present"]
               != list(BLOCK_RANGE)):
        raise PixelBlockBlocked("requested block does not match original reviewed TIFF table")
    compressed = _read_one(bounds=BLOCK_RANGE, open_request=open_request, timeout=timeout)
    outcome = decode_original_block(
        compressed, predictor=coding["predictor"],
        synthetic_polygon_overlap=synthetic_polygon_overlap,
    )
    return {
        "profile": "oc-esa-worldcover-one-classified-block-v0",
        "source_id": SOURCE,
        "tile_id": "N48E009",
        "operation": OPERATION,
        "retrieved_utc": datetime.now(timezone.utc).isoformat(),
        "original_object_size": SOURCE_TOTAL,
        "source_header_4096_sha256": HEADER_SHA256,
        "source_tile_tables_10368_sha256": TABLE_SHA256,
        "compressed_block_index": 185,
        "compressed_block_range": list(BLOCK_RANGE),
        "compressed_block_bytes": len(compressed),
        "compressed_block_sha256": hashlib.sha256(compressed).hexdigest(),
        **coding, **outcome,
        "request_set_sha256": hashlib.sha256(
            ("GET " + URL + " " + str(HEADER_RANGE) + str(TABLE_RANGE)
             + str(BLOCK_RANGE)).encode("ascii")
        ).hexdigest(),
        "access_contract_sha256": contract_sha,
        "code_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "source_bytes_persisted": False,
        "raster_pixels_persisted": False,
        "full_original_file_sha256_verified": False,
        "full_cog_conformance_verified": False,
        "real_building_exposure_matched": False,
        "model_input_approved": False,
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--live", action="store_true")
    parser.add_argument("--synthetic-polygon", action="store_true",
                        help="overlay only the fixed invented EPSG:4326 ring on verified pixels")
    args = parser.parse_args(argv)
    if not args.live:
        parser.error("requires explicit --live; offline by default")
    try:
        print(json.dumps(probe(synthetic_polygon_overlap=args.synthetic_polygon),
                         sort_keys=True, allow_nan=False))
    except (PixelBlockBlocked, ValueError, OSError) as exc:
        print(json.dumps({"status": "BLOCKED", "reason": str(exc),
                          "model_input_approved": False}), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
