#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""One read-only 4096-byte Range GET of public official BVV Oberbayern Hausumringe ZIP.

No full archive download, raw source-byte retention, private ALKIS WFS,
rights promotion, survey-vintage inference, buildings/TIV or CAT admission.
"""
from __future__ import annotations

import argparse
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path
import re
import ssl
import struct
import sys
from urllib.error import HTTPError,URLError
from urllib.request import Request,HTTPRedirectHandler,ProxyHandler,HTTPSHandler,build_opener

URL="https://geodaten.bayern.de/odd/m/3/daten/hausumringe/bezirk/data/091_Oberbayern_Hausumringe.zip"
INDEX="https://geodaten.bayern.de/odd/m/3/daten/hausumringe/bezirk/kml/HU_regierungsbezirk.kml"
RANGE="bytes=0-4095"
LIMIT=4096
FIRST_NAME=b"hausumringe.dbf"
SOURCE="de.bayern.hausumringe"


class PrefixBlocked(ValueError):
    """Exact source, transport, ZIP member or rights scope verification failed."""


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self,req,fp,code,msg,headers,newurl):
        raise PrefixBlocked("original BVV source redirected")


def validate_prefix(raw,*,status,response_url,headers):
    if type(raw) is not bytes or len(raw)!=LIMIT:
        raise PrefixBlocked("expected exactly 4096 original prefix bytes")
    if status!=206 or response_url!=URL:
        raise PrefixBlocked("exact approved URL and HTTP 206 required")
    cr=headers.get("Content-Range","")
    match=re.fullmatch(r"bytes 0-4095/([0-9]{9})",cr)
    if not match or not 100_000_000<=int(match.group(1))<=250_000_000:
        raise PrefixBlocked("unexpected partial range or original archive size")
    media=headers.get("Content-Type","").split(";",1)[0].strip().lower()
    if media not in ("application/zip","application/octet-stream","binary/octet-stream"):
        raise PrefixBlocked("original ZIP media type mismatched")
    if headers.get("Content-Length") is not None and headers["Content-Length"]!=str(LIMIT):
        raise PrefixBlocked("provider Content-Length outside bounded Range")
    if headers.get("Content-Encoding","identity").lower()!="identity":
        raise PrefixBlocked("original provider bytes must not be HTTP-compressed")
    if raw[:4]!=b"PK\x03\x04":
        raise PrefixBlocked("not a ZIP local original header")
    version,flags,method,mtime,mdate,crc,compressed,uncompressed,n,extra=struct.unpack_from("<HHHHHIIIHH",raw,4)
    if version!=20 or flags!=0 or method!=8 or n!=len(FIRST_NAME) or extra!=0:
        raise PrefixBlocked("unsupported original ZIP member header")
    if raw[30:30+n]!=FIRST_NAME or compressed<=0 or uncompressed<=0:
        raise PrefixBlocked("unexpected original ZIP entry identity")
    return {
        "profile":"oc-bvv-hu-by-oberbayern-public-original-4k-prefix-t1-v0",
        "source_id":SOURCE,
        "official_archive_url":URL,
        "official_public_kml_index":INDEX,
        "http_status":status,
        "response_media_type":media,
        "original_request_range":RANGE,
        "original_archive_total_bytes_transport_report_only":int(match.group(1)),
        "original_prefix_bytes":LIMIT,
        "original_prefix_sha256":hashlib.sha256(raw).hexdigest(),
        "first_original_zip_entry":FIRST_NAME.decode("ascii"),
        "first_original_zip_member_is_deflate":True,
        "complete_original_archive_sha256_verified":False,
        "full_original_archive_downloaded":False,
        "original_shapefile_polygons_downloaded":False,
        "original_survey_vintage_verified":False,
        "source_bytes_persisted":False,
        "bulk_licence_or_science_approval_inferred":False,
        "model_input_approved":False,
    }


def probe():
    req=Request(URL,method="GET",headers={
        "Range":RANGE,"Accept-Encoding":"identity","Accept":"application/zip",
        "User-Agent":"OpenCatastrophe-BVV-4KiB-ReadOnly/0.1",
    })
    try:
        with build_opener(
            ProxyHandler({}),NoRedirect(),HTTPSHandler(context=ssl.create_default_context())
        ).open(req,timeout=25) as response:
            if response.status!=206:
                raise PrefixBlocked("provider did not honor exact HTTP byte range")
            raw=response.read(LIMIT+1)
            receipt=validate_prefix(raw,status=response.status,
                response_url=response.geturl(),headers=response.headers)
    except (HTTPError,URLError,TimeoutError,OSError) as exc:
        raise PrefixBlocked("official public regional ZIP range request failed") from exc
    receipt["retrieved_at_utc"]=datetime.now(timezone.utc).isoformat()
    receipt["script_sha256"]=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    return receipt


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--live",action="store_true",help="one fixed original 4096-byte GET")
    args=p.parse_args(argv)
    if not args.live:
        p.error("provider network request is opt-in")
    try:
        print(json.dumps(probe(),sort_keys=True,allow_nan=False))
        return 0
    except PrefixBlocked:
        print("BLOCKED: official BVV original ZIP range or identity unavailable",file=sys.stderr)
        return 2


if __name__=="__main__":
    raise SystemExit(main())
