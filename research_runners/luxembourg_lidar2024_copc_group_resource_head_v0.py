#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Original ACT LiDAR2024 classified pointcloud group archive access receipts.

Read exactly three *official publisher* individual JSON resource records
and perform HTTPS HEAD only on individually allowlisted same-origin ZIP paths.
No GET/archive bytes, no arbitrary URLs/redirects, no point cloud/locations or
model admission. Archive bytes, hashes and permissions require separate gates.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import urllib.error
from urllib.parse import urlsplit
from urllib.request import Request, build_opener, HTTPRedirectHandler

OFFICIAL_API = (
    "https://data.public.lu/api/1/datasets/"
    "lidar-2024-releve-3d-du-territoire-luxembourgeois/"
    "resources/"
)
# Exact resource UUIDs were identified in the official original tile
# assembly GeoPackage under merged PR #975. These belong to only the two
# predeclared Luxembourg pilot areas, NEVER arbitrary neighbouring tiles.
RESOURCES = {
    "luxembourg-city": (
        "9bc4df35-4c5a-4d79-8a05-a2faadd6dab1",
        "Lidar2024_C020_R013",
    ),
    "berdorf-south": (
        "1e68ff5f-9182-42a4-8222-7496f3b689d7",
        "Lidar2024_C030_R028",
    ),
    "berdorf-north": (
        "ff8e2bac-b1aa-441a-82a6-9af4221a1fab",
        "Lidar2024_C030_R029",
    ),
}
MAX_JSON_BYTES = 262144
MAX_ARCHIVE_SIZE = 4 * 1024**3
MIN_ARCHIVE_SIZE = 1024
MAX_TOTAL_ARCHIVES = 3
HEX = re.compile(r"^[0-9a-fA-F]{32,128}$")


class ArchiveReceiptError(ValueError):
    """Fail closed on publisher metadata drift or unreviewed source access."""


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise ArchiveReceiptError("Publisher redirected; downstream target unreviewed")


def _only_publisher_url(url: str, expected_slug: str) -> str:
    if not isinstance(url,str) or len(url)>2048:
        raise ArchiveReceiptError("Publisher source download URL invalid")
    p=urlsplit(url)
    if (p.scheme!="https" or p.hostname!="download.data.public.lu"
        or p.username is not None or p.password is not None
        or p.port not in (None,443) or p.query or p.fragment):
        raise ArchiveReceiptError("Publisher ZIP source origin not independently allowlisted")
    if not p.path.startswith("/resources/") or not p.path.lower().endswith(".zip"):
        raise ArchiveReceiptError("Source path not a direct publisher ZIP")
    if expected_slug.lower() not in p.path.lower():
        raise ArchiveReceiptError("Source ZIP name mismatches published tile index group")
    return url


def _source_digest_from_metadata(resource: dict) -> dict:
    """Extract explicitly typed publisher digests, never fabricate stronger hash."""
    checks=[]
    def add(kind, value):
        if not isinstance(kind,str) or not isinstance(value,str):
            return
        kind=kind.lower().replace("-","")
        if kind not in ("md5","sha1","sha256"):
            return
        expected_len={"md5":32,"sha1":40,"sha256":64}[kind]
        if len(value)==expected_len and HEX.fullmatch(value):
            checks.append({"kind":kind,"value":value.lower()})
    for name in ("md5","sha1","sha256"):
        add(name,resource.get(name))
    raw=resource.get("checksum")
    if isinstance(raw,dict):
        add(raw.get("type") or raw.get("algorithm"),raw.get("value") or raw.get("hash"))
    elif isinstance(raw,str) and ":" in raw:
        kind,value=raw.split(":",1)
        add(kind,value.strip())
    hashes=resource.get("checksums")
    if isinstance(hashes,dict):
        for kind,value in hashes.items():
            add(kind,value)
    by_kind={q["kind"]:q["value"] for q in checks}
    if len(by_kind)!=len(checks):
        raise ArchiveReceiptError("Publisher reports duplicate or conflicting digest definitions")
    return by_kind


def _open(opener, request, *, max_body=0):
    """Network wrapper injectable for deterministic no-network unit tests."""
    try:
        response=opener.open(request,timeout=20)
    except (urllib.error.URLError,OSError,ValueError) as exc:
        if isinstance(exc,ArchiveReceiptError):
            raise
        raise ArchiveReceiptError("Official metadata or ZIP HEAD not readable") from exc
    try:
        with response:
            status=response.getcode()
            if status!=200:
                raise ArchiveReceiptError("Unexpected publisher HTTP response")
            if max_body:
                body=response.read(max_body+1)
                if len(body)>max_body:
                    raise ArchiveReceiptError("Official resource JSON response exceeds strict body cap")
                return body,response.info()
            return None,response.info()
    except (OSError,ValueError) as exc:
        if isinstance(exc,ArchiveReceiptError):
            raise
        raise ArchiveReceiptError("Publisher response malformed") from exc


