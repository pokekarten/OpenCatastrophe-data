# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Bounded true original NRW 2022 SHP/DBF prefix -> one physical geocoding smoke.

NOT company R+V insured locations or Oasis model input. No raw OI/record rows
persisted. Avoid expensive 859MB original download while auditing geometry paths.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import struct
import sys
from collections import Counter

from rva_nrw_hu_2022_original_zip_range_receipt_v0 import (
    _head,_range,MAX_TAIL,eocd_from_last_bytes,parse_directory,OriginalZipBlocked
)
from rva_nrw_hu_2022_original_member_headers_v0 import read_member_prefix,verify_headers

MAX_COMPRESSED=128*1024
MAX_DECOMPRESSED=512*1024
MAX_RECORDS=250


def parse_first_original_records(shp:bytes,dbf:bytes,limit:int=MAX_RECORDS)->tuple[list[dict],dict]:
    if not isinstance(shp,bytes) or not isinstance(dbf,bytes) or not 1<=limit<=MAX_RECORDS:
        raise OriginalZipBlocked("bad bounded source record input")
    if (len(shp)<100 or struct.unpack_from(">I",shp,0)[0]!=9994
        or struct.unpack_from("<I",shp,32)[0]!=5 or len(dbf)<33):
        raise OriginalZipBlocked("original polygon/DBF prefix signature mismatch")
    dbflen=struct.unpack_from("<H",dbf,8)[0]
    recordlen=struct.unpack_from("<H",dbf,10)[0]
    if dbflen!=161 or recordlen!=46 or len(dbf)<dbflen:
        raise OriginalZipBlocked("NRW original 2022 four-field DBF schema drift")
    off=100
    selected=[]
    rejected=Counter()
    inspected=0
    while inspected<limit and off+8<=len(shp):
        record_id,halfwords=struct.unpack_from(">II",shp,off)
        size=halfwords*2
        if record_id!=inspected+1 or size<44 or size>MAX_DECOMPRESSED:
            raise OriginalZipBlocked("source SHP record sequence/type/size mismatch")
        if off+8+size>len(shp):
            rejected["incomplete_prefix_last_record"]+=1
            break
        rowoffset=dbflen+inspected*recordlen
        if rowoffset+recordlen>len(dbf):
            rejected["dbf_prefix_exhausted"]+=1
            break
        source=shp[off+8:off+8+size]
        if struct.unpack_from("<I",source,0)[0]!=5:
            rejected["not_polygon_record"]+=1
            off+=8+size
            inspected+=1
            continue
        parts,points=struct.unpack_from("<II",source,36)
        if (parts<1 or parts>100 or points<4 or points>10000
            or 44+4*parts+16*points!=size):
            rejected["polygon_bad_structure"]+=1
            off+=8+size
            inspected+=1
            continue
        indexes=list(struct.unpack_from("<"+"I"*parts,source,44))
        if indexes[0]!=0 or sorted(set(indexes))!=indexes or indexes[-1]>=points:
            rejected["invalid_part_offsets"]+=1
            off+=8+size
            inspected+=1
            continue
        if parts!=1:
            rejected["complex_multipart_polygon"]+=1
            off+=8+size
            inspected+=1
            continue
        start=44+4*parts
        coords=list(struct.iter_unpack("<dd",source[start:start+16*points]))
        if (len(coords)!=points or coords[0]!=coords[-1]
            or any(not (math.isfinite(x) and math.isfinite(y))
                   for x,y in coords)):
            rejected["invalid_ring"]+=1
            off+=8+size
            inspected+=1
            continue
        row=dbf[rowoffset:rowoffset+recordlen]
        if row[0]!=0x20:
            rejected["deleted_dbf_record"]+=1
            off+=8+size
            inspected+=1
            continue
        ags=row[1:9].decode("ascii","strict").strip()
        # Original physical building func code and object ID are NOT
        # insured occupancy or carrier identity, and never emitted.
        gfk=row[26:36].decode("ascii","strict").strip()
        if not re.fullmatch(r"05\d{6}",ags):
            rejected["out_of_nrw_source_ags"]+=1
            off+=8+size
            inspected+=1
            continue
        selected.append({"ags_kreis":ags[:5],"coords":coords,"gfk":gfk})
        off+=8+size
        inspected+=1
    return selected,{"shp_records_inspected":inspected,"nonadmitted_reasons":dict(rejected)}


