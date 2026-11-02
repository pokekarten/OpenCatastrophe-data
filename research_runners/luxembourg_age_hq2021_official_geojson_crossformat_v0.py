# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Publisher-original AGE HWGK2021 GeoJSON independent shapefile geometry challenge.

The *publisher* also publishes GeoJSON for HQ10/HQ100/HQext, with separately
reported SHA-1 checksums. Read these exact original bytes only in transient
CI memory. Derive aggregate feature/polygon/ring/XY counts and coordinate
domain, then compare them to source-original ZIP SHP counts. NEVER export
source geometry, feature identifiers, locations or numeric depth values.

Provider GeoJSON geometry is an alternate original representation, NOT proof
of scientifically correct 2021 flood intensity, source geometry topology,
insured asset exposure or CAT loss-model eligibility.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import re

MAX_GEOJSON_BYTES = 96 * 1024 * 1024
MAX_FEATURES = 100000
MAX_POLYGONS = 100000
MAX_RINGS = 100000
MAX_POINTS = 4_000_000

SOURCES = {
    "hq10": {
        "catalogue": "https://data.public.lu/en/datasets/flood-hazard-maps-10-year-flood/",
        "resource_id": "183d2084-543a-48a2-9471-67223ae98d03",
        "url": ("https://download.data.public.lu/resources/"
                "flood-hazard-maps-10-year-flood/20220613-155146/hwgk2021-hq10.geojson"),
        "sha1": "aeeaa1555eb769560d3d83c1e32450ee6a78e755",
        "shp_rings": 13439,
        "shp_points": 1493429,
    },
    "hq100": {
        "catalogue": "https://data.public.lu/en/datasets/flood-hazard-maps-100-year-flood/",
        "resource_id": "6fc9a735-4795-4841-9f00-ab874a111346",
        "url": ("https://download.data.public.lu/resources/"
                "flood-hazard-maps-100-year-flood/20220613-154835/hwgk2021-hq100.geojson"),
        "sha1": "070966eac7451d9a4f5aeba1d2b7a3f25bf07f51",
        "shp_rings": 6379,
        "shp_points": 1336393,
    },
    "hqext": {
        "catalogue": "https://data.public.lu/en/datasets/flood-hazard-maps-extreme/",
        "resource_id": "209e35f0-f3ce-460f-83f0-062c2ea76637",
        "url": ("https://download.data.public.lu/resources/"
                "flood-hazard-maps-extreme/20220613-154535/hwgk2021-hqext.geojson"),
        "sha1": "c85a4b3de65170fa93406ef76a77ccfd4cf75124",
        "shp_rings": 5108,
        "shp_points": 1288014,
    },
}


class OriginalGeoJSONError(ValueError):
    """The exact original publisher GeoJSON failed a guarded research gate."""


def _reject_nonfinite_constant(value: str):
    raise OriginalGeoJSONError("Nonfinite JSON numeric constant in original source")


