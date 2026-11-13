#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Source-verified, first original JRC/BVV 1,024-cell cross-epoch comparison.

Original official GHSL BUILT-S/V R2023A E2020: one immutable 512x512
TIFF source block per product, with exact 32KiB source-prefix and source
block SHA gates. Official Bavarian HU-BY: complete original 2.7m-record
Oberbayern SHP member, 20 verified bounded HTTP-206 source ranges,
full native SHA/CRC, streaming GEOS union. Compute per-cell comparisons
only in ephemeral memory; output anonymous global statistics and one
ordered SHA-256. Never persist original cells, geometries or buildings.
Not a calibrated model or a valid 2020 cadastral survey ground truth.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import struct
import sys
import zlib
from datetime import datetime, timezone

from scripts.probe_ghsl_built_native_original_block_v0 import (
    _fetch_range, aggregate_native_block, NATIVE_BYTES, TILE_SIDE,
    WINDOW_SIDE, WINDOW_LOCAL_X, WINDOW_LOCAL_Y, GHSLNativeBlocked,
)
from scripts.verify_ghsl_built_r2023a_native_prefix_v0 import (
    PRODUCTS, PREFIX_BYTES, verify_original_tiff_prefix,
)
from research_runners.bvv_oberbayern_full_shp_roi_stream_v0 import (
    FullSHPBlocked, VerifiedOriginalSegmentStream,
    inspect_original_stream, frozen_roi_geometries,
)

ORIGINAL_GHSL = {
    "surface":{
        "original_compressed_sha":"eae39538ec234c80d43f135e7022e1c2ad4be3e10d72dcdc2e82534431a276d9",
        "original_window_sha":"2f1a3322b2081e70e8e7b08339dc14b61d5286605208f063fd57539e80121106",
        "original_decoded_sha":"1d961e2c951e4db8df6e22776903aa06ea943a9f49728ef4a8fa8178506c8923",
        "positive":937,"zero":87,"sum":74802406,
    },
    "volume":{
        "original_compressed_sha":"578a62b6164f30ab82479e37cbfbf4353af2db18ff2eef65552aff5dce12e53c",
        "original_window_sha":"2929b3c7e33e00948ca6589bec268eb80ff59bafe13d9463e8440ee7bf298ec9",
        "original_decoded_sha":"e91e026954d2f37d19c48ea87b3e33207e8c67e0efdda0d5c66589a3e751b5f5",
        "positive":937,"zero":87,"sum":520775503,
    },
}
BVV_FROZEN={
    "original_full_decoded_shape_bytes":501212696,
    "original_full_decoded_shape_crc32":"55540a66",
    "original_full_decoded_shape_sha256":"977e35aa7764564be115776ea56f78ef228d3cc79939b28f08c6cbe96e2e7a0c",
    "full_original_compressed_member_sha256":"22364ef161d6411e2010be590d791508242ec6d36ffc3a314833cedcd6afc615",
    "original_partial_first_49197_sha256":"8a3c95bbbca493b192f6923fa4b6060798f561775f647bd34ffd4fc3af316f80",
    "original_full_native_records_checked":2703736,
    "original_shape_polygons_checked":2703736,
    "original_max_content_bytes":10284,
    "provider_original_206_segments_verified":20,
    "provider_source_range_mode":"contiguous_exact_206_bounded_segments",
    "roi_original_polygon_records_intersecting":417565,
    "roi_bbox_candidates":431083,
    "roi_original_polygon_areas_union_m2":56791644.17,
    "roi_original_polygon_overlap_area_m2":80167.285,
    "roi_invalid_geos_rings":0,"roi_invalid_geos_polygons":0,
    "roi_complete_for_this_verified_SHAPE_archive_only":True,
    "historical_2020_ground_truth_verified":False,
    "source_coordinates_geometries_or_bytes_persisted":False,
    "model_input_approved":False,
}
CELL_COUNT=32*32
SOURCE_EPOCH=2020
BVV_AREA_TOLERANCE_M2=0.5


class CellwiseBlocked(ValueError):
    """Original source, geometry, source support or admission gate failed."""


def decode_native_1024_original_values(inflated: bytes) -> tuple[tuple[int,...],bytes]:
    """Pure uint32 source window decoder; can be unit-tested with fake data."""
    if type(inflated) is not bytes or len(inflated)!=NATIVE_BYTES:
        raise CellwiseBlocked("source original UINT32 tile length drift")
    whole=bytearray()
    for r in range(WINDOW_LOCAL_Y,WINDOW_LOCAL_Y+WINDOW_SIDE):
        offset=(r*TILE_SIDE+WINDOW_LOCAL_X)*4
        whole.extend(inflated[offset:offset+WINDOW_SIDE*4])
    if len(whole)!=CELL_COUNT*4:
        raise CellwiseBlocked("original native 32x32 window bytes incomplete")
    values=tuple(v[0] for v in struct.iter_unpack("<I",whole))
    if any(v==0xffffffff for v in values):
        raise CellwiseBlocked("unreviewed candidate UINT32-max NoData in native window")
    return values,bytes(whole)


