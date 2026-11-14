#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""CRS-consistent ACT Apr↔Nov singleton CACLR address-position diagnostic.

Read only SHA-pinned original public ACT sources in a temporary runner.
One-to-one *text* key is a candidate link; metric distance is internally
correlated ACT evidence, not an independent surveyed address/building truth.
Never export a source ID, individual coordinate, geometry, matched row or
an insurer exposure.
"""
from __future__ import annotations

import argparse
from collections import Counter
from contextlib import closing
import csv
import hashlib
import json
import math
from pathlib import Path
import sqlite3
import statistics
import struct
import sys
import tempfile
import zipfile

from research_runners.lu_bd_adresses_original_csv_quality_v0 import (
    EXPECTED_SHA256 as NOV_SHA,
    EXPECTED_SIZE as NOV_SIZE,
    HEADER as NOV_HEADER,
    _valid_number,
    verify_original_stream,
)
from research_runners.lu_geobase_addresses_20260401_original_v0 import (
    EXPECTED_GPKG_SHA256 as APR_GPKG_SHA,
    EXPECTED_ZIP_SHA256 as APR_ZIP_SHA,
    _text_id,
    inspect as inspect_april,
)
from research_runners.luxembourg_geobase_buildings_20261001_v0 import _safe

APR_ROWS = 179024
NOV_ROWS = 179768
EXPECTED_SHARED_SINGLETON_CACLR = 177709
MAX_GPKG_BYTES = 400 * 1024 * 1024
MAX_GEOMETRY_BYTES = 200000
ENVELOPE_LENGTH = {0:0, 1:32, 2:48, 3:48, 4:64}


class ParityError(ValueError):
    """Unsupported or drifted original address location evidence."""


def geopackage_single_point(value: object) -> tuple[float,float] | None:
    """Parse v1 StandardGeoPackageBinary MULTIPOINT; refuse 2+ or empty.

    OGC GeoPackage standard: 8-byte GP header, optional coordinate envelope
    and WKB; no source IDs or raw coordinates are ever emitted to logs.
    """
    if not isinstance(value,(bytes,bytearray)) or not 9 <= len(value) <= MAX_GEOMETRY_BYTES:
        raise ParityError("invalid original GPKG geometry blob size")
    if value[:2] != b"GP" or value[2] != 0:
        raise ParityError("unreviewed GeoPackageBinary magic/version")
    flags=value[3]
    if flags & 0xE0:
        raise ParityError("extended/reserved GeoPackageBinary flags")
    envelope_code=(flags >> 1) & 7
    if envelope_code not in ENVELOPE_LENGTH:
        raise ParityError("unknown GeoPackage envelope code")
    byteorder = "<" if flags & 1 else ">"
    if struct.unpack_from(byteorder+"i",value,4)[0] != 2169:
        raise ParityError("GeoPackage feature declares non-LUREF SRS")
    offset=8+ENVELOPE_LENGTH[envelope_code]
    if flags & 0x10:
        return None
    if len(value)<=offset:
        raise ParityError("truncated GeoPackage geometry")
    try:
        from shapely import wkb
        geometry=wkb.loads(value[offset:])
    except Exception as exc:
        raise ParityError("undecodable original multipoint WKB") from exc
    if geometry.geom_type != "MultiPoint":
        raise ParityError("original declared MULTIPOINT geometry changed")
    if geometry.is_empty or len(geometry.geoms)!=1:
        return None
    pt=geometry.geoms[0]
    x,y=float(pt.x),float(pt.y)
    if not (math.isfinite(x) and math.isfinite(y)
            and 25000 <= x <= 130000 and 25000 <= y <= 160000):
        raise ParityError("original GPKG point outside reviewed EPSG2169 envelope")
    return x,y


def percentile(values:list[float], probability:float)->float|None:
    if not values:
        return None
    ordered=sorted(values)
    position=(len(ordered)-1)*probability
    lo=math.floor(position);hi=math.ceil(position)
    return ordered[lo]+(ordered[hi]-ordered[lo])*(position-lo)


def metric_summary(distances:list[float], non_singlepoint:int)->dict:
    if any(type(d) not in (float,int) or not math.isfinite(d) or d<0 for d in distances):
        raise ParityError("nonfinite or negative positional residual")
    if type(non_singlepoint) is not int or non_singlepoint<0:
        raise ParityError("invalid omitted source geometry count")
    return {
        "matched_singleton_caclr_key_candidates": len(distances)+non_singlepoint,
        "metric_residual_observations": len(distances),
        "omitted_empty_or_multipoint_original_geometries": non_singlepoint,
        "residual_at_most_0_01m": sum(d<=0.01 for d in distances),
        "residual_at_most_1m": sum(d<=1 for d in distances),
        "residual_at_most_10m": sum(d<=10 for d in distances),
        "residual_at_most_50m": sum(d<=50 for d in distances),
        "residual_over_50m": sum(d>50 for d in distances),
        "median_residual_m": None if not distances else round(statistics.median(distances),3),
        "p95_residual_m": None if not distances else round(percentile(distances,.95),3),
        "p99_residual_m": None if not distances else round(percentile(distances,.99),3),
        "max_residual_m": None if not distances else round(max(distances),3),
        "same_provider_family": True,
        "same_physical_address_or_building_proven": False,
        "independent_survey_accuracy_proven": False,
        "temporal_changes_adjudicated": False,
        "insurer_exposure_or_tiv_proven": False,
        "cat_model_input_admitted": False,
        "per_record_ids_coords_or_matches_exported": False,
    }


def _november(path:Path):
    count:Counter[str]=Counter()
    coords:dict[str,tuple[float,float]]={}
    rows=0
    with path.open("r",encoding="utf-8-sig",newline="") as stream:
        reader=csv.reader(stream,delimiter=";",strict=True)
        if tuple(next(reader,()))!=NOV_HEADER:
            raise ParityError("original Nov address header drift")
        for row in reader:
            rows+=1
            if rows>NOV_ROWS or len(row)!=len(NOV_HEADER):
                raise ParityError("original Nov CSV row budget or width drift")
            key=_text_id(row[5],"november CACLR")
            east=_valid_number(row[8],25000,130000)
            north=_valid_number(row[9],25000,160000)
            if key is None or east is None or north is None:
                raise ParityError("original November CACLR/coordinate population missing")
            count[key]+=1
            coords.setdefault(key,(east,north))
    if rows!=NOV_ROWS:
        raise ParityError("original Nov national count changed")
    return count,coords


def _april_gpkg(zip_path:Path,work:Path)->Path:
    receipt=inspect_april(zip_path)
    if (receipt["observed_original_zip_sha256"]!=APR_ZIP_SHA
            or receipt["observed_original_gpkg_sha256"]!=APR_GPKG_SHA
            or len(receipt["gpkg_original_address_layers"])!=1
            or receipt["gpkg_original_address_layers"][0]["source_layer_name"]!="AD_Address"
            or receipt["gpkg_original_address_layers"][0]["original_feature_rows"]!=APR_ROWS):
        raise ParityError("original April source proof drift")
    target=work/"original-april.gpkg"
    with zipfile.ZipFile(zip_path) as archive:
        members=[z for z in archive.infolist()
                 if z.filename.lower().endswith(".gpkg") and not z.is_dir()]
        if len(members)!=1:
            raise ParityError("original April GPKG archive schema drift")
        member=members[0]
        _safe(member)
        if not 0<member.file_size<=MAX_GPKG_BYTES:
            raise ParityError("unbounded original April GPKG")
        size=0;digest=hashlib.sha256()
        with archive.open(member) as src,target.open("xb") as dst:
            while chunk:=src.read(1024*1024):
                size+=len(chunk)
                if size>member.file_size or size>MAX_GPKG_BYTES:
                    raise ParityError("unbounded April extraction")
                digest.update(chunk);dst.write(chunk)
        if size!=member.file_size or digest.hexdigest()!=APR_GPKG_SHA:
            raise ParityError("original April extracted SHA-256 drift")
    return target


def inspect(april_zip:Path,november_csv:Path)->dict:
    if any(p.is_symlink() or not p.is_file() for p in (april_zip,november_csv)):
        raise ParityError("original paths must be regular local files")
    if november_csv.stat().st_size != NOV_SIZE:
        raise ParityError("original Nov CSV source size drift")
    with november_csv.open("rb") as stream:
        receipt=verify_original_stream(stream)
    if receipt["original_sha256_computed"]!=NOV_SHA or receipt["row_count"]!=NOV_ROWS:
        raise ParityError("original Nov source hash or count drift")
    novcounts,novcoords=_november(november_csv)
    with tempfile.TemporaryDirectory(prefix="oc-lu-coordinate-parity-") as temp:
        original=_april_gpkg(april_zip,Path(temp))
        with closing(sqlite3.connect(original.resolve().as_uri()+"?mode=ro&immutable=1",uri=True)) as db:
            db.execute("PRAGMA query_only=ON")
            if db.execute("PRAGMA application_id").fetchone()[0] not in (
                0x47504B47,0x47503130,0x47503131):
                raise ParityError("original April file not GeoPackage")
            layer=db.execute(
                "SELECT c.srs_id,g.geometry_type_name FROM gpkg_contents c "
                "JOIN gpkg_geometry_columns g ON c.table_name=g.table_name "
                "WHERE c.table_name='AD_Address' AND c.data_type='features'"
            ).fetchone()
            if layer is None or layer[0]!=2169 or str(layer[1]).upper()!="MULTIPOINT":
                raise ParityError("original April SRS/geometry changed")
            counts:Counter[str]=Counter()
            size=0
            for (value,) in db.execute('SELECT "AlternativeIdentifier" FROM "AD_Address"'):
                size+=1
                if size>APR_ROWS:
                    raise ParityError("April source count exceeded bound")
                key=_text_id(value,"April AlternativeIdentifier")
                if key is None:
                    raise ParityError("April source CACLR key missing")
                counts[key]+=1
            if size!=APR_ROWS:
                raise ParityError("April source count drift")
            eligible={key for key,num in counts.items()
                      if num==1 and novcounts.get(key)==1}
            if len(eligible)!=EXPECTED_SHARED_SINGLETON_CACLR:
                raise ParityError("April/November original singleton-key population changed")
            residuals=[];non_singlepoint=0;observed=0
            for key,blob in db.execute('SELECT "AlternativeIdentifier","geom" FROM "AD_Address"'):
                key=_text_id(key,"April AlternativeIdentifier")
                if key not in eligible:
                    continue
                observed+=1
                point=geopackage_single_point(blob)
                if point is None:
                    non_singlepoint+=1
                else:
                    x,y=novcoords[key]
                    residuals.append(math.hypot(point[0]-x,point[1]-y))
            if observed!=len(eligible):
                raise ParityError("original singleton candidate conservation failed")
    return {
        "profile":"lu-apr-nov-caclr-singleton-position-parity-v0",
        "sources":{"april_geobase_zip_sha256":APR_ZIP_SHA,
                   "april_geobase_gpkg_sha256":APR_GPKG_SHA,
                   "november_bd_adresses_csv_sha256":NOV_SHA},
        "snapshots":{"april":"2026-04-01","november":"2026-11-02"},
        "apr_original_address_rows":APR_ROWS,
        "nov_original_address_rows":NOV_ROWS,
        "common_singleton_original_caclr_keys":len(eligible),
        "shared_non_singleton_keys_not_evaluated":545,
        "crs_compared":"EPSG:2169 to EPSG:2169 (source-native planar meters)",
        **metric_summary(residuals,non_singlepoint),
    }


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--april-addresses-zip",required=True,type=Path)
    p.add_argument("--november-addresses-csv",required=True,type=Path)
    a=p.parse_args(argv)
    try:
        result=inspect(a.april_addresses_zip,a.november_addresses_csv)
    except (OSError,ValueError,UnicodeError,csv.Error,sqlite3.DatabaseError,
            zipfile.BadZipFile,EOFError):
        print("BLOCKED: original cross-release singleton position evidence invalid",
              file=sys.stderr)
        return 2
    print(json.dumps(result,sort_keys=True,indent=2,allow_nan=False))
    return 0


if __name__=="__main__":
    raise SystemExit(main())