def profile_original_geojson(obj: dict, *, scenario: str) -> dict:
    if scenario not in SOURCES or not isinstance(obj, dict):
        raise OriginalGeoJSONError("Unknown scenario or publisher source root")
    kind = obj.get("type")
    if kind == "FeatureCollection":
        features = obj.get("features")
        if not isinstance(features, list) or not 1 <= len(features) <= MAX_FEATURES:
            raise OriginalGeoJSONError("Invalid source FeatureCollection")
    elif kind == "Feature":
        features = [obj]
    elif kind in ("Polygon", "MultiPolygon"):
        features = [{"geometry": obj, "properties": {}}]
    else:
        raise OriginalGeoJSONError("Unsupported publisher original root object")

    geom_type_counts = {"Polygon": 0, "MultiPolygon": 0}
    num_polygons = num_rings = num_points = num_holes = 0
    closed_rings = nonfinite = 0
    mins = [math.inf, math.inf]
    maxs = [-math.inf, -math.inf]
    field_names = set()
    coordinate_lengths = set()
    for feature in features:
        if not isinstance(feature, dict):
            raise OriginalGeoJSONError("Invalid original feature")
        properties = feature.get("properties")
        if properties is not None:
            if not isinstance(properties, dict) or len(properties) > 128:
                raise OriginalGeoJSONError("Invalid publisher source property schema")
            for raw_name in properties:
                if not isinstance(raw_name, str):
                    raise OriginalGeoJSONError("Nonnumeric source property field")
                field_names.add(raw_name if re.fullmatch(r"[A-Za-z0-9_]{1,48}", raw_name)
                                else "[nonstandard-name]")
            if len(field_names) > 128:
                raise OriginalGeoJSONError("Oversized source property schema")
        geom = feature.get("geometry")
        if not isinstance(geom, dict):
            raise OriginalGeoJSONError("Missing original feature geometry")
        shape = geom.get("type")
        if shape not in geom_type_counts:
            raise OriginalGeoJSONError("Nonpolygon original source geometry")
        geom_type_counts[shape] += 1
        coordinates = geom.get("coordinates")
        if not isinstance(coordinates, (list, tuple)):
            raise OriginalGeoJSONError("Source geometry coordinates not a list")
        polygons = [coordinates] if shape == "Polygon" else coordinates
        if not polygons or num_polygons + len(polygons) > MAX_POLYGONS:
            raise OriginalGeoJSONError("No source polygons or unbounded population")
        for polygon in polygons:
            if not isinstance(polygon, (list, tuple)) or not polygon:
                raise OriginalGeoJSONError("Empty original polygon")
            num_polygons += 1
            num_holes += len(polygon) - 1
            if num_rings + len(polygon) > MAX_RINGS:
                raise OriginalGeoJSONError("Unbounded original rings")
            for ring in polygon:
                if not isinstance(ring, (list, tuple)) or len(ring) < 4:
                    raise OriginalGeoJSONError("Incomplete original polygon ring")
                num_rings += 1
                if num_points + len(ring) > MAX_POINTS:
                    raise OriginalGeoJSONError("Original coordinate count exceeds research gate")
                start = end = None
                for point in ring:
                    if not isinstance(point, (list, tuple)) or len(point) not in (2, 3):
                        raise OriginalGeoJSONError("Unexpected original point dimensions")
                    coordinate_lengths.add(len(point))
                    try:
                        x, y = float(point[0]), float(point[1])
                    except (TypeError, ValueError, OverflowError) as exc:
                        raise OriginalGeoJSONError("Unusable source XY") from None
                    if not math.isfinite(x) or not math.isfinite(y):
                        nonfinite += 1
                        raise OriginalGeoJSONError("Nonfinite original source XY")
                    for index, val in enumerate((x, y)):
                        mins[index] = min(mins[index], val)
                        maxs[index] = max(maxs[index], val)
                    if start is None:
                        start = (x, y)
                    end = (x, y)
                closed_rings += start == end
                num_points += len(ring)
    if not all(math.isfinite(x) for x in (*mins, *maxs)) or (
            mins[0] >= maxs[0] or mins[1] >= maxs[1]):
        raise OriginalGeoJSONError("Empty or invalid published geographic extent")

    x0, y0 = mins
    x1, y1 = maxs
    domain = ("looks_luxembourg_longitude_latitude" if
              5.5 < x0 < x1 < 6.9 and 49.0 < y0 < y1 < 50.6 else
              "looks_luxembourg_projected_EPSG2169" if
              40000 < x0 < x1 < 115000 and 50000 < y0 < y1 < 150000 else
              "unrecognized_coordinate_domain")
    reference = SOURCES[scenario]
    return {
        "original_geojson_root_type": kind,
        "source_feature_count": len(features),
        "geometry_type_counts": geom_type_counts,
        "original_publisher_polygon_group_count": num_polygons,
        "original_publisher_ring_parts": num_rings,
        "original_publisher_hole_ring_count_from_grouping": num_holes,
        "original_publisher_point_pairs": num_points,
        "original_source_coordinate_dimensions": sorted(coordinate_lengths),
        "closed_publisher_rings": closed_rings,
        "open_publisher_rings": num_rings - closed_rings,
        "all_original_coordinate_pairs_finite": nonfinite == 0,
        "source_coordinate_domain_hypothesis": domain,
        "original_publisher_bbox_rounded_4dp": [round(x0, 4), round(y0, 4),
                                                 round(x1, 4), round(y1, 4)],
        "source_property_field_names_only": sorted(field_names),
        "ring_count_matches_original_publisher_shapefile": num_rings == reference["shp_rings"],
        "point_count_matches_original_publisher_shapefile": num_points == reference["shp_points"],
        "GeoJSON_source_polygon_holes_are_hydraulically_verified": False,
        "GeoJSON_and_SHP_topological_sets_proven_equal": False,
        "WGS84_to_LUREF_transform_ground_verified": False,
        "source_feature_ids_values_or_geometries_exported": False,
        "numeric_hazard_depth_units_or_values_verified": False,
        "insurer_CAT_model_input_admitted": False,
        "neon_database_modified": False,
    }


