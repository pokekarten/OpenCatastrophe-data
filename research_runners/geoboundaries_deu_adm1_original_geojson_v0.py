#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Bounded, SHA-256-pinned original geoBoundaries DEU ADM1 GeoJSON quality gate.

Only examines an externally provided file. No downloader, database writes, raw
features, coordinates or provider-owned identifiers are output. Connectivity
and reuse rights are separately reviewed; geometry is not insured exposure.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import sys
from typing import Any

SOURCE_GIT_COMMIT = "9469f09"
BOUNDARY_ID = "DEU-ADM1-10402087"
DATA_YEAR = 2021
SOURCE_URL = (
    "https://media.githubusercontent.com/media/wmgeolab/geoBoundaries/"
    "9469f09/releaseData/gbOpen/DEU/ADM1/geoBoundaries-DEU-ADM1.geojson"
)
SOURCE_LFS_OID_SHA256 = "56e069593595c5006e7044d46b023c2afc6b4a109a669b570ee229e758c00682"
SOURCE_LFS_SIZE = 6_254_151
MAX_SOURCE_BYTES = 7_340_032
MAX_VERTICES = 750_000
EXPECTED_FEATURES = 16
# Guard against a silently wrong CRS, longitude/latitude axis flip or country.
GEOGRAPHIC_EXTENT_CEILING = (5.0, 47.0, 16.0, 56.0)
# 1e-8 square degrees is a conservative *diagnostic* gate, not an area
# estimate suitable for actuarial exposure or border dispute adjudication.
MAX_OVERLAP_DEGREES_SQUARED = 1e-8


class BoundaryGeometryError(ValueError):
    """Fail-closed source identity, metadata or spatial integrity violation."""


