# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Original 2022 NRW HU ZIP *metadata* via bounded HTTP HEAD and byte ranges.

No full 859MB download, no shapefile/feature rows, no insurer exposure.
ZIP central directory and member identifiers only; no full-source SHA256.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import struct
import sys
from urllib.request import Request,urlopen
from urllib.error import URLError

URL="https://www.opengeodata.nrw.de/produkte/geobasis/lk/hist/hist_hu_shp/2022_hu_EPSG4647_Shape.zip"
MAX_TAIL=65557       # 22-byte EOCD + 65535 max comment
MAX_DIRECTORY=1024*1024
MIN_ZIP_SIZE=800_000_000
MAX_ZIP_SIZE=1_100_000_000
MAX_MEMBERS=10000


class OriginalZipBlocked(ValueError):
    pass


def eocd_from_last_bytes(last:bytes,absolute_start:int,total:int)->dict:
    if not last or len(last)>MAX_TAIL or total<MIN_ZIP_SIZE or total>MAX_ZIP_SIZE:
        raise OriginalZipBlocked("original ZIP length or EOF range invalid")
    found=[]
    for i in range(max(0,len(last)-MAX_TAIL),len(last)-21):
        if last[i:i+4]!=b"PK\x05\x06":continue
        (sig,disk,cd_disk,disk_entries,entries,cdsize,cdoffset,comment)=struct.unpack_from("<IHHHHIIH",last,i)
        if (i+22+comment!=len(last) or sig!=0x06054b50):continue
        found.append((i,disk,cd_disk,disk_entries,entries,cdsize,cdoffset))
    if len(found)!=1:
        raise OriginalZipBlocked("EOCD absent, ambiguous or ZIP comment invalid")
    i,disk,cd_disk,disk_entries,entries,cdsize,cdoffset=found[0]
    if (disk or cd_disk or entries!=disk_entries or not 1<=entries<=MAX_MEMBERS
        or not 1<=cdsize<=MAX_DIRECTORY or cdoffset==0xffffffff
        or absolute_start+i != cdoffset+cdsize):
        raise OriginalZipBlocked("ZIP multipart/ZIP64/central-directory bounds unsupported")
    return {"member_count":entries,"central_offset":cdoffset,"central_size":cdsize,
            "tail_sha256":hashlib.sha256(last).hexdigest(),"eocd_at":absolute_start+i}


def parse_directory(data:bytes,expected_entries:int)->list[dict]:
    if len(data)>MAX_DIRECTORY or not 1<=expected_entries<=MAX_MEMBERS:
        raise OriginalZipBlocked("central directory bytes outside bound")
    records=[]
    i=0
    while i<len(data):
        if len(data)-i<46 or data[i:i+4]!=b"PK\x01\x02":
            raise OriginalZipBlocked("central directory signature/header invalid")
        fields=struct.unpack_from("<IHHHHHHIIIHHHHHII",data,i)
        _,_made,_need,flags,method,_,_,crc,compressed,uncompressed,fnlen,extra,comment,diskstart,_,_,offset=fields
        j=i+46+fnlen+extra+comment
        if j>len(data) or diskstart!=0 or compressed==0xffffffff or offset==0xffffffff:
            raise OriginalZipBlocked("unsupported ZIP64/central directory entry")
        filename_bytes=data[i+46:i+46+fnlen]
        try:
            name=filename_bytes.decode("utf-8" if (flags & 0x800) else "cp437")
        except UnicodeDecodeError as exc:
            raise OriginalZipBlocked("invalid ZIP member name encoding") from exc
        safe_path = name[:-1] if name.endswith("/") else name
        if (not safe_path or name.startswith("/") or "\\" in name
            or any(part in (".","..","") for part in safe_path.split("/"))
            or len(name)>255):
            raise OriginalZipBlocked("dangerous member filename")
        records.append({"name":name,"local_header_offset":offset,"compressed_bytes":compressed,
                        "uncompressed_bytes":uncompressed,"method":method,
                        "crc32_hex":f"{crc:08x}"})
        i=j
    if len(records)!=expected_entries or len(set(x['name'] for x in records))!=len(records):
        raise OriginalZipBlocked("central directory entry count/identity drift")
    suffixes={x['name'].lower().rsplit(".",1)[-1] for x in records if "." in x['name']}
    required={"shp","shx","dbf","prj"}
    if not required.issubset(suffixes):
        raise OriginalZipBlocked("official shape member family not established")
    if sum(x["uncompressed_bytes"] for x in records)>20_000_000_000:
        raise OriginalZipBlocked("uncompressed size out of bounds")
    return records


