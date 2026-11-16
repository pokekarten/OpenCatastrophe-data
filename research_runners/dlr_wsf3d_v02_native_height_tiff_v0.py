# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Offline bounded original WSF3D v02 native BuildingHeight GeoTIFF preflight.

This source-specific contract accepts exactly one pinned 1x1-degree tile from
the DLR download service, already obtained through a separately reviewed and
authorized acquisition. It NEVER makes HTTP requests. A caller-supplied SHA
is an integrity check, not independent evidence of provider authenticity.

The public research receipt contains aggregate raster diagnostics only. It
does not export TIFF bytes, per-pixel locations, individual building heights
or insured values. No model admission, no physical ground-truth validation.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import re
import sys

SOURCE_ID = "dlr.wsf.3d.v02"
PROFILE = "dlr-wsf3d-v02-native-buildingheight-one-tile-offline-v0"
TILE_NAME = "WSF3D_V02_e021_s24_e022_s25_BuildingHeight.tif"
MAX_SOURCE_BYTES = 65_536
EXPECTED_BOUNDS = (21.0, -25.0, 22.0, -24.0)
BOUNDS_TOLERANCE_DEG = 0.0001
VALID_DTYPE_NAMES = {"uint8", "uint16", "int16", "float32", "float64"}


class WSF3DScienceBlocked(ValueError):
    """Native source identity/geometry/numeric quality gate did not pass."""


