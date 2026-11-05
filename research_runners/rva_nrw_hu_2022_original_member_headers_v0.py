# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Inspect official NRW 2022 Hausumringe PRJ/DBF/SHP HEADERS through byte ranges only.

Still NO full ZIP, NO actual individual feature, NO WGS84 OED site, NO insured
location and NO full-source SHA-256. Only original source byte headers/prefixes.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import struct
import sys
import zlib

from rva_nrw_hu_2022_original_zip_range_receipt_v0 import (
    URL,_head,_range,eocd_from_last_bytes,parse_directory,MAX_TAIL,
    OriginalZipBlocked,
)

MAX_MEMBER_PREFIX=32768
MAX_LOCAL_EXTRA=4096
MAX_OUTPUT=8192


def read_member_prefix(member:dict,total:int,*,range_fn=_range)->tuple[bytes,bool]:
    off=member["local_header_offset"]
    if type(off) is not int or not 0<=off<total-30:
        raise OriginalZipBlocked("ZIP local member offset invalid")
    local=range_fn(off,off+29,total)
    if len(local)!=30 or local[:4]!=b"PK\x03\x04":
        raise OriginalZipBlocked("ZIP local member header missing")
    (sig,version,flags,method,tm,date,crc,csize,usize,nlen,xlen)=struct.unpack("<IHHHHHIIIHH",local)
    if (flags & 1 or flags & 0x40 or method!=8 or method!=member["method"]
        or nlen==0 or nlen+xlen>MAX_LOCAL_EXTRA):
        raise OriginalZipBlocked("ZIP member encryption/method/length unsupported")
    ident=range_fn(off+30,off+30+nlen+xlen-1,total)
    name_bytes=ident[:nlen]
    try:
        name=name_bytes.decode("utf-8" if flags&0x800 else "cp437")
    except UnicodeDecodeError as exc:
        raise OriginalZipBlocked("ZIP local name decoding failed") from exc
    if name!=member["name"]:
        raise OriginalZipBlocked("ZIP local vs central member identity mismatch")
    compressed_start=off+30+nlen+xlen
    compressed_length=member["compressed_bytes"]
    if (type(compressed_length) is not int or compressed_length<1
        or compressed_start+compressed_length>total):
        raise OriginalZipBlocked("ZIP member data region outside archive")
    nbytes=min(compressed_length,MAX_MEMBER_PREFIX)
    compressed=range_fn(compressed_start,compressed_start+nbytes-1,total)
    if len(compressed)!=nbytes:
        raise OriginalZipBlocked("compressed member prefix length changed")
    decoder=zlib.decompressobj(-15)
    try:
        data=decoder.decompress(compressed,MAX_OUTPUT)
    except zlib.error as exc:
        raise OriginalZipBlocked("ZIP compressed member prefix corrupt") from exc
    if len(data)>MAX_OUTPUT or len(data)==0:
        raise OriginalZipBlocked("ZIP member prefix decode missing or oversized")
    complete=compressed_length<=MAX_MEMBER_PREFIX
    if complete:
        if (not decoder.eof or len(data)!=member["uncompressed_bytes"]
            or zlib.crc32(data)&0xffffffff != int(member["crc32_hex"],16)):
            raise OriginalZipBlocked("small full member CRC/size mismatch")
    return data, complete


