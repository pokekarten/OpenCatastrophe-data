#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Read exact original BVV Oberbayern SHP member *as a bounded stream*.

Preconditions: original source prefix, ZIP directory, complete PRJ (EPSG:25832),
original DBF and original SHX independently validated in trusted main Actions.

One read-only fixed original HTTP Range streams the complete 166.17 MB raw-
DEFLATE hausumringe.shp member, while never writing original provider bytes
to disk or Git and never storing nonmatching records. Checks the full 501 MB
uncompressed source SHP CRC, header, every polygon record structure and count
against independently proven SHX/DBF. Only two original WSF2019 native 32x32
Munich windows are queried; the report contains no cadastral coordinates,
feature IDs or raw provider geometry. The grid is a 10-m-scale **derived**
uint16 area-fraction raster, not raw source data. No WSF pixel contents are
used by this script; a later scientific join against *verified* Neon mask
samples is required to calculate true partial/vintage-mismatched overlay.
"""
from __future__ import annotations

import argparse
import base64
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import ssl
import struct
import sys
from urllib.error import HTTPError, URLError
from urllib.request import Request, ProxyHandler, HTTPSHandler, build_opener
import zlib

from research_runners.by_hausumringe_oberbayern_zip_prefix_v0 import URL, SOURCE, NoRedirect, PrefixBlocked
from research_runners.by_hausumringe_oberbayern_zip_central_v0 import FROZEN, TOTAL
from research_runners.by_hausumringe_oberbayern_shx_v0 import EXPECTED_SHX_ENTRIES

START = 275_903
NAME = b"hausumringe.shp"
ZIP_HEADER_BYTES = 30 + len(NAME)
COMPRESSED_BYTES = 166_172_236
UNCOMPRESSED_BYTES = 501_212_696
READ_BYTES = ZIP_HEADER_BYTES + COMPRESSED_BYTES
END = START + READ_BYTES - 1
RANGE = f"bytes={START}-{END}"
EXPECTED_CRC32 = 0x55540A66
MAX_SOURCE_RECORD_BYTES = 10_284
MAX_POLYGONS_PER_WINDOW = 2048
CHUNK = 1024 * 1024
DECOMPRESSED_CHUNK_MAX = 4 * 1024 * 1024
# Published existing, independently GDAL-verified 32x32 WSF Neon windows.
# The source original raster mask bits must NEVER be copied into this repository.
WINDOWS = {
    28: (11.548022640413272,48.12858881962954,11.550897249322455,48.13146342853872),
    29: (11.549459944867865,48.12571421072036,11.552334553777047,48.12858881962954),
}


class SHPBlocked(PrefixBlocked):
    """Fail closed when original SHP transport, structure or geometry differs."""


def _deps():
    try:
        import numpy as np
        from pyproj import Transformer
        from shapely.geometry import Polygon, box
        from shapely.ops import unary_union, transform
    except ImportError as exc:
        raise SHPBlocked("pinned independent shapely/PROJ/numpy are required") from exc
    return np, Transformer, Polygon, box, unary_union, transform


def _bbox_intersects(a, b):
    return a[0] < b[2] and a[2] > b[0] and a[1] < b[3] and a[3] > b[1]


def _ring_area(ring):
    return sum((x1*y2-x2*y1) for (x1,y1),(x2,y2) in zip(ring,ring[1:])) / 2


class OriginalShpReader:
    """Streaming header and all record checks; only two local clip geometries stay in RAM."""
    def __init__(self):
        np, Transformer, Polygon, box, union, transform = _deps()
        self.to_utm = Transformer.from_crs(4326,25832,always_xy=True)
        self.to_lonlat = Transformer.from_crs(25832,4326,always_xy=True)
        self.Polygon=Polygon
        self.box=box
        self.union=union
        self.transform=transform
        self.np=np
        self.window_utm={}
        self.chosen={s:[] for s in WINDOWS}
        self.counts={s:0 for s in WINDOWS}
        for s,(w,so,e,n) in WINDOWS.items():
            points=[self.to_utm.transform(x,y) for x in (w,e) for y in (so,n)]
            self.window_utm[s]=(min(x for x,_ in points),min(y for _,y in points),
                                max(x for x,_ in points),max(y for _,y in points))
        self.buf=bytearray()
        self.header_ok=False
        self.records=0
        self.output_bytes=0
        self.discarded_polygons=0

    def feed(self, chunk: bytes):
        if not chunk:
            return
        self.output_bytes+=len(chunk)
        if self.output_bytes>UNCOMPRESSED_BYTES:
            raise SHPBlocked("original SHP decompressed bytes exceed 501MB cap")
        self.buf.extend(chunk)
        if not self.header_ok:
            if len(self.buf)<100:
                return
            header=bytes(self.buf[:100])
            if (struct.unpack_from(">I",header,0)[0]!=9994
                or any(struct.unpack_from(">5I",header,4))
                or struct.unpack_from(">I",header,24)[0]*2!=UNCOMPRESSED_BYTES
                or struct.unpack_from("<II",header,28)!=(1000,5)):
                raise SHPBlocked("original SHP binary header/type/size mismatch")
            region=struct.unpack_from("<4d",header,36)
            if not (all(math.isfinite(v) for v in region)
                    and 250000<region[0]<region[2]<950000
                    and 5000000<region[1]<region[3]<5900000):
                raise SHPBlocked("original SHP broad ETRS89-UTM32 bounds malformed")
            del self.buf[:100]
            self.header_ok=True
        while len(self.buf)>=8:
            record,words=struct.unpack_from(">II",self.buf,0)
            size=words*2
            if record!=self.records+1 or not 112<=size<=MAX_SOURCE_RECORD_BYTES:
                raise SHPBlocked("original SHP record id/size outside reviewed SHX profile")
            if len(self.buf)<8+size:
                return
            self._record(bytes(self.buf[8:8+size]))
            self.records+=1
            if self.records>EXPECTED_SHX_ENTRIES:
                raise SHPBlocked("original SHP exceeds independent DBF/SHX count")
            del self.buf[:8+size]

    def _record(self, b: bytes):
        shape=struct.unpack_from("<I",b,0)[0]
        if shape!=5:
            raise SHPBlocked("original record has non-Polygon shape type")
        bb=struct.unpack_from("<4d",b,4)
        if not all(map(math.isfinite,bb)) or bb[0]>bb[2] or bb[1]>bb[3]:
            raise SHPBlocked("invalid original record bounding envelope")
        parts,points=struct.unpack_from("<II",b,36)
        if not (1<=parts<=1000 and 4<=points<=30000
                and len(b)==44+4*parts+16*points):
            raise SHPBlocked("original Shape record parts/points byte length invalid")
        hits=[s for s,r in self.window_utm.items() if _bbox_intersects(bb,r)]
        if not hits:
            self.discarded_polygons+=1
            return
        start_parts=44
        offsets=struct.unpack_from(f"<{parts}I",b,start_parts)
        if offsets[0]!=0 or any(offsets[i]>=offsets[i+1] for i in range(parts-1)):
            raise SHPBlocked("original Polygon part offsets not strictly ordered")
        if offsets[-1]+4>points:
            raise SHPBlocked("polygon last ring cannot have four vertices")
        coords_start=start_parts+4*parts
        rings=[]
        for index,p0 in enumerate(offsets):
            p1=offsets[index+1] if index+1<parts else points
            if p1-p0<4:
                raise SHPBlocked("invalid polygon ring length")
            ring=[struct.unpack_from("<dd",b,coords_start+i*16) for i in range(p0,p1)]
            if ring[0]!=ring[-1] or any(not(math.isfinite(x) and math.isfinite(y)) for x,y in ring):
                raise SHPBlocked("invalid original closed UTM ring")
            rings.append(ring)
        shells=[]
        holes=[]
        for ring in rings:
            sign=_ring_area(ring)
            polygon=self.Polygon(ring)
            if polygon.is_empty or not polygon.is_valid or polygon.area<=0 or sign==0:
                raise SHPBlocked("selected original cadastral polygon invalid")
            if sign<0:
                shells.append(polygon)
            else:
                holes.append(polygon)
        if not shells:
            raise SHPBlocked("source SHP contains no clockwise exterior ring")
        geometry=self.union(shells)
        if holes:
            geometry=geometry.difference(self.union(holes))
        if geometry.is_empty or not geometry.is_valid or geometry.area<=0:
            raise SHPBlocked("source polygon holes/shells inconsistent")
        for s in hits:
            clip=self.box(*self.window_utm[s])
            if geometry.intersects(clip):
                self.chosen[s].append(geometry)
                self.counts[s]+=1
                if self.counts[s]>MAX_POLYGONS_PER_WINDOW:
                    raise SHPBlocked("per-window original Polygon hard count exceeded")

    def finish(self):
        if not self.header_ok or self.buf or self.output_bytes!=UNCOMPRESSED_BYTES:
            raise SHPBlocked("original SHP stream truncated or has leftover bytes")
        if self.records!=EXPECTED_SHX_ENTRIES:
            raise SHPBlocked("original SHP count does not match independently validated DBF/SHX")
        return self.aggregate()

    def aggregate(self):
        results=[]
        for sid,(w,so,e,n) in WINDOWS.items():
            if self.chosen[sid]:
                polygon=self.union(self.chosen[sid])
                delta_x=(e-w)/32
                delta_y=(n-so)/32
                def to_pixel(x,y,z=None):
                    xx,yy=self.to_lonlat.transform(x,y)
                    return ((self.np.asarray(xx)-w)/delta_x,
                            (n-self.np.asarray(yy))/delta_y)
                mapped=self.transform(to_pixel,polygon)
                clipped=mapped.intersection(self.box(0,0,32,32))
                if not clipped.is_valid:
                    raise SHPBlocked("original selected polygons do not union cleanly")
            else:
                clipped=self.box(0,0,0,0)
            fractions=[]
            for py in range(32):
                for px in range(32):
                    area=clipped.intersection(self.box(px,py,px+1,py+1)).area if not clipped.is_empty else 0.0
                    if not math.isfinite(area) or area < -1e-7 or area > 1.0000001:
                        raise SHPBlocked("source pixel area conservation failed")
                    fractions.append(max(0,min(65535,round(max(0,area)*65535))))
            data=struct.pack("<1024H",*fractions)
            results.append({
                "neon_native_wsf_sample_id":sid,
                "official_polygon_candidates_in_broad_utm_bbox":self.counts[sid],
                "fractional_original_footprint_area_native_pixel_equivalents":round(sum(fractions)/65535,6),
                "positive_footprint_pixels":sum(x>0 for x in fractions),
                "derived_fraction_uint16_le_32x32_base64":base64.b64encode(data).decode("ascii"),
                "derived_fraction_uint16_le_sha256":hashlib.sha256(data).hexdigest(),
                "quantization_absolute_error_per_cell_max":1/65535,
                "original_geometry_coordinates_emitted":False,
            })
        return results


def verify_live(transport):
    """Accepts one already-open source HTTP response for offline fake-stream tests."""
    if transport.status!=206 or transport.geturl()!=URL:
        raise SHPBlocked("official exact original source response must be HTTP 206")
    h=transport.headers
    if (h.get("Content-Range")!=f"bytes {START}-{END}/{TOTAL}"
        or h.get("Content-Length") not in (None,str(READ_BYTES))
        or h.get("Content-Encoding","identity").lower()!="identity"
        or h.get("Content-Type","").split(";",1)[0].strip().lower()
            not in ("application/zip","application/octet-stream","binary/octet-stream")):
        raise SHPBlocked("original source compressed Shape Range/encoding drift")
    local=transport.read(ZIP_HEADER_BYTES)
    if len(local)!=ZIP_HEADER_BYTES or local[:4]!=b"PK\x03\x04":
        raise SHPBlocked("original Shape ZIP local header incomplete")
    (version,flags,method,mtime,mdate,crc,zipped,rawlen,name_len,extra_len)=struct.unpack_from("<HHHHHIIIHH",local,4)
    if (version,flags,method,crc,zipped,rawlen,name_len,extra_len)!=(20,0,8,EXPECTED_CRC32,COMPRESSED_BYTES,UNCOMPRESSED_BYTES,len(NAME),0):
        raise SHPBlocked("original source Shape header versus directory not identical")
    if (local[30:]!=NAME or FROZEN["hausumringe.shp"]!=(START,COMPRESSED_BYTES,UNCOMPRESSED_BYTES)
        or END+1!=FROZEN["hausumringe.shx"][0]):
        raise SHPBlocked("original Shape member identity/adjacency drift")
    sha=hashlib.sha256()
    rawsha=hashlib.sha256()
    crc_accum=0
    unzip=zlib.decompressobj(wbits=-15)
    reader=OriginalShpReader()
    compressed_read=0
    while compressed_read<COMPRESSED_BYTES:
        take=min(CHUNK,COMPRESSED_BYTES-compressed_read)
        compressed=transport.read(take)
        if not compressed or len(compressed)>take:
            raise SHPBlocked("source Shape streaming Range truncated/overread")
        compressed_read+=len(compressed)
        sha.update(compressed)
        input_data=compressed
        while input_data:
            decompressed=unzip.decompress(input_data,DECOMPRESSED_CHUNK_MAX)
            if decompressed:
                rawsha.update(decompressed)
                crc_accum=zlib.crc32(decompressed,crc_accum)
                reader.feed(decompressed)
            input_data=unzip.unconsumed_tail
        if unzip.eof and compressed_read<COMPRESSED_BYTES:
            raise SHPBlocked("ZIP SHP DEFLATE unexpectedly finished before source member end")
    if transport.read(1):
        raise SHPBlocked("original server returned more than specified member bytes")
    trailer=unzip.flush()
    if trailer:
        rawsha.update(trailer)
        crc_accum=zlib.crc32(trailer,crc_accum)
        reader.feed(trailer)
    if not unzip.eof or unzip.unused_data or unzip.unconsumed_tail or crc_accum!=EXPECTED_CRC32:
        raise SHPBlocked("source original Shape DEFLATE tail/CRC32 mismatch")
    overview=reader.finish()
    return {
        "profile":"oc-bvv-official-oberbayern-original-shp-2-wsf-native-window-v0",
        "source_id":SOURCE,
        "official_original_zip_url":URL,
        "original_http_range":RANGE,
        "original_compressed_shp_bytes_verified":compressed_read,
        "original_uncompressed_shp_bytes_verified":reader.output_bytes,
        "original_compressed_shp_sha256":sha.hexdigest(),
        "original_uncompressed_shp_sha256":rawsha.hexdigest(),
        "original_shp_zip_crc32_verified":f"{crc_accum:08x}",
        "full_official_shp_member_verified":True,
        "original_shp_polygon_record_count_verified":reader.records,
        "shx_and_dbf_original_record_count_expected":EXPECTED_SHX_ENTRIES,
        "original_source_shp_polygon_bytes_persisted":False,
        "original_source_shp_polygon_coordinates_emitted":False,
        "original_hu_by_survey_vintage_verified":False,
        "wsf2019_raster_mask_compared":False,
        "2019_versus_current_cadastre_epoch_mismatch":True,
        "population_wide_detection_metrics_approved":False,
        "model_input_approved":False,
        "native_window_source_derived_grids":overview,
    }


def probe():
    req=Request(URL,method="GET",headers={
        "Range":RANGE,
        "Accept-Encoding":"identity",
        "Accept":"application/zip",
        "User-Agent":"OpenCatastrophe-BVV-SHP-Bounded-Research-Windows-v0",
    })
    try:
        with build_opener(ProxyHandler({}),NoRedirect(),
            HTTPSHandler(context=ssl.create_default_context())
        ).open(req,timeout=120) as res:
            result=verify_live(res)
    except (HTTPError,URLError,TimeoutError,OSError) as exc:
        raise SHPBlocked("original public Shape source streaming access failed") from exc
    result["retrieved_at_utc"]=datetime.now(timezone.utc).isoformat()
    result["runner_sha256"]=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    return result


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--live",action="store_true")
    args=p.parse_args(argv)
    if not args.live:
        p.error("166MB original ZIP-SHP research stream requires reviewed trusted-main-only explicit opt-in")
    try:
        print(json.dumps(probe(),sort_keys=True,allow_nan=False))
        return 0
    except SHPBlocked:
        print("BLOCKED: original BVV SHP geometry scientific source integrity failed",file=sys.stderr)
        return 2


if __name__=="__main__":
    raise SystemExit(main())