def fetch_frozen_ghsl_cells(product: str) -> tuple[int,...]:
    """Exact fixed original TIFF header + one reviewed original compressed tile."""
    if product not in ORIGINAL_GHSL or product not in PRODUCTS:
        raise CellwiseBlocked("unreviewed original JRC product")
    rule=ORIGINAL_GHSL[product]
    config=PRODUCTS[product]
    header=_fetch_range(product,0,PREFIX_BYTES)
    meta=verify_original_tiff_prefix(header,product)
    if (meta["fixed_source_block_offset"]!=config["native_block_offset"] or
            meta["fixed_source_block_compressed_bytes"]!=config["native_block_bytes"]):
        raise CellwiseBlocked("reviewed original JRC raster block mapping drift")
    compressed=_fetch_range(product,config["native_block_offset"],config["native_block_bytes"])
    summary=aggregate_native_block(compressed,expected_bytes=config["native_block_bytes"])
    frozen={
        "original_source_compressed_block_sha256":rule["original_compressed_sha"],
        "original_source_decoded_block_sha256":rule["original_decoded_sha"],
        "fixed_window_uint32_le_sha256":rule["original_window_sha"],
        "fixed_window_positive_non_sentinel_cells":rule["positive"],
        "fixed_window_zero_cells":rule["zero"],
        "fixed_window_potential_uint32_max_sentinel_cells":0,
        "fixed_window_positive_sum_raw_source_units":rule["sum"],
        "fixed_original_window_global_col_row":[22973,4899],
        "fixed_original_window_shape":[32,32],
    }
    for key,want in frozen.items():
        if summary.get(key)!=want:
            raise CellwiseBlocked("original 2020 GHSL source-value SHA/unit count drift: "+key)
    stream=zlib.decompressobj()
    try:
        native=stream.decompress(compressed,NATIVE_BYTES+1)
    except zlib.error as exc:
        raise CellwiseBlocked("original native GeoTIFF payload corrupt") from exc
    if (len(native)!=NATIVE_BYTES or not stream.eof
            or stream.unused_data or stream.unconsumed_tail):
        raise CellwiseBlocked("original native GeoTIFF Deflate envelope not exact")
    values,window=decode_native_1024_original_values(native)
    if (hashlib.sha256(window).hexdigest()!=rule["original_window_sha"]
            or hashlib.sha256(native).hexdigest()!=rule["original_decoded_sha"]
            or sum(values)!=rule["sum"]
            or sum(v>0 for v in values)!=rule["positive"]):
        raise CellwiseBlocked("independent 1,024 native UINT32 source values differ")
    return values


def build_frozen_1024_cells():
    """Split exact original GHSL source 32x32 into row-major projected cells."""
    from pyproj import Transformer
    from shapely.geometry import Polygon
    from shapely.ops import unary_union
    parent,_=frozen_roi_geometries()
    s,v=PRODUCTS["surface"],PRODUCTS["volume"]
    if (s["origin"]!=v["origin"] or s["scale"]!=v["scale"]
        or WINDOW_SIDE!=32):
        raise CellwiseBlocked("BUILT-S/V original native geographic grids diverged")
    lon0,lat0=s["origin"]
    dx,dy=s["scale"][:2]
    if not (0.00833<dx<0.00834 and 0.00833<dy<0.00834):
        raise CellwiseBlocked("original GHSL angular cell pitch changed")
    start_col,start_row=22973,4899
    transform=Transformer.from_crs("EPSG:4326","EPSG:25832",always_xy=True)
    cells=[]
    for r in range(32):
        for c in range(32):
            left=lon0+(start_col+c)*dx
            right=lon0+(start_col+c+1)*dx
            top=lat0-(start_row+r)*dy
            bottom=lat0-(start_row+r+1)*dy
            footprint=Polygon([
                transform.transform(left,top),
                transform.transform(right,top),
                transform.transform(right,bottom),
                transform.transform(left,bottom),
            ])
            if not footprint.is_valid or not 100000<footprint.area<2000000:
                raise CellwiseBlocked("native projected geographic cell invalid")
            cells.append(footprint)
    if len(cells)!=CELL_COUNT:
        raise CellwiseBlocked("original native raster cell count changed")
    reconstructed=unary_union(cells)
    if (not reconstructed.is_valid
        or parent.symmetric_difference(reconstructed).area>0.01
        or abs(sum(x.area for x in cells)-parent.area)>0.01):
        raise CellwiseBlocked("1,024 projected native cells do not exactly partition original ROI")
    return parent,tuple(cells)


