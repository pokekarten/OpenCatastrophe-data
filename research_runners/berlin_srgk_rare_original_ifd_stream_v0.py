#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""One exact Berlin rare-event ZIP: ephemeral bounded stream, TIFF metadata only.

The TIFF first IFD lies 167112958 bytes into an uncompressed DEFLATE
member; raw HTTP ZIP ranges cannot address its uncompressed offset.
Download exactly ONE reviewed source to a private, auto-deleted CI temp dir,
validate full length and original central SHA, CRC-stream the TIFF into
the void, retain <=256 KiB end metadata. Never export original pixels.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
from hashlib import sha256
import json
import math
import os
from pathlib import Path
import ssl
import struct
import sys
import tempfile
from urllib import error, request
import zipfile

from research_runners import berlin_srgk_depth_zip_central_range_v0 as original

PROFILE = "berlin-srgk-rare-original-full-byte-ephemeral-tiff-metadata-v0"
ZIP_URL = original.SOURCE_BASE + "wasserstand_seltenes_ereignis.zip"
ZIP_BYTES = 132_689_382
ZIP_CENTRAL_SHA256 = "9a593d9d3e39c21ee99c34d13550c16ae9c0d8c3390c653dfb566f49f00be7b3"
TIFF_NAME = "wasserstand_T50_1.tif"
TIFF_BYTES = 167_298_853
TIFF_COMPRESSED = 132_689_170
TIFF_IFD_OFFSET = 167_112_958
TAIL_LIMIT = 262_144
CHUNK = 1024 * 1024
TIMEOUT = 150
TAG_SIZES = {1:1, 2:1, 3:2, 4:4, 5:8, 12:8}


class OriginalTiffBlocked(ValueError):
    """Original-source identity, compact metadata or safety budget not proven."""


