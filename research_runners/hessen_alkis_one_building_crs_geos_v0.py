#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Original Hessen ALKIS one-building CRS/GEOS preflight, not CAT admission.

Read only the previously reviewed single-feature WFS URL. Validate raw
ETRS89 2D exterior topology with pinned Shapely; perform a PROJ-provided,
no-ballpark EPSG:4258 -> EPSG:4326 operation; quantify its reported
accuracy against WorldCover geographic pixel boundaries. Neither source
coordinates, source GML nor GEOS geometries are emitted/stored.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import sys
from urllib import request, error
from xml.etree import ElementTree as ET

from scripts import probe_hessen_alkis_one_gml_ring_v0 as gml
from scripts import probe_hessen_alkis_one_wfs_building_v0 as wfs

SOURCE = gml.SOURCE
URL = wfs.URL
MAX_BYTES = wfs.MAX_BYTES
TIMEOUT_SECONDS = wfs.TIMEOUT_SECONDS
MAX_VERTICES = 128
REQUIRED_PYPROJ = "3.7.2"
REQUIRED_SHAPELY = "2.1.2"
# Exact provider WorldCover 2021 v200 N48E009 geographic raster step.
PIXEL_STEP_DEGREES = 1/12000
GRID_WEST = 9.0
GRID_NORTH = 51.0
GRID_BLOCK_ROW = 5
GRID_BLOCK_COLUMN = 5
BLOCK_SIDE = 1024


class CRSBlocked(ValueError):
    """Original-source, geometry, coordinate-operation or accuracy gate failed."""


def _reviewed_transformer():
    try:
        import pyproj
        import shapely
        from pyproj import Transformer, Geod, aoi, network
        from shapely.geometry import Polygon
        from shapely.ops import transform as shapely_transform
    except ImportError as exc:
        raise CRSBlocked("pinned optional PyProj and Shapely runtime is mandatory") from exc
    if pyproj.__version__ != REQUIRED_PYPROJ or shapely.__version__ != REQUIRED_SHAPELY:
        raise CRSBlocked("unreviewed PyProj/Shapely library version")
    network.set_network_enabled(False)
    try:
        transformer=Transformer.from_crs(
            "EPSG:4258", "EPSG:4326", always_xy=True,
            allow_ballpark=False, only_best=True,
            area_of_interest=aoi.AreaOfInterest(9.47,50.50,9.50,50.54),
        )
    except Exception as exc:
        raise CRSBlocked("authoritative offline ETRS89 to WGS84 operation unavailable") from exc
    if (transformer.accuracy is None or not math.isfinite(transformer.accuracy)
            or not 0 < transformer.accuracy <= 1.0):
        raise CRSBlocked("source-to-WorldCover coordinate operation lacks <=1 m declared accuracy")
    return pyproj, shapely, Polygon, shapely_transform, Geod, transformer


def _source_polygon(raw: bytes):
    try:
        source=gml.inspect_gml_preflight(raw)
    except gml.RingBlocked as exc:
        raise CRSBlocked("original one-building GML preflight rejected source geometry") from exc
    if (source["polygon_surface_count"]!=1
            or source["exterior_ring_count"]!=1
            or source["interior_ring_count"]!=0
            or not source["all_rings_closed_nondegenerate_and_non_crossing"]
            or not source["all_coordinates_within_worldcover_original_block_extent"]):
        raise CRSBlocked("unreviewed original ALKIS polygon/multipart/holes or source geometry")
    try:
        root=ET.fromstring(raw)
        member=root.find(f"{{{wfs.WFS_NS}}}member")
        if member is None or len(member)!=1:
            raise CRSBlocked("source one-member WFS structure missing")
        building=member[0]
        surfaces=[
            item for item in building.iter()
            if item.tag in (f"{{{wfs.GML_NS}}}Polygon",
                            f"{{{wfs.GML_NS}}}PolygonPatch")
        ]
        if len(surfaces)!=1 or surfaces[0].tag != f"{{{wfs.GML_NS}}}Polygon":
            raise CRSBlocked("unsupported ALKIS GML surface type")
        rings=surfaces[0].findall(
            f"{{{wfs.GML_NS}}}exterior/{{{wfs.GML_NS}}}LinearRing"
        )
        if len(rings)!=1:
            raise CRSBlocked("unexpected exterior ring count")
        points=gml._ring_positions(rings[0])
    except (gml.RingBlocked,ET.ParseError) as exc:
        raise CRSBlocked("original GML polygon decoding failed") from exc
    if len(points)>MAX_VERTICES:
        raise CRSBlocked("unreviewed original polygon vertex budget")
    return source, points


