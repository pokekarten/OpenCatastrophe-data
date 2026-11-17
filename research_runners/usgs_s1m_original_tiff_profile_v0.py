# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Offline USGS S1M original-file byte and native GeoTIFF header preflight.

No network access, pixel data read, external provider body persistence, source
re-licensing, or model admission. The caller's supplied expected SHA-256 and
size are NOT independent proof of provider provenance. An independently
trusted exact-asset receipt and GeoPackage work-unit lineage are still needed.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import re
import sys

SOURCE_ID = "usgs.3dep.seamless-1m.s1m"
PILOT_SOURCE_ID = "6a9785801ba49b050c166274"
ORIGINAL_FILENAME = "S1M_n0450e1510_20260821.tif"
ORIGINAL_URL = (
    "https://prd-tnm.s3.amazonaws.com/StagedProducts/Elevation/"
    "S1M/n04e15/n0450e1510/" + ORIGINAL_FILENAME
)
MAX_ORIGINAL_BYTES = 1_000_000_000  # bounded source, not a download allowance
READ_CHUNK = 1024 * 1024
LOWER_HEX_SHA = re.compile(r"[0-9a-f]{64}\Z")


# Exact frozen TNMAccess WGS84 product bbox, not native Albers coordinates.
FROZEN_PRODUCT_BBOX_WGS84 = (
    -81.0028601420002, 25.92070859857935,
    -80.8895404313893, 26.025030076412904,
)
MAX_BBOX_EDGE_DRIFT_DEGREES = 0.01


class Blocked(ValueError):
    """Reject any input or raster metadata outside the frozen research scope."""


def check_local_identity(path: Path, expected_sha256: str, expected_bytes: int) -> dict:
    """Hash the entire local byte stream before any untrusted TIFF parser opens it."""
    if type(expected_sha256) is not str or LOWER_HEX_SHA.fullmatch(expected_sha256) is None:
        raise Blocked("expected SHA-256 must contain exactly 64 lowercase hex characters")
    if type(expected_bytes) is not int or not 0 < expected_bytes <= MAX_ORIGINAL_BYTES:
        raise Blocked("expected byte count outside reviewed maximum")
    if path.name != ORIGINAL_FILENAME or path.is_symlink() or not path.is_file():
        raise Blocked("not the pinned regular local S1M filename")
    size = path.stat().st_size
    if size != expected_bytes:
        raise Blocked("local source byte count differs from supplied expectation")
    sha = hashlib.sha256()
    seen = 0
    try:
        with path.open("rb") as f:
            while True:
                chunk = f.read(READ_CHUNK)
                if not chunk:
                    break
                seen += len(chunk)
                if seen > expected_bytes:
                    raise Blocked("original byte stream expanded after stat")
                sha.update(chunk)
    except OSError as exc:
        raise Blocked("source file became unavailable during hashing") from exc
    if seen != expected_bytes or sha.hexdigest() != expected_sha256:
        raise Blocked("original full-file SHA-256 or byte count mismatch")
    return {"file_sha256":sha.hexdigest(), "file_bytes":seen}


def check_native_header(profile: object) -> dict:
    """Validate metadata observed from a native TIFF; never infer pixel quality."""
    keys = {
        "driver", "bands", "dtype", "horizontal_epsg", "horizontal_unit_factor",
        "width", "height", "is_tiled", "nodata", "pixel_x", "pixel_y",
        "rot_x", "rot_y", "origin_x", "origin_y",
    }
    if type(profile) is not dict or set(profile) != keys:
        raise Blocked("missing or unexpected native S1M GeoTIFF header attributes")
    if profile["driver"] != "GTiff" or type(profile["bands"]) is not int or profile["bands"] != 1:
        raise Blocked("source is not a single-band GeoTIFF")
    if profile["dtype"] not in ("float32", "float64") or profile["is_tiled"] is not True:
        raise Blocked("S1M must have a tiled floating-point native raster")
    if type(profile["horizontal_epsg"]) is not int or profile["horizontal_epsg"] != 6350:
        raise Blocked("S1M native horizontal CRS is not EPSG:6350")
    if type(profile["horizontal_unit_factor"]) not in (int, float) or (
        (type(profile["horizontal_unit_factor"]) is float and not math.isfinite(profile["horizontal_unit_factor"]))
        or profile["horizontal_unit_factor"] != 1
    ):
        raise Blocked("S1M horizontal units are not metres")
    for key in ("width", "height"):
        if type(profile[key]) is not int or not 9000 <= profile[key] <= 11000:
            raise Blocked("native S1M tile extent is not approximately 10 km")
    for key, expected in (("pixel_x", 1), ("pixel_y", -1),
                          ("rot_x", 0), ("rot_y", 0), ("nodata", -999999)):
        value = profile[key]
        if type(value) not in (int, float) or (type(value) is float and not math.isfinite(value)) or value != expected:
            raise Blocked("invalid S1M native raster spacing, orientation or NoData: " + key)
    for key in ("origin_x", "origin_y"):
        value = profile[key]
        if type(value) not in (int, float) or (type(value) is float and not math.isfinite(value)):
            raise Blocked("unbounded S1M projected origin")
    return {
        "header_matches_published_horizontal_profile": True,
        "horizontal_epsg": 6350,
        "horizontal_unit": "metre",
        "pixel_spacing_m": 1,
        "nodata_sentinel": -999999,
        "vertical_epsg_5703_verified_from_header": False,
        "geoid18_verified_from_original_lineage": False,
        "pixel_values_read": False,
        "void_backfill_and_blending_verified": False,
        "companion_geopackage_verified": False,
        "cog_layout_independently_verified": False,
        "model_input_approved": False,
    }


