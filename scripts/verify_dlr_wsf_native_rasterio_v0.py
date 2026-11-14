#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Independently verify two original DLR WSF 2019 COG pixel windows with GDAL.

Read exactly two immutable HTTP Range slices from the public DLR original TIFF:
32,768 bytes of its native TIFF/GeoTIFF header and the exact 24,659-byte
compressed block identified by that header. Assemble a temporary *sparse*
local TIFF containing only those original bytes at their original offsets;
GDAL/rasterio then independently decodes the original LZW tile, geokeys and
geotransform. Reject any pixel, class, CRS, alignment or SHA mismatch.

No full TIFF download, open network VFS, tile-byte upload or permanent artifact.
Never infer building counts, insured TIV, cadastral coverage or model admission.
"""
from __future__ import annotations

import hashlib
import json
import math
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from scripts.probe_dlr_wsf_native_cog_tile_v0 import (
    HEADER_SHA256,
    NATIVE_TILE_BYTES,
    NATIVE_TILE_OFFSET,
    NATIVE_TILE_SHA256,
    SOURCE,
    URL,
    WINDOWS,
    NativeCOGBlocked,
    _fetch_range,
    parse_native_header,
)


def verify_with_rasterio(header: bytes, tile: bytes) -> dict:
    """Independent GDAL decoding of the original tile, with fixed SHA guards."""
    if (hashlib.sha256(header).hexdigest() != HEADER_SHA256
            or hashlib.sha256(tile).hexdigest() != NATIVE_TILE_SHA256):
        raise NativeCOGBlocked("native source response identity changed")
    metadata = parse_native_header(header)
    if (metadata["tile_offset"], metadata["tile_compressed_bytes"]) != (
            NATIVE_TILE_OFFSET, NATIVE_TILE_BYTES):
        raise NativeCOGBlocked("original source tile address changed")

    try:
        import numpy as np
        import rasterio
        from rasterio.windows import Window, bounds
    except ImportError as exc:
        raise NativeCOGBlocked("GDAL/rasterio and numpy required for independent check") from exc

    # No third-party data is committed or left in the workspace. This temp
    # file is sparse: no missing TIFF tiles / overviews are materialized.
    with tempfile.TemporaryDirectory(prefix="oc-wsf-native-check-") as directory:
        path = Path(directory) / "temporary-original-ranges-only.tif"
        with path.open("wb") as output:
            output.write(header)
            output.seek(NATIVE_TILE_OFFSET, os.SEEK_SET)
            output.write(tile)
        if path.stat().st_size != NATIVE_TILE_OFFSET + NATIVE_TILE_BYTES:
            raise NativeCOGBlocked("sparse TIFF size or byte offsets changed")

        with rasterio.Env(GDAL_DISABLE_READDIR_ON_OPEN="YES"):
            with rasterio.open(path, "r") as src:
                if (src.driver != "GTiff"
                        or src.width != 22487 or src.height != 22487
                        or src.count != 1 or src.dtypes != ("uint8",)
                        or src.crs is None or src.crs.to_epsg() != 4326
                        or src.block_shapes != [(512, 512)]
                        or src.nodata is not None):
                    raise NativeCOGBlocked("GDAL disagrees with original COG metadata")
                affine = src.transform
                expected = metadata["geotransform"]
                computed = [affine.a, affine.b, affine.c,
                            affine.d, affine.e, affine.f]
                if not all(math.isclose(g, h, abs_tol=1e-12, rel_tol=0)
                           for g, h in zip(computed, expected)):
                    raise NativeCOGBlocked("independent GDAL geotransform mismatch")
                out = {}
                for label, cfg in WINDOWS.items():
                    local_x, local_y = cfg["tile_xy"]
                    global_col = 33 * 512 + local_x
                    global_row = 40 * 512 + local_y
                    window = Window(global_col, global_row, 32, 32)
                    data = src.read(1, window=window)
                    if data.shape != (32, 32):
                        raise NativeCOGBlocked("GDAL returned a wrong native window")
                    unique, counts = np.unique(data, return_counts=True)
                    hist = {int(v): int(n) for v, n in zip(unique, counts)}
                    if set(hist) - {0, 255}:
                        raise NativeCOGBlocked("independent decoder produced invalid class")
                    positives = hist.get(255, 0)
                    if positives != cfg["expected_255"]:
                        raise NativeCOGBlocked("native GDAL settlement class histogram mismatch")
                    rows = [
                        "".join("1" if int(value) == 255 else "0" for value in row)
                        for row in data
                    ]
                    digest = hashlib.sha256("\n".join(rows).encode("utf-8")).hexdigest()
                    if digest != cfg["rows_sha256"]:
                        raise NativeCOGBlocked("GDAL native pixels differ from Neon stored mask")
                    west, south, east, north = bounds(window, affine)
                    out[label] = {
                        "native_global_col": global_col,
                        "native_global_row": global_row,
                        "bbox_lonlat": [west, south, east, north],
                        "counts": {"0": 1024 - positives, "255": positives},
                        "mask_rows_sha256": digest,
                    }
                return {
                    "source_id": SOURCE,
                    "original_asset": URL,
                    "verification": "independent GDAL/rasterio native LZW decode",
                    "rasterio_version": rasterio.__version__,
                    "gdal_version": rasterio.__gdal_version__,
                    "original_header_32kb_sha256": HEADER_SHA256,
                    "original_compressed_block_sha256": NATIVE_TILE_SHA256,
                    "epsg": 4326,
                    "full_original_tiff_downloaded": False,
                    "native_windows": out,
                    "provider_bytes_persisted": False,
                    "original_provider_bytes_committed": False,
                    "model_input_approved": False,
                    "retrieved_at_utc": datetime.now(timezone.utc).isoformat(),
                }


def run() -> dict:
    header, total = _fetch_range(0, 32768)
    tile, total2 = _fetch_range(NATIVE_TILE_OFFSET, NATIVE_TILE_BYTES)
    if total != total2:
        raise NativeCOGBlocked("original TIFF remote asset changed between requests")
    return verify_with_rasterio(header, tile)


def main() -> int:
    import sys
    try:
        print(json.dumps(run(), sort_keys=True))
        return 0
    except (NativeCOGBlocked, OSError, ValueError, RuntimeError) as exc:
        print(f"BLOCKED: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
