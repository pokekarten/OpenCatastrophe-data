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
    return match.group(1)


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
        geoid_height_m: Sequence[Sequence[float]]) -> dict:
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
        "geoid_conversion_rule": "bedrock_egm2008_m_plus_geoid_m",
        "bedrock_original_sha256_label": bedrock_sha256,
        "geoid_original_sha256_label": geoid_sha256,
        "converted_values_m": ellipsoid,
        "converted_sample_sha256": hashlib.sha256(deterministic.encode()).hexdigest(),
        "source_bytes_acquired": False,
        "model_input_admitted": False,
    }
