# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Tiny source-original prefix of Microsoft Louisiana ZIP for building QC.

Fetches ONLY first 65,536 compressed-source bytes, requires consistent
original ZIP metadata receipt and ETag, bounded raw-deflate decompression.
No full archive, building IDs, positions, source polygons or personal data
printed/persisted; nonrandom first records cannot estimate statewide quality.
"""
from __future__ import annotations

import argparse
import json
import math
import re
import struct
import sys
import zlib

from research_runners.microsoft_louisiana_original_zip_receipt_v0 import (
    URL, OriginalArchiveError, original_fetch, _request, probe,
)

SAMPLE_COMPRESSED_BYTES = 65_536
SAMPLE_MAX_UNCOMPRESSED_BYTES = 400_000
MAX_RECORDS = 20
MAX_PARSE_PREFIX = 15_000
SCHEMA = "opencatastrophe-ms-la-building-geojson-prefix-v0"


class SampleError(ValueError):
    pass


def sample(*, fetch=original_fetch):
    receipt = probe(fetch=fetch)
    n,tag = receipt["http_archive_size_bytes"],receipt["original_etag_metadata_only_not_sha256"]
    start,end=0,SAMPLE_COMPRESSED_BYTES-1
    status,h,raw=fetch(_request(start=start,end=end,etag=tag),SAMPLE_COMPRESSED_BYTES)
    if (status!=206 or len(raw)!=SAMPLE_COMPRESSED_BYTES
        or h.get("content-range")!=f"bytes {start}-{end}/{n}"
        or h.get("content-length")!=str(SAMPLE_COMPRESSED_BYTES)
        or h.get("etag")!=tag):
        raise SampleError("provider source prefix changed or ignored Range")
    if len(raw)<30 or raw[:4]!=b"PK\x03\x04":
        raise SampleError("original ZIP member header missing")
    _,version,flags,method,mtime,mdate,crc,compressed,unpacked,nlen,xlen=struct.unpack(
        "<IHHHHHIIIHH",raw[:30])
    start_data=30+nlen+xlen
    if (flags & 1 or method!=8 or not 1<=nlen<=128
        or start_data>=SAMPLE_COMPRESSED_BYTES
        or raw[30:30+nlen].decode("utf-8")!=receipt["source_member_name"]):
        raise SampleError("unexpected source compression/member/filename")
    # ZIP local fields might be zero under a ZIP data descriptor; the
    # central directory provides the validated exact archive member size.
    if compressed and compressed!=receipt["source_member_compressed_bytes"]:
        raise SampleError("original local/central compressed length mismatch")
    if unpacked and unpacked!=receipt["source_member_uncompressed_bytes"]:
        raise SampleError("original local/central uncompressed length mismatch")
    try:
        z=zlib.decompressobj(-15)
        plain=z.decompress(raw[start_data:],SAMPLE_MAX_UNCOMPRESSED_BYTES+1)
    except zlib.error as exc:
        raise SampleError("original deflate data invalid") from exc
    if len(plain)>SAMPLE_MAX_UNCOMPRESSED_BYTES:
        raise SampleError("excessive decompressed source prefix")
    try:
        text=plain.decode("utf-8",errors="strict")
    except UnicodeError as exc:
        raise SampleError("source prefix is not valid UTF8") from exc
    head=text[:MAX_PARSE_PREFIX]
    if '"FeatureCollection"' not in head:
        raise SampleError("expected GeoJSON FeatureCollection prefix")
    match=re.search(r'"features"\s*:\s*\[', head)
    if match is None:
        raise SampleError("original GeoJSON features array not in bounded prefix")
    pos=match.end()
    decoder=json.JSONDecoder(parse_constant=lambda x:(_ for _ in ()).throw(
        SampleError("nonfinite source JSON constant")))
    counts={"Polygon":0,"MultiPolygon":0}
    invalid=0
    sample_count=0
    seen_inside=0
    try:
        from shapely.geometry import shape
    except ImportError as exc:
        raise SampleError("reviewed spatial runtime unavailable") from exc
    while sample_count<MAX_RECORDS:
        while pos<len(text) and text[pos] in " \t\r\n,":
            pos+=1
        if pos>=len(text) or text[pos]=="]":
            break
        try:
            item,new_pos=decoder.raw_decode(text,pos)
        except json.JSONDecodeError:
            # Unfinished final object is expected at bounded deflate EOF.
            break
        pos=new_pos
        if type(item) is not dict or item.get("type")!="Feature":
            raise SampleError("first official records not GeoJSON Features")
        if "geometry" not in item or type(item["geometry"]) is not dict:
            raise SampleError("missing original footprint")
        geom=item["geometry"]
        if geom.get("type") not in counts:
            raise SampleError("nonpolygon original footprint")
        try:
            g=shape(geom)
        except (TypeError,ValueError,IndexError) as exc:
            raise SampleError("unparseable original building polygon") from exc
        if g.is_empty or not g.is_valid or g.area<=0:
            invalid+=1
        else:
            bbox=g.bounds
            if not all(math.isfinite(a) for a in bbox):
                raise SampleError("nonfinite source coordinates")
            if -96<=bbox[0]<=bbox[2]<=-87 and 27<=bbox[1]<=bbox[3]<=34:
                seen_inside+=1
            else:
                raise SampleError("sample outside coarse Louisiana source extent")
        counts[geom["type"]]+=1
        sample_count+=1
    if sample_count<1:
        raise SampleError("no complete feature in bounded source prefix")
    return {
        "schema":SCHEMA,
        "original_archive_size_bytes":n,
        "original_source_member":receipt["source_member_name"],
        "original_archive_source_ETag_metadata_not_SHA":tag,
        "original_compressed_prefix_bytes_read":SAMPLE_COMPRESSED_BYTES,
        "uncompressed_prefix_bytes_decoded":len(plain),
        "first_completed_nonrandom_building_features":sample_count,
        "valid_sample_polygon_features":sample_count-invalid,
        "invalid_sample_polygon_features":invalid,
        "source_sample_polygon_count":counts["Polygon"],
        "source_sample_multipolygon_count":counts["MultiPolygon"],
        "valid_sample_footprints_in_louisiana_sanity_bbox":seen_inside,
        "source_record_positions_or_ids_emitted":False,
        "original_full_archive_sha256_verified":False,
        "sample_statistically_representative":False,
        "source_imagery_vintage_verified":False,
        "building_to_parish_join_executed":False,
        "insured_asset_or_policy_verified":False,
        "cat_model_input_admitted":False,
    }


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--live",action="store_true")
    args=p.parse_args(argv)
    if not args.live:
        print("BLOCKED: explicit --live required",file=sys.stderr)
        return 2
    try:
        out=sample()
    except (SampleError,OriginalArchiveError,OSError,UnicodeError,
            TypeError,ValueError,struct.error) as exc:
        print("BLOCKED:",exc,file=sys.stderr)
        return 2
    print(json.dumps(out,sort_keys=True,indent=2))
    return 0


if __name__=="__main__":
    raise SystemExit(main())