def compute_1024_cell_statistics(original_union, source_receipt:dict,
                                  source_surface:tuple[int,...],
                                  source_volume:tuple[int,...]):
    """Only source-limited global aggregates; no original cell values emitted."""
    from shapely.strtree import STRtree
    if (not isinstance(source_receipt,dict)
        or source_receipt.get("roi_original_polygon_records_intersecting")!=417565
        or abs(source_receipt.get("roi_original_polygon_areas_union_m2",0)-56791644.17)>0.005
        or source_receipt.get("model_input_approved") is not False
        or len(source_surface)!=CELL_COUNT or len(source_volume)!=CELL_COUNT
        or not getattr(original_union,"is_valid",False)):
        raise CellwiseBlocked("original BVV source union or GHSL 1024-cell prerequisite missing")
    for key,values in (("surface",source_surface),("volume",source_volume)):
        rule=ORIGINAL_GHSL[key]
        if (any(type(v) is not int or v<0 or v>=0xffffffff for v in values)
            or sum(values)!=rule["sum"]
            or sum(v>0 for v in values)!=rule["positive"]
            or sum(v==0 for v in values)!=rule["zero"]):
            raise CellwiseBlocked("original native JRC cell data does not match frozen source counts")
    roi,cells=build_frozen_1024_cells()
    if abs(original_union.difference(roi).area)>0.1:
        raise CellwiseBlocked("original cadastral union outside original frozen GHSL source ROI")
    geo_parts=tuple(original_union.geoms) if original_union.geom_type=="MultiPolygon" else (original_union,)
    if not geo_parts or len(geo_parts)>500000:
        raise CellwiseBlocked("unreviewed original cadastral GEOS geometry component count")
    tree=STRtree(geo_parts)
    area_by_cell=[]
    digest=hashlib.sha256()
    # Source GeoTIFF scanline ordering: north -> south, west -> east.
    for i,cell in enumerate(cells):
        matches=tree.query(cell,predicate="intersects")
        area=math.fsum(geo_parts[int(k)].intersection(cell).area for k in matches)
        if not math.isfinite(area) or area<0 or area>cell.area+0.1:
            raise CellwiseBlocked("original cadastral cell clipped area invalid")
        area_by_cell.append(area)
        # Pin *all* 1,024 original values without logging/persisting them.
        # Little-endian tuple: BUILT-S m² UINT32, BUILT-V m³ UINT32,
        # official recent footprint area * 1000 as uint64.
        digest.update(struct.pack("<IIQ",source_surface[i],source_volume[i],
                                  int(round(area*1000))))
    total_area=math.fsum(area_by_cell)
    if abs(total_area-original_union.area)>BVV_AREA_TOLERANCE_M2:
        raise CellwiseBlocked("original official polygon union not conserved across 1,024 projected cells")
    if abs(total_area-source_receipt["roi_original_polygon_areas_union_m2"])>BVV_AREA_TOLERANCE_M2:
        raise CellwiseBlocked("official original full-source ROI aggregate differs from cell overlay")
    both=sum(a>0 and v>0.000001 for a,v in zip(source_surface,area_by_cell))
    ghsl_only=sum(a>0 and v<=0.000001 for a,v in zip(source_surface,area_by_cell))
    bvv_only=sum(a==0 and v>0.000001 for a,v in zip(source_surface,area_by_cell))
    neither=CELL_COUNT-both-ghsl_only-bvv_only
    if min(both,ghsl_only,bvv_only,neither)<0 or both+ghsl_only!=937:
        raise CellwiseBlocked("original native cell support cross-tabulation drift")
    xs=tuple(float(x) for x in source_surface)
    ys=tuple(float(y) for y in area_by_cell)
    mx=math.fsum(xs)/CELL_COUNT
    my=math.fsum(ys)/CELL_COUNT
    sx=math.fsum((x-mx)**2 for x in xs)
    sy=math.fsum((y-my)**2 for y in ys)
    if sx<=0 or sy<=0:
        raise CellwiseBlocked("original source 1024-cell variances cannot be zero")
    corr=math.fsum((x-mx)*(y-my) for x,y in zip(xs,ys))/math.sqrt(sx*sy)
    if not -1.000001<=corr<=1.000001:
        raise CellwiseBlocked("original cross-epoch association math invalid")
    return {
        "profile":"oc-ghsl-bvv-original-1024-cell-paired-cross-epoch-research-v0",
        "paired_native_original_cells":CELL_COUNT,
        "paired_native_cell_tuple_sha256":digest.hexdigest(),
        "paired_sha256_binary_format":"row_major_le_uint32_surface_m2_uint32_volume_m3_uint64_bvv_area_m2_x1000",
        "paired_ghsl_s_surface_cells_positive":937,
        "paired_ghsl_s_surface_cells_zero":87,
        "paired_bvv_footprint_positive_cells":both+bvv_only,
        "paired_both_source_footprint_cells_positive":both,
        "paired_ghsl_positive_bvv_zero_cells":ghsl_only,
        "paired_ghsl_zero_bvv_positive_cells":bvv_only,
        "paired_both_zero_cells":neither,
        "paired_cellwise_exploratory_pearson_r":round(corr,6),
        "paired_official_current_footprint_cell_areas_sum_m2":round(total_area,3),
        "paired_official_current_area_conservation_tolerance_m2":BVV_AREA_TOLERANCE_M2,
        "paired_ghsl_e2020_original_built_surface_total_m2":sum(source_surface),
        "paired_ghsl_e2020_original_built_volume_total_m3_context_only":sum(source_volume),
        "paired_source_epoch_mismatch_2020_vs_current_bvv":True,
        "paired_pearson_is_not_model_accuracy":True,
        "paired_geographic_cells_not_constant_100m":True,
        "paired_native_cell_values_or_original_geometries_persisted":False,
        "paired_bvv_individual_building_count_claimed":False,
        "paired_exposure_or_tiv_approved":False,
        "model_input_approved":False,
    }


