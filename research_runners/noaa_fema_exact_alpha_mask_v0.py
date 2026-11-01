# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Research-only exact NOAA alpha-positive raster mask -> FEMA count-only polygon.

Opt-in live command: original single 81,979-byte NOAA TIFF block 324,
HTTP206/ETag-pinned, plus exactly one FEMA public aggregate POST query.
No FEMA feature row, feature coordinates, image byte, image derived polygon,
or building record is logged or committed. A positive count is only a spatial
point-versus-raster-mask match, NOT an independently validated damage label.
"""

from __future__ import annotations

import hashlib
import json
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from typing import Any

from research_runners.noaa_michael_exact_alpha_live_v0 import (
    CANONICAL_HEIGHT, CANONICAL_WIDTH, SOURCE_ID, STAC_URL,
    SourceAlphaProbeError, fetch_range, measure_alpha,
)
from research_runners.noaa_michael_tiff_header_v0 import (
    TIFFHeaderError, _table, _vals, preflight as tiff_header_preflight,
)
from research_runners.noaa_fema_envelope_overlap_v0 import (
    COHORT_WHERE, FEMA_LAYER, _polygon_from_bbox,
)

BLOCK = 324
SIZE = 512
UNCOMPRESSED = SIZE * SIZE * 4
MAX_EDGES = 100_000
MAX_VERTICES = 15_000
MAX_GEOMETRY_BYTES = 300_000
MAX_REPLY_BYTES = 2000


class ExactAlphaMaskError(ValueError):
    """Raster mask is not a supported, authenticated, valid geographic shape."""


def alpha_mask_from_deflate(data: bytes, *, width: int = 512,
                            height: int = 512) -> list[bytes]:
    """Decode all four 8-bit channels with TIFF horizontal Predictor=2.

    Returns only one byte/pixel (0 or 1), clipped to the actual raster.
    Each row resets the predictor for the fourth interleaved alpha sample.
    """
    import zlib
    if type(data) is not bytes or not 1 <= len(data) <= 1_000_000:
        raise ExactAlphaMaskError("compressed original TIFF block not bounded")
    if type(width) is not int or type(height) is not int or not (
        1 <= width <= SIZE and 1 <= height <= SIZE
    ):
        raise ExactAlphaMaskError("invalid in-raster pixel dimensions")
    try:
        d = zlib.decompressobj()
        raw = d.decompress(data, UNCOMPRESSED + 1)
    except zlib.error as exc:
        raise ExactAlphaMaskError("original Deflate/Adler32 failed") from exc
    if len(raw) != UNCOMPRESSED or not d.eof or d.unused_data or d.unconsumed_tail:
        raise ExactAlphaMaskError("original TIFF block incomplete or oversized")
    result = []
    for y in range(height):
        a = 0
        row = bytearray(width)
        for x in range(SIZE):
            a = (a + raw[(y * SIZE + x) * 4 + 3]) & 255
            if x < width:
                row[x] = int(a > 0)
        result.append(bytes(row))
    return result


def _direction(a: tuple[int, int], b: tuple[int, int]) -> tuple[int, int]:
    return b[0] - a[0], b[1] - a[1]


def _turn_order(last: tuple[int, int], next_dir: tuple[int, int]) -> int:
    dx, dy = last
    return {
        (-dy, dx): 0,  # right in pixel y-down orientation
        (dx, dy): 1,   # straight
        (dy, -dx): 2,  # left
        (-dx, -dy): 3,
    }.get(next_dir, 10)


def _area2(ring: list[tuple[int, int]]) -> int:
    return sum(x1*y2-x2*y1 for (x1,y1),(x2,y2) in zip(ring,ring[1:]))


def _remove_collinear(ring: list[tuple[int, int]]) -> list[tuple[int, int]]:
    vertices = ring[:-1]
    result = []
    for i, v in enumerate(vertices):
        prev = vertices[(i-1) % len(vertices)]
        nxt = vertices[(i+1) % len(vertices)]
        if (v[0] - prev[0]) * (nxt[1] - v[1]) != (
            (v[1] - prev[1]) * (nxt[0] - v[0])
        ):
            result.append(v)
    if len(result) < 4:
        raise ExactAlphaMaskError("invalid polygon boundary after simplification")
    return result + [result[0]]


def polygonize_exact_positive_pixels(mask: list[bytes]) -> tuple[list[list[tuple[int, int]]], int]:
    """Exact union of alpha-positive raster *pixel squares* via boundary edges.

    Rightmost turn at diagonal-only shared vertices preserves simple separate
    rings. Outer rings/hole signs are retained through lon/latitude y-flip.
    Signed pixel-area sum is validated against *every* original alpha>0 cell.
    """
    if (type(mask) is not list or not 1 <= len(mask) <= SIZE or
        type(mask[0]) is not bytes or not 1 <= len(mask[0]) <= SIZE or
        any(type(r) is not bytes or len(r) != len(mask[0]) or
            any(px not in (0, 1) for px in r) for r in mask)):
        raise ExactAlphaMaskError("mask must be rectangular, nonempty and strictly binary")
    h, w = len(mask), len(mask[0])
    edges: dict[tuple[int,int], list[tuple[int,int]]] = {}
    positive = 0

    def edge(a: tuple[int,int], b: tuple[int,int]) -> None:
        edges.setdefault(a, []).append(b)

    for y, row in enumerate(mask):
        for x, val in enumerate(row):
            if not val:
                continue
            positive += 1
            if y == 0 or not mask[y-1][x]:
                edge((x,y),(x+1,y))
            if x+1 == w or not row[x+1]:
                edge((x+1,y),(x+1,y+1))
            if y+1 == h or not mask[y+1][x]:
                edge((x+1,y+1),(x,y+1))
            if x == 0 or not row[x-1]:
                edge((x,y+1),(x,y))
    total = sum(len(out) for out in edges.values())
    if positive == 0:
        return [], 0
    if total > MAX_EDGES:
        raise ExactAlphaMaskError("original source raster boundary exceeds geometric complexity cap")

    used: set[tuple[tuple[int,int],tuple[int,int]]] = set()
    loops = []
    for start in sorted(edges):
        for first in sorted(edges[start]):
            if (start,first) in used:
                continue
            used.add((start,first))
            ring = [start,first]
            current, prev = first, start
            while current != start:
                if len(ring) > total + 1:
                    raise ExactAlphaMaskError("unclosed original raster boundary")
                candidates = [p for p in edges.get(current, []) if (current,p) not in used]
                if not candidates:
                    raise ExactAlphaMaskError("source raster boundary has open or ambiguous ring")
                outgoing = min(candidates,key=lambda q: (_turn_order(_direction(prev,current),_direction(current,q)),q))
                used.add((current,outgoing))
                prev, current = current, outgoing
                ring.append(current)
            loops.append(_remove_collinear(ring))
    if len(used) != total or sum(_area2(r) for r in loops) != 2 * positive:
        raise ExactAlphaMaskError("source alpha mask polygon area mismatches original pixel census")
    if sum(len(r) for r in loops) > MAX_VERTICES:
        raise ExactAlphaMaskError("original alpha mask too complex for provider polygon query")
    return loops, positive


def build_alpha_mask_query(header: bytes, stac: dict[str, Any],
                           original_block: bytes) -> dict[str, Any]:
    """Build one public FEMA query spanning exactly source alpha-positive pixels."""
    try:
        meta = tiff_header_preflight(header, stac)
        if meta["tile_id_from_stac_only"] != SOURCE_ID:
            raise ExactAlphaMaskError("unreviewed source tile")
        tags = _table(header)
        if _vals(header,tags,317,3) != (2,) or _vals(header,tags,338,3) != (2,):
            raise ExactAlphaMaskError("unreviewed predictor or alpha band")
        offsets, lengths = _vals(header,tags,324,4),_vals(header,tags,325,4)
        if type(original_block) is not bytes or len(original_block) != lengths[BLOCK]:
            raise ExactAlphaMaskError("original source block byte count mismatch")
        mask = alpha_mask_from_deflate(original_block)
        audit = measure_alpha(original_block)
        loops, positive = polygonize_exact_positive_pixels(mask)
        if not loops or positive != audit["alpha_nonzero_pixels"]:
            raise ExactAlphaMaskError("original source-pixel alpha census mismatch")
        sx,sy,sz = _vals(header,tags,33550,12)
        px,py,pz,geo_x,geo_y,gz = _vals(header,tags,33922,12)
        row, col = divmod(BLOCK,19)
        geo_rings = []
        for ring in loops:
            coords = [[round(geo_x+(col*SIZE+x)*sx,12),
                       round(geo_y-(row*SIZE+y)*sy,12)] for x,y in ring]
            geo_rings.append(coords)
        geom = json.dumps({"rings":geo_rings,"spatialReference":{"wkid":4326}},
                          separators=(",",":"),allow_nan=False)
        if len(geom.encode("utf-8")) > MAX_GEOMETRY_BYTES:
            raise ExactAlphaMaskError("source polygon exceeds provider request cap")
        return {
            "query": {
                "where": COHORT_WHERE,
                "geometry": geom,
                "geometryType": "esriGeometryPolygon",
                "inSR": "4326",
                "spatialRel": "esriSpatialRelIntersects",
                "returnGeometry": "false",
                "returnCountOnly": "true",
                "f": "json",
            },
            "receipt": {
                "source_original_tile": SOURCE_ID,
                "source_original_block": BLOCK,
                "original_compressed_block_sha256": hashlib.sha256(original_block).hexdigest(),
                "alpha_positive_pixels": positive,
                "actual_original_mask_ring_count": len(loops),
                "actual_original_mask_vertex_count": sum(len(r) for r in loops),
                "polygon_geometry_bytes_not_logged": len(geom),
                "all_source_positive_alpha_pixel_squares_included": True,
                "fema_source_point_coordinates_retrieved": False,
                "original_image_bytes_persisted": False,
                "fema_original_image_lineage_verified": False,
                "model_input_admitted": False,
            },
        }
    except TIFFHeaderError as exc:
        raise ExactAlphaMaskError("original source TIFF/STAC metadata failed") from exc


def dilate_alpha_mask(mask: list[bytes], *, radius: int = 2) -> list[bytes]:
    """Expand mask by exactly two source pixels in all directions.

    This conservative query retains the same raster boundary, never leaves
    the single verified TIFF block, and tolerates pixel rounding on edges.
    It does not prove equality of remote-sensing and flight georeferencing.
    """
    if radius != 2 or not mask:
        raise ExactAlphaMaskError("only the fixed 2-pixel sensitivity test is supported")
    height,width=len(mask),len(mask[0])
    padded=[bytearray(width) for _ in range(height)]
    for y,row in enumerate(mask):
        for x,alpha in enumerate(row):
            if alpha:
                for yy in range(max(0,y-radius),min(height,y+radius+1)):
                    padded[yy][max(0,x-radius):min(width,x+radius+1)]=(
                        b"\x01"*(
                            min(width,x+radius+1)-max(0,x-radius)
                        )
                    )
    return [bytes(row) for row in padded]


def _rect_query(bbox: list[float]) -> dict[str, str]:
    return {
        "where":COHORT_WHERE,
        "geometry":_polygon_from_bbox(bbox),
        "geometryType":"esriGeometryPolygon",
        "inSR":"4326",
        "spatialRel":"esriSpatialRelIntersects",
        "returnCountOnly":"true",
        "returnGeometry":"false",
        "f":"json",
    }


def positive_control_queries(header: bytes, original_block: bytes) -> dict[str, dict[str,str]]:
    """Generate simple correct-source WGS84 positive controls and 2px mask.

    Neither the controls nor the exact mask coordinates are emitted into
    logs, the data register, the test fixtures, or any original image file.
    """
    tags=_table(header)
    sx,sy,sz=_vals(header,tags,33550,12)
    px,py,pz,geo_x,geo_y,gz=_vals(header,tags,33922,12)
    audit=measure_alpha(original_block)
    alpha_bbox=audit["nonzero_alpha_pixel_extent_xy_in_block"]
    if alpha_bbox is None:
        raise ExactAlphaMaskError("source alpha-positive pixel mask unexpectedly empty")
    row,col=divmod(BLOCK,19)

    def bbox_for_grid(x0:int,y0:int,x1:int,y1:int)->list[float]:
        return [
            geo_x+(col*SIZE+x0)*sx,
            geo_y-(row*SIZE+y1)*sy,
            geo_x+(col*SIZE+x1)*sx,
            geo_y-(row*SIZE+y0)*sy,
        ]

    x0,y0,xmax,ymax=alpha_bbox
    mask=alpha_mask_from_deflate(original_block)
    dilated=dilate_alpha_mask(mask)
    rings,count=polygonize_exact_positive_pixels(dilated)
    if count<audit["alpha_nonzero_pixels"]:
        raise ExactAlphaMaskError("source dilated alpha mask lost original covered pixels")
    geo_rings=[]
    for ring in rings:
        geo_rings.append([
            [round(geo_x+(col*SIZE+x)*sx,12),
             round(geo_y-(row*SIZE+y)*sy,12)]
            for x,y in ring
        ])
    geo=json.dumps({"rings":geo_rings,"spatialReference":{"wkid":4326}},
                   separators=(",",":"),allow_nan=False)
    if len(geo.encode("utf-8"))>MAX_GEOMETRY_BYTES:
        raise ExactAlphaMaskError("2px sensitivity mask too complex")
    dilated_query=_rect_query(bbox_for_grid(0,0,512,512))
    dilated_query["geometry"]=geo
    return {
        "full_raster_block":_rect_query(bbox_for_grid(0,0,512,512)),
        "all_positive_alpha_bbox":_rect_query(bbox_for_grid(x0,y0,xmax+1,ymax+1)),
        "dilated_alpha_mask_2px":dilated_query,
    }


def _public_count_only_post(query: dict[str,str]) -> int:
    """Exactly one source-provider aggregate-only HTTP POST."""
    body=urlencode(query).encode("utf-8")
    if len(body)>MAX_GEOMETRY_BYTES+3000:
        raise ExactAlphaMaskError("FEMA aggregate POST body exceeds bounded size")
    request=Request(FEMA_LAYER,data=body,method="POST",headers={
        "Content-Type":"application/x-www-form-urlencoded",
        "Accept":"application/json",
        "User-Agent":"OpenCatastropheData-SourceResearch/0.1",
    })
    with urlopen(request,timeout=30) as response:
        if response.getcode()!=200 or response.geturl()!=FEMA_LAYER:
            raise ExactAlphaMaskError("FEMA original aggregate URI/status drift")
        raw=response.read(MAX_REPLY_BYTES+1)
    if len(raw)>MAX_REPLY_BYTES:
        raise ExactAlphaMaskError("untrusted oversized FEMA response")
    result=json.loads(raw)
    if (type(result) is not dict or set(result)!={"count"} or
        type(result["count"]) is not int or
        not 0<=result["count"]<=1):
        raise ExactAlphaMaskError("unexpected FEMΑ public aggregate response")
    return result["count"]


def run_live_once() -> dict[str, Any]:
    """Opt-in original NOAA source fetch plus one small aggregate FEMA POST."""
    import urllib.request
    req = urllib.request.Request(STAC_URL,headers={"User-Agent":"OpenCatastropheResearch/0.1"})
    try:
        with urlopen(req,timeout=20) as r:
            if r.getcode()!=200 or r.geturl()!=STAC_URL:
                raise ExactAlphaMaskError("NOAA STAC origin/status drift")
            raw = r.read(200_001)
        if len(raw)>200_000:
            raise ExactAlphaMaskError("NOAA STAC exceeds bounded read")
        stac=json.loads(raw)
        header,etag,total=fetch_range(0,4096)
        tags = _table(header)
        off=_vals(header,tags,324,4)[BLOCK]
        length=_vals(header,tags,325,4)[BLOCK]
        block,etag2,total2=fetch_range(off,length,if_match=etag)
        if total2 != total or (etag and etag2 != etag):
            raise ExactAlphaMaskError("NOAA source object version/length drift")
        result=build_alpha_mask_query(header,stac,block)
        receipt=result["receipt"]
        # Two independent positive controls must prove the spatial service
        # still returns the one known original FEMA source point for both the
        # original block and the larger alpha-bounding rectangle. They guard
        # against a false zero from wrong source/CRS, permissions or epoch.
        controls=positive_control_queries(header,block)
        original_parent=_public_count_only_post(controls["full_raster_block"])
        bbox_parent=_public_count_only_post(controls["all_positive_alpha_bbox"])
        exact_count=_public_count_only_post(result["query"])
        padded_count=_public_count_only_post(controls["dilated_alpha_mask_2px"])
        if original_parent != 1 or bbox_parent != 1:
            raise ExactAlphaMaskError("positive source polygon controls did not return 1/1")
        if not 0<=exact_count<=padded_count<=bbox_parent:
            raise ExactAlphaMaskError("source mask/bbox/FEMA count hierarchy failed")
        return {
            "profile":"noaa_michael_real_pixel_alpha_polygon_fema_count_v0",
            **receipt,
            "source_original_http206_file_total_bytes":total,
            "full_block_fema_positive_control_count":original_parent,
            "alpha_bbox_fema_positive_control_count":bbox_parent,
            "exact_alpha_positive_mask_fema_count":exact_count,
            "two_pixel_dilated_alpha_mask_fema_count":padded_count,
            "conservative_alpha_sensitivity_radius_pixels":2,
            "fema_point_on_visible_raster_polygon_candidate":exact_count>0,
            "fema_georeferencing_precision_fully_verified":False,
            "independent_damage_assessment_proven":False,
            "model_input_admitted":False,
        }
    except ExactAlphaMaskError:
        raise
    except Exception as exc:
        raise ExactAlphaMaskError("original provider alpha mask or FEMA aggregate query unavailable") from exc


def main() -> int:
    try:
        print(json.dumps(run_live_once(),sort_keys=True))
        return 0
    except ExactAlphaMaskError as exc:
        print("NOAA_EXACT_ALPHA_MASK_PILOT_BLOCKED: "+str(exc))
        return 2


if __name__=="__main__":
    raise SystemExit(main())