def inspect_original_crs_and_topology(raw: bytes) -> dict:
    source, etrs_points=_source_polygon(raw)
    pyproj, shapely, Polygon, transform_geometry, Geod, transformer = _reviewed_transformer()
    etrs=Polygon(etrs_points)
    if not etrs.is_valid or etrs.is_empty or etrs.area <= 0:
        raise CRSBlocked("original ETRS89 polygon failed independent GEOS topology")
    try:
        wgs=transform_geometry(
            lambda lon,lat,z=None: transformer.transform(lon,lat,errcheck=True),
            etrs,
        )
    except Exception as exc:
        raise CRSBlocked("offline non-ballpark ETRS89-to-WGS84 transform failed") from exc
    if not wgs.is_valid or wgs.is_empty or wgs.area<=0:
        raise CRSBlocked("transformed WGS84 polygon failed GEOS topology")
    vertices=list(wgs.exterior.coords)
    if len(vertices)!=len(etrs_points):
        raise CRSBlocked("coordinate transform lost/added polygon vertices")
    if any(not math.isfinite(value) for point in vertices for value in point):
        raise CRSBlocked("nonfinite transformed WGS84 coordinate")

    xmin=GRID_WEST+GRID_BLOCK_COLUMN*BLOCK_SIDE*PIXEL_STEP_DEGREES
    xmax=GRID_WEST+(GRID_BLOCK_COLUMN+1)*BLOCK_SIDE*PIXEL_STEP_DEGREES
    ymax=GRID_NORTH-GRID_BLOCK_ROW*BLOCK_SIDE*PIXEL_STEP_DEGREES
    ymin=GRID_NORTH-(GRID_BLOCK_ROW+1)*BLOCK_SIDE*PIXEL_STEP_DEGREES
    margin=transformer.accuracy
    geod=Geod(ellps="WGS84")
    def segment_distance(lon1,lat1,lon2,lat2):
        return abs(geod.inv(lon1,lat1,lon2,lat2)[2])
    edge_mins=[]
    block_edge_mins=[]
    for lon,lat in vertices:
        near_lon=GRID_WEST+round((lon-GRID_WEST)/PIXEL_STEP_DEGREES)*PIXEL_STEP_DEGREES
        near_lat=GRID_NORTH-round((GRID_NORTH-lat)/PIXEL_STEP_DEGREES)*PIXEL_STEP_DEGREES
        edge_mins.append(min(
            segment_distance(lon,lat,near_lon,lat),
            segment_distance(lon,lat,lon,near_lat),
        ))
        block_edge_mins.append(min(
            segment_distance(lon,lat,xmin,lat),
            segment_distance(lon,lat,xmax,lat),
            segment_distance(lon,lat,lon,ymin),
            segment_distance(lon,lat,lon,ymax),
        ))
    in_block=all(
        xmin < lon < xmax and ymin < lat < ymax for lon,lat in vertices
    )
    all_vertices_beyond_block_margin=in_block and min(block_edge_mins)>margin
    # 1 m reported transformation accuracy can be larger than pixel-boundary
    # margins. This does NOT prove point/cell membership, entire-boundary
    # robustness, a land-cover classification or a WorldCover join.
    return {
        "profile":"oc-hessen-original-one-building-crs-geos-v0",
        "building_polygon_surfaces_from_original":1,
        "building_exterior_vertex_positions_including_closure":len(vertices),
        "original_epsg4258_geos_valid":True,
        "transformed_epsg4326_geos_valid":True,
        "coordinate_operation_accuracy_metres_declared":margin,
        "coordinate_operation_is_non_ballpark":True,
        "coordinate_operation_is_offline":True,
        "source_crs":"EPSG:4258",
        "raster_crs":"EPSG:4326",
        "coordinates_axis_order_handled":"GML_lat_lon_to_GIS_lon_lat",
        "wgs84_polygon_vertices_within_source_block":in_block,
        "all_vertices_more_than_operation_accuracy_from_block_edges":
            all_vertices_beyond_block_margin,
        "all_vertices_more_than_operation_accuracy_from_raster_grid_lines":
            min(edge_mins)>margin,
        "source_reported_number_returned":source["source_reported_number_returned"],
        "original_wfs_member_count":source["parsed_original_building_members"],
        "wfs_count_discrepancy_still_blocked":
            source["provider_count_discrepancy_remains_blocked"],
        "source_building_survey_vintage_verified":False,
        "building_geodetic_position_survey_grade_verified":False,
        "worldcover_2021_original_pixel_intersection_performed":False,
        "model_input_approved":False,
    }


