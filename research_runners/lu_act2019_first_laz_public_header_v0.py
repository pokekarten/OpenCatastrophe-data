#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""ACT LiDAR 2019: bounded first LAZ member LASF header in three reviewed ZIPs.

Reuse canonical original index, 3 original ZIP central-directory SHA receipts
and source sizes; request only tiny HTTP206 byte ranges. The LAZ member itself
is ZIP/Deflate compressed, so at most 16 KiB of its compressed *beginning*
are fetched and at most 111 decompressed bytes (public LAS header) are read.
No LiDAR point data, member names, coordinates, VLRs, ZIP/LAZ files or whole
archive hashes are emitted.
"""
from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path
import struct
from urllib.request import build_opener
import zlib

from research_runners.lu_act2019_original_lidar_tile_index_v0 import (
    _unique_pairs, _reject_constant, verify_original, OriginalIndexError,
)
from research_runners.lu_act2019_three_tile_http_preflight_v0 import (
    RejectRedirects, build_site_windows, select_site_urls, TileProbeError,
)
from research_runners.lu_act2019_three_zip_directory_range_v0 import (
    DirectoryError, MAX_TAIL, ORIGINAL_SIZE_BY_SITE, OBSERVED_DIRECTORY_SHA256_BY_SITE,
    OBSERVED_LAZ_MEMBER_COUNT_PER_ZIP, CENTRAL_STRUCT, safe_range,
    locate_eocd, summarize_central, inspect_one_zip, freeze_original_directory_receipts,
)

MAX_LAZ_ZIP_PREFIX_COMPRESSED_BYTES = 16_384
PUBLIC_LAS_HEADER_PREFIX_BYTES = 111
LOCAL_HEADER_BYTES = 30
MAX_LOCAL_NAME_AND_EXTRA_BYTES = 4_096
LOCAL_STRUCT = struct.Struct("<IHHHHHIIIHH")
PUBLIC_LAS_HEADER_VERSIONS = {2: 227, 3: 235, 4: 375}
# Minimum standard point record lengths; LAS extra-byte records may be longer.
MIN_POINT_RECORD_LENGTHS = {0:20, 1:28, 2:26, 3:34, 4:57,
                            5:63, 6:30, 7:36, 8:38, 9:59, 10:67}
MAX_POINT_FORMAT_BY_LAS_MINOR = {2:3, 3:5, 4:10}


class PublicHeaderError(ValueError):
    """Only self-authored non-sensitive error labels are ever printed."""


def first_central_laz_member(directory: bytes, *, original_cd_offset: int) -> dict:
    """Select deterministic first reviewed .laz member WITHOUT emitting its name."""
    if not isinstance(directory, bytes) or len(directory)<CENTRAL_STRUCT.size:
        raise PublicHeaderError("Original ZIP directory missing for public header")
    h=CENTRAL_STRUCT.unpack_from(directory)
    (signature, made, needed, flags, method, mtime, mdate,
     crc, compressed, uncompressed, name_len, extra_len, comment_len,
     disk, internal, external, local_offset)=h
    end=CENTRAL_STRUCT.size+name_len+extra_len+comment_len
    if (signature!=b"PK\x01\x02" or disk!=0 or flags&1
            or method!=8 or compressed<=0 or uncompressed<PUBLIC_LAS_HEADER_PREFIX_BYTES
            or local_offset>=original_cd_offset or local_offset<0
            or not 1<=name_len<=1024 or end>len(directory)):
        raise PublicHeaderError("Reviewed first ZIP member is not valid deflated LAZ metadata")
    filename=directory[CENTRAL_STRUCT.size:CENTRAL_STRUCT.size+name_len]
    if not filename.lower().endswith(b".laz") or b".." in filename.split(b"/"):
        raise PublicHeaderError("First ZIP member not reviewed LAZ extension/path")
    return {
        "original_local_header_offset":local_offset,
        "name_for_internal_equality_only":filename,
        "declared_compressed_bytes":compressed,
        "declared_uncompressed_bytes":uncompressed,
        "central_flags":flags,
        "compression_method":method,
    }


def zip_deflated_member_first_public_bytes(url: str, *,
        archive_size: int, cd_offset: int, first: dict, opener) -> tuple[bytes,dict]:
    """Read 30-byte local header, private name, <=16KiB deflate, emit <=111 bytes."""
    offset=first["original_local_header_offset"]
    fixed=safe_range(url,start=offset,length=LOCAL_HEADER_BYTES,total=archive_size,opener=opener)
    h=LOCAL_STRUCT.unpack(fixed)
    signature,needed,flags,method,mtime,mdate,crc,compressed,uncompressed,name_len,extra_len=h
    if (signature!=0x04034B50 or method!=8 or flags!=first["central_flags"]
            or not 1<=name_len<=1024 or name_len+extra_len>MAX_LOCAL_NAME_AND_EXTRA_BYTES):
        raise PublicHeaderError("Original ZIP local header differs from central directory")
    variable=safe_range(url,start=offset+LOCAL_HEADER_BYTES,
                        length=name_len+extra_len,total=archive_size,opener=opener)
    if variable[:name_len]!=first["name_for_internal_equality_only"]:
        raise PublicHeaderError("Original local ZIP name differs from verified central name")
    body_start=offset+LOCAL_HEADER_BYTES+name_len+extra_len
    if (body_start+first["declared_compressed_bytes"]>cd_offset
            or first["declared_compressed_bytes"]<2):
        raise PublicHeaderError("Original compressed member offset/size outside archive")
    budget=min(MAX_LAZ_ZIP_PREFIX_COMPRESSED_BYTES,first["declared_compressed_bytes"])
    prefix=safe_range(url,start=body_start,length=budget,total=archive_size,opener=opener)
    try:
        inflater=zlib.decompressobj(wbits=-15)
        public=inflater.decompress(prefix,max_length=PUBLIC_LAS_HEADER_PREFIX_BYTES)
    except zlib.error as exc:
        raise PublicHeaderError("Original member DEFLATE prefix is not decodable") from exc
    if len(public)!=PUBLIC_LAS_HEADER_PREFIX_BYTES:
        raise PublicHeaderError("Insufficient original LAS public header prefix")
    return public,{
        "zip_member_compression_method":method,
        "zip_local_metadata_name_cross_checked":True,
        "compressed_member_prefix_bytes_fetched":budget,
        "max_public_uncompressed_las_header_bytes":len(public),
        "member_full_deflate_stream_integrity_verified":False,
        "archive_or_laz_sha256_verified":False,
    }


def classify_public_las_prefix(prefix:bytes, *, member_uncompressed_bytes:int) -> dict:
    """Only LAS 1.2–1.4 public header fields; no GPS/position/point records."""
    if (not isinstance(prefix,bytes) or len(prefix)!=PUBLIC_LAS_HEADER_PREFIX_BYTES
            or prefix[:4]!=b"LASF"):
        raise PublicHeaderError("Original first LAS member missing LASF public signature")
    major,minor=prefix[24],prefix[25]
    header_bytes=struct.unpack_from("<H",prefix,94)[0]
    point_offset=struct.unpack_from("<I",prefix,96)[0]
    vlr_count=struct.unpack_from("<I",prefix,100)[0]
    raw_format=prefix[104]
    record_bytes=struct.unpack_from("<H",prefix,105)[0]
    legacy_declared_points=struct.unpack_from("<I",prefix,107)[0]
    point_format=raw_format&0x3F
    if (major!=1 or minor not in PUBLIC_LAS_HEADER_VERSIONS
            or header_bytes!=PUBLIC_LAS_HEADER_VERSIONS[minor]
            or not header_bytes<=point_offset<member_uncompressed_bytes
            or not 0<=vlr_count<=512
            or raw_format&0x40
            or point_format>MAX_POINT_FORMAT_BY_LAS_MINOR.get(minor,-1)
            or not MIN_POINT_RECORD_LENGTHS.get(point_format,1025)<=record_bytes<=1024):
        raise PublicHeaderError("Original LAS version, point-format or header offsets invalid")
    return {
        "original_decompressed_member_begins_LASF":True,
        # Hash of ONLY 111 public prefix bytes; never the full member ZIP/LAZ digest.
        "las_public_first111_sha256_not_member_sha256":sha256(prefix).hexdigest(),
        "las_major":major,"las_minor":minor,
        "las_header_bytes_declared":header_bytes,
        "las_point_data_offset_declared":point_offset,
        "las_vlr_count_declared":vlr_count,
        "las_point_format_code_declared":point_format,
        "laszip_compressed_header_flag_declared":bool(raw_format&0x80),
        "las_point_record_bytes_declared":record_bytes,
        "las_legacy_point_count_field_unverified":legacy_declared_points,
        "point_records_or_las_vlrs_read":False,
        "actual_building_class6_points_verified":False,
        "geodetic_crs_or_vdatum_verified":False,
        "source_epoch_independent_of_vdl3d_verified":False,
    }


def inspect_first_member(url, *, original_archive_bytes:int, directory_sha256:str, opener) -> dict:
    """Strict original ZIP receipt then one bounded first-member header challenge."""
    orig=inspect_one_zip(url,expected_size=original_archive_bytes,opener=opener)
    if (orig["central_directory_sha256_partial_metadata_only"]!=directory_sha256
            or orig["member_extension_counts"]["laz"]!=OBSERVED_LAZ_MEMBER_COUNT_PER_ZIP):
        raise PublicHeaderError("Original pinned ZIP central directory differs")
    start=max(0,original_archive_bytes-MAX_TAIL)
    tail=safe_range(url,start=start,length=original_archive_bytes-start,
                    total=original_archive_bytes,opener=opener)
    eocd=locate_eocd(tail,tail_start=start,total=original_archive_bytes)
    offset=eocd["offset"]; length=eocd["size"]
    if offset>=start:
        directory=tail[offset-start:offset-start+length]
    else:
        directory=safe_range(url,start=offset,length=length,
                             total=original_archive_bytes,opener=opener)
    # Recheck actual directory structure; hash pin checked above from same ZIP
    # response and must also match these re-read bytes.
    from hashlib import sha256
    if sha256(directory).hexdigest()!=directory_sha256:
        raise PublicHeaderError("Original selected directory changed during header read")
    verified=summarize_central(directory,entries=eocd["entries"],
                              archive_size=original_archive_bytes,directory_offset=offset)
    if verified["member_extension_counts"]["laz"]!=9 or verified["zip_method_code_counts"]!={"8":9}:
        raise PublicHeaderError("Original directory source taxonomy drifted")
    first=first_central_laz_member(directory,original_cd_offset=offset)
    header,transit=zip_deflated_member_first_public_bytes(
        url,archive_size=original_archive_bytes,cd_offset=offset,first=first,
        opener=opener)
    classified=classify_public_las_prefix(
        header,member_uncompressed_bytes=first["declared_uncompressed_bytes"])
    return {
        "zip_central_directory_sha256_only":directory_sha256,
        "selected_member_order":"first_original_central_directory_entry",
        "declared_first_laz_uncompressed_member_bytes":first["declared_uncompressed_bytes"],
        **transit,**classified,
    }


def run(index:Path, *, opener=None):
    receipt=verify_original(index)
    try:
        data=json.loads(index.read_text(encoding="utf-8"),
                        object_pairs_hook=_unique_pairs,parse_constant=_reject_constant)
    except (ValueError,UnicodeError) as exc:
        raise PublicHeaderError("Original source index cannot be reloaded") from exc
    urls=select_site_urls(data,build_site_windows())
    if opener is None:
        opener=build_opener(RejectRedirects())
    output={}
    for site,sizes in ORIGINAL_SIZE_BY_SITE.items():
        chosen=urls[site]
        digests=OBSERVED_DIRECTORY_SHA256_BY_SITE[site]
        if len(chosen)!=len(sizes) or len(chosen)!=len(digests):
            raise PublicHeaderError("Original source archive selection drifted")
        output[site]=[inspect_first_member(u,original_archive_bytes=size,
                                         directory_sha256=sha,opener=opener)
                      for u,size,sha in zip(chosen,sizes,digests,strict=True)]
    return {
        "profile":"lu-act2019-3-original-zip-first-laz-public-header-v0",
        "original_index_sha256":receipt["original_index_sha256"],
        "three_original_source_zip_directories_pinned":True,
        "sites":output,
        "max_uncompressed_original_las_header_bytes_per_archive":PUBLIC_LAS_HEADER_PREFIX_BYTES,
        "full_source_zip_or_laz_downloaded":False,
        "actual_lidar_point_classes_or_building_geo_checked":False,
        "2019_capture_lineage_independent_of_vdl_verified":False,
        "rights_review_completed":False,
        "cat_insurer_exposure_admitted":False,
        "original_source_urls_and_member_names_logged":False,
    }


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--original-index",required=True,type=Path)
    args=p.parse_args(argv)
    try:
        result=run(args.original_index)
    except (OriginalIndexError,TileProbeError,DirectoryError,
            PublicHeaderError,OSError,ValueError,TypeError,struct.error):
        print("BLOCKED: strict original 2019 LAZ public header and ZIP source gate")
        return 2
    print(json.dumps(result,sort_keys=True,indent=2,allow_nan=False))
    return 0


if __name__=="__main__":
    raise SystemExit(main())
