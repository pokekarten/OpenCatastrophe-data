#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""One WFS Building × original WorldCover raster: research-only pixel comparison.

Four pre-reviewed original GETs total: one fixed Hessen COUNT=1 WFS GML
and the previously approved 4KiB+10368B+56442B WorldCover TIFF ranges.
No raw GML, positions, original pixel data or GIS objects ever exported or
saved. The WFS 'numberReturned=0 vs one member' contradiction still blocks
building/model admission. Pixel shifts are NOT physical-metre uncertainty.
"""
from __future__ import annotations

import argparse
from collections import defaultdict
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import sys
from urllib import error, request
import zlib

from research_runners import hessen_alkis_one_building_crs_geos_v0 as hessen
from scripts import probe_hessen_alkis_one_wfs_building_v0 as wfs
from scripts import probe_esa_worldcover_classified_block185_v0 as wc
from scripts.worldcover_synthetic_grid_shift_sensitivity_v0 import OFFSETS
from scripts.worldcover_synthetic_polygon_overlap_v0 import (
    SIDE, VALID_CODES, SCALE,
)

MAX_CANDIDATE_CELLS = 256
MIN_AREA_PIXEL_SQUARES = 0.000001


class PairBlocked(ValueError):
    """Unapproved original pairing or excessive topology/pixel work."""


def _class_distribution(source_pixels: bytes, polygon, *, box):
    """Exact GEOS pixel-square intersections, no copied pixel/ring output."""
    if polygon.is_empty or not polygon.is_valid or polygon.area < MIN_AREA_PIXEL_SQUARES:
        raise PairBlocked("invalid or sub-resolution one-building comparison polygon")
    left,bottom,right,top = polygon.bounds
    if not (0 < left < right < SIDE and 0 < bottom < top < SIDE):
        raise PairBlocked("one building or shift spills outside frozen TIFF block")
    c0,c1=math.floor(left),math.ceil(right)
    r0,r1=math.floor(bottom),math.ceil(top)
    if (c1-c0)*(r1-r0)>MAX_CANDIDATE_CELLS:
        raise PairBlocked("source feature exceeds bounded 256 candidate raster cells")
    weighted=defaultdict(float)
    cells=0
    for row in range(r0,r1):
        for column in range(c0,c1):
            fraction=polygon.intersection(box(column,row,column+1,row+1)).area
            if fraction<=1e-12:
                continue
            code=source_pixels[row*SIDE+column]
            if code not in VALID_CODES:
                raise PairBlocked("invalid original ESA pixel class")
            weighted[code]+=fraction
            cells+=1
    area=sum(weighted.values())
    if not area or abs(area-polygon.area)>max(1e-8,polygon.area*1e-5):
        raise PairBlocked("source polygon pixel area did not conserve GEOS area")
    return {
        code:value/area for code,value in weighted.items()
    },cells


def inspect_original_pair(wfs_raw: bytes, source_pixels: bytes) -> dict:
    """Parse original source geometry in memory; output only bounded aggregates."""
    if type(source_pixels) is not bytes or len(source_pixels)!=SIDE*SIDE:
        raise PairBlocked("one verified 1024x1024 source class block required")
    if len(OFFSETS)!=17 or OFFSETS[0]!=(0.0,0.0):
        raise PairBlocked("synthetic sensitivity shift budget drift")
    # Existing original GML, count contradiction, shape, CRS and provider checks
    # remain authoritative. Never normalize the provider numberReturned field.
    try:
        audit=hessen.inspect_original_crs_and_topology(wfs_raw)
        source, etrs_points=hessen._source_polygon(wfs_raw)
        pyproj, shapely, Polygon, transform_geometry, Geod, transformer = (
            hessen._reviewed_transformer()
        )
        from shapely.affinity import translate
        from shapely.geometry import box
    except (hessen.CRSBlocked, ImportError, ValueError) as exc:
        raise PairBlocked("original Building CRS/GEOS preflight blocked") from exc

    if (not audit["original_epsg4258_geos_valid"]
            or not audit["transformed_epsg4326_geos_valid"]
            or not audit["wgs84_polygon_vertices_within_source_block"]
            or not audit["all_vertices_more_than_operation_accuracy_from_block_edges"]
            or audit["coordinate_operation_accuracy_metres_declared"]>1
            or audit["model_input_approved"] is not False
            or source["provider_count_discrepancy_remains_blocked"] is not True
            or source["parsed_original_building_members"]!=1):
        raise PairBlocked("original source Count/CRS/GEOS uncertainty gates not satisfied")

    etrs=Polygon(etrs_points)
    if not etrs.is_valid or etrs.is_empty:
        raise PairBlocked("independently invalid original ETRS89 source ring")
    try:
        wgs=transform_geometry(
            lambda lon,lat,z=None: transformer.transform(lon,lat,errcheck=True),etrs
        )
        grid=transform_geometry(
            lambda lon,lat,z=None: (
                (lon-9.0)/SCALE - 5*SIDE,
                (51.0-lat)/SCALE - 5*SIDE,
            ),wgs
        )
    except Exception as exc:
        raise PairBlocked("failed reviewed source CRS to exact WorldCover pixel grid") from exc
    if not grid.is_valid or grid.is_empty or grid.area<=0:
        raise PairBlocked("transformed original source polygon invalid in pixel grid")

    all_shares=[]
    cell_counts=[]
    try:
        for dx,dy in OFFSETS:
            shifted=translate(grid,xoff=dx,yoff=dy)
            shares,touched=_class_distribution(source_pixels,shifted,box=box)
            all_shares.append(shares)
            cell_counts.append(touched)
    except (ValueError,IndexError,OverflowError,ArithmeticError) as exc:
        raise PairBlocked("invalid original pixel+geometry source comparison") from exc
    classes=sorted(set().union(*(set(s) for s in all_shares)))
    base=all_shares[0]
    changes=[
        sum(abs(share.get(k,0)-base.get(k,0)) for k in classes)/2
        for share in all_shares
    ]
    if not all(math.isfinite(delta) and 0<=delta<=1+1e-6 for delta in changes):
        raise PairBlocked("unbounded or invalid class sensitivity")
    def major(s):
        vmax=max(s.values())
        candidates=[k for k,v in s.items() if abs(v-vmax)<=1e-8]
        return candidates[0] if len(candidates)==1 else None
    majority=major(base)

    return {
        "profile":"oc-original-hessen-wfs-building-worldcover-block185-research-v0",
        "geometry_input":"one_original_Hessen_ALKIS_WFS_Building_GML_member",
        "worldcover_raster":"original_ESA_WorldCover_2021_v200_N48E009_block185",
        "source_building_feature_members_parsed":1,
        "source_wfs_reported_number_returned":source["source_reported_number_returned"],
        "wfs_count_discrepancy_still_blocked":True,
        "original_epsg4258_geos_valid":True,
        "transformed_epsg4326_geos_valid":True,
        "source_to_raster_crs_operation_declared_accuracy_metres":
            audit["coordinate_operation_accuracy_metres_declared"],
        "source_geometry_all_vertices_inside_original_raster_block":True,
        "fixed_research_scenarios":len(OFFSETS),
        "offset_steps_in_raster_pixels":[0.25,1.0],
        "offsets_are_not_geodetic_accuracy_metres":True,
        "baseline_intersected_pixel_cell_count":cell_counts[0],
        "maximum_intersected_pixel_cell_count":max(cell_counts),
        "baseline_area_weighted_original_class_fractions":{
            str(k):round(base.get(k,0.0),6) for k in classes
        },
        "class_fraction_ranges_over_grid_shifts":{
            str(k):{
                "minimum":round(min(s.get(k,0) for s in all_shares),6),
                "maximum":round(max(s.get(k,0) for s in all_shares),6),
            } for k in classes
        },
        "max_total_variation_over_grid_shifts":round(max(changes),6),
        "baseline_majority_if_unique":majority,
        "any_shift_changes_unique_majority":any(
            major(s)!=majority for s in all_shares[1:]
        ),
        "actual_polygon_raster_research_intersection_executed":True,
        "original_provider_source_feature_vintage_verified":False,
        "source_building_physical_identity_verified":False,
        "etrs89_wgs84_survey_epoch_verified":False,
        "insurer_exposure_or_tiv_inferred":False,
        "model_input_approved":False,
        "source_coordinates_or_raw_pixel_values_exported":False,
    }


def _one_wfs_bytes(*, opener) -> bytes:
    wfs.validate_frozen_getfeature()
    req=request.Request(
        wfs.URL,method="GET",
        headers={
            "Accept":"application/gml+xml,application/xml,text/xml",
            "Accept-Encoding":"identity",
            "User-Agent":"OpenCatastrophe-OneHessen-WorldCover-Pair-Research/0.1",
        }
    )
    try:
        with opener(req,wfs.TIMEOUT_SECONDS) as response:
            if response.status!=200 or response.geturl()!=wfs.URL:
                raise PairBlocked("WFS source original URL/status mismatched")
            mime=response.headers.get("Content-Type","").split(";",1)[0].strip().lower()
            if mime not in ("text/xml","application/xml","application/gml+xml",
                            "application/vnd.ogc.gml","application/vnd.ogc.wfs_xml"):
                raise PairBlocked("WFS original content MIME not reviewed")
            if response.headers.get("Content-Encoding","identity").lower()!="identity":
                raise PairBlocked("original WFS HTTP compression not reviewed")
            length=response.headers.get("Content-Length")
            if length is not None and (
                not length.isdigit() or int(length)>wfs.MAX_BYTES
            ):
                raise PairBlocked("original WFS declared body exceeds source cap")
            raw=response.read(wfs.MAX_BYTES+1)
    except (PairBlocked,wfs.CapabilityBlocked):
        raise
    except (error.HTTPError,error.URLError,TimeoutError,OSError) as exc:
        raise PairBlocked("bounded original WFS one-feature fetch unavailable") from exc
    if not 0<len(raw)<=wfs.MAX_BYTES:
        raise PairBlocked("unbounded original WFS one-feature body")
    return raw


def probe(*, wfs_open=wfs._open, worldcover_open=wc._open,
          contract_path=wc.CONTRACT_PATH) -> dict:
    gml=_one_wfs_bytes(opener=wfs_open)
    timeout,contract_sha=wc.reviewed_contract(contract_path)
    header=wc._read_one(bounds=wc.HEADER_RANGE,open_request=worldcover_open,timeout=timeout)
    coding=wc.tiff_sample_coding(header)
    tables=wc._read_one(bounds=wc.TABLE_RANGE,open_request=worldcover_open,timeout=timeout)
    if hashlib.sha256(tables).hexdigest()!=wc.TABLE_SHA256:
        raise PairBlocked("WorldCover original tile table checksum drift")
    try:
        table_meta=wc.inspect_tables(tables)
    except wc.TableSampleBlocked as exc:
        raise PairBlocked("original TIFF offsets invalid") from exc
    if (table_meta["selected_block_index"]!=185
            or table_meta["selected_block_source_byte_range_if_present"]!=list(wc.BLOCK_RANGE)):
        raise PairBlocked("original WorldCover byte offset changed")
    compressed=wc._read_one(bounds=wc.BLOCK_RANGE,open_request=worldcover_open,timeout=timeout)
    compressed_sha=hashlib.sha256(compressed).hexdigest()
    if compressed_sha!="526eb0819a9101a4e23df17dd70a040444190bb034528237fee29b415f9dd29a":
        raise PairBlocked("original WorldCover compressed block bytes drift")
    source_summary=wc.decode_original_block(compressed,predictor=coding["predictor"])
    if source_summary["decoded_block_sha256"]!="5a7cd7ce34de5d054e0f134cd5823b6bac77314fd3a2431ee547fe40cc0b3b7e":
        raise PairBlocked("WorldCover original pixel classification bytes drift")
    if coding["predictor"]!=1:
        raise PairBlocked("source predictor not supported in the original-pairing audit")
    # Second bounded decompression has exactly the same previously verified
    # compressed SHA and decoded SHA. No data persists; no new source request.
    d=zlib.decompressobj()
    pixels=d.decompress(compressed,SIDE*SIDE+1)
    if (len(pixels)!=SIDE*SIDE or not d.eof or d.unused_data or d.unconsumed_tail
            or hashlib.sha256(pixels).hexdigest()!=source_summary["decoded_block_sha256"]):
        raise PairBlocked("redecoded source block changed or exceeded 1024x1024 bytes")
    joined=inspect_original_pair(gml,pixels)
    return {
        **joined,
        "source_wfs_original_bytes":len(gml),
        "source_wfs_original_sha256":hashlib.sha256(gml).hexdigest(),
        "source_worldcover_decoded_sha256":source_summary["decoded_block_sha256"],
        "worldcover_exact_three_ranges_reused":True,
        "worldcover_access_contract_sha256":contract_sha,
        "original_provider_get_count":4,
        "source_request_set_sha256":hashlib.sha256(
            ("GET "+wfs.URL+" GET "+wc.URL+" "+
             str(wc.HEADER_RANGE)+str(wc.TABLE_RANGE)+str(wc.BLOCK_RANGE)).encode("ascii")
        ).hexdigest(),
        "code_sha256":hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "retrieved_utc":datetime.now(timezone.utc).isoformat(),
        "no_original_source_bytes_persisted":True,
        "no_original_source_geometry_coordinates_exported":True,
    }


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--live",action="store_true")
    args=parser.parse_args(argv)
    if not args.live:
        parser.error("all original sources disabled without reviewed --live")
    try:
        print(json.dumps(probe(),sort_keys=True,allow_nan=False))
    except (PairBlocked,hessen.CRSBlocked,wfs.BuildingFeatureBlocked,
            wc.PixelBlockBlocked,ValueError,OSError) as exc:
        print(json.dumps({"status":"BLOCKED","reason":str(exc),
                          "model_input_approved":False}),file=sys.stderr)
        return 1
    return 0


if __name__=="__main__":
    raise SystemExit(main())