def probe(*, open_request=wfs._open) -> dict:
    wfs.validate_frozen_getfeature()
    req=request.Request(
        URL,method="GET",
        headers={
            "Accept":"application/gml+xml,application/xml,text/xml",
            "Accept-Encoding":"identity",
            "User-Agent":"OpenCatastrophe-Hessen-OneBuilding-ETRS89-WGS84/0.1",
        },
    )
    try:
        with open_request(req,TIMEOUT_SECONDS) as response:
            if response.status!=200 or response.geturl()!=URL:
                raise CRSBlocked("unreviewed original WFS response status or URL")
            mime=response.headers.get("Content-Type","").split(";",1)[0].strip().lower()
            if mime not in ("application/xml","text/xml","application/gml+xml",
                            "application/vnd.ogc.gml","application/vnd.ogc.wfs_xml"):
                raise CRSBlocked("unreviewed original WFS GML MIME")
            if response.headers.get("Content-Encoding","identity").lower()!="identity":
                raise CRSBlocked("unreviewed transfer encoding")
            size=response.headers.get("Content-Length")
            if size is not None and (not size.isdigit() or int(size)>MAX_BYTES):
                raise CRSBlocked("unbounded original source Content-Length")
            raw=response.read(MAX_BYTES+1)
    except (CRSBlocked,wfs.CapabilityBlocked):
        raise
    except (error.URLError,error.HTTPError,TimeoutError,OSError) as exc:
        raise CRSBlocked("original single-feature WFS source unavailable") from exc
    details=inspect_original_crs_and_topology(raw)
    return {
        **details,
        "source_id":SOURCE,
        "original_source_request_sha256":
            hashlib.sha256(("GET "+URL).encode("ascii")).hexdigest(),
        "source_response_sha256":hashlib.sha256(raw).hexdigest(),
        "source_response_bytes":len(raw),
        "retrieved_utc":datetime.now(timezone.utc).isoformat(),
        "code_sha256":hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "pyproj_version":REQUIRED_PYPROJ,
        "shapely_version":REQUIRED_SHAPELY,
        "raw_source_geometry_or_address_persisted":False,
        "raw_building_coordinates_or_ids_emitted":False,
    }


def main(argv=None) -> int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--live",action="store_true")
    args=p.parse_args(argv)
    if not args.live:
        p.error("single reviewed official source requires explicit --live")
    try:
        print(json.dumps(probe(),sort_keys=True,allow_nan=False))
    except (CRSBlocked,gml.RingBlocked,wfs.BuildingFeatureBlocked,
            wfs.CapabilityBlocked,ValueError,OSError) as exc:
        print(json.dumps({"status":"BLOCKED","reason":str(exc),
                          "model_input_approved":False}),file=sys.stderr)
        return 1
    return 0


if __name__=="__main__":
    raise SystemExit(main())