class NoRedirect(request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise OriginalTiffBlocked("original provider redirected")


def _open(req: request.Request, timeout: int):
    return request.build_opener(
        request.ProxyHandler({}), NoRedirect(),
        request.HTTPSHandler(context=ssl.create_default_context()),
    ).open(req, timeout=timeout)


def download_ephemeral(path: Path, *, opener=_open) -> str:
    req = request.Request(ZIP_URL, method="GET",
        headers={"Accept":"application/zip","Accept-Encoding":"identity"})
    try:
        with opener(req, TIMEOUT) as r:
            if r.status != 200 or r.geturl() != ZIP_URL:
                raise OriginalTiffBlocked("exact approved original source GET status/url failed")
            if r.headers.get("Content-Encoding","identity").lower() != "identity":
                raise OriginalTiffBlocked("unexpected source transport encoding")
            ct = r.headers.get("Content-Type","").split(";",1)[0].lower().strip()
            if ct not in ("application/zip","application/octet-stream"):
                raise OriginalTiffBlocked("original ZIP server content type drift")
            length = r.headers.get("Content-Length","")
            if length != str(ZIP_BYTES):
                raise OriginalTiffBlocked("publisher ZIP size changed; no unreviewed download")
            flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
            if hasattr(os, "O_NOFOLLOW"):
                flags |= os.O_NOFOLLOW
            fd = os.open(path,flags,0o600)
            digest=sha256()
            size=0
            with os.fdopen(fd,"wb") as output:
                while size < ZIP_BYTES:
                    block=r.read(min(CHUNK,ZIP_BYTES-size))
                    if not block:
                        break
                    size+=len(block)
                    digest.update(block)
                    output.write(block)
                if size != ZIP_BYTES or r.read(1):
                    raise OriginalTiffBlocked("original ZIP stream length not exactly pinned")
    except OriginalTiffBlocked:
        raise
    except (error.URLError,TimeoutError,OSError) as exc:
        raise OriginalTiffBlocked("official source stream unavailable") from exc
    return digest.hexdigest()


def original_directory_check(path: Path) -> dict:
    if not path.is_file() or path.is_symlink() or path.stat().st_size != ZIP_BYTES:
        raise OriginalTiffBlocked("expected original ZIP file not found or wrong size")
    with path.open("rb") as f:
        f.seek(ZIP_BYTES - original.TAIL)
        tail=f.read(original.TAIL)
        cd_offset, cd_size, members=original.locate_eocd(tail,ZIP_BYTES)
        f.seek(cd_offset)
        central=f.read(cd_size)
    if sha256(central).hexdigest() != ZIP_CENTRAL_SHA256:
        raise OriginalTiffBlocked("source original ZIP central directory SHA mismatch")
    rows=original.parse_directory(central,members)
    if (members!=1 or len(rows["bounded_tiff_name_samples"])!=1
        or rows["bounded_tiff_name_samples"][0]!={
            "name":TIFF_NAME,
            "compressed_size_bytes":TIFF_COMPRESSED,
            "uncompressed_size_bytes":TIFF_BYTES,
        }):
        raise OriginalTiffBlocked("source TIFF member identity drift")
    return {"original_source_central_sha256":ZIP_CENTRAL_SHA256,
            "original_source_member_count":members}


def _slice_value(tail: bytes, start: int, source_bytes: int, kind: int,
                 count: int, inline4: bytes, endian: str):
    unit=TAG_SIZES.get(kind)
    if unit is None or not 0 < count <= 4096 or unit*count > 131072:
        return None
    needed=unit*count
    if needed <= 4:
        return inline4[:needed]
    absolute=struct.unpack(endian+"I",inline4)[0]
    local=absolute-start
    if absolute+needed>source_bytes or local<0 or local+needed>len(tail):
        return None
    return tail[local:local+needed]


def extract_tiff_tail_metadata(tail: bytes, header: bytes, source_bytes: int) -> dict:
    if (type(header) is not bytes or len(header)!=8 or
        header[:2] not in (b"II",b"MM") or
        type(tail) is not bytes or not 8<len(tail)<=TAIL_LIMIT or
        source_bytes<len(tail)):
        raise OriginalTiffBlocked("original TIFF header/end-region invalid")
    endian="<" if header[:2]==b"II" else ">"
    if struct.unpack_from(endian+"H",header,2)[0]!=42:
        raise OriginalTiffBlocked("original TIFF format not classic TIFF")
    ifd=struct.unpack_from(endian+"I",header,4)[0]
    if ifd!=TIFF_IFD_OFFSET:
        raise OriginalTiffBlocked("original TIFF first IFD offset drift")
    start=source_bytes-len(tail)
    rel=ifd-start
    if rel<0 or rel+2>len(tail):
        raise OriginalTiffBlocked("expected TIFF first IFD outside bounded end-region")
    entries=struct.unpack_from(endian+"H",tail,rel)[0]
    if not 0<entries<=512 or rel+2+12*entries+4>len(tail):
        raise OriginalTiffBlocked("invalid, truncated or overlarge first IFD")
    tags={}
    for i in range(entries):
        off=rel+2+i*12
        tag,kind,count=struct.unpack_from(endian+"HHI",tail,off)
        if tag in tags:
            raise OriginalTiffBlocked("duplicate source TIFF tag")
        tags[tag]=(kind,count,tail[off+8:off+12])
    dimensions={}
    for code,name in ((256,"raster_width_px"),(257,"raster_height_px")):
        if code not in tags:
            raise OriginalTiffBlocked("missing original TIFF horizontal raster dimension")
        kind,count,inline=tags[code]
        if kind not in (3,4) or count!=1:
            raise OriginalTiffBlocked("unexpected TIFF width/height type")
        value=struct.unpack(endian+("H" if kind==3 else "I"),
             inline[:2] if kind==3 else inline)[0]
        if not 0<value<=200000:
            raise OriginalTiffBlocked("unreasonable original raster dimensions")
        dimensions[name]=value
    geokeys={}
    if 34735 in tags:
        kind,count,inline=tags[34735]
        payload=_slice_value(tail,start,source_bytes,kind,count,inline,endian)
        if payload is not None and kind==3 and count>=4 and len(payload)%2==0:
            words=struct.unpack(endian+"H"*(len(payload)//2),payload)
            if words[0]!=1 or words[3]*4+4>len(words) or words[3]>128:
                raise OriginalTiffBlocked("unreviewed GeoTIFF GeoKey directory")
            for idx in range(words[3]):
                key,location,n,value=words[4+4*idx:8+4*idx]
                if key in (1024,2048,3072,3076,4096,4099) and location==0 and n==1:
                    geokeys[str(key)]=value
    scale=None
    if 33550 in tags:
        kind,count,inline=tags[33550]
        val=_slice_value(tail,start,source_bytes,kind,count,inline,endian)
        if val is not None and kind==12 and count==3:
            v=struct.unpack(endian+"ddd",val)
            if all(math.isfinite(x) and x>0 for x in v[:2]):
                scale=[round(x,9) for x in v]
    nodata=None
    if 42113 in tags:
        kind,count,inline=tags[42113]
        val=_slice_value(tail,start,source_bytes,kind,count,inline,endian)
        if val is not None and kind==2 and count<=48:
            try:
                label=val.decode("ascii").rstrip("\x00")
            except UnicodeError:
                label=""
            if label and len(label)<=47 and all(c in "-+.0123456789eENaAnInf" for c in label):
                nodata=label
    return {
        **dimensions,
        "source_first_ifd_entries":entries,
        "source_first_ifd_metadata_offset":ifd,
        "geokey_directory_tag_present":34735 in tags,
        "geokey_direct_numeric_ids":geokeys,
        "model_pixel_scale_tag_present":33550 in tags,
        "horizontal_pixel_scale_candidate":scale,
        "model_tiepoint_tag_present":33922 in tags,
        "source_nodata_tag_present":42113 in tags,
        "source_nodata_ascii_candidate":nodata,
        "source_tiff_sample_format_tag_present":339 in tags,
        "physical_flood_depth_unit_scale_authoritatively_verified":False,
        "insured_model_input_admitted":False,
    }


def inspect_archive(path: Path) -> dict:
    source=original_directory_check(path)
    with zipfile.ZipFile(path,"r") as z:
        if len(z.infolist())!=1:
            raise OriginalTiffBlocked("expected one TIFF member only")
        info=z.infolist()[0]
        if (info.filename!=TIFF_NAME or info.file_size!=TIFF_BYTES or
            info.compress_size!=TIFF_COMPRESSED or
            info.compress_type!=zipfile.ZIP_DEFLATED or info.flag_bits&1):
            raise OriginalTiffBlocked("pinned source member profile mismatch")
        tiff_sha=sha256()
        retained=bytearray()
        count=0
        prefix=b""
        with z.open(info,"r") as entry:
            while True:
                block=entry.read(CHUNK)
                if not block:
                    break
                if not prefix:
                    prefix=block[:8]
                count+=len(block)
                if count>TIFF_BYTES:
                    raise OriginalTiffBlocked("uncompressed TIFF exceeds approved length")
                tiff_sha.update(block)
                if len(block)>=TAIL_LIMIT:
                    retained=bytearray(block[-TAIL_LIMIT:])
                else:
                    retained.extend(block)
                    if len(retained)>TAIL_LIMIT:
                        del retained[:-TAIL_LIMIT]
        # ZipExtFile verifies the original CRC32 on full read. The TIFF raw
        # chunks above are discarded immediately; only the end-region remains.
        if count!=TIFF_BYTES:
            raise OriginalTiffBlocked("original ZIP member failed total-length check")
        metadata=extract_tiff_tail_metadata(bytes(retained),prefix,count)
    return {
        **source, **metadata,
        "original_member_name":TIFF_NAME,
        "original_member_sha256_local_reproducibility":tiff_sha.hexdigest(),
        "original_member_crc_read_to_end":True,
        "original_uncompressed_member_bytes_streamed":count,
        "original_member_bytes_or_pixels_persisted":False,
    }


def probe(*, opener=_open, clock=lambda: datetime.now(timezone.utc)) -> dict:
    with tempfile.TemporaryDirectory(prefix="oc-srgk-rare-") as directory:
        path=Path(directory)/"original-provider.zip"
        ziphash=download_ephemeral(path,opener=opener)
        data=inspect_archive(path)
    # TemporaryDirectory has closed before this receipt is returned.
    stamp=clock()
    if not isinstance(stamp,datetime) or stamp.utcoffset() is None:
        raise OriginalTiffBlocked("invalid source receipt clock")
    return {
        "profile":PROFILE,
        "source_exact_original_url":ZIP_URL,
        "original_zip_full_sha256_local_reproducibility":ziphash,
        "original_zip_bytes_streamed":ZIP_BYTES,
        "original_source_observed_utc":stamp.astimezone(timezone.utc).isoformat(),
        "script_sha256":sha256(Path(__file__).read_bytes()).hexdigest(),
        "private_temp_source_archive_deleted":True,
        "original_archive_or_raster_not_stored_in_git_or_neon":True,
        "no_per_building_hazard_or_raster_pixel_values_reported":True,
        "full_zip_download_was_reviewed_and_source_locked":True,
        "second_pilot_raster_extent_intersection_not_yet_proven":True,
        "actual_insurer_exposure_or_loss_computed":False,
        "cat_model_input_approved":False,
        **data,
    }


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--live",action="store_true")
    args=p.parse_args(argv)
    if not args.live:
        p.error("explicit --live required for exactly one reviewed 132.7 MB source acquisition")
    try:
        print(json.dumps(probe(),sort_keys=True,allow_nan=False))
    except (OriginalTiffBlocked,original.ZipIndexBlocked,OSError,ValueError,
            zipfile.BadZipFile,zipfile.LargeZipFile) as exc:
        print("BLOCKED: "+str(exc),file=sys.stderr)
        return 2
    return 0


if __name__=="__main__":
    raise SystemExit(main())
