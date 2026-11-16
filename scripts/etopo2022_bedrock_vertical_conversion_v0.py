# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Offline ETOPO 2022 bedrock + geoid scientific transformation preflight.

ETOPO 2022 v1, 15 arc-second bedrock elevation has EGM2008 vertical datum
(EPSG:3855). Companion geoid heights must be ADDED to get WGS84 ellipsoidal
heights (EPSG:4979), as in official NOAA ETOPO 2022 User Guide §2.2.

This transformation only accepts two named, co-registered product slices.
It cannot establish pixel alignment/CRS from a filename alone: callers must
verify spatial grids, original files/hashes, nodata, licence, resolution and
model admission separately. No network, data acquisition or source publication.
"""
from __future__ import annotations

import hashlib
import json
import math
import re
from collections.abc import Sequence

_FILENAME = re.compile(r"^ETOPO_2022_v1_15s_([NS](?:0[0-9]|[1-8][0-9]|90)[EW](?:0[0-9][0-9]|1[0-7][0-9]|180))_(bed|geoid)\.nc$")
_HASH = re.compile(r"^[0-9a-f]{64}$")
_MAX_CELLS = 10000


class ETOPOVerticalBlocked(ValueError):
    """Unknown source asset, misaligned slice, or scientifically unsafe value."""


def _asset(filename: str, expected_kind: str) -> str:
    if type(filename) is not str:
        raise ETOPOVerticalBlocked("asset filename must be text")
    match = _FILENAME.fullmatch(filename)
    if not match or match.group(2) != expected_kind:
        raise ETOPOVerticalBlocked("wrong ETOPO 2022 v1 15s NetCDF source asset")
    tile = match.group(1)
    _tile_origin(tile)
    return tile


def _tile_origin(tile: str) -> tuple[int, int]:
    """Decode the 15-degree tile north/left BORDER, not its first pixel."""
    north = int(tile[1:3]) * (1 if tile[0] == "N" else -1)
    west = int(tile[4:7]) * (1 if tile[3] == "E" else -1)
    if north not in range(-75, 91, 15) or west not in range(-180, 166, 15):
        raise ETOPOVerticalBlocked("tile not aligned to official 15-degree boundaries")
    return north, west


def _axis_indices(values: Sequence[float], *, label: str, size: int,
                  border: int, direction: int) -> tuple[int, ...]:
    """Verify caller-supplied 15s cell centres within one official 15° tile.

    'direction' is -1 for latitude measured southward from the north
    border and +1 for longitude measured eastward from the west border.
    A metadata read elsewhere MUST still prove these values came from the
    two original files; this numeric gate cannot establish provenance.
    """
    if type(values) not in (tuple, list) or len(values) != size:
        raise ETOPOVerticalBlocked(f"{label} axis length/shape mismatch")
    indices = []
    for value in values:
        if type(value) not in (float, int):
            raise ETOPOVerticalBlocked(f"{label} coordinate not numeric")
        try:
            coordinate = float(value)
        except (OverflowError, ValueError) as exc:
            raise ETOPOVerticalBlocked(f"{label} coordinate cannot be represented") from exc
        if not math.isfinite(coordinate):
            raise ETOPOVerticalBlocked(f"{label} coordinate is not finite")
        # ETOPO v1 15 arcseconds = 1/240 degrees; subtract 0.5 for
        # cell-centre registration rather than accepting tile boundary nodes.
        offset = (coordinate - border) * direction * 240 - 0.5
        index = round(offset)
        if not 0 <= index < 3600 or abs(offset - index) > 0.00002:
            raise ETOPOVerticalBlocked(f"{label} off the 15s cell-centre lattice")
        indices.append(index)
    steps = [b - a for a, b in zip(indices, indices[1:])]
    # A zig-zag 0,1,0 has valid *absolute* neighbour distances but repeats
    # the first pixel: each axis must be strictly monotone, either direction.
    if steps and (abs(steps[0]) != 1 or any(step != steps[0] for step in steps[1:])):
        raise ETOPOVerticalBlocked(f"{label} axis has gaps, duplicates or reverses direction")
    return tuple(indices)


def _paired_window_grid(*, tile: str,
        bedrock_lat_deg: Sequence[float], bedrock_lon_deg: Sequence[float],
        geoid_lat_deg: Sequence[float], geoid_lon_deg: Sequence[float],
        height: int, width: int) -> None:
    """Check both supplied axis arrays describe the same 15s cell window."""
    north, west = _tile_origin(tile)
    bedlat = _axis_indices(bedrock_lat_deg, label="bedrock latitude", size=height,
                           border=north, direction=-1)
    geolat = _axis_indices(geoid_lat_deg, label="geoid latitude", size=height,
                           border=north, direction=-1)
    bedlon = _axis_indices(bedrock_lon_deg, label="bedrock longitude", size=width,
                           border=west, direction=1)
    geolon = _axis_indices(geoid_lon_deg, label="geoid longitude", size=width,
                           border=west, direction=1)
    if (bedlat, bedlon) != (geolat, geolon):
        raise ETOPOVerticalBlocked("bedrock/geoid coordinate arrays do not identify the same cells")


def _matrix(values: Sequence[Sequence[float]], label: str) -> tuple[tuple[float, ...], ...]:
    if type(values) not in (tuple, list) or not values or len(values) > _MAX_CELLS:
        raise ETOPOVerticalBlocked(f"invalid {label} raster dimensions")
    width = None
    output = []
    total = 0
    for row in values:
        if type(row) not in (tuple, list) or not row:
            raise ETOPOVerticalBlocked(f"empty or malformed {label} row")
        if width is None:
            width = len(row)
        if len(row) != width:
            raise ETOPOVerticalBlocked(f"ragged {label} raster")
        total += len(row)
        if total > _MAX_CELLS:
            raise ETOPOVerticalBlocked("sample must be at most 10000 cells")
        checked = []
        for x in row:
            if type(x) not in (int, float):
                raise ETOPOVerticalBlocked(f"non-numeric {label} elevation")
            try:
                number = float(x)
            except (OverflowError, ValueError) as exc:
                raise ETOPOVerticalBlocked(f"invalid {label} elevation") from exc
            if not math.isfinite(number):
                raise ETOPOVerticalBlocked(f"nonfinite {label} elevation/nodata")
            checked.append(number)
        output.append(tuple(checked))
    return tuple(output)


def convert_bedrock_egm2008_to_wgs84(*,
        bedrock_filename: str, geoid_filename: str,
        bedrock_sha256: str, geoid_sha256: str,
        bedrock_elevation_m: Sequence[Sequence[float]],
        geoid_height_m: Sequence[Sequence[float]],
        bedrock_lat_deg: Sequence[float] | None = None,
        bedrock_lon_deg: Sequence[float] | None = None,
        geoid_lat_deg: Sequence[float] | None = None,
        geoid_lon_deg: Sequence[float] | None = None) -> dict:
    """Convert finite, already co-registered *sample arrays*; fail closed.

    Caller-provided original-hash labels are NOT cryptographically reverified:
    this function has no original provider files. Scientific co-registration
    remains external; matching filenames/shape alone is insufficient.
    """
    tile = _asset(bedrock_filename, "bed")
    if _asset(geoid_filename, "geoid") != tile:
        raise ETOPOVerticalBlocked("bedrock and geoid tiles differ")
    if type(bedrock_sha256) is not str or not _HASH.fullmatch(bedrock_sha256):
        raise ETOPOVerticalBlocked("missing original bedrock byte identity")
    if type(geoid_sha256) is not str or not _HASH.fullmatch(geoid_sha256):
        raise ETOPOVerticalBlocked("missing original geoid byte identity")
    if bedrock_sha256 == geoid_sha256:
        raise ETOPOVerticalBlocked("bedrock and geoid original identities are identical")
    bed = _matrix(bedrock_elevation_m, "bedrock")
    geoid = _matrix(geoid_height_m, "geoid")
    if len(bed) != len(geoid) or len(bed[0]) != len(geoid[0]):
        raise ETOPOVerticalBlocked("bedrock and geoid sample shapes differ")
    coordinate_axes = (bedrock_lat_deg, bedrock_lon_deg, geoid_lat_deg, geoid_lon_deg)
    if any(axis is not None for axis in coordinate_axes):
        if any(axis is None for axis in coordinate_axes):
            raise ETOPOVerticalBlocked("all four coordinate axes are required together")
        _paired_window_grid(
            tile=tile,
            bedrock_lat_deg=bedrock_lat_deg,
            bedrock_lon_deg=bedrock_lon_deg,
            geoid_lat_deg=geoid_lat_deg,
            geoid_lon_deg=geoid_lon_deg,
            height=len(bed), width=len(bed[0]),
        )
    ellipsoid = [[a+b for a,b in zip(row_a,row_b)] for row_a,row_b in zip(bed,geoid)]
    if any(not math.isfinite(v) for row in ellipsoid for v in row):
        raise ETOPOVerticalBlocked("nonfinite converted elevation")
    deterministic = json.dumps(ellipsoid, allow_nan=False, separators=(",", ":"))
    return {
        "profile": "etopo2022-v1-bedrock-15s-geoid-paired-sample-v0",
        "tile": tile, "width": len(bed[0]), "height": len(bed),
        "source_vertical_epsg": 3855, "output_ellipsoidal_epsg": 4979,
        "input_original_hash_labels_verified_from_bytes": False,
        "sample_spatial_grid_coregistration_independently_verified": False,
        "supplied_coordinate_arrays_15s_cell_parity_checked": all(
            axis is not None for axis in coordinate_axes
        ),
        "coordinates_verified_from_original_file_bytes": False,
        "geoid_conversion_rule": "bedrock_egm2008_m_plus_geoid_m",
        "bedrock_original_sha256_label": bedrock_sha256,
        "geoid_original_sha256_label": geoid_sha256,
        "converted_values_m": ellipsoid,
        "converted_sample_sha256": hashlib.sha256(deterministic.encode()).hexdigest(),
        "source_bytes_acquired": False,
        "model_input_admitted": False,
    }
