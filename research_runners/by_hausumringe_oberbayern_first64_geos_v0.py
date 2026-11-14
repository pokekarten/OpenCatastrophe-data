#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""BVV HU-BY first 64 original Shapefile records: bounded GEOS ring QA.

Source is the one independently SHA-identified 49,197-byte ZIP Range
already used for the verified first original Polygon. This reads exactly
one byte range and processes a fixed leading, NONRANDOM selection of 64
records from the original partial DEFLATE stream.

Only anonymous aggregate topology counts and hashes are printed.
No original coordinates, source features, polygon arrays, owner/insured
identity, asset positions, original bytes or addresses are persisted.
Not scientific representativeness or a 2020 GHSL ground-truth sample.
"""
from __future__ import annotations

from datetime import datetime, timezone
import argparse
import hashlib
import json
import math
import ssl
import struct
import sys
from urllib.error import HTTPError, URLError
from urllib.request import Request, ProxyHandler, HTTPSHandler, build_opener
import zlib

from research_runners.by_hausumringe_oberbayern_zip_prefix_v0 import (
    URL, SOURCE, NoRedirect,
)
from research_runners.by_hausumringe_oberbayern_shp_first_original_v0 import (
    START, END, TOTAL, READ_BYTES, ZIP_HEADER_BYTES, MAX_INFLATED_PREVIEW,
    BVVShpPreviewBlocked, inspect_original_shp_prefix,
    inspect_bounded_shp_preview, SHP_HEADER_BYTES,
)

FIRST_RECORDS = 64
MAX_RECORD_POINTS = 4096
MAX_PARTS = 64
EXACT_ORIGINAL_RANGED_SHA256 = "8a3c95bbbca493b192f6923fa4b6060798f561775f647bd34ffd4fc3af316f80"
FIRST_ORIGINAL_CONTENT_SHA256 = "f6c7b5bc74f1d040a7280f0eb238c0f007aa6126c8c711f71f255b4f6f0c00ab"


class BoundedGEOSBlocked(BVVShpPreviewBlocked):
    """Original source identity/first-64 geometry preview unavailable."""


def inspect_first64_decoded(decoded: bytes) -> dict:
    """Pure offline first-64 binary/GEOs checks on caller-provided source prefix.

    Not a provider proof: verify_original_source() pins source response SHA
    independently before this function is invoked on any real data.
    """
    if type(decoded) is not bytes or not 100 <= len(decoded) <= MAX_INFLATED_PREVIEW:
        raise BoundedGEOSBlocked("Shapefile preview bytes outside reviewed limit")
    first_check = inspect_bounded_shp_preview(decoded)
    if first_check["original_first_record_content_sha256"] != FIRST_ORIGINAL_CONTENT_SHA256:
        # Synthetic tests should exercise the same scientific code without
        # pretending their first Polygon matches the real original digest.
        return _inspect_native_records(decoded, first_record_receipt_pinned=False)
    return _inspect_native_records(decoded, first_record_receipt_pinned=True)


def _inspect_native_records(decoded: bytes, *, first_record_receipt_pinned: bool) -> dict:
    try:
        from shapely.geometry import LinearRing, Polygon
    except ImportError as exc:
        raise BoundedGEOSBlocked("independent Shapely/GEOS dependency required") from exc
    n=0
    pos=SHP_HEADER_BYTES
    ring_count=0
    geos_invalid_rings=0
    geos_invalid_simple_part_polygons=0
    multipart_records=0
    null_shapes=0
    total_points=0
    first64_bytes=bytearray()
    xmin,ymin,xmax,ymax=struct.unpack_from("<4d",decoded,36)
    while n<FIRST_RECORDS:
        if pos+8>len(decoded):
            raise BoundedGEOSBlocked("original prefix ended before fixed first 64 records")
        record_no,content_words=struct.unpack_from(">II",decoded,pos)
        size=content_words*2
        if record_no!=n+1 or not 4<=size<=MAX_INFLATED_PREVIEW:
            raise BoundedGEOSBlocked("noncontiguous original record number or invalid size")
        end=pos+8+size
        if end>len(decoded):
            raise BoundedGEOSBlocked("first 64 original records not complete")
        raw=memoryview(decoded)[pos+8:end]
        shape=struct.unpack_from("<I",raw,0)[0]
        first64_bytes.extend(decoded[pos:end])
        if shape==0:
            if size!=4:
                raise BoundedGEOSBlocked("invalid Shapefile NULL shape length")
            null_shapes+=1
        elif shape==5:
            if size<128:
                raise BoundedGEOSBlocked("original Polygon source content too short")
            bx0,by0,bx1,by1=struct.unpack_from("<4d",raw,4)
            parts,points=struct.unpack_from("<II",raw,36)
            if (not 1<=parts<=MAX_PARTS or not 4<=points<=MAX_RECORD_POINTS
                or 44+4*parts+16*points!=size
                or not all(math.isfinite(v) for v in (bx0,by0,bx1,by1))
                or not (xmin<=bx0<bx1<=xmax and ymin<=by0<by1<=ymax)):
                raise BoundedGEOSBlocked("invalid original multi-ring native Polygon frame or bbox")
            offsets=struct.unpack_from("<"+"I"*parts,raw,44)
            if offsets[0]!=0 or any(offsets[i]>=offsets[i+1] for i in range(parts-1)):
                raise BoundedGEOSBlocked("unreviewed Shape Polygon ring start offsets")
            if parts>1: multipart_records+=1
            edges=tuple(offsets)+(points,)
            actual_min_x=actual_min_y=float("inf")
            actual_max_x=actual_max_y=float("-inf")
            for part in range(parts):
                a,b=edges[part],edges[part+1]
                if b-a<4: raise BoundedGEOSBlocked("short Polygon ring")
                coords=[]
                for i in range(a,b):
                    x,y=struct.unpack_from("<dd",raw,44+4*parts+16*i)
                    if (not math.isfinite(x) or not math.isfinite(y)
                            or not xmin<=x<=xmax or not ymin<=y<=ymax):
                        raise BoundedGEOSBlocked("nonfinite/out-of-bounds source native coordinates")
                    actual_min_x=min(actual_min_x,x);actual_max_x=max(actual_max_x,x)
                    actual_min_y=min(actual_min_y,y);actual_max_y=max(actual_max_y,y)
                    coords.append((x,y))
                if coords[0]!=coords[-1]:
                    raise BoundedGEOSBlocked("source native Polygon has open ring")
                ring=LinearRing(coords)
                if not ring.is_simple or not ring.is_valid:
                    geos_invalid_rings+=1
                if not Polygon(coords).is_valid:
                    geos_invalid_simple_part_polygons+=1
                ring_count+=1
            if (not math.isclose(actual_min_x,bx0,rel_tol=0,abs_tol=1e-6)
                or not math.isclose(actual_max_x,bx1,rel_tol=0,abs_tol=1e-6)
                or not math.isclose(actual_min_y,by0,rel_tol=0,abs_tol=1e-6)
                or not math.isclose(actual_max_y,by1,rel_tol=0,abs_tol=1e-6)):
                raise BoundedGEOSBlocked("source record bounding box differs from native vertices")
            total_points+=points
        else:
            raise BoundedGEOSBlocked("unexpected first64 original shape geometry type")
        n+=1
        pos=end
    return {
        "profile":"oc-bvv-oberbayern-first64-original-shp-geos-ring-qa-v0",
        "source_id":SOURCE,
        "original_source_64_leading_records_nonrandom":True,
        "native_source_records_structurally_decoded":n,
        "native_source_polygon_records":n-null_shapes,
        "native_source_null_shape_records":null_shapes,
        "native_source_multipart_records":multipart_records,
        "native_source_rings_checked_with_geos":ring_count,
        "native_source_vertices_transiently_checked":total_points,
        "geos_invalid_rings":geos_invalid_rings,
        "geos_invalid_single_part_polygon_interpretations":geos_invalid_simple_part_polygons,
        "geos_full_original_multipart_hole_assembly_tested":False,
        "first64_uncompressed_record_bytes_sha256":hashlib.sha256(first64_bytes).hexdigest(),
        "native_record64_ending_uncompressed_byte_offset_not_persisted":True,
        "original_first_record_source_SHA_identity_matched":first_record_receipt_pinned,
        "native_source_coords_polygons_or_record_identifiers_persisted":False,
        "original_complete_SHX_SHP_SHA_or_crc_verified":False,
        "scientifically_representative_buildings_sample":False,
        "survey_snapshot_vintage_verified":False,
        "2020_ghsl_independent_ground_truth":False,
        "insurance_CAT_model_input_approved":False,
    }


def inspect_live_original_source(raw: bytes, *, status: int, response_url: str, headers) -> dict:
    if hashlib.sha256(raw).hexdigest()!=EXACT_ORIGINAL_RANGED_SHA256:
        raise BoundedGEOSBlocked("original 2026-11-12 source response SHA-256 drift")
    original=inspect_original_shp_prefix(raw,status=status,response_url=response_url,headers=headers)
    compressed=raw[ZIP_HEADER_BYTES:]
    try:
        stream=zlib.decompressobj(wbits=-15)
        decoded=stream.decompress(compressed,MAX_INFLATED_PREVIEW+1)
    except zlib.error as exc:
        raise BoundedGEOSBlocked("original source compressed record prefix corrupt") from exc
    if (len(decoded)>MAX_INFLATED_PREVIEW or stream.eof
          or stream.unused_data or stream.unconsumed_tail):
        raise BoundedGEOSBlocked("unbounded/complete original source compressed frame")
    result=inspect_first64_decoded(decoded)
    if not result["original_first_record_source_SHA_identity_matched"]:
        raise BoundedGEOSBlocked("first original Polygon record SHA does not match source")
    return {
        **original,**result,
        "original_http_response_sha256":EXACT_ORIGINAL_RANGED_SHA256,
        "first64_geos_review_is_bounded_not_whole_region":True,
        "source_geometry_or_pixels_persisted":False,
        "model_input_approved":False,
    }


def probe() -> dict:
    req=Request(URL,method="GET",headers={
        "Range":f"bytes={START}-{END}",
        "Accept-Encoding":"identity",
        "Accept":"application/zip",
        "User-Agent":"OpenCatastrophe-BVV-First64-Shape-GEOS-Research/0.1",
    })
    try:
        with build_opener(ProxyHandler({}),NoRedirect(),
                          HTTPSHandler(context=ssl.create_default_context())
                          ).open(req,timeout=35) as res:
            if res.status!=206:raise BoundedGEOSBlocked("source ignored HTTP Range")
            raw=res.read(READ_BYTES+1)
            result=inspect_live_original_source(raw,status=res.status,
                response_url=res.geturl(),headers=res.headers)
    except (HTTPError,URLError,OSError,TimeoutError) as exc:
        raise BoundedGEOSBlocked("official BVV original bounded source unavailable") from exc
    result["retrieved_at_utc"]=datetime.now(timezone.utc).isoformat()
    return result


def main(argv=None) -> int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--live",action="store_true")
    args=p.parse_args(argv)
    if not args.live:
        p.error("original source must run on reviewed trusted main only")
    try:
        print(json.dumps(probe(),sort_keys=True,allow_nan=False))
        return 0
    except (BoundedGEOSBlocked,BVVShpPreviewBlocked,ValueError) as exc:
        print("BLOCKED: "+str(exc),file=sys.stderr)
        return 2


if __name__=="__main__":
    raise SystemExit(main())