def run_original_probe():
    surface=fetch_frozen_ghsl_cells("surface")
    volume=fetch_frozen_ghsl_cells("volume")
    # Check the requested source grid before any 166MB BVV original download.
    roi,_=build_frozen_1024_cells()
    reader=VerifiedOriginalSegmentStream()
    def on_verified_original_union(geometry,receipt):
        return compute_1024_cell_statistics(geometry,receipt,surface,volume)
    observed=inspect_original_stream(
        reader, status=None,response_url=None,headers={},roi=roi,
        verified_segments=True, original_roi_union_analysis=on_verified_original_union,
    )
    for k,v in BVV_FROZEN.items():
        if observed.get(k)!=v:
            raise CellwiseBlocked("original complete-source immutable SHP SHA/CRC or ROI drift: "+k)
    if observed.get("profile")!="oc-bvv-original-oberbayern-complete-shp-ghsl-roi-v0":
        raise CellwiseBlocked("original 2.7m whole SHP source runner has changed")
    if (observed.get("paired_native_original_cells")!=CELL_COUNT
        or observed.get("paired_ghsl_s_surface_cells_positive")!=937
        or observed.get("model_input_approved") is not False):
        raise CellwiseBlocked("original cellwise research source result unavailable")
    observed.update({
        "original_jrc_2020_surface_window_sha256":ORIGINAL_GHSL["surface"]["original_window_sha"],
        "original_jrc_2020_volume_window_sha256":ORIGINAL_GHSL["volume"]["original_window_sha"],
        "original_source_workflow_is_research_only":True,
        "original_source_publisher_rights":"BVV HU-BY CC BY 4.0 with attribution; JRC GHS BUILT-S/V CC BY 4.0",
        "source_rights_attribution":"Datenquelle: Bayerische Vermessungsverwaltung – www.geodaten.bayern.de",
        "original_source_raw_geometries_or_pixels_stored":False,
        "full_original_GHSL_tiffs_acquired":False,
        "source_cadastre_survey_vintage_verified":False,
        "current_BVV_vs_2020_GHSL_is_historical_validation":False,
        "model_input_approved":False,
        "observed_at_utc":datetime.now(timezone.utc).isoformat(),
    })
    return observed


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--live",action="store_true")
    a=p.parse_args(argv)
    if not a.live:
        p.error("only reviewed trusted-main may run original JRC and Bavarian source GETs")
    try:
        print(json.dumps(run_original_probe(),sort_keys=True,allow_nan=False))
        return 0
    except (CellwiseBlocked,FullSHPBlocked,GHSLNativeBlocked,ValueError,OSError,OverflowError) as exc:
        print("BLOCKED: original 1024-cell research source verification unavailable: "+str(exc),
              file=sys.stderr)
        return 2


if __name__=="__main__":
    raise SystemExit(main())
