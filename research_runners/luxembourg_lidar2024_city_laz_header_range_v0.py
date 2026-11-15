#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Read only the original LAS public header of the fixed city tile via ZIP HTTP206.

Original 1.7GB ZIP and LAZ member are never transferred. A ZIP member with
compression method != STORED is recorded as blocked; no decompression is
attempted. Even valid LAS headers DO NOT report any observed class 5/6 points.
All network inputs/outputs are fixed original source metadata only.
"""
from __future__ import annotations

import json
import struct
from urllib.request import build_opener
from urllib.error import HTTPError, URLError

from research_runners.luxembourg_lidar2024_copc_group_resource_head_v0 import (
    OFFICIAL_API, NoRedirect, _only_publisher_url,
    _source_digest_from_metadata, ArchiveReceiptError,
)
from research_runners.luxembourg_lidar2024_city_copc_zip_directory_range_v0 import (
    CITY_RESOURCE_ID, CITY_GROUP, CITY_ORIGINAL_BYTES, CITY_PUBLISHER_SHA1,
    CITY_STUDY_TILE, ZIP_TAIL_BYTES, parse_eocd, read_http, _request,
    ZipRangeError, MAX_ZIP_MEMBERS,
)

MAX_NAME=240
MAX_EXTRA=2048


class LAZHeaderError(ValueError):
    """A source byte range or LAS header failed exact original contract."""


def city_member(directory: bytes, *, expected_members: int) -> dict:
    """Use original ZIP CD without downloading or revealing arbitrary filenames."""
    if not isinstance(directory, bytes) or not 1 <= expected_members <= MAX_ZIP_MEMBERS:
        raise LAZHeaderError("Invalid ZIP source central-directory candidate")
    found=[]
    pos=0
    for _ in range(expected_members):
        if pos+46>len(directory):
            raise LAZHeaderError("Truncated ZIP central directory")
        parts=struct.unpack_from("<IHHHHHHIIIHHHHHII", directory, pos)
        if parts[0] != 0x02014B50:
            raise LAZHeaderError("Non ZIP central-directory source header")
        flags,method=parts[3],parts[4]
        compressed,uncompressed=parts[8],parts[9]
        namelen,extralen,commentlen=parts[10:13]
        local_offset=parts[16]
        nextpos=pos+46+namelen+extralen+commentlen
        if (nextpos>len(directory) or not 1<=namelen<=MAX_NAME
            or extralen>MAX_EXTRA or flags & 1 or flags & 0x40
            or method not in (0,8) or local_offset == 0xFFFFFFFF
            or compressed == 0xFFFFFFFF or uncompressed == 0xFFFFFFFF):
            raise LAZHeaderError("Unsupported encrypted/ZIP64/invalid source ZIP member")
        raw=directory[pos+46:pos+46+namelen]
        try:
            name=raw.decode("utf-8" if flags & 0x800 else "cp437")
        except UnicodeError as exc:
            raise LAZHeaderError("Unsupported source ZIP name encoding") from exc
        if name.startswith("/") or "\\" in name or ":" in name or any(
            bit in ("", ".", "..") for bit in name.rstrip("/").split("/")
        ):
            raise LAZHeaderError("Unsafe source ZIP member path")
        if CITY_STUDY_TILE in name:
            if not name.lower().endswith(".laz"):
                raise LAZHeaderError("City tile member is not LAZ")
            found.append(dict(
                name_raw=raw, flags=flags, method=method, offset=local_offset,
                compressed=compressed, uncompressed=uncompressed
            ))
        pos=nextpos
    if pos!=len(directory) or len(found)!=1:
        raise LAZHeaderError("Original ZIP directory differs from single selected city tile")
    if found[0]["compressed"] <= 0 or found[0]["uncompressed"] < 235:
        raise LAZHeaderError("Original selected LAZ member size invalid")
    return found[0]


def local_file_data_offset(header: bytes, member: dict) -> tuple[int,int]:
    if not isinstance(header, bytes) or len(header)!=30:
        raise LAZHeaderError("Original local ZIP header must be exactly 30 bytes")
    fields=struct.unpack("<IHHHHHIIIHH",header)
    if fields[0]!=0x04034B50 or fields[2]!=member["flags"] or fields[3]!=member["method"]:
        raise LAZHeaderError("ZIP local/header compression or flag drift")
    name_len,extra_len=fields[-2:]
    if name_len!=len(member["name_raw"]) or extra_len>MAX_EXTRA:
        raise LAZHeaderError("Unexpected ZIP local member path or oversized extra field")
    data_offset=member["offset"]+30+name_len+extra_len
    if (not 0 < data_offset < CITY_ORIGINAL_BYTES
        or data_offset+member["compressed"]>CITY_ORIGINAL_BYTES):
        raise LAZHeaderError("Original ZIP member exceeds frozen archive byte budget")
    return data_offset,name_len+extra_len


def las_prefix_info(header: bytes, *, member_size: int) -> dict:
    """Only public LAS prefix fields; never bounding boxes or point contents."""
    if not isinstance(header,bytes) or len(header)!=110 or header[:4]!=b"LASF":
        raise LAZHeaderError("No original LASF signature at selected LAZ data start")
    major,minor=header[24],header[25]
    hsize=struct.unpack_from("<H",header,94)[0]
    point_data_start=struct.unpack_from("<I",header,96)[0]
    vlrs=struct.unpack_from("<I",header,100)[0]
    rawformat=header[104]
    point_len=struct.unpack_from("<H",header,105)[0]
    legacy=struct.unpack_from("<I",header,107)[0] if len(header)>=111 else None
    if (major!=1 or minor not in (2,3,4)
        or hsize != {2:227,3:235,4:375}[minor]
        or point_data_start < hsize or point_data_start >= member_size
        or not 0 <= vlrs <= 512 or rawformat & 0x40
        or (rawformat & 0x3F)>10 or not 1 <= point_len <= 1024):
        raise LAZHeaderError("Invalid LAS version/header, point format or point-offset")
    return dict(version=f"{major}.{minor}",header_size=hsize,
                point_data_offset=point_data_start,vlr_count=vlrs,
                point_record_format=rawformat & 0x3f,
                laz_compression_flag_present=bool(rawformat & 0x80),
                point_record_length=point_len)


def complete_las_header(prefix:bytes, remainder:bytes, preliminary:dict) -> dict:
    total=prefix+remainder
    if len(total)!=preliminary["header_size"]:
        raise LAZHeaderError("Original LAS header size changed between byte ranges")
    major,minor=total[24],total[25]
    if major!=1 or str(minor)!=preliminary["version"].split(".")[1]:
        raise LAZHeaderError("Original LAS version changed between byte ranges")
    legacy_points=struct.unpack_from("<I",total,107)[0]
    extended_points=struct.unpack_from("<Q",total,247)[0] if minor==4 else None
    total_points=extended_points if minor==4 and extended_points else legacy_points
    if not 1<=total_points<=200000000:
        raise LAZHeaderError("Unbounded/empty declared point count in original LAS header")
    return {
        "las_version":preliminary["version"],
        "point_record_format":preliminary["point_record_format"],
        "point_record_bytes":preliminary["point_record_length"],
        "laz_compressed_bit_declared":preliminary["laz_compression_flag_present"],
        "point_data_offset_bytes":preliminary["point_data_offset"],
        "variable_length_record_count_declared":preliminary["vlr_count"],
        "original_tile_points_declared_by_las_header":total_points,
        "original_las_header_bytes_checked":len(total),
        "original_crs_from_vlr_verified":False,
        "copc_vlr_verified":False,
        "building_class_6_points_counted":False,
        "high_vegetation_class_5_points_counted":False,
        "actual_point_records_read":False,
    }


MAX_PUBLIC_VLR_BYTES=32768


def inspect_public_vlrs(content:bytes, *, declared_count:int,
                        public_point_offset:int, las_header_size:int,
                        selected_laz_size:int) -> dict:
    """Read LAS public VLRs only: no source point records, class counts or coordinates."""
    if (not isinstance(content,bytes) or not 0<len(content)<=MAX_PUBLIC_VLR_BYTES
        or not 1<=declared_count<=512 or
        len(content)!=public_point_offset-las_header_size):
        raise LAZHeaderError("Unbounded/missing original public LAS VLR section")
    pos=0
    vlr_codes=[]
    copc_info=None
    for i in range(declared_count):
        if pos+54>len(content):
            raise LAZHeaderError("Truncated original LAS VLR header")
        reserved,who,record_id,body_bytes,description=struct.unpack_from(
            "<H16sHH32s",content,pos
        )
        try:
            owner=who.split(b"\0",1)[0].decode("ascii")
        except UnicodeError as exc:
            raise LAZHeaderError("Unparseable original VLR type") from exc
        end=pos+54+body_bytes
        if end>len(content):
            raise LAZHeaderError("VLR payload passes public point-data offset")
        vlr_codes.append((owner,record_id))
        if owner=="copc" and record_id==1:
            if i!=0 or body_bytes!=160 or copc_info is not None:
                raise LAZHeaderError("COPC info VLR is misplaced or wrong size")
            data=content[pos+54:end]
            nums=struct.unpack("<5d2Q2d11Q",data)
            if (not all(__import__("math").isfinite(x) for x in (*nums[:5],*nums[7:9]))
                or nums[3]<=0 or nums[4]<=0
                or nums[5]<=public_point_offset
                or not 32<=nums[6]<=MAX_PUBLIC_VLR_BYTES
                or nums[5]+nums[6]>selected_laz_size
                or any(nums[9:])
                or nums[7]>nums[8]):
                raise LAZHeaderError("COPC hierarchy location, extents or reserved bytes invalid")
            copc_info={
                "copc_info_vlr_first_and_160_bytes_verified":True,
                "copc_root_hierarchy_offset_within_selected_laz":nums[5],
                "copc_root_hierarchy_size_bytes":nums[6],
                "root_hierarchy_page_downloaded":False,
            }
        pos=end
    if pos<len(content) and any(content[pos:]):
        raise LAZHeaderError("Unexpected nonzero public LAS VLR padding")
    return {
        "public_las_vlr_region_bytes_checked":len(content),
        "actual_public_vlr_headers_checked":declared_count,
        "copc_info_vlr_verified":bool(copc_info),
        "copc_root_hierarchy_metadata":copc_info,
        "copc_hierarchy_page_entries_read":False,
        "actual_point_cloud_class_values_read":False,
        "source_horizontal_or_vertical_epsg_verified":False,
    }


def inspect_copc_root_hierarchy(page:bytes, *, source_member_bytes:int,
                                root_offset:int) -> dict:
    """Bounded hierarchy-entry metadata; NO class, position or point payload read."""
    if (not isinstance(page,bytes) or not 32<=len(page)<=32768
        or len(page)%32 or root_offset<1000 or root_offset+len(page)>source_member_bytes):
        raise LAZHeaderError("COPC root hierarchy byte range invalid")
    counts={}
    chunk_count=0
    child_page_count=0
    empty_count=0
    declared_points=0
    visited=set()
    for i in range(0,len(page),32):
        lvl,x,y,z,off,size,npoints=struct.unpack_from("<iiiiQii",page,i)
        if (not 0<=lvl<=25 or not all(0<=axis<2**lvl for axis in (x,y,z))
            or (lvl,x,y,z) in visited):
            raise LAZHeaderError("Invalid COPC root hierarchy voxel keys")
        visited.add((lvl,x,y,z))
        if npoints==-1:
            if (size<=0 or size%32 or off<1000
                or off+size>source_member_bytes or size>32768):
                raise LAZHeaderError("Invalid COPC referenced nested hierarchy page")
            child_page_count+=1
        elif npoints==0:
            if size!=0:
                raise LAZHeaderError("COPC empty voxel has unexpected source chunk length")
            empty_count+=1
        elif npoints>0:
            if (size<=0 or off<1000 or off+size>source_member_bytes
                or npoints>200000000):
                raise LAZHeaderError("COPC hierarchy compressed point chunk outside source member")
            chunk_count+=1
            declared_points+=npoints
        else:
            raise LAZHeaderError("COPC unsupported negative hierarchy point count")
        counts[lvl]=counts.get(lvl,0)+1
    return {
        "source_root_hierarchy_bytes_read_only":len(page),
        "source_root_hierarchy_entries_validated":len(page)//32,
        "root_hierarchy_entries_by_octree_level":dict(sorted(counts.items())),
        "root_compressed_point_chunks_declared":chunk_count,
        "root_nested_hierarchy_pages_declared":child_page_count,
        "root_empty_octree_nodes":empty_count,
        "root_entries_point_counts_sum_not_full_population":declared_points,
        "root_hierarchy_leaf_xyz_voxel_keys_exported":False,
        "root_compressed_point_chunk_bytes_read":False,
        "per_point_xyz_classification_or_building_identity_exported":False,
    }


def inspect(opener=None):
    opener=opener or build_opener(NoRedirect())
    raw=read_http(opener,_request(OFFICIAL_API+CITY_RESOURCE_ID+"/"),
                  status=200,limit=262144)
    try:
        obj=json.loads(raw)
    except (ValueError,UnicodeError) as exc:
        raise LAZHeaderError("Invalid original publisher source metadata") from exc
    if not isinstance(obj,dict):
        raise LAZHeaderError("Source resource response is not an object")
    data=obj.get("data",obj)
    if not isinstance(data,dict) or data.get("id")!=CITY_RESOURCE_ID or (
        data.get("filesize") or data.get("size")
    )!=CITY_ORIGINAL_BYTES or _source_digest_from_metadata(data).get("sha1") != CITY_PUBLISHER_SHA1:
        raise LAZHeaderError("Publisher original archive identity, size or SHA-1 metadata drift")
    url=_only_publisher_url(data.get("url"),CITY_GROUP)
    try:
        with opener.open(_request(url,method="HEAD"),timeout=25) as rs:
            if rs.getcode()!=200 or rs.info().get("Content-Length")!=str(CITY_ORIGINAL_BYTES):
                raise LAZHeaderError("Original group archive HTTP HEAD changed")
    except (HTTPError,URLError,OSError) as exc:
        raise LAZHeaderError("Original publisher HEAD unavailable") from exc

    tailbegin=CITY_ORIGINAL_BYTES-ZIP_TAIL_BYTES
    tail=read_http(opener,_request(url,start=tailbegin,end=CITY_ORIGINAL_BYTES-1),
        status=206,limit=ZIP_TAIL_BYTES,
        range_expected=(tailbegin,CITY_ORIGINAL_BYTES-1,CITY_ORIGINAL_BYTES))
    eocd=parse_eocd(tail,full_size=CITY_ORIGINAL_BYTES)
    directory=read_http(opener,_request(url,start=eocd["directory_start"],end=eocd["directory_end"]),
        status=206,limit=eocd["directory_bytes"],
        range_expected=(eocd["directory_start"],eocd["directory_end"],CITY_ORIGINAL_BYTES))
    member=city_member(directory,expected_members=eocd["members"])
    base={
        "schema_version":"lu-original-classified-city-LAZ-public-header-range-v0",
        "official_city_tile":CITY_STUDY_TILE,
        "city_archive_bytes":CITY_ORIGINAL_BYTES,
        "published_archive_sha1_not_verified_against_whole_zip":CITY_PUBLISHER_SHA1,
        "zip_tile_member_method":member["method"],
        "zip_tile_member_compressed_bytes":member["compressed"],
        "zip_tile_member_uncompressed_bytes":member["uncompressed"],
        "full_original_zip_or_LAZ_downloaded":False,
        "actual_classified_points_read":False,
        "source_rights_and_scientific_model_admitted":False,
    }
    if member["method"]!=0:
        base["las_header_verified"]=False
        base["access_blocker"]="selected LAZ member ZIP-deflated; bounded LAZ header range unavailable"
        return base
    offset=member["offset"]
    local=read_http(opener,_request(url,start=offset,end=offset+29),
        status=206,limit=30,range_expected=(offset,offset+29,CITY_ORIGINAL_BYTES))
    data_start,extra_bytes=local_file_data_offset(local,member)
    name_extra=read_http(opener,_request(url,start=offset+30,end=offset+29+extra_bytes),
        status=206,limit=extra_bytes,
        range_expected=(offset+30,offset+29+extra_bytes,CITY_ORIGINAL_BYTES))
    if name_extra[:len(member["name_raw"])]!=member["name_raw"]:
        raise LAZHeaderError("Local original LAZ filename mismatches original ZIP directory")
    first=read_http(opener,_request(url,start=data_start,end=data_start+109),
        status=206,limit=110,range_expected=(data_start,data_start+109,CITY_ORIGINAL_BYTES))
    preliminary=las_prefix_info(first,member_size=member["uncompressed"])
    end=data_start+preliminary["header_size"]-1
    if end>=data_start+member["compressed"]:
        raise LAZHeaderError("Original LAS header crosses selected ZIP member payload")
    rem=read_http(opener,_request(url,start=data_start+110,end=end),
        status=206,limit=preliminary["header_size"]-110,
        range_expected=(data_start+110,end,CITY_ORIGINAL_BYTES))
    base["las_header_verified"]=True
    base.update(complete_las_header(first,rem,preliminary))
    public_bytes=preliminary["point_data_offset"]-preliminary["header_size"]
    if not 0<public_bytes<=MAX_PUBLIC_VLR_BYTES:
        raise LAZHeaderError("Original public LAS VLR region exceeds reviewed 32 KiB budget")
    start_vlr=data_start+preliminary["header_size"]
    end_vlr=start_vlr+public_bytes-1
    vlrs=read_http(opener,_request(url,start=start_vlr,end=end_vlr),
        status=206,limit=public_bytes,
        range_expected=(start_vlr,end_vlr,CITY_ORIGINAL_BYTES))
    base.update(inspect_public_vlrs(
        vlrs,declared_count=preliminary["vlr_count"],
        public_point_offset=preliminary["point_data_offset"],
        las_header_size=preliminary["header_size"],
        selected_laz_size=member["uncompressed"]))
    if base["copc_info_vlr_verified"]:
        hier=base["copc_root_hierarchy_metadata"]
        root_start=data_start+hier["copc_root_hierarchy_offset_within_selected_laz"]
        root_end=root_start+hier["copc_root_hierarchy_size_bytes"]-1
        if root_end>=data_start+member["compressed"]:
            raise LAZHeaderError("COPC hierarchy extends beyond source LAZ member")
        page=read_http(opener,_request(url,start=root_start,end=root_end),
            status=206,limit=hier["copc_root_hierarchy_size_bytes"],
            range_expected=(root_start,root_end,CITY_ORIGINAL_BYTES))
        base.update(inspect_copc_root_hierarchy(
            page,source_member_bytes=member["uncompressed"],
            root_offset=hier["copc_root_hierarchy_offset_within_selected_laz"]))
        # Positive evidence flags are set only AFTER a fully parsed original
        # 206 page. Do not preserve obsolete preflight false values here.
        base["copc_vlr_verified"]=True
        base["copc_hierarchy_page_entries_read"]=True
        base["copc_root_hierarchy_metadata"]["root_hierarchy_page_downloaded"]=True
    return base


def main(argv=None):
    import argparse
    p=argparse.ArgumentParser(description=__doc__)
    p.parse_args(argv)
    try:
        report=inspect()
    except (ZipRangeError,ArchiveReceiptError,LAZHeaderError) as exc:
        p.exit(2,"BLOCKED: "+str(exc)+"\n")
    print(json.dumps(report,sort_keys=True,indent=2,allow_nan=False))
    return 0


if __name__=="__main__":
    raise SystemExit(main())
