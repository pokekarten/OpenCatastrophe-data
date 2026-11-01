#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Bounded original city COPC ZIP central-directory proof via HTTP206 Range only.

Only a fixed, independently observed official 2024 city grouped ZIP source.
Request at most 65,557 bytes from the very end, then <=256KiB of ZIP central
directory. Never GET a whole 1.70GB archive, original LAZ or point bytes.
No raw ZIP bytes, internal file paths, point positions or individual building
identifiers are logged or persisted. Requires exact pinned portal metadata.
"""
from __future__ import annotations

import argparse
import json
import re
import struct
from urllib.request import Request, build_opener
from urllib.error import HTTPError, URLError

from research_runners.luxembourg_lidar2024_copc_group_resource_head_v0 import (
    OFFICIAL_API, RESOURCES, NoRedirect, _only_publisher_url,
    _source_digest_from_metadata, ArchiveReceiptError,
)

CITY_RESOURCE_ID,CITY_GROUP=RESOURCES["luxembourg-city"]
CITY_ORIGINAL_BYTES=1700086212
CITY_PUBLISHER_SHA1="f8650c5eee38d941921199a0c6e1f64b985c9b34"
CITY_STUDY_TILE="77000_75500"
ZIP_TAIL_BYTES=65557
MAX_DIRECTORY_BYTES=262144
MAX_ZIP_MEMBERS=100
RE_HTTPS_RANGE=re.compile(r"bytes (\d+)-(\d+)/(\d+)\Z")


class ZipRangeError(ValueError):
    pass


def read_http(opener,req,*,status:int,limit:int=0,range_expected=None):
    try:
        with opener.open(req,timeout=25) as r:
            code=r.getcode()
            if code!=status:
                # CRITICAL: reject HTTP200 for range requests without reading
                # any of the 1.70GB body, even from a misconfigured source.
                raise ZipRangeError("Original ZIP publisher did not honour exact HTTP status/range")
            headers=r.info()
            if range_expected is not None:
                range_header=headers.get("Content-Range","")
                m=RE_HTTPS_RANGE.fullmatch(range_header.strip())
                if not m or tuple(map(int,m.groups()))!=range_expected:
                    raise ZipRangeError("Original ZIP HTTP Content-Range differs from requested bound")
                length=headers.get("Content-Length")
                if length is not None and (not str(length).isdigit() or int(length)!=range_expected[1]-range_expected[0]+1):
                    raise ZipRangeError("Original ZIP HTTP range Content-Length mismatch")
            if limit:
                fragment=r.read(limit+1)
                if len(fragment)>limit or (range_expected is not None and len(fragment)!=limit):
                    raise ZipRangeError("Original metadata/range response oversized or byte-range truncated")
                return fragment
            return None
    except (HTTPError,URLError,OSError,ValueError) as exc:
        if isinstance(exc,ZipRangeError):
            raise
        raise ZipRangeError("Official range resource cannot be safely read") from exc


def parse_eocd(tail:bytes,*,full_size:int) -> dict:
    if not isinstance(tail,bytes) or not ZIP_TAIL_BYTES<=len(tail)<=ZIP_TAIL_BYTES:
        raise ZipRangeError("Original ZIP EOCD tail range must be exactly 65,557 bytes")
    if not 1024*1024<=full_size<=4*1024**3:
        raise ZipRangeError("Original official ZIP total outside conservative budget")
    signature=b"PK\x05\x06"
    pos=tail.rfind(signature)
    if pos<0 or pos+22>len(tail):
        raise ZipRangeError("ZIP end-of-central-directory header not present in bounded tail")
    sig,disk,cd_disk,entries_disk,entries_total,cd_size,cd_offset,comment_len=struct.unpack_from("<IHHHHIIH",tail,pos)
    if pos+22+comment_len!=len(tail):
        raise ZipRangeError("Untrusted trailing ZIP bytes or central directory comment length")
    if (disk!=0 or cd_disk!=0 or entries_disk!=entries_total or not 1<=entries_total<=MAX_ZIP_MEMBERS
            or not 1<=cd_size<=MAX_DIRECTORY_BYTES
            or cd_offset<=0 or cd_offset+cd_size>full_size-ZIP_TAIL_BYTES+pos):
        raise ZipRangeError("Source multi-disk, ZIP64, oversized or structurally invalid central directory")
    if entries_total==65535 or cd_size==0xFFFFFFFF or cd_offset==0xFFFFFFFF:
        raise ZipRangeError("ZIP64 central-directory variant requires separately reviewed parser")
    return {
        "members":entries_total,
        "directory_bytes":cd_size,
        "directory_start":cd_offset,
        "directory_end":cd_offset+cd_size-1,
        "zip_comment_bytes":comment_len,
    }


def parse_directory(directory:bytes, *, count:int) -> dict:
    if not isinstance(directory,bytes) or not 1<=len(directory)<=MAX_DIRECTORY_BYTES:
        raise ZipRangeError("ZIP central directory exceeds metadata-only budget")
    if not 1<=count<=MAX_ZIP_MEMBERS:
        raise ZipRangeError("ZIP source member count outside reviewed cap")
    pos=0
    n_laz=0
    n_las=0
    n_copc=0
    study_tile_hits=0
    seen=set()
    total_archive_payload=0
    for _ in range(count):
        if pos+46>len(directory):
            raise ZipRangeError("Truncated ZIP central directory file header")
        parts=struct.unpack_from("<IHHHHHHIIIHHHHHII",directory,pos)
        if parts[0]!=0x02014B50:
            raise ZipRangeError("Expected ZIP central-directory file header signature")
        flag=parts[3];method=parts[4]
        comp_size,uncomp_size=parts[8],parts[9]
        name_len,extra_len,comment_len=parts[10],parts[11],parts[12]
        disk_start,local_offset=parts[13],parts[16]
        stop=pos+46+name_len+extra_len+comment_len
        if (stop>len(directory) or name_len<1 or name_len>240 or flag&1
                or method not in (0,8) or disk_start!=0
                or comp_size==0xFFFFFFFF or uncomp_size==0xFFFFFFFF
                or local_offset==0xFFFFFFFF):
            raise ZipRangeError("ZIP central directory uses unsafe/encrypted/ZIP64 member variant")
        raw=directory[pos+46:pos+46+name_len]
        try:
            name=raw.decode("utf-8" if flag&(1<<11) else "cp437")
        except UnicodeError as exc:
            raise ZipRangeError("Unparseable original ZIP member path") from exc
        if (name.startswith("/") or "\\" in name or "\x00" in name or
            ":" in name or any(x in ("","..",".") for x in name.rstrip("/").split("/"))
            or name in seen):
            raise ZipRangeError("Unsafe or repeated original ZIP member")
        seen.add(name)
        lower=name.lower()
        if lower.endswith(".copc.laz"):n_copc+=1
        if lower.endswith(".laz"):n_laz+=1
        if lower.endswith(".las"):n_las+=1
        if CITY_STUDY_TILE in name:study_tile_hits+=1
        total_archive_payload+=comp_size
        pos=stop
    if pos!=len(directory):
        raise ZipRangeError("Unexpected unparsed ZIP central-directory data")
    return {
        "declared_original_zip_member_count":count,
        "declared_laz_members":n_laz,
        "declared_copc_laz_named_members":n_copc,
        "declared_las_members":n_las,
        "city_study_tile_filename_reference_present":study_tile_hits>0,
        "city_study_tile_named_member_count":study_tile_hits,
        "sum_reported_compressed_member_bytes":total_archive_payload,
    }


def _request(url,*,method="GET",start=None,end=None):
    headers={"Accept-Encoding":"identity","User-Agent":"OpenCatastrophe-LU-COPC-range-research/0"}
    if start is not None:
        headers["Range"]=f"bytes={start}-{end}"
    return Request(url,method=method,headers=headers)


def inspect(opener=None):
    if opener is None:
        opener=build_opener(NoRedirect())
    raw=read_http(opener,_request(OFFICIAL_API+CITY_RESOURCE_ID+"/"),
                  status=200,limit=262144)  # metadata body strictly capped
    try:
        data=json.loads(raw)
    except (ValueError,UnicodeError) as exc:
        raise ZipRangeError("Official source resource JSON unreadable") from exc
    if not isinstance(data,dict):
        raise ZipRangeError("Official source metadata not an object")
    if isinstance(data.get("data"),dict):
        data=data["data"]
    if data.get("id")!=CITY_RESOURCE_ID or data.get("size")!=CITY_ORIGINAL_BYTES:
        raise ZipRangeError("Official city resource UUID / archive size differs from frozen receipt")
    published=_source_digest_from_metadata(data)
    if published.get("sha1")!=CITY_PUBLISHER_SHA1:
        raise ZipRangeError("Publisher-provided original city archive SHA1 metadata changed")
    try:
        url=_only_publisher_url(data.get("url"),CITY_GROUP)
    except ArchiveReceiptError as exc:
        raise ZipRangeError("Publisher returned unreviewed direct grouped ZIP URL") from exc
    # HEAD metadata must continue to agree with the previously independently
    # checked exact-source 1,700,086,212 byte receipt.
    try:
        with opener.open(_request(url,method="HEAD"),timeout=25) as rsp:
            if rsp.getcode()!=200 or rsp.info().get("Content-Length")!=str(CITY_ORIGINAL_BYTES):
                raise ZipRangeError("Official city ZIP HEAD differs from original verified byte count")
    except (HTTPError,URLError,OSError) as exc:
        raise ZipRangeError("Original city ZIP HEAD not readable") from exc
    start=CITY_ORIGINAL_BYTES-ZIP_TAIL_BYTES
    end=CITY_ORIGINAL_BYTES-1
    tail=read_http(opener,_request(url,start=start,end=end),status=206,
                   limit=ZIP_TAIL_BYTES,range_expected=(start,end,CITY_ORIGINAL_BYTES))
    eocd=parse_eocd(tail,full_size=CITY_ORIGINAL_BYTES)
    directory=read_http(opener,_request(url,start=eocd["directory_start"],
                                       end=eocd["directory_end"]),status=206,
                        limit=eocd["directory_bytes"],range_expected=(
                            eocd["directory_start"],eocd["directory_end"],CITY_ORIGINAL_BYTES))
    counts=parse_directory(directory,count=eocd["members"])
    return {
        "schema_version":"lu-lidar2024-city-classified-copc-group-zip-cd-range-v0",
        "official_city_zip_resource_id":CITY_RESOURCE_ID,
        "official_group":CITY_GROUP,
        "original_archive_total_bytes":CITY_ORIGINAL_BYTES,
        "original_publisher_sha1_unverified":CITY_PUBLISHER_SHA1,
        "original_archive_sha256_verified":False,
        "zip_tail_range_bytes":ZIP_TAIL_BYTES,
        "zip_directory_range_bytes":eocd["directory_bytes"],
        "original_range_requests_status_206":2,
        **counts,
        "original_zip_archive_downloaded":False,
        "original_copc_laz_member_payload_downloaded":False,
        "actual_class_6_building_or_class_5_vegetation_points_read":False,
        "original_internal_file_names_exported":False,
        "source_rights_and_scientific_admission_approved":False,
        "cat_model_input_admitted":False,
    }


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.parse_args(argv)
    try:
        report=inspect()
    except (ZipRangeError,ArchiveReceiptError) as exc:
        parser.exit(2,"BLOCKED: "+str(exc)+"\n")
    print(json.dumps(report,sort_keys=True,indent=2,ensure_ascii=False,allow_nan=False))
    return 0


if __name__=="__main__":
    raise SystemExit(main())