def reproject_first_valid_physical_building(rows:list[dict])->dict:
    # Optional independently pinned CRS/geometry toolchain, invoked only after
    # official ZIP member/header checks; NOT a full DBF/SHP CRC/full file check.
    from pyproj import Transformer
    from shapely.geometry import Polygon
    transformer=Transformer.from_crs("EPSG:4647","EPSG:4326",always_xy=True)
    details=[]
    for row in rows:
        poly=Polygon(row["coords"])
        if not poly.is_valid or poly.is_empty or poly.area<=0:
            continue
        p=poly.representative_point()
        x,y=p.x,p.y
        if not (32_200_000<=x<=32_600_000 and 5_500_000<=y<=5_900_000):
            continue
        lon,lat=transformer.transform(x,y)
        if not (5.7<lon<9.9 and 50.0<lat<52.8):
            continue
        details.append({"kreis_ags":row["ags_kreis"],"lon":round(lon,6),
                        "lat":round(lat,6),"original_geometry_valid":True})
        if len(details)==3:break
    if not details:
        raise OriginalZipBlocked("no independently transformed interior physical candidate in bounded original prefix")
    return {
        "schema":"NRW_HU_2022_ORIGINAL_FIRST_PHYSICAL_POLYGON_SMOKE_V0",
        "actual_source_geometry_reprojected_to_wgs84":True,
        "verified_source_EPSG4647_to_EPSG4326_transform":True,
        "observed_original_example_physical_polygons_count":len(details),
        "original_example_county_codes":[p["kreis_ags"] for p in details],
        # Coordinates of ONLY original publicly published physical polygons,
        # NEVER R+V insured sites, customer addresses or company TIV.
        "physical_source_only_sample_wgs84_coordinates":[{"lat":p["lat"],"lon":p["lon"]} for p in details],
        "source_original_zip_sha256_verified":False,
        "full_source_shape_crc_verified":False,
        "all_NRW_buildings_ingested":False,
        "selected_hu_footprint_is_residential_use_verified":False,
        "actual_RV_insured_site_location_verified":False,
        "model_input_approved":False,
        "German_Oasis_GUL_IL_RI_OEP_AEP":False,
    }


def probe():
    total=_head()
    tail_start=total-MAX_TAIL
    tail=_range(tail_start,total-1,total)
    cd=eocd_from_last_bytes(tail,tail_start,total)
    blob=_range(cd["central_offset"],cd["central_offset"]+cd["central_size"]-1,total)
    members=parse_directory(blob,cd["member_count"])
    verify_headers(members,total)
    lookup={m["name"].rsplit(".",1)[1].lower():m for m in members}
    prefixes={}
    for ext in ("shp","dbf"):
        data,complete=read_member_prefix(lookup[ext],total,
              max_compressed=MAX_COMPRESSED,max_output=MAX_DECOMPRESSED)
        if complete:
            raise OriginalZipBlocked("not an expected large original polygon/attribute source")
        prefixes[ext]=data
    physical,audit=parse_first_original_records(prefixes["shp"],prefixes["dbf"])
    result=reproject_first_valid_physical_building(physical)
    # Retain aggregate-only genuine source-code observations, without OI,
    # individual source building use or insured-asset assertions.
    from rva_nrw_hu_gfk_residential_candidate_v0 import audit_gfk_counts
    counter=Counter(row["gfk"] for row in physical)
    result["original_prefix_GFK_candidate_function_audit"]=audit_gfk_counts(dict(counter))
    result["bounded_original_prefix_audit"]=audit
    result["original_zip_byte_count"]=total
    result["original_source_member_sha256_digests_are_full_file"]=False
    return result


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--live",action="store_true",help="explicit source-only bounded range inspection")
    opt=ap.parse_args()
    if not opt.live:ap.exit(2,"BLOCKED: live original source opt-in required\n")
    print(json.dumps(probe(),sort_keys=True,indent=2))
    return 0

if __name__=="__main__":
    try:sys.exit(main())
    except (OSError,ValueError,UnicodeError,struct.error) as exc:
        print("NRW_HU_2022_ORIGINAL_POLYGON_SMOKE_BLOCKED: "+str(exc),file=sys.stderr)
        sys.exit(2)
