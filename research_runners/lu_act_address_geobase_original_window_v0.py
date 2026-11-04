#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Same-window original ACT 2026 addresses versus GeoBase building polygons.

Research-only; two previously published 100m research windows, full SHA-256
proof for both source families, ephemeral coordinates, aggregates only.
This does NOT establish independent ground truth or insured building identity.
"""
from __future__ import annotations

import argparse
from collections import Counter
import csv
import hashlib
import json
import math
from pathlib import Path
import tempfile
import zipfile

from research_runners.lu_bd_adresses_original_csv_quality_v0 import (
    EXPECTED_SHA256 as ADDRESS_SHA, EXPECTED_SIZE as ADDRESS_BYTES,
    HEADER as ADDRESS_HEADER, verify_original_stream,
)
from research_runners.luxembourg_geobase_2026_id_quality_v0 import (
    EXPECTED_ZIP_SHA256 as GEOBASE_ZIP_SHA,
    EXPECTED_GPKG_SHA256 as GEOBASE_GPKG_SHA,
    EXPECTED_FEATURE_COUNT as GEOBASE_NATIONAL_ROWS,
    EXPECTED_LAYER, MAX_GPKG_BYTES, audit as audit_geobase,
)
from research_runners.luxembourg_geobase_buildings_20261001_v0 import (
    GeoBaseError, _safe,
)
from research_runners.luxembourg_gpkg_schema_window_v0 import (
    GeoPackageGateError, inspect as inspect_gpkg, sample as sample_gpkg,
)

# Two predeclared public research locations, previously used in ACT-GIS work.
STUDY_SITES = {
    "luxembourg-city": (6.1319, 49.6116, 107),
    "berdorf-village": (6.348821, 49.820946, 16),
}
HALFWIDTH_M = 50.0
MAX_ADDRESSES_IN_WINDOW = 400
MAX_GEOBASE_POLYGONS = 400
NATIONAL_ADDRESS_ROWS = 179_768


class AddressFootprintError(ValueError):
    """Any source/coordinate/window/quality mismatch rejects this diagnostic."""


def classify(points, polygons):
    """Classify *candidate relations* only, never unique building identities.

    Points/polygons are already validated, projected to the same metric CRS.
    This bounded O(points × polygons) routine has no private source metadata.
    """
    if not isinstance(points, list) or not isinstance(polygons, list):
        raise AddressFootprintError("Synthetic point and polygon lists required")
    if not 1 <= len(points) <= MAX_ADDRESSES_IN_WINDOW or not 1 <= len(polygons) <= MAX_GEOBASE_POLYGONS:
        raise AddressFootprintError("Original spatial observation budget violated")
    if any(pt.geom_type != "Point" or pt.is_empty for pt in points):
        raise AddressFootprintError("Invalid address point")
    if any(poly.geom_type not in ("Polygon", "MultiPolygon") or poly.is_empty
           or not poly.is_valid or poly.area <= 0 for poly in polygons):
        raise AddressFootprintError("Invalid building polygon")
    counts = Counter()
    address_by_polygon = Counter()
    distances = []
    for point in points:
        interior = [i for i, poly in enumerate(polygons) if poly.contains(point)]
        border = [i for i, poly in enumerate(polygons) if poly.touches(point)]
        if len(interior) > 1:
            state = "multiple_containing_polygons"
        elif len(interior) == 1 and border:
            state = "interior_plus_boundary_ambiguity"
        elif len(interior) == 1:
            state = "one_containing_polygon_candidate"
            address_by_polygon[interior[0]] += 1
        elif border:
            state = "boundary_only_ambiguous"
        else:
            state = "no_intersecting_polygon"
            distances.append(min(poly.distance(point) for poly in polygons))
        counts[state] += 1
    if sum(counts.values()) != len(points):
        raise AddressFootprintError("Point classifications do not conserve source sample")
    # Include no actual coordinate, building ID or original address index.
    return {
        "address_points_sampled": len(points),
        "geobase_polygons_sampled": len(polygons),
        "status_counts": dict(sorted(counts.items())),
        "polygons_with_exactly_one_uniquely_contained_address": sum(v == 1 for v in address_by_polygon.values()),
        "polygons_without_uniquely_contained_sample_addresses": len(polygons) - len(address_by_polygon),
        "polygons_with_multiple_uniquely_contained_addresses": sum(v > 1 for v in address_by_polygon.values()),
        "addresses_in_such_polygons": sum(v for v in address_by_polygon.values() if v > 1),
        "outside_distance_mean_m": None if not distances else round(math.fsum(distances) / len(distances), 3),
        "outside_distance_max_m": None if not distances else round(max(distances), 3),
        "all_address_points_classified": True,
        "one_to_one_physical_building_identity_proven": False,
        "reference_source_independent": False,
        "cat_model_exposure_admitted": False,
    }


def _verified_geobase_gpkg(source_zip: Path, work: Path) -> Path:
    """Exact original ZIP + full CRC GPKG verify, with a single local extract."""
    receipt = audit_geobase(source_zip)
    if (receipt["original_zip_sha256"] != GEOBASE_ZIP_SHA
            or receipt["original_gpkg_sha256"] != GEOBASE_GPKG_SHA
            or receipt["counts"]["source_object_rows"] != GEOBASE_NATIONAL_ROWS):
        raise AddressFootprintError("GeoBase official original identity/count mismatch")
    target = work / "original-geobase.gpkg"
    with zipfile.ZipFile(source_zip) as archive:
        members = [x for x in archive.infolist() if x.filename.lower().endswith(".gpkg") and not x.is_dir()]
        if len(members) != 1:
            raise AddressFootprintError("Expected exactly one verified GeoPackage")
        member = members[0]
        _safe(member)
        if not 1 <= member.file_size <= MAX_GPKG_BYTES:
            raise AddressFootprintError("GeoPackage decompression budget exceeded")
        sha = hashlib.sha256()
        size = 0
        with archive.open(member) as inp, target.open("xb") as out:
            while block := inp.read(65536):
                size += len(block)
                if size > member.file_size or size > MAX_GPKG_BYTES:
                    raise AddressFootprintError("Unbounded original GeoPackage")
                sha.update(block)
                out.write(block)
        if size != member.file_size or sha.hexdigest() != GEOBASE_GPKG_SHA:
            raise AddressFootprintError("Extracted GPKG hash differs from original receipt")
    return target


def exact_area_candidates(polygons, native_window):
    """Reject bounding-box-only RTree samples and zero-area boundary touches."""
    if (not isinstance(polygons, list) or not 1 <= len(polygons) <= MAX_GEOBASE_POLYGONS
            or native_window.is_empty or not native_window.is_valid or native_window.area <= 0):
        raise AddressFootprintError("Invalid fixed exact-area polygon candidates")
    accepted = []
    for polygon in polygons:
        if (polygon.geom_type not in ("Polygon", "MultiPolygon") or polygon.is_empty
                or not polygon.is_valid or polygon.area <= 0):
            raise AddressFootprintError("Invalid original building geometry candidate")
        if polygon.intersects(native_window) and polygon.intersection(native_window).area > 0:
            accepted.append(polygon)
    if not accepted:
        raise AddressFootprintError("No positive-area building intersections in approved window")
    return accepted


def run(address_csv: Path, geobase_zip: Path, *, site: str = "luxembourg-city") -> dict:
    """Only original pinned data accepted, no original records or geometries emitted."""
    try:
        from pyproj import Transformer
        from shapely.geometry import box, Point, shape, Polygon
    except ImportError as exc:
        raise AddressFootprintError("Pinned PyProj/Shapely runtime required") from exc

    if site not in STUDY_SITES:
        raise AddressFootprintError("Unapproved original research site")
    centre_lon, centre_lat, expected_polygons = STUDY_SITES[site]
    if any(p.is_symlink() or not p.is_file() for p in (address_csv, geobase_zip)):
        raise AddressFootprintError("Original inputs must be local regular nonsymlink files")
    if address_csv.stat().st_size != ADDRESS_BYTES:
        raise AddressFootprintError("Original address source size drifted")
    with address_csv.open("rb") as f:
        address_receipt = verify_original_stream(f, transformer=Transformer.from_crs(2169,4326,always_xy=True))
    if (address_receipt["original_sha256_computed"] != ADDRESS_SHA
            or address_receipt["row_count"] != NATIONAL_ADDRESS_ROWS
            or address_receipt["missing_wgs84_pairs"] != 0
            or address_receipt["missing_luref_pairs"] != 0):
        raise AddressFootprintError("Verified national address dataset changed")

    to_3035 = Transformer.from_crs(4326, 3035, always_xy=True)
    to_2169 = Transformer.from_crs(3035, 2169, always_xy=True)
    cx, cy = to_3035.transform(centre_lon, centre_lat)
    square = box(cx-HALFWIDTH_M,cy-HALFWIDTH_M,cx+HALFWIDTH_M,cy+HALFWIDTH_M)
    corners = [to_2169.transform(x,y) for x,y in (
        (cx-HALFWIDTH_M,cy-HALFWIDTH_M),(cx+HALFWIDTH_M,cy-HALFWIDTH_M),
        (cx+HALFWIDTH_M,cy+HALFWIDTH_M),(cx-HALFWIDTH_M,cy+HALFWIDTH_M))]
    if not all(math.isfinite(a) and math.isfinite(b) for a,b in corners):
        raise AddressFootprintError("Non-finite local source bounding box")
    native_window = Polygon(corners)
    if native_window.is_empty or not native_window.is_valid or native_window.area <= 0:
        raise AddressFootprintError("Invalid transformed original research window")
    bbox = (min(x for x,y in corners), min(y for x,y in corners),
            max(x for x,y in corners), max(y for x,y in corners))

    with tempfile.TemporaryDirectory(prefix="lu-act-address-geobase-window-") as temp:
        working = Path(temp)
        gpkg = _verified_geobase_gpkg(geobase_zip, working)
        metadata, conn = inspect_gpkg(gpkg, expected_sha256=GEOBASE_GPKG_SHA)
        try:
            layers = [e for e in metadata["layers"] if e["table"] == EXPECTED_LAYER]
            if (len(layers) != 1 or layers[0]["feature_count"] != GEOBASE_NATIONAL_ROWS
                    or layers[0]["srs_id"] != 2169):
                raise AddressFootprintError("Unexpected original building layer or CRS")
            local_geojson = working / "local-buildings.geojson"
            building_count = sample_gpkg(conn,layers[0],id_field="BU_BuildingID",
                                         bbox=bbox,limit=MAX_GEOBASE_POLYGONS,output=local_geojson)
        finally:
            conn.close()
        provider_geojson = json.loads(local_geojson.read_text(encoding="utf-8"))
        if provider_geojson.get("type") != "FeatureCollection" or len(provider_geojson.get("features",[])) != building_count:
            raise AddressFootprintError("Unexpected bounded original geometry collection")
        # RTree is an enclosing rectangle, so remove zero-area/bbox-only hits.
        polygons = exact_area_candidates(
            [shape(item["geometry"]) for item in provider_geojson["features"]],
            native_window,
        )
        if len(polygons) != expected_polygons:
            raise AddressFootprintError(f"Exact-area aggregate polygon count at {site}: observed {len(polygons)}; previously observed {expected_polygons}")
        # All points are compared in native EPSG2169 metre coordinates. Only
        # the WGS84 versions decide the independent, frozen EPSG3035 window.
        points = []
        case_keys = set()
        repeated_case_ids = 0
        read_count = 0
        with address_csv.open("r", encoding="utf-8-sig", newline="") as stream:
            reader = csv.reader(stream, delimiter=";", strict=True)
            if tuple(next(reader)) != ADDRESS_HEADER:
                raise AddressFootprintError("Original address field contract drifted")
            for row in reader:
                read_count += 1
                if len(row) != len(ADDRESS_HEADER):
                    raise AddressFootprintError("Unreviewed original address schema")
                lon, lat = float(row[7]), float(row[6])
                wx, wy = to_3035.transform(lon, lat)
                if not math.isfinite(wx) or not math.isfinite(wy):
                    raise AddressFootprintError("Non-finite transformed source address")
                if square.covers(Point(wx,wy)):
                    points.append(Point(float(row[8]),float(row[9])))
                    if len(points) > MAX_ADDRESSES_IN_WINDOW:
                        raise AddressFootprintError("Address count exceeds predeclared research sample")
                    # The ephemeral address IDs are never exported or logged.
                    key = row[5]
                    repeated_case_ids += key in case_keys
                    case_keys.add(key)
        if read_count != NATIONAL_ADDRESS_ROWS:
            raise AddressFootprintError("Original source population changed between reads")
        if not points:
            raise AddressFootprintError("No official address points within fixed window")
        result = classify(points, polygons)
    return {
        "profile": "lu-act20261102-address-vs-geobase20261001-original-100m-v0",
        "study_site": site,
        "study_area": "fixed 100m x 100m EPSG3035 original research window",
        "original_source_evidence": {
            "address_csv_sha256": ADDRESS_SHA,
            "address_csv_national_rows": NATIONAL_ADDRESS_ROWS,
            "geobase_buildings_zip_sha256": GEOBASE_ZIP_SHA,
            "geobase_buildings_gpkg_sha256": GEOBASE_GPKG_SHA,
            "geobase_buildings_national_rows": GEOBASE_NATIONAL_ROWS,
            "address_snapshot": "2026-11-02",
            "building_snapshot": "2026-10-01",
        },
        "within_window_repeated_address_id_rows": int(repeated_case_ids),
        **result,
        "same_national_act_provider_family": True,
        "cross_vintage_evolution_checked": False,
        "original_records_exported": False,
        "individual_match_pairs_published": False,
        "insured_tiv_inferred": False,
        "commercial_rights_admitted": False,
        "scientific_model_admission": False,
    }


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--address-csv", required=True, type=Path)
    p.add_argument("--geobase-zip", required=True, type=Path)
    p.add_argument("--site", choices=tuple(STUDY_SITES), default="luxembourg-city")
    args = p.parse_args(argv)
    try:
        result = run(args.address_csv, args.geobase_zip, site=args.site)
    except AddressFootprintError as exc:
        # Only enumerated public sites and bounded aggregate counts are permitted
        # in these self-authored messages. Never include source record values,
        # provider row data, original addresses or geometry coordinates.
        p.exit(2,"BLOCKED: reviewed original-stage rule: "+str(exc)+"\n")
    except (GeoBaseError, GeoPackageGateError,
            OSError, UnicodeError, ValueError, RuntimeError, csv.Error,
            zipfile.BadZipFile, OverflowError):
        p.exit(2,"BLOCKED: exact original source or geometry contract failed\n")
    print(json.dumps(result,ensure_ascii=False,sort_keys=True,indent=2,allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
