# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Fixed official Microsoft Louisiana building-footprint archive metadata proof.

Only HEAD plus bounded end-of-ZIP and central-directory Range reads, no
GeoJSON data, no 2M buildings, no insurer location/TIV, no stored source bytes.
Observed ETag/size do not certify whole-file SHA, licence, or source vintage.
"""
from __future__ import annotations

import argparse
import json
import re
import struct
import sys
from urllib.request import (
    Request, build_opener, HTTPSHandler, ProxyHandler, HTTPRedirectHandler,
)

URL = "https://minedbuildings.z5.web.core.windows.net/legacy/usbuildings-v2/Louisiana.geojson.zip"
EXPECTED_MEMBER = "Louisiana.geojson"
MAX_ORIGINAL_BYTES = 350_000_000
MAX_TAIL_BYTES = 66_000
MAX_CENTRAL_BYTES = 4096
MIN_UNCOMPRESSED_BYTES = 100_000_000
MAX_UNCOMPRESSED_BYTES = 1_500_000_000
SCHEMA = "opencatastrophe-ms-louisiana-original-zip-metadata-v0"


class OriginalArchiveError(ValueError):
    pass


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def original_fetch(request, limit):
    opener = build_opener(ProxyHandler({}), HTTPSHandler(), NoRedirect())
    with opener.open(request, timeout=20) as response:
        headers = {k.lower(): v for k,v in response.headers.items()}
        # For HEAD, Content-Length is the remote object size, not the
        # number of response-body bytes. Never reject it against the zero-byte
        # HEAD response budget; it is later checked against MAX_ORIGINAL_BYTES.
        if request.get_method() == "HEAD":
            body = response.read(1)
            if body:
                raise OriginalArchiveError("HEAD unexpectedly returned source bytes")
            return response.status, headers, b""
        if headers.get("content-length") and int(headers["content-length"]) > limit:
            raise OriginalArchiveError("range response exceeds declared byte limit")
        body = response.read(limit + 1)
        if len(body) > limit:
            raise OriginalArchiveError("response exceeds stream limit")
        return response.status,headers,body


def _request(*, method="GET", start=None, end=None, etag=None):
    hdr = {"Accept-Encoding":"identity",
           "User-Agent":"OpenCatastrophe-readonly-Microsoft-building-research/0"}
    if start is not None:
        hdr["Range"] = f"bytes={start}-{end}"
    if etag:
        hdr["If-Match"] = etag
    return Request(URL, headers=hdr, method=method)


def probe(fetch=original_fetch):
    status, meta, body = fetch(_request(method="HEAD"), 0)
    if status != 200 or body:
        raise OriginalArchiveError("source HEAD unavailable")
    size_raw = meta.get("content-length", "")
    if not re.fullmatch(r"[1-9][0-9]*", size_raw):
        raise OriginalArchiveError("missing immutable-sized source archive")
    n = int(size_raw)
    if not 22 < n <= MAX_ORIGINAL_BYTES:
        raise OriginalArchiveError("unexpected source ZIP archive size")
    tag = meta.get("etag", "")
    if (not 1 <= len(tag) <= 150 or not tag.startswith('"')
            or not tag.endswith('"')):
        raise OriginalArchiveError("original archive ETag not documented")
    if meta.get("accept-ranges", "").lower() not in ("bytes", ""):
        raise OriginalArchiveError("source does not advertise byte range support")

    def get(start, end):
        length=end-start+1
        if not (0 <= start <= end < n and length <= MAX_TAIL_BYTES):
            raise OriginalArchiveError("bounded source range refused")
        res, hdr, bytes_ = fetch(
            _request(start=start,end=end,etag=tag), length)
        if (res != 206 or hdr.get("content-length") != str(length)
                or hdr.get("content-range") != f"bytes {start}-{end}/{n}"
                or len(bytes_) != length
                or hdr.get("etag") not in (tag,None)):
            raise OriginalArchiveError("range/ETag differs from original HEAD")
        return bytes_

    tail = get(max(0,n-MAX_TAIL_BYTES),n-1)
    # Fixed no-ZIP64 single-disk central directory, no source rows needed.
    pos = tail.rfind(b"PK\x05\x06")
    if pos < 0 or pos+22 > len(tail):
        raise OriginalArchiveError("ZIP end record unavailable")
    sig,disk,central_disk,on_disk,total,cd_len,cd_start,comment = struct.unpack_from(
        "<IHHHHIIH",tail,pos)
    if (sig != 0x06054b50 or disk or central_disk or total != 1
            or on_disk != total or comment != len(tail)-(pos+22)
            or not 46 <= cd_len <= MAX_CENTRAL_BYTES
            or cd_start+cd_len != n-(len(tail)-pos)):
        raise OriginalArchiveError("not an exact one-member ZIP32 archive")
    central = get(cd_start,cd_start+cd_len-1)
    if len(central)<46 or central[:4] != b"PK\x01\x02":
        raise OriginalArchiveError("central directory missing")
    (
        sig,made,needed,flags,method,mtime,mdate,crc,compressed,unpacked,
        name_len,extra_len,comment_len,part_num,int_attr,ext_attr,local_offset,
    ) = struct.unpack_from("<IHHHHHHIIIHHHHHII", central,0)
    if (sig != 0x02014b50 or flags & 1 or method not in (0,8)
            or not MIN_UNCOMPRESSED_BYTES <= unpacked <= MAX_UNCOMPRESSED_BYTES
            or not 1 <= compressed <= n
            or name_len == 0 or 46+name_len+extra_len+comment_len != len(central)
            or local_offset >= cd_start):
        raise OriginalArchiveError("unexpected or unsafe ZIP member")
    if central[46:46+name_len].decode("utf-8") != EXPECTED_MEMBER:
        raise OriginalArchiveError("original archive member/extension mismatch")
    return {
        "schema":SCHEMA,
        "provider":"Microsoft US Building Footprints",
        "official_source_url":URL,
        "http_archive_size_bytes":n,
        "original_etag_metadata_only_not_sha256":tag,
        "central_directory_size_bytes":cd_len,
        "source_member_name":EXPECTED_MEMBER,
        "source_member_uncompressed_bytes":unpacked,
        "source_member_compressed_bytes":compressed,
        "source_zip_entries":total,
        "source_byte_ranges_only":True,
        "full_archive_sha256_verified":False,
        "geojson_original_records_read":False,
        "reported_2173567_buildings_verified":False,
        "source_per_building_imagery_vintage_verified":False,
        "source_ODbL_reuse_rights_approved":False,
        "georeferenced_parish_crosswalk_executed":False,
        "insurance_TIV_or_policies_verified":False,
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
        result=probe()
    except (OriginalArchiveError,OSError,UnicodeError,struct.error) as exc:
        print("BLOCKED:",exc,file=sys.stderr)
        return 2
    print(json.dumps(result,indent=2,sort_keys=True))
    return 0


if __name__=="__main__":
    raise SystemExit(main())