def check_frozen_florida_footprint(profile: object) -> dict:
    """Cross-check a native Albers tile against one frozen WGS84 catalogue bbox.

    A passing caller-provided profile does not attest original source bytes,
    source-project lineage, elevation pixels or reuse permission.
    """
    check_native_header(profile)
    try:
        from rasterio.warp import transform_bounds
    except ImportError as exc:
        raise Blocked("pinned Rasterio/PROJ required for spatial source check") from exc
    west_native = profile["origin_x"]
    north_native = profile["origin_y"]
    east_native = west_native + profile["width"] * profile["pixel_x"]
    south_native = north_native + profile["height"] * profile["pixel_y"]
    if not (west_native < east_native and south_native < north_native):
        raise Blocked("native S1M raster bounds are reversed or degenerate")
    try:
        bbox = transform_bounds(
            "EPSG:6350", "EPSG:4326", west_native, south_native,
            east_native, north_native, densify_pts=21,
        )
    except (ValueError, RuntimeError, OverflowError) as exc:
        raise Blocked("cannot transform S1M Albers tile bounds into WGS84") from exc
    if (
        len(bbox) != 4 or not all(math.isfinite(x) for x in bbox)
        or not (bbox[0] < bbox[2] and bbox[1] < bbox[3])
        or any(
            abs(observed - frozen) > MAX_BBOX_EDGE_DRIFT_DEGREES
            for observed, frozen in zip(bbox, FROZEN_PRODUCT_BBOX_WGS84)
        )
    ):
        raise Blocked("native raster footprint does not match pinned Florida S1M catalogue bounds")
    return {
        "frozen_florida_catalogue_bbox_consistent": True,
        "bbox_drift_tolerance_degrees": MAX_BBOX_EDGE_DRIFT_DEGREES,
        "native_raster_provider_origin_independently_attested": False,
        "native_raster_elevation_pixels_verified": False,
    }


def inspect_original_tiff(path: Path, expected_sha256: str, expected_bytes: int) -> dict:
    """Offline native-header screen after full local byte checksum verification."""
    receipt = check_local_identity(path, expected_sha256, expected_bytes)
    try:
        import rasterio
    except ImportError as exc:
        raise Blocked("pinned Rasterio/GDAL dependency required to decode TIFF header") from exc
    try:
        with rasterio.Env(GDAL_DISABLE_READDIR_ON_OPEN="YES", PROJ_NETWORK="OFF"):
            with rasterio.open(path, "r") as src:
                if src.crs is None or src.crs.to_epsg() is None:
                    raise Blocked("native horizontal GeoTIFF CRS missing or unrecognized")
                profile = {
                    "driver": src.driver, "bands": src.count,
                    "dtype": src.dtypes[0] if src.count == 1 else None,
                    "horizontal_epsg": src.crs.to_epsg(),
                    "horizontal_unit_factor": src.crs.linear_units_factor[1],
                    "width": src.width, "height": src.height,
                    "is_tiled": src.is_tiled, "nodata": src.nodata,
                    "pixel_x": src.transform.a, "pixel_y": src.transform.e,
                    "rot_x": src.transform.b, "rot_y": src.transform.d,
                    "origin_x": src.transform.c, "origin_y": src.transform.f,
                }
                result = check_native_header(profile)
                footprint = check_frozen_florida_footprint(profile)
    except (OSError, ValueError, RuntimeError, TypeError, IndexError, AttributeError) as exc:
        if isinstance(exc, Blocked):
            raise
        raise Blocked("invalid or unreviewed source TIFF metadata") from exc
    return {
        "source_id": SOURCE_ID,
        "catalogue_source_id_reference_only": PILOT_SOURCE_ID,
        "catalogue_download_url_reference_only": ORIGINAL_URL,
        "identity_status": "caller_supplied_full_file_sha_matches_not_independent_provider_attestation",
        **receipt,
        **result,
        **footprint,
        "source_provider_original_verified": False,
        "external_bytes_committed_to_git": False,
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--original-tiff", type=Path, required=True)
    ap.add_argument("--expected-sha256", required=True)
    ap.add_argument("--expected-bytes", type=int, required=True)
    args = ap.parse_args(argv)
    try:
        print(json.dumps(inspect_original_tiff(
            args.original_tiff, args.expected_sha256, args.expected_bytes),
            sort_keys=True, allow_nan=False))
        return 0
    except (Blocked, OSError) as exc:
        print("BLOCKED: " + str(exc), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
