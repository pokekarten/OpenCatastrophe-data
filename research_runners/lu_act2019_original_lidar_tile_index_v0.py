#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Integrity and fixed-study-area coverage of the ACT original 2019 LiDAR tile index.

Fetch nothing here: caller supplies the official original 440 kB GeoJSON in a
temporary file. No LiDAR point clouds or per-tile URLs/coordinates are emitted.
This is a source-access receipt, NOT independent observed building identity.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
from urllib.parse import urlsplit

OFFICIAL_INDEX = (
    "https://download.data.public.lu/resources/"
    "lidar-2019-releve-3d-du-territoire-luxembourgeois/"
    "20200225-183349/lidar-urls.geojson"
)
# Original publisher resource metadata (not a hash manufactured by this script).
PUBLISHED_SHA1 = "6fa8f0bd8afdf87bd175c9dab2d7b479b1b18874"
# Independently calculated from all 450512 exact original bytes in Actions 41892606021.
OBSERVED_ORIGINAL_SHA256 = "2ad881f794e3699b83a0b312c84c2b0e467f21a7ec92bbf10a0c9a21aa4d1e6a"
OBSERVED_ORIGINAL_BYTES = 450_512
OBSERVED_FEATURES = 1_287
OBSERVED_STUDY_TILE_COUNTS = {"luxembourg-city": 1, "berdorf-village": 2}
INDEX_BYTES_MAX = 600_000
ITEMS_MAX = 2000
POINTS_MAX = 20
TILE_PATH_PREFIX = "/resources/lidar-2019-releve-3d-du-territoire-luxembourgeois/"
CRS84 = "urn:ogc:def:crs:OGC:1.3:CRS84"
# Public, predeclared sites already used by #1272 and #1288.
SITES = {"luxembourg-city": (6.1319, 49.6116),
         "berdorf-village": (6.348821, 49.820946)}
WINDOW_HALF_M = 50.0


class OriginalIndexError(ValueError):
    """Only authored validation labels may appear in public error messages."""


def _unique_pairs(pairs):
    result = {}
    for key, val in pairs:
        if key in result:
            raise OriginalIndexError("Duplicate original JSON object keys")
        result[key] = val
    return result


def _reject_constant(_):
    raise OriginalIndexError("Nonfinite JSON constant")


def _validate_asset_url(value):
    if not isinstance(value, str) or len(value) > 480:
        raise OriginalIndexError("Malformed original tile URL")
    parts = urlsplit(value)
    if (parts.scheme != "https" or parts.hostname != "download.data.public.lu"
            or parts.username or parts.password or parts.port
            or parts.query or parts.fragment or not parts.path.startswith(TILE_PATH_PREFIX)
            or not parts.path.endswith(".zip") or "\\" in value or "%" in parts.path):
        raise OriginalIndexError("Unreviewed original tile download endpoint")
    return value


def _validate_polygon(geometry):
    if not isinstance(geometry, dict) or geometry.get("type") != "Polygon":
        raise OriginalIndexError("Only original tile Polygon bounds supported")
    rings = geometry.get("coordinates")
    if not isinstance(rings, list) or len(rings) != 1:
        raise OriginalIndexError("Unreviewed original tile ring structure")
    ring = rings[0]
    if not isinstance(ring, list) or not 4 <= len(ring) <= POINTS_MAX:
        raise OriginalIndexError("Original tile geometry vertex budget exceeded")
    for pair in ring:
        if (not isinstance(pair, list) or len(pair) != 2
                or not all(type(z) in (int, float) and math.isfinite(z) for z in pair)):
            raise OriginalIndexError("Nonfinite or malformed original coordinate")
        lon, lat = pair
        if not (5.0 <= lon <= 7.1 and 48.6 <= lat <= 50.6):
            raise OriginalIndexError("Outside bounded Luxembourg tile envelope")
    if ring[0] != ring[-1]:
        raise OriginalIndexError("Original tile ring not closed")
    return geometry


def profile_index(source: dict, *, min_items=1):
    """Validate source geometry + URL structure; no feature identifiers emitted."""
    if not isinstance(source, dict) or source.get("type") != "FeatureCollection":
        raise OriginalIndexError("Expected original GeoJSON FeatureCollection")
    crs = source.get("crs")
    if (not isinstance(crs, dict) or crs.get("type") != "name"
            or not isinstance(crs.get("properties"), dict)
            or crs["properties"].get("name") != CRS84):
        raise OriginalIndexError("Original CRS84 axis contract changed")
    features = source.get("features")
    if (not isinstance(features, list) or type(min_items) is not int
            or not 1 <= min_items <= ITEMS_MAX
            or not min_items <= len(features) <= ITEMS_MAX):
        raise OriginalIndexError("Invalid original tile count or bounded sample")
    urls = set()
    polygons = []
    for item in features:
        if not isinstance(item, dict) or item.get("type") != "Feature":
            raise OriginalIndexError("Unexpected original feature type")
        props = item.get("properties")
        if not isinstance(props, dict):
            raise OriginalIndexError("Missing original tile URL property")
        url = _validate_asset_url(props.get("url"))
        if url in urls:
            raise OriginalIndexError("Duplicate original tile URL")
        urls.add(url)
        polygons.append(_validate_polygon(item.get("geometry")))
    return polygons