def inspect_native_bytes(original: bytes, *, expected_sha256: str) -> dict:
    """Check a small, locally supplied *original* raster without any network.

    Synthetic test inputs may supply their own hash; real T1/T3 workflows
    must freeze independently collected original bytes and retrieval receipt.
    """
    if type(original) is not bytes or not 0 < len(original) <= MAX_SOURCE_BYTES:
        raise WSF3DScienceBlocked("missing or oversized original source bytes")
    if (type(expected_sha256) is not str
            or re.fullmatch(r"[a-f0-9]{64}", expected_sha256) is None):
        raise WSF3DScienceBlocked("missing immutable original SHA256 identifier")
    measured_sha256 = hashlib.sha256(original).hexdigest()
    if measured_sha256 != expected_sha256:
        raise WSF3DScienceBlocked("original source SHA256 mismatch")
    if original[:4] not in {b"II*\\x00", b"MM\\x00*"}:
        raise WSF3DScienceBlocked("not a classic unmodified TIFF byte stream")
    try:
        import numpy as np
        from rasterio.io import MemoryFile
        from rasterio.errors import RasterioError
        from rasterio.enums import Compression
    except ImportError as exc:
        raise WSF3DScienceBlocked("pinned optional native TIFF reader unavailable") from exc

    try:
        # MemoryFile prevents a malformed TIFF sidecar or driver reference from
        # reading arbitrary local files. Dimension gates precede raster decode.
        with MemoryFile(original) as memory:
            with memory.open() as raster:
                if raster.driver != "GTiff" or raster.count != 1:
                    raise WSF3DScienceBlocked("not a single-band GeoTIFF")
                width, height = raster.width, raster.height
                if not (300 <= width <= 2048 and 300 <= height <= 2048):
                    raise WSF3DScienceBlocked("unsupported source raster dimensions")
                if raster.dtypes[0] not in VALID_DTYPE_NAMES:
                    raise WSF3DScienceBlocked("unsupported native source dtype")
                if raster.compression != Compression.lzw:
                    raise WSF3DScienceBlocked("native source compression is not LZW")
                if raster.crs is None or raster.crs.to_epsg() != 4326:
                    raise WSF3DScienceBlocked("original height raster CRS not EPSG:4326")
                t = raster.transform
                if (not all(math.isfinite(x) for x in (t.a, t.b, t.c, t.d, t.e, t.f))
                        or t.a <= 0 or t.e >= 0 or abs(t.b) > 1e-11
                        or abs(t.d) > 1e-11):
                    raise WSF3DScienceBlocked("rotated, south-up or nonfinite source transform")
                if not (0.0004 <= t.a <= 0.0013
                        and 0.0004 <= -t.e <= 0.0013):
                    raise WSF3DScienceBlocked("source grid deviates from ~90m reference")
                actual_bounds = (
                    raster.bounds.left, raster.bounds.bottom,
                    raster.bounds.right, raster.bounds.top,
                )
                if any(not math.isfinite(a) or abs(a - b) > BOUNDS_TOLERANCE_DEG
                       for a, b in zip(actual_bounds, EXPECTED_BOUNDS)):
                    raise WSF3DScienceBlocked("wrong provider 1-degree geographic tile")
                values = raster.read(1, masked=True)
                valid = values.compressed()
                if not np.all(np.isfinite(valid)):
                    raise WSF3DScienceBlocked("nonfinite unmasked building height")
                if np.any(valid < 0):
                    raise WSF3DScienceBlocked("negative unmasked building height")
                if valid.size and float(valid.max()) > 10_000:
                    raise WSF3DScienceBlocked("physically implausible height range")
                nodata = raster.nodata
                if nodata is not None and not math.isfinite(nodata):
                    raise WSF3DScienceBlocked("nonfinite raster nodata marker")
                actual_valid = int(valid.size)
                return {
                    "profile": PROFILE,
                    "source_id": SOURCE_ID,
                    "product_version": "WSF3D_V02",
                    "tile_name": TILE_NAME,
                    "original_bytes": len(original),
                    "original_sha256": measured_sha256,
                    "raster_driver": raster.driver,
                    "compression": raster.compression.name,
                    "band_count": raster.count,
                    "raster_crs": "EPSG:4326",
                    "image_width_pixels": width,
                    "image_height_pixels": height,
                    "total_pixels": width * height,
                    "mask_valid_pixels": actual_valid,
                    "masked_pixels": width * height - actual_valid,
                    "native_dtype": raster.dtypes[0],
                    "nodata_marker_present": nodata is not None,
                    "observed_min_height_raw": float(valid.min()) if valid.size else None,
                    "observed_max_height_raw": float(valid.max()) if valid.size else None,
                    "observed_pixel_values_scientifically_calibrated": False,
                    "provider_nodata_semantics_independently_verified": False,
                    "individual_building_heights_verified": False,
                    "insured_building_replacement_values_verified": False,
                    "independent_building_ground_truth_verified": False,
                    "original_provider_retrieval_receipt_verified_by_this_function": False,
                    "raw_raster_pixel_values_emitted": False,
                    "provider_bytes_persisted_by_runner": False,
                    "CAT_model_input_approved": False,
                }
    except (WSF3DScienceBlocked, RasterioError):
        raise
    except (OSError, OverflowError, TypeError, ValueError, RuntimeError) as exc:
        raise WSF3DScienceBlocked("native TIFF decode/semantic validation failed") from exc


def audit_file(path: Path, *, expected_sha256: str) -> dict:
    """Exact filename, regular file, byte cap, SHA; no provider GET."""
    if (type(path) is not Path or path.name != TILE_NAME or path.is_symlink()
            or not path.is_file() or path.stat().st_size > MAX_SOURCE_BYTES):
        raise WSF3DScienceBlocked("wrong source file path or original-byte bound")
    with path.open("rb") as stream:
        original = stream.read(MAX_SOURCE_BYTES + 1)
    return inspect_native_bytes(original, expected_sha256=expected_sha256)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--original-tiff", type=Path, required=True)
    parser.add_argument("--original-sha256", required=True)
    args = parser.parse_args(argv)
    try:
        print(json.dumps(audit_file(args.original_tiff, expected_sha256=args.original_sha256),
                         sort_keys=True, indent=2, allow_nan=False))
    except Exception:
        # Never print source driver errors: they can contain filesystem paths
        # and untrusted external geospatial metadata.
        print("BLOCKED: original WSF3D v02 native height science preflight",
              file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
