# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Two original sources, bounded actual first-20 building-to-parish spatial QC.

Original Census 2026 COUNTY SHA is independently pinned; a narrow original
Microsoft Louisiana-v2 ZIP byte range is source-metadata-checked in CI.
The first twenty Microsoft source polygons are not randomly selected.
This makes only aggregate geographic-match observations; NOT real insurer
exposure or model input. No full Microsoft source file is downloaded.
"""
from __future__ import annotations

import argparse
import io
import json
import math
from pathlib import Path
import re
import struct
import sys
import zipfile
import zlib

from research_runners.us_census_2026_county_zip_audit_v0 import STEM, MAX_ZIP_BYTES
from research_runners.us_census_2026_louisiana_64_parish_qc_v0 import (
    _la_positions, inspect_all_louisiana,
)
from research_runners.us_census_2026_parish_spatial_pilot_v0 import (
    PINNED_ORIGINAL_SHA256, _reconstruct_shape,
)

MS_PREFIX_BYTES = 65_536
MAX_UNCOMPRESSED_PREFIX = 1_048_576
MS_SOURCE = "Microsoft USBuildingFootprints Louisiana-v2"
MS_RESEARCH_ORIGINAL_ETAG = '"0x8DCFF4D6A6BD59D"'
MS_RESEARCH_ARCHIVE_BYTES = 83_974_949
MS_ZIP_MEMBER = "Louisiana.geojson"
MS_SOURCE_CRS = "EPSG:4326"   # GeoJSON RFC 7946 WGS84
CENSUS_SOURCE_CRS = "EPSG:4269"  # NAD83, as declared by original PRJ
METRIC_CRS = "EPSG:5070"  # CONUS Albers, metres; research crosswalk
BORDER_MARGIN_M = 10.0
MAX_SAMPLE_FEATURES = 20
MAX_VERTICES_PER_FOOTPRINT = 4096
REPORT_PROFILE = "OC_LA_2026_CENSUS_MS_REAL_PREFIX_SPATIAL_QC_V0"


class SourceJoinError(ValueError):
    pass


def _reject(reason):
    raise SourceJoinError("research-only Louisiana two-source join: " + reason)


def _source_geojson_prefix(prefix: bytes):
    """Decode just complete source GeoJSON features from fixed ZIP first range.

    The actual provider Range, exact original ETag and archive length
    are separately required by the fixed workflow. Never output positions.
    """
    if type(prefix) is not bytes or len(prefix) != MS_PREFIX_BYTES:
        _reject("must supply only exact fixed 65536-byte source ZIP prefix")
    if prefix[:4] != b"PK\x03\x04":
        _reject("original ZIP local-header signature missing")
    if len(prefix) < 30:
        _reject("truncated ZIP local header")
    _,version,flags,method,mtime,mdate,crc,packed,unpacked,nlen,xlen = (
        struct.unpack_from("<IHHHHHIIIHH",prefix,0)
    )
    data_start=30+nlen+xlen
    if (flags & 1 or method != 8 or
            not 1 <= nlen <= 128 or data_start >= len(prefix) or
            prefix[30:30+nlen] != MS_ZIP_MEMBER.encode("ascii")):
        _reject("source file is not the pinned plain-deflate Louisiana GeoJSON")
    if packed and packed != 83_974_765:
        _reject("ZIP local compressed length contradicts audited archive receipt")
    if unpacked and unpacked != 629_872_164:
        _reject("ZIP local uncompressed length contradicts audited archive receipt")
    try:
        z = zlib.decompressobj(-15)
        body = z.decompress(prefix[data_start:], MAX_UNCOMPRESSED_PREFIX+1)
        if len(body)>MAX_UNCOMPRESSED_PREFIX:
            _reject("too many decompressed original source bytes")
        text=body.decode("utf8",errors="strict")
    except (zlib.error,UnicodeError) as exc:
        raise SourceJoinError("original ZIP partial deflate/UTF8 decode failed") from exc
    if not re.search(r'"type"\s*:\s*"FeatureCollection"',text[:15000]):
        _reject("missing original FeatureCollection")
    begin=re.search(r'"features"\s*:\s*\[',text[:15000])
    if begin is None:
        _reject("missing bounded source features collection")
    decoder=json.JSONDecoder(parse_constant=lambda value: _reject("nonfinite source JSON"))
    pos=begin.end()
    polygons=[]
    from shapely.geometry import shape
    from shapely.errors import GEOSException
    for _ in range(MAX_SAMPLE_FEATURES):
        while pos<len(text) and text[pos] in " \n\r\t,":
            pos+=1
        if pos>=len(text) or text[pos] == "]":
            break
        try:
            obj,pos=decoder.raw_decode(text,pos)
        except (json.JSONDecodeError,TypeError) as exc:
            raise SourceJoinError("fewer than twenty complete source building objects") from exc
        if type(obj) is not dict or obj.get("type")!="Feature" or type(obj.get("geometry")) is not dict:
            _reject("source object is not an explicit GeoJSON Feature")
        geometry=obj["geometry"]
        if geometry.get("type") not in ("Polygon","MultiPolygon"):
            _reject("non-footprint original feature")
        # Prevent huge malformed source inputs from exhausting a later GIS
        # library even when the entire input prefix is bounded.
        vertices=0
        structures = ([geometry.get("coordinates")] if geometry["type"]=="Polygon"
                      else geometry.get("coordinates"))
        if type(structures) is not list or not structures:
            _reject("missing polygon ring structure")
        for polygon in structures:
            if type(polygon) is not list or not polygon:
                _reject("invalid source polygon")
            for ring in polygon:
                if type(ring) is not list or len(ring)<4 or ring[0]!=ring[-1]:
                    _reject("open original building ring")
                vertices+=len(ring)
                if vertices>MAX_VERTICES_PER_FOOTPRINT:
                    _reject("source polygon vertex budget exceeded")
                for position in ring:
                    if (type(position) is not list or len(position)!=2 or
                            any(type(x) not in (float,int) or not math.isfinite(x)
                                for x in position)):
                        _reject("invalid building coordinate")
        try:
            footprint=shape(geometry)
        except (GEOSException,TypeError,ValueError,IndexError) as exc:
            raise SourceJoinError("source building polygon parse failed") from exc
        if footprint.is_empty or not footprint.is_valid or footprint.area<=0:
            _reject("invalid source building polygon topology")
        a,b,c,d=footprint.bounds
        if not (-96<=a<=c<=-87 and 27<=b<=d<=34):
            _reject("building source polygon outside coarse Louisiana envelope")
        polygons.append(footprint)
    if len(polygons)!=MAX_SAMPLE_FEATURES:
        _reject("expected all twenty first source features")
    return tuple(polygons)


def classify_footprints(parishes, footprints, *, boundary_margin_m=BORDER_MARGIN_M):
    """Require entire original footprint inside one parish and >=10m border.

    Boundary, overlap and outside candidates are *reported*, never silently
    assigned to the nearest parish or silently omitted from denominators.
    """
    from shapely.ops import transform
    from pyproj import Transformer
    if (type(parishes) is not dict or not parishes or
            any(type(k) is not str or re.fullmatch(r"22[0-9]{3}",k) is None
                for k in parishes)
            or type(footprints) not in (tuple,list)
            or not 1<=len(footprints)<=MAX_SAMPLE_FEATURES
            or type(boundary_margin_m) not in (int,float)
            or not math.isfinite(boundary_margin_m)
            or not 0 < boundary_margin_m <= 100):
        _reject("bad original parish/source footprint scope")
    from shapely.geometry import Polygon, MultiPolygon
    to_metric_admin=Transformer.from_crs(CENSUS_SOURCE_CRS,METRIC_CRS,always_xy=True).transform
    to_metric_building=Transformer.from_crs(MS_SOURCE_CRS,METRIC_CRS,always_xy=True).transform
    fixed={}
    for code,g in sorted(parishes.items()):
        if not isinstance(g,(Polygon,MultiPolygon)) or g.is_empty or not g.is_valid:
            _reject("invalid source administrative geometry")
        fixed[code]=transform(to_metric_admin,g)
        if fixed[code].is_empty or not fixed[code].is_valid:
            _reject("invalid projected administrative geometry")
    from shapely.prepared import prep
    prepared={code:prep(g) for code,g in fixed.items()}
    result={"strict_matched":0,"boundary_or_datum_uncertain":0,
            "multiple_parish_intersections":0,"outside_all_parishes":0}
    code_counts={}
    for raw in footprints:
        if not isinstance(raw,(Polygon,MultiPolygon)) or raw.is_empty or not raw.is_valid or raw.area<=0:
            _reject("invalid original candidate footprint passed to matcher")
        g=transform(to_metric_building,raw)
        if g.is_empty or not g.is_valid or g.area<=0:
            _reject("invalid transformed source footprint")
        hits=[code for code in fixed if prepared[code].intersects(g)]
        if not hits:
            result["outside_all_parishes"]+=1
        elif len(hits)>1:
            result["multiple_parish_intersections"]+=1
        else:
            code=hits[0]
            if (not prepared[code].contains(g) or
                fixed[code].boundary.distance(g) <= boundary_margin_m):
                result["boundary_or_datum_uncertain"]+=1
            else:
                result["strict_matched"]+=1
                code_counts[code]=code_counts.get(code,0)+1
    if sum(result.values())!=len(footprints):
        _reject("source footprint result count not conserved")
    return result,code_counts


def verify_two_source_pilot(census_zip:bytes, microsoft_prefix:bytes):
    geo_receipt=inspect_all_louisiana(
        census_zip,expected_sha256=PINNED_ORIGINAL_SHA256)
    with zipfile.ZipFile(io.BytesIO(census_zip)) as archive:
        dbf=archive.read(f"{STEM}.dbf")
        shp=archive.read(f"{STEM}.shp")
        shx=archive.read(f"{STEM}.shx")
    indices=_la_positions(dbf)
    parishes={code:_reconstruct_shape(shp,shx,ordinal)[0]
              for code,ordinal in sorted(indices.items())}
    footprints=_source_geojson_prefix(microsoft_prefix)
    summary,groups=classify_footprints(parishes,footprints)
    return {
        "profile":REPORT_PROFILE,
        "census_original_zip_sha256_verified":geo_receipt["original_source_sha256"],
        "census_2026_louisiana_parish_geometries_validated":len(parishes),
        "microsoft_provider":MS_SOURCE,
        "microsoft_original_ETag_from_prior_source_metadata":MS_RESEARCH_ORIGINAL_ETAG,
        "microsoft_original_zip_size_from_prior_source_metadata":MS_RESEARCH_ARCHIVE_BYTES,
        "microsoft_compressed_prefix_bytes_inspected":len(microsoft_prefix),
        "actual_first_nonrandom_microsoft_footprints":len(footprints),
        "geometric_building_to_parish_classification_counts":summary,
        "matched_parish_count_in_first_twenty":len(groups),
        "geographic_boundary_margin_m":BORDER_MARGIN_M,
        "census_coordinate_reference":CENSUS_SOURCE_CRS,
        "microsoft_geojson_coordinate_reference":MS_SOURCE_CRS,
        "research_metric_coordinate_reference":METRIC_CRS,
        "coordinate_epoch_datum_transform_independently_verified":False,
        "building_source_imagery_vintage_verified":False,
        "complete_microsoft_archive_original_sha256_verified":False,
        "full_louisiana_footprint_inventory_verified":False,
        "sample_random_or_representative":False,
        "building_roofprints_are_confirmed_insured_assets":False,
        "per_feature_positions_or_source_ids_emitted":False,
        "original_source_data_persisted":False,
        "legal_and_scientific_admission_passed":False,
        "cat_model_input_admitted":False,
    }


def main(argv=None):
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--census-zip",type=Path,required=True)
    ap.add_argument("--ms-prefix",type=Path,required=True)
    args=ap.parse_args(argv)
    a,b=args.census_zip,args.ms_prefix
    if (a.is_symlink() or b.is_symlink() or
            not a.is_file() or not b.is_file() or
            a.stat().st_size>MAX_ZIP_BYTES or
            b.stat().st_size!=MS_PREFIX_BYTES):
        _reject("expected only bounded ordinary source receipt files")
    print(json.dumps(verify_two_source_pilot(a.read_bytes(),b.read_bytes()),
                     indent=2,sort_keys=True,allow_nan=False))


if __name__=="__main__":
    try:
        main()
    except (OSError,SourceJoinError,ValueError,zlib.error,struct.error) as exc:
        print("BLOCKED:",exc,file=sys.stderr)
        sys.exit(2)