def _obj(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    out = {}
    for key, value in pairs:
        if key in out:
            raise BoundaryGeometryError("duplicate JSON property")
        out[key] = value
    return out


def _nonfinite(_value: str) -> None:
    raise BoundaryGeometryError("non-finite JSON number")


def _text(value: Any, name: str) -> str:
    if type(value) is not str or not value.strip() or len(value) > 500:
        raise BoundaryGeometryError(f"invalid or missing provider {name}")
    return value


def inspect_geojson_bytes(
    raw: bytes, *, expected_sha256: str, expected_size: int,
) -> dict[str, Any]:
    """Validate one exact provider byte image; fixture hashes permitted in tests.

    No automatic extraction of point locations or building/insurance exposure.
    """
    if type(raw) is not bytes or not 0 < len(raw) <= MAX_SOURCE_BYTES:
        raise BoundaryGeometryError("source file is empty or exceeds byte budget")
    if len(raw) != expected_size:
        raise BoundaryGeometryError("original LFS byte count mismatch (pointer file?)")
    actual = hashlib.sha256(raw).hexdigest()
    if actual != expected_sha256:
        raise BoundaryGeometryError("original LFS SHA-256 mismatch")
    if raw.startswith(b"version https://git-lfs.github.com/spec/"):
        raise BoundaryGeometryError("Git LFS pointer is not GeoJSON")
    try:
        document = json.loads(raw.decode("utf-8"), object_pairs_hook=_obj,
                              parse_constant=_nonfinite)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise BoundaryGeometryError("invalid UTF-8 GeoJSON") from exc
    if type(document) is not dict or document.get("type") != "FeatureCollection":
        raise BoundaryGeometryError("original must be a GeoJSON FeatureCollection")
    crs = document.get("crs")
    if crs is not None and crs not in (
        {"type": "name", "properties": {"name": "EPSG:4326"}},
        {"type": "name", "properties": {"name": "urn:ogc:def:crs:OGC:1.3:CRS84"}},
    ):
        raise BoundaryGeometryError("unexpected embedded source CRS declaration")
    features = document.get("features")
    if type(features) is not list or len(features) != EXPECTED_FEATURES:
        raise BoundaryGeometryError("expected exactly 16 DEU ADM1 polygons")
    try:
        import shapely
        from shapely.geometry import shape
    except ImportError as exc:
        raise BoundaryGeometryError("optional reviewed Shapely dependency missing") from exc

    seen_ids: set[str] = set()
    seen_names: set[str] = set()
    geometries = []
    total_vertices = 0
    overall = [math.inf, math.inf, -math.inf, -math.inf]
    for feature in features:
        if type(feature) is not dict or feature.get("type") != "Feature":
            raise BoundaryGeometryError("unexpected feature kind")
        props = feature.get("properties")
        if type(props) is not dict:
            raise BoundaryGeometryError("feature properties missing")
        source_id = _text(props.get("shapeID"), "shapeID")
        name = _text(props.get("shapeName"), "shapeName")
        if _text(props.get("shapeGroup"), "shapeGroup") != "DEU":
            raise BoundaryGeometryError("feature country identity drift")
        if _text(props.get("shapeType"), "shapeType") != "ADM1":
            raise BoundaryGeometryError("feature administrative level drift")
        if source_id in seen_ids or name in seen_names:
            raise BoundaryGeometryError("duplicate admin identifier/name")
        seen_ids.add(source_id)
        seen_names.add(name)
        geom_doc = feature.get("geometry")
        if type(geom_doc) is not dict or geom_doc.get("type") not in ("Polygon", "MultiPolygon"):
            raise BoundaryGeometryError("non-polygon provider geometry")
        try:
            geom = shape(geom_doc)
        except (TypeError, ValueError, IndexError) as exc:
            raise BoundaryGeometryError("unparseable source polygon") from exc
        if geom.is_empty or not geom.is_valid or geom.area <= 0:
            raise BoundaryGeometryError("empty, invalid or zero-area source polygon")
        if bool(shapely.has_z(geom)):
            raise BoundaryGeometryError("unexpected Z coordinate")
        coords = shapely.get_coordinates(geom)
        total_vertices += len(coords)
        if total_vertices > MAX_VERTICES:
            raise BoundaryGeometryError("polygon vertex budget exceeded")
        if not all(math.isfinite(float(p)) for row in coords for p in row):
            raise BoundaryGeometryError("non-finite longitude or latitude")
        xmin, ymin, xmax, ymax = tuple(float(n) for n in geom.bounds)
        if not (
            GEOGRAPHIC_EXTENT_CEILING[0] <= xmin <= xmax <= GEOGRAPHIC_EXTENT_CEILING[2]
            and GEOGRAPHIC_EXTENT_CEILING[1] <= ymin <= ymax <= GEOGRAPHIC_EXTENT_CEILING[3]
        ):
            raise BoundaryGeometryError("geometry coordinates are outside Germany WGS84 ceiling")
        overall[0] = min(overall[0], xmin)
        overall[1] = min(overall[1], ymin)
        overall[2] = max(overall[2], xmax)
        overall[3] = max(overall[3], ymax)
        geometries.append(geom)

    # The diagnostic is bounded by 16 states. Only polygonal intersection
    # area is considered: normal shared borders have zero area. Do not infer
    # nationwide completeness from these 16 independent polygons.
    max_overlap = 0.0
    for i, left in enumerate(geometries):
        for right in geometries[i + 1:]:
            if not left.intersects(right):
                continue
            overlap = float(left.intersection(right).area)
            if not math.isfinite(overlap):
                raise BoundaryGeometryError("non-finite inter-feature overlap")
            max_overlap = max(overlap, max_overlap)
            if overlap > MAX_OVERLAP_DEGREES_SQUARED:
                raise BoundaryGeometryError("material overlapping source ADM1 polygons")

    return {
        "profile": "oc-geoboundaries-deu-adm1-full-geojson-research-v0",
        "source_id": "geoboundaries.gbopen",
        "boundary_id_from_reviewed_metadata": BOUNDARY_ID,
        "source_github_commit": SOURCE_GIT_COMMIT,
        "year_represented_from_reviewed_metadata": DATA_YEAR,
        "source_geojson_sha256": actual,
        "source_geojson_bytes": len(raw),
        "features": EXPECTED_FEATURES,
        "unique_feature_ids": len(seen_ids),
        "unique_names": len(seen_names),
        "total_polygon_coordinates": total_vertices,
        "all_polygons_ogc_valid": True,
        "max_polygon_intersection_square_degrees": round(max_overlap, 12),
        "wgs84_bbox_rounded_3dp": [round(v, 3) for v in overall],
        "coordinate_reference_system": "WGS84 longitude-latitude assumed from GeoJSON; geographic extent sanity checked",
        "source_metadata_crs_declared": crs is not None,
        "provider_bytes_persisted": False,
        "building_exposure_present": False,
        "insurance_data_present": False,
        "source_geometry_admitted_to_model": False,
    }


def inspect_original_file(path: Path) -> dict[str, Any]:
    if not path.is_file() or path.is_symlink():
        raise BoundaryGeometryError("expected regular non-symlink local original file")
    stat = path.stat()
    if stat.st_size != SOURCE_LFS_SIZE:
        raise BoundaryGeometryError("original pinned LFS size mismatch")
    with path.open("rb") as f:
        raw = f.read(MAX_SOURCE_BYTES + 1)
    return inspect_geojson_bytes(raw, expected_sha256=SOURCE_LFS_OID_SHA256,
                                 expected_size=SOURCE_LFS_SIZE)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--original-geojson", type=Path, required=True,
                   help="separately acquired, pinned Git-LFS original (not a pointer)")
    args = p.parse_args(argv)
    try:
        print(json.dumps(inspect_original_file(args.original_geojson), sort_keys=True,
                         indent=2, allow_nan=False))
    except (BoundaryGeometryError, OSError, ValueError) as exc:
        print(f"BLOCKED: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
