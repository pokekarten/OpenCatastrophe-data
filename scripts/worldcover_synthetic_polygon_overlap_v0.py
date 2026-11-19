# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Synthetic EPSG:4326 polygon overlap with one real, validated WorldCover block.

A bounded geometry-to-raster diagnostic; area is in ANGULAR pixel-square units,
not square metres. Never reads source remotely, stores raster/geometry bytes,
or admits land cover as a physical building or insured asset.
"""
from __future__ import annotations

from collections import defaultdict
import math

SIDE = 1024
SCALE = 3 / 36000
WEST = 9.0
NORTH = 51.0
BLOCK_INDEX = 185
BLOCK_ROW = 5
BLOCK_COLUMN = 5
MAX_CELLS = 64
VALID_CODES = frozenset((0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 95, 100))


class PolygonOverlapBlocked(ValueError):
    """Unverified or excessive synthetic raster/geometry intersection."""


def _synthetic_lonlat(column: float, row: float) -> tuple[float, float]:
    """Invented coordinates, not an address or surveyed building footprint."""
    return (
        WEST + (BLOCK_COLUMN * SIDE + column) * SCALE,
        NORTH - (BLOCK_ROW * SIDE + row) * SCALE,
    )


# Invented, frozen four-corner single-ring polygon around the synthetic point
# 9.5 E, 50.5 N. NOT sourced from OSM, ALKIS, EUBUCCO or an actual property.
SYNTHETIC_FOOTPRINT_WGS84 = tuple(_synthetic_lonlat(c, r) for c, r in (
    (877.8, 878.4), (882.2, 878.4), (882.2, 881.6), (877.8, 881.6),
))


def _twice_area(points):
    return sum(ax * by - bx * ay for (ax, ay), (bx, by)
               in zip(points, points[1:] + points[:1]))


def _orient(a, b, c):
    return (b[0]-a[0])*(c[1]-a[1]) - (b[1]-a[1])*(c[0]-a[0])


def _segments_touch(a, b, c, d):
    """Treat crossing and edge-touching nonadjacent sides as invalid."""
    eps = 1e-10
    ac, ad = _orient(a,b,c), _orient(a,b,d)
    ca, cb = _orient(c,d,a), _orient(c,d,b)
    if ac*ad < -eps and ca*cb < -eps:
        return True
    def within(p, u, v):
        return (min(u[0],v[0])-eps <= p[0] <= max(u[0],v[0])+eps and
                min(u[1],v[1])-eps <= p[1] <= max(u[1],v[1])+eps)
    return any(abs(cross) <= eps and within(p,u,v) for p,u,v,cross in (
        (c,a,b,ac), (d,a,b,ad), (a,c,d,ca), (b,c,d,cb)))


def _polygon_in_local_pixels(ring):
    if type(ring) not in (tuple,list) or not 3 <= len(ring) <= 12:
        raise PolygonOverlapBlocked("only a bounded exterior polygon ring is supported")
    points=[]
    for pair in ring:
        if type(pair) not in (tuple,list) or len(pair)!=2:
            raise PolygonOverlapBlocked("explicit EPSG:4326 (longitude,latitude) pairs required")
        lon,lat=pair
        if (type(lon) not in (int,float) or type(lat) not in (int,float)
                or not math.isfinite(lon) or not math.isfinite(lat)):
            raise PolygonOverlapBlocked("invalid or nonfinite WGS84 coordinates")
        column=(lon-WEST)/SCALE - BLOCK_COLUMN*SIDE
        row=(NORTH-lat)/SCALE - BLOCK_ROW*SIDE
        # WGS84 float roundtrips can create artificial micro-slivers along
        # a mathematically exact integer pixel boundary. Snap ONLY within
        # 1e-8 of a pixel; never move a genuine footprint across a grid cell.
        column=float(round(column)) if abs(column-round(column))<=1e-8 else column
        row=float(round(row)) if abs(row-round(row))<=1e-8 else row
        if not (0 <= column < SIDE and 0 <= row < SIDE):
            raise PolygonOverlapBlocked("polygon outside the only reviewed original raster block")
        points.append((column,row))
    points=tuple(points)
    if abs(_twice_area(points)) < 1e-8:
        raise PolygonOverlapBlocked("empty or zero-area polygon")
    for i in range(len(points)):
        a,b=points[i],points[(i+1)%len(points)]
        if math.dist(a,b)<1e-7:
            raise PolygonOverlapBlocked("degenerate polygon edge")
        for j in range(i+1,len(points)):
            if j-i==1 or (i==0 and j==len(points)-1):
                continue
            c,d=points[j],points[(j+1)%len(points)]
            if _segments_touch(a,b,c,d):
                raise PolygonOverlapBlocked("non-simple self-intersecting polygon")
    return points


def _clip(points, axis, border, keep_above):
    if not points:
        return []
    inside=lambda p: p[axis]>=border if keep_above else p[axis]<=border
    out=[]
    previous=points[-1]
    for point in points:
        before, after=inside(previous),inside(point)
        if before!=after:
            t=(border-previous[axis])/(point[axis]-previous[axis])
            out.append((previous[0]+t*(point[0]-previous[0]),
                        previous[1]+t*(point[1]-previous[1])))
        if after:
            out.append(point)
        previous=point
    return out


def _pixel_overlap_area(points, row, column):
    clipped=list(points)
    for axis,value,keep_above in (
        (0,column,True), (0,column+1,False),
        (1,row,True), (1,row+1,False),
    ):
        clipped=_clip(clipped,axis,value,keep_above)
    return abs(_twice_area(tuple(clipped)))/2 if len(clipped)>=3 else 0.0


def evaluate_synthetic_polygon_in_block(
    pixels: bytes, *, ring=SYNTHETIC_FOOTPRINT_WGS84,
) -> dict:
    """True polygon/pixel clipping, but ONLY synthetic geometry in one block.

    Real footprints, holes, multipolygons, larger windows and geographic
    ground areas are intentionally unsupported. Outputs only aggregates.
    """
    if type(pixels) is not bytes or len(pixels) != SIDE*SIDE:
        raise PolygonOverlapBlocked("exactly one decoded 1024x1024 uint8 block required")
    points=_polygon_in_local_pixels(ring)
    c0=math.floor(min(x for x,_ in points))
    c1=math.ceil(max(x for x,_ in points))
    r0=math.floor(min(y for _,y in points))
    r1=math.ceil(max(y for _,y in points))
    if (c1-c0)*(r1-r0)>MAX_CELLS:
        raise PolygonOverlapBlocked("bounded polygon-to-cell work budget exceeded")
    weighted=defaultdict(float)
    touched=0
    expected_area=abs(_twice_area(points))/2
    for row in range(r0,r1):
        for col in range(c0,c1):
            area=_pixel_overlap_area(points,row,col)
            if area<1e-10:
                continue
            code=pixels[row*SIDE+col]
            if code not in VALID_CODES:
                raise PolygonOverlapBlocked("unreviewed ESA WorldCover class code")
            weighted[code]+=area
            touched+=1
    covered=sum(weighted.values())
    if covered<=0 or abs(covered-expected_area)>1e-5:
        raise PolygonOverlapBlocked("polygon/rasters do not conserve overlap area")
    # Polygon area centroid is not a substitute for full footprint intersection.
    twice=_twice_area(points)
    centroid_col=sum((a[0]+b[0])*(a[0]*b[1]-b[0]*a[1])
                     for a,b in zip(points,points[1:]+points[:1]))/(3*twice)
    centroid_row=sum((a[1]+b[1])*(a[0]*b[1]-b[0]*a[1])
                     for a,b in zip(points,points[1:]+points[:1]))/(3*twice)
    if not (0<=centroid_col<SIDE and 0<=centroid_row<SIDE):
        raise PolygonOverlapBlocked("centroid outside the single reviewed block")
    center_code=pixels[math.floor(centroid_row)*SIDE+math.floor(centroid_col)]
    if center_code not in VALID_CODES:
        raise PolygonOverlapBlocked("unreviewed ESA WorldCover centroid class")
    return {
        "profile":"oc-worldcover-synthetic-polygon-overlap-v0",
        "geometry_kind":"constructed_synthetic_single_ring_not_real_building",
        "geometry_crs":"EPSG:4326",
        "source_tile":"N48E009",
        "source_tiff_block_index":BLOCK_INDEX,
        "method":"exact_polygon_pixel_clipping_in_angular_grid_units",
        "polygon_area_pixel_units":round(expected_area,6),
        "intersected_pixel_cell_count":touched,
        "area_weighted_class_fractions":{
            str(code):round(area/covered,6) for code,area in sorted(weighted.items())
        },
        "centroid_pixel_class_code":center_code,
        "polygon_class_heterogeneity_observed":len(weighted)>1,
        "source_pixel_values_exported":False,
        "real_building_footprint_matched":False,
        "insured_tiv_inferred":False,
        "model_input_approved":False,
    }
