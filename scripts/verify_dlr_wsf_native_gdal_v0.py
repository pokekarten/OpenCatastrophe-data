#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Independent GDAL/rasterio validation of two original DLR WSF2019 native pixel windows.

Builds an ephemeral *sparse* local TIFF from exactly two original HTTP byte
ranges, not an unauthorized full-file download: 32 KiB original TIFF header and
one 24,659-byte native LZW block. GDAL (not the repo's hand-written LZW decoder)
reads two original-resolution 32x32 windows and must reproduce Neon pixel hashes
and class counts exactly. Sparse unwritten blocks are never sampled. No full
raster / private data / original provider bytes are committed or uploaded.
"""
from __future__ import annotations

import hashlib
import json
import math
import tempfile
from pathlib import Path
from datetime import datetime, timezone

from scripts.probe_dlr_wsf_native_cog_tile_v0 import (
    SOURCE, URL, LICENSE_URL, HEADER_SHA256, NATIVE_TILE_SHA256,
    NATIVE_TILE_OFFSET, NATIVE_TILE_BYTES, HEADER_SIZE, WINDOWS,
    NativeCOGBlocked, _fetch_range, parse_native_header,
)

SAMPLE_IDS = {"nonsettlement": 28, "mixed": 29}
WINDOW_SIZE = 32
EXPECTED_CLASSES = frozenset((0, 255))
MAX_ORIGINAL_SIZE = 100_000_000


def mask_receipt(values: object) -> dict:
    """Summarize a 32x32 GDAL uint8 array without keeping any source pixels."""
    import numpy as np
    if not isinstance(values, np.ndarray) or values.shape != (32, 32):
        raise NativeCOGBlocked("GDAL returned an invalid native pixel window shape")
    if values.dtype != np.dtype("uint8"):
        raise NativeCOGBlocked("GDAL did not return native uint8 pixel classes")
    classes, counts = np.unique(values, return_counts=True)
    if not set(int(x) for x in classes).issubset(EXPECTED_CLASSES):
        raise NativeCOGBlocked("GDAL returned unreviewed pixel classes")
    n255 = int(np.count_nonzero(values == 255))
    rows = ["".join("1" if int(x) == 255 else "0" for x in line)
            for line in values]
    digest = hashlib.sha256("\n".join(rows).encode("ascii")).hexdigest()
    return {"0": 1024 - n255, "255": n255, "mask_rows_sha256": digest}


def check_gdal_windows(src: object, canonical_header: dict) -> dict:
    """Cross-check native EPSG:4326 and mask hash using independent rasterio."""
    import rasterio
    from rasterio.windows import Window
    if (src.driver != "GTiff" or src.count != 1
            or (src.width, src.height) != (22487, 22487)
            or src.dtypes != ("uint8",)
            or src.block_shapes != [(512, 512)]
            or src.crs != rasterio.crs.CRS.from_epsg(4326)
            or src.nodata is not None or src.mask_flag_enums[0] == []):
        raise NativeCOGBlocked("GDAL source dimensions, native band, CRS or NoData differ")
    transform = src.transform
    canonical = canonical_header["geotransform"]
    observed = (transform.a, transform.b, transform.c,
                transform.d, transform.e, transform.f)
    if any(not math.isclose(a, b, rel_tol=0, abs_tol=1e-11)
           for a, b in zip(observed, canonical)):
        raise NativeCOGBlocked("GDAL affine geo-transform differs from original TIFF")
    if src.profile.get("compress", "").lower() != "lzw":
        raise NativeCOGBlocked("GDAL did not recognize TIFF LZW")
    receipts = {}
    for label, rule in WINDOWS.items():
        x, y = rule["tile_xy"]
        col = 33 * 512 + x
        row = 40 * 512 + y
        array = src.read(
            1, window=Window(col, row, WINDOW_SIZE, WINDOW_SIZE),
            out_shape=(WINDOW_SIZE, WINDOW_SIZE),
            masked=False,
            resampling=rasterio.enums.Resampling.nearest,
        )
        result = mask_receipt(array)
        if (result["255"] != rule["expected_255"]
                or result["mask_rows_sha256"] != rule["rows_sha256"]):
            raise NativeCOGBlocked(f"independent GDAL/Neon {label} class mismatch")
        receipts[label] = {
            "neon_sample_id": SAMPLE_IDS[label],
            "native_column": col, "native_row": row,
            "width": 32, "height": 32,
            "class_0": result["0"],
            "class_255": result["255"],
            "rows_sha256": result["mask_rows_sha256"],
            "compared_to_neon": True,
        }
    return receipts


def verify_bounded_gdal(header: bytes, tile: bytes, total_bytes: int) -> dict:
    """Assemble two original fixed ranges into a transient sparse GTiff."""
    try:
        import rasterio
    except ImportError as exc:
        raise NativeCOGBlocked("rasterio independent GDAL dependency required") from exc
    if (len(header) != HEADER_SIZE
            or hashlib.sha256(header).hexdigest() != HEADER_SHA256
            or len(tile) != NATIVE_TILE_BYTES
            or hashlib.sha256(tile).hexdigest() != NATIVE_TILE_SHA256):
        raise NativeCOGBlocked("provider native header or block hash mismatch")
    if (not isinstance(total_bytes, int) or isinstance(total_bytes, bool)
            or not 13_000_000 <= total_bytes <= MAX_ORIGINAL_SIZE
            or NATIVE_TILE_OFFSET + len(tile) > total_bytes):
        raise NativeCOGBlocked("provider original TIFF total size invalid")
    meta = parse_native_header(header)
    if meta["tile_offset"] != NATIVE_TILE_OFFSET or meta["tile_compressed_bytes"] != len(tile):
        raise NativeCOGBlocked("compressed tile address differs from header")
    with tempfile.TemporaryDirectory(prefix="wsf2019-native-cog-") as tmp:
        filename = Path(tmp) / "original-range-sparse.tif"
        with filename.open("w+b") as f:
            f.truncate(total_bytes)  # sparse allocation; zero-filled other blocks are never read
            f.seek(0)
            f.write(header)
            f.seek(NATIVE_TILE_OFFSET)
            f.write(tile)
            f.flush()
        with rasterio.Env(GDAL_DISABLE_READDIR_ON_OPEN="EMPTY_DIR"):
            with rasterio.open(filename, sharing=False) as src:
                sampled = check_gdal_windows(src, meta)
    return {
        "source_id": SOURCE,
        "original_filename": URL.rsplit("/", 1)[-1],
        "original_tiff_total_bytes": total_bytes,
        "original_header_32768_sha256": HEADER_SHA256,
        "original_tile_24659_sha256": NATIVE_TILE_SHA256,
        "crs": "EPSG:4326", "native_resolution_verified": True,
        "independent_decoder": "rasterio GDAL libtiff",
        "rasterio_version": rasterio.__version__,
        "gdal_version": rasterio.__gdal_version__,
        "original_downloaded_bytes": HEADER_SIZE + NATIVE_TILE_BYTES,
        "full_tiff_downloaded": False,
        "original_provider_bytes_uploaded": False,
        "native_windows": sampled,
        "individual_building_count_verified": False,
        "insured_tiv_verified": False, "model_input_approved": False,
    }


def run_probe() -> dict:
    header, total_a = _fetch_range(0, HEADER_SIZE)
    tile, total_b = _fetch_range(NATIVE_TILE_OFFSET, NATIVE_TILE_BYTES)
    if total_a != total_b:
        raise NativeCOGBlocked("source identity changed between fixed range requests")
    receipt = verify_bounded_gdal(header, tile, total_a)
    receipt["license_evidence"] = LICENSE_URL
    receipt["retrieved_at_utc"] = datetime.now(timezone.utc).isoformat()
    return receipt


def main() -> int:
    try:
        print(json.dumps(run_probe(), sort_keys=True))
        return 0
    except NativeCOGBlocked as exc:
        import sys
        print("BLOCKED: " + str(exc), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
