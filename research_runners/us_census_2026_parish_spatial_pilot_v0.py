# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Exact-source pilot: three Louisiana county-equivalent SHP geometries.

Shapefile binary is parsed from the original ZIP after the independently
repeated full-source SHA256 gate. Source shape polygons are rebuilt by
Shapefile ring winding convention with no silent repair or simplification.
No coordinates, input bytes or private exposure leave the local process.

Research QC only. Zero insured location/TIV/claims or rights/admission.
"""
from __future__ import annotations

import argparse
from hashlib import sha256
import io
import json
import math
from pathlib import Path
import struct
import sys
import zipfile

from research_runners.us_census_2026_county_zip_audit_v0 import (
    CensusZipError, MAX_ZIP_BYTES, STEM, audit_original_zip,
)

PINNED_ORIGINAL_SHA256 = "b527c9ba7aeb8f17ef118f026eae5e5a938aa1d00b873bc32342d0dce59321c0"
# Strictly audited official identifiers: Orleans, Jefferson, St. Bernard.
PILOT_GEOIDS = ("22051", "22071", "22087")
MAX_PARTS_PER_REGION = 25000
MAX_POINTS_PER_REGION = 1_500_000
# Geographic NAD83 lon/lat, large enough to cover Louisiana offshore shapes,
# but not an exact Louisiana border or official bounds.
LA_ENVELOPE = (-96.0, 27.0, -87.0, 34.0)
OVERLAP_THRESHOLD_SQDEG = 1e-8


class PilotGeometryError(ValueError):
    pass


def _fail(message):
    raise PilotGeometryError(message)


def _column_schema(dbf):
    header_len = struct.unpack_from("<H", dbf, 8)[0]
    rec_len = struct.unpack_from("<H", dbf, 10)[0]
    count = struct.unpack_from("<I", dbf, 4)[0]
    if header_len < 65 or len(dbf) < header_len + rec_len * count:
        _fail("DBF structural mismatch")
    position = 1
    fields = {}
    for offset in range(32, header_len-1, 32):
        descriptor = dbf[offset:offset+32]
        name = descriptor[:11].split(b"\x00", 1)[0].decode("ascii")
        width = descriptor[16]
        fields[name] = (position, width)
        position += width
    if "GEOID" not in fields or position != rec_len:
        _fail("invalid original DBF GEOID offsets")
    return header_len, rec_len, count, fields


def _selected_indexes(dbf, geoids):
    header_len, rec_len, count, fields = _column_schema(dbf)
    pos, width = fields["GEOID"]
    expected = {geoid.encode("ascii") for geoid in geoids}
    indexes = {}
    for ordinal in range(count):
        row = dbf[header_len + rec_len*ordinal:header_len + rec_len*(ordinal+1)]
        geoid = row[pos:pos+width].strip(b" ")
        if geoid in expected:
            if geoid in indexes:
                _fail("duplicate exact pilot GEOID")
            indexes[geoid] = ordinal
    if set(indexes) != expected:
        _fail("missing exact official pilot GEOID in source")
    return indexes


def _signed_area(coords):
    return math.fsum(
        a[0]*b[1]-b[0]*a[1]
        for a,b in zip(coords, coords[1:]))/2.0


def _reconstruct_shape(shp, shx, ordinal):
    try:
        from shapely.geometry import LinearRing, Polygon, MultiPolygon
    except ImportError as exc:
        raise PilotGeometryError("reviewed Shapely runtime missing") from exc

    index_offset = 100 + ordinal*8
    if index_offset+8 > len(shx):
        _fail("selected feature outside SHX")
    first_words, content_words = struct.unpack_from(">II", shx, index_offset)
    off = first_words*2
    content_end = off + 8 + content_words*2
    if off < 100 or content_end > len(shp):
        _fail("original SHX offset outside SHP")
    rec_number, declared_words = struct.unpack_from(">II", shp, off)
    if rec_number != ordinal+1 or declared_words != content_words:
        _fail("mismatched original polygon record identity")
    body = memoryview(shp)[off+8:content_end]
    if len(body) < 44:
        _fail("original shape body truncated")
    stype, xmin, ymin, xmax, ymax, parts, points = struct.unpack_from("<i4dii", body, 0)
    if stype != 5 or not 1 <= parts <= MAX_PARTS_PER_REGION or not 4 <= points <= MAX_POINTS_PER_REGION:
        _fail("unsupported or unbounded polygon parts/vertices")
    if len(body) != 44 + 4*parts + 16*points:
        _fail("selected polygon byte count disagreement")
    if not (LA_ENVELOPE[0] <= xmin <= xmax <= LA_ENVELOPE[2]
            and LA_ENVELOPE[1] <= ymin <= ymax <= LA_ENVELOPE[3]):
        _fail("selected original county bbox lies outside coarse Louisiana extent")
    starts = list(struct.unpack_from(f"<{parts}i", body, 44))
    if starts[0] != 0 or starts != sorted(set(starts)) or starts[-1] >= points:
        _fail("invalid original SHP ring offsets")
    stops = starts[1:] + [points]
    shell_rings, hole_rings = [], []
    ring_count = 0
    for first,last in zip(starts,stops):
        if last-first < 4:
            _fail("polygon part too short for closed ring")
        offset = 44+parts*4+first*16
        coords = []
        for idx in range(last-first):
            lon,lat = struct.unpack_from("<dd",body,offset+idx*16)
            if (not math.isfinite(lon) or not math.isfinite(lat)
                or not LA_ENVELOPE[0] <= lon <= LA_ENVELOPE[2]
                or not LA_ENVELOPE[1] <= lat <= LA_ENVELOPE[3]):
                _fail("invalid/non-finite source coordinate")
            coords.append((lon,lat))
        if coords[0] != coords[-1] or len(set(coords[:-1])) < 3:
            _fail("source ring is not closed/nondegenerate")
        ring = LinearRing(coords)
        if not ring.is_simple or not ring.is_valid:
            _fail("invalid or self-crossing original polygon ring")
        signed = _signed_area(coords)
        if abs(signed) <= 1e-13:
            _fail("zero or near-zero original ring area")
        if signed < 0:
            shell_rings.append((coords,Polygon(coords)))
        else:
            hole_rings.append((coords,Polygon(coords)))
        ring_count += 1

    if not shell_rings:
        _fail("selected region has no clockwise source exterior ring")
    shell_holes = [[] for _ in shell_rings]
    for coords,hole in hole_rings:
        witness = hole.representative_point()
        hosts = [(shell.area,i) for i,(_,shell) in enumerate(shell_rings)
                 if shell.contains(witness)]
        if not hosts:
            _fail("source counterclockwise hole without containing shell")
        _,index = min(hosts)
        shell_holes[index].append(coords)
    polygons = [
        Polygon(shell_coords, shell_holes[i])
        for i,(shell_coords,_) in enumerate(shell_rings)
    ]
    geom = MultiPolygon(polygons) if len(polygons) > 1 else polygons[0]
    if geom.is_empty or not geom.is_valid or geom.area <= 0:
        _fail("selected county has invalid source multi-ring geometry")
    # Source SHP per-feature bounds checked without geometry repair. Areas are
    # degrees squared, diagnostic only, NOT geographic km2/actuarial exposures.
    bounds = geom.bounds
    if max(abs(a-b) for a,b in zip((xmin,ymin,xmax,ymax),bounds)) > 1e-7:
        _fail("SHP feature bbox and source rings disagree")
    return geom, {"ring_count":ring_count,
                  "outer_shells":len(shell_rings),
                  "interior_holes":len(hole_rings),
                  "original_coordinate_count":points,
                  "is_valid":True}


def inspect_pilot_bytes(raw, *, expected_sha256=None, geoids=PILOT_GEOIDS):
    if type(geoids) is not tuple or not geoids or len(geoids)>3 or len(set(geoids))!=len(geoids):
        _fail("bounded exact requested original GEOIDs only")
    if any(type(g) is not str or len(g)!=5 or not g.isascii() or not g.isdigit()
           or not g.startswith("22") for g in geoids):
        _fail("selected area must contain explicit Louisiana parish GEOIDs")
    full = audit_original_zip(raw, independently_pinned_sha256=expected_sha256)
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        shp = archive.read(f"{STEM}.shp")
        shx = archive.read(f"{STEM}.shx")
        dbf = archive.read(f"{STEM}.dbf")
    positions = _selected_indexes(dbf, geoids)
    regions = {}
    for encoded,ordinal in positions.items():
        regions[encoded.decode("ascii")] = _reconstruct_shape(shp, shx, ordinal)
    overlap_values = []
    for index,left in enumerate(sorted(regions)):
        for right in sorted(regions)[index+1:]:
            lg,rg = regions[left][0],regions[right][0]
            if lg.intersects(rg):
                intersection = lg.intersection(rg)
                overlap = float(intersection.area)
                if not math.isfinite(overlap):
                    _fail("nonfinite inter-parish polygon intersection")
                overlap_values.append(overlap)
                if overlap > OVERLAP_THRESHOLD_SQDEG:
                    _fail("selected official parish interiors overlap materially")
    return {
        "profile":"OC_CENSUS_2026_LOUISIANA_PARISH_PILOT_QC_V0",
        "source_zip_sha256_observed": full["source_zip_sha256_observed"],
        "sha256_matched_independent_pin":full["sha256_matched_independent_pin"],
        "source_original_county_equivalents":full["dbf_feature_count"],
        "selected_parish_geoids":sorted(regions),
        "selected_polygon_qc":[
            {"geoid":code,**regions[code][1]}
            for code in sorted(regions)],
        "max_selected_interparish_overlap_square_degrees":
            max(overlap_values,default=0.0),
        "selected_original_geometry_valid":True,
        "national_topology_and_complete_coverage_verified":False,
        "original_geometries_persisted":False,
        "insured_exposure_or_policy_matched":False,
        "native_model_region_assignment_admitted":False,
        "any_cat_model_input_admitted":False,
    }


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--source-zip",required=True,type=Path)
    args=p.parse_args(argv)
    path=args.source_zip
    if path.is_symlink() or not path.is_file() or path.stat().st_size>MAX_ZIP_BYTES:
        _fail("original ZIP must be bounded nonsymlink local file")
    raw=path.read_bytes()
    print(json.dumps(inspect_pilot_bytes(
        raw,expected_sha256=PINNED_ORIGINAL_SHA256),sort_keys=True,
        indent=2,allow_nan=False))


if __name__ == "__main__":
    try:
        main()
    except (OSError,CensusZipError,PilotGeometryError) as exc:
        print("BLOCKED:",exc,file=sys.stderr)
        sys.exit(2)