def _resource_entry(name: str, resource_id: str, slug: str, opener) -> dict:
    url=OFFICIAL_API+resource_id+"/"
    request=Request(url,headers={"Accept":"application/json",
                                "Accept-Encoding":"identity",
                                "User-Agent":"OpenCatastrophe-source-receipt/1"},method="GET")
    raw,meta=_open(opener,request,max_body=MAX_JSON_BYTES)
    try:
        data=json.loads(raw)
    except (ValueError,UnicodeError) as exc:
        raise ArchiveReceiptError("Publisher metadata not valid JSON") from exc
    if not isinstance(data,dict):
        raise ArchiveReceiptError("Original publisher resource record must be a JSON object")
    if "data" in data and isinstance(data["data"],dict):
        data=data["data"]
    if data.get("id")!=resource_id:
        raise ArchiveReceiptError("Source resource UUID does not match exact tile index")
    original_url=_only_publisher_url(data.get("url"),slug)
    supplied_size=data.get("filesize") or data.get("size")
    if supplied_size is not None:
        if not isinstance(supplied_size,int) or isinstance(supplied_size,bool):
            raise ArchiveReceiptError("Publisher archive byte count not integer")
        if not MIN_ARCHIVE_SIZE<=supplied_size<=MAX_ARCHIVE_SIZE:
            raise ArchiveReceiptError("Official source metadata archive size outside bounded budget")
    head=Request(original_url,headers={"Accept-Encoding":"identity",
                                      "User-Agent":"OpenCatastrophe-source-receipt/1"},method="HEAD")
    _,head_headers=_open(opener,head)
    size_header=head_headers.get("Content-Length")
    if not isinstance(size_header,str) or not re.fullmatch(r"[0-9]+",size_header):
        raise ArchiveReceiptError("Official archive HEAD missing unambiguous Content-Length")
    actual_size=int(size_header)
    if not MIN_ARCHIVE_SIZE<=actual_size<=MAX_ARCHIVE_SIZE:
        raise ArchiveReceiptError("Original official ZIP too large/invalid for next source phase")
    if supplied_size is not None and supplied_size!=actual_size:
        raise ArchiveReceiptError("Official resource metadata and original ZIP HEAD size disagree")
    return {
        "source_area":name,
        "official_resource_id":resource_id,
        "official_tile_archive_name":slug,
        "source_url_host":"download.data.public.lu",
        "publisher_record_filename_matches_tile_index":True,
        "publisher_metadata_size_bytes":supplied_size,
        "original_zip_head_http_status":200,
        "original_zip_head_declared_bytes":actual_size,
        "original_zip_bytes_downloaded":0,
        "publisher_reported_checksums_unverified":_source_digest_from_metadata(data),
        "source_full_archive_sha256_verified":False,
        "actual_copc_header_or_point_classes_read":False,
        "actual_roof_vs_vegetation_points_observed":False,
        "model_input_admitted":False,
    }


def inspect(opener=None) -> dict:
    if opener is None:
        opener=build_opener(NoRedirect())
    if len(RESOURCES)!=MAX_TOTAL_ARCHIVES or len({x[0] for x in RESOURCES.values()})!=MAX_TOTAL_ARCHIVES:
        raise ArchiveReceiptError("Unreviewed source resource list")
    rows=[_resource_entry(name,resource_id,slug,opener)
          for name,(resource_id,slug) in RESOURCES.items()]
    return {
        "schema_version":"lu-act-lidar2024-official-classified-copc-three-group-resource-head-v0",
        "source_catalogue":"ACT public 2024 LiDAR classified pointcloud group ZIPs",
        "official_resource_records_queried":len(rows),
        "original_zip_head_requests":len(rows),
        "original_archive_bytes_acquired":0,
        "total_source_group_bytes_head_declared":sum(x["original_zip_head_declared_bytes"] for x in rows),
        "resources":rows,
        "publisher_metadata_hashes_are_not_verified_digests":True,
        "classified_point_support_proven":False,
        "independent_building_truth_proven":False,
        "rights_and_scientific_admission_approved":False,
        "model_input_admitted":False,
    }


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.parse_args(argv)
    try:
        print(json.dumps(inspect(),sort_keys=True,indent=2,ensure_ascii=False,allow_nan=False))
    except ArchiveReceiptError as exc:
        parser.exit(2,"BLOCKED: "+str(exc)+"\n")
    return 0


if __name__=="__main__":
    raise SystemExit(main())