def _head():
    request=Request(URL,headers={"User-Agent":"OpenCatastrophe-source-readonly-preflight/0.1"},method="HEAD")
    with urlopen(request,timeout=30) as response:
        if response.status!=200 or response.geturl()!=URL:
            raise OriginalZipBlocked("publisher HEAD URL/status changed")
        length=response.headers.get("Content-Length","")
        if not length.isdecimal():
            raise OriginalZipBlocked("publisher HEAD exact length missing")
        n=int(length)
        if not MIN_ZIP_SIZE<=n<=MAX_ZIP_SIZE:
            raise OriginalZipBlocked("publisher ZIP size outside anticipated bound")
        return n


def _range(start:int,end:int,total:int)->bytes:
    if start<0 or end<start or end>=total or end-start+1>MAX_DIRECTORY:
        raise OriginalZipBlocked("requested byte range outside bound")
    header={"User-Agent":"OpenCatastrophe-source-readonly-preflight/0.1",
            "Range":f"bytes={start}-{end}"}
    request=Request(URL,headers=header,method="GET")
    with urlopen(request,timeout=30) as response:
        if response.status!=206 or response.geturl()!=URL:
            raise OriginalZipBlocked("server did not enforce partial-content response")
        cr=response.headers.get("Content-Range","")
        if cr!=f"bytes {start}-{end}/{total}":
            raise OriginalZipBlocked("partial-content byte range changed")
        if response.headers.get("Content-Length") not in (None,str(end-start+1)):
            raise OriginalZipBlocked("partial range wrong length")
        data=response.read(end-start+2)
    if len(data)!=end-start+1:
        raise OriginalZipBlocked("partial range truncated or excessive")
    return data


def probe():
    total=_head()
    tail_start=max(0,total-MAX_TAIL)
    tail=_range(tail_start,total-1,total)
    eocd=eocd_from_last_bytes(tail,tail_start,total)
    cdstart=eocd["central_offset"]
    directory=_range(cdstart,cdstart+eocd["central_size"]-1,total)
    members=parse_directory(directory,eocd["member_count"])
    return {
        "schema":"NRW_HU_2022_OFFICIAL_ZIP_RANGE_METADATA_V0",
        "official_url":URL,
        "original_publisher_zip_byte_count_from_head":total,
        "archive_eocd_and_central_directory_validated":True,
        "archive_member_names_and_sizes_from_original_ranges":members,
        "archive_member_count":len(members),
        "observed_central_directory_sha256":hashlib.sha256(directory).hexdigest(),
        "observed_eocd_tail_sha256":eocd["tail_sha256"],
        "original_zip_sha256_verified":False,
        "original_zip_fully_downloaded":False,
        "original_zip_feature_rows_read":False,
        "source_crs_from_index":"EPSG:4647",
        "source_crs_from_original_prj_independently_verified":False,
        "real_rva_policy_geography_observed":False,
        "OED_individual_geocodes_created":False,
        "model_input_approved":False,
        "HTTP_request_count":3,
        "HTTP_content_byte_request_upper_bound":MAX_TAIL+MAX_DIRECTORY,
    }


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--live",action="store_true",help="opt-in 3 strict bounded official requests; no ZIP payload")
    args=ap.parse_args()
    if not args.live:
        ap.exit(2,"BLOCKED: --live must be explicitly selected\n")
    print(json.dumps(probe(),ensure_ascii=False,sort_keys=True,indent=2))
    return 0

if __name__=="__main__":
    try:sys.exit(main())
    except (OSError,OriginalZipBlocked,struct.error) as exc:
        print("NRW_HU_2022_ORIGINAL_RANGE_BLOCKED: "+str(exc),file=sys.stderr)
        sys.exit(2)