def audit(original: Path, *, scenario: str, review_polygon_groups=False) -> dict:
    if scenario not in SOURCES:
        raise OriginalGeoJSONError("Unknown original publisher source scenario")
    p = Path(original)
    if (p.is_symlink() or not p.is_file() or
            not 0 < p.stat().st_size <= MAX_GEOJSON_BYTES):
        raise OriginalGeoJSONError("Missing/oversized original publisher file")
    h1, h2 = hashlib.sha1(), hashlib.sha256()
    with p.open("rb") as f:
        while chunk := f.read(1024 * 1024):
            h1.update(chunk)
            h2.update(chunk)
    expected = SOURCES[scenario]
    if h1.hexdigest() != expected["sha1"]:
        raise OriginalGeoJSONError("Publisher original GeoJSON SHA-1 differs from catalogue")
    try:
        with p.open("r", encoding="utf-8-sig") as f:
            obj = json.load(f, parse_constant=_reject_nonfinite_constant)
    except (ValueError, UnicodeError, RecursionError, TypeError, OverflowError):
        # Do not expose source coordinate-bearing parser failures.
        raise OriginalGeoJSONError("Original publisher JSON parser rejected file") from None
    profile = profile_original_geojson(obj, scenario=scenario)
    topology = {}
    if review_polygon_groups:
        from research_runners.luxembourg_age_hq2021_geojson_group_ogc_v0 import (
            GroupTopologyError, challenge_publisher_groups,
        )
        try:
            topology = challenge_publisher_groups(obj)
        except GroupTopologyError:
            raise OriginalGeoJSONError("Original polygon group GEOS diagnostic blocked") from None
        if topology["original_publisher_groups_examined"] != profile["original_publisher_polygon_group_count"]:
            raise OriginalGeoJSONError("Original publisher geometry group count not conserved")
    return {
        "profile": "lu-age-hq2021-original-publisher-geojson-crossformat-v0",
        "scenario": scenario,
        "official_catalogue_url": expected["catalogue"],
        "source_original_url": expected["url"],
        "source_original_resource_id": expected["resource_id"],
        "published_source_sha1_matches": True,
        "observed_independent_sha256": h2.hexdigest(),
        "source_original_bytes": p.stat().st_size,
        **profile,
        **({"independent_publisher_group_OGC_diagnostic": topology} if review_polygon_groups else {}),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scenario", choices=tuple(SOURCES), required=True)
    parser.add_argument("--source-geojson", type=Path, required=True)
    parser.add_argument("--review-polygon-groups", action="store_true")
    args = parser.parse_args()
    try:
        print(json.dumps(audit(args.source_geojson, scenario=args.scenario,
                               review_polygon_groups=args.review_polygon_groups),
                         sort_keys=True, indent=2, allow_nan=False))
    except (OriginalGeoJSONError, OSError):
        parser.exit(2, "BLOCKED: Official publisher GeoJSON source integrity or format rejected\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