def site_coverage(polygons):
    """Count fixed 100m square/tile intersections; no per-tile URLs or ID output."""
    try:
        from pyproj import Transformer
        from shapely.geometry import Polygon
        from shapely.geometry import shape
    except ImportError as exc:
        raise OriginalIndexError("Pinned GIS runtime missing") from exc
    wgs_to_3035 = Transformer.from_crs(4326, 3035, always_xy=True)
    epsg3035_to_wgs = Transformer.from_crs(3035, 4326, always_xy=True)
    safe_polys = []
    for raw in polygons:
        geom = shape(raw)
        if geom.is_empty or not geom.is_valid or geom.area <= 0:
            raise OriginalIndexError("Invalid actual tile geometry")
        safe_polys.append(geom)
    output = {}
    for site, (lon, lat) in SITES.items():
        x,y = wgs_to_3035.transform(lon,lat)
        ring = [epsg3035_to_wgs.transform(a,b) for a,b in (
            (x-WINDOW_HALF_M,y-WINDOW_HALF_M),
            (x+WINDOW_HALF_M,y-WINDOW_HALF_M),
            (x+WINDOW_HALF_M,y+WINDOW_HALF_M),
            (x-WINDOW_HALF_M,y+WINDOW_HALF_M),
        )]
        window = Polygon(ring)
        if not window.is_valid or window.area <= 0:
            raise OriginalIndexError("Invalid fixed research window")
        positive_tiles = sum(g.intersects(window) and g.intersection(window).area > 0 for g in safe_polys)
        if positive_tiles != OBSERVED_STUDY_TILE_COUNTS[site]:
            raise OriginalIndexError("Exact source site tile coverage drift")
        output[site] = {
            "original_index_tile_polygons_intersecting_100m_window": positive_tiles,
            "actual_2019_lidar_tile_bytes_retrieved": False,
            "source_observation_independent_of_vdl3d_verified": False,
            "2019_lidar_building_identity_verified": False,
        }
    return output


def verify_original(path: Path) -> dict:
    if path.is_symlink() or not path.is_file() or not 0 < path.stat().st_size <= INDEX_BYTES_MAX:
        raise OriginalIndexError("Original index must be one bounded local regular file")
    raw = path.read_bytes()
    sha1 = hashlib.sha1(raw).hexdigest()
    if sha1 != PUBLISHED_SHA1:
        raise OriginalIndexError("Original index source differs from publisher SHA1")
    if len(raw) != OBSERVED_ORIGINAL_BYTES or hashlib.sha256(raw).hexdigest() != OBSERVED_ORIGINAL_SHA256:
        raise OriginalIndexError("Original full SHA256/size differs from observed source receipt")
    try:
        source=json.loads(raw.decode("utf-8-sig"),object_pairs_hook=_unique_pairs,
                          parse_constant=_reject_constant)
    except (ValueError,UnicodeError) as exc:
        raise OriginalIndexError("Malformed original GeoJSON document") from exc
    polygons=profile_index(source)
    if len(polygons) != OBSERVED_FEATURES:
        raise OriginalIndexError("Original tile-index population differs from observed receipt")
    return {
        "profile": "lu-act2019-original-lidar-tile-index-two-site-v0",
        "official_index_resource": OFFICIAL_INDEX,
        "original_index_bytes": len(raw),
        "publisher_sha1_verified": True,
        "original_index_sha1": sha1,
        "original_index_sha256": hashlib.sha256(raw).hexdigest(),
        "original_index_crs": "OGC:CRS84",
        "original_index_tile_polygons": len(polygons),
        "fixed_study_windows": site_coverage(polygons),
        "provider_catalogue_license_label": "CC0",
        "full_original_tile_zip_hashes_verified": False,
        "point_clouds_retrieved": False,
        "actual_lidar_building_classes_inspected": False,
        "upstream_shared_lineage_with_vdl_resolved": False,
        "independent_building_validation_completed": False,
        "commercial_source_rights_review_completed": False,
        "cat_exposure_model_input_admitted": False,
        "raw_original_urls_or_geometries_logged": False,
    }


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--original-index",required=True,type=Path)
    args=parser.parse_args(argv)
    try:
        report=verify_original(args.original_index)
    except OriginalIndexError as exc:
        # All error messages originate from constant, hand-reviewed stage labels.
        # Never print raw provider URL, per-tile coordinate or other original values.
        print("BLOCKED: reviewed original index rule: " + str(exc))
        return 2
    except (OSError,ValueError,TypeError):
        print("BLOCKED: original LiDAR2019 tile-index integrity or spatial preflight")
        return 2
    print(json.dumps(report,sort_keys=True,indent=2,allow_nan=False))
    return 0


if __name__=="__main__":
    raise SystemExit(main())