def verify_headers(members:list[dict],total:int,*,range_fn=_range)->dict:
    by_suffix={r["name"].lower().rsplit(".",1)[-1]:r
               for r in members if "." in r["name"]}
    for suffix in ("prj","dbf","shp","shx"):
        if suffix not in by_suffix:
            raise OriginalZipBlocked("required original HU source component absent")
    # All four sources must represent one exact original shapefile family.
    stems={x["name"].rsplit(".",1)[0] for x in by_suffix.values()}
    if len(stems)!=1 or stems!={"2022_hu_shp"}:
        raise OriginalZipBlocked("original HU member stem mismatch")
    prj,complete=read_member_prefix(by_suffix["prj"],total,range_fn=range_fn)
    if not complete or len(prj)<100 or len(prj)>8192:
        raise OriginalZipBlocked("original PRJ not exactly read")
    try: prjtxt=prj.decode("ascii")
    except UnicodeDecodeError as exc:
        raise OriginalZipBlocked("original PRJ non-ASCII or corrupt") from exc
    if not any(s in prjtxt.upper() for s in ("ETRS","UTM","TRANSVERSE_MERCATOR")):
        raise OriginalZipBlocked("projected CRS original WKT not identified")
    dbf,_=read_member_prefix(by_suffix["dbf"],total,range_fn=range_fn)
    if len(dbf)<33:
        raise OriginalZipBlocked("original DBF source header incomplete")
    nrecords=struct.unpack_from("<I",dbf,4)[0]
    header_length=struct.unpack_from("<H",dbf,8)[0]
    record_length=struct.unpack_from("<H",dbf,10)[0]
    if (not 1_000_000<nrecords<30_000_000 or not 33<=header_length<=4096
        or (header_length-33)%32!=0 or not 1<=record_length<=500
        or len(dbf)<header_length or dbf[header_length-1]!=0x0d
        or abs((header_length+record_length*nrecords)-by_suffix["dbf"]["uncompressed_bytes"])>2):
        raise OriginalZipBlocked("DBF header count/length/field descriptors mismatch")
    fields=[]
    for i in range(32,header_length-1,32):
        raw=dbf[i:i+32]
        if len(raw)!=32:
            raise OriginalZipBlocked("truncated DBF descriptor")
        name=raw[:11].split(b"\x00",1)[0].decode("ascii","strict")
        ftype=chr(raw[11])
        length=raw[16]
        if not name or len(name)>11 or length<1:
            raise OriginalZipBlocked("invalid DBF column structure")
        fields.append({"name":name,"type":ftype,"length":length})
    shp,_=read_member_prefix(by_suffix["shp"],total,range_fn=range_fn)
    if len(shp)<100:
        raise OriginalZipBlocked("source SHP header missing")
    if (struct.unpack_from(">I",shp,0)[0]!=9994
        or struct.unpack_from("<I",shp,28)[0]!=1000
        or struct.unpack_from(">I",shp,24)[0]*2 != by_suffix["shp"]["uncompressed_bytes"]):
        raise OriginalZipBlocked("SHP source header semantics corrupted")
    shape_type=struct.unpack_from("<I",shp,32)[0]
    if shape_type not in (5,15,25):
        raise OriginalZipBlocked("expected original polygon-type SHP source")
    bbox=list(struct.unpack_from("<dddd",shp,36))
    if not all(math.isfinite(x) for x in bbox) or bbox[0]>=bbox[2] or bbox[1]>=bbox[3]:
        raise OriginalZipBlocked("invalid source projected extent")
    shx=by_suffix["shx"]["uncompressed_bytes"]
    if shx<100 or (shx-100)%8:
        raise OriginalZipBlocked("SHP index length invalid")
    shx_n=(shx-100)//8
    if shx_n!=nrecords:
        raise OriginalZipBlocked("DBF record count does not match SHX record count")
    return {
        "schema":"NRW_HU_2022_ORIGINAL_RANGE_HEADER_RECEIPT_V0",
        "source_original_url":URL,
        "original_2022_HU_DBF_row_count":nrecords,
        "original_2022_HU_SHX_index_record_count":shx_n,
        "original_DBF_fields":fields,
        "original_DBF_record_length":record_length,
        "original_DBF_header_length":header_length,
        "original_polygon_SHP_shape_type":shape_type,
        "original_projected_bbox_in_source_units":bbox,
        "original_prj_wkt_sha256":hashlib.sha256(prj).hexdigest(),
        "original_prj_wkt_length":len(prj),
        "original_prj_text_excerpt":prjtxt[:110],
        "actual_original_ZIP_full_sha256_verified":False,
        "original_SHP_and_DBF_member_CRCs_fully_verified":False,
        "source_2022_building_footprints_count_as_2022_zensus_living_space_buildings":False,
        "real_RV_insured_site_geometry_observed":False,
        "EPSG_4647_to_4326_conversion_executed":False,
        "individual_OED_sites_geocoded":False,
        "native_German_CAT_model_ready":False,
    }


def probe():
    total=_head()
    tail_start=max(0,total-MAX_TAIL)
    tail=_range(tail_start,total-1,total)
    end=eocd_from_last_bytes(tail,tail_start,total)
    start=end["central_offset"]
    directory=_range(start,start+end["central_size"]-1,total)
    members=parse_directory(directory,end["member_count"])
    out=verify_headers(members,total)
    out["original_ZIP_HEAD_byte_count"]=total
    out["original_central_directory_sha256"]=hashlib.sha256(directory).hexdigest()
    out["original_downloaded_total_bounded_header_bytes"]="<~300KiB"
    return out


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--live",action="store_true",help="opt-in header-only bounded official source requests")
    args=ap.parse_args()
    if not args.live:
        ap.exit(2,"BLOCKED: opt-in --live required\n")
    print(json.dumps(probe(),sort_keys=True,ensure_ascii=False,indent=2))
    return 0

if __name__=="__main__":
    try:sys.exit(main())
    except (OSError,ValueError,UnicodeDecodeError,struct.error) as exc:
        print("NRW_HU_2022_MEMBER_HEADER_BLOCKED: "+str(exc),file=sys.stderr)
        sys.exit(2)
