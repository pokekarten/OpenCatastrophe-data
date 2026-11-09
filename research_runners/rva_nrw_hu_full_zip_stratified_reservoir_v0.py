# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Bounded-memory streaming survey and county-stratified reservoir of official 2022 NRW HU.

No insurer portfolio is used or inferred in this source-only module. Requires
an explicitly acquired full 901,092,946-byte official historical ZIP; does
not download it. Source eligibility = narrowly documented 2021 official
ALKIS 31001_GFK residential *function*, not verified living-space occupancy.
Models, insured geocodes, roof structure, 2022 construction age and 2025 R+V
association all remain unverified. Full original ZIP and all four member CRCs
are checked before any selected file can be exported.
"""
from __future__ import annotations

from collections import Counter
from functools import lru_cache
import hashlib
import heapq
import math
from pathlib import Path
import re
import stat
import struct
import zipfile

from rva_nrw_hu_gfk_residential_candidate_v0 import classify_gfk

EXPECTED_ZIP_BYTES = 901_092_946
EXPECTED_ORIGINAL_SHA256 = "10e5b9fd1d299ef0efa883bfadce7c4c3fd2ed7b42076557cbdff887a0d277da"
EXPECTED_FEATURES = 11_232_755
MEMBERS = {
    "2022_hu_shp.shp":(2_089_262_804,0x385d573b),
    "2022_hu_shp.shx":(89_862_140,0x87e38e30),
    "2022_hu_shp.dbf":(516_706_892,0x08d33c15),
    "2022_hu_shp.prj":(414,0x9a485a65),
}
SALT = "OpenCatastrophe-2026-rva-nrw-HU22-research-reservoir-v0"
MAX_RECORD_BYTES = 8_000_000


class SourceBlocked(ValueError):
    """A source/candidate/identity/scientific gate failed closed."""


def sha256_regular_file(path:Path,*,expected_size:int=EXPECTED_ZIP_BYTES)->str:
    if path.is_symlink() or not path.is_file() or path.stat().st_size!=expected_size:
        raise SourceBlocked("original ZIP must be regular non-symlink expected exact size")
    digest=hashlib.sha256()
    with path.open("rb") as f:
        while chunk:=f.read(4*1024*1024):
            digest.update(chunk)
    return digest.hexdigest()


def validate_official_zip_metadata(z:zipfile.ZipFile,*,production:bool=True)->dict:
    names=set(z.namelist())
    if production and names!=set(MEMBERS):
        raise SourceBlocked("exact four original 2022 HU member names required")
    found={}
    for item in z.infolist():
        if (item.filename.startswith("/") or ".." in item.filename.split("/")
            or item.flag_bits&1 or item.compress_type!=zipfile.ZIP_DEFLATED):
            raise SourceBlocked("ZIP file entry unsafe or unsupported")
        if production:
            want=MEMBERS[item.filename]
            if (item.file_size,item.CRC)!=want:
                raise SourceBlocked("original HU original archive member size or CRC changed")
        found[item.filename]={"uncompressed_bytes":item.file_size,"CRC32":f"{item.CRC:08x}"}
    return dict(sorted(found.items()))


def inspect_headers(shp,dbf,shx_length:int,*,expected_count:int)->None:
    s=shp.read(100)
    d=dbf.read(161)
    if len(s)!=100 or len(d)!=161:
        raise SourceBlocked("original shape and DBF headers missing")
    if (struct.unpack_from(">I",s,0)[0]!=9994
        or struct.unpack_from("<I",s,28)[0]!=1000
        or struct.unpack_from("<I",s,32)[0]!=5
        or struct.unpack_from("<I",d,4)[0]!=expected_count
        or struct.unpack_from("<H",d,8)[0]!=161
        or struct.unpack_from("<H",d,10)[0]!=46
        or d[160]!=13
        or shx_length!=100+expected_count*8):
        raise SourceBlocked("original Polygon/record/DBF/SHX contract drift")


@lru_cache(maxsize=1)
def _pinned_transformer():
    from pyproj import Transformer
    return Transformer.from_crs("EPSG:4647","EPSG:4326",always_xy=True)


def _point_from_shape(payload:bytes)->tuple[float,float,float]:
    """Return interior WGS84 (lon,lat) and geometric footprint area (m2).

    Source coordinates are EPSG:4647. Only single-ring Polygon5 objects are
    handled; multipart/hole topologies stay unadmitted rather than guessing.
    """
    from shapely.geometry import Polygon
    if not 48<=len(payload)<=MAX_RECORD_BYTES or struct.unpack_from("<I",payload,0)[0]!=5:
        raise SourceBlocked("candidate is not supported Polygon5")
    n_parts,n_points=struct.unpack_from("<II",payload,36)
    if n_parts!=1 or not 4<=n_points<=400_000 or len(payload)!=44+4*n_parts+16*n_points:
        raise SourceBlocked("candidate multipart, holes or source record layout unsupported")
    if struct.unpack_from("<I",payload,44)[0]!=0:
        raise SourceBlocked("candidate ring offset invalid")
    xy=list(struct.iter_unpack("<dd",payload[48:]))
    if len(xy)!=n_points or xy[0]!=xy[-1]:
        raise SourceBlocked("candidate ring is open or empty")
    if any(not math.isfinite(x) or not math.isfinite(y) for x,y in xy):
        raise SourceBlocked("candidate projected coordinate invalid")
    poly=Polygon(xy)
    if not poly.is_valid or poly.is_empty or not 20<=poly.area<=100_000:
        raise SourceBlocked("candidate footprint topology/area outside conservative pilot")
    point=poly.representative_point()
    if not (32_200_000<point.x<32_600_000 and 5_500_000<point.y<5_900_000):
        raise SourceBlocked("candidate source CRS coordinates outside NRW")
    lon,lat=_pinned_transformer().transform(point.x,point.y)
    if not (5.5<lon<10 and 50<lat<52.8):
        raise SourceBlocked("candidate WGS84 coordinates outside NRW")
    return round(lon,7),round(lat,7),round(poly.area,2)


def sample_hu_stream(shp,dbf,*,expected_count:int,shx_length:int,
                     county_targets:dict[str,int])->tuple[dict[str,list[dict]],dict]:
    """Single sequential pass, capped heap by target Kreis. No raw IDs output."""
    if (not county_targets or len(county_targets)>53
        or any(not re.fullmatch(r"05\d{3}",k) or type(n) is not int or n<1 or n>10000
               for k,n in county_targets.items())
        or sum(county_targets.values())>10000):
        raise SourceBlocked("invalid bounded county sample targets")
    inspect_headers(shp,dbf,shx_length,expected_count=expected_count)
    heaps={ags:[] for ags in county_targets}
    audit=Counter()
    eligible=Counter()
    seen_source=0
    for idx in range(expected_count):
        raw=dbf.read(46)
        rec=shp.read(8)
        if len(raw)!=46 or len(rec)!=8:
            raise SourceBlocked("source SHP/DBF alignment changed before end of original")
        rec_id,words=struct.unpack(">II",rec)
        nbytes=words*2
        if rec_id!=idx+1 or nbytes<4 or nbytes>MAX_RECORD_BYTES:
            raise SourceBlocked("original sequential SHP record header unsupported")
        payload=shp.read(nbytes)
        if len(payload)!=nbytes:
            raise SourceBlocked("original SHP record truncated")
        seen_source+=1
        if raw[0]!=0x20:
            audit["deleted_dbf"]+=1
            continue
        try:
            ags=raw[1:9].decode("ascii").strip()
            source_oid=raw[9:26].decode("ascii").strip()
            gfk=raw[26:36].decode("ascii").strip()
        except UnicodeError:
            audit["invalid_attribute_encoding"]+=1
            continue
        if not re.fullmatch(r"05\d{6}",ags):
            audit["outside_valid_NRW_AGS"]+=1
            continue
        county=ags[:5]
        if county not in heaps:
            audit["unknown_2022_Census_Kreis"]+=1
            continue
        category,_=classify_gfk(gfk)
        audit["gfk_"+category]+=1
        if category!="residential_function_candidate_only":
            continue
        eligible[county]+=1
        if not re.fullmatch(r"DENW[A-Za-z0-9]{10,13}",source_oid):
            audit["unverified_original_OI_identity"]+=1
            continue
        priority=int.from_bytes(hashlib.sha256((SALT+"|"+source_oid).encode("ascii")).digest()[:16],"big")
        heap=heaps[county]
        if len(heap)==county_targets[county] and -priority<=heap[0][0]:
            continue
        try:
            lon,lat,area=_point_from_shape(payload)
        except SourceBlocked:
            audit["candidate_polygon_rejected"]+=1
            continue
        source_id_digest=hashlib.sha256(source_oid.encode("ascii")).hexdigest()
        info={"lon":lon,"lat":lat,"footprint_area_m2":area,"source_gfk":gfk,
              "original_OI_sha256":source_id_digest}
        key=(-priority,-rec_id,info)
        if len(heap)<county_targets[county]:
            heapq.heappush(heap,key)
        elif key[:2]>heap[0][:2]:
            heapq.heapreplace(heap,key)
    if shp.read(1) or dbf.read(2) not in (b"\x1a",b""):
        raise SourceBlocked("SHP/DBF contains unexpected extra bytes")
    selected={}
    oid_digests=set()
    for ags,heap in heaps.items():
        if len(heap)!=county_targets[ags]:
            raise SourceBlocked("not enough eligible distinct HU physical candidates in "+ags)
        selected[ags]=[]
        for _a,_b,site in sorted(heap,reverse=True):
            if site["original_OI_sha256"] in oid_digests:
                raise SourceBlocked("duplicate source OI among different selected physical sites")
            oid_digests.add(site["original_OI_sha256"])
            selected[ags].append(site)
    return selected,{
        "original_shp_and_dbf_records_scanned":seen_source,
        "source_gfk_and_schema_quarantine_counts":dict(sorted(audit.items())),
        "source_residential_function_candidates_by_Kreis":dict(sorted(eligible.items())),
        "selected_source_physical_candidate_count":len(oid_digests),
        "stable_reservoir_seed_label":SALT,
        "source_geometry_nonselected_objects_not_assumed_valid":True,
    }


def sample_full_official_zip(path:Path, county_targets:dict[str,int])->tuple[dict,dict]:
    sha=sha256_regular_file(path)
    if sha != EXPECTED_ORIGINAL_SHA256:
        raise SourceBlocked("original provider 2022 archive SHA256 identity drift")
    with zipfile.ZipFile(path) as archive:
        members=validate_official_zip_metadata(archive)
        shpinfo=archive.getinfo("2022_hu_shp.shp")
        shxinfo=archive.getinfo("2022_hu_shp.shx")
        # Every uncompressed member is streamed to EOF: zipfile verifies CRC.
        with archive.open("2022_hu_shp.shp") as shp,archive.open("2022_hu_shp.dbf") as dbf:
            selected,audit=sample_hu_stream(
                shp,dbf,expected_count=EXPECTED_FEATURES,
                shx_length=shxinfo.file_size,county_targets=county_targets)
        with archive.open("2022_hu_shp.prj") as f:
            prj=f.read()
        if (len(prj)!=414 or
            hashlib.sha256(prj).hexdigest()!="bb566c8913055c06c80a9a072861ef72aa17e0d77f1f9794fec28dc8313406d8"):
            raise SourceBlocked("original 2022 exact EPSG4647 projection WKT drift")
        with archive.open("2022_hu_shp.shx") as f:
            while f.read(4*1024*1024):
                pass
    audit.update({
        "exact_source_original_url":
            "https://www.opengeodata.nrw.de/produkte/geobasis/lk/hist/hist_hu_shp/2022_hu_EPSG4647_Shape.zip",
        "full_original_source_zip_sha256":sha,
        "full_original_source_archive_bytes":EXPECTED_ZIP_BYTES,
        "all_four_original_member_CRCs_verified_by_ZipExtFile_EOF":True,
        "original_zip_member_metadata":members,
        "source_2022_hu_buildings_prove_company_insured_risks":False,
        "source_age_observed_per_building":False,
        "all_GFK_codes_are_insured_residential":False,
        "original_source_2022_GFK_codebook_exact_vintage_reconciled":False,
        "model_input_approved":False,
    })
    return selected,audit
