#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Original ACT GeoBase building digitization-source lineage in fixed 100m sites.

Never emit raw Source values except preapproved publisher-defined codes,
original IDs, geometries, addresses, coordinates, property values or matches.
A source label does not establish independent measurement or CAT admission.
"""
from __future__ import annotations

import argparse
from collections import Counter
import json
import math
from pathlib import Path
import tempfile

from research_runners.lu_act_address_geobase_original_window_v0 import (
    STUDY_SITES, HALFWIDTH_M, GEOBASE_ZIP_SHA, GEOBASE_GPKG_SHA,
    GEOBASE_NATIONAL_ROWS, EXPECTED_LAYER, MAX_GEOBASE_POLYGONS,
    _verified_geobase_gpkg,
)
from research_runners.luxembourg_gpkg_schema_window_v0 import (
    GeoPackageGateError, inspect as inspect_gpkg, identifier, decode_gpkg_wkb,
)

# Publisher BD-L-GeoBase original contents-description v1 (2024-09-24), BU
# field "Source": provenance of digitized building, not survey accuracy.
PUBLISHER_CODES = (
    "Bati3DACT", "Bati3DVDL", "PCN", "MO", "Ortho",
)
PROVENANCE_GROUPS = PUBLISHER_CODES + ("missing_label", "other_unreviewed")
ENCLOSING_RECTANGLE_COUNTS = {"luxembourg-city": 107, "berdorf-village": 18}
MAX_ORIGINAL_GEOMETRY_BYTES = 2 * 1024 * 1024


class SourceLineageError(ValueError):
    """Fail closed without revealing any source feature or unreviewed label."""


def summarize_source_codes(labels: list[object], *, expected: int) -> dict[str, int]:
    """Offline deterministic aggregate; unknown labels never echoed."""
    if (not isinstance(labels, list) or not isinstance(expected, int)
            or isinstance(expected, bool) or not 1 <= expected <= MAX_GEOBASE_POLYGONS
            or len(labels) != expected):
        raise SourceLineageError("Invalid or unconserved source-label sample")
    counts = Counter({code: 0 for code in PROVENANCE_GROUPS})
    for value in labels:
        if value is None or value == "":
            counts["missing_label"] += 1
        elif not isinstance(value, str) or len(value) > 128:
            raise SourceLineageError("Unreviewed original source-label type or length")
        elif value in PUBLISHER_CODES:
            counts[value] += 1
        else:
            counts["other_unreviewed"] += 1
    if sum(counts.values()) != expected:
        raise SourceLineageError("Source lineage counts do not conserve polygons")
    return {code: counts[code] for code in PROVENANCE_GROUPS}


def study_rect(site: str):
    """Exact equal-area quadrilateral in original EPSG:2169 metres."""
    if site not in STUDY_SITES:
        raise SourceLineageError("Unapproved geographic study site")
    try:
        from pyproj import Transformer
        from shapely.geometry import Polygon
    except ImportError as exc:
        raise SourceLineageError("Pinned GIS dependencies required") from exc
    lon, lat, exact_count = STUDY_SITES[site]
    project = Transformer.from_crs(4326,3035,always_xy=True)
    native = Transformer.from_crs(3035,2169,always_xy=True)
    x,y = project.transform(lon,lat)
    points = [native.transform(a,b) for a,b in (
        (x-HALFWIDTH_M,y-HALFWIDTH_M),
        (x+HALFWIDTH_M,y-HALFWIDTH_M),
        (x+HALFWIDTH_M,y+HALFWIDTH_M),
        (x-HALFWIDTH_M,y+HALFWIDTH_M),
    )]
    if not all(math.isfinite(v) for p in points for v in p):
        raise SourceLineageError("Invalid public study geometry")
    poly = Polygon(points)
    if poly.is_empty or not poly.is_valid or poly.area <= 0:
        raise SourceLineageError("Invalid public study area")
    return poly, exact_count


def inspect_site(conn, layer: dict, site: str) -> dict:
    """Read only original Source and geometry in the strict fixed area."""
    # Validate selected public site before importing optional spatial modules.
    study, expected = study_rect(site)
    try:
        from shapely import wkb
        from shapely.geometry import box
    except ImportError as exc:
        raise SourceLineageError("Pinned Shapely required") from exc
    if (layer["table"] != EXPECTED_LAYER or layer["feature_count"] != GEOBASE_NATIONAL_ROWS
            or layer["srs_id"] != 2169 or not layer["has_rtree"]
            or "Source" not in {field["name"] for field in layer["fields"]}
            or "geom" != layer["geometry_column"]):
        raise SourceLineageError("Original GeoBase building schema/rtree invalid")
    a,b,c,d = study.bounds
    table = identifier(layer["table"])
    geom = identifier(layer["geometry_column"])
    tree = identifier("rtree_"+layer["table"]+"_"+layer["geometry_column"])
    query = (
        f"SELECT b.Source, b.{geom} FROM {table} b JOIN {tree} r ON b.ROWID=r.id "
        "WHERE r.maxx>=? AND r.minx<=? AND r.maxy>=? AND r.miny<=? "
        "ORDER BY b.id LIMIT ?"
    )
    rows = conn.execute(query,(a,c,b,d,MAX_GEOBASE_POLYGONS+1)).fetchall()
    if len(rows) > MAX_GEOBASE_POLYGONS:
        raise SourceLineageError("RTree raw candidate count exceeded fixed limit")
    # The RTree query returns overlapping *envelope rectangles*, not necessarily
    # polygons intersecting even the enclosing native-coordinate rectangle.
    # Reproduce the prior GeoBase native-bbox geometric sampler exactly before
    # applying positive area clipping against the rotated EPSG:3035 square.
    enclosing_native = box(a,b,c,d)
    rectangle_polygon_count = 0
    observed_labels = []
    for label, blob in rows:
        if not isinstance(blob, bytes) or len(blob) > MAX_ORIGINAL_GEOMETRY_BYTES:
            raise SourceLineageError("Original geometry missing or over budget")
        try:
            geometry = wkb.loads(decode_gpkg_wkb(blob, 2169))
        except (ValueError, TypeError) as exc:
            raise SourceLineageError("Unreviewed original geometry encoding") from exc
        if (geometry.geom_type not in ("Polygon", "MultiPolygon")
                or geometry.is_empty or not geometry.is_valid or geometry.area <= 0):
            raise SourceLineageError("Invalid original building geometry")
        if not geometry.intersects(enclosing_native):
            continue
        rectangle_polygon_count += 1
        if geometry.intersects(study) and geometry.intersection(study).area > 0:
            observed_labels.append(label)
    if rectangle_polygon_count != ENCLOSING_RECTANGLE_COUNTS[site]:
        raise SourceLineageError("Geometry-filtered enclosing rectangle population drifted")
    if len(observed_labels) != expected:
        raise SourceLineageError("Original positive-area population drifted")
    return {
        "site": site,
        "raw_rtree_envelope_hits": len(rows),
        "enclosing_rectangle_polygon_candidates": rectangle_polygon_count,
        "rectangle_only_candidates_excluded": rectangle_polygon_count-len(observed_labels),
        "true_area_building_polygons": len(observed_labels),
        "publisher_source_categories": summarize_source_codes(observed_labels,expected=expected),
        "original_source_labels_per_feature_exported": False,
        "source_family_independence_verified": False,
        "physical_asset_identity_verified": False,
        "insured_exposure_admitted": False,
    }


def run(source_zip: Path) -> dict:
    if source_zip.is_symlink() or not source_zip.is_file():
        raise SourceLineageError("Original fixed GeoBase ZIP must be a local regular file")
    with tempfile.TemporaryDirectory(prefix="lu-geobase-source-origin-") as tmp:
        gpkg = _verified_geobase_gpkg(source_zip, Path(tmp))
        receipt, db = inspect_gpkg(gpkg, expected_sha256=GEOBASE_GPKG_SHA)
        try:
            layer = [x for x in receipt["layers"] if x["table"] == EXPECTED_LAYER]
            if len(layer) != 1:
                raise SourceLineageError("Expected one exact original building layer")
            sites = [inspect_site(db,layer[0],s) for s in STUDY_SITES]
        finally:
            db.close()
    return {
        "profile":"lu-act-geobase-20261001-building-provenance-two-site-v0",
        "original_zip_sha256":GEOBASE_ZIP_SHA,
        "original_gpkg_sha256":GEOBASE_GPKG_SHA,
        "national_original_building_objects":GEOBASE_NATIONAL_ROWS,
        "results":sites,
        "site_sampling_representative":False,
        "producer_code_means_independent_observation":False,
        "manual_source_adjudication_completed":False,
        "original_source_rows_exported":False,
        "commercial_reuse_review_completed":False,
        "model_input_admitted":False,
    }


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--geobase-zip",required=True,type=Path)
    args=parser.parse_args(argv)
    try:
        report=run(args.geobase_zip)
    except SourceLineageError as exc:
        # These are only fixed self-authored stage names, never provider text.
        print("BLOCKED: source-lineage gate: "+str(exc))
        return 2
    except (OSError,ValueError,GeoPackageGateError,TypeError):
        print("BLOCKED: original GeoBase source, schema, area or lineage gate failed")
        return 2
    print(json.dumps(report,indent=2,sort_keys=True,allow_nan=False))
    return 0


if __name__=="__main__":
    raise SystemExit(main())
